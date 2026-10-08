"""Fountain Court (C01): the game's hub, the real Dalton Trumbo Fountain Court in front of CU
Boulder's University Memorial Center. 1920x540, the camera scrolls across three screens.

West (left) to east (right), across the back:
  the food-truck lane under string lights, with the Flatirons in the last of the sunset behind;
  the north gate, two lanes signposted MACKY and OLD MAIN with both buildings small in the distance;
  the UMC's sandstone front: CU Book Store on the west wing, the open main doors in the pavilion
  (UNIVERSITY MEMORIAL CENTER on its frieze), the Career Center on the east wing;
  the gate to Norlin Quad, Norlin's portico far off between pines;
  Farrand Hall, red brick and sandstone, four floors of dorm windows and its lobby doors.
The court: the long fountain basin with its row of jets and bronze plaque, a sandstone-tiled court
around it, brick-red paver paths to every exit (the Hill across Broadway on the left edge, Farrand
Field off the right edge, Engineering down the bottom walk), picnic tables in front of the trucks,
a coffee cart, the campus map and an events column, chalk on the paving, a lot of open floor."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import flagstones, light_pool, ashlar_wall, LEAVES
from props import lamp_post, park_bench, shrub, grass_tuft, atlas_tree, MUM, LEAF, OUT, IRON
from facade import TRIM, steps
from lib_farrand import (lawn, food_truck, picnic_table, festoon, treeline_back, back_tree, far_hedge, a_frame_sign,
                         half_barrel_planter,
                         TRUCK_TEAL, TRUCK_CREAM, TRUCK_PINK, TRUCK_MUSTARD, STRIPE_TRIM, queue_marks)
from c01_lib import (court_sky, distant_landmark, stone_pier, fingerpost, street_sign, umc_front, farrand_front,
                     hanging_banner, paver_poly, court_tiles, chalk_art, drain_grate, tree_grate, parking_lane,
                     fountain_basin, fountain_front, fountain_layers, coffee_cart, map_board, event_column,
                     bike_rack, bins, FOUNTAIN, PAVE, WALL, PAVER, SHADOW, GOLD)

ROOM = "C01"
W, H = 1920, 540
BASE = 212                      # walk_bounds top: the back of the court
SKY_H = 204
WEST = (0, 548)                 # food-truck lane
NORTH_GAP = (548, 724)          # lanes to Macky (590) and Old Main (684)
LANE_MACKY, LANE_OLDMAIN = 590, 684
UMC = (724, 1476)
PAVILION = (1010, 1190)
BOOK, MAIN_DOOR, CAREER = 860, 1100, 1340
DOOR_BOTTOM = 216
NORLIN_GAP = (1476, 1624)
LANE_NORLIN = 1550
FARRAND = (1624, 1920)
FARRAND_DOOR = 1770
COURT = (840, 232, 520, 244)    # sandstone-tiled court around the fountain: x, y, w, h
PROMENADE = (378, 418)          # east-west walk from the Hill crossing to Farrand Field
ENG_LANE = 1540                 # the walk down to Engineering
TRUCKS = [(106, TRUCK_MUSTARD, "GREEN CHILE", 1), (272, TRUCK_PINK, "DUMPLINGS", -1), (438, TRUCK_TEAL, "WAFFLES", 1)]
LAMPS = [(21, 776, 256), (22, 1424, 256), (23, 922, 308), (24, 1278, 308), (25, 604, 432), (26, 1602, 432), (27, 1842, 300)]
LAWNS = [(40, 434, 470, 70), (1624, 434, 256, 70)]
TREES = [(29, 252, 480, 5, 120), (30, 1732, 488, 6, 132)]


# ---------------------------------------------------------------------------------------------
def paint_west(bg, twinkles):
    """Food-truck lane: dark trees against the sunset, a low sandstone wall, string light poles."""
    x0, x1 = WEST
    treeline_back(bg, x0 - 20, x1 + 10, BASE - 14, seed=11, heights=(64, 100), gap=(44, 70), cells=(5, 6, 5, 5))
    far_hedge(bg, x0, x1, BASE - 16, seed=4, height=9)
    ashlar_wall(bg, x0, BASE - 18, x1 - x0, 18, WALL, seed=5)
    # string-light poles behind the wall and the festoons strung over the trucks
    poles = [8, 189, 355, 532]
    for px in poles:
        bg.rect(px - 1, BASE - 98, 3, 82, OUT); bg.vline(px, BASE - 97, 80, "#5e4430")
        bg.rect(px - 3, BASE - 100, 7, 3, OUT)
    for a, b in zip(poles, poles[1:]):
        twinkles += festoon(bg, a, BASE - 96, b, BASE - 96, sag=16, every=8, seed=a)
    twinkles += festoon(bg, poles[0], BASE - 92, poles[2], BASE - 90, sag=26, every=9, seed=77)
    twinkles += festoon(bg, poles[1], BASE - 90, poles[3], BASE - 92, sag=24, every=9, seed=78)
    # Broadway street sign at the far left, over the wall
    street_sign(bg, 26, BASE - 64, BASE - 18, "BROADWAY")


def paint_gap_far(bg, x0, x1, horizon, seed=0):
    """Ground seen through a gap in the back: the far lawn and hedge between the piers."""
    rng = np.random.default_rng(seed)
    bg.rect(x0, horizon, x1 - x0, BASE - horizon, "#22302b")
    for yy in range(horizon, BASE, 3):
        bg.hline(x0, yy, x1 - x0, "#273629" if (yy // 3) % 2 else "#22302b")
    for _ in range((x1 - x0) * (BASE - horizon) // 14):
        bg.px(int(rng.integers(x0, x1)), int(rng.integers(horizon, BASE)), "#2f4237")


def far_lane(bg, cx, top, w_top, w_base, seed=0):
    """A path running away from the court: pavers narrowing toward the horizon."""
    pts = [(cx - w_top // 2, top), (cx + w_top // 2, top), (cx + w_base // 2, BASE), (cx - w_base // 2, BASE)]
    bg.poly(pts, PAVER[2])
    for k, yy in enumerate(range(top, BASE, 3)):
        t = (yy - top) / (BASE - top)
        half = (w_top + (w_base - w_top) * t) / 2
        bg.hline(int(cx - half), yy, int(2 * half), PAVER[1])
        for xx in range(int(cx - half) + (k % 2) * 3, int(cx + half), 6):
            bg.px(xx, yy, PAVER[1])
    bg.line(cx - w_top // 2, top, cx - w_base // 2, BASE, TRIM[2])
    bg.line(cx + w_top // 2, top, cx + w_base // 2, BASE, TRIM[2])


def paint_north_gap(bg, twinkles):
    """Two lanes north: Macky's twin towers on the left, Old Main's tower on the right."""
    x0, x1 = NORTH_GAP
    horizon = BASE - 44
    paint_gap_far(bg, x0, x1, horizon, seed=8)
    macky = distant_landmark(4, 64, brightness=0.7)
    oldmain = distant_landmark(3, 74, brightness=0.72)
    bg.paste(macky, LANE_MACKY - macky.shape[1] // 2 - 6, horizon + 4 - macky.shape[0])
    bg.paste(oldmain, LANE_OLDMAIN - oldmain.shape[1] // 2 + 8, horizon + 6 - oldmain.shape[0])
    far_hedge(bg, x0, x1, horizon + 4, seed=9, height=6)
    for (tx, cell, h) in [(x0 + 4, 6, 84), (636, 5, 70), (x1 - 4, 5, 78)]:
        spr = back_tree(h, cell, brightness=0.6, seed=tx)
        bg.paste(spr, tx - spr.shape[1] // 2, BASE - 10 - spr.shape[0])
    far_lane(bg, LANE_MACKY, horizon + 4, 8, 40, seed=1)
    far_lane(bg, LANE_OLDMAIN, horizon + 6, 8, 40, seed=2)
    # low wall pieces and the three piers
    for (a, b) in [(562, 570), (610, 629), (643, 664), (704, 710)]:
        ashlar_wall(bg, a, BASE - 14, b - a, 14, WALL, seed=a)
    for px in (548, 629, 710):
        twinkles.append([*stone_pier(bg, px, BASE, w=14, h=38), "fde9b6", 1])
    fingerpost(bg, 636, BASE - 76, BASE - 52, [("MACKY", -1, BASE - 74), ("OLD MAIN", 1, BASE - 62)])


def paint_norlin_gap(bg, twinkles):
    """The gate to Norlin Quad: the library's portico far off between two pines."""
    x0, x1 = NORLIN_GAP
    horizon = BASE - 46
    paint_gap_far(bg, x0, x1, horizon, seed=12)
    norlin = distant_landmark(1, 60, brightness=0.7)
    bg.paste(norlin, LANE_NORLIN - norlin.shape[1] // 2, horizon + 6 - norlin.shape[0])
    far_hedge(bg, x0, x1, horizon + 4, seed=13, height=6)
    for (tx, cell, h) in [(x0 + 12, 6, 96), (x1 - 10, 6, 104)]:
        spr = back_tree(h, cell, brightness=0.62, seed=tx)
        bg.paste(spr, tx - spr.shape[1] // 2, BASE - 8 - spr.shape[0])
    far_lane(bg, LANE_NORLIN, horizon + 6, 10, 44, seed=3)
    for (a, b) in [(1490, 1528), (1572, 1610)]:
        ashlar_wall(bg, a, BASE - 14, b - a, 14, WALL, seed=a)
    for px in (1476, 1610):
        twinkles.append([*stone_pier(bg, px, BASE, w=14, h=38), "fde9b6", 1])
    fingerpost(bg, 1504, BASE - 74, BASE - 52, [("NORLIN", 1, BASE - 72)])


# ---------------------------------------------------------------------------------------------
def path_quad(bg, a, b, width, seed):
    """A straight paver path from point a to point b, `width` wide (measured across x)."""
    (ax, ay), (bx, by) = a, b
    h = width / 2
    return paver_poly(bg, [(ax - h, ay), (ax + h, ay), (bx + h, by), (bx - h, by)], seed=seed)


def paint_floor(bg, reflections):
    # base paving everywhere
    flagstones(bg, 0, BASE, W, H - BASE, PAVE, seed=21, row0=9, row1=15, moss=0.08,
               leaf_clusters=[(150, 300, 90, 60), (420, 470, 60, 40), (252, 470, 50, 50), (1732, 480, 50, 40),
                              (1880, 260, 40, 30), (700, 250, 60, 20), (1600, 250, 60, 20)])
    bg.rect(0, BASE, W, 2, C(SHADOW, 0.45))
    # truck lane on the west side
    parking_lane(bg, 0, BASE, WEST[1], 40, seed=4, bays=[189, 355])
    queue_marks_xy = [(106, 262), (272, 262), (438, 262)]
    # paths: the east-west promenade, the north lanes, Norlin, Farrand's door, the walk to Engineering
    y0, y1 = PROMENADE
    paver_poly(bg, [(0, y0), (W, y0), (W, y1), (0, y1)], seed=31)
    path_quad(bg, (LANE_MACKY, BASE), (LANE_MACKY - 12, y0 + 3), 40, seed=32)
    path_quad(bg, (LANE_OLDMAIN, BASE), (COURT[0] + 20, COURT[1] + 70), 40, seed=33)
    path_quad(bg, (LANE_NORLIN, BASE), (COURT[0] + COURT[2] - 20, COURT[1] + 70), 44, seed=34)
    path_quad(bg, (FARRAND_DOOR, BASE), (FARRAND_DOOR - 30, y0 + 3), 42, seed=35)
    path_quad(bg, (ENG_LANE - 10, y1 - 3), (ENG_LANE, H), 44, seed=36)
    # the fountain court: brick border and big sandstone flags
    cx, cy, cw, ch = COURT
    paver_poly(bg, [(cx - 8, cy - 8), (cx + cw + 8, cy - 8), (cx + cw + 8, cy + ch + 8), (cx - 8, cy + ch + 8)], seed=37)
    court_tiles(bg, cx, cy, cw, ch, seed=38)
    court_inlay(bg)
    for (xx, yy, ww, hh) in [(cx, cy, cw, 1), (cx, cy + ch - 1, cw, 1), (cx, cy, 1, ch), (cx + cw - 1, cy, 1, ch)]:
        bg.rect(xx, yy, ww, hh, TRIM[3])
    # warm paver runner from the UMC doors to the fountain, inlaid in the court
    paver_poly(bg, [(MAIN_DOOR - 30, BASE + 4), (MAIN_DOOR + 30, BASE + 4), (MAIN_DOOR + 30, FOUNTAIN["back"] - 4),
                    (MAIN_DOOR - 30, FOUNTAIN["back"] - 4)], seed=39)
    steps(bg, MAIN_DOOR, DOOR_BOTTOM, 60, 2, rise=4, spread=5)
    # the fountain basin (the near rim is a prop)
    fountain_basin(bg, reflections=reflections, seed=5)
    light_pool(bg, MAIN_DOOR, FOUNTAIN["front"] + 22, 170, 22, color="#9ad0e8", strength=0.12)
    # drains, tree grates, chalk
    for (dx, dy) in [(944, 380), (1252, 380), (700, 470), (1460, 300)]:
        drain_grate(bg, dx, dy)
    # two lawns below the promenade, each holding one of the court's trees
    for (lx, ly, lw, lh) in LAWNS:
        lawn(bg, lx, ly, lw, lh, seed=lx, tufts=0.9, leaves=0.04)
        for (xx, yy, ww, hh) in [(lx - 2, ly - 2, lw + 4, 2), (lx - 2, ly + lh, lw + 4, 2), (lx - 2, ly, 2, lh), (lx + lw, ly, 2, lh)]:
            bg.rect(xx, yy, ww, hh, TRIM[2])
        bg.hline(lx - 2, ly - 2, lw + 4, TRIM[4]); bg.hline(lx, ly, lw, C(SHADOW, 0.35))
    chalk_art(bg, 712, 444, seed=2)
    # queue marks in front of the truck hatches
    for (qx, qy) in queue_marks_xy:
        queue_marks(bg, qx, qy, n=3, gap=12)
    plaza_dressing(bg)
    # the Broadway crossing at the left edge, the path out to Farrand Field at the right edge
    from surfaces import asphalt
    asphalt(bg, 0, y0 - 6, 22, (y1 - y0) + 12, seed=9)
    for yy in range(y0 - 4, y1 + 6, 6):
        bg.rect(2, yy, 16, 3, "#d8d4c8"); bg.hline(2, yy, 16, "#ecead8")
    bg.rect(22, y0 - 6, 2, (y1 - y0) + 12, TRIM[2])
    # planting strip along the bottom edge, open where the walk to Engineering leaves
    rng = np.random.default_rng(14)
    gap0, gap1 = ENG_LANE - 26, ENG_LANE + 26
    for (a, b) in [(0, gap0), (gap1, W)]:
        bg.rect(a, 518, b - a, H - 518, "#22302b")
        bg.rect(a, 515, b - a, 3, WALL[4]); bg.hline(a, 515, b - a, WALL[5]); bg.hline(a, 518, b - a, WALL[1])
        for x in range(a - 4, b, 13):
            w = int(rng.integers(14, 24)); h = int(rng.integers(10, 16))
            if x + w > b + 2:
                continue
            bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.4 else None), x, 520 + int(rng.integers(0, 6)))
        for x in range(a + 6, b - 6, 37):
            grass_tuft(bg, x, 520, 6, seed=x)
    for xx in (gap0 - 3, gap1):
        bg.rect(xx, 512, 3, H - 512, WALL[3]); bg.vline(xx, 512, H - 512, WALL[5])


