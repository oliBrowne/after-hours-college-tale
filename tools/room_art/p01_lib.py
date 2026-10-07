"""Pearl Street startup (P01 open office, P02 break room): the second floor of an 1890s red-brick
block on the pedestrian mall, sandblasted brick, heart-pine floor, a spiral duct under the joists,
and a fictional startup (DISRUPTR) moved in with standing desks, neon, a gong and kombucha."""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, LEAF, AMBER, ground_shadow, shrub
from lib_eng import MICRO, exit_sign, outlet, floor_cord
from lib_umc import halo, soft_ellipse

INK = "#171a2b"
SHADOW = "#0d0b16"
BRICK = ["#3a1e1e", "#56291f", "#6e3426", "#843f2c", "#985034", "#ab613f", "#bf744e"]   # sandblasted 1890s brick
MORTAR = ["#5e4a44", "#7a6458", "#94806e"]
SANDST = ["#4a3a36", "#6e5a4e", "#8e7764", "#a88f78", "#c0a88c", "#d6c0a2"]           # Lyons sandstone sills
PINE = ["#2e1c14", "#4a2e1c", "#664026", "#7a4e2e", "#8c5c34", "#9e6c3e", "#b27e4a"]   # heart-pine boards
TIMBER = ["#140e0e", "#1e1614", "#2c201a", "#3c2c22", "#4e3a2c"]
DUCT = ["#22242e", "#3a3e4a", "#565c6a", "#7a8090", "#a2a8b6", "#c8ccd6"]
SASH = ["#14201e", "#1e302c", "#2a423c", "#3a5850"]                                   # old green window sash
NEON_PINK = ["#5a1438", "#a8286c", "#e84a98", "#ff8ac4", "#ffe2f2"]
NEON_CYAN = ["#123a48", "#1e7a96", "#38c0e0", "#8ae8ff", "#e6fdff"]
NEON_MINT = ["#14402e", "#20845e", "#3cc896", "#8ef0c8", "#e8fff4"]
BUTCHER = ["#4a2e1a", "#6e4626", "#946034", "#b47c46", "#cc965a", "#deb07a"]
SCREEN = ["#0e1220", "#161c30", "#22304e", "#2e4a78", "#4a78b4", "#8ab8ec"]
WHITE = ["#7e828e", "#a6aab4", "#c8ccd2", "#e2e4e6", "#f2f2ee"]
CHROME = ["#2e3038", "#4e5260", "#787c8a", "#a6aab6", "#d2d6de"]
MARKER = ["#2a3a8a", "#c83a3a", "#2a7a4a", "#1a1a24", "#c86a1a"]
STICKY = ["#f2d84a", "#f28ab0", "#8ad8f0", "#a8e07a", "#f2a24a"]
COGNAC = ["#2a140c", "#4a2414", "#6e381e", "#8e4c28", "#ac6434", "#c47e46"]
FLEECE = ["#2e3040", "#4a4e5e", "#6a6e7e", "#8a8e9c"]   # heather-grey fleece
TEAL_P = ["#12302e", "#1c4a46", "#286460", "#3a807a", "#56a098"]
ORANGE = ["#5a240e", "#8a3a14", "#b8561e", "#dc7a2e", "#f2a050"]
WARM = AMBER


def _rng(seed):
    return np.random.default_rng(seed)


EXTRA = {"$": [".###", "##..", ".##.", "..##", "###."], "(": [".#", "#.", "#.", "#.", ".#"],
         ")": ["#.", ".#", ".#", ".#", "#."], ",": [".", ".", ".", "#", "#"]}


def micro_width(s):
    w = 0
    for ch in s.upper():
        g = EXTRA.get(ch) or MICRO.get(ch)
        w += (len(g[0]) + 1) if g else 3
    return max(0, w - 1)


def micro_text(cv, s, x, y, colour):
    """lib_eng's 3x5 lettering plus $ ( ) and comma."""
    cx = x
    for ch in s.upper():
        g = EXTRA.get(ch) or MICRO.get(ch)
        if g is None:
            cx += 3
            continue
        for r, row in enumerate(g):
            for k, c in enumerate(row):
                if c == "#":
                    cv.px(cx + k, y + r, colour)
        cx += len(g[0]) + 1
    return cx - x - 1


# --------------------------------------------------------------------------- structure

def loft_ceiling(cv, x, w, h=16, seed=0):
    """The ceiling edge: dark joist ends, a galvanised spiral duct on hangers running the room."""
    rng = _rng(seed)
    cv.rect(x, 0, w, h, TIMBER[1])
    for jx in range(x + 6, x + w, 24):                      # joist ends
        cv.rect(jx, 0, 10, h - 4, TIMBER[3]); cv.hline(jx, 0, 10, TIMBER[4]); cv.vline(jx + 9, 0, h - 4, TIMBER[0])
        cv.hline(jx, h - 5, 10, TIMBER[2])
    cv.hline(x, h - 4, w, TIMBER[0])
    cv.rect(x, h - 3, w, 3, TIMBER[2]); cv.hline(x, h - 3, w, TIMBER[4])   # ledger board
    # spiral duct: a 9px tube with seams every 6px and a lit top
    dy = 3
    cv.rect(x, dy, w, 9, OUT)
    cv.rect(x, dy + 1, w, 7, DUCT[2]); cv.hline(x, dy + 1, w, DUCT[4]); cv.hline(x, dy + 2, w, DUCT[3]); cv.hline(x, dy + 6, w, DUCT[1])
    for sx in range(x + int(rng.integers(0, 6)), x + w, 6):
        cv.line(sx, dy + 1, sx + 2, dy + 7, DUCT[1])
        cv.px(sx, dy + 2, DUCT[5])
    for hx in range(x + 40, x + w, 120):                    # hanger straps
        cv.rect(hx, 0, 2, dy + 1, DUCT[3]); cv.rect(hx - 1, dy, 4, 9, C(DUCT[1], 0.7))


