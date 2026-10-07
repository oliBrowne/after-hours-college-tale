"""The Career Center (C03) on the Fountain Court, and its battle backdrop (the career fair in the
UMC ballroom). Builds on c02_lib (the store ceiling, floor margins, doorway, chalkboard a-frame) so
the two shops off the court read as one building.

The Career Center is the court's one modern front: cool grey walls, a navy accent wall with raised
CAREER CENTER letters (the navy-and-white fascia it shows on the court), blue-grey carpet tile, a
LinkedOut kiosk in LinkedOut blue. Sections:
  palettes ........ OFFICE, NAVY, CARPET_O, LINKED, WALNUT, PEAK (the fictional PEAKLINE recruiter)
  walls ........... office_wall, office_ceiling, accent_wall, raised_letters, blinds_window, diploma,
                    framed_photo, job_board, wall_tv (+ tv_slides), brochure_rack, popup_banner, fabric_banner
  floors .......... office_carpet
  props ........... advisor_desk, guest_chair, linkedout_kiosk (+ kiosk_screen), fair_table, beam_seats,
                    water_cooler, snake_plant
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, LEAF, ground_shadow
from lib_eng import micro_text, micro_width
from lib_umc import halo, soft_ellipse
from lib_umc2 import text_mask, paint_mask, CHROME
from lib_oldmain import cork_surface
import c02_lib as S

# --- palettes ---------------------------------------------------------------------------------
OFFICE = ["#34323e", "#4a4856", "#5e5c6a", "#6e6c7a", "#7c7a88", "#8a8896", "#9a98a6"]     # cool grey drywall
NAVY = ["#0e1428", "#151d38", "#1d2848", "#26345a", "#30416e", "#3e5284"]
CARPET_O = ["#1e2232", "#262a3e", "#2e344a", "#383f58", "#444c68"]
LINKED = ["#0a2a52", "#124a8a", "#1e6cc0", "#3a8ae0", "#8ac0f4", "#e8f2fc"]                # LinkedOut blue
WALNUT = ["#2a1810", "#40261a", "#5a3624", "#744a30", "#8e5e3c", "#a8744c"]
PEAK = ["#0e3a3a", "#145656", "#1e7470", "#2e968c", "#6ac8b4"]                             # PEAKLINE teal
PAPER = ["#a8a49c", "#d0ccc2", "#ece8de", "#faf8f2"]
SHADOW = S.SHADOW


def _rng(seed):
    return np.random.default_rng(seed)


# --- walls ------------------------------------------------------------------------------------
def office_wall(cv, x, y, w, h, seed=0):
    S.store_wall(cv, x, y, w, h, seed=seed, pal=OFFICE)


def office_ceiling(cv, x, w, h=12, panels=()):
    """A pale acoustic ceiling band with flush LED panels and their cool wash on the wall."""
    cv.rect(x, 0, w, h, "#3a3846")
    for gx in range(x, x + w, 24):
        cv.vline(gx, 0, h - 3, "#32303e")
    cv.hline(x, h - 3, w, "#4a4858"); cv.hline(x, h - 2, w, "#565466"); cv.hline(x, h - 1, w, "#2a2834")
    cv.hline(x, h, w, C(SHADOW, 0.45))
    for (cx, pw) in panels:
        cv.rect(cx - pw // 2, h - 3, pw, 3, "#f2f4fa"); cv.hline(cx - pw // 2, h - 1, pw, "#c8ccd8")
        for (d, a) in [(10, 0.05), (6, 0.06), (3, 0.07)]:
            cv.rect(cx - pw // 2 - d, h, pw + 2 * d, d * 2, C("#e8eeff", a))


def accent_wall(cv, x, y, w, h, seed=0):
    """A navy feature wall: flat paint with soft roller marks and a walnut slat band along the foot."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, NAVY[3])
    for _ in range(w * h // 80):
        px_, py_ = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        cv.hline(px_, py_, int(rng.integers(2, 4)), NAVY[2] if rng.random() < 0.6 else NAVY[4])
    for (hh, a) in [(10, 0.14), (5, 0.12), (2, 0.14)]:
        cv.rect(x, y, w, hh, C(SHADOW, a))
    sy = y + h - 26
    cv.rect(x, sy, w, 21, WALNUT[2])
    for sx in range(x, x + w, 4):
        cv.vline(sx, sy, 21, WALNUT[1]); cv.vline(sx + 1, sy, 21, WALNUT[4])
    cv.hline(x, sy, w, WALNUT[5]); cv.hline(x, sy + 20, w, WALNUT[0])
    cv.rect(x, y + h - 5, w, 5, S.BLACK[2]); cv.hline(x, y + h - 5, w, S.BLACK[4])
    cv.vline(x, y, h, C(SHADOW, 0.4)); cv.vline(x + w - 1, y, h, C("#ffffff", 0.08))


def raised_letters(cv, s, cx, y, scale=2, face="#eef0f6", side="#8a90a8", glow="#e8eeff"):
    """Dimensional wall letters: the face in the game font at `scale`, a two-step side below-right,
    a soft wall-wash above from the three little spot cans."""
    m = text_mask(s, scale)
    h, w = m.shape
    x0 = cx - w // 2
    paint_mask(cv, m, x0 + 2, y + 2, C(SHADOW, 0.35))
    paint_mask(cv, m, x0 + 1, y + 1, side)
    paint_mask(cv, m, x0, y, face)
    for k in (-1, 0, 1):
        sx = cx + k * w // 3
        cv.rect(sx - 2, y - 9, 5, 3, S.BLACK[2]); cv.rect(sx - 1, y - 7, 3, 1, "#fff6e0")
        halo(cv, sx, y + 2, 18, colour=glow, strength=0.05, steps=3)
    return x0, w, h


def night_view(cv, x, y, w, h, seed=0):
    """What the window shows: stars, the dark ridge of the Flatirons, campus roofs with lit windows,
    a lamp-post glow."""
    rng = _rng(seed)
    cv.dither_v(x, y, w, h, "#0c1226", "#26305a", steps=4)
    for _ in range(w * h // 50):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h // 2)), "#c8d0f0" if rng.random() < 0.5 else "#8a96c8")
    ridge = [(x, y + h * 0.55)]
    for i, xx in enumerate(range(x, x + w + 6, 6)):
        ridge.append((xx, y + h * 0.5 - 6 * abs(np.sin(i * 0.9)) - (8 if i in (3, 4) else 0)))
    cv.poly(ridge + [(x + w, y + h), (x, y + h)], "#1a1a34")
    for bx in range(x, x + w, 11):
        bh = int(rng.integers(8, 16))
        cv.rect(bx, y + h - bh, 11, bh, "#2a1e2a")
        cv.rect(bx, y + h - bh, 11, 2, "#4a2a26")                       # red tile roofs
        for _ in range(2):
            if rng.random() < 0.7:
                cv.rect(bx + int(rng.integers(1, 8)), y + h - bh + int(rng.integers(4, max(5, bh - 2))), 2, 2, "#f6cf7a")


def blinds_window(cv, x, y, w, h, seed=0, raised=0.4):
    """A tall office window at night with venetian blinds: the top part drawn down (closed slats),
    the rest raised so the campus shows through; a white frame and a deep sill."""
    cv.rect(x - 4, y - 4, w + 8, h + 8, OUT)
    cv.rect(x - 3, y - 3, w + 6, h + 6, "#c8c8d2"); cv.hline(x - 3, y - 3, w + 6, "#eeeef4")
    night_view(cv, x, y, w, h, seed=seed)
    cv.vline(x + w // 2, y, h, "#a8a8b4"); cv.vline(x + w // 2 + 1, y, h, "#6e6e7c")
    bh = int(h * raised)
    for yy in range(y, y + bh, 3):
        cv.hline(x, yy, w, "#d8d8e0"); cv.hline(x, yy + 1, w, "#b0b0bc"); cv.hline(x, yy + 2, w, "#8a8a98")
    cv.rect(x, y + bh, w, 3, "#e8e8ee"); cv.hline(x, y + bh + 2, w, "#7a7a88")       # bottom rail
    cv.vline(x + 5, y + bh + 3, 14, "#e8e8ee"); cv.rect(x + 4, y + bh + 16, 3, 3, "#c8c8d2")   # pull cord
    cv.rect(x - 6, y + h + 2, w + 12, 4, "#d8d8e0"); cv.hline(x - 6, y + h + 2, w + 12, "#f6f6fa"); cv.hline(x - 6, y + h + 5, w + 12, C(SHADOW, 0.5))


def diploma(cv, x, y, w=26, h=20):
    """A framed diploma: black frame, cream mat, a ribboned gold seal and a line of script."""
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, S.BLACK[2])
    cv.rect(x + 3, y + 3, w - 6, h - 6, "#f2ead6")
    cv.hline(x + 6, y + 6, w - 12, "#3a2a26"); cv.hline(x + 8, y + 9, w - 16, "#8a7a6a")
    cv.ellipse(x + w - 10, y + h - 9, 5, 5, S.GOLD[3]); cv.px(x + w - 8, y + h - 5, "#c8382c"); cv.px(x + w - 9, y + h - 4, "#c8382c")
    cv.hline(x + 5, y + h - 6, 8, "#8a7a6a")


def framed_photo(cv, x, y, w=22, h=16):
    """A framed photo of the Flatirons at sunset."""
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, WALNUT[3])
    cv.dither_v(x + 2, y + 2, w - 4, h - 4, "#e8906a", "#5a3a6a", steps=3)
    for (px_, ph) in [(x + 5, 6), (x + 9, 8), (x + 13, 7)]:
        cv.poly([(px_ - 3, y + h - 2), (px_, y + h - 2 - ph), (px_ + 3, y + h - 2)], "#3a2a3a")


def job_board(cv, x, y, w, h, seed=0):
    """A cork board headed JOBS: postings with tear-off tabs, an INTERN poster, a red HIRING card,
    business cards, push pins."""
    rng = _rng(seed)
    cv.rect(x - 3, y - 3, w + 6, h + 6, OUT)
    cv.rect(x - 2, y - 2, w + 4, h + 4, WALNUT[3]); cv.hline(x - 2, y - 2, w + 4, WALNUT[5])
    cork_surface(cv, x, y, w, h, seed=seed)
    s = "JOBS"
    cv.rect(x + w // 2 - text_width(s) // 2 - 4, y + 2, text_width(s) + 8, 11, NAVY[2])
    text(cv, s, x + w // 2 - text_width(s) // 2, y + 2, "#f2ecdc")
    # postings with tear-off tabs
    xx = x + 4
    while xx < x + w - 18:
        pw, ph = int(rng.integers(16, 22)), int(rng.integers(20, 26))
        py_ = y + 16 + int(rng.integers(0, max(1, h - ph - 26)))
        cv.rect(xx + 1, py_ + 1, pw, ph, C(SHADOW, 0.4)); cv.rect(xx, py_, pw, ph, PAPER[3])
        cv.rect(xx + 2, py_ + 2, pw - 4, 3, [NAVY[3], "#c8382c", PEAK[2], S.GOLD[2]][int(rng.integers(4))])
        for ly in range(py_ + 7, py_ + ph - 8, 2):
            cv.hline(xx + 2, ly, int(rng.integers(pw // 2, pw - 3)), PAPER[0])
        for tx in range(xx + 1, xx + pw - 2, 3):                       # tear-off tabs, a few already taken
            if rng.random() < 0.7:
                cv.vline(tx, py_ + ph - 6, 6, PAPER[2]); cv.px(tx, py_ + ph - 4, PAPER[0])
            else:
                cv.vline(tx, py_ + ph - 6, 6, C(SHADOW, 0.0))
        cv.px(xx + pw // 2, py_ + 1, "#e84a3a")
        xx += pw + int(rng.integers(3, 6))
    # a red HIRING card and two business cards along the bottom
    hx, hy = x + w - 34, y + h - 13
    cv.rect(hx, hy, 30, 10, "#c8382c"); micro_text(cv, "HIRING", hx + 15 - micro_width("HIRING") // 2, hy + 3, "#f6f4ee")
    cv.rect(x + 6, y + h - 10, 12, 7, PAPER[3]); cv.hline(x + 8, y + h - 8, 7, NAVY[3])
    cv.rect(x + 20, y + h - 9, 12, 7, "#e8eef6"); cv.hline(x + 22, y + h - 7, 6, PEAK[2])


def tv_slides(w, h):
    """The events screen's slideshow: CAREER FAIR TONIGHT; LinkedOut's UPDATE YOUR PROFILE;
    RESUME REVIEW 4PM. Each a w x h Canvas."""
    slides = []
    # 1: the fair
    cv = Canvas(w, h)
    cv.rect(0, 0, w, h, NAVY[2]); cv.rect(0, h - 8, w, 8, S.GOLD[2])
    text(cv, "CAREER", w // 2 - text_width("CAREER") // 2, 3, "#f2ecdc")
    text(cv, "FAIR", w // 2 - text_width("FAIR") // 2, 13, S.GOLD[4])
    micro_text(cv, "TONIGHT 6-9", w // 2 - micro_width("TONIGHT 6-9") // 2, h - 6, S.BLACK[1])
    for k in range(5):                                                  # little people in a queue
        px_ = 6 + k * 7
        cv.rect(px_, h - 15, 3, 5, ["#e86a5a", "#8ac0f4", "#f2d23a", "#7ae0a0", "#f2ecdc"][k]); cv.rect(px_, h - 18, 3, 3, "#e8c8a8")
    slides.append(cv)
    # 2: LinkedOut
    cv = Canvas(w, h)
    cv.rect(0, 0, w, h, LINKED[5]); cv.rect(0, 0, w, 10, LINKED[2])
    linkedout_logo(cv, 3, 2)
    micro_text(cv, "LINKEDOUT", 14, 3, LINKED[5])
    cv.ellipse(5, 14, 10, 10, PAPER[0]); cv.ellipse(7, 15, 6, 5, "#e8c8a8"); cv.rect(7, 20, 6, 3, LINKED[2])
    micro_text(cv, "UPDATE", 18, 14, LINKED[0]); micro_text(cv, "YOUR PROFILE", 18, 20, LINKED[1])
    cv.rect(w - 22, h - 9, 19, 7, LINKED[2]); micro_text(cv, "GO", w - 16, h - 8, LINKED[5])
    slides.append(cv)
    # 3: resume review
    cv = Canvas(w, h)
    cv.rect(0, 0, w, h, PEAK[1])
    cv.rect(5, 4, 14, h - 8, PAPER[3]); cv.rect(7, 6, 10, 2, NAVY[3])
    for ly in range(10, h - 6, 2):
        cv.hline(7, ly, 8 if ly % 4 else 10, PAPER[0])
    text(cv, "RESUME", 24, 4, "#f2ecdc")
    text(cv, "REVIEW", 24, 14, PEAK[4])
    micro_text(cv, "WALK-INS 4PM", 24, h - 7, "#f2ecdc")
    slides.append(cv)
    return slides


def wall_tv(cv, x, y, w, h):
    """A big flat screen on the accent wall: black bezel, the wall mount's shadow, the first slide."""
    cv.rect(x - 3, y - 3, w + 6, h + 6, C(SHADOW, 0.35))
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT); cv.rect(x - 1, y - 1, w + 2, h + 2, "#1a1a22")
    cv.hline(x - 1, y - 1, w + 2, "#3a3a46")
    cv.paste(tv_slides(w, h)[0], x, y)
    cv.px(x + w - 2, y + h + 1, "#7ae0a0")
    for (d, a) in [(6, 0.04), (3, 0.05)]:
        cv.rect(x - d, y + h + 2, w + 2 * d, d, C("#8ac0f4", a))


def linkedout_logo(cv, x, y, size=8):
    """LinkedOut's mark: a white rounded square with a little open door in LinkedOut blue."""
    cv.rect(x, y, size, size, LINKED[5]); cv.px(x, y, (0, 0, 0, 0)); cv.px(x + size - 1, y, (0, 0, 0, 0))
    cv.px(x, y + size - 1, (0, 0, 0, 0)); cv.px(x + size - 1, y + size - 1, (0, 0, 0, 0))
    cv.rect(x + 2, y + 2, 3, size - 3, LINKED[2]); cv.rect(x + 5, y + 3, 1, size - 4, LINKED[1])    # a door, ajar
    cv.px(x + 4, y + size // 2, LINKED[5])


def brochure_rack(cv, x, y, cols=3, rows=3, seed=0, titles=("RESUME", "INTERVIEW", "MAJORS", "WHAT NOW?")):
    """A wall rack of clear acrylic pockets full of leaflets; one pocket is empty."""
    rng = _rng(seed)
    pw, ph = 16, 20
    w, h = cols * (pw + 2) + 2, rows * (ph + 2) + 2
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT); cv.rect(x, y, w, h, "#5a5868")
    cols_ = [NAVY[4], "#c8382c", PEAK[3], S.GOLD[3], "#e8eef6", "#7a3a8a"]
    k = 0
    for r in range(rows):
        for c in range(cols):
            px_, py_ = x + 2 + c * (pw + 2), y + 2 + r * (ph + 2)
            if (r, c) == (0, 2):
                cv.rect(px_, py_ + 6, pw, ph - 6, C("#c8d8f0", 0.25)); cv.hline(px_, py_ + 6, pw, "#e8f0ff")   # empty
                continue
            col = cols_[int(rng.integers(len(cols_)))]
            cv.rect(px_ + 1, py_, pw - 2, ph, col); cv.hline(px_ + 1, py_, pw - 2, shade(col, 0.3))
            cv.rect(px_ + 3, py_ + 4, pw - 6, 3, PAPER[3])
            cv.hline(px_ + 3, py_ + 10, pw - 7, shade(col, 0.4)); cv.hline(px_ + 3, py_ + 12, pw - 9, shade(col, 0.4))
            cv.rect(px_, py_ + 6, pw, ph - 6, C("#c8d8f0", 0.22)); cv.hline(px_, py_ + 6, pw, "#e8f0ff")   # acrylic front
            k += 1
    return w, h


def popup_banner(cv, cx, base, w, h, name, lines=(), pal=PEAK, logo=True):
    """A roll-up banner standing against the wall: the silver cassette foot, the pole behind, the
    printed banner: the company name on a colour band, a mountain logo, slogan lines, a photo band."""
    x = cx - w // 2
    top = base - h
    cv.rect(x - 2, base - 4, w + 4, 4, OUT); cv.rect(x - 1, base - 3, w + 2, 2, CHROME[2]); cv.hline(x - 1, base - 3, w + 2, CHROME[3])
    cv.rect(x - 4, base - 1, 3, 1, OUT); cv.rect(x + w + 1, base - 1, 3, 1, OUT)
    cv.rect(x - 1, top - 1, w + 2, h - 3, OUT)
    cv.rect(x, top, w, h - 5, "#f2f2f6")
    cv.rect(x, top, w, 14, pal[2]); cv.hline(x, top, w, pal[4])
    if text_width(name) <= w - 2:
        text(cv, name, cx - text_width(name) // 2, top + 2, "#f6f6fa")
    else:
        micro_text(cv, name, cx - micro_width(name) // 2, top + 5, "#f6f6fa")
    yy = top + 18
    if logo:
        cv.poly([(cx - 10, yy + 12), (cx - 3, yy), (cx + 2, yy + 7), (cx + 5, yy + 3), (cx + 11, yy + 12)], pal[3])
        cv.poly([(cx - 3, yy), (cx - 1, yy + 4), (cx - 5, yy + 4)], "#f6f6fa")
        yy += 16
    for (s, col) in lines:
        micro_text(cv, s, cx - micro_width(s) // 2, yy, col)
        yy += 7
    pb = base - 5 - 16
    cv.rect(x, pb, w, 16, pal[1])
    for k in range(3):                                                 # stock photo: people at a laptop
        px_ = x + 5 + k * (w - 10) // 3
        cv.rect(px_, pb + 6, 5, 10, ["#e86a5a", "#f2ecdc", "#8ac0f4"][k]); cv.rect(px_ + 1, pb + 2, 3, 4, "#e8c8a8")
    cv.rect(cx - 6, pb + 10, 12, 4, "#c8ccd8")


def fabric_banner(cv, x0, x1, y, label, sag=4, bg=NAVY[3], fg="#f2ecdc", edge=None):
    """A fabric banner hung between two ceiling wires, lettered across, a little sag at the hem."""
    edge = edge or S.GOLD[3]
    w = x1 - x0
    if y > 10:
        cv.vline(x0 + 4, 10, y - 10, IRON[2]); cv.vline(x1 - 5, 10, y - 10, IRON[2])
    cv.rect(x0, y, w, 16, OUT); cv.rect(x0 + 1, y + 1, w - 2, 14, bg)
    cv.hline(x0 + 1, y + 1, w - 2, shade(bg, 0.25)); cv.hline(x0 + 1, y + 13, w - 2, edge)
    for k in range(w // 6):
        cv.px(x0 + 1 + k * 6 + 3, y + 15 + (1 if 0 < k < w // 6 - 1 else 0) * (sag // 3), edge)
    text(cv, label, x0 + w // 2 - text_width(label) // 2, y + 3, fg)


# --- floors -----------------------------------------------------------------------------------
def office_carpet(cv, x, y, w, h, seed=0, pal=CARPET_O, tile=24):
    """Blue-grey carpet tile in a linear loop pattern, every tile quarter-turned, a few darker
    accent tiles running in a broken line, seams just visible."""
    rng = _rng(seed)
    for ty in range(y, y + h, tile):
        for tx in range(x, x + w, tile):
            tw, th = min(tile, x + w - tx), min(tile, y + h - ty)
            i, j = (tx - x) // tile, (ty - y) // tile
            accent = (i + 2 * j) % 7 == 0
            base_ = shade(pal[2], -0.07) if accent else pal[2]
            cv.rect(tx, ty, tw, th, base_)
            if (i + j) % 2 == 0:
                for k in range(tx + 1, tx + tw, 3):
                    cv.vline(k, ty + 1, th - 2, shade(base_, -0.1))
                for k in range(ty + 2, ty + th, 6):
                    cv.hline(tx + 1, k, tw - 2, shade(base_, 0.06))
            else:
                for k in range(ty + 1, ty + th, 3):
                    cv.hline(tx + 1, k, tw - 2, shade(base_, -0.1))
                for k in range(tx + 2, tx + tw, 6):
                    cv.vline(k, ty + 1, th - 2, shade(base_, 0.06))
            cv.hline(tx, ty, tw, pal[3]); cv.vline(tx, ty, th, shade(pal[2], 0.04))
            if rng.random() < 0.04:
                cv.px(tx + int(rng.integers(2, tile - 2)), ty + int(rng.integers(2, tile - 2)), pal[4])


# --- props ------------------------------------------------------------------------------------
def advisor_desk(width=132, height=52, seed=0):
    """The advisor's desk from the guest side: a walnut top, a pale modesty panel with walnut trim
    and a brass ADVISOR nameplate; on top the back of a monitor on its arm, a mint bowl, a tissue box,
    a stack of folders with the four-year plan on top, a succulent, a CU mug and a pen cup."""
    W, Hc = width + 8, height + 10
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 4, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    top = base - 30
    cx = ox + width // 2
    # monitor (we see its back) on an arm, left of centre
    mx = ox + 30
    cv.rect(mx - 2, top - 8, 5, 8, OUT); cv.vline(mx, top - 8, 8, IRON[3])
    cv.rect(mx - 18, top - 30, 38, 23, OUT); cv.rect(mx - 17, top - 29, 36, 21, "#2a2a34")
    cv.hline(mx - 17, top - 29, 36, "#4a4a58"); cv.rect(mx - 5, top - 22, 10, 8, "#24242c"); cv.px(mx + 15, top - 11, "#7ae0a0")
    for (d, a) in [(4, 0.06), (2, 0.08)]:                              # the screen's glow spilling round its edges
        cv.rect(mx - 17 - d, top - 29 - d, 36 + 2 * d, d, C(LINKED[4], a))
    # folders and the plan
    fx = ox + 58
    for k, col in enumerate([NAVY[4], "#c8382c", S.GOLD[3]]):
        cv.rect(fx + k, top - 4 - k * 2, 22, 3, OUT); cv.rect(fx + 1 + k, top - 3 - k * 2, 20, 2, col)
    cv.rect(fx + 2, top - 12, 20, 4, PAPER[3]); cv.hline(fx + 4, top - 11, 12, NAVY[3]); cv.hline(fx + 4, top - 9, 8, PAPER[0])
    # tissue box, mint bowl, mug, pen cup, succulent
    cv.rect(ox + 84, top - 8, 14, 8, OUT); cv.rect(ox + 85, top - 7, 12, 7, PEAK[3]); cv.hline(ox + 85, top - 7, 12, PEAK[4])
    cv.rect(ox + 89, top - 11, 4, 4, PAPER[3])
    cv.ellipse(ox + 101, top - 6, 13, 7, OUT); cv.ellipse(ox + 102, top - 5, 11, 5, "#c8d8f0")
    for k in range(4):
        cv.px(ox + 104 + k * 2, top - 5 + (k % 2), ["#e84a3a", "#f6f4ee", "#7ae0a0", "#e84a3a"][k])
    cv.rect(ox + 117, top - 9, 7, 9, OUT); cv.rect(ox + 118, top - 8, 5, 8, S.BLACK[3]); cv.px(ox + 120, top - 6, S.GOLD[3])
    cv.rect(ox + 123, top - 7, 2, 4, OUT)
    cv.rect(ox + 8, top - 8, 7, 8, OUT); cv.rect(ox + 9, top - 7, 5, 7, "#e8e4da")
    for k, c in enumerate(["#2a5aa8", "#c8382c", "#3a3a4a"]):
        cv.vline(ox + 9 + k * 2, top - 12 + k, 5, c)
    # top
    cv.rect(ox - 1, top - 1, width + 2, 6, OUT)
    cv.rect(ox, top, width, 4, WALNUT[4]); cv.hline(ox, top, width, WALNUT[5]); cv.hline(ox, top + 3, width, WALNUT[2])
    # front: pale modesty panel with walnut trim and legs
    cv.rect(ox + 2, top + 5, width - 4, base - top - 6, OUT)
    cv.rect(ox + 3, top + 5, width - 6, base - top - 10, "#b8b6c0")
    cv.hline(ox + 3, top + 5, width - 6, "#d8d6e0"); cv.rect(ox + 3, base - 9, width - 6, 3, "#8a8896")
    for lx in (ox + 3, ox + width - 8):
        cv.rect(lx, top + 5, 5, base - top - 6, WALNUT[3]); cv.vline(lx, top + 5, base - top - 6, WALNUT[5])
    s = "ADVISOR"
    pw = micro_width(s) + 8
    cv.rect(cx - pw // 2, top + 10, pw, 9, OUT); cv.rect(cx - pw // 2 + 1, top + 11, pw - 2, 7, S.GOLD[3])
    cv.hline(cx - pw // 2 + 1, top + 11, pw - 2, S.GOLD[5])
    micro_text(cv, s, cx - micro_width(s) // 2, top + 12, S.BLACK[1])
    return cv, cx, base


def guest_chair(width=28, height=34, seed=0, upholstery=PEAK):
    """A guest chair seen from behind (facing the desk): an upholstered back, chrome frame, legs."""
    W, Hc = width + 4, height + 4
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 2, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2, 2)
    for lx in (ox + 3, ox + width - 5):
        cv.rect(lx, base - 14, 3, 14, OUT); cv.vline(lx + 1, base - 13, 12, CHROME[2])
    cv.rect(ox + 1, base - 16, width - 2, 5, OUT); cv.rect(ox + 2, base - 15, width - 4, 3, shade(upholstery[1], -0.1))
    cv.rect(ox + 2, base - height, width - 4, height - 14, OUT)
    cv.rect(ox + 3, base - height + 1, width - 6, height - 16, upholstery[1])
    cv.hline(ox + 3, base - height + 1, width - 6, upholstery[3]); cv.vline(ox + 3, base - height + 1, height - 16, upholstery[2])
    cv.vline(ox + width - 4, base - height + 1, height - 16, upholstery[0])
    for k in range(3):
        cv.px(ox + 7 + k * (width - 14) // 2, base - height + 8, upholstery[0])          # buttons
    return cv, cx, base


def kiosk_screen(w, h):
    """The LinkedOut kiosk's screen: a blue header with the mark and a red notification badge, a
    profile card reading 0 VIEWS, a TAP button."""
    cv = Canvas(w, h)
    cv.rect(0, 0, w, h, LINKED[5])
    cv.rect(0, 0, w, 9, LINKED[2]); cv.hline(0, 8, w, LINKED[1])
    linkedout_logo(cv, 2, 1, size=7)
    cv.hline(11, 4, w - 22, LINKED[4])                                   # search bar
    cv.rect(w - 9, 1, 8, 7, "#d83a32"); micro_text(cv, "99", w - 8, 2, "#ffffff")
    cv.ellipse(2, 11, 9, 9, PAPER[0]); cv.ellipse(4, 12, 5, 4, "#e8c8a8"); cv.rect(4, 16, 5, 3, LINKED[2])
    micro_text(cv, "0", 13, 11, LINKED[0])
    micro_text(cv, "VIEWS", 13, 17, LINKED[1])
    cv.rect(2, h - 7, w - 4, 6, LINKED[2]); cv.hline(2, h - 7, w - 4, LINKED[3])
    micro_text(cv, "TAP", w // 2 - micro_width("TAP") // 2, h - 6, LINKED[5])
    return cv


def linkedout_kiosk(width=42, height=78, seed=0):
    """A floor-standing touch kiosk: a weighted base, a white column with a LinkedOut-blue stripe,
    a tilted screen head, and a lit LINKEDOUT topper. Returns (canvas, ax, ay, screen_rect)."""
    W, Hc = width + 6, height + 6
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 3, height + 3
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2, 3)
    cv.rect(cx - 13, base - 5, 27, 5, OUT); cv.rect(cx - 12, base - 4, 25, 3, "#c8ccd8"); cv.hline(cx - 12, base - 4, 25, "#eef0f6")
    col_top = base - 44
    cv.rect(cx - 7, col_top, 15, base - col_top - 4, OUT)
    cv.rect(cx - 6, col_top + 1, 13, base - col_top - 6, "#dcdee6"); cv.vline(cx - 6, col_top + 1, base - col_top - 6, "#f6f6fa")
    cv.vline(cx + 6, col_top + 1, base - col_top - 6, "#9a9eae")
    cv.rect(cx - 2, col_top + 4, 5, base - col_top - 12, LINKED[2]); cv.vline(cx - 2, col_top + 4, base - col_top - 12, LINKED[3])
    linkedout_logo(cv, cx - 3, base - 20, size=7)
    # screen head, tilted back: a bezel with the screen, its glow
    hx0, hy0 = ox + 2, base - height + 12
    hw, hh = width - 4, 32
    cv.poly([(hx0 + 2, hy0), (hx0 + hw - 2, hy0), (hx0 + hw, hy0 + hh), (hx0, hy0 + hh)], OUT)
    cv.poly([(hx0 + 3, hy0 + 1), (hx0 + hw - 3, hy0 + 1), (hx0 + hw - 1, hy0 + hh - 1), (hx0 + 1, hy0 + hh - 1)], "#2a2a34")
    sx, sy, sw, sh = hx0 + 4, hy0 + 3, hw - 8, hh - 7
    cv.paste(kiosk_screen(sw, sh), sx, sy)
    cv.rect(hx0 + 1, hy0 + hh - 2, hw - 2, 2, "#4a4a58")
    # topper
    s = "LINKEDOUT"
    tw = micro_width(s) + 6
    cv.rect(cx - tw // 2, base - height, tw, 10, OUT); cv.rect(cx - tw // 2 + 1, base - height + 1, tw - 2, 8, LINKED[2])
    cv.hline(cx - tw // 2 + 1, base - height + 1, tw - 2, LINKED[3])
    micro_text(cv, s, cx - micro_width(s) // 2, base - height + 3, LINKED[5])
    cv.rect(cx - 1, base - height + 10, 3, 2, OUT)
    return cv, cx, base, (sx, sy, sw, sh)


def fair_table(width=154, height=46, seed=0, name="PEAKLINE", pal=PEAK):
    """A career fair table: a fitted teal cloth to the floor printed with the PEAKLINE mountain mark
    and name; on top a fan of brochures, a bowl of stress balls, a cup of pens, sticker sheets, a
    tablet on a stand for sign-ups, water bottles and a bowl of candy."""
    rng = _rng(seed)
    W, Hc = width + 8, height + 10
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 4, height + 6
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 + 2, 3)
    top = base - 28
    # cloth
    cv.rect(ox, top, width, base - top, OUT)
    cv.rect(ox + 1, top + 1, width - 2, base - top - 2, pal[1])
    cv.rect(ox + 1, top + 1, width - 2, 4, pal[2]); cv.hline(ox + 1, top + 1, width - 2, pal[3])
    for fx in range(ox + 8, ox + width - 6, 18):
        cv.vline(fx, top + 6, base - top - 8, shade(pal[1], -0.15))
    cv.poly([(cx - 30, top + 22), (cx - 22, top + 9), (cx - 17, top + 16), (cx - 13, top + 11), (cx - 6, top + 22)], pal[3])
    cv.poly([(cx - 22, top + 9), (cx - 20, top + 13), (cx - 24, top + 13)], "#f2f6f6")
    text(cv, name, cx - 2, top + 11, "#f2f6f6")
    cv.hline(ox + 1, base - 3, width - 2, shade(pal[1], -0.3))
    # things on top (left to right)
    yy = top
    for k in range(5):                                                   # brochure fan
        bx = ox + 8 + k * 3
        cv.rect(bx, yy - 9 + (k % 2), 9, 9, OUT); cv.rect(bx + 1, yy - 8 + (k % 2), 7, 8, [pal[3], "#f2f6f6", pal[2], S.GOLD[3], "#f2f6f6"][k])
    cv.ellipse(ox + 30, yy - 7, 17, 8, OUT); cv.ellipse(ox + 31, yy - 6, 15, 6, "#d8dce4")                 # stress balls
    for k in range(5):
        c = [pal[3], "#e86a5a", S.GOLD[3], pal[4], "#8ac0f4"][k]
        cv.ellipse(ox + 32 + k * 3, yy - 9 + (k % 2) * 2, 5, 5, OUT); cv.ellipse(ox + 33 + k * 3, yy - 8 + (k % 2) * 2, 3, 3, c)
    px_ = ox + 52
    cv.rect(px_, yy - 9, 7, 9, OUT); cv.rect(px_ + 1, yy - 8, 5, 8, "#f2f6f6")                            # pen cup
    for k, c in enumerate([pal[2], "#2a5aa8", pal[3]]):
        cv.vline(px_ + 1 + k * 2, yy - 14 + (k % 2), 6, c)
    # the tablet on its stand (sign-ups), centre right
    tx = ox + width - 54
    cv.poly([(tx, yy - 1), (tx + 20, yy - 1), (tx + 18, yy - 16), (tx + 2, yy - 16)], OUT)
    cv.poly([(tx + 2, yy - 2), (tx + 18, yy - 2), (tx + 16, yy - 15), (tx + 3, yy - 15)], "#e8f2fc")
    cv.rect(tx + 5, yy - 13, 10, 2, pal[2]); cv.hline(tx + 5, yy - 9, 9, PAPER[0]); cv.hline(tx + 5, yy - 6, 7, PAPER[0])
    # sticker sheets, water bottles, candy
    cv.rect(ox + 66, yy - 3, 14, 3, OUT); cv.rect(ox + 67, yy - 2, 12, 2, "#f2f6f6")
    for k in range(3):
        cv.px(ox + 69 + k * 3, yy - 2, [pal[3], "#e86a5a", S.GOLD[3]][k])
    for k in range(3):
        bx = ox + width - 30 + k * 5
        cv.rect(bx, yy - 12, 4, 12, OUT); cv.rect(bx + 1, yy - 11, 2, 11, "#8ac0f4"); cv.px(bx + 1, yy - 11, "#e8f2fc")
        cv.rect(bx + 1, yy - 7, 2, 3, pal[2]); cv.rect(bx + 1, yy - 14, 2, 2, OUT)
    cv.ellipse(ox + width - 14, yy - 6, 12, 6, OUT); cv.ellipse(ox + width - 13, yy - 5, 10, 4, "#c8d8f0")
    for k in range(4):
        cv.px(ox + width - 11 + k * 2, yy - 5 + (k % 2), ["#f2d23a", "#e84a3a", "#7ae0a0", "#f2d23a"][k])
    return cv, cx, base


def beam_seats(width=98, height=36, seed=0, colours=None):
    """Three joined waiting chairs on a chrome beam, navy, gold, navy; somebody's resume left on one."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    seats = colours or [(NAVY[3], NAVY[5], NAVY[1]), (S.GOLD[2], S.GOLD[4], S.GOLD[1]), (NAVY[3], NAVY[5], NAVY[1])]
    sw = width // 3
    cv.rect(ox, base - 13, width, 3, OUT); cv.hline(ox + 1, base - 12, width - 2, CHROME[2])
    for lx in (ox + 6, ox + width - 9):
        cv.rect(lx, base - 12, 4, 12, OUT); cv.vline(lx + 1, base - 11, 10, CHROME[2])
        cv.rect(lx - 3, base - 2, 10, 2, CHROME[1])
    for i, (c, hi, lo) in enumerate(seats):
        sx = ox + i * sw + 1
        cv.rect(sx + 1, base - height, sw - 4, 18, OUT)
        cv.rect(sx + 2, base - height + 1, sw - 6, 16, c); cv.hline(sx + 2, base - height + 1, sw - 6, hi)
        cv.vline(sx + 2, base - height + 1, 16, hi); cv.hline(sx + 3, base - height + 12, sw - 8, lo)
        cv.rect(sx, base - 19, sw - 2, 7, OUT)
        cv.rect(sx + 1, base - 18, sw - 4, 4, hi); cv.hline(sx + 1, base - 15, sw - 4, c); cv.hline(sx + 1, base - 14, sw - 4, lo)
    # a resume left on the right seat
    rx = ox + 2 * sw + 6
    cv.rect(rx, base - 21, 12, 5, OUT); cv.rect(rx + 1, base - 20, 10, 3, PAPER[3]); cv.hline(rx + 2, base - 19, 6, NAVY[3])
    return cv, ox + width // 2, base


def water_cooler(width=22, height=50, seed=0):
    """A water cooler: the blue bottle upside down on a white cabinet, two taps, a cone-cup tube."""
    cv = Canvas(width + 6, height + 4, seed=seed)
    ox, base = 3, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2, 2)
    cv.rect(ox + 2, base - 32, width - 4, 32, OUT)
    cv.rect(ox + 3, base - 31, width - 6, 30, "#dcdee6"); cv.vline(ox + 3, base - 31, 30, "#f6f6fa"); cv.vline(ox + width - 4, base - 31, 30, "#9a9eae")
    cv.rect(ox + 5, base - 24, width - 10, 8, "#b8bcc8")
    cv.rect(ox + 6, base - 23, 3, 3, "#3a6aa8"); cv.rect(ox + width - 9, base - 23, 3, 3, "#c8382c")
    cv.rect(ox + 5, base - 15, width - 10, 2, "#8a8e9a")
    # the bottle
    cv.rect(cx - 2, base - 35, 5, 4, OUT)
    cv.ellipse(cx - 8, base - height, 17, 18, OUT); cv.ellipse(cx - 7, base - height + 1, 15, 16, "#5a8ac8")
    cv.vline(cx - 5, base - height + 4, 9, "#a8d0f4"); cv.ellipse(cx - 3, base - height + 10, 7, 4, "#4a7ab8")
    cv.hline(cx - 6, base - height + 7, 13, "#7aa8e0")
    # cone cups in their tube
    cv.rect(ox + width - 3, base - 30, 4, 12, OUT); cv.rect(ox + width - 2, base - 29, 2, 10, "#f2f6f6")
    return cv, cx, base


def snake_plant(width=36, height=58, seed=0):
    """A tall snake plant: upright sword leaves banded in two greens with yellow edges, in a white
    cylinder planter."""
    rng = _rng(seed)
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 - 2, 2)
    pot_w, pot_h = width - 12, 16
    for k in range(9):
        lx = cx + int(round((k - 4) * 2.2)) + int(rng.integers(-1, 2))
        lh = int(rng.integers(height - 34, height - pot_h + 2))
        lean = (k - 4) * 0.12 + rng.uniform(-0.08, 0.08)
        for i in range(lh):
            t = i / lh
            xx = int(round(lx + lean * i))
            ww = max(1, int(round(3 * np.sin(np.pi * (0.15 + 0.85 * t)) + 1)))
            yy = base - pot_h - i
            c = LEAF[3] if (i // 3) % 2 else LEAF[4]
            cv.hline(xx - ww // 2 - 1, yy, ww + 2, OUT)
            cv.hline(xx - ww // 2, yy, ww, c)
            if ww > 1 and t < 0.9:
                cv.px(xx - ww // 2, yy, "#c8c060")
    px_ = cx - pot_w // 2
    cv.rect(px_ - 1, base - pot_h - 1, pot_w + 2, pot_h + 1, OUT)
    cv.rect(px_, base - pot_h, pot_w, pot_h - 1, "#e8e8ee"); cv.vline(px_ + 2, base - pot_h + 1, pot_h - 3, "#ffffff")
    cv.rect(px_ + pot_w - 6, base - pot_h, 5, pot_h - 1, "#b8bac6"); cv.hline(px_, base - pot_h, pot_w, "#f6f6fa")
    return cv, cx, base


def ring_light(width=30, height=64, seed=0):
    """A ring light on a tripod for the FREE HEADSHOTS corner: the lit ring, a phone clamped in it."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 - 2, 2)
    for dx in (-11, 0, 11):
        cv.line(cx, base - 20, cx + dx, base - 1, OUT)
    cv.line(cx + 1, base - 20, cx - 10, base - 1, IRON[3]); cv.line(cx + 1, base - 20, cx + 12, base - 1, IRON[3])
    cv.rect(cx - 1, base - height + 18, 3, height - 38, OUT); cv.vline(cx, base - height + 18, height - 38, IRON[4])
    r = 11
    ry = base - height + r + 1
    ring = Canvas(cv.w, cv.h)
    ring.ellipse(cx - r - 1, ry - r - 1, 2 * r + 3, 2 * r + 3, OUT)
    ring.ellipse(cx - r, ry - r, 2 * r + 1, 2 * r + 1, "#fff6e6")
    ring.ellipse(cx - r + 2, ry - r + 2, 2 * r - 3, 2 * r - 3, "#e8e4f0")
    ring.ellipse(cx - r + 3, ry - r + 3, 2 * r - 5, 2 * r - 5, OUT)
    hole = Canvas(cv.w, cv.h)
    hole.ellipse(cx - r + 4, ry - r + 4, 2 * r - 7, 2 * r - 7, OUT)
    ring.a[hole.a[..., 3] > 0.5] = 0
    cv.paste(ring, 0, 0)
    cv.rect(cx - 3, ry - 5, 7, 11, OUT); cv.rect(cx - 2, ry - 4, 5, 9, "#2a2a34"); cv.px(cx, ry - 3, "#8ac0f4")
    cv.vline(cx, ry + 6, r - 5, IRON[3])
    return cv, cx, base


def cocktail_table(width=34, height=52, seed=0):
    """A tall round networking table: a white cloth to the floor gathered with a navy sash, HELLO
    name tags and a marker on top."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 + 1, 3)
    top = base - 36
    cv.poly([(ox + 2, top + 4), (ox + width - 2, top + 4), (cx + 5, top + 16), (ox + width - 1, base), (ox + 1, base), (cx - 5, top + 16)], OUT)
    cv.poly([(ox + 3, top + 5), (ox + width - 3, top + 5), (cx + 4, top + 16), (ox + width - 2, base - 1), (ox + 2, base - 1), (cx - 4, top + 16)], "#e8e8ee")
    for fx in (cx - 6, cx, cx + 6):
        cv.line(fx, top + 18, fx + (fx - cx), base - 2, "#b8bac6")
    cv.rect(cx - 6, top + 13, 13, 4, NAVY[3]); cv.hline(cx - 6, top + 13, 13, NAVY[5])
    cv.ellipse(ox, top - 2, width, 9, OUT); cv.ellipse(ox + 1, top - 1, width - 2, 7, "#f6f6fa")
    cv.rect(cx - 9, top - 1, 10, 6, "#d83a32"); cv.rect(cx - 8, top + 1, 8, 3, "#f6f6fa")      # HELLO tags
    cv.rect(cx + 2, top, 9, 5, "#d83a32"); cv.rect(cx + 3, top + 2, 7, 2, "#f6f6fa")
    cv.line(cx - 2, top + 4, cx + 4, top + 2, OUT); cv.px(cx - 2, top + 4, NAVY[4])
    return cv, cx, base
