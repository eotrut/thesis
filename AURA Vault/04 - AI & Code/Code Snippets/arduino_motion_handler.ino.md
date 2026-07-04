---
tags: [code, arduino, cpp, firmware]
created: 2026-03-29
status: draft
---
# arduino_motion_handler.ino

> Minimal *custom* motion handler illustrating the serial contract from [[🖥️ Serial Communication Protocol]]. For production, a GRBL/Marlin variant is recommended; this shows the concept clearly.

```cpp
// arduino_motion_handler.ino
// Parses simple G-code lines, steps NEMA 23 via TB6600, sprays via relay.
// Dual-X: both X drivers share STEP/DIR so they move identically (anti-racking).

const int X_STEP = 54, X_DIR = 55, X_EN = 38;   // X1 + X2 wired together
const int Y_STEP = 60, Y_DIR = 61, Y_EN = 56;
const int SPRAY_RELAY = 9;
const int XMIN = 3, XMAX = 2, YMIN = 14;

const float STEPS_PER_MM = 40.0;   // see Mechanical Design (1/8 microstep)
long curX = 0, curY = 0;           // current position in steps

void setup() {
  Serial.begin(115200);
  pinMode(X_STEP, OUTPUT); pinMode(X_DIR, OUTPUT); pinMode(X_EN, OUTPUT);
  pinMode(Y_STEP, OUTPUT); pinMode(Y_DIR, OUTPUT); pinMode(Y_EN, OUTPUT);
  pinMode(SPRAY_RELAY, OUTPUT);
  pinMode(XMIN, INPUT_PULLUP); pinMode(XMAX, INPUT_PULLUP); pinMode(YMIN, INPUT_PULLUP);
  digitalWrite(X_EN, LOW); digitalWrite(Y_EN, LOW);   // enable drivers (active low)
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

void moveTo(long tx, long ty) {
  long dx = tx - curX, dy = ty - curY;
  digitalWrite(X_DIR, dx >= 0 ? HIGH : LOW);
  digitalWrite(Y_DIR, dy >= 0 ? HIGH : LOW);
  long nx = abs(dx), ny = abs(dy), n = max(nx, ny);
  for (long i = 0; i < n; i++) {          // naive per-axis stepping
    if (i < nx) pulse(X_STEP);
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
  digitalWrite(X_DIR, LOW);
  while (digitalRead(XMIN) == HIGH) { pulse(X_STEP); delayMicroseconds(400); }
  digitalWrite(Y_DIR, LOW);
  while (digitalRead(YMIN) == HIGH) { pulse(Y_STEP); delayMicroseconds(400); }
  curX = 0; curY = 0;
}
```

> [!note] This is a teaching skeleton. Real use needs acceleration ramps and proper Bresenham interpolation — reasons to prefer GRBL/Marlin. See [[🖥️ Serial Communication Protocol]].
