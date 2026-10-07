"""Engineering loading court (E01): the service court behind the real CU Boulder Engineering Center
(1965, William Muchow with Pietro Belluschi) at night.

Back: the Engineering Center as it really looks: raw board-formed concrete (plank imprints, form-tie
holes, rain streaks under every ledge) beside rough pink-red Lyons sandstone, single-slope red tile
roofs, and stepped massing with concrete towers rising out of frame like grain silos (a stair tower
with a full-height slot on the left, the main tower over the dock, a third set back behind the shed
roof, the distant office tower with its red beacon). Deep-set narrow windows in concrete frames,
a few lit late. The dock block's ground floor is the loading dock: ENGINEERING CENTER on the
concrete canopy, the shared workshop's roll-up door open on a lit room (a welding screen flickering
blue behind it), DOCK 2 shut, a gas-cylinder cage and a materials rack against a sandstone panel.
Left: the low sandstone annex under a tile roof, bins and a dumpster. Right: the wing toward the
creek with a humming condenser. The facade is painted on a taller canvas (see paint_facade) so the
battle backdrop can show the tower tops.
Ground: a concrete apron in front of the doors, the asphalt court with loading-bay paint and tar
snakes, and the sandstone walk ("a path you can use") from the Norlin quad (bottom left) to the
footbridge over the creek (right). Before the bridge is repaired, its deck has a gap and a CLOSED
barricade (overlay while bridge_ready is unset)."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import light_pool
from props import OUT, IRON, LEAF, shrub, grass_tuft, MUM
from lib_umc import hazard_band, SAFETY, SHADOW, halo
import lib_eng as E
import ec_exterior as X

ROOM = "E01"
W, H = 960, 540
BASE = 142                       # foot of the facade = top of the walkable court
WALK = (20, 142, 920, 374)
MAIN = (300, 720)                # the Engineering block (x span)
WING = (720, 904)                # right wing x span
OPEN_DOOR = (472, 76, 70, 72)    # workshop roll-up (x, w, top, h): bottom on BASE
DOCK2 = (594, 70, 72)            # closed roll-up (x, w, top)
APRON = (300, 720, 230)          # concrete apron x span and its front edge
PATH = [(-10, 468), (180, 470), (600, 472), (680, 471), (740, 464), (790, 450), (830, 430), (858, 410),
        (880, 396), (900, 389), (970, 387)]
PATH_HALF = 17
BANK_X = 898                     # creek bank starts here (right edge of the court)
WATER_X = 920                    # the creek's near waterline
BRIDGE = (880, 376, 398)         # deck x start, north and south edge rows
LAMP = (115, 370)
ROOK = (580, 355)


EXTRA = 124                      # the facade canvas rises this far above the room's top edge (tower tops, for the battle)
FAR = (82, 150, 12)              # the distant office tower (x0, x1, top): small with distance, red beacon
T1 = (176, 252, -100)            # left stair tower (x0, x1 incl. side face, top) rising out of frame
T2 = (566, 698, -90)             # the main tower over the dock
T3 = (416, 484, -64)             # a tower further back, behind the shed roof
ANNEX_EAVE = 60                  # front-sloping tile roof over the left annex: eave row
UPPER_RAKE = ((298, 28), (566, 2))   # the dock block's shed roof (wall top, low end to high end)
CANOPY = (380, 700, 46, 12)      # concrete canopy over the dock (x0, x1, fascia top, fascia height)
WING_RAKE = ((716, 18), (906, 44))   # the right wing's shed roof falls toward the creek
WING_BAND = 84                   # the wing's concrete floor band (sandstone above, concrete below)
SIGN = "ENGINEERING CENTER"


def far_tower(fc, o):
    """The distant office tower (ECOT) over the annex: concrete at a smaller scale, slit windows,
    a shed cap and the aviation beacon. Returns the beacon point in room coordinates."""
    x0, x1, top = FAR
    side = 8
    rng = np.random.default_rng(31)
    fc.rect(x0 - 1, o + top - 1, x1 - x0 + 2, 80, X.BOARD[0])
    for yy in range(o + top, o + 80):
        k = (yy - o - top) % 3
        fc.hline(x0, yy, x1 - x0 - side, X.BOARD[4] if k == 0 else X.BOARD[3])
        fc.hline(x1 - side, yy, side, X.BOARD[2] if k == 0 else X.BOARD[1])
    fc.vline(x0, o + top, 80, X.BOARD[5])
    for row, yy in enumerate(range(o + top + 8, o + 70, 9)):
        for col, xx in enumerate(range(x0 + 6, x1 - side - 3, 6)):
            lit = rng.random() < 0.16
            fc.rect(xx, yy, 2, 6, E.WARM[2] if lit else "#1a1c2e")
            if lit:
                fc.px(xx, yy, E.WARM[3])
        fc.hline(x0 + 1, yy + 7, x1 - x0 - side - 2, X.BOARD[5])
    # shed cap sloping down to the left, a rooftop plant box, the beacon mast
    for x in range(x0 - 2, x1 + 2):
        yl = o + top - int((x - x0 + 2) * 6 / (x1 - x0 + 4))
        fc.vline(x, yl - 3, 3, X.CLAY[4] if x % 3 else X.CLAY[2]); fc.px(x, yl - 3, X.CLAY[6])
        fc.vline(x, yl, o + top - yl + 1, X.BOARD[5])
    fc.rect(x1 - 26, o + top - 14, 14, 6, X.BOARD[2]); fc.hline(x1 - 26, o + top - 14, 14, X.BOARD[4])
    fc.rect(x1 - 18, o + top - 22, 2, 9, X.BOARD[1])
    return (x1 - 17, top - 23)


def tower(fc, o, x0, x1, top, base, seed, side=10, rake=None, cols=(), rows=(), lit=0.2, win=(10, 26),
          slot=None, tone=6):
    """A board-formed concrete tower (a grain-silo block): lit front face, darker side face, a shed
    roof cap (rake = drop in px from one side; > 0 falls to the left, < 0 to the right), deep-set
    narrow windows in rows, or a full-height stair slot."""
    rng = np.random.default_rng(seed)
    fx1 = x1 - side
    dl, dr = (rake, 0) if (rake or 0) > 0 else (0, -(rake or 0))
    poly = [(x0, o + top + dl), (x1, o + top + dr), (x1, o + base), (x0, o + base)]

    def walls(tmp):
        X.board_concrete(tmp, x0, o + top, fx1 - x0, base - top, seed=seed, base=tone, ox=x0, oy=top)
        X.board_concrete(tmp, fx1, o + top, side, base - top, seed=seed + 1, base=tone, side=-3, ox=x0, oy=top)
        tmp.vline(x0, o + top, base - top, X.BOARD[tone + 2]); tmp.vline(fx1, o + top, base - top, X.BOARD[tone - 3])
        X.drips(tmp, x0, o + top + max(dl, dr) + 3, fx1 - x0, 22, seed=seed + 7, density=0.3)
    X.paint_masked(fc, poly, walls)
    if rake:
        X.shed_rake(fc, x0 - 2, o + top + dl, x1 + 2, o + top + dr, thick=8, seed=seed)
    else:
        X.ledge(fc, x0 - 2, o + top - 3, x1 - x0 + 4, 4, seed=seed)
    w, h = win
    for ry in rows:
        for cx in cols:
            X.deep_window(fc, cx, o + ry, w, h, lit=rng.random() < lit, seed=int(rng.integers(1e6)),
                          blind=0.35 if rng.random() < 0.4 else 0.0, figure=rng.random() < 0.3)
    if slot:
        sx, sw, sy0, sy1 = slot
        X.stair_slot(fc, sx, o + sy0, sw, sy1 - sy0, lit=True, floor_h=34)


def paint_facade(extra=EXTRA):
    """The back of the Engineering Center on a transparent canvas whose ground row is BASE + extra
    (sky left clear). Returns the canvas and key points in room coordinates."""
    o = extra
    fc = Canvas(W, BASE + o)
    pts = {}
    # --- far: trees and the distant office tower ---------------------------------------------
    E.tree_mass(fc, -10, 330, o + 62, o + 34, seed=2)
    pts["beacon"] = far_tower(fc, o)
    E.tree_mass(fc, 690, 970, o + 46, o + 26, seed=5)
    # --- the tower set back behind the dock block's roof --------------------------------------
    tower(fc, o, T3[0], T3[1], T3[2], 60, seed=33, side=8, rake=-8, tone=5, cols=(430, 456), rows=(-40, 0),
          lit=0.3, win=(8, 22))
    paint_upper(fc, o)
    # --- the main tower over the dock: three floors of deep-set windows ----------------------
    tower(fc, o, T2[0], T2[1], T2[2], 60, seed=41, side=12, rake=14, cols=(580, 606, 632, 658),
          rows=(-70, -26, 16), lit=0.3)
    # --- the left stair tower with its full-height slot -----------------------------------------
    tower(fc, o, T1[0], T1[1], T1[2], BASE, seed=17, side=10, rake=-12, slot=(203, 12, -96, 100))
    fc.rect(186, o + 70, 14, 8, OUT); fc.rect(187, o + 71, 12, 6, "#e6d6b1"); fc.rect(187, o + 71, 12, 2, "#c84a3c")
    paint_annex(fc, o)
    pts.update(paint_dock(fc, o))
    pts["fan"] = paint_wing(fc, o)
    return fc, pts


def paint_annex(fc, o):
    """Left: the low annex in Lyons sandstone under a front-sloping red tile shed roof, deep windows
    in concrete frames, a concrete plinth; the link to the dock block; bins, a dumpster, an oak."""
    x1 = T1[0]
    X.tile_band(fc, -2, o + ANNEX_EAVE - 13, x1 + 2, 13, seed=4)
    X.lyons_wall(fc, 0, o + ANNEX_EAVE + 3, x1, BASE - ANNEX_EAVE - 15, seed=7)
    X.board_concrete(fc, 0, o + BASE - 12, x1, 12, seed=8, base=6, ox=0, oy=BASE - 12)
    X.ledge(fc, 0, o + BASE - 13, x1, 2, seed=9, drip=0)
    for i, (wx, lit, blind) in enumerate([(26, True, 0.35), (82, False, 0.0), (138, True, 0.0)]):
        X.deep_window(fc, wx, o + 80, 12, 30, lit=lit, blind=blind, seed=i, figure=(i == 2))
    E.wall_pack(fc, 112, o + 66)
    # the link between the stair tower and the dock block: sandstone under a concrete coping
    lx0, lx1 = T1[1], MAIN[0]
    X.lyons_wall(fc, lx0, o + 70, lx1 - lx0, BASE - 70 - 12, seed=12)
    X.board_concrete(fc, lx0, o + BASE - 12, lx1 - lx0, 12, seed=8, base=6, ox=0, oy=BASE - 12)
    X.ledge(fc, lx0, o + 66, lx1 - lx0, 4, seed=13)
    fc.rect(264, o + 66, 4, BASE - 66, OUT); fc.vline(265, o + 66, BASE - 66, E.STEEL[4])
    for yy in range(66 + 10, BASE, 18):
        fc.rect(263, o + yy, 6, 2, E.STEEL[2])
    fc.rect(260, o + BASE - 4, 10, 4, E.STEEL[2])
    # an oak at the corner of the annex (trunk at the wall foot, behind everyone)
    from props import atlas_tree
    tree, tax, tay = atlas_tree(128, cell=5, seed=2)
    fc.paste(tree, 36 - tax, o + BASE - 2 - tay)
    # recycling bins and the dumpster against the stair tower, a hydrant at the corner
    E.wheelie_bin(fc, 176, o + BASE - 28)
    E.wheelie_bin(fc, 194, o + BASE - 28, colour="#3a6a3a", hi="#5a8a5a")
    E.dumpster(fc, 214, o + BASE - 32, w=54, h=32)
    E.fire_hydrant(fc, 286, o + BASE)


def paint_upper(fc, o):
    """The dock block's upper floor: Lyons sandstone between concrete fins, deep narrow windows,
    under a red tile shed roof rising from the stair-tower side to the main tower."""
    (ax, ay), (bx, by) = UPPER_RAKE
    poly = [(ax, o + ay), (bx, o + by), (bx, o + CANOPY[2] + 2), (ax, o + CANOPY[2] + 2)]

    def wall(tmp):
        X.lyons_wall(tmp, ax, o + by, bx - ax, CANOPY[2] + 2 - by, seed=21)
        for fx in (ax, 372, 452, 532):
            X.board_concrete(tmp, fx, o + by, 9, CANOPY[2] + 2 - by, seed=fx, base=7, ox=0, oy=0)
            tmp.vline(fx, o + by, CANOPY[2] + 2 - by, X.BOARD[9]); tmp.vline(fx + 8, o + by, CANOPY[2] + 2 - by, X.BOARD[4])
    X.paint_masked(fc, poly, wall)
    X.shed_rake(fc, ax - 2, o + ay, bx, o + by, thick=9, seed=22)
    for i, wx in enumerate((392, 416, 474, 498, 548)):
        top = ay + (by - ay) * (wx - ax) / (bx - ax)
        wy = max(int(top) + 8, 22)
        X.deep_window(fc, wx, o + wy, 8, 40 - wy, lit=i in (1, 3), seed=60 + i, frame=2, sill=False)
    X.ledge(fc, ax, o + CANOPY[2], CANOPY[0] - ax, 4, seed=23)


def paint_dock(fc, o):
    """The dock block's ground floor: board-formed concrete piers and lintel, a Lyons sandstone
    panel behind the cylinder cage and rack, the concrete canopy with the building's name, the
    workshop's open roll-up door and DOCK 2."""
    x0, x1 = MAIN
    gtop = CANOPY[2] + 4
    X.board_concrete(fc, x0, o + gtop, x1 - x0, BASE - gtop, seed=51, base=6, ox=0, oy=0)
    # sandstone panel set back in a concrete frame
    px0, px1, py0, py1 = 314, 458, 66, BASE - 10
    X.lyons_wall(fc, px0, o + py0, px1 - px0, py1 - py0, seed=52)
    fc.rect(px0, o + py0, px1 - px0, 2, C("#0e0c16", 0.55)); fc.rect(px0, o + py0, 2, py1 - py0, C("#0e0c16", 0.4))
    X.ledge(fc, px0 - 2, o + py1, px1 - px0 + 4, 3, seed=53, drip=0)
    # corner piers stand proud: lit edge, shadow side
    for qx in (x0, x1 - 10):
        fc.vline(qx, o + gtop, BASE - gtop, X.BOARD[9]); fc.vline(qx + 9, o + gtop, BASE - gtop, X.BOARD[3])
    # the canopy: a cantilevered concrete slab with the building's name on its fascia
    cx0, cx1, cy, ch = CANOPY
    X.board_concrete(fc, cx0, o + cy, cx1 - cx0, ch, seed=54, base=7, ox=0, oy=0, ties=False)
    fc.hline(cx0, o + cy, cx1 - cx0, X.BOARD[9]); fc.hline(cx0, o + cy + ch - 1, cx1 - cx0, X.BOARD[4])
    fc.vline(cx0, o + cy, ch, X.BOARD[9]); fc.vline(cx1 - 1, o + cy, ch, X.BOARD[4])
    fc.rect(cx0, o + cy + ch, cx1 - cx0, 4, C(SHADOW, 0.5))
    X.drips(fc, cx0, o + cy + ch + 4, cx1 - cx0, 16, seed=55, density=0.25, alpha=0.26)
    sx = OPEN_DOOR[0] + OPEN_DOOR[1] // 2 - text_width(SIGN) // 2 + 4
    X.letters(fc, SIGN, sx, o + cy + 2, "#3a2820", shadow="#5a5052")
    # roll-up doors
    ox, ow, ot, oh = OPEN_DOOR
    inside = E.rollup_door_open(fc, ox, o + ot, ow, oh, seed=2)
    inside = {"screen": (inside["screen"][0], inside["screen"][1] - o, inside["screen"][2], inside["screen"][3]),
              "floor": inside["floor"] - o}
    label = "WORKSHOP"
    lx = ox + ow // 2 - text_width(label) // 2
    fc.rect(lx - 3, o + ot - 10, text_width(label) + 6, 9, E.STEEL[1])
    text(fc, label, lx, o + ot - 10, SAFETY[3])
    dx, dw, dt = DOCK2
    E.rollup_door_closed(fc, dx, o + dt, dw, BASE - dt, label="DOCK 2", seed=4)
    E.pallet_stack(fc, 670, o + BASE, w=34, n=3)
    E.pallet_stack(fc, 672, o + BASE - 18, w=30, n=1)
    E.traffic_cone(fc, 710, o + BASE)
    l1 = E.gooseneck_dock_light(fc, ox - 8, o + 74, arm=10)
    l2 = E.gooseneck_dock_light(fc, ox + ow + 8, o + 74, arm=10, flip=True)
    # gas cylinders, a sprinkler riser with its red bell, a materials rack
    E.cylinder_cage(fc, 318, o + 104, 44, 38, seed=1)
    fc.rect(372, o + 70, 5, BASE - 70, OUT); fc.vline(373, o + 70, BASE - 70, "#c84a3c"); fc.vline(374, o + 70, BASE - 70, "#8a2e2e")
    fc.rect(369, o + 96, 11, 6, "#8a2e2e"); fc.ellipse(368, o + 76, 12, 12, OUT); fc.ellipse(369, o + 77, 10, 10, "#c84a3c"); fc.px(372, o + 79, "#f08a7a")
    E.materials_rack(fc, 392, o + 82, 62, 60, seed=3)
    # electrical panel and conduit between the doors
    fc.rect(560, o + 84, 22, 30, OUT); fc.rect(561, o + 85, 20, 28, "#6a6e7a"); fc.hline(561, o + 85, 20, "#8e94a2")
    fc.rect(563, o + 88, 16, 4, "#e6d6b1"); fc.rect(565, o + 89, 3, 2, "#c84a3c"); fc.rect(569, o + 96, 9, 2, OUT)
    fc.rect(568, o + 62, 3, 22, E.STEEL[3]); fc.vline(568, o + 62, 22, E.STEEL[5])
    # dock-edge bollards either side of the open door
    for bx in (ox - 14, ox + ow + 8):
        fc.rect(bx, o + BASE - 26, 7, 26, OUT); fc.rect(bx + 1, o + BASE - 25, 5, 25, SAFETY[2])
        fc.vline(bx + 1, o + BASE - 25, 25, SAFETY[3])
        for yy in range(BASE - 22, BASE - 2, 8):
            fc.rect(bx + 1, o + yy, 5, 3, "#1a1820")
    E.wall_pack(fc, 690, o + 74)
    return {"inside": inside, "dock_lights": ((l1[0], l1[1] - o), (l2[0], l2[1] - o))}


