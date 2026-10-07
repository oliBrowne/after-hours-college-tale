"""A tiny pixel painter for hand-built mid-resolution props and room surfaces.

Coordinates are integer game pixels. Colours are hex strings or RGB tuples in 0..1.
"""
import os
import paths
import numpy as np
from PIL import Image, ImageDraw

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32.0


def C(value, alpha=1.0):
    if isinstance(value, str):
        v = value.lstrip("#")
        return (int(v[0:2], 16) / 255, int(v[2:4], 16) / 255, int(v[4:6], 16) / 255, alpha)
    if len(value) == 3:
        return (*value, alpha)
    return value


def mix(a, b, t):
    a, b = C(a), C(b)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


def shade(c, amount):
    """amount < 0 darkens toward ink-violet, > 0 lightens toward warm cream."""
    c = C(c)
    if amount < 0:
        return mix(c, "#141223", -amount)
    return mix(c, "#fff1d6", amount)


class Canvas:
    def __init__(self, w, h, fill=None, seed=1):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.float32)
        if fill is not None:
            self.a[:] = C(fill)
        self.rng = np.random.default_rng(seed)

    # --- primitives -------------------------------------------------------
    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            col = C(c)
            if col[3] >= 1:
                self.a[y, x] = col
            else:
                self.a[y, x, :3] = np.array(col[:3]) * col[3] + self.a[y, x, :3] * (1 - col[3])
                self.a[y, x, 3] = max(self.a[y, x, 3], col[3])

    def rect(self, x, y, w, h, c):
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        col = C(c)
        if col[3] >= 1:
            self.a[y0:y1, x0:x1] = col
        else:
            reg = self.a[y0:y1, x0:x1]
            reg[..., :3] = np.array(col[:3]) * col[3] + reg[..., :3] * (1 - col[3])
            reg[..., 3] = np.maximum(reg[..., 3], col[3])

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def poly(self, points, c):
        mask = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(mask).polygon([tuple(p) for p in points], fill=255)
        m = np.array(mask) > 0
        self.fill_mask(m, c)

    def ellipse(self, x, y, w, h, c):
        mask = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(mask).ellipse([x, y, x + w - 1, y + h - 1], fill=255)
        self.fill_mask(np.array(mask) > 0, c)

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            t = i / max(1, n - 1)
            self.px(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), c)

    def fill_mask(self, m, c):
        col = C(c)
        if col[3] >= 1:
            self.a[m] = col
        else:
            reg = self.a[m]
            reg[:, :3] = np.array(col[:3]) * col[3] + reg[:, :3] * (1 - col[3])
            reg[:, 3] = np.maximum(reg[:, 3], col[3])
            self.a[m] = reg

    def mask_rect(self, x, y, w, h):
        m = np.zeros((self.h, self.w), bool)
        m[max(0, y):max(0, y + h), max(0, x):max(0, x + w)] = True
        return m

    # --- textures ---------------------------------------------------------
    def dither_v(self, x, y, w, h, top, bottom, steps=6):
        """Vertical gradient quantised to `steps` bands with ordered dithering between them."""
        for yy in range(h):
            t = yy / max(1, h - 1) * (steps - 1)
            band = int(t)
            frac = t - band
            ca = mix(top, bottom, band / (steps - 1))
            cb = mix(top, bottom, min(steps - 1, band + 1) / (steps - 1))
            for xx in range(w):
                c = cb if frac > BAYER4[(y + yy) % 4, (x + xx) % 4] else ca
                self.px(x + xx, y + yy, c)

    def speckle(self, mask, colors, density=0.08):
        ys, xs = np.where(mask)
        pick = self.rng.random(len(ys)) < density
        for yy, xx in zip(ys[pick], xs[pick]):
            self.px(xx, yy, colors[self.rng.integers(len(colors))])

    def box(self, x, y, w, h, base, outline="#171a2b", light=0.18, dark=-0.28, rim=True):
        """A shaded block: outline, lit top edge, darker bottom/right edge."""
        if outline:
            self.rect(x, y, w, h, outline)
            x, y, w, h = x + 1, y + 1, w - 2, h - 2
        self.rect(x, y, w, h, base)
        if rim:
            self.hline(x, y, w, shade(base, light))
            self.vline(x, y, h, shade(base, light * 0.5))
            self.hline(x, y + h - 1, w, shade(base, dark))
            self.vline(x + w - 1, y, h, shade(base, dark * 0.7))

    def wood(self, x, y, w, h, base, vertical=False, plank=6, seed=0):
        """Planks with grain streaks and knots."""
        rng = np.random.default_rng(seed)
        self.rect(x, y, w, h, base)
        if vertical:
            for px0 in range(x, x + w, plank):
                tone = shade(base, rng.uniform(-0.12, 0.1))
                self.rect(px0, y, min(plank, x + w - px0), h, tone)
                self.vline(px0, y, h, shade(base, -0.35))
                for _ in range(max(1, h // 6)):
                    gx = px0 + 1 + rng.integers(max(1, plank - 2))
                    gy = y + rng.integers(h)
                    self.vline(gx, gy, rng.integers(2, 6), shade(tone, -0.15))
        else:
            for py0 in range(y, y + h, plank):
                tone = shade(base, rng.uniform(-0.12, 0.1))
                ph = min(plank, y + h - py0)
                self.rect(x, py0, w, ph, tone)
                self.hline(x, py0 + ph - 1, w, shade(base, -0.35))
                self.hline(x, py0, w, shade(tone, 0.1))
                for _ in range(max(1, w // 7)):
                    gx = x + rng.integers(w)
                    gy = py0 + 1 + rng.integers(max(1, ph - 2))
                    self.hline(gx, gy, rng.integers(3, 9), shade(tone, -0.14))
                seam = x + rng.integers(4, max(5, w - 4))
                self.vline(seam, py0, ph - 1, shade(base, -0.3))

    def paste(self, src, x, y):
        if isinstance(src, Canvas):
            src = src.a
        h, w = src.shape[:2]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        s = src[y0 - y:y1 - y, x0 - x:x1 - x]
        d = self.a[y0:y1, x0:x1]
        al = s[..., 3:4]
        d[..., :3] = s[..., :3] * al + d[..., :3] * (1 - al)
        d[..., 3:4] = np.maximum(d[..., 3:4], al)

    def outline_outside(self, c="#171a2b"):
        from scipy import ndimage
        m = self.a[..., 3] > 0.5
        ring = ndimage.binary_dilation(m, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])) & ~m
        self.a[ring] = C(c)

    def image(self):
        return Image.fromarray((np.clip(self.a, 0, 1) * 255).round().astype(np.uint8), "RGBA")

    def save(self, path):
        self.image().save(path)


_FONT = None


def _font():
    global _FONT
    if _FONT is None:
        import re
        base = paths.PROJECT + "/assets/art/afterhours-font"
        img = np.array(Image.open(base + ".png").convert("RGBA")).astype(np.float32) / 255
        chars = {}
        for line in open(base + ".fnt"):
            if line.startswith("char "):
                kv = dict(re.findall(r"(\w+)=(-?\d+)", line))
                chars[int(kv["id"])] = tuple(int(kv[k]) for k in ("x", "y", "width", "height", "xoffset", "yoffset"))
        _FONT = (img, chars)
    return _FONT


def text(cv, s, x, y, color, advance=6):
    """Blit the game's bitmap font (alpha from the glyph sheet) at 1:1."""
    img, chars = _font()
    col = C(color)
    for i, ch in enumerate(s):
        g = chars.get(ord(ch))
        if not g:
            continue
        gx, gy, gw, gh, ox, oy = g
        glyph = img[gy:gy + gh, gx:gx + gw]
        alpha = np.maximum(glyph[..., 3], glyph[..., :3].max(-1) * (glyph[..., 3] > 0))
        for yy in range(gh):
            for xx in range(gw):
                if glyph[yy, xx, 3] > 0.5 and glyph[yy, xx, :3].max() > 0.5:
                    cv.px(x + i * advance + xx + ox - 1, y + yy + oy, col)


def text_width(s, advance=6):
    return len(s) * advance
