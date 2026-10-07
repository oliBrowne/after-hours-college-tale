extends RefCounted
## SUNBEAM / a RARE wandering mini-boss: the frontman of a jam band, tie-dye and a guitar,
## with a bus that blows bubbles. More generous and a little longer than the common
## route fights (wide gaps, slow bullets, 440 ticks). Three attacks, one per turn,
## cycling in order: guitar riff, bubble bus, tie-dye. Phase 1 is a little denser.
## The promise "Join the jam": three glowing music notes show up one after another;
## stand in each and press confirm while promised. The danger plans around the
## current note: the riff's gap, the bubbles and the tie-dye gaps all leave it alone.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["riff", "bubble_bus", "tie_dye"]
const PHASES: Array[int] = [0, 1]
const NOTES: int = 3

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const BLUE: Color = Color("8fb3ea")
const LILAC: Color = Color("a68db8")
const ROSE: Color = Color("e8837b")
const DYES: Array[Color] = [Color("e8837b"), Color("e8b45c"), Color("b9d5bc"), Color("8fb3ea"), Color("a68db8"), Color("d98fc4")]

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 440 + 40 * clampi(int(s.phase), 0, 1)
	s.bannerColor = AMBER
	s.spots = []
	s.gaps = []
	s.busX = 0.0
	s.busTarget = 0.0
	s.side = 1.0
	s.rowY = (1.0 if D.rand(s) < 0.5 else -1.0) * 17.0
	match id:
		"riff":
			s.phaseName = "Guitar Riff"
			s.hint = "Soundwaves roll across in rows. Fly through the marked gap. Confirm on the glowing notes."
			s.spots = [Vector2(-58, s.rowY), Vector2(58, s.rowY), Vector2(0, s.rowY)]
		"bubble_bus":
			s.phaseName = "Bubble Bus"
			s.hint = "Bubbles drift up and pop into rings. Keep clear of them. Confirm on the glowing notes."
			s.side = 1.0 if D.rand(s) < 0.5 else -1.0
			s.spots = [Vector2(s.side * 62.0, -30.0), Vector2(s.side * 86.0, -22.0), Vector2(s.side * 44.0, -36.0)]
		"tie_dye":
			s.phaseName = "Tie-Dye"
			s.hint = "Colour rings spread out slowly. Find each gap. Confirm on the glowing notes."
			# All three notes sit on one ray from the middle, so one gap line serves them all.
			var ray: Vector2 = Vector2.from_angle((0.28 if D.rand(s) < 0.5 else -0.28) + (0.0 if D.rand(s) < 0.5 else PI))
			s.ray = ray
			s.spots = [ray * 44.0, ray * 74.0, ray * 98.0]
	for i: int in range(NOTES):
		D.objective(s, {"kind": "confirm", "r": 11.0, "label": "note" if i == 0 else "", "active": false})

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return _played(s) >= NOTES

static func progress(s: Dictionary) -> String:
	return "Notes played %d/%d" % [_played(s), NOTES]

static func _played(s: Dictionary) -> int:
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	return count

## The note being chased right now as a box-space point, or Vector2.INF when all are played.
static func _note(s: Dictionary) -> Vector2:
	for o: Dictionary in s.objectives:
		if not o.done: return Vector2(float(o.x), float(o.y))
	return Vector2.INF

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	_notes(s, t)
	match str(s.patternId):
		"riff": _riff(s, t, phase)
		"bubble_bus": _bubble_bus(s, t, phase)
		"tie_dye": _tie_dye(s, t, phase)

## Pop bubbles into ring bursts. A bubble is removed one tick after it pops.
static func after(s: Dictionary, _t: int) -> void:
	var popped: Array = []
	for b: Dictionary in s.bullets:
		if b.get("bubble", false) and not b.get("popped", false) and int(b.age) >= int(b.life) - 1:
			b.popped = true
			b.life = int(b.age)
			popped.append(Vector2(float(b.x), float(b.y)))
	for at: Vector2 in popped:
		D.shot(s, {"space": "box", "x": at.x, "y": at.y, "collide": "ring", "shape": "pop", "radius": 4.0, "grow": 0.9, "thick": 1.8, "gap": D.rand(s) * TAU, "gapWidth": 1.9, "maxRadius": 34.0 + 6.0 * clampi(int(s.phase), 0, 1), "arm": 14, "life": 120})

