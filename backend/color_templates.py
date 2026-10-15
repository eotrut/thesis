"""
AURA — demographic colour templates (desktop app, Color Recommendation page).

A template is a named palette of five colours for one of the seven "who is
this room for?" categories that ``color_recommender.CATEGORY_BIAS`` already
uses. Templates are the second way into colour recommendation: the camera-scan
flow derives a palette from the user's own room; a template shows what the
demographic colour-preference literature suggests for a group, before (or
instead of) scanning anything.

What a template is and is not
-----------------------------
Every palette is a RESEARCH-SUPPORTED TENDENCY, not a popularity ranking:
the cited studies measured what their participants preferred, not what sells
or what is "most popular". The UI labels them that way.

As with CATEGORY_BIAS, the honest split is:
* the DIRECTION of each colour (which hue family, lighter/darker, more or less
  saturated) follows a specific finding, cited per swatch in ``basis``;
* the EXACT SHADE (the L*/C*/h numbers) is AURA's choice, kept inside the same
  paint band the recommender uses so a template never proposes a colour the
  scan flow could not.

Colours are defined in CIE LCh(ab), the same space color_recommender works
in, and converted to hex with its converter, so a swatch here and a swatch from
a scan mean the same thing numerically.

Sources: the nine verified papers of Literature Review Master, Theme 7
(Huang et al., 2009 is left out — it could not be verified, see the vault's
2026-08-16 citation audit). Yıldırım et al. (2007) is a café study, so it
informs no palette here.

Example photos are openly licensed (CC0 / public domain / CC BY / CC BY-SA)
files from Wikimedia Commons, downloaded once through the Commons API, resized
to 1024 px and bundled in desktop/ui/assets/templates/. Licence and author were
read from each file's own Commons metadata on 2026-10-14. They illustrate a
colour family; they are not evidence and not AURA output.
"""

from __future__ import annotations

from color_recommender import (
    CATEGORY_BIAS,
    NEUTRAL_CHROMA,
    PAINT_CHROMA,
    PAINT_LIGHTNESS,
    _lch_to_hex,
)

LABEL = "Research-supported tendency"

DISCLAIMER = (
    "Based on published colour-preference studies. They describe tendencies in "
    "the groups that were studied, not rules, and not popularity or sales "
    "rankings. The colour directions come from the studies; the exact shades "
    "are AURA's choice. The study populations (for example in China, the "
    "Netherlands and Spain) may not match your household, so treat this as a "
    "starting point."
)

# --------------------------------------------------------------------------- #
# References — APA entries as verified in the vault (Writing Notes, 2026-08-16)
# --------------------------------------------------------------------------- #

