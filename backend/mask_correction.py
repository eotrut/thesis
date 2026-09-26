"""
AURA — Manual mask correction (brush tool).

Human-in-the-loop patch applied to the segmentation output *after* YOLOv8
inference and *before* anything downstream consumes it. The panel asked for it
at the 2026-08-08 proposal defense as a safety net for whatever the model still
misses while the training set grows from 300 images toward ~1,000; it is a
stopgap alongside fine-tuning, not a replacement for it.

Pipeline position
-----------------
    segmentation_model.predict
        -> parse_detections           (app.py)
        -> resolve_wall               (app.py)
        -> apply_correction()         <- this module
        -> render_overlay / polygon_to_mm / colour clustering

Because the patch lands on the detection list itself, every consumer of that
list gets the corrected mask for free: the overlay images, the mm-space
polygons that become G-code, and the non-wall clustering the colour recommender
runs. There is one corrected mask per image, not one per view.

Two ways to draw a correction
-----------------------------
``brush``  A freehand stroke: a polyline plus a radius.
``smart``  A *click*. The point is handed to ``smart_select``, which answers
           with a region — MobileSAM when its weights are present, a Lab flood
           fill otherwise. Shift/right-click adds further positive/negative
           points to refine the same selection.

Both are stored the same way and composite identically; ``smart`` is an input
method for the same correction, not a separate feature. What is stored is the
**prompt** (the click and its settings), never the resulting outline — see
below.

Why a stroke list and not a rasterised bitmap
---------------------------------------------
The payload is the operations themselves, in normalized (0-1) image
coordinates, rather than a PNG of the finished correction:

* ~1 KB of JSON per correction instead of a few hundred KB of bitmap on every
  request, and it rides in a form field next to ``corners`` rather than needing
  a second multipart file.
* Resolution-independent. The same stroke list replays onto a thumbnail-sized
  preview canvas and onto the full-resolution frame the server segments, which
  is what lets a correction drawn in Upload / Playback carry into the Toolpath
  planner untouched.
* Reversible client-side: undo is popping the last stroke, which a flattened
  bitmap cannot offer.

The cost is that the server has to rasterise, which is a handful of OpenCV
draws — cheap next to the ~100 ms inference it follows. A ``smart`` operation
pays more (a SAM decode is ~150-300 ms), which is why ``smart_select`` memoises
results by (frame, prompt): the click that made the selection warms the cache
and every later replay of the same correction is free.

Brush geometry
--------------
``radius`` is normalized against the image **width** only, and the rasteriser
scales it by width for both axes, so the brush stays circular in pixel space on
a non-square frame. The client draws with the identical convention
(``lineWidth = 2 * radius * canvasWidth``, round caps and joins), so its preview
and this rasterisation agree.

Semantics
---------
``add``   — "this is paintable wall". Unions into the wall mask, and is
            subtracted from any non-paintable detection it covers: claiming a
            region as paintable has to also drop an obstacle's claim on it, or
            the toolpath would still route around it.
``erase`` — "this is not paintable". Subtracted from the wall masks, and the
            part that actually overlapped wall is re-emitted as a synthetic
            non-paintable region.

Strokes composite in order with last-writer-wins per pixel, so erasing over an
earlier add undoes it exactly.

Why erase becomes an obstacle rather than only a hole
-----------------------------------------------------
A detection carries a single-ring polygon, so an erase in the *middle* of a
wall region would vanish the moment the mask was reduced back to its outer
contour — the toolpath would happily paint straight over it. Emitting the
erased area as a non-paintable region instead routes the raster fill around it
through the same subtraction that already handles windows and trim. The binary
``_mask`` stays hole-accurate for the overlay renderer either way.
"""

from __future__ import annotations

import json
import logging

import cv2
import numpy as np

from smart_select import (
    DEFAULT_WAND_TOLERANCE,
    SmartSelectError,
    SmartSelectUnavailable,
    normalize_engine,
    select_region,
)

logger = logging.getLogger("aura.correction")

# --------------------------------------------------------------------------- #
# Payload limits
#
# A correction is drawn by hand, so these are far above anything a person can
# produce with a mouse; they exist so a malformed or hostile payload cannot turn
# into unbounded rasterisation work.
# --------------------------------------------------------------------------- #

