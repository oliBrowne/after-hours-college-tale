extends RefCounted
## CHIP / Confetti Hop: the mascot's rehearsal on the audience lawn. The soul
## hops between columns (lanes mode) and nothing else, so every attack is
## beatable with left / right hops alone (pointer players have two hop buttons).
## Five handmade attacks, one per turn, cycling. The lanes are re-fitted to the
## box every tick (44 px apart), so resizing the box adds or removes columns.
## The promise: Chip calls a column five times a turn and the called column
## moves each time; touching three of them keeps it (columnsReached >= 3).
## Stage 1 and 2 add a layer to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["confetti_cannon", "party_horns", "the_wave", "balloon_release", "ralphie_run"]
const PHASES: Array[int] = [0, 1, 2]
const SPACING: float = 44.0
const CALLS: Array[int] = [40, 130, 220, 310, 400]
const CALL_OPEN: int = 90
const ROW_ABOVE_FLOOR: float = 16.0
## Holding left / right hops again after this many ticks (key repeat).
const REPEAT: int = 14
const MINT: Color = Color("b9d5bc")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const ROSE: Color = Color("e8837b")
const LILAC: Color = Color("a68db8")
const GOLD: Color = Color("cfb87c")
const BROWN: Color = Color("6b4a33")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 480 + 60 * clampi(int(s.phase), 0, 2)
	s.columnsReached = 0
	s.callObj = -1
	s.callLane = -1
	s.callAt = -1000
	s.callCounted = false
	s.queue = []
	s.wqueue = []
	s.gapPlan = {}
	s.cannonKick = -100
	s.ralphie = {}
	s.calf = {}
	s.seat = -1
	s.waveDir = 1
	s.inflating = []
	s.rowAbove = 36.0 if id == "the_wave" else ROW_ABOVE_FLOOR
	match id:
		"confetti_cannon":
			s.phaseName = "Confetti Cannons"
			s.hint = "Cannons fire down every marked column. Hop to the open one; it is Chip's call."
		"party_horns":
			s.phaseName = "Party Horns"
			s.hint = "Horns unroll from the walls as far as their shadow. Streamers block a column."
		"the_wave":
			s.phaseName = "The Wave"
			s.hint = "The crowd's wave sweeps the row. Sit in the empty seat or hop through behind it."
		"balloon_release":
			s.phaseName = "Balloon Release"
			s.hint = "Balloons rise up a column, then pop on the beat. Mind the falling confetti."
		"ralphie_run":
			s.phaseName = "Ralphie Run"
			s.hint = "The buffalo paws, then charges straight down. The lawn slides under its path."
	_fit(s)
	D.set_mode(s, "lanes")

# ---------------------------------------------------------------- lanes and calls

