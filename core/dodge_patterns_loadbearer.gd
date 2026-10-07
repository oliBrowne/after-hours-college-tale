extends RefCounted
## LOADBEARER: the loader on the engineering test floor that wants to carry
## every plan alone. "EVERY PLAN. ONE SUPPORT. DO NOT LET GO." Four handmade
## attacks, one per turn, cycling: a wrecking swing, falling girders, stress
## cracks under a crushing load, and a riveting line of steel struts.
## The promise (Shared Foundations): two foundations sit near the floor. Each
## has its own window (ticks 0-115 and 180-295); confirm beside it while
## promised to light it before its hanging weight falls. A lit foundation
## catches its weight and shelters you (its box-space Rect2 joins s.safe).
## An unlit one lets the weight crash through and crack the floor.
## Phase 1 (from the second turn) adds a layer to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["crane", "girders", "cracks", "rivets"]
const PHASES: Array[int] = [0, 1]
const LENGTH: int = 420
const WINDOWS: Array[int] = [0, 180]
const OPEN: int = 115
const REACH: float = 20.0
const STEEL: Color = Color("7d8a99")
const IRON: Color = Color("3a3f4a")
const AMBER: Color = Color("e8b45c")
const ROSE: Color = Color("e8837b")
const CREAM: Color = Color("e6d6b1")
const CONCRETE: Color = Color("5d5a58")
const DUST: Color = Color("b49a80")
const HAZARD: Color = Color("e0a030")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = LENGTH
	s.phaseName = "Shared Foundations"
	s.anchorsLit = [false, false]
	s.currentAnchor = 0
	s.anchorWindow = false
	s.weightState = ["hang", "hang"]
	s.safe = []
	s.botGoal = null
	s.bannerColor = HAZARD
	s.blueFloor = id == "girders"
	match id:
		"crane":
			s.hint = "The load swings on a steel cable. Stay under it or out of reach. Light each foundation."
		"girders":
			s.hint = "Pinned to the test floor. Dodge girders and rivets, jump the shards. Light each foundation."
		"cracks":
			s.hint = "The load presses down and the walls crack. Slip between cracks. Light each foundation."
		"rivets":
			s.hint = "Steel struts march across. Ride their gaps. Light each foundation before its weight falls."
	for i: int in range(2):
		var at: Vector2 = _foundation(s, i)
		D.objective(s, {"kind": "confirm", "x": at.x, "y": at.y, "r": REACH, "active": false})

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return bool(s.anchorsLit[0]) and bool(s.anchorsLit[1])

static func progress(s: Dictionary) -> String:
	return "Foundations lit %d/2\nConfirm before weight falls" % int(s.objectiveCount)

static func _foundation(s: Dictionary, i: int) -> Vector2:
	var h: Vector2 = D.half(s)
	return Vector2((-1.0 if i == 0 else 1.0) * (h.x - 58.0), h.y - (16.0 if bool(s.blueFloor) else 30.0))

static func _shelter(s: Dictionary, i: int) -> Rect2:
	var at: Vector2 = _foundation(s, i)
	return Rect2(at - Vector2(20, 26), Vector2(40, 52))

static func _soul(s: Dictionary) -> Vector2:
	return Vector2(float(s.soul.x), float(s.soul.y))

static func tick(s: Dictionary, t: int) -> void:
	_foundations(s, t)
	var phase: int = int(s.phase)
	match str(s.patternId):
		"crane": _crane(s, t, phase)
		"girders": _girders(s, t, phase)
		"cracks": _cracks(s, t, phase)
		"rivets": _rivets(s, t, phase)
	_grow(s)
	_weights(s, t)

static func after(s: Dictionary, _t: int) -> void:
	var safe: Array = []
	for i: int in range(2):
		var o: Dictionary = s.objectives[i]
		var at: Vector2 = _foundation(s, i)
		o.x = at.x; o.y = at.y
		s.anchorsLit[i] = bool(o.done)
		if o.done: safe.append(_shelter(s, i))
	s.safe = safe

# ---------------------------------------------------------------- foundations

static func _foundations(s: Dictionary, t: int) -> void:
	s.currentAnchor = mini(1, t / 180)
	s.anchorWindow = t < 360 and t % 180 < OPEN
	for i: int in range(2):
		var o: Dictionary = s.objectives[i]
		var start: int = WINDOWS[i]
		if t == start:
			o.active = true
			D.banner(s, "%s FOUNDATION" % ("LEFT" if i == 0 else "RIGHT"), 50)
		if t == start + OPEN:
			o.active = false
			_drop(s, i)
		if t == start + OPEN - 32:
			D.warn(s, {"kind": "lb_drop", "x": _foundation(s, i).x, "w": 18.0}, 32, true)
			D.banner(s, "WEIGHT FALLS", 32)
	# Autopilot: head for the next foundation just before its window, and
	# otherwise wait under a lit one (a player would shelter there too).
	s.botGoal = null
	if t >= 150 and t < 180 and not s.objectives[1].done:
		s.botGoal = _foundation(s, 1)
	elif not s.objectives[0].active and not s.objectives[1].active:
		var soul: Vector2 = _soul(s)
		for i: int in range(2):
			if s.objectives[i].done and (s.botGoal == null or soul.distance_to(_foundation(s, i)) < soul.distance_to(Vector2(s.botGoal))):
				s.botGoal = _foundation(s, i)

