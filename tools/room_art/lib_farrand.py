"""Shared look of the after-hours festival on Farrand Field (rooms F01-F06).

Everything paints at 1:1 game pixels on pixel.Canvas, in the same style as the approved rooms
(clean colour clusters, ink outlines on props, warm bulbs against cool night shadow). Room scripts
using it: build_f01.py (cable walk), build_f02.py (volunteer tent), build_f03.py (food court);
battle scripts build_battle_f01/f02/f03.py show how the battle helpers are used.

Ground:      lawn (mown stripes, tufts), trodden_patch, puddle, litter, plywood_deck, mat_tile,
             mat_walkway, mat_path_vertical, tape_arrow, cable_run, cable_ramp_vertical,
             cable_ramp_horizontal, blob_mask, straw_bed (food court straw), woodchip, queue_marks
Skyline:     farrand_sky (dusk + Flatirons, tiled), treeline_back, back_tree, far_hedge,
             distant_stage (main stage glow with truss lamps), light_tower
Lights:      festoon (string lights; returns bulb points for twinkle layers), bulb, light_pool,
             festoon_occluders (overhead strings cut into y-sorted occluder pieces)
Structures:  peaked_tent (canvas marquee, striped roof, valance, optional frame-tent ridge),
             scallop_valance, canvas_wall, pvc_window, stone_wall_side (gate piers with lanterns),
             heras_fence_side, food_truck (side-on, open hatch with awning or shuttered),
             market_stall (timber stall with striped canopy), kiosk, menu_board, end_face
Props:       festoon_pole (lamp), crowd_barrier (rail), traffic_cone, hay_bales, trestle_table,
             picnic_table, a_frame_sign, cable_cart, soup_cart, half_barrel_planter (with optional
             festoon mast), wheelie_bins, cooler, crate, water_jug, chair_stack, hivis_vest
Battle:      battle_grass_rgb, battle_mats_rgb, barrier_texture, cone_sprite, string_across,
             field_treeline, end_face (closes off a side-on truck plane)
Palettes:    GRASS, STRAW, STRAW_BED, BARK, DIRT, MAT, CANVAS, RED, TEAL_C, HAZARD, CONE, REFLECT,
             STEEL, PLY, HAY, BULB, GREEN_TAPE, TRUCK_TEAL/CREAM/PINK/MUSTARD, CHALK, STRIPE_TRIM

Layout notes for the other Farrand rooms: keepsake pickups glint on the floor at fixed points that
are not in rooms.json (F03 (748, 302), F05 (748, 294)); keep those spots free of props and occluders.
The shared fauna sheet gets moth, bat, fox and raccoon from fauna_extra_farrand.py.
"""
import numpy as np
from PIL import Image
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, LEAF, MUM, ground_shadow

# --- palettes (painted bright and warm; the world tint cools them) ---------------------------
GRASS = ["#1c2a24", "#25382d", "#304736", "#3b563f", "#486648", "#5a7850", "#6f8a5a", "#88a066"]
STRAW = ["#2f2a24", "#463d30", "#5e523c", "#776948", "#918055", "#a99868"]
DIRT = ["#251d1e", "#352a28", "#4a3a32", "#5d4a3c", "#715a48"]
MAT = ["#1c2020", "#2a302e", "#3a423e", "#4a544e", "#58625a", "#6c766a", "#86907e"]
CANVAS = ["#4a443f", "#6e655c", "#918574", "#b1a38c", "#cbbda3", "#e0d4bb", "#f0e7d2"]
RED = ["#33141a", "#521e26", "#702a32", "#8e3a40", "#a84c4c", "#c4665a"]
TEAL_C = ["#18282c", "#22393c", "#2e4f50", "#3e6663", "#56837a", "#78a596"]
HAZARD = ["#1a1720", "#2a2630", "#b88a2a", "#e0b23a", "#f2cf5c"]
CONE = ["#3e1610", "#7a2a16", "#b8461e", "#e0662c", "#f2904a", "#f6b67a"]
REFLECT = ["#a8a8b0", "#d8d8dc", "#f2f2ee"]
STEEL = ["#1c1d27", "#2e303c", "#454857", "#646878", "#8a8e9c", "#b4b8c4"]
PLY = ["#3a2a22", "#5a4232", "#7a5c42", "#987552", "#b48e64", "#cba57a"]
HAY = ["#3e3020", "#5e4a2a", "#806636", "#a08444", "#bca252", "#d4bc6c"]
BULB = ["#7a4a24", "#e9a84a", "#f6cf7a", "#fff0c4"]
WIRE = "#1a1418"
GREEN_TAPE = ["#2a6a44", "#3e9a5c", "#62c47c"]
INK = "#171a2b"


def _rng(seed):
    return np.random.default_rng(abs(int(seed)))


