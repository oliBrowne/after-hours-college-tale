"""Broadway underpass (U08): the little Broadway & Euclid bike/pedestrian underpass by the UMC.
The multi-use path comes down a ramp from the Hill side (left), runs sunk between sandstone and
form-liner retaining walls, ducks under Broadway's short road bridge (the vertical strip of road in
the middle, an occluder, so people walking under it disappear) and climbs out toward the UMC (right).
Above the back wall is street level at night: the back of a Hill building, an oak and a pine, a
lawn lamp, Broadway's street sign; on the right the UMC's sandstone and red-tile corner. Walt has
made camp against the back wall just west of the bridge: patched dome tent, flattened cardboard,
his lantern, a milk crate with a radio mid-repair, a shopping cart and a stack of boxes. A small
Flatirons mural is painted on the east wall. Cars' lights come and go on the bridge."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import light_pool, ashlar_wall, sidewalk, LEAVES
from facade import roof_tiles, cornice, window, wall_lantern, brick_wall, SANDSTONE, TRIM
from props import lamp_post, shrub, grass_tuft, MUM
from midlib import sprite_from_cell
import lib_eng as E

ROOM = "U08"
W, H = 640, 360
INK = "#171a2b"
SHADOW = "#0d0b16"
FLOOR = 166                 # foot of the back (north) retaining wall
CAP = 86                    # top of the back wall where the path is deepest
WEST_RAMP = (150, 124)      # west of x 150 the wall shrinks; at the screen edge its cap is at y 124
EAST_RAMP = (598, 114)      # east of x 598 likewise, toward the UMC
DECK = (372, 500)           # Broadway's bridge: the vertical strip of road
PARA = 10                   # parapet width on each side of the deck
BRIDGE_N = 80               # north end of the bridge (end piers, expansion joint)
OCC_TOP = 108               # the deck occluder starts here; above it the cars' lights can show
FRONT = 340                 # cap of the front (south) retaining wall
FRONT_TOP = 322             # top of the front railing (front occluder starts here)
LAMPS = (360, 584)          # wall lights (placements 7 and 8), painted into the wall
CRATE = (338, 204)          # Walt's crate and radio (placement 2)
DIAL = (22, 9)              # the radio dial's needle in the crate sprite
MURAL = (514, 110, 72, 42)  # x, y, w, h of the Flatirons mural on the east wall
PILASTERS = (96, 236)
BRIDGE_LAMPS = ((377, 324), (495, 206))   # heritage lamps on the parapets (anchor = foot)
SB_LANE, NB_LANE = 414, 458               # lane centres: southbound (down), northbound (up)

STONE = ["#3a2c31", "#5b4644", "#8a6e60", "#9a7c6b", "#b49481", "#cdb099"]   # U02 terrace sandstone
STONE_DK = ["#2a2026", "#3e3034", "#5b4644", "#6a5450", "#7a6258", "#8a6e60"]
FORM = ["#2c282e", "#3e383c", "#514948", "#5e5552", "#6a605b", "#776b64", "#85786e"]   # warm form-liner concrete
PATH = ["#25232b", "#353239", "#46424a", "#58535a", "#66606a", "#716b74", "#7c7680", "#8a8490"]
CONC = E.CONC
TARP = ["#1a2a4a", "#24386a", "#30508e", "#4068a8", "#5a84c0"]
NYLON = ["#1e2a22", "#2a3a2c", "#3a4e38", "#4e6648", "#66805a", "#86a070"]
CARD = ["#4a3620", "#6a4e2e", "#8a6a3c", "#a8844e", "#c4a066", "#dcc088"]
RUST = ["#2a1a16", "#4a2a20", "#6e3e28", "#94562e"]
WIRE = ["#2a2e3a", "#4a5060", "#6e7688", "#98a0b0"]
IRONC = ["#14141e", "#22222e", "#34344a", "#4e4e66", "#6c6c88"]


def cap_y(x):
    """Screen y of the back wall's cap at column x (lower toward both ends, where the path ramps up)."""
    if x < WEST_RAMP[0]:
        return int(round(WEST_RAMP[1] + (CAP - WEST_RAMP[1]) * x / WEST_RAMP[0]))
    if x > EAST_RAMP[0]:
        return int(round(CAP + (EAST_RAMP[1] - CAP) * (x - EAST_RAMP[0]) / (W - 1 - EAST_RAMP[0])))
    return CAP


def on_deck(x):
    return DECK[0] <= x < DECK[1]


