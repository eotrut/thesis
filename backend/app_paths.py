"""
AURA — where files live, from source or from the packaged desktop app.

Two layouts have to work:

* From source (``python backend/app.py`` or ``python desktop/aura_desktop.py``):
  everything is relative to the repository root, exactly as before.

* Frozen by PyInstaller into ``AURA.exe``. PyInstaller unpacks the bundled
  read-only files (pages, Python code) into a resource directory it names in
  ``sys._MEIPASS``; that is NOT the folder the exe sits in, and ``__file__``
  points inside it. The model weights are deliberately not bundled there:
  they are git-ignored, large, and swapped by hand, so they sit in a ``model``
  folder next to ``AURA.exe`` where a user can see and replace them.

Everything that builds a path to a page or a weights file goes through this
module, so the two layouts differ in exactly one place.
"""

from __future__ import annotations

import os
import sys

# True inside a PyInstaller build. ``sys.frozen`` is set by its bootloader.
FROZEN: bool = bool(getattr(sys, "frozen", False))

if FROZEN:
    # Read-only files bundled into the build (pages, code).
    RESOURCE_ROOT = os.path.abspath(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
    # The folder holding AURA.exe — where the user-visible files live.
    INSTALL_DIR = os.path.dirname(os.path.abspath(sys.executable))
    PROJECT_ROOT = INSTALL_DIR
    MODEL_DIR = os.path.join(INSTALL_DIR, "model")
else:
    BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
    RESOURCE_ROOT = PROJECT_ROOT
    INSTALL_DIR = PROJECT_ROOT
    MODEL_DIR = os.path.join(PROJECT_ROOT, "website", "model")


def model_file(name: str) -> str:
    """Absolute path of a weights file in the model folder (may not exist)."""
    return os.path.join(MODEL_DIR, name)


def display_path(path: str) -> str:
    """Path relative to the project/install root, for logs and /api/status.

    Falls back to the absolute path when the two are on different drives,
    where ``os.path.relpath`` raises on Windows.
    """
    try:
        return os.path.relpath(path, PROJECT_ROOT)
    except ValueError:
        return path
