"""Write LICENSES.txt and a licenses/ folder into a built AURA package.

build.py runs this with the *build venv's* Python, so the package metadata it
reads is exactly what PyInstaller bundled from:

    <venv>\\Scripts\\python.exe desktop/write_licenses.py <work_dir> <out_dir>

1. Finds which installed distributions actually ship, from PyInstaller's own
   inventories: PYZ-00.toc (every Python module packed) and COLLECT-00.toc
   (every file copied next to AURA.exe). Build-only tools in the venv (pip,
   PyInstaller's analysis code...) are not listed, except the PyInstaller
   bootloader, which is part of AURA.exe.
2. Copies each shipped distribution's own licence/notice files from its
   .dist-info into <out_dir>/licenses/<name>-<version>/, plus the font licences.
3. Writes <out_dir>/LICENSES.txt: the curated credits from backend/credits.py
   followed by the full package inventory with the licence each one declares.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import sys
from importlib import metadata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "backend"))

import credits  # noqa: E402

LICENCE_FILE = re.compile(r"(LICEN[CS]E|COPYING|NOTICE|AUTHORS)", re.I)
# The bootloader is compiled into AURA.exe, so it ships even though no
# pyinstaller module is in the archive.
ALWAYS_SHIPPED = {"pyinstaller"}


def read_toc(path: str) -> list:
    with open(path, encoding="utf-8") as fh:
        return ast.literal_eval(fh.read())


def shipped_top_levels(work_dir: str) -> set[str]:
    names = set()
    pyz = read_toc(os.path.join(work_dir, "PYZ-00.toc"))
    for entry in pyz[1]:
        names.add(entry[0].split(".")[0].lower())
    collect = read_toc(os.path.join(work_dir, "COLLECT-00.toc"))
    for entry in collect[0]:
        first = re.split(r"[\\/]", entry[0])[0]
        names.add(first.split(".")[0].lower())
        # some wheels ship DLLs in a sibling "<pkg>.libs" folder
        names.add(first.lower().removesuffix(".libs"))
    return names


def declared_licence(dist: metadata.Distribution) -> str:
    """The licence a distribution declares, best field first."""
    m = dist.metadata
    expr = (m.get("License-Expression") or "").strip()
    if expr:
        return expr
    lic = (m.get("License") or "").strip()
    # A one-line License field is a name; a multi-line one is the whole text.
    usable = lic if lic and len(lic) <= 160 and len(lic.splitlines()) == 1 else ""
    classifiers = [c.split("::")[-1].strip() for c in (m.get_all("Classifier") or [])
                   if c.startswith("License ::") and c.split("::")[-1].strip() != "OSI Approved"]
    if usable and classifiers and not any(k.lower() in usable.lower() for k in classifiers):
        return f"{usable} ({' / '.join(classifiers)})"
    if usable:
        return usable
    if classifiers:
        return " / ".join(classifiers)
    return "see licence files"


def title_from_file(path: str) -> str:
    """'MIT License' etc. from a licence file's first line, when metadata names none."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line:
                if re.search(r"licen[cs]e", line, re.I) and len(line) <= 60:
                    return f"{line} (from its licence file)"
                return ""
    return ""


def homepage(dist: metadata.Distribution) -> str:
    m = dist.metadata
    for raw in m.get_all("Project-URL") or []:
        label, _, url = raw.partition(",")
        if label.strip().lower() in ("source", "source code", "repository", "homepage", "home", "github", "code"):
            return url.strip()
    return (m.get("Home-page") or "").strip()


def shipped_distributions(work_dir: str) -> list[metadata.Distribution]:
    shipped = shipped_top_levels(work_dir)
    by_dist: dict[str, set[str]] = {}
    for top, dists in metadata.packages_distributions().items():
        for d in dists:
            by_dist.setdefault(d.lower(), set()).add(top.lower())
    out, seen = [], set()
    for dist in metadata.distributions():
        name = dist.metadata["Name"]
        key = name.lower()
        if key in seen:
            continue
        tops = by_dist.get(key, set())
        if key in ALWAYS_SHIPPED or tops & shipped:
            out.append(dist)
            seen.add(key)
    return sorted(out, key=lambda d: d.metadata["Name"].lower())


def copy_licence_files(dist: metadata.Distribution, dest_root: str) -> list[str]:
    name, version = dist.metadata["Name"], dist.version
    copied = []
    for f in dist.files or []:
        rel = str(f).replace("\\", "/")
        if ".dist-info" not in rel or not LICENCE_FILE.search(rel.rsplit("/", 1)[-1]):
            continue
        src = f.locate()
        if not os.path.isfile(src):
            continue
        # keep the path inside .dist-info: numpy has several LICENSE files
        inner = rel.split(".dist-info/", 1)[1]
        dest = os.path.join(dest_root, f"{name}-{version}", *inner.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(os.path.relpath(dest, os.path.dirname(dest_root)).replace("\\", "/"))
    return copied


def main() -> int:
    work_dir, out_dir = sys.argv[1], sys.argv[2]
    lic_dir = os.path.join(out_dir, "licenses")
    if os.path.isdir(lic_dir):
        shutil.rmtree(lic_dir)
    os.makedirs(lic_dir)

    packages = []
    for dist in shipped_distributions(work_dir):
        files = copy_licence_files(dist, lic_dir)
        licence = declared_licence(dist)
        if licence == "see licence files" and files:
            licence = title_from_file(os.path.join(out_dir, files[0])) or licence
        packages.append({
            "name": dist.metadata["Name"],
            "version": dist.version,
            "license": licence,
            "url": homepage(dist),
            "files": files,
        })

    # The Python runtime (python311.dll + stdlib) ships too; its licence sits
    # in the base install the venv was made from.
    py_lic = os.path.join(sys.base_prefix, "LICENSE.txt")
    if os.path.isfile(py_lic):
        os.makedirs(os.path.join(lic_dir, "python"))
        shutil.copy2(py_lic, os.path.join(lic_dir, "python", "LICENSE.txt"))

    fonts_dir = os.path.join(lic_dir, "fonts")
    os.makedirs(fonts_dir)
    for font in credits.FONTS:
        src = os.path.join(HERE, "ui", "assets", "fonts", font["license_file"])
        shutil.copy2(src, os.path.join(fonts_dir, font["license_file"]))

    with open(os.path.join(lic_dir, "packages.json"), "w", encoding="utf-8") as fh:
        json.dump(packages, fh, indent=1)
    with open(os.path.join(out_dir, "LICENSES.txt"), "w", encoding="utf-8") as fh:
        fh.write(credits.render_text(packages))

    missing = [p["name"] for p in packages if not p["files"]]
    print(f"  {len(packages)} shipped packages credited in LICENSES.txt")
    if missing:
        print(f"  no licence file in metadata (licence named only): {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
