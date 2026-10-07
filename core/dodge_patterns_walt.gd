class_name DodgePatternsWalt
extends RefCounted
## HOLD THE LIGHT: the storm on Broadway. Five handmade attacks, one per turn,
## cycling in order. Every attack keeps Walt's promise: three GUSTs are called,
## and raising the lantern (confirm beside it) before each one keeps it lit.
## Phase 1 (from the second turn) adds a layer to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["crosswind", "dust_devil", "downdraft", "sign_spin", "rain"]
const PHASES: Array[int] = [0, 1]
const LENGTH: int = 480
const GUSTS: Array[int] = [130, 270, 400]
const LANTERN_REACH: float = 26.0

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = LENGTH
	s.lanternAt = Vector2(0, 34)
	s.gustUntil = -1
	s.gustDir = Vector2.LEFT
	s.baseWind = Vector2.ZERO
	s.gap = 3
	s.spin = 1.0
	s.slant = 0.6
	s.roof = Rect2(-32, -16, 64, 6)
	match id:
		"crosswind":
			s.phaseName = "Crosswind"
			s.hint = "Wind pushes you. Slip through the paper gaps. Raise the lantern before each GUST."
		"dust_devil":
			s.phaseName = "Dust Devil"
			s.hint = "Debris spirals out of the whirlwind. Circle with the gaps."
			s.lanternAt = Vector2(-50, 36)
		"downdraft":
			s.phaseName = "Downdraft"
			s.hint = "Pinned down: up or confirm jumps, hold for height. Hop bags, duck sheets."
			s.lanternAt = Vector2(-96, 34)
		"sign_spin":
			s.phaseName = "Bus Stop Sign"
			s.hint = "The sign spins. Keep out of the marked rows as the box turns."
			s.lanternAt = Vector2(0, 0)
		"rain":
			s.phaseName = "Sideways Rain"
			s.hint = "Rain slants with the wind. Stay under the moving shelter roof."
			s.lanternAt = Vector2(0, 2)

static func lantern_local(s: Dictionary) -> Vector2:
	if s.patternId == "rain":
		return Vector2(s.roof.get_center().x, s.roof.end.y + 10)
	return s.lanternAt

static func confirm(s: Dictionary) -> void:
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	if soul.distance_to(lantern_local(s)) <= LANTERN_REACH:
		s.lanternRaised = 90
		s.lantern = mini(100, int(s.lantern) + 20)
		D.effect(s, "lantern", D.to_world(s, lantern_local(s)), 30)

static func promise_complete(s: Dictionary) -> bool:
	return int(s.gustsKept) >= 3 and int(s.lantern) > 0

static func tick(s: Dictionary, t: int) -> void:
	_gusts(s, t)
	var phase: int = int(s.phase)
	match str(s.patternId):
		"crosswind": _crosswind(s, t, phase)
		"dust_devil": _dust_devil(s, t, phase)
		"downdraft": _downdraft(s, t, phase)
		"sign_spin": _sign_spin(s, t, phase)
		"rain": _rain(s, t, phase)
	var gusting: bool = t < int(s.gustUntil)
	s.wind = Vector2(s.baseWind) + (Vector2(s.gustDir) * 1.15 if gusting else Vector2.ZERO)

static func after(_s: Dictionary, _t: int) -> void:
	pass

