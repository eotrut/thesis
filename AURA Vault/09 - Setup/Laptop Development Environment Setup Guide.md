---
tags: [setup, environment, windows, rtx3050, guide]
date: 2026-07-06
---

# Laptop Development Environment Setup Guide

Target machine: **Windows laptop, NVIDIA RTX 3050 (4GB VRAM, Ampere, compute capability 8.6)**
Purpose: deployment + local dev machine for this thesis project (inference only — fine-tuning happens on Kaggle's T4, see [[AI Pipeline & Training Strategy — Session Notes]]).

> [!warning] Version mismatches are the #1 cause of setup pain
> The single biggest failure point on this project is a **CUDA Toolkit / GPU driver / PyTorch build mismatch**. Install in the order below and don't skip the verification step after PyTorch.

---

## 1. Git

**Recommended version:** Git for Windows 2.45+ (any recent 2.4x is fine — no specific pin required).

1. Download from [git-scm.com/download/win](https://git-scm.com/download/win).
2. Run the installer. Recommended options during install:
   - "Use Visual Studio Code as Git's default editor" (if VS Code already installed, otherwise leave default)
   - "Git from the command line and also from 3rd-party software"
   - "Use the OpenSSL library"
   - "Checkout Windows-style, commit Unix-style line endings" (default — keep it)
3. Verify install:

```powershell
git --version
```

4. Basic config (run once):

```powershell
git config --global user.name "Kurt Manabat"
git config --global user.email "kurtrobynmanabat@gmail.com"
git config --global init.defaultBranch main
```

5. Clone the thesis repository:

```powershell
cd C:\Users\Roehl\Claude\Projects
git clone https://github.com/eotrut/thesis.git
cd thesis
```

> [!warning]
> If `git clone` asks for credentials and password auth fails, GitHub no longer accepts account passwords over HTTPS — use a Personal Access Token (Settings → Developer settings → Personal access tokens) as the password, or set up SSH keys instead.

---

## 2. Python 3.11

**Why 3.11:** best balance of library compatibility for this stack — PyTorch, Ultralytics, OpenCV, and Roboflow all have mature stable wheels for 3.11. 3.12/3.13 can lag behind on some ML package wheels, and 3.9/3.10 are older than needed.

**Recommended approach:** direct install from python.org (simpler than pyenv on Windows; pyenv-win works but adds overhead not needed for a single-project machine).

1. Download Python 3.11.x (latest patch) from [python.org/downloads](https://www.python.org/downloads/).
2. During install, **check "Add python.exe to PATH"** before clicking Install.
3. Verify:

```powershell
python --version
pip --version
```

4. Create a virtual environment inside the cloned repo:

```powershell
cd C:\Users\Roehl\Claude\Projects\thesis
python -m venv venv
venv\Scripts\activate
```

> [!warning]
> Always activate `venv` before installing any of the packages below. Installing globally will make dependency versions harder to reproduce and can conflict with other Python tools on the machine.

---

## 3. NVIDIA Driver + CUDA Toolkit

The RTX 3050 (compute capability 8.6, Ampere) is supported by CUDA 11.1 and later, including all current 12.x releases.

1. Update the GPU driver first via **NVIDIA GeForce Experience** or [nvidia.com/drivers](https://www.nvidia.com/Download/index.aspx). A recent driver (r551+) supports current CUDA 12.x runtimes.
2. Install **CUDA Toolkit 12.1** from [developer.nvidia.com/cuda-12-1-0-download-archive](https://developer.nvidia.com/cuda-12-1-0-download-archive) (Windows → x86_64 → your Windows version → exe (local)).
3. Verify install:

```powershell
nvidia-smi
nvcc --version
```

`nvidia-smi` should show the RTX 3050 and a driver-supported CUDA version at or above 12.1. `nvcc --version` should report release 12.1.

> [!warning] Common mismatch
> You do **not** need the CUDA Toolkit version to exactly equal the PyTorch CUDA build number. PyTorch ships its own CUDA runtime bundled in the pip wheel. The system CUDA Toolkit mainly matters for the NVIDIA driver being new enough. If `nvidia-smi` reports a CUDA version lower than 12.1, update the driver before proceeding.

---

## 4. PyTorch with CUDA support

With `venv` activated:

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

This installs the PyTorch build compiled against CUDA 12.1, which matches the toolkit installed above and is fully compatible with the RTX 3050's compute capability 8.6.

**Verify GPU is detected:**

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

Expected output: a torch version string, `True`, and `NVIDIA GeForce RTX 3050`.

> [!warning]
> If `torch.cuda.is_available()` returns `False`, the most common causes are: (1) you installed the CPU-only wheel by omitting `--index-url`, (2) the GPU driver is older than the CUDA 12.1 requirement, or (3) a second Python/venv is active and the wrong one is being checked. Re-run `nvidia-smi` and re-check the venv is activated.

---

## 5. Ultralytics YOLOv8

```powershell
pip install ultralytics
```

This also pulls in NumPy, Pillow, and other core dependencies if not already present.

**Quick verification test** (runs a pretrained YOLOv8 segmentation model on a sample image):

```powershell
python -c "from ultralytics import YOLO; model = YOLO('yolov8n-seg.pt'); results = model('https://ultralytics.com/images/bus.jpg'); print('OK - inference ran on:', model.device)"
```

First run downloads the `yolov8n-seg.pt` weights automatically. Confirm the console output shows detections and no CUDA errors.

> [!warning]
> The `ultralytics` package now also ships newer model families (YOLO11, YOLO26) by default. This project specifically uses **YOLOv8 segmentation** (`yolov8n-seg.pt` / `yolov8s-seg.pt` etc.) — always specify the `v8` filename explicitly when loading models so a different architecture isn't loaded by mistake.

---

## 6. OpenCV

```powershell
pip install opencv-python
```

Verify:

```powershell
python -c "import cv2; print(cv2.__version__)"
```

---

## 7. pyserial

```powershell
pip install pyserial
```

Verify:

```powershell
python -c "import serial; print(serial.__version__)"
```

> [!warning]
> On Windows, the Arduino will show up as a COM port (e.g. `COM3`), not `/dev/ttyUSB0`. Check **Device Manager → Ports (COM & LPT)** with the Arduino plugged in to find the correct port name before writing serial connection code.

---

## 8. VS Code + Extensions

1. Download from [code.visualstudio.com](https://code.visualstudio.com/).
2. Install and open, then install these extensions (Ctrl+Shift+X):
   - **Python** (Microsoft) — core Python language support, debugging, venv detection
   - **Pylance** (Microsoft) — fast type checking and IntelliSense, usually bundled with Python extension but confirm it's enabled
   - **Arduino** (Microsoft, or vscode-arduino) — syntax highlighting, board/sketch management, upload from within VS Code
3. After opening the `thesis` repo folder in VS Code, select the interpreter: Ctrl+Shift+P → "Python: Select Interpreter" → choose `.\venv\Scripts\python.exe`.

---

## 9. Arduino IDE

**Recommended version:** Arduino IDE **2.x** (current stable line) — the legacy 1.8.x IDE still works but 2.x has a better serial monitor and board manager UI.

1. Download from [arduino.cc/en/software](https://www.arduino.cc/en/software).
2. Install, then open **Tools → Board → Boards Manager** and install the board package matching your Arduino (e.g. "Arduino AVR Boards" for Uno/Nano/Mega).
3. Plug in the Arduino, then **Tools → Port** and confirm the COM port appears (same port pyserial will need).
4. Upload the standard "Blink" example sketch as a sanity check that drivers and upload permissions are working.

> [!warning]
> If the Arduino isn't recognized, install the **CH340** or **FTDI** USB driver depending on the board's USB chip — many clone boards use CH340 and need a separate driver on Windows.

---

## 10. Obsidian

1. Download from [obsidian.md](https://obsidian.md/).
2. Open the vault at `C:\Users\Roehl\Claude\Projects\thesis\AURA Vault`.
3. Recommended community plugins for thesis documentation (Settings → Community plugins → Browse):
   - **Dataview** — query and summarize notes (e.g. list all meeting notes, track task status across the vault)
   - **Templater** — reusable note templates (e.g. a standard "session notes" or "meeting notes" template)
   - **Excalidraw** — diagrams for system architecture / pipeline sketches
   - **Kanban** — visual task board for thesis milestones, works well alongside `01 - Project Management`
   - **Advanced Tables** — easier markdown table editing for data/spec tables
   - **Git** (obsidian-git) — auto commit/push/pull the vault itself as part of version control, if you want the vault backed up alongside the code

---

## 11. Roboflow Python package

```powershell
pip install roboflow
```

Verify:

```powershell
python -c "import roboflow; print(roboflow.__version__)" 2>$null; if ($?) { echo "roboflow import OK" }
```

(A simple `import roboflow` succeeding without error is sufficient — the package doesn't require API authentication just to import.)

---

## Verification Checklist

Run through this list after completing all steps above, with `venv` activated:

- [ ] `git --version` returns a version number
- [ ] `git clone` of the thesis repo completed without auth errors
- [ ] `python --version` reports **3.11.x**
- [ ] `nvidia-smi` shows the RTX 3050 and CUDA version ≥ 12.1
- [ ] `nvcc --version` reports CUDA release 12.1
- [ ] `python -c "import torch; print(torch.cuda.is_available())"` prints **True**
- [ ] `torch.cuda.get_device_name(0)` prints **NVIDIA GeForce RTX 3050**
- [ ] YOLOv8 verification script runs inference with no CUDA errors
- [ ] `import cv2` succeeds and prints a version
- [ ] `import serial` succeeds and prints a version
- [ ] VS Code shows Python, Pylance, and Arduino extensions installed
- [ ] VS Code interpreter is set to `.\venv\Scripts\python.exe`
- [ ] Arduino IDE detects the board's COM port and Blink sketch uploads successfully
- [ ] Obsidian vault opens at the correct folder with recommended plugins enabled
- [ ] `import roboflow` succeeds with no error

---

## Reminder: commit and push this setup

Once everything above is confirmed working, commit and push the environment/setup work to the repo:

```powershell
cd C:\Users\Roehl\Claude\Projects\thesis
git add .
git commit -m "Add laptop dev environment setup (Python 3.11, CUDA 12.1, PyTorch, YOLOv8, tooling)"
git push origin main
```
