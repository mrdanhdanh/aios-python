#!/usr/bin/env python3
"""Generate a synthetic magenta-bg sprite sheet (4 fake frames) for AC3 test."""
from pathlib import Path

import numpy as np
from PIL import Image

W = H = 256
img = np.zeros((H, W, 3), dtype=np.uint8)
img[:, :] = (255, 0, 255)  # magenta background

colors = [(255, 120, 40), (40, 200, 120), (60, 120, 255), (230, 230, 60)]
for r in range(2):
    for c in range(2):
        cx = c * 128 + 64
        cy = r * 128 + 64
        img[cy - 30:cy + 30, cx - 30:cx + 30] = colors[r * 2 + c]

out = Path(__file__).resolve().parent / "sample_raw.png"
Image.fromarray(img).save(out)
print("wrote", out)
