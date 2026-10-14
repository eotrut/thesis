"""
AURA desktop app — the existing backend and pages inside a native window.

This is not a rewrite. The Flask backend (backend/app.py) is the same code the
website uses; this file starts it inside the app's own process and shows its
pages in a window instead of a browser tab.

What happens at launch
----------------------
1. A window opens immediately with a "Starting AURA…" screen.
2. On a background thread: the backend is imported (this pulls in PyTorch, the
   slow part), the YOLOv8 model loads onto CUDA if an NVIDIA GPU is usable and
   onto the CPU otherwise, and a small web server starts on 127.0.0.1 (this
   computer only, unreachable from the network) at a port Windows picks.
3. The window switches to the Dashboard.
4. When the window closes, the server is stopped, the webcam released and the
   process exits — nothing is left running in the background.

The window is pywebview, which on Windows uses Microsoft Edge WebView2 (the
browser engine built into Windows 10/11). The pages it shows are the app's own
copies in desktop/ui/, so website/ is not touched.

Run from source (project venv active):
    python desktop/aura_desktop.py

Environment variables (all optional):
    AURA_DESKTOP_PORT   fixed port instead of a free one (default 0 = pick)
    AURA_DESKTOP_DEBUG  1 = allow right-click > Inspect (Edge DevTools)
    AURA_DEVICE         cpu / cuda:0 — force the inference device (backend)
Logs: %LOCALAPPDATA%\\AURA\\logs\\aura-desktop.log (previous run: .log.1)
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import threading
from typing import Any

logger = logging.getLogger("aura.desktop")

APP_TITLE = "AURA"
HOST = "127.0.0.1"
HOME_PAGE = "dashboard.html"
LOG_FORMAT = "%(asctime)s  %(levelname)-7s %(name)s: %(message)s"

FROZEN = bool(getattr(sys, "frozen", False))
if FROZEN:
    # PyInstaller bundle: the pages and the backend modules are unpacked here.
    BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    UI_DIR = os.path.join(BUNDLE_DIR, "ui")
    BACKEND_DIR = BUNDLE_DIR
else:
    DESKTOP_DIR = os.path.dirname(os.path.abspath(__file__))
    UI_DIR = os.path.join(DESKTOP_DIR, "ui")
    BACKEND_DIR = os.path.join(os.path.dirname(DESKTOP_DIR), "backend")


# --------------------------------------------------------------------------- #
# Small pure helpers (covered by backend/tools/test_desktop_shell.py)
# --------------------------------------------------------------------------- #

def origin_for(port: int) -> str:
    """The app's own web address, e.g. ``http://127.0.0.1:53817``."""
    return f"http://{HOST}:{int(port)}"


def is_own_origin(uri: str | None, origin: str | None) -> bool:
    """True only for pages served by this app's own backend.

    Used to auto-allow the camera. ``http://127.0.0.1:5381`` must not match
    ``http://127.0.0.1:53817``, nor ``http://127.0.0.1:53817.evil.example``,
    so the check is the exact origin or the origin followed by ``/``.
    """
    if not uri or not origin:
        return False
    return uri == origin or uri.startswith(origin + "/")


def requested_port() -> int:
    """Port from AURA_DESKTOP_PORT, or 0 (let Windows choose a free one)."""
    raw = os.environ.get("AURA_DESKTOP_PORT", "").strip()
    try:
        port = int(raw) if raw else 0
    except ValueError:
        logger.warning("AURA_DESKTOP_PORT=%r is not a number — using a free port.", raw)
        return 0
    return port if 0 <= port <= 65535 else 0


def log_dir() -> str:
    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    return os.path.join(base, "AURA", "logs")


def backend_environment(ui_dir: str) -> dict[str, str]:
    """Settings the backend reads at import time, for the desktop layout.

    The two YOLO_* switches stop Ultralytics from pip-installing packages or
    probing the internet at runtime. In the packaged app "run pip with this
    Python" would mean launching AURA.exe again, and the app must work offline.
    """
    return {
        "AURA_HOST": HOST,
        "AURA_WEB_DIR": ui_dir,
        "AURA_HOME_PAGE": HOME_PAGE,
        "YOLO_AUTOINSTALL": "false",
        "YOLO_OFFLINE": "true",
    }


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #

