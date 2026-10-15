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

## Build the Windows app (AURA.exe)

```powershell
py -3.11 desktop/build.py cpu --zip     # small build to hand out
py -3.11 desktop/build.py gpu --zip     # CUDA build for the RTX 3050 laptop
```

Output goes to `desktop/dist/AURA-CPU/` (or `AURA-GPU/`) plus a `.zip` of it. Both folders are git-ignored. The first build of each flavour downloads torch into a clean build venv under `desktop/build/` (also git-ignored). Add `--skip-install` to reuse that venv on later builds.

| | CPU build | CUDA build |
|---|---|---|
| Who it's for | anyone, any Windows laptop | Kurt's RTX 3050 laptop |
| torch | 2.5.1+cpu | 2.5.1+cu121 |
| Unpacked size | **581 MB** | **3.74 GB** |
| Zipped size | **243 MB** | **2.33 GB** |
| Build time | ~3.5 min | ~6 min |

These sizes were measured on 2026-10-14 and include `best.pt` and `mobile_sam.pt`. The CUDA build is bigger because PyTorch's CUDA wheel carries NVIDIA's GPU libraries (cuDNN, cuBLAS and others). On a laptop without an NVIDIA GPU it still runs, on the CPU.

How the build is put together:
- **One recipe, two packages.** `aura.spec` is the PyInstaller recipe for both. The only difference is which torch the build venv has, so the code is identical.
- **Folder, not single file.** The output is `AURA.exe` plus an `_internal\` folder (PyInstaller "onedir" mode). A single-file exe would unpack hundreds of MB to a temp folder on every launch.
- **Weights sit next to the exe.** `build.py` copies `website/model/best.pt` and `mobile_sam.pt` into `model\` beside `AURA.exe`, where they can be swapped without rebuilding. They are git-ignored, so the build stops with a message if they are missing.
- **Training-only libraries are left out.** roboflow, pandas, tensorboard and pyserial are never installed in the build venvs. ultralytics' tracking and dashboard modules are excluded from the bundle.
- **No installs or online checks at runtime.** The app turns off Ultralytics' auto-install and online checks (`YOLO_AUTOINSTALL=false`, `YOLO_OFFLINE=true`). On the first build, ultralytics' tracker module pip-installed a package into the build venv during analysis. Inside the packaged app that same call would relaunch `AURA.exe`.
- **Exact versions are recorded.** `BUILD-INFO.txt` in each build lists every package version and the git commit it was built from.

### "Windows protected your PC" (unknown publisher)

`AURA.exe` is not code-signed. A signing certificate costs money and has to be tied to a verified publisher. So the first time someone runs a copy downloaded from the internet or a chat app, Windows SmartScreen shows **"Windows protected your PC… Unknown publisher"**. This is expected for an unsigned student project. Click **More info → Run anyway**. Some antivirus programs also scan a large unsigned app slowly on its first start. `README-FIRST.txt`, shipped inside each build, tells recipients the same thing.

### Testing the CPU build without Python

To test the build the way it will run elsewhere: copy `AURA-CPU` to a folder outside the project, then start `AURA.exe` with Python removed from `PATH` and no `PYTHON*` variables set. While it runs, list the DLLs the process has loaded. Everything should come from the app folder or `C:\Windows`, except Windows' own WebView2 runtime. This was done on 2026-10-14; see the vault build log. The real test is still a second laptop with no Python on it.

## Glossary

- **pywebview**: a Python library that opens a desktop window with a web page inside. On Windows it uses **WebView2**.
- **WebView2**: Microsoft Edge's browser engine, packaged so apps can embed it. It is built into Windows 10 (21H2 and later) and Windows 11, so nothing extra needs installing.
- **127.0.0.1**: this computer only. The app's server cannot be reached from the network. `python backend/app.py` binds `0.0.0.0`, which means "every network interface".
- **Free port**: the app asks Windows for any unused port number, so it never collides with the website backend on 5000 or with a second copy of AURA.
- **PyInstaller**: a tool that packs a Python program, the Python interpreter and every library it uses into a folder with an `.exe`, so the target PC needs no Python.
- **venv (virtual environment)**: a private, self-contained Python install with only the packages you put in it. The builds each use their own clean venv, so nothing from the development venv leaks into the app.
- **Hook**: a small recipe PyInstaller uses for a specific library, telling it which hidden files (DLLs, data) that library needs at runtime.
- **CUDA**: NVIDIA's system for running computations on the graphics card. "CPU build" means torch without CUDA; "CUDA build" means torch with NVIDIA's GPU libraries included.

## Look and fonts

The app uses a warm, light "design-studio" theme: a near-neutral warm off-white background, white rounded cards and a terracotta accent. The background is kept close to neutral, and paint swatches and photos sit on white or neutral-grey patches, so the surroundings don't change how a paint colour looks. The theme colours are variables at the top of `ui/style.css`. The mask and toolpath colours drawn over camera images (green, amber, red) are unchanged.

Fonts are bundled in `ui/assets/fonts/` and loaded locally, so the app needs no internet connection:

- **Fraunces** (headings), by the Fraunces Project Authors (Undercase Type), SIL Open Font License 1.1, https://github.com/undercasetype/Fraunces
- **DM Sans** (body text), by the DM Sans Project Authors (Colophon Foundry, for Google), SIL Open Font License 1.1, https://github.com/googlefonts/dm-fonts

The `.woff2` files are the Latin and Latin Extended subsets from the Fontsource 5.3.0 variable packages (`@fontsource-variable/fraunces`, `@fontsource-variable/dm-sans` on npm), which repackage the Google Fonts builds. The licence texts ship beside them (`OFL-Fraunces.txt`, `OFL-DMSans.txt`).

## Licenses screen and LICENSES.txt

The app's **Licenses** page (in the nav bar) credits everything bundled: the main components, the fonts, the training data and the 14 template photos. It also explains what Ultralytics' AGPL-3.0 licence requires and where to get the source. The data lives in `backend/credits.py` and is served by `GET /api/credits`. The photo credits come straight from `backend/color_templates.py`, so they cannot drift apart.

Each build also gets, next to `AURA.exe`:

- **`LICENSES.txt`**: the same credits, plus every Python package that actually shipped, with its version and the licence its own metadata declares.
- **`licenses\`**: each shipped package's own licence and notice files, the Python runtime's licence, and the two font licences.

`desktop/write_licenses.py` produces both, and `build.py` runs it with the build venv's Python. "Actually shipped" comes from PyInstaller's own inventories of what it packed (`PYZ-00.toc` and `COLLECT-00.toc` in `build/work-<flavour>/aura/`), so build-only tools such as pip are left out.

**AGPL-3.0, in short:** Ultralytics YOLOv8 is AGPL-3.0, so AURA's own software is released under AGPL-3.0 as well (`LICENSE` at the repo root; each build ships it as `LICENSE.txt`). Anyone who receives AURA must be able to get the complete source for that exact version. That source is the public repository, and `BUILD-INFO.txt` names the commit.

`python backend/tools/test_credits.py` checks that every bundled component, font and photo is credited. It also re-checks each stated licence against the installed package's metadata and runs the build writer against the last CPU build.

## Colour templates (Color Recommendation → Browse Templates)

This is a second way into colour recommendation, alongside the camera scan, which is unchanged. There is one template per "who is this room for?" category, the same seven categories as `CATEGORY_BIAS`. Each template has:

- **Five colours.** Each colour is defined in CIE LCh, cites the specific finding behind it and stays inside the recommender's paint band.
- **Two example photos.** They are openly licensed (CC0, public domain, CC BY or CC BY-SA), come from Wikimedia Commons and are credited. They are bundled in `ui/assets/templates/`, so they work offline.
- **Caveats and full APA sources.**

Every template is labelled **"Research-supported tendency"**, never "popular": the studies measured preference, not popularity. The direction of each colour comes from the papers; the exact shades are ours. Data lives in `backend/color_templates.py` and is served by `GET /api/color-templates`. **Scan my room for this group** switches to the scan flow with that category preselected.

`python backend/tools/test_color_templates.py` checks that each palette still follows its cited direction. Examples: the boys' palette is more saturated than the girls', the teen palette has no green, and the elderly palette has a cool bedroom option. It also checks the paint band, citations, photo licences and the wording.

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
python backend/tools/test_credits.py
```

The shell test covers path resolution (from source and as a simulated packaged build), the app's page set (the three tools plus Licenses), `127.0.0.1` binding, clean server shutdown, and the camera-permission origin check. It needs no weights, GPU, webcam or window.
