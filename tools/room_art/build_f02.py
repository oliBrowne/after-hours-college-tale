"""Farrand / volunteer tent (F02): the big striped crew marquee on a plywood apron, open at the
front. Inside: the long crew table with the urn and charging radios, the vest rack with three
hi-vis vests, chair stacks, water, and the wet canvas the volunteers keep folding. In front, the
check-in table and two hay-bale benches; the THREE NAMES sign-up board stands just inside.
When the volunteers are released (flag volunteers_released) the canvas flaps are tied back, a
SHIFT FINISHED board hangs from the valance, the vests are gone and three mugs dry on the table."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from props import OUT, IRON, WOOD, ground_shadow, shrub
import lib_farrand as F

ROOM = "F02"
W, H = 800, 480
WALK_TOP = 142
FAR_EDGE = 120
TENT = (400, 230)        # placement 0 floor point
TENT_W, EAVE_H, PEAK_H = 470, 84, 34
NOTICE = (590, 200)      # placement 5 floor point
APRON = (148, 228, 504, 116)   # plywood boards in front of the tent: x, y, w, h


# --- the tent -----------------------------------------------------------------------------------
def crew_interior(released):
    """Paints the inside of the marquee (back wall, crew table, vest rack, stacks, wet canvas)."""
    def paint(cv, x, y, w, h):
        rng = np.random.default_rng(5)
        floor_y = y + h - 14
        # ridge bulbs light the back wall: brighter band under them
        cv.rect(x, y, w, 10, C(F.BULB[2], 0.10))
        # plywood floor inside
        for yy in range(floor_y, y + h + 2):
            cv.hline(x, yy, w, F.PLY[2] if (yy - floor_y) % 5 else F.PLY[1])
        for sx in range(x + 30, x + w, 64):
            cv.vline(sx, floor_y, 16, F.PLY[1])
        # back windows: clear PVC showing the night outside
        for wx in range(x + 40, x + w - 30, 92):
            F.pvc_window(cv, wx, y + 10, 14, 26, lit=False)
        # long crew table along the back wall
        tx0, tx1, ty = x + 120, x + 300, floor_y - 18
        cv.rect(tx0, ty, tx1 - tx0, 4, OUT); cv.hline(tx0 + 1, ty + 1, tx1 - tx0 - 2, F.PLY[4])
        for lx in (tx0 + 4, tx1 - 7):
            cv.rect(lx, ty + 4, 3, 14, OUT)
        cv.rect(tx0 + 1, ty + 4, tx1 - tx0 - 2, 8, C("#120e18", 0.5))
        # urn, mugs, radios charging (green LEDs), first-aid box, a stack of flyers
        cv.rect(tx0 + 10, ty - 16, 12, 16, OUT); cv.rect(tx0 + 11, ty - 15, 10, 14, F.STEEL[4]); cv.vline(tx0 + 12, ty - 15, 14, F.STEEL[5])
        cv.rect(tx0 + 13, ty - 18, 6, 2, OUT); cv.rect(tx0 + 21, ty - 7, 3, 2, OUT)
        if not released:
            for k in range(3):
                cv.rect(tx0 + 28 + k * 7, ty - 5, 5, 5, OUT); cv.rect(tx0 + 29 + k * 7, ty - 4, 3, 3, ["#c84a3c", "#e6d6b1", "#425da6"][k])
        for k in range(4):
            rx = tx0 + 60 + k * 9
            cv.rect(rx, ty - 9, 6, 9, OUT); cv.rect(rx + 1, ty - 8, 4, 7, "#2a2832"); cv.vline(rx + 4, ty - 14, 5, OUT)
            cv.px(rx + 2, ty - 7, "#5cf08a" if (released or k != 1) else "#f05a4a")
        cv.rect(tx0 + 104, ty - 9, 14, 9, OUT); cv.rect(tx0 + 105, ty - 8, 12, 7, "#e6e2d8"); cv.rect(tx0 + 110, ty - 7, 2, 5, "#c84a3c"); cv.rect(tx0 + 108, ty - 5, 6, 1, "#c84a3c")
        cv.rect(tx0 + 128, ty - 4, 16, 4, "#e6d6b1"); cv.hline(tx0 + 129, ty - 3, 12, "#9a7c6e")
        cv.rect(tx0 + 150, ty - 6, 20, 6, F.TEAL_C[3]); cv.hline(tx0 + 150, ty - 6, 20, F.TEAL_C[4])
        # vest rack: a rail on two stands with three hi-vis vests (gone when released)
        vx = x + 34
        cv.rect(vx, floor_y - 44, 56, 2, OUT); cv.hline(vx, floor_y - 44, 56, F.STEEL[4])
        for sx in (vx, vx + 54):
            cv.rect(sx, floor_y - 44, 2, 44, OUT); cv.rect(sx - 3, floor_y - 1, 8, 2, OUT)
        if not released:
            for k in range(3):
                F.hivis_vest(cv, vx + 8 + k * 15, floor_y - 43, ["#d8e040", "#f0a030", "#d8e040"][k])
        else:
            for k in range(3):
                cv.vline(vx + 12 + k * 15, floor_y - 42, 4, F.STEEL[4]); cv.hline(vx + 9 + k * 15, floor_y - 38, 7, F.STEEL[3])
        # chair stacks, water crates, coolers
        F.chair_stack(cv, x + 318, floor_y + 2, n=7, w=14)
        F.chair_stack(cv, x + 338, floor_y + 2, n=5, w=14)
        for k in range(3):
            F.crate(cv, x + 362 + (k % 2) * 3, floor_y + 2 - k * 10, 18, 10, F.TEAL_C)
            for j in range(3):
                cv.rect(x + 365 + (k % 2) * 3 + j * 5, floor_y - 6 - k * 10, 3, 4, "#8ab4d8")
        F.cooler(cv, x + 388, floor_y + 2, 20, 12)
        F.water_jug(cv, x + 412, floor_y + 2); F.water_jug(cv, x + 422, floor_y + 2)
        # the wet canvas: a heap on the floor; once released, folded square on a pallet
        cx0 = x + 100
        if not released:
            cv.poly([(cx0, floor_y + 4), (cx0 + 8, floor_y - 8), (cx0 + 22, floor_y - 12), (cx0 + 34, floor_y - 6), (cx0 + 46, floor_y + 4)], OUT)
            cv.poly([(cx0 + 2, floor_y + 3), (cx0 + 9, floor_y - 7), (cx0 + 22, floor_y - 10), (cx0 + 33, floor_y - 5), (cx0 + 44, floor_y + 3)], F.CANVAS[2])
            cv.line(cx0 + 10, floor_y - 5, cx0 + 30, floor_y - 2, F.CANVAS[3]); cv.line(cx0 + 16, floor_y, cx0 + 38, floor_y + 1, F.CANVAS[1])
            cv.rect(cx0 + 14, floor_y - 4, 10, 2, F.RED[3])
            for k in range(5):  # drips on the boards
                cv.px(cx0 + 6 + k * 8, floor_y + 6, "#6a6a90")
        else:
            cv.rect(cx0 + 4, floor_y - 2, 36, 5, OUT); cv.rect(cx0 + 5, floor_y - 1, 34, 3, F.PLY[3])
            cv.rect(cx0 + 6, floor_y - 12, 32, 10, OUT); cv.rect(cx0 + 7, floor_y - 11, 30, 8, F.CANVAS[3])
            cv.hline(cx0 + 7, floor_y - 11, 30, F.CANVAS[5]); cv.hline(cx0 + 7, floor_y - 7, 30, F.CANVAS[2])
            cv.vline(cx0 + 22, floor_y - 12, 10, F.RED[3])
        # festoon under the ridge, inside the tent
        F.festoon(cv, x + 6, y + 4, x + w - 6, y + 4, sag=8, every=11, seed=7)
    return paint


def flap(cv, x, top, base, side, tied):
    """A side wall flap at a front corner: hanging loose and damp, or rolled and tied."""
    if tied:
        cv.rect(x - 3, top, 7, 8, OUT); cv.rect(x - 2, top + 1, 5, 6, F.CANVAS[4]); cv.hline(x - 2, top + 3, 5, F.CANVAS[2])
        cv.rect(x - 3, top + 3, 7, 2, F.RED[3])
        return
    w = 22
    x0 = x if side > 0 else x - w
    pts = [(x0, top), (x0 + w, top), (x0 + w - (4 if side > 0 else 0), base - 10), (x0 + (0 if side > 0 else 4), base - 4)]
    cv.poly([(p[0] + (1 if side > 0 else -1), p[1]) for p in pts], OUT)
    cv.poly(pts, F.CANVAS[3])
    for k in range(3, w, 6):
        cv.vline(x0 + k, top + 2, base - top - 14, F.CANVAS[2])
    cv.rect(x0, base - 18, w, 6, C("#5a5a7a", 0.35))   # damp hem


def volunteer_tent(released):
    tent, ax, ay = F.peaked_tent(TENT_W, EAVE_H, PEAK_H, open_front=True, seed=7, depth=28,
                                 interior=crew_interior(released), valance_text="VOLUNTEERS",
                                 poles=[0, TENT_W // 3, 2 * TENT_W // 3, TENT_W - 3], ridge=TENT_W - 150)
    eave = ay - EAVE_H
    ox = ax - TENT_W // 2
    # side flaps at the two front corners
    flap(tent, ox + 3, eave + 10, ay, 1, released)
    flap(tent, ox + TENT_W - 3, eave + 10, ay, -1, released)
    if released:
        # SHIFT FINISHED board hung from the valance on two cords
        label = "SHIFT FINISHED"
        bw = text_width(label) + 10
        bx = ax - bw // 2
        by = eave + 16
        tent.vline(bx + 6, eave + 9, by - eave - 9, F.WIRE); tent.vline(bx + bw - 7, eave + 9, by - eave - 9, F.WIRE)
        tent.rect(bx, by, bw, 13, OUT); tent.rect(bx + 1, by + 1, bw - 2, 11, "#e6d6b1"); tent.hline(bx + 1, by + 1, bw - 2, "#fff3d6")
        tent.hline(bx + 1, by + 11, bw - 2, "#b8a888")
        text(tent, label, bx + 5, by + 2, "#2c4a4c")
    return tent, ax, ay


def cut(tent, ax, ay, sprite, sax, say, at):
    """Clear the tent's pixels where a prop standing behind its front edge is opaque."""
    x0 = at[0] - sax - (TENT[0] - ax)
    y0 = at[1] - say - (TENT[1] - ay)
    m = sprite.a[..., 3] > 0
    hh, ww = m.shape
    sub = tent.a[max(0, y0):y0 + hh, max(0, x0):x0 + ww]
    mm = m[max(0, -y0):max(0, -y0) + sub.shape[0], max(0, -x0):max(0, -x0) + sub.shape[1]]
    sub[mm, 3] = 0


