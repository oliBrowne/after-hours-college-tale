extends RefCounted
## HACKY-SACK HIPPIE / a wandering campus fight. The sack has been in the air for forty
## minutes. Three slow, telegraphed attacks, one per turn, cycling in order: circle up
## (sacks kicked across), drum circle (beat-timed rings), patchouli (drifting haze).
## Phase 1 is the same three a little denser.
## The promise "Keep the sack up": a friendly green sack arcs back and forth over the box
## (it is the same path in every attack, so the danger can plan around it). Stand in it
## and press confirm three times while promised.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["circle_up", "drum_circle", "patchouli"]
const PHASES: Array[int] = [0, 1]
const KEEPS: int = 3
const PASS: int = 110
const GRAV: float = 0.018

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const BLUE: Color = Color("8fb3ea")
const LILAC: Color = Color("a68db8")
const ROSE: Color = Color("e8837b")
const SHIRTS: Array[Color] = [Color("e8b45c"), Color("a68db8"), Color("e8837b"), Color("8fb3ea")]

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 400 + 40 * clampi(int(s.phase), 0, 1)
	s.bannerColor = AMBER
	s.tells = []
	s.kick = -99
	match id:
		"circle_up":
			s.phaseName = "Circle Up"
			s.hint = "Sacks get kicked along dotted arcs. Stay off them. Confirm when the green sack passes."
		"drum_circle":
			s.phaseName = "Drum Circle"
			s.hint = "Drums boom on the beat and send rings. Slip through the gap. Confirm on the green sack."
		"patchouli":
			s.phaseName = "Patchouli"
			s.hint = "Slow haze drifts in. Float around it. Confirm when the green sack passes by."
	for i: int in range(KEEPS):
		D.objective(s, {"kind": "confirm", "r": 13.0, "label": "sack" if i == 0 else "", "active": false})

## Where the friendly sack is at a tick: a long lob between the left and right sides,
## highest in the middle, where it moves slowest. Same for every objective.
static func _sack(s: Dictionary, tick: int) -> Vector2:
	var h: Vector2 = D.half(s)
	var n: int = int(tick / PASS)
	var u: float = float(tick % PASS) / float(PASS)
	var dir: float = 1.0 if n % 2 == 0 else -1.0
	return Vector2(dir * (2.0 * u - 1.0) * 0.72 * h.x, (0.5 - 0.95 * 4.0 * u * (1.0 - u)) * h.y)

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return _kept(s) >= KEEPS

static func progress(s: Dictionary) -> String:
	return "Sack kept up %d/%d" % [_kept(s), KEEPS]

static func _kept(s: Dictionary) -> int:
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	return count

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	_follow(s, t)
	match str(s.patternId):
		"circle_up": _circle_up(s, t, phase)
		"drum_circle": _drum_circle(s, t, phase)
		"patchouli": _patchouli(s, t, phase)

static func after(_s: Dictionary, _t: int) -> void:
	pass

## One objective at a time rides the sack; the next shows 24 ticks after the last.
static func _follow(s: Dictionary, t: int) -> void:
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		var spot: Vector2 = _sack(s, t)
		o.x = spot.x; o.y = spot.y
		var ready: bool = t >= 40 if i == 0 else last_done >= 0 and int(s.clock) - last_done >= 24
		o.active = ready
		if ready and not bool(o.get("shown", false)):
			o.shown = true
			D.effect(s, "pulse", D.to_world(s, spot), 18)
		return

## How near a path (points every `step` ticks from tick t0) comes to the friendly sack.
static func _clearance(s: Dictionary, t0: int, pts: PackedVector2Array, step: int) -> float:
	var best: float = 999.0
	for k: int in range(pts.size()):
		best = minf(best, pts[k].distance_to(_sack(s, t0 + k * step)))
	return best

# ---------------------------------------------------------------- attacks

## The four players sit at the box corners: low left, high left, low right, high right.
static func _player(s: Dictionary, i: int) -> Vector2:
	var h: Vector2 = D.half(s)
	return Vector2((-1.0 if i < 2 else 1.0) * (h.x - 10.0), (0.55 if i % 2 == 0 else -0.55) * h.y)

