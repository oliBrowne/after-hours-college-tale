"""Inside the party house (H02): an old Hill living room on a Friday night.

Picture-rail walls in deep green over oak wainscot, a staircase taped off at the bottom, a bay
window onto College Ave, the fireplace with the house letters over the mantel, the kitchen doorway
packed with people (only their silhouettes), and a DJ corner with speakers, an LED strip and a TV
running a visualiser. Floors are worn oak. All letters and the house are fictional."""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, LEAF, ground_shadow, shrub
from interior import PANEL, FLOOR, crown, plank_floor
from facade import GLOW, FRAME
from h01_lib import CUP, PARTY, CLAP_CREAM, HOUSE_B, greek_letters, greek_small, greek_width, cups_row, cup_flat, SHADOW

INK = "#171a2b"
GREEN_WALL = ["#141e1c", "#1a2824", "#20322c", "#283c34", "#30463c", "#3a5246"]
OAK = ["#24161a", "#3a2420", "#56362a", "#704834", "#8a5c40", "#a8744f", "#c08a5c"]
LEATHER = ["#1e1210", "#341c16", "#4e2a1e", "#6a3a28", "#844c34", "#a06444"]
BRICK_IN = ["#2e1618", "#4a2222", "#62302a", "#7a3c32", "#904a3a"]
NEON = {"pink": "#ff6ab4", "cyan": "#4ae0f0", "violet": "#a07aff", "amber": "#ffbf5a"}


def _rng(seed):
    return np.random.default_rng(seed)


