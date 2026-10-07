"""Farrand Hall dorm room (D01) on move-in day: palettes, wall/floor painters and the props.

Late August, the hour before sunset. The west window frames the Flatirons with the low sun just
right of the slabs, so a long gold patch falls in across the tile toward the left. The room is a
1950s Farrand double: painted cinder-block walls, vinyl tile, a steam convector under a steel
casement window, built-in wooden desks with hutches and a wardrobe. The left half is Jules's (bare
blue dorm mattress, boxes still taped, an empty corkboard with the RA's welcome note); the right
half is Jakerson's, who moved in yesterday and has already decorated (string lights, a tennis
poster, his racket on the wall, a pennant, a rug, a plant on the sill, a mini-fridge).
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, ground_shadow, shrub, LEAF

INK = "#171a2b"

# --- palettes ---------------------------------------------------------------------------------
BLOCK = ["#5a4a4c", "#706058", "#8e7a68", "#a89276", "#b8a282", "#c4ae8c", "#d2bc98"]   # painted block, warm
TILE = ["#3a2c30", "#56443e", "#6a5648", "#786250", "#866e58", "#947c62", "#a48a6c"]     # vinyl tile
TRIM = ["#24161c", "#3a2420", "#4e3026", "#6a4230"]                                      # rubber cove base
OAK = ["#2c1a1a", "#4a2e22", "#6a4430", "#86583a", "#a06e48", "#b88658", "#cc9c6c"]      # dorm furniture
STEEL_W = ["#1e1c26", "#2e2c38", "#46424e", "#5e5864", "#7a7280"]                        # window frame
VINYL = ["#1a2440", "#243458", "#2e4472", "#3e5a8e", "#5878aa", "#7c98c4"]               # dorm mattress
CARD = ["#3e2a1e", "#5e4028", "#7e5834", "#9a7040", "#b48650", "#c89c62"]                # cardboard
TAPE = ["#8a7a5e", "#b8a67e", "#d8c8a0"]
NAVY = ["#141a30", "#1e2846", "#2a3860", "#3a4c7c", "#52669a"]                           # Jakerson's duvet
OLIVE = ["#232614", "#363a1e", "#4c5028", "#646a34", "#7e8442"]                          # his jacket colour
CREAM = ["#9a8a74", "#c0b094", "#e0d2b4", "#f2e8d0"]
GOLD = ["#c47a2c", "#e9a84a", "#f6cf7a", "#fff0c4"]
SUNLIGHT = "#ffd890"
RACKET = ["#1a1524", "#2a3a6a", "#4a6ab0", "#e6e2d8", "#c8c0a8"]


def _rng(seed):
    return np.random.default_rng(abs(int(seed)))


# --- walls and floor --------------------------------------------------------------------------
def block_wall(cv, x, y, w, h, seed=0, course=8, unit=18):
    """Painted cinder block: running bond, soft recessed joints, a few chips and paint drips."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, BLOCK[3])
    row = 0
    for yy in range(y, y + h, course):
        ch = min(course, y + h - yy)
        off = (unit // 2) if row % 2 else 0
        for xx in range(x - off, x + w, unit):
            x0, x1 = max(x, xx), min(x + w, xx + unit - 1)
            if x1 <= x0:
                continue
            tone = BLOCK[4] if rng.random() < 0.8 else BLOCK[5] if rng.random() < 0.6 else BLOCK[3]
            cv.rect(x0, yy, x1 - x0, ch - 1, tone)
            cv.hline(x0, yy, x1 - x0, shade(tone, 0.07))
            # the pitted face of the block shows through the paint as a few darker dimples
            for _ in range((x1 - x0) * ch // 30):
                cv.px(x0 + int(rng.integers(0, max(1, x1 - x0))), yy + 1 + int(rng.integers(0, max(1, ch - 2))), shade(tone, -0.07))
        cv.hline(x, yy + ch - 1, w, BLOCK[3])
        for xx in range(x - off + unit - 1, x + w, unit):
            if x <= xx < x + w:
                cv.vline(xx, yy, ch - 1, BLOCK[3])
        row += 1


def ceiling_band(cv, x, w, h=8):
    """The ceiling edge: a strip of acoustic tile in shadow, a painted cove line under it."""
    cv.rect(x, 0, w, h, "#2a2026")
    for xx in range(x, x + w, 3):
        cv.px(xx, 2 + (xx // 3) % 3, "#33282e")
    cv.hline(x, h - 2, w, BLOCK[1]); cv.hline(x, h - 1, w, BLOCK[2])
    cv.hline(x, h, w, C("#0d0b16", 0.25))


def cove_base(cv, x, y, w):
    """Rubber cove base along the foot of the wall."""
    cv.rect(x, y - 4, w, 4, TRIM[1]); cv.hline(x, y - 4, w, TRIM[3]); cv.hline(x, y - 1, w, TRIM[0])


def vct_floor(cv, x, y, w, h, seed=0, size=14):
    """Vinyl composition tile: square-ish tiles (a touch shorter going back), two alternating
    tones laid checker-loose, flecked, with scuffs and a faint wax sheen."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, TILE[1])
    yy, row = y, 0
    while yy < y + h:
        th = int(round(size * (0.72 + 0.28 * (yy - y) / max(1, h))))
        th = min(th, y + h - yy)
        for i, xx in enumerate(range(x, x + w, size)):
            x1 = min(x + w, xx + size - 1)
            r = rng.random()
            tone = TILE[4] if r < 0.62 else shade(TILE[4], 0.03) if r < 0.86 else TILE[3] if r < 0.95 else TILE[5]
            cv.rect(xx, yy, x1 - xx + 1, th, shade(tone, -0.07))      # joints barely show
            cv.rect(xx, yy, x1 - xx, th - 1, tone)
            cv.hline(xx, yy, x1 - xx, shade(tone, 0.05))
            for _ in range((x1 - xx) * th // 11):
                fx, fy = xx + int(rng.integers(0, max(1, x1 - xx))), yy + int(rng.integers(0, max(1, th - 1)))
                cv.px(fx, fy, shade(tone, float(rng.choice([-0.1, -0.05, 0.07]))))
            if rng.random() < 0.06:
                sx = xx + int(rng.integers(1, max(2, x1 - xx - 6)))
                cv.hline(sx, yy + int(rng.integers(2, max(3, th - 2))), int(rng.integers(3, 7)), shade(tone, -0.18))
        yy += th
        row += 1


def braided_rug(cv, cx, cy, rx, ry, seed=0):
    """An oval braided rug (navy, olive, cream, rust rings) - flat on the floor."""
    rings = [NAVY[2], CREAM[1], OLIVE[3], "#8e4a34", NAVY[3], CREAM[2], OLIVE[2], "#a85a3c", NAVY[2]]
    cv.ellipse(cx - rx - 1, cy - ry + 1, rx * 2 + 3, ry * 2 + 1, C("#0d0b16", 0.45))
    n = len(rings)
    for i, c in enumerate(rings):
        k = 1 - i / n
        erx, ery = max(2, int(rx * k)), max(1, int(ry * k))
        cv.ellipse(cx - erx, cy - ery, erx * 2 + 1, ery * 2 + 1, c)
    # braid stitches on each ring: short dark ticks along the ellipses
    for i in range(n):
        k = 1 - (i + 0.5) / n
        erx, ery = rx * k, ry * k
        steps = int(2 * np.pi * max(erx, 4) / 3)
        for s in range(steps):
            a = s / steps * 2 * np.pi
            px, py = int(round(cx + np.cos(a) * erx)), int(round(cy + np.sin(a) * ery))
            if s % 2 == 0:
                cv.px(px, py, shade(rings[i], -0.25))


def light_patch(cv, poly, colour=SUNLIGHT, alpha=0.22):
    cv.poly(poly, C(colour, alpha))


# --- the window -------------------------------------------------------------------------------
def window_view(w, h, seed=0, with_mask=False):
    """What the west window sees: gold sky, the Flatirons with the low sun just right of them,
    the green August campus (red tile roofs, sandstone, spruce and cottonwood) catching the light."""
    import lib_tennis as T
    rng = _rng(seed)
    cv = Canvas(w, h, seed=seed)
    sun = (w - 16, int(h * 0.40))
    T.golden_sky(cv, 0, 0, w, h, sun, seed=5, reach=150.0)
    for (x, y, ln, th) in [(6, 9, 40, 2), (58, 5, 34, 2), (100, 14, 26, 2)]:
        T.gold_cloud(cv, x, y, ln, th, rng)
    T.sun_disc(cv, *sun, r=6)
    sky = cv.a.copy()
    # the slabs fill the glass: the sun is going down just behind the right-hand ridge
    mtn, ridge = T.golden_flatirons(scale=2.15, colors=26)
    mh, mw = mtn.shape[:2]
    mx0 = int(mw * 0.2)
    crop = mtn[:, mx0:mx0 + w]
    top = int(ridge[mx0:mx0 + w].min())
    cv.paste(crop, 0, 9 - top)
    # far campus along the bottom: low red tile roofs, sandstone walls lit gold, green crowns
    base = h - 6
    for (rx, rw, rh) in [(6, 22, 6), (44, 16, 5), (88, 26, 7), (128, 18, 5)]:
        if rx >= w:
            continue
        top_y = base - rh - 5
        cv.rect(rx, top_y + 4, rw, rh + 4, "#c8946a")
        for k in range(rx + 2, rx + rw - 2, 4):
            cv.px(k, top_y + 6, "#5a3a3a"); cv.px(k, top_y + 7, "#f2c070")
        cv.poly([(rx - 2, top_y + 4), (rx + rw // 2, top_y), (rx + rw + 1, top_y + 4)], "#b0583e")
        cv.hline(rx - 1, top_y + 4, rw + 2, "#7a3a30"); cv.line(rx + rw // 2, top_y, rx + rw + 1, top_y + 4, "#e08a58")
    for i in range(int(w / 9)):
        tx = int(rng.integers(-4, w)); tr = int(rng.integers(3, 6))
        ty = base - int(rng.integers(-2, 4))
        cv.ellipse(tx - tr, ty - tr, tr * 2, tr * 2 - 1, "#3a5232")
        cv.ellipse(tx - tr + 1, ty - tr + 1, tr * 2 - 3, tr - 1, "#56703c")
        cv.px(tx + tr - 2, ty - tr + 1, "#c8b860")
    for sx in (30, 74, 118):
        if sx < w:
            for yy in range(0, 16):
                half = max(0, yy // 3)
                cv.hline(sx - half, base - 15 + yy, half * 2 + 1, "#2a3e34" if yy % 4 else "#344a3a")
            cv.px(sx + 1, base - 14, "#b8a858")
    cv.rect(0, base, w, h - base, "#3a5232")
    cv.hline(0, base, w, "#56703c")
    if with_mask:
        return cv, np.all(np.isclose(cv.a, sky), axis=-1)
    return cv


def casement_window(cv, x, y, w, h, seed=0, with_mask=False):
    """1950s steel casement: a deep painted reveal, bronze frames, a wide fixed centre light
    between two opening sashes (the right one propped open), sill, convector below."""
    view, sky = window_view(w, h, seed=seed, with_mask=True)
    # reveal
    cv.rect(x - 6, y - 6, w + 12, h + 10, BLOCK[2]); cv.rect(x - 5, y - 5, w + 10, h + 8, BLOCK[5])
    cv.hline(x - 5, y - 5, w + 10, BLOCK[6]); cv.vline(x - 5, y - 5, h + 8, BLOCK[6])
    cv.rect(x - 2, y - 2, w + 4, h + 4, STEEL_W[0])
    cv.paste(view, x, y)
    # frames: outer, two sash mullions, transom bars
    sash = w // 4
    for mx in (x + sash, x + w - sash - 1):
        cv.rect(mx - 1, y, 3, h, STEEL_W[1]); cv.vline(mx, y, h, STEEL_W[3])
    for k in (1, 2):
        ty = y + h * k // 3
        cv.hline(x, ty, sash, STEEL_W[2]); cv.hline(x + w - sash, ty, sash, STEEL_W[2])
    cv.rect(x, y, w, 2, STEEL_W[1]); cv.rect(x, y + h - 2, w, 2, STEEL_W[1])
    cv.vline(x, y, h, STEEL_W[1]); cv.vline(x + w - 1, y, h, STEEL_W[1])
    # glass sheen streaks on the centre light
    for gx in (x + sash + 14, x + sash + 20, x + w - sash - 30):
        cv.line(gx, y + h - 6, gx + 10, y + 8, C("#fff0c4", 0.16))
    # the right sash propped open: its frame swung into the room, catching the sun
    ox = x + w - sash
    cv.poly([(ox, y), (ox + sash - 8, y + 4), (ox + sash - 8, y + h - 2), (ox, y + h)], C("#fff0c4", 0.12))
    cv.line(ox + sash - 8, y + 4, ox + sash - 8, y + h - 2, STEEL_W[3])
    cv.line(ox, y, ox + sash - 8, y + 4, STEEL_W[3])
    cv.line(ox + sash - 8, y + h * 2 // 3, ox + sash - 3, y + h * 2 // 3 + 3, STEEL_W[4])   # stay arm
    # mini blinds pulled up into a bunch at the head
    cv.rect(x - 1, y - 1, w + 2, 6, "#d8ccb4")
    for yy in range(y, y + 5, 2):
        cv.hline(x - 1, yy, w + 2, "#b8aa90")
    cv.hline(x - 1, y + 5, w + 2, C("#0d0b16", 0.35))
    cv.vline(x + 12, y + 5, 22, "#b8aa90"); cv.rect(x + 11, y + 26, 3, 3, "#d8ccb4")
    # sill
    cv.rect(x - 8, y + h + 2, w + 16, 5, OAK[4]); cv.hline(x - 8, y + h + 2, w + 16, OAK[6])
    cv.hline(x - 8, y + h + 6, w + 16, OAK[1])
    if with_mask:
        # open sky still showing through the glass (frames, blinds and sheen excluded)
        sky = sky & np.all(np.isclose(cv.a[y:y + h, x:x + w], view.a), axis=-1)
        return y + h + 2, sky
    return y + h + 2


def convector(cv, x, y, w, h):
    """Steel convector cabinet under the window (1950s steam heat): louvred top, painted cream."""
    cv.rect(x, y, w, h, OUT)
    cv.rect(x + 1, y + 1, w - 2, h - 2, "#bcae96")
    cv.hline(x + 1, y + 1, w - 2, "#d6cab2")
    for gx in range(x + 4, x + w - 4, 3):
        cv.vline(gx, y + 3, 4, "#7e7262")
    cv.rect(x + 3, y + 9, w - 6, h - 12, "#a89a82")
    for gy in range(y + 11, y + h - 4, 2):
        cv.hline(x + 5, gy, w - 10, "#968a74")
    cv.rect(x + w - 12, y + 3, 6, 3, "#6a4430")   # the valve knob
    cv.hline(x, y + h, w, C("#0d0b16", 0.4))


# --- wall pieces ------------------------------------------------------------------------------
def dorm_door(cv, x, y, w, h):
    """The room door seen from inside: oak veneer, steel frame, lever handle, closer arm, the
    fire evacuation plan, a coat hook with a lanyard."""
    cv.rect(x - 4, y - 4, w + 8, h + 4, STEEL_W[1]); cv.rect(x - 3, y - 3, w + 6, h + 3, "#8a8070")
    cv.hline(x - 3, y - 3, w + 6, "#a89e8a")
    cv.rect(x, y, w, h, OAK[3])
    rng = _rng(7)
    for gx in range(x + 1, x + w - 1, 3):
        cv.vline(gx, y + int(rng.integers(0, 6)), h - 6, OAK[4] if (gx // 3) % 2 else OAK[3])
    cv.vline(x, y, h, OAK[5]); cv.vline(x + w - 1, y, h, OAK[1])
    # closer arm at the head
    cv.rect(x + 4, y + 2, 14, 4, STEEL_W[3]); cv.line(x + 17, y + 4, x + 28, y + 2, STEEL_W[2])
    # fire plan in a frame
    cv.rect(x + 11, y + 14, 22, 16, OUT); cv.rect(x + 12, y + 15, 20, 14, "#e6e0d0")
    cv.rect(x + 12, y + 15, 20, 3, "#c84a3c")
    for k in range(3):
        cv.hline(x + 14, y + 20 + k * 3, 10 + (k % 2) * 4, "#7a7a8a")
    cv.px(x + 27, y + 24, "#3cba7a"); cv.line(x + 16, y + 26, x + 26, y + 26, "#c84a3c")
    # lever handle and lock
    hx, hy = x + w - 9, y + h // 2 + 2
    cv.rect(hx, hy - 3, 4, 7, STEEL_W[2]); cv.rect(hx - 6, hy, 8, 2, "#c8c4bc"); cv.hline(hx - 6, hy, 8, "#ece8e0")
    cv.px(hx + 1, hy - 7, "#c8c4bc")
    # coat hook with a lanyard and a room key
    cv.rect(x + 18, y + 38, 3, 3, "#c8c4bc")
    cv.line(x + 19, y + 41, x + 15, y + 52, "#d0a040"); cv.line(x + 19, y + 41, x + 23, y + 52, "#d0a040")
    cv.rect(x + 17, y + 52, 5, 3, "#a8a8b0")
    # kick plate
    cv.rect(x + 1, y + h - 8, w - 2, 8, "#9a948a"); cv.hline(x + 1, y + h - 8, w - 2, "#c0bab0")


def corkboard_welcome(cv, x, y, w, h):
    """Jules's corkboard: empty except for the RA's welcome note, a floor-meeting slip and pins."""
    cv.rect(x - 2, y - 2, w + 4, h + 4, OAK[1]); cv.rect(x - 1, y - 1, w + 2, h + 2, OAK[4])
    cv.rect(x, y, w, h, "#9a6e48")
    rng = _rng(31)
    for _ in range(w * h // 5):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), "#7e5838" if rng.random() < 0.5 else "#b0845a")
    # a paper star with both names (the RA makes one for every room)
    sx, sy = x + 12, y + 13
    star = [(sx, sy - 10), (sx + 3, sy - 3), (sx + 10, sy - 3), (sx + 4, sy + 2), (sx + 7, sy + 9), (sx, sy + 5),
            (sx - 7, sy + 9), (sx - 4, sy + 2), (sx - 10, sy - 3), (sx - 3, sy - 3)]
    cv.poly([(px + 1, py + 1) for px, py in star], C("#0d0b16", 0.4))
    cv.poly(star, "#f2d27a"); cv.line(sx, sy - 10, sx + 3, sy - 3, "#fff0c4")
    cv.hline(sx - 3, sy - 1, 7, "#7e3a30"); cv.hline(sx - 3, sy + 2, 6, "#425da6")
    cv.px(sx, sy - 7, "#c84a3c")
    # welcome note
    nx, ny = x + 25, y + 4
    cv.rect(nx + 1, ny + 1, 20, 18, C("#0d0b16", 0.4)); cv.rect(nx, ny, 20, 18, "#e6e0d0")
    cv.hline(nx + 2, ny + 3, 14, "#c84a3c"); cv.hline(nx + 2, ny + 6, 16, "#6a6a7a"); cv.hline(nx + 2, ny + 9, 12, "#6a6a7a")
    cv.hline(nx + 2, ny + 12, 15, "#6a6a7a"); cv.ellipse(nx + 12, ny + 13, 5, 4, "#f2d27a"); cv.px(nx + 10, ny, "#3a7a5a")
    # floor meeting slip, slightly crooked
    cv.poly([(x + 6, y + 26), (x + 22, y + 24), (x + 23, y + 32), (x + 7, y + 34)], "#9fc2b0")
    cv.line(x + 9, y + 28, x + 19, y + 27, "#4a6a5a"); cv.line(x + 9, y + 31, x + 16, y + 30, "#4a6a5a")
    cv.px(x + 14, y + 25, "#c84a3c")
    # spare push pins along the frame
    for i, c in enumerate(["#c84a3c", "#425da6", "#e8b45c", "#5c897c"]):
        cv.px(x + w - 12 + i * 3, y + h - 4, c)


def wall_scars(cv, pts):
    """Leftovers of last year's residents: tape squares, a nail hole, a sticky-tack smudge."""
    for (x, y, kind) in pts:
        if kind == "tape":
            cv.rect(x, y, 4, 2, C("#e8dcc0", 0.7)); cv.rect(x + 18, y, 4, 2, C("#e8dcc0", 0.7))
            cv.rect(x, y + 22, 4, 2, C("#e8dcc0", 0.6)); cv.rect(x + 18, y + 22, 4, 2, C("#e8dcc0", 0.5))
        elif kind == "nail":
            cv.px(x, y, "#3a2a2a"); cv.px(x + 1, y, BLOCK[2])
        else:
            cv.rect(x, y, 2, 2, C("#7a6a8a", 0.6))


def tennis_poster(cv, x, y, w=34, h=46):
    """A vintage-style tournament print: a racket and a ball over a clay court, SET POINT."""
    cv.rect(x + 1, y + 1, w, h, C("#0d0b16", 0.5))
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, "#e6d6b1")
    cv.rect(x + 2, y + 2, w - 4, h - 14, "#c86a3c")                      # clay
    cv.rect(x + 2, y + 2, w - 4, 12, "#e8a860")                          # sky band
    cv.hline(x + 2, y + 24, w - 4, "#f2e8d0"); cv.vline(x + w // 2, y + 24, h - 38, "#f2e8d0")
    # racket
    cx, cy = x + 13, y + 14
    cv.ellipse(cx - 6, cy - 8, 13, 17, "#1a2a4a"); cv.ellipse(cx - 4, cy - 6, 9, 13, "#e8a860")
    for k in range(-3, 4, 2):
        cv.vline(cx + k, cy - 5, 11, C("#f2e8d0", 0.8))
    for k in range(-4, 6, 2):
        cv.hline(cx - 3, cy + k, 8, C("#f2e8d0", 0.8))
    cv.line(cx + 1, cy + 8, cx + 5, cy + 17, "#1a2a4a"); cv.line(cx + 2, cy + 8, cx + 6, cy + 17, "#3a2a2a")
    # ball
    cv.ellipse(x + w - 12, y + 6, 7, 7, "#d8e040"); cv.px(x + w - 10, y + 7, "#f2f8a0")
    cv.line(x + w - 11, y + 9, x + w - 7, y + 11, "#f2f8f0")
    text(cv, "SET", x + 3, y + h - 12, "#7e3a30")
    cv.hline(x + 21, y + h - 7, 10, "#7e3a30"); cv.hline(x + 21, y + h - 4, 7, "#7e3a30")


def band_poster(cv, x, y, w=24, h=32):
    """A gig poster from a Red Rocks show: a moon over red rock fins."""
    cv.rect(x + 1, y + 1, w, h, C("#0d0b16", 0.5))
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.dither_v(x, y, w, h - 8, "#2a2050", "#c45a5a", steps=4)
    cv.ellipse(x + w - 10, y + 3, 6, 6, "#f6e7c4")
    cv.poly([(x, y + h - 8), (x + 4, y + 12), (x + 9, y + h - 8)], "#8e3a2c")
    cv.poly([(x + 12, y + h - 8), (x + 18, y + 8), (x + w, y + h - 8)], "#a8483a")
    cv.line(x + 18, y + 8, x + 22, y + h - 9, "#d0704a")
    cv.rect(x, y + h - 8, w, 8, "#1a1424")
    cv.hline(x + 2, y + h - 6, w - 8, "#f6cd78"); cv.hline(x + 2, y + h - 3, w - 12, "#c8c0e0")


def pennant(cv, x, y, length=66, h=14, label="BOULDER"):
    """A felt banner pennant: a lettered panel tapering to a point, pinned at the left edge."""
    body = len(label) * 6 + 8
    pts = [(x, y), (x + body, y), (x + length, y + h // 2), (x + body, y + h), (x, y + h)]
    cv.poly([(px + 1, py + 1) for px, py in pts], C("#0d0b16", 0.4))
    cv.poly(pts, OUT)
    cv.poly([(x + 1, y + 1), (x + body, y + 1), (x + length - 3, y + h // 2), (x + body, y + h - 1), (x + 1, y + h - 1)], "#1a1418")
    cv.hline(x + 1, y + 1, body, "#2a2428")
    cv.rect(x, y, 4, h + 1, "#cfb87c"); cv.vline(x, y, h + 1, "#e6d6a0")
    text(cv, label, x + 6, y + (h - 8) // 2, "#cfb87c", advance=6)
    cv.px(x + 2, y + 2, "#c84a3c"); cv.px(x + 2, y + h - 2, "#c84a3c")


def wall_racket(cv, x, y):
    """Jakerson's racket hung on the wall on two hooks, head up, angled; a ball tube beside it."""
    cx, cy = x, y
    # head (oval frame), strings, throat, grip
    cv.ellipse(cx - 9, cy - 12, 19, 25, OUT)
    cv.ellipse(cx - 8, cy - 11, 17, 23, RACKET[2]); cv.ellipse(cx - 6, cy - 9, 13, 19, RACKET[1])
    cv.ellipse(cx - 5, cy - 8, 11, 17, C("#0d0b16", 0.25))
    for k in range(-4, 5, 2):
        cv.vline(cx + k, cy - 7, 15, RACKET[3])
    for k in range(-7, 8, 2):
        cv.hline(cx - 4, cy + k, 9, RACKET[4])
    cv.px(cx - 6, cy - 9, "#8aa8e0"); cv.px(cx - 5, cy - 10, "#8aa8e0")
    cv.poly([(cx - 3, cy + 11), (cx + 3, cy + 11), (cx + 1, cy + 17), (cx - 1, cy + 17)], RACKET[2])
    cv.rect(cx - 2, cy + 17, 4, 14, OUT); cv.rect(cx - 1, cy + 17, 2, 13, "#e6e2d8")
    for gy in range(cy + 18, cy + 30, 3):
        cv.px(cx - 1, gy, "#a8a498")
    cv.rect(cx - 2, cy + 30, 4, 2, RACKET[2])
    # hooks
    cv.rect(cx - 10, cy - 2, 2, 3, "#c8c4bc"); cv.rect(cx + 9, cy - 2, 2, 3, "#c8c4bc")


def string_lights(cv, x0, y0, x1, y1, sag=8, every=7, seed=0):
    """Warm fairy lights pinned along the wall; returns the bulb points for a twinkle layer."""
    rng = _rng(seed)
    pts = []
    n = max(2, int(abs(x1 - x0)))
    for i in range(n + 1):
        t = i / n
        xx = x0 + (x1 - x0) * t
        yy = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        p = (int(round(xx)), int(round(yy)))
        cv.px(p[0], p[1], "#2a2028")
        if i % every == every // 2:
            c = GOLD[2] if rng.random() < 0.8 else "#f2a0a0"
            cv.rect(p[0] - 2, p[1] - 1, 5, 5, C(c, 0.14))
            cv.px(p[0], p[1] + 1, c); cv.px(p[0], p[1] + 2, shade(c, 0.35))
            pts.append([p[0], p[1] + 1, c.lstrip("#"), 1])
    return pts


def photo_strip(cv, x, y):
    """Photos clipped to a twine line: friends from home, a dog, a tennis team."""
    cv.line(x, y, x + 34, y + 2, "#c8b090")
    cols = ["#5c897c", "#c86a3c", "#425da6", "#e8b45c"]
    for i in range(4):
        px, py = x + 2 + i * 8, y + 1 + (i // 2)
        cv.rect(px, py + 1, 7, 8, "#f2e8d0"); cv.rect(px + 1, py + 2, 5, 5, cols[i])
        cv.px(px + 2 + (i % 2), py + 4, "#f2d2a0")
        cv.rect(px + 3, py, 1, 2, "#a8a8b0")


def light_switch(cv, x, y):
    cv.rect(x, y, 6, 9, "#d8d0c0"); cv.rect(x + 2, y + 3, 2, 3, "#f2ece0"); cv.vline(x + 5, y, 9, "#a89e8a")


def thermostat(cv, x, y):
    cv.rect(x, y, 10, 7, "#d8d0c0"); cv.rect(x + 2, y + 2, 6, 3, "#5c897c"); cv.px(x + 3, y + 3, "#9ad0b8")


def smoke_detector(cv, x, y):
    cv.ellipse(x - 5, y, 11, 5, "#e6e0d0"); cv.hline(x - 4, y + 3, 9, "#b8b0a0"); cv.px(x + 2, y + 2, "#c84a3c")


# --- props --------------------------------------------------------------------------------------
def dorm_bed(made=True, seed=0, width=54, depth=70, head=24):
    """A twin XL on a raised oak frame, head against the wall, seen from the foot.
    made: Jakerson's (navy plaid duvet, two pillows, a throw, a racket bag on the foot).
    not made: Jules's (bare blue vinyl mattress, folded sheets, a pillow still in its bag)."""
    rng = _rng(seed)
    W_, H_ = width + 6, depth + head + 14
    cv = Canvas(W_, H_, seed=seed)
    ox, base = 3, H_ - 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    top_y = base - 12 - depth + 10          # mattress top surface starts here (just below the headboard)
    front = base - 12                        # front edge of the mattress top
    # headboard: oak panel with two rails
    hb = top_y - head + 8
    cv.rect(ox, hb, width, head, OUT)
    cv.rect(ox + 1, hb + 1, width - 2, head - 2, OAK[3])
    cv.hline(ox + 1, hb + 1, width - 2, OAK[5]); cv.hline(ox + 1, hb + 2, width - 2, OAK[4])
    for k in range(ox + 6, ox + width - 6, 8):
        cv.rect(k, hb + 6, 5, head - 10, OAK[2]); cv.vline(k, hb + 6, head - 10, OAK[4])
    # side rails (seen as thin strips at either side of the mattress)
    cv.rect(ox, top_y, 3, front - top_y + 2, OUT); cv.rect(ox + width - 3, top_y, 3, front - top_y + 2, OUT)
    cv.vline(ox + 1, top_y, front - top_y, OAK[4]); cv.vline(ox + width - 2, top_y, front - top_y, OAK[2])
    mx0, mx1 = ox + 2, ox + width - 2
    mw = mx1 - mx0
    if made:
        # duvet: navy with a cream and olive plaid, folded back at the head
        cv.rect(mx0, top_y, mw, front - top_y + 4, NAVY[2])
        for gx in range(mx0 + 3, mx1, 9):
            cv.vline(gx, top_y + 14, front - top_y - 10, NAVY[3]); cv.vline(gx + 1, top_y + 14, front - top_y - 10, C(CREAM[1], 0.5))
        for gy in range(top_y + 18, front, 9):
            cv.hline(mx0, gy, mw, NAVY[3]); cv.hline(mx0, gy + 1, mw, C(OLIVE[4], 0.6))
        cv.vline(mx0, top_y, front - top_y + 4, NAVY[4])
        cv.vline(mx1 - 1, top_y, front - top_y + 4, NAVY[1])
        # folded-back top edge and white sheet
        cv.rect(mx0, top_y + 11, mw, 4, CREAM[3]); cv.hline(mx0, top_y + 14, mw, CREAM[1])
        # pillows
        for px in (mx0 + 2, mx0 + mw // 2 + 1):
            cv.rect(px, top_y + 1, mw // 2 - 3, 10, OUT)
            cv.rect(px + 1, top_y + 2, mw // 2 - 5, 8, CREAM[2]); cv.hline(px + 1, top_y + 2, mw // 2 - 5, CREAM[3])
            cv.hline(px + 2, top_y + 8, mw // 2 - 7, CREAM[1])
        # olive throw folded across the foot
        cv.rect(mx0, front - 14, mw, 9, OLIVE[3]); cv.hline(mx0, front - 14, mw, OLIVE[4]); cv.hline(mx0, front - 6, mw, OLIVE[1])
        for fx in range(mx0 + 1, mx1, 2):
            cv.px(fx, front - 5, OLIVE[2])
        # racket bag lying on the throw (black with a blue stripe)
        bx = mx0 + 8
        cv.rect(bx, front - 22, 30, 10, OUT); cv.rect(bx + 1, front - 21, 28, 8, "#24222f")
        cv.hline(bx + 1, front - 21, 28, "#3a384e"); cv.hline(bx + 2, front - 17, 26, RACKET[2])
        cv.rect(bx + 24, front - 23, 5, 2, "#a8a8b0")
        # duvet hangs over the front edge
        cv.rect(mx0 - 1, front, mw + 2, 7, NAVY[2]); cv.hline(mx0 - 1, front, mw + 2, NAVY[3])
        for gx in range(mx0 + 3, mx1, 9):
            cv.vline(gx, front, 7, NAVY[3])
        cv.hline(mx0 - 1, front + 6, mw + 2, NAVY[0])
    else:
        # bare vinyl mattress with its seam piping and a ticket label
        cv.rect(mx0, top_y, mw, front - top_y + 4, VINYL[3])
        cv.rect(mx0 + 1, top_y + 1, mw - 2, front - top_y + 2, VINYL[3])
        cv.hline(mx0, top_y, mw, VINYL[5]); cv.vline(mx0, top_y, front - top_y + 4, VINYL[4])
        cv.vline(mx1 - 1, top_y, front - top_y + 4, VINYL[1])
        for gy in range(top_y + 6, front, 12):
            cv.hline(mx0 + 2, gy, mw - 4, VINYL[4])
        cv.line(mx0 + 6, top_y + 20, mx0 + 20, top_y + 40, C(VINYL[5], 0.5))   # sheen
        # folded sheets (stack) and a pillow in its plastic bag
        sx, sy = mx0 + 5, top_y + 6
        cv.rect(sx, sy, 22, 13, OUT)
        for k, c in enumerate([CREAM[2], "#9ac0d8", CREAM[3]]):
            cv.rect(sx + 1, sy + 1 + k * 4, 20, 4, c); cv.hline(sx + 1, sy + 4 + k * 4, 20, shade(c, -0.2))
        px_, py_ = mx0 + 28, top_y + 4
        cv.rect(px_, py_, 20, 13, OUT); cv.rect(px_ + 1, py_ + 1, 18, 11, CREAM[2])
        cv.rect(px_ + 1, py_ + 1, 18, 11, C("#c8e0f0", 0.35)); cv.line(px_ + 3, py_ + 2, px_ + 8, py_ + 10, "#ffffff")
        cv.rect(px_ + 14, py_ + 5, 4, 3, "#c84a3c")
        # a small box on the bed (desk stuff) with a strip of tape
        bx, by_ = mx0 + 11, front - 23
        cv.rect(bx, by_, 28, 17, OUT); cv.rect(bx + 1, by_ + 1, 26, 6, CARD[4]); cv.rect(bx + 1, by_ + 7, 26, 9, CARD[3])
        cv.vline(bx + 14, by_ + 1, 6, TAPE[2]); cv.hline(bx + 1, by_ + 7, 26, CARD[2])
        text(cv, "DESK", bx + 2, by_ + 7, "#2a1a14")
        # mattress front face
        cv.rect(mx0 - 1, front, mw + 2, 6, VINYL[2]); cv.hline(mx0 - 1, front, mw + 2, VINYL[4])
        cv.hline(mx0 - 1, front + 5, mw + 2, VINYL[0])
    # footboard rail and the raised frame with storage underneath
    fy = front + 6
    cv.rect(ox, fy, width, 4, OUT); cv.rect(ox + 1, fy + 1, width - 2, 2, OAK[5]); cv.hline(ox + 1, fy + 1, width - 2, OAK[6])
    cv.rect(ox + 3, fy + 4, width - 6, base - fy - 4, "#1a1218")
    for lx in (ox, ox + width - 4):
        cv.rect(lx, fy + 4, 4, base - fy - 4, OUT); cv.vline(lx + 1, fy + 4, base - fy - 5, OAK[4])
    if made:
        # a plastic bin and a pair of sneakers under the bed
        cv.rect(ox + 8, base - 6, 18, 6, "#c8d0d8"); cv.hline(ox + 8, base - 6, 18, "#e6ecf0"); cv.rect(ox + 9, base - 4, 16, 3, "#5a6a8a")
        cv.rect(ox + 32, base - 3, 7, 3, "#e6e2d8"); cv.rect(ox + 40, base - 3, 7, 3, "#e6e2d8")
        cv.px(ox + 33, base - 3, "#425da6"); cv.px(ox + 41, base - 3, "#425da6")
    else:
        cv.rect(ox + 10, base - 7, 22, 7, CARD[3]); cv.hline(ox + 10, base - 7, 22, CARD[4]); cv.vline(ox + 21, base - 7, 3, TAPE[2])
    return cv, ox + width // 2, base


def desk_hutch(kind="jakerson", width=56, seed=0):
    """Built-in oak desk with a hutch, seen from the front: a drawer stack, the top, two shelves.
    jakerson: laptop, books, a small trophy, a photo, a mug of pens, a speaker.
    jules: empty shelves, one open box on the top, a desk lamp still in its carton."""
    rng = _rng(seed)
    H_ = 98
    cv = Canvas(width + 6, H_ + 4, seed=seed)
    ox, base = 3, H_ + 1
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    top = base - 30                         # desk top front edge
    # hutch back and sides
    hy = top - 58
    cv.rect(ox, hy, width, 60, OUT)
    cv.rect(ox + 1, hy + 1, width - 2, 58, OAK[2])
    cv.rect(ox + 3, hy + 3, width - 6, 54, OAK[1])
    cv.rect(ox + 3, hy + 3, width - 6, 2, C("#0d0b16", 0.35))
    cv.hline(ox + 1, hy + 1, width - 2, OAK[5])
    shelf = hy + 24
    cv.rect(ox + 1, shelf, width - 2, 3, OAK[4]); cv.hline(ox + 1, shelf, width - 2, OAK[6]); cv.hline(ox + 1, shelf + 3, width - 2, C("#0d0b16", 0.4))
    # desk top (seen slightly from above) and the front apron
    cv.rect(ox - 1, top - 8, width + 2, 10, OUT)
    cv.rect(ox, top - 7, width, 8, OAK[4]); cv.hline(ox, top - 7, width, OAK[5]); cv.hline(ox, top, width, OAK[6])
    cv.rect(ox, top + 1, width, 4, OAK[3]); cv.hline(ox, top + 4, width, OAK[1])
    # drawer pedestal on the right, open knee space on the left
    px0 = ox + width - 22
    cv.rect(ox, top + 5, width, base - top - 5, OUT)
    cv.rect(ox + 1, top + 5, px0 - ox - 2, base - top - 6, "#1a1218")
    cv.rect(px0, top + 5, 21, base - top - 6, OAK[3])
    for k in range(3):
        dy = top + 6 + k * 8
        cv.rect(px0 + 1, dy, 19, 7, OAK[4]); cv.hline(px0 + 1, dy, 19, OAK[5]); cv.hline(px0 + 1, dy + 6, 19, OAK[1])
        cv.rect(px0 + 8, dy + 3, 5, 1, "#c8c4bc")
    cv.rect(ox + 1, top + 5, 3, base - top - 6, OAK[3])
    if kind == "jakerson":
        # top shelf: books in varied colours, a small trophy, a photo frame
        x = ox + 4
        for c in ["#7e3a30", "#2a3860", "#c88a3a", "#3e6663", "#5a2a4a", "#e6d6b1", "#2a2a3a"]:
            bw = int(rng.integers(3, 5)); bh = int(rng.integers(13, 19))
            cv.rect(x, shelf - bh, bw, bh, c); cv.vline(x, shelf - bh, bh, shade(c, 0.2)); cv.hline(x, shelf - bh + 3, bw, shade(c, 0.35))
            x += bw
        cv.poly([(x + 1, shelf), (x + 3, shelf - 16), (x + 6, shelf)], "#5a2a2a")   # a leaning book
        tx = ox + width - 16
        cv.rect(tx, shelf - 4, 8, 4, "#3a2a2a"); cv.rect(tx + 3, shelf - 9, 2, 5, GOLD[1])
        cv.poly([(tx, shelf - 15), (tx + 8, shelf - 15), (tx + 6, shelf - 9), (tx + 2, shelf - 9)], GOLD[2]); cv.px(tx + 2, shelf - 14, GOLD[3])
        cv.rect(tx - 12, shelf - 12, 9, 12, OUT); cv.rect(tx - 11, shelf - 11, 7, 10, "#e6e0d0"); cv.rect(tx - 10, shelf - 10, 5, 6, "#5c897c")
        # lower shelf: a speaker, a tin of tennis balls, a plant cutting in a jar
        cv.rect(ox + 5, top - 22, 10, 13, OUT); cv.rect(ox + 6, top - 21, 8, 11, "#24222f"); cv.ellipse(ox + 7, top - 18, 6, 6, "#3a384e")
        cv.rect(ox + 18, top - 21, 7, 12, OUT); cv.rect(ox + 19, top - 20, 5, 10, "#d8e040"); cv.hline(ox + 19, top - 20, 5, "#e6e2d8")
        cv.rect(ox + 28, top - 15, 6, 6, C("#a8d8e0", 0.6)); cv.vline(ox + 30, top - 21, 6, LEAF[3]); cv.px(ox + 29, top - 21, LEAF[4]); cv.px(ox + 32, top - 19, LEAF[4])
        # on the desk top: open laptop with a glowing screen, a mug of pens, a notebook
        lx = ox + 18
        cv.rect(lx, top - 17, 22, 13, OUT); cv.rect(lx + 1, top - 16, 20, 11, "#1e2a3a")
        for k, ln in enumerate([12, 8, 14, 6]):
            cv.hline(lx + 3, top - 14 + k * 2, ln, ["#7ae0a0", "#c8d0f0", "#7ae0a0", "#f6cd78"][k])
        cv.rect(lx - 2, top - 4, 26, 3, "#a8a8b0"); cv.hline(lx - 2, top - 4, 26, "#d0d0d8")
        cv.rect(ox + width - 14, top - 9, 6, 7, OUT); cv.rect(ox + width - 13, top - 8, 4, 6, "#c84a3c")
        cv.vline(ox + width - 12, top - 12, 4, "#e8b45c"); cv.vline(ox + width - 11, top - 13, 5, "#425da6")
        cv.rect(ox + 3, top - 5, 12, 3, "#e6e0d0"); cv.hline(ox + 3, top - 5, 12, "#ffffff")
    else:
        # hutch empty but for a couple of textbooks still in shrink wrap and the dust line
        cv.rect(ox + 6, shelf - 14, 5, 14, "#c84a3c"); cv.rect(ox + 11, shelf - 13, 5, 13, "#3a5a8a")
        cv.line(ox + 7, shelf - 12, ox + 14, shelf - 3, C("#ffffff", 0.5))
        cv.hline(ox + 20, shelf - 1, width - 26, C("#d8c8b0", 0.35))
        # open box on the desk with a mug and cables poking out
        bx = ox + 6
        cv.rect(bx, top - 19, 26, 16, OUT); cv.rect(bx + 1, top - 12, 24, 9, CARD[3]); cv.rect(bx + 1, top - 18, 24, 6, "#2a1a14")
        cv.poly([(bx, top - 19), (bx - 6, top - 24), (bx - 5, top - 19)], CARD[4])
        cv.poly([(bx + 25, top - 19), (bx + 32, top - 23), (bx + 30, top - 18)], CARD[5])
        cv.rect(bx + 4, top - 22, 6, 6, "#e6e0d0"); cv.rect(bx + 10, top - 21, 2, 3, "#e6e0d0")
        cv.line(bx + 16, top - 18, bx + 19, top - 26, "#24222f"); cv.line(bx + 19, top - 26, bx + 22, top - 24, "#24222f")
        text(cv, "MUGS", bx + 1, top - 12, "#2a1a14", advance=6)
        # desk lamp still in its printed carton
        lx = ox + width - 18
        cv.rect(lx, top - 26, 13, 22, OUT); cv.rect(lx + 1, top - 25, 11, 20, "#e6e0d0"); cv.rect(lx + 1, top - 25, 11, 4, "#5c897c")
        cv.line(lx + 4, top - 10, lx + 8, top - 18, "#3a3a4a"); cv.poly([(lx + 7, top - 19), (lx + 11, top - 17), (lx + 9, top - 15)], "#c88a3a")
    return cv, ox + width // 2, base


def desk_chair(seed=0, hoodie=False, facing=1):
    """A wooden dorm chair pulled out from the desk; Jakerson's has his hoodie over the back."""
    cv = Canvas(26, 42, seed=seed)
    cx, base = 13, 40
    ground_shadow(cv, cx, base, 10, 2)
    # back
    cv.rect(cx - 9, 2, 18, 18, OUT)
    cv.rect(cx - 8, 3, 16, 4, OAK[4]); cv.hline(cx - 8, 3, 16, OAK[5])
    for k in range(cx - 7, cx + 8, 4):
        cv.vline(k, 7, 12, OAK[3])
    cv.rect(cx - 8, 7, 2, 13, OAK[4]); cv.rect(cx + 6, 7, 2, 13, OAK[2])
    # seat
    cv.rect(cx - 10, 19, 20, 6, OUT); cv.rect(cx - 9, 20, 18, 2, OAK[5]); cv.rect(cx - 9, 22, 18, 2, OAK[3])
    # legs
    for lx in (cx - 9, cx + 7):
        cv.rect(lx, 25, 3, base - 25, OUT); cv.vline(lx + 1, 25, base - 26, OAK[4])
    cv.rect(cx - 7, 32, 14, 2, OAK[2])
    if hoodie:
        cv.rect(cx - 10, 1, 20, 12, OUT)
        cv.rect(cx - 9, 2, 18, 10, "#2e4472"); cv.hline(cx - 9, 2, 18, "#3e5a8e")
        cv.rect(cx - 9, 12, 5, 14, "#2e4472"); cv.vline(cx - 10, 12, 14, OUT); cv.vline(cx - 4, 12, 14, OUT)
        cv.vline(cx - 1, 6, 6, "#c8c4bc"); cv.vline(cx + 2, 6, 5, "#c8c4bc")
        cv.rect(cx - 9, 24, 5, 2, OUT)
    return cv, cx, base


def wardrobe(width=60, height=84, seed=0):
    """Built-in oak wardrobe with two doors; on top, Jakerson's suitcase and a ball tube."""
    cv = Canvas(width + 6, height + 30, seed=seed)
    ox, base = 3, height + 28
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    top = base - height
    cv.rect(ox, top - 6, width, 7, OUT); cv.rect(ox + 1, top - 5, width - 2, 5, OAK[5]); cv.hline(ox + 1, top - 5, width - 2, OAK[6])
    cv.rect(ox, top, width, height, OUT)
    cv.wood(ox + 1, top + 1, width - 2, height - 2, OAK[3], vertical=True, plank=7, seed=seed + 2)
    mid = ox + width // 2
    cv.vline(mid, top + 1, height - 2, OAK[1])
    for dx0, dx1 in ((ox + 4, mid - 3), (mid + 3, ox + width - 4)):
        cv.rect(dx0, top + 5, dx1 - dx0, height - 14, OAK[2]); cv.rect(dx0 + 1, top + 6, dx1 - dx0 - 2, height - 16, OAK[4])
        cv.hline(dx0 + 1, top + 6, dx1 - dx0 - 2, OAK[5])
    cv.rect(mid - 4, top + height // 2 - 4, 2, 8, "#c8c4bc"); cv.rect(mid + 3, top + height // 2 - 4, 2, 8, "#c8c4bc")
    # a mirror on the right door, catching the window's gold
    mx0 = mid + 7
    cv.rect(mx0, top + 10, width // 2 - 14, height - 30, "#6a6a80")
    cv.rect(mx0 + 1, top + 11, width // 2 - 16, height - 32, "#a8a0b8")
    cv.line(mx0 + 2, top + 40, mx0 + 10, top + 14, "#f6dca8"); cv.line(mx0 + 3, top + 46, mx0 + 12, top + 22, "#f6dca8")
    # toe kick
    cv.rect(ox + 1, base - 5, width - 2, 4, OAK[1])
    # suitcase on top (tipped on its side) and the ball tube
    sx = ox + 6
    cv.rect(sx, top - 22, 34, 17, OUT); cv.rect(sx + 1, top - 21, 32, 15, "#7a2a2a"); cv.hline(sx + 1, top - 21, 32, "#a84a40")
    for k in (sx + 9, sx + 24):
        cv.vline(k, top - 21, 15, "#5a1a1a")
    cv.rect(sx + 13, top - 25, 8, 4, OUT); cv.hline(sx + 14, top - 24, 6, "#3a3a4a")
    cv.rect(sx + 26, top - 18, 5, 4, "#e6e0d0")
    tx = ox + width - 14
    cv.rect(tx, top - 26, 8, 21, OUT); cv.rect(tx + 1, top - 25, 6, 19, C("#d8e8f0", 0.8))
    for k in range(3):
        cv.ellipse(tx + 1, top - 24 + k * 6, 6, 6, "#d8e040")
    cv.rect(tx, top - 27, 8, 3, "#2a2a3a")
    return cv, ox + width // 2, base


def box_stack(seed=0, labels=("BOOK", "JULES", "MISC")):
    """Jules's moving boxes: two side by side, one on top, tape and marker labels."""
    rng = _rng(seed)
    cv = Canvas(72, 58, seed=seed)
    ox, base = 3, 55
    ground_shadow(cv, ox + 32, base, 34, 3)

    def box(x, y, w, h, label, lid=6):
        cv.rect(x, y - lid, w, h + lid, OUT)
        cv.rect(x + 1, y - lid + 1, w - 2, lid - 1, CARD[4])            # top face
        cv.vline(x + w // 2, y - lid + 1, lid - 1, TAPE[2])
        cv.hline(x + 1, y - lid + 1, w - 2, CARD[5])
        cv.rect(x + 1, y, w - 2, h - 1, CARD[3])                          # front face
        cv.hline(x + 1, y, w - 2, CARD[2])
        cv.vline(x + w - 2, y, h - 1, CARD[2])
        cv.rect(x + w // 2 - 1, y, 3, 5, C(TAPE[1], 0.9))
        for _ in range(3):
            cv.px(x + 2 + int(rng.integers(0, w - 4)), y + 2 + int(rng.integers(0, h - 4)), CARD[2])
        tw = len(label) * 6
        text(cv, label, x + (w - tw) // 2 + 1, y + h // 2 - 4, "#2a1a14")
    box(ox, base - 20, 32, 20, labels[0])
    box(ox + 32, base - 22, 34, 22, labels[1])
    box(ox + 12, base - 44, 34, 18, labels[2], lid=6)
    # a roll of tape on the top box
    cv.ellipse(ox + 38, base - 54, 8, 5, "#b8a67e"); cv.ellipse(ox + 40, base - 53, 4, 3, CARD[2])
    return cv, ox + 32, base


def duffel_pile(seed=0):
    """A duffel bag, a rolled rug tied with string, and a laundry bag, all just dropped."""
    cv = Canvas(70, 30, seed=seed)
    ox, base = 3, 27
    ground_shadow(cv, ox + 32, base, 34, 3)
    # rolled rug (lying along the floor)
    cv.rect(ox, base - 12, 36, 11, OUT); cv.rect(ox + 1, base - 11, 34, 9, "#a85a3c")
    for k in range(ox + 3, ox + 34, 4):
        cv.vline(k, base - 11, 9, "#c87a50")
    cv.ellipse(ox + 30, base - 12, 9, 11, OUT); cv.ellipse(ox + 31, base - 11, 7, 9, "#c87a50"); cv.ellipse(ox + 33, base - 9, 3, 4, "#7a3a2a")
    cv.vline(ox + 10, base - 12, 11, "#e6d6b1"); cv.vline(ox + 22, base - 12, 11, "#e6d6b1")
    # duffel bag
    dx = ox + 30
    cv.ellipse(dx, base - 18, 34, 18, OUT); cv.ellipse(dx + 1, base - 17, 32, 16, "#3e6663"); cv.ellipse(dx + 3, base - 16, 26, 7, "#56837a")
    cv.hline(dx + 4, base - 10, 26, "#2e4f50"); cv.line(dx + 8, base - 17, dx + 14, base - 22, OUT); cv.line(dx + 22, base - 17, dx + 16, base - 22, OUT)
    cv.rect(dx + 14, base - 14, 6, 3, "#e8b45c")
    return cv, ox + 32, base


def mini_fridge(seed=0):
    """A mini-fridge with a microwave on top, magnets, a cereal box and a fruit bowl."""
    cv = Canvas(34, 64, seed=seed)
    ox, base = 3, 61
    w = 26
    ground_shadow(cv, ox + w // 2, base, w // 2 + 2, 2)
    # fridge
    cv.rect(ox, base - 30, w, 30, OUT); cv.rect(ox + 1, base - 29, w - 2, 28, "#2a2a34"); cv.hline(ox + 1, base - 29, w - 2, "#4a4a58")
    cv.vline(ox + 1, base - 29, 28, "#3a3a46")
    cv.rect(ox + w - 5, base - 25, 2, 12, "#a8a8b0")
    cv.hline(ox + 1, base - 22, w - 2, "#1a1a22")
    for (mx, my, c) in [(5, 18, "#e8b45c"), (10, 14, "#c84a3c"), (6, 9, "#5c897c")]:
        cv.rect(ox + mx, base - my, 3, 3, c)
    cv.rect(ox + 11, base - 20, 7, 9, "#e6e0d0")   # a schedule under a magnet
    # microwave
    my = base - 30
    cv.rect(ox, my - 15, w, 15, OUT); cv.rect(ox + 1, my - 14, w - 2, 13, "#c8c8d0"); cv.hline(ox + 1, my - 14, w - 2, "#e6e6ee")
    cv.rect(ox + 3, my - 12, 15, 9, "#1e2230"); cv.line(ox + 4, my - 4, ox + 9, my - 11, C("#8a96c8", 0.4))
    cv.rect(ox + 20, my - 12, 4, 3, "#3a4a3a"); cv.px(ox + 21, my - 11, "#7af08a")
    for k in range(3):
        cv.rect(ox + 20, my - 8 + k * 2, 4, 1, "#8a8a98")
    # cereal box and a bowl of apples on top
    cv.rect(ox + 3, my - 31, 10, 16, OUT); cv.rect(ox + 4, my - 30, 8, 15, "#e8b45c"); cv.rect(ox + 5, my - 26, 6, 5, "#c84a3c")
    cv.ellipse(ox + 14, my - 21, 11, 6, "#e6e0d0")
    for (ax_, ay_, c) in [(15, 23, "#c84a3c"), (18, 24, "#a8c040"), (20, 22, "#c84a3c")]:
        cv.ellipse(ox + ax_, my - ay_, 4, 4, c)
    return cv, ox + w // 2, base


def desk_lamp(height=52):
    """Jakerson's arm lamp standing on his desk; the sprite reaches down to the desk's floor line
    so it y-sorts in front of the desk (the light is at h - 5)."""
    cv = Canvas(22, height + 2, seed=3)
    cx, base = 11, height
    foot = base - 34                      # desk top surface on screen relative to the anchor
    cv.rect(cx - 5, foot - 2, 10, 3, OUT); cv.rect(cx - 4, foot - 2, 8, 2, "#2e3a2a"); cv.hline(cx - 4, foot - 2, 8, "#4a5a3a")
    cv.line(cx, foot - 2, cx - 3, foot - 10, OUT); cv.line(cx + 1, foot - 2, cx - 2, foot - 10, "#4a5a3a")
    cv.line(cx - 3, foot - 10, cx + 3, foot - 15, OUT); cv.line(cx - 2, foot - 10, cx + 4, foot - 15, "#4a5a3a")
    # shade, glowing
    head_y = base - height + 5
    cv.poly([(cx + 1, head_y - 3), (cx + 8, head_y - 1), (cx + 6, head_y + 5), (cx - 2, head_y + 3)], OUT)
    cv.poly([(cx + 2, head_y - 2), (cx + 7, head_y), (cx + 5, head_y + 4), (cx - 1, head_y + 2)], "#3e5a3a")
    cv.line(cx - 1, head_y + 3, cx + 5, head_y + 5, GOLD[3])
    cv.rect(cx, head_y + 4, 4, 2, C(GOLD[2], 0.7))
    return cv, cx, base


def sill_plants(cv, x, y):
    """Pothos trailing from a terracotta pot and a little cactus on the right half of the sill."""
    pot = shrub(0, 0, 18, 12, seed=41, density=1.2)
    cv.paste(pot, x - 2, y - 14)
    cv.poly([(x + 1, y - 6), (x + 14, y - 6), (x + 12, y), (x + 3, y)], OUT)
    cv.poly([(x + 2, y - 5), (x + 13, y - 5), (x + 11, y - 1), (x + 4, y - 1)], "#b86a4a")
    cv.hline(x + 1, y - 6, 14, "#d08a64")
    for k, (dx, ln) in enumerate([(3, 10), (12, 16)]):
        for i in range(ln):
            cv.px(x + dx + (i % 3 == 1), y + i, LEAF[3] if i % 2 else LEAF[4])
    cx = x + 30
    cv.rect(cx, y - 5, 7, 5, OUT); cv.rect(cx + 1, y - 4, 5, 4, "#c8c0e0")
    cv.rect(cx + 2, y - 12, 3, 8, "#4a7a4a"); cv.vline(cx + 2, y - 12, 8, "#6a9a5a"); cv.px(cx + 3, y - 13, "#f2a0c0")


def box_fan(seed=0):
    """Jules's box fan (it is August, the room is on the sunny side): white frame, grille, blades."""
    cv = Canvas(30, 36, seed=seed)
    cx, base = 15, 34
    ground_shadow(cv, cx, base, 12, 2)
    x0, y0, s = 2, 4, 26
    cv.rect(x0, y0, s, s, OUT)
    cv.rect(x0 + 1, y0 + 1, s - 2, s - 2, "#d8d4cc"); cv.hline(x0 + 1, y0 + 1, s - 2, "#f2eee6"); cv.vline(x0 + s - 2, y0 + 1, s - 2, "#a8a49c")
    cv.rect(x0 + 3, y0 + 3, s - 6, s - 6, "#2a2832")
    c0 = (x0 + s // 2, y0 + s // 2)
    for a in range(3):
        ang = a * 2 * np.pi / 3 + 0.4
        tip = (c0[0] + np.cos(ang) * 9, c0[1] + np.sin(ang) * 9)
        side = (c0[0] + np.cos(ang + 0.7) * 7, c0[1] + np.sin(ang + 0.7) * 7)
        cv.poly([c0, tip, side], "#8a96b0")
        cv.line(c0[0], c0[1], int(tip[0]), int(tip[1]), "#b0bcd0")
    for gy in range(y0 + 4, y0 + s - 3, 3):
        cv.hline(x0 + 3, gy, s - 6, C("#c8c4bc", 0.45))
    cv.rect(c0[0] - 2, c0[1] - 2, 5, 5, "#d8d4cc"); cv.px(c0[0], c0[1], "#5c897c")
    cv.rect(x0 + s - 8, y0 - 3, 6, 3, OUT); cv.hline(x0 + s - 7, y0 - 2, 4, "#a8a49c")   # dial on top
    for fx in (x0 + 3, x0 + s - 6):
        cv.rect(fx, y0 + s, 3, base - y0 - s, OUT)
    return cv, cx, base


def bean_bag(seed=0):
    """Jakerson's olive bean bag, slumped, a game controller left on it."""
    cv = Canvas(48, 34, seed=seed)
    cx, base = 24, 31
    ground_shadow(cv, cx, base, 20, 3)
    cv.ellipse(3, 6, 42, 26, OUT)
    cv.ellipse(4, 7, 40, 24, OLIVE[2])
    cv.ellipse(6, 8, 30, 14, OLIVE[3]); cv.ellipse(9, 9, 18, 7, OLIVE[4])
    cv.ellipse(14, 12, 22, 9, OLIVE[1])                       # the dent where someone sat
    cv.line(8, 22, 18, 26, OLIVE[1]); cv.line(30, 25, 40, 20, OLIVE[1])
    cv.rect(26, 9, 9, 5, OUT); cv.rect(27, 10, 7, 3, "#2a2a34"); cv.px(28, 11, "#c84a3c"); cv.px(32, 11, "#5c897c")
    return cv, cx, base


def movein_cart(seed=0):
    """A move-in day rolling bin (the volunteers' gold canvas carts): a laundry basket, a lamp
    with its shade on crooked, pillows and a poster tube - the rest of Jules's stuff."""
    cv = Canvas(70, 56, seed=seed)
    ox, base = 4, 53
    w = 60
    ground_shadow(cv, ox + w // 2, base, w // 2 + 2, 3)
    top = base - 30
    # contents first (they stick up out of the bin)
    cv.rect(ox + 6, top - 10, 26, 12, OUT); cv.rect(ox + 7, top - 9, 24, 10, "#c8d0d8")          # laundry basket
    for k in range(ox + 9, ox + 30, 3):
        cv.vline(k, top - 7, 7, "#8a98a8")
    cv.rect(ox + 10, top - 14, 14, 6, "#e6e0d0"); cv.hline(ox + 10, top - 14, 14, "#ffffff")      # folded towels
    cv.rect(ox + 34, top - 9, 20, 11, OUT); cv.rect(ox + 35, top - 8, 18, 9, "#c86a8a")          # pillow
    cv.hline(ox + 35, top - 8, 18, "#e08aa8")
    cv.vline(ox + 46, top - 28, 20, "#2a2832"); cv.vline(ox + 47, top - 28, 20, "#4a4858")         # lamp pole
    cv.poly([(ox + 40, top - 26), (ox + 52, top - 30), (ox + 55, top - 20), (ox + 42, top - 17)], OUT)
    cv.poly([(ox + 41, top - 25), (ox + 51, top - 29), (ox + 54, top - 21), (ox + 43, top - 18)], "#e6d6b1")
    cv.line(ox + 26, top - 2, ox + 36, top - 26, OUT); cv.line(ox + 27, top - 2, ox + 37, top - 26, "#425da6")   # poster tube
    cv.line(ox + 28, top - 2, ox + 38, top - 26, "#5671b0")
    # the bin: gold canvas on a steel frame, CU volunteers' tag
    cv.rect(ox, top, w, 24, OUT)
    cv.rect(ox + 1, top + 1, w - 2, 22, "#c89c34"); cv.hline(ox + 1, top + 1, w - 2, "#e4c060")
    for k in range(ox + 6, ox + w - 4, 10):
        cv.vline(k, top + 3, 19, "#a07a26")
    cv.hline(ox + 1, top + 22, w - 2, "#74561e")
    cv.rect(ox - 1, top - 1, w + 2, 3, IRON[3]); cv.hline(ox - 1, top - 1, w + 2, IRON[4])
    cv.rect(ox + w // 2 - 8, top + 8, 16, 10, "#1a1418")
    text(cv, "07", ox + w // 2 - 6, top + 9, "#e4c060", advance=6)
    # casters
    for wx in (ox + 3, ox + w - 8):
        cv.rect(wx, base - 6, 5, 6, OUT); cv.rect(wx + 1, base - 4, 3, 3, IRON[3])
    return cv, ox + w // 2, base
