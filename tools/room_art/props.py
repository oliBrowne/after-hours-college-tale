"""Hand-built mid-resolution prop sprites. Each painter returns (Canvas, anchor_x, anchor_y):
the anchor is the pixel that sits on the prop's floor position (its node origin)."""
import numpy as np
from pixel import Canvas, C, mix, shade

OUT = "#1a1524"
IRON = ["#16141f", "#24222f", "#34324a", "#4d4b66", "#6c6a88"]
WOOD = ["#2c1a1a", "#4a2b24", "#6b3f2e", "#8c573b", "#ad754d", "#c99364"]
SAND = ["#3d2e33", "#5e4743", "#7d625a", "#9a7c6e", "#b59584", "#cfb09a"]
LEAF = ["#16201f", "#22302b", "#2f4237", "#3f5741", "#566d4a", "#73864f"]
MUM = ["#e0a43c", "#c8682e", "#a83c32", "#f2d27a"]
AMBER = ["#7a4a24", "#c47a2c", "#eaa845", "#f6cf7a", "#fff0c4"]


def ground_shadow(cv, cx, cy, rx, ry=3, alpha=0.38):
    for yy in range(-ry, ry + 1):
        span = int(rx * np.sqrt(max(0.0, 1 - (yy / (ry + 0.5)) ** 2)))
        cv.rect(cx - span, cy + yy, span * 2 + 1, 1, C("#0d0b16", alpha))


