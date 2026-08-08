"""
AURA — Colour recommendation from room context.

Pipeline
--------
1. Take the YOLOv8 detections for a frame and build a mask of everything that
   is NOT paintable wall — floor, furniture, ceiling, fixtures.
2. Discard pixels that carry no usable hue (near-white, near-black, near-grey)
   and cluster what remains to find the room's dominant *chromatic* colour.
3. Optionally pull that seed toward a reference image the user uploaded ("what
   should this room look like?") and lean it toward who the room is for.
4. Apply colour-wheel relationships to the resulting colour, in CIE LCh, to
   propose one primary wall colour plus five alternatives.

Steps 1-2 describe the room as photographed; step 3 is the only place the user's
own intent enters, and it acts on the shared seed so the whole palette moves
together. Both of its inputs are optional — with neither supplied the pipeline
is exactly steps 1, 2, 4, i.e. unchanged.

Why LCh(ab) and not HSL
-----------------------
HSL hue is a formula over sRGB max/min channels; it carries no model of human
vision. Equal HSL hue steps are perceptually uneven — the 60 deg from red to
yellow crosses far less apparent colour change than the 60 deg from cyan to
blue — and HSL "lightness" is not lightness at all: at L=0.5, S=1 a yellow is
blindingly bright and a blue is dark. Two consequences showed up directly in
the old palettes: a "complementary" pair generated at HSL hue +180 was often
not the visual opposite, and swatches nominally sharing a lightness looked
wildly unequal in weight. That is the inconsistency this module now removes.

CIE LCh(ab) is the cylindrical form of CIE L*a*b*: the same space, with the a*/b*
plane rewritten in polar coordinates.

    L*  perceptual lightness, 0 (black) to 100 (diffuse white)
    C*  chroma — distance from the neutral axis, i.e. colourfulness
    h   hue angle in degrees, 0-360

Because Lab is approximately perceptually uniform, a hue rotation in ``h`` is a
rotation on a wheel that matches what an observer sees, so +180 deg really is
the visual complement and +120/+120 really does divide the wheel into thirds.
Splitting lightness (L*) from colourfulness (C*) also means the two can be
constrained independently — which is exactly what a wall colour needs.

Conversions go through ``colour-science`` (sRGB -> XYZ -> Lab -> LCh) rather
than OpenCV. This matters: cv2's 8-bit Lab is quantised and *rescaled* (L is
stored 0-255, a/b are offset by 128), so its numbers are not CIE units and the
L*/C* limits below would not mean what they say. colour-science works in
floating point CIE units throughout, under the D65 illuminant that sRGB itself
is defined against.

Why k-means and not colorthief
------------------------------
colorthief only accepts a file/PIL image and quantises the WHOLE picture — it
has no concept of a mask, so the wall itself (usually the largest region in
frame) would dominate the result and we would end up recommending a colour
based mostly on the wall's current paint. OpenCV k-means runs directly on an
arbitrary pixel selection, which is exactly what a segmentation mask gives us,
and cv2 is already a dependency.

Clustering happens in CIE Lab, not RGB: Euclidean distance in Lab approximates
perceived colour difference, so clusters split the way a person would group
them. RGB distance over-weights green and would merge colours that look clearly
different. Lab is also the space LCh is read from, so the seed filter and the
clustering share one set of units.

Paint-friendly clamping
-----------------------
A raw complementary hue at full chroma is a terrible interior wall colour.
Every generated colour is pushed into an L*/C* band typical of interior
emulsion (``PAINT_LIGHTNESS`` / ``PAINT_CHROMA``) before being returned. The
hue relationship is preserved; only lightness and colourfulness are tamed.

Clamping alone is not sufficient, because the L*/C* band is a box and the sRGB
gamut is not: a dark saturated yellow, say, has coordinates in the band that no
monitor or paint can show. Naively clipping the resulting RGB would shift the
hue and silently break the very relationship the palette is built on, so each
colour is instead gamut-mapped by reducing C* at constant L* and h until it is
displayable (see ``_lch_to_rgb``).
"""

from __future__ import annotations

import logging
import warnings

import cv2
import numpy as np

# colour-science warns at import that SciPy is absent. Nothing used here needs
# it — the sRGB/XYZ/Lab/LCh transforms are closed-form — and SciPy is a large
# dependency to add to a pinned CUDA venv for a warning's sake, so silence just
# this one message rather than pulling it in.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*SciPy.*")
    import colour

logger = logging.getLogger("aura.color")

# Cap on pixels fed to k-means. A 1280x720 frame is ~920k pixels; clustering all
# of them costs far more than it improves the answer, so we sample.
MAX_SAMPLE_PIXELS = 20000
DEFAULT_K = 5

# Minimum pixels a region needs before we trust a colour read from it.
MIN_REGION_PIXELS = 500

# --------------------------------------------------------------------------- #
# Interior-paint band, in CIE LCh(ab) units.
#
# L* 30-88 keeps a colour off both ends of the lightness range: below ~30 a wall
# reads as near-black under domestic lighting, above ~88 it is indistinguishable
# from white and the hue relationship stops being visible at all. C* 12-60 keeps
# it off the pure neutral axis without reaching the poster-paint chroma that
# becomes oppressive over a whole wall.
#
# WIDENED 2026-08-08, from L* 30-70 / C* 20-60. The original band was set tight
# to eliminate washed-out and hyper-saturated failures first, and it did — but it
# was tighter than real emulsion and the note in the vault said so: measured
# against this module's OWN name table, Soft Sage Green (C* 16.5) and Slate Grey
# (C* 4.6) fell under the old chroma floor and Honey Gold (L* 74.6) over the old
# lightness ceiling. Pastels were unreachable outright: a light pink #F8C8DC
# (L* 85.2) clamped to #CD9FB2, a dusty mauve. That surfaced as a real complaint
# the first time a pastel reference image was tried, which is exactly the
# evidence the old comment here said would justify widening.
#
# Still narrower than the full sRGB gamut, and deliberately so — the point of
# the band is that a wall colour is not a poster colour.
# --------------------------------------------------------------------------- #

PAINT_LIGHTNESS = (30.0, 88.0)   # L*
PAINT_CHROMA = (12.0, 60.0)      # C*

