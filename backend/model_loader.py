"""
AURA — YOLOv8 segmentation model loader.

Responsibilities
----------------
* Resolve the weights path relative to the project root (never hardcoded).
* Load the Ultralytics YOLOv8 instance-segmentation model.
* Select CUDA when available, fall back to CPU, and log which device is used.
* Survive a missing / corrupt ``best.pt`` — the server must still start and
  report a clear error through ``/api/status`` instead of crashing.

Version-compatibility notes
---------------------------
Verified against the project venv on 2026-07-30:

    Python 3.11.5 · torch 2.5.1+cu121 · torchvision 0.20.1+cu121
    ultralytics 8.4.90 · opencv-python 5.0.0.93 · numpy 2.4.4

Risks to watch when anything is upgraded:

1. torch / torchvision must move together AND keep the same CUDA suffix.
   ``torch 2.5.1+cu121`` pairs only with ``torchvision 0.20.1+cu121``. A plain
   ``pip install torch`` pulls the CPU (or a cu12x) wheel from PyPI and
   silently breaks CUDA — always install from the cu121 index URL. See
   requirements.txt.
2. The +cu121 wheels bundle their own CUDA runtime, so the *driver* must
   support CUDA 12.1 or newer (NVIDIA driver >= 530). The RTX 3050 laptop GPU
   used for AURA deployment satisfies this. A driver older than 530 shows up as
   ``torch.cuda.is_available() == False`` with no other error.
3. Ultralytics >= 8.3 loads checkpoints with ``weights_only=False`` internally.
   On torch >= 2.6 the default flipped to ``weights_only=True``, which makes
   third-party .pt files raise ``UnpicklingError``. We are on torch 2.5.1 so
   this does not bite yet — but pin torch before upgrading, or upgrade
   ultralytics in the same step.
4. numpy 2.x requires torch >= 2.3 and opencv >= 4.10. Do not downgrade numpy
   below 2.0 without also rebuilding the torch wheel.
5. 4 GB VRAM (RTX 3050 laptop) is enough for YOLOv8n/s-seg inference at
   imgsz=640. If a larger variant (m/l/x) is ever trained on Kaggle, expect
   CUDA OOM here and lower AURA_IMGSZ or fall back to CPU.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

import numpy as np

logger = logging.getLogger("aura.model")

# --------------------------------------------------------------------------- #
# Paths — everything is derived from this file's location, nothing hardcoded.
# --------------------------------------------------------------------------- #

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, "website", "model", "best.pt")

# Where the trained weights live. Override with AURA_MODEL_PATH if you keep a
# second checkpoint around (e.g. comparing Kaggle runs for Chapter 4).
MODEL_PATH = os.environ.get("AURA_MODEL_PATH") or DEFAULT_MODEL_PATH

# Optional stand-in so the backend can be exercised before best.pt exists.
# Off by default: set AURA_ALLOW_FALLBACK=1 to enable. The fallback is the
# COCO-pretrained yolov8n-seg.pt at the project root (the Phase-1 zero-shot
# baseline from the vault notes) — useful for wiring/UI tests, NOT for results.
ALLOW_FALLBACK = os.environ.get("AURA_ALLOW_FALLBACK", "0").lower() in ("1", "true", "yes")
FALLBACK_MODEL_PATH = os.environ.get("AURA_FALLBACK_MODEL") or os.path.join(
    PROJECT_ROOT, "yolov8n-seg.pt"
)

# --------------------------------------------------------------------------- #
# Inference defaults
# --------------------------------------------------------------------------- #

DEFAULT_CONF = float(os.environ.get("AURA_CONF", "0.25"))
DEFAULT_IOU = float(os.environ.get("AURA_IOU", "0.45"))
DEFAULT_IMGSZ = int(os.environ.get("AURA_IMGSZ", "640"))

# Class names that count as "the paintable wall". The custom Roboflow dataset
# may label it "wall", "Wall", "paintable-wall", ... so we match by substring.
# Override with a comma-separated AURA_WALL_CLASSES.
WALL_KEYWORDS = tuple(
    kw.strip().lower()
    for kw in os.environ.get("AURA_WALL_CLASSES", "wall,paintable,surface").split(",")
    if kw.strip()
)

# Names that must NEVER count as wall, checked BEFORE the positive keywords.
# This matters because the trained AURA model's two classes are "wall" and
# "non-paintable" — and "non-paintable" *contains* the substring "paintable".
# Without this veto every obstacle is scored as paintable wall, which silently
# drives wall_coverage toward 1.0 and makes the colour preview tint windows,
# outlets and trim. Override with a comma-separated AURA_NON_WALL_CLASSES.
NON_WALL_KEYWORDS = tuple(
    kw.strip().lower()
    for kw in os.environ.get(
        "AURA_NON_WALL_CLASSES",
        "non-paintable,non_paintable,nonpaintable,not-paintable,unpaintable,obstacle",
    ).split(",")
    if kw.strip()
)


class ModelLoadError(RuntimeError):
    """Raised internally when weights cannot be loaded; never escapes to Flask."""


class SegmentationModel:
    """Thin wrapper around ``ultralytics.YOLO`` with graceful failure.

    The object is always constructible. If the weights are missing or broken,
    ``is_loaded`` stays False and ``error`` holds a human-readable message that
    the API surfaces verbatim — the server keeps running either way.
    """

    def __init__(self, model_path: str = MODEL_PATH) -> None:
        self.model_path: str = model_path
        self.model: Any = None
        self.error: str | None = None
        self.device: str = "cpu"
        self.device_name: str = "CPU"
        self.names: dict[int, str] = {}
        self.task: str | None = None
        self.using_fallback: bool = False
        self.loaded_at: float | None = None
        self.warmup_ms: float | None = None

        # Ultralytics models are not documented as thread-safe, and Flask's dev
        # server is threaded (stream + status + segment can overlap). One lock
        # around predict() keeps frames from interleaving on the GPU.
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Loading
    # ------------------------------------------------------------------ #

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def load(self) -> bool:
        """Load weights. Returns True on success; records ``error`` on failure."""
        self.model = None
        self.error = None
        self.using_fallback = False

        path = self._resolve_weights()
        if path is None:
            return False

        try:
            import torch
            from ultralytics import YOLO
        except ImportError as exc:  # pragma: no cover - environment problem
            self.error = (
                f"Required package missing: {exc}. Install with "
                f"`pip install -r backend/requirements.txt`."
            )
            logger.error(self.error)
            return False

        # Device selection: CUDA if the driver + wheel agree, else CPU.
        forced = os.environ.get("AURA_DEVICE", "").strip().lower()
        if forced:
            self.device = forced
        elif torch.cuda.is_available():
            self.device = "cuda:0"
        else:
            self.device = "cpu"

        try:
            model = YOLO(path)
            model.to(self.device)
        except Exception as exc:
            self.error = (
                f"Failed to load weights from {path}: {type(exc).__name__}: {exc}"
            )
            logger.error(self.error)
            # A CUDA-side failure is often just this GPU; retry on CPU so a demo
            # can still run rather than dying on stage.
            if self.device != "cpu":
                logger.warning("Retrying model load on CPU...")
                try:
                    model = YOLO(path)
                    model.to("cpu")
                    self.device = "cpu"
                    self.error = None
                except Exception as cpu_exc:
                    self.error = (
                        f"Failed to load weights from {path} on both CUDA and CPU: "
                        f"{type(cpu_exc).__name__}: {cpu_exc}"
                    )
                    logger.error(self.error)
                    return False
            else:
                return False

        self.model = model
        self.model_path = path
        self.names = dict(getattr(model, "names", {}) or {})
        self.task = getattr(model, "task", None)
        self.loaded_at = time.time()

        if self.device.startswith("cuda"):
            try:
                idx = int(self.device.split(":")[1]) if ":" in self.device else 0
                self.device_name = torch.cuda.get_device_name(idx)
            except Exception:
                self.device_name = "CUDA device"
        else:
            self.device_name = "CPU"

        logger.info("Model loaded: %s", self.model_path)
        logger.info("Device: %s (%s)", self.device, self.device_name)
        logger.info("Task: %s | classes: %s", self.task, self.names or "<none>")

        if self.task != "segment":
            logger.warning(
                "Model task is '%s', not 'segment'. AURA needs instance-segmentation "
                "masks; the API will fall back to bounding boxes and report "
                "masks_available=false.",
                self.task,
            )

        self._warmup()
        return True

    def _resolve_weights(self) -> str | None:
        """Pick the weights file, or record a clear error and return None."""
        if os.path.isfile(self.model_path):
            return self.model_path

        rel = os.path.relpath(self.model_path, PROJECT_ROOT)
        if ALLOW_FALLBACK and os.path.isfile(FALLBACK_MODEL_PATH):
            self.using_fallback = True
            logger.warning(
                "Trained weights not found at %s — falling back to the COCO "
                "baseline %s because AURA_ALLOW_FALLBACK is set. Results from "
                "this model are NOT the fine-tuned AURA model.",
                rel,
                os.path.relpath(FALLBACK_MODEL_PATH, PROJECT_ROOT),
            )
            return FALLBACK_MODEL_PATH

        self.error = (
            f"Model weights not found at '{rel}'. Train the model on Kaggle, "
            f"download best.pt, and place it there. (Set AURA_ALLOW_FALLBACK=1 to "
            f"run against the COCO-pretrained yolov8n-seg.pt baseline instead.)"
        )
        logger.error(self.error)
        return None

    def _warmup(self) -> None:
        """One dummy pass so the first real request isn't paying CUDA init cost."""
        try:
            blank = np.zeros((DEFAULT_IMGSZ, DEFAULT_IMGSZ, 3), dtype=np.uint8)
            start = time.perf_counter()
            self.predict(blank)
            self.warmup_ms = (time.perf_counter() - start) * 1000.0
            logger.info("Warmup inference: %.0f ms", self.warmup_ms)
        except Exception as exc:  # non-fatal
            logger.warning("Warmup pass failed (continuing anyway): %s", exc)

    # ------------------------------------------------------------------ #
    # Inference
    # ------------------------------------------------------------------ #

    def predict(
        self,
        image_bgr: np.ndarray,
        conf: float = DEFAULT_CONF,
        iou: float = DEFAULT_IOU,
        imgsz: int = DEFAULT_IMGSZ,
    ):
        """Run inference on one BGR frame and return the Ultralytics Results.

        Raises ``ModelLoadError`` if the model never loaded — callers turn that
        into a 503 rather than a traceback.
        """
        if not self.is_loaded:
            raise ModelLoadError(self.error or "Model is not loaded.")

        with self._lock:
            results = self.model.predict(
                source=image_bgr,
                conf=conf,
                iou=iou,
                imgsz=imgsz,
                device=self.device,
                verbose=False,
                retina_masks=True,  # masks at input resolution, not 160x160
            )
        return results[0]

    # ------------------------------------------------------------------ #
    # Class helpers
    # ------------------------------------------------------------------ #

    def is_wall_class(self, class_name: str) -> bool:
        name = (class_name or "").lower().strip()
        # Negative match wins: "non-paintable" must not be read as "paintable".
        if any(kw in name for kw in NON_WALL_KEYWORDS):
            return False
        return any(kw in name for kw in WALL_KEYWORDS)

    @property
    def has_wall_class(self) -> bool:
        """True if any class in the model looks like the paintable wall.

        When False, the API infers the wall as the largest-area mask and flags
        it with ``wall_class_inferred`` so the UI never claims false certainty.
        """
        return any(self.is_wall_class(n) for n in self.names.values())

    def status(self) -> dict:
        """Serializable snapshot for /api/status."""
        return {
            "model_loaded": self.is_loaded,
            "model_path": os.path.relpath(self.model_path, PROJECT_ROOT).replace("\\", "/"),
            "model_error": self.error,
            "using_fallback_model": self.using_fallback,
            "task": self.task,
            "masks_available": self.task == "segment",
            "class_names": {int(k): v for k, v in self.names.items()},
            "wall_classes_detected": self.has_wall_class,
            "device": self.device,
            "warmup_ms": round(self.warmup_ms, 1) if self.warmup_ms else None,
        }


# --------------------------------------------------------------------------- #
# Module-level singleton — imported by app.py
# --------------------------------------------------------------------------- #

segmentation_model = SegmentationModel()


def load_model() -> SegmentationModel:
    """Load (or reload) the shared model instance and return it."""
    segmentation_model.load()
    return segmentation_model


def torch_info() -> dict:
    """CUDA / GPU facts for /api/status. Never raises."""
    info = {
        "torch_version": None,
        "torch_cuda_version": None,
        "cuda_available": False,
        "gpu_name": None,
        "gpu_memory_gb": None,
        "gpu_count": 0,
    }
    try:
        import torch

        info["torch_version"] = torch.__version__
        info["torch_cuda_version"] = torch.version.cuda
        info["cuda_available"] = bool(torch.cuda.is_available())
        if info["cuda_available"]:
            info["gpu_count"] = torch.cuda.device_count()
            info["gpu_name"] = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            info["gpu_memory_gb"] = round(props.total_memory / (1024 ** 3), 1)
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not query torch/CUDA info: %s", exc)
    return info
