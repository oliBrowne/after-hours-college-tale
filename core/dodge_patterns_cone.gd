extends RefCounted
## CAPTAIN LANCE'S PELOTON (internal id "cone"): the Boulder cycling club's paceline. Three riders
## call three passes at once (ON YOUR LEFT! ON YOUR RIGHT! BOTH SIDES!) because nobody wants to cancel
## their own call, and Lance only wants nobody hit on the path. Five handmade attacks, one per turn,
## cycling in order. Every attack keeps the same promise: three marked routes per turn. A route
## row is announced (mint), then its marked spot opens for 60 ticks; touching
## it while promised keeps that route. A crossed-out call (plum, struck through, CALL CANCELLED)
## is cancelled: never follow it, and in On Your Left and Velodrome a call that
## would cover the marked route is always cancelled. Riders are drawn from above, heading where
## they travel; the old cones are gone.
## Phase 1 (from the second turn) adds a layer to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["calls", "echelon", "tape", "gravel", "velodrome"]
const PHASES: Array[int] = [0, 1]
const LENGTH: int = 480
const ROUTES: Array[int] = [100, 230, 360]
const WINDOW: int = 60
const SHOW: int = 50
const RW: float = 26.0
const RH: float = 11.0
const LANES: Array[float] = [22.0, 37.0, 52.0]
const LANE_SPEED: Array[float] = [0.022, -0.016, 0.012]

const PINK: Color = Color("e8509c")
const LIME: Color = Color("b6e63c")
const CYAN: Color = Color("3ad0e8")
const SUN: Color = Color("f2d23a")
## Rider kits: [jersey, helmet].
const KITS: Array = [[Color("e8509c"), Color("b6e63c")], [Color("b6e63c"), Color("e8509c")], [Color("3ad0e8"), Color("e8509c")], [Color("f2d23a"), Color("3ad0e8")]]
const CREAM: Color = Color("e6d6b1")
const MINT: Color = Color("b9d5bc")
const PLUM: Color = Color("6b526a")
const ROSE: Color = Color("e8837b")
const INK: Color = Color("0d101c")
const TAPE: Color = Color("e8c84a")
const GRAVEL: Color = Color("b49a80")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = LENGTH
	s.routesKept = 0
	s.route = {}
	s.lastRow = -1
	s.calls = []
	s.slide = Vector2.ZERO
	s.tilt = Vector2.ZERO
	s.lastSoul = Vector2.ZERO
	s.flow = 1.0
	s.funnelGap = 3
	s.bannerColor = MINT
	# The three route rows are decided up front so the traffic can make room.
	var rows: Array = []
	for k: int in range(ROUTES.size()):
		var row: int = int(D.rand(s) * 3.0)
		if k > 0 and row == int(rows[k - 1]): row = (row + 1 + int(D.rand(s) * 2.0)) % 3
		rows.append(row)
	s.routeRows = rows
	s.routeX = [D.rand_range(s, -1.0, 1.0), D.rand_range(s, -1.0, 1.0), D.rand_range(s, -1.0, 1.0)]
	match id:
		"calls":
			s.phaseName = "On Your Left"
			s.hint = "Riders call a side, then sweep down it. Cancelled calls stay put. Touch each marked route."
		"echelon":
			s.phaseName = "Echelon"
			s.hint = "Riders cross in a V that points at its gap. Slip through. Touch each marked route."
		"tape":
			s.phaseName = "Tape Off"
			s.hint = "Course tape closes in from the edges. Pass through each tape's gap."
		"gravel":
			s.phaseName = "Loose Gravel"
			s.hint = "The road is loose gravel; the marked route is swept clear. Dodge the signs and brooms."
		"velodrome":
			s.phaseName = "Velodrome"
			s.hint = "Ride the gaps in the traffic to the marked exit. REVERSE flips a lane; cancelled calls don't."

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return int(s.routesKept) >= 3

static func preview(_s: Dictionary, _phase: int) -> void:
	pass

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = int(s.phase)
	_routes(s, t)
	match str(s.patternId):
		"calls": _calls(s, t, phase)
		"echelon": _echelon(s, t, phase)
		"tape": _tape(s, t, phase)
		"gravel": _gravel(s, t, phase)
		"velodrome": _velodrome(s, t, phase)

static func after(s: Dictionary, _t: int) -> void:
	var route: Dictionary = s.route
	if not route.is_empty() and not route.counted:
		var o: Dictionary = s.objectives[int(route.obj)]
		if o.done:
			route.counted = true
			s.routesKept = int(s.routesKept) + 1
			s.objectiveChanged = true
			s.botGoal = null
	s.lastSoul = Vector2(float(s.soul.x), float(s.soul.y))

# ---------------------------------------------------------------- routes