## Columns 44 px apart, centred, as many as fit in the current box width.
static func _fit(s: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	var n: int = clampi(int(floor((float(s.box.w) - 16.0) / SPACING)) + 1, 2, 7)
	s.laneY = h.y - float(s.get("rowAbove", ROW_ABOVE_FLOOR))
	if n == s.lanes.size(): return
	var lanes: Array = []
	for i: int in range(n): lanes.append((float(i) - float(n - 1) * 0.5) * SPACING)
	s.lanes = lanes
	s.soul.lane = _nearest(s, float(s.soul.x))
	if int(s.callLane) >= 0 and int(s.callObj) >= 0:
		var o: Dictionary = s.objectives[int(s.callObj)]
		s.callLane = _nearest(s, float(o.x))

static func _nearest(s: Dictionary, x: float) -> int:
	var best: int = 0
	for i: int in range(s.lanes.size()):
		if absf(float(s.lanes[i]) - x) < absf(float(s.lanes[best]) - x): best = i
	return best

static func _lane_x(s: Dictionary, i: int) -> float:
	return float(s.lanes[clampi(i, 0, s.lanes.size() - 1)])

## World (arena) point of column i on the soul's row.
static func _lane_world(s: Dictionary, i: int) -> Vector2:
	return D.to_world(s, Vector2(_lane_x(s, i), float(s.laneY)))

static func _place_call(s: Dictionary, t: int, lane: int = -1) -> void:
	if int(s.callObj) >= 0: s.objectives[int(s.callObj)].active = false
	var n: int = s.lanes.size()
	if lane < 0:
		var here: int = int(s.soul.lane)
		var need: int = 1 if int(s.phase) == 0 else 2
		var options: Array[int] = []
		for i: int in range(n):
			if absi(i - here) >= need and absi(i - here) <= need + 1 and i != int(s.callLane): options.append(i)
		if options.is_empty():
			for i: int in range(n):
				if i != here: options.append(i)
		# Prefer a column no balloon will cross soon and no streamer hangs over.
		if s.patternId == "party_horns":
			var dry: Array[int] = []
			for i: int in options:
				if not _streamer_in(s, i): dry.append(i)
			if not dry.is_empty(): options = dry
		if s.has("busy"):
			var calm: Array[int] = []
			var busy: Array = _busy_lanes(s, t, t + 70)
			for i: int in options:
				if not busy.has(_lane_x(s, i)): calm.append(i)
			if not calm.is_empty(): options = calm
		lane = options[int(D.rand(s) * options.size()) % options.size()]
	s.callLane = lane
	s.callAt = t
	s.callCounted = false
	D.objective(s, {"kind": "touch", "x": _lane_x(s, lane), "y": float(s.laneY), "w": 9.0, "h": 12.0, "label": "CALL"})
	s.callObj = s.objectives.size() - 1

static func _calls(s: Dictionary, t: int) -> void:
	if s.patternId != "confetti_cannon":
		for at: int in CALLS:
			if t == at: _place_call(s, t)
	if int(s.callObj) >= 0:
		var o: Dictionary = s.objectives[int(s.callObj)]
		o.x = _lane_x(s, int(s.callLane)); o.y = float(s.laneY)
		if not o.done and t >= int(s.callAt) + CALL_OPEN: o.active = false

static func _count_calls(s: Dictionary) -> void:
	if int(s.callObj) < 0 or bool(s.callCounted): return
	var o: Dictionary = s.objectives[int(s.callObj)]
	if o.done:
		s.callCounted = true
		s.columnsReached = int(s.columnsReached) + 1

## The engine hops once per press. A held direction repeats every REPEAT ticks.
static func _repeat(s: Dictionary) -> void:
	if int(s.soul.lastHop) == 0:
		s.heldTicks = 0
		return
	s.heldTicks = int(s.get("heldTicks", 0)) + 1
	if int(s.heldTicks) >= REPEAT:
		s.heldTicks = 0
		s.soul.lastHop = 0

# ---------------------------------------------------------------- scheduling helpers

static func _queue(s: Dictionary, at: int, props: Dictionary) -> void:
	s.queue.append({"at": at, "props": props})

static func _queue_warn(s: Dictionary, at: int, props: Dictionary, life: int, loud: bool = false) -> void:
	s.wqueue.append({"at": at, "props": props, "life": life, "loud": loud})

static func _run_queue(s: Dictionary, t: int) -> void:
	var keep: Array = []
	for q: Dictionary in s.queue:
		if int(q.at) <= t: D.shot(s, q.props)
		else: keep.append(q)
	s.queue = keep
	var keep_w: Array = []
	for q: Dictionary in s.wqueue:
		if int(q.at) <= t: D.warn(s, q.props, int(q.life), bool(q.loud))
		else: keep_w.append(q)
	s.wqueue = keep_w

## A stream of confetti that crosses the soul's row at world x between ticks
## arrive and until (attack time). It falls straight down in arena space, so it
## stays a true column even when the box is tilted.
static func _stream(s: Dictionary, t: int, x: float, row_y: float, arrive: int, until: int, sway: float = 0.0) -> void:
	var vy: float = 4.5
	var at: int = arrive
	while at <= until:
		var lead: int = mini(30, at - t)
		var props: Dictionary = {"x": x + D.rand_range(s, -1.5, 1.5), "y": row_y - vy * lead, "vy": vy, "r": 3.0, "shape": "confetti",
			"hue": int(D.rand(s) * 4.0), "rot": D.rand(s) * TAU, "spin": 0.25, "life": 80}
		if sway > 0.0: props.wave = {"amp": sway, "freq": 0.18, "phase": D.rand(s) * TAU}
		_queue(s, at - lead, props)
		at += 3

static func _band(s: Dictionary, x: float, life: int, loud: bool = false, half: float = 12.0) -> void:
	D.warn(s, {"kind": "lane", "x": x, "w": half, "horizontal": false}, life, loud)

# ---------------------------------------------------------------- contract

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return int(s.columnsReached) >= 3

static func progress(s: Dictionary) -> String:
	return "Called columns %d/3" % mini(3, int(s.columnsReached))

static func tick(s: Dictionary, t: int) -> void:
	_fit(s)
	_repeat(s)
	var phase: int = clampi(int(s.phase), 0, 2)
	match str(s.patternId):
		"confetti_cannon": _cannon(s, t, phase)
		"party_horns":
			_horns(s, t, phase)
			_update_horns(s)
			_horn_hint(s)
		"the_wave": _wave(s, t, phase)
		"balloon_release": _balloons(s, t, phase)
		"ralphie_run": _ralphie(s, t, phase)
	_calls(s, t)
	_run_queue(s, t)

static func after(s: Dictionary, _t: int) -> void:
	_count_calls(s)

# ---------------------------------------------------------------- 1. Confetti Cannons

# Two cannons on the top corners fire down every column but one. The open
# column is Chip's call. Between volleys the box resizes, so the number of
# columns changes. Stage 1: the gap slides one column mid-volley (start in
# the first gap, hop as it moves). Stage 2: the box also tilts each volley, so
# the straight-down columns cut across a slanted lawn.
const CANNON_WIDTHS: Array[float] = [256.0, 212.0, 168.0, 256.0, 212.0]

static func _cannon(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 256.0, "h": 112.0}, 20)
	for k: int in range(CALLS.size()):
		var at: int = CALLS[k]
		if k > 0 and t == at - 26:
			D.box_to(s, {"w": CANNON_WIDTHS[k]}, 20)
			if phase >= 2: D.box_to(s, {"rot": 0.22 * (1.0 if k % 2 == 1 else -1.0)}, 20)
		if t == at: _volley(s, t, phase)

static func _volley(s: Dictionary, t: int, phase: int) -> void:
	var n: int = s.lanes.size()
	var here: int = int(s.soul.lane)
	var lo: int = 1 if phase == 0 else 2
	var options: Array[int] = []
	for i: int in range(n):
		if absi(i - here) >= lo and absi(i - here) <= lo + 1: options.append(i)
	if options.is_empty():
		for i: int in range(n):
			if i != here: options.append(i)
	var first: int = options[int(D.rand(s) * options.size()) % options.size()]
	var second: int = first
	if phase >= 1:
		var step: int = 1 if D.rand(s) < 0.5 else -1
		if first + step < 0 or first + step >= n: step = -step
		second = first + step
	var arrive: int = t + 46
	s.cannonKick = arrive
	s.gapPlan = {"a": first, "b": second, "from": t, "arrive": arrive, "switch": arrive + 14, "until": arrive + 34}
	_place_call(s, t, second)
	D.banner(s, "FIRE IN THE HOLE", 40)
	var beeped: bool = false
	for i: int in range(n):
		var p: Vector2 = _lane_world(s, i)
		var sway: float = 3.0 if phase >= 1 else 0.0
		var loud: bool = not beeped and i != first and i != second
		if loud: beeped = true
		if i == first and i == second: continue
		if i == second:
			# The new gap opens shortly after the volley starts.
			_band(s, p.x, arrive - t)
			_stream(s, t, p.x, p.y, arrive, arrive + 6, sway)
		elif i == first:
			# The old gap closes once the new one is open.
			_queue_warn(s, arrive - 18, {"kind": "lane", "x": p.x, "w": 12.0, "horizontal": false}, 40)
			_stream(s, t, p.x, p.y, arrive + 22, arrive + 34, sway)
		else:
			_band(s, p.x, arrive - t, loud)
			_stream(s, t, p.x, p.y, arrive, arrive + 34, sway)

