"""Battle backdrop for the Broadway underpass (U08): standing on the sunken path west of the bridge,
looking east along it. Sandstone and form-liner retaining walls run along both sides (Walt's tent,
crate and lantern against the left one), and just ahead is the little bridge: a sandstone-faced
portal, Broadway's deck with its parapet, railing and lamps on top, cars' lights crossing behind the
railing. The tunnel is only one road wide; through it the east ramp climbs toward the lit UMC,
whose upper floors and red-tile roof also show over the bridge."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, text, text_width
from surfaces import ashlar_wall
from facade import umc_facade
from props import lamp_post
from midlib import sprite_from_cell
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
import lib_eng as E
import build_u08 as R

ROOM = "U08"
INK = "#10121e"
HAZE = "#2a2438"
HW = 220.0           # half width of the path between the retaining walls
Z0 = 40.0            # nearest wall section
ZB = 600.0           # west face of the bridge (the portal)
ZT = 760.0           # east face: the tunnel is one road wide
TH = 112.0           # tunnel clearance
STREET = 128.0       # street level = top of the walls = Broadway's deck
RAMP_END = 1100.0    # the east ramp climbs from ZT to here...
TERRACE = 64.0       # ...up to the UMC side
ZU = 1200.0          # the UMC's facade
LANTERN = (-120.0, 520.0)
CAMP = [("crate", -72.0, 584.0), ("tent", -170.0, 556.0), ("lantern", *LANTERN)]
WALL_LIGHTS = [(-HW, 360.0), (HW, 300.0), (HW, 540.0)]      # (side X, depth)
TUNNEL_LIGHTS = [(-HW, 680.0), (HW, 680.0)]
RAMP_LAMPS = [(-176.0, 900.0), (176.0, 1010.0)]
PARAPET_LAMPS = [-150.0, 116.0]
LAMP_HEAD = 49      # texels from a lamp_post(60)'s foot up to its lantern


def wall_top(Z):
    """The walls are lower near the camera (the path ramps up behind us) and full height by the camp."""
    return np.clip(84 + (Z - Z0) * (STREET - 84) / (360 - Z0), 84, STREET)


def ramp_y(Z):
    return np.clip((Z - ZT) / (RAMP_END - ZT), 0, 1) * TERRACE


# ---------------------------------------------------------------- floors
def path_rgb(X, Z):
    """Concrete path slabs with saw joints, a dashed centre stripe and worn edge lines."""
    pal = pal_array(R.PATH)
    cell = hash2(np.floor(X / 72), np.floor(Z / 46), 3)
    rgb = pal[np.where(cell < 0.3, 3, np.where(cell < 0.8, 4, 5))].copy()
    agg = hash2(np.floor(X / 3), np.floor(Z / 5), 7)
    rgb[agg > 0.95] = pal[6]
    jx = np.abs(((X + 36) % 72) - 36) < 1.0
    jz = np.abs(((Z + 23) % 46) - 23) < 1.4
    rgb[jx | jz] = pal[2]
    wear = hash2(np.floor(X / 4), np.floor(Z / 14), 13) < 0.85
    yel = np.array(C("#e0b84a")[:3], np.float32)
    white = np.array(C("#d8d4cc")[:3], np.float32)
    m = (np.abs(X) < 2.6) & (((Z // 50) % 2) == 0) & wear
    rgb[m] = rgb[m] * 0.3 + yel * 0.7
    for lx in (-HW + 26, HW - 26):
        m = (np.abs(X - lx) < 2.2) & wear
        rgb[m] = rgb[m] * 0.5 + white * 0.5
    # shadow along both wall feet
    rgb[np.abs(X) > HW - 12] *= 0.78
    return rgb


def ground_shader(X, Z):
    rgb = path_rgb(X, Z)
    # cardboard flattened in front of the tent
    card = (X > -206) & (X < -96) & (Z > 500) & (Z < 560)
    rgb[card] = pal_array(R.CARD)[np.where(hash2(np.floor(X / 26), np.floor(Z / 22), 5)[card] < 0.5, 3, 2)]
    # under the bridge: dark, with the tunnel lights' pools
    rgb[(Z >= ZB) & (Z < ZT)] *= 0.42
    for (lx, lz) in TUNNEL_LIGHTS:
        warm_light(rgb, np.hypot((X - lx * 0.75) * 0.8, (Z - lz) * 1.4), 110, colour="#f6cf7a", strength=0.3)
    # the bridge's shadow reaching out of the portal
    near_portal = np.clip(1 - (ZB - Z) / 140, 0, 1) * (Z < ZB)
    rgb *= (1 - 0.35 * np.ceil(near_portal * 3) / 3)[:, None]
    warm_light(rgb, np.hypot(X - LANTERN[0], (Z - LANTERN[1]) * 1.3), 170, colour="#f6cf7a", strength=0.42)
    for (lx, lz) in WALL_LIGHTS:
        warm_light(rgb, np.hypot((X - lx * 0.85) * 0.8, (Z - lz) * 1.2), 120, colour="#f6cf7a", strength=0.2)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 500, 1400, amount=0.45)
    out[Z >= ZT - 0.5, 3] = 0.0
    return out


def ramp_layer(v):
    """The east ramp rising out of the tunnel (a sloped plane, intersected by hand)."""
    s = TERRACE / (RAMP_END - ZT)
    k = (v.sy - v.h0) / v.F
    with np.errstate(divide="ignore", invalid="ignore"):
        Z = (v.cam + s * ZT) / (s + k)
    mask = (s + k > 1e-4) & (Z >= ZT) & (Z <= RAMP_END)
    X = (v.sx[mask] - v.vx) * Z[mask] / v.F
    Zm = Z[mask]
    rgb = path_rgb(X, Zm)
    # grooves across the ramp, lighter as it climbs into the lamplight
    rgb[((Zm // 9) % 2) == 0] *= 0.9
    for (lx, lz) in RAMP_LAMPS:
        warm_light(rgb, np.hypot(X - lx * 0.8, (Zm - lz) * 0.8), 150, colour="#f6cf7a", strength=0.38)
    out = rgba_of(rgb)
    fog(out, Zm, HAZE, 600, 1500, amount=0.45)
    out[np.abs(X) >= HW, 3] = 0
    v._blend(mask, out)


def ceiling_shader(X, Z):
    """The deck's underside: board-formed concrete, lit by the tunnel's fixtures."""
    conc = pal_array(E.CONC)
    rgb = np.tile(conc[2], X.shape + (1,)).astype(np.float32)
    rgb[(Z % 40) < 3] = conc[1]
    for (lx, lz) in TUNNEL_LIGHTS:
        warm_light(rgb, np.hypot((X - lx * 0.6) * 0.5, Z - lz), 90, colour="#f6cf7a", strength=0.25)
    out = rgba_of(rgb)
    out[(Z < ZB) | (Z >= ZT - 0.5) | (np.abs(X) >= HW), 3] = 0.0
    return out


# ---------------------------------------------------------------- walls
def wall_texture(side, length):
    """A strip of retaining wall at room scale: rough plinth, coursed sandstone, fractured-rib form
    liner above, pilasters and the abutment quoins; a poster and tags on the left wall."""
    w, h = int(length / ROOM_TO_BATTLE) + 2, int(STREET / ROOM_TO_BATTLE) + 2
    cv = Canvas(w, h)
    R.form_liner(cv, 0, 0, w, h - 40, seed=20 + side)
    ashlar_wall(cv, 0, h - 40, w, 32, R.STONE, course=6, seed=21 + side, cap=False)
    cv.hline(0, h - 41, w, R.FORM[0])
    ashlar_wall(cv, 0, h - 8, w, 8, R.STONE_DK, course=7, seed=22 + side, cap=False)
    for px in range(60, w - 30, 110):
        R.quoins(cv, px, 0, 12, h - 8)
    R.quoins(cv, w - 16, 0, 16, h - 2, flip=True)
    if side < 0:
        rng = np.random.default_rng(3)
        for (x, y, col) in [(70, 30, "#c84a6a"), (190, 22, "#4ab0a8")]:
            px_, py_ = x, y
            for _ in range(20):
                cv.rect(px_, py_, 2, 2, C(col, 0.7))
                px_ += int(rng.choice([1, 2, 3])); py_ = min(max(py_ + int(rng.choice([-2, -1, 0, 1, 2])), y - 4), y + 5)
        # the LAST LIGHT paste-up behind the camp
        cv.rect(250, 36, 22, 28, "#d8ccb0"); cv.rect(253, 40, 16, 10, "#3a2a5a"); cv.rect(258, 42, 6, 5, "#f6cf7a")
        for yy in (53, 57):
            cv.hline(253, yy, 14, "#6a5a4a")
    return cv.a


def wall_shader(tex, flip, lights):
    h, w = tex.shape[:2]

    def shade_(u, Y, Z):
        tu = (w - 1 - u / ROOM_TO_BATTLE) if flip else u / ROOM_TO_BATTLE
        tv = (h - 2) - Y / ROOM_TO_BATTLE
        o = texture_lookup(tex, tu, tv, wrap=False)
        o[..., 3] = 1.0
        top = wall_top(Z)
        # sandstone coping along the top
        stone = pal_array(R.STONE)
        cop = (Y > top - 7) & (Y <= top)
        o[cop, :3] = stone[4]
        o[cop & (Y > top - 2), :3] = stone[5]
        o[(Y > top - 8) & (Y <= top - 7), :3] = stone[1]
        o[Y > top, 3] = 0.0
        rgb = o[..., :3]
        rgb *= 0.86
        for lz in lights:
            warm_light(rgb, np.hypot((Z - lz) * 0.9, (Y - 92) * 1.3), 80, colour="#f6cf7a", strength=0.3)
        if not flip:
            warm_light(rgb, np.hypot((Z - LANTERN[1]) * 1.1, Y * 0.9), 130, colour="#f6cf7a", strength=0.32)
        # the bridge's shadow on the last stretch before the portal
        near = np.clip(1 - (ZB - Z) / 120, 0, 1)
        rgb *= (1 - 0.3 * np.ceil(near * 3) / 3)[:, None]
        return fog(o, Z, HAZE, 400, 1400, amount=0.45)
    return shade_


def railing_shader(top_fn):
    """Iron railing standing on a wall top: posts, a mid rail and a top rail; gaps transparent."""
    def shade_(u, Y, Z):
        out = np.zeros(u.shape + (4,), np.float32)
        rel = Y - top_fn(Z)
        post = (u % 16) < 1.8
        rail = ((rel > 17) & (rel <= 19.5)) | ((rel > 9) & (rel <= 10.5))
        m = (rel > 0) & (rel <= 19.5) & (post | rail)
        out[m, :3] = pal_array(R.IRONC)[2]
        out[m & (rel > 18.5), :3] = pal_array(R.IRONC)[4]
        out[m, 3] = 1.0
        return fog(out, Z, HAZE, 400, 1400, amount=0.45)
    return shade_


def tunnel_wall_shader(u, Y, Z):
    """Inside the tunnel: form-liner concrete in the bridge's shade, lit by one fixture each side."""
    conc = pal_array(R.FORM)
    rib = np.floor(Z / 6) % 3
    rgb = conc[np.where(rib == 0, 1, np.where(rib == 1, 3, 2)).astype(int)].copy()
    rgb[Y < 10] = conc[1]
    rgb *= 0.75
    for (lx, lz) in TUNNEL_LIGHTS:
        warm_light(rgb, np.hypot((Z - lz) * 1.0, (Y - 80) * 1.2), 70, colour="#f6cf7a", strength=0.45)
    return rgba_of(rgb)


