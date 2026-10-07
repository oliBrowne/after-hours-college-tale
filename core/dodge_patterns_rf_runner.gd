extends RefCounted
## ALTITUDE RUNNER / a wandering campus fight. Mile eleven at 5,400 feet and he feels
## amazing. Three slow, telegraphed attacks, one per turn, cycling in order:
## intervals, hydration, hill repeats. Phase 1 is the same three a little denser.
## The promise "Match his pace": three green markers jog around one after another
## (touch the first, stay with the other two). They move at jogging speed, always
## through the safe part of the box.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["intervals", "hydration", "hill_repeats"]
const PHASES: Array[int] = [0, 1]
const PACES: int = 3
const COLUMN_GAP: float = 44.0

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const BLUE: Color = Color("8fb3ea")
const LILAC: Color = Color("a68db8")
const ROSE: Color = Color("e8837b")
const STONE: Color = Color("b49a80")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 400 + 40 * clampi(int(s.phase), 0, 1)
	s.bannerColor = AMBER
	s.jogs = []
	s.tells = []
	s.skip = -1
	match id:
		"intervals":
			s.phaseName = "Intervals"
			s.hint = "Sprinters run the red columns in turn. Stay in the gaps. Match the green marker's pace."
			# Vertical jogs inside the gaps between the columns.
			s.jogs = [_jog(-0.6, 0.0, 0.0, 0.5, 0.02, 0.0), _jog(0.2, 0.0, 0.0, 0.5, 0.02, 2.0), _jog(-0.2, 0.0, 0.0, 0.5, 0.019, 4.0)]
		"hydration":
			s.phaseName = "Hydration Break"
			s.hint = "Bottles fly along dotted arcs and splash. Step clear. Match the green marker's pace."
			# Horizontal jogs along the top, above the highest arc.
			s.jogs = [_jog(-0.4, -0.72, 0.38, 0.0, 0.02, 0.0), _jog(0.4, -0.72, 0.38, 0.0, 0.02, 2.2), _jog(0.0, -0.72, 0.5, 0.0, 0.018, 4.0)]
		"hill_repeats":
			s.phaseName = "Hill Repeats"
			s.hint = "He jogs the floor with his sign. Rocks roll down dotted paths. Match the green pace."
			s.jogs = [_jog(0.0, -0.35, 0.5, 0.0, 0.02, 1.0), _jog(0.0, -0.35, 0.5, 0.0, 0.02, 4.0), _jog(0.0, -0.35, 0.45, 0.0, 0.022, 2.5)]
	# Pace 0 is touched, 1 and 2 are held for a little under a second.
	D.objective(s, {"kind": "touch", "r": 10.0, "label": "pace", "active": false})
	D.objective(s, {"kind": "hold", "r": 10.0, "need": 45, "active": false})
	D.objective(s, {"kind": "hold", "r": 10.0, "need": 55, "active": false})

## A jog path in fractions of the half box: centre (cx, cy), swing (ax, ay).
static func _jog(cx: float, cy: float, ax: float, ay: float, w: float, ph: float) -> Dictionary:
	return {"c": Vector2(cx, cy), "a": Vector2(ax, ay), "w": w, "ph": ph}

static func _spot(s: Dictionary, i: int, tick: int) -> Vector2:
	var j: Dictionary = s.jogs[i]
	var c: Vector2 = j.c
	var a: Vector2 = j.a
	var swing: float = sin(float(j.w) * float(tick) + float(j.ph))
	return Vector2(c.x + a.x * swing, c.y + a.y * swing) * D.half(s)

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return _matched(s) >= PACES

static func progress(s: Dictionary) -> String:
	return "Pace matched %d/%d" % [_matched(s), PACES]

static func _matched(s: Dictionary) -> int:
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	return count

## The marker being chased right now, or -1 when all three are matched.
static func _current(s: Dictionary) -> int:
	for i: int in range(s.objectives.size()):
		if not s.objectives[i].done: return i
	return -1

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	_markers(s, t)
	match str(s.patternId):
		"intervals": _intervals(s, t, phase)
		"hydration": _hydration(s, t, phase)
		"hill_repeats": _hill_repeats(s, t, phase)

static func after(_s: Dictionary, _t: int) -> void:
	pass

## One marker at a time, jogging along its path; the next shows 24 ticks after the last.
static func _markers(s: Dictionary, t: int) -> void:
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		var spot: Vector2 = _spot(s, i, t)
		o.x = spot.x; o.y = spot.y
		var ready: bool = t >= 40 if i == 0 else last_done >= 0 and int(s.clock) - last_done >= 24
		o.active = ready
		if ready and not bool(o.get("shown", false)):
			o.shown = true
			D.effect(s, "pulse", D.to_world(s, spot), 18)
		return