static func _routes(s: Dictionary, t: int) -> void:
	for k: int in range(ROUTES.size()):
		var open: int = ROUTES[k]
		if t == open - SHOW:
			var ring: bool = s.patternId == "velodrome"
			var spot: Vector2
			var decoy: Vector2
			var lane: int = -1
			var decoy_lane: int = -1
			if ring:
				# Velodrome routes are its exits, where the outer lane meets the wall.
				var exits: Array[Vector2] = [Vector2(0, -46), Vector2(46, 0), Vector2(0, 46), Vector2(-46, 0)]
				var e: int = _exit_index(s, k)
				spot = exits[e]
				lane = 2
				decoy_lane = 2
				decoy = exits[(e + 1 + int(D.rand(s) * 3.0)) % 4]
				D.objective(s, {"kind": "touch", "x": spot.x, "y": spot.y, "r": 12.0, "active": false, "label": "EXIT"})
			else:
				var h: Vector2 = D.half(s)
				var rows: Array[float] = [-h.y + 18.0, 0.0, h.y - 18.0]
				var row: int = int(s.routeRows[k])
				var other: int = (row + 1 + int(D.rand(s) * 2.0)) % 3
				spot = _plan_spot(s, k)
				decoy = Vector2(D.rand_range(s, -h.x + 44.0, h.x - 44.0), rows[other])
			if not ring: D.objective(s, {"kind": "touch", "x": spot.x, "y": spot.y, "w": RW, "h": RH, "active": false, "label": "ROUTE"})
			s.route = {"k": k, "x": spot.x, "y": spot.y, "dx": decoy.x, "dy": decoy.y, "lane": lane, "decoyLane": decoy_lane, "obj": s.objectives.size() - 1,
				"counted": false, "from": open - SHOW, "open": open, "close": open + WINDOW, "ring": ring}
			D.warn(s, {"kind": "none"}, 1, true)
		if not s.route.is_empty() and int(s.route.k) == k:
			var o: Dictionary = s.objectives[int(s.route.obj)]
			if t == open: o.active = true
			if t == open + WINDOW: o.active = false
	var r: Dictionary = s.route
	var next: int = _next_route(t, 110)
	if not r.is_empty() and not r.counted and t >= int(r.from) and t < int(r.close):
		s.botGoal = _lead(s, Vector2(float(r.x), float(r.y)))
	elif next >= 0 and t < ROUTES[next] - SHOW:
		# QA autopilot only: head for the coming route a little early.
		s.botGoal = _lead(s, _plan_spot(s, next))
	else:
		s.botGoal = null

## Velodrome exits: each marked exit is next to the previous one.
static func _exit_index(s: Dictionary, k: int) -> int:
	var e: int = int(s.routeRows[0])
	for i: int in range(1, k + 1):
		e = (e + (1 if int(s.routeRows[i]) % 2 == 0 else 3)) % 4
	return e

## Where route k will be marked (rows and x are decided in setup).
static func _plan_spot(s: Dictionary, k: int) -> Vector2:
	if s.patternId == "velodrome":
		var exits: Array[Vector2] = [Vector2(0, -46), Vector2(46, 0), Vector2(0, 46), Vector2(-46, 0)]
		return exits[_exit_index(s, k)]
	var h: Vector2 = D.half(s)
	var rows: Array[float] = [-h.y + 18.0, 0.0, h.y - 18.0]
	var x: float = float(s.routeX[k]) * (h.x - 44.0)
	if s.patternId == "echelon":
		# The marked route is downstream: the traffic carries you toward it.
		var downstream: float = -1.0 if ROUTES[k] < 190 else 1.0
		x = downstream * lerpf(16.0, h.x - 44.0, absf(float(s.routeX[k])))
	return Vector2(x, rows[int(s.routeRows[k])])

## The autopilot plans whole 18-tick runs and stops ~17 px short of its goal,
## so aim it a little past the spot along the way in.
static func _lead(s: Dictionary, target: Vector2) -> Vector2:
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var d: Vector2 = target - soul
	return target + d.normalized() * 15.0 if d.length() > 2.0 else target

## The route whose window opens within lead ticks (or is open now), or -1.
static func _next_route(t: int, lead: int, s: Dictionary = {}) -> int:
	for k: int in range(ROUTES.size()):
		if not s.is_empty() and not s.route.is_empty() and int(s.route.k) == k and s.route.counted: continue
		if t >= ROUTES[k] - lead and t < ROUTES[k] + WINDOW: return k
	return -1

## True while the marked route is shown or open (with a little margin).
static func _route_live(s: Dictionary, from: int, to: int) -> bool:
	var r: Dictionary = s.route
	if r.is_empty() or r.counted: return false
	return to >= int(r.from) and from < int(r.close)

# ---------------------------------------------------------------- calls

const REGIONS: Dictionary = {"LEFT": [[-120.0, -40.0]], "MIDDLE": [[-40.0, 40.0]], "RIGHT": [[40.0, 120.0]], "BOTH SIDES": [[-120.0, -40.0], [40.0, 120.0]]}

## On Your Left: the peloton shouts a side, its band lights up, and a wall of
## riders sweeps down it. Loose wheels roll across the floor in between. Phase 1: the
## captain changes the call (it is struck out, CALL CANCELLED, and replaced) and the
## loose wheels bounce.
static func _calls(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 240.0, "h": 112.0}, 24)
	if t >= 20 and t <= 372 and (t - 20) % 64 == 0:
		_new_call(s, t, phase, "")
	for call: Dictionary in s.calls:
		if phase > 0 and int(call.swap) == t and not call.crossed:
			# The captain changes the call: strike it, call where you are.
			call.crossed = true
			call.crossAt = t
			_new_call(s, t, phase, str(call.text), 34, true)
		if int(call.fire) == t and not call.crossed:
			_drop(s, call)
	var every: int = 34 if phase > 0 else 42
	if t % every == 12 and t > 30 and t < 410:
		_roll(s, phase > 0 and int(t / every) % 2 == 0, phase > 0)

static func _new_call(s: Dictionary, t: int, phase: int, not_region: String, lead: int = 40, aimed: bool = false) -> void:
	var names: Array = REGIONS.keys()
	var text: String
	var soul_x: float = float(s.soul.x)
	if aimed or D.rand(s) < 0.55:
		text = "LEFT" if soul_x < -40.0 else "RIGHT" if soul_x > 40.0 else "MIDDLE"
		if text == not_region: text = "BOTH SIDES" if text == "MIDDLE" else "MIDDLE"
	else:
		text = names[int(D.rand(s) * names.size())]
		if text == not_region: text = names[(names.find(text) + 1 + int(D.rand(s) * 3.0)) % names.size()]
	var fire: int = t + lead
	var crossed: bool = D.rand(s) < 0.15
	if _route_live(s, fire - 10, fire + 40):
		for span: Array in REGIONS[text]:
			if float(s.route.x) + RW > float(span[0]) and float(s.route.x) - RW < float(span[1]): crossed = true
	var swap: int = t + 14 if phase > 0 and not_region.is_empty() and not crossed and D.rand(s) < 0.4 else -1
	s.calls.append({"at": t, "fire": fire, "text": text, "crossed": crossed, "swap": swap, "crossAt": t if crossed else -1})
	D.warn(s, {"kind": "none"}, 1, true)

