"""
AURA — Toolpath smoke test and visualiser.

Standalone script, not part of the Flask app. Runs the same pipeline
``/api/toolpath`` runs — segment, map to millimetres, subtract the
non-paintable detections, raster-fill, serialize — against a still image, then
draws the resulting path over that image and prints the coverage summary.

It loads the model directly through ``model_loader`` rather than calling a
running server, so it works with nothing else started, and it reuses app.py's
own ``run_inference`` so this can never drift from what the endpoint does.

Calibration is always the uncalibrated fallback here: no corner markers are
detected, so every millimetre figure it prints is a scale assumption against
AURA_WALL_WIDTH_MM / AURA_WALL_HEIGHT_MM, not a measurement.

Input images come from ``samples/`` (real photographs — see samples/README.md).
It falls back to ``website/assets/test_result_*.jpg`` only when that directory
is empty, and says so loudly: those files are annotated segmentation exports,
so scoring the model on them is scoring it against its own output.

The plan is clipped to the gantry's reachable travel, and the summary reports
how much was cut — that leftover is what a second gantry position has to cover.

Run:
    python backend/tools/test_toolpath.py
    python backend/tools/test_toolpath.py website/assets/test_result_3.jpg
    python backend/tools/test_toolpath.py --wall-width 2400 --wall-height 1200
    python backend/tools/test_toolpath.py --out C:\\temp\\path.png

    # force heavy clipping, to see the reach boundary bite:
    $env:AURA_TRAVEL_X_MM = "500"; $env:AURA_TRAVEL_Y_MM = "500"
    python backend/tools/test_toolpath.py

The PNG is written to the system temp directory by default — it is a scratch
artifact, not something to commit.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import tempfile
import textwrap

import cv2
import matplotlib

matplotlib.use("Agg")  # headless: this script only ever writes a file

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

from coordinate_mapping import WALL_HEIGHT_MM, WALL_WIDTH_MM, WallCalibration  # noqa: E402
from model_loader import load_model  # noqa: E402
from toolpath_generator import (  # noqa: E402
    events_to_gcode,
    generate_toolpath,
    travel_envelope,
)

# Imported last: pulling in app.py builds the Flask object and the camera
# handle (neither opens a device), and gives us the exact inference path the
# endpoint uses.
from app import run_inference  # noqa: E402

# Matches the website's legend semantics — green is the paintable wall, amber
# is everything the robot must not spray.
COLOR_PAINT = "#22C55E"
COLOR_TRAVEL = "#F43F5E"
COLOR_OBSTACLE = "#EAB308"
COLOR_ENVELOPE = "#38BDF8"

# Real photographs live in samples/. website/assets/ is the website's demo
# gallery and its test_result_*.jpg files are annotated segmentation EXPORTS —
# flat colour fills, not photographs — so running the model on them scores it
# against its own output. Kept only as a fallback so the script still does
# something before any photo has been shot, and it says so loudly when it does.
SAMPLES_DIR = os.path.join(PROJECT_ROOT, "samples")
SAMPLE_PATTERNS = ("*.jpg", "*.jpeg", "*.png")
FALLBACK_GLOB = os.path.join(PROJECT_ROOT, "website", "assets", "test_result_*.jpg")
ANNOTATED_EXPORT_DIR = os.path.join(PROJECT_ROOT, "website", "assets")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the AURA toolpath pipeline on one image and plot it.",
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Image to process. Defaults to the first photo in samples/, "
             "falling back to website/assets/test_result_*.jpg.",
    )
    parser.add_argument("--out", help="Output PNG path (default: system temp dir).")
    parser.add_argument(
        "--wall-width", type=float, default=WALL_WIDTH_MM,
        help=f"Assumed wall width in mm (default {WALL_WIDTH_MM:.0f}).",
    )
    parser.add_argument(
        "--wall-height", type=float, default=WALL_HEIGHT_MM,
        help=f"Assumed wall height in mm (default {WALL_HEIGHT_MM:.0f}).",
    )
    parser.add_argument(
        "--step-over", type=float, default=None,
        help="Row spacing in mm (default: nozzle width x (1 - overlap)).",
    )
    return parser.parse_args()


def resolve_image(path: str | None) -> str:
    """Pick the image to run on: the argument, else the first real sample."""
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


def annotated_export_warning(image_path: str) -> str | None:
    """Flag an image that is a rendered mask rather than a photograph.

    Checked by location rather than by inspecting pixels: everything under
    website/assets is site gallery content, and the test_result_* files there
    are segmentation output with the mask burnt in.
    """
    if os.path.dirname(os.path.abspath(image_path)) != os.path.abspath(
        ANNOTATED_EXPORT_DIR
    ):
        return None
    return (
        "This image is an ANNOTATED EXPORT from website/assets, not a photo — "
        "flat colour fills with the mask already burnt in. The geometry below "
        "(mapping, clipping, G-code) is unaffected, but the segmentation it "
        "rests on is scoring the model against its own output, so treat the "
        "confidence and mask quality as optimistic. Put a real wall photo in "
        "samples/ — see samples/README.md."
    )


def resolve_output(path: str | None, image_path: str) -> str:
    if path:
        return os.path.abspath(path)
    stem = os.path.splitext(os.path.basename(image_path))[0]
    return os.path.join(tempfile.gettempdir(), f"aura_toolpath_{stem}.png")


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def render(image_bgr, toolpath, obstacle_polygons, wall_w, wall_h, envelope,
           out_path, title):
    """Draw the path in millimetre space over the source image.

    The uncalibrated transform stretches the whole frame onto the wall
    rectangle, so drawing the image with ``extent=[0, wall_w, wall_h, 0]`` puts
    it in exactly the coordinate frame the path was planned in — +y down, origin
    top-left — and the two line up without any per-point back-projection.
    """
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    width_in = 11.0
    fig, ax = plt.subplots(figsize=(width_in, width_in * (wall_h / wall_w)))
    ax.imshow(rgb, extent=[0.0, wall_w, wall_h, 0.0], aspect="equal")

    for polygon in obstacle_polygons:
        if len(polygon) >= 3:
            ring = list(polygon) + [polygon[0]]
            ax.plot(
                [p[0] for p in ring], [p[1] for p in ring],
                color=COLOR_OBSTACLE, linewidth=1.4, linestyle=":", alpha=0.9,
            )

    paint = [
        [tuple(e["from"]), tuple(e["to"])]
        for e in toolpath["events"] if e["type"] == "paint"
    ]
    travel = [
        [tuple(e["from"]), tuple(e["to"])]
        for e in toolpath["events"] if e["type"] == "travel"
    ]

    if paint:
        ax.add_collection(
            LineCollection(paint, colors=COLOR_PAINT, linewidths=2.0, alpha=0.95)
        )
    if travel:
        ax.add_collection(
            LineCollection(
                travel, colors=COLOR_TRAVEL, linewidths=1.0,
                linestyles="dashed", alpha=0.85,
            )
        )

    # The gantry's reachable rectangle. Anything green would have to stay inside
    # it; the axes stay on the wall, so an envelope larger than the wall simply
    # runs off the edge of the plot.
    env_x0, env_y0, env_x1, env_y1 = envelope
    ax.add_patch(
        Rectangle(
            (env_x0, env_y0), env_x1 - env_x0, env_y1 - env_y0,
            fill=False, edgecolor=COLOR_ENVELOPE, linewidth=2.0,
            linestyle=(0, (8, 4)), alpha=0.95,
        )
    )

    ax.set_xlim(0.0, wall_w)
    ax.set_ylim(wall_h, 0.0)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title(title, fontsize=10)
    ax.legend(
        handles=[
            Line2D([], [], color=COLOR_PAINT, lw=2, label="paint (spray on)"),
            Line2D([], [], color=COLOR_TRAVEL, lw=1, ls="--", label="travel (spray off)"),
            Line2D([], [], color=COLOR_OBSTACLE, lw=1.4, ls=":", label="non-paintable"),
            Line2D([], [], color=COLOR_ENVELOPE, lw=2, ls="--", label="gantry reach"),
        ],
        loc="upper right", fontsize=8, framealpha=0.85,
    )

    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    args = parse_args()
    image_path = resolve_image(args.image)
    out_path = resolve_output(args.out, image_path)
    export_warning = annotated_export_warning(image_path)

    frame = cv2.imread(image_path)
    if frame is None:
        sys.exit(f"Could not decode {image_path} as an image.")
    height, width = frame.shape[:2]

    model = load_model()
    if not model.is_loaded:
        sys.exit(
            f"Model not loaded: {model.error}\n"
            f"(Set AURA_ALLOW_FALLBACK=1 to run against the COCO baseline.)"
        )

    result = run_inference(frame, "pre", source="toolpath-test")

    calibration = WallCalibration.uncalibrated(
        width, height, args.wall_width, args.wall_height
    )
    wall_polygons = [
        calibration.polygon_to_mm(d["polygon"])
        for d in result["detections"] if d["is_wall"] and d["polygon"]
    ]
    obstacle_polygons = [
        calibration.polygon_to_mm(d["polygon"])
        for d in result["detections"] if not d["is_wall"] and d["polygon"]
    ]

    toolpath = generate_toolpath(wall_polygons, obstacle_polygons, args.step_over)
    gcode = events_to_gcode(toolpath["events"])
    envelope = travel_envelope()

    title = (
        f"{os.path.basename(image_path)} — {toolpath['row_count']} rows @ "
        f"{toolpath['step_over_mm']:.1f} mm step-over "
        f"({calibration.calibration_mode})"
    )
    if toolpath["was_clipped"]:
        title += f" · {toolpath['clipped_pct']:.1f}% clipped to gantry reach"
    if export_warning:
        # The PNG may end up in the thesis; the caveat has to travel with it.
        title += "\nANNOTATED EXPORT, not a photograph — segmentation quality is optimistic"

    render(
        frame, toolpath, obstacle_polygons,
        args.wall_width, args.wall_height, envelope, out_path, title,
    )

    # ---- summary ---------------------------------------------------------- #
    area_m2 = toolpath["paintable_area_mm2"] / 1_000_000.0
    total_length = toolpath["total_paint_length_mm"] + toolpath["total_travel_length_mm"]
    efficiency = (
        100.0 * toolpath["total_paint_length_mm"] / total_length if total_length else 0.0
    )

    print()
    print("=" * 68)
    print(f"  AURA toolpath — {os.path.basename(image_path)}")
    print("=" * 68)
    if export_warning:
        print("  !! NOT A PHOTOGRAPH")
        for line in textwrap.wrap(export_warning, 62):
            print(f"     {line}")
        print("  " + "-" * 64)
    print(f"  Image             : {image_path}")
    print(f"  Resolution        : {width} x {height} px")
    print(f"  Inference         : {result['inference_ms']:.1f} ms on {model.device}"
          f"{'  [FALLBACK MODEL]' if model.using_fallback else ''}")
    print(f"  Detections        : {len(result['detections'])} "
          f"({len(wall_polygons)} wall, {len(obstacle_polygons)} non-paintable)")
    print(f"  Wall detected     : {result['wall_detected']}")
    print("  " + "-" * 64)
    print(f"  Calibration       : {calibration.calibration_mode}")
    print(f"  Assumed wall      : {args.wall_width:.0f} x {args.wall_height:.0f} mm")
    if not calibration.is_verified:
        print("                      (no corner markers — mm figures are a scale")
        print("                       assumption, NOT a measurement)")
    print("  " + "-" * 64)
    env_x, env_y = toolpath["travel_envelope_mm"]
    margin = toolpath["travel_margin_mm"]
    print(f"  Gantry travel     : {env_x:.1f} x {env_y:.1f} mm rail, "
          f"{margin:.0f} mm margin/end")
    print(f"  Reachable box     : [{envelope[0]:.1f}, {envelope[1]:.1f}, "
          f"{envelope[2]:.1f}, {envelope[3]:.1f}] mm")
    if toolpath["was_clipped"]:
        clipped_m2 = toolpath["clipped_area_mm2"] / 1_000_000.0
        print(f"  CLIPPED           : {toolpath['clipped_area_mm2']:,.0f} mm2 "
              f"({clipped_m2:.3f} m2) = {toolpath['clipped_pct']:.1f}% of the "
              f"detected wall")
        print("                      outside this position's reach — reposition the")
        print("                      gantry and re-run to cover the rest")
    else:
        print("  Clipped           : none — the whole wall is within reach")
    print("  " + "-" * 64)
    print(f"  Rows painted      : {toolpath['row_count']}")
    print(f"  Step-over         : {toolpath['step_over_mm']:.2f} mm")
    print(f"  Paintable area    : {toolpath['paintable_area_mm2']:,.0f} mm2 "
          f"({area_m2:.3f} m2)  [after clip]")
    print(f"  Paint travel      : {toolpath['total_paint_length_mm']:,.1f} mm")
    print(f"  Dry travel        : {toolpath['total_travel_length_mm']:,.1f} mm")
    print(f"  Path efficiency   : {efficiency:.1f}% of motion is spraying")
    print(f"  Bounds (mm)       : {toolpath['bounds_mm']}")
    print(f"  Path events       : {len(toolpath['events'])}")
    print(f"  G-code lines      : {len(gcode)}")
    print("  " + "-" * 64)

    head, tail = 8, 5
    if gcode:
        for line in gcode[:head]:
            print(f"    {line}")
        if len(gcode) > head + tail:
            print(f"    ... {len(gcode) - head - tail} more lines ...")
        for line in gcode[max(head, len(gcode) - tail):]:
            print(f"    {line}")
    else:
        print("    <no G-code — nothing paintable in this frame>")

    print("  " + "-" * 64)
    print(f"  Plot written to   : {out_path}")
    print("=" * 68)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
