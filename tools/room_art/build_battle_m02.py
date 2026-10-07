"""Battle backdrop for the Macky lobby (M02): down the length of the lobby to the auditorium doors.

The room shows the lobby's back wall flat on; here the camera stands in the middle of the lobby
floor and looks down its length. Rose and buff tiles with oxblood cabochons recede to the great
padded doors under their gilt sunburst, light seeping under them, AUDITORIUM over the arch. Down
the left wall, tall stained-glass windows between sandstone pilasters look out at the night (or,
in the dawn version, at the Flatirons lit pink). Up the right wall the stone stair climbs to the
balcony gallery, its brass-railed balustrade stepping up. Iron lanterns hang from the coffered
ceiling in a row; the oxblood runner leads the eye to the doors. At dawn the sun is behind us: the
front doors throw a long panel of morning light down the runner and onto the far doors.
Layers: the lanterns and sconces breathe, dust turns in the air, a moth circles a lantern."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, shade, mix, text, text_width
from props import OUT, IRON
from lib_norlin import plaster_wall, oak_wainscot, wall_sconce
from lib_macky import (lobby_window, auditorium_doors, gilt_band, hanging_lantern, window_view, DRESS, PLASTER_M,
                       VELVET_M, CARPET_M, TILE_M, TILE_BUFF, INSET_M, BRASS, GILT_M, SHADOW)
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "M02"
INK = "#10121e"
HALL = 420.0          # walls at X = -HALL and +HALL
Z0, Z_FAR = 140.0, 1060.0
CEIL = 250.0
DADO = 62.0           # dado rail height (world)
LANTERNS = [430.0, 650.0, 870.0]
LANTERN_X = 170.0
STAIR = (300.0, 470.0, 860.0, 150.0)    # inner X, start Z, end Z, top height
GALLERY_Z1 = Z_FAR
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


# --- painted textures ---------------------------------------------------------------------------
def pilaster_tex(cv, x, top, base, w=22):
    cv.rect(x, top, w, base - top, DRESS[3]); cv.vline(x, top, base - top, DRESS[5]); cv.vline(x + w - 1, top, base - top, DRESS[1])
    cv.vline(x + 5, top + 12, base - top - 24, DRESS[2]); cv.vline(x + w - 6, top + 12, base - top - 24, DRESS[4])
    cv.rect(x - 3, top, w + 6, 7, DRESS[4]); cv.hline(x - 3, top, w + 6, DRESS[6]); cv.hline(x - 3, top + 6, w + 6, DRESS[1])
    cv.rect(x - 3, base - 10, w + 6, 10, DRESS[3]); cv.hline(x - 3, base - 10, w + 6, DRESS[5])


def side_wall(dawn, windows=True, seed=0):
    """A side wall laid out along its length (u = distance from Z0), CEIL tall, world units:
    plaster, stencilled frieze, oak dado, sandstone pilasters, and either stained-glass windows
    (left) or portraits and sconces (right). Returns (rgba, glow points as (u, Y))."""
    L, Hh = int(Z_FAR - Z0), int(CEIL)
    cv = Canvas(L, Hh, seed=seed)
    plaster_wall(cv, 0, 0, L, Hh, pal=PLASTER_M, seed=seed)
    fy = 20
    cv.rect(0, fy, L, 12, PLASTER_M[5]); cv.hline(0, fy, L, PLASTER_M[2]); cv.hline(0, fy + 11, L, PLASTER_M[2])
    for x in range(4, L, 16):
        cv.poly([(x, fy + 6), (x + 5, fy + 2), (x + 10, fy + 6), (x + 5, fy + 10)], VELVET_M[3]); cv.px(x + 5, fy + 6, GILT_M)
    dado_top = Hh - int(DADO)
    oak_wainscot(cv, 0, dado_top, L, int(DADO), seed=seed, panel=34)
    glows = []
    piers = [160, 370, 580, 790]
    for p in piers:
        pilaster_tex(cv, p - 11, fy + 12, Hh)
    for k in range(len(piers) + 1):
        a = piers[k - 1] if k > 0 else 0
        b = piers[k] if k < len(piers) else L
        mid = (a + b) // 2
        if b - a < 120:
            continue
        if windows:
            lobby_window(cv, mid, 56, 66, 108, dawn=dawn, seed=seed + k)
        else:
            # a framed print and a sconce either side
            pw, ph = 52, 64
            cv.rect(mid - pw // 2 - 4, 62, pw + 8, ph + 8, OUT); cv.rect(mid - pw // 2 - 3, 63, pw + 6, ph + 6, BRASS[2])
            cv.rect(mid - pw // 2, 66, pw, ph, ["#2a3a4a", "#3a2a30", "#2c3a2a"][k % 3])
            cv.rect(mid - pw // 2 + 6, 72, pw - 12, ph - 26, ["#6a7a8a", "#8a5a4a", "#6a7a5a"][k % 3])
            cv.poly([(mid - pw // 2 + 6, 72 + ph - 26), (mid - 4, 92), (mid + 10, 104), (mid + pw // 2 - 6, 72 + ph - 26)], "#3a2c2a")
            cv.hline(mid - 14, 66 + ph - 12, 28, "#c8b896")
        for sx in (a + 26, b - 26):
            if 20 < sx < L - 20:
                wall_sconce(cv, sx, 120)
                glows.append((sx, 112))
    return grade(cv.a, dawn), glows


def far_wall(dawn):
    """The end of the lobby at room scale: plaster, frieze, dado, the auditorium doors under
    AUDITORIUM, sconces and two framed programmes. Bottom row = floor."""
    W_, H_ = int(2 * HALL / ROOM_TO_BATTLE) + 4, int(CEIL / ROOM_TO_BATTLE) + 2
    cv = Canvas(W_, H_, seed=3)
    cx = W_ // 2
    plaster_wall(cv, 0, 0, W_, H_, pal=PLASTER_M, seed=3)
    cv.rect(0, 12, W_, 8, PLASTER_M[5]); cv.hline(0, 12, W_, PLASTER_M[2]); cv.hline(0, 19, W_, PLASTER_M[2])
    for x in range(3, W_, 10):
        cv.poly([(x, 16), (x + 3, 13), (x + 6, 16), (x + 3, 19)], VELVET_M[3]); cv.px(x + 3, 16, GILT_M)
    base = H_ - 1
    oak_wainscot(cv, 0, base - 37, W_, 37, seed=4, panel=26)
    fan = auditorium_doors(cv, cx, base, open_=False, dawn=dawn, seed=5)
    gilt_band(cv, cx, base - 120, "AUDITORIUM", w=96)
    glows = [fan]
    for sx in (cx - 58, cx + 58):
        wall_sconce(cv, sx, base - 68)
        glows.append((sx, base - 76))
    for px_ in (cx - 150, cx + 120):
        cv.rect(px_ - 2, base - 112, 34, 50, OUT); cv.rect(px_ - 1, base - 111, 32, 48, BRASS[2])
        cv.rect(px_, base - 110, 30, 46, "#1a1418"); cv.rect(px_ + 2, base - 108, 26, 10, "#d8b45a")
        for k in range(4):
            cv.hline(px_ + 5, base - 92 + k * 6, 20, "#a89a86" if k else "#e6d6b1")
    for p in (cx - 104, cx + 92):
        cv.rect(p, 20, 12, base - 20, DRESS[3]); cv.vline(p, 20, base - 20, DRESS[5]); cv.vline(p + 11, 20, base - 20, DRESS[1])
    if dawn:
        # the morning comes in through the front doors behind us and lands on the far wall
        for (hw, top, a) in [(46, base - 96, 0.12), (36, base - 86, 0.12)]:
            cv.rect(cx - hw, top, hw * 2, base - top, C("#f8d498", a))
    return grade(cv.a, dawn), glows, (W_, H_)


# --- shaders ------------------------------------------------------------------------------------
def floor_shader(dawn):
    rose, buff = pal_array(TILE_M), pal_array(TILE_BUFF)
    inset = pal_array(INSET_M)
    carpet = pal_array(CARPET_M)
    mul = np.array(DAWN if dawn else NIGHT, np.float32)

    def shader(X, Z):
        size = 36.0
        ci, ri = np.floor(X / size), np.floor(Z / (size * 0.9))
        fx, fz = X / size - ci, Z / (size * 0.9) - ri
        chk = (ci + ri) % 2
        t = hash2(ci, ri, 7)
        tone = np.where(chk[:, None] > 0, rose[2] * (1 - t[:, None]) + rose[3] * t[:, None],
                        buff[2] * (1 - t[:, None]) + buff[3] * t[:, None])
        rgb = tone
        rgb[(fz < 0.06) | (fx < 0.04)] = pal_array(["#3e2826"])[0]
        rgb[(fz > 0.06) & (fz < 0.12)] = rgb[(fz > 0.06) & (fz < 0.12)] * 1.1
        # cabochons where four tiles meet
        dx, dz = np.minimum(fx, 1 - fx), np.minimum(fz, 1 - fz) * 0.9
        cab = (dx + dz) < 0.12
        rgb[cab] = inset[1]
        # the border inlay along both walls
        ax = np.abs(X)
        band = (ax > HALL - 46) & (ax < HALL - 34)
        rgb[band] = pal_array(["#5a2228"])[0]
        rgb[(ax > HALL - 36) & (ax < HALL - 34)] = pal_array(["#c8a070"])[0]
        # the oxblood runner
        run = ax < 52
        rgb[run] = carpet[3]
        rgb[(ax < 44) & (ax > 40)] = carpet[5]
        lz = (Z / 44.0) % 1
        loz = (np.abs(X) / 9 + np.abs(lz - 0.5) * 4.0) < 1.0
        rgb[loz & (ax < 38)] = carpet[4]
        rgb[(ax < 2.2) & (np.abs(lz - 0.5) < 0.05)] = carpet[6]
        rgb[(ax < 38) & (ax > 34)] = carpet[2]
        rgb = rgb * mul
        out = rgba_of(rgb)
        for lz_ in LANTERNS:
            for lx_ in (-LANTERN_X, LANTERN_X):
                warm_light(out[..., :3], np.hypot(X - lx_, (Z - lz_) * 0.7), 150, strength=0.3 if not dawn else 0.14)
        # the doors' fanlight and the seep of light under them, mirrored on the polish
        warm_light(out[..., :3], np.hypot(X * 1.6, (Z - Z_FAR) * 0.5), 120, strength=0.4)
        if dawn:
            panel = (np.abs(X + 10) < 70 + (Z - 300) * 0.02) & (Z < Z_FAR)
            o = out[panel, :3]
            out[panel, :3] = o * 0.62 + (o * 0.4 + np.array(C("#f8d498")[:3]) * 0.6) * 0.38
        fog(out, Z, "#2a1a20" if not dawn else "#5a4044", 700, 1500, amount=0.35)
        return out
    return shader


def ceiling_shader(dawn):
    mul = np.array(DAWN if dawn else NIGHT, np.float32)
    beam = pal_array(["#2c1a1a", "#4a2b24", "#6b3f2e"])
    panel = pal_array(PLASTER_M)

    def shader(X, Z):
        bx = (X + HALL) / 140.0 % 1
        bz = (Z - Z0) / 140.0 % 1
        rgb = np.repeat(panel[3][None], X.shape[0], 0)
        inner = (bx > 0.14) & (bx < 0.86) & (bz > 0.14) & (bz < 0.86)
        rgb[inner] = panel[4]
        deep = (bx > 0.22) & (bx < 0.78) & (bz > 0.22) & (bz < 0.78)
        rgb[deep] = panel[2]
        rgb[(np.abs(bx - 0.5) < 0.05) & (np.abs(bz - 0.5) < 0.05)] = pal_array([GILT_M])[0]
        b = (bx < 0.08) | (bx > 0.92) | (bz < 0.08) | (bz > 0.92)
        rgb[b] = beam[1]
        rgb[(bx < 0.02) | (bz < 0.02)] = beam[2]
        rgb = rgb * mul * 0.85
        out = rgba_of(rgb)
        for lz_ in LANTERNS:
            for lx_ in (-LANTERN_X, LANTERN_X):
                warm_light(out[..., :3], np.hypot(X - lx_, (Z - lz_) * 0.8), 110, strength=0.32 if not dawn else 0.12)
        fog(out, Z, "#2a1a20" if not dawn else "#5a4044", 700, 1500, amount=0.4)
        return out
    return shader


def wall_shader(tex, lights=(), dawn=False):
    """A side wall from its painted texture, warmed round its sconces and under the lanterns."""
    th, tw = tex.shape[:2]

    def shader(u, Y, Z):
        out = texture_lookup(tex, u, th - 1 - Y)
        out[..., 3] = 1
        for (su, row) in lights:
            warm_light(out[..., :3], np.hypot(u - su, (Y - (CEIL - row)) * 1.3), 70, strength=0.32)
        for lz in LANTERNS:
            warm_light(out[..., :3], np.hypot(Z - lz, (Y - 140) * 0.8), 160, strength=0.16 if not dawn else 0.08)
        fog(out, Z, "#2a1a20" if not dawn else "#5a4044", 800, 1500, amount=0.3)
        return out
    return shader


# --- the stair and gallery (crisp, after the reduce) -------------------------------------------
def stair_and_gallery(cv, v, dawn):
    """The stone stair up the right wall and the gallery it reaches, as projected polygons."""
    mul = np.array(DAWN if dawn else NIGHT, np.float32)

    def g(c):
        rgb = np.array(C(c)[:3], np.float32) * mul
        return tuple(rgb) + (1.0,)

    def P(X, Y, Z):
        return v.project(X, Y, Z)

    x_in, z0, z1, top = STAIR
    n = 20
    run, rise = (z1 - z0) / n, top / n
    # gallery fascia and floor edge (far end), drawn first
    gy = top
    cv.poly([P(x_in, gy - 14, z1), P(x_in, gy - 14, GALLERY_Z1), P(x_in, gy, GALLERY_Z1), P(x_in, gy, z1)], g(DRESS[2]))
    cv.poly([P(x_in, gy - 3, z1), P(x_in, gy - 3, GALLERY_Z1), P(x_in, gy, GALLERY_Z1), P(x_in, gy, z1)], g(DRESS[4]))
    # balustrade along the gallery
    for zz in np.arange(z1 + 8, GALLERY_Z1, 22):
        a, b = P(x_in, gy, zz), P(x_in, gy + 34, zz)
        cv.line(int(a[0]), int(a[1]), int(b[0]), int(b[1]), g(DRESS[3]))
    cv.poly([P(x_in, gy + 32, z1), P(x_in, gy + 32, GALLERY_Z1), P(x_in, gy + 36, GALLERY_Z1), P(x_in, gy + 36, z1)], g(BRASS[2]))
    # the flight, far steps first: tread, riser, and the side face toward the hall
    for k in range(n - 1, -1, -1):
        za, zb = z0 + k * run, z0 + (k + 1) * run
        y0, y1 = k * rise, (k + 1) * rise
        side = [P(x_in, 0, za), P(x_in, 0, zb), P(x_in, y1, zb), P(x_in, y1, za)]
        cv.poly(side, g(DRESS[2]))
        # a sloping oak string along the top of the side face
        cv.poly([P(x_in, y0 - 6, za), P(x_in, y1 - 6, zb), P(x_in, y1 - 1, zb), P(x_in, y0 - 1, za)], g("#6b3f2e"))
        if y1 < v.cam:
            cv.poly([P(x_in, y1, za), P(HALL, y1, za), P(HALL, y1, zb), P(x_in, y1, zb)], g(DRESS[4]))
        cv.poly([P(x_in, y0, za), P(HALL, y0, za), P(HALL, y1, za), P(x_in, y1, za)], g(DRESS[3]))
        # the plum runner up the middle of the flight
        mx = (x_in + HALL) / 2
        cv.poly([P(mx - 26, y0, za), P(mx + 26, y0, za), P(mx + 26, y1, za), P(mx - 26, y1, za)], g(CARPET_M[3]))
        cv.line(*[int(c) for c in P(x_in, y1, za)], *[int(c) for c in P(x_in, y1, zb)], g(DRESS[5]))
    # balusters and the brass handrail along the open side of the flight
    for k in range(0, n, 2):
        za = z0 + (k + 0.5) * run
        yb = (k + 1) * rise
        a, b = P(x_in + 6, yb, za), P(x_in + 6, yb + 34, za)
        cv.line(int(a[0]), int(a[1]), int(b[0]), int(b[1]), g(DRESS[4]))
    a, b = P(x_in + 6, 34 + rise, z0), P(x_in + 6, top + 34, z1)
    for d in (0, 1):
        cv.line(int(a[0]), int(a[1]) + d, int(b[0]), int(b[1]) + d, g(BRASS[3] if d == 0 else BRASS[1]))
    # the newel post at the foot
    a, b = P(x_in + 6, 0, z0), P(x_in + 6, 46, z0)
    cv.rect(int(a[0]) - 3, int(b[1]), 7, int(a[1] - b[1]), g(DRESS[3]))
    cv.rect(int(a[0]) - 4, int(b[1]) - 3, 9, 4, g(BRASS[3]))
    cv.ellipse(int(a[0]) - 3, int(b[1]) - 8, 7, 6, "#f6cf7a")
    return [(int(a[0]), int(b[1]) - 5)]


def render(dawn):
    v = View(horizon=98, cam=52, fill="#141223")
    v.ground(ceiling_shader(dawn), height=CEIL, y_from=0, y_to=v.h0)
    v.ground(floor_shader(dawn))
    left, lglow = side_wall(dawn, windows=True, seed=11)
    right, rglow = side_wall(dawn, windows=False, seed=12)
    v.plane((-HALL, Z0), (-HALL, Z_FAR), wall_shader(left, lglow, dawn), y_max=CEIL)
    v.plane((HALL, Z0), (HALL, Z_FAR), wall_shader(right, rglow, dawn), y_max=CEIL)
    glows = []
    for (u, y) in lglow:
        sx, sy = v.project(-HALL, CEIL - y, Z0 + u)
        glows.append([int(round(sx)), int(round(sy)), "fff0c4", 1])
    for (u, y) in rglow:
        sx, sy = v.project(HALL, CEIL - y, Z0 + u)
        glows.append([int(round(sx)), int(round(sy)), "fff0c4", 1])
    fw, fglow, (fw_w, fw_h) = far_wall(dawn)
    sx, sy, sc = v.sprite(fw, 0, Z_FAR, anchor=(0.5, 1.0), scale=ROOM_TO_BATTLE)
    k = sc * ROOM_TO_BATTLE
    for (gx, gy) in fglow:
        glows.append([int(round(sx + (gx - fw_w / 2) * k)), int(round(sy + (gy - fw_h) * k)), "f6cf7a", 1])
    # the lanterns hanging down the middle, far first
    lc = Canvas(24, 70)
    hanging_lantern(lc, 12, 68, chain_top=0)
    lantern = grade(lc.a, dawn)
    for lz in sorted(LANTERNS, reverse=True):
        for lx in (-LANTERN_X, LANTERN_X):
            sx, sy, sc = v.sprite(lantern, lx, lz, Y=CEIL - 112.0, anchor=(0.5, 1.0), scale=ROOM_TO_BATTLE)
            k = sc * ROOM_TO_BATTLE
            glows.append([int(round(sx)), int(round(sy - 15 * k)), "fff0c4", 2 if lz < 700 else 1])
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    glows += [[x, y, "f6cf7a", 1] for (x, y) in stair_and_gallery(cv, v, dawn)]
    return v, cv, glows


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    v, cv, glows = render(False)
    cv.save(os.path.join(out, "battle-far.png"))
    vd, cvd, _ = render(True)
    cvd.save(os.path.join(out, "battle-far-dawn.png"))
    res = f"res://assets/art/rooms/{ROOM}/"
    lantern_pts = [g for g in glows if g[3] == 2 or g[2] == "fff0c4"]
    return {
        "far": res + "battle-far.png",
        "far_dawn": res + "battle-far-dawn.png",
        "layers": [
            {"kind": "twinkle", "points": glows, "rate": 1.2, "min": 0.55},
            {"kind": "particles", "style": "dust", "count": 18, "rect": [180, 30, 280, 130], "speed": [0, 3], "color": "f8e0b0"},
            {"kind": "fauna", "fauna": [{"kind": "lamp_moth", "x": 320, "y": 40, "range": 8, "speed": 1.5, "rate": 9.0}]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
