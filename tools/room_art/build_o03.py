"""Old Main empty office (O03): the first purpose.

Back wall: faded ochre plaster under a plain cornice and an oak picture rail, frame-and-panel oak
dado. Darker rectangles and empty hooks show where pictures hung for decades; a calendar left on an
old month, a stopped clock. A chalkboard still carries the first purpose, half erased: GATHER ALL,
a ring of little figures with arrows pointing in to one centre, DO NOT CLOSE. On the right the
quiet window - a broad triple sash with a wooden blind half down, the campus and the Flatirons
under the moon, a built-in window seat below - and an oak filing cabinet with one drawer pulled
open and empty, an empty coat stand. At the left the narrow service door to the cabinet room (shut
until the original directory has been read, booth_origin; then it stands ajar on lamplight).
Floor: worn oak boards with the unfaded outlines of furniture taken away, a faded green rug under
the big desk, the moonlight laid across the boards in window panes reaching the inspect spot, a
runner from the service door, lamplight.
Props: the big partners' desk with the open CEREMONY DIRECTORY, the first recording on a reel-to-reel
machine and a lit banker's lamp; a writing table with Jules's phone glowing (an unread message; once
read, family_message_read, a reply sits under it); a glass-fronted bookcase almost cleared; a
bench half under a dust sheet; a standard lamp with a pleated shade."""
import paths
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
from lib_oldmain import (plaster_om, cornice_om, panel_wainscot, sash_window, night_glass, radiator, oak_frame, chalkboard,
                         venetian_blind, ghost_frame, ghost_outline, oak_boards, reel_recorder, banker_lamp_om, schoolhouse_clock,
                         runner_om, spill, notice_paper, OFFICE_OCHRE, OAK_IN, GILT_OM, CREAM_TRIM, PAPER_TINTS, RUG_GREEN, BOARDS,
                         LEATHER, STEEL_OM, OXBLOOD, INK)

ROOM = "O03"
W, H = 800, 480
BASE = 142
WALK = (20, 142, 760, 314)
FLOOR_BOTTOM = WALK[1] + WALK[3]
DADO_Y = 100
RAIL_Y = 28                                # picture rail
WINDOW = (522, 22, 96, 78)                 # glass box of the triple window: x, y, w, h
SEAT_Y = 112                               # top of the built-in window seat
DOOR = (78, 34, 74)                        # service door: left x, width, height (bottom at BASE)
BOARD = (296, 38, 156, 64)                 # chalkboard
CABINET = (676, 62, 44)                    # filing cabinet: x, top, width (stands on BASE)
CLOCK = (228, 40)
CALENDAR = (472, 50)
GHOSTS = [(170, 52, 40, 30), (128, 40, 26, 34), (650, 36, 22, 18), (734, 44, 30, 40)]
LAMP = (115, 350)
DESK = (410, 329)
SMALL_DESK = (630, 314)
RUG = (268, 286, 288, 92)
HALL_DOOR = (692, 66)                      # front doorway to the hall: left x, width


