extends RefCounted
## KYLE / the founder of a startup on Pearl Street. He glides in on an electric
## scooter through kombucha steam while his pitch deck projects behind him:
## "We're like a family here." An optional mini-boss between chapters. Three
## attacks (slides of the deck), one per turn, cycling. Phase 1 is denser; phase 2
## is denser still and adds one layer.
##  pivot       big arrows warn one way, flip, and dash the opposite way along a lane.
##              (phase 2: vertical pivot arrows cross the lanes)
##  burn_rate   the area under a climbing chart burns; the chart pivots about a hinge
##              and the gap above it swings. (phase 2: a line hangs from the ceiling)
##  quick_sync  invites drop down marked lanes and stack; "Quick sync?" pings send an
##              expanding ring with one gap. (phase 2: overbooked rows, one free slot)
## The promise ("Ask what the product does", peaceful): three question marks glow on
## the slides one after another, away from the current danger (hot lanes skip the
## marker, the chart carries it, invites keep off its lane). Confirm on each.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["pivot", "burn_rate", "quick_sync"]
const PHASES: Array[int] = [0, 1, 2]
const QUESTIONS: int = 3
const LANES: Array[float] = [-36.0, 0.0, 36.0]
const WARN: int = 52           # pivot: warning before the dash...
const FAKE: int = 32           # ...of which the arrow points the wrong way
const MORPH: int = 56          # burn rate: a pivot is forecast, then morphs, this long
const COLS: int = 30           # burn rate: 8 px columns across the box
const SLOTS: int = 7           # quick sync: 7 calendar lanes, 32 px apart
const SLOT0: float = -96.0
const SLOT_W: float = 32.0
const TIMES: Array[String] = ["9:00", "9:30", "1:00", "1:30", "2:00", "2:30", "3:00", "4:00"]

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const ROSE: Color = Color("e8837b")
const MINT: Color = Color("b9d5bc")
const BLUE: Color = Color("5b8fd6")
const TEAL: Color = Color("5fb8a8")
const LILAC: Color = Color("a68db8")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	var phase: int = clampi(int(s.phase), 0, 2)
	s.patternId = id
	s.length = 460 + 40 * phase
	s.spots = []
	s.laneFree = [0, 0, 0]
	s.queue = []
	s.n = 0
	s.pivots = []
	s.knots = []
	match id:
		"pivot":
			s.phaseName = "The Pivot"
			s.hint = "Arrows warn one way, then dash the other. Leave the hot lane. Glowing ?: stand, confirm."
			s.spots = [Vector2(0.55, -0.67), Vector2(-0.5, 0.67), Vector2(0.45, 0.0)]
		"burn_rate":
			s.phaseName = "Burn Rate"
			s.hint = "The area under the chart burns. Ride the gap as it pivots. Glowing ?: stand, confirm."
			s.spots = [Vector2(-0.25, 0.0), Vector2(0.2, 0.0), Vector2(0.0, 0.0)]
			var ticks: Array = [[170, 330], [130, 260, 390], [100, 215, 330, 440]][phase]
			for i: int in range(ticks.size()):
				s.pivots.append([ticks[i], 1.0 if i % 2 == 0 else -1.0, (1.0 if i % 2 == 0 else -1.0) * D.rand_range(s, 20.0, 50.0)])
			for i: int in range(COLS): s.knots.append(D.rand_range(s, -3.0 - 2.0 * phase, 3.0 + 2.0 * phase))
		"quick_sync":
			s.phaseName = "Quick Sync"
			s.hint = "Invites drop on marked lanes and stack. Quick sync? rings have a gap. Glowing ?: confirm."
			s.spots = [Vector2(-0.55, -0.45), Vector2(0.5, -0.55), Vector2(0.05, -0.4)]
	for i: int in range(QUESTIONS):
		D.objective(s, {"kind": "confirm", "r": 13.0, "label": "ask", "active": false, "x": 0.0, "y": 0.0})

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return _asked(s) >= QUESTIONS

static func progress(s: Dictionary) -> String:
	return "Questions asked %d/%d" % [_asked(s), QUESTIONS]

static func _asked(s: Dictionary) -> int:
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	return count

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 2)
	match str(s.patternId):
		"pivot": _pivot(s, t, phase)
		"burn_rate": _burn(s, t, phase)
		"quick_sync": _sync(s, t, phase)
	_questions(s, t)

