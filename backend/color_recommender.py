"""
AURA — Colour recommendation from room context.

Pipeline
--------
1. Take the YOLOv8 detections for a frame and build a mask of everything that
   is NOT paintable wall — floor, furniture, ceiling, fixtures.
2. Cluster those pixels to find the room's dominant colour.
3. Apply colour-wheel relationships to that dominant colour to propose one
   primary wall colour plus five alternatives.

Why k-means and not colorthief
------------------------------
colorthief only accepts a file/PIL image and quantises the WHOLE picture — it
has no concept of a mask, so the wall itself (usually the largest region in
frame) would dominate the result and we would end up recommending a colour
based mostly on the wall's current paint. OpenCV k-means runs directly on an
arbitrary pixel selection, which is exactly what a segmentation mask gives us,
and cv2 is already a dependency. No extra package is needed.

Clustering happens in CIE-Lab rather than RGB: Euclidean distance in Lab
approximates perceived colour difference, so clusters split the way a person
would group them. RGB distance over-weights green and would merge colours that
look clearly different.

Paint-friendly clamping
-----------------------
A raw complementary hue at full saturation is a terrible interior wall colour.
Every generated colour is therefore pushed into a saturation/value band typical
of interior emulsion (see ``PAINT_SATURATION`` / ``PAINT_VALUE``) before being
returned. The hue relationship is preserved; only the intensity is tamed.
"""

from __future__ import annotations

import colorsys
import logging

import cv2
import numpy as np

logger = logging.getLogger("aura.color")

# Cap on pixels fed to k-means. A 1280x720 frame is ~920k pixels; clustering all
# of them costs far more than it improves the answer, so we sample.
MAX_SAMPLE_PIXELS = 20000
DEFAULT_K = 5

# Minimum pixels a region needs before we trust a colour read from it.
MIN_REGION_PIXELS = 500

# Interior-paint intensity band. Saturation stays muted and value stays high so
# the suggestions read as wall paint rather than as accent-poster colours.
PAINT_SATURATION = (0.14, 0.40)
PAINT_VALUE = (0.74, 0.93)
NEUTRAL_SATURATION = (0.04, 0.10)

# Hue anchors used by the warm / cool variants (degrees on the colour wheel).
WARM_ANCHOR_DEG = 32.0    # amber / terracotta
COOL_ANCHOR_DEG = 212.0   # slate blue

# --------------------------------------------------------------------------- #
# Named colour table — nearest-match in Lab gives every generated hex a name.
# Chosen to cover the hue circle at interior-paint lightness, plus a spread of
# neutrals and a few deeper tones so dark rooms still name sensibly.
# --------------------------------------------------------------------------- #

NAMED_COLORS: list[tuple[str, str]] = [
    # neutrals / whites
    ("Chalk White", "#F7F4EE"),
    ("Off-White Cream", "#F0EAD6"),
    ("Warm Ivory", "#F3E9D8"),
    ("Soft Linen", "#EAE0D2"),
    ("Greige", "#D8D0C4"),
    ("Pearl Grey", "#D9D9D6"),
    ("Silver Mist", "#C6C9C7"),
    ("Dove Grey", "#A9ADAE"),
    ("Slate Grey", "#7C848A"),
    ("Charcoal", "#4A5157"),
    ("Graphite", "#36393D"),
    # reds / pinks
    ("Blush Pink", "#E8C7C4"),
    ("Dusty Rose", "#C99A96"),
    ("Clay Rose", "#B87A73"),
    ("Brick Red", "#9E4B42"),
    ("Deep Garnet", "#6E3038"),
    # oranges / terracotta
    ("Apricot Cream", "#EFC9A8"),
    ("Peach Sand", "#EBC3A3"),
    ("Warm Terracotta", "#C97B5F"),
    ("Copper Clay", "#B26B4A"),
    ("Burnt Sienna", "#A65B3C"),
    # yellows / beiges
    ("Butter Cream", "#F0E2B6"),
    ("Wheat", "#E4D5B0"),
    ("Sand Dune", "#DCC9A6"),
    ("Warm Beige", "#D8C3A5"),
    ("Honey Gold", "#D9B26A"),
    ("Ochre", "#C29A4A"),
    # greens
    ("Mint Whisper", "#CFE0D2"),
    ("Sage Mist", "#BFC9B4"),
    ("Soft Sage Green", "#A8B99D"),
    ("Eucalyptus", "#93A98F"),
    ("Olive Grove", "#7D8A5C"),
    ("Fern Green", "#6E8B63"),
    ("Forest Green", "#45604B"),
    # teals / cyans
    ("Aqua Haze", "#C9DEDB"),
    ("Seafoam", "#AFCFC8"),
    ("Ocean Slate", "#5B8790"),
    ("Muted Teal", "#4F8A8B"),
    ("Deep Teal", "#35625F"),
    # blues
    ("Sky Wash", "#C7D8E8"),
    ("Powder Blue", "#BCCEE0"),
    ("Cornflower", "#7D9AD1"),
    ("Slate Blue", "#6B7FD4"),
    ("Steel Blue", "#6C87A8"),
    ("Denim Blue", "#5A7599"),
    ("Navy Ink", "#33455E"),
    # purples / violets
    ("Lavender Grey", "#C3BCD0"),
    ("Soft Lilac", "#CBBEDA"),
    ("Wisteria", "#A88FD0"),
    ("Amethyst Mist", "#9B87C4"),
    ("Violet Haze", "#B08FD9"),
    ("Dusty Mauve", "#A38FA8"),
    ("Orchid Blush", "#D69AC9"),
    ("Plum Smoke", "#7E6A86"),
    ("Deep Aubergine", "#52405C"),
]

