---
tags: [reference, mechanical]
authors: Kumtole et al.
year: 2022
doi: n/a
---
# Automatic Wall Painting Robot with XY Motion + Sensors

> [!note] Correction (2026-07-18)
> The author surname is **Kumtole**, not "Kumote" — corrected during the full reference audit of the concept paper. The last author's surname is **Sayyad Liyakat**, not "Liyakaf." This note's filename in the vault still reads "Kumote 2022..." from before the correction; consider renaming the file to "Kumtole 2022 - Auto Wall Painting Robot.md" next time you're in Obsidian (the sync tooling can't delete/rename the old file remotely).

## Citation
Kumtole, S., et al. (2022). *Automatic wall painting robot.* (As cited in AURA concept paper, 2026.)
## Core Argument
A wall-painting robot using an XY motion stage with sensor feedback can automate painting of flat walls, reducing manual labor.
## Methodology
Built an XY-motion painting platform with sensors for wall detection/positioning; executed programmed painting motions.
## Key Findings
- XY motion is adequate for flat-wall coverage.
- Sensor feedback aids positioning and boundary detection.
- Automation reduces labor and improves consistency vs manual painting.
## Limitations
- Motion is pre-programmed; no learned perception of design/regions.
- No AI color reasoning.
- Limited to simple coverage tasks.
## Relevance to AURA
Direct mechanical precedent: confirms the XY-gantry approach AURA adopts for flat walls and the labor-reduction motivation.
## AURA Builds On This By
Adding a **deep-learning perception layer and AI color recommendation** on top of the proven XY mechanics, so AURA decides *where* and *what color* rather than replaying fixed motions. See [[⚙️ Mechanical Design]].
