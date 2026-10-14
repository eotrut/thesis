"""
AURA — Desktop app shell tests.

Standalone script, same shape as ``test_color_recommender.py``: run it, read
the summary, exit code says whether anything broke.

What is under test is the plumbing that turns the website into the desktop app
(desktop/aura_desktop.py + backend/app_paths.py), not the model or the pages'
behaviour:

* path resolution from source AND as a PyInstaller build (simulated in a child
  interpreter by setting ``sys.frozen`` / ``sys._MEIPASS`` / ``sys.executable``,
  which is exactly what PyInstaller's bootloader sets), so weights are looked
  for in ``model/`` next to AURA.exe and pages in the bundle;
* the app serves only Camera View, Color Recommendation and Dashboard, while
  ``python backend/app.py`` still serves the whole website from website/;
* the server binds 127.0.0.1 on a free port and stops when asked;
* the camera auto-permission origin check cannot be fooled by a look-alike
  address;
* ``Camera.close()`` cannot hang shutdown.

Needs no model weights, no GPU, no webcam and no window — it never imports
pywebview or loads YOLO.

Run:
    python backend/tools/test_desktop_shell.py
    python backend/tools/test_desktop_shell.py -v
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DESKTOP_DIR = os.path.join(PROJECT_ROOT, "desktop")
UI_DIR = os.path.join(DESKTOP_DIR, "ui")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, DESKTOP_DIR)

import aura_desktop as shell  # noqa: E402  (pure helpers; pywebview is imported lazily)

APP_PAGES = {"dashboard.html", "color-recommendation.html", "camera-view.html"}
DROPPED_PAGES = {"index.html", "about.html", "results.html"}


def run_child(code: str, env: dict | None = None) -> dict:
    """Run ``code`` in a fresh interpreter and return the JSON it prints last."""
    full_env = dict(os.environ)
    for key in ("AURA_WEB_DIR", "AURA_HOME_PAGE", "AURA_HOST", "AURA_MODEL_PATH",
                "AURA_SAM_MODEL", "AURA_FALLBACK_MODEL"):
        full_env.pop(key, None)
    full_env.update(env or {})
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, env=full_env, cwd=PROJECT_ROOT, timeout=120,
    )
    if out.returncode != 0:
        raise RuntimeError(f"child failed:\n{out.stderr[-1500:]}")
    return json.loads(out.stdout.strip().splitlines()[-1])


def same(a: str, b: str) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

def check_source_paths(verbose: bool) -> list[str]:
    """From source, nothing moves: weights in website/model, pages in website/."""
    import app_paths
    import model_loader
    import smart_select

    failures = []
    if app_paths.FROZEN:
        failures.append("FROZEN is True when running from source")
    expected_models = os.path.join(PROJECT_ROOT, "website", "model")
    if not same(app_paths.MODEL_DIR, expected_models):
        failures.append(f"MODEL_DIR {app_paths.MODEL_DIR!r} != {expected_models!r}")
    if not same(model_loader.DEFAULT_MODEL_PATH, os.path.join(expected_models, "best.pt")):
        failures.append(f"best.pt resolves to {model_loader.DEFAULT_MODEL_PATH!r}")
    if not same(smart_select.DEFAULT_SAM_PATH, os.path.join(expected_models, "mobile_sam.pt")):
        failures.append(f"mobile_sam.pt resolves to {smart_select.DEFAULT_SAM_PATH!r}")
    if not same(model_loader.FALLBACK_MODEL_PATH, os.path.join(PROJECT_ROOT, "yolov8n-seg.pt")) \
            and not os.environ.get("AURA_FALLBACK_MODEL"):
        failures.append(f"fallback resolves to {model_loader.FALLBACK_MODEL_PATH!r}")
    if verbose:
        print(f"         source MODEL_DIR = {app_paths.MODEL_DIR}")
    return failures


def check_frozen_paths(verbose: bool) -> list[str]:
    """As a PyInstaller build: pages from the bundle, weights next to AURA.exe."""
    with tempfile.TemporaryDirectory() as tmp:
        install = os.path.join(tmp, "AURA")
        bundle = os.path.join(install, "_internal")
        exe = os.path.join(install, "AURA.exe")
        code = f"""
