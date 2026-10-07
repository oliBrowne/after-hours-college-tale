extends RefCounted
## ROOK: night marshal, key lender, folding-chair enthusiast; folded paper with
## a job that never ends. "LAST CALL. No one leaves until everyone who could
## have arrived is accounted for." Each stage (battle.rook_stage) keeps its own
## promise, so each stage has its own small set of handmade attacks, cycling by
## turn within the stage:
##   0 Keys and Exits       confirm at the key, then at the exit
##   1 Two Impossible Jobs  hold the exit chosen with REVISE (west/east) 60 ticks;
##                          the declined exit is where the trouble comes from
##   2 One Shift Together   two shared stopping cues (confirm in the open cue);
##                          a shared pocket shelters you
## Attacks lean on Rook's keys, locks and exits, rook-like straight-line moves,
## the last-call bell, folding chairs and the lights going out.

const D = preload("res://core/dodge_box.gd")
## ORDER is only for the preview harness: entry i is the attack each stage
## plays on turn i (stage 0 / stage 1 / stage 2). setup() reads STAGES.
const ORDER: Array[String] = ["key_ring/last_call/patrol", "lock_up/two_jobs/lights_out", "chairs/last_call/patrol"]
const STAGES: Array = [["key_ring", "lock_up", "chairs"], ["last_call", "two_jobs"], ["patrol", "lights_out"]]
const PHASES: Array[int] = [0, 1, 2]
const STAGE_NAMES: Array[String] = ["Keys and Exits", "Two Impossible Jobs", "One Shift Together"]
const LENGTH: int = 540
const KEY_AT: Vector2 = Vector2(-72, -36)
const EXIT_AT: Vector2 = Vector2(80, 34)
const HOLD_X: float = 80.0
const HOLD_Y: float = 10.0
const CUES: Array[int] = [140, 290, 430]
const CUE_OPEN: int = 70

const AMBER: Color = Color("e8b45c")
const BRASS: Color = Color("c9a050")
const CREAM: Color = Color("e6d6b1")
const MINT: Color = Color("b9d5bc")
const EXIT_GREEN: Color = Color("6fcf8e")
const PLUM: Color = Color("6b526a")
const ROSE: Color = Color("e8837b")
const LILAC: Color = Color("a68db8")
const STEEL: Color = Color("8f98a8")
const INK: Color = Color("0d101c")

static func _stage(s: Dictionary) -> int:
	return clampi(int(s.phase), 0, 2)

static func setup(s: Dictionary) -> void:
	var stage: int = _stage(s)
	var pool: Array = STAGES[stage]
	var id: String = pool[int(s.turn) % pool.size()]
	s.patternId = id
	s.length = LENGTH
	s.keyHeld = false
	s.exitReached = false
	s.exitHold = 0
	s.sharedCues = 0
	s.chosenExit = 0.0
	s.cueOpen = false
	s.cueList = []
	s.pocket = Rect2(-22, -20, 44, 40)
	s.pocketGhost = null
	s.legs = []
	s.lanes = []
	s.cells = []
	s.chairSpots = []
	s.bannerColor = AMBER
	s.ringAngle = 0.0
	match stage:
		0:
			D.objective(s, {"kind": "confirm", "x": KEY_AT.x, "y": KEY_AT.y, "r": 14.0, "label": "KEY"})
			D.objective(s, {"kind": "confirm", "x": EXIT_AT.x, "y": EXIT_AT.y, "r": 14.0, "label": "EXIT", "active": false})
		1:
			D.objective(s, {"kind": "hold", "x": HOLD_X, "y": HOLD_Y, "r": 20.0, "need": 60, "active": false, "label": "EXIT"})
	var title: String = ""
	match id:
		"key_ring":
			title = "Key Ring"
			s.hint = "The key ring tightens and loosens. The key rides its gap. Confirm it, then the exit."
		"lock_up":
			title = "Lock Up"
			s.hint = "Locks slide in straight lines, rook moves. Read the lanes. Key, then exit."
		"chairs":
			title = "Set Out Chairs"
			s.hint = "Chairs land on the outlined spots. Carts roll the aisles. Key, then exit."
		"last_call":
			title = "Last Call"
			s.hint = "The bell calls everyone back to the declined door. Hold your exit; slip the headcount."
		"two_jobs":
			title = "Keep Them In, Let Them Out"
			s.hint = "Two jobs take turns: walls close in, then everything flies out. Hold your exit."
		"patrol":
			title = "Night Patrol"
			s.hint = "The shared pocket patrols in straight lines. Stay in it; confirm when it stops."
			s.pocket = Rect2(-22, -20, 44, 40)
			s.legs = [[50, 100, Vector2(-76, -20)], [180, 220, Vector2(-76, 22)], [330, 380, Vector2(76, 22)], [460, 500, Vector2(0, 0)]]
			s.cueTimes = [112, 236, 392]
		"lights_out":
			title = "Lights Out"
			s.hint = "Rook turns the lights off room by room. Leave flickering rooms. Confirm in the cue."
			s.pocket = Rect2(-82, -2, 40, 36)
	s.phaseName = "%s / %s" % [STAGE_NAMES[stage], title]

## The preview harness sets what main.gd sets after create.
static func preview(s: Dictionary, _phase: int) -> void:
	s.revision = "west"

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	match _stage(s):
		0: return bool(s.exitReached)
		1: return int(s.exitHold) >= 60 and str(s.revision) in ["west", "east"]
	return int(s.sharedCues) >= 2 and str(s.revision) in ["west", "east"]

