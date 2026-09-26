---
tags: [reminder, pinned, metrics, evaluation]
created: 2026-08-16
status: pending
---
.# 📌 Read First — Retrain Metrics Warning

> [!danger] IMPORTANT — read before the ~1,000-image retrain evaluation
> Applies specifically to the mAP/IoU re-measurement after retraining. Keep this note until that evaluation actually happens — this is not a "remove when convenient" reminder.

## What to do (when that day comes)
1. **Do not use the brush or smart-select correction tools while running the test images through the model.**
2. Score mAP and IoU on the model's raw, uncorrected output only.
3. The correction tools are fine to use again immediately after — this restriction only applies to the scoring run itself.

## Why
- mAP and IoU are supposed to measure how good the *model* is, not how good the operator is at clicking corrections.
- If the brush/smart-select is active during that measurement, the score partly reflects the human fixing the model's mistakes, not the model's own output — so the retrain's real effect can't be judged.
- Already documented in [[🔮 Segmentation Model]] → "For Chapter 4" note. This pinned note exists because Kurt asked for a standing reminder since it's easy to forget mid-testing, same pattern as [[📌 Read First - Samples Capture Reminder]].

## Status
**Not yet relevant** — the retrain hasn't happened. Claude: surface this if/when retrain-evaluation work comes up, until Kurt confirms it's no longer needed.