static func after(s: Dictionary, _t: int) -> void:
	if str(s.patternId) == "quick_sync": _stack(s)

## One question mark at a time: the next glows 24 ticks after the last was asked.
## On the burn rate slide the mark rides the chart, midway up the gap above it.
static func _questions(s: Dictionary, t: int) -> void:
	var h: Vector2 = D.half(s)
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		var spot: Vector2 = Vector2(s.spots[i]) * h
		if str(s.patternId) == "burn_rate":
			spot.y = minf(maxf((_line(s, spot.x, t) - h.y + 8.0) * 0.5, -h.y + 14.0), _line(s, spot.x, t) - 16.0)
		o.x = spot.x; o.y = spot.y
		var ready: bool = t >= 40 if i == 0 else last_done >= 0 and int(s.clock) - last_done >= 24
		o.active = ready
		if ready and not bool(o.get("shown", false)):
			o.shown = true
			D.effect(s, "pulse", D.to_world(s, spot), 18)
		return

static func _active(s: Dictionary) -> Dictionary:
	for o: Dictionary in s.objectives:
		if o.active and not o.done: return o
	return {}

# ---------------------------------------------------------------- 1. The Pivot

## An arrow is planned on a lane: for 32 ticks its ghost creeps in pointing one way,
## then it flips for 20 more (all inside a red lane band), then it dashes the other
## way. At most two lanes are hot at once, never the marker's while promised.
## Phase 1: some events send a second arrow the other way, 14 ticks later. Phase 2:
## every event does, and every third adds a vertical pivot arrow.
static func _pivot(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 108.0}, 30)
	var speed: float = 3.8 + 0.2 * phase
	var win: int = int((2.0 * h.x + 60.0) / speed)
	var every: int = int([78, 66, 58][phase])
	if t >= 20 and t < int(s.length) - 190 and (t - 20) % every == 0:
		var n: int = int(s.n)
		s.n = n + 1
		var used: Array = []
		for r: int in range(2 if (phase == 1 and n % 2 == 1) or phase >= 2 else 1):
			var lane: int = _lane(s, t + r * 14 + WARN, used, n + r)
			if lane < 0: continue
			used.append(lane)
			s.laneFree[lane] = t + r * 14 + WARN + win + 4
			s.queue.append({"at": t + r * 14, "horizontal": true, "pos": LANES[lane], "d": -1.0 if (n + r) % 2 == 0 else 1.0})
		if phase >= 2 and n % 3 == 1:
			var o: Dictionary = _active(s)
			var cols: Array = [-84.0, -42.0, 0.0, 42.0, 84.0]
			cols.sort_custom(func(a: float, b: float) -> bool: return absf(a - float(s.soul.x)) < absf(b - float(s.soul.x)))
			for x: float in cols:
				if o.is_empty() or not bool(s.promised) or absf(float(o.x) - x) > 40.0:
					s.queue.append({"at": t + 24, "horizontal": false, "pos": x, "d": -1.0 if n % 2 == 0 else 1.0})
					break
	var kept: Array = []
	for q: Dictionary in s.queue:
		if int(q.at) > t:
			kept.append(q)
			continue
		var horizontal: bool = bool(q.horizontal)
		var d: float = float(q.d)
		var pos: float = float(q.pos)
		var band: Dictionary = {"kind": "lane", "y": D.centre(s).y + pos, "h": 18.0, "horizontal": true} if horizontal else {"kind": "lane", "x": D.centre(s).x + pos, "w": 14.0, "horizontal": false}
		D.warn(s, band, WARN)
		D.warn(s, {"kind": "pivot", "space": "box", "pos": pos, "dir": d, "horizontal": horizontal}, WARN, true)
		var start: float = -d * ((h.x if horizontal else h.y) + 22.0)
		D.shot(s, {"space": "box", "x": start if horizontal else pos, "y": pos if horizontal else start, "vx": d * speed if horizontal else 0.0, "vy": 0.0 if horizontal else d * speed,
			"collide": "rect", "w": 16.0 if horizontal else 9.0, "h": 9.0 if horizontal else 16.0, "shape": "arrow", "hold": true, "arm": WARN, "life": WARN + win + 20})
	s.queue = kept

