# AURA desktop app

The AURA desktop app for Windows. It runs the same Flask backend as the website (`backend/app.py`) inside the app's own process and shows the pages in a native window instead of a browser tab. This is not a rewrite: the segmentation, colour and toolpath code is shared with the website.

The app has three pages: **Dashboard**, **Color Recommendation** and **Camera View**. Home, About and Results stay on the website only (panel recommendation, Oct 2026).

## What's in this folder

| Path | What it is |
|---|---|
| `aura_desktop.py` | Entry point. Opens the window, starts the backend on `127.0.0.1` at a free port, and shuts everything down when the window closes. |
| `ui/` | The app's own copies of `dashboard.html`, `color-recommendation.html`, `camera-view.html`, `nav.js` and `style.css`, forked from `website/` on 2026-10-14. The app is restyled here; `website/` is left as it is. |
| `requirements-desktop.txt` | Extra packages on top of `backend/requirements.txt` (pywebview). |

Paths that differ between "from source" and "packaged as AURA.exe" are resolved in one place, `backend/app_paths.py`.

## Run from source

From the project root with the venv active:

```powershell
pip install -r desktop/requirements-desktop.txt
python desktop/aura_desktop.py
```

A "Starting AURA…" screen shows while PyTorch and the model load (about 5–10 s on the RTX 3050 laptop), then the Dashboard opens. The **Inference Device** card shows whether the model is running on CUDA or the CPU.

## Glossary

- **pywebview**: a Python library that opens a desktop window with a web page inside. On Windows it uses **WebView2**.
- **WebView2**: Microsoft Edge's browser engine, packaged so apps can embed it. It is built into Windows 10 (21H2 and later) and Windows 11, so nothing extra needs installing.
- **127.0.0.1**: this computer only. The app's server cannot be reached from the network. `python backend/app.py` binds `0.0.0.0`, which means "every network interface".
- **Free port**: the app asks Windows for any unused port number, so it never collides with the website backend on 5000 or with a second copy of AURA.

## Camera

Camera View offers two sources:

- **Laptop / USB camera (picked in the app)**: the window opens the camera itself, the way a browser would. Use this one on a laptop with only a built-in webcam. The app grants camera permission to its own pages automatically, so there's no Edge prompt.
- **Backend camera (opened by the AURA engine)**: OpenCV opens camera index 0 (set `AURA_CAMERA_INDEX` to change it).

If no camera shows up, check **Windows Settings › Privacy & security › Camera**, which needs "Let desktop apps access your camera" turned on, and close Zoom, Teams or the Camera app.

## Logs

`%LOCALAPPDATA%\AURA\logs\aura-desktop.log`, with the previous run kept as `aura-desktop.log.1`. The startup lines say which device inference runs on, for example:

```
aura.desktop: Inference device: CUDA — cuda:0 (NVIDIA GeForce RTX 3050 Laptop GPU)
```

## Options (environment variables)

| Variable | Effect |
|---|---|
| `AURA_DEVICE=cpu` | Force CPU inference even with a GPU present. |
| `AURA_DESKTOP_PORT=5055` | Use a fixed port instead of a free one. |
| `AURA_DESKTOP_DEBUG=1` | Enable right-click › Inspect (Edge DevTools) in the window. |

All the backend's own `AURA_*` variables (see `backend/README.md`) still apply.

## Tests

```powershell
python backend/tools/test_desktop_shell.py
```

This covers path resolution (from source and as a simulated packaged build), the three-page set, `127.0.0.1` binding, clean server shutdown, and the camera-permission origin check. It needs no weights, GPU, webcam or window.
