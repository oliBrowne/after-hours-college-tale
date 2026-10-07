extends RefCounted
## EMPTY CHAIR: "Keep the seat clear. Rest by the little lantern. You do not
## have to fill every gap." Four handmade attacks, one per turn, cycling. The
## promise never changes: stay in the lantern's quiet pocket for 120 ticks
## while promised, and never enter the empty seat (a plum avoid zone; entering
## it breaks the promise). The pocket shelters you, so every attack is about the
## pocket moving, going dark or being crowded, and about the space around the
## seat, which pulls at you like something wanting to be filled.
## Phase 1 (from the second turn) adds a layer to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["lantern", "lamps", "guests", "make_room"]
const PHASES: Array[int] = [0, 1]
const LENGTH: int = 420
const NEED: int = 120

const AMBER: Color = Color("e8b45c")
const CREAM: Color = Color("e6d6b1")
const MINT: Color = Color("b9d5bc")
const PLUM: Color = Color("6b526a")
const ROSE: Color = Color("e8837b")
const LILAC: Color = Color("a68db8")
const DUST: Color = Color("cfc3b0")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = LENGTH
	s.quietTicks = 0
	s.chairEntered = false
	s.pocket = Rect2(-106, 10, 58, 40)
	s.pocketLit = true
	s.flicker = -1
	s.lamps = []
	s.lamp = 0
	s.nextLamp = -1
	s.chairPath = []
	s.chairGhost = null
	s.pull = 0.0
	s.bannerColor = AMBER
	# The soul starts beside the little lantern.
	s.soul.x = -80.0; s.soul.y = 30.0
	D.objective(s, {"kind": "avoid", "x": 0.0, "y": 0.0, "w": 24.0, "h": 28.0, "always": true, "chair": true})
	match id:
		"lantern":
			s.phaseName = "Little Lantern"
			s.hint = "The lantern walks around the seat. Stay in its light; dust falls outside it."
			s.pocket = _rect_at(_orbit_point(0), Vector2(26, 19))
			s.pull = 0.24
		"lamps":
			s.phaseName = "Three Lamps"
			s.hint = "One lamp at a time. Move when the next one blinks. Slip through the hush rings."
			s.lamps = [Vector2(-80, 28), Vector2(0, -42), Vector2(80, 28)]
			s.pocket = _rect_at(s.lamps[0], Vector2(26, 16))
		"guests":
			s.phaseName = "Who Could Sit"
			s.hint = "Possible guests walk to the seat. Let them pass. Follow the lantern along the floor."
			s.pocket = _rect_at(Vector2(-80, 32), Vector2(26, 18))
			s.pull = 0.24
		"make_room":
			s.phaseName = "Make Room"
			s.hint = "The empty space moves where it likes. Step aside, then come back to the light."
			s.chairPath = [[60, 110, Vector2(-60, 22)], [170, 230, Vector2(66, -14)], [290, 340, Vector2(-60, 22)], [380, 420, Vector2(0, 0)]]

static func _rect_at(centre: Vector2, half: Vector2) -> Rect2:
	return Rect2(centre - half, half * 2.0)

static func _chair(s: Dictionary) -> Dictionary:
	return s.objectives[0]

static func _chair_rect(s: Dictionary) -> Rect2:
	var o: Dictionary = _chair(s)
	return Rect2(float(o.x) - float(o.w), float(o.y) - float(o.h), float(o.w) * 2.0, float(o.h) * 2.0)

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return int(s.quietTicks) >= NEED and not s.chairEntered

static func preview(_s: Dictionary, _phase: int) -> void:
	pass

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = int(s.phase)
	match str(s.patternId):
		"lantern": _lantern(s, t, phase)
		"lamps": _lamps(s, t, phase)
		"guests": _guests(s, t, phase)
		"make_room": _make_room(s, t, phase)
	# The empty seat pulls at you a little.
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var chair: Rect2 = _chair_rect(s)
	# (It lets go a little way from the seat's edge.)
	var toward: Vector2 = (chair.get_center() - soul)
	s.wind = (toward.normalized() * float(s.pull) if _rect_distance(chair, soul) >= 12.0 else Vector2.ZERO).rotated(float(s.box.rot))
	_quiet(s, soul, chair)

