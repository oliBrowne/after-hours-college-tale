"""Dusk sky with the Flatirons, cut from the title painting and reduced to mid resolution."""
import numpy as np
from PIL import Image
from midlib import ART, downscale, quantize


def flatirons_panel(scale=2.2, colors=36):
    img = np.array(Image.open(f"{ART}/boulder-title-v2.png").convert("RGBA")).astype(np.float32) / 255.0
    crop = img[0:292, 714:1142].copy()  # sky and slabs, clear of the window frame and maple
    # Paint out the one falling leaf in the crop by borrowing sky from the left.
    for (x0, y0, x1, y1) in [(395, 0, 428, 42)]:
        crop[y0:y1, x0:x1] = crop[y0:y1, x0 - 40:x1 - 40]
    h, w = crop.shape[:2]
    small = downscale(crop, (round(w / scale), round(h / scale)))
    small[..., 3] = 1.0
    return quantize(small, colors, saturation=0.92, contrast=1.04)


def panorama(width=640, height=150, building=(214, 426), scale=2.2):
    left = flatirons_panel(scale)
    ph, pw = left.shape[:2]
    right = left[:, ::-1]
    sky = np.zeros((height, width, 4), np.float32)
    sky[..., 3] = 1
    y = height - ph - 22
    # Fill everything with per-row sky colour first (sampled from the panel's left sky columns).
    row_colour = np.median(left[:, :6, :3], axis=1)
    for yy in range(height):
        src = min(ph - 1, max(0, yy - y))
        sky[yy, :, :3] = row_colour[src]
    sky[max(0, y):y + ph, 0:pw] = left[max(0, -y):, :]
    sky[max(0, y):y + ph, width - pw:width] = right[max(0, -y):, :]
    # Bridge the gap behind the building with mirrored strips so no seam peeks out.
    gap0, gap1 = pw, width - pw
    top = max(0, y)
    for i in range(max(0, gap1 - gap0)):
        if i < (gap1 - gap0) // 2:
            sky[top:y + ph, gap0 + i] = left[max(0, -y):, pw - 1 - i]
        else:
            j = gap1 - 1 - (gap0 + i)
            sky[top:y + ph, gap0 + i] = right[max(0, -y):, j]
    return sky, y