# ---------------------------------------------------------------------------- wall
def service_door(cv, x, w, h, ajar=False):
    """A plain oak service door in a moulded casing with a brass CABINET plate; ajar, it swings in
    on lamplight from the cabinet room."""
    top = BASE - h
    cv.rect(x - 5, top - 5, w + 10, h + 5, OUT)
    cv.rect(x - 4, top - 4, w + 8, h + 4, OAK_IN[4]); cv.vline(x - 4, top - 4, h + 4, OAK_IN[6]); cv.vline(x + w + 3, top - 4, h + 4, OAK_IN[2])
    cv.hline(x - 4, top - 4, w + 8, OAK_IN[6])
    cv.rect(x - 6, top - 7, w + 12, 3, OUT); cv.hline(x - 5, top - 6, w + 10, CREAM_TRIM[4])
    if ajar:
        cv.rect(x, top, w, h, OXBLOOD[3])
        cv.rect(x, top, w, h, C("#f6cf7a", 0.22))
        cv.rect(x + 4, top + 10, 12, 18, C("#fde9b6", 0.18))
        cv.rect(x, BASE - 10, w, 10, OXBLOOD[2]); cv.hline(x, BASE - 10, w, OXBLOOD[5])
        # the leaf swung in, seen nearly edge-on
        cv.poly([(x + w - 10, top), (x + w, top + 3), (x + w, BASE), (x + w - 10, BASE - 3)], OAK_IN[3])
        cv.vline(x + w - 10, top, h - 3, OAK_IN[5]); cv.rect(x + w - 8, top + 38, 2, 3, GILT_OM[4])
    else:
        cv.rect(x, top, w, h, OAK_IN[3]); cv.vline(x, top, h, OAK_IN[5]); cv.vline(x + w - 1, top, h, OAK_IN[1])
        for (py_, ph) in ((top + 5, 30), (top + 40, 28)):
            cv.rect(x + 4, py_, w - 8, ph, OAK_IN[2]); cv.rect(x + 5, py_ + 1, w - 10, ph - 2, OAK_IN[4])
            cv.rect(x + 7, py_ + 3, w - 14, ph - 6, OAK_IN[3]); cv.hline(x + 5, py_ + 1, w - 10, OAK_IN[6])
        cv.rect(x + w - 7, top + 38, 3, 3, GILT_OM[3]); cv.px(x + w - 7, top + 38, GILT_OM[5])
        cv.rect(x + w - 6, top + 42, 1, 3, "#1a1414")
    pw = micro_width("CABINET") + 4
    cv.rect(x + (w - pw) // 2, top - 13, pw, 7, GILT_OM[2]); cv.hline(x + (w - pw) // 2, top - 13, pw, GILT_OM[4])
    micro_text(cv, "CABINET", x + (w - pw) // 2 + 2, top - 12, "#3a2a14")


def triple_window(bg):
    """The quiet window: three round-headed sashes under one moulded head, the blind half down, a
    deep sill and the built-in window seat with its cushion below."""
    x, y, w, h = WINDOW
    sw = (w - 8) // 3
    for k in range(3):
        sx = x + k * (sw + 4)
        sash_window(bg, sx, y, sw, h, seed=50 + k, moon=(sx + 18, y + 22, 5) if k == 2 else None)
    # one moulded head over all three
    bg.rect(x - 9, y - 7, w + 18, 5, OUT); bg.rect(x - 8, y - 6, w + 16, 3, CREAM_TRIM[3]); bg.hline(x - 8, y - 6, w + 16, CREAM_TRIM[5])
    venetian_blind(bg, x - 2, y + 2, w + 4, 22)
    # window seat
    bg.rect(x - 14, SEAT_Y, w + 28, BASE - SEAT_Y, OUT)
    bg.rect(x - 13, SEAT_Y + 1, w + 26, 6, "#3e5a4e"); bg.hline(x - 13, SEAT_Y + 1, w + 26, "#5a7a6a"); bg.hline(x - 13, SEAT_Y + 6, w + 26, "#2a3e36")
    for bx in range(x - 9, x + w + 10, 24):
        bg.vline(bx, SEAT_Y + 2, 4, "#2e463c")
    panel_wainscot(bg, x - 13, SEAT_Y + 7, w + 26, BASE - SEAT_Y - 7, pal=OAK_IN, panel=26)
    # a dried-out plant and a forgotten mug on the seat
    bg.rect(x + 4, SEAT_Y - 6, 8, 6, OUT); bg.rect(x + 5, SEAT_Y - 5, 6, 5, "#8a4a30"); bg.hline(x + 5, SEAT_Y - 5, 6, "#a85a3a")
    for (dx, dy) in ((-2, -10), (0, -12), (3, -11), (5, -9), (7, -12)):
        bg.line(x + 8, SEAT_Y - 6, x + 8 + dx, SEAT_Y - 6 + dy, "#7a6a3a")
    bg.rect(x + w - 16, SEAT_Y - 5, 6, 5, OUT); bg.rect(x + w - 15, SEAT_Y - 4, 4, 4, "#d8d0c0"); bg.vline(x + w - 10, SEAT_Y - 3, 2, "#d8d0c0")


def filing_cabinet(bg, x, top, w):
    """A four-drawer oak filing cabinet against the wall, the second drawer pulled out and empty."""
    h = BASE - top
    bg.rect(x - 1, top - 1, w + 2, h + 1, OUT)
    bg.rect(x, top, w, h, OAK_IN[3]); bg.vline(x, top, h, OAK_IN[5]); bg.vline(x + w - 1, top, h, OAK_IN[1])
    bg.rect(x - 2, top - 3, w + 4, 3, OAK_IN[5]); bg.hline(x - 2, top - 3, w + 4, OAK_IN[6])
    dh = (h - 6) // 4
    for k in range(4):
        dy = top + 3 + k * dh
        if k == 1:
            bg.rect(x - 3, dy - 2, w + 6, dh + 3, OUT)
            bg.rect(x - 2, dy - 1, w + 4, 4, OAK_IN[1])
            bg.rect(x - 2, dy + 3, w + 4, dh - 2, OAK_IN[4]); bg.hline(x - 2, dy + 3, w + 4, OAK_IN[6])
            bg.rect(x + w // 2 - 5, dy + 6, 10, 3, GILT_OM[3]); bg.rect(x + w // 2 - 4, dy + 7, 8, 1, GILT_OM[1])
        else:
            bg.rect(x + 3, dy, w - 6, dh - 2, OAK_IN[2]); bg.rect(x + 4, dy + 1, w - 8, dh - 4, OAK_IN[4])
            bg.rect(x + w // 2 - 6, dy + 2, 12, 5, OAK_IN[1]); bg.rect(x + w // 2 - 5, dy + 3, 10, 3, "#d8ccb0")
            bg.rect(x + w // 2 - 4, dy + dh - 6, 8, 2, GILT_OM[3])


def coat_stand(bg, x):
    bg.rect(x - 1, 46, 3, BASE - 50, OUT); bg.vline(x, 46, BASE - 50, OAK_IN[5])
    for d in (-1, 1):
        bg.line(x, 50, x + d * 7, 44, OUT); bg.line(x, 51, x + d * 6, 46, OAK_IN[5])
        bg.line(x, BASE - 4, x + d * 8, BASE - 1, OUT)
    bg.rect(x - 2, 43, 5, 4, OUT); bg.rect(x - 1, 44, 3, 2, OAK_IN[6])
    # one empty wire hanger
    bg.line(x + 6, 46, x + 1, 54, "#8a8e96"); bg.line(x + 6, 46, x + 11, 54, "#8a8e96"); bg.hline(x + 1, 54, 11, "#8a8e96")


def calendar(bg, x, y):
    bg.rect(x - 1, y - 1, 20, 26, OUT); bg.rect(x, y, 18, 24, "#ece2c6")
    bg.rect(x, y, 18, 7, "#9a2a24"); micro_text(bg, "OCT", x + 3, y + 1, "#f2e6c8")
    for r in range(4):
        for c in range(5):
            bg.px(x + 2 + c * 3, y + 10 + r * 3, "#5a4a3a")
    bg.line(x + 4, y + 12, x + 7, y + 15, "#b82a26")
    bg.rect(x + 8, y - 3, 2, 3, GILT_OM[3])


def back_wall(bg):
    plaster_om(bg, 0, 10, W, DADO_Y - 10, pal=OFFICE_OCHRE, seed=33, shadow_top=6, cracks=0, body=(5, 6))
    cornice_om(bg, 0, -3, W, ceiling=("#1a1620", "#241e28", "#2e2632"))
    # faded paint: unfaded rectangles where pictures hung, the picture rail with its hooks
    for (gx, gy, gw, gh) in GHOSTS:
        ghost_frame(bg, gx, gy, gw, gh, OFFICE_OCHRE[5], rail_y=RAIL_Y)
    bg.rect(0, RAIL_Y, W, 3, OAK_IN[3]); bg.hline(0, RAIL_Y, W, OAK_IN[6]); bg.hline(0, RAIL_Y + 2, W, OAK_IN[1])
    panel_wainscot(bg, 0, DADO_Y, W, BASE - DADO_Y, pal=OAK_IN, panel=34)
    # the service door, the clock that stopped, the chalkboard, the calendar
    x, w, h = DOOR
    service_door(bg, x, w, h, ajar=False)
    schoolhouse_clock(bg, CLOCK[0], CLOCK[1], hour=4, minute=10)
    chalkboard(bg, *BOARD, seed=4)
    calendar(bg, *CALENDAR)
    # the quiet window, the filing cabinet, the coat stand
    triple_window(bg)
    filing_cabinet(bg, *CABINET)
    coat_stand(bg, 752)
    # a radiator under the clock, a light switch by the door
    radiator(bg, 170, 112, 36, 24)
    bg.rect(124, 76, 5, 8, OUT); bg.rect(125, 77, 3, 6, "#d8ccb0"); bg.px(126, 79, "#3a2a26")
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))


# ---------------------------------------------------------------------------- floor
def floor(bg):
    oak_boards(bg, 0, BASE, W, H - BASE, seed=12)
    bg.rect(0, BASE, W, 3, C("#0d0b16", 0.45)); bg.rect(0, BASE + 3, W, 2, C("#0d0b16", 0.2))
    # where furniture stood: a long table, a cabinet, a sofa, a second desk
    for (gx, gy, gw, gh) in ((150, 384, 96, 22), (560, 226, 64, 14), (40, 300, 26, 40), (470, 410, 70, 18), (300, 190, 40, 14)):
        ghost_outline(bg, gx, gy, gw, gh)
    # the faded rug under the big desk
    rx, ry, rw, rh = RUG
    bg.rect(rx, ry, rw, rh, RUG_GREEN[0])
    bg.rect(rx + 1, ry + 1, rw - 2, rh - 2, RUG_GREEN[4])
    bg.rect(rx + 4, ry + 4, rw - 8, rh - 8, RUG_GREEN[1])
    bg.rect(rx + 6, ry + 6, rw - 12, rh - 12, RUG_GREEN[2])
    for k in range(rx + 10, rx + rw - 10, 12):
        bg.rect(k, ry + 2, 4, 2, RUG_GREEN[5]); bg.rect(k + 3, ry + rh - 4, 4, 2, RUG_GREEN[5])
    cxr, cyr = rx + rw // 2, ry + rh // 2 + 4
    bg.poly([(cxr, cyr - 22), (cxr + 70, cyr), (cxr, cyr + 22), (cxr - 70, cyr)], RUG_GREEN[3])
    bg.poly([(cxr, cyr - 14), (cxr + 44, cyr), (cxr, cyr + 14), (cxr - 44, cyr)], RUG_GREEN[1])
    bg.poly([(cxr, cyr - 6), (cxr + 18, cyr), (cxr, cyr + 6), (cxr - 18, cyr)], RUG_GREEN[4])
    for fx in range(rx + 2, rx + rw - 1, 3):
        bg.vline(fx, ry - 3, 3, "#b4a480"); bg.vline(fx, ry + rh, 3, "#b4a480")
    rng = np.random.default_rng(2)
    for _ in range(40):          # threadbare where people stood at the desk
        tx, ty = int(rng.integers(cxr - 60, cxr + 60)), int(rng.integers(ry + rh - 26, ry + rh - 6))
        bg.rect(tx, ty, int(rng.integers(2, 5)), 1, RUG_GREEN[3])
    # a narrow runner from the service door to its mat
    x, w, h = DOOR
    runner_om(bg, x + 2, BASE, w - 4, 82, vertical=True, pal=("#1e0e12", "#341418", "#481a20", "#5a2026", "#7a3234", "#8c3e3c"), seed=4, motif=16)
    # moonlight from the triple window across the boards, sashes and blind slats in it
    wx, wy, ww, wh = WINDOW
    for i, f in enumerate((1.0, 0.8)):
        a = 0.10 + 0.06 * i
        x0 = wx - 10 + int((1 - f) * 20)
        bg.poly([(x0, BASE + 2), (x0 + int(ww * f), BASE + 2), (x0 + int(ww * f) - 34, 236), (x0 - 34, 236)], C("#b4c4f0", a))
    for k in range(1, 3):
        mx_ = wx - 10 + k * ww // 3
        bg.poly([(mx_ - 1, BASE + 2), (mx_ + 3, BASE + 2), (mx_ - 31, 236), (mx_ - 35, 236)], C("#0d0b16", 0.12))
    # lamplight: the standard lamp, the banker's lamp on the big desk, Jules's phone (cool)
    light_pool(bg, LAMP[0], LAMP[1] + 2, 52, 15, strength=0.26)
    light_pool(bg, DESK[0] - 50, DESK[1] + 6, 90, 18, strength=0.16)
    light_pool(bg, SMALL_DESK[0], SMALL_DESK[1] + 4, 44, 10, color="#a8d0f0", strength=0.12)
    # the doorway to the hall at the front right
    x0, fw = HALL_DOOR
    spill(bg, x0 - 20, FLOOR_BOTTOM - 50, fw + 40, H - FLOOR_BOTTOM + 50, "#f6cf7a",
          steps=((1.0, 0.05), (0.6, 0.05), (0.3, 0.05)), side="bottom")
    # a few things left on the floor: a paperclip chain, a fallen index card, a rubber band
    for (fx, fy) in ((248, 260), (512, 404), (178, 330), (604, 372)):
        bg.rect(fx, fy, 7, 4, "#e8dcc0"); bg.hline(fx, fy, 7, "#fff6dc"); bg.hline(fx + 1, fy + 2, 5, C("#3a3a5a", 0.5))
    bg.rect(356, 446, 4, 2, "#a8323a")
    depth_shade(bg, 0, 410, W, H - 410, steps=3, alpha=0.2)


def front_and_margins(bg):
    fy = FLOOR_BOTTOM + 8
    x0, fw = HALL_DOOR
    for (a, b) in ((0, x0), (x0 + fw, W)):
        bg.rect(a, fy, b - a, H - fy, OFFICE_OCHRE[3]); bg.hline(a, fy, b - a, OFFICE_OCHRE[6]); bg.hline(a, fy + 1, b - a, OFFICE_OCHRE[4])
    for jx in (x0 - 4, x0 + fw):
        bg.rect(jx, fy - 1, 4, H - fy + 1, OUT); bg.rect(jx + 1, fy, 2, H - fy, OAK_IN[4]); bg.vline(jx + 1, fy, H - fy, OAK_IN[6])
    for x0_, inner in ((0, 9), (W - 10, 0)):
        bg.rect(x0_, BASE, 10, FLOOR_BOTTOM - BASE, OFFICE_OCHRE[2]); bg.vline(x0_ + inner, BASE, FLOOR_BOTTOM - BASE, OFFICE_OCHRE[5])
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.36))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.36))
    bg.rect(0, FLOOR_BOTTOM, W, H - FLOOR_BOTTOM, C("#0d0b16", 0.38))


