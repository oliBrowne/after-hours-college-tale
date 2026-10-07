"""Macky Auditorium's shared look for M01-M04 (the procession walk, the lobby, the cloakroom, the
orchestra pit) and their battle backdrops.

Everything paints at 1:1 game pixels against a 52px character. Macky is rough-faced Lyons
sandstone (rose and buff blocks with deep joints), smooth dressed sandstone for arches, sills and
quoins, red barrel-tile roofs, two square crenellated towers, Romanesque round arches, and Boston
ivy that turns crimson in autumn. Sections:
  palettes ........... MSTONE, DRESS, IVY, IVY_RED, BRASS, PLASTER_M, OAK_M, VELVET_M, NIGHT_M, DAWN_M
  stone .............. rough_ashlar, dressed_band, quoin_column, voussoirs, corbel_table, crenellation
  ivy ................ ivy
  facade ............. macky_doorway, macky_window, lancet_pair, macky_tower, macky_front
  sky ................ night_sky_m, dawn_sky_m, flatirons_m, treeline_m, stars_mask
  outdoor props ...... procession_lamp, long_bench, reserved_notice, tape_box, stencil_text
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, LEAF, MUM, AMBER, ground_shadow, shrub, grass_tuft
from facade import ROOF, FRAME, GLOW, DARKGLASS, roof_tiles
from surfaces import light_pool, LEAVES

INK = "#171a2b"
SHADOW = "#0d0b16"

# --- palettes ---------------------------------------------------------------------------------
# rough-faced Lyons sandstone, joint to sunlit face
MSTONE = ["#2a1c22", "#40292c", "#573634", "#6d4540", "#82554a", "#956353", "#a8735f", "#bb866e", "#cf9c80"]
# smooth dressed sandstone (voussoirs, jambs, sills, quoins, string courses)
DRESS = ["#4e3a3a", "#6e5248", "#8e6c5a", "#a8846a", "#bf9a7c", "#d4b292", "#e6caa8"]
IVY = ["#0f1712", "#16231a", "#1f3022", "#2a3f2a", "#375036", "#486443"]
IVY_RED = ["#3e1620", "#5a1e26", "#7a2a2c", "#9a3a30", "#b44e34", "#c86a3c"]
BRASS = ["#4a3018", "#7a5428", "#a87c38", "#d0a650", "#f0d48a"]
CU_GOLD = ["#5a4418", "#8a6a24", "#b8913a", "#d8b45a", "#f0d68a"]
NIGHT_M = ["#0e1026", "#141634", "#1a1c40", "#22224a", "#2c2852", "#382e5a", "#463462"]
DAWN_M = ["#4e5a8e", "#62679a", "#7a72a2", "#9478a2", "#b07e9c", "#c98a92", "#de9888", "#eaa882", "#f2bc86", "#f6d090"]


def _rng(seed):
    return np.random.default_rng(seed)


def hexmix(a, b, t):
    """mix() as a hex string (keeps palettes printable)."""
    c = mix(a, b, t)
    return "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in c[:3])


def grade(pal, mul, add=(0, 0, 0)):
    """Multiply/offset a palette (for night and dawn light on the same material)."""
    out = []
    for p in pal:
        c = C(p)
        out.append("#%02x%02x%02x" % tuple(int(round(min(1, max(0, c[i] * mul[i] + add[i])) * 255)) for i in range(3)))
    return out


# --- stone ------------------------------------------------------------------------------------
def rough_ashlar(cv, x, y, w, h, seed=0, pal=MSTONE, mask=None, courses=(6, 7, 7, 8), lit=0.0):
    """Rock-faced sandstone in courses: every block its own rose, buff or rust tone, a lit upper
    lip, a shadowed foot, a few knobs on the face and deep dark joints. mask (canvas-sized bool)
    limits where it paints; lit > 0 warms the faces (sunrise on the upper courses)."""
    rng = _rng(seed)
    tmp = Canvas(w, h, seed=seed)
    tmp.rect(0, 0, w, h, pal[1])
    yy = 0
    row = 0
    while yy < h:
        ch = int(rng.choice(courses))
        xx = -int(rng.integers(0, 12))
        while xx < w:
            bw = int(rng.integers(9, 23)) if ch < 8 else int(rng.integers(12, 26))
            x0, x1 = max(0, xx), min(w, xx + bw - 1)
            if x1 - x0 >= 1:
                r = rng.random()
                base = pal[int(rng.choice([4, 5, 5, 6, 6, 7]))]
                if r < 0.22:
                    base = hexmix(base, "#c8a070", 0.35)          # buff block
                elif r < 0.34:
                    base = hexmix(base, "#8a4030", 0.3)           # rusty block
                elif r < 0.42:
                    base = shade(base, -0.12)
                if lit:
                    base = hexmix(base, "#f2b07a", lit)
                tmp.rect(x0, yy, x1 - x0, ch - 1, base)
                tmp.hline(x0, yy, x1 - x0, shade(base, 0.12))
                tmp.vline(x0, yy, ch - 1, shade(base, 0.06))
                tmp.hline(x0, yy + ch - 2, x1 - x0, shade(base, -0.16))
                tmp.vline(x1 - 1, yy + 1, ch - 2, shade(base, -0.1))
                # rock-face knobs: a lit pixel over a dark one
                for _ in range(max(1, (x1 - x0) * ch // 22)):
                    kx = x0 + 1 + int(rng.integers(0, max(1, x1 - x0 - 2)))
                    ky = yy + 1 + int(rng.integers(0, max(1, ch - 3)))
                    tmp.px(kx, ky, shade(base, 0.09)); tmp.px(kx, ky + 1, shade(base, -0.1))
            xx += bw
        yy += ch
        row += 1
    if mask is None:
        cv.paste(tmp, x, y)
    else:
        sub = mask[max(0, y):y + h, max(0, x):x + w]
        reg = cv.a[max(0, y):y + h, max(0, x):x + w]
        src = tmp.a[max(0, -y):max(0, -y) + reg.shape[0], max(0, -x):max(0, -x) + reg.shape[1]]
        reg[sub[:src.shape[0], :src.shape[1]]] = src[sub[:src.shape[0], :src.shape[1]]]


def dressed_band(cv, x, y, w, h, pal=DRESS, joints=18, seed=0):
    """A smooth sandstone course (string course, sill band, plinth cap): lit top, shadow under."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[3])
    cv.hline(x, y, w, pal[5]); cv.hline(x, y + 1, w, pal[4])
    cv.hline(x, y + h - 1, w, pal[1])
    for jx in range(x + int(rng.integers(4, joints)), x + w - 2, joints + int(rng.integers(-4, 5))):
        cv.vline(jx, y + 1, h - 2, pal[2])
    cv.hline(x, y + h, w, C(SHADOW, 0.45))


def quoin_column(cv, x, y0, y1, side="left", pal=DRESS):
    """Smooth corner stones up a tower edge, long and short in turn."""
    for k, qy in enumerate(range(y0, y1, 8)):
        qh = min(7, y1 - qy)
        if qh <= 1:
            break
        qw = 12 if k % 2 == 0 else 7
        qx = x if side == "left" else x - qw
        cv.rect(qx, qy, qw, qh, pal[3]); cv.hline(qx, qy, qw, pal[5]); cv.hline(qx, qy + qh - 1, qw, pal[1])
        if side == "left":
            cv.vline(qx, qy, qh, pal[4])
        else:
            cv.vline(qx + qw - 1, qy, qh, pal[2])


def voussoirs(cv, cx, spring, r, thick=6, pal=DRESS, n=11, key=True):
    """A ring of wedge stones round a semicircular arch springing at row `spring` (centre cx)."""
    for yy in range(spring - r - thick - 1, spring + 1):
        for xx in range(int(cx - r - thick - 1), int(cx + r + thick + 2)):
            dx, dy = xx - cx + 0.5, yy - spring + 0.5
            d = np.hypot(dx, dy)
            if r < d <= r + thick and dy <= 0.5:
                a = np.arctan2(-dy, dx)                    # 0 right .. pi left
                k = int(a / np.pi * n)
                c = pal[4] if k % 2 else pal[3]
                if d > r + thick - 1.2:
                    c = pal[1]
                elif d < r + 1.3:
                    c = shade(c, -0.12)
                elif abs(a / np.pi * n - round(a / np.pi * n)) < 0.08:
                    c = pal[2]
                cv.px(xx, yy, c)
    if key:
        kx = int(round(cx - 0.5))
        cv.rect(kx - 3, spring - r - thick - 2, 7, thick + 3, pal[5]); cv.hline(kx - 3, spring - r - thick - 2, 7, pal[6])
        cv.vline(kx + 3, spring - r - thick - 2, thick + 3, pal[2])


def corbel_table(cv, x, y, w, pal=DRESS, step=8):
    """A row of little round-headed corbels under a cornice or parapet (Romanesque)."""
    cv.rect(x, y, w, 3, pal[3]); cv.hline(x, y, w, pal[5]); cv.hline(x, y + 2, w, pal[1])
    for cx in range(x + 2, x + w - 3, step):
        cv.rect(cx, y + 3, 3, 4, pal[3]); cv.px(cx, y + 3, pal[5]); cv.vline(cx + 2, y + 3, 4, pal[1])
        cv.hline(cx + 3, y + 5, step - 3, C(SHADOW, 0.35))
        cv.px(cx + 3, y + 4, C(SHADOW, 0.25)); cv.px(cx + step - 1, y + 4, C(SHADOW, 0.25))
    cv.hline(x, y + 7, w, C(SHADOW, 0.3))