def setup_logging() -> str:
    """Log to a file (always) and to the console (when there is one).

    The packaged exe has no console, so Python's ``sys.stdout``/``sys.stderr``
    are ``None`` there; anything printed (the backend's startup banner,
    Ultralytics messages) would vanish or crash. Both are pointed at the log
    file in that case.
    """
    directory = log_dir()
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        directory = tempfile.gettempdir()
    path = os.path.join(directory, "aura-desktop.log")

    # Keep exactly one previous run for "it broke last time" reports.
    try:
        if os.path.exists(path):
            os.replace(path, path + ".1")
    except OSError:
        pass

    stream = open(path, "w", encoding="utf-8", buffering=1, errors="replace")
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt="%H:%M:%S")
    file_handler = logging.StreamHandler(stream)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    if sys.__stdout__ is not None and stream is not sys.stdout:
        console = logging.StreamHandler(sys.__stdout__)
        console.setFormatter(formatter)
        root.addHandler(console)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    return path


# --------------------------------------------------------------------------- #
# Backend lifecycle
# --------------------------------------------------------------------------- #

class Shell:
    """Owns the backend server for the lifetime of the window."""

    def __init__(self, log_path: str) -> None:
        self.log_path = log_path
        self.origin: str | None = None
        self.server: Any = None
        self.backend: Any = None
        self._thread: threading.Thread | None = None

    def start_backend(self, port: int = 0) -> str:
        """Import the backend, load the model, serve on 127.0.0.1. Returns origin."""
        os.environ.update(backend_environment(UI_DIR))
        if BACKEND_DIR not in sys.path:
            sys.path.insert(0, BACKEND_DIR)

        import app as backend  # noqa: E402 — heavy: imports torch + ultralytics
        from werkzeug.serving import make_server

        self.backend = backend
        backend.load_model()

        # threaded=True for the same reason as app.py: an MJPEG stream holds a
        # worker for its whole life and /api/status must still answer.
        # Werkzeug's request threads are daemon threads, so they cannot keep
        # the process alive after the window closes.
        self.server = make_server(HOST, port, backend.app, threaded=True)
        backend.PORT = self.server.port
        self.origin = origin_for(self.server.port)

        self._thread = threading.Thread(
            target=self.server.serve_forever, name="aura-http", daemon=True
        )
        self._thread.start()
        logger.info("Backend serving %s on %s", UI_DIR, self.origin)
        return self.origin

    def report_device(self) -> None:
        """The startup check: which device inference runs on, in the log."""
        backend = self.backend
        if backend is None:
            return
        model = backend.segmentation_model
        if model.is_loaded:
            kind = "CUDA" if str(model.device).startswith("cuda") else "CPU"
            logger.info("Inference device: %s — %s (%s)", kind, model.device, model.device_name)
        else:
            logger.error("Model NOT loaded: %s", model.error)
        try:
            backend.startup_report()  # the same banner `python backend/app.py` prints
        except Exception:
            logger.exception("Startup report failed (non-fatal)")

    def stop(self, timeout: float = 5.0) -> None:
        """Stop serving and release the webcam. Never raises."""
        if self.server is not None:
            stopper = threading.Thread(target=self.server.shutdown, daemon=True)
            stopper.start()
            stopper.join(timeout)
            try:
                self.server.server_close()
            except Exception:
                pass
            logger.info("Backend stopped")
        if self.backend is not None:
            try:
                if not self.backend.camera.close(timeout=2.0):
                    logger.warning("Camera busy at shutdown — Windows frees it on exit.")
            except Exception:
                logger.exception("Camera release failed (non-fatal)")


# --------------------------------------------------------------------------- #
# Window
# --------------------------------------------------------------------------- #

PAGE_STYLE = (
    "body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;"
    "background:#0A1628;color:#E2E8F0;font-family:'Segoe UI',sans-serif}"
    ".box{max-width:620px;padding:32px;text-align:center}"
    "h1{font-size:28px;letter-spacing:.2em;margin:0 0 12px}"
    "p{color:#94A3B8;line-height:1.5}"
    "code{background:#0F1E3A;padding:2px 6px;border-radius:4px;color:#E2E8F0}"
)


