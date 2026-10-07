"""Graduation morning (G01 Folsom Field) and its battle backdrop.

Everything paints at 1:1 game pixels against a 52px character, in full morning sun (the world tint
after dawn_started is (0.90, 0.88, 0.87), nearly neutral, so colours are painted as they should read).
Sun low in the east-south-east, behind the viewer's left shoulder: lit faces look left/front, ground
shadows run up and to the right.

Sections:
  palettes ....... SKY_MORN, TURF_SUN, TURF_SHADE, LINE, CHAIR_W, ALUM, RISER, CLOTHES, SKIN, HAIR,
                   CU gold/black (from lib_macky2), ROBE, HOODS, FLOWERS, BALLOON
  sky & stadium .. morning_sky, stands (crowd rows, aisles, concourse, rim), rim_parapet,
                   press_box, scoreboard, light_tower, field_wall, stand_banner, tunnel
  stage .......... stage_set (deck, skirt, fan bunting, stairs, backdrop, COMMENCEMENT banner,
                   faculty), seated_faculty, draped_chair, flower_pot, flower_urn, pennant
  floor .......... turf, yard_lines, runner, tile_path, confetti_flat, program_flat, cap_flat
  props .......... white_chair_row, podium_thrust, field_lamp, balloon_bunch
  small things ... mortarboard (tossed caps for the animated layers)
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, ground_shadow
from lib_macky2 import CU_GOLD, CU_BLACK, _rng
from lib_macky import stencil_text

INK = "#171a2b"

# --- palettes ---------------------------------------------------------------------------------
SKY_MORN = ["#5c88c8", "#6690cc", "#7098d0", "#7ca2d4", "#88aad6", "#96b2d8", "#a4bad8", "#b2c0d6",
            "#c0c6d4", "#cecad0", "#dacecc", "#e4d4ca"]
TURF_SUN = ["#1c3418", "#26441e", "#305424", "#3c662a", "#467430", "#548438", "#669846", "#80ac54"]
TURF_SHADE = ["#16262a", "#1c3030", "#223c34", "#2a4a3a", "#305440", "#3a6048", "#4a7058", "#5e8068"]
LINE = ["#a8b0a4", "#d4dacc", "#eef2e6", "#ffffff"]
CHAIR_W = ["#5e5e70", "#8a8a9c", "#b0b0be", "#cfd0d8", "#e6e6ea", "#f6f6f6"]
ALUM = ["#5a5e6a", "#7c808c", "#a0a6b0", "#c4c8d0", "#e0e4e8"]
RISER = ["#4a4650", "#5e5862", "#726a72", "#887e84", "#a09496", "#b8acaa"]      # stand concrete in sun
STEEL = ["#2a2c36", "#3e4250", "#5a6070", "#7a8292", "#a0a8b6", "#c8ced8"]
GOLD = CU_GOLD
BLACK = CU_BLACK
SKIN = ["#f2cca8", "#e0b08a", "#c89068", "#a87050", "#845238", "#5e3a28"]
HAIR = ["#1a1414", "#2e2018", "#4a3020", "#6a4a2a", "#a07a44", "#c8a868", "#d8d4cc", "#8a8a90"]
CLOTHES = ["#1a1a22", "#24242e", "#e8e4dc", "#f4f2ec", "#cfb87c", "#d8b45a", "#b8913a",       # black, white, CU gold
           "#3a5a9a", "#5a7ab8", "#2a3a6a", "#9a3a3a", "#c85a5a", "#e88aa0", "#f0b8c0",
           "#4a8a5a", "#7ab07a", "#8a6ab0", "#c0a0d8", "#e8a050", "#7ac0c8", "#6a6a72", "#a8a8b0"]
CLOTHES_W = [6, 4, 4, 3, 6, 4, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 2, 2]
ROBE = ["#0e0c14", "#18161e", "#24222c", "#34323e", "#4a4856"]
HOODS = ["#3a6ab0", "#d6bc80", "#a83030", "#e8e0d0", "#6a3a8a", "#2a7a5a", "#e07a3a", "#7ab0d8"]
FLOWERS = {"gold": ["#8a5a10", "#c8901c", "#f0c030", "#fbe27a"],
           "white": ["#a8a8b0", "#d0d0d4", "#eeeef0", "#ffffff"],
           "purple": ["#4a2a6a", "#6a3a8a", "#9a6ab8", "#c8a0e0"],
           "red": ["#6a1a1a", "#a02828", "#d04040", "#f07a6a"]}
LEAFG = ["#16261a", "#22381e", "#2e4a26", "#3e602e", "#56783a"]
CONFETTI_PILE = ["#f6cf7a", "#f8f4ea", "#e88aa0", "#7ac0c8", "#d8b45a"]
CONFETTI = ["#f6cf7a", "#ffffff", "#e88aa0", "#7ac0c8", "#d8b45a", "#c0a0d8", "#1a1a22"]
TERRACOTTA = ["#4a2418", "#7a3a24", "#a85a36", "#c87a4a"]


def _w(rng, items, weights):
    p = np.array(weights, float)
    return items[int(rng.choice(len(items), p=p / p.sum()))]


def outlined(cv, colour=INK):
    cv.outline_outside(colour)
    return cv


# ============================================================================================
# sky
# ============================================================================================
def morning_sky(cv, x, y, w, h, seed=0, pal=SKY_MORN):
    """Clear morning sky: deep blue overhead easing to a warm pale haze at the mountains, stepped
    bands with ragged joins (no gradient)."""
    from lib_macky2 import band_ramp
    band_ramp(cv, x, y, w, h, pal, seed=seed, curve=0.85)


# ============================================================================================
# stadium
# ============================================================================================
def stands(cv, rim, wall_y, x0=0, x1=960, pitch=5, bow=10, aisles=(), concourse=None, seed=0, mask=None,
           empty=0.08, standing=0.1, signs=0.012, zones=(), haze=("#cac2c6", 0.16)):
    """Rows of aluminium bench seating packed with families, seen from the field.

    rim(x) -> top y of the stands at column x; rows run from wall_y up to the rim at `pitch` px,
    sagging `bow` px in the middle so the bowl curves up to both sides. Each person is a 3x4 cluster
    (hair, face, two rows of shirt) sitting on the bench line; some stand and wave, some hold a sign.
    aisles: x positions of stair aisles (5px). concourse: (row index, portal xs) for a walkway band.
    Returns {"flash": [(x, y)], "rows": [...]} for camera-flash twinkles."""
    rng = _rng(seed)
    W = cv.w

    def row_y(k, x):
        t = (x - 480) / 480.0
        return int(round(wall_y - 1 - k * pitch - bow * t * t))

    flash = []
    nrows = 60
    aisle_set = set()
    for ax in aisles:
        for d in range(-2, 3):
            aisle_set.add(ax + d)
    conc_row = concourse[0] if concourse else None
    # 1. risers: tread (lit) and face (shade) for every row, under everything
    for x in range(max(0, x0), min(W, x1)):
        top = rim(x)
        for k in range(nrows):
            y = row_y(k, x)
            if y - pitch < top - 1:
                break
            if mask is not None and not mask[max(0, min(cv.h - 1, y)), x]:
                continue
            cv.vline(x, y - pitch + 1, pitch - 1, RISER[1])
            cv.px(x, y - pitch + 1, RISER[3])
            cv.px(x, y, ALUM[2])
        # fill any sliver between the last row and the rim
        yl = row_y(0, x)
        while yl - pitch >= top - 1:
            yl -= pitch
        if yl > top:
            cv.vline(x, top, yl - top + 1, RISER[3])
    # 2. people, seat by seat
    for k in range(nrows):
        conc = conc_row is not None and k == conc_row
        family = None
        fam_left = 0
        x = x0 + int(rng.integers(0, 3))
        while x < x1 - 3:
            y = row_y(k, x + 1)
            top = rim(x + 1)
            if y - pitch < top - 1 or y - 4 < 0:
                x += 4
                continue
            if any((x + d) in aisle_set for d in range(4)):
                x += 4
                continue
            if mask is not None and not mask[min(cv.h - 1, max(0, y)), min(W - 1, x + 1)]:
                x += 4
                continue
            if conc:
                x += 4
                continue
            if fam_left <= 0:
                family = (_w(rng, CLOTHES, CLOTHES_W), int(rng.integers(0, len(SKIN))), rng.random())
                fam_left = int(rng.integers(2, 7))
                if rng.random() < 0.07:          # an empty run of seats
                    for _ in range(int(rng.integers(1, 4))):
                        cv.hline(x, y - 1, 3, ALUM[2]); cv.hline(x, y - 2, 3, ALUM[1])
                        x += 4
                    continue
            fam_left -= 1
            if rng.random() < empty:
                cv.hline(x, y - 1, 3, ALUM[2]); cv.hline(x, y - 2, 3, ALUM[1])
                x += 4
                continue
            shirt = family[0] if rng.random() < 0.45 else _w(rng, CLOTHES, CLOTHES_W)
            for (zx0, zx1, zk0, zk1, zcols, zw, zp) in zones:
                if zx0 <= x < zx1 and zk0 <= k < zk1 and rng.random() < zp:
                    shirt = _w(rng, zcols, zw)
            sk = SKIN[min(len(SKIN) - 1, max(0, family[1] + int(rng.integers(-1, 2))))]
            hair = HAIR[int(rng.integers(0, len(HAIR)))]
            hat = rng.random()
            if hat < 0.12:
                hair = GOLD[3]                   # CU gold cap
            elif hat < 0.18:
                hair = "#f0e6c8"                 # sun hat
            elif hat < 0.22:
                hair = BLACK[1]
            up = 1 if rng.random() < standing else 0
            yy = y - up
            cv.hline(x, yy - 2, 3, shirt); cv.hline(x, yy - 1, 3, shade(shirt, -0.18))
            cv.hline(x + 1 - (1 if rng.random() < 0.5 else 0), yy - 3, 2, sk)
            hx = x + (1 if rng.random() < 0.6 else 0)
            cv.hline(hx, yy - 4, 2 if hat < 0.22 else 1 + int(rng.random() < 0.6), hair)
            if up and rng.random() < 0.6:        # arm up, waving
                ax = x - 1 if rng.random() < 0.5 else x + 3
                cv.px(ax, yy - 3, sk); cv.px(ax, yy - 4, sk)
            if rng.random() < signs and y - 9 > top:
                sc = ["#f4f2ec", "#f0d060", "#f4f2ec", "#e88aa0"][int(rng.integers(0, 4))]
                cv.rect(x - 1, yy - 8, 6, 4, sc); cv.hline(x - 1, yy - 4, 6, shade(sc, -0.3))
                cv.hline(x, yy - 7, 4, ["#1a1a22", "#a02828", "#2a3a6a"][int(rng.integers(0, 3))])
                cv.hline(x + 1, yy - 6, 2, "#1a1a22")
            if rng.random() < 0.012:
                flash.append((x + 1, yy - 2))
            x += 4
    # 3. stair aisles: concrete steps with a centre handrail
    for ax in aisles:
        for x in range(ax - 2, ax + 3):
            if not (0 <= x < W):
                continue
            top = rim(x)
            for k in range(nrows):
                y = row_y(k, x)
                if y - pitch < top - 1:
                    break
                if mask is not None and not mask[max(0, min(cv.h - 1, y)), x]:
                    continue
                cv.vline(x, y - pitch + 1, pitch, RISER[3])
                cv.px(x, y - pitch + 1, RISER[5]); cv.px(x, y - pitch + 3, RISER[4])
                cv.px(x, y, RISER[1])
        for k in range(nrows):
            y = row_y(k, ax)
            if y - pitch < rim(ax) - 1:
                break
            if mask is not None and not mask[max(0, min(cv.h - 1, y)), ax]:
                continue
            cv.vline(ax, y - pitch + 1, pitch, "#d8d0a0")
            if k % 4 == 0:
                cv.px(ax, y - pitch + 1, GOLD[4])
    # 4. the concourse: a walkway band crossing the section with portals into the stadium
    if concourse:
        k, portals = concourse
        for x in range(max(0, x0), min(W, x1)):
            y = row_y(k, x)
            if y - pitch < rim(x) - 1:
                continue
            if mask is not None and not mask[max(0, min(cv.h - 1, y)), x]:
                continue
            cv.vline(x, y - pitch + 1, pitch, RISER[1])
            cv.px(x, y - pitch + 1, STEEL[4]); cv.px(x, y - pitch + 2, STEEL[2])
            cv.px(x, y, RISER[4])
        for px_ in portals:
            y = row_y(k, px_)
            # a dark tunnel mouth under the rows above (vomitory), people coming out of it
            cv.rect(px_ - 7, y - 4 - pitch * 2, 14, 4 + pitch * 2, "#1a161e")
            cv.rect(px_ - 6, y - 3 - pitch * 2, 12, 2 + pitch * 2, "#2a2430")
            cv.hline(px_ - 8, y - 5 - pitch * 2, 16, RISER[5]); cv.vline(px_ - 8, y - 4 - pitch * 2, 4 + pitch * 2, RISER[4])
            cv.vline(px_ + 7, y - 4 - pitch * 2, 4 + pitch * 2, RISER[1])
            cv.rect(px_ - 3, y - 6 - pitch * 2, 6, 1, GOLD[3])
            for k2, dx in enumerate((-4, 1)):
                c = _w(rng, CLOTHES, CLOTHES_W)
                cv.rect(px_ + dx, y - 3, 2, 3, c); cv.px(px_ + dx, y - 4, SKIN[int(rng.integers(0, 5))])
    # distance: a thin warm haze over the whole bowl so it sits behind the field
    if haze:
        m = np.zeros((cv.h, cv.w), bool)
        for x in range(max(0, x0), min(W, x1)):
            m[max(0, rim(x) - 4):wall_y + 1, x] = True
        cv.fill_mask(m, C(haze[0], haze[1]))
    return {"flash": flash, "row_y": row_y}


def rim_parapet(cv, x0, x1, y, pal=RISER, rail=True):
    """The concrete lip along the top of a stand: lit coping, shadowed face, a steel rail."""
    cv.rect(x0, y, x1 - x0, 4, pal[3]); cv.hline(x0, y, x1 - x0, pal[5]); cv.hline(x0, y + 3, x1 - x0, pal[1])
    for x in range(x0 + 3, x1, 12):
        cv.vline(x, y + 1, 2, pal[2])
    if rail:
        cv.hline(x0, y - 3, x1 - x0, STEEL[4])
        for x in range(x0 + 2, x1, 8):
            cv.vline(x, y - 3, 3, STEEL[2])


def press_box(cv, x0, x1, top, base, label="FOLSOM FIELD"):
    """The west-side press box and club level on top of the stands: a pale concrete block with a
    long band of tinted glass reflecting the sky, a fascia with the stadium name, roof units."""
    w = x1 - x0
    # roof plant and antennas
    cv.rect(x0 + 18, top - 6, 30, 6, STEEL[3]); cv.hline(x0 + 18, top - 6, 30, STEEL[5]); cv.vline(x0 + 47, top - 6, 6, STEEL[1])
    for gx in range(x0 + 20, x0 + 46, 4):
        cv.vline(gx, top - 4, 3, STEEL[2])
    cv.rect(x0 + w - 70, top - 4, 22, 4, STEEL[3]); cv.hline(x0 + w - 70, top - 4, 22, STEEL[4])
    cv.vline(x0 + w - 30, top - 14, 14, STEEL[2]); cv.hline(x0 + w - 33, top - 12, 7, STEEL[2]); cv.px(x0 + w - 30, top - 15, "#e04434")
    # body
    cv.rect(x0, top, w, base - top, RISER[4])
    cv.hline(x0, top, w, RISER[5]); cv.hline(x0, top + 1, w, "#e8dccc")
    cv.vline(x0, top, base - top, "#e8dccc"); cv.vline(x1 - 1, top, base - top, RISER[2])
    # fascia with the name
    fy = top + 3
    cv.rect(x0 + 2, fy, w - 4, 10, BLACK[1]); cv.hline(x0 + 2, fy, w - 4, BLACK[3]); cv.hline(x0 + 2, fy + 9, w - 4, GOLD[2])
    tw = text_width(label)
    text(cv, label, x0 + (w - tw) // 2, fy - 1, GOLD[3])
    for lx in (x0 + (w - tw) // 2 - 14, x0 + (w + tw) // 2 + 6):
        cv.rect(lx, fy + 2, 8, 6, GOLD[3]); cv.rect(lx + 2, fy + 4, 4, 2, BLACK[1])
    # glass band: sky reflected in it, mullions, a few people at the glass
    gy, gh = fy + 12, base - fy - 16
    cv.rect(x0 + 2, gy, w - 4, gh, "#3a5a80")
    cv.rect(x0 + 2, gy, w - 4, max(1, gh // 3), "#6a8ab0")
    cv.hline(x0 + 2, gy + gh // 3, w - 4, "#8aa8c8")
    rng = _rng(77)
    for k, gx in enumerate(range(x0 + 2, x1 - 2, 9)):
        cv.vline(gx, gy, gh, STEEL[1])
        if rng.random() < 0.35:            # glint running across the pane
            cv.line(gx + 2, gy + gh - 2, gx + 6, gy + 1, "#c8dcf0")
        if rng.random() < 0.3:             # someone at the window
            px_ = gx + 3 + int(rng.integers(0, 3))
            cv.rect(px_, gy + gh - 4, 2, 4, _w(rng, CLOTHES, CLOTHES_W)); cv.px(px_, gy + gh - 5, SKIN[int(rng.integers(0, 5))])
    cv.hline(x0 + 2, gy + gh, w - 4, RISER[1])
    cv.rect(x0, base - 3, w, 3, RISER[3]); cv.hline(x0, base - 3, w, RISER[5])


def scoreboard(cv, x, y, w, h, legs_to=None):
    """The video board: steel frame, CU header, CONGRATULATIONS over a big GRADUATES, gold trim,
    lamp-lit LED letters on a dark screen. Returns the screen rect for the animated border."""
    if legs_to is not None:
        for lx in (x + 22, x + w - 26):
            cv.rect(lx, y + h, 5, legs_to - y - h, STEEL[2]); cv.vline(lx, y + h, legs_to - y - h, STEEL[4])
            for ly in range(y + h + 3, legs_to, 6):
                cv.line(lx, ly, lx + 4, ly + 5, STEEL[1])
    cv.rect(x - 1, y - 1, w + 2, h + 2, INK)
    cv.rect(x, y, w, h, STEEL[1]); cv.hline(x, y, w, STEEL[4]); cv.vline(x, y, h, STEEL[3])
    # header
    cv.rect(x + 3, y + 3, w - 6, 10, BLACK[1]); cv.hline(x + 3, y + 12, w - 6, GOLD[2])
    lab = "CU BOULDER"
    tw = text_width(lab)
    text(cv, lab, x + (w - tw) // 2, y + 2, GOLD[3])
    for bx in (x + 6, x + w - 14):
        cv.rect(bx, y + 5, 8, 6, GOLD[3]); cv.rect(bx + 2, y + 7, 4, 2, BLACK[1])
    # screen
    sx, sy, sw, sh = x + 3, y + 15, w - 6, h - 22
    cv.rect(sx, sy, sw, sh, "#10141c")
    for yy in range(sy, sy + sh, 2):               # LED scan rows
        cv.hline(sx, yy, sw, "#141a24")
    s1 = "CONGRATULATIONS"
    t1 = text_width(s1)
    text(cv, s1, sx + (sw - t1) // 2, sy + 3, GOLD[4])
    s2 = "GRADUATES"
    t2 = text_width(s2) * 2
    stencil_text(cv, s2, sx + (sw - t2) // 2 + 1, sy + 13, "#a08040", scale=2)
    stencil_text(cv, s2, sx + (sw - t2) // 2, sy + 12, "#fff6dc", scale=2)
    # little stars either side of GRADUATES
    for (stx, sty) in ((sx + 6, sy + 18), (sx + sw - 8, sy + 18)):
        cv.px(stx, sty, GOLD[4]); cv.px(stx - 1, sty, GOLD[3]); cv.px(stx + 1, sty, GOLD[3]); cv.px(stx, sty - 1, GOLD[3]); cv.px(stx, sty + 1, GOLD[3])
    # gold trim and ribbon board below
    cv.rect(x + 3, y + h - 6, w - 6, 4, GOLD[2]); cv.hline(x + 3, y + h - 6, w - 6, GOLD[4])
    for bx in range(x + 6, x + w - 6, 10):
        cv.rect(bx, y + h - 5, 5, 2, BLACK[1])
    return (sx, sy, sw, sh)


def light_tower(cv, cx, top, base, lamps=(5, 3)):
    """A stadium light standard: lattice mast from the rim and a bank of (unlit) lamps on top."""
    # mast
    cv.rect(cx - 2, top + 14, 5, base - top - 14, STEEL[1])
    cv.vline(cx - 2, top + 14, base - top - 14, STEEL[4]); cv.vline(cx + 2, top + 14, base - top - 14, STEEL[2])
    for y in range(top + 16, base, 5):
        cv.line(cx - 1, y, cx + 1, y + 4, STEEL[3])
    # bank
    nx, ny = lamps
    bw, bh = nx * 5 + 3, ny * 5 + 3
    bx, by = cx - bw // 2, top
    cv.rect(bx - 1, by - 1, bw + 2, bh + 2, INK)
    cv.rect(bx, by, bw, bh, STEEL[2]); cv.hline(bx, by, bw, STEEL[4])
    for i in range(nx):
        for j in range(ny):
            lx, ly = bx + 2 + i * 5, by + 2 + j * 5
            cv.rect(lx, ly, 4, 4, STEEL[0]); cv.rect(lx, ly, 3, 3, "#c8ccd4"); cv.px(lx, ly, "#ffffff")
            cv.px(lx + 2, ly + 2, "#8a92a0")
    cv.rect(bx + 2, by + bh, bw - 4, 2, STEEL[1])


def field_wall(cv, x0, x1, top, base, gaps=()):
    """The padded wall between the field and the stands: concrete coping, black pad with a gold
    stripe, its shadow on the turf below."""
    for x in range(x0, x1):
        if any(a <= x < b for (a, b) in gaps):
            continue
        cv.vline(x, top, 2, RISER[5])
        cv.vline(x, top + 2, base - top - 2, BLACK[1])
        cv.px(x, top + 2, BLACK[3])
        cv.px(x, top + 5, GOLD[2]); cv.px(x, top + 6, GOLD[3])
        cv.px(x, base - 1, BLACK[0])
        if x % 24 == 0:
            cv.vline(x, top + 3, base - top - 4, BLACK[0])


def stand_banner(cv, x, y, label, bg=None, fg=None, edge=None, pad=5, h=12, tie=True):
    """A cloth banner hung over the front of the stands (sewn hem, grommets, a little sag)."""
    bg = bg or GOLD[3]
    fg = fg or BLACK[1]
    edge = edge or shade(bg, -0.3)
    w = text_width(label) + pad * 2
    cv.rect(x - 1, y - 1, w + 2, h + 2, INK)
    cv.rect(x, y, w, h, bg)
    cv.hline(x, y, w, shade(bg, 0.18)); cv.hline(x, y + h - 1, w, edge)
    cv.hline(x, y + 1, w, shade(bg, 0.08))
    # a fold catching the light (under the lettering)
    cv.vline(x + w // 3, y + 1, h - 2, shade(bg, -0.08))
    text(cv, label, x + pad, y + (h - 7) // 2 - 2, fg)
    if tie:
        for gx in (x + 1, x + w - 2):
            cv.px(gx, y + 1, "#c8ccd4")
            cv.vline(gx, y - 3, 3, "#e8e4dc")
    return w


def tunnel(cv, cx, base, w=34, h=22):
    """The players' tunnel into the stands: a dark arch with a gold CU plate over it."""
    x0 = cx - w // 2
    cv.rect(x0 - 3, base - h - 3, w + 6, h + 3, RISER[4]); cv.hline(x0 - 3, base - h - 3, w + 6, RISER[5])
    cv.rect(x0, base - h, w, h, "#120e16")
    cv.rect(x0 + 3, base - h + 3, w - 6, h - 3, "#1e1822")
    cv.rect(x0 + 6, base - h + 7, w - 12, h - 7, "#2a2430")
    cv.ellipse(x0, base - h - 4, w, 10, RISER[4])
    cv.ellipse(x0 + 2, base - h - 2, w - 4, 8, "#120e16")
    cv.rect(cx - 9, base - h - 14, 18, 11, INK)
    cv.rect(cx - 8, base - h - 13, 16, 9, GOLD[3]); text(cv, "CU", cx - 6, base - h - 14, BLACK[1])
    # gates folded back
    for gx in (x0 + 1, x0 + w - 3):
        for yy in range(base - h + 2, base, 3):
            cv.hline(gx, yy, 2, STEEL[3])


