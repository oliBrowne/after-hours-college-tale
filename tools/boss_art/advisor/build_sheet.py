"""Pack Advisor Bev's drawn cells (draw_advisor.py -> cells/) into the game's sheet, like Eric's.

python3 build_sheet.py                 writes out/advisor-v1.png + out/advisor-atlas.json,
                                       out/world/ (hand-drawn 50px world cells + feet.json),
                                       out/talk/advisor-<face>.png, out/idle/advisor-{blink,pose1,pose2}.png
                                       and the 3x contact sheet ../sheet.png
python3 build_sheet.py --bake DUMPDIR  also writes the world cells as native-clean bakes into
                                       out/native-clean/, keyed by the shrunk images the game dumped
                                       (AH_NATIVE_DUMP) when fitting her at world height 50 (same
                                       matching as tools/eric_art/build_sheet.py).

Atlas layout = Eric's plus one cell:
  0-5   82px battle body, 84x92 (0 front, 1 talking, 2 tell, 3 reaction/hit, 4 side facing right, 5 back)
  6-11  64x64 portraits (0 neutral, 1 warm, 2 concern, 3 surprised, 4-5 spares = neutral, warm)
  12    "advisor-entrance", 128x104 intro-card pose (same 82px body scale, foot on the chair column)
She sits in a rolling office chair in every cell; the foot point is the chair column on the floor row.
"""
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = os.path.join(HERE, "cells")
OUTDIR = os.path.join(HERE, "out")
ID = "advisor"
WORLD = 50
BATTLE = 82
CAST = "/tmp/claude-0/designs/cast-reference.png"


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    feet = json.load(open(os.path.join(CELLS, "feet.json")))
    bodies = [Image.open(os.path.join(CELLS, "battle-%d.png" % i)).convert("RGBA") for i in range(6)]
    faces = [Image.open(os.path.join(CELLS, "portrait-%d.png" % i)).convert("RGBA") for i in range(4)]
    faces += [faces[0], faces[1]]
    ent = Image.open(os.path.join(CELLS, "entrance.png")).convert("RGBA")
    pad = 4
    row1 = sum(b.width + pad for b in bodies) + pad
    row2 = sum(f.width + pad for f in faces) + pad + ent.width + pad
    width = max(row1, row2)
    top2 = pad + max(b.height for b in bodies) + pad
    height = top2 + max(64, ent.height) + pad
    sheet = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    cells = []
    x = pad
    for i, b in enumerate(bodies):
        sheet.paste(b, (x, pad))
        fx, fy = feet["battle-%d.png" % i]
        cells.append({"rect": [x, pad, b.width, b.height], "foot": [float(fx), fy], "height": BATTLE})
        x += b.width + pad
    x = pad
    for f in faces:
        sheet.paste(f, (x, top2))
        cells.append({"rect": [x, top2, 64, 64], "foot": [32.0, 63], "height": 64})
        x += 64 + pad
    sheet.paste(ent, (x, top2))
    fx, fy = feet["entrance.png"]
    cells.append({"rect": [x, top2, ent.width, ent.height], "foot": [float(fx), fy], "height": BATTLE,
                  "name": ID + "-entrance"})
    sheet.save(os.path.join(OUTDIR, ID + "-v1.png"))
    with open(os.path.join(OUTDIR, ID + "-atlas.json"), "w", newline="\r\n") as fh:
        fh.write(json.dumps({"path": ID + "-v1.png", "size": [width, height], "cells": cells,
                             "names": {"12": ID + "-entrance"}}) + "\n")
    print("sheet", width, height)
    # world cells, stored like Eric's out/world-N.png + feet (the bake step keys them to game dumps)
    wdir = os.path.join(OUTDIR, "world"); os.makedirs(wdir, exist_ok=True)
    wfeet = {}
    for i in range(6):
        im = Image.open(os.path.join(CELLS, "world-%d.png" % i))
        im.save(os.path.join(wdir, "%s-world-%d.png" % (ID, i)))
        wfeet["%s-world-%d.png" % (ID, i)] = feet["world-%d.png" % i]
    json.dump({"height": WORLD, "battle_height": BATTLE, "feet": wfeet}, open(os.path.join(wdir, "feet.json"), "w"), indent=2)
    # talking portraits + idle extras
    for sub in ("talk", "idle"):
        os.makedirs(os.path.join(OUTDIR, sub), exist_ok=True)
    for i in range(4):
        Image.open(os.path.join(CELLS, "talk-%d.png" % i)).save(os.path.join(OUTDIR, "talk", "%s-%d.png" % (ID, i)))
    for k in ("blink", "pose1", "pose2"):
        Image.open(os.path.join(CELLS, "idle-%s.png" % k)).save(os.path.join(OUTDIR, "idle", "%s-%s.png" % (ID, k)))
    contact_sheet(feet)
    if "--bake" in sys.argv:
        bake(sys.argv[sys.argv.index("--bake") + 1], feet)