static func _drop(s: Dictionary, call: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	for span: Array in REGIONS[str(call.text)]:
		var x: float = float(span[0]) + 7.0
		while x <= float(span[1]) - 6.0:
			for row: int in range(2):
				D.shot(s, {"space": "box", "x": x + (row * 6.5), "y": -h.y - 8.0 - row * 22.0, "vy": 4.2, "collide": "rect", "w": 4.0, "h": 5.0, "shape": "rider", "life": 70})
			x += 13.0
	D.effect(s, "pulse", D.to_world(s, Vector2((float(REGIONS[str(call.text)][0][0]) + float(REGIONS[str(call.text)][0][1])) * 0.5, -h.y)), 14)

static func _roll(s: Dictionary, bounce: bool, aim: bool = false) -> void:
	var h: Vector2 = D.half(s)
	var side: float = -1.0 if D.rand(s) < 0.5 else 1.0
	var speed: float = 2.1
	var y: float = D.rand_range(s, -h.y + 10.0, h.y - 10.0)
	if D.rand(s) < (0.85 if aim else 0.5): y = clampf(float(s.soul.y) + D.rand_range(s, -10.0, 10.0), -h.y + 8.0, h.y - 8.0)
	if bounce: y = h.y - 6.0
	D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 4.0), "y": y, "dir": Vector2(-side, 0)}, 30)
	var b: Dictionary = {"space": "box", "x": side * (h.x + 10.0 + speed * 30.0), "y": y, "vx": -side * speed, "r": 5.0, "shape": "wheel", "spin": -side * 0.16, "life": 260}
	if bounce: b.merge({"vy": -D.rand_range(s, 2.2, 3.4), "ay": 0.13, "bounce": 0.92, "y": y - 20.0}, true)
	D.shot(s, b)

# ---------------------------------------------------------------- echelon

## Echelon: riders in a V (a chevron pointing at its gap) cross the box. The
## gap snakes. Halfway the captain sends the peloton the other way (U-TURN).
## Phase 1: the support crew lobs water bottles at you from the top corners.
static func _echelon(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 236.0, "h": 112.0}, 24)
	if t == 150:
		D.warn(s, {"kind": "arrows", "dir": Vector2.RIGHT}, 50, true)
		D.banner(s, "U-TURN!", 50)
	if t == 190:
		# The captain clears the old line before the peloton comes the other way.
		s.flow = -1.0
		for b: Dictionary in s.bullets:
			if b.get("funnel", false): b.fade = 20
	var every: int = 34 if phase > 0 else 40
	if t % every == 0 and t >= 16 and t < 410 and not (t > 150 and t < 192):
		var h: Vector2 = D.half(s)
		var slots: int = 8
		var spacing: float = (h.y * 2.0 - 10.0) / float(slots - 1)
		var step: int = -1 if D.rand(s) < 0.5 else 1
		var next: int = _next_route(t, 170, s)
		if next >= 0:
			# Steer the funnels' gaps onto the coming route row.
			var ry: float = _plan_spot(s, next).y
			var want: int = clampi(int(round((ry + h.y - 5.0) / spacing - 1.0)), 0, 5)
			step = clampi(want - int(s.funnelGap), -2, 2)
		s.funnelGap = clampi(int(s.funnelGap) + step, 0, 5)
		var from: float = float(s.flow)
		var centre: float = float(s.funnelGap) + 1.0
		var speed: float = 1.3 + phase * 0.2
		for i: int in range(slots):
			if i >= int(s.funnelGap) and i <= int(s.funnelGap) + 2: continue
			var lag: float = absf(float(i) - centre) * 5.0
			D.shot(s, {"space": "box", "x": from * (h.x + 14.0 + lag), "y": -h.y + 5.0 + i * spacing, "vx": -from * speed, "collide": "rect", "w": 4.0, "h": 5.0, "shape": "rider", "life": 260, "funnel": true})
	if phase > 0 and t % 56 == 28 and t > 40 and t < 400:
		var left: bool = D.rand(s) < 0.5
		var h2: Vector2 = D.half(s)
		var start: Vector2 = Vector2((-h2.x - 18.0) if left else (h2.x + 18.0), -h2.y - 30.0)
		var target: Vector2 = Vector2(float(s.soul.x), float(s.soul.y)) + Vector2(D.rand_range(s, -10.0, 10.0), 0)
		var ticks: float = 62.0
		var g: float = 0.07
		D.shot(s, {"space": "box", "x": start.x, "y": start.y, "vx": (target.x - start.x) / ticks, "vy": (target.y - start.y - 0.5 * g * ticks * ticks) / ticks, "ay": g, "r": 4.5, "shape": "bottle", "spin": 0.15 * (1.0 if left else -1.0), "life": 200})

# ---------------------------------------------------------------- tape

