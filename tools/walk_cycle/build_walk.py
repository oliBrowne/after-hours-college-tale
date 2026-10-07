"""Walk cycles for the world sprites.

The generated side-view walks held one wide stride in every frame, so the legs never passed each
other and the body never rose or dipped: walkers slid across the floor. This redraws the legs
below the hip at native size with a real eight-frame cycle (contact, passing, contact, passing),
keeps everything above the hip exactly as drawn, and lifts the upper body one pixel on the passing
frames. Front and back views keep their drawn legs and get the same one-pixel bob; Jakerson, whose
only pose per direction is standing, gets a lifted-foot step for front and back.

python3 build_walk.py [OUT]   reads src/ (the native frames the game draws, dumped from the build)
and writes OUT (default ../../assets/art/walk) as one strip per actor and direction plus walk.json.
"""
import glob, json, math, os, re, sys
from collections import Counter
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "assets", "art", "walk")
INK = (18, 15, 30, 255)
FRAMES = 8
PALETTES = {  # one trouser/shoe palette per actor, sampled from the first side view built
	# Eric's probe cable crosses his legs and would win the sample, so his khakis are set here.
	"eric": dict(base=(182, 164, 118, 255), shade=(150, 130, 90, 255), shoe=(154, 104, 62, 255), shoe_dark=(116, 72, 44, 255)),
}

# Per actor: leg length above the last filled row (hip), stride half-width, leg widths, shoe size.
SIDE = {
	"jules": dict(hip=10, stride=6, thigh=6, shin=5, shoe=(7, 3)),
	"imani": dict(hip=8, stride=6, thigh=6, shin=5, shoe=(7, 3)),
	"walt": dict(hip=7, stride=4, thigh=6, shin=5, shoe=(8, 3)),
	"jak": dict(hip=21, stride=7, thigh=6, shin=5, shoe=(8, 3)),
	"jaktennis": dict(hip=21, stride=7, thigh=6, shin=5, shoe=(8, 3)),
	"eric": dict(hip=9, stride=4, thigh=7, shin=6, shoe=(6, 3)),
}


def load(actor, anim, index):
	path = glob.glob(os.path.join(SRC, "%s_%s_%d_*.png" % (actor, anim, index)))[0]
	fx, fy = map(int, re.search(r"_(\d+)_(\d+)\.png$", path).groups())
	return Image.open(path).convert("RGBA"), (fx, fy)


def opaque(p):
	return p[3] >= 128


def ground_row(im):
	"""Last filled row above the bottom ink line."""
	return im.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()[3] - 2


def luminance(c):
	return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def palette(im, hip, ground):
	"""Trouser and shoe colours sampled from the drawn legs."""
	legs = Counter(); shoes = Counter()
	for y in range(hip, ground + 1):
		for x in range(im.width):
			p = im.getpixel((x, y))
			if not opaque(p) or p[:3] == INK[:3]: continue
			(shoes if y >= ground - 2 else legs)[p[:3]] += 1
	trouser = [c for c, _ in legs.most_common(4)]
	base = trouser[0]
	shade = min(trouser[1:3], key=lambda c: abs(luminance(c) - luminance(base) * 0.78)) if len(trouser) > 1 else base
	if luminance(shade) > luminance(base): base, shade = shade, base
	shoe = [c for c, _ in shoes.most_common(6) if c not in trouser[:2]] or [base]
	shoe_dark = min(shoe[:3], key=luminance)
	shoe_light = max(shoe[:3], key=luminance)
	return dict(base=base + (255,), shade=shade + (255,), shoe=shoe_light + (255,), shoe_dark=shoe_dark + (255,))


def disc_line(layer, a, b, width, color):
	"""Thick pixel line: every pixel whose centre lies within width/2 of segment a-b."""
	r = width / 2.0
	x0 = int(min(a[0], b[0]) - r - 1); x1 = int(max(a[0], b[0]) + r + 2)
	y0 = int(min(a[1], b[1]) - r - 1); y1 = int(max(a[1], b[1]) + r + 2)
	ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; ll = dx * dx + dy * dy or 1
	for y in range(y0, y1):
		for x in range(x0, x1):
			if not (0 <= x < layer.width and 0 <= y < layer.height): continue
			cx, cy = x + 0.5, y + 0.5
			t = max(0.0, min(1.0, ((cx - ax) * dx + (cy - ay) * dy) / ll))
			px, py = ax + t * dx, ay + t * dy
			if (cx - px) ** 2 + (cy - py) ** 2 <= r * r: layer.putpixel((x, y), color)