## One note at a time; the next appears 24 ticks after the last was played.
static func _notes(s: Dictionary, t: int) -> void:
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		var spot: Vector2 = Vector2(s.spots[i])
		o.x = spot.x; o.y = spot.y
		var ready: bool = t >= 40 if i == 0 else last_done >= 0 and int(s.clock) - last_done >= 24
		o.active = ready
		if ready and not bool(o.get("shown", false)):
			o.shown = true
			D.effect(s, "pulse", D.to_world(s, spot), 18)
		return

# ---------------------------------------------------------------- attacks

## Guitar Riff: a front of soundwaves rolls across with one wide gap, marked in amber.
## While promised the gap sits on the note row (a little off true); otherwise it is on
## the side you are not on. Phase 0 plays from the left; phase 1 from both sides.
static func _riff(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 112.0}, 30)
		D.banner(s, "ONE MORE JAM", 70)
	var every: int = 112 - 22 * phase
	if t % every == 12 and t < int(s.length) - 170:
		var h: Vector2 = D.half(s)
		var n: int = int(t / every)
		var side: float = -1.0 if phase == 0 or n % 2 == 0 else 1.0
		var half_gap: float = 30.0 - 4.0 * phase
		var gap_y: float = float(s.rowY) + D.rand_range(s, -8.0, 8.0)
		if not bool(s.promised):
			gap_y = (1.0 if float(s.soul.y) < 0.0 else -1.0) * D.rand_range(s, 14.0, h.y - 26.0)
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": gap_y + half_gap + 8.0, "dir": Vector2(-side, 0)}, 44, true)
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": gap_y - half_gap - 8.0, "dir": Vector2(-side, 0)}, 44)
		s.gaps.append({"y": gap_y, "half": half_gap, "side": side, "until": int(s.clock) + 44})
		var y: float = -h.y + 5.0
		while y < h.y:
			if absf(y - gap_y) > half_gap:
				D.shot(s, {"space": "box", "x": side * (h.x + 8.0), "y": y, "vx": -side * (1.15 + 0.15 * phase), "collide": "rect", "w": 4.0, "h": 5.5, "shape": "wave", "face": -side, "hue": int((y + h.y) / 10.0), "hold": true, "arm": 44, "life": 44 + 300})
			y += 10.0

## Bubble Bus: the bus rolls along the bottom, on the side away from the notes, and blows bubbles
## that drift up. A bubble flashes, then pops into a small ring with a wide gap.
static func _bubble_bus(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 112.0}, 30)
		D.banner(s, "THE BUS IS HERE", 70)
	var h: Vector2 = D.half(s)
	# Promised: the bus works the half opposite the notes. Otherwise it patrols the whole floor.
	s.busTarget = -float(s.side) * 0.5 * h.x + sin(float(t) * 0.02) * 0.2 * h.x if bool(s.promised) else sin(float(t) * 0.017) * 0.6 * h.x
	s.busX = move_toward(float(s.busX), float(s.busTarget), 0.8)
	var every: int = 36 - 8 * phase
	if t % every == 20 and t < int(s.length) - 170:
		D.shot(s, {"space": "box", "x": float(s.busX) + D.rand_range(s, -14.0, 14.0), "y": h.y - 26.0, "vx": D.rand_range(s, -0.08, 0.08), "vy": -0.55, "r": 6.5, "shape": "bubble", "bubble": true, "pierce": false, "arm": 22, "life": 70 + int(D.rand(s) * 26.0), "wave": {"amp": 6.0, "freq": 0.05, "phase": D.rand(s) * TAU}})