# ---------------------------------------------------------------- street level (above the walls)
def paint_street_level(bg):
    """Night sky, the Hill side (building back, trees, lawn, lamp) and the UMC corner."""
    stars = E.night_sky(bg, 0, 0, W, 64, seed=31, stars=70, horizon=80)
    E.tree_mass(bg, 110, 352, 60, 30, seed=5)
    E.tree_mass(bg, 506, 540, 60, 34, seed=9)
    hill_back(bg)
    umc_corner(bg)
    # lawns at street level, behind the railings
    E.put_rgb(bg, 0, 56, E.grass_np(356, 80, seed=5))
    E.put_rgb(bg, 518, 58, E.grass_np(122, 70, seed=6))
    bg.hline(118, 56, 238, C("#0d0b16", 0.35))
    # campus flagstone walks behind the railings, joining Broadway's sidewalks
    E.put_rgb(bg, 0, 58, E.flagstone_np(356, 12, seed=4))
    E.put_rgb(bg, 518, 60, E.flagstone_np(122, 11, seed=5))
    for (x0, y0, w) in ((0, 58, 356), (518, 60, 122)):
        bg.hline(x0, y0, w, C(SHADOW, 0.4)); bg.hline(x0, y0 + 11 + (1 if x0 == 0 else 0), w, C("#566d4a", 0.6))
    # fallen oak leaves on the lawn and the walk
    rng = np.random.default_rng(16)
    for _ in range(70):
        lx, ly = int(rng.normal(170, 40)), int(rng.normal(74, 9))
        if 0 <= lx < 352 and 56 < ly < cap_y(max(0, min(W - 1, lx))):
            c = LEAVES[int(rng.integers(len(LEAVES)))]
            bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
    # Hill trees: an autumn oak and a pine
    oak = sprite_from_cell(5, height=96, colors=36)
    bg.paste(oak, 116, 66 - oak.shape[0])
    pine = sprite_from_cell(6, height=88, colors=32)
    bg.paste(pine, 214, 68 - pine.shape[0])
    for (cx, cy, rx) in ((168, 66, 30), (246, 68, 22)):
        light_pool(bg, cx, cy, rx, 4, color="#0d0b16", strength=0.5, steps=2)
    # the Hill lawn lamp
    lp, ax, ay = lamp_post(60)
    bg.paste(lp, 300 - ax, 78 - ay)
    light_pool(bg, 300, 80, 34, 7, strength=0.22)
    # sidewalks along Broadway on both sides, with kerbs
    for (sx, sw, sh, seed) in ((352, 20, CAP + 6, 12), (500, 18, EAST_RAMP[1], 13)):
        E.put_rgb(bg, sx, 0, E.conc_slabs_np(sw, sh, slab=sw, row=12, seed=seed, pal=PATH, base=3))
    bg.vline(370, 0, CAP + 6, "#8a8a96"); bg.vline(371, 0, CAP + 6, "#5a5662")
    bg.vline(500, 0, EAST_RAMP[1], "#5a5662"); bg.vline(501, 0, EAST_RAMP[1], "#8a8a96")
    # Broadway's street sign at the corner
    street_sign(bg, 364, 76, "BROADWAY")
    # shrubs along the top of the back wall
    rng = np.random.default_rng(14)
    x = 4
    while x < W:
        if 350 <= x < 520:
            x = 520 if x < 520 else x
        w = int(rng.integers(16, 26)); h = int(rng.integers(10, 16))
        top = cap_y(min(W - 1, x + w // 2))
        bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None),
                 x, top - h + 3)
        x += w - 4 + int(rng.integers(0, 10))
    return stars


def hill_back(bg):
    """The back corner of a Hill building: brick, a lit kitchen window, a vent, a downpipe, a dumpster."""
    x0, x1, base = 0, 112, 56
    brick_wall(bg, x0, 0, x1 - x0, base, seed=4)
    bg.rect(x0, base - 5, x1 - x0, 5, "#4a4048"); bg.hline(x0, base - 5, x1 - x0, "#6a5e64")
    # corner: a slim shadowed return and the ink edge
    bg.rect(x1 - 5, 0, 5, base, "#3a1f22"); bg.vline(x1, 0, base, INK)
    window(bg, 14, 8, 22, 22, lit=True, seed=3, curtain="#7e3a30")
    window(bg, 52, 8, 14, 22, lit=False, seed=4)
    # vent and its grille
    bg.rect(80, 10, 12, 8, "#4a4e5e"); bg.hline(80, 10, 12, "#6e7488")
    for yy in (12, 14, 16):
        bg.hline(81, yy, 10, "#2a2e3a")
    # downpipe with brackets
    bg.rect(101, 0, 3, base - 2, "#3a3e4e"); bg.vline(101, 0, base - 2, "#5e6478")
    for yy in range(6, base, 14):
        bg.rect(100, yy, 5, 2, "#22252f")
    wall_lantern(bg, 46, 32)
    E.dumpster(bg, 50, 30, w=46, h=26)


def umc_corner(bg):
    """The UMC's south-west corner seen over the east wall: sandstone ashlar, red tile eave, lit windows."""
    x0, x1, base = 532, 640, 58
    roof_tiles(bg, x0 - 4, 0, x1 - x0 + 4, 7, seed=6)
    ashlar_wall(bg, x0, 10, x1 - x0, base - 10, SANDSTONE, course=5, seed=7, cap=False)
    cornice(bg, x0 - 3, 9, x1 - x0 + 3)
    for k, qy in enumerate(range(17, base - 6, 6)):
        qw = 7 if k % 2 == 0 else 5
        bg.rect(x0, qy, qw, 5, TRIM[2]); bg.hline(x0, qy, qw, TRIM[4]); bg.hline(x0, qy + 4, qw, TRIM[0])
    bg.vline(x0 - 1, 9, base - 9, INK)
    for i, wx in enumerate((548, 580, 612)):
        window(bg, wx, 30, 14, 16, lit=(i != 1), arch=True, seed=50 + i, curtain="#7e3a30")
    bg.rect(x0, base - 6, x1 - x0, 6, TRIM[1]); bg.hline(x0, base - 6, x1 - x0, TRIM[3])
    bg.hline(x0, base, x1 - x0, C(SHADOW, 0.5))
    wall_lantern(bg, 568, 22)
    # warm spill from the windows onto the lawn
    for wx in (555, 619):
        light_pool(bg, wx, 64, 16, 4, strength=0.2)


def street_sign(bg, px, base, label):
    """A green street-name blade on a post (at street level, so it is background)."""
    top = base - 44
    bg.rect(px - 1, top, 3, base - top, "#3a3e4e"); bg.vline(px - 1, top, base - top, "#5e6478")
    tw = text_width(label)
    sx = px - tw - 8
    bg.rect(sx - 1, top - 1, tw + 10, 13, INK)
    bg.rect(sx, top, tw + 8, 11, "#2a6a4a"); bg.hline(sx, top, tw + 8, "#3e8a60")
    text(bg, label, sx + 4, top + 1, "#e8e4d8")
    bg.rect(px - 2, top - 2, 5, 2, "#3a3e4e")


def paint_railing(bg, xs, top_of):
    """Iron railing: a top rail, a mid rail and posts, following the cap line given by top_of(x)."""
    for x in xs:
        c = top_of(x)
        bg.px(x, c - 14, IRONC[3]); bg.px(x, c - 13, IRONC[1])
        bg.px(x, c - 8, IRONC[2])
        if x % 10 == 3:
            bg.rect(x, c - 13, 2, 13, IRONC[1]); bg.px(x, c - 13, IRONC[4])
            bg.px(x + 1, c - 1, IRONC[0])
        elif x % 10 == 8:
            bg.vline(x, c - 13, 13, IRONC[2])


