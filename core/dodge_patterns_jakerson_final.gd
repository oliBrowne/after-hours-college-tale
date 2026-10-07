extends RefCounted
## JAKERSON / the friendly rematch after graduation. A victory lap that plays
## like a final exam: each of the five attacks remixes one mechanic the player
## learned on the way (falling code, the blue soul's lob, beat-synced cues,
## Walt's shelter, Chip's lanes), one per turn, cycling in order.
## The promise: three diploma signatures (mint boxes) show up one after another;
## stand in each and press confirm while promised. Every signature waits for as
## long as it takes and sits where the attack's soul mode can reach it.
## Phase 1 (from the second turn) adds a layer to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["commit_storm", "lob_rally", "on_the_beat", "shelter_drill", "loading_lanes"]
const PHASES: Array[int] = [0, 1]
const SIGNATURES: int = 3
## Holding left / right in lanes mode hops again after this many ticks.
const REPEAT: int = 14

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const BLUE: Color = Color("8fb3ea")
const LILAC: Color = Color("a68db8")
const ROSE: Color = Color("e8837b")
const BALL: Color = Color("d8e86a")
const GOLD: Color = Color("cfb87c")
const GLYPHS: Array[String] = ["0", "1", "{", "}", ";", "(", ")", "#", "=", "&"]

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	var phase: int = clampi(int(s.phase), 0, 1)
	s.patternId = id
	s.length = 480 + 40 * phase
	s.signSpots = [Vector2(-0.6, 0.45), Vector2(0.6, -0.4), Vector2(0.0, 0.5)]
	s.boxW = 224.0
	s.queue = []
	s.reticles = []
	s.walls = []
	s.pocket = {}
	s.bars = []
	s.lastGap = -1
	s.rally = 0
	s.botGoal = null
	match id:
		"commit_storm":
			s.phaseName = "Commit Storm"
			s.hint = "Code falls two columns at a time; red bands warn first. Sign each diploma: stand in it, Z."
			s.signSpots = [Vector2(-0.6, 0.5), Vector2(0.55, -0.45), Vector2(0.05, 0.55)]
		"lob_rally":
			s.phaseName = "Lob Rally"
			s.hint = "Blue soul: up or Z jumps, like a lob. Hop the low balls, step off the marks. Sign mid-air."
			s.signSpots = [Vector2(0.5, 0), Vector2(-0.55, 0), Vector2(0.2 if phase == 0 else 0.55, 0)]
			# Start on your side of the court (left of the phase 1 net).
			s.soul.x = -60.0
			D.set_mode(s, "blue")
		"on_the_beat":
			s.phaseName = "On the Beat"
			s.hint = "Serves land on the beat: leave each shrinking ring. In the racket on a beat, you return it."
			s.signSpots = [Vector2(0.55, -0.45), Vector2(-0.6, 0.4), Vector2(0.1, 0.5)]
		"shelter_drill":
			s.phaseName = "Shelter Drill"
			s.hint = "Caps sweep across: ride the lit shelter, nothing hits you in it. Sign between the drills."
			s.signSpots = [Vector2(-0.65, 0.55), Vector2(0.65, -0.55), Vector2(-0.1, -0.6)]
		"loading_lanes":
			s.phaseName = "Loading Lanes"
			s.hint = "Hop to the gap in each loading bar. Packets drop down red lanes. Sign in a lane with Z."
			s.boxW = 216.0
			s.lanes = [-88.0, -44.0, 0.0, 44.0, 88.0]
			s.laneY = 40.0
			s.soul.x = 0.0
			D.set_mode(s, "lanes")
	for i: int in range(SIGNATURES):
		D.objective(s, {"kind": "confirm", "r": 13.0, "label": "sign", "active": false, "x": 0.0, "y": 0.0, "lane": -1})
	if id == "lob_rally":
		# Signatures hang at jump height: a tall box you pass through mid-jump.
		for o: Dictionary in s.objectives:
			o.w = 12.0; o.h = 15.0

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return _signed(s) >= SIGNATURES

static func progress(s: Dictionary) -> String:
	return "Signatures %d/%d" % [_signed(s), SIGNATURES]

static func _signed(s: Dictionary) -> int:
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	return count

static func _b(s: Dictionary) -> int:
	return int(s.get("beatTicks", 30))

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	match str(s.patternId):
		"commit_storm": _commit_storm(s, t, phase)
		"lob_rally": _lob_rally(s, t, phase)
		"on_the_beat": _on_the_beat(s, t, phase)
		"shelter_drill": _shelter_drill(s, t, phase)
		"loading_lanes": _loading_lanes(s, t, phase)
	_run_queue(s, t)
	_signatures(s, t)

static func after(s: Dictionary, _t: int) -> void:
	if s.patternId == "lob_rally" and int(s.phase) >= 1:
		_net_cord(s)

# ---------------------------------------------------------------- signatures

## One signature at a time: the next appears 24 ticks after the last was signed
## and no earlier than tick 40 + 100 per signature (On the Beat: on a beat).
static func _signatures(s: Dictionary, t: int) -> void:
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		# Spread over the attack like an exam: never before tick 40 + 100 per signature.
		var ready: bool = t >= 40 + 100 * i and (i == 0 or (last_done >= 0 and int(s.clock) - last_done >= 24))
		if ready and not bool(o.get("shown", false)) and s.patternId == "on_the_beat" and t % _b(s) != 0:
			ready = false
		# Shelter Drill: wait until some spot is clear of the walls for a while.
		if ready and not bool(o.get("shown", false)) and s.patternId == "shelter_drill" and _shelter_spot(s) == Vector2.INF:
			ready = false
		if ready and not bool(o.get("shown", false)):
			o.shown = true
			if s.patternId == "loading_lanes": o.lane = _signature_lane(s)
			if s.patternId == "shelter_drill": s.signSpots[i] = _shelter_spot(s)
			_follow_signature(s, o, i)
			D.effect(s, "pulse", D.to_world(s, Vector2(float(o.x), float(o.y))), 18)
		if bool(o.get("shown", false)): _follow_signature(s, o, i)
		o.active = ready
		return