static func _quiet(s: Dictionary, soul: Vector2, chair: Rect2) -> void:
	var pocket: Rect2 = s.pocket
	s.safe = [pocket] if s.pocketLit else []
	if bool(s.promised) and s.pocketLit and pocket.has_point(soul) and not chair.has_point(soul) and not s.chairEntered:
		s.quietTicks = int(s.quietTicks) + 1
		if int(s.quietTicks) == NEED:
			s.objectiveChanged = true
			D.effect(s, "kept", D.to_world(s, pocket.get_center()), 40)
	# Autopilot: rest in the lit part of the pocket that the seat does not cover.
	var goal: Vector2 = pocket.get_center()
	if s.pocketLit: goal = _free_spot(pocket, chair)
	if int(s.nextLamp) >= 0: goal = Vector2(s.lamps[int(s.nextLamp)])
	if s.chairGhost != null or not s.pocketLit:
		# Wait beside the pocket, clear of where the seat is (or is going).
		var seat: Rect2 = chair if s.chairGhost == null else Rect2(Vector2(s.chairGhost) - chair.size * 0.5, chair.size)
		goal = _aside(s, pocket.get_center(), seat.merge(chair) if s.chairGhost != null else seat)
	s.botGoal = _lead(soul, _around(soul, goal, chair))

## Autopilot waypoint: go round the seat's corner instead of through it.
static func _around(from: Vector2, to: Vector2, seat: Rect2) -> Vector2:
	var wide: Rect2 = seat.grow(10.0)
	var blocked: bool = false
	var n: int = int(from.distance_to(to) / 4.0) + 1
	for i: int in range(n + 1):
		if wide.has_point(from.lerp(to, float(i) / n)): blocked = true; break
	if not blocked or wide.has_point(from): return to
	var corners: Array[Vector2] = [seat.grow(20.0).position, seat.grow(20.0).end, Vector2(seat.grow(20.0).position.x, seat.grow(20.0).end.y), Vector2(seat.grow(20.0).end.x, seat.grow(20.0).position.y)]
	var best: Vector2 = to
	var best_d: float = INF
	for c: Vector2 in corners:
		var d: float = from.distance_to(c) + c.distance_to(to)
		if d < best_d: best_d = d; best = c
	return best

## The autopilot plans whole 18-tick runs and stops ~17 px short of its goal,
## so aim it a little past the spot along the way in.
static func _lead(soul: Vector2, target: Vector2) -> Vector2:
	var d: Vector2 = target - soul
	return target + d.normalized() * 15.0 if d.length() > 2.0 else target

static func _aside(s: Dictionary, from: Vector2, seat: Rect2) -> Vector2:
	var h: Vector2 = D.half(s) - Vector2(6, 6)
	if _rect_distance(seat, from) >= 14.0: return from
	var best: Vector2 = from
	var best_cost: float = INF
	for i: int in range(16):
		var dir: Vector2 = Vector2.from_angle(i * TAU / 16.0)
		for step: int in range(1, 12):
			var p: Vector2 = (from + dir * step * 8.0).clamp(-h, h)
			if _rect_distance(seat, p) >= 14.0:
				var cost: float = from.distance_to(p)
				if cost < best_cost: best_cost = cost; best = p
				break
	return best

static func _free_spot(pocket: Rect2, chair: Rect2) -> Vector2:
	var centre: Vector2 = pocket.get_center()
	if not pocket.intersects(chair.grow(6.0)): return centre
	var best: Vector2 = centre
	var best_d: float = -INF
	for fx: float in [0.15, 0.5, 0.85]:
		for fy: float in [0.2, 0.5, 0.8]:
			var p: Vector2 = pocket.position + pocket.size * Vector2(fx, fy)
			var d: float = _rect_distance(chair, p)
			if d > best_d: best_d = d; best = p
	return best

static func _rect_distance(r: Rect2, p: Vector2) -> float:
	var dx: float = maxf(r.position.x - p.x, p.x - r.end.x)
	var dy: float = maxf(r.position.y - p.y, p.y - r.end.y)
	return maxf(dx, dy)