def same(a, b):
    pa, pb = a.load(), b.load()
    for y in range(a.height):
        for x in range(a.width):
            ca, cb = pa[x, y], pb[x, y]
            if (ca[3] >= 128) != (cb[3] >= 128): return False
            if ca[3] >= 128 and ca[:3] != cb[:3]: return False
    return True


def bake(dump, feet):
    """Match each dumped shrunk cell to its battle cell by size and pixels, then write the world cell."""
    scale = WORLD / BATTLE
    clean = os.path.join(OUTDIR, "native-clean"); os.makedirs(clean, exist_ok=True)
    done = 0
    for path in sorted(glob.glob(os.path.join(dump, "*.png"))):
        if path.endswith("-src.png"): continue
        src = path[:-4] + "-src.png"
        if not os.path.exists(src): continue
        source = Image.open(src).convert("RGBA")
        if Image.open(path).size == source.size: continue
        for i in range(6):
            cell = Image.open(os.path.join(CELLS, "battle-%d.png" % i)).convert("RGBA")
            if source.size != cell.size or not same(source, cell): continue
            shrunk = Image.open(path)
            fx, fy = feet["battle-%d.png" % i]
            pivot = (round(fx * scale), round(fy * scale))
            world = Image.open(os.path.join(CELLS, "world-%d.png" % i)).convert("RGBA")
            wx, wy = feet["world-%d.png" % i]
            canvas = Image.new("RGBA", shrunk.size, (0, 0, 0, 0))
            canvas.paste(world, (pivot[0] - wx, pivot[1] - wy), world)
            canvas.save(os.path.join(clean, os.path.basename(path)))
            print("baked cell", i, os.path.basename(path), shrunk.size, "pivot", pivot)
            done += 1
    print("baked", done)


def contact_sheet(feet, S=3):
    BG = (44, 44, 62, 255)
    GROUND = (70, 70, 96, 255)
    font = ImageFont.load_default()
    up = lambda im: im.resize((im.width * S, im.height * S), Image.NEAREST)
    cast = Image.open(CAST).convert("RGBA") if os.path.exists(CAST) else None

    def ref(x0, x1, y0, y1):
        """A figure cut from the 3x cast reference (already at sheet scale), trimmed to its pixels."""
        if cast is None: return None
        im = cast.crop((x0, y0, x1, y1))
        px = im.load()
        for yy in range(im.height):
            for xx in range(im.width):
                if px[xx, yy][:3] == BG[:3]: px[xx, yy] = (0, 0, 0, 0)
        bb = im.getbbox()
        return im.crop((bb[0], 0, bb[2], im.height)) if bb else None

    c = lambda n: up(Image.open(os.path.join(CELLS, n)).convert("RGBA"))
    r1 = [(c("battle-%d.png" % i), "battle-%d" % i) for i in range(6)]
    for (x0, x1, lab) in ((20, 225, "ref eric 80"), (1440, 1640, "ref dev 80"), (1680, 1830, "ref jakerson 80")):
        im = ref(x0, x1, 20, 284)
        if im: r1.append((im, lab))
    r2 = [(c("world-%d.png" % i), "world-%d" % i) for i in range(6)]
    r2 += [(c("idle-%s.png" % k), "idle-" + k) for k in ("blink", "pose1", "pose2")]
    for (x0, x1, lab) in ((20, 140, "ref eric"), (990, 1125, "ref jules"), (1225, 1345, "ref imani"), (1400, 1525, "ref dev")):
        im = ref(x0, x1, 300, 496)
        if im: r2.append((im, lab))
    r3 = [(c("portrait-%d.png" % i), "portrait-%d" % i) for i in range(4)]
    r3 += [(c("talk-%d.png" % i), "talk-%d" % i) for i in range(4)]
    r4 = [(c("entrance.png"), "advisor-entrance (cell 12)")]
    im = ref(1030, 1235, 510, 712)
    if im: r4.append((im, "ref jakerson portrait"))
    rows = [(r1, True), (r2, True), (r3, False), (r4, True)]
    pad = 12
    widths = [sum(im.width + pad for im, _ in r) + pad for r, _ in rows]
    heights = [max(im.height for im, _ in r) + 26 for r, _ in rows]
    W, H = max(widths), sum(heights) + pad * 2
    sheet = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    y = pad
    for (r, grounded), rh in zip(rows, heights):
        x = pad
        base = y + rh - 18
        if grounded:
            d.rectangle([0, base, W, base + 1], fill=GROUND)
        for im, label in r:
            top = base - im.height if grounded else y
            sheet.alpha_composite(im, (x, top))
            d.text((x, base + 4), label, fill=(200, 200, 220, 255), font=font)
            x += im.width + pad
        y += rh
    sheet.save(os.path.join(HERE, "sheet.png"))
    print("contact sheet", W, H)


if __name__ == "__main__":
    main()