REFERENCES: dict[str, dict[str, str]] = {
    "bogicevic2018": {
        "short": "Bogicevic et al. (2018)",
        "apa": "Bogicevic, V., Bujisic, M., Cobanoglu, C., & Feinstein, A. H. (2018). "
               "Gender and age preferences of hotel room design. International Journal of "
               "Contemporary Hospitality Management, 30(2), 874–899.",
        "doi": "10.1108/IJCHM-08-2016-0450",
        "finding": "762 participants: men preferred rooms in masculine colour schemes; "
                   "women were equally satisfied with masculine or feminine schemes.",
    },
    "hao2025": {
        "short": "Hao & Guan (2025)",
        "apa": "Hao, K., & Guan, H. (2025). A study of children's color preferences for "
               "consultation room furniture. HERD: Health Environments Research & Design "
               "Journal, 18(2), 208–220.",
        "doi": "10.1177/19375867251327969",
        "finding": "Children aged 3–15 preferred warm colours, high brightness and a "
                   "saturation of about 25/100 (75/100 second); boys preferred higher "
                   "saturation than girls; older children preferred lower saturation.",
    },
    "jiang2020": {
        "short": "Jiang et al. (2020)",
        "apa": "Jiang, L., Cheung, V., Westland, S., Rhodes, P. A., Shen, L., & Xu, L. "
               "(2020). The impact of color preference on adolescent children's choice of "
               "furniture. Color Research and Application, 45(4), 754–767.",
        "doi": "10.1002/col.22507",
        "finding": "508 Chinese adolescents (12–16): most preferred colours were light "
                   "blue, light red and white; for furniture, white, light yellow, light "
                   "blue and light red; green was disliked; boys preferred blue more "
                   "strongly, girls the red hue.",
    },
    "li2022": {
        "short": "Li et al. (2022)",
        "apa": "Li, M., Cai, Q., Li, C., Wu, X., Wang, T., Xu, J., & Wu, Z. (2022). A study "
               "in bedroom living environment preferences of the urban elderly in China. "
               "Sustainability, 14(20), 13552.",
        "doi": "10.3390/su142013552",
        "finding": "306 urban elderly respondents: bedroom colour key words were low "
                   "saturation, bright and warm tones.",
    },
    "rapuano2023": {
        "short": "Rapuano et al. (2023)",
        "apa": "Rapuano, M., Sarno, M., Ruotolo, F., Ruggiero, G., Iuliano, S., Masullo, M., "
               "Maffei, L., Cioffi, F., & Iachini, T. (2023). Emotional reactions to "
               "different indoor solutions: The role of age. Buildings, 13(7), 1737.",
        "doi": "10.3390/buildings13071737",
        "finding": "Across ages 19–86, the 'Nature' room (brown, orange and green with "
                   "wood) and the 'Vivacious' room were rated most positively; the white "
                   "and blue/cold rooms evoked more negative emotions. The elderly relied "
                   "more on colour and materials when judging a room.",
    },
    "torres2020": {
        "short": "Torres et al. (2020)",
        "apa": "Torres, A., Serra, J., Llopis, J., & Delcampo, A. (2020). Color preference "
               "cool versus warm in nursing homes depends on the expected activity for "
               "interior spaces. Frontiers of Architectural Research, 9(4), 739–750.",
        "doi": "10.1016/j.foar.2020.06.002",
        "finding": "Nursing-home residents preferred warm colours for activity rooms and "
                   "cool colours for bedrooms (both genders).",
    },
    "voordt2017": {
        "short": "Van der Voordt et al. (2017)",
        "apa": "Van der Voordt, T., Bakker, I., & de Boon, J. (2017). Color preferences for "
               "four different types of spaces. Facilities, 35(3/4), 155–169.",
        "doi": "10.1108/F-06-2015-0043",
        "finding": "1,077 Dutch respondents: white was the most preferred colour for every "
                   "space (28–44%); brown ranked second for living rooms, especially among "
                   "men; third choice for the bedroom was yellow (men) and red (women). The "
                   "authors suggest colours that resemble nature.",
    },
}

# Bogicevic's abstract names no colours. Which colours made up the "masculine"
# and "feminine" schemes is known only from the lead author's description in
# press coverage of the study (dark brown, blue, grey vs pink, purple, orange,
# yellow, turquoise). Said once, on the two templates that rely on it.
BOGICEVIC_COLOUR_CAVEAT = (
    "The colours in Bogicevic et al.'s masculine set (dark brown, blue, grey) and "
    "feminine set (pink, purple, orange, yellow, turquoise) are as described by the "
    "lead author in press coverage of the study; the paper's abstract does not list "
    "them."
)

# --------------------------------------------------------------------------- #
# Templates
#
# kind "colour"  -> must sit inside PAINT_LIGHTNESS / PAINT_CHROMA
# kind "neutral" -> near-grey/white, C* <= NEUTRAL_CHROMA (same exemption the
#                   recommender gives its neutral swatch)
# --------------------------------------------------------------------------- #

def _sw(name, role, kind, lch, basis, why):
    return {"name": name, "role": role, "kind": kind, "lch": lch, "basis": basis, "why": why}


