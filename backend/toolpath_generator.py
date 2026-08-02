"""
AURA — Toolpath generation and G-code serialization.

Takes the millimetre polygons produced by ``coordinate_mapping`` and plans the
spray path over them, then serializes that plan into CNC-style G-code for the
gantry controller.

Pipeline position
-----------------
    /api/segment detections
        -> coordinate_mapping.WallCalibration.polygon_to_mm
        -> generate_toolpath()          <- this module
        -> events_to_gcode()            <- this module
        -> serial link to the Arduino   (Phase 2, not built yet)

Strategy
--------
Boustrophedon ("as the ox ploughs") raster fill, the standard coverage pattern
for a spray end-effector on a 2-axis gantry:

1. Union the wall regions, then subtract the union of the non-paintable
   regions. Windows, doors, outlets and trim become holes in the paintable
   geometry rather than special cases in the path logic — routing around them
   falls out of the geometry for free.
2. Sweep horizontal scan lines across the result, spaced by the step-over.
3. Intersect each scan line with the paintable geometry. A row crossing a hole
   comes back as several disjoint spans; each span is one paint stroke and the
   gaps between them are travel moves with the spray off.
4. Reverse direction every other row so the end of one row is next to the start
   of the next, instead of driving the full width of the wall dry.

Reach, and why clipping is not an error path
-------------------------------------------
The paintable geometry is clipped to the gantry's travel envelope before any
row is generated. The X rail is 4.5 ft — deliberately shorter than most walls —
so covering a full wall is a multi-position workflow: paint what this position
reaches, slide the gantry over, re-calibrate, paint the next section. "The mask
extends past what I can reach" is therefore the normal case, not a failure, and
the clipped-away area is reported so the operator knows how much is left.

Clipping bounds against the RAILS, not the calibration marker quad. The markers
define the pixel->mm mapping and nothing more; they can be placed imprecisely or
deliberately mark a smaller test area, so they are not a safe statement about
where the machine can physically move.

Why shapely
-----------
The subtract-then-slice step is the whole job, and doing it by hand means
implementing polygon clipping and even-odd span sorting correctly for concave
shapes with holes — exactly the code that is easy to get subtly wrong and hard
to defend in a thesis. shapely is a thin binding over GEOS, is pure geometry
with no CUDA or numeric-stack coupling, and is already used for this by every
comparable CNC/CAM pipeline.

Step-over
---------
``step_over_mm = nozzle_width_mm * (1 - overlap)``. Passes must overlap or the
seam between them shows as a stripe once the paint dries; 20% is the usual
starting point for airless spray and is tuned on the real rig later.

Units are millimetres throughout, +y down, matching ``coordinate_mapping``.
"""

from __future__ import annotations

import logging
import math
import os

logger = logging.getLogger("aura.toolpath")

# shapely is imported defensively for the same reason model_loader tolerates a
# missing best.pt: app.py imports this module at startup, and a missing
# dependency must not take the whole server (and /api/segment with it) down.
# The failure surfaces per-request instead, with an install hint.
try:
    from shapely.geometry import LineString, Polygon, box
    from shapely.ops import unary_union

    SHAPELY_ERROR: str | None = None
except ImportError as exc:  # pragma: no cover - environment problem
    LineString = Polygon = box = unary_union = None  # type: ignore[assignment]
    SHAPELY_ERROR = (
        f"shapely is not installed ({exc}). Install it with "
        f"`pip install -r backend/requirements.txt`."
    )
    logger.error(SHAPELY_ERROR)


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# PLACEHOLDER — the spray assembly is not finalised. 25 mm is the fan width of
# the off-the-shelf nozzle the prototype is being costed around; measure the
# real deposition width on the built rig (spray a test card at the working
# stand-off distance) and set AURA_NOZZLE_WIDTH_MM from that before quoting any
# coverage figure in the paper.
NOZZLE_WIDTH_MM = float(os.environ.get("AURA_NOZZLE_WIDTH_MM", "25"))

