---
tags: [code, python, segmentation, pytorch]
created: 2026-03-29
status: draft
---
# segmentation_inference.py

> Reference implementation for [[🔮 Segmentation Model]]. Requires `torch`, `torchvision`, `opencv-python`, `numpy`.

```python
# segmentation_inference.py
# Load a trained segmentation model, run it on a USB-camera frame, overlay the mask.
import cv2
import numpy as np
import torch
import torchvision.transforms as T

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
INPUT_SIZE = 512
NUM_CLASSES = 2  # binary: 0 = not paintable, 1 = paintable

# ImageNet normalization (backbone was pretrained on ImageNet).
PREPROC = T.Compose([
    T.ToPILImage(),
    T.Resize((INPUT_SIZE, INPUT_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def load_model(checkpoint_path):
    # DeepLabV3+ with a MobileNetV3 backbone (see AI & Software Design note).
    from torchvision.models.segmentation import deeplabv3_mobilenet_v3_large
    model = deeplabv3_mobilenet_v3_large(num_classes=NUM_CLASSES, weights=None)
    state = torch.load(checkpoint_path, map_location=DEVICE)
    model.load_state_dict(state)
    model.eval().to(DEVICE)
    return model


def capture_frame(cam_index=0):
    cap = cv2.VideoCapture(cam_index)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Camera capture failed")
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


@torch.no_grad()
def infer(model, frame_rgb):
    h, w = frame_rgb.shape[:2]
    x = PREPROC(frame_rgb).unsqueeze(0).to(DEVICE)
    logits = model(x)["out"]                       # (1, C, H, W)
    mask = logits.argmax(1).squeeze(0).byte().cpu().numpy()
    mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
    return mask                                    # 0/1 mask at source size


def overlay(frame_rgb, mask, alpha=0.5):
    color = np.zeros_like(frame_rgb)
    color[mask == 1] = (0, 255, 0)                 # paintable = green
    return cv2.addWeighted(frame_rgb, 1.0, color, alpha, 0)


if __name__ == "__main__":
    model = load_model("checkpoints/aura_seg_best.pt")
    frame = capture_frame(0)
    mask = infer(model, frame)
    vis = overlay(frame, mask)
    cv2.imwrite("mask_overlay.png", cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
    print("paintable pixel fraction: %.3f" % (mask.mean()))
```