TEMPLATES: list[dict] = [
    {
        "category": "none",
        "name": "Natural Calm",
        "audience": "General — no specific occupant",
        "summary": "White as the base, with nature-like browns, greens and a terracotta accent.",
        "swatches": [
            _sw("Warm White", "Main wall / ceiling", "neutral", (95, 3, 85), ["voordt2017"],
                "White was the most preferred colour for every room type."),
            _sw("Soft Sand", "Main wall", "colour", (82, 14, 75), ["voordt2017", "rapuano2023"],
                "Brown ranked second for living rooms; nature-like colours were rated positively."),
            _sw("Sage Green", "Feature wall", "colour", (72, 16, 135), ["rapuano2023"],
                "Green was part of the most positively rated 'Nature' room."),
            _sw("Terracotta", "Accent", "colour", (60, 30, 48), ["rapuano2023"],
                "Orange and brown were part of the 'Nature' room."),
            _sw("Walnut", "Trim / furniture", "colour", (42, 18, 60), ["rapuano2023", "voordt2017"],
                "Wood and brown tones; brown was a common living-room choice."),
        ],
        "photos": ["general-living-room", "general-wood-panelled-room"],
        "caveats": [
            "Rapuano et al. found all-white and cold blue rooms rated less positively, which is "
            "why white is paired with warm, nature-like colours rather than used alone.",
        ],
    },
    {
        "category": "child_boy",
        "name": "Sunny Play",
        "audience": "Child — boy",
        "summary": "Warm and bright, with a few stronger warm accents and one sky blue.",
        "swatches": [
            _sw("Apricot Cream", "Main wall", "colour", (80, 20, 65), ["hao2025"],
                "Warm hue at high brightness and low-moderate saturation — the most preferred combination."),
            _sw("Sunny Yellow", "Feature wall", "colour", (84, 42, 90), ["hao2025"],
                "Higher saturation was the second preference, and boys preferred more saturated colours than girls."),
            _sw("Tangerine", "Accent", "colour", (68, 48, 58), ["hao2025"],
                "A stronger warm accent, in line with boys' higher saturation preference."),
            _sw("Sky Blue", "Accent", "colour", (72, 26, 245), ["jiang2020"],
                "For older boys (12+), blue was preferred more strongly than by girls."),
            _sw("Warm White", "Trim / ceiling", "neutral", (94, 4, 80), ["hao2025"],
                "Preference increased with brightness."),
        ],
        "photos": ["child-boy-yellow-bedroom", "child-boy-warm-kids-room"],
        "caveats": [
            "AURA's scan-flow bias for this group sets wall saturation above Hao & Guan's "
            "measured level as a design choice; here the main wall stays near the measured "
            "level and the stronger colours are kept to accents.",
        ],
    },
    {
        "category": "child_girl",
        "name": "Peach Garden",
        "audience": "Child — girl",
        "summary": "Warm and bright like the boys' palette, but softer, with a light rose.",
        "swatches": [
            _sw("Peach Blush", "Main wall", "colour", (82, 18, 55), ["hao2025"],
                "Warm hue at high brightness and low saturation — the most preferred combination."),
            _sw("Butter", "Feature wall", "colour", (87, 28, 92), ["hao2025"],
                "Warm and bright; preference increased with brightness."),
            _sw("Soft Coral", "Accent", "colour", (72, 30, 38), ["hao2025"],
                "Warm accent kept less saturated than the boys' accents (girls preferred lower saturation)."),
            _sw("Rose Pink", "Accent", "colour", (78, 22, 10), ["jiang2020"],
                "For older girls (12+), the red hue was preferred; light red ranked second overall."),
            _sw("Warm White", "Trim / ceiling", "neutral", (94, 4, 80), ["hao2025"],
                "Preference increased with brightness."),
        ],
        "photos": ["child-girl-cream-nursery", "child-girl-soft-nursery"],
        "caveats": [],
    },
    {
        "category": "teen",
        "name": "Fresh Light",
        "audience": "Teen (about 12–16)",
        "summary": "The teens' own top three — light blue, light red, white — plus light yellow. No green.",
        "swatches": [
            _sw("Clean White", "Main wall", "neutral", (95, 2, 90), ["jiang2020"],
                "White was the third most preferred colour and the top furniture choice."),
            _sw("Light Blue", "Feature wall", "colour", (80, 20, 245), ["jiang2020"],
                "Light blue was the most preferred colour."),
            _sw("Blush", "Feature wall", "colour", (78, 22, 20), ["jiang2020"],
                "Light red was the second most preferred colour."),
            _sw("Light Yellow", "Accent", "colour", (87, 34, 95), ["jiang2020"],
                "Light yellow was among the favourite furniture colours."),
            _sw("Denim Blue", "Accent", "colour", (55, 28, 258), ["jiang2020", "hao2025"],
                "Boys preferred blue more strongly; saturation stays moderate because older children preferred lower saturation."),
        ],
        "photos": ["teen-light-blue-room", "teen-white-loft-bedroom"],
        "caveats": ["Green is left out on purpose: the adolescents in Jiang et al. disliked it."],
    },
    {
        "category": "adult_man",
        "name": "Slate & Walnut",
        "audience": "Adult — man",
        "summary": "White base with the 'masculine' blue, grey and dark brown, and a mustard accent.",
        "swatches": [
            _sw("Soft White", "Main wall / ceiling", "neutral", (93, 3, 85), ["voordt2017"],
                "Men chose white most often for every room type (32–44%)."),
            _sw("Slate Blue", "Feature wall", "colour", (52, 24, 262), ["bogicevic2018"],
                "Men preferred masculine schemes; blue is part of that set."),
            _sw("Warm Grey", "Main wall", "neutral", (66, 4, 75), ["bogicevic2018"],
                "Grey is part of the masculine set."),
            _sw("Walnut Brown", "Trim / furniture", "colour", (42, 20, 58), ["bogicevic2018", "voordt2017"],
                "Dark brown is part of the masculine set; brown was men's second living-room choice."),
            _sw("Mustard", "Accent", "colour", (78, 40, 85), ["voordt2017"],
                "Yellow was men's third choice for the bedroom."),
        ],
        "photos": ["adult-man-blue-living-room", "adult-man-leather-and-mustard"],
        "caveats": [BOGICEVIC_COLOUR_CAVEAT],
    },
    {
        "category": "adult_woman",
        "name": "Rose & Sea Glass",
        "audience": "Adult — woman",
        "summary": "A mix of both schemes — rose, lavender and turquoise with a slate blue — on a white base.",
        "swatches": [
            _sw("Soft White", "Main wall / ceiling", "neutral", (93, 3, 85), ["voordt2017"],
                "Women also chose white most often for every room type (28–38%)."),
            _sw("Dusty Rose", "Feature wall", "colour", (70, 22, 12), ["bogicevic2018", "voordt2017"],
                "Pink is part of the feminine set; red was women's third bedroom choice."),
            _sw("Soft Lavender", "Feature wall", "colour", (72, 18, 305), ["bogicevic2018"],
                "Purple is part of the feminine set."),
            _sw("Sea Glass", "Accent", "colour", (76, 20, 195), ["bogicevic2018"],
                "Turquoise is part of the feminine set."),
            _sw("Slate Blue", "Accent", "colour", (55, 22, 262), ["bogicevic2018"],
                "Women were equally satisfied with masculine schemes, so one masculine colour is included."),
        ],
        "photos": ["adult-woman-violet-bedroom", "adult-woman-white-and-pink"],
        "caveats": [
            "Bogicevic et al. found no preference between the two schemes for women, so this "
            "palette deliberately mixes them rather than leaning one way — the same reason "
            "AURA's scan flow applies no bias for this group.",
            BOGICEVIC_COLOUR_CAVEAT,
        ],
    },
    {
        "category": "elderly",
        "name": "Warm Linen",
        "audience": "Elderly",
        "summary": "Bright, warm and low in saturation, with nature colours and one soft cool for bedrooms.",
        "swatches": [
            _sw("Warm Linen", "Main wall", "colour", (88, 12, 78), ["li2022"],
                "Low saturation, bright, warm tones were the key words for elderly bedrooms."),
            _sw("Soft Apricot", "Living / activity room", "colour", (80, 18, 62), ["li2022", "torres2020"],
                "Warm and bright; warm colours were preferred for activity rooms."),
            _sw("Sage", "Feature wall", "colour", (74, 14, 130), ["rapuano2023"],
                "Green was part of the most positively rated 'Nature' room."),
            _sw("Clay", "Accent / trim", "colour", (66, 20, 52), ["rapuano2023"],
                "Brown and orange with wood were part of the 'Nature' room."),
            _sw("Mist Blue", "Bedroom option", "colour", (80, 12, 235), ["torres2020"],
                "Nursing-home residents preferred cool colours for bedrooms."),
        ],
        "photos": ["elderly-warm-light-room", "elderly-calm-bedroom"],
        "caveats": [
            "The studies disagree for bedrooms: Li et al. found warm tones preferred, Torres "
            "et al. found cool. Both are offered — Mist Blue is the bedroom alternative.",
        ],
    },
]