## A dotted path that stays visible while the thing is about to move along it.
static func _tell(s: Dictionary, pts: PackedVector2Array, warn: int, flight: int) -> void:
	s.tells.append({"pts": pts, "start": int(s.clock) + warn, "until": int(s.clock) + warn + flight})

# ---------------------------------------------------------------- attacks

## Intervals: five columns; the sprinters run them one after another (down, then
## back up on the next sweep). One column rests each sweep. Phase 1 is faster.
static func _intervals(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 220.0, "h": 112.0}, 30)
	var gap: int = 18 - 3 * phase
	if t >= 14 and (t - 14) % gap == 0 and t < int(s.length) - 140:
		var n: int = int((t - 14) / gap)
		var step: int = n % 7
		if step == 0: s.skip = int(D.rand(s) * 5.0) % 5
		var col: int = step if int(n / 7) % 2 == 0 else 4 - step
		if step < 5 and col != int(s.skip):
			var h: Vector2 = D.half(s)
			var x: float = float(col - 2) * COLUMN_GAP
			var dir: float = 1.0 if int(n / 7) % 2 == 0 else -1.0
			D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 9.0, "horizontal": false}, 36)
			D.warn(s, {"kind": "edge", "space": "box", "x": x, "y": -dir * (h.y - 3.0), "dir": Vector2(0, dir)}, 36, step == 0)
			D.shot(s, {"space": "box", "x": x, "y": -dir * (h.y + 14.0), "vy": dir * (2.1 + 0.3 * phase), "collide": "rect", "w": 5.5, "h": 7.5, "shape": "sprinter", "face": dir, "hold": true, "arm": 36, "life": 36 + 200})