# ---------------------------------------------------------------- 2. Party Horns

# Party horns unroll along the row from either wall, as deep as their dashed
# shadow, on the beat. Streamers drift down single columns and block them for a
# while, so the safe column is wherever the horn does not reach and no streamer
# hangs. Stage 1: a second horn answers from the other wall. Stage 2: the lawn
# slides left and right under it all.
static func _horns(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 256.0, "h": 108.0}, 20)
	var every: int = 50
	if t >= 30 and t < 440 and (t - 30) % every == 0:
		var n: int = s.lanes.size()
		var left_first: bool = int((t - 30) / every) % 2 == 0
		var reach: int = 2 + int(D.rand(s) * float(n - 3))
		reach = clampi(reach, 1, n - 2)
		var answer: int = 0
		if phase >= 1 and int((t - 30) / every) % 2 == 1:
			answer = clampi(n - 1 - reach - int(D.rand(s) * 2.0), 1, n - 2)
			for i: int in range(n):
				if _streamer_in(s, i): answer = 0
		# Never cover every column a streamer leaves open.
		for guard: int in range(8):
			var lreach: int = reach if left_first else answer
			var rreach: int = answer if left_first else reach
			var open_ok: bool = false
			var here: int = int(s.soul.lane)
			for i: int in range(lreach, n - rreach):
				if _streamer_in(s, i): continue
				var crosses: bool = false
				for j: int in range(mini(i, here) + 1, maxi(i, here)):
					if _streamer_in(s, j): crosses = true
				if not crosses: open_ok = true
			if open_ok: break
			if reach > 1: reach -= 1
			elif answer > 0: answer -= 1
		_horn(s, -1.0 if left_first else 1.0, reach, 46)
		if answer > 0: _horn(s, 1.0 if left_first else -1.0, answer, 70)
		if phase >= 2:
			D.box_to(s, {"cx": 128.0 + (22.0 if left_first else -22.0)}, 30, 4)
	if t % 80 == 40 and t > 30 and t < 430:
		_streamer(s, t, phase)

static func _horn(s: Dictionary, side: float, reach: int, warn_ticks: int) -> void:
	var n: int = s.lanes.size()
	var deepest: int = reach - 1 if side < 0.0 else n - reach
	var edge: float = _lane_x(s, deepest) + (16.0 if side < 0.0 else -16.0)
	var length: float = absf(D.half(s).x * side - edge)
	D.shot(s, {"space": "box", "x": side * D.half(s).x, "y": float(s.laneY), "collide": "rect", "w": 0.5, "h": 5.0, "shape": "horn",
		"horn": {"side": side, "length": length, "warn": warn_ticks}, "arm": warn_ticks, "life": warn_ticks + 40})
	D.warn(s, {"kind": "edge", "space": "box", "x": side * (D.half(s).x - 6.0), "y": float(s.laneY) - 12.0, "dir": Vector2(-side, 0)}, warn_ticks, true)

## QA autopilot hint: the bot only looks 18 ticks ahead, the horn tells 42.
## When the soul's column will be covered soon, point it at the nearest column
## that will not be (the called one if possible).
static func _horn_hint(s: Dictionary) -> void:
	var n: int = s.lanes.size()
	var bad: Array[bool] = []
	var ribbon: Array[bool] = []
	for i: int in range(n):
		bad.append(false); ribbon.append(false)
	var h: Vector2 = D.half(s)
	for b: Dictionary in s.bullets:
		if b.shape == "horn":
			var hn: Dictionary = b.horn
			var until_live: int = int(hn.warn) - int(b.age)
			if until_live > 30 or int(b.age) > int(hn.warn) + 30: continue
			var tip: float = float(hn.side) * h.x - float(hn.side) * float(hn.length)
			for i: int in range(n):
				var x: float = _lane_x(s, i)
				if (float(hn.side) < 0.0 and x < tip + 6.0) or (float(hn.side) > 0.0 and x > tip - 6.0): bad[i] = true
		elif b.shape == "streamer":
			var bottom: float = float(b.y) + float(b.h)
			if bottom > float(s.laneY) - 55.0 and float(b.y) - float(b.h) < float(s.laneY) + 6.0:
				bad[_nearest(s, float(b.x))] = true
				ribbon[_nearest(s, float(b.x))] = true
	var here: int = int(s.soul.lane)
	if not bad[here]:
		# Safe here: only head for the call if the way there stays clear.
		s.botGoal = null
		var call: int = int(s.callLane)
		if int(s.callObj) >= 0 and s.objectives[int(s.callObj)].active and not s.objectives[int(s.callObj)].done and call >= 0 and call < n:
			for j: int in range(mini(call, here), maxi(call, here) + 1):
				if bad[j]: s.botGoal = Vector2(_lane_x(s, here), float(s.laneY))
		return
	var best: int = -1
	for i: int in range(n):
		if bad[i]: continue
		var blocked: bool = false
		for j: int in range(mini(i, here) + 1, maxi(i, here)):
			if ribbon[j]: blocked = true
		if blocked: continue
		if best < 0 or absi(i - here) < absi(best - here) or (absi(i - here) == absi(best - here) and i == int(s.callLane)): best = i
	s.botGoal = Vector2(_lane_x(s, best), float(s.laneY)) if best >= 0 else null

