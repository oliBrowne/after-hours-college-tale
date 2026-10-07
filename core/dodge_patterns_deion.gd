extends RefCounted
## COACH PRIME / Hurdle Run: Deion's track and field drills. The soul is blue
## and pinned at a fixed x (RUN_X), so every attack is beatable with jump
## (confirm or up; hold up for a little more height) and duck (precision while
## grounded) alone, which is all a pointer player has here. The box may turn
## and gravity may flip; obstacles always come from the runner's front.
## Promise: clear two obstacles without touching them (runnerCleared >= 2) and
## grab the relay flag a teammate holds out above you (touch; it needs a jump).
## Five handmade attacks, one per turn, cycling. Stage 1 and 2 add a layer.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["hurdle_drill", "agility_ladder", "switch_sides", "whistle_rings", "punt_return"]
const PHASES: Array[int] = [0, 1, 2]
const RUN_X: float = -70.0
const FLAG_RISE: float = 27.0
const FLAG_WINDOWS: Array = [[80, 210], [270, 400]]
const BEAT: int = 30
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const ROSE: Color = Color("e8837b")
const LILAC: Color = Color("a68db8")
const GOLD: Color = Color("cfb87c")
const TRACK: Color = Color("c28b65")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 480
	s.runnerCleared = 0
	s.duckable = true
	s.queue = []
	s.flagObj = -1
	s.mate = {"x": 200.0, "state": "away"}
	s.whistleAt = -100
	s.scroll = 0.0
	s.speed = 3.0
	match id:
		"hurdle_drill":
			s.phaseName = "Hurdle Drill"
			s.hint = "Jump the hurdles, duck the bars. Arrows on the right show what's next."
		"agility_ladder":
			s.phaseName = "Agility Ladder"
			s.hint = "Hop the cones on the beat. In the tunnel, duck the pads and keep hopping."
		"switch_sides":
			s.phaseName = "Switch Sides"
			s.hint = "Coach flips the field. Your jump and duck stay the same; the floor moves."
		"whistle_rings":
			s.phaseName = "Whistle Blasts"
			s.hint = "Each whistle ring has a gap. Be on the ground or in the air as it passes."
		"punt_return":
			s.phaseName = "Punt Return"
			s.hint = "Footballs bounce oddly. Jump the low ones, stand under the high ones."
	D.set_mode(s, "blue")
	s.soul.x = RUN_X
	s.soul.y = D.half(s).y - 4.0
	s.flagObj = -1

# ---------------------------------------------------------------- frame of reference

## +1 when the runner's floor is the box bottom, -1 when gravity points up.
static func _gs(s: Dictionary) -> float:
	return 1.0 if Vector2(s.soul.gravity).y >= 0.0 else -1.0

## Box-space y of the floor edge and of the soul's centre when standing.
static func _floor(s: Dictionary) -> float:
	return _gs(s) * D.half(s).y

static func _ground(s: Dictionary) -> float:
	return _gs(s) * (D.half(s).y - 4.0)

static func _pin(s: Dictionary) -> void:
	s.soul.x = RUN_X

## Box-space x where obstacles enter (just past the runner's front wall).
static func _entry(s: Dictionary) -> float:
	return D.half(s).x + 14.0

# ---------------------------------------------------------------- obstacles

static func _queue(s: Dictionary, at: int, props: Dictionary) -> void:
	s.queue.append({"at": at, "props": props})

static func _run_queue(s: Dictionary, t: int) -> void:
	var keep: Array = []
	for q: Dictionary in s.queue:
		if int(q.at) <= t:
			var props: Dictionary = q.props
			if props.has("kind_build"):
				_build(s, props)
			else:
				D.shot(s, props)
		else: keep.append(q)
	s.queue = keep