# ---------------------------------------------------------------- the retaining walls
def form_liner(cv, x, y, w, h, seed=0):
    """Fractured-rib form-liner concrete: vertical ribs, each broken into segments of its own length."""
    rng = np.random.default_rng(seed)
    prof = [1, 4, 5, 4, 3]           # tone per column of a 5px rib: groove, lit face, crest, shade
    for rib in range(x // 5, (x + w) // 5 + 1):
        yy = y - int(rng.integers(0, 10))
        while yy < y + h:
            seg = int(rng.integers(5, 16))
            off = int(rng.choice([-1, 0, 0, 1]))
            for k in range(5):
                xx = rib * 5 + k
                if x <= xx < x + w:
                    t = int(np.clip(prof[k] + (off if k else 0), 0, len(FORM) - 1))
                    cv.rect(xx, max(y, yy), 1, min(seg, y + h - max(y, yy)), FORM[t])
            if y <= yy + seg < y + h:
                cv.rect(rib * 5 + 1, yy + seg, 4, 1, FORM[2])
            yy += seg
    cv.hline(x, y, w, FORM[1]); cv.hline(x, y + h - 1, w, FORM[0])


def quoins(cv, x, y, w, h, seed=0, flip=False):
    """Sandstone blocks stacked in alternating lengths (pilasters and the abutment corners)."""
    k = 0
    for qy in range(y, y + h, 8):
        qh = min(8, y + h - qy)
        qw = w if k % 2 == 0 else w - 3
        qx = x + (w - qw if flip else 0)
        tone = STONE[3] if k % 2 == 0 else STONE[4]
        cv.rect(qx, qy, qw, qh, STONE[1])
        cv.rect(qx, qy, qw - 1, qh - 1, tone)
        cv.hline(qx, qy, qw - 1, shade(tone, 0.08))
        cv.px(qx + 2 + (k * 5) % max(1, qw - 4), qy + 3, shade(tone, -0.1))
        k += 1


def back_wall(bg):
    """The north retaining wall: sandstone coping, fractured-rib form liner, a coursed sandstone
    band, a rough plinth, pilasters; the cap steps down toward both ramps."""
    face = Canvas(W, FLOOR)
    form_liner(face, 0, 80, W, 40, seed=3)
    face.hline(0, 120, W, FORM[0])
    ashlar_wall(face, 0, 121, W, 33, STONE, course=6, seed=4, cap=False)
    ashlar_wall(face, 0, 154, W, 12, STONE_DK, course=11, seed=5, cap=False)
    face.hline(0, 153, W, STONE[5])
    for px in PILASTERS:
        quoins(face, px, 80, 12, 74, seed=px)
    # graffiti tags on the form liner, and a paste-up poster near the camp
    paint_graffiti(face)
    # the abutment corners where the walls meet the bridge, and a slot of the lit tunnel inside
    quoins(face, DECK[0] - 16, 80, 12, 86, flip=False)
    quoins(face, DECK[1] + 4, 80, 12, 86, flip=True)
    paint_mural(face)
    for x in range(W):
        if on_deck(x):
            continue
        c = cap_y(x)
        bg.a[c + 5:FLOOR, x] = face.a[c + 5:FLOOR, x]
        # coping: lit top, joints every 24px, a shadow line under the nose
        joint = (x % 24) == 0
        bg.px(x, c, STONE[5] if not joint else STONE[3])
        for yy in range(c + 1, c + 4):
            bg.px(x, yy, STONE[2] if joint else STONE[4] if yy < c + 3 else STONE[3])
        bg.px(x, c + 4, STONE[1])
        bg.px(x, c + 5, C(SHADOW, 0.5)); bg.px(x, c + 6, C(SHADOW, 0.25))
    # the wall foot meets the floor
    bg.hline(0, FLOOR - 1, W, C(SHADOW, 0.45))


def paint_graffiti(cv):
    """A few spray tags on the form liner (lines, not speckle) and a half-torn paste-up."""
    rng = np.random.default_rng(12)
    for (x, y, col, n) in [(126, 98, "#c84a6a", 22), (300, 104, "#4ab0a8", 18), (610, 112, "#e0a040", 10)]:
        px, py = x, y
        for i in range(n):
            cv.rect(px, py, 2, 2, C(col, 0.75))
            px += int(rng.choice([1, 2, 2, 3])); py += int(rng.choice([-2, -1, 0, 1, 2]))
            py = min(max(py, y - 5), y + 6)
        cv.hline(x, y + 9, n * 2, C(col, 0.45))
    # paste-up poster, half torn: LAST LIGHT arts night
    cv.rect(176, 110, 24, 32, "#d8ccb0"); cv.rect(176, 110, 24, 2, "#b8a888")
    cv.rect(179, 114, 18, 11, "#3a2a5a"); cv.rect(184, 117, 8, 5, "#f6cf7a")
    for yy in (128, 132, 136):
        cv.hline(179, yy, 16 if yy != 136 else 9, "#6a5a4a")
    cv.poly([(192, 142), (200, 132), (200, 142)], STONE[3])


def paint_mural(cv):
    """The Flatirons at dusk, rollered onto a rendered panel set into the east wall."""
    x, y, w, h = MURAL
    cv.rect(x - 3, y - 3, w + 6, h + 6, FORM[5]); cv.hline(x - 3, y - 3, w + 6, FORM[6]); cv.hline(x - 3, y + h + 2, w + 6, FORM[2])
    bands = ["#2c2450", "#4a3068", "#7a3e72", "#b0506a", "#d8705a", "#eea05a"]
    for yy in range(h):
        cv.hline(x, y + yy, w, bands[min(len(bands) - 1, int(yy / h * 1.4 * len(bands)))])
    cv.ellipse(x + 48, y + 9, 13, 13, "#f8d07a"); cv.ellipse(x + 50, y + 11, 9, 9, "#fce6a6")
    # three slabs, back to front, with their strata
    for (px, top, col, hi) in [(12, 14, "#3a2a4a", "#5a3e5e"), (34, 8, "#4a2e46", "#7a4658"), (58, 18, "#3e2840", "#6a3c52")]:
        cv.poly([(x + px - 16, y + h), (x + px, y + top), (x + px + 18, y + h)], col)
        for k in range(0, h - top, 4):
            cv.hline(x + px - 1 - k // 4, y + top + k, 2 + k // 3, hi)
    cv.rect(x, y + h - 6, w, 6, "#24303a")
    for px in range(x + 2, x + w - 2, 4):
        hh = 3 + (px * 7) % 4
        cv.poly([(px - 2, y + h - 5), (px + 1, y + h - 5 - hh), (px + 3, y + h - 5)], "#1a2630")
    for px in range(x, x + w, 7):
        cv.vline(px + 3, y + h, 1 + (px % 3), C("#d8705a", 0.6))
    cv.hline(x + w - 14, y + h - 3, 10, "#e8dcc4")
    cv.rect(x - 4, y - 4, w + 8, 1, C(SHADOW, 0.5)); cv.rect(x - 4, y + h + 3, w + 8, 1, C(SHADOW, 0.5))


# ---------------------------------------------------------------- the path
def paint_floor(bg):
    """Concrete path slabs, a dashed centre stripe, bike stencils and arrows, ramps at both ends."""
    rgb = E.conc_slabs_np(W, FRONT - FLOOR, slab=48, row=28, seed=21, pal=PATH, base=4)
    E.put_rgb(bg, 0, FLOOR, rgb)
    bg.rect(0, FLOOR, W, 5, C(SHADOW, 0.4)); bg.rect(0, FLOOR + 5, W, 3, C(SHADOW, 0.2))
    # centre stripe, edge line and stencils
    for x in range(6, W, 24):
        bg.rect(x, 252, 13, 2, C("#e0b84a", 0.75))
    E.worn_line(bg, 0, 324, W, 1, "#d8d4cc", alpha=0.45, seed=4)
    stencil_bike(bg, 150, 296)
    arrow_floor(bg, 196, 292, right=True)
    stencil_bike(bg, 560, 232)
    arrow_floor(bg, 516, 228, right=False)
    # ramps rising to street level at both ends: grooved concrete, lighter as it climbs
    for (x0, x1, d) in ((0, 34, -1), (606, W, 1)):
        for k, (a, b) in enumerate(((0, 12), (12, 24), (24, 34))):
            xa = x0 + a if d > 0 else x1 - b
            bg.rect(xa, FLOOR + 2, b - a, FRONT - FLOOR - 2, C(PATH[6 - k], 0.35))
        for x in range(x0 + 1, x1, 3):
            bg.vline(x, FLOOR + 6, FRONT - FLOOR - 8, C(PATH[2], 0.5))
        edge = x0 + 34 if d < 0 else x1 - 34
        bg.vline(edge, FLOOR + 2, FRONT - FLOOR - 2, C(PATH[1], 0.6))
    # drain grate at the wall foot and a puddle holding lamp light
    bg.rect(526, 168, 20, 5, "#1a1a24")
    for x in range(527, 545, 3):
        bg.vline(x, 169, 3, "#3a3a48")
    bg.ellipse(574, 290, 34, 8, "#1c2844"); bg.ellipse(578, 292, 24, 4, "#283a5c")
    bg.hline(584, 293, 10, "#f6cf7a"); bg.hline(587, 294, 5, "#e9a84a")
    # leaves blown down the ramps and under the oak, a wrapper and a bottle cap near the cart
    rng = np.random.default_rng(23)
    for (cx, cy, r, n) in [(16, 300, 40, 36), (W - 16, 230, 40, 30), (170, 214, 44, 16), (300, 320, 50, 10)]:
        for _ in range(n):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
            lx, ly = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.6)
            if 0 <= lx < W and FLOOR + 3 < ly < FRONT - 2 and not on_deck(lx):
                c = LEAVES[int(rng.integers(len(LEAVES)))]
                bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
    bg.rect(150, 230, 4, 2, "#c84a4a"); bg.px(232, 312, "#c8c8d0")


def stencil_bike(bg, x, y):
    """A bike-path stencil (side view) in worn white paint."""
    c = C("#d8d4cc", 0.5)
    for cx in (x - 8, x + 8):
        for (dx, dy) in [(-3, -1), (-3, 0), (-3, 1), (3, -1), (3, 0), (3, 1), (-2, -2), (-1, -3), (0, -3), (1, -3),
                         (2, -2), (-2, 2), (-1, 3), (0, 3), (1, 3), (2, 2)]:
            bg.px(cx + dx, y + dy, c)
    for (a, b) in [((x - 8, y), (x - 3, y - 6)), ((x - 3, y - 6), (x + 8, y)), ((x - 8, y), (x + 1, y)),
                   ((x + 1, y), (x - 3, y - 6)), ((x + 5, y - 7), (x + 8, y)), ((x - 5, y - 7), (x - 1, y - 7))]:
        bg.line(a[0], a[1], b[0], b[1], c)


def arrow_floor(bg, x, y, right=True):
    c = C("#d8d4cc", 0.45)
    d = 1 if right else -1
    bg.rect(x - 8 if right else x, y, 8, 2, c)
    for k in range(4):
        bg.vline(x + d * k, y - 3 + k, 8 - 2 * k, c)


def portal_shadows(bg):
    """The bridge's shadow and the dark tunnel mouths on the floor and wall either side of the deck."""
    for (edge, d) in ((DECK[0], -1), (DECK[1], 1)):
        for (w, a) in ((56, 0.22), (36, 0.26), (20, 0.32), (8, 0.42)):
            x = edge - w if d < 0 else edge
            bg.rect(x, FLOOR - 1, w, FRONT - FLOOR + 1, C(SHADOW, a))
            bg.rect(x, CAP + 5, w, FLOOR - CAP - 6, C(SHADOW, a * 0.6))
        # a sliver of the tunnel's inner wall, lit by its own fixture
        sx = edge - 4 if d < 0 else edge
        bg.rect(sx, CAP + 7, 4, FLOOR - CAP - 7, "#1a1626")
        bg.rect(sx, 108, 4, 44, "#2e2430"); bg.rect(sx, 116, 4, 28, "#4a3630"); bg.rect(sx, 122, 4, 16, "#6e4e32")
        bg.rect(sx + 1, 126, 2, 5, "#f6cf7a"); bg.px(sx + 1, 125, "#2a2a34"); bg.px(sx + 2, 125, "#2a2a34")
        # warm light from the tunnel's fixtures spilling out of the mouth, along the floor
        x = edge - 4 if d < 0 else edge
        for (yy, hh, a) in ((214, 72, 0.12), (228, 44, 0.14), (240, 20, 0.16)):
            bg.rect(x, yy, 4, hh, C("#e9a84a", a))


def front_strip():
    """The front (south) retaining wall seen from above: its railing, coping, and the lawn beyond.
    Painted on its own canvas (rows FRONT_TOP..H) so it can be both background and occluder."""
    cv = Canvas(W, H - FRONT_TOP)
    f = FRONT - FRONT_TOP
    E.put_rgb(cv, 0, f + 6, E.grass_np(W, H - FRONT - 6, seed=8))
    rng = np.random.default_rng(15)
    x = -6
    while x < W:
        w = int(rng.integers(14, 22)); h = int(rng.integers(9, 13))
        cv.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None),
                 x, f + 8 + int(rng.integers(0, 5)))
        x += w - 3 + int(rng.integers(0, 8))
    # coping seen from above: shadowed inner lip, lit top, outer nose
    cv.rect(0, f - 1, W, 1, C(SHADOW, 0.6))
    cv.rect(0, f, W, 6, STONE[3]); cv.hline(0, f, W, STONE[5]); cv.hline(0, f + 1, W, STONE[4])
    cv.hline(0, f + 5, W, STONE[1]); cv.hline(0, f + 6, W, C(SHADOW, 0.5))
    for x in range(0, W, 24):
        cv.vline(x, f + 1, 4, STONE[2])
    # iron railing on the coping
    for x in range(W):
        cv.px(x, f - 14, IRONC[3]); cv.px(x, f - 13, IRONC[1]); cv.px(x, f - 7, IRONC[2])
        if x % 10 == 3:
            cv.rect(x, f - 13, 2, 14, IRONC[1]); cv.px(x, f - 13, IRONC[4]); cv.px(x, f + 1, IRONC[0])
        elif x % 10 == 8:
            cv.vline(x, f - 13, 13, IRONC[2])
    # leave the deck to the bridge
    cv.a[:, DECK[0]:DECK[1]] = 0
    return cv