## Course Tape: lengths of course tape slide in from the edges, each with one gap
## near you, building a moving grid. Phase 1: the tape is re-strung as it moves,
## so each gap slides along it.
static func _tape(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 236.0, "h": 112.0}, 24)
	if t < 14 or t > 384: return
	if t % 40 == 14:
		var h: Vector2 = D.half(s)
		var horizontal: bool = int(t / 40) % 2 == 0
		var from: float = -1.0 if D.rand(s) < 0.5 else 1.0
		var slide: float = (0.45 if D.rand(s) < 0.5 else -0.45) if phase > 0 else 0.0
		var gap: float = 32.0
		if horizontal:
			var gx: float = clampf(float(s.soul.x) + D.rand_range(s, 16.0, 46.0) * (-1.0 if D.rand(s) < 0.5 else 1.0), -h.x + 22.0, h.x - 22.0)
			var next_h: int = _next_route(t, 150, s)
			if next_h >= 0: gx = clampf(_plan_spot(s, next_h).x + D.rand_range(s, -9.0, 9.0), -h.x + 22.0, h.x - 22.0)
			var y: float = from * (h.y + 6.0)
			D.warn(s, {"kind": "tape", "a": Vector2(-h.x, from * (h.y - 2.0)), "b": Vector2(h.x, from * (h.y - 2.0)), "gap": gx, "horizontal": true}, 24, true)
			var reach: float = h.x + 260.0
			var left_len: float = (gx - gap * 0.5) + reach
			var right_len: float = reach - (gx + gap * 0.5)
			D.shot(s, {"space": "box", "x": -reach + left_len * 0.5, "y": y, "vy": -from * 0.95, "vx": slide, "collide": "rect", "w": left_len * 0.5, "h": 2.5, "shape": "tape", "life": 170})
			D.shot(s, {"space": "box", "x": reach - right_len * 0.5, "y": y, "vy": -from * 0.95, "vx": slide, "collide": "rect", "w": right_len * 0.5, "h": 2.5, "shape": "tape", "life": 170})
		else:
			var gy: float = clampf(float(s.soul.y) + D.rand_range(s, 16.0, 34.0) * (-1.0 if D.rand(s) < 0.5 else 1.0), -h.y + 18.0, h.y - 18.0)
			var next_v: int = _next_route(t, 150, s)
			if next_v >= 0: gy = clampf(_plan_spot(s, next_v).y + D.rand_range(s, -4.0, 4.0), -h.y + 18.0, h.y - 18.0)
			var x: float = from * (h.x + 6.0)
			D.warn(s, {"kind": "tape", "a": Vector2(from * (h.x - 2.0), -h.y), "b": Vector2(from * (h.x - 2.0), h.y), "gap": gy, "horizontal": false}, 24, true)
			var reach_y: float = h.y + 200.0
			var top_len: float = (gy - gap * 0.5) + reach_y
			var bottom_len: float = reach_y - (gy + gap * 0.5)
			D.shot(s, {"space": "box", "x": x, "y": -reach_y + top_len * 0.5, "vx": -from * 1.25, "vy": slide * 0.6, "collide": "rect", "w": 2.5, "h": top_len * 0.5, "shape": "tape", "life": 230})
			D.shot(s, {"space": "box", "x": x, "y": reach_y - bottom_len * 0.5, "vx": -from * 1.25, "vy": slide * 0.6, "collide": "rect", "w": 2.5, "h": bottom_len * 0.5, "shape": "tape", "life": 230})
	# A lone rider flashes past on your row, pinning the tape down.
	if t % 60 == 44 and t > 60:
		var h3: Vector2 = D.half(s)
		var side: float = -1.0 if D.rand(s) < 0.5 else 1.0
		var y3: float = clampf(float(s.soul.y), -h3.y + 10.0, h3.y - 10.0)
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h3.x - 4.0), "y": y3, "dir": Vector2(-side, 0)}, 30)
		D.shot(s, {"space": "box", "x": side * (h3.x + 10.0 + 2.0 * 30.0), "y": y3, "vx": -side * 2.0, "r": 5.0, "shape": "rider", "life": 240})

# ---------------------------------------------------------------- gravel

## Loose Gravel: the soul slides (momentum), except on the swept marked route.
## LOOSE GRAVEL signs bounce around the box and street-sweeper brooms push along called rows.
## Phase 1: a fourth sign, and the road cambers (the slide drifts downhill).
static func _gravel(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 248.0, "h": 112.0}, 24)
		s.lastSoul = Vector2(float(s.soul.x), float(s.soul.y))
		var count: int = 4 if phase > 0 else 3
		for i: int in range(count):
			var x: float = -96.0 + i * (192.0 / float(count - 1))
			var y: float = -30.0 if i % 2 == 0 else 30.0
			var a: float = PI * 0.25 + (PI * 0.5 if i % 2 == 0 else 0.0) + (PI if i >= 2 else 0.0)
			D.shot(s, {"space": "box", "x": x, "y": y, "vx": cos(a) * 1.15, "vy": sin(a) * 1.15, "hold": true, "arm": 45, "collide": "rect", "w": 6.0, "h": 8.0, "shape": "gravel_sign", "life": 900, "sign": true})
	# Slip: the wind carries what you put in, and lets go slowly.
	var pos: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var rot: float = float(s.box.rot)
	var moved: Vector2 = pos - Vector2(s.lastSoul)
	var input: Vector2 = moved - Vector2(s.wind).rotated(-rot)
	var dry: bool = _dry(s, t, pos)
	if dry: s.slide = Vector2(s.slide) * 0.5
	else: s.slide = Vector2(s.slide) * 0.9 + input * 0.07
	if phase > 0:
		if t == 120 or t == 270:
			var dir: Vector2 = Vector2.RIGHT if t == 120 else Vector2.LEFT
			D.warn(s, {"kind": "arrows", "dir": dir}, 40, true)
			D.banner(s, "THE ROAD CAMBERS", 40)
		if t == 160: s.tilt = Vector2(0.32, 0)
		if t == 300: s.tilt = Vector2(-0.32, 0)
	s.wind = (Vector2(s.slide) + (Vector2.ZERO if dry else Vector2(s.tilt))).rotated(rot)
	for b: Dictionary in s.bullets:
		if not b.get("sign", false) or int(b.age) <= int(b.arm): continue
		if absf(float(b.x)) > h.x - 7.0: b.vx = -signf(float(b.x)) * absf(float(b.vx))
		if absf(float(b.y)) > h.y - 9.0: b.vy = -signf(float(b.y)) * absf(float(b.vy))
	# Street-sweeper brooms push along a called row.
	if t % 64 == 30 and t < 400:
		var side: float = -1.0 if D.rand(s) < 0.5 else 1.0
		var y: float = clampf(pos.y + D.rand_range(s, -8.0, 8.0), -h.y + 14.0, h.y - 14.0)
		if int(t / 64) % 2 == 1: y = D.rand_range(s, -h.y + 14.0, h.y - 14.0)
		D.warn(s, {"kind": "band", "rect": Rect2(-h.x, y - 13.0, h.x * 2.0, 26.0)}, 36, true)
		var speed: float = 3.2
		D.shot(s, {"space": "box", "x": side * (h.x + 12.0 + speed * 36.0), "y": y, "vx": -side * speed, "collide": "rect", "w": 5.0, "h": 12.0, "shape": "broom", "life": 200})
	# Grit flung up from the road, aimed loosely.
	if t % 26 == 8 and t > 40 and t < 410:
		var x: float = clampf(pos.x + D.rand_range(s, -30.0, 30.0), -h.x + 8.0, h.x - 8.0)
		D.shot(s, {"space": "box", "x": x, "y": -h.y - 30.0, "vy": 1.7, "ay": 0.03, "r": 2.6, "shape": "grit", "life": 140})

