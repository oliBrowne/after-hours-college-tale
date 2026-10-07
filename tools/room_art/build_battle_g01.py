"""Battle backdrop for Folsom Field (G01): standing in the centre aisle among the white chairs,
looking up the black-and-gold runner to the commencement stage. The podium on its thrust is the
focal point; faculty in robes and coloured hoods sit on the deck in front of the black drape with
its COMMENCEMENT banner. Behind, the stadium bowl: packed end-zone stands with the video board
on the left corner, the tall side stands rising out of frame on both sides, light standards on
the rim, and the Flatirons standing over it all in the morning sun. Ground: mown turf bands, the
goal and five-yard lines, chair shadows running away to the right, confetti along the aisle.
Layers: a cirrus strip drifting behind the mountains, mortarboards tossed into the air, falling
confetti, camera flashes in the crowd, soft shafts of sunlit haze, birds."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, mix, shade, text, text_width
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, texture_lookup
from lib_macky2 import title_flatirons, band_ramp, _rng
import lib_grad as G

ROOM = "G01"
INK = "#10121e"
HAZE = "#e6dccc"
Z_BACK = 1300.0                 # end-zone stands (fronto-parallel)
X_SIDE = 700.0                  # side stands' front face
Z_SIDE0 = 380.0                 # where the side stands start (beside the viewer)
RIM_BACK = 140.0                # rim height of the end-zone stands
WALL_H = 14.0                   # padded field wall at the foot of the stands
K = 3.0                         # world units per crowd-texture pixel
Z_STAGE, Z_DECK1, Z_DRAPE = 660.0, 745.0, 770.0
STAGE_W, DECK_H, DRAPE_H = 300.0, 34.0, 112.0
RUNNER = 68.0
GOAL_Z, FIVE_Z = 632.0, 408.0
HASH_X = 300.0
CHAIR_ROWS = [500.0, 548.0, 596.0]
CHAIR_X0, CHAIR_DX, CHAIR_N = 104.0, 51.0, 10


def side_rim(Z):
    """The side stands climb toward the viewer (the bowl wraps round)."""
    return RIM_BACK + np.clip(Z_BACK - Z, 0, None) * 0.4


# ---------------------------------------------------------------------------------------------
# crowd texture (room-scale painting of seat rows, sampled by the stand planes)
# ---------------------------------------------------------------------------------------------
def crowd_texture(seed, width=1500, height=200):
    cv = Canvas(width, height, fill=G.RISER[2])
    G.stands(cv, lambda x: 0, height - 1, x0=0, x1=width, pitch=5, bow=0,
             aisles=tuple(range(60, width, 96)), concourse=(14, tuple(range(108, width, 192))), seed=seed,
             zones=[(0, 300, 0, 12, [G.GOLD[3], G.GOLD[4], G.BLACK[1]], [5, 2, 2], 0.85)], haze=None, signs=0.02)
    # banners hung over the front rail
    rng = _rng(seed)
    x = 40
    labels = [("SKO BUFFS", None, None), ("CONGRATS GRADS", "#f4f2ec", G.BLACK[1]), ("WE ARE SO PROUD", G.BLACK[1], G.GOLD[3]),
              ("GO BUFFS", None, None), ("CLASS ACT", "#f4f2ec", G.BLACK[1])]
    i = 0
    while x < width - 120:
        lab, bgc, fgc = labels[(i + seed) % len(labels)]
        x += G.stand_banner(cv, x, height - 13, lab, bg=bgc, fg=fgc) + int(rng.integers(60, 160))
        i += 1
    return cv.a


def stand_shader(tex, back=False, flip=False):
    h, w = tex.shape[:2]

    def shade_(u, Y, Z):
        n = len(Y)
        out = np.zeros((n, 4), np.float32)
        rim = np.full(n, RIM_BACK, np.float32) if back else side_rim(Z)
        tu = (u / K) if not flip else (w - 1 - u / K)
        tv = (h - 1) - (Y - WALL_H) / K
        crowd = texture_lookup(tex, tu, tv, wrap=True)
        crowd[..., 3] = 1
        out[:] = crowd
        # parapet along the rim
        lip = (Y > rim - 6) & (Y <= rim)
        out[lip, :3] = pal_array([G.RISER[4]])[0]
        out[lip & (Y > rim - 2), :3] = pal_array(["#e8dccc"])[0]
        # the padded field wall with its gold stripe
        wall = Y < WALL_H
        out[wall, :3] = pal_array([G.BLACK[1]])[0]
        out[wall & (Y > WALL_H - 2.5), :3] = pal_array([G.RISER[5]])[0]
        out[wall & (np.abs(Y - 8) < 1.6), :3] = pal_array([G.GOLD[3]])[0]
        out[Y > rim, 3] = 0
        fog(out, Z, HAZE, 300, 1600, amount=0.3)
        return out
    return shade_


# ---------------------------------------------------------------------------------------------
# ground
# ---------------------------------------------------------------------------------------------
def in_chair_shadow(X, Z):
    """Chair shadows lying away and to the right (low sun behind the viewer's left shoulder)."""
    sh = np.zeros(X.shape, bool)
    for zr in CHAIR_ROWS:
        dz = Z - zr
        on = (dz >= 0) & (dz < 34)
        Xs = X - 0.7 * dz
        for sgn in (-1, 1):
            j = np.round((sgn * Xs - CHAIR_X0) / CHAIR_DX)
            ok = (j >= 0) & (j < CHAIR_N)
            cx = sgn * (CHAIR_X0 + j * CHAIR_DX)
            sh |= on & ok & (np.abs(Xs - cx) < 13)
    return sh


def ground_shader(X, Z):
    n = X.shape[0]
    rgb = np.zeros((n, 3), np.float32)
    ax = np.abs(X)
    scr_x = X * 320.0 / Z
    scr_y = 52 * 320.0 / Z
    stripe = (np.floor(Z / 56.0) % 2).astype(int)
    tuft = hash2(np.floor(scr_x / 2), np.floor(scr_y), 3)
    sun = pal_array(G.TURF_SUN)
    shd = pal_array(G.TURF_SHADE)
    k = np.clip(5 - 2 * stripe + (tuft > 0.8) * 1 + (tuft > 0.95) * 1 - (tuft < 0.18) * 1, 0, 7)
    rgb[:] = sun[k]
    sh = in_chair_shadow(X, Z)
    ks = np.clip(4 - stripe + (tuft > 0.85) * 1 - (tuft < 0.15) * 1, 0, 7)
    rgb[sh] = shd[ks[sh]]
    # field lines
    line = pal_array([G.LINE[2]])[0]
    for (lz, half) in ((GOAL_Z, 6.0), (FIVE_Z, 3.5)):
        m = np.abs(Z - lz) < half
        rgb[m] = rgb[m] * 0.12 + line * 0.88
    hm = (np.abs(ax - HASH_X) < 10) & (np.abs(((Z + 22) % 45) - 22) < 2.0) & (Z < GOAL_Z)
    rgb[hm] = rgb[hm] * 0.15 + line * 0.85
    # the aisle runner, black with gold borders and a pinstripe
    run = (ax < RUNNER) & (Z < Z_STAGE)
    blk = pal_array(G.BLACK)
    pile = (np.floor(Z / 9.0) % 3 == 0)
    rr = np.where(pile[:, None], blk[1], blk[2])
    rgb[run] = rr[run]
    rgb[run & (ax > RUNNER - 6)] = pal_array([G.GOLD[2]])[0]
    rgb[run & (ax > RUNNER - 2)] = pal_array([G.GOLD[4]])[0]
    rgb[run & (np.abs(ax - (RUNNER - 13)) < 1.4)] = pal_array([G.GOLD[2]])[0]
    rgb[run & sh] *= 0.7
    # confetti lying along the aisle and around the stage
    cell = hash2(np.floor(X / 4), np.floor(Z / 4), 21)
    dens = (np.clip(1 - np.abs(ax - 50) / 140, 0, 1) * 0.10 + np.clip(1 - np.abs(Z - (Z_STAGE - 30)) / 60, 0, 1) * 0.08) \
        * np.clip((Z - 300) / 250, 0.15, 1)
    conf = cell < dens
    cols = pal_array(G.CONFETTI_PILE)
    pick = (hash2(np.floor(X / 4), np.floor(Z / 4), 22) * len(G.CONFETTI_PILE)).astype(int)
    rgb[conf] = cols[np.clip(pick, 0, len(G.CONFETTI_PILE) - 1)][conf]
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 500, 1700, amount=0.45)
    return out


