"""Offline previews (no Godot needed).

    python3 preview.py room   <ID> <out.png> [flag=value ...]   whole room at 2x, dusk tint, scale markers
    python3 preview.py battle <ID> <out.png> [dawn]              battle backdrop at 2x under the battle UI

Room previews composite the background, state overlays, animals and every placement's painted
prop in y order (like the game), then apply the world's dusk tint (0.68, 0.72, 0.84). Grey
outlined boxes mark placements that still use the old procedural drawing; small cyan figures
52px tall show character scale at a few floor points; a small yellow box marks a keepsake spot. Battle previews put the real battle UI
(command menu and fighters, captured in game) over the backdrop. Animated layers are shown as one still
(drift strips, blink textures and rects, twinkle points); beams, particles, movers and fauna are left out.
"""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from fauna import fauna_sheet

PROJECT = os.environ.get("AH_PROJECT", paths.PROJECT)
HERE = os.path.dirname(os.path.abspath(__file__))
DUSK = (0.68, 0.72, 0.84)
DAWN = (0.90, 0.88, 0.87)
# Keepsake pickups (core/party_growth.gd): keep these floor spots clear.
KEEPSAKES = {"U01": (52, 204), "U04": (60, 320), "U05": (580, 264), "U07": (60, 322), "F03": (748, 302),
             "F05": (748, 294), "N03": (60, 334), "N05": (60, 318), "E02": (748, 326)}


def load(res):
    return np.array(Image.open(res.replace("res://", PROJECT + "/")).convert("RGBA")).astype(np.float32) / 255


def over(dst, src, x, y):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4]
    dst[y0:y1, x0:x1, :3] = s[..., :3] * a + dst[y0:y1, x0:x1, :3] * (1 - a)


def shows(o, flags):
    v = flags.get(o["flag"])
    if "equals" in o:
        return str(v) == str(o["equals"])
    on = v not in (None, False, "", "false")
    return on == bool(o.get("when", True))


def box(img, x, y, w, h, c):
    H, W = img.shape[:2]
    for (xx, yy, ww, hh) in [(x, y, w, 1), (x, y + h - 1, w, 1), (x, y, 1, h), (x + w - 1, y, 1, h)]:
        x0, y0, x1, y1 = max(0, xx), max(0, yy), min(W, xx + ww), min(H, yy + hh)
        if x0 < x1 and y0 < y1:
            img[y0:y1, x0:x1, :3] = c