## Plan an obstacle that reaches the runner exactly at tick arrive (attack time).
## kind: hurdle, cone, bar, sled. It is built when it spawns, using the floor
## side at that moment, and its arrow tell shows 30 ticks before it enters.
static func _plan(s: Dictionary, t: int, kind: String, arrive: int, speed: float = -1.0) -> void:
	if speed <= 0.0: speed = float(s.speed)
	var travel: int = int(ceil((_entry(s) - RUN_X) / speed))
	var spawn: int = maxi(t, arrive - travel)
	var tell: int = maxi(t, spawn - 30)
	_queue(s, tell, {"kind_build": "tell", "kind": kind, "life": spawn - tell})
	_queue(s, spawn, {"kind_build": "obstacle", "kind": kind, "speed": speed, "arrive": arrive, "travel": travel})

static func _build(s: Dictionary, p: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	var gs: float = _gs(s)
	var kind: String = str(p.kind)
	if p.kind_build == "tell":
		if int(p.life) <= 0: return
		var y: float = _ground(s) if kind in ["hurdle", "cone", "sled"] else _ground(s) - gs * 22.0
		D.warn(s, {"kind": "edge", "space": "box", "x": h.x - 3.0, "y": y, "dir": Vector2.LEFT}, int(p.life), true)
		if kind == "bar": D.warn(s, {"kind": "edge", "space": "box", "x": h.x - 3.0, "y": y - gs * 14.0, "dir": Vector2.LEFT}, int(p.life))
		s.whistleAt = int(s.clock)
		return
	var speed: float = float(p.speed)
	var x: float = _entry(s)
	var b: Dictionary = {"space": "box", "x": x, "vx": -speed, "collide": "rect", "obstacle": true, "life": 400, "shape": kind}
	match kind:
		"hurdle":
			b.w = 4.0; b.h = 7.0; b.y = gs * (h.y - 7.0)
		"cone":
			b.w = 3.5; b.h = 5.0; b.y = gs * (h.y - 5.0)
		"sled":
			b.w = 6.0; b.h = 9.0; b.y = gs * (h.y - 9.0)
		"bar":
			# Hangs from the ceiling down to just above a ducking runner.
			b.w = 4.0; b.h = h.y - 2.5; b.y = -gs * 2.5
	D.shot(s, b)

## Obstacles cleared: anything flagged obstacle that gets past the runner
## without ever touching the soul (hit or not, invulnerable or not).
static func _track_obstacles(s: Dictionary) -> void:
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	if bool(s.soul.ducking): soul += Vector2(s.soul.gravity) * 3.0
	for b: Dictionary in s.bullets:
		if not b.get("obstacle", false) or b.get("passed", false) or b.has("fade"): continue
		var gap: float = D.clearance(s, b, soul) + (1.5 if bool(s.soul.ducking) else 0.0)
		if gap <= 0.0 and int(b.age) > int(b.arm): b.touched = true
		var past: bool = false
		if b.collide == "ring":
			past = float(b.radius) > Vector2(float(b.x), float(b.y)).distance_to(soul) + float(b.thick) + 6.0
		else:
			past = float(b.x) + float(b.get("w", b.get("r", 4.0))) < RUN_X - 5.0
		if past:
			b.passed = true
			if not b.get("touched", false):
				s.runnerCleared = int(s.runnerCleared) + 1
				if bool(s.promised) and int(s.runnerCleared) <= 2:
					s.objectiveChanged = true
					D.effect(s, "kept", D.to_world(s, soul + Vector2(0, -_gs(s) * 10.0)), 20)

# ---------------------------------------------------------------- the relay flag

static func _flag_point(s: Dictionary) -> Vector2:
	return Vector2(RUN_X, _ground(s) - _gs(s) * FLAG_RISE)

static func _flag(s: Dictionary, t: int) -> void:
	var o: Dictionary = {}
	if int(s.flagObj) >= 0: o = s.objectives[int(s.flagObj)]
	var done: bool = not o.is_empty() and o.done
	var open: bool = false
	for w: Array in FLAG_WINDOWS:
		if t >= int(w[0]) and t < int(w[1]): open = true
	var mate: Dictionary = s.mate
	var h: Vector2 = D.half(s)
	var target: float = RUN_X + 18.0
	if open and not done:
		mate.state = "running"
		mate.x = maxf(target, float(mate.x) - 4.0)
		if float(mate.x) <= target + 0.5:
			if o.is_empty():
				D.objective(s, {"kind": "touch", "x": RUN_X, "y": 0.0, "r": 8.0, "label": "FLAG"})
				s.flagObj = s.objectives.size() - 1
				o = s.objectives[int(s.flagObj)]
			o.active = true
	else:
		if not o.is_empty(): o.active = false
		if float(mate.x) < h.x + 40.0 and mate.state != "away":
			mate.x = float(mate.x) - 3.0
			if float(mate.x) < -h.x - 30.0: mate.state = "away"; mate.x = h.x + 40.0
		elif not done:
			# Next window: wait off-box to the right.
			for w: Array in FLAG_WINDOWS:
				if t >= int(w[0]) - 40 and t < int(w[0]):
					mate.state = "running"
					mate.x = minf(float(mate.x), h.x + 40.0)
	if not o.is_empty():
		var p: Vector2 = _flag_point(s)
		o.x = p.x; o.y = p.y

static func _flag_done(s: Dictionary) -> bool:
	return int(s.flagObj) >= 0 and bool(s.objectives[int(s.flagObj)].done)

# ---------------------------------------------------------------- contract

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return int(s.runnerCleared) >= 2 and _flag_done(s)

static func progress(s: Dictionary) -> String:
	return "Obstacles cleared %d/2 / flag %s" % [mini(2, int(s.runnerCleared)), "held" if _flag_done(s) else "open"]

static func tick(s: Dictionary, t: int) -> void:
	_pin(s)
	var phase: int = clampi(int(s.phase), 0, 2)
	s.scroll = float(s.scroll) + float(s.speed)
	match str(s.patternId):
		"hurdle_drill": _hurdles(s, t, phase)
		"agility_ladder": _ladder(s, t, phase)
		"switch_sides": _switch(s, t, phase)
		"whistle_rings": _rings(s, t, phase)
		"punt_return": _punts(s, t, phase)
	_run_queue(s, t)
	_flag(s, t)
	# QA autopilot hint: stay on the ground unless the flag is up for grabs.
	var flag_up: bool = int(s.flagObj) >= 0 and bool(s.objectives[int(s.flagObj)].active) and not _flag_done(s)
	s.botGoal = null if flag_up else Vector2(RUN_X, _ground(s))

static func after(s: Dictionary, _t: int) -> void:
	if str(s.soul.mode) == "blue": _pin(s)
	_track_obstacles(s)
	_bounces(s)

# ---------------------------------------------------------------- 1. Hurdle Drill

# Hurdles (jump) and hanging bars (duck) arrive on the beat; an arrow at the
# right wall shows each one's height before it enters. Stage 1 adds combos:
# double hurdles one jump clears, and a bar right after a hurdle (land, then
# duck). Stage 2 adds medicine balls that bounce in: jump them when low,
# stay put when they bounce high.
static func _hurdles(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 92.0}, 20)
		s.speed = 3.0 + phase * 0.2
	if t % BEAT != 0 or t < 30 or t > 330: return
	var beat: int = int(t / BEAT)
	var arrive: int = t + 70
	var roll: float = D.rand(s)
	if phase >= 2 and beat % 4 == 2:
		_medicine(s, t, arrive)
		return
	if beat % 5 == 4: return
	if phase >= 1 and roll < 0.3 and beat % 2 == 1:
		_plan(s, t, "hurdle", arrive)
		_plan(s, t, "hurdle", arrive + 10)
		D.banner(s, "DOUBLE", 30)
	elif phase >= 1 and roll < 0.55 and beat % 2 == 0:
		_plan(s, t, "hurdle", arrive)
		_plan(s, t, "bar", arrive + 30)
	else:
		_plan(s, t, "bar" if roll > 0.62 else "hurdle", arrive)

