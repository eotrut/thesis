---
tags: [hardware, build, log]
created: 2026-03-29
updated: 2026-08-03
status: active
---
# 🔧 Assembly Log

> [!info] One entry per build session. Photograph everything (evidence for Chapter 4 + defense). Related: [[⚙️ Mechanical Design]] · [[🔌 Electronics & Wiring]] · [[🧪 Calibration & Testing Log]].

## 2026-03-29 — Planning Phase Complete
**What was done:** Concept paper submitted. Finalized architecture (IPO), hardware stack, and budget. Locked key decisions: dual-X NEMA 23, TB6600 drivers, Arduino Mega + RAMPS, laptop-side AI.
**Issues encountered:** None (design phase).
**How resolved:** —
**Next steps:** Finalize BOM suppliers; place procurement wave 1 (frame, motors, drivers, controller) in May.
**Photos/evidence:** Concept paper PDF in project files.

---

## 2026-07-30 — All Parts Procured; Build Phase Starting
**What was done:** All components for the gantry system have been purchased. Procurement is complete. Team is transitioning from planning/AI work into physical build.
**Issues encountered:** Open design decision — **V-slot rail configuration for the bottom axis**: debating whether to use **two V-slot rails** (one on each side of the bottom) or **one rail** (center). Trade-offs under consideration:
- **Two rails (dual bottom):** More stable, better load distribution, reduces racking risk on the bottom axis — but adds cost and complexity in alignment.
- **One rail (single bottom):** Simpler, cheaper, less alignment work — but higher racking risk if the load isn't centered.
**How resolved:** Decision pending — to be confirmed before frame assembly begins.
**Next steps:**
  - Resolve single vs. dual bottom V-slot rail question (see [[⚙️ Mechanical Design]])
  - Begin gantry frame assembly once rail config is locked
  - Document frame assembly with photos for Chapter 4 evidence
**Photos/evidence:** Pending — will photograph build sessions.

---

## 2026-08-03 — First Power-On + Motor Test
**What was done:** Standalone bench test of one NEMA23 + TB6600 + Arduino Mega 2560 on a breadboard. Established and verified full signal chain: Arduino → TB6600 → NEMA23. Motor confirmed spinning smoothly in both directions under software control.

**Hardware used:** Arduino Mega 2560, TB6600 stepper driver, NEMA23 motor (with timing pulley installed), 24V 30A PSU, breadboard.

**Wiring (TB6600 signal side → Arduino):**
- PUL− / DIR− / ENA− → shared GND rail → Arduino GND
- PUL+ → Arduino pin 3
- DIR+ → Arduino pin 4
- ENA+ → Arduino pin 5

**Driver settings:** Current = 3A (matched to NEMA23 spec). Microstepping = all DIP switches OFF → 32 microsteps / 6400 pulses per revolution.

**Issues encountered:**
1. Motor did nothing on first power-on despite correct PUL/DIR wiring.
2. Root cause: TB6600 ENA pin is **active-low** on this unit. Tying ENA+ to 5V was actively disabling the driver, not enabling it.

**How resolved:**
1. Disconnected ENA entirely — motor began spinning immediately (TB6600 defaults to enabled when ENA is floating).
2. Rewired ENA+ to Arduino pin 5 for software control. Code pulls ENA LOW to enable, HIGH to disable (de-energizes coils during idle to reduce heat).

**Test code behavior:** Motor spins 6400 steps CW → 1s pause → 6400 steps CCW → 1s pause → de-energizes for 2s → repeats. Running smoothly.

**Next steps:**
- Test second NEMA23 + TB6600 unit the same way
- Integrate both motors into RAMPS board once gantry frame is assembled
- Verify direction convention matches intended X/Y axis orientation on the wall

**Photos/evidence:** Pending.

---

## [Date] — Frame Assembly (X-axis)
**What was done:**
**Issues encountered:**
**How resolved:**
**Next steps:**
**Photos/evidence:**

---

## [Date] — Frame Assembly (Y-axis + carriage)
**What was done:**
**Issues encountered:**
**How resolved:**
**Next steps:**
**Photos/evidence:**

---

## [Date] — Wiring (motors → drivers → RAMPS)
**What was done:**
**Issues encountered:**
**How resolved:**
**Next steps:**
**Photos/evidence:**

---

## [Date] — Spray System Mounting
**What was done:**
**Issues encountered:**
**How resolved:**
**Next steps:**
**Photos/evidence:**