static func _gusts(s: Dictionary, t: int) -> void:
	for g: int in GUSTS:
		if t == g - 60:
			D.banner(s, "GUST", 60)
			s.gustDir = Vector2.LEFT if D.rand(s) < 0.5 else Vector2.RIGHT
			if s.patternId == "downdraft": s.gustDir = Vector2(s.gustDir) * 0.6
			D.warn(s, {"kind": "gust", "dir": s.gustDir}, 60, true)
			# In the whirlwind Walt holds the lantern out on your side of the eye.
			if s.patternId == "dust_devil":
				s.lanternAt = Vector2(absf(Vector2(s.lanternAt).x) * (-1.0 if float(s.soul.x) < 0.0 else 1.0), Vector2(s.lanternAt).y)
			# In the crosswind he steps along the bottom row to meet you.
			if s.patternId == "crosswind":
				s.lanternAt = Vector2(clampf(float(s.soul.x), -70.0, 70.0), Vector2(s.lanternAt).y)
		if t == g:
			# Anywhere inside the raised lantern's glow counts, not only touching it.
			var near: bool = Vector2(float(s.soul.x), float(s.soul.y)).distance_to(lantern_local(s)) <= LANTERN_REACH + 14.0
			# A lantern raised during the warning stays sheltered through the gust;
			# standing in its glow also shelters you from the push.
			if int(s.lanternRaised) > 0:
				s.gustsKept = int(s.gustsKept) + 1
				D.effect(s, "kept", D.to_world(s, lantern_local(s)), 40)
			else:
				s.lantern = maxi(0, int(s.lantern) - 34)
				D.effect(s, "gutter", D.to_world(s, lantern_local(s)), 40)
			# Holding the raised lantern shelters you from the push itself.
			s.gustUntil = t + (0 if near and int(s.lanternRaised) > 0 else 28)
			for i: int in range(6 + int(s.phase) * 3):
				var from_x: float = 150.0 if Vector2(s.gustDir).x < 0 else -150.0
				D.shot(s, {"x": 128.0 + from_x * 1.2, "y": D.rand_range(s, -10.0, 130.0), "vx": -signf(from_x) * D.rand_range(s, 3.0, 4.2), "vy": D.rand_range(s, -0.3, 0.3), "r": 2.5, "shape": "grit", "spin": 0.3, "life": 140})

# Crosswind: a snaking corridor through walls of loose paper, with a steady push
# from upwind that flips halfway (telegraphed). Phase 1 adds tumbling bags.
static func _crosswind(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 112.0}, 24)
		s.baseWind = Vector2(-0.5, 0)
	if t == 200:
		D.warn(s, {"kind": "arrows", "dir": Vector2.RIGHT}, 50, true)
		D.banner(s, "THE WIND TURNS", 50)
	if t == 238: s.baseWind = Vector2.ZERO
	if t == 252: s.baseWind = Vector2(0.5, 0)
	var flipped: bool = t >= 245
	var every: int = 16 if phase > 0 else 22
	if t % every == 0 and t < 440 and not (t > 222 and t < 262):
		# While a GUST is called the paper gap drifts down to the lantern's row.
		var calling: bool = GUSTS.any(func(g: int) -> bool: return t >= g - 60 and t <= g + 10)
		if calling: s.gap = mini(5, int(s.gap) + 1)
		else: s.gap = clampi(int(s.gap) + (-1 if D.rand(s) < 0.5 else 1), 0, 5)
		var h: Vector2 = D.half(s)
		var slots: int = 8
		var spacing: float = (h.y * 2.0 - 8.0) / float(slots - 1)
		var side: float = -1.0 if flipped else 1.0
		for i: int in range(slots):
			if i == int(s.gap) or i == int(s.gap) + 1: continue
			D.shot(s, {"space": "box", "x": side * (h.x + 12.0), "y": -h.y + 4.0 + i * spacing, "vx": -side * (2.1 + phase * 0.4), "collide": "rect", "w": 4.0, "h": 4.5,
				"shape": "paper", "rot": D.rand(s) * TAU, "spin": D.rand_range(s, -0.15, 0.15), "wave": {"amp": 3.5, "freq": 0.11, "phase": i * 0.8}, "life": 220})
	if phase > 0 and t % 90 == 45 and t < 420:
		var side_b: float = -1.0 if flipped else 1.0
		D.shot(s, {"space": "box", "x": side_b * (D.half(s).x + 14.0), "y": -20.0, "vx": -side_b * 1.5, "vy": -1.0, "ay": 0.14, "bounce": 0.92, "r": 8.0, "shape": "bag", "spin": -side_b * 0.08, "life": 300})

