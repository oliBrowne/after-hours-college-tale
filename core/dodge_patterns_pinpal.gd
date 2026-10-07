extends RefCounted
## PIN PAL / Return Service: a bowling pin running the ball return. Five
## handmade attacks, one per turn, cycling in order. The soul is in flipper
## mode in every attack: it runs along the lane floor and confirm swings the
## flipper. The promise is the old one: return three balls (s.deflections).
## Balls are the threat and the objective at once: flip one back and it is
## yours, let it land on you and it hurts. Pins, rakes and gutters are not
## returnable: dodge them sideways. Phase 1 (from the second turn) adds a layer
## to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["return_service", "bumpers", "pinsetter", "tilt", "strike"]
const PHASES: Array[int] = [0, 1]
const BALL_R: float = 5.5
const GUTTER: float = 14.0

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const ROSE: Color = Color("e8837b")
const LILAC: Color = Color("a68db8")
const PIN_RED: Color = Color("c8505a")
const BALL_BLUE: Color = Color("5b6fc8")
const WOOD: Color = Color("8a6a44")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 480 + 60 * clampi(int(s.phase), 0, 1)
	s.queue = []
	s.tells = []
	s.bumpers = []
	s.rakes = []
	s.chutes = []
	s.lit = -1
	s.litUntil = -1
	s.tiltTarget = 0.0
	s.tiltNow = 0.0
	s.rack = {}
	s.floorY = 48.0
	s.markers = [{"id": 0, "x": 128.0, "y": 104.0, "collected": false, "active": false}]
	D.set_mode(s, "flipper")
	match id:
		"return_service":
			s.phaseName = "Return Service"
			s.hint = "Stand under a falling ball and confirm to flip it back. Pins fall in the red lanes."
		"bumpers":
			s.phaseName = "Bumper Alley"
			s.hint = "Balls ricochet off the bumpers. A lit bumper drops a chip straight down. Flip the balls."
		"pinsetter":
			s.phaseName = "Pinsetter"
			s.hint = "The sweep bar comes down. Wait under its gap. The ball follows through the gap: flip it."
		"tilt":
			s.phaseName = "TILT"
			s.hint = "The lane tilts and you slide. Keep out of the gutters at both ends. Flip the balls."
		"strike":
			s.phaseName = "Strike!"
			s.hint = "Strike! Pins fly and fall where they land. Then the balls come back: flip them."

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return int(s.deflections) >= 3

static func progress(s: Dictionary) -> String:
	return "Balls returned %d/3" % mini(3, int(s.deflections))

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	s.floorY = D.half(s).y - 12.0
	match str(s.patternId):
		"return_service": _return_service(s, t, phase)
		"bumpers": _bumpers(s, t, phase)
		"pinsetter": _pinsetter(s, t, phase)
		"tilt": _tilt(s, t, phase)
		"strike": _strike(s, t, phase)
	_run_queue(s, t)

static func after(s: Dictionary, t: int) -> void:
	_ball_physics(s, t)
	_bot_hint(s)
	s.markers[0].collected = int(s.deflections) >= 3
	var kept: Array = []
	for tell: Dictionary in s.tells:
		if int(tell.until) > int(s.clock): kept.append(tell)
	s.tells = kept

# ---------------------------------------------------------------- shared pieces

## Queue an event for a later tick: {"at": t, "kind": ..., ...}.
static func _later(s: Dictionary, event: Dictionary) -> void:
	s.queue.append(event)

static func _run_queue(s: Dictionary, t: int) -> void:
	var kept: Array = []
	var due: Array = []
	for e: Dictionary in s.queue:
		if int(e.at) <= t: due.append(e)
		else: kept.append(e)
	s.queue = kept
	for e: Dictionary in due:
		match str(e.kind):
			"ball": _ball(s, float(e.x), float(e.get("vx", 0.0)), float(e.get("vy", 1.0)), bool(e.get("arena", false)))
			"pin": _pin(s, float(e.x), float(e.get("vx", 0.0)), float(e.get("speed", 2.4)), bool(e.get("arena", false)))
			"spark": _spark(s, float(e.x), float(e.y), int(e.get("count", 1)))
			"strike": _strike_hit(s)
			"spare":
				if t < int(s.length) - 90:
					var h: Vector2 = D.half(s)
					_pin_lane(s, t, clampf(float(s.soul.x), -h.x + 8.0, h.x - 8.0), 40, 2.5)

