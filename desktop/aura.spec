# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller recipe for the AURA desktop app. Run through desktop/build.py,
which picks the flavour, installs the right torch and copies the weights in:

    py -3.11 desktop/build.py cpu      # -> desktop/dist/AURA-CPU/AURA.exe
    py -3.11 desktop/build.py gpu      # -> desktop/dist/AURA-GPU/AURA.exe

One recipe, two packages: the only difference between the builds is which
torch wheel is installed in the build venv (CPU-only or +cu121). The flavour
here just names the output folder.

"onedir" on purpose (a folder with AURA.exe + _internal/), not "onefile":
a one-file exe would unpack ~1-5 GB to a temp folder on EVERY launch.
"""

import os

from PyInstaller.utils.hooks import collect_submodules

FLAVOR = os.environ.get("AURA_BUILD_FLAVOR", "cpu").lower()
if FLAVOR not in ("cpu", "gpu"):
    raise SystemExit(f"AURA_BUILD_FLAVOR must be cpu or gpu, not {FLAVOR!r}")

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821 (SPECPATH is injected)
BACKEND = os.path.join(ROOT, "backend")
DESKTOP = os.path.join(ROOT, "desktop")

# ultralytics resolves YOLO / SAM by name at runtime (`from ultralytics import
# SAM` goes through a module __getattr__), which static analysis cannot follow.
# Tracking and "solutions" (dashboards, counters) are not used by AURA and are
# left out: ultralytics.trackers runs check_requirements("lap") at import,
# which with auto-install on pip-installs into whatever Python imports it —
# it did exactly that to the build venv on the first build (2026-10-14).
# build.py also sets YOLO_AUTOINSTALL=false so nothing installs during analysis.
hiddenimports = collect_submodules(
    "ultralytics",
    filter=lambda name: not name.startswith(("ultralytics.trackers", "ultralytics.solutions")),
)

# Imported somewhere in the dependency tree but never on AURA's inference path,
# and large. Checked by running every endpoint and listing sys.modules
# (2026-10-14): none of these appear. Training-only tools would only get here
# if a build venv had them installed; the build venvs do not, this is a guard.
excludes = [
    "roboflow",
    "polars",            # ultralytics hard dependency, used only for exports/metrics tables
    "pandas",
    "tensorboard",
    "torch.utils.tensorboard",
    "IPython",
    "jupyter",
    "notebook",
    "pytest",
    "tkinter",           # no Tk windows; matplotlib only renders off-screen if at all
    "serial",            # pyserial — robot link, not used by the API
]

a = Analysis(  # noqa: F821
    [os.path.join(DESKTOP, "aura_desktop.py")],
    pathex=[BACKEND],
    binaries=[],
    datas=[(os.path.join(DESKTOP, "ui"), "ui")],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AURA",
    debug=False,
    strip=False,
    # UPX compression is off: it breaks some torch/CUDA DLLs and makes
    # antivirus tools far more suspicious of an unsigned exe.
    upx=False,
    # No console window. Output goes to %LOCALAPPDATA%\AURA\logs instead.
    console=False,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=f"AURA-{FLAVOR.upper()}",
)
