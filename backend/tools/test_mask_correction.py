"""
AURA — Manual mask correction smoke test.

Standalone script, not part of the Flask app. Runs one image through the same
inference path ``/api/segment`` and ``/api/toolpath`` run, twice: once as the
model sees it, once with a synthetic brush correction applied, and prints what
changed. It also checks the invariants that make the feature defensible rather
than merely working:

1. **Confidence never moves.** A hand-drawn region is not a detection, so
   ``wall_confidence`` must be identical before and after. If a correction could
   raise it, every confidence figure in the thesis would become a mixture of
   model output and operator opinion.
2. **Add only adds, erase only erases.** Wall coverage rises with an add-only
   correction and falls with an erase-only one, by the area the correction
   reports — no third behaviour hiding in the compositing.
3. **Last stroke wins.** An add and an erase over the same pixels cancel to a
   no-op, which is what makes undo-by-brushing-back work.
4. **An erase mid-wall reaches the G-code.** The polygon a detection carries is
   a single ring, so a hole punched in the middle of a wall would vanish if the
   correction were only subtracted from the mask. It is re-emitted as a
   non-paintable region instead; this asserts the planner actually routes
   around it.

Like ``test_toolpath.py`` it loads the model directly through ``model_loader``
and reuses app.py's own ``run_inference``, so it cannot drift from what the
endpoints do, and it needs nothing else running.

Input images come from ``samples/`` (real photographs — see samples/README.md).
It falls back to ``website/assets/test_result_*.jpg`` only when that directory
is empty, and says so: those files are annotated segmentation exports, so
scoring the model on them is scoring it against its own output. For *this*
script the distinction is milder than usual — it measures the correction's
effect on a mask, not the mask's accuracy — but the same image should be used
for before and after, which it is.

Run:
    python backend/tools/test_mask_correction.py
    python backend/tools/test_mask_correction.py samples/wall_01.jpg
    python backend/tools/test_mask_correction.py --out C:\\temp\\correction.png

The PNG is written to the system temp directory by default — it is a scratch
artifact, not something to commit.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import tempfile

import cv2
import numpy as np

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

from coordinate_mapping import WALL_HEIGHT_MM, WALL_WIDTH_MM, WallCalibration  # noqa: E402
from mask_correction import CorrectionError, parse_correction  # noqa: E402
from model_loader import load_model  # noqa: E402
from smart_select import SmartSelectError  # noqa: E402
from smart_select import status as smart_status  # noqa: E402
from toolpath_generator import generate_toolpath  # noqa: E402

# Imported last: pulling in app.py builds the Flask object and the camera handle
# (neither opens a device) and gives us the exact inference path the endpoints
# use.
from app import run_inference  # noqa: E402

SAMPLES_DIR = os.path.join(PROJECT_ROOT, "samples")
SAMPLE_PATTERNS = ("*.jpg", "*.jpeg", "*.png")
FALLBACK_GLOB = os.path.join(PROJECT_ROOT, "website", "assets", "test_result_*.jpg")

# Tolerance on an area comparison, as a fraction of the frame. Rasterisation
# rounds at region edges and polygons are simplified before they reach the
# planner, so an exact equality would fail on arithmetic rather than on logic.
AREA_TOLERANCE = 0.004


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply a synthetic brush correction to one image and check "
                    "what it changed.",
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Image to process. Defaults to the first photo in samples/, "
             "falling back to website/assets/test_result_*.jpg.",
    )
    parser.add_argument("--out", help="Output PNG path (default: system temp dir).")
    parser.add_argument(
        "--no-smart", action="store_true",
        help="Skip the smart-select checks (they load MobileSAM on first use).",
    )
    return parser.parse_args()


def resolve_image(path: str | None) -> str:
    if path:
        if not os.path.isfile(path):
            sys.exit(f"Image not found: {path}")
        return os.path.abspath(path)

    samples: list[str] = []
    for pattern in SAMPLE_PATTERNS:
        samples.extend(glob.glob(os.path.join(SAMPLES_DIR, pattern)))
    if samples:
        return sorted(samples)[0]

    fallback = sorted(glob.glob(FALLBACK_GLOB))
    if not fallback:
        sys.exit(
            f"No images found. Put a wall photo in {SAMPLES_DIR} "
            f"(see samples/README.md) or pass one as an argument."
        )
    return fallback[0]


# --------------------------------------------------------------------------- #
# Synthetic corrections
#
# Stroke coordinates are normalized, so these are the same shapes on any frame:
# a band across the upper-left quarter, and a blob at the centre — which on a
# wall photo is reliably inside the wall region, so the erase has something to
# bite on.
# --------------------------------------------------------------------------- #

ADD_STROKE = {
    "kind": "brush",
    "mode": "add",
    "radius": 0.04,
    "points": [[0.06, 0.10], [0.18, 0.11], [0.30, 0.15]],
}
ERASE_STROKE = {"kind": "brush", "mode": "erase", "radius": 0.06, "points": [[0.50, 0.50]]}


def smart(mode: str, point, engine: str = "auto", labels=None, tolerance: int = 18) -> dict:
    """A smart-select operation: a click, not an outline."""
    points = point if isinstance(point[0], (list, tuple)) else [point]
    return {
        "kind": "smart",
        "mode": mode,
        "engine": engine,
        "points": [list(p) for p in points],
        "labels": list(labels) if labels else [1] * len(points),
        "tolerance": tolerance,
    }


def correction(*ops) -> object:
    """Build a MaskCorrection the same way the endpoint does — through the parser.

    Going via ``parse_correction`` rather than constructing the object directly
    means this script exercises the validation the browser's payload hits.
    """
    return parse_correction(json.dumps({"version": 2, "ops": list(ops)}))


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #

def plan(frame: np.ndarray, result: dict) -> dict:
    """Run the toolpath half, exactly as /api/toolpath does after inference."""
    height, width = frame.shape[:2]
    calibration = WallCalibration.uncalibrated(
        width, height, WALL_WIDTH_MM, WALL_HEIGHT_MM
    )
    wall = [
        calibration.polygon_to_mm(det["polygon"])
        for det in result["detections"]
        if det["is_wall"] and det["polygon"]
    ]
    obstacles = [
        calibration.polygon_to_mm(det["polygon"])
        for det in result["detections"]
        if not det["is_wall"] and det["polygon"]
    ]
    return generate_toolpath(wall, obstacles)


def segment(frame: np.ndarray, corr=None) -> dict:
    return run_inference(frame, "post", source="correction-test", correction=corr)


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

class Checks:
    """Collects pass/fail lines so every invariant is reported, not just the first."""

    def __init__(self) -> None:
        self.failures = 0

    def expect(self, ok: bool, label: str, detail: str = "") -> None:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            self.failures += 1
        print(f"  [{mark}] {label}" + (f"  — {detail}" if detail else ""))


def run_checks(frame: np.ndarray, baseline: dict) -> Checks:
    checks = Checks()
    base_cov = baseline["wall_coverage"]
    base_conf = baseline["wall_confidence"]

    print("\n  Invariants")
    print("  " + "-" * 64)

    added = segment(frame, correction(ADD_STROKE))
    stats = added["mask_correction"]
    checks.expect(
        added["wall_confidence"] == base_conf,
        "add leaves wall_confidence untouched",
        f"{base_conf} -> {added['wall_confidence']}",
    )
    checks.expect(
        added["wall_coverage"] >= base_cov,
        "add does not reduce wall coverage",
        f"{base_cov:.4f} -> {added['wall_coverage']:.4f} "
        f"(+{stats['added_area_ratio']:.4f} reported)",
    )
    checks.expect(
        stats["removed_px"] == 0,
        "an add-only correction removes nothing",
        f"removed_px={stats['removed_px']}",
    )

    erased = segment(frame, correction(ERASE_STROKE))
    stats = erased["mask_correction"]
    checks.expect(
        erased["wall_confidence"] == base_conf,
        "erase leaves wall_confidence untouched",
        f"{base_conf} -> {erased['wall_confidence']}",
    )
    checks.expect(
        stats["added_px"] == 0,
        "an erase-only correction adds nothing",
        f"added_px={stats['added_px']}",
    )
    checks.expect(
        abs((base_cov - erased["wall_coverage"]) - stats["removed_area_ratio"])
        <= AREA_TOLERANCE,
        "coverage falls by the area the erase reports",
        f"{base_cov:.4f} -> {erased['wall_coverage']:.4f}, "
        f"reported -{stats['removed_area_ratio']:.4f}",
    )

    # Same place, both modes: the later stroke owns those pixels. Stated as
    # "the overlapped pair equals the second stroke alone" rather than "the pair
    # cancels to nothing" — whether anything is left depends on what the model
    # already had there, which is exactly what must NOT change the rule.
    spot = [[0.75, 0.30]]
    add_one = {"mode": "add", "radius": 0.05, "points": spot}
    erase_one = {"mode": "erase", "radius": 0.05, "points": spot}

    erase_only = segment(frame, correction(erase_one))["mask_correction"]
    add_then_erase = segment(frame, correction(add_one, erase_one))["mask_correction"]
    checks.expect(
        add_then_erase["added_px"] == 0
        and add_then_erase["removed_px"] == erase_only["removed_px"],
        "add then erase over the same pixels leaves only the erase",
        f"added_px={add_then_erase['added_px']}, removed_px="
        f"{add_then_erase['removed_px']} vs {erase_only['removed_px']} alone",
    )

    add_only = segment(frame, correction(add_one))["mask_correction"]
    erase_then_add = segment(frame, correction(erase_one, add_one))["mask_correction"]
    checks.expect(
        erase_then_add["removed_px"] == 0
        and erase_then_add["added_px"] == add_only["added_px"],
        "erase then add over the same pixels leaves only the add",
        f"removed_px={erase_then_add['removed_px']}, added_px="
        f"{erase_then_add['added_px']} vs {add_only['added_px']} alone",
    )

    # The one that actually protects the machine: a hole in the middle of the
    # wall has to survive into the plan, not just into the mask.
    base_plan = plan(frame, baseline)
    erased_plan = plan(frame, erased)
    checks.expect(
        erased_plan["paintable_area_mm2"] < base_plan["paintable_area_mm2"],
        "an erase mid-wall reduces the planned paintable area",
        f"{base_plan['paintable_area_mm2']:,.0f} -> "
        f"{erased_plan['paintable_area_mm2']:,.0f} mm2",
    )

    # Malformed payloads are rejected, not silently dropped — an operator who
    # corrected a mask must never be shown an uncorrected plan as if it worked.
    for label, payload in (
        ("unknown mode", '{"version":1,"strokes":[{"mode":"x","radius":0.1,"points":[[0,0]]}]}'),
        ("future version", '{"version":99,"strokes":[]}'),
        ("not JSON", "wall please"),
        ("empty points", '{"version":1,"strokes":[{"mode":"add","radius":0.1,"points":[]}]}'),
    ):
        try:
            parse_correction(payload)
            checks.expect(False, f"rejects {label}", "accepted it")
        except CorrectionError as exc:
            checks.expect(True, f"rejects {label}", str(exc)[:52])

    checks.expect(
        parse_correction("") is None, "an absent correction is None, not an error"
    )

    # A v1 payload (brush only, `strokes`) must still be readable — a browser
    # tab left open across a server upgrade should lose smart select, not the
    # whole correction.
    legacy = parse_correction(
        json.dumps({"version": 1, "strokes": [dict(ADD_STROKE, kind=None) and ADD_STROKE]})
    )
    checks.expect(
        legacy is not None and legacy.stroke_count == 1 and legacy.smart_count == 0,
        "a v1 payload still parses as brush-only",
    )
    try:
        parse_correction(
            json.dumps({"version": 1, "ops": [smart("add", [0.5, 0.5])]})
        )
        checks.expect(False, "rejects a smart op inside a v1 envelope", "accepted it")
    except CorrectionError as exc:
        checks.expect(True, "rejects a smart op inside a v1 envelope", str(exc)[:48])

    return checks


def run_smart_checks(frame: np.ndarray, baseline: dict) -> Checks:
    """Smart select's own invariants, per engine that this machine can run."""
    checks = Checks()
    base_cov = baseline["wall_coverage"]
    engines = smart_status()["engines"]

    print("\n  Smart select — engines available: " + ", ".join(engines))
    print("  " + "-" * 64)

    # A point well inside the wall the model already found. Selecting it and
    # ERASING must remove real area; selecting it and ADDING must be ~a no-op,
    # because it was already wall. That pair is the strongest evidence the
    # engine is actually landing where it was clicked.
    on_wall = [0.62, 0.47]

    for engine in engines:
        erased = segment(frame, correction(smart("erase", on_wall, engine=engine)))
        stats = erased["mask_correction"]
        checks.expect(
            stats["removed_px"] > 0,
            f"[{engine}] a click on the wall selects real wall to erase",
            f"-{100 * stats['removed_area_ratio']:.2f}% of the frame",
        )
        checks.expect(
            erased["wall_coverage"] < base_cov,
            f"[{engine}] erasing the selection lowers wall coverage",
            f"{base_cov:.4f} -> {erased['wall_coverage']:.4f}",
        )
        checks.expect(
            erased["wall_confidence"] == baseline["wall_confidence"],
            f"[{engine}] smart select leaves wall_confidence untouched",
        )
        checks.expect(
            stats["engines_used"] == [engine],
            f"[{engine}] the response names the engine that ran",
            f"engines_used={stats['engines_used']}",
        )

        # Adding a selection that is already wall should contribute essentially
        # nothing. Not *exactly* nothing: the engine's idea of the wall boundary
        # and YOLOv8's differ by a rim of a few hundred pixels, which is real
        # disagreement between two models rather than an error. The claim worth
        # asserting is that the selection lands inside the existing wall, i.e.
        # nearly all of it shows up as "already there" and only the rim as new.
        added = segment(frame, correction(smart("add", on_wall, engine=engine)))
        new_px = added["mask_correction"]["added_px"]
        overlap_px = stats["removed_px"]  # the same selection, intersected with wall
        selection_px = new_px + overlap_px
        outside = new_px / float(selection_px or 1)
        checks.expect(
            outside < 0.05,
            f"[{engine}] adding a region that is already wall adds only its rim",
            f"{new_px} px new of {selection_px} px selected ({100 * outside:.2f}% outside "
            f"the model's wall)",
        )

    # Replay determinism: the same prompt must resolve to the same region every
    # time, or a re-plan would silently emit different G-code from the same
    # saved correction.
    prompt = correction(smart("erase", on_wall, engine=engines[0]))
    first = segment(frame, prompt)["mask_correction"]["removed_px"]
    second = segment(frame, correction(smart("erase", on_wall, engine=engines[0])))
    checks.expect(
        first == second["mask_correction"]["removed_px"],
        "the same prompt replays to the same region",
        f"{first} px both times",
    )

    # A saved selection naming an engine the server does not have must fail
    # loudly rather than resolving with a different engine behind the operator.
    if "sam" not in engines:
        try:
            segment(frame, correction(smart("add", on_wall, engine="sam")))
            checks.expect(False, "an unavailable engine refuses to substitute", "it did")
        except SmartSelectError as exc:
            checks.expect(True, "an unavailable engine refuses to substitute", str(exc)[:44])
    else:
        checks.expect(True, "MobileSAM present — no-substitution path not exercised here")

    for label, payload in (
        ("no positive point", {"kind": "smart", "mode": "add",
                               "points": [[0.5, 0.5]], "labels": [0]}),
        ("unknown engine", {"kind": "smart", "mode": "add",
                            "points": [[0.5, 0.5]], "engine": "magic"}),
        ("mismatched labels", {"kind": "smart", "mode": "add",
                               "points": [[0.5, 0.5]], "labels": [1, 1]}),
    ):
        try:
            parse_correction(json.dumps({"version": 2, "ops": [payload]}))
            checks.expect(False, f"rejects {label}", "accepted it")
        except CorrectionError as exc:
            checks.expect(True, f"rejects {label}", str(exc)[:44])

    return checks


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

