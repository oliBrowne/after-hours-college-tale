"""Folsom Field on commencement morning (G01): the payoff after the last night.

Painted for the morning only (the game reaches G01 after dawn_started). We stand on the field
looking west down the centre aisle toward the commencement stage at the end zone. Behind it the
stadium bowl rises in the sun, every row packed with families: low end-zone stands in the middle
so the Flatirons show over the rim, the tall side stands curving up to both edges with the press
box (FOLSOM FIELD) on the left and the video board (CONGRATULATIONS / GRADUATES) on the right,
light standards at the corners, banners over the field wall, the players' tunnel. The stage: a
black drape crowned by the COMMENCEMENT banner, the university's name and seal, two rows of
faculty in robes and coloured hoods (a few chairs empty, gowns and hoods thrown over them),
fan bunting along the skirt, stairs with gold rails, urns and pots of gold and white flowers.
Floor: mown turf in crisp bands with the goal line, a five-yard line and hash marks; the black
and gold aisle runner from the podium thrust to the bottom edge; a walkway of turf-protection
tiles across the front leading to the two exits (dawn walk bottom left, tennis courts bottom
right) through gaps in the low front wall; confetti, petals, dropped programmes and a cap.
Ground shadows run up and to the right (low sun behind the viewer's left shoulder).
Props: six rows of white folding chairs with things left on them, the podium on its thrust,
the field light, a gold-and-black balloon bunch tied to the last chair of the front row.
Layers: mortarboards tossed into the air over the stands (frame blinks), falling confetti,
the stage pennants and rim flags flapping, the video board's chase lights, camera flashes in
the crowd, a cirrus strip drifting, birds and pigeons."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from surfaces import light_pool
from lib_macky2 import (title_flatirons, ridge_extend, far_range, forest_ridge, valley_haze, cirrus, _ridge, _rng)
import lib_grad as G

ROOM = "G01"
W, H = 960, 540
WALK = (20, 230, 920, 290)
FLOOR = 212                     # turf begins under the field wall
WALL = (196, FLOOR)             # padded field wall (top, base)
STAGE = (330, 630)              # stage x extent
DECK_BACK, DECK_Y, FRONT = 184, 206, 230
MOUNT = (300, 14)               # title Flatirons: left x, top y
RIM_SIDE, RIM_MID = 62, 104     # top of the side stands / of the end-zone stands
PRESS = (10, 236, 28)           # press box x0, x1, top (sits on the left rim)
BOARD = (744, 10, 172, 52)      # video board x, y, w, h
TOWERS = (292, 668)             # light standards on the corner steps
RUNNER = (440, 520)
PATH_Y = (490, 508)             # tile walkway across the front
EXITS = ((44, 106), (854, 916)) # gaps in the front wall under the thresholds
GOAL_Y, FIVE_Y = 262, 394       # goal line, five-yard line
HASH_X = (303, 657)
LAMP = (112, 470)
BALLOONS = (860, 300)
ROWS = [(250, 318), (710, 318), (250, 372), (710, 372), (250, 426), (710, 426)]
SHADOW = (0.53, -0.47)          # ground shadow direction per unit of length (up and right)
NPC_CLEAR = [(560, 480), (120, 480)]


def rim(x):
    """Top of the stands at column x: tall side stands, the low end-zone section in the middle,
    a stepped corner between."""
    if x <= 250 or x >= 710:
        return RIM_SIDE
    if 320 <= x <= 640:
        return RIM_MID
    if x < 320:
        return int(round(RIM_SIDE + (RIM_MID - RIM_SIDE) * (x - 250) / 70))
    return int(round(RIM_SIDE + (RIM_MID - RIM_SIDE) * (710 - x) / 70))


# ---------------------------------------------------------------------------------------------
# sky and mountains
# ---------------------------------------------------------------------------------------------
def sky_and_mountains(bg):
    G.morning_sky(bg, 0, 0, W, 116, seed=3)
    rng = _rng(7)
    for (cx, cy, ln) in [(250, 20, 120), (520, 8, 90), (640, 26, 110)]:
        cirrus(bg, cx, cy, ln, rng, pal=("#e8e4ea", "#f6f2f2", "#d4d0de"))
    src, ridge = title_flatirons(1.6)
    mh, mw = src.shape[:2]
    mx, my = MOUNT
    xs, far = _ridge(0, W - 1, [(0, 60), (0.2, 56), (0.3, 64), (0.6, 66), (0.7, 54), (0.8, 58), (1.0, 62)], rng, 0.7)
    far_range(bg, 0, far, 116, seed=11, pal=["#8a90b4", "#949ab8", "#a2a6bc", "#b0b0c0", "#bebac2", "#cac2c4"])
    xs, near = _ridge(0, mx, [(0, 80), (0.3, 72), (0.6, 64), (0.85, 58), (1.0, my + ridge[0])], rng, 0.6)
    forest_ridge(bg, 0, near[:mx], 120, seed=12)
    bg.paste(src, mx, my)
    xs, right = _ridge(mx + mw, W - 1, [(0, my + ridge[-1]), (0.3, 84), (1.0, 92)], rng, 0.5)
    right_img = ridge_extend(src, ridge, np.round(right).astype(int), 120, seed=13, block=(60, 90), haze="#b0a0b4", haze_amt=0.2)
    bg.paste(right_img, mx + mw, 0)
    valley_haze(bg, 0, W, 88, 116, colour="#e0d4d0", alpha=(0.12, 0.22, 0.34), seed=5)


# ---------------------------------------------------------------------------------------------
# the stadium
# ---------------------------------------------------------------------------------------------
def stadium(bg):
    info = G.stands(bg, rim, WALL[0], x0=0, x1=W, pitch=5, bow=10,
                    aisles=(40, 118, 196, 274, 346, 420, 540, 614, 686, 764, 842, 920),
                    concourse=(14, (78, 158, 236, 724, 802, 880)), seed=21,
                    zones=[(766, 960, 0, 12, [G.GOLD[3], G.GOLD[4], G.BLACK[1]], [5, 2, 2], 0.85),     # the gold-out block
                           (0, 118, 16, 30, [G.BLACK[1], G.BLACK[2], G.GOLD[3], "#f4f2ec"], [4, 2, 2, 1], 0.6)])
    # parapets along the rims (the end-zone one carries flag poles), the corner steps
    G.rim_parapet(bg, 318, 643, RIM_MID - 4)
    G.rim_parapet(bg, 0, 252, RIM_SIDE - 4, rail=False)
    G.rim_parapet(bg, 708, W, RIM_SIDE - 4, rail=False)
    for (a, b, sgn) in ((250, 320, 1), (640, 710, -1)):
        for x in range(a, b + 1):
            y = rim(x)
            bg.rect(x, y - 4, 1, 5, G.RISER[3]); bg.px(x, y - 4, G.RISER[5]); bg.px(x, y, G.RISER[1])
    # press box on the left rim, video board on the right
    G.press_box(bg, PRESS[0], PRESS[1], PRESS[2], RIM_SIDE - 2)
    bx, by, bw, bh = BOARD
    screen = G.scoreboard(bg, bx, by, bw, bh, legs_to=RIM_SIDE + 2)
    for tx in TOWERS:
        G.light_tower(bg, tx, 22, rim(tx) - 2)
    return info, screen


def rim_flags(cv, wave=0):
    """Small CU flags on poles along the end-zone rim (gold, black, white in turn)."""
    pts = []
    for i, x in enumerate(range(334, 630, 26)):
        if 392 <= x <= 568:          # hidden behind the stage banner anyway; keep the rim simple there
            pass
        top = RIM_MID - 18
        cv.vline(x, top, 14, G.STEEL[3]); cv.px(x, top - 1, G.GOLD[4])
        col = [G.GOLD[3], G.BLACK[1], "#f4f2ec"][i % 3]
        for k in range(4):
            ln = 7 - (k // 2) + (wave if k in (1, 2) else 0)
            cv.hline(x + 1, top + k, ln, col if k else shade(col, 0.15))
        cv.px(x + 7 + wave, top + 2 + (1 if wave else 0), shade(col, -0.25))
        pts.append((x, top))
    return pts


def field_wall_and_banners(bg):
    G.field_wall(bg, 0, W, WALL[0], WALL[1])
    G.tunnel(bg, 70, WALL[1], w=34, h=22)
    G.stand_banner(bg, 110, 184, "CONGRATS GRADS", bg="#f4f2ec", fg=G.BLACK[1], edge="#b8b0a0")
    G.stand_banner(bg, 214, 186, "SKO BUFFS")
    G.stand_banner(bg, 678, 184, "WE ARE SO PROUD", bg=G.BLACK[1], fg=G.GOLD[3], edge=G.BLACK[0])
    G.stand_banner(bg, 792, 186, "GO BUFFS")
    G.stand_banner(bg, 866, 184, "CU", bg="#f4f2ec", fg=G.BLACK[1], edge="#b8b0a0", pad=6)


# ---------------------------------------------------------------------------------------------
# floor
# ---------------------------------------------------------------------------------------------
def chair_xs(cx, width=300, n=10, cw=16):
    """Left edges of the chairs in a row prop centred on cx (matches lib_grad.white_chair_row)."""
    ox = cx - width // 2
    pitch = width / n
    return [int(round(ox + i * pitch + pitch / 2)) - cw // 2 for i in range(n)]


def shadow_mask():
    from PIL import Image, ImageDraw
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    dx, dy = SHADOW

    def cast(poly_base, length):
        a, b = poly_base
        d.polygon([a, b, (b[0] + dx * length, b[1] + dy * length), (a[0] + dx * length, a[1] + dy * length)], fill=255)

    for (cx, by) in ROWS:
        for x in chair_xs(cx):
            # the back panel throws a band; legs throw thin lines
            cast(((x + 1, by - 2), (x + 15, by - 2)), 24)
    # podium thrust, the lamp, the balloon bunch
    cast(((458, 245), (504, 245)), 40)
    cast(((LAMP[0] - 2, LAMP[1]), (LAMP[0] + 2, LAMP[1])), 70)
    cast(((BALLOONS[0] - 1, BALLOONS[1]), (BALLOONS[0] + 1, BALLOONS[1])), 40)     # the ribbon's thin shadow
    sh = np.array(img) > 0
    sh[:FRONT] = False
    return sh


def floor(bg, sh):
    fl = np.zeros((H, W), bool)
    fl[FLOOR:, :] = True
    shade_cv = Canvas(W, H)
    for cv, pal in ((bg, G.TURF_SUN), (shade_cv, G.TURF_SHADE)):
        G.turf(cv, 0, FLOOR, W, H - FLOOR, pal=pal, band=33, seed=42)
        # goal line, five-yard line, hash marks
        G.paint_line(cv, 0, GOAL_Y, W, 3, seed=1)
        G.paint_line(cv, 0, FIVE_Y, W, 2, seed=2)
        for hx in HASH_X:
            for y in range(GOAL_Y + 26, H - 20, 26):
                if abs(y - FIVE_Y) < 6:
                    continue
                G.paint_line(cv, hx - 4, y, 9, 1, seed=y + hx)
        # sideline ticks at both screen edges (the yard marks)
        for y in range(GOAL_Y + 26, H - 20, 26):
            G.paint_line(cv, 22, y, 5, 1, seed=y); G.paint_line(cv, W - 27, y, 5, 1, seed=y + 1)
    tint = shade_cv.a.copy()
    bg.a[sh] = tint[sh]
    # walkway of turf tiles across the front and down through both exits
    path = np.zeros((H, W), bool)
    path[PATH_Y[0]:PATH_Y[1], 8:W - 8] = True
    for (a, b) in EXITS:
        path[PATH_Y[0]:, a:b] = True
    G.tile_path(bg, path, size=(16, 9), seed=5)
    edge = path & ~np.roll(path, 1, axis=0)
    bg.fill_mask(edge, C("#0d0b16", 0.25))
    bot = path & ~np.roll(path, -1, axis=0)
    bg.fill_mask(bot, C("#0d0b16", 0.35))
    for col in (path & ~np.roll(path, 1, axis=1), path & ~np.roll(path, -1, axis=1)):
        bg.fill_mask(col, C("#0d0b16", 0.25))
    # the shadows reach over the tiles too
    bg.fill_mask(sh & path, C("#1a2a3a", 0.35))
    # aisle runner from the thrust to the bottom edge
    G.runner(bg, RUNNER[0], RUNNER[1], FRONT, H, seed=6)
    bg.fill_mask(sh & (np.arange(W)[None, :] >= RUNNER[0]) & (np.arange(W)[None, :] < RUNNER[1]), C("#0d0b16", 0.3))
    # a crisp darker edge where each shadow begins
    from scipy import ndimage
    sedge = sh & ~ndimage.binary_erosion(sh)
    bg.fill_mask(sedge & fl, C("#0d0b16", 0.1))
    return path


def end_zone_words(bg):
    """COLORADO and BUFFALOES painted in the end zone either side of the stage: black letters
    with a gold keyline, grass blades showing through the paint here and there."""
    from lib_macky import stencil_text
    for (word, cx) in (("COLORADO", 166), ("BUFFALOES", 752)):
        tw = len(word) * 18
        x, y = cx - tw // 2, 228
        tmp = Canvas(W, H)
        stencil_text(tmp, word, x, y, "#ffffff", scale=3)
        m = tmp.a[..., 3] > 0.5
        from scipy import ndimage
        ring = ndimage.binary_dilation(m, iterations=1) & ~m
        bg.fill_mask(ring, C(G.GOLD[3], 0.9))
        bg.fill_mask(m, C(G.BLACK[1], 0.88))
        # paint wear: blades poking through in short vertical ticks (a pattern, not noise)
        ys, xs = np.where(m)
        pick = ((xs * 7 + ys * 3) % 23 == 0)
        for yy, xx in zip(ys[pick], xs[pick]):
            bg.px(xx, yy, G.TURF_SUN[3]); bg.px(xx, yy - 1, G.TURF_SUN[4])
        top = ys.min()
        bg.fill_mask(m & (np.arange(H)[:, None] == top), C(G.BLACK[3], 0.9))


def front_wall(bg):
    """The low padded wall along the near sideline (seen from behind), gaps at both exits with
    gate posts; the concourse beyond is just a strip of shadow."""
    y0 = 522
    for x in range(W):
        if any(a <= x < b for (a, b) in EXITS):
            continue
        bg.vline(x, y0, H - y0, G.BLACK[1])
        bg.px(x, y0, G.RISER[5]); bg.px(x, y0 + 1, G.RISER[3])
        bg.px(x, y0 + 5, G.GOLD[2]); bg.px(x, y0 + 6, G.GOLD[3])
        if x % 24 == 12:
            bg.vline(x, y0 + 2, H - y0 - 2, G.BLACK[0])
    for (a, b) in EXITS:
        for gx in (a - 4, b):
            bg.rect(gx, y0 - 8, 4, H - y0 + 8, G.STEEL[1]); bg.vline(gx, y0 - 8, H - y0 + 8, G.STEEL[4])
            bg.rect(gx - 1, y0 - 10, 6, 3, G.GOLD[3]); bg.hline(gx - 1, y0 - 10, 6, G.GOLD[4])
    # little gold CU plates along the wall
    for x in range(150, W - 100, 160):
        if any(a - 20 <= x <= b + 20 for (a, b) in EXITS) or RUNNER[0] - 30 <= x <= RUNNER[1] + 10:
            continue
        bg.rect(x, y0 + 9, 14, 9, G.GOLD[3]); bg.hline(x, y0 + 9, 14, G.GOLD[4]); text(bg, "CU", x + 1, y0 + 8, G.BLACK[1])


def margins(bg):
    bg.rect(0, FLOOR, WALK[0], H - FLOOR, C("#0d0b16", 0.22))
    bg.rect(WALK[0] + WALK[2], FLOOR, W - WALK[0] - WALK[2], H - FLOOR, C("#0d0b16", 0.22))
    bg.rect(0, WALK[1] + WALK[3], W, H - WALK[1] - WALK[3], C("#0d0b16", 0.25))


# ---------------------------------------------------------------------------------------------
# the stage and what stands around it
# ---------------------------------------------------------------------------------------------
def stage(bg):
    info = G.stage_set(bg, STAGE[0], STAGE[1], DECK_BACK, DECK_Y, FRONT, seed=31)
    # speakers on tripods and flower urns at the stage corners
    for sx in (298, 662):
        bg.line(sx, 214, sx - 7, 229, G.STEEL[2]); bg.line(sx, 214, sx + 7, 229, G.STEEL[2]); bg.vline(sx, 200, 29, G.STEEL[3])
        bg.rect(sx - 6, 176, 12, 26, G.INK)
        bg.rect(sx - 5, 177, 10, 24, G.BLACK[2]); bg.hline(sx - 5, 177, 10, G.BLACK[3])
        for yy in range(180, 199, 3):
            bg.hline(sx - 4, yy, 8, G.BLACK[0])
        bg.px(sx + 3, 199, "#4cc05a")
    G.flower_urn(bg, 318, 229, h=32, seed=1)
    G.flower_urn(bg, 642, 229, h=32, seed=2)
    # potted mums and hydrangeas along the foot of the skirt
    kinds = ["gold", "white", "gold", "purple", "white", "gold"]
    k = 0
    for x in range(STAGE[0] + 32, STAGE[1] - 26, 17):
        if abs(x - 480) < 30:
            continue
        G.flower_pot(bg, x, 229, kind=kinds[k % len(kinds)], w=12, h=7, seed=x)
        k += 1
    return info


def pennants(cv, wave=0):
    """Tall gold and black banners on poles at the back corners of the deck (pole behind)."""
    for px_ in (346, 613):
        cv.vline(px_ - 1, 104, DECK_BACK - 104 + 2, G.STEEL[1]); cv.vline(px_, 104, DECK_BACK - 104 + 2, G.STEEL[4])
        cv.rect(px_ - 1, 101, 3, 3, G.GOLD[3]); cv.px(px_, 100, G.GOLD[4])
    G.pennant(cv, 340, 112, 58, G.GOLD[3], G.GOLD[1], emblem=lambda c, x, y: G._torch(c, x, y, G.BLACK[1], "#c84a3c"), wave=wave)
    G.pennant(cv, 607, 112, 58, G.BLACK[1], G.GOLD[3], emblem=lambda c, x, y: G._torch(c, x, y, G.GOLD[3], "#fff2b0"), wave=-wave)


def floor_details(bg, path):
    rng = _rng(71)
    ok = np.zeros((H, W), bool)
    ok[FRONT + 2:WALK[1] + WALK[3] - 2, WALK[0]:WALK[0] + WALK[2]] = True
    for (nx, ny) in NPC_CLEAR:
        ok[ny - 8:ny + 4, nx - 14:nx + 14] = False
    # confetti: thick near the stage and the aisle, scattered between the rows
    near = ok.copy()
    G.confetti_clumps(bg, [(404, 250, 40, 8), (556, 252, 40, 8), (480, 300, 26, 7), (468, 384, 22, 6),
                           (500, 466, 20, 5), (424, 330, 18, 5), (540, 420, 18, 5), (760, 272, 22, 5),
                           (200, 272, 24, 5), (330, 474, 18, 4), (640, 340, 16, 4)], seed=1, mask=near)
    G.confetti_flat(bg, 20, FRONT + 10, 920, 270, n=90, seed=3, mask=ok)
    G.petals(bg, 480, 250, 110, 50, seed=4, mask=ok)
    # dropped programmes and a mortarboard that came down in the aisle
    for (x, y, o) in [(380, 252, False), (566, 262, True), (92, 330, False), (900, 386, True), (418, 446, False),
                      (650, 448, True), (240, 466, False), (812, 470, False), (530, 330, False)]:
        if ok[y, x]:
            G.program_flat(bg, x, y, open_=o, seed=x)
    G.cap_flat(bg, 498, 404)
    G.cap_flat(bg, 612, 276)
    # a tassel near the tile path, a gold honour cord dropped in a loop, a bouquet left on the grass
    bg.line(330, 476, 336, 478, G.GOLD[3]); bg.px(337, 478, G.GOLD[4])
    G.honour_cord(bg, 712, 462)
    G.bouquet_flat(bg, 846, 444)
    G.bouquet_flat(bg, 392, 288, flip=True)
    # the lamp's last glow
    light_pool(bg, LAMP[0], LAMP[1] + 2, 26, 8, color="#f6cf7a", strength=0.12)


# ---------------------------------------------------------------------------------------------
# animated layer textures
# ---------------------------------------------------------------------------------------------
CAP_BOX = (0, 30, W, 186)       # texture area for the tossed caps (x, y, w, h)
CAP_FRAMES = 16


def cap_frames(out, res):
    """Mortarboards thrown up from the chairs: each cap rises into view over the stands, turns
    over at the top and drops back, eight frames out of a sixteen-frame cycle."""
    rng = _rng(81)
    caps = []
    for x in [96, 214, 330, 412, 560, 640, 736, 828, 900]:
        caps.append((x + int(rng.integers(-10, 10)), int(rng.integers(100, 150)), int(rng.integers(-14, 15)),
                     int(rng.integers(0, CAP_FRAMES)), int(rng.integers(0, 4))))
    sprites = [G.mortarboard(t) for t in range(4)]
    layers = []
    bx, by, bw, bh = CAP_BOX
    for f in range(CAP_FRAMES):
        cv = Canvas(bw, bh)
        for (x, apex, drift, phase, tilt) in caps:
            i = (f - phase) % CAP_FRAMES
            if i >= 8:
                continue
            t = i / 7.0
            y = 206 - apex * (1 - (2 * t - 1) ** 2) - 6 * t       # parabola, a little lower on the way down
            xx = x + drift * t
            spr = sprites[(tilt + i) % 4]
            cv.paste(spr, int(round(xx)) - 6 - bx, int(round(y)) - 5 - by)
        name = f"caps-{f:02d}.png"
        cv.save(os.path.join(out, name))
        pat = "".join("1" if k == f else "0" for k in range(CAP_FRAMES))
        layers.append({"kind": "blink", "pattern": pat, "rate": 8.0, "texture": res + name, "x": bx, "y": by})
    return layers


def patch_layer(out, res, name, pre, draw, rect, pattern, rate):
    """A blink layer that swaps a region for an alternate frame: the clean background under it
    plus `draw(canvas)` painting the alternate pose."""
    x, y, w, h = rect
    cv = Canvas(W, H)
    cv.a[y:y + h, x:x + w] = pre.a[y:y + h, x:x + w]
    draw(cv)
    patch = Canvas(w, h)
    patch.a = cv.a[y:y + h, x:x + w].copy()
    patch.save(os.path.join(out, name))
    return {"kind": "blink", "pattern": pattern, "rate": rate, "texture": res + name, "x": x, "y": y}


def cirrus_strip(out):
    cv = Canvas(W, 12)
    rng = _rng(91)
    for k in range(5):
        x0 = k * 190 + int(rng.integers(0, 80))
        ln = int(rng.integers(50, 100))
        for j in range(3):
            o = int(rng.integers(-6, 14)) + j * 10
            l2 = int(ln * rng.uniform(0.4, 0.8))
            for xx in range(l2):
                cv.px((x0 + o + xx) % W, 3 + j * 2, C("#f6f2f4", 0.55))
            for xx in range(l2 // 3):
                cv.px((x0 + o + 4 + xx) % W, 2 + j * 2, C("#ffffff", 0.45))
    cv.save(os.path.join(out, "cirrus.png"))


# ---------------------------------------------------------------------------------------------
def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    sky_and_mountains(bg)
    crowd, screen = stadium(bg)
    stands_snap = bg.a.copy()
    pre_flags = Canvas(W, H); pre_flags.a = bg.a.copy()
    flag_pts = rim_flags(bg)
    field_wall_and_banners(bg)
    sh = shadow_mask()
    path = floor(bg, sh)
    end_zone_words(bg)
    front_wall(bg)
    stage_info = stage(bg)
    pre_pennants = Canvas(W, H); pre_pennants.a = bg.a.copy()
    pennants(bg)
    floor_details(bg, path)
    margins(bg)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, name=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        props[str(index)] = {"texture": res + name, "anchor": [ax, ay]}

    for i in range(6):
        save(i, G.white_chair_row(300, 34, n=10, seed=100 + i))
    save(6, G.podium_thrust())
    save(7, G.field_lamp(68))
    save(10, G.balloon_bunch(40, 90, seed=5))

    # --- layers ------------------------------------------------------------------------------
    layers = []
    cirrus_strip(out)
    layers.append({"kind": "drift", "texture": res + "cirrus.png", "y": 0, "speed": 2.5, "alpha": 1.0})
    # flapping: rim flags and the stage pennants swap to a second pose
    x0f = min(p[0] for p in flag_pts) - 2
    layers.append(patch_layer(out, res, "flags-b.png", pre_flags,
                              lambda c: rim_flags(c, wave=1), (x0f, RIM_MID - 20, 310, 12), "0110", 2.2))
    layers.append(patch_layer(out, res, "pennants-b.png", pre_pennants,
                              lambda c: pennants(c, wave=2), (326, 100, 300, 76), "0011", 1.6))
    layers += cap_frames(out, res)
    # falling confetti over the field and the stage
    for k, col in enumerate(["f6cf7a", "ffffff", "e88aa0", "7ac0c8", "d8b45a", "c0a0d8"]):
        layers.append({"kind": "particles", "style": "dust", "count": 14, "rect": [0, 40, W, 280],
                       "speed": [2, -10 - 2 * k], "color": col})
    # the video board's chase lights along its gold trim
    bx, by, bw, bh = BOARD
    dots_a = [[x, by + bh - 5, 2, 1, "fff4c0", 1.0] for x in range(bx + 6, bx + bw - 6, 10)]
    dots_b = [[x + 5, by + bh - 5, 2, 1, "fff4c0", 1.0] for x in range(bx + 6, bx + bw - 6, 10)]
    layers.append({"kind": "blink", "pattern": "10", "rate": 4.0, "rects": dots_a})
    layers.append({"kind": "blink", "pattern": "01", "rate": 4.0, "rects": dots_b})
    # camera flashes in the crowd, the lamp breathing, glints on the stage rails
    rng = _rng(93)
    flashes = [list(p) + ["ffffff", 1] for p in crowd["flash"]
               if np.abs(bg.a[p[1], p[0], :3] - stands_snap[p[1], p[0], :3]).sum() < 1e-3
               if not (STAGE[0] - 4 <= p[0] <= STAGE[1] + 4 and p[1] > DECK_BACK - 70)
               and not (BOARD[0] - 2 <= p[0] <= BOARD[0] + BOARD[2] + 2 and p[1] < BOARD[1] + BOARD[3] + 4)
               and not (TOWERS[0] - 3 <= p[0] <= TOWERS[0] + 3 or TOWERS[1] - 3 <= p[0] <= TOWERS[1] + 3)]
    rng.shuffle(flashes)
    layers.append({"kind": "twinkle", "points": flashes[:40], "rate": 3.0, "min": 0.0})
    layers.append({"kind": "twinkle", "points": [[LAMP[0], LAMP[1] - 63, "fff0c4", 1],
                                                  [334, 196, "fff4c0", 1], [626, 196, "fff4c0", 1], [480, 162, "fff4c0", 1]],
                   "rate": 1.0, "min": 0.3})

    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": [],
        "fauna": [
            {"kind": "bird", "x": 120, "y": 40, "fly": 12.0, "rate": 4.0},
            {"kind": "bird", "x": 136, "y": 34, "fly": 12.0, "rate": 4.4},
            {"kind": "bird", "x": 600, "y": 24, "fly": 9.0, "rate": 3.6},
            {"kind": "pigeon", "x": 636, "y": 458, "range": 8, "speed": 0.3, "rate": 2.0},
            {"kind": "pigeon", "x": 662, "y": 450, "range": 5, "speed": 0.25, "rate": 1.7, "flip": True},
            {"kind": "pigeon", "x": 372, "y": 282, "range": 6, "speed": 0.3, "rate": 1.8},
            {"kind": "mk2_robin", "x": 220, "y": 476, "range": 4, "speed": 0.3, "rate": 2.0},
            {"kind": "macky_sparrow", "x": 560, "y": 229, "range": 5, "speed": 0.4, "rate": 2.4},
            {"kind": "squirrel", "x": 930, "y": 470, "range": 3, "speed": 0.25, "rate": 1.4, "flip": True},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
