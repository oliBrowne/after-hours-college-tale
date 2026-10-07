"""Battle backdrop for the tennis courts (G02): the friendly set.

A low view from our baseline straight down Court 3: the fighters stand on the near baseline, the
lines run away to the net and the far baseline and converge on the horizon. Beyond the back
fence (backlit windscreen glowing green-gold, COURT 3 on it, the chain-link above) the autumn
trees stand dark with gold rims, the CU hall's red roof catches the light on the right, and the
Flatirons sit in silhouette against a low golden sun just above their shoulder. Everything throws
its shadow straight at us: the windscreen's band across the far run-off, the net's long mesh
shadow over the near service boxes, and the two light towers' thin shadows running the full
length of the surrounds. The ball machine waits at the far baseline, its LED blinking; a ball
arcs out of it over the net and bounces toward us. Pollen and leaves drift in the sun, a few
birds cross, rays turn slowly out of the sun. Painted at golden hour (the game reaches G02 after
dawn_started), so far and far_dawn are the same image."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from midlib import sprite_from_cell
from pixel import Canvas, C, mix, shade, text, text_width
from persp import View, hash2, fog, pal_array, rgba_of
from lib_macky2 import backlit, _ridge, AUTUMN
import lib_tennis as T

ROOM = "G02"
INK = "#10121e"
SUN = (300, 60)                  # the sun on screen, just over the Flatirons' shoulder
Z_BASE0, Z_NET, Z_BASE1 = 120.0, 595.0, 1070.0     # near baseline (under the menus), net, far baseline
Z_SERV0, Z_SERV1 = 339.0, 851.0                     # the fighters stand on our service line
Z_FENCE = 1326.0
DOUBLES, SINGLES = 219.0, 165.0                     # half widths (40 units = 1 m)
NET_HALF, NET_H = 255.0, 36.0
WS_H, FENCE_H = 72.0, 144.0                         # windscreen and fence height
POST_EVERY = 120.0
TOWERS = [(-470.0, 1340.0), (470.0, 1340.0)]
TOWER_H = 440.0
MACHINE = (120.0, 1100.0)
# shadows run toward the viewer: a point h above (X, Z) shades (X + SX*h, Z + SZ*h)
SX, SZ = 0.25, -4.0
HAZE = "#e8c8a4"
LINE = "#efe6cc"


def tower_x(X, Z):
    return 320 + X * 320.0 / Z


def shade_masks(X, Z):
    """(full, half) shadow masks on the ground for world points X, Z."""
    full = np.zeros(X.shape, bool)
    half = np.zeros(X.shape, bool)
    # back fence: windscreen solid, the chain-link above it a lighter shade, posts solid
    h = (Z_FENCE - Z) / -SZ
    X0 = X - SX * h
    ok = Z < Z_FENCE
    full |= ok & (h <= WS_H)
    half |= ok & (h > WS_H) & (h <= FENCE_H)
    full |= ok & (h <= FENCE_H + 2) & (np.abs(((X0 + POST_EVERY / 2) % POST_EVERY) - POST_EVERY / 2) < 2.0)
    # sun through the wind flaps and between two windscreen panels
    vent = (np.abs(((X0 + 30) % 180) - 90) < 4) & (np.abs(h - 46) < 3)
    gap = np.abs(X0 - 242) < 1.6
    full &= ~(ok & (vent | gap) & (h <= WS_H))
    # the net: mesh as half shade, tape and posts solid, the centre strap
    h = (Z_NET - Z) / -SZ
    X0 = X - SX * h
    ok = (Z < Z_NET) & (h >= 0)
    top = NET_H + 6 * (np.abs(X0) / NET_HALF) ** 1.6
    half |= ok & (np.abs(X0) < NET_HALF) & (h < top - 2)
    full |= ok & (np.abs(X0) < NET_HALF) & (np.abs(h - top + 1) <= 1.2)
    full |= ok & (np.abs(np.abs(X0) - NET_HALF - 3) < 2.5) & (h < NET_H + 8)
    full |= ok & (np.abs(X0) < 1.5) & (h < NET_H - 2)
    # light towers: thin poles and the bank of floods at the top
    for (tx, tz) in TOWERS:
        h = (tz - Z) / -SZ
        X0 = X - SX * h
        ok = (Z < tz) & (h <= TOWER_H)
        full |= ok & (np.abs(X0 - tx) < 3.0 + h * 0.004)
        full |= (Z < tz) & (h > TOWER_H - 16) & (h <= TOWER_H + 6) & (np.abs(X0 - tx) < 28)
    # the ball machine at the far baseline
    mx, mz = MACHINE
    h = (mz - Z) / -SZ
    X0 = X - SX * h
    full |= (Z < mz) & (h <= 40) & (np.abs(X0 - mx) < 16 - h * 0.1)
    return full, half


def ground_shader(X, Z):
    n = X.shape[0]
    full, half = shade_masks(X, Z)
    ax = np.abs(X)
    court = (ax < DOUBLES) & (Z > Z_BASE0 - 2) & (Z < Z_BASE1 + 2)
    # squeegee passes: long bands across the court, one tone apart
    band = (hash2(np.floor(Z / 26.0), np.floor((X + 3000) / 340.0), 4) > 0.55).astype(int)
    # wear behind the baselines and at the T
    worn = (((X / 150.0) ** 2 + ((Z - Z_BASE0 + 10) / 40.0) ** 2) < 1) | (((X / 150.0) ** 2 + ((Z - Z_BASE1 - 20) / 60.0) ** 2) < 1)
    worn |= ((X / 50.0) ** 2 + ((Z - Z_SERV0) / 30.0) ** 2) < 1
    k = 3 + band + worn
    # the low sun's glare on the acrylic: a stepped wedge running out toward the sun
    xs_sun = (SUN[0] - 320) / 320.0 * Z
    g = np.abs(X - xs_sun) / (Z * 0.12 + 30)
    glare = np.clip((1 - g) * 3, 0, 3).astype(int) * (Z > 420)
    k = np.clip(k + (glare > 0), 0, 6)
    sun_c, sun_s = T.P(T.COURT_SUN), T.P(T.SURR_SUN)
    sh_c, sh_s = T.P(T.COURT_SHADE), T.P(T.SURR_SHADE)
    lit = np.where(court[:, None], sun_c[k], sun_s[k])
    dark = np.where(court[:, None], sh_c[np.clip(3 + band + worn, 0, 6)], sh_s[np.clip(3 + band + worn, 0, 6)])
    gold = np.array(C("#f0cc88")[:3])
    a = (glare * 0.11)[:, None]
    lit = lit * (1 - a) + gold * a
    rgb = np.where(full[:, None], dark, np.where(half[:, None], lit * 0.45 + dark * 0.55, lit))
    # lines: baselines 4 units, the rest 2, centre marks
    lines = np.zeros(n, bool)
    for zl, wl in ((Z_BASE0, 4.0), (Z_BASE1, 4.0), (Z_SERV0, 2.0), (Z_SERV1, 2.0)):
        span = DOUBLES if wl > 3 else SINGLES
        lines |= (np.abs(Z - zl) < wl / 2 + 0.6) & (ax < span + 1)
    for xl in (DOUBLES, SINGLES):
        lines |= (np.abs(ax - xl) < 1.2) & (Z > Z_BASE0 - 2) & (Z < Z_BASE1 + 2)
    lines |= (ax < 1.2) & (Z > Z_SERV0) & (Z < Z_SERV1)
    lines |= (ax < 1.2) & ((np.abs(Z - Z_BASE0) < 14) | (np.abs(Z - Z_BASE1) < 14))
    lc = np.array(C(LINE)[:3]) * np.where(full[:, None], 0.62, np.where(half[:, None], 0.8, 1.0))
    rgb = np.where(lines[:, None], lc[None, :] if lc.ndim == 1 else lc, rgb)
    # leaves along the fence foot and in the side run-offs
    cell = hash2(np.floor(X / 5), np.floor(Z / 5), 21)
    drift = np.clip(1 - (Z_FENCE - Z) / 160, 0, 1) * 0.5 + np.clip((ax - DOUBLES - 40) / 300, 0, 1) * 0.18
    leaf = cell < drift * 0.35
    pick = (hash2(np.floor(X / 5), np.floor(Z / 5), 22) * 4).astype(int)
    lp = T.P(["#c05a2c", "#e08a3c", "#a84a30", "#e0b844"])
    lrgb = lp[np.clip(pick, 0, 3)] * np.where(full[:, None], 0.6, 1.0)
    rgb[leaf] = lrgb[leaf]
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 1500, 4000, amount=0.55)
    return out


def sky(v):
    """Golden late-afternoon sky in stepped bands, brightest round the sun; gold-lit cloud bars."""
    cv = Canvas(640, 112)
    T.golden_sky(cv, 0, 0, 640, 112, SUN, seed=9, reach=300.0)
    rng = T._rng(4)
    for (x, y, ln, th) in [(40, 30, 110, 3), (180, 46, 70, 2), (360, 40, 120, 3), (500, 26, 90, 2), (430, 70, 80, 2)]:
        T.gold_cloud(cv, x, y, ln, th, rng)
    T.sun_disc(cv, *SUN, r=10)
    v.strip(cv.a, 0, solid=False)


def mountains(v):
    """The Flatirons in silhouette with the sun just past them: cool violet body, every crest
    rimmed gold, warm haze in the valley; far hills either side."""
    rng = T._rng(7)
    cv = Canvas(640, 112)
    xs, far = _ridge(0, 639, [(0, 74), (0.35, 70), (0.55, 76), (0.7, 64), (0.85, 70), (1.0, 66)], rng, 0.6)
    T.far_hills(cv, 0, far, 112, pal=["#9a7c8a", "#a8868c", "#b8928e", "#c89e90", "#d8ac92", "#e8c09a"], seed=3)
    mtn, ridge = T.golden_flatirons(scale=2.0)
    lit = backlit(mtn, body=(0.5, 0.42, 0.52), lift=(0.06, 0.04, 0.07), rim="#ffd890", rim2="#f6b46a",
                  haze="#c89aa0", haze_amt=0.18)
    cv.paste(lit, 8, 22)
    # the valley haze at their feet (three flat steps)
    for k, (y0, a) in enumerate([(84, 0.12), (90, 0.12), (95, 0.14)]):
        m = np.zeros((112, 640), bool)
        for x in range(640):
            m[y0 + int(2 * np.sin(x / (15 + 4 * k) + k)):, x] = True
        cv.fill_mask(m & (cv.a[..., 3] > 0), C("#f0c8a0", a))
    v.strip(cv.a, 0)


def far_campus(v):
    """The CU hall on the right (its red roof and the west wall catching the sun), backlit autumn
    crowns along the fence, two big oaks at the edges."""
    cv = Canvas(640, 112)
    T.campus_hall(cv, 470, 660, 80, 112, seed=21, pavilion=(560, 36, 8))
    cv.vline(574, 54, 18, "#c8ccd0")
    rng = T._rng(12)
    dark_aut = [["#2a1a1c", "#3e2422", "#5a3226", "#a85a30", "#f0b860"], ["#2a2218", "#3e3220", "#5a4626", "#b08a34", "#f6d070"],
                ["#22201c", "#2e2a22", "#3e3a28", "#7a6a38", "#d8b860"]]
    x = -10
    while x < 650:
        if not (250 < x < 360):
            r, hh = int(rng.integers(10, 18)), int(rng.integers(16, 28))
            T.tree_crown(cv, x, 102 - hh // 2, r, hh, dark_aut[int(rng.integers(3))], rng, lit_side=-1)
        x += int(rng.integers(12, 22))
    # gold rims on the crowns' top edges (the sun is behind them)
    m = cv.a[..., 3] > 0.5
    up = m & ~np.roll(m, 1, axis=0)
    up[:60] &= False
    v.strip(cv.a, 0)
    for (X, Z, hh) in [(-2200.0, 2100.0, 300.0), (1900.0, 2200.0, 320.0)]:
        h = int(round(hh * v.scale(Z) * 1.6))
        spr = sprite_from_cell(5, height=h, colors=36)
        spr = backlit(spr, body=(0.42, 0.34, 0.4), rim="#ffcc70", rim2="#f09040", fringe=0.5)
        v.sprite(spr, X, Z, scale=Z / v.F)


def fence_shader(X, Y):
    """The back fence seen from the court, against the sun: the windscreen glows (light through
    the knit, tree shadows across it), vents bright, black posts and rails, the chain-link above
    a light dark lattice over the view."""
    n = X.shape[0]
    out = np.zeros((n, 4), np.float32)
    ws = Y <= WS_H
    blob = (np.sin(X / 53.0) + np.sin(X / 31.0 + Y / 17.0 + 1.3) * 0.8 + np.sin(X / 89.0 - Y / 23.0 + 2.1) * 0.7
            + np.clip(1 - np.abs(X - (SUN[0] - 320) * Z_FENCE / 320) / 500, 0, 1) * 1.6)
    k = np.clip(np.floor(blob * 0.9 + 2).astype(int), 0, 4)
    pal = T.P(["#1e342c", "#2c4a3a", "#3e5e44", "#5a744c", "#7a8a54"])
    out[ws, :3] = pal[k[ws]]
    out[ws & ((np.floor(Y) % 4) == 0), :3] *= 0.9
    vent = ws & (np.abs(((X + 30) % 180) - 90) < 4) & (np.abs(Y - 46) < 3)
    out[vent, :3] = np.array(C("#f6dc90")[:3])
    gap = ws & (np.abs(X - 242) < 1.6)
    out[gap, :3] = np.array(C("#f8e4a0")[:3])
    out[ws, 3] = 1
    hem = (np.abs(Y - WS_H) < 2.5) | (Y < 3)
    out[hem & ws, :3] = pal[0]
    mesh = (Y > WS_H) & (Y <= FENCE_H)
    lat = ((np.floor((X + Y) / 6) % 2) == 0)
    out[mesh, :3] = np.array(C("#1a1c22")[:3])
    out[mesh, 3] = np.where(lat[mesh], 0.38, 0.24)
    rail = (np.abs(Y - FENCE_H) < 2.5) | (np.abs(Y - WS_H - 1) < 1.5)
    post = np.abs(((X + POST_EVERY / 2) % POST_EVERY) - POST_EVERY / 2) < 2.2
    out[(rail | post) & (Y <= FENCE_H + 3), :3] = np.array(C("#14161a")[:3])
    out[(rail | post) & (Y <= FENCE_H + 3), 3] = 1
    rimc = post & (np.abs(((X + POST_EVERY / 2) % POST_EVERY) - POST_EVERY / 2 + 2.0) < 0.8)
    out[rimc & (Y <= FENCE_H), :3] = np.array(C("#d8a860")[:3])
    fog(out, np.full(n, Z_FENCE), HAZE, 1500, 4000, amount=0.4)
    return out


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52)
    sky(v)
    mountains(v)
    v.ground(ground_shader)
    far_campus(v)
    v.back(Z_FENCE, fence_shader, region=lambda X, Y: (Y >= 0) & (Y <= FENCE_H + 3))
    # the ball machine waiting at the far baseline (its room sprite, scaled to battle size)
    mach, ax, ay = T.ball_machine(34, 40)
    mx, mz = MACHINE
    msx, msy, ms = v.sprite(mach.a, mx, mz, anchor=(ax / mach.w, ay / mach.h), scale=1.38)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp 1:1 details: the net, the light towers, the sign on the windscreen, balls, leaves
    s = 320.0 / Z_NET
    gy = int(round(98 + 52 * s))
    xl, xr = int(round(320 - NET_HALF * s)), int(round(320 + NET_HALF * s))
    for x in range(xl, xr + 1):
        t = abs(x - 320) / (xr - 320)
        ty = int(round(gy - (NET_H + 6 * t ** 1.6) * s))
        for y in range(ty + 1, gy):
            if (x % 2 == 0) or ((y - ty) % 2 == 0):
                cv.px(x, y, C("#121418", 0.55))
        cv.px(x, ty, "#fff4dc"); cv.px(x, ty + 1, C("#c8c0a8", 0.8))
    cv.vline(320, int(round(gy - NET_H * s)) + 1, int(round(NET_H * s)) - 1, "#efe6cc")
    for px_ in (xl - 1, xr + 1):
        top = int(round(gy - (NET_H + 8) * s))
        cv.rect(px_ - 1, top, 2, gy - top + 1, "#1c3a2c"); cv.px(px_ - 1 if px_ > 320 else px_, top, "#f0c070")
    # light towers at the far corners (dark against the glow, gold on the sun side)
    for (tx, tz) in TOWERS:
        s_ = 320.0 / tz
        x = int(round(320 + tx * s_)); base = int(round(98 + 52 * s_)); top = int(round(base - TOWER_H * s_))
        cv.rect(x - 1, top + 4, 2, base - top - 4, "#2a2832"); cv.vline(x - 1 if tx > 0 else x, top + 4, base - top - 4, "#c89058")
        cv.rect(x - 7, top + 2, 15, 2, "#2a2832"); cv.hline(x - 7, top + 2, 15, "#e8b060")
        for k in range(3):
            cv.rect(x - 7 + k * 5, top - 2, 4, 4, "#1e1c26"); cv.hline(x - 7 + k * 5, top - 2, 4, "#f0c070")
    # the court number on the far windscreen
    s_ = 320.0 / Z_FENCE
    sy = int(round(98 + (52 - 52) * s_))
    px_, py_ = 296, sy - 6
    cv.rect(px_ - 1, py_ - 1, 11, 13, T.OUT); cv.rect(px_, py_, 9, 11, T.BLUE_SIGN[2]); cv.hline(px_, py_, 9, T.BLUE_SIGN[3])
    text(cv, "3", px_ + 2, py_ + 2, "#f4f0e4")
    cv.px(px_ + 1, py_ - 2, "#f2f0e8"); cv.px(px_ + 7, py_ - 2, "#f2f0e8")
    # a few balls and leaves lying on the near court (1:1, they would block up in world space)
    rng = T._rng(33)
    for (x, y) in [(150, 156), (171, 158), (402, 153), (596, 162), (40, 170), (282, 141), (348, 133)]:
        T.tennis_ball(cv, x, y, shadow=False)
        cv.hline(x, y + 2, 4, C("#0e1a20", 0.3))
    for _ in range(140):
        lx, ly = int(rng.integers(0, 640)), int(rng.integers(150, 360))
        dim = 1 - min(0.6, max(0.0, (ly - 156) / 204 * 0.62))
        c = ["#c05a2c", "#e08a3c", "#a84a30", "#e0b844"][int(rng.integers(4))]
        col = tuple(np.array(C(c)[:3]) * dim)
        cv.px(lx, ly, col); cv.px(lx + 1, ly, tuple(np.array(col) * 0.8))

    solid = v.solid_mask()
    for (tx, tz) in TOWERS:                         # towers were painted after reduce: mark them solid
        s_ = 320.0 / tz
        x = int(round(320 + tx * s_)); base = int(round(98 + 52 * s_)); top = int(round(base - TOWER_H * s_))
        solid[top - 2:base, x - 7:x + 8] = True
    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = solid.astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))

    # layers: the arcing ball (one blink layer per frame), the machine's LED, rays, pollen, leaves
    layers = [
        # a lob out of the machine, over the net, coming at us (grows as it nears)
        {"kind": "movers", "from": [int(msx) - 2, int(msy) - 16], "to": [290, 178], "count": 1, "period": 3.6,
         "size": [1, 5], "color": "d8ec4a", "ease": "in"},
    ]
    led = (int(round(msx + (24 - ax) * ms)), int(round(msy + (25 - ay) * ms)))
    layers.append({"kind": "blink", "pattern": "1100", "rate": 2.0, "rects": [[led[0], led[1], 1, 1, "3cfa6a", 1.0]]})
    sx, sy = SUN
    rays = []
    for i, (ang, w, ln, a) in enumerate([(100, 60, 260, 0.06), (78, 54, 260, 0.06), (122, 46, 240, 0.05), (56, 44, 240, 0.04)]):
        rays.append({"kind": "beam", "x": sx, "y": sy, "angle": ang, "sweep": 2.5, "period": 12 + i * 2, "phase": i * 1.4,
                     "length": ln, "width": w, "color": "ffe8b8", "alpha": a, "floor": 400})
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "far_dawn": res + "battle-far.png",
        "near_dawn": res + "battle-near.png",
        "layers": [
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "bird", "x": 80, "y": 34, "fly": 9.0, "rate": 4.0},
                {"kind": "bird", "x": 92, "y": 28, "fly": 9.0, "rate": 3.6},
                {"kind": "bird", "x": 230, "y": 20, "fly": 7.0, "rate": 3.2}]},
        ] + rays + layers + [
            {"kind": "particles", "style": "dust", "count": 28, "rect": [170, 40, 300, 120], "speed": [2, 4], "color": "ffe6a8"},
            {"kind": "particles", "style": "leaf", "count": 12, "rect": [-20, -10, 680, 175], "speed": [-26, 14]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