def outline(layer, top):
	"""Ink around the leg's own pixels, never above the hip row."""
	src = layer.copy()
	for y in range(top, layer.height):
		for x in range(layer.width):
			if opaque(src.getpixel((x, y))): continue
			for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
				if 0 <= nx < layer.width and 0 <= ny < layer.height and opaque(src.getpixel((nx, ny))):
					layer.putpixel((x, y), INK); break


def leg(size, hip, foot, lift, heel_up, facing, cfg, pal, near, top):
	"""One leg: thigh and shin with the knee bent forward, then a shoe pointing the way of travel."""
	layer = Image.new("RGBA", size, (0, 0, 0, 0))
	sw, sh = cfg["shoe"]
	ankle = (foot[0] + 0.5, foot[1] - sh - lift + 0.5)
	hx, hy = hip
	length = cfg["hip"] - sh + 1.0
	d = math.dist((hx, hy), ankle)
	bend = math.sqrt(max(0.0, (length / 2) ** 2 - (d / 2) ** 2))
	mx, my = (hx + ankle[0]) / 2, (hy + ankle[1]) / 2
	knee = (mx + facing * bend, my)
	trouser = pal["base"] if near else pal["shade"]
	disc_line(layer, (hx, hy), knee, cfg["thigh"], trouser)
	disc_line(layer, knee, ankle, cfg["shin"], trouser)
	# Shoe: heel behind the ankle, toe ahead; a lifted heel tips the shoe toe-down.
	heel = int(round(ankle[0] - facing * 2)); toe = heel + facing * (sw - 1)
	base_y = foot[1] - lift
	for i in range(sw):
		x = heel + facing * i
		rows = sh - (1 if i == sw - 1 else 0)
		drop = 1 if (heel_up and i < 3) else 0
		for j in range(rows):
			y = base_y - j - drop
			if 0 <= x < size[0] and 0 <= y < size[1]:
				layer.putpixel((x, y), pal["shoe_dark"] if (j == 0 or not near) else pal["shoe"])
	if near:
		# A sliver of shade down the back of the near trouser leg keeps the two legs apart.
		for y in range(top, size[1]):
			row = [x for x in range(size[0]) if layer.getpixel((x, y)) == trouser]
			if len(row) >= 4:
				edge = row[0] if facing > 0 else row[-1]
				layer.putpixel((edge, y), pal["shade"])
	outline(layer, top)
	return layer


def foot_at(phase, stride):
	"""Foot offset and lift for a phase of the cycle: stance glides back, swing arcs forward."""
	if phase < 0.5:
		return stride * (1 - 4 * phase), 0, False
	q = (phase - 0.5) * 2
	step = int(round(q * 4)) % 4
	lift = [0, 2, 3, 1][step]
	# The swinging foot leads a pixel as it passes, so its toe shows beside the planted one.
	return -stride + 2 * stride * q + (1 if step else 0), lift, step == 0