static func tick(s: Dictionary, t: int) -> void:
	var stage: int = _stage(s)
	match str(s.patternId):
		"key_ring": _key_ring(s, t)
		"lock_up": _lock_up(s, t)
		"chairs": _chairs(s, t)
		"last_call": _last_call(s, t)
		"two_jobs": _two_jobs(s, t)
		"patrol": _patrol(s, t)
		"lights_out": _lights_out(s, t)
	match stage:
		0: _keys_promise(s)
		1: _exit_promise(s)
		2: _cue_promise(s, t)

static func after(s: Dictionary, _t: int) -> void:
	match _stage(s):
		0:
			var key: Dictionary = s.objectives[0]
			var exit: Dictionary = s.objectives[1]
			if key.done and not s.keyHeld:
				s.keyHeld = true
				exit.active = true
				D.banner(s, "KEY HELD", 40)
			if exit.done and not s.exitReached:
				s.exitReached = true
				D.banner(s, "EXIT REACHED", 50)
				s.bannerColor = MINT
		1:
			s.exitHold = int(s.objectives[0].progress)
		2:
			for cue: Dictionary in s.cueList:
				var o: Dictionary = s.objectives[int(cue.obj)]
				if o.done and not cue.counted:
					cue.counted = true
					s.sharedCues = int(s.sharedCues) + 1
					o.active = false

# ---------------------------------------------------------------- promises

static func _soul(s: Dictionary) -> Vector2:
	return Vector2(float(s.soul.x), float(s.soul.y))

## The autopilot plans whole 18-tick runs and stops ~17 px short of its goal,
## so aim it a little past the spot along the way in.
static func _lead(s: Dictionary, target: Vector2) -> Vector2:
	var d: Vector2 = target - _soul(s)
	return target + d.normalized() * 15.0 if d.length() > 2.0 else target

static func _keys_promise(s: Dictionary) -> void:
	var key: Dictionary = s.objectives[0]
	var exit: Dictionary = s.objectives[1]
	if not key.done: s.botGoal = _lead(s, Vector2(float(key.x), float(key.y)))
	elif not exit.done: s.botGoal = _lead(s, Vector2(float(exit.x), float(exit.y)))
	else: s.botGoal = null

static func _declined(s: Dictionary) -> Array[float]:
	var rev: String = str(s.revision)
	var out: Array[float] = []
	if rev != "east": out.append(1.0)
	if rev != "west": out.push_front(-1.0)
	return out

static func _exit_promise(s: Dictionary) -> void:
	var o: Dictionary = s.objectives[0]
	var rev: String = str(s.revision)
	if rev in ["west", "east"]:
		s.chosenExit = -HOLD_X if rev == "west" else HOLD_X
		o.x = float(s.chosenExit)
		if not o.done: o.active = true
	else:
		o.active = false
	s.botGoal = _lead(s, Vector2(float(o.x), float(o.y))) if o.active and not o.done else null

static func _cue_times(s: Dictionary) -> Array:
	return s.get("cueTimes", CUES)

static func _cue_promise(s: Dictionary, t: int) -> void:
	s.safe = [s.pocket]
	var times: Array = _cue_times(s)
	var open: bool = false
	for i: int in range(times.size()):
		var at: int = int(times[i])
		if t == at:
			var spot: Vector2 = Rect2(s.pocket).get_center()
			D.objective(s, {"kind": "confirm", "x": spot.x, "y": spot.y, "r": 14.0, "label": "STOP"})
			s.cueList.append({"t": at, "obj": s.objectives.size() - 1, "counted": false})
			D.banner(s, "STOPPING CUE", 40)
			s.bannerColor = MINT
			D.warn(s, {"kind": "none"}, 1, true)
		if t >= at and t < at + CUE_OPEN: open = true
		if t == at + CUE_OPEN:
			for cue: Dictionary in s.cueList:
				if int(cue.t) == at: s.objectives[int(cue.obj)].active = false
	s.cueOpen = open
	# The cue rides with the shared pocket.
	var goal: Variant = null
	for cue: Dictionary in s.cueList:
		var o: Dictionary = s.objectives[int(cue.obj)]
		if o.active and not o.done:
			var c: Vector2 = Rect2(s.pocket).get_center()
			o.x = c.x; o.y = c.y
			goal = _lead(s, c)
	if goal == null: goal = _lead(s, _pocket_goal(s))
	s.botGoal = goal

## Autopilot: rest in the shared pocket (or where it is going).
static func _pocket_goal(s: Dictionary) -> Vector2:
	if s.pocketGhost != null: return Vector2(s.pocketGhost)
	return Rect2(s.pocket).get_center()

# ---------------------------------------------------------------- shared hazards

## A rook move: a lock (and its chain) slides fast along a marked row or column.
static func _rook_move(s: Dictionary, horizontal: bool, at: float, from: float, warn: int = 30, speed: float = 6.0) -> void:
	var h: Vector2 = D.half(s)
	if horizontal:
		D.warn(s, {"kind": "rook_lane", "space": "box", "horizontal": true, "at": at, "w": 7.0}, warn, true)
		for i: int in range(4):
			var lead_x: float = from * (h.x + 14.0 + speed * warn + i * 10.0)
			D.shot(s, {"space": "box", "x": lead_x, "y": at, "vx": -from * speed, "collide": "rect", "w": 5.5 if i == 0 else 3.0, "h": 5.5 if i == 0 else 2.5, "shape": "lock" if i == 0 else "chain", "life": 140})
	else:
		D.warn(s, {"kind": "rook_lane", "space": "box", "horizontal": false, "at": at, "w": 7.0}, warn, true)
		for i: int in range(4):
			var lead_y: float = from * (h.y + 14.0 + speed * warn + i * 10.0)
			D.shot(s, {"space": "box", "x": at, "y": lead_y, "vy": -from * speed, "collide": "rect", "w": 5.5 if i == 0 else 2.5, "h": 5.5 if i == 0 else 3.0, "shape": "lock" if i == 0 else "chain", "life": 140})

