extends RefCounted
## COMMUTER CYCLIST / a wandering campus fight. Late for a 9 AM, shouts ON YOUR LEFT.
## Three slow, telegraphed attacks, one per turn, cycling in order: bike lanes,
## bell rings, skid. Phase 1 is the same three a little denser.
## The promise "Share the path": two green lane markers show up one after another;
## stand in each and press confirm while promised. Each marker sits away from the
## danger and stays until it is taken.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["bike_lane", "bell_rings", "skid"]
const PHASES: Array[int] = [0, 1]
const SHARES: int = 2
const LANES: Array[float] = [-36.0, 0.0, 36.0]

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const BLUE: Color = Color("8fb3ea")
const ROSE: Color = Color("e8837b")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 380 + 40 * clampi(int(s.phase), 0, 1)
	s.bannerColor = AMBER
	s.spots = []
	s.skids = []
	s.bell = Vector2(0.0, -44.0)
	s.rang = -99
	match id:
		"bike_lane":
			s.phaseName = "Bike Lane"
			s.hint = "Cyclists cross the red lanes. Wait between them. Confirm on the green markers."
			s.spots = [Vector2(-0.55, 0.32), Vector2(0.55, -0.32)]
		"bell_rings":
			s.phaseName = "Bell Rings"
			s.hint = "Every ding sends out a ring with a gap. Slip through it. Confirm on the green markers."
			s.spots = [Vector2(-0.62, 0.5), Vector2(0.62, 0.5)]
		"skid":
			s.phaseName = "Skid"
			s.hint = "A cyclist skids along the dotted line and drops bottles. Confirm on the green markers."
			s.spots = [Vector2(-0.62, -0.45), Vector2(0.62, 0.45)]
	for i: int in range(SHARES):
		D.objective(s, {"kind": "confirm", "r": 12.0, "label": "share" if i == 0 else "", "active": false, "x": 0.0, "y": 0.0})

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return _shared(s) >= SHARES

static func progress(s: Dictionary) -> String:
	return "Lanes shared %d/%d" % [_shared(s), SHARES]

static func _shared(s: Dictionary) -> int:
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	return count

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	_markers(s, t)
	match str(s.patternId):
		"bike_lane": _bike_lane(s, t, phase)
		"bell_rings": _bell_rings(s, t, phase)
		"skid": _skid(s, t, phase)

static func after(_s: Dictionary, _t: int) -> void:
	pass

## One marker at a time: the next appears 24 ticks after the last was taken.
static func _markers(s: Dictionary, t: int) -> void:
	var h: Vector2 = D.half(s)
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		var spot: Vector2 = Vector2(s.spots[i]) * h
		o.x = spot.x; o.y = spot.y
		var ready: bool = t >= 40 if i == 0 else last_done >= 0 and int(s.clock) - last_done >= 24
		o.active = ready
		if ready and not bool(o.get("shown", false)):
			o.shown = true
			D.effect(s, "pulse", D.to_world(s, spot), 18)
		return

# ---------------------------------------------------------------- attacks

## A cyclist enters a lane from the side after a red band and an edge warning.
static func _cyclist(s: Dictionary, side: float, y: float, speed: float, warn: int, shout: bool) -> void:
	var h: Vector2 = D.half(s)
	D.warn(s, {"kind": "lane", "y": D.centre(s).y + y, "h": 8.0, "horizontal": true}, warn)
	D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": y, "dir": Vector2(-side, 0)}, warn, shout)
	if shout: D.banner(s, "ON YOUR LEFT", 50)
	D.shot(s, {"space": "box", "x": side * (h.x + 16.0), "y": y, "vx": -side * speed, "collide": "rect", "w": 9.0, "h": 6.0, "shape": "cyclist", "face": -side, "hold": true, "arm": warn, "life": warn + 240})