## A medicine ball hops toward the runner with a steady bounce, timed so it
## reaches the runner at the top of a hop (stay down) or right as it lands
## (jump it).
static func _medicine(s: Dictionary, t: int, arrive: int) -> void:
	var high: bool = D.rand(s) < 0.5
	var gs: float = _gs(s)
	var speed: float = 2.2
	var r: float = 5.0
	var g: float = 0.16
	var travel: float = (_entry(s) - RUN_X) / speed
	var period: float = travel / (1.5 if high else 2.0)
	var hop: float = g * period * 0.5
	var spawn: int = arrive - int(round(travel))
	_queue(s, maxi(t, spawn), {"space": "box", "x": _entry(s), "y": gs * (D.half(s).y - r), "vx": -speed, "vy": -gs * hop, "ay": gs * g, "r": r,
		"shape": "medicine", "obstacle": true, "life": 300, "hop": hop, "spin": -0.1})

## Keeps medicine balls and footballs bouncing (either floor), with each
## football's own sequence of restitutions.
static func _bounces(s: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	for b: Dictionary in s.bullets:
		if b.shape != "medicine" and b.shape != "football": continue
		var gs: float = 1.0 if float(b.ay) >= 0.0 else -1.0
		var floor_c: float = gs * (h.y - float(b.r))
		if (gs > 0.0 and float(b.y) >= floor_c and float(b.vy) > 0.0) or (gs < 0.0 and float(b.y) <= floor_c and float(b.vy) < 0.0):
			b.y = floor_c
			if b.shape == "medicine":
				b.vy = -gs * float(b.hop)
			else:
				var seq: Array = b.get("seq", [0.6])
				var i: int = int(b.get("bounced", 0))
				b.vy = -float(b.vy) * float(seq[mini(i, seq.size() - 1)])
				b.bounced = i + 1
				b.spin = -float(b.spin) * 1.3

# ---------------------------------------------------------------- 2. Agility Ladder

# Cones on every beat: hop, hop, hop. Midway the ceiling drops into a tunnel
# where hanging tackle pads (duck) alternate with cones. Stage 1: some beats
# hold two quick cones one jump clears. Stage 2: the drill field tilts.
static func _ladder(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 96.0}, 20)
		s.speed = 3.2
	if t == 170:
		D.banner(s, "TUNNEL", 50)
		D.warn(s, {"kind": "flip"}, 40, true)
		D.box_to(s, {"h": 60.0, "cy": 78.0}, 36, 10)
	if t == 330:
		D.banner(s, "OPEN FIELD", 40)
		D.box_to(s, {"h": 96.0, "cy": 60.0}, 30)
	if phase >= 2:
		if t == 90: D.box_to(s, {"rot": -0.16}, 40)
		if t == 250: D.box_to(s, {"rot": 0.16}, 50)
		if t == 400: D.box_to(s, {"rot": 0.0}, 30)
	if t % BEAT != 0 or t < 30 or t > 350: return
	var beat: int = int(t / BEAT)
	var arrive: int = t + 70
	var tunnel: bool = arrive >= 220 and arrive < 340
	if arrive > 205 and arrive < 222: return
	if tunnel:
		if beat % 2 == 0: _plan(s, t, "bar", arrive)
		else: _plan(s, t, "cone", arrive)
	else:
		if beat % 6 == 5: return
		_plan(s, t, "cone", arrive)
		if phase >= 1 and beat % 3 == 1: _plan(s, t, "cone", arrive + 12)

