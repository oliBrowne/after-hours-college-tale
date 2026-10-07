"""Pixel clouds lit from below by the set sun, on a horizontally tileable transparent strip."""
import numpy as np
from pixel import Canvas, C

DUSK = ["#845687", "#a96088", "#bb6184", "#c97d94", "#d36d7a", "#ee8f73", "#f7b07e"]


def _cloud(length, thick, rng, pal):
    """One flat-bottomed cloud: a long base with rounded heaps on top, lit underside."""
    w, h = length + 8, thick * 3 + 6
    cv = Canvas(w, h)
    floor = h - 3
    lumps = [(4, floor - thick, length, thick + 1)]
    x = 6
    while x < length - 8:
        lw = int(rng.integers(10, 22)); lh = int(rng.integers(thick, thick * 2 + 2))
        lumps.append((x, floor - lh, lw, lh + 1))
        x += int(rng.integers(6, 14))
    for (lx, ly, lw, lh) in lumps:
        cv.ellipse(lx - 1, ly - 1, lw + 2, (lh + 1) * 2, pal[0])
    for (lx, ly, lw, lh) in lumps:
        cv.ellipse(lx, ly, lw, lh * 2, pal[1])
        cv.ellipse(lx + 1, ly + 1, lw - 3, lh * 2 - 2, pal[3] if rng.random() < 0.5 else pal[2])
        cv.ellipse(lx + 2, ly + lh // 2 + 1, lw - 4, lh, pal[4])
    cv.a[floor + 1:] = 0
    m = cv.a[..., 3] > 0
    for xx in range(w):
        col = np.where(m[:floor + 1, xx])[0]
        if len(col):
            b = col.max()
            cv.px(xx, b, pal[6] if 6 < xx < w - 6 else pal[5])
            cv.px(xx, b - 1, pal[5])
    return cv.a


def cloud_strip(width=640, height=40, count=5, seed=1, pal=DUSK, sizes=(60, 130)):
    rng = np.random.default_rng(seed)
    cv = Canvas(width, height)
    xs = np.sort(rng.choice(np.arange(0, width, 40), count, replace=False)) + rng.integers(0, 30, count)
    for cx in xs:
        cl = _cloud(int(rng.integers(*sizes)), int(rng.integers(3, 6)), rng, pal)
        ch = cl.shape[0]
        cy = int(rng.integers(0, max(1, height - ch)))
        for dx in (-width, 0, width):
            cv.paste(cl, int(cx) + dx, cy)
    return cv