# --------------------------------------------------------------------------- #
# Fixed neutral fallbacks.
#
# Deliberately NOT generated: these are the manual escape hatch for when none of
# the derived suggestions suit the user, so they must stay identical between
# rooms and never shift with the segmentation result. Returned verbatim by
# /api/recommend-colors and mirrored as static chips on the colour page.
# --------------------------------------------------------------------------- #

NEUTRAL_COLORS: list[dict] = [
    {"hex": "#FFFFFF", "name": "Pure White"},
    {"hex": "#F5F5F0", "name": "Off White"},
    {"hex": "#D3D3D3", "name": "Light Gray"},
    {"hex": "#9E9E9E", "name": "Medium Gray"},
    {"hex": "#4A4A4A", "name": "Charcoal"},
    {"hex": "#1C1C1C", "name": "Matte Black"},
]


# --------------------------------------------------------------------------- #
# Small colour conversions
# --------------------------------------------------------------------------- #

def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def rgb_to_hex(rgb) -> str:
    r, g, b = (int(max(0, min(255, round(float(c))))) for c in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def _rgb_to_lab(rgb_array: np.ndarray) -> np.ndarray:
    """(N,3) uint8 RGB -> (N,3) float32 Lab."""
    arr = rgb_array.reshape(-1, 1, 3).astype(np.uint8)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)


_NAMED_LAB: np.ndarray | None = None


def _named_lab() -> np.ndarray:
    global _NAMED_LAB
    if _NAMED_LAB is None:
        rgbs = np.array([hex_to_rgb(h) for _, h in NAMED_COLORS], dtype=np.uint8)
        _NAMED_LAB = _rgb_to_lab(rgbs)
    return _NAMED_LAB


def name_color(rgb, taken: set[str] | None = None) -> str:
    """Nearest named colour by CIE76 distance in Lab.

    ``taken`` lets a caller reserve names already used elsewhere in the same
    palette. Two swatches showing different hexes under one name reads as a
    bug in the UI, so we walk outward to the next-nearest unused name instead.
    """
    lab = _rgb_to_lab(np.array([rgb], dtype=np.uint8))[0]
    distances = np.linalg.norm(_named_lab() - lab, axis=1)
    for index in np.argsort(distances):
        name = NAMED_COLORS[int(index)][0]
        if not taken or name not in taken:
            return name
    return NAMED_COLORS[int(np.argmin(distances))][0]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _hsv_to_hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, _clamp(s, 0.0, 1.0), _clamp(v, 0.0, 1.0))
    return rgb_to_hex((r * 255, g * 255, b * 255))


def _rgb_to_hsv(rgb) -> tuple[float, float, float]:
    r, g, b = (c / 255.0 for c in rgb)
    return colorsys.rgb_to_hsv(r, g, b)


def _shift_hue(hue: float, degrees: float) -> float:
    return (hue + degrees / 360.0) % 1.0


