---
tags: [defense, panel, recommendations, action-items, prototype-defense]
created: 2026-10-04
status: confirmed by Kurt 2026-10-14 (after listening to the voice message)
---
# 🎯 Prototype Defense — Panel Recommendations (Oct 2026)

> [!info] Related
> [[🧭 Prototype Defense Readiness]] · [[🎯 Post-Defense Recommendations & Action Items]] (the earlier proposal-defense list) · [[🎨 Color Recommendation Module]] · [[🔌 Backend API & Web Integration]] · [[📋 Master Task Tracker]]

> [!success] Confirmed — 2026-10-14
> Written 2026-10-04 from what Kurt remembered of the defense. After listening to the recorded voice message, Kurt confirmed everything here is right; no corrections. Items marked **(my reading)** were interpretations; Kurt confirmed the note as a whole, so treat them as accepted unless he says otherwise.

## Outcome
Defense went well. **Hardware: panel wants nothing changed.** Changes are software-only.

## Software changes asked for

### 1. Remove the non-functional pages
Delete **Home** (`index.html`), **About** (`about.html`) and **Results** (`results.html`) and the matching entries in `website/nav.js`. Panel wants "just the features."
- **Kept:** Color Recommendation, Camera View.
- **Dashboard (`dashboard.html`) stays** — Kurt confirmed 2026-10-04.
- If the app becomes desktop software (item 2), the landing/navbar structure goes away anyway.

### 2. Website → desktop software
Panel suggested moving the whole thing off the browser into an installable/desktop application, "if we can get it to be a software instead."
- **Confirmed by Kurt 2026-10-04: required, not optional.**
- **Website stays in the repo** (Kurt's call, 2026-10-04). The desktop software is a new deliverable alongside it. **(my reading)** the page removals in item 1 apply to the software; whether the website folder itself also loses Home/About/Results is not decided.
- Current stack for reference: Flask backend (`backend/app.py`) serving static HTML/JS pages, opened in a browser.
- Approach options are for the brainstorm, not decided.

### 3. Color Recommendation — demographic-based recommendation with templates
Today: camera view scans the wall and recommends a palette from the image (plus the optional reference image and the 7-category "for whom" dropdown built 2026-08-08, which only *biases* the maths — see [[🎨 Color Recommendation Module]] § Reference Image + Demographic Category).
New ask: a recommendation driven by **demographic**, with **templates** so the user can see **what is popular for that demographic**.
- **(my reading)** this means preset palette/room templates per demographic group (e.g. child, teen, adult man/woman, elderly), browsable, in addition to the camera-scan result — not necessarily replacing it. Not yet confirmed.
- Existing building blocks: 7 categories already in `CATEGORY_BIAS`, and the demographic literature in [[📚 Literature Review Master]] Theme 7 (10 papers).
- **Caveat to carry into the brainstorm:** "popular" needs a source. The 10 papers give colour-*preference tendencies* by age/gender, not popularity rankings or sales data. Templates should be labelled by what the literature supports, not invented popularity numbers.

### 4. General UI improvements
Fonts and overall look judged weak. To be done as part of the software migration rather than polishing the website first.

### 5. Credit the licenses used
If the project becomes distributed software, the licenses of what it bundles must be credited (an Acknowledgements / Licenses screen + a `LICENSES`/`NOTICE` file).
- **(my reading) things to inventory:** Ultralytics YOLOv8 (the package is AGPL-3.0 as far as I know — the one that matters most for distribution), MobileSAM, PyTorch, OpenCV, Flask, colour-science, the Roboflow training dataset's own license, and any fonts chosen in the UI redo.
- **Licenses above are from my recollection, not yet checked against each project.** Verify each before writing the credits.

## Open questions
- [x] Dashboard kept or cut? — **kept** (2026-10-04)
- [x] Is "make it software" required? — **yes, required** (2026-10-04)
- [x] Does the website folder also lose Home/About/Results? — **leave `website/` untouched for now** (2026-10-04); revisit at the brainstorm once we know whether the software reuses those pages' HTML.
- [x] Do templates replace the camera-scan recommendation or sit alongside it? — **alongside** (2026-10-14): demographic template browsing is a second way in; the camera-scan flow is unchanged.
- [ ] Anything in the voice message that differs from the above.

## Brainstorm decisions (2026-10-14)
- **Desktop software approach:** wrap the existing pages (Camera View, Color Recommendation, Dashboard) in an app window with the Python backend started behind it, packaged as a Windows `.exe`. Not a native rewrite.
- **Runs on other people's laptops, Windows only** (no Mac build).
- **GPU if available, CPU otherwise.** App detects an NVIDIA GPU at startup and falls back to CPU. Not CUDA-required.
- **Two packages from one codebase:** small CPU build to hand out, larger CUDA build for Kurt's RTX 3050 laptop. Rough size estimates (unmeasured): CPU ~1–1.3 GB unpacked / ~400–600 MB zipped; GPU ~5–6 GB / ~2.5–3.5 GB. Leave out training-only libraries (e.g. `roboflow`) to trim.
- **Model files** `best.pt` and `mobile_sam.pt` are git-ignored and must be bundled by hand.
- **Expect** a Windows "unknown publisher" warning (unsigned `.exe`).
- **Template source:** research-supported, built from the 10 demographic colour-preference papers ([[📚 Literature Review Master]] Theme 7). Labelled "research-supported tendencies", not "popular"/best-seller claims, since the papers give preferences, not popularity rankings. Optional later: small evaluator survey to back it up.
- **Claude Code setup:** Opus 5.5, medium effort; high only when stuck (e.g. packaging).

### Color templates — decisions (2026-10-14)
- **Template = named palette (~5 colours) per demographic**, shown alongside the camera-scan flow (not replacing it).
- **Source of the palettes: research-supported**, built from the demographic colour-preference papers ([[📚 Literature Review Master]] Theme 7). UI label: "research-supported tendency", not "most popular" — the papers show preference tendencies, not popularity rankings.
- **Example photos: openly licensed only** (e.g. Unsplash, Pexels, Wikimedia Commons), each credited in the licenses screen. **No Pinterest images** — copyright, and Pinterest's terms (as far as I know) prohibit automated scraping.
- **Pinterest allowed as research input only:** Kurt browses / uses Pinterest Trends by hand to see which palettes recur per group and cites it as supporting evidence; nothing is copied into the app. (Whether Pinterest Trends can filter by age/gender is unverified — check before citing.)
- The existing **reference-image upload** already lets a user supply their own Pinterest-style picture.

### UI redo — decisions (2026-10-14)
- **Direction: warm / design-studio** (soft neutral tones, rounded cards, interior-design-app feel) — Kurt's choice.
- **Colour-accuracy caution:** keep the background a near-neutral warm off-white, not a strong tint, and show paint swatches/previews against a neutral patch, so the surroundings don't skew how the recommended colours look.
- **Fonts: free, open-licensed, bundled inside the app** (works offline; each font listed on the licenses screen). Specific fonts not picked yet.
- Done as part of the desktop migration, applied to Camera View, Color Recommendation and Dashboard.

## Not started
Nothing in this note has been implemented. No code or other vault notes were changed.

## Build log

### Stage 1: app shell running from source (2026-10-14)
**Status:** done and tested on Kurt's laptop. Not committed yet (waiting for Kurt's OK).

