"""Balcony (M05): Rook's LAST CALL, "one last call".

We stand on Macky's balcony. Back band: the front of the balcony (a velvet-capped parapet with a
brass rail) between two gilt columns, and over it the whole auditorium falling away to the stage:
rows of red seats with a RESERVED card on nearly every one, two tiers of side boxes, tall windows
dark with night, a coffered ceiling, two crystal chandeliers hanging in the void, and far off the
proscenium with VAL's teal frame glowing on the graduation set. The ends of the balcony are house
walls in elevation: on the left the steel service door (SERVICE STAIR, locked until balcony_open),
on the right the padded stage door under a LAST CALL lightbox, roped off while Rook keeps it.
Floor: the front aisle along the parapet is a gold-bordered runner from door to door; behind the
brass cross-aisle rail the balcony floor is wall-to-wall theatre carpet marked with the pale ghosts
of seats that were unbolted and taken away (every future gets a place, every living person loses
one), brass bolt plates still in the carpet; stairwells go down at both bottom corners.
Dawn (background_dawn): house lights up, every card gone, the house windows full of sunrise with
light falling across the void, morning shafts on the balcony carpet from the windows behind us.
States: stage door open with stage light spilling out (rook_resolution), service door open onto
the stair (balcony_open), LAST CALL blinking while Rook is unresolved, cards multiplying in the
house until dawn."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT
from surfaces import light_pool
from lib_macky2 import (HOUSE, HOUSE_DAWN, GILT, VELVET, SEAT, CARD, CARD_RED, LIMESTONE, OAKF, OAK_SUN, CU_GOLD, CU_BLACK,
                        CARPET_B, CARPET_B_DAWN, RUNNER_M, _rng, halo, house_view, stage_far, chandelier, sconce_m,
                        balcony_carpet, balcony_parapet, side_door, lightbox_sign, enamel_sign, brass_rail, velvet_bench,
                        seating_chart, standard_lamp_m, runner_m)

ROOM = "M05"
W, H = 960, 540
BASE = 142
WALK = (20, 142, 920, 374)
COLS = ((150, 168), (790, 808))           # gilt columns framing the view over the parapet
PARAPET_TOP = 116
DOOR_W, DOOR_TOP = 54, 64
DOOR_L, DOOR_R = 75, 840                  # service door (threshold 6) and stage door (threshold 7)
CHANDELIERS = (330, 630)
AISLE = (148, 212)                        # front aisle runner along the parapet
RAIL = (485, 235)
LAMP = (210, 429)
BENCH = (440, 435)
CHART = (370, 264)
ROOK = (575, 350)
STAIRS = (75, 875)                        # stairwells down at the bottom corners
STAIR_TOP = 468
RUNNER_DAWN = ["#3a1a20", "#4e2028", "#662a32", "#7e343a", "#c8a060", "#e8c880"]


def column(bg, x0, x1, dawn):
    """A gilt-capped fluted column standing from the balcony floor to the soffit."""
    pal = HOUSE_DAWN if dawn else HOUSE
    w = x1 - x0
    bg.rect(x0 - 1, 0, w + 2, BASE, OUT)
    bg.rect(x0, 0, w, BASE, pal[4])
    bg.vline(x0, 0, BASE, pal[6]); bg.vline(x0 + 1, 0, BASE, pal[5]); bg.vline(x1 - 1, 0, BASE, pal[2])
    for fx in range(x0 + 4, x1 - 2, 3):
        bg.vline(fx, 24, BASE - 40, pal[3])
    # capital (gilt acanthus band) and base
    bg.rect(x0 - 3, 12, w + 6, 10, OUT)
    bg.rect(x0 - 2, 13, w + 4, 8, GILT[2]); bg.hline(x0 - 2, 13, w + 4, GILT[4]); bg.hline(x0 - 2, 20, w + 4, GILT[1])
    for k in range(x0 - 1, x1 + 2, 3):
        bg.px(k, 16, GILT[4]); bg.px(k + 1, 18, GILT[1])
    bg.rect(x0 - 3, BASE - 14, w + 6, 14, OUT)
    bg.rect(x0 - 2, BASE - 13, w + 4, 12, pal[3]); bg.hline(x0 - 2, BASE - 13, w + 4, GILT[3]); bg.hline(x0 - 2, BASE - 8, w + 4, pal[5])


def soffit(bg, dawn):
    """The underside of the gallery above, a dark band with gilt egg-and-dart across the top of
    the view (it frames the house as a near edge)."""
    pal = HOUSE_DAWN if dawn else HOUSE
    bg.rect(0, 0, W, 9, pal[1])
    bg.hline(0, 9, W, OUT)
    bg.hline(0, 7, W, GILT[2]); bg.hline(0, 8, W, GILT[1])
    for xx in range(0, W, 6):
        bg.rect(xx + 1, 2, 3, 4, pal[3]); bg.px(xx + 2, 3, GILT[3]); bg.px(xx + 4, 4, GILT[1])


def end_wall(bg, x0, x1, dawn, door_cx, kind, seed):
    """A house wall at the end of the balcony with the door that threshold leads to."""
    pal = HOUSE_DAWN if dawn else HOUSE
    rng = _rng(seed)
    bg.rect(x0, 0, x1 - x0, BASE, pal[3])
    for yy in range(10, BASE, 2):
        for xx in range(x0 + (yy // 2) % 3, x1, 7):
            if rng.random() < 0.18:
                bg.px(xx, yy, pal[2] if rng.random() < 0.6 else pal[4])
    # frieze under the soffit: gilt rosettes on a darker band
    bg.rect(x0, 10, x1 - x0, 10, pal[2]); bg.hline(x0, 19, x1 - x0, GILT[2]); bg.hline(x0, 20, x1 - x0, pal[5])
    for xx in range(x0 + 6, x1 - 2, 14):
        bg.ellipse(xx - 2, 12, 5, 5, GILT[2]); bg.px(xx, 14, GILT[4])
    # dado
    dy = BASE - 30
    bg.rect(x0, dy, x1 - x0, 30, OAK_SUN[1] if dawn else OAKF[2])
    bg.hline(x0, dy, x1 - x0, GILT[2] if not dawn else GILT[3]); bg.hline(x0, dy + 1, x1 - x0, OAKF[4])
    for px_ in range(x0 + 4, x1 - 20, 30):
        if abs(px_ + 12 - door_cx) < DOOR_W // 2 + 18:
            continue
        bg.rect(px_, dy + 5, 24, 20, OAKF[1] if not dawn else OAK_SUN[0]); bg.rect(px_ + 1, dy + 6, 22, 18, OAKF[3] if not dawn else OAK_SUN[2])
        bg.hline(px_ + 1, dy + 6, 22, OAKF[4] if not dawn else OAK_SUN[3])
    bg.hline(x0, BASE - 1, x1 - x0, OUT)
    # the door with a moulded architrave and a small cornice
    dx = door_cx - DOOR_W // 2
    h = BASE - DOOR_TOP
    bg.rect(dx - 9, DOOR_TOP - 12, DOOR_W + 18, h + 12, OUT)
    bg.rect(dx - 8, DOOR_TOP - 11, DOOR_W + 16, h + 11, pal[5]); bg.vline(dx - 8, DOOR_TOP - 11, h + 11, pal[7])
    bg.vline(dx + DOOR_W + 7, DOOR_TOP - 11, h + 11, pal[2])
    bg.rect(dx - 12, DOOR_TOP - 16, DOOR_W + 24, 6, OUT)
    bg.rect(dx - 11, DOOR_TOP - 15, DOOR_W + 22, 4, GILT[2] if kind == "stage" else pal[6]); bg.hline(dx - 11, DOOR_TOP - 15, DOOR_W + 22, GILT[4] if kind == "stage" else pal[7])
    side_door(bg, dx, DOOR_TOP, DOOR_W, h, kind=kind, dawn=dawn, open_=False)
    return dx


def rope(bg, dx):
    """A velvet rope on brass hooks across the stage door, a small LAST CALL tag on it."""
    y = 104
    for hx in (dx - 2, dx + DOOR_W + 1):
        bg.rect(hx - 1, y - 2, 3, 4, OUT); bg.px(hx, y - 1, GILT[4]); bg.px(hx, y, GILT[2])
    for xx in range(dx - 1, dx + DOOR_W + 1):
        t = (xx - dx) / DOOR_W
        sag = int(round(9 * np.sin(np.pi * min(1, max(0, t)))))
        bg.px(xx, y + sag - 1, OUT); bg.px(xx, y + sag, VELVET[4]); bg.px(xx, y + sag + 1, VELVET[2]); bg.px(xx, y + sag + 2, OUT)
    cx = dx + DOOR_W // 2
    bg.rect(cx - 9, y + 11, 19, 9, OUT); bg.rect(cx - 8, y + 12, 17, 7, CARD[2]); bg.hline(cx - 7, y + 14, 15, CARD_RED)
    bg.hline(cx - 6, y + 16, 12, CARD[0])


def house_band(bg, dawn):
    """The auditorium seen over the parapet (the persp render), chandeliers, the far stage and,
    at night, a card on almost every seat. Returns (crisp card points, the other seat points)."""
    v, info = house_view(dawn=dawn, seed=7)
    hv = v.reduce(72)
    x0, x1 = COLS[0][1], COLS[1][0]
    stage_far(hv, *info["stage"], dawn=dawn)
    if dawn:
        # sunrise pouring in at the right windows, falling across the void in stepped bands
        ys, xs = np.mgrid[0:BASE, 0:W]
        for (a, b, al) in ((610, 660, 0.10), (520, 600, 0.07), (690, 720, 0.06)):
            m = (xs > a - (ys - 18) * 0.8) & (xs < b - (ys - 18) * 0.8) & (ys > 18) & (ys < BASE)
            hv.fill_mask(m, C("#ffe2a8", al))
    for cx in CHANDELIERS:
        hv.paste(chandelier(lit=1.0), cx - 28, -2)
    crisp, extra = [], []
    rng = _rng(17)
    for (sx, sy, r, h) in info["seats"]:
        x, y = int(round(sx)), int(round(sy)) - 1
        if not (x0 + 2 <= x < x1 - 2 and 22 <= y < PARAPET_TOP - 6):
            continue
        (crisp if h < 0.62 else extra).append((x, y, 2 if y > 84 else 1))
    if not dawn:
        for (x, y, w) in crisp:
            hv.rect(x, y, w, 1, CARD[3] if rng.random() < 0.7 else CARD[2])
    bg.a[0:BASE, x0:x1] = hv.a[0:BASE, x0:x1]
    return crisp, extra


def stairwell(bg, cx, dawn):
    """A carpeted stair going down out of the bottom of the room, brass nosings fading into the
    dark below (flat paint: it starts at the threshold mat)."""
    x0, x1 = cx - 34, cx + 34
    run = RUNNER_DAWN if dawn else RUNNER_M
    bg.rect(x0 - 4, STAIR_TOP - 3, x1 - x0 + 8, H - STAIR_TOP + 3, OUT)
    for i, ty in enumerate(range(STAIR_TOP, H, 8)):
        k = min(1.0, i * 0.14)
        tread = mix(run[3], "#0e0a10", k)
        riser = mix(run[1], "#0a080c", k)
        bg.rect(x0, ty, x1 - x0, 8, riser)
        bg.rect(x0, ty, x1 - x0, 4, tread)
        bg.hline(x0, ty, x1 - x0, mix(GILT[4], "#0e0a10", k))
        bg.hline(x0 + 10, ty + 1, x1 - x0 - 20, mix(run[4], "#0e0a10", k))
    # stair walls either side (plaster dropping away)
    pal = HOUSE_DAWN if dawn else HOUSE
    for (sx, d) in ((x0 - 4, 1), (x1, -1)):
        bg.rect(sx, STAIR_TOP - 3, 4, H - STAIR_TOP + 3, pal[1])
        bg.vline(sx + (3 if d == 1 else 0), STAIR_TOP - 3, H - STAIR_TOP + 3, pal[3])
    bg.hline(x0 - 4, STAIR_TOP - 3, x1 - x0 + 8, GILT[3]); bg.hline(x0 - 4, STAIR_TOP - 2, x1 - x0 + 8, GILT[1])


def aisle_runner(bg, pal):
    """The front-aisle runner from door to door: a red field of small gold-centred lozenges inside
    a patterned border band (diamonds and studs between two gold lines)."""
    x0, x1, y0, y1 = 8, W - 8, AISLE[0], AISLE[1]
    w, h = x1 - x0, y1 - y0
    bg.rect(x0, y0, w, h, pal[0])
    bg.rect(x0 + 1, y0 + 1, w - 2, h - 2, pal[4])
    bg.rect(x0 + 2, y0 + 2, w - 4, h - 4, pal[1])
    bg.rect(x0 + 8, y0 + 8, w - 16, h - 16, pal[4])
    bg.rect(x0 + 9, y0 + 9, w - 18, h - 18, pal[2])
    for xx in range(x0 + 6, x1 - 4, 8):                      # border band motifs
        for yy in (y0 + 5, y1 - 6):
            if (xx // 8) % 2:
                bg.px(xx, yy, pal[4]); bg.px(xx - 1, yy, pal[3]); bg.px(xx + 1, yy, pal[3]); bg.px(xx, yy - 1, pal[3]); bg.px(xx, yy + 1, pal[3])
            else:
                bg.px(xx, yy, pal[5])
    for yy in range(y0 + 9, y1 - 9):
        for xx in (x0 + 5, x1 - 6):
            if yy % 6 == 0:
                bg.px(xx, yy, pal[4])
    for j, yy in enumerate(range(y0 + 17, y1 - 12, 14)):     # field lozenges
        for xx in range(x0 + 22 + (j % 2) * 16, x1 - 16, 32):
            bg.poly([(xx - 5, yy), (xx, yy - 3), (xx + 5, yy), (xx, yy + 3)], pal[3])
            bg.px(xx, yy, pal[5]); bg.px(xx - 1, yy, pal[4]); bg.px(xx + 1, yy, pal[4])
    # worn tread along the middle where people walk door to door
    rng = _rng(29)
    for _ in range(320):
        xx, yy = int(rng.integers(x0 + 10, x1 - 10)), int(rng.integers(y0 + 22, y1 - 22))
        bg.px(xx, yy, C(pal[1], 0.5))


def seat_ghosts(bg, dawn):
    """Where the balcony's own seats were unbolted: paler, unworn rectangles of carpet in curved
    rows with two brass bolt plates each, a thin line of dust along each footprint's back."""
    rng = _rng(23)
    pts = []
    for r, y0 in enumerate(range(282, 506, 40)):
        off = 13 if r % 2 else 0
        for x in range(46 + off, 920, 26):
            if abs(x - 480) < 30:
                continue                                    # centre aisle
            y = int(round(y0 - 0.00011 * (x - 480) ** 2))
            if abs(x - BENCH[0]) < 96 and -40 < y - BENCH[1] < 10:
                continue
            if abs(x - LAMP[0]) < 26 and -16 < y - LAMP[1] < 12:
                continue
            if abs(x - ROOK[0]) < 34 and -50 < y - ROOK[1] < 12:
                continue
            if any(abs(x - s) < 58 for s in STAIRS) and y > 430:
                continue
            if y < 250 or y > 506:
                continue
            if rng.random() < 0.12:
                continue                                    # a few never had a seat (wheelchair bays)
            pts.append((x, y))
    face = CARPET_B_DAWN if dawn else CARPET_B
    for (x, y) in pts:
        bg.rect(x - 8, y - 9, 17, 9, C(mix(face[3], face[4], 0.6), 0.7))        # unworn carpet where the seat stood
        bg.hline(x - 7, y - 10, 15, C(face[0], 0.35))                         # dust line along the old seat back
        bg.hline(x - 7, y - 1, 15, C(face[5], 0.18))
        for bx in (x - 6, x + 5):                                             # brass bolt plates
            bg.rect(bx, y - 3, 2, 2, GILT[3]); bg.px(bx, y - 3, GILT[5]); bg.px(bx + 1, y - 2, GILT[1])
        if rng.random() < 0.3:
            bg.px(x + int(rng.integers(-7, 8)), y - int(rng.integers(3, 9)), C(face[6], 0.6))   # a lost thread of gilt
    return pts