# ---------------------------------------------------------------- the bridge
def paint_bridge(bg):
    """Broadway's short bridge over the path: asphalt, bike lanes, the double yellow, sandstone
    parapets with iron rails, end piers and an expansion joint where the deck begins."""
    x0, x1 = DECK
    rx0, rx1 = x0 + PARA, x1 - PARA
    E.put_rgb(bg, x0, 0, E.asphalt_np(x1 - x0, H, seed=17))
    # tar snakes
    for (sx, sy, n) in ((402, 30, 60), (466, 150, 90), (420, 262, 70)):
        E.tar_snake(bg, sx, sy, n, seed=sx, vertical=True)
    # bike lanes, lane lines and the double yellow centre line
    for lx in (rx0 + 13, rx1 - 14):
        E.worn_line(bg, lx, 0, 2, H, "#d8d4cc", alpha=0.7, seed=lx)
    cx = (rx0 + rx1) // 2
    for lx in (cx - 3, cx + 1):
        E.worn_line(bg, lx, 0, 2, H, "#e0b84a", alpha=0.85, seed=lx + 1, wear=0.1)
    for (bx, by) in ((rx0 + 6, 150), (rx1 - 7, 270), (rx0 + 6, 40)):
        bike_v(bg, bx, by)
    # kerbs north of the bridge, then parapets along both edges of the deck
    for (px, flip) in ((x0, False), (rx1, True)):
        bg.rect(px, 0, PARA, BRIDGE_N, "#5a5662")
        bg.vline(px if not flip else px + PARA - 1, 0, BRIDGE_N, "#9a9aa4")
        bg.vline(px + PARA - 1 if not flip else px, 0, BRIDGE_N, C(SHADOW, 0.4))
        parapet(bg, px, BRIDGE_N, H - BRIDGE_N, flip)
        # piers where the parapet meets the back and front walls
        for py in (BRIDGE_N - 4, FRONT - 4):
            pier(bg, px - 2, py, PARA + 4)
    # expansion joints across the road where the deck begins and ends
    for jy in (BRIDGE_N + 6, FRONT + 2):
        bg.rect(rx0, jy, rx1 - rx0, 4, "#3a3a46"); bg.hline(rx0, jy, rx1 - rx0, "#6a6a78")
        bg.hline(rx0, jy + 3, rx1 - rx0, "#1e1e28")
        for x in range(rx0 + 3, rx1, 9):
            bg.rect(x, jy + 1, 4, 2, "#4e4e5c")
    # inner shadows cast by the parapets on the road
    bg.rect(rx0, BRIDGE_N + 10, 2, H, C(SHADOW, 0.3)); bg.rect(rx1 - 2, BRIDGE_N + 10, 2, H, C(SHADOW, 0.3))
    # the lamps' pools on the road
    for (lx, ly) in BRIDGE_LAMPS:
        light_pool(bg, lx + (12 if lx < cx else -12), ly - 4, 30, 9, strength=0.24)


