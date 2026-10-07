"""Farrand / food court (F03): the row of food trucks and stalls along the back of the field at
closing time. TACOS still has its hatch lit, the COCOA stall glows, NOODLES has its shutter down
and a CLOSED card. In front, the court: bark chips over the lawn, a wash-up table with three mugs
drying on a rack (one with a chipped handle), a picnic table, and a half-barrel planter whose
timber mast holds the string lights strung out over the court like a canopy. Mags' soup cart,
counter wiped and pot lidded, stands ready to go home. Mats lead in from the cable walk on the
left and out to the audience lawn on the right, where the main stage glows past the bins."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from props import OUT, IRON, WOOD, ground_shadow, shrub, atlas_tree
import lib_farrand as F

ROOM = "F03"
W, H = 800, 480
WALK_TOP = 142
FAR_EDGE = 120
BACK = 141                       # where the truck row stands
KEEPSAKE = (748, 302)            # floor point of the keepsake pickup: keep clear and readable
MAGS = (605, 395)                # Mags stands here (drawn by the game)
TABLE0, TABLE1, PLANTER, CART, TREE, LAMP = (330, 250), (570, 345), (410, 350), (625, 225), (170, 235), (100, 350)
MAST_H = 150


def left_path(x):
    return float(np.interp(x, [0, 120, 250], [400, 398, 384]))


def right_path(x):
    return float(np.interp(x, [640, 720, 800], [402, 404, 405]))


# --- the truck row ------------------------------------------------------------------------------
def taco_goods(cv, x, y, w, h):
    """Inside the taco truck: steel shelf with tubs of salsa, a stack of foil, a hanging ticket rail."""
    cv.hline(x + 1, y + 12, w - 2, "#6a4a32")
    for k, c in enumerate(["#c8382c", "#e0b23a", "#4a8a3a", "#e6d6b1", "#c8382c", "#7a4a8a", "#e0b23a"]):
        tx = x + 3 + k * ((w - 8) // 7)
        cv.rect(tx, y + 8, 5, 4, OUT); cv.rect(tx + 1, y + 9, 3, 3, c); cv.hline(tx + 1, y + 9, 3, shade(c, 0.35))
    cv.hline(x + 4, y + 15, w - 8, "#8a6a4a")
    for k in range(5):
        cv.rect(x + 8 + k * 9, y + 15, 4, 5, "#f2ead6"); cv.hline(x + 8 + k * 9, y + 19, 4, "#c8b89a")


def cocoa_counter(cv, x0, top, w):
    """On the cocoa counter: the urn, a pyramid of mugs, a jar of marshmallows, a tip tin."""
    ux = x0 + 10
    cv.rect(ux, top - 18, 13, 18, OUT); cv.rect(ux + 1, top - 17, 11, 16, F.STEEL[4]); cv.vline(ux + 2, top - 17, 16, F.STEEL[5])
    cv.rect(ux + 3, top - 20, 7, 2, OUT); cv.rect(ux + 12, top - 6, 3, 2, OUT); cv.px(ux + 14, top - 4, "#5a3a2a")
    for row, n in enumerate((4, 3, 2)):
        for k in range(n):
            mx = x0 + 34 + row * 3 + k * 7
            my = top - 5 - row * 5
            c = ["#c84a3c", "#e6d6b1", "#425da6", "#2e7a5a"][(k + row) % 4]
            cv.rect(mx, my, 6, 5, OUT); cv.rect(mx + 1, my + 1, 4, 4, c); cv.hline(mx + 1, my + 1, 4, shade(c, 0.3))
    jx = x0 + w - 36
    cv.rect(jx, top - 12, 10, 12, OUT); cv.rect(jx + 1, top - 11, 8, 11, "#cfe0e8"); cv.rect(jx + 1, top - 14, 8, 3, "#c84a3c")
    for k in range(5):
        cv.rect(jx + 2 + (k % 3) * 2, top - 9 + (k // 3) * 3, 2, 2, "#f6f0e2")
    cv.rect(x0 + w - 20, top - 6, 7, 6, OUT); cv.rect(x0 + w - 19, top - 5, 5, 5, F.HAZARD[3])


def cocoa_back(cv, x, y, w, h):
    """Back of the cocoa stall: mugs on hooks, tins and a chalk menu."""
    for k in range(x + 4, x + w // 2, 8):
        cv.vline(k + 2, y + 4, 2, F.WIRE)
        c = ["#c84a3c", "#e6d6b1", "#425da6"][(k // 8) % 3]
        cv.rect(k, y + 6, 5, 5, OUT); cv.rect(k + 1, y + 7, 3, 3, c)
    for k in range(x + 6, x + w // 2, 9):
        c = ["#7a4a2a", "#c8a03a", "#5a7a4a"][(k // 9) % 3]
        cv.rect(k, y + 16, 6, 7, OUT); cv.rect(k + 1, y + 17, 4, 6, c); cv.hline(k + 1, y + 17, 4, shade(c, 0.3))
    F.menu_board(cv, x + w // 2 + 8, y + 2, w // 2 - 12, h - 4, lines=4, seed=5)


def truck_row(bg):
    """Paint the trucks and stalls along the back; returns twinkle points and light spills."""
    pts = []
    taco, tax, tay, tinfo = F.food_truck(180, 80, pal=F.TRUCK_TEAL, name="TACOS", seed=11, goods=taco_goods)
    tx0 = 96 - tax
    bg.paste(taco, tx0, BACK - tay)
    pts += [[p[0] + tx0, p[1] + BACK - tay, p[2], p[3]] for p in tinfo["bulbs"]]
    stall, sax, say, sb = F.market_stall(118, 88, canopy=F.RED, name="COCOA", seed=13, counter=cocoa_counter, back=cocoa_back)
    sx0 = 268 - sax
    bg.paste(stall, sx0, BACK - say)
    pts += [[p[0] + sx0, p[1] + BACK - say, p[2], p[3]] for p in sb]
    noodle, nax, nay, ninfo = F.food_truck(168, 78, pal=F.TRUCK_PINK, name="NOODLES", open_=False, seed=12, facing=1,
                                          trim=["#2c4a4c", "#e6d6b1"])
    nx0 = 446 - nax
    bg.paste(noodle, nx0, BACK - nay)
    hatch_t = tinfo["hatch"]
    return pts, {
        "taco": ((hatch_t[0] + hatch_t[2]) // 2 + tx0, BACK - tay + hatch_t[3]),
        "stall": (268, BACK),
        "taco_roof": (tx0 + taco.w - 12, BACK - 80 + 2),
        "stall_peak": (sx0 + stall.w - 30, BACK - 88 + 2),
        "noodle_roof": (nx0 + 10, BACK - 78 + 3),
    }


def back_right(bg):
    """Behind the cart: the bins and the token kiosk, shut for the night."""
    F.wheelie_bins(bg, 548, BACK)
    k, kax, kay, _ = F.kiosk(60, 66, name="TOKENS", seed=3)
    bg.paste(k, 722 - kax, BACK - kay)


# --- props --------------------------------------------------------------------------------------
def washup_table():
    """Placement 0 (object cups): the wash-up station: a basin of suds, a jerrycan with a tap,
    a wire drying rack with three mugs upside down (the blue one's handle chipped), tea towel."""
    def items(cv, x0, top, width):
        # jerrycan with tap at the left end, drip tray
        jx = x0 + 6
        cv.rect(jx, top - 18, 16, 18, OUT); cv.rect(jx + 1, top - 17, 14, 17, "#3a6ab0"); cv.hline(jx + 1, top - 17, 14, "#5a8ad0")
        cv.vline(jx + 2, top - 16, 15, "#5a8ad0"); cv.rect(jx + 4, top - 21, 6, 3, OUT); cv.rect(jx + 5, top - 20, 4, 2, "#e6e2d8")
        cv.rect(jx + 15, top - 6, 4, 2, OUT); cv.px(jx + 18, top - 4, "#9ad0e8")
        # washing-up basin with suds
        bx = x0 + 28
        cv.rect(bx, top - 9, 34, 9, OUT); cv.rect(bx + 1, top - 8, 32, 8, "#4a9a8a"); cv.hline(bx + 1, top - 8, 32, "#6ab8a6")
        for k, sx in enumerate(range(bx + 3, bx + 31, 4)):
            cv.rect(sx, top - 11 - (k % 2), 4, 3, "#e8f0f2"); cv.px(sx + 1, top - 12 - (k % 2), "#ffffff")
        cv.rect(bx + 24, top - 15, 2, 6, "#c8a03a")   # brush handle
        # wire drying rack with three mugs upside down
        rx = x0 + 70
        cv.rect(rx, top - 3, 46, 3, OUT); cv.hline(rx + 1, top - 2, 44, F.STEEL[4])
        for k in range(rx + 2, rx + 45, 4):
            cv.vline(k, top - 14, 11, F.STEEL[3])
        cv.hline(rx + 1, top - 14, 44, F.STEEL[4])
        for k, c in enumerate(["#c84a3c", "#e6d6b1", "#425da6"]):
            mx = rx + 5 + k * 14
            cv.rect(mx, top - 13, 10, 10, OUT); cv.rect(mx + 1, top - 12, 8, 9, c)
            cv.vline(mx + 1, top - 12, 9, shade(c, 0.3)); cv.vline(mx + 8, top - 12, 9, shade(c, -0.25))
            cv.hline(mx + 1, top - 4, 8, shade(c, -0.35))           # rim at the bottom: upside down
            if k < 2:
                cv.rect(mx + 10, top - 11, 3, 6, OUT); cv.vline(mx + 10, top - 10, 4, c)
            else:   # the chipped one: half a handle and a nick in the rim
                cv.rect(mx + 10, top - 11, 3, 3, OUT); cv.px(mx + 10, top - 10, c)
                cv.px(mx + 6, top - 4, OUT); cv.px(mx + 7, top - 4, "#d8dce8")
            cv.px(mx + 4, top - 2, "#9ad0e8")                       # drip
        # tea towel hung over the edge, a hand-written card
        cv.rect(x0 + 120, top - 1, 14, 12, "#e6e2d8"); cv.hline(x0 + 120, top + 3, 14, "#c84a3c"); cv.hline(x0 + 120, top + 8, 14, "#c84a3c")
        cv.rect(x0 + 120, top + 11, 14, 1, "#b8b0a0")
        card = "CUPS"
        cw = text_width(card) + 6
        cx_ = x0 + width - cw - 4
        cv.rect(cx_, top - 13, cw, 11, OUT); cv.rect(cx_ + 1, top - 12, cw - 2, 9, "#f2ead6")
        text(cv, card, cx_ + 3, top - 13, "#2c4a4c")
        cv.line(cx_ + 4, top - 2, cx_ + 2, top, OUT); cv.line(cx_ + cw - 5, top - 2, cx_ + cw - 3, top, OUT)
    cv, ax, ay = F.trestle_table(150, 30, cloth=None, seed=20, items=items, top_height=20)
    # a bucket under the table
    cv.rect(ax - 40, ay - 10, 12, 10, OUT); cv.rect(ax - 39, ay - 9, 10, 9, "#c8a03a"); cv.hline(ax - 39, ay - 9, 10, "#e0c060")
    return cv, ax, ay


def mags_table():
    """Placement 1: the picnic table where Mags is packing up: a bus tub of bowls, her thermos,
    the folded apron, the cash tin shut."""
    def items(cv, x0, top, width):
        bx = x0 + 18
        cv.rect(bx, top - 9, 30, 9, OUT); cv.rect(bx + 1, top - 8, 28, 8, "#3a3a4a"); cv.hline(bx + 1, top - 8, 28, "#5a5a6a")
        for k in range(4):
            cv.rect(bx + 3 + k * 6, top - 12, 6, 4, "#e6e2d8"); cv.hline(bx + 3 + k * 6, top - 12, 6, "#ffffff"); cv.px(bx + 3 + k * 6, top - 9, "#9a948a")
        tx = x0 + 60
        cv.rect(tx, top - 16, 7, 16, OUT); cv.rect(tx + 1, top - 15, 5, 15, "#2e7a5a"); cv.vline(tx + 1, top - 15, 15, "#4a9a76")
        cv.rect(tx, top - 19, 7, 4, OUT); cv.rect(tx + 1, top - 18, 5, 2, F.STEEL[4])
        cv.rect(x0 + 74, top - 4, 18, 4, OUT); cv.rect(x0 + 75, top - 3, 16, 3, "#c84a3c"); cv.hline(x0 + 75, top - 3, 16, "#e06a5a")
        cv.hline(x0 + 78, top - 1, 10, "#e6d6b1")
        cv.rect(x0 + 98, top - 7, 18, 7, OUT); cv.rect(x0 + 99, top - 6, 16, 6, "#3e6a4a"); cv.hline(x0 + 99, top - 6, 16, "#5c897c")
        cv.rect(x0 + 105, top - 4, 4, 2, "#c8a03a")
    return F.picnic_table(140, 30, seed=21, items=items)


def pine_with_lights():
    tree, tax, tay = atlas_tree(98, cell=6, seed=4)
    rng = np.random.default_rng(6)
    pts = []
    # a spiral of bulbs wound down the pine
    for (x0, y0, x1, y1) in [(tree.w // 2 - 6, 18, tree.w // 2 + 8, 30), (tree.w // 2 + 10, 32, tree.w // 2 - 14, 48),
                             (tree.w // 2 - 16, 50, tree.w // 2 + 18, 66)]:
        pts += F.festoon(tree, x0, y0, x1, y1, sag=4, every=6, seed=int(rng.integers(100)))
    return tree, tax, tay, pts


# --- background ---------------------------------------------------------------------------------
def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=31)
    twinkles = []

    sky, _ = F.farrand_sky(W, 150, panels=(1, 0, 1, 0), offset=300, scale=2.0, stars=46, seed=11)
    bg.a[:150] = sky
    F.far_hedge(bg, 0, W, FAR_EDGE, seed=13)
    stage_pts = F.distant_stage(bg, 812, FAR_EDGE + 2, w=170, h=60, seed=14)
    F.treeline_back(bg, -10, 820, FAR_EDGE + 6, seed=15, heights=(64, 100), gap=(46, 80), skip=[(700, 820)])
    tower_pts = F.light_tower(bg, 640, FAR_EDGE + 4, 96, seed=6)
    F.lawn(bg, 0, FAR_EDGE, W, H - FAR_EDGE, seed=33, clover=0.03, leaves=0.08, stripes=(46, 0.3))
    bg.rect(0, FAR_EDGE, W, WALK_TOP - FAR_EDGE, C("#2a2440", 0.3))

    # the food truck row and the clutter behind the cart
    row_pts, spots = truck_row(bg)
    twinkles += row_pts
    back_right(bg)

    # --- floor -------------------------------------------------------------------------------------
    keep = F.blob_mask(W, H, KEEPSAKE[0], KEEPSAKE[1] - 10, 34, 26, seed=1, rough=0.0)
    # a pad of mats under each serving hatch for the queue
    F.mat_walkway(bg, lambda x: 160.0, width=34, mat=(46, 17), seed=31, x0=54, x1=146)
    F.mat_walkway(bg, lambda x: 160.0, width=34, mat=(46, 17), seed=34, x0=222, x1=314)
    # bark chips over the court
    court = F.blob_mask(W, H, 470, 352, 214, 84, seed=5, rough=0.2, cell=40) & ~keep
    F.straw_bed(bg, court, seed=7)
    # mats in from the cable walk and out to the audience lawn
    F.mat_walkway(bg, left_path, width=44, seed=32, x0=0, x1=246)
    F.mat_walkway(bg, right_path, width=44, seed=33, x0=652, x1=W)
    F.trodden_patch(bg, 560, 186, 50, 14, seed=4)
    F.trodden_patch(bg, 120, 214, 40, 16, seed=5)
    # queue marks taped in front of the open hatches
    tx, ty = spots["taco"]
    F.queue_marks(bg, tx, 150, n=3, gap=8)
    F.queue_marks(bg, spots["stall"][0], 150, n=3, gap=8)
    # cables: from the trucks round the court to the cable walk, a ramp over the left mats
    F.cable_run(bg, [(206, 142), (214, 190), (200, 260), (150, 330), (136, 380), (128, 430), (120, 480)], count=3, seed=9, tape_every=44)
    F.cable_ramp_vertical(bg, 133, int(left_path(133)) - 23, int(left_path(133)) + 23)
    F.cable_run(bg, [(536, 142), (552, 176), (600, 196), (660, 200), (690, 168), (700, 142)], count=2, seed=10, tape_every=50)
    # rain in the dips; things dropped at closing
    F.puddle(bg, 238, 444, 22, 6, seed=7)
    F.puddle(bg, 52, 300, 24, 7, seed=8, reflect=("#f6cf7a", "#e8a0d0"))
    F.puddle(bg, 690, 448, 22, 6, seed=9)
    rng = np.random.default_rng(13)
    for kind, (x, y) in zip(["cup", "flyer", "band", "cup_down", "flyer", "cup", "cap"],
                            [(300, 330), (470, 420), (520, 280), (360, 405), (60, 250), (690, 360), (230, 200)]):
        F.litter(bg, x, y, kind, seed=int(rng.integers(100)))
    for (x, y) in [(260, 300), (500, 300), (650, 300), (440, 260)]:   # paper food boats
        bg.rect(x, y, 8, 3, OUT); bg.rect(x + 1, y, 6, 2, "#e6d6b1"); bg.px(x + 2, y, "#c84a3c")

    # --- light -----------------------------------------------------------------------------------
    F.light_pool(bg, tx, 170, 76, 22, strength=0.4)
    F.light_pool(bg, spots["stall"][0], 168, 62, 20, strength=0.34)
    F.light_pool(bg, LAMP[0] + 6, LAMP[1] + 4, 44, 14, strength=0.24)
    F.light_pool(bg, PLANTER[0], 320, 210, 64, strength=0.14)       # under the canopy of strings
    F.light_pool(bg, 800, 404, 70, 24, strength=0.16)               # the audience lawn's glow

    # --- edges -----------------------------------------------------------------------------------
    for x0_ in (0, W - 20):
        bg.rect(x0_, WALK_TOP, 20, H - WALK_TOP, C("#0d0b16", 0.32))
    rng = np.random.default_rng(17)
    for y in range(WALK_TOP - 4, H - 20, 14):
        for xx, gap in ((-8, (366, 426)), (W - 12, (372, 432))):
            if gap[0] < y < gap[1]:
                continue
            bg.paste(shrub(0, 0, 20, 16, seed=int(rng.integers(1e6))), xx, y)
    x = -6
    while x < W:
        bw = int(rng.integers(30, 40))
        bale, _, _ = F.hay_bales(bw, 18, seed=int(rng.integers(1e6)))
        bg.paste(bale, x, H - 25)
        x += bw + int(rng.integers(0, 12))
    bg.rect(0, H - 24, W, 24, C("#0d0b16", 0.35))
    bg.save(os.path.join(out, "background.png"))

    # --- props -----------------------------------------------------------------------------------
    props = {}

    def save(index, sprite, ax, ay, extra=None):
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [int(ax), int(ay)]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(0, *washup_table())
    save(1, *mags_table())
    planter, pax, pay, crown = F.half_barrel_planter(70, 44, seed=22, mast=MAST_H, mast_dx=16)
    save(2, planter, pax, pay)
    save(3, *F.soup_cart(86, 45, seed=23))
    tree, tax, tay, tree_pts = pine_with_lights()
    save(4, tree, tax, tay)
    pole, plx, ply, lbulb = F.festoon_pole(55, seed=24)
    save(5, pole, plx, ply)

    # string lights radiating from the mast in the planter, cut into y-sorted pieces
    mx, my = PLANTER[0] - pax + crown[0], PLANTER[1] - pay + crown[1]
    pole_top = (LAMP[0] - plx + plx, LAMP[1] - 55 + 3)
    tree_top = (TREE[0] + 4, TREE[1] - 78)
    cart_tip = (CART[0] - 38, CART[1] - 86)
    occ = []
    targets = [
        ("s-taco", spots["taco_roof"], BACK, 26, 6),
        ("s-stall", spots["stall_peak"], BACK, 20, 5),
        ("s-noodle", spots["noodle_roof"], BACK, 14, 4),
        ("s-cart", cart_tip, CART[1], 12, 3),
        ("s-tree", tree_top, TREE[1], 18, 5),
        ("s-pole", pole_top, LAMP[1], 22, 5),
    ]
    for i, (name, (tx_, ty_), floor, sag, pieces) in enumerate(targets):
        occ += F.festoon_occluders(ROOM, out, name, mx, my, PLANTER[1], tx_, ty_, floor, sag=sag, every=9,
                                   seed=40 + i, pieces=pieces)

    # twinkles: every bulb drawn on the background and props, plus the hanging strings
    string_pts = []
    for i, (name, (tx_, ty_), floor, sag, pieces) in enumerate(targets):
        tmp = Canvas(W, H)
        string_pts += F.festoon(tmp, mx, my, tx_, ty_, sag=sag, every=9, seed=40 + i)
    tree_pts = [[TREE[0] - tax + p[0], TREE[1] - tay + p[1], p[2], p[3]] for p in tree_pts]
    lamp_xy = (LAMP[0] - plx + lbulb[0], LAMP[1] - ply + lbulb[1])

    return {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": occ,
        "props": props,
        "label_only": [],
        "fauna": [
            {"kind": "moth", "x": lamp_xy[0] - 3, "y": lamp_xy[1] + 4, "range": 6, "speed": 2.0, "rate": 8.0},
            {"kind": "moth", "x": lamp_xy[0] + 5, "y": lamp_xy[1] + 1, "range": 5, "speed": 1.5, "rate": 7.0, "flip": True},
            {"kind": "moth", "x": spots["taco"][0] - 10, "y": BACK - 50, "range": 7, "speed": 1.8, "rate": 8.0},
            {"kind": "raccoon", "x": 630, "y": 150, "range": 14, "speed": 0.3, "rate": 3.0},
            {"kind": "bat", "x": 200, "y": 26, "fly": 16.0, "rate": 7.0},
        ],
        "leaves": [],
        "layers": [
            {"kind": "beam", "x": 760, "y": FAR_EDGE - 52, "angle": -104, "sweep": 18, "period": 9.5, "phase": 0.5,
             "length": 130, "width": 24, "color": "c8b0ff", "alpha": 0.14, "floor": -400},
            {"kind": "beam", "x": 790, "y": FAR_EDGE - 52, "angle": -84, "sweep": 16, "period": 11.0, "phase": 2.0,
             "length": 130, "width": 24, "color": "ffd0e8", "alpha": 0.13, "floor": -400},
            {"kind": "twinkle", "points": twinkles + tree_pts, "rate": 1.8, "min": 0.4},
            {"kind": "twinkle", "points": string_pts, "rate": 2.2, "min": 0.45},
            {"kind": "twinkle", "points": [[x, y, "f6dca0", 1] for (x, y) in stage_pts] + [[x, y, "fff0c4", 1] for (x, y) in tower_pts],
             "rate": 1.2, "min": 0.5},
            {"kind": "particles", "style": "dust", "count": 6, "rect": [spots["taco"][0] - 30, BACK - 60, 60, 30],
             "speed": [0, -6], "color": "e8e0d0"},
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT))[:300])
