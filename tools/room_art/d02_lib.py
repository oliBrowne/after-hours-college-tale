"""Farrand Hall inside (D02 second-floor hallway, D03 lobby + laundry room).

Farrand is a 1950s residence hall: red brick and sandstone. Inside, the halls have a red brick
wainscot under a sandstone chair rail, cream-painted block above, an acoustic-tile ceiling with
frosted drum lights, speckled asphalt-tile linoleum with an oxblood border, birch doors in
teal-painted steel frames. Move-in day: name tags on every door, boxes and carts everywhere.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, ground_shadow, shrub
from facade import BRICK, SANDSTONE, TRIM, brick_wall
from surfaces import light_pool
from lib_eng import micro_text, micro_width, scribble, painted_block, hashn, P, put_rgb, exit_sign, outlet
from lib_umc import soft_ellipse, halo, extinguisher
from lib_oldmain import radiator, cork_surface, notice_paper, night_glass, framed_photo

INK = "#171a2b"
SHADOW = "#0d0b16"
# cream painted block (painted_block: mortar 2, body 4/5, odd 3, lit 6)
FH_BLOCK = ["#3c3330", "#584a42", "#76665a", "#958270", "#a8937c", "#b39e86", "#c6b296", "#d6c4a6"]
FH_BRICK = BRICK
FH_SAND = SANDSTONE
BIRCH = ["#4a2e20", "#6a4430", "#87593c", "#9e6c48", "#b48058", "#c8966a", "#dab080"]
STEEL_T = ["#16222a", "#203238", "#2c4448", "#3c5a5a", "#527470", "#6e9088"]
ACOUSTIC = ["#5e564c", "#8a8070", "#a89c88", "#bcb09a", "#cec2aa"]
LINO_F = ["#6a5c50", "#7c6c5e", "#8a796a", "#968574", "#a29080"]       # field tile (greige)
LINO_G = ["#5e5650", "#6e655e", "#7c7269", "#887e74", "#958a7f"]       # field tile (cooler grey)
LINO_OX = ["#3e2424", "#52302c", "#643a34", "#74443c", "#844e44"]      # oxblood border
CPAPER = ["#e8c24a", "#5cb0a0", "#e07a5a", "#8aa8e0", "#c890d0", "#9ccf6a", "#f2e8d0"]  # construction paper
WARM = ["#7a4a24", "#c47a2c", "#e9a84a", "#f6cf7a", "#fff0c4"]
CARD = ["#5a3e26", "#7a5634", "#9a7046", "#b48856", "#c8a06a", "#dcb880"]   # cardboard
CHROME = ["#3a3c48", "#5a5c6a", "#80828e", "#a8aab4", "#cfd0d8"]

DOOR_W, DOOR_H = 36, 72


def _rng(seed):
    return np.random.default_rng(seed)


# ------------------------------------------------------------------------------------- walls
def acoustic_soffit(cv, x, w, y=0, h=12, seed=0):
    """The edge of the acoustic-tile ceiling: pale pitted tiles in a T-bar grid, a shadow under it."""
    cv.rect(x, y, w, h, ACOUSTIC[3])
    xs = np.arange(x, x + w)
    for yy in range(y, y + h):
        for xx in xs[(hashn(xs, np.full_like(xs, yy), seed) > 0.83)]:
            cv.px(int(xx), yy, ACOUSTIC[2])
        for xx in xs[(hashn(xs, np.full_like(xs, yy), seed + 5) > 0.97)]:
            cv.px(int(xx), yy, ACOUSTIC[1])
    for tx in range(x + (-x % 32), x + w, 32):
        cv.vline(tx, y, h, ACOUSTIC[1]); cv.vline(tx + 1, y, h, ACOUSTIC[4])
    cv.hline(x, y + h - 2, w, "#e2d8c2")          # T-bar edge
    cv.hline(x, y + h - 1, w, ACOUSTIC[0])
    cv.hline(x, y + h, w, C(SHADOW, 0.35))


def hall_wall(cv, x, w, base, top=12, seed=0, rail=44):
    """Cream block above a red brick wainscot with a sandstone chair rail and a rubber cove base."""
    painted_block(cv, x, top, w, base - rail - top, seed=seed, pal=FH_BLOCK)
    # a soft shadow band under the ceiling
    cv.rect(x, top, w, 2, C(SHADOW, 0.22)); cv.rect(x, top + 2, w, 2, C(SHADOW, 0.1))
    ry = base - rail
    cv.rect(x, ry, w, 5, FH_SAND[3]); cv.hline(x, ry, w, FH_SAND[5]); cv.hline(x, ry + 1, w, FH_SAND[4])
    cv.hline(x, ry + 4, w, FH_SAND[1])
    rng = _rng(seed + 9)
    for jx in range(x + int(rng.integers(10, 40)), x + w, int(rng.integers(38, 52))):   # stone joints
        cv.vline(jx, ry + 1, 3, FH_SAND[2])
    brick_wall(cv, x, ry + 5, w, rail - 8, pal=FH_BRICK, seed=seed + 1)
    cv.rect(x, base - 3, w, 3, "#2a2226"); cv.hline(x, base - 3, w, "#433a3c")


def drum_light(cv, cx, y=12, glow=True):
    """Frosted-glass drum fixture hanging from the soffit, warm light washing the wall below it."""
    if glow:
        # a warm wash fanning down the wall under the fixture, in flat steps
        for k, (rx, ry, a) in enumerate(((70, 60, 0.07), (50, 44, 0.07), (32, 28, 0.08), (18, 14, 0.09))):
            soft_ellipse(cv, cx, y + 8, rx, ry, "#f6cf7a", a)
    cv.rect(cx - 2, y - 1, 5, 2, IRON[2])
    cv.rect(cx - 15, y, 31, 11, OUT)
    cv.rect(cx - 14, y + 1, 29, 9, "#f2dfb4"); cv.hline(cx - 14, y + 1, 29, "#fff6dc"); cv.hline(cx - 14, y + 2, 29, "#fffaee")
    cv.hline(cx - 14, y + 6, 29, "#ecd09a"); cv.hline(cx - 14, y + 7, 29, "#e6c48a"); cv.hline(cx - 13, y + 8, 27, "#d6a866")
    cv.rect(cx - 9, y + 3, 6, 2, "#ffffff")
    for k in (-10, 10):                                   # the glass is held by two little screws
        cv.px(cx + k, y + 9, CHROME[2])
    cv.rect(cx - 15, y + 10, 31, 1, CHROME[1]); cv.rect(cx - 2, y + 11, 5, 2, CHROME[3])


def number_plate(cv, x, y, s):
    w = micro_width(s) + 6
    cv.rect(x, y, w, 9, OUT); cv.rect(x + 1, y + 1, w - 2, 7, "#2a2a36"); cv.hline(x + 1, y + 1, w - 2, "#3e3e4e")
    micro_text(cv, s, x + 3, y + 2, "#e8d8a8")
    for k in range(3):                                # braille dots
        cv.px(x + 3 + k * 2, y + 10, "#a8a6b4")
    return w


# ---------------------------------------------------------------------------------- name tags
def tag_icon(cv, kind, x, y, colour):
    """A small construction-paper sticker the RA cut out (about 9 px)."""
    if kind == "star":
        pts = []
        for i in range(10):
            a = -np.pi / 2 + i * np.pi / 5
            r = 5 if i % 2 == 0 else 2.2
            pts.append((x + 4.5 + np.cos(a) * r, y + 5 + np.sin(a) * r))
        cv.poly([(px_ + 0.5, py_ + 0.5) for px_, py_ in pts], OUT)
        cv.poly(pts, colour)
    elif kind == "ball":                              # a tennis ball
        cv.ellipse(x - 1, y - 1, 11, 11, OUT); cv.ellipse(x, y, 9, 9, "#d8e04a")
        cv.px(x + 2, y + 2, "#f2f6a0")
        for k in range(5):
            cv.px(x + 1 + k, y + 3 + (k % 3 == 1), "#f6f6e6"); cv.px(x + 4 + k // 2, y + 6 + k // 3, "#f6f6e6")
    elif kind == "mountain":
        cv.poly([(x - 1, y + 9), (x + 3, y + 1), (x + 5, y + 4), (x + 7, y + 2), (x + 10, y + 9)], OUT)
        cv.poly([(x, y + 8), (x + 3, y + 2), (x + 5, y + 5), (x + 7, y + 3), (x + 9, y + 8)], colour)
        cv.px(x + 3, y + 2, "#f6f6e6"); cv.px(x + 7, y + 3, "#f6f6e6")
    elif kind == "heart":
        cv.ellipse(x, y + 1, 5, 5, colour); cv.ellipse(x + 4, y + 1, 5, 5, colour)
        cv.poly([(x, y + 4), (x + 9, y + 4), (x + 4.5, y + 9)], colour)
        cv.px(x + 1, y + 2, shade(colour, 0.3))
    elif kind == "note":
        cv.rect(x + 6, y, 2, 7, OUT); cv.ellipse(x + 2, y + 5, 6, 5, OUT); cv.ellipse(x + 3, y + 6, 4, 3, colour)
        cv.rect(x + 7, y, 3, 2, OUT)
    elif kind == "sun":
        cv.ellipse(x + 1, y + 1, 8, 8, OUT); cv.ellipse(x + 2, y + 2, 6, 6, colour)
        for (dx, dy) in ((4, -1), (4, 10), (-1, 5), (10, 5)):
            cv.px(x + dx + 1, y + dy, colour)
    elif kind == "buff":                              # a little bison silhouette
        cv.rect(x, y + 3, 9, 4, OUT); cv.rect(x + 1, y + 2, 4, 4, OUT); cv.rect(x + 1, y + 7, 1, 2, OUT); cv.rect(x + 7, y + 7, 1, 2, OUT)
        cv.px(x, y + 1, OUT); cv.px(x + 5, y + 1, OUT)
    else:                                             # plain circle
        cv.ellipse(x, y, 9, 9, OUT); cv.ellipse(x + 1, y + 1, 7, 7, colour)


def name_tag(cv, cx, y, name, colour, icon=None, icon_colour=None, right=False):
    """A paper strip with the name in marker, a sticker icon overlapping one end."""
    w = micro_width(name) + (4 if len(name) > 6 else 6)
    x = cx - w // 2
    cv.rect(x + 1, y + 1, w, 9, C(SHADOW, 0.35))
    cv.rect(x, y, w, 9, colour); cv.hline(x, y, w, shade(colour, 0.25)); cv.hline(x, y + 8, w, shade(colour, -0.2))
    micro_text(cv, name, x + (w - micro_width(name)) // 2, y + 2, "#2a2030")
    if icon:
        ix = x + w - 7 if right else x - 2
        tag_icon(cv, icon, ix, y - 8, icon_colour or CPAPER[0])
    return w


# --------------------------------------------------------------------------------------- doors
def transom(cv, x0, top, w, lit=False, seed=0):
    """The transom light over a 1950s door: wired glass, warm when somebody is home."""
    th = 12
    y = top - th - 3
    cv.rect(x0 - 4, y - 4, w + 8, th + 5, OUT)
    cv.rect(x0 - 3, y - 3, w + 6, th + 3, STEEL_T[3]); cv.hline(x0 - 3, y - 3, w + 6, STEEL_T[5]); cv.vline(x0 - 3, y - 3, th + 3, STEEL_T[5])
    if lit:
        cv.rect(x0, y, w, th, "#e9a84a"); cv.rect(x0, y, w, 4, "#f6cf7a"); cv.hline(x0, y + th - 2, w, "#c47a2c")
        halo(cv, x0 + w // 2, y + th // 2, w // 2 + 10, colour="#f6cf7a", strength=0.12, steps=2)
    else:
        cv.rect(x0, y, w, th, "#262c44"); cv.rect(x0, y, w, 3, "#323a58")
        cv.line(x0 + 3, y + th - 2, x0 + 10, y + 1, "#4a5680")
    for k in range(1, 3):
        cv.vline(x0 + k * w // 3, y, th, STEEL_T[2])
    cv.hline(x0 - 1, top - 3, w + 2, STEEL_T[3]); cv.hline(x0 - 1, top - 2, w + 2, STEEL_T[1])


def door_frame(cv, x0, top, w, h):
    cv.rect(x0 - 4, top - 4, w + 8, h + 4, OUT)
    cv.rect(x0 - 3, top - 3, w + 6, h + 3, STEEL_T[3])
    cv.vline(x0 - 3, top - 3, h + 3, STEEL_T[5]); cv.hline(x0 - 3, top - 3, w + 6, STEEL_T[5])
    cv.vline(x0 - 2, top - 2, h + 2, STEEL_T[4])
    cv.vline(x0 + w + 2, top - 3, h + 3, STEEL_T[2])
    cv.rect(x0 - 1, top - 1, w + 2, h + 1, STEEL_T[1])


def birch_leaf(cv, x0, top, w, h, seed=0, tone=0.0):
    """A flush birch-veneer door: vertical grain in long streaks, lit left edge."""
    xs, ys = np.mgrid[0:h, 0:w][1], np.mgrid[0:h, 0:w][0]
    n = hashn(xs // 2 + seed * 7, ys // 11 + (xs % 5), seed)
    idx = np.where(n < 0.18, 3, np.where(n > 0.9, 5, 4))
    fine = hashn(xs, ys // 3, seed + 2)
    idx = np.where(fine > 0.93, idx - 1, idx)
    rgb = P(BIRCH)[idx]
    if tone:
        rgb = rgb * (1 + tone)
    put_rgb(cv, x0, top, np.clip(rgb, 0, 1))
    cv.vline(x0, top, h, BIRCH[5]); cv.vline(x0 + 1, top, h, BIRCH[6])
    cv.vline(x0 + w - 1, top, h, BIRCH[2]); cv.hline(x0, top, w, BIRCH[2])


def door_hardware(cv, x0, top, w, h):
    # kick plate, lever handle, peephole
    cv.rect(x0 + 1, top + h - 8, w - 2, 7, CHROME[2]); cv.hline(x0 + 1, top + h - 8, w - 2, CHROME[4])
    cv.hline(x0 + 1, top + h - 2, w - 2, CHROME[1])
    for sx in (x0 + 3, x0 + w - 4):
        cv.px(sx, top + h - 6, CHROME[1])
    lx, ly = x0 + w - 9, top + 38
    cv.rect(lx + 3, ly - 2, 4, 6, OUT); cv.rect(lx + 4, ly - 1, 2, 4, CHROME[3])
    cv.rect(lx - 2, ly, 8, 3, OUT); cv.rect(lx - 1, ly + 1, 6, 1, CHROME[4])
    cv.rect(lx - 2, ly + 3, 8, 1, C(SHADOW, 0.3))
    cv.px(x0 + w // 2, top + 15, OUT); cv.px(x0 + w // 2, top + 14, CHROME[3])
    return lx, ly


def whiteboard(cv, x, y, w=22, h=15, seed=0, doodle="hi"):
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#e8eaf0"); cv.hline(x + 1, y + 1, w - 2, "#ffffff")
    cv.rect(x + 1, y + h - 2, w - 2, 1, "#a8aab8")
    rng = _rng(seed)
    if doodle == "hi":
        micro_text(cv, "HI!", x + 3, y + 3, "#3a5aa8")
        cv.line(x + 14, y + 9, x + 18, y + 5, "#c84a3c"); cv.line(x + 18, y + 5, x + 19, y + 9, "#c84a3c")
    elif doodle == "smile":
        cv.ellipse(x + 6, y + 3, 9, 9, "#3a8a5a"); cv.ellipse(x + 7, y + 4, 7, 7, "#e8eaf0")
        cv.px(x + 9, y + 6, "#3a8a5a"); cv.px(x + 12, y + 6, "#3a8a5a"); cv.hline(x + 9, y + 9, 4, "#3a8a5a")
    else:
        scribble(cv, x + 3, y + 4, w - 6, "#3a5aa8", seed=seed, rows=3, gap=3)
    cv.rect(x + w - 6, y + h - 3, 4, 1, "#c84a3c")      # marker on the ledge


def dorm_door(cv, cx, base, number, tags=(), deco=(), seed=0, ajar=False, lit=None):
    """A dorm room door: teal steel frame, birch leaf, kick plate and lever, the room number plate
    on the wall beside it, the RA's paper name tags and whatever the residents stuck on it.
    tags: [(name, colour, icon, icon_colour)]; deco: any of whiteboard, hanger, lights, pennant,
    poster, calendar. Returns the leaf box (x0, top, w, h)."""
    x0, top = cx - DOOR_W // 2, base - DOOR_H
    door_frame(cv, x0, top, DOOR_W, DOOR_H)
    transom(cv, x0, top, DOOR_W, lit=ajar if lit is None else lit, seed=seed)
    if ajar:
        open_room(cv, x0, top, DOOR_W, DOOR_H, seed=seed)
    else:
        birch_leaf(cv, x0, top, DOOR_W, DOOR_H, seed=seed)
        lx, ly = door_hardware(cv, x0, top, DOOR_W, DOOR_H)
        ty = top + 24
        for i, t in enumerate(tags):
            name, colour, icon, ic = (list(t) + [None, None])[:4]
            name_tag(cv, cx - 1, ty, name, colour, icon, ic, right=i % 2 == 1)
            ty += 12
        if "whiteboard" in deco:
            whiteboard(cv, x0 + 4, top + 46, seed=seed, doodle=["hi", "smile", "lines"][seed % 3])
        if "calendar" in deco:
            cv.rect(x0 + 5, top + 46, 16, 16, OUT); cv.rect(x0 + 6, top + 47, 14, 14, "#f2ecdc"); cv.rect(x0 + 6, top + 47, 14, 3, "#c84a3c")
            for k in range(12):
                cv.px(x0 + 7 + (k % 4) * 3, top + 52 + (k // 4) * 3, "#5a5a6a" if k > 3 else "#c84a3c")
        if "poster" in deco:
            cv.rect(x0 + 5, top + 3, 26, 15, OUT); cv.rect(x0 + 6, top + 4, 24, 13, "#2a3a6a")
            cv.poly([(x0 + 6, top + 16), (x0 + 13, top + 8), (x0 + 18, top + 12), (x0 + 22, top + 7), (x0 + 29, top + 16)], "#e07a5a")
            cv.ellipse(x0 + 22, top + 5, 4, 4, "#f6cf7a")
        if "pennant" in deco:
            cv.poly([(x0 + 4, top + 4), (x0 + 30, top + 9), (x0 + 4, top + 14)], OUT)
            cv.poly([(x0 + 5, top + 5), (x0 + 27, top + 9), (x0 + 5, top + 13)], "#1a1a22")
            micro_text(cv, "CU", x0 + 8, top + 7, "#cfb87c")
        if "hanger" in deco:                          # a do-not-disturb card on the lever
            cv.rect(lx - 1, ly + 3, 9, 15, OUT); cv.rect(lx, ly + 4, 7, 13, "#e07a5a"); cv.rect(lx + 2, ly + 2, 3, 3, OUT)
            cv.rect(lx + 3, ly + 3, 1, 1, "#e07a5a")
            for k in range(3):
                cv.hline(lx + 1, ly + 8 + k * 3, 5, "#f6e6c8")
        if "lights" in deco:                          # fairy lights taped round the frame
            pts = [(x0 - 3 + i * 4, top - 19) for i in range(11)] + [(x0 - 4, top - 19 + i * 5) for i in range(1, 17)] + \
                  [(x0 + DOOR_W + 3, top - 19 + i * 5) for i in range(1, 17)]
            for k, (px_, py_) in enumerate(pts):
                c = ["#f6cf7a", "#f2a0a0", "#a0d8f0", "#b0f0a0"][k % 4]
                cv.px(px_, py_, c); cv.rect(px_ - 1, py_ - 1, 3, 3, C(c, 0.18))
    w = number_plate(cv, x0 + DOOR_W + 6, top + 22, str(number))
    return (x0, top, DOOR_W, DOOR_H)


def open_room(cv, x0, top, w, h, seed=0):
    """A door standing open: the lamp-lit room inside (loft bed edge, poster, string of lights,
    desk lamp), the door leaf swung back into the room."""
    rng = _rng(seed)
    fl = top + h - 16                                       # where the room's floor meets its far wall
    cv.rect(x0, top, w, h, "#4a3024")
    cv.rect(x0, top, w, fl - top, "#a87a52")                # far wall, lamp-lit
    cv.rect(x0, top, w, 6, "#8a6040"); cv.rect(x0, top + 6, w, 3, "#966a46")
    cv.rect(x0, fl, w, h - 16, "#6a4630"); cv.hline(x0, fl, w, "#3a2418")      # floor inside (carpet tile)
    for yy in range(fl + 4, top + h, 4):
        cv.hline(x0, yy, w, "#5e3e2a")
    # loft bed: a steel rail, a striped blanket hanging over it, the ladder
    cv.rect(x0 + 6, top + 26, w - 6, 3, "#2a2a36"); cv.hline(x0 + 6, top + 26, w - 6, "#4a4a5a")
    for k in range(0, w - 8, 2):
        cv.vline(x0 + 7 + k, top + 29, 9 + (k // 2) % 2, ["#3e7a6e", "#e6d6b1", "#3e7a6e", "#c84a3c"][(k // 2) % 4])
    cv.vline(x0 + w - 6, top + 29, fl - top - 29, "#2a2a36")
    for yy in range(top + 34, fl, 7):
        cv.hline(x0 + w - 10, yy, 5, "#3a3a4a")
    # under the loft: the desk, its lamp, a laptop glow, a chair back
    cv.rect(x0 + 8, fl - 14, 20, 3, "#5a3a26"); cv.hline(x0 + 8, fl - 14, 20, "#8a5a3a")
    cv.vline(x0 + 9, fl - 11, 11, "#3a2418"); cv.vline(x0 + 26, fl - 11, 11, "#3a2418")
    cv.rect(x0 + 18, fl - 20, 7, 6, "#2a2a36"); cv.rect(x0 + 19, fl - 19, 5, 4, "#8ab0e0")
    cv.rect(x0 + 10, fl - 24, 5, 3, "#f6cd78"); cv.vline(x0 + 12, fl - 21, 7, "#2a2a36")
    halo(cv, x0 + 12, fl - 20, 14, colour="#fff0c4", strength=0.2, steps=2)
    cv.rect(x0 + 12, fl - 9, 9, 9, "#2a3a6a"); cv.hline(x0 + 12, fl - 9, 9, "#3a4a8a")
    # poster and a string of lights along the top
    cv.rect(x0 + 12, top + 9, 13, 14, "#1e2240"); cv.ellipse(x0 + 15, top + 11, 7, 7, "#e9a84a"); cv.hline(x0 + 13, top + 20, 11, "#c890d0")
    for k in range(10):
        px_ = x0 + 7 + k * 3; py_ = top + 3 + int(round(1.5 * np.sin(k * 0.8)))
        cv.px(px_, py_, ["#fff0c4", "#f2a0a0", "#a0d8f0"][k % 3])
    # the leaf, swung back against the inside wall (seen nearly edge-on)
    cv.rect(x0, top, 7, h, BIRCH[3]); cv.vline(x0 + 6, top, h, BIRCH[5]); cv.vline(x0, top, h, BIRCH[1])
    cv.rect(x0 + 3, top + 38, 3, 2, CHROME[3])
    cv.rect(x0 + 1, top + h - 8, 5, 7, CHROME[2])
    # a rubber doorstop wedge and light across the threshold
    cv.rect(x0 + 8, top + h - 3, 4, 3, "#2a2a36")
    cv.rect(x0, top + h - 1, w, 1, "#d8a066")


def stair_door(cv, cx, base, label="STAIRS"):
    """Steel fire door to the stairwell: wired-glass vision panel, push bar, closer arm, a sign."""
    w, h = 38, 74
    x0, top = cx - w // 2, base - h
    door_frame(cv, x0, top, w, h)
    cv.rect(x0, top, w, h, STEEL_T[2]); cv.vline(x0, top, h, STEEL_T[4]); cv.vline(x0 + 1, top, h, STEEL_T[3])
    cv.vline(x0 + w - 1, top, h, STEEL_T[1])
    for yy in range(top + 3, top + h - 2, 9):                 # faint pressed panel lines
        cv.hline(x0 + 3, yy, w - 6, shade(STEEL_T[2], 0.05))
    gx, gy = x0 + 8, top + 8
    cv.rect(gx - 1, gy - 1, 10, 28, OUT); cv.rect(gx, gy, 8, 26, "#3a4060")
    for yy in range(gy, gy + 26):                             # diamond wire mesh
        for xx in range(gx, gx + 8):
            if (xx - gx + yy - gy) % 5 == 0 or (xx - gx - (yy - gy)) % 5 == 0:
                cv.px(xx, yy, "#5a6488")
    cv.rect(gx + 1, gy + 1, 2, 10, C("#c8d0f0", 0.35))
    by = top + 38
    cv.rect(x0 + 3, by, w - 6, 5, OUT); cv.rect(x0 + 4, by + 1, w - 8, 3, CHROME[3]); cv.hline(x0 + 4, by + 1, w - 8, CHROME[4])
    cv.rect(x0 + w - 10, top + 2, 9, 3, OUT); cv.line(x0 + w - 6, top + 4, x0 + w - 16, top + 6, CHROME[1])
    sw = micro_width(label) + 6
    cv.rect(x0 + w // 2 - sw // 2, top + 48, sw, 9, OUT); cv.rect(x0 + w // 2 - sw // 2 + 1, top + 49, sw - 2, 7, "#e8e2d0")
    micro_text(cv, label, x0 + w // 2 - sw // 2 + 3, top + 50, "#a82a24")
    cv.rect(x0 + 1, top + h - 8, w - 2, 7, CHROME[2]); cv.hline(x0 + 1, top + h - 8, w - 2, CHROME[4])
    return x0, top, w, h


def hall_window(cv, x, y, w, h, seed=0, moon=None):
    """Steel casement window in a sandstone surround (lintel, jambs, deep sill), the campus at
    night outside. (x, y, w, h) is the glass."""
    cv.rect(x - 6, y - 8, w + 12, 7, FH_SAND[3]); cv.hline(x - 6, y - 8, w + 12, FH_SAND[5]); cv.hline(x - 6, y - 2, w + 12, FH_SAND[1])
    for k in range(3):
        cv.vline(x - 6 + (k + 1) * (w + 12) // 4, y - 7, 5, FH_SAND[2])
    cv.rect(x - 5, y - 1, 4, h + 1, FH_SAND[3]); cv.vline(x - 5, y - 1, h + 1, FH_SAND[5])
    cv.rect(x + w + 1, y - 1, 4, h + 1, FH_SAND[2])
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    mask = np.zeros((cv.h, cv.w), bool)
    mask[y:y + h, x:x + w] = True
    night_glass(cv, mask, y, y + h, seed=seed, moon=moon)
    # muntins: three lights wide, four high; an opened hopper at the bottom
    for k in range(1, 3):
        cv.vline(x + k * w // 3, y, h, "#2a2e3e")
    for k in range(1, 4):
        cv.hline(x, y + k * h // 4, w, "#2a2e3e")
    cv.line(x + 2, y + h - 4, x + w // 3 - 2, y + 2, C("#c8d0f0", 0.25))
    cv.rect(x - 8, y + h + 1, w + 16, 4, FH_SAND[4]); cv.hline(x - 8, y + h + 1, w + 16, FH_SAND[5])
    cv.hline(x - 8, y + h + 5, w + 16, C(SHADOW, 0.5))


def lounge_opening(cv, cx, base, w=58, h=74, seed=0):
    """A wide doorway into the floor's study lounge: a couch back, a TV's blue light, a vending
    machine and a window onto the night. Returns the TV screen rect for a flicker layer."""
    x0, top = cx - w // 2, base - h
    door_frame(cv, x0, top, w, h)
    cv.rect(x0, top, w, h, "#2c2230")
    cv.rect(x0, top, w, h - 16, "#3a3040")
    for yy in range(top + 6, top + h - 16, 8):
        cv.hline(x0, yy, w, "#342a3a")
    cv.rect(x0, top + h - 16, w, 16, "#3a2c2c"); cv.hline(x0, top + h - 16, w, "#241a1e")
    # window
    wm = np.zeros((cv.h, cv.w), bool); wm[top + 8:top + 30, x0 + 6:x0 + 24] = True
    cv.rect(x0 + 5, top + 7, 20, 24, OUT)
    night_glass(cv, wm, top + 8, top + 30, seed=seed + 4)
    cv.vline(x0 + 15, top + 8, 22, "#2a2e3e")
    # vending machine glowing at the right
    vx = x0 + w - 16
    cv.rect(vx, top + 20, 14, h - 34, OUT); cv.rect(vx + 1, top + 21, 12, h - 36, "#a82a24")
    cv.rect(vx + 2, top + 23, 8, 22, "#f2e6c0")
    for k in range(5):
        cv.hline(vx + 3, top + 26 + k * 4, 6, ["#5cb0a0", "#e8c24a", "#e07a5a"][k % 3])
    cv.rect(vx + 10, top + 24, 2, 8, "#2a2a36")
    # TV on a cart, couch back in front of it
    tv = (x0 + 26, top + 34, 14, 10)
    cv.rect(tv[0] - 1, tv[1] - 1, tv[2] + 2, tv[3] + 2, OUT); cv.rect(*tv, "#6a8ad0")
    cv.rect(tv[0] + 1, tv[1] + 1, 5, 3, "#a8c4f0")
    cv.rect(tv[0] + 2, tv[1] + tv[3] + 1, tv[2] - 4, 8, "#2a2a36")
    halo(cv, tv[0] + tv[2] // 2, tv[1] + tv[3] // 2, 18, colour="#8ab0f0", strength=0.14, steps=2)
    cv.rect(x0 + 4, top + h - 22, w - 8, 12, OUT); cv.rect(x0 + 5, top + h - 21, w - 10, 10, "#5c897c")
    cv.hline(x0 + 5, top + h - 21, w - 10, "#7aa898")
    for k in range(x0 + 14, x0 + w - 8, 12):
        cv.vline(k, top + h - 20, 8, "#4a7268")
    # sign over the doorway
    s = "STUDY LOUNGE"
    sw = micro_width(s) + 6
    cv.rect(cx - sw // 2, top - 14, sw, 9, OUT); cv.rect(cx - sw // 2 + 1, top - 13, sw - 2, 7, "#2a2a36")
    micro_text(cv, s, cx - sw // 2 + 3, top - 12, "#e8d8a8")
    return tv


# ---------------------------------------------------------------------------------- wall bits
def drinking_fountain(cv, cx, base):
    """1950s wall-hung stainless fountain: bowl, bubbler, push button, trap pipe into the wall."""
    y = base - 44                                         # bowl rim, about hip height
    # a sandstone backsplash panel behind it
    cv.rect(cx - 16, y - 24, 33, 46, OUT); cv.rect(cx - 15, y - 23, 31, 44, FH_SAND[3])
    cv.hline(cx - 15, y - 23, 31, FH_SAND[5]); cv.vline(cx - 15, y - 23, 44, FH_SAND[4]); cv.vline(cx + 15, y - 23, 44, FH_SAND[2])
    cv.hline(cx - 15, y - 2, 31, FH_SAND[2]); cv.hline(cx - 15, y + 21, 31, FH_SAND[1])
    for (bx, by) in ((cx - 13, y - 21), (cx + 12, y - 21), (cx - 13, y + 18), (cx + 12, y + 18)):
        cv.px(bx, by, CHROME[2])
    # the fountain: rounded stainless body, dished top with the bubbler, push button on the front
    cv.rect(cx - 14, y - 1, 29, 4, OUT); cv.rect(cx - 13, y + 3, 27, 8, OUT); cv.rect(cx - 10, y + 11, 21, 5, OUT)
    cv.rect(cx - 13, y, 27, 3, CHROME[4]); cv.hline(cx - 13, y, 27, "#eef0f4")
    cv.rect(cx - 9, y + 1, 19, 2, "#6a7a98"); cv.hline(cx - 8, y + 1, 17, "#8a9ab8")       # the water in the dish
    cv.rect(cx + 3, y - 2, 3, 3, CHROME[3]); cv.px(cx + 4, y - 3, "#c8e0f8"); cv.px(cx + 3, y - 4, "#a8c8f0")
    cv.rect(cx - 12, y + 3, 25, 8, CHROME[3]); cv.hline(cx - 12, y + 3, 25, CHROME[4]); cv.vline(cx + 12, y + 3, 8, CHROME[1])
    cv.rect(cx - 9, y + 11, 19, 4, CHROME[2]); cv.hline(cx - 9, y + 14, 19, CHROME[1])
    cv.rect(cx - 3, y + 5, 7, 4, OUT); cv.rect(cx - 2, y + 6, 5, 2, "#d8dce6")
    cv.rect(cx - 2, y + 16, 5, 4, CHROME[1]); cv.vline(cx - 1, y + 16, 4, CHROME[2])          # trap
    cv.hline(cx - 13, y + 21, 27, C(SHADOW, 0.25))


def pull_station(cv, x, y):
    cv.rect(x, y, 9, 12, OUT); cv.rect(x + 1, y + 1, 7, 10, "#c83a32"); cv.hline(x + 1, y + 1, 7, "#e85a4a")
    cv.rect(x + 2, y + 5, 5, 2, "#f2e6d0"); cv.rect(x + 3, y + 8, 3, 2, "#8a2420")


def thermostat(cv, x, y):
    cv.rect(x, y, 8, 10, OUT); cv.rect(x + 1, y + 1, 6, 8, "#d8d0bc"); cv.ellipse(x + 2, y + 2, 4, 4, "#a89c88"); cv.px(x + 3, y + 3, "#c83a32")


def light_switch(cv, x, y):
    cv.rect(x, y, 5, 8, OUT); cv.rect(x + 1, y + 1, 3, 6, "#e2dac6"); cv.rect(x + 2, y + 2, 1, 2, "#8a8070")


def wall_shadow(cv, x, base, w, depth=4):
    """The soft contact shadow where the floor meets the wall."""
    for k in range(depth):
        cv.hline(x, base + k, w, C(SHADOW, 0.28 * (1 - k / depth)))


# ------------------------------------------------------------------------------------- floors
def lino_floor(cv, x, y, w, h, seed=0, tile=16, border_rows=(0,), bottom_border=True, x_border=None, stripe=None):
    """Speckled 1950s asphalt-tile linoleum: two close tones in a quiet checker, each tile marbled
    with one short paler streak and a few chips, an oxblood border course along the wall (and the
    near wall). Rows deepen toward the viewer; one tile in thirty is a replacement a shade off."""
    rng = _rng(seed)
    rows, yy = [], y
    while yy < y + h:
        th = min(int(round(10 + 4 * (yy - y) / max(1, h))), y + h - yy)
        rows.append((yy, th))
        yy += th
    last = len(rows) - 1
    for row, (yy, th) in enumerate(rows):
        for col, xx in enumerate(range(x, x + w, tile)):
            x1 = min(x + w, xx + tile)
            border = row in border_rows or (bottom_border and row == last) or \
                (x_border is not None and (xx < x_border[0] or x1 > x_border[1])) or \
                (stripe is not None and stripe[0] <= yy < stripe[1])
            pal = LINO_OX if border else (LINO_F if (col + row) % 2 == 0 else LINO_G)
            base = 2 if rng.random() > 0.035 else int(rng.choice([1, 3]))
            cv.rect(xx, yy, x1 - xx, th, pal[base])
            cv.hline(xx, yy, x1 - xx, pal[min(4, base + 1)])
            cv.hline(xx, yy + th - 1, x1 - xx, pal[max(0, base - 1)])
            cv.vline(x1 - 1, yy + 1, th - 2, shade(pal[base], -0.05))
            if x1 - xx > 7 and th > 5:
                sx, sy = xx + int(rng.integers(2, x1 - xx - 5)), yy + int(rng.integers(2, th - 2))
                d = 1 if rng.random() < 0.5 else -1
                for k in range(int(rng.integers(3, 6))):
                    cv.px(sx + k, min(yy + th - 2, max(yy + 1, sy + (k // 2) * d)), shade(pal[base], 0.08))
                for _ in range(2):
                    cv.px(xx + int(rng.integers(1, x1 - xx - 1)), yy + int(rng.integers(1, th - 1)), pal[int(rng.choice([1, 3]))])
    if stripe is not None:                    # cream inlay lines either side of the oxblood band
        band = [yy for (yy, th) in rows if stripe[0] <= yy < stripe[1]]
        if band:
            top_y = band[0]; bot_y = [yy + th for (yy, th) in rows if yy == band[-1]][0]
            cv.hline(x, top_y, w, "#c8b49a"); cv.hline(x, bot_y - 1, w, "#b8a48a")
    # scuffs from move-in carts
    for _ in range(w * h // 1400):
        sx, sy = x + int(rng.integers(0, w - 12)), y + int(rng.integers(6, h - 4))
        cv.line(sx, sy, sx + int(rng.integers(4, 12)), sy + int(rng.integers(-1, 2)), C("#2a2020", 0.3))


def doormat(cv, cx, y, w=30, h=8, colour="#5a4a3e", seed=0, word=None):
    x = cx - w // 2
    cv.rect(x + 1, y + 1, w, h, C(SHADOW, 0.35))
    cv.rect(x, y, w, h, colour); cv.hline(x, y, w, shade(colour, 0.15))
    for yy in range(y + 2, y + h - 1, 2):
        cv.hline(x + 2, yy, w - 4, shade(colour, -0.12))
    cv.rect(x, y + h - 1, w, 1, shade(colour, -0.3))
    if word:
        micro_text(cv, word, cx - micro_width(word) // 2, y + 2, shade(colour, 0.35))


def sneakers(cv, x, y, colour="#e6e2d6", accent="#c84a3c"):
    for k, dx in enumerate((0, 8)):
        cv.rect(x + dx, y + k, 7, 3, OUT); cv.rect(x + dx + 1, y + k, 5, 2, colour); cv.px(x + dx + 2, y + k, accent)
        cv.hline(x + dx, y + k + 3, 7, C(SHADOW, 0.35))


def pizza_box(cv, x, y):
    cv.rect(x + 1, y + 1, 18, 10, C(SHADOW, 0.35))
    cv.rect(x, y, 18, 10, CARD[3]); cv.hline(x, y, 18, CARD[4]); cv.rect(x, y + 9, 18, 1, CARD[1])
    cv.ellipse(x + 5, y + 2, 8, 6, "#c84a3c"); cv.px(x + 8, y + 4, "#f6e6c8")
    cv.rect(x + 2, y + 3, 2, 4, CARD[2])


def skateboard(cv, x, y):
    cv.rect(x + 1, y + 2, 26, 6, C(SHADOW, 0.35))
    cv.rect(x + 2, y, 22, 6, OUT); cv.rect(x, y + 1, 26, 4, OUT)
    cv.rect(x + 1, y + 1, 24, 4, "#2a2a36"); cv.hline(x + 3, y + 1, 20, "#3e3e50")
    cv.rect(x + 8, y + 2, 8, 2, "#5cb0a0")
    for wx in (x + 4, x + 20):
        cv.rect(wx, y + 5, 3, 2, "#e8c24a")


def dropped_tag(cv, x, y, name, colour):
    w = micro_width(name) + 6
    cv.rect(x + 1, y + 1, w, 9, C(SHADOW, 0.35))
    cv.rect(x, y, w, 9, colour); micro_text(cv, name, x + 3, y + 2, "#2a2030")


# -------------------------------------------------------------------------------------- props
def move_in_cart(width=64, height=58, seed=0):
    """A grey rolling move-in bin heaped with a resident's things: boxes, a lamp, a pillow, a
    rolled rug, a desk fan; the handle frame at one end."""
    cv = Canvas(width + 8, height + 6, seed=seed)
    ox, base = 4, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3)
    bin_top = base - 26
    # casters
    for wx in (ox + 5, ox + width - 9):
        cv.rect(wx, base - 4, 5, 4, OUT); cv.rect(wx + 1, base - 3, 3, 2, "#3a3a46")
    # load (behind the bin's front lip)
    cv.rect(ox + 6, bin_top - 16, 22, 18, OUT); cv.rect(ox + 7, bin_top - 15, 20, 16, CARD[3])
    cv.hline(ox + 7, bin_top - 15, 20, CARD[4]); cv.vline(ox + 17, bin_top - 15, 6, CARD[1])
    cv.rect(ox + 8, bin_top - 8, 12, 2, "#c8b890")
    cv.ellipse(ox + 26, bin_top - 12, 20, 12, OUT); cv.ellipse(ox + 27, bin_top - 11, 18, 10, "#e6dcf0")    # pillow
    cv.hline(ox + 30, bin_top - 9, 10, "#c8bcd8")
    cv.rect(ox + 40, bin_top - 26, 3, 24, OUT); cv.vline(ox + 41, bin_top - 25, 22, "#a8aab4")      # lamp stem
    cv.poly([(ox + 35, bin_top - 26), (ox + 47, bin_top - 26), (ox + 45, bin_top - 33), (ox + 37, bin_top - 33)], OUT)
    cv.poly([(ox + 36, bin_top - 27), (ox + 46, bin_top - 27), (ox + 44, bin_top - 32), (ox + 38, bin_top - 32)], "#e07a5a")
    cv.rect(ox + 44, bin_top - 10, 14, 6, OUT); cv.rect(ox + 45, bin_top - 9, 12, 4, "#5c897c")    # rolled rug
    cv.vline(ox + 48, bin_top - 9, 4, "#e6d6b1"); cv.vline(ox + 53, bin_top - 9, 4, "#e6d6b1")
    cv.ellipse(ox + 10, bin_top - 26, 11, 11, OUT); cv.ellipse(ox + 11, bin_top - 25, 9, 9, "#3a4a6a")   # fan
    cv.ellipse(ox + 13, bin_top - 23, 5, 5, "#8aa8e0"); cv.px(ox + 15, bin_top - 21, OUT)
    # the bin
    cv.rect(ox, bin_top, width - 6, 24, OUT)
    cv.rect(ox + 1, bin_top + 1, width - 8, 22, "#5a5c6c"); cv.hline(ox + 1, bin_top + 1, width - 8, "#8a8c9c")
    cv.hline(ox + 1, bin_top + 2, width - 8, "#6e7080")
    for k in range(ox + 6, ox + width - 8, 10):
        cv.vline(k, bin_top + 4, 17, "#4c4e5c")
    cv.rect(ox + 14, bin_top + 9, 26, 7, "#2a2a36"); micro_text(cv, "FARRAND", ox + 15, bin_top + 10, "#e8d8a8")
    cv.hline(ox + 1, bin_top + 22, width - 8, "#3a3c48")
    # handle frame
    hx = ox + width - 6
    cv.rect(hx, bin_top - 20, 4, 44, OUT); cv.vline(hx + 1, bin_top - 19, 42, CHROME[3]); cv.vline(hx + 2, bin_top - 19, 42, CHROME[2])
    cv.rect(hx - 3, bin_top - 22, 8, 3, OUT); cv.hline(hx - 2, bin_top - 21, 6, CHROME[4])
    return cv, ox + width // 2, base


def mini_fridge(width=26, height=36, seed=0):
    """A black mini fridge out in the hall with a FREE? note taped on, a box fan on top."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 2)
    top = base - 30
    cv.rect(ox, top, width, 30, OUT)
    cv.rect(ox + 1, top + 1, width - 2, 28, "#2a2a34"); cv.vline(ox + 1, top + 1, 28, "#44444e"); cv.hline(ox + 1, top + 1, width - 2, "#4a4a56")
    cv.hline(ox + 1, top + 8, width - 2, "#16161e")
    cv.rect(ox + width - 5, top + 11, 2, 10, "#6a6a78")
    cv.rect(ox + 4, top + 12, 14, 11, "#f2ecd8"); cv.hline(ox + 4, top + 12, 14, "#ffffff")
    micro_text(cv, "FREE", ox + 5, top + 13, "#c84a3c"); cv.hline(ox + 6, top + 20, 9, "#8a8aa0")
    cv.rect(ox + 8, top + 11, 5, 2, C("#e8e0c0", 0.7))
    for k, c in enumerate(("#e8c24a", "#5cb0a0", "#e07a5a")):     # magnets
        cv.rect(ox + 4 + k * 5, top + 3, 3, 3, c)
    cv.rect(ox + 2, base - 2, width - 4, 2, "#16161e")
    # box fan on top
    cv.rect(ox + 3, top - 6, width - 6, 7, OUT); cv.rect(ox + 4, top - 5, width - 8, 5, "#d8d4c8")
    for k in range(ox + 6, ox + width - 5, 2):
        cv.vline(k, top - 4, 3, "#9a968a")
    return cv, ox + width // 2, base


