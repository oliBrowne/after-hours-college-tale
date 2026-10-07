"""Dawn exit (M07): the last room. The party comes out of Macky's stage door into the first sun.

Painted at sunrise only (the game reaches M07 after dawn_started). We look west across the garden
in front of Macky toward Norlin Quad and the Flatirons: the slabs blaze rose-gold in the first
light while their pine slopes stay blue, morning haze lies in the valley, the campus roofs and
Old Main's clock tower catch the sun over a sandstone garden wall, and the gate in the middle
opens onto the quad. Behind the viewer the sun has just cleared Macky, so every shadow runs long
and up the screen, and Macky's own crenellated tower shadow still covers the corner where the
stage door is. Floor: a dewy lawn with footprints, random-flagstone walks (from the gate to a
round plaza with a brass sun set in it, then down to both corners), leaves under the trees, mist
along the wall. Props: two sunlit autumn oaks, the long bench (thermos of cocoa, cups, programme,
scarf), the lamp still glowing in the shadow, the stone planter.
Layers: clouds drifting behind the mountains (skyline occluder), mist along the wall, dew
glints, warm motes, a goose V, robins on the lawn by the inspect spot ("Just birds")."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, mix, shade
from surfaces import light_pool
from props import shrub, MUM
from lib_norlin import crazy_paving, kerb, stone_planter
from lib_norlin import lawn as quad_lawn
from lib_macky2 import (SKY_DAWN, HAZE_DAWN, SHADOW_DAWN, DEW, SUN, LIMESTONE, AUTUMN, STONE_SUN, dawn_sky, dawn_clouds,
                        title_flatirons, ridge_extend, campus_morning, valley_haze, garden_wall, gate_pier, spruce, far_range,
                        cloud_bank, cirrus, forest_ridge, lenticular, sunlit_tree, dawn_bench, dawn_lamp, tree_shadow, footprints, sun_medallion,
                        _ridge, _rng)

ROOM = "M07"
W, H = 960, 540
BASE = 142
WALK = (20, 142, 920, 374)
MOUNT = (250, 18)                 # title Flatirons: left x, top y
WALL_TOP = 128                    # garden wall coping
GATE = (470, 550)                 # gap in the wall where the quad path leaves (threshold 7 at 510, 200)
TOWER_X = 742                     # Old Main's clock tower over the roofs
TREES = [(180, 270), (750, 300)]
BENCH = (430, 329)
LAMP = (190, 414)
PLANTER = (620, 425)
PLAZA = (500, 372, 205, 80)       # centre x, y, radii
MEDALLION = (432, 410)
SHADOW_ANGLE = -58                # long shadows run up and to the right (sun low behind-left)
GRASS_SUN = ["#1e2a1c", "#2c3e22", "#4a6230", "#567236", "#6e8c40", "#8aa24a", "#aabc5e"]     # lawn in the sun
GRASS_SHADE = ["#16222a", "#1c2c30", "#2a4038", "#30483e", "#40584c", "#5a7062", "#8aa0a0"]   # in shadow, dew silvered
PAVE_SUN = ["#4a3430", "#6e4e42", "#9a7460", "#a8826a", "#b89276", "#d0ac88"]
PAVE_SHADE = ["#2e2a34", "#46404a", "#5c5460", "#665c66", "#70666e", "#80767c"]
LEAVES = ["#c05a2c", "#e08a3c", "#a84a30", "#e0b844", "#8a3a26", "#f4b45a"]


# ---------------------------------------------------------------------------------------------
# back band: sky, the Flatirons, valley haze, campus, garden wall and gate
# ---------------------------------------------------------------------------------------------
def skyline(bg):
    """Paints the band above the floor. Returns the mask of everything that is not sky (for the
    skyline occluder that lets clouds drift behind the mountains)."""
    dawn_sky(bg, 0, 0, W, 112, seed=3)
    rng = _rng(7)
    for (cx, cy, ln) in [(40, 14, 150), (300, 8, 120), (610, 18, 170), (820, 10, 110)]:
        cirrus(bg, cx, cy, ln, rng)
    # wave clouds standing over the Front Range, lit from beneath
    lenticular(bg, 760, 46, 190, 5, layers=3, seed=1)
    lenticular(bg, 610, 38, 90, 3, layers=1, seed=2)
    lenticular(bg, 120, 52, 140, 4, layers=2, seed=3)
    sky = bg.a.copy()
    src, ridge = title_flatirons(1.6)
    mh, mw = src.shape[:2]
    mx, my = MOUNT
    # far ranges behind, pale with distance (South Boulder Peak's shoulder to the right of the
    # slabs, the foothills fading north on the left)
    xs, far = _ridge(0, W - 1, [(0, 66), (0.12, 60), (0.22, 68), (0.3, 72), (0.6, 70), (0.66, 56), (0.71, 50), (0.77, 56),
                                (0.84, 64), (0.9, 60), (1.0, 68)], rng, 0.7)
    xs, far2 = _ridge(0, W - 1, [(0, 78), (0.3, 82), (0.55, 76), (0.7, 72), (0.85, 78), (1.0, 74)], rng, 0.6)
    far_range(bg, 0, far, 112, seed=11, pal=["#968aac", "#9e90ae", "#ac9cb4", "#baa6b6", "#c8b0b8", "#d4bcbc"])
    far_range(bg, 0, far2, 112, seed=12)
    # near range to the left of the slabs (Flagstaff Mountain's shoulder), the slabs themselves
    xs, near = _ridge(0, mx, [(0, 84), (0.2, 76), (0.42, 79), (0.6, 68), (0.8, 62), (1.0, my + ridge[0])], rng, 0.6)
    forest_ridge(bg, 0, near[:mx], 120, seed=12)
    bg.paste(src, mx, my)
    # the slabs fall away to the right into foothills under the far haze
    xs, right = _ridge(mx + mw, W - 1, [(0, my + ridge[-1]), (0.3, 96), (1.0, 100)], rng, 0.5)
    right_img = ridge_extend(src, ridge, np.round(right).astype(int), 130, seed=13, block=(60, 90), haze="#a88aa4", haze_amt=0.22)
    bg.paste(right_img, mx + mw, 0)
    # what is not sky
    solid = np.abs(bg.a[..., :3] - sky[..., :3]).sum(-1) > 0.01
    # morning haze lying in the valley at the mountains' feet
    valley_haze(bg, 0, W, 82, 112, colour="#d4b2b4", alpha=(0.14, 0.26, 0.4), seed=5, mask=solid | (np.arange(H)[:, None] >= 100))
    bg.rect(0, 108, W, 34, mix("#b49aa8", "#8a7c80", 0.4))      # under the campus
    solid[100:, :] = True
    # campus across the quad, the clock tower, spruces
    campus_morning(bg, 0, W, WALL_TOP - 2, seed=21, gate=GATE, tower_x=TOWER_X)
    # tall blue spruces framing both ends, inside the wall
    for (sx, sh) in [(12, 104), (44, 82), (70, 58), (906, 96), (936, 118)]:
        spruce(bg, sx, WALL_TOP + 2, sh, seed=sx)
    # the gate gap: the quad path running away between lawns
    ga, gb = GATE
    bg.rect(ga, WALL_TOP - 4, gb - ga, BASE - WALL_TOP + 4, GRASS_SUN[3])
    for yy in range(WALL_TOP - 4, BASE):
        t = (yy - (WALL_TOP - 4)) / (BASE - WALL_TOP + 4)
        half = int(6 + t * 30)
        bg.hline((ga + gb) // 2 - half, yy, half * 2, PAVE_SUN[3] if yy % 3 else PAVE_SUN[2])
        bg.px((ga + gb) // 2 - half - 1, yy, LIMESTONE[3]); bg.px((ga + gb) // 2 + half, yy, LIMESTONE[3])
    bg.hline((ga + gb) // 2 - 6, WALL_TOP - 4, 12, PAVE_SUN[4])
    # the wall either side of the gate with its hedge; piers and lanterns
    garden_wall(bg, 0, ga - 8, WALL_TOP, BASE, seed=31)
    garden_wall(bg, gb + 8, W, WALL_TOP, BASE, seed=32)
    for px_ in (ga - 4, gb + 4):
        gate_pier(bg, px_, WALL_TOP - 8, BASE, lamp=True, lit=0.25)
    return solid


# ---------------------------------------------------------------------------------------------
# floor: lawn, walks, plaza, shadows, mist, dew
# ---------------------------------------------------------------------------------------------
def walk_mask():
    ys, xs = np.mgrid[0:H, 0:W]
    m = np.zeros((H, W), bool)
    cx, cy, rx, ry = PLAZA
    m |= ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1
    # quad path from the gate down to the plaza, widening a little
    ga, gb = GATE
    for y in range(BASE, cy):
        t = (y - BASE) / (cy - BASE)
        half = 36 + int(t * 8)
        m[y, (ga + gb) // 2 - half:(ga + gb) // 2 + half] = True
    # curving walks from the plaza down to both corners (stage door left, UMC right)
    def walk(pts, half):
        from PIL import Image, ImageDraw
        img = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(img)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            d.line([(x0, y0), (x1, y1)], fill=255, width=half * 2)
        for (x, y) in pts:
            d.ellipse([x - half, y - half, x + half, y + half], fill=255)
        return np.array(img) > 0
    m |= walk([(330, 410), (260, 448), (170, 466), (60, 468), (-20, 468)], 26)
    m |= walk([(680, 410), (750, 446), (850, 466), (980, 468)], 26)
    return m


def shadow_mask():
    """Long morning shadows: the oaks, bench, lamp and planter, and Macky's south tower (behind
    the viewer, bottom left) laying a crenellated shadow over the stage-door corner."""
    from PIL import Image, ImageDraw
    sh = np.zeros((H, W), bool)
    a = np.deg2rad(SHADOW_ANGLE)
    dx, dy = np.cos(a), np.sin(a) * 0.55
    for i, (tx, ty) in enumerate(TREES):
        tree_shadow(sh, tx + 2, ty - 2, 170, SHADOW_ANGLE, 92, 46, seed=60 + i, trunk=7, gap=0.3)
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    bx, by = BENCH
    L = 50
    d.polygon([(bx - 104, by - 2), (bx + 104, by - 2), (bx + 104 + dx * L, by - 2 + dy * L), (bx - 104 + dx * L, by - 2 + dy * L)], fill=255)
    px_, py_ = PLANTER
    L = 84
    d.polygon([(px_ - 75, py_ - 2), (px_ + 75, py_ - 2), (px_ + 75 + dx * L, py_ - 2 + dy * L), (px_ - 75 + dx * L, py_ - 2 + dy * L)], fill=255)
    sh |= np.array(img) > 0
    L = 330
    vx, vy = dx * L, dy * L
    base_l, base_r = (-70, 560), (110, 560)
    far_l = (base_l[0] + vx, base_l[1] + vy)
    far_r = (base_r[0] + vx, base_r[1] + vy)
    pts = [base_l, base_r, far_r]
    n = 7
    for k in range(n, 0, -1):          # merlons along the far edge
        t0, t1 = k / n, (k - 0.5) / n
        p0 = (far_l[0] + (far_r[0] - far_l[0]) * t0, far_l[1] + (far_r[1] - far_l[1]) * t0)
        p1 = (far_l[0] + (far_r[0] - far_l[0]) * t1, far_l[1] + (far_r[1] - far_l[1]) * t1)
        ext = (dx * 18, dy * 18)
        pts += [p0, (p0[0] + ext[0], p0[1] + ext[1]), (p1[0] + ext[0], p1[1] + ext[1]), p1]
    pts.append(far_l)
    img = Image.new("L", (W, H), 0)
    ImageDraw.Draw(img).polygon(pts, fill=255)
    sh |= np.array(img) > 0
    sh[:BASE + 8] = False
    return sh


def floor(bg, walks, sh):
    """Lawn and walks painted twice from the same seeds, once in the sun and once in shadow,
    then joined along the shadow edges (a hue shift, not a darkening)."""
    rng = _rng(41)
    fl = np.zeros((H, W), bool)
    fl[BASE:, :] = True
    lawn_m = fl & ~walks
    shade_cv = Canvas(W, H)
    for cv, gp, pp, kl in ((bg, GRASS_SUN, PAVE_SUN, STONE_SUN[5]), (shade_cv, GRASS_SHADE, PAVE_SHADE, "#8a8088")):
        quad_lawn(cv, 0, BASE, W, H - BASE, seed=42, pal=gp, band=26, mask=lawn_m)
        crazy_paving(cv, walks & fl, pal=pp, seed=43, cell=(18, 10), moss=0.08)
        kerb(cv, walks & fl, light=kl, dark="#2a2a22")
    cx, cy, rx, ry = PLAZA
    yy, xx = np.mgrid[0:H, 0:W]
    e = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    ring = (e <= 0.86) & (e >= 0.76) & walks
    for cv, band in ((bg, ["#7a4438", "#94584a", "#b07462"]), (shade_cv, ["#4a3a44", "#5a4852", "#6a5862"])):
        cv.fill_mask(ring, band[1])
        cv.fill_mask(ring & (e <= 0.775), band[0])
        cv.fill_mask(ring & (e >= 0.845), band[2])
        cv.fill_mask(ring & (((np.arctan2((yy - cy) / ry, (xx - cx) / rx) * 18 / np.pi) % 1) < 0.08), band[0])
    sun_medallion(bg, *MEDALLION, r=36)
    sun_medallion(shade_cv, *MEDALLION, r=36, pal=["#3a3038", "#5a4c48", "#7a6a5a", "#948066", "#a89278"], field=PAVE_SHADE + ["#8a8088"])
    bg.a[sh] = shade_cv.a[sh]
    # shadow edges: one darker pixel row where shade begins (crisp)
    from scipy import ndimage
    edge = sh & ~ndimage.binary_erosion(sh)
    bg.fill_mask(edge & fl, C("#0d0b16", 0.12))
    # flower bed along the foot of the wall: mulch, asters and mums
    ga, gb = GATE
    bg.rect(0, BASE, ga - 8, 7, "#3a2620"); bg.rect(gb + 8, BASE, W - gb - 8, 7, "#3a2620")
    for x in range(-4, W, 9):
        if ga - 6 < x < gb - 2:
            continue
        sw, sh_ = int(rng.integers(10, 15)), int(rng.integers(6, 9))
        fl_ = [MUM[0], MUM[1], "#a888c8"] if rng.random() < 0.6 else ["#9a7ac0", "#c0a0e0", MUM[3]]
        bg.paste(shrub(0, 0, sw, sh_, seed=int(rng.integers(1e6)), flowers=fl_, density=1.2), x, BASE - 2)
    bg.hline(0, BASE + 7, ga - 8, C("#0d0b16", 0.3)); bg.hline(gb + 8, BASE + 7, W - gb - 8, C("#0d0b16", 0.3))
    # dew: silver in the shade (still wet), a few gold glints where the sun has reached it
    ys, xs = np.where(sh & lawn_m)
    pick = rng.random(len(ys)) < 0.007
    for y, x in zip(ys[pick], xs[pick]):
        bg.px(x, y, "#9cb4b8" if rng.random() < 0.8 else "#d0e0e0")
    ys, xs = np.where(lawn_m & ~sh)
    pick = rng.random(len(ys)) < 0.0015
    for y, x in zip(ys[pick], xs[pick]):
        bg.px(x, y, "#fff2c8")
    return lawn_m


def details(bg, walks, lawn_m, sh):
    rng = _rng(71)
    # footprints across the dewy lawn: someone cut the corner from the stage door to the bench
    footprints(bg, [(172, 436), (214, 420), (258, 404), (300, 388)], "#0e1a1c", step=7, alpha=0.6)
    footprints(bg, [(186, 440), (228, 424), (270, 408), (306, 394)], "#0e1a1c", step=7, alpha=0.55)
    # a rabbit's hop marks toward the hedge
    for k in range(6):
        x, y = 820 + k * 14, 238 - k * 6
        bg.rect(x, y, 2, 1, C("#1a2a24", 0.45)); bg.rect(x + 3, y, 2, 1, C("#1a2a24", 0.45)); bg.px(x + 1, y + 2, C("#1a2a24", 0.4))
    # leaf litter under the oaks, a few blown onto the walks
    for (cx, cy, r, n) in [(180, 262, 70, 170), (750, 292, 74, 180), (500, 372, 160, 40), (620, 420, 90, 25)]:
        for _ in range(n):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
            lx, ly = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.45)
            if BASE + 9 <= ly < 514 and 0 <= lx < W - 1:
                c = LEAVES[int(rng.integers(len(LEAVES)))]
                if sh[ly, lx]:
                    c = shade(c, -0.25)
                bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
                if rng.random() < 0.3:
                    bg.px(lx, ly - 1, shade(c, 0.15))
    # a few late dandelions and clover flowers in the lawn
    for _ in range(30):
        fx, fy = int(rng.integers(30, 930)), int(rng.integers(170, 506))
        if not lawn_m[fy, fx]:
            continue
        for _ in range(int(rng.integers(3, 6))):
            px_, py_ = fx + int(rng.integers(-4, 5)), fy + int(rng.integers(-2, 3))
            if lawn_m[py_, px_]:
                bg.px(px_, py_, "#f2e6c8" if rng.random() < 0.6 else "#f0c040")
    # mist lying on the lawn along the wall (flat translucent bands, ragged tops)
    for (mx_, my_, mw_) in [(40, BASE + 12, 150), (300, BASE + 16, 120), (600, BASE + 10, 170), (820, BASE + 18, 110)]:
        for k, al in enumerate((0.14, 0.12)):
            for x in range(mx_ + k * 12, mx_ + mw_ - k * 12):
                t = (x - mx_) / mw_
                hh = int((8 - k * 3) * np.sin(np.pi * t) + rng.integers(0, 2))
                if hh > 0:
                    bg.rect(x, my_ - hh, 1, hh * 2 - k, C("#eee4e6", al))
    # the lamp's last glow in the tower shadow
    light_pool(bg, LAMP[0], LAMP[1] + 2, 30, 9, color="#f6cf7a", strength=0.16)
    # edges: hedges in the side margins (gaps where the walks leave) and a planted strip below
    from surfaces import ashlar_wall
    bg.rect(0, 516, W, 24, "#1e2a22")
    ashlar_wall(bg, 0, 514, W, 5, [shade(c, -0.05) for c in STONE_SUN[:6]], seed=33)
    for x in range(-6, W, 14):
        w, h = int(rng.integers(16, 24)), int(rng.integers(10, 15))
        bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None), x, 520 + int(rng.integers(0, 6)))
    for x0 in (0, W - 20):
        for y in range(BASE + 60, 514, 11):
            if 430 <= y <= 500:
                continue
            w, h = int(rng.integers(18, 24)), int(rng.integers(12, 16))
            bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6))), x0 - 4 + int(rng.integers(0, 6)), y - h)
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.22))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.22))
    bg.rect(0, WALK[1] + WALK[3], W, H - WALK[1] - WALK[3], C("#0d0b16", 0.3))


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    solid = skyline(bg)
    walks = walk_mask()
    sh = shadow_mask()
    lawn_m = floor(bg, walks, sh)
    details(bg, walks, lawn_m, sh)
    bg.save(os.path.join(out, "background.png"))

    # skyline occluder: everything above the floor that is not sky, so clouds drift behind it
    occ = Canvas(W, BASE)
    m = solid[:BASE].copy()
    m[100:] = True
    occ.a[m] = bg.a[:BASE][m]
    occ.save(os.path.join(out, "skyline.png"))

    props = {}

    def save(index, made, name=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        props[str(index)] = {"texture": res + name, "anchor": [ax, ay]}

    save(0, sunlit_tree(140, seed=81))
    save(1, sunlit_tree(146, seed=82, flip=True, tint=(1.04, 1.0, 0.86)))
    save(2, dawn_bench(210, 32, seed=83))
    save(3, dawn_lamp(68, glass=0.4))
    save(4, stone_planter(150, 54, seed=84))

    # textures for layers
    clouds_hi = cloud_bank(W, 40, count=4, seed=5, sizes=(60, 120), thick=(5, 8))
    clouds_hi.save(os.path.join(out, "clouds-high.png"))
    clouds_lo = cloud_bank(W, 30, count=5, seed=9, sizes=(30, 70), thick=(3, 5))
    clouds_lo.save(os.path.join(out, "clouds-low.png"))
    # low mist drifting along the wall: separate soft-edged wisps (two flat tones)
    mist = Canvas(W, 16)
    mrng = _rng(91)
    for k in range(6):
        x0, ln = k * 160 + int(mrng.integers(0, 60)), int(mrng.integers(60, 110))
        for x in range(ln):
            t = x / ln
            hh = int(5 * np.sin(np.pi * t) + mrng.integers(0, 2))
            if hh > 0:
                mist.rect((x0 + x) % W, 10 - hh, 1, hh + 2, C("#f4ecee", 0.4))
                if hh > 2:
                    mist.rect((x0 + x) % W, 10 - hh + 2, 1, hh - 1, C("#ffffff", 0.25))
    mist.save(os.path.join(out, "mist.png"))

    rng = _rng(92)
    dew = []
    while len(dew) < 34:
        x, y = int(rng.integers(30, 930)), int(rng.integers(160, 505))
        if lawn_m[y, x] and not sh[y, x]:
            dew.append([x, y, "fff6e0" if len(dew) % 3 else "f6e2a8", 1])
    layers = [
        {"kind": "drift", "texture": res + "clouds-high.png", "y": 2, "speed": 3.0, "alpha": 1.0},
        {"kind": "drift", "texture": res + "clouds-low.png", "y": 46, "speed": 5.5, "alpha": 0.9},
        {"kind": "drift", "texture": res + "mist.png", "y": BASE + 2, "speed": 2.0, "alpha": 0.8},
        {"kind": "twinkle", "points": dew, "rate": 1.6, "min": 0.0},
        {"kind": "twinkle", "points": [[LAMP[0], LAMP[1] - 58, "fff0c4", 2], [GATE[0] - 4, WALL_TOP - 23, "fff0c4", 1],
                                       [GATE[1] + 4, WALL_TOP - 23, "fff0c4", 1], [TOWER_X, WALL_TOP - 2 - 44 - 26, "fff0c8", 1]],
         "rate": 0.8, "min": 0.45},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [260, 200, 460, 220], "speed": [2, -1], "color": "f6d896"},
    ]
    geese = [{"kind": "mk2_goose", "x": 300 - 12 * k, "y": 22 + 5 * abs(k - 2) + (k > 2) * 0, "fly": 16.0, "rate": 3.0}
             for k in range(5)]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [{"texture": res + "skyline.png", "x": 0, "y": 0, "base": 141}],
        "props": props,
        "label_only": [],
        "overlays": [],
        "fauna": geese + [
            {"kind": "mk2_robin", "x": 672, "y": 280, "range": 4, "speed": 0.3, "rate": 2.0},
            {"kind": "mk2_robin", "x": 700, "y": 268, "range": 0, "speed": 0.0, "rate": 1.6},
            {"kind": "mk2_robin", "x": 690, "y": 292, "range": 3, "speed": 0.2, "rate": 2.2, "flip": True},
            {"kind": "mk2_magpie", "x": 560, "y": 478, "range": 6, "speed": 0.3, "rate": 1.5},
            {"kind": "rabbit", "x": 880, "y": 250, "range": 3, "speed": 0.2, "rate": 1.4},
            {"kind": "squirrel", "x": 214, "y": 276, "range": 4, "speed": 0.3, "rate": 1.4},
            {"kind": "bird", "x": 120, "y": 64, "fly": 11.0, "rate": 4.0},
        ],
        "leaves": [[120, 160, 130, 110], [690, 190, 130, 110]],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