static func after(s: Dictionary, _t: int) -> void:
	if _chair(s).broken and not s.chairEntered:
		s.chairEntered = true
		D.banner(s, "THE SEAT WAS FILLED", 60)
		s.bannerColor = ROSE

# ---------------------------------------------------------------- little lantern

static func _orbit_point(t: int) -> Vector2:
	var a: float = PI * 0.82 + maxf(0.0, float(t - 40)) * 0.0118
	return Vector2(cos(a) * 84.0, sin(a) * 37.0)

## Little Lantern: the light walks an ellipse around the seat; dust motes fall
## in marked columns, aimed where you stand. At the top and bottom of its walk
## the light passes the seat, so only a strip of it is yours. Phase 1: moths
## circle the lantern, and it gutters (goes dark) three times.
static func _lantern(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 248.0, "h": 118.0}, 24)
		if phase > 0:
			for i: int in range(5):
				D.shot(s, {"space": "box", "orbit": {"ox": 0.0, "oy": 0.0, "radius": 36.0, "angle": i * TAU / 5.0, "av": 0.045}, "arm": 40, "r": 2.5, "shape": "moth", "life": 900, "moth": true})
	var centre: Vector2 = _orbit_point(t)
	s.pocket = _rect_at(centre, Vector2(26, 19))
	if phase > 0:
		for b: Dictionary in s.bullets:
			if b.get("moth", false):
				b.orbit.ox = centre.x; b.orbit.oy = centre.y
				b.orbit.radius = 36.0 + 4.0 * sin(float(b.age) * 0.06)
		for g: int in [110, 230, 350]:
			if t == g - 30:
				s.flicker = t
				D.banner(s, "THE LANTERN GUTTERS", 30)
				D.warn(s, {"kind": "none"}, 1, true)
			if t == g: s.pocketLit = false
			if t == g + 40: s.pocketLit = true; s.flicker = -1
	if t % 12 == 6 and t > 20 and t < 396:
		var aimed: bool = int(t / 12) % 2 == 0
		var x: float = float(s.soul.x) + D.rand_range(s, -5.0, 5.0) if aimed else D.rand_range(s, -h.x + 10.0, h.x - 10.0)
		x = clampf(x, -h.x + 8.0, h.x - 8.0)
		s.columns = s.get("columns", [])
		s.columns.append({"x": x, "at": t + 34})
		D.warn(s, {"kind": "column", "x": x, "w": 8.0}, 34)
	for col: Dictionary in s.get("columns", []):
		var since: int = t - int(col.at)
		if since >= 0 and since < 30 and since % 4 == 0:
			D.shot(s, {"space": "box", "x": float(col.x) + D.rand_range(s, -3.0, 3.0), "y": -h.y - 4.0, "vy": 2.5, "r": 2.6, "shape": "mote", "wave": {"amp": 2.5, "freq": 0.12, "phase": D.rand(s) * TAU}, "life": 80})

# ---------------------------------------------------------------- three lamps

