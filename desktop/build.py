"""
Build the AURA desktop app into a folder that runs without Python.

    py -3.11 desktop/build.py cpu          # small build to hand out
    py -3.11 desktop/build.py gpu          # CUDA build for the RTX 3050 laptop
    py -3.11 desktop/build.py cpu --zip    # also make the zip to share

What it does, in order:
1. Makes (once) a clean build venv in desktop/build/venv-<flavour> and installs
   desktop/requirements-build-<flavour>.txt into it — only the packages the
   app needs, with the CPU-only or the CUDA torch. Nothing from the project's
   own venv (roboflow, training tools) can end up in the package.
2. Checks the venv really has the torch it should (CPU build: no CUDA).
3. Runs PyInstaller with desktop/aura.spec -> desktop/dist/AURA-<FLAVOUR>/.
4. Copies best.pt and mobile_sam.pt from website/model/ into the build's
   model/ folder (they are git-ignored, so they are not in the repo).
5. Adds README-FIRST.txt and BUILD-INFO.txt (exact versions, git commit).
6. Writes LICENSES.txt and a licenses/ folder of licence texts for every
   package that actually shipped (desktop/write_licenses.py).
7. Prints the folder size, and with --zip writes desktop/dist/AURA-<F>.zip.

Must run with Python 3.11 (the version the app is pinned to). Takes 5-15 min;
the first run also downloads torch (~200 MB CPU / ~2.5 GB CUDA).
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
import time

DESKTOP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DESKTOP)
BUILD = os.path.join(DESKTOP, "build")
DIST = os.path.join(DESKTOP, "dist")
MODEL_SRC = os.path.join(ROOT, "website", "model")
MODEL_FILES = ("best.pt", "mobile_sam.pt")

EXPECTED_CUDA = {"cpu": None, "gpu": "12.1"}


def step(msg: str) -> None:
    print(f"\n=== {msg}", flush=True)


def run(cmd: list[str], **kw) -> None:
    print("  $ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def output(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def folder_size(path: str) -> int:
    total = 0
    for base, _dirs, files in os.walk(path):
        for name in files:
            total += os.path.getsize(os.path.join(base, name))
    return total


def gb(n: int) -> str:
    return f"{n / 1024 ** 3:.2f} GB ({n / 1024 ** 2:,.0f} MB)"


def git_describe() -> str:
    try:
        commit = output(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"])
        # Untracked files under backend/tools (tests, their logs) never go into
        # the app, so they don't make the build differ from the commit.
        dirty = [line for line in output(["git", "-C", ROOT, "status", "--porcelain", "--",
                                          "backend", "desktop"]).splitlines()
                 if not (line.startswith("??") and line[3:].startswith("backend/tools/"))]
        return commit + (" + uncommitted changes in backend/ or desktop/" if dirty else "")
    except Exception:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the AURA desktop app")
    parser.add_argument("flavor", choices=("cpu", "gpu"))
    parser.add_argument("--zip", action="store_true", help="also write desktop/dist/AURA-<F>.zip")
    parser.add_argument("--skip-install", action="store_true",
                        help="reuse the build venv as-is (faster rebuilds)")
    args = parser.parse_args()
    flavor = args.flavor
    name = f"AURA-{flavor.upper()}"

    if sys.version_info[:2] != (3, 11):
        sys.exit(f"Run this with Python 3.11 (py -3.11 ...), not {sys.version.split()[0]}.")
    if sys.platform != "win32":
        sys.exit("The desktop app is Windows-only.")

    missing = [f for f in MODEL_FILES if not os.path.isfile(os.path.join(MODEL_SRC, f))]
    if missing:
        sys.exit(f"Missing weights in website/model/: {', '.join(missing)}. "
                 f"They are git-ignored; copy them there first.")

    started = time.time()
    venv = os.path.join(BUILD, f"venv-{flavor}")
    py = os.path.join(venv, "Scripts", "python.exe")

    if not os.path.isfile(py):
        step(f"Creating clean build venv {os.path.relpath(venv, ROOT)}")
        run([sys.executable, "-m", "venv", venv])
        run([py, "-m", "pip", "install", "--upgrade", "pip"])
    if not args.skip_install:
        step(f"Installing requirements-build-{flavor}.txt")
        run([py, "-m", "pip", "install", "-r",
             os.path.join(DESKTOP, f"requirements-build-{flavor}.txt")])

    step("Checking the venv has the right torch")
    cuda = output([py, "-c", "import torch; print(torch.version.cuda)"])
    cuda = None if cuda == "None" else cuda
    torch_version = output([py, "-c", "import torch; print(torch.__version__)"])
    print(f"  torch {torch_version}, CUDA build: {cuda}")
    if cuda != EXPECTED_CUDA[flavor]:
        sys.exit(f"Wrong torch for a {flavor} build (CUDA {cuda}, expected "
                 f"{EXPECTED_CUDA[flavor]}). Delete {venv} and run again.")

    step("Running PyInstaller")
    # YOLO_AUTOINSTALL=false: PyInstaller imports ultralytics modules to scan
    # them, and some call check_requirements() at import time, which would
    # otherwise pip-install into the build venv mid-build.
    env = dict(os.environ, AURA_BUILD_FLAVOR=flavor,
               YOLO_AUTOINSTALL="false", YOLO_OFFLINE="true")
    for var in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(var, None)
    run([py, "-m", "PyInstaller", os.path.join(DESKTOP, "aura.spec"),
         "--noconfirm", "--clean",
         "--distpath", DIST,
         "--workpath", os.path.join(BUILD, f"work-{flavor}")], env=env)

    out = os.path.join(DIST, name)
    step(f"Adding model weights to {os.path.relpath(out, ROOT)}\\model")
    model_dir = os.path.join(out, "model")
    os.makedirs(model_dir, exist_ok=True)
    for f in MODEL_FILES:
        shutil.copy2(os.path.join(MODEL_SRC, f), os.path.join(model_dir, f))
        print(f"  {f}")

    shutil.copy2(os.path.join(DESKTOP, "README-FIRST.txt"), os.path.join(out, "README-FIRST.txt"))

    # LICENSES.txt + licenses/: run in the build venv so the package metadata
    # it reads is exactly what PyInstaller bundled (see write_licenses.py).
    step("Writing LICENSES.txt and licenses\\")
    run([py, os.path.join(DESKTOP, "write_licenses.py"),
         os.path.join(BUILD, f"work-{flavor}", "aura"), out], env=env)

    freeze = output([py, "-m", "pip", "freeze"])
    with open(os.path.join(out, "BUILD-INFO.txt"), "w", encoding="utf-8") as fh:
        fh.write(
            f"AURA desktop — {flavor.upper()} build\n"
            f"Built     : {dt.datetime.now():%Y-%m-%d %H:%M}\n"
            f"Git       : {git_describe()}\n"
            f"Python    : {output([py, '-c', 'import sys; print(sys.version.split()[0])'])}\n"
            f"torch     : {torch_version} (CUDA build: {cuda})\n\n"
            f"Exact packages in the build venv:\n{freeze}\n"
        )

    size = folder_size(out)
    step("Done")
    print(f"  Folder : {out}")
    print(f"  Size   : {gb(size)} unpacked")

    if args.zip:
        archive = os.path.join(DIST, f"{name}.zip")
        if os.path.exists(archive):
            os.remove(archive)
        print("  Zipping (takes a few minutes)...", flush=True)
        # Windows' bundled bsdtar writes real .zip files and, unlike PowerShell's
        # Compress-Archive, copes with the >2 GB CUDA DLLs.
        run(["tar", "-a", "-c", "-f", archive, "-C", DIST, name])
        print(f"  Zip    : {archive}")
        print(f"  Size   : {gb(os.path.getsize(archive))}")

    print(f"  Took   : {(time.time() - started) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