## A ball drop: a chevron and ghost ball at the top for `warn` ticks, then the
## ball. x is box space unless arena is true.
static func _drop(s: Dictionary, t: int, x: float, vx: float, warn_ticks: int = 40, arena: bool = false, vy: float = 1.0) -> void:
	var at: Vector2 = Vector2(x, D.centre(s).y - D.half(s).y + 6.0) if arena else D.to_world(s, Vector2(x, -D.half(s).y + 6.0))
	s.tells.append({"x": at.x, "y": at.y, "until": int(s.clock) + warn_ticks, "kind": "ball"})
	_later(s, {"at": t + warn_ticks, "kind": "ball", "x": x, "vx": vx, "vy": vy, "arena": arena})

static func _ball(s: Dictionary, x: float, vx: float, vy: float, arena: bool = false) -> void:
	var b: Dictionary = {"space": "box", "x": x, "y": -D.half(s).y - 6.0, "vx": vx, "vy": vy, "ay": 0.028, "r": BALL_R, "shape": "ball", "returnable": true, "ball": true, "life": 600}
	if arena:
		b.space = "arena"
		b.y = D.centre(s).y - D.half(s).y - 30.0
	D.shot(s, b)

## A pin dropped down a red lane after a warning (box x unless arena).
static func _pin_lane(s: Dictionary, t: int, x: float, warn_ticks: int = 36, speed: float = 2.4, arena: bool = false, vx: float = 0.0) -> void:
	var world_x: float = x if arena else D.centre(s).x + x
	D.warn(s, {"kind": "lane", "x": world_x, "w": 5.0, "horizontal": false}, warn_ticks)
	_later(s, {"at": t + warn_ticks - 8, "kind": "pin", "x": x, "speed": speed, "arena": arena, "vx": vx})

static func _pin(s: Dictionary, x: float, vx: float, speed: float, arena: bool = false) -> Dictionary:
	var b: Dictionary = {"space": "box", "x": x, "y": -D.half(s).y - 12.0, "vx": vx, "vy": speed, "collide": "rect", "w": 3.0, "h": 7.0, "r": 5.0, "shape": "pin", "spin": 0.0, "life": 300}
	if arena:
		b.space = "arena"
		b.y = D.centre(s).y - D.half(s).y - 34.0
	return D.shot(s, b)

## Chips a lit bumper drops straight down (or in a V).
static func _spark(s: Dictionary, x: float, y: float, count: int) -> void:
	for i: int in range(count):
		var vx: float = (float(i) - float(count - 1) * 0.5) * 0.6
		D.shot(s, {"space": "box", "x": x, "y": y, "vx": vx, "vy": 2.2, "ay": 0.02, "r": 3.0, "shape": "chip", "spin": 0.3, "life": 200})