static func _dry(s: Dictionary, t: int, pos: Vector2) -> bool:
	var r: Dictionary = s.route
	if r.is_empty() or t < int(r.from) or t >= int(r.close) + 10: return false
	return absf(pos.y - float(r.y)) <= 13.0

# ---------------------------------------------------------------- velodrome

## Velodrome: three lanes of riders circle the infield in a square
## box, alternating direction. REVERSE calls flip a lane after a warning;
## cancelled calls do not. Phase 1: the infield crew throws water bottles outward.
static func _velodrome(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 112.0, "h": 112.0}, 30)
		D.shot(s, {"space": "box", "x": 0.0, "y": 0.0, "hold": true, "arm": 40, "r": 8.0, "shape": "infield", "life": 900})
		for corner: Vector2 in [Vector2(-47, -47), Vector2(47, -47), Vector2(47, 47), Vector2(-47, 47)]:
			D.shot(s, {"space": "box", "x": corner.x, "y": corner.y, "hold": true, "arm": 40, "r": 10.0, "shape": "bike_rack", "life": 900})
		var cars: Array[int] = [2, 3, 3]
		for lane: int in range(3):
			var radius: float = LANES[lane]
			var step: float = 11.0 / radius
			for car: int in range(cars[lane]):
				var base: float = car * TAU / cars[lane] + lane * 0.7
				for j: int in range(2):
					D.shot(s, {"space": "box", "orbit": {"ox": 0.0, "oy": 0.0, "radius": radius, "angle": base + j * step, "av": LANE_SPEED[lane]}, "arm": 45, "r": 4.5, "shape": "rider", "life": 900, "lane": lane})
	if t >= 56 and t <= 380 and (t - 56) % 54 == 0:
		var lane: int = int(D.rand(s) * 3.0)
		var crossed: bool = D.rand(s) < 0.25
		if lane == 2 and _next_route(t + 40, 30) >= 0: crossed = true
		s.calls.append({"at": t, "fire": t + 40, "text": "LANE %d REVERSE" % (lane + 1), "crossed": crossed, "swap": -1, "crossAt": t if crossed else -1, "lane": lane})
		D.warn(s, {"kind": "lanespin", "lane": lane, "dir": -signf(_lane_av(s, lane)), "crossed": crossed}, 40, true)
	for call: Dictionary in s.calls:
		if int(call.fire) == t and not call.crossed:
			for b: Dictionary in s.bullets:
				if b.has("lane") and int(b.lane) == int(call.lane): b.orbit.av = -float(b.orbit.av)
	if phase > 0 and t % 48 == 20 and t > 50 and t < 400:
		var aim: float = Vector2(float(s.soul.x), float(s.soul.y)).angle()
		for i: int in range(3):
			var a: float = aim + (i - 1) * 0.55 + D.rand_range(s, -0.12, 0.12)
			D.shot(s, {"space": "box", "x": 0.0, "y": 0.0, "vx": cos(a) * 1.25, "vy": sin(a) * 1.25, "hold": true, "arm": 22, "r": 3.5, "shape": "bottle", "life": 160})

static func _lane_av(s: Dictionary, lane: int) -> float:
	for b: Dictionary in s.bullets:
		if b.has("lane") and int(b.lane) == lane: return float(b.orbit.av)
	return LANE_SPEED[lane]

# ---------------------------------------------------------------- progress / drawing

static func progress(s: Dictionary) -> String:
	return "Marked routes %d/3\nCancelled calls stay cancelled" % mini(3, int(s.routesKept))