# --- props in front ------------------------------------------------------------------------------
def signup_board(released):
    """THREE NAMES: a whiteboard on an easel, three name lines, tally marks of calls; when the
    volunteers are released the names are ticked and HOME is written underneath."""
    width, height = 72, 42
    cv = Canvas(width + 6, height + 6, seed=3)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 - 8, 2)
    top = base - height
    for lx in (ox + 10, ox + width - 12):
        cv.line(lx, top + 28, lx - 4, base, OUT); cv.line(lx + 1, top + 28, lx - 3, base, F.STEEL[3])
    cv.line(ox + width // 2, top + 20, ox + width // 2 + 6, base, OUT)
    cv.rect(ox, top, width, 30, OUT)
    cv.rect(ox + 1, top + 1, width - 2, 28, F.STEEL[4]); cv.rect(ox + 2, top + 2, width - 4, 26, "#eef0ee")
    cv.rect(ox + 2, top + 2, width - 4, 9, "#2c4a4c")
    text(cv, "THREE NAMES", ox + width // 2 - text_width("THREE NAMES") // 2, top + 2, "#f6cd78")
    for k in range(3):
        ly = top + 14 + k * 5
        cv.hline(ox + 6, ly, 18 + (k * 7) % 9, "#3a4a7a")
        cv.px(ox + 6, ly - 1, "#3a4a7a"); cv.px(ox + 12, ly - 1, "#3a4a7a")
        if released:
            cv.line(ox + width - 14, ly, ox + width - 12, ly + 1, "#2a8a4c"); cv.line(ox + width - 12, ly + 1, ox + width - 8, ly - 3, "#2a8a4c")
        else:
            for t in range(6 + k * 3):  # tally marks: called again and again
                tx = ox + 30 + t * 3 + (t // 5)
                if t % 5 == 4:
                    cv.line(tx - 12, ly, tx, ly - 3, "#c8382c")
                else:
                    cv.vline(tx, ly - 3, 4, "#c8382c")
    cv.rect(ox + 2, top + 28, width - 4, 2, F.STEEL[3])
    cv.rect(ox + width - 14, top + 27, 8, 2, "#c8382c")  # marker on the tray
    return cv, ox + width // 2, base


def checkin_table(released):
    def items(cv, x0, top, width):
        if not released:
            # clipboard, walkie-talkie squawking, lanyard tangle, megaphone, cash box
            cv.rect(x0 + 14, top - 3, 14, 4, "#8c573b"); cv.rect(x0 + 15, top - 4, 12, 3, "#e6e2d8"); cv.rect(x0 + 19, top - 5, 4, 2, F.STEEL[4])
            cv.rect(x0 + 40, top - 9, 6, 9, OUT); cv.rect(x0 + 41, top - 8, 4, 7, "#2a2832"); cv.vline(x0 + 44, top - 15, 6, OUT); cv.px(x0 + 42, top - 7, "#f05a4a")
            for k in range(3):
                cv.line(x0 + 48 + k * 2, top - 12 - k * 2, x0 + 52 + k * 3, top - 15 - k * 2, "#f6cd78")
            for k in range(5):
                cv.line(x0 + 64 + k * 3, top - 1, x0 + 70 + k * 2, top - 4 + (k % 2), ["#e05a8a", "#425da6", "#f6cd78", "#5c897c", "#e05a8a"][k])
            cv.poly([(x0 + 92, top - 2), (x0 + 106, top - 8), (x0 + 106, top + 0), (x0 + 92, top)], "#e0b23a")
            cv.rect(x0 + 90, top - 3, 3, 3, OUT); cv.vline(x0 + 106, top - 8, 9, OUT)
            cv.rect(x0 + 118, top - 6, 18, 6, OUT); cv.rect(x0 + 119, top - 5, 16, 4, "#3e6a4a"); cv.hline(x0 + 119, top - 5, 16, "#5c897c")
        else:
            # tea towel with three mugs drying upside down, vests folded in a neat pile
            cv.rect(x0 + 34, top - 1, 48, 2, "#e6e2d8")
            for k in range(0, 48, 6):
                cv.px(x0 + 34 + k, top - 1, "#c84a3c")
            for k, c in enumerate(["#c84a3c", "#e6d6b1", "#425da6"]):
                mx = x0 + 40 + k * 14
                cv.rect(mx, top - 8, 9, 7, OUT); cv.rect(mx + 1, top - 7, 7, 6, c); cv.vline(mx + 1, top - 7, 6, shade(c, 0.25))
                cv.rect(mx + 9, top - 6, 2, 4, OUT); cv.px(mx + 10, top - 5, c)
                cv.px(mx + 3, top, "#8ab4d8")
            for k in range(3):
                cv.rect(x0 + 100, top - 3 - k * 3, 18, 3, OUT); cv.hline(x0 + 101, top - 2 - k * 3, 16, ["#d8e040", "#f0a030", "#d8e040"][k])
            cv.rect(x0 + 128, top - 6, 6, 6, OUT); cv.rect(x0 + 129, top - 5, 4, 5, "#2a2832"); cv.vline(x0 + 132, top - 10, 4, OUT)
    return F.trestle_table(160, 30, cloth=F.TEAL_C, seed=6, items=items, top_height=20)


# --- background ----------------------------------------------------------------------------------
def spread_canvas(w=170, h=44, seed=0):
    """The wet canvas left for daylight: spread flat on the lawn, pegged at the corners, a puddle
    in its sag, the red stripe of its edge showing (overlay for volunteers_released)."""
    rng = np.random.default_rng(seed)
    cv = Canvas(w + 8, h + 8, seed=seed)
    ox, oy = 4, 4
    skew = 10
    pts = [(ox + skew, oy), (ox + w, oy + 2), (ox + w - skew, oy + h), (ox, oy + h - 3)]
    cv.poly([(p[0], p[1] + 2) for p in pts], C("#0d0b16", 0.35))
    cv.poly(pts, F.CANVAS[3])
    for k in range(0, w, 22):   # panel seams
        cv.line(ox + skew + k, oy + 1, ox + k, oy + h - 3, F.CANVAS[2])
    cv.poly([(ox + skew, oy), (ox + w, oy + 2), (ox + w - 1, oy + 6), (ox + skew - 1, oy + 4)], F.RED[3])
    cv.ellipse(ox + w // 2 - 22, oy + h // 2 - 5, 44, 12, "#7a7698")
    cv.ellipse(ox + w // 2 - 16, oy + h // 2 - 3, 30, 7, "#9a92b4")
    for _ in range(40):
        cv.px(ox + int(rng.integers(12, w - 12)), oy + int(rng.integers(8, h - 6)), F.CANVAS[2])
    for p in pts:
        cv.rect(p[0] - 1, p[1] - 3, 2, 4, F.WOOD[2]); cv.px(p[0] - 1, p[1] - 3, F.WOOD[4])
    return cv


def generator(cv, x, base):
    """A towable diesel generator at the back of the field: housing, vents, a red panel light."""
    w, h = 64, 30
    cv.rect(x, base - h, w, h, OUT)
    cv.rect(x + 1, base - h + 1, w - 2, h - 6, "#3e5a4a"); cv.hline(x + 1, base - h + 1, w - 2, "#5a7a64")
    for vx in range(x + 6, x + 34, 4):
        cv.vline(vx, base - h + 6, 12, "#2a3e34")
    cv.rect(x + 40, base - h + 5, 18, 9, "#2a2832"); cv.px(x + 43, base - h + 8, "#f05a4a"); cv.px(x + 47, base - h + 8, "#5cf08a")
    cv.rect(x + 36, base - h + 15, 26, 9, "#2a3e34")
    text(cv, "GEN2", x + 37, base - h + 15, "#e6d6b1")
    cv.rect(x + 10, base - h - 8, 4, 8, OUT)
    cv.ellipse(x + 4, base - 6, 10, 10, OUT); cv.ellipse(x + w - 14, base - 6, 10, 10, OUT)
    cv.rect(x - 10, base - 4, 12, 2, OUT)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=12)
    twinkles = []

    # sky, far trees, the audience lawn's glow to the right
    sky, _ = F.farrand_sky(W, 150, panels=(1, 0, 1, 0), offset=120, scale=2.0, stars=50, seed=6)
    bg.a[:150] = sky
    F.far_hedge(bg, 0, W, FAR_EDGE, seed=5)
    stage_pts = F.distant_stage(bg, 742, FAR_EDGE + 2, w=150, h=56, seed=6)
    F.treeline_back(bg, -10, 820, FAR_EDGE + 6, seed=9, heights=(70, 112), gap=(44, 76), skip=[(668, 820)])
    F.lawn(bg, 0, FAR_EDGE, W, H - FAR_EDGE, seed=21, clover=0.03, leaves=0.1, stripes=(46, 0.3))
    bg.rect(0, FAR_EDGE, W, WALK_TOP - FAR_EDGE, C("#2a2440", 0.32))
    # backstage clutter left of the tent: generator, pallets, a light tower
    generator(bg, 40, WALK_TOP + 2)
    for k in range(3):
        bg.rect(118, WALK_TOP - 6 - k * 6, 34, 5, OUT); bg.rect(119, WALK_TOP - 5 - k * 6, 32, 3, F.PLY[3]); bg.hline(119, WALK_TOP - 5 - k * 6, 32, F.PLY[5])
    lt = F.light_tower(bg, 16, WALK_TOP - 4, 92, seed=4)
    # festoon masts and strings at the back, across to the stage glow
    for (mx, mh) in [(150, 96), (660, 92)]:
        bg.rect(mx, WALK_TOP - mh, 3, mh, "#2a2432"); bg.vline(mx, WALK_TOP - mh, mh, "#3e3646")
    twinkles += F.festoon(bg, 0, 70, 150, WALK_TOP - 96, sag=12, every=8, seed=3)
    twinkles += F.festoon(bg, 663, WALK_TOP - 92, W, 66, sag=12, every=8, seed=4)

    # plywood apron in front of the tent, mat path down to the cable walk, path to the lawn
    ax0, ay0, aw, ah = APRON
    F.plywood_deck(bg, ax0, ay0, aw, ah, seed=11)
    F.mat_path_vertical(bg, lambda y: 210 + (y - 456) * 0.05, ay0 + ah, H - 24, width=36, seed=3)
    F.mat_walkway(bg, lambda x: float(np.interp(x, [ax0 + aw, 800], [326, 342])), width=44, seed=4, x0=ax0 + aw, x1=W)
    F.trodden_patch(bg, 210, 452, 40, 12, seed=5)
    F.trodden_patch(bg, 700, 300, 50, 18, seed=6)
    F.trodden_patch(bg, 90, 250, 46, 30, seed=7)
    # cables: generator to the tent, tent to the lawn
    F.cable_run(bg, [(70, WALK_TOP + 2), (96, 180), (120, 214), (150, 226)], count=3, seed=7, tape_every=40)
    F.cable_run(bg, [(650, 228), (690, 260), (720, 300), (800, 318)], count=2, seed=8, tape_every=45)
    F.cable_ramp_vertical(bg, 724, 304, 352)
    # wet boards and puddles from the storm
    F.puddle(bg, 330, 320, 22, 5, seed=4)
    F.puddle(bg, 86, 330, 30, 8, seed=5, reflect=("#f6cf7a", "#e8a0d0"))
    F.puddle(bg, 700, 432, 24, 7, seed=6)
    for kind, (x, y) in zip(["cup", "band", "flyer", "cup_down", "cap", "flyer"],
                            [(476, 380), (300, 412), (660, 236), (120, 410), (560, 272), (40, 300)]):
        F.litter(bg, x, y, kind)
    # light: the tent's open front spills warm light on the apron, the pole lamp, the lawn exit
    F.light_pool(bg, 400, 240, 230, 34, strength=0.3)
    F.light_pool(bg, 156, 336, 50, 15, strength=0.24)
    F.light_pool(bg, 800, 340, 80, 30, strength=0.2)
    # edges: hedges on the sides, hay bales along the bottom
    for x0_ in (0, W - 20):
        bg.rect(x0_, WALK_TOP, 20, H - WALK_TOP, C("#0d0b16", 0.35))
    rng = np.random.default_rng(8)
    for y in range(WALK_TOP - 6, H - 20, 14):
        for xx in (-8, W - 12):
            if xx > 400 and 312 < y < 362:
                continue  # opening to the audience lawn
            bg.paste(shrub(0, 0, 20, 16, seed=int(rng.integers(1e6))), xx, y)
    x = -6
    while x < W:
        if 180 < x < 240:
            x += 60
            continue
        bw = int(rng.integers(30, 40))
        bale, _, _ = F.hay_bales(bw, 18, seed=int(rng.integers(1e6)))
        bg.paste(bale, x, H - 25)
        x += bw + int(rng.integers(0, 10))
    bg.rect(0, H - 24, W, 24, C("#0d0b16", 0.35))
    # festoon mast at the right edge for the string from the tent
    bg.rect(786, 210, 3, 86, OUT); bg.vline(787, 211, 84, F.WOOD[3]); bg.rect(782, 294, 11, 4, OUT)
    bg.save(os.path.join(out, "background.png"))
    spread_canvas(seed=3).save(os.path.join(out, "wet-canvas.png"))

    # --- props ------------------------------------------------------------------------------------
    props = {}

    def save(index, made, extra=None, name=None):
        sprite, sx_, sy_ = made[:3]
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [int(sx_), int(sy_)]}
        entry.update(extra or {})
        if str(index) in props:
            props[str(index)].update({"flag": entry["flag"], "flag_texture": entry["texture"]})
        else:
            props[str(index)] = entry

    board = signup_board(False)
    board_done = signup_board(True)
    tents = []
    for released in (False, True):
        tent, tax, tay = volunteer_tent(released)
        cut(tent, tax, tay, *board, NOTICE)
        tents.append((tent, tax, tay))
    save(0, tents[0])
    save(0, tents[1], {"flag": "volunteers_released"}, name="prop-0-released.png")
    save(1, checkin_table(False))
    save(1, checkin_table(True), {"flag": "volunteers_released"}, name="prop-1-released.png")
    save(2, F.hay_bales(90, 30, seed=4, blanket=F.RED))
    save(3, F.hay_bales(100, 30, seed=5, blanket=F.TEAL_C))
    pole, pax, pay, bulb = F.festoon_pole(55, seed=4)
    save(4, (pole, pax, pay))
    save(5, board)
    save(5, board_done, {"flag": "volunteers_released"}, name="prop-5-released.png")

    # overhead string from the pole to the tent's front corner, y-sorted in pieces
    occluders = []
    occluders += F.festoon_occluders(ROOM, out, "festoon-b", 640, 152, 232, 787, 214, 296, sag=16, every=9, seed=42, pieces=4)

    return {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": occluders,
        "overlays": [{"texture": f"res://assets/art/rooms/{ROOM}/wet-canvas.png", "x": 452, "y": 384, "flag": "volunteers_released"}],
        "props": props,
        "label_only": [],
        "fauna": [
            {"kind": "moth", "x": 151, "y": 285, "range": 6, "speed": 2.1, "rate": 8.0},
            {"kind": "moth", "x": 161, "y": 293, "range": 5, "speed": 1.6, "rate": 7.0, "flip": True},
            {"kind": "fox", "x": 690, "y": 200, "range": 24, "speed": 0.35, "rate": 3.0},
            {"kind": "bat", "x": 300, "y": 30, "fly": 19.0, "rate": 7.0},
        ],
        "leaves": [],
        "layers": [
            {"kind": "beam", "x": 712, "y": FAR_EDGE - 50, "angle": -100, "sweep": 16, "period": 9.0, "phase": 1.0,
             "length": 120, "width": 24, "color": "c8b0ff", "alpha": 0.14, "floor": -400},
            {"kind": "beam", "x": 770, "y": FAR_EDGE - 50, "angle": -80, "sweep": 16, "period": 10.5, "phase": 3.0,
             "length": 120, "width": 24, "color": "ffd0e8", "alpha": 0.13, "floor": -400},
            {"kind": "twinkle", "points": twinkles, "rate": 1.8, "min": 0.4},
            {"kind": "twinkle", "points": [[x, y, "f6dca0", 1] for (x, y) in stage_pts] + [[x, y, "fff0c4", 1] for (x, y) in lt], "rate": 1.2, "min": 0.5},
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT))[:300])
