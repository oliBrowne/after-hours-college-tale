"""Battle backdrop for the main stage (F06): the fight is on the stage deck itself, looking out
over the lit lip at the field the show was for. The front truss runs across the top with its
lamps, the roof's corner legs (with side lights) frame the view, the PA hangs drop outside them
against the pleated black masking, the ground subs stand at the deck's corners and the wedges face
us along the edge; the lone mic stands centre stage with the setlist taped at its foot, and the
fighters stand in the truss lamps' pink and violet pools. Out past the lip the field lies under
the eastern dusk (the Flatirons are behind us now), the full moon rising in the pink belt over the
trees: the aisle mat, rows of folding chairs facing us, the festoon poles with their strings, the
delay towers, the mix tent at the back of the field, and far off campus with Norlin's lit windows.
Beams sweep out over the field; a car's lights crawl through the gap in the trees."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, text, text_width
from props import OUT
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light
import lib_farrand as F
import lib_farrand2 as G

ROOM = "F06"
INK = "#10121e"
HAZE = "#4a3a5e"
DECK_H = 48.0              # the deck stands 28 room px above the field
Z_LIP = 440.0              # front edge of the deck
DECK_HALF = 297.0          # half the deck's width (350 room px)
MASK_X = 330.0             # the black masking legs at the sides of the stage
AISLE_HALF = 36.0
ROWS = [1000.0, 1090.0]    # front rows of chairs, either side of the aisle
POLES = [(-150, 1150), (150, 1300), (-150, 1500), (150, 1750)]
TOWERS = [(-440, 1550), (440, 1550)]
Z_FOH = 2100.0


def lawn_shader(X, Z):
    rgb = F.battle_grass_rgb(X, Z, stripe=96.0, seed=9)
    ax = np.abs(X)
    pit = (Z < Z_LIP + 150) & (ax < DECK_HALF + 20)
    aisle = (ax < AISLE_HALF) & (Z >= Z_LIP + 150) & (Z < Z_FOH - 60)
    rgb[pit] = F.battle_mats_rgb(X[pit], Z[pit], half=DECK_HALF, seed=1)
    rgb[aisle] = F.battle_mats_rgb(X[aisle], Z[aisle], half=AISLE_HALF, seed=2)
    rgb[aisle & (ax > AISLE_HALF - 2.5)] = pal_array(F.MAT)[0]
    cross = (np.abs(Z - 1230) < 26)
    rgb[cross] = F.battle_mats_rgb(Z[cross] - 1230, X[cross], half=26, seed=3)
    # trodden mud where the crowd stood, confetti near the stage
    dirt = pal_array(F.DIRT)
    worn = hash2(np.floor(X / 26), np.floor(Z / 40), 5) > 0.7
    worn &= ~(pit | aisle | cross)
    rgb[worn] = rgb[worn] * 0.6 + dirt[2] * 0.4
    conf = (hash2(np.floor(X / 3), np.floor(Z / 5), 13) > 0.94) & (Z < 1300)
    cols = pal_array(["#f06a8a", "#f6cf7a", "#7ad0c8", "#c8a0f0", "#f2f2ee"])
    pick = (hash2(np.floor(X / 3), np.floor(Z / 5), 17) * 4.99).astype(int)
    rgb[conf] = cols[pick[conf]]
    # the stage's spill on the pit, the delay towers' pools, the mix tent's glow
    warm_light(rgb, np.hypot(X * 0.5, (Z - Z_LIP) * 0.9), 330, colour="#f0a0c8", strength=0.4)
    warm_light(rgb, np.hypot(X * 0.8, (Z - Z_LIP - 60) * 1.2), 160, colour="#f6c27a", strength=0.3)
    for (tx, tz) in TOWERS:
        warm_light(rgb, np.hypot(X - tx, (Z - tz) * 0.4), 140, strength=0.3)
    warm_light(rgb, np.hypot(X, (Z - Z_FOH) * 0.3), 160, colour="#f6dca0", strength=0.3)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 1200, 4200, amount=0.85)
    return out


def deck_shader(X, Z):
    """The stage deck under the fighters: black-painted 8x4 panels with dark joints and scuffs,
    coloured spike marks where the band stood, two cable runs taped down from the wedges back to
    the drum riser, the setlist taped at the mic's foot, the downstage edge taped white, the lit
    nosing at the lip, and the truss lamps' pools of pink, amber and violet."""
    d = pal_array(G.DECK)
    col = np.floor((X + 1000) / 106)
    row = np.floor(Z / 53)
    tone = hash2(col, row, 3)
    rgb = d[3] * (1 - tone[:, None] * 0.35) + d[4] * (tone[:, None] * 0.35)
    grain = hash2(np.floor(X / 3), np.floor(Z / 11), 5)
    rgb *= (0.96 + 0.06 * grain[:, None])
    fx = (X + 1000) / 106 - col
    fz = Z / 53 - row
    rgb[(fx < 0.012) | (fz < 0.03)] = d[2]
    scuff = hash2(np.floor(X / 3), np.floor(Z / 2), 8) > 0.988
    rgb[scuff] = d[4]
    # spike marks: small coloured tape crosses where the band stood
    for (sx, sz, c) in [(-230, 300, "#f6cf7a"), (230, 296, "#7ad0c8"), (-120, 372, "#f06a8a"), (140, 366, "#f2f2ee")]:
        dz = (Z - sz) * 1.6
        arm = ((np.abs((X - sx) - dz) < 1.6) | (np.abs((X - sx) + dz) < 1.6)) & (np.abs(X - sx) < 7)
        rgb[arm] = pal_array([c])[0]
    # two cable runs taped down, straight back from the centre wedges
    for cx in (-86.0, 86.0):
        line = (np.abs(X - cx) < 1.6) & (Z < Z_LIP - 20)
        rgb[line] = pal_array(["#100e16"])[0]
        rgb[line & (X - cx > 0.6)] = pal_array(["#3a3444"])[0]
        tape = (np.abs(X - cx) < 4.5) & (np.mod(Z, 48) < 5) & (Z < Z_LIP - 20)
        rgb[tape] = pal_array(["#77798a"])[0]
    # the setlist taped at the mic's foot: a white sheet, typed lines, a red last line
    paper = (np.abs(X - 4) < 15) & (np.abs(Z - 414) < 10)
    rgb[paper] = pal_array(["#e8e4d8"])[0]
    lines = paper & (np.mod(Z - 404, 4.5) < 1.2) & (np.abs(X - 1) < 10)
    rgb[lines] = pal_array(["#6a6670"])[0]
    rgb[paper & (Z > 419.5) & (np.abs(X - 1) < 10) & (Z < 421.5)] = pal_array(["#c8382c"])[0]
    rgb[paper & ((np.abs(X - 4) > 12) & (np.abs(Z - 414) > 7))] = pal_array(["#77798a"])[0]
    # white tape along the downstage edge, the warm nosing at the lip
    rgb[(Z > Z_LIP - 34) & (Z < Z_LIP - 26) & (np.mod(X, 40) < 30) & (np.abs(X) < DECK_HALF)] = pal_array(["#d8d4c8"])[0]
    # the truss lamps' pools on the deck, where the fighters stand
    warm_light(rgb, np.hypot((X + 196) * 0.9, (Z - 336) * 1.4), 120, colour="#ff7ab8", strength=0.62)
    warm_light(rgb, np.hypot((X - 186) * 0.9, (Z - 330) * 1.4), 120, colour="#a890ff", strength=0.62)
    warm_light(rgb, np.hypot(X * 0.9, (Z - 396) * 1.4), 90, colour="#ffd890", strength=0.55)
    wing = np.abs(X) > DECK_HALF                        # the wing platforms, darker, unlit
    rgb[wing] = rgb[wing] * 0.62
    rgb[(Z >= Z_LIP - 14) & ~wing] = pal_array(G.LIP)[1]
    rgb[(Z >= Z_LIP - 7) & ~wing] = pal_array(G.LIP)[3]
    out = rgba_of(rgb)
    out[(Z > Z_LIP) | (np.abs(X) > MASK_X + 1), 3] = 0
    return out