def paint_wing(fc, o):
    """Right: the wing toward the creek, Lyons sandstone over a board-formed concrete ground floor,
    deep windows, a red tile shed roof falling toward the water, a condenser on its pad."""
    x0, x1 = WING[0], WING[1]
    (ax, ay), (bx, by) = WING_RAKE
    poly = [(ax, o + ay), (bx, o + by), (bx, o + WING_BAND + 2), (ax, o + WING_BAND + 2)]
    X.paint_masked(fc, poly, lambda t: X.lyons_wall(t, ax, o + ay, bx - ax, WING_BAND + 2 - ay, seed=71))
    X.shed_rake(fc, ax - 2, o + ay, bx, o + by, thick=9, seed=72)
    X.board_concrete(fc, x0, o + WING_BAND, x1 - x0, BASE - WING_BAND, seed=73, base=6, ox=0, oy=0)
    X.ledge(fc, x0, o + WING_BAND, x1 - x0, 4, seed=74)
    # a full-height concrete pier where the wing meets the dock block
    X.board_concrete(fc, x0, o + 10, 10, BASE - 10, seed=75, base=7, ox=0, oy=0)
    fc.vline(x0, o + 10, BASE - 10, X.BOARD[9]); fc.vline(x0 + 9, o + 10, BASE - 10, X.BOARD[4])
    X.ledge(fc, x0 - 1, o + 8, 12, 3, seed=76, drip=0)
    for i, wx in enumerate((744, 778, 812, 846, 878)):
        top = ay + (by - ay) * (wx - ax) / (bx - ax)
        wy = int(top) + 10
        X.deep_window(fc, wx, o + wy, 10, WING_BAND - 8 - wy, lit=i in (1, 3), seed=80 + i,
                      blind=0.4 if i == 1 else 0.0, figure=i == 3)
    for i, wx in enumerate((744, 842, 876)):
        X.deep_window(fc, wx, o + 98, 10, 26, lit=(i == 2), seed=90 + i)
    # condenser on a pad: grille, the fan (animated as a layer), a refrigerant line
    cx, cy = 770, BASE - 30
    fc.rect(cx - 2, o + BASE - 4, 52, 4, X.BOARD[6]); fc.hline(cx - 2, o + BASE - 4, 52, X.BOARD[8])
    fc.rect(cx, o + cy, 48, 26, OUT); fc.rect(cx + 1, o + cy + 1, 46, 24, "#8e94a2"); fc.hline(cx + 1, o + cy + 1, 46, "#b4b8c4")
    for gy in range(cy + 4, cy + 24, 2):
        fc.hline(cx + 3, o + gy, 18, "#5e6476")
    fc.ellipse(cx + 24, o + cy + 3, 21, 21, OUT); fc.ellipse(cx + 25, o + cy + 4, 19, 19, "#2a2c38")
    fc.line(cx + 46, o + cy + 6, cx + 54, o + cy - 12, E.STEEL[1]); fc.line(cx + 47, o + cy + 6, cx + 55, o + cy - 12, "#3a3a48")
    E.wall_pack(fc, 828, o + 88)
    return (cx + 25, cy + 4)