def brick_wall_p(cv, x, y, w, h, seed=0, pal=BRICK):
    """Sandblasted common brick: 7x3 bricks, recessed pale mortar, worn faces, the odd clinker."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, MORTAR[1])
    for row, yy in enumerate(range(y, y + h, 4)):
        off = 0 if row % 2 else 4
        header = row % 6 == 5                                # a header course every sixth row
        step = 4 if header else 8
        for xx in range(x - off, x + w, step):
            x0, x1 = max(x, xx), min(x + w, xx + step - 1)
            if x1 <= x0:
                continue
            r = rng.random()
            tone = pal[2] if r < 0.18 else pal[3] if r < 0.55 else pal[4] if r < 0.85 else pal[5] if r < 0.96 else pal[1]
            bh = min(3, y + h - yy)
            cv.rect(x0, yy, x1 - x0, bh, tone)
            cv.hline(x0, yy, x1 - x0, shade(tone, 0.07))
            if bh == 3:
                cv.hline(x0, yy + 2, x1 - x0, shade(tone, -0.08))
            if rng.random() < 0.35:
                cv.px(x0 + int(rng.integers(0, x1 - x0)), yy + int(rng.integers(0, bh)), shade(tone, float(rng.choice([-0.16, 0.12]))))
        cv.hline(x, yy + 3, w, MORTAR[0]) if yy + 3 < y + h else None


def ghost_paint(cv, x, y, s, colour="#d8c8a8", alpha=0.18):
    """A faded painted sign on old brick (the building's 1900s tenant), in the big font, worn."""
    tmp = Canvas(text_width(s) + 2, 12)
    text(tmp, s, 1, 0, colour)
    m = tmp.a[..., 3] > 0.5
    rng = _rng(len(s))
    ys, xs = np.where(m)
    for yy, xx in zip(ys, xs):
        if rng.random() < 0.72:
            cv.px(x + xx, y + yy, C(colour, alpha))


def baseboard(cv, x, base, w):
    cv.rect(x, base - 6, w, 6, TIMBER[2]); cv.hline(x, base - 6, w, TIMBER[4]); cv.hline(x, base - 5, w, TIMBER[3])
    cv.hline(x, base - 1, w, TIMBER[0])


def pearl_view(w, h, seed=0):
    """Pearl Street across the mall at night, seen from upstairs: the opposite block's brick and
    sandstone upper floors with lit windows and a cornice, the mall's trees wrapped in white lights,
    shop awnings glowing below. Returns (Canvas, light points [(x, y)])."""
    rng = _rng(seed)
    cv = Canvas(w, h, seed=seed)
    cv.dither_v(0, 0, w, h // 3, "#141632", "#3a2c52", steps=4)
    for _ in range(w // 9):
        cv.px(int(rng.integers(0, w)), int(rng.integers(0, h // 5)), "#b8b8dc")
    roof = h // 4
    x = 0
    lights = []
    k = 0
    pals = [BRICK, ["#2e2a2c", "#4a4040", "#5e5250", "#726460", "#86766e", "#9a8a80", "#ae9c90"], SANDST + ["#e0cfb4"]]
    while x < w:
        bw = int(rng.integers(46, 78))
        pal = pals[k % 3]
        top = roof + int(rng.integers(-6, 7))
        cv.rect(x, top, bw, h - top, pal[2])
        for yy in range(top + 6, h, 3):                     # coursing read at distance
            cv.hline(x, yy, bw, shade(pal[2], -0.08))
        cv.rect(x - 1, top - 4, bw + 2, 4, pal[4]); cv.hline(x - 1, top - 4, bw + 2, pal[5]); cv.hline(x - 1, top - 1, bw + 2, pal[1])
        for dx in range(x + 1, x + bw - 1, 4):               # corbel dentils under the cornice
            cv.px(dx, top, pal[4])
        if bw > 54 and rng.random() < 0.6:                   # a pediment with a date stone
            cx = x + bw // 2
            cv.poly([(cx - 12, top - 4), (cx, top - 11), (cx + 12, top - 4)], pal[4])
            cv.hline(cx - 3, top - 7, 6, pal[1])
        n = max(2, bw // 14)
        for i in range(n):
            wx = x + 4 + i * (bw - 8) // n + 2
            for row in range(2):
                wy = top + 8 + row * 22
                ww, wh = 7, 14
                lit = rng.random() < 0.55
                cv.rect(wx - 1, wy - 2, ww + 2, wh + 3, pal[4])
                cv.ellipse(wx - 1, wy - 4, ww + 2, 6, pal[4])
                glass = WARM[2] if lit else "#1c2036"
                cv.rect(wx, wy, ww, wh, glass)
                cv.ellipse(wx, wy - 3, ww, 6, glass)
                if lit:
                    cv.rect(wx, wy, 3, 5, WARM[3]); cv.hline(wx, wy + wh // 2, ww, shade(WARM[2], -0.25))
                else:
                    cv.px(wx + 1, wy + 2, "#3a4466")
                cv.vline(wx + ww // 2, wy - 2, wh + 2, INK)
        x += bw
        k += 1
    # the mall's trees, wrapped in lights, between us and the shopfronts
    tb = h - 16
    for tx in range(-6, w + 10, 26):
        tx2 = tx + int(rng.integers(-4, 5))
        r = int(rng.integers(13, 18))
        cy = tb - int(rng.integers(8, 16))
        cv.ellipse(tx2 - r, cy - r, r * 2, int(r * 1.7), "#121a1a")
        cv.ellipse(tx2 - r + 2, cy - r + 1, r * 2 - 6, int(r * 1.1), "#1a2624")
        for _ in range(int(r * 2.2)):
            a = rng.uniform(0, 2 * np.pi); d = np.sqrt(rng.uniform(0, 1))
            lx, ly = int(tx2 + np.cos(a) * d * (r - 2)), int(cy - r * 0.15 + np.sin(a) * d * (r - 3) * 0.8)
            if 0 <= lx < w and 0 <= ly < h:
                cv.px(lx, ly, "#fff4d0" if rng.random() < 0.7 else WARM[3])
                lights.append((lx, ly))
    # shop awnings and lit fronts along the bottom edge
    cv.rect(0, h - 12, w, 12, "#2a1e22")
    for sx in range(0, w, 34):
        c1 = ["#7e2a2a", "#2a5a52", "#c47a2c", "#3a3a6a"][int(rng.integers(4))]
        cv.rect(sx + 2, h - 12, 28, 4, c1); cv.hline(sx + 2, h - 12, 28, shade(c1, 0.25))
        cv.rect(sx + 3, h - 8, 26, 8, WARM[2]); cv.rect(sx + 4, h - 7, 10, 7, WARM[3])
        cv.vline(sx + 16, h - 8, 8, "#2a1e22")
    return cv, lights


def arched_window(cv, cx, top, w, h, view, vx, seed=0):
    """Tall 1890s window: segmental brick arch with a sandstone keystone, deep brick reveal, old green
    double-hung sash, sandstone sill. `view` is the street panorama; vx its x at the window's left."""
    x0 = cx - w // 2
    rise = 7
    # arch of soldier bricks over the opening
    for i in range(-3, w + 4):
        t = (i - w / 2) / (w / 2 + 3)
        yy = top - int(round(rise * (1 - t * t)))
        for d in range(0, 7):
            c = BRICK[4] if (i // 2) % 2 else BRICK[3]
            cv.px(x0 + i, yy - d, c if d not in (0, 6) else MORTAR[1])
    cv.rect(cx - 3, top - rise - 8, 7, 9, SANDST[4]); cv.hline(cx - 3, top - rise - 8, 7, SANDST[5]); cv.vline(cx + 3, top - rise - 7, 8, SANDST[2])
    # opening + reveal
    for i in range(w):
        t = (i - w / 2 + 0.5) / (w / 2)
        yy = top - int(round(rise * (1 - t * t)))
        cv.vline(x0 + i, yy, top + h - yy, BRICK[1])
    glass_top = lambda i: top + 1 - int(round((rise - 1) * (1 - ((i - (w - 8) / 2 + 0.5) / ((w - 8) / 2)) ** 2)))
    gx0, gw = x0 + 4, w - 8
    for i in range(gw):
        gt = glass_top(i)
        for yy in range(gt, top + h - 2):
            vy = yy - (top - rise)
            if 0 <= vy < view.h and 0 <= vx + 4 + i < view.w:
                cv.a[yy, gx0 + i] = view.a[vy, vx + 4 + i]
    # sash frame: outer, meeting rail, muntins (2 over 2), a lower sash raised a crack
    sash = SASH
    for i in range(gw):
        gt = glass_top(i)
        cv.px(gx0 + i, gt, sash[2]); cv.px(gx0 + i, gt + 1, sash[1])
    cv.rect(gx0 - 2, top - 2, 3, h, sash[1]); cv.vline(gx0 - 2, top - 2, h, sash[3])
    cv.rect(gx0 + gw - 1, top - 2, 3, h, sash[1]); cv.vline(gx0 + gw + 1, top - 2, h, sash[0])
    mid = top + h // 2 - 4
    cv.rect(gx0, mid, gw, 4, sash[1]); cv.hline(gx0, mid, gw, sash[3]); cv.hline(gx0, mid + 3, gw, sash[0])
    cv.rect(gx0 + gw // 2 - 1, top - 4, 2, h - 2, sash[1]); cv.vline(gx0 + gw // 2 - 1, top - 4, h - 2, sash[2])
    cv.rect(gx0, top + h - 4, gw, 3, sash[1]); cv.hline(gx0, top + h - 4, gw, sash[3])
    cv.rect(gx0 + 3, mid + 2, 3, 2, "#a8906a")                                     # sash lock
    # reflection streaks on the lower panes
    cv.line(gx0 + 2, top + h - 8, gx0 + 8, mid + 8, C("#e8e8f8", 0.18))
    cv.line(gx0 + gw // 2 + 2, top + h - 8, gx0 + gw // 2 + 7, mid + 12, C("#e8e8f8", 0.12))
    # sandstone sill, its shadow
    sy = top + h - 1
    cv.rect(x0 - 4, sy, w + 8, 5, SANDST[3]); cv.hline(x0 - 4, sy, w + 8, SANDST[5]); cv.hline(x0 - 4, sy + 1, w + 8, SANDST[4])
    cv.hline(x0 - 4, sy + 4, w + 8, SANDST[1]); cv.rect(x0 - 3, sy + 5, w + 6, 2, C(SHADOW, 0.35))
    return sy


def radiator(cv, cx, base, w=40, h=24):
    """Cast-iron column radiator, painted silver long ago, on short feet against the wall."""
    x0 = cx - w // 2
    cv.rect(x0, base - h, w, h - 2, OUT)
    for k, sx in enumerate(range(x0 + 1, x0 + w - 1, 4)):
        cv.rect(sx, base - h + 1, 3, h - 4, DUCT[3]); cv.vline(sx, base - h + 1, h - 4, DUCT[4]); cv.vline(sx + 2, base - h + 1, h - 4, DUCT[2])
        cv.px(sx + 1, base - h + 1, DUCT[5])
    cv.rect(x0 + 1, base - h + 5, w - 2, 2, DUCT[1]); cv.rect(x0 + 1, base - 7, w - 2, 2, DUCT[1])
    cv.rect(x0 + 2, base - 2, 3, 2, OUT); cv.rect(x0 + w - 5, base - 2, 3, 2, OUT)
    cv.rect(x0 + w, base - 8, 5, 3, CHROME[2]); cv.px(x0 + w + 4, base - 9, "#a83a2a")       # valve


def pendant(cv, cx, drop, lit=True):
    """Edison bulb on a cloth cord hanging from the joists; returns the bulb centre."""
    cv.vline(cx, 0, drop, "#1a1418")
    cv.rect(cx - 2, drop, 5, 3, "#2a2420"); cv.hline(cx - 2, drop, 5, "#6a5a3a")
    by = drop + 3
    cv.ellipse(cx - 3, by, 7, 9, OUT)
    cv.ellipse(cx - 2, by + 1, 5, 7, WARM[3] if lit else "#4a4458")
    if lit:
        cv.vline(cx, by + 2, 4, WARM[4]); cv.px(cx - 1, by + 3, WARM[4]); cv.px(cx + 1, by + 3, WARM[4])
        halo(cv, cx, by + 4, 18, strength=0.07)
    return cx, by + 4


# --------------------------------------------------------------------------- neon, boards, screen

def neon_text(cv, s, x, y, pal=NEON_PINK, scale=2, glow=True):
    """Glass-tube lettering: the game font scaled up, a hot white-pink core in a coloured tube,
    a stepped glow on the brick, a clear acrylic backer and its standoffs. Returns the tube mask origin."""
    tw = text_width(s) + 2
    tmp = Canvas(tw, 12)
    text(tmp, s, 1, 0, "#ffffff")
    m = tmp.a[..., 3] > 0.5
    big = np.repeat(np.repeat(m, scale, 0), scale, 1)
    H, W = big.shape
    from scipy import ndimage
    ring1 = ndimage.binary_dilation(big, iterations=1) & ~big
    if glow:
        for it, a in [(9, 0.05), (6, 0.07), (3, 0.1)]:
            g = ndimage.binary_dilation(big, iterations=it)
            ys, xs = np.where(g)
            for yy, xx in zip(ys, xs):
                cv.px(x + xx, y + yy, C(pal[2], a))
    # acrylic backer
    bx0, by0 = x - 4, y - 3
    cv.rect(bx0, by0, W + 8, H + 6, C("#c8e0f0", 0.08)); cv.hline(bx0, by0, W + 8, C("#e8f4ff", 0.25))
    for sx in (bx0 + 1, bx0 + W + 6):
        for sy in (by0 + 1, by0 + H + 4):
            cv.px(sx, sy, CHROME[4])
    ys, xs = np.where(ring1)
    for yy, xx in zip(ys, xs):
        cv.px(x + xx, y + yy, C(pal[1], 0.9))
    er = ndimage.binary_erosion(big)
    ys, xs = np.where(big)
    for yy, xx in zip(ys, xs):
        cv.px(x + xx, y + yy, pal[4] if er[yy, xx] or (yy % scale == 0 and xx % scale == 0) else pal[3])
    return big


def neon_bolt(cv, x, y, pal=NEON_CYAN):
    """A lightning-bolt glyph in neon tube (the logo mark)."""
    pts = [(x + 8, y), (x + 2, y + 11), (x + 7, y + 11), (x + 3, y + 21), (x + 13, y + 8), (x + 8, y + 8), (x + 12, y)]
    halo(cv, x + 7, y + 10, 16, pal[2], 0.07)
    for (a, b) in zip(pts, pts[1:] + pts[:1]):
        cv.line(a[0] + 1, a[1], b[0] + 1, b[1], pal[2])
        cv.line(a[0], a[1], b[0], b[1], pal[4])


def whiteboard(cv, x, y, w, h, seed=0):
    """A wall of whiteboard: aluminium frame, marker tray, the plan in four colours, sticky notes."""
    rng = _rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT)
    cv.rect(x - 1, y - 1, w + 2, h + 2, CHROME[3]); cv.hline(x - 1, y - 1, w + 2, CHROME[4])
    cv.rect(x, y, w, h, WHITE[3])
    for _ in range(w * h // 30):                                   # ghosts of old erasures
        cv.hline(x + int(rng.integers(0, w - 8)), y + int(rng.integers(0, h)), int(rng.integers(3, 9)), WHITE[2])
    cv.line(x + 2, y + 2, x + 12, y + h - 4, C(WHITE[4], 0.6))
    # the plan: MVP > ??? > IPO across the top
    bx = x + 6
    for k, (label, col) in enumerate([("MVP", MARKER[0]), ("???", MARKER[1]), ("IPO", MARKER[2])]):
        bw = micro_width(label) + 6
        cv.rect(bx, y + 6, bw, 9, col); cv.rect(bx + 1, y + 7, bw - 2, 7, WHITE[3])
        micro_text(cv, label, bx + 3, y + 8, col)
        if label == "???":
            cv.ellipse(bx - 3, y + 3, bw + 6, 15, MARKER[1]); cv.ellipse(bx - 2, y + 4, bw + 4, 13, WHITE[3])
            cv.rect(bx + 1, y + 7, bw - 2, 7, WHITE[3]); micro_text(cv, label, bx + 3, y + 8, MARKER[1])
            cv.rect(bx, y + 6, bw, 1, MARKER[1]); cv.rect(bx, y + 14, bw, 1, MARKER[1])
        if k < 2:
            ax = bx + bw + 2
            cv.hline(ax, y + 10, 10, MARKER[3]); cv.px(ax + 8, y + 9, MARKER[3]); cv.px(ax + 8, y + 11, MARKER[3])
        bx += bw + 14
    # a hockey-stick chart
    gx, gy = x + 6, y + 24
    cv.vline(gx, gy, 26, MARKER[3]); cv.hline(gx, gy + 26, 40, MARKER[3])
    pts = [(gx + 2, gy + 23), (gx + 12, gy + 22), (gx + 22, gy + 21), (gx + 28, gy + 16), (gx + 33, gy + 6), (gx + 37, gy - 2)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], MARKER[2])
    micro_text(cv, "$$$", gx + 26, gy + 18, MARKER[2])
    # a scooter with wings
    sx, sy = x + 58, y + 40
    cv.ellipse(sx, sy + 6, 5, 5, MARKER[3]); cv.ellipse(sx + 18, sy + 6, 5, 5, MARKER[3])
    cv.ellipse(sx + 1, sy + 7, 3, 3, WHITE[3]); cv.ellipse(sx + 19, sy + 7, 3, 3, WHITE[3])
    cv.hline(sx + 3, sy + 7, 17, MARKER[3]); cv.line(sx + 18, sy + 7, sx + 15, sy - 8, MARKER[3]); cv.hline(sx + 12, sy - 8, 7, MARKER[3])
    cv.poly([(sx + 8, sy + 5), (sx + 2, sy - 4), (sx + 12, sy + 2)], MARKER[0])
    cv.poly([(sx + 10, sy + 5), (sx + 7, sy - 6), (sx + 14, sy + 3)], MARKER[0])
    micro_text(cv, "V2", sx + 22, sy - 6, MARKER[4])
    # columns of scribbled todo lines and a big TAM circle
    for r in range(5):
        lx, ly = x + w - 52, y + 24 + r * 6
        cv.rect(lx, ly, 3, 3, MARKER[3]); cv.px(lx + 1, ly + 1, WHITE[3])
        if r < 2:
            cv.line(lx, ly + 1, lx + 1, ly + 2, MARKER[2]); cv.line(lx + 1, ly + 2, lx + 3, ly - 1, MARKER[2])
        xx = lx + 6
        while xx < lx + 22 + int(rng.integers(0, 14)):
            seg = int(rng.integers(2, 6))
            cv.hline(xx, ly + 1, seg, MARKER[0] if r % 2 else MARKER[3]); xx += seg + 1
    cx, cy = x + w - 18, y + h - 18
    for rr, col in [(13, MARKER[1]), (8, MARKER[4]), (4, MARKER[0])]:
        cv.ellipse(cx - rr, cy - rr, rr * 2 + 1, rr * 2 + 1, col); cv.ellipse(cx - rr + 1, cy - rr + 1, rr * 2 - 1, rr * 2 - 1, WHITE[3])
    micro_text(cv, "TAM", cx - 5, cy - 2, MARKER[1])
    micro_text(cv, "DO NOT ERASE", x + 6, y + h - 9, MARKER[1])
    cv.rect(x + 6, y + h - 7, 22, 3, WHITE[3])                       # ...half erased
    # sticky notes
    for k in range(9):
        px_, py_ = x + 70 + int(rng.integers(0, w - 130)), y + 4 + int(rng.integers(0, h - 34))
        c = STICKY[k % len(STICKY)]
        cv.rect(px_ + 1, py_ + 1, 7, 7, C(SHADOW, 0.3)); cv.rect(px_, py_, 7, 7, c); cv.hline(px_, py_, 7, shade(c, 0.2))
        cv.hline(px_ + 1, py_ + 3, 4, shade(c, -0.4)); cv.hline(px_ + 1, py_ + 5, 3, shade(c, -0.4))
    # tray with markers and an eraser
    cv.rect(x + 8, y + h + 1, w - 16, 3, CHROME[2]); cv.hline(x + 8, y + h + 1, w - 16, CHROME[4])
    for k, mx in enumerate(range(x + 20, x + 60, 7)):
        cv.rect(mx, y + h, 5, 2, MARKER[k % 4]); cv.px(mx + 4, y + h, WHITE[4])
    cv.rect(x + w - 30, y + h - 2, 12, 4, "#2a2a34"); cv.hline(x + w - 30, y + h - 2, 12, "#5a5a6a")


SLIDE_W, SLIDE_H = 176, 98


def slide(kind):
    """One slide of Kyle's pitch deck at screen size (projected: slightly washed, warm hot-spot)."""
    cv = Canvas(SLIDE_W, SLIDE_H, fill="#eef0f2")
    w, h = SLIDE_W, SLIDE_H
    pink, ink, grey = "#d83a88", "#1e2234", "#9aa0ae"
    if kind == "title":
        cv.rect(0, 0, w, h, "#16182a")
        for i in range(0, w + h, 10):                                  # diagonal speed lines
            cv.line(i, 0, i - h, h, "#1e2238")
        neon_text(cv, "DISRUPTR", w // 2 - 50, 26, NEON_PINK, scale=2, glow=False)
        neon_bolt(cv, w // 2 - 70, 22, NEON_CYAN)
        s = "SCOOTERS. BUT AI."
        text(cv, s, w // 2 - text_width(s) // 2, 56, "#e6e8f2")
        s2 = "SERIES A DECK - KYLE"
        micro_text(cv, s2, w // 2 - micro_width(s2) // 2, 74, "#8a8ea8")
        micro_text(cv, "CONFIDENTIAL", 4, h - 8, "#5a5e78")
    elif kind == "traction":
        text(cv, "TRACTION", 8, 5, ink)
        cv.hline(8, 16, 46, pink)
        gx, gy, gw, gh = 18, 24, w - 34, h - 38
        cv.vline(gx, gy, gh, ink); cv.hline(gx, gy + gh, gw, ink)
        for k in range(1, 5):
            cv.hline(gx + 1, gy + gh - k * gh // 5, gw - 1, "#dcdfe6")
        pts = []
        for i in range(gw - 6):
            t = i / (gw - 6)
            pts.append((gx + 2 + i, gy + gh - 3 - int((gh - 6) * t ** 5)))
        for a, b in zip(pts, pts[1:]):
            cv.line(a[0], a[1], b[0], b[1], pink); cv.line(a[0], a[1] + 1, b[0], b[1] + 1, pink)
        cv.poly([(pts[-1][0] - 4, pts[-1][1] + 6), (pts[-1][0] + 3, pts[-1][1] - 2), (pts[-1][0] + 4, pts[-1][1] + 7)], pink)
        micro_text(cv, "(NO UNITS)", gx + 4, gy + 2, grey)
        micro_text(cv, "NOW", gx + gw - 18, gy + gh + 3, grey); micro_text(cv, "THEN", gx, gy + gh + 3, grey)
    elif kind == "tam":
        text(cv, "MARKET SIZE", 8, 5, ink)
        cv.hline(8, 16, 64, pink)
        cx, cy = w // 2 + 20, h // 2 + 8
        for r, c, lab in [(38, "#f6d6e6", "TAM $9T"), (26, "#eeaacc", "SAM $4T"), (14, pink, "SOM $2T")]:
            cv.ellipse(cx - r, cy - r, r * 2 + 1, r * 2 + 1, c)
        for k, (lab, yy) in enumerate([("TAM: EVERYONE", 30), ("SAM: ALSO EVERYONE", 42), ("SOM: KYLE'S FRIENDS", 54)]):
            cv.rect(8, yy + 1, 3, 3, ["#f6d6e6", "#eeaacc", pink][k])
            micro_text(cv, lab, 14, yy, ink)
        micro_text(cv, "$9T", cx - 5, cy - 32, ink); micro_text(cv, "$4T", cx - 5, cy - 20, ink); micro_text(cv, "$2T", cx - 5, cy - 2, "#ffffff")
    elif kind == "hiring":
        cv.rect(0, 0, w, h, "#f6e8f0")
        s = "WE'RE HIRING"
        text(cv, s, w // 2 - text_width(s) // 2, 22, pink)
        s = "(UNPAID)"
        micro_text(cv, s, w // 2 - micro_width(s) // 2, 36, grey)
        for k, (lab, c) in enumerate([("ROCKSTARS", "#3a7ad8"), ("NINJAS", ink), ("INTERNS", "#2a9a6a")]):
            bx = 18 + k * 50
            cv.ellipse(bx + 8, 50, 16, 16, c); cv.ellipse(bx + 12, 53, 8, 8, "#f2d0b8")
            micro_text(cv, lab, bx + 16 - micro_width(lab) // 2, 72, ink)
        micro_text(cv, "PERKS: KOMBUCHA, EQUITY (SOMEDAY)", 8, h - 10, grey)
    # projection: a warm hot-spot in the middle, slight keystone shading at the corners
    halo(cv, w // 2, h // 2 - 4, 60, "#fff6d8", 0.05)
    for (x0, y0) in [(0, 0), (w - 6, 0), (0, h - 4), (w - 6, h - 4)]:
        cv.rect(x0, y0, 6, 4, C("#7a7e94", 0.12))
    return cv


def projection_screen(cv, x, y, w, h):
    """Motorised screen case on the brick, black-bordered fabric, the bottom bar and pull. Returns the
    slide area (x, y) so slides can be laid on top."""
    cv.rect(x - 6, y - 7, w + 12, 7, OUT); cv.rect(x - 5, y - 6, w + 10, 5, WHITE[2]); cv.hline(x - 5, y - 6, w + 10, WHITE[4])
    cv.hline(x - 5, y - 2, w + 10, WHITE[0])
    cv.rect(x - 1, y, w + 2, h + 1, "#18181e")
    cv.rect(x, y, w, h, "#2a2a32")
    cv.rect(x + 2, y + 2, w - 4, h - 4, "#eef0f2")
    cv.rect(x - 3, y + h, w + 6, 4, OUT); cv.rect(x - 2, y + h + 1, w + 4, 2, CHROME[3])
    cv.vline(x + w // 2, y + h + 4, 8, "#1a1a20"); cv.rect(x + w // 2 - 2, y + h + 11, 5, 3, CHROME[2])
    cv.rect(x + 1, y + h + 4, w, 2, C(SHADOW, 0.35))
    return x + (w - SLIDE_W) // 2, y + (h - SLIDE_H) // 2


def ceiling_projector(cv, cx, beam_to):
    """A projector on a drop pole from the ceiling, and its faint cone onto the screen."""
    cv.rect(cx - 1, 0, 3, 10, CHROME[2]); cv.vline(cx - 1, 0, 10, CHROME[4])
    cv.rect(cx - 12, 9, 25, 9, OUT); cv.rect(cx - 11, 10, 23, 7, WHITE[2]); cv.hline(cx - 11, 10, 23, WHITE[4])
    cv.hline(cx - 11, 16, 23, WHITE[0])
    for vx in range(cx - 9, cx - 1, 2):
        cv.vline(vx, 11, 4, WHITE[1])
    cv.ellipse(cx + 3, 13, 6, 5, OUT); cv.ellipse(cx + 4, 14, 4, 3, "#bfe6ff"); cv.px(cx + 5, 14, "#ffffff")
    cv.px(cx - 9, 15, "#5cf08a")
    x0, y0, x1, y1 = beam_to
    lens = (cx + 6, 17)
    cv.poly([lens, (x0, y1), (x1, y1)], C("#e8f0ff", 0.05))
    cv.poly([lens, (x0 + 20, y0 + 10), (x1 - 20, y0 + 10)], C("#e8f0ff", 0.04))


def stair_door(cv, cx, base, w=40, h=74):
    """The old five-panel fir door to the stairwell, a transom lettered STAIRS, a green EXIT sign."""
    x0, top = cx - w // 2, base - h
    cv.rect(x0 - 5, top - 14, w + 10, h + 14, TIMBER[0])
    cv.rect(x0 - 4, top - 13, w + 8, h + 13, TIMBER[3]); cv.vline(x0 - 4, top - 13, h + 13, TIMBER[4]); cv.vline(x0 + w + 3, top - 13, h + 13, TIMBER[1])
    cv.rect(x0 - 6, top - 15, w + 12, 3, TIMBER[4]); cv.hline(x0 - 6, top - 15, w + 12, "#6a5038")
    # transom: glass with gold-leaf lettering
    cv.rect(x0, top - 11, w, 9, "#1e1a2a"); cv.rect(x0 + 1, top - 10, w - 2, 7, "#2e2a46")
    micro_text(cv, "STAIRS", cx - micro_width("STAIRS") // 2, top - 9, "#d8b45a")
    cv.rect(x0 - 1, top - 2, w + 2, 2, TIMBER[2])
    # door: five horizontal panels
    cv.rect(x0, top, w, h, "#5a3a26"); cv.vline(x0, top, h, "#7a5236"); cv.vline(x0 + w - 1, top, h, "#3e2618")
    for k in range(5):
        py = top + 4 + k * 13
        cv.rect(x0 + 5, py, w - 10, 10, "#4a2e1e"); cv.rect(x0 + 6, py + 1, w - 12, 8, "#68442c")
        cv.hline(x0 + 6, py + 1, w - 12, "#80583a"); cv.hline(x0 + 5, py + 9, w - 10, "#3a2416")
    cv.rect(x0 + w - 8, top + h // 2, 4, 4, "#c8a050"); cv.px(x0 + w - 7, top + h // 2 + 1, "#f0d080")
    cv.rect(x0 + w - 7, top + h // 2 + 5, 2, 3, "#2a1a10")
    cv.rect(x0 + w // 2 - 9, top + 32, 18, 9, "#e8e2d2"); micro_text(cv, "PUSH", x0 + w // 2 - 7, top + 34, "#a83a2a")
    cv.rect(x0 + 2, top + 2, 10, 3, "#3a4048"); cv.line(x0 + 12, top + 3, x0 + 18, top + 2, "#2a2e36")   # closer
    exit_sign(cv, x0 + w + 8, top - 12)


def doorway_glimpse(cv, cx, base, w=50, h=76):
    """An open doorway into the break room: painted casing, warm light, the sticker fridge's flank
    and a glimpse of the floor and the snack wall's bins."""
    x0, top = cx - w // 2, base - h
    cv.rect(x0 - 5, top - 5, w + 10, h + 5, TIMBER[0])
    cv.rect(x0 - 4, top - 4, w + 8, h + 4, "#e2d8c6"); cv.vline(x0 - 4, top - 4, h + 4, "#f2ead8"); cv.vline(x0 + w + 3, top - 4, h + 4, "#a89c88")
    cv.hline(x0 - 4, top - 4, w + 8, "#f6f0e2")
    cv.rect(x0, top, w, h, "#c8a070")
    cv.dither_v(x0, top, w, h - 18, "#e8c08a", "#c89462", steps=4)
    # far wall: snack bins and a bit of mint neon
    for k in range(4):
        for r in range(3):
            bx, by = x0 + 3 + k * 7, top + 14 + r * 9
            cv.rect(bx, by, 6, 7, "#f2e6d0"); cv.rect(bx + 1, by + 3, 4, 3, STICKY[(k + r) % 5])
    for k in range(4):
        cv.px(x0 + 6 + k * 4, top + 6, NEON_MINT[3]); cv.px(x0 + 7 + k * 4, top + 6, NEON_MINT[4])
    # the fridge's side, covered in stickers
    fx = x0 + w - 16
    cv.rect(fx, top + 4, 16, h - 14, CHROME[3]); cv.vline(fx, top + 4, h - 14, CHROME[4]); cv.hline(fx, top + 26, 16, CHROME[1])
    rng = _rng(5)
    for _ in range(18):
        sx, sy = fx + 1 + int(rng.integers(0, 12)), top + 6 + int(rng.integers(0, h - 22))
        c = ["#e84a98", "#3a8ad8", "#f2d84a", "#2a9a6a", "#f2f2ea", "#e86a2a"][int(rng.integers(6))]
        cv.rect(sx, sy, 3, 2, c)
    # floor inside
    cv.rect(x0, base - 18, w, 18, PINE[4])
    for yy in range(base - 18, base, 4):
        cv.hline(x0, yy, w, PINE[3])
    cv.rect(x0, base - 18, w, 2, C(SHADOW, 0.3))
    cv.rect(x0 - 2, base - 2, w + 4, 2, "#8a7a5a")


def vest_hooks(cv, x, y, n=3):
    """A rail of hooks and the team's identical heather fleece vests; one wears a SPARE tag."""
    cv.rect(x - 2, y, n * 14 + 2, 3, TIMBER[3]); cv.hline(x - 2, y, n * 14 + 2, TIMBER[4])
    body = FLEECE
    for k in range(n):
        vx = x + k * 14
        cv.px(vx + 6, y + 3, CHROME[3])
        cv.rect(vx, y + 4, 13, 19, OUT)
        cv.rect(vx + 1, y + 5, 11, 17, body[2]); cv.vline(vx + 1, y + 5, 17, body[3]); cv.vline(vx + 11, y + 5, 17, body[1])
        cv.rect(vx + 4, y + 4, 5, 3, OUT); cv.rect(vx + 1, y + 7, 2, 5, OUT); cv.rect(vx + 10, y + 7, 2, 5, OUT)   # neck + armholes
        cv.vline(vx + 6, y + 7, 15, body[0]); cv.px(vx + 6, y + 8, CHROME[4])          # zip
        for yy in range(y + 13, y + 21, 3):
            cv.hline(vx + 2, yy, 3, body[1]); cv.hline(vx + 8, yy + 1, 3, body[1])       # quilting
        cv.rect(vx + 8, y + 9, 2, 2, "#e84a98")                                        # logo patch
    tx = x + 2 * 14 + 3
    cv.line(tx + 4, y + 14, tx + 2, y + 25, "#e6e2d6"); cv.rect(tx - 1, y + 25, 8, 6, "#f2ecdc"); cv.hline(tx, y + 27, 6, "#c83a3a")


def framed_poster(cv, x, y, w, h, lines, bg="#16182a", fg="#f2ecdc", accent="#e84a98"):
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT); cv.rect(x - 1, y - 1, w + 2, h + 2, "#d6d2c8")
    cv.rect(x, y, w, h, bg)
    for k, s in enumerate(lines):
        micro_text(cv, s, x + w // 2 - micro_width(s) // 2, y + 4 + k * 7, fg if k else accent)
    cv.rect(x + 1, y + h + 2, w, 2, C(SHADOW, 0.35))


def thermostat(cv, x, y):
    cv.rect(x, y, 9, 9, OUT); cv.rect(x + 1, y + 1, 7, 7, "#2a2e38"); cv.ellipse(x + 2, y + 2, 5, 5, "#e8a85a"); cv.px(x + 4, y + 4, "#ffffff")


# --------------------------------------------------------------------------- floor

def pine_floor(cv, x, y, w, h, seed=0):
    """Refinished heart-pine boards (3-4px wide rows read as 5" boards), butt joints, nail pairs,
    honey tones with darker heartwood streaks and a satin sheen."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, PINE[2])
    yy = y
    while yy < y + h:
        rh = 6 + (1 if (yy - y) > h * 0.55 else 0)
        rh = min(rh, y + h - yy)
        xx = x - int(rng.integers(0, 60))
        while xx < x + w:
            pl = int(rng.integers(50, 120))
            x0, x1 = max(x, xx), min(x + w, xx + pl)
            if x1 - x0 >= 2:
                tone = PINE[int(rng.choice([3, 4, 4, 5, 5, 6]))]
                cv.rect(x0, yy, x1 - x0, rh - 1, tone)
                cv.hline(x0, yy, x1 - x0, shade(tone, 0.07))
                for _ in range((x1 - x0) // 7):
                    gx = x0 + int(rng.integers(0, max(1, x1 - x0 - 8)))
                    cv.hline(gx, yy + 1 + int(rng.integers(0, max(1, rh - 2))), int(rng.integers(4, 12)), shade(tone, -0.09))
                if rng.random() < 0.18:
                    kx = x0 + int(rng.integers(3, max(4, x1 - x0 - 3)))
                    cv.rect(kx, yy + rh // 2 - 1, 2, 2, PINE[1]); cv.px(kx + 2, yy + rh // 2, shade(tone, -0.18))
                cv.vline(x1 - 1, yy, rh - 1, PINE[1])
                cv.px(x0 + 2, yy + 1, PINE[1]); cv.px(x0 + 2, yy + rh - 3, PINE[1])     # nail pair
            xx += pl
        cv.hline(x, yy + rh - 1, w, PINE[0])
        yy += rh


def kilim_rug(cv, x, y, w, h, seed=0):
    """A flat-woven rug: rust and indigo bands with stepped diamonds, fringe at the ends."""
    cv.rect(x + 1, y + 2, w, h, C(SHADOW, 0.35))
    cv.rect(x, y, w, h, "#7a2e24")
    cv.rect(x + 3, y + 2, w - 6, h - 4, "#2a3260"); cv.rect(x + 5, y + 4, w - 10, h - 8, "#8e3a2a")
    for yy in range(y + 6, y + h - 6, 2):
        cv.hline(x + 5, yy, w - 10, "#863628")
    cy = y + h // 2
    for k, xx in enumerate(range(x + 18, x + w - 12, 22)):
        c = "#d8a24a" if k % 2 else "#e6d6b1"
        for s in range(9, 0, -3):
            cv.poly([(xx, cy - s), (xx + s + 2, cy), (xx, cy + s), (xx - s - 2, cy)], c if s % 2 else "#2a3260")
    for k in range(x + 8, x + w - 8, 6):
        cv.px(k, y + 3, "#e6d6b1"); cv.px(k, y + h - 4, "#e6d6b1")
    for fy in range(y + 1, y + h - 1, 2):
        cv.hline(x - 3, fy, 3, "#e6d6b1"); cv.hline(x + w, fy, 3, "#e6d6b1")


def tyre_marks(cv, pts, seed=0):
    """Black rubber scuffs from an e-scooter ridden indoors: a broken double arc."""
    rng = _rng(seed)
    for (a, b) in zip(pts, pts[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
        for i in range(n):
            if rng.random() < 0.18:
                continue
            t = i / max(1, n)
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            cv.px(int(x), int(y), C("#141018", 0.55))
            if rng.random() < 0.5:
                cv.px(int(x) + 1, int(y), C("#141018", 0.3))


def tape_x(cv, cx, cy, c="#e8c24a"):
    for d in range(-5, 6):
        cv.rect(cx + d * 2 - 1, cy + d, 3, 1, c)
        cv.rect(cx - d * 2 - 1, cy + d, 3, 1, c)


def power_strip(cv, x, y, label="KYLE"):
    cv.rect(x, y, 26, 5, OUT); cv.rect(x + 1, y + 1, 24, 3, "#e6e2d6")
    for k in range(4):
        cv.rect(x + 3 + k * 5, y + 2, 2, 1, "#5a5a68")
    cv.px(x + 23, y + 2, "#e84a3a")
    cv.rect(x + 2, y + 6, micro_width(label) + 4, 7, "#f2ecdc"); micro_text(cv, label, x + 4, y + 7, "#c83a3a")


# --------------------------------------------------------------------------- props

def _screen_ui(cv, x, y, w, h, kind, seed=0):
    """What is on a monitor: code, a dashboard, chat, a fish tank screensaver, or off."""
    rng = _rng(seed)
    if kind == "off":
        cv.rect(x, y, w, h, "#12141c"); cv.line(x + 2, y + h - 3, x + w // 2, y + 2, "#2a2e3a")
        return
    if kind == "code":
        cv.rect(x, y, w, h, SCREEN[0])
        for r in range(y + 2, y + h - 1, 2):
            ind = int(rng.integers(0, 3)) * 2
            xx = x + 2 + ind
            while xx < x + w - 3 and rng.random() < 0.8:
                seg = int(rng.integers(2, 6))
                cv.hline(xx, r, min(seg, x + w - 2 - xx), ["#e86a9a", "#8ad8f0", "#f2d07a", "#a8e07a", "#c8ccd8"][int(rng.integers(5))])
                xx += seg + 1
    elif kind == "dash":
        cv.rect(x, y, w, h, "#e8ecf2")
        cv.rect(x, y, w, 3, "#2a3048")
        for k in range(4):
            bh = int(rng.integers(3, h - 7))
            cv.rect(x + 2 + k * 4, y + h - 2 - bh, 3, bh, ["#3a7ad8", "#e84a98", "#2a9a6a", "#f2a24a"][k])
        cv.line(x + w // 2 + 1, y + h - 3, x + w - 3, y + 5, "#e84a98")
        cv.rect(x + w // 2, y + 4, 2, 2, "#2a9a6a")
    elif kind == "chat":
        cv.rect(x, y, w, h, "#f2f0f4"); cv.rect(x, y, 5, h, "#3a1e4a")
        for r in range(y + 2, y + h - 2, 4):
            cv.rect(x + 7, r, 2, 2, ["#e84a98", "#3a8ad8", "#2a9a6a"][int(rng.integers(3))])
            cv.hline(x + 10, r, int(rng.integers(4, w - 12)), "#8a8a98")
    elif kind == "fish":
        cv.rect(x, y, w, h, "#1a4a7a"); cv.rect(x, y + h - 3, w, 3, "#c8a86a")
        cv.rect(x + 3, y + 4, 4, 2, "#f2a24a"); cv.px(x + 2, y + 4, "#f2a24a"); cv.rect(x + w - 8, y + 7, 3, 2, "#f2e04a")
        cv.vline(x + w - 4, y + h - 8, 5, "#3a9a5a"); cv.px(x + 9, y + 2, "#bfe6ff")
    cv.hline(x, y, w, C("#ffffff", 0.15))


def monitor(cv, cx, base, w=26, h=17, kind="code", seed=0, arm=True):
    """A flat monitor on a stand; screen faces the room."""
    x0 = cx - w // 2
    top = base - h - 6
    cv.rect(cx - 1, top + h, 3, 6, IRON[1]); cv.rect(cx - 5, base - 1, 11, 2, IRON[2]); cv.hline(cx - 5, base - 1, 11, IRON[3])
    cv.rect(x0 - 1, top - 1, w + 2, h + 2, OUT); cv.rect(x0, top, w, h, IRON[1])
    _screen_ui(cv, x0 + 1, top + 1, w - 2, h - 3, kind, seed)
    cv.px(cx, top + h - 1, "#5cf08a" if kind != "off" else IRON[3])


def standing_desk(variant="intern", width=76, height=58, seed=0):
    """A sit-stand desk raised to standing: butcher-block top seen from above at an angle, black
    T-legs with the motor columns, screens facing the room, the owner's things."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 6, seed=seed)
    ox, base = 4, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 3, width // 2 + 2, 4, alpha=0.32)
    top_front = base - 30                                 # front edge of the desktop (standing height)
    depth = 11
    if variant == "treadmill":
        # treadmill deck under the desk, its belt running toward us
        cv.rect(ox + 8, base - 9, width - 16, 9, OUT)
        cv.rect(ox + 9, base - 8, width - 18, 7, "#2a2a34"); cv.hline(ox + 9, base - 8, width - 18, "#4a4a58")
        for k in range(ox + 12, ox + width - 12, 5):
            cv.vline(k, base - 7, 5, "#22222a")
        cv.rect(ox + 7, base - 9, 3, 9, CHROME[2]); cv.rect(ox + width - 10, base - 9, 3, 9, CHROME[2])
        cv.rect(cx - 8, base - 5, 16, 4, OUT); cv.rect(cx - 7, base - 4, 14, 2, "#0e1a14")
        cv.rect(cx - 5, base - 4, 9, 1, "#5cf08a")                       # its little display
    # legs: two columns with feet
    for lx in (ox + 10, ox + width - 14):
        cv.rect(lx, top_front + 2, 5, base - top_front - 4, OUT)
        cv.rect(lx + 1, top_front + 2, 3, base - top_front - 5, IRON[2]); cv.vline(lx + 1, top_front + 2, base - top_front - 5, IRON[4])
        cv.rect(lx + 1, top_front + 12, 3, 1, IRON[1])     # the telescoping joint
        cv.rect(lx - 3, base - 4, 11, 3, OUT); cv.rect(lx - 2, base - 3, 9, 1, IRON[3])
    cv.rect(ox + 12, top_front + 4, width - 24, 3, IRON[1])            # crossbar / cable tray
    cv.line(ox + width - 18, top_front + 7, ox + width - 22, base - 3, "#1a1a20")   # power cord down a leg
    cv.rect(ox + 14, top_front + 2, 8, 4, IRON[2]); cv.px(ox + 15, top_front + 3, "#5cf08a")  # keypad
    # desktop slab (top + front edge)
    tx0, tx1 = ox, ox + width
    ty = top_front - depth
    cv.rect(tx0, ty - 1, width, depth + 6, OUT)
    for yy in range(ty, top_front + 1):
        cv.hline(tx0 + 1, yy, width - 2, BUTCHER[3] if (yy - ty) % 3 else BUTCHER[4])
    for k in range(tx0 + 1, tx1 - 1, 5):                               # butcher-block strips
        cv.vline(k + int(rng.integers(0, 2)), ty, depth + 1, BUTCHER[2])
    cv.hline(tx0 + 1, ty, width - 2, BUTCHER[5])
    cv.rect(tx0 + 1, top_front + 1, width - 2, 3, BUTCHER[2]); cv.hline(tx0 + 1, top_front + 1, width - 2, BUTCHER[4])
    cv.hline(tx0 + 1, top_front + 3, width - 2, BUTCHER[1])
    back = ty + 3
    if variant == "intern":
        # an old thick laptop, a lanyard, sticky notes, a free tote, a mug
        lx = cx - 12
        cv.rect(lx, back - 10, 22, 12, OUT); cv.rect(lx + 1, back - 9, 20, 10, "#2a2c34")
        _screen_ui(cv, lx + 2, back - 8, 18, 8, "chat", seed + 1)
        cv.rect(lx - 2, back + 2, 26, 4, OUT); cv.rect(lx - 1, back + 3, 24, 2, "#8a8a96"); cv.hline(lx - 1, back + 3, 24, "#b8b8c4")
        for k, c in enumerate(STICKY[:3]):
            cv.rect(lx + 24 + k * 2, back - 7 + k * 3, 6, 6, c); cv.hline(lx + 25 + k * 2, back - 5 + k * 3, 4, shade(c, -0.4))
        cv.rect(tx0 + 6, back - 3, 6, 7, "#f2ecdc"); cv.vline(tx0 + 12, back - 1, 3, "#f2ecdc"); cv.rect(tx0 + 7, back - 1, 4, 2, "#e84a98")
        cv.line(tx0 + 14, back + 5, tx0 + 20, back + 2, "#e84a98"); cv.rect(tx0 + 19, back + 1, 4, 5, "#f2ecdc")   # lanyard + badge
        cv.rect(tx1 - 14, back - 12, 10, 14, OUT); cv.rect(tx1 - 13, back - 11, 8, 12, "#e6dcc6"); cv.rect(tx1 - 11, back - 8, 4, 4, "#e84a98")  # tote
        cv.line(tx1 - 12, back - 12, tx1 - 9, back - 16, "#c8bca4"); cv.line(tx1 - 6, back - 12, tx1 - 9, back - 16, "#c8bca4")
    elif variant == "treadmill":
        monitor(cv, cx, back, 30, 19, "dash", seed + 2)
        cv.rect(tx0 + 6, back - 2, 14, 4, IRON[1]); cv.hline(tx0 + 6, back - 2, 14, IRON[3])     # keyboard
        cv.ellipse(tx1 - 16, back - 4, 7, 8, "#3a8a5a"); cv.rect(tx1 - 15, back + 1, 5, 4, "#c47a5a")   # succulent
        cv.rect(tx1 - 8, back - 6, 5, 8, "#4a7ad8"); cv.hline(tx1 - 8, back - 6, 5, "#8ab0f0")          # water bottle
        cv.rect(tx1 - 7, back - 8, 3, 2, IRON[2])
        cv.rect(cx - 10, back + 4, 20, 3, IRON[2])                                                  # treadmill console strap
    elif variant == "triple":
        for k, (dx, kind) in enumerate([(-24, "dash"), (0, "code"), (24, "fish")]):
            monitor(cv, cx + dx, back, 23, 16, kind, seed + 3 + k)
        cv.rect(cx - 10, back + 3, 20, 3, IRON[1]); cv.hline(cx - 10, back + 3, 20, IRON[3])
        cv.ellipse(cx + 14, back + 3, 6, 4, IRON[2])
        cv.rect(tx0 + 3, back + 2, 5, 5, "#f2ecdc"); cv.vline(tx0 + 8, back + 3, 2, "#f2ecdc")
    elif variant == "cleared":
        monitor(cv, cx - 12, back, 26, 17, "off", seed + 4)
        # a banker's box with a plant, a framed photo and a mug sticking out
        bx = cx + 6
        cv.rect(bx, back - 10, 24, 15, OUT); cv.rect(bx + 1, back - 9, 22, 13, "#d8c8a4"); cv.hline(bx + 1, back - 9, 22, "#ece0c2")
        cv.rect(bx + 8, back - 6, 8, 3, "#8a7a5a")
        cv.ellipse(bx + 3, back - 22, 9, 13, LEAF[3]); cv.ellipse(bx + 5, back - 20, 5, 8, LEAF[4])
        cv.rect(bx + 14, back - 16, 7, 7, OUT); cv.rect(bx + 15, back - 15, 5, 5, "#8ab8ec")
    return cv, cx, base


def rolling_whiteboard(width=64, height=66, seed=0):
    """A double-sided whiteboard on a steel frame with casters; the side we see is mid-brainstorm."""
    rng = _rng(seed)
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 2, width // 2, 3)
    for lx in (ox + 3, ox + width - 6):
        cv.rect(lx, base - height + 2, 3, height - 6, OUT); cv.vline(lx + 1, base - height + 2, height - 7, CHROME[3])
        cv.rect(lx - 4, base - 5, 11, 3, OUT); cv.hline(lx - 3, base - 4, 9, CHROME[2])
        cv.rect(lx - 3, base - 3, 3, 3, OUT); cv.rect(lx + 3, base - 3, 3, 3, OUT)
    bx, by, bw, bh = ox, base - height + 2, width, 40
    cv.rect(bx, by, bw, bh, OUT); cv.rect(bx + 1, by + 1, bw - 2, bh - 2, CHROME[3])
    cv.rect(bx + 2, by + 2, bw - 4, bh - 4, WHITE[3])
    cv.line(bx + 3, by + 3, bx + 10, by + bh - 4, C(WHITE[4], 0.7))
    # user journey: boxes and arrows, a frowning face, KYLE'S IDEA
    for k in range(3):
        x = bx + 5 + k * 19
        cv.rect(x, by + 6, 13, 9, MARKER[k]); cv.rect(x + 1, by + 7, 11, 7, WHITE[3])
        cv.hline(x + 3, by + 10, 6, MARKER[3])
        if k < 2:
            cv.hline(x + 13, by + 10, 5, MARKER[3]); cv.px(x + 16, by + 9, MARKER[3]); cv.px(x + 16, by + 11, MARKER[3])
    micro_text(cv, "WHY?", bx + 6, by + 20, MARKER[1])
    cv.ellipse(bx + 34, by + 19, 10, 10, MARKER[3]); cv.ellipse(bx + 35, by + 20, 8, 8, WHITE[3])
    cv.px(bx + 37, by + 22, MARKER[3]); cv.px(bx + 40, by + 22, MARKER[3]); cv.hline(bx + 37, by + 26, 4, MARKER[3]); cv.px(bx + 36, by + 27, MARKER[3]); cv.px(bx + 41, by + 27, MARKER[3])
    micro_text(cv, "PIVOT?", bx + 6, by + 29, MARKER[0])
    cv.rect(bx + bw - 12, by + 25, 7, 7, STICKY[0]); cv.rect(bx + bw - 20, by + 27, 7, 7, STICKY[1])
    cv.rect(bx + 4, by + bh - 1, bw - 8, 3, OUT); cv.hline(bx + 5, by + bh, bw - 10, CHROME[3])
    cv.rect(bx + 10, by + bh - 2, 5, 2, MARKER[0]); cv.rect(bx + 17, by + bh - 2, 5, 2, MARKER[1])
    return cv, cx, base


def ping_pong_p(width=120, height=46, seed=0):
    """Tournament ping-pong table seen from its long side at a 3/4 angle: the blue top shows
    depth, white lines, a sagging net, a paddle and balls; DISRUPTR stencilled on the side."""
    cv = Canvas(width + 8, height + 6, seed=seed)
    ox, base = 4, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 3, width // 2 + 2, 4)
    top = base - 24
    depth = 18
    # legs + undercarriage
    for lx in (ox + 10, ox + width - 13):
        cv.rect(lx, top + 3, 4, base - top - 4, OUT); cv.vline(lx + 1, top + 3, base - top - 5, CHROME[2])
        cv.rect(lx - 3, base - 3, 10, 3, OUT); cv.hline(lx - 2, base - 2, 8, CHROME[1])
    cv.rect(cx - 2, top + 3, 4, base - top - 6, OUT)
    cv.rect(ox + 14, top + 8, width - 28, 2, IRON[1])
    # table top (parallelogram-ish: back edge slightly inset)
    cv.poly([(ox + 3, top - depth), (ox + width - 3, top - depth), (ox + width, top), (ox, top)], OUT)
    cv.poly([(ox + 4, top - depth + 1), (ox + width - 4, top - depth + 1), (ox + width - 1, top - 1), (ox + 1, top - 1)], "#1e4a8a")
    for yy in range(top - depth + 1, top):
        if (yy - top) % 4 == 0:
            cv.hline(ox + 6, yy, width - 12, "#24549a")
    cv.line(ox + 4, top - depth + 1, ox + width - 4, top - depth + 1, "#f2f2ea")
    cv.line(ox + 1, top - 1, ox + width - 1, top - 1, "#f2f2ea")
    cv.line(ox + 4, top - depth + 1, ox + 1, top - 1, "#f2f2ea"); cv.line(ox + width - 4, top - depth + 1, ox + width - 1, top - 1, "#f2f2ea")
    cv.hline(ox + 4, top - depth // 2, width - 8, C("#f2f2ea", 0.7))
    # table edge (front apron) with the stencil
    cv.rect(ox, top, width, 4, "#163a6e"); cv.hline(ox, top, width, "#2a5a9a"); cv.hline(ox, top + 3, width, OUT)
    # net across the middle, sagging
    for yy in range(top - depth - 6, top + 1):
        t = (yy - (top - depth - 6)) / (depth + 6)
        sag = int(2 * np.sin(np.pi * t))
        cv.px(cx + sag - 1 + int((top - yy) * 0.15), yy, OUT)
    for yy in range(top - depth - 5, top - 1, 2):
        t = (yy - (top - depth - 6)) / (depth + 6)
        x = cx + int((top - yy) * 0.15) + int(2 * np.sin(np.pi * t))
        cv.rect(x, yy, 2, 1, "#e6e6de")
    cv.rect(cx + 1, top - 7, 3, 7, OUT); cv.rect(cx + 2, top - 6, 1, 5, "#f2f2ea")
    cv.rect(cx - 1 + int(depth * 0.15), top - depth - 8, 3, 4, CHROME[3])
    # the BALLS ARE A BENEFIT sign taped to the net
    cv.rect(cx - 9, top - 13, 12, 7, "#f2ecdc"); cv.hline(cx - 8, top - 11, 9, "#5a5a68"); cv.hline(cx - 8, top - 9, 7, "#5a5a68")
    # paddles and balls
    for (px_, py_, c) in [(ox + 24, top - 12, "#c83a3a"), (ox + width - 34, top - 8, "#2a2a36")]:
        cv.ellipse(px_, py_, 9, 7, OUT); cv.ellipse(px_ + 1, py_ + 1, 7, 5, c); cv.rect(px_ + 8, py_ + 3, 6, 2, WOOD[4])
    cv.ellipse(cx + 18, top - 14, 3, 3, "#f6f2e6"); cv.ellipse(ox + width - 16, base - 1, 3, 3, "#f6a24a")
    return cv, cx, base


def sofa_back(width=124, height=38, seed=0):
    """A cognac leather sofa seen from behind, facing the screen: rolled arms, three cushion backs,
    a fleece vest and a laptop left on top."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base - 1, width // 2 + 2, 3)
    for lx in (ox + 6, ox + width - 9):
        cv.rect(lx, base - 5, 3, 5, OUT); cv.vline(lx + 1, base - 5, 4, WOOD[1])
    cv.rect(ox + 4, base - 31, width - 8, 27, OUT)
    cv.rect(ox + 5, base - 30, width - 10, 25, COGNAC[3])
    cv.hline(ox + 5, base - 30, width - 10, COGNAC[5]); cv.hline(ox + 5, base - 29, width - 10, COGNAC[4])
    for k in range(1, 3):                                     # seams between the three backs
        sx = ox + 4 + k * (width - 8) // 3
        cv.vline(sx, base - 29, 22, COGNAC[1]); cv.vline(sx + 1, base - 29, 22, COGNAC[4])
    for yy in range(base - 22, base - 6, 5):
        cv.hline(ox + 6, yy, width - 12, COGNAC[2])
    cv.rect(ox + 5, base - 8, width - 10, 3, COGNAC[1])
    for ax in (ox, ox + width - 10):                           # rolled arms
        cv.rect(ax, base - 30, 10, 26, OUT); cv.rect(ax + 1, base - 29, 8, 24, COGNAC[2])
        cv.ellipse(ax, base - 33, 10, 8, OUT); cv.ellipse(ax + 1, base - 32, 8, 6, COGNAC[4]); cv.hline(ax + 2, base - 31, 5, COGNAC[5])
    # vest over the back, a laptop's edge
    vx = ox + 30
    cv.rect(vx, base - 33, 16, 14, OUT); cv.rect(vx + 1, base - 32, 14, 12, FLEECE[2]); cv.vline(vx + 8, base - 32, 12, FLEECE[1])
    cv.rect(vx + 3, base - 30, 2, 2, "#e84a98")
    cv.rect(ox + width - 44, base - 34, 20, 4, OUT); cv.rect(ox + width - 43, base - 33, 18, 2, CHROME[3])
    return cv, ox + width // 2, base


def gong_stand(width=40, height=58, seed=0):
    """The sales gong: a bronze disc on cords in a black frame, mallet hooked on the side."""
    cv = Canvas(width + 10, height + 6, seed=seed)
    ox, base = 5, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 2, width // 2, 3)
    for lx in (ox + 2, ox + width - 5):
        cv.rect(lx, base - height + 4, 4, height - 6, OUT); cv.vline(lx + 1, base - height + 4, height - 7, IRON[3])
        cv.rect(lx - 4, base - 4, 12, 3, OUT); cv.hline(lx - 3, base - 3, 10, IRON[2])
    cv.rect(ox, base - height + 2, width, 5, OUT); cv.rect(ox + 1, base - height + 3, width - 2, 3, "#a83a2a"); cv.hline(ox + 1, base - height + 3, width - 2, "#c85a3a")
    cv.rect(ox - 2, base - height + 1, 4, 7, OUT); cv.rect(ox + width - 2, base - height + 1, 4, 7, OUT)
    r = 13
    gy = base - height + 20
    cv.line(cx - 6, base - height + 7, cx - 4, gy - r + 1, "#c8a86a"); cv.line(cx + 6, base - height + 7, cx + 4, gy - r + 1, "#c8a86a")
    cv.ellipse(cx - r, gy - r + 2, r * 2 + 1, r * 2 + 1, OUT)
    cv.ellipse(cx - r + 1, gy - r + 3, r * 2 - 1, r * 2 - 1, "#a8742a")
    cv.ellipse(cx - r + 3, gy - r + 5, r * 2 - 5, r * 2 - 5, "#c8923a")
    cv.ellipse(cx - 5, gy - 3, 10, 10, "#a8742a"); cv.ellipse(cx - 3, gy - 1, 6, 6, "#e0b45a")
    cv.px(cx - 6, gy - 7, "#fff0b0"); cv.px(cx - 5, gy - 8, "#f6d67a")
    # mallet with its price tag
    mx = ox + width + 1
    cv.line(mx, base - 34, mx - 1, base - 16, WOOD[4]); cv.ellipse(mx - 3, base - 38, 7, 6, OUT); cv.ellipse(mx - 2, base - 37, 5, 4, "#e6d6b1")
    cv.rect(mx + 1, base - 26, 4, 3, "#f2ecdc")
    # little sign: RING WHEN WE CLOSE
    cv.rect(ox + 4, base - 13, width - 8, 7, "#f2ecdc"); micro_text(cv, "RING ME", cx - micro_width("RING ME") // 2, base - 12, "#a83a2a")
    return cv, cx, base


def tall_plant(width=34, height=64, kind="fig", seed=0):
    """A fiddle-leaf fig or a snake plant in a white ceramic pot on a wooden stand."""
    rng = _rng(seed)
    cv = Canvas(width + 10, height + 6, seed=seed)
    ox, base = 5, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 1, width // 2 - 4, 2)
    pw, ph = 18, 15
    if kind == "fig":
        cv.vline(cx, base - height + 10, height - ph - 8, WOOD[2]); cv.vline(cx + 1, base - height + 10, height - ph - 8, WOOD[1])
        for k in range(13):
            ly = base - height + 4 + k * 3 + int(rng.integers(-2, 3))
            side = -1 if k % 2 else 1
            lx = cx + side * int(rng.integers(3, 11))
            c = LEAF[3] if ly < base - height + 22 else LEAF[2]
            cv.ellipse(lx - 5, ly - 4, 11, 9, OUT)
            cv.ellipse(lx - 4, ly - 3, 9, 7, c)
            cv.ellipse(lx - 3, ly - 3, 5, 3, LEAF[4] if k % 3 else LEAF[5])
            cv.line(lx - 2 * side, ly + 2, lx + 2 * side, ly - 2, LEAF[1])
    else:
        for k in range(8):
            lx = cx - 7 + k * 2
            lh = int(rng.integers(height - 34, height - 20))
            lean = int(rng.integers(-3, 4))
            for i in range(lh):
                t = i / lh
                w = 3 if t < 0.8 else 2
                cv.rect(lx + int(lean * t), base - ph - i, w, 1, LEAF[3] if (i // 5) % 2 else "#5a7a3a")
            cv.px(lx + lean, base - ph - lh, "#c8c06a")
    # pot on a mid-century stand
    py = base - ph - 4
    cv.rect(cx - pw // 2 - 1, py, pw + 2, ph + 1, OUT)
    cv.rect(cx - pw // 2, py + 1, pw, ph - 1, "#e6e2d8"); cv.vline(cx - pw // 2, py + 1, ph - 1, "#f6f2ea"); cv.vline(cx + pw // 2 - 1, py + 1, ph - 1, "#b8b2a6")
    cv.hline(cx - pw // 2, py + 3, pw, "#c8c2b6")
    for lx in (cx - 7, cx + 6):
        cv.line(lx, base - 4, lx + (-2 if lx < cx else 2), base, WOOD[3])
    return cv, cx, base


# --------------------------------------------------------------------------- break room (P02)

def snack_wall(cv, x, y, w, h, seed=0):
    """Pegboard wall of clear gravity bins and shelves: candy, nuts, chips, bars, PROTEIN DUST."""
    rng = _rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT)
    cv.rect(x - 1, y - 1, w + 2, h + 2, "#b8946a")
    cv.rect(x, y, w, h, "#d8b888")
    for py in range(y + 2, y + h, 4):
        for px_ in range(x + 2, x + w, 4):
            cv.px(px_, py, "#a8845a")
    # top: FUEL letters
    s = "FUEL"
    cv.rect(x + w // 2 - 16, y + 2, 32, 11, "#1e2234"); text(cv, s, x + w // 2 - text_width(s) // 2, y + 3, "#f2d84a")
    # two rows of gravity bins
    fills = ["#e84a3a", "#f2d84a", "#6a3a1e", "#f2a24a", "#a8e07a", "#e84a98", "#c8a070", "#5a3a8a", "#f2f2ea", "#3a8ad8"]
    bw, bh = 13, 22
    for r in range(2):
        for k in range((w - 6) // (bw + 2)):
            bx, by = x + 4 + k * (bw + 2), y + 16 + r * (bh + 6)
            c = fills[int(rng.integers(len(fills)))]
            cv.rect(bx, by, bw, bh, OUT)
            cv.rect(bx + 1, by + 1, bw - 2, bh - 6, "#d8e4ec")
            lvl = int(rng.integers(3, bh - 8))
            cv.rect(bx + 1, by + bh - 5 - lvl, bw - 2, lvl, c)
            for _ in range(lvl * 2):
                cv.px(bx + 1 + int(rng.integers(0, bw - 2)), by + bh - 5 - int(rng.integers(1, lvl + 1)), shade(c, float(rng.choice([-0.25, 0.2]))))
            cv.vline(bx + 2, by + 1, bh - 7, C("#ffffff", 0.45))
            cv.rect(bx + 3, by + bh - 5, bw - 6, 4, CHROME[2]); cv.rect(bx + bw // 2 - 1, by + bh - 2, 3, 2, CHROME[3])   # dispenser lever
    # bottom shelf: chip bags and bar boxes
    sy = y + h - 14
    cv.rect(x + 2, sy + 10, w - 4, 3, WOOD[3]); cv.hline(x + 2, sy + 10, w - 4, WOOD[5])
    xx = x + 4
    while xx < x + w - 10:
        c = ["#e84a3a", "#3a8ad8", "#f2d84a", "#2a9a6a", "#e86a2a", "#8a3ab8"][int(rng.integers(6))]
        bw2 = int(rng.integers(7, 11)); bh2 = int(rng.integers(7, 11))
        cv.rect(xx, sy + 10 - bh2, bw2, bh2, OUT); cv.rect(xx + 1, sy + 11 - bh2, bw2 - 2, bh2 - 2, c)
        cv.hline(xx + 1, sy + 11 - bh2, bw2 - 2, shade(c, 0.3)); cv.rect(xx + 2, sy + 13 - bh2, bw2 - 4, 2, "#f2f2ea")
        xx += bw2 + 1


def kegerator(cv, cx, base, w=50, h=56):
    """Kombucha kegerator: stainless box with a three-tap tower, drip tray, a chalk menu above, and
    one tap handle taped over."""
    x0 = cx - w // 2
    top = base - h + 18
    cv.rect(x0, top, w, base - top, OUT)
    cv.rect(x0 + 1, top + 1, w - 2, base - top - 3, CHROME[3]); cv.vline(x0 + 1, top + 1, base - top - 3, CHROME[4])
    for k in range(x0 + 4, x0 + w - 3, 3):
        cv.vline(k, top + 3, base - top - 8, CHROME[2] if k % 2 else CHROME[3])
    cv.rect(x0 + w - 8, top + 6, 3, 14, CHROME[1])
    cv.rect(x0 + 1, base - 5, w - 2, 3, IRON[1])
    cv.rect(x0 + 4, top + 26, 23, 7, "#f2ecdc"); micro_text(cv, "BOOCH", x0 + 6, top + 27, "#3a8a5a")
    # tower
    tw = 34
    tx = cx - tw // 2
    cv.rect(tx, top - 18, tw, 10, OUT); cv.rect(tx + 1, top - 17, tw - 2, 8, CHROME[3]); cv.hline(tx + 1, top - 17, tw - 2, CHROME[4])
    cv.rect(cx - 3, top - 8, 7, 9, OUT); cv.rect(cx - 2, top - 8, 5, 8, CHROME[2])
    handles = [("#d8a24a", "G"), ("#c83a6a", "H"), ("#2a2a34", "?")]
    for k, (c, lab) in enumerate(handles):
        hx = tx + 5 + k * 12
        cv.rect(hx, top - 28, 5, 11, OUT); cv.rect(hx + 1, top - 27, 3, 9, c); cv.vline(hx + 1, top - 27, 9, shade(c, 0.3))
        cv.rect(hx + 1, top - 9, 3, 3, CHROME[4]); cv.px(hx + 2, top - 6, CHROME[2])
    cv.rect(tx + 28, top - 24, 5, 4, "#e6dcc6")                     # tape over the third handle
    cv.rect(tx + 2, top - 2, tw - 4, 3, IRON[2]); cv.hline(tx + 2, top - 2, tw - 4, CHROME[2])    # drip tray
    return top - 28


def chalk_menu(cv, x, y, w=60, h=42):
    cv.rect(x - 2, y - 2, w + 4, h + 4, WOOD[2]); cv.hline(x - 2, y - 2, w + 4, WOOD[4])
    cv.rect(x, y, w, h, "#1e2420")
    for _ in range(40):
        cv.px(x + int(_ * 37 % w), y + int(_ * 53 % h), "#2a322c")
    micro_text(cv, "ON TAP", x + w // 2 - micro_width("ON TAP") // 2, y + 3, "#f2ecdc")
    cv.hline(x + 10, y + 9, w - 20, "#a8a89a")
    for k, (s, c) in enumerate([("GINGER", "#e8c24a"), ("HIBISCUS", "#f28ab0"), ("KYLE'S SCOBY", "#8ad8f0")]):
        micro_text(cv, s, x + 4, y + 13 + k * 8, c)
    cv.line(x + 4, y + 31, x + 4 + micro_width("KYLE'S SCOBY"), y + 31, "#e84a3a")
    micro_text(cv, "DO NOT", x + w - micro_width("DO NOT") - 3, y + h - 7, "#e84a3a")


def sticker_fridge(cv, cx, base, w=42, h=92, seed=0):
    """Tall stainless fridge, doors papered in stickers (mountains, skis, bands, dead startups),
    a magnet whiteboard, a takeout menu."""
    rng = _rng(seed)
    x0, top = cx - w // 2, base - h
    cv.rect(x0, top, w, h, OUT)
    cv.rect(x0 + 1, top + 1, w - 2, h - 3, CHROME[3]); cv.vline(x0 + 1, top + 1, h - 3, CHROME[4]); cv.vline(x0 + w - 2, top + 1, h - 3, CHROME[2])
    split = top + 30
    cv.hline(x0 + 1, split, w - 2, OUT); cv.hline(x0 + 1, split + 1, w - 2, CHROME[2])
    for hy0, hy1 in [(top + 18, split - 3), (split + 5, split + 30)]:
        cv.rect(x0 + w - 6, hy0, 3, hy1 - hy0, CHROME[1]); cv.vline(x0 + w - 6, hy0, hy1 - hy0, CHROME[4])
    cols = ["#e84a98", "#3a8ad8", "#f2d84a", "#2a9a6a", "#f2f2ea", "#e86a2a", "#8a3ab8", "#c83a3a", "#1e2234", "#a8e07a"]
    for _ in range(int(w * h / 22)):
        sx, sy = x0 + 3 + int(rng.integers(0, w - 12)), top + 3 + int(rng.integers(0, h - 10))
        if abs(sy - split) < 2:
            continue
        kind = rng.random()
        c = cols[int(rng.integers(len(cols)))]
        if kind < 0.3:
            cv.ellipse(sx, sy, 5, 5, OUT); cv.ellipse(sx + 1, sy + 1, 3, 3, c)
        elif kind < 0.55:
            cv.rect(sx, sy, 7, 4, c); cv.hline(sx + 1, sy + 2, 5, shade(c, -0.4) if c != "#1e2234" else "#f2f2ea")
        elif kind < 0.75:                                           # mountain sticker
            cv.rect(sx, sy, 7, 6, "#f2f2ea"); cv.poly([(sx + 1, sy + 5), (sx + 3, sy + 1), (sx + 6, sy + 5)], "#2a5a9a")
        else:
            cv.rect(sx, sy, 5, 5, c); cv.px(sx + 2, sy + 2, "#f2f2ea")
    # the DISRUPTR sticker on top, a small magnet whiteboard
    cv.rect(x0 + 5, top + 6, micro_width("DISRUPTR") + 4, 7, "#16182a"); micro_text(cv, "DISRUPTR", x0 + 7, top + 7, "#e84a98")
    cv.rect(x0 + 6, split + 36, 24, 16, OUT); cv.rect(x0 + 7, split + 37, 22, 14, WHITE[4])
    micro_text(cv, "MILK?", x0 + 8, split + 39, MARKER[0]); cv.hline(x0 + 9, split + 46, 12, MARKER[1])
    cv.rect(x0 + 2, base - 4, w - 4, 2, IRON[1])


def counter_run(cv, x, base, w, seed=0, shelf_from=6):
    """Kitchenette: walnut-stained base cabinets, a quartz top, an undermount sink and a gooseneck
    tap, an espresso machine with a DESCALE screen, oat milk, a grinder; open shelves of mugs above."""
    rng = _rng(seed)
    top = base - 34
    cv.rect(x, top + 4, w, base - top - 4, OUT)
    cv.rect(x + 1, top + 5, w - 2, base - top - 7, "#4a3426")
    for k, dx in enumerate(range(x + 1, x + w - 1, 22)):
        dw = min(21, x + w - 1 - dx)
        cv.rect(dx + 1, top + 7, dw - 2, base - top - 13, "#5e4230"); cv.hline(dx + 1, top + 7, dw - 2, "#76543c")
        cv.rect(dx + dw // 2 - 3, top + 10, 6, 1, CHROME[3])
    cv.rect(x + 1, base - 5, w - 2, 3, "#1a1210")
    cv.rect(x - 2, top, w + 4, 5, OUT); cv.rect(x - 1, top + 1, w + 2, 3, "#d6d2ca"); cv.hline(x - 1, top + 1, w + 2, "#eeeae4")
    # sink + tap
    sx = x + 14
    cv.rect(sx, top + 1, 22, 2, "#8a8e98")
    cv.vline(sx + 11, top - 12, 12, CHROME[3]); cv.hline(sx + 11, top - 12, 6, CHROME[3]); cv.vline(sx + 16, top - 12, 3, CHROME[3])
    cv.px(sx + 12, top - 12, CHROME[4])
    cv.rect(sx + 24, top - 7, 5, 7, "#f2f2ea"); cv.hline(sx + 24, top - 7, 5, "#3a8a5a")            # soap
    # espresso machine
    ex = x + w - 46
    cv.rect(ex, top - 22, 30, 22, OUT); cv.rect(ex + 1, top - 21, 28, 20, CHROME[3]); cv.hline(ex + 1, top - 21, 28, CHROME[4])
    cv.rect(ex + 3, top - 18, 12, 6, "#101820"); micro_text(cv, "DESC", ex + 4, top - 17, "#e8a84a")
    cv.rect(ex + 17, top - 18, 4, 4, IRON[1]); cv.rect(ex + 22, top - 18, 4, 4, IRON[1])
    cv.rect(ex + 6, top - 9, 16, 3, IRON[2]); cv.rect(ex + 12, top - 6, 4, 3, IRON[1])
    cv.rect(ex + 11, top - 3, 6, 3, "#f2f2ea")
    cv.rect(ex + 31, top - 14, 8, 14, "#e6dcc6"); cv.rect(ex + 32, top - 10, 6, 4, "#5a7ad8")       # oat milk
    cv.rect(x + 42, top - 16, 9, 16, OUT); cv.rect(x + 43, top - 15, 7, 6, "#6a3a1e"); cv.rect(x + 43, top - 9, 7, 9, IRON[2])   # grinder
    # open shelves with mugs
    for r, sy in enumerate((top - 44, top - 66)):
        sw = w - 6 - shelf_from
        cv.rect(x + shelf_from, sy, sw, 3, WOOD[3]); cv.hline(x + shelf_from, sy, sw, WOOD[5]); cv.rect(x + shelf_from, sy + 3, sw, 1, C(SHADOW, 0.4))
        for bx in (x + shelf_from + 3, x + w - 10):
            cv.rect(bx, sy + 3, 2, 4, IRON[2])                                     # brackets
        xx = x + shelf_from + 3
        while xx < x + w - 14:
            c = ["#f2f2ea", "#e84a98", "#1e2234", "#f2d84a", "#3a8ad8", "#e86a2a"][int(rng.integers(6))]
            if rng.random() < 0.75:
                cv.rect(xx, sy - 7, 6, 7, OUT); cv.rect(xx + 1, sy - 6, 4, 6, c); cv.rect(xx + 6, sy - 5, 2, 3, OUT)
                xx += 9
            else:
                cv.rect(xx, sy - 10, 5, 10, OUT); cv.rect(xx + 1, sy - 9, 3, 8, "#c89a5a"); cv.rect(xx + 1, sy - 7, 3, 3, "#f2ecdc")   # jar
                xx += 7
    cv.rect(sx - 2, top - 30, 28, 9, "#f2ecdc"); micro_text(cv, "WASH IT", sx, top - 28, "#c83a3a")    # over the sink
    return top


def waste_bins(cv, x, base):
    """Four bins against the wall: COMPOST, RECYCLE, LANDFILL and EQUITY."""
    for k, (lab, c) in enumerate([("C", "#2a8a4a"), ("R", "#2a5ab0"), ("L", "#3a3a44"), ("E", "#c8962e")]):
        bx = x + k * 13
        cv.rect(bx, base - 24, 12, 24, OUT); cv.rect(bx + 1, base - 23, 10, 21, c); cv.vline(bx + 1, base - 23, 21, shade(c, 0.25))
        cv.rect(bx, base - 27, 12, 4, OUT); cv.rect(bx + 1, base - 26, 10, 2, shade(c, 0.15))
        cv.rect(bx + 3, base - 18, 6, 7, "#f2f2ea"); micro_text(cv, lab, bx + 5, base - 17, c)


def letterboard(cv, x, y, lines, w=56):
    h = 6 + len(lines) * 7
    cv.rect(x - 2, y - 2, w + 4, h + 4, WOOD[3]); cv.hline(x - 2, y - 2, w + 4, WOOD[5])
    cv.rect(x, y, w, h, "#16161c")
    for yy in range(y + 1, y + h, 2):
        cv.hline(x, yy, w, "#1e1e26")
    for k, s in enumerate(lines):
        micro_text(cv, s, x + w // 2 - micro_width(s) // 2, y + 4 + k * 7, "#f2f2ea")


def beanbag_big(width=54, height=40, seed=0):
    """A huge orange corduroy beanbag slumped against nothing: a tall back that has folded over,
    a seat hollow on the front-left, a teal throw and a laptop half sliding off."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 2, width // 2 + 1, 3)
    body = [(ox + 2, base - 8), (ox + 4, base - 18), (ox + 14, base - 26), (ox + 30, base - height + 4), (ox + 44, base - height + 2),
            (ox + width - 2, base - 24), (ox + width - 1, base - 10), (ox + width - 8, base - 2), (ox + 8, base - 1)]
    cv.poly([(x + dx, y + dy) for (x, y) in body for (dx, dy) in [(0, 0)]], OUT)
    inner = [(x + (1 if x < cx else -1), y + 1) for (x, y) in body]
    cv.poly(inner, ORANGE[2])
    # the back hump, lit from the upper left, folded over at the top
    cv.ellipse(ox + 26, base - height + 3, 26, 22, ORANGE[3])
    cv.ellipse(ox + 30, base - height + 4, 14, 8, ORANGE[4])
    cv.line(ox + 28, base - height + 14, ox + 48, base - height + 10, ORANGE[1])
    # the seat hollow in front of it
    cv.ellipse(ox + 8, base - 22, 30, 14, ORANGE[1]); cv.ellipse(ox + 11, base - 20, 22, 9, ORANGE[2])
    cv.hline(ox + 12, base - 21, 14, ORANGE[3])
    # corduroy wales across the front, darker underside
    for k in range(ox + 4, ox + width - 4, 3):
        for yy in range(base - 10, base - 3, 2):
            cv.px(k, yy, ORANGE[1])
    cv.hline(ox + 8, base - 3, width - 16, ORANGE[0])
    # teal throw over the right side, a laptop sliding off the seat
    cv.poly([(ox + width - 16, base - 26), (ox + width - 2, base - 22), (ox + width - 3, base - 8), (ox + width - 16, base - 12)], TEAL_P[3])
    for k in range(4):
        cv.line(ox + width - 15 + k * 3, base - 25 + k, ox + width - 15 + k * 3, base - 12 + k // 2, TEAL_P[2])
    cv.hline(ox + width - 16, base - 26, 10, TEAL_P[4])
    cv.poly([(ox + 12, base - 22), (ox + 26, base - 24), (ox + 28, base - 19), (ox + 14, base - 17)], OUT)
    cv.poly([(ox + 13, base - 22), (ox + 25, base - 23), (ox + 27, base - 19), (ox + 15, base - 18)], CHROME[3])
    cv.px(ox + 20, base - 21, "#e84a98")
    return cv, cx, base


def foosball(width=70, height=38, seed=0):
    """A foosball table from the side at a 3/4 angle: walnut box, green pitch, chrome rods with
    red and blue men, the score beads; one blue goalie glued in place."""
    cv = Canvas(width + 16, height + 6, seed=seed)
    ox, base = 8, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 3, width // 2 + 2, 4)
    top = base - 24
    depth = 14
    for lx in (ox + 3, ox + width - 7):
        cv.rect(lx, top + 4, 5, base - top - 5, OUT); cv.rect(lx + 1, top + 4, 3, base - top - 6, WOOD[2])
        cv.rect(lx - 1, base - 3, 7, 3, OUT)
    cv.rect(ox, top - depth - 1, width, depth + 10, OUT)
    cv.rect(ox + 1, top - depth, width - 2, depth, "#2e6a3a")
    cv.hline(ox + 1, top - depth, width - 2, WOOD[4]); cv.vline(ox + width // 2, top - depth + 1, depth - 1, "#e6e6de")
    cv.ellipse(cx - 4, top - depth // 2 - 3, 8, 6, C("#e6e6de", 0.0)); cv.px(cx - 3, top - depth // 2, "#e6e6de"); cv.px(cx + 3, top - depth // 2, "#e6e6de")
    cv.rect(ox + 1, top, width - 2, 8, WOOD[3]); cv.hline(ox + 1, top, width - 2, WOOD[5]); cv.hline(ox + 1, top + 7, width - 2, WOOD[1])
    # rods (receding) with men
    for k, rx in enumerate(range(ox + 6, ox + width - 4, 8)):
        col = "#c83a3a" if k % 2 == 0 else "#2a5ab0"
        cv.line(rx - 3, top + 3, rx + 3, top - depth - 3, CHROME[3])
        cv.rect(rx - 6, top + 2, 4, 2, OUT); cv.rect(rx + 2, top - depth - 4, 3, 2, OUT)   # handles out each side
        for j in range(1 + (k % 3)):
            t = (j + 1) / (2 + (k % 3))
            mx = int(rx - 3 + 6 * t); my = int(top + 3 - (depth + 6) * t)
            cv.rect(mx - 1, my - 1, 3, 4, OUT); cv.rect(mx, my, 1, 2, col)
    for k in range(5):
        cv.px(ox + 6 + k * 2, top - depth - 2, "#f2ecdc"); cv.px(ox + width - 16 + k * 2, top - depth - 2, "#f2ecdc")
    cv.ellipse(cx + 6, top - 9, 3, 3, "#f6f2e6")
    return cv, cx, base


def high_top(width=72, height=52, seed=0):
    """Reclaimed-wood high-top on a black pipe base with two stools; a sticker-covered laptop
    and the WORLD'S OKAYEST FOUNDER mug."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 3, width // 2 + 1, 4)
    top_front = base - 30
    depth = 12
    cv.rect(cx - 2, top_front + 2, 5, base - top_front - 5, OUT); cv.vline(cx - 1, top_front + 2, base - top_front - 6, IRON[3])
    cv.ellipse(cx - 10, base - 5, 21, 5, OUT); cv.ellipse(cx - 9, base - 4, 19, 3, IRON[2])
    cv.rect(cx - 16, top_front - depth - 1, 33, depth + 5, OUT)
    for yy in range(top_front - depth, top_front + 1):
        cv.hline(cx - 15, yy, 31, WOOD[4] if (yy - top_front) % 4 else WOOD[3])
    cv.hline(cx - 15, top_front - depth, 31, WOOD[5]); cv.rect(cx - 15, top_front + 1, 31, 2, WOOD[2])
    lx = cx - 12
    cv.rect(lx, top_front - 9, 14, 6, OUT); cv.rect(lx + 1, top_front - 8, 12, 4, CHROME[3])
    for k, c in enumerate(["#e84a98", "#f2d84a", "#3a8ad8", "#2a9a6a"]):
        cv.rect(lx + 2 + k * 3, top_front - 7, 2, 2, c)
    cv.rect(cx + 6, top_front - 9, 6, 7, OUT); cv.rect(cx + 7, top_front - 8, 4, 5, "#f2f2ea"); cv.rect(cx + 12, top_front - 7, 2, 3, OUT)
    for sx in (ox + 6, ox + width - 14):                                   # stools
        cv.rect(sx, base - 26, 12, 4, OUT); cv.rect(sx + 1, base - 25, 10, 2, "#2a2a34"); cv.hline(sx + 1, base - 25, 10, "#4a4a58")
        cv.line(sx + 2, base - 22, sx, base - 1, IRON[3]); cv.line(sx + 9, base - 22, sx + 11, base - 1, IRON[3])
        cv.hline(sx + 1, base - 9, 10, IRON[2])
    return cv, cx, base


def dog_bed(width=44, height=22, seed=0):
    """The office dog asleep in a round bed embroidered SEED ROUND."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 2, width // 2, 3)
    cv.ellipse(ox, base - height + 2, width, height - 2, OUT)
    cv.ellipse(ox + 1, base - height + 3, width - 2, height - 4, "#3a4a7a")
    cv.ellipse(ox + 5, base - height + 5, width - 10, height - 10, "#c8b89a")
    # the dog: golden, curled, nose to tail
    dx, dy = ox + 9, base - height + 4
    cv.ellipse(dx, dy, 26, 12, OUT); cv.ellipse(dx + 1, dy + 1, 24, 10, "#c88a3a"); cv.ellipse(dx + 3, dy + 1, 16, 5, "#e0a84a")
    cv.ellipse(dx + 18, dy + 3, 10, 8, OUT); cv.ellipse(dx + 19, dy + 4, 8, 6, "#d8983e")
    cv.rect(dx + 21, dy + 4, 4, 3, "#a86a2a")                              # ear
    cv.px(dx + 26, dy + 8, OUT); cv.hline(dx + 22, dy + 7, 2, "#7a4a1e")   # nose, closed eye
    cv.line(dx + 2, dy + 8, dx + 14, dy + 10, "#e0a84a")                  # tail over the nose
    cv.rect(cx - 13, base - 6, 26, 5, "#3a4a7a"); micro_text(cv, "SEED ROUND", cx - micro_width("SEED ROUND") // 2, base - 6, "#f2d84a")
    return cv, cx, base


def kegs(width=40, height=32, seed=0):
    """Two empty sixth-barrel kegs, one tipped on its side, a delivery tag."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 2, width // 2, 3)
    kx = ox + 2
    cv.rect(kx, base - 28, 16, 27, OUT); cv.rect(kx + 1, base - 27, 14, 25, CHROME[3]); cv.vline(kx + 2, base - 27, 25, CHROME[4]); cv.vline(kx + 13, base - 27, 25, CHROME[1])
    for yy in (base - 24, base - 8):
        cv.hline(kx + 1, yy, 14, CHROME[1]); cv.hline(kx + 1, yy + 1, 14, CHROME[4])
    cv.ellipse(kx + 1, base - 31, 14, 6, OUT); cv.ellipse(kx + 2, base - 30, 12, 4, CHROME[2]); cv.rect(kx + 6, base - 30, 4, 2, IRON[2])
    cv.rect(kx + 3, base - 18, 9, 6, "#f2ecdc"); cv.hline(kx + 4, base - 16, 6, "#c83a6a")
    # tipped keg
    tx = ox + 18
    cv.rect(tx, base - 14, 22, 13, OUT); cv.rect(tx + 1, base - 13, 20, 11, CHROME[3]); cv.hline(tx + 1, base - 13, 20, CHROME[4]); cv.hline(tx + 1, base - 3, 20, CHROME[1])
    for xx in (tx + 4, tx + 17):
        cv.vline(xx, base - 13, 11, CHROME[1])
    cv.ellipse(tx + 18, base - 15, 6, 15, OUT); cv.ellipse(tx + 19, base - 14, 4, 13, CHROME[2])
    return cv, cx, base


def road_bike_stand(width=60, height=42, seed=0):
    """A carbon road bike up on a display stand (Boulder): matte black frame, pink bar tape, deep
    rims, a KYLE'S tag on the bars."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 2, width // 2, 3)
    r = 12
    lift = 6                                                   # the stand holds the rear wheel up
    wheels = [(ox + r + 1, base - r - 1 - lift), (ox + width - r - 2, base - r - 1)]
    for (wx, wy) in wheels:
        for a in np.linspace(0, 2 * np.pi, 110):
            cv.px(int(round(wx + np.cos(a) * r)), int(round(wy + np.sin(a) * r)), OUT)
            cv.px(int(round(wx + np.cos(a) * (r - 1))), int(round(wy + np.sin(a) * (r - 1))), "#2a2a34")
            cv.px(int(round(wx + np.cos(a) * (r - 3))), int(round(wy + np.sin(a) * (r - 3))), "#3a3a46")
        for a in np.linspace(0, np.pi, 6, endpoint=False):
            cv.line(int(wx + np.cos(a) * 8), int(wy + np.sin(a) * 8), int(wx - np.cos(a) * 8), int(wy - np.sin(a) * 8), C(CHROME[3], 0.6))
        cv.rect(wx - 1, wy - 1, 3, 3, CHROME[3])
    (ax, ay), (bx, by) = wheels
    # the stand under the rear axle
    cv.line(ax, ay, ax - 4, base - 1, IRON[3]); cv.line(ax, ay, ax + 6, base - 1, IRON[3]); cv.hline(ax - 6, base - 1, 14, IRON[2])
    crank = (cx - 2, base - r - 3 - lift // 2)
    seat = (cx - 9, base - 2 * r - 10 - lift)
    head = (bx - 6, base - 2 * r - 8)
    for p, q in [((ax, ay), crank), (crank, seat), (seat, (ax, ay)), (seat, head), (crank, head), (head, (bx, by))]:
        cv.line(p[0], p[1], q[0], q[1], "#1e1e26"); cv.line(p[0], p[1] - 1, q[0], q[1] - 1, "#3a3a48")
    cv.line(seat[0] + 2, seat[1] + 1, head[0] - 2, head[1] + 1, "#e84a98")      # pink accent on the top tube
    cv.rect(seat[0] - 4, seat[1] - 3, 10, 3, OUT); cv.hline(seat[0] - 3, seat[1] - 2, 8, "#3a3a48")
    cv.line(head[0], head[1], head[0] + 1, head[1] - 5, OUT)
    cv.line(head[0] + 1, head[1] - 5, head[0] + 7, head[1] - 5, "#e84a98"); cv.line(head[0] + 7, head[1] - 5, head[0] + 8, head[1] - 1, "#e84a98")
    cv.ellipse(crank[0] - 4, crank[1] - 4, 9, 9, CHROME[3]); cv.ellipse(crank[0] - 2, crank[1] - 2, 5, 5, OUT)
    cv.rect(head[0] + 4, head[1] - 2, 6, 5, "#f2ecdc"); cv.hline(head[0] + 5, head[1], 4, "#c83a3a")
    return cv, cx, base


def swag_boxes(width=40, height=40, seed=0):
    """Shipping boxes of logo hoodies, one open with a grey hoodie spilling out."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 2, width // 2, 3)
    card = ["#4a3220", "#6e4c30", "#8e6640", "#a87c50", "#c09460"]
    for (bx, by, bw, bh) in [(ox, base - 20, 24, 20), (ox + 18, base - 18, 22, 18), (ox + 4, base - 38, 22, 18)]:
        cv.rect(bx, by, bw, bh, OUT); cv.rect(bx + 1, by + 1, bw - 2, bh - 2, card[3]); cv.hline(bx + 1, by + 1, bw - 2, card[4])
        cv.vline(bx + bw // 2, by + 1, 4, "#c8b88a"); cv.rect(bx + 1, by + 4, bw - 2, 1, card[2])
    cv.rect(ox + 21, base - 14, 16, 7, "#f2ecdc"); micro_text(cv, "SWAG", ox + 22, base - 13, "#c83a3a")
    # the open box on top: flaps up, a hoodie spilling over
    cv.poly([(ox + 4, base - 38), (ox + 1, base - 44), (ox + 10, base - 41)], card[2])
    cv.poly([(ox + 26, base - 38), (ox + 30, base - 44), (ox + 20, base - 41)], card[2])
    cv.ellipse(ox + 7, base - 42, 16, 8, OUT); cv.ellipse(ox + 8, base - 41, 14, 6, FLEECE[2])
    cv.rect(ox + 14, base - 39, 8, 12, FLEECE[2]); cv.vline(ox + 14, base - 39, 12, FLEECE[3])
    cv.rect(ox + 16, base - 36, 4, 3, "#e84a98")
    return cv, cx, base


def hot_desk_bench(width=150, height=42, seed=0):
    """A long communal table on hairpin legs: laptops, a jar of pens, a 'saved' seat (a laptop
    and a jacket), a HOT DESKS tent card; two benches either side are folded into it."""
    rng = _rng(seed)
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base - 3, width // 2 + 2, 4)
    top_front = base - 22
    depth = 14
    for lx in (ox + 6, ox + width - 10, ox + width // 2 - 2):
        cv.line(lx, top_front + 3, lx - 1, base - 2, IRON[3]); cv.line(lx + 3, top_front + 3, lx + 4, base - 2, IRON[2])
    # bench in front
    cv.rect(ox + 8, base - 9, width - 16, 4, OUT); cv.rect(ox + 9, base - 8, width - 18, 2, WOOD[4]); cv.hline(ox + 9, base - 8, width - 18, WOOD[5])
    for lx in (ox + 14, ox + width - 16):
        cv.rect(lx, base - 5, 2, 5, IRON[2])
    cv.rect(ox, top_front - depth - 1, width, depth + 5, OUT)
    for yy in range(top_front - depth, top_front + 1):
        cv.hline(ox + 1, yy, width - 2, WOOD[4] if (yy - top_front) % 5 else WOOD[3])
    for k in range(ox + 20, ox + width - 2, 32):
        cv.vline(k + int(rng.integers(0, 6)), top_front - depth, depth + 1, WOOD[3])
    cv.hline(ox + 1, top_front - depth, width - 2, WOOD[5]); cv.rect(ox + 1, top_front + 1, width - 2, 3, WOOD[2])
    cv.hline(ox + 1, top_front + 3, width - 2, WOOD[1])
    t = top_front - depth + 3
    for k, lx in enumerate((ox + 10, ox + 62, ox + 104)):
        cv.rect(lx, t - 6, 16, 9, OUT); cv.rect(lx + 1, t - 5, 14, 7, CHROME[3] if k != 1 else "#2a2a34")
        if k != 1:
            for j, c in enumerate(STICKY[:3] if k == 0 else ["#e84a98", "#2a9a6a"]):
                cv.rect(lx + 3 + j * 4, t - 3, 3, 3, c)
        else:
            cv.rect(lx + 2, t - 4, 12, 5, SCREEN[3]); cv.hline(lx + 3, t - 2, 8, SCREEN[5])
        cv.rect(lx - 1, t + 3, 18, 2, CHROME[2])
    cv.rect(ox + 84, t - 4, 14, 10, OUT); cv.rect(ox + 85, t - 3, 12, 8, "#3a5a3a")                  # saved seat: a jacket
    cv.rect(ox + 40, t - 6, 5, 8, "#e6e2d6"); cv.vline(ox + 41, t - 10, 4, MARKER[0]); cv.vline(ox + 43, t - 9, 3, MARKER[1])  # pen jar
    cv.poly([(ox + width - 26, t + 4), (ox + width - 20, t - 6), (ox + width - 14, t + 4)], "#f2ecdc")  # tent card
    cv.hline(ox + width - 23, t - 1, 6, "#c83a3a")
    return cv, cx, base


def flatirons_view(w, h, seed=0):
    """Out the back window: rooftops and a fire escape across the alley, the Flatirons black against
    the last of the dusk, a few lights on the mesa. Returns a Canvas."""
    rng = _rng(seed)
    cv = Canvas(w, h, seed=seed)
    cv.dither_v(0, 0, w, h * 2 // 3, "#1a1838", "#6a4a6a", steps=5)
    for _ in range(w // 6):
        cv.px(int(rng.integers(0, w)), int(rng.integers(0, h // 4)), "#c8c8e8")
    base = h * 2 // 3
    pts = [(0, base)]
    for x in range(0, w + 4, 4):
        slab = 22 * max(0, 1 - abs(((x * 1.0) % 26) - 13) / 13) + 6 * np.sin(x * 0.2)
        pts.append((x, base - 6 - int(slab)))
    pts.append((w, base))
    cv.poly(pts, "#221a30")
    for x in range(2, w, 26):                                  # lit slab faces
        cv.line(x + 8, base - 26, x + 13, base - 8, "#3a2c46")
    cv.rect(0, base, w, h - base, "#1a1624")
    for x in range(0, w, 11):                                   # rooftops across the alley
        rh = int(rng.integers(4, 12))
        cv.rect(x, base - rh + 8, 11, h, "#120f1a")
        if rng.random() < 0.5:
            cv.px(x + 4, base - rh + 11, WARM[3])
    for yy in range(base + 6, h, 7):                            # the fire escape across the alley
        cv.hline(0, yy, w, "#2a2434"); cv.hline(0, yy + 1, w, "#0e0c14")
        for xx in range(1, w, 3):
            cv.px(xx, yy - 3, "#2a2434")
    return cv


def office_glimpse(cv, cx, base, w=46, h=74):
    """The doorway back into the open office: casing, the brick far wall with the neon's pink
    glow, a desk monitor's light, the pine floor."""
    x0, top = cx - w // 2, base - h
    cv.rect(x0 - 5, top - 5, w + 10, h + 5, TIMBER[0])
    cv.rect(x0 - 4, top - 4, w + 8, h + 4, "#e2d8c6"); cv.vline(x0 - 4, top - 4, h + 4, "#f2ead8"); cv.vline(x0 + w + 3, top - 4, h + 4, "#a89c88")
    sub = Canvas(w, h, seed=3)
    brick_wall_p(sub, 0, 0, w, h - 16, seed=9)
    sub.rect(0, 0, w, h - 16, C("#0d0b16", 0.35))
    halo(sub, w // 2 + 6, 14, 26, NEON_PINK[2], 0.12)
    for k, ch in enumerate("UPTR"):
        text(sub, ch, 4 + k * 6, 8, NEON_PINK[3])
    sub.rect(6, h - 36, 30, 3, BUTCHER[3]); sub.vline(9, h - 33, 17, IRON[2]); sub.vline(32, h - 33, 17, IRON[2])
    sub.rect(14, h - 48, 14, 10, OUT); sub.rect(15, h - 47, 12, 8, SCREEN[3]); sub.hline(16, h - 45, 8, SCREEN[5])
    halo(sub, 21, h - 43, 12, SCREEN[5], 0.08)
    sub.rect(0, h - 16, w, 16, PINE[4])
    for yy in range(h - 16, h, 4):
        sub.hline(0, yy, w, PINE[3])
    sub.rect(0, h - 16, w, 2, C(SHADOW, 0.4))
    cv.paste(sub, x0, top)
    cv.rect(x0 - 2, base - 2, w + 4, 2, "#8a7a5a")


def subway_tile(cv, x, y, w, h):
    """White glazed subway tile backsplash, grey grout, a glint per tile."""
    cv.rect(x, y, w, h, "#9a9a9e")
    for r, yy in enumerate(range(y, y + h, 4)):
        off = 0 if r % 2 else 4
        for xx in range(x - off, x + w, 8):
            x0, x1 = max(x, xx), min(x + w, xx + 7)
            if x1 > x0:
                cv.rect(x0, yy, x1 - x0, min(3, y + h - yy), "#e2e2e0")
                cv.px(x0, yy, "#f6f6f2")