def masking_shader(u, Y, Z):
    """The black masking at the side of the stage: pleated drape (a lit fold, a mid, a shadow
    fold), the violet uplight from the deck climbing it in steps, scaffold ledgers showing faintly
    through, a darker hem where it meets the deck."""
    sc = pal_array(G.SCRIM + ["#3a3446"])
    wash = pal_array(G.WASH)
    k = np.mod(u, 22.0) / 22.0
    fold = np.where(k < 0.18, 4, np.where(k < 0.5, 3, np.where(k < 0.8, 2, 1)))
    rgb = sc[fold].copy()
    t = np.clip(1 - Y / 220.0, 0, 1)
    lvl = (np.ceil(t * 4) / 4) ** 1.6 * 0.5
    up = np.where((fold >= 3)[:, None], wash[3], wash[1])
    rgb = rgb * (1 - lvl[:, None]) + up * lvl[:, None]
    led = (np.mod(Y, 90) < 2.0) & (Y > 40)
    rgb[led] = rgb[led] * 0.7 + pal_array([G.TRUSS[3]])[0] * 0.3
    rgb[(Y < 6) & (Y > -2)] = sc[0]
    out = rgba_of(rgb)
    return out


def roof_leg(cv, x, y0, y1, w=10, inner=1, lamps=((58, "#ffb8d8"), (92, "#c8b0ff"))):
    """The roof's corner leg in front of the masking: a box truss (two lit chords, zigzag
    lacing, battens) with a pair of side-light cans clamped on, aimed across the deck. inner is
    the side facing centre stage (+1 = right). Returns the lit lens points."""
    for yy in range(y0, y1, 12):                         # lacing and battens
        cv.line(x + 1, yy, x + w - 2, yy + 6, G.TRUSS[3]); cv.line(x + w - 2, yy + 6, x + 1, yy + 12, G.TRUSS[3])
        cv.hline(x + 1, yy, w - 2, G.TRUSS[4])
    cv.vline(x - 1, y0, y1 - y0, OUT); cv.vline(x + w, y0, y1 - y0, OUT)
    if inner > 0:     # left leg: its right (inner) chord catches the stage light
        cv.vline(x, y0, y1 - y0, G.TRUSS[2]); cv.vline(x + 1, y0, y1 - y0, G.TRUSS[4])
        cv.vline(x + w - 2, y0, y1 - y0, "#8a6a8a"); cv.vline(x + w - 1, y0, y1 - y0, "#d8b8d0")
    else:
        cv.vline(x, y0, y1 - y0, "#d8b8d0"); cv.vline(x + 1, y0, y1 - y0, "#8a6a8a")
        cv.vline(x + w - 2, y0, y1 - y0, G.TRUSS[4]); cv.vline(x + w - 1, y0, y1 - y0, G.TRUSS[2])
    pts = []
    for (ly, col) in lamps:
        lx = x + w + 1 if inner > 0 else x - 6
        cv.rect(x + (w if inner > 0 else -2), ly + 1, 2, 2, G.TRUSS[0])          # clamp
        cv.rect(lx, ly - 1, 5, 6, OUT); cv.hline(lx, ly - 1, 5, G.TRUSS[4])
        face = lx + 4 if inner > 0 else lx
        cv.vline(face, ly, 4, col); cv.px(face, ly + 1, "#ffffff")
        cv.rect(face - 2 if inner < 0 else face, ly - 1, 3, 6, C(col, 0.16))
        pts.append([face, ly + 1, col.lstrip("#"), 1])
    return pts


