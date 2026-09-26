# AURA — Autonomous Unified Robotic Adaptive

An AI-based autonomous wall-painting robot integrating deep learning segmentation, color recommendation, and adaptive spray control.

Undergraduate thesis project · BS Computer Engineering · Holy Angel University, Angeles City, Pampanga, Philippines

AURA segments a wall with a fine-tuned YOLOv8 instance-segmentation model, recommends a
coherent paint palette from the room's own colours, and (in later phases) drives a gantry
to spray it. This repo holds the research vault, the trained-model backend, and the demo
website.

---

## Structure

| Path | What it is |
|---|---|
| `AURA Vault/` | Obsidian vault — research, design decisions, thesis chapters. The project's source of truth. |
| `backend/` | Flask API serving the YOLOv8 model (segmentation, colour recommendation, webcam stream) |
| `website/` | Demo site — dashboard, camera view, colour recommendation, results |
| `website/model/` | Where the trained `best.pt` (and optional `mobile_sam.pt`) go — **weights are not in the repo**, see below |
| `requirements.txt` | Exact `pip freeze` of the working environment |
| `create_vault.py` | Utility that scaffolds the Obsidian vault |

The manuscript (`.docx`) is git-ignored and not in this repo or the source zip — Word
binaries diff as opaque blobs, so the working copy is kept elsewhere. Ask for it separately
if you need it.

---

## Quick start

### 1. Requirements

- **Python 3.11**
- **PyTorch 2.5.1+cu121** and **Ultralytics 8.4.90** — pinned in
  [`requirements.txt`](requirements.txt) (and mirrored in
  [`backend/requirements.txt`](backend/requirements.txt), which also documents the
  version-mismatch risks below in more detail)
- NVIDIA GPU with driver **≥ 530** for CUDA 12.1 (optional — falls back to CPU)
- A webcam, for the live camera view (optional)

### 2. Environment

```bash
python -m venv venv
venv\Scripts\activate                 # Windows
# source venv/bin/activate            # macOS / Linux

pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu121
```

> **The `--extra-index-url` is required.** `torch`, `torchvision` and `torchaudio` are
> pinned to `+cu121` builds that do not exist on PyPI. Without it the install fails with
> `No matching distribution found for torch==2.5.1+cu121`.
>
> Installing plain `torch` from PyPI instead will "work" but gives you the CPU-only wheel —
> the server still runs, just roughly 10× slower. The startup banner prints
> `CUDA : NOT AVAILABLE` when that has happened.
>
> **Do not downgrade `numpy` below 2.x.** `opencv-python` 5.x and the pinned torch/torchvision
> wheels are built against the numpy 2 ABI; installing numpy 1.x breaks those imports at
> runtime rather than at install time, which makes it a confusing failure to debug.

### 3. Model weights — required, and not in this repo

Trained checkpoints are git-ignored (tens of MB). **A fresh clone cannot run inference
until you supply them.**

Download `best.pt` from the Kaggle training run and place it at:

```
website/model/best.pt
```

Without it the server still starts, but `/api/status` reports `model_loaded: false` with the
reason and every inference endpoint returns HTTP 503 — by design, so a missing file gives a
clear message instead of a crash.

`mobile_sam.pt` (same folder) is **optional** — it only powers the mask editor's smart-select
tool. Without it, smart select falls back to a colour flood fill and the app still works.
See [`website/model/README.md`](website/model/README.md) for where to get both files.

### 4. Run

```bash
python backend/app.py                  # binds 0.0.0.0 (all interfaces) by default
```

For a local demo, bind to loopback only — the API has no authentication:

```bash
AURA_HOST=127.0.0.1 python backend/app.py        # macOS / Linux
```

```powershell
$env:AURA_HOST = "127.0.0.1"; python backend/app.py   # Windows PowerShell
```

Then open **http://localhost:5000/index.html**. Full list of environment variables
(port, model path, confidence threshold, etc.): **[`backend/README.md`](backend/README.md)**.

A healthy start prints:

```
Model         : LOADED
                website\model\best.pt
Inference on  : cuda:0 (NVIDIA GeForce RTX 3050 Laptop GPU)
Task          : segment
Classes (2)   : non-paintable, wall
```

---

## API

Served on `localhost:5000`. CORS is open, so the HTML pages also work opened directly off
disk via `file://`.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/segment` | POST | Multipart image → base64 original + mask overlay + detections |
| `/api/recommend-colors` | POST | Multipart image → wall palette derived from the room's colours |
| `/api/stream` | GET | MJPEG webcam stream, `?overlay=pre\|during\|post` |
| `/api/status` | GET | Model / camera / CUDA state |
| `/api/capture` | GET | One segmented still from the webcam |

Full documentation, including request/response shapes and configuration environment
variables: **[`backend/README.md`](backend/README.md)**.

---

## Tests

These are standalone scripts, not a `pytest` suite — run them directly:

```bash
python backend/tools/test_mask_correction.py   # brush/smart-select correction invariants
python backend/tools/test_toolpath.py           # segmentation -> toolpath -> G-code pipeline
```

Both load the model directly (no server needed) and use photos from `samples/`, falling back
to the annotated `website/assets/test_result_*.jpg` exports (with a printed warning) only
when `samples/` is empty. Those exports have masks already burnt in, so scores measured
against them reflect the model against its own output, not fresh ground truth.

---

## Model performance

YOLOv8n-seg (COCO-pretrained, fine-tuned) · 300 images · 2 classes (`wall`, `non-paintable`)
· 100 epochs, early stopping patience 20 · 640×640 · trained on a Kaggle Tesla T4.

| Metric | Value |
|---|---|
| mAP@0.50 | 0.780 |
| mAP@0.50–0.95 | 0.548 |
| Precision | 0.845 |
| Recall | 0.729 |

**Preliminary** — the dataset is still expanding toward a 1,000-image target. Precision
exceeding recall means the model under-segments rather than over-segments, which is the
safer failure mode for a painting robot: a missed strip can be repainted, whereas spraying
a window cannot be undone.

Inference runs at roughly **100 ms/frame** on an RTX 3050 laptop GPU (~1.8 s one-off warm-up).

---

## Troubleshooting

**Status shows 80 COCO classes, or `yolov8n-seg.pt` instead of `best.pt`.**
An old server process is still holding port 5000 and answering requests. Kill it and restart:

```powershell
Get-CimInstance Win32_Process -Filter "Name like '%python%'" |
  Where-Object { $_.CommandLine -like '*backend/app.py*' } | Stop-Process -Force
```

**`torch.cuda.is_available()` is False.**
Either the CPU-only wheel got installed (see the index-URL note above) or the NVIDIA driver
is older than 530.

**Camera opens but the feed is black.**
Another application is holding the webcam — browsers in a video call are the usual culprit.
Windows hands the second consumer black frames rather than failing to open, so the camera
still reports as available. Close whatever else is using it.

**Colour recommendations look wrong on the test images.**
`website/assets/test_result_*.jpg` are already-annotated exports with masks burnt in, so the
recommender samples the annotation colour instead of the room. Use a plain room photo.

---

## Notes

- The backend is **localhost-only and unauthenticated** — intended for a local demo, not
  network exposure.
- The demo UI has **no CDN dependencies**; everything runs offline.
- Gantry motion control is not yet wired to the API — the dashboard's painting-progress card
  is inert.