def side_cycle(actor, direction, source_frames):
	cfg = SIDE[actor]
	facing = 1 if direction == "right" else -1
	first, (fx, fy) = source_frames[0]
	ground = ground_row(first)
	cut = ground - cfg["hip"]
	pal = PALETTES.get(actor) or palette(first, cut, ground)
	PALETTES[actor] = pal
	frames = []
	for i in range(FRAMES):
		upper, _ = source_frames[(i * len(source_frames)) // FRAMES]
		near_p = i / FRAMES; far_p = ((i + FRAMES // 2) % FRAMES) / FRAMES
		passing = i % (FRAMES // 2) == FRAMES // 4
		bob = -1 if passing else 0
		canvas = Image.new("RGBA", first.size, (0, 0, 0, 0))
		body = upper.crop((0, 0, upper.width, cut))
		canvas.alpha_composite(body, (0, bob))
		if bob:
			# Keep the hip row filled under the raised body.
			canvas.alpha_composite(upper.crop((0, cut - 1, upper.width, cut)), (0, cut - 1))
		hip_y = cut - 0.5 + bob
		layers = []
		for near, p, off in ((False, far_p, -1), (True, near_p, 1)):
			dx, lift, heel = foot_at(p, cfg["stride"])
			hip = (fx + 0.5 + off * 0.5 * facing, hip_y)
			foot = (int(round(fx + facing * dx)), ground)
			layers.append(leg(first.size, hip, foot, lift, heel, facing, cfg, pal, near, cut - 1 + bob + 1))
		for layer in layers: canvas.alpha_composite(layer)
		# The trousers tuck under the body: redraw the body's lowest rows on top.
		canvas.alpha_composite(body.crop((0, cut - 2, body.width, cut)), (0, cut - 2 + bob))
		frames.append(canvas)
	return frames, (fx, fy)


def top_row(im):
	return im.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()[1]


def bobbed(im, dy, split_from_ground):
	"""Move everything above the knees by dy pixels (negative is up), leaving the feet planted."""
	ground = ground_row(im)
	split = ground - split_from_ground
	if not dy: return im.copy()
	out = im.copy()
	out.paste((0, 0, 0, 0), (0, 0, im.width, split))
	upper = im.crop((0, 0, im.width, split))
	if dy < 0:
		out.alpha_composite(upper, (0, dy))
		# Stretch the row at the knee to close the gap under the raised body.
		for k in range(-dy):
			out.alpha_composite(im.crop((0, split - 1, im.width, split)), (0, split - 1 - k))
	else:
		# Sitting lower: drop the body and lose the top rows of the shins under it.
		out.paste((0, 0, 0, 0), (0, split, im.width, split + dy))
		out.alpha_composite(upper, (0, dy))
	return out


def front_cycle(actor, direction, source_frames):
	"""Front/back views keep their drawn legs; contact frames (feet apart) sit, the rest rise one pixel."""
	frames = []
	spreads = []
	for im, _ in source_frames:
		a = im.getchannel("A"); g = ground_row(im)
		low = a.crop((0, g - 2, im.width, g + 1)).point(lambda v: 255 if v >= 128 else 0).getbbox()
		spreads.append(low[2] - low[0])
	idle, _ = load(actor, "idle_" + direction, 0)
	rest = top_row(idle)
	wide = sorted(spreads)[len(spreads) // 2]
	for (im, foot), spread in zip(source_frames, spreads):
		target = rest if spread > wide else rest - 1
		frames.append(bobbed(im, target - top_row(im), 6))
	return frames, source_frames[0][1]


def lifted(im, foot, side, lift, knee):
	"""Front/back step from a standing pose: one leg's lower half rises `lift` pixels."""
	g = ground_row(im); fx = foot[0]
	out = im.copy()
	xs = range(0, fx) if side < 0 else range(fx, im.width)
	top = g - knee
	for x in xs:
		column = [im.getpixel((x, y)) for y in range(top, g + 2)]
		for k, y in enumerate(range(top, g + 2)):
			src = k + lift
			out.putpixel((x, y), column[src] if src < len(column) else (0, 0, 0, 0))
	return out


def stand_cycle(actor, direction):
	im, foot = load(actor, "idle_" + direction, 0)
	knee = SIDE[actor]["hip"] // 2
	seq = [(0, 0), (-1, 1), (-1, 2), (-1, 1), (0, 0), (1, 1), (1, 2), (1, 1)]
	frames = []
	for side, lift in seq:
		step = lifted(im, foot, side, lift, knee) if lift else im.copy()
		frames.append(bobbed(step, -1 if lift == 2 else 0, knee + 2))
	return frames, foot


def main():
	os.makedirs(OUT, exist_ok=True)
	meta = {}
	jobs = []
	for actor in ("jules", "imani", "walt"):
		for direction in ("right", "left"):
			src = [load(actor, "walk_" + direction, i) for i in range(6)]
			jobs.append((actor, direction, side_cycle(actor, direction, src)))
		for direction in ("down", "up"):
			src = [load(actor, "walk_" + direction, i) for i in range(6)]
			jobs.append((actor, direction, front_cycle(actor, direction, src)))
	for actor in ("jak", "jaktennis", "eric"):
		src = [load(actor, "idle_right", 0)]
		jobs.append((actor, "right", side_cycle(actor, "right", src)))
		for direction in ("down", "up"):
			jobs.append((actor, direction, stand_cycle(actor, direction)))
	for actor, direction, (frames, foot) in jobs:
		w, h = frames[0].size
		strip = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
		for i, f in enumerate(frames): strip.paste(f, (i * w, 0))
		name = "%s-%s.png" % (actor, direction)
		strip.save(os.path.join(OUT, name))
		meta.setdefault(actor, {})[direction] = dict(file=name, frames=len(frames), size=[w, h], foot=list(foot))
	with open(os.path.join(OUT, "walk.json"), "w", newline="\r\n") as f:
		f.write(json.dumps(meta, indent=2) + "\n")
	print("wrote", len(jobs), "strips to", OUT)


if __name__ == "__main__":
	main()