static func _fling_key(s: Dictionary, from: Vector2, dir: Vector2, speed: float, arm: int = 14) -> void:
	D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": dir.x * speed, "vy": dir.y * speed, "hold": true, "arm": arm, "r": 3.5, "shape": "key", "rot": dir.angle(), "life": 220})

# ---------------------------------------------------------------- stage 0

static func _ring_radius(t: int) -> float:
	return 32.0 + 24.0 * cos(float(t) * 0.018)

## Key Ring: Rook's key ring breathes around the middle of the box, spinning;
## the key you need rides in its one gap. Inside, the ring tightens to the hub,
## so leave through the gap. Keys are flung at you from the ring.
static func _key_ring(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 236.0, "h": 120.0}, 24)
		s.ringAngle = PI - 14.5 * TAU / 16.0 + (D.rand(s) - 0.5) * 1.2  # gap starts on the far (west) side from the exit
		for i: int in range(16):
			if i >= 14: continue
			D.shot(s, {"space": "box", "orbit": {"ox": 0.0, "oy": 0.0, "radius": _ring_radius(0), "angle": float(s.ringAngle) + i * TAU / 16.0, "av": 0.0}, "arm": 40, "r": 4.0, "shape": "key", "life": 900, "ringKey": true})
	s.ringAngle = float(s.ringAngle) + 0.013
	var radius: float = _ring_radius(t)
	for b: Dictionary in s.bullets:
		if b.get("ringKey", false):
			b.orbit.radius = radius
			b.orbit.av = 0.013
			b.rot = float(b.orbit.angle) + PI * 0.5
	# The gap is the two missing slots (14 and 15); the key sits in it.
	var gap: float = float(s.ringAngle) + 14.5 * TAU / 16.0
	var key: Dictionary = s.objectives[0]
	if not key.done:
		var at: Vector2 = Vector2.from_angle(gap) * radius
		key.x = at.x; key.y = at.y
	if t % 34 == 20 and t > 40 and t < 480:
		var soul: Vector2 = _soul(s)
		var a: float = soul.angle() if soul.length() > 1.0 else D.rand(s) * TAU
		var inside: bool = soul.length() < radius
		for k: int in range(3):
			var ang: float = a + (k - 1) * 0.32
			var from: Vector2 = Vector2.from_angle(ang) * radius
			var dir: Vector2 = (soul - from).normalized() if not inside else -from.normalized()
			if not inside: dir = dir.rotated((k - 1) * 0.18)
			_fling_key(s, from, dir, 1.7)
	if t % 120 == 60 and t < 480:
		_rook_move(s, true, clampf(_soul(s).y, -50.0, 50.0), -1.0 if D.rand(s) < 0.5 else 1.0, 34, 5.0)

## Lock Up: closing time. Locks slide along rows and columns (rook moves), each
## lane marked first, two at a time from the middle on; the doors squeeze the
## room narrower and open it again.
static func _lock_up(s: Dictionary, t: int) -> void:
	if t == 0: D.box_to(s, {"w": 248.0, "h": 116.0}, 24)
	if t == 180:
		D.warn(s, {"kind": "curtain"}, 40, true)
		D.banner(s, "DOORS CLOSING", 40)
		D.box_to(s, {"w": 184.0}, 50, 40)
	if t == 400:
		D.box_to(s, {"w": 248.0}, 50)
	var soul: Vector2 = _soul(s)
	var h: Vector2 = D.half(s)
	var every: int = 36
	if t % every == 10 and t > 20 and t < 480:
		var row_turn: bool = int(t / every) % 2 == 0
		var from: float = -1.0 if D.rand(s) < 0.5 else 1.0
		if row_turn: _rook_move(s, true, clampf(soul.y + D.rand_range(s, -4.0, 4.0), -h.y + 6.0, h.y - 6.0), from)
		else: _rook_move(s, false, clampf(soul.x + D.rand_range(s, -4.0, 4.0), -h.x + 6.0, h.x - 6.0), from)
		if t > 200:
			# A second lane, offset, so the cross has to be read.
			var off: float = D.rand_range(s, 26.0, 44.0) * (-1.0 if D.rand(s) < 0.5 else 1.0)
			if row_turn: _rook_move(s, false, clampf(soul.x + off, -h.x + 6.0, h.x - 6.0), -from)
			else: _rook_move(s, true, clampf(soul.y + off * 0.6, -h.y + 6.0, h.y - 6.0), -from)
	if t % 50 == 25 and t > 60 and t < 470:
		var corner: Vector2 = Vector2(h.x - 8.0, h.y - 8.0) * Vector2(-1.0 if D.rand(s) < 0.5 else 1.0, -1.0 if D.rand(s) < 0.5 else 1.0)
		_fling_key(s, corner, (soul - corner).normalized(), 1.9, 20)

