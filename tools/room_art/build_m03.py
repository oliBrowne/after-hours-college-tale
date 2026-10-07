"""Macky cloakroom (M03): tickets are invitations.

The back wall: oak panelling under ochre plaster. In the middle the cloakroom hatch, CLOAKROOM
in gilt over it: through the opening, rows of numbered brass hooks hung with coats recede under a
bare bulb, and the oak counter runs across the front with its brass rail and hinged flap. Left,
the narrow green service door to the backstage stair (to the balcony). Right, a wall of numbered
pigeonholes for gloves and scarves. Two round windows high in the wall show the sky (dawn in the
dawn version, with small warm patches of light below them).
The floor: oak parquet worn pale along the path from the lobby door (bottom right) to the hatch,
dropped red tickets, a glove, a scarf.
Props: two rolling coat racks packed with coats, graduation gowns and mortarboards (they empty out
when the guests are freed), the ticket table (red ADMIT tickets everywhere, squared into cream
invitations once freed), the ASK FIRST chalkboard, a floor lamp.
State: attendees_freed swaps the racks and the table; attendee_choice hangs a card on the counter
(GO HOME SAFE for "leave", ONE GATHERING for "invite"); freed tickets flutter about."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from props import OUT, IRON, WOOD
from lib_norlin import runner_n, plaster_wall, oak_wainscot, parquet_floor, standard_lamp, depth_shade, OAK_FLOOR
from lib_macky import (board_floor, coat_rack, ticket_table, ask_first_board, cloak_counter, hook_rows, oculus, gilt_band,
                       hanging_lantern, dressed_band, DRESS, PLASTER_M, CARPET_M, BRASS, GILT_M, SHADOW, COATS, TICKET_RED, CARD,
                       GLOW)

ROOM = "M03"
W, H = 800, 480
WALL = 142
DADO = 96
WALK = (20, 142, 760, 314)
HATCH = (300, 562, 50)            # x0, x1, top of the cloakroom hatch opening
SERVICE_X = 75
OCULI = [(180, 40), (690, 40)]
BULBS = [(230, 56), (610, 56)]
LAMP = (120, 385)
CARD_BOX = (381, 112, 100, 24)     # x, y, w, h of the attendee_choice card on the counter front
SHADE_AMBER = ["#4a2a1a", "#7a4424", "#b0662e", "#d88a40", "#f0b060"]


def service_door(cv, cx, bottom, w=34, h=70):
    """The narrow painted service door to the backstage stair: dressed stone frame, green
    panels, a push bar, a small wired-glass light, BACKSTAGE stencilled above."""
    x = cx - w // 2
    top = bottom - h
    cv.rect(x - 5, top - 5, w + 10, h + 5, DRESS[3]); cv.hline(x - 5, top - 5, w + 10, DRESS[5]); cv.vline(x - 5, top - 5, h + 5, DRESS[5])
    cv.vline(x + w + 4, top - 5, h + 5, DRESS[1])
    cv.rect(x, top, w, h, OUT)
    cv.rect(x + 1, top + 1, w - 2, h - 1, "#2c4a3c"); cv.vline(x + 1, top + 1, h - 1, "#3e6450")
    for (py, ph) in [(top + 26, 18), (top + 48, 18)]:
        cv.rect(x + 5, py, w - 10, ph, "#25402f"); cv.hline(x + 5, py, w - 10, "#1a2c22"); cv.hline(x + 5, py + ph - 1, w - 10, "#3e6450")
    cv.rect(x + 8, top + 6, w - 16, 14, IRON[1]); cv.rect(x + 9, top + 7, w - 18, 12, "#3a4a5a")
    for gx in range(x + 9, x + w - 9, 3):
        cv.vline(gx, top + 7, 12, C("#1a2230", 0.5))
    cv.px(x + 10, top + 9, "#8a9ab0")
    cv.rect(x + 3, top + 44, w - 6, 3, IRON[3]); cv.hline(x + 3, top + 44, w - 6, IRON[4])
    cv.rect(x - 2, bottom - 2, w + 4, 2, DRESS[4])
    lab = "BACKSTAGE"
    cv.rect(cx - text_width(lab) // 2 - 3, top - 17, text_width(lab) + 6, 11, "#1c1418")
    text(cv, lab, cx - text_width(lab) // 2, top - 16, "#e6d6b1")


def hatch(cv, dawn):
    """The cloakroom opening: coats on rows of hooks receding under a bare bulb, the counter."""
    x0, x1, top = HATCH
    # the room behind: darker panelling, hooks with coats in three rows, a bulb
    cv.rect(x0, top, x1 - x0, WALL - top, "#24161a")
    for yy in range(top, WALL, 6):
        cv.hline(x0, yy, x1 - x0, "#2a1a1c")
    hook_rows(cv, x0 + 6, x1 - 6, [top + 14, top + 40], seed=4)
    bx = (x0 + x1) // 2
    cv.vline(bx, top, 8, IRON[2])
    for rr, a in [(40, 0.05), (26, 0.07), (14, 0.09)]:
        cv.ellipse(bx - rr, top + 10 - rr // 2, rr * 2 + 1, rr + 2, C("#f6cf7a", a))
    cv.rect(bx - 2, top + 8, 5, 3, IRON[3]); cv.ellipse(bx - 2, top + 10, 5, 6, "#fff0c4")
    # the opening's frame: dressed stone jambs and lintel with the gilt name
    for sx in (x0 - 8, x1):
        cv.rect(sx, top, 8, WALL - top, DRESS[3]); cv.vline(sx, top, WALL - top, DRESS[5] if sx < x0 else DRESS[1])
        for yy in range(top + 7, WALL, 9):
            cv.hline(sx, yy, 8, DRESS[1])
    cv.rect(x0 - 10, top - 10, x1 - x0 + 20, 10, DRESS[3]); cv.hline(x0 - 10, top - 10, x1 - x0 + 20, DRESS[5]); cv.hline(x0 - 10, top - 1, x1 - x0 + 20, DRESS[1])
    gilt_band(cv, (x0 + x1) // 2, top - 26, "CLOAKROOM", w=86)
    cloak_counter(cv, x0, x1, WALL, top_h=38)
    return (bx, top + 12)


def pigeonholes(cv, x, y, w, h, seed=0):
    """Oak pigeonholes for small things, each with a brass number plate; gloves, scarves and a
    hat in some."""
    rng = np.random.default_rng(seed)
    cw, ch = 20, 16
    cv.rect(x - 3, y - 3, w + 6, h + 6, OUT); cv.rect(x - 2, y - 2, w + 4, h + 4, WOOD[3]); cv.hline(x - 2, y - 2, w + 4, WOOD[5])
    for yy in range(y, y + h, ch):
        for xx in range(x, x + w, cw):
            cv.rect(xx, yy, cw - 2, ch - 2, "#1c1214"); cv.hline(xx, yy, cw - 2, "#120a0c")
            r = rng.random()
            if r < 0.3:
                c = COATS[int(rng.integers(len(COATS)))]
                cv.rect(xx + 2, yy + ch - 8, cw - 6, 5, c); cv.hline(xx + 2, yy + ch - 8, cw - 6, shade(c, 0.25))
            elif r < 0.45:
                c = ["#a83c32", "#d8b45a", "#3a5aa0"][int(rng.integers(3))]
                cv.rect(xx + 3, yy + ch - 6, 5, 3, c); cv.rect(xx + 9, yy + ch - 6, 5, 3, shade(c, -0.15))
            cv.rect(xx + cw // 2 - 3, yy + ch - 2, 5, 2, BRASS[3])
        cv.rect(x, yy + ch - 2, w, 2, WOOD[2]); cv.hline(x, yy + ch - 2, w, WOOD[4])


def choice_card(label_lines, w=80, h=24):
    """A card hung by a string on the counter front, lettered by hand."""
    cv = Canvas(w, h)
    cv.line(w // 2 - 14, 0, w // 2, 4, "#2a2026"); cv.line(w // 2, 4, w // 2 + 14, 0, "#2a2026")
    cv.rect(4, 4, w - 8, h - 5, OUT); cv.rect(5, 5, w - 10, h - 7, CARD[2]); cv.hline(5, 5, w - 10, CARD[3])
    for i, ln in enumerate(label_lines):
        text(cv, ln, w // 2 - text_width(ln) // 2, 5 + i * 8, "#7a2a26" if i == 0 else "#4a3a34")
    return cv


def back_wall(cv, dawn):
    plaster_wall(cv, 0, 11, W, DADO - 11, pal=PLASTER_M, seed=5)
    cv.rect(0, 0, W, 11, "#2a1a1c"); cv.hline(0, 8, W, WOOD[4]); cv.hline(0, 9, W, WOOD[2]); cv.hline(0, 10, W, C(SHADOW, 0.6))
    oak_wainscot(cv, 0, DADO, W, WALL - DADO, seed=6, panel=24)
    lights = []
    for (ox_, oy) in OCULI:
        oculus(cv, ox_, oy, 11, dawn=dawn, seed=ox_)
    lights.append(hatch(cv, dawn))
    service_door(cv, SERVICE_X, WALL)
    pigeonholes(cv, 618, 58, 140, 64, seed=8)
    # a notice by the hatch and a clock
    cv.rect(236, 56, 44, 34, OUT); cv.rect(237, 57, 42, 32, CARD[2]); cv.hline(237, 57, 42, CARD[3])
    text(cv, "TICKET", 240, 58, "#7a2a26"); text(cv, "PLEASE", 240, 67, "#7a2a26")
    cv.hline(241, 79, 34, CARD[0]); cv.hline(241, 83, 28, CARD[0])
    cv.ellipse(133, 30, 23, 23, OUT); cv.ellipse(134, 31, 21, 21, BRASS[2]); cv.ellipse(136, 33, 17, 17, "#efe4cc")
    cv.line(144, 41, 144, 35, "#1a1418"); cv.line(144, 41, 149, 42, "#1a1418"); cv.px(144, 41, "#a83c32")
    # bare bulbs hanging over the racks
    for (bx, by) in BULBS:
        cv.vline(bx, 11, by - 11, IRON[2])
        for rr, a in [(16, 0.05), (10, 0.08)]:
            cv.ellipse(bx - rr, by - rr + 2, rr * 2 + 1, rr * 2 + 1, C("#f6cf7a", a))
        cv.rect(bx - 2, by - 3, 5, 3, IRON[3]); cv.ellipse(bx - 3, by - 1, 7, 8, "#fde9b6"); cv.px(bx - 1, by + 1, "#ffffff")
        lights.append((bx, by + 2))
    cv.rect(0, WALL - 2, W, 2, C(SHADOW, 0.35))
    return lights


def floor(cv, dawn):
    board_floor(cv, 0, WALL, W, H - WALL, seed=9)
    # an oxblood runner from the lobby door (bottom right) round to the hatch
    runner_n(cv, 398, WALL, 66, 300 - WALL + 120, pal=CARPET_M, vertical=True)
    runner_n(cv, 398, 400, W - 398, 40, pal=CARPET_M, vertical=False)
    cv.rect(398, 400, 66, 40, CARPET_M[3]); cv.rect(402, 404, 58, 32, CARPET_M[5]); cv.rect(404, 406, 54, 28, CARPET_M[2])
    # a coir mat in front of the hatch
    cv.rect(380, WALL + 2, 102, 16, "#3a2c20"); cv.rect(382, WALL + 3, 98, 13, "#6a5236")
    for xx in range(383, 479, 3):
        cv.vline(xx, WALL + 4, 11, "#5a4430")
    # dropped tickets, a glove, a scarf
    rng = np.random.default_rng(23)
    for _ in range(26):
        tx, ty = int(rng.integers(40, 760)), int(rng.integers(WALL + 30, 450))
        if 395 <= tx <= 475 and 300 <= ty <= 345:
            continue
        cv.rect(tx, ty, 5, 3, TICKET_RED[int(rng.integers(1, 3))]); cv.hline(tx, ty, 5, TICKET_RED[3]); cv.hline(tx, ty + 3, 5, C(SHADOW, 0.3))
    cv.rect(316, 396, 8, 4, "#3a4a6a"); cv.rect(323, 397, 3, 2, "#3a4a6a"); cv.px(316, 395, "#3a4a6a"); cv.px(318, 395, "#3a4a6a")
    for k in range(18):
        cv.rect(660 + k * 2, 360 + int(3 * np.sin(k * 0.6)), 3, 3, "#a83c32" if (k // 2) % 2 else "#e6d6b1")
    # the lobby door at the bottom right: a brass threshold strip and light from the lobby
    light_pool(cv, 760, 470, 60, 18, strength=0.16)


def light(cv, dawn, lights):
    for (bx, by) in BULBS:
        light_pool(cv, bx, WALL + 40, 90, 34, strength=0.18)
    light_pool(cv, 431, WALL + 8, 80, 12, strength=0.2)
    light_pool(cv, LAMP[0], LAMP[1] + 2, 54, 16, strength=0.26)
    if dawn:
        # morning through the round windows: two warm discs on the wall and the floor
        for (ox_, oy) in OCULI:
            cv.ellipse(ox_ + 6, oy + 34, 22, 14, C("#f8d498", 0.16))
            cv.ellipse(ox_ + 18, WALL + 30, 30, 12, C("#f8d498", 0.12))
            cv.ellipse(ox_ + 22, WALL + 33, 22, 8, C("#f8d498", 0.1))


def margins(cv):
    for (x, w) in [(0, WALK[0]), (WALK[0] + WALK[2], W - WALK[0] - WALK[2])]:
        cv.rect(x, WALL, w, H - WALL, C(SHADOW, 0.28))
    bottom = WALK[1] + WALK[3]
    depth_shade(cv, 0, bottom - 30, W, H - bottom + 30, steps=3, alpha=0.36)


def paint(dawn):
    cv = Canvas(W, H, fill="#171a2b", seed=8)
    lights = back_wall(cv, dawn)
    floor(cv, dawn)
    light(cv, dawn, lights)
    margins(cv)
    return cv, lights


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    night, lights = paint(False)
    night.save(os.path.join(out, "background.png"))
    day, _ = paint(True)
    day.save(os.path.join(out, "background-dawn.png"))
    x, y, w, h = CARD_BOX
    choice_card(("GO HOME SAFE", "NO SEAT LOST"), w, h).save(os.path.join(out, "card-leave.png"))
    choice_card(("ONE GATHERING", "THEN HOME"), w, h).save(os.path.join(out, "card-invite.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    res = f"res://assets/art/rooms/{ROOM}/"
    for idx, seed in ((0, 1), (1, 2)):
        coat_rack(160, 110, fullness=0.3, seed=seed)[0].save(os.path.join(out, f"prop-{idx}-freed.png"))
        save(idx, coat_rack(160, 110, fullness=1.0, seed=seed), {"flag": "attendees_freed", "flag_texture": res + f"prop-{idx}-freed.png"})
    ticket_table(190, 48, freed=True, seed=3)[0].save(os.path.join(out, "prop-2-freed.png"))
    save(2, ticket_table(190, 48, seed=3), {"flag": "attendees_freed", "flag_texture": res + "prop-2-freed.png"})
    save(3, ask_first_board(96, 56))
    save(4, standard_lamp(68, shade_pal=SHADE_AMBER, seed=4))

    glow = [[int(x_), int(y_), "fff0c4", 2] for (x_, y_) in lights]
    glow.append([LAMP[0], LAMP[1] - 63, "fff0c4", 2])
    manifest = {
        "background": res + "background.png",
        "background_dawn": res + "background-dawn.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": [
            {"texture": res + "card-leave.png", "x": x, "y": y, "flag": "attendee_choice", "equals": "leave"},
            {"texture": res + "card-invite.png", "x": x, "y": y, "flag": "attendee_choice", "equals": "invite"},
        ],
        "fauna": [{"kind": "umc2_mouse", "x": 520, "y": 444, "range": 12, "speed": 0.7, "rate": 5.0}],
        "layers": [
            {"kind": "twinkle", "points": glow, "rate": 1.0, "min": 0.6},
            # once the guests are free, a few tickets ride the draught from the lobby door
            {"kind": "fauna", "flag": "attendees_freed", "fauna": [
                {"kind": "macky_ticket", "x": 80, "y": 190, "fly": 9.0, "rate": 5.0},
                {"kind": "macky_ticket", "x": 420, "y": 250, "fly": 7.0, "rate": 4.0},
                {"kind": "macky_ticket", "x": 600, "y": 170, "fly": 8.0, "rate": 6.0}]},
        ],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