import json, sys
sys.frozen = True
sys._MEIPASS = {bundle!r}
sys.executable = {exe!r}
sys.path.insert(0, {BACKEND_DIR!r})
sys.path.insert(0, {DESKTOP_DIR!r})
import app_paths, model_loader, smart_select, aura_desktop
print(json.dumps({{
    "frozen": app_paths.FROZEN,
    "resource": app_paths.RESOURCE_ROOT,
    "install": app_paths.INSTALL_DIR,
    "model_dir": app_paths.MODEL_DIR,
    "best": model_loader.DEFAULT_MODEL_PATH,
    "sam": smart_select.DEFAULT_SAM_PATH,
    "fallback": model_loader.FALLBACK_MODEL_PATH,
    "ui": aura_desktop.UI_DIR,
    "backend": aura_desktop.BACKEND_DIR,
    "shown": model_loader.display_path(model_loader.DEFAULT_MODEL_PATH),
}}))
"""
        got = run_child(code)

    failures = []
    expect = {
        "resource": bundle,
        "install": install,
        "model_dir": os.path.join(install, "model"),
        "best": os.path.join(install, "model", "best.pt"),
        "sam": os.path.join(install, "model", "mobile_sam.pt"),
        "fallback": os.path.join(install, "model", "yolov8n-seg.pt"),
        "ui": os.path.join(bundle, "ui"),
        "backend": bundle,
    }
    if got["frozen"] is not True:
        failures.append("FROZEN not detected from sys.frozen")
    for key, want in expect.items():
        if not same(got[key], want):
            failures.append(f"frozen {key}: {got[key]!r} != {want!r}")
    if got["shown"].replace("\\", "/") != "model/best.pt":
        failures.append(f"status would show {got['shown']!r}, not 'model/best.pt'")
    if verbose:
        print(f"         frozen best.pt -> {got['best']}")
    return failures


def check_display_path_other_drive(verbose: bool) -> list[str]:
    """relpath raises across drives on Windows; display_path must not."""
    import app_paths

    if sys.platform != "win32":
        return []
    drive = os.path.splitdrive(app_paths.PROJECT_ROOT)[0].upper()
    other = "Z:" if drive != "Z:" else "Y:"
    path = other + "\\models\\best.pt"
    try:
        shown = app_paths.display_path(path)
    except Exception as exc:  # pragma: no cover - the bug this guards
        return [f"display_path raised {type(exc).__name__}: {exc}"]
    return [] if shown == path else [f"display_path({path!r}) -> {shown!r}"]


def check_origin_guard(verbose: bool) -> list[str]:
    """Camera auto-allow must match this app's exact origin only."""
    origin = shell.origin_for(53817)
    cases = [
        ("http://127.0.0.1:53817", True),
        ("http://127.0.0.1:53817/", True),
        ("http://127.0.0.1:53817/camera-view.html", True),
        ("http://127.0.0.1:5381/camera-view.html", False),     # prefix port
        ("http://127.0.0.1:538170/", False),                   # longer port
        ("http://127.0.0.1:53817.evil.example/", False),       # look-alike host
        ("http://localhost:53817/", False),                    # different origin string
        ("https://example.com/", False),
        ("", False),
        (None, False),
    ]
    failures = [
        f"is_own_origin({uri!r}) -> {not want}, expected {want}"
        for uri, want in cases
        if shell.is_own_origin(uri, origin) is not want
    ]
    if shell.is_own_origin("http://127.0.0.1:53817/", None):
        failures.append("allowed with no origin set (server not started yet)")
    if origin != "http://127.0.0.1:53817":
        failures.append(f"origin_for -> {origin!r}")
    return failures


def check_port_parsing(verbose: bool) -> list[str]:
    cases = {None: 0, "": 0, "5055": 5055, "abc": 0, "-1": 0, "70000": 0, " 6000 ": 6000}
    failures = []
    saved = os.environ.pop("AURA_DESKTOP_PORT", None)
    try:
        for raw, want in cases.items():
            if raw is None:
                os.environ.pop("AURA_DESKTOP_PORT", None)
            else:
                os.environ["AURA_DESKTOP_PORT"] = raw
            got = shell.requested_port()
            if got != want:
                failures.append(f"AURA_DESKTOP_PORT={raw!r} -> {got}, expected {want}")
    finally:
        os.environ.pop("AURA_DESKTOP_PORT", None)
        if saved is not None:
            os.environ["AURA_DESKTOP_PORT"] = saved
    return failures


