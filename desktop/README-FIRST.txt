AURA - AI-Based Autonomous Wall Painting Robot (desktop app)
Holy Angel University - BS Computer Engineering

HOW TO START
------------
1. Unzip the whole folder somewhere, e.g. your Desktop or Documents.
   Do not run AURA.exe from inside the zip, and keep every file together:
   AURA.exe needs the _internal and model folders next to it.
2. Double-click AURA.exe.
3. The first start takes up to a minute while the AI model loads.
   You will see "Starting the segmentation engine..." until it is ready.

"WINDOWS PROTECTED YOUR PC" / UNKNOWN PUBLISHER
-----------------------------------------------
AURA is a student project and the exe is not code-signed (signing needs a
paid certificate), so Windows SmartScreen warns about an unknown publisher.
This is expected. To run it:
    click "More info"  ->  "Run anyway".
Some antivirus programs scan large unsigned apps slowly on first start;
that is also expected.

CPU OR GPU
----------
The Dashboard's "Inference Device" card shows what the AI runs on:
  CPU  - works on any laptop. Each frame takes a few tenths of a second.
  CUDA - only in the GPU build, and only with an NVIDIA graphics card
         (driver 530 or newer). Falls back to CPU automatically otherwise.

CAMERA
------
Camera View > Camera > "Laptop / USB camera" uses the built-in webcam.
If it stays black: Windows Settings > Privacy & security > Camera, turn on
"Camera access" and "Let desktop apps access your camera", and close other
apps that use the camera (Zoom, Teams, Camera).

REQUIREMENTS
------------
Windows 10 (21H2 or newer) or Windows 11, 64-bit. Nothing else to install:
Python is inside the app, and the window uses Microsoft Edge WebView2, which
is part of Windows. About 8 GB RAM recommended.

LICENSES AND SOURCE CODE
------------------------
AURA is built on open-source software. The "Licenses" tab in the app
credits everything it bundles. LICENSES.txt (next to AURA.exe) lists every
included package with its licence, and the licenses folder holds their full
licence texts. AURA includes Ultralytics YOLOv8, which is licensed under the
AGPL-3.0, so AURA's complete source code is available to you at
https://github.com/eotrut/thesis (BUILD-INFO.txt names the exact version).

IF SOMETHING GOES WRONG
-----------------------
Log file: %LOCALAPPDATA%\AURA\logs\aura-desktop.log
(paste that path into the File Explorer address bar). Send it with a
description of what happened.

Model files are in the "model" folder (best.pt = AURA's trained wall
segmentation model, mobile_sam.pt = MobileSAM for the smart-select tool).