# The "neutral" alternative is the near-grey escape hatch, so it is exempt from
# the chroma floor above by design — forcing C* >= 20 on it would make it a
# second analogous swatch rather than a neutral.
NEUTRAL_CHROMA = 6.0

# --------------------------------------------------------------------------- #
# Seed-pixel gate, also in LCh(ab).
#
# Rooms are mostly neutral: white ceilings, grey floors, black shadow, blown
# highlights on glass and gloss. Those pixels have no meaningful hue — a
# near-white pixel's hue angle is sensor noise amplified by the polar
# conversion — but they are numerous, so k-means on the raw region hands back a
# near-neutral centroid and every harmony rotation applied to it is arbitrary.
# That is the single largest source of the inconsistency this module had.
# Filtering them out BEFORE clustering means the seed is drawn from pixels that
# actually carry colour: timber, textiles, foliage, painted furniture.
# --------------------------------------------------------------------------- #

SEED_MAX_LIGHTNESS = 85.0   # brighter than this is a highlight or white paint
SEED_MIN_LIGHTNESS = 15.0   # darker than this is shadow, and hue is unreadable
SEED_MIN_CHROMA = 10.0      # below this the pixel is on the neutral axis

# Pixels that must survive the gate before a chromatic seed is trusted. Fewer
# than this and the room genuinely has no dominant hue, so we say so rather than
# inventing one from a handful of stray pixels.
MIN_SEED_PIXELS = 200

# Hue anchors used by the warm / cool variants, as LCh(ab) hue angles. These are
# NOT the old HSL angles: they were re-measured from the paint colours they are
# meant to name (Warm Terracotta #C97B5F -> h 45.7, Steel Blue #6C87A8 -> h 266.5).
WARM_ANCHOR_DEG = 48.0    # amber / terracotta
COOL_ANCHOR_DEG = 267.0   # slate blue

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
# Demographic bias — "who is this room for?"
#
# Deltas applied ONCE to the shared seed (L*, C*, hue) before any harmony rule
# runs, so all six swatches carry the same lean instead of drifting apart. Same
# mechanism as WARM_ANCHOR_DEG / COOL_ANCHOR_DEG above, just keyed by category
# rather than fixed: a positive hue_nudge_deg walks toward the warm anchor, a
# negative one toward the cool anchor.
#
# The deltas are pre-clamp. _paint_color still forces the result back inside
# PAINT_LIGHTNESS / PAINT_CHROMA, so a bias can shift a palette within the
# interior-paint band but never out of it — which also means a large delta on an
# already-extreme seed is partly absorbed by the clamp. That is intended: the
# band is the harder constraint.
#
# These are hand-derived from the direction of published findings, not fitted to
# data — the same status as PAINT_LIGHTNESS / PAINT_CHROMA, i.e. defensible
# starting points and an explicit tuning target for the evaluator study. The
# source literature is largely hotel rooms, nursing homes and residential
# surveys being generalised to "wall colour for a home room"; state that plainly
# rather than implying precision.
#
# One row group is weaker than that and is marked inline: the child/teen CHROMA
# values were raised above what Hao et al. actually measured, as a judgement
# call. Every other number here follows the direction of its citation.
# --------------------------------------------------------------------------- #

CATEGORY_BIAS: dict[str, dict[str, float]] = {
    # ------------------------------------------------------------------ #
    # NOTE on the three young-occupant rows: their CHROMA is a deliberate
    # design choice, NOT a value derived from the literature — unlike every
    # other number in this table. Hao et al. (2025) reported children preferring
    # HSV S ~25/100 at V ~75/100, which converts to roughly L* 72 / C* 20 in the
    # units used here; these rows sit well above that. Raised 2026-08-08 on the
    # judgement that a moderate-low backdrop measured in a paediatric-furniture
    # study reads as flat for a children's bedroom wall.
    #
    # What IS still Hao-derived in these rows: the warm hue nudge, the positive
    # lightness delta, the boy > girl chroma ordering, and the 12-point size of
    # that gap. Only the common offset moved. Say exactly this if asked at the
    # defence — the honest answer is that the direction is cited and the
    # magnitude is ours, and the evaluator study is what settles it.
    # ------------------------------------------------------------------ #
    "child_boy":   {"lightness_delta": 8.0,  "chroma_delta": 18.0,  "hue_nudge_deg": 12.0},
    "child_girl":  {"lightness_delta": 8.0,  "chroma_delta": 6.0,   "hue_nudge_deg": 12.0},
    # Jiang et al. (2020); Hao et al. (2025): same direction as child, milder
    # magnitude as age increases. Lifted by half the children's raise (+6) to
    # keep that documented age gradient monotonic — leaving it at +2 while the
    # child rows moved to +18/+6 would have made this row's own stated rationale
    # false. One line to revert if the gradient is not wanted.
    "teen":        {"lightness_delta": 4.0,  "chroma_delta": 8.0,   "hue_nudge_deg": 6.0},
    # Bogicevic et al. (2018): men prefer "masculine" — cooler, more saturated.
    "adult_man":   {"lightness_delta": 0.0,  "chroma_delta": 8.0,   "hue_nudge_deg": -10.0},
    # Bogicevic et al. (2018): women were equally satisfied with masculine and
    # feminine schemes, so no directional bias is evidence-backed. Deliberately
    # a no-op rather than an invented lean.
    "adult_woman": {"lightness_delta": 0.0,  "chroma_delta": 0.0,   "hue_nudge_deg": 0.0},
    # Li et al. (2022); Rapuano et al. (2023): lighter, less saturated, warmer.
    # Torres et al. (2020) complicates this — warm for activity rooms, cool for
    # bedrooms — but AURA has no room-type context, so this takes the general
    # (bedroom-leaning) finding. Known limitation, documented in Chapter 5.
    "elderly":     {"lightness_delta": 6.0,  "chroma_delta": -10.0, "hue_nudge_deg": 10.0},
    # Default: current behaviour, untouched.
    "none":        {"lightness_delta": 0.0,  "chroma_delta": 0.0,   "hue_nudge_deg": 0.0},
}

