"""Battle backdrop for the graduation stage (M06): VAL, "everyone you could be".

The reverse of the room: we stand on the stage among VAL's set and look out into the house. The
oak deck runs out to the footlights at the lip; beyond it the whole of Macky's auditorium faces us,
row upon row of red velvet seats rising away, a RESERVED card glowing on almost every one, the
stair aisles marked by small amber lights. Two tiers of boxes line the side walls, a crystal
chandelier hangs in the middle of the house, the balcony's gilt fascia crosses the back with more
carded rows climbing to the booth, and under the balcony the lobby doors wait beneath green EXIT
signs. The house curtain frames the picture: a swagged red valance across the top, the gathered
legs at both sides. Teal light from VAL's frame behind us washes the deck.
Layers: cards appearing on the empty seats in waves, card glints, a follow-spot from the booth
sweeping the deck and a teal special from a box, footlights and candles breathing, EXIT signs,
dust in the beams.
far_dawn: house lights up, the cards gone, the windows full of sunrise, the lobby doors open on
morning, the footlights off and the deck under plain work light."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, mix, text, text_width
from persp import View, hash2, fog, pal_array, rgba_of, warm_light
from lib_macky2 import (HOUSE, HOUSE_DAWN, GILT, SEAT, VELVET, CARD, CARD_RED, CARPET_M, OAKF, OAK_SUN, VAL_TEAL, EXIT,
                        chandelier, halo, _rng, IdView)

ROOM = "M06"
INK = "#10121e"
LIP_Z = 440.0                    # front of the stage deck
PIT_Z = 548.0                    # pit rail
HW = 520.0                       # half width of the house (side walls)
ROW0, ROWD, NROWS = 584.0, 34.0, 30
RAKE = 0.07
FLOOR = -40.0                    # house floor below the deck
BAL_Z, BAL_Y0, BAL_Y1 = 1150.0, 178.0, 232.0     # balcony fascia
BACK_Z = 1600.0
CEIL = 430.0
SEAT_W = 26.0
AISLES = (170.0, 205.0)          # |X| range of the two stair aisles
CHAND = (0.0, 1000.0, 262.0)     # X, Z, crown Y: hanging just in front of the balcony
DOORS = (-300.0, 0.0, 300.0)     # lobby door pairs (X centre) under the balcony


def hf(Z):
    return FLOOR + np.maximum(0.0, Z - ROW0) * RAKE


def hb(Z):
    return 196.0 + np.maximum(0.0, Z - BAL_Z) * 0.42


def extra(cid):
    return hash2(np.int64(cid), np.int64(cid // 7), 55) >= 0.62


def build_scene(dawn):
    v = View(horizon=98, cam=52)
    iv = IdView(v)
    house = pal_array(HOUSE_DAWN if dawn else HOUSE)
    gilt = pal_array(GILT)
    seat = pal_array(SEAT)
    vel = pal_array(VELVET)
    card = pal_array(CARD)
    carpet = pal_array(CARPET_M)
    haze = "#4a3a38" if dawn else "#140e18"

    # --- ceiling, back walls, balcony -----------------------------------------------------------
    def ceiling(X, Z):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        fx, fz = X / 110.0 - np.floor(X / 110.0), Z / 110.0 - np.floor(Z / 110.0)
        rgb[:] = house[4]
        rgb[(fx < 0.1) | (fz < 0.1)] = gilt[2]
        rgb[(fx > 0.24) & (fx < 0.76) & (fz > 0.24) & (fz < 0.76)] = house[2]
        out = rgba_of(rgb)
        fog(out, Z, haze, 800, 2200, amount=0.5)
        return out
    iv.paint("ground", ceiling, height=CEIL, y_from=-1.0, y_to=98.0, z_max=BACK_Z)

    def back_upper(X, Y):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        rgb[:] = house[3]
        # the booth window at the top centre of the balcony
        booth = (np.abs(X) < 60) & (Y > 330) & (Y < 380)
        rgb[booth] = pal_array(["#2a2c3a" if not dawn else "#5a5250"])[0]
        rgb[booth & (np.abs(X) < 8)] = pal_array(["#fff4d8" if not dawn else "#8a7a6a"])[0]
        out = rgba_of(rgb)
        fog(out, np.full(X.shape, BACK_Z), haze, 800, 2200, amount=0.5)
        return out
    iv.paint("back", back_upper, BACK_Z, region=lambda X, Y: (np.abs(X) < HW) & (Y > BAL_Y0) & (Y < CEIL))

    # balcony rows climbing to the booth, far to near
    for j in reversed(range(12)):
        zb = BAL_Z + 34 + j * 34
        y0 = float(hb(zb))

        def brow(X, Y, j=j, y0=y0):
            n = X.shape[0]
            rgb = np.zeros((n, 3), np.float32)
            yy = Y - y0
            c = np.floor((X + HW) / SEAT_W)
            fx = (X + HW) / SEAT_W - c
            rgb[:] = seat[3]
            rgb[yy < 12] = seat[1]
            rgb[(yy >= 12) & (yy < 17)] = seat[5]
            rgb[yy > 32] = seat[5]
            if not dawn:
                cm = (yy > 22) & (yy < 29) & (np.abs(fx - 0.5) < 0.24) & ~extra((5000 + j * 100 + c).astype(np.int64))
                rgb[cm] = card[2]
            out = rgba_of(rgb)
            fog(out, np.full(n, zb), haze, 800, 2200, amount=0.5)
            return out

        def bids(X, Y, j=j, y0=y0):
            yy = Y - y0
            c = np.floor((X + HW) / SEAT_W)
            fx = (X + HW) / SEAT_W - c
            cm = (yy > 22) & (yy < 29) & (np.abs(fx - 0.5) < 0.24)
            return np.where(cm, (5000 + j * 100 + c).astype(np.int64), -1)
        iv.paint("back", brow, zb, ids=bids,
                 region=lambda X, Y, y0=y0: (np.abs(X) < HW - 30) & (Y > y0 - 30) & (Y < y0 + 34) &
                 ((X + HW) / SEAT_W - np.floor((X + HW) / SEAT_W) > 0.06) & ~((np.abs(X) > 160) & (np.abs(X) < 190)))

    def fascia(X, Y):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        rgb[:] = house[4]
        rgb[Y > BAL_Y1 - 10] = vel[3]
        rgb[Y > BAL_Y1 - 3] = vel[5]
        rgb[(Y < BAL_Y1 - 10) & (Y > BAL_Y1 - 13)] = gilt[4]
        rgb[Y < BAL_Y0 + 5] = gilt[2]
        pan = (X / 90.0 - np.floor(X / 90.0))
        cart = (pan > 0.15) & (pan < 0.85) & (Y > BAL_Y0 + 10) & (Y < BAL_Y1 - 18)
        rgb[cart] = house[3]
        rgb[cart & ((pan < 0.19) | (pan > 0.81) | (Y < BAL_Y0 + 13) | (Y > BAL_Y1 - 21))] = gilt[3]
        rgb[(np.abs(pan - 0.5) < 0.05) & (np.abs(Y - (BAL_Y0 + BAL_Y1 - 8) / 2) < 6)] = gilt[4]
        out = rgba_of(rgb)
        fog(out, np.full(X.shape, BAL_Z), haze, 800, 2200, amount=0.45)
        return out
    iv.paint("back", fascia, BAL_Z, region=lambda X, Y: (np.abs(X) < HW) & (Y > BAL_Y0) & (Y < BAL_Y1))

    def under_back(X, Y):
        n = X.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        rgb[:] = house[2]
        rgb[Y < hf(BACK_Z) + 26] = pal_array(OAK_SUN if dawn else OAKF)[2]
        for dx in DOORS:
            fr = (np.abs(X - dx) < 52) & (Y < hf(BACK_Z) + 122)
            rgb[fr] = gilt[2]
            d = (np.abs(X - dx) < 44) & (Y < hf(BACK_Z) + 114)
            if dawn:
                rgb[d] = pal_array(["#f6d49a"])[0]
                rgb[d & (np.abs(X - dx) < 14)] = pal_array(["#fff0c8"])[0]
            else:
                rgb[d] = vel[2]
                rgb[d & (np.abs(X - dx) < 1.5)] = vel[0]
                rgb[d & (np.abs(np.abs(X - dx) - 22) < 8) & (np.abs(Y - hf(BACK_Z) - 84) < 9)] = pal_array(["#f6cf7a"])[0]
        out = rgba_of(rgb)
        fog(out, np.full(n, BACK_Z), haze, 800, 2200, amount=0.45)
        return out
    iv.paint("back", under_back, BACK_Z, region=lambda X, Y: (np.abs(X) < HW) & (Y > FLOOR) & (Y < BAL_Y0))

    def soffit(X, Z):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        rgb[:] = house[2]
        fz = Z / 60.0 - np.floor(Z / 60.0)
        rgb[fz < 0.1] = house[1]
        out = rgba_of(rgb)
        fog(out, Z, haze, 800, 2200, amount=0.45)
        out[..., 3] = ((Z > BAL_Z) & (Z < BACK_Z - 0.5) & (np.abs(X) < HW)).astype(np.float32)
        return out
    iv.paint("ground", soffit, height=BAL_Y0, y_from=-1.0, y_to=98.0, z_max=BACK_Z)

    # --- side walls with two tiers of boxes -----------------------------------------------------
    def side_wall(u, Y, Z):
        n = u.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        rgb[:] = house[3]
        bay = Z / 170.0 - np.floor(Z / 170.0)
        pil = bay < 0.1
        rgb[pil] = house[5]
        rgb[pil & (bay < 0.03)] = house[6]
        for (y0, y1) in ((50.0, 140.0), (190.0, 280.0)):
            box = (bay > 0.16) & (bay < 0.94) & (Y > y0) & (Y < y1)
            rgb[box] = house[0]
            par = box & (Y < y0 + 26)
            rgb[par] = house[5]
            rgb[par & (Y > y0 + 22)] = gilt[4]
            rgb[par & (Y < y0 + 4)] = gilt[2]
            rgb[par & (Y > y0 + 6) & (Y < y0 + 20) & (np.floor(Z / 7) % 2 == 0)] = house[3]
            dr = box & (Y > y1 - 16)
            rgb[dr] = vel[3]
            rgb[dr & (Y < y1 - 13)] = vel[5]
            ch = box & (Y > y0 + 26) & (Y < y0 + 44) & (np.floor(Z / 22) % 2 == 0)
            rgb[ch] = seat[3]
            if not dawn:
                cd = ch & (Y > y0 + 34) & (Y < y0 + 40)
                rgb[cd] = card[2]
        win = (bay > 0.34) & (bay < 0.76) & (Y > 310) & (Y < 400 - 60 * ((bay - 0.55) / 0.21) ** 2)
        rgb[win] = pal_array(["#f2b878" if dawn else "#1a2244"])[0]
        if dawn:
            rgb[win & (bay < 0.45)] = pal_array(["#fde2b0"])[0]
        rgb[(np.abs(Y - 300) < 4) & ~pil] = gilt[2]
        rgb[Y < FLOOR + 24] = pal_array(OAK_SUN if dawn else OAKF)[2]
        out = rgba_of(rgb)
        if not dawn:
            for k in range(8):                       # sconce glow between the boxes
                zc = 170.0 * k + 8
                warm_light(out[..., :3], np.hypot(Z - zc, (Y - 165) * 1.6), 60.0, colour="#f6cf7a", strength=0.35)
        fog(out, Z, haze, 800, 2200, amount=0.5)
        return out
    for side in (-1, 1):
        iv.paint("plane", side_wall, (side * HW, LIP_Z - 200), (side * HW, BACK_Z), y_max=CEIL, y_min=FLOOR)

    # chandelier in the middle of the house
    cx, cz, cy = CHAND
    sx, sy, sc = v.sprite(chandelier(lit=1.0).a, cx, cz, Y=cy, anchor=(0.5, 0.0), scale=2.6)
    chand = (sx, sy, sc)

    # --- the house rows, far to near ------------------------------------------------------------
    for i in reversed(range(NROWS)):
        zr = ROW0 + i * ROWD
        y0 = float(hf(zr))

        def row(X, Y, i=i, y0=y0, zr=zr):
            n = X.shape[0]
            rgb = np.zeros((n, 3), np.float32)
            yy = Y - y0
            c = np.floor((X + HW) / SEAT_W)
            fx = (X + HW) / SEAT_W - c
            rgb[:] = carpet[1]                                     # the riser/floor under the seats
            st = yy > 0
            rgb[st] = seat[2]
            rgb[st & (yy >= 10) & (yy < 15)] = seat[5]             # cushion front edge
            rgb[st & (yy >= 15)] = seat[3]
            rgb[st & (yy >= 15) & ((fx < 0.12) | (fx > 0.88))] = seat[2]
            rgb[st & (yy > 33)] = seat[5]
            if not dawn:
                cm = st & (yy > 23) & (yy < 30) & (np.abs(fx - 0.5) < 0.24) & ~extra((i * 100 + c).astype(np.int64))
                rgb[cm] = card[2]
                rgb[cm & (yy < 25)] = card[3]
                rgb[cm & (np.abs(yy - 27) < 0.8)] = pal_array([CARD_RED])[0]
            # stair aisles: carpet with an amber step light on each row
            ais = (np.abs(X) > AISLES[0]) & (np.abs(X) < AISLES[1])
            rgb[ais] = carpet[3]
            rgb[ais & (yy < 2)] = gilt[3]
            if not dawn:
                rgb[ais & (yy < 3) & (np.abs(np.abs(X) - 187) < 4)] = pal_array(["#f6b04a"])[0]
            out = rgba_of(rgb)
            if not dawn:
                warm_light(out[..., :3], np.full(n, (zr - ROW0) * 1.0), 420.0, colour="#58c0b8", strength=0.2)
            fog(out, np.full(n, zr), haze, 800, 2200, amount=0.5)
            ais_open = ais & (yy > 2)
            out[..., 3] = (~ais_open & ~((yy > 0) & ((fx < 0.04) | (fx > 0.96)))).astype(np.float32)
            return out

        def rids(X, Y, i=i, y0=y0):
            yy = Y - y0
            c = np.floor((X + HW) / SEAT_W)
            fx = (X + HW) / SEAT_W - c
            cm = (yy > 23) & (yy < 30) & (np.abs(fx - 0.5) < 0.24) & ~((np.abs(X) > AISLES[0]) & (np.abs(X) < AISLES[1]))
            return np.where(cm, (i * 100 + c).astype(np.int64), -1)
        iv.paint("back", row, zr, ids=rids,
                 region=lambda X, Y, y0=y0: (np.abs(X) < HW - 34) & (Y > y0 - ROWD * RAKE - 2) & (Y < y0 + 36))

    # the orchestra pit: dark, a brass rail, little music-stand lights
    def pit(X, Z):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        rgb[:] = pal_array(["#0c080c"])[0]
        out = rgba_of(rgb)
        out[..., 3] = ((Z > LIP_Z) & (Z < PIT_Z + 40)).astype(np.float32)
        return out
    iv.paint("ground", pit, height=FLOOR - 60, z_max=PIT_Z + 40)

    def pit_rail(X, Y):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        rgb[:] = vel[2]
        rgb[Y > FLOOR + 22] = gilt[4]
        rgb[Y > FLOOR + 25] = gilt[5]
        return rgba_of(rgb)
    iv.paint("back", pit_rail, PIT_Z, region=lambda X, Y: (np.abs(X) < HW - 30) & (Y > FLOOR) & (Y < FLOOR + 27))

    # --- the stage deck -------------------------------------------------------------------------
    oak = pal_array(OAK_SUN if dawn else OAKF)

    def deck(X, Z):
        n = X.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        b = np.floor(Z / 16.0)
        fz = Z / 16.0 - b
        off = hash2(b, 3) * 300
        seg = np.floor((X + off) / 300.0)
        tone = hash2(seg, b, 5)
        k = np.clip(2 + (tone > 0.5).astype(int) + (tone > 0.85).astype(int), 0, 6)
        rgb[:] = oak[k]
        rgb[fz < 0.1] = oak[1]
        rgb[((X + off) / 300.0 - seg) < 0.008] = oak[1]
        # spike tape and VAL's teal tape frame on the deck
        sp = hash2(np.floor(X / 40), np.floor(Z / 40), 8) > 0.965
        rgb[sp & (np.abs((X % 40) - 20) < 6) & (np.abs((Z % 40) - 20) < 1.2)] = pal_array(["#e0c040"])[0]
        tf = (np.abs(np.abs(X) - 230) < 2.5) & (Z > 250) & (Z < 400) | (np.abs(Z - 400) < 2.5) & (np.abs(X) < 230)
        rgb[tf] = pal_array(["#58c0b8" if not dawn else "#4a7a74"])[0]
        lip = Z > LIP_Z - 10
        rgb[lip] = oak[1]
        rgb[Z > LIP_Z - 3] = gilt[2]
        out = rgba_of(rgb)
        if not dawn:
            warm_light(out[..., :3], np.hypot(X * 0.7, (Z - 200) * 1.2), 300.0, colour="#58c0b8", strength=0.22)
            warm_light(out[..., :3], (LIP_Z - Z) * 1.0, 60.0, colour="#f6cf7a", strength=0.4)
        else:
            warm_light(out[..., :3], np.hypot(X * 0.5, (Z - 300) * 1.0), 380.0, colour="#f2e8d8", strength=0.3)
        out[..., 3] = (Z < LIP_Z).astype(np.float32)
        return out
    iv.paint("ground", deck, z_max=LIP_Z + 1)
    v.rows(156, 360, INK, 0.0, 0.62)
    return v, iv, chand


def frame(cv, dawn):
    """The house curtain at 1:1: swagged valance across the top, gathered legs at the sides."""
    W = 640
    for x in range(W):
        t = (x % 106) / 106
        d = int(round(12 * np.sin(np.pi * t)))
        for y in range(0, 10 + d):
            k = 3 if y < 8 else (4 if y < 8 + d - 2 else 2)
            cv.px(x, y, VELVET[k])
        cv.px(x, 10 + d, VELVET[5]); cv.px(x, 11 + d, VELVET[1])
        if (x // 2) % 2 == 0:
            cv.px(x, 12 + d, GILT[3])
    for k in range(0, W, 106):
        cv.rect(k - 1, 6, 3, 14, GILT[3]); cv.px(k, 20, GILT[4]); cv.px(k, 21, GILT[2])
    cv.hline(0, 0, W, GILT[2]); cv.hline(0, 1, W, GILT[4])
    for (x0, side) in ((0, 0), (W - 26, 1)):
        for xx in range(x0, x0 + 26):
            for y in range(0, 158):
                waist = 0 if y < 92 else int(6 * np.sin(np.pi * min(1.0, (y - 92) / 60)))
                edge = (xx - x0) if side == 1 else (x0 + 25 - xx)
                if side == 0 and xx > x0 + 25 - waist:
                    continue
                if side == 1 and xx < x0 + waist:
                    continue
                fold = (xx + (y // 40)) % 5
                cv.px(xx, y, VELVET[[2, 3, 4, 3, 2][fold]] if y < 156 else VELVET[1])
        ty = 96
        tx = x0 + (4 if side == 0 else 6)
        cv.rect(tx, ty, 16, 3, GILT[3]); cv.hline(tx, ty, 16, GILT[4])
        cv.rect(tx + (6 if side == 0 else 8), ty + 3, 3, 8, GILT[2]); cv.px(tx + (7 if side == 0 else 9), ty + 11, GILT[4])


def finish(v, iv, chand, dawn):
    cv = v.reduce(112)
    sx, sy, sc = chand
    for y in range(0, int(round(sy))):
        cv.px(int(round(sx)), y, GILT[3] if y % 3 else GILT[1])
    # footlights along the lip: little hooded lamps glowing up
    feet = []
    for X in np.arange(-430, 431, 48):
        x, y = v.project(X, 3.0, LIP_Z - 4)
        x, y = int(round(x)), int(round(y))
        if 26 < x < 614:
            cv.rect(x - 2, y, 5, 2, "#1a1214"); cv.hline(x - 1, y - 1, 3, "#fff0c4" if not dawn else "#6a5a4a")
            feet.append([x, y - 1, "fff0c4", 1])
    # brass sconces between the boxes on the side walls
    sconces = []
    for side in (-1, 1):
        for k in range(2, 9):
            x, y = v.project(side * HW, 165.0, 170.0 * k + 8)
            x, y = int(round(x)), int(round(y))
            if 28 < x < 612:
                cv.vline(x, y, 3, GILT[2]); cv.px(x, y - 1, "#fde9b6" if not dawn else "#c8b8a0")
                sconces.append([x, y - 1, "fde9b6", 1])
    # EXIT signs over the lobby doors
    exits = []
    for dx in DOORS:
        x, y = v.project(dx, hf(BACK_Z) + 132, BACK_Z)
        x, y = int(round(x)), int(round(y))
        cv.rect(x - 5, y - 2, 11, 5, "#0e1a14")
        cv.hline(x - 4, y, 9, EXIT[3] if not dawn else EXIT[2]); cv.px(x - 4, y - 1, EXIT[4] if not dawn else EXIT[2])
        exits.append([x, y, "9ef0c0", 1])
    frame(cv, dawn)
    return cv, feet + sconces, exits


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v, iv, chand = build_scene(False)
    cv, feet, exits = finish(v, iv, chand, False)
    boxes = iv.boxes(min_px=4, max_y=134)
    cv.save(os.path.join(out, "battle-far.png"))
    vd, ivd, chd = build_scene(True)
    cvd, _, _ = finish(vd, ivd, chd, True)
    cvd.save(os.path.join(out, "battle-far-dawn.png"))

    crisp = [b for cid, b in boxes.items() if not extra(cid)]
    extras = [b for cid, b in boxes.items() if extra(cid)]
    rng = _rng(71)
    layers = []
    order = rng.permutation(len(extras))
    waves = 4
    for k in range(waves):
        rects = []
        for i in order[k::waves]:
            x, y, w, h = extras[int(i)]
            rects.append([x, y, w, h, "ece2c8"])
            if h >= 3:
                rects.append([x, y + h - 2, w, 1, "9a2a2c"])
        pat = "0" * (k + 1) + "1" * (waves + 2 - k) + "00"
        layers.append({"kind": "blink", "pattern": pat, "rate": 1.0, "rects": rects})
    glints = [[x + w // 2, y + h // 2, "f2fff8", 1] for (x, y, w, h) in crisp if w >= 2]
    rng.shuffle(glints)
    sx, sy, sc = chand
    candles = [[int(round(sx + dx * sc)), int(round(sy + (13 + int(3 * (1 - (dx / 20) ** 2))) * sc)), "fff4d8", 1]
               for dx in range(-20, 21, 5)]
    bx, by = v.project(0.0, 356.0, BACK_Z - 10)
    layers += [
        {"kind": "twinkle", "points": glints[:44], "rate": 1.5, "min": 0.25},
        {"kind": "twinkle", "points": feet + candles, "rate": 1.1, "min": 0.55},
        {"kind": "twinkle", "points": exits, "rate": 0.6, "min": 0.7},
        {"kind": "beam", "x": int(bx), "y": int(by), "angle": 92, "sweep": 16, "period": 12, "phase": 0.0,
         "length": 150, "width": 74, "color": "e8f0ff", "alpha": 0.13, "floor": 152},
        {"kind": "beam", "x": 44, "y": 64, "angle": 32, "sweep": 6, "period": 9, "phase": 1.7,
         "length": 250, "width": 60, "color": "58c0b8", "alpha": 0.08, "floor": 160},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [240, 30, 170, 120], "speed": [1, 2], "color": "e8f0ff"},
        {"kind": "particles", "style": "dust", "count": 14, "rect": [40, 60, 240, 100], "speed": [2, 1], "color": "9ef0e0"},
    ]
    return {
        "far": res + "battle-far.png",
        "far_dawn": res + "battle-far-dawn.png",
        "layers": layers,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