static func _drop(s: Dictionary, i: int) -> void:
	var h: Vector2 = D.half(s)
	var at: Vector2 = _foundation(s, i)
	s.weightState[i] = "fall"
	D.shot(s, {"space": "box", "x": at.x, "y": -h.y - 12.0, "vy": 1.2, "ay": 0.3, "collide": "rect", "w": 15.0, "h": 9.0, "shape": "weight", "weight": i, "life": 400})

static func _weights(s: Dictionary, _t: int) -> void:
	var h: Vector2 = D.half(s)
	for b: Dictionary in s.bullets:
		if not b.has("weight") or b.has("fade"): continue
		var i: int = int(b.weight)
		var at: Vector2 = _foundation(s, i)
		if b.has("rest"):
			b.rest = int(b.rest) - 1
			b.x = at.x
			if int(b.rest) <= 0: b.fade = 20
			continue
		var lit: bool = bool(s.anchorsLit[i])
		var land: float = at.y - 26.0 - 9.0 if lit else h.y - 9.0
		if float(b.y) + float(b.vy) >= land:
			b.y = land; b.vy = 0.0; b.ay = 0.0
			b.rest = 70 if lit else 34
			s.weightState[i] = "held" if lit else "crashed"
			if lit:
				D.effect(s, "kept", D.to_world(s, Vector2(at.x, land)), 30)
				D.banner(s, "LOAD SHARED", 40)
			else:
				D.effect(s, "hit", D.to_world(s, Vector2(at.x, h.y)), 24)
				D.banner(s, "CRACK", 30)
				for side: float in [-1.0, 1.0]:
					D.shot(s, {"space": "box", "x": at.x + side * 16.0, "y": h.y - 2.5, "vx": side * 2.2, "collide": "rect", "w": 3.0, "h": 2.5, "shape": "shard", "life": 120})
					D.shot(s, {"space": "box", "x": at.x + side * 8.0, "y": h.y - 10.0, "vx": side * 1.1, "vy": -2.4, "ay": 0.12, "r": 2.5, "shape": "chip", "life": 90})

# ---------------------------------------------------------------- strokes

static func _stroke(s: Dictionary, from: Vector2, dir: Vector2, length: float, speed: float, thick: float, warn: int, linger: int, shape: String, extra: Dictionary = {}) -> Dictionary:
	var props: Dictionary = {"space": "box", "x": from.x, "y": from.y, "collide": "rect", "w": 0.5, "h": thick, "rot": dir.angle(), "shape": shape, "arm": warn,
		"life": warn + int(ceil(length / speed)) + linger + 40,
		"stroke": {"ox": from.x, "oy": from.y, "dx": dir.x, "dy": dir.y, "len": length, "speed": speed, "warn": warn, "linger": linger, "cur": 0.0, "full": false, "fullAt": 0}}
	props.merge(extra, true)
	return D.shot(s, props)

static func _grow(s: Dictionary) -> void:
	var chips: Array = []
	for b: Dictionary in s.bullets:
		if not b.has("stroke") or b.has("fade"): continue
		var k: Dictionary = b.stroke
		var grown: float = clampf(float(int(b.age) - int(k.warn)) * float(k.speed), 0.0, float(k.len))
		var d: Vector2 = Vector2(float(k.dx), float(k.dy))
		var mid: Vector2 = Vector2(float(k.ox), float(k.oy)) + d * grown * 0.5
		b.x = mid.x; b.y = mid.y; b.w = maxf(0.5, grown * 0.5)
		k.cur = grown
		if grown >= float(k.len) and not bool(k.full):
			k.full = true; k.fullAt = int(b.age)
		if bool(k.full) and int(b.age) - int(k.fullAt) >= int(k.linger):
			b.fade = 14
			if b.get("spall", false): chips.append(Vector2(float(k.ox), float(k.oy)) + d * float(k.len))
	# A crack spalls as it closes: a chip flies off each joint.
	for at: Vector2 in chips:
		var a: float = D.rand(s) * TAU
		D.shot(s, {"space": "box", "x": at.x, "y": at.y, "vx": cos(a) * 1.1, "vy": sin(a) * 1.1, "r": 2.5, "shape": "chip", "spin": 0.2, "life": 110})

static func _rivet(s: Dictionary, x: float, bounce: bool) -> void:
	D.warn(s, {"kind": "lb_rivet", "x": x}, 26)
	s.rivetsDue = s.get("rivetsDue", [])
	s.rivetsDue.append({"x": x, "at": int(s.clock) + 26, "bounce": bounce})