# Fraction of a pass covered again by the next one. 0.2 = 20% overlap.
SPRAY_OVERLAP = float(os.environ.get("AURA_SPRAY_OVERLAP", "0.2"))

if not 0.0 <= SPRAY_OVERLAP < 1.0:
    logger.warning(
        "AURA_SPRAY_OVERLAP=%s is outside [0, 1) — clamping. 1.0 or more means "
        "a zero/negative step-over, which is not a path.",
        SPRAY_OVERLAP,
    )
    SPRAY_OVERLAP = min(max(SPRAY_OVERLAP, 0.0), 0.95)

STEP_OVER_MM = NOZZLE_WIDTH_MM * (1.0 - SPRAY_OVERLAP)

# --------------------------------------------------------------------------- #
# Reachable travel envelope
#
# The gantry's rails, NOT the calibration marker quad. The four markers define
# the pixel->mm mapping only; they are not a statement about where the machine
# can physically move (they can be placed slightly off, or deliberately mark a
# smaller test area). Clipping has to bound against the hardware.
#
# X is intentionally shorter than most walls: 4.5 ft of rail against a wall that
# is usually wider. Full coverage is a MULTI-POSITION workflow — paint what this
# position reaches, slide the gantry over, re-calibrate, paint the next section.
# That is why geometry outside the envelope is clipped and reported rather than
# treated as an error; on most real walls it is the normal case.
# --------------------------------------------------------------------------- #

TRAVEL_X_MM = float(os.environ.get("AURA_TRAVEL_X_MM", "1371.6"))   # 4.5 ft rail
TRAVEL_Y_MM = float(os.environ.get("AURA_TRAVEL_Y_MM", "2743.2"))   # 9 ft rail

# PROVISIONAL — homing / limit-switch clearance kept clear at each end. The
# frame is not built, so this has never been measured; 50 mm is a placeholder.
# Measure the real clearance once the limit switches are installed and set
# AURA_TRAVEL_MARGIN_MM from it before any live run.
TRAVEL_MARGIN_MM = float(os.environ.get("AURA_TRAVEL_MARGIN_MM", "50"))

# Slack on the soft-limit backstop. G-code is emitted at 2 dp, so anything below
# 0.01 mm is float noise at the boundary rather than a real out-of-range move.
SOFT_LIMIT_TOLERANCE_MM = 0.01

# A scan line is extended this far past the geometry's bounding box so it
# cleanly crosses the boundary instead of starting exactly on it, where
# floating-point comparison decides whether the first span exists.
EDGE_PAD_MM = 1.0

# Spans shorter than this are numerical slivers where a scan line clips a
# corner, not real strokes. At a 25 mm nozzle, half a millimetre of travel
# deposits nothing and only makes the gantry stutter.
MIN_SPAN_MM = 0.5

# Below this two positions are the same point, so no move is emitted.
MIN_MOVE_MM = 1e-6


class ToolpathError(RuntimeError):
    """Toolpath generation is unavailable (missing dependency).

    Invalid *arguments* raise ``ValueError`` instead — the distinction lets the
    API answer 503 for "this server cannot do it" and 500 for "that input was
    wrong".
    """


class SoftLimitError(ValueError):
    """A move outside the machine's physical travel reached serialization.

    Clipping should already have removed everything unreachable, so this only
    fires on a calibration or arithmetic error. It is raised rather than
    emitted on purpose: a bad coordinate that reaches the controller is a
    gantry driving into its end stop, so the failure has to be loud.
    """


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #

def _require_shapely() -> None:
    if SHAPELY_ERROR is not None:
        raise ToolpathError(SHAPELY_ERROR)