# ---------------------------------------------------------------------------------------------
# stage
# ---------------------------------------------------------------------------------------------
def skirt_texture():
    """The stage front at room scale: black pleated skirt, gold nosing, fan bunting, swags."""
    w, h = int(2 * STAGE_W / ROOM_TO_BATTLE), int(DECK_H / ROOM_TO_BATTLE) + 2
    cv = Canvas(w, h, fill=G.BLACK[1])
    for x in range(w):
        if x % 4 == 0:
            cv.vline(x, 2, h - 2, G.BLACK[0])
        elif x % 4 == 1:
            cv.vline(x, 2, h - 2, G.BLACK[2])
    cv.rect(0, 0, w, 2, G.GOLD[3]); cv.hline(0, 0, w, G.GOLD[4])
    for fx in range(26, w - 20, 34):
        if abs(fx - w // 2) < 30:
            continue
        G.fan_bunting(cv, fx, 2, r=10)
    return cv.a


def drape_shader(X, Y):
    n = len(X)
    out = np.zeros((n, 4), np.float32)
    f = np.floor((X + 400) / 9.0) % 3
    pal = pal_array(["#121016", "#1a1820", "#221e28"])
    out[:, :3] = pal[f.astype(int)]
    out[:, 3] = 1
    top = Y > DRAPE_H - 4
    out[top, :3] = pal_array([G.STEEL[2]])[0]
    return out


def deck_shader(X, Z):
    n = len(X)
    out = np.zeros((n, 4), np.float32)
    inside = (np.abs(X) < STAGE_W) & (Z >= Z_STAGE) & (Z <= Z_DRAPE)
    out[:, :3] = pal_array(["#545462"])[0]
    out[:, 3] = inside.astype(np.float32)
    return out


def podium_sprite():
    spr, ax, ay = G.podium_thrust()
    return spr.a, ax / spr.w, ay / spr.h


# ---------------------------------------------------------------------------------------------
# sky and the range
# ---------------------------------------------------------------------------------------------
def sky(v):
    cv = Canvas(640, 112)
    G.morning_sky(cv, 0, 0, 640, 112, seed=4)
    rng = _rng(6)
    from lib_macky2 import cirrus
    for (x, y, ln) in [(60, 14, 120), (300, 6, 90), (520, 20, 100)]:
        cirrus(cv, x, y, ln, rng, pal=("#e8e4ea", "#f6f2f2", "#d4d0de"))
    v.strip(cv.a, 0, solid=False)


def mountains(v):
    src, ridge = title_flatirons(1.2)
    h, w = src.shape[:2]
    x0 = 50                                   # the slabs centred over the stage, Green Mountain to the left
    from lib_macky2 import valley_haze
    cv = Canvas(640, 120)
    cv.paste(src, x0, -2)
    valley_haze(cv, 0, 640, 60, 112, colour="#e0d4d0", alpha=(0.12, 0.2, 0.3), seed=3, mask=cv.a[..., 3] > 0.5)
    v.strip(cv.a, 0, solid=True)


def board_sprite():
    """A smaller video board for the far corner, CONGRATULATIONS / GRADUATES (1x letters)."""
    w, h = 104, 44
    cv = Canvas(w + 2, h + 30)
    x, y = 1, 1
    for lx in (x + 20, x + w - 24):
        cv.rect(lx, y + h, 4, 28, G.STEEL[2]); cv.vline(lx, y + h, 28, G.STEEL[4])
    cv.rect(x - 1, y - 1, w + 2, h + 2, G.INK)
    cv.rect(x, y, w, h, G.STEEL[1]); cv.hline(x, y, w, G.STEEL[4])
    cv.rect(x + 3, y + 3, w - 6, 9, G.BLACK[1]); cv.hline(x + 3, y + 11, w - 6, G.GOLD[2])
    text(cv, "CU BOULDER", x + (w - text_width("CU BOULDER")) // 2, y + 1, G.GOLD[3])
    cv.rect(x + 3, y + 13, w - 6, h - 19, "#10141c")
    for yy in range(y + 13, y + h - 6, 2):
        cv.hline(x + 3, yy, w - 6, "#141a24")
    s1, s2 = "CONGRATULATIONS", "GRADUATES"
    text(cv, s1, x + (w - text_width(s1)) // 2, y + 12, G.GOLD[4])
    text(cv, s2, x + (w - text_width(s2)) // 2, y + 22, "#fff6dc")
    cv.rect(x + 3, y + h - 5, w - 6, 3, G.GOLD[2]); cv.hline(x + 3, y + h - 5, w - 6, G.GOLD[4])
    return cv


def tower_sprite():
    cv = Canvas(32, 64)
    G.light_tower(cv, 16, 2, 64)
    return cv


# ---------------------------------------------------------------------------------------------
def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    rng = _rng(12)
    v = View(horizon=98, cam=52)
    sky(v)
    mountains(v)
    # light standards and the video board stand on the end-zone rim (behind the stand faces)
    tw = tower_sprite()
    for X in (-X_SIDE + 40, X_SIDE - 40):
        v.sprite(tw.a, X, Z_BACK + 10, Y=RIM_BACK - 4, anchor=(0.5, 1.0), scale=(Z_BACK + 10) / v.F)
    # the stadium: end-zone stands, then both side stands (rows converge on the vanishing point)
    back_tex = crowd_texture(31)
    v.back(Z_BACK, lambda X, Y: stand_shader(back_tex, back=True)(X + 2000, Y, np.full(len(X), Z_BACK, np.float32)),
           region=lambda X, Y: (np.abs(X) <= X_SIDE) & (Y >= 0) & (Y <= RIM_BACK))
    side_tex = crowd_texture(32, width=1600, height=260)
    v.plane((-X_SIDE, Z_BACK), (-X_SIDE, Z_SIDE0), stand_shader(side_tex), y_max=600)
    v.plane((X_SIDE, Z_SIDE0), (X_SIDE, Z_BACK), stand_shader(side_tex, flip=True), y_max=600)
    v.ground(ground_shader, z_max=Z_BACK)
    # board on the left corner of the rim, drawn crisp at 1:1
    bd = board_sprite()
    v.sprite(bd.a, -X_SIDE + 60, Z_BACK, Y=RIM_BACK - 30, anchor=(0.5, 1.0), scale=Z_BACK / v.F)
    # the stage: drape, deck, faculty, skirt, podium, flowers, pennants
    v.back(Z_DRAPE, drape_shader, region=lambda X, Y: (np.abs(X) <= STAGE_W - 40) & (Y >= DECK_H) & (Y <= DRAPE_H))
    v.ground(deck_shader, height=DECK_H, z_max=Z_DRAPE)
    seats = []
    for side in (-1, 1):
        for k in range(4):
            seats.append((side * (52 + k * 30), Z_DECK1, k))
        for k in range(4):
            seats.append((side * (66 + k * 30), Z_DECK1 - 40, k))
    seats.sort(key=lambda s: -s[1])
    for i, (X, Z, k) in enumerate(seats):
        hood = G.HOODS[int(rng.integers(0, len(G.HOODS)))]
        if rng.random() < 0.18:
            spr, ax, ay = G.draped_chair(hood, seed=i)
        else:
            spr, ax, ay = G.seated_faculty(hood, G.SKIN[int(rng.integers(0, len(G.SKIN)))], G.HAIR[int(rng.integers(0, len(G.HAIR)))],
                                           seed=i, clap=rng.random() < 0.4, tam=rng.random() < 0.7)
        v.sprite(spr.a, X, Z, Y=DECK_H, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE)
    sk = skirt_texture()
    skh, skw = sk.shape[:2]
    v.plane((-STAGE_W, Z_STAGE), (STAGE_W, Z_STAGE),
            lambda u, Y, Z: texture_lookup(sk, u / ROOM_TO_BATTLE, (DECK_H - Y) / ROOM_TO_BATTLE, wrap=False), y_max=DECK_H)
    for X in (-STAGE_W - 22, STAGE_W + 22):
        cv = Canvas(30, 40)
        G.flower_urn(cv, 15, 38, h=32, seed=int(X))
        v.sprite(cv.a, X, Z_STAGE - 6, anchor=(0.5, 38 / 40), scale=ROOM_TO_BATTLE)
    for i, X in enumerate(np.arange(-STAGE_W + 40, STAGE_W - 30, 30)):
        if abs(X) < 60:
            continue
        cv = Canvas(20, 22)
        G.flower_pot(cv, 10, 20, kind=["gold", "white", "gold", "purple"][i % 4], w=12, h=7, seed=i)
        v.sprite(cv.a, X, Z_STAGE - 8, anchor=(0.5, 20 / 22), scale=ROOM_TO_BATTLE)
    for (X, body, trim) in ((-STAGE_W + 20, G.GOLD[3], G.GOLD[1]), (STAGE_W - 20, G.BLACK[1], G.GOLD[3])):
        cv = Canvas(30, 110)
        G.pennant(cv, 8, 12, 58, body, trim, emblem=lambda c, x, y, b=body: G._torch(c, x, y, G.BLACK[1] if b == G.GOLD[3] else G.GOLD[3], "#c84a3c"))
        cv.vline(14, 4, 104, G.STEEL[3]); cv.px(14, 3, G.GOLD[4])
        v.sprite(cv.a, X, Z_DECK1, Y=DECK_H, anchor=(14 / 30, 108 / 110), scale=ROOM_TO_BATTLE)
    for (X, Z, kind) in [(-150, 380, "prog"), (190, 360, "cap"), (-96, 430, "open"), (128, 470, "prog"), (-260, 470, "cap"),
                         (240, 440, "open"), (84, 340, "bouquet")]:
        c3 = Canvas(20, 12)
        if kind == "cap":
            G.cap_flat(c3, 3, 2)
        elif kind == "bouquet":
            c3.line(2, 8, 13, 5, G.LEAFG[3]); c3.line(2, 9, 12, 6, G.LEAFG[2]); c3.rect(4, 7, 4, 3, "#e6dcc6")
            for (fx, fy, col) in [(13, 3, G.FLOWERS["red"][2]), (15, 5, G.FLOWERS["gold"][2]), (11, 4, G.FLOWERS["white"][3])]:
                c3.rect(fx - 1, fy - 1, 3, 3, G.INK); c3.rect(fx - 1, fy - 1, 2, 2, col)
        else:
            G.program_flat(c3, 4, 2, open_=(kind == "open"))
        v.sprite(c3.a, X, Z, anchor=(0.5, 1.0), scale=ROOM_TO_BATTLE)
    pa, pax, pay = podium_sprite()
    v.sprite(pa, 0, Z_STAGE - 20, anchor=(pax, pay), scale=ROOM_TO_BATTLE)
    # chairs either side of the aisle, far rows first
    kinds = [None, None, None, "cap", "programme", "gown", "stole", "bouquet", "seat_programme", "bottle", "sign", None, None]
    for zr in sorted(CHAIR_ROWS, reverse=True):
        for sgn in (-1, 1):
            for j in range(CHAIR_N):
                X = sgn * (CHAIR_X0 + j * CHAIR_DX) + float(rng.integers(-3, 4))
                spr, ax, ay = G.folding_chair(kinds[int(rng.integers(0, len(kinds)))], rng=rng)
                v.sprite(spr.a, X, zr, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(120)

    # crisp 1:1 lettering on the drape: the COMMENCEMENT banner and the seal
    bxl, byt = v.project(0, DRAPE_H - 2, Z_DRAPE)
    lab = "COMMENCEMENT"
    lw = text_width(lab) + 12
    x0, y0 = int(round(bxl)) - lw // 2, int(round(byt)) + 1
    cv.rect(x0 - 1, y0 - 1, lw + 2, 14, G.INK)
    cv.rect(x0, y0, lw, 12, G.GOLD[3]); cv.hline(x0, y0, lw, G.GOLD[4]); cv.hline(x0, y0 + 11, lw, G.GOLD[1])
    text(cv, lab, x0 + 6, y0 - 1, G.BLACK[1])

    solid = v.solid_mask()
    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = solid.astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))

    # --- layer textures ------------------------------------------------------------------------
    strip = Canvas(640, 14)
    r2 = _rng(41)
    for k in range(4):
        x0_ = k * 160 + int(r2.integers(0, 60))
        ln = int(r2.integers(50, 90))
        for j in range(3):
            o = int(r2.integers(-6, 14)) + j * 10
            for xx in range(int(ln * r2.uniform(0.4, 0.8))):
                strip.px((x0_ + o + xx) % 640, 3 + j * 3, C("#f6f2f4", 0.6))
    strip.save(os.path.join(out, "battle-cirrus.png"))

    caps = []
    for x in [24, 296, 352, 412, 586, 628]:
        caps.append((x + int(rng.integers(-8, 9)), int(rng.integers(70, 110)), int(rng.integers(-16, 17)),
                     int(rng.integers(0, 16)), int(rng.integers(0, 4))))
    sprites = [G.mortarboard(t, big=True) for t in range(4)]
    cap_layers = []
    for f in range(16):
        c2 = Canvas(640, 170)
        for (x, apex, drift, phase, tilt) in caps:
            i = (f - phase) % 16
            if i >= 8:
                continue
            t = i / 7.0
            y = 150 - apex * (1 - (2 * t - 1) ** 2) - 6 * t
            c2.paste(sprites[(tilt + i) % 4], int(round(x + drift * t)) - 6, int(round(y)) - 5)
        name = f"battle-caps-{f:02d}.png"
        c2.save(os.path.join(out, name))
        cap_layers.append({"kind": "blink", "pattern": "".join("1" if k == f else "0" for k in range(16)), "rate": 8.0,
                           "texture": res + name, "x": 0, "y": 0})

    # camera flashes in the stands (pixels that are crowd, above the stage)
    flashes = []
    tries = 0
    while len(flashes) < 40 and tries < 4000:
        tries += 1
        x, y = int(rng.integers(0, 640)), int(rng.integers(0, 106))
        if not solid[y, x]:
            continue
        if 200 <= x <= 440 and y > 50:
            continue
        if 392 <= x <= 628 and y <= 70:
            continue
        flashes.append([x, y, "ffffff", 1])

    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "drift", "depth": "far", "texture": res + "battle-cirrus.png", "y": 2, "speed": 2.0, "alpha": 1.0},
            {"kind": "fauna", "depth": "far", "fauna": [{"kind": "bird", "x": 80 + 14 * k, "y": 20 + 4 * (k % 2), "fly": 10.0, "rate": 4.0}
                                                         for k in range(3)]},
            {"kind": "beam", "x": -60, "y": -40, "angle": 38, "sweep": 1.5, "period": 14, "phase": 0.0,
             "length": 420, "width": 90, "color": "fff0d0", "alpha": 0.07, "floor": 900},
            {"kind": "beam", "x": 40, "y": -60, "angle": 52, "sweep": 1.5, "period": 17, "phase": 1.7,
             "length": 380, "width": 60, "color": "fff0d0", "alpha": 0.05, "floor": 900},
            {"kind": "twinkle", "points": flashes, "rate": 3.0, "min": 0.0},
        ] + cap_layers + [
            {"kind": "particles", "style": "dust", "count": 16, "rect": [0, 0, 640, 170], "speed": [3, -10 - 3 * k], "color": col}
            for k, col in enumerate(["f6cf7a", "ffffff", "e88aa0", "7ac0c8", "d8b45a"])
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
