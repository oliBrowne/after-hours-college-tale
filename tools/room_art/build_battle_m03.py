"""Battle backdrop for the cloakroom (M03): down the aisle of the coat store, behind the hatch.

The room shows the cloakroom from the guests' side. Here the camera is in the store behind the
counter: a long aisle between two walls of coats and black graduation gowns hung shoulder to
shoulder on rails, every one with a cream ticket tag, hat shelves above them crowded with
mortarboards, bowlers and hat boxes. Bare bulbs hang down the aisle. At the far end the hatch
opens on the warm cloakroom, the counter with its brass bell across the bottom. The floorboards
run toward it with a worn oxblood runner. Tickets come loose and tumble through the air.
At dawn the hatch shows the morning: the room beyond is lit by the round windows, the bulbs
still burn."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON, WOOD
from lib_macky import (COATS, GOWN, CARD, TICKET_RED, CARPET_M, FLOOR_HONEY, PLASTER_M, BRASS, GILT_M, DRESS,
                       hook_rows, gilt_band, oculus, SHADOW)
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "M03"
INK = "#10121e"
AISLE = 300.0         # coat walls at X = -AISLE and +AISLE
Z0, Z_FAR = 120.0, 1000.0
CEIL = 230.0
RAIL = 170.0          # height of the coat rails
SHELF = 196.0         # hat shelf
BULBS = [400.0, 600.0, 800.0]
NIGHT = (0.68, 0.72, 0.84)
DAWN = (0.90, 0.936, 0.967)


def emissive(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r > 0.55) & (r - b > 0.36) & (g - b > 0.2)


def grade(rgba, dawn, keep_glow=True):
    out = rgba.copy()
    mul = np.array(DAWN if dawn else NIGHT, np.float32)
    m = ~emissive(out[..., :3]) if keep_glow else np.ones(out.shape[:-1], bool)
    out[m, :3] = out[m, :3] * mul
    return out


def coat_wall(seed=0):
    """One side of the aisle, laid out along its length (u = distance from Z0, rows from the
    ceiling down, world units): panelling behind, the hat shelf, the rail of coats and gowns seen
    side-on like spines on a shelf, ticket tags, a few umbrellas and shoes below."""
    L, Hh = int(Z_FAR - Z0), int(CEIL)
    rng = np.random.default_rng(seed)
    cv = Canvas(L, Hh, seed=seed)
    cv.rect(0, 0, L, Hh, "#24161a")
    for x in range(0, L, 40):
        cv.vline(x, 0, Hh, "#1c1014"); cv.vline(x + 1, 0, Hh, "#2e1c1e")
    rail_r = Hh - int(RAIL)
    shelf_r = Hh - int(SHELF)
    # hat shelf with its load
    cv.rect(0, shelf_r, L, 5, WOOD[3]); cv.hline(0, shelf_r, L, WOOD[5]); cv.hline(0, shelf_r + 4, L, WOOD[1])
    x = 4
    while x < L - 20:
        kind = rng.choice(["board", "board", "hat", "box", "box"])
        if kind == "board":
            cv.poly([(x, shelf_r - 3), (x + 9, shelf_r - 7), (x + 18, shelf_r - 3), (x + 9, shelf_r)], GOWN[1])
            cv.hline(x + 2, shelf_r - 3, 14, GOWN[2]); cv.px(x + 9, shelf_r - 5, "#d8b45a"); cv.vline(x + 16, shelf_r - 3, 6, "#d8b45a")
            x += 20
        elif kind == "hat":
            col = COATS[int(rng.integers(len(COATS)))]
            cv.ellipse(x, shelf_r - 4, 20, 5, shade(col, -0.2)); cv.rect(x + 4, shelf_r - 12, 12, 9, col); cv.hline(x + 4, shelf_r - 5, 12, "#5a2a2e")
            x += 22
        else:
            bw, bh = int(rng.integers(18, 30)), int(rng.integers(10, 18))
            col = ["#c8b896", "#8a5a4a", "#5a6a7a", "#d8c8a8"][int(rng.integers(4))]
            cv.rect(x, shelf_r - bh, bw, bh, OUT); cv.rect(x + 1, shelf_r - bh + 1, bw - 2, bh - 2, col)
            cv.hline(x + 1, shelf_r - bh + 1, bw - 2, shade(col, 0.2)); cv.hline(x + 1, shelf_r - bh + 4, bw - 2, shade(col, -0.2))
            x += bw + 3
    # two tiers of rails, coats and gowns packed along them
    bright = COATS + ["#9a6a3a", "#8a2a2a", "#c8a050", "#2a5a5a", "#3a3a6a", "#b07a50"]
    for (rail_y, lo, hi, gp) in [(RAIL, 58, 74, 0.3), (RAIL - 84, 50, 66, 0.1)]:
        rail_r = Hh - int(rail_y)
        cv.rect(0, rail_r - 2, L, 4, OUT); cv.hline(0, rail_r - 1, L, IRON[4]); cv.hline(0, rail_r, L, IRON[3])
        x = 2 + int(rng.integers(0, 6))
        while x < L - 10:
            gown = rng.random() < gp
            col = GOWN[1] if gown else bright[int(rng.integers(len(bright)))]
            w = int(rng.integers(12, 18))
            length = int(rng.integers(lo, hi)) + (8 if gown else 0)
            top = rail_r + 3
            dark, darker, light = shade(col, -0.25), shade(col, -0.5), shade(col, 0.25)
            cv.line(x + w // 2, rail_r - 3, x + w // 2, rail_r + 2, IRON[4])
            for yy in range(top, top + length):
                t = (yy - top) / length
                ww = w - 4 + min(4, (yy - top) * 2) + int(t * 3)
                xo = x + (w - ww) // 2
                cv.hline(xo, yy, ww, col)
                cv.hline(xo, yy, 2, light)
                cv.hline(xo + ww - 3, yy, 2, dark)
                cv.px(xo + ww - 1, yy, darker)
                if 0.12 < t < 0.6:
                    cv.px(xo + ww // 2, yy, dark)
            cv.hline(x, top + length - 1, w, darker)
            if gown:
                cv.vline(x + 4, top + 2, 30, "#d8b45a"); cv.vline(x + 5, top + 2, 30, "#b8913a")
            if rng.random() < 0.6:
                tx = x + w // 2 + 1
                cv.vline(tx, rail_r + 2, 5, CARD[1])
                cv.rect(tx - 2, rail_r + 7, 6, 8, CARD[0]); cv.rect(tx - 1, rail_r + 8, 4, 6, CARD[2]); cv.px(tx, rail_r + 10, TICKET_RED[1])
            x += int(rng.integers(9, 13))
    # umbrellas and shoes on the floor below
    for _ in range(L // 60):
        ux = int(rng.integers(10, L - 10))
        if rng.random() < 0.5:
            cv.line(ux, Hh - 2, ux + 4, Hh - 46, OUT); cv.line(ux + 1, Hh - 2, ux + 5, Hh - 46, ["#2a2a3a", "#5a2a2e", "#2c3a4a"][int(rng.integers(3))])
            cv.rect(ux + 3, Hh - 50, 4, 5, IRON[2])
        else:
            cv.rect(ux, Hh - 6, 12, 5, "#1a1214"); cv.hline(ux, Hh - 6, 12, "#3a2a2a")
    cv.rect(0, Hh - 4, L, 4, "#1a1012")
    return cv.a


def far_end(dawn):
    """The hatch seen from inside the store at room scale: dark panelling with hooks, the opening
    on the lit cloakroom (its round window, the coat racks, the lamp), the counter across it."""
    W_, H_ = int(2 * AISLE / ROOM_TO_BATTLE) + 4, int(CEIL / ROOM_TO_BATTLE) + 2
    cv = Canvas(W_, H_, seed=4)
    cv.rect(0, 0, W_, H_, "#24161a")
    for x in range(0, W_, 24):
        cv.vline(x, 0, H_, "#1c1014")
    base = H_ - 1
    cx = W_ // 2
    hook_rows(cv, 6, cx - 80, [base - 96, base - 66], seed=7)
    hook_rows(cv, cx + 80, W_ - 6, [base - 96, base - 66], seed=8)
    # the opening, and the cloakroom beyond it, lit
    x0, x1, top = cx - 66, cx + 66, base - 108
    room = "#e8b070" if not dawn else "#f0c898"
    cv.rect(x0, top, x1 - x0, base - top, room)
    for yy in range(top, base - 60, 5):
        cv.hline(x0, yy, x1 - x0, "#d8a060" if not dawn else "#e4b888")
    cv.rect(x0, base - 60, x1 - x0, 60, "#c88a4a" if not dawn else "#d8a070")
    for yy in range(base - 60, base, 6):
        cv.hline(x0, yy, x1 - x0, "#b07438" if not dawn else "#c08858")
    cv.rect(x0, base - 66, x1 - x0, 6, WOOD[3]); cv.hline(x0, base - 66, x1 - x0, WOOD[5])
    oculus(cv, cx + 30, top + 20, 9, dawn=dawn, seed=3)
    # the far racks of coats in the room beyond, small
    for rx in (x0 + 10, x1 - 50):
        cv.rect(rx, base - 64, 40, 2, IRON[3])
        for k in range(6):
            cv.rect(rx + 2 + k * 6, base - 62, 6, 26, COATS[(k * 5 + rx) % len(COATS)])
            cv.vline(rx + 2 + k * 6, base - 62, 26, OUT)
    if not dawn:
        cv.rect(cx - 36, top + 34, 3, 32, BRASS[2]); cv.rect(cx - 41, top + 28, 13, 7, "#d88a40"); cv.hline(cx - 41, top + 34, 13, "#fde9b6")
    # frame of the opening
    for sx in (x0 - 7, x1):
        cv.rect(sx, top - 7, 7, base - top + 7, DRESS[2]); cv.vline(sx, top - 7, base - top + 7, DRESS[4] if sx > x0 else DRESS[1])
    cv.rect(x0 - 7, top - 9, x1 - x0 + 14, 9, DRESS[3]); cv.hline(x0 - 7, top - 9, x1 - x0 + 14, DRESS[5])
    # the counter across the bottom, seen from behind: plain boards, a cash drawer, the bell on top
    ct = base - 34
    cv.rect(x0 - 10, ct, x1 - x0 + 20, 34, WOOD[2])
    for xx in range(x0 - 8, x1 + 10, 18):
        cv.vline(xx, ct + 6, 28, WOOD[1])
    cv.rect(x0 - 12, ct - 4, x1 - x0 + 24, 5, WOOD[4]); cv.hline(x0 - 12, ct - 4, x1 - x0 + 24, WOOD[5])
    cv.rect(cx - 12, ct + 10, 24, 8, WOOD[3]); cv.rect(cx - 3, ct + 13, 6, 2, BRASS[3])
    cv.ellipse(cx + 20, ct - 9, 9, 6, BRASS[3]); cv.px(cx + 22, ct - 8, BRASS[4]); cv.rect(cx + 23, ct - 11, 2, 2, BRASS[2])
    for k in range(5):
        cv.rect(cx - 40 + k * 3, ct - 5 - k, 8, 2, TICKET_RED[1 + k % 2])
    return grade(cv.a, dawn), (cx, top + 40)


def floor_shader(dawn):
    pal = pal_array(FLOOR_HONEY)
    carpet = pal_array(CARPET_M)
    mul = np.array(DAWN if dawn else NIGHT, np.float32)

    def shader(X, Z):
        board = 22.0
        col = np.floor(X / board)
        fx = X / board - col
        length = 160 + 80 * hash2(col, 3)
        off = hash2(col, 5) * length
        seg = np.floor((Z + off) / length)
        fz = (Z + off) / length - seg
        t = hash2(col, seg, 7)
        rgb = pal[2] * (1 - t[:, None]) + pal[4] * t[:, None]
        grain = hash2(np.floor(X / 3.0), np.floor(Z / 12.0), 11)
        rgb = rgb * (0.95 + 0.07 * grain[:, None])
        rgb[fx < 0.06] = pal[0]
        rgb[fz < 0.015] = pal[1]
        ax = np.abs(X)
        run = ax < 48
        rgb[run] = carpet[3]
        rgb[(ax < 42) & (ax > 38)] = carpet[5]
        lz = (Z / 40.0) % 1
        rgb[(ax / 8 + np.abs(lz - 0.5) * 4) < 1.0] = carpet[4]
        worn = run & (hash2(np.floor(X / 6), np.floor(Z / 10), 2) > 0.8)
        rgb[worn] = carpet[2]
        rgb = rgb * mul
        out = rgba_of(rgb)
        for bz in BULBS:
            warm_light(out[..., :3], np.hypot(X, (Z - bz) * 0.8), 150, strength=0.32 if not dawn else 0.2)
        warm_light(out[..., :3], np.hypot(X, (Z - Z_FAR) * 0.6), 160, colour="#f6cf7a" if not dawn else "#f8d8a8", strength=0.3)
        fog(out, Z, "#1e1218", 700, 1400, amount=0.45)
        return out
    return shader


def wall_shader(tex, dawn, flip=False):
    th, tw = tex.shape[:2]

    def shader(u, Y, Z):
        uu = (tw - 1 - u) if flip else u
        out = texture_lookup(tex, uu, th - 1 - Y)
        out[..., 3] = 1
        for bz in BULBS:
            warm_light(out[..., :3], np.hypot(Z - bz, (Y - 150) * 0.9), 180, strength=0.14 if not dawn else 0.08)
        fog(out, Z, "#1e1218", 700, 1400, amount=0.45)
        return out
    return shader


def ceiling_shader(dawn):
    mul = np.array(DAWN if dawn else NIGHT, np.float32)

    def shader(X, Z):
        joist = ((Z / 60.0) % 1) < 0.18
        rgb = np.repeat(pal_array(["#2a1a1c"]), X.shape[0], 0)
        rgb[joist] = pal_array(["#3e2622"])[0]
        rgb = rgb * mul
        out = rgba_of(rgb)
        fog(out, Z, "#1e1218", 700, 1400, amount=0.45)
        return out
    return shader


def bulb_sprite():
    """A bare bulb on its flex (room scale): ceramic holder, a bright glass pear."""
    cv = Canvas(9, 30)
    cv.vline(4, 0, 22, IRON[2])
    cv.rect(2, 20, 5, 3, IRON[3])
    cv.ellipse(1, 22, 7, 7, OUT); cv.ellipse(2, 23, 5, 5, "#fde9b6"); cv.px(3, 24, "#ffffff")
    return cv.a


def render(dawn):
    v = View(horizon=98, cam=52, fill="#141223")
    v.ground(ceiling_shader(dawn), height=CEIL, y_from=0, y_to=v.h0)
    v.ground(floor_shader(dawn))
    left = grade(coat_wall(seed=21), dawn)
    right = grade(coat_wall(seed=22), dawn)
    v.plane((-AISLE, Z0), (-AISLE, Z_FAR), wall_shader(left, dawn), y_max=CEIL)
    v.plane((AISLE, Z0), (AISLE, Z_FAR), wall_shader(right, dawn), y_max=CEIL)
    fw, glow_at = far_end(dawn)
    sx, sy, sc = v.sprite(fw, 0, Z_FAR, anchor=(0.5, 1.0), scale=ROOM_TO_BATTLE)
    k = sc * ROOM_TO_BATTLE
    glows = [[int(round(sx + (glow_at[0] - fw.shape[1] / 2) * k)), int(round(sy + (glow_at[1] - fw.shape[0]) * k)), "f6cf7a", 2]]
    bulb = grade(bulb_sprite(), dawn)
    for bz in sorted(BULBS, reverse=True):
        bx, by, bs = v.sprite(bulb, 0, bz, Y=CEIL - 52, anchor=(0.5, 1.0), scale=ROOM_TO_BATTLE)
        kk = bs * ROOM_TO_BATTLE
        glows.append([int(round(bx)), int(round(by - 4 * kk)), "fff0c4", 2 if bz < 700 else 1])
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    return cv, glows


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    cv, glows = render(False)
    cv.save(os.path.join(out, "battle-far.png"))
    cvd, _ = render(True)
    cvd.save(os.path.join(out, "battle-far-dawn.png"))
    res = f"res://assets/art/rooms/{ROOM}/"
    return {
        "far": res + "battle-far.png",
        "far_dawn": res + "battle-far-dawn.png",
        "layers": [
            {"kind": "twinkle", "points": glows, "rate": 1.0, "min": 0.6},
            {"kind": "fauna", "fauna": [
                {"kind": "macky_ticket", "x": 40, "y": 60, "fly": 10.0, "rate": 5.0},
                {"kind": "macky_ticket", "x": 300, "y": 30, "fly": 7.0, "rate": 4.0},
                {"kind": "macky_ticket", "x": 520, "y": 84, "fly": 12.0, "rate": 6.0},
                {"kind": "macky_ticket", "x": 180, "y": 110, "fly": 8.0, "rate": 5.0}]},
            {"kind": "particles", "style": "dust", "count": 14, "rect": [200, 40, 240, 110], "speed": [0, 3], "color": "f8e0b0"},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
