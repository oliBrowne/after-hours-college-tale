extends RefCounted
## CHAD, NETWORKING LEGEND: "Let's circle back. Coffee chat? Coffee chat." A
## relentless campus networker in a quarter-zip vest, with a ring light and LED
## business cards, who keeps trying to book the one FREE slot on your calendar.
## Four handmade attacks, one per turn, cycling. The promise never changes (it is
## EMPTY CHAIR's, re-dressed): stay in the Do Not Disturb bubble for 120 ticks
## while promised, and never step into the FREE slot (a plum avoid zone drawn as
## a calendar block; stepping in books it and breaks the promise). The bubble
## shelters you, so every attack is about the bubble moving, being switched off
## or crowded, and about the space around the slot, which pulls at you like a
## calendar that wants to be full. You don't have to fill every gap.
## Phase 1 (from the second turn) adds a layer to every attack.
## The state field names (quietTicks, chairEntered, pocket, pocketLit, lamps,
## chairGhost, ...) are EMPTY CHAIR's on purpose: the promise logic is the same.

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
const LINK: Color = Color("5b8fd6")
const NAVY: Color = Color("1d2a44")
const LED: Color = Color("7fe3f0")
const STEAM: Color = Color("ddd3c4")
const MOON: Color = Color("f0e2b6")
const COFFEE: Color = Color("8a5a3c")
const INK: Color = Color("0a0c17")

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
	s.longBanner = ""
	s.longTicks = 0
	# You start in the Do Not Disturb bubble, left of the free slot.
	s.soul.x = -80.0; s.soul.y = 30.0
	D.objective(s, {"kind": "avoid", "x": 0.0, "y": 0.0, "w": 24.0, "h": 28.0, "always": true, "chair": true})
	match id:
		"lantern":
			s.phaseName = "Do Not Disturb"
			s.hint = "The DND bubble circles your free slot. Rest inside it; pings fall everywhere else."
			s.pocket = _rect_at(_orbit_point(0), Vector2(26, 19))
			s.pull = 0.24
		"lamps":
			s.phaseName = "Three Coffee Chats"
			s.hint = "One coffee chat at a time. Go when the next cup blinks. Slip through steam rings."
			s.lamps = [Vector2(-80, 28), Vector2(0, -42), Vector2(80, 28)]
			s.pocket = _rect_at(s.lamps[0], Vector2(26, 16))
		"guests":
			s.phaseName = "Let's Circle Back"
			s.hint = "Networkers march on your free slot. Let them pass. Follow the DND bubble along the floor."
			s.pocket = _rect_at(Vector2(-80, 32), Vector2(26, 18))
			s.pull = 0.24
		"make_room":
			s.phaseName = "Quick Sync?"
			s.hint = "Chad keeps moving your free slot. Step aside, then come back to the DND bubble."
			s.chairPath = [[60, 110, Vector2(-60, 22)], [170, 230, Vector2(66, -14)], [290, 340, Vector2(-60, 22)], [380, 420, Vector2(0, 0)]]

static func _rect_at(centre: Vector2, half: Vector2) -> Rect2:
	return Rect2(centre - half, half * 2.0)

## The FREE slot is objective 0 (an avoid zone).
static func _chair(s: Dictionary) -> Dictionary:
	return s.objectives[0]

static func _chair_rect(s: Dictionary) -> Rect2:
	var o: Dictionary = _chair(s)
	return Rect2(float(o.x) - float(o.w), float(o.y) - float(o.h), float(o.w) * 2.0, float(o.h) * 2.0)

## Banners: the view's own banner holds about 25 characters; longer lines are
## drawn here (draw_over) in the same spot.
static func _say(s: Dictionary, text: String, ticks: int, col: Color = AMBER) -> void:
	s.bannerColor = col
	if text.length() > 25:
		D.banner(s, "", 0)
		s.longBanner = text; s.longTicks = ticks
	else:
		D.banner(s, text, ticks)
		s.longTicks = 0

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
	# The free slot pulls at you a little: a calendar wants to be full.
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var chair: Rect2 = _chair_rect(s)
	# (It lets go a little way from the slot's edge.)
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
			_say(s, "YOU DON'T HAVE TO FILL EVERY GAP", 70, MINT)
	# Autopilot: rest in the part of the bubble that the slot does not cover.
	var goal: Vector2 = pocket.get_center()
	if s.pocketLit: goal = _free_spot(pocket, chair)
	if int(s.nextLamp) >= 0: goal = Vector2(s.lamps[int(s.nextLamp)])
	if s.chairGhost != null or not s.pocketLit:
		# Wait beside the bubble, clear of where the slot is (or is going).
		var seat: Rect2 = chair if s.chairGhost == null else Rect2(Vector2(s.chairGhost) - chair.size * 0.5, chair.size)
		goal = _aside(s, pocket.get_center(), seat.merge(chair) if s.chairGhost != null else seat)
	s.botGoal = _lead(soul, _around(soul, goal, chair))