static func _t(s: Dictionary) -> int:
	return int(s.clock) - int(s.leadIn)

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var t: int = _t(s)
	var h: Vector2 = D.half(s)
	var id: String = str(s.patternId)
	if id == "velodrome":
		for lane: int in range(3):
			c.draw_arc(v.box_point(Vector2.ZERO), LANES[lane], 0, TAU, 48, Color(0.55, 0.4, 0.26, 0.38), 9.0)
			c.draw_arc(v.box_point(Vector2.ZERO), LANES[lane] + 7.5, 0, TAU, 48, Color(CREAM, 0.12), 1.0)
	if id == "gravel":
		c.draw_colored_polygon(v.box_rect_poly(Rect2(-h, h * 2.0)), Color(GRAVEL, 0.08))
		for i: int in range(44):
			var gx: float = fposmod(float(i) * 47.3, h.x * 2.0) - h.x
			var gy: float = fposmod(float(i) * 31.7 + float(i % 3) * 9.0, h.y * 2.0) - h.y
			c.draw_rect(Rect2(v.box_point(Vector2(gx, gy)), Vector2(1.5, 1.5)), Color(GRAVEL, 0.35))
	# The marked route and the crossed-out call.
	var r: Dictionary = s.route
	if not r.is_empty() and t >= int(r.from) and t < int(r.close) + 20:
		var live: bool = t >= int(r.open) and t < int(r.close)
		var pulse: float = 0.5 + 0.5 * sin(float(s.clock) * 0.25)
		if r.ring:
			var exit_at: Vector2 = Vector2(float(r.x), float(r.y))
			var lane_rect: Rect2 = Rect2(exit_at - Vector2(12, 12) + exit_at.normalized() * 6.0, Vector2(24, 24))
			c.draw_colored_polygon(v.box_rect_poly(lane_rect), Color(MINT, 0.14 if live else 0.05 + 0.06 * pulse))
			var dl: Vector2 = Vector2(float(r.dx), float(r.dy))
			c.draw_colored_polygon(v.box_rect_poly(Rect2(dl - Vector2(12, 12) + dl.normalized() * 6.0, Vector2(24, 24))), Color(PLUM, 0.25))
			_cross(c, v.box_point(dl), 7.0)
			if not live and not r.counted: c.draw_arc(v.box_point(Vector2(float(r.x), float(r.y))), 10.0, 0, TAU, 20, Color(MINT, 0.4 + 0.5 * pulse), 1.0)
		else:
			var band: Rect2 = Rect2(-h.x, float(r.y) - 13.0, h.x * 2.0, 26.0)
			c.draw_colored_polygon(v.box_rect_poly(band), Color(MINT, 0.16 if live else 0.07 + 0.07 * pulse))
			c.draw_line(v.box_point(Vector2(-h.x, float(r.y) - 13.0)), v.box_point(Vector2(h.x, float(r.y) - 13.0)), Color(MINT, 0.3), 1)
			c.draw_line(v.box_point(Vector2(-h.x, float(r.y) + 13.0)), v.box_point(Vector2(h.x, float(r.y) + 13.0)), Color(MINT, 0.3), 1)
			var dband: Rect2 = Rect2(-h.x, float(r.dy) - 13.0, h.x * 2.0, 26.0)
			c.draw_colored_polygon(v.box_rect_poly(dband), Color(PLUM, 0.22))
			c.draw_line(v.box_point(Vector2(-h.x, float(r.dy))), v.box_point(Vector2(h.x, float(r.dy))), Color(PLUM, 0.9), 1)
			_cross(c, v.box_point(Vector2(float(r.dx), float(r.dy))), 8.0)
			if not live and not r.counted:
				var spot: Rect2 = Rect2(Vector2(float(r.x) - RW, float(r.y) - RH), Vector2(RW, RH) * 2.0)
				var poly: PackedVector2Array = v.box_rect_poly(spot)
				c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(MINT, 0.35 + 0.5 * pulse), 1)
	# Call bands.
	for call: Dictionary in s.calls:
		if t < int(call.at) or t >= int(call.fire): continue
		if call.has("lane"): continue
		for span: Array in REGIONS[str(call.text)]:
			var rect: Rect2 = Rect2(float(span[0]), -h.y, float(span[1]) - float(span[0]), h.y * 2.0)
			var poly2: PackedVector2Array = v.box_rect_poly(rect)
			if call.crossed:
				c.draw_colored_polygon(poly2, Color(PLUM, 0.16))
				c.draw_line(poly2[0], poly2[2], Color(PLUM, 0.6), 1)
				c.draw_line(poly2[1], poly2[3], Color(PLUM, 0.6), 1)
			else:
				var p: float = float(t - int(call.at)) / float(int(call.fire) - int(call.at))
				c.draw_colored_polygon(poly2, Color(ROSE, 0.08 + 0.16 * p + 0.06 * sin(float(s.clock) * 0.6)))
				c.draw_polyline(poly2 + PackedVector2Array([poly2[0]]), Color(ROSE, 0.5), 1)
	for w: Dictionary in s.warnings:
		var f: float = 0.5 + 0.5 * sin(float(w.age) * 0.5)
		match str(w.kind):
			"band":
				var poly3: PackedVector2Array = v.box_rect_poly(w.rect)
				c.draw_colored_polygon(poly3, Color(ROSE, 0.08 + 0.12 * f))
				c.draw_polyline(poly3 + PackedVector2Array([poly3[0]]), Color(ROSE, 0.4), 1)
			"tape":
				var a: Vector2 = w.a
				var b: Vector2 = w.b
				var along: Vector2 = (b - a).normalized()
				var gap_at: Vector2 = Vector2(float(w.gap), a.y) if w.horizontal else Vector2(a.x, float(w.gap))
				var n: int = int(a.distance_to(b) / 8.0)
				for i: int in range(n):
					var p0: Vector2 = a + along * (i * 8.0)
					if p0.distance_to(gap_at) < 15.0: continue
					c.draw_line(v.box_point(p0), v.box_point(p0 + along * 4.0), Color(PINK, 0.4 + 0.5 * f), 2)
				c.draw_arc(v.box_point(gap_at), 5.0, 0, TAU, 12, Color(MINT, 0.6), 1)
			"lanespin":
				var lane: int = int(w.lane)
				var col: Color = Color(PLUM, 0.7) if w.crossed else Color(ROSE, 0.4 + 0.5 * f)
				var a0: float = float(w.age) * 0.08 * float(w.dir)
				for k: int in range(4):
					var ang: float = a0 + k * TAU / 4.0
					var at: Vector2 = v.box_point(Vector2.from_angle(ang) * LANES[lane])
					var tangent: Vector2 = Vector2.from_angle(ang + PI * 0.5 * float(w.dir)).rotated(float(s.box.rot))
					v.chevron(c, at, tangent, col)