def _anchor_hue(hue: float, anchor_degrees: float, spread_degrees: float = 18.0) -> float:
    """A hue that genuinely sits at ``anchor_degrees``, nudged by the room's hue.

    Interpolating from the room hue *toward* an anchor does not work: from a
    blue room, moving partway toward amber takes the short path through
    magenta, so the "warm" option comes back pink. The label would be lying.

    Instead we start AT the anchor and let the room shift it by at most
    ``spread_degrees``. The result is always recognisably warm (or cool) while
    still varying between rooms.
    """
    anchor = (anchor_degrees / 360.0) % 1.0
    delta = (hue - anchor + 0.5) % 1.0 - 0.5          # signed, in turns
    shift = (delta / 0.5) * (spread_degrees / 360.0)  # scale +-180deg -> +-spread
    return (anchor + shift) % 1.0


def _paint_color(hue: float, saturation: float, value: float, neutral: bool = False) -> str:
    band = NEUTRAL_SATURATION if neutral else PAINT_SATURATION
    return _hsv_to_hex(
        hue,
        _clamp(saturation, band[0], band[1]),
        _clamp(value, PAINT_VALUE[0], PAINT_VALUE[1]),
    )


# --------------------------------------------------------------------------- #
# Dominant-colour extraction
# --------------------------------------------------------------------------- #

def extract_dominant_colors(
    frame_bgr: np.ndarray,
    mask: np.ndarray | None = None,
    k: int = DEFAULT_K,
) -> list[dict]:
    """Cluster the masked pixels and return colours sorted by area share.

    ``mask`` is a boolean HxW array selecting the pixels to consider; None means
    the whole frame. Returns [] when there is not enough pixel data to trust.
    """
    if mask is None:
        pixels = frame_bgr.reshape(-1, 3)
    else:
        pixels = frame_bgr[mask]

    if pixels.shape[0] < MIN_REGION_PIXELS:
        return []

    if pixels.shape[0] > MAX_SAMPLE_PIXELS:
        # Fixed seed: the same photo must always yield the same recommendation,
        # otherwise the palette flickers between identical uploads.
        rng = np.random.default_rng(0)
        idx = rng.choice(pixels.shape[0], MAX_SAMPLE_PIXELS, replace=False)
        pixels = pixels[idx]

    lab = cv2.cvtColor(
        pixels.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB
    ).reshape(-1, 3).astype(np.float32)

    distinct = np.unique(lab, axis=0).shape[0]
    clusters = int(max(1, min(k, distinct)))

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 1.0)
    _, labels, centers = cv2.kmeans(
        lab, clusters, None, criteria, 3, cv2.KMEANS_PP_CENTERS
    )
    labels = labels.ravel()

    results: list[dict] = []
    for i, center in enumerate(centers):
        share = float(np.count_nonzero(labels == i)) / float(labels.size)
        lab_px = np.uint8([[np.clip(center, 0, 255)]])
        bgr = cv2.cvtColor(lab_px, cv2.COLOR_LAB2BGR).reshape(3)
        rgb = (int(bgr[2]), int(bgr[1]), int(bgr[0]))
        results.append(
            {
                "hex": rgb_to_hex(rgb),
                "name": name_color(rgb),
                "share": round(share, 4),
                "_rgb": rgb,
            }
        )

    results.sort(key=lambda c: -c["share"])
    return results


def build_context_mask(detections: list[dict], height: int, width: int) -> tuple[np.ndarray, str]:
    """Select the pixels that represent the ROOM rather than the wall.

    Preference order, falling back when a region is too small to read:
      1. the non-paintable detections (floor, furniture, fixtures)
      2. everything outside the wall mask
      3. the whole frame
    """
    wall = np.zeros((height, width), dtype=bool)
    non_wall = np.zeros((height, width), dtype=bool)

    for det in detections:
        mask = det.get("_mask")
        if mask is None:
            continue
        area = mask.astype(bool)
        if det.get("is_wall"):
            wall |= area
        else:
            non_wall |= area

    if int(np.count_nonzero(non_wall)) >= MIN_REGION_PIXELS:
        return non_wall, "non_wall_detections"

    outside = ~wall
    if int(np.count_nonzero(outside)) >= MIN_REGION_PIXELS:
        return outside, "outside_wall_mask"

    return np.ones((height, width), dtype=bool), "whole_frame"


# --------------------------------------------------------------------------- #
# Colour-theory palette generation
# --------------------------------------------------------------------------- #