static func _follow_signature(s: Dictionary, o: Dictionary, i: int) -> void:
	var h: Vector2 = D.half(s)
	var spot: Vector2 = s.signSpots[i]
	match str(s.patternId):
		"lob_rally":
			o.x = spot.x * h.x
			o.y = h.y - 4.0 - 26.0
		"loading_lanes":
			o.x = _lane_x(s, int(o.lane)); o.y = float(s.laneY)
		_:
			o.x = spot.x * h.x; o.y = spot.y * h.y

# ---------------------------------------------------------------- shared helpers

static func _queue(s: Dictionary, at: int, props: Dictionary) -> void:
	s.queue.append({"at": at, "props": props})

static func _run_queue(s: Dictionary, t: int) -> void:
	var keep: Array = []
	for q: Dictionary in s.queue:
		if int(q.at) <= t: D.shot(s, q.props)
		else: keep.append(q)
	s.queue = keep

static func _glyph(s: Dictionary) -> String:
	return GLYPHS[int(D.rand(s) * GLYPHS.size()) % GLYPHS.size()]

# ---------------------------------------------------------------- 1. Commit Storm

# Falling Code, remixed: two red columns at a time (one on you, one elsewhere),
# faster code, and the editor window refactors narrower and wider between
# volleys. Phase 1: merge-conflict rows of < and > slide across your row.
const SQUEEZES: Array = [[130, 150.0, "REFACTOR"], [270, 236.0, "SCOPE CREEP"], [390, 176.0, "REFACTOR"]]

static func _commit_storm(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
		s.boxW = 224.0
	for sq: Array in SQUEEZES:
		if t == int(sq[0]) - 30:
			var narrower: bool = float(sq[1]) < float(s.boxW)
			if narrower: D.warn(s, {"kind": "curtain"}, 30, true)
			D.banner(s, str(sq[2]), 40)
			D.box_to(s, {"w": float(sq[1])}, 30, 30)
			s.boxW = float(sq[1])
	var every: int = 40 if phase == 0 else 38
	if t % every == 6 and t >= 20 and t < int(s.length) - 100:
		var lim: float = float(s.boxW) * 0.5 - 12.0
		var a: float = clampf(float(s.soul.x) + D.rand_range(s, -3.0, 3.0), -lim, lim)
		var b: float = a
		for attempt: int in range(10):
			b = D.rand_range(s, -lim, lim)
			if absf(b - a) >= 40.0: break
		if absf(b - a) < 40.0: b = clampf(a + (40.0 if a < 0.0 else -40.0), -lim, lim)
		var speed: float = 1.7 + 0.15 * phase
		_code_column(s, a, speed, 34, int(t / every) % 2 == 0)
		_code_column(s, b, speed, 34, false)
	if phase >= 1 and t % 96 == 60 and t < int(s.length) - 120:
		var h: Vector2 = D.half(s)
		var y: float = clampf(float(s.soul.y), -h.y + 10.0, h.y - 10.0)
		var side: float = 1.0 if int(t / 96) % 2 == 0 else -1.0
		D.warn(s, {"kind": "lane", "y": D.centre(s).y + y, "h": 8.0, "horizontal": true}, 40, true)
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 4.0), "y": y, "dir": Vector2(-side, 0)}, 40)
		for i: int in range(6):
			D.shot(s, {"space": "box", "x": side * (h.x + 8.0 + i * 14.0), "y": y, "vx": -side * 2.2, "r": 4.0, "shape": "glyph",
				"glyph": "<" if side > 0.0 else ">", "conflict": true, "hold": true, "arm": 40, "life": 260})

static func _code_column(s: Dictionary, x: float, speed: float, warn_ticks: int, loud: bool) -> void:
	var h: Vector2 = D.half(s)
	D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 8.0, "horizontal": false}, warn_ticks, loud)
	for i: int in range(4):
		D.shot(s, {"space": "box", "x": x, "y": -h.y - 8.0 - i * 15.0, "vy": speed, "r": 4.0, "shape": "glyph", "glyph": _glyph(s),
			"hold": true, "arm": warn_ticks, "life": 240})

# ---------------------------------------------------------------- 2. Lob Rally

# The blue soul, explained as a lob: low skimmers bounce along the floor from
# either baseline (jump them) and soft lobs drop on a marked spot near you
# (step off the mark; the ball rolls on after it lands). Phase 1: a net rises
# in the middle, the signatures alternate sides so you have to lob yourself
# over it, and skimmers that clip the net cord pop up over it.
static func _lob_rally(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 100.0}, 24)
		D.banner(s, "LIKE A LOB", 50)
		if phase >= 1:
			D.shot(s, {"space": "box", "x": 0.0, "y": 50.0 - 9.0, "collide": "rect", "w": 2.5, "h": 9.0, "shape": "net", "hold": true, "arm": 60,
				"life": int(s.length) + 60})
	if phase >= 1 and t == 30: D.banner(s, "NET UP", 40)
	var every: int = 46 if phase == 0 else 44
	if t >= 30 and (t - 30) % every == 0 and t < int(s.length) - 110:
		var k: int = int((t - 30) / every)
		if k % 3 == 2: _lob(s, phase)
		else: _skimmer(s, 1.0 if k % 2 == 0 else -1.0, phase)

static func _skimmer(s: Dictionary, side: float, phase: int) -> void:
	var h: Vector2 = Vector2(112.0, 50.0)
	var speed: float = 1.7 + 0.1 * phase
	var warn_ticks: int = 34
	D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": h.y - 6.0, "dir": Vector2(-side, 0)}, warn_ticks, true)
	D.shot(s, {"space": "box", "x": side * (h.x + 6.0 + speed * warn_ticks), "y": h.y - 4.5, "vx": -side * speed, "vy": -1.6, "ay": 0.12, "bounce": 0.92,
		"r": 4.5, "shape": "tennis", "spin": -0.15 * side, "skim": true, "life": 330})