# ---------------------------------------------------------------- 3. Switch Sides

# A mixed drill, and then Coach flips the field: the box turns upside down
# (stage 0), gravity flips the runner to the other floor (stage 1), or both,
# one after the other (stage 2). Obstacles always form on your floor.
static func _switch(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 220.0, "h": 96.0}, 20)
		s.speed = 3.0
	var turn_at: int = 200 if phase != 2 else 150
	var flip_at: int = 320 if phase >= 1 else -1
	if phase == 1: turn_at = -1
	if phase == 1: flip_at = 210
	if phase == 2: flip_at = 320
	if turn_at > 0:
		if t == turn_at - 50:
			D.banner(s, "SWITCH SIDES", 50)
			D.warn(s, {"kind": "flip"}, 50, true)
		if t == turn_at:
			# A card flip: the box narrows while it turns so it never towers.
			D.box_to(s, {"rot": float(s.box.rot) + PI}, 40)
			D.box_to(s, {"w": 110.0}, 20, 0, "out")
			D.box_to(s, {"w": 220.0}, 20, 20, "in")
	if flip_at > 0:
		if t == flip_at - 50:
			D.banner(s, "GRAVITY CHECK", 50)
			D.warn(s, {"kind": "flip"}, 50, true)
		if t == flip_at:
			s.soul.gravity = -Vector2(s.soul.gravity)
			s.soul.grounded = false
			D.effect(s, "mode", D.soul_world(s), 24)
	if t % 20 != 0 or t < 30 or t > 380: return
	var arrive: int = t + 66
	# The turn is only a change of view (everything lives in box space), so the
	# drill goes on through it. Around a gravity flip nothing may be in flight:
	# obstacles are built on the floor that exists when they spawn.
	if flip_at > 0 and arrive > flip_at - 12 and t < flip_at + 10: return
	if turn_at > 0 and arrive > turn_at - 8 and arrive < turn_at + 10: return
	var step: int = int(t / 20)
	if step % 3 == 2: return
	var roll: float = D.rand(s)
	var kind: String = "bar" if roll < 0.35 else "sled" if roll < 0.55 else "cone" if roll < 0.7 else "hurdle"
	_plan(s, t, kind, arrive)