## A lane that is free when its dash would start, not the marker's, and only while
## fewer than two lanes are busy. Every other event aims at the lane you are in.
static func _lane(s: Dictionary, start: int, used: Array, n: int) -> int:
	var o: Dictionary = _active(s)
	var skip: int = clampi(roundi(float(o.y) / 36.0) + 1, 0, 2) if bool(s.promised) and not o.is_empty() else -1
	var mine: int = clampi(roundi(float(s.soul.y) / 36.0) + 1, 0, 2)
	var busy: int = 0
	var open: Array = []
	for i: int in range(3):
		if int(s.laneFree[i]) > start: busy += 1
		elif i != skip and not used.has(i): open.append(i)
	if busy >= 2 or open.is_empty(): return -1
	if n % 2 == 0 and open.has(mine): return mine
	return int(open[int(D.rand(s) * open.size()) % open.size()])

# ---------------------------------------------------------------- 2. Burn Rate

## line(x) = a baseline that climbs over the fight + slope k times the distance from a
## hinge + jitter. Columns under it burn (after a 44 tick draw-in). A dotted forecast
## shows each pivot 56 ticks ahead; then k flips and the hinge moves over 56 ticks, so
## the gap above the line swings sideways. Phase 2 hangs a second line 46 px above.
static func _burn(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 112.0}, 30)
		for i: int in range(COLS):
			for hi: int in range(1 + (1 if phase >= 2 else 0)):
				D.shot(s, {"space": "box", "x": -116.0 + 8.0 * i, "y": h.y, "collide": "rect", "w": 4.6, "h": 8.0, "shape": "column", "high": hi == 1, "hold": true, "arm": 44, "life": int(s.length) + 60})
	for p: Array in s.pivots:
		if t == int(p[0]) - MORPH:
			D.banner(s, "PIVOT!", MORPH)
			D.warn(s, {"kind": "none"}, MORPH, true)
	for b: Dictionary in s.bullets:
		if str(b.shape) != "column": continue
		var edge: float = _line(s, float(b.x), t)
		if bool(b.high):
			edge -= 46.0
			b.y = (edge - h.y - 6.0) * 0.5 if edge > -h.y else -h.y - 40.0
			b.h = maxf(0.5, (edge + h.y + 6.0) * 0.5) if edge > -h.y else 0.5
		else:
			b.y = (minf(edge, h.y + 4.0) + h.y + 6.0) * 0.5
			b.h = maxf(0.5, (h.y + 6.0 - minf(edge, h.y + 4.0)) * 0.5)

## (slope, hinge x) at tick t: each pivot blends the pair toward its target.
static func _shape(s: Dictionary, t: float) -> Vector2:
	var k: float = -1.0
	var hinge: float = 0.0
	for p: Array in s.pivots:
		if t < float(p[0]): break
		var u: float = clampf((t - float(p[0])) / MORPH, 0.0, 1.0)
		k = lerpf(k, float(p[1]), u * u * (3.0 - 2.0 * u))
		hinge = lerpf(hinge, float(p[2]), u * u * (3.0 - 2.0 * u))
	return Vector2(k, hinge)

static func _line(s: Dictionary, x: float, t: float) -> float:
	var sh: Vector2 = _shape(s, t)
	var base: float = lerpf(24.0, -8.0, clampf(t / float(int(s.length) - 150), 0.0, 1.0))
	var amp: float = [18.0, 20.0, 22.0][clampi(int(s.phase), 0, 2)]
	var y: float = base + sh.x * amp * (x - sh.y) / 120.0 + float(s.knots[clampi(int((x + 120.0) / 8.0), 0, COLS - 1)])
	return maxf(y, -D.half(s).y + 24.0)

# ---------------------------------------------------------------- 3. Quick Sync