## Balls bounce off the side walls and bumpers (box space even when the ball
## lives in arena space), and leave a gutter puff when they drop past you.
static func _ball_physics(s: Dictionary, t: int) -> void:
	var h: Vector2 = D.half(s)
	var rot: float = float(s.box.rot)
	for b: Dictionary in s.bullets:
		if not b.get("ball", false) or b.has("fade"): continue
		var box: bool = b.space == "box"
		var at: Vector2 = Vector2(float(b.x), float(b.y)) if box else D.to_local(s, Vector2(float(b.x), float(b.y)))
		var vel: Vector2 = Vector2(float(b.vx), float(b.vy)) if box else Vector2(float(b.vx), float(b.vy)).rotated(-rot)
		var changed: bool = false
		if absf(at.x) > h.x - BALL_R and signf(vel.x) == signf(at.x) and at.y > -h.y - 4.0:
			vel.x = -vel.x * 0.9; changed = true
		if not b.get("friendly", false):
			for bumper: Dictionary in s.bumpers:
				var centre: Vector2 = Vector2(float(bumper.x), float(bumper.y))
				var off: Vector2 = at - centre
				if off.length() < float(bumper.r) + BALL_R and vel.dot(off) < 0.0:
					var n: Vector2 = off.normalized()
					vel = vel - 2.0 * vel.dot(n) * n
					vel = vel.normalized() * clampf(vel.length() * 1.05, 1.4, 2.3)
					changed = true
					if int(bumper.flash) <= 0 and t >= 0:
						bumper.flash = 26
						D.effect(s, "pulse", D.to_world(s, centre), 14)
						if s.patternId == "bumpers":
							var count: int = 3 if int(s.phase) > 0 else 1
							var drop: Vector2 = centre + Vector2(0, float(bumper.r) + 2.0)
							D.warn(s, {"kind": "lane", "x": D.centre(s).x + drop.x, "w": 4.0 + 6.0 * float(count - 1), "horizontal": false}, 26)
							_later(s, {"at": t + 26, "kind": "spark", "x": drop.x, "y": drop.y, "count": count})
			if at.y > h.y + 2.0 and not b.get("gone", false):
				b.gone = true
				D.effect(s, "gutter", D.to_world(s, Vector2(at.x, h.y - 2.0)), 30)
		elif at.y < -h.y - 2.0 and not b.get("home_run", false):
			b.home_run = true
			D.effect(s, "kept", D.to_world(s, Vector2(at.x, -h.y + 2.0)), 24)
		if changed:
			if box:
				b.vx = vel.x; b.vy = vel.y
			else:
				var w: Vector2 = vel.rotated(rot)
				b.vx = w.x; b.vy = w.y
	for bumper: Dictionary in s.bumpers:
		bumper.flash = maxi(0, int(bumper.flash) - 1)

## QA autopilot: wait where the next falling ball will reach the floor.
static func _bot_hint(s: Dictionary) -> void:
	s.botGoal = null
	if int(s.deflections) >= 3: return
	var h: Vector2 = D.half(s)
	var rot: float = float(s.box.rot)
	var floor_y: float = float(s.floorY)
	var best: float = INF
	for b: Dictionary in s.bullets:
		if not b.get("ball", false) or b.get("friendly", false) or b.has("fade"): continue
		var box: bool = b.space == "box"
		var at: Vector2 = Vector2(float(b.x), float(b.y)) if box else D.to_local(s, Vector2(float(b.x), float(b.y)))
		var vel: Vector2 = Vector2(float(b.vx), float(b.vy)) if box else Vector2(float(b.vx), float(b.vy)).rotated(-rot)
		var acc: Vector2 = Vector2(float(b.ax), float(b.ay)) if box else Vector2(float(b.ax), float(b.ay)).rotated(-rot)
		var dy: float = floor_y - 14.0 - at.y
		if dy < -6.0: continue
		var eta: float = maxf(0.0, dy) / maxf(0.4, vel.y)
		if acc.y > 0.001 and dy > 0.0:
			eta = (-vel.y + sqrt(maxf(0.0, vel.y * vel.y + 2.0 * acc.y * dy))) / acc.y
		if eta > 160.0: continue
		var x: float = at.x + vel.x * eta
		var span: float = h.x - BALL_R
		x = span - absf(fposmod(x + span, span * 4.0) - span * 2.0)
		if eta < best:
			best = eta
			s.botGoal = Vector2(x, floor_y)

# ---------------------------------------------------------------- attacks

