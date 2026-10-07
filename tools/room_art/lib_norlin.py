"""Norlin Library's shared look, for every Norlin room (N01-N07) and its battle backdrops.

Everything paints at 1:1 game pixels against a 52px character. Sections:
  palettes ............ OAK, SPINES, PLASTER_N, STONE_N, LAMP_GREEN, BRASS, MARBLE, CARPET_*, NIGHT_N
  books ............... book_row, wall_shelves, bookcase (prop), book_stack, open_book
  walls ............... plaster_wall, oak_wainscot, ceiling_band, stone_wall, quoins, directional_sign, plaque
  windows ............. arched_window (interior, night view), facade_window (exterior, lit)
  lamps ............... banker_lamp, pendant_lamp, shade_pendant, wall_sconce, standard_lamp (prop), quiet_lamp_post (prop),
                        plinth_lamp
  furniture ........... reading_table, checkout_desk, library_bench, card_catalogue, notice_stand, urn_plant,
                        library_ladder, regulator_clock (+ pendulum_frames), wall_clock_big, wall_speaker
  reading room ........ built_in_shelves, window_seat, garden_door (glazed, garden beyond), reel_deck,
                        headphones, bookmark_card, marked_bookcase (open book in two inks)
  quad ................ stone_planter, quad_bench, quiet_lamp_post, fountain_grass, iron_gate, iron_arch,
                        book_drop, chalk, loose_page
  floors .............. marble_floor, cabochon_floor, floor_inlay, depth_shade, parquet_floor, carpet,
                        runner_n, moon_patch, lawn, paving, crazy_paving, book_medallion, kerb, tree_pit,
                        stone_steps, flag_path
  facade .............. column, norlin_portico (the columned west front at character scale)
  battle textures ..... shelf_wall_texture (a wall of books for perspective planes)
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, SAND, LEAF, MUM, AMBER, ground_shadow, shrub, grass_tuft
from facade import TRIM, ROOF, FRAME, GLOW, DARKGLASS, roof_tiles
from surfaces import light_pool, LEAVES

# --- palettes ---------------------------------------------------------------------------------
OAK = WOOD                                                     # library oak, the campus wood family
OAK_DARK = ["#140c10", "#1e1214", "#2c1a1a", "#3e2620", "#55342a", "#6b4432"]  # shelf backs, shadowed oak
SPINES = ["#7e3a30", "#9e4e52", "#a83c32", "#425da6", "#2c3f6e", "#3f5741", "#5c897c", "#c47a2c",
          "#d9a441", "#e6d6b1", "#6b3f5e", "#8c573b", "#3a2a33", "#7a6a9c", "#b8694c", "#4a6a5a"]
GILT = "#e8c070"
PAGE = ["#8a7a68", "#b8a888", "#e6d6b1", "#f6ecd2"]           # paper edges, shadow to lit
PLASTER_N = ["#3e2e30", "#4e3a38", "#5e4640", "#6c5248", "#7a5e52", "#8a6c5c", "#9a7c68"]  # warm lamplit plaster
STONE_N = ["#4e3634", "#6a4a42", "#8a6654", "#a07a62", "#b48c70", "#c8a284", "#dcbc9c"]   # Norlin sandstone
LIME = ["#5e5450", "#857868", "#a8977e", "#c2b096", "#d8c8aa", "#ece0c4"]                  # limestone trim
LAMP_GREEN = ["#0f2a20", "#1b4632", "#2a6446", "#3f875e", "#73b98c"]
BRASS = ["#4a3018", "#7a5428", "#a87c38", "#d0a650", "#f0d48a"]
MARBLE = ["#3a2c2e", "#6e5a52", "#8a7466", "#a08a78", "#b8a08a", "#ccb8a0", "#e0d0b8"]
ROSE = ["#3a2428", "#5a3a3a", "#6e4844", "#80564e", "#92665a"]
CARPET_PLUM = ["#1e1018", "#2e1622", "#45202e", "#5e2a3a", "#7a3646", "#c0884a", "#e0b26a"]
CARPET_GREEN = ["#0e1a16", "#16261f", "#1f3429", "#2a4434", "#365640", "#c0884a", "#e0b26a"]
NIGHT_N = ["#0c1022", "#141a34", "#1e2648", "#2a3462", "#3c4a80", "#5a6aa0"]
GRASS = ["#1a2618", "#22321e", "#2c3e24", "#36492a", "#425732", "#52683c", "#647a46"]


def _rng(seed):
    return np.random.default_rng(seed)


# --- books ------------------------------------------------------------------------------------
def book_row(cv, x, base, w, max_h, seed=0, lean=0.06, gaps=0.05, stacks=0.05, palette=SPINES, dim=0.0):
    """Fill a shelf from x to x+w, books standing on row `base` (their bottom pixel is base-1).
    Spines vary in width, height and colour; some carry gilt bands or a title label, a few lean
    or lie in a small stack. dim > 0 darkens toward shadow (shelves away from the light)."""
    rng = _rng(seed)
    bx = x
    end = x + w
    while bx < end - 1:
        r = rng.random()
        if r < gaps:
            bx += int(rng.integers(2, 6))
            continue
        if r < gaps + stacks and end - bx > 14:
            # a few books lying flat
            sw = int(rng.integers(10, 15))
            sw = min(sw, end - bx)
            yy = base
            for k in range(int(rng.integers(2, 4))):
                c = shade(palette[int(rng.integers(len(palette)))], -dim)
                th = int(rng.integers(2, 4))
                inset = int(rng.integers(0, 2))
                cv.rect(bx + inset, yy - th, sw - inset - int(rng.integers(0, 2)), th, c)
                cv.hline(bx + inset, yy - th, sw - inset - 1, shade(c, 0.18))
                cv.vline(bx + sw - 2, yy - th, th, shade(PAGE[2], -dim - 0.1))
                yy -= th
            bx += sw + 1
            continue
        bw = int(rng.choice([2, 3, 3, 3, 4, 4, 5]))
        bh = int(rng.integers(max(4, int(max_h * 0.62)), max_h + 1))
        if bx + bw > end:
            bw = end - bx
            if bw < 2:
                break
        c = shade(palette[int(rng.integers(len(palette)))], -dim + float(rng.uniform(-0.06, 0.06)))
        if r > 1 - lean and bw <= 3 and end - bx > bh // 2 + 4:
            # a leaning book: a parallelogram resting on its neighbour
            for i in range(bh):
                off = i * 2 // 5
                cv.hline(bx + off, base - 1 - i, bw, c)
                cv.px(bx + off, base - 1 - i, shade(c, 0.2))
            bx += bw + bh * 2 // 5 + 1
            continue
        top = base - bh
        cv.rect(bx, top, bw, bh, c)
        cv.vline(bx, top, bh, shade(c, 0.22))                    # lit edge
        if bw >= 3:
            cv.vline(bx + bw - 1, top, bh, shade(c, -0.25))      # spine shadow
        cv.hline(bx, top, bw, shade(c, 0.32))
        g = rng.random()
        if bw >= 3 and g < 0.45:
            cv.hline(bx + 1, top + 2, bw - 2, shade(GILT, -dim * 0.6))
            if bh > 9:
                cv.hline(bx + 1, base - 3, bw - 2, shade(GILT, -dim * 0.6 - 0.2))
        elif bw >= 3 and g < 0.6 and bh > 10:
            cv.rect(bx + 1, top + bh // 3, bw - 2, 3, shade(PAGE[2], -dim - 0.05))
        bx += bw


def book_stack(cv, x, base, w, n=3, seed=0, palette=SPINES):
    """A small pile of closed books lying flat (on a desk or a cart), seen from the front."""
    rng = _rng(seed)
    yy = base
    for k in range(n):
        c = palette[int(rng.integers(len(palette)))]
        th = int(rng.integers(2, 4))
        bw = w - int(rng.integers(0, 4))
        ox = x + int(rng.integers(0, max(1, w - bw + 1)))
        cv.rect(ox - 1, yy - th - 1, bw + 2, th + 2, OUT)
        cv.rect(ox, yy - th, bw, th, c)
        cv.hline(ox, yy - th, bw, shade(c, 0.25))
        cv.rect(ox + bw - 3, yy - th, 2, th, PAGE[2]); cv.vline(ox + bw - 2, yy - th, th, PAGE[1])
        yy -= th + 1


def open_book(cv, x, y, w=14, h=7, inks=("#3a4a7a",), seed=0):
    """An open book seen from above: two pages, a dark gutter, lines of writing in the given inks."""
    rng = _rng(seed)
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, PAGE[3])
    cv.rect(x, y + h - 1, w, 1, PAGE[1])
    cv.vline(x + w // 2, y, h, PAGE[0])
    cv.vline(x + w // 2 - 1, y, h, PAGE[2])
    for i, ly in enumerate(range(y + 1, y + h - 1, 2)):
        for side in (0, 1):
            ink = inks[(i + side) % len(inks)]
            lx = x + 1 + side * (w // 2 + 1)
            cv.hline(lx, ly, int(rng.integers(2, w // 2 - 1)), ink)


def wall_shelves(cv, x, y, w, h, seed=0, shelf=22, dim=0.0, frame=True):
    """Built-in shelving painted into a wall: oak frame, dark back, shelf boards, rows of books."""
    rng = _rng(seed)
    if frame:
        cv.rect(x - 3, y - 4, w + 6, h + 4, OAK[1])
        cv.rect(x - 2, y - 3, w + 4, h + 3, OAK[3])
        cv.hline(x - 3, y - 4, w + 6, OAK[4]); cv.hline(x - 2, y - 3, w + 4, OAK[5])
    cv.rect(x, y, w, h, OAK_DARK[1])
    rows = list(range(y + shelf, y + h + 1, shelf))
    prev = y
    for k, sy in enumerate(rows):
        cv.hline(x, prev, w, OAK_DARK[0])
        book_row(cv, x + 1, sy - 2, w - 2, shelf - 5, seed=seed * 31 + k, dim=dim)
        cv.rect(x, sy - 2, w, 2, OAK[3]); cv.hline(x, sy - 2, w, OAK[5])
        cv.hline(x, sy, w, C("#0d0b16", 0.5))
        prev = sy
    # uprights every ~40px so long runs read as separate bays
    for ux in range(x + 40 + int(rng.integers(0, 6)), x + w - 20, 44):
        cv.rect(ux, y, 3, h, OAK[2]); cv.vline(ux, y, h, OAK[4])


def bookcase(width=130, height=112, seed=0, shelf=22, ladder=False, top_band=4, dim=0.0, crown=True):
    """A freestanding oak bookcase, full of books, as a prop (anchor bottom-centre).
    `height` is the case height in pixels; a little crown and a floor shadow sit around it."""
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.45)
    top = base - height
    cv.rect(ox, top, width, height, OUT)
    # top surface seen from above, then the crown moulding
    cv.rect(ox + 1, top + 1, width - 2, top_band, OAK[4]); cv.hline(ox + 1, top + 1, width - 2, OAK[5])
    if crown:
        cv.rect(ox - 2, top + top_band, width + 4, 5, OUT)
        cv.rect(ox - 1, top + top_band + 1, width + 2, 3, OAK[3]); cv.hline(ox - 1, top + top_band + 1, width + 2, OAK[5])
        cv.hline(ox - 1, top + top_band + 3, width + 2, OAK[2])
    inner_top = top + top_band + 6
    plinth = 7
    side = 4
    # stiles and back
    cv.rect(ox + 1, inner_top, side, base - inner_top - 1, OAK[3]); cv.vline(ox + 1, inner_top, base - inner_top - 1, OAK[4])
    cv.rect(ox + width - 1 - side, inner_top, side, base - inner_top - 1, OAK[2]); cv.vline(ox + width - 2, inner_top, base - inner_top - 1, OAK[1])
    bx0, bx1 = ox + 1 + side, ox + width - 1 - side
    cv.rect(bx0, inner_top, bx1 - bx0, base - plinth - inner_top, OAK_DARK[1])
    # a centre upright for wide cases
    bays = [(bx0, bx1)]
    if width > 90:
        mid = ox + width // 2
        cv.rect(mid - 1, inner_top, 3, base - plinth - inner_top, OAK[3]); cv.vline(mid - 1, inner_top, base - plinth - inner_top, OAK[4])
        bays = [(bx0, mid - 1), (mid + 2, bx1)]
    usable = base - plinth - inner_top
    n = max(2, round(usable / shelf))
    step = usable / n
    for k in range(n):
        y0 = inner_top + int(round(k * step))
        y1 = inner_top + int(round((k + 1) * step))
        for b, (a0, a1) in enumerate(bays):
            cv.hline(a0, y0, a1 - a0, OAK_DARK[0])
            book_row(cv, a0 + 1, y1 - 2, a1 - a0 - 2, y1 - y0 - 5, seed=seed * 97 + k * 7 + b, dim=dim)
        cv.rect(bx0, y1 - 2, bx1 - bx0, 2, OAK[3]); cv.hline(bx0, y1 - 2, bx1 - bx0, OAK[5])
    # plinth
    cv.rect(ox + 1, base - plinth, width - 2, plinth - 1, OAK[2]); cv.hline(ox + 1, base - plinth, width - 2, OAK[4])
    cv.hline(ox + 1, base - 2, width - 2, OAK[1])
    for px_ in range(ox + 8, ox + width - 8, 16):
        cv.rect(px_, base - plinth + 2, 10, 2, OAK[1])
    if ladder:
        library_ladder(cv, ox + width - 30, top + top_band + 2, base)
    return cv, ox + width // 2, base


def library_ladder(cv, x, top, base):
    """A rolling library ladder leaning on a case: brass rail at the top, oak rungs, castors."""
    cv.rect(x - 6, top + 2, 30, 2, BRASS[2]); cv.hline(x - 6, top + 2, 30, BRASS[4])
    cv.line(x, top + 3, x - 7, base - 2, OUT); cv.line(x + 1, top + 3, x - 6, base - 2, OAK[4])
    cv.line(x + 12, top + 3, x + 5, base - 2, OUT); cv.line(x + 13, top + 3, x + 6, base - 2, OAK[4])
    n = (base - top) // 9
    for i in range(1, n):
        yy = top + 3 + i * 9
        t = (yy - top) / max(1, base - top)
        lx = int(round(x + 1 - 7 * t))
        cv.hline(lx, yy, 12, OAK[5]); cv.hline(lx, yy + 1, 12, OAK[2])
    for wx in (x - 8, x + 4):
        cv.rect(wx, base - 3, 3, 3, IRON[1])


# --- walls ------------------------------------------------------------------------------------
def plaster_wall(cv, x, y, w, h, pal=PLASTER_N, seed=0, shadow_top=14):
    """Warm lamplit plaster: a mottled field with a few soft-edged patches and a ceiling shadow."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[4])
    for _ in range(w * h // 260):
        px_, py_ = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        pw, ph = int(rng.integers(4, 14)), int(rng.integers(2, 5))
        cv.rect(px_, py_, pw, ph, pal[int(rng.choice([3, 5]))])
    for _ in range(w * h // 14):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), pal[int(rng.choice([3, 3, 5]))])
    for i in range(shadow_top):
        a = 0.5 * (1 - i / shadow_top)
        for xx in range(x, x + w):
            if rng.random() < a:
                cv.px(xx, y + i, pal[2])


def ceiling_band(cv, x, y, w, h=10, pal=OAK, stencil=True):
    """The dark ceiling edge seen at the top of a wall: beam, painted stencil band, cornice."""
    cv.rect(x, y, w, h, OAK_DARK[2])
    cv.hline(x, y + h - 4, w, OAK[3]); cv.hline(x, y + h - 3, w, OAK[4]); cv.hline(x, y + h - 2, w, OAK[2])
    cv.hline(x, y + h - 1, w, C("#0d0b16", 0.6))
    if stencil:
        for sx in range(x + 2, x + w, 10):
            cv.px(sx, y + 2, "#7a3646"); cv.px(sx + 1, y + 3, GILT); cv.px(sx + 2, y + 2, "#7a3646")
            cv.px(sx + 5, y + 3, "#2a4434"); cv.px(sx + 6, y + 2, "#2a4434")
        cv.hline(x, y + 5, w, BRASS[1])


def oak_wainscot(cv, x, y, w, h, seed=0, panel=24):
    """Oak dado: rail on top, raised panels, skirting."""
    cv.rect(x, y, w, h, OAK[2])
    cv.rect(x, y, w, 4, OAK[4]); cv.hline(x, y, w, OAK[5]); cv.hline(x, y + 4, w, OAK[0])
    for px_ in range(x + 3, x + w - 8, panel):
        pw = min(panel - 5, x + w - px_ - 3)
        cv.rect(px_, y + 7, pw, h - 13, OAK[1])
        cv.rect(px_ + 1, y + 8, pw - 2, h - 15, OAK[3])
        cv.hline(px_ + 1, y + 8, pw - 2, OAK[4]); cv.vline(px_ + 1, y + 8, h - 15, OAK[4])
        cv.rect(px_ + 3, y + 10, pw - 6, h - 19, OAK[2])
    cv.rect(x, y + h - 4, w, 4, OAK[1]); cv.hline(x, y + h - 4, w, OAK[3])


def stone_wall(cv, x, y, w, h, pal=STONE_N, seed=0, course=6):
    """Dressed sandstone ashlar: long blocks in courses, each with a lit top and a darker foot."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[1])
    row = 0
    for yy in range(y, y + h, course):
        ch = min(course, y + h - yy)
        xx = x - int(rng.integers(0, 14))
        while xx < x + w:
            sw = int(rng.integers(14, 28))
            x0, x1 = max(x, xx), min(x + w, xx + sw - 1)
            r = rng.random()
            tone = pal[3] if r < 0.5 else pal[4] if r < 0.8 else pal[2]
            if x1 > x0:
                cv.rect(x0, yy, x1 - x0, ch - 1, tone)
                cv.hline(x0, yy, x1 - x0, shade(tone, 0.1))
                for _ in range((x1 - x0) * ch // 7):
                    cv.px(x0 + int(rng.integers(0, x1 - x0)), yy + int(rng.integers(0, max(1, ch - 1))),
                          shade(tone, float(rng.choice([-0.07, -0.04, 0.05]))))
            xx += sw
        row += 1


def quoins(cv, x, y0, y1, side="left", pal=LIME):
    """Alternating long and short limestone blocks up a building corner."""
    for k, qy in enumerate(range(y0, y1, 7)):
        qw = 10 if k % 2 == 0 else 6
        qx = x if side == "left" else x - qw
        cv.rect(qx, qy, qw, 6, pal[2]); cv.hline(qx, qy, qw, pal[4]); cv.hline(qx, qy + 5, qw, pal[0])


def plaque(cv, x, y, label, fg=GILT, bg="#1f1a2a", pad=4, frame=BRASS):
    """A small sign board with the game font: brass frame, dark field, gilt letters."""
    w = text_width(label) + pad * 2
    cv.rect(x - 1, y - 1, w + 2, 14, OUT)
    cv.rect(x, y, w, 12, frame[2]); cv.hline(x, y, w, frame[4]); cv.hline(x, y + 11, w, frame[1])
    cv.rect(x + 1, y + 1, w - 2, 10, bg)
    text(cv, label, x + pad, y + 1, fg)
    return w


def directional_sign(cv, x, y, label, arrow="left"):
    """A hanging gilt-on-oak sign pointing the way ('<' or '>' painted into the label)."""
    lab = ("< " + label) if arrow == "left" else (label + " >")
    w = text_width(lab) + 10
    for hx in (x + 6, x + w - 7):
        cv.vline(hx, y - 8, 8, IRON[2])
    cv.rect(x - 1, y - 1, w + 2, 15, OUT)
    cv.rect(x, y, w, 13, OAK[2]); cv.hline(x, y, w, OAK[4]); cv.hline(x, y + 12, w, OAK[1])
    cv.rect(x + 2, y + 2, w - 4, 9, "#1c1418")
    text(cv, lab, x + 5, y + 2, GILT)
    return w


# --- windows ----------------------------------------------------------------------------------
def _night_glass(cv, x, y, w, h, seed, arch, view, moon=None):
    """Night seen through a window: graded sky, stars, a roofline or treeline, a lit window or two."""
    rng = _rng(seed)
    r = w / 2
    top = y - (int(r) if arch else 0)
    for yy in range(top, y + h):
        t = (yy - top) / max(1, y + h - top)
        c = NIGHT_N[1] if t < 0.3 else NIGHT_N[2] if t < 0.62 else NIGHT_N[3]
        for xx in range(x, x + w):
            if arch and yy < y:
                dx, dy = xx - (x + r - 0.5), yy - y
                if dx * dx + dy * dy > r * r:
                    continue
            cv.px(xx, yy, c)
    for _ in range(max(2, w * h // 70)):
        sx, sy = x + int(rng.integers(0, w)), top + int(rng.integers(0, max(1, (y + h - top) * 2 // 3)))
        if cv.a[sy, sx, 2] > 0.1:
            cv.px(sx, sy, "#c8d0f0" if rng.random() < 0.5 else "#8a96c8")
    if moon:
        mx, my = moon
        cv.ellipse(mx - 3, my - 3, 7, 7, "#efe2b8"); cv.ellipse(mx - 1, my - 4, 7, 7, NIGHT_N[1])
    if view == "trees":
        for bx in range(x - 4, x + w + 4, 5):
            bh = int(rng.integers(h // 5, h // 3))
            cv.ellipse(bx, y + h - bh, 9, bh * 2, "#121a22")
        for _ in range(w // 8):
            cv.px(x + int(rng.integers(0, w)), y + h - int(rng.integers(2, h // 5)), "#1e2a2a")
    elif view == "campus":
        for bx in range(x, x + w, 8):
            bh = int(rng.integers(5, 13))
            cv.rect(bx, y + h - bh, 8, bh, "#121628")
            if rng.random() < 0.5:
                cv.px(bx + int(rng.integers(1, 7)), y + h - bh + int(rng.integers(2, max(3, bh))), "#e9a84a")
        cv.rect(x, y + h - 3, w, 3, "#0e1120")


def arched_window(cv, x, y, w, h, seed=0, view="campus", frame=OAK, surround=None, mullion=FRAME, moon=None,
                  transom=True, sill=True):
    """Tall interior window, round-headed: deep reveal, oak frame, small panes, night beyond.
    (x, y) is the top-left of the rectangular part; the arch rises w/2 above y."""
    r = w // 2
    sur = surround or STONE_N
    # reveal (the thickness of the wall), lit on one side
    cv.ellipse(x - 6, y - r - 6, w + 12, w + 12, sur[2])
    cv.rect(x - 6, y, w + 12, h + 4, sur[2])
    cv.ellipse(x - 5, y - r - 5, w + 10, w + 10, sur[4])
    cv.rect(x - 5, y, w + 10, h + 3, sur[4])
    cv.ellipse(x - 3, y - r - 3, w + 6, w + 6, sur[1])
    cv.rect(x - 3, y, w + 6, h + 1, sur[1])
    cv.rect(x - 3, y, 3, h + 1, sur[3])                       # the lit jamb
    # keystone
    cv.rect(x + r - 3, y - r - 7, 7, 6, sur[5]); cv.hline(x + r - 3, y - r - 7, 7, sur[6] if len(sur) > 6 else sur[5])
    # frame and glass
    cv.ellipse(x - 1, y - r - 1, w + 2, w + 2, frame[1]); cv.rect(x - 1, y, w + 2, h + 1, frame[1])
    _night_glass(cv, x, y, w, h, seed, True, view, moon)
    # panes: glazing bars every 6px, a heavier transom bar and a central mullion
    for gx in range(x + 5, x + w - 1, 6):
        cv.vline(gx, y - r + 2, h + r - 2, C(mullion, 0.85))
    for gy in range(y + 6, y + h, 8):
        cv.hline(x, gy, w, C(mullion, 0.85))
    for a in np.linspace(np.pi, 2 * np.pi, 9)[1:-1]:
        cv.line(x + r - 0.5, y, int(round(x + r - 0.5 + np.cos(a) * r)), int(round(y + np.sin(a) * r)), C(mullion, 0.6))
    if transom:
        cv.rect(x, y - 1, w, 2, frame[3]); cv.hline(x, y - 1, w, frame[4])
    cv.vline(x + r - 1, y - r, h + r, frame[3]); cv.vline(x + r, y - r, h + r, frame[2])
    # reflections on the glass
    cv.line(x + 2, y + h - 6, x + 7, y + h - 18, C("#8a96c8", 0.35))
    cv.line(x + w - 6, y + 10, x + w - 3, y + 4, C("#8a96c8", 0.3))
    if sill:
        cv.rect(x - 7, y + h + 1, w + 14, 4, sur[5]); cv.hline(x - 7, y + h + 1, w + 14, sur[6] if len(sur) > 6 else sur[5])
        cv.hline(x - 7, y + h + 4, w + 14, sur[1]); cv.hline(x - 7, y + h + 5, w + 14, C("#0d0b16", 0.45))


def facade_window(cv, x, y, w, h, seed=0, lit=True, arch=False, tiers=2, surround=LIME):
    """An exterior window glowing with lamplight: limestone surround, bronze frame, small panes,
    a spandrel panel between tiers, bookcases faintly seen inside. With arch=True a round head
    rises w/2 above y."""
    rng = _rng(seed)
    r = w // 2
    top = y - (r if arch else 0)
    # glass mask (rectangle plus an optional semicircle), then the frame ring around it
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    glass = (xs >= x) & (xs < x + w) & (ys >= y) & (ys < y + h)
    if arch:
        glass |= ((xs - (x + r - 0.5)) ** 2 + (ys - y + 0.5) ** 2 <= r * r) & (ys < y) & (ys >= top)
    from scipy import ndimage
    frame = ndimage.binary_dilation(glass, iterations=1) & ~glass
    surr = ndimage.binary_dilation(glass, iterations=3) & ~glass & ~frame
    cv.a[surr] = C(surround[2])
    lit_side = surr & (xs < x + 1)
    cv.a[lit_side] = C(surround[4])
    cv.a[frame] = C("#2a1c18")
    pal = GLOW if lit else DARKGLASS
    for yy in range(top, y + h):
        t = (yy - top) / max(1, y + h - top)
        c = C(pal[3] if t < 0.22 else pal[2] if t < 0.65 else pal[1])
        row = glass[yy]
        cv.a[yy, row] = c
    if lit:
        # shelves glimpsed inside
        for sy in range(y + h - 4, y + h // 2, -6):
            cv.hline(x, sy, w, shade(GLOW[1], -0.3))
            for bx in range(x, x + w, 2):
                if rng.random() < 0.6:
                    cv.vline(bx, sy - 3, 3, shade(GLOW[1], -float(rng.uniform(0.1, 0.4))))
        cv.rect(x + 1, top + (r // 2 if arch else 1), max(1, w // 3), max(2, h // 4), GLOW[4])
    else:
        cv.line(x + 1, y + h - 3, x + w - 3, y + 2, DARKGLASS[3])
    # glazing bars, clipped to the glass
    bars = np.zeros_like(glass)
    bars[:, x + 4:x + w - 1:5] = True
    bars[y + 6:y + h:7, :] = True
    if arch:
        bars[top:y, :] &= False
        bars[top:y, x + r - 1] = True
        bars[y, :] = True
    cv.a[bars & glass] = C(FRAME)
    if tiers == 2:
        sy = y + h * 2 // 5
        cv.rect(x - 1, sy, w + 2, 6, "#5a3a24"); cv.hline(x - 1, sy, w + 2, "#8a6230")
        for k in range(x + 1, x + w - 1, 4):
            cv.rect(k, sy + 2, 2, 2, "#3a2418")
    if arch:
        cv.rect(x + r - 2, top - 4, 4, 4, surround[4]); cv.hline(x + r - 2, top - 4, 4, surround[5])
    cv.rect(x - 4, y + h + 2, w + 8, 3, surround[3]); cv.hline(x - 4, y + h + 2, w + 8, surround[5])
    cv.hline(x - 4, y + h + 5, w + 8, C("#0d0b16", 0.5))


# --- lamps ------------------------------------------------------------------------------------
def banker_lamp(cv, x, y, glow=True):
    """A green-shaded desk lamp standing on row y (its foot), centred on x. About 11px tall."""
    if glow:
        for r, a in [(11, 0.06), (7, 0.08)]:
            cv.ellipse(x - r, y - 2 - r // 2, r * 2 + 1, r, C("#f6cf7a", a))
    cv.rect(x - 3, y - 2, 7, 2, OUT); cv.hline(x - 2, y - 2, 5, BRASS[3])
    cv.vline(x, y - 7, 5, BRASS[2]); cv.px(x + 1, y - 6, BRASS[1])
    cv.rect(x - 5, y - 11, 11, 5, OUT)
    cv.rect(x - 4, y - 10, 9, 3, LAMP_GREEN[3]); cv.hline(x - 3, y - 10, 7, LAMP_GREEN[4])
    cv.hline(x - 4, y - 8, 9, LAMP_GREEN[2])
    cv.hline(x - 4, y - 7, 9, "#f6cf7a" if glow else LAMP_GREEN[1])
    if glow:
        cv.rect(x - 6, y - 6, 13, 3, C("#f6cf7a", 0.18))


def pendant_lamp(cv, x, y, chain_top=0, r=5, lit=True, glass=None):
    """A hanging library lantern: chain from chain_top, brass cap, opal glass globe, warm core."""
    cv.vline(x, chain_top, y - chain_top - r, IRON[2])
    for cy in range(chain_top + 1, y - r, 3):
        cv.px(x, cy, IRON[3])
    cv.rect(x - 3, y - r - 2, 7, 3, BRASS[2]); cv.hline(x - 3, y - r - 2, 7, BRASS[4])
    if lit:
        for rr, a in [(r * 3, 0.05), (r * 2, 0.08)]:
            cv.ellipse(x - rr, y - rr, rr * 2 + 1, rr * 2 + 1, C("#f6cf7a", a))
    g = glass or (["#e9a84a", "#f6cd78", "#fde9b6"] if lit else ["#3a3448", "#4e4860", "#6a6480"])
    cv.ellipse(x - r - 1, y - r - 1, r * 2 + 3, r * 2 + 3, OUT)
    cv.ellipse(x - r, y - r, r * 2 + 1, r * 2 + 1, g[0])
    cv.ellipse(x - r + 1, y - r, r * 2 - 1, r * 2 - 1, g[1])
    cv.ellipse(x - r // 2, y - r + 1, r, r, g[2])
    cv.rect(x - 1, y + r, 3, 2, BRASS[1])


def shade_pendant(cv, x, y, chain_top=0, w=16, shade_pal=LAMP_GREEN, lit=True):
    """A reading-room pendant: rod from the ceiling, a wide green enamel shade (lit cream inside),
    a warm bulb under it and a soft glow below. (x, y) is the bottom centre of the shade."""
    cv.vline(x, chain_top, y - chain_top - 7, IRON[1])
    cv.rect(x - 2, chain_top, 5, 2, BRASS[2])
    if lit:
        for rr, a in [(w, 0.05), (w * 2 // 3, 0.08)]:
            cv.ellipse(x - rr, y - 2, rr * 2 + 1, rr + 2, C("#f6cf7a", a))
    hw = w // 2
    cv.rect(x - 2, y - 9, 5, 3, BRASS[2]); cv.hline(x - 2, y - 9, 5, BRASS[4])
    cv.poly([(x - 3, y - 7), (x + 3, y - 7), (x + hw + 1, y), (x - hw - 1, y)], OUT)
    cv.poly([(x - 2, y - 6), (x + 2, y - 6), (x + hw, y - 1), (x - hw, y - 1)], shade_pal[3])
    cv.poly([(x - 2, y - 6), (x, y - 6), (x - hw + 3, y - 1), (x - hw, y - 1)], shade_pal[4])
    cv.hline(x - hw, y - 1, w + 1, shade_pal[2])
    cv.hline(x - hw + 1, y, w - 1, "#f6cd78" if lit else shade_pal[1])
    if lit:
        cv.rect(x - 2, y + 1, 5, 2, "#fde9b6")


def wall_sconce(cv, x, y, lit=True):
    """A brass wall bracket with a small cream shade; (x, y) is the bracket plate."""
    if lit:
        for rr, a in [(14, 0.05), (9, 0.08)]:
            cv.ellipse(x - rr, y - 6 - rr, rr * 2 + 1, rr * 2 + 1, C("#f6cf7a", a))
    cv.rect(x - 2, y, 5, 5, BRASS[1]); cv.rect(x - 1, y + 1, 3, 3, BRASS[3])
    cv.vline(x, y - 4, 4, BRASS[2])
    cv.poly([(x - 4, y - 5), (x + 4, y - 5), (x + 3, y - 11), (x - 3, y - 11)], OUT)
    cv.poly([(x - 3, y - 6), (x + 3, y - 6), (x + 2, y - 10), (x - 2, y - 10)], "#f6cd78" if lit else "#6a6480")
    cv.hline(x - 3, y - 6, 7, "#fde9b6" if lit else "#4e4860")


def standard_lamp(height=68, shade_pal=LAMP_GREEN, seed=0):
    """Indoor floor lamp as a prop: weighted brass foot, slim column, a shade whose underside glows.
    The bulb sits about 5px below the top so it matches the room's point light (h - 5)."""
    w = 26
    cv = Canvas(w, height + 5, seed=seed)
    cx, base = w // 2, height + 2
    ground_shadow(cv, cx, base, 8, 2)
    cv.ellipse(cx - 6, base - 4, 13, 5, OUT); cv.ellipse(cx - 5, base - 4, 11, 4, BRASS[2]); cv.hline(cx - 4, base - 4, 8, BRASS[4])
    top = base - height
    cv.rect(cx - 1, top + 12, 3, height - 15, OUT); cv.vline(cx, top + 12, height - 15, BRASS[3])
    for ry in (top + 26, top + 44):
        cv.rect(cx - 2, ry, 5, 2, BRASS[1]); cv.hline(cx - 2, ry, 5, BRASS[4])
    # shade: trapezoid, lit from inside
    cv.poly([(cx - 6, top), (cx + 6, top), (cx + 10, top + 12), (cx - 10, top + 12)], OUT)
    cv.poly([(cx - 5, top + 1), (cx + 5, top + 1), (cx + 9, top + 11), (cx - 9, top + 11)], shade_pal[3])
    cv.poly([(cx - 4, top + 1), (cx + 0, top + 1), (cx - 2, top + 10), (cx - 8, top + 10)], shade_pal[4])
    cv.poly([(cx + 3, top + 2), (cx + 5, top + 2), (cx + 8, top + 10), (cx + 5, top + 10)], shade_pal[2])
    cv.hline(cx - 9, top + 11, 19, "#f6cd78")
    cv.rect(cx - 2, top + 12, 5, 2, "#fde9b6")
    return cv, cx, base


def lantern_head(cv, cx, top, glass=("#e9a84a", "#f6cf7a", "#fff0c4")):
    """Square iron lantern with a pyramid cap (lamp posts, plinth lamps)."""
    cv.poly([(cx - 7, top + 5), (cx, top), (cx + 6, top + 5)], IRON[1]); cv.hline(cx - 6, top + 4, 12, IRON[3])
    cv.rect(cx - 1, top - 2, 2, 2, IRON[2])
    cv.rect(cx - 5, top + 5, 10, 12, IRON[1])
    cv.rect(cx - 4, top + 6, 8, 10, glass[0]); cv.rect(cx - 3, top + 7, 6, 8, glass[1]); cv.rect(cx - 1, top + 8, 2, 5, glass[2])
    cv.vline(cx, top + 6, 10, C(IRON[1], 0.6))
    cv.rect(cx - 6, top + 16, 12, 2, IRON[1]); cv.hline(cx - 6, top + 16, 12, IRON[3])


def quiet_lamp_post(height=68):
    """The quad's 'quiet lamp': an iron post with a reading-lamp green hood over a warm lantern,
    a book-shaped plaque on the post. Lamp core sits ~5px below the top."""
    w = 26
    cv = Canvas(w, height + 6, seed=3)
    cx, base = w // 2, height + 2
    ground_shadow(cv, cx, base, 10, 2)
    cv.rect(cx - 6, base - 5, 12, 5, IRON[1]); cv.hline(cx - 6, base - 5, 12, IRON[3])
    cv.rect(cx - 4, base - 9, 8, 4, IRON[2]); cv.hline(cx - 4, base - 9, 8, IRON[4])
    top = base - height
    cv.rect(cx - 2, top + 18, 4, height - 27, IRON[2]); cv.vline(cx - 2, top + 18, height - 27, IRON[3]); cv.vline(cx + 1, top + 18, height - 27, IRON[0])
    for ry in (top + 24, top + 40):
        cv.rect(cx - 3, ry, 6, 2, IRON[1]); cv.hline(cx - 3, ry, 6, IRON[4])
    # little open-book plaque on the post
    py = top + 44
    cv.rect(cx - 6, py, 12, 7, OUT); cv.rect(cx - 5, py + 1, 5, 5, PAGE[3]); cv.rect(cx + 1, py + 1, 4, 5, PAGE[2])
    cv.hline(cx - 4, py + 3, 3, PAGE[0]); cv.hline(cx + 2, py + 3, 2, PAGE[0])
    # lantern and its green hood
    cv.rect(cx - 5, top + 6, 10, 11, IRON[1])
    cv.rect(cx - 4, top + 7, 8, 9, AMBER[2]); cv.rect(cx - 3, top + 8, 6, 7, AMBER[3]); cv.rect(cx - 1, top + 9, 2, 4, AMBER[4])
    cv.rect(cx - 6, top + 16, 12, 2, IRON[1]); cv.hline(cx - 6, top + 16, 12, IRON[3])
    cv.poly([(cx - 9, top + 7), (cx - 4, top + 1), (cx + 4, top + 1), (cx + 9, top + 7)], OUT)
    cv.poly([(cx - 8, top + 6), (cx - 3, top + 2), (cx + 3, top + 2), (cx + 8, top + 6)], LAMP_GREEN[3])
    cv.hline(cx - 3, top + 2, 6, LAMP_GREEN[4]); cv.hline(cx - 8, top + 6, 17, LAMP_GREEN[1])
    cv.rect(cx - 1, top - 1, 2, 2, IRON[2])
    return cv, cx, base


def plinth_lamp(cv, cx, base, plinth_w=18, plinth_h=24, post=22, pal=STONE_N):
    """A stone plinth with an iron lantern on top, painted into a background (base = floor row)."""
    x0 = cx - plinth_w // 2
    cv.rect(x0 - 2, base - plinth_h, plinth_w + 4, 4, LIME[3]); cv.hline(x0 - 2, base - plinth_h, plinth_w + 4, LIME[5])
    cv.hline(x0 - 2, base - plinth_h + 3, plinth_w + 4, LIME[1])
    cv.rect(x0, base - plinth_h + 4, plinth_w, plinth_h - 6, pal[3])
    cv.vline(x0, base - plinth_h + 4, plinth_h - 6, pal[5]); cv.vline(x0 + plinth_w - 1, base - plinth_h + 4, plinth_h - 6, pal[1])
    cv.rect(x0 + 3, base - plinth_h + 8, plinth_w - 6, plinth_h - 14, pal[2]); cv.rect(x0 + 4, base - plinth_h + 9, plinth_w - 8, plinth_h - 16, pal[3])
    cv.rect(x0 - 2, base - 3, plinth_w + 4, 3, LIME[2]); cv.hline(x0 - 2, base - 3, plinth_w + 4, LIME[4])
    top = base - plinth_h - post
    cv.rect(cx - 2, top + 16, 4, post - 16, IRON[2]); cv.vline(cx - 2, top + 16, post - 16, IRON[3])
    cv.rect(cx - 4, base - plinth_h - 3, 8, 3, IRON[1])
    lantern_head(cv, cx, top)
    return (cx, top + 11)


# --- furniture --------------------------------------------------------------------------------
def library_chair_back(cv, cx, base, h=13, w=11, pal=OAK):
    """The back of an oak chair seen over a table: two posts, a top rail, a slat."""
    x = cx - w // 2
    cv.rect(x - 1, base - h - 1, w + 2, h + 1, OUT)
    cv.rect(x, base - h, w, 3, pal[4]); cv.hline(x, base - h, w, pal[5])
    cv.rect(x, base - h + 3, 2, h - 3, pal[3]); cv.rect(x + w - 2, base - h + 3, 2, h - 3, pal[2])
    cv.rect(x + 2, base - h + 3, w - 4, h - 3, OAK_DARK[1])
    cv.rect(x + w // 2 - 1, base - h + 3, 3, h - 4, pal[3])


def reading_table(width=150, height=38, lamps=2, seed=0, chairs=True, clutter=True, top_depth=11, extra=None):
    """A long oak reading-room table seen from the front and a little above: chair backs on the
    far side, green banker's lamps, open books and paper on the top, a front apron and legs.
    `extra(cv, ox, top_y, width)` may paint more on the table top."""
    rng = _rng(seed)
    pad_top = 16
    cv = Canvas(width + 8, height + pad_top + 6, seed=seed)
    ox, base = 4, height + pad_top + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3, alpha=0.42)
    front = base - 22                       # front edge of the table top
    top_y = front - top_depth               # far edge of the top surface
    if chairs:
        n = max(2, width // 40)
        for i in range(n):
            cx = ox + int((i + 0.5) * width / n) + int(rng.integers(-3, 4))
            library_chair_back(cv, cx, top_y + 2, h=13)
    # legs (turned), stretcher
    for lx in (ox + 5, ox + width - 10):
        cv.rect(lx, front + 3, 5, base - front - 3, OUT)
        cv.rect(lx + 1, front + 3, 3, base - front - 4, OAK[2]); cv.vline(lx + 1, front + 3, base - front - 4, OAK[3])
        cv.rect(lx, front + 10, 5, 2, OAK[4])
    cv.rect(ox + 9, base - 7, width - 18, 2, OAK[1])
    # top surface and the front apron
    cv.rect(ox, top_y - 1, width, front - top_y + 6, OUT)
    cv.rect(ox + 1, top_y, width - 2, front - top_y, OAK[4])
    for gy in range(top_y + 2, front, 3):
        for _ in range(width // 14):
            gx = ox + 2 + int(rng.integers(0, width - 12))
            cv.hline(gx, gy, int(rng.integers(4, 10)), OAK[3])
    cv.hline(ox + 1, top_y, width - 2, OAK[5])
    cv.rect(ox + 1, front, width - 2, 4, OAK[3]); cv.hline(ox + 1, front, width - 2, OAK[5])
    cv.hline(ox + 1, front + 3, width - 2, OAK[1])
    # lamps along the centre line, with warm pools on the wood
    lamp_xs = [ox + int((i + 0.5) * width / lamps) for i in range(lamps)]
    for lx in lamp_xs:
        cv.ellipse(lx - 13, top_y + 1, 27, front - top_y - 1, C("#f6cf7a", 0.16))
        cv.ellipse(lx - 8, top_y + 2, 17, front - top_y - 3, C("#fde9b6", 0.12))
    if clutter:
        for i in range(int(width // 30)):
            px_ = ox + 8 + int(rng.integers(0, width - 26))
            if any(abs(px_ + 7 - lx) < 10 for lx in lamp_xs):
                continue
            k = rng.random()
            py_ = top_y + 2 + int(rng.integers(0, max(1, top_depth - 8)))
            if k < 0.4:
                open_book(cv, px_, py_, 14, 6, seed=seed + i)
            elif k < 0.7:
                cv.rect(px_, py_ + 1, 9, 6, PAGE[3]); cv.hline(px_ + 1, py_ + 3, 6, PAGE[0]); cv.hline(px_ + 1, py_ + 5, 5, PAGE[0])
                cv.line(px_ + 10, py_ + 6, px_ + 15, py_ + 3, "#c47a2c")
            else:
                book_stack(cv, px_, py_ + 6, 11, n=2, seed=seed + i)
    if extra:
        extra(cv, ox, top_y, width)
    for lx in lamp_xs:
        banker_lamp(cv, lx, top_y + top_depth // 2 + 3)
    return cv, ox + width // 2, base


def library_bench(width=90, height=30, seed=0, cushion="#2a4434"):
    """A plain oak reading bench with a long green cushion, seen from the front."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    seat = base - 14
    for lx in (ox + 3, ox + width - 8):
        cv.rect(lx, seat + 3, 5, base - seat - 3, OUT); cv.rect(lx + 1, seat + 3, 3, base - seat - 4, OAK[2]); cv.vline(lx + 1, seat + 3, base - seat - 4, OAK[3])
    cv.rect(ox + 7, base - 6, width - 14, 2, OAK[1])
    # seat top (seen from above), cushion, apron
    cv.rect(ox, seat - 9, width, 13, OUT)
    cv.rect(ox + 1, seat - 8, width - 2, 8, OAK[4]); cv.hline(ox + 1, seat - 8, width - 2, OAK[5])
    cc = C(cushion)
    cv.rect(ox + 4, seat - 7, width - 8, 6, cushion); cv.hline(ox + 4, seat - 7, width - 8, shade(cushion, 0.25))
    cv.hline(ox + 4, seat - 2, width - 8, shade(cushion, -0.3))
    for bx in range(ox + 14, ox + width - 10, 16):
        cv.px(bx, seat - 4, shade(cushion, -0.35))
    cv.rect(ox + 1, seat, width - 2, 3, OAK[3]); cv.hline(ox + 1, seat, width - 2, OAK[5]); cv.hline(ox + 1, seat + 2, width - 2, OAK[1])
    return cv, ox + width // 2, base


def checkout_desk(width=180, height=52, seed=0, left_plate="CHECKOUT", right_plate="RETURNS"):
    """The circulation desk: a long oak counter with raised panels, a green leather top seen from
    above with a brass edge, a banker's lamp, returned books, a date stamp and ink pad, a card
    file and a bell. Brass plates on the front: CHECKOUT on the left, a RETURNS slot on the right."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.45)
    front_top = base - 30
    top_y = front_top - 10
    # counter top: oak rim, leather inlay, brass front edge
    cv.rect(ox - 1, top_y - 1, width + 2, front_top - top_y + 3, OUT)
    cv.rect(ox, top_y, width, front_top - top_y, OAK[4]); cv.hline(ox, top_y, width, OAK[5])
    cv.rect(ox + 4, top_y + 2, width - 8, front_top - top_y - 4, "#24402e"); cv.hline(ox + 4, top_y + 2, width - 8, "#2e5038")
    cv.rect(ox - 1, front_top, width + 2, 3, BRASS[2]); cv.hline(ox - 1, front_top, width + 2, BRASS[4])
    # front: oak with raised panels
    cv.rect(ox, front_top + 3, width, base - front_top - 3, OUT)
    cv.rect(ox + 1, front_top + 3, width - 2, base - front_top - 4, OAK[3])
    pw = 26
    for px_ in range(ox + 5, ox + width - pw, pw + 4):
        cv.rect(px_, front_top + 7, pw, base - front_top - 14, OAK[1])
        cv.rect(px_ + 1, front_top + 8, pw - 2, base - front_top - 16, OAK[4])
        cv.rect(px_ + 3, front_top + 10, pw - 6, base - front_top - 20, OAK[3])
        cv.hline(px_ + 1, front_top + 8, pw - 2, OAK[5])
    cv.rect(ox + 1, base - 5, width - 2, 4, OAK[2]); cv.hline(ox + 1, base - 5, width - 2, OAK[4])
    # brass plates
    if left_plate:
        tw = text_width(left_plate) + 6
        px_ = ox + 10
        cv.rect(px_, front_top + 9, tw, 11, BRASS[2]); cv.hline(px_, front_top + 9, tw, BRASS[4]); cv.hline(px_, front_top + 19, tw, BRASS[0])
        text(cv, left_plate, px_ + 3, front_top + 10, "#3a2418")
    if right_plate:
        tw = text_width(right_plate) + 6
        px_ = ox + width - 10 - tw
        cv.rect(px_, front_top + 7, tw, 18, BRASS[2]); cv.hline(px_, front_top + 7, tw, BRASS[4])
        text(cv, right_plate, px_ + 3, front_top + 7, "#3a2418")
        cv.rect(px_ + 4, front_top + 18, tw - 8, 4, OUT); cv.hline(px_ + 5, front_top + 19, tw - 10, "#120c10")
    # on the counter: lamp, returned books, stamp and pad, card file, bell
    lamp_x = ox + 22
    cv.ellipse(lamp_x - 16, top_y + 1, 33, front_top - top_y - 1, C("#f6cf7a", 0.14))
    book_stack(cv, ox + 44, front_top - 1, 16, n=3, seed=seed + 1)
    book_stack(cv, ox + 64, front_top - 1, 13, n=2, seed=seed + 2)
    cv.rect(ox + width - 64, top_y + 3, 12, 5, OUT); cv.rect(ox + width - 63, top_y + 4, 10, 3, "#7e3a30")
    cv.rect(ox + width - 48, top_y + 1, 4, 6, OUT); cv.rect(ox + width - 47, top_y + 2, 2, 4, OAK[2]); cv.rect(ox + width - 49, top_y + 6, 6, 2, IRON[2])
    cv.rect(ox + width - 38, top_y - 4, 14, 10, OUT); cv.rect(ox + width - 37, top_y - 3, 12, 8, OAK[3]); cv.hline(ox + width - 37, top_y - 3, 12, OAK[5])
    for k in range(4):
        cv.vline(ox + width - 35 + k * 3, top_y - 6, 3, PAGE[3] if k % 2 else PAGE[2])
    cv.ellipse(ox + width - 18, top_y + 1, 7, 5, OUT); cv.ellipse(ox + width - 17, top_y + 1, 5, 4, BRASS[3]); cv.px(ox + width - 15, top_y, BRASS[4])
    cv.rect(ox + width // 2 - 9, top_y + 3, 18, 6, PAGE[3]); cv.hline(ox + width // 2 - 7, top_y + 5, 12, PAGE[0]); cv.hline(ox + width // 2 - 7, top_y + 7, 9, PAGE[0])
    banker_lamp(cv, lamp_x, top_y + 6)
    return cv, ox + width // 2, base


def regulator_clock(cv, cx, top, case_h=44, w=26, hour=11, minute=56):
    """A wall regulator clock: oak case with a crown, a cream dial, a glazed door below with the
    pendulum pivot (the swinging rod and bob are animated layers; see pendulum_frames)."""
    cv.rect(cx - w // 2 - 2, top - 4, w + 4, 4, OAK[4]); cv.hline(cx - w // 2 - 2, top - 4, w + 4, OAK[5])
    cv.poly([(cx - 6, top - 4), (cx, top - 9), (cx + 6, top - 4)], OAK[3])
    cv.rect(cx - w // 2 - 1, top - 1, w + 2, case_h + 2, OUT)
    cv.rect(cx - w // 2, top, w, case_h, OAK[3]); cv.vline(cx - w // 2, top, case_h, OAK[5]); cv.vline(cx + w // 2 - 1, top, case_h, OAK[1])
    r = w // 2 - 3
    wall_clock_big(cv, cx, top + r + 3, r=r, hour=hour, minute=minute)
    gy0 = top + 2 * r + 9
    cv.rect(cx - w // 2 + 3, gy0, w - 6, top + case_h - 3 - gy0, "#1e1418")
    cv.rect(cx - w // 2 + 4, gy0 + 1, w - 8, top + case_h - 5 - gy0, "#2a2024")
    cv.line(cx - w // 2 + 5, top + case_h - 6, cx - w // 2 + 9, gy0 + 3, C("#8a96c8", 0.35))
    cv.rect(cx - 1, gy0 + 1, 3, 2, BRASS[3])
    cv.poly([(cx - w // 2 - 1, top + case_h), (cx + w // 2, top + case_h), (cx + 3, top + case_h + 5), (cx - 3, top + case_h + 5)], OAK[2])
    return (cx, gy0 + 2, top + case_h - 6)


def pendulum_frames(length, swing=3):
    """Three small RGBA frames of a pendulum (rod and brass bob) leaning left, upright, right.
    Each frame is (canvas, ox) with the pivot at (ox, 0)."""
    frames = []
    for lean in (-swing, 0, swing):
        w = 2 * swing + 9
        cv = Canvas(w, length + 4)
        ox = w // 2
        cv.line(ox, 0, ox + lean, length - 3, BRASS[2])
        cv.ellipse(ox + lean - 3, length - 4, 7, 7, OUT)
        cv.ellipse(ox + lean - 2, length - 3, 5, 5, BRASS[3]); cv.px(ox + lean - 1, length - 2, BRASS[4])
        frames.append((cv, ox))
    return frames


def moon_patch(cv, x, y, w, h, slant=14, color="#b4c4f0", strength=0.12):
    """Cool moonlight thrown on the floor by a tall window: a slanted, stepped parallelogram."""
    for i, f in enumerate((1.0, 0.75, 0.5)):
        a = strength * (0.5 + 0.5 * i / 2)
        ww, hh = int(w * f), int(h * f)
        x0 = x + (w - ww) // 2
        y0 = y + (h - hh) // 2
        cv.poly([(x0, y0), (x0 + ww, y0), (x0 + ww + slant * f, y0 + hh), (x0 + slant * f, y0 + hh)], C(color, a / 2))


def card_catalogue(cv, x, base, w=40, h=34, seed=0):
    """Oak card-catalogue cabinet against a wall: rows of small drawers with brass pulls and labels."""
    rng = _rng(seed)
    top = base - h
    cv.rect(x - 1, top - 1, w + 2, h + 1, OUT)
    cv.rect(x, top, w, h, OAK[3]); cv.rect(x, top, w, 3, OAK[4]); cv.hline(x, top, w, OAK[5])
    cv.rect(x, base - 5, w, 5, OAK[1]); cv.hline(x, base - 5, w, OAK[2])
    dw, dh = 8, 5
    for yy in range(top + 4, base - 6, dh + 1):
        for xx in range(x + 2, x + w - dw, dw + 1):
            cv.rect(xx, yy, dw, dh, OAK[2]); cv.hline(xx, yy, dw, OAK[4])
            cv.rect(xx + 2, yy + 1, 4, 2, PAGE[2] if rng.random() < 0.85 else PAGE[3])
            cv.px(xx + 3, yy + 3, BRASS[3]); cv.px(xx + 4, yy + 3, BRASS[2])
    if rng.random() < 2:
        # one drawer pulled out
        xx, yy = x + 2 + (dw + 1) * 2, top + 4 + (dh + 1) * 2
        cv.rect(xx - 1, yy + 1, dw + 2, dh + 2, OUT); cv.rect(xx, yy + 2, dw, dh, OAK[4])
        for k in range(3):
            cv.hline(xx + 1, yy + 2 + k, dw - 2, PAGE[3] if k % 2 == 0 else PAGE[1])


def notice_stand(width=66, height=48, label="NOTICE", seed=0, body=None, board=OAK):
    """A free-standing oak notice board on two feet: header plate with the label, a paper sheet.
    body(cv, x, y, w, h) paints the sheet's contents; otherwise ruled lines."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 - 4, 2)
    # feet and posts
    for px_ in (ox + 6, ox + width - 10):
        cv.rect(px_, base - 12, 4, 12, OUT); cv.vline(px_ + 1, base - 12, 11, board[3]); cv.vline(px_ + 2, base - 12, 11, board[2])
        cv.rect(px_ - 3, base - 2, 10, 2, OUT); cv.hline(px_ - 2, base - 2, 8, board[3])
    top = base - height
    cv.rect(ox, top, width, height - 10, OUT)
    cv.rect(ox + 1, top + 1, width - 2, height - 12, board[3]); cv.hline(ox + 1, top + 1, width - 2, board[5])
    cv.vline(ox + 1, top + 1, height - 12, board[4]); cv.vline(ox + width - 2, top + 1, height - 12, board[1])
    # header plate
    tw = text_width(label)
    hx = ox + width // 2 - tw // 2 - 3
    cv.rect(hx, top + 3, tw + 6, 11, "#1f1a2a"); cv.hline(hx, top + 3, tw + 6, BRASS[3]); cv.hline(hx, top + 13, tw + 6, BRASS[1])
    text(cv, label, hx + 3, top + 4, GILT)
    sx, sy, sw, sh = ox + 6, top + 16, width - 12, height - 30
    cv.rect(sx + 1, sy + 1, sw, sh, C("#0d0b16", 0.4))
    cv.rect(sx, sy, sw, sh, PAGE[3]); cv.hline(sx, sy, sw, "#fff8e6")
    if body:
        body(cv, sx, sy, sw, sh)
    else:
        for ly in range(sy + 3, sy + sh - 2, 3):
            cv.hline(sx + 3, ly, sw - 8, PAGE[0])
    cv.px(sx + sw // 2, sy + 1, "#c84a3c")
    return cv, ox + width // 2, base


def urn_plant(width=56, height=44, seed=0):
    """A fern in a glazed teal urn: arching fronds made of paired leaflets, lighter on top."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 3, 2)
    cx = ox + width // 2
    pot_h, pot_w = 16, 22
    mouth = base - pot_h
    fronds = []
    for i in range(18):
        ang = np.pi * (0.06 + 0.88 * (i + rng.uniform(-0.35, 0.35)) / 17)
        length = rng.uniform(height * 0.5, height * 0.85) * (1.0 if abs(ang - np.pi / 2) > 0.5 else 0.8)
        fronds.append((np.sin(ang), ang, length))
    fronds.sort()                      # draw the low, sideways fronds first
    for _, ang, length in fronds:
        droop = rng.uniform(0.45, 0.9)
        n = int(length)
        prev = None
        for k in range(n):
            t = k / max(1, n - 1)
            px_ = cx - np.cos(ang) * length * t * 0.95
            py_ = mouth + 1 - np.sin(ang) * length * t * 0.8 + droop * length * 0.5 * t * t
            ix, iy = int(round(px_)), int(round(py_))
            cv.px(ix, iy, LEAF[1])
            if 1 < k < n - 1 and k % 2 == 0:
                leaf_len = max(1, int(3 * (1 - abs(t - 0.45) * 1.4)))
                upper = LEAF[4] if t < 0.7 else LEAF[3]
                for s in range(1, leaf_len + 1):
                    cv.px(ix - s, iy - s // 2 - 1, upper)
                    cv.px(ix + s, iy - s // 2 - 1, LEAF[3] if s < leaf_len else LEAF[2])
                cv.px(ix, iy - 1, LEAF[5] if t < 0.4 else upper)
    px0 = cx - pot_w // 2
    cv.poly([(px0 - 1, mouth - 1), (px0 + pot_w, mouth - 1), (px0 + pot_w - 4, base), (px0 + 3, base)], OUT)
    cv.poly([(px0, mouth), (px0 + pot_w - 1, mouth), (px0 + pot_w - 5, base - 1), (px0 + 4, base - 1)], "#2a5a5a")
    cv.poly([(px0 + 2, mouth + 1), (px0 + 8, mouth + 1), (px0 + 8, base - 2), (px0 + 5, base - 2)], "#3e7a74")
    cv.rect(px0 - 2, mouth - 2, pot_w + 4, 4, OUT); cv.rect(px0 - 1, mouth - 1, pot_w + 2, 2, "#3e7a74"); cv.hline(px0 - 1, mouth - 1, pot_w + 2, "#6aa89a")
    cv.vline(px0 + 4, mouth + 3, pot_h - 6, "#6aa89a")
    cv.hline(px0 + 2, mouth + 7, pot_w - 4, GILT); cv.hline(px0 + 3, mouth + 8, pot_w - 6, BRASS[1])
    cv.rect(px0 + 3, base - 2, pot_w - 6, 2, "#1e3a3c")
    return cv, cx, base


def wall_clock_big(cv, cx, cy, r=13, hour=11, minute=56, case=OAK):
    """A large wall clock: oak bezel, cream face, hour ticks, roman-ish marks, hands at hour:minute."""
    cv.ellipse(cx - r - 3, cy - r - 3, r * 2 + 7, r * 2 + 7, OUT)
    cv.ellipse(cx - r - 2, cy - r - 2, r * 2 + 5, r * 2 + 5, case[3])
    cv.ellipse(cx - r - 2, cy - r - 2, r * 2 + 4, r * 2 + 3, case[4])
    cv.ellipse(cx - r, cy - r, r * 2 + 1, r * 2 + 1, "#e6d6b1")
    cv.ellipse(cx - r + 2, cy - r + 1, r * 2 - 3, r * 2 - 4, "#efe4c4")
    for k in range(12):
        a = k / 12 * 2 * np.pi
        x1, y1 = cx + np.sin(a) * (r - 1), cy - np.cos(a) * (r - 1)
        x2, y2 = cx + np.sin(a) * (r - (4 if k % 3 == 0 else 2)), cy - np.cos(a) * (r - (4 if k % 3 == 0 else 2))
        cv.line(int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2)), "#4a3a34")
    ha = ((hour % 12) + minute / 60) / 12 * 2 * np.pi
    ma = minute / 60 * 2 * np.pi
    cv.line(cx, cy, int(round(cx + np.sin(ha) * r * 0.5)), int(round(cy - np.cos(ha) * r * 0.5)), "#1a1424")
    cv.line(cx, cy, int(round(cx + np.sin(ma) * r * 0.8)), int(round(cy - np.cos(ma) * r * 0.8)), "#1a1424")
    cv.rect(cx - 1, cy - 1, 2, 2, BRASS[3])


def wall_speaker(cv, x, y, w=16, h=20):
    """An old public-address loudspeaker cabinet on a wall bracket: oak case with a rounded top,
    a cloth grille behind a sunburst fret, a brass badge. (x, y) is its top-left."""
    cv.rect(x + w // 2 - 1, y - 6, 3, 6, IRON[2]); cv.hline(x + w // 2 - 3, y - 6, 7, IRON[1])
    cv.rect(x - 1, y + 2, w + 2, h - 1, OUT)
    cv.ellipse(x - 1, y - 1, w + 2, 8, OUT)
    cv.ellipse(x, y, w, 6, OAK[4]); cv.rect(x, y + 3, w, h - 3, OAK[3])
    cv.vline(x, y + 3, h - 3, OAK[5]); cv.vline(x + w - 1, y + 3, h - 3, OAK[1])
    gx, gy, gw, gh = x + 3, y + 4, w - 6, h - 9
    cv.rect(gx, gy, gw, gh, "#6a5038")
    for k in range(gy, gy + gh, 2):
        cv.hline(gx, k, gw, "#5a4230")
    cx, cy = gx + gw // 2, gy + gh - 1
    for a in np.linspace(np.pi * 1.08, np.pi * 1.92, 5):
        cv.line(cx, cy, int(round(cx + np.cos(a) * gw * 0.6)), int(round(cy + np.sin(a) * gh)), OAK[2])
    cv.rect(x + 1, y + h - 4, w - 2, 3, OAK[2]); cv.hline(x + 1, y + h - 4, w - 2, OAK[4])
    cv.rect(x + w // 2 - 2, y + h - 4, 4, 2, BRASS[3])


# --- reading room ----------------------------------------------------------------------------
def built_in_shelves(cv, x, top, w, base, seed=0, shelf=20, crown=True, ladder_x=None, dim=0.0):
    """Floor-to-cornice shelving built into a wall (top to base): a carved cornice, bays of books,
    a plinth at the floor and, optionally, a rolling ladder at ladder_x."""
    if crown:
        cv.rect(x - 4, top - 7, w + 8, 7, OUT)
        cv.rect(x - 3, top - 6, w + 6, 5, OAK[3]); cv.hline(x - 3, top - 6, w + 6, OAK[5]); cv.hline(x - 3, top - 3, w + 6, OAK[2])
        for dx in range(x - 1, x + w + 2, 4):
            cv.px(dx, top - 2, OAK[1])
    plinth = 8
    inner = base - plinth - top
    n = max(1, int(round(inner / shelf)))
    wall_shelves(cv, x, top, w, inner, seed=seed, shelf=inner // n, dim=dim, frame=True)
    cv.rect(x - 3, base - plinth, w + 6, plinth, OAK[2]); cv.hline(x - 3, base - plinth, w + 6, OAK[4])
    cv.hline(x - 3, base - 2, w + 6, OAK[1])
    for px_ in range(x + 2, x + w - 6, 14):
        cv.rect(px_, base - plinth + 3, 9, 2, OAK[1])
    if ladder_x is not None:
        library_ladder(cv, ladder_x, top - 2, base)


def window_seat(cv, x, y, w, h=10, cushion="#2a4434"):
    """A built-in oak window seat under a tall window: cushion on top, panelled front."""
    cv.rect(x - 1, y - 1, w + 2, h + 1, OUT)
    cv.rect(x, y, w, 4, cushion); cv.hline(x, y, w, shade(cushion, 0.3)); cv.hline(x, y + 3, w, shade(cushion, -0.3))
    for bx in range(x + 6, x + w - 3, 10):
        cv.px(bx, y + 1, shade(cushion, -0.35))
    cv.rect(x, y + 4, w, h - 4, OAK[3]); cv.hline(x, y + 4, w, OAK[5])
    for px_ in range(x + 2, x + w - 6, 12):
        cv.rect(px_, y + 6, 9, h - 8, OAK[2])


def _garden_glass(cv, x, y, w, h, seed=0, arch_r=0):
    """The margin garden at night seen through glass: indigo sky, layered hedge and fern masses,
    a warm lantern far off, a pale path running away. Returns the glass mask."""
    rng = _rng(seed)
    top = y - arch_r
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    glass = (xs >= x) & (xs < x + w) & (ys >= y) & (ys < y + h)
    if arch_r:
        glass |= ((xs - (x + w / 2 - 0.5)) ** 2 + (ys - y + 0.5) ** 2 <= arch_r * arch_r) & (ys < y) & (ys >= top)
    for yy in range(top, y + h):
        t = (yy - top) / max(1, y + h - top)
        c = NIGHT_N[1] if t < 0.25 else NIGHT_N[2] if t < 0.45 else "#1a2a26" if t < 0.7 else "#203226"
        cv.a[yy][glass[yy]] = C(c)
    hz = top + int((y + h - top) * 0.45)
    for bx in range(x - 2, x + w + 2, 4):
        bh = int(rng.integers(4, 10))
        for yy in range(hz - bh, hz + 3):
            for xx in range(bx, bx + 5):
                if 0 <= yy < cv.h and 0 <= xx < cv.w and glass[yy, xx]:
                    cv.px(xx, yy, "#16261c")
    lx = x + int(w * 0.68)
    for r, a in [(6, 0.18), (3, 0.3)]:
        cv.ellipse(lx - r, hz - 4 - r, 2 * r + 1, 2 * r + 1, C("#f6cf7a", a))
    cv.rect(lx, hz - 5, 2, 3, "#fde9b6"); cv.vline(lx, hz - 2, 6, "#0e1612")
    for yy in range(hz + 2, y + h):
        t = (yy - hz) / max(1, y + h - hz)
        half = int(2 + t * w * 0.28)
        cx = x + w // 2 - int(t * 3)
        for xx in range(cx - half, cx + half):
            if glass[yy, xx]:
                cv.px(xx, yy, "#4a4a46" if (yy + xx // 5) % 4 else "#3a3a38")
    for side in (0, 1):
        for k in range(5):
            fx = x + (2 + k * 3 if side == 0 else w - 3 - k * 3)
            fy = y + h - 2 - int(rng.integers(6, 18))
            for d in range(-4, 5):
                yy = fy + abs(d) // 2
                xx = fx + d
                for yk in range(yy, y + h):
                    if 0 <= xx < cv.w and glass[yk, xx]:
                        cv.px(xx, yk, "#24402c" if yk > yy + 1 else "#3a6040")
    for _ in range(w * h // 60):
        sx, sy = x + int(rng.integers(0, w)), top + int(rng.integers(0, max(1, hz - top - 4)))
        if glass[sy, sx]:
            cv.px(sx, sy, "#8a96c8")
    return glass


def garden_door(cv, cx, bottom, w=40, h=72, seed=0, label=None):
    """A pair of glazed oak doors under a round stone arch, the night garden showing through the
    small panes, brass handles, a worn stone sill. (cx, bottom) is the threshold."""
    r = w // 2
    x, top = cx - r, bottom - h
    rect_top = top + r
    cv.ellipse(x - 7, top - 7, w + 14, w + 14, STONE_N[2]); cv.rect(x - 7, rect_top, w + 14, h - r, STONE_N[2])
    cv.ellipse(x - 6, top - 6, w + 12, w + 12, STONE_N[4]); cv.rect(x - 6, rect_top, w + 12, h - r, STONE_N[4])
    cv.ellipse(x - 3, top - 3, w + 6, w + 6, STONE_N[1]); cv.rect(x - 3, rect_top, w + 6, h - r, STONE_N[1])
    cv.rect(x - 3, rect_top, 3, h - r, STONE_N[3])
    cv.rect(cx - 3, top - 8, 7, 6, STONE_N[5]); cv.hline(cx - 3, top - 8, 7, STONE_N[6])
    for k, qy in enumerate(range(rect_top + 2, bottom - 4, 9)):
        qw = 5 if k % 2 == 0 else 3
        cv.rect(x - 7 - qw, qy, qw, 8, STONE_N[3]); cv.hline(x - 7 - qw, qy, qw, STONE_N[5])
        cv.rect(x + w + 7, qy, qw, 8, STONE_N[2]); cv.hline(x + w + 7, qy, qw, STONE_N[4])
    cv.ellipse(x - 1, top - 1, w + 2, w + 2, OAK[1]); cv.rect(x - 1, rect_top, w + 2, h - r, OAK[1])
    glass = _garden_glass(cv, x + 2, rect_top, w - 4, h - r - 10, seed=seed, arch_r=r - 2)
    cv.rect(x, bottom - 12, w, 12, OAK[3]); cv.hline(x, bottom - 12, w, OAK[5])
    cv.rect(x + 3, bottom - 9, r - 6, 6, OAK[2]); cv.rect(cx + 3, bottom - 9, r - 6, 6, OAK[2])
    bars = np.zeros_like(glass)
    bars[:, x + 7:x + w - 2:6] = True
    bars[rect_top + 6:bottom - 12:8, :] = True
    bars[:rect_top, :] = False
    bars[:rect_top, cx - 1] = True
    cv.a[bars & glass] = C(OAK[2])
    cv.rect(x, rect_top - 1, w, 2, OAK[3]); cv.hline(x, rect_top - 1, w, OAK[4])
    cv.vline(cx - 1, top, h, OAK[3]); cv.vline(cx, top, h, OAK[1])
    for hx in (cx - 4, cx + 3):
        cv.rect(hx, bottom - 30, 2, 5, BRASS[3]); cv.px(hx, bottom - 30, BRASS[4])
    cv.line(x + 3, bottom - 16, x + 9, bottom - 30, C("#8a96c8", 0.35))
    cv.rect(x - 8, bottom - 2, w + 16, 2, STONE_N[5]); cv.hline(x - 8, bottom - 2, w + 16, STONE_N[6])
    if label:
        lw = text_width(label) + 8
        plaque(cv, cx - lw // 2, top - 24, label)


def reel_deck(cv, x, y):
    """A reel-to-reel tape recorder on a table, (x, y) its front-left foot: grey case seen from
    above, two reels with brown tape, chunky keys on the front, an amber level meter."""
    cv.rect(x - 1, y - 15, 36, 16, OUT)
    cv.rect(x, y - 14, 34, 10, "#6a6470"); cv.hline(x, y - 14, 34, "#8a8494")
    cv.rect(x, y - 4, 34, 4, "#4a4652"); cv.hline(x, y - 4, 34, "#5e5a68")
    for k in range(5):
        cv.rect(x + 3 + k * 4, y - 3, 3, 2, "#c8c0b4" if k != 2 else "#c84a3c")
    cv.rect(x + 24, y - 3, 8, 2, "#e9a84a")
    for rx in (x + 8, x + 26):
        cv.ellipse(rx - 6, y - 21, 13, 8, OUT)
        cv.ellipse(rx - 5, y - 20, 11, 6, "#5a3a28")
        cv.ellipse(rx - 2, y - 18, 5, 3, "#b8b0a8"); cv.px(rx, y - 17, OUT)
    cv.line(x + 8, y - 13, x + 26, y - 13, "#5a3a28")
    cv.rect(x + 14, y - 12, 6, 3, "#2a2a30")


def headphones(cv, x, y, band="#2a2830", cup="#4a4652", cord_to=None):
    """A pair of headphones lying on a table: arched band, two round cups; optional cord."""
    for k in range(15):
        a = np.pi + np.pi * k / 14
        px_, py_ = int(round(x + 6 + np.cos(a) * 7)), int(round(y - 1 + np.sin(a) * 5))
        cv.rect(px_, py_ - 1, 2, 2, OUT); cv.px(px_, py_, band)
    for cxx in (x, x + 10):
        cv.rect(cxx - 1, y - 3, 6, 5, OUT); cv.rect(cxx, y - 2, 4, 3, cup); cv.hline(cxx, y - 2, 4, shade(cup, 0.3))
    if cord_to:
        cv.line(x + 12, y + 1, cord_to[0], cord_to[1], "#1a1820")


def bookmark_card(cv, x, y, label="NEXT", ink="#2a3a6a", paper=None):
    """A cream bookmark card lying on a table with a red ribbon tassel: one printed word and a
    blank ruled line waiting to be written on. Returns its width."""
    paper = paper or PAGE[2]
    w = text_width(label) + 8
    cv.rect(x - 1, y - 1, w + 2, 15, OUT)
    cv.rect(x, y, w, 13, paper); cv.hline(x, y + 12, w, PAGE[1])
    text(cv, label, x + 4, y, ink)
    cv.hline(x + 3, y + 10, w - 6, PAGE[0])
    cv.px(x + w, y + 2, "#c84a3c"); cv.line(x + w + 1, y + 3, x + w + 4, y + 9, "#c84a3c"); cv.rect(x + w + 3, y + 9, 3, 3, "#a83a32")
    return w


def marked_bookcase(width=100, height=100, seed=0, inks=("#2c3f6e", "#a83a32")):
    """A bookcase whose middle shelf holds a large open book on a slanted rest, its pages written
    over by two hands in two inks (blue and red), a ribbon hanging down. Prop (anchor bottom-centre)."""
    cv, ax, ay = bookcase(width, height, seed=seed)
    ox = 4
    top = ay - height
    cx = ox + width // 2
    yb = top + int(height * 0.55)
    cv.rect(cx - 24, yb - 3, 48, 5, OUT)
    cv.rect(cx - 23, yb - 2, 46, 3, OAK[4]); cv.hline(cx - 23, yb - 2, 46, OAK[5])
    bw, bh = 40, 15
    bx, by = cx - bw // 2, yb - 3 - bh
    cv.rect(bx - 2, by - 1, bw + 4, bh + 2, OUT)
    cv.rect(bx - 1, by, bw + 2, bh, "#5a2a26")
    cv.rect(bx, by, bw, bh - 1, PAGE[3]); cv.hline(bx, by + bh - 2, bw, PAGE[1])
    cv.vline(bx + bw // 2, by, bh - 1, PAGE[0]); cv.vline(bx + bw // 2 - 1, by, bh - 1, PAGE[2])
    rng = _rng(seed)
    for i, ly in enumerate(range(by + 2, by + bh - 2, 2)):
        for side in (0, 1):
            lx = bx + 2 + side * (bw // 2 + 1)
            n = int(rng.integers(8, bw // 2 - 3))
            cv.hline(lx, ly, n, inks[0])
            if (i + side) % 2 == 1:
                cv.hline(lx + int(rng.integers(1, 6)), ly + 1, int(rng.integers(3, 8)), inks[1])
    cv.vline(bx + bw - 2, by + 2, 6, inks[1]); cv.vline(bx + 1, by + 6, 4, inks[1])
    cv.vline(bx + bw // 2 + 3, by + bh - 1, 8, "#c84a3c"); cv.px(bx + bw // 2 + 3, by + bh + 7, "#a83a32")
    return cv, ax, ay


MAPLE = ["#2a1014", "#4a1a1c", "#7a2a26", "#a83c32", "#c8582e", "#e08a4a"]
GRASS_PLUME = ["#5e4a34", "#8a7050", "#b49a70", "#d8c094"]


def fountain_grass(cv, cx, base, w=18, h=24, seed=0):
    """An ornamental grass clump: a dense fan of arching blades from one crown, darker inside,
    lighter at the lit edge, buff plumes nodding at the tips."""
    rng = _rng(seed)
    blades = sorted((rng.uniform(-1, 1) for _ in range(30)), key=abs, reverse=True)
    for i, side in enumerate(blades):
        hh = rng.uniform(h * 0.6, h) * (1 - 0.25 * abs(side))
        inner = abs(side) < 0.35
        for k in range(int(hh)):
            t = k / hh
            x = cx + side * w * 0.55 * t ** 1.5
            y = base - hh * np.sin(t * np.pi * 0.6) / np.sin(np.pi * 0.6)
            c = LEAF[2] if inner and t < 0.6 else LEAF[4] if (side < 0 and t > 0.3) else LEAF[3]
            cv.px(int(round(x)), int(round(y)), c)
        if rng.random() < 0.45 and abs(side) > 0.2:
            tx = cx + side * w * 0.55
            ty = base - hh
            for k in range(4):
                c = GRASS_PLUME[3 - min(3, k)]
                cv.px(int(round(tx + side * k * 0.7)), int(round(ty + k)), c)
                cv.px(int(round(tx + side * k * 0.7)) + 1, int(round(ty + k)), shade(c, -0.2))
    cv.rect(cx - 3, base - 1, 7, 2, LEAF[1])


def stone_planter(width=180, height=65, seed=0):
    """A raised sandstone planter for the quad: ashlar face with a limestone cap, a mulched bed
    seen from above, ornamental grasses, shrubs, autumn mums and a small red maple in the middle."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 10, seed=seed)
    ox, base = 4, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.42)
    face_h, bed = 20, 7
    cap_y = base - face_h - 3
    bed_y = cap_y - bed
    # bed (far half) behind the plants: dark mulch with a back cap edge
    cv.rect(ox + 2, bed_y - 2, width - 4, 3, LIME[3]); cv.hline(ox + 2, bed_y - 2, width - 4, LIME[5])
    cv.rect(ox + 2, bed_y + 1, width - 4, bed, "#2a1c18")
    for _ in range(width):
        cv.px(ox + 3 + int(rng.integers(0, width - 6)), bed_y + 1 + int(rng.integers(0, bed)), "#3e2a20" if rng.random() < 0.6 else "#1e1412")
    # plants, back to front
    cx = ox + width // 2
    from midlib import sprite_from_cell
    maple = sprite_from_cell(5, height=height - 14, colors=28, saturation=1.1)
    maple[..., :3] = maple[..., :3] * np.array([1.08, 0.82, 0.78])      # turn the oak's gold toward maple red
    cv.paste(np.clip(maple, 0, 1), cx - maple.shape[1] // 2, cap_y - maple.shape[0] + 4)
    # back row of shrubs either side of the maple, grasses at the ends, mums along the front
    x = ox + 2
    while x < ox + width - 14:
        if abs(x + 12 - cx) < 12:
            x += 6
            continue
        sw, sh = int(rng.integers(22, 30)), int(rng.integers(17, 25))
        cv.paste(shrub(0, 0, sw, sh, seed=seed + x), x - 2, cap_y - sh + 1)
        x += sw - 7
    for gx in (ox + 14, ox + width - 14):
        fountain_grass(cv, gx, cap_y + 1, w=24, h=30, seed=seed + gx)
    x = ox + 6
    k = 0
    while x < ox + width - 10:
        sw, sh = int(rng.integers(12, 17)), int(rng.integers(8, 12))
        col = [MUM[k % 3], MUM[(k + 1) % 3], MUM[3]]
        cv.paste(shrub(0, 0, sw, sh, seed=seed + 300 + x, flowers=col, density=1.3), x - 2, cap_y - sh + 3)
        x += sw - 1
        k += 1
    # front cap and ashlar face
    cv.rect(ox, cap_y - 1, width, face_h + 4, OUT)
    from surfaces import ashlar_wall
    ashlar_wall(cv, ox + 1, cap_y + 3, width - 2, face_h, [STONE_N[0], STONE_N[1], STONE_N[2], STONE_N[3], STONE_N[4], STONE_N[5]], course=5, seed=seed, cap=False)
    cv.rect(ox - 1, cap_y - 1, width + 2, 4, LIME[3]); cv.hline(ox - 1, cap_y - 1, width + 2, LIME[5]); cv.hline(ox - 1, cap_y + 2, width + 2, LIME[1])
    cv.hline(ox + 1, base - 2, width - 2, C("#0d0b16", 0.5))
    return cv, cx, base


def quad_bench(width=150, height=32, seed=0):
    """A long quad bench: sandstone pedestals, oak seat slats seen from above, a slatted back on
    iron standards, a small brass memorial plaque in the middle of the back rail."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2, 2, alpha=0.4)
    seat = base - 13
    # back rest: two slats on iron standards
    for sx in (ox + 12, ox + width // 2, ox + width - 13):
        cv.rect(sx - 1, base - height + 2, 3, height - 12, OUT); cv.vline(sx, base - height + 2, height - 13, IRON[3])
    for i, by in enumerate((base - height + 2, base - height + 8)):
        cv.rect(ox + 4, by, width - 8, 5, OUT)
        cv.rect(ox + 5, by + 1, width - 10, 3, OAK[4 if i == 0 else 3]); cv.hline(ox + 5, by + 1, width - 10, OAK[5])
        for gx in range(ox + 10, ox + width - 10, 13):
            cv.hline(gx, by + 2, 4, OAK[2])
    cv.rect(ox + width // 2 - 6, base - height + 3, 12, 3, BRASS[3]); cv.hline(ox + width // 2 - 5, base - height + 4, 10, BRASS[1])
    # seat slats seen from above
    cv.rect(ox, seat - 6, width, 9, OUT)
    for k, sy in enumerate((seat - 5, seat - 3, seat - 1)):
        cv.rect(ox + 1, sy, width - 2, 2, OAK[4] if k != 1 else OAK[3]); cv.hline(ox + 1, sy, width - 2, OAK[5] if k == 0 else OAK[4])
    cv.rect(ox + 1, seat + 1, width - 2, 2, OAK[2]); cv.hline(ox + 1, seat + 2, width - 2, OAK[1])
    # sandstone pedestals
    for px_ in (ox + 4, ox + width // 2 - 6, ox + width - 16):
        cv.rect(px_, seat + 3, 12, base - seat - 3, OUT)
        cv.rect(px_ + 1, seat + 3, 10, base - seat - 4, STONE_N[3]); cv.vline(px_ + 1, seat + 3, base - seat - 4, STONE_N[5])
        cv.vline(px_ + 10, seat + 3, base - seat - 4, STONE_N[1]); cv.hline(px_ + 1, seat + 3, 10, STONE_N[1])
    return cv, ox + width // 2, base


def loose_page(cv, x, y, seed=0, w=7, h=5):
    """A fallen sheet of paper lying flat (on steps or grass), a couple of ruled lines, a curl."""
    rng = _rng(seed)
    cv.rect(x + 1, y + 1, w, h, C("#0d0b16", 0.35))
    cv.rect(x, y, w, h, PAGE[3]); cv.hline(x, y, w, "#fff8e6")
    for ly in range(y + 1, y + h - 1, 2):
        cv.hline(x + 1, ly, int(rng.integers(2, w - 1)), PAGE[0])
    cv.px(x + w - 1, y, PAGE[1])


def iron_gate(cv, x, base, w=44, h=34, open_frac=0.6):
    """A pair of wrought-iron gate leaves between two stone piers, swung partly open."""
    for gx in (x - 8, x + w):
        cv.rect(gx, base - h - 6, 8, h + 6, STONE_N[3]); cv.vline(gx, base - h - 6, h + 6, STONE_N[5]); cv.vline(gx + 7, base - h - 6, h + 6, STONE_N[1])
        cv.rect(gx - 1, base - h - 9, 10, 4, LIME[3]); cv.hline(gx - 1, base - h - 9, 10, LIME[5])
        cv.ellipse(gx + 1, base - h - 14, 6, 6, LIME[2]); cv.px(gx + 3, base - h - 13, LIME[4])
    leaf = int(w / 2 * (1 - open_frac))
    for side in (0, 1):
        lx = x if side == 0 else x + w - leaf
        cv.rect(lx, base - h, max(2, leaf), 2, IRON[2]); cv.rect(lx, base - 4, max(2, leaf), 2, IRON[2])
        for bx in range(lx, lx + max(2, leaf), 3):
            cv.vline(bx, base - h, h - 2, IRON[1]); cv.px(bx, base - h - 1, IRON[3])


def book_drop(cv, x, base, w=20, h=28):
    """A blue steel book-return drop box against a wall: domed lid, pull slot, open-book decal."""
    top = base - h
    cv.rect(x - 1, top + 3, w + 2, h - 3, OUT)
    cv.ellipse(x - 1, top - 1, w + 2, 10, OUT); cv.ellipse(x, top, w, 8, "#3a4f8a"); cv.hline(x + 3, top + 1, w - 6, "#5671b0")
    cv.rect(x, top + 4, w, h - 6, "#2c3f6e"); cv.vline(x, top + 4, h - 6, "#425da6"); cv.vline(x + w - 1, top + 4, h - 6, "#1b2140")
    cv.rect(x + 3, top + 6, w - 6, 3, OUT); cv.hline(x + 4, top + 7, w - 8, IRON[3])
    bx, by = x + w // 2, top + 15
    cv.poly([(bx - 6, by), (bx - 1, by - 1), (bx - 1, by + 4), (bx - 6, by + 5)], PAGE[3])
    cv.poly([(bx + 1, by - 1), (bx + 6, by), (bx + 6, by + 5), (bx + 1, by + 4)], PAGE[2])
    cv.rect(x + 2, base - 4, w - 4, 2, IRON[1])
    cv.rect(x + 1, base - 2, 3, 2, OUT); cv.rect(x + w - 4, base - 2, 3, 2, OUT)


def chalk(cv, x, y, label, color="#e8b4c8"):
    """Chalk writing on paving: the game font in a pale pastel, with a few gaps where it rubbed off."""
    tmp = Canvas(text_width(label) + 2, 10)
    text(tmp, label, 1, 0, color)
    rng = _rng(len(label))
    m = tmp.a[..., 3] > 0
    m &= rng.random(m.shape) > 0.12
    ys, xs = np.where(m)
    for yy, xx in zip(ys, xs):
        cv.px(x + xx, y + yy, C(color, 0.8))


# --- floors -----------------------------------------------------------------------------------
def marble_floor(cv, x, y, w, h, seed=0, size=24, pal=MARBLE, accent=ROSE):
    """Polished stone tiles in a checker of buff and rose, rows a touch deeper toward the viewer,
    faint veining and a sheen line on each tile."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[0])
    yy, row = y, 0
    while yy < y + h:
        th = int(round(size * (0.6 + 0.2 * (yy - y) / max(1, h))))
        th = min(th, y + h - yy)
        for i, xx in enumerate(range(x, x + w, size)):
            x1 = min(x + w, xx + size - 1)
            rose = (i + row) % 2 == 1
            base = accent[3] if rose else pal[3]
            if rng.random() < 0.15:
                base = accent[4] if rose else pal[4]
            cv.rect(xx, yy, x1 - xx, th - 1, base)
            cv.hline(xx, yy, x1 - xx, shade(base, 0.1))
            for _ in range((x1 - xx) * th // 12):
                cv.px(xx + int(rng.integers(0, max(1, x1 - xx))), yy + int(rng.integers(0, max(1, th - 1))),
                      shade(base, float(rng.choice([-0.06, 0.04]))))
            if rng.random() < 0.35:
                vx, vy = xx + int(rng.integers(2, size - 4)), yy + 1
                for _ in range(int(rng.integers(3, th))):
                    cv.px(vx, vy, shade(base, -0.12)); vx += int(rng.integers(-1, 2)); vy += 1
                    if vy >= yy + th - 1:
                        break
            if rng.random() < 0.3:
                cv.line(xx + 3, yy + th - 3, xx + 8, yy + 2, shade(base, 0.14))
        yy += th
        row += 1


def cabochon_floor(cv, x, y, w, h, seed=0, size=24, field=("#5a4034", "#74543f", "#7e5c45", "#88654b", "#926e52"),
                   inset=("#2a2430", "#423a48", "#5a5262"), joint="#563c34", border=None):
    """Polished honey-sandstone tiles laid square, their corners clipped by small dark slate
    diamonds (cabochons) where four tiles meet; rows a little deeper toward the viewer, a lit
    top edge, a faint vein now and then. Optional `border` = (thickness, colour) for a darker
    band framing the field."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, joint)
    yy, rows = y, []
    while yy < y + h:
        th = int(round(size * (0.58 + 0.18 * (yy - y) / max(1, h))))
        th = max(4, min(th, y + h - yy))
        rows.append((yy, th))
        yy += th
    off = (w % size) // 2 - size // 2
    cols = list(range(x + off, x + w, size))
    for (yy, th) in rows:
        for xx in cols:
            x0, x1 = max(x, xx + 1), min(x + w, xx + size)
            if x1 <= x0:
                continue
            tone = field[int(rng.choice([2, 3, 3, 4, 2]))]
            cv.rect(x0, yy + 1, x1 - x0, th - 1, tone)
            cv.hline(x0, yy + 1, x1 - x0, shade(tone, 0.1))
            cv.hline(x0, yy + th - 1, x1 - x0, shade(tone, -0.08))
            for _ in range((x1 - x0) * th // 22):
                cv.px(x0 + int(rng.integers(0, max(1, x1 - x0))), yy + 2 + int(rng.integers(0, max(1, th - 3))),
                      shade(tone, float(rng.choice([-0.05, 0.05]))))
            if rng.random() < 0.22:
                vx, vy = x0 + int(rng.integers(3, max(4, x1 - x0 - 3))), yy + 2
                for _ in range(int(rng.integers(3, th))):
                    cv.px(vx, vy, shade(tone, -0.12)); vx += int(rng.integers(-1, 2)); vy += 1
                    if vy >= yy + th - 1:
                        break
    for (yy, th) in rows[1:]:
        for xx in cols:
            cx, cy = xx, yy
            if x + 3 < cx < x + w - 3 and y + 3 < cy < y + h - 3:
                cv.poly([(cx - 5, cy), (cx, cy - 3), (cx + 5, cy), (cx, cy + 3)], inset[0])
                cv.poly([(cx - 4, cy), (cx, cy - 2), (cx + 4, cy), (cx, cy + 2)], inset[1])
                cv.hline(cx - 2, cy - 1, 3, inset[2])
    if border:
        t, col = border
        cv.rect(x, y, w, t, col); cv.hline(x, y + t, w, shade(col, 0.2))


def floor_inlay(cv, x, y, w, h, t=4, colour="#5a2e2c", line="#c8a070"):
    """A rectangular band of dark red stone let into a floor (a hall's field border), with a thin
    brass-coloured fillet along its inner edge. Flat paint only."""
    for (xx, yy, ww, hh) in [(x, y, w, t), (x, y + h - t, w, t), (x, y, t, h), (x + w - t, y, t, h)]:
        cv.rect(xx, yy, ww, hh, colour)
    cv.hline(x, y, w, shade(colour, 0.18))
    cv.hline(x + t, y + t, w - 2 * t, line); cv.hline(x + t, y + h - t - 1, w - 2 * t, shade(line, -0.25))
    cv.vline(x + t, y + t, h - 2 * t, line); cv.vline(x + w - t - 1, y + t, h - 2 * t, shade(line, -0.15))


def depth_shade(cv, x, y, w, h, steps=3, alpha=0.24, colour="#0d0b16", from_bottom=True):
    """Stepped darkening bands (no smooth gradient) toward the bottom (or top) of a floor area."""
    bh = h // steps
    for i in range(steps):
        if from_bottom:
            yy = y + h - (steps - i) * bh
            cv.rect(x, yy, w, y + h - yy, C(colour, alpha / steps))
        else:
            cv.rect(x, y, w, (steps - i) * bh, C(colour, alpha / steps))


OAK_FLOOR = ["#2c1a1a", "#4a2b24", "#5c3628", "#683e2e", "#724532", "#7c4c36"]   # worn parquet, close tones


def parquet_floor(cv, x, y, w, h, seed=0, pal=OAK_FLOOR, block=20, joint=0.14):
    """Oak parquet in a basket weave (squashed for the floor's perspective): square blocks of
    strips, alternating direction, each block one of a few close tones, soft strip joints, a lit
    edge on each block. Calm enough to sit under props; pass pal=OAK for a brighter, busier floor."""
    rng = _rng(seed)
    bh = block // 2
    cv.rect(x, y, w, h, pal[1])
    for row, by in enumerate(range(y, y + h, bh)):
        for col, bx in enumerate(range(x, x + w, block)):
            tone = pal[int(rng.choice([3, 3, 4, 2, 3]))]
            x1, y1 = min(x + w, bx + block), min(y + h, by + bh)
            cv.rect(bx, by, x1 - bx, y1 - by, tone)
            if (row + col) % 2 == 0:
                for k in range(by + 3, y1 - 1, 3):
                    cv.hline(bx + 1, k, x1 - bx - 1, shade(tone, -joint))
            else:
                for k in range(bx + 5, x1, 5):
                    cv.vline(k, by + 1, y1 - by - 1, shade(tone, -joint))
            cv.hline(bx, by, x1 - bx, shade(tone, 0.08))
            cv.vline(bx, by, y1 - by, shade(tone, -0.25))
        cv.hline(x, by + bh - 1, w, shade(pal[2], -0.2))


def carpet(cv, x, y, w, h, pal=CARPET_PLUM, seed=0, motif=16):
    """A large patterned carpet (squashed by the floor's perspective): dark border band with a
    gold line and a running lozenge, a field of a diamond lattice with gold rosettes at the
    crossings and alternating diamond fills, fringe at the short ends."""
    rng = _rng(seed)
    cv.rect(x - 1, y - 1, w + 2, h + 2, C("#0d0b16", 0.45))
    cv.rect(x, y, w, h, pal[1])
    cv.rect(x + 2, y + 2, w - 4, h - 4, pal[5]); cv.rect(x + 3, y + 3, w - 6, h - 6, pal[1])
    for bx in range(x + 8, x + w - 8, 10):
        for (by, s) in ((y + 6, 1), (y + h - 7, -1)):
            cv.poly([(bx - 3, by), (bx, by - 2), (bx + 3, by), (bx, by + 2)], pal[3]); cv.px(bx, by, pal[6])
    cv.rect(x + 10, y + 10, w - 20, h - 20, pal[5]); cv.rect(x + 11, y + 11, w - 22, h - 22, pal[2])
    fx0, fy0, fx1, fy1 = x + 11, y + 11, x + w - 11, y + h - 11
    half = motif // 2
    ys, xs = np.mgrid[fy0:fy1, fx0:fx1]
    U = (xs - fx0 + half) % motif - half
    V = ((ys - fy0) * 2 + half) % motif - half
    D = np.abs(U) + np.abs(V)
    cell = ((xs - fx0 + half) // motif + ((ys - fy0) * 2 + half) // motif) % 2
    field = np.where(cell[..., None] == 0, np.array(C(pal[2])[:3]), np.array(C(pal[3])[:3]))
    field[D >= half - 1] = np.array(C(pal[4])[:3])
    field[(D <= 1)] = np.array(C(pal[5])[:3])
    field[(D == 0)] = np.array(C(pal[6])[:3])
    inner = (D == half // 2) & (cell == 1)
    field[inner] = np.array(C(pal[1])[:3])
    cv.a[fy0:fy1, fx0:fx1, :3] = field
    cv.a[fy0:fy1, fx0:fx1, 3] = 1
    for fy in range(y, y + h, 2):
        cv.px(x - 2, fy, PAGE[1]); cv.px(x + w + 1, fy, PAGE[1])


def runner_n(cv, x, y, w, h, pal=CARPET_GREEN, vertical=True):
    """A long carpet runner: dark field, gold border lines, a small repeating lozenge."""
    cv.rect(x - 1, y, w + 2, h, C("#0d0b16", 0.4)) if vertical else cv.rect(x, y - 1, w, h + 2, C("#0d0b16", 0.4))
    cv.rect(x, y, w, h, pal[3])
    if vertical:
        cv.vline(x + 2, y, h, pal[5]); cv.vline(x + w - 3, y, h, pal[5])
        cv.rect(x + 4, y, w - 8, h, pal[2])
        for yy in range(y + 4, y + h - 3, 10):
            cx = x + w // 2
            cv.poly([(cx, yy - 3), (cx + 4, yy), (cx, yy + 3), (cx - 4, yy)], pal[4]); cv.px(cx, yy, pal[6])
    else:
        cv.hline(x, y + 2, w, pal[5]); cv.hline(x, y + h - 3, w, pal[5])
        cv.rect(x, y + 4, w, h - 8, pal[2])
        for xx in range(x + 5, x + w - 4, 12):
            cy = y + h // 2
            cv.poly([(xx - 4, cy), (xx, cy - 3), (xx + 4, cy), (xx, cy + 3)], pal[4]); cv.px(xx, cy, pal[6])


def lawn(cv, x, y, w, h, seed=0, pal=GRASS, band=22, mask=None):
    """Mown quad lawn: soft mowing bands, then little blade tufts on a jittered grid (lighter on
    the lit bands), darker hollows and a few clover patches. mask limits where it paints."""
    rng = _rng(seed)
    sub = np.zeros((cv.h, cv.w), bool)
    sub[max(0, y):y + h, max(0, x):x + w] = True
    if mask is not None:
        sub &= mask
    ys, xs = np.where(sub)
    wave = (np.sin(xs / 37.0) * 3 + np.sin(xs / 11.0)).astype(int)
    stripe = ((ys + wave) // band) % 2
    cv.a[ys, xs, :3] = np.where(stripe[:, None] == 0, np.array(C(pal[3])[:3]), np.array(C(pal[2])[:3]))
    cv.a[ys, xs, 3] = 1
    # hollows: small darker blobs
    for _ in range(w * h // 900):
        cx, cy = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        bw, bh = int(rng.integers(5, 12)), int(rng.integers(2, 4))
        for yy in range(cy, cy + bh):
            for xx in range(cx - bw // 2 + (yy - cy), cx + bw // 2 - (yy - cy)):
                if 0 <= xx < cv.w and 0 <= yy < cv.h and sub[yy, xx]:
                    cv.px(xx, yy, shade(cv.a[yy, xx], -0.12))
    # blade tufts: a 3px "v" or a 2px stroke
    for gy in range(y, y + h, 4):
        for gx in range(x + (gy // 4 % 2) * 3, x + w, 6):
            if rng.random() < 0.45:
                continue
            tx, ty = gx + int(rng.integers(0, 4)), gy + int(rng.integers(0, 3))
            if not (0 <= tx < cv.w - 2 and 1 <= ty < cv.h and sub[ty, tx]):
                continue
            lit = stripe[0] if False else (((ty + int(np.sin(tx / 37.0) * 3 + np.sin(tx / 11.0))) // band) % 2 == 0)
            c = pal[5] if lit and rng.random() < 0.55 else pal[4] if lit else pal[3] if rng.random() < 0.6 else pal[1]
            if rng.random() < 0.5:
                cv.px(tx, ty, c); cv.px(tx + 2, ty, c); cv.px(tx + 1, ty + 1 if ty + 1 < cv.h else ty, shade(c, -0.15))
            else:
                cv.px(tx, ty, c); cv.px(tx, ty + 1 if ty + 1 < cv.h else ty, shade(c, -0.18))
    for _ in range(max(1, w * h // 5000)):
        cx, cy = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        for _ in range(7):
            px_, py_ = cx + int(rng.integers(-4, 5)), cy + int(rng.integers(-2, 3))
            if 0 <= px_ < cv.w and 0 <= py_ < cv.h and sub[py_, px_]:
                cv.px(px_, py_, pal[5]); cv.px(px_ + 1, py_, pal[6])


PAVE_N = ["#3a2e32", "#56464a", "#66544f", "#725e57", "#7c675e", "#887266"]     # quad paving (sandstone)
PAVE_RED = ["#36222a", "#55343a", "#683e3e", "#744842", "#80524a", "#8c5c52"]   # red sandstone walk


def paving(cv, mask, pal=PAVE_N, seed=0, row0=7, row1=12, leaves=0.0, moss=0.06):
    """Irregular ashlar paving (surfaces.flagstones) clipped to a mask, rows deepening downward."""
    from surfaces import flagstones
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    tmp = Canvas(x1 - x0, y1 - y0, seed=seed)
    flagstones(tmp, 0, 0, x1 - x0, y1 - y0, pal, seed=seed, row0=row0, row1=row1, leaves=leaves, moss=moss)
    sub = mask[y0:y1, x0:x1]
    cv.a[y0:y1, x0:x1][sub] = tmp.a[sub]


def crazy_paving(cv, mask, pal=PAVE_N, seed=0, cell=(17, 10), moss=0.12, grow=0.5):
    """CU's random flagstone: irregular polygonal sandstone flags (a jittered Voronoi), each its own
    tone, dark joints, a lit upper lip and a shaded lower lip, a few chips and mossy joints.
    Flags grow by `grow` toward the bottom of the mask for a touch of perspective."""
    from scipy.spatial import cKDTree
    rng = _rng(seed)
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pts = []
    yy = float(y0 - cell[1])
    while yy < y1 + cell[1]:
        f = 1 + grow * max(0.0, (yy - y0) / max(1, y1 - y0))
        cw, ch = cell[0] * f, cell[1] * f
        off = rng.uniform(0, cw)
        xx = x0 - cw + off
        while xx < x1 + cw:
            pts.append((xx + rng.uniform(-0.35, 0.35) * cw, (yy + rng.uniform(-0.3, 0.3) * ch) * 1.7))
            xx += cw
        yy += ch
    pts = np.array(pts)
    gy, gx = np.mgrid[y0:y1, x0:x1]
    _, ident = cKDTree(pts).query(np.stack([gx.ravel(), gy.ravel() * 1.7], 1))
    ident = ident.reshape(gy.shape)
    tones = rng.integers(0, 4, len(pts))
    tone_cols = np.array([C(pal[2])[:3], C(pal[3])[:3], C(pal[4])[:3], C(mix(pal[3], pal[5], 0.5))[:3]], np.float32)
    rgb = tone_cols[tones[ident]].copy()
    # per-stone faint mottling
    mott = (rng.random(gy.shape) < 0.07)
    rgb[mott] *= 0.93
    joint = np.zeros(gy.shape, bool)
    joint[:, :-1] |= ident[:, :-1] != ident[:, 1:]
    joint[:-1, :] |= ident[:-1, :] != ident[1:, :]
    lip_top = np.zeros(gy.shape, bool)
    lip_top[1:, :] = (ident[1:, :] != ident[:-1, :])
    lip_bot = np.zeros(gy.shape, bool)
    lip_bot[:-1, :] = (ident[:-1, :] != ident[1:, :])
    lip_bot[:-1, :] &= ~joint[1:, :] | True
    rgb[lip_top & ~joint] = rgb[lip_top & ~joint] * 0.85 + np.array(C(pal[5])[:3]) * 0.15
    below = np.zeros(gy.shape, bool)
    below[:-1, :] = joint[1:, :] & ~joint[:-1, :]
    rgb[below] *= 0.9
    rgb[joint] = np.array(C(pal[1])[:3])
    mossy = joint & (rng.random(gy.shape) < moss) & np.isin(ident, np.where(rng.random(len(pts)) < 0.3)[0])
    rgb[mossy] = np.array(C("#3f5741")[:3])
    sub = mask[y0:y1, x0:x1]
    region = cv.a[y0:y1, x0:x1]
    region[sub, :3] = rgb[sub]
    region[sub, 3] = 1


def book_medallion(cv, cx, cy, r=34, pal=LIME, field=PAVE_RED):
    """An inlaid stone medallion in the paving: rings, rays, and an open book at the centre
    (squashed to the floor's perspective)."""
    sy = 0.42
    def ell(rx, c):
        cv.ellipse(cx - rx, int(cy - rx * sy), rx * 2 + 1, int(rx * 2 * sy) + 1, c)
    ell(r + 2, pal[1]); ell(r, pal[3]); ell(r - 2, field[3]); ell(r - 6, pal[2]); ell(r - 7, field[2])
    for k in range(16):
        a = k / 16 * 2 * np.pi
        x1, y1 = cx + np.cos(a) * (r - 8), cy + np.sin(a) * (r - 8) * sy
        x2, y2 = cx + np.cos(a) * (r * 0.42), cy + np.sin(a) * (r * 0.42) * sy
        cv.line(int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2)), pal[2] if k % 2 else pal[3])
    ell(int(r * 0.42), pal[2]); ell(int(r * 0.42) - 1, field[1])
    # open book: two pages as slanted quads, a spine line
    bw, bh = int(r * 0.32), int(r * 0.32 * sy * 2) + 2
    cv.poly([(cx - bw, cy - bh // 2 + 1), (cx - 1, cy - bh // 2), (cx - 1, cy + bh // 2), (cx - bw, cy + bh // 2 + 1)], pal[4])
    cv.poly([(cx + 1, cy - bh // 2), (cx + bw, cy - bh // 2 + 1), (cx + bw, cy + bh // 2 + 1), (cx + 1, cy + bh // 2)], pal[3])
    cv.vline(cx, cy - bh // 2, bh + 1, pal[1])
    for k in range(-bh // 2 + 2, bh // 2, 2):
        cv.hline(cx - bw + 2, cy + k, bw - 4, pal[2]); cv.hline(cx + 3, cy + k, bw - 4, pal[1])


def kerb(cv, mask, light=LIME[3], dark="#2a2026"):
    """A crisp edge where paving meets lawn: a lit limestone line on the paving side, a dark
    line on the lawn side below it."""
    from scipy import ndimage
    inner = mask & ~ndimage.binary_erosion(mask)
    outer = ndimage.binary_dilation(mask) & ~mask
    cv.a[inner] = C(light)
    cv.a[outer] = C(dark)


def tree_pit(cv, cx, cy, rx=20, ry=7):
    """A round iron tree grate set in the paving, soil and leaves showing through."""
    cv.ellipse(cx - rx - 2, cy - ry - 2, rx * 2 + 5, ry * 2 + 5, LIME[2])
    cv.ellipse(cx - rx, cy - ry, rx * 2 + 1, ry * 2 + 1, "#241a1a")
    for k in range(-rx + 2, rx - 1, 3):
        h = int(ry * np.sqrt(max(0.0, 1 - (k / rx) ** 2)))
        cv.vline(cx + k, cy - h + 1, h * 2 - 1, IRON[2])
    for r in (rx // 2, rx - 2):
        for a in np.linspace(0, 2 * np.pi, r * 4):
            cv.px(int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r * ry / rx)), IRON[3])


def iron_arch(cv, cx, y, half, label, fg="#e6d6b1"):
    """A wrought-iron arch springing from two pier tops with a small sign hanging from it."""
    pts = [(int(round(cx + half * np.cos(a))), int(round(y - half * 0.45 * np.sin(a)))) for a in np.linspace(0, np.pi, 40)]
    for (x, yy) in pts:
        cv.px(x, yy, IRON[1]); cv.px(x, yy + 1, IRON[2])
    for k in range(-half + 6, half - 5, 6):
        a = np.arccos(k / half)
        top = int(round(y - half * 0.45 * np.sin(a)))
        cv.vline(cx + k, top + 2, max(0, y - top - 1), C(IRON[1], 0.8))
        cv.px(cx + k, top + 2, IRON[3])
    w = text_width(label) + 8
    sy = int(y - half * 0.45) + 6
    cv.vline(cx - w // 2 + 4, sy - 5, 5, IRON[2]); cv.vline(cx + w // 2 - 4, sy - 5, 5, IRON[2])
    cv.rect(cx - w // 2 - 1, sy - 1, w + 2, 13, OUT)
    cv.rect(cx - w // 2, sy, w, 11, "#1f1a2a"); cv.hline(cx - w // 2, sy, w, IRON[3])
    text(cv, label, cx - w // 2 + 4, sy, fg)


def stone_steps(cv, cx, top, w, n, rise=6, spread=3, pal=LIME, worn=True, seed=0):
    """A broad flight of steps seen from the front and above, widening toward the viewer:
    lit nosing, tread, darker riser, a few worn patches in the middle."""
    rng = _rng(seed)
    for i in range(n):
        sw = w + i * spread * 2
        y = top + i * rise
        x0 = cx - sw // 2
        cv.rect(x0, y, sw, rise, pal[2])
        cv.rect(x0, y, sw, rise - 2, pal[3])
        cv.hline(x0, y, sw, pal[5]); cv.hline(x0, y + 1, sw, pal[4])
        cv.hline(x0, y + rise - 2, sw, pal[1]); cv.hline(x0, y + rise - 1, sw, pal[0])
        for jx in range(x0 + int(rng.integers(8, 30)), x0 + sw - 6, int(rng.integers(26, 44))):
            cv.vline(jx, y + 1, rise - 2, pal[2])
        if worn:
            for _ in range(sw // 10):
                wx = cx + int(rng.normal(0, sw / 6))
                cv.px(wx, y + 2 + int(rng.integers(0, max(1, rise - 4))), shade(pal[3], -0.08))
        cv.vline(x0, y, rise, pal[4]); cv.vline(x0 + sw - 1, y, rise, pal[1])


def flag_path(cv, mask, pal=STONE_N, seed=0, row=8):
    """Sandstone flags in running courses filling a mask (paths across a lawn): each flag gets a
    lit top edge, a dark joint and a little speckle; edges of the mask get a crisp border."""
    from scipy import ndimage
    rng = _rng(seed)
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return
    y0, y1 = ys.min(), ys.max() + 1
    x0, x1 = xs.min(), xs.max() + 1
    yy = y0
    while yy < y1:
        rh = row + int(rng.integers(-1, 2)) + (1 if (yy - y0) > (y1 - y0) // 2 else 0)
        xx = x0 - int(rng.integers(0, 18))
        while xx < x1:
            sw = int(rng.integers(int(rh * 1.5), int(rh * 3.2)))
            tone = pal[int(rng.choice([2, 3, 3, 4]))]
            tone = mix(tone, pal[3], 0.35)
            sub = mask[yy:yy + rh, max(0, xx):xx + sw]
            if sub.any():
                cv.a[yy:yy + rh - 1, max(0, xx) + 1:xx + sw][sub[:rh - 1, 1:]] = C(tone)
                top_row = mask[yy, max(0, xx) + 1:xx + sw]
                cv.a[yy, max(0, xx) + 1:xx + sw][top_row] = C(shade(tone, 0.1))
                for _ in range(sw * rh // 12):
                    px_, py_ = xx + int(rng.integers(1, sw)), yy + int(rng.integers(0, max(1, rh - 1)))
                    if 0 <= px_ < cv.w and py_ < cv.h and mask[py_, px_]:
                        cv.px(px_, py_, shade(tone, float(rng.choice([-0.08, -0.04, 0.05]))))
                # joints
                for jy in range(yy, min(cv.h, yy + rh)):
                    if 0 <= xx < cv.w and mask[jy, xx]:
                        cv.px(xx, jy, pal[1])
                jrow = min(cv.h - 1, yy + rh - 1)
                seg = mask[jrow, max(0, xx):xx + sw]
                cv.a[jrow, max(0, xx):xx + sw][seg] = C(pal[1])
            xx += sw
        yy += rh
    edge = mask & ~ndimage.binary_erosion(mask)
    cv.a[edge] = C(pal[1])


# --- facade -----------------------------------------------------------------------------------
def column(cv, cx, base, height, w=18, pal=LIME, capital="ionic", lit_from=-1):
    """A free-standing round column at character scale: square plinth, torus, a shaft with
    cylinder shading and drum joints, an Ionic capital with little volutes, the abacus on top.
    base is the floor row; the column occupies base-height .. base-1."""
    top = base - height
    # plinth and torus
    pw = w + 8
    cv.rect(cx - pw // 2, base - 4, pw, 4, pal[2]); cv.hline(cx - pw // 2, base - 4, pw, pal[4]); cv.hline(cx - pw // 2, base - 1, pw, pal[0])
    tw = w + 4
    cv.rect(cx - tw // 2, base - 7, tw, 3, pal[3]); cv.hline(cx - tw // 2, base - 7, tw, pal[5]); cv.hline(cx - tw // 2 + 1, base - 5, tw - 2, pal[1])
    # shaft
    s_top, s_bot = top + 9, base - 7
    ramp = [pal[5], pal[4], pal[4], pal[3], pal[3], pal[3], pal[2], pal[2], pal[1]]
    for i in range(w):
        t = i / max(1, w - 1)
        if lit_from > 0:
            t = 1 - t
        c = ramp[min(len(ramp) - 1, int(t * len(ramp)))]
        cv.vline(cx - w // 2 + i, s_top, s_bot - s_top, c)
    cv.vline(cx - w // 2 - 1, s_top, s_bot - s_top, OUT if lit_from > 0 else pal[1])
    cv.vline(cx - w // 2 + w, s_top, s_bot - s_top, pal[0] if lit_from < 0 else pal[1])
    # subtle fluting
    for i in range(2, w - 1, 3):
        cv.vline(cx - w // 2 + i, s_top + 3, s_bot - s_top - 6, C("#0d0b16", 0.1))
    for jy in range(s_bot - 22, s_top + 6, -22):
        cv.hline(cx - w // 2, jy, w, C("#0d0b16", 0.12))
    # necking, echinus, volutes, abacus
    cv.rect(cx - w // 2, s_top - 2, w, 2, pal[3]); cv.hline(cx - w // 2, s_top - 2, w, pal[5])
    ew = w + 6
    cv.rect(cx - ew // 2, top + 3, ew, 4, pal[3]); cv.hline(cx - ew // 2, top + 3, ew, pal[5]); cv.hline(cx - ew // 2, top + 6, ew, pal[1])
    if capital == "ionic":
        for side in (-1, 1):
            vx = cx + side * (ew // 2) - (2 if side > 0 else 0)
            cv.rect(vx - 1, top + 3, 4, 5, pal[1]); cv.rect(vx, top + 4, 2, 3, pal[4]); cv.px(vx + (1 if side < 0 else 0), top + 5, pal[0])
    aw = w + 10
    cv.rect(cx - aw // 2, top, aw, 3, pal[4]); cv.hline(cx - aw // 2, top, aw, pal[5]); cv.hline(cx - aw // 2, top + 2, aw, pal[2])


def entablature(cv, x, y, w, h=22, inscription=None, pal=LIME, ink=None):
    """Architrave (two fasciae), a frieze that may carry carved letters, and a dentilled cornice
    with a deep shadow under it. (x, y) is the top of the cornice."""
    # cornice
    cv.rect(x - 4, y, w + 8, 5, pal[3]); cv.hline(x - 4, y, w + 8, pal[5]); cv.hline(x - 4, y + 4, w + 8, pal[1])
    for dx in range(x - 2, x + w + 2, 5):
        cv.rect(dx, y + 5, 3, 2, pal[2]); cv.px(dx + 2, y + 6, pal[0])
    cv.hline(x - 4, y + 7, w + 8, C("#0d0b16", 0.45))
    # frieze
    fy = y + 8
    fh = h - 15
    cv.rect(x, fy, w, fh, pal[3])
    cv.hline(x, fy, w, pal[2])
    rng = _rng(7)
    for _ in range(w * fh // 10):
        cv.px(x + int(rng.integers(0, w)), fy + int(rng.integers(0, fh)), shade(pal[3], float(rng.choice([-0.05, 0.04]))))
    if inscription:
        tw = text_width(inscription)
        tx = x + w // 2 - tw // 2
        ty = fy + (fh - 8) // 2
        text(cv, inscription, tx, ty + 1, pal[4])            # lit lower lip of each carved stroke
        text(cv, inscription, tx, ty, ink or pal[0])
    # architrave
    ay = fy + fh
    cv.rect(x, ay, w, h - 8 - fh, pal[3])
    cv.hline(x, ay, w, pal[5]); cv.hline(x, ay + 3, w, pal[4]); cv.hline(x, ay + h - 9 - fh, w, pal[1])
    cv.hline(x, y + h, w, C("#0d0b16", 0.55))


def bronze_doors(cv, cx, bottom, w=40, h=70, lit=True):
    """Norlin's bronze double doors in a limestone frame: glazed upper panels glowing from the
    lobby, ribbed lower panels, push bars, a hood moulding above."""
    x, top = cx - w // 2, bottom - h
    cv.rect(x - 7, top - 8, w + 14, h + 8, LIME[2])
    cv.vline(x - 7, top - 8, h + 8, LIME[4]); cv.vline(x + w + 6, top - 8, h + 8, LIME[1])
    for yy in range(top - 2, bottom, 9):
        cv.hline(x - 7, yy, 7, LIME[1]); cv.hline(x + w, yy, 7, LIME[1])
    cv.rect(x - 10, top - 13, w + 20, 5, LIME[3]); cv.hline(x - 10, top - 13, w + 20, LIME[5]); cv.hline(x - 10, top - 9, w + 20, LIME[0])
    cv.rect(x - 1, top - 1, w + 2, h + 1, "#1a1210")
    pal = ["#3a2a1c", "#5a4026", "#7a5a30", "#9a7438"]
    for d in (0, 1):
        dx = x + d * (w // 2)
        dw = w // 2 - 1
        cv.rect(dx, top, dw, h, pal[1]); cv.vline(dx, top, h, pal[3]); cv.vline(dx + dw - 1, top, h, pal[0])
        gy0, gy1 = top + 4, top + h * 11 // 20
        cv.rect(dx + 3, gy0, dw - 6, gy1 - gy0, "#1a1210")
        for yy in range(gy0 + 1, gy1 - 1):
            t = (yy - gy0) / max(1, gy1 - gy0)
            c = (GLOW[3] if t < 0.3 else GLOW[2] if t < 0.75 else GLOW[1]) if lit else DARKGLASS[1]
            cv.hline(dx + 4, yy, dw - 8, c)
        cv.vline(dx + dw // 2, gy0, gy1 - gy0, pal[0])
        for k in range(gy0 + 7, gy1 - 2, 8):
            cv.hline(dx + 4, k, dw - 8, pal[0])
        if lit:
            cv.rect(dx + 4, gy0 + 1, 3, 5, GLOW[4])
        for k in range(gy1 + 4, bottom - 4, 4):
            cv.hline(dx + 3, k, dw - 6, pal[2]); cv.hline(dx + 3, k + 1, dw - 6, pal[0])
        cv.rect(dx + 2, gy1 + 1, dw - 4, 2, BRASS[3]); cv.hline(dx + 2, gy1 + 1, dw - 4, BRASS[4])
    cv.rect(x - 2, bottom - 1, w + 4, 2, LIME[3])


def norlin_portico(cv, cx, base, columns=6, spacing=64, col_h=102, col_w=18, inscription=None, seed=0,
                   end_w=66, roof_h=12, lit_windows=(True, True, True, True), door_lit=True):
    """Norlin's west front at character scale, centred on cx with its floor on row `base`:
    a tile roof edge and dentilled cornice at the top, an entablature with a carved inscription,
    a colonnade of `columns` Ionic columns in front of a shadowed recess with tall two-tier
    windows, the bronze doors in the centre bay, and solid sandstone end walls with arched
    windows and lanterns. Returns a dict of useful coordinates (door, lanterns, bays)."""
    rng = _rng(seed)
    span = spacing * (columns - 1)
    px0, px1 = cx - span // 2 - col_w, cx + span // 2 + col_w      # colonnade extent
    x0, x1 = px0 - end_w, px1 + end_w                                # whole front
    ent_h = 24
    ent_top = base - col_h - ent_h
    # roof edge across the top (cropped by the canvas edge)
    roof_top = ent_top - roof_h
    roof_tiles(cv, x0 - 6, max(0, roof_top), x1 - x0 + 12, ent_top - max(0, roof_top) - 2, seed=seed)
    # recess behind the columns: dark sandstone in shadow, deeper toward the top
    stone_wall(cv, px0, ent_top, px1 - px0, base - ent_top, pal=[shade(c, -0.42) for c in STONE_N], seed=seed + 1)
    for i in range(14):
        cv.hline(px0, ent_top + ent_h + i, px1 - px0, C("#0d0b16", 0.4 * (1 - i / 14)))
    # end walls
    for (ex0, ex1, side) in [(x0, px0, -1), (px1, x1, 1)]:
        stone_wall(cv, ex0, ent_top, ex1 - ex0, base - ent_top, seed=seed + (3 if side < 0 else 4))
        quoins(cv, ex0 if side < 0 else ex1, ent_top + ent_h, base - 6, "left" if side < 0 else "right")
        quoins(cv, ex1 if side < 0 else ex0, ent_top + ent_h, base - 6, "right" if side < 0 else "left")
        mx = (ex0 + ex1) // 2
        facade_window(cv, mx - 11, base - 86, 22, 56, seed=seed + 11 + side, lit=True, arch=True, tiers=2)
        cv.rect(ex0, base - 8, ex1 - ex0, 8, LIME[2]); cv.hline(ex0, base - 8, ex1 - ex0, LIME[4]); cv.hline(ex0, base - 1, ex1 - ex0, LIME[0])
    # windows and the door in the bays
    bays = []
    col_xs = [cx - span // 2 + i * spacing for i in range(columns)]
    for i in range(columns - 1):
        bx0, bx1 = col_xs[i] + col_w // 2, col_xs[i + 1] - col_w // 2
        bays.append((bx0, bx1))
    mid = (columns - 1) // 2
    info = {"columns": col_xs, "x0": x0, "x1": x1, "ent_top": ent_top, "lanterns": []}
    wi = 0
    for i, (bx0, bx1) in enumerate(bays):
        bcx = (bx0 + bx1) // 2
        if i == mid and columns % 2 == 0:
            dh = 70
            bronze_doors(cv, bcx, base - 1, 40, dh, lit=door_lit)
            th = max(8, base - dh - 14 - (ent_top + ent_h) - 6)
            facade_window(cv, bcx - 13, ent_top + ent_h + 4, 26, th, seed=seed + 20, lit=True, tiers=1)
            info["door"] = (bcx, base - 1, dh)
        else:
            ww = min(26, bx1 - bx0 - 12)
            facade_window(cv, bcx - ww // 2, base - col_h + 14, ww, col_h - 30, seed=seed + 30 + i,
                          lit=lit_windows[wi % len(lit_windows)], tiers=2)
            wi += 1
    # stylobate
    cv.rect(px0 - 4, base - 4, px1 - px0 + 8, 4, LIME[3]); cv.hline(px0 - 4, base - 4, px1 - px0 + 8, LIME[5]); cv.hline(px0 - 4, base - 1, px1 - px0 + 8, LIME[1])
    # columns cast soft shadows onto the recess (light from the lanterns low and to the left)
    for x in col_xs:
        for k in range(col_w + 6):
            a = 0.32 if k < col_w else 0.32 * (1 - (k - col_w) / 6)
            cv.vline(x + col_w // 2 + 2 + k, ent_top + ent_h, col_h - 6, C("#0d0b16", a))
    # columns, then the entablature over everything
    for i, x in enumerate(col_xs):
        column(cv, x, base - 3, col_h - 3, col_w, capital="ionic", lit_from=-1)
    entablature(cv, x0, ent_top, x1 - x0, ent_h, inscription=inscription)
    # lanterns on the end walls beside the colonnade
    for lx in (px0 - 12, px1 + 12):
        cv.rect(lx - 1, base - 52, 3, 6, FRAME)
        cv.rect(lx - 4, base - 64, 9, 13, FRAME); cv.rect(lx - 3, base - 62, 7, 9, GLOW[3]); cv.rect(lx - 1, base - 61, 3, 5, GLOW[4])
        cv.poly([(lx - 5, base - 63), (lx, base - 68), (lx + 5, base - 63)], FRAME)
        info["lanterns"].append((lx, base - 58))
    return info


# --- battle textures --------------------------------------------------------------------------
def shelf_wall_texture(length, height, seed=0, shelf=22, bay=46, dim=0.0, crown=True):
    """A long wall of oak bookshelves laid out flat (u along the wall), for perspective planes:
    cornice at the top, bays of shelves full of books, a plinth at the floor."""
    cv = Canvas(length, height, seed=seed)
    cv.rect(0, 0, length, height, OAK_DARK[1])
    top = 8 if crown else 0
    if crown:
        cv.rect(0, 0, length, 6, OAK[3]); cv.hline(0, 0, length, OAK[5]); cv.hline(0, 5, length, OAK[1])
        cv.hline(0, 6, length, OAK_DARK[0]); cv.hline(0, 7, length, OAK_DARK[0])
    plinth = 8
    rows = list(range(top + shelf, height - plinth + 1, shelf))
    for bx in range(0, length, bay):
        b1 = min(length, bx + bay - 4)
        prev = top
        for k, sy in enumerate(rows):
            book_row(cv, bx + 1, sy - 2, b1 - bx - 2, shelf - 5, seed=seed * 131 + bx * 3 + k, dim=dim)
            prev = sy
        cv.rect(b1, top, 4, height - top, OAK[3]); cv.vline(b1, top, height - top, OAK[4]); cv.vline(b1 + 3, top, height - top, OAK[1])
    for sy in rows:
        cv.rect(0, sy - 2, length, 2, OAK[3]); cv.hline(0, sy - 2, length, OAK[5])
    cv.rect(0, height - plinth, length, plinth, OAK[2]); cv.hline(0, height - plinth, length, OAK[4])
    return cv.a
