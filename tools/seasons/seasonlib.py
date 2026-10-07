"""Shared helpers for the season pass: images as uint8 RGBA arrays, colour maths, region hints,
deterministic noise and small morphology. numpy + Pillow only (like tools/room_art)."""
import os
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.environ.get("AH_PROJECT") or os.path.abspath(os.path.join(HERE, "..", ".."))
ROOMS_DIR = os.path.join(PROJECT, "assets", "art", "rooms")


# ---------------------------------------------------------------------------------------------
# files
# ---------------------------------------------------------------------------------------------
def res_path(res):
    return res.replace("res://", PROJECT + "/")


def load(path):
    return np.array(Image.open(res_path(path)).convert("RGBA"))


def save(arr, path):
    """Writes a pixel-art PNG as small as possible without changing a single pixel: an indexed
    PNG when the image has at most 256 colours (checked by reading it back), else RGBA."""
    path = res_path(path)
    img = Image.fromarray(arr.astype(np.uint8), "RGBA")
    flat = arr.reshape(-1, 4)
    cols = np.unique(flat, axis=0)
    if len(cols) <= 256:
        # build the palette exactly: map every pixel to its colour index
        key = (flat[:, 0].astype(np.int64) << 24) | (flat[:, 1].astype(np.int64) << 16) | (flat[:, 2].astype(np.int64) << 8) | flat[:, 3]
        ckey = (cols[:, 0].astype(np.int64) << 24) | (cols[:, 1].astype(np.int64) << 16) | (cols[:, 2].astype(np.int64) << 8) | cols[:, 3]
        idx = np.searchsorted(ckey, key)
        pal_img = Image.fromarray(idx.reshape(arr.shape[:2]).astype(np.uint8), "P")
        pal = np.zeros((256, 3), np.uint8)
        pal[:len(cols)] = cols[:, :3]
        pal_img.putpalette(pal.reshape(-1).tolist())
        alpha = np.full(256, 255, np.uint8)
        alpha[:len(cols)] = cols[:, 3]
        pal_img.info["transparency"] = bytes(alpha.tolist())
        pal_img.save(path, optimize=True, transparency=bytes(alpha.tolist()))
        back = np.array(Image.open(path).convert("RGBA"))
        if np.array_equal(back, arr):
            return path
    img.save(path, optimize=True)
    return path


# ---------------------------------------------------------------------------------------------
# colour
# ---------------------------------------------------------------------------------------------
def hexrgb(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def ramp(hexes):
    return np.array([hexrgb(h) for h in hexes], np.float32)


def hsv(rgb):
    """rgb float/uint8 (..., 3) 0-255 -> h (deg), s, v (0-1)."""
    c = rgb[..., :3].astype(np.float32) / 255.0
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    mx = c.max(-1)
    mn = c.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    nz = d > 1e-6
    rm = nz & (mx == r)
    gm = nz & (mx == g) & ~rm
    bm = nz & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    h = h * 60.0
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h, s, mx


def lum(rgb):
    c = rgb[..., :3].astype(np.float32)
    return (0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]) / 255.0


def hue_in(h, lo, hi):
    """Hue range test that wraps (lo > hi means across 0)."""
    return (h >= lo) & (h <= hi) if lo <= hi else (h >= lo) | (h <= hi)


def mix(a, b, t):
    return a * (1 - t) + b * t


# ---------------------------------------------------------------------------------------------
# deterministic noise (no randomness at import time; seeds make rebuilds byte-identical)
# ---------------------------------------------------------------------------------------------
def hash2(x, y, seed=0):
    """Integer hash -> float [0, 1) per (x, y)."""
    x = np.asarray(x, np.int64)
    y = np.asarray(y, np.int64)
    n = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFF).astype(np.float32) / float(0x1000000)


def grid_hash(h, w, seed=0, ox=0, oy=0):
    ys, xs = np.mgrid[0:h, 0:w]
    return hash2(xs + ox, ys + oy, seed)