static func _fire_rivets(s: Dictionary) -> void:
	if not s.has("rivetsDue"): return
	var h: Vector2 = D.half(s)
	var keep: Array = []
	for r: Dictionary in s.rivetsDue:
		if int(r.at) == int(s.clock):
			var props: Dictionary = {"space": "box", "x": float(r.x), "y": -h.y - 4.0, "vy": 3.3, "r": 2.5, "shape": "rivet", "life": 180}
			if bool(r.bounce): props.merge({"bounce": 0.55, "ay": 0.12, "vx": D.rand_range(s, -0.6, 0.6)}, true)
			D.shot(s, props)
		elif int(r.at) > int(s.clock):
			keep.append(r)
	s.rivetsDue = keep

# ---------------------------------------------------------------- Wrecking Swing
# A gantry trolley swings a wrecking load from wall to wall on a steel cable
# (the cable hurts too), so the only safe ground is under the arc or out of
# its reach in the top corners. Each time the load hits a wall it shakes bolts
# loose back into the box, and rivets drop from the gantry near you.
# Phase 1: a second, shorter load swings out of step through the middle.
static func _swing(t: int, period: float, amp: float, offset: float) -> float:
	return -amp * cos(TAU * maxf(0.0, float(t - 36)) / period + offset)

static func _crane(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 256.0, "h": 120.0}, 20)
		s.pivot = Vector2(0, -150)
		D.shot(s, {"space": "box", "x": 0.0, "y": 0.0, "r": 11.0, "shape": "ball", "ball": 0, "arm": 36, "life": 2000})
		D.shot(s, {"space": "box", "x": 0.0, "y": 0.0, "collide": "rect", "w": 90.0, "h": 1.5, "shape": "cable", "cable": true, "arm": 36, "life": 2000})
		if phase > 0:
			D.shot(s, {"space": "box", "x": 0.0, "y": 0.0, "r": 8.0, "shape": "ball", "ball": 1, "arm": 36, "life": 2000})
	var pivot: Vector2 = s.pivot
	var big: float = _swing(t, 150.0, 0.66, 0.0)
	for b: Dictionary in s.bullets:
		if b.has("cable"):
			# The cable is steel too: only the part inside the box matters.
			var dir: Vector2 = Vector2(sin(big), cos(big))
			var inner: float = (-h.y - 6.0 - pivot.y) / maxf(0.2, dir.y)
			var from: Vector2 = pivot + dir * inner
			var to: Vector2 = pivot + dir * (196.0 - 11.0)
			var mid: Vector2 = (from + to) * 0.5
			b.x = mid.x; b.y = mid.y; b.w = from.distance_to(to) * 0.5; b.rot = dir.angle()
			continue
		if not b.has("ball"): continue
		var second: bool = int(b.ball) == 1
		var length: float = 150.0 if second else 196.0
		var theta: float = _swing(t, 112.0, 0.78, PI) if second else big
		var at: Vector2 = pivot + Vector2(sin(theta), cos(theta)) * length
		b.x = at.x; b.y = at.y
	# The big load reaches a wall every half swing: CLANG, bolts shake loose.
	if t > 36 and (t - 36) % 75 == 0 and t < 380:
		var side: float = -1.0 if ((t - 36) / 75) % 2 == 0 else 1.0
		var hit: Vector2 = pivot + Vector2(sin(side * 0.66), cos(0.66)) * 196.0
		D.effect(s, "hit", D.to_world(s, hit), 20)
		for i: int in range(4 + phase):
			var a: float = (PI if side > 0.0 else 0.0) + D.rand_range(s, -0.75, 0.75)
			D.shot(s, {"space": "box", "x": hit.x - side * 8.0, "y": hit.y, "vx": cos(a) * D.rand_range(s, 1.4, 2.1), "vy": sin(a) * D.rand_range(s, 1.4, 2.1), "ay": 0.02, "r": 2.5, "shape": "bolt", "spin": 0.2, "life": 200})
	var every: int = 28 if phase == 0 else 32
	if t >= 20 and t <= 380 and t % every == 0:
		var x: float = clampf(float(s.soul.x) + D.rand_range(s, -12.0, 12.0), -h.x + 8.0, h.x - 8.0)
		_rivet(s, x, false)
	_fire_rivets(s)