static func _lob(s: Dictionary, phase: int) -> void:
	var h: Vector2 = Vector2(112.0, 50.0)
	var tx: float = clampf(float(s.soul.x) + D.rand_range(s, -6.0, 6.0), -h.x + 14.0, h.x - 14.0)
	var ticks: float = 60.0
	var sx: float = tx + 70.0
	var sy: float = -h.y - 24.0
	var r: float = 5.0
	var ay: float = 0.09
	var vx: float = (tx - sx) / ticks
	var vy: float = (h.y - r - sy - 0.5 * ay * ticks * ticks) / ticks
	D.warn(s, {"kind": "landing", "space": "box", "x": tx, "y": h.y, "born": int(s.clock)}, int(ticks), true)
	D.shot(s, {"space": "box", "x": sx, "y": sy, "vx": vx, "vy": vy, "ay": ay, "bounce": 0.35, "r": r, "shape": "tennis", "lob": true, "spin": -0.1, "life": 320})
	if phase >= 1:
		# A second, shorter lob lands on the other side of the net.
		var tx2: float = clampf(-tx * 0.7 + D.rand_range(s, -10.0, 10.0), -h.x + 14.0, h.x - 14.0)
		if absf(tx2) < 24.0: tx2 = 40.0 if tx < 0.0 else -40.0
		var t2: float = 76.0
		var sx2: float = tx2 + 60.0
		var vx2: float = (tx2 - sx2) / t2
		var vy2: float = (h.y - r - sy - 0.5 * ay * t2 * t2) / t2
		D.warn(s, {"kind": "landing", "space": "box", "x": tx2, "y": h.y, "born": int(s.clock)}, int(t2))
		D.shot(s, {"space": "box", "x": sx2, "y": sy, "vx": vx2, "vy": vy2, "ay": ay, "bounce": 0.35, "r": r, "shape": "tennis", "lob": true, "spin": -0.1, "life": 320})

## Phase 1: a skimmer that reaches the net clips the cord and pops up over it.
static func _net_cord(s: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	for b: Dictionary in s.bullets:
		if not b.get("skim", false) or b.get("corded", false) or b.has("fade"): continue
		if signf(float(b.px)) != signf(float(b.x)) and float(b.y) > h.y - 24.0:
			b.corded = true
			b.vy = -3.0
			b.bounce = 0.5
			D.effect(s, "pulse", D.to_world(s, Vector2(float(b.x), float(b.y))), 14)

# ---------------------------------------------------------------- 3. On the Beat

# Beat-synced serves: every beat a reticle appears where a serve will land two
# beats later (alternately on you and near you); it shrinks to the beat and
# bursts. Every bar Jakerson's racket swings a ring with one gap. A racket face
# drifts around the court: be inside it on a beat and you return every serve
# landing near you on that beat. Phase 1: each landing kicks up four balls.
static func _on_the_beat(s: Dictionary, t: int, phase: int) -> void:
	var bt: int = _b(s)
	if t == 0: D.box_to(s, {"w": 208.0, "h": 112.0}, 24)
	if t % bt != 0: return
	var k: int = int(t / bt)
	var h: Vector2 = D.half(s)
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var in_racket: bool = soul.distance_to(_sweet(s, t)) <= 14.0
	if in_racket:
		s.rally = int(s.rally) + 1
		D.effect(s, "lantern", D.soul_world(s), 22)
	var keep: Array = []
	for r: Dictionary in s.reticles:
		if int(r.land) > t:
			keep.append(r); continue
		if int(r.land) < t: continue
		var at: Vector2 = Vector2(float(r.x), float(r.y))
		if in_racket and at.distance_to(soul) <= 40.0:
			# Returned: the ball goes back over to Jakerson.
			D.effect(s, "block", D.to_world(s, at), 16)
			D.shot(s, {"space": "box", "x": at.x, "y": at.y, "vx": 2.6, "vy": -2.2, "collide": "none", "friendly": true, "r": 3.5, "shape": "tennis", "spin": 0.2, "life": 70})
			continue
		D.shot(s, {"space": "box", "x": at.x, "y": at.y, "r": 11.0, "shape": "impact", "life": 8})
		D.effect(s, "pulse", D.to_world(s, at), 14)
		if phase >= 1:
			var base: float = k * 0.7
			for i: int in range(4):
				var a: float = base + i * PI * 0.5
				D.shot(s, {"space": "box", "x": at.x, "y": at.y, "vx": cos(a) * 1.05, "vy": sin(a) * 1.05, "r": 3.0, "shape": "tennis", "kick": true, "spin": 0.15, "life": 150})
	s.reticles = keep
	if in_racket:
		for b: Dictionary in s.bullets:
			if b.get("kick", false) and not b.get("friendly", false) and Vector2(float(b.x), float(b.y)).distance_to(soul) <= 40.0:
				b.friendly = true; b.fade = 20
	# Serve for two beats from now.
	if k >= 1 and t + 2 * bt < int(s.length) - 80:
		var target: Vector2 = soul + Vector2(D.rand_range(s, -4.0, 4.0), D.rand_range(s, -4.0, 4.0))
		if k % 2 == 1:
			var angle: float = D.rand_range(s, -PI, PI)
			target = soul + Vector2.from_angle(angle) * D.rand_range(s, 24.0, 46.0)
		target = Vector2(clampf(target.x, -h.x + 10.0, h.x - 10.0), clampf(target.y, -h.y + 10.0, h.y - 10.0))
		var land: int = t + 2 * bt
		s.reticles.append({"x": target.x, "y": target.y, "born": t, "land": land})
		var from: Vector2 = Vector2(h.x + 40.0, -h.y - 40.0)
		var ticks: float = float(2 * bt)
		var ay: float = 0.03
		D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": (target.x - from.x) / ticks, "vy": (target.y - from.y - 0.5 * ay * ticks * ticks) / ticks, "ay": ay,
			"collide": "none", "r": 3.0, "shape": "serve", "life": 2 * bt})
	# Every bar the racket swings a ring (one beat of wind-up).
	if k % 4 == 2 and t < int(s.length) - 120:
		var origin: Vector2 = D.centre(s) + Vector2(h.x + 8.0, -h.y - 8.0)
		D.warn(s, {"kind": "racket", "x": origin.x, "y": origin.y}, bt, true)
		var gap: float = (D.soul_world(s) - origin).angle() + D.rand_range(s, 0.25, 0.5) * (1.0 if D.rand(s) < 0.5 else -1.0)
		_queue(s, t + bt, {"x": origin.x, "y": origin.y, "collide": "ring", "radius": 6.0, "grow": 1.4, "thick": 2.0, "gap": gap, "gapWidth": 0.72,
			"shape": "ring", "maxRadius": 320.0})