def box_stack(width=40, height=44, labels=("BOOKS", "JAKERSON"), seed=0, racket=True):
    """Moving boxes stacked against the wall, marker labels, a tennis racket bag leaning on them."""
    cv = Canvas(width + 22, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 3, 2)
    boxes = [(ox, base - 22, width, 22), (ox + 4, base - 40, width - 10, 18)]
    for i, (bx, by, bw, bh) in enumerate(boxes):
        cv.rect(bx, by, bw, bh, OUT)
        cv.rect(bx + 1, by + 1, bw - 2, bh - 2, CARD[3 - i % 2]); cv.hline(bx + 1, by + 1, bw - 2, CARD[4])
        cv.rect(bx + bw // 2 - 3, by + 1, 6, bh - 2, C("#d8c8a0", 0.55))      # packing tape
        cv.vline(bx + bw - 2, by + 1, bh - 2, CARD[1])
        lab = labels[i % len(labels)]
        micro_text(cv, lab, bx + max(2, bw // 2 - micro_width(lab) // 2), by + bh - 8, "#2a2030")
        cv.rect(bx + 3, by + 3, 6, 4, "#f2ecd8")        # a shipping label
    if racket:                                          # a tennis racket leaning on the boxes
        rx, ry = ox + width + 4, base - 46               # centre of the head
        cv.line(rx - 1, ry + 9, rx - 4, base - 1, OUT); cv.line(rx, ry + 9, rx - 3, base - 1, OUT)
        cv.line(rx + 1, ry + 9, rx - 2, base - 1, OUT)
        cv.line(rx, ry + 10, rx - 3, base - 8, "#c8c4d0"); cv.line(rx - 2, base - 8, rx - 3, base - 2, "#e8e2d6")   # grip
        cv.ellipse(rx - 7, ry - 10, 15, 20, OUT); cv.ellipse(rx - 6, ry - 9, 13, 18, "#3a6ac8")
        cv.ellipse(rx - 5, ry - 8, 11, 16, "#2a2a36")
        for k in range(-3, 4, 2):
            cv.vline(rx + k, ry - 7, 14, "#d8d4c4")
        for k in range(-6, 8, 3):
            cv.hline(rx - 4, ry + k, 9, "#d8d4c4")
        cv.ellipse(rx - 5, ry - 8, 11, 16, C("#000000", 0.0))
        cv.ellipse(rx + 4, base - 7, 6, 6, OUT); cv.ellipse(rx + 5, base - 6, 4, 4, "#d8e04a")   # a ball by the boxes
    return cv, ox + width // 2, base


def guitar_case(width=18, height=50, seed=0):
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 2)
    cx = ox + width // 2
    cv.ellipse(cx - 9, base - 22, 18, 22, OUT); cv.ellipse(cx - 7, base - 38, 14, 16, OUT); cv.rect(cx - 4, base - 50, 8, 16, OUT)
    cv.ellipse(cx - 8, base - 21, 16, 20, "#24222e"); cv.ellipse(cx - 6, base - 37, 12, 14, "#24222e"); cv.rect(cx - 3, base - 49, 6, 15, "#24222e")
    cv.vline(cx - 5, base - 35, 28, "#3a3848"); cv.vline(cx - 2, base - 48, 12, "#3a3848")
    for (sx, sy, c) in ((cx - 3, base - 16, "#e8c24a"), (cx + 1, base - 28, "#5cb0a0"), (cx - 4, base - 9, "#e07a5a")):
        cv.rect(sx, sy, 5, 4, c)
    cv.rect(cx + 3, base - 24, 3, 6, "#6a6a78")
    return cv, cx, base


def laundry_pile(width=36, height=24, seed=0):
    """A floormate's laundry basket full of clothes, a pair of sneakers beside it."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 2)
    bw = width - 14
    for k, c in enumerate(("#5c897c", "#e6d6b1", "#c84a3c", "#8aa8e0", "#e8c24a")):
        cv.ellipse(ox + 1 + k * 4, base - 21 + (k % 2) * 2, 10, 8, OUT)
        cv.ellipse(ox + 2 + k * 4, base - 20 + (k % 2) * 2, 8, 6, c)
    cv.rect(ox, base - 15, bw, 15, OUT); cv.rect(ox + 1, base - 14, bw - 2, 13, "#e8e4dc")
    for yy in range(base - 12, base - 2, 3):
        for xx in range(ox + 3, ox + bw - 2, 4):
            cv.rect(xx, yy, 2, 2, "#a8a49c")
    cv.hline(ox + 1, base - 14, bw - 2, "#ffffff")
    sneakers(cv, ox + bw + 1, base - 5, colour="#e6e2d6", accent="#3a5aa8")
    return cv, ox + width // 2, base


def leaning_bike(width=54, height=34, seed=0):
    from lib_eng import bike
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    bike(cv, ox + 1, base, frame="#2e6a5e", hi="#4a9080", r=10, seed=seed)
    cv.rect(ox + 22, base - 26, 6, 4, OUT); cv.rect(ox + 23, base - 25, 4, 2, "#c84a3c")    # a U-lock on the frame
    return cv, ox + width // 2, base


def hall_bench(width=84, height=30, seed=0):
    """A long oak bench with steel legs (the kind every 1950s hall has), someone's backpack on it."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3)
    st = base - 16
    for lx in (ox + 5, ox + width - 9):
        cv.rect(lx, st + 3, 4, 13, OUT); cv.vline(lx + 1, st + 4, 11, CHROME[2])
    cv.rect(ox, st - 2, width, 7, OUT)
    cv.wood(ox + 1, st - 1, width - 2, 5, WOOD[4], vertical=False, plank=5, seed=seed)
    cv.hline(ox + 1, st - 1, width - 2, WOOD[5])
    # backpack
    bx = ox + 14
    cv.rect(bx, st - 14, 16, 14, OUT); cv.rect(bx + 1, st - 13, 14, 12, "#3a5aa8"); cv.hline(bx + 1, st - 13, 14, "#5a7ac8")
    cv.rect(bx + 3, st - 7, 10, 5, "#2a4a8a"); cv.vline(bx + 8, st - 7, 5, "#e8c24a")
    return cv, ox + width // 2, base


# ------------------------------------------------------------------------------ the RA board
def scallop_border(cv, x, y, w, h, cols=(CPAPER[0], CPAPER[1]), r=3):
    """Bulletin-board border trimmer: a ring of scalloped paper in alternating colours."""
    k = 0
    for xx in range(x, x + w - r, 2 * r):
        for yy, flip in ((y, 1), (y + h - r - 1, -1)):
            c = cols[k % len(cols)]
            cv.rect(xx, yy, 2 * r, r + 1 if flip > 0 else r + 1, c)
            cv.px(xx, yy + (r if flip > 0 else 0), C(SHADOW, 0.0))
            cv.ellipse(xx, yy + (r - 1 if flip > 0 else -r + 1), 2 * r, 2 * r - 1, c)
            cv.px(xx + r, yy + (2 * r - 1 if flip > 0 else -r + 1), shade(c, -0.3))
        k += 1
    k = 0
    for yy in range(y + r + 1, y + h - 2 * r, 2 * r):
        for xx, flip in ((x, 1), (x + w - r - 1, -1)):
            c = cols[(k + 1) % len(cols)]
            cv.rect(xx, yy, r + 1, 2 * r, c)
            cv.ellipse(xx + (r - 1 if flip > 0 else -r + 1), yy, 2 * r - 1, 2 * r, c)
        k += 1


def paper_letters(cv, cx, y, s, cols=CPAPER[:6]):
    """Cut-paper letters, one coloured square each, the RA's welcome."""
    adv = 8
    x = cx - len(s) * adv // 2
    k = 0
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        c = cols[k % len(cols)]
        k += 1
        cv.rect(x + i * adv + 1, y + 1, 7, 11, C(SHADOW, 0.4))
        cv.rect(x + i * adv, y, 7, 11, c); cv.hline(x + i * adv, y, 7, shade(c, 0.3))
        text(cv, ch, x + i * adv + 1, y + 1, "#2a2030")


def polaroid(cv, x, y, hair, shirt, skin):
    cv.rect(x, y, 9, 11, OUT); cv.rect(x + 1, y + 1, 7, 9, "#f6f2e8")
    cv.rect(x + 2, y + 2, 5, 5, "#8aa8c8")
    cv.rect(x + 2, y + 5, 5, 2, shirt); cv.rect(x + 3, y + 3, 3, 2, skin); cv.hline(x + 3, y + 2, 3, hair)


def ra_board(cv, x, y, w=150, h=66, seed=0, ra="MIKA", room="210"):
    """The RA's bulletin board: aluminium frame, cork, scalloped border, cut-paper WELCOME HOME,
    and the move-in week notices (floor meeting, quiet hours, laundry, meet your floor photos)."""
    rng = _rng(seed)
    cv.rect(x - 3, y - 3, w + 6, h + 6, OUT)
    cv.rect(x - 2, y - 2, w + 4, h + 4, CHROME[3]); cv.hline(x - 2, y - 2, w + 4, CHROME[4]); cv.hline(x - 2, y + h + 1, w + 4, CHROME[1])
    cork_surface(cv, x, y, w, h, seed=seed)
    scallop_border(cv, x, y, w, h)
    paper_letters(cv, x + w // 2, y + 7, "WELCOME HOME")
    by = y + 21
    # floor meeting flyer
    notice_paper(cv, x + 8, by, 30, 30, tint="#f2e8d0", seed=seed + 1, title="FLOOR", rows=0, pin="#c84a3c")
    micro_text(cv, "MTG", x + 17, by + 10, "#2a2a3a")
    text(cv, "9PM", x + 12, by + 17, "#c84a3c")
    # meet your floor: polaroid grid
    px0 = x + 42
    cv.rect(px0, by, 38, 34, "#e8c24a"); cv.hline(px0, by, 38, shade("#e8c24a", 0.3))
    micro_text(cv, "MEET 2ND", px0 + 3, by + 2, "#2a2030")
    looks = [("#2a1a14", "#c84a3c", "#c89070"), ("#e8c890", "#3a5aa8", "#e8b890"), ("#14100c", "#5c897c", "#8a5a3a"),
             ("#6a3a1a", "#e8c24a", "#d8a07a"), ("#1a1410", "#c890d0", "#b07a5a"), ("#3a2a1a", "#e6e2d6", "#e0b08a")]
    for i, (hr, sh, sk) in enumerate(looks):
        polaroid(cv, px0 + 3 + (i % 3) * 11, by + 9 + (i // 3) * 12, hr, sh, sk)
    # quiet hours with a moon, laundry arrow, tear-off flyer, RA card, calendar
    notice_paper(cv, x + 84, by, 24, 18, tint="#c8d8f0", seed=seed + 2, title="QUIET", rows=1, pin="#3a5aa8")
    cv.ellipse(x + 100, by + 10, 5, 5, "#e8c24a"); cv.ellipse(x + 102, by + 9, 4, 4, "#c8d8f0")
    notice_paper(cv, x + 84, by + 20, 24, 18, tint="#d8f0c8", seed=seed + 3, title="WASH", rows=0, pin="#3a8a5a")
    micro_text(cv, "LOBBY", x + 86, by + 28, "#2a2a3a")
    cv.vline(x + 104, by + 27, 6, "#3a8a5a"); cv.px(x + 103, by + 31, "#3a8a5a"); cv.px(x + 105, by + 31, "#3a8a5a")
    notice_paper(cv, x + 112, by - 1, 28, 22, tint="#f6ecd2", seed=seed + 4, title="CAL", rows=0, pin="#d8b260")
    for k in range(15):
        c = "#c84a3c" if k in (2, 9) else "#8a8a9a"
        cv.rect(x + 115 + (k % 5) * 5, by + 9 + (k // 5) * 4, 3, 2, c)
    notice_paper(cv, x + 112, by + 23, 28, 17, tint="#f0d0e0", seed=seed + 5, title="RA " + ra, rows=0, pin="#c84a3c")
    micro_text(cv, "RM " + room, x + 117, by + 32, "#2a2a3a")
    tag_icon(cv, "star", x + 134, by + 18, "#e8c24a")
    return [(x + 8, by, 30, 30, "#f2e8d0"), (x + 84, by, 24, 18, "#c8d8f0"), (x + 112, by - 1, 28, 22, "#f6ecd2")]


def hall_poster(cv, x, y, seed=0, title="OPEN MIC", colour="#2a3a6a"):
    """A screen-printed event poster taped to the block, one corner curling."""
    w, h = 34, 44
    cv.rect(x + 1, y + 1, w, h, C(SHADOW, 0.35))
    cv.rect(x, y, w, h, colour); cv.hline(x, y, w, shade(colour, 0.25))
    micro_text(cv, title, x + (w - micro_width(title)) // 2, y + 4, "#f6cd78")
    cv.ellipse(x + 9, y + 13, 16, 16, "#e07a5a"); cv.ellipse(x + 12, y + 16, 10, 10, colour)
    cv.rect(x + 16, y + 14, 2, 14, "#e6d6b1"); cv.rect(x + 14, y + 12, 6, 4, "#e6d6b1")       # a microphone
    micro_text(cv, "FRI 8", x + (w - micro_width("FRI 8")) // 2, y + 32, "#e6d6b1")
    cv.hline(x + 5, y + 39, w - 10, shade(colour, 0.3))
    for (tx, ty) in ((x - 1, y - 1), (x + w - 4, y - 1)):
        cv.rect(tx, ty, 5, 3, C("#e8e0c0", 0.75))
    cv.poly([(x + w - 6, y + h), (x + w, y + h - 6), (x + w, y + h)], C(SHADOW, 0.0))
    cv.poly([(x + w - 6, y + h - 1), (x + w - 1, y + h - 6), (x + w - 6, y + h - 6)], shade(colour, 0.35))


def room_sign(cv, x, y, lines=("< 201-214", "STAIRS >")):
    """The hall's directional sign: a dark plate with cream letters in the game font."""
    w = max(text_width(s) for s in lines) + 10
    h = 4 + 11 * len(lines)
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#2a2a36"); cv.hline(x + 1, y + 1, w - 2, "#3e3e4e")
    for i, s in enumerate(lines):
        text(cv, s, x + 5, y + 2 + i * 11, "#e8d8a8")


def packing_peanuts(cv, cx, cy, seed=0, n=14):
    rng = _rng(seed)
    for _ in range(n):
        x = cx + int(rng.normal(0, 9)); y = cy + int(rng.normal(0, 3))
        cv.rect(x, y, 2, 1, "#f2ecdc"); cv.px(x, y + 1, "#b8b0a0")


# ================================================================== D03: lobby and laundry
TERRAZZO = ["#5a4e48", "#7a6c62", "#8e8074", "#a09284", "#b2a494", "#c6b8a6"]
BRASS_FH = ["#4a3018", "#7a5428", "#a87c38", "#d0a650", "#f0d48a"]
MINT = ["#2a3a36", "#3e5650", "#56726a", "#6e8c82", "#88a69a", "#a6c2b4", "#c4dccf"]   # glazed laundry tile
VINYL_T = ["#1e3a3a", "#2c5250", "#3e6e68", "#5a8c84", "#7aaea2"]        # teal vinyl upholstery
MUSTARD = ["#4a3410", "#7a5618", "#a8782a", "#c89838", "#e0b850"]


TERRAZZO_ROSE = ["#5e4a46", "#7e665e", "#927870", "#a48a80", "#b49a8e", "#c8aea0"]


def terrazzo_floor(cv, x, y, w, h, seed=0, cell=64):
    """Lobby terrazzo: big squares poured alternately in a warm grey and a rose mix, thick with marble
    chips, divided by thin brass strips; a darker border course along the wall. Squares get taller
    toward the viewer."""
    ys, xs = np.mgrid[y:y + h, x:x + w]
    n = hashn(xs, ys, seed)
    n2 = hashn(xs // 2, ys, seed + 7)
    idx = np.full(xs.shape, 2)
    idx = np.where(n > 0.80, 3, idx)
    idx = np.where(n > 0.95, 4, idx)
    idx = np.where(n < 0.08, 1, idx)
    idx = np.where(n2 > 0.988, 5, idx)
    lines_y = [y + 12]
    yy = y + 12
    while yy < y + h:
        yy += int(round(cell * 0.55 * (0.8 + 0.45 * (yy - y) / h)))
        lines_y.append(yy)
    row = np.zeros(xs.shape, int)
    for ly in lines_y:
        row += (ys >= ly)
    col = (xs - x) // cell
    rose = ((row + col) % 2 == 1) & (ys >= y + 12)
    rgb = np.where(rose[..., None], P(TERRAZZO_ROSE)[idx], P(TERRAZZO)[idx])
    put_rgb(cv, x, y, rgb)
    for ly in lines_y:
        cv.hline(x, ly, w, BRASS_FH[1]); cv.hline(x, ly + 1, w, C(BRASS_FH[3], 0.35))
    for lx in range(x + cell, x + w, cell):
        cv.vline(lx, y + 12, h - 12, BRASS_FH[1])
    cv.rect(x, y, w, 12, C("#3a2a2a", 0.45))           # the dark border course along the wall
    cv.hline(x, y + 11, w, BRASS_FH[2])


def floor_medallion(cv, cx, cy, rx=34, ry=14):
    """A terrazzo medallion inlaid in front of the doors: a sandstone ring, a compass star, 1949."""
    cv.ellipse(cx - rx, cy - ry, 2 * rx + 1, 2 * ry + 1, BRASS_FH[2])
    cv.ellipse(cx - rx + 1, cy - ry + 1, 2 * rx - 1, 2 * ry - 1, "#7a4a3e")
    cv.ellipse(cx - rx + 5, cy - ry + 3, 2 * rx - 9, 2 * ry - 5, BRASS_FH[2])
    cv.ellipse(cx - rx + 6, cy - ry + 4, 2 * rx - 11, 2 * ry - 7, TERRAZZO[3])
    for (dx, dy) in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        tipx, tipy = cx + dx * (rx - 9), cy + dy * (ry - 5)
        cv.poly([(cx - dy * 3, cy + dx * 2), (tipx, tipy), (cx + dy * 3, cy - dx * 2)], "#5c897c" if dx == 0 else "#b8694c")
    cv.ellipse(cx - 3, cy - 2, 7, 5, BRASS_FH[3])


def tile_wainscot(cv, x, y, w, h, pal=MINT):
    """Glazed 6 px tiles in a stack bond with a bullnose cap: the laundry room's wipe-clean wall."""
    rng = _rng(3)
    for yy in range(y + 3, y + h, 6):
        for xx in range(x, x + w, 6):
            k = rng.random()
            tone = pal[4] if k < 0.7 else pal[3] if k < 0.9 else pal[5]
            cv.rect(xx, yy, min(5, x + w - xx), min(5, y + h - yy), tone)
            cv.px(xx, yy, pal[6])
    cv.rect(x, y, w, 3, pal[5]); cv.hline(x, y, w, pal[6]); cv.hline(x, y + 2, w, pal[3])


def fluorescent(cv, cx, y, w=46):
    """A two-tube fluorescent fixture with a wrap lens; a cool wash on the wall below."""
    for (rx, ry, a) in ((60, 50, 0.06), (40, 34, 0.07), (24, 18, 0.08)):
        soft_ellipse(cv, cx, y + 6, rx, ry, "#e8f0ff", a)
    cv.rect(cx - w // 2 - 1, y, w + 2, 8, OUT)
    cv.rect(cx - w // 2, y + 1, w, 6, "#e8eef6"); cv.hline(cx - w // 2, y + 1, w, "#ffffff")
    cv.hline(cx - w // 2, y + 5, w, "#c8d0dc"); cv.hline(cx - w // 2, y + 6, w, "#a8b0c0")
    for k in range(cx - w // 2 + 3, cx + w // 2 - 2, 4):
        cv.px(k, y + 4, "#d8e0ea")


def mailboxes(cv, x, y, cols=9, rows=6, seed=0):
    """A bank of 1950s brass mailbox doors: a little window and a combination dial on each, set in
    a sandstone surround, a MAIL plate on top and a slot for outgoing letters."""
    rng = _rng(seed)
    cw, ch = 10, 10
    w, h = cols * cw + 4, rows * ch + 4
    cv.rect(x - 4, y - 14, w + 8, h + 20, FH_SAND[2]); cv.hline(x - 4, y - 14, w + 8, FH_SAND[4])
    cv.rect(x - 4, y + h + 4, w + 8, 3, FH_SAND[4]); cv.hline(x - 4, y + h + 4, w + 8, FH_SAND[5])
    cv.rect(x, y, w, h, OUT)
    for r in range(rows):
        for c in range(cols):
            bx, by = x + 2 + c * cw, y + 2 + r * ch
            cv.rect(bx, by, cw - 1, ch - 1, BRASS_FH[2]); cv.hline(bx, by, cw - 1, BRASS_FH[4]); cv.vline(bx, by, ch - 1, BRASS_FH[3])
            cv.rect(bx + 2, by + 2, 5, 2, "#2a2230" if rng.random() < 0.7 else "#e6dcc0")    # window (some have mail)
            cv.px(bx + 4, by + 6, BRASS_FH[0]); cv.px(bx + 3, by + 6, BRASS_FH[1])            # dial
            cv.px(bx + 7, by + 7, BRASS_FH[1])
    s = "MAIL"
    cv.rect(x + w // 2 - 14, y - 12, 28, 10, OUT); cv.rect(x + w // 2 - 13, y - 11, 26, 8, BRASS_FH[3])
    micro_text(cv, s, x + w // 2 - micro_width(s) // 2, y - 10, BRASS_FH[0])
    return w, h


def front_entrance(cv, cx, base, seed=0):
    """The hall's front doors: a pair of glass doors and a transom in a sandstone surround, FARRAND
    HALL in brass letters over them, the lamp-lit walk and the night outside."""
    w, h = 56, 76
    x0, top = cx - w // 2, base - h
    # sandstone surround and lettered lintel
    cv.rect(x0 - 12, top - 34, w + 24, h + 34, FH_SAND[3])
    for yy in range(top - 34, base, 7):                       # coursed blocks
        cv.hline(x0 - 12, yy, w + 24, FH_SAND[2])
        off = 0 if (yy // 7) % 2 else 9
        for xx in range(x0 - 12 + off, x0 + w + 12, 18):
            cv.vline(xx, yy, 7, FH_SAND[2])
    cv.vline(x0 - 12, top - 34, h + 34, FH_SAND[5]); cv.vline(x0 + w + 11, top - 34, h + 34, FH_SAND[1])
    cv.rect(x0 - 14, top - 36, w + 28, 3, FH_SAND[4]); cv.hline(x0 - 14, top - 36, w + 28, FH_SAND[5])
    s = "FARRAND HALL"
    cv.rect(cx - text_width(s) // 2 - 4, top - 30, text_width(s) + 8, 12, FH_SAND[2])
    text(cv, s, cx - text_width(s) // 2 + 1, top - 29, BRASS_FH[0])
    text(cv, s, cx - text_width(s) // 2, top - 30, BRASS_FH[4])
    # frame and transom, the two oak-and-glass leaves
    cv.rect(x0 - 3, top - 15, w + 6, h + 15, OUT)
    cv.rect(x0 - 2, top - 14, w + 4, h + 14, "#5a4a3a")
    for lx in (x0, x0 + w // 2):
        cv.rect(lx, top, w // 2, h, "#7a6448"); cv.vline(lx, top, h, "#9a8058"); cv.vline(lx + w // 2 - 1, top, h, "#3a2e26")
        cv.hline(lx, top, w // 2, "#9a8058")
    outside = np.zeros((cv.h, cv.w), bool)
    outside[top - 12:top - 2, x0:x0 + w] = True
    for lx in (x0, x0 + w // 2):
        outside[top + 3:base - 12, lx + 3:lx + w // 2 - 3] = True
    night_glass(cv, outside, top - 12, base - 30, seed=seed, skyline=True)
    # the walk outside: paving in the lamp's pool, a lamp post on the far side
    for lx in (x0, x0 + w // 2):
        gx0, gx1 = lx + 3, lx + w // 2 - 3
        cv.rect(gx0, base - 26, gx1 - gx0, 14, "#3e3848"); cv.hline(gx0, base - 26, gx1 - gx0, "#2a2634")
        for yy in range(base - 22, base - 12, 4):
            cv.hline(gx0, yy, gx1 - gx0, "#4a4456")
    cv.rect(x0 + 38, top + 24, 2, base - 26 - top - 24, "#1a1824")
    cv.rect(x0 + 36, top + 18, 6, 6, "#f6cd78"); cv.rect(x0 + 37, top + 19, 4, 3, "#fff0c4"); cv.hline(x0 + 35, top + 17, 8, "#1a1824")
    halo(cv, x0 + 39, top + 21, 10, colour="#f6cf7a", strength=0.25, steps=2)
    soft_ellipse(cv, x0 + 39, base - 20, 9, 3, "#f6cf7a", 0.4)
    cv.rect(x0 - 2, top - 2, w + 4, 2, "#5a4a3a")
    for k in range(1, 4):
        cv.vline(x0 + k * w // 4, top - 12, 10, "#5a4a3a")
    for lx in (x0, x0 + w // 2):
        cv.line(lx + 5, base - 18, lx + 14, top + 6, C("#c8d0f0", 0.2))
        cv.rect(lx + 1, base - 11, w // 2 - 2, 10, "#7a6448"); cv.hline(lx + 1, base - 11, w // 2 - 2, "#9a8058")
        cv.rect(lx + 3, top + 40, w // 2 - 6, 3, OUT); cv.hline(lx + 4, top + 41, w // 2 - 8, CHROME[4])
    cv.vline(cx, top - 14, h + 14, OUT)
    return x0, top, w, h


def fireplace(cv, cx, base, seed=0):
    """The lobby's sandstone fireplace: rough ashlar breast, a dressed mantel shelf with a clock and
    a pair of candlesticks, the firebox with a grate of logs. Returns the firebox rect."""
    w = 84
    x0 = cx - w // 2
    top = base - 136
    from surfaces import ashlar_wall
    ashlar_wall(cv, x0 + 8, top, w - 16, 136 - 40, FH_SAND, course=6, seed=seed, cap=False)
    cv.vline(x0 + 8, top, 96, FH_SAND[5]); cv.vline(x0 + w - 9, top, 96, FH_SAND[1])
    # mantel
    my = base - 44
    cv.rect(x0, my - 4, w, 8, OUT); cv.rect(x0 + 1, my - 3, w - 2, 6, FH_SAND[4]); cv.hline(x0 + 1, my - 3, w - 2, FH_SAND[5])
    cv.hline(x0 + 1, my + 2, w - 2, FH_SAND[2])
    # lower surround and the firebox
    ashlar_wall(cv, x0 + 4, my + 4, w - 8, 40, FH_SAND, course=7, seed=seed + 1, cap=False)
    fb = (cx - 20, base - 30, 40, 26)
    cv.rect(fb[0] - 3, fb[1] - 3, fb[2] + 6, fb[3] + 3, FH_SAND[1])
    cv.ellipse(fb[0] - 3, fb[1] - 9, fb[2] + 6, 14, FH_SAND[1])
    cv.rect(*fb, "#140c10"); cv.ellipse(fb[0], fb[1] - 6, fb[2], 12, "#140c10")
    for yy in range(fb[1] - 4, fb[1] + fb[3], 4):                         # firebrick at the back
        cv.hline(fb[0] + 4, yy, fb[2] - 8, "#2a1414")
    cv.rect(fb[0] + 5, base - 9, fb[2] - 10, 3, "#3a1a10")                 # logs on the grate
    cv.rect(fb[0] + 8, base - 12, fb[2] - 16, 3, "#4a2a18"); cv.hline(fb[0] + 8, base - 12, fb[2] - 16, "#6a3a20")
    cv.rect(fb[0] + 3, base - 5, fb[2] - 6, 2, IRON[2])
    for k in range(fb[0] + 5, fb[0] + fb[2] - 4, 5):
        cv.vline(k, base - 6, 3, IRON[1])
    halo(cv, cx, base - 14, 46, colour="#f6a050", strength=0.16, steps=3)
    # hearth stone flush with the floor (painted on the floor by the room)
    # things on the mantel: a clock, two candlesticks, a little framed photo
    cv.rect(cx - 6, my - 15, 13, 11, OUT); cv.rect(cx - 5, my - 14, 11, 10, WOOD[3]); cv.ellipse(cx - 3, my - 13, 7, 7, "#e6dcc0")
    cv.px(cx, my - 11, OUT); cv.px(cx + 1, my - 10, OUT)
    for sx in (x0 + 12, x0 + w - 14):
        cv.rect(sx, my - 12, 3, 8, BRASS_FH[3]); cv.rect(sx - 1, my - 5, 5, 1, BRASS_FH[2]); cv.rect(sx, my - 15, 2, 3, "#f2ecdc")
        cv.px(sx, my - 17, "#f6cd78")
    cv.rect(x0 + w - 32, my - 12, 10, 8, OUT); cv.rect(x0 + w - 31, my - 11, 8, 6, "#8aa8c8")
    return fb


def fire_frames(n=4, w=40, h=26, seed=0):
    """Flames for the fireplace, n loop frames of crisp licks over the logs (RGBA canvases)."""
    rng = _rng(seed)
    frames = []
    for f in range(n):
        cv = Canvas(w, h)
        for k in range(7):
            fx = 6 + k * 4 + int(rng.integers(-1, 2))
            fh = int(8 + 7 * abs(np.sin(f * 1.3 + k * 1.7)) + rng.integers(0, 3))
            base = h - 11
            for yy in range(fh):
                t = yy / fh
                half = max(0, int(round(2.5 * (1 - t))))
                c = "#fff0c4" if t < 0.25 and k % 2 else "#f6cd78" if t < 0.45 else "#e9a84a" if t < 0.75 else "#c84a2c"
                cv.rect(fx - half, base - yy, 2 * half + 1, 1, c)
        cv.rect(8, h - 11, w - 16, 2, "#ff9a4a")
        for _ in range(3):
            cv.px(int(rng.integers(8, w - 8)), int(rng.integers(0, h - 16)), "#ffd27a")
        frames.append(cv)
    return frames


def desk_wall(cv, x, y, w, seed=0):
    """Behind the front desk: package cubbies with parcels, the key box, a FRONT DESK plate."""
    from lib_umc import key_cabinet
    rng = _rng(seed)
    cw, ch, cols, rows = 14, 12, 6, 3
    px0 = x + 4
    cv.rect(px0 - 2, y - 2, cols * cw + 3, rows * ch + 3, OUT)
    for r in range(rows):
        for c in range(cols):
            bx, by = px0 + c * cw, y + r * ch
            cv.rect(bx, by, cw - 1, ch - 1, WOOD[1]); cv.rect(bx + 1, by + 1, cw - 3, ch - 2, "#2a1a16")
            cv.hline(bx, by + ch - 2, cw - 1, WOOD[4])
            if rng.random() < 0.7:
                pw, ph = int(rng.integers(6, 11)), int(rng.integers(4, 8))
                cv.rect(bx + 2, by + ch - 2 - ph, pw, ph, CARD[3]); cv.hline(bx + 2, by + ch - 2 - ph, pw, CARD[4])
                cv.rect(bx + 2 + pw // 2, by + ch - 2 - ph, 1, ph, C("#d8c8a0", 0.6))
            elif rng.random() < 0.5:
                cv.rect(bx + 2, by + 4, 9, 6, "#f2ecdc"); cv.rect(bx + 3, by + 5, 3, 2, "#c84a3c")
    key_cabinet(cv, px0 + cols * cw + 8, y + 2, w=24, h=26, open_=False)
    s = "FRONT DESK"
    sw = text_width(s) + 10
    sx = x + w // 2 - sw // 2
    cv.rect(sx, y - 20, sw, 13, OUT); cv.rect(sx + 1, y - 19, sw - 2, 11, BRASS_FH[2]); cv.rect(sx + 2, y - 18, sw - 4, 9, "#2a2230")
    text(cv, s, sx + 5, y - 19, BRASS_FH[4])


def bunting(cv, x0, y0, x1, y1, sag=10, letters="WELCOME", cols=CPAPER[:6]):
    """A string of paper pennants, one letter on each."""
    n = len(letters)
    pts = []
    for i in range(x1 - x0 + 1):
        t = i / max(1, x1 - x0)
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        cv.px(x0 + i, int(round(y)), "#2a2030")
        pts.append((x0 + i, y))
    for k, ch in enumerate(letters):
        t = (k + 0.5) / n
        px_, py_ = pts[int(t * (len(pts) - 1))]
        py_ = int(round(py_))
        c = cols[k % len(cols)]
        cv.poly([(px_ - 5, py_), (px_ + 5, py_), (px_, py_ + 13)], OUT)
        cv.poly([(px_ - 4, py_ + 1), (px_ + 4, py_ + 1), (px_, py_ + 11)], c)
        micro_text(cv, ch, px_ - 1, py_ + 2, "#2a2030")


def lost_socks(cv, x, y, w=54, h=34, seed=0):
    """The laundry room's LOST SOCKS board: odd socks pinned to cork, each one a different pattern."""
    rng = _rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT); cv.rect(x - 1, y - 1, w + 2, h + 2, WOOD[3])
    cork_surface(cv, x, y, w, h, seed=seed)
    s = "LOST SOCKS"
    cv.rect(x + w // 2 - micro_width(s) // 2 - 2, y + 2, micro_width(s) + 4, 7, "#f2ecdc")
    micro_text(cv, s, x + w // 2 - micro_width(s) // 2, y + 3, "#c84a3c")
    for k in range(6):
        sx, sy = x + 4 + k * 8 + int(rng.integers(-1, 2)), y + 12 + (k % 2) * 4
        c = ["#e6e2d6", "#c84a3c", "#3a5aa8", "#e8c24a", "#5c897c", "#c890d0"][k]
        cv.rect(sx, sy, 4, 11, OUT); cv.rect(sx + 1, sy, 2, 10, c)
        cv.rect(sx + 1, sy + 9, 5, 4, OUT); cv.rect(sx + 2, sy + 9, 3, 3, c)
        if k % 2:
            for yy in range(sy + 2, sy + 9, 3):
                cv.hline(sx + 1, yy, 2, shade(c, -0.35))
        cv.px(sx + 2, sy, "#c84a3c")


# ---------------------------------------------------------------------------- D03 props
def front_desk(width=140, height=52, seed=0):
    """The front desk: a curved-cornered birch counter on a sandstone plinth, a bell, the sign-in
    clipboard, a stack of room keys in envelopes, a desk lamp and a MOVE-IN tent card."""
    cv = Canvas(width + 8, height + 20, seed=seed)
    ox, base = 4, height + 16
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    top = base - 40
    cv.rect(ox, top, width, 40, OUT)
    cv.rect(ox + 1, base - 7, width - 2, 6, FH_SAND[3]); cv.hline(ox + 1, base - 7, width - 2, FH_SAND[5])
    for k in range(ox + 1, ox + width - 1, 3):                     # vertical birch slats
        cv.vline(k, top + 6, 27, BIRCH[4] if (k // 3) % 3 else BIRCH[5])
        cv.vline(k + 2, top + 6, 27, BIRCH[3])
    cv.rect(ox - 2, top - 2, width + 4, 8, OUT); cv.rect(ox - 1, top - 1, width + 2, 6, WOOD[4])
    cv.hline(ox - 1, top - 1, width + 2, WOOD[5]); cv.hline(ox - 1, top + 4, width + 2, WOOD[2])
    s = "WELCOME"
    cv.rect(ox + width // 2 - 26, top + 12, 52, 13, OUT); cv.rect(ox + width // 2 - 25, top + 13, 50, 11, "#2a2230")
    text(cv, s, ox + width // 2 - text_width(s) // 2, top + 14, BRASS_FH[4])
    # on top
    cv.rect(ox + 10, top - 12, 3, 10, OUT); cv.poly([(ox + 5, top - 12), (ox + 17, top - 12), (ox + 14, top - 18), (ox + 8, top - 18)], "#3e6e68")
    cv.rect(ox + 6, top - 11, 11, 2, C("#fff0c4", 0.7))
    cv.rect(ox + 30, top - 5, 14, 5, "#e6dcc0"); cv.rect(ox + 32, top - 7, 10, 3, CHROME[3])          # clipboard
    cv.ellipse(ox + 52, top - 7, 9, 7, BRASS_FH[3]); cv.px(ox + 56, top - 8, BRASS_FH[4]); cv.px(ox + 56, top - 9, OUT)   # bell
    for k in range(4):                                                                                  # key envelopes
        cv.rect(ox + 70 + k * 2, top - 6 + k, 12, 4, ["#f2ecdc", "#e8c24a", "#f2ecdc", "#8aa8e0"][k])
    cv.rect(ox + width - 50, top - 12, 34, 9, OUT); cv.rect(ox + width - 49, top - 11, 32, 7, "#f2ecdc")
    micro_text(cv, "MOVE-IN", ox + width - 48, top - 10, "#c84a3c")
    return cv, ox + width // 2, base


def couch_back(width=112, height=36, seed=0):
    """A mid-century couch seen from behind: teal vinyl back with button tufting, walnut legs and
    arms, a knitted throw over one end."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    for lx in (ox + 6, ox + width - 9):
        cv.rect(lx, base - 5, 3, 5, OUT); cv.vline(lx + 1, base - 5, 4, WOOD[4])
    cv.rect(ox, base - 32, width, 28, OUT)
    cv.rect(ox + 1, base - 31, width - 2, 26, VINYL_T[2]); cv.hline(ox + 1, base - 31, width - 2, VINYL_T[4])
    cv.hline(ox + 1, base - 30, width - 2, VINYL_T[3]); cv.hline(ox + 1, base - 7, width - 2, VINYL_T[1])
    for k in range(ox + 12, ox + width - 8, 14):
        for yy in (base - 24, base - 15):
            cv.px(k + (7 if yy == base - 15 else 0), yy, VINYL_T[0]); cv.px(k + 1 + (7 if yy == base - 15 else 0), yy, VINYL_T[3])
    for ax in (ox, ox + width - 7):                                # walnut arm caps
        cv.rect(ax, base - 34, 7, 30, OUT); cv.rect(ax + 1, base - 33, 5, 28, WOOD[3]); cv.vline(ax + 1, base - 33, 28, WOOD[5])
    cv.rect(ox + width - 34, base - 33, 24, 18, OUT)                # the throw
    cv.rect(ox + width - 33, base - 32, 22, 16, MUSTARD[3])
    for yy in range(base - 30, base - 16, 3):
        cv.hline(ox + width - 33, yy, 22, MUSTARD[2])
    for k in range(ox + width - 32, ox + width - 11, 3):
        cv.vline(k, base - 16, 3, MUSTARD[4])
    return cv, ox + width // 2, base


def armchair(width=40, height=40, seed=0, facing=1):
    """A low mid-century armchair seen three-quarter from the side, mustard cushion, walnut frame."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3)
    for lx in (ox + 4, ox + width - 7):
        cv.line(lx + 1, base - 9, lx, base, OUT); cv.line(lx + 2, base - 9, lx + 1, base, WOOD[3])
    cv.rect(ox + 1, base - 18, width - 2, 10, OUT); cv.rect(ox + 2, base - 17, width - 4, 8, MUSTARD[3])
    cv.hline(ox + 2, base - 17, width - 4, MUSTARD[4]); cv.hline(ox + 2, base - 10, width - 4, MUSTARD[1])
    bx = ox + (width - 12 if facing > 0 else 0)
    cv.rect(bx, base - 38, 12, 26, OUT); cv.rect(bx + 1, base - 37, 10, 24, MUSTARD[2]); cv.vline(bx + 1, base - 37, 24, MUSTARD[4])
    for yy in range(base - 34, base - 14, 6):
        cv.px(bx + 5, yy, MUSTARD[1])
    cv.rect(ox, base - 22, width, 3, OUT); cv.hline(ox + 1, base - 21, width - 2, WOOD[4])
    return cv, ox + width // 2, base


def coffee_table(width=60, height=20, seed=0):
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    for lx in (ox + 4, ox + width - 6):
        cv.line(lx, base - 9, lx - 1, base, OUT); cv.line(lx + 1, base - 9, lx, base, WOOD[4])
    cv.rect(ox, base - 14, width, 6, OUT); cv.rect(ox + 1, base - 13, width - 2, 4, WOOD[3]); cv.hline(ox + 1, base - 13, width - 2, WOOD[5])
    cv.rect(ox + 6, base - 17, 14, 4, "#c84a3c"); cv.rect(ox + 8, base - 19, 12, 3, "#e6dcc0")          # magazines
    cv.ellipse(ox + width - 16, base - 18, 8, 5, "#e8e2d6"); cv.px(ox + width - 12, base - 17, "#6a3a20")  # a mug
    cv.rect(ox + 26, base - 16, 12, 3, "#3a5aa8")                                                      # a campus map
    return cv, ox + width // 2, base


def floor_lamp_fh(height=64):
    """A tall brass floor lamp with a pleated drum shade (the lobby's rest-and-save light)."""
    w = 24
    cv = Canvas(w, height + 4, seed=19)
    cx, base = w // 2, height + 1
    ground_shadow(cv, cx, base, 8, 2)
    cv.ellipse(cx - 6, base - 3, 13, 4, OUT); cv.ellipse(cx - 5, base - 3, 11, 3, BRASS_FH[2])
    cv.rect(cx - 1, 14, 2, base - 16, BRASS_FH[2]); cv.vline(cx - 1, 14, base - 16, BRASS_FH[4])
    cv.rect(cx - 2, 30, 4, 2, BRASS_FH[3])
    cv.poly([(cx - 7, 1), (cx + 6, 1), (cx + 9, 15), (cx - 10, 15)], OUT)
    cv.poly([(cx - 6, 2), (cx + 5, 2), (cx + 8, 14), (cx - 9, 14)], "#e9a84a")
    cv.poly([(cx - 5, 3), (cx + 1, 3), (cx + 3, 13), (cx - 7, 13)], "#f6cd78")
    for k in range(cx - 8, cx + 8, 3):
        cv.vline(k, 4, 10, C("#c47a2c", 0.5))
    cv.hline(cx - 9, 14, 18, "#c47a2c")
    return cv, cx, base


def washer(width=40, height=46, seed=0, lid_open=False):
    """A white top-loading coin-op washer: control backsplash with a dial and a coin slide."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    top = base - height
    cv.rect(ox, top, width, 10, OUT); cv.rect(ox + 1, top + 1, width - 2, 8, "#d8dce4"); cv.hline(ox + 1, top + 1, width - 2, "#f2f4f8")
    cv.ellipse(ox + 5, top + 3, 5, 5, "#5a5c6a"); cv.px(ox + 7, top + 4, "#e8e8f0")
    cv.rect(ox + width - 16, top + 3, 11, 4, CHROME[2]); cv.rect(ox + width - 15, top + 4, 9, 2, CHROME[4])
    cv.rect(ox + 13, top + 3, 8, 3, "#2a3a2a"); cv.px(ox + 14, top + 4, "#7ae0a0")
    cv.rect(ox, top + 10, width, height - 10, OUT)
    cv.rect(ox + 1, top + 10, width - 2, 8, "#e6e8ee"); cv.hline(ox + 1, top + 10, width - 2, "#ffffff")
    if lid_open:
        cv.rect(ox + 4, top + 4, width - 8, 7, "#c8ccd6"); cv.rect(ox + 6, top + 12, width - 12, 5, "#3a4050")
    else:
        cv.rect(ox + 4, top + 12, width - 8, 5, "#d0d4dc"); cv.hline(ox + 4, top + 12, width - 8, "#f6f8fc")
    cv.rect(ox + 1, top + 18, width - 2, height - 20, "#c8ccd6"); cv.vline(ox + 1, top + 18, height - 20, "#e2e4ea")
    cv.vline(ox + width - 2, top + 18, height - 20, "#a8acb8")
    cv.rect(ox + 1, base - 4, width - 2, 3, "#8a8e9a")
    # the coin meter on the front and a strip of instructions
    mx = ox + width // 2 - 6
    cv.rect(mx, top + 22, 12, 9, OUT); cv.rect(mx + 1, top + 23, 10, 7, CHROME[3]); cv.hline(mx + 1, top + 23, 10, CHROME[4])
    cv.rect(mx + 3, top + 25, 6, 1, OUT); cv.rect(mx + 4, top + 27, 4, 2, "#e8c24a")
    cv.rect(ox + 5, top + 34, width - 10, 2, "#a8acb8")
    return cv, ox + width // 2, base


def dryer_stack(width=46, height=94, seed=0):
    """Two coin-op dryers stacked: round chrome-ringed porthole doors, the lower one dark, the upper
    one lit inside (its tumbling clothes are an animated layer). Returns the upper window centre too."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    top = base - height
    half = height // 2
    wins = []
    for k in range(2):
        y0 = top + k * half
        cv.rect(ox, y0, width, half, OUT)
        cv.rect(ox + 1, y0 + 1, width - 2, half - 2, "#d8dce4"); cv.hline(ox + 1, y0 + 1, width - 2, "#f2f4f8")
        cv.rect(ox + 1, y0 + 1, width - 2, 7, "#c8ccd6"); cv.hline(ox + 1, y0 + 8, width - 2, "#a8acb8")
        cv.rect(ox + width - 16, y0 + 3, 11, 3, CHROME[2]); cv.rect(ox + 4, y0 + 3, 6, 3, "#2a2a36")
        cv.px(ox + 5, y0 + 4, "#ff5a4a" if k == 0 else "#3a3a46")
        wcx, wcy, r = ox + width // 2, y0 + 9 + (half - 10) // 2, 13
        cv.ellipse(wcx - r - 1, wcy - r - 1, 2 * r + 3, 2 * r + 3, OUT)
        cv.ellipse(wcx - r, wcy - r, 2 * r + 1, 2 * r + 1, CHROME[3])
        cv.ellipse(wcx - r + 2, wcy - r + 2, 2 * r - 3, 2 * r - 3, CHROME[1])
        inner = "#7a5a3e" if k == 0 else "#20222e"
        cv.ellipse(wcx - r + 3, wcy - r + 3, 2 * r - 5, 2 * r - 5, inner)
        if k == 0:
            cv.ellipse(wcx - r + 4, wcy - r + 4, 2 * r - 7, 2 * r - 7, "#a8784a")
        cv.line(wcx - 6, wcy + 5, wcx - 1, wcy - 6, C("#ffffff", 0.35))
        cv.rect(wcx + r - 1, wcy - 3, 3, 6, CHROME[2])
        wins.append((wcx, wcy, r - 4))
    return cv, ox + width // 2, base, wins


def tumble_frames(r=9, n=4, seed=0):
    """Clothes tumbling in a lit drum: n frames of a few coloured lumps rotated round the drum."""
    frames = []
    cols = ["#c84a3c", "#e6e2d6", "#3a5aa8", "#e8c24a", "#5c897c"]
    for f in range(n):
        cv = Canvas(2 * r + 1, 2 * r + 1)
        for k, c in enumerate(cols):
            a = f * (np.pi / 2) / 1.0 + k * 1.25
            rr = r * (0.35 + 0.12 * (k % 3))
            x = r + int(round(np.cos(a) * rr)); y = r + int(round(np.sin(a) * rr)) + 1
            cv.ellipse(x - 3, y - 2, 6, 5, shade(c, -0.25)); cv.ellipse(x - 2, y - 2, 4, 3, c)
        m = np.zeros((2 * r + 1, 2 * r + 1), bool)
        yy, xx = np.mgrid[0:2 * r + 1, 0:2 * r + 1]
        cv.a[((xx - r) ** 2 + (yy - r) ** 2) > r * r] = 0
        frames.append(cv)
    return frames


def vending_soap(width=30, height=70, seed=0):
    """A laundry-soap vending machine: lit front with little boxes behind glass, coin slot."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    top = base - height
    cv.rect(ox, top, width, height, OUT)
    cv.rect(ox + 1, top + 1, width - 2, height - 2, "#3a5aa8"); cv.hline(ox + 1, top + 1, width - 2, "#5a7ac8")
    cv.rect(ox + 3, top + 4, width - 6, 9, "#f2ecdc"); micro_text(cv, "SOAP", ox + width // 2 - micro_width("SOAP") // 2, top + 6, "#3a5aa8")
    cv.rect(ox + 3, top + 15, width - 12, 36, "#e8e2c8")
    for r in range(4):
        for c in range(3):
            cv.rect(ox + 5 + c * 6, top + 18 + r * 9, 4, 6, ["#e07a5a", "#5cb0a0", "#e8c24a"][(r + c) % 3])
            cv.hline(ox + 5 + c * 6, top + 18 + r * 9, 4, "#ffffff")
        cv.hline(ox + 4, top + 24 + r * 9, width - 14, "#a8a090")
    cv.rect(ox + width - 8, top + 17, 4, 10, CHROME[3]); cv.rect(ox + width - 7, top + 19, 2, 3, OUT)
    cv.rect(ox + 4, base - 14, width - 8, 7, "#1e2a5a")
    return cv, ox + width // 2, base


def folding_table_fh(width=120, height=34, seed=0):
    """The laundry room's long folding table with stacks of folded clothes and a dryer sheet box."""
    cv = Canvas(width + 6, height + 16, seed=seed)
    ox, base = 3, height + 12
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - 22
    for lx in (ox + 4, ox + width - 7):
        cv.rect(lx, top + 4, 3, base - top - 4, OUT); cv.vline(lx + 1, top + 4, base - top - 5, CHROME[2])
    cv.rect(ox, top - 1, width, 7, OUT); cv.rect(ox + 1, top, width - 2, 5, "#c8c0b0"); cv.hline(ox + 1, top, width - 2, "#e6dece")
    cv.hline(ox + 1, top + 4, width - 2, "#8a8478")
    rng = _rng(seed)
    x = ox + 8
    for k in range(4):
        c = ["#3a5aa8", "#e6e2d6", "#c84a3c", "#5c897c"][k]
        n = int(rng.integers(2, 5))
        for j in range(n):
            cv.rect(x, top - 3 - j * 3, 16, 3, OUT); cv.rect(x + 1, top - 3 - j * 3, 14, 2, shade(c, 0.1 * (j % 2)))
        x += 22
    cv.rect(ox + width - 18, top - 7, 11, 7, OUT); cv.rect(ox + width - 17, top - 6, 9, 5, "#e07a5a"); cv.hline(ox + width - 17, top - 6, 9, "#f2a08a")
    return cv, ox + width // 2, base


def wire_cart(width=34, height=38, seed=0):
    """A rolling wire laundry cart with a hanging rail, a shirt on a hanger."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    for wx in (ox + 2, ox + width - 5):
        cv.rect(wx, base - 3, 4, 3, OUT)
    bt = base - 22
    cv.rect(ox, bt, width, 17, OUT)
    for k in range(ox + 1, ox + width - 1, 3):
        cv.vline(k, bt + 1, 15, CHROME[3])
    for yy in range(bt + 1, bt + 16, 4):
        cv.hline(ox + 1, yy, width - 2, CHROME[2])
    cv.rect(ox + 2, bt + 2, width - 4, 6, "#c890d0")                # clothes inside
    for px_ in (ox + 1, ox + width - 2):
        cv.vline(px_, base - height, height - 5, CHROME[1])
    cv.hline(ox + 1, base - height, width - 2, CHROME[3])
    cv.line(ox + 14, base - height, ox + 17, base - height + 4, CHROME[4])
    cv.poly([(ox + 9, base - height + 5), (ox + 25, base - height + 5), (ox + 23, bt - 1), (ox + 11, bt - 1)], OUT)
    cv.poly([(ox + 10, base - height + 6), (ox + 24, base - height + 6), (ox + 22, bt - 2), (ox + 12, bt - 2)], "#e8c24a")
    return cv, ox + width // 2, base


def ping_pong(width=112, height=40, seed=0):
    """The lobby's ping-pong table: green top with white lines, the net, two paddles and a ball."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    top = base - 30
    for lx in (ox + 8, ox + width - 11, ox + width // 2 - 2):
        cv.rect(lx, top + 10, 3, base - top - 10, OUT); cv.vline(lx + 1, top + 10, base - top - 11, CHROME[1])
    cv.rect(ox, top, width, 12, OUT)
    cv.rect(ox + 1, top + 1, width - 2, 9, "#2e6a4a"); cv.hline(ox + 1, top + 1, width - 2, "#3e8a62")
    cv.rect(ox + 1, top + 9, width - 2, 2, "#1e4a32")
    cv.hline(ox + 2, top + 1, width - 4, "#f2f2ea"); cv.hline(ox + 2, top + 8, width - 4, "#e6e6de")
    cv.vline(ox + 2, top + 1, 8, "#f2f2ea"); cv.vline(ox + width - 3, top + 1, 8, "#f2f2ea")
    cv.hline(ox + 3, top + 5, width - 6, C("#f2f2ea", 0.7))
    cx = ox + width // 2
    cv.rect(cx - 1, top - 5, 3, 15, OUT); cv.rect(cx, top - 4, 1, 13, "#e6e6de")
    for yy in range(top - 4, top + 9, 2):
        cv.px(cx - 1, yy, "#8a8a98"); cv.px(cx + 1, yy, "#8a8a98")
    for (px_, c) in ((ox + 22, "#c84a3c"), (ox + width - 30, "#2a2a36")):
        cv.ellipse(px_, top + 2, 7, 6, OUT); cv.ellipse(px_ + 1, top + 3, 5, 4, c); cv.rect(px_ + 6, top + 4, 4, 2, WOOD[4])
    cv.ellipse(cx + 16, top + 3, 3, 3, "#f6f2e6")
    return cv, ox + width // 2, base


def plastic_chairs(width=84, height=36, count=3, seed=0):
    """A row of moulded plastic chairs bolted to a steel beam, seen from the front."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 2)
    for lx in (ox + 6, ox + width - 9):
        cv.rect(lx, base - 12, 3, 12, OUT); cv.vline(lx + 1, base - 12, 11, CHROME[2])
    cv.rect(ox + 2, base - 15, width - 4, 4, OUT); cv.hline(ox + 3, base - 14, width - 6, CHROME[3])
    cw = width // count
    cols = ["#e07a5a", "#5cb0a0", "#e8c24a"]
    for i in range(count):
        x = ox + i * cw + 2
        c = cols[(i + seed) % 3]
        cv.rect(x, base - 34, cw - 4, 16, OUT); cv.rect(x + 1, base - 33, cw - 6, 14, c)
        cv.hline(x + 1, base - 33, cw - 6, shade(c, 0.25)); cv.rect(x + 3, base - 30, cw - 10, 2, shade(c, -0.2))
        cv.rect(x - 1, base - 20, cw - 2, 6, OUT); cv.rect(x, base - 19, cw - 4, 4, shade(c, -0.1)); cv.hline(x, base - 19, cw - 4, shade(c, 0.2))
    return cv, ox + width // 2, base


def wet_floor_sign(width=18, height=26):
    cv = Canvas(width + 4, height + 4, seed=5)
    ox, base = 2, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    cv.poly([(ox + 2, base), (ox + width // 2 - 2, base - height), (ox + width // 2 + 2, base - height), (ox + width - 2, base)], OUT)
    cv.poly([(ox + 3, base - 1), (ox + width // 2 - 1, base - height + 1), (ox + width // 2 + 1, base - height + 1), (ox + width - 3, base - 1)], "#e8c24a")
    cv.rect(ox + width // 2 - 4, base - 16, 8, 7, "#2a2030"); cv.rect(ox + width // 2 - 3, base - 15, 6, 5, "#e8c24a")
    cv.px(ox + width // 2, base - 14, "#2a2030"); cv.rect(ox + width // 2 - 1, base - 13, 2, 2, "#2a2030")
    return cv, ox + width // 2, base


def upright_piano(width=56, height=46, seed=0):
    """The lobby's old upright piano, seen from the front: walnut case, a hinged lid with a stack of
    sheet music and a mug on it, the music desk with an open book, the keyboard, brass pedals and a
    bench pulled out to one side."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    pw = width - 14                                        # the piano itself; the bench sits to the right
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3)
    top = base - 40
    # case
    cv.rect(ox, top, pw, 40, OUT)
    cv.rect(ox + 1, top + 1, pw - 2, 38, WOOD[2]); cv.vline(ox + 1, top + 1, 38, WOOD[4])
    cv.vline(ox + pw - 2, top + 1, 38, WOOD[1])
    cv.rect(ox - 1, top - 2, pw + 2, 4, OUT); cv.rect(ox, top - 1, pw, 2, WOOD[3]); cv.hline(ox, top - 1, pw, WOOD[5])
    # upper panel: two carved recesses and the music desk with an open book
    for px_ in (ox + 4, ox + pw // 2 + 1):
        cv.rect(px_, top + 3, pw // 2 - 5, 11, WOOD[1]); cv.hline(px_, top + 3, pw // 2 - 5, WOOD[0]); cv.hline(px_, top + 13, pw // 2 - 5, WOOD[3])
    cv.rect(ox + 8, top + 7, pw - 16, 9, OUT)
    cv.rect(ox + 9, top + 8, (pw - 18) // 2, 7, "#f2ecdc"); cv.rect(ox + 10 + (pw - 18) // 2, top + 8, (pw - 18) // 2, 7, "#e6dcc0")
    for yy in range(top + 9, top + 14, 2):                 # staves
        cv.hline(ox + 10, yy, (pw - 20) // 2, "#8a8478"); cv.hline(ox + 11 + (pw - 18) // 2, yy, (pw - 20) // 2, "#8a8478")
    cv.hline(ox + 6, top + 16, pw - 12, WOOD[4])
    # keyboard: key slip, white keys with the black-key pattern, the fallboard lip above it
    ky = top + 18
    cv.rect(ox + 2, ky - 1, pw - 4, 2, WOOD[0])
    cv.rect(ox + 2, ky + 1, pw - 4, 5, "#f2eee2"); cv.hline(ox + 2, ky + 5, pw - 4, "#c8c0b0")
    for k, xx in enumerate(range(ox + 3, ox + pw - 3, 2)):
        if k % 7 not in (2, 6):
            cv.rect(xx, ky + 1, 1, 3, "#1e1a22")
    cv.rect(ox + 1, ky + 6, pw - 2, 2, WOOD[3]); cv.hline(ox + 1, ky + 6, pw - 2, WOOD[5])
    # lower panel, toe blocks and pedals
    cv.rect(ox + 4, ky + 9, pw - 8, 10, WOOD[1]); cv.hline(ox + 4, ky + 9, pw - 8, WOOD[0])
    for px_ in (ox + pw // 2 - 6, ox + pw // 2 - 1, ox + pw // 2 + 4):
        cv.rect(px_, base - 4, 3, 2, BRASS_FH[3]); cv.px(px_, base - 4, BRASS_FH[4])
    cv.rect(ox, base - 2, pw, 2, WOOD[0])
    # on the lid: sheet music, a mug, a little paper sign
    cv.rect(ox + 4, top - 5, 13, 3, "#f2ecdc"); cv.rect(ox + 5, top - 7, 11, 2, "#e6dcc0")
    cv.rect(ox + pw - 12, top - 7, 5, 5, OUT); cv.rect(ox + pw - 11, top - 6, 3, 4, "#c84a3c"); cv.px(ox + pw - 7, top - 5, OUT)
    cv.rect(ox + pw // 2 - 4, top - 9, 9, 7, OUT); cv.rect(ox + pw // 2 - 3, top - 8, 7, 5, CPAPER[0])
    cv.hline(ox + pw // 2 - 2, top - 6, 5, "#2a2030")
    # the bench, pulled out to the right
    bx = ox + pw + 1
    cv.rect(bx, base - 14, 13, 5, OUT); cv.rect(bx + 1, base - 13, 11, 3, WOOD[3]); cv.hline(bx + 1, base - 13, 11, WOOD[5])
    for lx in (bx + 1, bx + 10):
        cv.rect(lx, base - 9, 2, 9, OUT); cv.vline(lx, base - 9, 8, WOOD[3])
    return cv, ox + width // 2, base


def puddle(cv, cx, cy, w=30, h=7, seed=0):
    """A flat spill of soapy water on the lino: a pale blue sheen with a bright rim and a few suds."""
    rng = _rng(seed)
    cv.ellipse(cx - w // 2, cy - h // 2, w, h, C("#a8c4e0", 0.35))
    cv.ellipse(cx - w // 2 + 4, cy - h // 2 + 1, w - 12, h - 3, C("#d8e8f6", 0.3))
    cv.ellipse(cx + w // 2 - 6, cy - 1, 8, 4, C("#a8c4e0", 0.35))
    for _ in range(5):
        cv.px(cx + int(rng.integers(-w // 2 + 3, w // 2 - 3)), cy + int(rng.integers(-2, 3)), "#f2f6fa")