def compose(room, view=None, flags=None, markers=True, tint=True):
    flags = flags or {}
    m = json.load(open(f"{PROJECT}/assets/art/rooms/{room}/manifest.json"))
    rooms = json.load(open(f"{PROJECT}/content/rooms.json"))
    layout = rooms[room]
    placements = layout["placements"]
    dawn = flags.get("dawn_started") and "background_dawn" in m
    img = load(m["background_dawn" if dawn else "background"]).copy()
    for o in m.get("overlays", []):
        if shows(o, flags):
            over(img, load(o["texture"]), int(o["x"]), int(o["y"]))
    sheet, regions = fauna_sheet()
    for f in m.get("fauna", []):
        rx, ry, rw, rh, n = regions[f["kind"]]
        spr = sheet.a[ry:ry + rh, rx:rx + rw]
        if f.get("flip"):
            spr = spr[:, ::-1]
        over(img, spr, int(f["x"]) - rw // 2, int(f["y"]) - rh)
    items = []
    painted = set(int(k) for k in m.get("props", {}))
    for key, p in m.get("props", {}).items():
        pl = dict(placements[int(key)])
        if "base_x" in pl:
            pl["x"] = pl["base_x"] + (pl.get("shift_x", 0) if flags.get("stacks_shifted") else 0)
        tex = p["texture"]
        if p.get("flag") and flags.get(p["flag"]):
            tex = p["flag_texture"]
        items.append((pl["y"], load(tex), int(pl["x"] - p["anchor"][0]), int(pl["y"] - p["anchor"][1])))
    for o in m.get("occluders", []):
        items.append((o["base"], load(o["texture"]), o["x"], o["y"]))
    for _, spr, x, y in sorted(items, key=lambda t: t[0]):
        over(img, spr, x, y)
    static_layers(img, [l for l in m.get("layers", []) if "flag" not in l or shows(l, flags)])
    if tint:
        img[..., :3] *= np.array(DAWN if flags.get("dawn_started") else DUSK)
    if markers:
        label_only = set(int(i) for i in m.get("label_only", []))
        for i, pl in enumerate(placements):
            if i in painted or i in label_only or pl["kind"] == "threshold":
                continue
            w, h = int(pl.get("w", 30)), int(pl.get("h", 30))
            box(img, int(pl["x"] - w / 2), int(pl["y"] - h), w, h, (0.6, 0.6, 0.6))
        if room in KEEPSAKES:
            kx, ky = KEEPSAKES[room]
            box(img, kx - 8, ky - 12, 16, 12, (1.0, 0.85, 0.2))
        wb = layout.get("walk_bounds", [20, 140, 600, 200])
        for fx in np.linspace(wb[0] + 40, wb[0] + wb[2] - 40, 4):
            for fy in (wb[1] + 2, wb[1] + wb[3] - 10):
                box(img, int(fx) - 9, int(fy) - 52, 18, 52, (0.3, 0.9, 0.95))
    if view is None:
        return img
    vx, vy = view
    return img[vy:vy + 360, vx:vx + 640]


def static_layers(img, layers):
    """A still of the animated layers: drift strips at x 0, blink textures and rects, twinkle points lit."""
    for l in layers:
        if l["kind"] == "drift":
            tex = load(l["texture"])
            for x in range(0, img.shape[1], tex.shape[1]):
                over(img, tex * np.array([1, 1, 1, l.get("alpha", 1.0)], np.float32), x, int(l.get("y", 0)))
        elif l["kind"] == "blink":
            if "texture" in l:
                over(img, load(l["texture"]), int(l.get("x", 0)), int(l.get("y", 0)))
            for r in l.get("rects", []):
                c = np.array([int(r[4][i:i + 2], 16) / 255 for i in (0, 2, 4)] + [r[5] if len(r) > 5 else 1.0], np.float32)
                over(img, np.broadcast_to(c, (int(r[3]), int(r[2]), 4)).copy(), int(r[0]), int(r[1]))
        elif l["kind"] == "twinkle":
            for p in l.get("points", []):
                c = np.array([int(p[2][i:i + 2], 16) / 255 for i in (0, 2, 4)] + [1.0], np.float32)
                over(img, c.reshape(1, 1, 4), int(p[0]), int(p[1]))


def battle(room, dawn=False, ui="menu"):
    m = json.load(open(f"{PROJECT}/assets/art/rooms/{room}/manifest.json"))
    spec = m["battle"]
    far = spec.get("far_dawn", spec["far"]) if dawn else spec["far"]
    img = load(far).copy()
    static_layers(img, [l for l in spec.get("layers", []) if l.get("depth", "near") == "far"])
    near = spec.get("near_dawn", spec.get("near")) if dawn else spec.get("near")
    if near:
        over(img, load(near), 0, 0)
    static_layers(img, [l for l in spec.get("layers", []) if l.get("depth", "near") == "near"])
    overlay = np.array(Image.open(f"{HERE}/ui-overlay-{ui}.png").convert("RGBA")).astype(np.float32) / 255
    over(img, overlay, 0, 0)
    return img


def save2x(img, path):
    h, w = img.shape[:2]
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)[..., :3]).resize((w * 2, h * 2), 0).save(path)


if __name__ == "__main__":
    mode, room, out = sys.argv[1], sys.argv[2], sys.argv[3]
    extra = sys.argv[4:]
    if mode == "room":
        flags = {}
        for e in extra:
            k, _, v = e.partition("=")
            flags[k] = True if v in ("", "true") else False if v == "false" else v
        save2x(compose(room, flags=flags), out)
    else:
        save2x(battle(room, dawn="dawn" in extra, ui="dodge" if "dodge" in extra else "menu"), out)
    print(out)