## Set Out Chairs: Rook sets out folding chairs on a grid. Each spot is
## outlined first, then the chair stays a while before folding away. Chair
## carts roll along the aisles between the rows.
static func _chairs(s: Dictionary, t: int) -> void:
	if t == 0: D.box_to(s, {"w": 248.0, "h": 116.0}, 24)
	var soul: Vector2 = _soul(s)
	var h: Vector2 = D.half(s)
	if t % 16 == 8 and t > 16 and t < 470:
		var aimed: bool = int(t / 16) % 2 == 0
		var x: float = soul.x if aimed else D.rand_range(s, -100.0, 100.0)
		var y: float = soul.y if aimed else D.rand_range(s, -40.0, 40.0)
		var cell: Vector2 = Vector2(clampf(round(x / 30.0) * 30.0, -105.0, 105.0), clampf(round(y / 26.0) * 26.0, -39.0, 39.0))
		var clear: bool = cell.distance_to(Vector2(float(s.objectives[0].x), float(s.objectives[0].y))) > 24.0 and cell.distance_to(EXIT_AT) > 24.0
		for spot: Dictionary in s.chairSpots:
			if Vector2(spot.at).distance_to(cell) < 4.0 and t < int(spot.until): clear = false
		if clear:
			s.chairSpots.append({"at": cell, "until": t + 36 + 150})
			D.shot(s, {"space": "box", "x": cell.x, "y": cell.y, "hold": true, "arm": 36, "collide": "rect", "w": 6.0, "h": 7.0, "shape": "folding", "life": 186})
	if t % 70 == 40 and t > 40 and t < 470:
		var aisle: float = -13.0 if D.rand(s) < 0.5 else 13.0
		if absf(soul.y - 13.0) < absf(soul.y + 13.0): aisle = 13.0
		else: aisle = -13.0
		var from: float = -1.0 if D.rand(s) < 0.5 else 1.0
		D.warn(s, {"kind": "rook_lane", "space": "box", "horizontal": true, "at": aisle, "w": 7.0}, 36, true)
		for i: int in range(3):
			D.shot(s, {"space": "box", "x": from * (h.x + 14.0 + 3.0 * 36.0 + i * 13.0), "y": aisle, "vx": -from * 3.0, "collide": "rect", "w": 6.0, "h": 5.0, "shape": "cart", "life": 200})
	var spots: Array = []
	for spot: Dictionary in s.chairSpots:
		if t < int(spot.until): spots.append(spot)
	s.chairSpots = spots

# ---------------------------------------------------------------- stage 1

## Last Call: the bell rings and the declined door sends out everyone who could
## have arrived; they are called back and return to the door. A headcount line
## sweeps across from that side with one gap. Before REVISE, both doors do it.
static func _last_call(s: Dictionary, t: int) -> void:
	if t == 0: D.box_to(s, {"w": 248.0, "h": 112.0}, 24)
	var h: Vector2 = D.half(s)
	var soul: Vector2 = _soul(s)
	var sides: Array[float] = _declined(s)
	if t % 60 == 0 and t >= 30 and t < 470:
		var side: float = sides[int(t / 60) % sides.size()]
		s.bell = t
		if t == 60: D.banner(s, "LAST CALL", 50)
		var door: Vector2 = Vector2(side * (h.x - 2.0), HOLD_Y)
		D.warn(s, {"kind": "door", "side": side}, 24, true)
		var aim: float = (soul - door).angle()
		s.fan = s.get("fan", [])
		s.fan.append({"at": t + 24, "side": side, "aim": aim})
	for fan: Dictionary in s.get("fan", []):
		if int(fan.at) == t:
			var door2: Vector2 = Vector2(float(fan.side) * (h.x - 2.0), HOLD_Y)
			for k: int in range(5):
				var a: float = float(fan.aim) + (k - 2) * 0.24
				var dir: Vector2 = Vector2.from_angle(a)
				var speed: float = 2.5
				var decel: float = speed * speed / (2.0 * 200.0)
				D.shot(s, {"space": "box", "x": door2.x, "y": door2.y, "vx": dir.x * speed, "vy": dir.y * speed, "ax": -dir.x * decel, "ay": -dir.y * decel, "r": 4.0, "shape": "guest", "life": 2 * int(speed / decel) + 4})
	if t % 100 == 70 and t < 460:
		var side2: float = sides[int(t / 100) % sides.size()]
		var gy: float = clampf(soul.y + D.rand_range(s, 18.0, 34.0) * (-1.0 if D.rand(s) < 0.5 else 1.0), -h.y + 16.0, h.y - 16.0)
		var gap: float = 30.0
		var x: float = side2 * (h.x + 6.0)
		var top_len: float = (gy - gap * 0.5) + h.y + 20.0
		var bottom_len: float = h.y + 20.0 - (gy + gap * 0.5)
		D.warn(s, {"kind": "edge", "space": "box", "x": side2 * (h.x - 4.0), "y": gy, "dir": Vector2(-side2, 0)}, 30, true)
		D.shot(s, {"space": "box", "x": x + side2 * 45.0, "y": -h.y - 20.0 + top_len * 0.5, "vx": -side2 * 1.5, "collide": "rect", "w": 2.5, "h": top_len * 0.5, "shape": "tally", "life": 240})
		D.shot(s, {"space": "box", "x": x + side2 * 45.0, "y": h.y + 20.0 - bottom_len * 0.5, "vx": -side2 * 1.5, "collide": "rect", "w": 2.5, "h": bottom_len * 0.5, "shape": "tally", "life": 240})

