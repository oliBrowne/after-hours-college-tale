"""Battle backdrop for the Pearl Street open office (P01): Kyle's pitch. The fight happens on the
heart-pine floor in the middle of the office, looking down the room at the far brick wall, where
the projector throws the deck onto the pull-down screen: DISRUPTR in pink neon to its left over
the stairwell door, the break room's warm doorway to its right. Down the left wall, the tall arched
windows onto Pearl Street at night (lit cornices across the mall, the trees in white lights) over
cast-iron radiators; down the right wall, the whiteboard wall, the vests, the MOVE FAST poster.
Joists and the spiral duct overhead, Edison pendants, standing desks with glowing monitors, the
gong. Layers: the slides advance, the projector beam and its dust, the R buzzing, street lights
twinkling, the bulbs breathing."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_umc import halo
import p01_lib as L

ROOM = "P01"
INK = "#10121e"
F = 320.0
SC = 72 / 52                   # room-scale sprite -> battle world scale
WALL_X = 300.0
Z_NEAR, Z_BACK = 250.0, 520.0
CEIL = 200.0
FW = int(round(2 * WALL_X * F / Z_BACK))
FH = int(round(CEIL * F / Z_BACK))
WIN_Z = (300.0, 380.0, 460.0)  # centres of the left wall's windows
WIN_W, WIN_Y0, WIN_Y1 = 46, 52, 160
PENDANTS = [(-190.0, 290.0), (190.0, 290.0), (-70.0, 300.0), (70.0, 300.0)]


def floor_shader(X, Z):
    """Heart-pine boards running toward the screen, nail pairs and butt joints, satin sheen; warm
    pools under the pendants, the screen's cool spill, window light from the left, tyre scuffs."""
    plank = 11.0
    col = np.floor(X / plank)
    fx = X / plank - col
    length = 90 + 70 * hash2(col, 3)
    off = hash2(col, 5) * length
    seg = np.floor((Z + off) / length)
    fz = (Z + off) / length - seg
    tone = hash2(col, seg, 7)
    pine = pal_array(L.PINE)
    k = np.clip((3 + tone * 3.99).astype(int), 3, 6)
    rgb = pine[k] * 0.92
    grain = hash2(np.floor(X / 2.0), np.floor(Z / 7.0), 11)
    rgb = rgb * (0.93 + 0.09 * grain[:, None])
    rgb[fx < 0.09] = pine[1]
    rgb[fz < 0.012] = pine[1]
    for (px_, pz) in PENDANTS:
        warm_light(rgb, np.hypot((X - px_) * 1.0, (Z - pz) * 2.2), 120, colour="#f6cf7a", strength=0.28)
    warm_light(rgb, np.hypot(X * 0.8, (Z - Z_BACK) * 1.6), 220, colour="#dfe8ff", strength=0.32)
    for wz in WIN_Z:                                             # cool street light through the windows
        warm_light(rgb, np.hypot((X + WALL_X - 30) * 1.4, (Z - wz - 20) * 1.1), 70, colour="#b8c8f0", strength=0.2)
    # the scuffed donut where Kyle likes to stop
    ring = np.abs(np.hypot((X - 150) * 0.9, (Z - 360) * 2.6) - 60)
    rgb = np.where(((ring < 2.2) & (hash2(np.floor(X / 3), np.floor(Z / 3), 9) > 0.25))[:, None], rgb * 0.55, rgb)
    out = rgba_of(rgb)
    fog(out, Z, "#2a1e26", 480, 800, amount=0.4)
    return out


def ceiling_shader(X, Z):
    """Joists across the room, the plank decking between them, the spiral duct down the middle."""
    t = pal_array(L.TIMBER)
    d = pal_array(L.DUCT)
    jz = np.mod(Z, 48.0)
    rgb = np.where((jz < 9)[:, None], t[3], t[1])
    rgb = np.where(((jz >= 9) & (jz < 10))[:, None], t[0], rgb)
    rgb = np.where(((jz >= 0) & (jz < 1.5))[:, None], t[4], rgb)
    plank = np.mod(X, 14.0) < 1.0
    rgb = np.where((plank & (jz >= 10))[:, None], t[0], rgb)
    duct = np.abs(X + 40) < 15
    seam = np.mod(Z + (X + 40) * 0.4, 8.0) < 1.2
    dt = np.where((np.abs(X + 40) < 5)[:, None], d[4], np.where((np.abs(X + 40) < 11)[:, None], d[3], d[2]))
    dt = np.where(seam[:, None], d[1], dt)
    rgb = np.where(duct[:, None], dt, rgb)
    out = rgba_of(rgb)
    fog(out, Z, "#1a1418", 400, 700, amount=0.45)
    return out