def floor(bg, dawn):
    fl = np.zeros((H, W), bool)
    fl[BASE:, :] = True
    balcony_carpet(bg, fl, pal=CARPET_B_DAWN if dawn else CARPET_B, seed=31)
    # the front aisle runner from door to door along the parapet
    aisle_runner(bg, RUNNER_DAWN if dawn else RUNNER_M)
    bg.hline(0, BASE, W, C("#0a0608", 0.7)); bg.hline(0, BASE + 1, W, C("#0a0608", 0.35))
    seat_ghosts(bg, dawn)
    # the rail's shadow thrown back toward us by the light of the house
    rx0, rx1 = RAIL[0] - 290, RAIL[0] + 290
    bg.rect(rx0, RAIL[1] + 1, rx1 - rx0, 7, C("#0d0b16", 0.22 if not dawn else 0.12))
    for px_ in list(range(rx0 + 2, rx1, 48)) + [rx1 - 3]:
        lean = (px_ - 480) * 0.05
        for k in range(26):
            bg.rect(int(px_ - 1 + lean * k / 26), RAIL[1] + 1 + k, 3, 1, C("#0d0b16", 0.2 if not dawn else 0.1))
    # light falls off away from the house: stepped bands following the curve of the rows
    ys, xs = np.mgrid[0:H, 0:W]
    yeff = ys + 0.00011 * (xs - 480) ** 2 + 6 * ((xs * 7 + ys * 3) % 5 == 0)
    for (y0, a) in ((300, 0.07), (365, 0.07), (430, 0.07), (495, 0.08)):
        bg.fill_mask((yeff > y0) & fl, C("#0d0b16", a if not dawn else a * 0.6))
    for cx in STAIRS:
        stairwell(bg, cx, dawn)
    rng = _rng(37)
    # programmes and a few dropped RESERVED cards on the carpet
    for k in range(7):
        px_, py_ = int(rng.integers(40, 900)), int(rng.integers(250, 500))
        if abs(px_ - ROOK[0]) < 40 and abs(py_ - ROOK[1] + 20) < 40:
            continue
        bg.rect(px_ + 1, py_ + 1, 8, 5, C("#0d0b16", 0.35)); bg.rect(px_, py_, 8, 5, "#e6dcc4"); bg.hline(px_, py_, 8, "#fff6e0")
        bg.hline(px_ + 1, py_ + 2, 6, CARD_RED if k % 2 else CU_GOLD[2])
    if not dawn:
        light_pool(bg, LAMP[0], LAMP[1] + 2, 44, 13, color="#f6cf7a", strength=0.2)
        # the house's glow coming up over the parapet onto the front aisle
        for yy in range(BASE + 2, BASE + 26, 2):
            bg.hline(COLS[0][1], yy, COLS[1][0] - COLS[0][1], C("#f6cf7a", 0.05 * (BASE + 26 - yy) / 24))
        light_pool(bg, DOOR_R, BASE + 26, 40, 14, color="#e84a3a", strength=0.12)      # LAST CALL's red
        light_pool(bg, DOOR_L, BASE + 20, 26, 8, color="#8ab0d0", strength=0.06)
    else:
        light_pool(bg, LAMP[0], LAMP[1] + 2, 40, 11, color="#f6cf7a", strength=0.1)
        # morning through the windows behind us: shafts reaching up the carpet from the bottom edge
        ys, xs = np.mgrid[0:H, 0:W]
        for (a, b, al) in ((150, 250, 0.13), (300, 350, 0.1), (620, 740, 0.12), (790, 830, 0.08)):
            sl = 0.55
            m = (xs > a + (H - ys) * sl) & (xs < b + (H - ys) * sl) & (ys > AISLE[1] + 6) & fl
            bg.fill_mask(m, C("#ffdca0", al))
            m2 = (xs > a + 10 + (H - ys) * sl) & (xs < b - 10 + (H - ys) * sl) & (ys > AISLE[1] + 40) & fl
            bg.fill_mask(m2, C("#fff0c8", al * 0.6))
    # dark margins
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.35))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.35))
    bg.rect(0, WALK[1] + WALK[3], W, H - WALK[1] - WALK[3], C("#0d0b16", 0.45))