def build_palette(dominant_rgb, dominant_name: str) -> dict:
    """One complementary primary + five relationship-based alternatives."""
    hue, sat, val = _rgb_to_hsv(dominant_rgb)

    # A near-grey dominant colour has a meaningless hue, so anchor off a warm
    # neutral instead of amplifying sensor noise into a confident hue claim.
    hue_is_meaningful = sat >= 0.08
    base_hue = hue if hue_is_meaningful else (WARM_ANCHOR_DEG / 360.0)

    complement = _shift_hue(base_hue, 180.0)
    recommended_hex = _paint_color(complement, max(sat, 0.22), max(val, 0.80))

    variants = [
        ("analogous", _paint_color(_shift_hue(base_hue, 32.0), max(sat, 0.20), 0.86)),
        ("triadic", _paint_color(_shift_hue(base_hue, 120.0), max(sat, 0.20), 0.84)),
        ("neutral", _paint_color(base_hue, 0.06, 0.90, neutral=True)),
        ("warm", _paint_color(_anchor_hue(base_hue, WARM_ANCHOR_DEG), max(sat, 0.22), 0.87)),
        ("cool", _paint_color(_anchor_hue(base_hue, COOL_ANCHOR_DEG), max(sat, 0.22), 0.85)),
    ]

    relationship_notes = {
        "analogous": "Sits next to the room's dominant hue — quieter, low-contrast pairing.",
        "triadic": "A third of the wheel away — balanced contrast without opposing the room.",
        "neutral": "Near-grey at the room's hue — lets furniture and flooring lead.",
        "warm": "Pulled toward amber — makes north-facing or low-light rooms feel warmer.",
        "cool": "Pulled toward slate blue — calms rooms with strong warm daylight.",
    }

    # Reserve names as we go so no two swatches in one palette share a label.
    used_names: set[str] = set()
    recommended_name = name_color(hex_to_rgb(recommended_hex), used_names)
    used_names.add(recommended_name)

    alternatives = []
    for relationship, hex_value in variants:
        alt_name = name_color(hex_to_rgb(hex_value), used_names)
        used_names.add(alt_name)
        alternatives.append(
            {
                "hex": hex_value,
                "name": alt_name,
                "relationship": relationship,
                "description": relationship_notes[relationship],
            }
        )

    if hue_is_meaningful:
        rationale = (
            f"The room's dominant colour reads as {dominant_name} ({rgb_to_hex(dominant_rgb)}). "
            f"This suggestion sits opposite it on the colour wheel, so the wall separates "
            f"cleanly from the floor and furniture instead of blending into them. Saturation "
            f"is held in the interior-paint range so the contrast stays comfortable over a "
            f"large area."
        )
    else:
        rationale = (
            f"The room reads as close to neutral ({dominant_name}, {rgb_to_hex(dominant_rgb)}), "
            f"so there is no strong hue to complement. This is a soft warm tone that adds "
            f"colour without competing with the existing furnishings."
        )

    return {
        "recommended": {
            "hex": recommended_hex,
            "name": recommended_name,
            "description": rationale,
            "relationship": "complementary",
        },
        "alternatives": alternatives,
    }


def recommend_colors(frame_bgr: np.ndarray, detections: list[dict]) -> dict:
    """Full recommendation for one segmented frame.

    ``detections`` are the dicts produced by ``app.parse_detections`` and must
    still carry their internal ``_mask`` arrays.
    """
    height, width = frame_bgr.shape[:2]
    mask, source = build_context_mask(detections, height, width)

    context_colors = extract_dominant_colors(frame_bgr, mask)
    if not context_colors:
        # Nothing readable at all — recommend from a warm neutral and say so.
        fallback_rgb = (200, 190, 178)
        palette = build_palette(fallback_rgb, name_color(fallback_rgb))
        palette.update(
            {
                "dominant_color": None,
                "context_colors": [],
                "context_source": "unavailable",
                "context_pixel_ratio": 0.0,
            }
        )
        return palette

    dominant = context_colors[0]
    palette = build_palette(dominant["_rgb"], dominant["name"])
    palette.update(
        {
            "dominant_color": {
                "hex": dominant["hex"],
                "name": dominant["name"],
                "share": dominant["share"],
            },
            "context_colors": [
                {k: v for k, v in c.items() if not k.startswith("_")}
                for c in context_colors
            ],
            "context_source": source,
            "context_pixel_ratio": round(
                float(np.count_nonzero(mask)) / float(height * width), 4
            ),
        }
    )
    return palette
