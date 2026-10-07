"""Helpers that turn the painted environment atlas into mid-resolution pixel sprites.

Everything here works at 1:1 game pixels (the game renders at 640x360).
"""
import os
import paths
import json
import numpy as np
from PIL import Image
from scipy import ndimage

ART = paths.PROJECT + "/assets/art"


def load_rgba(path):
    return np.array(Image.open(path).convert("RGBA")).astype(np.float32) / 255.0


def atlas_cell(index):
    meta = json.load(open(f"{ART}/environment-detail-atlas.json"))
    x, y, w, h = meta["cells"][index]
    img = load_rgba(f"{ART}/environment-detail-v1.png")
    return img[y:y + h, x:x + w].copy()


def clean_components(rgba, keep_ratio=0.015, border_ratio=0.12):
    """Drop slivers of neighbouring cells and stray matte pixels."""
    mask = rgba[..., 3] > 0.43
    labels, count = ndimage.label(mask, structure=np.ones((3, 3)))
    if count == 0:
        return rgba
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    largest = sizes.max()
    keep = np.zeros(count + 1, bool)
    h, w = mask.shape
    for i, size in enumerate(sizes, start=1):
        ys, xs = np.where(labels == i)
        touches = ys.min() == 0 or xs.min() == 0 or ys.max() == h - 1 or xs.max() == w - 1
        if size == largest:
            keep[i] = True
        elif touches:
            keep[i] = size >= largest * border_ratio * 4
        else:
            keep[i] = size >= largest * keep_ratio
    out = rgba.copy()
    out[~keep[labels], 3] = 0.0
    out[out[..., 3] <= 0.43, 3] = 0.0
    return out


def trim(rgba):
    ys, xs = np.where(rgba[..., 3] > 0)
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def downscale(rgba, size):
    """Premultiplied box downscale, then a hard alpha edge."""
    w, h = size
    premul = rgba.copy()
    premul[..., :3] *= premul[..., 3:4]
    img = Image.fromarray((premul * 255).round().astype(np.uint8), "RGBA")
    small = np.array(img.resize((w, h), Image.BOX)).astype(np.float32) / 255.0
    alpha = small[..., 3:4]
    rgb = np.where(alpha > 0.01, small[..., :3] / np.maximum(alpha, 1e-6), 0)
    out = np.concatenate([np.clip(rgb, 0, 1), (alpha > 0.5).astype(np.float32)], -1)
    return out


def quantize(rgba, colors=40, saturation=1.0, contrast=1.0, brightness=1.0):
    """Median-cut palette without dithering so clusters read as hand-placed pixels."""
    rgb = rgba[..., :3].copy()
    if saturation != 1.0:
        grey = rgb.mean(-1, keepdims=True)
        rgb = grey + (rgb - grey) * saturation
    if contrast != 1.0:
        rgb = 0.5 + (rgb - 0.5) * contrast
    rgb = np.clip(rgb * brightness, 0, 1)
    opaque = rgba[..., 3] > 0
    img = Image.fromarray((rgb * 255).round().astype(np.uint8), "RGB")
    q = img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    out = np.array(q.convert("RGB")).astype(np.float32) / 255.0
    return np.concatenate([out, opaque[..., None].astype(np.float32)], -1)


def despeckle(rgba):
    """Replace lone pixels whose 8 neighbours all share another colour."""
    out = rgba.copy()
    h, w = rgba.shape[:2]
    key = (rgba[..., 0] * 255).astype(int) * 65536 + (rgba[..., 1] * 255).astype(int) * 256 + (rgba[..., 2] * 255).astype(int)
    key[rgba[..., 3] == 0] = -1
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            n = key[y - 1:y + 2, x - 1:x + 2].flatten()
            n = np.delete(n, 4)
            if (n == n[0]).all() and n[0] != key[y, x] and n[0] != -1:
                out[y, x] = rgba[y - 1, x - 1]
    return out


def outline(rgba, color=(0.09, 0.08, 0.13), alpha_only=True):
    """Add a 1px dark outline on the outside of the silhouette (bottom/sides)."""
    mask = rgba[..., 3] > 0
    grown = ndimage.binary_dilation(mask, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    ring = grown & ~mask
    out = rgba.copy()
    out[ring, :3] = color
    out[ring, 3] = 1.0
    return out


def pad(rgba, n=1):
    return np.pad(rgba, ((n, n), (n, n), (0, 0)))


def sprite_from_cell(index, width=None, height=None, colors=40, **grade):
    cell = trim(clean_components(atlas_cell(index)))
    h, w = cell.shape[:2]
    if width and not height:
        height = round(h * width / w)
    if height and not width:
        width = round(w * height / h)
    small = downscale(cell, (width, height))
    return quantize(small, colors, **grade)


def to_image(rgba):
    return Image.fromarray((np.clip(rgba, 0, 1) * 255).round().astype(np.uint8), "RGBA")


def paste(dst, src, x, y):
    """Alpha-over src onto dst (both float RGBA arrays) at integer x, y."""
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    a = s[..., 3:4]
    d[..., :3] = s[..., :3] * a + d[..., :3] * (1 - a)
    d[..., 3:4] = np.maximum(d[..., 3:4], a)
