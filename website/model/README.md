# AURA — Trained Model Weights

Drop the fine-tuned YOLOv8 instance-segmentation checkpoint here as:

```
website/model/best.pt
```

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

## Git

`best.pt` is git-ignored (model checkpoints are tens of MB). Keep your own copy
of each Kaggle run's weights alongside its metrics for Chapter 4.