# --------------------------------------------------------------------------- #
# Example photos — Wikimedia Commons, metadata read 2026-10-14
# --------------------------------------------------------------------------- #

PHOTO_DIR = "assets/templates"

PHOTOS: dict[str, dict[str, str]] = {
    "general-living-room": {
        "caption": "White walls with warm wood and plants.",
        "author": "Jarosław Ceborski", "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Living_room_(Unsplash).jpg",
        "origin": "Unsplash, via Wikimedia Commons",
    },
    "general-wood-panelled-room": {
        "caption": "Wood panelling, a plant and a yellow accent.",
        "author": "Breather", "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source": "https://commons.wikimedia.org/wiki/File:15A_Hanover_St_interior_(Unsplash).jpg",
        "origin": "Unsplash, via Wikimedia Commons",
    },
    "child-boy-yellow-bedroom": {
        "caption": "Warm yellow walls with a blue floor (historic children's bedroom, Sinaia, Romania).",
        "author": "Dennis G. Jarvis", "license": "CC BY-SA 2.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/2.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Romania-1687_-_Children%27s_Bedroom_(7646877616).jpg",
        "origin": "Flickr, via Wikimedia Commons",
    },
    "child-boy-warm-kids-room": {
        "caption": "Warm walls with strong, saturated accents (store display).",
        "author": "Olybrius", "license": "Public domain",
        "license_url": "",
        "source": "https://commons.wikimedia.org/wiki/File:Lisses_-_magasin_IKEA_1.jpg",
        "origin": "Wikimedia Commons (released into the public domain by the author)",
    },
    "child-girl-cream-nursery": {
        "caption": "Warm cream walls with colourful decorations.",
        "author": "Andwhatsnext (photo © 2006 Nancy J Price)", "license": "CC BY-SA 3.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Nursery-home-staging-700.jpg",
        "origin": "English Wikipedia, via Wikimedia Commons",
    },
    "child-girl-soft-nursery": {
        "caption": "Soft, light walls with natural wood.",
        "author": "ajay_suresh", "license": "CC BY 2.0",
        "license_url": "https://creativecommons.org/licenses/by/2.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Baby_Nursery_(51260797083).jpg",
        "origin": "Flickr, via Wikimedia Commons",
    },
    "teen-light-blue-room": {
        "caption": "A light blue wall with white (gallery kids' room).",
        "author": "Evan Delshaw", "license": "CC BY 2.0",
        "license_url": "https://creativecommons.org/licenses/by/2.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Kids_Room_(20679286272).jpg",
        "origin": "Flickr, via Wikimedia Commons",
    },
    "teen-white-loft-bedroom": {
        "caption": "A white bedroom with a study corner.",
        "author": "Gabriel Beaudry", "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source": "https://commons.wikimedia.org/wiki/File:NY_loft_bedroom_(Unsplash).jpg",
        "origin": "Unsplash, via Wikimedia Commons",
    },
    "adult-man-blue-living-room": {
        "caption": "A blue wall, a brown sofa and a mustard chair.",
        "author": "katherine raz", "license": "CC BY 2.0",
        "license_url": "https://creativecommons.org/licenses/by/2.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Ikea_Karlstad_Swivel_Chair_(3465043271).jpg",
        "origin": "Flickr, via Wikimedia Commons",
    },
    "adult-man-leather-and-mustard": {
        "caption": "Grey and white walls, brown leather and mustard (co-working lounge).",
        "author": "Dan Gold", "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Casual_Meeting_Room_(Unsplash).jpg",
        "origin": "Unsplash, via Wikimedia Commons",
    },
    "adult-woman-violet-bedroom": {
        "caption": "Violet walls with white bedding (hotel room).",
        "author": "Markus Spiske", "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Hotel_bedroom_windows_(Unsplash).jpg",
        "origin": "Unsplash, via Wikimedia Commons",
    },
    "adult-woman-white-and-pink": {
        "caption": "White walls with pink accents.",
        "author": "Breather", "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Minimal_creative_interior_(Unsplash).jpg",
        "origin": "Unsplash, via Wikimedia Commons",
    },
    "elderly-warm-light-room": {
        "caption": "Bright, warm light with leather and wood.",
        "author": "Breather", "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Breather_Montreal_interior_(Unsplash).jpg",
        "origin": "Unsplash, via Wikimedia Commons",
    },
    "elderly-calm-bedroom": {
        "caption": "A calm, light bedroom with soft blue accents.",
        "author": "Ali Inay", "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source": "https://commons.wikimedia.org/wiki/File:Ali_Inay_2015-02-25_(Unsplash).jpg",
        "origin": "Unsplash, via Wikimedia Commons",
    },
}