## Keep Them In, Let Them Out: two jobs take turns. KEEP THEM IN: walls of keys
## close in from both sides, each with a gap. LET THEM OUT: a ring of
## programmes bursts from the middle toward the doors. Locks slam down the
## declined door's column all the while.
static func _two_jobs(s: Dictionary, t: int) -> void:
	if t == 0: D.box_to(s, {"w": 248.0, "h": 116.0}, 24)
	var h: Vector2 = D.half(s)
	var soul: Vector2 = _soul(s)
	var job: int = int((t - 20) / 100) % 2 if t >= 20 else -1
	if t >= 20 and (t - 20) % 100 == 0 and t < 460:
		D.banner(s, "KEEP THEM IN" if job == 0 else "LET THEM OUT", 40)
		s.bannerColor = AMBER
	var local: int = (t - 20) % 100
	if job == 0 and t < 460 and (local == 20 or local == 60):
		for side: float in [-1.0, 1.0]:
			var gy: float = clampf(soul.y + D.rand_range(s, -30.0, 30.0), -h.y + 14.0, h.y - 14.0)
			D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 4.0), "y": gy, "dir": Vector2(-side, 0)}, 24)
			var slots: int = 9
			var spacing: float = (h.y * 2.0 - 8.0) / float(slots - 1)
			for i: int in range(slots):
				var y: float = -h.y + 4.0 + i * spacing
				if absf(y - gy) < 16.0: continue
				D.shot(s, {"space": "box", "x": side * (h.x + 10.0 + 1.3 * 24.0), "y": y, "vx": -side * 1.3, "r": 4.0, "shape": "key", "rot": PI * 0.5 * side, "life": 260})
	if job == 1 and t < 460 and (local == 16 or local == 56):
		# The crowd bursts out from somewhere near the middle, not on top of you.
		var origin: Vector2 = Vector2(D.rand_range(s, -50.0, 50.0), D.rand_range(s, -24.0, 24.0))
		if origin.distance_to(soul) < 40.0: origin = (origin + (origin - soul).normalized() * 40.0).clamp(Vector2(-70, -30), Vector2(70, 30))
		D.effect(s, "pulse", D.to_world(s, origin), 24)
		var gap: float = (soul - origin).angle() + D.rand_range(s, 0.6, 1.0) * (-1.0 if D.rand(s) < 0.5 else 1.0)
		var count: int = 18
		for i: int in range(count):
			var a: float = gap + PI / count + i * TAU / count
			if absf(wrapf(a - gap, -PI, PI)) < 0.42: continue
			D.shot(s, {"space": "box", "x": origin.x + cos(a) * 6.0, "y": origin.y + sin(a) * 6.0, "vx": cos(a) * 1.25, "vy": sin(a) * 1.25, "hold": true, "arm": 22, "collide": "rect", "w": 4.5, "h": 3.5, "shape": "programme", "rot": a, "life": 200})
	if t % 44 == 30 and t > 40 and t < 470:
		for side3: float in _declined(s):
			_rook_move(s, false, side3 * (h.x - 22.0) + D.rand_range(s, -10.0, 10.0), -1.0 if D.rand(s) < 0.5 else 1.0, 30, 5.0)

# ---------------------------------------------------------------- stage 2

## Night Patrol: the shared pocket moves in rook moves (straight lines between
## stops; its next stop is outlined first). When it stops, a stopping cue opens
## inside it. Outside, locks slide along marked lanes and the flashlight sweeps.
static func _patrol(s: Dictionary, t: int) -> void:
	if t == 0: D.box_to(s, {"w": 248.0, "h": 116.0}, 24)
	var h: Vector2 = D.half(s)
	var soul: Vector2 = _soul(s)
	var from: Vector2 = Vector2.ZERO
	s.pocketGhost = null
	for leg: Array in s.legs:
		var start: int = int(leg[0]); var stop: int = int(leg[1]); var to: Vector2 = leg[2]
		if t >= start - 40 and t < start:
			s.pocketGhost = to
			if t == start - 40: D.warn(s, {"kind": "none"}, 1, true)
		if t >= start and t <= stop:
			var p: float = float(t - start) / float(stop - start)
			p = p * p * (3.0 - 2.0 * p)
			s.pocket = Rect2(from.lerp(to, p) - Vector2(22, 20), Vector2(44, 40))
		from = to
	if t % 30 == 0 and t > 30 and t < 480:
		var row_turn: bool = int(t / 30) % 2 == 0
		var side: float = -1.0 if D.rand(s) < 0.5 else 1.0
		if row_turn: _rook_move(s, true, clampf(soul.y + D.rand_range(s, -5.0, 5.0), -h.y + 6.0, h.y - 6.0), side, 30, 5.0)
		else: _rook_move(s, false, clampf(soul.x + D.rand_range(s, -5.0, 5.0), -h.x + 6.0, h.x - 6.0), side, 30, 5.0)
	if t % 90 == 60 and t < 470:
		var rig: Vector2 = Vector2(128.0 + (110.0 if int(t / 90) % 2 == 0 else -110.0), -34.0)
		var aim: float = (D.soul_world(s) - rig).angle()
		var sweep: float = 0.011 * (-1.0 if rig.x > 128.0 else 1.0)
		D.shot(s, {"x": rig.x, "y": rig.y, "collide": "beam", "angle": aim - sweep * 30.0, "len": 300.0, "w0": 6.0, "w1": 40.0, "warn": 34, "live": 46, "av": 0.0, "sweep": sweep, "shape": "flashlight"})
	for b: Dictionary in s.bullets:
		if b.collide == "beam": b.av = float(b.sweep) if int(b.age) >= int(b.warn) else 0.0

