"""
AURA — Demographic colour template tests.

Standalone script, same shape as ``test_color_recommender.py``: run it, read
the summary, exit code says whether anything broke.

The templates are data, so what can break is (a) a palette drifting away from
the finding it cites when someone re-tunes a shade, (b) a swatch leaving the
paint band the scan flow is held to, (c) a citation or photo licence going
missing. Each check below is one of those rules.

The literature checks are written as DIRECTIONS (more saturated than, contains
a light blue, no green), the same way the recommender's own tests avoid golden
hex values: the exact shades are a design choice and are expected to be
re-tuned; the direction each one cites is not.

Run:
    python backend/tools/test_color_templates.py
    python backend/tools/test_color_templates.py -v
"""

from __future__ import annotations

import argparse
import os
import re
import sys

import numpy as np

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
UI_DIR = os.path.join(PROJECT_ROOT, "desktop", "ui")
sys.path.insert(0, BACKEND_DIR)

import color_recommender as cr  # noqa: E402
import color_templates as ct  # noqa: E402

BY_CAT = {t["category"]: t for t in ct.TEMPLATES}
WARM = lambda h: h >= 340 or h <= 100        # reds, oranges, yellows  # noqa: E731
COOL = lambda h: 180 <= h <= 290             # cyans and blues          # noqa: E731
GREEN = lambda h: 100 < h < 175              # noqa: E731


def colours(category):
    return [s for s in BY_CAT[category]["swatches"] if s["kind"] == "colour"]


def mean(values):
    values = list(values)
    return sum(values) / len(values)


def mean_l(category):
    return mean(s["lch"][0] for s in colours(category))


def mean_c(category):
    return mean(s["lch"][1] for s in colours(category))


def hex_to_lch(value):
    import colour

    rgb = np.array(cr.hex_to_rgb(value), dtype=float) / 255.0
    lab = colour.XYZ_to_Lab(colour.sRGB_to_XYZ(rgb))
    return colour.Lab_to_LCHab(lab)


# --------------------------------------------------------------------------- #
# Structure
# --------------------------------------------------------------------------- #

def check_one_template_per_category(verbose):
    cats = [t["category"] for t in ct.TEMPLATES]
    failures = []
    if sorted(cats) != sorted(cr.CATEGORY_BIAS):
        failures.append(f"template categories {sorted(cats)} != CATEGORY_BIAS {sorted(cr.CATEGORY_BIAS)}")
    if len(set(cats)) != len(cats):
        failures.append("a category has more than one template")
    return failures


def check_five_named_swatches(verbose):
    failures = []
    for t in ct.TEMPLATES:
        names = [s["name"] for s in t["swatches"]]
        if len(names) != 5:
            failures.append(f"{t['category']}: {len(names)} swatches, expected 5")
        if len(set(names)) != len(names):
            failures.append(f"{t['category']}: duplicate swatch names")
        for s in t["swatches"]:
            if s["kind"] not in ("colour", "neutral"):
                failures.append(f"{t['category']}/{s['name']}: kind {s['kind']!r}")
            if not s["why"].strip():
                failures.append(f"{t['category']}/{s['name']}: no 'why'")
    return failures


def check_paint_band(verbose):
    """Colours obey the recommender's paint band; neutrals its neutral limit."""
    lo_l, hi_l = cr.PAINT_LIGHTNESS
    lo_c, hi_c = cr.PAINT_CHROMA
    failures = []
    for t in ct.TEMPLATES:
        for s in t["swatches"]:
            l, c, _ = s["lch"]
            where = f"{t['category']}/{s['name']}"
            if s["kind"] == "colour":
                if not (lo_l <= l <= hi_l):
                    failures.append(f"{where}: L* {l} outside {cr.PAINT_LIGHTNESS}")
                if not (lo_c <= c <= hi_c):
                    failures.append(f"{where}: C* {c} outside {cr.PAINT_CHROMA}")
            elif c > cr.NEUTRAL_CHROMA:
                failures.append(f"{where}: neutral with C* {c} > {cr.NEUTRAL_CHROMA}")
    return failures


