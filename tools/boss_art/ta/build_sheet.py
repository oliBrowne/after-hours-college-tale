"""Pack Gwen the Red's drawn cells (draw_ta.py -> out/) into the game's sheet, in Professor Eric's layout.

python3 build_sheet.py [OUT]                 writes OUT/ta-v1.png + OUT/ta-atlas.json, and the world cells
                                             as OUT/world/ta-world-0..5.png + OUT/world/ta-world.json
python3 build_sheet.py [OUT] --bake DUMPDIR  also writes the hand-drawn 52px world cells as native-clean bakes
                                             into OUT/native-clean/, keyed by the shrunk images the game dumps
                                             (AH_NATIVE_DUMP) when fitting her at world height 52 -- exactly
                                             what Eric's build_sheet.py does for assets/art/native-clean.

Cells 0-5 are the 82px battle body (front, talking, tell, reaction, side facing right, back),
6-9 the 64x64 portraits (neutral, warm, concern, surprised), 10-11 spares (neutral, warm), and
12 "ta-entrance", the gym-leader intro-card pose on a wider canvas (its pen rises above her head).
The world never resamples her art: the game shrinks the 82px cell to 52px and NativeCleanArt swaps in
the redrawn world cell, aligned on the same foot point.
Nothing here writes into the game folder; copy OUT/ta-v1.png + ta-atlas.json into assets/art/ to ship.
"""
import glob, json, os, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = 52
BATTLE = 82


def main():
	args = [a for a in sys.argv[1:]]
	out = args[0] if args and not args[0].startswith("--") else os.path.join(HERE, "out")
	feet = json.load(open(os.path.join(out, "feet.json")))
	bodies = [Image.open(os.path.join(out, "battle-%d.png" % i)).convert("RGBA") for i in range(6)]
	faces = [Image.open(os.path.join(out, "portrait-%d.png" % i)).convert("RGBA") for i in range(4)]
	faces += [faces[0], faces[1]]
	entrance = Image.open(os.path.join(out, "entrance.png")).convert("RGBA")
	pad = 4
	width = sum(b.width + pad for b in bodies) + pad
	width = max(width, sum(f.width + pad for f in faces) + pad, entrance.width + 2 * pad)
	row2 = pad + max(b.height for b in bodies) + pad
	row3 = row2 + 64 + pad
	height = row3 + entrance.height + pad
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
		sheet.paste(f, (x, row2))
		cells.append({"rect": [x, row2, 64, 64], "foot": [32.0, 63], "height": 64})
		x += 64 + pad
	sheet.paste(entrance, (pad, row3))
	fx, fy = feet["entrance.png"]
	cells.append({"rect": [pad, row3, entrance.width, entrance.height], "foot": [float(fx), fy], "height": BATTLE,
	              "name": "ta-entrance"})
	sheet.save(os.path.join(out, "ta-v1.png"))
	with open(os.path.join(out, "ta-atlas.json"), "w", newline="\r\n") as fh:
		fh.write(json.dumps({"path": "ta-v1.png", "size": [width, height], "cells": cells, "entrance": 12}) + "\n")
	print("sheet", width, height)
	# world cells, stored beside the sheet with their foot points (the bake source)
	wdir = os.path.join(out, "world")
	os.makedirs(wdir, exist_ok=True)
	world = {}
	for i in range(6):
		shutil.copyfile(os.path.join(out, "world-%d.png" % i), os.path.join(wdir, "ta-world-%d.png" % i))
		im = Image.open(os.path.join(out, "world-%d.png" % i))
		world["ta-world-%d.png" % i] = {"size": list(im.size), "foot": feet["world-%d.png" % i], "height": WORLD,
		                               "battle_cell": i}
	with open(os.path.join(wdir, "ta-world.json"), "w", newline="\r\n") as fh:
		fh.write(json.dumps({"world_height": WORLD, "battle_height": BATTLE, "cells": world}, indent=1) + "\n")
	print("world cells", len(world))
	if "--bake" in args:
		bake(out, args[args.index("--bake") + 1], feet)


def same(a, b):
	"""Same drawing: identical opaque pixels (import may change the colour under transparent ones)."""
	pa, pb = a.load(), b.load()
	for y in range(a.height):
		for x in range(a.width):
			ca, cb = pa[x, y], pb[x, y]
			if (ca[3] >= 128) != (cb[3] >= 128): return False
			if ca[3] >= 128 and ca[:3] != cb[:3]: return False
	return True


def bake(out, dump, feet):
	"""Match each dumped shrunk cell to its battle cell by size and pivot, then write the world cell."""
	scale = WORLD / BATTLE
	clean = os.path.join(out, "native-clean")
	os.makedirs(clean, exist_ok=True)
	done = 0
	for path in sorted(glob.glob(os.path.join(dump, "*.png"))):
		if path.endswith("-src.png"): continue
		src = path[:-4] + "-src.png"
		if not os.path.exists(src): continue
		source = Image.open(src).convert("RGBA")
		if Image.open(path).size == source.size: continue  # the battle size is drawn 1:1, nothing to swap
		for i in range(6):
			cell = Image.open(os.path.join(out, "battle-%d.png" % i)).convert("RGBA")
			if source.size != cell.size or not same(source, cell): continue
			shrunk = Image.open(path)
			fx, fy = feet["battle-%d.png" % i]
			pivot = (round(fx * scale), round(fy * scale))
			world = Image.open(os.path.join(out, "world-%d.png" % i)).convert("RGBA")
			wx, wy = feet["world-%d.png" % i]
			canvas = Image.new("RGBA", shrunk.size, (0, 0, 0, 0))
			canvas.paste(world, (pivot[0] - wx, pivot[1] - wy), world)
			canvas.save(os.path.join(clean, os.path.basename(path)))
			print("baked cell", i, os.path.basename(path), shrunk.size, "pivot", pivot)
			done += 1
	print("baked", done)


if __name__ == "__main__":
	main()
