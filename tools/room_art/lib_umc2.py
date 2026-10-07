"""Shared pieces for the Connection (U06), the bowling alley and arcade in the UMC basement, and its
battle backdrop. Builds on lib_umc.py (U03 atrium, U05 repair landing, U07 lost property) so the
building reads as one: the same brass and oxblood enamel signs as lost property, the pink LANES neon
seen down the stair from the repair landing, the navy arcade carpet seen through lost property's
doorway, the club room's dark wainscot and its LAST LIGHT style cloth banner.

Painters that return (Canvas, anchor_x, anchor_y) follow props.py: the anchor is the floor point.
"""
import numpy as np
from scipy import ndimage
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, ground_shadow
from interior import PLASTER, PANEL, FLOOR, VELVET, NIGHT, wainscot
from lib_umc import (BRASS, PAPER, KRAFT, SAFETY, CONCRETE, BLOCK, SHADOW, EXIT_GREEN, ITEM_COLOURS,
                     halo, soft_ellipse, bolt, enamel_sign)

INK = "#171a2b"
# midnight-indigo plaster of the alley walls (the club room's plum, pushed toward blue)
INDIGO = ["#151329", "#1d1a35", "#252141", "#2d284d", "#37315a", "#453d6c"]
# retro stripe band that runs round the whole room
STRIPES = ["#f0c060", "#d9782e", "#a8403c"]
# maple lane beds and approaches
MAPLE = ["#4a2e22", "#6e4630", "#946240", "#b07a50", "#c8925e", "#dcae78", "#ecc896"]
# pins: enamel white, shade, deep shade, red neck stripes
PIN = ["#fbf4e6", "#ddd2be", "#a89c8e", "#d23a44", "#8a1e2a"]
# neon tubes: tube colour, bright core, glow
NEON_PINK = ["#5a1a3a", "#ff6aa0", "#ffd0e2", "#ff7aa8"]
NEON_TEAL = ["#123a3a", "#3ad8c8", "#d0fff6", "#58e0d0"]
NEON_GOLD = ["#5a3a10", "#ffc850", "#fff0c0", "#f6cf7a"]
# cosmic carpet: the arcade carpet of lost property's doorway (lib_umc.arcade_carpet), lifted a step
CARPET = ["#16172e", "#1f2040", "#272953", "#323466", "#3e3f7a"]
CONFETTI = ["#c45a88", "#3aa8a0", "#c8a058", "#6a5ac8"]
# molded settee shells
SHELLS = [("#c8642a", "#e8904a", "#8a3e1c"), ("#2a8a86", "#4ab8aa", "#1a5a58"), ("#b83c3c", "#dc6a5a", "#7a2228"),
          ("#d9a441", "#f0c860", "#8a6420")]
CHROME = ["#3a3a4c", "#6a6a80", "#a4a4b8", "#dcdce8"]
BALLS = [("#c4407a", "#ff8ab8"), ("#2a8a86", "#6ae0d0"), ("#5a3ab0", "#9a7ae8"), ("#d9782e", "#ffb060"),
         ("#2c4aa0", "#6a8ae0"), ("#3a8a3a", "#7ad07a"), ("#1e1a2a", "#5a5470")]


# ---------------------------------------------------------------------------------------------
# lettering
# ---------------------------------------------------------------------------------------------

def text_mask(s, scale=1):
    """Boolean mask of a string in the game font, nearest-scaled."""
    t = Canvas(len(s) * 6 + 4, 12)
    text(t, s, 1, 0, "#ffffff")
    m = t.a[..., 3] > 0.5
    ys, xs = np.where(m)
    m = m[:, xs.min():xs.max() + 1] if len(xs) else m
    m = m[ys.min():ys.max() + 1] if len(ys) else m
    if scale > 1:
        m = np.kron(m, np.ones((scale, scale), bool))
    return m


def paint_mask(cv, m, x, y, colour):
    h, w = m.shape
    full = np.zeros((cv.h, cv.w), bool)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(cv.w, x + w), min(cv.h, y + h)
    if x0 >= x1 or y0 >= y1:
        return full
    full[y0:y1, x0:x1] = m[y0 - y:y1 - y, x0 - x:x1 - x]
    cv.fill_mask(full, colour)
    return full


def neon_text(cv, s, cx, y, pal=NEON_PINK, scale=2, glow=True):
    """Bent-glass neon lettering centred on cx: a stepped glow on the wall, a dark tube shadow, the
    lit tube with a bright core along its upper-left. Returns (x0, y0, w, h) of the letters."""
    m = text_mask(s, scale)
    h, w = m.shape
    x0 = cx - w // 2
    if glow:
        pad = np.pad(m, 6)
        for r, a in [(5, 0.06), (3, 0.09), (1, 0.14)]:
            paint_mask(cv, ndimage.binary_dilation(pad, iterations=r), x0 - 6, y - 6, C(pal[3], a))
    paint_mask(cv, m, x0 + 1, y + 1, pal[0])
    paint_mask(cv, m, x0, y, pal[1])
    if scale > 1:
        # the top-left pixel of every scaled font pixel is the bright core of the tube
        core = m.copy()
        core[1::scale, :] = False
        core[:, 1::scale] = False
        paint_mask(cv, core, x0, y, pal[2])
    return (x0, y, w, h)


