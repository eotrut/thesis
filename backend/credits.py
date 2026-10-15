"""Credits and licences for everything the AURA desktop app bundles.

One source of truth for two outputs:

* the in-app **Licenses** screen (``GET /api/credits`` -> desktop/ui/licenses.html)
* ``LICENSES.txt`` in the built package (desktop/write_licenses.py, run by
  desktop/build.py), which adds the full list of shipped Python packages and
  copies each one's own licence files into ``licenses/``.

Every licence below was read from the component's own package metadata (the
build venv's ``.dist-info``) or from its repository's LICENSE file via the
GitHub API, not from memory. ``dist`` names the installed distribution, and
test_credits.py re-checks the declared licence against it, so a dependency
that changes licence fails the tests instead of going stale here.

Template photo credits are not repeated here: they come from
color_templates.PHOTOS, the same data shown under each photo.
"""

from __future__ import annotations

from color_templates import PHOTO_DIR, PHOTOS

SOURCE_URL = "https://github.com/eotrut/thesis"

AURA_COPYRIGHT = "Copyright (C) 2026 Kurt Robyn A. Manabat, Reymon G. David Jr. and Lester Usi"

AGPL_URL = "https://www.gnu.org/licenses/agpl-3.0.html"

# Main components, in the order the screen shows them. `match` is the text the
# installed package's own licence metadata must contain (checked by the tests).
COMPONENTS: list[dict] = [
    {
        "name": "Ultralytics YOLOv8",
        "role": "Wall segmentation model framework (training and inference); also runs MobileSAM.",
        "license": "AGPL-3.0", "license_url": AGPL_URL,
        "copyright": "Ultralytics (authors Glenn Jocher, Jing Qiu)",
        "url": "https://github.com/ultralytics/ultralytics",
        "dist": "ultralytics", "match": "AGPL",
        "note": "Copyleft licence: see \"Ultralytics and the AGPL-3.0\" below.",
    },
    {
        "name": "AURA segmentation model (best.pt)",
        "role": "YOLOv8n-seg fine-tuned by the AURA team on its own wall dataset.",
        "license": "AGPL-3.0", "license_url": AGPL_URL,
        "copyright": "Starting weights: Ultralytics; fine-tuning: the AURA team",
        "url": "https://github.com/ultralytics/assets/releases",
        "note": "Trained from Ultralytics' pretrained YOLOv8n-seg weights. Ultralytics offers its software and AI models under AGPL-3.0 (or its paid Enterprise License).",
    },
    {
        "name": "MobileSAM (mobile_sam.pt)",
        "role": "Smart select in the mask editor: click a point, get a region.",
        "license": "Apache-2.0", "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "copyright": "Chaoning Zhang et al. (the MobileSAM authors)",
        "url": "https://github.com/ChaoningZhang/MobileSAM",
        "note": "Licence from the MobileSAM repository's LICENSE file. The weights file is the one Ultralytics redistributes in its assets release.",
    },
    {
        "name": "PyTorch",
        "role": "Runs the neural networks (CPU, or NVIDIA CUDA in the GPU build).",
        "license": "BSD-3-Clause", "license_url": "https://github.com/pytorch/pytorch/blob/main/LICENSE",
        "copyright": "Facebook, Inc. (Meta) and the PyTorch contributors",
        "url": "https://github.com/pytorch/pytorch",
        "dist": "torch", "match": "BSD",
        "note": "The GPU build also contains NVIDIA CUDA and cuDNN libraries inside PyTorch, redistributed under NVIDIA's own licence terms.",
    },
    {
        "name": "torchvision",
        "role": "Image operations used by Ultralytics.",
        "license": "BSD-3-Clause", "license_url": "https://github.com/pytorch/vision/blob/main/LICENSE",
        "copyright": "Soumith Chintala and the torchvision contributors",
        "url": "https://github.com/pytorch/vision",
        "dist": "torchvision", "match": "BSD",
    },
    {
        "name": "OpenCV (opencv-python)",
        "role": "Camera capture, image processing, mask drawing.",
        "license": "Apache-2.0", "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "copyright": "OpenCV team and contributors",
        "url": "https://github.com/opencv/opencv-python",
        "dist": "opencv-python", "match": "Apache",
        "note": "Includes FFmpeg as a separate DLL (opencv_videoio_ffmpeg), licensed LGPL-2.1; its licence text ships in licenses/ (OpenCV's LICENSE-3RD-PARTY.txt). FFmpeg source: https://ffmpeg.org.",
    },
    {
        "name": "Flask",
        "role": "The app's built-in local web server (with Werkzeug and Jinja2).",
        "license": "BSD-3-Clause", "license_url": "https://github.com/pallets/flask/blob/main/LICENSE.txt",
        "copyright": "Pallets",
        "url": "https://github.com/pallets/flask",
        "dist": "flask", "match": "BSD",
    },
    {
        "name": "colour-science",
        "role": "Colour maths for recommendations (CIE Lab / LCh, colour differences).",
        "license": "BSD-3-Clause", "license_url": "https://github.com/colour-science/colour/blob/develop/LICENSE",
        "copyright": "Colour Developers",
        "url": "https://github.com/colour-science/colour",
        "dist": "colour-science", "match": "BSD",
    },
    {
        "name": "NumPy",
        "role": "Array maths everywhere in the backend.",
        "license": "BSD-3-Clause (with bundled MIT, Zlib, 0BSD and CC0 parts)",
        "license_url": "https://github.com/numpy/numpy/blob/main/LICENSE.txt",
        "copyright": "NumPy Developers",
        "url": "https://github.com/numpy/numpy",
        "dist": "numpy", "match": "BSD-3-Clause",
    },
    {
        "name": "pywebview",
        "role": "The desktop window that shows the app (uses Windows' Edge WebView2).",
        "license": "BSD-3-Clause", "license_url": "https://github.com/r0x0r/pywebview/blob/master/LICENSE",
        "copyright": "Roman Sirokov and contributors",
        "url": "https://github.com/r0x0r/pywebview",
        "dist": "pywebview", "match": "BSD",
        "note": "On Windows it uses pythonnet (MIT). WebView2 itself is part of Windows and is not bundled.",
    },
    {
        "name": "PyInstaller",
        "role": "Packs AURA into AURA.exe; its small start-up program (the bootloader) is inside AURA.exe.",
        "license": "GPL-2.0-or-later with the Bootloader Exception",
        "license_url": "https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt",
        "copyright": "PyInstaller Development Team",
        "url": "https://github.com/pyinstaller/pyinstaller",
        "dist": "pyinstaller", "match": "exception",
        "note": "The Bootloader Exception allows apps built with PyInstaller to be distributed under any licence.",
    },
    {
        "name": "Python 3.11",
        "role": "The Python runtime bundled inside the app (python311.dll and standard library).",
        "license": "PSF-2.0", "license_url": "https://docs.python.org/3/license.html",
        "copyright": "Python Software Foundation",
        "url": "https://www.python.org",
        "note": "The package also includes Microsoft Visual C++ runtime DLLs (vcruntime140, msvcp140) that ship with Python, redistributed under Microsoft's terms.",
    },
]

