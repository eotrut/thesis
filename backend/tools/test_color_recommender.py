"""
AURA — Colour recommendation invariant tests.

Standalone script, not part of the Flask app and not a pytest suite — same
shape as ``test_toolpath.py``: run it, read the summary, exit code says whether
anything broke.

It exercises ``color_recommender`` directly on synthetic frames rather than
through the API, so it needs no model, no weights and no server. Segmentation
is not what is under test here; the colour maths is. Every case passes
``detections=[]``, which sends ``build_context_mask`` down its whole-frame
fallback — deliberate, because it makes the input to the palette exactly
reproducible instead of dependent on what YOLOv8 happened to find.

Why this file exists
--------------------
Three rounds of fixes on 2026-08-08 each broke something the round before had
established, and every check was an ad-hoc script that was thrown away
afterwards. Two of those regressions (a lightness give-back that paid for
nothing, and a chroma request that came back smaller when asked to be larger)
would have been caught immediately by the invariants below. They are properties
of the module rather than golden hex values on purpose: the constants are
explicitly a tuning target for the evaluator study, so a test that pins exact
colours would fail every time a constant is legitimately re-tuned, and would
get deleted rather than fixed. These assertions should survive re-tuning.

What is NOT covered
-------------------
Anything requiring a real photograph. Every frame here is synthetic, so this
says nothing about whether the palettes look good — only that the module holds
its own rules. See the vault note's "Still open" for the real-photo gap.

Run:
    python backend/tools/test_color_recommender.py
    python backend/tools/test_color_recommender.py -v
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import color_recommender as cr  # noqa: E402


# --------------------------------------------------------------------------- #
# Synthetic frames
#
# Chosen to hit each branch the module can take, not to look like rooms:
#   warm_room     a readable chromatic seed  -> chromatic_pixels
#   neutral_room  readable but near-grey     -> neutral_room_fallback
#   tiny_frame    below MIN_REGION_PIXELS    -> unavailable
#   pink_ref      a vivid accent over a pale backdrop, i.e. the shape of a real
#                 mood board: the backdrop wins on area, the accent on chroma
#   white_ref     no pixel survives the chromatic gate
# --------------------------------------------------------------------------- #

def warm_room() -> np.ndarray:
    frame = np.full((480, 640, 3), 235, np.uint8)
    frame[330:, :] = (60, 110, 170)          # timber floor, BGR
    frame[200:330, 60:280] = (150, 130, 60)  # teal sofa
    return frame


def neutral_room() -> np.ndarray:
    frame = np.full((480, 640, 3), 238, np.uint8)
    frame[330:, :] = (205, 205, 208)
    return frame


def tiny_frame() -> np.ndarray:
    return np.full((10, 10, 3), 240, np.uint8)


def pink_ref() -> np.ndarray:
    frame = np.zeros((600, 400, 3), np.uint8)
    frame[:, :] = (220, 230, 239)            # pale cream backdrop
    frame[430:520, :] = (245, 245, 245)
    frame[520:, :] = (90, 138, 192)          # wood — the area-dominant colour
    rng = np.random.default_rng(0)
    for _ in range(40):                      # pink accents — chroma-dominant
        y, x = rng.integers(20, 400), rng.integers(10, 380)
        frame[y:y + 26, x:x + 26] = (126, 71, 228)
    return frame


def white_ref() -> np.ndarray:
    return np.full((300, 300, 3), 250, np.uint8)


def lch_of(hex_value: str) -> tuple[float, float, float]:
    values = cr._rgb_to_lch(np.array([cr.hex_to_rgb(hex_value)], np.uint8))[0]
    return float(values[0]), float(values[1]), float(values[2])


def swatches(palette: dict) -> list[dict]:
    return [palette["recommended"]] + palette["alternatives"]


# --------------------------------------------------------------------------- #
# Checks. Each returns a list of failure strings; empty means it passed.
# --------------------------------------------------------------------------- #

def check_band_containment(verbose: bool) -> list[str]:
    """No swatch may leave the interior-paint band.

    The band is the module's central promise — a wall colour is not a poster
    colour — and every constant change so far has risked pushing something out
    of it. Tolerance allows for the 8-bit hex round trip only.
    """
    failures = []
    low, high = cr.PAINT_LIGHTNESS
    for room_name, room in (("warm", warm_room()), ("neutral", neutral_room())):
        for ref_name, ref in (("none", None), ("pink", pink_ref())):
            for category in cr.CATEGORY_BIAS:
                palette = cr.recommend_colors(
                    room, [], reference_frame_bgr=ref, category=category
                )
                for swatch in swatches(palette):
                    lightness, chroma, _ = lch_of(swatch["hex"])
                    if not (low - 2.0 <= lightness <= high + 2.0):
                        failures.append(
                            f"{room_name}/{ref_name}/{category}: {swatch['hex']} "
                            f"L*={lightness:.1f} outside {cr.PAINT_LIGHTNESS}"
                        )
                    if chroma > cr.PAINT_CHROMA[1] + 2.0:
                        failures.append(
                            f"{room_name}/{ref_name}/{category}: {swatch['hex']} "
                            f"C*={chroma:.1f} above {cr.PAINT_CHROMA[1]}"
                        )
    if verbose:
        print("    28 room x reference x category combinations, 6 swatches each")
    return failures


def check_unique_names(verbose: bool) -> list[str]:
    """Two swatches showing different hexes under one name reads as a bug."""
    failures = []
    for room_name, room in (("warm", warm_room()), ("neutral", neutral_room())):
        for ref_name, ref in (("none", None), ("pink", pink_ref())):
            for category in cr.CATEGORY_BIAS:
                palette = cr.recommend_colors(
                    room, [], reference_frame_bgr=ref, category=category
                )
                names = [s["name"] for s in swatches(palette)]
                if len(names) != len(set(names)):
                    failures.append(
                        f"{room_name}/{ref_name}/{category}: duplicate name in {names}"
                    )
    return failures


def check_determinism(verbose: bool) -> list[str]:
    """The same photo must always give the same palette.

    Both RNGs involved are pinned (numpy for subsampling, cv2's global for
    k-means++ seeding). A thesis result that changes between identical runs is
    not a result.
    """
    failures = []
    room, ref = warm_room(), pink_ref()
    first = cr.recommend_colors(room, [], reference_frame_bgr=ref, category="teen")
    for run in range(3):
        again = cr.recommend_colors(room, [], reference_frame_bgr=ref, category="teen")
        if [s["hex"] for s in swatches(first)] != [s["hex"] for s in swatches(again)]:
            failures.append(f"run {run + 1} differed from the first")
    return failures


def check_graceful_degradation(verbose: bool) -> list[str]:
    """Optional inputs may be ignored, never fatal, and never misreported."""
    failures = []
    room = warm_room()

    baseline = cr.recommend_colors(room, [])
    if baseline["reference_used"] or baseline["reference_weight"] is not None:
        failures.append("no reference supplied but reference_used/weight set")

    # A reference with no readable hue must be dropped, and dropping it must
    # leave the palette byte-identical to not having sent one at all.
    dropped = cr.recommend_colors(room, [], reference_frame_bgr=white_ref())
    if dropped["reference_used"]:
        failures.append("white reference reported as used")
    if [s["hex"] for s in swatches(dropped)] != [s["hex"] for s in swatches(baseline)]:
        failures.append("dropped reference still changed the palette")

    # An unknown category must degrade to 'none', not error and not be echoed.
    bogus = cr.recommend_colors(room, [], category="wizard")
    if bogus["category_applied"] != "none":
        failures.append(f"unknown category echoed as {bogus['category_applied']!r}")
    if [s["hex"] for s in swatches(bogus)] != [s["hex"] for s in swatches(baseline)]:
        failures.append("unknown category still biased the palette")

    # Unreadable room, usable reference -> the reference carries it alone, and
    # the reported weight must say 1.0 rather than REFERENCE_SEED_WEIGHT.
    ref_only = cr.recommend_colors(tiny_frame(), [], reference_frame_bgr=pink_ref())
    if ref_only["seed_source"] != "reference_only":
        failures.append(f"seed_source was {ref_only['seed_source']!r}")
    if ref_only["reference_weight"] != 1.0:
        failures.append(f"reference-only weight was {ref_only['reference_weight']}")

    # Nothing readable at all still returns a full palette.
    nothing = cr.recommend_colors(tiny_frame(), [])
    if nothing["seed_source"] != "unavailable" or len(nothing["alternatives"]) != 5:
        failures.append("unreadable frame did not return the warm-neutral fallback")

    for palette, label in ((baseline, "baseline"), (ref_only, "reference_only")):
        for key in ("reference_used", "reference_weight", "reference_dominant_color",
                    "category_applied", "seed_source"):
            if key not in palette:
                failures.append(f"{label} response missing {key!r}")
    return failures


def check_relationship_semantics(verbose: bool) -> list[str]:
    """A reference is matched; a room photo alone is opposed.

    The distinction this guards is the one that made a pink reference return
    teal: the room answers "what must this wall contrast with?", a reference
    answers "what do I want it to look like?", and only the first wants a
    180 deg rotation.
    """
    failures = []
    for category in cr.CATEGORY_BIAS:
        palette = cr.recommend_colors(warm_room(), [], category=category)
        if palette["recommended"]["relationship"] != "complementary":
            failures.append(
                f"{category}: room-only gave "
                f"{palette['recommended']['relationship']!r}, expected complementary"
            )

    blended = cr.recommend_colors(warm_room(), [], reference_frame_bgr=pink_ref())
    if blended["recommended"]["relationship"] != "reference-match":
        failures.append(f"blend gave {blended['recommended']['relationship']!r}")

    nothing = cr.recommend_colors(tiny_frame(), [])
    if nothing["recommended"]["relationship"] != "warm-neutral":
        failures.append(f"no-usable-hue gave {nothing['recommended']['relationship']!r}")
    return failures


def check_reference_seed_is_salient(verbose: bool) -> list[str]:
    """The reference seed is the accent, not the backdrop.

    ``pink_ref`` is built so the wood outvotes the pink on area while losing on
    chroma — the shape of a real mood board. Selecting by area alone is what
    made a pink reference seed as terracotta.
    """
    failures = []
    seed = cr.extract_reference_seed(pink_ref())
    if seed is None:
        return ["no seed extracted from the pink reference"]

    _, chroma, hue = seed["_lch"]
    if chroma < 40.0:
        failures.append(f"seed chroma {chroma:.1f} — picked a muted cluster")
    if not (hue < 40.0 or hue > 330.0):
        failures.append(f"seed hue {hue:.1f} is not in the pink/red range")
    if verbose:
        print(f"    reference seed {seed['hex']} C*={chroma:.1f} h={hue:.1f}")
    return failures


def check_neutral_room_hue_not_averaged(verbose: bool) -> list[str]:
    """A near-grey room must not drag the reference's hue.

    The module discards meaningless hues per-pixel and per-centroid; the blend
    has to obey the same rule. It did not, and a C* 1.1 grey pulled a pink
    reference 33 deg toward amber.
    """
    ref = pink_ref()
    from_neutral = cr.recommend_colors(neutral_room(), [], reference_frame_bgr=ref)
    reference_only = cr.recommend_colors(tiny_frame(), [], reference_frame_bgr=ref)

    neutral_hue = lch_of(from_neutral["recommended"]["hex"])[2]
    alone_hue = lch_of(reference_only["recommended"]["hex"])[2]
    drift = abs((neutral_hue - alone_hue + 180.0) % 360.0 - 180.0)
    if verbose:
        print(f"    neutral-room hue {neutral_hue:.1f} vs reference-alone "
              f"{alone_hue:.1f} (drift {drift:.1f} deg)")
    if drift > 3.0:
        return [f"neutral room shifted the reference hue by {drift:.1f} deg"]
    return []


def check_chroma_monotonic(verbose: bool) -> list[str]:
    """Asking for more chroma must never return less.

    ``_fit_lightness_for_chroma`` trades lightness for chroma where the gamut
    binds. An early version gave up on the trade when the full request was
    unreachable, so a larger request could land on a smaller result — the more
    saturated demographic came out less saturated than the less saturated one.
    """
    failures = []
    for hue in range(0, 360, 15):
        best = -1.0
        for requested in (20.0, 30.0, 40.0, 50.0, 60.0):
            got = lch_of(cr._paint_color(78.0, requested, float(hue)))[1]
            if got < best - 0.75:
                failures.append(
                    f"hue {hue}: request {requested:.0f} gave C*={got:.1f}, "
                    f"below an earlier {best:.1f}"
                )
            best = max(best, got)
    return failures


def check_lightness_never_spent_for_nothing(verbose: bool) -> list[str]:
    """The chroma trade must not lower lightness without buying chroma.

    A bisection assuming available-chroma is monotonic in lightness returned
    the floor at hues where no trade exists, costing the plain room palettes
    12 points of lightness and gaining them none.
    """
    failures = []
    for hue in range(0, 360, 15):
        for lightness in (40.0, 55.0, 70.0, 82.0):
            for chroma in (25.0, 45.0, 60.0):
                fitted = cr._fit_lightness_for_chroma(lightness, chroma, float(hue))
                if fitted > lightness + 1e-6:
                    failures.append(f"hue {hue} L*{lightness}: raised lightness")
                if fitted < lightness - 1e-6:
                    gained = (cr._max_in_gamut_chroma(fitted, float(hue))
                              - cr._max_in_gamut_chroma(lightness, float(hue)))
                    if gained <= 0.0:
                        failures.append(
                            f"hue {hue} L*{lightness} C*{chroma}: dropped to "
                            f"L*{fitted:.1f} for no chroma gain"
                        )
    return failures


def check_demographic_distinctness(verbose: bool) -> list[str]:
    """Categories whose chroma deltas differ must render differently.

    Not covered by the monotonicity check above: plain clipping *is* monotonic,
    it just flattens everything above the ceiling onto the same value. That is
    precisely how child_boy and child_girl came to return the same hex — 12 C*
    apart in the table, both clipped to the sRGB ceiling at L* 78, so the
    gender split silently disappeared.

    Asserted at a pink hue, where the distinction is renderable. It genuinely
    is not renderable around cyan-blue (~200-230 deg), where the ceiling sits
    below both requests at every lightness in the band — that is sRGB, not a
    regression, and pinning it here would encode a false expectation.
    """
    failures = []
    room, ref = neutral_room(), pink_ref()
    boy = cr.recommend_colors(room, [], reference_frame_bgr=ref, category="child_boy")
    girl = cr.recommend_colors(room, [], reference_frame_bgr=ref, category="child_girl")

    boy_hex = boy["recommended"]["hex"]
    girl_hex = girl["recommended"]["hex"]
    if boy_hex == girl_hex:
        failures.append(f"child_boy and child_girl both rendered {boy_hex}")

    # The boy > girl ordering is the part Hao et al. actually supports, so it
    # has to survive whatever the magnitudes are re-tuned to.
    boy_chroma = lch_of(boy_hex)[1]
    girl_chroma = lch_of(girl_hex)[1]
    expected = (cr.CATEGORY_BIAS["child_boy"]["chroma_delta"]
                > cr.CATEGORY_BIAS["child_girl"]["chroma_delta"])
    if expected and boy_chroma <= girl_chroma:
        failures.append(
            f"child_boy C*={boy_chroma:.1f} is not above child_girl "
            f"C*={girl_chroma:.1f}, but its chroma_delta is higher"
        )
    if verbose:
        print(f"    child_boy {boy_hex} C*={boy_chroma:.1f} vs "
              f"child_girl {girl_hex} C*={girl_chroma:.1f}")
    return failures


def check_palette_is_one_family(verbose: bool) -> list[str]:
    """Alternatives must track the recommendation's lightness.

    They were absolute values tuned for the old L* 30-70 band; once the band
    reached 88 a pastel recommendation shipped with alternatives 13 L* darker
    and the palette stopped reading as a set. Excludes the neutral swatch,
    which is deliberately the lightest chip in the palette.
    """
    failures = []
    cases = (
        ("pastel", neutral_room(), pink_ref(), "child_girl"),
        ("mid", warm_room(), None, "none"),
        ("elderly-light", neutral_room(), pink_ref(), "elderly"),
    )
    for label, room, ref, category in cases:
        palette = cr.recommend_colors(
            room, [], reference_frame_bgr=ref, category=category
        )
        recommended = lch_of(palette["recommended"]["hex"])[0]
        for alternative in palette["alternatives"]:
            if alternative["relationship"] == "neutral":
                continue
            spread = abs(lch_of(alternative["hex"])[0] - recommended)
            if spread > 12.0:
                failures.append(
                    f"{label}: {alternative['relationship']} is {spread:.1f} L* "
                    f"from the recommendation"
                )
    return failures


CHECKS = (
    ("band containment", check_band_containment),
    ("unique swatch names", check_unique_names),
    ("determinism", check_determinism),
    ("graceful degradation", check_graceful_degradation),
    ("relationship semantics", check_relationship_semantics),
    ("reference seed is salient", check_reference_seed_is_salient),
    ("neutral room does not drag hue", check_neutral_room_hue_not_averaged),
    ("chroma monotonic in request", check_chroma_monotonic),
    ("lightness never spent for nothing", check_lightness_never_spent_for_nothing),
    ("demographic categories stay distinct", check_demographic_distinctness),
    ("palette reads as one family", check_palette_is_one_family),
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Invariant tests for backend/color_recommender.py"
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print what each check exercised")
    args = parser.parse_args()

    print(f"colour recommender — band L* {cr.PAINT_LIGHTNESS}, C* {cr.PAINT_CHROMA}, "
          f"reference weight {cr.REFERENCE_SEED_WEIGHT}\n")

    total_failures = 0
    for name, check in CHECKS:
        failures = check(args.verbose)
        total_failures += len(failures)
        print(f"  [{'FAIL' if failures else ' ok '}] {name}")
        for failure in failures:
            print(f"         {failure}")

    print()
    if total_failures:
        print(f"{total_failures} failure(s).")
        return 1
    print(f"All {len(CHECKS)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
