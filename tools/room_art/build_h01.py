"""The Hill (H01): frat row on College Ave at night.

Three big old Hill houses at character scale, all fictional: a red-brick foursquare with brass
letters and its porch light on (GAMMA THETA XI), the party house in sage clapboard with its door
propped open, string lights along the porch, a spray-painted bedsheet banner, lawn chairs and a
flamingo on the porch roof and party light pulsing in every window (XI OMEGA LAMBDA), and a Tudor
house that has mostly gone to bed, pumpkins on the steps (PHI XI PI). Lawns with autumn leaves and
red cups, a plaid couch on the lawn, the sidewalk, the parkway with a big oak and street lamps,
then College Ave itself, old patched asphalt, a hatchback at the kerb. East: the corner and the way
back down to campus. The street in front of the party house is left clear for Tanner's couch."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import sidewalk, LEAVES
from facade import brick_wall, BRICK, SANDSTONE, FRAME, GLOW
from props import lamp_post, atlas_tree, shrub, OUT, LEAF
from lib_farrand import lawn, festoon, light_pool, back_tree, GRASS
from c01_lib import court_sky
from h01_lib import (CLAP_SAGE, CLAP_CREAM, SLATE, PORCH_GREY, DOOR_RED, DOOR_GREEN, PARTY, CUP, ASPHALT, CURB, SHADOW,
                     HOUSE_A, HOUSE_B, HOUSE_C, greek_letters, greek_small, greek_width, clapboard, stucco_tudor,
                     foundation, house_window, front_door, porch_light, house_number, mailbox_wall, shingles, eave,
                     gutter_downspout, porch, porch_couch, rocking_chair, grill, cups_row, cup_flat, bedsheet_banner,
                     lawn_chair, flamingo, pumpkin, concrete_walk, parked_car, lawn_couch, yard_sign, cornhole_boards,
                     recycling_bin, hydrant, street_sign_post, scooter_flat, gutter_leaves, storm_drain, manhole,
                     tar_seams)

ROOM = "H01"
W, H = 960, 540
FB, PD, RISE, HP = 196, 18, 16, 100      # facade base, porch depth, porch deck height, porch roof height
WALK_TOP = 240
LAWN0, WALK0, WALK1, PARK1, CURB1, STREET1 = 230, 326, 352, 368, 372, 508
HA, HB, HC = (20, 300), (336, 640), (676, 896)   # house spans
DOOR_A, DOOR_B, DOOR_C = 160, 485, 786


def side_yard(bg, x0, x1, seed=0):
    """The gap between two houses: dark side yard, a fence gate, bins, a tree behind, sky above."""
    rng = np.random.default_rng(seed)
    bg.rect(x0, 60, x1 - x0, FB + 34 - 60, "#141220")
    # far trees and a neighbour's lit back window
    tree = back_tree(120, cell=5, brightness=0.45, seed=seed)
    th, tw = tree.shape[:2]
    bg.paste(tree, (x0 + x1) // 2 - tw // 2, FB - th + 10)
    bg.rect(x0 + 6, 118, 8, 10, GLOW[2]); bg.rect(x0 + 7, 119, 3, 4, GLOW[3])
    # board fence with a gate
    fy = FB + 2
    for fx in range(x0, x1, 4):
        top = fy - 34 - (2 if (fx // 4) % 2 else 0)
        bg.rect(fx, top, 3, LAWN0 - top, "#3a2a24"); bg.vline(fx, top, LAWN0 - top, "#523a2e"); bg.px(fx + 1, top, "#6a4a36")
    bg.rect(x0, fy - 26, x1 - x0, 3, "#2a1e1c"); bg.rect(x0, fy - 8, x1 - x0, 3, "#2a1e1c")
    bg.rect(x0 + 6, fy - 20, 4, 3, "#a3a9b8")
    # wheelie bins against the fence
    for k, (bx, col) in enumerate([(x0 + 4, ("#1e3e78", "#2a54a0")), (x0 + 18, ("#1e3a2a", "#2e5a3e"))]):
        if bx + 13 > x1:
            continue
        bg.rect(bx, LAWN0 - 22, 13, 22, OUT); bg.rect(bx + 1, LAWN0 - 21, 11, 20, col[0]); bg.vline(bx + 1, LAWN0 - 21, 20, col[1])
        bg.rect(bx - 1, LAWN0 - 24, 15, 3, OUT); bg.hline(bx, LAWN0 - 23, 13, col[1])
    bg.rect(x0, LAWN0 - 2, x1 - x0, 2, C(SHADOW, 0.5))


def house_a(bg):
    """Red-brick foursquare, brass letters, sandstone piers, everything tidy, porch light on."""
    x0, x1 = HA
    brick_wall(bg, x0, 0, x1 - x0, FB, seed=11)
    # hipped roof and eave
    shingles(bg, [(x0 - 10, 26), (x1 + 10, 26), (x1 - 40, -30), (x0 + 40, -30)], SLATE, seed=2)
    eave(bg, x0 - 10, x1 + 10, 24, CLAP_CREAM, depth=5)
    # sandstone quoins and the belt course between floors
    for qx in (x0, x1 - 7):
        for k, qy in enumerate(range(32, FB, 8)):
            qw = 7 if k % 2 == 0 else 5
            ox = qx if qx == x0 else x1 - qw
            bg.rect(ox, qy, qw, 7, SANDSTONE[3]); bg.hline(ox, qy, qw, SANDSTONE[5]); bg.hline(ox, qy + 6, qw, SANDSTONE[1])
    # upstairs: two windows, blinds down, brass letters between
    house_window(bg, x0 + 38, 40, 26, 34, mode="warm", seed=1, blinds=0.7, shutters="#26402e")
    house_window(bg, x1 - 64, 40, 26, 34, mode="dark", seed=2, shutters="#26402e")
    gw = greek_width(HOUSE_A, 2, 6)
    greek_letters(bg, HOUSE_A, DOOR_A - gw // 2, 46, 2, 6, face="#d0a650", hi="#f0d48a", dark="#7a5428")
    gutter_downspout(bg, x1 - 4, 30, FB)
    # downstairs behind the porch
    house_window(bg, x0 + 34, 134, 30, 42, mode="warm", seed=3, blinds=0.45, curtain="#7e3a30")
    house_window(bg, x1 - 70, 134, 30, 42, mode="tv", seed=4, blinds=0.2)
    front_door(bg, DOOR_A, FB, 32, 72, colour=DOOR_GREEN, open_=False)
    lamp_a = porch_light(bg, DOOR_A - 28, 140)
    mailbox_wall(bg, DOOR_A + 24, 150)
    rocking_chair(bg, x0 + 76, FB + 10); rocking_chair(bg, x0 + 92, FB + 10)
    grill(bg, x1 - 46, FB + 12)
    info = porch(bg, x0 + 6, x1 - 6, FB, PD, RISE, HP, DOOR_A, [x0 + 14, x0 + 104, x1 - 104, x1 - 14],
                 skirt="stone", seed=21, column_style="pier")
    return info, lamp_a


def house_b(bg):
    """The party house: sage clapboard, a front gable with the letters, lights everywhere."""
    x0, x1 = HB
    cx = DOOR_B
    # front gable: the roof's two slopes seen from above, the clapboard gable end between the rakes
    eave_y = 62
    shingles(bg, [(x0 - 16, eave_y), (x1 + 16, eave_y), (x1 + 16, -2), (x0 - 16, -2)], SLATE, seed=4)
    clapboard(bg, x0, eave_y, x1 - x0, FB - eave_y, CLAP_SAGE, seed=5)
    gable = Canvas(x1 - x0 + 32, eave_y + 2)
    clapboard(gable, 0, 0, gable.w, gable.h, CLAP_SAGE, seed=6)
    ys, xs = np.mgrid[0:gable.h, 0:gable.w]
    slope = (eave_y + 120) / (cx - x0 + 4)
    inside = ys > eave_y - (cx - x0 + 4 - np.abs(xs + x0 - 16 - cx)) * slope
    region = bg.a[0:gable.h, x0 - 16:x1 + 16]
    region[inside] = gable.a[inside]
    # rake boards along both slopes, shadow under them
    for side in (-1, 1):
        ex = x0 - 8 if side < 0 else x1 + 8
        top_y = eave_y - (cx - x0 + 12) * slope
        for k, c in enumerate([CLAP_CREAM[6], CLAP_CREAM[5], CLAP_CREAM[4], CLAP_CREAM[2], C(SHADOW, 0.5), C(SHADOW, 0.3)]):
            bg.line(ex, eave_y - 4 + k, cx, int(top_y) - 4 + k, c)
    eave(bg, x0 - 10, x0 + 12, eave_y - 2, CLAP_CREAM, depth=4); eave(bg, x1 - 12, x1 + 10, eave_y - 2, CLAP_CREAM, depth=4)
    # fish-scale shingles in the peak of the gable
    for yy in range(0, 22, 4):
        for xx in range(cx - 40 + (yy // 4 % 2) * 3, cx + 40, 6):
            if inside[yy, xx - x0 + 16]:
                bg.ellipse(xx, yy, 6, 5, CLAP_SAGE[3]); bg.hline(xx + 1, yy + 4, 4, CLAP_SAGE[1]); bg.px(xx + 2, yy + 1, CLAP_SAGE[5])
    cols = np.where(inside[22])[0]
    bx0, bx1 = x0 - 16 + cols.min() + 2, x0 - 16 + cols.max() - 2
    bg.rect(bx0, 22, bx1 - bx0, 3, CLAP_CREAM[4]); bg.hline(bx0, 22, bx1 - bx0, CLAP_CREAM[6]); bg.hline(bx0, 25, bx1 - bx0, C(SHADOW, 0.4))
    # upstairs: two party windows, the letters between them
    house_window(bg, x0 + 44, 18, 26, 36, mode="pink", seed=7)
    house_window(bg, x1 - 70, 18, 26, 36, mode="cyan", seed=8)
    gw = greek_width(HOUSE_B, 2, 6)
    greek_letters(bg, HOUSE_B, cx - gw // 2, 26, 2, 6, face="#e8dcc2", hi="#fff6e0", dark="#8e7e6a")
    gutter_downspout(bg, x0 + 3, 62, FB)
    # downstairs: big windows full of party, door propped open
    house_window(bg, x0 + 30, 132, 34, 44, mode="pink", seed=9, curtain="#3a1a3a")
    house_window(bg, x0 + 86, 132, 26, 44, mode="violet", seed=10)
    house_window(bg, x1 - 112, 132, 26, 44, mode="cyan", seed=11)
    house_window(bg, x1 - 64, 132, 34, 44, mode="pink", seed=12, curtain="#3a1a3a")
    party_glow = [GLOW[0], "#c46a8a", "#f0a0b8", "#ffd0dc", "#fff0f4"]
    front_door(bg, cx, FB, 34, 72, colour=DOOR_RED, open_=True, glow=party_glow)
    # a speaker wedged in the left window, cones facing the street
    bg.rect(x0 + 36, 150, 20, 26, OUT); bg.rect(x0 + 37, 151, 18, 24, "#24222f")
    for (sy, r) in [(156, 3), (167, 6)]:
        bg.ellipse(x0 + 46 - r, sy - r + 2, r * 2, r * 2, "#3a384e"); bg.px(x0 + 46, sy + 2, "#8a88a8")
    lamp_b = porch_light(bg, cx - 30, 138)
    house_number(bg, cx + 24, 140, 1130)
    porch_couch(bg, x0 + 132 - 70, FB + 14, w=60)
    cups_row(bg, x0 + 70, FB + 1, n=4, seed=3)
    info = porch(bg, x0 + 6, x1 - 6, FB, PD, RISE, HP, cx, [x0 + 16, x0 + 96, x1 - 96, x1 - 16], seed=22, step_w=44)
    # cups on the railing and the steps
    cups_row(bg, x0 + 30, info["pf"] - 20, n=5, seed=4, spacing=6)
    cups_row(bg, x1 - 80, info["pf"] - 20, n=3, seed=5, spacing=7)
    cups_row(bg, cx - 20, info["pf"] + 8, n=2, seed=6, spacing=30)
    # on the porch roof: two lawn chairs, a flamingo, a cooler-sized speaker
    rb = info["eave"] - 6
    lawn_chair(bg, x1 - 84, rb - 3); lawn_chair(bg, x1 - 62, rb - 5, colour="#c8642a", hi="#e8904a", dark="#8a3e1c")
    flamingo(bg, x0 + 40, rb - 1)
    bg.rect(x1 - 36, rb - 14, 12, 14, OUT); bg.rect(x1 - 35, rb - 13, 10, 12, "#24222f")      # a speaker on the roof too
    bg.ellipse(x1 - 33, rb - 10, 6, 6, "#3a384e"); bg.px(x1 - 31, rb - 8, "#8a88a8")
    # the banner, hung from the upstairs sills down over the porch roof
    bedsheet_banner(bg, cx - 62, 68, 124, 24, [("text", "RUSH WEEK", "#c42e3e"), ("text", "ALL WELCOME", "#2a3a8a")], seed=3)
    return info, lamp_b


def house_c(bg):
    """Tudor house: brick below, stucco and half-timber above, steep gable, mostly asleep."""
    x0, x1 = HC
    cx = DOOR_C
    brick_wall(bg, x0, 60, x1 - x0, FB - 60, seed=13)
    # steep gable roof with the stucco gable end
    shingles(bg, [(x0 - 12, 70), (cx, -120), (x1 + 12, 70), (x1 + 12, 76), (x0 - 12, 76)], SLATE, seed=6)
    ys, xs = np.mgrid[0:70, x0:x1]
    inside = ys > 66 - (66 + 110) * (1 - np.abs(xs - cx) / ((x1 - x0) / 2 + 6))
    tud = Canvas(x1 - x0, 70)
    stucco_tudor(tud, 0, 0, x1 - x0, 70, seed=4)
    # braces in the gable
    for k in range(3):
        bx = (x1 - x0) // 2 - 30 + k * 30
        tud.line(bx, 66, bx + 13, 20, "#3e2a24"); tud.line(bx + 1, 66, bx + 14, 20, "#2e1e1c")
    region = bg.a[0:70, x0:x1]
    region[inside] = tud.a[inside]
    for side in (-1, 1):
        ex = x0 - 8 if side < 0 else x1 + 8
        bg.line(ex, 72, cx, -112, TIMBER_EDGE[0]); bg.line(ex, 73, cx, -111, TIMBER_EDGE[1])
    eave(bg, x0 - 6, x1 + 6, 70, CLAP_CREAM, depth=4)
    house_window(bg, cx - 16, 14, 32, 26, mode="tv", seed=14)
    gutter_downspout(bg, x1 - 4, 76, FB)
    house_window(bg, x0 + 24, 118, 28, 40, mode="dark", seed=15)
    house_window(bg, x1 - 54, 118, 28, 40, mode="dark", seed=16, curtain="#2a3a5a")
    front_door(bg, cx, FB, 30, 72, colour=("#141a2a", "#1e2840", "#2a3a5a", "#3a4e74", "#4e66a0"), open_=False)
    porch_light(bg, cx + 26, 140, on=False)
    # house letters on a hanging board under the porch roof
    lw = len(HOUSE_C) * 10 - 2 + 8
    board_y = 50
    bg.rect(cx - lw // 2, board_y, lw, 14, OUT); bg.rect(cx - lw // 2 + 1, board_y + 1, lw - 2, 12, "#5a3a2e")
    bg.hline(cx - lw // 2 + 1, board_y + 1, lw - 2, "#7a5240")
    greek_small(bg, HOUSE_C, cx - lw // 2 + 4, board_y + 2, "#e6d6b1")
    swing_y = FB + 6
    bg.vline(x0 + 34, info_eave_c := FB + PD - HP + 6, swing_y - info_eave_c - 12, "#4d4b66")
    bg.vline(x0 + 66, info_eave_c, swing_y - info_eave_c - 12, "#4d4b66")
    bg.rect(x0 + 32, swing_y - 14, 38, 4, OUT); bg.rect(x0 + 33, swing_y - 13, 36, 2, "#8c573b")
    bg.rect(x0 + 32, swing_y - 22, 38, 3, OUT); bg.hline(x0 + 33, swing_y - 21, 36, "#ad754d")
    info = porch(bg, x0 + 10, x1 - 10, FB, PD, RISE, HP, cx, [x0 + 18, x1 - 18], seed=23, step_w=36)
    pumpkin(bg, cx - 26, info["pf"] + 9, 12, 9, carved=True); pumpkin(bg, cx + 16, info["pf"] + 17, 10, 8)
    return info


TIMBER_EDGE = ["#3e2a24", "#2e1e1c"]


def east_end(bg):
    """Past the last house: a hedge, the corner, sky down toward campus."""
    x0 = HC[1] + 4
    tree = back_tree(170, cell=5, brightness=0.55, seed=9)
    th, tw = tree.shape[:2]
    bg.paste(tree, x0 + 20 - tw // 2 + 30, LAWN0 - th + 6)
    hedge = shrub(0, 0, W - x0 + 10, 40, seed=31)
    bg.paste(hedge, x0 - 6, LAWN0 - 38)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=17)

    # --- sky: the dusk Flatirons sky from the hub's west end (the Hill is just across Broadway)
    sky, _ = court_sky(W, 240, split=10 ** 6, seed=5)
    bg.a[:240] = sky

    # --- side yards and the corner first, houses over them
    side_yard(bg, 0, HA[0], seed=3)
    side_yard(bg, HA[1], HB[0], seed=1)
    side_yard(bg, HB[1], HC[0], seed=2)
    east_end(bg)
    info_a, lamp_a = house_a(bg)
    info_b, lamp_b = house_b(bg)
    info_c = house_c(bg)
    # string lights: swagged along the party porch eave and from the porch to the parkway oak
    twinkles = []
    eb = info_b["eave"] + 6
    cols = [HB[0] + 16, HB[0] + 96, HB[1] - 96, HB[1] - 16]
    for a, b in zip([HB[0] + 2] + cols, cols + [HB[1] - 2]):
        twinkles += festoon(bg, a, eb, b, eb, sag=9, every=7, seed=a,
                            colours=["#f6cf7a", "#f6cf7a", "#ff8ad0", "#6ad8f0", "#fff0c4"])
    twinkles += festoon(bg, HB[0] + 2, eb - 4, HA[1] - 30, 150, sag=16, every=8, seed=3)

    # --- lawns: house fronts down to the sidewalk
    lawn(bg, 0, LAWN0, W, WALK0 - LAWN0, seed=4, pal=GRASS, tufts=0.9, leaves=0.0)
    bg.rect(0, LAWN0, W, 3, C(SHADOW, 0.45))
    # worn patch where the party spills out, and the front walks
    from lib_farrand import trodden_patch
    trodden_patch(bg, DOOR_B, 262, 80, 16, seed=5, strength=0.6)
    for dx, w in [(DOOR_A, 30), (DOOR_B, 36), (DOOR_C, 28)]:
        concrete_walk(bg, dx - w // 2, info_a["steps_bottom"] - 2, w, WALK0 - info_a["steps_bottom"] + 2, seed=dx)
    # leaves, cups and party debris on the grass
    rng = np.random.default_rng(8)
    for (cx, cy, r, n) in [(318, 300, 90, 160), (120, 280, 70, 50), (760, 290, 80, 60), (900, 300, 60, 60)]:
        for _ in range(n):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
            lx, ly = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.4)
            if LAWN0 + 4 <= ly < WALK0 - 2:
                c = LEAVES[int(rng.integers(len(LEAVES)))]
                bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
    for k, (x, y) in enumerate([(380, 268), (402, 300), (540, 262), (566, 314), (452, 318), (610, 280), (350, 312),
                                (288, 270), (520, 298), (640, 300), (700, 310)]):
        cup_flat(bg, x, y, tipped=(k % 3 != 0), seed=k)
    # a frisbee and a lost flip-flop
    bg.ellipse(674, 286, 10, 4, OUT); bg.ellipse(675, 286, 8, 3, "#e8e4dc")
    bg.rect(140, 316, 6, 3, OUT); bg.rect(141, 316, 4, 2, "#3a8ac8")

    # --- sidewalk, parkway, kerb
    sidewalk(bg, 0, WALK0, W, WALK1 - WALK0, seed=6, slab=20)
    bg.rect(0, WALK0, W, 1, C(SHADOW, 0.35))
    lawn(bg, 0, WALK1, W, PARK1 - WALK1, seed=7, pal=GRASS, tufts=0.6)
    for dx, w in [(DOOR_A, 30), (DOOR_B, 36), (DOOR_C, 28), (930, 40)]:
        concrete_walk(bg, dx - w // 2, WALK1, w, PARK1 - WALK1, seed=dx + 1)
    bg.rect(0, PARK1, W, CURB1 - PARK1, CURB[2]); bg.hline(0, PARK1, W, CURB[3]); bg.hline(0, CURB1 - 1, W, CURB[0])
    # chalk on the sidewalk: the house letters and an arrow to the door
    greek_small(bg, HOUSE_B, DOOR_B - 15, WALK0 + 9, C("#f2a0c8", 0.8))
    for k in range(4):
        bg.px(DOOR_B + 24 + k, WALK0 + 13 - k, "#9ad8e8"); bg.px(DOOR_B + 24 + k, WALK0 + 13 + k, "#9ad8e8")
    bg.hline(DOOR_B + 18, WALK0 + 13, 8, "#9ad8e8")
    scooter_flat(bg, 680, WALK0 + 10)
    for k, x in enumerate([230, 470, 810]):
        cup_flat(bg, x, WALK0 + 6 + (k % 2) * 8, tipped=True, seed=k + 20)

    # --- College Ave
    asph = np.zeros((STREET1 - CURB1, W, 4), np.float32)
    from lib_eng import asphalt_np
    try:
        asph = asphalt_np(W, STREET1 - CURB1, seed=9)
        bg.a[CURB1:STREET1] = asph if asph.shape[-1] == 4 else np.concatenate([asph, np.ones(asph.shape[:2] + (1,), np.float32)], -1)
    except Exception:
        bg.rect(0, CURB1, W, STREET1 - CURB1, ASPHALT[2])
    bg.rect(0, CURB1, W, 6, C(SHADOW, 0.35))
    tar_seams(bg, 0, W, CURB1 + 10, STREET1 - 4, seed=3, n=9)
    # patched trench and a manhole, a storm drain, leaves in the gutter
    bg.rect(240, 452, 140, 14, ASPHALT[3]); bg.hline(240, 452, 140, ASPHALT[1]); bg.hline(240, 465, 140, ASPHALT[1])
    manhole(bg, 700, 470)
    storm_drain(bg, 520, CURB1 + 1)
    gutter_leaves(bg, 0, W, CURB1 + 2, seed=4, density=0.35)
    # a faded SLOW stencil, oil stains under the parking lane, skid marks, a puddle with the party in it
    from lib_eng import big_stencil
    from lib_farrand import puddle
    big_stencil(bg, "SLOW", 150, 470, "#d8d4dc", alpha=0.32, scale=2)
    for ox in (112, 800):
        bg.ellipse(ox - 30, 404, 22, 6, C("#0d0b16", 0.3)); bg.ellipse(ox + 10, 406, 16, 5, C("#0d0b16", 0.3))
        bg.ellipse(ox - 4, 402, 10, 3, C("#3a2a4a", 0.35))
    for k in range(2):
        for t in range(60):
            x = 600 + t * 2
            y = 486 - k * 8 - int(6 * np.sin(t / 19))
            bg.px(x, y, C("#141218", 0.45))
    puddle(bg, 470, 392, 34, 6, seed=3, reflect=("#ff8ad0", "#f6cf7a", "#6ad8f0"), sky=("#24223a", "#33304e", "#4a3a62"))
    # the crosswalk at the east corner, faded
    for k, y in enumerate(range(CURB1 + 10, STREET1 - 6, 14)):
        bg.rect(900, y, 44, 7, C("#c8c4cc", 0.55))
    # far kerb and the other side's sidewalk edge
    bg.rect(0, STREET1, W, 4, CURB[2]); bg.hline(0, STREET1, W, CURB[3])
    sidewalk(bg, 0, STREET1 + 4, W, H - STREET1 - 4, seed=10, slab=20)
    # light: the porch lamps, the street lamps, the party house spilling pink across its lawn
    for (cx, cy, rx, ry, c, a) in [(lamp_a[0], LAWN0 + 6, 80, 22, "#f6cf7a", 0.22), (DOOR_B, LAWN0 + 18, 150, 40, "#f0a0c8", 0.18),
                                   (DOOR_B, 300, 90, 30, "#ffd0e0", 0.12), (170, 372, 90, 30, "#f6cf7a", 0.24),
                                   (622, 372, 90, 30, "#f6cf7a", 0.24)]:
        light_pool(bg, cx, cy, rx, ry, color=c, strength=a)
    # margins
    bg.rect(0, H - 20, W, 20, C(SHADOW, 0.5))
    bg.rect(0, LAWN0, 12, H - LAWN0, C(SHADOW, 0.3))
    bg.save(os.path.join(out, "background.png"))

    # --- props
    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made[:3]
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(2, lawn_couch(100, 40, seed=2))
    save(3, lamp_post(66))
    save(4, lamp_post(66))
    save(5, atlas_tree(150, cell=5, seed=3))
    save(6, parked_car(136, 52, seed=4))
    save(7, street_sign_post(52, 88, names=("COLLEGE AVE",), arrow="CAMPUS >"))
    save(8, yard_sign(40, 36, lines=("NO", "PARKING", "ON LAWN")))
    save(9, hydrant(14, 20))
    save(10, cornhole_boards(74, 18, seed=5))
    save(11, recycling_bin(24, 34, seed=6))
    car2, ax2, ay2 = parked_car(128, 50, body=("#2a1418", "#4a1e22", "#6a2a2a", "#8a3a34", "#a8524a"), seed=7)
    car2.a = car2.a[:, ::-1].copy()                      # parked nose-right, the other way round
    save(12, (car2, car2.w - 1 - ax2, ay2))

    # --- animated layers: party light pulsing in the windows, the string lights, the porch lamps
    layers = []
    win = {  # window glass rects of the party house (x, y, w, h)
        "up_l": (HB[0] + 44, 18, 26, 36), "up_r": (HB[1] - 70, 18, 26, 36),
        "dn_1": (HB[0] + 30, 132, 34, 44), "dn_2": (HB[0] + 86, 132, 26, 44),
        "dn_3": (HB[1] - 112, 132, 26, 44), "dn_4": (HB[1] - 64, 132, 34, 44),
    }
    cycle = [("ff5ab4", "0110"), ("5ad8ff", "1001"), ("a07aff", "0011")]
    for k, (key, (x, y, w, h)) in enumerate(win.items()):
        colour, _ = cycle[k % 3]
        pat = ["1100", "0110", "0011", "1001"][k % 4]
        layers.append({"kind": "blink", "pattern": pat, "rate": 2.2, "rects": [[x, y, w, h, colour, 0.22]]})
    layers += [
        {"kind": "twinkle", "points": twinkles, "rate": 1.8, "min": 0.4},
        {"kind": "twinkle", "points": [[lamp_a[0], lamp_a[1], "fff0c4", 2], [lamp_b[0], lamp_b[1], "fff0c4", 2]], "rate": 0.8, "min": 0.7},
        # the open door's light pulsing with the bass
        {"kind": "blink", "pattern": "10101000", "rate": 4.0, "rects": [[DOOR_B - 17, FB - 72, 34, 72, "ffd0e8", 0.16]]},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0],
        "fauna": [
            {"kind": "moth", "x": lamp_a[0], "y": lamp_a[1] + 14, "range": 6, "speed": 1.2, "rate": 8.0},
            {"kind": "lamp_moth", "x": 170, "y": 312, "range": 8, "speed": 1.1, "rate": 9.0},
            {"kind": "raccoon", "x": 330, "y": 236, "range": 10, "speed": 0.3, "rate": 3.0},
            {"kind": "night_bat", "x": 200, "y": 70, "fly": 14.0, "rate": 8.0},
        ],
        "leaves": [[262, 220, 112, 120], [880, 70, 70, 140]],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