# ---------------------------------------------------------------- Girder Drop
# Blue soul on the test floor. Girders drop into marked columns near you, land
# with a clang and send shards skidding both ways along the floor: step out of
# the column, then jump the shards. Landed girders block the floor until the
# crane lifts them (never between you and a foundation that is due), and loose
# rivets rain from the gantry. Phase 1: the crane also sweeps a girder across
# at head height, so for a moment you must not jump.
static func _girders(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 256.0, "h": 96.0}, 20)
		D.set_mode(s, "blue")
		s.soul.gravity = Vector2.DOWN
		s.dropsDue = []
	var every: int = 34 if phase == 0 else 38
	if t >= 24 and t <= 360 and (t - 24) % every == 0:
		var picked: bool = false
		var x: float = 0.0
		var next: int = 0 if t < 130 else 1
		var route: Vector2 = Vector2(minf(float(s.soul.x), _foundation(s, next).x) - 30.0, maxf(float(s.soul.x), _foundation(s, next).x) + 30.0)
		var open_route: bool = not s.objectives[next].done and t < WINDOWS[next] + OPEN
		for attempt: int in range(12):
			x = clampf(float(s.soul.x) + D.rand_range(s, -24.0, 24.0) * (1.0 + attempt * 0.25), -h.x + 22.0, h.x - 22.0)
			var ok: bool = true
			for i: int in range(2):
				if absf(x - _foundation(s, i).x) < 32.0: ok = false
			if open_route and x > route.x and x < route.y and absf(x - float(s.soul.x)) > 4.0: ok = false
			for b: Dictionary in s.bullets:
				if b.has("girder") and absf(float(b.x) - x) < 46.0: ok = false
			for due: Dictionary in s.dropsDue:
				if absf(float(due.x) - x) < 46.0: ok = false
			if ok:
				picked = true; break
		if picked:
			D.warn(s, {"kind": "lb_drop", "x": x, "w": 22.0}, 36, true)
			s.dropsDue.append({"x": x, "at": t + 36})
	var keep: Array = []
	for due: Dictionary in s.dropsDue:
		if int(due.at) == t:
			D.shot(s, {"space": "box", "x": float(due.x), "y": -h.y - 8.0, "vy": 1.0, "ay": 0.25, "collide": "rect", "w": 20.0, "h": 5.0, "shape": "girder", "girder": true, "life": 400})
		elif int(due.at) > t:
			keep.append(due)
	s.dropsDue = keep
	for b: Dictionary in s.bullets:
		if not b.has("girder") or b.has("fade"): continue
		if b.has("landed"):
			b.landed = int(b.landed) + 1
			if int(b.landed) == 96:
				b.vy = -1.3
				b.lift = true
			continue
		if float(b.y) + float(b.vy) >= h.y - 5.0:
			b.y = h.y - 5.0; b.vy = 0.0; b.ay = 0.0; b.landed = 0
			D.effect(s, "hit", D.to_world(s, Vector2(float(b.x), h.y)), 16)
			for side: float in [-1.0, 1.0]:
				D.shot(s, {"space": "box", "x": float(b.x) + side * 22.0, "y": h.y - 2.5, "vx": side * 2.1, "collide": "rect", "w": 3.0, "h": 2.5, "shape": "shard", "life": 140})
	if phase > 0 and t >= 70 and t <= 360 and (t - 70) % 92 == 0:
		var side2: float = -1.0 if D.rand(s) < 0.5 else 1.0
		var y: float = h.y - 25.0
		D.warn(s, {"kind": "lb_beam", "y": y, "h": 5.0}, 40, true)
		D.warn(s, {"kind": "edge", "space": "box", "x": side2 * (h.x - 4.0), "y": y, "dir": Vector2(-side2, 0)}, 40)
		D.shot(s, {"space": "box", "x": side2 * (h.x + 28.0 + 3.0 * 40.0), "y": y, "vx": -side2 * 3.0, "collide": "rect", "w": 26.0, "h": 4.0, "shape": "girder", "swung": true, "life": 260})
	for b2: Dictionary in s.bullets:
		if b2.shape == "shard" and absf(float(b2.x)) > h.x + 6.0: b2.dead = true
	# Loose rivets rain from the gantry between drops.
	if t >= 44 and t <= 370 and (t - 44) % 40 == 0:
		_rivet(s, clampf(float(s.soul.x) + D.rand_range(s, -10.0, 10.0), -h.x + 8.0, h.x - 8.0), false)
	_fire_rivets(s)

# ---------------------------------------------------------------- Stress Cracks
# The load presses down: the box is crushed flat (telegraphed), held, then
# released, and dust rains from the ceiling. Cracks run in from the walls,
# floor and ceiling toward you as jagged, forking lines (a hairline shows each
# first), then spall chips off their joints. Phase 1: when the load lands,
# rivets burst out of the ceiling at you.
static func _cracks(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 112.0}, 20)
	var squeeze_every: int = 120 if phase == 0 else 104
	if t >= 50 and t <= 340 and (t - 50) % squeeze_every == 0:
		D.warn(s, {"kind": "lb_squeeze"}, 30, true)
		D.banner(s, "LOAD", 30)
		D.box_to(s, {"h": 74.0, "cy": 79.0}, 12, 30, "in")
		D.box_to(s, {"h": 112.0, "cy": 60.0}, 30, 78, "out")
		if phase > 0:
			s.burstAt = t + 42
	if phase > 0 and t == int(s.get("burstAt", -1)):
		for i: int in range(3):
			var x: float = clampf(float(s.soul.x) + (i - 1) * 26.0, -h.x + 10.0, h.x - 10.0)
			var from: Vector2 = Vector2(x, -h.y + 2.0)
			var aim: Vector2 = (_soul(s) - from).normalized() * 1.7
			D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": aim.x, "vy": aim.y, "r": 2.5, "shape": "bolt", "spin": 0.2, "life": 160})
	if t >= 50 and t <= 340 and (t - 50) % squeeze_every == 42:
		for i: int in range(5):
			D.shot(s, {"space": "box", "x": D.rand_range(s, -h.x + 10.0, h.x - 10.0), "y": -h.y - 4.0, "vy": D.rand_range(s, 0.8, 1.3), "ay": 0.03, "r": 2.5, "shape": "chip", "spin": 0.2, "life": 160})
	var every: int = 30 if phase == 0 else 27
	if t >= 16 and t <= 370 and (t - 16) % every == 0:
		var n: int = (t - 16) / every
		var wall: int = [0, 1, 2, 0, 1, 3][n % 6]
		var soul: Vector2 = _soul(s)
		match wall:
			0, 1:
				var side: float = -1.0 if wall == 0 else 1.0
				var y: float = clampf(soul.y + D.rand_range(s, -8.0, 8.0), -h.y + 8.0, h.y - 8.0)
				_crack(s, Vector2(side * (h.x + 2.0), y), PI if side > 0.0 else 0.0, 6, 22.0)
			2, 3:
				var up: float = -1.0 if wall == 2 else 1.0
				var x: float = clampf(soul.x + D.rand_range(s, -8.0, 8.0), -h.x + 10.0, h.x - 10.0)
				_crack(s, Vector2(x, -up * (h.y + 2.0)), -PI / 2.0 if up < 0.0 else PI / 2.0, 5, 23.0)