def paint_court(bg):
    """Apron, asphalt, the sandstone walk with its curbs, the creek bank on the right."""
    xs, ys = E.grid(W, H - BASE)
    rgb = E.asphalt_np(W, H - BASE, seed=3)
    E.put_rgb(bg, 0, BASE, rgb)
    ax0, ax1, ay1 = APRON
    E.put_rgb(bg, ax0, BASE, E.conc_slabs_np(ax1 - ax0, ay1 - BASE, slab=42, row=22, seed=5))
    bg.hline(ax0, ay1, ax1 - ax0, E.CONC[2]); bg.hline(ax0, ay1 + 1, ax1 - ax0, C(SHADOW, 0.3))
    # a strip of concrete along the annex and wing too (narrow sidewalk at the wall foot)
    for (sx0, sx1) in [(0, ax0), (ax1, BANK_X)]:
        E.put_rgb(bg, sx0, BASE, E.conc_slabs_np(sx1 - sx0, 16, slab=30, row=16, seed=sx0 + 1))
        bg.hline(sx0, BASE + 16, sx1 - sx0, E.CONC[2])
    bg.rect(0, BASE, W, 2, C(SHADOW, 0.55))
    # tar snakes and patch repairs on the asphalt
    rng = np.random.default_rng(8)
    for (x, y, L, v) in [(60, 260, 140, False), (240, 330, 90, True), (420, 400, 150, False), (700, 250, 120, False),
                         (640, 300, 70, True), (150, 410, 110, False), (800, 330, 80, True), (330, 250, 60, False)]:
        E.tar_snake(bg, x, y, L, seed=x + y, vertical=v)
    # oil stains under where trucks park, tyre arcs
    for (x, y, rx, ry) in [(498, 262, 12, 4), (530, 286, 7, 3), (620, 240, 10, 3), (400, 300, 6, 2)]:
        E.soft_ellipse(bg, x, y, rx, ry, "#141218", 0.45)
    for k in range(3):
        for a in np.linspace(0.2, 1.2, 60):
            bg.px(int(380 + k * 9 + np.cos(a) * 120), int(400 - np.sin(a) * 90), C("#1a1820", 0.35))
    return rng