def parapet(bg, x, y, h, flip):
    """A low sandstone parapet seen from above: outer face in shadow, a lit coping with block joints,
    an iron rail with square posts along its top."""
    def col(i):          # column i counted from the outer (path) side
        return x + i if not flip else x + PARA - 1 - i
    tones = [INK, STONE[1], STONE[2], STONE[5], STONE[4], STONE[4], STONE[4], STONE[3], STONE[3], STONE[1]]
    for i, t in enumerate(tones):
        bg.vline(col(i), y, h, t)
    for yy in range(y + 8, y + h, 16):
        for i in range(1, PARA - 1):
            bg.px(col(i), yy, STONE[1] if i > 2 else STONE[0])
    # rail on the coping, with square posts and their little shadows
    bg.vline(col(5), y, h, IRONC[2])
    for yy in range(y + 4, y + h, 10):
        bg.rect(min(col(4), col(6)), yy, 3, 3, IRONC[1]); bg.px(col(5), yy, IRONC[4])
        bg.px(col(6) if not flip else col(6), yy + 3, C(SHADOW, 0.5))


def pier(bg, x, y, w):
    """A squat sandstone pier with a capstone, seen from above and a little from the front."""
    bg.rect(x - 1, y - 1, w + 2, 15, INK)
    bg.rect(x, y, w, 9, STONE[4]); bg.hline(x, y, w, STONE[5]); bg.rect(x + 2, y + 2, w - 4, 5, STONE[3])
    bg.hline(x, y + 8, w, STONE[1])
    bg.rect(x, y + 9, w, 4, STONE[2]); bg.hline(x + 1, y + 10, w - 2, STONE[3])
    bg.hline(x - 1, y + 14, w + 2, C(SHADOW, 0.5))