# ---------------------------------------------------------------- 4. Whistle Blasts

# The whistle beside the box blows a ring per beat. Each ring's gap is aimed at
# the ground (stay down) or at jump height (be in the air as it passes). Rings
# count as obstacles. Stage 1: the gap drifts as the ring grows, so read where
# it will be. Stage 2: bars come between two ground rings.
static func _rings(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 100.0}, 20)
		s.speed = 3.0
	var h: Vector2 = D.half(s)
	var source: Vector2 = Vector2(h.x + 40.0, h.y - 22.0)
	s.whistle = source
	if t % BEAT != 0 or t < 20 or t > 330: return
	var beat: int = int(t / BEAT)
	var high: bool = beat % 3 == 1 or (beat % 5 == 3)
	var target: Vector2 = Vector2(RUN_X, _ground(s) - (24.0 if high else 1.0))
	var grow: float = 2.4
	var dist: float = source.distance_to(target)
	var aim: float = (target - source).angle()
	var spin: float = 0.0
	if phase >= 1 and beat % 2 == 0:
		# Starts off target and drifts onto it by the time it arrives.
		spin = (0.0016 if D.rand(s) < 0.5 else -0.0016)
	var ticks: float = dist / grow
	var start_gap: float = aim - spin * ticks
	D.shot(s, {"space": "box", "x": source.x, "y": source.y, "collide": "ring", "radius": 4.0, "grow": grow, "thick": 2.0, "gap": start_gap,
		"gapWidth": 24.0 / dist, "gapSpin": spin, "shape": "whistle_ring", "maxRadius": dist + 60.0, "obstacle": true, "high": high})
	s.whistleAt = int(s.clock)
	if phase >= 2 and not high and (beat + 1) % 3 != 1 and beat % 2 == 0:
		_plan(s, t, "bar", t + int(ticks) + 15)

# ---------------------------------------------------------------- 5. Punt Return