## How near a path comes to where you stand now (the fight route aims at you).
static func _soul_gap(s: Dictionary, pts: PackedVector2Array) -> float:
	var best: float = 999.0
	for p: Vector2 in pts:
		best = minf(best, p.distance_to(Vector2(float(s.soul.x), float(s.soul.y))))
	return best

## Circle Up: a player kicks the sack across to a player on the other side. The arc
## is dotted for a moment first. Of a few random passes, the one that stays clear
## of the green sack is used.
static func _circle_up(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
		D.banner(s, "FORTY MINUTES", 70)
	var every: int = 56 - 10 * phase
	if t % every == 24 and t < int(s.length) - 150:
		var flight: int = 105 - 10 * phase
		var best: Dictionary = {}
		var far: float = -1.0
		for k: int in range(4):
			var from: int = int(D.rand(s) * 4.0) % 4
			var to: int = (2 if from < 2 else 0) + int(D.rand(s) * 2.0) % 2
			var a: Vector2 = _player(s, from)
			var b: Vector2 = _player(s, to)
			var vx: float = (b.x - a.x) / float(flight)
			var vy: float = (b.y - a.y - 0.5 * GRAV * flight * flight) / float(flight)
			var pts: PackedVector2Array = PackedVector2Array()
			for j: int in range(0, flight + 1, 7):
				pts.append(a + Vector2(vx * j, vy * j + 0.5 * GRAV * j * (j + 1)))
			var score: float = minf(_clearance(s, t + 36, pts, 7), 40.0) if bool(s.promised) else 60.0 - _soul_gap(s, pts)
			score += D.rand(s) * 4.0
			if score > far:
				far = score; best = {"from": from, "a": a, "vx": vx, "vy": vy, "pts": pts}
		s.kick = int(s.clock) + 36
		s.kicker = best.from
		D.effect(s, "pulse", D.to_world(s, best.a), 20)
		s.tells.append({"pts": best.pts, "start": int(s.clock) + 36, "until": int(s.clock) + 36 + flight})
		D.warn(s, {"kind": "ding"}, 36, true)
		D.shot(s, {"space": "box", "x": best.a.x, "y": best.a.y, "vx": best.vx, "vy": best.vy, "ay": GRAV, "r": 4.5, "shape": "sack", "spin": 0.1, "hold": true, "arm": 36, "life": 36 + flight + 80})

## Drum Circle: on every second downbeat a drum booms and a slow ring grows from it,
## ghosted for the first half second. The gap is aimed at where the green sack will
## be when the ring gets there (or beside you when you are not promised).
static func _drum_circle(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
	var downbeat: bool = (int(s.clock) + int(s.musicBase)) % int(s.beatTicks) == 0
	if downbeat and (phase > 0 or int(s.beat) % 2 == 0) and t >= 30 and t < int(s.length) - 150:
		var turn: int = int(s.beat) if phase > 0 else int(int(s.beat) / 2)
		_ring(s, t, phase, turn % 2, turn)

static func _ring(s: Dictionary, t: int, phase: int, side: int, turn: int) -> void:
	var h: Vector2 = D.half(s)
	var grow: float = 0.7 + 0.1 * phase
	var at: Vector2 = Vector2((-0.72 if side == 0 else 0.72) * h.x, 0.5 * h.y - 4.0)
	var beside: Vector2 = Vector2(float(s.soul.x) + (70.0 if float(s.soul.x) < 0.0 else -70.0), float(s.soul.y))
	var aim: float = (beside - at).angle()
	if bool(s.promised):
		var travel: float = 100.0
		for k: int in range(3):
			travel = maxf(0.0, (_sack(s, t + int(travel)) - at).length() - 10.0) / grow
		aim = (_sack(s, t + int(travel)) - at).angle()
	D.warn(s, {"kind": "ding"}, 30, side == turn % 2)
	D.shot(s, {"space": "box", "x": at.x, "y": at.y, "collide": "ring", "shape": "drumring", "radius": 10.0, "grow": grow, "thick": 2.4, "gap": aim, "gapWidth": 1.7, "maxRadius": 150.0 - 30.0 * phase, "arm": 30, "life": 400})

## Patchouli: slow clouds of haze drift in from the sides, swaying. Touching one
## costs a hit and the cloud is gone, so nothing lingers on you.
static func _patchouli(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
		D.banner(s, "GOOD VIBES", 70)
	var every: int = 84 - 18 * phase
	if t % every == 20 and t < int(s.length) - 170:
		var h: Vector2 = D.half(s)
		var n: int = int(t / every)
		var side: float = 1.0 if n % 2 == 0 else -1.0
		var y: float = D.rand_range(s, -0.7, 0.7) * h.y
		if not bool(s.promised): y = clampf(float(s.soul.y) + D.rand_range(s, -10.0, 10.0), -0.8 * h.y, 0.8 * h.y)
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": y, "dir": Vector2(-side, 0)}, 36, true)
		D.shot(s, {"space": "box", "x": side * (h.x + 20.0), "y": y, "vx": -side * 0.6, "vy": 0.0, "r": 11.0, "shape": "haze", "pierce": false, "hold": true, "arm": 36, "life": 36 + 460, "wave": {"amp": 7.0, "freq": 0.05, "phase": D.rand(s) * TAU}})

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var now: int = int(s.clock)
	match str(s.patternId):
		"circle_up":
			for i: int in range(4):
				var kicking: bool = now >= int(s.kick) - 12 and now < int(s.kick) + 10 and int(s.get("kicker", -1)) == i
				_hippie(c, v.box_point(_player(s, i)), SHIRTS[i], -1.0 if i < 2 else 1.0, kicking)
		"drum_circle":
			var h: Vector2 = D.half(s)
			var bt: int = int(s.beatTicks)
			var pulse: float = float((now + int(s.musicBase)) % bt) / float(bt)
			for side: float in [-0.72, 0.72]:
				var at: Vector2 = v.box_point(Vector2(side * h.x, 0.5 * h.y + 2.0))
				c.draw_colored_polygon(PackedVector2Array([at + Vector2(-7, 0), at + Vector2(7, 0), at + Vector2(5, 13), at + Vector2(-5, 13)]), Color(ROSE, 0.55))
				c.draw_line(at + Vector2(-6, 6), at + Vector2(6, 6), Color(CREAM, 0.35), 1)
				c.draw_circle(at, 7.0, Color(CREAM, 0.45))
				c.draw_arc(at, 7.0 + 5.0 * pulse, 0.0, TAU, 14, Color(AMBER, 0.6 * (1.0 - pulse)), 1)
		"patchouli":
			var h2: Vector2 = D.half(s)
			for side2: float in [-1.0, 1.0]:
				# An incense stick in the corner, with a thin curl of smoke.
				var base: Vector2 = v.box_point(Vector2(side2 * (h2.x - 12.0), h2.y - 2.0))
				c.draw_line(base, base + Vector2(0, -14), Color(AMBER, 0.6), 2)
				var smoke: PackedVector2Array = PackedVector2Array()
				for k: int in range(8):
					smoke.append(base + Vector2(sin(float(now) * 0.06 + k * 0.9) * (2.0 + k * 0.5), -15.0 - k * 4.0))
				c.draw_polyline(smoke, Color(LILAC, 0.3), 1)
	# The green sack and where it will be next, as a little dotted lead.
	for o: Dictionary in s.objectives:
		if bool(s.promised) and o.active and not o.done:
			for k: int in range(1, 5):
				c.draw_circle(v.box_point(_sack(s, now - int(s.leadIn) + k * 8)), 1.2, Color(MINT, 0.5 - 0.1 * k))
			_sack_art(c, v.box_point(Vector2(float(o.x), float(o.y))), float(now) * 0.08, Color(MINT, 0.95), Color(INK, 0.9))
	for k2: Dictionary in s.tells:
		if now >= int(k2.until): continue
		var before: bool = now < int(k2.start)
		var fade: float = 1.0 if before else clampf(float(int(k2.until) - now) / 20.0, 0.0, 1.0)
		var pts: PackedVector2Array = k2.pts
		for i2: int in range(pts.size()):
			c.draw_circle(v.box_point(pts[i2]), 1.6, Color(ROSE if before else AMBER, (0.7 + 0.3 * sin(float(now) * 0.4 + i2)) * fade))

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, _v: Node2D) -> bool:
	match str(b.shape):
		"sack":
			_sack_art(c, at, turn, Color(ROSE, alpha), Color(CREAM, alpha))
			return true
		"drumring":
			var gw: float = float(b.gapWidth) * 0.5
			var ghost: float = 0.3 if int(b.age) <= int(b.arm) else 1.0
			var steps: int = maxi(24, int(float(b.radius) * 0.6))
			c.draw_arc(at, float(b.radius), float(b.gap) + gw, float(b.gap) + TAU - gw, steps, Color(LILAC, 0.95 * alpha * ghost), 5)
			c.draw_arc(at, float(b.radius) + 1.5, float(b.gap) + gw, float(b.gap) + TAU - gw, steps, Color(AMBER, 0.75 * alpha * ghost), 1)
			return true
		"haze":
			# A puff of smoke: a few soft lobes around a core the size of the hitbox.
			var r: float = float(b.r)
			var drift: float = float(b.age) * 0.04
			var ghost2: float = 0.5 if int(b.age) <= int(b.arm) else 1.0
			for k: int in range(5):
				var a: float = drift + k * TAU / 5.0
				c.draw_circle(at + Vector2.from_angle(a) * r * 0.55, r * 0.62, Color(LILAC if k % 2 == 0 else BLUE, 0.34 * alpha * ghost2))
			c.draw_circle(at, r * 0.9, Color(MINT, 0.3 * alpha * ghost2))
			c.draw_arc(at, r, drift, drift + 4.2, 16, Color(CREAM, 0.75 * alpha * ghost2), 1)
			c.draw_arc(at, r * 0.55, drift + 2.0, drift + 5.5, 10, Color(CREAM, 0.5 * alpha * ghost2), 1)
			return true
	return false

## A hacky sack: a round bag with stitched seams.
static func _sack_art(c: CanvasItem, at: Vector2, turn: float, body: Color, stitch: Color) -> void:
	c.draw_circle(at, 4.6, body)
	c.draw_arc(at, 4.6, 0.0, TAU, 12, stitch, 1)
	c.draw_arc(at + Vector2(-4.5, 0).rotated(turn), 4.5, -0.9 + turn, 0.9 + turn, 6, stitch, 1)
	c.draw_arc(at + Vector2(4.5, 0).rotated(turn), 4.5, PI - 0.9 + turn, PI + 0.9 + turn, 6, stitch, 1)
	for k: int in range(3):
		c.draw_line(at + Vector2(-1.2, -2.0 + k * 2.0).rotated(turn), at + Vector2(1.2, -2.0 + k * 2.0).rotated(turn), stitch, 1)

## A sitting hippie in a tie-dye shirt with a headband; one foot kicks when it is their pass.
static func _hippie(c: CanvasItem, at: Vector2, shirt: Color, face: float, kicking: bool) -> void:
	c.draw_circle(at + Vector2(0, -1), 5.5, Color(shirt, 0.55))
	c.draw_arc(at + Vector2(0, -1), 3.0, 0.3, 2.8, 8, Color(CREAM, 0.5), 1)
	c.draw_circle(at + Vector2(0, -8.5), 3.0, Color(CREAM, 0.7))
	c.draw_line(at + Vector2(-3, -9.5), at + Vector2(3, -9.5), Color(ROSE, 0.8), 1)
	c.draw_arc(at + Vector2(0, -8.5), 3.4, PI, TAU, 8, Color(AMBER, 0.6), 2)
	var foot: Vector2 = Vector2(face * 11.0, -5.0 if kicking else 3.0)
	c.draw_line(at + Vector2(face * 3.0, 2.0), at + foot, Color(CREAM, 0.6), 2)