# Return Service: three chutes over the lane; the lit one drops a ball that
# bounces off the walls. Pins drop in red lanes in pairs, one over you.
# Phase 1 adds a bumper in the middle that knocks the balls off course.
static func _return_service(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 120.0}, 24)
	s.chutes = [-0.62 * h.x, 0.0, 0.62 * h.x]
	if phase > 0:
		s.bumpers = [{"x": 0.0, "y": -0.3 * h.y, "r": 11.0, "flash": int(s.bumpers[0].flash) if s.bumpers.size() > 0 else 0}]
	var every: int = 74 if phase == 0 else 60
	if t % every == 10 and t < int(s.length) - 120:
		var pick: int = int(D.rand(s) * 3.0)
		if pick == int(s.lit): pick = (pick + 1) % 3
		s.lit = pick; s.litUntil = int(s.clock) + 40
		_drop(s, t, float(s.chutes[pick]), D.rand_range(s, 0.4, 0.9) * (1.0 if D.rand(s) < 0.5 else -1.0))
	var pin_every: int = 46 if phase == 0 else 36
	if t % pin_every == 30 and t < int(s.length) - 90:
		var x1: float = clampf(float(s.soul.x), -h.x + 8.0, h.x - 8.0)
		var x2: float = D.rand_range(s, -h.x + 8.0, h.x - 8.0)
		if absf(x2 - x1) < 36.0: x2 = clampf(x1 + 50.0 * (1.0 if x1 < 0.0 else -1.0), -h.x + 8.0, h.x - 8.0)
		_pin_lane(s, t, x1, 40, 2.4)
		_pin_lane(s, t, x2, 40, 2.4)

# Bumper Alley: balls ricochet down through four bumpers. A bumper that is hit
# lights and drops a chip straight down its red lane. A pin falls over you
# now and then. Phase 1 bumpers drift and drop three chips in a V.
static func _bumpers(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 236.0, "h": 132.0}, 24)
	var spots: Array[Vector2] = [Vector2(-0.5, -0.5), Vector2(0.0, -0.66), Vector2(0.5, -0.5), Vector2(0.0, -0.14)]
	var old: Array = s.bumpers
	var next: Array = []
	for i: int in range(spots.size()):
		var drift: float = sin(t * 0.018 + i * 1.7) * 22.0 if phase > 0 else 0.0
		next.append({"x": spots[i].x * h.x + drift, "y": spots[i].y * h.y, "r": 10.0, "flash": int(old[i].flash) if old.size() > i else 0})
	s.bumpers = next
	var every: int = 62 if phase == 0 else 50
	if t % every == 10 and t < int(s.length) - 130:
		var x: float = D.rand_range(s, -0.75, 0.75) * h.x
		_drop(s, t, x, D.rand_range(s, -0.4, 0.4), 36)
	if t % 70 == 45 and t < int(s.length) - 90:
		_pin_lane(s, t, clampf(float(s.soul.x), -h.x + 8.0, h.x - 8.0), 40, 2.6)