# Opening clause of the rationale text, per seed origin: (hue found, near-grey
# seed). The recommendation is only as trustworthy as the user's ability to see
# what it was built from, so once an optional input moves the seed the sentence
# has to move with it — "the room's dominant colour" stops being true the moment
# a reference image is blended in.
SEED_ORIGIN_PHRASES: dict[str, tuple[str, str]] = {
    "room": (
        "The room's dominant colour reads as",
        "The room reads as close to neutral",
    ),
    "blend": (
        "The blend of your room photo and reference image reads as",
        "The blend of your room photo and reference image is close to neutral",
    ),
    # Room unreadable, reference usable — the palette really does rest on the
    # reference alone, and saying "blend" here would overstate the room's part.
    "reference": (
        "Your reference image reads as",
        "Your reference image is close to neutral",
    ),
}

# Smallest area share a reference cluster may have and still be eligible to seed
# the palette. Reference seeds are chosen by share x chroma (see
# ``extract_reference_seed``), and without a floor a few dozen very saturated
# pixels — a specular highlight, a JPEG ringing artefact — could outscore the
# colour the image is actually about.
MIN_REFERENCE_CLUSTER_SHARE = 0.05

# Share of the palette seed contributed by an optional reference ("what should
# this room look like?") image; the room photo carries the remainder.
#
# Reference-dominant on purpose: the room photo already constrains the answer
# through segmentation and the context breakdown, and a user who bothers to
# upload a reference is stating an intent the room itself does not express. A
# 50/50 split made the reference read as ignored on rooms with a strong hue.
#
# Raised 0.6 -> 0.7 on 2026-08-08. At 60/40 a warm-toned room still pulled a
# saturated reference hue about 21 deg toward its own; at 70/30 that drag is
# ~15 deg, so the reference survives the blend recognisably on rooms that have a
# strong colour of their own. Note this only affects rooms whose hue is
# MEANINGFUL — on a neutral room the reference has supplied 100% of the hue
# since the meaningful-hue check went into _blend_seeds, and this constant then
# governs L* and C* only.
REFERENCE_SEED_WEIGHT = 0.7


# --------------------------------------------------------------------------- #
# Colour conversions — sRGB <-> CIE Lab <-> CIE LCh(ab)
#
# All CIE values here are true colorimetric units (L* 0-100, a*/b* signed,
# C* >= 0, h in degrees), never OpenCV's rescaled 8-bit encoding.
# --------------------------------------------------------------------------- #