## Three Lamps: one lamp is lit at a time; the next blinks before it takes
## over and the old one goes dark. Hush rings spread from the seat with one gap
## each, and programmes drift across. Phase 1: the lamps change faster and the
## rings come in pairs with offset gaps.
static func _lamps(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0: D.box_to(s, {"w": 248.0, "h": 118.0}, 24)
	var switches: Array = [90, 180, 270] if phase > 0 else [130, 260]
	var order: Array[int] = [0, 1, 2, 1, 0]
	for i: int in range(switches.size()):
		if t == int(switches[i]) - 50:
			s.nextLamp = order[i + 1]
			D.warn(s, {"kind": "none"}, 1, true)
		if t == int(switches[i]):
			s.lamp = order[i + 1]
			s.nextLamp = -1
			s.pocket = _rect_at(s.lamps[int(s.lamp)], Vector2(26, 16))
	var every: int = 50
	if t % every == 20 and t < 390:
		_hush(s, 0.0)
	if phase > 0 and t % every == 34 and t < 390:
		_hush(s, 0.8 if int(t / every) % 2 == 0 else -0.8)
	if t % 30 == 0 and t > 20 and t < 400:
		var from: float = -1.0 if D.rand(s) < 0.5 else 1.0
		var y: float = D.rand_range(s, -h.y + 10.0, h.y - 10.0)
		if int(t / 30) % 3 == 0: y = clampf(float(s.soul.y), -h.y + 10.0, h.y - 10.0)
		D.warn(s, {"kind": "edge", "space": "box", "x": from * (h.x - 4.0), "y": y, "dir": Vector2(-from, 0)}, 30)
		D.shot(s, {"space": "box", "x": from * (h.x + 10.0 + 1.6 * 30.0), "y": y, "vx": -from * 1.6, "collide": "rect", "w": 5.0, "h": 4.0, "shape": "programme", "rot": 0.0, "spin": 0.03, "wave": {"amp": 4.0, "freq": 0.07, "phase": D.rand(s) * TAU}, "life": 260})

static func _hush(s: Dictionary, offset: float) -> void:
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var gap: float = soul.angle() + D.rand_range(s, 0.45, 0.9) * (-1.0 if D.rand(s) < 0.5 else 1.0) + offset
	D.shot(s, {"space": "box", "x": 0.0, "y": 0.0, "collide": "ring", "radius": 24.0, "grow": 1.25, "thick": 2.0, "gap": gap, "gapWidth": 0.85, "shape": "ring", "maxRadius": 150.0})
	D.effect(s, "pulse", D.to_world(s, Vector2.ZERO), 14)

# ---------------------------------------------------------------- who could sit

## Who Could Sit: faint outlines of people who might have taken the seat fade
## in at the edges, then walk to it and dissolve. Some walk the line through
## you. The lantern slides along the floor, under the seat and back. Phase 1:
## guests turn away at the seat and walk back out, faster.
static func _guests(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0: D.box_to(s, {"w": 248.0, "h": 118.0}, 24)
	var x: float = -80.0 * cos(maxf(0.0, float(t - 40)) * 0.0105)
	s.pocket = _rect_at(Vector2(x, 32), Vector2(26, 18))
	var every: int = 10 if phase > 0 else 9
	if t % every == 0 and t > 10 and t < 380:
		var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
		var dir: Vector2
		if int(t / every) % 3 == 0 and soul.length() > 30.0:
			dir = soul.normalized().rotated(D.rand_range(s, -0.08, 0.08))
		else:
			dir = Vector2.from_angle(D.rand(s) * TAU)
		var start: Vector2 = _edge_point(h, dir)
		var speed: float = 0.9
		var v: Vector2 = -start.normalized() * speed
		D.shot(s, {"space": "box", "x": start.x, "y": start.y, "vx": v.x, "vy": v.y, "hold": true, "arm": 36, "r": 4.5, "shape": "guest", "life": 300, "guest": true})
	var chair: Rect2 = _chair_rect(s).grow(2.0)
	for b: Dictionary in s.bullets:
		if not b.get("guest", false) or b.get("left", false): continue
		if chair.has_point(Vector2(float(b.x), float(b.y))):
			if phase > 0:
				b.left = true
				b.vx = -float(b.vx) * 1.5; b.vy = -float(b.vy) * 1.5
				D.effect(s, "block", D.to_world(s, Vector2(float(b.x), float(b.y))), 12)
			else:
				b.dead = true
				D.effect(s, "graze", D.to_world(s, Vector2(float(b.x), float(b.y))), 14)

static func _edge_point(h: Vector2, dir: Vector2) -> Vector2:
	var sx: float = (h.x - 6.0) / maxf(0.001, absf(dir.x))
	var sy: float = (h.y - 6.0) / maxf(0.001, absf(dir.y))
	return dir * minf(sx, sy)

# ---------------------------------------------------------------- make room

## Make Room: the empty space drifts on its own schedule (its next place is
## outlined first), twice settling over the lantern so you must step aside.
## Folding chairs slide along marked rows, and each time the seat settles it
## sets out a ring of chairs. Phase 1: rows come in pairs, rings are fuller.
static func _make_room(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0: D.box_to(s, {"w": 248.0, "h": 118.0}, 24)
	var o: Dictionary = _chair(s)
	var from: Vector2 = Vector2(0, 0)
	s.chairGhost = null
	for leg: Array in s.chairPath:
		var start: int = int(leg[0]); var stop: int = int(leg[1]); var to: Vector2 = leg[2]
		if t >= start - 50 and t < start:
			s.chairGhost = to
			if t == start - 50: D.warn(s, {"kind": "none"}, 1, true)
		if t >= start and t <= stop:
			var p: float = float(t - start) / float(stop - start)
			p = p * p * (3.0 - 2.0 * p)
			var at: Vector2 = from.lerp(to, p)
			o.x = at.x; o.y = at.y
			if t == stop:
				var count: int = 12 if phase > 0 else 8
				var spin: float = D.rand(s) * TAU
				for i: int in range(count):
					var a: float = spin + i * TAU / count
					D.shot(s, {"space": "box", "x": to.x + cos(a) * 20.0, "y": to.y + sin(a) * 20.0, "vx": cos(a) * 1.05, "vy": sin(a) * 1.05, "hold": true, "arm": 24, "collide": "rect", "w": 4.5, "h": 5.0, "shape": "folding", "rot": a + PI * 0.5, "life": 200})
		from = to
	# Where the seat settles over the lantern, the light goes out.
	var covered: Rect2 = s.pocket.intersection(_chair_rect(s))
	s.pocketLit = covered.get_area() < s.pocket.get_area() * 0.2
	if t % 24 == 10 and t > 20 and t < 390:
		_row(s, h, clampf(float(s.soul.y) + D.rand_range(s, -3.0, 3.0), -h.y + 10.0, h.y - 10.0))
		if phase > 0: _row(s, h, D.rand_range(s, -h.y + 10.0, h.y - 10.0))

static func _row(s: Dictionary, h: Vector2, y: float) -> void:
	var side: float = -1.0 if D.rand(s) < 0.5 else 1.0
	var speed: float = 2.8
	D.warn(s, {"kind": "row", "y": y, "h": 7.0}, 34)
	for i: int in range(2):
		D.shot(s, {"space": "box", "x": side * (h.x + 12.0 + speed * 34.0 + i * 20.0), "y": y, "vx": -side * speed, "collide": "rect", "w": 4.5, "h": 5.0, "shape": "folding", "life": 220})

# ---------------------------------------------------------------- progress / drawing

static func progress(s: Dictionary) -> String:
	return "Quiet time %d/120\nLeave the empty seat clear" % mini(120, int(s.quietTicks))

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var clock: int = int(s.clock)
	# A dim hall: faint rows of seats.
	for row: int in range(4):
		var y: float = -h.y + 18.0 + row * 28.0
		var x: float = -h.x + 10.0
		while x < h.x:
			c.draw_rect(Rect2(v.box_point(Vector2(x, y)), Vector2(12, 7)), Color(LILAC, 0.05))
			x += 22.0
	# Telegraphs.
	for w: Dictionary in s.warnings:
		var f: float = 0.5 + 0.5 * sin(float(w.age) * 0.5)
		match str(w.kind):
			"column":
				var poly: PackedVector2Array = v.box_rect_poly(Rect2(float(w.x) - float(w.w), -h.y, float(w.w) * 2.0, h.y * 2.0))
				c.draw_colored_polygon(poly, Color(ROSE, 0.06 + 0.12 * f))
				c.draw_line(v.box_point(Vector2(float(w.x), -h.y)), v.box_point(Vector2(float(w.x), -h.y + 10.0)), Color(ROSE, 0.7), 2)
			"row":
				var poly2: PackedVector2Array = v.box_rect_poly(Rect2(-h.x, float(w.y) - float(w.h), h.x * 2.0, float(w.h) * 2.0))
				c.draw_colored_polygon(poly2, Color(ROSE, 0.06 + 0.12 * f))
				c.draw_polyline(poly2 + PackedVector2Array([poly2[0]]), Color(ROSE, 0.35), 1)
	# The seat itself, under its hatching.
	var chair: Rect2 = _chair_rect(s)
	_draw_chair(c, v, chair.get_center(), 1.0)
	if s.chairGhost != null:
		var ghost: Rect2 = Rect2(Vector2(s.chairGhost) - chair.size * 0.5, chair.size)
		var gp: PackedVector2Array = v.box_rect_poly(ghost)
		var blink: float = 0.4 + 0.4 * sin(float(clock) * 0.3)
		for i: int in range(4):
			_dashed(c, gp[i], gp[(i + 1) % 4], Color(PLUM.lightened(0.3), blink))
		c.draw_line(v.box_point(chair.get_center()), v.box_point(Vector2(s.chairGhost)), Color(PLUM.lightened(0.3), 0.35), 1)
	# Other lamps: the next one blinks, the dark ones are just outlines.
	for i: int in range(s.lamps.size()):
		if i == int(s.lamp) and s.pocketLit: continue
		var r: Rect2 = _rect_at(s.lamps[i], Vector2(26, 16))
		var lp: PackedVector2Array = v.box_rect_poly(r)
		var next: bool = i == int(s.nextLamp)
		var col: Color = Color(MINT, 0.3 + 0.6 * float((clock / 8) % 2)) if next else Color(PLUM, 0.6)
		for k: int in range(4): _dashed(c, lp[k], lp[(k + 1) % 4], col)
		_lantern_icon(c, v.box_point(Vector2(r.get_center().x, r.end.y - 4.0)), 0.9 if next else 0.3, false)
	# The quiet pocket.
	var pocket: Rect2 = s.pocket
	var poly3: PackedVector2Array = v.box_rect_poly(pocket)
	var lit: bool = s.pocketLit
	var warn: bool = int(s.flicker) >= 0 and (clock / 5) % 2 == 0
	if lit and not warn:
		var flick: float = 0.85 + 0.15 * sin(float(clock) * 0.37)
		c.draw_circle(v.box_point(pocket.get_center()), maxf(pocket.size.x, pocket.size.y) * 0.62, Color(0.95, 0.72, 0.32, 0.07 * flick))
		c.draw_colored_polygon(poly3, Color(0.95, 0.75, 0.4, 0.10 * flick))
		c.draw_polyline(poly3 + PackedVector2Array([poly3[0]]), MINT, 2)
	else:
		for k: int in range(4): _dashed(c, poly3[k], poly3[(k + 1) % 4], Color(PLUM.lightened(0.2), 0.8))
	_lantern_icon(c, v.box_point(Vector2(pocket.get_center().x, pocket.end.y - 4.0)), 1.0 if lit and not warn else 0.35, lit)
	var fill: float = clampf(float(s.quietTicks) / float(NEED), 0.0, 1.0)
	var base: Vector2 = v.box_point(Vector2(pocket.position.x, pocket.end.y + 3.0))
	c.draw_line(base, v.box_point(Vector2(pocket.end.x, pocket.end.y + 3.0)), Color(MINT, 0.2), 2)
	if fill > 0.0: c.draw_line(base, v.box_point(Vector2(pocket.position.x + pocket.size.x * fill, pocket.end.y + 3.0)), MINT, 2)

static func _dashed(c: CanvasItem, a: Vector2, b: Vector2, col: Color) -> void:
	var n: int = maxi(1, int(a.distance_to(b) / 6.0))
	for i: int in range(0, n, 2):
		c.draw_line(a.lerp(b, float(i) / n), a.lerp(b, float(mini(i + 1, n)) / n), col, 1)

static func _draw_chair(c: CanvasItem, v: Node2D, centre: Vector2, alpha: float) -> void:
	var col: Color = Color(CREAM, 0.55 * alpha)
	var p: Callable = func(x: float, y: float) -> Vector2: return v.box_point(centre + Vector2(x, y))
	c.draw_line(p.call(-9.0, -18.0), p.call(-9.0, 4.0), col, 2)
	c.draw_line(p.call(9.0, -18.0), p.call(9.0, 4.0), col, 2)
	c.draw_line(p.call(-9.0, -16.0), p.call(9.0, -16.0), col, 1)
	c.draw_line(p.call(-9.0, -10.0), p.call(9.0, -10.0), col, 1)
	c.draw_line(p.call(-11.0, 4.0), p.call(11.0, 4.0), col, 3)
	c.draw_line(p.call(-9.0, 4.0), p.call(-12.0, 20.0), col, 2)
	c.draw_line(p.call(9.0, 4.0), p.call(12.0, 20.0), col, 2)
	c.draw_line(p.call(-9.0, 4.0), p.call(10.0, 20.0), Color(col, col.a * 0.6), 1)

static func _lantern_icon(c: CanvasItem, at: Vector2, glow: float, raised: bool) -> void:
	if raised: c.draw_circle(at + Vector2(0, -2), 7.0, Color(1.0, 0.8, 0.4, 0.15 * glow))
	c.draw_line(at + Vector2(-2, -7), at + Vector2(2, -7), Color(CREAM, glow), 1)
	c.draw_rect(Rect2(at + Vector2(-3, -6), Vector2(6, 8)), Color("3a3020"))
	c.draw_rect(Rect2(at + Vector2(-2, -4), Vector2(4, 4)), Color(1.0, 0.8, 0.4, 0.2 + 0.8 * glow))
	c.draw_rect(Rect2(at + Vector2(-3, -6), Vector2(6, 8)), Color(AMBER, glow), false, 1)

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	var armed: bool = int(b.age) > int(b.arm)
	match str(b.shape):
		"mote":
			c.draw_circle(at, float(b.r) + 1.5, Color(DUST, 0.18 * alpha))
			c.draw_circle(at, float(b.r), Color(DUST, alpha))
			return true
		"moth":
			var flap: float = absf(sin(float(b.age) * 0.5)) * 3.0 + 1.0
			var a: float = alpha * (1.0 if armed else 0.4)
			c.draw_colored_polygon(PackedVector2Array([at, at + Vector2(-4, -flap), at + Vector2(-4, flap * 0.5)]), Color(Color("b8ad98"), a))
			c.draw_colored_polygon(PackedVector2Array([at, at + Vector2(4, -flap), at + Vector2(4, flap * 0.5)]), Color(Color("b8ad98"), a))
			c.draw_circle(at, 1.2, Color(Color("5a4f40"), a))
			return true
		"guest":
			var a2: float = alpha * (0.85 if armed else 0.12 + 0.3 * float(b.age) / maxf(1.0, float(b.arm)))
			var col: Color = Color(LILAC.lightened(0.2), a2)
			if b.get("left", false): col = Color("c9a0b8", a2 * 0.85)
			c.draw_circle(at + Vector2(0, -3), 2.6, col)
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-4.5, 5), at + Vector2(-3, 0), at + Vector2(3, 0), at + Vector2(4.5, 5)]), col)
			if not armed: c.draw_arc(at, 7.0, 0, TAU, 14, Color(LILAC, 0.25), 1)
			return true
		"programme":
			var q: PackedVector2Array = v.quad(at, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(q, Color(CREAM, alpha))
			c.draw_line(at + Vector2(-3, -1).rotated(turn), at + Vector2(3, -1).rotated(turn), Color(PLUM, alpha), 1)
			c.draw_line(at + Vector2(-3, 1.5).rotated(turn), at + Vector2(2, 1.5).rotated(turn), Color(PLUM, alpha), 1)
			return true
		"folding":
			var a3: float = alpha * (1.0 if armed else 0.35 + 0.3 * sin(float(b.age) * 0.5))
			var col2: Color = Color(Color("a7a2b0"), a3)
			var up: Vector2 = Vector2(0, -1).rotated(turn)
			var side: Vector2 = Vector2(1, 0).rotated(turn)
			c.draw_line(at + up * 5.0 - side * 3.0, at - up * 5.0 + side * 3.0, col2, 2)
			c.draw_line(at + up * 5.0 + side * 3.0, at - up * 5.0 - side * 3.0, col2, 2)
			c.draw_line(at - side * 4.5, at + side * 4.5, Color(CREAM, a3), 2)
			return true
	return false