static func _cross(c: CanvasItem, at: Vector2, size: float) -> void:
	c.draw_line(at + Vector2(-size, -size), at + Vector2(size, size), Color(PLUM, 0.95), 3)
	c.draw_line(at + Vector2(-size, size), at + Vector2(size, -size), Color(PLUM, 0.95), 3)
	c.draw_line(at + Vector2(-size, -size), at + Vector2(size, size), CREAM, 1)
	c.draw_line(at + Vector2(-size, size), at + Vector2(size, -size), CREAM, 1)

## What a call sign says: the rider's call, or CALL CANCELLED once it is struck out.
const SIGN_TEXT: Dictionary = {"LEFT": "ON YOUR LEFT!", "RIGHT": "ON YOUR RIGHT!", "MIDDLE": "UP THE MIDDLE!", "BOTH SIDES": "BOTH SIDES!"}

static func _sign_text(call: Dictionary) -> String:
	if call.crossed: return "CALL CANCELLED"
	if call.has("lane"): return str(call.text).replace(" REVERSE", ": REVERSE!")
	return str(SIGN_TEXT.get(str(call.text), str(call.text)))

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var t: int = _t(s)
	var h: Vector2 = D.half(s)
	# Rider call signs above the box: live calls in pink, cancelled ones struck out.
	for call: Dictionary in s.calls:
		if t < int(call.at) or t >= int(call.fire) + 10: continue
		var cx: float = 0.0
		if not call.has("lane"):
			var spans: Array = REGIONS[str(call.text)]
			cx = 0.0 if spans.size() > 1 else (float(spans[0][0]) + float(spans[0][1])) * 0.5
		# Struck-out calls step up out of the way of the live one.
		var at: Vector2 = v.box_point(Vector2(cx, -h.y)) + Vector2(0, -30 if call.crossed and int(call.crossAt) > int(call.at) else -14)
		var words: String = _sign_text(call)
		var width: float = 16.0 + words.length() * 8.0
		var rect: Rect2 = Rect2(at - Vector2(width * 0.5, 8), Vector2(width, 14))
		c.draw_rect(rect, Color("2c2232") if call.crossed else Color("3a1c30"))
		c.draw_rect(rect, PLUM if call.crossed else PINK, false, 1)
		v.text(c, at + Vector2(0, 3), words, Color(CREAM, 0.5) if call.crossed else CREAM, width)
		if call.crossed:
			c.draw_line(rect.position + Vector2(2, 7), rect.end - Vector2(2, 7), ROSE, 2)
		_bike_icon(c, rect.position + Vector2(-6, 13), 1.0)

## A little bicycle in profile: two wheels and a frame.
static func _bike_icon(c: CanvasItem, base: Vector2, alpha: float) -> void:
	var rear: Vector2 = base + Vector2(-3.2, -2.0)
	var front: Vector2 = base + Vector2(3.2, -2.0)
	c.draw_arc(rear, 1.9, 0, TAU, 8, Color(CREAM, alpha), 1)
	c.draw_arc(front, 1.9, 0, TAU, 8, Color(CREAM, alpha), 1)
	c.draw_polyline(PackedVector2Array([rear, base + Vector2(-0.4, -5.6), front]), Color(PINK, alpha), 1)
	c.draw_line(base + Vector2(-0.4, -5.6), base + Vector2(1.6, -5.6), Color(LIME, alpha), 1)

## Which way a bullet is travelling on screen (riders face their direction of travel).
static func _heading(b: Dictionary, v: Node2D) -> float:
	var box_turn: float = float(v.pattern.box.rot) if str(b.space) == "box" else 0.0
	if b.has("orbit"):
		var o: Dictionary = b.orbit
		return float(o.angle) + (PI * 0.5 if float(o.get("av", 0.0)) >= 0.0 else -PI * 0.5) + box_turn
	var velocity: Vector2 = Vector2(float(b.vx), float(b.vy))
	return (velocity.angle() if velocity.length() > 0.05 else PI * 0.5) + box_turn