## Autopilot waypoint: go round the slot's corner instead of through it.
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
	s.longTicks = maxi(0, int(s.get("longTicks", 0)) - 1)
	if _chair(s).broken and not s.chairEntered:
		s.chairEntered = true
		_say(s, "YOU BOOKED THE FREE SLOT", 60, ROSE)

# ---------------------------------------------------------------- do not disturb

static func _orbit_point(t: int) -> Vector2:
	var a: float = PI * 0.82 + maxf(0.0, float(t - 40)) * 0.0118
	return Vector2(cos(a) * 84.0, sin(a) * 37.0)

## Do Not Disturb: the DND bubble walks an ellipse around the free slot;
## notification pings rain down marked columns, every other one aimed where you
## stand. At the top and bottom of its walk the bubble passes the slot, so only
## a strip of it is yours. Phase 1: "+1 SYNERGY" endorsements circle the bubble,
## and three times Chad's ring light sweeps in and flashes it (DND switches off
## for a moment, so step out and dodge).
static func _lantern(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 248.0, "h": 118.0}, 24)
		if phase > 0:
			_say(s, "ENDORSED: +1 SYNERGY", 50)
			for i: int in range(5):
				D.shot(s, {"space": "box", "orbit": {"ox": 0.0, "oy": 0.0, "radius": 36.0, "angle": i * TAU / 5.0, "av": 0.045}, "arm": 40, "r": 2.5, "shape": "endorse", "life": 900, "moth": true})
		else:
			_say(s, "5 PEOPLE VIEWED YOUR PROFILE", 60)
	if phase == 0:
		if t == 150: _say(s, "CHAD WANTS TO CONNECT", 50)
		if t == 290: _say(s, "3 NEW PINGS. COFFEE?", 50)
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
				_say(s, "RING LIGHT ON. SMILE!", 30)
				D.warn(s, {"kind": "none"}, 1, true)
			if t == g:
				s.pocketLit = false
				_say(s, "DND PAUSED. KEEP MOVING", 40)
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
			D.shot(s, {"space": "box", "x": float(col.x) + D.rand_range(s, -3.0, 3.0), "y": -h.y - 4.0, "vy": 2.5, "r": 2.6, "shape": "ping", "life": 80, "wave": {"amp": 2.5, "freq": 0.12, "phase": D.rand(s) * TAU}})

# ---------------------------------------------------------------- three coffee chats

## Three Coffee Chats: one cup is hot at a time (that is where the bubble is);
## the next cup blinks before Chad moves the chat there. Steam rings spread from
## the free slot with one gap each, and LED business cards drift across.
## Phase 1: the chats move faster and the rings come in pairs with offset gaps.
static func _lamps(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 248.0, "h": 118.0}, 24)
		_say(s, "COFFEE CHAT?", 40)
	var switches: Array = [90, 180, 270] if phase > 0 else [130, 260]
	var order: Array[int] = [0, 1, 2, 1, 0]
	for i: int in range(switches.size()):
		if t == int(switches[i]) - 50:
			s.nextLamp = order[i + 1]
			_say(s, "COFFEE CHAT? COFFEE CHAT.", 44)
			D.warn(s, {"kind": "none"}, 1, true)
		if t == int(switches[i]):
			s.lamp = order[i + 1]
			s.nextLamp = -1
			s.pocket = _rect_at(s.lamps[int(s.lamp)], Vector2(26, 16))
	var every: int = 50
	if t % every == 20 and t < 390:
		_steam(s, 0.0)
	if phase > 0 and t % every == 34 and t < 390:
		_steam(s, 0.8 if int(t / every) % 2 == 0 else -0.8)
	if t % 30 == 0 and t > 20 and t < 400:
		var from: float = -1.0 if D.rand(s) < 0.5 else 1.0
		var y: float = D.rand_range(s, -h.y + 10.0, h.y - 10.0)
		if int(t / 30) % 3 == 0: y = clampf(float(s.soul.y), -h.y + 10.0, h.y - 10.0)
		D.warn(s, {"kind": "edge", "space": "box", "x": from * (h.x - 4.0), "y": y, "dir": Vector2(-from, 0)}, 30)
		D.shot(s, {"space": "box", "x": from * (h.x + 10.0 + 1.6 * 30.0), "y": y, "vx": -from * 1.6, "collide": "rect", "w": 5.0, "h": 4.0, "shape": "card", "rot": 0.0, "spin": 0.03, "wave": {"amp": 4.0, "freq": 0.07, "phase": D.rand(s) * TAU}, "life": 260})

