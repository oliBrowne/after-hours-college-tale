"""Old Main courtyard (O01): the last open office.

Top of the room: Old Main's east front at character scale - red brick, sandstone trim, the two
gabled end pavilions, the slate roof and the base of the bell tower over the open front door
(warm hall light, a red runner inside), its broad sandstone steps coming down into the courtyard.
Almost every window is dark; one upper office to the right of the tower is still lamp-lit, the
last open office (it goes dark once Todd's finite plan is filed, chapter3_complete).
Behind: the night sky with the moon, the campus treeline, Macky's twin towers over the right-hand
garden wall (where the procession goes), a big spruce over the left wall.
Courtyard: herringbone brick framed in soldier courses, a sandstone cross walk from the Norlin quad
exit (left) to the Macky route (right) lined with paper luminaria (lit once the procession is
ready, chapter3_complete), the Old Main medallion at the foot of the steps, two lawn panels with
the oak (whose ordinary moon shadow lies on the grass) and a blue spruce, a gas lamp, leaves.
Props: the oak and spruce, a long iron-and-oak bench, the gas lamp (save point) and a brick planter."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from midlib import sprite_from_cell
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import light_pool, ashlar_wall, LEAVES
from props import shrub, grass_tuft, atlas_tree, MUM, LEAF, OUT, IRON
from lib_norlin import lawn, kerb, stone_steps, stone_wall, STONE_N, LIME
from lib_oldmain import (old_main, night_sky, macky_far, herringbone, soldier_band, cast_shadow, gas_lamp,
                         victorian_bench, brick_planter, luminaria, om_window, TRIM_OM, HERRING, GRASS_OM,
                         BRICK_OM, SLATE)

ROOM = "O01"
W, H = 960, 540
BASE = 142 - 3             # floor row of Old Main (top of the steps)
CX = 450                   # the front door / tower centre line
WALK = (20, 142, 920, 374)
STEPS = (270, 6, 6)        # top width, treads, rise (the stairs placement is 290 wide, 139..177)
OAK = (260, 265)
SPRUCE = (800, 300)
LAMP = (190, 409)
CROSS = (440, 482)         # the cross walk (Norlin quad <-> Macky route), y range
MEDALLION = (CX, 266)
MOON_AT = (800, 30)        # the moon over the right-hand wall: shadows fall to the lower left
LEAN = -0.42
FORECOURT = (CX - 152, 184, CX + 152, 356)   # sandstone-framed forecourt (x0, y0, x1, y1), 6px bands
BAND_Y = 184                                  # the band runs across the whole courtyard at the steps' foot
PUDDLE = (252, 426)
OFFICE = "u6"              # the last open office: upper floor, right of the tower
LIT = {"g4": "dim", "g5": "dim", "u3": "dim", "g7": "dim", "u9": "dim"}
LUMINARIA = [(x, CROSS[0] - 1) for x in range(746, 950, 24)] + [(x, CROSS[1] + 6) for x in range(758, 950, 24)]


def far_campus(bg):
    """Treeline along the horizon, Macky's towers to the right, a campus roofline to the left."""
    rng = np.random.default_rng(5)
    for x in range(-10, W + 10, 11):
        h = int(rng.integers(14, 30))
        bg.ellipse(x, 120 - h, int(rng.integers(16, 26)), h * 2, "#1d1b33")
    mk = macky_far(78, dim=0.5)
    bg.paste(mk, 884 - mk.shape[1] // 2, 122 - mk.shape[0])
    for (x0, w, h) in [(0, 64, 20), (58, 48, 14)]:
        bg.rect(x0, 120 - h, w, h, "#201c34")
        bg.poly([(x0 - 3, 120 - h), (x0 + w // 2, 114 - h), (x0 + w + 3, 120 - h)], "#201c34")
        for wx in range(x0 + 5, x0 + w - 4, 7):
            if rng.random() < 0.45:
                bg.rect(wx, 120 - h + 6, 2, 3, "#c98a46")
    for x in list(range(-6, 180, 9)) + list(range(730, W + 6, 9)):
        h = int(rng.integers(8, 16))
        bg.ellipse(x, 128 - h, int(rng.integers(12, 18)), h * 2, "#182224")
        if rng.random() < 0.3:
            bg.px(x + 5, 128 - h + 2, "#24302e")


def garden_walls(bg, x0, x1):
    """Low sandstone garden walls from the building's corners to the room edges, shrubs on top,
    a spruce behind the left wall and a lamp-lit gap toward Macky on the right."""
    top = 112
    pal = [shade(c, -0.32) for c in STONE_N]
    rng = np.random.default_rng(9)
    spruce = sprite_from_cell(6, height=132, colors=30, brightness=0.72, saturation=0.85)
    bg.paste(spruce, 62 - spruce.shape[1] // 2, top + 6 - spruce.shape[0])
    for (a, b) in ((0, x0), (x1, W)):
        stone_wall(bg, a, top, b - a, BASE - top, pal=pal, seed=a + 3, course=5)
        bg.rect(a, top - 3, b - a, 4, shade(LIME[2], -0.2)); bg.hline(a, top - 3, b - a, shade(LIME[4], -0.2))
        for x in range(a - 4, b, 15):
            w, h = int(rng.integers(18, 26)), int(rng.integers(10, 16))
            bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.25 else None), x, top - h + 1)
        for px_ in (a + 4, b - 12):
            if 0 < px_ < W - 8:
                bg.rect(px_, top - 9, 8, BASE - top + 9, LIME[2]); bg.vline(px_, top - 9, BASE - top + 9, LIME[4])
                bg.rect(px_ - 1, top - 11, 10, 3, LIME[3]); bg.hline(px_ - 1, top - 11, 10, LIME[5])


def ground_masks():
    ys, xs = np.mgrid[0:H, 0:W]
    floor = ys >= BASE
    def rrect(x0, y0, x1, y1, r):
        inside = (xs >= x0) & (xs < x1) & (ys >= y0) & (ys < y1)
        for (cx, cy) in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
            corner = ((xs < x0 + r) if cx == x0 + r else (xs >= x1 - r)) & ((ys < y0 + r) if cy == y0 + r else (ys >= y1 - r))
            inside &= ~(corner & ((xs - cx) ** 2 + (ys - cy) ** 2 > r * r))
        return inside
    lawn_l = rrect(34, 206, 280, 394, 14)
    lawn_r = rrect(690, 206, 934, 396, 14)
    cross = (ys >= CROSS[0]) & (ys < CROSS[1])
    bed = (ys >= BASE) & (ys < BASE + 7) & (((xs >= 162) & (xs < CX - 148)) | ((xs >= CX + 148) & (xs < 738)))
    return floor, lawn_l, lawn_r, cross, bed


def medallion(bg, cx, cy):
    """The Old Main seal set into the brick: sandstone rings, brick rays, a bronze plate (1876)."""
    sy = 0.4
    def ell(r, c):
        bg.ellipse(cx - r, int(round(cy - r * sy)), 2 * r + 1, int(round(2 * r * sy)) + 1, c)
    ell(50, TRIM_OM[1]); ell(48, TRIM_OM[3]); ell(46, HERRING[3]); ell(36, TRIM_OM[2]); ell(34, HERRING[4])
    for k in range(24):
        a = k / 24 * 2 * np.pi
        bg.line(int(round(cx + np.cos(a) * 34)), int(round(cy + np.sin(a) * 34 * sy)),
                int(round(cx + np.cos(a) * 46)), int(round(cy + np.sin(a) * 46 * sy)), HERRING[1] if k % 2 else HERRING[5])
    ell(20, TRIM_OM[4]); ell(19, "#6a4e2a")
    bg.ellipse(cx - 17, cy - 6, 35, 13, "#8a6a34")
    bg.ellipse(cx - 15, cy - 5, 31, 10, "#a8843e")
    t = "1876"
    text(bg, t, cx - text_width(t) // 2, cy - 5, "#5a4020")
    text(bg, t, cx - text_width(t) // 2 + 1, cy - 4 + 0, C("#e8c070", 0.0))
    bg.hline(cx - 12, cy - 6, 24, "#d8b060")


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=1)

    # --- sky, the far campus, garden walls, then Old Main itself
    stars = night_sky(bg, W, 134, seed=3, moon=MOON_AT,
                      clouds=[(118, 40, 70, 3), (300, 18, 60, 2), (846, 22, 100, 3), (700, 52, 70, 2)])
    far_campus(bg)
    info = old_main(bg, CX, BASE, seed=4, lit=LIT, office=OFFICE)
    garden_walls(bg, info["x0"] - 2, info["x1"] + 2)

    # --- ground: herringbone courtyard, lawn panels, the cross walk, the bed along the building
    floor, lawn_l, lawn_r, cross, bed = ground_masks()
    lawns = lawn_l | lawn_r
    herringbone(bg, floor & ~lawns & ~cross, seed=11)
    ys, xs = np.mgrid[0:H, 0:W]
    fx0, fy0, fx1, fy1 = FORECOURT
    bands = (ys >= BAND_Y) & (ys < BAND_Y + 6) & (xs >= WALK[0]) & (xs < WALK[0] + WALK[2])
    frame = (xs >= fx0) & (xs < fx1) & (ys >= fy0) & (ys < fy1)
    frame &= ~((xs >= fx0 + 6) & (xs < fx1 - 6) & (ys >= fy0 + 6) & (ys < fy1 - 6))
    bands = (bands | frame) & ~lawns
    bg.fill_mask(bands, TRIM_OM[2])
    top_edge = bands & ~np.roll(bands, 1, axis=0)
    left_edge = bands & ~np.roll(bands, 1, axis=1)
    bot_edge = bands & ~np.roll(bands, -1, axis=0)
    right_edge = bands & ~np.roll(bands, -1, axis=1)
    bg.fill_mask(top_edge | left_edge, TRIM_OM[4]); bg.fill_mask(bot_edge | right_edge, TRIM_OM[1])
    horiz = bands & (np.roll(bands, 3, axis=1) & np.roll(bands, -3, axis=1))
    joints = (horiz & ((xs % 23) == 0)) | (bands & ~horiz & (((ys - BAND_Y) % 19) == 0))
    bg.fill_mask(joints & ~top_edge & ~bot_edge, TRIM_OM[1])
    bg.fill_mask(bot_edge, TRIM_OM[1]); bg.fill_mask(np.roll(bot_edge, 1, axis=0) & ~bands & ~lawns, C("#0d0b16", 0.25))
    # foot traffic has worn a paler line from the steps down to the cross walk
    for (cx_, cy_, rx_, ry_) in [(CX, 320, 60, 120), (CX, 230, 110, 40)]:
        light_pool(bg, cx_, cy_, rx_, ry_, color="#d8b8a0", strength=0.07, steps=2)
    lawn(bg, 0, BASE, W, H - BASE, seed=21, pal=GRASS_OM, mask=lawns)
    # sandstone flags along the cross walk with brick soldier courses either side
    from lib_norlin import flag_path
    flag_path(bg, cross & floor, pal=[shade(c, -0.22) for c in STONE_N], seed=23, row=8)
    for y0 in (CROSS[0] - 4, CROSS[1]):
        soldier_band(bg, (ys >= y0) & (ys < y0 + 4), seed=y0)
    # soldier courses round the lawn panels, a lit kerb on the inside
    ring = ndimage.binary_dilation(lawns, iterations=4) & ~lawns & floor & ~cross
    soldier_band(bg, ring, seed=31)
    kerb(bg, lawns, light=GRASS_OM[5], dark="#1a1416")
    # a border of low autumn flowers just inside each lawn
    border = lawns & ~ndimage.binary_erosion(lawns, iterations=5) & ndimage.binary_erosion(lawns, iterations=1)
    fy, fx = np.where(border)
    frng = np.random.default_rng(17)
    pick = frng.random(len(fy)) < 0.32
    for y_, x_ in zip(fy[pick], fx[pick]):
        c = [MUM[0], MUM[1], MUM[3], LEAF[3], LEAF[4], LEAF[2]][int(frng.integers(6))]
        bg.px(x_, y_, c)
    # stepping stones across the lawns, worn into the grass
    for (x0_, y0_, x1_, y1_, n_) in [(286, 300, 150, 388, 7), (690, 330, 900, 216, 8)]:
        for k in range(n_):
            t = (k + 0.5) / n_
            sx_, sy_ = int(x0_ + (x1_ - x0_) * t), int(y0_ + (y1_ - y0_) * t)
            if not lawns[sy_, sx_]:
                continue
            bg.ellipse(sx_ - 7, sy_ - 3, 15, 7, "#1a1416")
            bg.ellipse(sx_ - 6, sy_ - 3, 13, 6, STONE_N[2]); bg.ellipse(sx_ - 5, sy_ - 3, 10, 4, STONE_N[3])
            bg.hline(sx_ - 3, sy_ - 3, 6, STONE_N[4])
    # a rain puddle on the brick holding the moon and the lit door
    px_, py_ = PUDDLE
    bg.ellipse(px_ - 22, py_ - 6, 45, 13, "#1a1a2e"); bg.ellipse(px_ - 20, py_ - 5, 41, 10, "#22243c")
    bg.ellipse(px_ - 14, py_ - 4, 22, 6, "#2a2e4c")
    bg.ellipse(px_ + 6, py_ - 3, 6, 4, "#d8d0b0"); bg.px(px_ + 8, py_ - 2, "#fff4d2")
    for k in range(3):
        bg.hline(px_ - 12 + k * 3, py_ + 1 + k, 7 - k * 2, "#8a6a3a")
    bg.hline(px_ - 18, py_ - 5, 12, "#3a3e5c")
    # planting bed along the building: dark soil, low ivy, mums peeking out
    bg.fill_mask(bed, "#1e1614")
    rng = np.random.default_rng(41)
    x = 160
    while x < 736:
        if CX - 152 <= x < CX + 146:
            x = CX + 146
            continue
        w_, h_ = int(rng.integers(10, 17)), int(rng.integers(6, 10))
        bg.paste(shrub(0, 0, w_, h_, seed=int(rng.integers(1e6)), palette=LEAF, flowers=MUM if rng.random() < 0.35 else None), x - 2, BASE + 8 - h_)
        x += w_ - 4
    # the broad steps down from the door, painted flat (people walk on them)
    top_w, n, rise = STEPS
    stone_steps(bg, CX, BASE, top_w, n, rise=rise, spread=2, pal=TRIM_OM, seed=24)
    medallion(bg, *MEDALLION)

    # --- shadows: the oak's ordinary shadow on its lawn, the spruce's, the building's eave line
    oak = atlas_tree(136, cell=5, seed=43)
    spruce = atlas_tree(140, cell=6, seed=44)
    cast_shadow(bg, oak[0], OAK[0], OAK[1], oak[1], oak[2], lean=LEAN, squash=0.26, alpha=0.4)
    cast_shadow(bg, spruce[0], SPRUCE[0], SPRUCE[1], spruce[1], spruce[2], lean=LEAN, squash=0.26, alpha=0.4)
    for i in range(6):
        bg.hline(0, BASE + i, W, C("#0d0b16", 0.3 * (1 - i / 6)))

    # --- leaves: drifts under the oak, along the walls, blown onto the steps
    for (cx, cy, r, n_) in [(OAK[0], OAK[1] + 4, 80, 220), (SPRUCE[0], SPRUCE[1], 60, 60), (300, 160, 70, 50),
                            (620, 170, 60, 40), (120, 430, 90, 60), (520, 470, 120, 50), (380, 330, 80, 50)]:
        for _ in range(n_):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
            lx, ly = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.45)
            if BASE + 1 <= ly < 514 and 0 <= lx < W - 1:
                c = LEAVES[int(rng.integers(len(LEAVES)))]
                bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
                if rng.random() < 0.3:
                    bg.px(lx, ly - 1, shade(c, 0.15))
    # a few notices blown out of the building, a folded paper crane on the brick near Rook's spot
    for (px_, py_) in [(512, 196), (372, 262), (600, 402), (150, 476)]:
        bg.rect(px_, py_, 7, 5, "#d8ccae"); bg.hline(px_, py_, 7, "#ece2c6")
        bg.hline(px_ + 1, py_ + 2, 4, "#8a7e6a"); bg.px(px_ + 6, py_ + 4, "#a89c80")
    bg.poly([(676, 352), (682, 348), (686, 352), (680, 351)], "#ece2c6"); bg.px(686, 350, "#c8bca4"); bg.px(675, 351, "#c8bca4")
    # the procession's luminaria along the walk to Macky (unlit; the overlay lights them)
    for (lx, ly) in LUMINARIA:
        luminaria(bg, lx, ly, lit=False)

    # --- warm light: the open door down the steps, the door lanterns, the gas lamp
    light_pool(bg, CX, BASE + 18, 70, 18, strength=0.22)
    light_pool(bg, CX, BASE + 6, 40, 8, strength=0.16)
    for (lx, _) in info["lanterns"]:
        light_pool(bg, lx, BASE + 8, 26, 7, strength=0.14)
    light_pool(bg, LAMP[0], LAMP[1] + 3, 56, 15, strength=0.24)
    # the last open office throws a faint patch onto the courtyard below it
    wx, wy, ww, wh = info["windows"][OFFICE]
    light_pool(bg, wx + ww // 2 + 14, BASE + 24, 22, 6, strength=0.08)

    # --- a planted strip along the bottom edge, dark margins outside the walkable courtyard
    bg.rect(0, 516, W, 24, "#1a2420")
    ashlar_wall(bg, 0, 514, W, 5, [shade(c, -0.1) for c in STONE_N[:6]], seed=33)
    for x in range(-6, W, 14):
        w, h = int(rng.integers(16, 24)), int(rng.integers(10, 15))
        bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None), x, 520 + int(rng.integers(0, 6)))
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.3))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.3))
    # the walks themselves stay lit where they leave the room
    for (y0, y1, x0, x1) in [(CROSS[0], CROSS[1], 0, WALK[0]), (CROSS[0], CROSS[1], WALK[0] + WALK[2], W)]:
        bg.rect(x0, y0, x1 - x0, y1 - y0, C("#f6cf7a", 0.05))
    bg.save(os.path.join(out, "background.png"))

    # --- state overlays: the office light goes out; the luminaria are lit for the procession
    dark = Canvas(W, H)
    dark.a[:] = bg.a
    om_window(dark, wx, wy, ww, wh, state="dark", arch="round", seed=99)
    pad = 6
    crop = Canvas(ww + 2 * pad, wh + 2 * pad + 10)
    crop.a[:] = dark.a[wy - pad - 10:wy + wh + pad, wx - pad:wx + ww + pad]
    crop.save(os.path.join(out, "office-closed.png"))
    lum = Canvas(W, 70)
    for (lx, ly) in LUMINARIA:
        luminaria(lum, lx, ly - CROSS[0] + 20, lit=True)
    for (lx, ly) in LUMINARIA:
        light_pool(lum, lx, ly - CROSS[0] + 21, 9, 3, strength=0.2)
    lum.save(os.path.join(out, "procession-lit.png"))
    overlays = [
        {"texture": res + "office-closed.png", "x": wx - pad, "y": wy - pad - 10, "flag": "chapter3_complete"},
        {"texture": res + "procession-lit.png", "x": 0, "y": CROSS[0] - 20, "flag": "chapter3_complete"},
    ]

    # --- props
    props = {}

    def save(index, made, extra=None, name=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(1, oak)
    save(2, spruce)
    save(3, victorian_bench(150, 32, seed=7))
    save(4, gas_lamp(68))
    save(5, brick_planter(170, 54, seed=8))

    # --- animated: lanterns and the lamp breathe, the office lamp, stars; luminaria flicker when lit
    head = LAMP[1] - 68 + 5
    glows = [[lx, ly, "fff0c4", 1] for (lx, ly) in info["lanterns"]]
    glows += [[LAMP[0], head, "fff0c4", 2], [CX, BASE - 60, "fde9b6", 1]]
    star_pts = [[sx, sy, "c8c0e0", 0] for (sx, sy, c) in stars[::6] if not (info["x0"] - 4 < sx < info["x1"] + 4 and sy > 4)]
    layers = [
        {"kind": "twinkle", "points": glows, "rate": 1.6, "min": 0.5},
        {"kind": "twinkle", "points": star_pts, "rate": 0.9, "min": 0.0},
        {"kind": "twinkle", "points": [[wx + ww - 4, wy + wh - 10, "fff0c4", 1]], "rate": 2.4, "min": 0.6,
         "flag": "chapter3_complete", "when": False},
        {"kind": "twinkle", "points": [[lx, ly - 3, "f6cf7a", 1] for (lx, ly) in LUMINARIA], "rate": 3.1, "min": 0.4,
         "flag": "chapter3_complete"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0],
        "overlays": overlays,
        "fauna": [
            {"kind": "barn_owl", "x": info["x0"] - 1, "y": BASE - 103, "range": 0, "speed": 0.0, "rate": 1.2},
            {"kind": "night_bat", "x": 380, "y": 22, "fly": 13.0, "rate": 7.0},
            {"kind": "night_bat", "x": 700, "y": 40, "fly": 10.0, "rate": 6.0},
            {"kind": "om_roost", "x": info["windows"]["g2"][0] + 10, "y": BASE - 15, "range": 0, "speed": 0.0, "rate": 0.4},
            {"kind": "squirrel", "x": 336, "y": 286, "range": 4, "speed": 0.3, "rate": 1.2},
            {"kind": "rabbit", "x": 868, "y": 372, "range": 6, "speed": 0.2, "rate": 0.8, "flip": True},
            {"kind": "lamp_moth", "x": LAMP[0] + 2, "y": head - 6, "range": 7, "speed": 2.3, "rate": 9.0},
            {"kind": "om_crane", "x": 200, "y": 206, "fly": 5.0, "rate": 3.0},
        ],
        "leaves": [[OAK[0] - 60, OAK[1] - 120, 120, 130], [SPRUCE[0] - 40, SPRUCE[1] - 100, 80, 100]],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