## Tie-Dye: coloured rings close in slowly from beyond the box, each with a wide gap
## that drifts, and pass right through the middle. While promised the gaps line up
## with the notes' ray at the moment the ring gets there; otherwise they sit beside you.
static func _tie_dye(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 112.0}, 30)
		D.banner(s, "FAR OUT", 70)
	var every: int = 66 - 12 * phase
	if t % every == 20 and t < int(s.length) - 190:
		var n: int = int(t / every)
		var speed: float = 0.55 + 0.08 * phase
		var spin: float = 0.006 * (1.0 if n % 2 == 0 else -1.0)
		var note: Vector2 = _note(s)
		var arrive: float = (150.0 - (note.length() if note != Vector2.INF else 70.0)) / speed
		var gap: float = Vector2(float(s.soul.x), float(s.soul.y)).angle() + D.rand_range(s, 1.3, 1.6) * (1.0 if n % 2 == 0 else -1.0)
		if bool(s.promised) and note != Vector2.INF: gap = Vector2(s.ray).angle()
		D.warn(s, {"kind": "ding"}, 28, true)
		D.shot(s, {"space": "box", "x": 0.0, "y": 0.0, "collide": "ring", "shape": "dyering", "hue": n, "radius": 150.0, "grow": -speed, "thick": 3.0, "gap": gap - spin * arrive, "gapSpin": spin, "gapWidth": 1.9, "maxRadius": 400.0, "arm": 28, "life": int(150.0 / speed) + 2})

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var now: int = int(s.clock)
	match str(s.patternId):
		"riff":
			# Guitar strings across the box, and the amber brackets that mark each gap.
			for i: int in range(6):
				var y: float = -h.y + 12.0 + float(i) * (2.0 * h.y - 24.0) / 5.0
				var pts: PackedVector2Array = PackedVector2Array()
				for k: int in range(0, 24):
					pts.append(v.box_point(Vector2(-h.x + float(k) * 2.0 * h.x / 23.0, y + 0.8 * sin(float(now) * 0.3 + float(k) * 0.9 + float(i)))))
				c.draw_polyline(pts, Color(CREAM, 0.1), 1)
			for g: Dictionary in s.gaps:
				if now >= int(g.until): continue
				var x: float = float(g.side) * (h.x - 7.0)
				var blink: float = 0.55 + 0.4 * sin(float(now) * 0.4)
				c.draw_colored_polygon(v.box_rect_poly(Rect2(-h.x, float(g.y) - float(g.half), 2.0 * h.x, 2.0 * float(g.half))), Color(AMBER, 0.05 + 0.05 * blink))
				c.draw_line(v.box_point(Vector2(x, float(g.y) - float(g.half))), v.box_point(Vector2(x, float(g.y) + float(g.half))), Color(AMBER, blink), 2)
				for edge: float in [-1.0, 1.0]:
					c.draw_line(v.box_point(Vector2(x, float(g.y) + edge * float(g.half))), v.box_point(Vector2(x - float(g.side) * 6.0, float(g.y) + edge * float(g.half))), Color(AMBER, blink), 2)
		"bubble_bus":
			_bus(c, v.box_point(Vector2(float(s.busX), h.y - 10.0)), signf(float(s.busTarget) - float(s.busX)), now)
		"tie_dye":
			# A faint swirl of dye turning in the middle, where every ring ends up.
			for i2: int in range(6):
				var a: float = float(now) * 0.01 + float(i2) * TAU / 6.0
				c.draw_arc(v.box_point(Vector2.ZERO), 16.0 + float(i2) * 6.0, a, a + 1.4, 10, Color(DYES[i2], 0.14), 3)
	for o: Dictionary in s.objectives:
		if bool(s.promised) and o.active and not o.done:
			_note_art(c, v.box_point(Vector2(float(o.x), float(o.y))), float(now))

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, _v: Node2D) -> bool:
	match str(b.shape):
		"wave":
			# A soundwave: two nested arcs bulging the way it travels, each row a different dye.
			var f: float = float(b.get("face", 1.0))
			var ghost: float = 0.35 if int(b.age) <= int(b.arm) else 1.0
			var col: Color = DYES[int(b.get("hue", 0)) % DYES.size()]
			var mid: float = 0.0 if f > 0.0 else PI
			c.draw_arc(at + Vector2(-f * 6.0, 0), 8.0, mid - 0.8, mid + 0.8, 8, Color(col, alpha * ghost), 3)
			c.draw_arc(at + Vector2(-f * 6.0, 0), 4.5, mid - 0.8, mid + 0.8, 6, Color(CREAM, 0.8 * alpha * ghost), 1)
			return true
		"bubble":
			# A soap bubble; it shivers and blushes just before it pops.
			var r: float = float(b.r) * minf(1.0, 0.4 + float(b.age) / 22.0)
			var soon: bool = int(b.age) > int(b.life) - 16
			var shake: Vector2 = Vector2(sin(float(b.age) * 1.7), cos(float(b.age) * 1.3)) * (1.2 if soon else 0.0)
			c.draw_circle(at + shake, r, Color(ROSE if soon else BLUE, 0.18 * alpha))
			c.draw_arc(at + shake, r, 0.0, TAU, 16, Color(ROSE if soon else CREAM, 0.9 * alpha), 1)
			c.draw_arc(at + shake, r * 0.65, 3.6, 4.7, 5, Color(CREAM, 0.8 * alpha), 1)
			return true
		"pop":
			var gw: float = float(b.gapWidth) * 0.5
			var ghost2: float = 0.35 if int(b.age) <= int(b.arm) else 1.0
			c.draw_arc(at, float(b.radius), float(b.gap) + gw, float(b.gap) + TAU - gw, 20, Color(MINT, 0.95 * alpha * ghost2), 3)
			c.draw_arc(at, float(b.radius) + 2.0, float(b.gap) + gw, float(b.gap) + TAU - gw, 20, Color(BLUE, 0.4 * alpha * ghost2), 1)
			return true
		"dyering":
			# Tie-dye: the ring is cut into coloured stretches that cycle with each ring.
			var gw2: float = float(b.gapWidth) * 0.5
			var ghost3: float = 0.3 if int(b.age) <= int(b.arm) else 1.0
			var start: float = float(b.gap) + gw2
			var span: float = TAU - 2.0 * gw2
			for k: int in range(7):
				var a0: float = start + span * float(k) / 7.0
				c.draw_arc(at, float(b.radius), a0, a0 + span / 7.0 + 0.02, maxi(6, int(float(b.radius) * 0.12)), Color(DYES[(k + int(b.get("hue", 0))) % DYES.size()], 0.95 * alpha * ghost3), 6)
			return true
	return false