def bike_v(bg, x, y):
    """Bike-lane symbol painted along a north-south lane (wheels stacked)."""
    c = C("#d8d4cc", 0.55)
    for cy in (y - 6, y + 6):
        for (dx, dy) in [(-1, -3), (0, -3), (1, -3), (-3, -1), (-3, 0), (-3, 1), (3, -1), (3, 0), (3, 1),
                         (-2, -2), (2, -2), (-2, 2), (2, 2), (-1, 3), (0, 3), (1, 3)]:
            bg.px(x + dx, cy + dy, c)
    bg.line(x, y - 6, x, y + 6, c); bg.line(x, y - 2, x + 3, y + 2, c)
    for k in range(3):
        bg.hline(x - k, y - 14 + k, 1 + 2 * k, c)
    bg.vline(x, y - 11, 3, c)


def bridge_lamps():
    """Heritage lamps on the parapets, on their own layer (they go into the deck occluder too)."""
    cv = Canvas(W, H)
    for (lx, ly) in BRIDGE_LAMPS:
        lp, ax, ay = lamp_post(58)
        cv.paste(lp, lx - ax, ly - ay)
        E.stepped_glow(cv, lx, ly - ay + 11, 9, 7, E.WARM[3], 0.2, 2)
    return cv


def paint_camp_floor(bg):
    """Flat things of the camp: cardboard sheets in front of the tent, light pools."""
    rng = np.random.default_rng(31)
    for (x, y, w, h, t) in [(214, 188, 70, 20, 3), (244, 196, 52, 14, 4), (150, 200, 40, 10, 2)]:
        bg.poly([(x, y + 2), (x + w, y), (x + w + 2, y + h), (x - 2, y + h - 1)], CARD[t])
        bg.hline(x, y + 2, w, CARD[t + 1]); bg.hline(x - 1, y + h - 1, w + 2, CARD[t - 2])
        for _ in range(3):
            fx = x + int(rng.integers(6, w - 6))
            bg.vline(fx, y + 3, h - 4, CARD[t - 1])
    light_pool(bg, 298, 210, 52, 16, strength=0.26)
    for lx in LAMPS:
        light_pool(bg, lx, 184, 46, 16, strength=0.2)


# ---------------------------------------------------------------- props
def outline(cv):
    cv.outline_outside(INK)
    return cv


def dome_tent():
    """Patched dome tent, a blue tarp over the back half, door flap tied open, sleeping bag inside."""
    w, h = 92, 56
    cv = Canvas(w, h)
    cx, by = 46, 52
    # dome body
    for yy in range(h):
        pass
    cv.ellipse(4, 8, 84, 88, NYLON[3])
    cv.rect(0, by + 1, w, h - by - 1, C("#000000", 0))
    cv.a[by + 1:] = 0
    # panel seams (poles) and shading
    for k, x in enumerate((20, 46, 72)):
        for yy in range(10, by):
            dx = int((x - cx) * (1 - ((by - yy) / (by - 8)) ** 2) ** 0.5) if x != cx else 0
            cv.px(cx + dx, yy, NYLON[1])
    cv.ellipse(10, 14, 30, 30, C(NYLON[4], 0.6))
    cv.rect(60, 14, 30, 40, C(NYLON[1], 0.35))
    # tarp over the back half with a sagging edge and bungee hooks
    cv.poly([(8, 30), (30, 10), (64, 8), (86, 26), (88, 40), (70, 34), (50, 38), (28, 34)], TARP[2])
    cv.poly([(30, 10), (64, 8), (60, 14), (34, 16)], TARP[3])
    for (a, b) in [((8, 30), (28, 34)), ((28, 34), (50, 38)), ((50, 38), (70, 34)), ((70, 34), (88, 40))]:
        cv.line(a[0], a[1], b[0], b[1], TARP[1])
    for p in ((8, 30), (50, 38), (88, 40)):
        cv.rect(p[0] - 1, p[1], 2, 3, "#c84a3a")
    # patches (duct tape and a sewn square)
    cv.rect(16, 38, 8, 6, "#9aa0a8"); cv.hline(16, 38, 8, "#c0c4ca"); cv.line(16, 44, 23, 38, "#7a8088")
    cv.rect(66, 40, 9, 8, "#8a5a3a"); cv.rect(67, 41, 7, 6, "#a8744a")
    for k in range(0, 9, 2):
        cv.px(66 + k, 40, "#e6d6b1"); cv.px(66 + k, 47, "#e6d6b1")
    # open door: dark inside, a sleeping bag, the flap tied back
    cv.poly([(34, by), (40, 26), (52, 26), (58, by)], "#141420")
    cv.poly([(38, by), (42, 40), (54, 40), (56, by)], "#7a3a3a")
    cv.hline(42, 42, 12, "#9a4a46"); cv.hline(40, 47, 16, "#5a2a2a")
    cv.poly([(52, 26), (62, 34), (60, by), (58, by)], NYLON[4]); cv.vline(60, 34, by - 34, NYLON[2])
    cv.rect(58, 36, 4, 2, "#d8c088")
    # guy lines and stakes on the ground
    cv.line(4, 46, 0, by, "#a8a8b0"); cv.line(88, 46, 91, by, "#a8a8b0")
    cv.hline(0, by, 3, "#6a6a72"); cv.hline(89, by, 3, "#6a6a72")
    cv.hline(6, by, 80, NYLON[0])
    return outline(cv), cx, by