## Will a streamer hang in this column while the next horns are out (42-100 ticks from now)?
static func _streamer_in(s: Dictionary, lane: int) -> bool:
	for b: Dictionary in s.bullets:
		if b.shape != "streamer" or int(b.lane) != lane: continue
		var top_late: float = float(b.y) - float(b.h) + float(b.vy) * 42.0
		var bottom_late: float = float(b.y) + float(b.h) + float(b.vy) * 100.0
		if top_late < float(s.laneY) + 6.0 and bottom_late > float(s.laneY) - 6.0: return true
	return false

static func _streamer(s: Dictionary, _t: int, phase: int) -> void:
	var n: int = s.lanes.size()
	var lane: int = int(D.rand(s) * n) % n
	var h: Vector2 = D.half(s)
	var speed: float = 1.5 + (0.3 if phase >= 2 else 0.0)
	D.shot(s, {"space": "box", "x": _lane_x(s, lane), "y": -h.y - 40.0, "vy": speed, "collide": "rect", "w": 3.0, "h": 22.0, "shape": "streamer",
		"hue": int(D.rand(s) * 4.0), "lane": lane, "life": 260})

## Horns follow their wall and their own timeline (unroll, hold, roll back).
static func _update_horns(s: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	for b: Dictionary in s.bullets:
		if b.shape != "horn": continue
		var hn: Dictionary = b.horn
		var age: int = int(b.age) - int(hn.warn)
		var e: float = 0.0
		if age >= 0:
			if age < 10: e = float(hn.length) * float(age + 1) / 10.0
			elif age < 26: e = float(hn.length)
			else: e = float(hn.length) * clampf(1.0 - float(age - 26) / 9.0, 0.0, 1.0)
		var wall: float = float(hn.side) * h.x
		b.w = maxf(0.5, e * 0.5)
		b.x = wall - float(hn.side) * e * 0.5
		b.y = float(s.laneY)
		if age == 10 and int(s.phase) >= 1 and not bool(hn.get("puffed", false)):
			# The horn's tip puffs confetti one column further on.
			hn.puffed = true
			var tip_x: float = wall - float(hn.side) * float(hn.length)
			for i: int in range(3):
				D.shot(s, {"space": "box", "x": tip_x, "y": float(s.laneY) - 4.0, "vx": -float(hn.side) * (0.62 + i * 0.08), "vy": -2.6, "ay": 0.13,
					"r": 2.6, "shape": "confetti", "hue": i, "rot": D.rand(s) * TAU, "spin": 0.3, "life": 90})
		hn.e = e

# ---------------------------------------------------------------- 3. The Wave

# The crowd's wave sweeps the row column by column: each fan's arms shoot up
# through it in turn. Sit in the one empty seat (lilac), or hop through right
# behind the crest. Between crests a cannon fires single columns behind it.
# Stage 1: every other wave has no empty seat. Stage 2: double crest, and the
# lawn narrows before the last wave.
static func _wave(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 256.0, "h": 112.0}, 20)
	var step: int = 20 if phase == 0 else 18
	var starts: Array = [40, 180, 360] if phase >= 2 else [40, 180, 320]
	if phase >= 2 and t == 320: D.box_to(s, {"w": 168.0}, 16)
	for k: int in range(starts.size()):
		var at: int = starts[k]
		var n: int = s.lanes.size()
		if t == at - 40:
			s.waveDir = 1 if k % 2 == 0 else -1
			s.seated = phase == 0 or k % 2 == 0
			s.seat = -1
			D.banner(s, "THE WAVE!" if s.seated else "NO EMPTY SEATS", 40)
			var edge_x: float = -float(s.waveDir) * (D.half(s).x - 6.0)
			D.warn(s, {"kind": "edge", "space": "box", "x": edge_x, "y": float(s.laneY), "dir": Vector2(float(s.waveDir), 0)}, 40, true)
		if t == at and bool(s.get("seated", false)): s.seat = 1 + int(D.rand(s) * float(n - 2))
		if t >= at and t < at + n * step and (t - at) % step == 0:
			var index: int = int((t - at) / step)
			var lane: int = index if int(s.waveDir) > 0 else n - 1 - index
			if lane != int(s.seat): _finger(s, lane)
			if phase >= 2:
				var echo: int = lane - 3 * int(s.waveDir)
				if echo >= 0 and echo < n and echo != int(s.seat): _finger(s, echo)
			# Cannon shots land two columns behind the crest.
			if index % 2 == 1 and index >= 1:
				var behind: int = lane - 2 * int(s.waveDir)
				if behind >= 0 and behind < n:
					var p: Vector2 = _lane_world(s, behind)
					_band(s, p.x, 44)
					_stream(s, t, p.x, p.y, t + 44, t + 56)
		if t == at + n * step + 6: s.seat = -1

## A fan's foam finger shoots up through the row and back (about 10 ticks of danger).
static func _finger(s: Dictionary, lane: int) -> void:
	D.shot(s, {"space": "box", "x": _lane_x(s, lane), "y": float(s.laneY) + 24.0, "vy": -4.15, "ay": 0.5, "collide": "rect", "w": 6.0, "h": 10.0,
		"shape": "finger", "life": 17, "lane": lane})