def check_no_runtime_installs(verbose: bool) -> list[str]:
    """Ultralytics must never pip-install or go online inside the app.

    In a frozen app, Ultralytics' auto-install runs `sys.executable -m pip`,
    and sys.executable is AURA.exe, so a stray check_requirements() would
    relaunch the app instead of installing anything. The first CPU build
    caught it installing `lap` into the build venv this way.
    """
    env = shell.backend_environment(UI_DIR)
    failures = []
    if env.get("YOLO_AUTOINSTALL") != "false":
        failures.append(f"YOLO_AUTOINSTALL={env.get('YOLO_AUTOINSTALL')!r}, expected 'false'")
    if env.get("YOLO_OFFLINE") != "true":
        failures.append(f"YOLO_OFFLINE={env.get('YOLO_OFFLINE')!r}, expected 'true'")
    if failures:
        return failures

    code = f"""
import json, sys
sys.path.insert(0, {BACKEND_DIR!r})
import ultralytics.utils as u
print(json.dumps({{"autoinstall": u.AUTOINSTALL, "online": bool(u.is_online())}}))
"""
    got = run_child(code, env)
    if got["autoinstall"] is not False:
        failures.append("ultralytics AUTOINSTALL still on under the app's environment")
    if got["online"] is not False:
        failures.append("ultralytics still reports itself online under YOLO_OFFLINE")
    return failures


def check_desktop_page_set(verbose: bool) -> list[str]:
    """desktop/ui holds the three app pages only, and nothing links elsewhere."""
    failures = []
    pages = {f for f in os.listdir(UI_DIR) if f.endswith(".html")}
    if pages != APP_PAGES:
        failures.append(f"desktop/ui pages {sorted(pages)} != {sorted(APP_PAGES)}")

    nav = open(os.path.join(UI_DIR, "nav.js"), encoding="utf-8").read()
    nav_hrefs = set(re.findall(r'href:\s*"([^"]+)"', nav))
    if nav_hrefs != APP_PAGES:
        failures.append(f"nav.js lists {sorted(nav_hrefs)}")

    for name in sorted(pages) + ["nav.js"]:
        text = open(os.path.join(UI_DIR, name), encoding="utf-8").read()
        for dropped in DROPPED_PAGES:
            if re.search(r'href=["\']?' + re.escape(dropped), text):
                failures.append(f"{name} links to {dropped}")
        if "python backend/app.py" in text.replace("`", "") and name != "nav.js":
            failures.append(f"{name} still tells the user to run python backend/app.py")
    return failures


def check_serving_modes(verbose: bool) -> list[str]:
    """Desktop env serves the app pages; no env serves the website as before."""
    code = """
import json, sys
sys.path.insert(0, %r)
import app
c = app.app.test_client()
paths = ["/", "/dashboard.html", "/camera-view.html", "/color-recommendation.html",
         "/index.html", "/about.html", "/results.html", "/nav.js", "/style.css"]
res = {}
for p in paths:
    r = c.get(p)
    res[p] = [r.status_code, r.get_data(as_text=True)[:4000] if r.status_code == 200 else ""]
    r.close()
print(json.dumps({"host": app.HOST, "web": app.WEBSITE_DIR, "res": res}))
""" % BACKEND_DIR

    failures = []
    desktop = run_child(code, shell.backend_environment(UI_DIR))
    if not same(desktop["web"], UI_DIR):
        failures.append(f"desktop WEBSITE_DIR {desktop['web']!r}")
    if desktop["host"] != "127.0.0.1":
        failures.append(f"desktop HOST {desktop['host']!r}, expected 127.0.0.1")
    res = desktop["res"]
    for page in APP_PAGES:
        if res["/" + page][0] != 200:
            failures.append(f"desktop /{page} -> {res['/' + page][0]}")
    for page in DROPPED_PAGES:
        if res["/" + page][0] != 404:
            failures.append(f"desktop /{page} -> {res['/' + page][0]}, expected 404")
    if res["/"][0] != 200 or "<title>Dashboard" not in res["/"][1]:
        failures.append("desktop / does not land on the Dashboard")
    if "DESKTOP APP COPY" not in res["/nav.js"][1]:
        failures.append("desktop /nav.js is not the app's copy")

    website = run_child(code)
    if website["host"] != "0.0.0.0":
        failures.append(f"website HOST changed to {website['host']!r}")
    wres = website["res"]
    for page in APP_PAGES | DROPPED_PAGES:
        if wres["/" + page][0] != 200:
            failures.append(f"website /{page} -> {wres['/' + page][0]} (website/ must be unchanged)")
    if wres["/"][1] != wres["/index.html"][1]:
        failures.append("website / no longer serves index.html")
    if verbose:
        print(f"         desktop serves {desktop['web']}")
    return failures