## The racket face (box space): it drifts slowly around the court.
static func _sweet(s: Dictionary, t: int) -> Vector2:
	var h: Vector2 = D.half(s)
	return Vector2(sin(t * 0.013) * (h.x - 26.0), sin(t * 0.021 + 1.0) * (h.y - 22.0))

# ---------------------------------------------------------------- 4. Shelter Drill

# Walt's shelter, as a drill: a pocket lights up on the side a sweep of tossed
# mortarboards will come from (a solid wall, no gap) and drifts around. Inside
# the lit pocket nothing can hit you, and caps that reach it are caught. Once
# the wall has passed you, you are free again. Between drills, diploma scrolls
# drop on you down red lanes. Phase 1: pincer drills, walls from both sides at
# once, so you hold the drifting shelter until both have passed.
const DRILLS: Array[int] = [100, 250, 400]
const WALL_SPEED: float = 2.6
const POCKET: Vector2 = Vector2(20, 18)
const SHELTER_H: Vector2 = Vector2(112.0, 56.0)
const SHELTER_SPOTS: Array[Vector2] = [Vector2(-0.7, 0.55), Vector2(0.7, -0.55), Vector2(-0.7, -0.55), Vector2(0.7, 0.55),
	Vector2(0.0, -0.6), Vector2(0.0, 0.6), Vector2(-0.35, 0.0), Vector2(0.35, 0.0)]

static func _shelter_drill(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 224.0, "h": 112.0}, 24)
	var h: Vector2 = SHELTER_H
	for k: int in range(DRILLS.size()):
		var start: int = DRILLS[k] - (10 if phase >= 1 else 0)
		var side: float = 1.0 if k % 2 == 0 else -1.0
		if t == start - 60:
			var amp: float = 22.0 if phase == 0 else 30.0
			# Phase 0: on the side the wall comes from. Pincer: on your side.
			var toward: float = side
			if phase >= 1: toward = signf(float(s.soul.x)) if absf(float(s.soul.x)) > 10.0 else (1.0 if D.rand(s) < 0.5 else -1.0)
			var base_x: float = D.rand_range(s, 46.0, 64.0) * toward
			var walls: Array = [{"start": start, "side": side}]
			if phase >= 1: walls.append({"start": start, "side": -side})
			var until: int = start
			for w: Dictionary in walls:
				# The wall's trailing column clears the far edge of the pocket's drift.
				var near_u: float = base_x * float(w.side) - amp - POCKET.x
				until = maxi(until, start + int((h.x + 12.0 - near_u + 24.0) / WALL_SPEED))
				s.walls.append(w)
			s.pocket = {"born": t, "baseX": base_x, "phi": D.rand_range(s, 0.0, TAU), "ampX": amp, "until": until + 8}
			D.banner(s, "TAKE SHELTER" if phase == 0 else "PINCER DRILL", 50)
			D.effect(s, "lantern", D.to_world(s, _pocket_centre(s, t)), 30)
			_wall_warn(s, side, 60)
			if phase >= 1: _wall_warn(s, -side, 60)
		if t == start:
			_wall(s, side)
			if phase >= 1: _wall(s, -side)
	# The pocket: safe while lit. Caps pass through it harmlessly (drawn dim).
	var zone: Rect2 = Rect2()
	if not s.pocket.is_empty() and t <= int(s.pocket.until):
		var c: Vector2 = _pocket_centre(s, t)
		zone = Rect2(c - POCKET, POCKET * 2.0)
		s.safe = [zone]
	else:
		s.safe = []
		if not s.pocket.is_empty(): s.pocket = {}
	for b: Dictionary in s.bullets:
		if b.shape != "cap": continue
		var inside: bool = zone.has_area() and zone.grow(2.0).has_point(Vector2(float(b.x), float(b.y)))
		b.collide = "none" if inside else "circle"
		b.sheltered = inside
	# Scrolls between drills.
	var calm: bool = true
	for w: Dictionary in s.walls:
		if t >= int(w.start) - 40 and t <= int(w.start) + 60: calm = false
	if calm and t % 30 == 10 and t >= 20 and t < int(s.length) - 90:
		var x: float = clampf(float(s.soul.x) + D.rand_range(s, -4.0, 4.0), -h.x + 10.0, h.x - 10.0)
		D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 8.0, "horizontal": false}, 30)
		D.shot(s, {"space": "box", "x": x, "y": -h.y - 8.0, "vy": 2.2, "r": 4.5, "shape": "scroll", "hold": true, "arm": 30, "life": 200})
	_shelter_hint(s, t)