# v1 carried `strokes` (brush only). v2 carries `ops`, which may also be smart
# selections. v1 payloads are still accepted and read as all-brush, so a stale
# browser tab degrades to "your brush strokes still work" rather than a 400.
CORRECTION_VERSION = 2
SUPPORTED_VERSIONS = (1, 2)

KIND_BRUSH = "brush"
KIND_SMART = "smart"
VALID_KINDS = (KIND_BRUSH, KIND_SMART)

MAX_STROKES = 512
MAX_POINTS_PER_STROKE = 4096
MAX_TOTAL_POINTS = 20000

# Each smart op costs an engine run on replay (memoised, but the first pass is
# real work), so this is much tighter than the brush limit.
MAX_SMART_OPS = 32
MAX_POINTS_PER_SMART_OP = 32

# Radius as a fraction of image width. The floor keeps a stroke from rasterising
# to nothing; the ceiling keeps one drag from redefining the whole frame.
MIN_RADIUS_NORM = 0.001
MAX_RADIUS_NORM = 0.25

VALID_MODES = ("add", "erase")

# Regions smaller than this are rasterisation slivers — a stroke clipping the
# corner of a mask — not something anyone meant to draw.
MIN_REGION_AREA_RATIO = 2e-5
MIN_REGION_AREA_PX = 32

# Contour simplification tolerance, as a fraction of the contour's perimeter.
# Shared with parse_detections so a corrected polygon is simplified exactly like
# a model one: if the two diverged, a correction would change polygon fidelity
# as a side effect of being applied.
POLYGON_EPSILON_RATIO = 0.004


class CorrectionError(ValueError):
    """Malformed correction payload. Subclasses ValueError so callers map it to 400.

    Deliberately *not* the graceful-degradation treatment that
    ``reference_image`` gets on /api/recommend-colors. A correction is an
    explicit act of the operator overriding the model, so dropping a broken one
    with a warning would show them an uncorrected plan that looks like their
    correction did nothing.
    """


# --------------------------------------------------------------------------- #
# Mask -> polygon
#
# Lives here rather than in app.py because both the model-detection parser and
# the corrector have to produce byte-identical polygon shape and simplification.
# --------------------------------------------------------------------------- #

def simplify_polygon(points, width: int, height: int) -> list[list[float]]:
    """Reduce a mask contour to a compact, normalized (0-1) polygon.

    The frontend clips its colour-preview canvas with this and the toolpath maps
    it into millimetres, so a few dozen points is plenty — shipping every
    contour pixel would bloat the JSON by hundreds of KB per detection.
    """
    if points is None or len(points) < 3:
        return []
    contour = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
    epsilon = POLYGON_EPSILON_RATIO * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    if len(approx) < 3:
        approx = np.asarray(points, dtype=np.float32).reshape(-1, 2)
    return [
        [round(float(x) / max(width, 1), 5), round(float(y) / max(height, 1), 5)]
        for x, y in approx
    ]


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

class Stroke:
    """One brush stroke: a polyline plus a radius, both in normalized units."""

    __slots__ = ("mode", "radius", "points")
    kind = KIND_BRUSH

    def __init__(self, mode: str, radius: float, points: list[tuple[float, float]]) -> None:
        self.mode = mode
        self.radius = radius
        self.points = points

    def render(self, frame: np.ndarray) -> tuple[np.ndarray, str | None]:
        height, width = frame.shape[:2]
        layer = np.zeros((height, width), dtype=np.uint8)
        _draw_stroke(layer, self, width, height)
        return layer.astype(bool), None


class SmartOp:
    """One smart selection: a click (plus refinements), resolved by an engine.

    Stores the **prompt**, not the outline it produced. That is what keeps a
    correction a few hundred bytes and lets it replay at any resolution — the
    property the Upload-to-Toolpath carry-over depends on. ``engine`` is the
    concrete engine the browser saw run, not ``auto``, so a replay can never
    answer with a different one than the operator approved.
    """

    __slots__ = ("mode", "engine", "points", "labels", "tolerance")
    kind = KIND_SMART

    def __init__(self, mode: str, engine: str, points: list[tuple[float, float]],
                 labels: list[int], tolerance: int) -> None:
        self.mode = mode
        self.engine = engine
        self.points = points
        self.labels = labels
        self.tolerance = tolerance

    def render(self, frame: np.ndarray) -> tuple[np.ndarray, str | None]:
        mask, engine_used = select_region(
            frame,
            [list(p) for p in self.points],
            list(self.labels),
            engine=self.engine,
            tolerance=self.tolerance,
            replay=True,
        )
        return mask, engine_used