def plaza_dressing(bg):
    """The big flagstone apron between the truck lane and the promenade was one flat field: brick
    expansion bands, cast-iron manhole covers, oil stains where the trucks idle, hairline cracks,
    chewing-gum dots and a hopscotch of painted bike-lane arrows, all kept clear of the paths."""
    rng = np.random.default_rng(77)
    y0, y1 = PROMENADE
    top = BASE + 54
    # brick expansion bands crossing the apron, with a sandstone edge
    for bx in range(60, WEST[1] + 60, 150):
        paver_poly(bg, [(bx, top), (bx + 9, top), (bx + 9, y0 - 2), (bx, y0 - 2)], seed=bx, brick=(9, 3), edge=False)
        bg.rect(bx - 1, top, 1, y0 - 2 - top, C(SHADOW, 0.3))
    # oil stains and tyre marks where the trucks idle
    for (tx, _, _, facing) in TRUCKS:
        for k in range(3):
            ox = tx + int(rng.integers(-26, 26)); oy = 266 + int(rng.integers(-3, 14))
            bg.ellipse(ox, oy, int(rng.integers(10, 22)), int(rng.integers(4, 8)), C(SHADOW, 0.28))
        bg.rect(tx - 30, 286, 3, 22, C(SHADOW, 0.16)); bg.rect(tx + 22, 286, 3, 22, C(SHADOW, 0.16))
    # cast-iron manhole covers
    for (mx, my) in [(196, 330), (468, 334), (1180, 352), (704, 304)]:
        bg.ellipse(mx - 9, my - 4, 18, 8, C(SHADOW, 0.6))
        bg.ellipse(mx - 8, my - 4, 16, 7, "#3a3640")
        for q in range(-6, 7, 3):
            bg.line(mx + q, my - 2, mx + q - 1, my + 2, "#25222c")
        bg.hline(mx - 7, my - 3, 14, "#5a5560")
    # hairline cracks
    for _ in range(26):
        cx = int(rng.integers(20, WEST[1] - 20)); cy = int(rng.integers(top + 6, y0 - 8))
        for _ in range(int(rng.integers(8, 20))):
            bg.px(cx, cy, C(SHADOW, 0.4))
            cx += int(rng.choice([-1, 1, 1])); cy += int(rng.choice([-1, 0, 1]))
    # chewing gum and dropped confetti from the career fair
    for _ in range(46):
        gx = int(rng.integers(20, WEST[1] - 10)); gy = int(rng.integers(top, y0 - 4))
        bg.px(gx, gy, C(rng.choice(["#2a2630", "#d8d0b8", "#d86a7a", "#e8b84a", "#6aaac8"]), 0.75))
    # painted bike-lane arrows
    for ax in (330, 600):
        for k in range(3):
            bg.hline(ax + k * 22, 336, 12, C("#e8dcb8", 0.5))
            bg.poly([(ax + k * 22 + 12, 333), (ax + k * 22 + 17, 336), (ax + k * 22 + 12, 339)], C("#e8dcb8", 0.5))


