"""Exterior materials of the real CU Boulder Engineering Center (1965, Muchow with Belluschi), used by
the E01 loading court and its battle backdrop.

The building is two materials side by side:
- raw board-formed concrete, grey and weathered: horizontal plank imprints with wood grain, form-tie
  holes in a grid, pour lines, darker drip streaks under every ledge and sill ("the concrete coffin");
- rough Lyons sandstone, CU's pink-tan to rusty-red flagstone, laid in irregular rough courses.
Over the lower wings sit single-slope (shed) roofs in red clay barrel tile, and stair/office towers rise
above them like grain silos, with narrow windows set deep in thick concrete frames.

Painters draw straight onto a Canvas at 1:1 game pixels. Big surfaces are numpy arrays; everything
uses a few tones per material (clean clusters, no noise dither).
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from lib_eng import P, H, hashn, grid, soft_field, put_rgb, WARM, STEEL
from facade import GLOW, DARKGLASS, FRAME
from props import OUT

# weathered board-formed concrete: 0 ink .. 9 top-lit
BOARD = ["#201f26", "#2e2d34", "#3d3b43", "#4e4b52", "#5f5b61", "#716c70", "#837d7f", "#97908f", "#aba3a0", "#c0b8b2"]
# Lyons sandstone families: (shadow, body, light, lit edge)
LYONS = {
    "pink": ("#8a5650", "#ae7366", "#c48a79", "#d8a48f"),
    "salmon": ("#94584a", "#b8705a", "#cc876c", "#dca082"),
    "rust": ("#743a32", "#93493c", "#a95b48", "#bf735a"),
    "tan": ("#866a56", "#a6866c", "#bc9c80", "#cfb294"),
    "plum": ("#5c3a3e", "#74494a", "#8a5a58", "#9e6e68"),
}
LYONS_MIX = [("pink", 0.32), ("salmon", 0.2), ("rust", 0.2), ("tan", 0.18), ("plum", 0.1)]
JOINT = "#33262c"          # deep raked mortar joint (reads dark at night)
MORTAR = "#5e4c4a"         # a mortar face catching light here and there
# red clay barrel tile (Klauder's campus roofs), a touch brighter than facade.ROOF for the night tint
CLAY = ["#2e1416", "#4e2220", "#6e2e26", "#8e3c2e", "#ac4e38", "#c4644a", "#d88062", "#e89a7c"]
STAIN = "#1c1a22"


# ---------------------------------------------------------------------------------------------
# board-formed concrete
# ---------------------------------------------------------------------------------------------

def board_np(w, h, seed=0, base=6, board=4, tie=(24, 16), lift=48, ox=0, oy=0, ties=True):
    """Board-formed concrete as an (h, w) index array into BOARD. (ox, oy) is the texture origin so
    neighbouring pieces share board lines and tie rows."""
    xs, ys = grid(w, h)
    X, Y = xs + ox, ys + oy
    row = Y // board
    r = Y % board
    # each board course is cut into planks of different lengths; a few planks a shade off
    shift = (hashn(row, 11, seed) * 60).astype(int)
    plank_len = 40 + (hashn(row, 12, seed) * 50).astype(int)
    plank = (X + shift) // plank_len
    t = hashn(plank, row, seed + 1)
    idx = base + np.where(t < 0.16, -1, np.where(t > 0.9, 1, 0))
    # each board leaves a small lit ridge along its upper edge (the plank imprint)
    idx = np.where(r == 0, idx + 1, idx)
    # wood grain: sparse short streaks inside a plank, a knot now and then
    gcell = (X + shift + row * 5) // 7
    g = hashn(gcell, row * 7 + r, seed + 2)
    idx = np.where((r == board // 2) & (g > 0.9), idx - 1, idx)
    knot = hashn(X // 2, row, seed + 3) > 0.996
    idx = np.where(knot & (r == 1), base - 2, idx)
    # weathering: tall darker streaky patches (rain runs down the face) and a few bleached ones
    f = _streaks(w, h, X, Y, seed + 4)
    idx = np.where(f < 0.22, idx - 1, np.where(f > 0.86, idx + 1, idx))
    # pour (lift) lines
    if lift:
        lr = Y % lift
        idx = np.where(lr == 0, base - 2, idx)
        idx = np.where(lr == 1, base + 2, idx)
    # form-tie holes in a grid, offset every other lift, with a lit lip under each
    if ties:
        tx, ty = tie
        lift_k = Y // max(1, (lift or 48))
        txo = (X + (lift_k % 2) * (tx // 2)) % tx
        tyo = (Y - board // 2) % ty
        hole = (tyo == 0) & (txo < 2)
        idx = np.where(hole, 1, idx)
        idx = np.where((tyo == 1) & (txo < 2), np.maximum(idx, base + 1), idx)
    return np.clip(idx, 0, len(BOARD) - 1)


def _streaks(w, h, X, Y, seed):
    """Weathering field stretched vertically: narrow columns that vary slowly down the wall."""
    col = hashn(X // 3, 0, seed)
    col2 = hashn(X // 9, 1, seed)
    run = hashn(X // 3, (Y + (col * 40).astype(int)) // 40, seed + 1)
    return 0.45 * col + 0.3 * col2 + 0.25 * run


def board_concrete(cv, x, y, w, h, seed=0, base=6, side=0, mask=None, **kw):
    """Paint board-formed concrete. side < 0 darkens (a face turned from the light)."""
    if w <= 0 or h <= 0:
        return
    idx = board_np(w, h, seed=seed, base=base + side, ox=kw.pop("ox", x), oy=kw.pop("oy", y), **kw)
    put_rgb(cv, x, y, P(BOARD)[idx], mask=mask)


def drips(cv, x, y, w, length, seed=0, density=0.35, alpha=0.32):
    """Dark weathering streaks running down from a ledge or sill (stepped fade, 1-2px wide)."""
    rng = np.random.default_rng(seed)
    xx = x
    while xx < x + w:
        if rng.random() < density:
            sw = 1 if rng.random() < 0.7 else 2
            L = int(rng.integers(max(3, length // 3), length + 1))
            a = alpha * (0.6 + 0.4 * rng.random())
            third = max(1, L // 3)
            cv.rect(xx, y, sw, third, C(STAIN, a))
            cv.rect(xx, y + third, sw, third, C(STAIN, a * 0.66))
            cv.rect(xx, y + 2 * third, sw, L - 2 * third, C(STAIN, a * 0.36))
            xx += sw + int(rng.integers(0, 3))
        else:
            xx += int(rng.integers(1, 5))
    # a soft dark band right under the ledge where water sits
    cv.rect(x, y, w, 2, C(STAIN, alpha * 0.6))


def ledge(cv, x, y, w, h=3, seed=0, drip=14):
    """A projecting concrete ledge / coping: lit top, shadow under, streaks below."""
    cv.rect(x, y, w, h, BOARD[7]); cv.hline(x, y, w, BOARD[9]); cv.hline(x, y + h - 1, w, BOARD[5])
    cv.hline(x, y + h, w, C(OUT, 0.55))
    if drip:
        drips(cv, x, y + h + 1, w, drip, seed=seed)


# ---------------------------------------------------------------------------------------------
# Lyons sandstone
# ---------------------------------------------------------------------------------------------

def lyons_wall(cv, x, y, w, h, seed=0, light=0):
    """Rough Lyons sandstone flagstone in irregular coursed blocks: pink, salmon, rust, tan and plum
    stones of varied length and height, some split into thin stacked slabs, deep dark joints.
    light shifts every stone toward its lit (1) or shadow (-1) tone."""
    rng = np.random.default_rng(seed)
    tmp = Canvas(w, h)
    tmp.rect(0, 0, w, h, JOINT)
    names = [n for n, _ in LYONS_MIX]
    probs = np.array([p for _, p in LYONS_MIX]); probs /= probs.sum()

    def stone(sx, sy, sw, sh):
        fam = LYONS[names[rng.choice(len(names), p=probs)]]
        body = fam[int(np.clip(1 + light + (1 if rng.random() < 0.35 else 0), 0, 3))]
        lo = fam[int(np.clip(0 + light, 0, 3))]
        hi = fam[int(np.clip(2 + light + (1 if rng.random() < 0.5 else 0), 0, 3))]
        tmp.rect(sx, sy, sw, sh, body)
        tmp.hline(sx, sy, sw, hi)                         # lit upper arris
        if sh > 2:
            tmp.hline(sx + 1, sy + sh - 1, sw - 1, lo)    # shadowed underside
        tmp.vline(sx + sw - 1, sy + 1, sh - 1, lo)
        if sw > 12 and sh > 3 and rng.random() < 0.6:     # bedding line through a long slab
            bx = sx + int(rng.integers(1, sw // 2))
            tmp.hline(bx, sy + int(rng.integers(1, sh - 1)), int(rng.integers(4, sw - (bx - sx))), lo)
        if sw > 6 and rng.random() < 0.35:                 # a pitted spot
            tmp.px(sx + int(rng.integers(1, sw - 2)), sy + int(rng.integers(1, max(2, sh - 1))), lo)
        # knocked corners so the stones read rough, not brick
        for (cx, cy) in ((sx, sy), (sx + sw - 1, sy), (sx, sy + sh - 1), (sx + sw - 1, sy + sh - 1)):
            if rng.random() < 0.45:
                tmp.px(cx, cy, JOINT)

    yy = 0
    while yy < h:
        ch = int(rng.choice([3, 4, 4, 5, 5, 6, 7, 8]))
        ch = min(ch, h - yy)
        xx = -int(rng.integers(0, 14))
        while xx < w:
            sw = int(rng.integers(6, 26)) if ch < 7 else int(rng.integers(10, 30))
            if ch >= 6 and rng.random() < 0.28:            # two thin slabs stacked in one course
                top_h = int(rng.integers(2, ch - 2))
                stone(xx, yy, sw - 1, top_h)
                cut = xx + int(rng.integers(-3, 4))
                stone(cut, yy + top_h + 1, sw - 1 + (xx - cut), ch - top_h - 2)
            else:
                stone(xx, yy, sw - 1, ch - 1)
            if rng.random() < 0.06:                         # a light mortar face in a wide joint
                tmp.vline(xx + sw - 1, yy + 1, max(1, ch - 2), MORTAR)
            xx += sw + (1 if rng.random() < 0.2 else 0)
        yy += ch
    cv.paste(tmp, x, y)


# ---------------------------------------------------------------------------------------------
# red tile shed roofs
# ---------------------------------------------------------------------------------------------

def tile_band(cv, x, y, w, h, seed=0):
    """Shed roof sloping down toward the viewer: barrel tile rows running down the slope, the lit
    crowns, round tile ends along the eave, a concrete fascia and its shadow under."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, CLAY[1])
    for tx in range(x, x + w, 4):
        tone = 4 if rng.random() < 0.65 else 3
        cv.vline(tx, y, h, CLAY[1]); cv.vline(tx + 1, y, h, CLAY[tone]); cv.vline(tx + 2, y, h, CLAY[tone + 1])
        cv.vline(tx + 3, y, h, CLAY[0])
        for ty in range(y + int(rng.integers(0, 5)), y + h - 2, 5):   # tile laps
            cv.hline(tx + 1, ty, 2, CLAY[tone + 2]); cv.hline(tx + 1, ty + 1, 2, CLAY[tone - 1])
        if rng.random() < 0.08:                                           # a darker replacement tile
            ty = y + int(rng.integers(0, max(1, h - 5)))
            cv.rect(tx + 1, ty, 2, 4, CLAY[2])
    for tx in range(x, x + w, 4):                                        # round ends along the eave
        cv.rect(tx + 1, y + h - 2, 2, 2, CLAY[5]); cv.px(tx, y + h - 1, CLAY[0])
    cv.rect(x, y + h, w, 3, BOARD[6]); cv.hline(x, y + h, w, BOARD[8]); cv.hline(x, y + h + 2, w, BOARD[4])
    cv.hline(x, y + h + 3, w, C(OUT, 0.6))