def check_hex_matches_lch(verbose):
    """The hex shown is the colour described (not gamut-clipped into another)."""
    failures = []
    worst = 0.0
    for t in ct.templates_payload()["templates"]:
        for s in t["swatches"]:
            if not re.fullmatch(r"#[0-9A-F]{6}", s["hex"]):
                failures.append(f"{t['category']}/{s['name']}: bad hex {s['hex']!r}")
                continue
            l, c, h = hex_to_lch(s["hex"])
            want = s["lch"]
            dl, dc = abs(l - want["l"]), abs(c - want["c"])
            dh = abs((h - want["h"] + 180) % 360 - 180) if want["c"] >= 10 else 0.0
            worst = max(worst, dl, dc)
            if dl > 1.0 or dc > 1.5 or dh > 3.0:
                failures.append(f"{t['category']}/{s['name']}: {s['hex']} is LCh "
                                f"({l:.1f}, {c:.1f}, {h:.0f}), asked for {tuple(want.values())}")
    if verbose:
        print(f"         worst L*/C* round-trip error {worst:.2f}")
    return failures


# --------------------------------------------------------------------------- #
# Citations and photos
# --------------------------------------------------------------------------- #

def check_citations(verbose):
    failures = []
    used = set()
    for t in ct.TEMPLATES:
        for s in t["swatches"]:
            if not s["basis"]:
                failures.append(f"{t['category']}/{s['name']}: no source")
            for key in s["basis"]:
                used.add(key)
                if key not in ct.REFERENCES:
                    failures.append(f"{t['category']}/{s['name']}: unknown source {key!r}")
    for key, ref in ct.REFERENCES.items():
        if not re.fullmatch(r"10\.\d{4,}/\S+", ref.get("doi", "")):
            failures.append(f"{key}: missing/odd DOI {ref.get('doi')!r}")
        if key not in used:
            failures.append(f"{key}: listed but no swatch cites it")
    if any("huang" in k.lower() for k in ct.REFERENCES):
        failures.append("Huang et al. (2009) is unverified and must not be cited")
    return failures


def check_photos(verbose):
    failures = []
    photo_dir = os.path.join(UI_DIR, *ct.PHOTO_DIR.split("/"))
    referenced = set()
    for t in ct.TEMPLATES:
        if len(t["photos"]) < 2:
            failures.append(f"{t['category']}: fewer than 2 example photos")
        for slug in t["photos"]:
            referenced.add(slug)
            meta = ct.PHOTOS.get(slug)
            if meta is None:
                failures.append(f"{slug}: no credit record")
                continue
            if not os.path.isfile(os.path.join(photo_dir, slug + ".jpg")):
                failures.append(f"{slug}: image file missing")
            if meta["license"] not in ct.ALLOWED_PHOTO_LICENSES:
                failures.append(f"{slug}: licence {meta['license']!r} not allowed")
            if meta["license"] != "Public domain" and not meta["license_url"].startswith("https://creativecommons.org/"):
                failures.append(f"{slug}: no licence link")
            if not meta["source"].startswith("https://commons.wikimedia.org/wiki/File:"):
                failures.append(f"{slug}: source is not a Commons file page")
            if not meta["author"].strip():
                failures.append(f"{slug}: no author")
            if "pinterest" in (meta["source"] + meta["origin"]).lower():
                failures.append(f"{slug}: Pinterest material is not allowed")
    bundled = {f[:-4] for f in os.listdir(photo_dir) if f.lower().endswith(".jpg")}
    for orphan in sorted(bundled - referenced):
        failures.append(f"{orphan}.jpg is bundled but has no credit record")
    for extra in sorted(set(ct.PHOTOS) - referenced):
        failures.append(f"{extra}: credit record for a photo no template uses")
    return failures


def check_wording(verbose):
    """Labelled as a tendency; never claimed as popularity."""
    payload = ct.templates_payload()
    failures = []
    if payload["label"] != "Research-supported tendency":
        failures.append(f"label is {payload['label']!r}")
    texts = [payload["disclaimer"]]
    for t in ct.TEMPLATES:
        texts += [t["name"], t["summary"], t["audience"], *t["caveats"]]
        texts += [s["why"] for s in t["swatches"]]
    banned = re.compile(r"\b(most popular|popular|best[- ]selling|trending|top-rated)\b", re.I)
    for text in texts:
        hit = banned.search(text)
        # The disclaimer is the one place that may name popularity — to deny it.
        if hit and text is not payload["disclaimer"]:
            failures.append(f"claims {hit.group(0)!r}: {text[:70]}")
    if "not popularity" not in payload["disclaimer"]:
        failures.append("disclaimer no longer says these are not popularity rankings")
    return failures


# --------------------------------------------------------------------------- #
# The literature, as directions
# --------------------------------------------------------------------------- #