# ---------------------------------------------------------------- 4. Balloon Release

# Balloons inflate under the floor (the growing arc is the tell), rise up their
# column through the row, and pop high up into a little shower of confetti that
# falls back down the same column. Seats open two at a time (3 columns, then
# 5) so old columns stay put. Stage 1: tied pairs, and the outer seats close
# near the end. Stage 2: balloon arches with one gap drift down over the row.
# A ledger of busy windows per column keeps at least one column free.
static func _balloons(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 124.0, "h": 112.0}, 20)
		s.busy = []
	if t == 150:
		D.box_to(s, {"w": 212.0}, 24)
		D.banner(s, "MORE SEATS", 40)
	if phase >= 1 and t == 360:
		D.banner(s, "SEATS CLOSING", 40)
		D.warn(s, {"kind": "curtain"}, 30, true)
		D.box_to(s, {"w": 124.0}, 24, 30)
	var every: int = 22 if phase == 0 else 26
	var quiet: bool = (t > 126 and t < 176) or (phase >= 1 and t > 318 and t < 404)
	if t % every == 4 and t > 10 and t < 420 and not quiet:
		var n: int = s.lanes.size()
		var lane: int = int(D.rand(s) * n) % n
		if int(t / every) % 3 == 0: lane = int(s.soul.lane)
		var placed: int = _try_balloon(s, t, lane)
		if phase >= 1 and int(t / every) % 3 == 1 and placed >= 0:
			var other: int = placed + (2 if placed + 2 < n else -2)
			if other >= 0 and other < n: _try_balloon(s, t, other, false)
	var keep: Array = []
	for f: Dictionary in s.inflating:
		if int(f.at) == t:
			var h: Vector2 = D.half(s)
			D.shot(s, {"space": "box", "x": float(f.x), "y": h.y + 10.0, "vy": -0.8, "r": 7.0, "shape": "balloon", "hue": int(f.hue), "life": 400})
		else: keep.append(f)
	s.inflating = keep
	for b: Dictionary in s.bullets:
		if b.shape == "balloon" and not b.get("arch", false) and float(b.y) < -8.0 and not b.dead:
			b.dead = true
			D.effect(s, "pulse", D.to_world(s, Vector2(float(b.x), float(b.y))), 14)
			for i: int in range(5):
				D.shot(s, {"space": "box", "x": float(b.x), "y": float(b.y), "vx": -0.36 + i * 0.18, "vy": -1.0, "ay": 0.045, "r": 2.6, "shape": "confetti",
					"hue": int(b.hue) if i % 2 == 0 else int(D.rand(s) * 4.0), "rot": D.rand(s) * TAU, "spin": 0.2, "life": 160})
	if phase >= 2 and t % 120 == 60 and t < 330:
		_arch(s, t)

## Busy windows (attack ticks) per column x: a balloon crossing the row, its
## confetti coming back down, an arch passing.
static func _busy_lanes(s: Dictionary, a: int, b: int) -> Array:
	var out: Array = []
	for w: Dictionary in s.busy:
		if int(w.b) + 10 >= a and int(w.a) - 10 <= b and not out.has(float(w.x)): out.append(float(w.x))
	return out

static func _free_with(s: Dictionary, x: float, a: int, b: int) -> bool:
	var busy: Array = _busy_lanes(s, a, b)
	if not busy.has(x): busy.append(x)
	var free: int = 0
	for lx: Variant in s.lanes:
		if not busy.has(float(lx)): free += 1
	return free >= 1

static func _try_balloon(s: Dictionary, t: int, lane: int, search: bool = true) -> int:
	var n: int = s.lanes.size()
	for k: int in range(n if search else 1):
		var i: int = (lane + k) % n
		var x: float = _lane_x(s, i)
		var release: int = t + 40
		if _free_with(s, x, release + 18, release + 47) and _free_with(s, x, release + 165, release + 182):
			s.busy.append({"x": x, "a": release + 18, "b": release + 47})
			s.busy.append({"x": x, "a": release + 165, "b": release + 182})
			s.inflating.append({"x": x, "at": release, "born": t, "hue": int(D.rand(s) * 4.0)})
			return i
	return -1

static func _arch(s: Dictionary, t: int) -> void:
	var n: int = s.lanes.size()
	var a: int = t + 104
	var b: int = t + 130
	var busy: Array = _busy_lanes(s, a, b)
	var options: Array[int] = []
	for i: int in range(n):
		if not busy.has(_lane_x(s, i)): options.append(i)
	if options.is_empty(): return
	var gap: int = options[int(D.rand(s) * options.size()) % options.size()]
	var h: Vector2 = D.half(s)
	for i: int in range(n):
		if i == gap: continue
		s.busy.append({"x": _lane_x(s, i), "a": a, "b": b})
		D.shot(s, {"space": "box", "x": _lane_x(s, i), "y": -h.y - 10.0, "vy": 0.9, "r": 6.0, "shape": "balloon", "hue": i % 4, "life": 200, "arch": true})
	D.banner(s, "BALLOON ARCH", 40)

# ---------------------------------------------------------------- 5. Ralphie Run