static func _crack(s: Dictionary, from: Vector2, heading: float, segs: int, length: float) -> void:
	var speed: float = 4.5
	var step: int = int(ceil(length / speed))
	var total: int = step * segs
	var at: Vector2 = from
	var angle: float = heading
	for i: int in range(segs):
		angle = heading + D.rand_range(s, -0.55, 0.55)
		var dir: Vector2 = Vector2.from_angle(angle)
		_stroke(s, at, dir, length, speed, 2.0, 26 + i * step, 40 + total - (i + 1) * step, "crack", {"spall": i % 2 == 1})
		at += dir * length
		if i == 1:
			var fork: float = angle + (0.95 if D.rand(s) < 0.5 else -0.95)
			var fdir: Vector2 = Vector2.from_angle(fork)
			_stroke(s, at, fdir, 18.0, speed, 1.6, 26 + (i + 1) * step, 40 + total - (i + 2) * step, "crack", {})
			var fat: Vector2 = at + fdir * 18.0
			var f2: Vector2 = Vector2.from_angle(fork + D.rand_range(s, -0.4, 0.4))
			_stroke(s, fat, f2, 16.0, speed, 1.6, 26 + (i + 2) * step, 40 + total - (i + 3) * step, "crack", {"spall": true})

# ---------------------------------------------------------------- Riveting Line
# Steel struts march across the box in a column, each with one gap; the gaps
# drift so the safe path snakes. Two marches per turn: the first sets off from
# behind the left foundation and the second from behind the right, so you can
# follow each train to the next foundation. Rivets drop from the gantry near
# you throughout. Phase 1: hot rivets bounce along the floor.
static func _rivets(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 248.0, "h": 116.0}, 20)
		s.marchGap = 0.0
	for start: int in [40, 250]:
		var dir: float = 1.0 if start == 40 else -1.0
		if t == start:
			D.warn(s, {"kind": "lb_march", "side": -dir}, 36, true)
			D.banner(s, "STRUTS", 36)
			s.marchGap = clampf(float(s.soul.y), -h.y + 22.0, h.y - 22.0)
		var u: int = t - start - 36
		if u >= 0 and u <= 90 and u % 10 == 0:
			if u > 0: s.marchGap = clampf(float(s.marchGap) + D.rand_range(s, -24.0, 24.0), -h.y + 22.0, h.y - 22.0)
			_strut(s, dir, float(s.marchGap), 16.0)
	for b: Dictionary in s.bullets:
		if b.has("strut") and absf(float(b.x)) > h.x + 12.0 and signf(float(b.x)) == signf(float(b.vx)): b.dead = true
	var every: int = 30 if phase == 0 else 26
	if t >= 12 and t <= 380 and t % every == 0:
		var x: float = clampf(float(s.soul.x) + D.rand_range(s, -22.0, 22.0), -h.x + 8.0, h.x - 8.0)
		_rivet(s, x, phase > 0)
	_fire_rivets(s)