## Bike Lane: three lanes, one cyclist at a time, from alternating sides. Wait in
## the strips between lanes; the green markers sit in those strips too.
static func _bike_lane(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
	var every: int = 46 if phase == 0 else 36
	if t % every == 12 and t < int(s.length) - 130:
		var n: int = int(t / every)
		var lane: int = [1, 0, 2, 1, 2, 0][n % 6]
		_cyclist(s, 1.0 if n % 2 == 0 else -1.0, LANES[lane], 2.0 + 0.3 * phase, 38 - 4 * phase, n % 3 == 0)

## Bell Rings: the bell on the handlebar dings; a ring grows from it, ghosted for
## a moment, with one gap that sits just beside you. Phase 1 dings more often.
static func _bell_rings(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 216.0, "h": 112.0}, 30)
	var h: Vector2 = D.half(s)
	var every: int = 76 if phase == 0 else 58
	var n: int = int(t / every)
	var flip: float = 1.0 if n % 2 == 0 else -1.0
	if t % every == 28 and t < int(s.length) - 150:
		s.bell = Vector2(-0.5 * flip * h.x, -h.y + 12.0)
		var bell: Vector2 = s.bell
		s.rang = int(s.clock)
		D.warn(s, {"kind": "ding"}, 26, true)
		var aim: float = (Vector2(float(s.soul.x), float(s.soul.y)) - bell).angle()
		var off: float = D.rand_range(s, 1.1, 1.4) * flip
		D.shot(s, {"space": "box", "x": bell.x, "y": bell.y, "collide": "ring", "shape": "dingring", "radius": 8.0, "grow": 0.8 + 0.1 * phase, "thick": 2.2, "gap": aim + off, "gapWidth": 1.6, "maxRadius": 190.0, "arm": 26, "life": 400})