## Lights Out: the room is six bays. Rook switches them off one after another:
## a bay flickers, then goes dark and hurts until the lights come back. The
## shared pocket (the one lamp you share) moves to a new bay before each cue.
## Folded paper planes glide through the lit bays.
static func _lights_out(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 252.0, "h": 120.0}, 24)
		for i: int in range(6):
			s.cells.append({"col": i % 3, "row": int(i / 3), "flicker": -1, "dark": -1, "until": -1})
	var h: Vector2 = Vector2(126, 60)
	var soul: Vector2 = _soul(s)
	# The shared lamp moves before each cue (outlined first).
	var bays: Array[Vector2] = [Vector2(-84, -30), Vector2(0, -30), Vector2(84, -30), Vector2(-84, 30), Vector2(0, 30), Vector2(84, 30)]
	var plan: Array[int] = [3, 1, 5, 0]
	var moves: Array[int] = [0, 100, 250, 390]
	s.pocketGhost = null
	for m: int in range(moves.size()):
		if m > 0 and t >= moves[m] - 40 and t < moves[m]: s.pocketGhost = bays[plan[m]] + Vector2(0, 2)
		if t == moves[m]:
			s.pocket = Rect2(bays[plan[m]] + Vector2(-20, -16), Vector2(40, 36))
			s.lampBay = plan[m]
	# Switch bays off: the bay you are in, then a random one.
	if t % 46 == 30 and t < 470:
		var mine: int = _bay_of(soul)
		var pick: int = mine if int(t / 46) % 2 == 0 else int(D.rand(s) * 6.0)
		var cell: Dictionary = s.cells[pick]
		if int(cell.until) < t and pick != int(s.get("lampBay", 3)):
			cell.flicker = t; cell.dark = t + 44; cell.until = t + 44 + 100
			D.warn(s, {"kind": "none"}, 1, true)
	for i: int in range(6):
		var cell2: Dictionary = s.cells[i]
		if t >= int(cell2.dark) and t < int(cell2.until) and _bay_of(soul) == i:
			D.hurt(s, D.soul_world(s))
	if t % 26 == 20 and t > 30 and t < 470:
		var side: float = -1.0 if D.rand(s) < 0.5 else 1.0
		var y: float = clampf(soul.y + D.rand_range(s, -14.0, 14.0), -h.y + 8.0, h.y - 8.0)
		if int(t / 26) % 2 == 1: y = D.rand_range(s, -h.y + 8.0, h.y - 8.0)
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 4.0), "y": y, "dir": Vector2(-side, 0)}, 28)
		D.shot(s, {"space": "box", "x": side * (h.x + 10.0 + 2.0 * 28.0), "y": y, "vx": -side * 2.0, "r": 3.5, "shape": "plane", "rot": PI if side > 0 else 0.0, "wave": {"amp": 9.0, "freq": 0.06, "phase": D.rand(s) * TAU}, "life": 220})

static func _bay_rect(i: int) -> Rect2:
	return Rect2(-126.0 + (i % 3) * 84.0, -60.0 + int(i / 3) * 60.0, 84.0, 60.0)

static func _bay_of(p: Vector2) -> int:
	var col: int = clampi(int(floor((p.x + 126.0) / 84.0)), 0, 2)
	var row: int = 0 if p.y < 0.0 else 1
	return row * 3 + col

# ---------------------------------------------------------------- progress / drawing

static func progress(s: Dictionary) -> String:
	return "Key %s / exit %s" % ["held" if s.keyHeld else "open", "reached" if s.exitReached else "open"] if int(s.phase) == 0 else "CONNECT > REVISE\nChoose one exit; decline one" if str(s.revision).is_empty() else "Chosen exit held %d/60" % mini(60, int(s.exitHold)) if int(s.phase) == 1 else "Shared stopping cues %d/2" % mini(2, int(s.sharedCues))