# --- walls ------------------------------------------------------------------------------------
def party_wall(cv, x, y, w, h, seed=0, rail=None):
    """Deep green painted plaster with a picture rail, the paint scuffed where people lean."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, GREEN_WALL[3])
    for _ in range(w * h // 14):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), GREEN_WALL[int(rng.choice([2, 4]))])
    for yy in range(y, y + 12):
        cv.hline(x, yy, w, C(SHADOW, 0.25 * (1 - (yy - y) / 12)))
    if rail:
        cv.rect(x, rail, w, 3, OAK[4]); cv.hline(x, rail, w, OAK[5]); cv.hline(x, rail + 3, w, C(SHADOW, 0.5))
    # shoulder-height scuffs
    for _ in range(w // 30):
        sx = x + int(rng.integers(0, w - 10)); sy = y + h - 60 + int(rng.integers(-6, 6))
        cv.hline(sx, sy, int(rng.integers(4, 12)), GREEN_WALL[2])


def oak_wainscot(cv, x, y, w, h):
    cv.rect(x, y, w, h, OAK[2])
    cv.rect(x, y, w, 3, OAK[5]); cv.hline(x, y, w, OAK[6]); cv.hline(x, y + 3, w, OAK[0])
    for px in range(x + 3, x + w - 8, 24):
        pw = min(20, x + w - px - 3)
        cv.rect(px, y + 6, pw, h - 11, OAK[1]); cv.rect(px + 1, y + 7, pw - 2, h - 13, OAK[3])
        cv.hline(px + 1, y + 7, pw - 2, OAK[4]); cv.vline(px + 1, y + 7, h - 13, OAK[4])
    cv.rect(x, y + h - 4, w, 4, OAK[1]); cv.hline(x, y + h - 4, w, OAK[3])


def led_strip(cv, x0, x1, y, colours=("#ff6ab4", "#a07aff", "#4ae0f0")):
    """LED tape along the crown: a coloured line and its wash on the wall below."""
    seg = (x1 - x0) // len(colours)
    for i, c in enumerate(colours):
        sx = x0 + i * seg
        cv.hline(sx, y, seg, c)
        for k, a in enumerate([0.22, 0.14, 0.08, 0.05]):
            cv.hline(sx, y + 1 + k * 2, seg, C(c, a)); cv.hline(sx, y + 2 + k * 2, seg, C(c, a))


# --- the staircase ----------------------------------------------------------------------------
def staircase(cv, x_bottom, base, steps=12, run=12, rise=8, width=26, seed=0, tape=True):
    """Stairs climbing left along the back wall: the stringer's panelled side, tread nosings, a
    banister with balusters and a newel post, caution tape across the bottom, a landing at the top.
    Returns the newel post top (for a lamp glow) and the landing rectangle."""
    rng = _rng(seed)
    x_top = x_bottom - steps * run
    top = base - steps * rise
    # the opening above: the upstairs hall (dark, one door with light under it)
    cv.rect(x_top - 4, 8, 76, top + 2, OUT); cv.rect(x_top - 3, 9, 74, top, "#0e1014")
    cv.rect(x_top, 12, 26, top - 14, "#1a1c22"); cv.rect(x_top + 4, top - 50, 18, 44, "#26222a")
    cv.hline(x_top + 4, top - 7, 18, GLOW[2]); cv.hline(x_top + 2, top - 6, 22, C(GLOW[2], 0.3))
    cv.rect(x_top + 18, top - 30, 2, 3, "#c0a060")
    # the stringer wall under the stairs (a triangle down to the floor), panelled
    pts = [(x_top, top), (x_bottom, base), (x_top, base)]
    cv.poly(pts, OAK[2])
    for k in range(steps):
        sx = x_top + k * run
        cv.vline(sx, top + k * rise + rise, base - (top + k * rise + rise), OAK[1])
    # a closet door under the stairs, coats spilling out
    cv.rect(x_top + 6, base - 46, 30, 46, OUT); cv.rect(x_top + 7, base - 45, 28, 45, OAK[3]); cv.hline(x_top + 7, base - 45, 28, OAK[5])
    cv.rect(x_top + 31, base - 24, 2, 3, "#d8b45a")
    for k, c in enumerate(["#3a2a4a", "#7e3a30", "#2a4a6a", "#c8a050", "#1e1e28"]):
        cv.ellipse(x_top + 4 + k * 8, base - 12 - (k % 2) * 4, 14, 12, OUT)
        cv.ellipse(x_top + 5 + k * 8, base - 11 - (k % 2) * 4, 12, 10, c)
        cv.hline(x_top + 7 + k * 8, base - 10 - (k % 2) * 4, 6, shade(c, 0.2))
    # treads and risers seen from the front-side
    for k in range(steps):
        sx = x_bottom - (k + 1) * run
        sy = base - (k + 1) * rise
        cv.rect(sx, sy, run + 1, rise, OAK[3])                   # riser face
        cv.rect(sx - 1, sy - 3, run + 2, 4, OUT)
        cv.rect(sx, sy - 2, run + 1, 2, OAK[5]); cv.hline(sx, sy - 2, run + 1, OAK[6])  # nosing
        cv.rect(sx + 2, sy + 1, run - 3, rise - 2, "#5e2a30"); cv.hline(sx + 2, sy + 1, run - 3, "#7a3a3c")  # runner carpet
        cv.vline(sx + run, sy, rise, OAK[1])
        # cups and a shoe left on the steps
        if k in (1, 4, 8):
            cv.rect(sx + 4, sy - 6, 3, 4, CUP[2]); cv.hline(sx + 4, sy - 6, 3, CUP[4])
    # banister: rail from the newel post up the slope, balusters on every step
    nx, ny = x_bottom + 4, base - 44
    for k in range(steps):
        bx = x_bottom - k * run - run // 2
        by_ = base - (k + 1) * rise - 2
        ry_ = ny + 8 - (nx - bx) * rise / run
        cv.rect(bx - 1, int(ry_), 3, by_ - int(ry_), OUT); cv.vline(bx, int(ry_), by_ - int(ry_), OAK[5])
    for t in range(0, nx - x_top + 2):
        xx = nx - t
        yy = int(ny + 8 - t * rise / run)
        cv.rect(xx, yy - 1, 1, 4, OUT); cv.px(xx, yy, OAK[6]); cv.px(xx, yy + 1, OAK[4])
    cv.rect(nx - 4, ny, 9, base - ny, OUT); cv.rect(nx - 3, ny + 1, 7, base - ny - 1, OAK[4])
    cv.vline(nx - 3, ny + 1, base - ny - 1, OAK[6]); cv.rect(nx - 5, ny - 4, 11, 5, OUT); cv.rect(nx - 4, ny - 3, 9, 3, OAK[5])
    cv.ellipse(nx - 3, ny - 9, 7, 6, OUT); cv.ellipse(nx - 2, ny - 8, 5, 4, OAK[5])
    if tape:
        # caution tape from the newel post to the wall, and a cardboard sign hanging off it
        for x in range(x_top - 2, nx - 3):
            yy = int(ny + 16 + 5 * np.sin((x - x_top) / (nx - x_top) * np.pi))
            c = "#e0c030" if ((x - x_top) // 4) % 2 else "#1a1820"
            cv.rect(x, yy, 1, 3, c)
        sxm = (x_top + nx) // 2 + 6
        sy = ny + 22
        cv.line(sxm - 6, sy - 1, sxm - 2, sy - 6, "#3a3848"); cv.line(sxm + 26, sy - 1, sxm + 22, sy - 6, "#3a3848")
        cv.rect(sxm - 10, sy, 46, 26, OUT); cv.rect(sxm - 9, sy + 1, 44, 24, "#b08a5a")
        for s, yy in [("NO PARTY", sy + 1), ("UPSTAIRS", sy + 9)]:
            text(cv, s, sxm + 13 - text_width(s) // 2, yy, "#2a1a1a")
        cv.hline(sxm - 6, sy + 21, 30, "#3a5aa8"); cv.px(sxm + 24, sy + 20, "#3a5aa8")    # the pen addition
    return (nx, ny - 6), (x_top, top)


# --- bay window -------------------------------------------------------------------------------
def bay_window(cv, x, y, w, h, seed=0):
    """Three tall sashes onto College Ave: the street lamp, the oak, a parked car's roof, the
    houses opposite; curtains tied back, string lights along the head."""
    rng = _rng(seed)
    cv.rect(x - 6, y - 8, w + 12, h + 14, OAK[1]); cv.rect(x - 5, y - 7, w + 10, h + 12, OAK[4]); cv.hline(x - 5, y - 7, w + 10, OAK[6])
    cv.rect(x - 1, y - 1, w + 2, h + 2, FRAME)
    # night outside
    cv.dither_v(x, y, w, h, "#141632", "#3a2c52", steps=4)
    for _ in range(18):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h // 3)), "#c8d0f0")
    # houses across the street: rooflines with lit windows
    hx = x
    while hx < x + w:
        hw = int(rng.integers(24, 40)); hh = int(rng.integers(22, 34))
        cv.poly([(hx, y + h - 18), (hx + hw // 2, y + h - 18 - hh), (hx + hw, y + h - 18), (hx + hw, y + h), (hx, y + h)], "#16141e")
        for _ in range(2):
            if rng.random() < 0.7:
                wx_ = hx + int(rng.integers(3, max(4, hw - 6)))
                cv.rect(wx_, y + h - 16 - int(rng.integers(0, 10)), 3, 4, GLOW[2] if rng.random() < 0.7 else "#8ab0f0")
        hx += hw - 2
    # the street lamp and its glow, the oak's dark crown
    lx = x + w - 24
    for r, a in [(14, 0.08), (9, 0.12), (5, 0.18)]:
        cv.ellipse(lx - r, y + 26 - r, r * 2, r * 2, C(AMBER[3], a))
    cv.vline(lx, y + 28, h - 28, "#0e0c14"); cv.rect(lx - 2, y + 24, 5, 5, AMBER[3])
    cv.ellipse(x - 6, y + 10, 50, 40, "#1a2018"); cv.ellipse(x + 2, y + 14, 34, 26, "#22281e")
    # sash bars: two mullions for the three panels, meeting rails
    for k in (1, 2):
        mx = x + k * w // 3
        cv.rect(mx - 2, y, 4, h, OAK[3]); cv.vline(mx - 2, y, h, OAK[5])
    cv.rect(x, y + h // 2 - 1, w, 3, OAK[3]); cv.hline(x, y + h // 2 - 1, w, OAK[5])
    # curtains tied back at each side
    for side in (0, 1):
        cxs = x - 4 if side == 0 else x + w - 12
        for i in range(16):
            fold = (i * 3) % 7
            c = "#5a1e2a" if fold < 3 else "#7a2a36" if fold < 5 else "#3a1420"
            col_x = cxs + i
            top_y = y - 6
            bot_y = y + h + 4 - (abs(i - (16 if side == 0 else 0)) // 3)
            cv.vline(col_x, top_y, bot_y - top_y, c)
        tie_x = cxs + (2 if side == 0 else 4)
        cv.rect(tie_x, y + h * 2 // 3, 10, 3, "#c0884a")
    # deep sill with stuff on it
    cv.rect(x - 8, y + h + 4, w + 16, 5, OAK[5]); cv.hline(x - 8, y + h + 4, w + 16, OAK[6]); cv.hline(x - 8, y + h + 9, w + 16, C(SHADOW, 0.6))
    cups_row(cv, x + 10, y + h + 4, n=3, seed=seed, spacing=7)
    cv.rect(x + w - 40, y + h - 4, 10, 8, OUT); cv.rect(x + w - 39, y + h - 3, 8, 6, "#3a7a3a")    # a sad houseplant
    cv.paste(shrub(0, 0, 16, 12, seed=4), x + w - 43, y + h - 16)


# --- fireplace and the wall of fame ---------------------------------------------------------------
def fireplace_mantel(cv, cx, base, seed=0):
    """Brick chimney breast, oak mantel with trophies and a paddle, the house letters above, a
    fireplace that has become a cup bin, a pair of composite photos either side."""
    rng = _rng(seed)
    w = 104
    x = cx - w // 2
    # chimney breast: painted brick, slightly proud of the wall
    cv.rect(x - 2, 6, w + 4, base - 6, OUT)
    for row, yy in enumerate(range(7, base, 4)):
        off = 0 if row % 2 else 4
        for xx in range(x - off, x + w, 8):
            x0, x1 = max(x, xx), min(x + w, xx + 7)
            if x1 > x0:
                cv.rect(x0, yy, x1 - x0, 3, BRICK_IN[int(rng.choice([2, 3, 3, 4]))])
        cv.hline(x, yy + 3, w, BRICK_IN[1])
    cv.vline(x, 7, base - 7, BRICK_IN[4]); cv.vline(x + w - 1, 7, base - 7, BRICK_IN[0])
    # letters above the mantel
    gw = greek_width(HOUSE_B, 2, 6)
    greek_letters(cv, HOUSE_B, cx - gw // 2, 24, 2, 6, face="#e8dcc2", hi="#fff6e0", dark="#8e7e6a")
    # mantel shelf on corbels
    my = 80
    cv.rect(x - 8, my, w + 16, 6, OUT); cv.rect(x - 7, my + 1, w + 14, 4, OAK[5]); cv.hline(x - 7, my + 1, w + 14, OAK[6])
    for kx in (x - 2, x + w - 6):
        cv.rect(kx, my + 6, 8, 8, OUT); cv.rect(kx + 1, my + 6, 6, 7, OAK[4])
    # on the mantel: two trophies, a paddle leaning, a framed photo, candles, cups
    for tx, h_ in [(x + 6, 14), (x + w - 16, 18)]:
        cv.rect(tx + 2, my - 3, 8, 3, OUT); cv.rect(tx + 4, my - h_, 4, h_ - 3, "#d8b45a"); cv.vline(tx + 4, my - h_, h_ - 3, "#f6d67a")
        cv.ellipse(tx + 1, my - h_ - 5, 10, 7, "#d8b45a"); cv.hline(tx + 3, my - h_ - 4, 5, "#f6d67a")
    px_ = x + 30
    cv.poly([(px_, my), (px_ + 4, my), (px_ + 12, my - 30), (px_ + 6, my - 32)], OUT)
    cv.poly([(px_ + 1, my - 1), (px_ + 3, my - 1), (px_ + 11, my - 29), (px_ + 7, my - 30)], OAK[5])
    cv.ellipse(px_ + 5, my - 44, 12, 16, OUT); cv.ellipse(px_ + 6, my - 43, 10, 14, OAK[5])
    greek_small(cv, ("XI",), px_ + 7, my - 41, "#7a2a2a")
    cv.rect(x + w - 44, my - 14, 16, 14, OUT); cv.rect(x + w - 43, my - 13, 14, 12, "#d8c8a8"); cv.rect(x + w - 41, my - 11, 10, 8, "#5a7a9a")
    for k in range(3):
        cv.rect(x + 54 + k * 5, my - 7 - k, 2, 7 + k, "#e6e0d2"); cv.px(x + 54 + k * 5, my - 9 - k, "#f6cf7a")
    cups_row(cv, x + w - 24, my, n=2, seed=seed + 1, spacing=5)
    # firebox: a black opening full of cups, a glowing LED log
    fx0, fx1, fy = x + 22, x + w - 22, my + 24
    cv.rect(fx0 - 4, fy - 4, fx1 - fx0 + 8, base - fy + 4, "#a89c88"); cv.hline(fx0 - 4, fy - 4, fx1 - fx0 + 8, "#c8bca4")
    cv.rect(fx0, fy, fx1 - fx0, base - fy, "#0e0c12")
    cv.ellipse(fx0 + 8, base - 10, 30, 8, C("#ff8a3a", 0.35)); cv.rect(fx0 + 14, base - 8, 20, 4, "#6a2a14"); cv.hline(fx0 + 16, base - 8, 16, "#ff9a4a")
    for k in range(9):
        cx_ = fx0 + 4 + int(rng.integers(0, fx1 - fx0 - 8)); cy_ = base - 4 - int(rng.integers(0, 12))
        cup_flat(cv, cx_, cy_, tipped=bool(k % 2), seed=k)
    cv.rect(fx0 - 8, base - 3, fx1 - fx0 + 16, 3, "#6a5e52"); cv.hline(fx0 - 8, base - 3, fx1 - fx0 + 16, "#8a7e6e")
    return (x, x + w)


def composite_frame(cv, x, y, w=30, h=40, seed=0, year="06"):
    """A framed house composite: rows of tiny oval portraits on a dark mat, a title plate."""
    rng = _rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT); cv.rect(x - 1, y - 1, w + 2, h + 2, "#a87c38"); cv.hline(x - 1, y - 1, w + 2, "#d0a650")
    cv.rect(x, y, w, h, "#16141e")
    for row in range(4):
        for col in range((w - 4) // 5):
            px_, py_ = x + 3 + col * 5, y + 4 + row * 7
            cv.rect(px_, py_, 3, 4, ["#e0b08a", "#c89068", "#a87050", "#f2cca8"][int(rng.integers(4))])
            cv.hline(px_, py_, 3, ["#2e2018", "#4a3020", "#a07a44", "#1a1414"][int(rng.integers(4))])
            cv.hline(px_, py_ + 4, 3, "#24222c")
    cv.rect(x + 4, y + h - 8, w - 8, 5, "#d0a650")
    text_y = y + h - 9
    cv.rect(x + w // 2 - 4, y + h - 7, 8, 2, "#7a5428")


def kitchen_opening(cv, x, base, w=76, h=92, seed=0):
    """A wide cased opening into the kitchen: green and pink party light, a fridge, cabinets,
    and the crowd as silhouettes against it."""
    rng = _rng(seed)
    top = base - h
    cv.rect(x - 7, top - 8, w + 14, h + 8, OAK[1]); cv.rect(x - 6, top - 7, w + 12, h + 7, OAK[4]); cv.hline(x - 6, top - 7, w + 12, OAK[6])
    cv.rect(x - 8, top - 10, w + 16, 4, OAK[5]); cv.hline(x - 8, top - 10, w + 16, OAK[6])
    # the kitchen: back wall tile, cabinets, fridge, the light
    for yy in range(top, base):
        t = (yy - top) / h
        cv.hline(x, yy, w, mix("#3a8a6a", "#1e3a34", t))
    for yy in range(top + 24, base - 30, 5):
        for xx in range(x + ((yy // 5) % 2) * 3, x + w, 6):
            cv.rect(xx, yy, 5, 4, C("#e8f4e0", 0.18))
    cv.rect(x + 2, top + 4, w - 4, 16, "#2a4a3a"); cv.hline(x + 2, top + 19, w - 4, "#16241e")
    for kx in range(x + 4, x + w - 8, 14):
        cv.rect(kx, top + 6, 12, 12, "#345a48"); cv.px(kx + 10, top + 14, "#c0c4cc")
    cv.rect(x + w - 26, top + 22, 24, base - top - 22, OUT); cv.rect(x + w - 25, top + 23, 22, base - top - 24, "#c8ccd0")
    cv.hline(x + w - 25, top + 23, 22, "#e8ecee"); cv.hline(x + w - 25, top + 46, 22, "#8a8e94")
    for k in range(5):
        cv.rect(x + w - 22 + (k * 5) % 18, top + 28 + (k * 7) % 14, 3, 3, ["#c84a3c", "#3a7ac8", "#e0c030", "#3ac87a", "#ff6ab4"][k])
    cv.ellipse(x + 8, top + 18, 40, 12, C("#ff6ab4", 0.22))                   # a pink bulb somebody swapped in
    cv.rect(x + 26, top - 1, 3, 6, "#16141e"); cv.rect(x + 25, top + 5, 5, 4, "#ff8ad0")
    # the crowd: heads and shoulders, packed, a raised cup or two
    sil = "#0e1214"
    for k in range(6):
        hx = x + 2 + k * 13 + int(rng.integers(-2, 3))
        hy = base - 46 + int(rng.integers(-5, 4))
        cv.ellipse(hx, hy, 9, 11, sil)
        cv.ellipse(hx - 4, hy + 10, 17, 14, sil)
        cv.rect(hx - 4, hy + 16, 17, base - hy - 16, sil)
        if k in (1, 4):
            cv.rect(hx + 10, hy - 6, 2, 12, sil); cv.rect(hx + 9, hy - 10, 4, 5, CUP[2]); cv.hline(hx + 9, hy - 10, 4, CUP[4])
    # rim light on the silhouettes from the kitchen behind
    m = (np.abs(cv.a[top:base, x:x + w, :3] - np.array(C(sil)[:3])).sum(-1) < 0.02)
    edge = m & ~np.roll(m, 1, 0)
    sub = cv.a[top:base, x:x + w]
    sub[edge] = C("#6ad8a0")
    cv.rect(x - 2, base - 2, w + 4, 2, "#6a5e52")
    return (x, top, w, h)


# --- DJ corner ----------------------------------------------------------------------------------
def wall_tv(cv, x, y, w=70, h=40):
    """A flat TV on the wall over the DJ table, running bars; returns the screen rect for the
    animated layer."""
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT); cv.rect(x - 1, y - 1, w + 2, h + 2, "#24222c")
    cv.rect(x, y, w, h, "#10121e")
    for k in range(10):
        bh = [10, 18, 26, 14, 30, 22, 12, 24, 16, 8][k]
        c = ["#ff6ab4", "#a07aff", "#4ae0f0"][k % 3]
        cv.rect(x + 3 + k * 7, y + h - 3 - bh, 5, bh, c)
    cv.vline(x + w // 2, y + h + 2, 6, "#3a3848")
    return (x, y, w, h)


def bedsheet(cv, x, y, w, h, seed=0):
    """The party's bedsheet banner on the wall: FALL BASH and the letters."""
    from h01_lib import bedsheet_banner
    bedsheet_banner(cv, x, y, w, h, [("text", "FALL BASH", "#c42e3e"), ("greek", HOUSE_B, "#2a3a8a")], seed=seed, sag=2)


