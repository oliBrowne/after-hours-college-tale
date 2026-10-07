"""Margin garden (N05): Norlin's roof garden at night, room for an empty space.

Top of the room: the night sky over campus - stepped indigo, stars, the moon, clouds drifting -
with the Flatirons leaning on the western horizon (left) and the red tile roofs of the campus
halls and Macky's towers below the terrace edge; a sandstone balustrade runs along the back of the
roof with urns on its piers and a festoon of warm bulbs swagged between them; pigeons doze on the
coping. Right: the stack wing of the library rises, its slit windows faintly lit.
The terrace: mown lawns edged with flower borders, oval beds, two lavender parterres, a clipped
box hedge down each side and pea gravel at the parapet foot and round the feeder; CU's random
sandstone flags make a small court (where Rook loiters) and paths to the three ways out - steps
down to the quad through a gap in the left parapet, the stair-head to the reading-room door at the bottom (warm light coming up), and the
grey service path to the stacks on the right, chained off until the stacks are shifted.
Props: two small trees in sandstone tubs, the long raised bed (with its bare patch left on
purpose and a low stone step at its end), the feeder bed where the pigeons gather, the lamp."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool, LEAVES
from props import OUT, IRON, LEAF, MUM, shrub, grass_tuft
from clouds import _cloud, cloud_strip
from facade import roof_tiles
from lib_norlin import (lawn, crazy_paving, kerb, quiet_lamp_post, stone_wall, quoins, directional_sign, stone_steps, depth_shade,
                        PAVE_N, STONE_N, LIME, GRASS, NIGHT_N)
from lib_norlin2 import (night_sky, moon, flatirons_night, campus_roofs, auditorium, balustrade, stone_urn, festoon, tub_tree,
                         raised_bed, feeder_bed, velvet_rope, lavender, GRAVEL, NIGHT_CLOUD, HAZARD)

ROOM = "N05"
W, H = 800, 480
BASE = 142
WALK = (20, 142, 760, 314)
SKY_H = 112
PARAPET = (96, BASE)                 # coping top, foot
PIERS = [8, 138, 268, 398, 528, 658]
WING_X = 690                         # the stack wing at the right
LAMP = (95, 335)
KEEPSAKE = (60, 318)
COURT = (420, 292, 92, 34)           # paved court: centre x, y, radius x, y
LEFT_GAP = (376, 426)                # steps down to the quad (y range in the left parapet)
FRONT_GAP = (514, 586)               # stair-head down to the reading-room door (x range)
FRONT_Y = 462                        # near parapet coping
SERVICE = (318, 356)                 # service path to the stacks (y range at the right edge)
ROPE = (752, 306)


def sky(bg):
    stars = night_sky(bg, 0, 0, W, SKY_H, seed=3, stars=130, star_h=80)
    moon(bg, 560, 30, r=8)
    crng = np.random.default_rng(4)
    for (cx, cy, length, thick) in [(30, 74, 90, 3), (250, 62, 60, 2), (612, 76, 80, 2)]:
        cl = _cloud(length, thick, crng, NIGHT_CLOUD)
        bg.paste(cl, cx, cy - cl.shape[0])
    flatirons_night(bg, -10, 330, 104, seed=5)
    lights = campus_roofs(bg, 300, WING_X, 104, seed=6, lit=0.45)
    auditorium(bg, 468, 104)
    # nearer tree crowns just below the parapet line
    rng = np.random.default_rng(7)
    for x in range(-6, WING_X, 9):
        h = int(rng.integers(6, 13))
        bg.ellipse(x, 108 - h, int(rng.integers(12, 18)), h * 2, "#182224")
    return stars, lights


def stack_wing(bg):
    """The library's stack wing rising at the right: sandstone with quoins, a tile roof edge, tall
    slit windows faintly lit, a downpipe, ivy, and a sign to the service aisle."""
    x0 = WING_X
    roof_tiles(bg, x0 - 4, 40, W - x0 + 4, 10, seed=3)
    stone_wall(bg, x0, 52, W - x0, BASE - 52, pal=[shade(c, -0.1) for c in STONE_N], seed=9, course=6)
    quoins(bg, x0, 54, BASE - 2, "left", pal=LIME)
    bg.rect(x0 - 2, 52, 2, BASE - 52, C("#0d0b16", 0.5))
    wins = []
    for i, wx in enumerate((726, 754, 782)):
        bg.rect(wx - 4, 60, 9, 40, LIME[2]); bg.rect(wx - 3, 61, 7, 38, OUT)
        lit = i != 1
        bg.rect(wx - 2, 62, 5, 36, "#c98a46" if lit else "#1e2038")
        if lit:
            for yy in range(64, 96, 5):
                bg.hline(wx - 2, yy, 5, "#8a5a30")
            wins.append((wx, 70))
        bg.rect(wx - 5, 100, 11, 3, LIME[3]); bg.hline(wx - 5, 100, 11, LIME[5])
    bg.rect(711, 50, 3, BASE - 50, IRON[2]); bg.vline(711, 50, BASE - 50, IRON[3])
    rng = np.random.default_rng(11)
    for _ in range(140):
        vx = x0 + int(abs(rng.normal(0, 12)))
        vy = BASE - int(abs(rng.normal(0, 30)))
        bg.px(vx, vy, LEAF[int(rng.integers(1, 4))])
    sw = directional_sign(bg, x0 + 8, 112, "SERVICE", arrow="right")
    return wins


def back(bg):
    stars, lights = sky(bg)
    wins = stack_wing(bg)
    top, base = PARAPET
    balustrade(bg, 0, WING_X, top, base, piers=PIERS, seed=2)
    for k, px_ in enumerate(PIERS[1:]):
        if k % 2 == 0:
            stone_urn(bg, px_, top - 7, seed=k + 3)
    bulbs = []
    anchors = [(PIERS[0], top - 10), (PIERS[2], top - 10), (PIERS[4], top - 10), (WING_X + 2, 60)]
    for (a, b) in zip(anchors, anchors[1:]):
        bulbs += festoon(bg, a[0], a[1], b[0], b[1], sag=14, every=10, seed=a[0])
    for (bx, by) in bulbs:
        pass
    # planting along the parapet foot: shrubs, grasses and a few late flowers against the balusters
    rng = np.random.default_rng(17)
    x = 4
    while x < WING_X - 10:
        if any(abs(x + 10 - p) < 14 for p in PIERS):
            x += 8
            continue
        sw, sh = int(rng.integers(18, 28)), int(rng.integers(12, 20))
        fl = MUM if rng.random() < 0.3 else None
        bg.paste(shrub(0, 0, sw, sh, seed=int(rng.integers(1e6)), flowers=fl), x, BASE - sh + 2)
        x += sw + int(rng.integers(6, 30))
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))
    return stars, lights, wins, bulbs


def band(xs, ys, a, b, half):
    (ax, ay), (bx, by) = a, b
    t = np.clip(((xs - ax) * (bx - ax) + (ys - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2), 0, 1)
    return np.hypot(xs - (ax + t * (bx - ax)), ys - (ay + t * (by - ay))) <= half


def poly_band(xs, ys, pts, half):
    m = np.zeros(xs.shape, bool)
    for a, b in zip(pts, pts[1:]):
        m |= band(xs, ys, a, b, half)
    return m


def masks():
    ys, xs = np.mgrid[0:H, 0:W]
    terrace = (ys >= BASE) & (ys < FRONT_Y)
    cx, cy, rx, ry = COURT
    court = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1
    left = poly_band(xs, ys, [(0, 401), (150, 401), (232, 392), (292, 352), (346, 312)], 19)
    front = poly_band(xs, ys, [(446, 318), (482, 368), (530, 418), (550, 470)], 19)
    right = poly_band(xs, ys, [(505, 300), (600, 322), (704, 337)], 15)
    lamp_pad = ((xs - 74) / 40.0) ** 2 + ((ys - 336) / 16.0) ** 2 <= 1
    paths = terrace & (court | left | front | right | lamp_pad)
    service = terrace & (xs >= 700) & (ys >= SERVICE[0]) & (ys < SERVICE[1])
    feed = ((xs - 548) / 74.0) ** 2 + ((ys - 230) / 24.0) ** 2 <= 1
    foot = (ys < BASE + 14)
    gravel_m = terrace & ~paths & ~service & (feed | foot)
    lawns = terrace & ~paths & ~service & ~gravel_m & (xs >= 22) & (xs < 778) & (ys < FRONT_Y - 6)
    return paths, service, lawns, gravel_m


def gravel(bg, mask, seed=0):
    """Warm pea gravel: a mid tone with scattered pebbles, each lit on top with a dark foot."""
    rng = np.random.default_rng(seed)
    ys, xs = np.where(mask)
    bg.a[ys, xs] = C(GRAVEL[3])
    n = len(ys) // 5
    pick = rng.integers(0, len(ys), n)
    for i in pick:
        x, y = int(xs[i]), int(ys[i])
        if y + 1 < H and mask[y + 1, x] and x + 1 < W and mask[y, x + 1]:
            c = GRAVEL[int(rng.choice([2, 4, 4, 5]))]
            bg.px(x, y, c); bg.px(x + 1, y, shade(c, -0.06)); bg.px(x, y + 1, GRAVEL[1])


def borders(bg, lawns):
    """Flower borders on the lawns: a dark soil strip with low clumps and dots of late flowers."""
    rng = np.random.default_rng(31)
    for (x0, y0, x1, y1) in [(28, 158, 330, 165), (560, 158, 772, 165), (24, 170, 31, 372), (771, 170, 778, 316)]:
        for y in range(y0, y1):
            for x in range(x0, x1):
                if lawns[y, x]:
                    bg.px(x, y, "#2a1c18" if (x + y) % 3 else "#3a2a20")
        for _ in range((x1 - x0) * (y1 - y0) // 6):
            x, y = int(rng.integers(x0, x1)), int(rng.integers(y0, y1))
            if lawns[y, x]:
                c = [MUM[0], MUM[1], MUM[2], "#8a72c0", "#e6d6b1", LEAF[3], LEAF[2]][int(rng.integers(7))]
                bg.px(x, y, c)


def flower_bed(bg, cx, cy, rx, ry, seed=0, flowers=None):
    """A flat oval bed cut into the lawn: dark soil with a lit edge, low clumps and late flowers."""
    rng = np.random.default_rng(seed)
    bg.ellipse(cx - rx - 1, cy - ry - 1, 2 * rx + 3, 2 * ry + 3, "#1e1a18")
    bg.ellipse(cx - rx, cy - ry, 2 * rx + 1, 2 * ry + 1, "#2a1c18")
    flowers = flowers or [MUM[0], MUM[1], MUM[2], "#e6d6b1"]
    for _ in range(rx * ry // 2):
        a = rng.uniform(0, 2 * np.pi); d = np.sqrt(rng.uniform(0, 1))
        x, y = int(cx + np.cos(a) * d * (rx - 2)), int(cy + np.sin(a) * d * (ry - 1))
        k = rng.random()
        if k < 0.45:
            bg.px(x, y, LEAF[2]); bg.px(x + 1, y, LEAF[3]); bg.px(x, y - 1, LEAF[3])
        elif k < 0.8:
            c = flowers[int(rng.integers(len(flowers)))]
            bg.px(x, y, c); bg.px(x, y - 1, shade(c, 0.2))
        else:
            bg.px(x, y, "#3e2a20")


def parterre(bg, x, y, w, h, seed=0):
    """A lavender parterre: clipped box edging round staggered rows of lavender clumps on dark soil."""
    rng = np.random.default_rng(seed)
    bg.rect(x - 1, y - 1, w + 2, h + 2, "#1e1a18")
    bg.rect(x, y, w, h, "#2a1c18")
    for _ in range(w * h // 6):
        bg.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), "#3e2a20" if rng.random() < 0.6 else "#1e1412")
    # back box edge first, then the clumps back to front, then the front box edge over their feet
    bg.rect(x, y, w, 4, LEAF[2]); bg.hline(x, y, w, LEAF[4]); bg.hline(x, y + 1, w, LEAF[3])
    rows = list(range(y + 12, y + h - 1, 10))
    for r, base in enumerate(rows):
        off = 6 if r % 2 else 0
        for cx in range(x + 8 + off, x + w - 6, 13):
            lavender(bg, cx + int(rng.integers(-1, 2)), base, w=12, h=int(rng.integers(10, 13)), seed=int(rng.integers(1 << 30)))
    for (xx, yy, ww, hh) in ((x, y + h - 4, w, 4), (x, y, 3, h), (x + w - 3, y, 3, h)):
        bg.rect(xx, yy, ww, hh, LEAF[3]); bg.hline(xx, yy, ww, LEAF[4])
    bg.hline(x, y + h, w, C("#0d0b16", 0.5))


def stepping_stones(bg, pts, seed=0):
    rng = np.random.default_rng(seed)
    for (x, y) in pts:
        rx, ry = int(rng.integers(5, 8)), 3
        bg.ellipse(x - rx - 1, y - ry, 2 * rx + 3, 2 * ry + 2, "#1e1a18")
        bg.ellipse(x - rx, y - ry, 2 * rx + 1, 2 * ry + 1, PAVE_N[3]); bg.hline(x - rx + 2, y - ry, 2 * rx - 3, PAVE_N[5])


def edges(bg):
    """Parapet copings round the terrace seen from above, with the three gaps and what is in them."""
    cope = LIME
    # near (front) coping with the stair-head gap
    for (x0, x1) in ((0, FRONT_GAP[0]), (FRONT_GAP[1], W)):
        bg.rect(x0, FRONT_Y, x1 - x0, 8, cope[3]); bg.hline(x0, FRONT_Y, x1 - x0, cope[5]); bg.hline(x0, FRONT_Y + 7, x1 - x0, cope[1])
        bg.rect(x0, FRONT_Y - 3, x1 - x0, 3, C("#0d0b16", 0.3))
        bg.rect(x0, FRONT_Y + 8, x1 - x0, H - FRONT_Y - 8, "#141226")
    gx0, gx1 = FRONT_GAP
    for i in range(4):
        y = FRONT_Y - 2 + i * 6
        c = shade(STONE_N[3], -0.12 * i)
        bg.rect(gx0, y, gx1 - gx0, 6, c); bg.hline(gx0, y, gx1 - gx0, shade(c, 0.15)); bg.hline(gx0, y + 5, gx1 - gx0, shade(c, -0.3))
    for i, a in enumerate((0.16, 0.1, 0.06)):
        bg.rect(gx0 - 6 - i * 10, FRONT_Y - 20 - i * 12, gx1 - gx0 + 12 + i * 20, 40 + i * 12, C("#f6cf7a", a))
    for px_ in (gx0 - 5, gx1 - 1):
        bg.rect(px_, FRONT_Y - 4, 6, 14, OUT); bg.rect(px_ + 1, FRONT_Y - 3, 4, 12, STONE_N[4]); bg.hline(px_ + 1, FRONT_Y - 3, 4, LIME[5])
    # left coping with the gap for the steps down to the quad
    ly0, ly1 = LEFT_GAP
    for (y0, y1) in ((BASE, ly0), (ly1, FRONT_Y)):
        bg.rect(0, y0, 10, y1 - y0, cope[3]); bg.vline(9, y0, y1 - y0, cope[5]); bg.vline(10, y0, y1 - y0, C("#0d0b16", 0.35))
    for i in range(3):
        x = 14 - i * 6
        c = shade(STONE_N[3], -0.14 * i)
        bg.rect(x - 6, ly0, 6, ly1 - ly0, c); bg.vline(x - 1, ly0, ly1 - ly0, shade(c, 0.18))
    for py_ in (ly0 - 6, ly1 - 2):
        bg.rect(2, py_, 12, 8, OUT); bg.rect(3, py_ + 1, 10, 6, STONE_N[4]); bg.hline(3, py_ + 1, 10, LIME[5])
        bg.rect(6, py_ - 8, 4, 8, OUT); bg.rect(7, py_ - 7, 2, 5, "#f6cf7a"); bg.px(7, py_ - 7, "#fff0c4")
    for i, a in enumerate((0.1, 0.07, 0.04)):
        bg.rect(0, ly0 - 12 - i * 8, 18 + i * 12, ly1 - ly0 + 24 + i * 16, C("#f6cf7a", a))
    # right coping with the service gap
    sy0, sy1 = SERVICE
    for (y0, y1) in ((BASE, sy0), (sy1, FRONT_Y)):
        bg.rect(W - 10, y0, 10, y1 - y0, cope[3]); bg.vline(W - 10, y0, y1 - y0, cope[5]); bg.vline(W - 11, y0, y1 - y0, C("#0d0b16", 0.35))


def floor(bg):
    paths, service, lawns, gravel_m = masks()
    bg.rect(0, BASE, W, FRONT_Y - BASE, GRAVEL[3])
    ys, xs = np.mgrid[0:H, 0:W]
    terr = (ys >= BASE) & (ys < FRONT_Y)
    gravel(bg, terr & (gravel_m | ~(lawns | paths | service)), seed=12)
    lawn(bg, 0, BASE, W, FRONT_Y - BASE, seed=13, mask=lawns, band=18)
    borders(bg, lawns)
    kerb(bg, lawns, light=SLEEPER_EDGE, dark="#1e1a18")
    flower_bed(bg, 262, 214, 36, 11, seed=41)
    flower_bed(bg, 470, 186, 30, 8, seed=42, flowers=["#8a72c0", "#b49ad8", "#e6d6b1"])
    flower_bed(bg, 736, 210, 24, 9, seed=43)
    parterre(bg, 646, 388, 104, 40, seed=44)
    parterre(bg, 60, 426, 120, 26, seed=45)
    stepping_stones(bg, [(330, 262), (306, 252), (282, 246), (230, 252), (205, 258)], seed=46)
    stepping_stones(bg, [(560, 300), (586, 292), (612, 290), (640, 296)], seed=47)
    crazy_paving(bg, paths, pal=PAVE_N, seed=14, cell=(16, 9), moss=0.1)
    kerb(bg, paths, light=LIME[2], dark="#2a2026")
    # service path to the stacks: grey concrete with hazard edges, as in the service aisle
    ys, xs = np.where(service)
    bg.a[ys, xs] = C("#4a4648")
    rng = np.random.default_rng(15)
    for _ in range(300):
        i = int(rng.integers(len(ys)))
        bg.px(int(xs[i]), int(ys[i]), "#545052" if rng.random() < 0.6 else "#3e3a3e")
    sy0, sy1 = SERVICE
    for x in range(700, W - 10, 8):
        bg.rect(x, sy0, 4, 2, HAZARD[2]); bg.rect(x + 4, sy0, 4, 2, HAZARD[0])
        bg.rect(x, sy1 - 2, 4, 2, HAZARD[2]); bg.rect(x + 4, sy1 - 2, 4, 2, HAZARD[0])
    edges(bg)
    # clipped box hedges along the side copings (outside the walkable terrace)
    rng2 = np.random.default_rng(19)
    for (x0, y0, y1) in ((8, BASE + 6, LEFT_GAP[0] - 8), (8, LEFT_GAP[1] + 10, FRONT_Y - 2),
                         (W - 22, BASE + 6, SERVICE[0] - 4), (W - 22, SERVICE[1] + 6, FRONT_Y - 2)):
        y = y0
        while y < y1:
            hh = int(rng2.integers(12, 18))
            bg.paste(shrub(0, 0, 16, hh, seed=int(rng2.integers(1e6)), density=1.4), x0 - 2, min(y, y1 - hh) - 2)
            y += hh - 5
    # tufts at lawn edges and seed spilt where the pigeons feed
    for (gx, gy) in [(40, 252), (300, 160), (322, 258), (566, 296), (764, 250), (632, 380), (232, 440)]:
        grass_tuft(bg, gx, gy, 6, seed=gx)
    for (sx, sy) in [(568, 228), (575, 231), (583, 226), (592, 233), (600, 228), (588, 237), (606, 232), (560, 233)]:
        bg.px(sx, sy, "#e0c080"); bg.px(sx + 1, sy, "#a88850")
    # fallen leaves under the trees and along the parapet foot
    for (cx, cy, r, n) in [(155, 262, 40, 60), (650, 282, 40, 60), (320, 148, 120, 50), (520, 148, 80, 30)]:
        for _ in range(n):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
            lx, ly = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.45)
            if BASE <= ly < FRONT_Y - 4:
                c = LEAVES[int(rng.integers(len(LEAVES)))]
                bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
    # light: the lamp, the festoons on the parapet foot, the stack wing's windows
    light_pool(bg, LAMP[0], LAMP[1] + 3, 46, 13, strength=0.26)
    light_pool(bg, 330, BASE + 8, 260, 14, strength=0.08)
    light_pool(bg, 750, BASE + 6, 50, 8, strength=0.08)
    depth_shade(bg, 0, 420, W, 42, steps=2, alpha=0.14)
    # margins
    bg.rect(0, BASE, WALK[0], FRONT_Y - BASE, C("#0d0b16", 0.25))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], FRONT_Y - BASE, C("#0d0b16", 0.25))


SLEEPER_EDGE = "#5a4636"


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    stars, lights, wins, bulbs = back(bg)
    floor(bg)
    bg.save(os.path.join(out, "background.png"))
    res = f"res://assets/art/rooms/{ROOM}/"

    props = {}

    def save(index, made, extra=None, name=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(0, tub_tree(110, seed=1, cell=5))
    save(1, tub_tree(110, seed=2, cell=5, tint=(1.08, 0.82, 0.78)))
    save(2, raised_bed(190, 65, seed=3, step=30))
    save(3, feeder_bed(80, 55, seed=4))
    save(4, quiet_lamp_post(68))

    # the service path stays chained until the stacks are shifted
    overlays = []
    chain = ["#1a1820", "#4a4858", "#7a7890"]
    for open_, name in ((False, "chain-closed.png"), (True, "chain-open.png")):
        velvet_rope(open_, rope=chain, post=IRON).save(os.path.join(out, name))
        overlays.append({"texture": res + name, "x": ROPE[0], "y": ROPE[1], "flag": "stacks_shifted", "when": open_})

    clouds = cloud_strip(width=W, height=34, count=4, seed=8, pal=NIGHT_CLOUD, sizes=(50, 110))
    clouds.save(os.path.join(out, "clouds.png"))
    rng = np.random.default_rng(21)
    star_pts = [stars[int(i)] for i in rng.choice(len(stars), 18, replace=False)]
    layers = [
        {"kind": "drift", "texture": res + "clouds.png", "y": 4, "speed": 2.0, "alpha": 0.85},
        {"kind": "twinkle", "points": [[x, y, "c8c0e0", 0] for (x, y) in star_pts], "rate": 0.9, "min": 0.0},
        {"kind": "twinkle", "points": [[x, y, "f6cf7a", 0] for (x, y) in bulbs] + [[x, y, "f6cf7a", 0] for (x, y) in lights[:6]] +
                                       [[x, y, "f6cf7a", 1] for (x, y) in wins] + [[LAMP[0], LAMP[1] - 60, "fff0c4", 2]],
         "rate": 1.3, "min": 0.5},
        {"kind": "particles", "style": "leaf", "count": 7, "rect": [40, 160, 700, 270], "speed": [16, 6]},
    ]

    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": overlays,
        "fauna": [
            {"kind": "pigeon", "x": 572, "y": 228, "range": 8, "speed": 0.3, "rate": 2.0},
            {"kind": "pigeon", "x": 594, "y": 234, "range": 6, "speed": 0.25, "rate": 1.6, "flip": True},
            {"kind": "pigeon", "x": 606, "y": 225, "range": 0, "speed": 0.0, "rate": 2.4},
            {"kind": "pigeon", "x": 186, "y": PARAPET[0] + 1, "range": 0, "speed": 0.0, "rate": 0.7},
            {"kind": "pigeon", "x": 452, "y": PARAPET[0] + 1, "range": 0, "speed": 0.0, "rate": 0.6, "flip": True},
            {"kind": "bird", "x": 120, "y": 36, "fly": 10.0, "rate": 4.0},
            {"kind": "bird", "x": 136, "y": 44, "fly": 10.0, "rate": 3.6},
            {"kind": "bird", "x": 150, "y": 38, "fly": 10.0, "rate": 4.4},
            {"kind": "night_bat", "x": 600, "y": 58, "fly": 12.0, "rate": 6.0},
            {"kind": "lamp_moth", "x": LAMP[0] + 2, "y": LAMP[1] - 64, "range": 7, "speed": 2.2, "rate": 9.0},
        ],
        "leaves": [[110, 160, 90, 90], [604, 180, 90, 90]],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