def paint(dawn):
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    crisp, extra = house_band(bg, dawn)
    balcony_parapet(bg, COLS[0][1], COLS[1][0], PARAPET_TOP, BASE, dawn=dawn)
    end_wall(bg, 0, COLS[0][0], dawn, DOOR_L, "service", seed=41)
    dxr = end_wall(bg, COLS[1][1], W, dawn, DOOR_R, "stage", seed=42)
    soffit(bg, dawn)
    for (x0, x1) in COLS:
        column(bg, x0, x1, dawn)
    # signs over the doors; sconces either side of them
    enamel_sign(bg, DOOR_L - (text_width("SERVICE STAIR") + 8) // 2, 30, "SERVICE STAIR", fg="#f2ead6", bg="#2a4a6a")
    lightbox_sign(bg, DOOR_R - (text_width("LAST CALL") + 8) // 2, 30, "LAST CALL", lit=False)
    enamel_sign(bg, 884, 78, "STAGE", fg=CU_GOLD[4], bg=CU_BLACK[2])
    for (sx, sy) in ((20, 70), (130, 70), (790 + 38, 52), (942, 52)):
        pass
    for (sx, sy) in ((18, 66), (132, 66), (902, 52)):
        sconce_m(bg, sx, sy, lit=1.0 if dawn else 0.6)
    if not dawn:
        rope(bg, dxr)
    floor(bg, dawn)
    return bg, crisp, extra


def door_overlay(kind, cx, dawn=False):
    """The door swung open: only the opening is replaced, plus a spill of light on the aisle."""
    tmp = Canvas(W, H)
    dx = cx - DOOR_W // 2
    h = BASE - DOOR_TOP
    side_door(tmp, dx, DOOR_TOP, DOOR_W, h, kind=kind, dawn=dawn, open_=True)
    ov = Canvas(DOOR_W + 40, h + 80)
    ox, oy = dx - 20, DOOR_TOP
    ov.a[0:h, 20:20 + DOOR_W] = tmp.a[DOOR_TOP:BASE, dx:dx + DOOR_W]
    ov.a[0:h, 20:20 + DOOR_W, 3] = 1.0
    if kind == "stage":
        # the unhooked rope hanging from the left post
        for yy in range(104 - DOOR_TOP, 104 - DOOR_TOP + 22):
            ov.a[yy, 20 + 7] = C(OUT); ov.a[yy, 20 + 8] = C(VELVET[4]); ov.a[yy, 20 + 9] = C(OUT)
        spill_c, spill_a = "#f6cf7a", 0.16
    else:
        spill_c, spill_a = "#a8c0d8", 0.06
    ys, xs = np.mgrid[0:ov.h, 0:ov.w]
    for (k, a) in ((0, spill_a), (6, spill_a * 0.6)):
        m = (ys >= h) & (ys < h + 50 - k * 3) & (np.abs(xs - (ov.w // 2)) < DOOR_W // 2 - 2 - k + (ys - h) * 0.22)
        col = C(spill_c)
        cur = ov.a[m]
        cur[:, :3] = col[:3]
        cur[:, 3] = np.maximum(cur[:, 3], a)
        ov.a[m] = cur
    return ov, ox, oy


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg, crisp, extra = paint(False)
    bg.save(os.path.join(out, "background.png"))
    bgd, _, _ = paint(True)
    bgd.save(os.path.join(out, "background-dawn.png"))

    props = {}

    def save(index, made, name=None, flag=None, flag_made=None, flag_name=None):
        sprite, ax, ay = made[:3]
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        if flag:
            flag_made[0].save(os.path.join(out, flag_name))
            entry.update({"flag": flag, "flag_texture": res + flag_name})
        props[str(index)] = entry

    save(0, brass_rail(580, 28, cards=True, seed=51), flag="dawn_started", flag_made=brass_rail(580, 28, cards=False, seed=51),
         flag_name="prop-0-dawn.png")
    save(1, velvet_bench(160, 32, seed=52))
    save(2, seating_chart(120, 58, "ONE EXIT"))
    save(3, standard_lamp_m(68))

    overlays = []
    for (kind, cx, flag, name) in (("stage", DOOR_R, "rook_resolution", "door-stage-open.png"),
                                   ("service", DOOR_L, "balcony_open", "door-service-open.png")):
        ov, ox, oy = door_overlay(kind, cx)
        ov.save(os.path.join(out, name))
        overlays.append({"texture": res + name, "x": ox, "y": oy, "flag": flag})

    # LAST CALL lit (blinking) while Rook keeps the doors
    lb = Canvas(90, 40)
    lw = text_width("LAST CALL") + 8
    halo(lb, 45, 16, 30, "#e84a3a", 0.16)
    lightbox_sign(lb, 45 - lw // 2, 10, "LAST CALL", lit=True)
    lb.save(os.path.join(out, "last-call.png"))
    lbx = DOOR_R - lw // 2 - (45 - lw // 2)

    layers = []
    # cards multiplying in the house: four waves appear one after another, then all vanish
    rng = _rng(61)
    order = rng.permutation(len(extra))
    waves = 4
    for k in range(waves):
        pts = [extra[int(i)] for i in order[k::waves]]
        pat = "0" * (k + 1) + "1" * (waves + 2 - k) + "00"
        layers.append({"kind": "blink", "pattern": pat, "rate": 0.9, "flag": "dawn_started", "when": False,
                       "rects": [[x, y, w, 1, "fff8e6"] for (x, y, w) in pts]})
    pick = rng.choice(len(crisp), min(46, len(crisp)), replace=False)
    layers += [
        {"kind": "twinkle", "points": [[crisp[int(i)][0], crisp[int(i)][1], "fffaf0", 1] for i in pick], "rate": 1.3, "min": 0.2,
         "flag": "dawn_started", "when": False},
        {"kind": "blink", "pattern": "1111111011110110", "rate": 3.0, "texture": res + "last-call.png", "x": lbx, "y": 20,
         "flag": "rook_resolution", "when": False},
        {"kind": "twinkle", "points": [[cx + dx, 13 + int(3 * (1 - (dx / 20) ** 2)), "fff4d8", 1] for cx in CHANDELIERS
                                       for dx in range(-20, 21, 5)], "rate": 1.6, "min": 0.45},
        {"kind": "twinkle", "points": [[18, 67, "fde9b6", 1], [132, 67, "fde9b6", 1], [902, 53, "fde9b6", 1],
                                       [LAMP[0], LAMP[1] - 62, "fff0c4", 2]], "rate": 0.9, "min": 0.6},
        {"kind": "particles", "style": "dust", "count": 18, "rect": [170, 20, 620, 100], "speed": [1, 2], "color": "f6e0b0",
         "flag": "dawn_started", "when": False},
        {"kind": "particles", "style": "dust", "count": 30, "rect": [140, 230, 700, 280], "speed": [-2, -1], "color": "ffe2a8",
         "flag": "dawn_started"},
        {"kind": "particles", "style": "dust", "count": 16, "rect": [500, 20, 260, 110], "speed": [1, 2], "color": "fff0c8",
         "flag": "dawn_started"},
    ]
    manifest = {
        "background": res + "background.png",
        "background_dawn": res + "background-dawn.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": overlays,
        "fauna": [
            {"kind": "lamp_moth", "x": LAMP[0], "y": LAMP[1] - 66, "range": 6, "speed": 2.0, "rate": 9.0},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