def window_ac(cv, x, y):
    cv.rect(x, y, 22, 16, OUT); cv.rect(x + 1, y + 1, 20, 14, "#b8b8b0")
    for yy in range(y + 3, y + 13, 2):
        cv.hline(x + 3, yy, 12, "#8a8a84")
    cv.rect(x + 16, y + 3, 3, 3, "#3ac87a")


# --- props --------------------------------------------------------------------------------------
def leather_couch(width=124, height=46, seed=0):
    """A three-seat leather chesterfield seen from the front, worn pale on the arms, a jacket and a
    throw pillow on it."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base - 1, width // 2 + 2, 3, alpha=0.5)
    L = LEATHER
    top = base - height
    seat = base - 18
    cv.rect(ox + 8, top, width - 16, seat - top + 4, OUT)
    cv.rect(ox + 9, top + 1, width - 18, seat - top + 2, L[3]); cv.hline(ox + 9, top + 1, width - 18, L[5])
    for bx in range(ox + 14, ox + width - 12, 8):                    # buttons
        for by in (top + 6, top + 14):
            cv.px(bx, by, L[1]); cv.px(bx + 1, by + 1, L[4])
    cw = (width - 24) // 3
    for i in range(3):
        cx0 = ox + 12 + i * cw
        cv.rect(cx0, seat - 2, cw - 1, 11, OUT); cv.rect(cx0 + 1, seat - 1, cw - 3, 9, L[3]); cv.hline(cx0 + 1, seat - 1, cw - 3, L[5])
        cv.hline(cx0 + 2, seat + 4, cw - 5, L[2])
    cv.rect(ox + 10, seat + 9, width - 20, base - seat - 12, OUT); cv.rect(ox + 11, seat + 9, width - 22, base - seat - 13, L[2])
    for ax in (ox, ox + width - 14):
        cv.rect(ax, seat - 14, 14, base - seat + 10, OUT)
        cv.rect(ax + 1, seat - 13, 12, base - seat + 8, L[3]); cv.ellipse(ax, seat - 17, 14, 8, OUT); cv.ellipse(ax + 1, seat - 16, 12, 6, L[4])
        cv.hline(ax + 3, seat - 15, 8, L[5])
    # a denim jacket on the left cushion, a pillow with the letters on the right
    cv.poly([(ox + 16, seat), (ox + 40, seat - 4), (ox + 44, seat + 6), (ox + 18, seat + 8)], "#2a4a7a")
    cv.hline(ox + 18, seat, 22, "#4a6aa0")
    cv.rect(ox + width - 44, seat - 12, 22, 14, OUT); cv.rect(ox + width - 43, seat - 11, 20, 12, "#e6d6b1")
    greek_small(cv, ("XI",), ox + width - 37, seat - 10, "#7a2a2a")
    for fx in (ox + 6, ox + width - 10):
        cv.rect(fx, base - 4, 4, 3, OUT)
    return cv, ox + width // 2, base


def pong_table(width=124, height=44, seed=0):
    """A folding table painted in the house colours, ten cups in a triangle at each end, a ball
    in flight-ish (resting by a cup), the house-rules sign taped to the front."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base - 1, width // 2, 3, alpha=0.5)
    top = base - height + 12
    depth = 14
    # legs
    for lx in (ox + 6, ox + width - 9):
        cv.rect(lx, top + depth, 3, base - top - depth, OUT); cv.vline(lx + 1, top + depth, base - top - depth - 1, IRON[3])
    cv.line(ox + 8, base - 2, ox + 20, top + depth + 2, IRON[2]); cv.line(ox + width - 8, base - 2, ox + width - 20, top + depth + 2, IRON[2])
    # table top (seen from above at a slant) and its front edge
    cv.rect(ox, top, width, depth + 4, OUT)
    cv.rect(ox + 1, top + 1, width - 2, depth, "#1e3a3a")
    cv.rect(ox + width // 2 - 1, top + 1, 2, depth, "#e6d6b1")                     # centre stripe
    greek_small(cv, ("OMEGA",), ox + width // 2 - 4, top + 3, C("#e6d6b1", 0.5))
    cv.rect(ox + 1, top + depth + 1, width - 2, 3, "#2c5250"); cv.hline(ox + 1, top + depth + 1, width - 2, "#3e6e68")
    # cups: triangles of 4-3-2-1 at each end
    for side in (0, 1):
        for r in range(4):
            for c in range(4 - r):
                cx = (ox + 4 + r * 4) if side == 0 else (ox + width - 8 - r * 4)
                cy = top + 2 + c * 4 + r * 2
                cv.rect(cx, cy - 1, 3, 4, CUP[2]); cv.hline(cx, cy - 1, 3, CUP[4]); cv.px(cx + 2, cy + 2, CUP[1])
    cv.ellipse(ox + width // 2 + 14, top + 7, 3, 3, "#f6f2e6")
    # the sign taped to the front edge
    cv.rect(ox + width // 2 - 22, top + depth + 4, 44, 10, "#f2ecdc"); cv.rect(ox + width // 2 - 22, top + depth + 4, 3, 2, C("#c8c0a8", 0.8))
    text(cv, "NO MERCY", ox + width // 2 - text_width("NO MERCY") // 2, top + depth + 4, "#c42e2e")
    return cv, ox + width // 2, base


def dj_table(width=110, height=50, seed=0):
    """A folding table with a black skirt, laptop, controller, a ring light, cables to the floor."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base - 1, width // 2 + 2, 3, alpha=0.5)
    top = base - 30
    cv.rect(ox, top, width, base - top, OUT)
    cv.rect(ox + 1, top + 1, width - 2, base - top - 2, "#14121c")
    for sx in range(ox + 4, ox + width - 3, 5):
        cv.vline(sx, top + 5, base - top - 7, "#1c1a26")
    cv.rect(ox, top, width, 4, "#2a2832"); cv.hline(ox, top, width, "#4d4b66")
    # LED tape along the skirt, a hand-written sign
    for k, sx in enumerate(range(ox + 2, ox + width - 2, 3)):
        cv.px(sx, top + 5, ["#ff6ab4", "#a07aff", "#4ae0f0"][k % 3])
    cv.rect(ox + width // 2 - 20, top + 12, 40, 10, "#e6e0d2")
    text(cv, "LOUDER", ox + width // 2 - text_width("LOUDER") // 2, top + 12, "#2a2030")
    # controller and laptop on top
    cv.rect(ox + 14, top - 6, 48, 7, OUT); cv.rect(ox + 15, top - 5, 46, 5, "#24222f")
    for jx in (ox + 22, ox + 52):
        cv.ellipse(jx - 5, top - 6, 11, 6, "#3a384e"); cv.px(jx, top - 4, "#4ae0f0")
    for k in range(4):
        cv.rect(ox + 33 + k * 3, top - 5, 2, 4, "#e6e6ea")
    lx = ox + 68
    cv.poly([(lx, top - 1), (lx + 30, top - 1), (lx + 28, top - 4), (lx + 2, top - 4)], "#8a8898")
    cv.rect(lx + 3, top - 22, 24, 18, OUT); cv.rect(lx + 4, top - 21, 22, 16, "#2a2a3e")
    cv.rect(lx + 6, top - 19, 18, 3, "#4ae0f0"); cv.rect(lx + 6, top - 14, 12, 2, "#ff6ab4"); cv.rect(lx + 6, top - 10, 15, 2, "#a07aff")
    cv.ellipse(lx + 12, top - 17, 6, 6, "#e6e6ea")                                     # a sticker on the lid back
    # cables down the front
    cv.line(ox + 20, top + 2, ox + 12, base, "#0e0c14"); cv.line(ox + 60, top + 2, ox + 72, base, "#0e0c14")
    return cv, ox + width // 2, base


def speaker_stand(width=30, height=66, seed=0):
    """A PA speaker on a tripod stand."""
    cv = Canvas(width + 10, height + 6, seed=seed)
    ox, base = 5, height + 3
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 1, width // 2 + 2, 2, alpha=0.45)
    cv.line(cx, base - 26, cx - 12, base, OUT); cv.line(cx, base - 26, cx + 12, base, OUT); cv.vline(cx, base - 26, 26, OUT)
    cv.line(cx - 1, base - 26, cx - 12, base - 1, IRON[3]); cv.line(cx + 1, base - 26, cx + 12, base - 1, IRON[2])
    cv.rect(cx - 1, base - 34, 3, 10, OUT); cv.vline(cx, base - 34, 9, IRON[4])
    btop = base - height
    bh = height - 32
    cv.rect(ox, btop, width, bh, OUT); cv.rect(ox + 1, btop + 1, width - 2, bh - 2, "#24222f")
    cv.hline(ox + 1, btop + 1, width - 2, "#4d4b66")
    for (cy, r) in [(btop + bh - 12, 9), (btop + 8, 4)]:
        cv.ellipse(cx - r, cy - r, r * 2 + 1, r * 2 + 1, "#3a384e"); cv.ellipse(cx - r + 2, cy - r + 2, r * 2 - 3, r * 2 - 3, "#16141f")
        cv.ellipse(cx - r // 2, cy - r // 2, r + 1, r + 1, "#4d4b66")
    cv.rect(cx - 2, btop + 2, 4, 2, "#4ae0f0")
    return cv, cx, base


def recliner(width=46, height=42, seed=0):
    cv = Canvas(width + 6, height + 8, seed=seed)
    ox, base = 3, height + 4
    ground_shadow(cv, ox + width // 2, base - 1, width // 2, 3, alpha=0.5)
    c = ["#1e1a26", "#2e2838", "#3e3650", "#4e4666", "#6a5e80"]
    top = base - height
    cv.rect(ox + 6, top, width - 12, 26, OUT); cv.rect(ox + 7, top + 1, width - 14, 24, c[2]); cv.hline(ox + 7, top + 1, width - 14, c[4])
    for yy in (top + 8, top + 16):
        cv.hline(ox + 8, yy, width - 16, c[1])
    cv.rect(ox + 6, top + 24, width - 12, 10, OUT); cv.rect(ox + 7, top + 25, width - 14, 8, c[3])
    cv.rect(ox + 8, base - 10, width - 16, 8, OUT); cv.rect(ox + 9, base - 9, width - 18, 6, c[2])    # footrest half up
    for ax in (ox, ox + width - 9):
        cv.rect(ax, top + 14, 9, base - top - 16, OUT); cv.rect(ax + 1, top + 15, 7, base - top - 18, c[2]); cv.hline(ax + 1, top + 15, 7, c[4])
    cv.rect(ox + width // 2 - 6, top + 4, 12, 8, "#f2d27a"); cv.hline(ox + width // 2 - 4, top + 7, 8, "#7a5a2a")      # RESERVED note
    return cv, ox + width // 2, base


def bean_bag(width=42, height=26, seed=0):
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base - 1, width // 2, 3, alpha=0.5)
    c = ["#3a1a14", "#6a2e1c", "#9a4a24", "#c86a30", "#e8904a"]
    cv.ellipse(ox - 1, base - height - 1, width + 2, height + 2, OUT)
    cv.ellipse(ox, base - height, width, height, c[2])
    cv.ellipse(ox + 4, base - height + 2, width - 14, height // 2, c[3]); cv.ellipse(ox + 8, base - height + 3, 10, 5, c[4])
    cv.ellipse(ox + width // 2 - 6, base - height + 6, 16, 8, c[1])                 # the dent where someone sat
    cv.hline(ox + 4, base - 4, width - 8, c[1])
    return cv, ox + width // 2, base


def cup_tower_bin(width=26, height=36, seed=0):
    """A kitchen trash can with a leaning tower of stacked cups growing out of it."""
    cv = Canvas(width + 8, height + 34, seed=seed)
    ox, base = 4, height + 30
    ground_shadow(cv, ox + width // 2, base - 1, width // 2, 2)
    top = base - 24
    cv.poly([(ox + 1, top), (ox + width - 1, top), (ox + width - 3, base - 1), (ox + 3, base - 1)], OUT)
    cv.poly([(ox + 2, top + 1), (ox + width - 2, top + 1), (ox + width - 4, base - 2), (ox + 4, base - 2)], "#8a8e98")
    cv.vline(ox + 4, top + 2, base - top - 5, "#b8bcc4"); cv.rect(ox, top - 2, width, 3, OUT); cv.hline(ox + 1, top - 1, width - 2, "#a8acb4")
    # the tower: stacked cups, leaning, 40-odd px tall
    x = ox + width // 2 - 2
    for k in range(14):
        y = top - 3 - k * 4
        x += 1 if k in (5, 9, 12) else 0
        cv.rect(x - 1, y, 6, 4, OUT); cv.rect(x, y, 4, 3, CUP[2]); cv.hline(x, y, 4, CUP[4]); cv.vline(x, y, 3, CUP[3])
    cv.rect(x - 1, top - 3 - 14 * 4, 6, 2, CUP[4])
    return cv, ox + width // 2, base


def snack_table(width=84, height=36, seed=0):
    cv = Canvas(width + 6, height + 10, seed=seed)
    ox, base = 3, height + 6
    ground_shadow(cv, ox + width // 2, base - 1, width // 2, 3, alpha=0.5)
    top = base - 22
    for lx in (ox + 4, ox + width - 7):
        cv.rect(lx, top + 4, 3, base - top - 4, OUT); cv.vline(lx + 1, top + 4, base - top - 5, IRON[3])
    cv.rect(ox, top - 1, width, 9, OUT); cv.rect(ox + 1, top, width - 2, 7, "#e6e0d2")
    for k in range(0, width - 2, 6):
        cv.rect(ox + 1 + k, top, 3, 7, "#c84a4a")                                   # checked plastic cloth
    cv.hline(ox + 1, top + 6, width - 2, "#9a8a7a")
    # pizza box open with one slice, chips bowl, salsas, a 2-litre bottle, cups
    cv.rect(ox + 6, top - 4, 26, 5, OUT); cv.rect(ox + 7, top - 3, 24, 3, "#c8a06a")
    cv.poly([(ox + 7, top - 4), (ox + 31, top - 4), (ox + 29, top - 16), (ox + 9, top - 16)], OUT)
    cv.poly([(ox + 8, top - 5), (ox + 30, top - 5), (ox + 28, top - 15), (ox + 10, top - 15)], "#d8b880")
    cv.poly([(ox + 12, top - 2), (ox + 22, top - 2), (ox + 17, top - 1)], "#e8a040"); cv.px(ox + 16, top - 2, "#c43a2a")
    cv.ellipse(ox + 36, top - 5, 16, 6, OUT); cv.ellipse(ox + 37, top - 4, 14, 4, "#e8c060")
    for k, c in enumerate(["#c43a2a", "#3a8a3a", "#e0a030"]):
        cv.rect(ox + 54 + k * 6, top - 3, 5, 3, OUT); cv.rect(ox + 55 + k * 6, top - 2, 3, 1, c)
    cv.rect(ox + width - 12, top - 16, 6, 16, OUT); cv.rect(ox + width - 11, top - 15, 4, 14, C("#5aa860", 0.9))
    cv.rect(ox + width - 11, top - 9, 4, 4, "#e6d6b1"); cv.rect(ox + width - 10, top - 18, 2, 3, "#c43a2a")
    cups_row(cv, ox + width - 26, top, n=3, seed=seed, spacing=4)
    return cv, ox + width // 2, base


def floor_lamp_h(height=64):
    """A thrifted floor lamp with a fringed shade and a pink bulb."""
    w = 24
    cv = Canvas(w, height + 4, seed=19)
    cx, base = w // 2, height + 1
    ground_shadow(cv, cx, base, 8, 2)
    cv.rect(cx - 6, base - 2, 12, 2, IRON[1]); cv.hline(cx - 6, base - 2, 12, IRON[3])
    cv.rect(cx - 1, 16, 2, base - 18, "#a87c38"); cv.vline(cx - 1, 16, base - 18, "#d0a650")
    cv.poly([(cx - 6, 2), (cx + 5, 2), (cx + 9, 15), (cx - 10, 15)], OUT)
    cv.poly([(cx - 5, 3), (cx + 4, 3), (cx + 8, 14), (cx - 9, 14)], "#e07aa8")
    cv.poly([(cx - 4, 4), (cx + 1, 4), (cx + 3, 13), (cx - 7, 13)], "#ffb0d0")
    for fx in range(cx - 9, cx + 9, 2):
        cv.vline(fx, 15, 3, "#c0884a")
    return cv, cx, base


def party_rug(cv, x, y, w, h, seed=0):
    """A worn oriental rug, kicked crooked, its near-right corner flipped over to show the back."""
    rng = _rng(seed)
    field, border, motif, fringe = "#5a2a30", "#2a3a5a", "#c8a050", "#d8ccb4"
    cv.rect(x + 2, y + 2, w, h, C(SHADOW, 0.35))
    cv.rect(x, y, w, h, border)
    cv.rect(x + 5, y + 4, w - 10, h - 8, "#c8a050"); cv.rect(x + 6, y + 5, w - 12, h - 10, field)
    for yy in range(y + 10, y + h - 8, 10):
        for xx in range(x + 14 + ((yy - y) // 10 % 2) * 10, x + w - 12, 20):
            cv.poly([(xx, yy - 4), (xx + 6, yy), (xx, yy + 4), (xx - 6, yy)], "#7a3a3c")
            cv.px(xx, yy, motif)
    cv.ellipse(x + w // 2 - 22, y + h // 2 - 12, 44, 24, "#2a3a5a"); cv.ellipse(x + w // 2 - 16, y + h // 2 - 8, 32, 16, "#7a3a3c")
    cv.ellipse(x + w // 2 - 6, y + h // 2 - 3, 12, 6, motif)
    for k in range(int(w * h / 40)):                       # wear: the pile worn through in a path
        wx = x + int(rng.normal(w * 0.55, w * 0.18)); wy = y + int(rng.integers(4, h - 4))
        if x + 6 < wx < x + w - 6:
            cv.hline(wx, wy, 2, C("#a89070", 0.3))
    for fx in range(x, x + w, 2):
        cv.vline(fx, y - 3, 3, fringe); cv.vline(fx, y + h, 3, fringe)
    # the flipped corner: a triangle of the rug's pale back laid over the front
    cx, cy = x + w, y + h
    cv.poly([(cx - 34, cy), (cx, cy - 20), (cx, cy)], "#3a2a26")
    cv.poly([(cx - 34, cy), (cx, cy - 20), (cx - 12, cy + 10)], "#b8a88a")
    for k in range(0, 30, 3):
        cv.line(cx - 34 + k, cy - (k * 20) // 34, cx - 34 + k + 4, cy - (k * 20) // 34 + 5, "#a09070")
    cv.line(cx - 34, cy, cx, cy - 20, "#d8ccb4")


def shoe_pile(cv, x, y, seed=0):
    """Shoes kicked off by the front door: sneakers, a boot, a sandal (flat floor detail)."""
    rng = _rng(seed)
    cols = ["#e6e2d6", "#2a2838", "#c84a3c", "#3a6ac8", "#6a4a2a", "#e0c030", "#1e1e28"]
    for k in range(9):
        sx = x + int(rng.integers(0, 54)); sy = y + int(rng.integers(0, 14))
        c = cols[int(rng.integers(len(cols)))]
        cv.rect(sx, sy, 9, 4, OUT); cv.rect(sx + 1, sy + 1, 7, 2, c); cv.hline(sx + 1, sy + 3, 7, "#d8d4c8" if c != "#e6e2d6" else "#a8a498")
        cv.px(sx + 6, sy + 1, shade(c, 0.3))
