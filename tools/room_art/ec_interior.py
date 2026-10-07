"""The Engineering Center's own building fabric, for the interior rooms E02-E05 and their battles.

CU Boulder's Engineering Center (1965, William Muchow with Pietro Belluschi) is raw board-formed
concrete inside and out ("the concrete coffin", "the mineshaft"): grey, weathered walls printed with
the grain of the plank formwork, a grid of form-tie holes, darker run-off streaks below them and
under every sill, pour lifts where one day's concrete met the next. Accents of rough Lyons
sandstone (the campus flagstone, pinkish tan to rusty red, laid in irregular courses) wrap lower
bands and piers. Overhead: exposed concrete beams and coffers, conduit, caged and fluorescent
lamps. Windows are narrow slots set deep in thick concrete frames.

Everything paints at 1:1 game pixels with clean tone clusters (no speckle): the wall surfaces are
built as an index array over a palette, so each board, grain streak and stain is a run of one tone.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
import lib_eng as E
from lib_eng import CONC, STEEL, WARM, OUT, NIGHT_BANDS, hashn, put_rgb, soft_field, micro_text
from lib_umc import halo, SHADOW, SAFETY

# Board-formed concrete (lib_eng's CONC, the same grey as the E01 exterior), 9 tones.
# Lyons sandstone: three families seen in one wall (tan-pink, rose, rust), body tones at [2..3].
LYONS = [
    ["#4e3832", "#7a5a4c", "#9c7a64", "#b69278", "#cfae90", "#e2c6a4"],   # buff / tan-pink
    ["#4c322e", "#764c44", "#946456", "#aa7a6a", "#c29482", "#d6ac96"],   # rose
    ["#46281f", "#6c3c2e", "#8a5038", "#a06448", "#b87e5e", "#cc9878"],   # rust red
]
MORTAR = ["#2e2628", "#4a3e3c", "#5e5250"]
CAGE = ["#14121a", "#2a2a34", "#4a4a56", "#6e6e7c"]


# ------------------------------------------------------------------------------ concrete

def board_index(w, h, x=0, y=0, seed=0, board=6, lift=48, ties=(24, 18), tie_off=(11, 8), base=5,
                streaks=0.32, stains=0.22, foot=6, panel=None, tie=2):
    """Palette indices (into CONC) for a board-formed concrete wall of w x h whose top-left sits at
    global (x, y), so neighbouring pieces line up. board: plank height; lift: pour-lift spacing;
    ties: form-tie grid pitch (None for none); streaks: share of tie holes that weep a dark run;
    stains: share of 7px column bands that carry a water stain from the top; foot: dirty band."""
    ys, xs = np.mgrid[0:h, 0:w]
    gx, gy = xs + x, ys + y
    row = gy // board
    iy = gy % board
    idx = np.full((h, w), base, np.int32)
    # planks: each course is cut into boards of its own length, staggered, each a tone off
    seglen = 34 + (hashn(row, 0, seed) * 52).astype(np.int32)
    shift = (hashn(row, 1, seed) * 97).astype(np.int32)
    seg = (gx + shift) // seglen
    segpos = (gx + shift) % seglen
    tone = hashn(seg, row, seed + 2)
    idx += np.where(tone < 0.16, -1, np.where(tone > 0.92, 1, 0))
    # broad pour mottling
    f = soft_field(w, h, 46, seed + 3) if w > 0 and h > 0 else np.zeros((h, w))
    idx -= (f < 0.2).astype(np.int32)
    idx += (f > 0.9).astype(np.int32)
    # wood grain: short streaks a tone darker inside the plank body, a few lit ones
    if board >= 4:
        body = (iy >= 1) & (iy <= board - 2)
        lane = hashn(seg * 7 + iy, row, seed + 4)
        g0 = hashn(seg, row * 5 + iy, seed + 5) * seglen
        gl = 5 + hashn(seg, row * 5 + iy, seed + 6) * 22
        on = (segpos >= g0) & (segpos < g0 + gl)
        idx -= (body & on & (lane < 0.34)).astype(np.int32)
        idx += (body & on & (lane > 0.93)).astype(np.int32)
        # knots: a 2px dark eye in a few boards
        kp = (hashn(seg, row, seed + 7) * (seglen - 6)).astype(np.int32) + 3
        knot = (hashn(seg, row, seed + 8) < 0.07) & (iy == board // 2) & ((segpos == kp) | (segpos == kp + 1))
        idx = np.where(knot, idx - 2, idx)
    # plank edges: a lit lip on top, a shadowed seam at the bottom, butt joints
    lip = hashn(seg, row, seed + 12)
    idx = np.where((iy == 0) & (lip < 0.45), idx + 1, idx)
    idx = np.where(iy == board - 1, idx - 1, idx)
    idx = np.where((segpos == 0) & (iy < board - 1) & (lip > 0.35), idx - 1, idx)
    if panel:
        idx = np.where(gx % panel == 0, idx - 1, idx)
    # pour lifts: a cold joint line with a lit lower edge
    if lift:
        idx = np.where(gy % lift == lift - 1, 2, idx)
        idx = np.where(gy % lift == 0, idx + 1, idx)
    # water stains running down from the top in a few column bands, ragged ends
    if stains:
        band = gx // 7
        has = hashn(band, 3, seed + 9) < stains
        L = (10 + hashn(band, 4, seed + 9) * h * 0.8).astype(np.int32) + (hashn(gx, 5, seed + 9) * 7).astype(np.int32)
        wid = 2 + (hashn(band, 6, seed + 9) * 4).astype(np.int32)
        inband = (gx % 7) < wid
        st = has & inband & (ys < L)
        idx -= st.astype(np.int32)
        idx -= (st & (ys < L // 3)).astype(np.int32)
    # form-tie holes with weeping runs below some of them
    if ties:
        tx, ty = ties
        ox, oy = tie_off
        hx, hy = (gx - ox) % tx, (gy - oy) % ty
        hid = hashn((gx - ox) // tx, (gy - oy) // ty, seed + 10)
        runl = (3 + hid * 40).astype(np.int32) % 14 + 3
        ts = tie
        run = (hx < ts) & (hy >= ts) & (hy < ts + runl // (3 - ts if ts < 3 else 1)) & (hid < streaks)
        idx -= run.astype(np.int32)
        hole = (hx < ts) & (hy < ts)
        idx = np.where(hole, 1 if ts > 1 else np.maximum(idx - 2, 1), idx)
        if ts > 1:
            idx = np.where((hx < ts) & (hy == ts) & ~run, idx + 1, idx)
            idx = np.where((hx == ts) & (hy < ts), idx + 1, idx)
    # dirt along the wall foot
    if foot:
        fj = (hashn(gx // 3, 7, seed + 11) * 3).astype(np.int32)
        idx -= (ys >= h - foot + fj).astype(np.int32)
    return np.clip(idx, 1, len(CONC) - 1)


def board_concrete(cv, x, y, w, h, seed=0, pal=CONC, **kw):
    """Paint a board-formed concrete wall into the canvas (see board_index for the options)."""
    if w <= 0 or h <= 0:
        return
    idx = board_index(w, h, x, y, seed=seed, **kw)
    put_rgb(cv, x, y, E.P(pal)[idx])


def conc_pier(cv, x, y, w, h, seed=0, ties=True):
    """A board-formed concrete pier standing proud of the wall: chamfered lit left arris, a
    shadowed right face and the shadow it throws on the wall to its right."""
    cv.rect(x + w, y, 4, h, C(SHADOW, 0.32))
    board_concrete(cv, x, y, w, h, seed=seed, base=6, lift=48, ties=(w // 2, 18) if ties else None,
                   tie_off=(x + w // 2 - 1, 9), stains=0.3, foot=5)
    cv.vline(x, y, h, CONC[7]); cv.vline(x + 1, y, h, CONC[8])
    cv.rect(x + w - 3, y, 3, h, C(CONC[2], 0.7)); cv.vline(x + w - 1, y, h, CONC[1])


def conc_cap(cv, x, y, w, depth=3):
    """A cast concrete sill / coping strip: lit top, face, shadow line under."""
    cv.rect(x, y, w, depth, CONC[6]); cv.hline(x, y, w, CONC[8]); cv.hline(x, y + depth - 1, w, CONC[4])
    cv.hline(x, y + depth, w, C(SHADOW, 0.55))


def edge_beam(cv, x, y, w, h=9, seed=0):
    """The exposed concrete beam along the top of a wall (board-formed face, lit underside)."""
    board_concrete(cv, x, y, w, h, seed=seed, base=4, lift=None, ties=None, stains=0, foot=0, board=4)
    cv.hline(x, y, w, CONC[2])
    cv.hline(x, y + h - 2, w, CONC[6]); cv.hline(x, y + h - 1, w, CONC[7])
    cv.rect(x, y + h, w, 3, C(SHADOW, 0.45))


def coffered_ceiling(cv, x, w, y=0, h=22, seed=0, bay=30, rib=5):
    """Exposed concrete overhead, seen past the top of the back wall: a waffle slab's coffers in
    two rows (each recess dark, its far inner face catching lamp light), the ribs between them
    pale, then the deep edge beam on the wall line with its shadow on the wall."""
    eb = 9
    sh = h - eb
    cv.rect(x, y, w, sh, CONC[3])
    board_concrete(cv, x, y, w, sh, seed=seed, base=3, board=3, lift=None, ties=None, stains=0, foot=0)
    rows = [(y + 1, sh // 2 - 2), (y + sh // 2 + 1, sh - sh // 2 - 2)]
    for r, (ry, rh) in enumerate(rows):
        off = (bay // 2) * 0
        for cx in range(x - bay + off + rib, x + w, bay):
            cw = bay - rib - (0 if r else 2)
            x0 = cx + (1 if r == 0 else 0)
            cv.rect(x0, ry, cw, rh, CONC[0])
            cv.rect(x0, ry, cw, 2 if rh > 4 else 1, CONC[4])            # far inner face, lit
            cv.vline(x0, ry, rh, CONC[2]); cv.vline(x0 + cw - 1, ry + 1, rh - 1, CONC[2])
            cv.px(x0, ry, CONC[5])
        cv.hline(x, ry + rh, w, CONC[6])                                   # rib underside, lit
    edge_beam(cv, x, y + sh, w, eb, seed=seed + 1)
    return []


def conduit(cv, x0, x1, y, drops=(), boxes=()):
    """Surface-run EMT conduit with straps; drops: (x, y_end) runs down to a box; boxes: (x, y)."""
    cv.rect(x0, y, x1 - x0, 2, STEEL[3]); cv.hline(x0, y, x1 - x0, STEEL[6]); cv.hline(x0, y + 2, x1 - x0, C(SHADOW, 0.4))
    for sx in range(x0 + 14, x1, 34):
        cv.rect(sx, y - 1, 2, 4, STEEL[2])
    for (dx, ye) in drops:
        cv.rect(dx, y, 2, ye - y, STEEL[3]); cv.vline(dx, y, ye - y, STEEL[6]); cv.vline(dx + 2, y + 2, ye - y - 2, C(SHADOW, 0.4))
        cv.rect(dx - 1, y - 1, 4, 4, STEEL[4])
        jbox(cv, dx + 1, ye)
    for (bx, by) in boxes:
        jbox(cv, bx, by)


def jbox(cv, cx, y):
    """A small grey junction box / outlet on the concrete (centred on cx, top at y)."""
    cv.rect(cx - 4, y, 9, 8, OUT); cv.rect(cx - 3, y + 1, 7, 6, STEEL[5]); cv.hline(cx - 3, y + 1, 7, STEEL[6])
    cv.rect(cx - 1, y + 3, 3, 2, STEEL[2])


def cage_lamp(cv, x, y_top, drop, lit=True):
    """A caged industrial lamp on a conduit drop: a steel box, a bulb in a wire guard. Returns
    the bulb point."""
    cv.rect(x, y_top, 2, drop, STEEL[2]); cv.vline(x, y_top, drop, STEEL[5])
    y = y_top + drop
    cv.rect(x - 4, y, 10, 4, OUT); cv.rect(x - 3, y + 1, 8, 2, STEEL[4]); cv.hline(x - 3, y + 1, 8, STEEL[6])
    bulb = WARM[4] if lit else "#5a5664"
    cv.rect(x - 2, y + 4, 6, 6, WARM[3] if lit else "#46424e"); cv.rect(x - 1, y + 5, 4, 4, bulb)
    for gx in (x - 3, x + 1, x + 4):
        cv.vline(gx, y + 4, 7, CAGE[0])
    cv.hline(x - 3, y + 7, 8, CAGE[0]); cv.hline(x - 2, y + 11, 6, CAGE[0])
    cv.px(x - 3, y + 4, CAGE[2]); cv.px(x + 4, y + 4, CAGE[2])
    if lit:
        halo(cv, x + 1, y + 8, 18, "#f6cf7a", 0.08, 3)
    return (x + 1, y + 7)


def strip_light(cv, x, y, w, chain=6, lit=True):
    """A two-tube fluorescent strip hung on chains (x = left end). Returns the tube's centre."""
    for cx in (x + 4, x + w - 5):
        for k in range(0, chain, 2):
            cv.px(cx, y + k, STEEL[4]); cv.px(cx, y + k + 1, STEEL[2])
    yy = y + chain
    cv.rect(x, yy, w, 4, OUT); cv.rect(x + 1, yy, w - 2, 2, STEEL[4]); cv.hline(x + 1, yy, w - 2, STEEL[6])
    cv.rect(x + 2, yy + 2, w - 4, 2, "#f2f0e0" if lit else "#4a4856")
    if lit:
        cv.hline(x + 3, yy + 3, w - 6, "#c8e0e8")
        E.stepped_glow(cv, x + w // 2, yy + 6, w // 2 + 10, 6, "#e8f0e8", 0.08, 2)
    return (x + w // 2, yy + 3)


def deep_window(cv, x, y, w, h, seed=0, depth=4, sky=True, mullion=True):
    """A narrow window set deep in a thick concrete frame: lit left reveal and sill, a dark head,
    the night beyond, run-off streaks under the sill. Returns star points."""
    rng = np.random.default_rng(seed)
    d = depth
    # the reveal (frame thickness), then the glass set back inside it
    cv.rect(x - d, y - d, w + 2 * d, h + 2 * d, CONC[3])
    cv.poly([(x - d, y - d), (x, y), (x, y + h), (x - d, y + h + d)], CONC[6])           # left reveal, lit
    cv.poly([(x + w + d - 1, y - d), (x + w - 1, y), (x + w - 1, y + h), (x + w + d - 1, y + h + d)], CONC[2])
    cv.rect(x - d, y - d, w + 2 * d, d, CONC[1])                                             # head in shadow
    cv.rect(x - d, y + h, w + 2 * d, d, CONC[5]); cv.hline(x - d, y + h, w + 2 * d, CONC[7])  # sill
    cv.hline(x - d - 1, y + h + d, w + 2 * d + 2, CONC[8])
    pts = []
    if sky:
        for k in range(h):
            cv.hline(x, y + k, w, NIGHT_BANDS[min(len(NIGHT_BANDS) - 1, k * 4 // max(1, h))])
        for _ in range(max(1, w * h // 120)):
            sx, sy = x + int(rng.integers(1, max(2, w - 1))), y + int(rng.integers(1, max(2, h * 2 // 3)))
            cv.px(sx, sy, "#c8ccec"); pts.append((sx, sy, "#e8ecff"))
        cv.line(x + 1, y + h - 2, x + min(w - 2, 6), y + h - 8, C("#8a90c0", 0.35))
    cv.rect(x, y, w, 1, STEEL[0]); cv.rect(x, y, 1, h, STEEL[0])
    if mullion and w >= 10:
        cv.vline(x + w // 2, y, h, STEEL[2])
    if mullion and h >= 20:
        cv.hline(x, y + h * 2 // 3, w, STEEL[2])
    # weathering under the sill
    for sx in (x + 1, x + w - 3):
        cv.rect(sx, y + h + d + 1, 2, 4 + int(rng.integers(0, 8)), C(CONC[2], 0.55))
    return pts


# ----------------------------------------------------------------------------- sandstone

def lyons_wall(cv, x, y, w, h, seed=0, course=(5, 6, 7, 8, 9, 10), length=(12, 38), cap=True, mortar=MORTAR[1],
               rust=0.14, rose=0.34, tall=0.16):
    """Rough Lyons sandstone in irregular courses: stones of three tone families (buff, rose,
    rust), each with a lit top bed, a shadowed foot and right joint, sometimes a bedding line or a
    pitted chip; beds jog a pixel; some stones run through two courses (tall); recessed dark
    mortar; an optional cast concrete cap on top."""
    rng = np.random.default_rng(seed)
    top = y
    if cap:
        conc_cap(cv, x, y, w, 3)
        top = y + 4
    cv.rect(x, top, w, y + h - top, mortar)
    busy = []                                   # (x0, x1, bottom) of tall stones from the course above
    yy = top
    while yy < y + h:
        ch = min(int(rng.choice(course)), y + h - yy)
        busy = [b for b in busy if b[2] > yy]
        xx = x - int(rng.integers(0, length[1]))
        while xx < x + w:
            sw = int(rng.integers(length[0], length[1] + 1))
            hit = [b for b in busy if b[0] < xx + sw and b[1] > xx]
            if hit:
                xx = max(b[1] for b in hit) + 1
                continue
            x0, x1 = max(x, xx), min(x + w, xx + sw - 1)
            r = rng.random()
            fam = LYONS[2] if r < rust else LYONS[1] if r < rust + rose else LYONS[0]
            body = fam[3] if rng.random() < 0.6 else fam[2]
            jt = int(rng.choice([0, 0, 0, 1]))
            jb = int(rng.choice([0, 0, 1]))
            sh_ = ch
            if rng.random() < tall and yy + ch + 4 < y + h and sw < length[1] * 0.8:
                sh_ = ch + int(rng.choice(course))
                sh_ = min(sh_, y + h - yy)
                busy.append((xx, xx + sw, yy + sh_))
            sy0, sh = yy + jt, sh_ - 1 - jt - jb
            if x1 - x0 >= 2 and sh >= 2:
                cv.rect(x0, sy0, x1 - x0, sh, body)
                cv.hline(x0, sy0, x1 - x0, fam[4])                          # lit bed edge
                cv.hline(x0 + 1, sy0 + sh - 1, x1 - x0 - 1, fam[1])          # shadowed foot
                cv.vline(x1 - 1, sy0 + 1, sh - 1, fam[1])
                if rng.random() < 0.45 and sh >= 4 and x1 - x0 > 8:          # bedding streak
                    by = sy0 + 1 + int(rng.integers(0, sh - 2))
                    bx = x0 + int(rng.integers(1, (x1 - x0) // 2))
                    cv.hline(bx, by, int(rng.integers(3, max(4, (x1 - x0) - (bx - x0) - 1))),
                             fam[2] if body == fam[3] else fam[4])
                if rng.random() < 0.2:                                       # a pitted chip
                    px_ = x0 + int(rng.integers(1, max(2, x1 - x0 - 2)))
                    cv.rect(px_, sy0 + 1, 2, 1, fam[1])
            xx += sw
        yy += ch
    cv.hline(x, y + h - 1, w, C(SHADOW, 0.5))


def lyons_pier(cv, x, y, w, h, seed=0):
    """A sandstone-clad pier: big irregular blocks, lit left arris, shaded right, cast shadow."""
    cv.rect(x + w, y, 4, h, C(SHADOW, 0.32))
    lyons_wall(cv, x, y, w, h, seed=seed, course=(7, 8, 9, 10), length=(8, max(10, w)), cap=False)
    cv.vline(x, y, h, LYONS[0][4])
    cv.rect(x + w - 2, y, 2, h, C(SHADOW, 0.35))


# --------------------------------------------------------------------- battle (perspective)

def conc_texture(w, h, seed=0, **kw):
    """A board-formed concrete texture as a float RGBA array (for persp planes / texture_lookup)."""
    cv = Canvas(w, h)
    board_concrete(cv, 0, 0, w, h, seed=seed, **kw)
    return cv


def lyons_texture(w, h, seed=0, **kw):
    cv = Canvas(w, h)
    lyons_wall(cv, 0, 0, w, h, seed=seed, **kw)
    return cv


def beam_ceiling_shader(X, Z, bay_z=120.0, bay_x=170.0, z0=300.0, fog_to=800.0, fog_col="#12121c"):
    """Shader for a concrete ceiling seen from below: coffers between cross beams (every bay_z of
    depth) and longitudinal beams (every bay_x), each beam a pale underside with a lit near arris."""
    from persp import pal_array, rgba_of, fog, hash2
    c = pal_array(CONC)
    rgb = np.empty(X.shape + (3,), np.float32)
    rgb[:] = c[1]
    rgb[(np.floor(Z / 9) % 2) == 0] = c[2] * 0.85 + c[1] * 0.15             # board marks on the soffit
    dz = (Z - z0) % bay_z
    cross = dz < 16
    rgb[cross] = c[4]
    rgb[cross & (dz < 3)] = c[2]
    rgb[cross & (dz > 13)] = c[6]
    dx = np.abs(((X + bay_x / 2) % bay_x) - bay_x / 2)
    lon = dx < 9
    rgb[lon & ~cross] = c[3]
    rgb[lon & ~cross & (dx > 7)] = c[5]
    pit = (hash2(np.floor(X / 5), np.floor(Z / 5), 31) > 0.985) & ~cross & ~lon
    rgb[pit] = c[3]
    out = rgba_of(rgb)
    fog(out, Z, fog_col, 420, fog_to, amount=0.45)
    return out


# ------------------------------------------------------------- signal-integrity bench (E03)

TRACE_CY = ["#0a1a22", "#14384a", "#2a6e8a", "#4ab8d8", "#9aeeff", "#e4fcff"]    # channel 1, cyan
TRACE_YE = ["#2a2410", "#6a5a1c", "#b8a03a", "#f0d860", "#fff4b0"]               # channel 2, yellow
SCREEN_BG = "#071016"
PCB = ["#0a2016", "#10321f", "#17462b", "#205c38", "#2e7448", "#4a9462"]
GOLD = ["#6a4a18", "#a87a2a", "#d8aa48", "#f2d27a"]
INSTR = ["#16181f", "#24272f", "#343842", "#474c58", "#5e6472", "#7a8090", "#9aa0ae"]
CABLE = {"sma": ("#c46a24", "#e89a50"), "probe": ("#1c1e26", "#4a4e5a"), "blue": ("#2c4a9a", "#5a7ad0")}


def _plot(acc, xs, ys):
    h, w = acc.shape
    prev = None
    for x, y in zip(xs, ys):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < w:
            if prev is not None and abs(y - prev) > 1:
                lo, hi = sorted((prev, y))
                acc[max(0, lo):min(h, hi + 1), x] += 1
            elif 0 <= y < h:
                acc[y, x] += 1
        prev = y


def si_screen_frame(w, h, k, n, kind="eye", grid=True):
    """One frame of a signal-integrity scope screen. kind: "eye" (an eye diagram drawn with
    phosphor persistence, shimmering with jitter), "ring" (a fast edge ringing out, the ring
    breathing), "tdr" (a TDR impedance step with a dip at a via), "xtalk" (an aggressor edge and
    the victim's crosstalk blip). Colours come in persistence bands, never smooth."""
    cv = Canvas(w, h, fill=SCREEN_BG)
    if grid:
        for gx in range(0, w, max(4, w // 8)):
            for gy in range(1, h, 2):
                cv.px(gx, gy, "#0e222c")
        for gy in range(0, h, max(4, h // 6)):
            for gx in range(1, w, 2):
                cv.px(gx, gy, "#0e222c")
    acc = np.zeros((h, w), np.float32)
    acc2 = np.zeros((h, w), np.float32)
    rng = np.random.default_rng(100 + k)
    ph = 6.2832 * k / max(1, n)
    top, bot = h * 0.16, h * 0.84
    mid = (top + bot) / 2
    amp = (bot - top) / 2
    t = np.linspace(0, 1, w * 3)
    if kind == "eye":
        ui = w / 2.0
        lv = lambda v: -1.0 if v == 0 else 1.0
        for b in range(26):
            p0, a, bb, c = rng.integers(0, 2, 4)
            jit = rng.normal(0, 1.3) + 0.8 * np.sin(ph + b * 0.7)
            xs = t * w
            u = (xs - ui * 0.5 - jit) / (ui * 0.12)
            u2 = (xs - ui * 1.5 - jit) / (ui * 0.12)
            isi = 0.1 * (lv(p0) - lv(a)) * 0.5
            y = lv(a) + isi + (lv(bb) - lv(a) - isi) * (0.5 + 0.5 * np.tanh(u)) + (lv(c) - lv(bb)) * (0.5 + 0.5 * np.tanh(u2))
            for uu, d in ((u, lv(bb) - lv(a)), (u2, lv(c) - lv(bb))):
                q = np.clip(uu - 1.0, 0, None)
                y = y + 0.16 * d * np.exp(-q * 0.22) * np.sin(q * 0.9) * (uu > 1.0)
            y = y + rng.normal(0, 0.03)
            _plot(acc, xs, mid - y * amp * 0.86)
    elif kind == "ring":
        xs = t * w
        e = w * 0.28
        u = (xs - e) / (w * 0.012)
        decay = 0.55 + 0.25 * np.sin(ph)
        y = np.tanh(u) + 0.7 * np.exp(-np.clip(xs - e, 0, None) / (w * 0.2 * decay)) * np.sin(np.clip(xs - e, 0, None) / (w * 0.022)) * (xs > e)
        _plot(acc, xs, mid - y * amp * 0.82)
        u2 = (xs - e - 3) / (w * 0.02)
        _plot(acc2, xs, bot + 2 - 0.5 * amp * (0.5 + 0.5 * np.tanh(u2)))
    elif kind == "tdr":
        xs = t * w
        y = np.where(xs < w * 0.18, -0.9, 0.0)
        y = y + 0.0 * xs
        y += -0.35 * np.exp(-((xs - w * (0.55 + 0.05 * np.sin(ph))) / (w * 0.04)) ** 2)
        y += 0.25 * np.exp(-((xs - w * 0.78) / (w * 0.05)) ** 2)
        y = np.where(xs < w * 0.18, -0.9, y + 0.1 * np.exp(-(xs - w * 0.18) / (w * 0.04)) * (xs >= w * 0.18))
        _plot(acc, xs, mid - y * amp * 0.8)
    else:   # xtalk
        xs = t * w
        e = w * (0.35 + 0.04 * np.sin(ph))
        y1 = np.tanh((xs - e) / (w * 0.015))
        _plot(acc2, xs, top + amp * 0.45 - y1 * amp * 0.35)
        blip = 0.5 * np.exp(-((xs - e) / (w * 0.03)) ** 2) * np.sin((xs - e) / (w * 0.012))
        _plot(acc, xs, bot - amp * 0.35 - blip * amp * 0.8)
    for a, pal in ((acc, TRACE_CY), (acc2, TRACE_YE)):
        ys, xs_ = np.nonzero(a)
        for y, x in zip(ys, xs_):
            v = a[y, x]
            c = pal[2] if v < 1.5 else pal[3] if v < 3.5 else pal[4]
            cv.px(int(x), int(y), c)
    return cv


def coil(cv, cx, cy, r, colour, hi, loops=3):
    """A coil of cable hanging from a hook at (cx, cy - r): a few overlapping loop outlines."""
    for k in range(loops):
        ox = k - loops // 2
        for a in np.linspace(0, 6.2832, 10 * r, endpoint=False):
            x = int(round(cx + ox + np.cos(a) * r * 0.8))
            y = int(round(cy + np.sin(a) * r))
            cv.px(x, y, colour)
        cv.px(cx + ox - int(r * 0.8), cy, hi)
    cv.px(cx, cy - r, hi)


def ring_coil(cv, cx, cy, r, colour, hi):
    """A coiled cable seen face on (an open ring of a few turns)."""
    for d in range(r - 2, r + 1):
        for a in np.linspace(0, 6.2832, 8 * r, endpoint=False):
            cv.px(int(round(cx + np.cos(a) * d)), int(round(cy + np.sin(a) * d * 0.9)), colour)
    for a in np.linspace(3.6, 4.6, 5):
        cv.px(int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r * 0.9)), hi)


def pcb(cv, x, y, w, h, seed=0, sma=True, chips=2):
    """A test board: green solder mask, gold differential pairs meandering between SMA edge
    launches, a couple of chips, a scatter of vias in rows."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, PCB[3]); cv.hline(x + 1, y + 1, w - 2, PCB[4])
    lanes = list(range(y + 2, y + h - 1, 2 if h < 10 else 4)) or [y + h // 2]
    for i, ly in enumerate(lanes):
        xx = x + 3
        yy = ly
        while xx < x + w - 3:
            cv.px(xx, yy, GOLD[2] if i % 2 == 0 else GOLD[1])
            if h >= 10 and rng.random() < 0.08 and y + 2 < yy + (1 if yy < ly + 1 else -1) < y + h - 2:
                yy += 1 if yy <= ly else -1
            xx += 1
    for _ in range(max(2, w * h // 60)):
        vx, vy = x + int(rng.integers(2, w - 2)), y + int(rng.integers(2, h - 2))
        cv.px(vx, vy, GOLD[3])
    for c in range(chips):
        cx = x + 6 + c * (w - 12) // max(1, chips)
        if h >= 8:
            cv.rect(cx, y + h // 2 - 2, 5, 4, "#16161c"); cv.hline(cx, y + h // 2 - 2, 5, "#34343e")
    if sma:
        for ly in (lanes[0], lanes[-1]):
            cv.rect(x - 2, ly - 1, 3, 3, GOLD[2]); cv.px(x - 2, ly, GOLD[3])
            cv.rect(x + w - 1, ly - 1, 3, 3, GOLD[2]); cv.px(x + w, ly, GOLD[3])


def scope_body(cv, x, y, w, h):
    """A bench oscilloscope: dark body, the screen (returned), a knob column with four channel
    keys, BNC inputs along the bottom edge. Returns (screen rect, input points)."""
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, INSTR[3]); cv.hline(x + 1, y + 1, w - 2, INSTR[5])
    cv.vline(x + 1, y + 1, h - 2, INSTR[4])
    sw, sh = w - 16, h - 9
    cv.rect(x + 3, y + 3, sw + 2, sh + 2, INSTR[0])
    screen = (x + 4, y + 4, sw, sh)
    kx = x + w - 10
    cv.rect(kx, y + 3, 8, h - 6, INSTR[2])
    for j, col in enumerate(("#f0d860", "#4ab8d8", "#d860b0", "#5a7ad0")):
        yy = y + 4 + j * 3
        if yy + 2 < y + h - 4:
            cv.rect(kx + 1, yy, 2, 2, col); cv.px(kx + 5, yy, INSTR[6]); cv.px(kx + 6, yy + 1, INSTR[1])
    ins = []
    for j in range(4):
        bx = x + 5 + j * 6
        if bx < x + sw:
            cv.rect(bx, y + h - 4, 3, 2, INSTR[6]); cv.px(bx + 1, y + h - 4, INSTR[0])
            ins.append((bx + 1, y + h - 2))
    cv.rect(x + 2, y + h, w - 4, 1, C(SHADOW, 0.5))
    return screen, ins


def vna_box(cv, x, y, w=34, h=16, label="VNA"):
    """A two-port network analyser / TDR: pale case, a small screen with a Smith chart and a
    trace, two SMA ports. Returns (screen rect, port points)."""
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#b8b6ae"); cv.hline(x + 1, y + 1, w - 2, "#dcdad2")
    cv.vline(x + 1, y + 1, h - 2, "#cac8c0"); cv.hline(x + 1, y + h - 2, w - 2, "#8a8880")
    sx, sy, sw, sh = x + 3, y + 3, min(16, w // 2), h - 6
    cv.rect(sx - 1, sy - 1, sw + 2, sh + 2, INSTR[1]); cv.rect(sx, sy, sw, sh, SCREEN_BG)
    cx, cy, r = sx + sw // 2, sy + sh // 2, max(2, sh // 2 - 1)
    for a in np.linspace(0, 6.2832, 24, endpoint=False):
        cv.px(int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r)), "#1e4a5a")
    cv.hline(cx - r, cy, 2 * r + 1, "#1e4a5a")
    micro_text(cv, label, x + sw + 6, y + 3, "#3a3a46")
    ports = []
    for j in range(2):
        px_ = x + sw + 7 + j * 8
        cv.rect(px_, y + h - 6, 4, 3, GOLD[1]); cv.px(px_ + 1, y + h - 5, GOLD[3])
        ports.append((px_ + 2, y + h - 4))
    return (sx, sy, sw, sh), ports


def cable(cv, a, b, sag, kind="sma"):
    col, hi = CABLE[kind]
    E.wire(cv, a[0], a[1], b[0], b[1], sag, col, hi)


def si_bench(cv, x, base, w=112, seed=0):
    """The signal-integrity probe bench against the wall: a steel bench with an ESD mat, a
    four-channel scope with a lit eye diagram, a VNA/TDR box, a test board under a probe arm,
    SMA and probe cables looping between them, coiled cables on a wall hook, a parts bin on the
    lower shelf. Returns animation anchors."""
    top = base - 26
    # frame, legs, lower shelf
    cv.rect(x, top, w, 4, OUT); cv.rect(x + 1, top + 1, w - 2, 2, "#3a5070"); cv.hline(x + 1, top + 1, w - 2, "#5a7496")
    cv.rect(x + 1, top + 3, w - 2, 1, INSTR[2])
    for lx in (x + 3, x + w - 6):
        cv.rect(lx, top + 4, 3, base - top - 4, OUT); cv.vline(lx + 1, top + 4, base - top - 5, INSTR[5])
    sy = base - 9
    cv.rect(x + 3, sy, w - 6, 3, OUT); cv.rect(x + 4, sy, w - 8, 2, INSTR[4]); cv.hline(x + 4, sy, w - 8, INSTR[6])
    # lower shelf: a parts bin and a stack of boards in ESD bags, a second VNA cal kit case
    cv.rect(x + 10, sy - 7, 20, 7, OUT); cv.rect(x + 11, sy - 6, 18, 5, "#2c4a8a"); cv.hline(x + 11, sy - 6, 18, "#4a6ab0")
    for k in range(3):
        cv.rect(x + 36 + k * 2, sy - 3 - k * 2, 24, 2, ("#8a8a96", "#a6a6b0", "#9a9aa6")[k])
    cv.rect(x + 70, sy - 8, 26, 8, OUT); cv.rect(x + 71, sy - 7, 24, 6, "#1e2028"); cv.rect(x + 80, sy - 7, 6, 2, GOLD[1])
    cv.rect(x + 2, base - 1, w - 4, 1, C(SHADOW, 0.5))
    # scope
    screen, ins = scope_body(cv, x + 4, top - 30, 46, 30)
    # VNA / TDR beside it
    vscreen, ports = vna_box(cv, x + 54, top - 16, 36, 16, "TDR")
    # the test board under a probe arm, on the mat
    pcb(cv, x + 91, top - 4, 18, 5, seed=seed + 3, chips=1)
    cv.rect(x + w - 6, top - 22, 3, 18, INSTR[2]); cv.vline(x + w - 6, top - 22, 18, INSTR[5])     # probe arm post
    cv.line(x + w - 5, top - 21, x + 100, top - 14, INSTR[5]); cv.line(x + 100, top - 14, x + 100, top - 6, "#e4e4ec")
    cv.rect(x + 98, top - 16, 4, 3, "#c03a32")
    # cables: probes from the scope inputs to the board, SMA from the TDR ports
    for k, (ix, iy) in enumerate(ins[:2]):
        cable(cv, (ix, iy), (x + 92 + k * 6, top - 2), 5 + k * 2, "probe" if k == 0 else "blue")
    cable(cv, ports[0], (x + 92, top - 3), 3, "sma")
    cable(cv, ports[1], (x + 108, top - 3), 2, "sma")
    # coiled cables on a wall hook above, a probe holder, a tag on the bench edge
    hx, hy = x + 70, top - 40
    cv.rect(hx - 1, hy - 2, 3, 3, INSTR[5])
    coil(cv, hx, hy + 6, 6, CABLE["sma"][0], CABLE["sma"][1], 3)
    coil(cv, hx + 14, hy + 7, 5, CABLE["probe"][0], CABLE["probe"][1], 3)
    cv.rect(hx + 13, hy - 2, 3, 3, INSTR[5])
    tw = E.micro_width("SI BENCH") + 4
    cv.rect(x + 36, top + 4, tw, 6, "#e6e2d0"); micro_text(cv, "SI BENCH", x + 38, top + 5, "#262830")
    return {"screen": screen, "vna": vscreen, "led": (x + w - 5, top - 23)}


def scope_cart(cv, x, base, w=36, seed=0):
    """A rolling scope cart against the wall: two steel shelves on posts and casters, a scope on
    top (lit trace), a probe pouch and a board on the lower shelf, a coil of probe cable over the
    handle. Returns the screen rect."""
    top = base - 34
    for px_ in (x + 1, x + w - 3):
        cv.rect(px_, top - 6, 2, base - top + 2, OUT); cv.vline(px_, top - 6, base - top, INSTR[5])
    cv.rect(x - 2, top - 8, w + 4, 2, INSTR[5]); cv.hline(x - 2, top - 8, w + 4, INSTR[6])     # handle
    for sy in (top, base - 10):
        cv.rect(x, sy, w, 3, OUT); cv.rect(x + 1, sy, w - 2, 2, INSTR[4]); cv.hline(x + 1, sy, w - 2, INSTR[6])
    for cx in (x + 2, x + w - 4):
        cv.rect(cx - 1, base - 4, 4, 4, OUT); cv.rect(cx, base - 3, 2, 2, INSTR[3])
    screen, ins = scope_body(cv, x + 2, top - 22, w - 4, 22)
    pcb(cv, x + 4, base - 17, 16, 7, seed=seed + 1, chips=1)
    cv.rect(x + 22, base - 18, 10, 8, OUT); cv.rect(x + 23, base - 17, 8, 6, "#3a2a22"); cv.hline(x + 23, base - 17, 8, "#5a4232")
    coil(cv, x - 1, top - 2, 5, CABLE["probe"][0], CABLE["probe"][1], 3)
    cable(cv, ins[0], (x + 6, base - 17), 4, "probe")
    cv.rect(x, base, w, 1, C(SHADOW, 0.5))
    return screen


def slot_colonnade(cv, x, y, w, h, pitch=40, open_w=26, depth=4, seed=0, pts=()):
    """Turn a long window band already painted at (x, y, w, h) into a row of tall openings set
    deep in board-formed concrete: the piers between them are cast over the band, each opening
    keeps its view with a lit left reveal and sill, a dark head and right reveal. Returns the
    points of pts that are still visible."""
    glass = cv.a[y:y + h, x:x + w].copy()
    board_concrete(cv, x - 3, y - 3, w + 6, h + 7, seed=seed, base=5, lift=None, ties=None, stains=0.4, foot=0)
    keep = []
    d = depth
    for ox in range(x + (pitch - open_w) // 2, x + w - open_w + 1, pitch):
        gx0, gx1, gy0, gy1 = ox + d, ox + open_w - d, y + d, y + h - d
        cv.a[gy0:gy1, gx0:gx1] = glass[gy0 - y:gy1 - y, gx0 - x:gx1 - x]
        cv.rect(ox, y, open_w, d, CONC[1])                                                  # head
        cv.poly([(ox, y), (gx0, gy0), (gx0, gy1), (ox, y + h)], CONC[6])                     # left reveal, lit
        cv.vline(ox, y, h, CONC[7])
        cv.poly([(ox + open_w - 1, y), (gx1 - 1, gy0), (gx1 - 1, gy1), (ox + open_w - 1, y + h)], CONC[2])
        cv.rect(ox, gy1, open_w, d, CONC[5]); cv.hline(ox, gy1, open_w, CONC[7])           # sill
        cv.hline(ox - 1, y + h, open_w + 2, CONC[8]); cv.hline(ox - 1, y + h + 1, open_w + 2, C(SHADOW, 0.4))
        cv.rect(gx0, gy0, gx1 - gx0, 1, STEEL[0]); cv.rect(gx0, gy0, 1, gy1 - gy0, STEEL[0])
        for sx in (ox + 2, ox + open_w - 5):                                                 # run-off under the sill
            cv.rect(sx, y + h + 2, 2, 3 + (sx * 7 + seed) % 7, C(CONC[3], 0.6))
        keep += [p for p in pts if gx0 + 1 <= p[0] < gx1 - 1 and gy0 + 1 <= p[1] < gy1]
    return keep


def foam_panel(cv, x, y, w, h, seed=0, tile=16):
    """A wedge-foam acoustic panel set into the concrete: a steel angle frame, the reveal's
    shadow on its top and left, the foam tiles inside."""
    E.acoustic_foam(cv, x + 2, y + 2, w - 4, h - 4, seed=seed, tile=tile, trim=10 ** 6)
    cv.rect(x, y, w, 2, STEEL[2]); cv.rect(x, y + h - 2, w, 2, STEEL[4]); cv.hline(x, y + h - 1, w, STEEL[6])
    cv.rect(x, y, 2, h, STEEL[3]); cv.rect(x + w - 2, y, 2, h, STEEL[2])
    cv.rect(x + 2, y + 2, w - 4, 2, C(SHADOW, 0.45)); cv.rect(x + 2, y + 2, 2, h - 4, C(SHADOW, 0.3))
    for bx in (x + 4, x + w - 6):
        for by in (y + 4, y + h - 6):
            cv.rect(bx, by, 2, 2, STEEL[5])


def reframe(cv, x, y, w, h, mapping):
    """Recolour exact pixels inside a rect (e.g. a lib piece's walnut frame to steel)."""
    sub = cv.a[y:y + h, x:x + w]
    for src, dst in mapping.items():
        s = np.array(C(src)[:3], np.float32)
        m = (np.abs(sub[..., :3] - s).sum(-1) < 1e-3) & (sub[..., 3] > 0)
        sub[m, :3] = np.array(C(dst)[:3], np.float32)


def beam_cans(cv, xs, y):
    """Can downlights fixed to the underside of the concrete edge beam; returns lamp points."""
    pts = []
    for xx in xs:
        cv.rect(xx - 4, y, 9, 3, OUT); cv.rect(xx - 3, y, 7, 2, STEEL[4]); cv.hline(xx - 3, y, 7, STEEL[6])
        cv.rect(xx - 2, y + 2, 5, 1, WARM[3]); cv.px(xx, y + 2, WARM[4])
        pts.append((xx, y + 2))
    return pts
