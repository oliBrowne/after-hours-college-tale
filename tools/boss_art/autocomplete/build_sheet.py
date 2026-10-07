"""Pack AUTOCOMPLETE's drawn cells (draw_autocomplete.py -> cells/) into the game's sheet layout.

python3 build_sheet.py cells                 writes out/autocomplete-v1.png + out/autocomplete-atlas.json,
                                             out/world/ (world cells + world-feet.json), out/talk/, out/idle/
                                             and the 3x contact sheet ../sheet.png
python3 build_sheet.py cells --bake DUMPDIR  also writes the hand-drawn 60px world cells as native-clean
                                             bakes into out/native-clean/, keyed by the shrunk images the
                                             game dumped (AH_NATIVE_DUMP) when fitting it at world height 60
                                             (the same mechanism as Professor Eric's build_sheet.py).

Layout = Professor Eric's (eric-atlas.json) plus an entrance cell:
cells 0-5 are the 88px battle body (0 front, 1 talking, 2 tell, 3 hit, 4 side facing right, 5 back),
6-9 the 64x64 portraits (neutral, warm, concern, surprised), 10-11 spares (neutral, warm),
12 "autocomplete-entrance" (136x112, 104px tall) for the gym-leader intro card.
It never walks: the world uses cells 0/4/5 for idle_down/right/up like Eric with no walk entry.
Nothing here writes into a game folder.
"""
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
ID = "autocomplete"
WORLD = 60
BATTLE = 88
ENTRANCE = 104
REF = "/tmp/claude-0/eric/ref"
ERIC = "/tmp/claude-0/eric/out"
INDEX_WORLD = "/tmp/claude-0/anim/in/world/index_idle_down_0_30_58.png"


def main():
	cells = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "cells")
	os.makedirs(OUT, exist_ok=True)
	feet = json.load(open(os.path.join(cells, "feet.json")))
	bodies = [Image.open(os.path.join(cells, "battle-%d.png" % i)).convert("RGBA") for i in range(6)]
	faces = [Image.open(os.path.join(cells, "portrait-%d.png" % i)).convert("RGBA") for i in range(4)]
	faces += [faces[0], faces[1]]
	ent = Image.open(os.path.join(cells, "battle-12.png")).convert("RGBA")
	pad = 4
	left = max(sum(b.width + pad for b in bodies), sum(f.width + pad for f in faces)) + pad
	width = left + ent.width + pad
	height = max(pad + max(b.height for b in bodies) + pad + 64 + pad, pad + ent.height + pad)
	sheet = Image.new("RGBA", (width, height), (0, 0, 0, 0))
	out_cells = []
	x = pad
	for i, b in enumerate(bodies):
		sheet.paste(b, (x, pad))
		fx, fy = feet["battle-%d.png" % i]
		out_cells.append({"rect": [x, pad, b.width, b.height], "foot": [float(fx), fy], "height": BATTLE})
		x += b.width + pad
	x = pad; top = pad + max(b.height for b in bodies) + pad
	for f in faces:
		sheet.paste(f, (x, top))
		out_cells.append({"rect": [x, top, 64, 64], "foot": [32.0, 63], "height": 64})
		x += 64 + pad
	sheet.paste(ent, (left, pad))
	fx, fy = feet["battle-12.png"]
	out_cells.append({"rect": [left, pad, ent.width, ent.height], "foot": [float(fx), fy], "height": ENTRANCE,
		"name": ID + "-entrance"})
	sheet.save(os.path.join(OUT, ID + "-v1.png"))
	with open(os.path.join(OUT, ID + "-atlas.json"), "w", newline="\r\n") as fh:
		fh.write(json.dumps({"path": ID + "-v1.png", "size": [width, height], "cells": out_cells}) + "\n")
	print("sheet", width, height)
	# world cells (drawn at 60px, swapped in over the shrunk battle cells like Eric's)
	wdir = os.path.join(OUT, "world"); os.makedirs(wdir, exist_ok=True)
	wfeet = {}
	for i in range(6):
		n = "world-%d.png" % i
		Image.open(os.path.join(cells, n)).save(os.path.join(wdir, "%s-world-%d.png" % (ID, i)))
		wfeet["%s-world-%d.png" % (ID, i)] = feet[n]
	json.dump({"height": WORLD, "battle_height": BATTLE, "feet": wfeet}, open(os.path.join(wdir, "world-feet.json"), "w"), indent=2)
	# talking portraits and idle extras
	tdir = os.path.join(OUT, "talk"); os.makedirs(tdir, exist_ok=True)
	for i in range(4):
		Image.open(os.path.join(cells, "talk-%d.png" % i)).save(os.path.join(tdir, "%s-%d.png" % (ID, i)))
	idir = os.path.join(OUT, "idle"); os.makedirs(idir, exist_ok=True)
	for k in ("blink", "pose1", "pose2"):
		Image.open(os.path.join(cells, "idle-%s.png" % k)).save(os.path.join(idir, "%s-%s.png" % (ID, k)))
	contact_sheet(cells)
	if "--bake" in sys.argv:
		bake(cells, sys.argv[sys.argv.index("--bake") + 1], feet)