def ramp_wall_shader(u, Y, Z):
    """The east ramp's walls: sandstone, getting lower as the path climbs."""
    stone = pal_array(R.STONE)
    row = np.floor(Y / 9)
    col = np.floor((Z + (row % 2) * 9) / 18)
    t = hash2(col, row, 31)
    rgb = stone[np.where(t < 0.4, 2, np.where(t < 0.85, 3, 4))].copy()
    joint = ((Y % 9) < 1.2) | (((Z + (row % 2) * 9) % 18) < 1.5)
    rgb[joint] = stone[1]
    top = STREET - (Z - ZT) / (RAMP_END - ZT) * (STREET - TERRACE - 8)
    rgb[Y > top - 5] = stone[4]
    for (lx, lz) in RAMP_LAMPS:
        warm_light(rgb, np.abs(Z - lz) * 0.8 + np.abs(Y - 60) * 0.3, 110, colour="#f6cf7a", strength=0.3)
    out = rgba_of(rgb)
    out[(Y < ramp_y(Z)) | (Y > top), 3] = 0.0
    return fog(out, Z, HAZE, 600, 1500, amount=0.5)


# ---------------------------------------------------------------- the bridge face
def portal_shader(X, Y):
    """The bridge's west face: concrete deck fascia between the walls, the sandstone parapet with a
    coping, the iron railing on top (gaps transparent)."""
    out = np.zeros(X.shape + (4,), np.float32)
    stone = pal_array(R.STONE)
    form = pal_array(R.FORM)
    fascia = (np.abs(X) < HW) & (Y >= TH) & (Y < STREET)
    rib = (np.floor((X + 400) / 5) % 4).astype(int)
    out[fascia, :3] = form[np.array([2, 4, 5, 3])[rib[fascia]]]
    out[fascia & (Y < TH + 4), :3] = form[1]
    band = fascia & (Y >= STREET - 8)
    out[band, :3] = stone[3]
    out[band & (Y >= STREET - 2), :3] = stone[4]
    out[fascia, 3] = 1.0
    para = (Y >= STREET) & (Y < STREET + 18)
    row = np.floor((Y - STREET) / 6)
    col = np.floor((X + (row % 2) * 10) / 22)
    t = hash2(col, row, 41)
    out[para, :3] = stone[np.where(t < 0.5, 3, np.where(t < 0.85, 2, 4))][para]
    j = para & ((((Y - STREET) % 6) < 1) | (((X + (row % 2) * 10) % 22) < 1.4))
    out[j, :3] = stone[1]
    cop = (Y >= STREET + 14) & (Y < STREET + 18)
    out[cop, :3] = stone[4]
    out[cop & (Y >= STREET + 16.5), :3] = stone[5]
    out[para, 3] = 1.0
    rail = (Y >= STREET + 18) & (Y < STREET + 33)
    post = np.abs(((X + 8) % 16) - 8) < 1.2
    bars = rail & (post | (Y >= STREET + 30) | ((Y >= STREET + 24) & (Y < STREET + 25.5)))
    out[bars, :3] = pal_array(R.IRONC)[2]
    out[bars & (Y >= STREET + 31.5), :3] = pal_array(R.IRONC)[4]
    out[bars, 3] = 1.0
    # the parapet lamps' light on the coping
    for lx in PARAPET_LAMPS:
        warm_light(out[..., :3], np.hypot(X - lx, (Y - STREET - 40) * 1.5), 90, colour="#f6cf7a", strength=0.28)
    return out