static func _strut(s: Dictionary, dir: float, gap: float, gh: float) -> void:
	var h: Vector2 = D.half(s)
	var x: float = -dir * (h.x + 8.0)
	var top: float = -h.y - 4.0
	var bottom: float = h.y + 4.0
	var upper_h: float = (gap - gh - top) * 0.5
	var lower_h: float = (bottom - gap - gh) * 0.5
	D.shot(s, {"space": "box", "x": x, "y": top + upper_h, "vx": dir * 2.4, "collide": "rect", "w": 4.0, "h": upper_h, "shape": "strut", "strut": true, "end": 1, "life": 200})
	D.shot(s, {"space": "box", "x": x, "y": bottom - lower_h, "vx": dir * 2.4, "collide": "rect", "w": 4.0, "h": lower_h, "shape": "strut", "strut": true, "end": -1, "life": 200})

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v) -> void:
	var h: Vector2 = D.half(s)
	var t: int = int(s.clock) - int(s.leadIn)
	# Test floor: faint blueprint grid.
	var x: float = -h.x + fposmod(h.x, 20.0)
	while x < h.x:
		c.draw_line(v.box_point(Vector2(x, -h.y)), v.box_point(Vector2(x, h.y)), Color(0.5, 0.6, 0.75, 0.06), 1)
		x += 20.0
	var y: float = -h.y + fposmod(h.y, 20.0)
	while y < h.y:
		c.draw_line(v.box_point(Vector2(-h.x, y)), v.box_point(Vector2(h.x, y)), Color(0.5, 0.6, 0.75, 0.06), 1)
		y += 20.0
	for w: Dictionary in s.warnings:
		var blink: float = 0.5 + 0.5 * sin(float(w.age) * 0.5)
		match str(w.kind):
			"lb_drop":
				var r: Rect2 = Rect2(Vector2(float(w.x) - float(w.w), -h.y), Vector2(float(w.w) * 2.0, h.y * 2.0))
				c.draw_colored_polygon(v.box_rect_poly(r), Color(ROSE, 0.08 + 0.10 * blink))
				for i: int in range(3):
					v.chevron(c, v.box_point(Vector2(float(w.x), -h.y + 10.0 + i * 8.0 + fposmod(float(w.age), 8.0))), Vector2.DOWN, Color(ROSE, 0.7))
			"lb_rivet":
				_dashed(c, v.box_point(Vector2(float(w.x), -h.y)), v.box_point(Vector2(float(w.x), h.y)), Color(HAZARD, 0.16 + 0.2 * blink))
				c.draw_circle(v.box_point(Vector2(float(w.x), -h.y + 2.0)), 3.0, Color(HAZARD, 0.5 + 0.5 * blink))
			"lb_beam":
				var r2: Rect2 = Rect2(Vector2(-h.x, float(w.y) - float(w.h)), Vector2(h.x * 2.0, float(w.h) * 2.0))
				c.draw_colored_polygon(v.box_rect_poly(r2), Color(ROSE, 0.08 + 0.12 * blink))
	_draw_foundations(c, s, v, t)

static func _draw_foundations(c: CanvasItem, s: Dictionary, v, t: int) -> void:
	for i: int in range(2):
		var at: Vector2 = _foundation(s, i)
		var lit: bool = bool(s.anchorsLit[i])
		var open: bool = s.objectives[i].active
		var failed: bool = not lit and t >= WINDOWS[i] + OPEN
		var base: Vector2 = v.box_point(at + Vector2(0, 6))
		if lit:
			var shelter: PackedVector2Array = v.box_rect_poly(_shelter(s, i))
			c.draw_colored_polygon(shelter, Color(AMBER, 0.08 + 0.03 * sin(float(s.clock) * 0.15)))
			shelter.append(shelter[0])
			_dashed_poly(c, shelter, Color(AMBER, 0.55))
		# A concrete footing with two anchor bolts.
		var footing: PackedVector2Array = PackedVector2Array([base + Vector2(-13, 6), base + Vector2(13, 6), base + Vector2(9, -4), base + Vector2(-9, -4)])
		c.draw_colored_polygon(footing, CONCRETE if not lit else Color("8a7a58"))
		c.draw_polyline(footing + PackedVector2Array([footing[0]]), AMBER if lit else Color(CREAM, 0.35 if not open else 0.6 + 0.4 * sin(float(s.clock) * 0.3)), 1)
		for bx: float in [-5.0, 5.0]:
			c.draw_line(base + Vector2(bx, -4), base + Vector2(bx, -8), STEEL, 2)
		if lit:
			c.draw_circle(base + Vector2(0, 1), 3.0, AMBER)
		elif failed:
			c.draw_polyline(PackedVector2Array([base + Vector2(-8, -3), base + Vector2(-2, 2), base + Vector2(2, -1), base + Vector2(8, 5)]), Color(ROSE, 0.8), 1)
		if open and bool(s.promised):
			var left: float = 1.0 - float(t - WINDOWS[i]) / float(OPEN)
			c.draw_line(base + Vector2(-13, 9), base + Vector2(-13.0 + 26.0 * clampf(left, 0.0, 1.0), 9), AMBER, 2)

