"""
AURA — Licences and credits tests (desktop app Licenses screen + LICENSES.txt).

Standalone script, same shape as the other test_*.py: run it, read the
summary, exit code says whether anything broke.

What can break: (a) a bundled component missing from the credits, (b) a
dependency changing licence while credits.py still states the old one, (c) a
font or template photo added to the app without a credit, (d) the screen or
the build no longer producing the notices.

For (b), each component's stated licence is re-checked against the installed
package's own metadata: in this Python if the package is installed here,
otherwise in the desktop build venvs (desktop/build/venv-*), which hold
exactly what the app bundles.

Run:
    python backend/tools/test_credits.py
    python backend/tools/test_credits.py -v
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile
from email.parser import Parser
from importlib import metadata

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DESKTOP_DIR = os.path.join(PROJECT_ROOT, "desktop")
UI_DIR = os.path.join(DESKTOP_DIR, "ui")
sys.path.insert(0, BACKEND_DIR)

import credits  # noqa: E402
import color_templates as ct  # noqa: E402

# Everything the panel / kickoff prompt asked to be credited, as the text that
# must appear in a credited name.
REQUIRED = ["Ultralytics", "MobileSAM", "PyTorch", "OpenCV", "Flask", "colour-science",
            "pywebview", "PyInstaller", "Python"]


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def licence_metadata(dist_name: str) -> tuple[str, str] | None:
    """(where, licence text from metadata) for an installed distribution."""
    try:
        m = metadata.metadata(dist_name)
        where = "this Python"
    except metadata.PackageNotFoundError:
        m = None
        for meta in sorted(glob.glob(os.path.join(DESKTOP_DIR, "build", "venv-*", "Lib",
                                                  "site-packages", "*.dist-info", "METADATA"))):
            folder = os.path.basename(os.path.dirname(meta))
            if _norm(folder.split("-")[0]) == _norm(dist_name):
                with open(meta, encoding="utf-8") as fh:
                    m = Parser().parse(fh, headersonly=True)
                where = os.path.relpath(meta, PROJECT_ROOT).split(os.sep)[2]
                break
        if m is None:
            return None
    fields = [m.get("License-Expression") or "", m.get("License") or ""]
    fields += [c for c in (m.get_all("Classifier") or []) if c.startswith("License ::")]
    return where, " | ".join(fields)


def check_required_present(verbose):
    names = " ".join(c["name"] for c in credits.COMPONENTS)
    failures = [f"no credit for {r}" for r in REQUIRED if r.lower() not in names.lower()]
    if not credits.FONTS:
        failures.append("no fonts credited")
    if not credits.DATASET.get("where"):
        failures.append("training dataset not credited")
    return failures


def check_component_fields(verbose):
    failures = []
    for c in credits.COMPONENTS:
        for key in ("name", "role", "license", "license_url", "copyright", "url"):
            if not c.get(key):
                failures.append(f"{c.get('name')}: missing {key}")
        for key in ("license_url", "url"):
            if c.get(key) and not c[key].startswith("https://"):
                failures.append(f"{c['name']}: {key} is not an https link")
    return failures


def check_licences_match_metadata(verbose):
    failures, checked = [], []
    for c in credits.COMPONENTS:
        if not c.get("dist"):
            continue
        found = licence_metadata(c["dist"])
        if found is None:
            if verbose:
                print(f"         {c['dist']}: not installed here or in a build venv, skipped")
            continue
        where, text = found
        checked.append(c["dist"])
        if c["match"].lower() not in text.lower():
            failures.append(f"{c['name']}: metadata ({where}) says {text!r}, credits say {c['license']}")
        elif verbose:
            print(f"         {c['dist']:15} {c['license']:40} ({where})")
    if "ultralytics" not in checked:
        failures.append("could not check Ultralytics' licence against its metadata")
    return failures


def check_agpl_and_source(verbose):
    failures = []
    ultra = next(c for c in credits.COMPONENTS if c.get("dist") == "ultralytics")
    if ultra["license"] != "AGPL-3.0":
        failures.append(f"Ultralytics credited as {ultra['license']}")
    if not any(credits.SOURCE_URL in line for line in credits.SOURCE_NOTE):
        failures.append("source note does not give the source URL")
    try:
        remote = subprocess.run(["git", "-C", PROJECT_ROOT, "remote", "get-url", "origin"],
                                capture_output=True, text=True, check=True).stdout.strip()
        if remote.removesuffix(".git").rstrip("/") != credits.SOURCE_URL:
            failures.append(f"SOURCE_URL {credits.SOURCE_URL} != git origin {remote}")
    except (OSError, subprocess.CalledProcessError):
        if verbose:
            print("         git not available, origin not compared")
    text = " ".join(credits.AGPL_SUMMARY)
    for needed in ("source code", "AGPL-3.0 text"):
        if needed not in text:
            failures.append(f"AGPL summary does not mention {needed!r}")
    return failures


def check_fonts(verbose):
    failures = []
    font_dir = os.path.join(UI_DIR, "assets", "fonts")
    prefixes = []
    for f in credits.FONTS:
        path = os.path.join(font_dir, f["license_file"])
        if not os.path.isfile(path):
            failures.append(f"{f['name']}: {f['license_file']} missing")
            continue
        text = open(path, encoding="utf-8").read()
        if "SIL OPEN FONT LICENSE Version 1.1" not in text or "OFL" not in f["license"].replace("Open Font License", "OFL"):
            failures.append(f"{f['name']}: licence file is not the SIL OFL 1.1")
        prefixes.append(_norm(f["name"]).replace(" ", "-"))
    for woff in glob.glob(os.path.join(font_dir, "*.woff2")):
        base = os.path.basename(woff)
        if not any(base.startswith(p) for p in prefixes):
            failures.append(f"{base} is bundled but its font is not credited")
    return failures


def check_photos(verbose):
    failures = []
    credited = {p["file"] for p in credits.photo_credits()}
    bundled = {f"{ct.PHOTO_DIR}/{os.path.basename(f)}"
               for f in glob.glob(os.path.join(UI_DIR, "assets", "templates", "*.jpg"))}
    for f in sorted(bundled - credited):
        failures.append(f"{f} is bundled but not credited")
    for f in sorted(credited - bundled):
        failures.append(f"{f} is credited but not bundled")
    for p in credits.photo_credits():
        # public domain has no licence document, so no licence link
        needs_link = p["license"] != "Public domain"
        if not (p["author"] and p["license"] and p["source"]) or (needs_link and not p["license_url"]):
            failures.append(f"{p['file']}: incomplete credit")
    if len(credited) != 14:
        failures.append(f"expected the 14 template photos, found {len(credited)}")
    return failures


def check_api(verbose):
    import app

    r = app.app.test_client().get("/api/credits")
    data = r.get_json()
    if r.status_code != 200 or not data.get("success"):
        return [f"/api/credits -> {r.status_code}"]
    failures = []
    for key, expected in (("components", len(credits.COMPONENTS)), ("fonts", len(credits.FONTS)),
                          ("photos", len(ct.PHOTOS))):
        if len(data.get(key, [])) != expected:
            failures.append(f"/api/credits {key}: {len(data.get(key, []))} != {expected}")
    return failures


def check_page_wiring(verbose):
    failures = []
    page = os.path.join(UI_DIR, "licenses.html")
    if not os.path.isfile(page):
        return ["desktop/ui/licenses.html missing"]
    html = open(page, encoding="utf-8").read()
    if "/api/credits" not in html:
        failures.append("licenses.html does not load /api/credits")
    if re.search(r'<(link|script)[^>]+(href|src)="https?://', html):
        failures.append("licenses.html loads something from the internet")
    nav = open(os.path.join(UI_DIR, "nav.js"), encoding="utf-8").read()
    if 'href: "licenses.html"' not in nav:
        failures.append("nav.js has no Licenses link")
    return failures


def check_render_text(verbose):
    fake = [{"name": "examplepkg", "version": "1.0", "license": "MIT", "url": "", "files": []}]
    text = credits.render_text(fake)
    failures = []
    for c in credits.COMPONENTS:
        if c["name"] not in text:
            failures.append(f"LICENSES.txt misses {c['name']}")
    for f in credits.FONTS:
        if f["name"] not in text:
            failures.append(f"LICENSES.txt misses font {f['name']}")
    for p in credits.photo_credits():
        if p["file"] not in text:
            failures.append(f"LICENSES.txt misses {p['file']}")
    for needed in (credits.SOURCE_URL, "ULTRALYTICS AND THE AGPL-3.0", "HOW TO SEE THE SOURCE",
                   credits.DATASET["where"], "examplepkg"):
        if needed not in text:
            failures.append(f"LICENSES.txt misses {needed!r}")
    return failures


def check_build_writer(verbose):
    """Runs desktop/write_licenses.py against the last CPU build, if there is one."""
    venv_py = os.path.join(DESKTOP_DIR, "build", "venv-cpu", "Scripts", "python.exe")
    work = os.path.join(DESKTOP_DIR, "build", "work-cpu", "aura")
    if not (os.path.isfile(venv_py) and os.path.isfile(os.path.join(work, "PYZ-00.toc"))):
        if verbose:
            print("         no CPU build to scan, skipped")
        return []
    failures = []
    with tempfile.TemporaryDirectory() as out:
        r = subprocess.run([venv_py, os.path.join(DESKTOP_DIR, "write_licenses.py"), work, out],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return [f"write_licenses.py failed: {r.stderr.strip()[-300:]}"]
        text = open(os.path.join(out, "LICENSES.txt"), encoding="utf-8").read()
        inventory = text.split("ALL BUNDLED PYTHON PACKAGES", 1)[-1]
        for pkg in ("ultralytics", "torch", "opencv-python", "Flask", "colour-science", "pywebview", "pyinstaller"):
            if not re.search(rf"^{re.escape(pkg)}\s", inventory, re.M | re.I):
                failures.append(f"{pkg} not in the shipped-package list")
        for pkg in ("pip", "polars"):
            if re.search(rf"^{pkg}\s", inventory, re.M):
                failures.append(f"{pkg} listed as shipped but it is not bundled")
        agpl = [f for f in glob.glob(os.path.join(out, "licenses", "ultralytics-*", "**", "LICENSE*"),
                                     recursive=True) if os.path.isfile(f)]
        if not agpl or "AFFERO" not in open(agpl[0], encoding="utf-8").read():
            failures.append("AGPL-3.0 text not copied into licenses/")
        for need in (("python", "LICENSE.txt"), ("fonts", "OFL-Fraunces.txt"), ("fonts", "OFL-DMSans.txt")):
            if not os.path.isfile(os.path.join(out, "licenses", *need)):
                failures.append(f"licenses/{'/'.join(need)} missing")
        if verbose:
            print(f"         {r.stdout.strip()}")
    return failures


CHECKS = [
    ("every required component is credited", check_required_present),
    ("each component has licence, links, copyright and role", check_component_fields),
    ("stated licences match the packages' own metadata", check_licences_match_metadata),
    ("Ultralytics AGPL-3.0 notes and source link", check_agpl_and_source),
    ("bundled fonts credited with their OFL texts", check_fonts),
    ("all 14 template photos credited, none extra", check_photos),
    ("GET /api/credits", check_api),
    ("Licenses page wired into the app, loads nothing online", check_page_wiring),
    ("LICENSES.txt text covers everything", check_render_text),
    ("build writer: shipped packages and licence texts", check_build_writer),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Tests for backend/credits.py")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    print(f"credits — {len(credits.COMPONENTS)} components, {len(credits.FONTS)} fonts, "
          f"{len(ct.PHOTOS)} photos\n")
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
