---
tags: [code, python, serial]
created: 2026-03-29
status: draft
---
# serial_command_template.py

> Reference implementation for [[🖥️ Serial Communication Protocol]]. Requires `pyserial` (`pip install pyserial`).

```python
# serial_command_template.py
# Minimal G-code serial controller for AURA (laptop -> Arduino Mega).
import time
import serial  # pip install pyserial


class GantrySerial:
    def __init__(self, port="COM3", baud=115200, timeout=5.0):
        # Windows: "COM3"; Linux: "/dev/ttyUSB0" or "/dev/ttyACM0"
        self.ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(2.0)  # allow Arduino auto-reset after port open
        self._flush_startup()

    def _flush_startup(self):
        # Drain any boot banner the firmware prints on reset.
        self.ser.reset_input_buffer()

    def send(self, cmd, retries=1):
        # Send one G-code line and block until 'ok'.
        line = (cmd.strip() + "\n").encode("ascii")
        for attempt in range(retries + 1):
            self.ser.write(line)
            resp = self._wait_ok()
            if resp is True:
                return True
            print("[warn] no ok for '%s' (attempt %d)" % (cmd, attempt + 1))
        # Safety: stop spray if we lose sync, then raise.
        self.ser.write(b"M5\n")
        raise RuntimeError("Arduino did not acknowledge: %s" % cmd)

    def _wait_ok(self):
        start = time.time()
        while time.time() - start < self.ser.timeout:
            resp = self.ser.readline().decode("ascii", "ignore").strip()
            if resp == "":
                continue
            if resp.lower().startswith("ok"):
                return True
            if resp.lower().startswith("error"):
                print("[err] firmware:", resp)
                return False
        return False  # timed out

    def move(self, x, y, feed=1500):
        self.send("G1 X%.2f Y%.2f F%d" % (x, y, feed))

    def spray_on(self):
        self.send("M3")

    def spray_off(self):
        self.send("M5")

    def home(self):
        self.send("G28")

    def close(self):
        self.spray_off()
        self.ser.close()


if __name__ == "__main__":
    g = GantrySerial(port="COM3")
    try:
        g.home()
        g.move(20, 50, feed=2000)   # travel to start
        g.spray_on()
        g.move(120, 50, feed=1200)  # paint stripe
        g.spray_off()
    finally:
        g.close()
```

> [!warning] Always wrap runs in try/finally so the spray is turned **off** even if the script crashes mid-stroke (Risk R-01/R-14).