def check_hao_children(verbose):
    """Hao & Guan (2025): warm + bright main wall; boys more saturated than girls;
    older children (teens) less saturated than children."""
    failures = []
    for cat in ("child_boy", "child_girl"):
        main = colours(cat)[0]
        l, c, h = main["lch"]
        if not WARM(h):
            failures.append(f"{cat}: main wall hue {h} is not warm")
        if l < 75:
            failures.append(f"{cat}: main wall L* {l} is not high brightness")
        if c > 25:
            failures.append(f"{cat}: main wall C* {c} is far above the measured ~20")
    if not mean_c("child_boy") > mean_c("child_girl"):
        failures.append(f"boys' palette C* {mean_c('child_boy'):.1f} not above girls' {mean_c('child_girl'):.1f}")
    children = (mean_c("child_boy") + mean_c("child_girl")) / 2
    if not mean_c("teen") < children:
        failures.append(f"teen C* {mean_c('teen'):.1f} not below children's {children:.1f}")
    if verbose:
        print(f"         mean C*: boy {mean_c('child_boy'):.1f}, girl {mean_c('child_girl'):.1f}, teen {mean_c('teen'):.1f}")
    return failures


def check_jiang_teens(verbose):
    """Jiang et al. (2020): light blue, light red, white; light yellow; no green."""
    failures = []
    sw = BY_CAT["teen"]["swatches"]
    if not any(s["kind"] == "colour" and 220 <= s["lch"][2] <= 270 and s["lch"][0] >= 70 for s in sw):
        failures.append("teen: no light blue")
    if not any(s["kind"] == "colour" and (s["lch"][2] >= 350 or s["lch"][2] <= 40) and s["lch"][0] >= 70 for s in sw):
        failures.append("teen: no light red / pink")
    if not any(s["kind"] == "neutral" and s["lch"][0] >= 90 for s in sw):
        failures.append("teen: no white")
    if not any(s["kind"] == "colour" and 80 <= s["lch"][2] <= 105 and s["lch"][0] >= 80 for s in sw):
        failures.append("teen: no light yellow")
    for s in sw:
        if s["kind"] == "colour" and GREEN(s["lch"][2]):
            failures.append(f"teen: {s['name']} is green, which the adolescents disliked")
    return failures


def check_elderly(verbose):
    """Li (2022): brighter, less saturated, mostly warm. Torres (2020): a cool
    bedroom option. Rapuano (2023): nature colours present."""
    failures = []
    if not mean_c("elderly") < mean_c("none"):
        failures.append(f"elderly C* {mean_c('elderly'):.1f} not below general {mean_c('none'):.1f}")
    if not mean_l("elderly") > mean_l("none"):
        failures.append(f"elderly L* {mean_l('elderly'):.1f} not above general {mean_l('none'):.1f}")
    warm = sum(WARM(s["lch"][2]) for s in colours("elderly"))
    if warm * 2 <= len(colours("elderly")):
        failures.append(f"elderly: only {warm}/{len(colours('elderly'))} warm colours")
    if not any(COOL(s["lch"][2]) for s in colours("elderly")):
        failures.append("elderly: no cool bedroom option (Torres et al.)")
    if not any(GREEN(s["lch"][2]) for s in colours("elderly")):
        failures.append("elderly: no nature green (Rapuano et al.)")
    return failures


def check_bogicevic_adults(verbose):
    """Men: the masculine set (blue, grey, dark brown). Women: both sets."""
    failures = []
    man = BY_CAT["adult_man"]["swatches"]
    if not any(s["kind"] == "colour" and COOL(s["lch"][2]) for s in man):
        failures.append("adult_man: no blue")
    if not any(s["kind"] == "neutral" and 40 <= s["lch"][0] <= 80 for s in man):
        failures.append("adult_man: no grey")
    if not any(s["kind"] == "colour" and s["lch"][0] < 50 and WARM(s["lch"][2]) for s in man):
        failures.append("adult_man: no dark brown")
    woman = colours("adult_woman")
    feminine = lambda h: h >= 330 or h <= 20 or 280 <= h < 330 or 180 <= h <= 210  # pink, purple, turquoise  # noqa: E731
    if not any(feminine(s["lch"][2]) for s in woman):
        failures.append("adult_woman: no colour from the feminine set")
    if not any(230 <= s["lch"][2] <= 280 for s in woman):
        failures.append("adult_woman: no colour from the masculine set (women were equally satisfied)")
    return failures