## Skid: the dotted line shows where a cyclist will slide through, bottom left to
## top right or back. Water bottles drop along the line and wobble for a while.
static func _skid(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
	var h: Vector2 = D.half(s)
	var every: int = 104 if phase == 0 else 84
	if t % every == 14 and t < int(s.length) - 170:
		var from_left: bool = int(t / every) % 2 == 0
		var jitter: float = D.rand_range(s, -7.0, 7.0)
		var a: Vector2 = Vector2(-h.x - 14.0, 0.6 * h.y + jitter)
		var z: Vector2 = Vector2(h.x + 14.0, -0.6 * h.y + jitter)
		if not from_left:
			var swap: Vector2 = a; a = z; z = swap
		var dir: Vector2 = (z - a).normalized()
		var face: float = signf(dir.x)
		var entry: Vector2 = a + dir * (14.0 / absf(dir.x))
		D.warn(s, {"kind": "edge", "space": "box", "x": entry.x - face * 3.0, "y": entry.y, "dir": dir}, 40, true)
		s.skids.append({"a": a, "b": z, "start": int(s.clock) + 40, "until": int(s.clock) + 40 + int(a.distance_to(z) / 2.2) + 20})
		D.shot(s, {"space": "box", "x": a.x, "y": a.y, "vx": dir.x * (2.2 + 0.2 * phase), "vy": dir.y * (2.2 + 0.2 * phase), "collide": "rect", "w": 9.0, "h": 6.0, "rot": (dir * face).angle(), "shape": "cyclist", "face": face, "skid": true, "hold": true, "arm": 40, "life": 260})
	# The skidding cyclist drops a wobbling water bottle every few ticks.
	var gap: int = 12 - 3 * phase
	for b: Dictionary in s.bullets:
		if not b.get("skid", false) or int(b.age) <= int(b.arm) or (int(b.age) - int(b.arm)) % gap != 0: continue
		if absf(float(b.x)) > h.x or absf(float(b.y)) > h.y: continue
		var drift: Vector2 = Vector2(-float(b.vy), float(b.vx)).normalized() * 0.12
		D.shot(s, {"space": "box", "x": b.x, "y": b.y, "vx": drift.x, "vy": drift.y, "r": 3.5, "shape": "bottle", "spin": 0.03, "arm": 16, "life": 140, "wave": {"amp": 5.0, "freq": 0.1, "phase": D.rand(s) * TAU}})

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	match str(s.patternId):
		"bike_lane":
			# Painted lane edges with a faint bike on each lane.
			for y: float in LANES:
				c.draw_dashed_line(v.box_point(Vector2(-h.x, y)), v.box_point(Vector2(h.x, y)), Color(CREAM, 0.16), 1.0, 6.0)
				_bike(c, v.box_point(Vector2(-h.x + 14.0, y)), 0.0, 1.0, Color(CREAM, 0.14))
		"bell_rings":
			# A handlebar across the top; the bell sits on its stem.
			var left: Vector2 = v.box_point(Vector2(-h.x + 16.0, -h.y + 5.0))
			var right: Vector2 = v.box_point(Vector2(h.x - 16.0, -h.y + 5.0))
			c.draw_line(left, right, Color(CREAM, 0.3), 2)
			c.draw_line(left, left + Vector2(0, 7), Color(BLUE, 0.6), 3)
			c.draw_line(right, right + Vector2(0, 7), Color(BLUE, 0.6), 3)
			var bell: Vector2 = v.box_point(Vector2(s.bell))
			var ding: bool = int(s.clock) - int(s.rang) < 12
			c.draw_arc(bell + Vector2(0, 1), 5.0, PI, TAU, 10, AMBER, 3)
			c.draw_line(bell + Vector2(-6, 1), bell + Vector2(6, 1), AMBER, 1)
			c.draw_circle(bell + Vector2(0, -6), 1.2, CREAM)
			if ding:
				c.draw_arc(bell, 9.0, PI + 0.5, TAU - 0.5, 8, Color(AMBER, 0.7), 1)
				c.draw_arc(bell, 12.0, PI + 0.7, TAU - 0.7, 8, Color(AMBER, 0.4), 1)
		"skid":
			for k: Dictionary in s.skids:
				var now: int = int(s.clock)
				if now >= int(k.until): continue
				var fade: float = 1.0 if now < int(k.start) else clampf(float(int(k.until) - now) / 30.0, 0.0, 1.0)
				var blink: float = 0.5 + 0.5 * sin(float(now) * 0.4)
				c.draw_dashed_line(v.box_point(Vector2(k.a)), v.box_point(Vector2(k.b)), Color(ROSE, (0.35 + 0.4 * blink * float(now < int(k.start))) * fade), 2.0, 7.0)
	# Green lane markers: a painted bike on each promise spot.
	for o: Dictionary in s.objectives:
		if bool(s.promised) and o.active and not o.done:
			_bike(c, v.box_point(Vector2(float(o.x), float(o.y))), 0.0, 1.0, Color(MINT, 0.9))

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, _v: Node2D) -> bool:
	match str(b.shape):
		"cyclist":
			# A rider in a rose shirt leaning over the bars; the bell is on the handlebar.
			_bike(c, at + Vector2(0, 3).rotated(turn), turn, float(b.get("face", 1.0)), Color(CREAM, alpha))
			var f: float = float(b.get("face", 1.0))
			c.draw_line(at + Vector2(-2 * f, -1).rotated(turn), at + Vector2(1 * f, -7).rotated(turn), Color(ROSE, alpha), 2)
			c.draw_circle(at + Vector2(2 * f, -9).rotated(turn), 2.2, Color(CREAM, alpha))
			c.draw_arc(at + Vector2(2 * f, -9).rotated(turn), 2.6, PI + turn, TAU + turn, 6, Color(AMBER, alpha), 2)
			c.draw_circle(at + Vector2(5 * f, -3).rotated(turn), 1.3, Color(AMBER, alpha))
			return true
		"bottle":
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-3, -1.8).rotated(turn), at + Vector2(3, -1.8).rotated(turn), at + Vector2(3, 1.8).rotated(turn), at + Vector2(-3, 1.8).rotated(turn)]), Color(BLUE, alpha))
			c.draw_line(at + Vector2(3, 0).rotated(turn), at + Vector2(5, 0).rotated(turn), Color(CREAM, alpha), 2)
			c.draw_line(at + Vector2(-1.5, -1).rotated(turn), at + Vector2(1.5, -1).rotated(turn), Color(CREAM, 0.7 * alpha), 1)
			return true
		"dingring":
			var gw: float = float(b.gapWidth) * 0.5
			var ghost: float = 0.3 if int(b.age) <= int(b.arm) else 1.0
			var start: float = float(b.gap) + gw
			var end: float = float(b.gap) + TAU - gw
			var steps: int = maxi(24, int(float(b.radius) * 0.6))
			c.draw_arc(at, float(b.radius), start, end, steps, Color(AMBER, 0.95 * alpha * ghost), 4)
			c.draw_arc(at, float(b.radius) - 4.0, start, end, steps, Color(CREAM, 0.3 * alpha * ghost), 1)
			return true
	return false

## A little bike seen from the side: two wheels and a frame. face = 1 points right.
static func _bike(c: CanvasItem, at: Vector2, turn: float, face: float, colour: Color) -> void:
	var r_wheel: Vector2 = at + Vector2(-6.0 * face, 1.0).rotated(turn)
	var f_wheel: Vector2 = at + Vector2(6.0 * face, 1.0).rotated(turn)
	c.draw_arc(r_wheel, 3.3, 0.0, TAU, 12, colour, 1)
	c.draw_arc(f_wheel, 3.3, 0.0, TAU, 12, colour, 1)
	var seat: Vector2 = at + Vector2(-2.0 * face, -3.0).rotated(turn)
	var head: Vector2 = at + Vector2(4.0 * face, -3.0).rotated(turn)
	var crank: Vector2 = at + Vector2(-1.0 * face, 1.0).rotated(turn)
	c.draw_polyline(PackedVector2Array([r_wheel, seat, head, f_wheel]), colour, 1)
	c.draw_polyline(PackedVector2Array([crank, seat]), colour, 1)
	c.draw_line(crank, head, colour, 1)