# Pinsetter: the sweep bar is outlined at the top, then comes down the lane
# with one gap (marked on the floor). The ball follows down through the gap.
# Pins fall between sweeps. Phase 1 bars slide sideways as they come down.
static func _pinsetter(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 124.0}, 24)
	var every: int = 124 if phase == 0 else 104
	if t % every == 16 and t < int(s.length) - 160:
		var soul_x: float = float(s.soul.x)
		var gx: float = D.rand_range(s, -h.x + 34.0, h.x - 34.0)
		if absf(gx - soul_x) < 60.0: gx = clampf(soul_x + (70.0 if soul_x < 0.0 else -70.0), -h.x + 34.0, h.x - 34.0)
		var drift: float = 0.0
		if phase > 0: drift = 0.4 * (-1.0 if gx > 0.0 else 1.0)
		var gap_half: float = 22.0 if phase == 0 else 20.0
		var arm: int = 50
		var speed: float = 1.5
		var x: float = -h.x - 30.0
		while x <= h.x + 30.0:
			if absf(x - gx) >= gap_half + 9.0:
				D.shot(s, {"space": "box", "x": x, "y": -h.y + 5.0, "vx": drift, "vy": speed, "collide": "rect", "w": 9.0, "h": 4.0, "shape": "rake", "hold": true, "arm": arm, "life": arm + 170})
			x += 18.0
		s.rakes.append({"x": gx, "vx": drift, "y": -h.y + 5.0, "vy": speed, "born": t, "arm": arm, "gap": gap_half})
		D.banner(s, "SWEEP", 40)
		_later(s, {"at": t + arm + 28, "kind": "ball", "x": gx + drift * 28.0, "vx": drift, "vy": 1.3})
	if t % every == 88 and t < int(s.length) - 90:
		var next_gap: float = float(s.rakes[-1].x) if s.rakes.size() > 0 else 0.0
		for i: int in range(1 + phase):
			var px: float = D.rand_range(s, -h.x + 10.0, h.x - 10.0)
			if i == 0: px = clampf(float(s.soul.x), -h.x + 8.0, h.x - 8.0)
			if absf(px - next_gap) < 26.0 and i > 0: px = -px
			_pin_lane(s, t, px, 36, 2.6)
	var kept: Array = []
	for rake: Dictionary in s.rakes:
		var age: int = t - int(rake.born)
		if age > int(rake.arm):
			rake.x = float(rake.x) + float(rake.vx)
			rake.y = float(rake.y) + float(rake.vy)
		if float(rake.y) < h.y + 10.0: kept.append(rake)
	s.rakes = kept

# TILT: the lane tips one way, then the other. You slide downhill and the
# gutters at both ends hurt. Balls and pins fall straight down the screen, so
# they cross the tilted lane at a slant. Phase 1 wobbles the lane and tips it
# further.
static func _tilt(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 228.0, "h": 112.0}, 24)
	var tilt_every: int = 120 if phase == 0 else 100
	var amount: float = 0.26 if phase == 0 else 0.3
	if t % tilt_every == 20 and t < int(s.length) - 100:
		# Mostly alternating, sometimes the same way twice (standing still drifts into a gutter).
		var dir: float = -signf(float(s.tiltTarget)) if absf(float(s.tiltTarget)) > 0.0 else (1.0 if D.rand(s) < 0.5 else -1.0)
		if D.rand(s) < 0.35: dir = -dir
		D.banner(s, "TILT", 40)
		D.warn(s, {"kind": "arrows", "dir": Vector2(dir, 0)}, 40, true)
		s.tiltPending = {"at": t + 40, "rot": dir * amount}
	if s.has("tiltPending") and t == int(s.tiltPending.at):
		s.tiltTarget = float(s.tiltPending.rot)
	if t == int(s.length) - 60: s.tiltTarget = 0.0
	s.tiltNow = move_toward(float(s.tiltNow), float(s.tiltTarget), 0.012)
	var wobble: float = sin(t * 0.09) * 0.05 if phase > 0 and absf(float(s.tiltTarget)) > 0.0 else 0.0
	if t >= 24: s.box.rot = float(s.tiltNow) + wobble
	# Slide downhill; the gutters at both ends hurt.
	var slope: float = sin(float(s.box.rot))
	s.soul.x = float(s.soul.x) + slope * 3.2
	if absf(float(s.soul.x)) > h.x - 4.0 - GUTTER + 2.0 and t >= 24:
		D.hurt(s, D.soul_world(s))
	var every: int = 66 if phase == 0 else 54
	if t % every == 30 and t < int(s.length) - 130:
		var c: Vector2 = D.centre(s)
		var x: float = c.x + D.rand_range(s, -0.6, 0.6) * h.x
		_drop(s, t, x, 0.0, 40, true, 1.0)
	if t % 50 == 5 and t < int(s.length) - 90:
		var c2: Vector2 = D.centre(s)
		# Pins lead you down the slope.
		var lead: float = clampf(float(s.soul.x) + sin(float(s.tiltTarget)) * 3.2 * 70.0, -h.x + GUTTER + 6.0, h.x - GUTTER - 6.0)
		var aim: float = D.to_world(s, Vector2(lead, float(s.floorY))).x
		_pin_lane(s, t, aim, 40, 2.3, true)
		if phase > 0:
			_pin_lane(s, t, c2.x + D.rand_range(s, -0.7, 0.7) * h.x, 40, 2.3, true)