FONTS: list[dict] = [
    {
        "name": "Fraunces", "use": "Headings",
        "author": "The Fraunces Project Authors (Undercase Type: Phaedra Charles, Flavia Zimbardi)",
        "license": "SIL Open Font License 1.1", "license_url": "https://openfontlicense.org",
        "url": "https://github.com/undercasetype/Fraunces",
        "license_file": "OFL-Fraunces.txt",
    },
    {
        "name": "DM Sans", "use": "Body text",
        "author": "The DM Sans Project Authors (Colophon Foundry, commissioned by Google)",
        "license": "SIL Open Font License 1.1", "license_url": "https://openfontlicense.org",
        "url": "https://github.com/googlefonts/dm-fonts",
        "license_file": "OFL-DMSans.txt",
    },
]
FONTS_PACKAGING = ("Font files: Latin and Latin Extended subsets from the Fontsource 5.3.0 "
                   "variable packages (@fontsource-variable/fraunces, @fontsource-variable/dm-sans), "
                   "bundled in the app so it works offline.")

DATASET = {
    "name": "AURA wall dataset",
    "where": "Roboflow project aura-thesis/wall-instance, version 4",
    "what": ("Wall photos annotated by the AURA team with instance-segmentation polygons "
             "for two classes, \"wall\" and \"non-paintable\"; used to fine-tune best.pt."),
    "images": ("About 40% of the images were photographed by the AURA team with its own camera. "
               "About 60% were collected online, mostly from Unsplash (Unsplash License: free to use "
               "and modify, attribution not required). Thanks to the Unsplash photographers."),
    "shipped": "The dataset itself is not included in the app; only the trained model weights are.",
}

AGPL_SUMMARY = [
    "AURA includes Ultralytics YOLOv8, which is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). "
    "When a program that includes AGPL-3.0 code is distributed, the AGPL-3.0 applies to the program as a whole, "
    "so AURA's own software is released under the AGPL-3.0 too (" + AURA_COPYRIGHT + ").",
    "Anyone who receives AURA must be able to get its complete source code, including the build scripts, "
    "for the exact version they received, at no extra charge.",
    "Recipients get the same rights the AGPL-3.0 gives: to use, study, change and share AURA under the same licence.",
    "Copyright and licence notices must be kept, and the AGPL-3.0 text must be included "
    "(it ships as LICENSE.txt next to AURA.exe).",
    "Ultralytics also sells an Enterprise License for closed-source use; AURA does not use it.",
]