static func _t(s: Dictionary) -> int:
	return int(s.clock) - int(s.leadIn)

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var t: int = _t(s)
	var h: Vector2 = D.half(s)
	var clock: int = int(s.clock)
	var id: String = str(s.patternId)
	# Floorboards of the old hall.
	for i: int in range(-5, 6):
		c.draw_line(v.box_point(Vector2(-h.x, i * 12.0)), v.box_point(Vector2(h.x, i * 12.0)), Color(BRASS, 0.05), 1)
	if id == "lights_out":
		for i: int in range(s.cells.size()):
			var cell: Dictionary = s.cells[i]
			var poly: PackedVector2Array = v.box_rect_poly(_bay_rect(i).grow(-1.0))
			var dark: bool = t >= int(cell.dark) and t < int(cell.until)
			var flick: bool = t >= int(cell.flicker) and t < int(cell.dark)
			if dark:
				c.draw_colored_polygon(poly, Color(0.0, 0.0, 0.02, 0.85))
				c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(ROSE, 0.55), 1)
			elif flick:
				var on: bool = (clock / (4 if t > int(cell.dark) - 16 else 7)) % 2 == 0
				c.draw_colored_polygon(poly, Color(ROSE, 0.10) if on else Color(0, 0, 0, 0.45))
				c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(ROSE, 0.6), 1)
			else:
				c.draw_colored_polygon(poly, Color(AMBER, 0.035))
				c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(BRASS, 0.18), 1)
	if id == "chairs":
		for spot: Dictionary in s.chairSpots:
			var at: Vector2 = Vector2(spot.at)
			var r: PackedVector2Array = v.box_rect_poly(Rect2(at - Vector2(8, 9), Vector2(16, 18)))
			c.draw_polyline(r + PackedVector2Array([r[0]]), Color(ROSE, 0.35), 1)
	# Lanes for rook moves.
	for w: Dictionary in s.warnings:
		var f: float = 0.5 + 0.5 * sin(float(w.age) * 0.5)
		match str(w.kind):
			"rook_lane":
				var rect: Rect2 = Rect2(-h.x - 4.0, float(w.at) - float(w.w), h.x * 2.0 + 8.0, float(w.w) * 2.0) if w.horizontal else Rect2(float(w.at) - float(w.w), -h.y - 4.0, float(w.w) * 2.0, h.y * 2.0 + 8.0)
				var poly2: PackedVector2Array = v.box_rect_poly(rect)
				c.draw_colored_polygon(poly2, Color(ROSE, 0.07 + 0.13 * f))
				c.draw_polyline(poly2 + PackedVector2Array([poly2[0]]), Color(ROSE, 0.4), 1)
			"door":
				var side: float = float(w.side)
				var door: Rect2 = Rect2(Vector2(side * h.x - (10.0 if side > 0 else 0.0), HOLD_Y - 14.0), Vector2(10, 28))
				c.draw_colored_polygon(v.box_rect_poly(door), Color(ROSE, 0.15 + 0.3 * f))
	# Doors on the side walls (stage 1).
	if _stage(s) == 1:
		for side2: float in [-1.0, 1.0]:
			var declined: bool = side2 in _declined(s) and not str(s.revision).is_empty()
			var col: Color = Color(PLUM, 0.9) if declined else Color(EXIT_GREEN, 0.7)
			var door2: Rect2 = Rect2(Vector2(side2 * h.x - (6.0 if side2 > 0 else 0.0), HOLD_Y - 14.0), Vector2(6, 28))
			c.draw_colored_polygon(v.box_rect_poly(door2), col)
			if declined:
				var mid: Vector2 = v.box_point(Vector2(side2 * (h.x - 14.0), HOLD_Y))
				c.draw_line(mid + Vector2(-6, -6), mid + Vector2(6, 6), Color(PLUM, 1.0), 3)
				c.draw_line(mid + Vector2(-6, 6), mid + Vector2(6, -6), Color(PLUM, 1.0), 3)
				c.draw_line(mid + Vector2(-6, -6), mid + Vector2(6, 6), CREAM, 1)
				c.draw_line(mid + Vector2(-6, 6), mid + Vector2(6, -6), CREAM, 1)
	# The shared pocket (stage 2).
	if _stage(s) == 2:
		var pocket: Rect2 = s.pocket
		var pp: PackedVector2Array = v.box_rect_poly(pocket)
		var flick2: float = 0.85 + 0.15 * sin(float(clock) * 0.37)
		c.draw_colored_polygon(pp, Color(0.95, 0.75, 0.4, 0.12 * flick2))
		c.draw_polyline(pp + PackedVector2Array([pp[0]]), Color(MINT, 0.8), 2)
		if s.pocketGhost != null:
			var g: Rect2 = Rect2(Vector2(s.pocketGhost) - pocket.size * 0.5, pocket.size)
			var gp: PackedVector2Array = v.box_rect_poly(g)
			var blink: float = 0.4 + 0.4 * sin(float(clock) * 0.3)
			for k: int in range(4): _dashed(c, gp[k], gp[(k + 1) % 4], Color(MINT, blink))
			c.draw_line(v.box_point(pocket.get_center()), v.box_point(g.get_center()), Color(MINT, 0.3), 1)
	# The key ring's band.
	if id == "key_ring":
		c.draw_arc(v.box_point(Vector2.ZERO), _ring_radius(maxi(0, t)), 0, TAU, 40, Color(BRASS, 0.25), 1)
		c.draw_circle(v.box_point(Vector2.ZERO), 5.0, Color(BRASS, 0.5))
	# The exit sign (stage 0).
	if _stage(s) == 0:
		var e: Vector2 = v.box_point(EXIT_AT + Vector2(0, -18))
		var lit: bool = s.keyHeld
		c.draw_rect(Rect2(e - Vector2(13, 5), Vector2(26, 10)), Color(EXIT_GREEN, 0.9 if lit else 0.3))
		v.text(c, e + Vector2(0, 4), "EXIT", INK if lit else Color(INK, 0.6), 30.0)