def check_server_lifecycle(verbose: bool) -> list[str]:
    """127.0.0.1 only, a free port, and shutdown actually stops it."""
    from flask import Flask
    from werkzeug.serving import make_server

    tiny = Flask("lifecycle")

    @tiny.route("/ping")
    def ping():
        return "pong"

    failures = []
    server = make_server(shell.HOST, 0, tiny, threaded=True)
    port = server.port
    if port == 0:
        failures.append("port 0 was not replaced by a real port")
    if server.server_address[0] != "127.0.0.1":
        failures.append(f"bound to {server.server_address[0]}, not 127.0.0.1")

    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        body = urllib.request.urlopen(f"{shell.origin_for(port)}/ping", timeout=5).read()
        if body != b"pong":
            failures.append(f"unexpected body {body!r}")
    except Exception as exc:
        failures.append(f"server not reachable: {exc}")

    start = time.perf_counter()
    stopper = threading.Thread(target=server.shutdown, daemon=True)
    stopper.start()
    stopper.join(5)
    server.server_close()
    worker.join(5)
    if worker.is_alive():
        failures.append("serve_forever thread still alive after shutdown")
    try:
        urllib.request.urlopen(f"{shell.origin_for(port)}/ping", timeout=2)
        failures.append("server still answering after shutdown")
    except (urllib.error.URLError, ConnectionError, OSError):
        pass
    if verbose:
        print(f"         port {port}, shutdown in {(time.perf_counter() - start) * 1000:.0f} ms")
    return failures


def check_camera_close_bounded(verbose: bool) -> list[str]:
    """Camera.close() returns promptly even while another thread holds the lock."""
    import app

    failures = []
    cam = app.Camera(index=99)
    if cam.close(timeout=0.5) is not True:
        failures.append("close() on an idle camera did not return True")

    held = threading.Event()
    release = threading.Event()

    def hog():
        with cam._lock:
            held.set()
            release.wait(5)

    t = threading.Thread(target=hog, daemon=True)
    t.start()
    held.wait(2)
    start = time.perf_counter()
    result = cam.close(timeout=0.3)
    elapsed = time.perf_counter() - start
    release.set()
    t.join(2)
    if result is not False:
        failures.append("close() reported success while the lock was held")
    if elapsed > 1.0:
        failures.append(f"close() blocked {elapsed:.2f}s with a 0.3s timeout")
    return failures


CHECKS = [
    ("paths from source are unchanged", check_source_paths),
    ("paths in a PyInstaller build (simulated)", check_frozen_paths),
    ("display_path survives another drive", check_display_path_other_drive),
    ("camera auto-allow matches own origin only", check_origin_guard),
    ("AURA_DESKTOP_PORT parsing", check_port_parsing),
    ("app disables Ultralytics auto-install / online checks", check_no_runtime_installs),
    ("desktop/ui holds only the three app pages", check_desktop_page_set),
    ("desktop serves app pages; website mode unchanged", check_serving_modes),
    ("server: 127.0.0.1, free port, clean shutdown", check_server_lifecycle),
    ("Camera.close() cannot hang shutdown", check_camera_close_bounded),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Tests for the AURA desktop app shell")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print what each check exercised")
    args = parser.parse_args()

    print(f"desktop shell — ui {os.path.relpath(UI_DIR, PROJECT_ROOT)}\n")

    total_failures = 0
    for name, check in CHECKS:
        try:
            failures = check(args.verbose)
        except Exception as exc:
            failures = [f"crashed: {type(exc).__name__}: {exc}"]
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
