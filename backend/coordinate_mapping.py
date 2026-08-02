"""
AURA — Image-space to wall-space coordinate mapping.

Turns the normalized (0-1) polygons that ``/api/segment`` returns into real
millimetre coordinates on the wall, so the toolpath generator can plan in the
units the gantry actually moves in.

Coordinate conventions
----------------------
Input  — normalized image space: x,y in 0-1, origin at the TOP-LEFT of the
         frame, +y DOWN (this is what ``parse_detections`` produces).
Output — wall space in millimetres, origin at the wall's top-left marker,
         +x right, +y DOWN.

Keeping +y down in wall space means the mapping is a pure change of scale in
the uncalibrated case and never silently mirrors the plan. Whether the gantry
firmware wants its origin at the bottom-left is a machine-frame concern and
belongs in the serial stage (Phase 2), not here.

Two calibration modes
---------------------
``from_corner_markers`` — the real one. Four image-pixel points (the wall's
corner markers) are paired with their four known millimetre positions and
solved into a perspective transform, so an off-axis or tilted camera still
produces a square plan. ``calibration_mode = "homography"``.

``uncalibrated`` — the fallback used while the gantry does not physically
exist yet. It assumes the frame is filled edge-to-edge by a wall of a
configured size and scales straight into it. There is no perspective
correction and no way to verify the scale, so it reports
``calibration_mode = "uncalibrated_scale"`` and every consumer (and the API
response) is expected to flag those numbers as unverified.

Both modes are stored as one 3x3 matrix mapping normalized image coordinates
directly to millimetres — an axis-aligned scale is just a homography with no
perspective terms — so ``point_to_mm`` has a single code path and
``to_dict``/``from_dict`` round-trip either mode identically.

Persistence
-----------
``to_dict``/``from_dict`` exist because the calibration transform is meant to
be solved once and reused until the camera or the workpiece moves. Nothing
writes it to disk yet; the endpoint returns it in its response so a caller can
hold on to it.
"""

from __future__ import annotations

import logging
import os

import cv2
import numpy as np

logger = logging.getLogger("aura.mapping")

# --------------------------------------------------------------------------- #
# Configuration
#
# Wall size used ONLY by the uncalibrated fallback — with real corner markers
# the physical size comes from the marker positions instead. Defaults are a
# 1 m x 1 m test panel, which is the size the prototype is being planned
# against until the gantry frame is built.
# --------------------------------------------------------------------------- #

WALL_WIDTH_MM = float(os.environ.get("AURA_WALL_WIDTH_MM", "1000"))
WALL_HEIGHT_MM = float(os.environ.get("AURA_WALL_HEIGHT_MM", "1000"))

# Below this the perspective divisor is treated as degenerate: the point has
# been projected onto (or past) the transform's horizon line, where millimetre
# coordinates are meaningless rather than merely inaccurate.
MIN_PERSPECTIVE_W = 1e-9

CORNER_LABELS = ("top-left", "top-right", "bottom-right", "bottom-left")


class CalibrationError(ValueError):
    """Bad calibration input. Subclasses ValueError so callers can map it to 400."""


# --------------------------------------------------------------------------- #
# Input coercion — every public constructor funnels through these, so the
# errors a user sees name the offending field instead of surfacing a numpy or
# cv2 message.
# --------------------------------------------------------------------------- #

def _coerce_point(value, label: str) -> tuple[float, float]:
    try:
        x, y = value
        return float(x), float(y)
    except (TypeError, ValueError) as exc:
        raise CalibrationError(
            f"{label} must be a pair of numbers like [x, y], got {value!r}."
        ) from exc


def _coerce_corners(points, label: str) -> np.ndarray:
    """4 point pairs -> (4,2) float32, in TL, TR, BR, BL order."""
    if points is None:
        raise CalibrationError(f"{label} is required (4 points).")
    try:
        listed = list(points)
    except TypeError as exc:
        raise CalibrationError(f"{label} must be a list of 4 [x, y] pairs.") from exc

    if len(listed) != 4:
        raise CalibrationError(
            f"{label} must have exactly 4 points in "
            f"{', '.join(CORNER_LABELS)} order, got {len(listed)}."
        )
    return np.array(
        [_coerce_point(p, f"{label}[{i}] ({CORNER_LABELS[i]})") for i, p in enumerate(listed)],
        dtype=np.float32,
    )