def shed_rake(cv, x0, y0, x1, y1, thick=9, seed=0, fascia=3):
    """A shed roof sloping sideways (the slope runs along the facade): a parallelogram of barrel tile
    whose rows follow the slope, the tile ends showing at the low end, and a concrete fascia under
    the rake. (x0, y0)-(x1, y1) is the top of the wall under it."""
    rng = np.random.default_rng(seed)
    lo_end = x1 if y1 > y0 else x0
    for x in range(min(x0, x1), max(x0, x1) + 1):
        yl = y0 + (y1 - y0) * (x - x0) / float(x1 - x0)
        ytop = int(round(yl)) - thick
        for k in range(thick):
            yy = ytop + k
            course = k // 3
            r = k % 3
            lap = ((x + course * 5 + int(yl) // 3) % 9)
            if r == 0:
                c = CLAY[6] if lap not in (0, 1) else CLAY[4]
            elif r == 1:
                c = CLAY[4] if lap != 0 else CLAY[2]
            else:
                c = CLAY[1]
            if k == 0:
                c = CLAY[7] if lap > 1 else CLAY[5]
            cv.px(x, yy, c)
        # fascia under the rake and its shadow line on the wall below
        yb = int(round(yl))
        for k in range(fascia):
            cv.px(x, yb + k, BOARD[[8, 6, 4][min(k, 2)]])
        cv.px(x, yb + fascia, C(OUT, 0.55))
    # tile ends at the low end: a column of round caps
    ly = y1 if lo_end == x1 else y0
    d = 1 if lo_end == x1 else -1
    for k in range(0, thick, 3):
        yy = int(round(ly)) - thick + k
        cv.rect(lo_end, yy, 2, 2, CLAY[5]); cv.px(lo_end + d * 2, yy + 1, CLAY[0])
        cv.px(lo_end + (1 if d > 0 else 0), yy, CLAY[7])


# ---------------------------------------------------------------------------------------------
# windows, towers, signs
# ---------------------------------------------------------------------------------------------

def deep_window(cv, x, y, w, h, lit=False, seed=0, frame=3, blind=0.0, sill=True, figure=False):
    """A narrow window set deep in a thick board-formed concrete frame: the frame's lit face, the
    shadowed reveal inside it, glass well back from the face, a projecting sill with streaks."""
    rng = np.random.default_rng(seed)
    f = frame
    cv.rect(x - f - 1, y - f - 1, w + 2 * f + 2, h + 2 * f + 2, OUT)
    cv.rect(x - f, y - f, w + 2 * f, h + 2 * f, BOARD[7])
    cv.hline(x - f, y - f, w + 2 * f, BOARD[9]); cv.vline(x - f, y - f, h + 2 * f, BOARD[8])
    cv.vline(x + w + f - 1, y - f, h + 2 * f, BOARD[5])
    for yy in range(y - f + 2, y + h + f, 4):                      # board marks on the frame
        cv.hline(x - f + 1, yy, f - 1, BOARD[6]); cv.hline(x + w + 1, yy, f - 2, BOARD[5])
    # glass
    if lit:
        for yy in range(y, y + h):
            t = (yy - y) / max(1, h)
            cv.hline(x, yy, w, GLOW[3] if t < 0.35 else GLOW[2] if t < 0.8 else GLOW[1])
        cv.hline(x, y + 3, w, GLOW[4])
        if blind > 0:
            bh = int(h * blind)
            cv.rect(x, y, w, bh, "#d8c2a0")
            for yy in range(y + 1, y + bh, 2):
                cv.hline(x, yy, w, "#b49c80")
        if figure:   # the back of a monitor / a desk lamp low in the window
            cv.rect(x + 1, y + h - 6, w - 2, 2, "#5a3420")
            cv.rect(x + w // 2 - 2, y + h - 11, 5, 5, "#2a2230"); cv.px(x + w // 2, y + h - 9, "#8ad0e0")
    else:
        for yy in range(y, y + h):
            t = (yy - y) / max(1, h)
            cv.hline(x, yy, w, DARKGLASS[1] if t < 0.45 else DARKGLASS[0])
        if w >= 4:
            cv.line(x + 1, y + h // 2 + 3, x + w - 2, y + h // 2 - 1, DARKGLASS[3])
            cv.line(x + 1, y + h // 2 + 6, x + w - 2, y + h // 2 + 2, C(DARKGLASS[2], 0.7))
    # the reveal: the deep frame shades the top and left of the glass
    cv.rect(x, y, w, 2, C("#0e0c16", 0.75)); cv.rect(x, y + 2, w, 1, C("#0e0c16", 0.35))
    cv.rect(x, y, 1, h, C("#0e0c16", 0.6))
    cv.hline(x, y + h * 2 // 3, w, FRAME)
    if sill:
        cv.rect(x - f - 1, y + h + f, w + 2 * f + 2, 2, BOARD[8]); cv.hline(x - f - 1, y + h + f + 2, w + 2 * f + 2, C(OUT, 0.6))
        drips(cv, x - f, y + h + f + 3, w + 2 * f, 12, seed=seed + 50, density=0.5, alpha=0.3)


def stair_slot(cv, x, y, w, h, lit=True, floor_h=30, seed=0):
    """A full-height slot window in a stair tower, set deep in the concrete: dusk glass with a
    centre mullion, each landing's warm light low in its floor, the landing slab and its rail."""
    cv.rect(x - 3, y - 3, w + 6, h + 6, OUT)
    cv.rect(x - 2, y - 2, w + 4, h + 4, BOARD[8]); cv.vline(x + w + 1, y - 2, h + 4, BOARD[5])
    for yy in range(y, y + h):
        k = (yy - y) % floor_h
        if lit and k > floor_h - 14:
            c = GLOW[3] if k > floor_h - 6 else GLOW[2]
        else:
            c = DARKGLASS[1] if k < floor_h // 2 else DARKGLASS[2]
        cv.hline(x, yy, w, c)
    for yy in range(y + floor_h - 1, y + h, floor_h):          # landing slab, rail and balusters
        cv.rect(x, yy, w, 3, BOARD[3]); cv.hline(x, yy, w, BOARD[6])
        cv.hline(x, yy - 7, w, OUT)
        for xx in range(x + 1, x + w, 3):
            cv.vline(xx, yy - 7, 7, C(OUT, 0.6))
        cv.line(x, yy - 10, x + w - 1, yy - 18, C(OUT, 0.7))  # the flight above, in silhouette
    cv.vline(x + w // 2, y, h, FRAME)
    cv.rect(x, y, w, 2, C("#0e0c16", 0.7)); cv.rect(x, y, 1, h, C("#0e0c16", 0.55))


def letters(cv, s, x, y, colour="#d8c49a", shadow="#1a1520"):
    """Cast letters standing proud of a wall: a shadow one pixel down-right, then the face."""
    text(cv, s, x + 1, y + 1, C(shadow, 0.85))
    text(cv, s, x, y, colour)


def paint_masked(cv, poly, painter):
    """Run painter(tmp) on a scratch canvas and keep only the part inside poly (for walls under a
    sloping roof)."""
    from PIL import Image, ImageDraw
    tmp = Canvas(cv.w, cv.h)
    painter(tmp)
    m = Image.new("L", (cv.w, cv.h), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
    tmp.a[np.array(m) == 0] = 0
    cv.paste(tmp, 0, 0)