static func _dashed(c: CanvasItem, a: Vector2, b: Vector2, col: Color) -> void:
	var n: int = maxi(1, int(a.distance_to(b) / 6.0))
	for i: int in range(0, n, 2):
		c.draw_line(a.lerp(b, float(i) / n), a.lerp(b, float(mini(i + 1, n)) / n), col, 1)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var t: int = _t(s)
	# The last-call bell above the box.
	if str(s.patternId) == "last_call":
		var at: Vector2 = v.box_point(Vector2(0, -h.y)) + Vector2(0, -14)
		var since: int = t - int(s.get("bell", -999))
		var swing: float = sin(float(since) * 0.5) * 0.5 * maxf(0.0, 1.0 - since / 30.0)
		var dir: Vector2 = Vector2(0, 1).rotated(swing)
		var side: Vector2 = Vector2(1, 0).rotated(swing)
		c.draw_colored_polygon(PackedVector2Array([at - side * 3.0, at + side * 3.0, at + dir * 9.0 + side * 7.0, at + dir * 9.0 - side * 7.0]), BRASS)
		c.draw_circle(at + dir * 10.0, 1.8, CREAM)
		if since >= 0 and since < 20:
			c.draw_arc(at + dir * 5.0, 10.0 + since * 0.8, -PI * 0.9, -PI * 0.1, 10, Color(CREAM, 1.0 - since / 20.0), 1)
	# Flashlight rigs.
	for b: Dictionary in s.bullets:
		if b.collide == "beam":
			var r: Vector2 = v.arena_point(Vector2(float(b.x), float(b.y)))
			c.draw_rect(Rect2(r - Vector2(5, 4), Vector2(10, 8)), Color("2c2838"))
			c.draw_rect(Rect2(r - Vector2(5, 4), Vector2(10, 8)), STEEL, false, 1)
			c.draw_circle(r + Vector2.from_angle(float(b.angle)) * 5.0, 2.5, AMBER)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	var armed: bool = int(b.age) > int(b.arm)
	var a: float = alpha * (1.0 if armed else 0.3 + 0.35 * sin(float(b.age) * 0.5))
	match str(b.shape):
		"key":
			var dir: Vector2 = Vector2.from_angle(turn)
			var side: Vector2 = Vector2(-dir.y, dir.x)
			c.draw_arc(at - dir * 3.0, 2.6, 0, TAU, 10, Color(BRASS, a), 2)
			c.draw_line(at - dir * 0.5, at + dir * 5.0, Color(BRASS, a), 2)
			c.draw_line(at + dir * 3.5, at + dir * 3.5 + side * 2.5, Color(BRASS, a), 1)
			c.draw_line(at + dir * 5.0, at + dir * 5.0 + side * 2.0, Color(BRASS, a), 1)
			return true
		"lock":
			var q: PackedVector2Array = v.quad(at + Vector2(0, 1), float(b.w), float(b.h) * 0.8, 0.0)
			c.draw_arc(at + Vector2(0, -float(b.h) * 0.5), float(b.w) * 0.6, PI, TAU, 10, Color(STEEL, alpha), 2)
			c.draw_colored_polygon(q, Color(BRASS, alpha))
			c.draw_circle(at + Vector2(0, 1), 1.3, Color(INK, alpha))
			return true
		"chain":
			c.draw_arc(at, 2.4, 0, TAU, 8, Color(STEEL, alpha), 1)
			return true
		"folding":
			var col: Color = Color(Color("a7a2b0"), a)
			var up: Vector2 = Vector2(0, -1).rotated(turn)
			var sd: Vector2 = Vector2(1, 0).rotated(turn)
			c.draw_line(at + up * 7.0 - sd * 4.0, at + up * 7.0 + sd * 4.0, col, 2)
			c.draw_line(at + up * 7.0 - sd * 4.0, at - up * 7.0 - sd * 5.0, col, 2)
			c.draw_line(at + up * 7.0 + sd * 4.0, at - up * 7.0 + sd * 5.0, col, 2)
			c.draw_line(at - sd * 5.5, at + sd * 5.5, Color(CREAM, a), 2)
			if not armed: c.draw_rect(Rect2(at - Vector2(8, 9), Vector2(16, 18)), Color(ROSE, 0.25 + 0.3 * sin(float(b.age) * 0.5)), false, 1)
			return true
		"cart":
			c.draw_colored_polygon(v.quad(at, float(b.w), float(b.h) * 0.7, turn), Color(Color("6a6478"), alpha))
			for i: int in range(3):
				c.draw_line(at + Vector2(-4 + i * 4, -float(b.h)).rotated(turn), at + Vector2(-4 + i * 4, -float(b.h) - 5).rotated(turn), Color(Color("a7a2b0"), alpha), 2)
			c.draw_circle(at + Vector2(-4, float(b.h)).rotated(turn), 1.6, Color(STEEL, alpha))
			c.draw_circle(at + Vector2(4, float(b.h)).rotated(turn), 1.6, Color(STEEL, alpha))
			return true
		"guest":
			var col2: Color = Color(CREAM, alpha * 0.9)
			c.draw_circle(at + Vector2(0, -3), 2.4, col2)
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-4, 5), at + Vector2(-2.5, 0), at + Vector2(2.5, 0), at + Vector2(4, 5)]), col2)
			c.draw_line(at + Vector2(-4, 5), at + Vector2(4, 5), Color(LILAC, alpha), 1)
			return true
		"tally":
			c.draw_colored_polygon(v.quad(at, float(b.w), float(b.h), turn), Color(CREAM, alpha * 0.9))
			var y: float = -float(b.h) + 4.0
			while y < float(b.h) - 2.0:
				c.draw_line(at + Vector2(-5, y).rotated(turn), at + Vector2(5, y + 3).rotated(turn), Color(ROSE, alpha * 0.8), 1)
				y += 10.0
			return true
		"programme":
			var q2: PackedVector2Array = v.quad(at, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(q2, Color(CREAM, a))
			c.draw_line(at + Vector2(-3, -1).rotated(turn), at + Vector2(3, -1).rotated(turn), Color(PLUM, a), 1)
			return true
		"plane":
			var fwd: Vector2 = Vector2.from_angle(turn)
			var sd2: Vector2 = Vector2(-fwd.y, fwd.x)
			c.draw_colored_polygon(PackedVector2Array([at + fwd * 6.0, at - fwd * 4.0 + sd2 * 4.0, at - fwd * 2.0, at - fwd * 4.0 - sd2 * 4.0]), Color(CREAM, alpha))
			c.draw_line(at + fwd * 6.0, at - fwd * 2.0, Color(LILAC, alpha), 1)
			return true
	return false