# ============================================================================================
# stage
# ============================================================================================
def flower_pot(cv, cx, base, kind="gold", w=12, h=9, pot=TERRACOTTA, seed=0):
    """A potted mum / hydrangea: a dome of little flower heads over leaves, in a pot."""
    rng = _rng(seed)
    fl = FLOWERS[kind]
    s = Canvas(w + 4, h + 10)
    sx, sb = (w + 4) // 2, h + 8                 # centre and base inside the sprite
    pw = max(6, w - 4)
    s.rect(sx - pw // 2, sb - 5, pw, 5, pot[2]); s.hline(sx - pw // 2, sb - 5, pw, pot[3]); s.vline(sx + pw // 2 - 1, sb - 5, 5, pot[1])
    s.hline(sx - pw // 2 - 1, sb - 6, pw + 2, pot[3])
    rim = sb - 6
    dome = Canvas(w + 4, h + 10)
    dome.ellipse(sx - w // 2, rim - h, w, h * 2, LEAFG[2])
    dome.a[rim:] = 0
    s.paste(dome, 0, 0)
    for _ in range(int(w * h * 0.4)):
        a = rng.uniform(np.pi, 2 * np.pi)
        d = np.sqrt(rng.uniform(0, 1))
        px_ = int(round(sx + np.cos(a) * d * (w / 2 - 1)))
        py_ = int(round(rim - 1 + np.sin(a) * d * (h - 1)))
        lit = px_ < sx + 1 and py_ < rim - h // 3
        c = fl[3] if lit and rng.random() < 0.6 else fl[2] if rng.random() < 0.7 else fl[1]
        s.px(px_, py_, c)
        if rng.random() < 0.3:
            s.px(px_ + 1, py_, fl[1])
    for _ in range(4):
        s.px(sx + int(rng.integers(-w // 2 + 1, w // 2)), rim - 1, LEAFG[3])
    s.outline_outside(INK)
    cv.paste(s, cx - sx, base - sb)


def flower_urn(cv, cx, base, h=30, seed=0):
    """A tall pedestal urn spilling gold and white flowers with trailing ivy (stage corners)."""
    rng = _rng(seed)
    # pedestal
    cv.rect(cx - 5, base - 12, 11, 12, INK)
    cv.rect(cx - 4, base - 11, 9, 11, "#d8d0c0"); cv.vline(cx - 4, base - 11, 11, "#f0eadc"); cv.vline(cx + 4, base - 11, 11, "#a8a090")
    cv.rect(cx - 6, base - 2, 13, 2, "#a8a090"); cv.hline(cx - 6, base - 2, 13, "#c8c0b0")
    # bowl
    cv.rect(cx - 8, base - 17, 17, 6, INK)
    cv.rect(cx - 7, base - 16, 15, 4, "#e0d8c8"); cv.hline(cx - 7, base - 16, 15, "#f6f0e2"); cv.hline(cx - 6, base - 12, 13, "#a8a090")
    # blooms
    top = base - h
    cv.ellipse(cx - 12, top - 1, 25, 22, INK)
    cv.ellipse(cx - 11, top, 23, 20, LEAFG[2])
    for _ in range(90):
        a = rng.uniform(0, 2 * np.pi)
        d = np.sqrt(rng.uniform(0, 1))
        px_ = int(cx + np.cos(a) * d * 10)
        py_ = int(top + 9 + np.sin(a) * d * 8)
        if py_ > base - 16:
            continue
        kind = "gold" if rng.random() < 0.55 else "white"
        fl = FLOWERS[kind]
        cv.px(px_, py_, fl[3] if (px_ < cx and rng.random() < 0.6) else fl[2])
        if rng.random() < 0.25:
            cv.px(px_, py_ + 1, fl[1])
    # trailing ivy over the rim
    for k in range(4):
        tx = cx - 8 + k * 5
        for j in range(int(rng.integers(3, 7))):
            cv.px(tx + (j % 2), base - 15 + j, LEAFG[3] if j % 2 else LEAFG[4])


def fan_bunting(cv, cx, top, r=12):
    """A pleated half-round fan swag: black, gold and white bands, a rosette at the top."""
    s = Canvas(r * 2 + 5, r + 5)
    ox, oy = r + 2, 1
    for rr, c in [(r, BLACK[1]), (r - 3, GOLD[3]), (r - 6, "#f4f2ec"), (r - 8, GOLD[3])]:
        s.ellipse(ox - rr, oy - rr, rr * 2 + 1, rr * 2 + 1, c)
    s.a[:oy] = 0
    for k in range(1, 8):                     # pleats radiating from the rosette
        a = np.pi * k / 8
        s.line(ox, oy, int(round(ox + np.cos(a) * r)), int(round(oy + np.sin(a) * r)), C("#0d0b16", 0.3))
    s.outline_outside(INK)
    s.a[:oy] = 0
    s.rect(ox - 2, oy - 1, 5, 3, GOLD[4]); s.px(ox, oy, GOLD[1])
    cv.paste(s, cx - ox, top - oy)


def seated_faculty(hood, skin, hair, seed=0, clap=False, tam=True):
    """A faculty member in academic dress seated facing the audience, about 26px tall: black
    gown with velvet facings in the colour of their hood, tam with a gold tassel, hands in the lap."""
    rng = _rng(seed)
    cv = Canvas(16, 30)
    cx, foot = 8, 28
    robe = ROBE
    # chair back peeking either side of the shoulders
    cv.rect(cx - 6, foot - 21, 13, 10, "#2a2632"); cv.hline(cx - 6, foot - 21, 13, "#4a4652")
    # gown body: shoulders to hem, knees forward
    cv.poly([(cx - 5, foot - 18), (cx + 5, foot - 18), (cx + 6, foot - 1), (cx - 6, foot - 1)], robe[2])
    cv.rect(cx - 6, foot - 10, 13, 4, robe[3])                       # lap / knees lit from above
    cv.hline(cx - 6, foot - 10, 13, robe[4])
    cv.vline(cx - 5, foot - 17, 7, robe[3])                          # lit left side
    cv.vline(cx + 5, foot - 17, 16, robe[1])
    # velvet facings down the front in the hood colour, hood lining over the shoulders
    cv.line(cx - 3, foot - 18, cx - 1, foot - 11, hood); cv.line(cx + 3, foot - 18, cx + 1, foot - 11, hood)
    cv.hline(cx - 4, foot - 18, 9, shade(hood, 0.15))
    cv.vline(cx, foot - 17, 3, "#f4f2ec")                            # shirt and tie at the collar
    cv.px(cx, foot - 15, "#7a2a2a")
    # bell sleeves with velvet bars
    for sx in (cx - 6, cx + 5):
        cv.rect(sx, foot - 16, 2, 7, robe[1])
        cv.px(sx, foot - 14, robe[3]); cv.px(sx, foot - 12, robe[3])
    # hands
    if clap:
        cv.rect(cx - 1, foot - 15, 3, 2, skin); cv.px(cx, foot - 16, skin)
    else:
        cv.rect(cx - 2, foot - 10, 4, 2, skin); cv.px(cx + 1, foot - 9, shade(skin, -0.2))
    # shoes
    cv.rect(cx - 4, foot - 1, 3, 1, "#0a0a0e"); cv.rect(cx + 2, foot - 1, 3, 1, "#0a0a0e")
    # head
    cv.rect(cx - 2, foot - 23, 5, 5, skin)
    cv.vline(cx + 2, foot - 22, 4, shade(skin, -0.15))
    cv.px(cx - 1, foot - 21, "#2a1a14"); cv.px(cx + 1, foot - 21, "#2a1a14")
    cv.hline(cx - 1, foot - 19, 2, shade(skin, -0.25))
    cv.px(cx - 3, foot - 22, hair); cv.px(cx + 3, foot - 22, hair); cv.px(cx - 3, foot - 21, hair)
    if hair in ("#d8d4cc", "#8a8a90"):
        cv.px(cx + 3, foot - 21, hair)
    # tam (soft velvet cap) or mortarboard
    if tam:
        cv.rect(cx - 3, foot - 25, 7, 2, robe[1]); cv.hline(cx - 3, foot - 25, 7, robe[3]); cv.rect(cx - 2, foot - 26, 5, 1, robe[2])
        cv.vline(cx + 4, foot - 25, 3, GOLD[4])
    else:
        cv.rect(cx - 2, foot - 24, 5, 1, robe[1]); cv.hline(cx - 4, foot - 25, 9, robe[2]); cv.hline(cx - 3, foot - 26, 7, robe[3])
        cv.vline(cx + 4, foot - 25, 3, GOLD[4])
    cv.outline_outside(INK)
    return cv, cx, foot


def draped_chair(hood, seed=0):
    """An empty stage chair, a gown thrown over its back and the hood draped over that, a tam on
    the seat (someone has gone to read names)."""
    cv = Canvas(16, 30)
    cx, foot = 8, 28
    # chair: black frame, back and seat facing us
    cv.rect(cx - 5, foot - 20, 11, 9, "#2a2632"); cv.hline(cx - 5, foot - 20, 11, "#4a4652")
    cv.rect(cx - 6, foot - 11, 13, 3, "#3a3642"); cv.hline(cx - 6, foot - 11, 13, "#5a5662")
    for lx in (cx - 5, cx + 5):
        cv.vline(lx, foot - 8, 8, "#2a2632")
    cv.hline(cx - 5, foot - 3, 11, "#2a2632")
    # gown over the back, hanging down behind the seat
    cv.poly([(cx - 5, foot - 21), (cx + 6, foot - 21), (cx + 6, foot - 12), (cx + 4, foot - 6), (cx - 6, foot - 11)], ROBE[2])
    cv.hline(cx - 5, foot - 21, 11, ROBE[4]); cv.vline(cx - 2, foot - 20, 8, ROBE[1]); cv.vline(cx + 2, foot - 20, 10, ROBE[3])
    # hood: velvet edge and satin lining
    cv.line(cx - 4, foot - 20, cx + 4, foot - 14, hood); cv.line(cx - 4, foot - 19, cx + 3, foot - 13, shade(hood, -0.2))
    cv.px(cx + 4, foot - 13, GOLD[3])
    # tam on the seat
    cv.rect(cx - 3, foot - 13, 6, 2, ROBE[1]); cv.hline(cx - 3, foot - 13, 6, ROBE[3]); cv.px(cx + 3, foot - 12, GOLD[4])
    cv.outline_outside(INK)
    return cv, cx, foot


def pennant(cv, x, top, h, body, trim, emblem=None, wave=0):
    """A tall vertical banner hung from a crossarm, swallowtail hem. wave (px) swings the lower
    part sideways for the animated frame."""
    w = 13
    s = Canvas(w + 12, h + 4)
    ox = 6
    for yy in range(h):
        t = yy / max(1, h - 1)
        dx = int(round(wave * t * t))
        s.hline(ox + dx, yy + 1, w, body)
        s.px(ox + dx, yy + 1, trim); s.px(ox + dx + w - 1, yy + 1, trim)
        s.px(ox + dx + 1, yy + 1, shade(body, 0.14))
        s.px(ox + dx + w - 3, yy + 1, shade(body, -0.12))
        s.px(ox + dx + w - 2, yy + 1, shade(body, -0.05))
    d = int(round(wave))
    for k, nw in enumerate((5, 3, 3, 1, 1)):  # swallowtail notch
        c0 = ox + d + w // 2 - nw // 2
        s.a[h - k, c0:c0 + nw] = 0
    if emblem:
        emblem(s, ox + int(round(wave * (1 / 3) ** 2)) + w // 2, h // 3)
    s.outline_outside(INK)
    s.hline(ox - 2, 0, w + 4, STEEL[3])
    cv.paste(s, x - ox, top - 1)


def _torch(cv, cx, cy, c, c2):
    """Small torch emblem (CU's lamp of learning)."""
    cv.rect(cx - 1, cy + 2, 3, 7, c)
    cv.rect(cx - 2, cy + 1, 5, 2, c)
    cv.px(cx, cy - 1, c2); cv.px(cx - 1, cy, c2); cv.px(cx + 1, cy, c2); cv.px(cx, cy - 2, c2)


def stage_set(cv, x0, x1, deck_back, deck_y, front, seed=0, faculty=True):
    """The commencement stage on the field: a carpeted deck, black skirt with fan bunting and gold
    trim, stairs at both front corners, a black drape backdrop crowned by the COMMENCEMENT banner,
    the university name, a seal, and two rows of faculty. Returns positions used by layers."""
    rng = _rng(seed)
    cx = (x0 + x1) // 2
    info = {}
    # --- backdrop: a black drape on a frame, banner across its top -----------------------------
    bx0, bx1 = x0 + 18, x1 - 18
    btop = deck_back - 64
    cv.rect(bx0 - 2, btop - 2, bx1 - bx0 + 4, deck_back - btop + 2, STEEL[1])
    cv.rect(bx0, btop, bx1 - bx0, deck_back - btop, "#16141c")
    for x in range(bx0, bx1):
        f = (x - bx0) % 7
        c = "#221e28" if f in (1, 2) else "#1a1820" if f in (3, 4) else "#121016"
        cv.vline(x, btop + 22, deck_back - btop - 22, c)
    # banner
    label = "COMMENCEMENT"
    tw = text_width(label) * 2
    bw = tw + 24
    bl = cx - bw // 2
    by = btop - 2
    by -= 4
    bh = 26
    cv.rect(bl - 1, by - 1, bw + 2, bh + 2, INK)
    cv.rect(bl, by, bw, bh, GOLD[3])
    cv.hline(bl, by, bw, GOLD[4]); cv.hline(bl, by + bh - 1, bw, GOLD[1])
    cv.hline(bl + 2, by + 2, bw - 4, BLACK[1]); cv.hline(bl + 2, by + bh - 3, bw - 4, BLACK[1])
    stencil_text(cv, label, bl + 12 + 1, by + 3, GOLD[1], scale=2)
    stencil_text(cv, label, bl + 12, by + 2, BLACK[1], scale=2)
    for gx in (bl + 4, bl + bw - 6):
        cv.px(gx, by + 12, BLACK[1]); cv.px(gx + 1, by + 12, BLACK[1]); cv.px(gx, by + 11, GOLD[4])
    info["banner"] = (bl, by, bw, bh)
    # university name and the seal on the drape
    uni = "UNIVERSITY OF COLORADO BOULDER"
    uw = text_width(uni)
    text(cv, uni, cx - uw // 2, btop + 25, GOLD[3])
    sy = btop + 42
    cv.ellipse(cx - 9, sy - 9, 19, 19, INK)
    cv.ellipse(cx - 8, sy - 8, 17, 17, GOLD[3]); cv.ellipse(cx - 6, sy - 6, 13, 13, GOLD[1]); cv.ellipse(cx - 5, sy - 5, 11, 11, GOLD[2])
    _torch(cv, cx, sy - 4, BLACK[1], "#f6e6a0")
    for k in range(12):
        a = k / 12 * 2 * np.pi
        cv.px(int(round(cx + np.cos(a) * 7)), int(round(sy + np.sin(a) * 7)), GOLD[4])
    info["seal"] = (cx, sy)
    # --- deck: grey stage carpet in perspective rows ---------------------------------------------
    for y in range(deck_back, deck_y):
        t = (y - deck_back) / max(1, deck_y - deck_back)
        c = ["#4a4a58", "#545462", "#5e5e6c"][min(2, int(t * 3))]
        cv.hline(x0, y, x1 - x0, c)
        if y % 3 == 0:
            for x in range(x0 + (y % 6), x1, 6):
                cv.px(x, y, shade(c, -0.08))
    cv.hline(x0, deck_back, x1 - x0, "#2a2a34")
    # --- faculty: two rows each side of the centre --------------------------------------------
    if faculty:
        spots = []
        for side in (-1, 1):
            for k in range(4):
                spots.append((cx + side * (40 + k * 19), deck_back + 9, 0))
            for k in range(4):
                spots.append((cx + side * (49 + k * 19), deck_back + 18, 1))
        spots.sort(key=lambda s: s[1])
        for i, (fx, fy, row) in enumerate(spots):
            hood = HOODS[int(rng.integers(0, len(HOODS)))]
            r = rng.random()
            if r < 0.18:
                spr, ax, ay = draped_chair(hood, seed=i)
            else:
                sk = SKIN[int(rng.integers(0, len(SKIN)))]
                hair = HAIR[int(rng.integers(0, len(HAIR)))]
                spr, ax, ay = seated_faculty(hood, sk, hair, seed=i, clap=rng.random() < 0.35, tam=rng.random() < 0.7)
            cv.paste(spr, fx - ax, fy - ay)
    # --- front edge and skirt --------------------------------------------------------------------
    cv.rect(x0, deck_y - 1, x1 - x0, 2, GOLD[3]); cv.hline(x0, deck_y - 1, x1 - x0, GOLD[4])
    cv.rect(x0, deck_y + 1, x1 - x0, front - deck_y - 1, BLACK[1])
    for x in range(x0, x1):
        if (x - x0) % 4 == 0:
            cv.vline(x, deck_y + 1, front - deck_y - 1, BLACK[0])
        elif (x - x0) % 4 == 1:
            cv.vline(x, deck_y + 1, front - deck_y - 1, BLACK[2])
    cv.hline(x0, front - 1, x1 - x0, "#0a0a0e")
    # stairs at both front corners
    for sx0 in (x0 + 2, x1 - 24):
        n = 4
        sh = (front - deck_y) // n
        for k in range(n):
            yy = deck_y + 1 + k * sh
            cv.rect(sx0, yy, 22, sh, "#3a3a46")
            cv.hline(sx0, yy, 22, GOLD[3]); cv.hline(sx0, yy + 1, 22, "#5e5e6c")
        for rx in (sx0, sx0 + 21):
            cv.vline(rx, deck_y - 10, front - deck_y + 10, GOLD[2])
            cv.vline(rx + (1 if rx == sx0 else -1), deck_y - 10, 2, GOLD[4])
        cv.line(sx0, deck_y - 10, sx0, front - 1, GOLD[3])
    info["stairs"] = ((x0 + 2, x0 + 24), (x1 - 24, x1 - 2))
    # fan bunting along the skirt, between the stairs, leaving the centre for the podium thrust
    fans = [x for x in range(x0 + 44, x1 - 34, 34) if abs(x - cx) > 30]
    for fx in fans:
        fan_bunting(cv, fx, deck_y + 2, r=12)
    # garland swags between the fans
    for a, b in zip(fans[:-1], fans[1:]):
        if abs((a + b) / 2 - cx) < 30:
            continue
        for x in range(a + 12, b - 11):
            t = (x - a - 12) / max(1, b - a - 23)
            y = deck_y + 2 + int(4 * np.sin(t * np.pi))
            cv.px(x, y, LEAFG[3]); cv.px(x, y + 1, LEAFG[1])
            if x % 3 == 0:
                cv.px(x, y, FLOWERS["gold"][2])
    info["fans"] = fans
    return info


# ============================================================================================
# floor
# ============================================================================================
def turf(cv, x, y, w, h, pal=TURF_SUN, band=33, seed=0, mask=None):
    """Stadium grass: crisp mowing bands across the field (two greens), blade tufts on a jittered
    grid, lighter on the lit band, a few darker divots and clover flecks."""
    rng = _rng(seed)
    sub = np.zeros((cv.h, cv.w), bool)
    sub[max(0, y):y + h, max(0, x):x + w] = True
    if mask is not None:
        sub &= mask
    ys, xs = np.where(sub)
    stripe = (ys // band) % 2
    cv.a[ys, xs, :3] = np.where(stripe[:, None] == 0, np.array(C(pal[4])[:3]), np.array(C(pal[3])[:3]))
    cv.a[ys, xs, 3] = 1
    for gy in range(y, y + h, 3):
        for gx in range(x + (gy // 3 % 2) * 2, x + w, 4):
            if rng.random() < 0.35:
                continue
            tx, ty = gx + int(rng.integers(0, 3)), gy + int(rng.integers(0, 2))
            if not (0 <= tx < cv.w - 2 and 1 <= ty < cv.h - 1 and sub[ty, tx]):
                continue
            lit = (ty // band) % 2 == 0
            r = rng.random()
            if lit:
                c = pal[6] if r < 0.35 else pal[5] if r < 0.8 else pal[3]
            else:
                c = pal[5] if r < 0.25 else pal[4] if r < 0.7 else pal[2]
            if rng.random() < 0.5:
                cv.px(tx, ty, c); cv.px(tx + 1, ty - 1, c)
            else:
                cv.px(tx, ty, c); cv.px(tx, ty - 1, shade(c, 0.08))
    for _ in range(w * h // 6000):
        cx, cy = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        if 0 <= cx < cv.w - 4 and 0 <= cy < cv.h and sub[cy, cx]:
            cv.rect(cx, cy, 4, 1, pal[1]); cv.rect(cx + 1, cy + 1, 2, 1, pal[2])
    for _ in range(w * h // 9000):
        cx, cy = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        for _ in range(5):
            px_, py_ = cx + int(rng.integers(-3, 4)), cy + int(rng.integers(-1, 2))
            if 0 <= px_ < cv.w and 0 <= py_ < cv.h and sub[py_, px_]:
                cv.px(px_, py_, pal[6]); cv.px(px_ + 1, py_, pal[5])


def paint_line(cv, x, y, w, h, seed=0, mask=None, alpha=1.0):
    """A chalk-white field line, a little worn where the grass shows through."""
    rng = _rng(seed)
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if not (0 <= xx < cv.w and 0 <= yy < cv.h):
                continue
            if mask is not None and not mask[yy, xx]:
                continue
            r = rng.random()
            if r < 0.06:
                continue
            c = LINE[2] if yy == y else LINE[1] if yy == y + h - 1 else LINE[2] if r < 0.8 else LINE[3]
            cv.px(xx, yy, C(c, alpha))


def runner(cv, x0, x1, y0, y1, seed=0):
    """The centre-aisle carpet: CU black with gold borders and a pinstripe, pile in soft rows."""
    rng = _rng(seed)
    for y in range(y0, y1):
        c = BLACK[2] if (y // 2) % 3 else BLACK[1]
        cv.hline(x0, y, x1 - x0, c)
        if y % 4 == 0:
            for x in range(x0 + 6 + (y // 4 % 2) * 3, x1 - 6, 7):
                cv.hline(x, y, 2, BLACK[3])
    cv.rect(x0, y0, 3, y1 - y0, GOLD[2]); cv.vline(x0, y0, y1 - y0, GOLD[4])
    cv.rect(x1 - 3, y0, 3, y1 - y0, GOLD[2]); cv.vline(x1 - 1, y0, y1 - y0, GOLD[1])
    cv.vline(x0 + 6, y0, y1 - y0, GOLD[2]); cv.vline(x1 - 7, y0, y1 - y0, GOLD[1])
    # edge where the carpet sits on the grass
    cv.vline(x0 - 1, y0, y1 - y0, C("#0d0b16", 0.45)); cv.vline(x1, y0, y1 - y0, C("#0d0b16", 0.35))
    # a seam across it
    for sy in range(y0 + 90, y1, 120):
        cv.hline(x0 + 3, sy, x1 - x0 - 6, BLACK[0])


def tile_path(cv, mask, size=(16, 10), seed=0, pal=("#5e646e", "#8a929c", "#a8b0b8", "#c4cad0", "#dce0e4")):
    """Interlocking turf-protection tiles laid as a walkway: square panels with a lit bevel, a
    darker seam and a grid of drain holes (regular, so it reads as the tile's surface)."""
    rng = _rng(seed)
    tw, th = size
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return
    for y, x in zip(ys, xs):
        fx, fy = x % tw, y % th
        tone = 2 if ((x // tw) + (y // th)) % 2 else 3
        c = pal[tone]
        if fx == 0 or fy == 0:
            c = pal[0]
        elif fy == 1 or fx == 1:
            c = pal[4]
        elif fy == th - 1 or fx == tw - 1:
            c = pal[1]
        elif fx % 4 == 3 and fy % 3 == 2:
            c = pal[1]
        cv.px(x, y, c)


def confetti_flat(cv, x, y, w, h, n=200, seed=0, mask=None, cols=CONFETTI):
    """Confetti lying flat on the grass: 2x1 and 1x2 flecks with a dark tick under each."""
    rng = _rng(seed)
    for _ in range(n):
        px_, py_ = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        if mask is not None and not (0 <= py_ < mask.shape[0] and 0 <= px_ < mask.shape[1] and mask[py_, px_]):
            continue
        c = cols[int(rng.integers(len(cols)))]
        if rng.random() < 0.6:
            cv.hline(px_, py_, 2, c)
        else:
            cv.vline(px_, py_, 2, c)
        cv.px(px_ + 1, py_ + 1, C("#0d0b16", 0.25))


def program_flat(cv, x, y, open_=False, seed=0):
    """A commencement programme dropped on the grass: cream booklet, gold seal, a crease."""
    if open_:
        cv.rect(x - 1, y - 1, 14, 7, C("#0d0b16", 0.3))
        cv.rect(x, y, 6, 5, "#f2ecdc"); cv.rect(x + 6, y, 6, 5, "#e6dcc6")
        cv.vline(x + 6, y, 5, "#b8ae98")
        for k in (1, 3):
            cv.hline(x + 1, y + k, 4, "#8a8070"); cv.hline(x + 7, y + k, 4, "#8a8070")
    else:
        cv.rect(x - 1, y - 1, 8, 9, C("#0d0b16", 0.3))
        cv.rect(x, y, 7, 8, "#f6f0e2"); cv.hline(x, y, 7, "#ffffff"); cv.vline(x + 6, y, 8, "#c8bca4")
        cv.rect(x + 1, y + 1, 5, 2, BLACK[1]); cv.rect(x + 2, y + 4, 3, 3, GOLD[3]); cv.px(x + 3, y + 5, GOLD[1])


def cap_flat(cv, x, y):
    """A mortarboard lying on the grass, tassel trailing."""
    cv.poly([(x, y + 2), (x + 6, y), (x + 12, y + 2), (x + 6, y + 5)], ROBE[2])
    cv.line(x, y + 2, x + 6, y, ROBE[4]); cv.line(x + 6, y, x + 12, y + 2, ROBE[3])
    cv.px(x + 6, y + 2, GOLD[4])
    cv.line(x + 6, y + 2, x + 9, y + 6, GOLD[3]); cv.px(x + 9, y + 7, GOLD[4])
    cv.hline(x + 1, y + 6, 10, C("#0d0b16", 0.25))


def petals(cv, cx, cy, r, n, seed=0, mask=None):
    rng = _rng(seed)
    for _ in range(n):
        a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
        px_, py_ = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.5)
        if mask is not None and not (0 <= py_ < mask.shape[0] and 0 <= px_ < mask.shape[1] and mask[py_, px_]):
            continue
        c = ["#f0c030", "#fbe27a", "#ffffff", "#e88aa0"][int(rng.integers(0, 4))]
        cv.px(px_, py_, c); cv.px(px_ + 1, py_, shade(c, -0.2))


# ============================================================================================
# props
# ============================================================================================
def mortarboard(tilt=0, tassel=1, big=False):
    """A tossed mortarboard (for the animated layers): the black board seen at an angle with a lit
    top face and edge, the skull cap under it, a gold button and tassel. tilt 0..3 picks the
    angle; big gives the nearer, battle-size cap. Returns an RGBA Canvas."""
    s = 2 if big else 1
    cv = Canvas(13 * s + 4, 11 * s + 4)
    shapes = [[(0, 4), (6, 1), (12, 4), (6, 7)],        # nearly flat, top face toward us
              [(1, 2), (9, 0), (11, 5), (3, 7)],        # tipped right
              [(1, 5), (3, 1), (11, 2), (9, 7)],        # tipped left
              [(0, 4), (6, 3), (12, 4), (6, 5)]]        # edge on
    pts = [(2 + x * s, 2 + y * s) for (x, y) in shapes[tilt % 4]]
    mx = sum(p[0] for p in pts) // 4
    my = sum(p[1] for p in pts) // 4
    if tilt % 4 != 3:
        cv.rect(mx - 2 * s + 1, my + s, 4 * s - 1, 2 * s, ROBE[1])         # skull cap under the board
    cv.poly(pts, ROBE[2])
    if big:
        inner = [((p[0] - mx) * 0.6 + mx, (p[1] - my) * 0.6 + my) for p in pts]
        cv.poly(inner, ROBE[3])
    cv.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], ROBE[4])
    cv.line(pts[1][0], pts[1][1], pts[2][0], pts[2][1], "#6a6878")
    cv.line(pts[3][0], pts[3][1], pts[2][0], pts[2][1], ROBE[1])
    cv.px(mx, my, GOLD[4])
    if tassel:
        tx = mx + (2 * s if tilt % 2 == 0 else -2 * s)
        cv.line(mx, my, tx, my + 3 * s, GOLD[3])
        cv.rect(tx - (s - 1), my + 3 * s, s, 2 * s + 1, GOLD[3]); cv.px(tx, my + 3 * s, GOLD[4])
    cv.outline_outside(INK)
    return cv


def folding_chair(kind=None, rng=None, cw=16, h=30):
    """One white resin folding chair seen from behind (it faces the stage): a moulded backrest
    with a lit top rail and a hand slot, the seat seen through the gap under it, rear posts running
    down to splayed feet, front legs inset, braces. kind adds what its graduate left on it.
    Returns (Canvas, anchor_x, anchor_y)."""
    rng = rng or _rng(0)
    Wc = CHAIR_W
    s = Canvas(cw + 8, h + 12)
    ox, base = 4, s.h - 2
    top = base - h
    back_h = 10
    seat_y = top + back_h
    upper = Canvas(s.w, s.h)
    # backrest: rounded top corners, lit top rail, shaded lower edge
    upper.rect(ox, top, cw, back_h, Wc[4])
    upper.hline(ox + 1, top, cw - 2, Wc[5]); upper.hline(ox, top + 1, cw, Wc[5])
    upper.a[top, ox] = 0; upper.a[top, ox + cw - 1] = 0
    upper.vline(ox, top + 1, back_h - 1, Wc[5]); upper.vline(ox + cw - 1, top + 1, back_h - 1, Wc[2])
    upper.hline(ox + 1, top + back_h - 2, cw - 2, Wc[3]); upper.hline(ox + 1, top + back_h - 1, cw - 2, Wc[2])
    upper.hline(ox + cw // 2 - 2, top + 3, 4, Wc[1]); upper.hline(ox + cw // 2 - 2, top + 4, 4, Wc[2])   # hand slot
    # the seat beyond the backrest, between the rear posts
    for (px_, c) in ((ox, Wc[4]), (ox + cw - 2, Wc[3])):
        upper.rect(px_, seat_y, 2, 3, c)
    upper.rect(ox + 2, seat_y, cw - 4, 3, Wc[3]); upper.hline(ox + 2, seat_y, cw - 4, Wc[1]); upper.hline(ox + 2, seat_y + 2, cw - 4, Wc[2])
    if kind == "seat_programme":    # a programme left lying on the seat
        upper.rect(ox + 5, seat_y, 5, 2, "#f6f0e2"); upper.px(ox + 7, seat_y + 1, GOLD[3])
    # things over the backrest
    t = top
    if kind == "cap":               # mortarboard perched on the top rail, tassel down the back
        upper.poly([(ox + 1, t - 1), (ox + 8, t - 4), (ox + 15, t - 1), (ox + 8, t + 2)], ROBE[2])
        upper.line(ox + 1, t - 1, ox + 8, t - 4, ROBE[4]); upper.line(ox + 8, t - 4, ox + 15, t - 1, ROBE[3])
        upper.px(ox + 8, t - 1, GOLD[4])
        upper.line(ox + 8, t - 1, ox + 11, t + 2, GOLD[3]); upper.vline(ox + 11, t + 2, 4, GOLD[3]); upper.px(ox + 11, t + 6, GOLD[4])
    elif kind == "programme":       # programme tucked behind the backrest, sticking up
        px_ = ox + 3 + int(rng.integers(0, 6))
        upper.rect(px_, t - 5, 6, 7, "#f6f0e2"); upper.hline(px_, t - 5, 6, "#ffffff"); upper.vline(px_ + 5, t - 5, 7, "#c8bca4")
        upper.rect(px_ + 1, t - 4, 4, 1, BLACK[1]); upper.rect(px_ + 2, t - 2, 2, 2, GOLD[3])
    elif kind == "gown":            # a black gown slung over the back, folds, a sleeve hanging lower
        for xx in range(ox - 1, ox + cw + 1):
            bot = seat_y + 1 + int(abs(np.sin(xx * 1.7)) * 3)
            upper.vline(xx, t - 1, bot - t + 1, ROBE[2])
            if (xx - ox) % 4 == 1:
                upper.vline(xx, t, bot - t - 1, ROBE[3])
            elif (xx - ox) % 4 == 3:
                upper.vline(xx, t + 1, bot - t - 1, ROBE[1])
        upper.hline(ox, t - 1, cw, ROBE[4])
        sx = ox + (cw - 5 if rng.random() < 0.5 else 0)
        upper.rect(sx, seat_y + 2, 5, 9, ROBE[2]); upper.vline(sx, seat_y + 2, 9, ROBE[3]); upper.hline(sx, seat_y + 10, 5, ROBE[1])
        hood = HOODS[int(rng.integers(0, len(HOODS)))]
        upper.line(ox + 2, t + 1, ox + cw - 4, t + 5, hood)
    elif kind == "stole":           # a gold honours stole over the top rail
        for sx in (ox + 3, ox + cw - 6):
            upper.rect(sx, t - 1, 3, 13, GOLD[3]); upper.vline(sx, t - 1, 13, GOLD[4]); upper.hline(sx, t + 11, 3, GOLD[1])
            upper.px(sx + 1, t + 9, BLACK[1])
        upper.hline(ox + 4, t - 1, cw - 8, GOLD[4])
    elif kind == "bouquet":         # flowers in paper laid along the top of the back
        upper.line(ox + 1, t + 1, ox + 13, t - 2, LEAFG[2]); upper.line(ox + 1, t + 2, ox + 12, t - 1, LEAFG[3])
        upper.rect(ox + 3, t - 1, 4, 3, "#e6dcc6")
        for (fx, fy, c) in [(ox + 11, t - 5, FLOWERS["red"][2]), (ox + 13, t - 3, FLOWERS["gold"][2]), (ox + 9, t - 3, FLOWERS["white"][2]),
                            (ox + 12, t - 6, FLOWERS["red"][3]), (ox + 14, t - 5, FLOWERS["white"][3])]:
            upper.rect(fx - 1, fy - 1, 2, 2, c); upper.px(fx, fy, shade(c, 0.2))
    elif kind == "sign":            # a little card taped to the back: a name and a heart
        upper.rect(ox + 3, t + 2, 10, 5, "#f4e6a0"); upper.hline(ox + 4, t + 3, 6, "#3a3a46"); upper.px(ox + 11, t + 5, "#d04040")
    upper.outline_outside(INK)
    # legs (no ink: thin white against the grass reads cleaner): front legs inset, rear posts splay
    for lx in (ox + 3, ox + cw - 4):
        s.vline(lx, seat_y + 3, base - seat_y - 5, Wc[1])
    s.hline(ox + 3, base - 9, cw - 6, Wc[1])
    for (lx, d, c) in ((ox, -1, Wc[4]), (ox + cw - 2, 1, Wc[3])):
        mid = seat_y + 3 + (base - seat_y - 3) // 2
        s.rect(lx, seat_y + 3, 2, mid - seat_y - 3, c)
        s.rect(lx + (d if d > 0 else 0), mid, 2 if d < 0 else 2, base - mid, c)
        if d < 0:
            s.vline(lx - 1, mid, base - mid, c); s.vline(lx + 1, mid, base - mid, Wc[2])
        s.px(lx + (0 if d < 0 else 1), base - 1, Wc[0]); s.px(lx + (-1 if d < 0 else 2), base - 1, Wc[0])
        s.vline(lx + (1 if d < 0 else 0), seat_y + 3, mid - seat_y - 3, Wc[2])
    s.hline(ox, base - 5, cw, Wc[2]); s.hline(ox + 1, base - 4, cw - 2, Wc[1])
    if kind == "bottle":            # a water bottle on the grass under the seat
        bx = ox + cw // 2 - 1
        s.rect(bx - 1, base - 9, 4, 9, INK)
        s.rect(bx, base - 8, 2, 7, "#9ac8e0"); s.px(bx, base - 8, "#e0f0f8"); s.rect(bx, base - 9, 2, 1, "#3a6ab0")
    s.paste(upper, 0, 0)
    return s, ox + cw // 2, base


def white_chair_row(width=300, height=34, n=10, seed=0, rich=True):
    """A row of white folding chairs seen from behind, facing the stage, with what the graduates
    left when they stood to throw their caps: a mortarboard on a back, programmes tucked over a
    rail or left on a seat, a gown slung over one, a bouquet, a stole, a water bottle beneath.
    Anchor bottom centre."""
    rng = _rng(seed)
    CW, CH = width + 12, height + 14
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 6, CH - 3
    pitch = width / n
    kinds = []
    for i in range(n):
        r = rng.random()
        k = None
        if rich:
            for (lim, name) in ((0.13, "cap"), (0.24, "programme"), (0.31, "gown"), (0.37, "stole"), (0.43, "bouquet"),
                                (0.49, "seat_programme"), (0.53, "bottle"), (0.56, "sign")):
                if r < lim:
                    k = name
                    break
        kinds.append(k)
    for i in range(n):
        cx = int(round(ox + i * pitch + pitch / 2)) + int(rng.integers(-1, 2))
        dy = 1 if rng.random() < 0.25 else 0
        cv.rect(cx - 8, base - 1 - dy, 17, 2, C("#0d0b16", 0.28))
        spr, ax, ay = folding_chair(kinds[i], rng=rng)
        cv.paste(spr, cx - ax, base - dy - ay)
    return cv, ox + width // 2, base


def podium_thrust(seed=0):
    """The podium on a small thrust in front of the stage: a carpeted step with fan bunting on
    its face, the lectern (oak, a gold CU seal), a gooseneck microphone, a glass of water and
    the open book of names. Anchor bottom centre at the thrust's front edge."""
    w, h = 50, 60
    cv = Canvas(w, h, seed=seed)
    cx, base = w // 2, h - 2
    # thrust step: front face (black skirt, gold nosing) and carpeted top running back to the stage
    tw = 44
    tx = cx - tw // 2
    face_top = base - 11
    cv.rect(tx - 1, face_top - 15, tw + 2, base - face_top + 16, INK)
    cv.rect(tx, face_top - 14, tw, 14, "#545462")
    for y in range(face_top - 14, face_top):
        if y % 3 == 0:
            for x in range(tx + (y % 6), tx + tw, 6):
                cv.px(x, y, "#4a4a58")
    cv.rect(tx, face_top - 1, tw, 2, GOLD[3]); cv.hline(tx, face_top - 1, tw, GOLD[4])
    cv.rect(tx, face_top + 1, tw, base - face_top - 1, BLACK[1])
    for x in range(tx, tx + tw):
        if (x - tx) % 4 == 0:
            cv.vline(x, face_top + 1, base - face_top - 1, BLACK[0])
        elif (x - tx) % 4 == 1:
            cv.vline(x, face_top + 1, base - face_top - 1, BLACK[2])
    fan_bunting(cv, cx, face_top + 1, r=8)
    # lectern: standing on the thrust top
    lb = face_top - 5
    lw = 26
    lx = cx - lw // 2
    lt = lb - 36
    cv.rect(lx - 1, lt - 1, lw + 2, lb - lt + 2, INK)
    oak = ["#3a2018", "#5a3424", "#7e4c30", "#a0663e", "#c0844e", "#dca262"]
    cv.rect(lx, lt + 4, lw, lb - lt - 4, oak[3])
    cv.vline(lx, lt + 4, lb - lt - 4, oak[5]); cv.vline(lx + 1, lt + 4, lb - lt - 4, oak[4])
    cv.vline(lx + lw - 1, lt + 4, lb - lt - 4, oak[1]); cv.vline(lx + lw - 2, lt + 4, lb - lt - 4, oak[2])
    for gy in range(lt + 8, lb - 2, 5):
        cv.hline(lx + 3, gy, 4 + (gy * 7) % 9, oak[2])
    cv.rect(lx + 3, lb - 4, lw - 6, 3, oak[2]); cv.hline(lx + 3, lb - 4, lw - 6, oak[4])
    # slanted top with the open book of names
    cv.rect(lx - 2, lt, lw + 4, 5, oak[4]); cv.hline(lx - 2, lt, lw + 4, oak[5]); cv.hline(lx - 2, lt + 4, lw + 4, oak[1])
    cv.rect(lx - 3, lt - 1, lw + 6, 1, INK)
    cv.rect(cx - 8, lt - 2, 16, 3, "#f6f0e2"); cv.vline(cx, lt - 2, 3, "#c8bca4")
    cv.hline(cx - 7, lt - 1, 6, "#8a8070"); cv.hline(cx + 2, lt - 1, 5, "#8a8070")
    # seal on the front
    sy = lt + 15
    cv.ellipse(cx - 7, sy - 7, 15, 15, INK)
    cv.ellipse(cx - 6, sy - 6, 13, 13, GOLD[3]); cv.ellipse(cx - 4, sy - 4, 9, 9, BLACK[1])
    _torch(cv, cx, sy - 3, GOLD[3], "#fff2b0")
    cv.px(cx - 5, sy - 3, GOLD[4]); cv.px(cx - 4, sy - 5, GOLD[4])
    # gooseneck mic and a glass of water
    cv.line(cx + 6, lt, cx + 9, lt - 7, STEEL[2]); cv.line(cx + 9, lt - 7, cx + 6, lt - 11, STEEL[2])
    cv.rect(cx + 4, lt - 13, 4, 3, BLACK[1]); cv.px(cx + 5, lt - 13, STEEL[4])
    cv.rect(lx + 1, lt - 5, 3, 4, "#c8e0ec"); cv.px(lx + 1, lt - 5, "#ffffff"); cv.hline(lx + 1, lt - 3, 3, "#8ab8d0")
    cv.outline_outside(INK)
    return cv, cx, base


def field_lamp(height=68):
    """The field light / save post: a black iron campus lamp with an acorn lantern still faintly
    lit, a gold-and-black CLASS banner on a bracket, a bow of ribbon on the post. Lamp core
    ~5px below the top."""
    from lib_norlin import lantern_head
    w = 34
    cv = Canvas(w, height + 6, seed=17)
    cx, base = 12, height + 2
    ground_shadow(cv, cx, base, 9, 2)
    cv.rect(cx - 6, base - 5, 13, 5, OUT); cv.rect(cx - 5, base - 4, 11, 4, IRON[2]); cv.hline(cx - 5, base - 4, 11, IRON[4])
    cv.rect(cx - 4, base - 10, 9, 5, OUT); cv.rect(cx - 3, base - 9, 7, 4, IRON[2]); cv.vline(cx - 3, base - 9, 4, IRON[4])
    top = base - height
    cv.rect(cx - 2, top + 18, 5, height - 28, OUT)
    cv.vline(cx - 1, top + 18, height - 28, IRON[3]); cv.vline(cx, top + 18, height - 28, IRON[2]); cv.vline(cx + 1, top + 18, height - 28, IRON[1])
    cv.vline(cx - 1, top + 18, height - 28, mix(IRON[4], "#f6c47a", 0.35))
    for ry in (top + 21, top + 46):
        cv.rect(cx - 3, ry, 7, 2, IRON[1]); cv.hline(cx - 3, ry, 7, IRON[4])
    glass = (mix("#e9a84a", "#e0d4bc", 0.5), mix("#f6cf7a", "#efe6d2", 0.5), "#fff6e0")
    lantern_head(cv, cx, top, glass=glass)
    # banner on a bracket
    by = top + 24
    cv.rect(cx + 2, by, 16, 2, IRON[1]); cv.hline(cx + 2, by, 16, IRON[3]); cv.px(cx + 17, by - 1, IRON[3])
    bx0, bw, bh = cx + 5, 13, 24
    cv.rect(bx0 - 1, by + 2, bw + 2, bh + 1, OUT)
    cv.rect(bx0, by + 2, bw, bh, GOLD[3]); cv.vline(bx0, by + 2, bh, GOLD[4]); cv.vline(bx0 + bw - 1, by + 2, bh, GOLD[1])
    cv.rect(bx0 + 1, by + 3, bw - 2, 2, BLACK[1]); cv.rect(bx0 + 1, by + bh - 4, bw - 2, 2, BLACK[1])
    _torch(cv, bx0 + bw // 2, by + 9, BLACK[1], "#c84a3c")
    for k in range(bw // 2 + 1):
        cv.vline(bx0 + bw // 2 - k, by + bh + 2 - (k // 2) - 1, (k // 2) + 1, (0, 0, 0, 0))
        cv.vline(bx0 + bw // 2 + k, by + bh + 2 - (k // 2) - 1, (k // 2) + 1, (0, 0, 0, 0))
    # ribbon bow tied on the post
    ry = top + 32
    cv.rect(cx - 5, ry, 3, 3, GOLD[3]); cv.rect(cx + 2, ry, 3, 3, GOLD[3]); cv.rect(cx - 1, ry + 1, 2, 2, GOLD[4])
    cv.vline(cx - 3, ry + 3, 5, GOLD[2]); cv.vline(cx + 2, ry + 3, 6, GOLD[2])
    return cv, cx, base


def balloon_bunch(width=40, height=90, seed=0):
    """Gold, black and white balloons (one gold foil star) on curled ribbons, tied off at the
    bottom to a little gold weight hidden behind the chair it is tied to. Anchor bottom centre."""
    rng = _rng(seed)
    W_, H_ = width + 16, height + 4
    cv = Canvas(W_, H_, seed=seed)
    ax, ay = W_ // 2, H_ - 2
    balloons = [(-11, 14, "gold"), (6, 9, "black"), (-2, 2, "white"), (13, 22, "gold"), (-15, 30, "black"),
                (3, 24, "gold"), (-6, 18, "star")]
    pals = {"gold": ["#6a4a10", "#b8862a", "#e0b040", "#f6d870", "#fff4c0"],
            "black": ["#08080c", "#16161e", "#262632", "#3e3e4e", "#9a9ab0"],
            "white": ["#a0a0aa", "#c8c8d0", "#e6e6ea", "#f6f6f8", "#ffffff"]}
    knot = (ax, ay - 2)
    # ribbons first, curling down to the knot
    tops = []
    for (dx, dy, kind) in balloons:
        bx, by = ax + dx, 2 + dy + 12
        tops.append((bx, by))
        n = ay - 2 - by
        for k in range(n):
            t = k / max(1, n)
            x = int(round(bx + (knot[0] - bx) * t + np.sin(t * 9 + dx) * 1.5 * (1 - t)))
            cv.px(x, by + k, GOLD[3] if (k // 3) % 2 else "#f4f2ec")
    # balloons, back to front
    for (dx, dy, kind) in sorted(balloons, key=lambda b: b[1]):
        bx, by = ax + dx, 2 + dy
        if kind == "star":
            pts = []
            for k in range(10):
                a = -np.pi / 2 + k * np.pi / 5
                r = 8 if k % 2 == 0 else 4
                pts.append((bx + np.cos(a) * r, by + 6 + np.sin(a) * r))
            cv.poly([(p[0] - 0.5, p[1] - 0.5) for p in pts], INK)
            cv.poly(pts, "#d8b040")
            inner = [(bx + (p[0] - bx) * 0.6, by + 6 + (p[1] - by - 6) * 0.6) for p in pts]
            cv.poly(inner, "#f6dc80")
            cv.px(bx - 2, by + 3, "#ffffff"); cv.px(bx - 1, by + 3, "#fff4c0")
            continue
        p = pals[kind]
        cv.ellipse(bx - 7, by - 1, 15, 16, INK)
        cv.ellipse(bx - 6, by, 13, 14, p[2])
        cv.ellipse(bx - 5, by + 1, 9, 10, p[3] if kind != "black" else p[3])
        # shading: lower right darker
        sub = Canvas(cv.w, cv.h)
        sub.ellipse(bx - 6, by, 13, 14, "#000000")
        m = sub.a[..., 3] > 0
        ys, xs = np.where(m)
        lower = (xs - bx) * 0.6 + (ys - by - 7) > 3
        cv.a[ys[lower], xs[lower], :3] = np.array(C(p[1])[:3])
        cv.rect(bx - 3, by + 2, 2, 3, p[4]); cv.px(bx - 1, by + 2, p[4])
        cv.rect(bx - 1, by + 14, 3, 2, p[1]); cv.px(bx, by + 16, p[1])
    # the knot and a gold weight
    cv.rect(knot[0] - 3, ay - 5, 7, 5, INK)
    cv.rect(knot[0] - 2, ay - 4, 5, 3, GOLD[3]); cv.hline(knot[0] - 2, ay - 4, 5, GOLD[4])
    return cv, ax, ay


def confetti_clumps(cv, clumps, seed=0, mask=None):
    """Confetti lying where it landed: drifts of flecks around a few centres (cx, cy, rx, n),
    denser in the middle, so it reads as heaps rather than an even sprinkle."""
    rng = _rng(seed)
    for (cx, cy, rx, n) in clumps:
        for _ in range(n * 6):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, 0.5)) * rx
            px_, py_ = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.45)
            if mask is not None and not (0 <= py_ < mask.shape[0] and 0 <= px_ < mask.shape[1] and mask[py_, px_]):
                continue
            c = _w(rng, CONFETTI_PILE, [5, 5, 2, 1, 1])
            r = rng.random()
            if r < 0.45:
                cv.hline(px_, py_, 2, c)
            elif r < 0.75:
                cv.vline(px_, py_, 2, c)
            else:
                cv.rect(px_, py_, 2, 2, c); cv.px(px_ + 1, py_ + 1, shade(c, -0.2))


def honour_cord(cv, x, y):
    """A gold honour cord dropped on the grass: a twisted loop with tassels at both ends."""
    pts = [(x, y + 3), (x + 4, y), (x + 10, y - 1), (x + 15, y + 2), (x + 13, y + 6), (x + 6, y + 6), (x + 3, y + 4), (x + 8, y + 2),
           (x + 18, y + 5), (x + 22, y + 4)]
    for (a, b) in zip(pts[:-1], pts[1:]):
        cv.line(a[0], a[1] + 1, b[0], b[1] + 1, C("#0d0b16", 0.3))
    for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        cv.line(a[0], a[1], b[0], b[1], GOLD[3] if i % 2 else GOLD[4])
    for (tx, ty) in (pts[0], pts[-1]):
        cv.rect(tx - 1, ty, 3, 3, GOLD[2]); cv.px(tx, ty, GOLD[4])


def bouquet_flat(cv, x, y, flip=False):
    """A bouquet left lying on the grass: paper cone, stems, a few roses and a sunflower."""
    s = Canvas(22, 12)
    s.poly([(1, 8), (8, 5), (9, 10), (2, 11)], "#e6dcc6"); s.line(1, 8, 8, 5, "#fff8e6"); s.line(2, 11, 9, 10, "#b8ae98")
    s.line(8, 7, 14, 6, LEAFG[3]); s.line(8, 8, 14, 8, LEAFG[2])
    for (fx, fy, c) in [(15, 4, FLOWERS["red"]), (17, 7, FLOWERS["gold"]), (14, 9, FLOWERS["red"]), (18, 4, FLOWERS["white"])]:
        s.rect(fx - 1, fy - 1, 3, 3, c[1]); s.px(fx, fy, c[3]); s.px(fx - 1, fy - 1, c[2])
    s.outline_outside(INK)
    if flip:
        s.a = s.a[:, ::-1].copy()
    cv.rect(x + 2, y + 11, 18, 1, C("#0d0b16", 0.25))
    cv.paste(s, x, y)
