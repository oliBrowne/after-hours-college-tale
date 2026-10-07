#!/usr/bin/env python3
"""Bake each boss's entrance pose to assets/art/entrance/<id>.png for services/boss_intro.gd.

Two sources:
  * a finished sheet:   assets/art/<id>-atlas.json with a cell named "<id>-entrance" (or "entrance": 12)
  * a loose cell:       tools/boss_art/entrances/<id>-entrance.png  (existing bosses, drawn without a sheet)
The file is padded so the foot sits at the bottom centre (width even, height = foot y + 1), which is
where the card places it. Usage: bake_entrance.py [id ...]  (no ids: every id found).
"""
import json, os, sys
from PIL import Image
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "assets", "art")
OUT = os.path.join(ART, "entrance")
LOOSE = os.path.join(ROOT, "tools", "boss_art", "entrances")

def foot_centred(img, fx, fy):
    img = img.crop((0, 0, img.width, int(fy) + 1))          # nothing below the feet
    half = int(max(fx, img.width - fx) + 1)                  # widest side from the foot
    out = Image.new("RGBA", (half * 2, img.height), (0, 0, 0, 0))
    out.paste(img, (half - int(fx), 0))
    return out

def from_sheet(i):
    path = os.path.join(ART, i + "-atlas.json")
    if not os.path.exists(path): return None
    atlas = json.load(open(path)); sheet = Image.open(os.path.join(ART, i + "-v1.png")).convert("RGBA")
    index = atlas.get("entrance")
    if index is None:
        names = [n for n, c in enumerate(atlas["cells"]) if c.get("name") == i + "-entrance"]
        index = names[0] if names else None
    if index is None: return None
    c = atlas["cells"][index]; x, y, w, h = c["rect"]
    return foot_centred(sheet.crop((x, y, x + w, y + h)), *c["foot"])

def from_loose(i):
    p = os.path.join(LOOSE, i + "-entrance.png"); meta = os.path.join(LOOSE, "entrances.json")
    if not os.path.exists(p) or not os.path.exists(meta): return None
    m = json.load(open(meta))[i]; return foot_centred(Image.open(p).convert("RGBA"), *m["foot"])

ids = sys.argv[1:]
if not ids:
    ids = sorted({f[:-len("-atlas.json")] for f in os.listdir(ART) if f.endswith("-atlas.json")}
                 | ({f[:-len("-entrance.png")] for f in os.listdir(LOOSE) if f.endswith("-entrance.png")} if os.path.isdir(LOOSE) else set()))
os.makedirs(OUT, exist_ok=True)
for i in ids:
    img = from_sheet(i) or from_loose(i)
    if img is None: print("skip", i); continue
    img.save(os.path.join(OUT, i + ".png"), optimize=True); print("baked", i, img.size)