# Ralphie trots along the top, paws the ground over a column, then charges
# straight down. While it paws the whole lawn slides, so the column under the
# marked path changes. Stage 1: a calf charges between Ralphie's runs. Stage 2:
# the final stampede marks three paths at once.
static func _ralphie(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 256.0, "h": 104.0}, 20)
		s.ralphie = {"x": 128.0, "from": 128.0, "to": 128.0, "state": "trot", "since": 0, "size": 1.0}
		s.calf = {"x": 20.0, "from": 20.0, "to": 20.0, "state": "idle", "since": 0, "size": 0.7}
	var cycle: int = 72
	if t >= 20 and t < 420 and (t - 20) % cycle == 0:
		var final: bool = phase >= 2 and t >= 20 + cycle * 4
		_aim(s, t, s.ralphie, final)
	if phase >= 1 and t >= 56 and t < 400 and (t - 56) % cycle == 0:
		_aim(s, t, s.calf, false)
	for r: Dictionary in [s.ralphie, s.calf]:
		if r.is_empty(): continue
		var age: int = t - int(r.since)
		match str(r.state):
			"trot":
				r.x = lerpf(float(r.from), float(r.to), clampf(float(age) / 14.0, 0.0, 1.0))
				if age >= 14: r.state = "paw"; r.since = t
			"paw":
				if age >= 30:
					r.state = "charge"; r.since = t
					for x: float in r.get("paths", [float(r.x)]):
						var top: float = D.centre(s).y - D.half(s).y - 24.0
						D.shot(s, {"x": x, "y": top, "vy": 6.5, "collide": "rect", "w": 11.0 * float(r.size) + 2.0, "h": 14.0 * float(r.size), "shape": "buffalo", "size": float(r.size), "life": 40})
					D.effect(s, "pulse", Vector2(float(r.x), D.centre(s).y - D.half(s).y - 16.0), 16)
					r.clods = t + 17
			"charge":
				if t == int(r.get("clods", -1)) and is_same(r, s.ralphie):
					# Turf flies out of the hoofprints and lands one column to each side.
					for x: float in r.get("paths", [float(r.x)]):
						var row: Vector2 = D.to_world(s, Vector2(0, float(s.laneY)))
						for side: float in [-1.0, 1.0]:
							D.shot(s, {"x": x, "y": row.y, "vx": side * SPACING / 30.0, "vy": -3.0, "ay": 0.2, "r": 3.5, "shape": "clod", "rot": D.rand(s) * TAU, "spin": 0.15, "life": 60})
				if age >= 24: r.state = "idle"

static func _aim(s: Dictionary, t: int, r: Dictionary, stampede: bool) -> void:
	# Slide the lawn first, then aim where the soul will be if it stands still.
	var slide: float = 0.0
	if is_same(r, s.ralphie):
		var cx: float = float(s.box.cx)
		var to_cx: float = 128.0 + (30.0 if cx <= 128.0 else -30.0) * (1.0 if D.rand(s) < 0.75 else 0.0)
		slide = to_cx - cx
		D.box_to(s, {"cx": to_cx}, 30, 16)
	var soul_after: Vector2 = D.soul_world(s) + Vector2(slide, 0)
	var paths: Array = [soul_after.x]
	if stampede:
		var n: int = s.lanes.size()
		var here: int = int(s.soul.lane)
		var picks: Array[int] = [here]
		for i: int in range(n):
			if picks.size() >= 3: break
			var j: int = (here + 2 + i * 2) % n
			if j != here and not picks.has(j) and absi(j - here) != 1: picks.append(j)
		paths = []
		for j: int in picks: paths.append(_lane_world(s, j).x + slide)
	r.from = float(r.x); r.to = clampf(float(paths[0]), -10.0, 266.0)
	r.state = "trot"; r.since = t
	r.paths = paths
	for x: float in paths:
		_band(s, float(x), 62, is_same(r, s.ralphie), 15.0)
	if stampede: D.banner(s, "STAMPEDE", 44)

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	# Mown lawn stripes and the crowd's front row along the floor.
	for i: int in range(-4, 5):
		var x: float = i * 40.0
		c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(x - 20.0, -h.y), Vector2(20.0, h.y * 2.0))), Color(0.35, 0.5, 0.35, 0.06))
	c.draw_line(v.box_point(Vector2(-h.x, float(s.laneY) + 9.0)), v.box_point(Vector2(h.x, float(s.laneY) + 9.0)), Color(GOLD, 0.25), 1)
	# Chip's call: the whole column glows faintly.
	if (bool(s.promised)) and int(s.callObj) >= 0:
		var o: Dictionary = s.objectives[int(s.callObj)]
		if o.active and not o.done:
			c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(float(o.x) - 13.0, -h.y), Vector2(26.0, h.y * 2.0))), Color(MINT, 0.07))
	if s.patternId == "confetti_cannon" and not s.gapPlan.is_empty():
		_draw_gap_plan(c, s, v)
	if s.patternId == "the_wave":
		_draw_crowd(c, s, v)
	if s.patternId == "party_horns":
		for b: Dictionary in s.bullets:
			if b.shape == "horn" and int(b.age) <= int(b.horn.warn):
				var hn: Dictionary = b.horn
				var wall: float = float(hn.side) * h.x
				var tip: float = wall - float(hn.side) * float(hn.length)
				var p: float = float(b.age) / float(hn.warn)
				var y: float = float(s.laneY)
				var x: float = wall
				while absf(x - wall) < float(hn.length):
					var x2: float = x - float(hn.side) * 5.0
					c.draw_line(v.box_point(Vector2(x, y - 5.0)), v.box_point(Vector2(x2, y - 5.0)), Color(ROSE, 0.45 + 0.5 * p), 1)
					c.draw_line(v.box_point(Vector2(x, y + 5.0)), v.box_point(Vector2(x2, y + 5.0)), Color(ROSE, 0.45 + 0.5 * p), 1)
					x -= float(hn.side) * 9.0
				c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(minf(wall, tip), y - 5.0), Vector2(absf(wall - tip), 10.0))), Color(ROSE, 0.08 + 0.12 * p))
				c.draw_line(v.box_point(Vector2(tip, y - 8.0)), v.box_point(Vector2(tip, y + 8.0)), Color(ROSE, 0.6 + 0.4 * p), 2)
				# The rolled-up horn waits at the wall.
				var coil: Vector2 = v.box_point(Vector2(wall - float(hn.side) * 6.0, y))
				c.draw_arc(coil, 4.0 + p * 1.5, 0, TAU, 12, Color(_hue(1), 0.9), 2)
	if s.patternId == "balloon_release":
		var t: int = int(s.clock) - int(s.leadIn)
		for f: Dictionary in s.inflating:
			var p2: float = clampf(float(t - int(f.born)) / 40.0, 0.0, 1.0)
			var at: Vector2 = v.box_point(Vector2(float(f.x), h.y - 3.0))
			c.draw_arc(at, 3.0 + p2 * 5.0, PI, TAU, 10, Color(_hue(int(f.hue)), 0.4 + 0.5 * p2), 2)