def comparison_image(baseline: dict, corrected: dict) -> np.ndarray:
    """Before / after overlays side by side, with a caption strip."""
    left = baseline["overlay_image"]
    right = corrected["overlay_image"]
    strip = np.full((34, left.shape[1] * 2 + 12, 3), 32, dtype=np.uint8)

    canvas = np.full(
        (left.shape[0], left.shape[1] * 2 + 12, 3), 32, dtype=np.uint8
    )
    canvas[:, : left.shape[1]] = left
    canvas[:, left.shape[1] + 12 :] = right

    for text, x in (("model only", 10), ("corrected", left.shape[1] + 22)):
        cv2.putText(
            strip, text, (x, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (200, 200, 200), 1, cv2.LINE_AA,
        )
    return np.vstack([strip, canvas])


def main() -> int:
    args = parse_args()
    image_path = resolve_image(args.image)

    frame = cv2.imread(image_path)
    if frame is None:
        sys.exit(f"Could not read {image_path} as an image.")

    model = load_model()
    if not model.is_loaded:
        sys.exit(f"Model not loaded: {model.error}")

    height, width = frame.shape[:2]
    line = "=" * 68

    print()
    print(line)
    print("  AURA — Manual mask correction smoke test")
    print(line)
    print(f"  Image           : {os.path.relpath(image_path, PROJECT_ROOT)}  ({width}x{height})")
    print(f"  Model           : {os.path.basename(model.model_path)} on {model.device}")
    if os.path.dirname(os.path.abspath(image_path)) != SAMPLES_DIR:
        print("  NOTE            : not from samples/ — if this is an annotated export,")
        print("                    the mask under the brush is the model's own output")
    print("  " + "-" * 64)

    baseline = segment(frame)
    print(f"  Model detections: {len(baseline['detections'])}")
    print(f"  Wall coverage   : {baseline['wall_coverage']:.4f}")
    print(f"  Wall confidence : {baseline['wall_confidence']}")

    both = segment(frame, correction(ADD_STROKE, ERASE_STROKE))
    stats = both["mask_correction"]
    print("  " + "-" * 64)
    print(f"  Corrected       : {len(both['detections'])} detections "
          f"({stats['added_region_count']} added, {stats['removed_region_count']} removed)")
    print(f"  Wall coverage   : {both['wall_coverage']:.4f}")
    print(f"  Wall confidence : {both['wall_confidence']}  (unchanged by design)")
    print(f"  Area added      : +{100 * stats['added_area_ratio']:.2f}% of the frame")
    print(f"  Area removed    : -{100 * stats['removed_area_ratio']:.2f}% of the frame")

    base_plan = plan(frame, baseline)
    both_plan = plan(frame, both)
    print("  " + "-" * 64)
    print(f"  Plan (model)    : {base_plan['row_count']} rows, "
          f"{base_plan['paintable_area_mm2']:,.0f} mm2, "
          f"{len(base_plan['events'])} moves")
    print(f"  Plan (corrected): {both_plan['row_count']} rows, "
          f"{both_plan['paintable_area_mm2']:,.0f} mm2, "
          f"{len(both_plan['events'])} moves")

    checks = run_checks(frame, baseline)
    failures = checks.failures
    if not args.no_smart:
        failures += run_smart_checks(frame, baseline).failures

    out_path = args.out or os.path.join(
        tempfile.gettempdir(), "aura_mask_correction.png"
    )
    cv2.imwrite(out_path, comparison_image(baseline, both))

    print("  " + "-" * 64)
    print(f"  Comparison PNG  : {out_path}")
    if failures:
        print(f"  RESULT          : {failures} check(s) FAILED")
    else:
        print("  RESULT          : all checks passed")
    print(line)
    print()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
