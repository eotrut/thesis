---
tags: [ai, serial, firmware, protocol]
created: 2026-03-29
status: active
---
# 🖥️ Serial Communication Protocol

> [!info] Related
> [[🏗️ System Architecture Overview]] · [[🔌 Electronics & Wiring]] · Code: [[serial_command_template.py]] · [[arduino_motion_handler.ino]]

## Link Parameters
- **Baud rate:** 115200 (8N1). High enough to stream G-code without motion starvation.
- **Transport:** USB serial (Arduino Mega USB-B → laptop).

## Command Format (GRBL-compatible)
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
- A **command queue** holds the G-code list.
- **Blocking send**: write line → wait for `ok` (with timeout, e.g., 5 s).
- On timeout: retry once, then abort with a logged error.
See [[serial_command_template.py]].

## Error Recovery
> [!warning] If Arduino doesn't respond
> - Timeout → **retry the last line** once.
> - Second failure → **halt streaming**, send `M5` (spray off) for safety, surface an error to the operator.
> - Never blindly continue — a missed move desyncs paint from position (R-03).

## Spray-Timing Strategy (encoder-less)
AURA has no motion encoder, so spray fires by **coordinate-arrival trigger**: because Python waits for `ok` after each move, it *knows* the head has reached the target before sending `M3`. For long strokes, embed `M3`/`M5` **between** the moves that bound the painted segment. Avoid pure time-delay triggering — it drifts.

## Example Command Sequence — paint a single horizontal stripe
```gcode
G28                     ; home
G1 X20 Y50 F2000        ; move to stripe start (no spray)
M3                      ; spray on
G1 X120 Y50 F1200       ; paint across at slower feed
M5                      ; spray off
G1 X20 Y60 F2000        ; reposition for next row
```
