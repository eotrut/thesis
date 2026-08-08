"""
AURA — Backend API server.

AI-Based Autonomous Wall Painting Robot · Holy Angel University
Connects the trained YOLOv8 instance-segmentation model to the AURA website.

Why Flask and not FastAPI
-------------------------
The two hard requirements here are (a) multipart image upload and (b) an MJPEG
webcam stream. MJPEG is a *blocking* generator pushing frames from a shared
OpenCV capture; in FastAPI that has to be pushed onto a threadpool by hand
(``StreamingResponse`` over a sync generator) or rewritten async, and OpenCV's
``VideoCapture.read()`` is blocking either way. Flask's threaded dev server maps
onto that model directly with no async ceremony, and the whole surface is three
endpoints — FastAPI's schema/validation upside doesn't pay for itself here.

Endpoints
---------
POST /api/segment   multipart image -> base64 original + masked overlay + detections
POST /api/toolpath  multipart image -> mm-space serpentine paint path + G-code
GET  /api/stream    MJPEG webcam stream, ?overlay=pre|during|post
GET  /api/status    model / camera / CUDA status for the dashboard

Run:
    python backend/app.py                  # http://localhost:5000
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
import threading
import time

import cv2
import numpy as np
from flask import Flask, Response, jsonify, request, send_from_directory

# Make `python backend/app.py` work regardless of the shell's CWD.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from color_recommender import (  # noqa: E402
    CATEGORY_BIAS,
    NEUTRAL_COLORS,
    recommend_colors,
)
from coordinate_mapping import (  # noqa: E402
    WALL_HEIGHT_MM,
    WALL_WIDTH_MM,
    CalibrationError,
    WallCalibration,
)
from model_loader import (  # noqa: E402
    PROJECT_ROOT,
    ModelLoadError,
    load_model,
    segmentation_model,
    torch_info,
)
from toolpath_generator import (  # noqa: E402
    SoftLimitError,
    ToolpathError,
    events_to_gcode,
    generate_toolpath,
)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

WEBSITE_DIR = os.path.join(PROJECT_ROOT, "website")

HOST = os.environ.get("AURA_HOST", "0.0.0.0")
PORT = int(os.environ.get("AURA_PORT", "5000"))

CAMERA_INDEX = int(os.environ.get("AURA_CAMERA_INDEX", "0"))
CAMERA_WIDTH = int(os.environ.get("AURA_CAMERA_WIDTH", "1280"))
CAMERA_HEIGHT = int(os.environ.get("AURA_CAMERA_HEIGHT", "720"))
STREAM_FPS = float(os.environ.get("AURA_STREAM_FPS", "15"))
STREAM_JPEG_QUALITY = int(os.environ.get("AURA_STREAM_QUALITY", "80"))
UPLOAD_JPEG_QUALITY = int(os.environ.get("AURA_UPLOAD_QUALITY", "90"))

MAX_UPLOAD_BYTES = 16 * 1024 * 1024  # matches the "~10MB" hint in the UI, with headroom

# Overlay colours (BGR) — kept in sync with the legends on camera-view.html
# and the caption on color-recommendation.html. Change them together.
COLOR_WALL = (94, 197, 34)      # #22C55E green — paintable wall region
COLOR_OBJECT = (8, 179, 234)    # #EAB308 amber — non-paintable / obstacles
COLOR_TEXT = (255, 255, 255)

MASK_ALPHA = 0.45
VALID_OVERLAYS = ("pre", "during", "post")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("aura.api")
logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__, static_folder=WEBSITE_DIR, static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES


# --------------------------------------------------------------------------- #
# CORS — the frontend is often opened straight off disk (file://), which sends
# `Origin: null`. A wildcard ACAO covers that; we never use cookies/credentials,
# so wildcard is safe here. Done by hand to avoid the flask-cors dependency.
# --------------------------------------------------------------------------- #

@app.after_request
def add_cors_headers(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/<path:_any>", methods=["OPTIONS"])
def cors_preflight(_any: str) -> Response:
    return Response(status=204)


# --------------------------------------------------------------------------- #
# Shared inference telemetry (feeds the dashboard cards)
# --------------------------------------------------------------------------- #

class Telemetry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.last_confidence: float | None = None
        self.last_wall_detected: bool | None = None
        self.last_detection_count: int = 0
        self.last_inference_ms: float | None = None
        self.last_source: str | None = None
        self.last_timestamp: float | None = None
        self.frames_processed: int = 0

    def record(self, confidence, wall_detected, count, inference_ms, source) -> None:
        with self._lock:
            self.last_confidence = confidence
            self.last_wall_detected = wall_detected
            self.last_detection_count = count
            self.last_inference_ms = inference_ms
            self.last_source = source
            self.last_timestamp = time.time()
            self.frames_processed += 1

    def snapshot(self) -> dict:
        with self._lock:
            age = (time.time() - self.last_timestamp) if self.last_timestamp else None
            return {
                "confidence": (
                    round(self.last_confidence, 4)
                    if self.last_confidence is not None
                    else None
                ),
                "wall_detected": self.last_wall_detected,
                "detection_count": self.last_detection_count,
                "inference_ms": (
                    round(self.last_inference_ms, 1)
                    if self.last_inference_ms is not None
                    else None
                ),
                "source": self.last_source,
                "age_seconds": round(age, 1) if age is not None else None,
                "frames_processed": self.frames_processed,
            }


telemetry = Telemetry()


# --------------------------------------------------------------------------- #
# Camera management
# --------------------------------------------------------------------------- #

class Camera:
    """Shared webcam handle.

    One capture object is reused across all stream viewers — Windows will not
    hand the same device to two processes/handles at once, so opening per
    request would fail the second time. ``availability`` is cached because
    probing the camera on Windows (MSMF) takes ~1-2 s and the dashboard polls
    /api/status every 3 s.
    """

    PROBE_TTL_SECONDS = 30.0

    def __init__(self, index: int = CAMERA_INDEX) -> None:
        self.index = index
        self._cap: cv2.VideoCapture | None = None
        self._lock = threading.Lock()
        self._viewers = 0
        self._available: bool | None = None
        self._probed_at: float = 0.0
        self._error: str | None = None
        self.backend_name: str | None = None

    # -- internals -------------------------------------------------------- #

    def _backends(self):
        """Preferred capture backends, most reliable first for this platform."""
        if sys.platform == "win32":
            # DSHOW opens far faster than MSMF on Windows and avoids the
            # "MSMF: can't grab frame" warning spam on many USB webcams.
            return [(cv2.CAP_DSHOW, "DSHOW"), (cv2.CAP_MSMF, "MSMF"), (cv2.CAP_ANY, "ANY")]
        return [(cv2.CAP_ANY, "ANY")]

    def _open_locked(self) -> bool:
        if self._cap is not None and self._cap.isOpened():
            return True

        for api, name in self._backends():
            cap = cv2.VideoCapture(self.index, api)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # prefer latest frame over backlog
                ok, _ = cap.read()
                if ok:
                    self._cap = cap
                    self.backend_name = name
                    self._error = None
                    self._available = True
                    self._probed_at = time.time()
                    logger.info("Camera %d opened via %s", self.index, name)
                    return True
            cap.release()

        self._cap = None
        self._available = False
        self._probed_at = time.time()
        self._error = (
            f"Could not open camera index {self.index}. Check that a webcam is "
            f"connected, that no other app (Zoom/Teams/Camera) is using it, and "
            f"that Windows camera privacy access is enabled."
        )
        logger.error(self._error)
        return False

    def _release_locked(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Camera %d released", self.index)

    # -- public ----------------------------------------------------------- #

    def acquire(self) -> bool:
        with self._lock:
            if not self._open_locked():
                return False
            self._viewers += 1
            return True

    def release(self) -> None:
        with self._lock:
            self._viewers = max(0, self._viewers - 1)
            if self._viewers == 0:
                self._release_locked()

    def read(self):
        with self._lock:
            if self._cap is None:
                return False, None
            return self._cap.read()

    def grab_single_frame(self):
        """Open, grab one frame, and close again (used by /api/capture)."""
        if not self.acquire():
            return None
        try:
            for _ in range(5):  # first frames off a cold webcam are often black
                ok, frame = self.read()
                if ok and frame is not None:
                    return frame
            return None
        finally:
            self.release()

    @property
    def is_streaming(self) -> bool:
        return self._viewers > 0

    def availability(self) -> tuple[bool, str | None]:
        """Cached availability check — never disturbs an in-progress stream."""
        if self.is_streaming:
            return True, None
        fresh = (time.time() - self._probed_at) < self.PROBE_TTL_SECONDS
        if self._available is not None and fresh:
            return self._available, self._error

        with self._lock:
            opened = self._open_locked()
            if opened and self._viewers == 0:
                self._release_locked()
        return opened, self._error


camera = Camera()


# --------------------------------------------------------------------------- #
# Image helpers
# --------------------------------------------------------------------------- #

def decode_upload(file_storage) -> np.ndarray | None:
    """Decode an uploaded image into a BGR ndarray. Returns None if unreadable."""
    data = file_storage.read()
    if not data:
        return None
    buf = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    return image


def encode_jpeg_b64(image_bgr: np.ndarray, quality: int = UPLOAD_JPEG_QUALITY) -> str:
    """BGR ndarray -> raw base64 JPEG string (no data-URI prefix)."""
    ok, buf = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("JPEG encoding failed")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def encode_jpeg_bytes(image_bgr: np.ndarray, quality: int = STREAM_JPEG_QUALITY) -> bytes:
    ok, buf = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("JPEG encoding failed")
    return buf.tobytes()


def normalize_overlay(value: str | None) -> str:
    value = (value or "").strip().lower()
    return value if value in VALID_OVERLAYS else "post"


def normalize_category(value: str | None) -> str:
    """Read the optional "who is this room for?" field.

    Absent, blank or unrecognised all mean "no demographic bias". An unknown key
    is logged and downgraded rather than rejected: the field only ever tunes a
    palette, so a stale or mistyped value should cost the user the tuning, not
    the whole recommendation.
    """
    value = (value or "").strip().lower()
    if not value:
        return "none"
    if value not in CATEGORY_BIAS:
        logger.warning("Unknown category %r — falling back to 'none'.", value)
        return "none"
    return value


# --------------------------------------------------------------------------- #
# Detection parsing
# --------------------------------------------------------------------------- #

def _simplify_polygon(points: np.ndarray, width: int, height: int) -> list[list[float]]:
    """Reduce a mask contour to a compact, normalized (0-1) polygon.

    The frontend clips its colour-preview canvas with this, so a few dozen
    points is plenty — shipping every contour pixel would bloat the JSON by
    hundreds of KB per detection.
    """
    if points is None or len(points) < 3:
        return []
    contour = points.astype(np.float32).reshape(-1, 1, 2)
    epsilon = 0.004 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    if len(approx) < 3:
        approx = points.reshape(-1, 2)
    return [
        [round(float(x) / max(width, 1), 5), round(float(y) / max(height, 1), 5)]
        for x, y in approx
    ]


def parse_detections(result, width: int, height: int) -> list[dict]:
    """Turn one Ultralytics Result into plain dicts + binary masks.

    Each dict carries a ``_mask`` key (uint8 HxW, 0/1) used for rendering; it is
    stripped before the response is serialized.
    """
    detections: list[dict] = []
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return detections

    masks = getattr(result, "masks", None)
    names = segmentation_model.names or getattr(result, "names", {}) or {}

    mask_data = None
    mask_polys = None
    if masks is not None:
        try:
            mask_data = masks.data.cpu().numpy()  # (N, H, W) float 0..1
            mask_polys = masks.xy  # list of (K, 2) pixel-space contours
        except Exception as exc:
            logger.warning("Could not read mask tensors: %s", exc)

    cls_ids = boxes.cls.cpu().numpy().astype(int)
    confs = boxes.conf.cpu().numpy().astype(float)
    xyxy = boxes.xyxy.cpu().numpy().astype(float)
    frame_area = float(width * height) or 1.0

    for i in range(len(cls_ids)):
        class_id = int(cls_ids[i])
        class_name = str(names.get(class_id, f"class_{class_id}"))

        binary = None
        polygon: list[list[float]] = []
        if mask_data is not None and i < len(mask_data):
            binary = (mask_data[i] > 0.5).astype(np.uint8)
            # retina_masks=True should already match frame size; resize defensively.
            if binary.shape[:2] != (height, width):
                binary = cv2.resize(
                    binary, (width, height), interpolation=cv2.INTER_NEAREST
                )
            if mask_polys is not None and i < len(mask_polys):
                polygon = _simplify_polygon(np.asarray(mask_polys[i]), width, height)
            area = float(binary.sum())
        else:
            # Detection-only model: fall back to the box as a rectangular region.
            x1, y1, x2, y2 = xyxy[i]
            binary = np.zeros((height, width), dtype=np.uint8)
            cv2.rectangle(binary, (int(x1), int(y1)), (int(x2), int(y2)), 1, -1)
            polygon = [
                [round(x1 / width, 5), round(y1 / height, 5)],
                [round(x2 / width, 5), round(y1 / height, 5)],
                [round(x2 / width, 5), round(y2 / height, 5)],
                [round(x1 / width, 5), round(y2 / height, 5)],
            ]
            area = float(max(0.0, (x2 - x1)) * max(0.0, (y2 - y1)))

        detections.append(
            {
                "class_id": class_id,
                "class_name": class_name,
                "confidence": round(float(confs[i]), 4),
                "bbox": [round(float(v), 1) for v in xyxy[i]],
                "polygon": polygon,
                "area_ratio": round(area / frame_area, 4),
                "is_wall": segmentation_model.is_wall_class(class_name),
                "_mask": binary,
            }
        )

    return detections


def resolve_wall(detections: list[dict]) -> bool:
    """Decide which detections are 'the wall'. Returns True if inferred by area.

    If the trained model has an explicit wall-like class, that wins. If it does
    not (e.g. a single-class model named something else), we fall back to the
    largest-area mask and report ``wall_class_inferred`` so the UI can say so
    rather than implying the model named it.
    """
    if not detections:
        return False
    if segmentation_model.has_wall_class:
        return False

    largest = max(detections, key=lambda d: d["area_ratio"])
    largest["is_wall"] = True
    return True


# --------------------------------------------------------------------------- #
# Overlay rendering
# --------------------------------------------------------------------------- #

def render_overlay(frame: np.ndarray, detections: list[dict], mode: str) -> np.ndarray:
    """Draw segmentation masks onto a copy of the frame.

    pre    — untouched frame (baseline / "before" view)
    during — wall region only, blue
    post   — wall region blue + every other detected object amber
    """
    out = frame.copy()
    if mode == "pre" or not detections:
        return out

    if mode == "during":
        visible = [d for d in detections if d["is_wall"]]
    else:
        visible = detections

    if not visible:
        return out

    # Composite all fills in one blend so overlapping masks don't stack alpha.
    tint = np.zeros_like(out)
    painted = np.zeros(out.shape[:2], dtype=bool)

    for det in visible:
        mask = det.get("_mask")
        if mask is None:
            continue
        color = COLOR_WALL if det["is_wall"] else COLOR_OBJECT
        area = mask.astype(bool)
        tint[area] = color
        painted |= area

    if painted.any():
        out[painted] = cv2.addWeighted(
            out, 1.0 - MASK_ALPHA, tint, MASK_ALPHA, 0.0
        )[painted]

    # Outlines + labels on top of the fill.
    for det in visible:
        mask = det.get("_mask")
        if mask is None:
            continue
        color = COLOR_WALL if det["is_wall"] else COLOR_OBJECT
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, contours, -1, color, 2)

        label = f"{det['class_name']} {det['confidence']:.2f}"
        x1, y1 = int(det["bbox"][0]), int(det["bbox"][1])
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        y_text = max(th + 6, y1)
        cv2.rectangle(out, (x1, y_text - th - 6), (x1 + tw + 8, y_text + 2), color, -1)
        cv2.putText(
            out, label, (x1 + 4, y_text - 2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1, cv2.LINE_AA,
        )

    return out


def banner_frame(width: int, height: int, lines: list[str]) -> np.ndarray:
    """A dark placeholder frame carrying an error message, for the MJPEG stream."""
    frame = np.full((height, width, 3), 17, dtype=np.uint8)
    frame[:] = (32, 17, 8)  # #081120-ish, matching the site's panel background
    y = height // 2 - (len(lines) - 1) * 16
    for line in lines:
        (tw, _), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.putText(
            frame, line, ((width - tw) // 2, y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA,
        )
        y += 32
    return frame


# --------------------------------------------------------------------------- #
# Core inference entry point
# --------------------------------------------------------------------------- #

def run_inference(frame: np.ndarray, overlay: str, source: str) -> dict:
    """Segment one frame and build the full response payload (minus base64)."""
    height, width = frame.shape[:2]

    start = time.perf_counter()
    result = segmentation_model.predict(frame)
    inference_ms = (time.perf_counter() - start) * 1000.0

    detections = parse_detections(result, width, height)
    wall_inferred = resolve_wall(detections)

    wall_dets = [d for d in detections if d["is_wall"]]
    wall_detected = len(wall_dets) > 0
    wall_confidence = max((d["confidence"] for d in wall_dets), default=None)
    top_confidence = max((d["confidence"] for d in detections), default=None)
    wall_coverage = round(sum(d["area_ratio"] for d in wall_dets), 4) if wall_dets else 0.0

    overlay_image = render_overlay(frame, detections, overlay)

    telemetry.record(
        confidence=wall_confidence if wall_confidence is not None else top_confidence,
        wall_detected=wall_detected,
        count=len(detections),
        inference_ms=inference_ms,
        source=source,
    )

    return {
        "detections": detections,
        "overlay_image": overlay_image,
        "wall_detected": wall_detected,
        "wall_confidence": wall_confidence,
        "top_confidence": top_confidence,
        "wall_coverage": wall_coverage,
        "wall_class_inferred": wall_inferred,
        "inference_ms": round(inference_ms, 1),
        "width": width,
        "height": height,
    }


def public_detections(detections: list[dict]) -> list[dict]:
    """Strip the internal ``_mask`` ndarray before JSON serialization."""
    return [
        {k: v for k, v in det.items() if not k.startswith("_")} for det in detections
    ]


def segmentation_response(frame: np.ndarray, result: dict, overlay: str) -> dict:
    """Build the JSON body shared by /api/segment and /api/capture.

    Carries two overlapping sets of keys on purpose:

    * ``original`` / ``masked`` / ``confidence`` / ``classes`` — the compact
      contract in the project spec, so the endpoint can be exercised directly
      (curl, thesis appendix) without knowing the internals.
    * the longer ``*_image`` / ``wall_*`` / ``detections`` fields — what the
      website actually renders: per-detection polygons, coverage, timings.

    ``confidence`` is the wall's confidence when a wall was found, falling back
    to the top detection otherwise, and is 0.0 rather than null on an empty
    frame so the UI can format it without a null check.
    """
    original_b64 = encode_jpeg_b64(frame)
    masked_b64 = encode_jpeg_b64(result["overlay_image"])
    confidence = result["wall_confidence"]
    if confidence is None:
        confidence = result["top_confidence"]

    return {
        "success": True,
        "model_loaded": True,
        # --- spec contract ---
        "original": original_b64,
        "masked": masked_b64,
        "wall_detected": result["wall_detected"],
        "confidence": round(float(confidence), 4) if confidence is not None else 0.0,
        "classes": list(segmentation_model.names.values()),
        # --- detail used by the website ---
        "original_image": original_b64,
        "masked_image": masked_b64,
        "image_format": "jpeg",
        "detections": public_detections(result["detections"]),
        "detection_count": len(result["detections"]),
        "wall_confidence": result["wall_confidence"],
        "top_confidence": result["top_confidence"],
        "wall_coverage": result["wall_coverage"],
        "wall_class_inferred": result["wall_class_inferred"],
        "overlay_mode": overlay,
        "image_width": result["width"],
        "image_height": result["height"],
        "inference_ms": result["inference_ms"],
        "device": segmentation_model.device,
        "model": os.path.basename(segmentation_model.model_path),
        "using_fallback_model": segmentation_model.using_fallback,
    }


# --------------------------------------------------------------------------- #
# API — POST /api/segment
# --------------------------------------------------------------------------- #

def model_unavailable():
    """503 body used by every endpoint that needs the weights."""
    return (
        jsonify(
            {
                "success": False,
                "model_loaded": False,
                "error": segmentation_model.error or "Model is not loaded.",
            }
        ),
        503,
    )


def frame_from_request():
    """Decode the uploaded image.

    Returns ``(frame, None)`` on success or ``(None, error_response)`` so the
    caller can `return` the error straight through.
    """
    # The last resort takes whatever file was sent under an unexpected name, but
    # never `reference_image`: on /api/recommend-colors that field is the mood
    # shot, and segmenting it as if it were the room would silently answer a
    # different question than the one asked.
    other_files = [
        f for name, f in request.files.items() if name != "reference_image"
    ]
    file_storage = (
        request.files.get("image")
        or request.files.get("file")
        or (other_files[0] if other_files else None)
    )
    if file_storage is None:
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": "No image uploaded. Send multipart/form-data with an "
                             "'image' field.",
                }
            ),
            400,
        )

    frame = decode_upload(file_storage)
    if frame is None:
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": f"Could not decode '{file_storage.filename}' as an image. "
                             f"Supported: JPG, PNG, BMP, WEBP.",
                }
            ),
            400,
        )
    return frame, None


@app.route("/api/segment", methods=["POST"])
def api_segment():
    if not segmentation_model.is_loaded:
        return model_unavailable()

    frame, error = frame_from_request()
    if error is not None:
        return error

    overlay = normalize_overlay(request.form.get("overlay") or request.args.get("overlay"))

    try:
        result = run_inference(frame, overlay, source="upload")
    except ModelLoadError as exc:
        return jsonify({"success": False, "model_loaded": False, "error": str(exc)}), 503
    except Exception as exc:
        logger.exception("Inference failed")
        return (
            jsonify({"success": False, "error": f"{type(exc).__name__}: {exc}"}),
            500,
        )

    # Raw base64 JPEG payloads. The frontend prefixes them with
    # "data:image/jpeg;base64," before assigning to img.src.
    return jsonify(segmentation_response(frame, result, overlay))


# --------------------------------------------------------------------------- #
# API — POST /api/recommend-colors
#
# Segments the frame, reads the room's dominant colour from everything that is
# NOT wall, and derives a wall palette from it. Self-contained: it re-runs
# inference rather than depending on a prior /api/segment call, so it can be
# exercised on its own.
#
# Two optional inputs tune the result and neither is ever fatal:
#   reference_image — a second upload, blended into the palette seed
#   category        — a CATEGORY_BIAS key, "who is this room for?"
# --------------------------------------------------------------------------- #

@app.route("/api/recommend-colors", methods=["POST"])
def api_recommend_colors():
    if not segmentation_model.is_loaded:
        return model_unavailable()

    frame, error = frame_from_request()
    if error is not None:
        return error

    # Optional second upload: what the user wants the room to LOOK like, as
    # opposed to the room photo above, which is what it looks like now. Only the
    # room photo drives segmentation; this one only tints the palette seed, so an
    # unreadable file is dropped with a warning instead of failing the request.
    reference_frame = None
    reference_file = request.files.get("reference_image")
    if reference_file is not None:
        reference_frame = decode_upload(reference_file)
        if reference_frame is None:
            logger.warning(
                "Could not decode reference image %r — continuing without it.",
                reference_file.filename,
            )

    category = normalize_category(
        request.form.get("category") or request.args.get("category")
    )

    try:
        # overlay="pre" — we need the masks, not a rendered overlay, so skip the
        # drawing work entirely.
        result = run_inference(frame, "pre", source="recommend")
        palette = recommend_colors(
            frame,
            result["detections"],
            reference_frame_bgr=reference_frame,
            category=category,
        )
    except ModelLoadError as exc:
        return jsonify({"success": False, "model_loaded": False, "error": str(exc)}), 503
    except Exception as exc:
        logger.exception("Colour recommendation failed")
        return jsonify({"success": False, "error": f"{type(exc).__name__}: {exc}"}), 500

    payload = {
        "success": True,
        "model_loaded": True,
        # --- spec contract ---
        "recommended": palette["recommended"],
        "alternatives": palette["alternatives"],
        # Fixed fallbacks — a copy so a caller mutating the response cannot
        # corrupt the module-level constant for every later request.
        "neutrals": [dict(color) for color in NEUTRAL_COLORS],
        # --- context the UI shows so the suggestion is explainable ---
        "dominant_color": palette["dominant_color"],
        "context_colors": palette["context_colors"],
        "context_source": palette["context_source"],
        "context_pixel_ratio": palette["context_pixel_ratio"],
        # Same transparency contract as dominant_color: say whether the optional
        # inputs actually reached the palette, so the UI never implies a
        # reference image or a demographic lean that was silently dropped.
        "reference_used": palette["reference_used"],
        "reference_weight": palette["reference_weight"],
        "reference_dominant_color": palette["reference_dominant_color"],
        "category_applied": palette["category_applied"],
        "wall_detected": result["wall_detected"],
        "wall_confidence": result["wall_confidence"],
        "wall_coverage": result["wall_coverage"],
        "detection_count": len(result["detections"]),
        "inference_ms": result["inference_ms"],
        "device": segmentation_model.device,
        "model": os.path.basename(segmentation_model.model_path),
    }
    return jsonify(payload)


# --------------------------------------------------------------------------- #
# API — POST /api/toolpath
#
# The stage between segmentation and the (not yet written) serial link: segment
# the frame, map the wall polygons into millimetres, subtract the non-paintable
# detections, raster-fill what is left, and hand back G-code.
#
# Calibration comes from the optional `corners` field. Without it the response
# says calibration_mode="uncalibrated_scale" and every millimetre figure in it
# is a scale assumption, not a measurement — the gantry does not exist yet, so
# that is the normal case today.
# --------------------------------------------------------------------------- #

def parse_corner_field(name: str) -> list | None:
    """Read an optional JSON corner array off the form/query string.

    Returns None when absent. Raises ``CalibrationError`` on malformed JSON so
    the caller answers 400 with the field name in the message.
    """
    raw = request.form.get(name) or request.args.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise CalibrationError(f"'{name}' is not valid JSON: {exc}") from exc
    if not isinstance(value, list):
        raise CalibrationError(
            f"'{name}' must be a JSON array of 4 [x, y] pairs, got "
            f"{type(value).__name__}."
        )
    return value


def calibration_from_request(width: int, height: int) -> WallCalibration:
    """Build the image->wall transform for this request.

    ``corners``      — 4 marker positions in image pixels (TL, TR, BR, BL).
    ``wall_corners`` — their measured positions on the wall in mm, same order.
                       Optional: defaults to the AURA_WALL_*_MM rectangle, i.e.
                       "those markers are the corners of a wall of the
                       configured size".

    With no ``corners`` at all this falls back to the uncalibrated scale.
    """
    image_corners = parse_corner_field("corners")
    if image_corners is None:
        return WallCalibration.uncalibrated(width, height, WALL_WIDTH_MM, WALL_HEIGHT_MM)

    wall_corners = parse_corner_field("wall_corners") or [
        [0.0, 0.0],
        [WALL_WIDTH_MM, 0.0],
        [WALL_WIDTH_MM, WALL_HEIGHT_MM],
        [0.0, WALL_HEIGHT_MM],
    ]
    return WallCalibration.from_corner_markers(image_corners, wall_corners, width, height)


@app.route("/api/toolpath", methods=["POST"])
def api_toolpath():
    if not segmentation_model.is_loaded:
        return model_unavailable()

    frame, error = frame_from_request()
    if error is not None:
        return error

    height, width = frame.shape[:2]
    try:
        calibration = calibration_from_request(width, height)
    except CalibrationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    try:
        # overlay="pre" — the masks are what we need; skip the drawing work.
        result = run_inference(frame, "pre", source="toolpath")

        wall_polygons = [
            calibration.polygon_to_mm(det["polygon"])
            for det in result["detections"]
            if det["is_wall"] and det["polygon"]
        ]
        obstacle_polygons = [
            calibration.polygon_to_mm(det["polygon"])
            for det in result["detections"]
            if not det["is_wall"] and det["polygon"]
        ]

        toolpath = generate_toolpath(wall_polygons, obstacle_polygons)
        gcode = events_to_gcode(toolpath["events"])
    except ModelLoadError as exc:
        return jsonify({"success": False, "model_loaded": False, "error": str(exc)}), 503
    except ToolpathError as exc:
        # Missing geometry dependency — the server cannot do this at all, which
        # is the same class of problem as missing weights.
        logger.error("Toolpath generation unavailable: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 503
    except CalibrationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except SoftLimitError as exc:
        # Clipping should have removed every unreachable move, so reaching here
        # means a bug upstream, not bad user input. Surfaced verbatim rather
        # than folded into the generic 500 so it is obvious in the logs.
        logger.error("Soft-limit violation while serializing G-code: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500
    except Exception as exc:
        logger.exception("Toolpath generation failed")
        return jsonify({"success": False, "error": f"{type(exc).__name__}: {exc}"}), 500

    payload = {
        "success": True,
        "model_loaded": True,
        # --- calibration ---
        "calibration_mode": calibration.calibration_mode,
        # Returned so a caller can store the solved transform and reuse it until
        # the camera or the workpiece moves. Nothing persists it server-side.
        "calibration": calibration.to_dict(),
        # --- what was found ---
        "wall_detected": result["wall_detected"],
        "wall_confidence": result["wall_confidence"],
        "wall_polygon_count": len(wall_polygons),
        "obstacle_polygon_count": len(obstacle_polygons),
        # The subtracted regions, in mm. Returned so a viewer can show what the
        # path routed around — the claim is only checkable if you can see the
        # obstacles next to the path that avoids them.
        "obstacle_polygons_mm": [
            [[round(x, 2), round(y, 2)] for x, y in polygon]
            for polygon in obstacle_polygons
        ],
        # --- reach ---
        # The X rail is shorter than most walls on purpose, so a wall that does
        # not fit is the normal case: the plan covers this gantry position and
        # `clipped_*` says how much is left for the next one.
        "was_clipped": toolpath["was_clipped"],
        "clipped_area_mm2": toolpath["clipped_area_mm2"],
        "clipped_pct": toolpath["clipped_pct"],
        "travel_envelope_mm": toolpath["travel_envelope_mm"],
        "travel_margin_mm": toolpath["travel_margin_mm"],
        # --- the plan ---
        "paintable_area_mm2": toolpath["paintable_area_mm2"],
        "row_count": toolpath["row_count"],
        "step_over_mm": toolpath["step_over_mm"],
        "total_paint_length_mm": toolpath["total_paint_length_mm"],
        "total_travel_length_mm": toolpath["total_travel_length_mm"],
        "bounds_mm": toolpath["bounds_mm"],
        # Both representations ship: `gcode` is what the machine will consume,
        # `events` is the same plan as geometry so the website can draw it on a
        # canvas without writing a G-code parser in JavaScript.
        "events": toolpath["events"],
        "gcode": gcode,
        "event_count": len(toolpath["events"]),
        # --- context ---
        "inference_ms": result["inference_ms"],
        "device": segmentation_model.device,
        "model": os.path.basename(segmentation_model.model_path),
        "using_fallback_model": segmentation_model.using_fallback,
    }
    return jsonify(payload)


# --------------------------------------------------------------------------- #
# API — GET /api/stream  (MJPEG)
# --------------------------------------------------------------------------- #

def mjpeg_frames(overlay: str):
    """Yield multipart MJPEG chunks from the webcam with live segmentation."""
    boundary = b"--frame\r\n"
    min_period = 1.0 / STREAM_FPS if STREAM_FPS > 0 else 0.0

    if not camera.acquire():
        _, err = camera.availability()
        frame = banner_frame(960, 540, ["Camera unavailable", (err or "")[:60]])
        yield boundary + b"Content-Type: image/jpeg\r\n\r\n" + encode_jpeg_bytes(frame) + b"\r\n"
        return

    try:
        while True:
            loop_start = time.perf_counter()

            ok, frame = camera.read()
            if not ok or frame is None:
                frame = banner_frame(960, 540, ["Lost camera frame", "Retrying..."])
                yield boundary + b"Content-Type: image/jpeg\r\n\r\n" + encode_jpeg_bytes(frame) + b"\r\n"
                time.sleep(0.5)
                continue

            if segmentation_model.is_loaded and overlay != "pre":
                try:
                    result = run_inference(frame, overlay, source="stream")
                    output = result["overlay_image"]
                except Exception as exc:
                    logger.warning("Stream inference failed: %s", exc)
                    output = frame
            else:
                output = frame

            try:
                jpeg = encode_jpeg_bytes(output)
            except Exception as exc:
                logger.warning("Stream encode failed: %s", exc)
                continue

            yield boundary + b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"

            elapsed = time.perf_counter() - loop_start
            if min_period > elapsed:
                time.sleep(min_period - elapsed)
    except GeneratorExit:
        # Browser navigated away / closed the <img>. Normal.
        pass
    finally:
        camera.release()


@app.route("/api/stream", methods=["GET"])
def api_stream():
    overlay = normalize_overlay(request.args.get("overlay"))
    logger.info("Stream opened (overlay=%s)", overlay)
    return Response(
        mjpeg_frames(overlay),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# --------------------------------------------------------------------------- #
# API — GET /api/status
# --------------------------------------------------------------------------- #

@app.route("/api/status", methods=["GET"])
def api_status():
    torch_facts = torch_info()
    model_status = segmentation_model.status()
    camera_ok, camera_error = camera.availability()

    if not model_status["model_loaded"]:
        robot_status, badge = "Error", "badge-error"
    elif camera.is_streaming:
        robot_status, badge = "Running", "badge-running"
    elif camera_ok:
        robot_status, badge = "Ready", "badge-connected"
    else:
        robot_status, badge = "Idle", "badge-idle"

    payload = {
        "online": True,
        "timestamp": time.time(),
        # Required fields
        "model_loaded": model_status["model_loaded"],
        "camera_available": camera_ok,
        "cuda_available": torch_facts["cuda_available"],
        "gpu_name": torch_facts["gpu_name"],
        # Extras the dashboard uses
        "model": os.path.basename(segmentation_model.model_path),
        "device": model_status["device"],
        "device_name": segmentation_model.device_name,
        "camera_index": camera.index,
        "camera_backend": camera.backend_name,
        "camera_error": camera_error,
        "camera_streaming": camera.is_streaming,
        "robot_status": robot_status,
        "robot_status_class": badge,
        "last_inference": telemetry.snapshot(),
        "torch_version": torch_facts["torch_version"],
        "torch_cuda_version": torch_facts["torch_cuda_version"],
        "gpu_memory_gb": torch_facts["gpu_memory_gb"],
    }
    payload.update(model_status)
    return jsonify(payload)


# --------------------------------------------------------------------------- #
# API — GET /api/capture  (single still from the webcam, segmented)
# Convenience for the "Open Camera" button on the color-recommendation page.
# --------------------------------------------------------------------------- #

@app.route("/api/capture", methods=["GET", "POST"])
def api_capture():
    if not segmentation_model.is_loaded:
        return (
            jsonify(
                {
                    "success": False,
                    "model_loaded": False,
                    "error": segmentation_model.error or "Model is not loaded.",
                }
            ),
            503,
        )

    frame = camera.grab_single_frame()
    if frame is None:
        _, err = camera.availability()
        return jsonify({"success": False, "error": err or "Camera unavailable."}), 503

    overlay = normalize_overlay(request.args.get("overlay"))
    result = run_inference(frame, overlay, source="capture")

    return jsonify(segmentation_response(frame, result, overlay))


# --------------------------------------------------------------------------- #
# Static hosting — serve the website from the same origin so the pages work at
# http://localhost:5000/ as well as straight off disk.
# --------------------------------------------------------------------------- #

@app.route("/")
def index():
    return send_from_directory(WEBSITE_DIR, "index.html")


@app.errorhandler(413)
def too_large(_e):
    return (
        jsonify(
            {
                "success": False,
                "error": f"Image exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB "
                         f"upload limit.",
            }
        ),
        413,
    )


# --------------------------------------------------------------------------- #
# Startup
# --------------------------------------------------------------------------- #

def startup_report() -> None:
    facts = torch_info()
    cam_ok, cam_err = camera.availability()
    line = "=" * 68

    print()
    print(line)
    print("  AURA — Autonomous Unified Robotic Adaptive · Backend API")
    print(line)
    print(f"  Server        : http://localhost:{PORT}")
    print(f"  Website       : http://localhost:{PORT}/index.html")
    print(f"  Project root  : {PROJECT_ROOT}")
    print("  " + "-" * 64)

    print(f"  PyTorch       : {facts['torch_version']} (CUDA build {facts['torch_cuda_version']})")
    if facts["cuda_available"]:
        print(f"  CUDA          : ACTIVE — {facts['gpu_name']} ({facts['gpu_memory_gb']} GB)")
    else:
        print("  CUDA          : NOT AVAILABLE — running on CPU (inference will be slow)")

    if segmentation_model.is_loaded:
        tag = "  [FALLBACK — not the fine-tuned AURA model]" if segmentation_model.using_fallback else ""
        print(f"  Model         : LOADED{tag}")
        print(f"                  {os.path.relpath(segmentation_model.model_path, PROJECT_ROOT)}")
        print(f"  Inference on  : {segmentation_model.device} ({segmentation_model.device_name})")
        print(f"  Task          : {segmentation_model.task}")
        classes = ", ".join(segmentation_model.names.values()) or "<none>"
        print(f"  Classes ({len(segmentation_model.names)})  : {classes[:200]}")
        if not segmentation_model.has_wall_class:
            print("  NOTE          : no class name matches a wall keyword — the largest")
            print("                  mask per frame is treated as the wall region.")
    else:
        print("  Model         : NOT LOADED")
        print(f"                  {segmentation_model.error}")

    print(f"  Camera        : {'AVAILABLE' if cam_ok else 'UNAVAILABLE'}"
          + (f" (index {camera.index}, {camera.backend_name})" if cam_ok else ""))
    if not cam_ok and cam_err:
        print(f"                  {cam_err}")

    print("  " + "-" * 64)
    print("  Endpoints     : POST /api/segment   GET /api/stream?overlay=pre|during|post")
    print("                  GET  /api/status    GET /api/capture")
    print("                  POST /api/recommend-colors")
    print("                  POST /api/toolpath")
    print(f"  CORS          : enabled for all origins (file:// pages included)")
    print(line)
    print()


if __name__ == "__main__":
    load_model()
    startup_report()
    # threaded=True is required: the MJPEG generator occupies one worker for the
    # whole life of the stream, and /api/status must stay answerable meanwhile.
    # use_reloader=False keeps the model from being loaded into memory twice.
    app.run(host=HOST, port=PORT, threaded=True, debug=False, use_reloader=False)