# Footballs are punted in from upfield and bounce oddly (each bounce has its
# own spring). Each punt is planned so it reaches the runner either skimming
# low (jump) or high (stay down). A shadow on the floor tracks every ball.
# Tackling sleds slide in between. Stage 1: punts come in pairs. Stage 2:
# onside kicks roll along the ground.
static func _punts(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 100.0}, 20)
		s.speed = 2.6
	if t >= 30 and t <= 330 and t % 60 == 30:
		_punt(s, t, t + 80, D.rand(s) < 0.5)
		if phase >= 1 and int(t / 60) % 2 == 1: _punt(s, t, t + 110, D.rand(s) < 0.5)
		D.banner(s, "PUNT", 24)
	if t >= 60 and t <= 340 and t % 60 == 0 and int(t / 60) % 2 == 0:
		_plan(s, t, "sled", t + 66)
	if phase >= 2 and t % 120 == 90 and t < 340:
		_queue(s, t + 20, {"space": "box", "x": _entry(s), "y": _gs(s) * (D.half(s).y - 4.0), "vx": -3.6, "r": 4.0, "shape": "football", "spin": -0.3, "obstacle": true, "life": 200})
		D.warn(s, {"kind": "edge", "space": "box", "x": D.half(s).x - 3.0, "y": _ground(s), "dir": Vector2.LEFT}, 20, true)

