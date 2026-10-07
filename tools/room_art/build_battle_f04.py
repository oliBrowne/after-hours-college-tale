"""Battle backdrop for the audience lawn (F04): standing in the mat aisle between the rows of
folding chairs, looking up at the main stage close enough to read it. The arched truss throws
beams into the dusk, the LED wall shows the mountains, the banner reads LAST LIGHT / ONE FINAL
SET. The delay towers stand out in the field (the owl still on the left one), festoons hang from
them to the poles at the cross-walk, and in front of the lip Chip's three called columns are taped
on the grass. The volunteer tent glows far left, the crew compound's portacabins far right."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C
from sky import flatirons_panel
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light
import lib_farrand as F
import lib_farrand2 as G

ROOM = "F04"
INK = "#10121e"
HAZE = "#3a2c48"
AISLE_X = -50.0           # world X of the aisle (and the stage's centre line)
AISLE_HALF = 34.0         # the mat aisle is 68 units wide (40 room px)
CROSS = (470.0, 518.0)    # the cross-walk mats behind the chairs
Z_LIP = 820.0             # front of the stage skirt
ROW_Z = 430.0             # the front row of chairs (the second row is behind the camera)
ROW_GAP = 127.0           # aisle centre to the inner end of a chair row (75 room px)
ROW_W = 289.0             # a row is 170 room px
ROW_H = 40.0              # folding chairs reach a person's hip
POLES = [(AISLE_X - 470, 494.0), (AISLE_X + 470, 494.0)]
POLE_H = 94.0
TOWERS = [(AISLE_X - 600, 900.0), (AISLE_X + 760, 900.0)]
COLUMNS = [-105.0, 0.0, 105.0]   # Chip's called columns, from the aisle line

# the stage sprite, painted at room scale
S_W, S_CX, S_ROOF, S_LIP, S_FACE, S_DECK = 560, 280, 56, 190, 28, 360


def ground_shader(X, Z):
    rgb = F.battle_grass_rgb(X, Z, stripe=96.0, seed=4)
    m = pal_array(F.MAT)
    dx = X - AISLE_X
    aisle = (np.abs(dx) < AISLE_HALF) & (Z < Z_LIP + 4)
    cross = (Z > CROSS[0]) & (Z < CROSS[1])
    # trodden mud: in front of the lip, along the aisle edges, at the cross-walk ends
    mud = np.zeros_like(X, bool)
    for (mx, mz, rx, rz) in [(AISLE_X - 70, 700, 70, 40), (AISLE_X + 90, 760, 80, 34), (AISLE_X - 200, 780, 60, 24),
                             (AISLE_X + 60, 380, 30, 50), (AISLE_X - 60, 560, 28, 40), (AISLE_X + 230, 650, 50, 26)]:
        d = np.hypot((X - mx) / rx, (Z - mz) / rz) + 0.35 * (hash2(np.floor(X / 9), np.floor(Z / 9), 3) - 0.5)
        mud |= d < 1
    dirt = pal_array(F.DIRT)
    tone = hash2(np.floor(X / 7), np.floor(Z / 11), 8)
    rgb[mud] = (dirt[2] * 0.55 + rgb[mud] * 0.45) * (0.9 + 0.2 * tone[mud, None])
    rgb[mud & (tone > 0.85)] = pal_array(F.STRAW)[3]
    # the cross-walk (mats laid across) and the aisle (mats laid along), dark lips at the edges
    rgb[cross] = F.battle_mats_rgb(Z[cross] - (CROSS[0] + CROSS[1]) / 2, X[cross], half=(CROSS[1] - CROSS[0]) / 2, seed=2)
    rgb[aisle] = F.battle_mats_rgb(dx[aisle], Z[aisle], half=AISLE_HALF, seed=3)
    rgb[aisle & (np.abs(dx) >= AISLE_HALF - 2)] = m[0]
    rgb[cross & ~aisle & ((Z < CROSS[0] + 2) | (Z > CROSS[1] - 2))] = m[0]
    # taped cable runs: one beside the aisle to the lip, one out to the crew gate on the right
    run = np.abs(X - (AISLE_X + AISLE_HALF + 12 + 3 * np.sin(Z / 37))) < 1.2
    rgb[run & (Z < Z_LIP)] = pal_array(["#1e1c24"])[0]
    tape = run & (np.mod(Z, 90) < 6) & (Z < Z_LIP)
    rgb[tape] = pal_array(F.HAZARD)[3]
    run2 = (np.abs(Z - (Z_LIP - 30 - 0.08 * (X - AISLE_X))) < 2.0) & (X > AISLE_X + 120)
    rgb[run2] = pal_array(["#22202a"])[0]
    # Chip's called columns: tape crosses before the lip, a dashed line across, white number tabs
    tw = pal_array(["#e8e4d8", "#c8382c", "#f2cf5c"])
    for k, cxo in enumerate(COLUMNS):
        cx = AISLE_X + cxo
        for cz in (Z_LIP - 44, Z_LIP - 92):
            dz = (Z - cz) * 0.55
            arm = (np.abs((X - cx) - dz) < 1.6) | (np.abs((X - cx) + dz) < 1.6)
            rgb[arm & (np.abs(X - cx) < 9)] = tw[0]
        tab = (np.abs(X - cx) < 6) & (Z > Z_LIP - 22) & (Z < Z_LIP - 8)
        rgb[tab] = tw[2]
    dash = (np.abs(Z - (Z_LIP - 130)) < 3) & (np.mod(X, 22) < 12) & (np.abs(X - AISLE_X) < 150)
    rgb[dash] = tw[0]
    # puddles holding the dusk
    for (px_, pz, rx, rz) in [(AISLE_X - 330, 700, 46, 22), (AISLE_X + 300, 420, 40, 18)]:
        d = np.hypot((X - px_) / rx, (Z - pz) / rz) + 0.25 * (hash2(np.floor(X / 6), np.floor(Z / 6), 9) - 0.5)
        water = d < 1
        rgb[water] = pal_array(["#5a4a78"])[0]
        rgb[water & (Z < pz - rz * 0.3)] = pal_array(["#8a5a84"])[0]
        rgb[water & (np.abs(X - px_) < rx * 0.15)] = pal_array(["#c88a6a"])[0]
    # stage spill on the grass in front of the lip: amber centre, pink and violet to the sides
    warm_light(rgb, np.hypot((X - AISLE_X) * 0.6, (Z - Z_LIP) * 0.9), 200, colour="#f6c27a", strength=0.42)
    warm_light(rgb, np.hypot((X - AISLE_X + 190) * 0.8, (Z - Z_LIP + 40) * 1.2), 110, colour="#e890c0", strength=0.3)
    warm_light(rgb, np.hypot((X - AISLE_X - 190) * 0.8, (Z - Z_LIP + 40) * 1.2), 110, colour="#a890e8", strength=0.3)
    for (lx, lz) in POLES:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.6), 120, strength=0.4)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 1100, 3400, amount=0.85)
    return out


def stage_sprite():
    """The main stage at room scale, as seen from the lawn at eye level: the deck top is edge-on,
    so the back gear stands right on the lip; the scaffold wings and masking go down to the ground
    behind the deck. The banner is left off here and drawn crisp after the reduce."""
    H = S_LIP + S_FACE + 6
    cv = Canvas(S_W, H, seed=4)
    ground = S_LIP + S_FACE - 4
    info = G.main_stage(cv, S_CX, S_DECK, ground, S_LIP, S_ROOF, rise=18, gear=False, deck=False, stairs=False,
                        banner=None, screen_h=64, seed=4)
    x0, x1 = S_CX - S_DECK // 2, S_CX + S_DECK // 2
    cv.rect(x0, S_LIP - 3, S_DECK, 3, G.DECK[3])
    base = S_LIP - 2
    G.drum_riser(cv, S_CX, base, w=86, seed=4)
    G.amp_stack(cv, S_CX - S_DECK // 4 - 20, base, 24, 30)
    G.amp_stack(cv, S_CX - S_DECK // 4 + 6, base, 24, 21, head=False)
    G.amp_stack(cv, S_CX + S_DECK // 4 - 4, base, 30, 34)
    G.keys_stand(cv, x0 + 22, base)
    G.guitar_on_stand(cv, S_CX + S_DECK // 4 + 36, base)
    G.guitar_on_stand(cv, S_CX - S_DECK // 4 - 30, base, body="#e0b23a")
    for mx in (S_CX - S_DECK // 6, S_CX + S_DECK // 6 + 10):
        G.mic_stand(cv, mx, base, 30, -1 if mx < S_CX else 1)
    front, fax, fay, finfo = G.stage_front(S_DECK, S_FACE, seed=4)
    fx0, fy0 = S_CX - fax, S_LIP + S_FACE - fay
    cv.paste(front, fx0, fy0)
    info["foot"] = [[fx0 + p[0], fy0 + p[1]] for p in finfo["lamps"]]
    info["wedge_leds"] = [[fx0 + p[0], fy0 + p[1]] for p in finfo["wedges"]]
    return cv, S_CX, S_LIP + S_FACE, info


def backstage_sprite():
    """The crew compound far right: scrim fence with the CREW ONLY sign, two portacabins with lit
    windows behind it, a light tower."""
    cv = Canvas(200, 90, seed=6)
    base = 86
    for k in range(2):
        x0 = 30 + k * 76
        cv.rect(x0, base - 52, 68, 34, G.OUT)
        cv.rect(x0 + 1, base - 51, 66, 32, G.CABIN[2]); cv.hline(x0 + 1, base - 51, 66, G.CABIN[4])
        for sx in range(x0 + 4, x0 + 66, 4):
            cv.vline(sx, base - 49, 30, G.CABIN[1])
        for wx in (x0 + 8, x0 + 40):
            cv.rect(wx, base - 44, 16, 10, "#1a1524"); cv.rect(wx + 1, base - 43, 14, 8, F.BULB[2])
            cv.rect(wx + 1, base - 43, 14, 2, F.BULB[3]); cv.vline(wx + 8, base - 43, 8, "#1a1524")
        cv.rect(x0 - 1, base - 55, 70, 4, "#1a1524"); cv.hline(x0, base - 54, 68, G.CABIN[5])
    pts = F.light_tower(cv, 184, base, 84, seed=8)
    for x in range(0, 200):
        k = x % 40
        if k in (0, 1):
            cv.vline(x, base - 30, 30, F.STEEL[4] if k == 0 else F.STEEL[2])
            continue
        for y in range(base - 28, base - 2):
            cv.px(x, y, G.SCRIM[2] if (x + y) % 3 else G.SCRIM[3])
        cv.px(x, base - 28, G.SCRIM[4])
    from pixel import text, text_width
    lw = text_width("CREW ONLY") + 8
    cv.rect(70, base - 24, lw, 11, "#1a1524"); cv.rect(71, base - 23, lw - 2, 9, F.HAZARD[3])
    text(cv, "CREW ONLY", 74, base - 24, "#1a1720")
    return cv, 100, base, pts


def mapper(at, ax, ay):
    """Canvas px -> screen px for a sprite placed by View.sprite (returns (sx, sy, s))."""
    sx, sy, s = at
    return lambda p: (sx + (p[0] - ax) * s, sy + (p[1] - ay) * s)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    v = View(horizon=98, cam=52, fill="#1b1830")
    pw = flatirons_panel(scale=1.9).shape[1]
    sky, _ = F.farrand_sky(640, 132, panels=(1, 0, 1), offset=pw - (300 - pw // 2), scale=1.9, stars=30, seed=9)
    v.strip(sky, 0, solid=False)
    v.strip(F.field_treeline(640, 34, seed=5, open_span=(170, 430)), 98 - 34 + 8)
    v.ground(ground_shader)

    # far: the volunteer tent and the crew compound
    tent, tax, tay = F.peaked_tent(196, 72, 40, open_front=False, seed=4, valance_text="VOLUNTEERS",
                                   poles=[0, 64, 129, 193])
    v.sprite(tent.a, -1150, 1500, anchor=(tax / tent.w, tay / tent.h), scale=ROOM_TO_BATTLE)
    bs, bax, bay, bs_pts = backstage_sprite()
    bs_at = v.sprite(bs.a, 1060, 1350, anchor=(bax / bs.w, bay / bs.h), scale=ROOM_TO_BATTLE)
    bs_map = mapper(bs_at, bax, bay)

    # delay towers out in the field
    tower_pts, tower_tops = [], []
    for k, (tx, tz) in enumerate(TOWERS):
        tw = Canvas(110, 136, seed=k)
        tpts = G.delay_tower(tw, 49, 132, 118, seed=k)
        at = v.sprite(tw.a, tx, tz, anchor=(55 / 110, 132 / 136), scale=ROOM_TO_BATTLE)
        m = mapper(at, 55, 132)
        tower_pts += [m(p) for p in tpts]
        tower_tops.append(m((55, 132 - 118 - 4)))

    # the stage
    st, sax, say, sinfo = stage_sprite()
    st_at = v.sprite(st.a, AISLE_X, Z_LIP, anchor=(sax / st.w, say / st.h), scale=ROOM_TO_BATTLE)
    sm = mapper(st_at, sax, say)

    # festoon poles on the cross-walk, then the front row of chairs (painted at on-screen size)
    def rows_at(z):
        h = int(round(ROW_H * v.scale(z)))
        w = int(round(ROW_W * v.scale(z)))
        for side in (-1, 1):
            cvr, rax, ray = G.chair_row(w, h, n=8, seed=int(z) + side)
            xc = AISLE_X + side * (ROW_GAP + ROW_W / 2)
            v.sprite(cvr.a, xc, z, anchor=(rax / cvr.w, ray / cvr.h), scale=z / v.F)
    pole_tops = []
    for (x, z) in POLES:
        h = int(round(POLE_H * v.scale(z)))
        pole, pax, pay, bulb = F.festoon_pole(h, arm=max(4, h // 6), seed=int(z) + int(x > 0), flip=x > 0)
        sx, sy, _ = v.sprite(pole.a, x, z, anchor=(pax / pole.w, pay / pole.h), scale=z / v.F)
        pole_tops.append(((sx, sy - h + 2), (sx - pax + bulb[0], sy - pay + bulb[1])))
    rows_at(ROW_Z)

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp: the banner under the truss
    arch = sinfo["arch"]
    by_c = arch(S_CX) + 11 + 5
    bx, by = sm((S_CX, by_c))
    label = "LAST LIGHT / ONE FINAL SET"
    from pixel import text_width
    bw = text_width(label) + 16
    truss_y = int(round(sm((S_CX, arch(S_CX) + 11))[1]))
    bx, by = int(round(bx)), int(round(by)) - 2
    G.stage_banner(cv, bx, by, label, tie_to=[(bx - bw // 2 + 3, truss_y), (bx + bw // 2 - 4, truss_y)])

    # crisp string lights: tower tops to the stage wings, towers to the poles, one span overhead
    wl, wr = sinfo["wings"]
    wing_top = S_ROOF + 18 - 14
    wing_l = sm((wl + 10, wing_top + 4))
    wing_r = sm((wr + 10, wing_top + 4))
    twinkles = []
    twinkles += F.string_across(cv, tower_tops[0], wing_l, sag=10, every=8, seed=1)
    twinkles += F.string_across(cv, wing_r, tower_tops[1], sag=10, every=8, seed=2)
    twinkles += F.string_across(cv, pole_tops[0][0], tower_tops[0], sag=12, every=9, seed=3)
    twinkles += F.string_across(cv, tower_tops[1], pole_tops[1][0], sag=12, every=9, seed=4)
    twinkles += F.string_across(cv, (-14, 20), pole_tops[0][0], sag=10, every=12, seed=5)
    twinkles += F.string_across(cv, pole_tops[1][0], (654, 16), sag=10, every=12, seed=6)
    twinkles += F.string_across(cv, pole_tops[0][0], pole_tops[1][0], sag=9, every=13, seed=7)

    lamps = [[int(round(sm(p)[0])), int(round(sm(p)[1])), p[2], 1] for p in sinfo["lamps"]]
    lamps += [[int(round(sm(p)[0])), int(round(sm(p)[1])), "f6dca0", 1] for p in sinfo["tower_lamps"]]
    lamps += [[int(round(p[0])), int(round(p[1])), "fff0c4", 1] for p in tower_pts]
    lamps += [[int(round(p[1][0])), int(round(p[1][1])), "fff0c4", 2] for p in pole_tops]
    foot = [[int(round(sm(p)[0])), int(round(sm(p)[1])), "f6cf7a", 1] for p in sinfo["foot"]]
    win = [[int(round(bs_map(p)[0])), int(round(bs_map(p)[1])), "f6dca0", 1] for p in bs_pts]

    # LED wall scan bands
    sx0, sy0, sw, sh = sinfo["screen"]
    (lx0, ly0), (lx1, ly1) = sm((sx0, sy0)), sm((sx0 + sw, sy0 + sh))
    lx0, ly0, lx1, ly1 = int(round(lx0)), int(round(ly0)), int(round(lx1)), int(round(ly1))
    scans = []
    n = 6
    for k in range(n):
        yy = ly0 + 2 + k * (ly1 - ly0 - 4) // n
        pat = "".join("1" if j == k else "0" for j in range(n + 2))
        scans.append({"kind": "blink", "pattern": pat, "rate": 5.0, "rects": [[lx0 + 1, yy, lx1 - lx0 - 2, 2, "b8a8e8", 0.12]]})
    leds = [[int(round(sm(p)[0])), int(round(sm(p)[1])), 1, 1, "5cf08a"] for p in sinfo["wedge_leds"]]

    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = v.solid_mask().astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))

    res = f"res://assets/art/rooms/{ROOM}/"
    owl = tower_tops[0]
    lip_y = int(round(sm((S_CX, S_LIP))[1]))
    truss_l = sm((S_CX - 90, arch(S_CX - 90) + 14))
    truss_r = sm((S_CX + 90, arch(S_CX + 90) + 14))
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "beam", "depth": "far", "x": int(round(wing_l[0])), "y": int(round(wing_l[1])), "angle": -112, "sweep": 14,
             "period": 9.0, "phase": 0.0, "length": 120, "width": 24, "color": "c8b0ff", "alpha": 0.18, "floor": -400},
            {"kind": "beam", "depth": "far", "x": int(round(wing_r[0])), "y": int(round(wing_r[1])), "angle": -68, "sweep": 14,
             "period": 10.5, "phase": 2.2, "length": 120, "width": 24, "color": "ffd0e8", "alpha": 0.18, "floor": -400},
            {"kind": "beam", "x": int(round(truss_l[0])), "y": int(round(truss_l[1])), "angle": 100, "sweep": 9, "period": 7.0,
             "phase": 1.0, "length": 100, "width": 34, "color": "fff0c4", "alpha": 0.16, "floor": lip_y + 18},
            {"kind": "beam", "x": int(round(truss_r[0])), "y": int(round(truss_r[1])), "angle": 80, "sweep": 10, "period": 8.5,
             "phase": 3.4, "length": 100, "width": 34, "color": "f2b0d0", "alpha": 0.15, "floor": lip_y + 16},
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "bat", "x": 60, "y": 30, "fly": 14.0, "rate": 7.0},
                {"kind": "bat", "x": 560, "y": 86, "fly": 12.0, "rate": 6.0}]},
            {"kind": "fauna", "fauna": [
                {"kind": "barn_owl", "x": int(round(owl[0])), "y": int(round(owl[1])) - 2, "range": 0, "speed": 0.0, "rate": 0.5}]},
            *scans,
            {"kind": "twinkle", "points": twinkles, "rate": 2.0, "min": 0.35},
            {"kind": "twinkle", "points": lamps + win, "rate": 1.3, "min": 0.55},
            {"kind": "twinkle", "points": foot, "rate": 0.9, "min": 0.6},
            {"kind": "blink", "pattern": "1000", "rate": 1.5, "rects": leds},
            {"kind": "particles", "style": "dust", "count": 12, "rect": [lx0 - 40, lip_y - 40, lx1 - lx0 + 80, 50],
             "speed": [0, -4], "color": "f6e0b0"},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:400])