def _to_polygon(points, label: str):
    """One [(x_mm, y_mm), ...] ring -> a valid shapely polygon, or None.

    Mask contours arrive simplified by ``approxPolyDP`` and can be
    self-intersecting; ``buffer(0)`` is the standard GEOS repair for that and
    may legitimately return a MultiPolygon, which unions fine downstream.
    """
    if points is None or len(points) < 3:
        return None
    try:
        polygon = Polygon([(float(x), float(y)) for x, y in points])
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
    except Exception as exc:
        logger.warning("Skipping unusable %s polygon: %s", label, exc)
        return None

    if polygon.is_empty or polygon.area <= 0.0:
        return None
    return polygon


def _union(polygons, label: str):
    """Union a list of coordinate rings into one geometry (may be empty)."""
    geoms = [g for g in (_to_polygon(p, label) for p in (polygons or [])) if g is not None]
    if not geoms:
        return None
    return unary_union(geoms)


def travel_envelope(
    travel_x_mm: float | None = None,
    travel_y_mm: float | None = None,
    margin_mm: float | None = None,
) -> tuple[float, float, float, float]:
    """The reachable rectangle in wall-frame mm, as ``(x0, y0, x1, y1)``.

    Origin (0, 0) is the gantry's home corner with +x right and +y down — the
    same frame ``coordinate_mapping`` emits, whose origin is the calibration's
    top-left corner. Marking the top-left corner marker at the home corner is
    what keeps those two origins the same point; see the note in
    ``coordinate_mapping``'s module docstring.
    """
    travel_x = float(TRAVEL_X_MM if travel_x_mm is None else travel_x_mm)
    travel_y = float(TRAVEL_Y_MM if travel_y_mm is None else travel_y_mm)
    margin = float(TRAVEL_MARGIN_MM if margin_mm is None else margin_mm)

    if not math.isfinite(travel_x) or not math.isfinite(travel_y):
        raise ValueError(
            f"Travel limits must be finite, got {travel_x} x {travel_y} mm. "
            f"Check AURA_TRAVEL_X_MM / AURA_TRAVEL_Y_MM."
        )
    if margin < 0 or not math.isfinite(margin):
        raise ValueError(
            f"AURA_TRAVEL_MARGIN_MM must be zero or positive, got {margin}."
        )
    if 2 * margin >= travel_x or 2 * margin >= travel_y:
        raise ValueError(
            f"A {margin} mm margin at each end leaves no reachable area inside "
            f"a {travel_x} x {travel_y} mm travel. Lower "
            f"AURA_TRAVEL_MARGIN_MM or check the travel limits."
        )

    return (margin, margin, travel_x - margin, travel_y - margin)


def _row_spans(geometry) -> list[tuple[float, float]]:
    """Horizontal-cut geometry -> [(x_start, x_end), ...] sorted left to right.

    The intersection of a line with a polygon is a LineString when the row
    crosses a solid band, a MultiLineString when a hole splits the row, and a
    GeometryCollection when it also grazes a vertex (which contributes Points —
    dropped, they are not strokes).
    """
    spans: list[tuple[float, float]] = []
    if geometry is None or geometry.is_empty:
        return spans

    parts = getattr(geometry, "geoms", None)
    parts = list(parts) if parts is not None else [geometry]

    for part in parts:
        if part.is_empty or part.geom_type != "LineString":
            continue
        min_x, _, max_x, _ = part.bounds
        if (max_x - min_x) >= MIN_SPAN_MM:
            spans.append((float(min_x), float(max_x)))

    spans.sort()
    return spans


def _distance(a, b) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _point(x: float, y: float) -> list[float]:
    # 3 dp is well below the mechanical resolution of the gantry and keeps the
    # event list readable; G-code is emitted at 2 dp anyway.
    return [round(float(x), 3), round(float(y), 3)]