# Dust Devil: a whirlwind in a narrow box throws out spiral arms of leaves. The
# spin reverses at the midpoint. Phase 1 adds a sparse counter-spiral.
static func _dust_devil(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 150.0, "h": 120.0}, 30)
		s.spin = 1.0
		s.armAngle = D.rand(s) * TAU
	if t == 210:
		D.warn(s, {"kind": "spin", "dir": -1.0}, 40, true)
		D.banner(s, "IT TURNS BACK", 40)
	if t == 250: s.spin = -1.0
	if t < 36 or t > 430: return
	if t % 8 == 0 and not (t > 236 and t < 256):
		var arms: int = 3
		s.armAngle = float(s.armAngle) + 0.2 * float(s.spin)
		var c: Vector2 = D.centre(s)
		for i: int in range(arms):
			D.shot(s, {"orbit": {"ox": c.x, "oy": c.y, "radius": 8.0, "angle": float(s.armAngle) + i * TAU / arms, "av": 0.01 * float(s.spin), "dr": 1.25, "maxRadius": 120.0},
				"r": 3.5, "shape": "leaf", "spin": 0.1, "rot": D.rand(s) * TAU})
	if phase > 0 and t % 18 == 9 and not (t > 236 and t < 256):
		var c2: Vector2 = D.centre(s)
		for i: int in range(2):
			D.shot(s, {"orbit": {"ox": c2.x, "oy": c2.y, "radius": 8.0, "angle": -float(s.armAngle) * 1.3 + i * PI, "av": -0.016 * float(s.spin), "dr": 1.0, "maxRadius": 120.0},
				"r": 3.0, "shape": "grit", "spin": 0.2})
	# The eye of the storm is not a hiding place.
	if t % 60 == 30:
		var c3: Vector2 = D.centre(s)
		var aim: Vector2 = (D.soul_world(s) - c3).normalized()
		D.shot(s, {"x": c3.x, "y": c3.y, "vx": aim.x * 1.6, "vy": aim.y * 1.6, "r": 4.0, "shape": "can", "spin": 0.2, "life": 200})

# Downdraft: blue soul. Bags hop along the ground at varying heights, sheets fly
# at head or ankle height. Phase 1 flips the whole box upside down mid-attack.
static func _downdraft(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 84.0, "cy": 64.0}, 24)
		D.set_mode(s, "blue")
		D.banner(s, "PINNED DOWN", 50)
	if phase > 0 and t == 210:
		D.warn(s, {"kind": "flip"}, 50, true)
		D.banner(s, "UPDRAFT", 50)
	if phase > 0 and t == 236:
		D.box_to(s, {"rot": PI}, 44, 0, "inout")
	var calm: bool = phase > 0 and t > 214 and t < 296
	if calm: return
	var h: Vector2 = D.half(s)
	var bag_every: int = 44 if phase > 0 else 52
	if t % bag_every == 6 and t < 430:
		D.shot(s, {"space": "box", "x": h.x + 12.0, "y": h.y - 7.0, "vx": -D.rand_range(s, 1.5, 2.2), "vy": -D.rand_range(s, 1.0, 3.6), "ay": 0.15, "bounce": 0.95,
			"r": 7.0, "shape": "bag", "spin": -0.06, "life": 360})
	if t % 70 == 40 and t < 420:
		var low: bool = int(t / 70) % 2 == 0
		var y: float = h.y - (5.0 if low else 30.0)
		D.warn(s, {"kind": "edge", "space": "box", "x": h.x - 2.0, "y": y, "dir": Vector2.LEFT}, 34)
		var speed: float = 3.0 + phase * 0.4
		for i: int in range(3 if low else 4):
			D.shot(s, {"space": "box", "x": h.x + 40.0 + i * 14.0 + speed * 34.0, "y": y, "vx": -speed, "collide": "rect", "w": 5.0, "h": 3.5,
				"shape": "sheet", "life": 260})
	if phase > 0 and t % 60 == 20 and t > 300 and t < 420:
		D.shot(s, {"space": "box", "x": D.rand_range(s, -h.x + 20.0, h.x - 20.0), "y": -h.y - 8.0, "vy": 1.4, "r": 3.0, "shape": "leaf", "spin": 0.2, "wave": {"amp": 10.0, "freq": 0.07}, "life": 200})

