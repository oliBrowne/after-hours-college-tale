"""Engineering animals for the shared fauna sheet: a mule deer grazing by the creek (E01) and a
workshop mouse is borrowed from the UMC set. The deer is drawn with Canvas primitives and turned
into palette rows, two frames: head up (alert, ears turned) and head down (grazing)."""
import numpy as np
from pixel import Canvas, C

PAL = {"k": "#1a1418", "b": "#86664e", "h": "#a4826a", "d": "#5a4232", "w": "#e2d6c2", "e": "#0b070c",
       "n": "#2a1a14", "c": "#cbb8a0"}
W, H = 34, 42


def _deer(grazing):
    """Mule deer facing left: long legs, white rump and black-tipped tail, big ears, a dark brow
    over a pale muzzle. Feet on the last row."""
    cv = Canvas(W, H)
    b, h, d, w, k = PAL["b"], PAL["h"], PAL["d"], PAL["w"], PAL["k"]
    base = H - 1
    # far legs (in shadow)
    cv.line(13, 23, 13, base, d); cv.line(28, 22, 30, 31, d); cv.line(30, 31, 28, base, d)
    # body: barrel, lit back, pale belly, white rump, tail
    cv.ellipse(9, 13, 22, 12, b)
    cv.ellipse(11, 13, 17, 4, h)
    cv.ellipse(14, 21, 12, 3, PAL["c"])
    cv.hline(12, 24, 14, d)
    cv.ellipse(25, 14, 7, 9, w)
    cv.rect(31, 15, 2, 4, w); cv.rect(31, 19, 2, 2, k)
    # near legs with knees and hocks
    cv.line(10, 22, 10, base, b); cv.line(11, 22, 11, base - 6, h)
    cv.line(24, 21, 26, 30, b); cv.line(26, 30, 25, base, b); cv.line(25, 21, 27, 30, h)
    for fx in (10, 13, 25, 28):
        cv.rect(fx, base, 2, 1, PAL["n"])
    if not grazing:
        cv.poly([(10, 20), (17, 15), (12, 7), (6, 9)], b)
        cv.poly([(12, 16), (15, 15), (11, 9), (10, 10)], h)
        cv.rect(6, 11, 5, 3, w)                      # throat patch
        cv.ellipse(1, 5, 11, 6, b)
        cv.ellipse(0, 7, 4, 3, w)
        cv.px(0, 8, PAL["n"])
        cv.rect(5, 5, 4, 1, d)
        cv.px(5, 6, PAL["e"])
        cv.poly([(6, 6), (3, 0), (6, 0), (9, 5)], b); cv.line(5, 1, 7, 4, PAL["c"])       # ears in a wide V
        cv.poly([(10, 5), (12, -1), (15, 0), (12, 6)], d); cv.px(13, 1, PAL["c"])
    else:
        cv.poly([(9, 18), (15, 15), (7, 33), (3, 32)], b)
        cv.poly([(11, 17), (13, 16), (6, 31), (5, 31)], h)
        cv.ellipse(0, 31, 9, 7, b)
        cv.ellipse(0, 34, 4, 4, w)
        cv.px(0, 36, PAL["n"])
        cv.rect(3, 31, 4, 2, d)
        cv.px(4, 33, PAL["e"])
        cv.ellipse(6, 27, 4, 6, b); cv.vline(7, 29, 2, PAL["c"])
        cv.ellipse(8, 28, 5, 4, d)
        for gx in (1, 3, 6):
            cv.vline(gx, base - 2, 3, "#4e6040")
    # room for the outline on the top and both sides
    cv.a = np.pad(cv.a, ((1, 0), (1, 1), (0, 0)))
    cv.h, cv.w = cv.a.shape[:2]
    cv.outline_outside(PAL["k"])
    return cv


def _rows(cv):
    inv = {}
    for k, v in PAL.items():
        inv[tuple((np.array(C(v)[:3]) * 255).round().astype(int))] = k
    rows = []
    for y in range(cv.h):
        r = ""
        for x in range(cv.w):
            px = cv.a[y, x]
            if px[3] < 0.5:
                r += "."
                continue
            key = tuple((px[:3] * 255).round().astype(int))
            if key not in inv:
                # nearest palette colour
                best = min(inv, key=lambda c: sum((a - b_) ** 2 for a, b_ in zip(c, key)))
                key = best
            r += inv[key]
        rows.append(r)
    return rows


DEER = [_rows(_deer(False)), _rows(_deer(True))]

KINDS = [("eng_deer", DEER, PAL)]