static func _pocket_centre(s: Dictionary, t: int) -> Vector2:
	var p: Dictionary = s.pocket
	var h: Vector2 = SHELTER_H
	var u: float = float(t - int(p.born))
	var x: float = float(p.baseX) + sin(u * 0.03 + float(p.phi)) * float(p.ampX)
	var y: float = sin(u * 0.045 + float(p.phi) * 1.7) * (h.y - 26.0)
	return Vector2(clampf(x, -h.x + 24.0, h.x - 24.0), y)

## Where a wall's lead column is, measured along its travel (u = x * side).
static func _wall_u(w: Dictionary, t: int) -> float:
	return SHELTER_H.x + 12.0 - WALL_SPEED * float(t - int(w.start))

static func _wall_warn(s: Dictionary, side: float, life: int) -> void:
	var h: Vector2 = SHELTER_H
	var first: bool = true
	for y: float in [-38.0, -13.0, 13.0, 38.0]:
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 4.0), "y": y, "dir": Vector2(-side, 0)}, life, first)
		first = false

static func _wall(s: Dictionary, side: float) -> void:
	var h: Vector2 = SHELTER_H
	for col: int in range(2):
		var y: float = -h.y + 5.0
		var i: int = 0
		while y <= h.y - 4.0:
			D.shot(s, {"space": "box", "x": side * (h.x + 12.0 + col * 12.0), "y": y, "vx": -side * WALL_SPEED, "r": 4.5, "shape": "cap",
				"rot": (i * 0.7 + col) * 0.5, "spin": 0.06 * side, "life": 200})
			y += 10.0; i += 1

## Pick the signature spot nearest the soul that no wall crosses soon.
static func _shelter_spot(s: Dictionary) -> Vector2:
	var t: int = int(s.clock) - int(s.leadIn)
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var best: Vector2 = Vector2.INF
	var best_score: float = 1000.0
	for spot: Vector2 in SHELTER_SPOTS:
		var at: Vector2 = spot * SHELTER_H
		var score: float = at.distance_to(soul)
		if score < 24.0: score += 60.0
		for w: Dictionary in s.walls:
			var until: float = (_wall_u(w, t) - at.x * float(w.side)) / WALL_SPEED
			if until > -16.0 and until < 50.0: score += 1000.0
		if score < best_score:
			best_score = score; best = spot
	return best

## QA autopilot: the bot looks 18 ticks ahead. Head for the pocket when a wall
## would reach the soul before it could get there, and stay until it passed.
static func _shelter_hint(s: Dictionary, t: int) -> void:
	s.botGoal = null
	if s.pocket.is_empty(): return
	var c: Vector2 = _pocket_centre(s, t)
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var need: float = soul.distance_to(c) / 1.5 + 16.0
	for w: Dictionary in s.walls:
		if t < int(w.start) - 60: continue
		var side: float = float(w.side)
		var gap: float = _wall_u(w, t) - soul.x * side
		# The pocket sits between the wall and you: get there before the wall does.
		var to_pocket: float = _wall_u(w, t) - (c.x * side + POCKET.x + 6.0)
		var limit: float = minf(gap, to_pocket) if to_pocket > -2.0 * POCKET.x else gap
		if gap > -24.0 and (limit - 8.0) / WALL_SPEED < need:
			s.botGoal = c
			return

# ---------------------------------------------------------------- 5. Loading Lanes

# Chip's lanes, as a progress bar: a loading bar with one gap lowers down the
# box; hop to the gap before it reaches your row. Between bars, packets drop
# down single red-marked lanes. Phase 1: every other bar buffers, its gap
# sliding one lane over (the arrow shows which way) as it gets close.
const BAR_Y0: float = -64.0

static func _loading_lanes(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 216.0, "h": 112.0}, 24)
	_repeat(s)
	var every: int = 66 if phase == 0 else 60
	var vy: float = 1.15 if phase == 0 else 1.25
	if t >= 16 and (t - 16) % every == 0 and t < int(s.length) - 150:
		_bar(s, t, int((t - 16) / every), vy, phase)
	_bar_slides(s, t)
	if t >= 40 and (t - 16) % every == every / 2 and t < int(s.length) - 130:
		_packet(s, t)
	_lanes_hint(s, t)

static func _lane_x(s: Dictionary, i: int) -> float:
	return float(s.lanes[clampi(i, 0, s.lanes.size() - 1)])

static func _repeat(s: Dictionary) -> void:
	if int(s.soul.lastHop) == 0:
		s.heldTicks = 0
		return
	s.heldTicks = int(s.get("heldTicks", 0)) + 1
	if int(s.heldTicks) >= REPEAT:
		s.heldTicks = 0
		s.soul.lastHop = 0

## Attack tick when a bar crosses the soul's row.
static func _bar_arrive(s: Dictionary, bar: Dictionary) -> int:
	return int(bar.born) + int((float(s.laneY) - BAR_Y0) / float(bar.vy))

static func _bar(s: Dictionary, t: int, k: int, vy: float, phase: int) -> void:
	var n: int = s.lanes.size()
	var here: int = int(s.lastGap) if int(s.lastGap) >= 0 else int(s.soul.lane)
	var dist: int = 1 if k % 2 == 0 else 2
	var dir: int = 1 if D.rand(s) < 0.5 else -1
	if here + dir * dist < 0 or here + dir * dist >= n: dir = -dir
	var final: int = clampi(here + dir * dist, 0, n - 1)
	var gap: int = final
	var slide: int = 0
	if phase >= 1 and k % 2 == 1:
		slide = 1 if D.rand(s) < 0.5 else -1
		if final - slide < 0 or final - slide >= n: slide = -slide
		gap = final - slide
	s.lastGap = final
	var bar: Dictionary = {"id": k, "born": t, "vy": vy, "gap": gap, "final": final, "slide": slide, "slid": slide == 0, "pct": mini(99, 18 * (k + 1))}
	bar.slideAt = t + int((float(s.laneY) - 46.0 - BAR_Y0) / vy)
	s.bars.append(bar)
	for i: int in range(n):
		if i == gap: continue
		_block(s, bar, i, BAR_Y0)
	D.effect(s, "pulse", D.to_world(s, Vector2(_lane_x(s, gap), -D.half(s).y + 4.0)), 16)