def check_voordt_white(verbose):
    """Van der Voordt (2017): white most preferred — adult and general palettes include it."""
    failures = []
    for cat in ("none", "adult_man", "adult_woman"):
        if not any(s["kind"] == "neutral" and s["lch"][0] >= 90 for s in BY_CAT[cat]["swatches"]):
            failures.append(f"{cat}: no white")
    return failures


def check_agrees_with_category_bias(verbose):
    """Templates and CATEGORY_BIAS cite the same papers, so they must lean the
    same way relative to the general palette wherever the bias is non-zero."""
    failures = []
    base_l, base_c = mean_l("none"), mean_c("none")
    for cat, bias in cr.CATEGORY_BIAS.items():
        if cat == "none":
            continue
        if bias["lightness_delta"] > 0 and not mean_l(cat) > base_l:
            failures.append(f"{cat}: bias lightens but template L* {mean_l(cat):.1f} <= general {base_l:.1f}")
        if bias["chroma_delta"] > 0 and not mean_c(cat) > base_c:
            failures.append(f"{cat}: bias saturates but template C* {mean_c(cat):.1f} <= general {base_c:.1f}")
        if bias["chroma_delta"] < 0 and not mean_c(cat) < base_c:
            failures.append(f"{cat}: bias desaturates but template C* {mean_c(cat):.1f} >= general {base_c:.1f}")
        if bias["hue_nudge_deg"] < 0 and not any(COOL(s["lch"][2]) for s in colours(cat)):
            failures.append(f"{cat}: bias cools but template has no cool colour")
    return failures


def check_api(verbose):
    import app

    r = app.app.test_client().get("/api/color-templates")
    data = r.get_json()
    failures = []
    if r.status_code != 200 or not data.get("success"):
        failures.append(f"/api/color-templates -> {r.status_code}")
    elif len(data["templates"]) != len(cr.CATEGORY_BIAS):
        failures.append(f"API returned {len(data['templates'])} templates")
    return failures


def check_page_wiring(verbose):
    """The app's Color Recommendation page has the templates view, keeps the scan
    flow, and shows the label from the API (not a hard-coded claim)."""
    page = open(os.path.join(UI_DIR, "color-recommendation.html"), encoding="utf-8").read()
    failures = []
    for needle in ('id="templates-section"', 'id="upload-section"', "/api/color-templates",
                   'id="mode-scan"', 'id="mode-templates"'):
        if needle not in page:
            failures.append(f"page is missing {needle}")
    if re.search(r"most popular", page, re.I):
        failures.append("page says 'most popular'")
    return failures


CHECKS = [
    ("one template per CATEGORY_BIAS category", check_one_template_per_category),
    ("five named swatches each, every one explained", check_five_named_swatches),
    ("colours inside the paint band, neutrals neutral", check_paint_band),
    ("hex shown matches the LCh described", check_hex_matches_lch),
    ("every swatch cites a verified source with a DOI", check_citations),
    ("photos: bundled, credited, openly licensed, from Commons", check_photos),
    ("labelled a research-supported tendency, not popularity", check_wording),
    ("Hao & Guan: warm/bright main wall; boys > girls; teens < children", check_hao_children),
    ("Jiang: teens' light blue, light red, white, yellow; no green", check_jiang_teens),
    ("Li / Torres / Rapuano: elderly palette", check_elderly),
    ("Bogicevic: masculine set for men, both sets for women", check_bogicevic_adults),
    ("Van der Voordt: white in general and adult palettes", check_voordt_white),
    ("templates lean the same way as CATEGORY_BIAS", check_agrees_with_category_bias),
    ("GET /api/color-templates", check_api),
    ("app page has the templates view beside the scan flow", check_page_wiring),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Tests for backend/color_templates.py")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    print(f"colour templates — {len(ct.TEMPLATES)} templates, {len(ct.PHOTOS)} photos, "
          f"{len(ct.REFERENCES)} sources\n")
    total = 0
    for name, check in CHECKS:
        try:
            failures = check(args.verbose)
        except Exception as exc:
            failures = [f"crashed: {type(exc).__name__}: {exc}"]
        total += len(failures)
        print(f"  [{'FAIL' if failures else ' ok '}] {name}")
        for failure in failures:
            print(f"         {failure}")
    print()
    if total:
        print(f"{total} failure(s).")
        return 1
    print(f"All {len(CHECKS)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