def loading_html() -> str:
    return (
        f"<!doctype html><html><head><meta charset='utf-8'><style>{PAGE_STYLE}</style></head>"
        "<body><div class='box'><h1>AURA</h1>"
        "<p>Starting the segmentation engine…<br>The first start can take up to a minute.</p>"
        "</div></body></html>"
    )


def error_html(message: str, log_path: str) -> str:
    import html

    return (
        f"<!doctype html><html><head><meta charset='utf-8'><style>{PAGE_STYLE}</style></head>"
        "<body><div class='box'><h1>AURA</h1>"
        "<p>The backend could not start.</p>"
        f"<p><code>{html.escape(message)}</code></p>"
        f"<p>Details are in<br><code>{html.escape(log_path)}</code></p>"
        "</div></body></html>"
    )


def install_camera_permission(shell: Shell) -> None:
    """Auto-allow the webcam for the app's own pages.

    WebView2 asks for camera permission like a browser does; pywebview does not
    answer that request, so WebView2 would show its own prompt on every launch
    (private mode forgets the answer). This answers "allow" for the camera only,
    and only when the requesting page is this app's own backend address.

    pywebview has no public hook for this, so the WebView2-ready handler of its
    Edge backend is wrapped (pywebview is pinned in desktop/requirements). If
    the internals ever move, this logs a warning and the Edge prompt is back —
    the camera still works after the user clicks Allow.
    """
    try:
        from webview.platforms import edgechromium
        from Microsoft.Web.WebView2.Core import (  # type: ignore[import-not-found]
            CoreWebView2PermissionKind,
            CoreWebView2PermissionState,
        )
    except Exception as exc:
        logger.warning("Camera auto-permission unavailable (%s); Edge will prompt.", exc)
        return

    original = edgechromium.EdgeChrome.on_webview_ready

    def on_webview_ready(self, sender, args):
        original(self, sender, args)
        if not args.IsSuccess:
            return
        try:
            def on_permission(_sender, event):
                if (
                    event.PermissionKind == CoreWebView2PermissionKind.Camera
                    and is_own_origin(str(event.Uri), shell.origin)
                ):
                    event.State = CoreWebView2PermissionState.Allow

            sender.CoreWebView2.PermissionRequested += on_permission
        except Exception:
            logger.exception("Could not attach the camera permission handler")

    edgechromium.EdgeChrome.on_webview_ready = on_webview_ready


def boot(window, shell: Shell) -> None:
    """Runs on pywebview's worker thread once the window exists."""
    try:
        origin = shell.start_backend(requested_port())
    except Exception as exc:
        logger.exception("Backend failed to start")
        window.load_html(error_html(f"{type(exc).__name__}: {exc}", shell.log_path))
        return
    # Report first, then show the page. The report probes the webcam (1-2 s on
    # Windows); doing it after load_url raced the Dashboard's first
    # /api/status poll for the camera lock and made that poll time out.
    # Done first, the probe result is cached for the page's first poll.
    shell.report_device()
    window.load_url(origin + "/")


def main() -> int:
    log_path = setup_logging()
    logger.info("AURA desktop starting (frozen=%s, python %s)", FROZEN, sys.version.split()[0])

    import webview

    # The toolpath view offers "Download G-code"; pywebview blocks downloads
    # unless told otherwise.
    webview.settings["ALLOW_DOWNLOADS"] = True

    shell = Shell(log_path)
    install_camera_permission(shell)

    window = webview.create_window(
        APP_TITLE,
        html=loading_html(),
        width=1360,
        height=860,
        min_size=(1024, 680),
        background_color="#0A1628",
        text_select=True,
    )

    debug = os.environ.get("AURA_DESKTOP_DEBUG", "").lower() in ("1", "true", "yes")
    try:
        webview.start(boot, (window, shell), debug=debug, private_mode=True)
    finally:
        # The window is gone (closed, or failed to open): shut everything down.
        shell.stop()
        logger.info("AURA desktop exited")
        logging.shutdown()

    # Hard exit on purpose. A model still loading on the boot thread, an open
    # MJPEG connection, or a library's helper thread could otherwise keep a
    # python.exe alive with no window — the "orphan process" case.
    os._exit(0)


if __name__ == "__main__":
    sys.exit(main())