static func _draw_gap_plan(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var g: Dictionary = s.gapPlan
	var t: int = int(s.clock) - int(s.leadIn)
	if t > int(g.until) or int(g.a) >= s.lanes.size() or int(g.b) >= s.lanes.size(): return
	var h: Vector2 = D.half(s)
	var y: float = float(s.laneY)
	for which: String in ["a", "b"]:
		var lane: int = int(g[which])
		var open: bool = (which == "a" and t < int(g.arrive) + 22) or (which == "b" and t >= int(g.arrive) + 7)
		if g.a == g.b: open = true
		if not open: continue
		var x: float = _lane_x(s, lane)
		var poly: PackedVector2Array = v.box_rect_poly(Rect2(Vector2(x - 14.0, -h.y + 2.0), Vector2(28.0, h.y * 2.0 - 4.0)))
		c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(CREAM, 0.35), 1)
	if int(g.a) != int(g.b):
		var a: Vector2 = v.box_point(Vector2(_lane_x(s, int(g.a)), y - 20.0))
		var b: Vector2 = v.box_point(Vector2(_lane_x(s, int(g.b)), y - 20.0))
		var dir: Vector2 = (b - a).normalized()
		c.draw_line(a + dir * 6.0, b - dir * 6.0, Color(CREAM, 0.6), 1)
		v.chevron(c, b - dir * 6.0, dir, Color(CREAM, 0.8))

static func _draw_crowd(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var y0: float = float(s.laneY)
	c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(-h.x, y0 + 12.0), Vector2(h.x * 2.0, h.y - y0 - 12.0))), Color(0.16, 0.13, 0.22, 0.9))
	for i: int in range(s.lanes.size()):
		var x: float = _lane_x(s, i)
		var finger: Dictionary = {}
		for b: Dictionary in s.bullets:
			if b.shape == "finger" and int(b.lane) == i: finger = b
		var lift: float = 0.0 if finger.is_empty() else clampf((y0 + 24.0 - float(finger.y)) * 0.35, 0.0, 6.0)
		var head: Vector2 = v.box_point(Vector2(x, y0 + 22.0 - lift))
		if i == int(s.seat):
			var seat: Vector2 = v.box_point(Vector2(x, y0 + 24.0))
			c.draw_rect(Rect2(seat + Vector2(-8, 0), Vector2(16, 5)), Color(LILAC, 0.9), false, 1)
			c.draw_line(seat + Vector2(-8, 0), seat + Vector2(-8, -10), Color(LILAC, 0.9), 1)
			v.text(c, seat + Vector2(0, -12), "SEAT", Color(LILAC, 0.9), 60.0)
			continue
		c.draw_circle(head + Vector2(0, 8), 6.0, Color(0.3, 0.24, 0.38))
		c.draw_circle(head, 4.0, Color(0.42, 0.33, 0.3))
		c.draw_arc(head, 4.0, PI, TAU, 8, Color(GOLD, 0.6), 1)
		if not finger.is_empty():
			var tip: Vector2 = v.box_point(Vector2(x, float(finger.y) + 6.0))
			c.draw_line(head + Vector2(-4, 4), tip + Vector2(-3, 0), Color(0.42, 0.33, 0.3), 2)
			c.draw_line(head + Vector2(4, 4), tip + Vector2(3, 0), Color(0.42, 0.33, 0.3), 2)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	if s.patternId == "confetti_cannon":
		var t: int = int(s.clock) - int(s.leadIn)
		var kick: float = 0.0
		if t >= int(s.cannonKick) - 30 and t <= int(s.cannonKick) + 30: kick = sin(float(t) * 1.3) * 1.5
		for side: float in [-1.0, 1.0]:
			var base: Vector2 = v.box_point(Vector2(side * (h.x - 10.0), -h.y - 9.0)) + Vector2(0, kick)
			var dir: Vector2 = Vector2(-side * 0.45, 1.0).normalized().rotated(float(s.box.rot))
			var side_v: Vector2 = Vector2(-dir.y, dir.x)
			var poly: PackedVector2Array = PackedVector2Array([base - side_v * 5.0 - dir * 4.0, base + side_v * 5.0 - dir * 4.0, base + side_v * 4.0 + dir * 10.0, base - side_v * 4.0 + dir * 10.0])
			c.draw_colored_polygon(poly, Color("3a2f45"))
			c.draw_polyline(poly + PackedVector2Array([poly[0]]), GOLD, 1)
			c.draw_circle(base - dir * 5.0, 3.0, Color("2a2333"))
	if s.patternId == "ralphie_run":
		for r: Dictionary in [s.ralphie, s.calf]:
			if r.is_empty() or str(r.state) in ["idle", "charge"]: continue
			var top: float = D.centre(s).y - h.y - 16.0
			var at: Vector2 = v.arena_point(Vector2(float(r.x), top))
			var paw: bool = str(r.state) == "paw"
			var bob: float = sin(float(s.clock) * (0.9 if paw else 0.5)) * (2.0 if paw else 1.0)
			_draw_buffalo(c, at + Vector2(0, bob), float(r.size), 1.0, true)
			if paw:
				for i: int in range(3):
					var p: float = fposmod(float(s.clock) * 0.06 + i * 0.33, 1.0)
					c.draw_circle(at + Vector2(-10.0 + i * 10.0, 9.0 - p * 6.0), 1.5 + p * 2.0, Color(0.7, 0.6, 0.45, 0.6 * (1.0 - p)))

