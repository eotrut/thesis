# AURA — Model Weights

Two checkpoints live here.

| File | What | Required? |
|---|---|---|
| `best.pt` | The fine-tuned YOLOv8 instance-segmentation model — the wall/non-paintable segmenter every page runs on | **Yes** for anything real |
| `mobile_sam.pt` | MobileSAM, used only by the mask editor's **smart select** (click a point, get a region) | Optional — falls back to a colour flood fill |

## `best.pt`

That is the exact path the backend looks for (`backend/model_loader.py`,
`DEFAULT_MODEL_PATH`). No other file name is picked up automatically.

## Where it comes from

Kaggle training run (Tesla T4) → `runs/segment/train*/weights/best.pt` → download
→ place here. See `AURA Vault/04 - AI & Code/🔮 Segmentation Model.md`.

## Requirements

- Must be a **segmentation** checkpoint (`yolov8*-seg`), not a detection one.
  A detection checkpoint loads, but produces boxes instead of pixel masks and
  the API reports `masks_available: false`.
- Class names should include something matching `wall` / `paintable` / `surface`.
  If none do, the backend treats the largest mask per frame as the wall and sets
  `wall_class_inferred: true` in the response.

## Overriding the path

```powershell
$env:AURA_MODEL_PATH = "C:\path\to\some-other-run.pt"
```

## Testing before best.pt exists

The COCO-pretrained baseline at the project root can stand in for wiring tests:

```powershell
$env:AURA_ALLOW_FALLBACK = "1"
python backend/app.py
```

This is for UI/plumbing checks only — those results are the Phase-1 zero-shot
baseline, not the fine-tuned AURA model, and must not be reported as such.

## `mobile_sam.pt` — smart select

Powers the **✨ Smart select** tool in the mask-correction editor: click a point
on the frame and MobileSAM returns the region under it, instead of brushing it in
by hand. 38 MB, and **no new Python dependency** — the ultralytics version AURA
already pins ships the SAM predictors.

```
website/model/mobile_sam.pt
```

Fetch it once, on a machine with internet:

```powershell
python -c "from ultralytics import SAM; SAM('mobile_sam.pt')"
# then move mobile_sam.pt into website/model/
```

**Get this onto the demo machine before defense day.** Without the file, smart
select silently becomes a colour flood fill — it still works, and the editor
labels which engine it is using, but the foundation-model demo is the part worth
showing. Same reasoning as the no-CDN decision: the venue's connectivity cannot
be assumed.

| Env var | Default | Notes |
|---|---|---|
| `AURA_SAM_MODEL` | `website/model/mobile_sam.pt` | Point at another SAM/SAM2 checkpoint |
| `AURA_SAM_IMGSZ` | `1024` | Drop to `512` if VRAM is tight — MobileSAM reserves ~2.3 GB of the RTX 3050's 4 GB alongside YOLOv8n |
| `AURA_SAM_DEVICE` | auto | `cpu` to keep the GPU entirely for YOLOv8 |
| `AURA_SMART_SELECT` | `1` | `0` forces the colour wand everywhere |

`/api/status` reports which engine is live under `smart_select`, and the startup
banner prints it.

## Git

Both checkpoints are git-ignored (`website/model/*.pt` — they are tens of MB).
Keep your own copy of each Kaggle run's weights alongside its metrics for
Chapter 4.
