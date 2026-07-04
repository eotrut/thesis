---
tags: [reference, mechanical]
authors: Kumote et al.
year: 2022
doi: n/a
---
# Automatic Wall Painting Robot with XY Motion + Sensors
## Citation
Kumote, S., et al. (2022). *Automatic wall painting robot.* (As cited in AURA concept paper, 2026.)
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
