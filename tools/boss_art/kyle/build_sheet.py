"""Pack Kyle's drawn cells (draw_kyle.py -> ./cells) into the game's sheet layout, like Eric's.

python3 build_sheet.py                  writes out/kyle-v1.png + out/kyle-atlas.json, out/world/ (the
                                        hand-drawn 52px world cells + feet.json), out/talk/, out/idle/,
                                        and the battle-only prop out/kyle-deck.png + kyle-deck.json
python3 build_sheet.py --bake DUMPDIR   also writes the world cells as native-clean bakes into
                                        out/native-clean/, keyed by the shrunk images the game dumped
                                        (AH_NATIVE_DUMP) when fitting him at world height 52 -- exactly
                                        how Eric's world cells reach assets/art/native-clean/.

Cells 0-5 are the battle body riding the scooter (front, talking, tell, reaction/hit, side facing
right, back), 6-9 the 64x64 portraits (neutral, warm, concern, surprised), 10-11 spares (neutral,
warm), and cell 12 "kyle-entrance", the intro-card scooter manual on a wider canvas (third row).
Battle height 84 = hair top to wheel contact (he stands 78 on the 6px deck); the foot point is the
tyre contact.  Props such as the raised clicker and its laser sit outside it on the 92x92 canvas.
World cells (52 = hair top to soles) show him standing in front of the parked scooter.
kyle-deck.png is the projected pitch deck, drawn BEHIND him in battle only; its json "anchor" is
his battle foot point inside that image.
"""
import glob, json, os, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = os.path.join(HERE, "cells")
OUT = os.path.join(HERE, "out")
ID = "kyle"
WORLD = 52
BATTLE = 84


def main():
	feet = json.load(open(os.path.join(CELLS, "feet.json")))
	bodies = [Image.open(os.path.join(CELLS, "battle-%d.png" % i)).convert("RGBA") for i in range(6)]
	faces = [Image.open(os.path.join(CELLS, "portrait-%d.png" % i)).convert("RGBA") for i in range(4)]
	faces += [faces[0], faces[1]]
	entrance = Image.open(os.path.join(CELLS, "entrance.png")).convert("RGBA")
	pad = 4
	width = max(sum(b.width + pad for b in bodies) + pad, sum(f.width + pad for f in faces) + pad, entrance.width + 2 * pad)
	bh = max(b.height for b in bodies)
	height = pad + bh + pad + 64 + pad + entrance.height + pad
	sheet = Image.new("RGBA", (width, height), (0, 0, 0, 0))
	cells = []
	names = ["front", "talk", "tell", "reaction", "side", "back"]
	x = pad
	for i, b in enumerate(bodies):
		sheet.paste(b, (x, pad))
		fx, fy = feet["battle-%d.png" % i]
		cells.append({"name": "%s-%s" % (ID, names[i]), "rect": [x, pad, b.width, b.height], "foot": [float(fx), fy], "height": BATTLE})
		x += b.width + pad
	x = pad; top = pad + bh + pad
	for i, f in enumerate(faces):
		sheet.paste(f, (x, top))
		face = ["neutral", "warm", "concern", "surprised", "neutral", "warm"][i]
		cells.append({"name": "%s-face-%s" % (ID, face), "rect": [x, top, 64, 64], "foot": [32.0, 63], "height": 64})
		x += 64 + pad
	top += 64 + pad
	sheet.paste(entrance, (pad, top))
	fx, fy = feet["entrance.png"]
	cells.append({"name": "%s-entrance" % ID, "rect": [pad, top, entrance.width, entrance.height], "foot": [float(fx), fy], "height": BATTLE})
	os.makedirs(OUT, exist_ok=True)
	sheet.save(os.path.join(OUT, "%s-v1.png" % ID))
	with open(os.path.join(OUT, "%s-atlas.json" % ID), "w", newline="\r\n") as fh:
		fh.write(json.dumps({"path": "%s-v1.png" % ID, "size": [width, height], "cells": cells}) + "\n")
	print("sheet", width, height, "cells", len(cells))
	# world cells, stored the way Eric's are before baking: drawn cells + their foot points
	wdir = os.path.join(OUT, "world"); os.makedirs(wdir, exist_ok=True)
	wfeet = {}
	for i in range(6):
		shutil.copy(os.path.join(CELLS, "world-%d.png" % i), os.path.join(wdir, "world-%d.png" % i))
		wfeet["world-%d.png" % i] = feet["world-%d.png" % i]
	with open(os.path.join(wdir, "feet.json"), "w") as fh:
		json.dump(wfeet, fh, indent=2)
	for sub, pattern in (("talk", "%s-*.png" % ID), ("idle", "%s-*.png" % ID)):
		os.makedirs(os.path.join(OUT, sub), exist_ok=True)
		for p in sorted(glob.glob(os.path.join(CELLS, sub, pattern))):
			shutil.copy(p, os.path.join(OUT, sub, os.path.basename(p)))
	for f in ("%s-deck.png" % ID, "%s-deck.json" % ID):
		shutil.copy(os.path.join(CELLS, f), os.path.join(OUT, f))
	print("world, talk, idle and the deck prop copied")
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
	"""Match each dumped shrunk cell to its battle cell by size and pivot, then write the world cell."""
	scale = WORLD / BATTLE
	clean = os.path.join(OUT, "native-clean"); os.makedirs(clean, exist_ok=True)
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