def lightbox(cv, x, y, w, h, label, face="#f2e2b8", ink="#7e2a26", frame=CHROME[1]):
    """A backlit sign box: chrome frame, glowing face, dark lettering."""
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, frame); cv.hline(x, y, w, CHROME[3])
    cv.rect(x + 2, y + 2, w - 4, h - 4, face)
    cv.hline(x + 2, y + 2, w - 4, shade(face, 0.4))
    cv.hline(x + 2, y + h - 3, w - 4, shade(face, -0.12))
    text(cv, label, x + w // 2 - text_width(label) // 2, y + h // 2 - 5, ink)
    for (d, a) in [(5, 0.04), (3, 0.05), (1, 0.07)]:
        cv.rect(x - 1 - d, y - 1 - d, w + 2 + 2 * d, d, C(face, a)); cv.rect(x - 1 - d, y + h + 1, w + 2 + 2 * d, d, C(face, a))
        cv.rect(x - 1 - d, y - 1, d, h + 2, C(face, a)); cv.rect(x + w + 1, y - 1, d, h + 2, C(face, a))


# ---------------------------------------------------------------------------------------------
# walls
# ---------------------------------------------------------------------------------------------

def indigo_wall(cv, x, y, w, h, seed=0):
    """Midnight-indigo plaster: clustered mottle, a stepped shade under the ceiling."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, INDIGO[2])
    for _ in range(w * h // 24):
        px, py = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        c = INDIGO[1] if rng.random() < 0.45 else INDIGO[3]
        cv.px(px, py, c)
        if rng.random() < 0.35:
            cv.px(px + 1, py, c)
    for (hh, a) in [(12, 0.12), (6, 0.12), (3, 0.14)]:
        cv.rect(x, y, w, hh, C("#0a0816", a))


def stripe_band(cv, x, y, w):
    """The retro triple stripe (amber, orange, rust) on a dark ground, 9 px tall."""
    cv.rect(x, y, w, 9, "#14101e")
    for i, c in enumerate(STRIPES):
        cv.rect(x, y + 1 + i * 3, w, 2, c)
        cv.hline(x, y + 1 + i * 3, w, shade(c, 0.18))
    cv.hline(x, y + 9, w, C(SHADOW, 0.5))


def ceiling_soffit(cv, x, w, h=8, cans=()):
    """Dark ceiling edge with a lip and recessed downlights (off after closing)."""
    cv.rect(x, 0, w, h, "#100d1a")
    cv.hline(x, h - 2, w, "#2a2438"); cv.hline(x, h - 1, w, "#3a3248")
    cv.hline(x, h, w, C(SHADOW, 0.6))
    for cx in cans:
        cv.rect(cx - 3, h - 2, 7, 2, "#4a4458"); cv.rect(cx - 2, h - 2, 5, 1, "#6a6278")


def shoe_cubbies(cv, x, y, w, h, cols=3, seed=0):
    """Built-in shoe-hire cubbies: a wooden case of square holes, each with a pair of two-tone
    bowling shoes (or empty), a size tag on every shelf edge."""
    rng = np.random.default_rng(seed)
    cv.rect(x - 1, y - 1, w + 2, h + 1, OUT)
    cv.rect(x, y, w, h, PANEL[3]); cv.hline(x, y, w, PANEL[5]); cv.vline(x, y, h, PANEL[4])
    cv.rect(x - 2, y - 4, w + 4, 4, PANEL[4]); cv.hline(x - 2, y - 4, w + 4, PANEL[5]); cv.hline(x - 2, y - 1, w + 4, PANEL[1])
    cw = (w - 2) // cols
    rows = (h - 4) // 14
    shoes = [("#b8403c", "#e6d6b1"), ("#3a5ab8", "#c49a68"), ("#8a5a3a", "#d8b888"), ("#2a8a86", "#1e1a2a"),
             ("#d8c8a8", "#b8403c"), ("#2a2436", "#c8a058"), ("#c8642a", "#2a2436")]
    size = 4
    for r in range(rows):
        for c in range(cols):
            hx, hy = x + 2 + c * cw, y + 2 + r * 14
            cv.rect(hx, hy, cw - 2, 12, "#1a1016")
            cv.hline(hx, hy, cw - 2, "#120a10")
            cv.rect(hx, hy + 11, cw - 2, 1, PANEL[1])
            if rng.random() < 0.82:
                body, trim = shoes[int(rng.integers(len(shoes)))]
                # a pair stacked heel to toe, seen from the side: heel cap in the second colour,
                # collar dipping to the toe, lace eyelets, a pale sole
                for k in (0, 1):
                    sx, sy = hx + 1 + k, hy + 1 + k * 5
                    sl = cw - 5
                    cv.rect(sx, sy + 1, sl, 4, OUT); cv.rect(sx + 1, sy, 3, 1, OUT)
                    cv.rect(sx + 1, sy + 1, sl - 2, 2, body); cv.rect(sx + 1, sy + 1, 3, 2, trim)
                    cv.px(sx + sl - 2, sy + 1, OUT)
                    cv.px(sx + 5, sy + 1, shade(body, 0.45))
                    cv.hline(sx + 1, sy + 3, sl - 2, shade(body, -0.25))
                    cv.hline(sx, sy + 4, sl, "#cfc6b4")
            # brass size tag on the shelf lip
            cv.rect(hx + cw // 2 - 3, hy + 11, 5, 2, BRASS[3])
            cv.px(hx + cw // 2 - 2, hy + 11, BRASS[4])
            size += 1
    cv.rect(x, y + h - 2, w, 2, PANEL[1])


def service_door(cv, cx, base, w=46, h=64, plate="CLUB"):
    """Blue-grey steel service door in a steel frame (the other end of the club room's STAFF door),
    a wired window with warm stair light behind it, push bar, a cream plate and a green lamp."""
    x0 = cx - w // 2
    top = base - h
    cv.rect(x0 - 4, top - 4, w + 8, h + 4, OUT)
    cv.rect(x0 - 3, top - 3, w + 6, h + 3, "#4a5a68"); cv.hline(x0 - 3, top - 3, w + 6, "#7a8a98")
    cv.vline(x0 - 3, top - 3, h + 3, "#6a7a88"); cv.vline(x0 + w + 2, top - 3, h + 3, "#33404c")
    cv.rect(x0, top, w, h, "#3a4a5a"); cv.hline(x0, top, w, "#56687a"); cv.vline(x0, top, h, "#4a5c6e")
    cv.vline(x0 + w - 1, top, h, "#2a3644")
    # wired-glass window, warm light from the stair to the club
    wx, wy, ww, wh = cx - 8, top + 7, 16, 20
    cv.rect(wx - 1, wy - 1, ww + 2, wh + 2, "#22303c")
    cv.rect(wx, wy, ww, wh, "#e9a84a")
    cv.rect(wx, wy, ww, 8, "#f6cd78"); cv.rect(wx + 2, wy + 1, 5, 4, "#fde9b6")
    cv.poly([(wx, wy + wh), (wx + ww, wy + 9), (wx + ww, wy + wh)], "#c47a32")   # the stair's shadow
    for gx in range(wx + 3, wx + ww, 4):
        for gy in range(wy + 2, wy + wh, 4):
            cv.px(gx, gy, C("#5a4a3a", 0.6))
    # push bar, hinges, kick plate
    cv.rect(x0 + 4, top + h // 2 + 4, w - 8, 3, OUT); cv.rect(x0 + 5, top + h // 2 + 4, w - 10, 2, "#c0c4cc")
    cv.hline(x0 + 5, top + h // 2 + 4, w - 10, "#e8ecf0")
    for hy in (top + 6, top + h - 12):
        cv.rect(x0 - 1, hy, 2, 5, "#8a96a4")
    cv.rect(x0 + 2, base - 8, w - 4, 7, "#5a6a7a"); cv.hline(x0 + 2, base - 8, w - 4, "#8a9aaa")
    # plate
    pw = text_width(plate) + 6
    cv.rect(cx - pw // 2, top + h // 2 + 12, pw, 10, "#e6d6b1"); cv.hline(cx - pw // 2, top + h // 2 + 12, pw, "#fff3d6")
    text(cv, plate, cx - text_width(plate) // 2, top + h // 2 + 12, "#7e3a30")
    # green lamp over the frame
    cv.rect(cx - 6, top - 7, 12, 3, OUT); cv.rect(cx - 5, top - 6, 10, 2, "#5cc28a")
    halo(cv, cx, top - 5, 9, colour="#5cc28a", strength=0.08)


def service_landing(cv, cx, top, bottom, w0=54, grow=6, n=3):
    """Concrete steps from a service door down to the floor (toward the viewer): each a lit tread,
    yellow nosing and a darker riser, a little wider than the one above."""
    step = (bottom - top) // n
    for i in range(n):
        y = top + i * step
        w = w0 + i * grow
        x = cx - w // 2
        cv.rect(x - 1, y, w + 2, step, OUT)
        cv.rect(x, y, w, step - 4, CONCRETE[5]); cv.hline(x, y, w, CONCRETE[6])
        for k in range(x + 3, x + w - 2, 7):
            cv.px(k, y + 2 + (k % 3), CONCRETE[4])
        cv.rect(x, y + step - 4, w, 1, SAFETY[2]); cv.hline(x, y + step - 3, w, SAFETY[1])
        cv.rect(x, y + step - 2, w, 2, CONCRETE[2])
    soft_ellipse(cv, cx, bottom + 1, w0 // 2 + n * grow // 2 + 2, 2, SHADOW, 0.35)


def panel_door(cv, cx, base, w=46, h=66, window="#f6cf7a"):
    """Panelled wooden door (lost property side of the building) with a frosted, lamp-lit upper
    pane, brass knob and kick plate, in a sandstone-and-wood architrave."""
    x0 = cx - w // 2
    top = base - h
    cv.rect(x0 - 5, top - 6, w + 10, h + 6, OUT)
    cv.rect(x0 - 4, top - 5, w + 8, h + 5, PANEL[4]); cv.hline(x0 - 4, top - 5, w + 8, PANEL[5])
    cv.vline(x0 - 4, top - 5, h + 5, PANEL[5]); cv.vline(x0 + w + 3, top - 5, h + 5, PANEL[2])
    cv.rect(x0 - 6, top - 8, w + 12, 3, PANEL[3]); cv.hline(x0 - 6, top - 8, w + 12, PANEL[5])
    cv.rect(x0, top, w, h, PANEL[2]); cv.hline(x0, top, w, PANEL[3])
    # frosted pane with the room's warm light and the shadow of coats on their rail
    px, py, pw, ph = x0 + 6, top + 6, w - 12, 22
    cv.rect(px - 1, py - 1, pw + 2, ph + 2, PANEL[1])
    cv.rect(px, py, pw, ph, window); cv.rect(px, py, pw, 5, shade(window, 0.35))
    # gold-leaf lettering on the frosted glass, the blur of coats on their rail behind it
    for k in range(px + 3, px + pw - 3, 6):
        cv.rect(k, py + 14, 4, 7, C("#a8743a", 0.35))
    cv.hline(px + 2, py + 13, pw - 4, C("#8a5a2a", 0.4))
    text(cv, "CLAIM", cx - 15, py + 2, "#6a3a18")
    halo(cv, cx, py + ph // 2, 30, colour=window, strength=0.05)
    # lower panels
    for (ppx, ppy, ppw, pph) in [(x0 + 5, top + 33, w // 2 - 7, h - 42), (cx + 2, top + 33, w // 2 - 7, h - 42)]:
        cv.rect(ppx, ppy, ppw, pph, PANEL[1]); cv.rect(ppx + 1, ppy + 1, ppw - 2, pph - 2, PANEL[3])
        cv.hline(ppx + 1, ppy + 1, ppw - 2, PANEL[4])
    cv.rect(x0 + w - 8, top + h // 2 + 2, 4, 4, BRASS[2]); cv.px(x0 + w - 8, top + h // 2 + 2, BRASS[4])
    cv.rect(x0 + 2, base - 7, w - 4, 6, BRASS[2]); cv.hline(x0 + 2, base - 7, w - 4, BRASS[4]); cv.hline(x0 + 2, base - 2, w - 4, BRASS[1])
    # light leaking under the door
    cv.hline(x0 + 2, base - 1, w - 4, "#f6cf7a")


def league_pennants(cv, x0, x1, y, sag=6, every=9, seed=0):
    """A string of league pennants hung under the ceiling, in the stripe colours and the neons."""
    rng = np.random.default_rng(seed)
    cols = STRIPES + ["#3aa8a0", "#c4407a", "#e6d6b1"]
    n = x1 - x0
    for i in range(n + 1):
        t = i / n
        xx, yy = x0 + i, y + int(round(sag * 4 * t * (1 - t)))
        cv.px(xx, yy, "#2a2232")
        if i % every == every // 2 and 2 < i < n - 2:
            c = cols[int(rng.integers(len(cols)))]
            cv.poly([(xx - 3, yy + 1), (xx + 3, yy + 1), (xx, yy + 7)], OUT)
            cv.poly([(xx - 2, yy + 1), (xx + 2, yy + 1), (xx, yy + 5)], c)
            cv.px(xx - 1, yy + 1, shade(c, 0.3))


def floor_litter(cv, items):
    """Small flat things dropped on the carpet: (x, y, kind) with kind token, card, pencil, straw,
    shoe or wrapper."""
    for (fx, fy, kind) in items:
        if kind == "token":
            cv.rect(fx, fy, 4, 3, OUT); cv.rect(fx + 1, fy, 2, 2, BRASS[3]); cv.px(fx + 1, fy, BRASS[4])
        elif kind == "card":
            cv.rect(fx, fy, 10, 6, PAPER[3]); cv.hline(fx, fy, 10, "#ffffff")
            for gx in range(fx + 2, fx + 10, 3):
                cv.vline(gx, fy + 1, 4, C("#425da6", 0.5))
            cv.hline(fx + 1, fy + 6, 10, C(SHADOW, 0.4))
        elif kind == "pencil":
            cv.line(fx, fy, fx + 6, fy - 2, "#e8b45c"); cv.px(fx + 6, fy - 2, "#3a2a26"); cv.px(fx, fy, "#e88aa0")
        elif kind == "straw":
            cv.line(fx, fy, fx + 7, fy + 1, "#e6d6b1"); cv.px(fx + 2, fy, "#c84a3c"); cv.px(fx + 5, fy + 1, "#c84a3c")
        elif kind == "wrapper":
            cv.rect(fx, fy, 5, 3, "#c84a3c"); cv.px(fx + 1, fy + 1, "#f6cf7a"); cv.px(fx + 4, fy, "#e6d6b1")
        elif kind == "shoe":
            # one bowling shoe nobody came back for, on its side
            cv.rect(fx, fy, 11, 5, OUT); cv.rect(fx + 1, fy - 1, 4, 1, OUT)
            cv.rect(fx + 1, fy, 9, 3, "#b8403c"); cv.rect(fx + 1, fy, 3, 3, "#e6d6b1")
            cv.px(fx + 5, fy, "#e8e0d0"); cv.px(fx + 7, fy, "#e8e0d0")
            cv.hline(fx, fy + 4, 11, "#d8d0c0"); cv.hline(fx + 1, fy + 5, 11, C(SHADOW, 0.4))


# ---------------------------------------------------------------------------------------------
# the lanes
# ---------------------------------------------------------------------------------------------

PIN_ROWS = [
    ".WWs.",
    ".WWs.",
    "..W..",
    ".rRr.",
    ".WWs.",
    "WWWws",
    "WWWws",
    "WWWws",
    "WWwws",
    ".Wws.",
    ".sss.",
]


def pin(cv, cx, base, lit=1.0):
    """One bowling pin standing with its foot at (cx, base): 5 x 11 px, lit from the upper left."""
    pal = {"W": PIN[0], "w": PIN[1], "s": PIN[2], "r": PIN[3], "R": PIN[4]}
    for yy, row in enumerate(PIN_ROWS):
        for xx, ch in enumerate(row):
            if ch == ".":
                continue
            c = pal[ch]
            if lit < 1.0:
                c = mix(c, "#2a2440", 1.0 - lit)
            cv.px(cx - 2 + xx, base - len(PIN_ROWS) + yy, c)


def pin_triangle(cv, cx, back, spacing=10, row_dy=5, missing=(), lit=1.0, chalk=True):
    """Ten pins (back row of four first). missing: indices 0-9 left empty, a chalk ring on the deck."""
    spots = []
    for row, n in enumerate((4, 3, 2, 1)):
        for k in range(n):
            spots.append((cx + int((k - (n - 1) / 2) * spacing), back + row * row_dy))
    for i, (px, py) in enumerate(spots):
        cv.hline(px - 2, py, 5, C(SHADOW, 0.45))
        if i in missing:
            if chalk:
                soft_ellipse(cv, px, py - 1, 3, 1, "#f6ecd2", 0.55)
                cv.px(px, py - 1, C(MAPLE[1], 0.8))
            continue
        pin(cv, px, py, lit=lit)
    return spots


def lane_bed(cv, x0, x1, y0, y1, foul, seed=0, reflect=True):
    """Maple lane boards (one pixel per board), the targeting arrows and dots, darker toward the
    pins, with the pin lights reflected down the oiled boards."""
    rng = np.random.default_rng(seed)
    w = x1 - x0
    for yy in range(y0, y1):
        t = (yy - y0) / max(1, y1 - y0)            # 0 at the pins, 1 at the foul line
        base = mix(MAPLE[3], MAPLE[4], 0.3 + 0.7 * t)
        cv.hline(x0, yy, w, base)
    # boards: every board its own faint tone, long splice marks
    for b in range(w):
        tone = float(rng.choice([-0.05, -0.02, 0.0, 0.02, 0.04]))
        if tone:
            cv.rect(x0 + b, y0, 1, y1 - y0, C(shade(MAPLE[4], tone), 0.35))
        if b % 3 == 2:
            cv.rect(x0 + b, y0, 1, y1 - y0, C(MAPLE[2], 0.18))
        for _ in range(2):
            sy = y0 + int(rng.integers(0, y1 - y0 - 4))
            cv.vline(x0 + b, sy, 1, C(MAPLE[2], 0.5))
    # the oil: a glossy streak down the middle, pin lights reflected near the deck
    if reflect:
        cx = (x0 + x1) // 2
        for (ww, a) in [(w - 12, 0.05), (w - 22, 0.05), (6, 0.06)]:
            cv.rect(cx - ww // 2, y0, ww, y1 - y0, C("#fff4dc", a))
        for (hh, a) in [(30, 0.1), (18, 0.1), (8, 0.12)]:
            cv.rect(x0 + 3, y0, w - 6, hh, C("#ffe8c0", a))
    # arrows at a quarter of the length from the foul line, dots in front of them
    ay = foul - int((foul - y0) * 0.27)
    cx = (x0 + x1) // 2
    for k in range(-3, 4):
        bx = cx + k * 5
        yy = ay + abs(k) * 3
        cv.px(bx, yy - 2, MAPLE[0]); cv.hline(bx - 1, yy - 1, 3, MAPLE[0]); cv.hline(bx - 1, yy, 3, MAPLE[1])
    for k in (-2, -1, 1, 2):
        cv.px(cx + k * 5 + (1 if k > 0 else -1) * 2, foul - 12, MAPLE[0])
    # foul line
    cv.hline(x0, foul, w, "#1a1220"); cv.hline(x0, foul + 1, w, MAPLE[1])


def gutter(cv, x, y0, y1, w=5):
    """A rounded channel: dark trough, lit lip on the lane side."""
    cv.rect(x, y0, w, y1 - y0, "#2a2232")
    cv.vline(x + w // 2, y0, y1 - y0, "#1a141f")
    cv.vline(x, y0, y1 - y0, "#4a4058"); cv.vline(x + w - 1, y0, y1 - y0, "#3a3246")


def capping(cv, x, y0, y1, w=11):
    """The raised division between two lanes (ball-return capping): charcoal with a lit top edge."""
    cv.rect(x, y0, w, y1 - y0, "#24202e")
    cv.vline(x + 1, y0, y1 - y0, "#4a4458"); cv.vline(x + 2, y0, y1 - y0, "#3a3448")
    cv.vline(x + w - 1, y0, y1 - y0, "#16121c")
    for yy in range(y0 + 10, y1, 26):
        cv.rect(x + w // 2 - 1, yy, 2, 1, "#5a5468")


def masking_mural(cv, x, y, w, h, seed=0):
    """The masking panels over the pin decks, painted as one cosmic-bowling mural: a violet night
    over the Flatirons, a ringed planet, a crescent moon and bowling-ball comets rolling across.
    Returns the bright star points (for a twinkle layer)."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, "#1a1640")
    bands = ["#1a1640", "#211a4c", "#2a1f58", "#352462", "#43296a"]
    bh = h / len(bands)
    for i, c in enumerate(bands):
        cv.rect(x, y + int(i * bh), w, int(bh) + 1, c)
        if i:
            for xx in range(x, x + w, 2):
                cv.px(xx + (i % 2), y + int(i * bh), bands[i - 1])
    stars = []
    for _ in range(w * h // 70):
        sx, sy = x + int(rng.integers(2, w - 2)), y + int(rng.integers(2, h - 16))
        cv.px(sx, sy, "#8a86c8" if rng.random() < 0.6 else "#c8c4f0")
    for _ in range(14):
        sx, sy = x + int(rng.integers(6, w - 6)), y + int(rng.integers(3, h - 20))
        cv.px(sx, sy, "#fff4dc"); cv.px(sx - 1, sy, "#8a86c8"); cv.px(sx + 1, sy, "#8a86c8")
        cv.px(sx, sy - 1, "#8a86c8"); cv.px(sx, sy + 1, "#8a86c8")
        stars.append((sx, sy))
    # ringed planet, left
    px, py = x + 54, y + 20
    cv.ellipse(px - 8, py - 8, 17, 17, "#3a7aa8"); cv.ellipse(px - 7, py - 7, 13, 13, "#58a0c8")
    cv.ellipse(px - 5, py - 6, 7, 6, "#8ad0e8")
    cv.hline(px - 7, py - 1, 15, "#2a5a88"); cv.hline(px - 6, py + 3, 13, "#2a5a88")
    for k in range(-14, 15):
        ry = int(round(k * 0.22))
        if abs(k) > 7 or ry > 0:
            cv.px(px + k, py + ry + 1, "#e8c070")
            cv.px(px + k, py + ry + 2, "#b88a48")
    # crescent moon, right
    mx, my = x + w - 58, y + 16
    cv.ellipse(mx - 7, my - 7, 15, 15, "#f6e7c4"); cv.ellipse(mx - 3, my - 9, 15, 15, bands[0])
    # bowling-ball comets: a ball with finger holes, a stepped tail streaming behind it
    for (bx, by, tail, col, tc) in [(x + 150, y + 14, 34, "#c4407a", "#ff8ab8"), (x + 268, y + 26, 28, "#2a8a86", "#6ae0d0"),
                                    (x + w - 110, y + 10, 22, "#5a3ab0", "#9a7ae8")]:
        for i, (ln, a) in enumerate([(tail, 0.25), (tail * 2 // 3, 0.4), (tail // 3, 0.6)]):
            cv.rect(bx - ln, by - 2 + i // 2, ln, 4 - i, C(tc, a))
        cv.ellipse(bx - 4, by - 4, 9, 9, OUT); cv.ellipse(bx - 3, by - 3, 7, 7, col)
        cv.px(bx - 2, by - 2, tc); cv.px(bx - 1, by - 2, tc)
        cv.px(bx + 1, by - 1, OUT); cv.px(bx + 2, by, OUT); cv.px(bx + 1, by + 1, OUT)
    # Flatirons and pines along the bottom, the campus roofline lit here and there
    base = y + h
    ridge = []
    for i, xx in enumerate(range(x, x + w + 1, 4)):
        ridge.append((xx, base - 14 - 4 * np.sin(i * 0.37) - 3 * np.sin(i * 1.1)))
    cv.poly(ridge + [(x + w, base), (x, base)], "#241a3c")
    for k, sx in enumerate(range(x + 170, x + 260, 18)):
        tip = base - 30 - (k % 2) * 5
        cv.poly([(sx, base - 14), (sx + 10, tip), (sx + 18, base - 14)], "#3a2850")
        cv.line(sx + 2, base - 15, sx + 10, tip + 1, "#6a4a7a")
    for xx in range(x, x + w, 6):
        th = int(rng.integers(3, 9))
        cv.poly([(xx, base - 6), (xx + 3, base - 6 - th), (xx + 6, base - 6)], "#18142a")
    cv.rect(x, base - 6, w, 6, "#18142a")
    for _ in range(w // 12):
        cv.px(x + int(rng.integers(0, w)), base - 4 - int(rng.integers(0, 2)), "#e9a84a")
    return stars


def club_banner(cv, cx, y, label="ONE ROUND / ONE PROMISE", rope=12):
    """A cloth banner tied across, cream with oxblood letters and a scalloped hem (the club room's
    LAST LIGHT banner is its sister)."""
    w = text_width(label) + 16
    x0 = cx - w // 2
    cv.line(x0, y, x0 - rope, y - 6, "#3a2a2a"); cv.line(x0 + w - 1, y, x0 + w - 1 + rope, y - 6, "#3a2a2a")
    cv.rect(x0, y, w, 13, "#e6d6b1"); cv.hline(x0, y, w, "#fff3d6"); cv.hline(x0, y + 12, w, "#b8a888")
    for sx in range(x0, x0 + w - 1, 12):
        cv.poly([(sx, y + 13), (sx + 6, y + 16), (sx + 12, y + 13)], "#d4c4a0")
    for k in (x0 + 3, x0 + w - 4):
        cv.px(k, y + 2, BRASS[3])
    text(cv, label, cx - text_width(label) // 2, y + 2, "#7e3a30")
    return (x0, y, w, 16)


def lane_number(cv, cx, y, n, lit="#f6cf7a"):
    """Backlit lane number plate under the masking."""
    cv.rect(cx - 6, y, 13, 11, OUT)
    cv.rect(cx - 5, y + 1, 11, 9, "#14101e")
    text(cv, str(n), cx - 2, y + 1, lit)
    cv.hline(cx - 5, y + 10, 11, CHROME[1])


def pit_cavity(cv, x0, x1, top, bottom):
    """The dark opening of the pinsetter over a pin deck: the machine's silhouette, the raised sweep
    bar, the deck light washing down onto the pins."""
    w = x1 - x0
    cv.rect(x0, top, w, bottom - top, "#0c0a14")
    # the pinsetter: turret and deck plate silhouettes, a little lit
    cv.rect(x0 + 4, top + 3, w - 8, 6, "#16121e"); cv.hline(x0 + 4, top + 8, w - 8, "#241e30")
    cv.ellipse(x0 + w // 2 - 9, top + 6, 18, 10, "#14101c"); cv.ellipse(x0 + w // 2 - 7, top + 7, 14, 7, "#1e1828")
    # deck light: a hidden strip under the masking throws light down onto the deck
    cv.rect(x0 + 2, top, w - 4, 2, "#fff0c8"); cv.hline(x0 + 2, top + 2, w - 4, "#a8946a")
    for i, a in enumerate([0.06, 0.08, 0.1, 0.12]):
        yy = top + 3 + i * (bottom - top - 3) // 4
        cv.rect(x0 + 1, yy, w - 2, bottom - yy, C("#ffe8c0", a))
    # the sweep bar parked up, its yellow edge
    sy = top + 14
    cv.rect(x0 + 1, sy, w - 2, 3, "#2a2432"); cv.hline(x0 + 1, sy + 2, w - 2, SAFETY[1])


def kickback(cv, x, top, bottom, w=11):
    """The side panels between pin decks: black laminate with a chrome edge and a dark shadow."""
    cv.rect(x, top, w, bottom - top, "#16121e")
    cv.vline(x + 1, top, bottom - top, CHROME[1]); cv.vline(x + 2, top, bottom - top, "#2a2636")
    cv.vline(x + w - 1, top, bottom - top, "#0a0810")
    cv.rect(x, bottom - 2, w, 2, "#2a2636")


def approach(cv, x0, x1, y0, y1, bays, seed=0):
    """The approaches: maple boards running across (one wide floor), seams at each lane's edge,
    the two rows of approach dots, a lit nosing where it steps down to the carpet."""
    rng = np.random.default_rng(seed)
    for yy in range(y0, y1):
        cv.hline(x0, yy, x1 - x0, MAPLE[4] if (yy - y0) % 5 else MAPLE[3])
    for _ in range((x1 - x0) * (y1 - y0) // 20):
        px, py = x0 + int(rng.integers(0, x1 - x0)), y0 + int(rng.integers(0, y1 - y0))
        cv.hline(px, py, int(rng.integers(2, 6)), C(MAPLE[3], 0.6))
    for (bx, cx) in bays:
        cv.vline(bx, y0, y1 - y0, C(MAPLE[2], 0.7))
        for dy in (12, 26):
            for k in (-10, -5, 0, 5, 10):
                cv.px(cx + k, y0 + dy, MAPLE[1])
    cv.rect(x0, y1, x1 - x0, 2, MAPLE[5]); cv.rect(x0, y1 + 2, x1 - x0, 2, MAPLE[1])
    cv.hline(x0, y1 + 4, x1 - x0, C(SHADOW, 0.5))
    # sheen
    for (hh, a) in [(8, 0.08), (4, 0.08)]:
        cv.rect(x0, y0, x1 - x0, hh, C("#fff4dc", a))


def practice_alcove(cv, cx, top, base, w=44, missing=(0,)):
    """A small recess in the wall for the practice deck: lit from above, nine pins and a chalk ring
    where the tenth used to stand."""
    x0 = cx - w // 2
    cv.rect(x0 - 3, top - 3, w + 6, base - top + 3, OUT)
    cv.rect(x0 - 2, top - 2, w + 4, base - top + 2, CHROME[1]); cv.hline(x0 - 2, top - 2, w + 4, CHROME[3])
    pit_cavity(cv, x0, x0 + w, top, base)
    cv.rect(x0, base - 6, w, 6, MAPLE[4]); cv.hline(x0, base - 6, w, MAPLE[5])
    return pin_triangle(cv, cx, base - 14, spacing=9, row_dy=4, missing=missing)


def ball_rack(cv, x, base, w=36, seed=0):
    """A two-tier rack of house balls against the wall: chrome rails, marbled balls with finger holes."""
    rng = np.random.default_rng(seed)
    top = base - 34
    for lx in (x + 1, x + w - 3):
        cv.rect(lx, top, 3, base - top, OUT); cv.vline(lx + 1, top + 1, base - top - 1, CHROME[2])
    for tier, ty in enumerate((top + 12, base - 4)):
        cv.rect(x, ty, w, 3, OUT); cv.hline(x + 1, ty + 1, w - 2, CHROME[2]); cv.hline(x + 1, ty, w - 2, CHROME[3])
        bx = x + 3
        while bx + 10 <= x + w - 1:
            col, hi = BALLS[int(rng.integers(len(BALLS)))]
            cv.ellipse(bx, ty - 10, 10, 10, OUT); cv.ellipse(bx + 1, ty - 9, 8, 8, col)
            cv.px(bx + 3, ty - 8, hi); cv.px(bx + 2, ty - 7, hi)
            for _ in range(3):
                cv.px(bx + 2 + int(rng.integers(0, 6)), ty - 8 + int(rng.integers(0, 6)), shade(col, 0.2))
            cv.px(bx + 5, ty - 6, OUT); cv.px(bx + 6, ty - 5, OUT); cv.px(bx + 5, ty - 4, OUT)
            bx += 11
    return (x, top, w, base - top)


def neon_pin(cv, cx, y, h=40, pal=NEON_PINK):
    """A neon bowling-pin outline on the wall."""
    pts = []
    prof = [(0.0, 2), (0.08, 3), (0.16, 2), (0.24, 1.5), (0.34, 2.5), (0.55, 5), (0.75, 5), (0.92, 3.5), (1.0, 3)]
    for t, r in prof:
        pts.append((t, r))
    m = np.zeros((h + 2, 16), bool)
    for yy in range(h):
        t = yy / (h - 1)
        for (t0, r0), (t1, r1) in zip(pts, pts[1:]):
            if t0 <= t <= t1:
                r = r0 + (r1 - r0) * (t - t0) / max(1e-6, t1 - t0)
                break
        r = int(round(r))
        m[yy + 1, 8 - r] = True; m[yy + 1, 8 + r] = True
    m[1, 6:11] = True; m[h, 5:12] = True
    for r, a in [(3, 0.06), (1, 0.1)]:
        paint_mask(cv, ndimage.binary_dilation(np.pad(m, 4), iterations=r), cx - 12, y - 4, C(pal[3], a))
    paint_mask(cv, m, cx - 8 + 1, y + 1, pal[0])
    paint_mask(cv, m, cx - 8, y, pal[1])
    # the red neck stripes in a second tube
    yy = y + int(h * 0.2)
    cv.hline(cx - 2, yy, 5, NEON_GOLD[1]); cv.hline(cx - 2, yy + 2, 5, NEON_GOLD[1])


# ---------------------------------------------------------------------------------------------
# floor
# ---------------------------------------------------------------------------------------------

def cosmic_carpet(cv, x, y, w, h, seed=0):
    """Bowling-alley carpet: the navy of lost property's doorway peek (arcade_carpet) with its neon
    zigzag weave, and the cosmic motifs it is known for laid on a staggered grid: ringed planets,
    four-point stars, comet swooshes and dot clusters."""
    rng = np.random.default_rng(seed)
    target, tx, ty = cv, x, y
    cv = Canvas(w, h)
    x, y = 0, 0
    reg = cv.a
    reg[:] = C(CARPET[2])
    ys, xs = np.mgrid[0:h, 0:w]
    k = xs % 8
    zig = (ys - 3) % 8 == (np.where(k < 4, k, 8 - k) // 2)
    reg[(ys % 16 < 8) & ~zig] = C(mix(CARPET[2], CARPET[1], 0.45))
    reg[zig] = C(CARPET[3])
    cw, ch = 34, 22
    for gy in range(-1, h // ch + 2):
        for gx in range(-1, w // cw + 2):
            ox = x + gx * cw + (cw // 2 if gy % 2 else 0)
            oy = y + gy * ch
            kind = (gx + 2 * gy) % 4
            mx, my = ox + int(rng.integers(-3, 4)), oy + int(rng.integers(-2, 3))
            if kind == 0:      # ringed planet
                c, hi = "#3aa8a0", "#7ad8cc"
                cv.rect(mx - 2, my - 1, 5, 3, c); cv.rect(mx - 1, my - 2, 3, 5, c)
                cv.px(mx - 1, my - 1, hi); cv.px(mx, my - 2, hi)
                for d in range(-5, 6):
                    if abs(d) > 1:
                        cv.px(mx + d, my + (1 if d > 0 else 0) - (d // 4), "#c8a058")
            elif kind == 1:    # four-point star
                c = "#d0609a"
                cv.px(mx, my, "#ffd0e2")
                for d in (1, 2):
                    cv.px(mx - d, my, c); cv.px(mx + d, my, c); cv.px(mx, my - d, c); cv.px(mx, my + d, c)
                cv.px(mx - 3, my, C(c, 0.5)); cv.px(mx + 3, my, C(c, 0.5))
            elif kind == 2:    # comet swoosh
                c = "#7a6ad8"
                for i in range(9):
                    cv.px(mx - 4 + i, my + int(round(2.2 * ((i - 4) / 4.0) ** 2)) - 1, c if i > 2 else C(c, 0.55))
                cv.rect(mx + 4, my, 2, 2, "#c8a058")
            else:              # cluster of dots
                for (dx, dy, c) in [(-2, 0, "#c8a058"), (1, -1, "#3aa8a0"), (2, 2, "#d0609a")]:
                    cv.px(mx + dx, my + dy, c)
            # a little confetti between motifs
            for _ in range(2):
                fx, fy = ox + int(rng.integers(8, cw - 8)) - cw // 2, oy + ch // 2 + int(rng.integers(-4, 5))
                cv.rect(fx, fy, 2, 1, C(CONFETTI[int(rng.integers(4))], 0.7))
    target.paste(cv, tx, ty)


def worn_path(cv, pts, rx, ry, colour="#8a86c8", alpha=0.05):
    """Walked-pale trails across the carpet (two stepped bands per stop)."""
    for (cx, cy) in pts:
        soft_ellipse(cv, cx, cy, rx, ry, colour, alpha)
        soft_ellipse(cv, cx, cy, int(rx * 0.6), int(ry * 0.6), colour, alpha)


def chip_rug(cv, x, y, w, h, label="CHIP'S CORNER"):
    """The rug of Chip's corner: black with a gold border, a charging buffalo in gold, the name
    woven along the front edge."""
    cv.rect(x - 1, y - 1, w + 2, h + 2, C(SHADOW, 0.5))
    cv.rect(x, y, w, h, "#1a1418")
    cv.rect(x + 2, y + 2, w - 4, h - 4, "#c8a058"); cv.rect(x + 4, y + 4, w - 8, h - 8, "#1a1418")
    cv.rect(x + 6, y + 6, w - 12, h - 12, "#241c20")
    for xx in range(x + 8, x + w - 8, 6):
        cv.px(xx, y + 7, "#5a4428"); cv.px(xx + 3, y + h - 8, "#5a4428")
    for fx in range(x, x + w, 2):
        cv.px(fx, y - 2, "#c8a058"); cv.px(fx, y + h + 1, "#c8a058")
    buffalo(cv, x + w - 34, y + h - 7)
    text(cv, label, x + 12, y + h - 17, "#d9b060")


def buffalo(cv, cx, by, gold="#d9b060", dark="#9a7438", hi="#f2d690"):
    """A charging bison in woven gold, facing left: the great shaggy hump over the shoulders, the
    head carried low with a beard and one horn, slim hindquarters, a tufted tail. (cx, by) = middle
    of the body on the hoof line; about 40 x 22 px."""
    cv.ellipse(cx - 16, by - 22, 22, 19, gold)          # hump and shoulders, high and massive
    cv.ellipse(cx - 2, by - 17, 20, 12, gold)           # barrel
    cv.ellipse(cx + 8, by - 18, 11, 11, gold)           # hindquarters
    cv.poly([(cx - 14, by - 13), (cx - 21, by - 12), (cx - 25, by - 8), (cx - 24, by - 4), (cx - 19, by - 3), (cx - 13, by - 6)], gold)
    cv.poly([(cx - 22, by - 5), (cx - 17, by - 4), (cx - 20, by + 0)], dark)      # beard
    cv.line(cx - 19, by - 12, cx - 21, by - 15, hi); cv.px(cx - 20, by - 16, hi)    # horn
    cv.px(cx - 21, by - 9, "#1a1418")                                              # eye
    for (lx, lh) in [(cx - 13, 8), (cx - 8, 9), (cx + 5, 8), (cx + 11, 9)]:       # legs and hooves
        cv.rect(lx, by - lh, 2, lh, gold); cv.hline(lx, by - 1, 2, dark)
    cv.line(cx + 18, by - 16, cx + 20, by - 10, gold); cv.rect(cx + 19, by - 10, 2, 3, dark)  # tail
    for k in range(4):                                  # shaggy shading down the front of the hump
        cv.vline(cx - 15 + k * 3, by - 18 + (k % 2) * 2, 6, C(dark, 0.7))
    cv.hline(cx - 11, by - 22, 9, hi); cv.hline(cx - 13, by - 21, 3, hi)
    cv.hline(cx - 4, by - 7, 14, C(dark, 0.6))          # belly line


def lounge_rug(cv, x, y, w, h, seed=0):
    """A retro rug for the arcade lounge: teal ground with a cream border, boomerangs in orange,
    cream and pink, small atomic starbursts between them."""
    rng = np.random.default_rng(seed)
    cv.rect(x - 1, y - 1, w + 2, h + 2, C(SHADOW, 0.5))
    cv.rect(x, y, w, h, "#1e4a4c")
    cv.rect(x + 2, y + 2, w - 4, h - 4, "#e6d6b1"); cv.rect(x + 3, y + 3, w - 6, h - 6, "#1e4a4c")
    cv.rect(x + 5, y + 5, w - 10, h - 10, "#24585a")
    for yy in range(y + 7, y + h - 6, 4):
        cv.hline(x + 6, yy, w - 12, "#225254")
    for row, gy in enumerate(range(y + 12, y + h - 8, 12)):
        for col, gx in enumerate(range(x + 10 + (row % 2) * 11, x + w - 14, 22)):
            c = ["#e8904a", "#e6d6b1", "#d0609a"][(row + col) % 3]
            if (row + col) % 2:
                cv.line(gx - 4, gy + 1, gx, gy - 2, c); cv.line(gx, gy - 2, gx + 4, gy + 1, c)
                cv.px(gx, gy - 1, shade(c, 0.3))
            else:
                cv.line(gx - 4, gy - 2, gx, gy + 1, c); cv.line(gx, gy + 1, gx + 4, gy - 2, c)
                cv.px(gx, gy, shade(c, 0.3))
            sx, sy = gx + 11, gy + 5
            if sx < x + w - 8 and sy < y + h - 6:
                cv.px(sx, sy, "#7ad8cc"); cv.px(sx - 1, sy, "#3a8a86"); cv.px(sx + 1, sy, "#3a8a86")
                cv.px(sx, sy - 1, "#3a8a86"); cv.px(sx, sy + 1, "#3a8a86")
    for fx in range(x, x + w, 2):
        cv.px(fx, y - 2, "#e6d6b1"); cv.px(fx, y + h + 1, "#e6d6b1")


# ---------------------------------------------------------------------------------------------
# props
# ---------------------------------------------------------------------------------------------

def rrect(cv, x, y, w, h, c):
    """Rectangle with its four corner pixels left off (a moulded, rounded look)."""
    cv.rect(x + 1, y, w - 2, h, c)
    cv.rect(x, y + 1, w, h - 2, c)


def bucket_seats(width=98, height=35, n=4, facing="front", seed=0, colours=None):
    """A row of moulded fibreglass settee seats on a chrome beam, alternating colours. facing='back'
    shows the shells from behind (seats that face the lanes)."""
    cols = colours or [SHELLS[(i + seed) % len(SHELLS)] for i in range(n)]
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 3)
    sw = width // n
    top = base - height
    # beam and pedestal legs
    beam = base - 12
    cv.rect(ox + 2, beam, width - 4, 3, OUT); cv.hline(ox + 3, beam + 1, width - 6, CHROME[2])
    for lx in (ox + 6, ox + width // 2 - 2, ox + width - 10):
        cv.rect(lx, beam + 2, 4, base - beam - 2, OUT); cv.vline(lx + 1, beam + 2, base - beam - 3, CHROME[2])
        cv.rect(lx - 2, base - 2, 8, 2, CHROME[1]); cv.hline(lx - 2, base - 2, 8, CHROME[3])
    for i in range(n):
        c, hi, lo = cols[i]
        sx = ox + i * sw
        if facing == "front":
            # the back shell: rim in the base colour, the scooped inner face lit, darker where it
            # curves down into the seat
            bx, bw, bh = sx + 2, sw - 4, 18
            rrect(cv, bx - 1, top, bw + 2, bh + 1, OUT)
            rrect(cv, bx, top + 1, bw, bh - 1, c)
            rrect(cv, bx + 2, top + 3, bw - 4, bh - 5, hi)
            cv.rect(bx + 2, top + bh - 6, bw - 4, 3, mix(hi, c, 0.5))
            cv.hline(bx + 3, top + 3, bw - 7, shade(hi, 0.3)); cv.vline(bx + 2, top + 4, 5, shade(hi, 0.2))
            # the seat pan: a wider lip, lit on top
            rrect(cv, sx, base - 20, sw - 1, 9, OUT)
            rrect(cv, sx + 1, base - 19, sw - 3, 7, c)
            cv.rect(sx + 2, base - 19, sw - 5, 3, hi); cv.hline(sx + 3, base - 19, sw - 7, shade(hi, 0.25))
            cv.hline(sx + 2, base - 14, sw - 5, lo)
        else:
            # from behind: the convex shell backs, a moulded rib, the seat's rear edge below
            bx, bw, bh = sx + 2, sw - 4, 22
            rrect(cv, bx - 1, top, bw + 2, bh + 1, OUT)
            rrect(cv, bx, top + 1, bw, bh - 1, c)
            cv.vline(bx + 1, top + 3, bh - 6, hi); cv.hline(bx + 2, top + 1, bw - 4, hi)
            cv.vline(bx + bw - 2, top + 3, bh - 5, lo)
            cv.rect(bx + bw // 2 - 1, top + 5, 2, bh - 10, shade(c, -0.12))
            cv.rect(bx + 2, top + bh - 3, bw - 4, 2, lo)
            cv.rect(sx + 1, base - 15, sw - 3, 3, OUT); cv.hline(sx + 2, base - 14, sw - 5, lo)
    return cv, ox + width // 2, base


def tent_card(cv, cx, by, label, face=PAPER[3], ink="#3a2a26", circle=False):
    """A folded card standing on a table top (its foot at by), with a red pencil ring if asked."""
    w = text_width(label) + 6
    x0 = cx - w // 2
    cv.rect(x0, by - 11, w, 11, OUT)
    cv.rect(x0 + 1, by - 10, w - 2, 9, face); cv.hline(x0 + 1, by - 10, w - 2, "#ffffff")
    cv.hline(x0 + 1, by - 2, w - 2, shade(face, -0.15))
    text(cv, label, cx - text_width(label) // 2, by - 11, ink)
    if circle:
        # the pencilled ring round ONE
        rx0, rx1 = x0 + 1, x0 + 22
        for xx in range(rx0, rx1):
            cv.px(xx, by - 12, "#c83a3c"); cv.px(xx + 1, by - 1, "#c83a3c")
        cv.vline(rx0 - 1, by - 11, 9, "#c83a3c"); cv.vline(rx1 + 1, by - 10, 9, "#c83a3c")


def scorer_table(width=70, height=35, label="ONE ROUND", circle=True, cards=1, seed=0):
    """A small scorer's table: a boomerang-laminate top seen from above with a chrome edge band, two
    chrome pedestal legs; scorecards, a stubby pencil, a soda cup, and a tent card with the label."""
    cv = Canvas(width + 4, height + 16, seed=seed)
    ox, base = 2, height + 14
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    edge = base - 16                       # chrome band along the front of the top
    depth = 10                             # the top surface, seen from above
    tt = edge - depth
    for lx in (ox + 8, ox + width - 11):
        cv.rect(lx, edge + 3, 3, base - edge - 4, OUT); cv.vline(lx + 1, edge + 3, base - edge - 5, CHROME[2])
        cv.rect(lx - 3, base - 2, 9, 2, CHROME[1]); cv.hline(lx - 3, base - 2, 9, CHROME[3])
    rrect(cv, ox, tt - 1, width, depth + 5, OUT)
    cv.rect(ox + 1, tt, width - 2, depth, "#d8c8a8"); cv.hline(ox + 2, tt, width - 4, "#f2e6cc")
    rng = np.random.default_rng(seed)
    for _ in range(width * depth // 14):    # boomerang flecks in the laminate
        fx, fy = ox + 3 + int(rng.integers(0, width - 7)), tt + 1 + int(rng.integers(0, depth - 2))
        cv.px(fx, fy, ["#e8904a", "#3a8a86", "#c4407a"][int(rng.integers(3))])
    cv.rect(ox + 1, edge, width - 2, 3, CHROME[1]); cv.hline(ox + 1, edge, width - 2, CHROME[3])
    # scorecards lying on the top, a pencil, a cup
    for i in range(cards):
        sx = ox + 5 + i * 22
        cv.rect(sx, tt + 3, 16, 6, PAPER[3]); cv.hline(sx, tt + 3, 16, "#ffffff")
        for gx in range(sx + 2, sx + 16, 3):
            cv.vline(gx, tt + 4, 4, C("#425da6", 0.55))
        cv.hline(sx + 1, tt + 6, 14, C("#425da6", 0.55))
        cv.px(sx + 3, tt + 5, "#c83a3c"); cv.px(sx + 4, tt + 4, "#c83a3c")
    px = ox + 6 + cards * 22
    cv.line(px, tt + 7, px + 7, tt + 5, "#e8b45c"); cv.px(px + 7, tt + 5, "#3a2a26"); cv.px(px, tt + 7, "#e88aa0")
    cx_ = ox + width - 10
    cv.rect(cx_ - 1, tt - 4, 7, 9, OUT); cv.rect(cx_, tt - 3, 5, 8, "#c84a3c")
    cv.hline(cx_, tt - 3, 5, "#ffffff"); cv.vline(cx_ + 3, tt - 7, 4, "#e6d6b1")
    if label:
        tent_card(cv, ox + width // 2 - 4, tt + 2, label, circle=circle)
    return cv, ox + width // 2, base


def pin_lamp(height=65):
    """A floor lamp made from a giant bowling pin: the pin is the base, a brass stem rises from its
    head to a lit drum shade (bulb ~5 px below the top, where the game's light sits)."""
    w = 22
    cv = Canvas(w, height + 4, seed=29)
    cx, base = w // 2, height + 1
    ground_shadow(cv, cx, base, 8, 2)
    # the pin, 10 wide and 24 tall
    prof = [(0, 2), (2, 3), (4, 2), (6, 2), (9, 3), (13, 5), (18, 5), (22, 4), (24, 3)]
    ph = 24
    py0 = base - ph
    for yy in range(ph):
        for (a, ra), (b, rb) in zip(prof, prof[1:]):
            if a <= yy <= b:
                r = int(round(ra + (rb - ra) * (yy - a) / max(1, b - a)))
                break
        cv.hline(cx - r - 1, py0 + yy, 2 * r + 3, OUT)
    for yy in range(ph):
        for (a, ra), (b, rb) in zip(prof, prof[1:]):
            if a <= yy <= b:
                r = int(round(ra + (rb - ra) * (yy - a) / max(1, b - a)))
                break
        cv.hline(cx - r, py0 + yy, 2 * r + 1, PIN[0])
        cv.px(cx + r, py0 + yy, PIN[1]); cv.px(cx + r - 1, py0 + yy, PIN[1] if r > 2 else PIN[0])
        if r > 3:
            cv.px(cx - r + 1, py0 + yy, "#ffffff")
    for sy in (py0 + 6, py0 + 8):
        cv.hline(cx - 2, sy, 5, PIN[3])
    cv.hline(cx - 4, base - 1, 9, PIN[2])
    # stem
    cv.rect(cx - 1, 15, 3, py0 - 15, OUT); cv.vline(cx, 15, py0 - 15, BRASS[3])
    cv.rect(cx - 2, (15 + py0) // 2, 5, 2, BRASS[2]); cv.hline(cx - 2, (15 + py0) // 2, 5, BRASS[4])
    # drum shade, lit
    cv.rect(cx - 8, 1, 17, 15, OUT)
    cv.rect(cx - 7, 2, 15, 13, "#e9a84a")
    cv.rect(cx - 6, 3, 9, 11, "#f6cd78"); cv.rect(cx - 5, 4, 3, 9, "#fde9b6")
    cv.hline(cx - 7, 2, 15, "#c47a2c"); cv.hline(cx - 7, 14, 15, "#c47a2c")
    cv.rect(cx - 2, 15, 5, 2, "#fff0c4")
    return cv, cx, base


def post_sign(width=122, height=27, label="LOST PROPERTY >", seed=0):
    """A wayfinding sign on two chrome posts: the oxblood-and-brass enamel of lost property."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2 - 10, 2)
    bt = base - height
    bh = 17
    for px in (ox + 16, ox + width - 19):
        cv.rect(px, bt + bh - 1, 3, base - bt - bh, OUT); cv.vline(px + 1, bt + bh, base - bt - bh - 1, CHROME[2])
        cv.rect(px - 3, base - 2, 9, 2, CHROME[1]); cv.hline(px - 3, base - 2, 9, CHROME[3])
    cv.rect(ox, bt, width, bh, OUT)
    cv.rect(ox + 1, bt + 1, width - 2, bh - 2, BRASS[2]); cv.hline(ox + 1, bt + 1, width - 2, BRASS[4])
    cv.hline(ox + 1, bt + bh - 2, width - 2, BRASS[0])
    cv.rect(ox + 3, bt + 3, width - 6, bh - 6, "#7e3a30"); cv.hline(ox + 3, bt + 3, width - 6, "#9a4a39")
    cv.hline(ox + 3, bt + bh - 4, width - 6, "#5e2a26")
    tx = ox + width // 2 - text_width(label) // 2
    text(cv, label, tx + 1, bt + 4, "#2a1418")
    text(cv, label, tx, bt + 3, PAPER[3])
    for bx in (ox + 5, ox + width - 6):
        cv.px(bx, bt + bh // 2, BRASS[4])
    return cv, ox + width // 2, base
