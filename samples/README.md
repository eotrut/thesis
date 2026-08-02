# Sample Images — Pipeline Test Fixtures

Raw photographs used to exercise the AURA pipeline end to end: segmentation →
coordinate mapping → toolpath → G-code.

```powershell
python backend/tools/test_toolpath.py                    # picks the first image here
python backend/tools/test_toolpath.py samples/wall_02.jpg
```

The toolpath test script looks in this directory first and only falls back to
`website/assets/` if it is empty.

## What belongs here

Ordinary photographs of walls, straight off the camera. Nothing else.

| Not this | Why |
|---|---|
| `website/assets/test_result_*.jpg` | Already-annotated segmentation **exports** — flat colour fills, not photographs. Running the model on them tests it against its own output. |
| Roboflow training images | See the hold-out rule below. |
| Screenshots, renders, diagrams | Site content, belongs in `website/assets/`. |

> **Why this directory exists at all.** These used to be the same folder.
> `website/assets/` is the site's demo gallery, and because it was the only
> image directory in the repo, its gallery exports quietly became the pipeline's
> test inputs. Every coverage figure measured before 2026-08-03 was measured
> against an annotated export rather than a photograph.

## ⚠️ Hold these out of the training set

Do **not** upload these to Roboflow, and do not copy training images in here.

If the same photographs train the model and validate the pipeline, the reported
IoU and confidence are measuring memorisation, and a panel is entitled to say
so. Shoot this set deliberately separately from the ~100–200 custom photos in
the Master Task Tracker, and record in the vault that they were held out.

## Naming

Flat directory, descriptive prefix:

```
wall_01_plain.jpg           plain wall, no obstacles
wall_02_window.jpg          named by the obstacle that matters
wall_03_glare.jpg           named by the condition being tested
calib_01_0deg.jpg           corner-marker shot, camera angle off-normal
calib_02_15deg.jpg
```

Keep files under ~2 MB. These are committed to git — resize before adding if the
camera writes 8 MP JPEGs.

## Still needed

Roughly 8–12 photographs closes every current gap, in priority order:

- [ ] **A wall with 4 measured corner markers** — the highest-value shot. It is
      the only thing blocking §1b of the vault's `🧪 Calibration & Testing Log`:
      real homography validation with real millimetre error, obtainable
      **before the gantry is built**. Tape crosses and a tape measure is the
      entire setup. Shoot the same wall at ~0°, ~15° and ~30° off normal; the
      homography should hold across all three.
- [ ] **A wall wider than the 4.5 ft X rail (1371.6 mm)** — makes multi-position
      envelope clipping a real test instead of one faked by shrinking
      `AURA_TRAVEL_X_MM`.
- [ ] **Obstacles that are not doors** — window, outlet, switch plate, skirting.
      Obstacle subtraction is a load-bearing claim and is currently evidenced by
      one door and two switch plates.
- [ ] **Hard lighting** — glare, a shadow gradient across the wall. This is where
      segmentation degrades, and degraded masks are what the planner must
      survive.

## Corner-marker measurements

A calibration photo is useless without the real positions of its markers. Record
them here as they are shot, in **top-left, top-right, bottom-right, bottom-left**
order — the order the Toolpath tab and `/api/toolpath` both expect.

| File | Marker mm (TL, TR, BR, BL) | Camera angle | Measured by | Date | Notes |
|---|---|---|---|---|---|
| _(none yet)_ | | | | | |

Once the gantry exists these should be the corners of its **reachable envelope**
(X 1371.6 mm, Y 2743.2 mm, less the homing margin) so the plan lands in the
machine's own coordinate frame — see `📐 Path Planning & G-code Generation`
§ Envelope Clipping.