def lantern():
    """Walt's hurricane lantern, lit."""
    cv = Canvas(14, 20)
    cv.rect(4, 0, 6, 2, "#2a2a34"); cv.px(7, 0, "#4a4a58")
    cv.rect(3, 2, 8, 2, "#3a3a46"); cv.hline(3, 2, 8, "#5a5a68")
    cv.rect(3, 4, 8, 10, "#e9a84a"); cv.rect(4, 5, 6, 8, "#f6cf7a"); cv.rect(6, 7, 2, 4, "#fff0c4")
    cv.vline(3, 4, 10, "#2a2a34"); cv.vline(10, 4, 10, "#2a2a34")
    cv.rect(2, 14, 10, 4, "#3a3a46"); cv.hline(2, 14, 10, "#5a5a68"); cv.hline(2, 17, 10, "#22222c")
    cv.line(2, 4, 7, -1, "#2a2a34"); cv.line(11, 4, 7, -1, "#2a2a34")
    return outline(cv), 7, 18


def crate_radio(dial_hole=False):
    """A milk crate with a valve radio on top, back panel off, antenna up. dial_hole leaves the
    dial's needle pixel open so the room's twinkle layer, painted under the prop, shows through."""
    cv = Canvas(32, 36)
    # crate
    cv.rect(2, 18, 28, 16, "#2a5a8a"); cv.hline(2, 18, 28, "#3e78ae"); cv.hline(2, 33, 28, "#1a3a5e")
    for x in range(5, 29, 5):
        cv.rect(x, 21, 3, 10, "#1a3a5e")
    cv.rect(10, 22, 12, 3, "#14284a")
    # radio: wooden cabinet, cloth grille, dial
    cv.rect(4, 6, 24, 13, "#6a4428"); cv.hline(4, 6, 24, "#8e5e36"); cv.hline(4, 18, 24, "#3e2616")
    cv.rect(6, 8, 11, 9, "#c8b48a")
    for y in range(9, 17, 2):
        cv.hline(6, y, 11, "#a89470")
    cv.rect(19, 8, 7, 4, "#e8dcb0"); cv.px(22, 9, "#c84a3a"); cv.hline(19, 11, 7, "#a89470")
    cv.rect(20, 14, 2, 2, "#2a1a10"); cv.rect(24, 14, 2, 2, "#2a1a10")
    # a valve leaning against it and the antenna
    cv.rect(28, 12, 3, 6, "#c8d8e0"); cv.px(29, 13, "#ffffff")
    cv.line(24, 6, 30, 0, "#a8a8b0")
    outline(cv)
    if dial_hole:
        cv.a[DIAL[1], DIAL[0]] = 0
    return cv, 16, 34


