"""Old Main notice hall (O02): who gets to say no.

Back wall: a crown moulding and a gilt stencilled frieze over deep green plaster, oak beadboard
wainscot below. In the middle, under the hall's old public-address horn (the Loudspeaker), the long
oak notice board - NOTICES in gilt on its header rail, a crowd of pinned papers on the cork, a few of
them stirring in the draught. Two tall round-headed sash windows with the campus and the Flatirons
under the moon, silver radiators beneath, brass gas-style sconces between. At the left end a
schoolhouse clock (11:42) and a sepia class photograph of 1877; at the right end the framed
architect's elevation of OLD MAIN 1876 and a red fire bell.
Floor: Victorian encaustic tile on the diagonal (terracotta and cream with black keys) inside a
plain border, an indigo-plum runner crossing the hall between the two side doors (cool moonlight
import paths
from the empty office on the left, warm lamplight from the cabinet room on the right) and a second
runner down to the courtyard doors at the front. Moonlight from the windows, lamp pools, a few
fallen notices.
Props: the free-standing WHAT YOU OWE board (ordinary office notices; once the notices have been
read, notice_limits, the three personal demands pasted over them), a staff pigeonhole cabinet, the
hand-lettered DIRECTORY on an easel, the information desk (OPEN AGAIN / IN THE MORNING), an oak
deacon's bench and a brass standard lamp with a milk-glass globe."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import light_pool
from props import OUT, IRON, ground_shadow
from lib_eng import micro_text, micro_width, scribble
from lib_norlin import moon_patch, depth_shade
from lib_oldmain import (plaster_om, cornice_om, stencil_frieze, beadboard, sash_window, radiator, sconce_om, horn_speaker,
                         notice_paper, cork_surface, oak_frame, scatter_notices, schoolhouse_clock, framed_photo,
                         elevation_print, encaustic_floor, tile_border, runner_om, spill, globe_pendant,
                         HALL_GREEN, OAK_IN, GILT_OM, CORK, PAPER, PAPER_TINTS, RED_STAMP, TILE_TERRA, TILE_CREAM, TILE_INK,
                         GLOBE, CREAM_TRIM, INK)

ROOM = "O02"
W, H = 800, 480
BASE = 142
WALK = (20, 142, 760, 314)
FLOOR_BOTTOM = WALK[1] + WALK[3]          # 456
RAIL_Y = 98                                # top of the wainscot's chair rail
WINDOWS = (222, 578)                       # sash windows (centre x)
WIN_W, WIN_TOP, WIN_H = 34, 26, 64
SCONCES = (268, 528)                       # backplates, at y SCONCE_Y
PENDANTS = (156, 644)                      # schoolhouse globes hanging from the ceiling
POOLS = ((236, 392, 64, 16), (590, 372, 70, 16))   # ceiling light on the floor: x, y, rx, ry
SCONCE_Y = 66
BOARD = (318, 42, 164, 54)                 # the notice board on the back wall: x, y, w, h
HORN = (398, 9)                            # the Loudspeaker: wall plate x, top
CHAIRS = (342, 382, 422, 462)              # waiting chairs against the wainscot under the board
CLOCK = (50, 26)
PHOTO = (80, 32, 52, 34)
PRINT = (660, 30, 72, 54)
FIRE_BELL = (758, 56)
CROSS_RUNNER = (288, 22)                   # runner between the side doors: top y, height
DOWN_RUNNER = (389, 22)                    # runner to the courtyard doors: left x, width
LAMP = (115, 210)
DESK = (235, 304)
STAND = (410, 329)
SIDE_DOOR = (268, 50)                      # side doorways: top y, height (left and right edges)
FRONT_DOOR = (364, 72)                     # front doorway: left x, width


# ------------------------------------------------------------------------------------- walls
def back_wall(bg):
    plaster_om(bg, 0, 13, W, RAIL_Y - 13, pal=HALL_GREEN, seed=21, shadow_top=6, cracks=0)
    cornice_om(bg, 0, 0, W)
    stencil_frieze(bg, 0, 13, W, ground=HALL_GREEN[2])
    beadboard(bg, 0, RAIL_Y, W, BASE - RAIL_Y, pal=OAK_IN, seed=4)
    # pilasters at both ends of the hall (the side walls turn here)
    for x0 in (0, W - 10):
        bg.rect(x0, 22, 10, RAIL_Y - 22, HALL_GREEN[3]); bg.vline(x0 + (9 if x0 == 0 else 0), 22, RAIL_Y - 22, HALL_GREEN[1])
        bg.vline(x0 + (1 if x0 == 0 else 8), 22, RAIL_Y - 22, HALL_GREEN[6])
    # windows with radiators below
    for i, wx in enumerate(WINDOWS):
        sash_window(bg, wx - WIN_W // 2, WIN_TOP, WIN_W, WIN_H, seed=30 + i, moon=(wx + 6, WIN_TOP + 14, 4) if i == 1 else None)
        radiator(bg, wx - 16, 112, 33, 23)
    # the notice board under the Loudspeaker
    bx, by, bw, bh = BOARD
    oak_frame(bg, bx, by, bw, bh, t=4)
    bg.rect(bx + 4, by + 3, bw - 8, 9, "#1c1622"); bg.hline(bx + 4, by + 3, bw - 8, "#2e2434")
    tw = text_width("NOTICES")
    text(bg, "NOTICES", bx + (bw - tw) // 2, by + 2, GILT_OM[4])
    cork_surface(bg, bx + 4, by + 13, bw - 8, bh - 17, seed=3)
    notices = scatter_notices(bg, bx + 4, by + 13, bw - 8, bh - 17, seed=12,
                              titles=["HOURS", "FEES", "KEYS", "SIGN", "LOST", "ROOM", "FORMS", "NO", "QUIET", "BACK 9"])
    horn_speaker(bg, HORN[0], HORN[1], wire_to=4)
    for k, chx in enumerate(CHAIRS):
        wall_chair(bg, chx, BASE - 1, seed=k)
    # sconces
    glows = [sconce_om(bg, sx, SCONCE_Y) for sx in SCONCES]
    glows += [globe_pendant(bg, px_, 58, chain_top=4, lit=True, r=6) for px_ in PENDANTS]
    # left end: schoolhouse clock and the class of 1877
    pivot, drop = schoolhouse_clock(bg, CLOCK[0], CLOCK[1], hour=11, minute=42)
    framed_photo(bg, *PHOTO, seed=5, rows=3, caption="1877")
    # right end: the architect's elevation and the fire bell
    elevation_print(bg, *PRINT)
    fx, fy = FIRE_BELL
    bg.rect(fx - 5, fy - 2, 11, 13, OUT); bg.rect(fx - 4, fy - 1, 9, 11, "#8a2a24"); bg.hline(fx - 4, fy - 1, 9, "#b84a3c")
    bg.ellipse(fx - 6, fy - 12, 13, 12, OUT); bg.ellipse(fx - 5, fy - 11, 11, 10, "#b84a3c")
    bg.ellipse(fx - 4, fy - 10, 6, 5, "#e07a5a"); bg.px(fx, fy - 6, "#3a1410")
    micro_text(bg, "FIRE", fx - 7, fy + 2, "#f2e2c0")
    # where the wall meets the floor
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))
    return notices, glows, pivot, drop


def wall_chair(bg, cx, base, seed=0):
    """An oak spindle-back chair standing against the wainscot (waiting for office hours)."""
    w = 16
    x0 = cx - w // 2
    seat = base - 14
    bg.rect(x0 + 1, base - 36, w - 2, 4, OUT); bg.rect(x0 + 2, base - 35, w - 4, 2, OAK_IN[5]); bg.hline(x0 + 2, base - 35, w - 4, OAK_IN[6])
    for sx in range(x0 + 3, x0 + w - 2, 3):
        bg.vline(sx, base - 32, 18, OUT); bg.vline(sx + 1, base - 32, 18, OAK_IN[4])
    bg.rect(x0, seat, w, 4, OUT); bg.rect(x0 + 1, seat + 1, w - 2, 2, OAK_IN[6])
    for lx in (x0 + 1, x0 + w - 3):
        bg.rect(lx, seat + 4, 2, base - seat - 4, OUT); bg.vline(lx, seat + 4, base - seat - 5, OAK_IN[4])
    bg.hline(x0 + 2, base - 5, w - 4, OAK_IN[2])
    bg.rect(x0 - 1, base - 1, w + 2, 1, C("#0d0b16", 0.5))


# ------------------------------------------------------------------------------------- floor
def floor(bg):
    # wear: the paths people take (side door to side door, the front doors up to the board)
    ys, xs = np.mgrid[BASE:H, 0:W].astype(np.float32)
    wear = np.clip(1 - np.abs(ys - 299) / 40, 0, 1) * 0.7 + np.clip(1 - np.abs(xs - 400) / 50, 0, 1) * np.clip((ys - 300) / 80, 0, 1) * 0.6
    encaustic_floor(bg, 0, BASE, W, H - BASE, seed=8, wear=wear)
    tile_border(bg, 16, BASE + 6, W - 32, FLOOR_BOTTOM - BASE - 2, band=7)
    # a shadow where the tiles meet the skirting
    bg.rect(0, BASE, W, 3, C("#0d0b16", 0.4)); bg.rect(0, BASE + 3, W, 2, C("#0d0b16", 0.18))
    # moonlight from the sash windows
    for wx in WINDOWS:
        moon_patch(bg, wx - 22, BASE + 4, 40, 54, slant=-16, strength=0.22)
    # runners
    ry, rh = CROSS_RUNNER
    runner_om(bg, -4, ry, W + 8, rh, seed=2)
    rx, rw = DOWN_RUNNER
    runner_om(bg, rx, ry + rh - 1, rw, H - ry - rh + 4, vertical=True, seed=3)
    bg.rect(rx + 1, ry + rh - 2, rw - 2, 3, "#2e2850")
    # light: the floor lamp, the sconces, the desk, light from the side doors and the front doors
    light_pool(bg, LAMP[0], LAMP[1] + 2, 50, 14, strength=0.26)
    for sx in SCONCES:
        light_pool(bg, sx + 4, BASE + 6, 26, 7, strength=0.14)
    for px_ in PENDANTS:
        light_pool(bg, px_, BASE + 8, 34, 8, strength=0.16)
    for (px_, py_, rx_, ry_) in POOLS:
        light_pool(bg, px_, py_, rx_, ry_, strength=0.12)
    light_pool(bg, DESK[0], DESK[1] + 4, 70, 12, strength=0.10)
    sy, sh = SIDE_DOOR
    spill(bg, 0, sy - 10, 90, sh + 30, "#a8bce8", side="left")
    spill(bg, W - 90, sy - 10, 90, sh + 30, "#f6cf7a", side="right")
    spill(bg, FRONT_DOOR[0] - 20, FLOOR_BOTTOM - 40, FRONT_DOOR[1] + 40, H - FLOOR_BOTTOM + 40, "#8a9ad0",
          steps=((1.0, 0.07), (0.6, 0.06), (0.3, 0.05)), side="bottom")
    # fallen notices, drifting toward the doors in the draught (flat on the floor)
    rng = np.random.default_rng(31)
    for (fx, fy) in [(470, 340), (512, 352), (292, 336), (562, 372), (640, 318), (700, 304), (176, 286), (84, 318),
                     (440, 408), (330, 420), (604, 444), (258, 362)]:
        w_, h_ = int(rng.integers(7, 11)), int(rng.integers(4, 6))
        tint = PAPER_TINTS[int(rng.integers(len(PAPER_TINTS)))]
        bg.rect(fx + 1, fy + 1, w_, h_, C("#140c08", 0.3))
        bg.rect(fx, fy, w_, h_, shade(tint, -0.08)); bg.hline(fx, fy, w_, tint)
        scribble(bg, fx + 1, fy + 2, w_ - 2, C("#2a2a3a", 0.45), seed=int(rng.integers(1e6)), rows=1)
    depth_shade(bg, 0, 410, W, H - 410, steps=3, alpha=0.18)


def walls_at_edges(bg):
    """The side walls seen end-on at the left and right edges, with the doorways to the office and
    the cabinet room; the front wall's cap at the bottom with the courtyard doors."""
    sy, sh = SIDE_DOOR
    for x0, inner in ((0, 9), (W - 10, 0)):
        bg.rect(x0, BASE, 10, FLOOR_BOTTOM - BASE, HALL_GREEN[2])
        bg.vline(x0 + inner, BASE, FLOOR_BOTTOM - BASE, HALL_GREEN[5])
        bg.rect(x0, sy, 10, sh, C("#0d0b16", 0.0))
        # doorway: the opening, oak jambs seen from above at each end
        bg.rect(x0, sy, 10, sh, "#1a1626")
        for jy in (sy - 4, sy + sh):
            bg.rect(x0, jy, 10, 4, OUT); bg.rect(x0 + 1, jy + 1, 8, 2, OAK_IN[4]); bg.hline(x0 + 1, jy + 1, 8, OAK_IN[6])
    # light from beyond each side door
    bg.rect(0, sy, 10, sh, C("#a8bce8", 0.22))
    bg.rect(W - 10, sy, 10, sh, C("#f6cf7a", 0.28))
    # front wall cap with the courtyard doorway
    fy = FLOOR_BOTTOM + 8
    x0, fw = FRONT_DOOR
    for (a, b) in ((0, x0), (x0 + fw, W)):
        bg.rect(a, fy, b - a, H - fy, HALL_GREEN[2]); bg.hline(a, fy, b - a, HALL_GREEN[5]); bg.hline(a, fy + 1, b - a, HALL_GREEN[3])
    for jx in (x0 - 4, x0 + fw):
        bg.rect(jx, fy - 1, 4, H - fy + 1, OUT); bg.rect(jx + 1, fy, 2, H - fy, OAK_IN[4]); bg.vline(jx + 1, fy, H - fy, OAK_IN[6])


