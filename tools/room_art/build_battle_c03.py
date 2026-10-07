"""Battle backdrop for the Career Center (C03): the career fair itself, set up in the UMC ballroom
next door, the fight happening in the centre aisle between the booths.

Pipe-and-drape booths run back on both sides in navy drape, each with a company header and its
roll-up banner (all fictional recruiters: PEAKLINE, MESA BANK, ALPENGLOW, CHINOOK, FLATIRON, TALUS,
KESTREL, BOULDERLY), a draped table in the company colour with swag on top. Above the drapes the
ballroom's plaster walls with tall night windows and sconces; a coffered ceiling with two
chandeliers and black-and-gold CU pennants. The far end: a low stage with a podium, the CAREER FAIR
banner and a big screen running the LinkedOut feed. Navy ballroom carpet with a gold motif.
Layers: the big screen cycling its slides, the chandeliers and the booth tablets twinkling, dust."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON, AMBER
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_eng import micro_text, micro_width
import c02_lib as S
import c03_lib as L

ROOM = "C03"
INK = "#10121e"
F = 320.0
DRAPE_X = 300.0                   # booth back drapes
TABLE_X = 238.0                   # table fronts facing the aisle
TABLE_D = 30.0                    # table depth
TABLE_H = 30.0
WALL_X = 380.0                    # ballroom walls
Z0, Z_BACK = 200.0, 720.0
BOOTH = 92.0
DRAPE_H = 96.0
CEIL = 230.0
FOG = "#221e30"
COMPANIES = [("PEAKLINE", L.PEAK), ("MESA BANK", ["#3a1a14", "#6a2a1e", "#a8442c", "#d06a44", "#f0a070"]),
             ("ALPENGLOW", ["#3a1430", "#6a2454", "#a8407a", "#d870a0", "#f4b0cc"]),
             ("CHINOOK", ["#2a2a10", "#4a4a1a", "#7a7a2a", "#a8a840", "#d8d870"]),
             ("FLATIRON", [L.NAVY[1], L.NAVY[2], L.NAVY[4], "#8ac0f4", "#c8d8f0"]),
             ("TALUS", ["#1a2a14", "#2a4a20", "#3e6e2e", "#5e9a44", "#9ac87a"]),
             ("KESTREL", ["#2a1a0a", "#5a3a14", "#a86a24", "#e0a040", "#f6d08a"]),
             ("BOULDERLY", [S.BLACK[1], S.BLACK[3], S.GOLD[2], S.GOLD[3], S.GOLD[5]])]
N_BOOTH = int((Z_BACK - 60 - Z0) // BOOTH)
FW = int(round(2 * WALL_X * F / Z_BACK))
FH = int(round(CEIL * F / Z_BACK))


def floor_shader(X, Z):
    """Navy ballroom carpet with a gold lattice motif, warm under the chandeliers and the stage."""
    p = pal_array(L.NAVY)
    g = pal_array(S.GOLD)
    cell = 34.0
    u, w_ = np.mod(X, cell) / cell - 0.5, np.mod(Z, cell) / cell - 0.5
    d = np.abs(u) + np.abs(w_)
    rgb = np.repeat(p[2][None, :], X.shape[0], 0)
    rgb = np.where(((d > 0.44) & (d < 0.5))[:, None], p[4], rgb)
    rgb = np.where((d < 0.08)[:, None], g[2] * 0.85, rgb)
    rgb = np.where(((np.abs(u) < 0.02) | (np.abs(w_) < 0.02))[:, None] & (d < 0.2)[:, None], p[3], rgb)
    rgb = rgb * (0.96 + 0.06 * hash2(np.floor(X / 2), np.floor(Z / 3), 2))[:, None]
    for z in (380.0, 560.0):
        warm_light(rgb, np.hypot(X * 0.8, (Z - z) * 1.0), 150, colour="#f6cf7a", strength=0.22)
    warm_light(rgb, np.hypot(X * 0.6, (Z - Z_BACK) * 1.4), 200, colour="#8ac0f4", strength=0.12)
    out = rgba_of(np.clip(rgb, 0, 1))
    fog(out, Z, FOG, 420, 800, amount=0.35)
    return out


def ceiling_shader(X, Z):
    """Coffered ballroom ceiling: deep plaster coffers with lit cove edges, recessed cans."""
    pl = pal_array(["#2a2434", "#3a3244", "#4a4054", "#5e5266", "#e8c890"])
    c = 60.0
    fx, fz = np.mod(X + 30, c) / c, np.mod(Z, c) / c
    beam = (fx < 0.12) | (fz < 0.12)
    rgb = np.where(beam[:, None], pl[3], pl[1])
    rgb = np.where(((fx > 0.12) & (fx < 0.16) | (fz > 0.12) & (fz < 0.16))[:, None], pl[4] * 0.8, rgb)
    can = np.hypot(np.mod(X + 30, c) - 36, np.mod(Z, c) - 36) < 3
    rgb = np.where(can[:, None], pal_array(["#fff0c4"])[0], rgb)
    out = rgba_of(rgb)
    out[..., :3] *= 0.85
    fog(out, Z, FOG, 420, 800, amount=0.4)
    out[(Z > Z_BACK) | (np.abs(X) > WALL_X), 3] = 0
    return out


def wall_tex():
    """The ballroom side wall above the booths: warm plaster, tall round-headed night windows with
    drapes, brass sconces between them."""
    Lw, Hh = int(Z_BACK - Z0), int(CEIL)
    cv = Canvas(Lw, Hh, seed=70)
    S.store_wall(cv, 0, 0, Lw, Hh, seed=71, pal=["#3a2c30", "#54403e", "#6a524c", "#7a605a", "#886c64", "#98786e", "#a88878"])
    for k, u in enumerate(range(40, Lw - 40, 110)):
        wx, wy, ww, wh = u, 40, 44, 110
        cv.rect(wx - 3, wy - 3, ww + 6, wh + 3, "#c8b8a0")
        cv.ellipse(wx - 3, wy - 25, ww + 6, 48, "#c8b8a0")
        cv.rect(wx, wy, ww, wh, "#141a34")
        cv.ellipse(wx, wy - 22, ww, 44, "#141a34")
        for yy in range(wy - 18, wy + wh, 16):
            cv.hline(wx, yy, ww, "#2a3458")
        cv.vline(wx + ww // 2, wy - 22, wh + 22, "#2a3458")
        rng = np.random.default_rng(k)
        for _ in range(16):
            cv.px(wx + int(rng.integers(2, ww - 2)), wy - 10 + int(rng.integers(0, 40)), "#c8d0f0")
        cv.rect(wx - 8, wy - 10, 10, wh + 10, "#5a2430"); cv.rect(wx + ww - 2, wy - 10, 10, wh + 10, "#5a2430")
        for dx in (-6, -2, ww, ww + 4):
            cv.vline(wx + dx, wy - 10, wh + 10, "#7a3440")
        sx = u + 82
        cv.rect(sx - 3, 90, 7, 12, OUT); cv.rect(sx - 2, 91, 5, 4, AMBER[3]); cv.rect(sx - 1, 96, 3, 5, S.GOLD[2])
        for (r, a) in [(26, 0.06), (16, 0.08), (8, 0.1)]:
            cv.ellipse(sx - r, 93 - r, 2 * r, 2 * r, C(AMBER[3], a))
    return cv.a


def drape_tex():
    """The booths' back drape laid flat (u = distance back from Z0): navy pleats, and for every booth
    a white header plate with the company name over its roll-up banner."""
    Lw, Hh = int(N_BOOTH * BOOTH + 10), int(DRAPE_H)
    cv = Canvas(Lw, Hh, seed=72)
    cv.rect(0, 0, Lw, Hh, L.NAVY[2])
    for x in range(0, Lw, 3):
        cv.vline(x, 8, Hh - 8, L.NAVY[1] if x % 6 else L.NAVY[3])
    cv.rect(0, 0, Lw, 3, IRON[3]); cv.hline(0, 0, Lw, IRON[4])                     # the pipe
    return cv


def booth_texture(side):
    """The drape with every booth's header plate and roll-up banner. The right-hand wall is read
    from its far end (see build), so its booths are laid out from the far end of the texture."""
    cv = drape_tex()
    Hh, Ld = cv.h, cv.w
    for k in range(N_BOOTH):
        name, pal = COMPANIES[(k * 2 + (0 if side < 0 else 1)) % len(COMPANIES)]
        u0 = int(k * BOOTH) if side < 0 else Ld - int((k + 1) * BOOTH)
        hw = max(text_width(name) + 10, 60)
        hx = u0 + int(BOOTH // 2) - hw // 2
        cv.rect(hx, 4, hw, 15, OUT); cv.rect(hx + 1, 5, hw - 2, 13, "#f2f2f6"); cv.rect(hx + 1, 15, hw - 2, 3, pal[2])
        text(cv, name, hx + hw // 2 - text_width(name) // 2, 5, pal[1])
        bx = u0 + int(BOOTH // 2) - 16
        cv.rect(bx - 1, 24, 34, Hh - 26, OUT); cv.rect(bx, 25, 32, Hh - 28, "#f2f2f6")
        cv.rect(bx, 25, 32, 12, pal[2])
        cv.poly([(bx + 6, 56), (bx + 13, 42), (bx + 18, 50), (bx + 21, 46), (bx + 27, 56)], pal[3])
        micro_text(cv, "HIRING", bx + 16 - micro_width("HIRING") // 2, 62, pal[1])
        cv.rect(bx, Hh - 18, 32, 14, pal[1])
        cv.rect(bx - 2, Hh - 4, 36, 3, IRON[4])
    return cv.a


def back_wall():
    """The far end at on-screen size: the ballroom end wall, the low stage with a podium and the
    CAREER FAIR skirt, a big screen with the LinkedOut feed's first slide, CU pennants either side."""
    cv = Canvas(FW, FH, seed=80)
    S.store_wall(cv, 0, 0, FW, FH, seed=81, pal=["#3a2c30", "#54403e", "#6a524c", "#7a605a", "#886c64", "#98786e", "#a88878"])
    cx = FW // 2
    # stage
    sy = FH - 12
    cv.rect(cx - 120, sy, 240, 12, OUT); cv.rect(cx - 119, sy + 1, 238, 3, L.WALNUT[4])
    cv.rect(cx - 119, sy + 4, 238, 8, L.NAVY[2])
    s = "CAREER FAIR"
    micro_text(cv, s, cx - micro_width(s) // 2, sy + 5, S.GOLD[4])
    # podium
    cv.rect(cx + 60, sy - 18, 16, 18, OUT); cv.rect(cx + 61, sy - 17, 14, 17, L.WALNUT[3]); cv.hline(cx + 61, sy - 17, 14, L.WALNUT[5])
    cv.rect(cx + 64, sy - 12, 8, 6, S.GOLD[2]); cv.vline(cx + 66, sy - 24, 7, IRON[3])
    # big screen
    sw, sh = 104, 56
    sx, sy0 = cx - sw // 2, sy - sh - 8
    cv.rect(sx - 3, sy0 - 3, sw + 6, sh + 6, OUT); cv.rect(sx - 2, sy0 - 2, sw + 4, sh + 4, "#1a1a22")
    cv.paste(feed_slides(sw, sh)[0], sx, sy0)
    for (d, a) in [(8, 0.04), (4, 0.06)]:
        cv.rect(sx - d, sy0 + sh + 3, sw + 2 * d, d, C("#8ac0f4", a))
    # pennants either side of the screen
    for k, px_ in enumerate([cx - 100, cx - 80, cx + 80, cx + 100]):
        col = S.BLACK[2] if k % 2 == 0 else S.GOLD[3]
        ink = S.GOLD[4] if k % 2 == 0 else S.BLACK[1]
        cv.rect(px_ - 7, 20, 15, 30, OUT); cv.rect(px_ - 6, 21, 13, 28, col)
        cv.poly([(px_ - 6, 49), (px_, 55), (px_ + 6, 49)], col)
        micro_text(cv, "CU", px_ - 3, 30, ink)
    L.fabric_banner(cv, cx - 60, cx + 60, 2, "CAREER FAIR")
    cv.rect(0, FH - 2, FW, 2, C(S.SHADOW, 0.5))
    return cv, (sx, sy0, sw, sh)


def feed_slides(w, h):
    """The big screen: three slides of the LinkedOut feed."""
    out = []
    posts = [("JUST GOT", "AN OFFER!", "#7ae0a0"), ("AGREE?", "HUSTLE IS", "#f2d23a"), ("WE'RE", "HIRING!!", "#ff8a7a")]
    for k, (a, b, c) in enumerate(posts):
        cv = Canvas(w, h)
        cv.rect(0, 0, w, h, L.LINKED[5]); cv.rect(0, 0, w, 12, L.LINKED[2])
        L.linkedout_logo(cv, 3, 2, size=8)
        text(cv, "LINKEDOUT", 14, 1, L.LINKED[5])
        cv.rect(4, 16, w - 8, h - 20, "#ffffff"); cv.hline(4, 16, w - 8, L.LINKED[4])
        cv.ellipse(8, 20, 12, 12, L.PAPER[0]); cv.ellipse(10, 22, 8, 6, "#e8c8a8"); cv.rect(10, 28, 8, 4, [L.PEAK[2], L.NAVY[3], "#a8442c"][k])
        text(cv, a, 24, 19, L.LINKED[0])
        text(cv, b, 24, 29, L.LINKED[1])
        cv.rect(8, h - 14, 12, 7, c); micro_text(cv, "+1", 10, h - 13, L.LINKED[0])
        micro_text(cv, f"{[214, 1987, 3][k]} LIKES", 24, h - 13, L.PAPER[0])
        out.append(cv)
    return out


def chandelier():
    """A small brass chandelier: a ring of candle bulbs, crystal drops, a chain."""
    cv = Canvas(40, 40, seed=5)
    for yy in range(0, 16, 2):
        cv.px(20, yy, S.GOLD[1]); cv.px(20, yy + 1, S.GOLD[2])
    cv.ellipse(6, 18, 29, 9, OUT); cv.ellipse(7, 19, 27, 7, S.GOLD[2]); cv.ellipse(10, 20, 21, 4, S.GOLD[1])
    cv.rect(18, 14, 5, 6, S.GOLD[3])
    bulbs = []
    for k, bx in enumerate((9, 15, 20, 25, 31)):
        cv.rect(bx, 15 + (2 if k in (0, 4) else 0), 2, 4, "#f6f4ee")
        cv.px(bx, 13 + (2 if k in (0, 4) else 0), "#fff0c4")
        bulbs.append((bx, 13 + (2 if k in (0, 4) else 0)))
    for k in range(5):
        cv.vline(10 + k * 5, 27, 4 + (k % 2) * 2, "#c8d8f0")
    cv.ellipse(17, 26, 7, 8, S.GOLD[2]); cv.px(20, 33, "#c8d8f0")
    return cv, bulbs


def table_shaders(pal, name, side):
    def front(u, Y, Z):
        rgb = np.repeat(pal_array([pal[1]])[0][None, :], u.shape[0], 0)
        rgb = np.where((Y > TABLE_H - 4)[:, None], pal_array([pal[2]])[0], rgb)
        rgb = np.where((np.mod(u, 12.0) < 1.0)[:, None], rgb * 0.85, rgb)
        mid = 30.0
        logo = (np.abs(u - mid) * 1.2 + (Y - 8)) < 10
        rgb = np.where((logo & (Y > 8))[:, None], pal_array([pal[3]])[0], rgb)
        rgb = np.where((Y < 2)[:, None], rgb * 0.6, rgb)
        out = rgba_of(np.clip(rgb, 0, 1))
        fog(out, Z, FOG, 420, 800, amount=0.3)
        return out

    def top(X, Z, z0=None, z1=None):
        rgb = np.repeat(pal_array([pal[2]])[0][None, :], X.shape[0], 0) * 1.12
        out = rgba_of(np.clip(rgb, 0, 1))
        fog(out, Z, FOG, 420, 800, amount=0.3)
        return out
    return front, top


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#1a1420")
    v.ground(floor_shader)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=CEIL)
    flat, screen = back_wall()
    fx0 = int(round(v.vx - FW / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - FH))
    v.strip(flat.a, fy0, fx0)
    # ballroom walls above the booths
    wall = wall_tex()
    Lw = wall.shape[1]
    for side in (-1, 1):
        def shade_wall(u, Y, Z, side=side):
            o = texture_lookup(wall, (Lw - 1 - u) if side < 0 else u, CEIL - Y, wrap=False)
            o[..., :3] *= 0.82 if side < 0 else 0.74
            fog(o, Z, FOG, 420, 800, amount=0.35)
            return o
        v.plane((side * WALL_X, Z_BACK), (side * WALL_X, Z0 - 60), shade_wall, y_max=CEIL)
    # booth back drapes
    for side in (-1, 1):
        tex = booth_texture(side)
        Ld = tex.shape[1]
        def shade_drape(u, Y, Z, tex=tex, side=side, Ld=Ld):
            uu = u if side < 0 else Ld - 1 - u
            o = texture_lookup(tex, uu, DRAPE_H - Y, wrap=False)
            o[..., :3] *= 0.92 if side < 0 else 0.82
            fog(o, Z, FOG, 420, 800, amount=0.3)
            return o
        v.plane((side * DRAPE_X, Z0), (side * DRAPE_X, Z0 + Ld), shade_drape, y_max=DRAPE_H)
    # booths from far to near: each booth's table, then the side drape in front of it
    def shade_div(u, Y, Z):
        rgb = np.repeat(pal_array([L.NAVY[3]])[0][None, :], u.shape[0], 0)
        rgb = np.where((np.mod(u, 4.0) < 1.5)[:, None], pal_array([L.NAVY[2]])[0], rgb)
        rgb = np.where((Y > 66)[:, None], pal_array([IRON[3]])[0], rgb)
        out_ = rgba_of(rgb)
        fog(out_, Z, FOG, 420, 800, amount=0.3)
        return out_
    for side in (-1, 1):
        v.plane((side * DRAPE_X, Z0 + N_BOOTH * BOOTH), (side * (TABLE_X + 4), Z0 + N_BOOTH * BOOTH), shade_div, y_max=68)
    for k in reversed(range(N_BOOTH)):
        z = Z0 + k * BOOTH
        for side in (-1, 1):
            name, pal = COMPANIES[(k * 2 + (0 if side < 0 else 1)) % len(COMPANIES)]
            za, zb = z + 14, z + BOOTH - 14
            front, top = table_shaders(pal, name, side)

            def top_masked(X, Z, za=za, zb=zb, side=side, top=top):
                o = top(X, Z)
                o[~((np.sign(X) == side) & (np.abs(X) > TABLE_X) & (np.abs(X) < TABLE_X + TABLE_D) & (Z > za) & (Z < zb)), 3] = 0
                return o
            v.ground(top_masked, y_from=v.h0 + 0.01, height=TABLE_H)
            v.plane((side * TABLE_X, za), (side * TABLE_X, zb), front, y_max=TABLE_H)
            v.plane((side * TABLE_X, za), (side * (TABLE_X + TABLE_D), za), front, y_max=TABLE_H)
            # swag on the table top: a brochure stand, a bowl of stress balls, the sign-up tablet
            for (dz, kind) in [(10, 0), (28, 1), (46, 2)]:
                spr = Canvas(10, 10)
                if kind == 0:
                    spr.rect(1, 1, 8, 9, OUT); spr.rect(2, 2, 6, 8, "#f2f2f6"); spr.rect(2, 2, 6, 3, pal[3])
                elif kind == 1:
                    spr.ellipse(0, 5, 10, 5, OUT); spr.ellipse(1, 5, 8, 4, "#d8dce4")
                    for j in range(3):
                        spr.px(2 + j * 3, 5, [pal[3], "#e86a5a", S.GOLD[3]][j])
                else:
                    spr.rect(1, 3, 8, 7, OUT); spr.rect(2, 4, 6, 5, "#e8f2fc"); spr.rect(2, 4, 6, 2, L.LINKED[2])
                v.sprite(spr.a, side * (TABLE_X + 12), za + dz, Y=TABLE_H, scale=1.3)
        for side in (-1, 1):
            v.plane((side * DRAPE_X, z), (side * (TABLE_X + 4), z), shade_div, y_max=68)
    # chandeliers and pennants hanging in the hall
    ch, bulbs = chandelier()
    lamp_pts = []
    for (X, z) in ((-160.0, 520.0), (160.0, 520.0), (0.0, 380.0)):
        sx_, sy_, s = v.sprite(ch.a, X, z, Y=CEIL - 10, anchor=(0.5, 0.0), scale=1.6)
        for (bx, by) in bulbs:
            p_ = [int(round(sx_ - 20 * s + bx * s)), int(round(sy_ + by * s)), "fff0c4", 1]
            if 0 <= p_[1] < 360:
                lamp_pts.append(p_)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    sx, sy0, sw, sh = screen
    for k, slide in enumerate(feed_slides(sw, sh)):
        name = f"battle-feed-{k}.png"
        slide.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if j == k else "0" for j in range(3)), "rate": 0.5,
                       "texture": res + name, "x": fx0 + sx, "y": fy0 + sy0})
    tabs = []
    for k in range(N_BOOTH):
        for side in (-1, 1):
            px_, py_ = v.project(side * (TABLE_X + 12), TABLE_H + 4, Z0 + k * BOOTH + 14 + 46)
            if 0 <= px_ < 640:
                tabs.append([int(round(px_)), int(round(py_)), "8ac0f4", 1])
    layers += [
        {"kind": "twinkle", "points": lamp_pts, "rate": 1.4, "min": 0.5},
        {"kind": "twinkle", "points": tabs, "rate": 0.9, "min": 0.3},
        {"kind": "particles", "style": "dust", "count": 24, "rect": [120, 10, 400, 130], "speed": [1, 3], "color": "f6e8c0"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
