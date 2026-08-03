---
tags: [code, arduino, cpp, firmware]
created: 2026-03-29
status: draft
---
# arduino_motion_handler.ino

> Minimal *custom* motion handler illustrating the serial contract from [[🖥️ Serial Communication Protocol]]. A GRBL/Marlin variant is **no longer an option** — those assume a RAMPS-style shield, which is not in this build ([[🔌 Electronics & Wiring]]). This custom sketch is the production path.

> [!warning] Pin numbers corrected 2026-08-04
> The original constants (54/55/38, 60/61/56) were **RAMPS 1.4 pin assignments** and are meaningless now that the Mega wires straight to the TB6600s. Replaced with the direct-wiring pinout; X-left (3/4/5) is bench tested, the rest are planned.

> [!bug] This snippet still parses G-code
> The command set has changed to `MOVE`/`SPRAY`/`HOME`, but whether the Arduino parses that directly or the host translates from G-code is an **open decision** — see [[🖥️ Serial Communication Protocol]]. The parsing section below is illustrative until that is settled; the stepping and homing logic is unaffected either way.

```cpp
// arduino_motion_handler.ino
// Steps NEMA 23 via TB6600 (direct-wired, no RAMPS), sprays via relay.
// Dual-X: both X drivers are pulsed from ONE step routine so they cannot
// desync. Never expose them to the host as two axes — that is risk R-02.

const int XL_STEP = 3,  XL_DIR = 4,  XL_EN = 5;    // X-left  (bench tested)
const int XR_STEP = 6,  XR_DIR = 7,  XR_EN = 8;    // X-right (mirrored)
const int Y_STEP  = 9,  Y_DIR  = 10, Y_EN  = 11;   // Y (driver not yet procured)
const int SPRAY_RELAY = 12;
const int XMIN = 22, XMAX = 23, YMIN = 24;         // both X ends homed (R-02 check)

// If the X motors are mounted facing opposite directions, invert one DIR.
const bool XR_DIR_INVERT = true;

const float STEPS_PER_MM = 160.0;  // 1/32 microstep, bench confirmed 2026-08-03
                                   // (200 * 32) / (20 * 2) — see Mechanical Design
long curX = 0, curY = 0;           // current position in steps

void setup() {
  Serial.begin(115200);
  pinMode(XL_STEP, OUTPUT); pinMode(XL_DIR, OUTPUT); pinMode(XL_EN, OUTPUT);
  pinMode(XR_STEP, OUTPUT); pinMode(XR_DIR, OUTPUT); pinMode(XR_EN, OUTPUT);
  pinMode(Y_STEP,  OUTPUT); pinMode(Y_DIR,  OUTPUT); pinMode(Y_EN,  OUTPUT);
  pinMode(SPRAY_RELAY, OUTPUT);
  pinMode(XMIN, INPUT_PULLUP); pinMode(XMAX, INPUT_PULLUP); pinMode(YMIN, INPUT_PULLUP);
  // ENA is active-low on these TB6600 units — LOW enables. Confirmed on bench.
  digitalWrite(XL_EN, LOW); digitalWrite(XR_EN, LOW); digitalWrite(Y_EN, LOW);
  digitalWrite(SPRAY_RELAY, LOW);
  Serial.println("ok");   // ready banner
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    handle(line);
    Serial.println("ok");   // acknowledge every command
  }
}

void handle(String cmd) {
  if (cmd.startsWith("G28")) { homeAxes(); return; }
  if (cmd.startsWith("M3"))  { digitalWrite(SPRAY_RELAY, HIGH); return; }
  if (cmd.startsWith("M5"))  { digitalWrite(SPRAY_RELAY, LOW);  return; }
  if (cmd.startsWith("G1")) {
    float x = parseVal(cmd, 'X', curX / STEPS_PER_MM);
    float y = parseVal(cmd, 'Y', curY / STEPS_PER_MM);
    moveTo((long)(x * STEPS_PER_MM), (long)(y * STEPS_PER_MM));
  }
}

float parseVal(String s, char key, float fallback) {
  int i = s.indexOf(key);
  if (i < 0) return fallback;
  return s.substring(i + 1).toFloat();
}

// Set X direction on BOTH drivers at once. Every X direction change must go
// through here — if the two DIR pins are ever set separately the motors can
// fight each other and rack the gantry (R-02).
void setXDir(bool forward) {
  digitalWrite(XL_DIR, forward ? HIGH : LOW);
  digitalWrite(XR_DIR, (forward != XR_DIR_INVERT) ? HIGH : LOW);
}

// One X step = one pulse to each driver, same iteration. Not two axes.
void stepX() {
  digitalWrite(XL_STEP, HIGH); digitalWrite(XR_STEP, HIGH);
  delayMicroseconds(5);
  digitalWrite(XL_STEP, LOW);  digitalWrite(XR_STEP, LOW);
  delayMicroseconds(5);
}

void moveTo(long tx, long ty) {
  long dx = tx - curX, dy = ty - curY;
  setXDir(dx >= 0);
  digitalWrite(Y_DIR, dy >= 0 ? HIGH : LOW);
  long nx = abs(dx), ny = abs(dy), n = max(nx, ny);
  for (long i = 0; i < n; i++) {          // naive per-axis stepping
    if (i < nx) stepX();
    if (i < ny) pulse(Y_STEP);
    delayMicroseconds(300);               // speed control (tune)
  }
  curX = tx; curY = ty;
}

void pulse(int pin) {
  digitalWrite(pin, HIGH); delayMicroseconds(5);
  digitalWrite(pin, LOW);  delayMicroseconds(5);
}

void homeAxes() {
  // Back off toward min endstops, then zero.
  setXDir(false);
  while (digitalRead(XMIN) == HIGH) { stepX(); delayMicroseconds(400); }
  digitalWrite(Y_DIR, LOW);
  while (digitalRead(YMIN) == HIGH) { pulse(Y_STEP); delayMicroseconds(400); }
  curX = 0; curY = 0;
}
```

> [!warning] Homing here does NOT yet check for racking
> `homeAxes()` stops as soon as `XMIN` triggers, which is whichever X corner arrives first — so a skewed gantry homes to a skewed zero and reports success. The R-02 mitigation calls for homing *both* X corners: drive until both `XMIN` and `XMAX` have triggered and reject the run if they are more than a tolerance apart. Add before trusting any positional measurement.

> [!note] This is a teaching skeleton
> Real use needs acceleration ramps and proper Bresenham interpolation. Those were previously "reasons to prefer GRBL/Marlin" — but with RAMPS out of the build that option is gone, so they are now work that has to be written here. Budget for it in Phase 2. See [[🖥️ Serial Communication Protocol]].