def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def rgb_to_hex(rgb) -> str:
    r, g, b = (int(max(0, min(255, round(float(c))))) for c in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def _rgb_to_lab(rgb_array: np.ndarray) -> np.ndarray:
    """(N,3) 0-255 RGB -> (N,3) float64 CIE Lab.

    sRGB is gamma-encoded, so the transform is sRGB -> linear -> XYZ (D65) ->
    Lab. colour-science does the whole chain; the only preparation needed is
    scaling the 8-bit codes to the 0-1 range it expects.
    """
    rgb = np.asarray(rgb_array, dtype=np.float64).reshape(-1, 3) / 255.0
    return colour.XYZ_to_Lab(colour.sRGB_to_XYZ(rgb))


def _lab_to_lch(lab: np.ndarray) -> np.ndarray:
    """(N,3) Lab -> (N,3) LCh(ab): the same colours in polar (a*,b*) form.

    C* = hypot(a*, b*) and h = atan2(b*, a*) in degrees. L* is carried through
    untouched, which is what lets lightness be constrained independently of
    colourfulness further down.
    """
    return colour.Lab_to_LCHab(np.asarray(lab, dtype=np.float64).reshape(-1, 3))


def _rgb_to_lch(rgb_array: np.ndarray) -> np.ndarray:
    """(N,3) 0-255 RGB -> (N,3) LCh(ab)."""
    return _lab_to_lch(_rgb_to_lab(rgb_array))


def _lab_to_rgb(lab_array: np.ndarray) -> np.ndarray:
    """(N,3) Lab -> (N,3) uint8 RGB, clipped to the displayable cube."""
    lab = np.asarray(lab_array, dtype=np.float64).reshape(-1, 3)
    rgb = colour.XYZ_to_sRGB(colour.Lab_to_XYZ(lab))
    return np.clip(rgb * 255.0, 0, 255).round().astype(np.uint8)


def _lch_to_linear_rgb(lightness: float, chroma: float, hue_deg: float) -> np.ndarray:
    """One LCh triple -> sRGB in 0-1, WITHOUT clipping.

    Left unclipped on purpose: values outside 0-1 are the signal that the colour
    falls outside the sRGB gamut, which ``_lch_to_rgb`` needs in order to detect
    and correct the problem instead of hiding it.
    """
    lch = np.array([[lightness, chroma, hue_deg % 360.0]], dtype=np.float64)
    return colour.XYZ_to_sRGB(colour.Lab_to_XYZ(colour.LCHab_to_Lab(lch)))[0]


def _lch_to_rgb(lightness: float, chroma: float, hue_deg: float) -> tuple[int, int, int]:
    """LCh(ab) -> 8-bit sRGB, gamut-mapped by reducing chroma.

    The L*/C* band is a rectangle but the sRGB gamut is a lumpy solid, and how
    much chroma a hue can carry depends strongly on both the hue and the
    lightness — sRGB reaches C* > 100 for yellow near L* 97, but barely 40 for
    the same hue at L* 40. So a coordinate can sit inside the paint band and
    still be unreachable.

    Clipping the out-of-range RGB channels would be the easy fix and the wrong
    one: clipping moves the colour across the a*/b* plane, so the hue angle
    shifts and a "complement" stops being opposite the seed. Instead we hold L*
    and h fixed — lightness and the harmony relationship are the two things the
    palette is actually built on — and binary-search the largest chroma that
    lands inside the gamut. C* = 0 is a grey and always displayable, so the
    search always has a valid lower bound to fall back to.
    """
    lightness = float(np.clip(lightness, 0.0, 100.0))
    hue_deg = float(hue_deg) % 360.0
    high = max(0.0, float(chroma))

    rgb = _lch_to_linear_rgb(lightness, high, hue_deg)
    if not _out_of_gamut(rgb):
        return _to_u8(rgb)

    low = 0.0
    for _ in range(24):  # 24 halvings resolves chroma to well under 1 unit
        mid = (low + high) / 2.0
        if _out_of_gamut(_lch_to_linear_rgb(lightness, mid, hue_deg)):
            high = mid
        else:
            low = mid
    return _to_u8(_lch_to_linear_rgb(lightness, low, hue_deg))


def _out_of_gamut(rgb: np.ndarray, tolerance: float = 1e-6) -> bool:
    return bool(np.any(rgb < -tolerance) or np.any(rgb > 1.0 + tolerance))


def _to_u8(rgb: np.ndarray) -> tuple[int, int, int]:
    values = np.clip(np.asarray(rgb, dtype=np.float64) * 255.0, 0, 255).round()
    return (int(values[0]), int(values[1]), int(values[2]))


def _lch_to_hex(lightness: float, chroma: float, hue_deg: float) -> str:
    return rgb_to_hex(_lch_to_rgb(lightness, chroma, hue_deg))


_NAMED_LAB: np.ndarray | None = None


def _named_lab() -> np.ndarray:
    global _NAMED_LAB
    if _NAMED_LAB is None:
        rgbs = np.array([hex_to_rgb(h) for _, h in NAMED_COLORS], dtype=np.uint8)
        _NAMED_LAB = _rgb_to_lab(rgbs)
    return _NAMED_LAB


def name_color(rgb, taken: set[str] | None = None) -> str:
    """Nearest named colour by CIE76 distance in Lab.

    Lab here is colorimetric, so the three axes are commensurate and a plain
    Euclidean distance is a valid dE76. (Run on cv2's 8-bit Lab it would not be:
    that encoding stretches L* by 255/100, weighting lightness ~2.55x against
    a*/b* and biasing every name toward whichever entry matched in brightness.)

    ``taken`` lets a caller reserve names already used elsewhere in the same
    palette. Two swatches showing different hexes under one name reads as a bug
    in the UI, so we walk outward to the next-nearest unused name instead.
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


def _shift_hue(hue_deg: float, degrees: float) -> float:
    """Rotate an LCh hue angle.

    This is the whole point of the LCh switch: the rotation happens on the
    perceptually uniform hue circle, so +180 is the visual complement and +120
    genuinely divides the wheel in three. The same arithmetic on an HSL hue
    lands somewhere else, because HSL's circle is unevenly stretched.
    """
    return (hue_deg + degrees) % 360.0


def _circular_mean_hue(hue_a: float, hue_b: float, weight_a: float) -> float:
    """Weighted circular mean of two hue angles (degrees). weight_a + weight_b == 1.

    Hue is an angle, so the arithmetic mean is wrong across the 0/360 wrap:
    averaging 350 and 10 gives 180 — cyan — when the answer a person expects is
    0, red. Converting each hue to a unit vector, averaging the vectors and
    reading the resulting angle back gets the short way round in every case,
    which is the standard directional-statistics fix.

    Degenerate case: two hues 180 apart at equal weight cancel to a near-zero
    vector, and the returned angle is then arbitrary. It cannot arise here —
    weight_a is REFERENCE_SEED_WEIGHT (0.6), never 0.5 — and even a small weight
    imbalance resolves it toward the heavier hue.
    """
    weight_b = 1.0 - weight_a
    rad_a, rad_b = np.radians(hue_a), np.radians(hue_b)
    x = weight_a * np.cos(rad_a) + weight_b * np.cos(rad_b)
    y = weight_a * np.sin(rad_a) + weight_b * np.sin(rad_b)
    return float(np.degrees(np.arctan2(y, x)) % 360.0)


def _anchor_hue(hue_deg: float, anchor_deg: float, spread_deg: float = 18.0) -> float:
    """A hue that genuinely sits at ``anchor_deg``, nudged by the room's hue.

    Interpolating from the room hue *toward* an anchor does not work: from a
    blue room, moving partway toward amber takes the short path through
    magenta, so the "warm" option comes back pink. The label would be lying.

    Instead we start AT the anchor and let the room shift it by at most
    ``spread_deg``. The result is always recognisably warm (or cool) while still
    varying between rooms.
    """
    delta = (hue_deg - anchor_deg + 180.0) % 360.0 - 180.0   # signed, degrees
    return (anchor_deg + (delta / 180.0) * spread_deg) % 360.0


def _max_in_gamut_chroma(lightness: float, hue_deg: float) -> float:
    """Largest C* that sRGB can actually show at this L* and hue.

    The paint band is a box and the gamut is not, so this is the real ceiling —
    and it varies enormously with lightness. At hue 10 deg it is C* 83 at L* 55
    but only C* 33 at L* 78. Anything asked for above the line here is not a
    colour that exists; it is a coordinate.
    """
    lo, hi = 0.0, 150.0
    for _ in range(24):
        mid = (lo + hi) / 2.0
        if _out_of_gamut(_lch_to_linear_rgb(lightness, mid, hue_deg)):
            hi = mid
        else:
            lo = mid
    return lo


# How much L* a colour may give up to keep the chroma it was asked for, when the
# two cannot both be had. See _fit_lightness_for_chroma.
CHROMA_LIGHTNESS_GIVEBACK = 12.0


def _fit_lightness_for_chroma(lightness: float, chroma: float, hue_deg: float) -> float:
    """Trade lightness for chroma when the gamut will not give both.

    ``_lch_to_rgb`` resolves an unreachable coordinate by holding L* and h and
    cutting C*. That is the right default — lightness and the harmony angle are
    what the palette is built on — but it silently destroys any distinction that
    lives in chroma alone. Two categories asking for C* 44 and C* 32 at L* 78
    both clip to the gamut ceiling of 32.9 and render as the same colour, which
    is exactly how the child_boy/child_girl split disappeared once the L* band
    was widened enough for their +8 lightness delta to take effect.

    So when chroma is the thing being asked for, spend lightness to buy it:
    walk L* down (never up, never more than CHROMA_LIGHTNESS_GIVEBACK, never
    below the paint band) to the highest value that can carry the requested
    chroma.

    Scanned rather than bisected, deliberately. Available chroma is NOT monotonic
    in lightness — it rises to a per-hue peak and falls away either side, and
    that peak sits at a very different L* for yellow than for blue. A bisection
    assuming monotonicity quietly returned the floor for hues where the trade
    does not exist, which cost the plain room palettes 12 points of lightness
    and bought them nothing.

    Two invariants, both learned the hard way:

    **Never pay lightness without gaining chroma.** Returning the floor when the
    trade does not exist cost the plain room palettes 12 points of lightness for
    nothing.

    **A larger chroma request must never produce a smaller result.** Falling
    back to "no trade at all" when the full request is unreachable broke that:
    child_girl (asking +6) found a lightness that fit and rendered C* 44.7, while
    child_boy (asking +18) found none, stayed put and clipped to C* 32.6 — the
    more saturated category came out less saturated. So when the request cannot
    be met in full, aim at the best chroma the range can actually deliver rather
    than giving up on the trade entirely.
    """
    available_here = _max_in_gamut_chroma(lightness, hue_deg)
    if available_here >= chroma:
        return lightness                      # nothing to trade, already fits

    floor = max(PAINT_LIGHTNESS[0], lightness - CHROMA_LIGHTNESS_GIVEBACK)
    steps = 24
    candidates = [
        lightness - (lightness - floor) * (i / steps) for i in range(steps + 1)
    ]
    reachable = [(cand, _max_in_gamut_chroma(cand, hue_deg)) for cand in candidates]

    # Aim for the request, or for the best this hue can do in range if that is
    # less. Capping the target at what is achievable is what keeps the result
    # monotonic in the request.
    target = min(chroma, max(available for _, available in reachable))
    if target <= available_here:
        return lightness                      # no trade would improve on staying

    return max(cand for cand, available in reachable if available >= target)


def _paint_color(
    lightness: float,
    chroma: float,
    hue_deg: float,
    neutral: bool = False,
) -> str:
    """Clamp one LCh triple into the interior-paint band and render it to hex.

    The hue angle passes through untouched — constraining only ever moves a
    colour along the L* and C* axes, so whatever harmony relationship put it at
    this angle survives the constraint step intact.
    """
    lightness = _clamp(lightness, *PAINT_LIGHTNESS)
    chroma = NEUTRAL_CHROMA if neutral else _clamp(chroma, *PAINT_CHROMA)
    if not neutral:
        # The neutral swatch is a near-grey by definition, so it has no chroma
        # worth defending and must keep the lightness it was given.
        lightness = _fit_lightness_for_chroma(lightness, chroma, hue_deg)
    return _lch_to_hex(lightness, chroma, hue_deg)


# --------------------------------------------------------------------------- #
# Dominant-colour extraction
# --------------------------------------------------------------------------- #

def _chromatic_gate(lch: np.ndarray) -> np.ndarray:
    """Boolean mask of pixels carrying a usable hue.

    Drops the three cases whose LCh hue angle is meaningless: near-white
    (L* > 85), near-black (L* < 15), and anything hugging the neutral axis
    (C* < 10). For those, ``h`` is determined by a couple of least-significant
    bits of sensor noise, so letting them into k-means seeds the harmony rules
    with a random angle.
    """
    return (
        (lch[:, 0] <= SEED_MAX_LIGHTNESS)
        & (lch[:, 0] >= SEED_MIN_LIGHTNESS)
        & (lch[:, 1] >= SEED_MIN_CHROMA)
    )


def _sample_lab(frame_bgr: np.ndarray, mask: np.ndarray | None) -> np.ndarray | None:
    """Masked pixels -> (N,3) CIE Lab, subsampled. None if the region is too small.

    Split out from ``extract_dominant_colors`` so the two reads a recommendation
    needs (unfiltered for context, gated for the seed) share one selection and
    one colour conversion instead of repeating both.
    """
    if mask is None:
        pixels = frame_bgr.reshape(-1, 3)
    else:
        pixels = frame_bgr[mask]

    if pixels.shape[0] < MIN_REGION_PIXELS:
        return None

    if pixels.shape[0] > MAX_SAMPLE_PIXELS:
        # Fixed seed: the same photo must always yield the same recommendation,
        # otherwise the palette flickers between identical uploads.
        rng = np.random.default_rng(0)
        idx = rng.choice(pixels.shape[0], MAX_SAMPLE_PIXELS, replace=False)
        pixels = pixels[idx]

    return _rgb_to_lab(pixels[:, ::-1])         # OpenCV hands us BGR


def _cluster_lab(lab: np.ndarray, k: int) -> list[dict]:
    """k-means over Lab points, returned as colour dicts sorted by area share."""
    lab32 = np.ascontiguousarray(lab, dtype=np.float32)

    distinct = np.unique(lab32, axis=0).shape[0]
    clusters = int(max(1, min(k, distinct)))

    # cv2.kmeans draws its k-means++ initial centres from OpenCV's own global
    # RNG, which is NOT covered by the fixed sampling seed above. Left alone it
    # re-seeds per call, so the same photo uploaded twice could land on
    # different centroids and return a visibly different palette — a real source
    # of the inconsistency this module was reworked to fix. Pin it per call so
    # the result is reproducible, which a thesis result has to be.
    cv2.setRNGSeed(0)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 1.0)
    _, labels, centers = cv2.kmeans(
        lab32, clusters, None, criteria, 3, cv2.KMEANS_PP_CENTERS
    )
    labels = labels.ravel()

    results: list[dict] = []
    for i, center in enumerate(centers):
        share = float(np.count_nonzero(labels == i)) / float(labels.size)
        centre_rgb = _lab_to_rgb(np.array([center], dtype=np.float64))[0]
        rgb_tuple = (int(centre_rgb[0]), int(centre_rgb[1]), int(centre_rgb[2]))
        lch = _rgb_to_lch(np.array([rgb_tuple], dtype=np.uint8))[0]
        results.append(
            {
                "hex": rgb_to_hex(rgb_tuple),
                "name": name_color(rgb_tuple),
                "share": round(share, 4),
                "_rgb": rgb_tuple,
                "_lch": (float(lch[0]), float(lch[1]), float(lch[2])),
            }
        )

    results.sort(key=lambda c: -c["share"])
    return results


def extract_dominant_colors(
    frame_bgr: np.ndarray,
    mask: np.ndarray | None = None,
    k: int = DEFAULT_K,
    chromatic_only: bool = False,
) -> list[dict]:
    """Cluster the masked pixels and return colours sorted by area share.

    ``mask`` is a boolean HxW array selecting the pixels to consider; None means
    the whole frame. Returns [] when there is not enough pixel data to trust.

    ``chromatic_only`` applies the LCh seed gate before clustering, so the
    result describes the room's *colour* rather than its area. It defaults off:
    the unfiltered call is still what the UI's context breakdown wants, since
    there "70% of this room is off-white" is true and worth showing. Only the
    palette seed needs the filtered view.
    """
    lab = _sample_lab(frame_bgr, mask)
    if lab is None:
        return []

    if chromatic_only:
        lab = _gate_lab(lab)
        if lab is None:
            return []

    return _cluster_lab(lab, k)


def _gate_lab(lab: np.ndarray) -> np.ndarray | None:
    """Apply the chromatic gate to Lab points. None if too little survives.

    A genuinely neutral room (white walls, grey carpet, nothing colourful in
    frame) legitimately has no dominant hue. Returning None lets the caller say
    so, rather than seeding a palette off a handful of noisy stray pixels.
    """
    keep = _chromatic_gate(_lab_to_lch(lab))
    if int(np.count_nonzero(keep)) < MIN_SEED_PIXELS:
        return None
    return lab[keep]


def extract_reference_seed(reference_frame_bgr: np.ndarray) -> dict | None:
    """Dominant *chromatic* colour of an optional reference / mood image.

    Same three steps the room's palette seed goes through — sample, chromatic
    gate, cluster — so both seeds are read in the same units by the same
    estimator and are meaningful to blend against each other.

    ``mask=None`` on purpose: a reference is a mood shot, a catalogue page,
    somebody else's living room. There is no wall of *ours* in it to segment,
    and nothing in it to exclude — the whole point is the colour the user liked.

    Returns None when the reference has no usable hue (a near-white or
    near-black image, or one too small to read), which the caller must treat as
    "no reference" rather than blending in a noise-derived angle.

    Picks by SALIENCE, not area — this is the one place the two questions come
    apart. For the room photo, "what colour is this room" is genuinely an
    area question, and the largest gated cluster is the right answer. A mood
    board is not describing a room; it is pointing at an accent. On the first
    real reference tried here — a pink Hello Kitty wall — the wood bed frame and
    warm mid-tones out-voted the pink 55/45 on area alone, so the "reference"
    seed came back terracotta and the palette had no pink anywhere in it. The
    backdrop wins on pixels almost every time; the thing the user actually
    pointed at wins on colourfulness.
    """
    lab = _sample_lab(reference_frame_bgr, None)
    if lab is None:
        return None

    gated = _gate_lab(lab)
    if gated is None:
        return None

    clusters = _cluster_lab(gated, DEFAULT_K)
    if not clusters:
        return None

    # share x chroma: a large muted region and a small vivid one can still beat
    # each other, which is the behaviour we want, but neither wins on its own.
    # The share floor stops a stray highlight or a JPEG artefact — a handful of
    # very colourful pixels — from defining the whole palette.
    candidates = [c for c in clusters if c["share"] >= MIN_REFERENCE_CLUSTER_SHARE]
    if not candidates:
        candidates = clusters
    return max(candidates, key=lambda c: c["share"] * c["_lch"][1])


def _blend_seeds(room_seed: dict, reference_seed: dict) -> dict:
    """Weighted LCh blend of the room's seed and a reference image's seed.

    L* and C* are plain weighted averages — both are linear magnitudes, so that
    is well defined. Hue is not: it is an angle, so it goes through
    ``_circular_mean_hue`` instead.

    The blended triple is rendered through ``_lch_to_rgb`` (gamut-mapped, since
    a blend of two in-gamut colours can still land outside sRGB) and then read
    back to LCh, so the seed handed on to ``build_palette`` describes a colour
    that can actually be displayed rather than a coordinate that cannot.

    Carries no ``share``: a blend of two images has no single area share, and
    inventing one would put a false percentage in the UI. Shares are reported
    per-image via ``dominant_color`` / ``reference_dominant_color`` instead.
    """
    room_lightness, room_chroma, room_hue = room_seed["_lch"]
    ref_lightness, ref_chroma, ref_hue = reference_seed["_lch"]

    weight = REFERENCE_SEED_WEIGHT
    lightness = weight * ref_lightness + (1.0 - weight) * room_lightness
    chroma = weight * ref_chroma + (1.0 - weight) * room_chroma

    # Only average hues that MEAN something. This is the same test the gate
    # applies per-pixel and build_palette applies to the centroid, and the blend
    # was the one place in the module that skipped it: a neutral room reaches
    # here via the neutral_room_fallback path carrying a centroid whose hue is
    # sensor noise, and a plain circular mean let that noise drag the reference
    # by up to 40% of the way. Measured on a grey room (C* 1.1, "hue" 19.5 deg)
    # against a pink reference: the pink came out 33 deg toward amber, i.e.
    # salmon, on the strength of an angle that was not a colour at all.
    room_hue_is_meaningful = room_chroma >= SEED_MIN_CHROMA
    ref_hue_is_meaningful = ref_chroma >= SEED_MIN_CHROMA

    if room_hue_is_meaningful and ref_hue_is_meaningful:
        hue = _circular_mean_hue(ref_hue, room_hue, weight)
    elif ref_hue_is_meaningful:
        hue = ref_hue          # neutral room — the reference is the only hue here
    elif room_hue_is_meaningful:
        hue = room_hue         # near-grey reference; unusual, the gate normally catches it
    else:
        # Neither carries a hue. Nothing to average, and build_palette will
        # detect the low blended chroma and take the warm-neutral path anyway.
        hue = ref_hue

    rgb = _lch_to_rgb(lightness, chroma, hue)
    lch = _rgb_to_lch(np.array([rgb], dtype=np.uint8))[0]

    return {
        "hex": rgb_to_hex(rgb),
        "name": name_color(rgb),
        "_rgb": rgb,
        "_lch": (float(lch[0]), float(lch[1]), float(lch[2])),
    }


def _public_color(cluster: dict) -> dict:
    """A clustered colour stripped to the fields the API reports.

    The ``_rgb``/``_lch`` working values stay internal — they are numpy-derived
    tuples the JSON layer has no use for, and the UI reads colours as hex.
    """
    return {"hex": cluster["hex"], "name": cluster["name"], "share": cluster["share"]}


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

def build_palette(
    dominant_rgb,
    dominant_name: str,
    category: str = "none",
    seed_origin: str = "room",
) -> dict:
    """One complementary primary + five relationship-based alternatives.

    Every relationship is a rotation of the seed's LCh hue angle. Lightness and
    chroma are then clamped into the paint band, which is safe to do afterwards
    precisely because LCh keeps those axes independent of hue — the same reason
    the old HSL implementation could not do this without also disturbing the
    hue it had just computed.

    ``category`` is a CATEGORY_BIAS key ("who is this room for?"). Unknown keys
    fall back to "none", i.e. no bias, so a stale value from a caller can never
    break a recommendation.

    ``seed_origin`` ("room" | "blend" | "reference") says what the seed MEANS,
    and two things depend on it: whether the recommended swatch opposes the seed
    or sits on it (see the block below), and the wording of the rationale text —
    once a reference image contributes to the seed, the palette is not derived
    from the room's colour alone and the explanation must not keep claiming it
    was.
    """
    lightness, chroma, hue = (
        float(v) for v in _rgb_to_lch(np.array([dominant_rgb], dtype=np.uint8))[0]
    )

    # A near-grey seed has a meaningless hue, so anchor off a warm neutral
    # instead of amplifying sensor noise into a confident hue claim. Same test
    # the seed gate applies per-pixel, now applied to the clustered centroid.
    hue_is_meaningful = chroma >= SEED_MIN_CHROMA
    base_hue = hue if hue_is_meaningful else WARM_ANCHOR_DEG

    # Chroma floor before clamping: a seed read off a muted floorboard should
    # still produce a wall colour with visible colour in it.
    base_chroma = max(chroma, PAINT_CHROMA[0])

    # Demographic lean, applied once to the shared seed and therefore inherited
    # by every swatch below — the recommended colour and all five alternatives
    # shift together instead of the palette losing its internal coherence.
    #
    # Deliberately AFTER hue_is_meaningful is decided: whether the room has a
    # readable hue is a property of the photograph, and a category can bias that
    # hue but must not be able to conjure one out of a neutral room.
    bias = CATEGORY_BIAS.get(category, CATEGORY_BIAS["none"])
    lightness += bias["lightness_delta"]
    base_chroma += bias["chroma_delta"]
    base_hue = _shift_hue(base_hue, bias["hue_nudge_deg"])

    # --------------------------------------------------------------------- #
    # Which way to point the recommendation depends on what the seed MEANS.
    #
    # A room photo answers "what must this wall hold its own against?", so the
    # useful answer is the visual opposite — the wall separates from the floor
    # and furniture instead of sinking into them. A reference image answers the
    # opposite question, "what do I want this room to look like?", and rotating
    # THAT by 180 deg turns the user's stated intent into the one colour the
    # palette is guaranteed not to contain. Uploading a pink reference returned
    # teal, every time, by construction. Same seed pipeline, opposite intent, so
    # the rotation has to be conditional on where the seed came from.
    # --------------------------------------------------------------------- #
    seed_follows_reference = seed_origin in ("blend", "reference")

    if not hue_is_meaningful:
        # No hue to oppose, so there is nothing for a 180 deg rotation to mean.
        # Rotating anyway is what made a grey room recommend a cold blue: the
        # fallback hue is the WARM anchor, and its complement is slate. Sit on
        # the anchor itself so the swatch matches the warm-neutral rationale
        # printed alongside it.
        recommended_hue = base_hue
        recommended_relationship = "warm-neutral"
    elif seed_follows_reference:
        # Sit ON the reference's hue. The alternatives below still fan out
        # around it — including the triadic and cool options — so contrast is
        # one click away rather than forced on someone who asked for pink.
        recommended_hue = base_hue
        recommended_relationship = "reference-match"
    else:
        # Complementary — 180 deg on the perceptual wheel, i.e. the true visual
        # opposite of the room's dominant hue.
        recommended_hue = _shift_hue(base_hue, 180.0)
        recommended_relationship = "complementary"

    recommended_hex = _paint_color(lightness, base_chroma, recommended_hue)

    variants = [
        # Analogous: a neighbour on the wheel. 30 deg in LCh is a smaller
        # apparent step than 30 deg in HSL over most of the circle, so this
        # reads as the quiet option it is meant to be.
        ("analogous", _paint_color(58.0, base_chroma * 0.85, _shift_hue(base_hue, 30.0))),
        # Triadic: an exact third of the wheel.
        ("triadic", _paint_color(55.0, base_chroma * 0.8, _shift_hue(base_hue, 120.0))),
        # Neutral: the seed's hue held at near-zero chroma, so it stays a grey
        # that leans the room's way rather than a colour.
        ("neutral", _paint_color(68.0, 0.0, base_hue, neutral=True)),
        ("warm", _paint_color(60.0, base_chroma * 0.9, _anchor_hue(base_hue, WARM_ANCHOR_DEG))),
        ("cool", _paint_color(56.0, base_chroma * 0.9, _anchor_hue(base_hue, COOL_ANCHOR_DEG))),
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

    # Name the seed for what it actually is. With a reference image in the mix
    # the palette is no longer derived from the room alone, and the rationale is
    # the one place the user reads where a suggestion came from.
    seed_phrase, neutral_phrase = SEED_ORIGIN_PHRASES.get(
        seed_origin, SEED_ORIGIN_PHRASES["room"]
    )

    if hue_is_meaningful and seed_follows_reference:
        rationale = (
            f"{seed_phrase} {dominant_name} ({rgb_to_hex(dominant_rgb)}). "
            f"This suggestion stays on that hue rather than opposing it — a reference image says "
            f"what you want the room to look like, so the palette follows it. Lightness and "
            f"colourfulness are held in the interior-paint range so it still reads as a wall "
            f"colour over a large area. The alternatives below fan out around the same hue if "
            f"you want more contrast than a match."
        )
    elif hue_is_meaningful:
        rationale = (
            f"{seed_phrase} {dominant_name} ({rgb_to_hex(dominant_rgb)}). "
            f"This suggestion sits opposite it on the perceptual colour wheel (CIE LCh), so the "
            f"wall separates cleanly from the floor and furniture instead of blending into them. "
            f"Lightness and colourfulness are held in the interior-paint range so the contrast "
            f"stays comfortable over a large area."
        )
    else:
        rationale = (
            f"{neutral_phrase} ({dominant_name}, {rgb_to_hex(dominant_rgb)}), "
            f"so there is no strong hue to complement. This is a soft warm tone that adds "
            f"colour without competing with the existing furnishings."
        )

    return {
        "recommended": {
            "hex": recommended_hex,
            "name": recommended_name,
            "description": rationale,
            "relationship": recommended_relationship,
        },
        "alternatives": alternatives,
    }


def recommend_colors(
    frame_bgr: np.ndarray,
    detections: list[dict],
    reference_frame_bgr: np.ndarray | None = None,
    category: str = "none",
) -> dict:
    """Full recommendation for one segmented frame.

    ``detections`` are the dicts produced by ``app.parse_detections`` and must
    still carry their internal ``_mask`` arrays.

    Two reads are taken of the same region. ``context_colors`` is unfiltered and
    answers "what is in this room, by area" — that is what the UI breakdown
    shows. The palette seed comes from a second, LCh-gated pass that answers
    "what colour is this room", which is a different question whenever the room
    is mostly neutral, i.e. almost always.

    ``reference_frame_bgr`` is an optional second upload — what the user wants
    the room to look like, not another view of the wall. When present and
    readable, its own gated seed is blended into the room's at
    ``REFERENCE_SEED_WEIGHT`` before any harmony rule runs. ``category`` is a
    CATEGORY_BIAS key. Both are optional and default to today's behaviour
    exactly; neither can fail the request, only be reported as unused.
    """
    height, width = frame_bgr.shape[:2]
    mask, source = build_context_mask(detections, height, width)

    # One selection and one sRGB->Lab conversion feeds both reads.
    lab = _sample_lab(frame_bgr, mask)
    context_colors = [] if lab is None else _cluster_lab(lab, DEFAULT_K)

    gated = None if lab is None else _gate_lab(lab)
    seed_colors = [] if gated is None else _cluster_lab(gated, DEFAULT_K)

    # Read the reference before deciding on the room seed: if the room turns out
    # to be unreadable, a usable reference is still a far better basis for a
    # palette than the hardcoded warm neutral.
    reference_seed = (
        None if reference_frame_bgr is None else extract_reference_seed(reference_frame_bgr)
    )

    # Report the category that was really applied, not the one that was asked
    # for — build_palette silently ignores an unknown key, and the response must
    # not claim a bias that did not happen.
    category_applied = category if category in CATEGORY_BIAS else "none"

    if seed_colors:
        seed = seed_colors[0]
        seed_source = "chromatic_pixels"
    elif context_colors:
        # Region is readable but genuinely neutral. Seed off its dominant colour
        # anyway; build_palette detects the low chroma and takes the warm-neutral
        # path rather than rotating a meaningless hue.
        seed = context_colors[0]
        seed_source = "neutral_room_fallback"
    elif reference_seed is not None:
        # Nothing readable in the room, but the user did supply a reference. Use
        # it on its own rather than discarding an input they explicitly gave.
        palette = build_palette(
            reference_seed["_rgb"],
            reference_seed["name"],
            category=category_applied,
            seed_origin="reference",
        )
        palette.update(
            {
                "dominant_color": None,
                "context_colors": [],
                "context_source": "unavailable",
                "context_pixel_ratio": 0.0,
                "seed_source": "reference_only",
                "reference_used": True,
                # 1.0, not REFERENCE_SEED_WEIGHT: there was no readable room
                # seed to blend against, so the reference carried the palette
                # outright. Reporting 0.7 here would be a lie the UI repeats.
                "reference_weight": 1.0,
                "reference_dominant_color": _public_color(reference_seed),
                "category_applied": category_applied,
            }
        )
        return palette
    else:
        # Nothing readable at all — recommend from a warm neutral and say so.
        fallback_rgb = (200, 190, 178)
        palette = build_palette(
            fallback_rgb, name_color(fallback_rgb), category=category_applied
        )
        palette.update(
            {
                "dominant_color": None,
                "context_colors": [],
                "context_source": "unavailable",
                "context_pixel_ratio": 0.0,
                "seed_source": "unavailable",
                "reference_used": False,
                "reference_weight": None,
                "reference_dominant_color": None,
                "category_applied": category_applied,
            }
        )
        return palette

    # A reference with no usable hue is reported as unused rather than blended:
    # its seed would be an angle read off near-white or near-black pixels, which
    # is exactly the noise the chromatic gate exists to keep out of the palette.
    reference_used = reference_seed is not None
    palette_seed = _blend_seeds(seed, reference_seed) if reference_used else seed

    palette = build_palette(
        palette_seed["_rgb"],
        palette_seed["name"],
        category=category_applied,
        seed_origin="blend" if reference_used else "room",
    )
    palette.update(
        {
            # The room's own dominant colour, with the area share it was read
            # from. Kept as the room's even when a reference is blended in — the
            # blend is reported separately, and this field answers "what colour
            # is this room", which the reference does not change.
            "dominant_color": _public_color(seed),
            "context_colors": [
                {k: v for k, v in c.items() if not k.startswith("_")}
                for c in context_colors
            ],
            "context_source": source,
            "context_pixel_ratio": round(
                float(np.count_nonzero(mask)) / float(height * width), 4
            ),
            "seed_source": seed_source,
            "reference_used": reference_used,
            # The weight actually applied, so the UI never has to hardcode a
            # number that can drift out of step with this module.
            "reference_weight": REFERENCE_SEED_WEIGHT if reference_used else None,
            "reference_dominant_color": (
                _public_color(reference_seed) if reference_used else None
            ),
            "category_applied": category_applied,
        }
    )
    return palette