# Bus Stop Sign: the square box spins while rows of paper cross the arena on
# fixed lanes, so a safe corner of the box drifts into danger as it turns.
static func _sign_spin(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 112.0, "h": 112.0}, 30)
	if t >= 30:
		s.box.rot = wrapf(float(s.box.rot) + 0.010 + phase * 0.004 + (0.006 if t > 300 else 0.0), -PI, PI)
	if t < 40 or t > 430: return
	var lanes: Array[float] = [10.0, 34.0, 60.0, 86.0, 110.0]
	if t % 40 == 0:
		var lane: int = int(D.rand(s) * lanes.size())
		var from_left: bool = D.rand(s) < 0.5
		var y: float = lanes[lane]
		D.warn(s, {"kind": "lane", "y": y, "h": 8.0, "horizontal": true}, 40)
		var speed: float = 3.6
		for i: int in range(7):
			var start: float = -100.0 - i * 13.0 - speed * 40.0
			D.shot(s, {"x": start if from_left else 256.0 - start, "y": y, "vx": speed if from_left else -speed, "collide": "rect", "w": 4.0, "h": 5.0,
				"shape": "paper", "rot": 0.0, "spin": 0.12, "life": 260})
	if phase > 0 and t % 80 == 60 and t > 120:
		var x: float = D.centre(s).x + D.rand_range(s, -40.0, 40.0)
		D.warn(s, {"kind": "lane", "x": x, "w": 8.0, "horizontal": false}, 40)
		for i: int in range(5):
			D.shot(s, {"x": x, "y": -70.0 - i * 13.0 - 3.2 * 40.0, "vy": 3.2, "collide": "rect", "w": 4.0, "h": 5.0, "shape": "paper", "spin": 0.12, "life": 260})

# Sideways Rain: dense slanted rain, a shelter roof that slides along the top
# of the box, and (phase 1) puddle splashes that erupt under you.
static func _rain(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 272.0, "h": 104.0}, 30)
		s.slant = 0.7
	var h: Vector2 = D.half(s)
	var roof_x: float = sin(t * 0.016) * (h.x - 46.0)
	s.roof = Rect2(roof_x - 32.0, -h.y + 34.0, 64.0, 6.0)
	if t == 190:
		D.warn(s, {"kind": "arrows", "dir": Vector2.LEFT}, 40, true)
		D.banner(s, "THE RAIN TURNS", 40)
	if t == 230: s.slant = -0.7
	if t < 24 or t > 440: return
	for i: int in range(2 if phase > 0 or t % 3 != 0 else 1):
		var x: float = D.rand_range(s, -h.x - 80.0, h.x + 80.0)
		D.shot(s, {"space": "box", "x": x, "y": -h.y - 6.0, "vx": float(s.slant) * 3.0, "vy": 3.4, "r": 1.6, "shape": "drop", "life": 120, "roofed": true})
	if phase > 0 and t % 75 == 50:
		var px: float = D.rand_range(s, -h.x + 24.0, h.x - 24.0)
		if absf(px - roof_x) < 40.0: px = clampf(px + 80.0 * signf(px - roof_x + 0.01), -h.x + 24.0, h.x - 24.0)
		s.splashes = s.get("splashes", [])
		s.splashes.append({"x": px, "at": t + 40})
		D.warn(s, {"kind": "puddle", "space": "box", "x": px, "y": h.y - 2.0}, 40)
	for splash: Dictionary in s.get("splashes", []):
		if int(splash.at) == t:
			for i: int in range(7):
				var a: float = -PI / 2.0 + (i - 3) * 0.22
				D.shot(s, {"space": "box", "x": float(splash.x), "y": h.y - 3.0, "vx": cos(a) * 2.2, "vy": sin(a) * 3.4, "ay": 0.09, "r": 2.2, "shape": "drop", "life": 120})
	for b: Dictionary in s.bullets:
		if b.get("roofed", false) and s.roof.grow(1.0).has_point(Vector2(float(b.x), float(b.y))):
			b.dead = true
			D.effect(s, "splash", D.to_world(s, Vector2(float(b.x), s.roof.position.y)), 8)

static func progress(s: Dictionary) -> String:
	return "Lantern %d%% / gusts %d/3" % [int(s.lantern), mini(3, int(s.gustsKept))]

static func draw_under(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(_c: CanvasItem, _b: Dictionary, _at: Vector2, _turn: float, _alpha: float, _v: Node2D) -> bool:
	return false