# Strike!: a rack of ten pins sits up the lane; the house ball rolls in from
# the side and scatters them. They arc through the air and land, a few of them
# on you. Then the balls come back down the return: flip them. Phase 1 pins
# bounce once off the lane, and racks come faster.
static func _strike(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 128.0}, 24)
	var every: int = 150 if phase == 0 else 126
	if t % every == 10 and t < int(s.length) - 170:
		var rx: float = D.rand_range(s, -0.45, 0.45) * h.x
		var ry: float = -0.55 * h.y
		var side: float = -1.0 if rx > 0.0 else 1.0
		var id: int = int(t / every)
		s.rack = {"x": rx, "y": ry, "id": id, "side": side, "hit": t + 80}
		var rows: Array[int] = [4, 3, 2, 1]
		for row: int in range(rows.size()):
			for k: int in range(rows[row]):
				var px: float = rx + (float(k) - float(rows[row] - 1) * 0.5) * 9.0
				var py: float = ry - 10.0 + row * 7.0
				D.shot(s, {"space": "box", "x": px, "y": py, "collide": "rect", "w": 3.0, "h": 7.0, "r": 5.0, "shape": "pin", "hold": true, "arm": 9999, "life": 900, "rack": id})
		D.warn(s, {"kind": "edge", "space": "box", "x": side * -(h.x - 3.0), "y": ry, "dir": Vector2(side, 0)}, 50, true)
		var start: Vector2 = Vector2(-side * (h.x + 14.0), ry)
		D.shot(s, {"space": "box", "x": start.x, "y": start.y, "vx": (rx - start.x) / 80.0, "vy": 0.0, "r": 9.0, "shape": "houseball", "friendly": true, "life": 200})
		_later(s, {"at": t + 80, "kind": "strike"})
		# Pin Pal sets up the spare: single pins over you between racks.
		for k: int in range(2):
			_later(s, {"at": t + 150 + k * 40 - 40, "kind": "spare"})
		var balls: int = 2 if phase == 0 else 3
		for i: int in range(balls):
			var spread: float = (float(i) - float(balls - 1) * 0.5)
			_later(s, {"at": t + 120 + i * 16, "kind": "ball", "x": rx + spread * 14.0, "vx": spread * 0.5, "vy": 0.8})
			s.tells.append({"x": D.to_world(s, Vector2(rx + spread * 14.0, -h.y + 6.0)).x, "y": D.to_world(s, Vector2(0, -h.y + 6.0)).y, "until": int(s.clock) + 120 + i * 16, "kind": "ball", "from": int(s.clock) + 90})