static func _block(s: Dictionary, bar: Dictionary, lane: int, y: float) -> void:
	D.shot(s, {"space": "box", "x": _lane_x(s, lane), "y": y, "vy": float(bar.vy), "collide": "rect", "w": 21.0, "h": 4.0, "shape": "loadseg",
		"lane": lane, "bar": int(bar.id), "life": 240})

static func _bar_slides(s: Dictionary, t: int) -> void:
	var keep: Array = []
	for bar: Dictionary in s.bars:
		if t > _bar_arrive(s, bar) + 60: continue
		keep.append(bar)
		if bool(bar.slid) or t < int(bar.slideAt): continue
		bar.slid = true
		var y: float = BAR_Y0 + float(bar.vy) * float(t - int(bar.born))
		for b: Dictionary in s.bullets:
			if b.shape == "loadseg" and int(b.bar) == int(bar.id) and int(b.lane) == int(bar.final):
				y = float(b.y)
				b.dead = true
				b.life = 0
		_block(s, bar, int(bar.gap), y)
		bar.gap = bar.final
		D.effect(s, "pulse", D.to_world(s, Vector2(_lane_x(s, int(bar.final)), y)), 16)
	s.bars = keep

static func _packet(s: Dictionary, t: int) -> void:
	var warn_ticks: int = 30
	var vy: float = 2.4
	var h: Vector2 = Vector2(108.0, 56.0)
	var arrive: int = t + warn_ticks + int((float(s.laneY) + h.y + 6.0) / vy)
	# Aim at the lane you will be parked in: the gap of the bar that passed last.
	var lane: int = int(s.soul.lane)
	var parked: int = -1000
	for bar: Dictionary in s.bars:
		var at: int = _bar_arrive(s, bar)
		if at <= arrive and at > parked and at > arrive - 70:
			parked = at; lane = int(bar.final)
	var bad: Array[int] = []
	for bar: Dictionary in s.bars:
		if absi(_bar_arrive(s, bar) - arrive) < 34: bad.append(int(bar.final))
	# Never drop a packet into a gap you will need when a bar passes.
	if lane in bad: return
	var x: float = _lane_x(s, lane)
	D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 10.0, "horizontal": false}, warn_ticks, true)
	D.shot(s, {"space": "box", "x": x, "y": -h.y - 6.0, "vy": vy, "r": 4.5, "shape": "scroll", "hold": true, "arm": warn_ticks, "life": 160})

## Place a signature in the gap of the next bar that has not reached the row.
static func _signature_lane(s: Dictionary) -> int:
	var t: int = int(s.clock) - int(s.leadIn)
	for bar: Dictionary in s.bars:
		if _bar_arrive(s, bar) > t + 20: return int(bar.final)
	var n: int = s.lanes.size()
	var here: int = int(s.soul.lane)
	var lane: int = int(D.rand(s) * n) % n
	if lane == here: lane = (lane + 2) % n
	return lane

## QA autopilot: the bot looks 18 ticks ahead, a bar tells 90. Point it at the
## gap of a bar that will reach the row soon.
static func _lanes_hint(s: Dictionary, t: int) -> void:
	s.botGoal = null
	for bar: Dictionary in s.bars:
		var until: int = _bar_arrive(s, bar) - t
		if until <= 50 and until >= -8:
			s.botGoal = Vector2(_lane_x(s, int(bar.final)), float(s.laneY))
			return

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var t: int = int(s.clock) - int(s.leadIn)
	match str(s.patternId):
		"commit_storm", "loading_lanes":
			# Editor gutter: faint line numbers down the left edge.
			var y: float = -h.y + 10.0
			var n: int = 1
			while y < h.y:
				v.text(c, v.box_point(Vector2(-h.x + 8.0, y + 4.0)), str(n), Color(BLUE, 0.16), 16.0)
				y += 14.0; n += 1
		"lob_rally", "on_the_beat":
			# A court: baseline, service lines, centre mark.
			c.draw_line(v.box_point(Vector2(-h.x, h.y - 3.0)), v.box_point(Vector2(h.x, h.y - 3.0)), Color(CREAM, 0.2), 1)
			c.draw_line(v.box_point(Vector2(0, -h.y)), v.box_point(Vector2(0, h.y)), Color(CREAM, 0.07), 1)
			c.draw_line(v.box_point(Vector2(-h.x * 0.55, -h.y)), v.box_point(Vector2(-h.x * 0.55, h.y)), Color(CREAM, 0.05), 1)
			c.draw_line(v.box_point(Vector2(h.x * 0.55, -h.y)), v.box_point(Vector2(h.x * 0.55, h.y)), Color(CREAM, 0.05), 1)
	match str(s.patternId):
		"lob_rally": _draw_lob_rally(c, s, v)
		"on_the_beat": _draw_beat(c, s, v, t)
		"shelter_drill": _draw_pocket(c, s, v, t)
		"loading_lanes": _draw_bars(c, s, v, t)