def same(a, b):
	pa, pb = a.load(), b.load()
	for y in range(a.height):
		for x in range(a.width):
			ca, cb = pa[x, y], pb[x, y]
			if (ca[3] >= 128) != (cb[3] >= 128): return False
			if ca[3] >= 128 and ca[:3] != cb[:3]: return False
	return True


def bake(cells, dump, feet):
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
			cell = Image.open(os.path.join(cells, "battle-%d.png" % i)).convert("RGBA")
			if source.size != cell.size or not same(source, cell): continue
			shrunk = Image.open(path)
			fx, fy = feet["battle-%d.png" % i]
			pivot = (round(fx * scale), round(fy * scale))
			world = Image.open(os.path.join(cells, "world-%d.png" % i)).convert("RGBA")
			wx, wy = feet["world-%d.png" % i]
			canvas = Image.new("RGBA", shrunk.size, (0, 0, 0, 0))
			canvas.paste(world, (pivot[0] - wx, pivot[1] - wy), world)
			canvas.save(os.path.join(clean, os.path.basename(path)))
			print("baked cell", i, os.path.basename(path), shrunk.size, "pivot", pivot)
			done += 1
	print("baked", done)


def contact_sheet(cells, S=3):
	BG = (44, 44, 62, 255)
	GROUND = (70, 70, 96, 255)
	font = ImageFont.load_default()

	def img(p):
		return Image.open(p).convert("RGBA") if os.path.exists(p) else None

	def grounded(im):
		bb = im.getbbox()
		return im.crop((0, 0, im.width, bb[3]))

	r1 = [(img(os.path.join(cells, "battle-%d.png" % i)), "battle-%d" % i) for i in range(6)]
	r1.append((img(os.path.join(cells, "battle-12.png")), "12 entrance"))
	for p, label in ((os.path.join(ERIC, "battle-0.png"), "ref eric 80"), (os.path.join(REF, "dev_80_idle_down.png"), "ref dev 80"),
			(os.path.join(REF, "jakerson_80_idle_down.png"), "ref jakerson 80")):
		im = img(p)
		if im: r1.append((grounded(im), label))
	r2 = [(img(os.path.join(cells, "world-%d.png" % i)), "world-%d" % i) for i in range(6)]
	r2 += [(img(os.path.join(cells, "idle-%s.png" % k)), "idle " + k) for k in ("blink", "pose1", "pose2")]
	for p, label in ((INDEX_WORLD, "old INDEX"), (os.path.join(ERIC, "world-0.png"), "ref eric"),
			(os.path.join(REF, "jules_idle_down_0_37_61.png"), "ref jules"), (os.path.join(REF, "imani_idle_down_0_36_55.png"), "ref imani")):
		im = img(p)
		if im: r2.append((grounded(im), label))
	r3 = [(img(os.path.join(cells, "portrait-%d.png" % i)), "portrait-%d" % i) for i in range(4)]
	r3 += [(img(os.path.join(cells, "talk-%d.png" % i)), "talk-%d" % i) for i in range(4)]
	im = img(os.path.join(REF, "jakerson_portrait_0.png"))
	if im: r3.append((im.resize((64, 64), Image.NEAREST), "ref jakerson"))
	rows = [r1, r2, r3]
	pad = 12
	widths = [sum(im.width * S + pad for im, _ in r) + pad for r in rows]
	heights = [max(im.height * S for im, _ in r) + 26 for r in rows]
	W, H = max(widths), sum(heights) + pad * 2
	sheet = Image.new("RGBA", (W, H), BG)
	d = ImageDraw.Draw(sheet)
	y = pad
	for r, rh in zip(rows, heights):
		x = pad
		base = y + rh - 18
		if r is not r3:
			d.rectangle([0, base, W, base + 1], fill=GROUND)
		for im, label in r:
			big = im.resize((im.width * S, im.height * S), Image.NEAREST)
			top = base - big.height if r is not r3 else y
			sheet.alpha_composite(big, (x, top))
			d.text((x, base + 4), label, fill=(200, 200, 220, 255), font=font)
			x += big.width + pad
		y += rh
	sheet.save(os.path.join(HERE, "sheet.png"))
	print("contact sheet", W, H)


if __name__ == "__main__":
	main()