def left_wall_tex():
    """The window wall laid out along its length (u = depth from Z_NEAR): brick, three arched windows
    onto Pearl Street, radiators. Returns texture and the window-light texels."""
    Lw, Hh = int(Z_BACK - Z_NEAR), int(CEIL)
    cv = Canvas(Lw, Hh, seed=21)
    L.brick_wall_p(cv, 0, 0, Lw, Hh, seed=22)
    cv.rect(0, Hh - 7, Lw, 7, L.TIMBER[2]); cv.hline(0, Hh - 7, Lw, L.TIMBER[4])
    view, lights = L.pearl_view(Lw, WIN_Y1 - WIN_Y0 + 20, seed=23)
    pts = []
    for wz in WIN_Z:
        cx = int(wz - Z_NEAR)
        top = Hh - WIN_Y1
        h = WIN_Y1 - WIN_Y0
        L.arched_window(cv, cx, top, WIN_W, h, view, cx - WIN_W // 2, seed=int(wz))
        L.radiator(cv, cx, Hh - 7, w=36, h=22)
        for (lx, ly) in lights:
            sx, sy = lx, top - 7 + ly
            if cx - WIN_W // 2 + 6 < sx < cx + WIN_W // 2 - 6 and top < sy < top + h - 6:
                pts.append((sx, sy))
    return cv.a, pts


def right_wall_tex():
    """The whiteboard wall along the right: brick, a long run of whiteboard, the vests, a poster."""
    Lw, Hh = int(Z_BACK - Z_NEAR), int(CEIL)
    cv = Canvas(Lw, Hh, seed=31)
    L.brick_wall_p(cv, 0, 0, Lw, Hh, seed=32)
    cv.rect(0, Hh - 7, Lw, 7, L.TIMBER[2]); cv.hline(0, Hh - 7, Lw, L.TIMBER[4])
    L.framed_poster(cv, 20, Hh - 150, 34, 46, ["MOVE", "FAST &", "BREAK", "THINGS", "(NOT", "THE TV)"])
    L.vest_hooks(cv, 70, Hh - 152, n=3)
    L.whiteboard(cv, 120, Hh - 140, 140, 80, seed=33)
    for ox in (40, 200):
        cv.rect(ox, Hh - 22, 5, 7, OUT); cv.rect(ox + 1, Hh - 21, 3, 5, "#d8d2c4")
    return cv.a


def back_wall():
    """The far wall at its on-screen size: brick, the screen with the title slide, the neon and the
    stair door on the left, the break-room doorway on the right."""
    cv = Canvas(FW, FH, seed=41)
    L.brick_wall_p(cv, 0, 0, FW, FH, seed=42)
    for y0, a in [(0, 0.35), (1, 0.2)]:
        cv.hline(0, y0, FW, C(L.SHADOW, a))
    L.baseboard(cv, 0, FH, FW)
    sw, sh = L.SLIDE_W + 16, L.SLIDE_H + 14
    sx0 = FW // 2 - sw // 2
    slide_at = L.projection_screen(cv, sx0, 9, sw, sh)
    # left: neon over the stair door
    L.neon_bolt(cv, 22, 14, L.NEON_CYAN)
    L.neon_text(cv, "DISRUPTR", 40, 18, L.NEON_PINK, scale=1)
    L.stair_door(cv, 52, FH, w=34, h=62)
    # right: the break room's doorway, warm
    L.doorway_glimpse(cv, FW - 50, FH, w=42, h=64)
    halo(cv, FW - 50, FH - 30, 40, "#f6c27a", 0.06)
    L.thermostat(cv, FW - 92, 60)
    return cv, slide_at


def pendant_sprite(drop=40):
    cv = Canvas(9, drop + 14)
    cv.vline(4, 0, drop, "#1a1418")
    cv.rect(2, drop, 5, 3, "#2a2420"); cv.hline(2, drop, 5, "#6a5a3a")
    cv.ellipse(1, drop + 3, 7, 9, OUT); cv.ellipse(2, drop + 4, 5, 7, L.WARM[3])
    cv.vline(4, drop + 5, 4, L.WARM[4])
    return cv


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#1a1420")
    v.ground(floor_shader)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=CEIL)
    flat, slide_at = back_wall()
    fx0 = int(round(v.vx - FW / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - FH))
    v.strip(flat.a, fy0, fx0)
    ltex, lpts = left_wall_tex()
    rtex = right_wall_tex()
    Lw = ltex.shape[1]

    def shade_left(u, Y, Z):
        o = texture_lookup(ltex, u, CEIL - Y, wrap=False)
        o[..., :3] *= 0.86
        fog(o, Z, "#2a1e26", 480, 800, amount=0.3)
        return o

    def shade_right(u, Y, Z):
        o = texture_lookup(rtex, Lw - 1 - u, CEIL - Y, wrap=False)
        o[..., :3] *= 0.76
        fog(o, Z, "#2a1e26", 480, 800, amount=0.3)
        return o
    v.plane((-WALL_X, Z_NEAR), (-WALL_X, Z_BACK), shade_left, y_max=CEIL)
    v.plane((WALL_X, Z_NEAR), (WALL_X, Z_BACK), shade_right, y_max=CEIL)
    # pendants hanging from the joists
    bulbs = []
    for (px_, pz) in PENDANTS:
        spr = pendant_sprite(36)
        v.sprite(spr.a, px_, pz, Y=CEIL, anchor=(0.5, 0.0), scale=SC)
        bx, by = v.project(px_, CEIL - (36 + 7) * SC, pz)
        bulbs.append([int(round(bx)), int(round(by)), "f6cf7a", 1])
    # furniture: standing desks down the left, the gong, a fig and the ping-pong table down the right
    things = [(L.standing_desk("triple", seed=3), -232, 505), (L.standing_desk("cleared", seed=4), -238, 430),
              (L.tall_plant(34, 64, "fig", seed=9), 250, 500), (L.gong_stand(40, 58, seed=8), 236, 430),
              (L.ping_pong_p(120, 46, seed=6), 160, 470)]
    glows = []
    for (made, X, Z) in sorted(things, key=lambda t: -t[2]):
        s_, ax_, ay_ = made[:3]
        v.sprite(s_.a, X, Z, anchor=(ax_ / s_.w, ay_ / s_.h), scale=SC)
        if X < 0:
            gx, gy = v.project(X, 46 * SC, Z)
            glows.append([int(round(gx)), int(round(gy)), "8ab8ec", 1])
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    sx, sy = fx0 + slide_at[0], fy0 + slide_at[1]
    cv.paste(L.slide("title"), sx, sy)                          # the deck stays crisp at 1:1
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    for k, kind in enumerate(["traction", "tam", "hiring"]):
        name = f"battle-slide-{kind}.png"
        L.slide(kind).save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if j == k + 1 else "0" for j in range(4)), "rate": 0.4,
                       "texture": res + name, "x": sx, "y": sy})
    win = []
    for (tu, tv) in lpts:
        px_, py_ = v.project(-WALL_X, CEIL - tv, Z_NEAR + tu)
        if 0 <= px_ < 640 and 0 <= py_ < 160:
            win.append([int(round(px_)), int(round(py_)), "fff4d0", 1])
    r_x = fx0 + 40 + 7 * 6
    layers += [
        {"kind": "beam", "x": 320, "y": -30, "angle": 90, "sweep": 1.5, "period": 9.0, "phase": 0.0,
         "length": 150, "width": 190, "color": "e8f0ff", "alpha": 0.07, "floor": 124},
        {"kind": "blink", "pattern": "00000000000000101100000000000000000000000000001000", "rate": 10.0,
         "rects": [[r_x - 1, fy0 + 17, 8, 10, "3a1e24", 0.7]]},
        {"kind": "twinkle", "points": win, "rate": 1.3, "min": 0.3},
        {"kind": "twinkle", "points": bulbs, "rate": 0.6, "min": 0.7},
        {"kind": "twinkle", "points": glows, "rate": 2.4, "min": 0.6},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [200, 10, 240, 120], "speed": [0, 3], "color": "e8f0ff"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
