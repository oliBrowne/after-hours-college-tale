"""Pack Professor Eric's drawn cells (draw_eric.py -> OUT) into the game's sheet.

python3 build_sheet.py OUT                 writes assets/art/eric-v1.png + eric-atlas.json
python3 build_sheet.py OUT --bake DUMPDIR  also writes the hand-drawn 46px world cells as native-clean
                                           bakes, keyed by the shrunk images the game dumped
                                           (AH_NATIVE_DUMP) when fitting him at world height 46.

Cells 0-5 are the 80px battle body (front, talking, tell, reaction, side facing right, back),
6-9 the 64x64 portraits (neutral, warm, concern, surprised), 10-11 spares (neutral, warm).
The world never resamples his art: the game shrinks the 80px cell to 46px and NativeCleanArt
swaps in the redrawn world cell, aligned on the same foot point.
"""
import glob, json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "..", "..", "assets", "art")
WORLD = 46
BATTLE = 80


def main():
	out = sys.argv[1]
	feet = json.load(open(os.path.join(out, "feet.json")))
	bodies = [Image.open(os.path.join(out, "battle-%d.png" % i)).convert("RGBA") for i in range(6)]
	faces = [Image.open(os.path.join(out, "portrait-%d.png" % i)).convert("RGBA") for i in range(4)]
	faces += [faces[0], faces[1]]
	pad = 4
	width = sum(b.width + pad for b in bodies) + pad
	width = max(width, sum(f.width + pad for f in faces) + pad)
	height = pad + max(b.height for b in bodies) + pad + 64 + pad
	sheet = Image.new("RGBA", (width, height), (0, 0, 0, 0))
	cells = []
	x = pad
	for i, b in enumerate(bodies):
		sheet.paste(b, (x, pad))
		fx, fy = feet["battle-%d.png" % i]
		cells.append({"rect": [x, pad, b.width, b.height], "foot": [float(fx), fy], "height": BATTLE})
		x += b.width + pad
	x = pad; top = pad + max(b.height for b in bodies) + pad
	for f in faces:
		sheet.paste(f, (x, top))
		cells.append({"rect": [x, top, 64, 64], "foot": [32.0, 63], "height": 64})
		x += 64 + pad
	sheet.save(os.path.join(ART, "eric-v1.png"))
	with open(os.path.join(ART, "eric-atlas.json"), "w", newline="\r\n") as fh:
		fh.write(json.dumps({"path": "eric-v1.png", "size": [width, height], "cells": cells}) + "\n")
	print("sheet", width, height)
	if "--bake" in sys.argv:
		bake(out, sys.argv[sys.argv.index("--bake") + 1], feet)


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
	clean = os.path.join(ART, "native-clean")
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
			canvas.alpha_composite(world, (pivot[0] - wx, pivot[1] - wy)) if pivot[0] >= wx and pivot[1] >= wy else canvas.paste(world, (pivot[0] - wx, pivot[1] - wy), world)
			canvas.save(os.path.join(clean, os.path.basename(path)))
			print("baked cell", i, os.path.basename(path), shrunk.size, "pivot", pivot)
			done += 1
	print("baked", done)


if __name__ == "__main__":
	main()