static func _hue(i: int) -> Color:
	var colours: Array[Color] = [AMBER, Color("8fb3ea"), ROSE, LILAC]
	return colours[posmod(i, 4)]

static func _draw_buffalo(c: CanvasItem, at: Vector2, size: float, alpha: float, facing_down: bool) -> void:
	var k: float = size
	var body: PackedVector2Array = []
	for i: int in range(12):
		var a: float = i * TAU / 12.0
		body.append(at + Vector2(cos(a) * 12.0 * k, sin(a) * 9.0 * k))
	c.draw_colored_polygon(body, Color(BROWN, alpha))
	var head: Vector2 = at + Vector2(0, (8.0 if facing_down else -8.0) * k)
	c.draw_circle(head, 6.0 * k, Color(Color("4a3222"), alpha))
	for side: float in [-1.0, 1.0]:
		c.draw_polyline(PackedVector2Array([head + Vector2(side * 4.0 * k, -2.0 * k), head + Vector2(side * 9.0 * k, -4.0 * k), head + Vector2(side * 9.0 * k, -8.0 * k)]), Color(CREAM, alpha), 2)
	c.draw_line(at + Vector2(-9.0 * k, -6.0 * k), at + Vector2(9.0 * k, -6.0 * k), Color(GOLD, 0.7 * alpha), 2)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"horn":
			var hn: Dictionary = b.horn
			var e: float = float(hn.get("e", 0.0))
			if e <= 0.5: return true
			var side: float = float(hn.side)
			var dir: Vector2 = Vector2(-side, 0).rotated(turn)
			var up: Vector2 = Vector2(0, -1).rotated(turn)
			var base: Vector2 = at - dir * e * 0.5
			var stripes: int = maxi(1, int(e / 8.0))
			for i: int in range(stripes):
				var a: Vector2 = base + dir * (e * float(i) / float(stripes))
				var b2: Vector2 = base + dir * (e * float(i + 1) / float(stripes))
				c.draw_line(a, b2, Color(_hue(i), alpha), 8)
			var tip: Vector2 = base + dir * e
			c.draw_circle(tip, 4.5, Color(CREAM, alpha))
			c.draw_line(base + up * 6.0, base - up * 6.0, Color(GOLD, alpha), 3)
			return true
		"streamer":
			var hh: float = float(b.h)
			var col: Color = _hue(int(b.get("hue", 0)))
			col.a = alpha
			var pts: PackedVector2Array = []
			for i: int in range(9):
				var y: float = -hh + hh * 2.0 * float(i) / 8.0
				pts.append(at + Vector2(sin(float(b.age) * 0.15 + i * 0.9) * 2.0, y).rotated(turn))
			c.draw_polyline(pts, col, 4)
			return true
		"finger":
			# Foam finger: a gold mitt with the index finger up; the drawn shape is the hitbox.
			var col2: Color = Color(Color("e0b84a"), alpha)
			var hw: float = float(b.w); var hh: float = float(b.h)
			c.draw_colored_polygon(v.quad(at + Vector2(0, hh * 0.35).rotated(turn), hw, hh * 0.65, turn), col2)
			c.draw_colored_polygon(v.quad(at + Vector2(-1.0, -hh * 0.5).rotated(turn), 2.2, hh * 0.5, turn), col2)
			c.draw_line(at + Vector2(-hw, hh * 0.1).rotated(turn), at + Vector2(hw, hh * 0.1).rotated(turn), Color(Color("1a1a2a"), alpha), 1)
			return true
		"balloon":
			var col3: Color = _hue(int(b.get("hue", 0)))
			var flash: bool = float(b.y) < -10.0 and int(b.age) % 10 < 5 and not b.get("arch", false)
			if flash: col3 = col3.lerp(Color.WHITE, 0.4)
			col3.a = alpha
			var r: float = float(b.r)
			var pts2: PackedVector2Array = []
			for i: int in range(12):
				var a2: float = i * TAU / 12.0
				pts2.append(at + Vector2(cos(a2) * r * 0.9, sin(a2) * r * 1.1).rotated(turn))
			c.draw_colored_polygon(pts2, col3)
			c.draw_circle(at + Vector2(-r * 0.35, -r * 0.4).rotated(turn), 1.5, Color(1, 1, 1, 0.6 * alpha))
			c.draw_line(at + Vector2(0, r * 1.1).rotated(turn), at + Vector2(1.5, r * 1.1 + 8.0).rotated(turn), Color(CREAM, 0.6 * alpha), 1)
			return true
		"buffalo":
			_draw_buffalo(c, at, float(b.get("size", 1.0)), alpha, true)
			return true
		"clod":
			c.draw_colored_polygon(v.quad(at, 3.5, 2.6, turn), Color(Color("5a4630"), alpha))
			c.draw_line(at + Vector2(-2, -3).rotated(turn), at + Vector2(-1, -5).rotated(turn), Color(Color("7aa36b"), alpha), 1)
			c.draw_line(at + Vector2(1, -3).rotated(turn), at + Vector2(2, -5).rotated(turn), Color(Color("7aa36b"), alpha), 1)
			return true
	return false
