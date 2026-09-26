"""
AURA — Smart region selection for the mask-correction tool.

Click a point, get a region. This is the *input method* for a manual mask
correction, not a replacement for it: the brush in ``mask_correction`` still
exists for everything smart select grabs wrongly, which is the whole reason the
correction feature exists in the first place.

Two engines
-----------
``sam``   **MobileSAM** (Zhang et al. 2023), a distilled Segment Anything
          (Kirillov et al. 2023) run through Ultralytics' own SAM predictor —
          already vendored in the ultralytics package AURA pins, so this is a
          40 MB weights download and **no new dependency**. Click a point and a
          promptable foundation model returns the object under it. Verified on
          the RTX 3050: clicking the wall returns the wall, clicking the door
          returns the door and not the wall.

``wand``  Flood fill in CIE Lab, i.e. a magic wand. No weights, no GPU, ~10 ms,
          works forever offline. Honest about what it is: colour region
          growing, not inference. It exists so a missing/failed SAM never
          leaves the operator with a dead button — the same graceful-
          degradation contract ``model_loader`` gives ``best.pt``.

``auto``  SAM if it is usable, wand otherwise. The endpoint reports which one
          actually ran, and the browser records *that* in the saved operation,
          so a replay never silently changes engines underneath a plan.

Why the result is memoised
--------------------------
A smart selection is stored as a **replayable prompt** (the click, not the
resulting outline), so a correction stays a few hundred bytes and survives being
replayed at a different resolution — the property that makes one correction work
across the Upload preview and the Toolpath plan. The cost is that every
``/api/toolpath`` re-plan re-runs every selection. A SAM decode is ~150-300 ms
on this GPU and corner-picking re-plans happen repeatedly, so results are cached
by (frame, engine, prompt). The preview click warms the cache and the plan that
follows is free.

VRAM
----
MobileSAM at ``imgsz=1024`` reserves ~2.3 GB alongside YOLOv8n-seg on the 4 GB
RTX 3050 — it fits, but with little headroom. ``AURA_SAM_IMGSZ`` lowers it and
``AURA_SAM_DEVICE=cpu`` sidesteps the GPU entirely. A CUDA OOM is caught, the
cache is dropped, and the request degrades to the wand rather than failing.
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
from collections import OrderedDict

import cv2
import numpy as np

logger = logging.getLogger("aura.smartselect")

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# Sits next to best.pt. Ultralytics will fetch it by bare name if the file is
# absent, but only with a network — so the local copy is what makes the demo
# venue's connectivity irrelevant, same rule as the no-CDN decision.
DEFAULT_SAM_PATH = os.path.join(PROJECT_ROOT, "website", "model", "mobile_sam.pt")
SAM_MODEL_PATH = os.environ.get("AURA_SAM_MODEL") or DEFAULT_SAM_PATH

SAM_IMGSZ = int(os.environ.get("AURA_SAM_IMGSZ", "1024"))
SAM_DEVICE = os.environ.get("AURA_SAM_DEVICE", "").strip().lower()

# Set AURA_SMART_SELECT=0 to force the wand everywhere (useful when demoing on a
# machine whose GPU is already committed).
SAM_ENABLED = os.environ.get("AURA_SMART_SELECT", "1").lower() not in ("0", "false", "no")

ENGINE_SAM = "sam"
ENGINE_WAND = "wand"
ENGINE_AUTO = "auto"
VALID_ENGINES = (ENGINE_AUTO, ENGINE_SAM, ENGINE_WAND)

# Wand tolerance is exposed 0-100 in the UI and mapped onto a Lab channel
# distance. 100 maps to 64, well past the point where a wall floods the whole
# frame, so the top of the slider is deliberately useless rather than clipped.
WAND_TOLERANCE_MAX_LAB = 64.0
DEFAULT_WAND_TOLERANCE = 18

# Speckle cleanup on a flood fill, in pixels of a frame's short side.
WAND_CLOSE_RATIO = 0.004

# Result cache. Entries are boolean masks; the byte cap matters more than the
# count because one 12 MP frame's mask is ~12 MB.
CACHE_MAX_ENTRIES = 24
CACHE_MAX_BYTES = 256 * 1024 * 1024


class SmartSelectError(ValueError):
    """Bad smart-select input. Subclasses ValueError so callers map it to 400."""


class SmartSelectUnavailable(RuntimeError):
    """The requested engine exists but could not run this time -> 503."""


# --------------------------------------------------------------------------- #
# Frame identity
# --------------------------------------------------------------------------- #

def frame_key(frame: np.ndarray) -> str:
    """A cheap content key for one decoded frame.

    Sampled rather than hashed in full: blake2b over a 12 MP frame costs more
    than the SAM decode the cache is meant to save. The strides are coprime so
    the sample is a lattice across the image rather than a few columns, and the
    shape is folded in, which is enough to tell one uploaded photo from another
    in a single-operator local demo.
    """
    sample = np.ascontiguousarray(frame[::13, ::7])
    digest = hashlib.blake2b(digest_size=16)
    digest.update(str(frame.shape).encode("ascii"))
    digest.update(sample.tobytes())
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# MobileSAM
# --------------------------------------------------------------------------- #

class SamSelector:
    """Lazily-loaded MobileSAM point-prompt segmenter.

    Constructed unconditionally and loaded on first use. Loading at import time
    would spend ~1.5 s and ~2 GB of VRAM on every server start for a feature
    most sessions never touch, so the cost is paid by the first click instead
    and reported through /api/status before then.
    """

    def __init__(self, model_path: str = SAM_MODEL_PATH) -> None:
        self.model_path = model_path
        self.predictor = None
        self.error: str | None = None
        self.device: str | None = None
        self._tried = False
        self._encoded_key: str | None = None
        # Ultralytics predictors hold per-image state in `set_image`, so two
        # requests must not interleave inside one. Flask's dev server is
        # threaded, hence the lock — same reasoning as SegmentationModel.
        self._lock = threading.RLock()

    # -- availability ----------------------------------------------------- #

    @property
    def is_loaded(self) -> bool:
        return self.predictor is not None

    @property
    def can_try(self) -> bool:
        """True if a load is worth attempting (or has already succeeded)."""
        if not SAM_ENABLED:
            return False
        if self.is_loaded:
            return True
        if self._tried:
            return False
        return os.path.isfile(self.model_path)

    def _resolve_device(self) -> str:
        if SAM_DEVICE:
            return SAM_DEVICE
        try:
            import torch

            return "cuda:0" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def load(self) -> bool:
        with self._lock:
            if self.is_loaded:
                return True
            if self._tried:
                return False
            self._tried = True

            if not SAM_ENABLED:
                self.error = "Smart select is disabled (AURA_SMART_SELECT=0)."
                return False
            if not os.path.isfile(self.model_path):
                rel = os.path.relpath(self.model_path, PROJECT_ROOT)
                self.error = (
                    f"MobileSAM weights not found at '{rel}'. Download "
                    f"mobile_sam.pt (38 MB) once with an internet connection and "
                    f"put it there; smart select falls back to the colour wand "
                    f"until then."
                )
                logger.warning(self.error)
                return False

            try:
                from ultralytics.models.sam import Predictor as SAMPredictor

                self.device = self._resolve_device()
                self.predictor = SAMPredictor(
                    overrides=dict(
                        conf=0.25,
                        task="segment",
                        mode="predict",
                        imgsz=SAM_IMGSZ,
                        model=self.model_path,
                        device=self.device,
                        verbose=False,
                        save=False,
                    )
                )
                logger.info(
                    "MobileSAM ready: %s on %s (imgsz=%d)",
                    os.path.basename(self.model_path), self.device, SAM_IMGSZ,
                )
                return True
            except Exception as exc:
                self.predictor = None
                self.error = f"Could not load MobileSAM: {type(exc).__name__}: {exc}"
                logger.error(self.error)
                return False

    # -- inference -------------------------------------------------------- #

    def _release_locked(self) -> None:
        if self.predictor is not None:
            try:
                self.predictor.reset_image()
            except Exception:
                pass
        self._encoded_key = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def predict(
        self, frame: np.ndarray, key: str, points_px: list[list[int]], labels: list[int]
    ) -> np.ndarray:
        """Point prompt -> boolean mask at frame resolution.

        Raises ``SmartSelectUnavailable`` when the engine is loaded but cannot
        answer right now (OOM, a broken predictor). Callers turn that into a 503
        rather than swapping engines behind the operator's back: a plan whose
        geometry silently changed engine is worse than a plan that says it
        failed.
        """
        with self._lock:
            if not self.load():
                raise SmartSelectUnavailable(self.error or "MobileSAM is not available.")

            try:
                # The encode is the expensive half and is per-image, so it is
                # held across calls for as long as the same frame keeps coming
                # back — which is exactly what a replayed correction does.
                if self._encoded_key != key:
                    self.predictor.reset_image()
                    self.predictor.set_image(frame)
                    self._encoded_key = key

                # The points MUST be nested one level: Ultralytics reads
                # `points=[p1, p2]` as two separate objects and answers with two
                # masks, while `points=[[p1, p2]]` reads them as two prompts for
                # ONE object. Flat is the shape that looks right and silently
                # breaks refinement — extra clicks return a second mask that
                # gets dropped, so shift-clicking appears to do nothing at all.
                result = self.predictor(points=[points_px], labels=[labels])[0]
                masks = result.masks
                if masks is None or len(masks.data) == 0:
                    return np.zeros(frame.shape[:2], dtype=bool)

                mask = masks.data[0].cpu().numpy()
            except Exception as exc:
                self._release_locked()
                name = type(exc).__name__
                if "OutOfMemory" in name or "CUDA out of memory" in str(exc):
                    raise SmartSelectUnavailable(
                        "The GPU ran out of memory during smart select. Lower "
                        "AURA_SAM_IMGSZ (try 512) or set AURA_SAM_DEVICE=cpu."
                    ) from exc
                raise SmartSelectUnavailable(f"Smart select failed: {name}: {exc}") from exc

        binary = mask > 0.5
        if binary.shape != frame.shape[:2]:
            binary = cv2.resize(
                binary.astype(np.uint8),
                (frame.shape[1], frame.shape[0]),
                interpolation=cv2.INTER_NEAREST,
            ).astype(bool)
        return binary

    def status(self) -> dict:
        return {
            "engine": ENGINE_SAM,
            "loaded": self.is_loaded,
            "available": self.can_try,
            "model": os.path.basename(self.model_path),
            "model_path": os.path.relpath(self.model_path, PROJECT_ROOT).replace("\\", "/"),
            "device": self.device,
            "imgsz": SAM_IMGSZ,
            "error": self.error,
        }


sam_selector = SamSelector()


# --------------------------------------------------------------------------- #
# Colour wand
# --------------------------------------------------------------------------- #

def wand_select(
    frame: np.ndarray, points_px: list[list[int]], labels: list[int], tolerance: int
) -> np.ndarray:
    """Flood fill from each positive point; subtract fills from negative ones.

    Runs in **CIE Lab**, matching the colour recommender's working space, so the
    tolerance is roughly perceptual rather than an RGB cube. ``FIXED_RANGE``
    compares every candidate pixel against the *seed* instead of its neighbour:
    a wall lit by a window drifts under the default relative mode and the fill
    walks off across the whole frame.
    """
    height, width = frame.shape[:2]
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    span = float(np.clip(tolerance, 0, 100)) / 100.0 * WAND_TOLERANCE_MAX_LAB
    diff = (span, span, span)
    flags = (
        4  # 4-connectivity: 8 leaks through single-pixel diagonal seams
        | cv2.FLOODFILL_MASK_ONLY
        | cv2.FLOODFILL_FIXED_RANGE
        | (255 << 8)
    )

    positive = np.zeros((height, width), dtype=bool)
    negative = np.zeros((height, width), dtype=bool)

    # FLOODFILL_MASK_ONLY leaves the image untouched, but floodFill still wants
    # a writable array. One copy up front rather than one per point — on a 12 MP
    # photo that is a 36 MB memcpy per click otherwise.
    canvas = lab.copy()

    for point, label in zip(points_px, labels):
        x = int(np.clip(point[0], 0, width - 1))
        y = int(np.clip(point[1], 0, height - 1))

        # floodFill wants a 2-pixel-larger mask and writes the region into it.
        scratch = np.zeros((height + 2, width + 2), dtype=np.uint8)
        cv2.floodFill(canvas, scratch, (x, y), 0, diff, diff, flags)
        region = scratch[1:-1, 1:-1] > 0

        if label:
            positive |= region
        else:
            negative |= region

    result = positive & ~negative
    if not result.any():
        return result

    # Close pinholes left by noise/JPEG artefacts inside an otherwise solid fill.
    radius = max(1, int(WAND_CLOSE_RATIO * min(height, width)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius + 1, 2 * radius + 1))
    closed = cv2.morphologyEx(result.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    return closed.astype(bool)


# --------------------------------------------------------------------------- #
# Result cache
# --------------------------------------------------------------------------- #

_cache: "OrderedDict[tuple, np.ndarray]" = OrderedDict()
_cache_bytes = 0
_cache_lock = threading.Lock()


def _cache_get(key: tuple) -> np.ndarray | None:
    with _cache_lock:
        mask = _cache.get(key)
        if mask is not None:
            _cache.move_to_end(key)
        return mask


def _cache_put(key: tuple, mask: np.ndarray) -> None:
    global _cache_bytes
    with _cache_lock:
        if key in _cache:
            return
        _cache[key] = mask
        _cache_bytes += mask.nbytes
        while _cache and (len(_cache) > CACHE_MAX_ENTRIES or _cache_bytes > CACHE_MAX_BYTES):
            _, evicted = _cache.popitem(last=False)
            _cache_bytes -= evicted.nbytes


def cache_stats() -> dict:
    with _cache_lock:
        return {"entries": len(_cache), "bytes": _cache_bytes}


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def normalize_engine(value: str | None) -> str:
    engine = (value or ENGINE_AUTO).strip().lower()
    if engine not in VALID_ENGINES:
        raise SmartSelectError(
            f"engine must be one of {', '.join(VALID_ENGINES)}, got {value!r}."
        )
    return engine


def resolve_engine(requested: str) -> str:
    """Which engine will actually run for this request."""
    if requested == ENGINE_WAND:
        return ENGINE_WAND
    if requested == ENGINE_SAM:
        return ENGINE_SAM
    return ENGINE_SAM if sam_selector.can_try else ENGINE_WAND


def select_region(
    frame: np.ndarray,
    points_norm: list[list[float]],
    labels: list[int],
    engine: str = ENGINE_AUTO,
    tolerance: int = DEFAULT_WAND_TOLERANCE,
    replay: bool = False,
) -> tuple[np.ndarray, str]:
    """Run one smart selection. Returns ``(boolean mask, engine that ran)``.

    ``replay`` marks a selection being re-run as part of an already-saved
    correction rather than made fresh. A fresh ``sam`` request may fall back to
    the wand and say so — the browser then records the wand as the operation's
    engine, so the fallback is a one-time decision. A *replay* may not: the
    saved operation names a concrete engine, and quietly answering with a
    different one would change the geometry driving the G-code. That case raises
    instead, and the operator is told to redo the selection.
    """
    if not points_norm:
        raise SmartSelectError("A smart selection needs at least one point.")
    if len(points_norm) != len(labels):
        raise SmartSelectError(
            f"points and labels must be the same length, got "
            f"{len(points_norm)} and {len(labels)}."
        )

    height, width = frame.shape[:2]
    points_px = [
        [int(round(min(max(float(x), 0.0), 1.0) * (width - 1))),
         int(round(min(max(float(y), 0.0), 1.0) * (height - 1)))]
        for x, y in points_norm
    ]
    labels = [1 if int(v) else 0 for v in labels]
    if not any(labels):
        raise SmartSelectError(
            "A smart selection needs at least one positive point — negative "
            "points only carve away from a region, they cannot define one."
        )

    tolerance = int(np.clip(tolerance, 0, 100))
    key_frame = frame_key(frame)
    wanted = resolve_engine(engine)

    if wanted == ENGINE_SAM and not sam_selector.can_try:
        if engine == ENGINE_SAM and replay:
            raise SmartSelectError(
                "This correction contains a MobileSAM selection but MobileSAM is "
                f"not available on this server ({sam_selector.error or 'no weights'}). "
                "Re-run the smart selection so the plan matches what you can see."
            )
        wanted = ENGINE_WAND

    cache_key = (
        key_frame,
        wanted,
        tuple(map(tuple, points_px)),
        tuple(labels),
        tolerance if wanted == ENGINE_WAND else -1,
    )
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached, wanted

    if wanted == ENGINE_SAM:
        try:
            mask = sam_selector.predict(frame, key_frame, points_px, labels)
        except SmartSelectUnavailable:
            if engine == ENGINE_SAM:
                # Explicitly asked for SAM and it is loaded but failed. Do not
                # substitute — see the docstring.
                raise
            logger.warning("MobileSAM unavailable, falling back to the colour wand.")
            wanted = ENGINE_WAND
            cache_key = (key_frame, wanted, tuple(map(tuple, points_px)),
                         tuple(labels), tolerance)
            mask = wand_select(frame, points_px, labels, tolerance)
    else:
        mask = wand_select(frame, points_px, labels, tolerance)

    _cache_put(cache_key, mask)
    return mask, wanted


def status() -> dict:
    """Smart-select availability, for /api/status and the startup banner."""
    sam = sam_selector.status()
    engines = [ENGINE_WAND]
    if sam["available"]:
        engines.insert(0, ENGINE_SAM)
    return {
        "available": True,  # the wand always is
        "default_engine": resolve_engine(ENGINE_AUTO),
        "engines": engines,
        "sam": sam,
        "wand": {"engine": ENGINE_WAND, "available": True,
                 "default_tolerance": DEFAULT_WAND_TOLERANCE},
        "cache": cache_stats(),
    }