# Licences a bundled photo may carry. No NC/ND: Commons does not accept them,
# and AURA is handed out freely.
ALLOWED_PHOTO_LICENSES = ("CC0 1.0", "Public domain", "CC BY 2.0", "CC BY-SA 2.0", "CC BY-SA 3.0")


def photo_credit(photo: dict) -> str:
    """One-line credit as shown under a photo and on the licenses screen."""
    licence = photo["license"]
    return f"Photo: {photo['author']} — {licence} — {photo['origin']} (resized)"


def _swatch_payload(swatch: dict) -> dict:
    lightness, chroma, hue = swatch["lch"]
    return {
        "name": swatch["name"],
        "role": swatch["role"],
        "kind": swatch["kind"],
        "hex": _lch_to_hex(lightness, chroma, hue),
        "lch": {"l": lightness, "c": chroma, "h": hue},
        "why": swatch["why"],
        "sources": [REFERENCES[key]["short"] for key in swatch["basis"]],
    }


def templates_payload() -> dict:
    """Everything the templates screen needs, JSON-ready."""
    templates = []
    for template in TEMPLATES:
        keys = sorted({k for s in template["swatches"] for k in s["basis"]})
        templates.append({
            "category": template["category"],
            "name": template["name"],
            "audience": template["audience"],
            "summary": template["summary"],
            "label": LABEL,
            "swatches": [_swatch_payload(s) for s in template["swatches"]],
            "photos": [
                {
                    "src": f"{PHOTO_DIR}/{slug}.jpg",
                    "caption": PHOTOS[slug]["caption"],
                    "credit": photo_credit(PHOTOS[slug]),
                    "license": PHOTOS[slug]["license"],
                    "license_url": PHOTOS[slug]["license_url"],
                    "source": PHOTOS[slug]["source"],
                }
                for slug in template["photos"]
            ],
            "sources": [
                {"key": k, "short": REFERENCES[k]["short"], "apa": REFERENCES[k]["apa"],
                 "doi": REFERENCES[k]["doi"], "finding": REFERENCES[k]["finding"]}
                for k in keys
            ],
            "caveats": template["caveats"],
        })
    return {
        "label": LABEL,
        "disclaimer": DISCLAIMER,
        "categories": list(CATEGORY_BIAS),
        "paint_band": {"lightness": list(PAINT_LIGHTNESS), "chroma": list(PAINT_CHROMA),
                       "neutral_chroma_max": NEUTRAL_CHROMA},
        "templates": templates,
    }