static func _draw_lob_rally(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	for w: Dictionary in s.warnings:
		if w.kind != "landing": continue
		var p: float = clampf(float(w.age) / float(w.life), 0.0, 1.0)
		var at: Vector2 = v.box_point(Vector2(float(w.x), h.y - 2.0))
		var blink: float = 0.5 + 0.5 * sin(float(w.age) * 0.5)
		c.draw_arc(at, 12.0 - 4.0 * p, PI, TAU, 12, Color(ROSE, 0.35 + 0.5 * blink), 1)
		c.draw_line(at + Vector2(-4, -4), at + Vector2(4, 0), Color(ROSE, 0.7), 1)
		c.draw_line(at + Vector2(4, -4), at + Vector2(-4, 0), Color(ROSE, 0.7), 1)
	# Ball shadows on the floor for lobs in the air.
	for b: Dictionary in s.bullets:
		if b.get("lob", false) and float(b.y) < h.y - 8.0:
			var height: float = clampf((h.y - float(b.y)) / 110.0, 0.0, 1.0)
			var at2: Vector2 = v.box_point(Vector2(float(b.x), h.y - 2.0))
			c.draw_line(at2 + Vector2(-5.0 + 2.0 * height, 0), at2 + Vector2(5.0 - 2.0 * height, 0), Color(INK, 0.6 - 0.3 * height), 2)

static func _draw_beat(c: CanvasItem, s: Dictionary, v: Node2D, t: int) -> void:
	var bt: int = _b(s)
	# The racket face (sweet spot): strings and a handle; it flashes on the beat.
	var sweet: Vector2 = _sweet(s, maxi(0, t))
	var at: Vector2 = v.box_point(sweet)
	var since: float = float(posmod(t, bt)) / float(bt)
	var flash: float = 1.0 - since
	var ring: PackedVector2Array = []
	for i: int in range(17):
		var a: float = i * TAU / 16.0
		ring.append(at + Vector2(cos(a) * 13.0, sin(a) * 15.0))
	c.draw_colored_polygon(ring, Color(AMBER, 0.06 + 0.12 * flash))
	c.draw_polyline(ring, Color(AMBER, 0.45 + 0.45 * flash), 2)
	for i: int in range(-2, 3):
		c.draw_line(at + Vector2(i * 4.5, -12), at + Vector2(i * 4.5, 12), Color(CREAM, 0.18), 1)
		c.draw_line(at + Vector2(-10, i * 5.0), at + Vector2(10, i * 5.0), Color(CREAM, 0.18), 1)
	c.draw_line(at + Vector2(9, 11), at + Vector2(16, 20), Color(AMBER, 0.6), 3)
	# Serve reticles: shrink onto the landing spot exactly on the beat.
	for r: Dictionary in s.reticles:
		var span: float = float(maxi(1, int(r.land) - int(r.born)))
		var p: float = clampf(float(t - int(r.born)) / span, 0.0, 1.0)
		var spot: Vector2 = v.box_point(Vector2(float(r.x), float(r.y)))
		c.draw_circle(spot, 14.0, Color(ROSE, 0.06 + 0.14 * p))
		c.draw_arc(spot, 14.0, 0, TAU, 20, Color(ROSE, 0.35 + 0.4 * p), 1)
		c.draw_arc(spot, 14.0 + 22.0 * (1.0 - p), 0, TAU, 24, Color(ROSE, 0.25 + 0.6 * p), 1)
		c.draw_line(spot + Vector2(-3, 0), spot + Vector2(3, 0), Color(ROSE, 0.8), 1)
		c.draw_line(spot + Vector2(0, -3), spot + Vector2(0, 3), Color(ROSE, 0.8), 1)

static func _draw_pocket(c: CanvasItem, s: Dictionary, v: Node2D, t: int) -> void:
	if s.pocket.is_empty(): return
	var centre: Vector2 = _pocket_centre(s, t)
	var age: int = t - int(s.pocket.born)
	var left: int = int(s.pocket.until) - t
	var fade: float = clampf(float(age) / 12.0, 0.0, 1.0) * clampf(float(left) / 12.0, 0.0, 1.0)
	var glow: float = 0.5 + 0.5 * sin(float(s.clock) * 0.18)
	var rect: Rect2 = Rect2(centre - POCKET, POCKET * 2.0)
	var poly: PackedVector2Array = v.box_rect_poly(rect)
	c.draw_colored_polygon(poly, Color(0.95, 0.72, 0.32, (0.12 + 0.06 * glow) * fade))
	c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(AMBER, (0.55 + 0.35 * glow) * fade), 2)
	# A little canopy on top, like Walt's shelter roof.
	var roof: PackedVector2Array = PackedVector2Array([v.box_point(centre + Vector2(-POCKET.x - 3.0, -POCKET.y)), v.box_point(centre + Vector2(0, -POCKET.y - 7.0)),
		v.box_point(centre + Vector2(POCKET.x + 3.0, -POCKET.y))])
	c.draw_colored_polygon(roof, Color(Color("6c5a4a"), fade))
	c.draw_polyline(roof, Color(AMBER, fade), 1)
	v.text(c, v.box_point(centre + Vector2(0, POCKET.y + 10.0)), "SHELTER", Color(AMBER, 0.6 * fade), 80.0)