## An invite drops down a lane (red band and invite icon for 36 ticks), lands on the
## floor or the stack and stays, dim and harmless, for 150 ticks. Every other drop
## aims at your lane; lanes hold two. "Quick sync?" pings open far from you and send a
## ring whose one gap sits 0.75 to 1.1 rad off your bearing (toward the marker while promised). Phase 2: every 140 ticks
## an overbooked row drops, every lane but yours.
static func _sync(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 116.0}, 30)
	var stop: int = int(s.length) - 170
	var every: int = int([40, 32, 28][phase])
	if t >= 20 and t < stop and (t - 20) % every == 0:
		var slot: int = _slot(s, int(s.n) % 2 == 0)
		s.n = int(s.n) + 1
		if slot >= 0: _block(s, h, slot, phase, true)
	if phase >= 2 and t >= 90 and t < stop and (t - 90) % 140 == 0:
		var free: int = _slot_of(float(s.soul.x))
		D.warn(s, {"kind": "free", "space": "box", "x": SLOT0 + SLOT_W * free}, 36)
		for i: int in range(SLOTS):
			if i != free and _count(s, i) < 2: _block(s, h, i, phase, false)
	if t >= 50 and t < stop + 40 and (t - 50) % int([120, 96, 84][phase]) == 0:
		var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
		var far: Array = []
		for o: Vector2 in [Vector2(-96, -44), Vector2(96, -44), Vector2(-96, 44), Vector2(96, 44), Vector2(0, -48)]:
			if o.distance_to(soul) >= 70.0: far.append(o)
		if not far.is_empty():
			var at: Vector2 = far[int(D.rand(s) * far.size()) % far.size()]
			var off: float = D.rand_range(s, 0.75, 1.1) * (1.0 if D.rand(s) < 0.5 else -1.0)
			var o2: Dictionary = _active(s)
			if bool(s.promised) and not o2.is_empty():
				# While promised the gap sits on the marker's side of you.
				off = absf(off) * (1.0 if wrapf((Vector2(float(o2.x), float(o2.y)) - at).angle() - (soul - at).angle(), -PI, PI) >= 0.0 else -1.0)
			var aim: float = (soul - at).angle() + off
			D.warn(s, {"kind": "ping", "space": "box", "x": at.x, "y": at.y}, 36, true)
			D.shot(s, {"space": "box", "x": at.x, "y": at.y, "collide": "ring", "radius": 4.0, "grow": 1.2, "thick": 2.2, "gap": aim, "gapWidth": 1.1, "maxRadius": 300.0, "shape": "ping", "arm": 36})

static func _slot_of(x: float) -> int:
	return clampi(roundi((x - SLOT0) / SLOT_W), 0, SLOTS - 1)

static func _count(s: Dictionary, slot: int) -> int:
	var count: int = 0
	for b: Dictionary in s.bullets:
		if str(b.shape) == "invite" and int(b.slot) == slot: count += 1
	return count

## A lane with room, away from the marker while promised; aimed = nearest to you.
static func _slot(s: Dictionary, aimed: bool) -> int:
	var o: Dictionary = _active(s)
	var skip: int = _slot_of(float(o.x)) if bool(s.promised) and not o.is_empty() else -9
	var open: Array = []
	for i: int in range(SLOTS):
		if _count(s, i) < 2 and absi(i - skip) > 1: open.append(i)
	if open.is_empty(): return -1
	var best: int = int(open[0])
	for i: int in open:
		if absf(SLOT0 + SLOT_W * i - float(s.soul.x)) < absf(SLOT0 + SLOT_W * best - float(s.soul.x)): best = i
	return best if aimed else int(open[int(D.rand(s) * open.size()) % open.size()])

static func _block(s: Dictionary, h: Vector2, slot: int, phase: int, icon: bool) -> void:
	var x: float = SLOT0 + SLOT_W * slot
	var label: String = TIMES[(int(s.n) * 3 + slot) % TIMES.size()]
	D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 16.0, "horizontal": false}, 36, icon)
	if icon: D.warn(s, {"kind": "invite", "space": "box", "x": x, "label": label}, 36)
	D.shot(s, {"space": "box", "x": x, "y": -h.y - 14.0, "vy": 2.2 + 0.1 * phase, "collide": "rect", "w": 15.0, "h": 9.0, "shape": "invite", "slot": slot, "label": label, "hue": slot % 4, "hold": true, "arm": 36, "life": 36 + 140})