def _clip_fields(
    travel_x: float,
    travel_y: float,
    margin: float,
    clipped_area_mm2: float = 0.0,
    clipped_pct: float = 0.0,
) -> dict:
    """The envelope-clipping half of the result, shared by every return path."""
    return {
        "was_clipped": clipped_area_mm2 > 0.0,
        "clipped_area_mm2": round(float(clipped_area_mm2), 2),
        "clipped_pct": round(float(clipped_pct), 2),
        # The rail limits in force for this run, and the margin held back from
        # each end — together they reconstruct the exact rectangle clipped
        # against, which is what makes a reported figure reproducible.
        "travel_envelope_mm": [round(float(travel_x), 2), round(float(travel_y), 2)],
        "travel_margin_mm": round(float(margin), 2),
    }


def _empty_toolpath(step_over_mm: float, clip_fields: dict) -> dict:
    """Nothing to paint. Bounds stay a 4-list so consumers can index blindly."""
    return {
        "events": [],
        "row_count": 0,
        "step_over_mm": round(step_over_mm, 3),
        "total_paint_length_mm": 0.0,
        "total_travel_length_mm": 0.0,
        "paintable_area_mm2": 0.0,
        "bounds_mm": [0.0, 0.0, 0.0, 0.0],
        **clip_fields,
    }


# --------------------------------------------------------------------------- #
# Toolpath generation
# --------------------------------------------------------------------------- #