## Hydration Break: bottles are tossed from the sides along arcs; each arc is drawn
## as dots with a splash mark where it lands. Phase 1 adds a second toss.
static func _hydration(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
		D.banner(s, "FEELING AMAZING", 70)
	var every: int = 52 - 8 * phase
	if t < int(s.length) - 150 and t % every == 12:
		var n: int = int(t / every)
		_toss(s, 1.0 if n % 2 == 0 else -1.0, float(s.soul.x) + D.rand_range(s, -24.0, 24.0))
	if phase > 0 and t < int(s.length) - 150 and t % every == 12 + 24:
		var n2: int = int(t / every)
		_toss(s, -1.0 if n2 % 2 == 0 else 1.0, float(s.soul.x) + D.rand_range(s, 40.0, 70.0) * (1.0 if D.rand(s) < 0.5 else -1.0))

static func _toss(s: Dictionary, side: float, target: float) -> void:
	var h: Vector2 = D.half(s)
	var flight: int = int(D.rand_range(s, 84.0, 94.0))
	var grav: float = 0.06
	var x0: float = side * (h.x + 12.0)
	var floor_y: float = h.y - 4.0
	var landing: float = clampf(target, -h.x + 16.0, h.x - 16.0)
	var vx: float = (landing - x0) / float(flight)
	var vy: float = -0.5 * grav * float(flight)
	var pts: PackedVector2Array = PackedVector2Array()
	for k: int in range(0, flight, 4):
		pts.append(Vector2(x0 + vx * k, floor_y + vy * k + 0.5 * grav * k * (k + 1)))
	pts.append(Vector2(landing, floor_y))
	D.warn(s, {"kind": "puddle", "space": "box", "x": landing, "y": floor_y - 1.0}, 40, true)
	D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": floor_y - 6.0, "dir": Vector2(-side, 0)}, 40)
	_tell(s, pts, 40, flight)
	D.shot(s, {"space": "box", "x": x0, "y": floor_y, "vx": vx, "vy": vy, "ay": grav, "bounce": 0.5, "r": 4.0, "shape": "bottle", "spin": 0.12 * side, "hold": true, "arm": 40, "life": 40 + 240})

## Hill Repeats: he jogs back and forth along the bottom carrying his sign (the
## sign is solid too). Rocks roll down along dotted paths, away from the green marker.
static func _hill_repeats(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
		D.banner(s, "5,430 FT", 70)
		D.shot(s, {"space": "box", "x": 0.0, "y": 45.0, "collide": "rect", "w": 7.0, "h": 10.0, "shape": "runner", "hill": 1, "arm": 40, "life": 900})
		D.shot(s, {"space": "box", "x": 0.0, "y": 20.0, "collide": "rect", "w": 33.0, "h": 6.0, "shape": "sign", "hill": 2, "arm": 40, "life": 900})
	var stride: float = 0.016 + 0.003 * phase
	var at: float = 76.0 * sin(stride * float(t))
	var face: float = signf(cos(stride * float(t)))
	for b: Dictionary in s.bullets:
		if b.has("hill"):
			b.x = at; b.px = at; b.face = face
	var every: int = 56 - 14 * phase
	if t % every == 24 and t < int(s.length) - 150:
		var h: Vector2 = D.half(s)
		var best: Dictionary = {}
		var far: float = -1.0
		for k: int in range(4):
			var x: float = clampf(float(s.soul.x) + D.rand_range(s, -16.0, 16.0), -0.8 * h.x, 0.8 * h.x) if k == 0 else D.rand_range(s, -0.8, 0.8) * h.x
			var vx: float = D.rand_range(s, 0.2, 0.4) * (1.0 if D.rand(s) < 0.5 else -1.0)
			var pts: PackedVector2Array = PackedVector2Array()
			for j: int in range(0, 90, 6):
				pts.append(Vector2(x + vx * j, -h.y - 6.0 + 0.7 * j + 0.5 * 0.012 * j * (j + 1)))
			# The first candidate is aimed at you; it wins whenever it stays clear of the marker.
			var clear: float = _clearance(s, t + 36, pts) if bool(s.promised) else 30.0
			var score: float = minf(clear, 30.0) + (12.0 if k == 0 else 0.0)
			if score > far:
				far = score; best = {"x": x, "vx": vx, "pts": pts}
		D.warn(s, {"kind": "edge", "space": "box", "x": best.x, "y": -h.y + 3.0, "dir": Vector2(0, 1)}, 36, int(t / every) % 2 == 0)
		_tell(s, best.pts, 36, 90)
		D.shot(s, {"space": "box", "x": best.x, "y": -h.y - 6.0, "vx": best.vx, "vy": 0.7, "ay": 0.012 + 0.003 * phase, "r": 4.5, "shape": "rock", "spin": 0.09 * signf(best.vx), "bounce": 0.4, "hold": true, "arm": 36, "life": 36 + 140})

## How near a falling path (sampled every 6 ticks) comes to the marker being chased.
static func _clearance(s: Dictionary, t0: int, pts: PackedVector2Array) -> float:
	var i: int = _current(s)
	if i < 0: return 999.0
	var best: float = 999.0
	for k: int in range(pts.size()):
		best = minf(best, pts[k].distance_to(_spot(s, i, t0 + k * 6)))
	return best

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	if str(s.patternId) == "hill_repeats":
		# A faint ridge line behind the climb.
		var ridge: PackedVector2Array = PackedVector2Array()
		for i: int in range(9):
			ridge.append(v.box_point(Vector2(-h.x + i * h.x * 0.25, -h.y + (14.0 if i % 2 == 0 else 26.0))))
		c.draw_polyline(ridge, Color(LILAC, 0.18), 1)
	var now: int = int(s.clock)
	for k: Dictionary in s.tells:
		if now >= int(k.until): continue
		var before: bool = now < int(k.start)
		var fade: float = 1.0 if before else clampf(float(int(k.until) - now) / 20.0, 0.0, 1.0)
		var pts: PackedVector2Array = k.pts
		for i: int in range(pts.size()):
			c.draw_circle(v.box_point(pts[i]), 1.3, Color(ROSE if before else BLUE, (0.55 + 0.3 * sin(float(now) * 0.4 + i)) * fade * 0.8))
	# Running shoes mark the green pace markers.
	for o: Dictionary in s.objectives:
		if bool(s.promised) and o.active and not o.done:
			var at: Vector2 = v.box_point(Vector2(float(o.x), float(o.y)))
			_shoe(c, at + Vector2(-3, 2), 1.0, Color(MINT, 0.9))
			_shoe(c, at + Vector2(3, -2), -1.0, Color(MINT, 0.9))

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"sprinter":
			# Upright, headband and singlet, pumping arms and legs; speed lines trail behind.
			var d: float = float(b.get("face", 1.0))
			var step: float = sin(float(b.age) * 0.5) * 2.5
			c.draw_line(at + Vector2(-4, -d * 8), at + Vector2(-4, -d * 15), Color(CREAM, 0.35 * alpha), 1)
			c.draw_line(at + Vector2(4, -d * 8), at + Vector2(4, -d * 13), Color(CREAM, 0.35 * alpha), 1)
			c.draw_line(at + Vector2(-2, 3), at + Vector2(-2 - step, 8), Color(CREAM, alpha), 2)
			c.draw_line(at + Vector2(2, 3), at + Vector2(2 + step, 8), Color(CREAM, alpha), 2)
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-4, -3), at + Vector2(4, -3), at + Vector2(3, 4), at + Vector2(-3, 4)]), Color(BLUE, alpha))
			c.draw_line(at + Vector2(-4, -2), at + Vector2(-6, 1 + step), Color(CREAM, alpha), 2)
			c.draw_line(at + Vector2(4, -2), at + Vector2(6, 1 - step), Color(CREAM, alpha), 2)
			c.draw_circle(at + Vector2(0, -6), 2.6, Color(CREAM, alpha))
			c.draw_line(at + Vector2(-2.6, -6.5), at + Vector2(2.6, -6.5), Color(ROSE, alpha), 1)
			return true
		"runner":
			var f: float = float(b.get("face", 1.0))
			var legs: float = sin(float(b.age) * 0.35) * 5.0
			var ghost: float = 0.4 if int(b.age) <= int(b.arm) else 1.0
			var col: Color = Color(CREAM, alpha * ghost)
			c.draw_line(at + Vector2(0, 3), at + Vector2(-legs, 10), col, 2)
			c.draw_line(at + Vector2(0, 3), at + Vector2(legs, 10), col, 2)
			_shoe(c, at + Vector2(-legs + 1, 10), f, Color(ROSE, alpha * ghost))
			_shoe(c, at + Vector2(legs + 1, 10), f, Color(ROSE, alpha * ghost))
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-4, -5), at + Vector2(4, -5), at + Vector2(3, 4), at + Vector2(-3, 4)]), Color(BLUE, alpha * ghost))
			c.draw_line(at + Vector2(0, -3), at + Vector2(-legs * 0.7, 1), col, 1)
			c.draw_line(at + Vector2(0, -3), at + Vector2(legs * 0.7, 1), col, 1)
			c.draw_circle(at + Vector2(0, -8), 3.0, col)
			c.draw_line(at + Vector2(-3, -9), at + Vector2(3, -9), Color(AMBER, alpha * ghost), 1)
			return true
		"sign":
			var ghost2: float = 0.4 if int(b.age) <= int(b.arm) else 1.0
			var board: PackedVector2Array = v.quad(at, float(b.w), float(b.h), 0.0)
			c.draw_line(at + Vector2(0, float(b.h)), at + Vector2(0, float(b.h) + 8), Color(CREAM, alpha * ghost2), 1)
			c.draw_colored_polygon(board, Color(AMBER, 0.92 * alpha * ghost2))
			c.draw_polyline(board + PackedVector2Array([board[0]]), Color(CREAM, alpha * ghost2), 1)
			v.text(c, at + Vector2(0, 4), "5,430 FT", Color(INK, alpha * ghost2), 66.0)
			return true
		"bottle":
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-3, -2).rotated(turn), at + Vector2(3, -2).rotated(turn), at + Vector2(3, 2).rotated(turn), at + Vector2(-3, 2).rotated(turn)]), Color(BLUE, alpha))
			c.draw_line(at + Vector2(3, 0).rotated(turn), at + Vector2(5, 0).rotated(turn), Color(ROSE, alpha), 2)
			c.draw_line(at + Vector2(-1, -1).rotated(turn), at + Vector2(1.5, -1).rotated(turn), Color(CREAM, 0.7 * alpha), 1)
			return true
		"rock":
			var rock: PackedVector2Array = PackedVector2Array()
			for i: int in range(7):
				var bump: float = 0.8 + 0.3 * fposmod(float(int(b.id) * 7 + i * 13), 5.0) / 4.0
				rock.append(at + Vector2.from_angle(float(i) * TAU / 7.0 + turn) * float(b.r) * bump)
			c.draw_colored_polygon(rock, Color(STONE, alpha))
			c.draw_polyline(rock + PackedVector2Array([rock[0]]), Color(INK, 0.5 * alpha), 1)
			c.draw_circle(at + Vector2(-1.5, -1.5).rotated(turn), 1.0, Color(CREAM, 0.6 * alpha))
			return true
	return false

## One running shoe, toe pointing the way of face (1 = right).
static func _shoe(c: CanvasItem, at: Vector2, face: float, colour: Color) -> void:
	c.draw_colored_polygon(PackedVector2Array([at + Vector2(-3 * face, -2), at + Vector2(0, -2), at + Vector2(4 * face, 1), at + Vector2(4 * face, 2.5), at + Vector2(-3 * face, 2.5)]), colour)
	c.draw_line(at + Vector2(-3 * face, 2.5), at + Vector2(4 * face, 2.5), Color(CREAM, 0.8), 1)