# --- ground -----------------------------------------------------------------------------------
def _soft_field(w, h, cell, rng):
    """Low-frequency value noise in 0..1 (bilinear upscale of a coarse random grid)."""
    gw, gh = max(2, w // cell + 2), max(2, h // cell + 2)
    g = rng.random((gh, gw)).astype(np.float32)
    img = Image.fromarray((g * 255).astype(np.uint8), "L").resize((gw * cell, gh * cell), Image.BILINEAR)
    return np.array(img)[:h, :w].astype(np.float32) / 255.0


def lawn(cv, x, y, w, h, seed=0, pal=GRASS, tufts=1.0, clover=0.0, leaves=0.0, mask=None, base=3, stripes=None):
    """Night lawn: broad tone patches, then fan-shaped tufts of blades (lit tips, dark foot)
    spaced out so each reads as a clump. Clumps grow a little toward the bottom (perspective).
    mask (canvas-sized bool) limits where grass is painted."""
    rng = _rng(seed)
    region = np.zeros((cv.h, cv.w), bool)
    region[max(0, y):y + h, max(0, x):x + w] = True
    if mask is not None:
        region &= mask
    field = _soft_field(cv.w, cv.h, 34, rng) * 0.7 + _soft_field(cv.w, cv.h, 11, rng) * 0.3
    if stripes:
        # mowing stripes: alternating bands across the field, edges ruffled by the noise
        period, slope = stripes
        ys, xs = np.mgrid[0:cv.h, 0:cv.w]
        phase = ((ys - xs * slope) / period + field * 0.35) % 1.0
        field = np.where(phase < 0.5, 0.7, 0.45) + (field - 0.5) * 0.45
    tones = np.digitize(field, [0.4, 0.62])  # 0 shadowed, 1 base, 2 lit
    for i, c in enumerate([pal[base - 1], pal[base], pal[base + 1]]):
        cv.fill_mask(region & (tones == i), c)

    def clump(cx, cy, size, hi, mid, lo):
        n = int(rng.integers(3, 6))
        for b in range(n):
            dx = b - n // 2
            bh = size - abs(dx) + int(rng.integers(0, 2))
            lean = 0.45 * dx + rng.uniform(-0.3, 0.3)
            for k in range(max(1, bh)):
                px_ = int(round(cx + dx + lean * k / max(1, bh)))
                py_ = cy - k
                if 0 <= px_ < cv.w and 0 <= py_ < cv.h and region[py_, px_]:
                    cv.px(px_, py_, hi if k >= bh - 1 else mid)
        if 0 <= cy + 1 < cv.h and region[cy + 1, cx]:
            cv.hline(cx - n // 2, cy + 1, n, lo)

    # Clumps on a jittered grid so they never clot into speckle.
    step_x, step_y = 11, 7
    for gy in range(y, y + h, step_y):
        t = (gy - y) / max(1, h)
        for gx in range(x + (gy // step_y % 2) * step_x // 2, x + w, step_x):
            if rng.random() > 0.72 * tufts:
                continue
            cx = gx + int(rng.integers(0, step_x)); cy = gy + int(rng.integers(0, step_y))
            if not (0 <= cx < cv.w and 0 <= cy < cv.h) or not region[cy, cx]:
                continue
            size = 2 + int(rng.random() < 0.45 + 0.35 * t) + int(rng.random() < 0.2 * t)
            tone = tones[cy, cx]
            r = rng.random()
            if r < 0.22:   # shadow clump
                clump(cx, cy, size, pal[base], pal[base - 1], pal[base - 2])
            else:
                hi = pal[base + 2 + tone // 2] if r < 0.85 else pal[base + 3 + tone // 2]
                clump(cx, cy, size, hi, pal[base + 1 + tone // 2], pal[base - 1])
    # clover heads / tiny flowers and fallen leaves
    for _ in range(int(w * h * clover / 400)):
        cx_, cy_ = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        if 0 <= cx_ < cv.w - 1 and 0 <= cy_ < cv.h - 1 and region[cy_, cx_]:
            c = ["#d8d4c0", "#e8d27a", "#c8b0d8"][int(rng.integers(3))]
            cv.px(cx_, cy_, c); cv.px(cx_ + 1, cy_, shade(c, -0.25)); cv.px(cx_, cy_ + 1, pal[base - 1])
    for _ in range(int(w * h * leaves / 400)):
        lx, ly = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        if 0 <= lx < cv.w - 1 and 0 <= ly < cv.h and region[ly, lx]:
            c = ["#c8682e", "#a83c32", "#d9a441", "#8c4a2a"][int(rng.integers(4))]
            cv.px(lx, ly, c); cv.px(lx + 1, ly, shade(c, -0.2))
            if rng.random() < 0.4:
                cv.px(lx, ly - 1, shade(c, 0.15))


def trodden_patch(cv, cx, cy, rx, ry, seed=0, mask=None, strength=1.0):
    """Grass worn down by feet: a ragged olive-brown patch with flattened straw clumps and a
    few bare-earth scuffs in the middle; low contrast so it reads as worn lawn, not a stain."""
    rng = _rng(seed)
    field = _soft_field(cv.w, cv.h, 9, rng)
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    d = ((xs - cx) / max(1, rx)) ** 2 + ((ys - cy) / max(1, ry)) ** 2
    worn = (d < 1) & (field > 0.25 + 0.6 * d / strength)
    if mask is not None:
        worn &= mask
    cv.fill_mask(worn, "#3e4a30")
    cv.fill_mask(worn & (field > 0.55 + 0.3 * d), "#4c5234")
    bare = worn & (d < 0.22) & (field > 0.8)
    cv.fill_mask(bare, DIRT[3])
    cv.fill_mask(bare & (field > 0.85), DIRT[4])
    for _ in range(int(rx * ry / 10 * strength)):
        a = rng.uniform(0, 2 * np.pi); r = np.sqrt(rng.random())
        px_, py_ = int(cx + np.cos(a) * r * rx), int(cy + np.sin(a) * r * ry)
        if 0 <= px_ < cv.w - 3 and 0 <= py_ < cv.h - 1 and worn[py_, px_]:
            c = STRAW[4] if rng.random() < 0.45 else STRAW[3]
            n = int(rng.integers(2, 4))
            for k in range(n):
                cv.px(px_ + k, py_ - (1 if k == n - 1 else 0), c)
            cv.px(px_, py_ + 1, "#2f3a26")


def puddle(cv, cx, cy, rx, ry, seed=0, reflect=("#f6cf7a",), sky=("#1e2840", "#2c3d5e", "#4d6488")):
    """Rainwater lying in a dip in the lawn or on the mats: ragged-edged and a little broken up, dusk
    sky reflected as slate-blue bands (darker toward us) with a few ripple glints, a pale far lip,
    wet dark grass round it, grass blades poking over the near rim, and short lamp streaks (not bars)."""
    rng = _rng(seed)
    field = _soft_field(cv.w, cv.h, 4, rng)
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    d = ((xs - cx) / max(1, rx)) ** 2 + ((ys - cy) / max(1, ry)) ** 2
    water = d + (field - 0.5) * 0.85 < 1
    wet = (d + (field - 0.5) * 0.85 < 1.6) & ~water
    cv.fill_mask(wet, C("#0d0b16", 0.3))
    rel = (ys - (cy - ry)) / max(1, 2 * ry)
    cv.fill_mask(water & (rel >= 0.55), sky[0])
    cv.fill_mask(water & (rel < 0.55), sky[1])
    cv.fill_mask(water & (rel < 0.28), sky[2])
    far_lip = np.zeros_like(water)
    far_lip[:-1] = water[1:] & ~water[:-1]
    near_lip = np.zeros_like(water)
    near_lip[1:] = water[:-1] & ~water[1:]
    cv.fill_mask(far_lip, "#7d93a8")
    cv.fill_mask(near_lip, "#141a24")
    # ripple glints: short pale dashes scattered over the surface
    for _ in range(max(3, rx // 4)):
        gx = cx + int(rng.integers(-rx, rx + 1)); gy = cy + int(rng.integers(-ry, ry + 1))
        if 0 <= gy < cv.h and 0 <= gx + 2 < cv.w and water[gy, gx] and water[gy, gx + 2]:
            cv.px(gx, gy, sky[2]); cv.px(gx + 1, gy, sky[2])
    # lamp light: a short broken vertical streak, not a bar
    for c in reflect:
        sx = cx + int(rng.integers(-rx // 2, rx // 2 + 1))
        for k in range(ry + 1):
            yy = cy - ry // 2 + k
            if 0 <= yy < cv.h and 0 <= sx < cv.w and water[yy, sx] and k % 3 != 2:
                cv.px(sx, yy, mix(c, sky[1], 0.35 + 0.15 * k))
                if k == 0 and sx + 1 < cv.w and water[yy, sx + 1]: cv.px(sx + 1, yy, mix(c, sky[1], 0.55))
    # grass blades standing over the near rim
    blades = ("#2c4a3c", "#3d6048", "#4d7a56")
    for _ in range(max(4, rx // 2)):
        bx = cx + int(rng.integers(-rx, rx + 1))
        col = np.where(water[:, bx])[0] if 0 <= bx < cv.w else []
        if len(col) == 0: continue
        by = int(col.max())
        tall = int(rng.integers(2, 5))
        for k in range(tall):
            if 0 <= by - k < cv.h: cv.px(bx, by - k, blades[(k + bx) % 3])


def litter(cv, x, y, kind, seed=0):
    """Small things dropped on the lawn, each readable: cup, wristband, flyer, bottle cap."""
    if kind == "cup":
        cv.rect(x, y, 3, 4, "#e6e2d8"); cv.hline(x, y + 1, 3, "#c84a3c"); cv.px(x + 2, y + 3, "#a8a49a")
        cv.px(x, y + 4, C("#0d0b16", 0.4)); cv.px(x + 1, y + 4, C("#0d0b16", 0.4))
    elif kind == "cup_down":
        cv.rect(x, y, 4, 3, "#e6e2d8"); cv.vline(x + 1, y, 3, "#c84a3c"); cv.hline(x, y + 3, 4, C("#0d0b16", 0.4))
    elif kind == "band":
        for (dx, dy) in [(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (2, 2)]:
            cv.px(x + dx, y + dy, "#e05a8a")
        cv.px(x + 3, y + 2, "#f6cf7a")
    elif kind == "flyer":
        cv.poly([(x, y + 1), (x + 6, y), (x + 7, y + 4), (x + 1, y + 5)], "#e6d6b1")
        cv.hline(x + 2, y + 2, 3, "#7e3a30"); cv.px(x + 1, y + 6, C("#0d0b16", 0.3))
    elif kind == "cap":
        cv.px(x, y, "#c8c8d0"); cv.px(x + 1, y, "#8a8a92")


def plywood_deck(cv, x, y, w, h, sheet=(72, 26), seed=0, pal=None, mud=6, wet=3):
    """Plywood sheets laid on the grass as a working floor: pale boards with long grain streaks,
    screw heads along the seams, muddy footprints and rain-darkened patches. Returns a mask."""
    rng = _rng(seed)
    pal = pal or ["#3e3026", "#5a4636", "#7a6048", "#947a5a", "#ab926c", "#c4ab82"]
    sw, sh0 = sheet
    cv.rect(x, y, w, h, pal[1])
    rows, yy = [], y
    while yy < y + h:   # rows grow a little toward the viewer
        sh = int(round(sh0 * (0.85 + 0.35 * (yy - y) / max(1, h))))
        rows.append((yy, sh))
        yy += sh
    for row, (yy, sh) in enumerate(rows):
        off = (sw // 2) if row % 2 else 0
        for xx in range(x - off, x + w, sw):
            x0, x1 = max(x, xx), min(x + w, xx + sw)
            hh = min(sh, y + h - yy)
            if x1 - x0 < 3:
                continue
            tone = mix(pal[3], pal[4], float(rng.random()) * 0.6)
            cv.rect(x0, yy, x1 - x0 - 1, hh - 1, tone)
            cv.hline(x0, yy, x1 - x0 - 1, shade(tone, 0.1))
            for _ in range((x1 - x0) * hh // 60):
                gx, gy = x0 + int(rng.integers(0, max(1, x1 - x0 - 8))), yy + 2 + int(rng.integers(0, max(1, hh - 4)))
                cv.hline(gx, gy, int(rng.integers(5, 16)), shade(tone, float(rng.choice([-0.08, -0.05, 0.05]))))
            if rng.random() < 0.25:
                kx, ky = x0 + int(rng.integers(4, max(5, x1 - x0 - 6))), yy + int(rng.integers(3, max(4, hh - 3)))
                cv.rect(kx, ky, 3, 2, shade(tone, -0.18)); cv.px(kx + 1, ky, shade(tone, -0.3))
            for sx in range(x0 + 3, x1 - 2, 9):
                cv.px(sx, yy + 2, pal[1])
            cv.vline(x1 - 1, yy, hh, pal[0])
        cv.hline(x, yy + sh - 1, w, pal[0])
    for _ in range(wet):
        cx_, cy_ = x + int(rng.integers(10, w - 10)), y + int(rng.integers(6, h - 6))
        cv.ellipse(cx_ - 14, cy_ - 4, 28, 8, C("#2a2030", 0.22))
    for _ in range(mud):
        fx, fy = x + int(rng.integers(6, w - 12)), y + int(rng.integers(4, h - 6))
        for k in range(3):
            px_, py_ = fx + k * 7, fy + (k % 2) * 3
            cv.rect(px_, py_, 3, 2, C(DIRT[1], 0.6)); cv.px(px_ + 1, py_ + 2, C(DIRT[1], 0.5))
    mask = np.zeros((cv.h, cv.w), bool)
    mask[y:y + h, x:x + w] = True
    cv.hline(x, y + h, w, C("#0d0b16", 0.55)); cv.hline(x, y + h + 1, w, C("#0d0b16", 0.3))
    return mask


def mat_tile(cv, x, y, w, h, pal=MAT, seed=0, lit=0.0):
    """One ground-protection mat: dark joint, lit top lip, rows of raised tread studs
    (a lit pixel with its shadow), bolt heads in the corners, the odd smear of mud."""
    rng = _rng(seed)
    base = mix(pal[3], pal[4], float(rng.random()) * 0.35 + lit)
    cv.rect(x, y, w, h, pal[1])
    cv.rect(x + 1, y + 1, w - 2, h - 2, base)
    cv.hline(x + 1, y + 1, w - 2, shade(base, 0.16))
    cv.vline(x + 1, y + 1, h - 2, shade(base, 0.08))
    cv.hline(x + 1, y + h - 2, w - 2, shade(base, -0.2))
    stud = mix(base, pal[6], 0.55)
    under = pal[2]
    for row, yy in enumerate(range(y + 3, y + h - 3, 4)):
        for xx in range(x + 4 + (row % 2) * 3, x + w - 4, 6):
            cv.hline(xx, yy, 2, stud)
            cv.hline(xx, yy + 1, 2, under)
    for (bx, by) in [(x + 2, y + 2), (x + w - 3, y + 2), (x + 2, y + h - 3), (x + w - 3, y + h - 3)]:
        cv.px(bx, by, pal[6])
    for _ in range(int(rng.integers(0, 3))):
        sx, sy = x + int(rng.integers(3, max(4, w - 6))), y + int(rng.integers(3, max(4, h - 3)))
        cv.hline(sx, sy, int(rng.integers(2, 6)), DIRT[2] if rng.random() < 0.6 else GRASS[4])
        cv.px(sx + 1, sy + 1, DIRT[1])


def mat_walkway(cv, centre, width=44, mat=(46, 22), seed=0, pal=MAT, x0=None, x1=None):
    """A walkway of mats laid left to right; centre(x) gives the path's mid y. Each mat column
    steps to follow the curve, as real laid mats do. Returns a canvas-sized mask of the walkway."""
    rng = _rng(seed)
    mw, mh = mat
    rows = max(1, int(round(width / mh)))
    mask = np.zeros((cv.h, cv.w), bool)
    x0 = 0 if x0 is None else x0
    x1 = cv.w if x1 is None else x1
    off = int(rng.integers(0, mw))
    xx = x0 - off
    while xx < x1:
        cy = int(round(centre(xx + mw / 2)))
        top = cy - rows * mh // 2
        for r in range(rows):
            mat_tile(cv, xx, top + r * mh, mw, mh, pal, seed=int(rng.integers(1e6)))
        mask[max(0, top):top + rows * mh, max(0, xx):max(0, xx + mw)] = True
        # the mats' outer edge sits slightly proud of the grass: dark lip under, lit lip above
        cv.hline(xx, top - 1, mw, C("#0d0b16", 0.35))
        cv.hline(xx, top + rows * mh, mw, C("#0d0b16", 0.55))
        cv.hline(xx, top + rows * mh + 1, mw, C("#0d0b16", 0.25))
        xx += mw
    return mask


def mat_path_vertical(cv, centre_x, y0, y1, width=34, mat_h=20, seed=0, pal=MAT):
    """Mats laid away from the viewer (bottom to top); centre_x(y) gives the path's mid x."""
    rng = _rng(seed)
    mask = np.zeros((cv.h, cv.w), bool)
    yy = y1
    while yy > y0:
        h = mat_h if yy - mat_h >= y0 else yy - y0
        if h < 4:
            break
        cx = int(round(centre_x(yy - h / 2)))
        x = cx - width // 2
        mat_tile(cv, x, yy - h, width, h, pal, seed=int(rng.integers(1e6)))
        cv.vline(x - 1, yy - h, h, C("#0d0b16", 0.3)); cv.vline(x + width, yy - h, h, C("#0d0b16", 0.5))
        mask[yy - h:yy, max(0, x):x + width] = True
        yy -= h
    return mask


def tape_arrow(cv, x, y, direction=1, colour=GREEN_TAPE, crossed=False, length=14):
    """Gaffer-tape arrow stuck on a mat (direction 1 = right, -1 = left, 'up'). crossed adds a red X."""
    c0, c1 = colour[1], colour[2]
    if direction == "up":
        cv.rect(x - 1, y - length + 4, 3, length - 4, c0); cv.vline(x - 1, y - length + 4, length - 4, c1)
        cv.poly([(x - 4, y - length + 5), (x + 1, y - length), (x + 5, y - length + 5)], c0)
        cv.hline(x - 2, y - length + 3, 4, c1)
    else:
        d = 1 if direction > 0 else -1
        tip = x + d * length
        cv.rect(min(x, tip - d * 4), y - 1, length - 4, 3, c0); cv.hline(min(x, tip - d * 4), y - 1, length - 4, c1)
        cv.poly([(tip - d * 5, y - 4), (tip, y), (tip - d * 5, y + 4)], c0)
        cv.line(tip - d * 5, y - 4, tip - d, y - 1, c1)
    if crossed:
        cx_ = x + (0 if direction == "up" else (length // 2) * (1 if direction == 1 else -1))
        cy_ = y - (length // 2 if direction == "up" else 0)
        for k in range(-4, 5):
            cv.px(cx_ + k, cy_ + k, "#d8483c"); cv.px(cx_ + k, cy_ - k, "#d8483c")
            cv.px(cx_ + k + 1, cy_ + k, "#a83030")


def cable_run(cv, points, count=3, seed=0, colours=("#1e1c24", "#2a2832", "#34303c", "#4a2424"), tape_every=60,
              spread=2):
    """A bundle of cables lying on the grass along a polyline: dark 1px lines with a lit top edge,
    drifting apart and back together, gaffer tape bands every so often."""
    rng = _rng(seed)
    pts = np.array(points, np.float32)
    seg = np.hypot(*(pts[1:] - pts[:-1]).T)
    total = float(seg.sum())
    n = max(2, int(total))
    s = np.linspace(0, total, n)
    cum = np.concatenate([[0], np.cumsum(seg)])
    xs = np.interp(s, cum, pts[:, 0]); ys = np.interp(s, cum, pts[:, 1])
    phase = rng.uniform(0, 6.3, count)
    for k in range(count):
        wob = np.round(np.sin(s / (23 + 7 * k) + phase[k]) * spread * 0.6 + (k - (count - 1) / 2) * 1.2).astype(int)
        col = colours[k % len(colours)]
        for i in range(n):
            px_, py_ = int(round(xs[i])), int(round(ys[i])) + wob[i]
            cv.px(px_, py_ + 1, C("#0d0b16", 0.45))
            cv.px(px_, py_, col)
            if (i + k * 3) % 5 < 2:
                cv.px(px_, py_, shade(col, 0.45))
    if tape_every:
        for d in np.arange(tape_every * 0.5, total, tape_every):
            i = int(d)
            px_, py_ = int(round(xs[i])), int(round(ys[i]))
            c = "#8c8e98" if rng.random() < 0.6 else HAZARD[3]
            cv.rect(px_ - 1, py_ - count // 2 - 1, 3, count + 2, c)
            cv.vline(px_ - 1, py_ - count // 2 - 1, count + 2, shade(c, 0.25))
            cv.px(px_ + 1, py_ + count // 2 + 1, shade(c, -0.3))


def cable_ramp_vertical(cv, x, y0, y1, seed=0):
    """Cable protector laid across a left-right walkway: black bevels, yellow lid down the middle."""
    w = 12
    cv.rect(x - 1, y0 - 1, w + 2, y1 - y0 + 3, C("#0d0b16", 0.45))
    cv.rect(x, y0, w, y1 - y0, HAZARD[1])
    cv.vline(x, y0, y1 - y0, HAZARD[0]); cv.vline(x + 1, y0, y1 - y0, "#3a3644")
    cv.vline(x + w - 1, y0, y1 - y0, HAZARD[0]); cv.vline(x + w - 2, y0, y1 - y0, "#24212c")
    for yy in range(y0 + 1, y1 - 1, 3):
        cv.px(x + 2, yy, "#4a4656"); cv.px(x + w - 3, yy + 1, "#14121a")
    cv.rect(x + 4, y0, 4, y1 - y0, HAZARD[3])
    cv.vline(x + 4, y0, y1 - y0, HAZARD[4]); cv.vline(x + 7, y0, y1 - y0, HAZARD[2])
    for yy in range(y0 + 4, y1 - 2, 8):
        cv.hline(x + 4, yy, 4, HAZARD[2])
    cv.hline(x, y0, w, "#4a4656"); cv.hline(x, y1 - 1, w, HAZARD[0])


def cable_ramp_horizontal(cv, x0, x1, y, seed=0):
    """Cable protector laid across a path that runs away from the viewer: lit back slope,
    yellow lid, darker front slope facing us."""
    cv.rect(x0 - 1, y - 1, x1 - x0 + 2, 10, C("#0d0b16", 0.45))
    cv.rect(x0, y, x1 - x0, 2, "#3a3644")
    cv.rect(x0, y + 2, x1 - x0, 3, HAZARD[3]); cv.hline(x0, y + 2, x1 - x0, HAZARD[4])
    for xx in range(x0 + 5, x1 - 2, 8):
        cv.vline(xx, y + 2, 3, HAZARD[2])
    cv.rect(x0, y + 5, x1 - x0, 3, HAZARD[1]); cv.hline(x0, y + 7, x1 - x0, HAZARD[0])
    for xx in range(x0 + 1, x1 - 1, 3):
        cv.px(xx, y + 6, "#14121a")
    cv.vline(x0, y, 8, HAZARD[0]); cv.vline(x1 - 1, y, 8, HAZARD[0])


# --- lights -----------------------------------------------------------------------------------
def bulb(cv, x, y, c=None, glow=True):
    """A festoon bulb hanging from the wire at (x, y): dark socket, 2x2 glass with a hot centre
    and a faint halo. Returns the glass centre for a twinkle point."""
    c = c or BULB[2]
    if glow:
        cv.rect(x - 2, y, 6, 6, C(c, 0.12))
        cv.rect(x - 1, y + 1, 4, 4, C(c, 0.12))
    cv.px(x, y, WIRE)
    cv.rect(x, y + 1, 2, 2, c)
    cv.px(x, y + 1, shade(c, 0.55))
    cv.px(x + 1, y + 2, shade(c, -0.25))
    return (x, y + 1)


def festoon(cv, x0, y0, x1, y1, sag=12, every=9, seed=0, colours=None, glow=True):
    """String lights between two points: a sagging wire with bulbs. Returns twinkle points
    [x, y, hex, size] for the room/battle layer."""
    rng = _rng(seed)
    colours = colours or [BULB[2], BULB[2], BULB[2], BULB[3], "#f2a0a0", "#a8d8c8"]
    n = max(2, int(max(abs(x1 - x0), abs(y1 - y0))))
    pts = []
    prev = None
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        p = (int(round(x)), int(round(y)))
        if p != prev:
            cv.px(p[0], p[1], WIRE)
        prev = p
        if i % every == every // 2 and 0 < i < n:
            c = colours[int(rng.integers(len(colours)))]
            bx, by = bulb(cv, p[0], p[1], c, glow)
            pts.append([bx, by, c.lstrip("#"), 1])
    return pts


def light_pool(cv, cx, cy, rx, ry, color="#f6cf7a", strength=0.18, steps=3, mask=None):
    """Stepped warm pool on the ground (concentric bands), optionally limited by a mask."""
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    d = np.sqrt(((xs - cx) / max(1, rx)) ** 2 + ((ys - cy) / max(1, ry)) ** 2)
    for i in range(steps):
        f = 1 - i / steps
        m = d < f
        if mask is not None:
            m &= mask
        cv.fill_mask(m, C(color, strength / steps))


# --- skyline ----------------------------------------------------------------------------------
def farrand_sky(width, height, panels=(0, 1, 0), offset=0, scale=2.0, stars=40, seed=3):
    """Dusk sky with the Flatirons tiled from the title painting: panels alternate plain and
    mirrored (1). Put trees or tents over the joins. A few early stars at the top."""
    from sky import flatirons_panel
    panel = flatirons_panel(scale)
    ph, pw = panel.shape[:2]
    sky = np.zeros((height, width, 4), np.float32)
    sky[..., 3] = 1
    top = height - ph - 22
    row_colour = np.median(panel[:, :6, :3], axis=1)
    for yy in range(height):
        sky[yy, :, :3] = row_colour[min(ph - 1, max(0, yy - top))]
    x = -offset
    i = 0
    while x < width:
        src = panel[:, ::-1] if panels[i % len(panels)] else panel
        x0, x1 = max(0, x), min(width, x + pw)
        y0 = max(0, top)
        if x1 > x0:
            sky[y0:top + ph, x0:x1] = src[max(0, -top):, x0 - x:x1 - x]
        x += pw
        i += 1
    rng = _rng(seed)
    for _ in range(stars):
        sx, sy = int(rng.integers(0, width)), int(rng.integers(0, max(1, top + 30)))
        if sky[sy, sx, :3].mean() < 0.42:
            sky[sy, sx, :3] = C("#e8e0f0" if rng.random() < 0.6 else "#f6dca0")[:3]
    return sky, top


def back_tree(height, cell=5, brightness=0.62, saturation=0.8, seed=0, colors=28):
    """A big field-edge tree from the atlas, dimmed for distance and night (RGBA array)."""
    from midlib import sprite_from_cell
    return sprite_from_cell(cell, height=height, colors=colors, brightness=brightness, saturation=saturation)


def treeline_back(cv, x0, x1, base, seed=0, heights=(70, 110), gap=(50, 90), cells=(5, 6, 5), skip=()):
    """A row of dark field-edge trees along the back of the lawn, their feet hidden by the
    far hedge. skip: (xa, xb) spans left open (for a tent or the stage)."""
    rng = _rng(seed)
    x = x0
    i = 0
    while x < x1:
        if any(a <= x <= b for a, b in skip):
            x += 20
            continue
        h = int(rng.integers(*heights))
        spr = back_tree(h, cells[i % len(cells)], brightness=0.5 + 0.12 * rng.random(), seed=seed + i)
        cv.paste(spr, x - spr.shape[1] // 2, base - spr.shape[0] + int(rng.integers(0, 6)))
        x += int(rng.integers(*gap))
        i += 1


def far_hedge(cv, x0, x1, y, seed=0, height=8):
    """The far edge of the field: a dark hedge of rounded clumps with a few lit windows behind."""
    rng = _rng(seed)
    for x in range(x0 - 6, x1 + 6, 5):
        hh = int(rng.integers(height - 3, height + 3))
        cv.ellipse(x, y - hh, int(rng.integers(8, 13)), hh * 2, "#1a2420" if rng.random() < 0.6 else "#1f2b24")
    for x in range(x0, x1, 4):
        if rng.random() < 0.3:
            cv.px(x, y - int(rng.integers(height - 3, height)), "#2b3a2f")
    cv.rect(x0, y, x1 - x0, 2, "#141c19")


def light_tower(cv, x, base, height, seed=0, lamps=2):
    """A scaffold delay/light tower in silhouette: lattice mast, a lamp bar at the top."""
    rng = _rng(seed)
    w = 7
    top = base - height
    cv.vline(x, top, height, "#1a1824"); cv.vline(x + w - 1, top, height, "#1a1824")
    for yy in range(top + 2, base, 5):
        cv.line(x, yy, x + w - 1, yy + 4, "#232031")
        cv.hline(x, yy, w, "#1d1b28")
    cv.rect(x - 4, top - 4, w + 8, 4, "#1a1824")
    pts = []
    for k in range(lamps):
        lx = x - 2 + k * (w + 4) // max(1, lamps - 1) if lamps > 1 else x + w // 2
        cv.rect(lx, top - 3, 2, 2, "#fff0c4")
        pts.append([lx, top - 3])
    return pts


def distant_stage(cv, cx, base, w=180, h=70, seed=0):
    """The main stage seen from far across the field: a halo of light in the haze, an arched
    black truss roof hung with lamps, a glowing back wall washed pink and violet, the warm lit
    deck with gear silhouettes, PA hangs and scaffold wings. Returns lamp points on the truss."""
    rng = _rng(seed)
    x0 = cx - w // 2
    top = base - h
    # halo in the air above and around the stage
    for (r, a) in [(w // 2 + 40, 0.07), (w // 2 + 20, 0.08), (w // 2, 0.1)]:
        cv.ellipse(cx - r, top - r // 4, r * 2, r // 2 + h, C("#c88ab0", a))
    # back wall: stepped wash, warm near the deck
    ox0, ox1, oy0, oy1 = x0 + 12, x0 + w - 12, top + 12, base - 9
    bands = ["#3a2040", "#552a56", "#7a3a66", "#a2506e", "#c86a6a"]
    for yy in range(oy0, oy1):
        t = (yy - oy0) / max(1, oy1 - oy0)
        cv.hline(ox0, yy, ox1 - ox0, bands[min(len(bands) - 1, int(t * len(bands)))])
    # LED screen panel in the middle, a pale shape on it
    sw, sh = w // 3, (oy1 - oy0) // 2
    sx, sy = cx - sw // 2, oy0 + 4
    cv.rect(sx - 1, sy - 1, sw + 2, sh + 2, "#1a1020")
    cv.rect(sx, sy, sw, sh, "#3a3070")
    for k in range(0, sw, 3):
        cv.vline(sx + k, sy, sh, C("#1a1020", 0.35))
    cv.poly([(sx + 4, sy + sh - 2), (sx + sw // 3, sy + 4), (sx + sw // 2, sy + sh - 6), (sx + 2 * sw // 3, sy + 6), (sx + sw - 4, sy + sh - 2)], "#6a5aa8")
    # light shafts from the truss
    for k, lx in enumerate(range(ox0 + 10, ox1 - 6, (ox1 - ox0) // 5)):
        col = ["#fff0c4", "#f0a0d0", "#a8c8ff"][k % 3]
        for yy in range(oy0, oy1):
            spread = (yy - oy0) // 4
            cv.hline(lx - spread // 2 + (k % 2) * (yy - oy0) // 6, yy, max(1, spread // 2 + 1), C(col, 0.13))
    # deck: warm lit floor, dark front, gear in silhouette
    cv.rect(x0 + 6, base - 10, w - 12, 3, "#e9a84a"); cv.hline(x0 + 6, base - 10, w - 12, "#f6cf7a")
    cv.rect(x0 + 6, base - 7, w - 12, 7, "#1c121c")
    for k in range(x0 + 10, x0 + w - 10, 6):
        cv.vline(k, base - 6, 5, "#24182a")
    for (gx, gw, gh) in [(cx - 20, 22, 8), (cx - 50, 8, 10), (cx + 38, 8, 10), (cx + 6, 6, 5), (cx - 34, 5, 4)]:
        cv.rect(gx, base - 10 - gh, gw, gh, "#1c121c")
        cv.hline(gx, base - 10 - gh, gw, "#3a2a3a")
    cv.vline(cx - 2, base - 22, 12, "#1c121c"); cv.px(cx - 2, base - 23, "#3a2a3a")  # mic stand
    # roof: arched truss with its lit underside and lamps
    pts = []
    for xx in range(x0 - 6, x0 + w + 6):
        t = (xx - x0) / w
        yy = top + int(round(9 * (2 * t - 1) ** 2))
        cv.vline(xx, yy, 7, "#16141e")
        cv.px(xx, yy + 7, "#4a3448")
        if xx % 4 == 0:
            cv.px(xx, yy + 2, "#2e2a3a"); cv.px(xx + 1, yy + 4, "#2e2a3a")
    for xx in range(x0 + 8, x0 + w - 6, 11):
        t = (xx - x0) / w
        yy = top + int(round(9 * (2 * t - 1) ** 2)) + 8
        c = "#fff0c4" if rng.random() < 0.6 else "#f0a0d0"
        cv.rect(xx, yy, 2, 2, c)
        pts.append([xx, yy])
    # PA hangs and scaffold wings
    for px_ in (x0 + 2, x0 + w - 10):
        cv.rect(px_, top + 12, 8, 26, "#121018")
        for yy in range(top + 13, top + 38, 4):
            cv.hline(px_ + 1, yy, 6, "#22202c")
    for tx in (x0 - 12, x0 + w + 4):
        cv.rect(tx, top - 4, 8, h + 4, "#16141e")
        for yy in range(top - 2, base, 5):
            cv.line(tx, yy, tx + 7, yy + 4, "#262232")
    return pts


# --- structures -------------------------------------------------------------------------------
def scallop_valance(cv, x, y, w, depth=8, pal_a=RED, pal_b=CANVAS, stripe=8):
    """Striped valance with scalloped hem along a canopy edge."""
    for i, sx in enumerate(range(x, x + w, stripe)):
        sw = min(stripe, x + w - sx)
        a = pal_a if i % 2 == 0 else pal_b
        cv.rect(sx, y, sw, depth, a[3] if a is pal_a else a[4])
        cv.vline(sx, y, depth, a[4] if a is pal_a else a[5])
        cv.hline(sx, y + depth - 2, sw, a[2] if a is pal_a else a[3])
        # scallop
        cv.rect(sx + 1, y + depth, max(1, sw - 2), 1, a[3] if a is pal_a else a[4])
        cv.rect(sx + 2, y + depth + 1, max(1, sw - 4), 1, a[2] if a is pal_a else a[3])
    cv.hline(x, y, w, shade(pal_b[5], 0.1))


def canvas_wall(cv, x, y, w, h, pal=CANVAS, seed=0, panel=24, lit=0.0):
    """Tent canvas: vertical panels with seams, soft vertical folds, a damp darker hem."""
    rng = _rng(seed)
    for xx in range(x, x + w):
        k = (xx - x) % panel
        tone = pal[4] if k < panel * 0.45 else pal[3] if k < panel * 0.85 else pal[2]
        cv.vline(xx, y, h, tone)
        if k == 0:
            cv.vline(xx, y, h, pal[2])
            cv.vline(xx + 1, y, h, pal[5])
    for _ in range(w // 9):
        fx = x + int(rng.integers(0, w))
        cv.vline(fx, y + int(rng.integers(0, h // 2)), int(rng.integers(h // 4, h // 2 + 1)), C(pal[1], 0.25))
    cv.rect(x, y + h - 3, w, 3, C(DIRT[2], 0.4))


def pvc_window(cv, x, y, w, h, lit=True):
    """Arched clear-PVC marquee window: canvas frame, mullions, warm light from inside."""
    r = w // 2
    cv.rect(x - 1, y + r - 1, w + 2, h - r + 2, CANVAS[1])
    cv.ellipse(x - 1, y - 1, w + 2, w + 2, CANVAS[1])
    pal = [BULB[1], BULB[2], BULB[3]] if lit else ["#2c3352", "#3e4a6e", "#6476a0"]
    cv.ellipse(x, y, w, w, pal[2])
    cv.rect(x, y + r, w, h - r, pal[1])
    cv.rect(x, y + h - h // 3, w, h // 3, pal[0])
    cv.vline(x + r, y, h, CANVAS[1])
    for yy in range(y + r, y + h, max(4, (h - r) // 2)):
        cv.hline(x, yy, w, CANVAS[1])
    if lit:
        cv.px(x + 1, y + r, "#fffaf0")


def peaked_tent(w, eave_h, peak_h, pal=CANVAS, stripe=RED, open_front=True, seed=0, interior=None,
                valance_text=None, depth=26, poles=None, windows=True, ropes=True, ridge=0):
    """A festival marquee seen from the front: canvas walls with arched PVC windows (or an open
    front showing interior(cv, x, y, w, h)), a red-and-cream panelled roof rising to a finial with
    a pennant, a scalloped valance, guy ropes pegged out at the sides.
    Returns (Canvas, anchor_x, anchor_y) with the anchor on the middle of the front edge."""
    rng = _rng(seed)
    side = 22 if ropes else 8
    W, H = w + side * 2, eave_h + peak_h + 14
    cv = Canvas(W, H, seed=seed)
    ox = side
    base = H - 3
    eave = base - eave_h
    ground_shadow(cv, ox + w // 2, base, w // 2 + 6, 3, alpha=0.42)
    if open_front:
        canvas_wall(cv, ox + 2, eave + 4, w - 4, eave_h - depth // 2 - 4, pal=[shade(c, -0.35) for c in pal], seed=seed, panel=30)
        cv.rect(ox + 2, base - depth // 2, w - 4, depth // 2, mix(DIRT[2], pal[2], 0.3))
        for yy in range(base - depth // 2, base, 3):
            cv.hline(ox + 2, yy, w - 4, C(DIRT[1], 0.35))
        if interior:
            interior(cv, ox + 2, eave + 4, w - 4, eave_h - 4)
    else:
        canvas_wall(cv, ox, eave, w, eave_h, pal=pal, seed=seed)
        # lower wall darker away from the lights, a mud line at the hem
        cv.rect(ox, base - eave_h // 3, w, eave_h // 3, C(pal[0], 0.18))
        if windows:
            nwin = max(2, w // 46)
            for i in range(nwin):
                wx = ox + int((i + 0.5) * w / nwin) - 7
                if abs(wx + 7 - (ox + w // 2)) < 26:
                    continue  # the door goes in the middle
                pvc_window(cv, wx, eave + 16, 14, 26, lit=rng.random() < 0.85)
    # roof: panels from the ridge (or peak) down to the eave, alternately red and cream
    peak = eave - peak_h
    cx = ox + w // 2
    r0, r1 = cx - ridge // 2, cx + ridge // 2
    e0, e1 = ox - 4, ox + w + 4
    eave_pts = list(range(e0, e1 + 1, 16))
    if eave_pts[-1] != e1:
        eave_pts.append(e1)
    to_ridge = lambda e: r0 + (e - e0) / (e1 - e0) * (r1 - r0)
    cv.poly([(e0 - 1, eave + 1), (r0, peak - 1), (r1, peak - 1), (e1 + 1, eave + 1)], OUT)
    for i in range(len(eave_pts) - 1):
        a, b = eave_pts[i], eave_pts[i + 1]
        col = stripe[3] if i % 2 == 0 else pal[4]
        mid = (a + b) / 2
        lit = 0.1 if mid < cx - w * 0.3 else 0.0 if mid < cx + w * 0.3 else -0.14
        cv.poly([(to_ridge(a), peak), (to_ridge(b), peak), (b, eave + 1), (a, eave + 1)], shade(col, lit))
    for e in eave_pts:
        cv.line(int(round(to_ridge(e))), peak + 1, e, eave, C(OUT, 0.3))
    if ridge:
        cv.hline(r0, peak, r1 - r0, pal[6]); cv.hline(r0, peak + 1, r1 - r0, C(pal[0], 0.3))
        # light catching the upper roof, damp sheen lower down
        cv.poly([(r0, peak + 2), (r1, peak + 2), (r1 + 4, peak + 6), (r0 - 4, peak + 6)], C(pal[6], 0.18))
    else:
        cv.vline(cx, peak, 3, pal[6])
    for fx in ([r0, r1] if ridge else [cx]):
        cv.rect(fx - 1, peak - 7, 3, 7, OUT); cv.px(fx, peak - 7, stripe[5])  # finial
        cv.poly([(fx + 1, peak - 7), (fx + 10, peak - 5), (fx + 1, peak - 3)], stripe[4])  # pennant
        cv.line(fx + 1, peak - 6, fx + 8, peak - 5, stripe[5])
    # valance
    scallop_valance(cv, ox - 4, eave, w + 8, depth=9, pal_a=stripe, pal_b=pal)
    if valance_text:
        tw = text_width(valance_text) + 8
        cv.rect(cx - tw // 2, eave + 1, tw, 9, OUT)
        cv.rect(cx - tw // 2 + 1, eave + 1, tw - 2, 8, "#211a26")
        text(cv, valance_text, cx - tw // 2 + 4, eave + 1, "#f6cd78")
    # poles
    poles = poles or [0, w // 3, 2 * w // 3, w - 3]
    for p in poles:
        px_ = ox + p
        cv.rect(px_, eave + 9, 3, base - eave - 9, OUT)
        cv.vline(px_ + 1, eave + 9, base - eave - 9, STEEL[4])
        cv.rect(px_ - 1, base - 2, 5, 2, STEEL[2])
    # guy ropes from the eave corners out to pegs
    if ropes:
        for s in (-1, 1):
            ex = ox - 4 if s < 0 else ox + w + 3
            for k, reach in enumerate((side - 3, side - 12)):
                gx = ex + s * reach
                cv.line(ex, eave + 4 + k * 10, gx, base - 1, "#cbbda3")
                cv.rect(gx - 1, base - 2, 2, 3, WOOD[2])
    return cv, ox + w // 2, base


def heras_fence_side(cv, x, y0, y1, seed=0, gap=None):
    """Temporary fence running away from the viewer along a room edge: mesh panels seen at a
    slant, green scrim with the festival's name stencilled, posts on rubber feet. gap=(ya, yb)
    leaves a gate opening with lantern posts and hazard tape on the open panel."""
    rng = _rng(seed)
    panel = 34
    for yy in range(y0, y1, panel):
        if gap and gap[0] - panel < yy <= gap[1] - 2:
            continue
        top = yy - 30
        # scrim: a slanted band between this post and the next
        for k in range(panel):
            sy = top + k
            cv.vline(x + 1 + k // 12, sy, 24, TEAL_C[1] if (k // 3) % 2 else TEAL_C[2])
        cv.vline(x + 1, top, 24 + panel - 1, TEAL_C[3])
        for k in range(0, panel, 6):
            cv.px(x + 2 + k // 12, top + k + 2, "#c8c8d0")  # cable ties
        # post and foot
        cv.rect(x - 1, top - 2, 3, 34, OUT); cv.vline(x, top - 1, 32, STEEL[4])
        cv.rect(x - 5, yy, 11, 5, OUT); cv.rect(x - 4, yy + 1, 9, 3, "#3a3644"); cv.hline(x - 4, yy + 1, 9, "#5a5666")
    if gap:
        for gy in gap:
            cv.rect(x - 2, gy - 40, 5, 42, OUT); cv.vline(x - 1, gy - 39, 40, STEEL[4]); cv.vline(x, gy - 39, 40, STEEL[3])
            cv.rect(x - 5, gy, 11, 5, OUT); cv.rect(x - 4, gy + 1, 9, 3, "#3a3644")
            cv.rect(x - 3, gy - 46, 7, 7, OUT); cv.rect(x - 2, gy - 45, 5, 5, BULB[2]); cv.px(x, gy - 44, BULB[3])
        # open gate panel swung back against the fence, hazard tape tied to it
        cv.line(x + 1, gap[0] - 34, x + 6, gap[0] - 20, STEEL[3])
        for k in range(0, 10, 2):
            cv.px(x + 2 + k // 2, gap[0] - 30 + k, HAZARD[3])


def stone_wall_side(cv, x, y0, y1, gap=None, seed=0, width=13):
    """Low sandstone wall running away from the viewer along a room edge (we see its coped top as
    a strip of stones), shrubs spilling over from beyond. gap=(ya, yb) opens a gateway flanked by
    two piers with lanterns. Returns the lantern points."""
    from facade import SANDSTONE, TRIM
    from props import shrub
    rng = _rng(seed)
    yy = y0
    while yy < y1:
        sh = int(rng.integers(6, 11))
        if gap and gap[0] - 8 < yy + sh and yy < gap[1] + 6:
            yy += sh
            continue
        tone = SANDSTONE[int(rng.choice([3, 3, 4, 2]))]
        cv.rect(x, yy, width, sh - 1, tone)
        cv.hline(x, yy, width, shade(tone, 0.12)); cv.vline(x, yy, sh - 1, shade(tone, 0.08))
        cv.hline(x, yy + sh - 1, width, SANDSTONE[0])
        cv.px(x + int(rng.integers(2, width - 2)), yy + int(rng.integers(1, max(2, sh - 2))), shade(tone, -0.12))
        yy += sh
    cv.vline(x + width, y0, y1 - y0, C("#0d0b16", 0.5)); cv.vline(x + width + 1, y0, y1 - y0, C("#0d0b16", 0.25))
    # shrubs beyond the wall (left of it)
    for sy in range(y0 - 10, y1, 13):
        if gap and gap[0] - 20 < sy < gap[1]:
            continue
        b = shrub(0, 0, 14, 14, seed=int(rng.integers(1e6)))
        cv.paste(b, x - 12, sy)
    pts = []
    if gap:
        for gy in gap:
            pw, ph = width + 4, 44
            px_ = x - 2
            top = gy - ph
            cv.rect(px_ - 1, top - 1, pw + 2, ph + 2, OUT)
            # pier: front face in ashlar, cap stone, lantern
            for k, ry in enumerate(range(top + 6, gy, 6)):
                tone = SANDSTONE[3] if k % 2 else SANDSTONE[4]
                cv.rect(px_, ry, pw, 5, tone); cv.hline(px_, ry, pw, shade(tone, 0.1)); cv.hline(px_, ry + 5, pw, SANDSTONE[1])
                cv.vline(px_ + (3 if k % 2 else 9), ry, 5, SANDSTONE[1])
            cv.rect(px_ - 2, top, pw + 4, 6, TRIM[2]); cv.hline(px_ - 2, top, pw + 4, TRIM[4]); cv.hline(px_ - 2, top + 5, pw + 4, TRIM[0])
            lx = px_ + pw // 2
            cv.rect(lx - 3, top - 11, 7, 10, OUT); cv.rect(lx - 2, top - 9, 5, 7, BULB[2]); cv.rect(lx - 1, top - 8, 3, 4, BULB[3])
            cv.poly([(lx - 4, top - 10), (lx, top - 14), (lx + 4, top - 10)], OUT)
            cv.rect(lx - 6, top - 12, 13, 12, C(BULB[2], 0.12))
            pts.append([lx, top - 6, "f6cf7a", 2])
    return pts


# --- props ------------------------------------------------------------------------------------
def festoon_pole(height=55, arm=10, seed=0, flip=False):
    """Timber festoon pole on a weighted foot, a short cross-arm and a caged bulb hanging from it.
    The bulb's centre sits height - 5 above the floor anchor, where the game puts the lamp light.
    Returns (Canvas, anchor_x, anchor_y, (bulb_x, bulb_y)) in canvas pixels."""
    w = 30
    H = height + 8
    cv = Canvas(w, H, seed=seed)
    d = -1 if flip else 1
    cx, base = w // 2 - 4 * d, H - 3
    lamp_y = base - (height - 5)
    ground_shadow(cv, cx, base, 7, 2)
    # weighted tyre foot
    cv.rect(cx - 6, base - 4, 13, 5, OUT); cv.rect(cx - 5, base - 3, 11, 3, "#2c2a34"); cv.hline(cx - 5, base - 3, 11, "#4a4656")
    cv.px(cx - 3, base - 2, "#3a3644"); cv.px(cx + 3, base - 2, "#3a3644")
    # post
    top = lamp_y - 10
    cv.rect(cx - 2, top, 5, base - 3 - top, OUT)
    cv.rect(cx - 1, top + 1, 3, base - 4 - top, WOOD[3])
    cv.vline(cx - 1, top + 1, base - 4 - top, WOOD[4]); cv.vline(cx + 1, top + 1, base - 4 - top, WOOD[2])
    for yy in range(top + 7, base - 6, 9):
        cv.px(cx, yy, WOOD[1])
    cv.rect(cx - 2, top - 1, 5, 2, IRON[2])
    # power cable taped down the post
    for yy in range(top + 6, base - 3):
        cv.px(cx - 2 * d, yy, WIRE)
    for yy in range(top + 14, base - 6, 13):
        cv.rect(cx - 2 * d - (1 if d > 0 else 0), yy, 2, 2, "#8c8e98")
    # cross-arm and hanging cage lamp
    ay = lamp_y - 7
    ax0 = cx if d > 0 else cx - arm - 1
    cv.rect(ax0, ay, arm + 2, 3, OUT); cv.hline(ax0 + 1, ay + 1, arm, WOOD[4])
    lx = cx + d * (arm - 1)
    cv.vline(lx, ay + 3, 1, WIRE)
    cv.rect(lx - 3, lamp_y - 3, 7, 8, C(BULB[2], 0.22))
    cv.rect(lx - 1, lamp_y - 2, 3, 5, BULB[2]); cv.vline(lx, lamp_y - 1, 2, BULB[3])
    cv.vline(lx - 2, lamp_y - 3, 6, IRON[1]); cv.vline(lx + 2, lamp_y - 3, 6, IRON[1])
    cv.hline(lx - 2, lamp_y - 3, 5, IRON[2]); cv.hline(lx - 1, lamp_y + 3, 3, IRON[1])
    cv.px(lx, lamp_y - 4, IRON[1])
    return cv, cx, base, (lx, lamp_y)


def crowd_barrier(width=150, height=26, seed=0, tape=True, sign=None):
    """A run of interlocking steel crowd barriers ("bike racks"): top rail, vertical bars,
    splayed feet, a strip of hazard tape tied along the top."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2, 2, alpha=0.32)
    seg = 50
    n = max(1, int(round(width / seg)))
    seg = width / n
    top = base - height
    for i in range(n):
        x0 = int(round(ox + i * seg)); x1 = int(round(ox + (i + 1) * seg)) - 2
        # bars
        for bx in range(x0 + 4, x1 - 2, 4):
            cv.vline(bx, top + 3, height - 9, OUT)
            cv.vline(bx + 1, top + 3, height - 9, STEEL[3])
        # frame
        cv.rect(x0, top, 3, height - 4, OUT); cv.vline(x0 + 1, top + 1, height - 6, STEEL[4])
        cv.rect(x1 - 2, top, 3, height - 4, OUT); cv.vline(x1 - 1, top + 1, height - 6, STEEL[3])
        cv.rect(x0, top, x1 - x0 + 1, 3, OUT); cv.hline(x0 + 1, top + 1, x1 - x0 - 1, STEEL[5])
        cv.rect(x0, base - 8, x1 - x0 + 1, 3, OUT); cv.hline(x0 + 1, base - 7, x1 - x0 - 1, STEEL[3])
        # flat feet
        for fx in (x0 - 2, x1 - 4):
            cv.rect(fx, base - 3, 9, 3, OUT); cv.hline(fx + 1, base - 2, 7, STEEL[2])
        # hook joint to the next section
        if i < n - 1:
            cv.rect(x1, top + 2, 3, 3, STEEL[2])
    if tape:
        y = top + 5
        for xx in range(ox, ox + width):
            yy = y + int(round(1.5 * np.sin(xx / 9.0)))
            c = HAZARD[3] if (xx // 5) % 2 == 0 else HAZARD[0]
            cv.px(xx, yy, c); cv.px(xx, yy + 1, shade(c, -0.2) if c == HAZARD[3] else HAZARD[1])
        # loose end fluttering
        cv.line(ox + width - 1, y, ox + width + 3, y + 6, HAZARD[3])
    if sign:
        sw = text_width(sign) + 8
        sx = ox + width // 2 - sw // 2
        cv.rect(sx, top + 7, sw, 11, OUT); cv.rect(sx + 1, top + 8, sw - 2, 9, "#e6d6b1")
        text(cv, sign, sx + 4, top + 8, "#7e3a30")
    return cv, ox + width // 2, base


def traffic_cone(cv, x, base, h=13, lean=0, tape=False):
    """A traffic cone standing at (x, base): square foot, reflective collar."""
    w = max(7, h * 3 // 5)
    cv.rect(x - w // 2 - 2, base - 2, w + 4, 3, OUT)
    cv.rect(x - w // 2 - 1, base - 2, w + 2, 2, CONE[1]); cv.hline(x - w // 2 - 1, base - 2, w + 2, CONE[3])
    for yy in range(h - 2):
        t = yy / max(1, h - 3)
        half = max(1, int(round((w / 2) * (1 - t * 0.8))))
        y = base - 3 - yy
        cx_ = x + int(round(lean * t))
        cv.hline(cx_ - half - 1, y, 1, OUT); cv.hline(cx_ + half + 1, y, 1, OUT)
        cv.hline(cx_ - half, y, half * 2 + 1, CONE[3])
        cv.px(cx_ - half, y, CONE[4]); cv.px(cx_ + half, y, CONE[2])
        if h * 0.35 < yy < h * 0.55:
            cv.hline(cx_ - half, y, half * 2 + 1, REFLECT[1]); cv.px(cx_ - half, y, REFLECT[2]); cv.px(cx_ + half, y, REFLECT[0])
    cv.hline(x + int(lean) - 1, base - h + 1, 3, OUT)


def hay_bales(width=90, height=30, seed=0, blanket=None):
    """Hay bale bench: square bales side by side, the lit top showing cut straw, the front face in
    shadow with straw ends, two twines around each, an optional folded blanket on top."""
    rng = _rng(seed)
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3, alpha=0.4)
    n = max(1, int(round(width / 44)))
    bw = width // n
    face = max(10, height // 2)
    top = base - height
    for i in range(n):
        x = ox + i * bw
        cv.rect(x, top + 1, bw - 1, height - 1, OUT)
        cv.rect(x + 1, top, bw - 3, 1, OUT)
        # top surface: lit, straw strokes running along the bale
        cv.rect(x + 1, top + 1, bw - 3, height - face - 1, HAY[4])
        for yy in range(top + 2, base - face - 1, 2):
            for _ in range(bw // 6):
                sx = x + 2 + int(rng.integers(0, bw - 7))
                cv.hline(sx, yy, int(rng.integers(2, 5)), HAY[5] if rng.random() < 0.5 else HAY[3])
        # front face: shadowed, cut straw ends as short vertical flecks
        cv.rect(x + 1, base - face, bw - 3, face - 1, HAY[2])
        cv.hline(x + 1, base - face, bw - 3, HAY[3])
        for _ in range(bw * face // 4):
            sx, sy = x + 2 + int(rng.integers(0, bw - 5)), base - face + 1 + int(rng.integers(0, face - 2))
            cv.vline(sx, sy, int(rng.integers(1, 3)), HAY[1] if rng.random() < 0.5 else HAY[3])
        cv.hline(x + 1, base - 2, bw - 3, HAY[1])
        # twine
        for tx in (x + bw // 3, x + 2 * bw // 3):
            cv.vline(tx, top + 1, height - 2, "#5a3a22")
            cv.vline(tx + 1, top + 1, height - face - 1, HAY[5])
        # straw poking out at the ends
        for _ in range(5):
            sy = top + int(rng.integers(2, height - 2))
            cv.px(x - 1, sy, HAY[3]); cv.px(x + bw - 1, sy + 1, HAY[3])
    if blanket:
        # a plaid blanket folded on the top face, one corner hanging over the front
        bx = ox + int(width * 0.5)
        bwid = min(26, width // 3)
        bh = height - face - 3
        by = top + 2
        cv.rect(bx - 1, by - 1, bwid + 2, bh + 2, OUT)
        cv.rect(bx, by, bwid, bh, blanket[3])
        for k in range(1, bwid, 5):
            cv.vline(bx + k, by, bh, blanket[2])
        for k in range(1, bh, 3):
            cv.hline(bx, by + k, bwid, blanket[4] if k % 2 else blanket[2])
        cv.hline(bx, by, bwid, blanket[5])
        hang = [(bx + bwid - 9, by + bh), (bx + bwid, by + bh), (bx + bwid, by + bh + 5), (bx + bwid - 5, by + bh + 7)]
        cv.poly([(p[0], p[1] + 1) for p in hang], OUT)
        cv.poly(hang, blanket[2])
        cv.vline(bx + bwid - 3, by + bh, 5, blanket[4])
    return cv, ox + width // 2, base


def trestle_table(width=150, height=30, cloth=None, seed=0, items=None, top_height=20):
    """Folding trestle table, optionally with a cloth; items(cv, x0, top, width) paints what is on it."""
    cv = Canvas(width + 6, height + 30, seed=seed)
    ox, base = 3, height + 26
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - top_height
    for lx in (ox + 4, ox + width - 8):
        cv.rect(lx, top + 3, 4, base - top - 3, OUT); cv.vline(lx + 1, top + 3, base - top - 4, STEEL[3])
        cv.rect(lx - 2, base - 2, 8, 2, OUT)
    cv.line(ox + 6, base - 4, ox + width - 6, top + 5, C(STEEL[1], 0.8))
    if cloth:
        cv.rect(ox, top - 1, width, 13, OUT)
        cv.rect(ox + 1, top, width - 2, 11, cloth[2]); cv.hline(ox + 1, top, width - 2, cloth[4])
        cv.hline(ox + 1, top + 1, width - 2, cloth[3])
        for fx in range(ox + 4, ox + width - 3, 7):
            cv.vline(fx, top + 4, 7, cloth[1])
        cv.hline(ox + 1, top + 10, width - 2, cloth[0])
    else:
        cv.rect(ox, top - 1, width, 5, OUT)
        cv.wood(ox + 1, top, width - 2, 3, PLY[3], plank=3, seed=seed)
        cv.hline(ox + 1, top, width - 2, PLY[5])
    if items:
        items(cv, ox, top, width)
    return cv, ox + width // 2, base


def picnic_table(width=140, height=30, seed=0, items=None):
    """Wooden picnic table with its two benches, seen from the front (long side)."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 30, seed=seed)
    ox, base = 4, height + 26
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    top = base - 22
    # far bench (behind the top, only its edge peeks)
    cv.rect(ox + 6, top - 5, width - 12, 4, OUT); cv.hline(ox + 7, top - 4, width - 14, PLY[3])
    # A-frame legs
    for lx in (ox + 16, ox + width - 22):
        cv.line(lx, top + 2, lx - 6, base - 1, OUT); cv.line(lx + 1, top + 2, lx - 5, base - 1, PLY[2])
        cv.line(lx + 4, top + 2, lx + 10, base - 1, OUT); cv.line(lx + 5, top + 2, lx + 11, base - 1, PLY[2])
    # top boards
    cv.rect(ox, top - 2, width, 7, OUT)
    cv.wood(ox + 1, top - 1, width - 2, 5, PLY[4], plank=5, seed=seed)
    cv.hline(ox + 1, top - 1, width - 2, PLY[5])
    for sx in range(ox + 1, ox + width - 1, 3):
        if rng.random() < 0.2:
            cv.px(sx, top + 1, PLY[2])
    # near bench
    by = base - 9
    cv.rect(ox - 2, by, width + 4, 5, OUT)
    cv.rect(ox - 1, by + 1, width + 2, 3, PLY[3]); cv.hline(ox - 1, by + 1, width + 2, PLY[5])
    for lx in (ox + 10, ox + width - 14):
        cv.rect(lx, by + 4, 4, base - by - 4, OUT); cv.vline(lx + 1, by + 4, base - by - 5, PLY[2])
    if items:
        items(cv, ox, top - 2, width)
    return cv, ox + width // 2, base


def a_frame_sign(width=90, height=58, lines=(), header=None, seed=0):
    """A sandwich-board sign on splayed legs. lines: [(text, colour, struck)] painted on cream board."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 - 6, 2)
    top = base - height
    leg = 14
    # back legs and front legs
    for lx in (ox + 6, ox + width - 9):
        cv.line(lx, base - leg - 2, lx - 2, base, OUT); cv.line(lx + 1, base - leg - 2, lx - 1, base, WOOD[2])
        cv.line(lx + 3, base - leg - 2, lx + 5, base, OUT); cv.line(lx + 2, base - leg - 2, lx + 4, base, WOOD[3])
    bh = height - leg
    cv.rect(ox, top, width, bh, OUT)
    cv.rect(ox + 1, top + 1, width - 2, bh - 2, WOOD[3]); cv.hline(ox + 1, top + 1, width - 2, WOOD[5])
    cv.rect(ox + 3, top + 3, width - 6, bh - 6, "#e6d6b1"); cv.hline(ox + 3, top + bh - 4, width - 6, "#c8b48e")
    y = top + 3
    if header:
        cv.rect(ox + 3, top + 3, width - 6, 10, "#2c4a4c")
        text(cv, header, ox + width // 2 - text_width(header) // 2, top + 3, "#f6cd78")
        y = top + 14
    for (s, col, struck) in lines:
        tx = ox + width // 2 - text_width(s) // 2
        text(cv, s, tx, y, col)
        if struck:
            cv.line(tx - 2, y + 5, tx + text_width(s), y + 4, "#c8382c")
        y += 9
    return cv, ox + width // 2, base


def cooler(cv, x, base, w=16, h=11, c=None):
    c = c or ["#1e3a5a", "#2c5a86", "#4a7ab0", "#e6e2d8"]
    cv.rect(x, base - h, w, h, OUT)
    cv.rect(x + 1, base - h + 1, w - 2, h - 2, c[1]); cv.hline(x + 1, base - h + 1, w - 2, c[2])
    cv.rect(x + 1, base - h + 3, w - 2, 1, c[3]); cv.hline(x + 1, base - 2, w - 2, c[0])
    cv.rect(x + w // 2 - 2, base - h - 1, 5, 2, OUT)


def crate(cv, x, base, w=14, h=10, pal=PLY):
    cv.rect(x, base - h, w, h, OUT)
    cv.rect(x + 1, base - h + 1, w - 2, h - 2, pal[3])
    for yy in range(base - h + 3, base - 1, 3):
        cv.hline(x + 1, yy, w - 2, pal[2])
    cv.hline(x + 1, base - h + 1, w - 2, pal[5])


def water_jug(cv, x, base):
    cv.rect(x, base - 12, 8, 12, OUT)
    cv.rect(x + 1, base - 11, 6, 10, "#5a86b0"); cv.vline(x + 1, base - 11, 10, "#8ab4d8")
    cv.rect(x + 2, base - 14, 4, 3, OUT); cv.rect(x + 3, base - 13, 2, 1, "#2c5a86")
    cv.hline(x + 1, base - 5, 6, "#3e6a94")


def chair_stack(cv, x, base, n=6, w=14):
    """A leaning stack of folded chairs."""
    for i in range(n):
        y = base - 3 - i * 3
        cv.rect(x + i % 2, y - 20 + i, w, 3, OUT); cv.hline(x + 1 + i % 2, y - 19 + i, w - 2, STEEL[3])
    cv.rect(x, base - 24 - n * 2, 2, 22 + n * 2, OUT); cv.rect(x + w - 1, base - 24 - n * 2, 2, 22 + n * 2, OUT)
    cv.vline(x + 1, base - 23 - n * 2, 20 + n * 2, STEEL[4])


def hivis_vest(cv, x, y, c="#d8e040"):
    """A hi-vis vest hanging from a hook at (x, y)."""
    cv.px(x + 4, y, OUT)
    cv.rect(x, y + 1, 9, 11, OUT)
    cv.rect(x + 1, y + 2, 7, 9, c); cv.vline(x + 4, y + 2, 9, shade(c, -0.35))
    cv.hline(x + 1, y + 6, 7, REFLECT[1]); cv.hline(x + 1, y + 9, 7, REFLECT[1])
    cv.px(x + 4, y + 1, OUT)


def cable_cart(width=72, height=43, seed=0):
    """Flatbed cable trolley: two cable drums (orange and black cable), a loose coil, a crate of
    connectors, push handle and fat wheels."""
    rng = _rng(seed)
    cv = Canvas(width + 10, height + 8, seed=seed)
    ox, base = 5, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    deck = base - 9
    # wheels
    for wx in (ox + 6, ox + width - 14):
        cv.ellipse(wx, deck + 1, 9, 9, OUT); cv.ellipse(wx + 1, deck + 2, 7, 7, "#2a2832"); cv.rect(wx + 3, deck + 4, 3, 3, STEEL[3])
    # flatbed
    cv.rect(ox, deck - 3, width, 5, OUT)
    cv.rect(ox + 1, deck - 2, width - 2, 3, PLY[3]); cv.hline(ox + 1, deck - 2, width - 2, PLY[5])
    cv.hline(ox + 1, deck, width - 2, PLY[1])
    # push handle (left)
    cv.rect(ox - 3, deck - 30, 3, 28, OUT); cv.vline(ox - 2, deck - 29, 26, STEEL[4])
    cv.rect(ox - 4, deck - 32, 7, 3, OUT); cv.hline(ox - 3, deck - 31, 5, "#c84a3c")

    def drum(x, r, cab):
        y = deck - 3 - r * 2
        cv.ellipse(x - 1, y - 1, r * 2 + 3, r * 2 + 3, OUT)
        cv.ellipse(x, y, r * 2 + 1, r * 2 + 1, PLY[2])
        cv.ellipse(x + 2, y + 2, r * 2 - 3, r * 2 - 3, cab[1])
        for k in range(0, r * 2 - 4, 2):
            cv.hline(x + 3, y + 3 + k, r * 2 - 5, cab[2] if k % 4 == 0 else cab[1])
        cv.ellipse(x + r - 2, y + r - 2, 5, 5, PLY[4]); cv.px(x + r, y + r, OUT)
        cv.hline(x + 2, y + 1, r * 2 - 3, PLY[4])
        cv.rect(x + r - 1, y + r * 2, 3, 3, STEEL[2])
    drum(ox + 4, 11, ["#2a1a14", "#c4581e", "#e8803a"])
    drum(ox + 30, 9, ["#121016", "#24222c", "#3a3844"])
    # crate of connectors
    crate(cv, ox + width - 22, deck - 3, 18, 11)
    for k in range(4):
        cv.rect(ox + width - 20 + k * 4, deck - 16, 2, 3, ["#e8b45c", "#5c897c", "#c84a3c", "#e6d6b1"][k])
    # loose coil hanging off the back
    cv.ellipse(ox + width - 10, deck - 6, 12, 12, "#1e1c24"); cv.ellipse(ox + width - 8, deck - 4, 8, 8, C("#000000", 0))
    for a in np.linspace(0, 2 * np.pi, 40):
        cv.px(int(ox + width - 4 + np.cos(a) * 5), int(deck + np.sin(a) * 5), "#34303c")
    cv.px(ox + width - 4, deck - 5, "#c84a3c")
    return cv, ox + width // 2, base


def festoon_occluders(room, out, name, x0, y0, floor0, x1, y1, floor1, sag=14, every=9, seed=0, pieces=5):
    """Overhead string lights crossing the walkable floor, cut into pieces that y-sort with the
    characters: each piece's base is the floor y beneath it (interpolated between the two
    anchors' floor points). Writes PNGs into `out`; returns occluder entries for the manifest."""
    import os
    full = Canvas(max(x0, x1) + 8, max(y0, y1) + sag + 12)
    festoon(full, x0, y0, x1, y1, sag=sag, every=every, seed=seed)
    entries = []
    xa, xb = min(x0, x1), max(x0, x1)
    edges = np.linspace(xa - 3, xb + 4, pieces + 1).astype(int)
    for i in range(pieces):
        a, b = edges[i], edges[i + 1]
        part = full.a[:, a:b].copy()
        ys = np.where(part[..., 3].max(axis=1) > 0)[0]
        if len(ys) == 0:
            continue
        top, bot = int(ys.min()), int(ys.max()) + 1
        piece = Canvas(b - a, bot - top)
        piece.a = part[top:bot]
        fname = f"{name}-{i}.png"
        piece.save(os.path.join(out, fname))
        t = ((a + b) / 2 - x0) / max(1, (x1 - x0))
        base = int(round(floor0 + (floor1 - floor0) * t))
        entries.append({"texture": f"res://assets/art/rooms/{room}/{fname}", "x": int(a), "y": int(top), "base": base})
    return entries


# --- battle backdrop helpers (persp.View shaders and textures) ---------------------------------
def battle_grass_rgb(X, Z, stripe=90.0, seed=0):
    """Lawn for a perspective ground shader: mowing stripes running toward the horizon,
    tufts as lit flecks with dark feet, a few fallen leaves."""
    from persp import hash2, pal_array
    g = pal_array(GRASS)
    band = (np.floor(X / stripe) % 2).astype(np.float32)
    rgb = g[3] * (1 - band[:, None]) + g[4] * band[:, None]
    cx, cz = np.floor(X / 5.0), np.floor(Z / 7.0)
    h = hash2(cx, cz, 31 + seed)
    fx, fz = X / 5.0 - cx, Z / 7.0 - cz
    tuft = (h > 0.62) & (fz > 0.45) & (np.abs(fx - 0.5) < 0.3)
    rgb[tuft] = g[5] * 0.6 + rgb[tuft] * 0.4
    tip = (h > 0.82) & (fz > 0.3) & (fz < 0.55) & (np.abs(fx - 0.5) < 0.2)
    rgb[tip] = g[6]
    foot = (h > 0.62) & (fz > 0.85)
    rgb[foot] = g[1]
    leaf = hash2(np.floor(X / 6), np.floor(Z / 6), 77 + seed) > 0.985
    rgb[leaf] = pal_array(["#c8682e"])[0]
    return rgb


def battle_mats_rgb(X, Z, half=64.0, mat_len=34.0, seed=0):
    """Ground-protection mats for a perspective shader: two mats across, dark joints, tread studs."""
    from persp import hash2, pal_array
    m = pal_array(MAT)
    col = np.floor(X / half * 2)
    row = np.floor(Z / mat_len)
    tone = hash2(col, row, 5 + seed)
    rgb = m[3] * (1 - tone[:, None] * 0.5) + m[4] * (tone[:, None] * 0.5)
    fx = X / (half / 2) - np.floor(X / (half / 2))
    fz = Z / mat_len - row
    stud = ((np.floor(X / 5.0) + np.floor(Z / 6.0)) % 2 == 0) & ((Z / 6.0) % 1 < 0.35) & ((X / 5.0) % 1 < 0.45)
    rgb[stud] = m[5] * 0.7 + rgb[stud] * 0.3
    rgb[(fx < 0.05) | (fx > 0.97) | (fz < 0.05)] = m[1]
    rgb[(fz > 0.05) & (fz < 0.1)] = m[5]
    return rgb


def barrier_texture(length, height=44, seed=0, section=84, tape=True):
    """Crowd barriers laid out along a run (u = distance along it), for persp.View.plane:
    rails and bars opaque, the gaps between bars transparent, hazard tape along the top."""
    cv = Canvas(length, height + 2, seed=seed)
    base = height + 1
    top = 1
    for x0 in range(0, length, section):
        x1 = min(length, x0 + section - 4)
        for bx in range(x0 + 6, x1 - 3, 6):
            cv.rect(bx, top + 4, 2, height - 12, STEEL[3]); cv.px(bx, top + 4, STEEL[4])
        cv.rect(x0, top, 4, height - 4, STEEL[4]); cv.vline(x0 + 3, top, height - 4, STEEL[2])
        cv.rect(x1 - 4, top, 4, height - 4, STEEL[3])
        cv.rect(x0, top, x1 - x0, 4, STEEL[5]); cv.hline(x0, top + 3, x1 - x0, STEEL[2])
        cv.rect(x0, base - 12, x1 - x0, 4, STEEL[3]); cv.hline(x0, base - 9, x1 - x0, STEEL[1])
        cv.rect(x0 - 3, base - 4, 12, 4, STEEL[2]); cv.rect(x1 - 8, base - 4, 12, 4, STEEL[2])
        if tape:
            for xx in range(x0, x1):
                yy = top + 7 + int(round(2 * np.sin(xx / 11.0)))
                c = HAZARD[3] if (xx // 7) % 2 == 0 else HAZARD[0]
                cv.rect(xx, yy, 1, 3, c)
    return cv.a


def cone_sprite(h=13, lean=0):
    """A traffic cone on its own small canvas (RGBA array), anchor bottom-centre."""
    w = max(9, h)
    cv = Canvas(w + 6, h + 3)
    traffic_cone(cv, (w + 6) // 2, h + 1, h, lean=lean)
    return cv.a


def string_across(cv, p0, p1, sag, every, seed=0, colours=None):
    """Crisp festoon on the reduced battle canvas between two screen points; returns twinkles."""
    return festoon(cv, int(round(p0[0])), int(round(p0[1])), int(round(p1[0])), int(round(p1[1])),
                   sag=sag, every=every, seed=seed, colours=colours)


def field_treeline(width=640, base=34, seed=3, open_span=(250, 390)):
    """Dark field-edge tree crowns along the horizon, an opening left for the stage."""
    rng = _rng(seed)
    cv = Canvas(width, base + 2)
    for x in range(-10, width + 10, 8):
        if open_span[0] < x < open_span[1]:
            continue
        h = int(rng.integers(10, 24))
        cv.ellipse(x, base - h, int(rng.integers(12, 22)), h * 2, "#231f36" if rng.random() < 0.6 else "#1f1b30")
    for x in range(-6, width, 6):
        if open_span[0] + 10 < x < open_span[1] - 10:
            continue
        h = int(rng.integers(4, 10))
        cv.ellipse(x, base - h + 3, int(rng.integers(8, 14)), h * 2, "#1a1828")
    cv.a[base:, :, 3] = 0
    return cv.a


# --- food court -------------------------------------------------------------------------------
TRUCK_TEAL = ["#122426", "#1d3638", "#2a5050", "#3a6c68", "#548c82", "#7eb0a2"]
TRUCK_CREAM = ["#33292a", "#5a4c46", "#857462", "#b09c80", "#d4c29e", "#ece0c0"]
TRUCK_PINK = ["#2a1824", "#462638", "#6c3a52", "#92526c", "#b8708a", "#d896a8"]
TRUCK_MUSTARD = ["#2e2214", "#4a3618", "#74561e", "#a07a26", "#c89c34", "#e4c060"]
CHALK = ["#161c1a", "#232c28", "#3a4440", "#dcd8c8"]
STRIPE_TRIM = ["#c84a3c", "#e6d6b1"]
BARK = ["#24191a", "#36261f", "#4a3426", "#5e4430", "#77583c", "#93704a"]
STRAW_BED = ["#2a2a20", "#3e3a28", "#565034", "#726840", "#8e8250", "#ab9c62", "#c8b878"]


def blob_mask(w, h, cx, cy, rx, ry, seed=0, rough=0.28, cell=18):
    """Irregular rounded region (an ellipse with a noisy edge) as a canvas-sized bool mask."""
    rng = _rng(seed)
    ys, xs = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xs - cx) / max(1, rx)) ** 2 + ((ys - cy) / max(1, ry)) ** 2)
    n = _soft_field(w, h, cell, rng)
    return d + (n - 0.5) * rough * 2 < 1.0


def woodchip(cv, mask, seed=0, pal=BARK, density=1.0):
    """Bark chips spread over the lawn where the food court gets the most feet: a warm brown bed
    of short broken strokes, thinning to scattered chips (grass showing) at the ragged edge."""
    rng = _rng(seed)
    h, w = mask.shape
    # distance into the region (rough): erode the mask a few times
    inner = mask.copy()
    depth = np.zeros(mask.shape, np.int16)
    for k in range(6):
        depth += inner
        e = inner.copy()
        e[1:, :] &= inner[:-1, :]; e[:-1, :] &= inner[1:, :]
        e[:, 1:] &= inner[:, :-1]; e[:, :-1] &= inner[:, 1:]
        inner = e
    n = _soft_field(w, h, 14, rng)
    core = mask & ((depth >= 4) | (n > 0.75 - depth * 0.08))
    cv.fill_mask(core & (n < 0.45), pal[1])
    cv.fill_mask(core & (n >= 0.45), pal[2])
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return
    count = int(len(xs) / 9 * density)
    pick = rng.integers(0, len(xs), count)
    shapes = [((0, 0), (1, 0)), ((0, 0), (1, 0), (2, 0)), ((0, 0), (1, 0), (2, 1)), ((0, 1), (1, 0), (2, 0)), ((0, 0), (1, 0), (1, 1))]
    for i in pick:
        x, y = int(xs[i]), int(ys[i])
        d = depth[y, x]
        if d < 4 and rng.random() > 0.25 + d * 0.15:
            continue
        r = rng.random()
        c = pal[3] if r < 0.62 else (pal[4] if r < 0.9 else pal[5])
        for (dx, dy) in shapes[int(rng.integers(len(shapes)))]:
            if 0 <= x + dx < w and 0 <= y + dy < h:
                cv.px(x + dx, y + dy, c)
        if y + 1 < h and d >= 4:
            cv.px(x, y + 1, pal[1])


def straw_bed(cv, mask, seed=0, pal=STRAW_BED, density=1.0):
    """Straw forked down over the mud where the food court gets the most feet: a dull gold bed of
    criss-crossed strands, thinning to loose wisps with grass between them at the edge."""
    rng = _rng(seed)
    h, w = mask.shape
    inner = mask.copy()
    depth = np.zeros(mask.shape, np.int16)
    for k in range(8):
        depth += inner
        e = inner.copy()
        e[1:, :] &= inner[:-1, :]; e[:-1, :] &= inner[1:, :]
        e[:, 1:] &= inner[:, :-1]; e[:, :-1] &= inner[:, 1:]
        inner = e
    n = _soft_field(w, h, 22, rng)
    core = mask & ((depth >= 5) | (n > 0.8 - depth * 0.1))
    cv.fill_mask(core & (n < 0.4), pal[1])
    cv.fill_mask(core & (n >= 0.4), pal[2])
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return
    count = int(len(xs) / 6 * density)
    pick = rng.integers(0, len(xs), count)
    dirs = [(1, 0), (1, 0), (2, 1), (1, 1), (2, -1), (1, -1), (3, 1), (3, -1)]
    for i in pick:
        x, y = int(xs[i]), int(ys[i])
        d = depth[y, x]
        if d < 5 and rng.random() > 0.2 + d * 0.13:
            continue
        r = rng.random()
        c = pal[3] if r < 0.45 else (pal[4] if r < 0.8 else (pal[5] if r < 0.96 else pal[6]))
        dx, dy = dirs[int(rng.integers(len(dirs)))]
        ln = int(rng.integers(3, 6))
        for t in range(ln):
            xx = x + int(round(t * dx / max(abs(dx), 1)))
            yy = y + int(round(t * dy / max(abs(dx), 1) * 0.6))
            if 0 <= xx < w and 0 <= yy < h:
                cv.px(xx, yy, c)
        if d >= 5 and y + 1 < h and rng.random() < 0.5:
            cv.px(x + 1, y + 1, pal[1])


def menu_board(cv, x, y, w, h, title=None, lines=4, seed=0, frame=None, chalk=CHALK, accent=("#f6cd78", "#e88a7a", "#9ad0b8")):
    """A chalkboard menu: wooden frame, a heading in the game font (if it fits), then lines of
    dishes with a price dot at the right in coloured chalk."""
    rng = _rng(seed)
    frame = frame or WOOD
    cv.rect(x, y, w, h, OUT)
    cv.rect(x + 1, y + 1, w - 2, h - 2, frame[3]); cv.hline(x + 1, y + 1, w - 2, frame[4])
    cv.rect(x + 2, y + 2, w - 4, h - 4, chalk[1])
    cv.rect(x + 2, y + 2, w - 4, 1, chalk[0])
    ly = y + 4
    if title and text_width(title) <= w - 4:
        text(cv, title, x + w // 2 - text_width(title) // 2, y + 1, accent[0])
        ly = y + 12
    k = 0
    while ly + 2 < y + h - 2 and k < lines:
        lw = int(rng.integers(max(4, (w - 10) // 2), max(5, w - 10)))
        cv.hline(x + 4, ly, lw, chalk[3] if k % 2 == 0 else shade(chalk[3], -0.15))
        if rng.random() < 0.5:
            cv.px(x + 4 + lw + 1, ly, chalk[3])
        cv.px(x + w - 5, ly, accent[1 + k % 2]); cv.px(x + w - 6, ly, accent[1 + k % 2])
        ly += 4
        k += 1
    # chalk dust smudge
    cv.rect(x + 3, y + h - 4, w // 3, 1, C(chalk[3], 0.25))


def _outline_poly(cv, pts, fill):
    cv.poly([(px - 1, py) for px, py in pts], OUT)
    cv.poly([(px + 1, py) for px, py in pts], OUT)
    cv.poly([(px, py - 1) for px, py in pts], OUT)
    cv.poly([(px, py + 1) for px, py in pts], OUT)
    cv.poly(pts, fill)


def _wheel(cv, cx, cy, r=9, rim=STEEL):
    cv.ellipse(cx - r, cy - r, 2 * r + 1, 2 * r + 1, OUT)
    cv.ellipse(cx - r + 1, cy - r + 1, 2 * r - 1, 2 * r - 1, "#26232e")
    cv.ellipse(cx - r + 4, cy - r + 4, 2 * r - 7, 2 * r - 7, rim[3])
    cv.ellipse(cx - r + 5, cy - r + 5, 2 * r - 9, 2 * r - 9, rim[4])
    cv.rect(cx - 1, cy - 1, 3, 3, rim[2]); cv.px(cx - 2, cy - 3, rim[5])
    cv.hline(cx - r + 3, cy - r + 1, 2 * r - 5, "#3a3644")


def food_truck(width=180, height=80, pal=TRUCK_TEAL, name="TACOS", open_=True, seed=0, facing=-1,
               trim=STRIPE_TRIM, menu_title=None, goods=None):
    """A step-van food truck seen side-on with its serving hatch toward us: cab at one end
    (facing=-1 cab on the left), boxy body with a painted name board, a propped-up awning with
    bulbs over a warm lit hatch and steel ledge (open_=True) or a rolled-down shutter with a
    CLOSED card, a chalk menu beside the hatch, roof vent, gas bottles at the back, wheels.
    goods(cv, x, y, w, h) paints the hatch interior shelves. Returns (Canvas, anchor_x, anchor_y,
    info) with info = {"hatch": (x0, y0, x1, y1), "bulbs": [twinkle points]} in canvas pixels."""
    rng = _rng(seed)
    w, h = width, height
    CW, CH = w + 12, h + 22
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 6, CH - 3
    ground_shadow(cv, ox + w // 2, base, w // 2 + 4, 3, alpha=0.45)
    top = base - h            # body roof
    belly = base - 12         # bottom of the body panels
    cab_w = 44
    cab_roof = top + 16
    bx0 = ox + cab_w - 2      # box body starts here
    # --- silhouettes (drawn cab-left, mirrored at the end if facing right)
    cab = [(bx0 + 2, cab_roof), (ox + 16, cab_roof), (ox + 6, base - 46), (ox + 1, base - 42), (ox + 1, belly + 2), (bx0 + 2, belly + 2)]
    _outline_poly(cv, cab, pal[3])
    cv.rect(bx0 - 1, top - 1, ox + w - bx0 + 2, belly - top + 3, OUT)
    cv.rect(bx0, top, ox + w - bx0, belly - top + 1, pal[3])
    cv.px(bx0, top, OUT); cv.px(ox + w - 1, top, OUT)
    # body shading: lit top, darker skirt, panel seams, rivets
    cv.rect(bx0, top + 1, ox + w - bx0, 2, pal[4]); cv.hline(bx0 + 1, top, ox + w - bx0 - 2, pal[5])
    cv.rect(bx0, belly - 8, ox + w - bx0, 9, pal[2])
    for sx in range(bx0 + 40, ox + w - 4, 44):
        cv.vline(sx, top + 3, belly - top - 11, pal[2])
    cv.rect(ox + 2, base - 30, bx0 - ox, 18, pal[2])
    # trim stripe all along
    cv.rect(ox + 2, belly - 13, w - 2, 3, trim[0]); cv.hline(ox + 2, belly - 13, w - 2, shade(trim[0], 0.25))
    cv.hline(ox + 2, belly - 10, w - 2, trim[1])
    # cab: side window, door seam, handle, mirror, headlight, bumper
    win = [(ox + 17, cab_roof + 3), (bx0 - 4, cab_roof + 3), (bx0 - 4, base - 48), (ox + 9, base - 48)]
    cv.poly(win, "#1c2438")
    cv.line(ox + 20, cab_roof + 5, ox + 12, base - 50, "#5a6a8a"); cv.line(ox + 24, cab_roof + 5, ox + 17, base - 50, "#3a4660")
    cv.rect(bx0 - 6, cab_roof + 2, 3, base - 48 - cab_roof, pal[2])
    cv.vline(ox + 8, base - 46, belly - base + 46, pal[2]); cv.vline(bx0 - 3, cab_roof + 2, belly - cab_roof - 1, pal[2])
    cv.rect(bx0 - 12, base - 40, 5, 2, STEEL[4])
    cv.rect(ox - 2, base - 50, 3, 7, OUT); cv.rect(ox - 1, base - 49, 1, 5, STEEL[4])
    cv.rect(ox + 1, base - 30, 4, 4, BULB[3]); cv.px(ox + 1, base - 30, "#ffffff")
    cv.rect(ox - 1, belly - 2, 10, 5, OUT); cv.rect(ox, belly - 1, 8, 3, STEEL[3])
    # roof: vent box, extractor chimney
    rv = ox + w - 58
    cv.rect(rv, top - 7, 26, 8, OUT); cv.rect(rv + 1, top - 6, 24, 6, STEEL[4]); cv.hline(rv + 1, top - 6, 24, STEEL[5])
    for k in range(rv + 3, rv + 24, 3):
        cv.vline(k, top - 4, 3, STEEL[2])
    cv.rect(rv + 34, top - 12, 5, 13, OUT); cv.rect(rv + 35, top - 11, 3, 11, STEEL[3]); cv.rect(rv + 33, top - 14, 7, 3, OUT)
    # underneath: skirt shadow, wheel arches, wheels, gas bottles at the back, a step
    cv.rect(ox + 2, belly + 1, w - 2, base - belly - 2, "#14111c")
    for wx in (ox + 26, ox + w - 34):
        cv.ellipse(wx - 12, belly - 10, 25, 22, OUT)
        cv.rect(wx - 12, belly + 1, 25, 10, "#14111c")
        cv.ellipse(wx - 11, belly - 9, 23, 20, "#14111c")
        _wheel(cv, wx, base - 9, 9)
    gx = ox + w - 18
    for k in range(2):
        cv.rect(gx - k * 7, belly - 6, 6, 15, OUT); cv.rect(gx + 1 - k * 7, belly - 5, 4, 13, ["#c8c4b8", "#d8a03a"][k])
        cv.hline(gx + 1 - k * 7, belly - 5, 4, "#ffffff" if k == 0 else "#f2cf5c")
    # serving hatch with chalk menu beside it
    hx0, hx1 = bx0 + 18, bx0 + 18 + int(w * 0.36)
    hy0, hy1 = top + 25, belly - 17
    menu_x = hx1 + 8
    info = {"hatch": (hx0, hy0, hx1, hy1), "bulbs": []}
    if open_:
        # warm interior: back wall, extractor hood, shelves, a cook's light
        cv.rect(hx0 - 1, hy0 - 1, hx1 - hx0 + 2, hy1 - hy0 + 2, OUT)
        cv.rect(hx0, hy0, hx1 - hx0, hy1 - hy0, BULB[1])
        cv.rect(hx0, hy0, hx1 - hx0, 4, "#5a3a2a"); cv.hline(hx0, hy0 + 4, hx1 - hx0, BULB[0])
        cv.rect(hx0 + 2, hy0 + 5, hx1 - hx0 - 4, 5, BULB[2])
        cv.rect(hx0 + (hx1 - hx0) // 2 - 6, hy0 + 5, 12, 3, BULB[3])
        cv.hline(hx0, hy0 + 12, hx1 - hx0, shade(BULB[1], -0.35))
        if goods:
            goods(cv, hx0, hy0, hx1 - hx0, hy1 - hy0)
        else:
            for k in range(hx0 + 3, hx1 - 4, 6):
                c = ["#c84a3c", "#e0b23a", "#5a9a5a", "#e6d6b1"][int(rng.integers(4))]
                cv.rect(k, hy0 + 8, 4, 4, c); cv.hline(k, hy0 + 8, 4, shade(c, 0.3))
        cv.rect(hx0, hy1 - 6, hx1 - hx0, 6, shade(BULB[1], -0.2))
        # steel ledge with squeeze bottles, napkins, tip jar
        cv.rect(hx0 - 4, hy1, hx1 - hx0 + 8, 4, OUT); cv.rect(hx0 - 3, hy1 + 1, hx1 - hx0 + 6, 2, STEEL[4]); cv.hline(hx0 - 3, hy1 + 1, hx1 - hx0 + 6, STEEL[5])
        cv.rect(hx0 + 2, hy1 - 6, 3, 6, "#c8382c"); cv.px(hx0 + 3, hy1 - 7, "#c8382c")
        cv.rect(hx0 + 6, hy1 - 6, 3, 6, "#e0b23a"); cv.px(hx0 + 7, hy1 - 7, "#e0b23a")
        cv.rect(hx0 + 12, hy1 - 5, 6, 5, OUT); cv.rect(hx0 + 13, hy1 - 4, 4, 4, STEEL[4]); cv.hline(hx0 + 13, hy1 - 6, 4, "#f2f2ee")
        cv.rect(hx1 - 9, hy1 - 6, 5, 6, OUT); cv.rect(hx1 - 8, hy1 - 5, 3, 5, "#9ab8c8"); cv.px(hx1 - 7, hy1 - 3, "#3e9a5c")
        # striped awning over the hatch with a scalloped edge and bulbs along it
        ay = hy0 - 1
        aw0, aw1 = hx0 - 7, hx1 + 7
        cv.poly([(hx0 - 2, ay - 10), (hx1 + 2, ay - 10), (aw1 + 1, ay + 1), (aw0 - 1, ay + 1)], OUT)
        for k in range(0, hx1 - hx0 + 4, 6):
            t0, t1 = k / (hx1 - hx0 + 4), min(1.0, (k + 3) / (hx1 - hx0 + 4))
            q = [(hx0 - 2 + (hx1 - hx0 + 4) * t0, ay - 9), (hx0 - 2 + (hx1 - hx0 + 4) * t1, ay - 9),
                 (aw0 + (aw1 - aw0) * t1, ay), (aw0 + (aw1 - aw0) * t0, ay)]
            cv.poly(q, trim[1])
        for k in range(3, hx1 - hx0 + 4, 6):
            t0, t1 = k / (hx1 - hx0 + 4), min(1.0, (k + 3) / (hx1 - hx0 + 4))
            q = [(hx0 - 2 + (hx1 - hx0 + 4) * t0, ay - 9), (hx0 - 2 + (hx1 - hx0 + 4) * t1, ay - 9),
                 (aw0 + (aw1 - aw0) * t1, ay), (aw0 + (aw1 - aw0) * t0, ay)]
            cv.poly(q, trim[0])
        cv.hline(hx0 - 1, ay - 9, hx1 - hx0 + 2, shade(trim[1], 0.2))
        for k in range(aw0, aw1, 6):
            cv.rect(k + 1, ay + 1, 4, 2, OUT); cv.hline(k + 2, ay + 1, 2, trim[(k - aw0) // 6 % 2])
        info["bulbs"] = festoon(cv, aw0, ay + 3, aw1, ay + 3, sag=2, every=7, seed=seed + 1)
    else:
        # roller shutter down, padlocked, a CLOSED card taped on
        cv.rect(hx0 - 1, hy0 - 1, hx1 - hx0 + 2, hy1 - hy0 + 2, OUT)
        for yy in range(hy0, hy1):
            cv.hline(hx0, yy, hx1 - hx0, STEEL[4] if (yy - hy0) % 3 == 0 else STEEL[3])
        cv.rect(hx0, hy0, hx1 - hx0, 3, STEEL[2])
        cv.rect(hx0, hy1 - 2, hx1 - hx0, 2, STEEL[2])
        cv.rect(hx0 + (hx1 - hx0) // 2 - 2, hy1 - 4, 4, 4, "#c8a03a"); cv.px(hx0 + (hx1 - hx0) // 2 - 1, hy1 - 6, "#c8a03a")
        cv.rect(hx0 - 4, hy1, hx1 - hx0 + 8, 3, OUT); cv.hline(hx0 - 3, hy1 + 1, hx1 - hx0 + 6, STEEL[3])
        cv.rect(hx0 - 4, hy0 - 6, hx1 - hx0 + 8, 5, OUT)
        for k in range(hx0 - 3, hx1 + 3, 4):
            cv.rect(k, hy0 - 5, 2, 3, trim[0]); cv.rect(k + 2, hy0 - 5, 2, 3, trim[1])
        cv.hline(hx0 - 3, hy0 - 3, hx1 - hx0 + 6, C("#0d0b16", 0.35))
    # menu board beside the hatch
    menu_board(cv, menu_x, hy0 - 2, 26, hy1 - hy0 + 4, lines=5, seed=seed + 2)
    # mirror for a truck facing right; the name board and card text go on after the flip
    if facing > 0:
        cv.a = cv.a[:, ::-1].copy()
        fx = lambda x0, ww: CW - x0 - ww
        info["hatch"] = (fx(hx1, 0), hy0, fx(hx0, 0), hy1)
        info["bulbs"] = [[CW - 1 - p[0], p[1], p[2], p[3]] for p in info["bulbs"]]
    else:
        fx = lambda x0, ww: x0
    # name board over the hatch
    nw = text_width(name) + 12
    hx0_, hx1_ = info["hatch"][0], info["hatch"][2]
    nbx = (hx0_ + hx1_) // 2 - nw // 2
    nby = top + 4
    cv.rect(nbx, nby, nw, 12, OUT); cv.rect(nbx + 1, nby + 1, nw - 2, 10, trim[1]); cv.hline(nbx + 1, nby + 1, nw - 2, "#fff6dc")
    cv.hline(nbx + 1, nby + 10, nw - 2, shade(trim[1], -0.25))
    text(cv, name, nbx + 6, nby + 1, trim[0] if trim[0] != trim[1] else "#2c4a4c")
    if not open_:
        hx0_, hy0_, hx1_, hy1_ = info["hatch"]
        cw_ = text_width("CLOSED") + 6
        ccx = (hx0_ + hx1_) // 2 - cw_ // 2
        cv.rect(ccx, hy0_ + 5, cw_, 11, OUT); cv.rect(ccx + 1, hy0_ + 6, cw_ - 2, 9, "#f2ead6")
        cv.rect(ccx + cw_ // 2 - 3, hy0_ + 4, 6, 2, C("#d8d0b0", 0.9))
        text(cv, "CLOSED", ccx + 3, hy0_ + 5, "#b8382c")
    anchor_x = ox + w // 2 if facing < 0 else CW - ox - w // 2
    return cv, anchor_x, base, info


def market_stall(width=120, height=88, canopy=RED, name="COCOA", seed=0, lit=True, counter=None, back=None):
    """A timber market stall: plank counter with a painted name board, corner posts, a striped
    pitched canopy with a scalloped valance, a bulb inside lighting the back shelves.
    counter(cv, x0, top, w) paints what stands on the counter, back(cv, x, y, w, h) the shelves.
    Returns (Canvas, anchor_x, anchor_y, bulbs)."""
    rng = _rng(seed)
    w, h = width, height
    CW, CH = w + 16, h + 8
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 8, CH - 3
    ground_shadow(cv, ox + w // 2, base, w // 2 + 4, 3, alpha=0.42)
    eave = base - int(h * 0.68)
    peak = base - h
    ctop = base - 30
    # back wall of the booth (dark planks, lit by the bulb), shelves
    cv.rect(ox + 3, eave, w - 6, ctop - eave, OUT)
    cv.wood(ox + 4, eave + 1, w - 8, ctop - eave - 1, WOOD[2], vertical=True, plank=7, seed=seed)
    if lit:
        F_ = BULB[2]
        cv.rect(ox + 4, eave + 1, w - 8, ctop - eave - 1, C(F_, 0.16))
        light_pool(cv, ox + w // 2, eave + 10, w // 2, 14, F_, 0.3)
    for sy in (eave + 12, eave + 22):
        cv.rect(ox + 6, sy, w - 12, 2, OUT); cv.hline(ox + 6, sy, w - 12, WOOD[4])
    if back:
        back(cv, ox + 6, eave + 1, w - 12, ctop - eave - 1)
    else:
        for sy in (eave + 12, eave + 22):
            for k in range(ox + 9, ox + w - 12, 7):
                c = ["#c84a3c", "#e6d6b1", "#425da6", "#e0b23a"][int(rng.integers(4))]
                cv.rect(k, sy - 5, 4, 5, OUT); cv.rect(k + 1, sy - 4, 2, 4, c)
    # corner posts
    for px_ in (ox, ox + w - 4):
        cv.rect(px_, eave - 2, 5, base - eave + 1, OUT); cv.rect(px_ + 1, eave - 1, 3, base - eave - 1, WOOD[3]); cv.vline(px_ + 1, eave - 1, base - eave - 1, WOOD[4])
    # counter: plank front panel, top board with overhang
    cv.rect(ox + 2, ctop, w - 4, base - ctop, OUT)
    cv.wood(ox + 3, ctop + 3, w - 6, base - ctop - 4, WOOD[3], vertical=True, plank=6, seed=seed + 1)
    cv.rect(ox + 3, base - 6, w - 6, 5, C("#0d0b16", 0.3))
    cv.rect(ox - 1, ctop - 1, w + 2, 4, OUT); cv.hline(ox, ctop, w, WOOD[5]); cv.hline(ox, ctop + 1, w, WOOD[4])
    nw = text_width(name) + 12
    nbx = ox + w // 2 - nw // 2
    cv.rect(nbx, ctop + 7, nw, 13, OUT); cv.rect(nbx + 1, ctop + 8, nw - 2, 11, CANVAS[5]); cv.hline(nbx + 1, ctop + 8, nw - 2, CANVAS[6])
    text(cv, name, nbx + 6, ctop + 9, canopy[2])
    if counter:
        counter(cv, ox, ctop - 1, w)
    # canopy roof: alternate stripes from the peak line down to the eave, valance
    r0, r1 = ox + 18, ox + w - 18
    e0, e1 = ox - 6, ox + w + 6
    pts = [(r0, peak), (r1, peak), (e1, eave), (e0, eave)]
    _outline_poly(cv, pts, canopy[3])
    n = 10
    for i in range(n):
        if i % 2:
            continue
        t0, t1 = i / n, (i + 1) / n
        a0 = (r0 + (r1 - r0) * t0, peak); a1 = (r0 + (r1 - r0) * t1, peak)
        b0 = (e0 + (e1 - e0) * t0, eave); b1 = (e0 + (e1 - e0) * t1, eave)
        cv.poly([a0, a1, b1, b0], CANVAS[4])
    cv.hline(r0, peak, r1 - r0, CANVAS[6])
    cv.rect(e0, eave - 3, e1 - e0, 3, C("#0d0b16", 0.2))
    scallop_valance(cv, e0, eave, e1 - e0, depth=7, pal_a=canopy, pal_b=CANVAS, stripe=8)
    bulbs = []
    if lit:
        bx = ox + w // 2
        cv.vline(bx, eave + 7, 4, WIRE)
        bulbs.append(list(bulb(cv, bx, eave + 11, BULB[3])) + ["fff0c4", 1])
        bulbs += festoon(cv, e0 + 2, eave + 8, e1 - 2, eave + 8, sag=4, every=8, seed=seed + 3)
    return cv, ox + w // 2, base, bulbs


def soup_cart(width=86, height=45, name="SOUP", seed=0, closed=True):
    """A push cart going home: steel counter wiped clean (a shine streak), the big pot with its
    lid on and the ladle hung up, bowls stacked, a cloth folded, the SOUP board on the front,
    the umbrella furled, one big wheel and a fold-down leg, the push handle at the left.
    Returns (Canvas, anchor_x, anchor_y)."""
    rng = _rng(seed)
    w = width
    CW, CH = w + 10, height + 50
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 5, CH - 3
    ground_shadow(cv, ox + w // 2, base, w // 2, 3)
    bx0, bx1 = ox + 10, ox + w - 6
    ctop = base - 34
    # body: red painted panels with cream trim
    cv.rect(bx0 - 1, ctop, bx1 - bx0 + 2, 25, OUT)
    cv.rect(bx0, ctop + 3, bx1 - bx0, 21, RED[3]); cv.hline(bx0, ctop + 3, bx1 - bx0, RED[4])
    cv.rect(bx0, ctop + 20, bx1 - bx0, 4, RED[2])
    cv.hline(bx0, ctop + 17, bx1 - bx0, CANVAS[5])
    for sx in (bx0 + (bx1 - bx0) // 3, bx0 + 2 * (bx1 - bx0) // 3):
        cv.vline(sx, ctop + 4, 13, RED[2])
    # name board
    nw = text_width(name) + 8
    nbx = (bx0 + bx1) // 2 - nw // 2
    cv.rect(nbx, ctop + 4, nw, 12, OUT); cv.rect(nbx + 1, ctop + 5, nw - 2, 10, CANVAS[5]); cv.hline(nbx + 1, ctop + 5, nw - 2, CANVAS[6])
    text(cv, name, nbx + 4, ctop + 5, RED[2])
    # steel counter top, wiped clean: one long shine
    cv.rect(bx0 - 3, ctop - 2, bx1 - bx0 + 6, 4, OUT)
    cv.hline(bx0 - 2, ctop - 1, bx1 - bx0 + 4, STEEL[4]); cv.hline(bx0 - 2, ctop, bx1 - bx0 + 4, STEEL[3])
    cv.hline(bx0 + 8, ctop - 1, 22, STEEL[5]); cv.hline(bx0 + 12, ctop - 1, 8, "#f2f2ee")
    # pot with the lid on, ladle hung on the side
    px0 = bx1 - 26
    cv.rect(px0, ctop - 17, 22, 16, OUT); cv.rect(px0 + 1, ctop - 16, 20, 14, STEEL[4])
    cv.vline(px0 + 2, ctop - 16, 14, STEEL[5]); cv.vline(px0 + 18, ctop - 16, 14, STEEL[3])
    cv.rect(px0 - 2, ctop - 13, 3, 3, OUT); cv.rect(px0 + 21, ctop - 13, 3, 3, OUT)
    cv.rect(px0 - 1, ctop - 19, 24, 3, OUT); cv.hline(px0, ctop - 18, 22, STEEL[5])
    cv.rect(px0 + 9, ctop - 22, 4, 3, OUT)
    cv.vline(bx1 + 2, ctop - 8, 14, STEEL[4]); cv.rect(bx1 + 1, ctop + 5, 4, 3, OUT); cv.rect(bx1 + 2, ctop + 6, 2, 1, STEEL[5])
    # bowls stacked, a folded cloth
    for k in range(4):
        cv.rect(bx0 + 6 - (k % 2), ctop - 3 - k * 2, 12, 2, OUT if k == 3 else "#e6e2d8")
    cv.hline(bx0 + 5, ctop - 9, 12, "#e6e2d8"); cv.hline(bx0 + 7, ctop - 10, 8, OUT)
    cv.rect(bx0 + 22, ctop - 4, 14, 3, "#e6e2d8"); cv.hline(bx0 + 22, ctop - 3, 14, "#c84a3c")
    # furled umbrella from the back corner
    ux = bx0 + 2
    cv.rect(ux, ctop - 46, 2, 46, OUT)
    cv.poly([(ux - 4, ctop - 18), (ux + 1, ctop - 50), (ux + 6, ctop - 18), (ux + 1, ctop - 14)], OUT)
    cv.poly([(ux - 3, ctop - 19), (ux + 1, ctop - 48), (ux + 5, ctop - 19), (ux + 1, ctop - 16)], RED[3])
    cv.line(ux + 1, ctop - 46, ux + 1, ctop - 17, CANVAS[5]); cv.line(ux + 2, ctop - 44, ux + 4, ctop - 20, RED[4])
    cv.rect(ux - 2, ctop - 30, 6, 2, CANVAS[4])
    cv.rect(ux, ctop - 53, 2, 4, OUT)
    # wheel, leg, handle
    _wheel(cv, bx1 - 14, base - 9, 9)
    cv.rect(bx0 + 4, ctop + 24, 3, base - ctop - 25, OUT); cv.rect(bx0 + 1, base - 2, 9, 2, OUT)
    cv.line(bx0 - 1, ctop + 6, ox, ctop - 2, OUT); cv.line(bx0 - 1, ctop + 7, ox, ctop - 1, OUT)
    cv.rect(ox - 2, ctop - 4, 3, 7, OUT); cv.vline(ox - 1, ctop - 3, 5, "#3a3644")
    return cv, ox + w // 2, base


def half_barrel_planter(width=70, height=44, seed=0, mast=0, mast_dx=0):
    """A whiskey half-barrel planted with arching grasses and orange mums. mast > 0 stands a
    timber festoon mast that tall in it (the strings tie on at its crown).
    Returns (Canvas, anchor_x, anchor_y, crown) with crown the mast top (or None)."""
    rng = _rng(seed)
    w = width
    CW = w + 8
    CH = max(height, mast + 10) + 10
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 4, CH - 3
    cx = ox + w // 2
    ground_shadow(cv, cx, base, w // 2 - 2, 3)
    bw, bh = w - 12, 25
    bx = cx - bw // 2
    btop = base - bh
    crown = None
    if mast:
        mcx = cx + mast_dx
        mt = base - mast
        cv.rect(mcx - 3, mt, 6, base - 8 - mt, OUT)
        cv.rect(mcx - 2, mt + 1, 4, base - 9 - mt, WOOD[3]); cv.vline(mcx - 2, mt + 1, base - 9 - mt, WOOD[4]); cv.vline(mcx + 1, mt + 1, base - 9 - mt, WOOD[2])
        cv.rect(mcx - 4, mt + 2, 8, 3, OUT); cv.hline(mcx - 3, mt + 3, 6, IRON[3])
        cv.rect(mcx - 1, mt - 7, 2, 7, OUT)
        cv.poly([(mcx + 1, mt - 7), (mcx + 9, mt - 5), (mcx + 1, mt - 3)], "#c84a3c")
        for yy in range(mt + 8, base - 10):
            cv.px(mcx + 2, yy, WIRE)
        crown = (mcx, mt + 3)
    # barrel: staves bulging slightly, lit on the left, two iron hoops, rim
    rows = range(btop, base - 1)
    for yy in rows:
        t = (yy - btop) / max(1, bh - 2)
        bulge = int(round(2 * np.sin(np.pi * t)))
        x0, x1 = bx - bulge, bx + bw + bulge
        cv.hline(x0 - 1, yy, x1 - x0 + 2, OUT)
        n = 9
        for k in range(n):
            sx0 = x0 + (x1 - x0) * k // n
            sx1 = x0 + (x1 - x0) * (k + 1) // n
            tone = [WOOD[2], WOOD[3], WOOD[4], WOOD[4], WOOD[4], WOOD[3], WOOD[3], WOOD[2], WOOD[2]][k]
            cv.hline(sx0, yy, sx1 - sx0, tone)
            cv.px(sx0, yy, WOOD[1])
    cv.hline(bx - 1, base - 1, bw + 2, OUT)
    for hy in (btop + 4, base - 7):
        t = (hy - btop) / max(1, bh - 2)
        bulge = int(round(2 * np.sin(np.pi * t)))
        cv.rect(bx - bulge - 1, hy, bw + 2 * bulge + 2, 2, IRON[1]); cv.hline(bx - bulge, hy, bw + 2 * bulge, IRON[3])
        cv.px(bx - bulge + 4, hy, IRON[4])
    cv.rect(bx - 2, btop - 2, bw + 4, 3, OUT); cv.hline(bx - 1, btop - 1, bw + 2, WOOD[5])
    cv.rect(bx, btop + 1, bw, 1, "#2a1e1a")
    # grasses: arching blades in two layers
    for i in range(44):
        sx = bx + 3 + int(rng.integers(0, bw - 6))
        ln = int(rng.integers(9, 24))
        lean = float(rng.uniform(-1.2, 1.2))
        c = [GRASS[4], GRASS[5], GRASS[6], STRAW[4], GRASS[7], STRAW[5]][int(rng.integers(6))]
        for t in range(ln):
            yy = btop - 1 - t
            xx = sx + int(round(lean * (t / ln) ** 2 * 10))
            cv.px(xx, yy, c if t > 3 else GRASS[2])
    # mums: dense domes of small blooms spilling over the rim
    for i in range(8):
        mx = bx + 4 + (bw - 8) * i // 7 + int(rng.integers(-2, 3))
        my = btop - 2 - int(rng.integers(0, 6))
        r = int(rng.integers(4, 6))
        cv.ellipse(mx - r, my - r + 1, 2 * r + 1, 2 * r, LEAF[1])
        cv.ellipse(mx - r + 1, my - r + 1, 2 * r - 1, 2 * r - 2, LEAF[2])
        hue = [MUM[0], MUM[1], MUM[2], MUM[0]][i % 4]
        cv.ellipse(mx - r + 1, my - r + 1, 2 * r - 1, 2 * r - 3, hue)
        for fy in range(my - r + 1, my + r):
            for fx in range(mx - r + 1, mx + r):
                if (fx + fy) % 3 == 0 and (fx - mx) ** 2 + (fy - my) ** 2 < r * r:
                    cv.px(fx, fy, shade(hue, -0.3))
        cv.hline(mx - r // 2, my - r + 1, r, shade(hue, 0.3))
        cv.px(mx - 1, my - r + 2, MUM[3]); cv.px(mx + 1, my - r + 3, MUM[3])
    return cv, cx, base, crown


def wheelie_bins(cv, x, base, kinds=("compost", "recycle", "trash")):
    """A row of wheelie bins with coloured lids and simple symbols, at (x, base)."""
    cols = {"compost": ("#2f5a34", "#4a8a4c", "#86c070"), "recycle": ("#244068", "#3a62a0", "#7aa0d8"),
            "trash": ("#24222c", "#3a3846", "#6a6878")}
    for k, kind in enumerate(kinds):
        d, m, l = cols[kind]
        bx = x + k * 20
        cv.rect(bx, base - 26, 18, 26, OUT)
        cv.rect(bx + 1, base - 22, 16, 20, m); cv.vline(bx + 2, base - 22, 20, l); cv.vline(bx + 15, base - 22, 20, d)
        cv.rect(bx - 1, base - 27, 20, 5, OUT); cv.rect(bx, base - 26, 18, 3, l); cv.hline(bx, base - 24, 18, m)
        cv.rect(bx + 1, base - 3, 4, 4, OUT); cv.rect(bx + 13, base - 3, 4, 4, OUT)
        # label
        cv.rect(bx + 5, base - 17, 8, 7, "#e6e2d8")
        if kind == "compost":
            cv.px(bx + 8, base - 15, "#2f5a34"); cv.rect(bx + 7, base - 14, 3, 2, "#4a8a4c"); cv.px(bx + 9, base - 12, "#2f5a34")
        elif kind == "recycle":
            cv.line(bx + 6, base - 11, bx + 9, base - 16, "#3a62a0"); cv.line(bx + 9, base - 16, bx + 12, base - 11, "#3a62a0"); cv.hline(bx + 6, base - 11, 7, "#3a62a0")
        else:
            cv.rect(bx + 7, base - 15, 4, 4, "#3a3846"); cv.hline(bx + 6, base - 15, 6, "#3a3846")


def queue_marks(cv, x, y, n=4, gap=14, colour="#e6d6b1"):
    """Taped QUEUE HERE floor marks: short bars in a line toward a hatch."""
    for k in range(n):
        cv.rect(x - 5, y + k * gap, 11, 2, colour)
        cv.px(x - 5, y + k * gap + 2, shade(colour, -0.35))


def kiosk(width=64, height=70, name="TOKENS", pal=TRUCK_MUSTARD, open_=False, seed=0):
    """A small box kiosk on skids (token sales, info): flat roof with a sign, one hatch with a
    shutter down (or lit and open), a price list taped beside it. Returns (Canvas, ax, ay, bulbs)."""
    w, h = width, height
    CW, CH = w + 10, h + 8
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 5, CH - 3
    ground_shadow(cv, ox + w // 2, base, w // 2 + 2, 3)
    top = base - h + 12
    cv.rect(ox - 1, top - 1, w + 2, base - top - 2, OUT)
    cv.rect(ox, top, w, base - top - 4, pal[3]); cv.hline(ox, top, w, pal[4]); cv.vline(ox, top, base - top - 4, pal[4])
    cv.rect(ox, base - 12, w, 8, pal[2])
    for sx in range(ox + 8, ox + w - 2, 10):
        cv.vline(sx, top + 2, base - top - 8, pal[2])
    cv.rect(ox - 2, base - 4, w + 4, 3, OUT); cv.hline(ox - 1, base - 3, w + 2, WOOD[3])
    # roof slab and sign
    cv.rect(ox - 4, top - 4, w + 8, 5, OUT); cv.hline(ox - 3, top - 3, w + 6, STEEL[4]); cv.hline(ox - 3, top - 2, w + 6, STEEL[3])
    nw = text_width(name) + 8
    nbx = ox + w // 2 - nw // 2
    cv.rect(nbx, top - 16, nw, 12, OUT); cv.rect(nbx + 1, top - 15, nw - 2, 10, "#f2ead6"); cv.hline(nbx + 1, top - 15, nw - 2, "#ffffff")
    cv.vline(nbx + 4, top - 4, 1, OUT); cv.vline(nbx + nw - 5, top - 4, 1, OUT)
    text(cv, name, nbx + 4, top - 16, pal[1])
    hx0, hx1, hy0, hy1 = ox + 8, ox + w - 18, top + 8, top + 30
    bulbs = []
    cv.rect(hx0 - 1, hy0 - 1, hx1 - hx0 + 2, hy1 - hy0 + 2, OUT)
    if open_:
        cv.rect(hx0, hy0, hx1 - hx0, hy1 - hy0, BULB[1]); cv.rect(hx0, hy0, hx1 - hx0, 3, BULB[0])
        bulbs.append([hx0 + (hx1 - hx0) // 2, hy0 + 4, "fff0c4", 1])
    else:
        for yy in range(hy0, hy1):
            cv.hline(hx0, yy, hx1 - hx0, STEEL[4] if (yy - hy0) % 3 == 0 else STEEL[3])
        cv.rect(hx0, hy1 - 2, hx1 - hx0, 2, STEEL[2])
    cv.rect(hx0 - 3, hy1, hx1 - hx0 + 6, 3, OUT); cv.hline(hx0 - 2, hy1 + 1, hx1 - hx0 + 4, STEEL[4])
    # price list taped beside the hatch
    px0 = hx1 + 4
    cv.rect(px0, hy0, 10, 14, "#f2ead6")
    for k in range(4):
        cv.hline(px0 + 2, hy0 + 3 + k * 3, 6, "#6a6a7a")
    cv.px(px0, hy0, "#c8d8e0"); cv.px(px0 + 9, hy0, "#c8d8e0")
    return cv, ox + w // 2, base, bulbs


def end_face(kind, pal, height, depth=64, trim=STRIPE_TRIM, canopy=RED, seed=0):
    """The end of a truck, stall or kiosk seen square-on, to close off a side-on plane in a battle
    backdrop (the trucks' rear doors and tail lights, the stall's gable). Room scale, same canvas
    height and base row as food_truck / market_stall / kiosk of that height.
    kind: "truck" (height = body height h), "stall" (h), "kiosk" (h)."""
    if kind == "truck":
        CH = height + 22
    else:
        CH = height + 8
    w = depth
    cv = Canvas(w, CH, seed=seed)
    base = CH - 3
    if kind == "truck":
        top, belly = base - height, base - 12
        cv.rect(0, top, w, belly - top + 1, OUT)
        cv.rect(1, top + 1, w - 2, belly - top - 1, shade(pal[3], -0.12)); cv.hline(1, top + 1, w - 2, pal[4])
        cv.rect(1, belly - 8, w - 2, 8, pal[2])
        cv.rect(1, belly - 13, w - 2, 3, trim[0]); cv.hline(1, belly - 10, w - 2, trim[1])
        # rear doors with windows, handles, tail lights, bumper, step
        cv.vline(w // 2, top + 4, belly - top - 6, pal[1])
        for dx in (6, w // 2 + 4):
            cv.rect(dx, top + 8, w // 2 - 10, 14, OUT); cv.rect(dx + 1, top + 9, w // 2 - 12, 12, "#1c2438")
            cv.line(dx + 2, top + 18, dx + 8, top + 10, "#3a4660")
        cv.rect(w // 2 - 4, top + 30, 3, 6, STEEL[4]); cv.rect(w // 2 + 2, top + 30, 3, 6, STEEL[4])
        for tx in (2, w - 6):
            cv.rect(tx, belly - 22, 4, 7, OUT); cv.rect(tx + 1, belly - 21, 2, 5, "#e0402c"); cv.px(tx + 1, belly - 21, "#ff8a6a")
        cv.rect(0, belly, w, 4, OUT); cv.hline(1, belly + 1, w - 2, STEEL[3])
        cv.rect(1, belly + 4, w - 2, base - belly - 4, "#14111c")
        for wx in (3, w - 15):
            cv.rect(wx, base - 15, 12, 15, OUT); cv.rect(wx + 1, base - 14, 10, 13, "#26232e"); cv.hline(wx + 2, base - 13, 8, "#3a3644")
        cv.rect(w // 2 - 8, belly + 4, 16, 3, OUT); cv.hline(w // 2 - 7, belly + 5, 14, STEEL[4])
        # roof vent seen end-on
        cv.rect(w // 2 - 10, top - 6, 20, 6, OUT); cv.rect(w // 2 - 9, top - 5, 18, 5, STEEL[3])
    elif kind == "stall":
        eave = base - int(height * 0.68)
        peak = base - height
        cv.rect(0, eave, w, base - eave, OUT)
        cv.wood(1, eave + 1, w - 2, base - eave - 2, shade(WOOD[3], -0.1), vertical=True, plank=7, seed=seed)
        cv.rect(1, base - 30, w - 2, 3, WOOD[4])
        # gable: the canopy end, a stripe band and its valance
        cv.poly([(-4, eave + 1), (w // 2, peak), (w + 4, eave + 1)], OUT)
        cv.poly([(-2, eave), (w // 2, peak + 2), (w + 2, eave)], CANVAS[3])
        cv.poly([(w // 2 - 6, peak + 6), (w // 2, peak + 2), (w // 2 + 6, peak + 6), (w // 2 + 6, eave), (w // 2 - 6, eave)], canopy[3])
        scallop_valance(cv, -2, eave, w + 4, depth=6, pal_a=canopy, pal_b=CANVAS, stripe=8)
    else:
        top = base - height + 12
        cv.rect(0, top - 1, w, base - top - 2, OUT)
        cv.rect(1, top, w - 2, base - top - 4, shade(pal[3], -0.12)); cv.hline(1, top, w - 2, pal[4])
        cv.rect(w // 2 - 8, top + 10, 16, base - top - 14, OUT); cv.rect(w // 2 - 7, top + 11, 14, base - top - 16, pal[2])
        cv.px(w // 2 + 4, top + 28, STEEL[5])
        cv.rect(-2, top - 4, w + 4, 5, OUT); cv.hline(-1, top - 3, w + 2, STEEL[4])
        cv.rect(0, base - 4, w, 3, OUT)
    return cv