## Search a few launch parameters by simulating the ball (same integration as
## the engine) until one reaches the runner in the wanted state: low (within
## 3 px of the floor: jump it) or high (40+ px up: stay down).
static func _punt(s: Dictionary, t: int, arrive: int, low: bool) -> void:
	var h: Vector2 = D.half(s)
	var r: float = 4.0
	var g: float = 0.12
	var floor_c: float = h.y - r
	var x0: float = h.x + 20.0
	var y0: float = -h.y - 30.0
	for attempt: int in range(32):
		var seq: Array = [0.45 + D.rand(s) * 0.4, 0.3 + D.rand(s) * 0.5, 0.5, 0.5]
		var travel: int = 70 + int(D.rand(s) * 40.0)
		var vx: float = -(x0 - RUN_X) / float(travel)
		var vy_init: float = D.rand_range(s, -1.5, 0.8)
		var x: float = x0; var y: float = y0; var vy: float = vy_init; var bounced: int = 0
		var at_runner: float = INF
		var ticks: int = 0
		for k: int in range(240):
			vy += g
			x += vx; y += vy
			ticks += 1
			if y >= floor_c and vy > 0.0:
				y = floor_c; vy = -vy * float(seq[mini(bounced, seq.size() - 1)]); bounced += 1
			if x <= RUN_X:
				at_runner = floor_c - y
				break
		if bounced == 0: continue
		if (low and at_runner <= 3.0) or (not low and at_runner >= 40.0):
			var spawn: int = arrive - ticks
			_queue(s, maxi(t, spawn), {"space": "box", "x": x0, "y": y0, "vx": vx, "vy": vy_init, "ay": g, "r": r, "shape": "football", "rot": 0.0, "spin": 0.2,
				"obstacle": true, "life": 400, "seq": seq, "low": low})
			return

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var gs: float = _gs(s)
	var fl: float = _floor(s)
	# Track: a lane line near the floor and scrolling hash marks.
	c.draw_line(v.box_point(Vector2(-h.x, fl - gs * 1.0)), v.box_point(Vector2(h.x, fl - gs * 1.0)), Color(TRACK, 0.9), 2)
	var off: float = fposmod(float(s.scroll), 40.0)
	var x: float = -h.x - off + 40.0
	while x < h.x:
		c.draw_line(v.box_point(Vector2(x, fl - gs * 2.0)), v.box_point(Vector2(x - 6.0, fl - gs * 2.0)), Color(CREAM, 0.35), 1)
		c.draw_line(v.box_point(Vector2(x * 0.7, -fl * 0.2)), v.box_point(Vector2(x * 0.7 - 10.0, -fl * 0.2)), Color(CREAM, 0.05), 1)
		x += 40.0
	# The runner's mark.
	c.draw_line(v.box_point(Vector2(RUN_X - 8.0, fl - gs * 1.0)), v.box_point(Vector2(RUN_X + 8.0, fl - gs * 1.0)), Color(GOLD, 0.6), 3)
	# Shadows under footballs and medicine balls.
	for b: Dictionary in s.bullets:
		if b.shape in ["football", "medicine"]:
			var bx: float = float(b.x)
			var height: float = absf(fl - float(b.y))
			var w: float = clampf(8.0 - height * 0.06, 3.0, 8.0)
			c.draw_line(v.box_point(Vector2(bx - w, fl - gs * 1.5)), v.box_point(Vector2(bx + w, fl - gs * 1.5)), Color(0, 0, 0, 0.55), 2)
	# The teammate with the relay flag.
	var mate: Dictionary = s.mate
	if str(mate.state) != "away":
		var mx: float = float(mate.x)
		var step: float = sin(float(s.clock) * 0.5) * 3.0
		var feet: Vector2 = v.box_point(Vector2(mx, fl))
		var up: Vector2 = Vector2(0, -gs).rotated(float(s.box.rot))
		var side: Vector2 = Vector2(-up.y, up.x)
		var hip: Vector2 = feet + up * 9.0
		c.draw_line(hip, feet + side * step, Color(LILAC, 0.9), 2)
		c.draw_line(hip, feet - side * step, Color(LILAC, 0.9), 2)
		c.draw_line(hip, hip + up * 8.0, Color(LILAC, 0.9), 3)
		c.draw_circle(hip + up * 11.0, 3.0, Color(LILAC, 0.9))
		var hold: bool = int(s.flagObj) >= 0 and bool(s.objectives[int(s.flagObj)].active) and not bool(s.objectives[int(s.flagObj)].done)
		var flag_at: Vector2 = v.box_point(_flag_point(s)) if hold else hip + up * 18.0 + side * 4.0
		c.draw_line(hip + up * 7.0, flag_at, Color(CREAM, 0.8), 1)
		if not _flag_done(s):
			c.draw_colored_polygon(PackedVector2Array([flag_at, flag_at + side * 7.0 + up * 2.0, flag_at + up * 4.0]), GOLD)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var toot: bool = int(s.clock) - int(s.whistleAt) < 10
	if s.patternId == "whistle_rings" and s.has("whistle"):
		var w: Vector2 = v.box_point(Vector2(s.whistle))
		c.draw_rect(Rect2(w + Vector2(-9, -4), Vector2(14, 8)), Color("c9a640"))
		c.draw_circle(w + Vector2(5, 0), 5.0, Color("c9a640"))
		c.draw_circle(w + Vector2(5, 0), 2.0, Color("3a3020"))
		c.draw_line(w + Vector2(-9, 0), w + Vector2(-16, 4), Color(CREAM, 0.7), 1)
		if toot:
			for i: int in range(3):
				c.draw_arc(w + Vector2(-12, 0), 6.0 + i * 4.0, PI * 0.75, PI * 1.25, 6, Color(CREAM, 0.7 - i * 0.2), 1)
	else:
		# Coach's whistle on the runner's front wall.
		var gs: float = _gs(s)
		var w2: Vector2 = v.box_point(Vector2(h.x + 12.0, -gs * (h.y - 10.0)))
		c.draw_rect(Rect2(w2 + Vector2(-5, -3), Vector2(9, 6)), Color("c9a640"))
		c.draw_circle(w2 + Vector2(4, 0), 3.5, Color("c9a640"))
		if toot:
			c.draw_arc(w2 + Vector2(-8, 0), 5.0, PI * 0.7, PI * 1.3, 6, Color(CREAM, 0.8), 1)
			c.draw_arc(w2 + Vector2(-8, 0), 9.0, PI * 0.7, PI * 1.3, 6, Color(CREAM, 0.5), 1)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	var down: Vector2 = Vector2(0, 1).rotated(turn)
	var side: Vector2 = Vector2(1, 0).rotated(turn)
	match str(b.shape):
		"hurdle", "cone", "sled":
			var hw: float = float(b.w); var hh: float = float(b.h)
			# Which way is the floor for this obstacle? Toward its far edge.
			var gs: float = 1.0 if float(b.y) > 0.0 else -1.0
			var top: Vector2 = at - down * hh * gs
			var base: Vector2 = at + down * hh * gs
			if b.shape == "hurdle":
				c.draw_line(top - side * hw, base - side * hw, Color(CREAM, alpha), 1)
				c.draw_line(top + side * hw, base + side * hw, Color(CREAM, alpha), 1)
				c.draw_line(top - side * (hw + 1.0), top + side * (hw + 1.0), Color(ROSE, alpha), 3)
				c.draw_line(top + down * gs * 3.0 - side * hw, top + down * gs * 3.0 + side * hw, Color(CREAM, alpha), 1)
			elif b.shape == "cone":
				c.draw_colored_polygon(PackedVector2Array([top, base + side * (hw + 1.0), base - side * (hw + 1.0)]), Color(Color("e8873b"), alpha))
				c.draw_line(at - side * (hw * 0.6), at + side * (hw * 0.6), Color(CREAM, alpha), 1)
			else:
				c.draw_colored_polygon(v.quad(at, hw, hh, turn), Color(Color("3a3448"), alpha))
				c.draw_rect(Rect2(at - Vector2(hw, hh), Vector2(hw, hh) * 2.0), Color(GOLD, alpha), false, 1) if absf(turn) < 0.01 else c.draw_polyline(v.quad(at, hw, hh, turn) + PackedVector2Array([v.quad(at, hw, hh, turn)[0]]), Color(GOLD, alpha), 1)
				c.draw_line(top + down * gs * 3.0 - side * hw, top + down * gs * 3.0 + side * hw, Color(GOLD, alpha), 1)
			return true
		"bar":
			var hw2: float = float(b.w); var hh2: float = float(b.h)
			var gs2: float = 1.0 if float(b.y) < 0.0 else -1.0
			var tip: Vector2 = at + down * hh2 * gs2
			var root: Vector2 = at - down * hh2 * gs2
			c.draw_line(root, tip - down * gs2 * 6.0, Color(Color("6b6478"), alpha), 2)
			c.draw_colored_polygon(v.quad(tip - down * gs2 * 4.0, hw2 + 2.0, 4.0, turn), Color(ROSE, alpha))
			c.draw_line(tip - side * (hw2 + 2.0), tip + side * (hw2 + 2.0), Color(CREAM, alpha), 1)
			return true
		"medicine":
			c.draw_circle(at, float(b.r), Color(Color("7a5a3a"), alpha))
			c.draw_arc(at, float(b.r), turn, turn + PI, 8, Color(GOLD, alpha), 1)
			c.draw_line(at - side * float(b.r), at + side * float(b.r), Color(Color("3a2a1a"), alpha), 1)
			return true
		"football":
			var r: float = float(b.r)
			var pts: PackedVector2Array = []
			for i: int in range(10):
				var a: float = i * TAU / 10.0
				pts.append(at + Vector2(cos(a) * r * 1.5, sin(a) * r * 0.9).rotated(turn))
			c.draw_colored_polygon(pts, Color(Color("8a4a2a"), alpha))
			c.draw_line(at - side * r * 0.6, at + side * r * 0.6, Color(CREAM, alpha), 1)
			return true
		"whistle_ring":
			var gw: float = float(b.gapWidth) * 0.5
			var rot: float = turn - float(b.rot)
			var col: Color = Color(Color("f2e3b0"), 0.95 * alpha)
			c.draw_arc(at, float(b.radius), float(b.gap) + rot + gw, float(b.gap) + rot + TAU - gw, maxi(32, int(float(b.radius) * 0.7)), col, 3.0)
			# Mark the gap's edges so it reads at a glance.
			for e: float in [float(b.gap) + rot + gw, float(b.gap) + rot - gw]:
				var p: Vector2 = at + Vector2.from_angle(e) * float(b.radius)
				c.draw_circle(p, 2.5, Color(AMBER, alpha))
			return true
	return false