def value_noise(h, w, cell, seed=0, ox=0, oy=0):
    """Smooth value noise in [0, 1] on a lattice of `cell` px (cell may be (cx, cy))."""
    cx, cy = (cell, cell) if np.isscalar(cell) else cell
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    fx = (xs + ox) / cx
    fy = (ys + oy) / cy
    ix = np.floor(fx).astype(np.int64)
    iy = np.floor(fy).astype(np.int64)
    tx = fx - ix
    ty = fy - iy
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)
    a = hash2(ix, iy, seed)
    b = hash2(ix + 1, iy, seed)
    c = hash2(ix, iy + 1, seed)
    d = hash2(ix + 1, iy + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fbm(h, w, cell, seed=0, octaves=3, ox=0, oy=0):
    total = np.zeros((h, w), np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        c = cell / (2 ** o) if np.isscalar(cell) else (cell[0] / 2 ** o, cell[1] / 2 ** o)
        total += amp * value_noise(h, w, c, seed + 17 * o, ox, oy)
        norm += amp
        amp *= 0.5
    return total / norm


# ---------------------------------------------------------------------------------------------
# region hints: {"rect": [x, y, w, h]} | {"poly": [[x, y], ...]} | {"ellipse": [cx, cy, rx, ry]}
# ---------------------------------------------------------------------------------------------
def shape_mask(shapes, h, w, ox=0, oy=0):
    """Union of hint shapes as a bool mask for an image whose top-left sits at room (ox, oy)."""
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    sub = Image.new("L", (w, h), 0)
    ds = ImageDraw.Draw(sub)
    any_sub = False
    for s in shapes or []:
        target = ds if s.get("cut") else d
        any_sub = any_sub or bool(s.get("cut"))
        if "rect" in s:
            x, y, ww, hh = s["rect"]
            target.rectangle([x - ox, y - oy, x - ox + ww - 1, y - oy + hh - 1], fill=255)
        elif "poly" in s:
            target.polygon([(px - ox, py - oy) for px, py in s["poly"]], fill=255)
        elif "ellipse" in s:
            cx, cy, rx, ry = s["ellipse"]
            target.ellipse([cx - rx - ox, cy - ry - oy, cx + rx - ox, cy + ry - oy], fill=255)
    m = np.array(img) > 0
    if any_sub:
        m &= ~(np.array(sub) > 0)
    return m


# ---------------------------------------------------------------------------------------------
# morphology on bool masks (numpy only)
# ---------------------------------------------------------------------------------------------
def shift(m, dx, dy, fill=False):
    """out[y, x] = m[y - dy, x - dx] (moves content by +dx, +dy)."""
    out = np.full_like(m, fill)
    h, w = m.shape
    ys0, ys1 = max(0, dy), min(h, h + dy)
    xs0, xs1 = max(0, dx), min(w, w + dx)
    out[ys0:ys1, xs0:xs1] = m[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out


def dilate(m, r=1, cross=True):
    out = m.copy()
    for _ in range(r):
        o = out.copy()
        o |= shift(out, 1, 0) | shift(out, -1, 0) | shift(out, 0, 1) | shift(out, 0, -1)
        if not cross:
            o |= shift(out, 1, 1) | shift(out, -1, -1) | shift(out, 1, -1) | shift(out, -1, 1)
        out = o
    return out


def erode(m, r=1, cross=True):
    return ~dilate(~m, r, cross)


def distance(m, maxd=12):
    """Approximate (city-block) distance from each pixel to the nearest True pixel of m, capped."""
    d = np.full(m.shape, maxd, np.int32)
    cur = m.copy()
    d[cur] = 0
    for i in range(1, maxd):
        nxt = dilate(cur, 1)
        d[nxt & ~cur] = i
        cur = nxt
    return d


def flood(allowed, seeds, max_iter=4000):
    """Pixels of `allowed` 4-connected to `seeds`."""
    cur = seeds & allowed
    for _ in range(max_iter):
        nxt = dilate(cur, 1) & allowed
        if nxt.sum() == cur.sum():
            return nxt
        cur = nxt
    return cur


def components(m):
    """Labels 4-connected components (small images only). Returns (labels, count)."""
    h, w = m.shape
    labels = np.zeros((h, w), np.int32)
    n = 0
    ys, xs = np.nonzero(m)
    for y0, x0 in zip(ys, xs):
        if labels[y0, x0]:
            continue
        n += 1
        stack = [(y0, x0)]
        labels[y0, x0] = n
        while stack:
            y, x = stack.pop()
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not labels[yy, xx]:
                    labels[yy, xx] = n
                    stack.append((yy, xx))
    return labels, n


def colour_keys(arr):
    a = arr.astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


def palette_mask(arr, region):
    """All pixels whose RGB colour also occurs inside `region`."""
    keys = colour_keys(arr)
    allowed = np.unique(keys[region])
    return np.isin(keys, allowed)
