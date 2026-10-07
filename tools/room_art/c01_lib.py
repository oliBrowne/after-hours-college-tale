"""Helpers for C01, the Dalton Trumbo Fountain Court in front of the UMC (the game's hub).

Everything paints at 1:1 game pixels in the approved style: clean colour clusters, ink outlines on
props, warm amber light against cool plum shadow, character scale (people ~52px, doors ~72px).

Skyline:    court_sky (dusk over the Flatirons in the west, moonrise in the east), distant_landmark
Buildings:  umc_front (the UMC's sandstone front with the Book Store and Career Center fronts),
            farrand_front (Farrand Hall, 1950s red brick with sandstone trim), stone_pier, fingerpost
Ground:     running_bond (brick-red paver paths), court_tiles, kerb_lines, chalk_art, drain_grate,
            tree_grate, parking_lane
Fountain:   fountain_basin (background water and coping), fountain_front (prop: front rim, plaque,
            jets), fountain_layers (animated sparkle and spray)
Props:      coffee_cart, map_board, event_column, bike_rack, bins
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, LEAF, MUM, ground_shadow, shrub
from facade import (SANDSTONE, TRIM, ROOF, FRAME, GLOW, DARKGLASS, BRICK, roof_tiles, cornice, window, pilaster,
                    open_doorway, wall_lantern, steps)
from surfaces import ashlar_wall, light_pool

INK = "#171a2b"
SHADOW = "#0d0b16"
PAVE = ["#4a3f45", "#5a4e52", "#665a5c", "#6c5f60", "#726465", "#7b6c6b"]
PAVER = ["#3e2628", "#4e2e2c", "#5e3a34", "#6c4238", "#7a4c40", "#8a5848"]      # brick-red path pavers
COURT = ["#4e3e40", "#64524f", "#76625a", "#806a60", "#8a7466", "#98806e"]       # lighter court flags
WALL = ["#3a2c31", "#5b4644", "#8a6e60", "#9a7c6b", "#b49481", "#cdb099"]        # low sandstone walls (U02)
WATER = ["#0f1a2c", "#16253c", "#1d3150", "#264064", "#33557c", "#4a7298", "#7aa6c8", "#c8e4f4"]
JET = ["#7ab0d4", "#a8d0ea", "#d6ecf8", "#f4fbff"]
GOLD = ["#5a3e14", "#8a6420", "#c8962e", "#e8b84a", "#f6d67a"]                   # CU gold
BLACKS = ["#141218", "#1e1c24", "#2a2832", "#3a3844"]
BRONZE = ["#2a1c14", "#4a3220", "#6e4c2c", "#9a7040", "#c49a5a"]
CHALK_COLS = ["#f2e6d0", "#f2a0b4", "#9ad8e8", "#f6d67a", "#a8e0a0", "#c8a8f0"]
COOL_GLOW = ["#3a5a62", "#5e8a8e", "#8ab8b4", "#bce0d6", "#e6f6ee"]                # Career Center interior


def _rng(seed):
    return np.random.default_rng(seed)


# --------------------------------------------------------------------------------------------
# Sky and distance

def court_sky(width, height, split=1100, moon=(1838, 40, 8), seed=3):
    """West (left): the dusk sky with the Flatirons (from the title painting), the panel's top at
    y 0 so its clouds fill the sky. East (right): the sky away from the sunset, violet with early
    stars and the moon rising. The two meet behind the UMC pavilion at x = split."""
    from lib_farrand import farrand_sky
    from lib_farrand2 import sky_east
    from sky import flatirons_panel
    ph = flatirons_panel(2.0).shape[0]
    west_h = ph + 22
    west, _ = farrand_sky(width, west_h, panels=(0, 1, 0, 1), offset=30, scale=2.0, stars=30, seed=seed)
    # the painting's top corner has a sliver of window frame: paint it out with the row's sky
    for y in range(3):
        row = west[y, :, :3]
        dark = row.mean(-1) < 0.2
        row[dark] = np.median(row[~dark], axis=0)
    east = sky_east(width, height, seed=seed + 2, stars=110, moon=moon)
    out = np.zeros((height, width, 4), np.float32)
    out[:min(height, west_h)] = west[:height]
    if height > west_h:
        out[west_h:] = west[-1]
    rng = _rng(seed)
    for y in range(height):
        x0 = split + int(rng.integers(-4, 5))
        out[y, x0:] = east[y, x0:]
    return out, 0


def distant_landmark(cell, height, brightness=0.72, saturation=0.8, colors=28):
    """A campus building from the painted atlas, small and hazy (it is a few hundred metres off)."""
    from midlib import sprite_from_cell
    return sprite_from_cell(cell, height=height, colors=colors, brightness=brightness, saturation=saturation)


# --------------------------------------------------------------------------------------------
# Walls, piers and signs at the back of the court

def stone_pier(cv, x, base, w=14, h=40, lantern=True):
    """Sandstone gate pier with a limestone cap and (optionally) a lantern on top."""
    cv.rect(x, base - h, w, h, WALL[2])
    for yy in range(base - h + 4, base, 6):
        cv.hline(x, yy, w, WALL[1])
        off = 0 if (yy // 6) % 2 else w // 2
        cv.vline(x + off, yy - 5, 5, WALL[1]) if off else None
    cv.vline(x, base - h, h, WALL[4]); cv.vline(x + w - 1, base - h, h, WALL[1])
    cv.rect(x - 2, base - h - 4, w + 4, 4, TRIM[2]); cv.hline(x - 2, base - h - 4, w + 4, TRIM[4])
    cv.hline(x - 2, base - h - 1, w + 4, TRIM[0])
    cv.hline(x, base - 1, w, C(SHADOW, 0.6))
    if lantern:
        lx = x + w // 2
        cv.rect(lx - 3, base - h - 15, 7, 11, FRAME)
        cv.rect(lx - 2, base - h - 13, 5, 7, GLOW[3]); cv.rect(lx - 1, base - h - 12, 3, 4, GLOW[4])
        cv.poly([(lx - 4, base - h - 14), (lx, base - h - 18), (lx + 4, base - h - 14)], FRAME)
        return (lx, base - h - 10)
    return None


def fingerpost(cv, x, top, base, arms):
    """A black fingerpost with cream arms. arms: [(label, direction -1/1, y)]."""
    cv.rect(x - 1, top, 3, base - top, OUT); cv.vline(x, top + 1, base - top - 1, IRON[3])
    cv.rect(x - 2, top - 2, 5, 3, OUT); cv.px(x, top - 1, GOLD[3])
    for label, d, y in arms:
        w = text_width(label) + 8
        x0 = x + 2 if d > 0 else x - 1 - w
        cv.rect(x0, y, w, 11, OUT)
        cv.rect(x0 + 1, y + 1, w - 2, 9, "#e6dcc4"); cv.hline(x0 + 1, y + 1, w - 2, "#fff6e0")
        tip = x0 + w if d > 0 else x0 - 1
        cv.poly([(tip, y), (tip + 4 * d, y + 5), (tip, y + 10)], OUT)
        cv.poly([(tip, y + 1), (tip + 3 * d, y + 5), (tip, y + 9)], "#e6dcc4")
        text(cv, label, x0 + 4, y + 1, "#2a2440")


def street_sign(cv, x, top, base, label):
    """A green street-name blade on a grey pole."""
    cv.rect(x - 1, top, 3, base - top, OUT); cv.vline(x, top, base - top, "#6a6878")
    w = text_width(label) + 6
    cv.rect(x - w // 2, top - 2, w, 11, OUT)
    cv.rect(x - w // 2 + 1, top - 1, w - 2, 9, "#2e7a4e"); cv.hline(x - w // 2 + 1, top - 1, w - 2, "#4a9a6a")
    text(cv, label, x - w // 2 + 3, top - 2, "#eef4ea")


# --------------------------------------------------------------------------------------------
# The UMC front

def _shop_glass(cv, x, y, w, h, pal, seed=0):
    """Glass with the interior lit: three bands of the glow palette, a ceiling light row."""
    cv.rect(x, y, w, h, pal[2])
    cv.rect(x, y, w, h // 4, pal[3])
    cv.rect(x, y + h - h // 3, w, h // 3, pal[1])
    for lx in range(x + 3, x + w - 2, 9):
        cv.rect(lx, y + 1, 4, 1, pal[4])


def tee(cv, x, y, body, logo=None, w=12, h=13):
    """A T-shirt on a hanger seen flat: shoulders, sleeves, a chest logo."""
    cv.px(x + w // 2, y - 2, "#c8c4b8"); cv.hline(x + w // 2 - 2, y - 1, 5, "#c8c4b8")
    cv.rect(x + 2, y, w - 4, h, body)
    cv.rect(x, y, w, 4, body)
    cv.px(x, y + 3, shade(body, -0.3)); cv.px(x + w - 1, y + 3, shade(body, -0.3))
    cv.rect(x + w // 2 - 1, y, 2, 1, shade(body, -0.4))
    cv.vline(x + w - 3, y + 4, h - 4, shade(body, -0.2))
    if logo:
        cv.rect(x + w // 2 - 2, y + 4, 4, 3, logo); cv.px(x + w // 2 - 3, y + 4, logo); cv.px(x + w // 2 + 2, y + 4, logo)


def book_store_front(cv, cx, base, seed=0):
    """CU Book Store frontage: black and gold sign band, striped awnings, display windows with
    gear and books, a glass double door with the lit shop behind. Door top at base - 62."""
    rng = _rng(seed)
    x0, x1 = cx - 62, cx + 62
    # stone surround and sign band
    cv.rect(x0 - 4, base - 92, x1 - x0 + 8, 92, TRIM[1]); cv.hline(x0 - 4, base - 92, x1 - x0 + 8, TRIM[3])
    cv.rect(x0, base - 88, x1 - x0, 15, OUT)
    cv.rect(x0 + 1, base - 87, x1 - x0 - 2, 13, BLACKS[1]); cv.hline(x0 + 1, base - 87, x1 - x0 - 2, BLACKS[3])
    label = "CU BOOK STORE"
    text(cv, label, cx - text_width(label) // 2 + 1, base - 86, GOLD[4])
    cv.px(x0 + 4, base - 81, GOLD[3]); cv.px(x1 - 5, base - 81, GOLD[3])
    # display windows either side of the door
    for wx in (x0 + 2, cx + 20):
        ww, wy, wh = 40, base - 58, 44
        cv.rect(wx - 2, wy - 2, ww + 4, wh + 4, FRAME)
        _shop_glass(cv, wx, wy, ww, wh, GLOW, seed)
        # back shelf of books
        for shelf in (wy + 14, wy + 26):
            cv.hline(wx, shelf, ww, WOOD[2])
            bx = wx + 1
            while bx < wx + ww - 2:
                bw = int(rng.integers(2, 4)); bh = int(rng.integers(5, 9))
                cv.rect(bx, shelf - bh, bw, bh, ["#7e3a30", "#425da6", "#5c897c", "#c47a2c", "#e6d6b1", BLACKS[2]][int(rng.integers(6))])
                bx += bw + (1 if rng.random() < 0.25 else 0)
        # gear on a rail in front: black and gold tees, a hoodie
        cv.hline(wx + 1, wy + 28, ww - 2, "#c8c4b8")
        for k, (body, logo) in enumerate([(BLACKS[2], GOLD[3]), (GOLD[3], BLACKS[0]), ("#e6e2d8", GOLD[2])]):
            tee(cv, wx + 1 + k * 13, wy + 30, body, logo)
        # a little buffalo on a stand, a price card
        bx, by = wx + ww - 9, wy + 42
        cv.rect(bx, by - 4, 7, 4, GOLD[2]); cv.rect(bx - 1, by - 6, 4, 3, GOLD[3]); cv.px(bx - 2, by - 5, GOLD[4])
        cv.rect(wx + 2, wy + wh - 6, 8, 5, "#f2ead6"); cv.hline(wx + 3, wy + wh - 4, 5, "#b8382c")
        # reflection streak
        cv.line(wx + ww - 12, wy + 2, wx + ww - 20, wy + 12, C("#fff6e0", 0.45))
        cv.rect(wx - 3, wy + wh + 2, ww + 6, 3, TRIM[2]); cv.hline(wx - 3, wy + wh + 2, ww + 6, TRIM[4])
    # awnings: black and gold stripes over each window
    for ax in (x0, cx + 18):
        _striped_awning(cv, ax, base - 72, 44, BLACKS[2], GOLD[3])
    # the door: glass double door in a bronze frame, shop light behind
    dx, dw, dh = cx - 17, 34, 62
    cv.rect(dx - 3, base - dh - 3, dw + 6, dh + 3, OUT)
    cv.rect(dx - 2, base - dh - 2, dw + 4, dh + 2, BRONZE[2])
    _shop_glass(cv, dx, base - dh, dw, dh, GLOW, seed + 1)
    # shelves seen through the door, the till light
    for sy in range(base - dh + 18, base - 8, 9):
        cv.hline(dx, sy, dw, WOOD[2])
        for bx in range(dx + 1, dx + dw - 1, 3):
            cv.rect(bx, sy - 5, 2, 5, ["#7e3a30", "#425da6", "#e6d6b1", GOLD[2]][(bx + sy) % 4])
    cv.vline(cx, base - dh, dh, BRONZE[1]); cv.vline(cx - 1, base - dh, dh, BRONZE[3])
    for hx in (cx - 4, cx + 3):
        cv.rect(hx, base - 36, 1, 10, GOLD[4])
    cv.rect(dx, base - 4, dw, 4, BRONZE[1])
    # OPEN card and hours
    cv.rect(dx + 2, base - 50, 12, 7, "#f2ead6")
    cv.rect(dx + 3, base - 48, 10, 3, "#2e7a4e")
    cv.rect(x0 - 4, base - 3, x1 - x0 + 8, 3, TRIM[1]); cv.hline(x0 - 4, base - 3, x1 - x0 + 8, TRIM[3])


def _striped_awning(cv, x, y, w, c1, c2, depth=9):
    for i, sx in enumerate(range(x, x + w, 5)):
        c = c1 if i % 2 == 0 else c2
        cv.poly([(sx, y), (min(x + w, sx + 5), y), (min(x + w, sx + 5) + 1, y + depth), (sx - 1, y + depth)], c)
    cv.hline(x - 1, y, w + 2, OUT)
    for i, sx in enumerate(range(x - 1, x + w + 1, 5)):
        c = c1 if i % 2 == 0 else c2
        cv.poly([(sx, y + depth), (sx + 5, y + depth), (sx + 2, y + depth + 3)], shade(c, -0.15))
    cv.hline(x - 1, y + depth + 4, w + 2, C(SHADOW, 0.35))


def career_center_front(cv, cx, base, seed=0):
    """Career Center: a modern glass entry set in the sandstone, brushed-steel letters on a dark
    fascia, a hanging CAREER FAIR banner and posters in the side lights. Door top at base - 66."""
    rng = _rng(seed)
    x0, x1 = cx - 58, cx + 58
    cv.rect(x0 - 3, base - 90, x1 - x0 + 6, 90, TRIM[1]); cv.hline(x0 - 3, base - 90, x1 - x0 + 6, TRIM[3])
    # fascia
    cv.rect(x0, base - 86, x1 - x0, 15, OUT)
    cv.rect(x0 + 1, base - 85, x1 - x0 - 2, 13, "#24303a"); cv.hline(x0 + 1, base - 85, x1 - x0 - 2, "#3e5262")
    label = "CAREER CENTER"
    text(cv, label, cx - text_width(label) // 2 + 1, base - 84, "#dce8ec")
    # glass curtain: two side lights and the doors, steel mullions
    gx0, gx1, gy = x0 + 4, x1 - 4, base - 66
    cv.rect(gx0 - 2, gy - 2, gx1 - gx0 + 4, 68, "#3a4652")
    _shop_glass(cv, gx0, gy, gx1 - gx0, 64, COOL_GLOW, seed)
    # inside: a reception counter and a screen, people-free
    cv.rect(gx0 + 6, gy + 40, 28, 10, "#5a6a74"); cv.hline(gx0 + 6, gy + 40, 28, "#a8c0c8")
    cv.rect(gx0 + 12, gy + 30, 14, 9, "#1e2a34"); cv.rect(gx0 + 13, gy + 31, 12, 7, "#5ab0c8"); cv.hline(gx0 + 14, gy + 33, 8, "#e6f6ee")
    # posters in the side lights
    for px_, col, words in [(gx1 - 30, "#c8962e", ("FAIR", "OCT")), (gx1 - 16, "#3e7aa0", ("JOBS", ""))]:
        cv.rect(px_, gy + 18, 13, 20, col); cv.hline(px_, gy + 18, 13, shade(col, 0.3))
        cv.rect(px_ + 2, gy + 30, 9, 1, "#f2ead6"); cv.rect(px_ + 2, gy + 33, 6, 1, "#f2ead6")
    for mx in (gx0 + 40, cx - 16, cx, cx + 16, gx1 - 40):
        cv.vline(mx, gy, 64, "#3a4652"); cv.vline(mx + 1, gy, 64, "#8a98a4")
    cv.hline(gx0, gy + 14, gx1 - gx0, "#3a4652")
    # door pulls, a reflection
    for hx in (cx - 4, cx + 4):
        cv.rect(hx, gy + 30, 1, 14, "#dce8ec")
    cv.line(gx0 + 8, gy + 4, gx0 + 2, gy + 12, C("#ffffff", 0.4))
    cv.line(cx + 12, gy + 16, cx + 6, gy + 26, C("#ffffff", 0.35))
    # canopy: a thin steel blade over the entry
    cv.rect(cx - 30, gy - 6, 60, 4, OUT); cv.rect(cx - 29, gy - 5, 58, 2, "#8a98a4"); cv.hline(cx - 29, gy - 5, 58, "#c8d4dc")
    cv.hline(cx - 30, gy - 2, 60, C(SHADOW, 0.4))
    cv.rect(gx0 - 3, base - 3, gx1 - gx0 + 6, 3, TRIM[1]); cv.hline(gx0 - 3, base - 3, gx1 - gx0 + 6, TRIM[3])


def hanging_banner(cv, x, y, w, h, colour, lines, ink="#f2ead6"):
    """A vertical fabric banner on a bracket arm, a few short words on it."""
    cv.rect(x - 3, y - 2, w + 6, 2, OUT); cv.hline(x - 3, y - 2, w + 6, IRON[3])
    cv.rect(x, y, w, h, OUT)
    cv.rect(x + 1, y, w - 2, h - 1, colour); cv.vline(x + 1, y, h - 1, shade(colour, 0.2)); cv.vline(x + w - 2, y, h - 1, shade(colour, -0.25))
    cv.poly([(x + 1, y + h - 1), (x + w // 2, y + h - 5), (x + w - 1, y + h - 1)], C(SHADOW, 0.0))
    for k, s in enumerate(lines):
        text(cv, s, x + w // 2 - text_width(s) // 2 + 1, y + 3 + k * 10, ink)


def umc_front(cv, x0, x1, base, pav0, pav1, book_cx, career_cx, door_bottom, seed=3):
    """The UMC's front at character scale: two three-storey sandstone wings under red tile, the
    taller entrance pavilion with UNIVERSITY MEMORIAL CENTER on its frieze and its doors open, the
    Book Store front on the west wing and the Career Center on the east wing.
    Returns light points (lanterns, sconces) for twinkle layers and window spots for reflections."""
    rng = _rng(seed)
    eave = base - 152
    glows = []
    roof_tiles(cv, x0 - 5, eave - 18, x1 - x0 + 10, 16, seed=seed)
    ashlar_wall(cv, x0, eave, x1 - x0, base - eave, SANDSTONE, course=5, seed=seed, cap=False)
    cornice(cv, x0 - 2, eave, x1 - x0 + 4)
    # string course between ground floor and the upper floors
    cv.rect(x0, base - 100, x1 - x0, 4, TRIM[2]); cv.hline(x0, base - 100, x1 - x0, TRIM[4]); cv.hline(x0, base - 97, x1 - x0, TRIM[0])
    # plinth
    cv.rect(x0, base - 8, x1 - x0, 8, TRIM[1]); cv.hline(x0, base - 8, x1 - x0, TRIM[3]); cv.hline(x0, base - 1, x1 - x0, C(SHADOW, 0.6))
    for qx in (x0, x1 - 7, pav0 - 7, pav1):
        for k, qy in enumerate(range(eave + 7, base - 8, 6)):
            qw = 7 if k % 2 == 0 else 5
            ox = qx if qx in (x0, pav1) else qx + 7 - qw
            cv.rect(ox, qy, qw, 5, TRIM[2]); cv.hline(ox, qy, qw, TRIM[4]); cv.hline(ox, qy + 4, qw, TRIM[0])
    # upper two storeys of windows on both wings
    lit_pattern = [1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1]
    spots = []
    i = 0
    for (a, b) in ((x0 + 12, pav0 - 22), (pav1 + 14, x1 - 20)):
        n = (b - a) // 32 + 1
        for k in range(n):
            wx = a + k * 32
            window(cv, wx, eave + 14, 14, 20, lit=bool(lit_pattern[i % 18]), seed=i)
            window(cv, wx - 1, eave + 56 - 8, 16, 26, lit=bool(lit_pattern[(i + 5) % 18]), seed=i + 30,
                   curtain="#7e3a30" if i % 3 == 0 else None)
            if lit_pattern[(i + 5) % 18]:
                spots.append(wx + 7)
            i += 1
    # ground floor: tall arched windows except where the shop fronts are
    for (a, b) in ((x0 + 12, pav0 - 22), (pav1 + 14, x1 - 20)):
        n = (b - a) // 32 + 1
        for k in range(n):
            wx = a + k * 32
            if abs(wx + 7 - book_cx) < 80 or abs(wx + 7 - career_cx) < 76:
                continue
            window(cv, wx - 1, base - 52, 16, 36, lit=True, arch=True, seed=i + 60, curtain="#7e3a30")
            spots.append(wx + 7)
            i += 1
    book_store_front(cv, book_cx, base, seed=seed + 4)
    career_center_front(cv, career_cx, base, seed=seed + 5)
    # sconces either side of each shop front
    for sx in (book_cx - 72, book_cx + 72, career_cx - 68, career_cx + 68):
        wall_lantern(cv, sx, base - 70)
        glows.append((sx, base - 66))
    # the pavilion: rises above the wings, its own cornice, the frieze inscription
    pw = pav1 - pav0
    ashlar_wall(cv, pav0, 0, pw, door_bottom, SANDSTONE, course=5, seed=seed + 9, cap=False)
    for px in (pav0, pav1 - 7):
        pilaster(cv, px, 0, 7, door_bottom)
    cv.rect(pav0 + 7, 0, pw - 14, 6, ROOF[2])
    roof_tiles(cv, pav0 - 4, 0, pw + 8, 8, seed=seed + 2)
    cornice(cv, pav0 - 4, 10, pw + 8)
    fx0, fx1 = pav0 + 10, pav1 - 10
    cv.rect(fx0, 20, fx1 - fx0, 13, TRIM[1]); cv.rect(fx0 + 1, 21, fx1 - fx0 - 2, 11, TRIM[3]); cv.hline(fx0 + 1, 21, fx1 - fx0 - 2, TRIM[4])
    cv.hline(fx0 + 1, 31, fx1 - fx0 - 2, TRIM[1])
    s = "UNIVERSITY MEMORIAL CENTER"
    text(cv, s, (pav0 + pav1) // 2 - text_width(s) // 2 + 1, 22, "#5a4038")
    cx = (pav0 + pav1) // 2
    # the great arched window over the doors, warm light behind
    window(cv, cx - 14, 62, 28, 44, lit=True, arch=True, seed=99, curtain="#7e3a30")
    spots.append(cx)
    # two small upper windows on the pavilion
    for wx in (pav0 + 22, pav1 - 36):
        window(cv, wx, 52, 14, 22, lit=True, seed=wx)
        window(cv, wx - 1, 92, 16, 28, lit=wx < cx, arch=True, seed=wx + 1)
    open_doorway(cv, cx, door_bottom, 46, 66, seed)
    for dx in (-36, 36):
        wall_lantern(cv, cx + dx, door_bottom - 54)
        glows.append((cx + dx, door_bottom - 50))
    # ivy creeping up the pavilion corners
    for vx, dirn in [(pav0 + 7, 1), (pav1 - 8, -1)]:
        for _ in range(90):
            yy = int(rng.integers(60, door_bottom - 2))
            xx = vx + dirn * int(abs(rng.normal(0, 3)))
            cv.px(xx, yy, ["#2f4237", "#3f5741", "#566d4a"][int(rng.integers(3))])
    return glows, spots


# --------------------------------------------------------------------------------------------
# Farrand Hall

def dorm_window(cv, x, y, w, h, kind, seed=0):
    """A 1950s steel window in a sandstone surround, with a student's room behind it.
    kind: dark, lit, blinds, flag, lights, plant, poster, tv."""
    rng = _rng(seed)
    cv.rect(x - 2, y - 3, w + 4, 3, TRIM[2]); cv.hline(x - 2, y - 3, w + 4, TRIM[4])           # lintel
    cv.rect(x - 1, y - 1, w + 2, h + 2, FRAME)
    lit = kind != "dark"
    pal = GLOW if lit else DARKGLASS
    cv.rect(x, y, w, h, pal[2]); cv.rect(x, y, w, h // 3, pal[3]); cv.rect(x, y + h - h // 3, w, h // 3, pal[1])
    if kind == "dark":
        cv.line(x + 1, y + h - 3, x + w - 3, y + 1, DARKGLASS[3])
    elif kind == "blinds":
        for yy in range(y + 1, y + h - 4, 2):
            cv.hline(x, yy, w, "#d8c8a0")
        cv.rect(x, y + h - 4, w, 4, pal[2])
    elif kind == "flag":
        cv.rect(x + 1, y + 2, w - 2, h - 6, BLACKS[1]); cv.rect(x + 3, y + 5, w - 6, h - 12, GOLD[3])
        cv.rect(x + w // 2 - 1, y + 7, 3, 3, BLACKS[1])
    elif kind == "lights":
        for k in range(x, x + w, 3):
            cv.px(k, y + 2 + (1 if (k // 3) % 2 else 0), ["#f2a0a0", "#fff0c4", "#a8d8c8", "#f6cf7a"][(k // 3) % 4])
    elif kind == "plant":
        cv.rect(x + 2, y + h - 5, 6, 4, "#a8604a")
        for k in range(8):
            cv.px(x + 2 + int(rng.integers(0, 7)), y + h - 6 - int(rng.integers(0, 6)), LEAF[3 + k % 2])
    elif kind == "poster":
        cv.rect(x + w - 8, y + 3, 6, 9, "#5a7ab0"); cv.rect(x + w - 7, y + 4, 4, 3, "#f2a0b4")
    elif kind == "tv":
        cv.rect(x, y, w, h, "#2a3a5a"); cv.rect(x, y + h - 6, w, 6, "#1e2a44")
    cv.vline(x + w // 2, y, h, FRAME); cv.hline(x, y + h // 2, w, FRAME)
    cv.rect(x - 2, y + h + 1, w + 4, 2, TRIM[3]); cv.hline(x - 2, y + h + 3, w + 4, C(SHADOW, 0.5))
    return lit


def farrand_front(cv, x0, x1, base, door_cx, seed=7):
    """Farrand Hall at character scale: a 1950s residence hall of red brick with sandstone
    quoins, sill courses and window surrounds, a low red tile roof, four floors of dorm windows
    with lives behind them, and the lobby entrance under a flat canopy with its name carved above.
    Returns (glows, tv_rect, fairy_points)."""
    from facade import brick_wall
    rng = _rng(seed)
    eave = base - 168
    roof_tiles(cv, x0 - 4, eave - 16, x1 - x0 + 8, 14, seed=seed)
    brick_wall(cv, x0, eave, x1 - x0, base - eave, seed=seed)
    cornice(cv, x0 - 2, eave, x1 - x0 + 4)
    # sandstone base and quoins on the corner
    cv.rect(x0, base - 14, x1 - x0, 14, SANDSTONE[3]); cv.hline(x0, base - 14, x1 - x0, SANDSTONE[5])
    for xx in range(x0, x1, 12):
        cv.vline(xx + (6 if (xx // 12) % 2 else 0), base - 13, 13, SANDSTONE[1])
    cv.hline(x0, base - 7, x1 - x0, SANDSTONE[1]); cv.hline(x0, base - 1, x1 - x0, C(SHADOW, 0.6))
    for k, qy in enumerate(range(eave + 8, base - 14, 6)):
        qw = 8 if k % 2 == 0 else 5
        cv.rect(x0, qy, qw, 5, TRIM[2]); cv.hline(x0, qy, qw, TRIM[4]); cv.hline(x0, qy + 4, qw, TRIM[0])
    # floors: sill course under each row
    rows = [eave + 14, eave + 50, eave + 86]
    kinds = ["lit", "dark", "blinds", "lit", "flag", "dark", "lights", "lit", "plant", "dark", "lit", "poster",
             "blinds", "lit", "dark", "tv", "lit", "lit", "dark", "lights", "lit", "blinds", "plant", "lit"]
    tv = None
    fairy = []
    i = 0
    for ry in rows:
        cv.rect(x0, ry + 26, x1 - x0, 3, SANDSTONE[4]); cv.hline(x0, ry + 26, x1 - x0, SANDSTONE[5])
        for wx in range(x0 + 16, x1 - 10, 30):
            k = kinds[i % len(kinds)]
            dorm_window(cv, wx, ry, 16, 20, k, seed=i)
            if k == "tv":
                tv = (wx, ry, 16, 20)
            if k == "lights":
                fairy += [(xx, ry + 2 + (1 if ((xx - wx) // 3) % 2 else 0)) for xx in range(wx, wx + 16, 3)]
            i += 1
    # ground floor: windows either side of the entrance
    gy = base - 54
    for wx in range(x0 + 16, x1 - 10, 30):
        if abs(wx + 8 - door_cx) < 52:
            continue
        dorm_window(cv, wx, gy, 16, 24, ["lit", "blinds", "lit", "dark", "lit"][i % 5], seed=i)
        i += 1
    # the entrance: sandstone portal, carved name, flat canopy, glass doors and the lit lobby
    px0, px1 = door_cx - 40, door_cx + 40
    cv.rect(px0, base - 98, px1 - px0, 98, SANDSTONE[3])
    for yy in range(base - 98, base, 6):
        cv.hline(px0, yy, px1 - px0, SANDSTONE[2])
    cv.vline(px0, base - 98, 98, SANDSTONE[5]); cv.vline(px1 - 1, base - 98, 98, SANDSTONE[1])
    cv.rect(px0 - 2, base - 100, px1 - px0 + 4, 3, TRIM[3]); cv.hline(px0 - 2, base - 100, px1 - px0 + 4, TRIM[4])
    name = "FARRAND HALL"
    cv.rect(door_cx - 40 + 2, base - 94, 76, 12, SANDSTONE[2])
    text(cv, name, door_cx - text_width(name) // 2 + 1, base - 93, "#3a2420")
    text(cv, name, door_cx - text_width(name) // 2, base - 94, "#e8cca8")
    dw, dh = 38, 66
    dx = door_cx - dw // 2
    cv.rect(dx - 2, base - dh - 2, dw + 4, dh + 2, FRAME)
    _shop_glass(cv, dx, base - dh, dw, dh, GLOW, seed)
    # lobby: a notice board and the front desk far inside
    cv.rect(dx + 4, base - 40, 14, 10, "#a8744f"); cv.rect(dx + 6, base - 38, 4, 3, "#f2ead6"); cv.rect(dx + 11, base - 37, 4, 4, "#f2a0b4")
    cv.rect(dx + 20, base - 26, 16, 8, WOOD[3]); cv.hline(dx + 20, base - 26, 16, WOOD[5])
    cv.vline(door_cx, base - dh, dh, FRAME); cv.vline(door_cx - 1, base - dh, dh, "#4a4458")
    cv.hline(dx, base - dh + 20, dw, FRAME)
    for hx in (door_cx - 4, door_cx + 3):
        cv.rect(hx, base - 38, 1, 10, "#c8c4b8")
    # flat canopy on two brackets
    cv.rect(door_cx - 34, base - dh - 10, 68, 6, OUT)
    cv.rect(door_cx - 33, base - dh - 9, 66, 4, SANDSTONE[4]); cv.hline(door_cx - 33, base - dh - 9, 66, SANDSTONE[5])
    cv.hline(door_cx - 34, base - dh - 4, 68, C(SHADOW, 0.45))
    glows = [(door_cx - 26, base - dh - 2), (door_cx + 26, base - dh - 2)]
    for gx_, gy_ in glows:
        cv.rect(gx_ - 2, gy_ - 1, 5, 3, GLOW[4]); cv.px(gx_, gy_ - 1, "#ffffff")
    # a downpipe and a little CU flag bracket
    cv.vline(x1 - 6, eave + 4, base - eave - 18, "#2a2838"); cv.vline(x1 - 7, eave + 4, base - eave - 18, "#4d4b66")
    return glows, tv, fairy


# --------------------------------------------------------------------------------------------
# Ground

def paver_poly(cv, pts, seed=0, brick=(9, 4), pal=PAVER, edge=True):
    """Fill a polygon with running-bond pavers and a sandstone kerb along its outline."""
    from PIL import Image, ImageDraw
    mask = Image.new("L", (cv.w, cv.h), 0)
    ImageDraw.Draw(mask).polygon([tuple(p) for p in pts], fill=255)
    m = np.array(mask) > 0
    ys, xs = np.where(m)
    if not len(ys):
        return m
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    rng = _rng(seed)
    bw, bh = brick
    sub = Canvas(x1 - x0, y1 - y0)
    sub.rect(0, 0, x1 - x0, y1 - y0, pal[0])
    for row, yy in enumerate(range(0, y1 - y0, bh)):
        off = ((row + y0 // bh) % 2) * (bw // 2)
        for xx in range(-off - (x0 % bw), x1 - x0, bw):
            a, b = max(0, xx), min(x1 - x0, xx + bw - 1)
            if b <= a:
                continue
            r = rng.random()
            tone = pal[3] if r < 0.5 else pal[2] if r < 0.8 else pal[4] if r < 0.95 else pal[5]
            sub.rect(a, yy, b - a, bh - 1, tone)
            sub.hline(a, yy, b - a, shade(tone, 0.07))
    reg = m[y0:y1, x0:x1]
    cv.a[y0:y1, x0:x1][reg] = sub.a[reg]
    if edge:
        from scipy import ndimage
        ring = m & ~ndimage.binary_erosion(m, structure=np.ones((3, 3)))
        cv.a[ring] = C(TRIM[2])
        inner = ndimage.binary_erosion(m, structure=np.ones((3, 3))) & ~ndimage.binary_erosion(m, structure=np.ones((5, 5)))
        cv.a[inner] = C(TRIM[1])
    return m


def court_tiles(cv, x, y, w, h, tile=(22, 12), seed=0, pal=COURT):
    """Large square-cut sandstone flags laid in a grid (the fountain court's floor)."""
    rng = _rng(seed)
    tw, th = tile
    cv.rect(x, y, w, h, pal[0])
    for yy in range(y, y + h, th):
        for xx in range(x, x + w, tw):
            a, b = xx + 1, min(x + w, xx + tw)
            hh = min(th - 1, y + h - yy - 1)
            if b <= a or hh <= 0:
                continue
            tone = mix(pal[3], pal[int(rng.integers(2, 6))], 0.5)
            cv.rect(a, yy + 1, b - a, hh, tone)
            cv.hline(a, yy + 1, b - a, shade(tone, 0.08)); cv.hline(a, yy + hh, b - a, shade(tone, -0.07))
            for _ in range((b - a) * hh // 16):
                cv.px(a + int(rng.integers(0, b - a)), yy + 1 + int(rng.integers(0, hh)), shade(tone, float(rng.choice([-0.06, 0.05]))))


def chalk_art(cv, x, y, seed=0):
    """Pavement chalk: WELCOME HOME / BUFFS in colours, a sun, hearts, a hopscotch run."""
    rng = _rng(seed)
    def col(i):
        return C(CHALK_COLS[i % len(CHALK_COLS)], 0.85)
    text(cv, "WELCOME HOME", x, y, col(0))
    text(cv, "BUFFS", x + 18, y + 10, col(3))
    # underline swoosh and a sun
    for k in range(48):
        cv.px(x + 4 + k, y + 21 + int(round(np.sin(k / 6) * 1.2)), col(2))
    sx, sy = x + 80, y + 8
    cv.ellipse(sx - 4, sy - 4, 9, 9, col(3))
    cv.ellipse(sx - 2, sy - 2, 5, 5, C("#000000", 0.0))
    for a in np.linspace(0, 2 * np.pi, 9)[:-1]:
        cv.px(int(sx + np.cos(a) * 7), int(sy + np.sin(a) * 7), col(3))
    for (hx, hy, c) in [(x - 12, y + 4, 1), (x + 70, y + 20, 1), (x + 92, y - 2, 4)]:
        cv.px(hx, hy, col(c)); cv.px(hx + 2, hy, col(c)); cv.hline(hx - 1, hy + 1, 5, col(c)); cv.hline(hx, hy + 2, 3, col(c)); cv.px(hx + 1, hy + 3, col(c))
    # hopscotch boxes running down
    hx, hy = x + 104, y + 4
    for k, n in enumerate([1, 2, 1, 2, 1]):
        for j in range(n):
            bx = hx + (j * 12 if n == 2 else 6)
            by = hy + k * 8
            for (a, b, c_, d) in [(bx, by, 11, 1), (bx, by + 7, 11, 1), (bx, by, 1, 8), (bx + 10, by, 1, 8)]:
                cv.rect(a, b, c_, d, col(5 if k % 2 else 4))
            cv.px(bx + 5, by + 3, col(0))


def drain_grate(cv, x, y, w=12, h=5):
    cv.rect(x, y, w, h, IRON[1])
    for xx in range(x + 1, x + w - 1, 2):
        cv.vline(xx, y + 1, h - 2, IRON[0])
    cv.hline(x, y, w, IRON[3])


def tree_grate(cv, cx, cy, r=18):
    """Round cast-iron tree grate flush with the paving."""
    cv.ellipse(cx - r - 2, cy - r // 3 - 1, 2 * r + 5, 2 * (r // 3) + 3, TRIM[1])
    cv.ellipse(cx - r, cy - r // 3, 2 * r + 1, 2 * (r // 3) + 1, IRON[1])
    for a in np.linspace(0, np.pi, 9):
        for rr in range(5, r):
            cv.px(int(round(cx + np.cos(a) * rr)), int(round(cy + np.sin(a) * rr / 3)), IRON[2])
            cv.px(int(round(cx + np.cos(a) * rr)), int(round(cy - np.sin(a) * rr / 3)), IRON[2])
    cv.ellipse(cx - 6, cy - 2, 13, 5, "#2a1e1a")


def parking_lane(cv, x, y, w, h, seed=0, bays=()):
    """The service lane the food trucks park on: asphalt, yellow kerb paint, bay lines."""
    from surfaces import asphalt
    asphalt(cv, x, y, w, h, seed=seed)
    for bx in bays:
        cv.vline(bx, y + 4, h - 6, C("#e6e2d8", 0.6))
    cv.rect(x, y + h - 3, w, 3, TRIM[2]); cv.hline(x, y + h - 3, w, TRIM[4])
    for xx in range(x, x + w, 10):
        cv.rect(xx, y + h - 3, 6, 1, "#d8b040")


# --------------------------------------------------------------------------------------------
# The fountain

FOUNTAIN = {"x0": 950, "x1": 1250, "back": 300, "front": 350, "face": 12, "jet_y": 328}
JETS = [(982, 22), (1018, 30), (1059, 36), (1100, 46), (1141, 36), (1182, 30), (1218, 22)]


def fountain_basin(cv, f=FOUNTAIN, reflections=(), seed=0):
    """The basin as seen from the court: sandstone coping all round (the near rim is the prop),
    the inner wall, dark water with the UMC's lit windows reflected in it, ripples and foam rings."""
    rng = _rng(seed)
    x0, x1, back, front = f["x0"], f["x1"], f["back"], f["front"]
    # outer coping top (back and the two ends), drawn as a band 6px deep
    cv.rect(x0 - 2, back - 2, x1 - x0 + 4, front - back + 4, OUT)
    cv.rect(x0, back, x1 - x0, front - back, TRIM[2])
    cv.hline(x0, back, x1 - x0, TRIM[4])
    for xx in range(x0 + 14, x1, 26):
        cv.vline(xx, back, 6, TRIM[1])
    # water area inside the coping
    wx0, wx1, wy0, wy1 = x0 + 7, x1 - 7, back + 6, front
    cv.rect(wx0, wy0, wx1 - wx0, wy1 - wy0, WATER[2])
    # inner wall of the far rim (lit stone in shadow), end walls
    cv.rect(wx0, wy0, wx1 - wx0, 4, SANDSTONE[1]); cv.hline(wx0, wy0, wx1 - wx0, SANDSTONE[2])
    cv.rect(wx0, wy0 + 4, 3, wy1 - wy0 - 4, SANDSTONE[1]); cv.rect(wx1 - 3, wy0 + 4, 3, wy1 - wy0 - 4, SANDSTONE[0])
    # water bands: darker near the far wall, a lighter sheen in the middle
    cv.rect(wx0 + 3, wy0 + 4, wx1 - wx0 - 6, 5, WATER[1])
    cv.rect(wx0 + 3, wy0 + 20, wx1 - wx0 - 6, 10, WATER[3])
    cv.rect(wx0 + 3, wy1 - 8, wx1 - wx0 - 6, 8, WATER[2])
    # reflections of the lit windows: broken warm streaks
    for (rx, strength) in reflections:
        if not (wx0 + 4 < rx < wx1 - 4):
            continue
        for yy in range(wy0 + 6, wy1 - 1):
            if rng.random() < 0.7:
                ln = int(rng.integers(2, 5 + strength))
                cv.hline(rx - ln // 2 + int(rng.integers(-1, 2)), yy, ln, C("#f6cf7a", 0.25 + 0.12 * strength))
    # ripples: short light dashes in loose rows
    for _ in range((wx1 - wx0) * (wy1 - wy0) // 40):
        xx, yy = int(rng.integers(wx0 + 4, wx1 - 8)), int(rng.integers(wy0 + 6, wy1 - 1))
        cv.hline(xx, yy, int(rng.integers(3, 7)), WATER[4] if rng.random() < 0.7 else WATER[5])
    # foam rings where the jets land
    for (jx, jh) in JETS:
        jy = f["jet_y"]
        cv.ellipse(jx - 8, jy - 2, 17, 6, WATER[5])
        cv.ellipse(jx - 6, jy - 1, 13, 4, WATER[6])
        cv.ellipse(jx - 3, jy - 1, 7, 3, WATER[7])
    # a few coins glinting on the bottom near the front
    for _ in range(14):
        xx, yy = int(rng.integers(wx0 + 6, wx1 - 6)), int(rng.integers(wy1 - 7, wy1 - 1))
        cv.px(xx, yy, "#c8a050" if rng.random() < 0.7 else "#d8d8dc")
    return (wx0, wy0, wx1, wy1)


def fountain_front(f=FOUNTAIN, seed=0):
    """Prop sprite: the near rim of the basin (coping top and front face) with the bronze plaque,
    and the row of jets rising out of the water, each with a spray crown. Anchored at the bottom
    centre of the front face."""
    x0, x1, front, face = f["x0"], f["x1"], f["front"], f["face"]
    top_y = f["jet_y"] - max(h for _, h in JETS) - 8
    W = x1 - x0 + 8
    H = front + face + 4 - top_y
    cv = Canvas(W, H, seed=seed)
    ox, oy = x0 - 4, top_y           # canvas origin in room pixels
    rng = _rng(seed)
    # jets: core, sheath, crown of falling droplets
    for (jx, jh) in JETS:
        cx = jx - ox
        by = f["jet_y"] - oy
        ty = by - jh
        cv.rect(cx - 2, ty + 3, 5, jh - 3, C(JET[0], 0.55))
        cv.rect(cx - 1, ty + 1, 3, jh - 1, C(JET[1], 0.9))
        cv.vline(cx, ty, jh, JET[3])
        cv.vline(cx - 1, ty + 4, jh - 8, JET[2])
        # crown: droplets arcing out and down from the top
        for side in (-1, 1):
            for k in range(1, 6):
                dx = side * (k + 1)
                dy = int(round(k * k * 0.45)) - 1
                cv.px(cx + dx, ty + dy, JET[2] if k < 3 else C(JET[1], 0.8))
                if k % 2 == 0:
                    cv.px(cx + dx + side, ty + dy + 2, C(JET[1], 0.7))
        cv.rect(cx - 1, ty - 1, 3, 2, JET[3])
        # splash at the base, in front of the foam ring
        for k in range(6):
            cv.px(cx + int(rng.integers(-5, 6)), by - int(rng.integers(0, 4)), C(JET[2], 0.85))
    # the near rim: coping top (6 rows) and the vertical face
    ry = front - oy - 6
    cv.rect(0, ry - 1, W, 1, OUT)
    cv.rect(2, ry, W - 4, 6, TRIM[2]); cv.hline(2, ry, W - 4, TRIM[4]); cv.hline(2, ry + 5, W - 4, TRIM[1])
    for xx in range(14, W, 26):
        cv.vline(xx, ry, 6, TRIM[1])
    fy = ry + 6
    cv.rect(0, ry - 1, 2, face + 8, OUT); cv.rect(W - 2, ry - 1, 2, face + 8, OUT)
    cv.rect(2, fy, W - 4, face, SANDSTONE[3])
    for yy in range(fy + 3, fy + face, 4):
        cv.hline(2, yy, W - 4, SANDSTONE[2])
        off = 0 if (yy // 4) % 2 else 9
        for xx in range(2 + off, W - 2, 18):
            cv.vline(xx, yy - 3, 3, SANDSTONE[2])
    cv.hline(2, fy, W - 4, SANDSTONE[5])
    cv.rect(0, fy + face, W, 1, OUT)
    # bronze plaque centred on the face
    s = "DALTON TRUMBO FOUNTAIN COURT"
    pw = text_width(s) + 6
    px = W // 2 - pw // 2
    cv.rect(px - 1, fy + 1, pw + 2, face - 1, OUT)
    cv.rect(px, fy + 2, pw, face - 3, BRONZE[2]); cv.hline(px, fy + 2, pw, BRONZE[4]); cv.hline(px, fy + face - 2, pw, BRONZE[1])
    text(cv, s, px + 4, fy + 1, "#f2d690")
    for (sx_, sy_) in ((px + 1, fy + 3), (px + pw - 2, fy + 3)):
        cv.px(sx_, sy_, BRONZE[4])
    # wet splash darkening on the coping near the jets
    for _ in range(30):
        cv.px(int(rng.integers(6, W - 6)), ry + int(rng.integers(1, 5)), SANDSTONE[2])
    # shadow on the ground in front
    cv.rect(2, fy + face + 1, W - 4, 2, C(SHADOW, 0.35))
    ax, ay = (1100 - ox), front + face - oy
    return cv, ax, ay


def fountain_layers(f=FOUNTAIN, seed=0):
    """Animated water: sparkles drifting on the surface (three offset blink phases), the foam at
    each jet pulsing, droplets falling around the jet crowns."""
    rng = _rng(seed)
    x0, x1, back, front = f["x0"], f["x1"], f["back"], f["front"]
    wx0, wy0, wx1, wy1 = x0 + 10, back + 10, x1 - 10, front - 1
    layers = []
    for j in range(3):
        rects = []
        for _ in range(26):
            rects.append([int(rng.integers(wx0, wx1)), int(rng.integers(wy0, wy1)), int(rng.integers(2, 4)), 1,
                          "c8e4f4" if rng.random() < 0.6 else "f6dca0", 0.8])
        layers.append({"kind": "blink", "pattern": "".join("1" if k == j else "0" for k in range(3)), "rate": 3.0,
                       "rects": rects})
    for j in range(2):
        rects = []
        for (jx, jh) in JETS:
            jy = f["jet_y"]
            r = 9 if j == 0 else 7
            rects.append([jx - r, jy, 2 * r + 1, 1, "c8e4f4", 0.9])
            rects.append([jx - r + 2, jy + 2, 2 * r - 3, 1, "7aa6c8", 0.8])
            # droplets around the crown
            for k in range(3):
                dx = int(rng.integers(5, 10)) * (1 if k % 2 else -1)
                rects.append([jx + dx, jy - jh + 4 + int(rng.integers(0, 10)) + j * 3, 1, 2, "d6ecf8", 0.9])
        layers.append({"kind": "blink", "pattern": "10" if j == 0 else "01", "rate": 4.0, "rects": rects})
    return layers


# --------------------------------------------------------------------------------------------
# Props

def coffee_cart(width=72, height=74, seed=0):
    """A coffee cart: steel body on two wheels, wood counter with an espresso machine and cups,
    a chalk menu, a striped umbrella on a pole, warm bulbs under its rim, COFFEE on the front."""
    rng = _rng(seed)
    w = width
    CW, CH = w + 12, height + 6
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 6, CH - 3
    cx = ox + w // 2
    ground_shadow(cv, cx, base, w // 2 + 2, 3, alpha=0.42)
    # umbrella pole and canopy
    top = base - height
    cv.rect(cx - 1, top + 10, 2, base - top - 40, OUT); cv.vline(cx, top + 10, base - top - 40, IRON[3])
    ub = [(ox - 4, top + 16), (cx, top + 2), (ox + w + 4, top + 16)]
    cv.poly([(ub[0][0] - 1, ub[0][1] + 1), (cx, top + 1), (ub[2][0] + 1, ub[2][1] + 1)], OUT)
    for i in range(8):
        t0, t1 = i / 8, (i + 1) / 8
        a = (ub[0][0] + (ub[2][0] - ub[0][0]) * t0, top + 16)
        b = (ub[0][0] + (ub[2][0] - ub[0][0]) * t1, top + 16)
        cv.poly([(cx, top + 2), a, b], "#2c6a68" if i % 2 else "#e6d6b1")
    for k in range(ox - 4, ox + w + 4, 6):
        cv.poly([(k, top + 16), (k + 6, top + 16), (k + 3, top + 19)], "#2c6a68" if (k // 6) % 2 else "#e6d6b1")
    cv.hline(ox - 4, top + 16, w + 8, shade("#2c6a68", -0.3))
    cv.rect(cx - 1, top - 1, 3, 3, OUT); cv.px(cx, top, GOLD[3])
    bulbs = []
    for k in range(ox - 1, ox + w + 2, 7):
        cv.px(k, top + 20, "#1a1418"); cv.rect(k, top + 21, 2, 2, AMBER[3]); cv.px(k, top + 21, AMBER[4])
        bulbs.append((k, top + 21))
    # body
    by0 = base - 34
    cv.rect(ox - 1, by0 - 1, w + 2, 26, OUT)
    cv.rect(ox, by0, w, 24, "#3e6663"); cv.hline(ox, by0, w, "#5c897c"); cv.rect(ox, by0 + 18, w, 6, "#2c4a4c")
    for sx in range(ox + 12, ox + w - 4, 16):
        cv.vline(sx, by0 + 2, 15, "#2c4a4c")
    # name board on the front
    s = "COFFEE"
    nw = text_width(s) + 8
    cv.rect(cx - nw // 2, by0 + 4, nw, 11, OUT); cv.rect(cx - nw // 2 + 1, by0 + 5, nw - 2, 9, "#e6d6b1")
    text(cv, s, cx - nw // 2 + 4, by0 + 4, "#4a2b24")
    # counter top with machine and cups
    cv.rect(ox - 3, by0 - 4, w + 6, 4, OUT); cv.rect(ox - 2, by0 - 3, w + 4, 2, WOOD[4]); cv.hline(ox - 2, by0 - 3, w + 4, WOOD[5])
    mx = ox + 8
    cv.rect(mx, by0 - 18, 20, 14, OUT); cv.rect(mx + 1, by0 - 17, 18, 12, "#b4b8c4"); cv.hline(mx + 1, by0 - 17, 18, "#e0e4ec")
    cv.rect(mx + 3, by0 - 12, 4, 3, "#2a2832"); cv.rect(mx + 12, by0 - 12, 4, 3, "#2a2832")
    cv.rect(mx + 2, by0 - 21, 16, 3, OUT); cv.rect(mx + 3, by0 - 20, 14, 1, "#8a8e9c")
    for k in range(3):
        cv.rect(mx + 3 + k * 5, by0 - 23, 3, 2, "#e6e2d8")
    # a steam wisp
    for k in range(5):
        cv.px(mx + 6 + (k % 2), by0 - 26 - k * 2, C("#e6e2d8", 0.5))
    for k in range(4):
        cx_ = ox + 36 + k * 6
        cv.rect(cx_, by0 - 7, 4, 4, "#f2ead6"); cv.hline(cx_, by0 - 7, 4, "#ffffff"); cv.hline(cx_, by0 - 5, 4, "#a8604a")
    cv.rect(ox + w - 10, by0 - 9, 6, 6, OUT); cv.rect(ox + w - 9, by0 - 8, 4, 4, "#9ab8c8")
    # chalk menu on an easel leaning on the cart
    from lib_farrand import menu_board
    menu_board(cv, ox + w - 18, by0 + 2, 18, 22, lines=4, seed=seed + 3)
    # wheels and a handle
    for wx in (ox + 12, ox + w - 26):
        cv.ellipse(wx - 6, base - 13, 13, 13, OUT); cv.ellipse(wx - 4, base - 11, 9, 9, IRON[2]); cv.px(wx, base - 7, IRON[4])
    cv.rect(ox - 6, by0 + 6, 6, 2, OUT); cv.rect(ox - 6, by0 + 6, 2, 10, OUT)
    cv.rect(ox + w - 4, base - 8, 3, 8, OUT)
    return cv, cx, base, bulbs


def map_board(width=66, height=58, seed=0):
    """Campus map on two posts: CAMPUS MAP header, green blocks of lawn, sandstone buildings,
    red-roofed boxes, paths, the fountain, and a red YOU ARE HERE dot."""
    rng = _rng(seed)
    w = width
    CW, CH = w + 6, height + 4
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 3, CH - 2
    ground_shadow(cv, ox + w // 2, base, w // 2, 2)
    top = base - height
    for px in (ox + 6, ox + w - 9):
        cv.rect(px, top + 30, 4, base - top - 30, OUT); cv.vline(px + 1, top + 30, base - top - 31, IRON[3])
    bh = 40
    cv.rect(ox, top, w, bh, OUT)
    cv.rect(ox + 1, top + 1, w - 2, bh - 2, IRON[2]); cv.hline(ox + 1, top + 1, w - 2, IRON[4])
    s = "CAMPUS MAP"
    cv.rect(ox + 2, top + 2, w - 4, 10, "#1e2c3a")
    text(cv, s, ox + w // 2 - text_width(s) // 2 + 1, top + 2, "#f2ead6")
    mx0, my0, mw, mh = ox + 3, top + 13, w - 6, bh - 16
    cv.rect(mx0, my0, mw, mh, "#e6dcc4")
    for (a, b, c, d, col) in [(2, 2, 14, 7, "#7a9a6a"), (20, 3, 12, 9, "#7a9a6a"), (36, 2, 12, 8, "#7a9a6a"),
                              (4, 14, 10, 8, "#7a9a6a"), (34, 15, 14, 7, "#7a9a6a")]:
        cv.rect(mx0 + a, my0 + b, c, d, col)
    for (a, b, c, d) in [(5, 3, 6, 4), (22, 4, 6, 3), (39, 3, 6, 4), (36, 16, 6, 4), (6, 16, 5, 3), (18, 15, 12, 5)]:
        cv.rect(mx0 + a, my0 + b, c, d, "#c4946a"); cv.hline(mx0 + a, my0 + b, c, "#a8504a")
    cv.hline(mx0, my0 + 12, mw, "#b8a888"); cv.vline(mx0 + 17, my0, mh, "#b8a888"); cv.vline(mx0 + 33, my0, mh, "#b8a888")
    cv.rect(mx0 + 20, my0 + 20, 8, 2, "#5a8ac8")
    cv.rect(mx0 + 23, my0 + 17, 3, 3, "#c83a3a"); cv.px(mx0 + 24, my0 + 16, "#ff6a5a")
    cv.rect(ox - 1, top + bh - 1, w + 2, 3, OUT); cv.hline(ox, top + bh, w, IRON[3])
    cv.rect(ox + 2, top - 3, w - 4, 3, OUT); cv.hline(ox + 3, top - 2, w - 6, IRON[3])
    return cv, ox + w // 2, base


def event_column(width=40, height=72, seed=0):
    """A round advertising column wrapped in layered posters, a domed cap with EVENTS on its band."""
    rng = _rng(seed)
    w = width
    CW, CH = w + 8, height + 6
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 4, CH - 3
    cx = ox + w // 2
    ground_shadow(cv, cx, base, w // 2 + 2, 3)
    top = base - height
    body_top = top + 20
    cv.rect(ox, body_top, w, base - body_top - 4, OUT)
    cv.rect(ox + 1, body_top, w - 2, base - body_top - 5, "#4a3a3a")
    # posters: overlapping rectangles, shaded toward the edges (cylinder)
    cols = ["#c84a3c", "#e6d6b1", "#3e7aa0", "#c8962e", "#6a4a8a", "#5c897c", "#f2a0b4", "#e8e2d0"]
    for k in range(14):
        pw_, ph_ = int(rng.integers(8, 15)), int(rng.integers(10, 18))
        px_ = ox + 1 + int(rng.integers(0, w - pw_ - 1))
        py_ = body_top + 1 + int(rng.integers(0, base - body_top - ph_ - 7))
        c = cols[int(rng.integers(len(cols)))]
        cv.rect(px_, py_, pw_, ph_, c)
        cv.hline(px_ + 1, py_ + 2, pw_ - 3, shade(c, -0.35)); cv.hline(px_ + 1, py_ + 5, pw_ - 5, shade(c, -0.3))
        if rng.random() < 0.5:
            cv.rect(px_ + 2, py_ + 8, pw_ - 4, 3, shade(c, 0.35))
    for xx in range(ox + 1, ox + w - 1):
        t = (xx - ox) / w
        if t < 0.15 or t > 0.8:
            cv.vline(xx, body_top, base - body_top - 5, C(SHADOW, 0.35 if t > 0.8 else 0.2))
        elif 0.25 < t < 0.35:
            cv.vline(xx, body_top, base - body_top - 5, C("#fff1d6", 0.12))
    # plinth
    cv.rect(ox - 2, base - 6, w + 4, 6, OUT); cv.rect(ox - 1, base - 5, w + 2, 4, IRON[2]); cv.hline(ox - 1, base - 5, w + 2, IRON[4])
    # cap: dome and finial above, then the band with EVENTS (drawn last so the dome never covers the text)
    cv.ellipse(ox + 2, top, w - 4, 10, OUT); cv.ellipse(ox + 3, top + 1, w - 6, 8, "#3e6663")
    cv.hline(ox + 6, top + 2, w - 14, "#5c897c")
    cv.rect(ox - 3, body_top - 12, w + 6, 12, OUT)
    cv.rect(ox - 2, body_top - 11, w + 4, 10, "#2c4a4c"); cv.hline(ox - 2, body_top - 11, w + 4, "#5c897c")
    s = "EVENTS"
    text(cv, s, cx - text_width(s) // 2 + 1, body_top - 10, GOLD[4])
    cv.rect(cx - 1, top - 2, 3, 4, OUT); cv.px(cx, top - 1, GOLD[3])
    return cv, cx, base


def bike_rack(width=84, height=34, seed=0):
    """Inverted-U hoops with three bikes locked to them (one with a basket, one missing a wheel)."""
    from props import bicycle
    rng = _rng(seed)
    w = width
    CW, CH = w + 10, height + 6
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 5, CH - 3
    ground_shadow(cv, ox + w // 2, base, w // 2 + 2, 3)
    # rear hoops
    for hx in range(ox + 4, ox + w - 4, 20):
        cv.rect(hx, base - 22, 2, 22, OUT); cv.rect(hx + 12, base - 22, 2, 22, OUT)
        cv.rect(hx, base - 23, 14, 2, OUT); cv.hline(hx + 1, base - 22, 12, IRON[4])
        cv.vline(hx + 1, base - 21, 20, IRON[3]); cv.vline(hx + 13, base - 21, 20, IRON[3])
    frames = ["#3a4f8a", "#a83c32", "#2e7a4e"]
    for k, fx in enumerate((ox - 2, ox + 26, ox + 52)):
        b, bax, bay = bicycle(36, 26)
        a = b.a.copy()
        # recolour the frame
        m = (np.abs(a[..., 0] - C("#3a4f8a")[0]) < 0.02) & (np.abs(a[..., 2] - C("#3a4f8a")[2]) < 0.02)
        a[m, :3] = C(frames[k])[:3]
        m2 = (np.abs(a[..., 0] - C("#5671b0")[0]) < 0.02) & (np.abs(a[..., 2] - C("#5671b0")[2]) < 0.02)
        a[m2, :3] = C(shade(frames[k], 0.25))[:3]
        cv.paste(a, fx, base - bay)
    # a basket on the first bike, a U-lock on the last
    cv.rect(ox + 24, base - 26, 8, 5, OUT); cv.rect(ox + 25, base - 25, 6, 3, WOOD[4])
    cv.rect(ox + 70, base - 18, 5, 2, "#e0b23a"); cv.vline(ox + 70, base - 22, 4, "#e0b23a"); cv.vline(ox + 74, base - 22, 4, "#e0b23a")
    return cv, ox + w // 2, base


def bins(seed=0):
    """Three bins in a row: compost, recycling, landfill."""
    from lib_farrand import wheelie_bins
    cv = Canvas(66, 32, seed=seed)
    ground_shadow(cv, 33, 29, 30, 2)
    wheelie_bins(cv, 3, 29)
    return cv, 33, 29