# --------------------------------------------------------------------------- #
# WallCalibration
# --------------------------------------------------------------------------- #

class WallCalibration:
    """Maps normalized (0-1) image points to millimetres on the wall.

    Construct through ``from_corner_markers`` or ``uncalibrated`` rather than
    calling ``__init__`` directly — both build the same normalized-image-to-mm
    matrix and only differ in how it was derived.
    """

    def __init__(
        self,
        matrix,
        image_width: int,
        image_height: int,
        calibration_mode: str,
        image_corners_px: list[list[float]] | None = None,
        wall_corners_mm: list[list[float]] | None = None,
    ) -> None:
        self.matrix = np.asarray(matrix, dtype=np.float64).reshape(3, 3)
        self.image_width = int(image_width)
        self.image_height = int(image_height)
        self.calibration_mode = calibration_mode
        # Kept for round-tripping and for the thesis appendix — the solved
        # matrix alone does not show what was measured to produce it.
        self.image_corners_px = image_corners_px
        self.wall_corners_mm = wall_corners_mm

    # ------------------------------------------------------------------ #
    # Constructors
    # ------------------------------------------------------------------ #

    @classmethod
    def from_corner_markers(
        cls,
        image_corners_px,
        wall_corners_mm,
        image_width: int,
        image_height: int,
    ) -> "WallCalibration":
        """Solve a perspective transform from 4 point correspondences.

        ``image_corners_px`` are pixel positions of the wall's corner markers in
        the frame; ``wall_corners_mm`` are the same corners' measured positions
        on the wall. Both must be ordered top-left, top-right, bottom-right,
        bottom-left.
        """
        if image_width <= 0 or image_height <= 0:
            raise CalibrationError(
                f"Image size must be positive, got {image_width}x{image_height}."
            )

        src_px = _coerce_corners(image_corners_px, "corners")
        dst_mm = _coerce_corners(wall_corners_mm, "wall_corners")

        try:
            px_to_mm = cv2.getPerspectiveTransform(src_px, dst_mm)
        except cv2.error as exc:
            raise CalibrationError(
                f"Could not solve a perspective transform from those corners "
                f"({exc}). Three collinear or duplicated points will do this."
            ) from exc

        # Fold normalized->pixel into the solved pixel->mm transform so the
        # stored matrix consumes the same 0-1 polygons the API hands out.
        norm_to_px = np.array(
            [[float(image_width), 0.0, 0.0],
             [0.0, float(image_height), 0.0],
             [0.0, 0.0, 1.0]],
            dtype=np.float64,
        )
        matrix = px_to_mm.astype(np.float64) @ norm_to_px

        if not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-12:
            raise CalibrationError(
                "Those corners produce a degenerate transform. Check that the 4 "
                "points are distinct, not collinear, and ordered "
                f"{', '.join(CORNER_LABELS)}."
            )

        calibration = cls(
            matrix=matrix,
            image_width=image_width,
            image_height=image_height,
            calibration_mode="homography",
            image_corners_px=src_px.astype(float).tolist(),
            wall_corners_mm=dst_mm.astype(float).tolist(),
        )
        logger.info(
            "Calibrated by corner markers: %dx%d px -> %.0fx%.0f mm envelope",
            image_width, image_height,
            float(dst_mm[:, 0].max() - dst_mm[:, 0].min()),
            float(dst_mm[:, 1].max() - dst_mm[:, 1].min()),
        )
        return calibration

    @classmethod
    def uncalibrated(
        cls,
        image_width: int,
        image_height: int,
        wall_width_mm: float = WALL_WIDTH_MM,
        wall_height_mm: float = WALL_HEIGHT_MM,
    ) -> "WallCalibration":
        """Fallback scale used when no physical corner markers exist.

        Stretches the full image bounds onto a ``wall_width_mm`` x
        ``wall_height_mm`` rectangle with the origin at its top-left. Axis
        aligned, so it corrects nothing: a tilted camera, a wall that does not
        fill the frame, or a wrong configured size all pass through as scale
        error. Results are only ever indicative — hence the distinct
        ``calibration_mode``.
        """
        if image_width <= 0 or image_height <= 0:
            raise CalibrationError(
                f"Image size must be positive, got {image_width}x{image_height}."
            )
        if wall_width_mm <= 0 or wall_height_mm <= 0:
            raise CalibrationError(
                f"Wall size must be positive, got "
                f"{wall_width_mm}x{wall_height_mm} mm. Check AURA_WALL_WIDTH_MM "
                f"/ AURA_WALL_HEIGHT_MM."
            )

        width_mm = float(wall_width_mm)
        height_mm = float(wall_height_mm)
        matrix = np.array(
            [[width_mm, 0.0, 0.0],
             [0.0, height_mm, 0.0],
             [0.0, 0.0, 1.0]],
            dtype=np.float64,
        )

        logger.info(
            "Uncalibrated scale: full frame (%dx%d px) assumed to be %.0fx%.0f mm",
            image_width, image_height, width_mm, height_mm,
        )
        return cls(
            matrix=matrix,
            image_width=image_width,
            image_height=image_height,
            calibration_mode="uncalibrated_scale",
            image_corners_px=[[0.0, 0.0],
                              [float(image_width), 0.0],
                              [float(image_width), float(image_height)],
                              [0.0, float(image_height)]],
            wall_corners_mm=[[0.0, 0.0],
                             [width_mm, 0.0],
                             [width_mm, height_mm],
                             [0.0, height_mm]],
        )

    # ------------------------------------------------------------------ #
    # Mapping
    # ------------------------------------------------------------------ #

    @property
    def is_verified(self) -> bool:
        """True only for a transform solved from measured corner markers."""
        return self.calibration_mode == "homography"

    def point_to_mm(self, x_norm: float, y_norm: float) -> tuple[float, float]:
        """One normalized (0-1) image point -> (x_mm, y_mm) on the wall."""
        x = float(x_norm)
        y = float(y_norm)
        m = self.matrix

        w = m[2, 0] * x + m[2, 1] * y + m[2, 2]
        if abs(w) < MIN_PERSPECTIVE_W:
            raise CalibrationError(
                f"Point ({x:.4f}, {y:.4f}) projects to infinity under this "
                f"calibration — the corner markers do not describe the plane "
                f"this point lies in."
            )

        # float() rather than the numpy scalars the matrix multiply produces —
        # np.float64 is not JSON-serializable and would fail at the response
        # boundary rather than here.
        x_mm = float((m[0, 0] * x + m[0, 1] * y + m[0, 2]) / w)
        y_mm = float((m[1, 0] * x + m[1, 1] * y + m[1, 2]) / w)
        return x_mm, y_mm

    def polygon_to_mm(self, polygon_norm) -> list[tuple[float, float]]:
        """A normalized polygon ([[x, y], ...]) -> [(x_mm, y_mm), ...]."""
        if not polygon_norm:
            return []
        return [
            self.point_to_mm(*_coerce_point(point, f"polygon point {i}"))
            for i, point in enumerate(polygon_norm)
        ]

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        """JSON-safe snapshot — solve once, reuse until the camera moves."""
        return {
            "calibration_mode": self.calibration_mode,
            "matrix": [[float(v) for v in row] for row in self.matrix],
            "image_width": self.image_width,
            "image_height": self.image_height,
            "image_corners_px": self.image_corners_px,
            "wall_corners_mm": self.wall_corners_mm,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WallCalibration":
        """Rebuild from ``to_dict`` output."""
        if not isinstance(data, dict):
            raise CalibrationError("Calibration data must be a JSON object.")
        try:
            matrix = np.asarray(data["matrix"], dtype=np.float64).reshape(3, 3)
        except KeyError as exc:
            raise CalibrationError("Calibration data is missing 'matrix'.") from exc
        except (TypeError, ValueError) as exc:
            raise CalibrationError(f"Calibration 'matrix' must be 3x3: {exc}") from exc

        if not np.isfinite(matrix).all():
            raise CalibrationError("Calibration 'matrix' contains non-finite values.")

        return cls(
            matrix=matrix,
            image_width=int(data.get("image_width", 0)),
            image_height=int(data.get("image_height", 0)),
            calibration_mode=str(data.get("calibration_mode", "homography")),
            image_corners_px=data.get("image_corners_px"),
            wall_corners_mm=data.get("wall_corners_mm"),
        )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<WallCalibration {self.calibration_mode} "
            f"{self.image_width}x{self.image_height}px>"
        )
