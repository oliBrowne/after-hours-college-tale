"""Room surfaces painted at 1:1 game pixels: flagstone terraces, plank floors, plaster and panelled walls."""
import numpy as np
from pixel import Canvas, C, mix, shade

LEAVES = ["#c8682e", "#a83c32", "#d9a441", "#8c4a2a"]


def flagstones(cv, x, y, w, h, pal, seed=0, row0=7, row1=13, leaves=0.0, moss=0.0, leaf_clusters=()):
    """Irregular ashlar paving; rows grow taller toward the bottom for a little perspective."""
    rng = np.random.default_rng(seed)
    mortar = pal[0]
    cv.rect(x, y, w, h, mortar)
    yy = y
    while yy < y + h:
        t = (yy - y) / max(1, h)
        rh = int(round(row0 + (row1 - row0) * t)) + int(rng.integers(-1, 2))
        rh = max(5, min(rh, y + h - yy))
        xx = x - int(rng.integers(0, 20))
        while xx < x + w:
            sw = int(rng.integers(int(rh * 1.6), int(rh * 3.4)))
            x0, x1 = max(x, xx + 1), min(x + w, xx + sw)
            if x1 - x0 >= 2:
                tone = mix(pal[3], pal[2 + int(rng.integers(0, 3))], 0.55) if rng.random() < 0.9 else pal[2]
                cv.rect(x0, yy + 1, x1 - x0, rh - 1, tone)
                cv.hline(x0, yy + 1, x1 - x0, shade(tone, 0.06))
                cv.hline(x0, yy + rh - 1, x1 - x0, shade(tone, -0.08))
                area = (x1 - x0) * (rh - 1)
                for _ in range(area // 14):
                    cv.px(x0 + int(rng.integers(0, x1 - x0)), yy + 1 + int(rng.integers(0, rh - 1)), shade(tone, float(rng.choice([-0.09, -0.05, 0.06]))))
                if rng.random() < 0.12:
                    cx = x0 + int(rng.integers(1, max(2, x1 - x0 - 1)))
                    cy = yy + 2
                    for _ in range(int(rng.integers(2, rh))):
                        cv.px(cx, cy, shade(tone, -0.25)); cx += int(rng.integers(-1, 2)); cy += 1
                if rng.random() < moss:
                    mx = x0 + int(rng.integers(0, max(1, x1 - x0 - 3)))
                    cv.rect(mx, yy + rh - 1, int(rng.integers(2, 5)), 1, "#3f5741")
                    cv.px(mx + 1, yy + rh - 2, "#566d4a")
            xx += sw
        yy += rh
    for (cx, cy, r, n) in leaf_clusters:
        for _ in range(n):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
            lx, ly = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.5)
            if not (x <= lx < x + w and y <= ly < y + h):
                continue
            c = LEAVES[int(rng.integers(len(LEAVES)))]
            cv.px(lx, ly, c); cv.px(lx + 1, ly, shade(c, -0.2))
            if rng.random() < 0.4:
                cv.px(lx, ly - 1, shade(c, 0.15))
    for _ in range(int(w * h * leaves / 100)):
        lx, ly = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        c = LEAVES[int(rng.integers(len(LEAVES)))]
        cv.px(lx, ly, c); cv.px(lx + 1, ly, shade(c, -0.2))
        if rng.random() < 0.5:
            cv.px(lx, ly - 1, shade(c, 0.15))


def light_pool(cv, cx, cy, rx, ry, color="#f6cf7a", strength=0.18, steps=3):
    """Stepped warm pool on the floor (three concentric bands, no soft gradient)."""
    for i in range(steps):
        f = 1 - i / steps
        a = strength * (i + 1) / steps
        erx, ery = int(rx * f), int(ry * f)
        for yy in range(-ery, ery + 1):
            span = int(erx * np.sqrt(max(0.0, 1 - (yy / (ery + 0.5)) ** 2)))
            cv.rect(cx - span, cy + yy, span * 2 + 1, 1, C(color, a / (i + 1)))


def ashlar_wall(cv, x, y, w, h, pal, course=5, seed=0, cap=True):
    """Rough-cut sandstone: courses of varying height, stones of varying length and tone."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, pal[1])
    top = y
    if cap:
        cv.rect(x, y, w, 3, pal[4]); cv.hline(x, y, w, pal[5]); cv.hline(x, y + 3, w, pal[1])
        top = y + 4
    yy = top
    while yy < y + h - 1:
        ch = min(int(rng.choice([course - 1, course, course, course + 2])), y + h - 1 - yy)
        xx = x - int(rng.integers(0, 10))
        while xx < x + w:
            sw = int(rng.integers(6, 15)) if ch < course + 2 else int(rng.integers(10, 20))
            x0, x1 = max(x, xx), min(x + w, xx + sw - 1)
            r = rng.random()
            tone = pal[3] if r < 0.55 else pal[2] if r < 0.85 else pal[4]
            if x1 > x0 and ch > 1:
                cv.rect(x0, yy, x1 - x0, ch - 1, tone)
                cv.hline(x0, yy, x1 - x0, shade(tone, 0.08))
                cv.px(x1 - 1, yy + ch - 2, shade(tone, -0.12))
                for _ in range((x1 - x0) * ch // 6):
                    cv.px(x0 + int(rng.integers(0, x1 - x0)), yy + int(rng.integers(0, max(1, ch - 1))), shade(tone, float(rng.choice([-0.07, -0.04, 0.05]))))
            xx += sw
        yy += ch
    cv.hline(x, y + h - 1, w, C("#0d0b16", 0.6))


def sidewalk(cv, x, y, w, h, seed=0, slab=18):
    """Square concrete slabs with expansion joints, stains and the odd crack."""
    rng = np.random.default_rng(seed)
    pal = ["#4f4a54", "#6a6570", "#77727c", "#807a84", "#8a8590"]
    cv.rect(x, y, w, h, pal[0])
    yy = y
    row = 0
    while yy < y + h:
        rh = 11 + (row // 4)
        rh = min(rh, y + h - yy)
        for xx in range(x - (slab // 2 if row % 2 else 0), x + w, slab):
            x0, x1 = max(x, xx + 1), min(x + w, xx + slab)
            if x1 - x0 < 2:
                continue
            tone = pal[int(rng.choice([2, 3, 3, 4]))]
            cv.rect(x0, yy + 1, x1 - x0, rh - 1, tone)
            cv.hline(x0, yy + 1, x1 - x0, shade(tone, 0.06))
            for _ in range((x1 - x0) * rh // 10):
                cv.px(x0 + int(rng.integers(0, x1 - x0)), yy + 1 + int(rng.integers(0, max(1, rh - 1))), shade(tone, float(rng.choice([-0.06, 0.05]))))
            if rng.random() < 0.06:
                cv.ellipse(x0 + int(rng.integers(0, max(1, x1 - x0 - 4))), yy + 2 + int(rng.integers(0, max(1, rh - 4))), 4, 2, shade(tone, -0.15))
            if rng.random() < 0.08:
                cx, cy = x0 + int(rng.integers(2, max(3, x1 - x0 - 2))), yy + 1
                for _ in range(rh - 2):
                    cv.px(cx, cy, shade(tone, -0.25)); cx += int(rng.integers(-1, 2)); cy += 1
        yy += rh
        row += 1


def asphalt(cv, x, y, w, h, seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, "#2c2a35")
    for _ in range(w * h // 4):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), "#35333f" if rng.random() < 0.6 else "#24222c")