# ---------------------------------------------------------------------------- props
def partners_desk(width=210, height=52, angle=0.0, seed=0, items=True):
    """The big partners' desk: green leather top, two drawer pedestals and a kneehole; on it the
    open CEREMONY DIRECTORY ledger with its red ribbon, the first recording on an upright
    reel-to-reel machine, a lit banker's lamp, index cards and a typed card reading VAL."""
    cv = Canvas(width + 8, height + 26, seed=seed)
    ox, base = 4, height + 24
    top = base - height
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    # top
    cv.rect(ox - 1, top, width + 2, 10, OUT)
    cv.rect(ox, top + 1, width, 7, OAK_IN[5]); cv.hline(ox, top + 1, width, OAK_IN[6])
    cv.rect(ox + 6, top + 2, width - 12, 4, "#2a4a3a"); cv.hline(ox + 6, top + 2, width - 12, "#3a6a50")
    cv.hline(ox, top + 8, width, OAK_IN[2])
    # front: pedestals and kneehole
    fy = top + 9
    cv.rect(ox + 1, fy, width - 2, base - fy, OUT)
    cv.rect(ox + 2, fy, width - 4, base - fy - 1, OAK_IN[3]); cv.vline(ox + 2, fy, base - fy - 1, OAK_IN[5])
    pw = 64
    for px_ in (ox + 5, ox + width - 5 - pw):
        for k in range(3):
            dy = fy + 3 + k * 13
            cv.rect(px_, dy, pw, 11, OAK_IN[2]); cv.rect(px_ + 1, dy + 1, pw - 2, 9, OAK_IN[4]); cv.hline(px_ + 1, dy + 1, pw - 2, OAK_IN[6])
            cv.rect(px_ + pw // 2 - 4, dy + 4, 8, 2, GILT_OM[3]); cv.px(px_ + pw // 2 - 4, dy + 4, GILT_OM[5])
    kx0, kx1 = ox + 5 + pw + 4, ox + width - 9 - pw
    cv.rect(kx0, fy + 3, kx1 - kx0, 10, OAK_IN[2]); cv.rect(kx0 + 1, fy + 4, kx1 - kx0 - 2, 8, OAK_IN[4]); cv.hline(kx0 + 1, fy + 4, kx1 - kx0 - 2, OAK_IN[6])
    cv.rect(kx0 + (kx1 - kx0) // 2 - 4, fy + 7, 8, 2, GILT_OM[3])
    cv.rect(kx0, fy + 15, kx1 - kx0, base - fy - 18, OAK_IN[0])
    cv.rect(kx0 + 3, fy + 16, kx1 - kx0 - 6, base - fy - 21, OAK_IN[1])
    cv.rect(kx0 + 3, fy + 16, kx1 - kx0 - 6, 3, "#120a08")
    cv.vline(kx0, fy + 15, base - fy - 18, OAK_IN[2]); cv.vline(kx1 - 1, fy + 15, base - fy - 18, OAK_IN[2])
    cv.rect(ox + 1, base - 4, width - 2, 4, OUT); cv.rect(ox + 2, base - 4, width - 4, 3, OAK_IN[2])
    if not items:
        return cv, ox + width // 2, base
    # on the desk: the banker's lamp (left), the ledger (centre), the recorder (right)
    banker_lamp_om(cv, ox + 22, top + 4, lit=True)
    lx, ly, lw, lh = ox + 58, top - 10, 60, 13
    cv.rect(lx - 1, ly - 1, lw + 2, lh + 3, OUT)
    cv.rect(lx, ly + lh - 1, lw, 3, "#5a2a22")
    for (px_, pw_) in ((lx, lw // 2), (lx + lw // 2, lw // 2)):
        cv.rect(px_, ly, pw_, lh, "#ece2c6"); cv.hline(px_, ly, pw_, "#fff6dc")
        for yy in range(ly + 3, ly + lh - 1, 2):
            cv.hline(px_ + 2, yy, pw_ - 4, C("#5a4a3a", 0.45))
    cv.vline(lx + lw // 2, ly, lh, "#a89a7c")
    micro_text(cv, "VAL", lx + 4, ly + 2, "#7a2a24")
    cv.vline(lx + lw // 2 + 6, ly + lh - 1, 6, "#b82a26"); cv.px(lx + lw // 2 + 7, ly + lh + 4, "#b82a26")
    reel_recorder(cv, ox + width - 62, top - 19, w=44, h=22, angle=0.4 + angle, lit=True)
    # index cards and a typed card standing against the recorder
    cv.rect(ox + 128, top - 3, 12, 4, OUT); cv.rect(ox + 129, top - 3, 10, 3, "#e8dcc0"); cv.hline(ox + 129, top - 3, 10, "#fff6dc")
    cv.rect(ox + 36, top - 1, 14, 3, PAPER_TINTS[2]); cv.rect(ox + 38, top - 2, 14, 2, PAPER_TINTS[0])
    return cv, ox + width // 2, base


def phone_table(width=120, height=38, replied=False, seed=0):
    """A slender writing table with Jules's phone lying face up and glowing: an unread message (a
    red dot), or once read, a reply under Mom's message. A paper cup of cold coffee, a pencil."""
    cv = Canvas(width + 8, height + 12, seed=seed)
    ox, base = 4, height + 10
    top = base - height
    ground_shadow(cv, ox + width // 2, base, width // 2 - 4, 2)
    cv.rect(ox - 1, top, width + 2, 7, OUT)
    cv.rect(ox, top + 1, width, 4, OAK_IN[5]); cv.hline(ox, top + 1, width, OAK_IN[6]); cv.hline(ox, top + 5, width, OAK_IN[2])
    cv.rect(ox + 3, top + 7, width - 6, 6, OUT); cv.rect(ox + 4, top + 7, width - 8, 5, OAK_IN[3])
    cv.rect(ox + width // 2 - 14, top + 8, 28, 3, OAK_IN[4]); cv.rect(ox + width // 2 - 2, top + 9, 4, 1, GILT_OM[3])
    for lx in (ox + 5, ox + width - 9):
        cv.rect(lx, top + 13, 4, base - top - 13, OUT); cv.rect(lx + 1, top + 13, 2, base - top - 14, OAK_IN[4])
    # the phone and its glow
    px_, py_ = ox + width // 2 + 6, top - 2
    for rr, a in ((12, 0.06), (8, 0.1)):
        cv.ellipse(px_ + 4 - rr, py_ - rr // 2, rr * 2, rr, C("#a8d0f0", a))
    cv.rect(px_ - 1, py_ - 4, 11, 6, OUT)
    cv.rect(px_, py_ - 3, 9, 4, "#8ac0e8"); cv.hline(px_, py_ - 3, 9, "#c8e4f8")
    cv.rect(px_ + 1, py_ - 2, 5, 1, "#f2f6fa")
    if replied:
        cv.rect(px_ + 3, py_ - 1, 5, 1, "#3a8a5a")
    else:
        cv.px(px_ + 8, py_ - 3, "#e04a3a")
    # coffee and pencil
    cx_ = ox + 22
    cv.rect(cx_ - 1, top - 7, 8, 8, OUT); cv.rect(cx_, top - 6, 6, 7, "#e8dcc0"); cv.rect(cx_, top - 3, 6, 2, "#8a3a2a"); cv.hline(cx_, top - 6, 6, "#3a2418")
    cv.line(ox + 40, top + 1, ox + 52, top - 1, "#d8a83a"); cv.px(ox + 52, top - 1, "#2a2a2a")
    return cv, ox + width // 2, base


def barrister_bookcase(width=110, height=108, seed=0):
    """A glass-fronted barrister bookcase in three stacked sections, nearly cleared: a few box
    files, an archive box marked VAL, a fallen book; a dusty globe on top."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    top = base - height
    rng = np.random.default_rng(seed)
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 3)
    ct = top + 14
    # globe on top
    gx = ox + 24
    cv.rect(gx - 3, ct - 3, 7, 3, OUT); cv.rect(gx - 2, ct - 3, 5, 2, GILT_OM[2])
    cv.ellipse(gx - 7, ct - 17, 15, 15, OUT); cv.ellipse(gx - 6, ct - 16, 13, 13, "#5a7a8a")
    cv.ellipse(gx - 4, ct - 14, 6, 5, "#8a9a6a"); cv.rect(gx + 1, ct - 9, 4, 3, "#8a9a6a"); cv.px(gx - 4, ct - 14, "#b4c4c8")
    cv.line(gx - 7, ct - 9, gx + 1, ct - 18, GILT_OM[3])
    cv.rect(ox + 60, ct - 4, 30, 4, OUT); cv.rect(ox + 61, ct - 4, 28, 3, "#b49a6a"); cv.hline(ox + 61, ct - 4, 28, "#d8bc8a")
    # carcass and three glazed sections
    cv.rect(ox - 1, ct, width + 2, 5, OUT); cv.rect(ox, ct + 1, width, 3, OAK_IN[5]); cv.hline(ox, ct + 1, width, OAK_IN[6])
    cv.rect(ox + 1, ct + 5, width - 2, base - ct - 5, OUT)
    cv.rect(ox + 2, ct + 5, width - 4, base - ct - 7, OAK_IN[3])
    sec_h = (base - ct - 14) // 3
    for k in range(3):
        sy = ct + 7 + k * sec_h
        cv.rect(ox + 5, sy, width - 10, sec_h - 4, "#140c0a")
        cv.rect(ox + 6, sy + 1, width - 12, sec_h - 6, "#1e1410")
        # contents
        if k == 0:
            for j, col in enumerate(("#3a4a6a", "#6a3a2a", "#3a5a3a")):
                cv.rect(ox + 10 + j * 9, sy + sec_h - 22, 8, 17, col); cv.rect(ox + 12 + j * 9, sy + sec_h - 18, 4, 4, "#e8dcc0")
        elif k == 1:
            bx0 = ox + width - 44
            cv.rect(bx0, sy + sec_h - 20, 30, 15, "#9a7a4a"); cv.hline(bx0, sy + sec_h - 20, 30, "#b8946a")
            cv.rect(bx0 + 8, sy + sec_h - 15, 14, 7, "#e8dcc0"); micro_text(cv, "VAL", bx0 + 10, sy + sec_h - 14, "#7a2a24")
            cv.poly([(ox + 12, sy + sec_h - 6), (ox + 30, sy + sec_h - 12), (ox + 32, sy + sec_h - 9), (ox + 14, sy + sec_h - 4)], "#5a2a3a")
        else:
            cv.rect(ox + 10, sy + sec_h - 9, 24, 4, "#d8ccb0"); cv.rect(ox + 11, sy + sec_h - 12, 22, 3, "#c8bc9c")
        # dust lines where books stood
        for dx in range(ox + 40, ox + width - 50, 5):
            if rng.random() < 0.4 and k != 1:
                cv.vline(dx, sy + sec_h - 7, 1, C("#8a7a62", 0.5))
        # glass and its reflection, the brass pull
        cv.rect(ox + 5, sy, width - 10, sec_h - 4, C("#8aa0c8", 0.10))
        cv.line(ox + 12, sy + sec_h - 6, ox + 24, sy + 1, C("#c8d4f0", 0.25)); cv.line(ox + 16, sy + sec_h - 6, ox + 28, sy + 1, C("#c8d4f0", 0.15))
        cv.hline(ox + 4, sy - 1, width - 8, OAK_IN[5]); cv.hline(ox + 4, sy + sec_h - 4, width - 8, OAK_IN[2])
        cv.rect(ox + width // 2 - 5, sy + 1, 10, 2, GILT_OM[3])
    cv.rect(ox, base - 6, width, 6, OUT); cv.rect(ox + 1, base - 5, width - 2, 4, OAK_IN[2]); cv.hline(ox + 1, base - 5, width - 2, OAK_IN[4])
    return cv, ox + width // 2, base


def sheeted_bench(width=105, height=32, seed=0):
    """A buttoned leather office bench, half under a dust sheet."""
    cv = Canvas(width + 8, height + 6, seed=seed)
    ox, base = 4, height + 3
    top = base - height
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 3)
    seat = base - 14
    cv.rect(ox, top + 2, width, seat - top - 2, OUT)
    cv.rect(ox + 1, top + 3, width - 2, seat - top - 4, LEATHER[3]); cv.hline(ox + 1, top + 3, width - 2, LEATHER[4])
    for bx in range(ox + 8, ox + width - 4, 10):
        for by in (top + 7, top + 12):
            cv.px(bx + (by // 5) % 2 * 5, by, LEATHER[1])
    cv.rect(ox - 1, seat, width + 2, 6, OUT); cv.rect(ox, seat + 1, width, 4, LEATHER[3]); cv.hline(ox, seat + 1, width, LEATHER[4])
    for lx in (ox + 3, ox + width - 7):
        cv.rect(lx, seat + 6, 4, base - seat - 6, OUT); cv.rect(lx + 1, seat + 6, 2, base - seat - 7, OAK_IN[4])
    # dust sheet thrown over the right half: draped over the back, pooling on the seat, hanging
    # down past the end to the floor in loose folds
    sx = ox + width // 2 - 8
    hem = [(ox + width + 4, base - 1), (ox + width - 6, base), (ox + width - 14, base - 2), (ox + width - 24, base - 4),
           (sx + 22, seat + 9), (sx + 12, seat + 7), (sx + 2, seat + 8), (sx - 5, seat + 4)]
    pts = [(sx - 2, top + 1), (sx + 10, top - 1), (ox + width - 4, top), (ox + width + 3, top + 6)] + hem
    cv.poly([(p[0] + 1, p[1] + 1) for p in pts], OUT)
    cv.poly([(p[0] - 1, p[1]) for p in pts], OUT)
    cv.poly(pts, "#c4bcac")
    # folds: shadowed valleys running down the drape
    for (x0, x1, y1) in ((sx + 6, sx + 4, seat + 7), (sx + 20, sx + 24, seat + 8), (ox + width - 16, ox + width - 12, base - 3),
                         (ox + width - 4, ox + width + 1, base - 2)):
        cv.line(x0, top + 3, x1, y1, "#9a9284"); cv.line(x0 + 1, top + 3, x1 + 1, y1, "#aaa294")
    cv.hline(sx + 2, top, ox + width - 6 - sx, "#e6e0d2"); cv.hline(sx, seat + 1, ox + width - sx - 10, "#d8d2c4")
    cv.line(ox + width - 2, top + 2, ox + width + 2, base - 3, "#e0dacc")
    return cv, ox + width // 2, base


def pleated_lamp(height=68):
    """A standard lamp with a pleated amber silk shade on a dark oak column. Bulb ~5px below the top."""
    w = 26
    cv = Canvas(w, height + 6)
    cx, base = w // 2, height + 3
    top = base - height
    ground_shadow(cv, cx, base, 8, 2)
    cv.ellipse(cx - 7, base - 5, 15, 6, OUT); cv.ellipse(cx - 6, base - 5, 13, 5, OAK_IN[3]); cv.hline(cx - 4, base - 5, 9, OAK_IN[5])
    cv.rect(cx - 2, top + 12, 4, base - top - 16, OUT)
    cv.vline(cx - 1, top + 12, base - top - 16, OAK_IN[5]); cv.vline(cx, top + 12, base - top - 16, OAK_IN[3])
    for ky in (top + 30, base - 14):
        cv.rect(cx - 3, ky, 6, 3, OUT); cv.rect(cx - 2, ky + 1, 4, 1, GILT_OM[4])
    cv.poly([(cx - 6, top), (cx + 6, top), (cx + 11, top + 12), (cx - 11, top + 12)], OUT)
    cv.poly([(cx - 5, top + 1), (cx + 5, top + 1), (cx + 10, top + 11), (cx - 10, top + 11)], "#d89a4a")
    for k in range(-8, 9, 3):
        cv.line(cx + k // 2, top + 1, cx + k, top + 11, "#b87a3a")
    cv.poly([(cx - 4, top + 1), (cx - 1, top + 1), (cx - 4, top + 11), (cx - 9, top + 11)], "#f0b860")
    cv.hline(cx - 10, top + 11, 21, "#fde9b6")
    cv.rect(cx - 2, top + 12, 5, 2, "#fff0c4")
    return cv, cx, base


# ---------------------------------------------------------------------------- build
def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    back_wall(bg)
    floor(bg)
    front_and_margins(bg)
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

    save(0, partners_desk(210, 52, seed=3))
    save(1, phone_table(120, 38, replied=False, seed=4), flag="family_message_read", flag_made=phone_table(120, 38, replied=True, seed=4))
    save(2, barrister_bookcase(110, 108, seed=5))
    save(4, sheeted_bench(105, 32, seed=6))
    save(5, pleated_lamp(68))

    # the service door stands ajar once the original directory has been read
    x, w, h = DOOR
    door = Canvas(w + 14, h + 15)
    tmp = Canvas(W, H)
    service_door(tmp, x, w, h, ajar=True)
    door.a[:] = tmp.a[BASE - h - 14:BASE + 1, x - 7:x + w + 7]
    door.save(os.path.join(out, "door-ajar.png"))
    overlays = [{"texture": res + "door-ajar.png", "x": x - 7, "y": BASE - h - 14, "flag": "booth_origin"}]

    wx, wy, ww, wh = WINDOW
    layers = [
        {"kind": "twinkle", "points": [[LAMP[0], LAMP[1] - 63, "fff0c4", 2], [DESK[0] - 83, DESK[1] - 57, "fde9b6", 1]],
         "rate": 1.1, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 18, "rect": [wx - 40, wy + 20, ww + 40, 200], "speed": [-1, 2], "color": "c8d4f0"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [3],
        "overlays": overlays,
        "fauna": [
            {"kind": "lamp_moth", "x": wx + ww - 18, "y": wy + 46, "range": 8, "speed": 1.6, "rate": 8.0},
            {"kind": "umc2_mouse", "x": 300, "y": BASE + 6, "range": 18, "speed": 0.3, "rate": 4.0, "flip": True},
        ],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(paths.PROJECT)