def paint_markings(bg):
    """Loading-bay paint: yellow bay lines from the dock, LOADING ZONE, a hatched KEEP CLEAR box
    in front of DOCK 2, a manhole and a storm drain."""
    ox, ow, ot, oh = OPEN_DOOR
    for x in (ox - 20, ox + ow + 18):
        E.worn_line(bg, x, 232, 3, 96, SAFETY[2], alpha=0.75, seed=x)
    E.worn_line(bg, ox - 20, 326, ow + 41, 3, SAFETY[2], alpha=0.7, seed=4)
    E.big_stencil(bg, "LOADING", ox + ow // 2 - 41, 262, SAFETY[2], alpha=0.5)
    E.big_stencil(bg, "ZONE", ox + ow // 2 - 23, 286, SAFETY[2], alpha=0.5)
    # KEEP CLEAR hatch in front of DOCK 2 on the apron
    dx, dw, dt = DOCK2
    hx0, hy0, hw, hh = dx - 6, BASE + 18, dw + 12, 50
    for yy in range(hh):
        for xx in range(hw):
            if (xx + yy) % 10 < 3:
                bg.px(hx0 + xx, hy0 + yy, C(SAFETY[2], 0.55))
    bg.rect(hx0, hy0, hw, 2, C(SAFETY[2], 0.75)); bg.rect(hx0, hy0 + hh - 2, hw, 2, C(SAFETY[2], 0.75))
    bg.rect(hx0, hy0, 2, hh, C(SAFETY[2], 0.75)); bg.rect(hx0 + hw - 2, hy0, 2, hh, C(SAFETY[2], 0.75))
    s = "KEEP CLEAR"
    bg.rect(hx0 + hw // 2 - text_width(s) // 2 - 2, hy0 + hh // 2 - 5, text_width(s) + 4, 11, E.CONC[4])
    text(bg, s, hx0 + hw // 2 - text_width(s) // 2, hy0 + hh // 2 - 5, C(SAFETY[3], 0.85))
    # the apron's foot line under the open door (tyre-worn) and a drain channel along the apron
    bg.rect(APRON[0] + 4, APRON[2] - 6, APRON[1] - APRON[0] - 8, 4, "#1c1a20")
    for gx in range(APRON[0] + 6, APRON[1] - 6, 3):
        bg.vline(gx, APRON[2] - 5, 2, E.STEEL[4])
    # manhole and a storm drain
    bg.ellipse(404, 312, 26, 12, OUT); bg.ellipse(405, 313, 24, 10, E.STEEL[2])
    for k in range(3):
        bg.hline(408, 316 + k * 2, 18, E.STEEL[4])
    bg.rect(176, 420, 22, 10, OUT)
    for gx in range(178, 196, 3):
        bg.vline(gx, 421, 8, E.STEEL[4])
    # service-vehicle stalls along the annex: white lines, wheel stops, SERVICE stencils
    for k, x in enumerate(range(26, 290, 66)):
        E.worn_line(bg, x, BASE + 22, 2, 62, "#d8d4cc", alpha=0.6, seed=30 + k)
        if x + 66 < 300:
            bg.rect(x + 14, BASE + 22, 38, 4, OUT); bg.rect(x + 15, BASE + 22, 36, 2, E.CONC[6]); bg.hline(x + 15, BASE + 22, 36, E.CONC[8])
            text(bg, "SERVICE", x + 12, BASE + 66, C("#d8d4cc", 0.45))
    E.worn_line(bg, 26, BASE + 84, 266, 2, "#d8d4cc", alpha=0.45, seed=37)
    # chalk on the asphalt by the notice: a truss bridge on two supports, a load arrow, "ASK?"
    ch = C("#d8d8d0", 0.55)
    cx0, cy0 = 238, 360
    bg.line(cx0, cy0, cx0 + 70, cy0, ch); bg.line(cx0, cy0 + 1, cx0 + 70, cy0 + 1, C("#d8d8d0", 0.3))
    for k in range(0, 70, 14):
        bg.line(cx0 + k, cy0, cx0 + k + 7, cy0 - 10, ch); bg.line(cx0 + k + 7, cy0 - 10, cx0 + k + 14, cy0, ch)
    bg.line(cx0 + 7, cy0 - 10, cx0 + 63, cy0 - 10, ch)
    for sx_ in (cx0 + 2, cx0 + 66):
        bg.poly([(sx_ - 4, cy0 + 9), (sx_, cy0 + 2), (sx_ + 4, cy0 + 9)], C("#d8d8d0", 0.45))
    bg.line(cx0 + 35, cy0 - 26, cx0 + 35, cy0 - 13, ch); bg.line(cx0 + 32, cy0 - 16, cx0 + 35, cy0 - 13, ch); bg.line(cx0 + 38, cy0 - 16, cx0 + 35, cy0 - 13, ch)
    text(bg, "ASK?", cx0 + 40, cy0 - 30, C("#d8d8d0", 0.5))
    # rain left in the low spots: the door light and the lamp reflected
    from lib_farrand import puddle
    sky = ("#232149", "#2e2853", "#4c3762")
    puddle(bg, 560, 214, 26, 6, seed=3, reflect=("#f6cf7a", "#fff0c4"), sky=sky)
    puddle(bg, 152, 392, 22, 5, seed=4, reflect=("#f6cf7a",), sky=sky)
    puddle(bg, 700, 330, 16, 4, seed=5, reflect=("#c8c0e0",), sky=sky)


def path_mask(w, h, pts, half):
    xs, ys = np.mgrid[0:h, 0:w]
    d = np.full((h, w), 1e9, np.float32)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        vx, vy = x1 - x0, y1 - y0
        t = np.clip(((ys - x0) * vx + (xs - y0) * vy) / float(vx * vx + vy * vy), 0, 1)
        px_ = x0 + t * vx
        py_ = y0 + t * vy
        d = np.minimum(d, np.hypot(ys - px_, xs - py_))
    return d


def paint_walk(bg):
    """The sandstone walk with granite curbs and a grass verge with shrubs below it."""
    d = path_mask(W, H, PATH, PATH_HALF)
    stone = E.flagstone_np(W, H, seed=9)
    grass = E.grass_np(W, H, seed=4)
    # grass below the walk (south of the centreline) down to the bottom edge
    cy = np.interp(np.arange(W), [p[0] for p in PATH], [p[1] for p in PATH])
    ys = np.arange(H)[:, None]
    south = (ys > cy[None, :] + PATH_HALF + 3)
    south &= (np.arange(W)[None, :] < BANK_X + 4)
    E.put_rgb(bg, 0, 0, grass, mask=south)
    on = d <= PATH_HALF
    E.put_rgb(bg, 0, 0, stone, mask=on)
    curb = (d > PATH_HALF) & (d <= PATH_HALF + 2)
    curb_rgb = np.zeros((H, W, 3), np.float32)
    curb_rgb[:] = E.H("#8a8690")
    lip = (d > PATH_HALF + 1) & (d <= PATH_HALF + 2)
    curb_rgb[lip] = E.H("#4a4650")
    E.put_rgb(bg, 0, 0, curb_rgb, mask=curb)
    # shrubs and tufts along the bottom verge
    rng = np.random.default_rng(14)
    x = 150
    while x < BANK_X - 30:
        if abs(x - 520) < 90:     # leave the workbench's foot clear of bushes
            x += 40
            continue
        yb = int(np.interp(x, [p[0] for p in PATH], [p[1] for p in PATH])) + PATH_HALF + 30
        yb = max(yb, 506)
        sw = int(rng.integers(26, 40))
        bush = shrub(0, 0, sw, int(sw * 0.55), seed=int(rng.integers(1e6)), palette=LEAF,
                     flowers=MUM if rng.random() < 0.25 else None)
        bg.paste(bush, x, min(yb, H - 2) - int(sw * 0.55) + 6)
        x += sw + int(rng.integers(30, 70))
    for _ in range(60):
        tx = int(rng.integers(0, BANK_X - 10))
        ty = int(np.interp(tx, [p[0] for p in PATH], [p[1] for p in PATH])) + PATH_HALF + int(rng.integers(6, 40))
        if ty < H - 4:
            grass_tuft(bg, tx, ty, int(rng.integers(3, 6)), seed=int(rng.integers(1e6)), palette=LEAF)


def paint_bank_and_bridge(bg):
    """The creek on the right: a stone-edged bank, grass running down to the water, reeds and
    rocks, moonlight on the ripples; the footbridge (repaired state) on its stone abutment."""
    x0, wx = BANK_X, WATER_X
    E.put_rgb(bg, x0, BASE, E.grass_np(W - x0, H - BASE, seed=7))
    # sandstone edging along the top of the bank
    for yy in range(BASE, H, 6):
        tone = E.STONE_E[4] if (yy // 6) % 2 else E.STONE_E[3]
        bg.rect(x0, yy, 4, 5, tone); bg.hline(x0, yy, 4, E.STONE_E[5]); bg.hline(x0, yy + 5, 4, E.STONE_E[1])
    bg.vline(x0 + 4, BASE, H - BASE, C(SHADOW, 0.4))
    # water: dark bands with moonlit ripple dashes
    wp = E.P(E.WATER)
    xs, ys = E.grid(W - wx, H - BASE)
    f = E.soft_field(W - wx, H - BASE, 10, 3)
    water = wp[np.where(f < 0.45, 1, 2)].copy()
    rip = (E.hashn(xs // 5, ys // 3, 4) > 0.86) & ((ys % 3) == 0)
    water[rip] = wp[3]
    water[(E.hashn(xs // 3, ys // 5, 5) > 0.97) & ((ys % 5) == 1)] = wp[4]
    E.put_rgb(bg, wx, BASE, water)
    frng = np.random.default_rng(9)
    for _ in range(60):                # current lines running downstream
        fx_ = wx + 4 + int(frng.integers(0, W - wx - 8))
        fy_ = BASE + int(frng.integers(0, H - BASE - 10))
        bg.vline(fx_, fy_, int(frng.integers(3, 9)), C(E.WATER[3], 0.8))
    for yy in range(BASE, H):          # muddy waterline
        bg.px(wx, yy, "#2e2a26"); bg.px(wx - 1, yy, "#3a3428")
    rng = np.random.default_rng(5)
    bx, y0, y1 = BRIDGE
    for _ in range(30):                # rocks at the waterline
        ry = int(rng.integers(BASE + 4, H - 4))
        if y0 - 16 < ry < y1 + 10:
            continue
        rx = wx - 4 + int(rng.integers(0, 8))
        bg.ellipse(rx, ry, 7, 4, "#3e3a46"); bg.hline(rx + 1, ry, 4, "#6a6470"); bg.hline(rx, ry + 3, 7, C(SHADOW, 0.5))
    for _ in range(40):                # reeds and cattails
        ry = int(rng.integers(BASE + 6, H - 4))
        if y0 - 18 < ry < y1 + 12:
            continue
        rx = wx - 9 + int(rng.integers(0, 8))
        for k in range(3):
            top = ry - int(rng.integers(6, 12))
            bg.line(rx + k * 2, ry, rx + k * 2 + int(rng.integers(-1, 2)), top, "#4e6040" if k % 2 else "#62744a")
        if rng.random() < 0.3:
            bg.rect(rx + 2, ry - 11, 2, 4, "#6a4a2e")
    # stone abutment where the walk meets the deck
    bg.rect(bx - 4, y0 - 4, 24, y1 - y0 + 12, OUT)
    for yy in range(y0 - 3, y1 + 7, 5):
        bg.rect(bx - 3, yy, 22, 4, E.STONE_E[3 + (yy // 5) % 2]); bg.hline(bx - 3, yy, 22, E.STONE_E[5])
    # deck shadow on the water, stringers, planks
    bg.rect(wx, y1 + 2, W - wx, 6, C("#06080e", 0.6))
    for x in range(bx, W, 4):
        tone = E.PLY[3] if (x // 4) % 3 else E.PLY[4]
        bg.rect(x, y0, 3, y1 - y0, tone)
        bg.hline(x, y0, 3, E.PLY[5]); bg.vline(x + 3, y0, y1 - y0, E.PLY[1])
        if (x // 4) % 5 == 2:
            bg.px(x + 1, (y0 + y1) // 2, E.PLY[1]); bg.px(x + 1, y0 + 3, E.PLY[2])
    bg.rect(bx, y0 - 2, W - bx, 2, E.STEEL[3]); bg.hline(bx, y0 - 2, W - bx, E.STEEL[5])
    bg.rect(bx, y1, W - bx, 3, E.STEEL[2]); bg.hline(bx, y1, W - bx, E.STEEL[4])
    # the deck's south face (timber fascia on a steel stringer) and a pier standing in the water
    bg.rect(bx, y1 + 3, W - bx, 4, E.PLY[2]); bg.hline(bx, y1 + 3, W - bx, E.PLY[3]); bg.hline(bx, y1 + 6, W - bx, E.PLY[1])
    for x in range(bx + 6, W, 16):
        bg.px(x, y1 + 4, E.STEEL[5])
    bg.rect(944, y1 + 7, 8, 18, OUT); bg.rect(945, y1 + 7, 6, 17, E.CONC[4]); bg.vline(945, y1 + 7, 17, E.CONC[6])
    bg.hline(942, y1 + 24, 12, C("#8aa4c8", 0.5)); bg.hline(940, y1 + 26, 16, C("#8aa4c8", 0.25))
    # north handrail (background: everyone on the deck stands in front of it)
    for x in range(bx + 2, W, 12):
        bg.rect(x, y0 - 16, 3, 15, OUT); bg.vline(x + 1, y0 - 15, 13, E.STEEL[5])
    bg.rect(bx, y0 - 17, W - bx, 3, OUT); bg.hline(bx, y0 - 16, W - bx, E.STEEL[6])
    bg.rect(bx, y0 - 9, W - bx, 1, E.STEEL[3])
    # where the walk meets the deck: a steel threshold plate
    bg.rect(bx - 2, y0, 3, y1 - y0, E.STEEL[4]); bg.vline(bx - 2, y0, y1 - y0, E.STEEL[6])


def south_rail():
    """Occluder: the bridge's south handrail (stands in front of anyone on the deck)."""
    bx, y0, y1 = BRIDGE
    cv = Canvas(W - bx, 18)
    for x in range(4, W - bx, 14):
        cv.rect(x, 3, 2, 14, OUT); cv.vline(x, 3, 13, E.STEEL[5])
    cv.rect(0, 2, W - bx, 3, OUT); cv.hline(0, 3, W - bx, E.STEEL[6])
    cv.rect(0, 9, W - bx, 1, E.STEEL[3])
    return cv, bx, y1 + 2 - 18


def broken_bridge():
    """Overlay while bridge_ready is unset: missing planks over the water and a CLOSED barricade."""
    bx, y0, y1 = BRIDGE
    x0 = 904
    cv = Canvas(W - x0, y1 - y0 + 34)
    oy = 26                         # canvas row of the deck's north edge
    # gap: three planks gone, water and the bare stringers showing
    gx = 908 - x0
    cv.rect(gx, oy, 14, y1 - y0, "#141c32")
    cv.hline(gx, oy + 4, 14, "#2a3a5c"); cv.hline(gx + 3, oy + 12, 8, "#2a3a5c")
    cv.rect(gx, oy + 6, 14, 2, "#3a3440"); cv.rect(gx, oy + 15, 14, 2, "#3a3440")
    cv.rect(gx + 15, oy + 2, 3, y1 - y0 - 4, E.PLY[2])          # one plank loose, skewed
    # the barricade: two sawhorses with a striped board and a CLOSED sign
    sx = 918 - x0
    for lx in (sx + 2, sx + 30):
        cv.line(lx, oy + 18, lx + 2, oy + 2, OUT); cv.line(lx + 1, oy + 18, lx + 3, oy + 2, "#e6d6b1")
    cv.rect(sx - 2, oy - 4, 40, 7, OUT)
    for k in range(38):
        cv.vline(sx - 1 + k, oy - 3, 5, "#c84a3c" if (k // 4) % 2 == 0 else "#e6d6b1")
    cv.rect(sx + 1, oy - 18, 40, 13, OUT); cv.rect(sx + 2, oy - 17, 38, 11, "#e6d6b1")
    text(cv, "CLOSED", sx + 3, oy - 17, "#a83c32")
    cv.vline(sx + 8, oy - 6, 3, OUT); cv.vline(sx + 32, oy - 6, 3, OUT)
    # hazard tape tied from the rail post across the deck mouth
    for k in range(0, 34):
        y = oy - 10 + int(4 * np.sin(k / 34 * np.pi))
        cv.px(k, y, "#e8b45c" if (k // 3) % 2 else "#1a1820")
    return cv, x0, y0 - oy


def condenser_frames(n=3):
    """Three frames of the condenser fan turning (blades under the grille)."""
    out = []
    for k in range(n):
        cv = Canvas(19, 19)
        cv.ellipse(0, 0, 19, 19, "#2a2c38")
        for b in range(3):
            a = k * 2 * np.pi / (3 * n) + b * 2 * np.pi / 3
            for r in range(2, 9):
                cv.px(int(round(9 + np.cos(a) * r)), int(round(9 + np.sin(a) * r)), "#6a6e7a")
                cv.px(int(round(9 + np.cos(a + 0.25) * r)), int(round(9 + np.sin(a + 0.25) * r)), "#4e5260")
        cv.rect(8, 8, 3, 3, "#8e94a2")
        for gy in range(1, 18, 3):
            cv.hline(1, gy, 17, C("#14141c", 0.55))
        for gx in range(1, 18, 3):
            cv.vline(gx, 1, 17, C("#14141c", 0.35))
        out.append(cv)
    return out


def paint_lights(bg, inside):
    """Pools from the lamp, the dock lights, the open door's spill, the wall packs."""
    ox, ow, ot, oh = OPEN_DOOR
    for k, a in enumerate([0.07, 0.06, 0.05]):
        spread = 14 + k * 16
        bg.poly([(ox - k * 4, BASE), (ox + ow + k * 4, BASE), (ox + ow + spread, BASE + 46 + k * 22), (ox - spread, BASE + 46 + k * 22)], C(E.WARM[3], a))
    light_pool(bg, ox + ow // 2, BASE + 22, 70, 18, strength=0.2)
    light_pool(bg, LAMP[0], LAMP[1] + 2, 64, 18, strength=0.26)
    light_pool(bg, 112, BASE + 14, 40, 10, strength=0.16)
    light_pool(bg, 812, BASE + 12, 40, 10, strength=0.14)
    light_pool(bg, 540, 442, 70, 12, strength=0.14)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=1)

    stars = E.night_sky(bg, 0, 0, W, BASE, seed=11, stars=150, horizon=118)
    E.night_clouds(bg, [(10, 40, 90, 3), (300, 16, 60, 2), (640, 10, 70, 2), (860, 30, 60, 2)], seed=6)
    fc, pts = paint_facade()
    bg.paste(fc, 0, -EXTRA)
    beacon, inside, dock_lights, fan_at = pts["beacon"], pts["inside"], pts["dock_lights"], pts["fan"]
    paint_court(bg)
    paint_markings(bg)
    paint_walk(bg)
    paint_bank_and_bridge(bg)
    paint_lights(bg, inside)
    # dark margins outside the walkable court
    bg.rect(0, BASE, 14, H - BASE, C(SHADOW, 0.35))
    bg.rect(0, H - 16, W, 16, C(SHADOW, 0.4))
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(0, E.flatbed_cart(110, 50, seed=2))
    save(1, E.bike_rack(180, 30, seed=3))
    save(2, E.sawhorse_table(180, 40, seed=4))
    save(3, E.notice_stand(90, 48, "ASK FIRST"))
    save(4, E.court_lamp(68))
    save(5, E.concrete_planter(88, 44, seed=5))

    rail, rx, ry = south_rail()
    rail.save(os.path.join(out, "bridge-rail.png"))
    broken, bx, by = broken_bridge()
    broken.save(os.path.join(out, "bridge-closed.png"))
    fans = E_frames = condenser_frames()
    layers = []
    for k, fr in enumerate(fans):
        fr.save(os.path.join(out, f"fan-{k}.png"))
        layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(len(fans))), "rate": 9.0,
                       "texture": res + f"fan-{k}.png", "x": fan_at[0], "y": fan_at[1]})
    sx, sy, sw, sh = inside["screen"]
    fy = inside["floor"]
    layers += [
        # welding behind the screen inside the workshop: blue-white flashes, a glow on the floor
        {"kind": "blink", "pattern": "000010001100000000101000000110", "rate": 11.0,
         "rects": [[sx, sy, sw, sh, "c8e0ff", 0.38], [sx - 10, fy - 2, sw + 16, 4, "c8e0ff", 0.22],
                   [OPEN_DOOR[0] + 10, BASE + 2, OPEN_DOOR[1] - 20, 10, "a8c8ff", 0.07]]},
        {"kind": "particles", "style": "dust", "count": 7, "rect": [sx - 4, fy - 16, sw + 2, 16], "speed": [0, 14], "color": "ffc86a"},
        # the tower's aviation beacon
        {"kind": "blink", "pattern": "1100000000", "rate": 2.5,
         "rects": [[beacon[0] - 1, beacon[1] - 1, 3, 3, "ff4a3a"], [beacon[0] - 4, beacon[1] - 4, 9, 9, "ff4a3a", 0.25]]},
        {"kind": "twinkle", "points": [[x, y, c.lstrip("#"), 1] for (x, y, c) in stars], "rate": 1.4, "min": 0.1},
        {"kind": "twinkle", "points": [[LAMP[0], LAMP[1] - 59, "fff0c4", 2],
                                       [dock_lights[0][0], dock_lights[0][1], "fff0c4", 1],
                                       [dock_lights[1][0], dock_lights[1][1], "fff0c4", 1]], "rate": 1.2, "min": 0.65},
    ]

    manifest = {
        "background": res + "background.png",
        "width": W,
        "props": props,
        "label_only": [],
        "occluders": [{"texture": res + "bridge-rail.png", "x": rx, "y": ry, "base": BRIDGE[2] + 2}],
        "overlays": [{"texture": res + "bridge-closed.png", "x": bx, "y": by, "flag": "bridge_ready", "when": False}],
        "fauna": [
            {"kind": "eng_deer", "x": 926, "y": 300, "range": 0, "speed": 0.0, "rate": 0.35},
            {"kind": "rabbit", "x": 60, "y": 512, "range": 6, "speed": 0.3, "rate": 1.2},
            {"kind": "lamp_moth", "x": LAMP[0] + 2, "y": LAMP[1] - 64, "range": 7, "speed": 1.8, "rate": 9.0},
            {"kind": "night_bat", "x": 200, "y": 30, "fly": 14.0, "rate": 6.0},
        ],
        "leaves": [[0, 40, 90, 110]],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