def portal_region(X, Y):
    return ((np.abs(X) < HW) & (Y >= TH) & (Y < STREET)) | ((np.abs(X) < 1600) & (Y >= STREET) & (Y < STREET + 33))


def umc_far():
    """The UMC across Broadway at room scale: sandstone wings, lit windows, the red tile roof."""
    cv = Canvas(820, 152)
    umc_facade(cv, 30, 790, 128, 340, 480, 146, seed=5)
    return cv.a


def sky_strip():
    cv = Canvas(640, 100)
    stars = E.night_sky(cv, 0, 0, 640, 100, seed=71, stars=90, horizon=110)
    E.night_clouds(cv, [(40, 30, 140, 10), (420, 22, 160, 9)], seed=7)
    return cv.a, stars


# ---------------------------------------------------------------- build
def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#141223")
    sky, stars = sky_strip()
    v.strip(sky, 0, solid=False)

    # beyond the bridge: the UMC at the top of the east ramp, trees either side of it
    umc = umc_far()
    uh, uw = umc.shape[:2]
    half = uw * ROOM_TO_BATTLE / 2
    v.back(ZU, lambda X, Y: fog(texture_lookup(umc, (X + half) / ROOM_TO_BATTLE, uh - 1 - (Y - TERRACE) / ROOM_TO_BATTLE, wrap=False),
                                np.full(X.shape, ZU), HAZE, 0, 1, 0.3),
           region=lambda X, Y: (Y >= TERRACE) & (np.abs(X) < half))
    for (cell, hgt, X, Z) in [(6, 120, -560.0, 1180.0), (5, 110, 620.0, 1150.0)]:
        v.sprite(sprite_from_cell(cell, height=hgt, colors=32), X, Z, Y=TERRACE, scale=ROOM_TO_BATTLE)
    # the ramp, its walls and lamps, seen through the tunnel
    ramp_layer(v)
    for sx in (-1, 1):
        v.plane((sx * HW, ZT), (sx * HW, RAMP_END + 80), ramp_wall_shader, y_max=STREET)
    for (lx, lz) in sorted(RAMP_LAMPS, key=lambda p: -p[1]):
        spr, ax, ay = lamp_post(60)
        v.sprite(spr.a, lx, lz, Y=float(ramp_y(lz)), anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE * 1.25)
    # the tunnel: walls, the deck's underside, the floor
    for sx in (-1, 1):
        v.plane((sx * HW, ZB), (sx * HW, ZT), tunnel_wall_shader, y_max=TH)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=TH, z_max=ZT)
    v.ground(ground_shader, z_max=ZT)
    # street level on both sides (Hill trees on the left, a pine and a lawn lamp on the right)
    for (cell, hgt, X, Z) in [(5, 120, -420.0, 430.0), (6, 130, -330.0, 700.0), (6, 120, 380.0, 760.0)]:
        v.sprite(sprite_from_cell(cell, height=hgt, colors=32), X, Z, Y=STREET, scale=ROOM_TO_BATTLE)
    lp, ax, ay = lamp_post(60)
    v.sprite(lp.a, 300.0, 420.0, Y=STREET, anchor=(ax / lp.w, ay / lp.h), scale=ROOM_TO_BATTLE * 1.3)
    # the bridge's west face and the lamps on its parapet
    v.back(ZB, portal_shader, region=portal_region)
    for lx in PARAPET_LAMPS:
        spr, ax, ay = lamp_post(60)
        v.sprite(spr.a, lx, ZB - 4, Y=STREET + 18, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE * 0.75)
    # the retaining walls and their railings, near the camera
    length = ZB - Z0
    left = wall_shader(wall_texture(-1, length), False, [l[1] for l in WALL_LIGHTS if l[0] < 0])
    right = wall_shader(wall_texture(1, length), True, [l[1] for l in WALL_LIGHTS if l[0] > 0])
    v.plane((-HW, Z0), (-HW, ZB), left, y_max=STREET)
    v.plane((HW, Z0), (HW, ZB), right, y_max=STREET)
    for sx in (-1, 1):
        v.plane((sx * HW, Z0), (sx * HW, ZB), railing_shader(wall_top), y_max=STREET + 22)
    # Walt's camp against the left wall, far to near
    painters = {"crate": R.crate_radio, "tent": R.dome_tent, "lantern": R.lantern}
    for (kind, X, Z) in sorted(CAMP, key=lambda c: -c[2]):
        spr, ax, ay = painters[kind]()
        v.sprite(spr.a, X, Z, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE)
    v.rows(156, 360, INK, 0.0, 0.62)
    sky_px = ~v.solid_mask()
    stars = [st for st in stars if sky_px[st[1], st[0]]]
    cv = v.reduce(112)

    def pt(X, Y, Z):
        sx, sy = v.project(X, Y, Z)
        return int(round(sx)), int(round(sy))

    # crisp details: BROADWAY in cast letters on the fascia, the wall light fixtures
    label = "BROADWAY"
    lx0, ly0 = pt(0, STREET - 9, ZB)
    tw = text_width(label)
    cv.rect(lx0 - tw // 2 - 3, ly0 - 1, tw + 6, 10, C("#1a1626", 0.55))
    text(cv, label, lx0 - tw // 2, ly0, "#d8c4a4")
    fixtures = []
    for (lx, lz) in WALL_LIGHTS + TUNNEL_LIGHTS:
        x, y = pt(lx * 0.995, 92 if lz < ZB else 82, lz)
        s = 2 if lz < 400 else 1
        # a caged fixture: dark housing, lit glass, cage bars
        cv.rect(x - s - 1, y - s - 2, 2 * s + 3, 2 * s + 4, "#1e1e28")
        cv.rect(x - s, y - s - 1, 2 * s + 1, 2 * s + 2, E.WARM[3]); cv.px(x, y, E.WARM[4])
        if s > 1:
            cv.vline(x - 1, y - s - 1, 2 * s + 2, "#2a2a34"); cv.vline(x + 1, y - s - 1, 2 * s + 2, "#2a2a34")
        fixtures.append([x, y, "fff0c4", s])
    cv.save(os.path.join(out, "battle-far.png"))

    lamp_pts = []
    for lx in PARAPET_LAMPS:
        lamp_pts.append(list(pt(lx, STREET + 18 + LAMP_HEAD * 0.75 * ROOM_TO_BATTLE, ZB - 4)) + ["fff0c4", 2])
    for (lx, lz) in RAMP_LAMPS:
        lamp_pts.append(list(pt(lx, float(ramp_y(lz)) + LAMP_HEAD * 1.25 * ROOM_TO_BATTLE, lz)) + ["fff0c4", 1])
    lx, ly = pt(LANTERN[0], 22, LANTERN[1])
    # cars on Broadway seen through the parapet railing: near lane headlights, far lane taillights
    ya = pt(0, STREET + 26, ZB)[1]       # headlights in the near lane, between the railing posts
    yb = pt(0, STREET + 30, ZB)[1]       # taillights in the far lane, just over them
    flick = fixtures[1]
    return {
        "far": res + "battle-far.png",
        "layers": [
            {"kind": "twinkle", "points": lamp_pts + fixtures, "rate": 1.1, "min": 0.6},
            {"kind": "twinkle", "points": [[lx, ly, "fff0c4", 2]], "rate": 1.6, "min": 0.7},
            {"kind": "twinkle", "points": [[s[0], s[1], "c8c0e0", 1] for s in stars[:8]], "rate": 0.7, "min": 0.3},
            {"kind": "blink", "pattern": "0000000000001010000000000000000011000000", "rate": 9.0,
             "rects": [[flick[0] - 2, flick[1] - 2, 5, 5, "2a2438", 1.0]]},
            {"kind": "movers", "from": [-20, ya], "to": [660, ya], "count": 2, "period": 6.5, "size": [2, 2],
             "pair": 14, "color": "fff0c4", "ease": "out"},
            {"kind": "movers", "from": [660, yb], "to": [-20, yb], "count": 2, "period": 8.0, "size": [2, 2],
             "pair": 12, "color": "ff5a4a", "ease": "out"},
            {"kind": "particles", "style": "dust", "count": 10, "rect": [lx - 60, ly - 60, 120, 70], "speed": [2, -4],
             "color": "ffd890"},
            {"kind": "fauna", "fauna": [{"kind": "umc_moth", "x": lx, "y": ly - 14, "range": 6, "speed": 0.8, "rate": 8.0}]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
