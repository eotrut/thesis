---
tags: [ai, serial, firmware, protocol]
created: 2026-03-29
updated: 2026-08-04
status: active
---
# 🖥️ Serial Communication Protocol

> [!info] Related
> [[🏗️ System Architecture Overview]] · [[🔌 Electronics & Wiring]] · Code: [[serial_command_template.py]] · [[arduino_motion_handler.ino]]

> [!warning] Protocol changed to a custom command set (2026-08-03)
> With RAMPS and Marlin out of the build ([[🔌 Electronics & Wiring]]), there is no mature firmware to inherit a G-code parser from — the Arduino runs a **custom sketch**, so it accepts a **custom command set**, not G-code. The GRBL-compatible table is kept below as the superseded design.

> [!bug] Open gap — the toolpath generator still emits G-code
> `backend/toolpath_generator.py` (`events_to_gcode()`) currently produces `G0`/`G1`/`M3`/`M5` lines, which this Arduino sketch will **not** parse. Nothing is broken today because nothing sends them yet, but the two ends do not meet. Two ways to close it, **not yet decided**:
>
> 1. **Translate in `serial_ctrl.py`** — keep the G-code emitter (it is built, tested and committed) and convert to `MOVE`/`SPRAY` on the way out. Smallest change; keeps the G-code artefact, which is the more conventional thing to show a panel.
> 2. **Replace the emitter** — have the toolpath stage output the custom commands directly. Fewer moving parts, but throws away working, tested code and the recognisable G-code output.
>
> Decide before firmware work starts — it determines what the Arduino sketch has to parse. See [[📐 Path Planning & G-code Generation]].

## Link Parameters
- **Baud rate:** 115200 (8N1). High enough to stream moves without motion starvation.
- **Transport:** USB serial (Arduino Mega USB-B → laptop).

## Command Format — custom (current)
| Command | Meaning |
|---|---|
| `MOVE X{x} Y{y}` | Linear move to (x, y) in mm, absolute |
| `SPRAY ON` | Spray on (relay closed) |
| `SPRAY OFF` | Spray off |
| `HOME` | Home all axes |

Example line: `MOVE X120.00 Y85.50\n`

> [!note] Command set is provisional
> Feed rate has no representation yet — the G-code design carried it per-move as `F`. Whether speed becomes a `MOVE` parameter, a separate `FEED` command, or a firmware constant is open, and is part of the same decision as the gap above.

## Command Format (GRBL-compatible) — superseded 2026-08-03
Kept as record. This is what `events_to_gcode()` still emits.

| Command | Meaning |
|---|---|
| `G1 X{x} Y{y} F{feed}` | Linear move to (x, y) at feedrate |
| `G28` | Home all axes |
| `M3` | Spray ON (spindle-on mapping → relay) |
| `M5` | Spray OFF |
| `G4 P{ms}` | Dwell (pause) |

Example line: `G1 X120.0 Y85.5 F1500\n`

## Handshake Protocol
1. Python sends one line terminated with `\n`.
2. Arduino executes, then replies **`ok`** (or `error:{code}`).
3. Python **blocks** until `ok` or a timeout, then sends the next line.

This flow-control keeps the Arduino's buffer from overflowing and guarantees ordering.

## Python Queue Implementation
- A **command queue** holds the command list.
- **Blocking send**: write line → wait for `ok` (with timeout, e.g., 5 s).
- On timeout: retry once, then abort with a logged error.
See [[serial_command_template.py]].

## Error Recovery
> [!warning] If Arduino doesn't respond
> - Timeout → **retry the last line** once.
> - Second failure → **halt streaming**, send `SPRAY OFF` for safety, surface an error to the operator.
> - Never blindly continue — a missed move desyncs paint from position (R-03).

## Spray-Timing Strategy (encoder-less)
AURA has no motion encoder, so spray fires by **coordinate-arrival trigger**: because Python waits for `ok` after each move, it *knows* the head has reached the target before sending `SPRAY ON`. For long strokes, embed the spray toggles **between** the moves that bound the painted segment. Avoid pure time-delay triggering — it drifts.

## Example Command Sequence — paint a single horizontal stripe
```
HOME                    ; home both axes
MOVE X20.00 Y50.00      ; move to stripe start (no spray)
SPRAY ON
MOVE X120.00 Y50.00     ; paint across
SPRAY OFF
MOVE X20.00 Y60.00      ; reposition for next row
```

The equivalent under the superseded G-code design, for comparison — this is what `events_to_gcode()` emits today:

```gcode
G28                     ; home
G1 X20 Y50 F2000        ; move to stripe start (no spray)
M3                      ; spray on
G1 X120 Y50 F1200       ; paint across at slower feed
M5                      ; spray off
G1 X20 Y60 F2000        ; reposition for next row
```

> [!warning] Dual-X is one axis to this protocol
> `MOVE X…` commands a single logical X position. The firmware fans that out to **both** X drivers ([[🔌 Electronics & Wiring]]); the protocol has no concept of two X motors and must not gain one, or the host could desync them and cause the racking R-02 exists to prevent.
