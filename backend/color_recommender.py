"""
AURA — Colour recommendation from room context.

Pipeline
--------
1. Take the YOLOv8 detections for a frame and build a mask of everything that
   is NOT paintable wall — floor, furniture, ceiling, fixtures.
2. Discard pixels that carry no usable hue (near-white, near-black, near-grey)
   and cluster what remains to find the room's dominant *chromatic* colour.
3. Apply colour-wheel relationships to that colour, in CIE LCh, to propose one
   primary wall colour plus five alternatives.

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
# L* 30-70 keeps a colour off both ends of the lightness range: below ~30 a wall
# reads as near-black under domestic lighting, above ~70 it washes out to an
# off-white and the hue relationship stops being visible at all. C* 20-60 keeps
# it clear of the neutral axis (C* < ~10 is grey) without reaching the
# poster-paint chroma that becomes oppressive over a whole wall.
#
# NOTE these are deliberately narrower than the range of real emulsion. Many
# catalogue interior colours sit above L* 70 (pale neutrals) or below C* 20
# (muted sages and greys); those are reachable through the fixed NEUTRAL_COLORS
# chips rather than through harmony generation. Widening the band is a
# one-line change here if the thesis evaluation calls for it.
# --------------------------------------------------------------------------- #

PAINT_LIGHTNESS = (30.0, 70.0)   # L*
PAINT_CHROMA = (20.0, 60.0)      # C*

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


def _paint_color(
    lightness: float,
    chroma: float,
    hue_deg: float,
    neutral: bool = False,
) -> str:
    """Clamp one LCh triple into the interior-paint band and render it to hex.

    The hue angle passes through untouched — clamping only ever moves a colour
    along the L* and C* axes, so whatever harmony relationship put it at this
    angle survives the constraint step intact.
    """
    lightness = _clamp(lightness, *PAINT_LIGHTNESS)
    chroma = NEUTRAL_CHROMA if neutral else _clamp(chroma, *PAINT_CHROMA)
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
    """One complementary primary + five relationship-based alternatives.

    Every relationship is a rotation of the seed's LCh hue angle. Lightness and
    chroma are then clamped into the paint band, which is safe to do afterwards
    precisely because LCh keeps those axes independent of hue — the same reason
    the old HSL implementation could not do this without also disturbing the
    hue it had just computed.
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

    if hue_is_meaningful:
        # Complementary — 180 deg on the perceptual wheel, i.e. the true visual
        # opposite of the room's dominant hue.
        recommended_hue = _shift_hue(base_hue, 180.0)
        recommended_relationship = "complementary"
    else:
        # No hue to oppose, so there is nothing for a 180 deg rotation to mean.
        # Rotating anyway is what made a grey room recommend a cold blue: the
        # fallback hue is the WARM anchor, and its complement is slate. Sit on
        # the anchor itself so the swatch matches the warm-neutral rationale
        # printed alongside it.
        recommended_hue = base_hue
        recommended_relationship = "warm-neutral"

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

    if hue_is_meaningful:
        rationale = (
            f"The room's dominant colour reads as {dominant_name} ({rgb_to_hex(dominant_rgb)}). "
            f"This suggestion sits opposite it on the perceptual colour wheel (CIE LCh), so the "
            f"wall separates cleanly from the floor and furniture instead of blending into them. "
            f"Lightness and colourfulness are held in the interior-paint range so the contrast "
            f"stays comfortable over a large area."
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
            "relationship": recommended_relationship,
        },
        "alternatives": alternatives,
    }


def recommend_colors(frame_bgr: np.ndarray, detections: list[dict]) -> dict:
    """Full recommendation for one segmented frame.

    ``detections`` are the dicts produced by ``app.parse_detections`` and must
    still carry their internal ``_mask`` arrays.

    Two reads are taken of the same region. ``context_colors`` is unfiltered and
    answers "what is in this room, by area" — that is what the UI breakdown
    shows. The palette seed comes from a second, LCh-gated pass that answers
    "what colour is this room", which is a different question whenever the room
    is mostly neutral, i.e. almost always.
    """
    height, width = frame_bgr.shape[:2]
    mask, source = build_context_mask(detections, height, width)

    # One selection and one sRGB->Lab conversion feeds both reads.
    lab = _sample_lab(frame_bgr, mask)
    context_colors = [] if lab is None else _cluster_lab(lab, DEFAULT_K)

    gated = None if lab is None else _gate_lab(lab)
    seed_colors = [] if gated is None else _cluster_lab(gated, DEFAULT_K)

    if seed_colors:
        seed = seed_colors[0]
        seed_source = "chromatic_pixels"
    elif context_colors:
        # Region is readable but genuinely neutral. Seed off its dominant colour
        # anyway; build_palette detects the low chroma and takes the warm-neutral
        # path rather than rotating a meaningless hue.
        seed = context_colors[0]
        seed_source = "neutral_room_fallback"
    else:
        # Nothing readable at all — recommend from a warm neutral and say so.
        fallback_rgb = (200, 190, 178)
        palette = build_palette(fallback_rgb, name_color(fallback_rgb))
        palette.update(
            {
                "dominant_color": None,
                "context_colors": [],
                "context_source": "unavailable",
                "context_pixel_ratio": 0.0,
                "seed_source": "unavailable",
            }
        )
        return palette

    palette = build_palette(seed["_rgb"], seed["name"])
    palette.update(
        {
            # The colour the palette was actually derived from, so the rationale
            # text and the swatch the UI shows next to it stay consistent.
            "dominant_color": {
                "hex": seed["hex"],
                "name": seed["name"],
                "share": seed["share"],
            },
            "context_colors": [
                {k: v for k, v in c.items() if not k.startswith("_")}
                for c in context_colors
            ],
            "context_source": source,
            "context_pixel_ratio": round(
                float(np.count_nonzero(mask)) / float(height * width), 4
            ),
            "seed_source": seed_source,
        }
    )
    return palette