## Falling invites stop on the stack; landed ones go dim and harmless, and settle
## down when the invite under them expires.
static func _stack(s: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	var landed: Array = []
	for i: int in range(SLOTS): landed.append([])
	for b: Dictionary in s.bullets:
		if str(b.shape) == "invite" and bool(b.get("landed", false)): landed[int(b.slot)].append(b)
	for slot: int in range(SLOTS):
		landed[slot].sort_custom(func(a: Dictionary, c: Dictionary) -> bool: return int(a.landAt) < int(c.landAt))
		for k: int in range(landed[slot].size()):
			landed[slot][k].y = move_toward(float(landed[slot][k].y), h.y - 9.0 - 18.0 * k, 3.0)
	for b: Dictionary in s.bullets:
		if str(b.shape) != "invite" or bool(b.get("landed", false)): continue
		var top: float = h.y - 18.0 * landed[int(b.slot)].size()
		if float(b.y) + 9.0 >= top and int(b.age) > int(b.arm):
			b.y = top - 9.0; b.vy = 0.0
			b.landed = true; b.landAt = int(s.clock); b.friendly = true; b.life = int(b.age) + 150
			D.effect(s, "block", D.to_world(s, Vector2(float(b.x), float(b.y))), 12)

# ---------------------------------------------------------------- drawing

static func _qmark(c: CanvasItem, at: Vector2, col: Color) -> void:
	c.draw_arc(at + Vector2(0, -4), 4.2, PI, TAU + 0.45 * PI, 12, col, 2)
	c.draw_line(at + Vector2(0.6, 0), at + Vector2(0, 2.5), col, 2)
	c.draw_circle(at + Vector2(0, 6), 1.3, col)

## A big arrow of 16 px half length pointing along dir (outline included).
static func _arrow(c: CanvasItem, at: Vector2, dir: Vector2, fill: Color, line: Color, width: float) -> void:
	var side: Vector2 = Vector2(-dir.y, dir.x)
	var pts: PackedVector2Array = [at - dir * 16.0 + side * 4.0, at + dir * 5.0 + side * 4.0, at + dir * 5.0 + side * 9.0, at + dir * 16.0, at + dir * 5.0 - side * 9.0, at + dir * 5.0 - side * 4.0, at - dir * 16.0 - side * 4.0]
	c.draw_colored_polygon(pts, fill)
	pts.append(pts[0])
	c.draw_polyline(pts, line, width)

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var clock: int = int(s.clock)
	var caption: String = {"pivot": "SLIDE 4: PIVOT", "burn_rate": "SLIDE 7: RUNWAY", "quick_sync": "SLIDE 9: SYNERGY"}[str(s.patternId)]
	v.text(c, v.box_point(Vector2(-h.x + 84.0, h.y - 6.0)), caption, Color(CREAM, 0.16), 150)
	match str(s.patternId):
		"pivot":
			for y: float in [-18.0, 18.0]:
				c.draw_line(v.box_point(Vector2(-h.x, y)), v.box_point(Vector2(h.x, y)), Color(CREAM, 0.07), 1)
			for w: Dictionary in s.warnings:
				if str(w.kind) != "pivot": continue
				# The ghost points the wrong way and creeps in, then flips at the real edge.
				var fake: bool = int(w.age) < FAKE
				var d: float = float(w.dir)
				var ext: float = (h.x if bool(w.horizontal) else h.y) - 22.0
				var along: float = (d * (ext - 0.7 * int(w.age))) if fake else (-d * ext)
				var at: Vector2 = v.box_point(Vector2(along, float(w.pos)) if bool(w.horizontal) else Vector2(float(w.pos), along))
				var dir: Vector2 = Vector2(-d if fake else d, 0.0) if bool(w.horizontal) else Vector2(0.0, -d if fake else d)
				var col: Color = Color(ROSE, 0.55 + 0.4 * sin(float(w.age) * (0.3 if fake else 0.9)))
				_arrow(c, at, dir, Color(col, 0.18), col, 2)
				if not fake: v.text(c, at + Vector2(0, -12), "PIVOT!", ROSE, 50)
		"burn_rate":
			var t: float = float(clock - int(s.leadIn))
			for p: Array in s.pivots:
				if t >= float(p[0]) - MORPH and t < float(p[0]):
					for x: int in range(-120, 121, 8):
						c.draw_circle(v.box_point(Vector2(x, _line(s, x, float(p[0]) + MORPH))), 1.4, Color(ROSE, 0.8))
			var pts: PackedVector2Array = []
			for x2: int in range(-116, 117, 8): pts.append(v.box_point(Vector2(x2, minf(_line(s, x2, t), h.y))))
			c.draw_polyline(pts, Color(AMBER, 0.9), 2)
		"quick_sync":
			for i: int in range(SLOTS + 1):
				c.draw_line(v.box_point(Vector2(SLOT0 - 16.0 + SLOT_W * i, -h.y)), v.box_point(Vector2(SLOT0 - 16.0 + SLOT_W * i, h.y)), Color(CREAM, 0.06), 1)
			for w2: Dictionary in s.warnings:
				var p2: Vector2 = v.box_point(Vector2(float(w2.get("x", 0.0)), float(w2.get("y", -h.y + 12.0))))
				match str(w2.kind):
					"invite":
						c.draw_rect(Rect2(p2 + Vector2(-15, 0), Vector2(30, 18)), Color(ROSE, 0.5), false, 1)
						v.text(c, p2 + Vector2(0, 12), str(w2.label), Color(ROSE, 0.9), 36)
					"free":
						c.draw_rect(Rect2(v.box_point(Vector2(float(w2.x) - 16.0, -h.y + 2.0)), Vector2(32, h.y * 2.0 - 4.0)), Color(MINT, 0.5), false, 1)
					"ping":
						# The bubble opens toward the middle of the box so it is never clipped.
						var down: float = 1.0 if float(w2.y) < 0.0 else -1.0
						var shift: float = -signf(float(w2.x)) * 34.0
						c.draw_rect(Rect2(p2 + Vector2(shift - 46.0, 8.0 if down > 0.0 else -22.0), Vector2(92, 14)), Color(TEAL, 0.9))
						c.draw_colored_polygon(PackedVector2Array([p2 + Vector2(-4, 8.0 * down), p2 + Vector2(4, 8.0 * down), p2]), Color(TEAL, 0.9))
						v.text(c, p2 + Vector2(shift, 19.0 if down > 0.0 else -11.0), "Quick sync?", INK, 96)
						c.draw_arc(p2, 4.0 + float(w2.age) * 0.3, 0, TAU, 14, Color(TEAL, 0.6), 1)
	var pulse: float = 0.5 + 0.5 * sin(float(clock) * 0.2)
	for o: Dictionary in s.objectives:
		if bool(s.promised) and o.active and not o.done:
			var at2: Vector2 = v.box_point(Vector2(float(o.x), float(o.y)))
			c.draw_circle(at2, 16.0 + pulse * 2.0, Color(TEAL, 0.12 + 0.10 * pulse))
			_qmark(c, at2, Color(CREAM, 0.9))

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	var armed: bool = int(b.age) <= int(b.arm)
	match str(b.shape):
		"arrow":
			_arrow(c, at, Vector2(signf(float(b.vx)), signf(float(b.vy))), Color(AMBER, 0.95 * alpha), Color(CREAM, alpha), 1)
			return true
		"column":
			c.draw_colored_polygon(v.quad(at, float(b.w), float(b.h), turn), Color(ROSE, (0.12 if armed else 0.5) * alpha))
			var lip: Vector2 = Vector2(0, float(b.h) if bool(b.high) else -float(b.h)).rotated(turn)
			c.draw_line(at + lip - Vector2(float(b.w), 0).rotated(turn), at + lip + Vector2(float(b.w), 0).rotated(turn), Color(AMBER, (0.35 if armed else 1.0) * alpha), 2)
			return true
		"invite":
			c.draw_colored_polygon(v.quad(at, float(b.w), float(b.h), turn), Color([BLUE, TEAL, LILAC, AMBER][int(b.hue)], 0.92 * alpha))
			c.draw_line(at + Vector2(-15, -9).rotated(turn), at + Vector2(15, -9).rotated(turn), Color(CREAM, alpha), 2)
			v.text(c, at + Vector2(0, 5), str(b.label), Color(INK, alpha), 36)
			return true
		"ping":
			var gw: float = float(b.gapWidth) * 0.5
			c.draw_arc(at, float(b.radius), float(b.gap) + gw, float(b.gap) + TAU - gw, maxi(24, int(float(b.radius) * 0.6)), Color(TEAL, (0.35 if armed else 1.0) * alpha), 3.0)
			return true
	return false
