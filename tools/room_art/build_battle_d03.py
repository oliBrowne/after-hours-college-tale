"""Battle backdrop for the Farrand lobby and laundry (D03): the fight happens in the laundry room's
aisle, looking down it toward the doorway back into the lobby, where the fire is going.

Coin-op top-loaders run back along the left wall under the mint glazed tile, stacked dryers along
the right with their chrome-ringed portholes (the nearest upper one still tumbling), fluorescent
tubes on the acoustic ceiling, speckled lino with a floor drain. The far wall: the LOST SOCKS
board, the clock, the LAUNDRY plate, the soap machine and the doorway, warm with firelight, the
lobby couch and the fireplace beyond. In the aisle: the folding table with its stacks, the wire
cart, a WET FLOOR sign by a soapy puddle, a basket of somebody's laundry.
Layers: the dryer tumbling, one tube flickering, the fire breathing in the doorway, lint drifting."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_eng import painted_block, micro_text, micro_width, wall_clock, outlet
from lib_umc import soft_ellipse, halo
from lib_oldmain import cork_surface
import d02_lib as L

ROOM = "D03"
INK = "#10121e"
F = 320.0
SC = 72 / 52                   # room-scale sprite -> battle world scale
WALL_X = 290.0                 # side walls
ROW_X = 256.0                  # machine fronts
Z_BACK = 560.0
N_MACH = 4                     # machines in each row
ROW_Z = (Z_BACK - N_MACH * 58.0, Z_BACK)   # machine rows run from here back to the far wall
CEIL = 120.0
WASH_H, DRY_H = 58.0, 96.0
WASH_W, DRY_W = 56, 56
TUBES = [(-80.0, 380.0, 450.0), (-80.0, 480.0, 550.0), (80.0, 380.0, 450.0), (80.0, 480.0, 550.0),
         (-80.0, 280.0, 350.0), (80.0, 280.0, 350.0)]
FLICKER = 3                    # index of the tube that flickers
FW = int(round(2 * WALL_X * F / Z_BACK))
FH = int(round(CEIL * F / Z_BACK))
DOOR = (FW // 2 - 17, 34)     # doorway into the lobby in the flat (centred on the aisle): left x, width


def floor_shader(X, Z):
    """Laundry lino: greige and grey tiles, an oxblood border at the machines, the floor drain,
    a soapy puddle by the sign, cool tube light down the aisle and a warm tongue from the lobby."""
    tile = 22.0
    cx, cz = np.floor(X / tile), np.floor(Z / tile)
    fx, fz = X / tile - cx, Z / tile - cz
    f, g, ox = pal_array(L.LINO_F), pal_array(L.LINO_G), pal_array(L.LINO_OX)
    r = hash2(cx, cz, 4)
    k = np.where(r < 0.93, 2, np.where(r < 0.97, 3, 1))
    rgb = np.where((((cx + cz) % 2) == 0)[:, None], f[k], g[k])
    border = (np.abs(X) > ROW_X - 18) | (Z > Z_BACK - 18)
    rgb = np.where(border[:, None], ox[2], rgb)
    rgb = np.where(((fx < 0.05) | (fz < 0.05))[:, None], rgb * 0.88, rgb)
    chip = hash2(np.floor(X / 2.5), np.floor(Z / 3.0), 6)
    rgb = np.where((chip < 0.05)[:, None], rgb * 0.86, np.where((chip > 0.97)[:, None], rgb * 1.1, rgb))
    # the drain: a chrome disc with slots
    d = np.hypot(X - 10, (Z - 470) * 1.0)
    rgb = np.where((d < 11)[:, None], pal_array([L.CHROME[2]])[0], rgb)
    rgb = np.where(((d < 9) & (np.abs(np.mod(X, 4) - 2) < 0.8))[:, None], pal_array([L.CHROME[0]])[0], rgb)
    # cool light down the aisle, warm from the doorway
    for (tx, z0, z1) in TUBES:
        warm_light(rgb, np.hypot((X - tx) * 0.8, np.maximum(0, np.abs(Z - (z0 + z1) / 2) - 30)), 90, colour="#e8f0ff", strength=0.2)
    dx = (DOOR[0] + DOOR[1] / 2 - FW / 2) * Z_BACK / F
    warm_light(rgb, np.hypot((X - dx) * 1.6, (Z - Z_BACK) * 0.9), 150, colour="#f6a050", strength=0.32)
    # soapy puddle by the WET FLOOR sign
    p = np.hypot((X - 92) / 46, (Z - 420) / 22)
    rgb = np.where((p < 1)[:, None], rgb * 0.7 + pal_array(["#a8c4e0"])[0] * 0.32, rgb)
    rgb = np.where(((p < 0.5) & (hash2(np.floor(X / 3), np.floor(Z / 3), 8) > 0.8))[:, None], pal_array(["#e8f0f8"])[0], rgb)
    out = rgba_of(np.clip(rgb, 0, 1))
    fog(out, Z, "#2a2632", 560, 900, amount=0.3)
    return out


def ceiling_shader(X, Z):
    """Acoustic tile in a T-bar grid, two rows of wrap-lens fluorescent fixtures."""
    a = pal_array(L.ACOUSTIC)
    gx, gz = X / 25.0, Z / 25.0
    rgb = np.repeat(a[3][None, :], X.shape[0], 0)
    rgb = np.where((hash2(np.floor(X / 2), np.floor(Z / 3), 22) > 0.85)[:, None], a[2], rgb)
    rgb = np.where(((np.abs(gx - np.round(gx)) < 0.05) | (np.abs(gz - np.round(gz)) < 0.035))[:, None], a[2] * 0.96, rgb)
    for (tx, z0, z1) in TUBES:
        body = (np.abs(X - tx) < 13) & (Z > z0) & (Z < z1)
        lens = (np.abs(X - tx) < 10) & (Z > z0 + 2) & (Z < z1 - 2)
        rgb = np.where(body[:, None], pal_array([L.CHROME[1]])[0], rgb)
        rgb = np.where(lens[:, None], pal_array(["#e8eef6"])[0], rgb)
        rgb = np.where((lens & (np.abs(X - tx) < 4))[:, None], pal_array(["#ffffff"])[0], rgb)
        warm_light(rgb, np.hypot(X - tx, np.maximum(0, np.abs(Z - (z0 + z1) / 2) - 35)), 40, colour="#e8f0ff", strength=0.2)
    out = rgba_of(rgb)
    out[..., :3] *= 0.86
    fog(out, Z, "#2a2632", 560, 900, amount=0.3)
    out[(Z > Z_BACK) | (np.abs(X) > WALL_X), 3] = 0
    return out


def side_wall_tex():
    """The side walls above the machines: mint glazed tile to shoulder height, cream block above."""
    Lw, Hh = int(Z_BACK - 250), int(CEIL)
    cv = Canvas(Lw, Hh, seed=70)
    painted_block(cv, 0, 0, Lw, Hh, seed=71, pal=L.FH_BLOCK, course=10, length=22)
    L.tile_wainscot(cv, 0, Hh - 100, Lw, 100)
    cv.rect(0, 0, Lw, 3, C(L.SHADOW, 0.3))
    return cv.a


def washer_tex():
    """The left row in world units (u from the near end back): coin-op top-loaders."""
    Lw, Hh = int(ROW_Z[1] - ROW_Z[0]), int(WASH_H)
    cv = Canvas(Lw, Hh, seed=72)
    cv.rect(0, 0, Lw, Hh, "#1e1a24")
    for k, u in enumerate(range(0, Lw - WASH_W + 1, WASH_W + 2)):
        w = WASH_W
        cv.rect(u, 0, w, 12, "#c8ccd6"); cv.hline(u, 0, w, "#eef0f4")                 # backsplash
        cv.ellipse(u + 6, 3, 7, 7, "#5a5c6a"); cv.px(u + 9, 5, "#e8e8f0")               # dial
        cv.rect(u + 20, 4, 10, 4, "#2a3a2a"); cv.px(u + 22, 5, "#7ae0a0" if k % 2 == 0 else "#e8c24a")
        cv.rect(u + w - 18, 3, 13, 5, L.CHROME[2]); cv.rect(u + w - 17, 4, 11, 3, L.CHROME[4])
        cv.rect(u, 12, w, 3, "#f6f8fc")                                                   # lid edge
        cv.rect(u, 15, w, Hh - 19, "#d8dce4"); cv.vline(u, 15, Hh - 19, "#f2f4f8"); cv.vline(u + w - 1, 15, Hh - 19, "#a8acb8")
        cv.rect(u + w // 2 - 8, 20, 16, 11, OUT); cv.rect(u + w // 2 - 7, 21, 14, 9, L.CHROME[3])   # coin meter
        cv.rect(u + w // 2 - 4, 23, 8, 1, OUT); cv.rect(u + w // 2 - 3, 26, 6, 3, "#e8c24a")
        cv.rect(u + 6, 36, w - 12, 2, "#b8bcc8")
        cv.rect(u, Hh - 4, w, 4, "#8a8e9a")
    return cv.a


def dryer_tex():
    """The right row: stacked dryers, chrome-ringed portholes, the upper drums lit. Symmetric
    pieces only (this wall is seen mirrored)."""
    Lw, Hh = int(ROW_Z[1] - ROW_Z[0]), int(DRY_H)
    cv = Canvas(Lw, Hh, seed=73)
    cv.rect(0, 0, Lw, Hh, "#1e1a24")
    wins = []
    half = Hh // 2
    for k, u in enumerate(range(0, Lw - DRY_W + 1, DRY_W + 2)):
        w = DRY_W
        for j in range(2):
            y0 = j * half
            cv.rect(u, y0, w, half - 1, "#d8dce4"); cv.hline(u, y0, w, "#f2f4f8")
            cv.rect(u, y0, w, 8, "#c8ccd6"); cv.hline(u, y0 + 8, w, "#a8acb8")
            cv.rect(u + w // 2 - 6, y0 + 3, 12, 3, "#2a2a36")
            cv.px(u + w // 2, y0 + 4, "#ff5a4a" if (j == 0 and k % 2 == 0) else "#3a3a46")
            cx, cy, r = u + w // 2, y0 + 8 + (half - 9) // 2, 15
            cv.ellipse(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, OUT)
            cv.ellipse(cx - r, cy - r, 2 * r + 1, 2 * r + 1, L.CHROME[3])
            cv.ellipse(cx - r + 3, cy - r + 3, 2 * r - 5, 2 * r - 5, L.CHROME[1])
            lit = j == 0
            cv.ellipse(cx - r + 4, cy - r + 4, 2 * r - 7, 2 * r - 7, "#a8784a" if lit else "#20222e")
            if lit:
                cv.ellipse(cx - r + 7, cy - r + 7, 2 * r - 13, 2 * r - 13, "#c89058")
            wins.append((u + w / 2, Hh - cy, r - 4, lit))
        cv.rect(u, Hh - 3, w, 3, "#8a8e9a")
    return cv.a, wins


def back_wall():
    """The far wall at its on-screen size (scale F / Z_BACK)."""
    cv = Canvas(FW, FH, seed=74)
    painted_block(cv, 0, 0, FW, FH, seed=75, pal=L.FH_BLOCK, course=5, length=11)
    L.tile_wainscot(cv, 0, FH - 26, FW, 26)
    cv.rect(0, 0, FW, 2, C(L.SHADOW, 0.3))
    cv.rect(0, FH - 2, FW, 2, "#2a2226")
    # the doorway into the lobby: firelit walls, the sandstone fireplace with the fire going,
    # terrazzo, the end of the teal couch
    dx, dw = DOOR
    dh = 46
    top = FH - dh
    cv.rect(dx - 3, top - 3, dw + 6, dh + 3, OUT); cv.rect(dx - 2, top - 2, dw + 4, dh + 2, L.STEEL_T[3])
    cv.vline(dx - 2, top - 2, dh + 2, L.STEEL_T[5])
    cv.rect(dx, top, dw, dh, "#c4895a")
    cv.rect(dx, top, dw, 5, "#9a6644"); cv.rect(dx, top + 5, dw, 2, "#ae7650")
    for yy in range(top + 10, FH - 8, 5):                                   # brick of the lobby wall, lit
        cv.hline(dx, yy, dw, "#b47a50")
    cx = dx + dw // 2
    cv.rect(cx - 9, top + 6, 18, dh - 12, L.FH_SAND[3]); cv.vline(cx - 9, top + 6, dh - 12, L.FH_SAND[5])   # chimney breast
    cv.rect(cx - 12, FH - 22, 24, 3, L.FH_SAND[5])                                                          # mantel
    cv.rect(cx - 7, FH - 17, 14, 10, "#2a1410")                                                             # firebox
    cv.rect(cx - 5, FH - 12, 10, 4, "#e9a84a"); cv.rect(cx - 3, FH - 15, 6, 4, "#f6cd78"); cv.px(cx, FH - 16, "#fff0c4")
    cv.rect(dx, FH - 7, dw, 5, "#a48a80"); cv.hline(dx, FH - 7, dw, "#c8aea0")                            # terrazzo
    cv.rect(dx, FH - 12, 7, 8, L.VINYL_T[2]); cv.hline(dx, FH - 12, 7, L.VINYL_T[4])                      # couch end
    cv.rect(dx + dw - 6, FH - 26, 2, 22, L.BRASS_FH[2]); cv.rect(dx + dw - 9, FH - 30, 8, 5, "#f6cd78")      # the brass lamp
    cv.rect(dx, FH - 2, dw, 2, "#5a3a2a")
    halo(cv, cx, FH - 12, 26, colour="#f6a050", strength=0.2, steps=3)
    s = "LOBBY"
    cv.rect(dx + dw // 2 - micro_width(s) // 2 - 2, top - 10, micro_width(s) + 4, 7, "#2a2a36")
    micro_text(cv, s, dx + dw // 2 - micro_width(s) // 2, top - 9, "#e8d8a8")
    # LOST SOCKS board and the clock, left of the door
    bx, by, bw, bh = 40, 14, 56, 30
    cv.rect(bx - 2, by - 2, bw + 4, bh + 4, OUT); cv.rect(bx - 1, by - 1, bw + 2, bh + 2, L.BIRCH[3])
    cork_surface(cv, bx, by, bw, bh, seed=3)
    s = "LOST SOCKS"
    cv.rect(bx + bw // 2 - micro_width(s) // 2 - 2, by + 2, micro_width(s) + 4, 7, "#f2ecdc")
    micro_text(cv, s, bx + bw // 2 - micro_width(s) // 2, by + 3, "#c84a3c")
    for k in range(6):
        sx, sy = bx + 5 + k * 8, by + 12 + (k % 2) * 3
        c = ["#e6e2d6", "#c84a3c", "#3a5aa8", "#e8c24a", "#5c897c", "#c890d0"][k]
        cv.rect(sx, sy, 3, 9, OUT); cv.rect(sx + 1, sy, 1, 8, c); cv.rect(sx + 1, sy + 7, 4, 3, OUT); cv.rect(sx + 2, sy + 7, 2, 2, c)
    wall_clock(cv, 112, 20, r=5)
    # LAUNDRY plate and CARD ONLY, right of the door; the soap machine against the wall
    s = "LAUNDRY"
    cv.rect(206, 12, micro_width(s) + 6, 9, OUT); cv.rect(207, 13, micro_width(s) + 4, 7, "#2a2a36")
    micro_text(cv, s, 209, 14, "#e8d8a8")
    s = "CARD ONLY"
    cv.rect(204, 26, micro_width(s) + 6, 8, "#f2ecdc"); micro_text(cv, s, 207, 27, "#3a5aa8")
    soap, sax, say = L.vending_soap(22, 42, seed=3)
    cv.paste(soap, 268 - sax, FH - say)
    outlet(cv, 120, FH - 22); outlet(cv, 236, FH - 22)
    return cv


def tumble_frames_ellipse(w, h, n=4, seed=0):
    """Clothes tumbling in a lit drum seen at an angle: n frames inside a w x h ellipse."""
    cols = ["#c84a3c", "#e6e2d6", "#3a5aa8", "#e8c24a", "#5c897c"]
    frames = []
    yy, xx = np.mgrid[0:h, 0:w]
    inside = ((xx - (w - 1) / 2) / (w / 2)) ** 2 + ((yy - (h - 1) / 2) / (h / 2)) ** 2 <= 1
    for f in range(n):
        cv = Canvas(w, h)
        cv.rect(0, 0, w, h, "#a8784a")
        for k, c in enumerate(cols):
            a = f * np.pi / 2 + k * 1.25
            rr = 0.35 + 0.12 * (k % 3)
            x = int(round((w - 1) / 2 + np.cos(a) * rr * w / 2))
            y = int(round((h - 1) / 2 + np.sin(a) * rr * h / 2)) + 1
            cv.rect(x - 2, y - 2, 4, 4, shade(c, -0.25)); cv.rect(x - 1, y - 2, 3, 3, c)
        cv.a[~inside] = 0
        frames.append(cv)
    return frames


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#1a1420")
    v.ground(floor_shader)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=CEIL)
    flat = back_wall()
    fx0 = int(round(v.vx - FW / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - FH))
    v.strip(flat.a, fy0, fx0)
    # side walls (seen above the machines), far to near
    wall = side_wall_tex()
    Lw = wall.shape[1]
    for side in (-1, 1):
        def shade_side(u, Y, Z, side=side):
            uu = Lw - 1 - u if side < 0 else u
            o = texture_lookup(wall, uu, CEIL - Y, wrap=False)
            o[..., :3] *= 0.82 if side < 0 else 0.74
            fog(o, Z, "#2a2632", 560, 900, amount=0.3)
            return o
        v.plane((side * WALL_X, Z_BACK), (side * WALL_X, 250.0), shade_side, y_max=CEIL)
    # the machine rows: fronts, then the near end faces
    wtex = washer_tex()
    dtex, wins = dryer_tex()

    def shade_wash(u, Y, Z):
        o = texture_lookup(wtex, u, WASH_H - Y, wrap=False)
        o[..., :3] *= 0.9
        fog(o, Z, "#2a2632", 560, 900, amount=0.3)
        return o

    def shade_dry(u, Y, Z):
        o = texture_lookup(dtex, u, DRY_H - Y, wrap=False)
        o[..., :3] *= 0.8
        fog(o, Z, "#2a2632", 560, 900, amount=0.3)
        return o
    v.plane((-ROW_X, ROW_Z[0]), (-ROW_X, ROW_Z[1]), shade_wash, y_max=WASH_H)
    v.plane((ROW_X, ROW_Z[0]), (ROW_X, ROW_Z[1]), shade_dry, y_max=DRY_H)

    def end_face(height, tone, split=None):
        """The side panel of the first machine: lit top edge, a seam, the kick base in shadow."""
        def sh(u, Y, Z):
            rgb = np.repeat(pal_array([tone])[0][None, :], u.shape[0], 0)
            rgb = np.where((Y > height - 3)[:, None], rgb * 1.15, rgb)
            rgb = np.where((Y < 4)[:, None], rgb * 0.6, rgb)
            rgb = np.where((np.abs(u - 4) < 1.2)[:, None], rgb * 0.82, rgb)
            if split:
                rgb = np.where((np.abs(Y - split) < 1.2)[:, None], pal_array([OUT])[0], rgb)
            else:
                rgb = np.where((np.abs(Y - (height - 12)) < 1.0)[:, None], rgb * 0.85, rgb)
            # a laminated notice taped to the panel (CLEAN THE LINT TRAP / NO DYE): ruled lines
            note = (u > 9) & (u < 27) & (Y > height * 0.52) & (Y < height * 0.52 + 22)
            rgb = np.where(note[:, None], pal_array(["#f2ecdc"])[0], rgb)
            rule = note & (np.mod(Y - height * 0.52, 4) < 1) & (Y < height * 0.52 + 18) & (u > 11) & (u < 25)
            rgb = np.where(rule[:, None], pal_array(["#5a5a6a"])[0], rgb)
            head = note & (Y > height * 0.52 + 17)
            rgb = np.where(head[:, None], pal_array(["#c84a3c"])[0], rgb)
            return rgba_of(np.clip(rgb, 0, 1))
        return sh
    v.plane((-WALL_X, ROW_Z[0]), (-ROW_X, ROW_Z[0]), end_face(WASH_H, "#b8bcc8"), y_max=WASH_H)
    v.plane((WALL_X, ROW_Z[0]), (ROW_X, ROW_Z[0]), end_face(DRY_H, "#a8acb8", split=DRY_H / 2), y_max=DRY_H)
    # things in the aisle (room-scale sprites)
    for (made, X, Z) in [(L.folding_table_fh(120, 34, seed=8), -112, 470),
                         (L.wire_cart(34, 38, seed=10), 150, 520),
                         (L.wet_floor_sign(18, 26), 70, 418),
                         (L.laundry_pile(36, 24, seed=11), -60, 380)]:
        s_, ax_, ay_ = made[:3]
        v.sprite(s_.a, X, Z, anchor=(ax_ / s_.w, ay_ / s_.h), scale=SC)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    # the nearest lit dryer drum tumbling (an ellipse foreshortened along the wall)
    u_c, y_c, r, _ = wins[0]
    z_c = ROW_Z[0] + (DRY_W / 2)
    xa, _ = v.project(ROW_X, y_c, z_c - r)
    xb, _ = v.project(ROW_X, y_c, z_c + r)
    sx, sy = v.project(ROW_X, y_c, z_c)
    tw = max(4, int(round(abs(xa - xb))))
    th = max(4, int(round(2 * r * F / z_c)))
    for k, fr in enumerate(tumble_frames_ellipse(tw, th, 4, seed=2)):
        name = f"battle-tumble-{k}.png"
        fr.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if j == k else "0" for j in range(4)), "rate": 3.0,
                       "texture": res + name, "x": int(round(sx - tw / 2)), "y": int(round(sy - th / 2))})
    # one tube flickering: dim its lens with rects along its length
    tx, z0, z1 = TUBES[FLICKER]
    rects = []
    for z in np.arange(z0 + 3, z1 - 2, 3.0):
        px_, py_ = v.project(tx, CEIL, z)
        hw = max(1, int(round(10 * F / z)))
        rects.append([int(round(px_)) - hw, int(round(py_)), 2 * hw, 1, "5e564c", 0.7])
    layers.append({"kind": "blink", "pattern": "11111111111111111111110101111111111111111", "rate": 8.0, "rects": rects})
    # the fire in the lobby doorway, lint in the tube light
    fire = [[fx0 + DOOR[0] + DOOR[1] // 2 - 4 + k * 3, fy0 + FH - 11 + (k % 2), c, 1] for k, c in enumerate(["e9a84a", "f6cd78", "fff0c4", "f6cd78"])]
    layers += [
        {"kind": "twinkle", "points": fire, "rate": 3.0, "min": 0.35},
        {"kind": "particles", "style": "dust", "count": 20, "rect": [150, 20, 340, 120], "speed": [2, 2], "color": "e8f0ff"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
