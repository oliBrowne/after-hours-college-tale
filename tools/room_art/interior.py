"""Interior pieces for the club room and other UMC rooms."""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, ground_shadow, shrub

PLASTER = ["#241a2c", "#2f2238", "#3a2a44", "#45334f", "#56405f"]
PANEL = ["#24151a", "#3a2220", "#55322a", "#6e4434", "#8a5a42", "#a8744f"]
FLOOR = ["#2e1d1c", "#4a2e26", "#5f3b2e", "#6f4634", "#7d5039", "#8c5c42"]
VELVET = ["#2a0f16", "#47161f", "#66202a", "#842c34", "#a33c3e"]
RUG = ["#2a1420", "#45202e", "#5e2a36", "#7a3640", "#c0884a", "#e0b26a"]
NIGHT = ["#0f1426", "#18203a", "#24305a", "#3c4f86"]


def plaster(cv, x, y, w, h, seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, PLASTER[2])
    for yy in range(y, y + h):
        t = (yy - y) / max(1, h)
        if t > 0.6:
            for xx in range(x, x + w):
                if rng.random() < (t - 0.6) * 0.5:
                    cv.px(xx, yy, PLASTER[1])
    for _ in range(w * h // 18):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), PLASTER[int(rng.choice([1, 3]))])


def crown(cv, x, y, w):
    cv.rect(x, y, w, 5, PANEL[3]); cv.hline(x, y, w, PANEL[5]); cv.hline(x, y + 4, w, PANEL[1])
    cv.hline(x, y + 2, w, PANEL[4])
    cv.hline(x, y + 5, w, C("#0d0b16", 0.5))


def wainscot(cv, x, y, w, h, seed=0):
    cv.rect(x, y, w, h, PANEL[2])
    cv.rect(x, y, w, 3, PANEL[4]); cv.hline(x, y, w, PANEL[5]); cv.hline(x, y + 3, w, PANEL[0])
    for px in range(x + 3, x + w - 10, 22):
        pw = min(18, x + w - px - 3)
        cv.rect(px, y + 6, pw, h - 10, PANEL[1])
        cv.rect(px + 1, y + 7, pw - 2, h - 12, PANEL[3])
        cv.hline(px + 1, y + 7, pw - 2, PANEL[4]); cv.vline(px + 1, y + 7, h - 12, PANEL[4])
    cv.rect(x, y + h - 3, w, 3, PANEL[1]); cv.hline(x, y + h - 3, w, PANEL[3])


def night_window(cv, x, y, w, h, seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x - 4, y - 4, w + 8, h + 8, PANEL[1]); cv.rect(x - 3, y - 3, w + 6, h + 6, PANEL[4]); cv.hline(x - 3, y - 3, w + 6, PANEL[5])
    cv.dither_v(x, y, w, h, NIGHT[0], NIGHT[2], steps=4)
    for _ in range(w * h // 40):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h * 2 // 3)), "#c8d0f0" if rng.random() < 0.5 else "#8a96c8")
    # campus roofline and lit windows
    sky_y = y + h - 12
    for bx in range(x, x + w, 9):
        bh = int(rng.integers(5, 12))
        cv.rect(bx, y + h - bh, 9, bh, "#121628")
        for _ in range(2):
            if rng.random() < 0.6:
                cv.px(bx + int(rng.integers(1, 8)), y + h - bh + int(rng.integers(2, max(3, bh))), "#e9a84a")
    cv.vline(x + w // 2, y, h, PANEL[3]); cv.hline(x, y + h // 2, w, PANEL[3])
    cv.rect(x - 5, y + h + 3, w + 10, 3, PANEL[4]); cv.hline(x - 5, y + h + 3, w + 10, PANEL[5])


def curtain(cv, x, y, w, h, flip=False, seed=0):
    """Velvet stage curtain gathered toward the outer edge."""
    rng = np.random.default_rng(seed)
    for i in range(w):
        fold = (i * 3) % 7
        c = VELVET[2] if fold < 2 else VELVET[3] if fold < 4 else VELVET[1] if fold < 6 else VELVET[4]
        xx = x + (w - 1 - i if flip else i)
        cv.vline(xx, y, h, c)
        if fold == 3:
            cv.vline(xx, y + 4, h - 8, VELVET[4])
    # tie-back
    ty = y + h * 2 // 3
    cv.rect(x + (2 if flip else w - 8), ty, 6, 3, "#c0884a"); cv.hline(x + (2 if flip else w - 8), ty, 6, "#e0b26a")
    cv.hline(x, y + h - 1, w, VELVET[0])


def valance(cv, x, y, w):
    cv.rect(x, y, w, 10, VELVET[3]); cv.hline(x, y, w, VELVET[4])
    for sx in range(x, x + w, 12):
        cv.poly([(sx, y + 9), (sx + 6, y + 14), (sx + 12, y + 9)], VELVET[2])
        cv.px(sx + 6, y + 13, "#c0884a")
    cv.hline(x, y + 9, w, "#c0884a")


def string_lights(cv, x0, y0, x1, y1, sag=10, every=7, seed=0):
    rng = np.random.default_rng(seed)
    n = max(2, int(abs(x1 - x0)))
    prev = None
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        p = (int(round(x)), int(round(y)))
        cv.px(p[0], p[1], "#1a1418")
        if i % every == 0 and 0 < i < n:
            c = AMBER[3] if rng.random() < 0.75 else "#f2a0a0"
            cv.rect(p[0] - 2, p[1], 5, 4, C(c, 0.18))
            cv.px(p[0], p[1] + 1, c); cv.px(p[0], p[1] + 2, shade(c, 0.3))


def poster(cv, x, y, w, h, base, title=None, seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x + 1, y + 1, w, h, C("#0d0b16", 0.5))
    cv.rect(x, y, w, h, base)
    cv.hline(x, y, w, shade(base, 0.2))
    if title:
        text(cv, title, x + 2, y + 2, "#1a1424" if sum(C(base)[:3]) > 1.8 else "#f6e3b4")
    for i in range(int(rng.integers(2, 4))):
        ly = y + h - 4 - i * 3
        cv.hline(x + 2, ly, int(rng.integers(w // 3, w - 3)), shade(base, -0.35))
    shape = rng.random()
    cx, cy = x + w // 2, y + h // 2
    if shape < 0.5:
        cv.ellipse(cx - 4, cy - 4, 8, 8, shade(base, -0.4)); cv.ellipse(cx - 2, cy - 3, 4, 3, shade(base, 0.35))
    else:
        cv.poly([(cx - 5, cy + 4), (cx, cy - 5), (cx + 5, cy + 4)], shade(base, -0.4))
    cv.px(x + w // 2, y + 1, "#c8c8d0")


def corkboard(cv, x, y, w, h, seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, PANEL[1]); cv.rect(x - 1, y - 1, w + 2, h + 2, PANEL[4])
    cv.rect(x, y, w, h, "#9a6e48")
    for _ in range(w * h // 5):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), "#7e5838" if rng.random() < 0.5 else "#b0845a")
    cols = ["#e6d6b1", "#f2d27a", "#9fc2b0", "#e8a0a0", "#c8d0f0"]
    for i in range(7):
        pw, ph = int(rng.integers(9, 15)), int(rng.integers(10, 15))
        px, py = x + 2 + int(rng.integers(0, w - pw - 3)), y + 2 + int(rng.integers(0, h - ph - 3))
        c = cols[i % len(cols)]
        cv.rect(px + 1, py + 1, pw, ph, C("#0d0b16", 0.4)); cv.rect(px, py, pw, ph, c)
        for ly in range(py + 3, py + ph - 2, 2):
            cv.hline(px + 2, ly, int(rng.integers(3, pw - 3)), shade(c, -0.35))
        cv.px(px + pw // 2, py + 1, "#c84a3c")


def wall_clock(cv, cx, cy, r=6):
    cv.ellipse(cx - r - 1, cy - r - 1, r * 2 + 3, r * 2 + 3, OUT)
    cv.ellipse(cx - r, cy - r, r * 2 + 1, r * 2 + 1, "#e6d6b1")
    cv.vline(cx, cy - r + 2, r - 1, OUT); cv.hline(cx, cy, r - 2, OUT)
    for a in range(12):
        ang = a / 12 * 2 * np.pi
        cv.px(int(round(cx + np.cos(ang) * (r - 1))), int(round(cy + np.sin(ang) * (r - 1))), "#8a7a6a")


def plank_floor(cv, x, y, w, h, seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, FLOOR[2])
    yy = y
    row = 0
    while yy < y + h:
        rh = 7 + (1 if (yy - y) > h / 2 else 0)
        xx = x - int(rng.integers(0, 50))
        while xx < x + w:
            pl = int(rng.integers(40, 90))
            x0, x1 = max(x, xx), min(x + w, xx + pl)
            tone = FLOOR[int(rng.choice([2, 3, 3, 4]))]
            cv.rect(x0, yy, x1 - x0, rh - 1, tone)
            cv.hline(x0, yy, x1 - x0, shade(tone, 0.08))
            for _ in range((x1 - x0) // 6):
                gx = x0 + int(rng.integers(0, max(1, x1 - x0 - 6)))
                cv.hline(gx, yy + 1 + int(rng.integers(0, rh - 2)), int(rng.integers(3, 8)), shade(tone, -0.1))
            if rng.random() < 0.2:
                kx = x0 + int(rng.integers(2, max(3, x1 - x0 - 2)))
                cv.px(kx, yy + rh // 2, FLOOR[1]); cv.px(kx + 1, yy + rh // 2, shade(tone, -0.18))
            cv.vline(x1 - 1, yy, rh - 1, FLOOR[1])
            xx += pl
        cv.hline(x, yy + rh - 1, w, FLOOR[0])
        yy += rh
        row += 1


def rug(cv, x, y, w, h):
    cv.rect(x - 1, y - 1, w + 2, h + 2, C("#0d0b16", 0.5))
    cv.rect(x, y, w, h, RUG[2])
    cv.rect(x + 2, y + 2, w - 4, h - 4, RUG[4]); cv.rect(x + 3, y + 3, w - 6, h - 6, RUG[1])
    cv.rect(x + 6, y + 5, w - 12, h - 10, RUG[2])
    for yy in range(y + 7, y + h - 7, 8):
        for xx in range(x + 9 + ((yy - y) // 8 % 2) * 8, x + w - 9, 16):
            cv.poly([(xx, yy - 3), (xx + 5, yy), (xx, yy + 3), (xx - 5, yy)], RUG[3])
            cv.px(xx, yy, RUG[5])
    for fx in range(x, x + w, 2):
        cv.px(fx, y - 2, RUG[5]); cv.px(fx, y + h + 1, RUG[5])


def folding_chairs(width=62, height=38, count=3, seed=0):
    """A row of folding chairs seen from behind (facing the stage)."""
    cv = Canvas(width + 4, height + 6, seed=seed)
    ox, base = 2, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    cw = width // count
    for i in range(count):
        x = ox + i * cw + 1
        w = cw - 3
        metal = ["#1b1f2e", "#30374d", "#4a5470", "#6e7a98"]
        # rear legs
        cv.rect(x + 1, base - 16, 2, 16, OUT); cv.rect(x + w - 3, base - 16, 2, 16, OUT)
        cv.vline(x + 1, base - 15, 14, metal[2]); cv.vline(x + w - 3, base - 15, 14, metal[1])
        # seat edge
        cv.rect(x, base - 17, w, 4, OUT); cv.rect(x + 1, base - 16, w - 2, 2, metal[2]); cv.hline(x + 1, base - 16, w - 2, metal[3])
        # back
        cv.rect(x, base - 31, w, 13, OUT)
        cv.rect(x + 1, base - 30, w - 2, 11, metal[1])
        cv.hline(x + 1, base - 30, w - 2, metal[3]); cv.vline(x + 1, base - 30, 11, metal[2])
        cv.hline(x + 2, base - 24, w - 4, metal[0])
        if (i + seed) % 3 == 0:
            # a tote bag or jacket left on one chair
            cv.rect(x + 3, base - 28, w - 7, 9, "#7e3a30"); cv.hline(x + 3, base - 28, w - 7, "#9a4a39")
    return cv, ox + width // 2, base


def folding_table(width=112, height=48, mixer=False, items=True, seed=0, top_height=20):
    cv = Canvas(width + 4, height + 14, seed=seed)
    ox, base = 2, height + 10
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - top_height
    for lx in [ox + 4, ox + width - 8]:
        cv.rect(lx, top + 3, 3, base - top - 3, OUT); cv.vline(lx + 1, top + 3, base - top - 4, IRON[3])
    # tablecloth
    cv.rect(ox, top - 1, width, 14, OUT)
    cv.rect(ox + 1, top, width - 2, 12, "#2c3352"); cv.hline(ox + 1, top, width - 2, "#3e4a6e")
    for fx in range(ox + 3, ox + width - 3, 6):
        cv.vline(fx, top + 4, 8, "#24294a")
    cv.hline(ox + 1, top + 11, width - 2, "#1b1f2e")
    if mixer:
        mx = ox + width // 2 - 26
        cv.rect(mx, top - 12, 52, 12, OUT)
        cv.rect(mx + 1, top - 11, 50, 10, "#353047"); cv.hline(mx + 1, top - 11, 50, "#56506e")
        for i in range(8):
            cv.vline(mx + 4 + i * 6, top - 9, 6, "#1b1824")
            cv.rect(mx + 3 + i * 6, top - 7 + (i * 3) % 5, 3, 2, "#e6d6b1")
            cv.px(mx + 4 + i * 6, top - 10, "#e8b45c" if i % 3 else "#5c897c")
        cv.line(mx + 51, top - 4, ox + width - 4, top + 14, "#16141f")
        cv.line(mx, top - 4, ox + 6, top + 16, "#16141f")
    elif items:
        cv.rect(ox + 12, top - 4, 14, 4, "#e6d6b1"); cv.hline(ox + 13, top - 3, 10, "#9a7c6e")
        cv.rect(ox + width - 30, top - 6, 10, 6, OUT); cv.rect(ox + width - 29, top - 5, 8, 5, "#c47a2c")
    if items:
        # a paper cup and a roll of tape
        cv.rect(ox + width - 14, top - 7, 5, 7, "#e6d6b1"); cv.hline(ox + width - 14, top - 7, 5, "#ffffff")
        cv.ellipse(ox + 30, top - 4, 6, 4, "#8a8fa3")
    return cv, ox + width // 2, base


def pa_speaker(width=37, height=66):
    cv = Canvas(width + 6, height + 6, seed=13)
    ox, base = 3, height + 2
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    cv.rect(ox, base - height, width, height, OUT)
    cv.rect(ox + 1, base - height + 1, width - 2, height - 2, "#24222f")
    cv.hline(ox + 1, base - height + 1, width - 2, "#4d4b66"); cv.vline(ox + 1, base - height + 1, height - 2, "#34324a")
    cx = ox + width // 2
    for (cy, r) in [(base - 20, 12), (base - height + 18, 7)]:
        cv.ellipse(cx - r, cy - r, r * 2 + 1, r * 2 + 1, "#3a384e")
        cv.ellipse(cx - r + 2, cy - r + 2, r * 2 - 3, r * 2 - 3, "#16141f")
        cv.ellipse(cx - r // 2, cy - r // 2, r + 1, r + 1, "#4d4b66")
        cv.px(cx - 1, cy - 1, "#8a88a8")
    for gy in range(base - height + 30, base - 36, 2):
        cv.hline(ox + 4, gy, width - 8, "#34324a")
    cv.rect(cx - 2, base - height + 3, 4, 2, "#e8b45c")
    return cv, ox + width // 2, base


def stage_front(width=486, height=18, seed=0):
    """Front lip of the stage: a lit edge, dark skirt with footlights."""
    cv = Canvas(width + 2, height + 4, seed=seed)
    ox, base = 1, height + 2
    cv.rect(ox, base - height, width, height, OUT)
    cv.rect(ox + 1, base - height, width - 2, 3, PANEL[4]); cv.hline(ox + 1, base - height, width - 2, PANEL[5])
    cv.rect(ox + 1, base - height + 3, width - 2, height - 4, "#1f1720")
    for sx in range(ox + 4, ox + width - 4, 4):
        cv.vline(sx, base - height + 4, height - 6, "#2a2029")
    for lx in range(ox + 24, ox + width - 20, 46):
        cv.rect(lx - 3, base - height + 5, 7, 4, OUT); cv.rect(lx - 2, base - height + 6, 5, 2, AMBER[3])
        cv.rect(lx - 6, base - height + 9, 13, 3, C(AMBER[3], 0.12))
    cv.hline(ox, base - 1, width, C("#0d0b16", 0.6))
    return cv, ox + width // 2, base


def stage_steps(width=42, height=32):
    cv = Canvas(width + 2, height + 4, seed=17)
    ox, base = 1, height + 2
    n = 4
    rise = height // n
    for i in range(n):
        y = base - (i + 1) * rise
        w = width - i * 4
        x = ox + (width - w) // 2 if False else ox + i * 4
        cv.rect(x, y, width - i * 4, rise, OUT)
        cv.rect(x + 1, y + 1, width - i * 4 - 2, rise - 1, PANEL[3])
        cv.hline(x + 1, y + 1, width - i * 4 - 2, PANEL[5])
    return cv, ox + width // 2, base


def floor_lamp(height=62):
    w = 22
    cv = Canvas(w, height + 4, seed=19)
    cx, base = w // 2, height + 1
    ground_shadow(cv, cx, base, 7, 2)
    cv.rect(cx - 5, base - 2, 10, 2, IRON[1]); cv.hline(cx - 5, base - 2, 10, IRON[3])
    cv.rect(cx - 1, 16, 2, base - 18, IRON[2]); cv.vline(cx - 1, 16, base - 18, IRON[4])
    # shade (lit fabric)
    cv.poly([(cx - 5, 2), (cx + 4, 2), (cx + 8, 16), (cx - 9, 16)], OUT)
    cv.poly([(cx - 4, 3), (cx + 3, 3), (cx + 7, 15), (cx - 8, 15)], "#e9a84a")
    cv.poly([(cx - 3, 4), (cx + 1, 4), (cx + 3, 14), (cx - 6, 14)], "#f6cd78")
    cv.hline(cx - 8, 15, 15, "#c47a2c")
    return cv, cx, base


def service_door(width=46, height=60, landing=49):
    """Door painted into the back wall plus the short landing that leads down to its floor anchor."""
    cv = Canvas(width + 24, height + landing + 6, seed=23)
    ox = 12
    door_bottom = height
    cv.rect(ox - 3, 0, width + 6, height + 1, PANEL[1]); cv.rect(ox - 2, 1, width + 4, height, PANEL[4])
    cv.rect(ox, 3, width, height - 3, "#3a4a5a"); cv.hline(ox, 3, width, "#56687a")
    cv.rect(ox + 4, 8, width - 8, 16, "#2a3442"); cv.rect(ox + 6, 10, width - 12, 12, "#1a2230")
    cv.rect(ox + width - 9, height // 2, 5, 3, "#c0c4cc")
    cv.rect(ox + 6, height - 18, width - 12, 9, "#e6d6b1")
    text(cv, "STAFF", ox + width // 2 - 15, height - 19, "#7e3a30")
    cv.rect(ox + width // 2 - 8, -0, 16, 3, "#5cc28a")
    # landing: three shallow steps of floor coming forward to the interaction point
    for i in range(3):
        y = door_bottom + i * (landing // 3)
        w = width + 8 + i * 6
        x = ox + width // 2 - w // 2
        cv.rect(x, y, w, landing // 3, FLOOR[3]); cv.hline(x, y, w, FLOOR[5]); cv.hline(x, y + landing // 3 - 1, w, FLOOR[0])
    return cv, ox + width // 2, height + landing


TILE = ["#3e3238", "#6a5850", "#8a7466", "#a08876", "#b89c86", "#cdb59c"]


def tile_floor(cv, x, y, w, h, size=20, seed=0):
    """Polished stone tiles laid on the diagonal-free grid, alternating warm and rose, with sheen."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, TILE[0])
    row = 0
    yy = y
    while yy < y + h:
        th = int(size * (0.55 + 0.25 * (yy - y) / max(1, h)))
        for i, xx in enumerate(range(x, x + w, size)):
            tone = TILE[3] if (i + row) % 2 == 0 else "#9a7470"
            x1 = min(x + w, xx + size - 1)
            cv.rect(xx, yy, x1 - xx, th - 1, tone)
            cv.hline(xx, yy, x1 - xx, shade(tone, 0.12))
            for _ in range((x1 - xx) * th // 9):
                cv.px(xx + int(rng.integers(0, max(1, x1 - xx))), yy + int(rng.integers(0, max(1, th - 1))), shade(tone, float(rng.choice([-0.06, 0.05]))))
            if rng.random() < 0.15:
                cv.line(xx + 2, yy + th - 3, xx + 6, yy + 1, shade(tone, 0.18))
        yy += th
        row += 1


def runner(cv, x, y, w, h, base="#5e2a36", border="#c0884a"):
    cv.rect(x - 1, y, w + 2, h, C("#0d0b16", 0.4))
    cv.rect(x, y, w, h, base)
    cv.vline(x + 2, y, h, border); cv.vline(x + w - 3, y, h, border)
    for yy in range(y + 4, y + h - 2, 8):
        cv.px(x + w // 2, yy, border); cv.px(x + w // 2 - 1, yy + 1, border); cv.px(x + w // 2 + 1, yy + 1, border)


def stair_down(cv, x, y, w, h):
    """An opening in the floor with steps dropping away into shadow, rails on both sides."""
    cv.rect(x, y, w, h, "#120f18")
    steps = 7
    for i in range(steps):
        sy = y + i * h // steps
        tone = mix("#8a7466", "#1a1520", i / steps)
        cv.rect(x + 2, sy, w - 4, max(2, h // steps - 1), tone)
        cv.hline(x + 2, sy, w - 4, shade(tone, 0.15))
    for rx in (x - 2, x + w - 1):
        cv.rect(rx, y - 18, 3, h + 18, OUT); cv.vline(rx + 1, y - 18, h + 18, "#a3a9b8")
    cv.rect(x - 3, y - 20, w + 6, 3, OUT); cv.hline(x - 2, y - 19, w + 4, "#c0c4cc")


def directory_sign(width=160, height=36, lines=("CLUB <", "REPAIR >")):
    cv = Canvas(width + 4, height + 6, seed=47)
    ox, base = 2, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 - 10, 2)
    for px in (ox + 8, ox + width - 12):
        cv.rect(px, base - 14, 4, 14, OUT); cv.vline(px + 1, base - 14, 13, WOOD[3])
    cv.rect(ox, base - height, width, height - 12, OUT)
    cv.rect(ox + 1, base - height + 1, width - 2, height - 14, WOOD[4])
    cv.rect(ox + 3, base - height + 3, width - 6, height - 18, "#1f1a2a")
    y = base - height + 4
    total = " / ".join(lines)
    text(cv, total, ox + width // 2 - text_width(total) // 2, y, "#f6cd78")
    cv.hline(ox + 1, base - height + 1, width - 2, WOOD[5])
    return cv, ox + width // 2, base


def reception_desk(width=102, height=46, label="LAST LIGHT"):
    cv = Canvas(width + 4, height + 8, seed=53)
    ox, base = 2, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - 30
    cv.rect(ox, top, width, 30, OUT)
    cv.wood(ox + 1, top + 4, width - 2, 25, PANEL[3], vertical=True, plank=6, seed=4)
    cv.rect(ox - 1, top - 2, width + 2, 6, OUT); cv.rect(ox, top - 1, width, 4, PANEL[5]); cv.hline(ox, top - 1, width, "#c99364")
    sw = text_width(label) + 8
    cv.rect(ox + width // 2 - sw // 2, top + 9, sw, 12, "#1f1a2a"); text(cv, label, ox + width // 2 - text_width(label) // 2, top + 10, "#f6cd78")
    # desk lamp, papers and a bell on top
    cv.rect(ox + 10, top - 10, 2, 9, OUT); cv.poly([(ox + 6, top - 10), (ox + 16, top - 10), (ox + 13, top - 15), (ox + 9, top - 15)], "#5c897c")
    cv.rect(ox + 7, top - 9, 8, 2, C("#f6cd78", 0.6))
    cv.rect(ox + 40, top - 4, 14, 3, "#e6d6b1"); cv.rect(ox + 56, top - 3, 10, 2, "#c8d0f0")
    cv.ellipse(ox + width - 18, top - 6, 7, 5, "#e8b45c"); cv.px(ox + width - 15, top - 7, "#fff0c4")
    return cv, ox + width // 2, base


def potted_plant(width=50, height=38, seed=0):
    cv = Canvas(width + 4, height + 8, seed=seed)
    ox, base = 2, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 - 4, 2)
    pot_w, pot_h = width - 16, 14
    leaves = shrub(0, 0, width - 6, height - 10, seed=seed + 3)
    cv.paste(leaves, ox + 1, base - height - 2)
    px = ox + (width - pot_w) // 2
    cv.poly([(px - 1, base - pot_h - 1), (px + pot_w, base - pot_h - 1), (px + pot_w - 3, base), (px + 2, base)], OUT)
    cv.poly([(px, base - pot_h), (px + pot_w - 1, base - pot_h), (px + pot_w - 4, base - 1), (px + 3, base - 1)], "#a8604a")
    cv.rect(px - 1, base - pot_h - 2, pot_w + 2, 3, "#c47a5a"); cv.hline(px - 1, base - pot_h - 2, pot_w + 2, "#d99a7a")
    cv.vline(px + 3, base - pot_h + 2, pot_h - 4, "#c47a5a")
    return cv, ox + width // 2, base