## A cyclist seen from above: a long thin bike, a handlebar, the jersey and a helmet up front.
static func _draw_rider(c: CanvasItem, at: Vector2, heading: float, jersey: Color, helmet: Color, alpha: float) -> void:
	var f: Vector2 = Vector2.from_angle(heading)
	var n: Vector2 = Vector2(-f.y, f.x)
	c.draw_line(at - f * 5.5, at + f * 5.5, Color(INK, alpha), 3)
	c.draw_line(at - f * 4.5, at + f * 4.5, Color(CREAM, 0.85 * alpha), 1)
	c.draw_line(at + f * 2.5 - n * 3.4, at + f * 2.5 + n * 3.4, Color(INK, alpha), 2)
	c.draw_colored_polygon(PackedVector2Array([at + f * 2.2 - n * 3.0, at + f * 2.2 + n * 3.0, at - f * 2.6 + n * 1.8, at - f * 2.6 - n * 1.8]), Color(jersey, alpha))
	c.draw_line(at + f * 1.8, at - f * 2.2, Color(CREAM, 0.8 * alpha), 1)
	c.draw_circle(at + f * 3.4, 2.2, Color(helmet, alpha))
	c.draw_circle(at + f * 3.9, 1.0, Color(INK, 0.55 * alpha))

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	var armed: bool = int(b.age) > int(b.arm)
	var a: float = alpha * (1.0 if armed else 0.35 + 0.35 * sin(float(b.age) * 0.4))
	match str(b.shape):
		"rider":
			var kit: Array = KITS[int(b.get("id", 0)) % KITS.size()]
			_draw_rider(c, at, _heading(b, v), kit[0], kit[1], a)
			return true
		"wheel":
			# A loose wheel rolling across the road.
			c.draw_arc(at, 4.6, 0, TAU, 14, Color(INK, a), 3)
			c.draw_arc(at, 4.6, 0, TAU, 14, Color(CREAM, 0.85 * a), 1)
			for k: int in range(3):
				var spoke: Vector2 = Vector2.from_angle(turn + k * PI / 3.0) * 4.0
				c.draw_line(at - spoke, at + spoke, Color(CREAM, 0.7 * a), 1)
			c.draw_circle(at, 1.0, Color(PINK, a))
			return true
		"bottle":
			# A water bottle: tumbling when thrown, level when it leaves the infield.
			var ang: float = turn if absf(float(b.spin)) > 0.001 else _heading(b, v)
			var f: Vector2 = Vector2.from_angle(ang)
			var n: Vector2 = Vector2(-f.y, f.x)
			c.draw_colored_polygon(PackedVector2Array([at - f * 4.0 - n * 1.9, at + f * 2.5 - n * 1.9, at + f * 2.5 + n * 1.9, at - f * 4.0 + n * 1.9]), Color(CYAN, a))
			c.draw_colored_polygon(PackedVector2Array([at + f * 2.5 - n * 1.0, at + f * 4.0 - n * 1.0, at + f * 4.0 + n * 1.0, at + f * 2.5 + n * 1.0]), Color(CREAM, a))
			c.draw_colored_polygon(PackedVector2Array([at + f * 4.0 - n * 1.3, at + f * 5.2 - n * 1.3, at + f * 5.2 + n * 1.3, at + f * 4.0 + n * 1.3]), Color(LIME, a))
			c.draw_line(at - f * 1.0 - n * 1.9, at - f * 1.0 + n * 1.9, Color(PINK, a), 1)
			return true
		"tape":
			# Course tape in club colours: pink and white stripes.
			var q: PackedVector2Array = v.quad(at, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(q, Color(CREAM, a))
			var long_x: bool = float(b.w) > float(b.h)
			var length: float = (float(b.w) if long_x else float(b.h))
			var axis: Vector2 = (Vector2(1, 0) if long_x else Vector2(0, 1)).rotated(turn)
			var across: Vector2 = Vector2(-axis.y, axis.x)
			var d: float = -length + 3.0
			while d < length - 3.0:
				var p: Vector2 = at + axis * d
				c.draw_line(p - across * 2.5, p + axis * 4.0 + across * 2.5, Color(PINK, a), 2)
				d += 9.0
			return true
		"gravel_sign":
			# A LOOSE GRAVEL diamond: yellow, three stones and a skid line.
			var up2: Vector2 = Vector2(0, -1).rotated(turn)
			var side2: Vector2 = Vector2(1, 0).rotated(turn)
			var diamond: PackedVector2Array = PackedVector2Array([at + up2 * 9.0, at + side2 * 7.0, at - up2 * 9.0, at - side2 * 7.0])
			c.draw_colored_polygon(diamond, Color(TAPE, a))
			c.draw_polyline(diamond + PackedVector2Array([diamond[0]]), Color(INK, a), 1)
			c.draw_circle(at - side2 * 2.5 + up2 * 1.5, 1.1, Color(INK, a))
			c.draw_circle(at + side2 * 2.2 - up2 * 0.5, 1.1, Color(INK, a))
			c.draw_circle(at - side2 * 0.5 - up2 * 4.0, 1.1, Color(INK, a))
			c.draw_line(at - side2 * 3.5 + up2 * 4.5, at + side2 * 1.5 + up2 * 3.0, Color(INK, a), 1)
			return true
		"broom":
			# A street sweeper's push broom: wooden handle, tan bristle head, loose bristle ends.
			var up3: Vector2 = Vector2(0, -1).rotated(turn)
			c.draw_line(at - up3 * 12.0, at + up3 * 22.0, Color("8a6a48", alpha), 2)
			c.draw_colored_polygon(v.quad(at - up3 * 5.0, 5.0, 7.0, turn), Color(Color("c9a86a"), alpha))
			c.draw_line(at + Vector2(-5, -4).rotated(turn), at + Vector2(5, -4).rotated(turn), Color(PINK, alpha), 1)
			for i: int in range(4):
				var x: float = -4.0 + i * 2.7
				c.draw_line(at + Vector2(x, 2).rotated(turn), at + Vector2(x + sin(float(b.age) * 0.4 + i) * 1.2, 10).rotated(turn), Color(Color("8a6a3c"), alpha), 1)
			return true
		"infield":
			# The velodrome infield: grass, a white line and a club pennant.
			c.draw_circle(at, float(b.r), Color(Color("3c5a3a"), a))
			c.draw_arc(at, float(b.r), 0, TAU, 20, Color(LIME, a), 1)
			c.draw_arc(at, float(b.r) - 3.0, 0, TAU, 16, Color(CREAM, 0.35 * a), 1)
			c.draw_line(at + Vector2(-1, 4), at + Vector2(-1, -6), Color(CREAM, a), 1)
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-1, -6), at + Vector2(5, -4), at + Vector2(-1, -2)]), Color(PINK, a))
			return true
		"bike_rack":
			# Bikes parked in the corners of the infield.
			c.draw_circle(at, float(b.r), Color(Color("2a2430"), a))
			for i: int in range(3):
				_bike_icon(c, at + Vector2(-6 + i * 6, 6 - (i % 2) * 5), a)
			c.draw_arc(at, float(b.r), 0, TAU, 20, Color(PINK, 0.6 * a), 1)
			return true
	return false
