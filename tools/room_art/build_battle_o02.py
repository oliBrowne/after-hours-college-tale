"""Battle backdrop for the notice hall (O02): looking down the length of Old Main's hall after
hours. On the left a row of shut office doors (frosted glass, gilt numbers, dark transoms, CLOSED
cards on the knobs) with crowded cork notice boards between them; on the right tall sash windows
throw moonlight across the encaustic tile and the indigo runner, silver radiators under them,
more boards between. Schoolhouse globes hang down the middle under the pressed-tin ceiling. At the
far end the big WHAT YOU OWE board sits under the old public-address horn, between the doorway to
the moonlit empty office and the lamp-lit cabinet room.
Animated: the horn speaks in bursts (sound rings), notices lift and settle in the draught, loose
pages tumble down the hall, dust turns in the moonlight, the globes breathe."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON
from lib_eng import micro_text, micro_width
from lib_oldmain import (plaster_om, cornice_om, stencil_frieze, beadboard, sash_window, radiator, horn_speaker, cork_surface,
                         oak_frame, scatter_notices, notice_paper, globe_pendant, sconce_om,
                         HALL_GREEN, OAK_IN, GILT_OM, TILE_TERRA, TILE_OX, TILE_CREAM, TILE_INK, RUNNER_OM, PAPER_TINTS,
                         CREAM_TRIM, HORN)
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "O02"
INK = "#10121e"
HAZE = "#1a2220"
VX = 300
Z0, Z_END = 170.0, 900.0
WALL_X = 250.0
HALL_H = 250.0
T = ROOM_TO_BATTLE                       # wall textures are painted at room scale
TEX_H = int(round(HALL_H / T)) + 1       # 148 room px from cornice to floor
RAIL = 104                               # chair rail (room px from the top of the wall texture)
DOORS = (24, 150, 276, 402)              # left wall: office doors (u, room px)
DOOR_NAMES = (("102", "BURSAR"), ("104", "RECORDS"), ("106", "DEAN"), ("108", "CLERK"))
L_BOARDS = (78, 204, 330)                # left wall: notice boards (u, room px)
WINDOWS_R = (40, 190, 340)               # right wall: sash windows (u, room px)
R_BOARDS = (98, 248)
PENDANTS = ((-92.0, 520.0), (92.0, 520.0), (-92.0, 760.0), (92.0, 760.0))
PENDANT_Y = 172.0
FLOOR_A = 27.0                           # tile lozenge period (world units) - the room's 16 px x 1.7


def wall_z(u_room):
    return Z0 + u_room * T


# ---------------------------------------------------------------------------- wall textures
def office_door(cv, x, bottom, number, name, w=30, h=72, lit=False, card=True):
    """An oak office door with a frosted upper panel (gilt number, small name), two raised panels
    below, a brass knob with a CLOSED card, a transom above, all in a moulded oak casing."""
    top = bottom - h
    # casing and transom
    cv.rect(x - 5, top - 17, w + 10, h + 17, OUT)
    cv.rect(x - 4, top - 16, w + 8, h + 16, OAK_IN[4]); cv.vline(x - 4, top - 16, h + 16, OAK_IN[6]); cv.vline(x + w + 3, top - 16, h + 16, OAK_IN[2])
    cv.hline(x - 4, top - 16, w + 8, OAK_IN[6])
    cv.rect(x - 7, top - 19, w + 14, 3, OUT); cv.hline(x - 6, top - 18, w + 12, CREAM_TRIM[4])
    cv.rect(x, top - 13, w, 9, "#141a2e" if not lit else "#a87a44")
    for k in range(1, 3):
        cv.vline(x + k * w // 3, top - 13, 9, OAK_IN[3])
    cv.hline(x, top - 4, w, OAK_IN[3]); cv.hline(x, top - 3, w, OAK_IN[5])
    # the door leaf
    cv.rect(x, top, w, h, OAK_IN[3]); cv.vline(x, top, h, OAK_IN[5]); cv.vline(x + w - 1, top, h, OAK_IN[1])
    gx, gy, gw, gh = x + 4, top + 4, w - 8, 28
    glass = ("#c8b07a", "#e0c890") if lit else ("#6a7484", "#7e8898")
    cv.rect(gx - 1, gy - 1, gw + 2, gh + 2, OAK_IN[1])
    cv.rect(gx, gy, gw, gh, glass[0])
    for yy in range(gy, gy + gh, 3):
        cv.hline(gx + (yy % 2), yy, gw - 1, glass[1])
    tw = text_width(number)
    text(cv, number, gx + (gw - tw) // 2, gy + 4, GILT_OM[4])
    nw = micro_width(name)
    micro_text(cv, name, gx + (gw - nw) // 2, gy + 16, GILT_OM[3])
    for py_ in (top + 36, top + 54):
        cv.rect(x + 4, py_, w - 8, 14, OAK_IN[2]); cv.rect(x + 5, py_ + 1, w - 10, 12, OAK_IN[4]); cv.rect(x + 7, py_ + 3, w - 14, 8, OAK_IN[3])
        cv.hline(x + 5, py_ + 1, w - 10, OAK_IN[6])
    kx, ky = x + w - 6, top + 40
    cv.rect(kx, ky, 3, 3, GILT_OM[3]); cv.px(kx, ky, GILT_OM[5])
    if card:
        cv.line(kx + 1, ky + 3, kx - 2, ky + 7, "#d8c8a0"); cv.line(kx + 1, ky + 3, kx + 4, ky + 7, "#d8c8a0")
        cv.rect(kx - 5, ky + 7, 12, 7, OUT); cv.rect(kx - 4, ky + 8, 10, 5, "#efe6cc")
        micro_text(cv, "SHUT", kx - 3, ky + 8, "#a82a24")


def left_wall_texture(length, seed=0):
    cv = Canvas(length, TEX_H, seed=seed)
    plaster_om(cv, 0, 13, length, RAIL - 13, pal=HALL_GREEN, seed=seed, shadow_top=6, cracks=0)
    cornice_om(cv, 0, 0, length)
    stencil_frieze(cv, 0, 13, length, ground=HALL_GREEN[2])
    beadboard(cv, 0, RAIL, length, TEX_H - RAIL, pal=OAK_IN, seed=seed + 1)
    for k, (u, (num, name)) in enumerate(zip(DOORS, DOOR_NAMES)):
        office_door(cv, u, TEX_H - 1, num, name, lit=(k == 2))
    papers = []
    for k, u in enumerate(L_BOARDS):
        oak_frame(cv, u, 40, 62, 46, t=3)
        cork_surface(cv, u + 3, 43, 56, 40, seed=seed + k)
        for p in scatter_notices(cv, u + 3, 43, 56, 40, seed=seed + 10 + k,
                                 titles=["FEES", "KEYS", "SIGN", "LOST", "HOURS", "NO", "FORMS"]):
            papers.append(p)
    return cv.a, papers


def right_wall_texture(length, seed=0):
    cv = Canvas(length, TEX_H, seed=seed)
    plaster_om(cv, 0, 13, length, RAIL - 13, pal=HALL_GREEN, seed=seed, shadow_top=6, cracks=0)
    cornice_om(cv, 0, 0, length)
    stencil_frieze(cv, 0, 13, length, ground=HALL_GREEN[2])
    beadboard(cv, 0, RAIL, length, TEX_H - RAIL, pal=OAK_IN, seed=seed + 1)
    for k, u in enumerate(WINDOWS_R):
        sash_window(cv, u, 26, 32, 64, seed=seed + k, moon=(u + 22, 40, 4) if k == 1 else None)
        radiator(cv, u + 1, 114, 30, 22)
    papers = []
    for k, u in enumerate(R_BOARDS):
        oak_frame(cv, u, 44, 54, 40, t=3)
        cork_surface(cv, u + 3, 47, 48, 34, seed=seed + k)
        papers += scatter_notices(cv, u + 3, 47, 48, 34, seed=seed + 20 + k, titles=["ROOM", "HOURS", "QUIET", "SIGN"])
        sconce_om(cv, u + 66, 66)
    return cv.a, papers


# ---------------------------------------------------------------------------- the far end
def end_wall(Wp, Hp):
    """The end of the hall at its on-screen size: the WHAT YOU OWE board under the horn, the
    doorways to the empty office (moonlit) and the cabinet room (lamp-lit) either side."""
    cv = Canvas(Wp, Hp, seed=4)
    rail = Hp - 27
    plaster_om(cv, 0, 4, Wp, rail - 4, pal=HALL_GREEN, seed=9, shadow_top=3, cracks=0, cell=20)
    cv.rect(0, 0, Wp, 3, "#262030"); cv.hline(0, 2, Wp, CREAM_TRIM[4]); cv.hline(0, 3, Wp, CREAM_TRIM[2])
    cv.rect(0, 4, Wp, 3, HALL_GREEN[2]); cv.hline(0, 4, Wp, GILT_OM[2])
    for xx in range(3, Wp, 6):
        cv.px(xx, 5, GILT_OM[3])
    beadboard(cv, 0, rail, Wp, Hp - rail, pal=OAK_IN, seed=3, board=4)
    cx = Wp // 2
    # the board
    bw, bh = 92, 36
    bx, by = cx - bw // 2, rail - bh - 6
    oak_frame(cv, bx, by, bw, bh, t=3)
    cv.rect(bx + 3, by + 3, bw - 6, 10, "#1c1622")
    text(cv, "WHAT YOU OWE", cx - text_width("WHAT YOU OWE") // 2 + 1, by + 2, GILT_OM[4])
    cork_surface(cv, bx + 3, by + 13, bw - 6, bh - 16, seed=5)
    papers = scatter_notices(cv, bx + 3, by + 13, bw - 6, bh - 16, seed=8, titles=["DUE", "OWED", "HOURS"])
    mouth = horn_speaker(cv, cx - 2, by - 22, wire_to=0, length=11, mouth=6)
    # doorways
    doors = []
    for side in (-1, 1):
        dw, dh = 22, 43
        dx = 10 if side < 0 else Wp - 10 - dw
        dy = Hp - dh
        cv.rect(dx - 3, dy - 3, dw + 6, dh + 3, OUT)
        cv.rect(dx - 2, dy - 2, dw + 4, dh + 2, OAK_IN[4]); cv.hline(dx - 2, dy - 2, dw + 4, OAK_IN[6])
        if side < 0:      # the empty office: dark, a moonlit window on its far wall
            cv.rect(dx, dy, dw, dh, "#141a30")
            cv.rect(dx + 6, dy + 8, 10, 16, "#2a3a6a"); cv.rect(dx + 7, dy + 9, 8, 14, "#4a5a90"); cv.vline(dx + 11, dy + 9, 14, "#2a3a6a")
            cv.poly([(dx + 4, dy + dh), (dx + 18, dy + dh), (dx + 16, dy + 30), (dx + 7, dy + 30)], C("#8aa0e0", 0.25))
            label = "OFFICE"
        else:             # the cabinet room: oxblood walls and lamplight
            cv.rect(dx, dy, dw, dh, "#4a1a1e")
            cv.rect(dx, dy + 24, dw, dh - 24, "#3a1416"); cv.hline(dx, dy + 24, dw, "#6a2a28")
            cv.rect(dx, dy + dh - 6, dw, 6, "#2a1210")
            cv.rect(dx + 2, dy + 14, 6, dh - 20, "#2a1a1a"); cv.hline(dx + 2, dy + 20, 6, "#4a3a36"); cv.hline(dx + 2, dy + 27, 6, "#4a3a36")
            cv.ellipse(dx + 7, dy + 8, 15, 15, C("#f6cf7a", 0.18))
            cv.poly([(dx + 12, dy + 12), (dx + 17, dy + 12), (dx + 19, dy + 17), (dx + 10, dy + 17)], "#f6cd78")
            cv.hline(dx + 11, dy + 17, 8, "#fde9b6"); cv.vline(dx + 14, dy + 18, dh - 21, "#8a6630")
            cv.rect(dx + 2, dy + dh - 4, dw - 4, 2, C("#f6cf7a", 0.3))
            label = "CABINET"
        lw = micro_width(label)
        cv.rect(dx + dw // 2 - lw // 2 - 2, dy - 11, lw + 4, 7, "#1c1622")
        micro_text(cv, label, dx + dw // 2 - lw // 2, dy - 10, GILT_OM[4])
        doors.append((dx, dy, dw, dh))
    return cv, papers, mouth


# ---------------------------------------------------------------------------- shaders
def floor_shader(X, Z):
    a = FLOOR_A
    u, v = (X + Z) / a, (X - Z) / a
    iu, iv = np.floor(u), np.floor(v)
    fu, fv = u - iu, v - iv
    check = ((iu + iv) % 2).astype(int)
    t = hash2(iu, iv, 8)
    A, B, K, Kc = pal_array(TILE_TERRA), pal_array(TILE_OX), pal_array(TILE_INK), pal_array(TILE_CREAM)
    tone = np.where(t < 0.25, 1, 2)
    rgb = np.where(check[:, None] == 0, A[tone], B[tone])
    lit = (fu < 0.10) | (fv > 0.90)
    rgb = np.where(lit[:, None], np.where(check[:, None] == 0, A[3], B[3]), rgb)
    grout = (fu < 0.05) | (fv < 0.05)
    rgb[grout] = K[1]
    du, dv = np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv)
    rgb[(du < 0.15) & (dv < 0.15)] = K[0]
    rgb[(du < 0.09) & (dv < 0.09)] = Kc[2]
    # border fillets along the walls
    ax = np.abs(X)
    rgb[(ax > WALL_X - 16)] = B[2]
    rgb[(np.abs(ax - (WALL_X - 16)) < 1.5) | (np.abs(ax - (WALL_X - 5)) < 1.2)] = K[0]
    # the runner
    rp = pal_array(RUNNER_OM)
    g = pal_array(GILT_OM)
    run = ax < 34
    rgb[run] = rp[2]
    rgb[run & (ax > 28)] = rp[1]
    rgb[run & (np.abs(ax - 25) < 1.5)] = g[2]
    rgb[run & (np.abs(ax - 31) < 1.2)] = rp[4]
    lz = (Z % 48.0) - 24
    loz = run & (ax + np.abs(lz) * 0.6 < 10)
    rgb[loz] = rp[4]
    rgb[run & (ax + np.abs(lz) * 0.6 < 3)] = g[3]
    # moonlight from the right-hand windows, laid across the floor in slanting panes
    for u0 in WINDOWS_R:
        z0, z1 = wall_z(u0), wall_z(u0 + 32)
        mz = Z + (WALL_X - X) * 0.55
        pane = (mz > z0) & (mz < z1) & (X > -60) & (X < WALL_X - 4)
        rgb[pane] = rgb[pane] * 0.8 + np.array(C("#b4c4f0")[:3]) * 0.2
        bar = pane & (np.abs(mz - (z0 + z1) / 2) < 2.2)
        rgb[bar] = rgb[bar] * 0.85
    for (px_, pz) in PENDANTS:
        warm_light(rgb, np.hypot(X - px_, (Z - pz) * 0.6), 120, strength=0.30)
    warm_light(rgb, np.hypot(X - 200, (Z - 880) * 0.5), 90, strength=0.25)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 600, 1400, amount=0.45)
    return out


def ceiling_shader(X, Z):
    """Pressed tin: square panels with a raised boss, beaded borders, dark painted cream-grey."""
    rgb = np.zeros((X.shape[0], 3), np.float32)
    s = 34.0
    fx, fz = (X % s) / s, (Z % s) / s
    rgb[:] = np.array(C("#2c2834")[:3])
    edge = (fx < 0.08) | (fz < 0.08)
    rgb[edge] = np.array(C("#3a3442")[:3])
    rgb[(fx < 0.04) | (fz < 0.04)] = np.array(C("#1e1a26")[:3])
    boss = (np.abs(fx - 0.5) + np.abs(fz - 0.5)) < 0.18
    rgb[boss] = np.array(C("#423a4a")[:3])
    rgb[(np.abs(fx - 0.5) + np.abs(fz - 0.5)) < 0.07] = np.array(C("#4e4656")[:3])
    rgb[np.abs(X) > WALL_X - 18] = np.array(C(CREAM_TRIM[2])[:3]) * 0.55
    for (px_, pz) in PENDANTS:
        warm_light(rgb, np.hypot(X - px_, (Z - pz)), 70, strength=0.2)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 500, 1300, amount=0.55)
    return out


# ---------------------------------------------------------------------------- build
def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, vx=VX, cam=52, fill="#141223")
    v.ground(floor_shader, z_max=Z_END)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=HALL_H, z_max=Z_END)
    L = int((Z_END - Z0) / T) + 2
    walls = {}
    for side in (-1, 1):
        tex, papers = left_wall_texture(L, seed=40) if side < 0 else right_wall_texture(L, seed=60)
        walls[side] = papers

        def shade_wall(u, Y, Z, tex=tex, side=side):
            o = texture_lookup(tex, u / T, (HALL_H - Y) / T, wrap=False)
            o[..., :3] *= 0.86 if side < 0 else 0.9
            for (px_, pz) in PENDANTS:
                warm_light(o[..., :3], np.abs(Z - pz) + np.abs(Y - 120) * 0.5, 110, strength=0.18)
            return fog(o, Z, HAZE, 600, 1400, amount=0.45)
        v.plane((side * WALL_X, Z0), (side * WALL_X, Z_END), shade_wall, y_max=HALL_H)
    # the far end, at its on-screen size
    s = v.scale(Z_END)
    Wp = int(round(2 * WALL_X * s)) + 2
    Hp = int(round(HALL_H * s))
    ew, end_papers, mouth = end_wall(Wp, Hp)
    ew.a[..., :3] *= 0.9
    fx0 = int(round(v.vx - Wp / 2))
    fy0 = int(round(v.ground_y(Z_END) - Hp))
    v.strip(ew.a, fy0, fx0)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp 1:1 globes on their chains
    glows = []
    for (px_, pz) in sorted(PENDANTS, key=lambda p: -p[1]):
        x, y = v.project(px_, PENDANT_Y, pz)
        _, ytop = v.project(px_, HALL_H, pz)
        r = max(3, int(round(6 * v.scale(pz) * 1.4)))
        globe_pendant(cv, int(round(x)), int(round(y)), chain_top=max(0, int(round(ytop))), lit=True, r=r)
        glows.append([int(round(x)), int(round(y)), "fde9b6", 2])
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    # notices lifting in the draught: a pale corner flips up and its shadow shows
    rng = np.random.default_rng(17)
    flips = []
    for side, papers in walls.items():
        for (px_, py_, pw, ph, tint) in papers:
            u_world = (px_ + pw) * T
            Z = Z0 + u_world
            Y = HALL_H - (py_ + ph) * T
            sx, sy = v.project(side * WALL_X, Y, Z)
            if not (0 <= sx < 640 and 0 <= sy < 166) or (392 <= sx <= 628 and sy <= 72) or (12 <= sx <= 65 and sy <= 26):
                continue
            sc = T * v.scale(Z)
            flips.append((sx, sy, sc, tint, side))
    for (px_, py_, pw, ph, tint) in end_papers:
        flips.append((fx0 + px_ + pw - 1, fy0 + py_ + ph - 1, 0.6, tint, 0))
    pick = rng.permutation(len(flips))[:12]
    n = len(pick)
    for k, i in enumerate(pick):
        sx, sy, sc, tint, side = flips[int(i)]
        w_ = max(2, int(round(4 * sc))); h_ = max(1, int(round(3 * sc)))
        x0 = int(round(sx - w_)) if side >= 0 else int(round(sx - w_ // 2))
        y0 = int(round(sy - h_))
        pat = ["0"] * (n * 2)
        pat[(k * 2) % len(pat)] = "1"
        if rng.random() < 0.5:
            pat[(k * 2 + 1) % len(pat)] = "1"
        layers.append({"kind": "blink", "pattern": "".join(pat), "rate": 3.0,
                       "rects": [[x0, y0 + h_, w_, max(1, h_ // 2), "1a120c", 0.6], [x0, y0 - 1, w_, h_, tint.lstrip("#")],
                                 [x0, y0 - 1, w_, 1, "fff6dc"]]})
    # the horn speaks in bursts: three rings travelling out of the mouth
    mx, my = fx0 + mouth[0], fy0 + mouth[1]
    for k in range(3):
        r = 4 + k * 3
        ring = Canvas(2 * r + 3, 2 * r + 3)
        cc = r + 1
        for ang in np.linspace(-0.2, 2.2, 14):
            ring.px(int(round(cc + np.cos(ang) * r)), int(round(cc + np.sin(ang) * r)), C("#f2e2c0", 0.8 - 0.2 * k))
        name = f"battle-ring-{k}.png"
        ring.save(os.path.join(out, name))
        pat = ["0"] * 16
        for burst in (0, 4):
            pat[burst + k] = "1"
        layers.append({"kind": "blink", "pattern": "".join(pat), "rate": 5.0, "texture": res + name, "x": mx - cc + 2, "y": my - cc + 2})
    layers += [
        {"kind": "twinkle", "points": glows, "rate": 1.2, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 20, "rect": [330, 20, 300, 140], "speed": [1, 2], "color": "c8d4f0"},
        {"kind": "particles", "style": "wind", "count": 6, "rect": [0, 118, 640, 46], "speed": [34, 0]},
        {"kind": "fauna", "fauna": [{"kind": "loose_page", "x": 40, "y": 70, "fly": 16.0, "rate": 6.0},
                                    {"kind": "loose_page", "x": 360, "y": 112, "fly": 12.0, "rate": 5.0}]},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