SOURCE_NOTE = [
    f"AURA's complete source code is public at {SOURCE_URL}, under the AGPL-3.0 "
    "(the LICENSE file in the repository).",
    "BUILD-INFO.txt next to AURA.exe records the exact git commit the build came from "
    "and the exact version of every package in it.",
    "To rebuild the app from source, follow desktop/README.md in the repository "
    "(\"Build the Windows app\").",
    "Each bundled package's own licence texts are in the licenses folder next to AURA.exe; "
    "LICENSES.txt lists every package with its version and licence.",
]


def photo_credits() -> list[dict]:
    """The 14 template photos, from the same data shown under each photo."""
    return [
        {"file": f"{PHOTO_DIR}/{key}.jpg", "caption": p["caption"], "author": p["author"],
         "license": p["license"], "license_url": p["license_url"],
         "source": p["source"], "origin": p["origin"]}
        for key, p in PHOTOS.items()
    ]


def credits_payload() -> dict:
    return {
        "source_url": SOURCE_URL,
        "components": COMPONENTS,
        "fonts": FONTS,
        "fonts_packaging": FONTS_PACKAGING,
        "dataset": DATASET,
        "photos": photo_credits(),
        "photos_note": ("Resized to 1024 px for the app; otherwise unchanged. "
                        "CC BY-SA photos remain under their CC BY-SA licence."),
        "agpl": AGPL_SUMMARY,
        "source_note": SOURCE_NOTE,
    }


def _wrap(text: str, indent: str = "  ", width: int = 78) -> str:
    import textwrap
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def render_text(packages: list[dict] | None = None) -> str:
    """LICENSES.txt for the built package. `packages` comes from the build scan."""
    rule = "=" * 78
    out = [rule, "AURA desktop app: licences and credits", rule, "",
           "AURA is a thesis project (BS Computer Engineering, Holy Angel University).",
           AURA_COPYRIGHT + ".",
           "AURA is free software under the GNU Affero General Public License v3.0;",
           "the full text is in LICENSE.txt next to AURA.exe.",
           f"Source code: {SOURCE_URL}", ""]

    out += ["ULTRALYTICS AND THE AGPL-3.0", "-" * 28]
    out += [_wrap("- " + line, "", 78).replace("\n", "\n  ") for line in AGPL_SUMMARY] + [""]

    out += ["HOW TO SEE THE SOURCE", "-" * 21]
    out += [_wrap("- " + line, "", 78).replace("\n", "\n  ") for line in SOURCE_NOTE] + [""]

    out += ["MAIN COMPONENTS", "-" * 15]
    for c in COMPONENTS:
        out += [f"{c['name']}  [{c['license']}]",
                _wrap(c["role"]),
                f"  Copyright: {c['copyright']}",
                f"  Project: {c['url']}",
                f"  Licence: {c['license_url']}"]
        if c.get("note"):
            out.append(_wrap(c["note"]))
        out.append("")

    out += ["FONTS", "-" * 5]
    for f in FONTS:
        out += [f"{f['name']} ({f['use'].lower()})  [{f['license']}]",
                f"  {f['author']}", f"  {f['url']}",
                f"  Licence text: licenses/fonts/{f['license_file']}", ""]
    out += [_wrap(FONTS_PACKAGING, ""), ""]

    out += ["TRAINING DATA", "-" * 13,
            f"{DATASET['name']}: {DATASET['where']}", _wrap(DATASET["what"]), _wrap(DATASET["images"]),
            _wrap(DATASET["shipped"]), ""]

    out += ["TEMPLATE PHOTOS (Color Recommendation > Browse Templates)", "-" * 57]
    for p in photo_credits():
        licence = f"{p['license']} ({p['license_url']})" if p["license_url"] else p["license"]
        out += [f"{p['file']}", f"  {p['author']}, {licence}",
                f"  {p['origin']}: {p['source']}"]
    out += ["", _wrap(credits_payload()["photos_note"], ""), ""]

    if packages:
        out += ["ALL BUNDLED PYTHON PACKAGES", "-" * 27,
                _wrap("Every package PyInstaller packed into this build, with the licence its own "
                      "metadata declares. Licence texts: licenses/<name>-<version>/.", ""), ""]
        width = max(len(p["name"]) for p in packages) + 2
        for p in packages:
            out.append(f"{p['name']:<{width}}{p['version']:<16}{p['license']}")
        out.append("")
    return "\n".join(out)