def foliage(cv, x, y, w, h, seed=0, flowers=0.0, palette=LEAF):
    """A clump of leaves: overlapping lumps, lit from the upper left, dark underside."""
    rng = np.random.default_rng(seed)
    lumps = []
    count = max(3, int(w * h / 60))
    for _ in range(count):
        lw = rng.integers(max(5, w // 5), max(7, w // 2))
        lh = rng.integers(max(4, h // 3), max(6, int(h * 0.8)))
        lx = x + rng.integers(0, max(1, w - lw))
        ly = y + rng.integers(0, max(1, h - lh))
        lumps.append((lx, ly, lw, lh))
    lumps.sort(key=lambda b: b[1] + b[3])
    for (lx, ly, lw, lh) in lumps:
        cv.ellipse(lx - 1, ly - 1, lw + 2, lh + 2, OUT)
    for (lx, ly, lw, lh) in lumps:
        cv.ellipse(lx, ly, lw, lh, palette[2])
        cv.ellipse(lx, ly + lh // 2, lw, lh - lh // 2, palette[1])
        cv.ellipse(lx + 1, ly + 1, max(2, lw - 3), max(2, lh // 2), palette[3])
        for _ in range(int(lw * lh / 5)):
            px = lx + rng.integers(0, lw)
            py = ly + rng.integers(0, lh)
            if (px - lx - lw / 2) ** 2 / (lw / 2) ** 2 + (py - ly - lh / 2) ** 2 / (lh / 2) ** 2 > 0.8:
                continue
            upper = py < ly + lh * 0.45
            c = palette[4] if upper and rng.random() < 0.6 else palette[3] if upper else palette[1]
            cv.rect(px, py, 2 if rng.random() < 0.5 else 1, 1, c)
        for _ in range(int(lw * lh * flowers / 6)):
            px = lx + 1 + rng.integers(0, max(1, lw - 2))
            py = ly + rng.integers(0, max(1, lh // 2 + 1))
            c = MUM[rng.integers(len(MUM))]
            cv.px(px, py, c)
            if rng.random() < 0.5:
                cv.px(px + 1, py, shade(c, -0.2))


def shrub(cx, by, w, h, seed=0, palette=LEAF, flowers=None, density=1.0):
    """A rounded bush built from small leaf clusters; returns a Canvas positioned at (cx - w//2 - 2, by - h - 2)."""
    rng = np.random.default_rng(seed)
    cv = Canvas(w + 4, h + 4, seed=seed)
    ox, oy = 2, 2
    rx, ry = w / 2, h / 2
    clumps = []
    for _ in range(int(w * h / 5 * density)):
        a = rng.uniform(0, 2 * np.pi)
        r = np.sqrt(rng.uniform(0, 1))
        x = rx + np.cos(a) * r * (rx - 2)
        y = ry + np.sin(a) * r * (ry - 2) * 0.95
        if y > h - 2:
            continue
        clumps.append((x, y, rng.integers(2, 4)))
    clumps.sort(key=lambda c: c[1])
    for (x, y, r) in clumps:
        t = y / h
        light = (1 - t) * 0.7 + (1 - x / w) * 0.3
        base = palette[1] if light < 0.3 else palette[2] if light < 0.5 else palette[3] if light < 0.72 else palette[4]
        cv.ellipse(int(ox + x - r), int(oy + y - r), r * 2, r * 2, base)
        cv.px(int(ox + x - r + 1), int(oy + y - r + 1), shade(base, 0.12) if light > 0.4 else base)
        if light > 0.78 and rng.random() < 0.5:
            cv.px(int(ox + x - 1), int(oy + y - r), palette[5])
        cv.px(int(ox + x + r - 1), int(oy + y + r - 1), palette[0])
    if flowers:
        for _ in range(int(w * h / 18)):
            a = rng.uniform(0, 2 * np.pi)
            r = np.sqrt(rng.uniform(0, 1))
            x = int(ox + rx + np.cos(a) * r * (rx - 3))
            y = int(oy + ry * 0.8 + np.sin(a) * r * (ry - 3) * 0.8)
            c = flowers[rng.integers(len(flowers))]
            if cv.a[y, x, 3] > 0:
                cv.px(x, y, c); cv.px(x + 1, y, shade(c, -0.15)); cv.px(x, y - 1, shade(c, 0.2))
    cv.outline_outside(OUT)
    return cv


def grass_tuft(cv, x, by, h, seed=0, palette=LEAF):
    rng = np.random.default_rng(seed)
    for i in range(6):
        lean = rng.integers(-2, 3)
        hh = rng.integers(h // 2, h + 1)
        cv.line(x + i, by, x + i + lean, by - hh, palette[3 if i % 2 else 4])


def stone_courses(cv, x, y, w, h, pal=SAND, course=6, seed=0):
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, pal[1])
    row = 0
    for yy in range(y, y + h, course):
        ch = min(course, y + h - yy)
        xx = x - (rng.integers(0, 8) if row % 2 else 0)
        while xx < x + w:
            sw = int(rng.integers(9, 17))
            x0, x1 = max(x, xx), min(x + w, xx + sw - 1)
            tone = pal[3] if rng.random() < 0.6 else pal[2] if rng.random() < 0.5 else pal[4]
            cv.rect(x0, yy, x1 - x0, ch - 1, tone)
            cv.hline(x0, yy, x1 - x0, shade(tone, 0.14))
            cv.hline(x0, yy + ch - 2, x1 - x0, shade(tone, -0.12))
            for _ in range((x1 - x0) * ch // 12):
                cv.px(x0 + rng.integers(0, max(1, x1 - x0)), yy + rng.integers(0, max(1, ch - 1)), shade(tone, rng.choice([-0.1, 0.08])))
            xx += sw
        row += 1


def lamp_post(height=62, indoor=False):
    w = 22
    cv = Canvas(w, height + 6, seed=3)
    cx, base = w // 2, height
    ground_shadow(cv, cx, base, 9, 2)
    # plinth
    cv.rect(cx - 5, base - 4, 10, 4, IRON[1]); cv.hline(cx - 5, base - 4, 10, IRON[3])
    cv.rect(cx - 4, base - 7, 8, 3, IRON[2]); cv.hline(cx - 4, base - 7, 8, IRON[4])
    cv.rect(cx - 3, base - 11, 6, 4, IRON[1]); cv.vline(cx - 3, base - 11, 4, IRON[3])
    # post with rings
    top = 18
    cv.rect(cx - 2, top, 4, base - 11 - top, IRON[2])
    cv.vline(cx - 2, top, base - 11 - top, IRON[3]); cv.vline(cx + 1, top, base - 11 - top, IRON[0])
    for ry in [top + 6, (top + base) // 2]:
        cv.rect(cx - 3, ry, 6, 2, IRON[1]); cv.hline(cx - 3, ry, 6, IRON[4])
    # lantern
    cv.rect(cx - 4, top - 2, 8, 2, IRON[1])
    cv.rect(cx - 4, 6, 8, 10, AMBER[2])
    cv.rect(cx - 3, 7, 6, 8, AMBER[3]); cv.rect(cx - 1, 8, 2, 5, AMBER[4])
    cv.vline(cx - 4, 6, 10, IRON[1]); cv.vline(cx + 3, 6, 10, IRON[0]); cv.vline(cx, 6, 10, C(IRON[1], 0.7))
    cv.rect(cx - 5, 15, 10, 2, IRON[1]); cv.hline(cx - 5, 15, 10, IRON[3])
    cv.poly([(cx - 6, 6), (cx, 1), (cx + 5, 6)], IRON[1]); cv.hline(cx - 5, 5, 10, IRON[3])
    cv.rect(cx - 1, 0, 2, 2, IRON[2])
    return cv, cx, base


def park_bench(width=96, height=34):
    cv = Canvas(width + 4, height + 4, seed=5)
    ox, base = 2, height
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 2)
    wood = WOOD
    # back rest slats
    for i, yy in enumerate([3, 8, 13]):
        cv.rect(ox + 3, yy, width - 6, 4, OUT)
        cv.rect(ox + 4, yy + 1, width - 8, 2, wood[4 if i == 0 else 3])
        cv.hline(ox + 4, yy + 1, width - 8, wood[5])
        for gx in range(ox + 9, ox + width - 6, 11):
            cv.hline(gx, yy + 2, 3, wood[2])
    # iron end frames
    for ex in [ox + 1, ox + width - 6]:
        cv.rect(ex, 2, 5, base - 2, OUT)
        cv.rect(ex + 1, 3, 3, base - 4, IRON[2]); cv.vline(ex + 1, 3, base - 4, IRON[4])
        cv.rect(ex - 1, 15, 7, 3, IRON[1]); cv.hline(ex - 1, 15, 7, IRON[3])
    cv.rect(ox + width // 2 - 2, 18, 4, base - 18, OUT); cv.rect(ox + width // 2 - 1, 19, 2, base - 20, IRON[2])
    # seat
    cv.rect(ox + 2, 19, width - 4, 6, OUT)
    cv.rect(ox + 3, 20, width - 6, 2, wood[4]); cv.hline(ox + 3, 20, width - 6, wood[5])
    cv.rect(ox + 3, 22, width - 6, 2, wood[2])
    # legs splay
    for lx in [ox + 3, ox + width - 7]:
        cv.rect(lx, 25, 4, base - 25, OUT); cv.rect(lx + 1, 25, 2, base - 26, IRON[2])
        cv.rect(lx - 1, base - 2, 6, 2, IRON[1])
    return cv, ox + width // 2, base


def planter_box(width=144, height=43, seed=7):
    cv = Canvas(width + 4, height + 10, seed=seed)
    ox, base = 2, height + 6
    rng = np.random.default_rng(seed)
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    face_top = base - 20
    # plants first so the stone lip overlaps their stems
    x = ox + 2
    while x < ox + width - 12:
        kind = rng.random()
        if kind < 0.5:
            w = int(rng.integers(20, 30)); h = int(rng.integers(16, 24))
            bush = shrub(0, 0, w, h, seed=int(rng.integers(1e6)))
            cv.paste(bush, x - 2, face_top - h + 2)
            x += w - 6
        elif kind < 0.8:
            w = int(rng.integers(12, 17)); h = int(rng.integers(9, 13))
            bloom = shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=[MUM[int(rng.integers(len(MUM)))]] * 2 + [MUM[3]], density=1.3)
            cv.paste(bloom, x - 2, face_top - h + 1)
            x += w - 2
        else:
            grass_tuft(cv, x + 2, face_top + 1, int(rng.integers(10, 16)), seed=int(rng.integers(1e6)))
            x += 7
    cv.rect(ox, face_top - 1, width, 21, OUT)
    stone_courses(cv, ox + 1, face_top + 3, width - 2, 16, SAND, 6, seed)
    cv.rect(ox - 1, face_top - 2, width + 2, 5, OUT)
    cv.rect(ox, face_top - 1, width, 3, SAND[4]); cv.hline(ox, face_top - 1, width, SAND[5])
    cv.hline(ox + 1, face_top + 2, width - 2, SAND[1])
    return cv, ox + width // 2, base


def custodian_cart(width=54, height=42):
    cv = Canvas(width + 14, height + 10, seed=9)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    blue = ["#1b2140", "#283866", "#3a4f8a", "#5671b0"]
    # frame and shelves
    cv.rect(ox, base - 34, width - 14, 30, OUT)
    cv.rect(ox + 1, base - 33, width - 16, 28, blue[1])
    cv.rect(ox + 1, base - 33, width - 16, 2, blue[3])
    cv.rect(ox + 1, base - 20, width - 16, 2, blue[2]); cv.hline(ox + 1, base - 18, width - 16, blue[0])
    # supplies on shelves
    for i, (sx, c) in enumerate([(3, "#e6d6b1"), (11, "#c47a2c"), (19, "#5c897c"), (27, "#e6d6b1")]):
        cv.rect(ox + sx, base - 30, 6, 9, OUT); cv.rect(ox + sx + 1, base - 29, 4, 8, c); cv.vline(ox + sx + 1, base - 29, 8, shade(c, 0.2))
    for sx in [4, 16, 28]:
        cv.rect(ox + sx, base - 15, 9, 8, OUT); cv.rect(ox + sx + 1, base - 14, 7, 7, "#9a7c6e"); cv.hline(ox + sx + 1, base - 14, 7, "#cfb09a")
    # handle
    cv.rect(ox - 3, base - 38, 3, 2, OUT); cv.rect(ox - 2, base - 38, 2, 22, OUT); cv.vline(ox - 2, base - 37, 20, IRON[3])
    # mop bucket + mop on the right
    bx = ox + width - 14
    cv.rect(bx, base - 16, 14, 13, OUT); cv.rect(bx + 1, base - 15, 12, 11, "#d9a441"); cv.hline(bx + 1, base - 15, 12, "#f2d27a")
    cv.rect(bx + 1, base - 10, 12, 1, "#a8742c")
    cv.line(bx + 5, base - 15, bx + 10, base - 44, "#b98a63")
    cv.line(bx + 6, base - 15, bx + 11, base - 44, "#8c573b")
    for i in range(5):
        cv.vline(bx + 3 + i, base - 18 + (i % 2), 4, "#e6d6b1")
    # wheels
    for wx in [ox + 3, ox + width - 22, bx + 2, bx + 9]:
        cv.rect(wx, base - 4, 4, 4, OUT); cv.rect(wx + 1, base - 3, 2, 2, IRON[3])
    return cv, ox + width // 2, base


def bike_workbench(width=86, height=43):
    cv = Canvas(width + 4, height + 8, seed=11)
    ox, base = 2, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - 22
    # legs and lower shelf
    for lx in [ox + 3, ox + width - 8]:
        cv.rect(lx, top + 3, 5, base - top - 3, OUT); cv.rect(lx + 1, top + 3, 3, base - top - 4, WOOD[2]); cv.vline(lx + 1, top + 3, base - top - 4, WOOD[3])
    cv.rect(ox + 3, base - 8, width - 6, 4, OUT); cv.rect(ox + 4, base - 7, width - 8, 2, WOOD[3])
    # parts bin on shelf
    cv.rect(ox + 14, base - 14, 16, 7, OUT); cv.rect(ox + 15, base - 13, 14, 5, "#425da6"); cv.hline(ox + 15, base - 13, 14, "#6b81bf")
    # top
    cv.rect(ox, top - 1, width, 6, OUT)
    cv.wood(ox + 1, top, width - 2, 4, WOOD[4], plank=2, seed=2)
    cv.hline(ox + 1, top, width - 2, WOOD[5])
    # vise
    cv.rect(ox + width - 18, top - 7, 12, 7, OUT); cv.rect(ox + width - 17, top - 6, 10, 5, IRON[3]); cv.hline(ox + width - 17, top - 6, 10, IRON[4])
    cv.rect(ox + width - 21, top - 4, 3, 2, IRON[2])
    # tools on top: wrench, screwdriver, chain loop, tyre levers
    cv.line(ox + 8, top - 2, ox + 20, top - 2, IRON[4]); cv.rect(ox + 6, top - 3, 3, 3, IRON[3]); cv.rect(ox + 20, top - 3, 3, 3, IRON[3])
    cv.rect(ox + 26, top - 2, 7, 2, "#c84a3c"); cv.hline(ox + 33, top - 2, 6, IRON[4])
    cv.ellipse(ox + 42, top - 5, 12, 5, IRON[1]); cv.ellipse(ox + 44, top - 4, 8, 3, C("#000000", 0))
    for i in range(0, 12, 2):
        cv.px(ox + 42 + i, top - 5 + (1 if i % 4 else 0), IRON[4])
    cv.rect(ox + 56, top - 2, 2, 2, "#e8b45c"); cv.rect(ox + 59, top - 2, 2, 2, "#5c897c")
    # a wheel leaning against the bench
    cx, cy, r = ox + 12, base - 12, 11
    for a in np.linspace(0, 2 * np.pi, 80):
        cv.px(int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r)), OUT)
        cv.px(int(round(cx + np.cos(a) * (r - 1))), int(round(cy + np.sin(a) * (r - 1))), IRON[2])
        cv.px(int(round(cx + np.cos(a) * (r - 2))), int(round(cy + np.sin(a) * (r - 2))), IRON[4] if a < 3.4 else IRON[3])
    for a in np.linspace(0, np.pi, 6, endpoint=False):
        cv.line(int(cx + np.cos(a) * 8), int(cy + np.sin(a) * 8), int(cx - np.cos(a) * 8), int(cy - np.sin(a) * 8), C(IRON[4], 0.8))
    cv.rect(cx - 1, cy - 1, 3, 3, IRON[4])
    return cv, ox + width // 2, base


def bus_shelter(width=138, height=73):
    from pixel import text, text_width
    cv = Canvas(width + 6, height + 26, seed=29)
    ox, base = 3, height + 22
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - height
    # back glass panel with reflections
    cv.rect(ox + 4, top + 10, width - 8, height - 16, C("#2c3352", 0.55))
    for gx in range(ox + 12, ox + width - 10, 22):
        cv.line(gx, top + height - 10, gx + 10, top + 14, C("#8a96c8", 0.35))
    cv.hline(ox + 4, top + 10, width - 8, C("#c8d0f0", 0.4))
    # posts
    for px in (ox + 2, ox + width - 6, ox + width // 2 - 2):
        cv.rect(px, top + 6, 4, height - 6, OUT); cv.rect(px + 1, top + 6, 2, height - 7, IRON[3])
    # roof and sign
    cv.rect(ox - 2, top + 2, width + 4, 7, OUT)
    cv.rect(ox - 1, top + 3, width + 2, 4, "#3a4f8a"); cv.hline(ox - 1, top + 3, width + 2, "#5671b0")
    sw = 86
    cv.rect(ox + width // 2 - sw // 2, top - 16, sw, 16, OUT)
    cv.rect(ox + width // 2 - sw // 2 + 1, top - 15, sw - 2, 14, "#1b2140")
    text(cv, "CAMPUS BUS", ox + width // 2 - text_width("CAMPUS BUS") // 2, top - 13, "#e6d6b1")
    cv.rect(ox + width // 2 - 1, top - 1, 2, 3, OUT)
    # bench inside the shelter
    cv.rect(ox + 14, base - 16, width - 28, 4, OUT); cv.rect(ox + 15, base - 15, width - 30, 2, WOOD[4])
    for lx in (ox + 18, ox + width - 22):
        cv.rect(lx, base - 12, 3, 12, OUT)
    return cv, ox + width // 2, base


def timetable(width=30, height=40):
    from pixel import text
    cv = Canvas(width + 4, height + 4, seed=31)
    ox, base = 2, height + 2
    cv.rect(ox + width // 2 - 1, base - 12, 3, 12, OUT)
    cv.rect(ox, base - height, width, height - 10, OUT)
    cv.rect(ox + 1, base - height + 1, width - 2, height - 12, "#e6d6b1")
    cv.rect(ox + 1, base - height + 1, width - 2, 6, "#c84a3c")
    for i, ly in enumerate(range(base - height + 10, base - 14, 3)):
        cv.hline(ox + 4, ly, width - 8 - (i % 3) * 4, "#5a4a44")
    cv.rect(ox + width - 9, base - 16, 6, 3, "#e8b45c")
    return cv, ox + width // 2, base


def mural_board(width=72, height=61):
    """Mara's mural on an easel board: a little Flatirons sunset."""
    from midlib import ART, downscale, quantize
    from PIL import Image
    cv = Canvas(width + 6, height + 6, seed=37)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 - 4, 2)
    # easel legs
    cv.line(ox + 10, base, ox + 18, base - height + 6, OUT); cv.line(ox + width - 10, base, ox + width - 18, base - height + 6, OUT)
    cv.line(ox + 11, base, ox + 19, base - height + 6, WOOD[3]); cv.line(ox + width - 11, base, ox + width - 19, base - height + 6, WOOD[3])
    pw, ph = width - 8, height - 20
    px, py = ox + 4, base - height
    cv.rect(px - 2, py - 2, pw + 4, ph + 4, OUT); cv.rect(px - 1, py - 1, pw + 2, ph + 2, WOOD[4])
    img = np.array(Image.open(f"{ART}/boulder-title-v2.png").convert("RGBA")).astype(np.float32) / 255
    crop = img[60:292, 760:1100].copy()
    small = quantize(downscale(crop, (pw, ph)), 20, saturation=1.15)
    small[..., 3] = 1
    cv.paste(small, px, py)
    # paint pots on the tray
    cv.rect(ox + 8, py + ph + 4, width - 16, 3, OUT); cv.hline(ox + 9, py + ph + 4, width - 18, WOOD[4])
    for i, c in enumerate(["#c84a3c", "#e8b45c", "#425da6", "#5c897c"]):
        cv.rect(ox + 12 + i * 12, py + ph, 6, 4, OUT); cv.rect(ox + 13 + i * 12, py + ph + 1, 4, 2, c)
    return cv, ox + width // 2, base


def bicycle(width=60, height=35):
    cv = Canvas(width + 6, height + 6, seed=41)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    r = 11
    wheels = [(ox + r + 1, base - r - 1), (ox + width - r - 2, base - r - 1)]
    for cx, cy in wheels:
        for a in np.linspace(0, 2 * np.pi, 90):
            cv.px(int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r)), OUT)
            cv.px(int(round(cx + np.cos(a) * (r - 1))), int(round(cy + np.sin(a) * (r - 1))), "#2a2838")
        for a in np.linspace(0, np.pi, 5, endpoint=False):
            cv.line(int(cx + np.cos(a) * 8), int(cy + np.sin(a) * 8), int(cx - np.cos(a) * 8), int(cy - np.sin(a) * 8), C("#a3a9b8", 0.7))
        cv.rect(cx - 1, cy - 1, 3, 3, "#a3a9b8")
    (ax, ay), (bx, by) = wheels
    crank = (ox + width // 2 - 2, base - r - 1)
    seat = (ox + width // 2 - 8, base - 2 * r - 6)
    head = (bx - 6, base - 2 * r - 6)
    frame = "#3a4f8a"
    for p, q in [(wheels[0], crank), (crank, seat), (seat, wheels[0]), (seat, head), (crank, head), (head, wheels[1])]:
        cv.line(p[0], p[1], q[0], q[1], frame)
        cv.line(p[0], p[1] - 1, q[0], q[1] - 1, "#5671b0")
    cv.rect(seat[0] - 4, seat[1] - 3, 9, 3, OUT)
    cv.line(head[0], head[1], head[0] + 2, head[1] - 6, OUT); cv.rect(head[0] - 2, head[1] - 7, 8, 2, OUT)
    cv.ellipse(crank[0] - 3, crank[1] - 3, 7, 7, "#a3a9b8"); cv.px(crank[0], crank[1], OUT)
    return cv, ox + width // 2, base


def bollard_lamp(height=32):
    w = 16
    cv = Canvas(w, height + 4, seed=43)
    cx, base = w // 2, height + 1
    ground_shadow(cv, cx, base, 6, 2)
    cv.rect(cx - 3, 12, 6, base - 12, OUT); cv.rect(cx - 2, 12, 4, base - 13, IRON[2]); cv.vline(cx - 2, 12, base - 13, IRON[4])
    cv.rect(cx - 4, 2, 8, 11, OUT); cv.rect(cx - 3, 4, 6, 7, AMBER[3]); cv.rect(cx - 2, 5, 4, 4, AMBER[4])
    cv.poly([(cx - 5, 3), (cx, -1), (cx + 4, 3)], OUT)
    return cv, cx, base


def atlas_tree(height=96, cell=5, seed=0):
    from midlib import sprite_from_cell
    spr = sprite_from_cell(cell, height=height, colors=36)
    h, w = spr.shape[:2]
    cv = Canvas(w, h + 3, seed=seed)
    ground_shadow(cv, w // 2, h, w // 3, 2)
    cv.paste(spr, 0, 0)
    return cv, w // 2, h
