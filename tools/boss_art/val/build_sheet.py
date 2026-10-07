"""Pack Val's drawn cells (draw_val.py -> out/cells) into the game's sheet, like Eric's build_sheet.py.

python3 build_sheet.py                    writes out/val-v1.png + out/val-atlas.json, out/world/*, out/val-screens.png
python3 build_sheet.py --bake DUMPDIR     also writes the hand-drawn 54px world cells as native-clean
                                          bakes (out/native-clean/), keyed by the shrunk images the game
                                          dumped (AH_NATIVE_DUMP) when fitting her at world height 54.

Atlas layout = Eric's layout plus one cell:
  0-5   84px battle body (front, talking, tell, reaction/hit, side facing right, back)
  6-9   64x64 portraits (neutral, warm, concern, surprised), 10-11 spares (neutral, warm)
  12    "val-entrance": intro-card pose on the Macky stage lift through dry ice (128x120)
talk/val-<face>.png and idle/val-{blink,pose1,pose2}.png are written by draw_val.py next to the sheet.
The world never resamples her art: the game shrinks the 84px cell to 54px and NativeCleanArt
swaps in the redrawn world cell, aligned on the same foot point.
"""
import glob, json, os, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
CELLS = os.path.join(OUT, "cells")
WORLD = 54
BATTLE = 84


def main():
	feet = json.load(open(os.path.join(CELLS, "feet.json")))
	bodies = [Image.open(os.path.join(CELLS, "battle-%d.png" % i)).convert("RGBA") for i in range(6)]
	faces = [Image.open(os.path.join(CELLS, "portrait-%d.png" % i)).convert("RGBA") for i in range(4)]
	faces += [faces[0], faces[1]]
	entrance = Image.open(os.path.join(CELLS, "entrance.png")).convert("RGBA")
	pad = 4
	width = sum(b.width + pad for b in bodies) + pad
	width = max(width, sum(f.width + pad for f in faces) + pad, entrance.width + 2 * pad)
	top2 = pad + max(b.height for b in bodies) + pad
	top3 = top2 + 64 + pad
	height = top3 + entrance.height + pad
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
	fx, fy = feet["entrance.png"]
	sheet.paste(entrance, (pad, top3))
	cells.append({"rect": [pad, top3, entrance.width, entrance.height], "foot": [float(fx), fy],
	              "height": feet["entrance-height"], "name": "val-entrance"})
	sheet.save(os.path.join(OUT, "val-v1.png"))
	with open(os.path.join(OUT, "val-atlas.json"), "w", newline="\r\n") as fh:
		fh.write(json.dumps({"path": "val-v1.png", "size": [width, height], "cells": cells}) + "\n")
	print("sheet", width, height)
	# world cells (redrawn at 54px, never scaled) + their feet, stored beside the sheet
	wdir = os.path.join(OUT, "world")
	os.makedirs(wdir, exist_ok=True)
	wfeet = {}
	for i in range(6):
		shutil.copy(os.path.join(CELLS, "world-%d.png" % i), os.path.join(wdir, "val-world-%d.png" % i))
		wfeet["val-world-%d.png" % i] = feet["world-%d.png" % i]
	with open(os.path.join(wdir, "feet.json"), "w") as fh:
		json.dump(wfeet, fh, indent=2)
	shutil.copy(os.path.join(CELLS, "screens.png"), os.path.join(OUT, "val-screens.png"))
	if "--bake" in sys.argv:
		bake(sys.argv[sys.argv.index("--bake") + 1], feet)


def same(a, b):
	"""Same drawing: identical opaque pixels (import may change the colour under transparent ones)."""
	pa, pb = a.load(), b.load()
	for y in range(a.height):
		for x in range(a.width):
			ca, cb = pa[x, y], pb[x, y]
			if (ca[3] >= 128) != (cb[3] >= 128): return False
			if ca[3] >= 128 and ca[:3] != cb[:3]: return False
	return True


def bake(dump, feet):
	"""Match each dumped shrunk cell to its battle cell by size and pixels, then write the world cell
	into out/native-clean/ under the dump's own name (copy those into assets/art/native-clean/)."""
	scale = WORLD / BATTLE
	clean = os.path.join(OUT, "native-clean")
	os.makedirs(clean, exist_ok=True)
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


if __name__ == "__main__":
	main()