static func draw_over(c: CanvasItem, s: Dictionary, v) -> void:
	var h: Vector2 = D.half(s)
	var t: int = int(s.clock) - int(s.leadIn)
	# The gantry above the box, with a trolley and hanging weight per foundation.
	var rail_y: float = -h.y - 46.0
	var a: Vector2 = v.box_point(Vector2(-h.x + 6.0, rail_y))
	var b: Vector2 = v.box_point(Vector2(h.x - 6.0, rail_y))
	c.draw_line(a, b, IRON, 5)
	c.draw_line(a + Vector2(0, -2), b + Vector2(0, -2), STEEL, 1)
	var x: float = a.x + 6.0
	while x < b.x:
		c.draw_line(Vector2(x, a.y - 2), Vector2(x + 6.0, a.y + 2), Color(STEEL, 0.5), 1)
		x += 10.0
	for i: int in range(2):
		var fx: float = _foundation(s, i).x
		var trolley: Vector2 = v.box_point(Vector2(fx, rail_y))
		c.draw_rect(Rect2(trolley - Vector2(6, 4), Vector2(12, 6)), Color("4a4458"))
		if str(s.weightState[i]) != "hang": continue
		var p: float = clampf(float(t - WINDOWS[i]) / float(OPEN), 0.0, 1.0) if t >= WINDOWS[i] else 0.0
		var hang: Vector2 = v.box_point(Vector2(fx, rail_y + 12.0 + 18.0 * p))
		c.draw_line(trolley, hang, Color(CREAM, 0.6), 1)
		_draw_weight(c, hang + Vector2(0, 9), 1.0, p > 0.72 and int(s.clock) % 10 < 5)
	if s.patternId == "crane" and s.has("pivot"):
		# Each load hangs from a trolley riding the gantry rail.
		var pivot: Vector2 = Vector2(s.pivot)
		for bl: Dictionary in s.bullets:
			if not bl.has("ball"): continue
			var ball: Vector2 = Vector2(float(bl.x), float(bl.y))
			var dir: Vector2 = (ball - pivot).normalized()
			var cross: Vector2 = pivot + dir * ((rail_y - pivot.y) / maxf(0.2, dir.y))
			var top: Vector2 = v.box_point(cross)
			var low: Vector2 = v.box_point(pivot + dir * ((-h.y - pivot.y) / maxf(0.2, dir.y)))
			c.draw_line(top, low, Color(CREAM, 0.7), 1)
			if int(bl.ball) == 1: c.draw_line(low, v.box_point(ball), Color(CREAM, 0.3), 1)
			c.draw_rect(Rect2(top - Vector2(7, 5), Vector2(14, 8)), Color(HAZARD if int(bl.ball) == 0 else STEEL, 0.9))
			c.draw_rect(Rect2(top - Vector2(7, 5), Vector2(14, 8)), IRON, false, 1)
	if s.patternId == "rivets":
		# Struts waiting outside the box are drawn as they approach.
		for bl: Dictionary in s.bullets:
			if bl.has("strut") and absf(float(bl.x)) > h.x - 2.0 and signf(float(bl.x)) != signf(float(bl.vx)) and not bl.has("fade"):
				var poly: PackedVector2Array = v.box_rect_poly(Rect2(Vector2(float(bl.x) - 4.0, float(bl.y) - float(bl.h)), Vector2(8.0, float(bl.h) * 2.0)))
				c.draw_colored_polygon(poly, Color(STEEL, 0.35))
	for w: Dictionary in s.warnings:
		var p2: float = float(w.age) / float(w.life)
		match str(w.kind):
			"lb_squeeze":
				for fx2: float in [-0.6, 0.0, 0.6]:
					v.chevron(c, v.box_point(Vector2(h.x * fx2, -h.y - 8.0 + p2 * 4.0)), Vector2.DOWN, Color(ROSE, 0.3 + 0.7 * p2))
					v.chevron(c, v.box_point(Vector2(h.x * fx2, -h.y - 14.0 + p2 * 4.0)), Vector2.DOWN, Color(ROSE, 0.3 + 0.7 * p2))
			"lb_march":
				var side: float = float(w.side)
				for yy: float in [-0.6, 0.0, 0.6]:
					for j: int in range(2):
						v.chevron(c, v.box_point(Vector2(side * (h.x + 10.0 + j * 6.0 - fposmod(float(w.age) * 0.4, 6.0)), h.y * yy)), Vector2(-side, 0), Color(ROSE, 0.4 + 0.6 * p2))

