"""Old Main's shared look, for the four Old Main rooms (O01 courtyard, O02 notice hall, O03 empty
office, O04 cabinet room) and their battle backdrops.

Old Main (1876) is CU's first building: red brick in running bond, rough sandstone plinth and
light sandstone trim (sills, string courses, keystones, quoins), segmental-arched windows below and
round-arched windows above, a bracketed cornice, a fish-scale slate roof with iron cresting, two
gabled end pavilions and the square bell tower over the front door.
Inside: Victorian offices after hours - oak wainscot under deep-coloured plaster, tall sash windows
with the campus night outside, cast-iron radiators, schoolhouse globe lamps, transom doors with
gilt lettering, encaustic tile, worn oak boards, filing cabinets and rubber stamps.

Everything paints at 1:1 game pixels against a 52px character. Prop painters return
(Canvas, anchor_x, anchor_y) like props.py: the anchor is the placement's floor point.
Sections: palettes / brick and trim / windows and doors / the facade (old_main) / courtyard
pieces / interior walls / interior props / perspective textures for the battles.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, LEAF, MUM, ground_shadow, shrub, grass_tuft
from facade import TRIM, GLOW, DARKGLASS, FRAME
from surfaces import light_pool, LEAVES

# --- palettes ---------------------------------------------------------------------------------
BRICK_OM = ["#241214", "#3e1e1e", "#5e2a26", "#72322b", "#843a2f", "#964634", "#a8553d", "#bc6a4c"]
MORTAR = "#3a2526"
TRIM_OM = ["#4e4140", "#7a685e", "#9c8672", "#b8a084", "#ccb698", "#e2d0ae"]   # light sandstone trim
ROUGH = ["#2e2426", "#463838", "#5a4844", "#6c5850", "#7e6a5e", "#927a6a"]     # rough-faced plinth stone
SLATE = ["#121019", "#1b1824", "#24202f", "#2e293b", "#3a3448", "#4a4258", "#5e5670"]
NIGHT_SKY = ["#121230", "#17173a", "#1d1c44", "#25234e", "#2f2a58", "#3c3262", "#4c3a68"]
NIGHT_CLOUD = ["#2c2648", "#3a3058", "#463864", "#52406c", "#6a4c76", "#8e5e80", "#b47486"]
MOON = "#efe2b8"
BELL = ["#3a2a14", "#5e4420", "#8a6630", "#b48a44", "#d8b260", "#f2d690"]
HERRING = ["#2e1a1a", "#4a2a26", "#5c322c", "#683a30", "#744236", "#80493a", "#8c5444"]  # courtyard brick
GRASS_OM = ["#18221a", "#1e2b1f", "#263524", "#2e3f2a", "#384b30", "#445a38", "#536a40"]
# interiors
OAK_OM = ["#1e1210", "#2e1c16", "#45291e", "#5c3826", "#744830", "#8c5a3a", "#a87048"]
HALL_GREEN = ["#1e2a25", "#28372f", "#324438", "#3c5143", "#46604f", "#4f6a57", "#5a7762", "#6a8670"]   # notice hall plaster
OFFICE_OCHRE = ["#2c241e", "#3e3226", "#52422e", "#625036", "#705c3e", "#7c6646", "#846c4b", "#9c825c"]  # empty office plaster
OXBLOOD = ["#220e12", "#341418", "#481a20", "#5a2026", "#6a282c", "#7a3234", "#8c3e3c", "#a04e48"]  # cabinet room damask
TILE_TERRA = ["#3a1e1a", "#5a2c24", "#74382c", "#8a4634"]
TILE_CREAM = ["#6e6252", "#8a7c66", "#a29278", "#b8a688"]
TILE_INK = ["#141218", "#1e1a22", "#2a242c"]
PAPER = ["#8a7e6a", "#b2a688", "#d4c8a6", "#ece2c6", "#faf2dc"]
PAPER_TINTS = ["#ece2c6", "#e8d89a", "#d8e4c8", "#e8c8c0", "#c8d4e4", "#f2e6b8"]
INKS = ["#2a2a3a", "#3a3a5a", "#7a2a26", "#2a3a5a"]
RED_STAMP = ["#5a1414", "#8a1e1e", "#b82a26", "#e04a3a", "#ff8a6a"]
GREEN_STAMP = ["#143a24", "#1e5a34", "#2a7a46", "#4aa868", "#8ad8a0"]
CAST_IRON = ["#121218", "#1c1c24", "#282832", "#363642", "#4a4a58", "#62627a"]
GLOBE = ["#a89a7c", "#d8caa4", "#f2e6c4", "#fff8e2"]
BLUE_NIGHT = ["#0c1022", "#141a34", "#1e2648", "#2a3462", "#3c4a80", "#5a6aa0"]
INK = "#171a2b"


def _rng(seed):
    return np.random.default_rng(seed)


def hashn(a, b, seed=0):
    """Deterministic integer-cell noise in 0..1 (same recipe as persp.hash2)."""
    h = (np.asarray(a).astype(np.int64) * 73856093) ^ (np.asarray(b).astype(np.int64) * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFF).astype(np.float32) / 65535.0


def P(hexes):
    return np.array([C(h)[:3] for h in hexes], np.float32)


# =============================================================================================
# brick and trim
# =============================================================================================
def brick_om(cv, x, y, w, h, pal=BRICK_OM, mortar=MORTAR, seed=0, dim=0.0, course=4, length=8, header_rate=0.0):
    """Running-bond red brick: 7x3 bricks with 1px mortar, each brick its own tone (mostly the
    middle reds, a few burnt dark headers and a few sun-faded ones), a lit top-left pixel on some."""
    x0, y0, x1, y1 = max(0, x), max(0, y), min(cv.w, x + w), min(cv.h, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    ys, xs = np.mgrid[y0:y1, x0:x1]
    row = (ys - y) // course
    off = np.where(row % 2 == 0, 0, length // 2)
    col = (xs - x + off) // length
    fx = (xs - x + off) % length
    fy = (ys - y) % course
    t = hashn(col, row, seed)
    pal_a = P(pal)
    idx = np.select([t < 0.06, t < 0.16, t < 0.42, t < 0.72, t < 0.93], [1, 2, 3, 4, 5], 6)
    rgb = pal_a[idx]
    lit = (fx == 0) & (fy == 0) & (hashn(col, row, seed + 3) < 0.45)
    rgb[lit] = rgb[lit] * 0.8 + pal_a[min(7, len(pal) - 1)] * 0.2
    dark = (fx == length - 2) & (fy == course - 2)
    rgb[dark] *= 0.86
    mort = (fx == length - 1) | (fy == course - 1)
    rgb[mort] = np.array(C(mortar)[:3])
    if dim:
        rgb *= (1 - dim)
    cv.a[y0:y1, x0:x1, :3] = rgb
    cv.a[y0:y1, x0:x1, 3] = 1


def stone_band(cv, x, y, w, h=4, pal=TRIM_OM, drip=True):
    """A sandstone string course: lit top, body, shadowed underside and a soft drip shadow."""
    cv.rect(x, y, w, h, pal[3]); cv.hline(x, y, w, pal[5]); cv.hline(x, y + 1, w, pal[4])
    cv.hline(x, y + h - 1, w, pal[1])
    rng = _rng(x * 7 + y)
    for jx in range(x + int(rng.integers(6, 20)), x + w - 2, int(rng.integers(22, 34))):
        cv.vline(jx, y + 1, h - 2, pal[2])
    if drip:
        cv.hline(x, y + h, w, C("#0d0b16", 0.45)); cv.hline(x, y + h + 1, w, C("#0d0b16", 0.18))


def rough_plinth(cv, x, y, w, h, pal=ROUGH, seed=0):
    """Rock-faced sandstone base course: big blocks with bulging lit tops and dark joints."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[1])
    yy = y
    row = 0
    while yy < y + h:
        ch = min(h - (yy - y), 6 if row % 2 == 0 else 5)
        xx = x - int(rng.integers(0, 12))
        while xx < x + w:
            bw = int(rng.integers(12, 22))
            a, b = max(x, xx + 1), min(x + w, xx + bw)
            if b > a and ch > 1:
                tone = pal[int(rng.choice([2, 3, 3, 4]))]
                cv.rect(a, yy + 1, b - a, ch - 1, tone)
                cv.hline(a + 1, yy + 1, b - a - 2, shade(tone, 0.12))
                cv.hline(a, yy + ch - 1, b - a, shade(tone, -0.18))
                for _ in range((b - a) * ch // 7):
                    cv.px(a + int(rng.integers(0, b - a)), yy + 1 + int(rng.integers(0, ch - 1)), shade(tone, float(rng.choice([-0.1, 0.07]))))
            xx += bw
        yy += ch
        row += 1
    cv.hline(x, y, w, pal[5])


def quoins_om(cv, x, y0, y1, side="left", pal=TRIM_OM):
    """Alternating long/short sandstone quoin blocks on a corner (x is the corner edge)."""
    k = 0
    for qy in range(y0, y1 - 3, 6):
        qw = 9 if k % 2 == 0 else 6
        qx = x if side == "left" else x - qw
        cv.rect(qx, qy, qw, 5, pal[3]); cv.hline(qx, qy, qw, pal[5]); cv.hline(qx, qy + 4, qw, pal[1])
        cv.vline(qx if side == "left" else qx + qw - 1, qy, 5, pal[4] if side == "left" else pal[2])
        k += 1


def arch_ring(cv, cx, cy, r_in, r_out, a0=np.pi, a1=2 * np.pi, pal=BRICK_OM, voussoirs=11, key=TRIM_OM, ry=None):
    """Radial brick voussoirs around an arch (segment or semicircle), with a stone keystone."""
    ry = ry or 1.0
    n = voussoirs
    for r in range(r_in, r_out + 1):
        steps = max(12, int(r * (a1 - a0) * 1.6))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            k = int((a - a0) / (a1 - a0) * n)
            tone = pal[5] if k % 2 == 0 else pal[3]
            if r == r_out:
                tone = shade(tone, 0.08)
            if r == r_in:
                tone = shade(tone, -0.15)
            cv.px(int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r * ry)), tone)
    if key:
        am = (a0 + a1) / 2
        kx, ky = int(round(cx + np.cos(am) * (r_in + r_out) / 2)), int(round(cy + np.sin(am) * (r_in + r_out) / 2 * ry))
        kw = 5
        kh = r_out - r_in + 4
        cv.rect(kx - kw // 2, ky - kh // 2 - 1, kw, kh, key[3]); cv.hline(kx - kw // 2, ky - kh // 2 - 1, kw, key[5])
        cv.vline(kx - kw // 2, ky - kh // 2 - 1, kh, key[4]); cv.vline(kx + kw // 2, ky - kh // 2 - 1, kh, key[1])


# =============================================================================================
# windows and doors (exterior)
# =============================================================================================
def _glass_rows(cv, mask, top, bottom, state, rng):
    """Fill a window's glass mask: night reflection when dark, lamplight when lit."""
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return
    for yy in range(top, bottom):
        row = mask[yy]
        if not row.any():
            continue
        t = (yy - top) / max(1, bottom - top)
        if state in ("lit", "office"):
            c = GLOW[3] if t < 0.25 else GLOW[2] if t < 0.7 else GLOW[1]
        elif state == "dim":
            c = "#b07a42" if t < 0.3 else "#8a5a34" if t < 0.75 else "#6a4028"
        else:
            c = DARKGLASS[2] if t < 0.2 else DARKGLASS[1] if t < 0.65 else DARKGLASS[0]
        cv.a[yy, row] = C(c)


def om_window(cv, x, y, w, h, state="dark", arch="segment", seed=0, sill=True, blind=None, pal=BRICK_OM):
    """A tall sash window in the brick wall. (x, y) is the top-left of the rectangular glass; the
    head rises above y (segmental: a shallow arch with brick voussoirs and keystone; round: a
    semicircle). state: dark (night glass, moon glint), dim, lit, office (lamp-lit with a desk
    lamp and chair seen inside). blind: fraction of the window covered by a drawn blind."""
    rng = _rng(seed)
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    rect = (xs >= x) & (xs < x + w) & (ys >= y) & (ys < y + h)
    if arch == "round":
        r = w / 2
        head = ((xs - (x + r - 0.5)) ** 2 + (ys - y + 0.5) ** 2 <= r * r) & (ys < y)
        top = y - int(r)
        # brick ring around the round head
        arch_ring(cv, x + w / 2 - 0.5, y, int(r) + 1, int(r) + 4, pal=pal, voussoirs=9)
    else:
        rise = max(2, w // 6)
        R = (w * w / 4 + rise * rise) / (2 * rise)
        ccy = y + R - rise
        head = ((xs - (x + w / 2 - 0.5)) ** 2 + (ys - ccy) ** 2 <= R * R) & (ys < y) & (xs >= x) & (xs < x + w)
        top = y - rise
        a_half = np.arcsin(min(1.0, (w / 2 + 1) / R))
        arch_ring(cv, x + w / 2 - 0.5, ccy, int(R) + 1, int(R) + 4, a0=1.5 * np.pi - a_half - 0.08, a1=1.5 * np.pi + a_half + 0.08,
                  pal=pal, voussoirs=7)
    glass = rect | head
    from scipy import ndimage
    frame = ndimage.binary_dilation(glass, iterations=1) & ~glass
    cv.a[frame] = C("#1c1416")
    # reveal: one px of lit jamb on the left inside the frame ring
    _glass_rows(cv, glass, top, y + h, state, rng)
    if state == "dark":
        # moon glint and a faint reflection of the courtyard trees
        cv.line(x + 1, y + h - 4, x + w // 2, y + 3, C(DARKGLASS[3], 0.7))
        cv.px(x + w - 3, top + 2, "#8a96c8")
    if state == "office":
        # a desk lamp's pool, a chair back and a shelf seen inside
        cv.rect(x, y + h - 9, w, 9, GLOW[1])
        cv.rect(x + 2, y + h - 10, w - 4, 2, "#4a2b24")
        cv.poly([(x + w - 7, y + h - 16), (x + w - 2, y + h - 16), (x + w - 3, y + h - 12), (x + w - 6, y + h - 12)], "#3a5a3a")
        cv.rect(x + w - 5, y + h - 12, 1, 2, "#2a1c18")
        cv.rect(x + w - 8, y + h - 12, 8, 2, GLOW[4])
        cv.rect(x + 2, y + h - 18, 5, 8, "#3a2420"); cv.rect(x + 3, y + h - 21, 3, 3, "#3a2420")
        cv.rect(x + 1, top + 3, w - 2, 1, "#a8723a")
        for bx in range(x + 1, x + w - 1, 2):
            cv.vline(bx, top + 4, 3, ["#7e3a30", "#425da6", "#c47a2c", "#5c897c"][int(rng.integers(4))])
    if blind:
        bh = int(h * blind)
        bc = "#c8b48a" if state in ("lit", "office", "dim") else "#5a5466"
        for yy in range(top, y + bh):
            row = glass[yy]
            cv.a[yy, row] = C(bc if (yy - top) % 3 else shade(bc, -0.2))
        cv.hline(x, y + bh, w, shade(bc, -0.35))
    # glazing: two-over-two sash: centre mullion, meeting rail, the upper sash's horns
    cv.a[glass & (xs == x + w // 2)] = C("#1c1416")
    mr = y + h // 2
    cv.hline(x, mr, w, "#2a1e1e"); cv.hline(x, mr + 1, w, "#4a3430" if state == "dark" else "#7a4a2a")
    if state in ("lit", "office"):
        cv.rect(x + 1, top + 1 + (2 if arch == "round" else 0), max(1, w // 4), max(2, h // 5), GLOW[4])
    # sill
    if sill:
        cv.rect(x - 3, y + h + 1, w + 6, 3, TRIM_OM[3]); cv.hline(x - 3, y + h + 1, w + 6, TRIM_OM[5])
        cv.hline(x - 3, y + h + 3, w + 6, TRIM_OM[1]); cv.hline(x - 3, y + h + 4, w + 6, C("#0d0b16", 0.45))
    return glass


def entrance_arch(cv, cx, bottom, w=40, h=72, open_=True, seed=0):
    """Old Main's front door: a round-headed sandstone arch on short columns, a glazed fanlight,
    the oak double doors folded back and warm hall light inside (a runner, a newel post, notices)."""
    x, top = cx - w // 2, bottom - h
    r = w // 2
    spring = top + r
    # sandstone surround with rock-faced voussoirs
    for rr in range(r + 1, r + 9):
        for a in np.linspace(np.pi, 2 * np.pi, int(rr * 4)):
            k = int((a - np.pi) / np.pi * 13)
            tone = TRIM_OM[3] if k % 2 else TRIM_OM[2]
            if rr == r + 8:
                tone = TRIM_OM[5]
            cv.px(int(round(cx - 0.5 + np.cos(a) * rr)), int(round(spring + np.sin(a) * rr)), tone)
    cv.rect(cx - 4, top - 9, 8, 9, TRIM_OM[4]); cv.hline(cx - 4, top - 9, 8, TRIM_OM[5]); cv.vline(cx + 3, top - 9, 9, TRIM_OM[1])
    for side in (x - 8, x + w):
        cv.rect(side, spring, 8, bottom - spring, TRIM_OM[2])
        cv.vline(side, spring, bottom - spring, TRIM_OM[4]); cv.vline(side + 7, spring, bottom - spring, TRIM_OM[0])
        # engaged column with a little capital
        cv.rect(side + 2, spring + 2, 4, bottom - spring - 6, TRIM_OM[4]); cv.vline(side + 2, spring + 2, bottom - spring - 6, TRIM_OM[5])
        cv.vline(side + 5, spring + 2, bottom - spring - 6, TRIM_OM[1])
        cv.rect(side + 1, spring, 6, 3, TRIM_OM[5]); cv.rect(side + 1, bottom - 5, 6, 4, TRIM_OM[3])
    # opening
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    hole = ((((xs - (cx - 0.5)) ** 2 + (ys - spring) ** 2) <= r * r) & (ys < spring)) | ((xs >= x) & (xs < x + w) & (ys >= spring) & (ys < bottom))
    from scipy import ndimage
    ring = ndimage.binary_dilation(hole) & ~hole
    cv.a[ring] = C("#1a1210")
    for yy in range(top, bottom):
        row = hole[yy]
        if not row.any():
            continue
        t = (yy - top) / h
        cv.a[yy, row] = C(mix(GLOW[3], GLOW[1], min(1.0, t * 1.1)))
    if open_:
        # hall seen through the door: far wall with a notice board, a runner up the middle
        cv.rect(x + 6, spring + 6, w - 12, 24, "#9a6a3a"); cv.hline(x + 6, spring + 6, w - 12, "#b8844a")
        cv.rect(cx - 9, spring + 9, 18, 12, "#6e4a2a")
        for i, c in enumerate(["#ece2c6", "#e8d89a", "#e8c8c0", "#d8e4c8"]):
            cv.rect(cx - 7 + i * 4, spring + 10 + (i % 2), 3, 4, c)
        cv.rect(x + 3, bottom - 14, w - 6, 14, GLOW[1])
        cv.poly([(cx - 5, spring + 30), (cx + 5, spring + 30), (cx + 10, bottom), (cx - 10, bottom)], "#7a2a26")
        cv.poly([(cx - 3, spring + 30), (cx + 3, spring + 30), (cx + 6, bottom), (cx - 6, bottom)], "#963a30")
        cv.hline(x + 3, bottom - 14, w - 6, GLOW[2])
        # fanlight bars
        for a in np.linspace(np.pi, 2 * np.pi, 7)[1:-1]:
            cv.line(int(cx), spring, int(round(cx + np.cos(a) * (r - 1))), int(round(spring + np.sin(a) * (r - 1))), "#5a3a24")
        cv.hline(x, spring, w, "#3a2418"); cv.hline(x, spring + 1, w, "#7a5a30")
        cv.rect(cx - 2, spring - 4, 4, 4, GLOW[4])
        # doors folded back against the jambs
        for (dx, d) in ((x, 1), (x + w - 9, -1)):
            cv.rect(dx, spring + 2, 9, bottom - spring - 2, OAK_OM[3])
            cv.vline(dx if d > 0 else dx + 8, spring + 2, bottom - spring - 2, OAK_OM[5])
            cv.vline(dx + 8 if d > 0 else dx, spring + 2, bottom - spring - 2, OAK_OM[1])
            cv.rect(dx + 2, spring + 5, 5, 14, OAK_OM[2]); cv.rect(dx + 3, spring + 6, 3, 12, GLOW[2])
            cv.rect(dx + 2, spring + 23, 5, bottom - spring - 28, OAK_OM[2]); cv.hline(dx + 2, spring + 23, 5, OAK_OM[4])
            cv.px(dx + (7 if d > 0 else 1), spring + 21, "#e8b45c")
    cv.rect(x - 2, bottom - 2, w + 4, 2, TRIM_OM[4])


def wall_lantern_om(cv, x, y):
    """Iron carriage lantern on a scrolled bracket (x is the bracket end, y the lamp top)."""
    cv.line(x - 6, y + 12, x, y + 12, FRAME); cv.line(x - 6, y + 12, x - 6, y + 7, FRAME)
    cv.px(x - 5, y + 6, FRAME)
    cv.rect(x - 3, y + 1, 7, 11, FRAME)
    cv.rect(x - 2, y + 3, 5, 7, GLOW[3]); cv.rect(x - 1, y + 4, 3, 4, GLOW[4])
    cv.poly([(x - 4, y + 2), (x, y - 3), (x + 4, y + 2)], FRAME); cv.px(x, y - 4, IRON[3])
    cv.rect(x - 2, y + 12, 5, 2, FRAME)


def slate_roof(cv, mask, seed=0, pal=SLATE, row=3, scale_w=4, dim=0.0):
    """Fish-scale slate over a mask: alternating rows of rounded scales, a lit lower lip on each,
    the odd darker or paler slate. Rows are counted from the bottom of the mask (the eaves)."""
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return
    yb = ys.max()
    r = (yb - ys) // row
    fy = (yb - ys) % row
    off = np.where(r % 2 == 0, 0, scale_w // 2)
    col = (xs + off) // scale_w
    fx = (xs + off) % scale_w
    t = hashn(col, r, seed)
    p = P(pal)
    base = np.where(t[:, None] < 0.12, p[2], np.where(t[:, None] < 0.85, p[3], p[4]))
    rgb = base.copy()
    lip = (fy == 0) & (fx > 0) & (fx < scale_w - 1)
    rgb[lip] = p[5] * 0.6 + base[lip] * 0.4
    edge = (fx == 0) | ((fy == row - 1) & ((fx == 0) | (fx == scale_w - 1)))
    rgb[edge] = p[1]
    # the round bottom corners of each scale show the row below
    corner = (fy == 0) & ((fx == 0) | (fx == scale_w - 1))
    rgb[corner] = p[1]
    if dim:
        rgb *= (1 - dim)
    cv.a[ys, xs, :3] = rgb
    cv.a[ys, xs, 3] = 1


def cresting(cv, x0, x1, y, every=4):
    """Iron cresting along a ridge: a rail with little fleur spikes."""
    cv.hline(x0, y, x1 - x0, IRON[1])
    for x in range(x0 + 1, x1 - 1, every):
        cv.vline(x, y - 3, 3, IRON[2]); cv.px(x, y - 4, IRON[3])
        cv.px(x - 1, y - 2, IRON[1]); cv.px(x + 1, y - 2, IRON[1])


def bracket_cornice(cv, x, y, w, pal=TRIM_OM, wood=OAK_OM, depth=6):
    """A Victorian bracketed cornice: overhanging eave board, paired scroll brackets, a frieze."""
    cv.rect(x - 4, y, w + 8, 3, pal[3]); cv.hline(x - 4, y, w + 8, pal[5]); cv.hline(x - 4, y + 2, w + 8, pal[1])
    cv.rect(x, y + 3, w, depth, "#3a2422")
    for bx in range(x + 3, x + w - 3, 12):
        for dx in (0, 3):
            cv.rect(bx + dx, y + 3, 2, depth - 1, pal[2]); cv.px(bx + dx, y + 3, pal[4]); cv.px(bx + dx + 1, y + depth + 1, pal[1])
    cv.hline(x, y + 3 + depth, w, pal[2])
    cv.hline(x, y + 4 + depth, w, C("#0d0b16", 0.5)); cv.hline(x, y + 5 + depth, w, C("#0d0b16", 0.22))


def chimney(cv, cx, top, bottom, w=12):
    brick_om(cv, cx - w // 2, top + 4, w, bottom - top - 4, seed=cx)
    cv.rect(cx - w // 2 - 2, top, w + 4, 4, TRIM_OM[3]); cv.hline(cx - w // 2 - 2, top, w + 4, TRIM_OM[5]); cv.hline(cx - w // 2 - 2, top + 3, w + 4, TRIM_OM[1])
    cv.rect(cx - 3, top - 4, 3, 4, "#4a2a26"); cv.rect(cx + 1, top - 3, 3, 3, "#4a2a26")
    cv.vline(cx + w // 2 - 1, top + 4, bottom - top - 4, C("#0d0b16", 0.35))


def dormer(cv, cx, bottom, w=16, h=18, state="dark"):
    """A small gabled dormer with a round-headed window, sitting on the roof slope."""
    x = cx - w // 2
    cv.poly([(x - 2, bottom - h + 6), (cx, bottom - h - 2), (x + w + 1, bottom - h + 6)], SLATE[1])
    cv.poly([(x, bottom - h + 6), (cx, bottom - h), (x + w - 1, bottom - h + 6)], TRIM_OM[2])
    cv.line(x - 2, bottom - h + 6, cx, bottom - h - 2, TRIM_OM[4]); cv.line(cx, bottom - h - 2, x + w + 1, bottom - h + 6, TRIM_OM[1])
    cv.rect(x, bottom - h + 6, w, h - 6, TRIM_OM[2]); cv.vline(x, bottom - h + 6, h - 6, TRIM_OM[4]); cv.vline(x + w - 1, bottom - h + 6, h - 6, TRIM_OM[0])
    gw = w - 8
    gx = cx - gw // 2
    cv.rect(gx - 1, bottom - h + 7, gw + 2, h - 9, "#1c1416")
    pal = GLOW if state == "lit" else DARKGLASS
    cv.rect(gx, bottom - h + 9, gw, h - 12, pal[1]); cv.rect(gx, bottom - h + 9, gw, 3, pal[2])
    cv.ellipse(gx, bottom - h + 6, gw, gw, pal[2])
    cv.vline(cx, bottom - h + 7, h - 10, "#1c1416")
    cv.hline(x - 1, bottom - 1, w + 2, C("#0d0b16", 0.5))


def oculus(cv, cx, cy, r, state="dim"):
    """A round window with radial glazing bars in a sandstone ring."""
    cv.ellipse(cx - r - 3, cy - r - 3, 2 * r + 7, 2 * r + 7, TRIM_OM[2])
    cv.ellipse(cx - r - 2, cy - r - 3, 2 * r + 5, 2 * r + 5, TRIM_OM[4])
    cv.ellipse(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, "#1c1416")
    pal = {"lit": GLOW, "dim": ["#3a2420", "#6e4430", "#8a5a3a", "#a8703f", "#c8904a"], "dark": DARKGLASS}[state]
    cv.ellipse(cx - r, cy - r, 2 * r + 1, 2 * r + 1, pal[1])
    cv.ellipse(cx - r + 1, cy - r + 1, 2 * r - 2, 2 * r - 2, pal[2])
    cv.ellipse(cx - r // 2, cy - r // 2 - 1, r, r, pal[3])
    for a in np.linspace(0, np.pi, 4, endpoint=False):
        cv.line(int(round(cx - np.cos(a) * r)), int(round(cy - np.sin(a) * r)), int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r)), "#1c1416")
    cv.ellipse(cx - 2, cy - 2, 5, 5, "#1c1416"); cv.px(cx, cy, pal[3])
    for k in range(-1, 2):
        cv.rect(cx + k * 0 - 2, cy - r - 6, 5, 4, TRIM_OM[4])
    cv.hline(cx - 2, cy - r - 6, 5, TRIM_OM[5])


def bell(cv, cx, top, size=12, angle=0.0, pal=BELL, yoke=True):
    """The tower bell hanging from its yoke, swung by `angle` (radians): a flared bronze bell,
    lit along its left shoulder, a dark mouth and the clapper showing below."""
    h = size + 3
    pts_l, pts_r = [], []
    ca, sa = np.cos(angle), np.sin(angle)

    def rot(px, py):
        return (cx + px * ca - py * sa, top + px * sa + py * ca)
    for i in range(h + 1):
        t = i / h
        half = size * (0.22 + 0.18 * t + 0.42 * t ** 3)
        pts_l.append(rot(-half, i)); pts_r.append(rot(half, i))
    poly = pts_l + pts_r[::-1]
    cv.poly([(round(p[0]), round(p[1])) for p in poly], pal[2])
    inner_l = [rot(-size * (0.22 + 0.18 * (i / h) + 0.42 * (i / h) ** 3) + 2, i) for i in range(1, h)]
    hi = [rot(-size * (0.22 + 0.18 * (i / h) + 0.42 * (i / h) ** 3) * 0.5, i) for i in range(1, h)]
    cv.poly([(round(p[0]), round(p[1])) for p in inner_l + hi[::-1]], pal[4])
    for p in inner_l[:h // 2]:
        cv.px(int(round(p[0])), int(round(p[1])), pal[5])
    # lip and mouth
    lx0, ly0 = rot(-size * 0.82, h); lx1, ly1 = rot(size * 0.82, h)
    cv.line(int(round(lx0)), int(round(ly0)), int(round(lx1)), int(round(ly1)), pal[1])
    mx, my = rot(0, h + 1)
    cv.ellipse(int(round(mx - size * 0.6)), int(round(my - 1)), int(size * 1.2), 3, pal[0])
    cx2, cy2 = rot(0, h + 3)
    cv.rect(int(round(cx2)) - 1, int(round(cy2)) - 1, 3, 3, pal[1])
    # crown and yoke
    yx, yy = rot(0, -2)
    cv.rect(int(round(yx)) - 2, int(round(yy)) - 2, 5, 3, pal[1])
    if yoke:
        cv.hline(cx - size, top - 4, size * 2 + 1, OAK_OM[2]); cv.hline(cx - size, top - 5, size * 2 + 1, OAK_OM[4])


# =============================================================================================
# the facade
# =============================================================================================
# Horizontal layout relative to the door's centre line (room pixels): end pavilions, the main
# walls and the tower bay.
OM_HALF = 284          # half width of the whole front
PAV_W = 88             # end pavilion width
TOWER_HALF = 38        # tower bay half width
GROUND_WIN = (20, 42)  # ground-floor window w, h (glass)
UPPER_WIN = (16, 24)
EAVES = 100            # height of the main eaves above the floor
TOWER_TOP = 274        # finial tip above the floor


def old_main(cv, cx, base, seed=0, lit=None, office=None, door_open=True, bell_angle=None):
    """Old Main's east front at character scale, centred on the door (cx) with its floor on row
    `base`. Everything above row 0 is simply cut off by the canvas, so the same painter serves the
    room (cropped under the roof) and the battle backdrop (the whole tower).
    lit: dict window-key -> state ("dark", "dim", "lit"); office: the key of the last open office.
    Window keys are ("g" | "u", index from the left). Returns a dict of useful coordinates."""
    lit = lit or {}
    rng = _rng(seed)
    x0, x1 = cx - OM_HALF, cx + OM_HALF
    pl0, pl1 = x0 + PAV_W, x1 - PAV_W              # inner edges of the end pavilions
    t0, t1 = cx - TOWER_HALF, cx + TOWER_HALF
    eave_y = base - EAVES
    info = {"windows": {}, "lanterns": [], "door": None}

    # --- roof behind everything: main hip roof, then the pavilion gables' roofs
    ridge = base - 132
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    main_roof = (ys >= ridge) & (ys < eave_y - 2) & (xs >= pl0 - 10 + (eave_y - ys) * 0) & (xs < pl1 + 10)
    slope = (eave_y - 2 - ys).clip(0)
    main_roof &= (xs >= pl0 - 6 + slope * 0.0) & (xs < pl1 + 6)
    slate_roof(cv, main_roof, seed=seed + 1)
    cresting(cv, pl0, pl1, ridge, every=5)
    for dx in (-118, -62, 62, 118):
        dormer(cv, cx + dx, eave_y - 4, 16, 20, state="lit" if dx == 118 and office else "dark")
    for chx in (pl0 + 16, pl1 - 16):
        chimney(cv, chx, base - 158, ridge + 4, w=12)

    # --- end pavilions with gables
    for (a, b, side) in ((x0, pl0, -1), (pl1, x1, 1)):
        peak = base - 136
        mid = (a + b) // 2
        gable = [(a - 3, eave_y + 1), (mid, peak - 3), (b + 2, eave_y + 1)]
        cv.poly(gable, TRIM_OM[1])
        inner = [(a + 3, eave_y + 2), (mid, peak + 4), (b - 4, eave_y + 2)]
        mask = np.zeros((cv.h, cv.w), bool)
        from PIL import Image, ImageDraw
        im = Image.new("L", (cv.w, cv.h), 0)
        ImageDraw.Draw(im).polygon(inner, fill=255)
        mask = np.array(im) > 0
        tmp = Canvas(cv.w, cv.h)
        brick_om(tmp, a, peak, b - a, eave_y - peak + 2, seed=seed + 7 + side)
        cv.a[mask] = tmp.a[mask]
        # stone coping along both slopes, kneelers at the feet, a finial at the peak
        for k in range(3):
            cv.line(a - 3 + k, eave_y - 1 + k * 0, mid, peak - 3 + k, TRIM_OM[5 - k])
            cv.line(mid, peak - 3 + k, b + 2 - k, eave_y - 1, TRIM_OM[3 - k])
        cv.rect(a - 5, eave_y - 3, 9, 6, TRIM_OM[3]); cv.hline(a - 5, eave_y - 3, 9, TRIM_OM[5])
        cv.rect(b - 4, eave_y - 3, 9, 6, TRIM_OM[3]); cv.hline(b - 4, eave_y - 3, 9, TRIM_OM[5])
        cv.rect(mid - 2, peak - 9, 5, 7, TRIM_OM[4]); cv.px(mid, peak - 11, TRIM_OM[5]); cv.px(mid, peak - 10, TRIM_OM[3])
        # a lunette (half-round attic window) in the gable
        oculus(cv, mid, eave_y - 16, 7, state="dim" if side > 0 else "dark")
        # pavilion walls
        brick_om(cv, a, eave_y, b - a, base - eave_y, seed=seed + 11 + side)
        quoins_om(cv, a, eave_y + 2, base - 10, "left")
        quoins_om(cv, b, eave_y + 2, base - 10, "right")

    # --- main walls between pavilions and tower
    for (a, b) in ((pl0, t0), (t1, pl1)):
        brick_om(cv, a, eave_y, b - a, base - eave_y, seed=seed + 21 + a, dim=0.06)
    # pavilions and tower project: a shadow on the recessed walls beside them
    for (sx, d) in ((pl0, 1), (t1, 1)):
        for k in range(7):
            cv.vline(sx + k, eave_y + 4, base - eave_y - 4, C("#0d0b16", 0.32 * (1 - k / 7)))
    bracket_cornice(cv, x0, eave_y - 4, x1 - x0)

    # --- tower bay: shaft, stages, belfry, cap
    shaft_top = base - 164
    brick_om(cv, t0, shaft_top, t1 - t0, base - shaft_top, seed=seed + 31)
    quoins_om(cv, t0, shaft_top + 2, base - 10, "left")
    quoins_om(cv, t1, shaft_top + 2, base - 10, "right")
    # stone panel over the arch carved OLD MAIN, the date below
    py = base - 98
    cv.rect(cx - 26, py, 52, 12, TRIM_OM[2]); cv.rect(cx - 25, py + 1, 50, 10, TRIM_OM[3])
    cv.hline(cx - 26, py, 52, TRIM_OM[5]); cv.hline(cx - 26, py + 11, 52, TRIM_OM[1])
    text(cv, "OLD MAIN", cx - text_width("OLD MAIN") // 2, py + 2, TRIM_OM[5])
    text(cv, "OLD MAIN", cx - text_width("OLD MAIN") // 2, py + 1, TRIM_OM[0])
    # stage above the roof: the stair hall's triple round-headed window, faintly lit
    stone_band(cv, t0 - 2, eave_y - 4, t1 - t0 + 4, 5)
    for k, dx in enumerate((-17, -5, 7)):
        tall = 0 if k == 1 else 4
        om_window(cv, cx + dx, base - 128 + tall, 10, 20 - tall, state="dim", arch="round", seed=seed + 40 + k, sill=False)
    cv.rect(cx - 21, base - 107, 42, 3, TRIM_OM[3]); cv.hline(cx - 21, base - 107, 42, TRIM_OM[5]); cv.hline(cx - 21, base - 105, 42, TRIM_OM[1])
    stone_band(cv, t0 - 3, shaft_top, t1 - t0 + 6, 6)
    # belfry: narrower, two-light open arch with the bell inside
    b0, b1 = cx - 32, cx + 32
    btop = shaft_top - 42
    brick_om(cv, b0, btop, b1 - b0, shaft_top - btop, seed=seed + 33)
    quoins_om(cv, b0, btop + 2, shaft_top, "left")
    quoins_om(cv, b1, btop + 2, shaft_top, "right")
    ow, oh = 36, 30
    ox, oy = cx - ow // 2, shaft_top - 4 - oh
    hole = ((xs >= ox) & (xs < ox + ow) & (ys >= oy + ow // 2) & (ys < oy + oh)) | \
           (((xs - (cx - 0.5)) ** 2 + (ys - (oy + ow // 2)) ** 2 <= (ow / 2) ** 2) & (ys < oy + ow // 2))
    arch_ring(cv, cx - 0.5, oy + ow // 2, ow // 2 + 1, ow // 2 + 4, pal=BRICK_OM, voussoirs=11)
    cv.a[hole] = C("#0e0c16")
    # the bell chamber's back wall faintly moonlit, the bell frame
    cv.a[hole & (ys > oy + oh - 6)] = C("#16131e")
    cv.hline(ox, oy + oh - 6, ow, OAK_OM[2])
    info["bell"] = (cx, oy + 10)
    if bell_angle is not None:
        bell(cv, cx, oy + 10, size=10, angle=bell_angle)
    cv.vline(ox - 1, oy + ow // 2, oh - ow // 2, TRIM_OM[3])
    cv.rect(ox - 1, oy + oh - 1, ow + 2, 3, TRIM_OM[3]); cv.hline(ox - 1, oy + oh - 1, ow + 2, TRIM_OM[5])
    info["belfry"] = (ox, oy, ow, oh)
    # cornice and pyramidal slate cap with lucarnes, cresting and a weathervane
    bracket_cornice(cv, b0 - 2, btop - 4, b1 - b0 + 4, depth=5)
    cap_base, cap_top = btop - 4, base - TOWER_TOP + 22
    cap = np.zeros((cv.h, cv.w), bool)
    from PIL import Image, ImageDraw
    im = Image.new("L", (cv.w, cv.h), 0)
    ImageDraw.Draw(im).polygon([(b0 - 4, cap_base), (cx - 3, cap_top), (cx + 2, cap_top), (b1 + 3, cap_base)], fill=255)
    cap = np.array(im) > 0
    slate_roof(cv, cap, seed=seed + 5)
    cv.line(b0 - 4, cap_base, cx - 3, cap_top, SLATE[5]); cv.line(cx + 2, cap_top, b1 + 3, cap_base, SLATE[1])
    dormer(cv, cx, cap_base - 6, 14, 18, state="dark")
    cresting(cv, cx - 4, cx + 5, cap_top, every=3)
    cv.vline(cx, cap_top - 22, 22, IRON[2]); cv.vline(cx - 1, cap_top - 18, 14, IRON[1])
    cv.ellipse(cx - 2, cap_top - 12, 5, 5, IRON[3])
    cv.line(cx - 7, cap_top - 20, cx + 6, cap_top - 20, IRON[3])
    cv.poly([(cx + 2, cap_top - 22), (cx + 8, cap_top - 20), (cx + 2, cap_top - 18)], IRON[3])
    cv.px(cx, cap_top - 23, "#e8b45c")
    info["vane"] = (cx, cap_top - 20)

    # --- windows: ground floor (segmental heads) and upper floor (round heads)
    gw, gh = GROUND_WIN
    uw, uh = UPPER_WIN
    centres = []
    for k in range(3):
        centres.append(pl0 + 26 + k * 40)
    for k in range(3):
        centres.append(t1 + 26 + k * 40)
    pav = [x0 + PAV_W // 2, x1 - PAV_W // 2]
    keys = []
    order = [pav[0] - 14, pav[0] + 14] + centres[:3] + centres[3:] + [pav[1] - 14, pav[1] + 14]
    for i, wx in enumerate(order):
        for floor_, (ww, wh, wy, arch) in (("g", (gw, gh, base - 16 - gh, "segment")), ("u", (uw, uh, base - 68 - uh + 2, "round"))):
            key = f"{floor_}{i}"
            state = lit.get(key, "dark")
            if office == key:
                state = "office"
            w_ = ww - (4 if wx in (pav[0] - 14, pav[0] + 14, pav[1] - 14, pav[1] + 14) else 0)
            om_window(cv, wx - w_ // 2, wy, w_, wh, state=state, arch=arch, seed=seed + 50 + i * 2 + (floor_ == "u"),
                      blind=0.35 if state == "dark" and (i * 3 + len(floor_)) % 4 == 0 else None)
            info["windows"][key] = (wx - w_ // 2, wy, w_, wh)
    # string courses and sill course
    stone_band(cv, x0, base - 64, x1 - x0, 4)
    stone_band(cv, x0, base - 14, x1 - x0, 3)
    # rough plinth with basement wells under the ground floor windows
    rough_plinth(cv, x0 - 2, base - 11, x1 - x0 + 4, 11, seed=seed + 61)
    for wx in order:
        cv.rect(wx - 6, base - 9, 12, 7, "#141218"); cv.rect(wx - 5, base - 8, 10, 5, DARKGLASS[1])
        for bx in range(wx - 4, wx + 5, 3):
            cv.vline(bx, base - 8, 5, IRON[2])
        cv.hline(wx - 6, base - 9, 12, ROUGH[5])
    # the entrance and its lanterns
    entrance_arch(cv, cx, base - 1, 40, 72, open_=door_open)
    info["door"] = (cx, base - 1, 72)
    for lx in (cx - 30, cx + 30):
        wall_lantern_om(cv, lx + (4 if lx < cx else -4), base - 62)
        info["lanterns"].append((lx + (4 if lx < cx else -4), base - 55))
    cv.hline(x0 - 2, base, x1 - x0 + 4, C("#0d0b16", 0.6))
    info["x0"], info["x1"] = x0, x1
    info["eave_y"], info["ridge"] = eave_y, ridge
    return info


# =============================================================================================
# courtyard pieces
# =============================================================================================
def herringbone(cv, mask, pal=HERRING, mortar=None, seed=0, a=4, dim=0.0):
    """90-degree herringbone brick paving over a mask: 7x3 and 3x7 bricks in stepped zig-zag
    bands, each brick its own tone, a lit top pixel row on the horizontals, dark mortar joints."""
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return
    cu, cw = xs // a, ys // a
    fx, fy = xs % a, ys % a
    d = cu - cw
    r = d % 4
    b = -(d - r) // 4
    k = np.where(r == 0, cu + 2 * b, np.where(r == 1, cu + 2 * b - 1, cu - 2 + 2 * b))
    horiz = r < 2
    t = hashn(k * 2 + horiz, b, seed)
    p = P(pal)
    idx = np.select([t < 0.08, t < 0.3, t < 0.66, t < 0.9], [2, 3, 4, 5], 6)
    rgb = p[idx]
    # joints: horizontal bricks close on their bottom row and the right end of their 2nd cell;
    # vertical bricks on their right column and the bottom of their lower cell
    joint = np.where(horiz, (fy == a - 1) | ((r == 1) & (fx == a - 1)), (fx == a - 1) | ((r == 2) & (fy == a - 1)))
    lit = np.where(horiz, (fy == 0) & ~joint, (fx == 0) & ~joint & (r == 3))
    rgb[lit] = rgb[lit] * 0.82 + p[6] * 0.18
    rgb[joint] = np.array(C(mortar or pal[1])[:3])
    if dim:
        rgb *= (1 - dim)
    cv.a[ys, xs, :3] = rgb
    cv.a[ys, xs, 3] = 1


def soldier_band(cv, mask, pal=HERRING, seed=0, vertical=False):
    """A border course of bricks on end (3 wide) over a band mask."""
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return
    k = (ys if vertical else xs) // 4
    f = (ys if vertical else xs) % 4
    t = hashn(k, 7, seed)
    p = P(pal)
    rgb = np.where(t[:, None] < 0.5, p[3], p[5])
    rgb[f == 3] = p[1]
    cv.a[ys, xs, :3] = rgb
    cv.a[ys, xs, 3] = 1


def cast_shadow(cv, sprite, fx, fy, ax, ay, lean=0.42, squash=0.24, alpha=0.32, colour="#0b0a16"):
    """A tree's own silhouette laid on the ground (the moon high to the upper left): every opaque
    sprite pixel h px above the floor lands lean*h to the right and squash*h below the foot."""
    a = sprite.a if isinstance(sprite, Canvas) else sprite
    ys, xs = np.where(a[..., 3] > 0.5)
    hgt = ay - ys
    keep = hgt > 2
    sx = np.round(fx + (xs[keep] - ax) + hgt[keep] * lean).astype(int)
    sy = np.round(fy + hgt[keep] * squash).astype(int)
    m = np.zeros((cv.h, cv.w), bool)
    ok = (sx >= 0) & (sx < cv.w) & (sy >= 0) & (sy < cv.h)
    m[sy[ok], sx[ok]] = True
    from scipy import ndimage
    m = ndimage.binary_closing(m, structure=np.ones((2, 3)))
    m = ndimage.binary_opening(m, structure=np.ones((1, 2)))
    cv.fill_mask(m, C(colour, alpha))
    return m


def gas_lamp(height=68):
    """A Victorian courtyard gas lamp: fluted cast-iron post on a stepped base, a ladder bar, a
    four-sided glass lantern glowing amber with a crown and finial. The flame sits ~5px under the top."""
    w = 24
    cv = Canvas(w, height + 6, seed=13)
    cx, base = w // 2, height + 2
    top = base - height
    ground_shadow(cv, cx, base, 10, 2)
    # stepped base
    cv.rect(cx - 6, base - 4, 12, 4, OUT); cv.rect(cx - 5, base - 4, 10, 3, CAST_IRON[2]); cv.hline(cx - 5, base - 4, 10, CAST_IRON[4])
    cv.rect(cx - 4, base - 9, 8, 5, OUT); cv.rect(cx - 3, base - 9, 6, 5, CAST_IRON[3]); cv.vline(cx - 3, base - 9, 5, CAST_IRON[5])
    cv.rect(cx - 3, base - 13, 6, 4, CAST_IRON[2]); cv.hline(cx - 3, base - 13, 6, CAST_IRON[4])
    # fluted post
    cv.rect(cx - 2, top + 20, 4, base - 13 - top - 20, OUT)
    cv.vline(cx - 1, top + 20, base - 13 - top - 20, CAST_IRON[4]); cv.vline(cx, top + 20, base - 13 - top - 20, CAST_IRON[2])
    for ry in (top + 28, top + 44):
        cv.rect(cx - 3, ry, 6, 2, OUT); cv.hline(cx - 2, ry, 4, CAST_IRON[5])
    # ladder bar
    cv.rect(cx - 7, top + 20, 14, 2, OUT); cv.hline(cx - 6, top + 20, 12, CAST_IRON[4])
    cv.px(cx - 7, top + 19, CAST_IRON[4]); cv.px(cx + 6, top + 19, CAST_IRON[4])
    # lantern: tapering glass box
    cv.poly([(cx - 6, top + 6), (cx + 5, top + 6), (cx + 3, top + 18), (cx - 4, top + 18)], OUT)
    cv.poly([(cx - 5, top + 7), (cx + 4, top + 7), (cx + 2, top + 17), (cx - 3, top + 17)], AMBER[2])
    cv.rect(cx - 3, top + 8, 6, 7, AMBER[3]); cv.rect(cx - 1, top + 9, 2, 4, AMBER[4])
    cv.vline(cx, top + 7, 11, C(OUT, 0.6))
    cv.rect(cx - 4, top + 18, 8, 2, OUT)
    # crown and finial
    cv.poly([(cx - 7, top + 7), (cx, top + 1), (cx + 6, top + 7)], OUT)
    cv.poly([(cx - 5, top + 6), (cx, top + 2), (cx + 4, top + 6)], CAST_IRON[3]); cv.hline(cx - 5, top + 6, 10, CAST_IRON[5])
    cv.rect(cx - 1, top - 1, 2, 3, CAST_IRON[4]); cv.px(cx, top - 2, CAST_IRON[5])
    return cv, cx, base


def victorian_bench(width=150, height=32, seed=0):
    """A long oak-slatted bench on scrolled cast-iron ends with a middle support, a small brass
    memorial plate on the back rail."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 3)
    wood = OAK_OM
    # back slats
    for i, yy in enumerate((base - 31, base - 26, base - 21)):
        cv.rect(ox + 4, yy, width - 8, 4, OUT)
        cv.rect(ox + 5, yy + 1, width - 10, 2, wood[5] if i == 0 else wood[4])
        cv.hline(ox + 5, yy + 1, width - 10, wood[6] if i == 0 else wood[5])
        for gx in range(ox + 11, ox + width - 8, 13):
            cv.hline(gx, yy + 2, 4, wood[3])
    cv.rect(ox + width // 2 - 8, base - 26, 16, 4, OUT); cv.rect(ox + width // 2 - 7, base - 25, 14, 2, "#c8a050"); cv.hline(ox + width // 2 - 7, base - 25, 14, "#f0d48a")
    # iron ends: scrolled arm, splayed legs
    for ex, d in ((ox + 1, 1), (ox + width - 7, -1), (ox + width // 2 - 3, 0)):
        cv.rect(ex, base - 32, 6, 32, OUT) if d else cv.rect(ex, base - 18, 6, 18, OUT)
        if d:
            cv.rect(ex + 1, base - 31, 4, 30, CAST_IRON[3]); cv.vline(ex + 1, base - 31, 30, CAST_IRON[5])
            ax = ex - 2 if d > 0 else ex + 2
            cv.rect(ax, base - 19, 10, 3, OUT); cv.hline(ax + 1, base - 18, 8, CAST_IRON[4])
            cv.ellipse(ax - 1 if d > 0 else ax + 6, base - 21, 5, 5, OUT); cv.px(ax + 1 if d > 0 else ax + 8, base - 19, CAST_IRON[5])
            cv.line(ex + 3, base - 8, ex + 3 - 3 * d, base - 1, OUT); cv.line(ex + 3, base - 8, ex + 3 + 3 * d, base - 1, OUT)
        else:
            cv.rect(ex + 1, base - 17, 4, 16, CAST_IRON[2])
    # seat
    cv.rect(ox + 2, base - 15, width - 4, 7, OUT)
    cv.rect(ox + 3, base - 14, width - 6, 2, wood[5]); cv.hline(ox + 3, base - 14, width - 6, wood[6])
    cv.rect(ox + 3, base - 12, width - 6, 2, wood[4])
    cv.hline(ox + 3, base - 10, width - 6, wood[2])
    rng = _rng(seed)
    for _ in range(width // 8):
        cv.hline(ox + 4 + int(rng.integers(0, width - 14)), base - 13 + int(rng.integers(0, 3)), int(rng.integers(2, 5)), wood[3])
    # a few fallen leaves on the seat
    for _ in range(3):
        lx = ox + 10 + int(rng.integers(0, width - 20))
        c = LEAVES[int(rng.integers(len(LEAVES)))]
        cv.px(lx, base - 14, c); cv.px(lx + 1, base - 14, shade(c, -0.2))
    return cv, ox + width // 2, base


def brick_planter(width=170, height=54, seed=0):
    """A raised brick planter with a sandstone coping, banked with autumn mums, ornamental grass
    plumes and a low shrub, a few leaves fallen on the coping."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    face_top = base - 24
    # planting behind the coping
    x = ox + 3
    while x < ox + width - 10:
        kind = rng.random()
        if kind < 0.38:
            w = int(rng.integers(20, 28)); h = int(rng.integers(16, 24))
            cv.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), palette=LEAF), x - 2, face_top - h + 3)
            x += w - 7
        elif kind < 0.78:
            w = int(rng.integers(13, 18)); h = int(rng.integers(10, 14))
            fl = [MUM[int(rng.integers(len(MUM)))]] * 2 + [MUM[3]]
            cv.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=fl, density=1.4), x - 2, face_top - h + 2)
            x += w - 3
        else:
            # ornamental grass with pale plumes
            gx = x + 4
            for i in range(9):
                lean = int(rng.integers(-3, 4))
                hh = int(rng.integers(14, 24))
                cv.line(gx + i // 2, face_top + 1, gx + i // 2 + lean, face_top - hh, ["#5e4a34", "#8a7050", "#6e5a3c"][i % 3])
                if i % 2 == 0:
                    cv.rect(gx + i // 2 + lean - 1, face_top - hh - 3, 2, 4, "#d8c094")
            x += 10
    # brick body
    cv.rect(ox, face_top - 1, width, base - face_top - 1, OUT)
    brick_om(cv, ox + 1, face_top + 3, width - 2, base - face_top - 5, seed=seed + 2)
    cv.rect(ox + 1, base - 5, width - 2, 3, TRIM_OM[2]); cv.hline(ox + 1, base - 5, width - 2, TRIM_OM[4])
    # coping
    cv.rect(ox - 2, face_top - 2, width + 4, 6, OUT)
    cv.rect(ox - 1, face_top - 1, width + 2, 4, TRIM_OM[3]); cv.hline(ox - 1, face_top - 1, width + 2, TRIM_OM[5])
    cv.hline(ox - 1, face_top + 2, width + 2, TRIM_OM[1])
    for jx in range(ox + 20, ox + width - 4, 28):
        cv.vline(jx, face_top, 3, TRIM_OM[2])
    for _ in range(6):
        lx = ox + int(rng.integers(2, width - 4))
        c = LEAVES[int(rng.integers(len(LEAVES)))]
        cv.px(lx, face_top, c); cv.px(lx + 1, face_top, shade(c, -0.2))
    return cv, ox + width // 2, base


def luminaria(cv, x, y, lit=False):
    """A paper lantern bag weighted with sand: 7px tall, a folded rim, a candle glow when lit."""
    paper = ["#8a7c64", "#b8a888", "#d8caa6", "#ece2c6"] if not lit else ["#a8642a", "#e09a44", "#f6cf7a", "#fff0c4"]
    cv.rect(x - 3, y - 7, 7, 7, "#2a2024")
    cv.rect(x - 2, y - 6, 5, 6, paper[1]); cv.vline(x - 2, y - 6, 6, paper[2]); cv.vline(x + 2, y - 6, 6, paper[0])
    cv.hline(x - 3, y - 7, 7, paper[3]); cv.hline(x - 2, y - 5, 5, paper[0])
    if lit:
        cv.rect(x - 1, y - 4, 2, 3, "#fff8e0")
        for r, al in ((7, 0.07), (4, 0.11)):
            cv.ellipse(x - r, y - 2 - r // 2, 2 * r + 1, r + 2, C("#f6cf7a", al))
    else:
        cv.px(x, y - 3, paper[0])
    cv.hline(x - 3, y, 7, C("#0d0b16", 0.45))


def night_sky(cv, w, h, seed=3, stars=150, moon=None, clouds=()):
    """Night over Old Main: stepped indigo bands, stars, a moon with a stepped halo, a few lit clouds."""
    for y in range(h):
        t = y / max(1, h - 1)
        i = min(len(NIGHT_SKY) - 1, int(t ** 0.85 * len(NIGHT_SKY)))
        cv.hline(0, y, w, NIGHT_SKY[i])
    rng = _rng(seed)
    pts = []
    for _ in range(stars):
        sx, sy = int(rng.integers(0, w)), int(rng.integers(0, int(h * 0.8)))
        c = "#c8c0e0" if rng.random() < 0.65 else "#f2d27a"
        cv.px(sx, sy, c)
        pts.append((sx, sy, c))
    if moon:
        mx, my = moon
        for r, a in [(24, 0.05), (17, 0.08), (12, 0.1)]:
            cv.ellipse(mx - r, my - r, r * 2 + 1, r * 2 + 1, C(MOON, a))
        cv.ellipse(mx - 8, my - 8, 17, 17, MOON); cv.ellipse(mx - 6, my - 7, 9, 7, "#fff4d2")
        for (cx, cy) in [(mx - 3, my + 2), (mx + 3, my - 3), (mx + 1, my + 4), (mx + 4, my + 3)]:
            cv.px(cx, cy, "#d8c8a0")
    from clouds import _cloud
    crng = _rng(seed + 1)
    for (cx, cy, length, thick) in clouds:
        cl = _cloud(length, thick, crng, NIGHT_CLOUD)
        cv.paste(cl, cx, cy - cl.shape[0])
    return pts


def macky_far(height=96, dim=0.62):
    """Macky Auditorium from the atlas, small and dimmed for the far distance."""
    from midlib import sprite_from_cell
    spr = sprite_from_cell(4, height=height, colors=28, brightness=dim, saturation=0.75)
    return spr


# =============================================================================================
# interior walls
# =============================================================================================
OAK_IN = ["#24160f", "#3a2418", "#523322", "#68422a", "#7e5234", "#96643e", "#b07c4c"]   # indoor oak (lit)
GILT_OM = ["#4a3418", "#7a5a2a", "#a8823c", "#cfa652", "#ecca78", "#fae6a8"]
CORK = ["#4e3420", "#664428", "#7a5432", "#8c623a", "#9e7246", "#b08454"]
SILVER = ["#22222c", "#383844", "#50505e", "#686876", "#82828e", "#a0a0aa"]           # painted radiators
CREAM_TRIM = ["#3a3430", "#5e5446", "#847660", "#a6967a", "#c2b292", "#dccca8"]       # painted mouldings
HORN = ["#16181e", "#262a30", "#363c42", "#4a5256", "#5e686a", "#7a8484", "#9aa4a0"]  # loudspeaker iron
RUNNER_OM = ["#1a1830", "#28233f", "#342d56", "#403767", "#603f63", "#804f67"]         # indigo-plum runner


def soft_noise(w, h, cell, seed=0):
    """Smooth value noise in 0..1 (bilinear between random lattice points)."""
    rng = _rng(seed)
    gw, gh = w // cell + 2, h // cell + 2
    g = rng.random((gh, gw)).astype(np.float32)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    fx, fy = xs / cell, ys / cell
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx
    b = g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx
    return a * (1 - ty) + b * ty


def plaster_om(cv, x, y, w, h, pal=HALL_GREEN, seed=0, shadow_top=8, body=(4, 5), cracks=4, cell=34):
    """Old painted plaster: two close tones in soft, wall-sized patches (clean clusters, no dither),
    a stepped shadow under the cornice, a few hairline cracks."""
    f = soft_noise(w, h, cell, seed) * 0.8 + soft_noise(w, h, 11, seed + 1) * 0.2
    idx = (f > 0.52).astype(int)
    rgb = P([pal[i] for i in body])[idx]
    region = cv.a[y:y + h, x:x + w]
    region[..., :3] = rgb[:region.shape[0], :region.shape[1]]
    region[..., 3] = 1
    for i in range(shadow_top):
        t = 1 - i / max(1, shadow_top)
        cv.hline(x, y + i, w, C(pal[1], 0.5 * t))
    rng = _rng(seed + 7)
    for _ in range(cracks):
        cx_, cy_ = int(rng.integers(x + 10, x + w - 10)), int(rng.integers(y + shadow_top + 4, y + h - 8))
        for _ in range(int(rng.integers(5, 13))):
            cv.px(cx_, cy_, pal[body[0] - 1])
            cx_ += int(rng.integers(-1, 2)); cy_ += 1


def cornice_om(cv, x, y, w, ceiling=("#1a1620", "#262030", "#322a3a"), trim=CREAM_TRIM):
    """The top of the wall: a strip of dark pressed-tin ceiling, then a stepped crown moulding with
    a dentil course. 13px tall."""
    cv.rect(x, y, w, 5, ceiling[1])
    for xx in range(x, x + w, 6):
        cv.vline(xx, y, 5, ceiling[0])
        cv.px(xx + 3, y + 2, ceiling[2])
    cv.hline(x, y + 4, w, ceiling[0])
    cv.hline(x, y + 5, w, trim[1]); cv.hline(x, y + 6, w, trim[4]); cv.hline(x, y + 7, w, trim[3])
    cv.rect(x, y + 8, w, 2, trim[2])
    for xx in range(x, x + w, 4):
        cv.rect(xx, y + 8, 2, 2, trim[4]); cv.px(xx + 1, y + 9, trim[3])
    cv.hline(x, y + 10, w, trim[3]); cv.hline(x, y + 11, w, trim[1]); cv.hline(x, y + 12, w, C(trim[0], 0.6))


def stencil_frieze(cv, x, y, w, ground="#2a3a30", gilt=GILT_OM, every=12):
    """A Victorian stencilled band under the cornice: gilt lozenges and dots between two rules."""
    cv.rect(x, y, w, 9, ground)
    cv.hline(x, y, w, gilt[2]); cv.hline(x, y + 8, w, gilt[1])
    for xx in range(x + every // 2, x + w, every):
        cv.poly([(xx, y + 2), (xx + 3, y + 4), (xx, y + 7), (xx - 3, y + 4)], gilt[3])
        cv.px(xx, y + 2, gilt[4]); cv.px(xx - 1, y + 3, gilt[4]); cv.px(xx, y + 4, gilt[1])
        cv.px(xx + every // 2, y + 4, gilt[2])
        cv.px(xx + every // 2 - 2, y + 4, gilt[1]); cv.px(xx + every // 2 + 2, y + 4, gilt[1])


def beadboard(cv, x, y, w, h, pal=OAK_IN, seed=0, board=8, rail=True):
    """Oak wainscot of narrow tongue-and-groove boards under a moulded chair rail, on a tall
    skirting board. (x, y) is the top of the rail; the skirting ends at y + h."""
    rng = _rng(seed)
    top = y + (5 if rail else 0)
    bot = y + h - 7
    for bx in range(x, x + w, board):
        bw = min(board, x + w - bx)
        r = rng.random()
        tone = pal[4] if r < 0.7 else (pal[3] if r < 0.9 else shade(pal[4], 0.06))
        cv.rect(bx, top, bw, bot - top, tone)
        cv.vline(bx, top, bot - top, pal[2])
        if bw > 2:
            cv.vline(bx + 1, top, bot - top, pal[5] if tone != pal[5] else pal[6])
            cv.vline(bx + bw // 2, top, bot - top, C(pal[2], 0.35))
        for _ in range(max(1, (bot - top) // 14)):
            gx, gy = bx + 2 + int(rng.integers(0, max(1, bw - 3))), top + int(rng.integers(2, max(3, bot - top - 6)))
            cv.vline(gx, gy, int(rng.integers(3, 8)), shade(tone, -0.12))
    if rail:
        cv.hline(x, y, w, pal[6]); cv.rect(x, y + 1, w, 2, pal[5]); cv.hline(x, y + 3, w, pal[3]); cv.hline(x, y + 4, w, pal[1])
    # skirting: plain board with a moulded top and a dark shoe
    cv.rect(x, bot, w, 7, pal[3])
    cv.hline(x, bot, w, pal[1]); cv.hline(x, bot + 1, w, pal[5]); cv.hline(x, bot + 2, w, pal[4])
    cv.hline(x, bot + 5, w, pal[2]); cv.hline(x, bot + 6, w, pal[1])


def night_glass(cv, mask, top, bottom, seed=0, moon=None, skyline=True, x0=None, x1=None):
    """Fill a window-shaped mask with the campus at night: banded indigo sky with stars, an
    optional moon, the dark Flatirons and a roofline with a few warm windows at the bottom."""
    rng = _rng(seed)
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return
    xa = xs.min() if x0 is None else x0
    xb = xs.max() if x1 is None else x1
    span = max(1, bottom - top)
    bands = [BLUE_NIGHT[1], BLUE_NIGHT[2], BLUE_NIGHT[3], BLUE_NIGHT[3]]
    t = (ys - top) / span
    k = np.clip((t * len(bands)).astype(int), 0, len(bands) - 1)
    cols = P(bands)[k]
    cv.a[ys, xs, :3] = cols
    cv.a[ys, xs, 3] = 1
    for _ in range(max(2, len(ys) // 70)):
        i = int(rng.integers(len(ys)))
        if t[i] < 0.6:
            cv.px(int(xs[i]), int(ys[i]), "#d8d4f0" if rng.random() < 0.6 else "#9a9ad0")
    if moon is not None:
        mx, my, r = moon
        for rr, a in ((r + 4, 0.10), (r + 2, 0.16)):
            m2 = ((xs - mx) ** 2 + (ys - my) ** 2) <= rr * rr
            cv.a[ys[m2], xs[m2], :3] = cv.a[ys[m2], xs[m2], :3] * (1 - a) + np.array(C("#c8d0f0")[:3]) * a
        m1 = ((xs - mx) ** 2 + (ys - my) ** 2) <= r * r
        cv.a[ys[m1], xs[m1], :3] = C(MOON)[:3]
        m3 = m1 & (((xs - mx - 1) ** 2 + (ys - my + 1) ** 2) <= max(1, r - 2) ** 2) & (xs > mx)
        cv.a[ys[m3], xs[m3], :3] = C("#d8caa0")[:3]
    if skyline:
        # Flatirons: three slabs leaning south, then a dark campus roofline with a few lit windows
        hz = bottom - max(6, span // 5)
        for i, (fx, fh) in enumerate(((0.18, 0.22), (0.45, 0.30), (0.74, 0.20))):
            px_ = xa + (xb - xa) * fx
            hh = span * fh
            sel = (ys >= hz - hh + np.abs(xs - px_) * 1.6) & (ys < hz + 2)
            cv.a[ys[sel], xs[sel], :3] = C("#1c1a34")[:3]
            hi = sel & (np.abs(xs - (px_ - 1)) < 1) & (ys < hz - 2)
            cv.a[ys[hi], xs[hi], :3] = C("#2e2a4a")[:3]
        roof = ys >= hz + np.where(((xs // 7) % 3) == 0, -2, 1)
        cv.a[ys[roof], xs[roof], :3] = C("#141226")[:3]
        for _ in range(max(1, (xb - xa) // 9)):
            wx = int(rng.integers(xa, xb + 1)); wy = int(rng.integers(hz + 3, bottom))
            if mask[min(mask.shape[0] - 1, wy), min(mask.shape[1] - 1, wx)]:
                cv.px(wx, wy, "#e9a84a")


def sash_window(cv, x, y, w, h, seed=0, moon=None, pal=OAK_IN, sill=CREAM_TRIM, arch=True, panes=(2, 2)):
    """A tall Victorian sash window in an oak casing: round-headed, two-over-two panes with a meeting
    rail, the campus night outside, a pale reflection streak, a deep painted sill.
    (x, y) is the top-left of the glass box (the arch springs at y + w//2). Returns the glass mask."""
    r = w // 2
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    cxw = x + (w - 1) / 2
    spring = y + r if arch else y

    def shape(grow):
        box = (xs >= x - grow) & (xs < x + w + grow) & (ys >= spring) & (ys < y + h + grow)
        if not arch:
            return box & (ys >= y - grow)
        dome = ((xs - cxw) ** 2 + (ys - spring) ** 2 <= (r + grow) ** 2) & (ys < spring)
        return box | dome
    cv.fill_mask(shape(5), OUT)
    cv.fill_mask(shape(4), pal[3])
    # casing light on the left/top, shadow on the right
    outer = shape(4) & ~shape(2)
    cv.fill_mask(outer & (xs < cxw) & (ys < y + h), pal[5])
    cv.fill_mask(outer & (xs > cxw + r - 1), pal[2])
    cv.fill_mask(shape(2) & ~shape(1), pal[1])
    glass = shape(0)
    night_glass(cv, glass, y, y + h, seed=seed, moon=moon)
    # reflections
    for d in (0, 1):
        cv.fill_mask(glass & (np.abs((xs - x) - (y + h - ys) * 0.45 - w * 0.25 - d * 3) < 0.6), C("#c8d0f0", 0.16))
    # muntins: centre bar, meeting rail, spring bar, arch spokes
    mid = y + (h + (r if arch else 0)) // 2
    cv.fill_mask(glass & (np.abs(xs - cxw) < 1), pal[3])
    cv.fill_mask(glass & (xs == int(cxw) - 1), pal[5])
    cv.fill_mask(glass & (ys >= mid) & (ys < mid + 3), pal[3])
    cv.fill_mask(glass & (ys == mid), pal[5])
    if arch:
        cv.fill_mask(glass & (ys == spring), pal[3])
        for ang in (0.6, np.pi - 0.6):
            for t_ in np.linspace(0, r, r * 2):
                px_, py_ = int(round(cxw + np.cos(ang) * t_)), int(round(spring - np.sin(ang) * t_))
                if 0 <= py_ < cv.h and 0 <= px_ < cv.w and glass[py_, px_]:
                    cv.px(px_, py_, pal[3])
    if panes[1] > 2:
        for k in range(1, panes[1] // 2):
            yy = spring + (mid - spring) * k // (panes[1] // 2)
            cv.fill_mask(glass & (ys == yy), pal[3])
    # sill
    sy = y + h + 4
    cv.rect(x - 7, sy, w + 14, 4, OUT)
    cv.rect(x - 6, sy, w + 12, 3, sill[3]); cv.hline(x - 6, sy, w + 12, sill[5]); cv.hline(x - 6, sy + 2, w + 12, sill[2])
    cv.hline(x - 5, sy + 4, w + 10, C(OUT, 0.5))
    return glass


def radiator(cv, x, y, w, h, pal=SILVER):
    """A silver-painted cast-iron column radiator with its valve and a pipe to the floor."""
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    for cx_ in range(x, x + w, 3):
        cv.rect(cx_, y, 2, h, pal[3])
        cv.vline(cx_, y + 1, h - 2, pal[4]); cv.px(cx_, y, pal[5]); cv.px(cx_ + 1, y, pal[4])
        cv.vline(cx_ + 2, y + 2, h - 4, pal[0])
        cv.px(cx_ + 1, y + 3, pal[5])
    cv.hline(x, y + 2, w, pal[2]); cv.hline(x, y + h - 3, w, pal[2])
    cv.rect(x, y + h, 2, 2, pal[1]); cv.rect(x + w - 2, y + h, 2, 2, pal[1])
    # valve and pipe on the left
    cv.rect(x - 4, y + h - 5, 4, 2, pal[2]); cv.vline(x - 4, y + h - 3, 5, pal[2])
    cv.rect(x - 6, y + h - 8, 5, 2, "#8a2a24"); cv.px(x - 5, y + h - 8, "#c8584a")


def globe_pendant(cv, x, y, chain_top=0, lit=True, r=5):
    """A schoolhouse pendant: chain from the ceiling, a brass gallery, a milk-glass globe glowing
    warm. (x, y) is the globe centre. Returns (x, y)."""
    for cy in range(chain_top, y - r - 3):
        cv.px(x, cy, IRON[2] if (cy - chain_top) % 3 else IRON[3])
    cv.rect(x - 3, chain_top, 7, 2, GILT_OM[2]); cv.hline(x - 3, chain_top, 7, GILT_OM[4])
    if lit:
        for rr, a in ((r * 4, 0.04), (r * 3, 0.06), (r * 2, 0.08)):
            cv.ellipse(x - rr, y - rr, rr * 2 + 1, rr * 2 + 1, C("#f6cf7a", a))
    cv.rect(x - 3, y - r - 3, 7, 3, OUT); cv.rect(x - 2, y - r - 3, 5, 2, GILT_OM[3]); cv.px(x - 2, y - r - 3, GILT_OM[5])
    g = GLOBE if lit else ["#4a4658", "#5e5a6c", "#767284", "#8a8698"]
    cv.ellipse(x - r - 1, y - r - 1, r * 2 + 3, r * 2 + 3, OUT)
    cv.ellipse(x - r, y - r, r * 2 + 1, r * 2 + 1, g[1])
    cv.ellipse(x - r + 1, y - r + 1, r * 2 - 1, r * 2 - 1, g[2])
    cv.ellipse(x - r + 2, y - r + 2, r, r, g[3])
    cv.hline(x - r + 2, y + r - 1, r * 2 - 3, g[0])
    return x, y


def sconce_om(cv, x, y, lit=True):
    """A brass gas-style wall bracket: oval backplate, swan-neck arm and a frosted tulip shade.
    (x, y) is the backplate; returns the shade's glow point."""
    if lit:
        for rr, a in ((16, 0.04), (11, 0.06), (7, 0.08)):
            cv.ellipse(x + 3 - rr, y - 8 - rr, rr * 2 + 1, rr * 2 + 1, C("#f6cf7a", a))
    cv.ellipse(x - 2, y - 3, 5, 8, OUT); cv.ellipse(x - 1, y - 2, 3, 6, GILT_OM[3]); cv.px(x, y - 1, GILT_OM[5])
    cv.hline(x + 1, y, 3, GILT_OM[2]); cv.px(x + 4, y - 1, GILT_OM[2]); cv.vline(x + 4, y - 5, 4, GILT_OM[3])
    cv.rect(x + 2, y - 6, 5, 2, GILT_OM[2])
    sh = ("#e9a84a", "#f6cd78", "#fde9b6") if lit else ("#4e4860", "#6a6480", "#8a849c")
    cv.poly([(x + 1, y - 7), (x + 7, y - 7), (x + 8, y - 13), (x, y - 13)], OUT)
    cv.poly([(x + 2, y - 8), (x + 6, y - 8), (x + 7, y - 12), (x + 1, y - 12)], sh[1])
    cv.vline(x + 3, y - 12, 4, sh[2]); cv.hline(x + 2, y - 8, 5, sh[0])
    return x + 4, y - 10


def horn_speaker(cv, cx, top, wire_to=0, pal=HORN, flip=False, length=20, mouth=10):
    """The hall's old public-address horn, hung from an iron bracket high on the wall and tipped
    down at the room: the driver drum at the back, the cone flaring forward to a wide mouth with a
    lit rolled rim and a dark throat. A cloth-covered wire runs up to the ceiling. (cx, top) is the
    bracket's wall plate. Returns the mouth centre."""
    from scipy import ndimage
    from PIL import Image, ImageDraw
    sg = -1 if flip else 1
    d = np.array([0.5 * sg, 0.866])
    pp = np.array([-d[1], d[0]])
    T = np.array([cx - 7 * sg, top + 8.0])
    M = T + d * length
    ys, xs = np.mgrid[0:cv.h, 0:cv.w].astype(np.float32)
    # wire and wall plate, bracket arm
    cv.vline(cx + 2 * sg, wire_to, top - wire_to, "#14121a"); cv.vline(cx + 3 * sg, wire_to, top - wire_to, pal[2])
    cv.rect(cx - 2, top - 3, 5, 9, OUT); cv.rect(cx - 1, top - 2, 3, 7, pal[3]); cv.px(cx - 1, top - 2, pal[5])
    ax0, ax1 = sorted((cx, int(T[0])))
    cv.rect(ax0, top + 1, ax1 - ax0 + 1, 3, OUT); cv.hline(ax0, top + 2, ax1 - ax0 + 1, pal[4])
    # driver drum behind the throat
    D = T - d * 4
    cv.ellipse(int(D[0]) - 5, int(D[1]) - 5, 11, 11, OUT)
    cv.ellipse(int(D[0]) - 4, int(D[1]) - 4, 9, 9, pal[3])
    cv.ellipse(int(D[0]) - 4, int(D[1]) - 4, 6, 5, pal[4]); cv.px(int(D[0]) - 2, int(D[1]) - 2, pal[6])
    # the cone
    im = Image.new("L", (cv.w, cv.h), 0)
    poly = [tuple(T + pp * 2.5), tuple(M + pp * mouth), tuple(M - pp * mouth), tuple(T - pp * 2.5)]
    ImageDraw.Draw(im).polygon(poly, fill=255)
    cone = np.array(im) > 0
    q = np.stack([xs - T[0], ys - T[1]], -1)
    along = q @ d
    side = q @ pp
    rad = 2.5 + (mouth - 2.5) * np.clip(along / length, 0, 1)
    sn = side / np.maximum(rad, 1)
    qm = np.stack([xs - M[0], ys - M[1]], -1)
    ma, mb = qm @ pp, qm @ d
    rim = (ma / (mouth + 0.5)) ** 2 + (mb / 4.2) ** 2 <= 1
    inner = (ma / (mouth - 1.6)) ** 2 + ((mb + 0.6) / 2.8) ** 2 <= 1
    throat = (ma / (mouth * 0.45)) ** 2 + ((mb + 1.0) / 1.6) ** 2 <= 1
    body = cone | rim
    out = ndimage.binary_dilation(body, structure=np.ones((3, 3))) & ~body
    cv.fill_mask(out, OUT)
    cv.fill_mask(cone & (sn < -0.35), pal[5])
    cv.fill_mask(cone & (sn >= -0.35) & (sn < 0.35), pal[4])
    cv.fill_mask(cone & (sn >= 0.35), pal[2])
    cv.fill_mask(cone & (np.abs(sn + 0.62) < 0.1), pal[6])
    cv.fill_mask(rim, pal[5])
    cv.fill_mask(rim & (ma * sg > 0), pal[3])
    cv.fill_mask(inner, pal[1])
    cv.fill_mask(throat, pal[0])
    cv.fill_mask(rim & ~inner & (mb < -1.5) & (ma * sg < 2), pal[6])
    return int(M[0]), int(M[1])


def notice_paper(cv, x, y, w, h, tint="#ece2c6", seed=0, title=None, ink="#2a2a3a", pin="#c84a3c", tabs=False,
                 rows=None, shadow=True, curl=False, title_col=None):
    """A pinned paper notice: soft shadow on the board, a lit top edge, a small title in 3x5 caps,
    unreadable handwriting/typing below, optional tear-off tabs and a curled corner."""
    from lib_eng import micro_text, micro_width, scribble
    rng = _rng(seed)
    if shadow:
        cv.rect(x + 1, y + 1, w, h, C("#140c08", 0.35))
    cv.rect(x, y, w, h, tint)
    cv.hline(x, y, w, shade(tint, 0.25)); cv.vline(x + w - 1, y + 1, h - 1, shade(tint, -0.12)); cv.hline(x, y + h - 1, w, shade(tint, -0.16))
    yy = y + 3
    if title:
        tw = micro_width(title)
        micro_text(cv, title, x + max(1, (w - tw) // 2), yy, title_col or ink)
        yy += 7
    n = rows if rows is not None else max(0, (y + h - (6 if tabs else 2) - yy) // 3)
    if n > 0 and w > 6:
        scribble(cv, x + 2, yy + 1, w - 4, C(ink, 0.55), seed=seed, rows=n, gap=3)
    if tabs:
        ty = y + h - 6
        cv.hline(x, ty, w, shade(tint, -0.2))
        for tx in range(x + 2, x + w - 1, 3):
            cv.vline(tx, ty + 1, 5, shade(tint, -0.22))
    if curl:
        cv.poly([(x + w - 5, y + h - 1), (x + w - 1, y + h - 5), (x + w - 5, y + h - 5)], shade(tint, -0.25))
    if pin:
        px_ = x + w // 2
        cv.px(px_ + 1, y + 2, C("#140c08", 0.5))
        cv.rect(px_ - 1, y, 2, 2, pin); cv.px(px_ - 1, y, shade(pin, 0.45))


def cork_surface(cv, x, y, w, h, seed=0, pal=CORK):
    """Cork: a warm field with small dark pores and paler grains in tight clusters."""
    cv.rect(x, y, w, h, pal[3])
    ys, xs = np.mgrid[y:y + h, x:x + w]
    n = hashn(xs // 2 + (ys % 2), ys, seed)
    n2 = hashn(xs, ys, seed + 3)
    reg = cv.a[y:y + h, x:x + w]
    reg[(n < 0.16)] = C(pal[2])
    reg[(n2 < 0.05)] = C(pal[1])
    reg[(n > 0.88)] = C(pal[4])


def oak_frame(cv, x, y, w, h, t=4, pal=OAK_IN):
    """A moulded oak picture/board frame (outer ink, lit top/left, shadowed bottom/right, mitres)."""
    cv.rect(x, y, w, h, OUT)
    cv.rect(x + 1, y + 1, w - 2, h - 2, pal[4])
    cv.rect(x + 1, y + 1, w - 2, t - 2, pal[5]); cv.rect(x + 1, y + 1, t - 2, h - 2, pal[5])
    cv.rect(x + 1, y + h - t + 1, w - 2, t - 2, pal[3]); cv.rect(x + w - t + 1, y + 1, t - 2, h - 2, pal[3])
    cv.hline(x + 1, y + 1, w - 2, pal[6])
    for i in range(t - 1):
        cv.px(x + 1 + i, y + h - 2 - i, pal[2]); cv.px(x + w - 2 - i, y + 1 + i, pal[2])
    cv.rect(x + t - 1, y + t - 1, w - 2 * t + 2, h - 2 * t + 2, pal[1])


def scatter_notices(cv, x, y, w, h, seed=0, titles=(), pins=("#c84a3c", "#3a5aa8", "#d8b260", "#3a8a5a"), density=1.0):
    """Fill a board area with overlapping pinned notices; returns their rects [(x, y, w, h, tint)]."""
    rng = _rng(seed)
    out = []
    titles = list(titles)
    cx_ = x + 2
    row_y = y + 2
    while row_y < y + h - 12:
        cx_ = x + 2 + int(rng.integers(0, 4))
        row_h = 0
        while cx_ < x + w - 10:
            pw = int(rng.integers(12, 24)); ph = int(rng.integers(14, 24))
            pw = min(pw, x + w - 2 - cx_)
            ph = min(ph, y + h - 2 - row_y)
            if pw < 9 or ph < 10:
                break
            if rng.random() < 0.88 * density:
                tint = PAPER_TINTS[int(rng.integers(len(PAPER_TINTS)))]
                title = titles.pop(0) if titles and rng.random() < 0.7 else None
                if title and (len(title) * 4) > pw - 2:
                    title = None
                py_ = row_y + int(rng.integers(0, 4))
                ph = min(ph, y + h - 2 - py_)
                notice_paper(cv, cx_, py_, pw, ph, tint=tint, seed=int(rng.integers(1e6)), title=title,
                             pin=pins[int(rng.integers(len(pins)))], tabs=rng.random() < 0.2 and ph > 16)
                out.append((cx_, py_, pw, ph, tint))
            cx_ += pw + int(rng.integers(1, 5))
            row_h = max(row_h, ph)
        row_y += max(12, row_h - int(rng.integers(0, 5)))
    return out


def schoolhouse_clock(cv, cx, top, hour=11, minute=42, pal=OAK_IN):
    """An octagonal schoolhouse wall clock with a drop case below (glass door, brass pivot).
    Returns the pendulum pivot (x, y) and the drop window (x, y, w, h)."""
    r = 9
    cy = top + r + 1
    oct_ = [(cx - 4, cy - r - 1), (cx + 4, cy - r - 1), (cx + r + 1, cy - 4), (cx + r + 1, cy + 4), (cx + 4, cy + r + 1),
            (cx - 4, cy + r + 1), (cx - r - 1, cy + 4), (cx - r - 1, cy - 4)]
    cv.poly([(px_ + (1 if px_ > cx else -1), py_ + (1 if py_ > cy else -1)) for px_, py_ in oct_], OUT)
    cv.poly(oct_, pal[4])
    cv.poly([(cx - 4, cy - r - 1), (cx + 4, cy - r - 1), (cx + r + 1, cy - 4), (cx - r - 1, cy - 4)], pal[5])
    # drop case
    cv.rect(cx - 7, cy + r - 1, 15, 17, OUT)
    cv.rect(cx - 6, cy + r - 1, 13, 15, pal[4]); cv.vline(cx - 6, cy + r, 14, pal[5]); cv.vline(cx + 6, cy + r, 14, pal[2])
    win = (cx - 4, cy + r + 2, 9, 9)
    cv.rect(win[0], win[1], win[2], win[3], "#1e1418"); cv.rect(win[0] + 1, win[1] + 1, win[2] - 2, win[3] - 2, "#2a2024")
    cv.px(win[0] + 1, win[1] + 7, C("#8a96c8", 0.4)); cv.px(win[0] + 2, win[1] + 6, C("#8a96c8", 0.4))
    cv.poly([(cx - 6, cy + r + 13), (cx + 7, cy + r + 13), (cx + 3, cy + r + 17), (cx - 2, cy + r + 17)], pal[3])
    # dial
    cv.ellipse(cx - 7, cy - 7, 15, 15, OUT)
    cv.ellipse(cx - 6, cy - 6, 13, 13, "#e8dcc0")
    cv.ellipse(cx - 6, cy - 6, 13, 13, "#e8dcc0")
    for (dx, dy) in ((0, -5), (5, 0), (0, 5), (-5, 0)):
        cv.px(cx + dx, cy + dy, "#3a2a26")
    a_h = (hour % 12 + minute / 60) / 12 * 2 * np.pi
    a_m = minute / 60 * 2 * np.pi
    cv.line(cx, cy, int(round(cx + np.sin(a_h) * 3)), int(round(cy - np.cos(a_h) * 3)), "#2a1a16")
    cv.line(cx, cy, int(round(cx + np.sin(a_m) * 5)), int(round(cy - np.cos(a_m) * 5)), "#2a1a16")
    cv.px(cx, cy, GILT_OM[3])
    return (cx, win[1] + 1), win


def framed_photo(cv, x, y, w, h, seed=0, rows=3, caption=None):
    """A sepia class photograph in a dark frame: rows of tiny figures (heads and shoulders, no
    faces), a pale sky above them; an optional 3x5 caption plate below."""
    from lib_eng import micro_text, micro_width
    rng = _rng(seed)
    cv.rect(x, y, w, h, OUT)
    cv.rect(x + 1, y + 1, w - 2, h - 2, "#2a1a14"); cv.hline(x + 1, y + 1, w - 2, "#4a3020")
    cv.rect(x + 2, y + 2, w - 4, h - 4, GILT_OM[2])
    px0, py0, pw, ph = x + 3, y + 3, w - 6, h - 6
    cv.rect(px0, py0, pw, ph, "#a08a68")
    cv.rect(px0, py0, pw, ph // 3, "#b49c78")
    cv.rect(px0, py0 + ph - 3, pw, 3, "#7a6448")
    for r in range(rows):
        ry = py0 + ph // 3 + r * max(3, (ph * 2 // 3 - 3) // rows)
        off = (r % 2) * 2
        for hx in range(px0 + 1 + off, px0 + pw - 2, 4):
            if rng.random() < 0.9:
                cv.rect(hx, ry, 2, 2, "#4a3828" if rng.random() < 0.7 else "#6a5438")
                cv.rect(hx - 1, ry + 2, 4, 2, "#3a2a20" if rng.random() < 0.6 else "#5a4a38")
    if caption:
        cw = micro_width(caption) + 4
        cv.rect(x + (w - cw) // 2, y + h + 1, cw, 7, GILT_OM[2]); cv.hline(x + (w - cw) // 2, y + h + 1, cw, GILT_OM[4])
        micro_text(cv, caption, x + (w - cw) // 2 + 2, y + h + 2, "#3a2a14")


def elevation_print(cv, x, y, w, h, title="OLD MAIN 1876"):
    """A framed architect's elevation of Old Main in brown ink on cream paper."""
    from lib_eng import micro_text, micro_width
    oak_frame(cv, x, y, w, h, t=4)
    px0, py0, pw, ph = x + 4, y + 4, w - 8, h - 8
    cv.rect(px0, py0, pw, ph, "#d8ccaa"); cv.rect(px0 + 2, py0 + 2, pw - 4, ph - 4, "#e4d8b6")
    ink = "#6a4430"
    gy = py0 + ph - 10
    bx0, bx1 = px0 + 6, px0 + pw - 6
    cxp = (bx0 + bx1) // 2
    cv.hline(bx0 - 2, gy, bx1 - bx0 + 5, ink)
    ey = gy - 14
    cv.hline(bx0, ey, bx1 - bx0 + 1, ink); cv.vline(bx0, ey, gy - ey, ink); cv.vline(bx1, ey, gy - ey, ink)
    cv.line(bx0 - 1, ey, bx0 + 8, ey - 5, ink); cv.line(bx0 + 8, ey - 5, bx1 - 8, ey - 5, ink); cv.line(bx1 - 8, ey - 5, bx1 + 1, ey, ink)
    for wx in range(bx0 + 3, bx1 - 1, 5):
        if abs(wx - cxp) > 4:
            cv.vline(wx, ey + 3, 3, ink); cv.vline(wx, ey + 9, 3, ink)
    ty = ey - 22
    cv.vline(cxp - 4, ty, gy - ty, ink); cv.vline(cxp + 4, ty, gy - ty, ink)
    cv.line(cxp - 5, ty, cxp, ty - 7, ink); cv.line(cxp, ty - 7, cxp + 5, ty, ink); cv.vline(cxp, ty - 10, 3, ink)
    cv.rect(cxp - 2, ty + 3, 5, 4, ink); cv.px(cxp, ty + 4, "#e4d8b6")
    cv.rect(cxp - 2, gy - 6, 5, 6, ink)
    tw = micro_width(title)
    micro_text(cv, title, px0 + (pw - tw) // 2, py0 + ph - 7, ink)


# =============================================================================================
# floors
# =============================================================================================
TILE_OX = ["#2a1412", "#3e1e1a", "#4e2620", "#5e2e26"]     # the darker red-brown lozenge


def encaustic_floor(cv, x, y, w, h, seed=0, sx=16, sy=10, pal_a=TILE_TERRA, pal_b=TILE_OX, key=TILE_CREAM, ink=TILE_INK, wear=None):
    """Victorian encaustic tile laid on the diagonal, foreshortened for the top-down view: terracotta
    and dark red-brown lozenges in a check, a small cream square where four meet, dark grout. Each
    tile has its own tone; a few are worn pale or cracked. `wear` is an optional (h, w) 0..1 map that
    pales the tiles along the paths people walk."""
    ys, xs = np.mgrid[y:y + h, x:x + w].astype(np.float32)
    u = xs / sx + ys / sy
    v = xs / sx - ys / sy
    iu, iv = np.floor(u), np.floor(v)
    fu, fv = u - iu, v - iv
    check = ((iu + iv) % 2).astype(int)
    t = hashn(iu.astype(int), iv.astype(int), seed)
    A, B, Kc, K = P(pal_a), P(pal_b), P(key), P(ink)
    tone = np.where(t < 0.25, 1, 2)
    rgb = np.where(check[..., None] == 0, A[tone], B[tone])
    # lit upper edges of each lozenge, grout round it
    lit = ((fu < 0.12) | (fv > 0.88))
    rgb = np.where(lit[..., None], np.where(check[..., None] == 0, A[3], B[3]), rgb)
    grout = (fu < 0.05) | (fv < 0.05)
    rgb[grout] = K[1]
    # small cream keys where four lozenges meet, ink-edged
    du, dv = np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv)
    keyo = (du < 0.16) & (dv < 0.16)
    keyi = (du < 0.10) & (dv < 0.10)
    rgb[keyo] = K[0]
    rgb[keyi] = Kc[2]
    rgb[keyi & (fu > 0.5) & (fv > 0.5)] = Kc[3]
    # worn and cracked tiles
    worn = (t > 0.95) & ~grout & ~keyo
    rgb[worn] = rgb[worn] * 0.82 + np.array(C("#c8a888")[:3]) * 0.18
    crack = (t > 0.90) & (t < 0.92) & (np.abs(fu - fv * 0.7 - 0.2) < 0.05)
    rgb[crack] = K[1]
    if wear is not None:
        wmask = ~grout & ~keyo & (hashn(iu.astype(int), iv.astype(int), seed + 5) < wear * 0.8)
        rgb[wmask] = rgb[wmask] * 0.88 + np.array(C("#c8a888")[:3]) * 0.12
    reg = cv.a[y:y + h, x:x + w]
    reg[..., :3] = rgb
    reg[..., 3] = 1


def tile_border(cv, x, y, w, h, band=7, pal_a=TILE_OX, pal_b=TILE_CREAM, ink=TILE_INK):
    """A plain border round a tiled field: an ink fillet, a terracotta band with cream squares, an
    ink fillet."""
    for (bx, by, bw, bh) in ((x, y, w, band), (x, y + h - band, w, band), (x, y, band, h), (x + w - band, y, band, h)):
        cv.rect(bx, by, bw, bh, pal_a[2])
    cv.rect(x + band, y + band, w - 2 * band, 1, ink[0]); cv.rect(x + band, y + h - band - 1, w - 2 * band, 1, ink[0])
    cv.rect(x + band, y + band, 1, h - 2 * band, ink[0]); cv.rect(x + w - band - 1, y + band, 1, h - 2 * band, ink[0])
    cv.rect(x, y, w, 1, ink[0]); cv.rect(x, y + h - 1, w, 1, ink[0]); cv.rect(x, y, 1, h, ink[0]); cv.rect(x + w - 1, y, 1, h, ink[0])
    for xx in range(x + 4, x + w - 4, 10):
        for yy in (y + band // 2 - 1, y + h - band // 2 - 2):
            cv.rect(xx, yy, 3, 2, pal_b[2]); cv.px(xx, yy, pal_b[3])
    for yy in range(y + 6, y + h - 6, 8):
        for xx in (x + band // 2 - 1, x + w - band // 2 - 2):
            cv.rect(xx, yy, 3, 2, pal_b[2]); cv.px(xx, yy, pal_b[3])


def runner_om(cv, x, y, w, h, pal=RUNNER_OM, gilt=GILT_OM, vertical=False, fringe=None, motif=14, seed=0):
    """A long hall runner: dark edge, gilt and plum border bands, an indigo field with a repeating
    small medallion; fringe ends optional ("start", "end", "both")."""
    cv.rect(x, y, w, h, pal[0])
    cv.rect(x + 1, y + 1, w - 2, h - 2, pal[4])
    cv.rect(x + 2, y + 2, w - 4, h - 4, gilt[2])
    cv.rect(x + 3, y + 3, w - 6, h - 6, pal[1])
    cv.rect(x + 4, y + 4, w - 8, h - 8, pal[2])
    rng = _rng(seed)
    if vertical:
        cxr = x + w // 2
        for yy in range(y + 8, y + h - 6, motif):
            cv.poly([(cxr, yy), (cxr + 4, yy + 3), (cxr, yy + 6), (cxr - 4, yy + 3)], pal[4])
            cv.px(cxr, yy + 3, gilt[3]); cv.px(cxr, yy, pal[5])
            cv.px(x + 6, yy + 3, pal[3]); cv.px(x + w - 7, yy + 3, pal[3])
    else:
        cyr = y + h // 2
        for xx in range(x + 8, x + w - 6, motif):
            cv.poly([(xx, cyr - 3), (xx + 4, cyr), (xx, cyr + 3), (xx - 4, cyr)], pal[4])
            cv.px(xx, cyr, gilt[3]); cv.px(xx - 1, cyr - 2, pal[5])
            cv.px(xx + motif // 2, y + 6, pal[3]); cv.px(xx + motif // 2, y + h - 7, pal[3])
    # a little wear along the middle
    for _ in range(max(2, (w * h) // 900)):
        wx, wy = int(rng.integers(x + 5, x + w - 5)), int(rng.integers(y + 5, y + h - 5))
        cv.rect(wx, wy, 3, 1, pal[3])
    if fringe:
        ends = []
        if vertical:
            if fringe in ("start", "both"): ends.append(("v", y - 3))
            if fringe in ("end", "both"): ends.append(("v", y + h))
            for _, fy in ends:
                for fx in range(x + 1, x + w - 1, 2):
                    cv.vline(fx, fy, 3, "#c8b892")
        else:
            if fringe in ("start", "both"): ends.append(("h", x - 3))
            if fringe in ("end", "both"): ends.append(("h", x + w))
            for _, fx in ends:
                for fy in range(y + 1, y + h - 1, 2):
                    cv.hline(fx, fy, 3, "#c8b892")


def spill(cv, x, y, w, h, colour, steps=((1.0, 0.05), (0.72, 0.05), (0.45, 0.06)), side="left"):
    """Light spilling in through a doorway at a room edge: stepped half-ellipses fading away from
    the edge. (x, y, w, h) bounds the largest one."""
    for f, a in steps:
        ww, hh = int(w * f), int(h * (0.55 + 0.45 * f))
        yy = y + (h - hh) // 2
        if side == "left":
            cv.ellipse(x - ww, yy, ww * 2, hh, C(colour, a))
        elif side == "right":
            cv.ellipse(x + w - ww, yy, ww * 2, hh, C(colour, a))
        else:  # bottom
            hb = int(h * f); wb = int(w * (0.55 + 0.45 * f))
            cv.ellipse(x + (w - wb) // 2, y + h - hb, wb, hb * 2, C(colour, a))


# =============================================================================================
# office pieces (O03 empty office, O04 cabinet room)
# =============================================================================================
BOARDS = ["#2a1a14", "#3e271c", "#4e3222", "#5c3c28", "#6a462e", "#785036", "#8a5e40"]   # worn oak floor
RUG_GREEN = ["#141e1a", "#1e2c26", "#2a3c32", "#36503e", "#8a6a3a", "#b48a4a", "#d8b26a"]
SLATE_BOARD = ["#1a2024", "#222a2e", "#2c3638", "#3a4648"]
CHALK = ["#8a9494", "#b4bcb8", "#dce2dc"]
LEATHER = ["#1c1210", "#2e1c16", "#44281e", "#5a3626", "#704430"]
STEEL_OM = ["#1a1c22", "#2a2e36", "#3c424c", "#525a64", "#6c7680", "#8a949c"]


def oak_boards(cv, x, y, w, h, seed=0, pal=BOARDS, row=7, mask=None):
    """Worn oak floorboards running across the room: each board its own tone, staggered butt
    joints, a dark seam under each row, a lit edge on top, nail pairs at the joists and a few
    grain streaks."""
    rng = _rng(seed)
    yy = y
    while yy < y + h:
        rh = min(row, y + h - yy)
        xx = x - int(rng.integers(0, 60))
        while xx < x + w:
            pl = int(rng.integers(50, 120))
            x0, x1 = max(x, xx), min(x + w, xx + pl)
            if x1 > x0:
                k = rng.random()
                tone = pal[4] if k < 0.55 else (pal[3] if k < 0.8 else pal[5])
                cv.rect(x0, yy, x1 - x0, rh, tone)
                cv.hline(x0, yy, x1 - x0, shade(tone, 0.08))
                for _ in range(max(1, (x1 - x0) // 30)):
                    gx = int(rng.integers(x0, max(x0 + 1, x1 - 6)))
                    cv.hline(gx, yy + 2 + int(rng.integers(0, max(1, rh - 3))), int(rng.integers(4, 12)), shade(tone, -0.1))
                if xx + pl < x + w:
                    cv.vline(xx + pl - 1, yy, rh, pal[1])
            xx += pl
        cv.hline(x, yy + rh - 1, w, pal[2])
        for nx in range(x + 20, x + w, 48):
            cv.px(nx + (yy // row) % 2 * 3, yy + 2, pal[2]); cv.px(nx + (yy // row) % 2 * 3, yy + 4, pal[2])
        yy += rh


def ghost_outline(cv, x, y, w, h, alpha=0.11, dust="#b8a488"):
    """Where furniture or a frame stood for decades: an unfaded patch with a dusty rim."""
    cv.rect(x, y, w, h, C("#0d0b16", alpha))
    cv.hline(x, y - 1, w, C(dust, 0.22)); cv.hline(x, y + h, w, C(dust, 0.22))
    cv.vline(x - 1, y, h, C(dust, 0.18)); cv.vline(x + w, y, h, C(dust, 0.18))


def ghost_frame(cv, x, y, w, h, wall, rail_y=None, hook=True):
    """A picture taken down: a cleaner, darker rectangle on faded paint, the wire's hook left on the
    picture rail and its cord hanging empty."""
    cv.rect(x, y, w, h, shade(wall, 0.07))
    cv.rect(x + 1, y + 1, w - 2, h - 2, shade(wall, 0.04))
    cv.hline(x, y + h, w, C("#0d0b16", 0.2))
    if hook and rail_y is not None:
        hx = x + w // 2
        cv.rect(hx - 1, rail_y, 3, 3, GILT_OM[2]); cv.px(hx, rail_y, GILT_OM[4])
        cv.line(hx, rail_y + 3, hx - w // 4, y - 2, C("#2a2420", 0.7))
        cv.line(hx, rail_y + 3, hx + w // 4, y - 2, C("#2a2420", 0.7))


def panel_wainscot(cv, x, y, w, h, pal=OAK_IN, panel=34, seed=0):
    """Frame-and-panel oak dado: a moulded cap, stiles and rails, bevelled raised panels, a tall
    skirting at the floor."""
    cv.rect(x, y, w, h, pal[3])
    cv.hline(x, y, w, pal[6]); cv.rect(x, y + 1, w, 2, pal[5]); cv.hline(x, y + 3, w, pal[2])
    sk = h - 7
    for px_ in range(x + 5, x + w - panel // 2, panel):
        pw = min(panel - 6, x + w - 5 - px_)
        if pw < 8:
            break
        ph = sk - 10
        cv.rect(px_, y + 7, pw, ph, pal[2])
        cv.rect(px_ + 1, y + 8, pw - 2, ph - 2, pal[4])
        cv.rect(px_ + 3, y + 10, pw - 6, ph - 6, pal[3])
        cv.hline(px_ + 1, y + 8, pw - 2, pal[5]); cv.vline(px_ + 1, y + 8, ph - 2, pal[5])
        cv.hline(px_ + 3, y + ph + 3, pw - 6, pal[5])
    cv.rect(x, y + sk, w, 7, pal[2]); cv.hline(x, y + sk, w, pal[1]); cv.hline(x, y + sk + 1, w, pal[4])
    cv.hline(x, y + h - 1, w, pal[1])


def chalkboard(cv, x, y, w, h, seed=0, heading="GATHER ALL", footer="DO NOT CLOSE"):
    """A slate chalkboard in an oak frame with its tray: half-erased smudges and, still legible, a
    diagram of a ring of little figures with arrows pointing in to one centre."""
    from lib_eng import micro_text, micro_width
    rng = _rng(seed)
    oak_frame(cv, x, y, w, h, t=3)
    bx, by, bw, bh = x + 3, y + 3, w - 6, h - 6
    cv.rect(bx, by, bw, bh, SLATE_BOARD[1])
    # erased smudges
    f = soft_noise(bw, bh, 12, seed)
    reg = cv.a[by:by + bh, bx:bx + bw]
    reg[f > 0.62, :3] = C(SLATE_BOARD[2])[:3]
    reg[f > 0.80, :3] = C(SLATE_BOARD[3])[:3]
    # the diagram
    cx_, cy_ = bx + bw // 2, by + bh // 2 + 3
    rx, ry = min(bw // 2 - 12, 34), min(bh // 2 - 8, 16)
    cv.rect(cx_ - 3, cy_ - 2, 7, 5, CHALK[1]); cv.rect(cx_ - 2, cy_ - 1, 5, 3, SLATE_BOARD[1])
    n = 12
    for k in range(n):
        a = k / n * 2 * np.pi
        px_, py_ = int(round(cx_ + np.cos(a) * rx)), int(round(cy_ + np.sin(a) * ry))
        cv.rect(px_ - 1, py_ - 2, 2, 2, CHALK[2]); cv.rect(px_ - 1, py_, 2, 2, CHALK[1])
        if k % 2 == 0:
            ex, ey = cx_ + np.cos(a) * 6, cy_ + np.sin(a) * 4
            sx_, sy_ = cx_ + np.cos(a) * (rx - 4), cy_ + np.sin(a) * (ry - 3)
            cv.line(int(round(sx_)), int(round(sy_)), int(round(ex)), int(round(ey)), C(CHALK[0], 0.85))
    tw = micro_width(heading)
    micro_text(cv, heading, bx + (bw - tw) // 2, by + 3, CHALK[2])
    if footer:
        fw = micro_width(footer)
        micro_text(cv, footer, bx + (bw - fw) // 2, by + bh - 7, CHALK[1])
        cv.hline(bx + (bw - fw) // 2, by + bh - 1, fw, C(CHALK[1], 0.6))
    for _ in range(5):
        sx_, sy_ = int(rng.integers(bx + 2, bx + bw - 12)), int(rng.integers(by + 10, by + bh - 10))
        cv.hline(sx_, sy_, int(rng.integers(4, 10)), C(CHALK[0], 0.5))
    # tray, chalk, a felt eraser
    cv.rect(x + 2, y + h - 1, w - 4, 3, OUT); cv.hline(x + 3, y + h - 1, w - 6, OAK_IN[5])
    cv.rect(x + 12, y + h - 2, 4, 1, CHALK[2]); cv.rect(x + w - 24, y + h - 3, 9, 2, "#4a3a2a"); cv.hline(x + w - 24, y + h - 3, 9, "#7a6a5a")


def venetian_blind(cv, x, y, w, h, slat=3, pal=("#8a7a62", "#a8987a", "#c8b894", "#5a4e40"), cord=True):
    """A wooden venetian blind lowered over the top of a window: slats with a lit top edge, the
    bottom rail, ladder tapes and a pull cord with its acorn."""
    for yy in range(y, y + h - 3, slat):
        cv.hline(x, yy, w, pal[2]); cv.hline(x, yy + 1, w, pal[1])
        if slat > 2:
            cv.hline(x, yy + 2, w, C(pal[3], 0.0))
    cv.rect(x - 1, y + h - 3, w + 2, 3, pal[3]); cv.hline(x - 1, y + h - 3, w + 2, pal[1])
    cv.rect(x - 1, y - 2, w + 2, 3, pal[3]); cv.hline(x - 1, y - 2, w + 2, pal[2])
    for tx in (x + w // 5, x + w - w // 5):
        cv.vline(tx, y, h - 3, C(pal[3], 0.6))
    if cord:
        cv.vline(x + w - 3, y, h + 14, pal[0]); cv.rect(x + w - 4, y + h + 14, 3, 4, pal[1]); cv.px(x + w - 4, y + h + 14, pal[2])
    return [(x + w - 3, y + h)]


def reel(cv, cx, cy, r, angle=0.0, tape=0.6, hub="#9aa0aa"):
    """A reel of tape seen face-on: aluminium flange, a dark ring of wound tape, three spokes."""
    cv.ellipse(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, OUT)
    cv.ellipse(cx - r, cy - r, 2 * r + 1, 2 * r + 1, "#a8aeb8")
    cv.ellipse(cx - r + 1, cy - r + 1, 2 * r - 1, 2 * r - 1, "#8a909c")
    rt = max(2, int(r * (0.35 + 0.6 * tape)))
    cv.ellipse(cx - rt, cy - rt, 2 * rt + 1, 2 * rt + 1, "#2a1e1a")
    cv.ellipse(cx - rt + 1, cy - rt + 1, 2 * rt - 1, 2 * rt - 1, "#3a2a22")
    cv.ellipse(cx - 2, cy - 2, 5, 5, hub)
    for k in range(3):
        a = angle + k * 2 * np.pi / 3
        for t_ in range(2, max(3, rt)):
            cv.px(int(round(cx + np.cos(a) * t_)), int(round(cy + np.sin(a) * t_)), "#c8ccd4" if t_ < rt - 1 else "#6a707a")
    cv.px(cx, cy, OUT)


def reel_recorder(cv, x, y, w=40, h=22, angle=0.0, lit=True):
    """A reel-to-reel tape recorder lying on a desk, its lid up: two reels, the tape path past the
    heads, a VU window glowing, three piano keys. (x, y) is the top-left of the deck."""
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, "#3a3430"); cv.hline(x, y, w, "#5a524a"); cv.vline(x, y, h, "#4a443e")
    r = min(h // 2 - 3, w // 5)
    c1, c2 = (x + r + 3, y + r + 3), (x + w - r - 4, y + r + 3)
    reel(cv, c1[0], c1[1], r, angle, tape=0.75)
    reel(cv, c2[0], c2[1], r, -angle * 0.8, tape=0.3)
    ty = y + h - 6
    cv.line(c1[0], c1[1] + r - 1, x + w // 2 - 3, ty, "#5a3a26"); cv.line(c2[0], c2[1] + r - 1, x + w // 2 + 3, ty, "#5a3a26")
    cv.hline(x + w // 2 - 3, ty, 7, "#6a4a30")
    cv.rect(x + w // 2 - 2, ty + 1, 5, 2, "#8a909c")
    cv.rect(x + 3, y + h - 4, 6, 2, "#f6cd78" if lit else "#4a443e")
    for k in range(3):
        cv.rect(x + w - 16 + k * 4, y + h - 4, 3, 2, "#d8d0c0")


def banker_lamp_om(cv, x, y, lit=True):
    """A green-shaded banker's lamp on a desk: (x, y) is its foot on the desk top. ~12px tall."""
    if lit:
        for rr, a in ((14, 0.05), (9, 0.08)):
            cv.ellipse(x - rr, y - 6 - rr // 2, rr * 2 + 1, rr + 4, C("#f6cf7a", a))
    cv.rect(x - 4, y - 2, 9, 2, OUT); cv.hline(x - 3, y - 2, 7, GILT_OM[3])
    cv.vline(x, y - 8, 6, GILT_OM[2]); cv.px(x + 1, y - 7, GILT_OM[4])
    cv.poly([(x - 7, y - 8), (x + 7, y - 8), (x + 5, y - 13), (x - 5, y - 13)], OUT)
    cv.poly([(x - 6, y - 9), (x + 6, y - 9), (x + 4, y - 12), (x - 4, y - 12)], "#2a6a4a")
    cv.hline(x - 4, y - 12, 9, "#4a9a6a"); cv.hline(x - 6, y - 9, 13, "#f6cd78" if lit else "#1e4a34")
    if lit:
        cv.rect(x - 5, y - 8, 11, 2, C("#fde9b6", 0.6))


# =============================================================================================
# cabinet room pieces (O04)
# =============================================================================================
WALNUT = ["#1c100c", "#2c1a12", "#3e2618", "#52321e", "#664026", "#7a4e30", "#925e3a"]
PARQUET = ["#24140e", "#3a2216", "#4e2e1c", "#5c3822", "#6a4228", "#784c2e", "#8e6040"]
VELVET_G = ["#0e1a16", "#16261e", "#1e3428", "#284434", "#345642", "#44684e"]
BRASS_OM = ["#3a2a12", "#5e4420", "#8a6630", "#b48a44", "#d8b260", "#f2d690"]
RUG_RED = ["#1e0c10", "#3a1218", "#561c22", "#6e262a", "#1c2238", "#2c3456", "#a8823c", "#d8b260"]


def damask(cv, x, y, w, h, pal=OXBLOOD, seed=0, rep=(16, 20)):
    """Damask wallpaper: a two-tone field with a repeating stylised flower-and-leaf motif in a
    half-drop, a faint vertical paper seam every 48px."""
    rx, ry = rep
    cv.rect(x, y, w, h, pal[4])
    ys, xs = np.mgrid[y:y + h, x:x + w]
    col = (xs - x) // rx
    yy = (ys - y + (col % 2) * (ry // 2)) % ry
    xx = (xs - x) % rx
    cxm, cym = rx // 2, ry // 2
    dx, dy = np.abs(xx - cxm), np.abs(yy - cym)
    motif = (dx / 4.5 + dy / 7.0) <= 1.0                    # the lozenge flower
    stem = (dx == 0) & (np.abs(yy - cym) <= 9)
    leaf = ((np.abs(dx - 3) <= 1) & (np.abs(yy - cym - 5) <= 1)) | ((np.abs(dx - 3) <= 1) & (np.abs(yy - cym + 5) <= 1))
    m = motif | stem | leaf
    reg = cv.a[y:y + h, x:x + w]
    reg[m] = C(pal[5])
    hi = motif & (xx < cxm) & (yy < cym)
    reg[hi] = C(pal[6])
    core = (dx / 1.5 + dy / 2.5) <= 1.0
    reg[core] = C(pal[3])
    seam = ((xs - x) % 48) == 0
    reg[seam] = C(pal[3])


def draped_window(cv, x, y, w, h, seed=0, moon=None, drape=VELVET_G, pelmet=BRASS_OM):
    """A tall sash window dressed with heavy velvet drapes tied back with gold cords and a
    pelmet board across the top. (x, y, w, h) is the glass box."""
    glass = sash_window(cv, x, y, w, h, seed=seed, moon=moon, pal=WALNUT)
    dw = max(8, w // 3)
    for side in (-1, 1):
        x0 = x - dw + 2 if side < 0 else x + w - 2
        top, bot = y - 6, y + h + 12
        pts = [(x0, top), (x0 + dw, top), (x0 + dw - (dw // 2 if side < 0 else 0), y + h // 2), (x0 + dw, bot), (x0, bot)]
        if side > 0:
            pts = [(x0, top), (x0 + dw, top), (x0 + dw, bot), (x0, bot), (x0 + dw // 2, y + h // 2)]
        cv.poly([(p[0] + (1 if side > 0 else -1), p[1]) for p in pts], OUT)
        cv.poly(pts, drape[3])
        for k in range(1, 4):
            fx = x0 + k * dw // 4
            cv.vline(fx, top + 2, bot - top - 4, drape[2])
            cv.vline(fx + 1, top + 2, bot - top - 4, drape[4])
        cy = y + h // 2
        tx = x0 + (dw - 3 if side < 0 else 2)
        cv.rect(tx - 2, cy - 1, 5, 3, pelmet[4]); cv.px(tx, cy + 2, pelmet[3]); cv.px(tx, cy + 3, pelmet[3])
    cv.rect(x - dw - 2, y - 12, w + 2 * dw + 4, 8, OUT)
    cv.rect(x - dw - 1, y - 11, w + 2 * dw + 2, 6, WALNUT[4]); cv.hline(x - dw - 1, y - 11, w + 2 * dw + 2, WALNUT[6])
    cv.hline(x - dw - 1, y - 7, w + 2 * dw + 2, pelmet[3])
    return glass


def oval_portrait(cv, cx, cy, rx=10, ry=13, seed=0, bg="#2a3a3a"):
    """A gilt oval frame holding a dim old portrait: only a dark head-and-shoulders silhouette
    against a painted ground (no likeness)."""
    cv.ellipse(cx - rx - 3, cy - ry - 3, 2 * rx + 7, 2 * ry + 7, OUT)
    cv.ellipse(cx - rx - 2, cy - ry - 2, 2 * rx + 5, 2 * ry + 5, BRASS_OM[3])
    cv.ellipse(cx - rx - 1, cy - ry - 1, 2 * rx + 3, 2 * ry + 3, BRASS_OM[2])
    cv.px(cx - rx // 2, cy - ry - 2, BRASS_OM[5]); cv.px(cx - rx, cy - ry // 2, BRASS_OM[5])
    cv.ellipse(cx - rx, cy - ry, 2 * rx + 1, 2 * ry + 1, bg)
    cv.ellipse(cx - rx + 2, cy - ry + 2, rx, ry, shade(bg, 0.12))
    sil = "#151218"
    cv.ellipse(cx - 4, cy - 7, 9, 10, sil)
    cv.ellipse(cx - 8, cy + 3, 17, 14, sil)
    cv.rect(cx - 1, cy + 3, 3, 4, shade(bg, 0.25))


def stamp_head(cv, cx, top, label, ink, lowered=0, handle=WALNUT):
    """One stamp of the rig hanging on its piston: brass cylinder, steel rod, a walnut handle and a
    rubber block with its word facing out. `lowered` pushes the rod down."""
    from lib_eng import micro_text, micro_width
    cv.rect(cx - 4, top, 9, 12, OUT); cv.rect(cx - 3, top + 1, 7, 10, BRASS_OM[3]); cv.vline(cx - 3, top + 1, 10, BRASS_OM[5])
    cv.hline(cx - 3, top + 4, 7, BRASS_OM[2]); cv.hline(cx - 3, top + 8, 7, BRASS_OM[2])
    rod = 10 + lowered
    cv.rect(cx - 1, top + 12, 3, rod, OUT); cv.vline(cx, top + 12, rod, "#b4bcc8")
    hy = top + 12 + rod
    cv.rect(cx - 5, hy, 11, 5, OUT); cv.rect(cx - 4, hy + 1, 9, 3, handle[4]); cv.hline(cx - 4, hy + 1, 9, handle[6])
    bw = max(18, micro_width(label) + 6)
    cv.rect(cx - bw // 2 - 1, hy + 5, bw + 2, 9, OUT)
    cv.rect(cx - bw // 2, hy + 5, bw, 3, handle[3])
    cv.rect(cx - bw // 2, hy + 8, bw, 5, ink[2]); cv.hline(cx - bw // 2, hy + 8, bw, ink[3])
    micro_text(cv, label, cx - micro_width(label) // 2, hy + 8, "#fff0e0")
    return hy + 14


def stamp_rig(cv, cx, top, state="active", lowered=(0, 0, 0), pipe_to=None):
    """Todd's stamp-audit rig bolted to the wall: a riveted brass gantry on iron brackets, three
    stamps on pistons (DENIED, AUDIT, APPROVED), a caged red AUDIT lamp and its sign above, a
    pressure gauge, an ink-pad table with stacks of forms below. state "active" (lamp ready),
    "approved" (the sign reads FINITE PLAN / APPROVED in green, the stamps at rest), "damaged"
    (an arm wrenched loose, the AUDIT stamp fallen, the lamp cracked, a REPAIRS PENDING tag).
    Returns key points."""
    from lib_eng import micro_text, micro_width
    pts = {}
    w = 168
    x0 = cx - w // 2
    beam = top + 30
    # pipes along the wall
    cv.rect(x0 - 24, beam + 4, 24, 3, OUT); cv.hline(x0 - 24, beam + 5, 24, BRASS_OM[3])
    pl = (pipe_to if pipe_to is not None else beam + 94) - beam - 4
    cv.rect(x0 - 26, beam + 4, 3, pl, OUT); cv.vline(x0 - 25, beam + 4, pl, BRASS_OM[2])
    # brackets
    for bx in (x0 + 4, x0 + w - 12):
        cv.rect(bx, beam - 6, 8, 36, OUT); cv.rect(bx + 1, beam - 5, 6, 34, CAST_IRON[3]); cv.vline(bx + 1, beam - 5, 34, CAST_IRON[5])
        cv.hline(bx + 1, beam + 28, 6, CAST_IRON[1])
        for by_ in (beam - 3, beam + 14, beam + 24):
            cv.rect(bx + 3, by_, 2, 2, CAST_IRON[5]); cv.px(bx + 4, by_ + 1, CAST_IRON[1])
    # the gantry beam with rivets
    cv.rect(x0, beam, w, 8, OUT); cv.rect(x0 + 1, beam + 1, w - 2, 6, BRASS_OM[3]); cv.hline(x0 + 1, beam + 1, w - 2, BRASS_OM[5])
    cv.hline(x0 + 1, beam + 6, w - 2, BRASS_OM[1])
    for rx in range(x0 + 6, x0 + w - 4, 8):
        cv.px(rx, beam + 3, BRASS_OM[1]); cv.px(rx, beam + 2, BRASS_OM[5])
    # a riveted iron backplate behind the pistons, a hose to each cylinder
    ty_ = beam + 52
    py0, py1 = beam + 8, ty_ - 6
    cv.rect(x0 + 17, py0, w - 34, py1 - py0, OUT)
    cv.rect(x0 + 18, py0, w - 36, py1 - py0 - 1, CAST_IRON[2])
    cv.vline(x0 + 18, py0, py1 - py0 - 1, CAST_IRON[4]); cv.hline(x0 + 18, py1 - 2, w - 36, CAST_IRON[1])
    for xx in range(x0 + 18 + 18, x0 + w - 18, 18):
        cv.vline(xx, py0, py1 - py0 - 1, CAST_IRON[1]); cv.vline(xx + 1, py0, py1 - py0 - 1, CAST_IRON[3])
    for xx in range(x0 + 21, x0 + w - 18, 6):
        cv.px(xx, py1 - 4, CAST_IRON[4]); cv.px(xx, py0 + 2, CAST_IRON[4])
    for dx in (-54, 0, 54):
        hx = cx + dx + 6
        cv.line(hx, beam + 7, hx + 4, beam + 13, OUT); cv.line(hx + 1, beam + 7, hx + 5, beam + 13, "#3a3a44")
    # gauge on the left bracket
    gx, gy = x0 + 8, beam - 12
    cv.ellipse(gx - 6, gy - 6, 13, 13, OUT); cv.ellipse(gx - 5, gy - 5, 11, 11, BRASS_OM[3]); cv.ellipse(gx - 4, gy - 4, 9, 9, "#e8dcc0")
    cv.line(gx, gy, gx + 3, gy - 2, "#b82a26" if state != "damaged" else "#2a2a2a"); cv.px(gx, gy, OUT)
    # sign and lamp above the middle of the beam
    sx_, sy_ = cx, top + 12
    if state == "approved":
        pw = 76
        cv.rect(sx_ - pw // 2 - 1, sy_ - 9, pw + 2, 20, OUT); cv.rect(sx_ - pw // 2, sy_ - 8, pw, 18, "#0e1a14")
        cv.rect(sx_ - pw // 2 - 3, sy_ - 11, pw + 6, 24, C("#4aa868", 0.12))
        text(cv, "FINITE PLAN", sx_ - text_width("FINITE PLAN") // 2, sy_ - 9, "#8ad8a0")
        micro_text(cv, "APPROVED", sx_ - micro_width("APPROVED") // 2, sy_ + 3, "#4aa868")
    else:
        pw = 40
        cv.rect(sx_ - pw // 2 - 1, sy_ - 1, pw + 2, 11, OUT); cv.rect(sx_ - pw // 2, sy_, pw, 9, "#1a0e10")
        text(cv, "AUDIT", sx_ - text_width("AUDIT") // 2, sy_ - 1, "#7a2a26" if state == "active" else "#4a1a18")
        # caged lamp on top of the sign
        ly = sy_ - 10
        cv.rect(sx_ - 5, ly, 11, 9, OUT); cv.ellipse(sx_ - 4, ly + 1, 9, 9, "#5a1414")
        cv.ellipse(sx_ - 3, ly + 2, 6, 5, "#8a1e1e")
        for k in (-3, 0, 3):
            cv.vline(sx_ + k, ly, 9, CAST_IRON[4])
        cv.hline(sx_ - 5, ly + 4, 11, CAST_IRON[4])
        if state == "damaged":
            cv.line(sx_ - 3, ly + 2, sx_ + 2, ly + 7, "#e8dcc0"); cv.line(sx_ + 1, ly + 2, sx_ - 1, ly + 5, "#e8dcc0")
        pts["lamp"] = (sx_, ly + 4)
        pts["sign"] = (sx_ - pw // 2, sy_, pw, 9)
    # three stamps on pistons
    stamps = (("DENIED", RED_STAMP, -54), ("AUDIT", RED_STAMP, 0), ("APPROVED", GREEN_STAMP, 54))
    feet = []
    for k, (lab, ink, dx) in enumerate(stamps):
        px_ = cx + dx
        if state == "damaged" and k == 1:
            # the AUDIT arm wrenched loose: the cylinder hangs crooked, the stamp lies on the table
            cv.rect(px_ - 4, beam + 8, 9, 6, OUT); cv.rect(px_ - 3, beam + 9, 7, 4, BRASS_OM[2])
            cv.line(px_, beam + 13, px_ + 9, beam + 26, OUT); cv.line(px_ + 1, beam + 13, px_ + 10, beam + 26, "#9aa2ae")
            cv.px(px_ + 10, beam + 27, "#f2d690"); cv.px(px_ + 12, beam + 25, "#f2d690")
            feet.append(None)
            continue
        if state == "approved":
            low = 0
        else:
            low = lowered[k]
        feet.append(stamp_head(cv, px_, beam + 8, lab, ink, lowered=low))
    pts["stamps"] = [(cx + dx, beam + 8) for _, _, dx in stamps]
    # ink-pad table and forms
    ty = beam + 52
    cv.rect(x0 + 10, ty, w - 20, 5, OUT); cv.rect(x0 + 11, ty + 1, w - 22, 3, WALNUT[4]); cv.hline(x0 + 11, ty + 1, w - 22, WALNUT[6])
    for lx in (x0 + 14, x0 + w - 18):
        cv.rect(lx, ty + 5, 4, 14, OUT); cv.vline(lx + 1, ty + 5, 13, WALNUT[4])
    for k, (lab, ink, dx) in enumerate(stamps):
        px_ = cx + dx
        cv.rect(px_ - 9, ty - 3, 19, 3, OUT); cv.rect(px_ - 8, ty - 3, 17, 2, ink[1])
        for j in range(3):
            cv.hline(px_ - 13 + j, ty - 4 - j, 8, PAPER_TINTS[j])
    if state == "damaged":
        px_ = cx
        cv.rect(px_ + 6, ty - 8, 20, 8, OUT); cv.rect(px_ + 7, ty - 7, 18, 3, WALNUT[3]); cv.rect(px_ + 7, ty - 4, 18, 3, RED_STAMP[2])
        cv.rect(px_ - 6, ty - 3, 12, 3, C(RED_STAMP[2], 0.8))
        # the tag
        tx, tyy = cx - 40, beam + 16
        cv.line(x0 + 30, beam + 7, tx + 10, tyy, "#c8b892")
        tw_ = micro_width("REPAIRS") + 6
        cv.rect(tx - 1, tyy - 1, tw_ + 2, 16, OUT); cv.rect(tx, tyy, tw_, 14, "#efe2b8")
        micro_text(cv, "REPAIRS", tx + 3, tyy + 2, "#7a2a24"); micro_text(cv, "PENDING", tx + 3, tyy + 8, "#7a2a24")
    pts["table"] = ty
    pts["box"] = (x0 - 28, top, w + 56, ty + 20 - top)
    return pts


def card_cabinet(width=135, height=112, seed=0, ladder=True, label="A-L"):
    """A tall walnut cabinet of small card drawers with brass label holders and pulls, a moulded
    cornice, a plinth; a rolling library ladder leaning on it; a few drawers sticking out."""
    from lib_eng import micro_text, micro_width
    cv = Canvas(width + 10, height + 8, seed=seed)
    ox, base = 5, height + 5
    top = base - height
    rng = _rng(seed)
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    cv.rect(ox - 2, top, width + 4, 7, OUT)
    cv.rect(ox - 1, top + 1, width + 2, 5, WALNUT[5]); cv.hline(ox - 1, top + 1, width + 2, WALNUT[6]); cv.hline(ox - 1, top + 5, width + 2, WALNUT[2])
    lw = micro_width(label) + 6
    cv.rect(ox + width // 2 - lw // 2, top + 1, lw, 6, BRASS_OM[3]); micro_text(cv, label, ox + width // 2 - lw // 2 + 3, top + 1, "#2a1a10")
    cv.rect(ox, top + 7, width, base - top - 7, OUT)
    cv.rect(ox + 1, top + 7, width - 2, base - top - 13, WALNUT[3])
    cv.vline(ox + 1, top + 7, base - top - 13, WALNUT[5])
    dw, dh = 12, 9
    cols = (width - 8) // dw
    rows = (base - top - 22) // dh
    gx0 = ox + (width - cols * dw) // 2
    for r in range(rows):
        for c in range(cols):
            x_, y_ = gx0 + c * dw, top + 10 + r * dh
            out_ = rng.random() < 0.05
            cv.rect(x_, y_, dw - 1, dh - 1, WALNUT[1])
            cv.rect(x_ + (0 if not out_ else -1), y_ + (0 if not out_ else 1), dw - 2, dh - 2, WALNUT[4] if not out_ else WALNUT[5])
            cv.hline(x_, y_, dw - 2, WALNUT[5])
            cv.rect(x_ + 3, y_ + 2, 5, 3, BRASS_OM[2]); cv.rect(x_ + 4, y_ + 3, 3, 1, "#e8dcc0")
            cv.px(x_ + 5, y_ + 6, BRASS_OM[4])
    cv.rect(ox, base - 6, width, 6, OUT); cv.rect(ox + 1, base - 5, width - 2, 4, WALNUT[2]); cv.hline(ox + 1, base - 5, width - 2, WALNUT[4])
    if ladder:
        lx = ox + width - 26
        for d in (0, 13):
            cv.line(lx + d, top - 2, lx + d + 10, base - 2, OUT); cv.line(lx + d + 1, top - 2, lx + d + 11, base - 2, WALNUT[5])
        for k in range(1, 9):
            yy = top + k * (height // 9)
            xx = lx + int(10 * (yy - top) / height)
            cv.hline(xx + 1, yy, 13, WALNUT[6]); cv.hline(xx + 1, yy + 1, 13, OUT)
        cv.rect(lx + 8, base - 4, 4, 4, OUT); cv.rect(lx + 21, base - 4, 4, 4, OUT)
    return cv, ox + width // 2, base


def persian_rug(cv, x, y, w, h, pal=RUG_RED, seed=0):
    """A big worn carpet: a navy main border with gold boteh between gold guard lines, an oxblood
    field with a lattice of small lozenges, a navy medallion with a red heart and gold outline,
    navy corner spandrels; worn paler in the middle; fringes at both ends."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[0])
    cv.rect(x + 1, y + 1, w - 2, h - 2, pal[6])
    cv.rect(x + 2, y + 2, w - 4, h - 4, pal[4])
    b = 10                                                   # main border width
    for k in range(x + 7, x + w - 9, 9):
        for yy in (y + 4, y + h - 8):
            cv.rect(k, yy, 3, 3, pal[6]); cv.px(k + 1, yy + 1, pal[7]); cv.px(k + 3, yy + 2, pal[3])
    for k in range(y + 12, y + h - 12, 9):
        for xx in (x + 4, x + w - 7):
            cv.rect(xx, k, 3, 3, pal[6]); cv.px(xx + 1, k + 1, pal[7])
    cv.rect(x + b, y + b, w - 2 * b, h - 2 * b, pal[6])
    cv.rect(x + b + 1, y + b + 1, w - 2 * b - 2, h - 2 * b - 2, pal[1])
    fx0, fy0, fw, fh = x + b + 2, y + b + 2, w - 2 * b - 4, h - 2 * b - 4
    cv.rect(fx0, fy0, fw, fh, pal[2])
    # lattice of small lozenges over the field
    for j, yy in enumerate(range(fy0 + 5, fy0 + fh - 3, 10)):
        for xx in range(fx0 + 6 + (j % 2) * 8, fx0 + fw - 4, 16):
            cv.poly([(xx, yy - 2), (xx + 3, yy), (xx, yy + 2), (xx - 3, yy)], pal[3])
            cv.px(xx, yy, pal[6])
    cxr, cyr = x + w // 2, y + h // 2
    # corner spandrels
    for (qx, qy) in ((fx0, fy0), (fx0 + fw - 1, fy0), (fx0, fy0 + fh - 1), (fx0 + fw - 1, fy0 + fh - 1)):
        sx_ = 1 if qx < cxr else -1
        sy_ = 1 if qy < cyr else -1
        cv.poly([(qx, qy), (qx + sx_ * 30, qy), (qx, qy + sy_ * 18)], pal[6])
        cv.poly([(qx, qy), (qx + sx_ * 27, qy), (qx, qy + sy_ * 16)], pal[4])
        cv.px(qx + sx_ * 5, qy + sy_ * 3, pal[7])
    # the medallion
    mw, mh = w // 5, h // 4
    cv.poly([(cxr, cyr - mh - 2), (cxr + mw + 3, cyr), (cxr, cyr + mh + 2), (cxr - mw - 3, cyr)], pal[6])
    cv.poly([(cxr, cyr - mh), (cxr + mw, cyr), (cxr, cyr + mh), (cxr - mw, cyr)], pal[4])
    cv.poly([(cxr, cyr - mh + 6), (cxr + mw - 10, cyr), (cxr, cyr + mh - 6), (cxr - mw + 10, cyr)], pal[2])
    cv.poly([(cxr, cyr - mh // 3), (cxr + mw // 3, cyr), (cxr, cyr + mh // 3), (cxr - mw // 3, cyr)], pal[6])
    cv.poly([(cxr, cyr - mh // 3 + 2), (cxr + mw // 3 - 3, cyr), (cxr, cyr + mh // 3 - 2), (cxr - mw // 3 + 3, cyr)], pal[3])
    for d in (-1, 1):
        cv.rect(cxr + d * (mw + 6) - 1, cyr - 1, 3, 3, pal[6])
        cv.rect(cxr - 1, cyr + d * (mh + 5) - 1, 3, 3, pal[6])
    # wear: threadbare flecks
    for _ in range((w * h) // 90):
        px_, py_ = int(rng.integers(fx0 + 4, fx0 + fw - 4)), int(rng.integers(fy0 + 4, fy0 + fh - 4))
        cv.px(px_, py_, pal[3] if rng.random() < 0.7 else pal[1])
    for fx in range(x + 1, x + w - 1, 3):
        cv.vline(fx, y - 3, 3, "#c8b892"); cv.vline(fx, y + h, 3, "#c8b892")