def court_inlay(bg):
    """Brick bands inlaid in the court: a frame around the basin, axes out to the court's edges,
    and sandstone diamonds in the four quarters, so the big court is not one flat field."""
    cx, cy, cw, ch = COURT
    f = FOUNTAIN
    fx0, fx1, fy0, fy1 = f["x0"] - 20, f["x1"] + 20, f["back"] - 18, f["front"] + f["face"] + 16
    mid = (f["back"] + f["front"]) // 2 + 4
    for pts in ([(fx0, fy0), (fx1, fy0), (fx1, fy0 + 8), (fx0, fy0 + 8)], [(fx0, fy1 - 8), (fx1, fy1 - 8), (fx1, fy1), (fx0, fy1)],
                [(fx0, fy0), (fx0 + 8, fy0), (fx0 + 8, fy1), (fx0, fy1)], [(fx1 - 8, fy0), (fx1, fy0), (fx1, fy1), (fx1 - 8, fy1)],
                [(cx, mid - 4), (fx0, mid - 4), (fx0, mid + 4), (cx, mid + 4)], [(fx1, mid - 4), (cx + cw, mid - 4), (cx + cw, mid + 4), (fx1, mid + 4)],
                [(MAIN_DOOR - 4, fy1), (MAIN_DOOR + 4, fy1), (MAIN_DOOR + 4, cy + ch), (MAIN_DOOR - 4, cy + ch)]):
        paver_poly(bg, pts, seed=int(pts[0][0] + pts[0][1]), brick=(7, 3), edge=False)
    for (dx, dy) in [((cx + fx0) // 2, (cy + mid) // 2), ((fx1 + cx + cw) // 2, (cy + mid) // 2),
                     ((cx + fx0) // 2, (mid + cy + ch) // 2 + 6), ((fx1 + cx + cw) // 2, (mid + cy + ch) // 2 + 6)]:
        for (r, col) in [(16, TRIM[1]), (14, TRIM[3]), (9, PAVER[3]), (7, TRIM[2])]:
            bg.poly([(dx - r, dy), (dx, dy - r // 2), (dx + r, dy), (dx, dy + r // 2)], col)
        bg.px(dx, dy, TRIM[4])


def foundation_planting(bg):
    """Low shrubs and mums along the foot of the UMC and Farrand Hall, clear of every door."""
    rng = np.random.default_rng(41)
    beds = [(UMC[0] + 4, BOOK - 76), (BOOK + 76, PAVILION[0] - 4), (PAVILION[1] + 4, CAREER - 70), (CAREER + 70, UMC[1] - 4),
            (FARRAND[0] + 4, FARRAND_DOOR - 44), (FARRAND_DOOR + 44, FARRAND[1])]
    for (a, b) in beds:
        bg.rect(a, BASE - 2, b - a, 5, "#2a2220"); bg.hline(a, BASE + 3, b - a, TRIM[1])
        x = a - 2
        while x < b - 10:
            w = int(rng.integers(12, 20)); h = int(rng.integers(9, 14))
            if x + w > b + 2:
                break
            bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.35 else None), x, BASE + 3 - h)
            x += w - 3


def paint_lights(bg):
    """Stepped warm pools: lamps, truck hatches, shop doors, the coffee cart, Farrand's lobby."""
    for (_, lx, ly) in LAMPS:
        light_pool(bg, lx, ly, 46, 13, strength=0.22)
    for (tx, _, _, facing) in TRUCKS:
        light_pool(bg, tx + 6 * facing, 258, 40, 12, strength=0.2)
    for (dx, s) in [(BOOK, 0.22), (MAIN_DOOR, 0.24), (CAREER, 0.16), (FARRAND_DOOR, 0.22)]:
        light_pool(bg, dx, BASE + 12, 44, 10, strength=s)
    light_pool(bg, CAREER, BASE + 12, 40, 9, color="#bce0d6", strength=0.1)
    light_pool(bg, 1446, 346, 40, 11, strength=0.2)
    light_pool(bg, 540, 306, 26, 7, strength=0.08)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    sky, _ = court_sky(W, SKY_H, split=MAIN_DOOR, moon=(1700, 14, 8))
    bg.a[:SKY_H] = sky

    twinkles = []
    paint_west(bg, twinkles)
    paint_north_gap(bg, twinkles)
    paint_norlin_gap(bg, twinkles)
    glows, spots = umc_front(bg, UMC[0], UMC[1], BASE, PAVILION[0], PAVILION[1], BOOK, CAREER, DOOR_BOTTOM)
    twinkles += [[x, y, "fde9b6", 1] for (x, y) in glows]
    hanging_banner(bg, CAREER + 84, BASE - 98, 42, 30, "#2c4a6e", ["CAREER", "FAIR"])
    hanging_banner(bg, BOOK - 110, BASE - 98, 36, 30, GOLD[2], ["GO", "BUFFS"], ink="#141218")
    fglows, tv, fairy = farrand_front(bg, FARRAND[0], FARRAND[1], BASE, FARRAND_DOOR)
    twinkles += [[x, y, "fff0c4", 1] for (x, y) in fglows]

    reflections = [(x, 1) for x in spots if 1000 < x < 1200] + [(MAIN_DOOR, 3)]
    paint_floor(bg, reflections)
    foundation_planting(bg)
    paint_lights(bg)
    bg.save(os.path.join(out, "background.png"))

    # ----- props
    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made[:3]
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [int(ax), int(ay)]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(10, fountain_front(seed=6))
    for i, (tx, pal, name, facing) in enumerate(TRUCKS):
        save(11 + i, food_truck(width=140, height=76, pal=pal, name=name, open_=True, seed=20 + i, facing=facing,
                                trim=STRIPE_TRIM if i != 1 else ["#2c6a68", "#e6d6b1"]))
    save(14, coffee_cart(seed=3))
    save(15, map_board(seed=4))
    save(16, event_column(seed=5))
    save(17, picnic_table(width=104, seed=6))
    save(18, picnic_table(width=104, seed=7))
    save(19, park_bench())
    save(20, park_bench())
    for (idx, _, _) in LAMPS:
        save(idx, lamp_post(62))
    save(28, bike_rack(seed=8))
    for (idx, _, _, cell, hh) in TREES:
        save(idx, atlas_tree(hh, cell=cell, seed=idx))
    save(31, bins(seed=9))
    save(32, a_frame_sign(width=60, height=50, header="TRUCKS", lines=[("OPEN", "#2c4a4c", False), ("LATE", "#7e3a30", False)], seed=10))
    save(33, half_barrel_planter(width=64, height=44, seed=11))

    # ----- animated layers
    res = f"res://assets/art/rooms/{ROOM}/"
    layers = fountain_layers(seed=7)
    layers.append({"kind": "twinkle", "points": twinkles, "rate": 1.3, "min": 0.5})
    if fairy:
        layers.append({"kind": "twinkle", "points": [[x, y, "f2a0a0", 1] for (x, y) in fairy], "rate": 2.2, "min": 0.3})
    if tv:
        tx, ty, tw, th = tv
        for j, col in enumerate(["5a8ad8", "8ab0f0", "3a5ab0"]):
            layers.append({"kind": "blink", "pattern": "".join("1" if k == j else "0" for k in range(3)), "rate": 2.6,
                           "rects": [[tx + 1, ty + 1, tw - 2, th - 8, col, 0.55]]})

    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0, 1, 2, 3],
        "fauna": [
            {"kind": "pigeon", "x": 1040, "y": 394, "range": 12, "speed": 0.3, "rate": 2.0},
            {"kind": "pigeon", "x": 1062, "y": 400, "range": 8, "speed": 0.25, "rate": 1.6, "flip": True},
            {"kind": "pigeon", "x": 1168, "y": 392, "range": 10, "speed": 0.28, "rate": 1.8, "flip": True},
            {"kind": "pigeon", "x": 300, "y": 372, "range": 14, "speed": 0.3, "rate": 2.0},
            {"kind": "squirrel", "x": 300, "y": 494, "range": 4, "speed": 0.25, "rate": 1.2},
            {"kind": "raccoon", "x": 568, "y": 252, "range": 3, "speed": 0.2, "rate": 1.0, "flip": True},
            {"kind": "rabbit", "x": 1880, "y": 236, "range": 0, "speed": 0.0, "rate": 0.7},
            {"kind": "umc_moth", "x": 778, "y": 202, "range": 7, "speed": 1.4, "rate": 9.0},
            {"kind": "umc_moth", "x": 1426, "y": 202, "range": 6, "speed": 1.2, "rate": 9.0},
            {"kind": "bird", "x": 120, "y": 40, "fly": 9.0, "rate": 4.0},
            {"kind": "bird", "x": 860, "y": 30, "fly": 7.0, "rate": 3.5},
            {"kind": "night_bat", "x": 1560, "y": 50, "fly": 14.0, "rate": 6.0},
        ] + [{"kind": "mk2_goose", "x": 300 - 12 * k, "y": 24 + 5 * abs(k - 2), "fly": 11.0, "rate": 3.0} for k in range(5)],
        "leaves": [[20, 110, 520, 120], [1736, 380, 60, 100], [216, 380, 80, 90]],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