def crenellation(cv, x, top, w, pal=MSTONE, dpal=DRESS, merlon=9, gap=6, h=9, lit=0.0):
    """A battlemented parapet: merlons with dressed caps, the sky showing through the crenels
    (the crenels are left untouched so whatever was painted behind shows)."""
    xx = x
    k = 0
    while xx < x + w:
        mw = min(merlon, x + w - xx)
        base_c = hexmix(pal[5], "#f2b07a", lit) if lit else pal[5]
        cv.rect(xx, top + 2, mw, h, base_c)
        cv.vline(xx, top + 2, h, shade(base_c, 0.1)); cv.vline(xx + mw - 1, top + 2, h, shade(base_c, -0.16))
        cv.hline(xx, top + 2 + h // 2, mw, pal[2])
        cap = hexmix(dpal[4], "#f6c08a", lit) if lit else dpal[4]
        cv.rect(xx - 1, top, mw + 2, 3, cap); cv.hline(xx - 1, top, mw + 2, dpal[6] if lit else dpal[5]); cv.hline(xx - 1, top + 2, mw + 2, dpal[1])
        xx += mw + gap
        k += 1
    cv.rect(x - 1, top + 2 + h, w + 2, 3, dpal[3]); cv.hline(x - 1, top + 2 + h, w + 2, dpal[5]); cv.hline(x - 1, top + 4 + h, w + 2, dpal[1])


# --- ivy --------------------------------------------------------------------------------------
def _leaf(cv, x, y, c, dark, light):
    """One ivy leaf: a lit tip, two mid pixels, a dark underside either side."""
    cv.px(x, y, c); cv.px(x + 1, y, c); cv.px(x, y - 1, light); cv.px(x + 1, y + 1, dark); cv.px(x - 1, y + 1, dark)


def _value_noise(w, h, cell, rng):
    gw, gh = w // cell + 2, h // cell + 2
    g = rng.random((gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / float(cell)
    x0, y0 = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def ivy(cv, x, y, w, h, seed=0, stems=10, reach=(0.4, 1.0), autumn=0.3, avoid=None, spread=13, density=1.0, lit=0.0):
    """Boston ivy climbing from the foot of a wall (row y + h) toward the top of the box: each
    stem raises a flame-shaped mass that is widest a third of the way up and frays into tendrils
    at its tip; the mass is filled with overlapping leaves lit from the upper left, and turns
    crimson and wine in patches (autumn = share of red). avoid (canvas-sized bool) keeps windows
    and doors clear apart from a leafy fringe."""
    rng = _rng(seed)
    pad = int(spread * 2)
    x, w = x - pad, w + 2 * pad                               # masses may spread past the stem box
    M = np.zeros((h, w), bool)
    ys = np.arange(h)[:, None]
    xs = np.arange(w)[None, :]
    tendrils = []
    for _ in range(stems):
        sx = rng.uniform(pad, w - pad)
        hs = h * rng.uniform(*reach)
        sp = spread * rng.uniform(0.6, 1.4)
        lean = rng.normal(0, 0.12)
        t = (h - 1 - ys) / max(1.0, hs)                       # 0 at the foot, 1 at the tip
        wob = np.sin(ys / rng.uniform(5, 9) + rng.uniform(0, 6)) * 2.0
        half = sp * (0.35 + 1.1 * np.sin(np.pi * np.clip(t, 0, 1) ** 0.6)) * (1 - np.clip(t, 0, 1) ** 1.8)
        half = half * (0.75 + 0.5 * np.sin(ys / rng.uniform(3, 6) + rng.uniform(0, 6)) ** 2)
        cxs = sx + lean * (h - 1 - ys) + wob
        M |= (np.abs(xs - cxs) <= half) & (t <= 1) & (t >= 0)
        tip_y = int(h - 1 - hs)
        for _ in range(int(rng.integers(1, 4))):
            tendrils.append((sx + lean * hs + rng.normal(0, sp * 0.5), tip_y + int(rng.integers(0, 8)), int(rng.integers(6, 16))))
    # fray the outline: knock out a ragged rim
    from scipy import ndimage
    rim = M & ~ndimage.binary_erosion(M, iterations=2)
    M &= ~(rim & (rng.random(M.shape) < 0.45))
    canvas_mask = np.zeros((cv.h, cv.w), bool)
    yy0, xx0 = max(0, y), max(0, x)
    sub = M[yy0 - y:min(h, cv.h - y), xx0 - x:min(w, cv.w - x)]
    canvas_mask[yy0:yy0 + sub.shape[0], xx0:xx0 + sub.shape[1]] = sub
    if avoid is not None:
        fringe = avoid & ~ndimage.binary_erosion(avoid, iterations=2)
        canvas_mask &= ~avoid | (fringe & (rng.random(avoid.shape) < 0.35))
    red_field = _value_noise(cv.w, cv.h, 11, rng)
    green = IVY if not lit else [hexmix(c, "#e0a060", lit * 0.45) for c in IVY]
    red = IVY_RED if not lit else [hexmix(c, "#f0a060", lit * 0.35) for c in IVY_RED]
    py, px_ = np.where(canvas_mask)
    # shadowed underlayer so gaps between leaves read as depth, not wall
    inner = ndimage.binary_erosion(canvas_mask, iterations=1)
    for yy, xx in zip(*np.where(inner)):
        if rng.random() < 0.8:
            cv.px(xx, yy, green[1])
    order = rng.permutation(len(py))
    n = int(len(py) * 0.36 * density)
    for i in order[:n]:
        yy, xx = int(py[i]), int(px_[i])
        is_red = red_field[yy, xx] < autumn * 0.9 + 0.05 * rng.random()
        pal = red if is_red else green
        # light from the upper left: leaves near the mass's upper-left edges are brighter
        up = canvas_mask[max(0, yy - 3), xx] and canvas_mask[yy, max(0, xx - 3)]
        if is_red:
            tone = int(rng.choice([1, 2, 2, 3])) if up else int(rng.choice([2, 3, 3, 4]))
        else:
            tone = int(rng.choice([2, 3, 3, 4])) if up else int(rng.choice([3, 4, 4, 5]))
        tone = min(len(pal) - 1, tone)
        _leaf(cv, xx, yy, pal[tone], pal[max(0, tone - 2)], pal[min(len(pal) - 1, tone + 1)])
    for (tx, ty, ln) in tendrils:
        cx_, cy_ = tx + x, ty + y
        for k in range(ln):
            cx_ += rng.normal(0, 0.6)
            ix, iy = int(round(cx_)), int(cy_ - k)
            if 0 <= ix < cv.w and 0 <= iy < cv.h and (avoid is None or not avoid[iy, ix]):
                cv.px(ix, iy, "#2a2018")
                if k % 3 == 1:
                    pal = red if rng.random() < autumn else green
                    _leaf(cv, ix + int(rng.choice([-1, 1])), iy, pal[3], pal[1], pal[4])


# --- facade -----------------------------------------------------------------------------------
def _arch_mask(cv, cx, spring, r, bottom, x0=None, x1=None):
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    left, right = cx - r, cx + r
    m = (xs >= left) & (xs < right) & (ys >= spring) & (ys < bottom)
    m |= ((xs - cx + 0.5) ** 2 + (ys - spring + 0.5) ** 2 <= r * r) & (ys < spring)
    return m


def macky_doorway(cv, cx, bottom, w=36, h=68, open_=False, lit=True, dawn=False, seed=0):
    """A round-arched entrance in a deep sandstone reveal: voussoir ring, dressed jambs, a fanlight
    with radiating glazing bars, and either two oak leaves with iron straps (closed) or the leaves
    swung in on a warm lobby (open)."""
    rng = _rng(seed)
    r = w // 2
    spring = bottom - (h - r)
    # jambs and voussoirs
    for side in (cx - r - 6, cx + r):
        cv.rect(side, spring, 6, bottom - spring, DRESS[3])
        cv.vline(side, spring, bottom - spring, DRESS[5] if side < cx else DRESS[2])
        for yy in range(spring + 6, bottom, 8):
            cv.hline(side, yy, 6, DRESS[1])
    voussoirs(cv, cx, spring, r, thick=6, n=9)
    # the reveal (wall thickness) in shadow
    m = _arch_mask(cv, cx, spring, r, bottom)
    cv.fill_mask(m, "#1c1418")
    inner = _arch_mask(cv, cx, spring + 1, r - 3, bottom)
    glow = GLOW if lit else DARKGLASS
    if dawn:
        glow = ["#6a4430", "#9a6a44", "#c8945c", "#e2b47a", "#f2d29a"]
    if open_:
        ys, xs = np.where(inner)
        for yy in np.unique(ys):
            t = (yy - (spring - r)) / max(1, bottom - (spring - r))
            c = mix(glow[3], glow[1], t * 0.9)
            row = inner[yy]
            cv.a[yy, row] = c
        # lobby glimpsed: floor, a far door, a hanging lantern
        cv.rect(cx - r + 3, bottom - 10, w - 6, 10, glow[1]); cv.hline(cx - r + 3, bottom - 10, w - 6, glow[2])
        for yy in range(bottom - 8, bottom, 3):
            cv.hline(cx - r + 3, yy, w - 6, shade(glow[1], -0.12))
        cv.rect(cx - 6, bottom - 34, 12, 24, shade(glow[1], -0.25)); cv.rect(cx - 5, bottom - 33, 10, 22, glow[2])
        cv.vline(cx, spring - r + 4, 10, FRAME); cv.rect(cx - 2, spring - r + 14, 5, 6, glow[4]); cv.rect(cx - 3, spring - r + 13, 7, 2, FRAME)
        for (lx, dw) in [(cx - r + 2, 7), (cx + r - 9, 7)]:
            cv.rect(lx, spring - 2, dw, bottom - spring + 2, "#4a2b24")
            cv.vline(lx + (dw - 1 if lx < cx else 0), spring - 2, bottom - spring + 2, "#2c1a1a")
            cv.rect(lx + 1, spring + 4, dw - 2, 2, IRON[2]); cv.rect(lx + 1, bottom - 14, dw - 2, 2, IRON[2])
    else:
        # door leaves: vertical oak boards, iron straps and studs, ring pulls
        cv.rect(cx - r + 3, spring, w - 6, bottom - spring, WOOD[2])
        for bx in range(cx - r + 3, cx + r - 3, 4):
            tone = WOOD[3] if (bx // 4) % 2 else WOOD[2]
            cv.rect(bx, spring, 4, bottom - spring, tone)
            cv.vline(bx, spring, bottom - spring, WOOD[1])
            for _ in range((bottom - spring) // 7):
                gy = spring + int(rng.integers(0, bottom - spring - 3))
                cv.vline(bx + 1 + int(rng.integers(0, 2)), gy, int(rng.integers(2, 5)), shade(tone, -0.12))
        cv.vline(cx - 1, spring, bottom - spring, WOOD[0]); cv.vline(cx, spring, bottom - spring, WOOD[1])
        for sy in (spring + 6, (spring + bottom) // 2, bottom - 9):
            cv.rect(cx - r + 3, sy, w - 6, 2, IRON[1]); cv.hline(cx - r + 3, sy, w - 6, IRON[3])
            for k in range(cx - r + 5, cx + r - 4, 5):
                cv.px(k, sy, IRON[4])
        for hx in (cx - 4, cx + 3):
            cv.ellipse(hx - 2, (spring + bottom) // 2 + 3, 4, 4, IRON[3]); cv.px(hx - 1, (spring + bottom) // 2 + 4, IRON[1])
        # fanlight
        fan = _arch_mask(cv, cx, spring, r - 3, spring)
        fan &= ~_arch_mask(cv, cx, spring, 0, spring)
        ys, xs = np.where(fan)
        for yy in np.unique(ys):
            t = (yy - (spring - r)) / max(1, r)
            cv.a[yy, fan[yy]] = C(glow[3] if t < 0.45 else glow[2])
        for k in range(1, 6):
            a = np.pi * k / 6
            cv.line(cx - 0.5, spring - 1, int(round(cx - 0.5 + np.cos(a) * (r - 3))), int(round(spring - 1 - np.sin(a) * (r - 3))), FRAME)
        cv.ellipse(cx - 4, spring - 4, 8, 8, FRAME); cv.ellipse(cx - 2, spring - 2, 4, 4, glow[4])
        cv.rect(cx - r + 3, spring - 1, w - 6, 2, WOOD[1])
    # threshold slab
    cv.rect(cx - r - 7, bottom - 2, w + 14, 2, DRESS[4]); cv.hline(cx - r - 7, bottom - 2, w + 14, DRESS[5])
    return (cx, spring - r // 2)


def macky_window(cv, cx, top, w, h, lit=True, dawn=False, seed=0, mullion=True, surround=6):
    """A tall round-headed window: voussoir head, dressed jambs, a stone mullion splitting it
    into two lights with a roundel in the head, leaded panes, warm hall light (or dawn sky
    reflected when unlit). (cx, top) is the crown of the arch."""
    r = w // 2
    spring = top + r
    bottom = top + h
    for side in (cx - r - 4, cx + r):
        cv.rect(side, spring, 4, bottom - spring, DRESS[3]); cv.vline(side, spring, bottom - spring, DRESS[5] if side < cx else DRESS[2])
        for yy in range(spring + 5, bottom, 7):
            cv.hline(side, yy, 4, DRESS[1])
    voussoirs(cv, cx, spring, r, thick=4, n=7, key=False)
    m = _arch_mask(cv, cx, spring, r, bottom)
    cv.fill_mask(m, FRAME)
    glass = _arch_mask(cv, cx, spring, r - 1, bottom - 1)
    if lit:
        pal = GLOW
    elif dawn:
        pal = ["#5a5a7e", "#7a7898", "#a08aa6", "#d0a0a0", "#f0c4a8"]
    else:
        pal = DARKGLASS + ["#8a96c8"]
    ys, xs = np.where(glass)
    for yy in np.unique(ys):
        t = (yy - top) / max(1, h)
        if lit:
            c = pal[3] if t < 0.3 else pal[2] if t < 0.7 else pal[1]
        elif dawn:
            c = pal[4] if t < 0.25 else pal[3] if t < 0.5 else pal[2] if t < 0.8 else pal[1]
        else:
            c = pal[2] if t < 0.3 else pal[1] if t < 0.7 else pal[0]
        cv.a[yy, glass[yy]] = C(c)
    if lit:
        # the hall's chandelier glimpsed through the glass
        cv.rect(cx - 3, spring + 3, 7, 2, GLOW[4]); cv.vline(cx, top + 2, spring + 3 - top - 2, shade(GLOW[1], -0.2))
    # leading: diagonal quarries
    for yy in range(top, bottom):
        for xx in range(cx - r, cx + r):
            if glass[yy, xx] and ((xx + yy) % 5 == 0 or (xx - yy) % 5 == 0):
                cv.px(xx, yy, mix(cv.a[yy, xx], C(FRAME), 0.55))
    if mullion and w >= 14:
        cv.rect(cx - 1, spring + 2, 2, bottom - spring - 2, DRESS[3]); cv.vline(cx - 1, spring + 2, bottom - spring - 2, DRESS[4])
        cv.ellipse(cx - 3, spring - 4, 7, 7, DRESS[3]); cv.ellipse(cx - 2, spring - 3, 5, 5, pal[4] if lit else pal[3])
    if not lit:
        cv.line(cx - r + 2, bottom - 4, cx - 1, spring + 4, C("#c8d0f0", 0.25))
    cv.rect(cx - r - 5, bottom, w + 10, 3, DRESS[4]); cv.hline(cx - r - 5, bottom, w + 10, DRESS[6]); cv.hline(cx - r - 5, bottom + 2, w + 10, DRESS[1])
    cv.hline(cx - r - 5, bottom + 3, w + 10, C(SHADOW, 0.45))


def lancet_pair(cv, cx, top, h, lit=True, dawn=False, louvre=False):
    """Two narrow round-headed openings under one hood (tower windows / belfry louvres)."""
    for dx in (-5, 5):
        x = cx + dx
        cv.rect(x - 4, top + 3, 8, h - 3, DRESS[3]); cv.ellipse(x - 4, top - 1, 8, 8, DRESS[3])
        cv.vline(x - 4, top + 3, h - 3, DRESS[5])
        cv.rect(x - 2, top + 3, 4, h - 4, FRAME); cv.ellipse(x - 2, top + 1, 4, 4, FRAME)
        if louvre:
            for yy in range(top + 4, top + h - 1, 2):
                cv.hline(x - 2, yy, 4, "#3a2a2a" if not dawn else "#5a4440")
        elif lit:
            cv.rect(x - 1, top + 3, 2, h - 6, GLOW[2]); cv.px(x - 1, top + 3, GLOW[4])
        else:
            cv.rect(x - 1, top + 3, 2, h - 6, "#e8b08c" if dawn else DARKGLASS[1])
    cv.ellipse(cx - 11, top - 4, 23, 12, C(DRESS[4], 0.0))
    cv.rect(cx - 10, top + h - 1, 21, 2, DRESS[4]); cv.hline(cx - 10, top + h - 1, 21, DRESS[6])


def macky_tower(cv, x0, w, base, top, seed=0, dawn=False, lit_windows=True, levels=None, sun=0.0):
    """One of the twin towers from its plinth (row base) to its battlement top (row top; may be
    above the canvas): rough ashlar, smooth quoins, string courses, a lit arched window low down,
    paired lancets above, the belfry with louvred openings, a corbel table and crenellations.
    sun > 0 warms the upper part (first light at dawn). Returns glow points for twinkle layers."""
    pts = []
    H_ = base - top
    rough_ashlar(cv, x0, top + 12, w, H_ - 12, seed=seed)
    if sun:
        # sunrise catches the upper half of the tower: warm the stone above the line
        lim = top + int(H_ * 0.48)
        y0 = max(0, top)
        reg = cv.a[y0:max(y0, lim), max(0, x0):x0 + w]
        reg[..., :3] = reg[..., :3] * (1 - sun) + (reg[..., :3] * 0.55 + np.array(C("#f6b47a")[:3]) * 0.45) * sun
    quoin_column(cv, x0, top + 14, base - 8, "left")
    quoin_column(cv, x0 + w, top + 14, base - 8, "right")
    cx = x0 + w // 2
    # plinth
    cv.rect(x0 - 2, base - 9, w + 4, 9, MSTONE[4])
    rough_ashlar(cv, x0 - 2, base - 8, w + 4, 8, seed=seed + 7, courses=(8,))
    dressed_band(cv, x0 - 3, base - 11, w + 6, 3)
    # string courses and windows by level (rows measured up from the base)
    levels = levels or {"low": 66, "mid": 132, "belfry": H_ - 46}
    dressed_band(cv, x0 - 1, base - 80, w + 2, 3, seed=seed + 1)
    dressed_band(cv, x0 - 1, base - 142, w + 2, 3, seed=seed + 2)
    macky_window(cv, cx, base - 70, 16, 46, lit=lit_windows and not dawn, dawn=dawn, seed=seed, mullion=False)
    pts.append((cx, base - 52))
    lancet_pair(cv, cx, base - 128, 34, lit=lit_windows and not dawn, dawn=dawn)
    pts.append((cx - 5, base - 112)); pts.append((cx + 5, base - 112))
    if H_ > 170:
        by = top + 24
        lancet_pair(cv, cx - 14, by, 28, louvre=True, dawn=dawn)
        lancet_pair(cv, cx + 14, by, 28, louvre=True, dawn=dawn)
        dressed_band(cv, x0 - 1, by + 30, w + 2, 3, seed=seed + 3)
        corbel_table(cv, x0 - 2, top + 13, w + 4)
        crenellation(cv, x0 - 2, top - 2, w + 4, lit=0.35 if sun else 0.0)
    # a deep shadow line where the tower stands proud of the wall behind
    return pts


def macky_front(cv, cx, base, tower_top=-40, wing_eave=36, gable=True, dawn=False, seed=0, door_open=True):
    """The east front at character scale, centred on the middle door (cx) with its sill on row
    `base`: the gabled entrance block with three round-arched doors, the carved name band and three
    tall hall windows; the twin towers either side (to row tower_top); lower wings beyond.
    Returns (lights, masks) where lights are window/lantern points and masks has 'building'."""
    rng = _rng(seed)
    lights = []
    TW = 92            # tower width
    BW = 98            # half width of the entrance block
    WW = 100           # wing width
    lt0, rt0 = cx - BW - TW, cx + BW
    # wings: two storeys, hipped tile roof
    for wx0 in (lt0 - WW, rt0 + TW):
        eave = base - 104
        roof_tiles(cv, wx0 - 4, eave - 14, WW + 8, 12, seed=wx0)
        cv.poly([(wx0 - 5, eave - 14), (wx0 + 6, eave - 22), (wx0 + WW - 6, eave - 22), (wx0 + WW + 5, eave - 14)], ROOF[2])
        cv.hline(wx0 + 6, eave - 22, WW - 12, ROOF[4])
        for tx in range(wx0 - 2, wx0 + WW + 2, 4):
            cv.vline(tx, eave - 21, 7, ROOF[1])
        rough_ashlar(cv, wx0, eave, WW, base - eave, seed=wx0 + 3)
        corbel_table(cv, wx0 - 2, eave, WW + 4)
        dressed_band(cv, wx0, base - 50, WW, 3, seed=wx0)
        for k, wx in enumerate(range(wx0 + 18, wx0 + WW - 8, 32)):
            on = rng.random() < 0.7 and not dawn
            macky_window(cv, wx, base - 44, 14, 38, lit=on, dawn=dawn, seed=k, mullion=False)
            if on:
                lights.append((wx, base - 26))
            on2 = rng.random() < 0.5 and not dawn
            macky_window(cv, wx, eave + 16, 12, 28, lit=on2, dawn=dawn, seed=k + 5, mullion=False)
            if on2:
                lights.append((wx, eave + 28))
        cv.rect(wx0 - 2, base - 8, WW + 4, 8, MSTONE[3]); rough_ashlar(cv, wx0 - 2, base - 7, WW + 4, 7, seed=wx0 + 9, courses=(7,))
    # entrance block
    eave = base - 138
    if gable:
        peak = eave - 40
        cv.poly([(cx - BW - 4, eave + 1), (cx, peak), (cx + BW + 4, eave + 1)], ROOF[1])
        for k in range(cx - BW, cx + BW, 4):
            hgt = int((BW + 4 - abs(k - cx)) * 40 / (BW + 4))
            cv.vline(k + 1, eave - hgt + 1, hgt, ROOF[3]); cv.vline(k + 2, eave - hgt + 1, hgt, ROOF[4]); cv.vline(k + 3, eave - hgt + 1, hgt, ROOF[0])
        cv.line(cx - BW - 4, eave, cx, peak, DRESS[4]); cv.line(cx, peak, cx + BW + 4, eave, DRESS[4])
        cv.line(cx - BW - 4, eave + 1, cx, peak + 1, DRESS[2]); cv.line(cx, peak + 1, cx + BW + 4, eave + 1, DRESS[2])
    rough_ashlar(cv, cx - BW, eave, 2 * BW, base - eave, seed=seed + 11)
    corbel_table(cv, cx - BW - 2, eave, 2 * BW + 4)
    # three hall windows
    for k, dx in enumerate((-58, 0, 58)):
        macky_window(cv, cx + dx, base - 128, 24, 34, lit=not dawn, dawn=dawn, seed=k + 20)
        if not dawn:
            lights.append((cx + dx, base - 108))
    # name band
    band_y = base - 89
    dressed_band(cv, cx - BW, band_y, 2 * BW, 11, seed=seed + 4)
    label = "MACKY AUDITORIUM"
    tx = cx - text_width(label) // 2
    text(cv, label, tx + 1, band_y + 2, DRESS[5])
    text(cv, label, tx, band_y + 1, DRESS[0])
    # plinth
    cv.rect(cx - BW, base - 8, 2 * BW, 8, MSTONE[3]); rough_ashlar(cv, cx - BW, base - 7, 2 * BW, 7, seed=seed + 13, courses=(7,))
    dressed_band(cv, cx - BW, base - 10, 2 * BW, 3, seed=seed + 5)
    # the three doors and lanterns between them
    for k, dx in enumerate((-58, 0, 58)):
        macky_doorway(cv, cx + dx, base, 36, 68, open_=(dx == 0 and door_open), lit=True, dawn=dawn, seed=k)
    for dx in (-29, 29):
        lx, ly = cx + dx, base - 50
        cv.rect(lx - 1, ly + 10, 3, 3, FRAME); cv.rect(lx - 3, ly, 7, 10, FRAME)
        cv.rect(lx - 2, ly + 2, 5, 6, GLOW[3] if not dawn else "#c8a070"); cv.rect(lx - 1, ly + 3, 3, 3, GLOW[4] if not dawn else "#e0c090")
        cv.poly([(lx - 4, ly + 1), (lx, ly - 3), (lx + 4, ly + 1)], FRAME); cv.rect(lx - 1, ly - 5, 3, 2, FRAME)
        lights.append((lx, ly + 5))
    # towers (stand slightly proud: a shadow line on the block and the wings)
    for tx0, sd in ((lt0, 1), (rt0, -1)):
        lights += macky_tower(cv, tx0, TW, base, tower_top, seed=tx0, dawn=dawn, sun=0.5 if dawn else 0.0)
        edge = tx0 + TW if sd > 0 else tx0 - 2
        cv.rect(edge, tower_top if tower_top > 0 else 0, 2, base - max(0, tower_top), C(SHADOW, 0.35))
    # ivy: up the towers, round the doors' outer edges, along the wings
    avoid = np.zeros((cv.h, cv.w), bool)
    for dx in (-58, 0, 58):
        avoid[:, cx + dx - 26:cx + dx + 26] |= (np.arange(cv.h)[:, None] > base - 80)
    for tx0 in (lt0, rt0):
        tcx = tx0 + TW // 2
        avoid[max(0, base - 74):base - 20, tcx - 12:tcx + 12] = True
        avoid[max(0, base - 132):base - 92, tcx - 13:tcx + 13] = True
    for (ix, iw, st, reach, sp, sd) in [(lt0 - 12, 40, 6, (0.55, 1.0), 10, 1), (lt0 + 58, 38, 4, (0.3, 0.75), 9, 2),
                                        (rt0 + TW - 28, 40, 6, (0.5, 1.0), 10, 3), (rt0 - 4, 30, 3, (0.25, 0.6), 8, 4),
                                        (lt0 - WW + 4, 30, 3, (0.3, 0.7), 8, 5), (rt0 + TW + WW - 34, 30, 3, (0.4, 0.8), 8, 6)]:
        ivy(cv, ix, max(0, base - 190), iw, min(190, base) - 6, seed=seed * 10 + sd, stems=st, reach=reach, autumn=0.35, avoid=avoid,
            spread=sp, lit=0.25 if dawn else 0.0)
    return lights, {"left_tower": (lt0, lt0 + TW), "right_tower": (rt0, rt0 + TW), "block": (cx - BW, cx + BW),
                    "wings": ((lt0 - WW, lt0), (rt0 + TW, rt0 + TW + WW))}


# --- sky --------------------------------------------------------------------------------------
def night_sky_m(cv, x, y, w, h, seed=0, stars=120, star_h=None, pal=NIGHT_M):
    """The last hour before dawn: stepped indigo bands, deepest overhead, a faint violet at the
    horizon, stars mostly high. Returns star points (some of them for a twinkle layer)."""
    rng = _rng(seed)
    prev = -1
    for yy in range(y, y + h):
        t = (yy - y) / max(1, h - 1)
        k = min(len(pal) - 1, int(t ** 0.85 * len(pal)))
        cv.hline(x, yy, w, pal[k])
        if k != prev and prev >= 0:
            # a ragged join: the band above reaches down a pixel here and there
            for xx in range(x, x + w, 3):
                if rng.random() < 0.4:
                    cv.rect(xx, yy, int(rng.integers(1, 4)), 1, pal[prev])
        prev = k
    pts = []
    for _ in range(stars):
        sx = x + int(rng.integers(0, w))
        sy = y + int(min(h - 2, abs(rng.normal(0, (star_h or h * 0.6) * 0.6))))
        c = "#d8d4f0" if rng.random() < 0.6 else "#f2d8a0"
        cv.px(sx, sy, c)
        if rng.random() < 0.08:
            cv.px(sx - 1, sy, C(c, 0.4)); cv.px(sx + 1, sy, C(c, 0.4)); cv.px(sx, sy - 1, C(c, 0.4)); cv.px(sx, sy + 1, C(c, 0.4))
        pts.append((sx, sy))
    return pts


def dawn_sky_m(cv, x, y, w, h, seed=0, sun_x=None, pal=DAWN_M):
    """Sunrise: soft blue overhead through lilac and rose to a peach and gold band at the horizon
    (row y + h), ragged band joins like the painted skies, long cloud streaks lit gold and pink
    from below; a pale morning star. sun_x puts a brighter glow low in the sky there."""
    rng = _rng(seed)
    n = len(pal)
    prev = -1
    for yy in range(y, y + h):
        t = (yy - y) / max(1, h - 1)
        k = min(n - 1, int(t ** 1.35 * n))
        cv.hline(x, yy, w, pal[k])
        if k != prev and prev >= 0:
            for xx in range(x, x + w, 3):
                if rng.random() < 0.4:
                    cv.rect(xx, yy, int(rng.integers(1, 5)), 1, pal[prev])
        prev = k
    if sun_x is not None:
        for (rx, ry, a, c) in [(150, 44, 0.12, "#f8d8a0"), (100, 30, 0.14, "#fbe2b0"), (60, 20, 0.18, "#fdeac0"), (30, 11, 0.22, "#fff2d0")]:
            cv.ellipse(sun_x - rx, y + h - ry, rx * 2, ry * 2, C(c, a))
    cv.px(x + int(w * 0.18), y + int(h * 0.12), "#f6f2ff")


def dawn_clouds(cv, x, y, w, h, seed=0, count=8, warm=1.0):
    """Long flat streaks of cloud lit from below by the sun about to rise."""
    rng = _rng(seed)
    for _ in range(count):
        cx, cy = x + int(rng.integers(-40, w)), y + int(rng.integers(0, h))
        L = int(rng.integers(40, 130))
        t = (cy - y) / max(1, h)
        body = hexmix("#7a6a96", "#b07a90", t)
        rim = hexmix("#e8a090", "#f8d098", t * warm)
        for k in range(3):
            ll = L - k * 24
            if ll < 10:
                break
            xx = cx + k * 11 + int(rng.integers(0, 6))
            cv.hline(xx, cy + k, ll, body)
            cv.hline(xx + 2, cy + k + 1, max(2, ll - 6), rim)
        cv.hline(cx + 4, cy - 1, max(2, L // 2), hexmix(body, "#a2a0c8", 0.4))


def flatirons_m(cv, x0, x1, base, seed=0, dawn=False, tall=1.0):
    """The Flatirons on the western horizon: Green Mountain's dark forested bulk, three tilted
    sandstone slabs in front with ribbed east faces and wooded gullies. At dawn the slabs catch the
    first sun (alpenglow) while the forest stays in shadow."""
    rng = _rng(seed)
    if dawn:
        mass, gully, slab, face, rib, crest = "#4a3a5a", "#2e2a40", "#a8606a", "#d07a6a", "#e8a07a", "#f6c08a"
        forest = ["#2a2c3a", "#34364a"]
    else:
        mass, gully, slab, face, rib, crest = "#1c1a34", "#121226", "#2a2644", "#34304f", "#433a5c", "#56486c"
        forest = ["#141626", "#1a1c2e"]
    span = x1 - x0
    ridge = []
    for x in range(x0, x1 + 1):
        t = (x - x0) / span
        hgt = (54 + 12 * np.sin(t * np.pi * 0.9 + 0.3) - 10 * t) * tall
        hgt *= min(1.0, (1 - t) / 0.2) ** 0.8 if t > 0.8 else 1.0
        ridge.append(int(base - hgt + rng.integers(0, 2)))
    for i, x in enumerate(range(x0, x1 + 1)):
        cv.vline(x, ridge[i], base - ridge[i] + 1, mass)
        if i % 3 == 0:
            cv.px(x, ridge[i], forest[1])
    for (a, b, hgt) in [(0.05, 0.42, 60), (0.36, 0.70, 52), (0.64, 0.94, 42)]:
        hgt = int(round(hgt * tall))
        sx0, sx1 = x0 + int(a * span), x0 + int(b * span)
        w = sx1 - sx0
        top = base - hgt
        crest_x = sx0 + int(w * 0.2)
        pts = [(sx0, base), (sx0 + int(w * 0.08), top + int(hgt * 0.35)), (crest_x - 3, top + 3), (crest_x, top),
               (crest_x + 4, top + 1), (crest_x + int(w * 0.18), top + int(hgt * 0.16)), (sx1, base)]
        cv.poly(pts, slab)
        cv.poly([(crest_x, top + 1), (crest_x + 4, top + 2), (crest_x + int(w * 0.18), top + int(hgt * 0.17)), (sx1, base),
                 (crest_x + int(w * 0.1), base)], face)
        for j in range(1, 6):
            xa = crest_x + int(w * 0.04 * j)
            cv.line(xa, top + 2 + j, xa + int((sx1 - xa) * 0.85), base - 1, rib if j % 2 else slab)
        cv.line(crest_x, top, crest_x + int(w * 0.18), top + int(hgt * 0.16), crest)
        cv.line(crest_x + int(w * 0.18), top + int(hgt * 0.16), sx1, base, rib)
        for yy in range(top + int(hgt * 0.45), base):
            gw = int((yy - top) * 0.25)
            cv.hline(sx0 - gw // 2, yy, gw, gully)
    # forest along the foot
    for _ in range(span * 3):
        px_ = x0 + int(rng.integers(0, span))
        py_ = base - int(abs(rng.normal(0, 7)))
        cv.px(px_, py_, forest[0] if rng.random() < 0.7 else forest[1])


def flatirons_cut(dawn=False, scale=2.5):
    """The Flatirons cut out of the title painting (sky transparent), for battle views where the
    mountains stand larger than flatirons_m draws them. Night: regraded to moonlit blue-violet with
    the slab faces pale; dawn: the painting's own alpenglow, warmed a touch. Returns float RGBA."""
    from scipy import ndimage
    from sky import flatirons_panel
    panel = flatirons_panel(scale, colors=24)
    ph, pw = panel.shape[:2]
    lum = panel[..., :3] @ np.array([0.3, 0.55, 0.15], np.float32)
    dark = (lum < 0.3) & (np.arange(ph)[:, None] > ph * 0.35)
    lab, n = ndimage.label(dark)
    keep = np.unique(lab[-1][lab[-1] > 0])
    body = np.isin(lab, keep)
    mask = np.zeros((ph, pw), bool)
    for x in range(pw):
        col = np.where(body[:, x])[0]
        if len(col):
            mask[col[0]:, x] = True
    mask = ndimage.binary_opening(mask, structure=np.ones((1, 3)))
    out = np.zeros_like(panel)
    if dawn:
        out[..., :3] = np.clip(panel[..., :3] * np.array([1.06, 0.98, 0.96], np.float32), 0, 1)
    else:
        ramp = np.array([C(c)[:3] for c in ["#12142a", "#191b36", "#212442", "#2c2e52", "#3a3a62", "#4e4c74", "#6a6488"]], np.float32)
        idx = np.clip(((lum - 0.08) / 0.5) * (len(ramp) - 1), 0, len(ramp) - 1).round().astype(int)
        out[..., :3] = ramp[idx]
    out[..., 3] = mask
    return out


def treeline_m(cv, x0, x1, base, seed=0, dawn=False, roofs=True, lit=0.35):
    """The campus beyond: rounded tree crowns and red-roofed sandstone halls along the horizon,
    a few lit windows (none at dawn). Returns lit window points."""
    rng = _rng(seed)
    pts = []
    far = "#2a2a3c" if dawn else "#1a1c30"
    near = "#33303c" if dawn else "#151726"
    for x in range(x0 - 8, x1 + 8, 9):
        hh = int(rng.integers(8, 17))
        cv.ellipse(x, base - hh, int(rng.integers(13, 20)), hh * 2, far)
    if roofs:
        x = x0 + int(rng.integers(0, 20))
        while x < x1 - 20:
            bw, bh = int(rng.integers(34, 62)), int(rng.integers(9, 15))
            if rng.random() < 0.3:
                x += bw // 2
                continue
            wall = "#4a3a44" if dawn else "#2a2238"
            roof = "#7a4a48" if dawn else "#4a2a2e"
            cv.rect(x, base - bh, bw, bh, wall)
            cv.poly([(x - 3, base - bh), (x + 6, base - bh - 6), (x + bw - 6, base - bh - 6), (x + bw + 3, base - bh)], roof)
            cv.hline(x + 6, base - bh - 6, bw - 12, "#9a5a4e" if dawn else "#6a3a36")
            for wx in range(x + 4, x + bw - 4, 6):
                if not dawn and rng.random() < lit:
                    cv.rect(wx, base - bh + 4, 2, 2, "#d0924a")
                    pts.append((wx, base - bh + 4))
                elif dawn and rng.random() < 0.3:
                    cv.rect(wx, base - bh + 4, 2, 2, "#e0a890")
            x += bw + int(rng.integers(8, 30))
    for x in range(x0 - 6, x1 + 6, 7):
        hh = int(rng.integers(4, 10))
        cv.ellipse(x, base - hh + 3, int(rng.integers(9, 15)), hh * 2, near)
    return pts


# --- outdoor props ----------------------------------------------------------------------------
def procession_lamp(height=68, dawn=False, banner=True):
    """A campus lamp post on the procession walk: fluted iron column, acorn lantern, and a CU
    commencement banner (gold, black border) hanging from a bracket. Lamp core ~5px below top."""
    w = 30
    cv = Canvas(w, height + 6, seed=17)
    cx, base = 11, height + 2
    ground_shadow(cv, cx, base, 9, 2)
    cv.rect(cx - 5, base - 5, 11, 5, OUT); cv.rect(cx - 4, base - 4, 9, 4, IRON[2]); cv.hline(cx - 4, base - 4, 9, IRON[4])
    cv.rect(cx - 3, base - 10, 7, 5, OUT); cv.rect(cx - 2, base - 9, 5, 4, IRON[2]); cv.vline(cx - 2, base - 9, 4, IRON[4])
    top = 16
    cv.rect(cx - 2, top, 5, base - 10 - top, OUT)
    cv.vline(cx - 1, top, base - 10 - top, IRON[3]); cv.vline(cx, top, base - 10 - top, IRON[2]); cv.vline(cx + 1, top, base - 10 - top, IRON[1])
    for ry in (top + 4, top + 22):
        cv.rect(cx - 3, ry, 7, 2, IRON[1]); cv.hline(cx - 3, ry, 7, IRON[4])
    # lantern: acorn globe
    glow = ["#c47a2c", "#eaa845", "#f6cf7a", "#fff0c4"] if not dawn else ["#8a7a6a", "#b8a890", "#d8c8b0", "#ece0cc"]
    cv.rect(cx - 3, top - 2, 7, 3, IRON[1])
    cv.ellipse(cx - 4, 3, 9, 13, OUT)
    cv.ellipse(cx - 3, 4, 7, 11, glow[1]); cv.ellipse(cx - 2, 5, 5, 8, glow[2]); cv.rect(cx - 1, 6, 2, 5, glow[3])
    cv.rect(cx - 2, 1, 5, 3, IRON[2]); cv.px(cx, 0, IRON[3])
    if banner:
        by = top + 6
        cv.rect(cx + 2, by, 14, 2, IRON[1]); cv.hline(cx + 2, by, 14, IRON[3])
        bx0, bw, bh = cx + 4, 12, 22
        cv.rect(bx0 - 1, by + 2, bw + 2, bh + 1, OUT)
        cv.rect(bx0, by + 2, bw, bh, CU_GOLD[3]); cv.vline(bx0, by + 2, bh, CU_GOLD[4]); cv.vline(bx0 + bw - 1, by + 2, bh, CU_GOLD[1])
        cv.rect(bx0 + 1, by + 3, bw - 2, 2, "#1a1418"); cv.rect(bx0 + 1, by + bh - 3, bw - 2, 2, "#1a1418")
        cv.poly([(bx0, by + bh + 2), (bx0 + bw // 2, by + bh - 2), (bx0 + bw, by + bh + 2)], (0, 0, 0, 0))
        # banner hem cut as a swallowtail
        for k in range(bw // 2):
            cv.px(bx0 + bw // 2 - k, by + bh + 1 - (k // 2), (0, 0, 0, 0))
            cv.px(bx0 + bw // 2 + k - 1, by + bh + 1 - (k // 2), (0, 0, 0, 0))
        # a little torch emblem
        ex = bx0 + bw // 2
        cv.rect(ex - 1, by + 10, 2, 6, "#1a1418"); cv.rect(ex - 2, by + 8, 4, 2, "#1a1418"); cv.px(ex - 1, by + 7, "#7e3a30"); cv.px(ex, by + 6, "#c84a3c")
    return cv, cx, base


def long_bench(width=140, height=32, seed=3):
    """A long campus bench: sandstone pedestals, oak slats for seat and back, iron arm rests."""
    rng = _rng(seed)
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 2)
    for i, yy in enumerate((3, 8)):
        cv.rect(ox + 6, yy, width - 12, 4, OUT)
        cv.rect(ox + 7, yy + 1, width - 14, 2, WOOD[4] if i == 0 else WOOD[3]); cv.hline(ox + 7, yy + 1, width - 14, WOOD[5])
        for gx in range(ox + 12, ox + width - 10, int(rng.integers(9, 14))):
            cv.hline(gx, yy + 2, 3, WOOD[2])
    for px_ in (ox + 18, ox + width // 2, ox + width - 19):
        cv.rect(px_ - 1, 6, 3, 12, OUT); cv.vline(px_, 6, 12, IRON[2])
    cv.rect(ox + 2, 15, width - 4, 6, OUT)
    cv.rect(ox + 3, 16, width - 6, 2, WOOD[4]); cv.hline(ox + 3, 16, width - 6, WOOD[5]); cv.rect(ox + 3, 18, width - 6, 2, WOOD[2])
    for px_ in (ox + 8, ox + width // 2 - 7, ox + width - 22):
        cv.rect(px_, 21, 14, base - 21, OUT)
        cv.rect(px_ + 1, 21, 12, base - 22, DRESS[3]); cv.vline(px_ + 1, 21, base - 22, DRESS[5]); cv.vline(px_ + 12, 21, base - 22, DRESS[1])
        cv.hline(px_ + 1, 21, 12, DRESS[4]); cv.hline(px_ + 1, base - 3, 12, DRESS[2])
    for ax in (ox + 2, ox + width - 7):
        cv.rect(ax, 11, 5, 3, OUT); cv.hline(ax + 1, 12, 3, IRON[3]); cv.rect(ax + 1, 13, 2, 3, IRON[2])
    return cv, ox + width // 2, base


def stencil_text(cv, s, x, y, colour, scale=2, alpha=1.0, worn=0.0, seed=0):
    """The game font blown up `scale` times (painted stencil on paving), optionally worn."""
    rng = _rng(seed)
    tmp = Canvas(text_width(s) + 2, 12)
    text(tmp, s, 0, 0, "#ffffff")
    m = tmp.a[..., 3] > 0.5
    ys, xs = np.where(m)
    col = C(colour, alpha)
    for yy, xx in zip(ys, xs):
        for dy in range(scale):
            for dx in range(scale):
                if worn and rng.random() < worn:
                    continue
                cv.px(x + xx * scale + dx, y + yy * scale + dy, col)


def tape_box(cv, x, y, w, h, colour="#e8c060", label=None, label_c="#e6d6b1", seed=0, worn=0.15):
    """A rectangle of floor tape (a reserved place marked on the paving), peeling here and there,
    with a small stencil label inside."""
    rng = _rng(seed)
    for (xx, yy, ww, hh) in [(x, y, w, 2), (x, y + h - 2, w, 2), (x, y, 2, h), (x + w - 2, y, 2, h)]:
        for py_ in range(yy, yy + hh):
            for px_ in range(xx, xx + ww):
                if rng.random() < worn:
                    continue
                cv.px(px_, py_, colour)
    for _ in range(2):
        px_ = x + int(rng.integers(2, w - 4)); py_ = y + h - 2
        cv.px(px_, py_ + 2, colour); cv.px(px_ + 1, py_ + 3, shade(colour, -0.2))
    if label:
        text(cv, label, x + w // 2 - text_width(label) // 2, y + h // 2 - 4, label_c)


def reserved_notice(width=84, height=60, title="RESERVED", lines=("FOR EVERY", "FUTURE")):
    """An easel sign on the walk: a cream card in a black frame with a gold header band, held
    on two oak legs. anchor bottom-centre."""
    cv = Canvas(width + 6, height + 6, seed=5)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 - 6, 2)
    for lx in (ox + 12, ox + width - 14):
        cv.rect(lx, base - 22, 3, 22, OUT); cv.vline(lx + 1, base - 22, 21, WOOD[3])
    cv.line(ox + width // 2, base - 24, ox + width // 2 + 6, base - 1, OUT)
    top = base - height
    ch = height - 18
    cv.rect(ox, top, width, ch, OUT)
    cv.rect(ox + 1, top + 1, width - 2, ch - 2, "#2a2230")
    cv.rect(ox + 3, top + 3, width - 6, ch - 6, "#e6d6b1"); cv.hline(ox + 3, top + 3, width - 6, "#f6ecd2")
    cv.rect(ox + 3, top + 3, width - 6, 12, CU_GOLD[3]); cv.hline(ox + 3, top + 3, width - 6, CU_GOLD[4]); cv.hline(ox + 3, top + 14, width - 6, CU_GOLD[1])
    text(cv, title, ox + width // 2 - text_width(title) // 2, top + 4, "#1a1418")
    for i, ln in enumerate(lines):
        text(cv, ln, ox + width // 2 - text_width(ln) // 2, top + 17 + i * 9, "#5a4a44")
    # a corner of the card curling, a paper clip
    cv.px(ox + width - 5, top + ch - 5, "#b8a888"); cv.px(ox + width - 6, top + ch - 4, "#b8a888")
    cv.rect(ox + 8, top + 1, 2, 5, IRON[4])
    return cv, ox + width // 2, base


# --- the lobby (M02) ----------------------------------------------------------------------------
PLASTER_M = ["#4a3430", "#5c4238", "#6e5040", "#7e5e4a", "#8e6c54", "#9e7c60", "#ae8c6c"]   # warm ochre plaster
VELVET_M = ["#2a0f16", "#47161f", "#66202a", "#842c34", "#a33c3e", "#c05048"]                 # oxblood leather/velvet
CARPET_M = ["#1a0c10", "#2e1218", "#4a1a22", "#66222c", "#842e36", "#c0884a", "#e0b26a"]      # runner (runner_n order)
TILE_M = ("#5e3e38", "#76504a", "#805850", "#8a6056", "#94685c")                              # rose sandstone tiles
INSET_M = ("#2a1018", "#4a1a22", "#6a2a2e")
SHADE_PARCH = ["#4a3a2a", "#7a6448", "#b89a74", "#d8c09a", "#f0dcb4"]                          # parchment lamp shade
GILT_M = "#e8c070"


TILE_BUFF = ("#644640", "#7c5a50", "#866258", "#906a5e", "#9a7464")


def lobby_tiles(cv, x, y, w, h, seed=0, size=22, rose=TILE_M, buff=TILE_BUFF, inset=INSET_M, joint="#3e2826"):
    """Polished sandstone tiles laid in a checker of rose and buff, rows a touch deeper toward the
    viewer, oxblood cabochons where four tiles meet, a lit top edge, a faint vein now and then."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, joint)
    yy, rows = y, []
    while yy < y + h:
        th = int(round(size * (0.6 + 0.16 * (yy - y) / max(1, h))))
        th = max(4, min(th, y + h - yy))
        rows.append((yy, th))
        yy += th
    off = (w % size) // 2 - size // 2
    cols = list(range(x + off, x + w, size))
    for r_, (yy, th) in enumerate(rows):
        for c_, xx in enumerate(cols):
            x0, x1 = max(x, xx + 1), min(x + w, xx + size)
            if x1 <= x0:
                continue
            fam = rose if (r_ + c_) % 2 else buff
            tone = fam[int(rng.choice([2, 3, 3, 2, 4, 1]))]
            cv.rect(x0, yy + 1, x1 - x0, th - 1, tone)
            cv.hline(x0, yy + 1, x1 - x0, shade(tone, 0.12))
            cv.hline(x0, yy + th - 1, x1 - x0, shade(tone, -0.1))
            if rng.random() < 0.2:
                vx, vy = x0 + int(rng.integers(3, max(4, x1 - x0 - 3))), yy + 2
                for _ in range(int(rng.integers(3, th))):
                    cv.px(vx, vy, shade(tone, -0.1)); vx += int(rng.integers(-1, 2)); vy += 1
                    if vy >= yy + th - 1:
                        break
            if rng.random() < 0.25:
                cv.line(x0 + 3, yy + th - 3, x0 + 7, yy + 3, shade(tone, 0.08))
    for (yy, th) in rows[1:]:
        for xx in cols:
            if x + 3 < xx < x + w - 3 and y + 3 < yy < y + h - 3:
                cv.poly([(xx - 4, yy), (xx, yy - 2), (xx + 4, yy), (xx, yy + 2)], inset[0])
                cv.poly([(xx - 3, yy), (xx, yy - 1), (xx + 3, yy), (xx, yy + 1)], inset[1])
                cv.px(xx - 1, yy - 1, inset[2])


def window_view(cv, x, y, w, h, dawn=False, seed=0, mask=None):
    """What a lobby window shows: sky bands (night with stars, or sunrise), the Flatirons as a
    small dark range (slabs pink with alpenglow at dawn), a line of campus trees. Painted into the
    rectangle and clipped to `mask` if given (a full-canvas bool array)."""
    rng = _rng(seed)
    sub = Canvas(w, h)
    pal = DAWN_M[1:] if dawn else ["#121634", "#182040", "#1e284c", "#263258", "#2e3a62"]
    for yy in range(h):
        t = yy / max(1, h - 1)
        sub.hline(0, yy, w, pal[min(len(pal) - 1, int(t ** 1.2 * len(pal)))])
    if not dawn:
        for _ in range(max(3, w * h // 60)):
            sub.px(int(rng.integers(0, w)), int(rng.integers(0, int(h * 0.55))), "#c8d0f0" if rng.random() < 0.6 else "#8a96c8")
    base = h - 6
    mass, face, crest = ("#4a3a5a", "#c87a74", "#f0b08a") if dawn else ("#1a1a34", "#2a2a48", "#3a3658")
    for (sx, sw, sh) in [(-4, 0.55, 0.42), (int(w * 0.35), 0.5, 0.36), (int(w * 0.7), 0.45, 0.28)]:
        ww = int(w * sw)
        top = base - int(h * sh)
        cx_ = sx + ww // 4
        sub.poly([(sx, base), (cx_, top), (sx + ww, base)], mass)
        sub.poly([(cx_, top + 1), (sx + ww, base), (cx_ + 2, base)], face)
        sub.line(cx_, top, cx_ + ww // 3, top + (base - top) // 3, crest)
    for xx in range(-4, w + 4, 5):
        th = int(rng.integers(3, 7))
        sub.ellipse(xx, base - th + 2, 7, th * 2, "#2a2a38" if dawn else "#10141e")
    sub.rect(0, base + 2, w, h - base - 2, "#2a2a38" if dawn else "#10141e")
    if mask is None:
        cv.paste(sub.a, x, y)
    else:
        reg = mask[y:y + h, x:x + w]
        tgt = cv.a[y:y + h, x:x + w]
        src = sub.a[:reg.shape[0], :reg.shape[1]]
        tgt[reg] = src[reg]


def lobby_window(cv, cx, top, w=40, h=70, dawn=False, seed=0):
    """A tall round-headed lobby window in a dressed sandstone surround: a border of stained glass
    (amber, ruby, blue squares), leaded clear quarries showing the sky and the mountains, a deep
    sill. (cx, top) is the crown of the arch."""
    r = w // 2
    spring = top + r
    bottom = top + h
    # surround: dressed jambs and a ring of voussoirs
    for side in (cx - r - 5, cx + r):
        cv.rect(side, spring, 5, bottom - spring, DRESS[3]); cv.vline(side, spring, bottom - spring, DRESS[5] if side < cx else DRESS[1])
        for yy in range(spring + 6, bottom, 8):
            cv.hline(side, yy, 5, DRESS[1])
    voussoirs(cv, cx, spring, r, thick=5, n=9)
    m = _arch_mask(cv, cx, spring, r, bottom)
    cv.fill_mask(m, FRAME)
    glass = _arch_mask(cv, cx, spring, r - 1, bottom - 1)
    ys, xs = np.where(glass)
    gx0, gy0 = xs.min(), ys.min()
    window_view(cv, gx0, gy0, xs.max() - gx0 + 1, ys.max() - gy0 + 1, dawn=dawn, seed=seed, mask=glass)
    # stained-glass border: small squares round the edge of the glass
    inner = _arch_mask(cv, cx, spring, r - 5, bottom - 5)
    border = glass & ~inner
    cols = ["#c47a2c", "#a83c32", "#3a5aa0", "#e9a84a", "#6a8a4a"] if not dawn else ["#e0a050", "#c85848", "#6a7ac0", "#f6c870", "#8aa860"]
    by, bx = np.where(border)
    for yy, xx in zip(by, bx):
        k = ((xx // 3) + (yy // 3)) % len(cols)
        cv.px(xx, yy, cols[k])
    # leading: border line, diamond quarries in the clear field
    edge = inner & ~_arch_mask(cv, cx, spring, r - 6, bottom - 6)
    cv.fill_mask(edge, FRAME)
    iy, ix = np.where(inner & ~edge)
    for yy, xx in zip(iy, ix):
        if (xx + yy) % 6 == 0 or (xx - yy) % 6 == 0:
            cv.px(xx, yy, mix(cv.a[yy, xx], C(FRAME), 0.5))
    # a transom bar and a reflection
    cv.rect(cx - r + 1, spring + 2, w - 2, 2, FRAME); cv.hline(cx - r + 1, spring + 2, w - 2, IRON[3])
    cv.line(cx - r + 4, bottom - 8, cx - r + 10, bottom - 22, C("#c8d0f0" if not dawn else "#fff0d8", 0.3))
    # sill
    cv.rect(cx - r - 7, bottom, w + 14, 4, DRESS[4]); cv.hline(cx - r - 7, bottom, w + 14, DRESS[6])
    cv.hline(cx - r - 7, bottom + 3, w + 14, DRESS[1]); cv.hline(cx - r - 7, bottom + 4, w + 14, C(SHADOW, 0.45))
    return bottom


def leather_door(cv, x, y, w, h, seed=0, porthole=True, lit_glass=True):
    """One leaf of a padded auditorium door: oxblood leather buttoned in a diamond grid, brass
    nail heads round the edge, a round porthole window, brass push and kick plates."""
    cv.rect(x, y, w, h, OUT)
    cv.rect(x + 1, y + 1, w - 2, h - 2, VELVET_M[2])
    for yy in range(y + 3, y + h - 3):
        for xx in range(x + 3, x + w - 3):
            u, v = (xx - x) % 8, (yy - y) % 8
            if abs(u - 4) + abs(v - 4) == 4:
                cv.px(xx, yy, VELVET_M[1])
            elif abs(u - 4) + abs(v - 4) == 3 and v < 4:
                cv.px(xx, yy, VELVET_M[3])
    for yy in range(y + 7, y + h - 4, 8):
        for xx in range(x + 7, x + w - 4, 8):
            cv.px(xx, yy, BRASS[3])
    for xx in range(x + 2, x + w - 2, 3):
        cv.px(xx, y + 2, BRASS[2]); cv.px(xx, y + h - 3, BRASS[2])
    for yy in range(y + 2, y + h - 2, 3):
        cv.px(x + 2, yy, BRASS[2]); cv.px(x + w - 3, yy, BRASS[2])
    cv.hline(x + 1, y + 1, w - 2, VELVET_M[4])
    if porthole:
        pcx, pcy = x + w // 2, y + 16
        cv.ellipse(pcx - 6, pcy - 6, 13, 13, BRASS[2]); cv.ellipse(pcx - 5, pcy - 5, 11, 11, BRASS[4])
        cv.ellipse(pcx - 4, pcy - 4, 9, 9, GLOW[2] if lit_glass else DARKGLASS[1])
        cv.ellipse(pcx - 3, pcy - 4, 6, 5, GLOW[3] if lit_glass else DARKGLASS[2])
        cv.px(pcx - 2, pcy - 2, "#fff0c4" if lit_glass else DARKGLASS[3])
    py = y + h // 2 + 2
    cv.rect(x + 3, py, w - 6, 5, BRASS[2]); cv.hline(x + 3, py, w - 6, BRASS[4]); cv.hline(x + 3, py + 4, w - 6, BRASS[1])
    cv.rect(x + 2, y + h - 9, w - 4, 7, BRASS[1]); cv.hline(x + 2, y + h - 9, w - 4, BRASS[3])


def house_glimpse(cv, x, y, w, h, seed=0):
    """The auditorium seen through open doors: the centre aisle running down between rows of red
    seat backs to the lit stage, the curtain glowing gold. Fills the rectangle."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, "#2a1418")
    # stage at the far end: warm proscenium glow and curtain
    sh = h // 3
    cv.rect(x, y, w, sh, "#6a2a26")
    for xx in range(x, x + w, 3):
        cv.vline(xx, y, sh, "#8a3a2e" if (xx // 3) % 2 else "#a8483a")
    cv.rect(x, y + sh - 3, w, 3, "#f0c070"); cv.hline(x, y + sh - 3, w, "#fff0c4")
    # seat rows stepping down toward us
    for k, yy in enumerate(range(y + sh + 1, y + h, 4)):
        cv.hline(x, yy, w, VELVET_M[3] if k % 2 else VELVET_M[2])
        cv.hline(x, yy + 1, w, VELVET_M[1])
        cv.hline(x, yy + 2, w, "#1a0c10")
    # the aisle: a carpet strip widening toward us
    for yy in range(y + sh, y + h):
        t = (yy - y - sh) / max(1, h - sh)
        hw = int(2 + t * w * 0.18)
        cv.hline(x + w // 2 - hw, yy, hw * 2, "#4a1a22" if yy % 4 else "#5e2430")
        cv.px(x + w // 2 - hw, yy, "#c0884a"); cv.px(x + w // 2 + hw - 1, yy, "#c0884a")
    # aisle lights
    for yy in range(y + sh + 4, y + h, 7):
        t = (yy - y - sh) / max(1, h - sh)
        hw = int(2 + t * w * 0.18)
        cv.px(x + w // 2 - hw - 1, yy, "#f6cf7a"); cv.px(x + w // 2 + hw, yy, "#f6cf7a")


def auditorium_doors(cv, cx, bottom, open_=False, dawn=False, seed=0):
    """The great doors from the lobby into the house: a round arch of dressed voussoirs over a
    gilt fanlight, two padded leather leaves (or, open, the house beyond), AUDITORIUM in gilt on
    a band above. Doors are 72px tall. Returns the fanlight centre for a glow point."""
    w, h = 62, 72
    r = w // 2 + 6
    spring = bottom - h
    # the deep reveal and jambs
    for side in (cx - r - 7, cx + r):
        cv.rect(side, spring, 7, h, DRESS[3]); cv.vline(side, spring, h, DRESS[5] if side < cx else DRESS[1])
        for yy in range(spring + 7, bottom, 9):
            cv.hline(side, yy, 7, DRESS[1])
        cv.rect(side - 1, spring - 3, 9, 3, DRESS[4]); cv.hline(side - 1, spring - 3, 9, DRESS[6])
    voussoirs(cv, cx, spring, r, thick=8, n=13)
    m = _arch_mask(cv, cx, spring, r, bottom)
    cv.fill_mask(m, "#1c1418")
    # fanlight: gilt sunburst over warm glass
    fan = _arch_mask(cv, cx, spring - 2, r - 3, spring - 2)
    ys, xs = np.where(fan)
    for yy, xx in zip(ys, xs):
        cv.px(xx, yy, GLOW[2] if (spring - yy) < r * 0.45 else GLOW[3])
    for k in range(1, 10):
        a = np.pi * k / 10
        cv.line(cx - 0.5, spring - 3, int(round(cx - 0.5 + np.cos(a) * (r - 3))), int(round(spring - 3 - np.sin(a) * (r - 3))), BRASS[2])
    cv.ellipse(cx - 6, spring - 8, 12, 12, BRASS[2]); cv.ellipse(cx - 4, spring - 6, 8, 8, BRASS[4]); cv.ellipse(cx - 2, spring - 4, 4, 4, GLOW[4])
    cv.rect(cx - r + 2, spring - 3, 2 * r - 4, 3, BRASS[1]); cv.hline(cx - r + 2, spring - 3, 2 * r - 4, BRASS[3])
    x0 = cx - r + 2
    dw = (2 * r - 4) // 2
    if open_:
        house_glimpse(cv, x0, spring, 2 * r - 4, h, seed=seed)
        for lx in (x0, x0 + 2 * dw - 6):
            cv.rect(lx, spring, 6, h, VELVET_M[1]); cv.vline(lx + (5 if lx == x0 else 0), spring, h, VELVET_M[3])
            cv.vline(lx + (0 if lx == x0 else 5), spring, h, OUT)
    else:
        leather_door(cv, x0, spring, dw, h, seed=seed, lit_glass=True)
        leather_door(cv, x0 + dw, spring, dw, h, seed=seed + 1, lit_glass=True)
        cv.vline(cx - 1, spring, h, OUT)
        # light seeping under the doors
        cv.hline(x0 + 1, bottom - 1, 2 * dw - 2, GLOW[3])
    # threshold slab
    cv.rect(cx - r - 8, bottom - 2, 2 * r + 16, 2, DRESS[4]); cv.hline(cx - r - 8, bottom - 2, 2 * r + 16, DRESS[6])
    return (cx, spring - r // 2)


def gilt_band(cv, cx, y, label, w=None, h=11):
    """A carved band of dressed stone with gilt capitals (over a door)."""
    w = w or text_width(label) + 20
    x = cx - w // 2
    cv.rect(x - 1, y - 1, w + 2, h + 2, DRESS[1])
    cv.rect(x, y, w, h, DRESS[3]); cv.hline(x, y, w, DRESS[5]); cv.hline(x, y + h - 1, w, DRESS[1])
    tx = cx - text_width(label) // 2
    text(cv, label, tx + 1, y + 2, "#5a3a20")
    text(cv, label, tx, y + 1, GILT_M)
    for ex in (x + 3, x + w - 6):
        cv.poly([(ex, y + h // 2), (ex + 2, y + 2), (ex + 4, y + h // 2), (ex + 2, y + h - 3)], GILT_M)


def stair_up(cv, cx, bottom, w=66, h=78, dawn=False, label=None):
    """An open arch in the back wall with a stone stair climbing away up through it (to the
    balcony): steps narrowing and darkening as they rise, a plum runner up the middle, brass
    handrails on the side walls, a lamp on the landing at the top."""
    r = w // 2
    spring = bottom - h + r
    for side in (cx - r - 6, cx + r):
        cv.rect(side, spring, 6, bottom - spring, DRESS[3]); cv.vline(side, spring, bottom - spring, DRESS[5] if side < cx else DRESS[1])
        for yy in range(spring + 6, bottom, 8):
            cv.hline(side, yy, 6, DRESS[1])
    voussoirs(cv, cx, spring, r, thick=7, n=11)
    m = _arch_mask(cv, cx, spring, r, bottom)
    cv.fill_mask(m, "#1a1218")
    top = bottom - h
    # the stairwell's side walls (plaster, lamplit from the landing)
    land_y = top + 20
    cv.rect(cx - r, land_y - 8, 2 * r, 10, PLASTER_M[2])
    sconce_x = cx
    cv.rect(cx - 9, land_y - 22, 18, 14, PLASTER_M[3])
    # steps from the floor up to the landing: each tread a band, narrower and darker as it rises
    n = 11
    for k in range(n):
        t = k / (n - 1)
        y1 = int(round(bottom - t * (bottom - land_y)))
        y0 = int(round(bottom - (k + 1) / (n - 1) * (bottom - land_y))) if k < n - 1 else land_y
        hw = int(round(r - 1 - t * 10))
        tone = [DRESS[4], DRESS[3], DRESS[3], DRESS[2], DRESS[2], DRESS[1]][min(5, int(t * 6))]
        rise = max(2, y1 - y0)
        cv.rect(cx - hw, y1 - rise, 2 * hw, rise, shade(tone, -0.18))
        cv.hline(cx - hw, y1 - rise, 2 * hw, tone)
        rw = int(round(9 - t * 4))
        cv.rect(cx - rw, y1 - rise, 2 * rw, rise, CARPET_M[3] if k % 2 else CARPET_M[2])
        cv.hline(cx - rw, y1 - rise, 2 * rw, CARPET_M[4])
        cv.px(cx - rw, y1 - rise + 1, BRASS[3]); cv.px(cx + rw - 1, y1 - rise + 1, BRASS[3])
    # side walls of the flight
    for sd in (-1, 1):
        for k in range(bottom - land_y):
            yy = bottom - k
            t = k / (bottom - land_y)
            edge = int(round(r - 1 - t * 10))
            x_in = cx + sd * edge
            x_out = cx + sd * (r - 1)
            a, b = sorted((x_in, x_out))
            cv.hline(a, yy, b - a + 1, PLASTER_M[1] if sd < 0 else PLASTER_M[2])
        # brass handrail climbing toward the landing
        cv.line(cx + sd * (r - 4), bottom - 30, cx + sd * (r - 12), land_y - 4, BRASS[3])
        cv.line(cx + sd * (r - 4), bottom - 29, cx + sd * (r - 12), land_y - 3, BRASS[1])
    # landing lamp
    cv.ellipse(cx - 14, land_y - 30, 29, 20, C("#f6cf7a", 0.12))
    cv.rect(cx - 3, land_y - 20, 7, 7, OUT); cv.rect(cx - 2, land_y - 19, 5, 5, GLOW[3]); cv.px(cx, land_y - 18, GLOW[4])
    if label:
        gilt_band(cv, cx, top - 16 - 12, label)
    cv.rect(cx - r - 7, bottom - 2, 2 * r + 14, 2, DRESS[4]); cv.hline(cx - r - 7, bottom - 2, 2 * r + 14, DRESS[6])
    return (cx, land_y - 16)


def hanging_lantern(cv, x, y, chain_top=0, lit=True, dawn=False):
    """A big iron hall lantern on a chain: hexagonal cage, amber glass, a crown of iron leaves.
    (x, y) is the bottom finial."""
    cv.vline(x, chain_top, y - 26 - chain_top, IRON[2])
    for cy in range(chain_top + 1, y - 26, 3):
        cv.px(x, cy, IRON[3]); cv.px(x - 1, cy + 1, IRON[1])
    top = y - 24
    if lit:
        for rr, a in [(20, 0.04), (14, 0.06), (9, 0.08)]:
            cv.ellipse(x - rr, top + 10 - rr, rr * 2 + 1, rr * 2 + 1, C("#f6cf7a", a))
    cv.poly([(x - 7, top + 2), (x, top - 3), (x + 7, top + 2)], OUT)
    cv.poly([(x - 5, top + 1), (x, top - 2), (x + 5, top + 1)], IRON[3])
    cv.rect(x - 7, top + 2, 15, 16, OUT)
    g = GLOW if lit else ["#3a3448", "#4e4860", "#6a6480", "#8a84a0", "#a8a0b8"]
    cv.rect(x - 6, top + 3, 13, 14, g[2]); cv.rect(x - 4, top + 4, 9, 11, g[3]); cv.rect(x - 1, top + 6, 3, 6, g[4])
    for bx in (x - 3, x + 3):
        cv.vline(bx, top + 3, 14, IRON[1])
    cv.hline(x - 6, top + 9, 13, IRON[1])
    cv.rect(x - 8, top + 17, 17, 3, IRON[2]); cv.hline(x - 8, top + 17, 17, IRON[4])
    cv.poly([(x - 4, top + 20), (x + 4, top + 20), (x, y)], OUT); cv.vline(x, top + 20, y - top - 20, IRON[3])


def hanging_sign(cv, cx, y, label, chain_top=0):
    """An oak sign board with gilt letters hung on two chains from the ceiling."""
    w = text_width(label) + 12
    x = cx - w // 2
    for hx in (x + 5, x + w - 6):
        cv.vline(hx, chain_top, y - chain_top, IRON[2])
        for cy in range(chain_top + 1, y, 3):
            cv.px(hx, cy, IRON[3])
    cv.rect(x - 1, y - 1, w + 2, 15, OUT)
    cv.rect(x, y, w, 13, WOOD[2]); cv.hline(x, y, w, WOOD[4]); cv.hline(x, y + 12, w, WOOD[1])
    cv.rect(x + 2, y + 2, w - 4, 9, "#1c1418")
    text(cv, label, x + 6, y + 2, GILT_M)
    return x, w


def directory_board(width=120, height=74, title="TWO CHOICES",
                    rows=(("< CLOAKROOM", "GUESTS"), ("ORCHESTRA PIT >", "SCORE"), ("BALCONY ^", "AFTER"))):
    """The lobby directory on its stand: a dark oak frame, a black felt board with white
    push-in letters, a gilt header plate with the title. anchor bottom-centre."""
    cv = Canvas(width + 4, height + 4, seed=9)
    ox, base = 2, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 - 8, 2)
    for lx in (ox + 14, ox + width - 17):
        cv.rect(lx, base - 22, 4, 22, OUT); cv.rect(lx + 1, base - 22, 2, 21, WOOD[3]); cv.vline(lx + 1, base - 22, 21, WOOD[4])
        cv.rect(lx - 3, base - 3, 10, 3, OUT); cv.hline(lx - 2, base - 3, 8, WOOD[2])
    top = base - height
    bh = height - 18
    cv.rect(ox, top, width, bh, OUT)
    cv.rect(ox + 1, top + 1, width - 2, bh - 2, WOOD[3]); cv.hline(ox + 1, top + 1, width - 2, WOOD[5])
    cv.rect(ox + 1, top + bh - 3, width - 2, 2, WOOD[1])
    cv.rect(ox + 4, top + 4, width - 8, bh - 8, "#141218")
    for yy in range(top + 6, top + bh - 5, 2):
        cv.hline(ox + 5, yy, width - 10, "#1a181f")
    # gilt header plate
    pw = text_width(title) + 10
    px_ = ox + width // 2 - pw // 2
    cv.rect(px_ - 1, top - 3, pw + 2, 13, OUT); cv.rect(px_, top - 2, pw, 11, BRASS[3]); cv.hline(px_, top - 2, pw, BRASS[4]); cv.hline(px_, top + 8, pw, BRASS[1])
    text(cv, title, px_ + 5, top - 2, "#2a1c10")
    for i, (a, b) in enumerate(rows):
        yy = top + 13 + i * 12
        text(cv, a, ox + 8 if b else ox + width // 2 - text_width(a) // 2, yy, "#e6e0d0")
        if b:
            text(cv, b, ox + width - 8 - text_width(b), yy, "#a89a86")
    return cv, ox + width // 2, base


def lobby_planter(width=82, height=54, seed=0):
    """A carved sandstone planter box: a kentia palm rising out of a mound of Boston fern, fronds
    spilling over the rim, ivy trailing down the front. anchor bottom-centre."""
    from props import foliage
    rng = _rng(seed)
    cv = Canvas(width + 12, height + 4, seed=seed)
    ox, base = 6, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    bh = 22
    top = base - bh
    mid = ox + width // 2
    # fern mound behind the rim
    foliage(cv, ox + 2, top - 15, width - 4, 19, seed=seed + 3)
    # fern fronds drooping out over both ends of the box
    for k in range(22):
        side = -1 if k % 2 else 1
        a = rng.uniform(0.05, 0.42) * np.pi
        L = int(rng.integers(12, 20))
        x0_ = mid + side * int(rng.integers(10, width // 2 - 4))
        y0_ = top - int(rng.integers(4, 12))
        for sgm in range(L):
            t = sgm / L
            px_ = int(round(x0_ + side * np.cos(a) * sgm * 1.2))
            py_ = int(round(y0_ - np.sin(a) * sgm * 0.7 + (t ** 2) * 13))
            cv.px(px_, py_, LEAF[3] if t < 0.4 else LEAF[4] if t < 0.8 else LEAF[5])
            if sgm % 2 == 1:
                cv.px(px_, py_ - 1, LEAF[2]); cv.px(px_ - side, py_ + 1, LEAF[3])
    # the palm: a stem and nine arching fronds with leaflets, lighter than the fern
    stem_top = top - 14
    cv.vline(mid, stem_top, top - stem_top, "#3e3020"); cv.vline(mid + 1, stem_top + 2, top - stem_top - 2, "#5a4630")
    palm = ["#3f5741", "#566d4a", "#73864f", "#8a9a5a"]
    for k in range(9):
        a = np.pi * (0.1 + 0.8 * k / 8) + rng.uniform(-0.05, 0.05)
        L = int(rng.integers(20, 26))
        for sgm in range(L):
            t = sgm / L
            px_ = int(round(mid + np.cos(a) * sgm * 1.25))
            py_ = int(round(stem_top - np.sin(a) * sgm * 1.05 + (t ** 2) * 11))
            cv.px(px_, py_, palm[2] if t < 0.5 else palm[1])
            if sgm > 2 and sgm % 2 == 0:
                drop = 2 + int(t * 3)
                cv.line(px_, py_, px_ - 1, py_ + drop, palm[3] if t < 0.6 else palm[2])
                cv.line(px_, py_, px_ + 1, py_ + drop, palm[1])
    # the box: dressed sandstone, a carved panel, a moulded rim
    cv.rect(ox, top, width, bh, OUT)
    cv.rect(ox + 1, top + 1, width - 2, bh - 2, DRESS[3]); cv.vline(ox + 1, top + 1, bh - 2, DRESS[5]); cv.vline(ox + width - 2, top + 1, bh - 2, DRESS[1])
    cv.rect(ox - 2, top - 1, width + 4, 5, OUT); cv.rect(ox - 1, top, width + 2, 3, DRESS[4]); cv.hline(ox - 1, top, width + 2, DRESS[6])
    cv.rect(ox + 8, top + 7, width - 16, bh - 12, DRESS[2]); cv.rect(ox + 9, top + 8, width - 18, bh - 14, DRESS[3])
    cv.hline(ox + 9, top + 8, width - 18, DRESS[1])
    cv.poly([(mid - 6, top + 11), (mid, top + 8), (mid + 6, top + 11), (mid, top + 14)], DRESS[4]); cv.px(mid, top + 11, DRESS[6])
    cv.rect(ox, base - 4, width, 3, DRESS[2]); cv.hline(ox, base - 4, width, DRESS[4])
    # trailing ivy over the rim
    for k in range(8):
        x = ox + 3 + int(rng.integers(0, width - 6))
        for sgm in range(int(rng.integers(4, 13))):
            cv.px(x + (sgm % 3 == 0), top + 1 + sgm, IVY[4] if sgm % 2 else IVY[3])
            if sgm % 3 == 1:
                cv.px(x - 1, top + 1 + sgm, IVY[5])
    return cv, ox + width // 2, base


def lobby_bench(width=115, height=32, seed=0):
    """An oak lobby bench: a buttoned oxblood velvet seat and back, carved oak ends, brass feet.
    anchor bottom-centre."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 2)
    # back
    cv.rect(ox + 6, 2, width - 12, 12, OUT)
    cv.rect(ox + 7, 3, width - 14, 10, VELVET_M[2]); cv.hline(ox + 7, 3, width - 14, VELVET_M[4])
    for bx in range(ox + 14, ox + width - 10, 12):
        cv.px(bx, 7, VELVET_M[0]); cv.px(bx + 6, 10, VELVET_M[0])
    cv.rect(ox + 6, 0, width - 12, 3, OUT); cv.rect(ox + 7, 1, width - 14, 1, WOOD[4])
    # seat
    cv.rect(ox + 2, 14, width - 4, 8, OUT)
    cv.rect(ox + 3, 15, width - 6, 5, VELVET_M[3]); cv.hline(ox + 3, 15, width - 6, VELVET_M[5])
    cv.hline(ox + 3, 19, width - 6, VELVET_M[1])
    cv.rect(ox + 2, 21, width - 4, 3, WOOD[3]); cv.hline(ox + 2, 21, width - 4, WOOD[5]); cv.hline(ox + 2, 23, width - 4, WOOD[1])
    # carved oak ends and a middle leg
    for lx in (ox, ox + width - 7, ox + width // 2 - 3):
        cv.rect(lx, 6 if lx != ox + width // 2 - 3 else 21, 7, base - (6 if lx != ox + width // 2 - 3 else 21), OUT)
        y0 = 7 if lx != ox + width // 2 - 3 else 22
        cv.rect(lx + 1, y0, 5, base - y0 - 3, WOOD[3]); cv.vline(lx + 1, y0, base - y0 - 3, WOOD[5])
        cv.rect(lx + 1, base - 3, 5, 2, BRASS[2]); cv.hline(lx + 1, base - 3, 5, BRASS[4])
    for lx in (ox, ox + width - 7):
        cv.ellipse(lx, 3, 7, 7, OUT); cv.ellipse(lx + 1, 4, 5, 5, WOOD[4]); cv.px(lx + 3, 6, WOOD[2])
    return cv, ox + width // 2, base


# --- the cloakroom (M03) ------------------------------------------------------------------------
COATS = ["#2a2a3a", "#3a2a2a", "#4a3a2a", "#2c3a4a", "#5a2a2e", "#3a4a3a", "#6a5a44", "#4a4a52", "#7a4a2a",
         "#1e1e26", "#5a4a5e", "#8a6a4a"]
GOWN = ["#121018", "#1c1a24", "#2a2632"]           # black graduation gowns
TICKET_RED = ["#7a2a26", "#a83c32", "#c85a48", "#e8a090"]
CARD = ["#8a7a68", "#c8b896", "#efe4cc", "#fbf4e2"]


def _coat(cv, cx, rail, length, colour, rng, gown=False, tag=None):
    """One coat (or graduation gown) on a hanger below the rail at row `rail`, facing us: hook and
    hanger, rounded shoulders, sleeves down both sides, lapels and buttons (or the gown's gold
    stole and bell sleeves), a cream ticket tag on the hook."""
    hw = int(rng.integers(8, 11))
    c0 = GOWN[1] if gown else colour
    dark, darker, light = shade(c0, -0.25), shade(c0, -0.45), shade(c0, 0.2)
    top, bot = rail + 3, rail + 3 + length
    cv.px(cx, rail - 1, IRON[4]); cv.px(cx, rail, IRON[3]); cv.px(cx, rail + 1, IRON[3])
    for yy in range(top, bot):
        t = (yy - top) / max(1, length)
        w_ = hw - 3 + min(3, yy - top) + int(t * 2.5)
        cv.hline(cx - w_ - 1, yy, 2 * w_ + 3, OUT)
        cv.hline(cx - w_, yy, 2 * w_ + 1, c0)
        # sleeves hang down the sides to about two thirds of the length
        if t < (0.85 if gown else 0.68) and yy > top + 2:
            sw = 3 + (int(t * 4) if gown else 0)
            cv.hline(cx - w_, yy, sw, dark); cv.hline(cx + w_ - sw + 1, yy, sw, darker)
            cv.px(cx - w_ + sw, yy, OUT); cv.px(cx + w_ - sw, yy, OUT)
        cv.px(cx - w_ + (4 if t < 0.68 else 1), yy, light)
    cv.hline(cx - hw + 2, top, 2 * hw - 3, OUT)
    cv.hline(cx - hw - 2, bot, 2 * hw + 5, OUT)
    if gown:
        for side in (-1, 1):
            cv.line(cx + side * 2, top + 1, cx + side * 3, top + 16, "#d8b45a")
            cv.line(cx + side * 3, top + 1, cx + side * 4, top + 16, "#b8913a")
        cv.vline(cx, top + 2, length - 3, GOWN[0])
    else:
        # lapels in a V, buttons, pocket flaps
        for k in range(8):
            cv.px(cx - 4 + k // 2, top + 1 + k, light); cv.px(cx + 4 - k // 2, top + 1 + k, dark)
        cv.vline(cx, top + 8, length - 10, darker)
        for by in range(top + 11, bot - 4, 6):
            cv.px(cx + 1, by, shade(c0, 0.45))
        py = top + int(length * 0.62)
        cv.hline(cx - hw + 5, py, 4, darker); cv.hline(cx + hw - 8, py, 4, darker)
    if tag:
        cv.rect(cx + 1, rail - 3, 5, 6, OUT); cv.rect(cx + 2, rail - 2, 3, 4, tag); cv.px(cx + 3, rail - 1, TICKET_RED[1])


def coat_rack(width=160, height=110, fullness=1.0, seed=0):
    """A double rolling cloakroom rack: iron frame on casters, a hat shelf on top with hats,
    mortarboards and hat boxes, a long rail packed with coats and black graduation gowns, each with
    a cream ticket tag. fullness < 1 leaves empty hangers (guests have collected their coats)."""
    rng = _rng(seed)
    cv = Canvas(width + 6, height + 4, seed=seed)
    ox, base = 3, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    shelf_y = base - height + 14
    rail = shelf_y + 8
    # uprights and base
    for px_ in (ox + 2, ox + width - 5):
        cv.rect(px_ - 1, shelf_y - 2, 5, base - shelf_y - 2, OUT); cv.vline(px_ + 1, shelf_y - 1, base - shelf_y - 4, IRON[3]); cv.vline(px_, shelf_y - 1, base - shelf_y - 4, IRON[4])
    cv.rect(ox, base - 7, width, 4, OUT); cv.hline(ox + 1, base - 6, width - 2, IRON[3])
    for wx in (ox + 3, ox + width // 3, ox + 2 * width // 3, ox + width - 6):
        cv.ellipse(wx - 2, base - 4, 5, 5, OUT); cv.px(wx, base - 2, IRON[4])
    # hat shelf with hats, mortarboards and boxes
    cv.rect(ox - 2, shelf_y - 2, width + 4, 4, OUT); cv.rect(ox - 1, shelf_y - 1, width + 2, 2, WOOD[4]); cv.hline(ox - 1, shelf_y - 1, width + 2, WOOD[5])
    x = ox + 4
    while x < ox + width - 14:
        kind = rng.choice(["board", "board", "hat", "box", "gap"]) if fullness > 0.5 else rng.choice(["gap", "gap", "board", "box"])
        if kind == "board":
            cv.poly([(x, shelf_y - 4), (x + 6, shelf_y - 7), (x + 13, shelf_y - 4), (x + 6, shelf_y - 2)], GOWN[1])
            cv.hline(x + 1, shelf_y - 4, 11, GOWN[2]); cv.rect(x + 3, shelf_y - 3, 7, 2, GOWN[0])
            cv.px(x + 6, shelf_y - 5, "#d8b45a"); cv.vline(x + 11, shelf_y - 4, 4, "#d8b45a")
            x += 15
        elif kind == "hat":
            col = COATS[int(rng.integers(len(COATS)))]
            cv.ellipse(x, shelf_y - 4, 14, 4, shade(col, -0.2)); cv.rect(x + 3, shelf_y - 8, 8, 5, col); cv.hline(x + 3, shelf_y - 5, 8, "#5a2a2e")
            x += 16
        elif kind == "box":
            bw = int(rng.integers(12, 18))
            col = ["#c8b896", "#8a5a4a", "#5a6a7a"][int(rng.integers(3))]
            cv.rect(x, shelf_y - 9, bw, 8, OUT); cv.rect(x + 1, shelf_y - 8, bw - 2, 6, col); cv.hline(x + 1, shelf_y - 8, bw - 2, shade(col, 0.2))
            cv.hline(x + 1, shelf_y - 5, bw - 2, shade(col, -0.2))
            x += bw + 2
        else:
            x += 10
    # the rail and its coats
    cv.rect(ox, rail - 1, width, 3, OUT); cv.hline(ox + 1, rail, width - 2, IRON[4])
    x = ox + 8
    i = 0
    while x < ox + width - 7:
        if rng.random() < fullness:
            gown = rng.random() < 0.3
            length = int(rng.integers(44, 62)) if not gown else int(rng.integers(58, 68))
            length = min(length, base - rail - 14)
            _coat(cv, x, rail + 1, length, COATS[int(rng.integers(len(COATS)))], rng, gown=gown,
                  tag=CARD[2] if rng.random() < 0.85 else None)
        else:
            # an empty hanger, a little askew
            cv.px(x, rail + 1, IRON[3])
            tilt = int(rng.integers(-1, 2))
            cv.line(x - 6, rail + 5 + tilt, x, rail + 2, IRON[4]); cv.line(x, rail + 2, x + 6, rail + 5 - tilt, IRON[4])
            cv.line(x - 6, rail + 5 + tilt, x + 6, rail + 5 - tilt, IRON[3])
        x += int(rng.integers(11, 15))
        i += 1
    return cv, ox + width // 2, base


def ticket_table(width=190, height=48, freed=False, seed=0):
    """The ticket sorting table: an oak table with a felt top; stacks and spills of red ADMIT
    tickets, a ticket spike, a roll of tickets, a brass bell, a cash tin and a rubber stamp.
    freed=True: the tickets are squared into neat fans of cream invitation cards tied with ribbon."""
    rng = _rng(seed)
    cv = Canvas(width + 6, height + 4, seed=seed)
    ox, base = 3, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top_y = base - height + 14
    depth = 14
    for lx in (ox + 6, ox + width - 11):
        cv.rect(lx, top_y + depth, 5, base - top_y - depth, OUT); cv.rect(lx + 1, top_y + depth, 3, base - top_y - depth - 1, WOOD[2]); cv.vline(lx + 1, top_y + depth, base - top_y - depth - 1, WOOD[4])
    cv.rect(ox + 10, base - 10, width - 20, 2, WOOD[1])
    cv.rect(ox, top_y - 1, width, depth + 6, OUT)
    cv.rect(ox + 1, top_y, width - 2, depth, "#2a4434"); cv.rect(ox + 3, top_y + 1, width - 6, depth - 2, "#365640")
    cv.rect(ox + 1, top_y + depth, width - 2, 4, WOOD[3]); cv.hline(ox + 1, top_y + depth, width - 2, WOOD[5]); cv.hline(ox + 1, top_y + depth + 3, width - 2, WOOD[1])
    cv.rect(ox + width // 2 - 10, top_y + depth + 1, 20, 2, WOOD[2]); cv.px(ox + width // 2, top_y + depth + 1, BRASS[4])
    y_ = top_y + 2
    if not freed:
        # spilled tickets everywhere, stacks, a spike full of stubs
        for _ in range(40):
            tx, ty = ox + 6 + int(rng.integers(0, width - 18)), y_ + int(rng.integers(0, depth - 5))
            c = TICKET_RED[int(rng.integers(1, 3))]
            cv.rect(tx, ty, 6, 3, c); cv.hline(tx, ty, 6, TICKET_RED[3]); cv.px(tx + 4, ty + 1, TICKET_RED[0])
        for (sx, n) in [(ox + 20, 6), (ox + 48, 9), (ox + width - 60, 7)]:
            for k in range(n):
                cv.rect(sx, y_ + 6 - k, 9, 3, TICKET_RED[1 + k % 2]); cv.hline(sx, y_ + 6 - k, 9, TICKET_RED[3])
        spx = ox + width - 30
        cv.rect(spx - 3, y_ + 7, 7, 2, IRON[2]); cv.vline(spx, y_ - 8, 15, IRON[4])
        for k in range(6):
            cv.rect(spx - 3, y_ + 4 - k * 2, 7, 2, TICKET_RED[1 + k % 2])
        # the roll of tickets unwinding off the edge
        rx = ox + width // 2 + 20
        cv.ellipse(rx - 5, y_ - 2, 11, 9, OUT); cv.ellipse(rx - 4, y_ - 1, 9, 7, TICKET_RED[1]); cv.ellipse(rx - 1, y_ + 1, 3, 3, TICKET_RED[0])
        for k in range(10):
            cv.rect(rx + 4 + k * 2, y_ + 6 + k, 3, 2, TICKET_RED[1 + (k // 2) % 2])
    else:
        # neat fans of cream invitations tied with red ribbon, a few left loose to take
        for (sx, n) in [(ox + 16, 5), (ox + 52, 5), (ox + width - 66, 5), (ox + width - 30, 4)]:
            for k in range(n):
                cv.rect(sx + k * 2, y_ + 5 - k, 12, 5, OUT); cv.rect(sx + k * 2 + 1, y_ + 5 - k, 10, 4, CARD[2]); cv.hline(sx + k * 2 + 1, y_ + 5 - k, 10, CARD[3])
                cv.px(sx + k * 2 + 9, y_ + 6 - k, "#d8b45a")
            cv.vline(sx + n + 4, y_ + 1, 8, TICKET_RED[1]); cv.px(sx + n + 3, y_ + 1, TICKET_RED[2]); cv.px(sx + n + 5, y_ + 1, TICKET_RED[2])
        for _ in range(5):
            tx, ty = ox + 30 + int(rng.integers(0, width - 60)), y_ + int(rng.integers(2, depth - 5))
            cv.rect(tx, ty, 10, 4, CARD[2]); cv.hline(tx, ty, 10, CARD[3]); cv.px(tx + 8, ty + 1, "#d8b45a")
    # the brass bell and a rubber stamp
    bx = ox + width // 2 - 14
    cv.ellipse(bx - 5, y_ + 1, 11, 7, OUT); cv.ellipse(bx - 4, y_ + 2, 9, 5, BRASS[3]); cv.px(bx - 1, y_ + 3, BRASS[4]); cv.rect(bx - 1, y_ - 1, 2, 2, BRASS[2])
    cv.rect(bx - 6, y_ + 6, 13, 2, OUT)
    sx = ox + width // 2 + 2
    cv.rect(sx, y_ + 2, 5, 3, "#2a2026"); cv.rect(sx + 1, y_ - 3, 3, 5, WOOD[3]); cv.ellipse(sx, y_ - 6, 5, 4, WOOD[4])
    return cv, ox + width // 2, base


def ask_first_board(width=96, height=56, label="ASK FIRST", lines=("TICKETS ARE", "INVITATIONS", "NOT ORDERS")):
    """A cloakroom A-frame chalkboard: oak frame, black board, the label in chalk capitals,
    three small chalk lines underneath. anchor bottom-centre."""
    cv = Canvas(width + 6, height + 4, seed=13)
    ox, base = 3, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2 - 6, 2)
    top = base - height
    # A-frame legs
    cv.line(ox + 6, base - 1, ox + 10, top + 4, OUT); cv.line(ox + width - 7, base - 1, ox + width - 11, top + 4, OUT)
    cv.line(ox + 7, base - 1, ox + 11, top + 4, WOOD[3]); cv.line(ox + width - 8, base - 1, ox + width - 12, top + 4, WOOD[2])
    bh = height - 10
    cv.rect(ox + 4, top, width - 8, bh, OUT)
    cv.rect(ox + 5, top + 1, width - 10, bh - 2, WOOD[3]); cv.hline(ox + 5, top + 1, width - 10, WOOD[5])
    cv.rect(ox + 8, top + 4, width - 16, bh - 8, "#1e2622")
    for k in range(6):
        cv.hline(ox + 10 + k * 13, top + 8 + (k * 7) % (bh - 14), 8, C("#c8d0c8", 0.08))
    chalk = "#e8ece0"
    text(cv, label, ox + width // 2 - text_width(label) // 2, top + 5, chalk)
    cv.hline(ox + width // 2 - text_width(label) // 2, top + 14, text_width(label) - 1, C(chalk, 0.5))
    for i, ln in enumerate(lines):
        text(cv, ln, ox + width // 2 - text_width(ln) // 2, top + 17 + i * 8, C("#b8c4b8", 0.85))
    cv.rect(ox + 10, top + bh - 4, 6, 2, "#f0f0e8")
    return cv, ox + width // 2, base


def cloak_counter(cv, x0, x1, base, top_h=40, seed=0):
    """The cloakroom counter built into the back wall: an oak half-height counter with a hinged
    flap, a brass rail, numbered brass hooks on the panelling behind, a call bell."""
    rng = _rng(seed)
    w = x1 - x0
    top = base - top_h
    cv.rect(x0, top, w, top_h, OUT)
    cv.rect(x0 + 1, top + 5, w - 2, top_h - 6, WOOD[2])
    for px_ in range(x0 + 4, x1 - 20, 28):
        cv.rect(px_, top + 10, 22, top_h - 16, WOOD[1]); cv.rect(px_ + 1, top + 11, 20, top_h - 18, WOOD[3])
        cv.hline(px_ + 1, top + 11, 20, WOOD[4]); cv.rect(px_ + 4, top + 14, 14, top_h - 24, WOOD[2])
    cv.rect(x0 - 2, top, w + 4, 6, OUT); cv.rect(x0 - 1, top + 1, w + 2, 4, WOOD[4]); cv.hline(x0 - 1, top + 1, w + 2, WOOD[5])
    cv.hline(x0, top + 7, w, BRASS[3]); cv.hline(x0, top + 8, w, BRASS[1])
    # hinged flap: a break in the counter top
    fx = x0 + w // 2 - 14
    cv.vline(fx, top, 6, OUT); cv.vline(fx + 28, top, 6, OUT)
    cv.rect(fx + 10, top + 2, 8, 2, BRASS[3])


def hook_rows(cv, x0, x1, ys, seed=0, fullness=1.0):
    """Rows of numbered brass coat hooks on the panelling, coats on most of them."""
    rng = _rng(seed)
    n = 1
    for y in ys:
        cv.rect(x0, y - 2, x1 - x0, 4, WOOD[3]); cv.hline(x0, y - 2, x1 - x0, WOOD[5]); cv.hline(x0, y + 1, x1 - x0, WOOD[1])
        for x in range(x0 + 8, x1 - 6, 14):
            cv.px(x, y, BRASS[4]); cv.px(x, y + 1, BRASS[2]); cv.px(x + 1, y + 2, BRASS[2])
            cv.rect(x - 2, y - 7, 5, 4, BRASS[2]); cv.px(x, y - 6, "#2a1c10")
            if rng.random() < fullness:
                col = COATS[int(rng.integers(len(COATS)))]
                L = int(rng.integers(18, 26))
                for yy in range(y + 2, y + 2 + L):
                    hw = 4 + (yy - y) // 8
                    cv.hline(x - hw, yy, hw * 2 + 1, col)
                    cv.px(x - hw, yy, OUT); cv.px(x + hw, yy, OUT)
                cv.hline(x - 5, y + 2 + L, 11, OUT)
                cv.vline(x, y + 4, L - 4, shade(col, -0.3))
            n += 1


FLOOR_HONEY = ["#2e1d1c", "#563826", "#6a4430", "#764c36", "#82563c", "#8e6044"]


def board_floor(cv, x, y, w, h, seed=0, pal=FLOOR_HONEY):
    """Long oak floorboards running across the room, butt joints staggered, grain flecks, a nail
    head now and then (interior.plank_floor with its own palette)."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[2])
    yy = y
    while yy < y + h:
        rh = 7 + (1 if (yy - y) > h / 2 else 0)
        xx = x - int(rng.integers(0, 50))
        while xx < x + w:
            pl = int(rng.integers(50, 110))
            x0, x1 = max(x, xx), min(x + w, xx + pl)
            tone = pal[int(rng.choice([2, 3, 3, 4]))]
            cv.rect(x0, yy, x1 - x0, rh - 1, tone)
            cv.hline(x0, yy, x1 - x0, shade(tone, 0.08))
            for _ in range((x1 - x0) // 7):
                gx = x0 + int(rng.integers(0, max(1, x1 - x0 - 6)))
                cv.hline(gx, yy + 1 + int(rng.integers(0, rh - 2)), int(rng.integers(3, 8)), shade(tone, -0.08))
            if rng.random() < 0.25:
                cv.px(x0 + 3, yy + rh // 2, pal[0]); cv.px(x1 - 4, yy + rh // 2, pal[0])
            cv.vline(x1 - 1, yy, rh - 1, pal[1])
            xx += pl
        cv.hline(x, yy + rh - 1, w, pal[0])
        yy += rh


def oculus(cv, cx, cy, r=10, dawn=False, seed=0):
    """A small round window high in the wall: dressed stone ring, four-pane leading, sky."""
    cv.ellipse(cx - r - 4, cy - r - 4, 2 * r + 9, 2 * r + 9, DRESS[1])
    cv.ellipse(cx - r - 3, cy - r - 3, 2 * r + 7, 2 * r + 7, DRESS[4])
    cv.ellipse(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, FRAME)
    m = np.zeros((cv.h, cv.w), bool)
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    m = (xs - cx) ** 2 + (ys - cy) ** 2 <= r * r
    window_view(cv, cx - r, cy - r, 2 * r + 1, 2 * r + 1, dawn=dawn, seed=seed, mask=m)
    cv.vline(cx, cy - r, 2 * r + 1, FRAME); cv.hline(cx - r, cy, 2 * r + 1, FRAME)
    for k in range(5):
        cv.px(cx - r + 2 + k, cy - r + 6 - k, C("#c8d0f0" if not dawn else "#fff0d8", 0.35))


# --- orchestra pit (M04) ------------------------------------------------------------------------
CURTAIN = ["#240810", "#3e0e18", "#5c1420", "#7c1c28", "#9c2630", "#b8363a", "#d24e46"]  # house curtain
PIT_FLOOR = ["#20161a", "#302226", "#3c2a2e", "#483234", "#543c3a", "#604640"]             # stained pit boards
FELT = ["#1c1420", "#261a2a", "#302234", "#3a2a3e"]                                        # black stage felt
METER_ON = {"g": ("#4cc05a", "#8ef08a"), "a": ("#e8a034", "#f8d070"), "r": ("#e04434", "#ff9a7a")}
METER_OFF = {"g": "#1e3024", "a": "#3a2c18", "r": "#3c1a1c"}
STAND_GLOW = "#ffe2a0"
CHAIR = ["#141018", "#221a26", "#30242e", "#4a3438"]                                       # black chair frame / seat


def stage_curtain(cv, x0, x1, y0, y1, seed=0, glows=(), split=None, pal=CURTAIN):
    """The house curtain hanging to the stage floor: velvet folds of varied width, each lit on its
    crest and dark in its crease, darker toward the flies, warmed in stepped bands where the
    footlights catch the hem; a gold-fringed hem along the bottom. glows = [(x, reach)] footlight
    spots; split = x of the centre opening (a sliver of work light shows through)."""
    rng = _rng(seed)
    w, h = x1 - x0, y1 - y0
    idx = np.zeros((h, w), int)
    xx = -int(rng.integers(0, 10))
    crease = np.zeros(w, bool)
    while xx < w:
        fw = int(rng.integers(9, 17))
        for i in range(fw):
            if 0 <= xx + i < w:
                t = i / max(1, fw - 1)
                v = np.cos((t - 0.38) * np.pi * 1.1)
                idx[:, xx + i] = 1 + int(round(max(0.0, v) * 3))
        if 0 <= xx < w:
            crease[xx] = True
        xx += fw
    ys = np.arange(h)[:, None]
    idx = idx - (ys < h * 0.35) - (ys < h * 0.15)           # darker up toward the flies
    for (gx, reach) in glows:
        dx = (np.arange(w)[None, :] + x0 - gx) / reach
        dy = (h - ys) / (reach * 0.9)
        d = np.sqrt(dx ** 2 + dy ** 2)
        idx = idx + (d < 1.0) + (d < 0.6) + (d < 0.3)
    idx = np.clip(idx, 0, len(pal) - 1)
    idx[:, crease] = np.minimum(idx[:, crease], 1)
    for k in range(len(pal)):
        m = np.zeros((cv.h, cv.w), bool)
        sub = idx == k
        m[y0:y1, x0:x1] = sub
        cv.fill_mask(m, pal[k])
    if split is not None:
        cv.vline(split, y0, h, "#0c0408"); cv.vline(split + 1, y0 + h // 3, h - h // 3, C("#ffe8b0", 0.55))
        cv.vline(split - 1, y0, h, pal[0])
    # hem: a darker band, then a gold bullion fringe
    cv.rect(x0, y1 - 6, w, 2, pal[1])
    for x in range(x0, x1):
        cv.vline(x, y1 - 4, 4, BRASS[3] if (x // 2) % 2 else BRASS[2])
    cv.hline(x0, y1 - 4, w, BRASS[4])


def curtain_valance(cv, x0, x1, top, depth=16, swag=64, pal=CURTAIN):
    """The fixed pelmet across the top: swagged velvet, its lower edge in shallow scallops with a
    gold fringe, a tasselled cord where the swags meet."""
    for sx in range(x0, x1, swag):
        for x in range(sx, min(x1, sx + swag)):
            t = (x - sx) / swag
            edge = top + depth - 5 + int(round(5 * np.sin(np.pi * t)))
            for y in range(top, edge):
                band = int((y - top) / max(1, edge - top) * 4)
                cv.px(x, y, pal[[2, 4, 3, 5][band % 4]])
            cv.vline(x, edge, 3, BRASS[3] if x % 2 else BRASS[2]); cv.px(x, edge, BRASS[4])
        cv.vline(sx, top, depth + 4, BRASS[1])
        cv.rect(sx - 1, top + depth - 2, 3, 3, BRASS[4]); cv.rect(sx - 1, top + depth + 1, 3, 6, BRASS[3]); cv.vline(sx + 1, top + depth + 1, 6, BRASS[1])
    cv.hline(x0, top, x1 - x0, BRASS[2])


def proscenium_side(cv, x0, x1, y0, y1, inner="right", seed=0):
    """A slice of the gilt proscenium arch beside the curtain: cream plaster pilaster with gilt
    fluting and a rosette panel, a heavy gilt moulding along the edge next to the curtain."""
    pl = ["#3a2a28", "#5a4436", "#7a604a", "#957a5c", "#ae9270"]
    w = x1 - x0
    cv.rect(x0, y0, w, y1 - y0, pl[2])
    for k, fx in enumerate(range(x0 + 6, x1 - 8, 5)):
        cv.vline(fx, y0, y1 - y0, pl[1]); cv.vline(fx + 1, y0, y1 - y0, pl[3]); cv.vline(fx + 2, y0, y1 - y0, BRASS[2] if k % 2 else pl[3])
    edge = x1 - 8 if inner == "right" else x0
    cv.rect(edge, y0, 8, y1 - y0, BRASS[2]); cv.vline(edge + 1, y0, y1 - y0, BRASS[4]); cv.vline(edge + 3, y0, y1 - y0, BRASS[3])
    cv.vline(edge + 6, y0, y1 - y0, BRASS[1]); cv.vline(edge + 7 if inner == "right" else edge, y0, y1 - y0, OUT)
    for ry in range(y0 + 8, y1 - 6, 18):                   # gilt beads down the moulding
        cv.rect(edge + 2, ry, 4, 3, BRASS[3]); cv.px(edge + 3, ry, BRASS[4])
    cv.rect(x0, y1 - 4, w, 4, pl[1]); cv.hline(x0, y1 - 4, w, pl[3])


def footlight(cv, x, y):
    """A footlight hood on the apron edge (lamp hidden, pointing upstage): a dark half-drum with a
    lit lip."""
    cv.rect(x - 5, y - 4, 11, 4, OUT); cv.rect(x - 4, y - 3, 9, 3, IRON[2]); cv.hline(x - 4, y - 3, 9, IRON[3])
    cv.hline(x - 3, y - 5, 7, "#ffe6a8"); cv.px(x - 4, y - 4, "#f6cf7a"); cv.px(x + 4, y - 4, "#f6cf7a")


def apron_lip(cv, x0, x1, y, seed=0):
    """The front edge of the stage seen from the pit: the boards' edge, an oak nosing with a brass
    strip, and the shadow it casts on the pit wall. Returns the y of the shadow's foot."""
    cv.rect(x0, y, x1 - x0, 3, "#2a1c1e"); cv.hline(x0, y, x1 - x0, "#5a4038")
    cv.rect(x0, y + 3, x1 - x0, 8, WOOD[2]); cv.hline(x0, y + 3, x1 - x0, WOOD[4]); cv.hline(x0, y + 4, x1 - x0, WOOD[3])
    rng = _rng(seed)
    for _ in range((x1 - x0) // 9):
        gx = x0 + int(rng.integers(0, x1 - x0 - 6))
        cv.hline(gx, y + 5 + int(rng.integers(0, 4)), int(rng.integers(3, 9)), WOOD[1])
    cv.hline(x0, y + 9, x1 - x0, BRASS[3]); cv.hline(x0, y + 10, x1 - x0, BRASS[1])
    cv.rect(x0, y + 11, x1 - x0, 4, C(SHADOW, 0.55)); cv.rect(x0, y + 15, x1 - x0, 2, C(SHADOW, 0.3))
    return y + 17


def slat_wall(cv, x, y, w, h, seed=0, pitch=4):
    """Acoustic oak slats on black felt: vertical battens of varied tone with dark gaps, a few
    battens a shade lighter where they were replaced."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, FELT[0])
    for sx in range(x, x + w, pitch):
        tone = WOOD[int(rng.choice([1, 2, 2, 3]))]
        cv.rect(sx, y, pitch - 1, h, tone)
        cv.vline(sx, y, h, shade(tone, 0.08))
        if rng.random() < 0.5:
            cv.vline(sx + 1, y + int(rng.integers(0, h - 6)), int(rng.integers(3, 8)), shade(tone, -0.1))
    cv.hline(x, y, w, C(SHADOW, 0.5))


def meter_geometry(x, y, cols=24, segs=11, pitch=9, seg_pitch=4):
    """Where the applause meter's segments are: (inner_x, inner_y, inner_w, inner_h)."""
    return x + 12, y + 7, cols * pitch - 2, segs * seg_pitch - 1


def _seg_zone(k, segs):
    return "r" if k >= segs - 2 else ("a" if k >= segs - 4 else "g")


def applause_meter(cv, x, y, cols=24, segs=11, pitch=9, seg_pitch=4, label="APPLAUSE"):
    """The big LED level meter on the pit wall: a black bezel with screws, every segment drawn
    dark (green, amber, red zones), a dB scale on the right and a brass name plate below. The lit
    segments are blink-layer frames from meter_frame()."""
    ix, iy, iw, ih = meter_geometry(x, y, cols, segs, pitch, seg_pitch)
    w, h = iw + 24, ih + 14
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, "#2a2430"); cv.hline(x, y, w, "#4a4052"); cv.vline(x, y, h, "#3a3242")
    cv.rect(ix - 3, iy - 3, iw + 6, ih + 6, "#0c0a10")
    for (sx, sy) in [(x + 3, y + 3), (x + w - 4, y + 3), (x + 3, y + h - 4), (x + w - 4, y + h - 4)]:
        cv.px(sx, sy, "#8a8090")
    for c in range(cols):
        for k in range(segs):
            sx = ix + c * pitch
            sy = iy + ih - (k + 1) * seg_pitch + 1
            cv.rect(sx, sy, pitch - 2, seg_pitch - 1, METER_OFF[_seg_zone(k, segs)])
    for k in range(0, segs, 2):                              # scale ticks
        cv.hline(ix + iw + 4, iy + ih - (k + 1) * seg_pitch + 2, 3, "#8a8090")
    cv.hline(ix - 7, iy + ih - 2 * seg_pitch + 2, 3, "#8a8090")
    pw = text_width(label) + 10
    px_ = x + w // 2 - pw // 2
    cv.rect(px_, y + h, pw, 11, OUT); cv.rect(px_ + 1, y + h, pw - 2, 10, BRASS[2]); cv.hline(px_ + 1, y + h, pw - 2, BRASS[4])
    cv.hline(px_ + 1, y + h + 9, pw - 2, BRASS[1])
    text(cv, label, px_ + 5, y + h + 1, "#2a1a10")
    return (ix, iy, iw, ih)


def meter_frame(levels, peaks=None, segs=11, pitch=9, seg_pitch=4):
    """One frame of lit segments (transparent elsewhere) for a blink layer: levels[c] segments lit
    in column c, plus a single peak-hold segment at peaks[c]."""
    cols = len(levels)
    iw, ih = cols * pitch - 2, segs * seg_pitch - 1
    cv = Canvas(iw, ih)
    for c, lv in enumerate(levels):
        lit = list(range(int(lv)))
        if peaks is not None and peaks[c] > lv:
            lit.append(int(peaks[c]) - 1)
        for k in lit:
            if not (0 <= k < segs):
                continue
            z = _seg_zone(k, segs)
            sx, sy = c * pitch, ih - (k + 1) * seg_pitch + 1
            cv.rect(sx, sy, pitch - 2, seg_pitch - 1, METER_ON[z][0]); cv.hline(sx, sy, pitch - 2, METER_ON[z][1])
    return cv


def setlist_paper(lines, title="PROGRAM", w=62, h=50, strike=False, seed=0):
    """A programme sheet taped to the pit wall, typed in black with the title in red; strike=True
    crosses the lines through in red pencil (the endless one)."""
    cv = Canvas(w, h)
    cv.rect(0, 0, w, h, OUT); cv.rect(1, 1, w - 2, h - 2, CARD[2]); cv.hline(1, 1, w - 2, CARD[3]); cv.vline(w - 2, 2, h - 3, CARD[1])
    cv.rect(w // 2 - 6, 0, 12, 3, C("#e8e0c8", 0.8))       # tape
    text(cv, title, w // 2 - text_width(title) // 2, 3, "#a83c32")
    cv.hline(5, 12, w - 10, "#a83c32")
    for i, ln in enumerate(lines):
        col = "#2a2026"
        if ln.startswith("!"):
            ln, col = ln[1:], "#a83c32"
        text(cv, ln, 6, 14 + i * 8, col)
    return cv


def crt_monitor(cv, x, y, w=30, h=24):
    """The conductor's video monitor on a wall bracket: a squat grey CRT showing the empty stage in
    blue-white. Returns the screen centre (for a twinkle)."""
    cv.rect(x + w // 2 - 2, y - 10, 4, 10, IRON[1]); cv.rect(x + w // 2 - 8, y - 12, 16, 3, IRON[2])
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, "#4a4a56"); cv.hline(x, y, w, "#6a6a78"); cv.vline(x + w - 1, y, h, "#34343e")
    sx, sy, sw, sh = x + 3, y + 3, w - 10, h - 7
    cv.rect(sx, sy, sw, sh, "#24344a")
    cv.rect(sx, sy + sh - 6, sw, 6, "#3a5070")              # stage floor on the screen
    cv.rect(sx + 2, sy + 2, sw - 4, sh - 9, "#4a2a3a")        # the curtain, tiny
    cv.rect(sx + sw // 2 - 1, sy + sh - 8, 2, 3, "#e8f0ff")   # the ghost light on stage
    cv.hline(sx, sy, sw, "#6a8ab0")
    for yy in range(sy + 1, sy + sh, 2):
        cv.hline(sx, yy, sw, C("#000000", 0.15))
    cv.rect(x + w - 6, y + 4, 3, 2, "#2a2a30"); cv.rect(x + w - 6, y + 8, 3, 2, "#2a2a30"); cv.px(x + w - 5, y + h - 4, "#6aff8a")
    return (sx + sw // 2, sy + sh // 2)


def cue_light_box(cv, x, y, label="QUIET", lit=True):
    """A red lightbox cue sign on the wall (QUIET), lit from inside."""
    w = text_width(label) + 10
    cv.rect(x - 1, y - 1, w + 2, 14, OUT)
    cv.rect(x, y, w, 12, "#2a1a1c")
    cv.rect(x + 2, y + 2, w - 4, 8, "#e04434" if lit else "#5a2226")
    text(cv, label, x + 5, y + 2, "#ffe0c8" if lit else "#3a1a1c")
    if lit:
        cv.rect(x - 4, y - 3, w + 8, 18, C("#ff6040", 0.08))
    return (x + w // 2, y + 6)


def cable_coil(cv, x, y, colour="#c86a2a", r=7):
    """An extension cable hung in loops over a wall hook: three overlapping rings (the wall shows
    through the middle), the plug hanging below."""
    cv.rect(x - 1, y - 3, 3, 4, IRON[3]); cv.px(x, y - 4, IRON[4])
    yy, xx = np.mgrid[0:cv.h, 0:cv.w]
    for k, dx in enumerate((-2, 1, 0)):
        cx_, cy_ = x + dx, y + r + 1 + k
        d = ((xx - cx_) / (r - k * 0.5)) ** 2 + ((yy - cy_) / (r + 1.5)) ** 2
        ring = (d <= 1.0) & (d >= 0.5)
        cv.fill_mask(ring & (yy >= y), shade(colour, -0.35 + k * 0.12))
        inner = (d <= 0.8) & (d >= 0.62) & (yy >= y)
        cv.fill_mask(inner, shade(colour, k * 0.08))
        cv.fill_mask((d <= 1.0) & (d >= 0.85) & (yy < cy_) & (yy >= y), shade(colour, 0.22))
    cv.line(x + 3, y + 2 * r + 3, x + 5, y + 2 * r + 10, colour); cv.rect(x + 4, y + 2 * r + 10, 3, 4, "#d8d0c0")


def concert_poster(cv, x, y, w=46, h=60, title="CONCERT", seed=0):
    """An old framed concert bill: cream paper, a big cello silhouette, the title in red, small
    lines of programme below."""
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT); cv.rect(x - 1, y - 1, w + 2, h + 2, BRASS[2]); cv.hline(x - 1, y - 1, w + 2, BRASS[4])
    cv.rect(x, y, w, h, "#e8d8b4"); cv.hline(x, y, w, "#f4e8cc")
    text(cv, title, x + w // 2 - text_width(title) // 2, y + 2, "#a83c32")
    cx_ = x + w // 2
    cv.ellipse(cx_ - 8, y + 26, 17, 16, "#5a2a1a"); cv.ellipse(cx_ - 6, y + 17, 13, 12, "#5a2a1a"); cv.rect(cx_ - 5, y + 24, 11, 6, "#5a2a1a")
    cv.rect(cx_ - 1, y + 12, 3, 9, "#2a1810"); cv.rect(cx_ - 2, y + 10, 5, 3, "#5a2a1a")
    cv.vline(cx_, y + 18, 20, "#e8d8b4"); cv.px(cx_ - 3, y + 29, "#e8d8b4"); cv.px(cx_ + 3, y + 29, "#e8d8b4")
    cv.vline(cx_, y + 42, 3, "#2a1810")
    for k in range(3):
        cv.hline(x + 6 + k * 2, y + 47 + k * 4, w - 12 - k * 4, "#8a7a62")


def pit_service_door(cv, cx, bottom, w=36, h=70, label="STAIR"):
    """The steel service door to the music stair: grey-green paint, a wired-glass light with the
    stairwell lamp behind it, a push bar, a lit STAIR sign above. Returns the sign's centre."""
    x, top = cx - w // 2, bottom - h
    cv.rect(x - 4, top - 4, w + 8, h + 4, IRON[1]); cv.hline(x - 4, top - 4, w + 8, IRON[3]); cv.vline(x - 4, top - 4, h + 4, IRON[3])
    cv.rect(x, top, w, h, OUT)
    cv.rect(x + 1, top + 1, w - 2, h - 1, "#3a4a44"); cv.vline(x + 1, top + 1, h - 1, "#4e625a"); cv.vline(x + w - 2, top + 1, h - 1, "#2a3632")
    gx, gy, gw, gh = x + 9, top + 8, w - 18, 18
    cv.rect(gx - 1, gy - 1, gw + 2, gh + 2, OUT); cv.rect(gx, gy, gw, gh, "#c8a060")
    cv.rect(gx, gy + gh // 2, gw, gh // 2, "#8a6a44")
    cv.line(gx, gy + gh - 2, gx + gw - 1, gy + 3, "#5a4430")   # the stair's string through the glass
    cv.line(gx, gy + gh - 6, gx + gw - 6, gy, "#5a4430")
    for k in range(gx + 2, gx + gw, 4):
        cv.vline(k, gy, gh, C("#2a2a30", 0.35))
    for k in range(gy + 2, gy + gh, 4):
        cv.hline(gx, k, gw, C("#2a2a30", 0.35))
    cv.rect(x + 3, top + 40, w - 6, 3, IRON[3]); cv.hline(x + 3, top + 40, w - 6, IRON[4])
    cv.rect(x + w - 8, top + 36, 3, 10, IRON[2])
    cv.rect(x + 1, bottom - 6, w - 2, 5, "#2a3632")
    cv.rect(x - 2, bottom - 1, w + 4, 1, BRASS[2])
    lw = text_width(label) + 8
    sx, sy = cx - lw // 2, top - 16
    cv.rect(sx - 1, sy - 1, lw + 2, 12, OUT); cv.rect(sx, sy, lw, 10, "#2c6a3a"); cv.hline(sx, sy, lw, "#5aa868")
    text(cv, label, sx + 4, sy + 1, "#e8ffe0")
    return (cx, sy + 5)


def pit_floor(cv, x, y, w, h, seed=0):
    """The pit's floor: stained boards worn by chair legs (board_floor in the pit palette)."""
    board_floor(cv, x, y, w, h, seed=seed, pal=PIT_FLOOR)


def spike_mark(cv, x, y, colour, kind="L"):
    """Coloured spike tape where a chair or stand belongs."""
    if kind == "L":
        cv.rect(x, y, 6, 2, colour); cv.rect(x, y, 2, 5, colour)
    elif kind == "T":
        cv.rect(x, y, 7, 2, colour); cv.rect(x + 2, y, 2, 5, colour)
    else:
        cv.rect(x, y, 5, 2, colour); cv.rect(x + 1, y - 1, 2, 4, colour)
    cv.px(x + 1, y, shade(colour, 0.3))


def gaff_cable(cv, pts, colour="#141018", tape="#3a3440", every=40):
    """A cable lying on the floor, taped down now and then."""
    from pixel import C as _C
    run = 0
    for (a, b) in zip(pts[:-1], pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], colour)
        cv.line(a[0], a[1] + 1, b[0], b[1] + 1, _C(SHADOW, 0.4))
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
        for i in range(0, n, 1):
            run += 1
            if run % every == 0:
                t = i / max(1, n)
                px_, py_ = int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t)
                cv.rect(px_ - 1, py_ - 2, 4, 5, tape); cv.hline(px_ - 1, py_ - 2, 4, shade(tape, 0.2))


def loose_sheet(cv, x, y, w=12, h=8, tilt=0, seed=0):
    """A page of sheet music dropped on the floor (staff lines in grey)."""
    pts = [(x, y + tilt), (x + w, y), (x + w + 1, y + h), (x + 1, y + h + tilt)]
    cv.poly([(px_ + 1, py_ + 1) for (px_, py_) in pts], C(SHADOW, 0.4))
    cv.poly(pts, CARD[2])
    for k in range(2, h - 1, 2):
        cv.line(x + 2, y + k + tilt, x + w - 2, y + k, CARD[0])
    cv.px(x + 4, y + 3 + tilt, "#2a2026"); cv.px(x + 7, y + 4, "#2a2026"); cv.px(x + 9, y + 2, "#2a2026")


# --- orchestra pit props ------------------------------------------------------------------------
def _pit_chair(cv, cx, base, lit=0.0, pad="#5a2a34"):
    """A black orchestra chair seen from the front (empty): backrest, padded seat, four legs. lit
    warms the seat where a stand light falls on it."""
    seat = base - 12
    for lx in (cx - 6, cx + 5):
        cv.vline(lx, seat, 12, CHAIR[0])                      # front legs
    for lx in (cx - 4, cx + 3):
        cv.vline(lx, seat + 1, 9, CHAIR[1])                   # back legs, shorter (further away)
    cv.rect(cx - 6, base - 23, 13, 9, CHAIR[0]); cv.rect(cx - 5, base - 22, 11, 7, CHAIR[2])
    cv.hline(cx - 5, base - 22, 11, hexmix(CHAIR[3], STAND_GLOW, lit * 0.35))
    cv.rect(cx - 7, seat - 2, 15, 3, CHAIR[0])
    cv.rect(cx - 6, seat - 2, 13, 2, hexmix(pad, STAND_GLOW, lit * 0.45))
    cv.hline(cx - 6, seat - 2, 13, hexmix(shade(pad, 0.2), STAND_GLOW, lit * 0.6))


def _stand(cv, cx, base, lit=True, h=30):
    """A music stand from behind (the player's side faces away): tripod legs, a pole, the desk's
    dark back plate, and the clip-on stand light glowing over its top edge."""
    top = base - h
    cv.line(cx, base - 6, cx - 5, base, OUT); cv.line(cx, base - 6, cx + 5, base, OUT); cv.line(cx, base - 6, cx + 1, base, IRON[1])
    cv.vline(cx, top + 10, h - 16, IRON[2])
    cv.rect(cx - 9, top + 2, 19, 11, OUT); cv.rect(cx - 8, top + 3, 17, 9, "#2a2832"); cv.hline(cx - 8, top + 3, 17, "#46424e")
    cv.hline(cx - 8, top + 11, 17, "#1a1820")
    if lit:
        cv.rect(cx - 3, top, 7, 3, OUT); cv.hline(cx - 2, top + 1, 5, IRON[3])
        cv.hline(cx - 7, top + 1, 15, "#b08a58")                # the music's top edge, lit
        cv.hline(cx - 8, top + 2, 17, STAND_GLOW)
        cv.px(cx - 9, top + 2, "#f6cf7a"); cv.px(cx + 9, top + 2, "#f6cf7a")


def _harp(cv, x, base, h=70):
    """A concert harp in profile: gilt column on the right, a carved crown, the curved neck, the
    slanting soundboard, strings between, a pedal base."""
    colx = x + 30
    top = base - h
    cv.rect(x + 2, base - 5, 34, 5, OUT); cv.rect(x + 3, base - 4, 32, 3, WOOD[2]); cv.hline(x + 3, base - 4, 32, BRASS[3])
    for k in range(5):
        cv.px(x + 8 + k * 5, base - 1, BRASS[4])               # pedals
    # soundboard: thick slanting body from the base up to the neck's far end
    for t in np.linspace(0, 1, 120):
        sx = int(round(x + 24 - t * 20)); sy = int(round(base - 5 - t * (h - 22)))
        cv.rect(sx - 1, sy, 5 - int(t * 2), 2, WOOD[3])
        cv.px(sx - 2, sy, OUT); cv.px(sx + 3 - int(t * 2), sy, WOOD[1])
    # neck: an S-curve from the column top down to the soundboard top
    sbx, sby = x + 4, base - 5 - (h - 22)
    pts = []
    for t in np.linspace(0, 1, 60):
        px_ = colx + (sbx - colx) * t
        py_ = top + 4 + (sby - top - 4) * t - 6 * np.sin(np.pi * t) + 3 * np.sin(2 * np.pi * t)
        pts.append((int(round(px_)), int(round(py_))))
    for (px_, py_) in pts:
        cv.rect(px_, py_ - 1, 2, 4, WOOD[3]); cv.px(px_, py_ - 2, OUT); cv.px(px_, py_ + 3, OUT); cv.px(px_, py_ - 1, BRASS[3])
    # strings from the neck down to the soundboard
    for k, sx in enumerate(range(sbx + 4, colx - 1, 2)):
        ny = min(py_ for (px_, py_) in pts if abs(px_ - sx) <= 1) + 3
        t = (x + 24 - sx) / 20.0
        sy = int(round(base - 5 - t * (h - 22)))
        cv.vline(sx, ny, max(0, sy - ny), "#e8d8b8" if k % 7 else "#c84a3c")
    # gilt column with a crown
    cv.rect(colx - 1, top + 2, 5, h - 7, OUT); cv.rect(colx, top + 3, 3, h - 9, BRASS[3]); cv.vline(colx, top + 3, h - 9, BRASS[4])
    for yy in range(top + 14, base - 8, 9):
        cv.hline(colx, yy, 3, BRASS[1])
    cv.rect(colx - 3, top - 3, 9, 7, OUT); cv.rect(colx - 2, top - 2, 7, 5, BRASS[3]); cv.hline(colx - 2, top - 2, 7, BRASS[4])
    cv.px(colx - 1, top - 4, BRASS[4]); cv.px(colx + 1, top - 5, BRASS[4]); cv.px(colx + 3, top - 4, BRASS[4])


def _timpani(cv, cx, base, r=13):
    """A kettledrum: copper bowl on three legs, a cream calfskin head, tuning rods round the rim."""
    rim = base - 18
    cv.line(cx - r + 3, rim + 8, cx - r + 1, base, OUT); cv.line(cx + r - 3, rim + 8, cx + r - 1, base, OUT); cv.vline(cx, rim + 10, base - rim - 10, OUT)
    cv.rect(cx - 4, base - 3, 9, 3, OUT)                       # pedal
    cv.ellipse(cx - r, rim - 4, 2 * r + 1, 2 * r - 2, OUT)
    cv.ellipse(cx - r + 1, rim - 3, 2 * r - 1, 2 * r - 4, "#a8582a")
    cv.ellipse(cx - r + 3, rim - 3, 2 * r - 9, 2 * r - 8, "#c8783a")
    cv.ellipse(cx - r + 5, rim - 1, 5, 7, "#f0b070")
    cv.rect(cx - r, rim - 6, 2 * r + 1, 6, C("#000000", 0))
    cv.ellipse(cx - r, rim - 6, 2 * r + 1, 9, OUT)
    cv.ellipse(cx - r + 1, rim - 5, 2 * r - 1, 7, "#e8dcc0"); cv.ellipse(cx - r + 4, rim - 4, 2 * r - 9, 4, "#f6ecd4")
    for k in range(-r + 2, r - 1, 5):
        cv.vline(cx + k, rim, 6, IRON[3])
    cv.hline(cx - r + 1, rim + 1, 2 * r - 1, IRON[2])


def _double_bass(cv, x, base, h=60):
    """An upright bass resting on its endpin: varnished body with f-holes, black fingerboard up the
    neck to the scroll, strings."""
    cx = x + 11
    btop = base - 36
    cv.vline(cx, base - 3, 3, IRON[3])
    cv.ellipse(cx - 11, btop + 12, 23, 22, OUT); cv.ellipse(cx - 9, btop + 2, 19, 16, OUT)
    cv.ellipse(cx - 10, btop + 13, 21, 20, "#8a3a1a"); cv.ellipse(cx - 8, btop + 3, 17, 14, "#8a3a1a")
    cv.rect(cx - 7, btop + 13, 15, 4, "#8a3a1a")
    cv.ellipse(cx - 7, btop + 15, 7, 12, "#b05a2a"); cv.ellipse(cx - 5, btop + 4, 6, 8, "#b05a2a")
    cv.px(cx - 4, btop + 17, "#e89a5a"); cv.px(cx - 5, btop + 18, "#e89a5a")
    for fx in (cx - 5, cx + 5):
        cv.vline(fx, btop + 12, 8, "#1a0c08"); cv.px(fx, btop + 11, "#1a0c08"); cv.px(fx, btop + 20, "#1a0c08")
    cv.rect(cx - 3, btop + 22, 7, 2, "#2a1a10")                # bridge
    cv.rect(cx - 1, base - h, 3, h - 16, OUT); cv.vline(cx, base - h + 2, h - 18, "#1c1418")
    cv.vline(cx - 1, btop + 8, 16, "#e8d8b8"); cv.vline(cx + 1, btop + 8, 16, "#c8b898")
    cv.rect(cx - 2, base - h - 2, 5, 6, OUT); cv.rect(cx - 1, base - h - 1, 3, 4, "#8a3a1a"); cv.px(cx + 2, base - h + 1, BRASS[3])


def _cello_lying(cv, x, base):
    """A cello laid on its side on the floor, as cellists leave them."""
    cv.ellipse(x, base - 12, 20, 12, OUT); cv.ellipse(x + 15, base - 11, 17, 11, OUT)
    cv.ellipse(x + 1, base - 11, 18, 10, "#9a4620"); cv.ellipse(x + 16, base - 10, 15, 9, "#9a4620")
    cv.ellipse(x + 3, base - 10, 10, 4, "#c06a30"); cv.ellipse(x + 18, base - 9, 8, 3, "#c06a30")
    cv.rect(x + 31, base - 8, 22, 3, OUT); cv.hline(x + 31, base - 7, 22, "#1c1418")
    cv.rect(x + 52, base - 10, 5, 6, OUT); cv.rect(x + 53, base - 9, 3, 4, "#9a4620")
    cv.hline(x + 6, base - 6, 26, "#e8d8b8")


def _instrument_case(cv, x, base, w=16, colour="#1c1a24"):
    """A violin case left on a chair seat."""
    cv.rect(x, base - 5, w, 5, OUT); cv.rect(x + 1, base - 4, w - 2, 3, colour); cv.hline(x + 1, base - 4, w - 2, shade(colour, 0.2))
    cv.rect(x + w // 2 - 1, base - 6, 3, 2, BRASS[2])


def pit_riser(width=390, height=84, seed=0):
    """The orchestra's low riser in the pit: a dark deck with a white safety edge, two rows of empty
    chairs facing the conductor in pairs, each pair sharing a music stand whose clip light still glows
    over the music and throws a warm pool on the deck; a harp at the left end, a double bass resting
    and the timpani at the right, a cello laid on its side, cases and a jacket left on seats.
    Returns (Canvas, ax, ay)."""
    rng = _rng(seed)
    W_, H_ = width + 4, height + 4
    cv = Canvas(W_, H_, seed=seed)
    ox, base = 2, H_ - 2
    face, deck = base - 8, base - 36
    # deck and front face
    cv.rect(ox, deck - 1, width, face - deck + 1, OUT)
    cv.rect(ox + 1, deck, width - 2, face - deck, "#30282e")
    for yy in range(deck + 4, face, 5):
        cv.hline(ox + 1, yy, width - 2, "#282026")
    for _ in range(width // 10):
        sx = ox + int(rng.integers(4, width - 10))
        cv.hline(sx, deck + 1 + int(rng.integers(0, face - deck - 2)), int(rng.integers(3, 9)), "#3a3036")
    cv.hline(ox + 1, deck, width - 2, "#4a3e46")
    cv.rect(ox, face, width, base - face, OUT); cv.rect(ox + 1, face + 1, width - 2, base - face - 2, "#1c161e")
    cv.hline(ox + 1, face, width - 2, "#e8e4d8"); cv.hline(ox + 1, face + 1, width - 2, "#a8a498")      # safety edge tape
    for sx in range(ox + 30, ox + width - 20, 64):
        cv.rect(sx, face + 3, 10, 3, "#2a242c")
    lx0, lx1 = ox + 58, ox + width - 84
    rows = [(deck + 11, 5, 0), (deck + 24, 4, 1)]         # (chair feet y, pairs, row)
    pairs = []
    for (cy, n, r) in rows:
        for i in range(n):
            cx = int(lx0 + (i + 0.5 + 0.5 * r) * (lx1 - lx0) / (n + 0.5 * r)) + int(rng.integers(-3, 4))
            pairs.append((cx, cy, rng.random() < 0.85))
    # warm pools first (stepped, two tones) so everything stands on them
    for (cx, cy, lit) in pairs:
        if lit:
            cv.ellipse(cx - 20, cy - 3, 41, 10, "#3e3034"); cv.ellipse(cx - 13, cy - 1, 27, 7, "#4e3a36")
    for (cx, cy, lit) in pairs:
        for k, dx in enumerate((-8, 8)):
            jitter = int(rng.integers(-1, 2))
            _pit_chair(cv, cx + dx + jitter, cy, lit=1.0 if lit else 0.2)
            pick = rng.random()
            if pick < 0.16:
                _instrument_case(cv, cx + dx - 7, cy - 14, 15)
            elif pick < 0.26:
                cv.rect(cx + dx - 5, cy - 16, 10, 3, CARD[2]); cv.hline(cx + dx - 5, cy - 16, 10, CARD[3])
            elif pick < 0.32:
                jc = COATS[int(rng.integers(len(COATS)))]
                cv.rect(cx + dx - 6, cy - 24, 13, 8, OUT); cv.rect(cx + dx - 5, cy - 23, 11, 6, jc); cv.hline(cx + dx - 5, cy - 23, 11, shade(jc, 0.25))
        _stand(cv, cx, cy + 7, lit=lit, h=24)
    # the harp at the left end, the bass and timpani at the right
    _harp(cv, ox + 8, deck + 26, h=74)
    _double_bass(cv, ox + width - 74, deck + 22, h=60)
    _timpani(cv, ox + width - 36, deck + 16, r=12)
    _timpani(cv, ox + width - 22, deck + 30, r=13)
    _cello_lying(cv, ox + 150, deck + 33)
    cv.rect(ox + 60, deck + 31, 14, 3, CARD[2]); cv.hline(ox + 60, deck + 31, 14, CARD[3])          # dropped part
    cv.rect(ox + 262, deck + 30, 3, 5, "#6a9ac8"); cv.px(ox + 263, deck + 29, "#d8e8f0")              # water bottle
    return cv, ox + width // 2, base


def pa_stack(width=42, height=100, seed=0, lit_side="right"):
    """A pit PA: a subwoofer cabinet on the floor, a pole, a full-range box on top with its horn and
    woofer behind black grille, a blue power LED; the side facing the orchestra catches the stand
    lights. Returns (Canvas, ax, ay)."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 + 1, 2)
    rim = STAND_GLOW

    def cabinet(x, y, w, h):
        cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
        cv.rect(x, y, w, h, "#24222c"); cv.hline(x, y, w, "#46424e")
        cv.rect(x + 3, y + 3, w - 6, h - 6, "#16141c")
        for gy in range(y + 4, y + h - 3, 2):
            cv.hline(x + 3, gy, w - 6, "#1e1c26")
        for (kx, ky) in [(x, y), (x + w - 3, y), (x, y + h - 3), (x + w - 3, y + h - 3)]:
            cv.rect(kx, ky, 3, 3, IRON[3]); cv.px(kx + 1, ky + 1, IRON[4])      # corner protectors
        if lit_side == "right":
            cv.vline(x + w - 1, y + 3, h - 6, hexmix("#24222c", rim, 0.45))
        else:
            cv.vline(x, y + 3, h - 6, hexmix("#24222c", rim, 0.45))

    sub_h = 34
    cabinet(ox, base - sub_h, width, sub_h)
    cv.ellipse(cx - 13, base - sub_h + 4, 27, 27, "#22202a"); cv.ellipse(cx - 9, base - sub_h + 8, 19, 19, "#1a1820")
    cv.ellipse(cx - 3, base - sub_h + 14, 7, 7, "#2c2a34")
    cv.rect(ox + 6, base - 4, width - 12, 2, IRON[1])
    cv.rect(cx - 9, base - sub_h - 1, 18, 2, IRON[3])            # pole socket
    top_h, top_w = 50, width - 6
    ty = base - height + 2
    cv.rect(cx - 1, ty + top_h, 3, base - sub_h - ty - top_h, OUT); cv.vline(cx, ty + top_h, base - sub_h - ty - top_h, IRON[4])
    cabinet(cx - top_w // 2, ty, top_w, top_h)
    tx = cx - top_w // 2
    cv.ellipse(cx - 11, ty + 22, 23, 23, "#22202a"); cv.ellipse(cx - 7, ty + 26, 15, 15, "#1a1820"); cv.ellipse(cx - 2, ty + 31, 5, 5, "#2c2a34")
    cv.rect(tx + 6, ty + 5, top_w - 12, 12, "#1a1820"); cv.rect(tx + 9, ty + 7, top_w - 18, 8, "#0e0c12")
    cv.hline(tx + 9, ty + 7, top_w - 18, "#2a2834")
    cv.rect(tx + 4, ty + top_h - 6, 6, 2, "#c8c4d0")              # badge
    cv.px(tx + top_w - 6, ty + top_h - 5, "#5ac8ff"); cv.px(tx + top_w - 6, ty + top_h - 6, C("#5ac8ff", 0.4))
    # cable down the pole
    for yy in range(ty + top_h, base - sub_h):
        cv.px(cx + 3, yy, "#0e0c12")
    return cv, cx, base


def score_table(width=210, height=48, ready=False, seed=0):
    """The conductor's long table at the front of the pit: oak top on trestles, the full score open
    on a slanted desk facing the podium side, a brass piano lamp bent over it, pencils, a baton, a
    metronome, stacks of parts, a mug. Before Imani chooses, the score is dense black with no rests
    and its pages spill over the front edge in an endless fold; once ready it has rests, a final
    double bar and FINE in red pencil, the spill gathered into a neat stack. Returns (Canvas, ax, ay)."""
    rng = _rng(seed)
    W_, H_ = width + 6, height + 6
    cv = Canvas(W_, H_, seed=seed)
    ox, base = 3, H_ - 3
    cx = ox + width // 2
    top = base - 24                                              # table surface (seen from above)
    ground_shadow(cv, cx, base, width // 2 - 4, 3)
    # trestle legs
    for lx in (ox + 14, ox + width - 20):
        cv.rect(lx, top + 8, 6, base - top - 8, OUT); cv.rect(lx + 1, top + 8, 4, base - top - 9, WOOD[2]); cv.vline(lx + 1, top + 8, base - top - 9, WOOD[3])
        cv.rect(lx - 4, base - 3, 14, 3, OUT); cv.hline(lx - 3, base - 3, 12, WOOD[3])
    cv.rect(ox + 18, base - 14, width - 34, 3, OUT); cv.hline(ox + 19, base - 13, width - 36, WOOD[2])        # stretcher
    # top: surface band and front edge
    cv.rect(ox, top - 1, width, 10, OUT)
    cv.rect(ox + 1, top, width - 2, 6, WOOD[3]); cv.hline(ox + 1, top, width - 2, WOOD[4])
    for _ in range(width // 10):
        gx = ox + int(rng.integers(3, width - 10))
        cv.hline(gx, top + 1 + int(rng.integers(0, 4)), int(rng.integers(4, 10)), WOOD[2])
    cv.rect(ox + 1, top + 6, width - 2, 2, WOOD[1]); cv.hline(ox + 1, top + 6, width - 2, WOOD[5])
    # the slanted score desk with the open full score
    dw, dh = 76, 22
    dx, dy = cx - dw // 2, top - dh + 2
    cv.rect(dx - 1, dy - 1, dw + 2, dh + 2, OUT); cv.rect(dx, dy, dw, dh, WOOD[2]); cv.hline(dx, dy + dh - 3, dw, BRASS[2])
    pw = dw // 2 - 3
    for side, px_ in enumerate((dx + 2, dx + dw // 2 + 1)):
        cv.rect(px_, dy + 1, pw, dh - 5, CARD[2]); cv.hline(px_, dy + 1, pw, CARD[3])
        if side == 0:
            cv.vline(px_ + pw - 1, dy + 1, dh - 5, CARD[1])
        for s, sy in enumerate((dy + 3, dy + 10)):
            for k in range(0, 5, 2):
                cv.hline(px_ + 1, sy + k, pw - 2, CARD[0])
            if ready:
                # phrases with breaths: note groups, then a rest, a bar line
                for nx in range(px_ + 2, px_ + pw - 2, 3):
                    gap = (nx - px_) % 14 > 9
                    if gap and s == side:
                        cv.rect(nx, sy + 1, 2, 1, "#2a2026")          # a rest
                    elif not gap:
                        cv.px(nx, sy + int(rng.integers(0, 5)), "#1a1418")
            else:
                for nx in range(px_ + 1, px_ + pw - 1):
                    if rng.random() < 0.7:
                        cv.px(nx, sy + int(rng.integers(0, 5)), "#1a1418")
                    if rng.random() < 0.25:
                        cv.vline(nx, sy - 1, 3, "#1a1418")
        if side == 1:
            ex = px_ + pw - 3
            if ready:
                cv.vline(ex, dy + 3, 12, "#1a1418"); cv.vline(ex + 1, dy + 3, 12, "#1a1418"); cv.vline(ex - 2, dy + 3, 12, "#1a1418")
            else:
                cv.vline(ex, dy + 3, 12, "#1a1418"); cv.vline(ex + 1, dy + 3, 12, "#1a1418")      # repeat sign
                cv.px(ex - 2, dy + 5, "#1a1418"); cv.px(ex - 2, dy + 8, "#1a1418"); cv.px(ex - 2, dy + 12, "#1a1418")
    if ready:
        # FINE in red pencil on a slip clipped to the right page
        sx_ = dx + dw - 30
        cv.rect(sx_, dy + dh - 13, 27, 10, OUT); cv.rect(sx_ + 1, dy + dh - 12, 25, 8, "#fbf4e2")
        text(cv, "FINE", sx_ + 2, dy + dh - 13, "#c03a2e")
    else:
        # red pencil on the left page: ENCORE, again and again
        cv.hline(dx + 4, dy + dh - 6, 28, "#c03a2e"); cv.hline(dx + 6, dy + dh - 5, 22, "#c03a2e")
    # the pages hanging over the front edge: an endless fold, or a squared stack
    if not ready:
        for k in range(4):
            fx = cx - 30 + k * 13 + int(rng.integers(-2, 3))
            ln = 16 + int(rng.integers(0, 10))
            cv.rect(fx, top + 6, 11, ln, OUT); cv.rect(fx + 1, top + 6, 9, ln - 1, CARD[2] if k % 2 else CARD[3])
            for yy in range(top + 8, top + 5 + ln, 3):
                cv.hline(fx + 2, yy, 7, CARD[0]); cv.px(fx + 3 + (yy * 3) % 5, yy, "#1a1418")
    else:
        sx_ = ox + width - 64
        for k in range(4):
            cv.rect(sx_ - k, top - 4 - k * 2, 22, 3, OUT); cv.rect(sx_ + 1 - k, top - 4 - k * 2, 20, 2, CARD[2 + k % 2])
        cv.rect(sx_ + 6, top - 12, 8, 2, "#c03a2e")                   # a ribbon tied round them
    # brass piano lamp on the left of the desk, lit
    lx = dx - 18
    cv.rect(lx - 4, top - 1, 9, 3, OUT); cv.hline(lx - 3, top - 1, 7, BRASS[3])
    cv.vline(lx, top - 16, 15, BRASS[2]); cv.line(lx, top - 16, lx + 12, top - 22, BRASS[2])
    cv.rect(lx + 10, top - 25, 12, 5, OUT); cv.rect(lx + 11, top - 24, 10, 3, BRASS[3]); cv.hline(lx + 11, top - 24, 10, BRASS[4])
    cv.hline(lx + 11, top - 20, 10, STAND_GLOW)
    cv.rect(lx + 8, top - 19, 16, 3, C(STAND_GLOW, 0.2))
    # clutter: baton, pencils, metronome, mug, parts
    cv.line(cx - 22, top + 3, cx - 6, top + 1, "#f2ead8"); cv.px(cx - 23, top + 3, "#5a3a26")
    cv.hline(cx + 8, top + 2, 9, "#e8c040"); cv.px(cx + 17, top + 2, "#2a2026"); cv.hline(cx + 10, top + 4, 7, "#c03a2e")
    mx = ox + width - 30
    cv.poly([(mx, top + 3), (mx + 10, top + 3), (mx + 7, top - 14), (mx + 3, top - 14)], OUT)
    cv.poly([(mx + 1, top + 2), (mx + 9, top + 2), (mx + 6, top - 13), (mx + 4, top - 13)], WOOD[3])
    cv.rect(mx + 3, top - 6, 4, 6, CARD[2]); cv.line(mx + 5, top - 1, mx + 7, top - 12, BRASS[4])
    kx = ox + 16
    cv.rect(kx, top - 6, 8, 8, OUT); cv.rect(kx + 1, top - 5, 6, 6, "#e6dccb"); cv.hline(kx + 1, top - 5, 6, "#5a3a2a"); cv.px(kx + 8, top - 3, "#e6dccb")
    for k in range(3):
        cv.rect(ox + 30 - k, top - 2 - k * 2, 18, 2, CARD[2 + k % 2])
    return cv, cx, base


def rest_board(width=100, height=56, label="REST"):
    """The rehearsal blackboard on its stand: a staff ruled in white, chalk notes running along,
    then a bar with only a whole rest in it, and REST chalked above it in yellow with a ring round
    the silence. Returns (Canvas, ax, ay)."""
    W_, H_ = width + 4, height + 3
    cv = Canvas(W_, H_)
    ox, base = 2, H_ - 1
    bh = 42
    by = base - height
    ground_shadow(cv, ox + width // 2, base, width // 2 - 8, 2)
    for lx in (ox + 12, ox + width - 16):
        cv.rect(lx, by + bh - 2, 4, base - by - bh + 2, OUT); cv.vline(lx + 1, by + bh - 1, base - by - bh, WOOD[3])
        cv.rect(lx - 3, base - 2, 10, 2, OUT)
    cv.rect(ox, by, width, bh, OUT)
    cv.rect(ox + 1, by + 1, width - 2, bh - 2, WOOD[3]); cv.hline(ox + 1, by + 1, width - 2, WOOD[5])
    cv.rect(ox + 4, by + 4, width - 8, bh - 8, "#1e2e28")
    for (sx, sy, sw) in [(ox + 10, by + 30, 18), (ox + 60, by + 8, 22)]:
        cv.hline(sx, sy, sw, "#2c3e36")                                 # old smudges
    cv.rect(ox + 2, by + bh - 4, width - 4, 3, WOOD[2]); cv.hline(ox + 2, by + bh - 4, width - 4, WOOD[4])
    cv.rect(ox + 20, by + bh - 5, 6, 2, "#efe8d8"); cv.rect(ox + 70, by + bh - 5, 4, 2, "#f0d060")
    sy0 = by + 18
    for k in range(5):
        cv.hline(ox + 7, sy0 + k * 3, width - 14, "#a8b8b0")
    # clef-ish squiggle, notes, bar lines
    cv.vline(ox + 9, sy0 - 3, 17, "#e8ece4"); cv.px(ox + 10, sy0 + 2, "#e8ece4"); cv.px(ox + 11, sy0 + 4, "#e8ece4"); cv.px(ox + 10, sy0 + 7, "#e8ece4")
    bars = [ox + 34, ox + 58, ox + 82]
    for bx in bars + [ox + width - 8]:
        cv.vline(bx, sy0, 13, "#e8ece4")
    cv.vline(ox + width - 10, sy0, 13, "#e8ece4")
    notes = [(ox + 16, 6), (ox + 21, 4), (ox + 26, 7), (ox + 30, 3), (ox + 63, 8), (ox + 68, 6), (ox + 73, 4), (ox + 78, 2),
             (ox + 86, 5)]
    for (nx, ny) in notes:
        cv.rect(nx, sy0 + ny, 3, 2, "#f2f4ee"); cv.vline(nx + 2, sy0 + ny - 6, 6, "#f2f4ee")
    # the whole rest in the silent bar, ringed, and REST chalked above
    rx = (bars[0] + bars[1]) // 2
    cv.rect(rx - 3, sy0 + 3, 7, 2, "#f2f4ee")
    yy_, xx_ = np.mgrid[0:cv.h, 0:cv.w]
    inner = ((xx_ - rx) / 9.2) ** 2 + ((yy_ - sy0 - 5) / 6.2) ** 2 < 1
    outer = ((xx_ - rx) / 10.5) ** 2 + ((yy_ - sy0 - 5) / 7.5) ** 2 < 1
    cv.fill_mask(outer & ~inner, "#f0d060")
    text(cv, label, rx - text_width(label) // 2, by + 4, "#f0d060")
    cv.line(rx, by + 12, rx, sy0 - 4, "#f0d060")
    return cv, ox + width // 2, base


def ghost_light_m(height=68, seed=0):
    """The ghost light left burning in the pit for the night: a bare bulb in a wire cage on a brass
    pole, three feet on castors, the cable coiled at the foot, a luggage tag reading REST. The bulb
    centre sits height - 5 above the anchor. Returns (Canvas, ax, ay)."""
    w = 28
    H_ = height + 8
    cv = Canvas(w, H_, seed=seed)
    cx, base = w // 2, H_ - 3
    by = base - (height - 5)
    ground_shadow(cv, cx, base, 10, 2)
    for (fx, fy) in [(cx - 9, base - 1), (cx + 9, base - 1), (cx + 2, base)]:
        cv.line(cx, base - 8, fx, fy, OUT)
        cv.rect(fx - 1, fy - 1, 3, 3, OUT); cv.px(fx, fy, IRON[3])
    cv.rect(cx - 2, base - 10, 5, 3, OUT)
    cv.rect(cx - 1, by + 8, 3, base - by - 18, OUT); cv.vline(cx, by + 8, base - by - 18, BRASS[3])
    for yy in range(by + 12, base - 12, 11):
        cv.px(cx, yy, BRASS[4])
    cv.rect(cx - 2, by + 30, 5, 3, OUT); cv.hline(cx - 1, by + 31, 3, BRASS[2])
    for yy in range(by + 9, base - 6):
        cv.px(cx + 2, yy, "#1a1418")
    cv.ellipse(cx - 2, base - 6, 12, 5, "#1a1418"); cv.ellipse(cx, base - 5, 8, 3, "#2a2430")
    cv.rect(cx - 6, by + 33, 5, 7, OUT); cv.rect(cx - 5, by + 34, 3, 5, CARD[2]); cv.line(cx - 3, by + 33, cx, by + 31, "#c8b896")
    cv.ellipse(cx - 8, by - 9, 17, 17, C(STAND_GLOW, 0.14))
    cv.ellipse(cx - 6, by - 7, 13, 13, C(STAND_GLOW, 0.2))
    cv.rect(cx - 2, by + 3, 5, 5, OUT); cv.rect(cx - 1, by + 4, 3, 3, IRON[3])
    cv.ellipse(cx - 3, by - 4, 7, 8, "#ffe6a0"); cv.ellipse(cx - 2, by - 3, 4, 5, "#fff6d8"); cv.px(cx - 1, by - 2, "#ffffff")
    for k in (-4, 0, 4):
        cv.line(cx + k, by - 6 + abs(k) // 2, cx + k, by + 3, IRON[2])
    cv.hline(cx - 4, by - 6, 9, IRON[2]); cv.hline(cx - 4, by - 1, 9, IRON[1]); cv.hline(cx - 3, by + 2, 7, IRON[2])
    cv.rect(cx - 1, by - 9, 3, 3, IRON[2])
    return cv, cx, base


def endless_scroll(w=230, h=90, seed=0):
    """Pages of manuscript paper fanfolded off the score table and across the floor, one page after
    another in a meandering line: the score with no rests going on and on. Flat on the floor
    (pages foreshortened). Returns the Canvas; its top-right corner meets the table's front edge."""
    rng = _rng(seed)
    cv = Canvas(w, h)
    pages = []
    x, y = w - 16, 2
    dirx = -1
    for i in range(30):
        pages.append((x, y, i))
        x += dirx * int(rng.integers(9, 12))
        y += int(rng.integers(1, 4))
        if x < 8 or (i in (11, 21)):
            y += 3
        if y > h - 10:
            break
        if x < 8:
            break
    for (px_, py_, i) in pages:
        pw, ph = 13, 7
        lift = 0 if i % 2 else 1
        cv.rect(px_ + 1, py_ + 1, pw, ph, C(SHADOW, 0.35))
        cv.rect(px_, py_ - lift, pw, ph, OUT)
        cv.rect(px_ + 1, py_ + 1 - lift, pw - 2, ph - 2, CARD[3] if i % 2 else CARD[2])
        cv.hline(px_ + 2, py_ + 2 - lift, pw - 4, CARD[1]); cv.hline(px_ + 2, py_ + 4 - lift, pw - 4, CARD[1])
        for k in range(3):
            cv.px(px_ + 2 + int(rng.integers(0, pw - 4)), py_ + 2 + int(rng.integers(0, 3)) - lift, "#1a1418")
        if i % 2 == 0:
            cv.vline(px_ + pw - 1, py_ - lift, ph, CARD[0])
    return cv
