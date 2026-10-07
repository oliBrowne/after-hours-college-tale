"""The Hill (H01, H02): frat row on College Ave at night and the party inside one of the houses.

Big old Hill houses at character scale (doors 72px, porch columns about 94px): clapboard, red brick
and Tudor stucco over sandstone foundations, deep porches with lattice skirts and front steps.
Every house and its Greek letters are fictional (GAMMA THETA XI, XI OMEGA LAMBDA, PHI XI PI).
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, LEAF, ground_shadow, shrub
from facade import BRICK, SANDSTONE, TRIM, FRAME, GLOW, DARKGLASS, brick_wall
from surfaces import ashlar_wall

INK = "#171a2b"
SHADOW = "#0d0b16"

# --- palettes -------------------------------------------------------------------------------
CLAP_SAGE = ["#18242a", "#22343a", "#2e4648", "#3a5a58", "#4a6e68", "#5e847a", "#78a092"]    # party house siding
CLAP_CREAM = ["#4a4038", "#6e6052", "#8e7e6a", "#a89680", "#c2b098", "#d8c8ac", "#e8dcc2"]   # trim and the Tudor stucco
SLATE = ["#141420", "#1c1c2a", "#252434", "#2f2d40", "#3a374c", "#48435a", "#5a536a"]         # roof shingles
PORCH_GREY = ["#262430", "#34323e", "#44414c", "#55525c", "#68646c", "#7c7880"]               # painted porch decking
TIMBER = ["#1e1416", "#2e1e1c", "#3e2a24", "#523a2e"]                                       # half-timbering
DOOR_RED = ["#3a1418", "#5a1c20", "#7a2a2a", "#9a3a32", "#b44e3e"]
DOOR_GREEN = ["#142420", "#1c3430", "#264840", "#345e52", "#4a7a6a"]
PARTY = {"pink": ["#5a1a4a", "#a82a7a", "#e04aa0", "#ff8ad0", "#ffd0ec"],
         "cyan": ["#123a4a", "#1e6a8a", "#2aa8c8", "#6ad8f0", "#c8f4ff"],
         "violet": ["#2a1a5a", "#4a2a9a", "#7a4ae0", "#a88af0", "#dcd0ff"],
         "amber": GLOW}
CUP = ["#5a1418", "#8a1e22", "#c42e2e", "#e4524a", "#f2ece0"]                                  # red party cups, white rims
ASPHALT = ["#1c1a22", "#24222a", "#2a2832", "#312f39", "#38363f", "#423f48"]
CURB = ["#5a5862", "#7a7882", "#9a98a2", "#b4b2ba"]
GRASS_H = ["#121c1a", "#18241f", "#1f2e26", "#283a2e", "#324838", "#3e5640", "#4c6648", "#5e7850"]


def _rng(seed):
    return np.random.default_rng(seed)


# --- Greek letters (all houses fictional) -------------------------------------------------------
_GLYPHS = {
    "G": ["########", "########", "##......", "##......", "##......", "##......", "##......", "##......", "##......", "###....."],
    "D": ["...##...", "...##...", "..####..", "..####..", ".##..##.", ".##..##.", "##....##", "##....##", "########", "########"],
    "TH": [".######.", "##....##", "##....##", "##....##", "########", "########", "##....##", "##....##", "##....##", ".######."],
    "L": ["...##...", "...##...", "..####..", "..####..", ".##..##.", ".##..##.", ".##..##.", "##....##", "##....##", "##....##"],
    "X": ["########", "########", "........", "........", ".######.", ".######.", "........", "........", "########", "########"],
    "P": ["########", "########", "##....##", "##....##", "##....##", "##....##", "##....##", "##....##", "##....##", "##....##"],
    "S": ["########", "########", ".##.....", "..##....", "...##...", "...##...", "..##....", ".##.....", "########", "########"],
    "PH": ["...##...", ".######.", "##.##.##", "##.##.##", "##.##.##", "##.##.##", "##.##.##", ".######.", "...##...", "...##..."],
    "PS": ["##.##.##", "##.##.##", "##.##.##", "##.##.##", "##.##.##", ".######.", "..####..", "...##...", "...##...", "..####.."],
    "O": ["..####..", ".##..##.", "##....##", "##....##", "##....##", "##....##", ".##..##.", "..#..#..", "###..###", "###..###"],
}
GREEK = {"GAMMA": "G", "DELTA": "D", "THETA": "TH", "LAMBDA": "L", "XI": "X", "PI": "P", "SIGMA": "S",
         "PHI": "PH", "PSI": "PS", "OMEGA": "O"}
HOUSE_A = ("GAMMA", "THETA", "XI")      # quiet brick house
HOUSE_B = ("XI", "OMEGA", "LAMBDA")     # the party house (the rush chair's house)
HOUSE_C = ("PHI", "XI", "PI")           # Tudor house, mostly asleep


def greek_width(names, scale=2, gap=4):
    return len(names) * 8 * scale + (len(names) - 1) * gap


def greek_mask(name, scale=2):
    g = _GLYPHS[GREEK[name]]
    m = np.array([[ch == "#" for ch in row] for row in g], bool)
    return np.repeat(np.repeat(m, scale, 0), scale, 1)


def greek_letters(cv, names, x, y, scale=2, gap=4, face="#e8dcc2", hi=None, dark=None, outline=OUT, drop=True):
    """Wooden or brass letters mounted on a wall: outline, face, lit top-left edge, dark lower edge,
    a soft drop shadow on the wall. Returns the total width."""
    hi = hi or shade(face, 0.3)
    dark = dark or shade(face, -0.35)
    cx = x
    for name in names:
        m = greek_mask(name, scale)
        h, w = m.shape
        if drop:
            ys, xs = np.where(m)
            for yy, xx in zip(ys, xs):
                cv.px(cx + xx + 2, y + yy + 2, C(SHADOW, 0.35))
        # outline ring
        pad = np.pad(m, 1)
        ring = (np.roll(pad, 1, 0) | np.roll(pad, -1, 0) | np.roll(pad, 1, 1) | np.roll(pad, -1, 1)) & ~pad
        ys, xs = np.where(ring)
        for yy, xx in zip(ys, xs):
            cv.px(cx + xx - 1, y + yy - 1, outline)
        ys, xs = np.where(m)
        for yy, xx in zip(ys, xs):
            up = yy == 0 or not m[yy - 1, xx]
            left = xx == 0 or not m[yy, xx - 1]
            down = yy == h - 1 or not m[yy + 1, xx]
            right = xx == w - 1 or not m[yy, xx + 1]
            c = hi if (up or left) else dark if (down or right) else face
            cv.px(cx + xx, y + yy, c)
        cx += w + gap
    return cx - gap - x


def greek_small(cv, names, x, y, colour, gap=2):
    """Letters at 1x (8x10) in a flat colour, for banners, paddles and flags."""
    cx = x
    for name in names:
        m = greek_mask(name, 1)
        ys, xs = np.where(m)
        for yy, xx in zip(ys, xs):
            cv.px(cx + xx, y + yy, colour)
        cx += m.shape[1] + gap
    return cx - gap - x


# --- walls ------------------------------------------------------------------------------------
def clapboard(cv, x, y, w, h, pal=CLAP_SAGE, board=4, seed=0, light=0.0):
    """Lap siding: 4px boards, a lit lip under each lap, a shadow line, the odd butt joint and
    a few spots where the paint has gone."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[3])
    for k, yy in enumerate(range(y, y + h, board)):
        bh = min(board, y + h - yy)
        tone = pal[3] if (k * 7 + seed) % 5 else pal[2]
        cv.rect(x, yy, w, bh, tone)
        cv.hline(x, yy, w, pal[1])                        # shadow under the lap above
        if bh > 1:
            cv.hline(x, yy + 1, w, shade(tone, 0.12))     # lit lip
        for _ in range(max(1, w // 70)):
            jx = x + int(rng.integers(4, max(5, w - 4)))
            cv.vline(jx, yy + 1, bh - 1, pal[1])
        if rng.random() < 0.25:
            px_ = x + int(rng.integers(0, max(1, w - 6)))
            cv.hline(px_, yy + 2, int(rng.integers(2, 6)), pal[4])
    if light:
        cv.rect(x, y, w, h, C("#f6cf7a", light))


def stucco_tudor(cv, x, y, w, h, seed=0, timbers=True):
    """Cream stucco with dark half-timbering: posts, a sill beam and a pair of braces."""
    rng = _rng(seed)
    pal = CLAP_CREAM
    cv.rect(x, y, w, h, pal[3])
    for _ in range(w * h // 6):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), pal[int(rng.choice([2, 4, 4]))])
    if timbers:
        for tx in range(x, x + w, 26):
            cv.rect(tx, y, 4, h, TIMBER[2]); cv.vline(tx, y, h, TIMBER[3]); cv.vline(tx + 3, y, h, TIMBER[0])
        cv.rect(x, y + h - 5, w, 5, TIMBER[2]); cv.hline(x, y + h - 5, w, TIMBER[3])
        cv.rect(x, y, w, 4, TIMBER[2]); cv.hline(x, y + 3, w, TIMBER[0])


def foundation(cv, x, y, w, h, seed=0):
    """Rough sandstone foundation showing below the porch or wall line."""
    ashlar_wall(cv, x, y, w, h, SANDSTONE, course=4, seed=seed, cap=False)
    cv.rect(x, y, w, h, C(SHADOW, 0.25))


# --- windows and doors ------------------------------------------------------------------------
def house_window(cv, x, y, w, h, mode="warm", seed=0, trim=CLAP_CREAM, blinds=0.0, curtain=None, shutters=None):
    """Double-hung window in a wide painted surround. mode: warm, dark, tv, or a PARTY colour."""
    rng = _rng(seed)
    # surround and head
    cv.rect(x - 4, y - 6, w + 8, h + 9, OUT)
    cv.rect(x - 3, y - 5, w + 6, h + 7, trim[4]); cv.hline(x - 3, y - 5, w + 6, trim[6]); cv.vline(x - 3, y - 5, h + 7, trim[5])
    cv.vline(x + w + 2, y - 5, h + 7, trim[2])
    cv.rect(x - 5, y - 8, w + 10, 3, trim[5]); cv.hline(x - 5, y - 8, w + 10, trim[6]); cv.hline(x - 5, y - 6, w + 10, trim[2])
    cv.rect(x - 1, y - 1, w + 2, h + 2, FRAME)
    if mode == "dark":
        pal = DARKGLASS
        for yy in range(y, y + h):
            t = (yy - y) / h
            cv.hline(x, yy, w, pal[2] if t < 0.3 else pal[1] if t < 0.8 else pal[0])
        cv.line(x + 1, y + h // 2 - 2, x + w // 2, y + 1, pal[3]); cv.line(x + 2, y + h - 3, x + w - 3, y + h // 2 + 1, pal[2])
    elif mode == "tv":
        cv.rect(x, y, w, h, "#1e2a4a")
        cv.rect(x, y + h // 2, w, h - h // 2, "#26365e")
        cv.rect(x + w // 3, y + h // 3, w // 3 + 1, h // 4, C("#8ab0f0", 0.6))
    else:
        pal = PARTY[mode] if mode in PARTY and mode != "amber" else GLOW
        for yy in range(y, y + h):
            t = (yy - y) / h
            cv.hline(x, yy, w, pal[3] if t < 0.25 else pal[2] if t < 0.7 else pal[1])
        cv.rect(x + 1, y + 1, max(1, w // 3), max(1, h // 4), pal[4])
        if mode in PARTY and mode != "amber":
            # silhouettes of the crowd inside, heads and shoulders against the light
            for k in range(int(rng.integers(1, 3))):
                hx = x + 2 + int(rng.integers(0, max(1, w - 8)))
                hy = y + h - 11 + int(rng.integers(-2, 3))
                cv.ellipse(hx, hy, 5, 6, pal[0]); cv.rect(hx - 2, hy + 5, 9, y + h - hy - 5, pal[0])
    if blinds:
        for yy in range(y, y + int(h * blinds), 2):
            cv.hline(x, yy, w, C(trim[4], 0.55))
        cv.hline(x, y + int(h * blinds), w, trim[2])
    if curtain:
        cv.rect(x, y, 3, h, curtain); cv.rect(x + w - 3, y, 3, h, curtain)
        cv.vline(x + 1, y, h, shade(curtain, 0.2)); cv.vline(x + w - 2, y, h, shade(curtain, -0.25))
    # sashes: meeting rail and the muntin of the upper sash
    cv.rect(x, y + h // 2 - 1, w, 2, trim[3]); cv.hline(x, y + h // 2 - 1, w, trim[5])
    cv.vline(x + w // 2, y, h // 2, trim[3])
    # sill
    cv.rect(x - 5, y + h + 1, w + 10, 3, trim[5]); cv.hline(x - 5, y + h + 1, w + 10, trim[6])
    cv.hline(x - 5, y + h + 4, w + 10, C(SHADOW, 0.5))
    if shutters:
        for sx in (x - 4 - 8, x + w + 4):
            cv.rect(sx, y - 5, 8, h + 7, OUT); cv.rect(sx + 1, y - 4, 6, h + 5, shutters)
            for yy in range(y - 2, y + h, 3):
                cv.hline(sx + 1, yy, 6, shade(shutters, -0.3))


def front_door(cv, cx, bottom, w=34, h=72, colour=DOOR_RED, open_=False, trim=CLAP_CREAM, glow=GLOW, seed=0):
    """A panelled front door with sidelight-free surround, transom, knocker; open_ swings it in
    and shows the warm hall (or the party light) behind."""
    x, top = cx - w // 2, bottom - h
    cv.rect(x - 7, top - 12, w + 14, h + 12, OUT)
    cv.rect(x - 6, top - 11, w + 12, h + 11, trim[4]); cv.hline(x - 6, top - 11, w + 12, trim[6])
    cv.vline(x - 6, top - 11, h + 11, trim[5]); cv.vline(x + w + 5, top - 11, h + 11, trim[2])
    cv.rect(x - 8, top - 14, w + 16, 4, trim[5]); cv.hline(x - 8, top - 14, w + 16, trim[6])
    # transom over the door
    cv.rect(x, top - 9, w, 7, FRAME); cv.rect(x + 1, top - 8, w - 2, 5, glow[3])
    for mx in range(x + 5, x + w - 2, 6):
        cv.vline(mx, top - 8, 5, FRAME)
    cv.rect(x - 1, top - 1, w + 2, h + 1, FRAME)
    if open_:
        for yy in range(top, bottom):
            t = (yy - top) / h
            cv.hline(x, yy, w, glow[3] if t < 0.25 else glow[2] if t < 0.75 else glow[1])
        # the hall inside: a stair rail, a coat on a hook, the floor
        cv.rect(x, bottom - 10, w, 10, glow[1]); cv.hline(x, bottom - 10, w, glow[2])
        for yy in range(bottom - 8, bottom, 3):
            cv.hline(x, yy, w, shade(glow[1], -0.15))
        cv.line(x + w - 4, top + 20, x + w - 18, bottom - 14, glow[0])
        for k in range(4):
            cv.vline(x + w - 6 - k * 4, top + 22 + k * 7, bottom - 14 - (top + 22 + k * 7), C(glow[0], 0.7))
        cv.rect(x + 4, top + 14, 6, 14, "#3a2a4a"); cv.rect(x + 5, top + 12, 4, 3, "#3a2a4a")
        # the door itself swung in against the left jamb
        cv.rect(x, top, 7, h, colour[2]); cv.vline(x + 6, top, h, colour[0]); cv.vline(x, top, h, colour[3])
        cv.rect(x + 2, top + 6, 3, 22, colour[1]); cv.rect(x + 2, top + 36, 3, 26, colour[1])
    else:
        cv.rect(x, top, w, h, colour[2]); cv.vline(x, top, h, colour[3]); cv.vline(x + w - 1, top, h, colour[0])
        for (py, ph) in [(6, 24), (36, 30)]:
            for px_ in (x + 4, x + w // 2 + 2):
                pw = w // 2 - 6
                cv.rect(px_, top + py, pw, ph, colour[1]); cv.rect(px_ + 1, top + py + 1, pw - 2, ph - 2, colour[2])
                cv.hline(px_ + 1, top + py + 1, pw - 2, colour[3])
        cv.rect(x + w - 7, top + 38, 3, 4, "#d8b45a"); cv.px(x + w - 7, top + 38, "#f6d67a")
        cv.rect(x + w // 2 - 2, top + 26, 5, 3, "#d8b45a")
    # threshold
    cv.rect(x - 4, bottom - 1, w + 8, 2, trim[3])


def porch_light(cv, x, y, on=True):
    """Wall lantern by a door: bracket, a glass box, a halo."""
    if on:
        for r, a in [(16, 0.07), (10, 0.1), (6, 0.14)]:
            cv.ellipse(x - r, y + 4 - r, r * 2, r * 2, C(AMBER[3], a))
    cv.rect(x - 1, y - 3, 3, 3, OUT)
    cv.rect(x - 3, y, 7, 10, OUT)
    cv.rect(x - 2, y + 1, 5, 8, AMBER[3] if on else "#2a2838")
    if on:
        cv.rect(x - 1, y + 2, 3, 4, AMBER[4])
    cv.poly([(x - 4, y + 1), (x, y - 2), (x + 4, y + 1)], OUT)
    return (x, y + 4)


def house_number(cv, x, y, n):
    s = str(n)
    w = text_width(s) + 4
    cv.rect(x, y, w, 10, OUT); cv.rect(x + 1, y + 1, w - 2, 8, "#1e1a24")
    text(cv, s, x + 2, y, "#d8b45a")


def mailbox_wall(cv, x, y):
    cv.rect(x, y, 10, 12, OUT); cv.rect(x + 1, y + 1, 8, 10, "#2a2838"); cv.hline(x + 1, y + 1, 8, "#4d4b66")
    cv.rect(x + 2, y + 4, 6, 1, "#16141f"); cv.rect(x + 3, y + 8, 4, 2, "#d8b45a")


# --- roofs ------------------------------------------------------------------------------------
def shingles(cv, poly, pal=SLATE, row=4, seed=0, top=None, bottom=None):
    """Fill a polygon with staggered asphalt shingle courses."""
    from persp import hash2
    tmp = Canvas(cv.w, cv.h)
    tmp.poly(poly, "#ffffff")
    m = tmp.a[..., 3] > 0
    ys, xs = np.where(m)
    if not len(ys):
        return m
    y0 = ys.min()
    r = (ys - y0) // row
    dy = (ys - y0) % row
    off = (r % 2) * 5
    col = (xs + off) // 10
    dx = (xs + off) % 10
    h = hash2(col, r, seed)
    tones = np.array([C(p)[:4] for p in pal], np.float32)
    idx = np.where(h < 0.25, 2, np.where(h < 0.8, 3, 4))
    out = tones[idx]
    out[dy == row - 1] = tones[1]
    out[(dx == 9) & (dy < row - 1)] = tones[1]
    hi = (dy == 0) & (hash2(xs, r, seed + 1) < 0.08)
    out[hi] = tones[5]
    cv.a[ys, xs] = out
    return m


def eave(cv, x0, x1, y, trim=CLAP_CREAM, depth=4):
    """Fascia board and the shadowed soffit under an eave."""
    cv.rect(x0, y, x1 - x0, depth, trim[4]); cv.hline(x0, y, x1 - x0, trim[6]); cv.hline(x0, y + depth - 1, x1 - x0, trim[2])
    cv.rect(x0 + 2, y + depth, x1 - x0 - 4, 3, C(SHADOW, 0.55))


def gutter_downspout(cv, x, y0, y1):
    cv.rect(x, y0, 3, y1 - y0, OUT); cv.vline(x + 1, y0, y1 - y0, "#6a6878")
    for yy in range(y0 + 10, y1, 22):
        cv.rect(x - 1, yy, 5, 2, OUT)


# --- the porch --------------------------------------------------------------------------------
def porch(cv, x0, x1, fb, pd, rise, height, steps_cx, columns, deck=PORCH_GREY, trim=CLAP_CREAM,
          roof_pal=SLATE, rail=True, skirt="lattice", seed=0, step_w=40, column_style="square"):
    """A front porch across x0..x1 against the facade base fb: a shingled shed roof whose front eave
    hangs at fb + pd - height, painted decking, columns on the front edge, a railing with balusters
    (open at the steps), a lattice skirt, and steps down to the lawn. Returns key y values."""
    pf = fb + pd                # porch front edge (deck surface)
    ground = pf + rise          # lawn at the porch front
    eave_y = pf - height        # front eave line
    roof_back = fb - height - 14
    # roof: slopes from the wall down to the front eave
    shingles(cv, [(x0 - 6, eave_y), (x1 + 6, eave_y), (x1 + 2, roof_back), (x0 - 2, roof_back)], roof_pal, seed=seed)
    cv.hline(x0 - 2, roof_back, x1 - x0 + 4, C(SHADOW, 0.6))
    eave(cv, x0 - 6, x1 + 6, eave_y, trim, depth=6)
    # decking
    for yy in range(fb, pf):
        k = (yy - fb) // 3
        cv.hline(x0, yy, x1 - x0, deck[3] if k % 2 else deck[2])
        if (yy - fb) % 3 == 2:
            cv.hline(x0, yy, x1 - x0, deck[1])
    cv.rect(x0, fb, x1 - x0, 3, C(SHADOW, 0.4))
    cv.rect(x0 - 2, pf, x1 - x0 + 4, 3, deck[4]); cv.hline(x0 - 2, pf, x1 - x0 + 4, deck[5])
    # skirt below the deck edge
    sy0, sy1 = pf + 3, ground
    cv.rect(x0, sy0, x1 - x0, sy1 - sy0, "#141220")
    if skirt == "lattice":
        for d in range(-(sy1 - sy0), x1 - x0, 6):
            cv.line(x0 + d, sy1 - 1, x0 + d + (sy1 - sy0), sy0, trim[3])
            cv.line(x0 + d + (sy1 - sy0), sy1 - 1, x0 + d, sy0, trim[2])
        cv.rect(x0, sy0, x1 - x0, sy1 - sy0, C(SHADOW, 0.25))
    else:
        foundation(cv, x0, sy0, x1 - x0, sy1 - sy0, seed=seed)
    cv.rect(x0 - 2, sy0, x1 - x0 + 4, 2, trim[3]); cv.hline(x0 - 2, sy1 - 1, x1 - x0 + 4, C(SHADOW, 0.6))
    # columns on the front edge
    for cx in columns:
        if column_style == "pier":
            # sandstone pier with a short tapered wood column on top
            ph = 30
            cv.rect(cx - 7, pf - ph, 14, ph, OUT)
            ashlar_wall(cv, cx - 6, pf - ph + 1, 12, ph - 1, SANDSTONE, course=4, seed=cx, cap=False)
            cv.rect(cx - 8, pf - ph - 3, 16, 4, trim[4]); cv.hline(cx - 8, pf - ph - 3, 16, trim[6])
            cv.poly([(cx - 4, pf - ph - 3), (cx + 3, pf - ph - 3), (cx + 2, eave_y + 6), (cx - 3, eave_y + 6)], OUT)
            cv.poly([(cx - 3, pf - ph - 3), (cx + 2, pf - ph - 3), (cx + 1, eave_y + 6), (cx - 2, eave_y + 6)], trim[4])
            cv.vline(cx - 2, eave_y + 6, pf - ph - eave_y - 9, trim[6])
        else:
            cv.rect(cx - 4, eave_y + 6, 9, pf - eave_y - 6, OUT)
            cv.rect(cx - 3, eave_y + 6, 7, pf - eave_y - 6, trim[4])
            cv.vline(cx - 3, eave_y + 6, pf - eave_y - 6, trim[6]); cv.vline(cx + 3, eave_y + 6, pf - eave_y - 6, trim[2])
            cv.rect(cx - 5, eave_y + 6, 11, 4, trim[5]); cv.rect(cx - 5, pf - 5, 11, 5, trim[3]); cv.hline(cx - 5, pf - 5, 11, trim[5])
    # railing between columns, open at the steps
    gap0, gap1 = steps_cx - step_w // 2, steps_cx + step_w // 2
    if rail:
        ry = pf - 20
        cols = sorted(columns)
        for a, b in zip([x0 - 2] + cols, cols + [x1 + 2]):
            for (s0, s1) in [(a + 5, min(b - 4, gap0)), (max(a + 5, gap1), b - 4)]:
                if s1 - s0 < 4:
                    continue
                cv.rect(s0, ry, s1 - s0, 4, OUT); cv.rect(s0, ry + 1, s1 - s0, 2, trim[5]); cv.hline(s0, ry + 1, s1 - s0, trim[6])
                cv.rect(s0, pf - 3, s1 - s0, 2, trim[3])
                for bx in range(s0 + 2, s1 - 1, 4):
                    cv.rect(bx, ry + 4, 2, pf - ry - 7, trim[4]); cv.px(bx + 1, ry + 4, trim[2])
    # steps down to the lawn
    n = 3
    run = (ground + 10 - pf) // n
    for i in range(n):
        y = pf + i * run
        sw = step_w + 6 + i * 6
        cv.rect(steps_cx - sw // 2 - 1, y, sw + 2, run + 1, OUT)
        cv.rect(steps_cx - sw // 2, y + 1, sw, 2, deck[5]); cv.hline(steps_cx - sw // 2, y + 1, sw, shade(deck[5], 0.15))
        cv.rect(steps_cx - sw // 2, y + 3, sw, run - 2, deck[2])
        cv.hline(steps_cx - sw // 2, y + run - 1, sw, deck[1])
    # stringer shadows at the step ends
    return {"pf": pf, "ground": ground, "eave": eave_y, "roof_back": roof_back, "steps_bottom": pf + n * run}


# --- porch things ------------------------------------------------------------------------------
def porch_couch(cv, x, base, w=58, colour=("#3a2a4a", "#4e3a5e", "#644a72", "#7a5e88")):
    """An old sofa against the wall under the porch roof (seen from the front)."""
    cv.rect(x, base - 22, w, 22, OUT)
    cv.rect(x + 1, base - 21, w - 2, 9, colour[1]); cv.hline(x + 1, base - 21, w - 2, colour[3])
    cv.rect(x + 1, base - 12, w - 2, 8, colour[2]); cv.hline(x + 1, base - 12, w - 2, colour[3])
    for sx in range(x + w // 3, x + w - 4, w // 3):
        cv.vline(sx, base - 12, 7, colour[0])
    for ax in (x, x + w - 6):
        cv.rect(ax, base - 16, 6, 13, OUT); cv.rect(ax + 1, base - 15, 4, 11, colour[2]); cv.hline(ax + 1, base - 15, 4, colour[3])
    cv.rect(x + 3, base - 3, 3, 3, OUT); cv.rect(x + w - 6, base - 3, 3, 3, OUT)


def rocking_chair(cv, x, base, colour=WOOD):
    cv.rect(x, base - 26, 12, 3, OUT); cv.rect(x + 1, base - 25, 10, 1, colour[4])
    for sx in range(x + 1, x + 11, 3):
        cv.vline(sx, base - 23, 10, colour[3])
    cv.rect(x - 1, base - 13, 14, 3, OUT); cv.hline(x, base - 12, 12, colour[4])
    cv.vline(x + 1, base - 10, 8, colour[2]); cv.vline(x + 10, base - 10, 8, colour[2])
    for k in range(16):
        cv.px(x - 2 + k, base - 1 - (1 if k in (0, 15) else 0), OUT)


def grill(cv, x, base):
    cv.ellipse(x, base - 18, 14, 10, OUT); cv.ellipse(x + 1, base - 17, 12, 8, "#2a2838"); cv.hline(x + 2, base - 16, 9, "#4d4b66")
    cv.hline(x + 1, base - 13, 12, OUT)
    for lx, l2 in [(x + 2, x), (x + 11, x + 13), (x + 7, x + 7)]:
        cv.line(lx, base - 9, l2, base - 1, OUT)
    cv.rect(x + 5, base - 20, 4, 2, OUT)


def cups_row(cv, x, y, n=5, seed=0, spacing=4):
    """Red cups standing on a rail or step: 3px wide, 4px tall, white rim."""
    rng = _rng(seed)
    xx = x
    for _ in range(n):
        cv.rect(xx, y - 4, 3, 4, CUP[2]); cv.vline(xx, y - 4, 4, CUP[3]); cv.px(xx + 2, y - 1, CUP[1])
        cv.hline(xx, y - 4, 3, CUP[4])
        xx += spacing + int(rng.integers(0, 3))


def cup_flat(cv, x, y, tipped=False, seed=0):
    """A cup on the lawn or floor: upright (3x4) or knocked over (5x3, mouth showing)."""
    if tipped:
        cv.rect(x, y, 5, 3, CUP[2]); cv.hline(x, y, 5, CUP[3]); cv.vline(x + 4, y, 3, CUP[4]); cv.px(x, y + 2, CUP[1])
        cv.px(x + 5, y + 1, "#1a1418")
    else:
        cv.rect(x, y, 3, 4, CUP[2]); cv.vline(x, y, 4, CUP[3]); cv.hline(x, y, 3, CUP[4]); cv.px(x + 2, y + 3, CUP[1])
    cv.hline(x, y + (3 if tipped else 4), 4 if not tipped else 6, C(SHADOW, 0.35))


def bedsheet_banner(cv, x, y, w, h, lines, seed=0, ink="#c42e3e", ink2="#2a3a8a", sag=3):
    """A bedsheet hung by its corners, spray-painted. lines: [(kind, payload, colour)] where kind is
    'text' (game font) or 'greek' (a tuple of letter names, 1x glyphs)."""
    rng = _rng(seed)
    pts = [(x, y), (x + w, y), (x + w - 2, y + h + sag), (x + w // 2, y + h - 1), (x + 2, y + h + sag)]
    cv.poly([(px + 1, py + 2) for px, py in pts], C(SHADOW, 0.45))
    cv.poly(pts, "#e6e0d2")
    for k in range(5):                       # folds and creases
        fx = x + 6 + int(rng.integers(0, max(1, w - 12)))
        cv.line(fx, y + 2, fx + int(rng.integers(-3, 4)), y + h - 2, "#c8c0b0")
    cv.hline(x, y, w, "#f6f2ea")
    yy = y + 3
    for kind, payload, colour in lines:
        if kind == "text":
            tw = text_width(payload)
            text(cv, payload, x + w // 2 - tw // 2, yy, colour)
            yy += 9
        else:
            gw = len(payload) * 10 - 2
            greek_small(cv, payload, x + w // 2 - gw // 2, yy + 1, colour)
            yy += 12
    # spray drips
    for _ in range(6):
        dx = x + 6 + int(rng.integers(0, max(1, w - 12)))
        cv.vline(dx, yy - 2, int(rng.integers(2, 5)), C(ink, 0.6))
    for (tx, ty) in [(x, y), (x + w - 1, y)]:
        cv.rect(tx - 1, ty - 2, 3, 3, OUT)


def lawn_chair(cv, x, base, colour="#2a8a7a", hi="#4ab0a0", dark="#1a5a50"):
    """A folding camp chair seen from the front: fabric back and seat, armrests with a cup holder,
    crossed legs (about 16x20)."""
    cv.rect(x + 1, base - 20, 14, 11, OUT)                         # back
    cv.rect(x + 2, base - 19, 12, 9, colour); cv.hline(x + 2, base - 19, 12, hi); cv.vline(x + 2, base - 19, 9, hi)
    cv.vline(x + 8, base - 18, 8, dark)
    cv.rect(x - 1, base - 11, 18, 4, OUT)                         # armrests and the seat sag
    cv.hline(x, base - 10, 16, "#8a8898"); cv.rect(x + 2, base - 9, 12, 2, dark)
    cv.rect(x - 2, base - 13, 4, 3, OUT); cv.rect(x - 1, base - 12, 2, 1, CUP[2])   # cup in the holder
    cv.line(x + 1, base - 7, x + 13, base, OUT); cv.line(x + 14, base - 7, x + 2, base, OUT)
    cv.line(x + 2, base - 7, x + 13, base - 1, "#8a8898"); cv.line(x + 13, base - 7, x + 3, base - 1, "#6a6878")
    cv.hline(x, base, 17, C(SHADOW, 0.4))


def flamingo(cv, x, base):
    """A plastic lawn flamingo (about 14x26): wire legs, fat pink body, S-neck, black-tipped beak."""
    pink = ["#7a2a4a", "#c84a7a", "#f07aa8", "#ffb0d0"]
    cv.vline(x + 5, base - 9, 9, "#3a3848"); cv.vline(x + 8, base - 9, 9, "#3a3848")
    cv.ellipse(x - 1, base - 18, 15, 10, OUT)
    cv.ellipse(x, base - 17, 13, 8, pink[2]); cv.ellipse(x + 1, base - 17, 8, 4, pink[3]); cv.hline(x + 2, base - 11, 9, pink[1])
    cv.poly([(x - 1, base - 15), (x - 4, base - 17), (x, base - 13)], pink[1])            # tail
    # neck: up from the chest, curving back, then forward to the head
    for (nx, ny) in [(11, 17), (12, 18), (12, 19), (11, 20), (10, 21), (10, 22), (10, 23), (11, 24)]:
        cv.rect(x + nx - 1, base - ny, 3, 1, OUT)
    for (nx, ny) in [(11, 17), (12, 18), (12, 19), (11, 20), (10, 21), (10, 22), (10, 23), (11, 24)]:
        cv.px(x + nx, base - ny, pink[2])
    cv.rect(x + 10, base - 27, 5, 4, OUT); cv.rect(x + 11, base - 26, 3, 2, pink[2])
    cv.rect(x + 14, base - 26, 3, 2, OUT); cv.px(x + 14, base - 25, "#e8e4dc")              # beak, black tip
    cv.px(x + 12, base - 26, "#1a1418")


def pumpkin(cv, x, base, w=10, h=8, carved=False):
    org = ["#5a2a10", "#a8501a", "#d8742a", "#f0a050"]
    cv.ellipse(x - 1, base - h - 1, w + 2, h + 2, OUT)
    cv.ellipse(x, base - h, w, h, org[2])
    for k in range(1, w, 3):
        cv.vline(x + k, base - h + 1, h - 2, org[1])
    cv.hline(x + 2, base - h + 1, w - 4, org[3])
    cv.rect(x + w // 2 - 1, base - h - 3, 2, 3, "#3a5a2a")
    if carved:
        cv.px(x + 2, base - h + 3, "#f6cf7a"); cv.px(x + w - 3, base - h + 3, "#f6cf7a")
        cv.hline(x + 2, base - 2, w - 4, "#f6cf7a")


# --- lawn, walks, street ------------------------------------------------------------------------
def concrete_walk(cv, x, y, w, h, seed=0):
    """The front walk from the steps to the sidewalk: square slabs, a crack, a leaf or two."""
    rng = _rng(seed)
    pal = ["#4f4a54", "#625d68", "#6c6772", "#77727c", "#827d86"]
    cv.rect(x, y, w, h, pal[0])
    yy = y
    while yy < y + h:
        rh = min(14, y + h - yy)
        tone = pal[int(rng.choice([2, 3, 3, 4]))]
        cv.rect(x + 1, yy + 1, w - 2, rh - 1, tone)
        cv.hline(x + 1, yy + 1, w - 2, shade(tone, 0.06))
        for _ in range(w * rh // 12):
            cv.px(x + 1 + int(rng.integers(0, w - 2)), yy + 1 + int(rng.integers(0, max(1, rh - 1))), shade(tone, float(rng.choice([-0.06, 0.05]))))
        yy += rh


def parked_car(width=136, height=52, body=("#1a2a40", "#24385a", "#2e4a72", "#3e5e8a", "#5a7aa8"), seed=0, couch_strap=False):
    """An old hatchback parked nose-left at the kerb: body panels, glass, wheels, lights, a dent."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base - 1, width // 2 + 2, 3, alpha=0.5)
    b = body
    wr = 11
    sill = base - 8
    belt = base - 26
    roof = base - height + 2
    # lower body
    body_pts = [(ox + 2, sill), (ox, belt + 4), (ox + 6, belt - 2), (ox + width - 6, belt - 4), (ox + width, belt + 2),
                (ox + width - 1, sill)]
    cv.poly([(px, py) for px, py in body_pts], OUT)
    cv.poly([(px + (1 if px < ox + width // 2 else -1), py + 1) for px, py in body_pts], b[2])
    cv.rect(ox + 3, belt + 1, width - 6, 3, b[3]); cv.hline(ox + 4, belt + 1, width - 8, b[4])
    cv.rect(ox + 3, sill - 6, width - 6, 6, b[1])
    # greenhouse
    gh = [(ox + 22, belt - 2), (ox + 40, roof + 2), (ox + width - 34, roof), (ox + width - 10, belt - 4)]
    cv.poly(gh, OUT)
    cv.poly([(ox + 24, belt - 3), (ox + 41, roof + 3), (ox + width - 35, roof + 1), (ox + width - 12, belt - 4)], b[3])
    cv.hline(ox + 41, roof + 1, width - 76, b[4])
    for (wx0, wx1) in [(ox + 30, ox + 68), (ox + 72, ox + width - 20)]:
        top_ = roof + 5
        cv.poly([(wx0, belt - 3), (wx0 + 10 if wx0 < ox + 40 else wx0, top_), (wx1 - (10 if wx1 > ox + width - 30 else 0), top_), (wx1, belt - 3)], "#1a2236")
        cv.line(wx0 + 6, belt - 4, wx0 + 14, top_ + 1, "#4a5a7a")
    cv.vline(ox + 70, roof + 4, belt - roof - 6, OUT)
    # doors, handle, mirror, lights
    for dx in (ox + 46, ox + 92):
        cv.vline(dx, belt, sill - belt, b[0])
    cv.rect(ox + 60, belt + 6, 6, 2, b[4]); cv.rect(ox + 104, belt + 6, 6, 2, b[4])
    cv.rect(ox + 24, belt - 6, 5, 4, OUT)
    cv.rect(ox + 1, belt + 4, 5, 4, "#f2e8c0"); cv.rect(ox + width - 5, belt + 2, 4, 6, "#c42e2e")
    cv.ellipse(ox + 60, belt + 12, 10, 5, b[1])                                                      # a dent
    cv.rect(ox + width - 30, belt + 2, 12, 5, "#e6d6b1"); text_px = [(ox + width - 28, belt + 4)]    # a parking sticker
    cv.hline(ox + width - 28, belt + 4, 8, "#7e3a30")
    # wheels
    for wx in (ox + 26, ox + width - 26):
        cv.ellipse(wx - wr, base - 2 * wr, wr * 2, wr * 2, OUT)
        cv.ellipse(wx - wr + 2, base - 2 * wr + 2, wr * 2 - 4, wr * 2 - 4, "#1e1c26")
        cv.ellipse(wx - 5, base - wr - 5, 10, 10, "#6a6878"); cv.ellipse(wx - 3, base - wr - 3, 6, 6, "#8a8898")
        cv.px(wx, base - wr, OUT)
        cv.poly([(wx - wr - 3, sill - 2), (wx - wr + 1, belt + 6), (wx + wr - 1, belt + 6), (wx + wr + 3, sill - 2)], C(OUT, 0.6))
    if couch_strap:
        pass
    return cv, ox + width // 2, base


def lawn_couch(width=100, height=40, seed=0):
    """A plaid three-seater dragged onto the lawn, facing the street, one cushion missing."""
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base - 1, width // 2 + 2, 3, alpha=0.5)
    pl = ["#3a1a1e", "#5a2a2a", "#7a3a32", "#94503c", "#b06a48"]
    plaid = ["#2a3a5a", "#d8b45a"]
    back_top = base - height + 2
    seat = base - 16
    # back
    cv.rect(ox + 6, back_top, width - 12, seat - back_top + 2, OUT)
    cv.rect(ox + 7, back_top + 1, width - 14, seat - back_top, pl[2])
    cv.hline(ox + 7, back_top + 1, width - 14, pl[4])
    for k, sx in enumerate(range(ox + 7, ox + width - 7, 8)):
        cv.vline(sx, back_top + 1, seat - back_top, C(plaid[k % 2], 0.35))
    for yy in range(back_top + 5, seat, 6):
        cv.hline(ox + 7, yy, width - 14, C(plaid[0], 0.4))
    # cushions (the middle one is gone)
    cw = (width - 16) // 3
    for i in range(3):
        cx0 = ox + 8 + i * cw
        if i == 1:
            cv.rect(cx0, seat + 2, cw - 1, 6, pl[0])
            cv.rect(cx0 + 4, seat + 4, 4, 2, "#e6d6b1"); cv.px(cx0 + 12, seat + 5, "#d8b45a")   # a lost coin, a receipt
            continue
        cv.rect(cx0, seat - 2, cw - 1, 10, OUT)
        cv.rect(cx0 + 1, seat - 1, cw - 3, 8, pl[3]); cv.hline(cx0 + 1, seat - 1, cw - 3, pl[4])
        cv.vline(cx0 + cw // 2, seat, 6, C(plaid[1], 0.4)); cv.hline(cx0 + 1, seat + 3, cw - 3, C(plaid[0], 0.4))
    # front rail and skirt
    cv.rect(ox + 6, seat + 7, width - 12, base - seat - 10, OUT)
    cv.rect(ox + 7, seat + 8, width - 14, base - seat - 12, pl[1])
    for sx in range(ox + 9, ox + width - 8, 3):
        cv.vline(sx, seat + 9, base - seat - 13, pl[0])
    # rolled arms
    for ax in (ox, ox + width - 12):
        cv.rect(ax, seat - 10, 12, base - seat + 6, OUT)
        cv.rect(ax + 1, seat - 9, 10, base - seat + 4, pl[2]); cv.hline(ax + 1, seat - 9, 10, pl[4])
        cv.ellipse(ax + 1, seat - 11, 10, 6, pl[3]); cv.hline(ax + 3, seat - 10, 6, pl[4])
    # feet and grass tufts growing round them
    for fx in (ox + 3, ox + width - 7):
        cv.rect(fx, base - 4, 4, 3, OUT)
    for gx in (ox + 1, ox + 30, ox + width - 10):
        for k in range(4):
            cv.line(gx + k * 2, base - 1, gx + k * 2 + (k % 2), base - 5, LEAF[3 if k % 2 else 4])
    return cv, ox + width // 2, base


def yard_sign(width=40, height=36, lines=("NO", "PARKING", "ON LAWN"), seed=0):
    """A hand-lettered plywood sign on a stake."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 2
    ground_shadow(cv, ox + width // 2, base - 1, 8, 2)
    cv.rect(ox + width // 2 - 2, base - 14, 4, 14, OUT); cv.vline(ox + width // 2 - 1, base - 13, 12, WOOD[3])
    top = base - height
    bh = 9 * len(lines) + 4
    cv.rect(ox, top, width, bh, OUT)
    cv.wood(ox + 1, top + 1, width - 2, bh - 2, "#c8a878", plank=5, seed=seed)
    for i, s in enumerate(lines):
        col = "#c42e2e" if i == 0 else "#2a2030"
        text(cv, s, ox + width // 2 - text_width(s) // 2, top + 1 + i * 9, col)
    return cv, ox + width // 2, base


def cornhole_boards(width=74, height=18, seed=0):
    """Two cornhole boards on the lawn, propped toward each other, bean bags scattered."""
    cv = Canvas(width + 4, height + 6, seed=seed)
    ox, base = 2, height + 3
    for bx, flip in [(ox, False), (ox + width - 26, True)]:
        top = base - height
        pts = [(bx, base - 2), (bx + 26, base - 2), (bx + 22, top), (bx + 4, top)]
        cv.poly([(p[0], p[1] + 1) for p in pts], C(SHADOW, 0.4))
        cv.poly(pts, OUT)
        cv.poly([(bx + 1, base - 3), (bx + 25, base - 3), (bx + 21, top + 1), (bx + 5, top + 1)], "#b08a5a")
        cv.poly([(bx + 3, base - 6), (bx + 23, base - 6), (bx + 20, top + 4), (bx + 6, top + 4)], "#1e3a6a")
        cv.ellipse(bx + 10, top + 4, 6, 4, OUT)
        cv.hline(bx + 4, base - 4, 18, "#d8b45a")
    for (x, y, c) in [(ox + 30, base - 4, "#c42e2e"), (ox + 37, base - 6, "#2a6ac8"), (ox + 44, base - 3, "#c42e2e")]:
        cv.rect(x, y, 4, 3, OUT); cv.rect(x + 1, y + 1, 2, 1, c)
    return cv, ox + width // 2, base


def recycling_bin(width=24, height=34, colour=("#122a50", "#1e3e78", "#2a54a0", "#4a74c0"), seed=0):
    """A wheeled kerbside bin, lid propped open by the cups inside."""
    cv = Canvas(width + 6, height + 8, seed=seed)
    ox, base = 3, height + 4
    ground_shadow(cv, ox + width // 2, base - 1, width // 2, 2)
    top = base - height + 6
    cv.poly([(ox, top), (ox + width, top), (ox + width - 2, base - 3), (ox + 2, base - 3)], OUT)
    cv.poly([(ox + 1, top + 1), (ox + width - 1, top + 1), (ox + width - 3, base - 4), (ox + 3, base - 4)], colour[2])
    cv.vline(ox + 2, top + 2, base - top - 7, colour[3])
    cv.rect(ox + width // 2 - 5, top + 8, 10, 8, colour[1])
    for k, (cx, cy) in enumerate([(ox + 9, top + 10), (ox + 12, top + 13), (ox + 8, top + 13)]):
        cv.px(cx, cy, "#e6e6ea")
    # cups heaped above the rim, lid tipped back
    for k in range(7):
        cx = ox + 3 + k * 3
        cy = top - 3 - (k % 3)
        cv.rect(cx, cy, 3, 4, CUP[2]); cv.hline(cx, cy, 3, CUP[4]); cv.px(cx + 2, cy + 3, CUP[1])
    cv.poly([(ox - 1, top - 2), (ox + width + 1, top - 2), (ox + width - 1, top - 9), (ox + 1, top - 9)], OUT)
    cv.poly([(ox, top - 3), (ox + width, top - 3), (ox + width - 2, top - 8), (ox + 2, top - 8)], colour[1])
    cv.hline(ox + 2, top - 8, width - 4, colour[3])
    cv.ellipse(ox - 1, base - 6, 6, 6, OUT); cv.ellipse(ox + width - 5, base - 6, 6, 6, OUT)
    return cv, ox + width // 2, base


def hydrant(width=14, height=20):
    cv = Canvas(width + 4, height + 4)
    ox, base = 2, height + 2
    ground_shadow(cv, ox + width // 2, base - 1, 6, 2)
    y = ["#5a3a10", "#a87a1e", "#d8a830", "#f0cc5a"]
    cx = ox + width // 2
    cv.rect(cx - 5, base - 3, 11, 3, OUT); cv.rect(cx - 4, base - 2, 9, 1, y[1])
    cv.rect(cx - 4, base - 15, 9, 13, OUT); cv.rect(cx - 3, base - 14, 7, 12, y[2]); cv.vline(cx - 3, base - 14, 12, y[3])
    cv.rect(cx - 7, base - 11, 15, 4, OUT); cv.rect(cx - 6, base - 10, 13, 2, y[2])
    cv.ellipse(cx - 4, base - 19, 9, 7, OUT); cv.ellipse(cx - 3, base - 18, 7, 5, y[2]); cv.px(cx - 1, base - 17, y[3])
    cv.rect(cx - 1, base - 21, 3, 3, OUT)
    return cv, cx, base


def street_sign_post(width=48, height=88, names=("COLLEGE AVE",), arrow="CAMPUS >"):
    """A street sign: green name blades on a pole, a white arrow plate below."""
    tw = max(text_width(n) for n in names) + 8
    cv = Canvas(max(width, tw) + 4, height + 4)
    cx, base = (max(width, tw) + 4) // 2, height + 2
    ground_shadow(cv, cx, base - 1, 6, 2)
    top = base - height
    cv.rect(cx - 1, top + 4, 3, height - 4, OUT); cv.vline(cx, top + 4, height - 5, "#8a8898")
    for i, n in enumerate(names):
        w = text_width(n) + 8
        y = top + i * 13
        cv.rect(cx - w // 2, y, w, 12, OUT)
        cv.rect(cx - w // 2 + 1, y + 1, w - 2, 10, "#2e7a4e"); cv.hline(cx - w // 2 + 1, y + 1, w - 2, "#4a9a6a")
        cv.rect(cx - w // 2 + 2, y + 2, w - 4, 8, C("#eef4ea", 0.0))
        text(cv, n, cx - text_width(n) // 2, y + 1, "#eef4ea")
    if arrow:
        w = text_width(arrow) + 8
        y = top + len(names) * 13 + 8
        cv.rect(cx - w // 2, y, w, 12, OUT); cv.rect(cx - w // 2 + 1, y + 1, w - 2, 10, "#e6e6ea")
        text(cv, arrow, cx - text_width(arrow) // 2, y + 1, "#1e2236")
    return cv, cx, base


def scooter_flat(cv, x, y, colour="#3ac87a"):
    """A rental e-scooter lying on its side on the sidewalk (flat floor detail)."""
    cv.line(x, y + 4, x + 22, y + 1, OUT); cv.line(x, y + 5, x + 22, y + 2, "#3a3848")
    cv.rect(x + 2, y + 3, 16, 3, OUT); cv.rect(x + 3, y + 3, 14, 2, colour)
    cv.line(x + 20, y + 1, x + 28, y - 5, OUT); cv.line(x + 21, y + 1, x + 29, y - 5, "#5a5868")
    cv.rect(x + 27, y - 7, 2, 5, OUT)
    for wx in (x - 2, x + 18):
        cv.ellipse(wx, y + 2, 6, 6, OUT); cv.px(wx + 2, y + 4, "#5a5868")
    cv.hline(x - 2, y + 8, 30, C(SHADOW, 0.35))


def gutter_leaves(cv, x0, x1, y, seed=0, density=0.5):
    from surfaces import LEAVES
    rng = _rng(seed)
    for _ in range(int((x1 - x0) * density)):
        lx = x0 + int(rng.integers(0, x1 - x0))
        ly = y + int(abs(rng.normal(0, 2)))
        c = LEAVES[int(rng.integers(len(LEAVES)))]
        cv.px(lx, ly, c); cv.px(lx + 1, ly, shade(c, -0.2))


def storm_drain(cv, x, y, w=22):
    cv.rect(x, y, w, 5, OUT); cv.rect(x + 1, y + 1, w - 2, 3, "#14121a")
    for bx in range(x + 2, x + w - 1, 3):
        cv.vline(bx, y + 1, 3, "#4a4852")


def manhole(cv, cx, cy, rx=11, ry=5):
    cv.ellipse(cx - rx - 1, cy - ry - 1, rx * 2 + 2, ry * 2 + 2, "#1a1820")
    cv.ellipse(cx - rx, cy - ry, rx * 2, ry * 2, "#3a3842")
    for k in range(-rx + 3, rx - 2, 3):
        cv.hline(cx + k, cy - ry + 2, 2, "#2a2832"); cv.hline(cx + k + 1, cy + ry - 3, 2, "#2a2832")
    cv.hline(cx - rx + 2, cy - ry, rx * 2 - 4, "#4a4852")


def tar_seams(cv, x0, x1, y0, y1, seed=0, n=6):
    """Black crack-seal squiggles on the old asphalt."""
    rng = _rng(seed)
    for _ in range(n):
        x = int(rng.integers(x0, x1)); y = int(rng.integers(y0, y1))
        length = int(rng.integers(20, 70))
        horiz = rng.random() < 0.6
        for k in range(length):
            cv.px(x, y, "#141218"); cv.px(x + (0 if horiz else 1), y + (1 if horiz else 0), "#1a1820")
            if horiz:
                x += 1; y += int(rng.integers(-1, 2)) if rng.random() < 0.3 else 0
            else:
                y += 1; x += int(rng.integers(-1, 2)) if rng.random() < 0.3 else 0
            if not (x0 <= x < x1 and y0 <= y < y1):
                break