## A glowing music note: a halo, a note head, a stem and a flag.
static func _note_art(c: CanvasItem, at: Vector2, now: float) -> void:
	c.draw_circle(at, 8.0 + 2.0 * sin(now * 0.2), Color(AMBER, 0.25))
	var head: PackedVector2Array = PackedVector2Array()
	for i: int in range(10):
		head.append(at + Vector2(-2.0, 3.0) + Vector2(cos(float(i) * TAU / 10.0) * 3.4, sin(float(i) * TAU / 10.0) * 2.5).rotated(-0.45))
	c.draw_colored_polygon(head, AMBER)
	c.draw_line(at + Vector2(1.0, 2.0), at + Vector2(1.0, -7.0), AMBER, 1)
	c.draw_polyline(PackedVector2Array([at + Vector2(1.0, -7.0), at + Vector2(5.0, -5.0), at + Vector2(4.0, -2.0)]), AMBER, 1)

## The bus: a two-tone van with a peace sign, a bubble wand on the roof; face = way it drives.
static func _bus(c: CanvasItem, at: Vector2, face: float, now: int) -> void:
	var f: float = face if face != 0.0 else 1.0
	c.draw_colored_polygon(PackedVector2Array([at + Vector2(-20, -7), at + Vector2(20, -7), at + Vector2(22, -3), at + Vector2(22, 6), at + Vector2(-22, 6), at + Vector2(-22, -3)]), Color(CREAM, 0.55))
	c.draw_colored_polygon(PackedVector2Array([at + Vector2(-22, 0), at + Vector2(22, 0), at + Vector2(22, 6), at + Vector2(-22, 6)]), Color(ROSE, 0.55))
	for k: int in range(4):
		c.draw_rect(Rect2(at + Vector2(-16 + k * 9, -5), Vector2(7, 4)), Color(BLUE, 0.6))
	c.draw_arc(at + Vector2(-f * 8, 3), 2.2, 0.0, TAU, 8, Color(AMBER, 0.8), 1)
	c.draw_line(at + Vector2(-f * 8, 1), at + Vector2(-f * 8, 5), Color(AMBER, 0.8), 1)
	c.draw_circle(at + Vector2(f * 21, 1), 1.5, Color(AMBER, 0.9))
	for wx: float in [-13.0, 13.0]:
		c.draw_circle(at + Vector2(wx, 7), 3.0, Color(INK, 0.9))
		c.draw_arc(at + Vector2(wx, 7), 3.0, 0.0, TAU, 8, Color(CREAM, 0.7), 1)
	c.draw_line(at + Vector2(0, -7), at + Vector2(0, -12), Color(CREAM, 0.6), 1)
	c.draw_arc(at + Vector2(0, -14), 2.5 + 0.5 * sin(float(now) * 0.3), 0.0, TAU, 8, Color(BLUE, 0.8), 1)