class MaskCorrection:
    """An ordered list of operations, rasterisable against a frame."""

    def __init__(self, ops: list) -> None:
        self.ops = ops

    def __bool__(self) -> bool:
        return bool(self.ops)

    # `strokes` kept as a name for the brush subset — several callers and the
    # response stats still speak in strokes, and a smart click is not one.
    @property
    def strokes(self) -> list[Stroke]:
        return [op for op in self.ops if op.kind == KIND_BRUSH]

    @property
    def smart_ops(self) -> list[SmartOp]:
        return [op for op in self.ops if op.kind == KIND_SMART]

    @property
    def op_count(self) -> int:
        return len(self.ops)

    @property
    def stroke_count(self) -> int:
        return len(self.strokes)

    @property
    def smart_count(self) -> int:
        return len(self.smart_ops)

    @property
    def add_stroke_count(self) -> int:
        return sum(1 for op in self.ops if op.mode == "add")

    @property
    def erase_stroke_count(self) -> int:
        return sum(1 for op in self.ops if op.mode == "erase")

    def rasterize(self, frame: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Flatten the operations into ``(add, erase, engines_used)``.

        add and erase are disjoint by construction: each operation paints into
        its own layer and clears the other, so the last operation over a pixel
        decides what that pixel means. That is what makes erasing back over an
        earlier add — brush or smart select — undo it exactly.

        Takes the frame rather than a size because a smart operation needs the
        pixels: its stored prompt is a click, and resolving it back into a
        region is the engine's job, not geometry's.
        """
        height, width = frame.shape[:2]
        add = np.zeros((height, width), dtype=np.uint8)
        erase = np.zeros((height, width), dtype=np.uint8)
        engines: list[str] = []

        for op in self.ops:
            painted, engine_used = op.render(frame)
            if engine_used:
                engines.append(engine_used)
            if not painted.any():
                continue
            if op.mode == "add":
                add[painted] = 1
                erase[painted] = 0
            else:
                erase[painted] = 1
                add[painted] = 0

        return add.astype(bool), erase.astype(bool), engines


def _draw_stroke(layer: np.ndarray, stroke: Stroke, width: int, height: int) -> None:
    """Rasterise one stroke into ``layer`` as 1s.

    Round caps and joins are drawn explicitly (a filled circle at every point)
    rather than relying on OpenCV's thick-polyline join behaviour, so the result
    matches the browser's ``lineCap: "round"`` preview exactly.
    """
    radius_px = max(1, int(round(stroke.radius * width)))
    points = np.array(
        [[int(round(x * width)), int(round(y * height))] for x, y in stroke.points],
        dtype=np.int32,
    )

    if len(points) > 1:
        cv2.polylines(layer, [points], False, 1, thickness=2 * radius_px)
    for point in points:
        cv2.circle(layer, (int(point[0]), int(point[1])), radius_px, 1, -1)


def _coerce_point(value, where: str) -> tuple[float, float]:
    try:
        x, y = value
        x = float(x)
        y = float(y)
    except (TypeError, ValueError) as exc:
        raise CorrectionError(
            f"{where} must be a pair of numbers like [x, y], got {value!r}."
        ) from exc
    if not (np.isfinite(x) and np.isfinite(y)):
        raise CorrectionError(f"{where} contains a non-finite coordinate.")
    # Strokes are allowed to run off the edge of the frame — that is what
    # happens when you brush past the border — so clamp rather than reject.
    return min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0)


def _parse_points(item: dict, where: str, limit: int) -> list[tuple[float, float]]:
    raw_points = item.get("points")
    if not isinstance(raw_points, list) or not raw_points:
        raise CorrectionError(f"{where}.points must be a non-empty array of [x, y] pairs.")
    if len(raw_points) > limit:
        raise CorrectionError(
            f"{where}.points has {len(raw_points)} points; the limit here is {limit}."
        )
    return [_coerce_point(p, f"{where}.points[{i}]") for i, p in enumerate(raw_points)]


def _parse_mode(item: dict, where: str) -> str:
    mode = str(item.get("mode", "")).strip().lower()
    if mode not in VALID_MODES:
        raise CorrectionError(
            f"{where}.mode must be one of {', '.join(VALID_MODES)}, got {item.get('mode')!r}."
        )
    return mode


def _parse_brush(item: dict, where: str) -> Stroke:
    try:
        radius = float(item.get("radius"))
    except (TypeError, ValueError) as exc:
        raise CorrectionError(
            f"{where}.radius must be a number (fraction of image width), got "
            f"{item.get('radius')!r}."
        ) from exc
    if not np.isfinite(radius) or radius <= 0:
        raise CorrectionError(f"{where}.radius must be positive, got {radius}.")

    return Stroke(
        mode=_parse_mode(item, where),
        radius=min(max(radius, MIN_RADIUS_NORM), MAX_RADIUS_NORM),
        points=_parse_points(item, where, MAX_POINTS_PER_STROKE),
    )


def _parse_smart(item: dict, where: str) -> SmartOp:
    try:
        engine = normalize_engine(item.get("engine"))
    except SmartSelectError as exc:
        raise CorrectionError(f"{where}.{exc}") from exc

    points = _parse_points(item, where, MAX_POINTS_PER_SMART_OP)

    raw_labels = item.get("labels")
    if raw_labels is None:
        # A bare click list with no labels means "all of these are positive",
        # which is the common single-click case.
        labels = [1] * len(points)
    elif not isinstance(raw_labels, list) or len(raw_labels) != len(points):
        raise CorrectionError(
            f"{where}.labels must be an array the same length as points "
            f"({len(points)}), got {raw_labels!r}."
        )
    else:
        labels = [1 if v else 0 for v in raw_labels]

    if not any(labels):
        raise CorrectionError(
            f"{where} has no positive point — negative points only carve away "
            f"from a region, they cannot define one."
        )

    try:
        tolerance = int(item.get("tolerance", DEFAULT_WAND_TOLERANCE))
    except (TypeError, ValueError) as exc:
        raise CorrectionError(
            f"{where}.tolerance must be an integer 0-100, got {item.get('tolerance')!r}."
        ) from exc

    return SmartOp(
        mode=_parse_mode(item, where),
        engine=engine,
        points=points,
        labels=labels,
        tolerance=min(max(tolerance, 0), 100),
    )


def parse_correction(raw: str | None) -> MaskCorrection | None:
    """Read the optional ``mask_correction`` form field.

    Returns None when absent or empty. Raises ``CorrectionError`` on anything
    malformed so the caller can answer 400 naming the problem.

    Accepts v2 (``ops``, brush + smart) and v1 (``strokes``, brush only). v1 is
    still read rather than rejected so a browser tab left open across a server
    upgrade degrades to "the brush half still works" instead of a hard failure
    mid-demo.
    """
    if raw is None or not str(raw).strip():
        return None

    try:
        payload = json.loads(raw)
    except ValueError as exc:
        raise CorrectionError(f"'mask_correction' is not valid JSON: {exc}") from exc

    if isinstance(payload, list):
        # Tolerated shorthand: a bare operation array with no envelope.
        payload = {"version": CORRECTION_VERSION, "ops": payload}
    if not isinstance(payload, dict):
        raise CorrectionError(
            f"'mask_correction' must be a JSON object with an 'ops' array, got "
            f"{type(payload).__name__}."
        )

    version = payload.get("version", CORRECTION_VERSION)
    try:
        version = int(version)
    except (TypeError, ValueError) as exc:
        raise CorrectionError(
            f"'mask_correction.version' must be an integer, got {version!r}."
        ) from exc
    if version not in SUPPORTED_VERSIONS:
        raise CorrectionError(
            f"Unsupported mask_correction version {version}; this server speaks "
            f"{' and '.join(str(v) for v in SUPPORTED_VERSIONS)}."
        )

    raw_ops = payload.get("ops")
    field = "ops"
    if raw_ops is None:
        raw_ops = payload.get("strokes")
        field = "strokes"
    if raw_ops is None:
        raise CorrectionError("'mask_correction' is missing 'ops'.")
    if not isinstance(raw_ops, list):
        raise CorrectionError(
            f"'mask_correction.{field}' must be an array, got {type(raw_ops).__name__}."
        )
    if len(raw_ops) > MAX_STROKES:
        raise CorrectionError(
            f"'mask_correction.{field}' has {len(raw_ops)} entries; the limit is "
            f"{MAX_STROKES}."
        )

    ops: list = []
    total_points = 0
    smart_count = 0

    for index, item in enumerate(raw_ops):
        where = f"mask_correction.{field}[{index}]"
        if not isinstance(item, dict):
            raise CorrectionError(f"{where} must be an object, got {type(item).__name__}.")

        # v1 entries have no `kind`; everything in a v1 payload is a brush.
        kind = str(item.get("kind", KIND_BRUSH)).strip().lower()
        if kind not in VALID_KINDS:
            raise CorrectionError(
                f"{where}.kind must be one of {', '.join(VALID_KINDS)}, got "
                f"{item.get('kind')!r}."
            )
        if kind == KIND_SMART and version < 2:
            raise CorrectionError(
                f"{where} is a smart selection, which needs mask_correction "
                f"version 2; this payload declares version {version}."
            )

        if kind == KIND_BRUSH:
            op = _parse_brush(item, where)
        else:
            smart_count += 1
            if smart_count > MAX_SMART_OPS:
                raise CorrectionError(
                    f"'mask_correction' carries more than {MAX_SMART_OPS} smart "
                    f"selections; each one costs an engine run on every replay."
                )
            op = _parse_smart(item, where)

        total_points += len(op.points)
        if total_points > MAX_TOTAL_POINTS:
            raise CorrectionError(
                f"'mask_correction' carries more than {MAX_TOTAL_POINTS} points in total."
            )
        ops.append(op)

    if not ops:
        return None

    correction = MaskCorrection(ops)
    logger.info(
        "Mask correction: %d op(s) — %d brush, %d smart (%d add, %d erase)",
        correction.op_count,
        correction.stroke_count,
        correction.smart_count,
        correction.add_stroke_count,
        correction.erase_stroke_count,
    )
    return correction


# --------------------------------------------------------------------------- #
# Application
# --------------------------------------------------------------------------- #

def _regions(mask: np.ndarray, width: int, height: int, min_area_px: int) -> list[dict]:
    """Split a boolean mask into one entry per connected blob.

    Splitting matters: an erase stroke can cut one wall detection into two, and
    reducing the result to a single outer contour would silently drop half the
    wall from the plan.

    Each blob's ``mask`` keeps its interior holes (the filled contour is
    intersected back against the source); its ``polygon`` is the outer ring
    only, which is the single-ring shape every downstream consumer expects.
    """
    regions: list[dict] = []
    if not mask.any():
        return regions

    binary = mask.astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        filled = np.zeros_like(binary)
        cv2.drawContours(filled, [contour], -1, 1, -1)
        blob = filled.astype(bool) & mask
        area = int(blob.sum())
        if area < min_area_px:
            continue

        polygon = simplify_polygon(contour.reshape(-1, 2), width, height)
        if not polygon:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        regions.append(
            {
                "mask": blob.astype(np.uint8),
                "polygon": polygon,
                "bbox": [float(x), float(y), float(x + w), float(y + h)],
                "area": area,
            }
        )

    return regions


def _respawn(det: dict, new_mask: np.ndarray, width: int, height: int,
             frame_area: float, min_area_px: int) -> list[dict]:
    """Rebuild one model detection after its mask was cut by a correction.

    Side effect worth knowing about: this re-derives polygons from the binary
    mask, one per connected blob, whereas ``parse_detections`` takes the single
    ring Ultralytics exports in ``masks.xy``. A model mask that was already two
    disjoint blobs therefore comes back as two polygons here and one there — so
    a correction can nudge the planned area slightly even in a region no stroke
    touched. The respawned decomposition is the more faithful of the two (it is
    the same mask the overlay renders), so this is left as-is rather than
    truncated to match; the uncorrected single-polygon export is the weaker
    path, and changing it would move already-recorded baseline figures.
    """
    out: list[dict] = []
    for region in _regions(new_mask, width, height, min_area_px):
        piece = dict(det)
        piece["_mask"] = region["mask"]
        piece["polygon"] = region["polygon"]
        piece["bbox"] = [round(v, 1) for v in region["bbox"]]
        piece["area_ratio"] = round(region["area"] / frame_area, 4)
        piece["corrected"] = True
        out.append(piece)
    return out


def _manual(mask: np.ndarray, is_wall: bool, class_name: str, width: int, height: int,
            frame_area: float, min_area_px: int) -> list[dict]:
    """Build synthetic detections for a region the operator drew.

    ``confidence`` is None, not 1.0. These regions did not come from the model,
    and a fabricated score would flow straight into ``wall_confidence`` and the
    dashboard telemetry — reporting the operator's certainty as the model's.
    ``is_wall`` is set explicitly rather than matched from the name, so the
    substring collision that ``non-paintable``/``paintable`` caused in the
    class matcher cannot reappear here.
    """
    out: list[dict] = []
    for region in _regions(mask, width, height, min_area_px):
        out.append(
            {
                "class_id": None,
                "class_name": class_name,
                "confidence": None,
                "bbox": [round(v, 1) for v in region["bbox"]],
                "polygon": region["polygon"],
                "area_ratio": round(region["area"] / frame_area, 4),
                "is_wall": is_wall,
                "source": "manual",
                "corrected": True,
                "_mask": region["mask"],
            }
        )
    return out


def apply_correction(
    detections: list[dict],
    correction: MaskCorrection,
    frame: np.ndarray,
) -> tuple[list[dict], dict]:
    """Patch a detection list with the operator's correction.

    Returns ``(detections, stats)``. The detection list keeps the same shape as
    ``parse_detections`` produces, so every downstream consumer is unchanged;
    entries gain ``source`` ("model" or "manual") and ``corrected`` so a caller
    can still tell the model's output from the human's.

    Takes the frame, not just its size: a smart-select operation stores a click
    and has to be resolved back into a region against the actual pixels.
    """
    height, width = frame.shape[:2]
    frame_area = float(width * height) or 1.0
    min_area_px = max(MIN_REGION_AREA_PX, int(MIN_REGION_AREA_RATIO * frame_area))

    add, erase, engines = correction.rasterize(frame)

    # The wall as the MODEL saw it, before any of this — both effective regions
    # are defined against it, so it has to be captured up front.
    wall_union = np.zeros((height, width), dtype=bool)
    for det in detections:
        mask = det.get("_mask")
        if det.get("is_wall") and mask is not None:
            wall_union |= mask.astype(bool)

    # Only the parts that actually change anything. Brushing "add" over a region
    # the model already called wall, or "erase" over bare background, is a no-op
    # and should not manufacture a region.
    added_region = add & ~wall_union
    removed_region = erase & wall_union

    corrected: list[dict] = []
    for det in detections:
        mask = det.get("_mask")
        if mask is None:
            corrected.append(det)
            continue

        current = mask.astype(bool)
        # Wall loses what was erased; an obstacle loses what was claimed as
        # paintable, or the toolpath would keep routing around a region the
        # operator just said to paint.
        cut = erase if det.get("is_wall") else add
        if not (current & cut).any():
            corrected.append(det)
            continue

        corrected.extend(
            _respawn(det, current & ~cut, width, height, frame_area, min_area_px)
        )

    manual_wall = _manual(
        added_region, True, "wall (manual)", width, height, frame_area, min_area_px
    )
    manual_obstacle = _manual(
        removed_region, False, "non-paintable (manual)", width, height,
        frame_area, min_area_px,
    )
    corrected.extend(manual_wall)
    corrected.extend(manual_obstacle)

    added_px = int(added_region.sum())
    removed_px = int(removed_region.sum())

    stats = {
        "op_count": correction.op_count,
        "stroke_count": correction.stroke_count,
        "smart_count": correction.smart_count,
        # Which engine(s) actually resolved the smart selections on this run.
        # Reported, not assumed: the browser records the engine it saw, and this
        # is the server confirming the same one ran.
        "engines_used": sorted(set(engines)),
        "add_stroke_count": correction.add_stroke_count,
        "erase_stroke_count": correction.erase_stroke_count,
        "added_px": added_px,
        "removed_px": removed_px,
        "added_area_ratio": round(added_px / frame_area, 4),
        "removed_area_ratio": round(removed_px / frame_area, 4),
        "added_region_count": len(manual_wall),
        "removed_region_count": len(manual_obstacle),
        # What the model alone said, kept alongside so a corrected response can
        # never be mistaken for a measurement of the model.
        "model_detection_count": len(detections),
        "model_wall_detected": bool(wall_union.any()),
    }

    logger.info(
        "Correction applied: +%.2f%% / -%.2f%% of frame (%d added, %d removed region(s))",
        100.0 * stats["added_area_ratio"],
        100.0 * stats["removed_area_ratio"],
        stats["added_region_count"],
        stats["removed_region_count"],
    )
    return corrected, stats
