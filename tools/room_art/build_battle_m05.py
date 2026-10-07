"""Battle backdrop for the balcony (M05): Rook's LAST CALL.

A new angle on the room: we stand in the balcony's cross-aisle and look along it to its far end,
where the ONE EXIT door waits under a red LAST CALL lightbox, ringed with marquee bulbs. On the
right the balcony's seat tiers climb away in rows of red velvet, a RESERVED card on almost every
seat back; small amber step lights mark the stair aisles. On the left the brass-railed parapet
runs into the distance, and over it the void of the house: two crystal chandeliers hanging at
eye level, the coffered ceiling far above, and across the house the proscenium wall, where VAL's
graduation set glows teal behind the swagged curtain. A low coffered soffit roofs the aisle with
small downlights pooling on the carpet.
Layers: more RESERVED cards keep appearing on the empty seats in waves (blinks), cards glint, the
bulbs around the exit chase, LAST CALL flickers, a follow-spot from the house sweeps across the
aisle, dust hangs in the void, a moth bats at the exit sign.
far_dawn / near_dawn: house lights up, the cards gone, the stage under grey work light, the exit
door open on morning with sunlight falling down the aisle from the stair hall beyond."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, mix, text, text_width
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, SS
from lib_macky2 import (HOUSE, HOUSE_DAWN, GILT, SEAT, VELVET, CARD, CARD_RED, CARPET_M, OAKF, OAK_SUN, VAL_TEAL,
                        CYC_NIGHT, CYC_DAWN, CHAIR, CU_GOLD, CU_BLACK, chandelier, lightbox_sign, halo, _rng)

ROOM = "M05"
INK = "#10121e"
PX = -330.0                      # the parapet (inner face) along the left of the aisle
X0 = 200.0                       # first seat riser on the right
TIER_D, TIER_H, NT = 44.0, 18.0, 8
Z0, ZE = 150.0, 900.0            # geometry starts just behind the camera's near field; end wall
CEIL = 230.0                     # aisle soffit
HOUSE_CEIL = 560.0
WALL_X = X0 + NT * TIER_D        # back wall of the balcony behind the top row
STAGE_X = -900.0                 # the proscenium wall across the void
PROS = (1040.0, 1700.0, -320.0, 250.0)       # opening on the stage wall: Z0, Z1, Y0, Y1
DOOR = (-95.0, 5.0, 132.0)       # exit door X0, X1, height
SEAT_DZ = 26.0
CHANDS = [(-560.0, 700.0, 205.0), (-610.0, 1320.0, 225.0)]   # X, Z, Y of the crown
DOWN_X = (-150.0, 30.0)          # soffit downlight lines
DOWN_DZ = 150.0
BEAM_FROM = (-30, 8)


def is_extra(r, k):
    return hash2(np.int64(r), np.int64(k), 77) >= 0.6


def seat_index(Z):
    return np.floor((Z - Z0) / SEAT_DZ).astype(np.int64)


def aisle_gap(k):
    return (k % 11) == 5


class Scene:
    def __init__(self, dawn):
        self.dawn = dawn
        self.v = View(horizon=98, cam=52)
        self.ids = np.full(self.v.a.shape[:2], -1, np.int64)
        self.house = pal_array(HOUSE_DAWN if dawn else HOUSE)
        self.haze = "#3a2a2c" if dawn else "#140e18"

    def track(self, call, shader, *args, ids=None, **kw):
        """Run a View paint call and keep the id buffer (which seat card owns each subpixel)."""
        cap = {}

        def f(*a):
            out = shader(*a)
            cap["alpha"] = out[..., 3]
            cap["ids"] = ids(*a) if ids is not None else None
            return out
        if call == "ground":
            m = self.v.ground(f, **kw)
        elif call == "plane":
            m = self.v.plane(args[0], args[1], f, **kw)
        else:
            m = self.v.back(args[0], f, **kw)
        if m is None or not m.any() or "alpha" not in cap:
            return m
        cur = self.ids[m]
        al = cap["alpha"] > 0.5
        new = cap["ids"] if cap["ids"] is not None else np.full(cur.shape, -1, np.int64)
        cur[al] = new[al]
        self.ids[m] = cur
        return m


# ---------------------------------------------------------------------------------------------
def build_scene(dawn):
    s = Scene(dawn)
    v = s.v
    house = s.house
    gilt = pal_array(GILT)
    seat = pal_array(SEAT)
    carpet = pal_array(CARPET_M)
    vel = pal_array(VELVET)
    card = pal_array(CARD)

    # --- the void: house ceiling, the proscenium wall across the house, the far side wall ---
    def house_ceiling(X, Z):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        fx, fz = X / 120.0 - np.floor(X / 120.0), Z / 120.0 - np.floor(Z / 120.0)
        rgb[:] = house[4]
        rgb[(fx < 0.1) | (fz < 0.1)] = gilt[2]
        rgb[(fx > 0.22) & (fx < 0.78) & (fz > 0.22) & (fz < 0.78)] = house[2]
        rgb[(np.abs(fx - 0.5) < 0.06) & (np.abs(fz - 0.5) < 0.06)] = gilt[3]
        out = rgba_of(rgb)
        fog(out, Z, s.haze, 600, 3000, amount=0.6)
        out[..., 3] = ((X < PX) & (X > STAGE_X)).astype(np.float32)
        return out
    s.track("ground", house_ceiling, height=HOUSE_CEIL, y_from=-1.0, y_to=98.0, z_max=3200.0)

    def far_wall(X, Y):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        rgb[:] = house[3]
        bay = X / 160.0 - np.floor(X / 160.0)
        rgb[bay < 0.1] = house[5]
        for (y0, y1) in ((-120.0, -20.0), (60.0, 160.0)):
            box = (bay > 0.2) & (bay < 0.9) & (Y > y0) & (Y < y1)
            rgb[box] = house[0]
            rgb[box & (Y < y0 + 22)] = gilt[2]
        out = rgba_of(rgb)
        fog(out, np.full(X.shape, 3000.0), s.haze, 600, 3000, amount=0.6)
        return out
    s.track("back", far_wall, 3000.0, region=lambda X, Y: (X < PX) & (X > STAGE_X) & (Y < HOUSE_CEIL))

    z0p, z1p, y0p, y1p = PROS

    def stage_wall(u, Y, Z):
        n = u.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        rgb[:] = house[3]
        bay = Z / 210.0 - np.floor(Z / 210.0)
        rgb[(bay < 0.08)] = house[5]
        for (y0, y1) in ((-150.0, -40.0), (60.0, 170.0)):          # boxes either side of the arch
            box = (bay > 0.16) & (bay < 0.9) & (Y > y0) & (Y < y1)
            rgb[box] = house[0]
            rgb[box & (Y < y0 + 20)] = gilt[2]
            rgb[box & (Y < y0 + 20) & (np.floor(Z / 9) % 2 == 0)] = house[4]
            rgb[box & (Y > y1 - 18)] = vel[3]
        frame = (Z > z0p - 60) & (Z < z1p + 60) & (Y > y0p) & (Y < y1p + 60)
        rgb[frame] = gilt[2]
        rgb[frame & ((Y > y1p + 40) | (Z < z0p - 48) | (Z > z1p + 48))] = gilt[4]
        opening = (Z > z0p) & (Z < z1p) & (Y > y0p) & (Y < y1p)
        cyc = pal_array(CYC_DAWN if dawn else CYC_NIGHT)
        rgb[opening] = cyc[2]
        rgb[opening & (Y > 120)] = cyc[1]
        # VAL's frame in the middle of the set, rows of mortarboards inside fading into the dark
        zc = (z0p + z1p) / 2
        fr = opening & (np.abs(Z - zc) < 150) & (Y > -20) & (Y < 192)
        inner = opening & (np.abs(Z - zc) < 134) & (Y > -4) & (Y < 176)
        teal = pal_array(VAL_TEAL)
        rgb[fr] = teal[4] if not dawn else teal[2]
        rgb[inner] = teal[1] if not dawn else cyc[3]
        # risers of ceremony chairs either side of the frame (rows of small backs)
        chairs = opening & (np.abs(Z - zc) > 170) & (Z > z0p + 80) & (Z < z1p - 80) & (Y < 40) & (Y > -160)
        crow = chairs & (((Y + 160) % 50) > 34) & (np.floor(Z / 18) % 2 == 0)
        rgb[crow] = pal_array([CHAIR[4]])[0]
        if not dawn:
            cardp = crow & (((Y + 160) % 50) > 40)
            rgb[cardp] = card[2]
        # flown chairs on lines and the banner along the top of the opening
        if not dawn:
            glowband = inner & (Y < 120)
            rgb[glowband] = teal[2]
            rgb[inner & (Y < 60)] = teal[3]
        ban = opening & (Y > y1p - 52) & (Y < y1p - 32) & (np.abs(Z - zc) < 240)
        rgb[ban] = pal_array([CU_BLACK[1] if not dawn else "#e6dcc4"])[0]
        rgb[ban & (np.abs(Y - (y1p - 42)) < 3) & (np.floor(Z / 16) % 3 != 0)] = pal_array([CU_GOLD[3] if not dawn else "#9a2a2c"])[0]
        # swagged valance and curtain legs inside the arch
        sw = (Z - z0p) / 132.0
        swag = opening & (Y > y1p - 14 - 14 * np.sin(np.pi * (sw - np.floor(sw))))
        rgb[swag] = vel[3]
        rgb[swag & (Y < y1p - 11 - 14 * np.sin(np.pi * (sw - np.floor(sw))))] = vel[5]
        legs = opening & ((Z < z0p + 70) | (Z > z1p - 70))
        rgb[legs] = vel[np.clip((np.floor(Z[legs] / 12) % 3).astype(int) + 2, 0, 6)]
        out = rgba_of(rgb)
        lit = out[opening, :3]
        if not dawn:
            warm_light(lit, np.hypot((Z[opening] - zc) * 0.5, (Y[opening] - 60) * 1.0), 330.0, colour="#58c0b8", strength=0.5)
        else:
            warm_light(lit, np.hypot((Z[opening] - zc) * 0.5, (Y[opening] + 40) * 1.0), 380.0, colour="#d8d0c0", strength=0.25)
        out[opening, :3] = lit
        fog(out, Z, s.haze, 700, 3000, amount=0.45)
        return out
    s.track("plane", stage_wall, (STAGE_X, Z0), (STAGE_X, 3000.0), y_max=HOUSE_CEIL, y_min=-600.0)

    # chandeliers hanging in the void (behind the parapet)
    chand_pts = []
    for (cx, cz, cy) in CHANDS:
        ch = chandelier(lit=1.0)
        sx, sy, sc = v.sprite(ch.a, cx, cz, Y=cy, anchor=(0.5, 0.0), scale=2.3)
        chand_pts.append((sx, sy, sc))

    # --- the balcony itself -----------------------------------------------------------------
    def soffit(X, Z):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        fx, fz = X / 70.0 - np.floor(X / 70.0), Z / 75.0 - np.floor(Z / 75.0)
        rgb[:] = house[2]
        rgb[(fx < 0.12) | (fz < 0.12)] = gilt[1]
        rgb[((fx < 0.05) | (fz < 0.05))] = gilt[3]
        rgb[(fx > 0.25) & (fx < 0.75) & (fz > 0.25) & (fz < 0.75)] = house[1]
        out = rgba_of(rgb)
        for dx in DOWN_X:
            d = np.hypot(X - dx, ((Z - Z0) % DOWN_DZ - DOWN_DZ / 2) * 1.0)
            if not dawn:
                warm_light(out[..., :3], d, 34.0, colour="#f6cf7a", strength=0.4)
        fog(out, Z, s.haze, 300, 1100, amount=0.55)
        out[..., 3] = ((X >= PX) & (X <= WALL_X) & (Z < ZE - 0.5)).astype(np.float32)
        return out
    s.track("ground", soffit, height=CEIL, y_from=-1.0, y_to=98.0, z_max=ZE)

    def end_wall(X, Y):
        n = X.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        rgb[:] = house[3]
        st = X / 22.0 - np.floor(X / 22.0)
        rgb[st < 0.5] = house[2]
        rgb[np.abs(st - 0.5) < 0.05] = gilt[1]
        dado = Y < 34
        rgb[dado] = pal_array(OAK_SUN if dawn else OAKF)[2]
        rgb[np.abs(Y - 34) < 1.5] = gilt[3]
        rgb[np.abs(Y - (CEIL - 8)) < 4] = gilt[2]
        dx0, dx1, dh = DOOR
        surround = (X > dx0 - 16) & (X < dx1 + 16) & (Y < dh + 20)
        rgb[surround] = gilt[2]
        rgb[surround & ((X < dx0 - 12) | (X > dx1 + 12) | (Y > dh + 16))] = gilt[4]
        door = (X > dx0) & (X < dx1) & (Y < dh)
        if not dawn:
            rgb[door] = vel[3]
            rgb[door & ((np.floor(X / 9) + np.floor(Y / 9)) % 2 == 0)] = vel[2]
            rgb[door & (np.abs(X - (dx0 + dx1) / 2) < 2)] = pal_array(["#1a0a10"])[0]
            for px_ in (dx0 + 25, dx1 - 25):
                port = door & (np.hypot(X - px_, Y - 92) < 11)
                rgb[port] = pal_array(["#f6cf7a"])[0]
                rgb[door & (np.abs(np.hypot(X - px_, Y - 92) - 12) < 2)] = gilt[4]
        else:
            # thrown open: the stair hall beyond full of morning
            rgb[door] = pal_array(["#f8d8a0"])[0]
            rgb[door & (X < dx0 + 18)] = pal_array(["#fff0c8"])[0]
            rgb[door & (Y < 18)] = pal_array(["#e0b880"])[0]
            leaf = (X > dx0 - 4) & (X < dx0 + 6) & (Y < dh)
            rgb[leaf] = vel[2]
        out = rgba_of(rgb)
        fog(out, np.full(n, ZE), s.haze, 300, 1100, amount=0.45)
        return out
    s.track("back", end_wall, ZE, region=lambda X, Y: (X >= PX) & (X <= WALL_X) & (Y < CEIL) & (Y > -1))

    def back_wall(u, Y, Z):
        rgb = np.zeros((u.shape[0], 3), np.float32)
        rgb[:] = house[2]
        rgb[np.abs(Y - (CEIL - 8)) < 4] = gilt[2]
        rgb[(Z / 180.0 - np.floor(Z / 180.0)) < 0.08] = house[4]
        out = rgba_of(rgb)
        fog(out, Z, s.haze, 300, 1100, amount=0.55)
        return out
    s.track("plane", back_wall, (WALL_X, Z0), (WALL_X, ZE), y_max=CEIL)

    # seat tiers, the highest (furthest from the aisle) first
    for r in reversed(range(NT)):
        xr = X0 + r * TIER_D
        hr = (r + 1) * TIER_H
        hp = r * TIER_H
        rf = float(r)

        def tread(X, Z, xr=xr):
            rgb = np.zeros((X.shape[0], 3), np.float32)
            rgb[:] = carpet[2]
            out = rgba_of(rgb)
            fog(out, Z, s.haze, 300, 1100, amount=0.55)
            out[..., 3] = ((X >= xr) & (X < xr + TIER_D) & (Z < ZE - 0.5)).astype(np.float32)
            return out
        if hr < v.cam - 2:
            s.track("ground", tread, height=hr, y_from=98.0, z_max=ZE)

        def back_face(u, Y, Z, hr=hr, rf=rf):
            n = u.shape[0]
            rgb = np.zeros((n, 3), np.float32)
            k = seat_index(Z)
            fz = (Z - Z0) / SEAT_DZ - k
            yy = Y - hr
            rgb[:] = seat[3]
            rgb[yy > 30] = seat[5]
            rgb[(yy > 33)] = seat[2]
            rgb[(yy < 30) & (np.floor(yy / 6) % 2 == 0) & (np.abs(fz - 0.5) < 0.05)] = seat[2]
            rgb[(fz < 0.1) | (fz > 0.9)] = seat[1]
            cardm = (yy > 19) & (yy < 26) & (np.abs(fz - 0.5) < 0.2)
            cid = (rf * 1000 + k).astype(np.int64)
            extra = hash2(np.full(n, int(rf), np.int64), k, 77) >= 0.6
            paint = cardm & ~extra & (not dawn)
            rgb[paint] = card[2]
            rgb[paint & (yy > 24)] = card[1]
            rgb[paint & (np.abs(yy - 22.5) < 0.8)] = pal_array([CARD_RED])[0]
            out = rgba_of(rgb)
            fog(out, Z, s.haze, 300, 1100, amount=0.55)
            gap = (fz < 0.04) | (fz > 0.96) | aisle_gap(k)
            out[..., 3] = (~gap).astype(np.float32)
            return out

        def back_ids(u, Y, Z, hr=hr, rf=rf):
            k = seat_index(Z)
            fz = (Z - Z0) / SEAT_DZ - k
            yy = Y - hr
            cardm = (yy > 19) & (yy < 26) & (np.abs(fz - 0.5) < 0.2) & ~aisle_gap(k)
            return np.where(cardm, (int(rf) * 1000 + k).astype(np.int64), -1)
        s.track("plane", back_face, (xr + 32, Z0), (xr + 32, ZE), y_max=hr + 36, y_min=hr, ids=back_ids)

        def cushion(X, Z, xr=xr):
            k = seat_index(Z)
            fz = (Z - Z0) / SEAT_DZ - k
            rgb = np.zeros((X.shape[0], 3), np.float32)
            rgb[:] = seat[4]
            rgb[(X > xr + 28)] = seat[2]
            rgb[(X < xr + 15)] = seat[5]
            out = rgba_of(rgb)
            fog(out, Z, s.haze, 300, 1100, amount=0.55)
            out[..., 3] = ((X >= xr + 12) & (X < xr + 32) & (fz > 0.08) & (fz < 0.92) & ~aisle_gap(k) & (Z < ZE - 0.5)).astype(np.float32)
            return out
        if hr + 14 < v.cam - 2:
            s.track("ground", cushion, height=hr + 14, y_from=98.0, z_max=ZE)

        def riser(u, Y, Z, hr=hr):
            rgb = np.zeros((u.shape[0], 3), np.float32)
            rgb[:] = carpet[1]
            rgb[Y > hr - 3] = gilt[3]
            rgb[Y > hr - 1.2] = gilt[5]
            k = seat_index(Z)
            out = rgba_of(rgb)
            fog(out, Z, s.haze, 300, 1100, amount=0.55)
            return out
        s.track("plane", riser, (xr, Z0), (xr, ZE), y_max=hr, y_min=hp)

    # --- the aisle floor and the parapet ------------------------------------------------------
    def aisle(X, Z):
        n = X.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        rgb[:] = carpet[3]
        fu, fw = X / 46.0 - np.floor(X / 46.0), Z / 46.0 - np.floor(Z / 46.0)
        d = np.abs(fu - 0.5) + np.abs(fw - 0.5)
        rgb[d < 0.2] = carpet[4]
        rgb[d < 0.06] = carpet[5]
        rgb[(np.abs(d - 0.5) < 0.03)] = carpet[2]
        border = (X < PX + 30) | (X > X0 - 30)
        rgb[border] = carpet[2]
        rgb[(np.abs(X - (PX + 26)) < 1.6) | (np.abs(X - (X0 - 26)) < 1.6)] = carpet[5]
        out = rgba_of(rgb)
        if not dawn:
            for dx in DOWN_X:
                dd = np.hypot(X - dx, ((Z - Z0) % DOWN_DZ - DOWN_DZ / 2) * 1.0)
                warm_light(out[..., :3], dd, 70.0, colour="#f6cf7a", strength=0.32)
            warm_light(out[..., :3], np.hypot((X + 45) * 0.8, (Z - ZE) * 0.5), 140.0, colour="#e84a3a", strength=0.4)
        else:
            # sun from the open door, a long bright tongue down the aisle
            sun = (np.abs(X + 45 + (ZE - Z) * 0.05) < 50 + (ZE - Z) * 0.08) & (Z > 360)
            out[sun, :3] = out[sun, :3] * 0.72 + pal_array(["#f8d49a"])[0] * 0.28
            core = (np.abs(X + 45 + (ZE - Z) * 0.05) < 22 + (ZE - Z) * 0.03) & (Z > 520)
            out[core, :3] = out[core, :3] * 0.7 + pal_array(["#fff0c8"])[0] * 0.3
        fog(out, Z, s.haze, 300, 1100, amount=0.5)
        out[..., 3] = ((X >= PX) & (X < X0 + 1) & (Z < ZE - 0.5)).astype(np.float32)
        return out
    s.track("ground", aisle, z_max=ZE)

    def parapet(u, Y, Z):
        n = u.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        oak = pal_array(OAK_SUN if dawn else OAKF)
        rgb[:] = oak[2]
        pz = Z / 90.0 - np.floor(Z / 90.0)
        panel = (pz > 0.08) & (pz < 0.92) & (Y > 6) & (Y < 30)
        rgb[panel] = oak[3]
        rgb[panel & ((pz < 0.12) | (Y > 27))] = gilt[2]
        rgb[Y < 4] = oak[1]
        cap = (Y >= 34) & (Y < 46)
        rgb[cap] = vel[3]
        rgb[cap & (Y > 43)] = vel[5]
        rgb[cap & (Y < 36)] = vel[1]
        post = (Y >= 46) & ((Z / 110.0 - np.floor(Z / 110.0)) < 0.045)
        rgb[post] = gilt[3]
        tube = (Y >= 58) & (Y < 63)
        rgb[tube] = gilt[4]
        rgb[tube & (Y > 61.5)] = gilt[5]
        out = rgba_of(rgb)
        fog(out, Z, s.haze, 300, 1100, amount=0.5)
        out[..., 3] = ((Y < 46) | post | tube).astype(np.float32)
        return out
    s.track("plane", parapet, (PX, Z0), (PX, ZE), y_max=63.0)
    v.rows(156, 360, INK, 0.0, 0.62)
    return s, chand_pts


def finish(s, chand_pts, dawn):
    v = s.v
    cv = v.reduce(112)
    # chandelier chains up into the dark of the house ceiling (1:1)
    for (sx, sy, sc) in chand_pts:
        x = int(round(sx))
        for y in range(0, int(round(sy))):
            cv.px(x, y, GILT[3] if y % 3 else GILT[1])
    # the exit: LAST CALL lightbox above, a ring of marquee bulbs around the door surround
    dx0, dx1, dh = DOOR
    ax, ay = v.project(dx0 - 16, dh + 20, ZE)
    bx, by = v.project(dx1 + 16, 0, ZE)
    x0, y0, x1, y1 = int(round(ax)), int(round(ay)), int(round(bx)), int(round(by))
    bulbs = []
    for x in range(x0, x1 + 1, 3):
        bulbs.append((x, y0 - 1))
    for y in range(y0 + 2, y1 - 1, 3):
        bulbs.append((x0 - 1, y)); bulbs.append((x1 + 1, y))
    for (x, y) in bulbs:
        cv.px(x, y, "#fff0c4" if not dawn else "#c8b8a0")
    lw = text_width("LAST CALL") + 8
    cx = (x0 + x1) // 2
    sign = (cx - lw // 2, y0 - 17)
    lightbox_sign(cv, sign[0], sign[1], "LAST CALL", lit=False)
    return cv, bulbs, sign, (x0, y0, x1, y1)


def card_rects(s):
    """Screen boxes of the visible card areas, from the id buffer, split into painted / extra."""
    ids = s.ids
    out = {}
    ys, xs = np.nonzero(ids >= 0)
    if len(ys) == 0:
        return [], []
    vals = ids[ys, xs]
    order = np.argsort(vals)
    vals, ys, xs = vals[order], ys[order], xs[order]
    uniq, starts = np.unique(vals, return_index=True)
    ends = list(starts[1:]) + [len(vals)]
    crisp, extra = [], []
    for cid, a, b in zip(uniq, starts, ends):
        if b - a < 6:
            continue
        x0, x1 = xs[a:b].min() / SS, (xs[a:b].max() + 1) / SS
        y0, y1 = ys[a:b].min() / SS, (ys[a:b].max() + 1) / SS
        rx, ry = int(np.floor(x0 + 0.3)), int(np.floor(y0 + 0.3))
        rw, rh = max(1, int(round(x1 - x0))), max(1, int(round(y1 - y0)))
        if ry > 150:
            continue
        r, k = divmod(int(cid), 1000)
        (extra if is_extra(r, k) else crisp).append((rx, ry, rw, rh))
    return crisp, extra


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    s, chand = build_scene(False)
    cv, bulbs, sign, door = finish(s, chand, False)
    crisp, extra = card_rects(s)
    cv.save(os.path.join(out, "battle-far.png"))
    sd, chd = build_scene(True)
    cvd, _, _, _ = finish(sd, chd, True)
    cvd.save(os.path.join(out, "battle-far-dawn.png"))

    # LAST CALL lit, with its red halo; the flicker pattern drops it for a beat now and then
    lw = text_width("LAST CALL") + 8
    on = Canvas(lw + 40, 40)
    halo(on, on.w // 2, 21, 30, "#e84a3a", 0.16)
    lightbox_sign(on, 20, 15, "LAST CALL", lit=True)
    on.save(os.path.join(out, "battle-lastcall.png"))

    layers = []
    # cards keep appearing on the empty seats, wave after wave, then all vanish together
    rng = _rng(91)
    order = rng.permutation(len(extra))
    waves = 4
    for k in range(waves):
        pts = [extra[int(i)] for i in order[k::waves]]
        rects = []
        for (x, y, w, h) in pts:
            rects.append([x, y, w, h, "ece2c8"])
            if h >= 3:
                rects.append([x, y + h // 2, w, 1, "9a2a2c"])
        pat = "0" * (k + 1) + "1" * (waves + 2 - k) + "00"
        layers.append({"kind": "blink", "pattern": pat, "rate": 1.1, "rects": rects})
    glints = [[x + w // 2, y + h // 2, "fffaf0", 1] for (x, y, w, h) in crisp if w >= 2]
    rng.shuffle(glints)
    # chandelier candles and soffit downlights
    candles = []
    for (sx, sy, sc) in chand:
        for dx in range(-20, 21, 5):
            yy = 20 + int(3 * (1 - (dx / 20) ** 2)) - 7
            candles.append([int(round(sx + dx * sc)), int(round(sy + yy * sc)), "fff4d8", 1])
    downs = []
    for dx in DOWN_X:
        z = Z0 + DOWN_DZ / 2
        while z < ZE:
            if z > 260:
                x, y = s.v.project(dx, 230.0, z)
                downs.append([int(round(x)), int(round(y)), "fde9b6", 1])
            z += DOWN_DZ
    # chase around the exit: three interleaved sets of bulbs
    chase = []
    for j in range(3):
        rects = [[x, y, 1, 1, "fffbe0"] for i, (x, y) in enumerate(bulbs) if i % 3 == j]
        pat = ["0", "0", "0"]
        pat[j] = "1"
        chase.append({"kind": "blink", "pattern": "".join(pat), "rate": 7.0, "rects": rects})
    layers += [
        {"kind": "twinkle", "points": glints[:40], "rate": 1.4, "min": 0.2},
        {"kind": "twinkle", "points": candles + downs, "rate": 1.2, "min": 0.5},
    ] + chase + [
        {"kind": "blink", "pattern": "1111111011110110", "rate": 3.0, "texture": res + "battle-lastcall.png",
         "x": sign[0] - 20, "y": sign[1] - 15},
        {"kind": "beam", "x": BEAM_FROM[0], "y": BEAM_FROM[1], "angle": 38, "sweep": 9, "period": 13, "phase": 0.6,
         "length": 330, "width": 70, "color": "e8ecff", "alpha": 0.11, "floor": 150},
        {"kind": "particles", "style": "dust", "count": 24, "rect": [0, 10, 260, 110], "speed": [1, 2], "color": "f6e0b0"},
        {"kind": "particles", "style": "dust", "count": 14, "rect": [180, 60, 260, 90], "speed": [-1, 1], "color": "e8ecff"},
        {"kind": "fauna", "fauna": [{"kind": "lamp_moth", "x": sign[0] + lw // 2, "y": sign[1] + 4, "range": 7, "speed": 2.2,
                                     "rate": 9.0}]},
    ]
    return {
        "far": res + "battle-far.png",
        "far_dawn": res + "battle-far-dawn.png",
        "layers": layers,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:400])