static func _draw_weight(c: CanvasItem, at: Vector2, alpha: float, warn: bool) -> void:
	var r: Rect2 = Rect2(at - Vector2(15, 9), Vector2(30, 18))
	c.draw_rect(r, Color(IRON, alpha))
	c.draw_rect(r, Color(ROSE if warn else STEEL, alpha), false, 1)
	for i: int in range(4):
		var x: float = r.position.x + 3.0 + i * 7.0
		c.draw_line(Vector2(x, r.end.y - 1.0), Vector2(x + 4.0, r.end.y - 5.0), Color(HAZARD, 0.8 * alpha), 2)
	c.draw_line(at + Vector2(-3, -9), at + Vector2(0, -12), Color(STEEL, alpha), 1)
	c.draw_line(at + Vector2(3, -9), at + Vector2(0, -12), Color(STEEL, alpha), 1)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v) -> bool:
	match str(b.shape):
		"weight":
			_draw_weight(c, at, alpha, false)
			return true
		"cable":
			var half: Vector2 = Vector2(float(b.w), 0).rotated(turn)
			var lit: bool = int(b.age) > int(b.arm)
			c.draw_line(at - half, at + half, Color(CREAM if lit else ROSE, alpha * (0.9 if lit else 0.4)), 2.0)
			return true
		"ball":
			var armed: bool = int(b.age) > int(b.arm)
			var r: float = float(b.r)
			c.draw_circle(at, r, Color(IRON, alpha))
			c.draw_arc(at, r, 0, TAU, 24, Color(STEEL if armed else Color(ROSE, 0.5 + 0.5 * sin(float(b.age) * 0.5)), alpha), 2)
			c.draw_circle(at + Vector2(-r * 0.35, -r * 0.35), r * 0.25, Color(CREAM, 0.35 * alpha))
			return true
		"girder":
			var hw: float = float(b.w); var hh: float = float(b.h)
			var body: PackedVector2Array = v.quad(at, hw, hh, turn)
			c.draw_colored_polygon(body, Color(Color("8c5a3a") if not b.get("swung", false) else Color("9a6a40"), alpha))
			c.draw_line(at + Vector2(-hw, -hh + 1).rotated(turn), at + Vector2(hw, -hh + 1).rotated(turn), Color(HAZARD, alpha), 2)
			c.draw_line(at + Vector2(-hw, hh - 1).rotated(turn), at + Vector2(hw, hh - 1).rotated(turn), Color(HAZARD, alpha), 2)
			var x: float = -hw + 5.0
			while x < hw - 2.0:
				c.draw_circle(at + Vector2(x, 0).rotated(turn), 1.0, Color(IRON, alpha))
				x += 8.0
			if b.get("lift", false) or b.get("swung", false):
				c.draw_line(at + Vector2(0, -hh).rotated(turn), at + Vector2(0, -hh - 140.0).rotated(turn), Color(CREAM, 0.5 * alpha), 1)
			return true
		"shard", "chip":
			var tri: PackedVector2Array = PackedVector2Array([at + Vector2(0, -3.5).rotated(turn), at + Vector2(3.5, 2.5).rotated(turn), at + Vector2(-3.5, 2.5).rotated(turn)])
			c.draw_colored_polygon(tri, Color(Color("a8a39b") if b.shape == "shard" else DUST, alpha))
			return true
		"rivet", "bolt":
			c.draw_circle(at, 3.0, Color(Color("f0c070") if b.shape == "rivet" else STEEL, alpha))
			c.draw_circle(at, 1.2, Color(IRON, alpha))
			if b.shape == "rivet":
				c.draw_line(at + Vector2(0, -3), at + Vector2(0, -8), Color(HAZARD, 0.5 * alpha), 2)
			return true
		"crack":
			var k: Dictionary = b.stroke
			var o: Vector2 = Vector2(float(k.ox), float(k.oy))
			var d: Vector2 = Vector2(float(k.dx), float(k.dy))
			var a: Vector2 = v.box_point(o)
			if int(b.age) <= int(k.warn):
				var blink: float = 0.3 + 0.25 * sin(float(b.age) * 0.5)
				_dashed(c, a, v.box_point(o + d * float(k.len)), Color(DUST, blink * alpha))
				return true
			var head: Vector2 = v.box_point(o + d * float(k.cur))
			c.draw_line(a, head, Color(Color("d8c6a8"), alpha), float(b.h) * 2.0 + 1.0)
			c.draw_line(a, head, Color(Color("2a2220"), alpha), 1.0)
			return true
		"strut":
			var hw2: float = float(b.w); var hh2: float = float(b.h)
			var poly: PackedVector2Array = v.quad(at, hw2, hh2, turn)
			c.draw_colored_polygon(poly, Color(STEEL, alpha))
			c.draw_line(at + Vector2(-hw2 + 1, -hh2).rotated(turn), at + Vector2(-hw2 + 1, hh2).rotated(turn), Color(IRON, alpha), 1)
			c.draw_line(at + Vector2(hw2 - 1, -hh2).rotated(turn), at + Vector2(hw2 - 1, hh2).rotated(turn), Color(IRON, alpha), 1)
			var tip: Vector2 = at + Vector2(0, hh2 * float(b.end)).rotated(turn)
			c.draw_line(tip + Vector2(-6, 0).rotated(turn), tip + Vector2(6, 0).rotated(turn), Color(HAZARD, alpha), 3)
			var y: float = -hh2 + 6.0
			while y < hh2 - 3.0:
				c.draw_circle(at + Vector2(0, y).rotated(turn), 1.0, Color(IRON, alpha))
				y += 9.0
			return true
	return false

static func _dashed(c: CanvasItem, a: Vector2, b: Vector2, color: Color) -> void:
	var length: float = a.distance_to(b)
	var dir: Vector2 = (b - a) / maxf(1.0, length)
	var x: float = 0.0
	while x < length:
		c.draw_line(a + dir * x, a + dir * minf(length, x + 5.0), color, 1)
		x += 9.0

static func _dashed_poly(c: CanvasItem, poly: PackedVector2Array, color: Color) -> void:
	for i: int in range(poly.size() - 1):
		_dashed(c, poly[i], poly[i + 1], color)