def generate_toolpath(
    wall_polygons_mm,
    obstacle_polygons_mm=None,
    step_over_mm: float | None = None,
    travel_x_mm: float | None = None,
    travel_y_mm: float | None = None,
    travel_margin_mm: float | None = None,
) -> dict:
    """Plan a serpentine raster fill over the reachable paintable wall area.

    ``wall_polygons_mm``     — rings of the paintable regions, in millimetres
                               (the ``is_wall`` detections, mapped by
                               ``WallCalibration.polygon_to_mm``).
    ``obstacle_polygons_mm`` — rings to subtract: everything ``is_wall`` is
                               False. Overlapping and self-intersecting rings
                               are fine, they are unioned and repaired.
    ``step_over_mm``         — row spacing; defaults to the nozzle/overlap
                               derived ``STEP_OVER_MM``.
    ``travel_*``             — override the gantry's reachable envelope;
                               default to the ``AURA_TRAVEL_*`` config.

    Geometry outside the gantry's reach is clipped away, and how much was lost
    is reported in ``clipped_area_mm2`` / ``clipped_pct`` — that leftover is
    what a second gantry position has to cover.

    Returns a dict of ``events`` (ordered ``travel``/``paint`` moves) plus the
    coverage figures the API and the thesis report. An empty, fully obscured, or
    entirely out-of-reach wall is not an error: it returns zero events.
    """
    _require_shapely()

    step = float(STEP_OVER_MM if step_over_mm is None else step_over_mm)
    if not math.isfinite(step) or step <= 0.0:
        raise ValueError(
            f"step_over_mm must be a positive number, got {step_over_mm!r}. "
            f"Check AURA_NOZZLE_WIDTH_MM / AURA_SPRAY_OVERLAP."
        )

    env_x0, env_y0, env_x1, env_y1 = travel_envelope(
        travel_x_mm, travel_y_mm, travel_margin_mm
    )
    travel_x = float(TRAVEL_X_MM if travel_x_mm is None else travel_x_mm)
    travel_y = float(TRAVEL_Y_MM if travel_y_mm is None else travel_y_mm)
    margin = float(TRAVEL_MARGIN_MM if travel_margin_mm is None else travel_margin_mm)
    no_clip = _clip_fields(travel_x, travel_y, margin)

    wall = _union(wall_polygons_mm, "wall")
    if wall is None or wall.is_empty:
        logger.info("No paintable wall geometry — empty toolpath.")
        return _empty_toolpath(step, no_clip)

    obstacles = _union(obstacle_polygons_mm, "obstacle")
    paintable = wall.difference(obstacles) if obstacles is not None else wall

    if paintable.is_empty or paintable.area <= 0.0:
        logger.info("Wall fully covered by non-paintable regions — empty toolpath.")
        return _empty_toolpath(step, no_clip)

    # Clip to what the gantry can actually reach. Done here, once, on the
    # geometry — clipping already-generated events instead would mean splitting
    # spans and re-deriving row and length totals from the leftovers.
    reachable_area = float(paintable.area)
    paintable = paintable.intersection(box(env_x0, env_y0, env_x1, env_y1))

    clipped_area = max(0.0, reachable_area - float(paintable.area))
    clipped_pct = (100.0 * clipped_area / reachable_area) if reachable_area else 0.0
    clip = _clip_fields(travel_x, travel_y, margin, clipped_area, clipped_pct)

    if clipped_area > 0.0:
        logger.info(
            "Clipped %.0f mm2 (%.1f%%) outside the %.1f x %.1f mm travel "
            "(margin %.1f mm) — that area needs another gantry position.",
            clipped_area, clipped_pct, travel_x, travel_y, margin,
        )

    if paintable.is_empty or paintable.area <= 0.0:
        logger.info("Wall is entirely outside the gantry's reach — empty toolpath.")
        return _empty_toolpath(step, clip)

    min_x, min_y, max_x, max_y = paintable.bounds

    events: list[dict] = []
    paint_length = 0.0
    travel_length = 0.0
    painted_rows = 0
    # Position of the nozzle at the end of the last emitted move. None until the
    # first stroke — the machine's resting position is the serial stage's
    # business, so nothing is invented for it here.
    current: tuple[float, float] | None = None

    row_index = 0
    while True:
        # Computed from the index rather than accumulated, so row spacing cannot
        # drift over a tall wall.
        y = min_y + step / 2.0 + row_index * step
        if y >= max_y:
            break

        scan = LineString([(min_x - EDGE_PAD_MM, y), (max_x + EDGE_PAD_MM, y)])
        spans = _row_spans(scan.intersection(paintable))

        if spans:
            # Serpentine: odd rows run right to left, so the row ends next to
            # where the following row begins.
            if row_index % 2 == 1:
                spans = [(end, start) for start, end in reversed(spans)]
            painted_rows += 1

            for x_start, x_end in spans:
                start = (x_start, y)
                end = (x_end, y)

                # One branch covers both gaps: between disjoint spans inside a
                # row (a hole) and between the last span of a row and the first
                # of the next.
                if current is not None:
                    hop = _distance(current, start)
                    if hop > MIN_MOVE_MM:
                        events.append(
                            {
                                "type": "travel",
                                "from": _point(*current),
                                "to": _point(*start),
                            }
                        )
                        travel_length += hop

                events.append(
                    {"type": "paint", "from": _point(*start), "to": _point(*end)}
                )
                paint_length += abs(x_end - x_start)
                current = end

        row_index += 1

    logger.info(
        "Toolpath: %d rows, %d events, %.0f mm painted, %.0f mm travel, "
        "%.0f mm2 paintable",
        painted_rows, len(events), paint_length, travel_length, paintable.area,
    )

    return {
        "events": events,
        # Rows that actually contain paint, not scan lines attempted — a row
        # whose entire width falls inside a window contributes nothing.
        "row_count": painted_rows,
        "step_over_mm": round(step, 3),
        "total_paint_length_mm": round(paint_length, 2),
        "total_travel_length_mm": round(travel_length, 2),
        # Post-clip: what this gantry position will actually cover.
        "paintable_area_mm2": round(float(paintable.area), 2),
        "bounds_mm": [round(float(v), 2) for v in (min_x, min_y, max_x, max_y)],
        **clip,
    }


# --------------------------------------------------------------------------- #
# G-code serialization
#
# The dialect is the GRBL-compatible subset the literature review cites for
# Arduino-class CNC controllers:
#
#   G0 X.. Y..   rapid move, spray off
#   G1 X.. Y..   paint move
#   M3 / M5      spray on / off (spindle commands, which is what a GRBL build
#                exposes for a relay-switched tool)
#
# No feed rate is emitted. F belongs with the motion tuning done against the
# real rig (Phase 2); a number invented here would silently become the number
# the machine runs at.
# --------------------------------------------------------------------------- #

