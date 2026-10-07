"""Character-scale building facades (doors about 1.4x a character's height)."""
import numpy as np
from pixel import Canvas, C, mix, shade
from surfaces import ashlar_wall

SANDSTONE = ["#5a3c3a", "#7a5248", "#a06e5a", "#b47f66", "#c69478", "#dcb093"]
TRIM = ["#7d6a5e", "#a8927c", "#c6b094", "#dccaa9", "#ece0c4"]
ROOF = ["#3c1c1f", "#5c2a27", "#7e3a30", "#9a4a39", "#b5604a", "#cc7a5c"]
FRAME = "#231a26"
GLOW = ["#8a4c26", "#c47a32", "#e9a84a", "#f6cd78", "#fde9b6"]
DARKGLASS = ["#1f2236", "#2c3352", "#3e4a6e", "#6476a0"]


def roof_tiles(cv, x, y, w, h, seed=0):
    """Barrel tile roof: vertical tile rows with lit crowns, eaves line at the bottom."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, ROOF[1])
    for tx in range(x, x + w, 4):
        tone = ROOF[3] if rng.random() < 0.7 else ROOF[2]
        cv.vline(tx + 1, y, h, tone)
        cv.vline(tx + 2, y, h, shade(tone, 0.1))
        cv.vline(tx, y, h, ROOF[1])
        cv.vline(tx + 3, y, h, ROOF[0])
        for ty in range(y + int(rng.integers(0, 4)), y + h, 4):
            cv.px(tx + 1, ty, ROOF[4]); cv.px(tx + 2, ty, ROOF[5] if rng.random() < 0.5 else ROOF[4])
            cv.px(tx + 1, ty + 3, ROOF[0])
    cv.rect(x, y + h, w, 2, ROOF[0])
    cv.hline(x, y + h + 2, w, C("#0d0b16", 0.6))


def cornice(cv, x, y, w):
    cv.rect(x, y, w, 4, TRIM[2]); cv.hline(x, y, w, TRIM[4]); cv.hline(x, y + 3, w, TRIM[0])
    for dx in range(x + 2, x + w - 2, 6):
        cv.rect(dx, y + 4, 3, 2, TRIM[1]); cv.px(dx + 2, y + 5, TRIM[0])
    cv.hline(x, y + 6, w, C("#0d0b16", 0.35))


def window(cv, x, y, w, h, lit=True, arch=False, seed=0, curtain=None):
    rng = np.random.default_rng(seed)
    # stone surround
    cv.rect(x - 3, y - 3, w + 6, h + 5, TRIM[1])
    cv.hline(x - 3, y - 3, w + 6, TRIM[3]); cv.vline(x - 3, y - 3, h + 5, TRIM[2])
    if arch:
        r = w // 2 + 3
        cv.ellipse(x - 3, y - r, w + 6, r * 2, TRIM[1])
        cv.ellipse(x - 2, y - r + 1, w + 4, r * 2 - 2, TRIM[2])
        cv.rect(x + w // 2 - 2, y - r - 1, 4, 4, TRIM[3]); cv.hline(x + w // 2 - 2, y - r - 1, 4, TRIM[4])
    # frame + glass
    cv.rect(x - 1, y - 1, w + 2, h + 2, FRAME)
    if arch:
        cv.ellipse(x - 1, y - w // 2 - 1, w + 2, w + 2, FRAME)
    pal = GLOW if lit else DARKGLASS
    gx0, gy0 = x, y - (w // 2 if arch else 0)
    for yy in range(gy0, y + h):
        t = (yy - gy0) / max(1, y + h - gy0)
        c = pal[3] if t < 0.25 else pal[2] if t < 0.7 else pal[1]
        for xx in range(x, x + w):
            if arch and yy < y:
                dx, dy = xx - (x + w / 2 - 0.5), yy - y
                if dx * dx + dy * dy > (w / 2) ** 2:
                    continue
            cv.px(xx, yy, c)
    if lit:
        cv.rect(x + 1, y + 1, max(1, w // 3), max(1, h // 3), GLOW[4] if rng.random() < 0.5 else GLOW[3])
        if curtain:
            cv.rect(x, y, 2, h, curtain); cv.rect(x + w - 2, y, 2, h, curtain)
    else:
        cv.line(x + 1, y + h - 3, x + w - 3, y + 1, DARKGLASS[3])
    # muntins
    cv.vline(x + w // 2, gy0, y + h - gy0, FRAME)
    for my in range(y + h // 3, y + h, max(4, h // 3)):
        cv.hline(x, my, w, FRAME)
    # sill
    cv.rect(x - 4, y + h + 1, w + 8, 2, TRIM[3]); cv.hline(x - 4, y + h + 3, w + 8, C("#0d0b16", 0.5))


def pilaster(cv, x, y, w, h):
    cv.rect(x, y, w, h, TRIM[2])
    cv.vline(x, y, h, TRIM[4]); cv.vline(x + 1, y, h, TRIM[3]); cv.vline(x + w - 1, y, h, TRIM[0])
    for yy in range(y + 6, y + h, 9):
        cv.hline(x, yy, w, TRIM[1])
    cv.rect(x - 1, y, w + 2, 3, TRIM[3]); cv.rect(x - 1, y + h - 3, w + 2, 3, TRIM[1])


def open_doorway(cv, cx, bottom, w, h, seed=0):
    """Arched entrance with both doors swung inward and warm light inside."""
    x, top = cx - w // 2, bottom - h
    r = w // 2
    # voussoirs
    cv.ellipse(x - 7, top - 7, w + 14, w + 14, TRIM[1])
    cv.rect(x - 7, top + r, w + 14, h - r, TRIM[1])
    for i, a in enumerate(np.linspace(np.pi, 2 * np.pi, 11)):
        c = TRIM[3] if i % 2 else TRIM[2]
        for rr in range(r + 1, r + 7):
            cv.px(int(round(cx - 0.5 + np.cos(a) * rr)), int(round(top + r + np.sin(a) * rr)), c)
    cv.rect(cx - 3, top - 8, 6, 8, TRIM[4]); cv.hline(cx - 3, top, 6, TRIM[1])
    for side in (x - 7, x + w + 1):
        cv.rect(side, top + r, 6, h - r, TRIM[2]); cv.vline(side, top + r, h - r, TRIM[4])
        for yy in range(top + r + 5, bottom, 7):
            cv.hline(side, yy, 6, TRIM[1])
    # opening + interior
    cv.ellipse(x - 1, top - 1, w + 2, w + 2, FRAME)
    cv.rect(x - 1, top + r, w + 2, h - r, FRAME)
    for yy in range(top, bottom):
        t = (yy - top) / h
        c = mix(GLOW[3], GLOW[1], t * 0.8)
        for xx in range(x, x + w):
            if yy < top + r:
                dx, dy = xx - (cx - 0.5), yy - (top + r)
                if dx * dx + dy * dy > r * r:
                    continue
            cv.px(xx, yy, c)
    # inner floor and far wall
    cv.rect(x, bottom - 12, w, 12, GLOW[1]); cv.hline(x, bottom - 12, w, GLOW[2])
    for yy in range(bottom - 11, bottom, 3):
        cv.hline(x, yy, w, shade(GLOW[1], -0.15))
    cv.rect(cx - 6, top + 10, 12, 9, GLOW[4]); cv.vline(cx, top + 2, 8, FRAME); cv.rect(cx - 3, top + 18, 6, 2, FRAME)
    # doors swung open against the jambs
    for (dx, dw) in [(x, 9), (x + w - 9, 9)]:
        cv.rect(dx, top + r - 4, dw, h - r + 4, "#4a2b24")
        cv.vline(dx + (dw - 1 if dx == x else 0), top + r - 4, h - r + 4, "#2c1a1a")
        cv.rect(dx + 2, top + r, dw - 4, 10, GLOW[2]); cv.rect(dx + 2, top + r + 14, dw - 4, 12, "#6b3f2e")
        cv.hline(dx + 2, top + r + 14, dw - 4, "#8c573b")
    # threshold
    cv.rect(x - 2, bottom - 2, w + 4, 2, TRIM[3])


def steps(cv, cx, top, w, n, rise=4, spread=6):
    for i in range(n):
        sw = w + i * spread * 2
        y = top + i * rise
        cv.rect(cx - sw // 2, y, sw, rise, TRIM[2])
        cv.hline(cx - sw // 2, y, sw, TRIM[4])
        cv.hline(cx - sw // 2, y + rise - 1, sw, TRIM[0])
        cv.vline(cx - sw // 2, y, rise, TRIM[3]); cv.vline(cx + sw // 2 - 1, y, rise, TRIM[0])


def wall_lantern(cv, x, y):
    cv.rect(x - 1, y + 9, 3, 4, FRAME)
    cv.rect(x - 3, y, 7, 10, FRAME)
    cv.rect(x - 2, y + 2, 5, 6, GLOW[3]); cv.rect(x - 1, y + 3, 3, 3, GLOW[4])
    cv.poly([(x - 4, y + 1), (x, y - 3), (x + 4, y + 1)], FRAME)


def umc_facade(cv, x0, x1, base, pav0, pav1, door_bottom, seed=3):
    """Two-storey sandstone wings with a taller entrance pavilion in the middle."""
    rng = np.random.default_rng(seed)
    eave = 22
    # wings
    roof_tiles(cv, x0 - 4, eave - 16, x1 - x0 + 8, 14, seed=seed)
    ashlar_wall(cv, x0, eave, x1 - x0, base - eave, SANDSTONE, course=5, seed=seed, cap=False)
    cornice(cv, x0 - 2, eave, x1 - x0 + 4)
    cv.rect(x0, base - 6, x1 - x0, 6, TRIM[1]); cv.hline(x0, base - 6, x1 - x0, TRIM[3])
    cv.hline(x0, base, x1 - x0, C("#0d0b16", 0.5))
    # limestone quoins at the wing corners
    for qx in (x0, x1 - 7):
        for k, qy in enumerate(range(eave + 7, base - 6, 6)):
            qw = 7 if k % 2 == 0 else 5
            ox = qx if qx == x0 else x1 - qw
            cv.rect(ox, qy, qw, 5, TRIM[2]); cv.hline(ox, qy, qw, TRIM[4]); cv.hline(ox, qy + 4, qw, TRIM[0])
    # windows on the wings
    lit = [True, True, False, True, True, True, False, True, True, False]
    i = 0
    for wx in list(range(x0 + 14, pav0 - 20, 34)) + list(range(pav1 + 14, x1 - 20, 34)):
        window(cv, wx, eave + 14, 14, 20, lit=lit[i % len(lit)], seed=i)
        window(cv, wx - 1, eave + 52, 16, 34, lit=lit[(i + 3) % len(lit)], arch=True, seed=i + 40, curtain="#7e3a30")
        i += 1
    # pavilion
    pw = pav1 - pav0
    ashlar_wall(cv, pav0, 0, pw, base + 8, SANDSTONE, course=5, seed=seed + 9, cap=False)
    for px in (pav0, pav1 - 6):
        pilaster(cv, px, 0, 6, base + 8)
    cornice(cv, pav0 - 3, 30, pw + 6)
    # plaque above the door
    cv.rect(pav0 + 18, 10, pw - 36, 12, TRIM[1]); cv.rect(pav0 + 19, 11, pw - 38, 10, TRIM[2])
    for lx in range(pav0 + 23, pav1 - 23, 3):
        cv.rect(lx, 15, 2, 2, TRIM[0])
    window(cv, (pav0 + pav1) // 2 - 6, 42, 12, 16, lit=True, arch=True, seed=99)
    cx = (pav0 + pav1) // 2
    open_doorway(cv, cx, door_bottom, 40, 58, seed)
    wall_lantern(cv, cx - 30, door_bottom - 44)
    wall_lantern(cv, cx + 30, door_bottom - 44)
    # ivy on the pavilion corners
    for vx, dirn in [(pav0 + 6, 1), (pav1 - 7, -1)]:
        for _ in range(60):
            yy = int(rng.integers(40, base + 6))
            xx = vx + dirn * int(abs(rng.normal(0, 3)))
            cv.px(xx, yy, ["#2f4237", "#3f5741", "#566d4a"][int(rng.integers(3))])


BRICK = ["#3a1f22", "#5a2c2a", "#7a3a32", "#8e4636", "#a3553f", "#b8694c"]
STUCCO = ["#5e5248", "#837262", "#a08c76", "#b6a088", "#cbb69b", "#ddcaae"]
TEAL = ["#1e2f33", "#2c4a4c", "#3e6663", "#5c897c", "#86b0a0"]


def brick_wall(cv, x, y, w, h, pal=BRICK, seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, pal[1])
    for row, yy in enumerate(range(y, y + h, 4)):
        off = 0 if row % 2 else 4
        for xx in range(x - off, x + w, 8):
            x0, x1 = max(x, xx), min(x + w, xx + 7)
            if x1 <= x0:
                continue
            tone = pal[int(rng.choice([2, 3, 3, 4]))]
            cv.rect(x0, yy, x1 - x0, min(3, y + h - yy), tone)
            if rng.random() < 0.3:
                cv.px(x0 + int(rng.integers(0, x1 - x0)), yy, shade(tone, 0.12))
    cv.hline(x, y + h - 1, w, C("#0d0b16", 0.5))


def stucco_wall(cv, x, y, w, h, pal=STUCCO, seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, pal[3])
    for _ in range(w * h // 5):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), pal[int(rng.choice([2, 4]))])
    cv.hline(x, y + h - 1, w, C("#0d0b16", 0.5))


def awning(cv, x, y, w, c1, c2, depth=10):
    for i, sx in enumerate(range(x, x + w, 6)):
        c = c1 if i % 2 == 0 else c2
        cv.poly([(sx, y), (sx + 6, y), (sx + 7, y + depth), (sx - 1, y + depth)], c)
    cv.hline(x - 1, y, w + 2, shade(c1, -0.4))
    for i, sx in enumerate(range(x - 1, x + w + 1, 6)):
        c = c1 if i % 2 == 0 else c2
        cv.poly([(sx, y + depth), (sx + 6, y + depth), (sx + 3, y + depth + 3)], shade(c, -0.15))
    cv.hline(x - 1, y + depth + 4, w + 2, C("#0d0b16", 0.35))


def shop_window(cv, x, y, w, h, lit=True, goods="books", seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, FRAME)
    pal = GLOW if lit else DARKGLASS
    for yy in range(y, y + h):
        t = (yy - y) / h
        cv.hline(x, yy, w, pal[3] if t < 0.3 else pal[2] if t < 0.75 else pal[1])
    if goods == "books":
        for shelf in range(y + 8, y + h - 2, 10):
            cv.hline(x, shelf, w, "#4a2b24")
            bx = x + 1
            while bx < x + w - 2:
                bw = int(rng.integers(2, 4)); bh = int(rng.integers(5, 9))
                cv.rect(bx, shelf - bh, bw, bh, ["#7e3a30", "#425da6", "#5c897c", "#c47a2c", "#e6d6b1"][int(rng.integers(5))])
                bx += bw + (1 if rng.random() < 0.3 else 0)
    elif goods == "cafe":
        cv.rect(x + 2, y + h - 10, w - 4, 3, "#4a2b24")
        for cx in range(x + 6, x + w - 6, 14):
            cv.rect(cx, y + h - 15, 4, 5, "#e6d6b1"); cv.px(cx + 4, y + h - 13, "#e6d6b1")
        cv.rect(x + w // 2 - 1, y + 2, 2, 8, FRAME); cv.ellipse(x + w // 2 - 4, y + 9, 8, 5, GLOW[4])
    elif goods == "records":
        for rx in range(x + 3, x + w - 10, 13):
            cv.ellipse(rx, y + 6, 10, 10, "#16141f"); cv.ellipse(rx + 3, y + 9, 4, 4, ["#c84a3c", "#e8b45c", "#5c897c"][int(rng.integers(3))])
    cv.vline(x + w // 2, y, h, FRAME) if goods != "cafe" else None
    if not lit:
        cv.line(x + 2, y + h - 4, x + w // 3, y + 2, DARKGLASS[3])
    cv.rect(x - 3, y + h + 2, w + 6, 3, TRIM[1]); cv.hline(x - 3, y + h + 2, w + 6, TRIM[3])


def shop_door(cv, x, bottom, w=20, h=46, lit=True, color="#2c4a4c"):
    cv.rect(x - 2, bottom - h - 2, w + 4, h + 2, FRAME)
    cv.rect(x, bottom - h, w, h, color); cv.vline(x, bottom - h, h, shade(color, 0.2))
    pal = GLOW if lit else DARKGLASS
    cv.rect(x + 3, bottom - h + 4, w - 6, h // 2, pal[2]); cv.rect(x + 4, bottom - h + 5, (w - 8) // 2, h // 2 - 2, pal[3])
    cv.rect(x + w - 6, bottom - h // 2 + 2, 3, 2, "#e8b45c")
    cv.rect(x - 4, bottom - h - 6, w + 8, 4, TRIM[2]); cv.hline(x - 4, bottom - h - 6, w + 8, TRIM[4])


def sign_board(cv, x, y, w, label, bg="#1f1a2a", fg="#f6cd78"):
    from pixel import text, text_width
    cv.rect(x - 1, y - 1, w + 2, 14, FRAME)
    cv.rect(x, y, w, 12, bg); cv.hline(x, y, w, shade(bg, 0.25))
    text(cv, label, x + w // 2 - text_width(label) // 2, y + 1, fg)


def storefront(cv, x, w, base, top, wall="brick", sign=None, goods="books", lit=True, awn=None, seed=0, upper_lit=(True, False)):
    rng = np.random.default_rng(seed)
    if wall == "brick":
        brick_wall(cv, x, top, w, base - top, seed=seed)
    else:
        stucco_wall(cv, x, top, w, base - top, seed=seed)
    cornice(cv, x - 2, top, w + 4)
    # upper floor windows
    n = max(1, (w - 16) // 34)
    for i in range(n):
        wx = x + 12 + i * ((w - 24) // n) + ((w - 24) // n - 14) // 2
        window(cv, wx, top + 16, 14, 22, lit=upper_lit[i % len(upper_lit)], seed=seed + i)
    # ground floor: sign band, shop window, door
    band = base - 62
    if sign:
        sign_board(cv, x + 8, band, w - 16, sign)
    if awn:
        awning(cv, x + 6, band + 14, w - 12, awn[0], awn[1])
    door_w = 20
    door_x = x + w - door_w - 10
    shop_window(cv, x + 10, base - 42, door_x - x - 18, 34, lit=lit, goods=goods, seed=seed)
    shop_door(cv, door_x, base, door_w, 44, lit=lit)
    cv.rect(x, base - 3, w, 3, TRIM[1]); cv.hline(x, base - 3, w, TRIM[3])
    # downpipe at the right edge
    cv.vline(x + w - 3, top + 6, base - top - 8, "#2a2838"); cv.vline(x + w - 4, top + 6, base - top - 8, "#4d4b66")
