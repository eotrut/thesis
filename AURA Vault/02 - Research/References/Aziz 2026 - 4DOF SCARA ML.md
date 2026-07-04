---
tags: [reference, control, ml]
authors: Aziz et al.
year: 2026
doi: n/a
---
# 4-DOF SCARA: Kinematic Modeling + Machine Learning
## Citation
Aziz, A., et al. (2026). *4-DOF SCARA robot kinematic modeling with machine learning (SVM, Random Forest).* (As cited in AURA concept paper, 2026.)
## Core Argument
Classical kinematic modeling of a SCARA arm can be augmented with machine-learning models (SVM, Random Forest) to improve control accuracy and prediction.
## Methodology
Derived SCARA forward/inverse kinematics and trained SVM and Random Forest models to refine positioning/behavior predictions.
## Key Findings
- ML augmentation improves control accuracy over pure analytical models.
- Classical ML (SVM/RF) is sufficient — deep nets not always required.
- Kinematic + ML hybrid is practical.
## Limitations
- Focused on articulated SCARA arm, not Cartesian gantry.
- Control-only; no perception or painting task.
- ML gains are incremental, task-specific.
## Relevance to AURA
Shows that **modest ML can meaningfully improve robotic control**, supporting AURA's pragmatic (non-heavyweight) AI choices and calibration approach.
## AURA Builds On This By
Applying the *right-sized-AI* philosophy — lightweight segmentation and K-means color logic rather than heavy models — and treating calibration/steps-per-mm tuning as AURA's control-accuracy layer. See [[🧪 Calibration & Testing Log]].