def wedge_face():
    """A floor wedge at the lip, its grille angled up at us: woofer, horn, lit top edge, feet."""
    cv = Canvas(32, 16)
    cv.poly([(0, 15), (4, 2), (27, 2), (31, 15)], OUT)
    cv.poly([(1, 14), (5, 3), (26, 3), (30, 14)], G.CASE[1])
    for yy in range(5, 14, 2):
        for xx in range(4, 28, 2):
            cv.px(xx + (yy // 2) % 2, yy, G.CASE[2])
    cv.ellipse(6, 5, 10, 9, G.CASE[0]); cv.ellipse(8, 7, 6, 5, G.CASE[2]); cv.px(10, 9, G.CASE[4])
    cv.rect(18, 6, 8, 5, G.CASE[0]); cv.rect(19, 7, 6, 3, G.CASE[2]); cv.hline(19, 7, 6, G.CASE[3])
    cv.hline(5, 3, 21, G.CASE[5]); cv.hline(5, 2, 22, G.CASE[3])
    cv.px(26, 12, "#5cf08a")
    cv.rect(2, 14, 3, 2, OUT); cv.rect(27, 14, 3, 2, OUT)
    return cv


def front_chairs(width, height, n, seed=0):
    """A row of folding chairs seen from the stage, so from the front: slatted backs, the seat's
    lit front edge, steel legs, at on-screen size. Anchor bottom centre."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 2, height + 2)
    base = height
    pitch = width / n
    cw = max(4, int(pitch) - 2)
    for i in range(n):
        if rng.random() < 0.08:          # a gap where a chair was carried off
            continue
        x = int(round(1 + i * pitch))
        top = base - height + (1 if rng.random() < 0.3 else 0)
        back_h = max(3, height * 4 // 10)
        seat_y = top + back_h + max(1, height // 8)
        cv.rect(x, top, cw, back_h, F.PLY[3]); cv.hline(x, top, cw, F.PLY[5])
        if back_h > 3:
            cv.hline(x + 1, top + back_h // 2, cw - 2, F.PLY[2])
        cv.vline(x, top, seat_y - top + 1, F.STEEL[3]); cv.vline(x + cw - 1, top, seat_y - top + 1, F.STEEL[2])
        cv.rect(x - 1 if cw > 4 else x, seat_y, cw + (2 if cw > 4 else 0), 2, F.PLY[4]); cv.hline(x, seat_y + 1, cw, F.PLY[2])
        cv.rect(x + 1, seat_y + 2, cw - 2, base - seat_y - 2, C(F.STEEL[0], 0.5))
        cv.vline(x, seat_y + 2, base - seat_y - 1, F.STEEL[3]); cv.vline(x + cw - 1, seat_y + 2, base - seat_y - 1, F.STEEL[2])
        if rng.random() < 0.14:          # a programme left on the seat
            cv.rect(x + 1, seat_y - 1, 3, 1, "#f2ead6")
    return cv, 1 + width // 2, base


def mic_stand_near(height):
    """The lone mic at centre stage, at on-screen size: round base, a two-tone pole, the clip and
    the mic, its cable coiled at the foot. Anchor bottom centre."""
    cv = Canvas(20, height + 4)
    cx, base = 9, height + 2
    cv.ellipse(cx - 6, base - 2, 13, 4, OUT); cv.hline(cx - 4, base - 2, 9, G.CASE[3])
    cv.ellipse(cx - 9, base - 1, 8, 3, "#100e16")                       # cable coil
    cv.rect(cx, base - height, 2, height - 1, OUT); cv.vline(cx, base - height + 10, height - 12, G.CASE[4])
    cv.vline(cx, base - height + 2, 8, G.CASE[5])
    cv.rect(cx - 1, base - height + 9, 4, 2, G.CASE[3])                 # clutch
    cv.rect(cx - 1, base - height - 1, 3, 3, G.CASE[2])                 # clip
    cv.rect(cx - 1, base - height - 7, 4, 7, OUT); cv.rect(cx, base - height - 6, 2, 5, "#9aa0ac")
    cv.px(cx, base - height - 6, "#d8dce4"); cv.hline(cx, base - height - 3, 2, "#5a5e6a")
    cv.vline(cx + 2, base - height + 1, height - 4, "#100e16")         # cable down the pole
    return cv, cx, base


def foh_tent():
    """The mix tent at the back of the field: a small open marquee on a riser, the desk glowing."""
    def inside(cv, x, y, w, h):
        cv.rect(x, y, w, h, "#2a2030")
        cv.rect(x + 4, y + h - 12, w - 8, 8, "#3a3644"); cv.hline(x + 4, y + h - 12, w - 8, "#5a5666")
        for k in range(x + 6, x + w - 8, 4):
            cv.px(k, y + h - 10, "#5cf08a" if (k // 4) % 3 else "#f6cf7a")
        cv.rect(x + w // 2 - 8, y + 4, 16, 10, "#6a8ad0"); cv.rect(x + w // 2 - 7, y + 5, 14, 8, "#a8c8f0")
    tent, ax, ay = F.peaked_tent(96, 34, 20, open_front=True, seed=7, interior=inside, valance_text="FOH", ropes=False,
                                 poles=[0, 95])
    return tent, ax, ay


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    v = View(horizon=98, cam=52, fill="#1b1830")
    v.strip(G.sky_east(640, 132, seed=6, horizon=86, moon=(252, 60, 8)), 0, solid=False)
    v.strip(F.field_treeline(640, 30, seed=11, open_span=(400, 470)), 98 - 30 + 4)
    camp = Canvas(140, 52)
    camp_pts = G.campus_far(camp, 8, 50, w=124, seed=3)
    camp_at = v.sprite(camp.a, 300, 3200, Y=-DECK_H, anchor=(0.5, 50 / 52), scale=ROOM_TO_BATTLE * 3200 / 1400)
    v.ground(lawn_shader, height=-DECK_H)

    # out on the field, far to near
    foh, fax, fay = foh_tent()
    v.sprite(foh.a, 0, Z_FOH, Y=-DECK_H, anchor=(fax / foh.w, fay / foh.h), scale=ROOM_TO_BATTLE)
    tower_pts = []
    for k, (tx, tz) in enumerate(TOWERS):
        tw = Canvas(110, 136, seed=k)
        pts = G.delay_tower(tw, 49, 132, 118, seed=k + 3)
        sx, sy, s = v.sprite(tw.a, tx, tz, Y=-DECK_H, anchor=(55 / 110, 132 / 136), scale=ROOM_TO_BATTLE)
        tower_pts += [(sx + (p[0] - 55) * s, sy + (p[1] - 132) * s) for p in pts]
    pole_tops = []
    for (x, z) in sorted(POLES, key=lambda p: -p[1]):
        h = max(12, int(round(94 * v.scale(z))))
        pole, pax, pay, bulb = F.festoon_pole(h, arm=max(3, h // 6), seed=int(z), flip=x > 0)
        sx, sy, _ = v.sprite(pole.a, x, z, Y=-DECK_H, anchor=(pax / pole.w, pay / pole.h), scale=z / v.F)
        pole_tops.append(((x, z), (sx, sy - h + 2), (sx - pax + bulb[0], sy - pay + bulb[1])))
    for z in sorted(ROWS, reverse=True):
        s = v.scale(z)
        w = int(round(300 * s))
        h = max(6, int(round(37 * s)))
        for side in (-1, 1):
            row, rax, ray = front_chairs(w, h, 12, seed=int(z) + side)
            v.sprite(row.a, side * (AISLE_HALF + 34 + 150), z, Y=-DECK_H, anchor=(rax / row.w, ray / row.h), scale=z / v.F)
    # the ground subs at the deck's corners, standing on the field and rising past the deck
    for side in (-1, 1):
        sub, sax, say = G.sub_stack(38, 68, seed=side + 2)
        v.sprite(sub.a[:, ::-1] if side > 0 else sub.a, side * (DECK_HALF + 6), Z_LIP + 24, Y=-DECK_H,
                 anchor=(sax / sub.w, say / sub.h), scale=ROOM_TO_BATTLE)
    # the deck, the wedges on its edge facing us, the lone mic, the masking either side
    v.ground(deck_shader, height=0.0)
    wedge_leds = []
    wedge = wedge_face()
    for x in (-220, -80, 80, 220):
        sx, sy, s = v.sprite(wedge.a if x < 0 else wedge.a[:, ::-1], x, Z_LIP - 22, anchor=(0.5, 15 / 16), scale=ROOM_TO_BATTLE)
        lx = 26 if x < 0 else 5
        wedge_leds.append([int(round(sx + (lx - 16) * s)), int(round(sy + (12 - 15) * s)), "5cf08a", 1])
    mic_h = int(round(66 * v.scale(388)))
    mic, mx, my = mic_stand_near(mic_h)
    v.sprite(mic.a, -6, 388, anchor=(mx / mic.w, my / mic.h), scale=388 / v.F)
    for side in (-1, 1):
        v.plane((side * MASK_X, 80.0), (side * MASK_X, Z_LIP + 40), masking_shader, y_max=420, y_min=0.0)

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp: string lights between the poles and out to the towers
    twinkles = []
    tops = sorted(pole_tops, key=lambda p: -p[0][1])
    for i in range(len(tops) - 1):
        a, b = tops[i][1], tops[i + 1][1]
        depth = (tops[i][0][1] + tops[i + 1][0][1]) / 2
        twinkles += F.string_across(cv, a, b, sag=max(2, int(20 * v.scale(depth))), every=max(4, int(12 * v.scale(depth))), seed=i)
    tt = [v.project(tx, -DECK_H + 118 * ROOM_TO_BATTLE, tz) for (tx, tz) in TOWERS]
    near_l = [t for t in pole_tops if t[0] == (-150, 1150)][0][1]
    near_r = [t for t in pole_tops if t[0] == (150, 1300)][0][1]
    twinkles += F.string_across(cv, tt[0], near_l, sag=6, every=6, seed=11)
    twinkles += F.string_across(cv, near_r, tt[1], sag=6, every=6, seed=12)

    # crisp frame: the front truss across the top with its lamps, the roof's corner legs with
    # their side lights, the PA hangs outside them
    before = cv.a.copy()
    arch = lambda x: int(round(-2 + 0.00006 * (x - 320) ** 2))
    leg_pts = []
    for side in (-1, 1):
        lx, _ = v.project(side * (MASK_X - 6), 0.0, Z_LIP + 36)
        x0 = int(round(lx)) - 5
        leg_pts += roof_leg(cv, x0, arch(x0) + 8, 172, w=10, inner=-side,
                            lamps=((56, "#ffb8d8"), (94, "#c8b0ff")) if side < 0 else ((60, "#c8b0ff"), (98, "#ffd0e8")))
    G.truss_band(cv, -10, 650, arch, 12)
    lamps = []
    kinds = ["par", "head", "par", "par", "head"]
    for i, lx in enumerate(range(20, 640, 30)):
        col = G.LAMP_COLOURS[i % len(G.LAMP_COLOURS)]
        lens = G.stage_lamp(cv, lx, arch(lx) + 12, col, kinds[i % len(kinds)], on=True)
        lamps.append([lens[0], lens[1], col.lstrip("#"), 1])
    for px_ in (14, 598):
        G.line_array(cv, px_, arch(px_) + 18, n=10, w=30, box=10, chain=4, lit=True)
    frame = np.any(np.abs(cv.a - before) > 1e-3, axis=2)

    win = [[int(round(camp_at[0] + (p[0] - 70) * camp_at[2])), int(round(camp_at[1] + (p[1] - 50) * camp_at[2])), "f6dca0", 1]
           for p in camp_pts]
    glows = [[int(round(t[2][0])), int(round(t[2][1])), "fff0c4", 1] for t in pole_tops]
    glows += [[int(round(x)), int(round(y)), "fff0c4", 1] for (x, y) in tower_pts]

    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = np.maximum(v.solid_mask().astype(np.float32), frame.astype(np.float32))
    near[:16, :, 3] = 1.0
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))
    res = f"res://assets/art/rooms/{ROOM}/"
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "beam", "depth": "far", "x": 150, "y": 14, "angle": -60, "sweep": 18, "period": 9.0, "phase": 0.0,
             "length": 120, "width": 24, "color": "c8b0ff", "alpha": 0.14, "floor": -400},
            {"kind": "beam", "depth": "far", "x": 490, "y": 14, "angle": -120, "sweep": 18, "period": 10.0, "phase": 2.0,
             "length": 120, "width": 24, "color": "ffd0e8", "alpha": 0.14, "floor": -400},
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "bat", "x": 200, "y": 40, "fly": 14.0, "rate": 7.0},
                {"kind": "bat", "x": 360, "y": 30, "fly": 11.0, "rate": 6.0}]},
            {"kind": "movers", "from": [404, 99], "to": [468, 99], "count": 1, "period": 16.0,
             "size": [1, 1], "pair": 0, "color": "f6dca0", "ease": "out"},
            {"kind": "beam", "x": 200, "y": 16, "angle": 62, "sweep": 14, "period": 7.0, "phase": 1.0,
             "length": 200, "width": 44, "color": "fff0c4", "alpha": 0.16, "floor": 118},
            {"kind": "beam", "x": 440, "y": 16, "angle": 118, "sweep": 14, "period": 8.0, "phase": 3.0,
             "length": 200, "width": 44, "color": "f2b0d0", "alpha": 0.15, "floor": 118},
            {"kind": "twinkle", "points": twinkles, "rate": 2.0, "min": 0.35},
            {"kind": "twinkle", "points": glows + win, "rate": 1.3, "min": 0.5},
            {"kind": "twinkle", "points": lamps + leg_pts, "rate": 1.6, "min": 0.55},
            {"kind": "blink", "pattern": "1110", "rate": 0.9, "rects": [[p[0], p[1], 1, 1, "5cf08a", 1.0] for p in wedge_leds]},
            {"kind": "particles", "style": "dust", "count": 14, "rect": [120, 60, 400, 80], "speed": [0, -4], "color": "f6e0b0"},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:400])