**What it is:** `python desktop/aura_desktop.py` opens an "AURA" window (pywebview on Edge WebView2). The Flask backend runs inside the same process on `127.0.0.1` at a port Windows picks, and the window shows the Dashboard. Closing the window stops the server, releases the webcam and ends the process.

**Changed / added**
- `desktop/aura_desktop.py` (new): launcher. Shows a "Starting AURA…" screen, then on a background thread imports the backend, loads the model, starts the server and opens the Dashboard. Logs to `%LOCALAPPDATA%\AURA\logs\aura-desktop.log` (previous run kept as `.log.1`). Auto-allows the camera for the app's own address only. Turns on downloads so "Download G-code" works. Hard-exits after the window closes so no python process is left behind.
- `desktop/ui/` (new): the app's own copies of `dashboard.html`, `color-recommendation.html`, `camera-view.html`, `nav.js` and `style.css`, copied from `website/` including Kurt's uncommitted browser-camera edits. App-only changes: the nav lists the three pages only; the API is always same-origin (no fallback to `localhost:5000`); error text says "close and reopen AURA" instead of `python backend/app.py`; camera source labels; the Dashboard **Inference Device** card now reads the device the model *actually* loaded on (it used to say "CUDA" whenever a GPU existed, even if the model was on the CPU).
- `backend/app_paths.py` (new): the one place that knows source layout vs. packaged layout. Packaged: pages come from the bundle (`sys._MEIPASS`), and weights from a `model\` folder next to `AURA.exe`.
- `backend/model_loader.py`, `backend/smart_select.py`: weights paths now come from `app_paths`. From source, nothing changes (`website/model/`).
- `backend/app.py`: `AURA_WEB_DIR` / `AURA_HOME_PAGE` env vars (defaults unchanged, so `python backend/app.py` still serves the whole website from `website/`); new `Camera.close()` with a bounded wait for shutdown.
- `desktop/requirements-desktop.txt`: `pywebview==6.2.1`, pinned exactly because the camera auto-permission wraps one pywebview internal.
- `backend/tools/test_desktop_shell.py`: 9 checks (paths from source and as a simulated packaged build, three-page set, website mode unchanged, 127.0.0.1 and free port, clean shutdown, camera origin guard, bounded camera close).
- `desktop/README.md`.
- `website/`: **not touched**.

**Verified (2026-10-14, RTX 3050 laptop)**
- Startup about 7 s to the Dashboard. Log: `Inference device: CUDA — cuda:0 (NVIDIA GeForce RTX 3050 Laptop GPU)`. Dashboard card: CUDA · 4 GB.
- Server listens on `127.0.0.1` only. `/index.html`, `/about.html` and `/results.html` return 404 in the app.
- Camera in the window: built-in **HP Wide Vision HD** and both EMEET USB cameras open at 1280×720 with no permission prompt. The live segmented feed works. "Backend camera" (OpenCV) also works.
- Close while streaming: exits in about 2.7 s, WebView2 child gone, port freed. Close during model load: exits in about 2.7 s, nothing left running.
- Tests: the new suite passes 9/9; `test_color_recommender`, `test_mask_correction` and `test_toolpath` still pass.

**Bug found and fixed during the stage:** the first Dashboard status poll timed out at startup because the startup device report probed the webcam at the same moment. The report now runs before the page opens.

**Known, deferred to later stages:** the app copies still load the Michroma font from Google Fonts (online), so offline it falls back to a system font. Bundled fonts come in Stage 4.

### Stage 2: Windows packages, CPU and CUDA (2026-10-14)
**Status:** both built and tested on Kurt's laptop. Not committed yet (waiting for Kurt's OK).

**Measured sizes** (including `best.pt` and `mobile_sam.pt`; the earlier estimates were unmeasured):

| | CPU build (to hand out) | CUDA build (RTX 3050 laptop) |
|---|---|---|
| Unpacked | **581 MB** (estimate was 1–1.3 GB) | **3.74 GB** (estimate was 5–6 GB) |
| Zipped | **243 MB** (estimate was 400–600 MB) | **2.33 GB** (estimate was 2.5–3.5 GB) |
| Build time | ~3.5 min | ~6 min |

**How to build:** `py -3.11 desktop/build.py cpu --zip` or `... gpu --zip`. The output goes to `desktop/dist/AURA-CPU/` (or `AURA-GPU/`) plus a zip; all of it is git-ignored. One PyInstaller recipe (`desktop/aura.spec`) serves both builds. The only difference is which torch the clean build venv holds (`2.5.1+cpu` or `2.5.1+cu121`). The output is a folder (`AURA.exe` + `_internal\`), not a single file, so nothing is unpacked to temp on every launch. The weights are copied into `model\` next to `AURA.exe`. Each build carries `README-FIRST.txt` (how to start it, the unknown-publisher warning, camera privacy settings) and `BUILD-INFO.txt` (exact package versions and the git commit).

**Left out:** roboflow, pandas, tensorboard and pyserial are never installed in the build venvs. polars is excluded from the bundle, as are ultralytics' tracking and "solutions" modules.

**Problem found and fixed:** on the first CPU build, PyInstaller's scan imported `ultralytics.trackers`. That module calls `check_requirements("lap")` on import, and Ultralytics' auto-install pip-installed `lap` into the build venv. Inside the packaged app the same call would run "pip" with `AURA.exe` as the Python, i.e. relaunch the app. Fixes:
- trackers and solutions are excluded from the bundle
- `YOLO_AUTOINSTALL=false` and `YOLO_OFFLINE=true` are set at build time and inside the app
- `lap` was removed from the venv
- a new test check guards this (`test_desktop_shell.py` is now 10/10).

**Tested (2026-10-14)**
- **CPU build, without Python:** copied to a folder outside the project and started with Python removed from `PATH` and no `PYTHON*` variables. Ready in 12 s and logged `Inference device: CPU`. Of the 210 DLLs loaded, the only one from outside the app folder and `C:\Windows` was Windows' own WebView2 runtime. All endpoints returned 200 (segment 0.21 s, recommend-colors, toolpath, MobileSAM smart select 1.7 s, wand). `/index.html` returned 404. The built-in HP camera worked with no permission prompt. Closing the window ended the process, freed the port and left no `AURA.exe` behind.
- **CUDA build, same test:** ready in 11 s on `cuda:0`, RTX 3050. Segment 0.16 s, MobileSAM 0.69 s, clean exit.
- **CUDA build with the GPU hidden** (`CUDA_VISIBLE_DEVICES=-1`): falls back to `Inference device: CPU` and runs.
- **Not yet tested:** a second laptop that has never had Python installed. Nothing above depended on this machine's Python, but that is the real-world check. Kurt's laptop also cannot show the SmartScreen warning, because locally built files don't carry the "downloaded from the internet" mark; recipients will see it.