def _fmt_mm(value: float) -> str:
    text = f"{value:.2f}"
    # -0.00 is valid G-code but reads as a bug in the thesis appendix listing.
    return "0.00" if text == "-0.00" else text


def _move(command: str, point) -> str:
    return f"{command} X{_fmt_mm(float(point[0]))} Y{_fmt_mm(float(point[1]))}"


def _check_soft_limits(point, command: str, travel_x: float, travel_y: float) -> None:
    """Refuse to serialize a move the machine cannot physically make.

    Checked against the FULL rail range, not the margin-shrunk clip envelope —
    this is a backstop against a calibration or arithmetic mistake, not a second
    copy of the clip step, and it should only ever fire on a bug.
    """
    x = float(point[0])
    y = float(point[1])

    if (
        x < -SOFT_LIMIT_TOLERANCE_MM or x > travel_x + SOFT_LIMIT_TOLERANCE_MM
        or y < -SOFT_LIMIT_TOLERANCE_MM or y > travel_y + SOFT_LIMIT_TOLERANCE_MM
    ):
        raise SoftLimitError(
            f"{command} X{x:.2f} Y{y:.2f} is outside the machine's travel "
            f"(0-{travel_x:.1f} x 0-{travel_y:.1f} mm). Envelope clipping should "
            f"have removed this move, so treat it as a calibration or arithmetic "
            f"bug rather than raising AURA_TRAVEL_X_MM / AURA_TRAVEL_Y_MM to "
            f"make it pass."
        )


def events_to_gcode(
    events,
    travel_x_mm: float | None = None,
    travel_y_mm: float | None = None,
) -> list[str]:
    """Ordered path events -> G-code lines.

    ``M3``/``M5`` bracket each *contiguous* run of paint moves rather than each
    individual stroke, so a run of adjoining spans does not chatter the spray
    valve on and off between them. A run always opens with a ``G0`` onto its
    first point: the machine has to be positioned there with the spray off, and
    that is also the only positioning move that can be emitted without assuming
    a home position.

    Every emitted coordinate is soft-limit checked against the physical travel;
    an out-of-range move raises ``SoftLimitError`` instead of being written out.
    """
    travel_x = float(TRAVEL_X_MM if travel_x_mm is None else travel_x_mm)
    travel_y = float(TRAVEL_Y_MM if travel_y_mm is None else travel_y_mm)

    lines: list[str] = []
    spraying = False
    position: tuple[float, float] | None = None

    for event in events or []:
        kind = (event or {}).get("type")

        if kind == "paint":
            start = (float(event["from"][0]), float(event["from"][1]))
            end = (float(event["to"][0]), float(event["to"][1]))

            # Not already sitting on the stroke's start: close any open run and
            # rapid there dry.
            _check_soft_limits(start, "G0", travel_x, travel_y)
            _check_soft_limits(end, "G1", travel_x, travel_y)

            if position is None or _distance(position, start) > MIN_MOVE_MM:
                if spraying:
                    lines.append("M5")
                    spraying = False
                lines.append(_move("G0", start))
                position = start

            if not spraying:
                lines.append("M3")
                spraying = True

            lines.append(_move("G1", end))
            position = end

        elif kind == "travel":
            end = (float(event["to"][0]), float(event["to"][1]))
            _check_soft_limits(end, "G0", travel_x, travel_y)

            if spraying:
                lines.append("M5")
                spraying = False
            if position is None or _distance(position, end) > MIN_MOVE_MM:
                lines.append(_move("G0", end))
                position = end

        else:
            logger.warning("Ignoring path event with unknown type %r", kind)

    # The program must not end with the spray live, and ends with an explicit
    # M5 even when the last move was already dry.
    if lines and (spraying or lines[-1] != "M5"):
        lines.append("M5")

    return lines