static func _draw_bars(c: CanvasItem, s: Dictionary, v: Node2D, t: int) -> void:
	var h: Vector2 = D.half(s)
	for bar: Dictionary in s.bars:
		var y: float = BAR_Y0 + float(bar.vy) * float(t - int(bar.born))
		if y > h.y - 4.0: continue
		var gx: float = _lane_x(s, int(bar.gap))
		var blink: float = 0.5 + 0.5 * sin(float(s.clock) * 0.4)
		var a: Vector2 = v.box_point(Vector2(gx - 20.0, y - 5.0))
		var b: Vector2 = v.box_point(Vector2(gx + 20.0, y + 5.0))
		c.draw_rect(Rect2(a, b - a), Color(AMBER, 0.45 + 0.4 * blink), false, 1)
		if not bool(bar.slid):
			var dir: Vector2 = Vector2(float(bar.slide), 0)
			for j: int in range(2):
				v.chevron(c, v.box_point(Vector2(gx + float(bar.slide) * (8.0 + j * 6.0), y)), dir, Color(AMBER, 0.6 + 0.4 * blink))
		v.text(c, v.box_point(Vector2(gx, y - 7.0)), "%d%%" % int(bar.pct), Color(LILAC, 0.55), 40.0)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	if s.patternId != "on_the_beat": return
	for w: Dictionary in s.warnings:
		if w.kind != "racket": continue
		# Jakerson's racket winds up just outside the box's top-right corner.
		var p: float = clampf(float(w.age) / float(w.life), 0.0, 1.0)
		var at: Vector2 = v.arena_point(Vector2(float(w.x), float(w.y)))
		var swing: float = -0.6 - 1.4 * p
		var head: Vector2 = at + Vector2.from_angle(swing) * 10.0
		c.draw_line(at, head, Color(CREAM, 0.9), 2)
		c.draw_arc(head + Vector2.from_angle(swing) * 5.0, 5.0, 0, TAU, 12, Color(ROSE, 0.5 + 0.5 * p), 1)
	if int(s.rally) > 0:
		var h: Vector2 = D.half(s)
		v.text(c, v.box_point(Vector2(h.x - 30.0, -h.y - 6.0)), "RALLY x%d" % int(s.rally), Color(AMBER, 0.85), 90.0)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"glyph":
			var conflict: bool = b.get("conflict", false)
			var waiting: bool = int(b.age) <= int(b.arm)
			c.draw_circle(at, 5.0, Color(INK, 0.6 * alpha))
			v.text(c, at + Vector2(0, 4), str(b.get("glyph", "1")), Color(ROSE if conflict else BLUE, alpha * (0.6 if waiting else 1.0)), 12.0)
			return true
		"tennis":
			var r: float = float(b.r)
			c.draw_circle(at, r, Color(BALL, alpha))
			c.draw_arc(at + Vector2(-r * 0.55, 0).rotated(turn), r * 0.7, -1.0 + turn, 1.0 + turn, 6, Color(CREAM, alpha), 1)
			c.draw_arc(at + Vector2(r * 0.55, 0).rotated(turn), r * 0.7, PI - 1.0 + turn, PI + 1.0 + turn, 6, Color(CREAM, alpha), 1)
			return true
		"serve":
			# A serve still in the air: harmless until it lands on its reticle.
			c.draw_circle(at, 2.5, Color(BALL, 0.55 * alpha))
			c.draw_circle(at, 1.0, Color(CREAM, 0.6 * alpha))
			return true
		"impact":
			var p: float = float(b.age) / 8.0
			c.draw_circle(at, float(b.r), Color(BALL, (0.55 - 0.4 * p) * alpha))
			for i: int in range(8):
				var a: float = i * TAU / 8.0 + 0.3
				c.draw_line(at + Vector2.from_angle(a) * 5.0, at + Vector2.from_angle(a) * (float(b.r) + 3.0), Color(CREAM, (1.0 - p) * alpha), 1)
			return true
		"net":
			var armed: bool = int(b.age) > int(b.arm)
			var rise: float = clampf(float(b.age) / float(maxi(1, int(b.arm))), 0.0, 1.0)
			var hh: float = float(b.h) * 2.0 * rise
			var bottom: Vector2 = at + Vector2(0, float(b.h)).rotated(turn)
			var top: Vector2 = bottom + Vector2(0, -hh).rotated(turn)
			var col: Color = CREAM if armed else Color(ROSE, 0.4 + 0.4 * sin(float(b.age) * 0.5))
			col.a *= alpha
			c.draw_line(bottom, top, col, 2)
			var y: float = 0.0
			while y < hh:
				c.draw_line(bottom + Vector2(-2.5, -y).rotated(turn), bottom + Vector2(2.5, -y).rotated(turn), Color(col, col.a * 0.6), 1)
				y += 3.0
			c.draw_line(top + Vector2(-3.5, 0).rotated(turn), top + Vector2(3.5, 0).rotated(turn), col, 2)
			return true
		"cap":
			# A tossed mortarboard: a tumbling square top, a crown and a tassel.
			if b.get("sheltered", false): alpha *= 0.35
			var top_poly: PackedVector2Array = PackedVector2Array([at + Vector2(-6, 0).rotated(turn), at + Vector2(0, -3).rotated(turn),
				at + Vector2(6, 0).rotated(turn), at + Vector2(0, 3).rotated(turn)])
			c.draw_colored_polygon(v.quad(at + Vector2(0, 2.5).rotated(turn), 3.0, 1.8, turn), Color(Color("1e1b28"), alpha))
			c.draw_colored_polygon(top_poly, Color(Color("2c2838"), alpha))
			c.draw_polyline(top_poly + PackedVector2Array([top_poly[0]]), Color(LILAC, alpha), 1)
			c.draw_line(at, at + Vector2(4, 4).rotated(turn), Color(GOLD, alpha), 1)
			c.draw_circle(at + Vector2(4, 4.5).rotated(turn), 1.2, Color(GOLD, alpha))
			return true
		"scroll":
			var body: PackedVector2Array = v.quad(at, 5.0, 3.0, turn)
			c.draw_colored_polygon(body, Color(CREAM, alpha))
			c.draw_circle(at + Vector2(-5, 0).rotated(turn), 3.0, Color(Color("d4c49d"), alpha))
			c.draw_circle(at + Vector2(5, 0).rotated(turn), 3.0, Color(Color("d4c49d"), alpha))
			c.draw_line(at + Vector2(0, -3).rotated(turn), at + Vector2(0, 3).rotated(turn), Color(ROSE, alpha), 2)
			return true
		"loadseg":
			var q: PackedVector2Array = v.quad(at, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(q, Color(Color("2c2838"), 0.95 * alpha))
			c.draw_colored_polygon(v.quad(at, float(b.w) - 1.5, float(b.h) - 1.5, turn), Color(BLUE, 0.8 * alpha))
			var x: float = -float(b.w) + 3.0
			while x < float(b.w) - 2.0:
				c.draw_line(at + Vector2(x, float(b.h) - 1.5).rotated(turn), at + Vector2(x + 3.0, -float(b.h) + 1.5).rotated(turn), Color(CREAM, 0.35 * alpha), 1)
				x += 6.0
			return true
	return false