def shopping_cart():
    """A shopping cart full of blankets, bags and a coffee jar."""
    w, h = 56, 46
    cv = Canvas(w, h)
    # contents above the basket rim
    cv.ellipse(6, 2, 22, 18, "#6a3a4a"); cv.ellipse(8, 4, 14, 8, "#8a4e5e")
    cv.ellipse(22, 0, 20, 20, "#2a2a32"); cv.ellipse(25, 3, 9, 6, "#4a4a56")
    cv.rect(38, 4, 9, 13, "#c8b07a"); cv.rect(38, 4, 9, 3, "#3a2a1a"); cv.rect(39, 9, 7, 4, "#8a5a2a")
    cv.ellipse(30, 10, 18, 10, "#d8d0c0"); cv.hline(32, 13, 12, "#a8a090")
    # basket: wire grid, slanted front
    cv.poly([(4, 12), (50, 12), (46, 34), (8, 34)], C(WIRE[1], 0.35))
    for x in range(6, 50, 4):
        cv.line(x, 12, x - 1 if x < 28 else x + 1, 34, WIRE[2])
    for y in range(14, 34, 4):
        cv.hline(5 + (y - 12) // 6, y, 44 - (y - 12) // 3, WIRE[2])
    cv.hline(3, 12, 49, WIRE[3]); cv.hline(7, 34, 40, WIRE[3])
    # handle, frame, wheels
    cv.line(50, 12, 54, 6, WIRE[3]); cv.hline(50, 6, 6, "#c84a3a")
    cv.line(10, 34, 8, 41, WIRE[2]); cv.line(44, 34, 46, 41, WIRE[2]); cv.hline(8, 40, 40, WIRE[2])
    for wx in (7, 46):
        cv.rect(wx - 2, 41, 5, 4, "#1a1a22"); cv.px(wx, 42, "#4a4a56")
    return outline(cv), 28, 44


def box_stack():
    """Two flattened boxes leaning on the wall and an intact box with a blanket folded on it."""
    cv = Canvas(40, 36)
    cv.poly([(2, 34), (6, 2), (20, 4), (18, 34)], CARD[2]); cv.line(6, 2, 2, 34, CARD[1]); cv.vline(12, 6, 26, CARD[1])
    cv.poly([(14, 34), (20, 8), (34, 10), (30, 34)], CARD[3]); cv.vline(25, 12, 20, CARD[2])
    cv.box(8, 18, 28, 16, CARD[3], outline=None)
    cv.hline(8, 25, 28, "#b0a070"); cv.rect(20, 18, 3, 16, "#c8b888")
    cv.rect(10, 15, 24, 4, "#4a6a5a"); cv.hline(10, 15, 24, "#5e8270"); cv.hline(10, 17, 24, "#3a5448")
    text(cv, "UP", 12, 26, C(CARD[0], 0.9))
    return outline(cv), 20, 34


def wall_light(lit=True):
    """A caged sodium light on the wall, anchored at the wall foot below it (placement-style)."""
    cv = Canvas(20, 74)
    cv.rect(6, 0, 8, 3, "#2a2a34")
    cv.rect(4, 3, 12, 9, "#1e1e28")
    cv.rect(5, 4, 10, 7, E.WARM[3] if lit else "#5a5040"); cv.rect(7, 5, 6, 4, E.WARM[4] if lit else "#6a6050")
    for x in (5, 8, 11, 14):
        cv.vline(x, 3, 9, "#2a2a34")
    cv.hline(4, 7, 12, "#2a2a34")
    cv.outline_outside(INK)
    return cv, 10, 72


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=8)
    stars = paint_street_level(bg)
    paint_railing(bg, [x for x in range(W) if not on_deck(x)], cap_y)
    back_wall(bg)
    paint_floor(bg)
    portal_shadows(bg)
    paint_camp_floor(bg)
    # lamp light washing the wall around each fixture, the lantern's glow
    for lx in LAMPS:
        E.stepped_glow(bg, lx, 104, 28, 22, E.WARM[3], 0.16, 3)
    E.stepped_glow(bg, 298, 178, 40, 24, E.WARM[3], 0.14, 3)
    # the caged wall lights are painted into the wall (so the flicker layer shows on them)
    for lx in LAMPS:
        light, ax, ay = wall_light()
        bg.paste(light, lx - ax, FLOOR - ay)
    # the radio dial behind the crate's open pixel
    bg.px(CRATE[0] - 16 + DIAL[0], CRATE[1] - 34 + DIAL[1], "#c84a3a")
    front = front_strip()
    bg.paste(front, 0, FRONT_TOP)
    paint_bridge(bg)
    lamps = bridge_lamps()
    bg.paste(lamps, 0, 0)
    bg.save(os.path.join(out, "background.png"))

    # Occluders: the deck (with its lamps) hides anyone walking under it; the front railing.
    deck = Canvas(W, H - OCC_TOP)
    deck.a[:, DECK[0]:DECK[1]] = bg.a[OCC_TOP:, DECK[0]:DECK[1]]
    deck.paste(lamps.a[OCC_TOP:], 0, 0)
    ys, xs = np.where(deck.a[..., 3] > 0)
    dx0, dx1 = int(xs.min()), int(xs.max()) + 1
    Canvas.save(_crop(deck, dx0, dx1), os.path.join(out, "deck.png"))
    front.save(os.path.join(out, "front-rail.png"))

    props = {}

    def save(index, made, name=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        props[str(index)] = {"texture": res + name, "anchor": [ax, ay]}
        return props[str(index)]

    save(0, dome_tent())
    lamp = save(1, lantern())
    # once Walt is on his feet he carries the lantern
    Canvas(1, 1).save(os.path.join(out, "empty.png"))
    lamp.update({"flag": "imani_joined", "flag_texture": res + "empty.png"})
    save(2, crate_radio(dial_hole=True))
    save(3, shopping_cart())
    save(4, box_stack())

    # Walt sitting on his cardboard (the room NPC uses this until he stands up)
    seated = Canvas(48, 48)
    seated.a = np.array(_walt_seated()).astype(np.float32) / 255
    seated.save(os.path.join(out, "walt-seated.png"))

    def lane(x, y0, y1, colour, period):
        return {"kind": "movers", "from": [x, y0], "to": [x, y1], "count": 2, "period": period,
                "size": [3, 3], "pair": 0, "color": colour, "ease": "in"}

    twinkles = [[s[0], s[1], "c8c0e0", 1] for s in stars[:6]]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [
            {"texture": res + "deck.png", "x": dx0, "y": OCC_TOP, "base": 999},
            {"texture": res + "front-rail.png", "x": 0, "y": FRONT_TOP, "base": 999},
        ],
        "props": props,
        "label_only": [7, 8],
        "fauna": [
            {"kind": "pigeon", "x": 556, "y": 318, "range": 10, "speed": 0.3, "rate": 2.0},
            {"kind": "pigeon", "x": 262, "y": CAP + 2, "range": 6, "speed": 0.24, "rate": 1.6, "flip": True},
            {"kind": "rabbit", "x": 80, "y": 74, "range": 4, "speed": 0.2, "rate": 1.2},
        ],
        "leaves": [[120, 10, 110, 150]],
        "layers": [
            # the wall light by the tunnel mouth buzzes and drops out now and then
            {"kind": "blink", "pattern": "0000000000001010000000000000000011000000", "rate": 9.0,
             "rects": [[LAMPS[0] - 5, 98, 10, 7, "5a5040", 1.0]]},
            # Walt's radio dial glows faintly
            {"kind": "twinkle", "points": [[CRATE[0] - 16 + DIAL[0], CRATE[1] - 34 + DIAL[1], "f6cf7a", 1]], "rate": 0.7, "min": 0.4},
            # street lamps at street level, and a few stars
            {"kind": "twinkle", "points": [[300, 29, "fff0c4", 1], [568, 26, "fff0c4", 1]] + twinkles, "rate": 0.9, "min": 0.5},
            # cars on Broadway: headlights coming south (down), taillights going north (up); they pass
            # on under the deck occluder
            lane(SB_LANE - 4, -6, OCC_TOP + 10, "fff0c4", 9.0),
            lane(SB_LANE + 4, -6, OCC_TOP + 10, "fff0c4", 9.0),
            lane(NB_LANE - 4, OCC_TOP + 10, -6, "ff5a4a", 11.0),
            lane(NB_LANE + 4, OCC_TOP + 10, -6, "ff5a4a", 11.0),
        ],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def _crop(cv, x0, x1):
    out = Canvas(x1 - x0, cv.h)
    out.a = cv.a[:, x0:x1].copy()
    return out


def _walt_seated():
    """Walt sitting against the wall under a plaid blanket (painted over his redrawn front frame;
    the painted PNG is kept beside this script)."""
    from PIL import Image
    return Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "u08_walt_seated.png")).convert("RGBA")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