static func _steam(s: Dictionary, offset: float) -> void:
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var gap: float = soul.angle() + D.rand_range(s, 0.45, 0.9) * (-1.0 if D.rand(s) < 0.5 else 1.0) + offset
	D.shot(s, {"space": "box", "x": 0.0, "y": 0.0, "collide": "ring", "radius": 24.0, "grow": 1.25, "thick": 2.0, "gap": gap, "gapWidth": 0.85, "shape": "steam", "maxRadius": 150.0})
	D.effect(s, "pulse", D.to_world(s, Vector2.ZERO), 14)

# ---------------------------------------------------------------- let's circle back

## Let's Circle Back: networkers (vest, outstretched hand, LED card) fade in at
## the edges, then march on the free slot; the slot declines them and they
## vanish. Some walk the line through you. The DND bubble slides along the
## floor, under the slot and back. Phase 1: they circle back from the slot and
## walk out again, faster.
static func _guests(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 248.0, "h": 118.0}, 24)
		_say(s, "LET'S CIRCLE BACK", 50)
	if phase > 0 and t == 200: _say(s, "CIRCLING BACK!", 40)
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
		D.shot(s, {"space": "box", "x": start.x, "y": start.y, "vx": v.x, "vy": v.y, "hold": true, "arm": 36, "r": 4.5, "shape": "networker", "life": 300, "guest": true})
	var chair: Rect2 = _chair_rect(s).grow(2.0)
	for b: Dictionary in s.bullets:
		if not b.get("guest", false) or b.get("left", false): continue
		if chair.has_point(Vector2(float(b.x), float(b.y))):
			var at: Vector2 = D.to_world(s, Vector2(float(b.x), float(b.y)))
			if phase > 0:
				b.left = true
				b.vx = -float(b.vx) * 1.5; b.vy = -float(b.vy) * 1.5
				D.effect(s, "block", at, 12)
				D.effect(s, "circle", at, 20)
			else:
				b.dead = true
				D.effect(s, "declined", at, 18)

static func _edge_point(h: Vector2, dir: Vector2) -> Vector2:
	var sx: float = (h.x - 6.0) / maxf(0.001, absf(dir.x))
	var sy: float = (h.y - 6.0) / maxf(0.001, absf(dir.y))
	return dir * minf(sx, sy)

# ---------------------------------------------------------------- quick sync?