def margins(bg):
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.36))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.36))
    bg.rect(0, FLOOR_BOTTOM, W, H - FLOOR_BOTTOM, C("#0d0b16", 0.38))


# ------------------------------------------------------------------------------------- props
def board_face(cv, x, y, w, h, demands, seed=0):
    """The cork face of the WHAT YOU OWE board: everyday office notices, or (demands) the three
    personal sentences pasted over them."""
    cork_surface(cv, x, y, w, h, seed=seed)
    rng = np.random.default_rng(seed)
    if not demands:
        # a big OFFICE HOURS notice in the middle, ordinary paperwork around it
        scatter_notices(cv, x + 1, y, 44, h, seed=seed + 1, titles=["FEES DUE", "KEYS", "SIGN IN"])
        scatter_notices(cv, x + w - 45, y, 44, h, seed=seed + 2, titles=["ROOM 104", "FORMS", "LOST"])
        nx, ny, nw, nh = x + (w - 84) // 2, y + 4, 84, h - 8
        notice_paper(cv, nx, ny, nw, nh, tint="#f2ead2", seed=seed + 3, title=None, pin="#c84a3c", rows=0)
        text(cv, "OFFICE HOURS", nx + 6, ny + 1, "#3a2a26")
        micro_text(cv, "MON-FRI  9 TO 5", nx + (nw - micro_width("MON-FRI  9 TO 5")) // 2, ny + 13, "#5a3a32")
        scribble(cv, nx + 8, ny + 22, nw - 16, C("#2a2a3a", 0.5), seed=seed + 4, rows=max(1, (nh - 24) // 3))
        cv.px(nx + 2, ny + 1, "#3a5aa8"); cv.px(nx + nw - 3, ny + 1, "#3a5aa8")
    else:
        # the old notices torn and pasted over: three strips, each with a red name tag
        scatter_notices(cv, x + 1, y, w - 2, h, seed=seed + 1, density=0.7)
        cv.rect(x, y, w, h, C("#1c120c", 0.35))
        rows = [("JULES", "NEVER DISAPPOINT", 4), ("IMANI", "KEEP EVERY AUDIENCE", -6), ("WALT", "NEED NOBODY", 10)]
        for i, (name, line, dx) in enumerate(rows):
            tag_w = micro_width(name) + 6
            sw = tag_w + text_width(line) + 8
            sx = x + (w - sw) // 2 + dx
            sy = y + 2 + i * 12
            cv.rect(sx + 1, sy + 1, sw, 11, C("#140c08", 0.45))
            cv.rect(sx, sy, sw, 11, "#efe6cc"); cv.hline(sx, sy, sw, "#fff6dc"); cv.hline(sx, sy + 10, sw, "#c8bc9c")
            cv.rect(sx + 2, sy + 2, tag_w, 7, RED_STAMP[2]); cv.hline(sx + 2, sy + 2, tag_w, RED_STAMP[3])
            micro_text(cv, name, sx + 5, sy + 3, "#fff0e0")
            text(cv, line, sx + tag_w + 5, sy + 1, "#3a1c1a")
            cv.rect(sx + sw // 2, sy - 1, 2, 2, "#c84a3c"); cv.px(sx + sw // 2, sy - 1, "#ff8a6a")


def notice_stand(width=180, height=80, demands=False, seed=0):
    """The free-standing hall board: two oak posts on bracket feet, a framed cork board with a gilt
    WHAT YOU OWE header, a stretcher with a ledge of leaflets below."""
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    top = base - height
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 - 6, 3)
    # posts and feet
    for px_ in (ox + 5, ox + width - 10):
        cv.rect(px_ - 1, top + 2, 7, base - top - 5, OUT)
        cv.rect(px_, top + 3, 5, base - top - 7, OAK_IN[3]); cv.vline(px_, top + 3, base - top - 7, OAK_IN[5]); cv.vline(px_ + 4, top + 3, base - top - 7, OAK_IN[1])
        cv.rect(px_ - 6, base - 5, 17, 4, OUT); cv.rect(px_ - 5, base - 5, 15, 3, OAK_IN[3]); cv.hline(px_ - 5, base - 5, 15, OAK_IN[5])
        cv.rect(px_ - 1, top, 7, 4, OUT); cv.rect(px_, top + 1, 5, 2, OAK_IN[5])
    # stretcher and leaflet ledge
    cv.rect(ox + 10, base - 17, width - 20, 4, OUT); cv.rect(ox + 11, base - 16, width - 22, 2, OAK_IN[4]); cv.hline(ox + 11, base - 16, width - 22, OAK_IN[6])
    rng = np.random.default_rng(seed + 9)
    lx = ox + 22
    while lx < ox + width - 30:
        tint = PAPER_TINTS[int(rng.integers(len(PAPER_TINTS)))]
        lw = int(rng.integers(8, 13))
        cv.rect(lx, base - 21, lw, 5, OUT); cv.rect(lx + 1, base - 20, lw - 2, 4, tint); cv.hline(lx + 1, base - 20, lw - 2, shade(tint, 0.3))
        lx += lw + int(rng.integers(3, 10))
    # the board: oak frame, gilt header, cork face
    bx, by, bw, bh = ox + 2, top + 4, width - 4, 58
    oak_frame(cv, bx, by, bw, bh, t=5)
    cv.rect(bx + 5, by + 4, bw - 10, 11, "#1c1622"); cv.hline(bx + 5, by + 4, bw - 10, "#2e2434")
    tw = text_width("WHAT YOU OWE")
    text(cv, "WHAT YOU OWE", bx + (bw - tw) // 2, by + 3, GILT_OM[4])
    board_face(cv, bx + 5, by + 15, bw - 10, bh - 20, demands, seed=seed + 20)
    return cv, cx, base


def pigeonhole_cabinet(width=110, height=95, seed=0):
    """The staff pigeonholes: an oak cabinet of open mail slots (papers, envelopes, a parcel, a few
    empty) with brass name tabs, two cupboard doors below, a wire tray and ledgers on top."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    top = base - height
    rng = np.random.default_rng(seed)
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 3)
    ct = top + 9                                   # top of the carcass (things stand on it)
    # things on top
    cv.rect(ox + 10, ct - 6, 26, 6, OUT); cv.rect(ox + 11, ct - 5, 24, 4, "#3a3444")
    for k in range(4):
        cv.hline(ox + 12, ct - 5 + k, 22, PAPER_TINTS[k])
    for gx in range(ox + 11, ox + 36, 4):
        cv.vline(gx, ct - 6, 6, "#5a5868")
    lx = ox + width - 40
    for i, col in enumerate(("#5a2a2a", "#2a3a5a", "#3a4a2a")):
        cv.rect(lx, ct - 3 - i * 3, 24 - i * 2, 3, OUT); cv.rect(lx + 1, ct - 3 - i * 3, 22 - i * 2, 2, col)
        cv.hline(lx + 1, ct - 3 - i * 3, 22 - i * 2, shade(col, 0.3)); cv.rect(lx + 18 - i * 2, ct - 3 - i * 3, 3, 2, "#e8dcc0")
    # cornice
    cv.rect(ox - 1, ct, width + 2, 6, OUT)
    cv.rect(ox, ct + 1, width, 4, OAK_IN[4]); cv.hline(ox, ct + 1, width, OAK_IN[6]); cv.hline(ox, ct + 4, width, OAK_IN[2])
    # carcass
    cv.rect(ox + 1, ct + 5, width - 2, base - ct - 5, OUT)
    cv.rect(ox + 2, ct + 6, width - 4, base - ct - 8, OAK_IN[3])
    cv.vline(ox + 2, ct + 6, base - ct - 8, OAK_IN[5]); cv.vline(ox + width - 3, ct + 6, base - ct - 8, OAK_IN[1])
    # pigeonholes: 6 x 4
    gx0, gy0, cols, rows, cw, chh = ox + 6, ct + 8, 6, 4, 16, 11
    for r in range(rows):
        for c in range(cols):
            x0, y0 = gx0 + c * cw, gy0 + r * (chh + 3)
            cv.rect(x0, y0, cw - 1, chh, "#1a100c"); cv.rect(x0 + 1, y0, cw - 3, 2, "#120a08")
            cv.vline(x0, y0, chh, "#2a1a12")
            k = rng.random()
            if k < 0.55:      # a stack of papers / letters
                n = int(rng.integers(2, 5))
                for j in range(n):
                    tint = PAPER_TINTS[int(rng.integers(len(PAPER_TINTS)))]
                    pw_ = cw - 4 - int(rng.integers(0, 4))
                    cv.hline(x0 + 2, y0 + chh - 1 - j, pw_, tint)
                cv.hline(x0 + 2, y0 + chh - n, cw - 6, shade(PAPER[3], 0.2))
            elif k < 0.75:    # envelopes leaning
                cv.rect(x0 + 2, y0 + 4, 9, 7, "#e8dcc0"); cv.line(x0 + 2, y0 + 4, x0 + 6, y0 + 7, "#a89a7c"); cv.line(x0 + 10, y0 + 4, x0 + 6, y0 + 7, "#a89a7c")
                cv.px(x0 + 6, y0 + 7, "#b82a26")
            elif k < 0.83:    # a parcel tied with string
                cv.rect(x0 + 2, y0 + 5, 11, 6, "#8a6a44"); cv.hline(x0 + 2, y0 + 5, 11, "#a8845a"); cv.vline(x0 + 7, y0 + 5, 6, "#d8c8a0")
            # brass name tab under each slot
            cv.rect(x0 + 4, y0 + chh + 1, 7, 2, GILT_OM[2]); cv.px(x0 + 4, y0 + chh + 1, GILT_OM[4])
        cv.hline(gx0 - 1, gy0 + r * (chh + 3) + chh, cols * cw, OAK_IN[5])
    # cupboard doors
    dy0 = gy0 + rows * (chh + 3) + 1
    dh = base - 7 - dy0
    for k in range(2):
        dx0 = ox + 6 + k * (width - 12) // 2
        dw = (width - 12) // 2 - 2
        cv.rect(dx0, dy0, dw, dh, OUT); cv.rect(dx0 + 1, dy0 + 1, dw - 2, dh - 2, OAK_IN[4])
        cv.rect(dx0 + 4, dy0 + 4, dw - 8, dh - 8, OAK_IN[3]); cv.hline(dx0 + 4, dy0 + 4, dw - 8, OAK_IN[2]); cv.hline(dx0 + 4, dy0 + dh - 5, dw - 8, OAK_IN[5])
        kx = dx0 + dw - 4 if k == 0 else dx0 + 3
        cv.rect(kx, dy0 + dh // 2 - 1, 2, 2, GILT_OM[4])
    # plinth
    cv.rect(ox, base - 6, width, 6, OUT); cv.rect(ox + 1, base - 5, width - 2, 4, OAK_IN[2]); cv.hline(ox + 1, base - 5, width - 2, OAK_IN[4])
    return cv, ox + width // 2, base


def hand_text(cv, s, x, y, colour, seed=0):
    """Game-font letters with a slightly wandering baseline, like a careful hand."""
    rng = np.random.default_rng(seed)
    off = 0
    for i, ch in enumerate(s):
        if rng.random() < 0.3:
            off = int(np.clip(off + rng.integers(-1, 2), -1, 1))
        text(cv, ch, x + i * 6, y + off, colour)


def directory_easel(width=100, height=62, seed=0):
    """A hand-lettered directory card pinned to a board on an oak easel."""
    cv = Canvas(width + 8, height + 6, seed=seed)
    ox, base = 4, height + 3
    top = base - height
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 - 10, 2)
    # back leg, then the front legs splaying out
    cv.line(cx, top + 30, cx + 2, base - 1, OUT); cv.line(cx + 1, top + 30, cx + 3, base - 1, OAK_IN[2])
    for (x0, x1) in ((ox + 20, ox + 10), (ox + width - 22, ox + width - 12)):
        for d in (-1, 0, 1, 2, 3):
            cv.line(x0 + d, top + 4, x1 + d, base - 1, OUT if d in (-1, 3) else (OAK_IN[6] if d == 0 else OAK_IN[4]))
        cv.rect(x1 - 2, base - 3, 7, 3, OUT); cv.hline(x1 - 1, base - 3, 5, OAK_IN[3])
    # pegs / ledge holding the board
    cv.rect(ox + 6, top + 43, width - 12, 4, OUT); cv.rect(ox + 7, top + 44, width - 14, 2, OAK_IN[5])
    # board with the card
    bx, by, bw, bh = ox + 2, top, width - 4, 44
    oak_frame(cv, bx, by, bw, bh, t=3)
    cv.rect(bx + 3, by + 3, bw - 6, bh - 6, "#2a2a30")
    kx, ky, kw, kh = bx + 4, by + 3, bw - 8, bh - 6
    cv.rect(kx + 1, ky + 1, kw, kh, C("#000000", 0.3))
    cv.rect(kx, ky, kw, kh, "#efe6cc"); cv.hline(kx, ky, kw, "#fff6dc"); cv.hline(kx, ky + kh - 1, kw, "#c8bc9c")
    cv.rect(kx + kw // 2 - 1, ky, 2, 2, "#c84a3c")
    hand_text(cv, "DIRECTORY", kx + (kw - text_width("DIRECTORY")) // 2, ky + 1, "#9a2a24", seed=1)
    cv.hline(kx + 18, ky + 11, kw - 36, C("#9a2a24", 0.7))
    hand_text(cv, "< EMPTY OFFICE", kx + 2, ky + 13, "#2a2a4a", seed=2)
    hand_text(cv, "CABINET ROOM >", kx + kw - 2 - text_width("CABINET ROOM >"), ky + 25, "#2a2a4a", seed=3)
    return cv, cx, base


def info_desk(width=130, height=42, seed=0):
    """The hall's information desk, shut for the night: an oak counter with raised panels and
    OPEN AGAIN / IN THE MORNING lettered in gilt on the front; on top a service bell, a closed
    register, an inkstand and a little stack of forms under a paperweight."""
    cv = Canvas(width + 8, height + 16, seed=seed)
    ox, base = 4, height + 14
    top = base - height
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    # top
    cv.rect(ox - 1, top, width + 2, 8, OUT)
    cv.rect(ox, top + 1, width, 5, OAK_IN[5]); cv.hline(ox, top + 1, width, OAK_IN[6]); cv.hline(ox, top + 5, width, OAK_IN[4])
    cv.hline(ox, top + 6, width, OAK_IN[2])
    for gx in range(ox + 9, ox + width, 23):
        cv.hline(gx, top + 3, 7, OAK_IN[4])
    # front
    fy = top + 7
    cv.rect(ox + 1, fy, width - 2, base - fy, OUT)
    cv.rect(ox + 2, fy, width - 4, base - fy - 1, OAK_IN[3])
    cv.vline(ox + 2, fy, base - fy - 1, OAK_IN[5])
    pw = 96
    px0 = ox + (width - pw) // 2
    for (x0, w_) in ((ox + 5, px0 - ox - 8), (px0, pw), (px0 + pw + 3, ox + width - 5 - px0 - pw - 3)):
        cv.rect(x0, fy + 3, w_, base - fy - 9, OAK_IN[2])
        cv.rect(x0 + 1, fy + 4, w_ - 2, base - fy - 11, OAK_IN[4]); cv.hline(x0 + 1, fy + 4, w_ - 2, OAK_IN[6])
        cv.rect(x0 + 3, fy + 6, w_ - 6, base - fy - 15, OAK_IN[3])
    cv.rect(px0 + 3, fy + 6, pw - 6, base - fy - 15, "#2a1a14")
    text(cv, "OPEN AGAIN", px0 + (pw - text_width("OPEN AGAIN")) // 2, fy + 5, GILT_OM[4])
    text(cv, "IN THE MORNING", px0 + (pw - text_width("IN THE MORNING")) // 2, fy + 15, GILT_OM[3])
    cv.rect(ox + 1, base - 4, width - 2, 4, OUT); cv.rect(ox + 2, base - 4, width - 4, 3, OAK_IN[2]); cv.hline(ox + 2, base - 4, width - 4, OAK_IN[4])
    # on the top
    bxl = ox + 14
    cv.rect(bxl - 1, top - 7, 13, 8, OUT); cv.rect(bxl, top - 6, 11, 6, "#5a2a2a"); cv.hline(bxl, top - 6, 11, "#7a3a34")
    cv.rect(bxl + 1, top - 3, 9, 2, "#e8dcc0"); cv.hline(bxl, top - 1, 11, "#3a1a18")
    bx2 = ox + width - 22
    cv.ellipse(bx2 - 5, top - 6, 11, 7, OUT); cv.ellipse(bx2 - 4, top - 5, 9, 5, GILT_OM[3]); cv.px(bx2 - 2, top - 4, GILT_OM[5])
    cv.rect(bx2, top - 8, 1, 3, GILT_OM[4]); cv.rect(bx2 - 5, top - 1, 11, 1, OUT)
    ix = ox + 40
    cv.rect(ix, top - 3, 14, 3, OUT); cv.rect(ix + 1, top - 3, 12, 2, OAK_IN[5])
    cv.rect(ix + 2, top - 6, 4, 3, "#1a1a2a"); cv.px(ix + 3, top - 6, "#5a5a7a")
    cv.line(ix + 9, top - 3, ix + 12, top - 10, "#e8dcc0"); cv.px(ix + 12, top - 10, "#f2ead6")
    fx = ox + width - 52
    for k in range(4):
        cv.rect(fx + (k % 2), top - 1 - k, 16, 1, PAPER_TINTS[k])
    cv.rect(fx + 5, top - 7, 6, 3, OUT); cv.rect(fx + 6, top - 7, 4, 2, "#5a7a9a"); cv.px(fx + 6, top - 7, "#9ab8d8")
    return cv, ox + width // 2, base


def deacon_bench(width=120, height=32, seed=0):
    """An oak deacon's bench: spindle back between a top rail and the seat, scrolled arms, turned
    legs; a red scarf somebody forgot over one arm."""
    cv = Canvas(width + 8, height + 6, seed=seed)
    ox, base = 4, height + 3
    top = base - height
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 3)
    seat = base - 13
    # back: top rail and spindles
    cv.rect(ox + 4, top, width - 8, 5, OUT); cv.rect(ox + 5, top + 1, width - 10, 3, OAK_IN[5]); cv.hline(ox + 5, top + 1, width - 10, OAK_IN[6])
    for sx in range(ox + 9, ox + width - 8, 5):
        cv.rect(sx - 1, top + 5, 3, seat - top - 5, OUT); cv.vline(sx, top + 5, seat - top - 5, OAK_IN[4])
        cv.px(sx, top + 9, OAK_IN[6])
    # arms
    for ax, d in ((ox, 1), (ox + width - 8, -1)):
        cv.rect(ax, top + 6, 8, 3, OUT); cv.rect(ax + 1, top + 7, 6, 1, OAK_IN[5])
        cv.rect(ax + (1 if d > 0 else 5), top + 8, 3, seat - top - 8, OUT); cv.vline(ax + (2 if d > 0 else 6), top + 8, seat - top - 8, OAK_IN[4])
    # seat and apron
    cv.rect(ox, seat, width, 5, OUT); cv.rect(ox + 1, seat + 1, width - 2, 2, OAK_IN[6]); cv.hline(ox + 1, seat + 3, width - 2, OAK_IN[4])
    cv.rect(ox + 3, seat + 5, width - 6, 3, OAK_IN[2]); cv.hline(ox + 3, seat + 5, width - 6, OAK_IN[3])
    # legs
    for lx in (ox + 3, ox + width // 2 - 1, ox + width - 6):
        cv.rect(lx, seat + 5, 4, base - seat - 5, OUT); cv.rect(lx + 1, seat + 5, 2, base - seat - 6, OAK_IN[4])
        cv.px(lx + 1, seat + 9, OAK_IN[6])
    # a forgotten scarf over the right arm
    sx0 = ox + width - 12
    cv.rect(sx0, top + 4, 7, 4, OUT); cv.rect(sx0 + 1, top + 5, 5, 2, "#a8323a")
    cv.rect(sx0 + 1, top + 7, 4, 12, OUT); cv.rect(sx0 + 2, top + 7, 2, 11, "#a8323a"); cv.vline(sx0 + 2, top + 8, 9, "#c84a4a")
    for fy in range(top + 18, top + 21):
        cv.px(sx0 + 2, fy, "#e8c0a0"); cv.px(sx0 + 3, fy + 1, "#e8c0a0")
    return cv, ox + width // 2, base


def globe_standard_lamp(height=68):
    """An indoor brass standard lamp: weighted round foot, a column with turned knops, a milk-glass
    globe on a brass gallery. The globe's centre is ~5px below the top (the room's point light)."""
    w = 22
    cv = Canvas(w, height + 6)
    cx, base = w // 2, height + 3
    top = base - height
    ground_shadow(cv, cx, base, 8, 2)
    cv.ellipse(cx - 7, base - 5, 15, 6, OUT); cv.ellipse(cx - 6, base - 5, 13, 5, GILT_OM[2]); cv.hline(cx - 4, base - 5, 9, GILT_OM[4])
    cv.rect(cx - 2, top + 14, 4, base - top - 18, OUT)
    cv.vline(cx - 1, top + 14, base - top - 18, GILT_OM[4]); cv.vline(cx, top + 14, base - top - 18, GILT_OM[2])
    for ky in (top + 24, top + 40, base - 12):
        cv.rect(cx - 3, ky, 6, 3, OUT); cv.rect(cx - 2, ky + 1, 4, 1, GILT_OM[5])
    globe_pendant(cv, cx, top + 6, chain_top=top + 13, lit=True, r=5)
    cv.rect(cx - 3, top + 11, 6, 3, OUT); cv.rect(cx - 2, top + 11, 4, 2, GILT_OM[3])
    return cv, cx, base


# ------------------------------------------------------------------------------------- build
def stir_frames(bg, notices, out, res, pick, seed=0):
    """Blink textures for notices lifting in the draught: the paper's lower corner curls up and the
    cork's shadow shows under it."""
    rng = np.random.default_rng(seed)
    layers = []
    chosen = [notices[i] for i in pick if i < len(notices)]
    n = len(chosen)
    for k, (x, y, w, h, tint) in enumerate(chosen):
        tex = Canvas(w + 2, h + 2)
        tex.a[:] = bg.a[y:y + h + 2, x:x + w + 2]
        lift = 4
        # lifted corner: the bottom rows shift up-right, cork shadow below
        tex.rect(0, h - lift, w, lift, C("#3a2414", 1.0))
        tex.rect(1, h - lift + 1, w, lift, C("#4e3420", 1.0))
        tex.poly([(w // 3, h - lift), (w, h - lift - 3), (w, h - lift + 2), (w // 3 + 2, h - lift + 1)], shade(tint, -0.22))
        tex.hline(w // 3, h - lift - 1, w - w // 3, shade(tint, 0.2))
        name = f"stir-{k}.png"
        tex.save(os.path.join(out, name))
        pat = ["0"] * (n * 3)
        pat[k * 3] = "1"
        if rng.random() < 0.5:
            pat[k * 3 + 1] = "1"
        layers.append({"kind": "blink", "pattern": "".join(pat), "rate": 2.5, "texture": res + name, "x": x, "y": y})
    return layers


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    notices, glows, pivot, drop = back_wall(bg)
    floor(bg)
    walls_at_edges(bg)
    margins(bg)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, name=None, flag=None, flag_made=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        if flag:
            fs, _, _ = flag_made
            fname = name.replace(".png", f"-{flag}.png")
            fs.save(os.path.join(out, fname))
            entry.update({"flag": flag, "flag_texture": res + fname})
        props[str(index)] = entry

    # the WHAT YOU OWE board changes once the notices have been read
    save(0, notice_stand(180, 80, demands=False, seed=7), flag="notice_limits", flag_made=notice_stand(180, 80, demands=True, seed=7))
    save(1, pigeonhole_cabinet(110, 95, seed=11))
    save(2, directory_easel(100, 62, seed=3))
    save(3, info_desk(130, 42, seed=5))
    save(4, deacon_bench(120, 32, seed=2))
    save(5, globe_standard_lamp(68))

    layers = stir_frames(bg, notices, out, res, pick=[1, 4, 7, 10, 13], seed=3)
    # the clock's pendulum swinging in its drop window
    from lib_norlin import pendulum_frames
    frames = pendulum_frames(6, swing=2)
    for k, (fcv, fox) in enumerate(frames):
        name = f"pendulum-{k}.png"
        fcv.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": ["1000", "0101", "0010"][k], "rate": 2.0, "texture": res + name,
                       "x": pivot[0] - fox, "y": pivot[1]})
    layers += [
        {"kind": "twinkle", "points": [[gx, gy, "fde9b6", 1] for gx, gy in glows] + [[LAMP[0], LAMP[1] - 63, "fff0c4", 2]],
         "rate": 1.2, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 16, "rect": [190, 30, 420, 140], "speed": [2, 1], "color": "c8d4f0"},
        {"kind": "particles", "style": "wind", "count": 5, "rect": [40, 250, 720, 190], "speed": [16, -2], "color": "c8d4f0"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": [],
        "fauna": [
            {"kind": "loose_page", "x": 120, "y": 250, "fly": 11.0, "rate": 5.0},
            {"kind": "lamp_moth", "x": LAMP[0] + 2, "y": LAMP[1] - 66, "range": 6, "speed": 2.1, "rate": 9.0},
            {"kind": "umc2_mouse", "x": 700, "y": BASE + 7, "range": 26, "speed": 0.35, "rate": 4.0},
        ],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(paths.PROJECT)