static func _strike_hit(s: Dictionary) -> void:
	var rack: Dictionary = s.rack
	if rack.is_empty(): return
	D.banner(s, "STRIKE!", 40)
	D.effect(s, "pulse", D.to_world(s, Vector2(float(rack.x), float(rack.y))), 20)
	var h: Vector2 = D.half(s)
	var floor_y: float = float(s.floorY)
	var g: float = 0.06
	var aimed: int = 0
	for b: Dictionary in s.bullets:
		if int(b.get("rack", -1)) != int(rack.id) or not b.has("hold"): continue
		b.erase("hold")
		b.arm = 0
		var vy: float = D.rand_range(s, -2.3, -1.1)
		var tx: float = D.rand_range(s, -h.x + 6.0, h.x - 6.0)
		if aimed < 3:
			tx = clampf(float(s.soul.x) + D.rand_range(s, -10.0, 10.0), -h.x + 6.0, h.x - 6.0)
			aimed += 1
		var dy: float = floor_y - float(b.y)
		var time: float = (-vy + sqrt(vy * vy + 2.0 * g * dy)) / g
		b.vx = (tx - float(b.x)) / time
		b.vy = vy
		b.ay = g
		b.spin = D.rand_range(s, -0.25, 0.25)
		b.life = int(b.age) + 360
		if int(s.phase) > 0: b.bounce = 0.55

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var t: int = int(s.clock) - int(s.leadIn)
	# Lane boards and the aiming arrows.
	var x: float = -h.x + 12.0
	while x < h.x:
		c.draw_line(v.box_point(Vector2(x, -h.y)), v.box_point(Vector2(x, h.y)), Color(WOOD, 0.16), 1)
		x += 12.0
	for i: int in range(-2, 3):
		var at: Vector2 = Vector2(i * 22.0, h.y * 0.25 + absf(i) * 6.0)
		c.draw_colored_polygon(PackedVector2Array([v.box_point(at + Vector2(0, -4)), v.box_point(at + Vector2(3, 3)), v.box_point(at + Vector2(-3, 3))]), Color(AMBER, 0.14))
	# The floor line the soul runs on.
	var fy: float = minf(float(s.floorY), h.y - 4.0)
	c.draw_line(v.box_point(Vector2(-h.x, fy + 6.0)), v.box_point(Vector2(h.x, fy + 6.0)), Color(MINT, 0.18), 1)
	if s.patternId == "tilt":
		for side: float in [-1.0, 1.0]:
			var inner: float = side * (h.x - GUTTER - 2.0)
			var outer: float = side * (h.x + 2.0)
			var r: Rect2 = Rect2(Vector2(minf(inner, outer), -h.y), Vector2(absf(outer - inner), h.y * 2.0))
			c.draw_colored_polygon(v.box_rect_poly(r), Color(INK, 0.85))
			var shimmer: float = 0.25 + 0.15 * sin(t * 0.2)
			c.draw_line(v.box_point(Vector2(inner, -h.y)), v.box_point(Vector2(inner, h.y)), Color(ROSE, shimmer + 0.2), 1)
			var y: float = -h.y + 8.0
			while y < h.y:
				c.draw_line(v.box_point(Vector2(inner + side * 4.0, y)), v.box_point(Vector2(inner + side * 9.0, y + 5.0)), Color(ROSE, shimmer), 1)
				y += 12.0
	if s.patternId == "pinsetter":
		for rake: Dictionary in s.rakes:
			if t - int(rake.born) > int(rake.arm) + 70: continue
			var gx: float = float(rake.x) + float(rake.vx) * maxf(0.0, float(int(rake.arm) - (t - int(rake.born))))
			var pulse: float = 0.5 + 0.5 * sin(t * 0.3)
			var base: Vector2 = Vector2(gx, fy + 2.0)
			c.draw_line(v.box_point(base + Vector2(-float(rake.gap) + 6.0, 6.0)), v.box_point(base + Vector2(float(rake.gap) - 6.0, 6.0)), Color(MINT, 0.5 + 0.4 * pulse), 2)
			v.chevron(c, v.box_point(base + Vector2(0, -6)), Vector2(0, 1).rotated(float(s.box.rot)), Color(MINT, 0.5 + 0.4 * pulse))
	for bumper: Dictionary in s.bumpers:
		var at2: Vector2 = v.box_point(Vector2(float(bumper.x), float(bumper.y)))
		var lit: float = float(bumper.flash) / 26.0
		c.draw_circle(at2, float(bumper.r), Color("2c2838").lerp(Color("f2d38a"), lit * 0.8))
		c.draw_arc(at2, float(bumper.r), 0, TAU, 20, AMBER.lerp(Color.WHITE, lit), 2)
		c.draw_arc(at2, float(bumper.r) - 4.0, 0, TAU, 16, Color(ROSE, 0.6 + 0.4 * lit), 1)
		c.draw_circle(at2, 2.5, CREAM)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	if s.patternId == "return_service":
		for i: int in range(s.chutes.size()):
			var at: Vector2 = v.box_point(Vector2(float(s.chutes[i]), -h.y - 7.0))
			var lit: bool = i == int(s.lit) and int(s.clock) < int(s.litUntil)
			var col: Color = AMBER if lit and int(s.clock) % 10 < 6 else Color("4a4458")
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-11, -6), at + Vector2(11, -6), at + Vector2(7, 6), at + Vector2(-7, 6)]), Color("1e1b28"))
			c.draw_polyline(PackedVector2Array([at + Vector2(-11, -6), at + Vector2(-7, 6), at + Vector2(7, 6), at + Vector2(11, -6)]), col, 2)
	for tell: Dictionary in s.tells:
		if int(s.clock) < int(tell.get("from", 0)): continue
		var at2: Vector2 = v.arena_point(Vector2(float(tell.x), float(tell.y)))
		var blink: float = 0.5 + 0.5 * sin(float(s.clock) * 0.45)
		c.draw_arc(at2 + Vector2(0, -16), BALL_R, 0, TAU, 14, Color(BALL_BLUE.lightened(0.4), 0.4 + 0.4 * blink), 1)
		v.chevron(c, at2 + Vector2(0, -6), Vector2.DOWN, Color(MINT, 0.5 + 0.5 * blink))
		v.chevron(c, at2 + Vector2(0, -1), Vector2.DOWN, Color(MINT, 0.3 + 0.5 * blink))

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"ball", "houseball":
			var r: float = float(b.r)
			var base: Color = BALL_BLUE if b.shape == "ball" else Color("5a2a3a")
			c.draw_circle(at, r, Color(base, alpha))
			c.draw_arc(at, r, 0, TAU, 18, Color(base.lightened(0.45), alpha), 1)
			var spin: float = float(b.age) * 0.15
			for i: int in range(3):
				var hole: Vector2 = Vector2(r * 0.42, 0).rotated(spin + i * 0.5 - 0.5)
				c.draw_circle(at + hole, 1.0, Color(INK, alpha))
			if b.get("friendly", false) and b.shape == "ball":
				c.draw_arc(at, r + 2.5, 0, TAU, 18, Color(MINT, 0.9), 1)
			return true
		"pin":
			var up: Vector2 = Vector2(0, -1).rotated(turn)
			var side: Vector2 = Vector2(1, 0).rotated(turn)
			var body: PackedVector2Array = []
			var profile: Array[Vector2] = [Vector2(0, -7), Vector2(1.6, -5.5), Vector2(1.2, -3), Vector2(3, 1), Vector2(2.6, 5), Vector2(1.6, 7)]
			for p: Vector2 in profile: body.append(at + side * p.x - up * p.y)
			for i: int in range(profile.size() - 1, -1, -1): body.append(at - side * profile[i].x - up * profile[i].y)
			c.draw_colored_polygon(body, Color(Color("f2ede0"), alpha))
			c.draw_line(at + up * 3.2 - side * 1.3, at + up * 3.2 + side * 1.3, Color(PIN_RED, alpha), 1)
			c.draw_line(at + up * 2.0 - side * 1.6, at + up * 2.0 + side * 1.6, Color(PIN_RED, alpha), 1)
			return true
		"chip":
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(0, -3.5).rotated(turn), at + Vector2(3, 0).rotated(turn), at + Vector2(0, 3.5).rotated(turn), at + Vector2(-3, 0).rotated(turn)]), Color(Color("f2d38a"), alpha))
			return true
		"rake":
			var lit: bool = int(b.age) > int(b.arm)
			var q: PackedVector2Array = v.quad(at, float(b.w), float(b.h), turn)
			if not lit:
				var blink: float = 0.5 + 0.5 * sin(float(b.age) * 0.5)
				c.draw_polyline(q + PackedVector2Array([q[0]]), Color(ROSE, 0.4 + 0.5 * blink), 1)
				return true
			c.draw_colored_polygon(q, Color(WOOD, alpha))
			c.draw_line(q[0], q[1], Color(AMBER, alpha), 1)
			return true
	return false