## Quick Sync?: Chad drags your free slot around the week (its next place is
## outlined first), twice right over the DND bubble so you must step aside.
## Calendar invites slide in along marked rows to fill the week, and each time
## the slot lands it sends a burst of invites. Phase 1: rows come in pairs and
## the bursts are fuller.
static func _make_room(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0: D.box_to(s, {"w": 248.0, "h": 118.0}, 24)
	var o: Dictionary = _chair(s)
	var from: Vector2 = Vector2(0, 0)
	var calls: Array[String] = ["QUICK SYNC?", "MOVING YOUR FREE TIME", "ANOTHER QUICK SYNC?", "OK, PUTTING IT BACK"]
	s.chairGhost = null
	var leg_i: int = 0
	for leg: Array in s.chairPath:
		var start: int = int(leg[0]); var stop: int = int(leg[1]); var to: Vector2 = leg[2]
		if t >= start - 50 and t < start:
			s.chairGhost = to
			if t == start - 50:
				D.warn(s, {"kind": "none"}, 1, true)
				_say(s, calls[mini(leg_i, calls.size() - 1)], 46)
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
					D.shot(s, {"space": "box", "x": to.x + cos(a) * 20.0, "y": to.y + sin(a) * 20.0, "vx": cos(a) * 1.05, "vy": sin(a) * 1.05, "hold": true, "arm": 24, "collide": "rect", "w": 4.5, "h": 5.0, "shape": "invite", "rot": a + PI * 0.5, "life": 200})
		from = to
		leg_i += 1
	# Where the slot lands on the bubble, DND is overruled.
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
		D.shot(s, {"space": "box", "x": side * (h.x + 12.0 + speed * 34.0 + i * 20.0), "y": y, "vx": -side * speed, "collide": "rect", "w": 4.5, "h": 5.0, "shape": "invite", "life": 220})

# ---------------------------------------------------------------- progress / drawing

static func progress(s: Dictionary) -> String:
	return "Quiet time %d/120\nKeep the slot FREE" % mini(120, int(s.quietTicks))

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var clock: int = int(s.clock)
	var t: int = clock - int(s.leadIn)
	# A night-mode calendar week: five day columns, faint hour lines.
	for i: int in range(1, 5):
		var x: float = -h.x + h.x * 2.0 * i / 5.0
		c.draw_line(v.box_point(Vector2(x, -h.y)), v.box_point(Vector2(x, h.y)), Color(LILAC, 0.08), 1)
	for j: int in range(1, 6):
		var y: float = -h.y + h.y * 2.0 * j / 6.0
		c.draw_line(v.box_point(Vector2(-h.x, y)), v.box_point(Vector2(h.x, y)), Color(LILAC, 0.04), 1)
	var days: Array[String] = ["M", "T", "W", "T", "F"]
	for i: int in range(5):
		v.text(c, v.box_point(Vector2(-h.x + h.x * 2.0 * (i + 0.5) / 5.0, -h.y + 11.0)), days[i], Color(LILAC, 0.16), 16.0)
	# Telegraphs.
	for w: Dictionary in s.warnings:
		var f: float = 0.5 + 0.5 * sin(float(w.age) * 0.5)
		match str(w.kind):
			"column":
				var poly: PackedVector2Array = v.box_rect_poly(Rect2(float(w.x) - float(w.w), -h.y, float(w.w) * 2.0, h.y * 2.0))
				c.draw_colored_polygon(poly, Color(ROSE, 0.06 + 0.12 * f))
				_bell(c, v.box_point(Vector2(float(w.x), -h.y + 5.0)), Color(ROSE, 0.6 + 0.4 * f))
			"row":
				var poly2: PackedVector2Array = v.box_rect_poly(Rect2(-h.x, float(w.y) - float(w.h), h.x * 2.0, float(w.h) * 2.0))
				c.draw_colored_polygon(poly2, Color(ROSE, 0.06 + 0.12 * f))
				c.draw_polyline(poly2 + PackedVector2Array([poly2[0]]), Color(ROSE, 0.35), 1)
	# The FREE slot: a calendar block under the view's plum hatching. Faint
	# chevrons show it pulling at you.
	var chair: Rect2 = _chair_rect(s)
	if float(s.pull) > 0.0: _pull_marks(c, v, chair, clock)
	_draw_slot(c, v, chair, 1.0, false)
	if s.chairGhost != null:
		var ghost: Rect2 = Rect2(Vector2(s.chairGhost) - chair.size * 0.5, chair.size)
		var blink: float = 0.4 + 0.4 * sin(float(clock) * 0.3)
		_draw_slot(c, v, ghost, blink, true)
		c.draw_line(v.box_point(chair.get_center()), v.box_point(Vector2(s.chairGhost)), Color(LINK.lightened(0.3), 0.35), 1)
		var dir: Vector2 = (Vector2(s.chairGhost) - chair.get_center()).normalized()
		if dir != Vector2.ZERO: v.chevron(c, v.box_point(Vector2(s.chairGhost) - dir * 8.0), dir.rotated(float(s.box.rot)), Color(LINK.lightened(0.3), blink))
	# The other coffee cups: the next one blinks, the cold ones are outlines.
	for i: int in range(s.lamps.size()):
		if i == int(s.lamp) and s.pocketLit: continue
		var r: Rect2 = _rect_at(s.lamps[i], Vector2(26, 16))
		var lp: PackedVector2Array = _round_poly(v, r, 6.0)
		var next: bool = i == int(s.nextLamp)
		var col: Color = Color(MINT, 0.3 + 0.6 * float((clock / 8) % 2)) if next else Color(PLUM, 0.6)
		_dashed_loop(c, lp, col)
		_cup_icon(c, v.box_point(Vector2(r.get_center().x, r.end.y - 4.0)), 0.9 if next else 0.3, next, clock)
	# Chad's ring light (Do Not Disturb, phase 1) sweeps in over the bubble.
	var pocket: Rect2 = s.pocket
	if str(s.patternId) == "lantern" and int(s.flicker) >= 0:
		_ring_light(c, v, s, pocket, t - int(s.flicker), clock)
	# The Do Not Disturb bubble.
	var poly3: PackedVector2Array = _round_poly(v, pocket, 6.0)
	var lit: bool = s.pocketLit
	var warn: bool = int(s.flicker) >= 0 and (clock / 5) % 2 == 0
	var icon_at: Vector2 = v.box_point(Vector2(pocket.get_center().x, pocket.end.y - 5.0))
	if lit and not warn:
		var flick: float = 0.85 + 0.15 * sin(float(clock) * 0.11)
		c.draw_circle(v.box_point(pocket.get_center()), maxf(pocket.size.x, pocket.size.y) * 0.62, Color(0.55, 0.6, 0.98, 0.06 * flick))
		c.draw_colored_polygon(poly3, Color(0.5, 0.55, 0.92, 0.13 * flick))
		c.draw_polyline(poly3 + PackedVector2Array([poly3[0]]), MINT, 2)
	else:
		_dashed_loop(c, poly3, Color(PLUM.lightened(0.2), 0.8))
	var glow: float = 1.0 if lit and not warn else 0.35
	if str(s.patternId) == "lamps": _cup_icon(c, icon_at, glow, lit, clock)
	else: _moon_icon(c, icon_at, glow, lit, clock)
	var fill: float = clampf(float(s.quietTicks) / float(NEED), 0.0, 1.0)
	var base: Vector2 = v.box_point(Vector2(pocket.position.x + 4.0, pocket.end.y + 3.0))
	c.draw_line(base, v.box_point(Vector2(pocket.end.x - 4.0, pocket.end.y + 3.0)), Color(MINT, 0.2), 2)
	if fill > 0.0: c.draw_line(base, v.box_point(Vector2(pocket.position.x + 4.0 + (pocket.size.x - 8.0) * fill, pocket.end.y + 3.0)), MINT, 2)

## A rectangle with cut corners (screen points), for the bubble and cups.
static func _round_poly(v: Node2D, r: Rect2, k: float) -> PackedVector2Array:
	var a: Vector2 = r.position; var b: Vector2 = r.end
	var pts: Array[Vector2] = [Vector2(a.x + k, a.y), Vector2(b.x - k, a.y), Vector2(b.x, a.y + k), Vector2(b.x, b.y - k), Vector2(b.x - k, b.y), Vector2(a.x + k, b.y), Vector2(a.x, b.y - k), Vector2(a.x, a.y + k)]
	var out: PackedVector2Array = []
	for p: Vector2 in pts: out.append(v.box_point(p))
	return out

static func _dashed_loop(c: CanvasItem, poly: PackedVector2Array, col: Color) -> void:
	for k: int in range(poly.size()): _dashed(c, poly[k], poly[(k + 1) % poly.size()], col)

static func _dashed(c: CanvasItem, a: Vector2, b: Vector2, col: Color) -> void:
	var n: int = maxi(1, int(a.distance_to(b) / 6.0))
	for i: int in range(0, n, 2):
		c.draw_line(a.lerp(b, float(i) / n), a.lerp(b, float(mini(i + 1, n)) / n), col, 1)

## The FREE slot as a calendar block: dark card, blue header with a clock, hour
## ticks down the side. A ghost (where it is being moved to) is dashed only.
static func _draw_slot(c: CanvasItem, v: Node2D, r: Rect2, alpha: float, ghost: bool) -> void:
	var poly: PackedVector2Array = v.box_rect_poly(r)
	if ghost:
		for i: int in range(4): _dashed(c, poly[i], poly[(i + 1) % 4], Color(LINK.lightened(0.3), alpha))
		var head: PackedVector2Array = v.box_rect_poly(Rect2(r.position, Vector2(r.size.x, 8.0)))
		c.draw_colored_polygon(head, Color(LINK, 0.25 * alpha))
		return
	c.draw_colored_polygon(poly, Color(NAVY, 0.85 * alpha))
	var head2: PackedVector2Array = v.box_rect_poly(Rect2(r.position, Vector2(r.size.x, 9.0)))
	c.draw_colored_polygon(head2, Color(LINK, 0.55 * alpha))
	var clock_at: Vector2 = v.box_point(r.position + Vector2(6.0, 4.5))
	c.draw_arc(clock_at, 2.6, 0, TAU, 10, Color(CREAM, 0.8 * alpha), 1)
	c.draw_line(clock_at, clock_at + Vector2(0, -1.8), Color(CREAM, 0.8 * alpha), 1)
	c.draw_line(clock_at, clock_at + Vector2(1.4, 0), Color(CREAM, 0.8 * alpha), 1)
	for k: int in range(1, 4):
		var y: float = r.position.y + 9.0 + (r.size.y - 9.0) * k / 4.0
		c.draw_line(v.box_point(Vector2(r.position.x + 2.0, y)), v.box_point(Vector2(r.position.x + 6.0, y)), Color(LILAC, 0.5 * alpha), 1)
	c.draw_line(v.box_point(Vector2(r.position.x + 1.0, r.position.y + 9.0)), v.box_point(Vector2(r.position.x + 1.0, r.end.y - 1.0)), Color(MINT, 0.5 * alpha), 2)

## Faint chevrons drifting in toward the slot: the calendar's pull.
static func _pull_marks(c: CanvasItem, v: Node2D, chair: Rect2, clock: int) -> void:
	var cc: Vector2 = chair.get_center()
	for i: int in range(8):
		var dir: Vector2 = Vector2.from_angle(i * TAU / 8.0 + 0.39)
		var d: float = 28.0 - fposmod(float(clock) * 0.3 + i * 9.0, 24.0)
		var at: Vector2 = cc + Vector2(dir.x * (chair.size.x * 0.5 + d + 2.0), dir.y * (chair.size.y * 0.5 + d * 0.7 + 2.0))
		var a: float = 0.22 * sin(PI * clampf((d - 4.0) / 24.0, 0.0, 1.0))
		v.chevron(c, v.box_point(at), -dir, Color(LILAC, a))

static func _bell(c: CanvasItem, at: Vector2, col: Color) -> void:
	c.draw_arc(at + Vector2(0, 1), 3.0, PI, TAU, 8, col, 2)
	c.draw_line(at + Vector2(-3, 1), at + Vector2(-3.5, 3), col, 1)
	c.draw_line(at + Vector2(3, 1), at + Vector2(3.5, 3), col, 1)
	c.draw_line(at + Vector2(-4.5, 3), at + Vector2(4.5, 3), col, 1)
	c.draw_circle(at + Vector2(0, 4.5), 1.0, col)

## A crescent moon (and a little "z") for Do Not Disturb.
static func _moon_icon(c: CanvasItem, at: Vector2, glow: float, raised: bool, clock: int) -> void:
	if raised: c.draw_circle(at + Vector2(0, -1), 7.0, Color(MOON, 0.12 * glow))
	c.draw_colored_polygon(_crescent(at + Vector2(0, -1), 3.8), Color(MOON, glow))
	if raised:
		var bob: float = sin(float(clock) * 0.08) * 1.0
		var z: Vector2 = at + Vector2(5, -7 + bob)
		var zc: Color = Color(MOON, 0.7 * glow)
		c.draw_polyline(PackedVector2Array([z, z + Vector2(3, 0), z + Vector2(0, 3), z + Vector2(3, 3)]), zc, 1)

## A filled crescent: the outer circle minus a circle shifted up and right.
static func _crescent(at: Vector2, big: float) -> PackedVector2Array:
	var small: float = big * 0.87
	var shift: float = big * 0.47
	var d: Vector2 = Vector2(1.0, -0.6).normalized()
	var x: float = (big * big - small * small + shift * shift) / (2.0 * shift)
	var y: float = sqrt(maxf(0.0, big * big - x * x))
	var a1: float = atan2(y, x)
	var b1: float = atan2(y, x - shift)
	var pts: PackedVector2Array = []
	for i: int in range(9):
		var a: float = lerpf(a1, TAU - a1, float(i) / 8.0)
		pts.append(at + Vector2.from_angle(a).rotated(d.angle()) * big)
	for i: int in range(9):
		var b: float = lerpf(TAU - b1, b1, float(i) / 8.0)
		pts.append(at + (Vector2(shift, 0) + Vector2.from_angle(b) * small).rotated(d.angle()))
	return pts

## A coffee cup; steaming when hot.
static func _cup_icon(c: CanvasItem, at: Vector2, glow: float, hot: bool, clock: int) -> void:
	if hot: c.draw_circle(at + Vector2(0, -2), 7.0, Color(AMBER, 0.12 * glow))
	c.draw_rect(Rect2(at + Vector2(-3.5, -5), Vector2(7, 6)), Color(CREAM, glow))
	c.draw_line(at + Vector2(-3, -4.5), at + Vector2(3, -4.5), Color(COFFEE, glow), 1)
	c.draw_arc(at + Vector2(4, -2), 1.8, -PI * 0.5, PI * 0.5, 6, Color(CREAM, glow), 1)
	c.draw_line(at + Vector2(-5, 1.5), at + Vector2(5, 1.5), Color(CREAM, 0.8 * glow), 1)
	if hot:
		for k: int in range(2):
			var pts: PackedVector2Array = []
			for j: int in range(5):
				var y: float = -7.0 - j * 1.6
				pts.append(at + Vector2(-1.5 + k * 3.0 + sin(y * 0.9 + float(clock) * 0.18 + k) * 1.1, y))
			c.draw_polyline(pts, Color(STEAM, 0.6 * glow), 1)

## Chad's ring light: slides in from the near edge along the top of the box
## (30 ticks of warning), then flashes the bubble while DND is off.
static func _ring_light(c: CanvasItem, v: Node2D, s: Dictionary, pocket: Rect2, since: int, clock: int) -> void:
	var h: Vector2 = D.half(s)
	var px: float = pocket.get_center().x
	var p: float = clampf(float(since) / 30.0, 0.0, 1.0)
	p = p * p * (3.0 - 2.0 * p)
	var from: float = (h.x + 14.0) * (1.0 if px >= 0.0 else -1.0)
	var lx: float = lerpf(from, px, p)
	var light: Vector2 = Vector2(lx, -h.y + 11.0)
	var on: bool = since >= 30
	var pulse: float = 0.5 + 0.5 * sin(float(clock) * 0.9)
	var cone_a: float = (0.12 + 0.08 * pulse) if on else 0.05 * p
	var top: float = minf(pocket.position.y, light.y + 6.0)
	var cone: PackedVector2Array = PackedVector2Array([v.box_point(light + Vector2(-6, 6)), v.box_point(light + Vector2(6, 6)), v.box_point(Vector2(pocket.end.x, maxf(top, pocket.end.y))), v.box_point(Vector2(pocket.position.x, maxf(top, pocket.end.y)))])
	c.draw_colored_polygon(cone, Color(1.0, 0.97, 0.88, cone_a))
	if on: c.draw_colored_polygon(_round_poly(v, pocket, 6.0), Color(1.0, 0.98, 0.9, 0.12 + 0.1 * pulse))
	c.draw_line(v.box_point(Vector2(lx, -h.y)), v.box_point(light + Vector2(0, -7)), Color(Color("4a4458"), 1.0), 2)
	var at: Vector2 = v.box_point(light)
	c.draw_arc(at, 7.0, 0, TAU, 20, Color(1.0, 0.96, 0.86, 0.6 + 0.4 * (pulse if on else p)), 3)
	c.draw_rect(Rect2(at + Vector2(-2, -3.5), Vector2(4, 7)), Color("1c2033"))
	c.draw_rect(Rect2(at + Vector2(-2, -3.5), Vector2(4, 7)), Color(LED, 0.8), false, 1)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	# The slot's label sits on top of the hatching so it stays readable.
	var chair: Rect2 = _chair_rect(s)
	var label: String = "BOOKED" if s.chairEntered else "FREE"
	var at: Vector2 = v.box_point(chair.get_center() + Vector2(0, 4))
	var plate_w: float = label.length() * 8.0 + 4.0
	c.draw_rect(Rect2(at + Vector2(-plate_w * 0.5, -11), Vector2(plate_w, 13)), Color(INK, 0.85))
	c.draw_rect(Rect2(at + Vector2(-plate_w * 0.5, -11), Vector2(plate_w, 13)), Color(ROSE if s.chairEntered else LINK.lightened(0.2), 0.8), false, 1)
	v.text(c, at, label, ROSE if s.chairEntered else CREAM, plate_w + 8.0)
	# Our own effects: a declined invite (a little X) and a circle-back arrow.
	for e: Dictionary in s.effects:
		var p: float = float(e.age) / float(e.life)
		var e_at: Vector2 = v.arena_point(Vector2(float(e.x), float(e.y)))
		match str(e.kind):
			"declined":
				var k: float = 3.0 + p * 2.0
				var col: Color = Color(LILAC.lightened(0.3), 1.0 - p)
				c.draw_line(e_at + Vector2(-k, -k), e_at + Vector2(k, k), col, 1)
				c.draw_line(e_at + Vector2(-k, k), e_at + Vector2(k, -k), col, 1)
			"circle":
				var r: float = 5.0 + p * 4.0
				var col2: Color = Color(ROSE, 0.9 * (1.0 - p))
				var a0: float = p * 3.0
				c.draw_arc(e_at, r, a0, a0 + PI * 1.5, 12, col2, 1)
				var tip: Vector2 = e_at + Vector2.from_angle(a0 + PI * 1.5) * r
				var tangent: Vector2 = Vector2.from_angle(a0 + PI * 2.0)
				v.chevron(c, tip, tangent, col2)
	# Long banners (the view's banner fits about 25 characters).
	if int(s.get("longTicks", 0)) > 0 and int(s.longTicks) % 16 < 11 and v.font != null:
		var top: Vector2 = v.arena_point(D.centre(s)) + Vector2(0, -D.half(s).y - 8.0)
		c.draw_string(v.font, top + Vector2(-160, 0), str(s.longBanner), HORIZONTAL_ALIGNMENT_CENTER, 320, 12, Color(s.get("bannerColor", AMBER)))

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	var armed: bool = int(b.age) > int(b.arm)
	match str(b.shape):
		"ping":
			# A notification badge falling down its column.
			c.draw_line(at + Vector2(0, -8), at + Vector2(0, -3), Color(ROSE, 0.25 * alpha), 2)
			c.draw_circle(at, float(b.r) + 2.0, Color(ROSE, 0.16 * alpha))
			c.draw_circle(at, float(b.r) + 0.4, Color(ROSE, alpha))
			c.draw_line(at + Vector2(0, -1.4), at + Vector2(0, 0.4), Color(CREAM, alpha), 1)
			c.draw_rect(Rect2(at + Vector2(-0.5, 1.0), Vector2(1, 1)), Color(CREAM, alpha))
			return true
		"endorse":
			# "+1 SYNERGY": a little blue endorsement pill.
			var a: float = alpha * (1.0 if armed else 0.4)
			c.draw_rect(Rect2(at + Vector2(-4, -3), Vector2(8, 6)), Color(LINK, a))
			c.draw_rect(Rect2(at + Vector2(-4, -3), Vector2(8, 6)), Color(LINK.lightened(0.4), a), false, 1)
			c.draw_line(at + Vector2(-2.5, 0), at + Vector2(0.5, 0), Color(CREAM, a), 1)
			c.draw_line(at + Vector2(-1, -1.5), at + Vector2(-1, 1.5), Color(CREAM, a), 1)
			c.draw_line(at + Vector2(2.5, -1.5), at + Vector2(2.5, 1.5), Color(CREAM, a), 1)
			return true
		"steam":
			# A steam ring from the slot, with one clear gap.
			var rot: float = float(v.pattern.box.rot) if b.space == "box" else 0.0
			var gw: float = float(b.gapWidth) * 0.5
			var r: float = float(b.radius)
			var g0: float = float(b.gap) + rot
			var segs: int = maxi(24, int(r * 0.6))
			c.draw_arc(at, r, g0 + gw, g0 + TAU - gw, segs, Color(STEAM, 0.9 * alpha), float(b.thick) * 2.0)
			var puffs: int = maxi(6, int((TAU - gw * 2.0) * r / 13.0))
			for i: int in range(puffs):
				var ang: float = g0 + gw + (TAU - gw * 2.0) * (i + 0.5) / puffs
				var wob: float = sin(ang * 5.0 + float(b.age) * 0.15) * 0.8
				c.draw_circle(at + Vector2.from_angle(ang) * (r + wob), 2.7, Color(STEAM, 0.3 * alpha))
			c.draw_arc(at, r - float(b.thick) - 2.0, g0 + gw, g0 + TAU - gw, segs, Color(COFFEE.lightened(0.3), 0.3 * alpha), 1)
			return true
		"card":
			# An LED business card.
			c.draw_colored_polygon(v.quad(at, float(b.w) + 1.5, float(b.h) + 1.5, turn), Color(LED, 0.16 * alpha))
			var q: PackedVector2Array = v.quad(at, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(q, Color(NAVY.lightened(0.1), alpha))
			c.draw_polyline(q + PackedVector2Array([q[0]]), Color(LED, alpha), 1)
			c.draw_line(at + Vector2(-3, -1).rotated(turn), at + Vector2(2, -1).rotated(turn), Color(CREAM, alpha), 1)
			c.draw_line(at + Vector2(-3, 1.5).rotated(turn), at + Vector2(0, 1.5).rotated(turn), Color(AMBER, alpha), 1)
			return true
		"networker":
			# A networker in a vest, hand out, card ready.
			var a2: float = alpha * (0.9 if armed else 0.12 + 0.3 * float(b.age) / maxf(1.0, float(b.arm)))
			var left: bool = b.get("left", false)
			var vest: Color = Color(ROSE.darkened(0.1), a2) if left else Color(LINK, a2)
			var skin: Color = Color(CREAM, a2)
			var dir: Vector2 = Vector2(float(b.vx), float(b.vy))
			if b.space == "box": dir = dir.rotated(float(v.pattern.box.rot))
			dir = dir.normalized() if dir.length() > 0.01 else Vector2.RIGHT
			c.draw_circle(at + Vector2(0, -4), 2.5, skin)
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-4.5, 5), at + Vector2(-3, -1), at + Vector2(3, -1), at + Vector2(4.5, 5)]), vest)
			c.draw_line(at + Vector2(0, -1), at + Vector2(0, 5), Color(CREAM, a2 * 0.7), 1)
			var shoulder: Vector2 = at + Vector2(signf(dir.x) * 2.5 if absf(dir.x) > 0.2 else 0.0, 0.5)
			var hand: Vector2 = shoulder + dir * 5.5
			c.draw_line(shoulder, hand, skin, 1)
			c.draw_rect(Rect2(hand + Vector2(-1.5, -1), Vector2(3, 2)), Color(LED, a2))
			if left:
				c.draw_arc(at + Vector2(0, -4), 6.0, -PI * 0.95, PI * 0.35, 10, Color(ROSE, 0.6 * a2), 1)
			if not armed: c.draw_arc(at, 7.0, 0, TAU, 14, Color(LINK, 0.3), 1)
			return true
		"invite":
			# A calendar invite: blue block, darker header, a plus.
			var a3: float = alpha * (1.0 if armed else 0.35 + 0.3 * sin(float(b.age) * 0.5))
			var q2: PackedVector2Array = v.quad(at, 5.0, 5.5, turn)
			c.draw_colored_polygon(q2, Color(LINK, 0.9 * a3))
			var up: Vector2 = Vector2(0, -1).rotated(turn)
			var side: Vector2 = Vector2(1, 0).rotated(turn)
			c.draw_line(at + up * 4.0 - side * 5.0, at + up * 4.0 + side * 5.0, Color(NAVY, a3), 2)
			c.draw_line(at - side * 2.0 - up * 0.5, at + side * 2.0 - up * 0.5, Color(CREAM, a3), 1)
			c.draw_line(at + up * 1.5, at - up * 2.5, Color(CREAM, a3), 1)
			c.draw_polyline(q2 + PackedVector2Array([q2[0]]), Color(CREAM, 0.7 * a3), 1)
			return true
	return false
