extends RefCounted
## PROFESSOR ERIC: a warm, endlessly enthusiastic signal-integrity professor,
## stuck at 1 AM on the Engineering test floor in a "one more measurement"
## loop. His attacks are his oscilloscope traces and the circuit effects he
## loves to explain, drawn so anyone can read them: a step edge that rings,
## crosstalk between neighbouring traces, ground bounce when every output
## switches at once, return current detouring around a slot in the plane, and
## an eye diagram that opens and closes on the beat. One attack per turn,
## cycling in order; each opens with one of his rules of thumb.
## The promise (Test Points): three probe points appear one after another;
## stand on each and press confirm while promised. Each appears no earlier than
## tick 40 + 100 per probe and 24 ticks after the last was probed, sits where
## the attack's soul mode can reach it, and waits for as long as it takes.
## Phase 1 (from the second cycle) adds a layer to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["ringing", "crosstalk", "ground_bounce", "return_path", "eye_diagram"]
const PHASES: Array[int] = [0, 1]
const PROBES: int = 3

const SCREEN: Color = Color("06120e")
const GRID: Color = Color("2f6a52")
const PHOSPHOR: Color = Color("8cf5a0")
const YELLOW: Color = Color("f2e46b")
const CYAN: Color = Color("6fe3f0")
const PCB: Color = Color("17442f")
const PCB_DARK: Color = Color("0d2a1e")
const COPPER: Color = Color("d08a4c")
const HOT: Color = Color("ffb35c")
const SILK: Color = Color("e9ecd8")
const ROSE: Color = Color("e8837b")
const MAGENTA: Color = Color("e889d8")
const INK: Color = Color("0d101c")
const MINT: Color = Color("b9d5bc")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	var phase: int = clampi(int(s.phase), 0, 1)
	s.patternId = id
	s.length = 460 + 40 * phase
	s.botGoal = null
	s.bannerColor = YELLOW
	s.queue = []
	s.safe = []
	match id:
		"ringing":
			s.phaseName = "Ringing"
			s.hint = "Each step edge overshoots and rings. Clear the yellow band before it sweeps by. Probe: Z."
			s.rule = "BW ~ 0.35 / RISE TIME"
			s.sweeps = []
		"crosstalk":
			s.phaseName = "Crosstalk"
			s.hint = "The aggressor fires down a red lane; its neighbours echo from both ends. Probe with Z."
			s.rule = "SPACE TRACES 3W APART"
			s.events = []
		"ground_bounce":
			s.phaseName = "Ground Bounce"
			s.hint = "Turned blue: up or confirm jumps. When every output switches, the floor bounces. Probe mid-air."
			s.rule = "~1 nH PER mm OF LEAD"
			s.pinAt = [-99, -99, -99, -99, -99, -99, -99, -99, -99]
			s.soul.x = 0.0
			D.set_mode(s, "blue")
		"return_path":
			s.phaseName = "Return Path"
			s.hint = "Return current detours around the slot. Ride it while the slot radiates noise. Probe: Z."
			s.rule = "NEVER ROUTE OVER A GAP"
			s.drills = _rp_schedule(phase)
		"eye_diagram":
			s.phaseName = "Eye Diagram"
			s.hint = "Stay inside the eye: it closes on the beat and slips sideways. Probe test points with Z."
			s.rule = "MEASURE, DON'T GUESS"
			s.eye = {"x0": 0.0, "x1": 0.0, "xs": 0, "xd": 1, "y0": 0.0, "y1": 0.0, "ys": 0, "yd": 1, "slip": 0}
	for i: int in range(PROBES):
		var o: Dictionary = D.objective(s, {"kind": "confirm", "r": 13.0, "label": "probe", "active": false, "x": 0.0, "y": 0.0})
		if id == "ground_bounce":
			# Probes hang at jump height: a tall box you pass through mid-jump.
			o.w = 12.0; o.h = 15.0

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return _probed(s) >= PROBES

static func progress(s: Dictionary) -> String:
	return "Test points probed %d/%d" % [_probed(s), PROBES]

static func _probed(s: Dictionary) -> int:
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	return count

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	if t == 0: D.banner(s, "RULE OF THUMB", 70)
	match str(s.patternId):
		"ringing": _ringing(s, t, phase)
		"crosstalk": _crosstalk(s, t, phase)
		"ground_bounce": _ground_bounce(s, t, phase)
		"return_path": _return_path(s, t, phase)
		"eye_diagram": _eye_diagram(s, t, phase)
	_run_queue(s, t)
	for b: Dictionary in s.bullets:
		if b.has("fadeAt") and int(b.age) >= int(b.fadeAt) and not b.has("fade"): b.fade = 16
	_probes(s, t)

static func after(_s: Dictionary, _t: int) -> void:
	pass

# ---------------------------------------------------------------- shared helpers

static func _b(s: Dictionary) -> int:
	return int(s.get("beatTicks", 30))

static func _div(a: int, b: int) -> int:
	return floori(float(a) / float(maxi(1, b)))

static func _soul(s: Dictionary) -> Vector2:
	return Vector2(float(s.soul.x), float(s.soul.y))

static func _later(s: Dictionary, at: int, item: Dictionary) -> void:
	item.at = at
	s.queue.append(item)

static func _run_queue(s: Dictionary, t: int) -> void:
	var keep: Array = []
	for q: Dictionary in s.queue:
		if int(q.at) > t:
			keep.append(q)
			continue
		match str(q.kind):
			"warn": D.warn(s, q.props, int(q.life), bool(q.get("loud", false)))
			"shot": D.shot(s, q.props)
	s.queue = keep

# ---------------------------------------------------------------- test points

## One probe at a time: the next appears 24 ticks after the last was probed and
## no earlier than tick 40 + 100 per probe. It stays until probed.
static func _probes(s: Dictionary, t: int) -> void:
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		if not bool(o.get("shown", false)):
			var ready: bool = t >= 40 + 100 * i and (i == 0 or (last_done >= 0 and int(s.clock) - last_done >= 24))
			if ready:
				var spot: Vector2 = _probe_spot(s, t, o)
				o.shown = true
				o.x = spot.x; o.y = spot.y
				D.effect(s, "pulse", D.to_world(s, spot), 18)
		if bool(o.get("shown", false)): _follow_probe(s, o)
		o.active = bool(o.get("shown", false))
		return

static func _probe_spot(s: Dictionary, t: int, o: Dictionary) -> Vector2:
	var soul: Vector2 = _soul(s)
	match str(s.patternId):
		"ground_bounce":
			var best_x: float = 48.0
			var best: float = INF
			for k: int in range(9):
				var x: float = _gb_pin_x(k)
				if absf(x) > 92.0: continue
				var score: float = absf(absf(x - soul.x) - 60.0)
				for b: Dictionary in s.bullets:
					if b.shape == "er_bit" and absf(float(b.x) - x) < 22.0: score += 200.0
				if score < best:
					best = score; best_x = x
			return Vector2(best_x, _gb_probe_y(s))
		"return_path":
			return _rp_probe_spot(s, t)
		"eye_diagram":
			var e: Dictionary = _eye_now(s, t)
			var side: float = -1.0 if soul.x > float(e.ex) else 1.0
			o.off = Vector2(side * 26.0, (1.0 if D.rand(s) < 0.5 else -1.0) * 10.0)
			return Vector2(float(e.ex), float(e.ey)) + Vector2(o.off)
	# Ringing and crosstalk: the calmest spot at a comfortable reach.
	var h: Vector2 = D.half(s)
	var best_at: Vector2 = Vector2(0, 0)
	var best_score: float = INF
	for gx: float in [-0.65, -0.35, 0.0, 0.35, 0.65]:
		for gy: float in [-0.7, -0.35, 0.0, 0.35, 0.7]:
			var at: Vector2 = Vector2(gx * h.x, gy * h.y)
			if s.patternId == "crosstalk": at.y = gy * 64.0 + 7.5 * signf(gy)
			var score: float = absf(at.distance_to(soul) - 55.0) + _risk(s, t, at)
			if score < best_score:
				best_score = score; best_at = at
	return best_at

static func _risk(s: Dictionary, t: int, at: Vector2) -> float:
	var risk: float = 0.0
	if s.patternId == "ringing":
		for sw: Dictionary in s.sweeps:
			if _ring_edge_x(sw, t) - RING_LEN > at.x + 10.0: continue
			var lo: float = minf(float(sw.pk), float(sw.y0)) - 14.0
			var hi: float = maxf(float(sw.pk), float(sw.y0)) + 14.0
			if at.y >= lo and at.y <= hi: risk += 500.0
	elif s.patternId == "crosstalk":
		for ev: Dictionary in s.events:
			if t > int(ev.end): continue
			for lane: int in ev.lanes:
				if absf(at.y - XT_LANES[lane]) < 12.0: risk += 500.0
	return risk

static func _follow_probe(s: Dictionary, o: Dictionary) -> void:
	match str(s.patternId):
		"ground_bounce":
			o.y = _gb_probe_y(s)
		"eye_diagram":
			var e: Dictionary = _eye_now(s, int(s.clock) - int(s.leadIn))
			o.x = float(e.ex) + Vector2(o.off).x
			o.y = float(e.ey) + Vector2(o.off).y

# ---------------------------------------------------------------- 1. Ringing

# The scope screen. A step edge sweeps across from the left, overshoots and
# rings down to its new level: everything between the rail it starts from and
# its first overshoot peak gets swept (shown first as a yellow band). Get past
# the peak. The overshoot peak sheds sparks into the clear side as it goes.
# Phase 1: every other sweep is two channels at once, a rising edge from the
# floor and a falling one from the ceiling; slip into the gap between them.
const RING_H: Vector2 = Vector2(116.0, 56.0)
const RING_V: float = 2.6
const RING_U: float = 24.0
const RING_L: float = 45.0
const RING_SEG: float = 6.0
const RING_LEN: float = 140.0
const RING_WARN: int = 40
const RING_EVERY: int = 94

static func _ringing(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 232.0, "h": 112.0}, 24)
	if t >= 6 and (t - 6) % RING_EVERY == 0 and t + RING_WARN < int(s.length) - 80:
		_ring_announce(s, t, phase, _div(t - 6, RING_EVERY))
	for sw: Dictionary in s.sweeps:
		_ring_advance(s, sw, t, phase)
	_ring_hint(s, t)

static func _ring_announce(s: Dictionary, t: int, phase: int, k: int) -> void:
	var h: Vector2 = RING_H
	var y: float = clampf(float(s.soul.y), -h.y + 4.0, h.y - 4.0)
	var enter: int = t + RING_WARN
	if phase >= 1 and k % 2 == 1:
		var side: float = 1.0 if D.rand(s) < 0.5 else -1.0
		if absf(y + side * 22.0) > h.y - 24.0: side = -side
		var mid: float = clampf(y + side * D.rand_range(s, 18.0, 26.0), -h.y + 24.0, h.y - 24.0)
		_ring_sweep(s, enter, 1.0, mid + 17.0, 0, mid, true)
		_ring_sweep(s, enter, -1.0, mid - 17.0, 1, mid, true)
		D.banner(s, "TWO CHANNELS", 40)
	else:
		# Rising from the floor when you are low, falling from the ceiling when high.
		var p: float = 1.0 if y > 0.0 else -1.0
		var pk: float = clampf(y - p * D.rand_range(s, 16.0, 26.0), -h.y + 28.0, h.y - 28.0)
		_ring_sweep(s, enter, p, pk, 0, pk - p * 14.0, false)
		if k == 0: D.banner(s, "WATCH THE OVERSHOOT", 44)

## p = +1: a rising edge from the floor (it overshoots upward, to pk);
## p = -1: a falling edge from the ceiling (it undershoots downward).
static func _ring_sweep(s: Dictionary, enter: int, p: float, pk: float, ch: int, goal: float, quiet: bool) -> void:
	var h: Vector2 = RING_H
	var y0: float = p * (h.y - 1.0)
	var r1: float = exp(-RING_U / RING_L)
	var y1: float = (pk + y0 * r1) / (1.0 + r1)
	s.sweeps.append({"enter": enter, "p": p, "y0": y0, "y1": y1, "pk": pk, "ch": ch, "spawned": 0.0, "goal": goal, "quiet": quiet})
	var lo: float = minf(pk, y0)
	var hi: float = maxf(pk, y0)
	D.warn(s, {"kind": "er_env", "space": "box", "lo": lo, "hi": hi, "y1": y1, "pk": pk, "ch": ch, "enterClock": int(s.clock) + RING_WARN}, RING_WARN + 92, ch == 0)
	for f: float in [0.25, 0.6, 0.9]:
		D.warn(s, {"kind": "edge", "space": "box", "x": -h.x + 4.0, "y": lerpf(y0, pk, f), "dir": Vector2.RIGHT}, RING_WARN)

static func _ring_y(sw: Dictionary, u: float) -> float:
	return float(sw.y1) + (float(sw.y0) - float(sw.y1)) * exp(-u / RING_L) * cos(PI * u / RING_U)

static func _ring_edge_x(sw: Dictionary, t: int) -> float:
	return -RING_H.x - 4.0 + RING_V * float(t - int(sw.enter))

static func _ring_advance(s: Dictionary, sw: Dictionary, t: int, phase: int) -> void:
	var since: int = t - int(sw.enter)
	if since < 0: return
	var edge: float = _ring_edge_x(sw, t)
	var entered: float = RING_V * float(since)
	# The waveform slides in through the left wall, one trace segment at a time.
	while float(sw.spawned) + RING_SEG <= entered and float(sw.spawned) < RING_LEN:
		var u0: float = float(sw.spawned)
		var u1: float = u0 + RING_SEG
		var a: Vector2 = Vector2(edge - u0, _ring_y(sw, u0))
		var b: Vector2 = Vector2(edge - u1, _ring_y(sw, u1))
		var mid: Vector2 = (a + b) * 0.5
		var d: Vector2 = a - b
		D.shot(s, {"space": "box", "x": mid.x, "y": mid.y, "vx": RING_V, "collide": "rect", "w": d.length() * 0.5 + 0.5, "h": 1.5, "rot": d.angle(),
			"shape": "er_trace", "ch": int(sw.ch), "u": u0, "life": 260})
		sw.spawned = u1
	# The overshoot peak sheds sparks into the clear side.
	if bool(sw.quiet): return
	var peak_x: float = edge - RING_U
	var every: int = 22 if phase == 0 else 16
	if since % every == 0 and peak_x > -RING_H.x + 10.0 and peak_x < RING_H.x - 10.0:
		D.shot(s, {"space": "box", "x": peak_x, "y": float(sw.pk) - float(sw.p) * 3.0, "vy": -float(sw.p) * 1.0, "drag": 0.975, "r": 2.5,
			"shape": "er_spark", "ch": int(sw.ch), "life": 96, "fadeAt": 80})

## QA autopilot: the bot looks 18 ticks ahead, a sweep crosses the box in 90.
## Step out of a band that is about to sweep past.
static func _ring_hint(s: Dictionary, t: int) -> void:
	s.botGoal = null
	var soul: Vector2 = _soul(s)
	for sw: Dictionary in s.sweeps:
		var edge: float = _ring_edge_x(sw, t)
		if edge - RING_LEN - 8.0 > soul.x: continue
		if edge < soul.x - 150.0: continue
		var lo: float = minf(float(sw.pk), float(sw.y0)) - 8.0
		var hi: float = maxf(float(sw.pk), float(sw.y0)) + 8.0
		if soul.y >= lo and soul.y <= hi:
			s.botGoal = Vector2(soul.x, clampf(float(sw.goal), -RING_H.y + 6.0, RING_H.y - 6.0))
			return

# ---------------------------------------------------------------- 2. Crosstalk

# Seven parallel traces. An aggressor fires a burst of bits down one lane (red
# band first). One beat later its neighbours pick up smaller blips at every
# edge (near-end crosstalk, same way), and when the aggressor reaches the far
# end, blips run back along the neighbours from there (far-end crosstalk).
# Stay two lanes away, or slip into the aggressor's lane once it has passed.
# Phase 1: every other burst is a bus, two aggressors three lanes apart.
const XT_H: Vector2 = Vector2(116.0, 56.0)
const XT_LANES: Array[float] = [-45.0, -30.0, -15.0, 0.0, 15.0, 30.0, 45.0]
const XT_V: float = 3.0
const XT_BACK: float = 2.2
const XT_WARN: int = 34
const XT_UI: float = 26.0
const XT_PATTERNS: Array[String] = ["1011", "1101", "101", "111", "1001"]

static func _crosstalk(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 232.0, "h": 112.0}, 24)
	var every: int = 74 if phase == 0 else 80
	if t >= 10 and (t - 10) % every == 0 and t < int(s.length) - 150:
		_xt_event(s, t, phase, _div(t - 10, every))

static func _lane_of(y: float) -> int:
	var best: int = 0
	for i: int in range(XT_LANES.size()):
		if absf(XT_LANES[i] - y) < absf(XT_LANES[best] - y): best = i
	return best

static func _xt_event(s: Dictionary, t: int, phase: int, k: int) -> void:
	var h: Vector2 = XT_H
	var n: int = XT_LANES.size()
	var here: int = _lane_of(float(s.soul.y))
	var dir: float = 1.0 if k % 2 == 0 else -1.0
	var aggressors: Array[int] = []
	if phase >= 1 and k % 2 == 1:
		var lo: int = maxi(0, here - 4)
		var hi: int = mini(n - 4, here + 1)
		var a: int = lo + int(D.rand(s) * float(hi - lo + 1)) % (hi - lo + 1)
		aggressors = [a, a + 3]
		D.banner(s, "BUS SWITCHING", 40)
	else:
		var picks: Array[int] = [-1, 0, 0, 1]
		aggressors = [clampi(here + picks[int(D.rand(s) * 4.0) % 4], 0, n - 1)]
		if k == 0: D.banner(s, "AGGRESSOR", 40)
	var victims: Array[int] = []
	for a: int in aggressors:
		for vl: int in [a - 1, a + 1]:
			if vl >= 0 and vl < n and vl not in aggressors and vl not in victims: victims.append(vl)
	var pattern: String = XT_PATTERNS[int(D.rand(s) * XT_PATTERNS.size()) % XT_PATTERNS.size()]
	var pulses: Array = []
	var i: int = 0
	while i < pattern.length():
		if pattern[i] != "1":
			i += 1
			continue
		var j: int = i
		while j < pattern.length() and pattern[j] == "1": j += 1
		pulses.append(Vector2(i * XT_UI, j * XT_UI))
		i = j
	var start_x: float = -dir * (h.x + 8.0)
	var bt: int = _b(s)
	var travel: int = int((2.0 * h.x + 16.0) / XT_V)
	var back_arm: int = XT_WARN + travel
	for a: int in aggressors:
		var y: float = XT_LANES[a]
		D.warn(s, {"kind": "lane", "y": D.centre(s).y + y, "h": 7.0, "horizontal": true}, XT_WARN, true)
		D.warn(s, {"kind": "edge", "space": "box", "x": -dir * (h.x - 4.0), "y": y, "dir": Vector2(dir, 0)}, XT_WARN)
		for pl: Vector2 in pulses:
			D.shot(s, {"space": "box", "x": start_x - dir * (pl.x + pl.y) * 0.5, "y": y, "vx": dir * XT_V, "collide": "rect", "w": (pl.y - pl.x) * 0.5 - 3.0, "h": 4.0,
				"shape": "er_pulse", "hold": true, "arm": XT_WARN, "life": XT_WARN + 140})
	for vl: int in victims:
		var y: float = XT_LANES[vl]
		D.warn(s, {"kind": "er_victim", "space": "box", "y": y, "dir": dir, "near": true}, XT_WARN + bt + 24)
		# Near end: a smaller blip at every aggressor edge, one beat behind it.
		for pl: Vector2 in pulses:
			for e: int in range(2):
				D.shot(s, {"space": "box", "x": start_x - dir * (pl.x if e == 0 else pl.y), "y": y, "vx": dir * XT_V, "r": 3.0, "shape": "er_spike",
					"sign": 1 if e == 0 else -1, "hold": true, "arm": XT_WARN + bt, "life": XT_WARN + bt + 140})
		# Far end: one blip per pulse runs back once the aggressor gets there.
		_later(s, t + back_arm - 28, {"kind": "warn", "props": {"kind": "edge", "space": "box", "x": dir * (h.x - 4.0), "y": y, "dir": Vector2(-dir, 0)}, "life": 28})
		_later(s, t + back_arm - 28, {"kind": "warn", "props": {"kind": "er_victim", "space": "box", "y": y, "dir": -dir, "near": false}, "life": 70})
		for jj: int in range(pulses.size()):
			D.shot(s, {"space": "box", "x": dir * (h.x + 8.0 + jj * 2.0 * XT_UI), "y": y, "vx": -dir * XT_BACK, "r": 3.0, "shape": "er_spike", "sign": 1,
				"far": true, "hold": true, "arm": back_arm, "life": back_arm + 130})
	var lanes: Array[int] = []
	lanes.append_array(aggressors)
	lanes.append_array(victims)
	s.events.append({"born": t, "lanes": lanes, "end": t + back_arm + 110})

# ---------------------------------------------------------------- 3. Ground Bounce

# Blue soul on a circuit board. Nine output pins line the top of the box; on
# each beat two of them switch and drop a bit straight down (one over you).
# On the last beat of every bar ALL the outputs switch at once: the ground
# reference bounces, the floor jolts and a ripple of spikes runs along it from
# one side a beat later. Jump it. Phase 1: the ground rings, so a second,
# smaller ripple follows the first.
const GB_H: Vector2 = Vector2(112.0, 50.0)
const GB_RIPPLE_V: float = 3.2

static func _gb_pin_x(i: int) -> float:
	return -96.0 + 24.0 * i

static func _gb_probe_y(s: Dictionary) -> float:
	return D.half(s).y - 4.0 - 26.0

static func _ground_bounce(s: Dictionary, t: int, phase: int) -> void:
	var bt: int = _b(s)
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 100.0}, 24)
		s.soul.gravity = Vector2.DOWN
	# Spikes stay on the (bouncing) floor.
	var floor_y: float = D.half(s).y
	for b: Dictionary in s.bullets:
		if b.shape == "er_gbspike": b.y = floor_y - float(b.h)
	if t % bt != 0 or t < bt or t > int(s.length) - 40 - 2 * bt - 30: return
	var k: int = _div(t, bt)
	if k % 4 == 3:
		_gb_switch_all(s, t, phase, bt, _div(k, 4))
		return
	var near: int = 0
	for i: int in range(9):
		if absf(_gb_pin_x(i) - float(s.soul.x)) < absf(_gb_pin_x(near) - float(s.soul.x)): near = i
	var other: int = int(D.rand(s) * 9.0) % 9
	if absi(other - near) < 2: other = (near + 3 + int(D.rand(s) * 3.0)) % 9
	for pin: int in [near, other]:
		s.pinAt[pin] = int(s.clock)
		D.shot(s, {"space": "box", "x": _gb_pin_x(pin), "y": -D.half(s).y + 4.0, "vy": 0.9, "ay": 0.045, "r": 4.5, "shape": "er_bit", "hold": true, "arm": 18, "life": 150})

static func _gb_switch_all(s: Dictionary, t: int, phase: int, bt: int, bar: int) -> void:
	for i: int in range(9): s.pinAt[i] = int(s.clock)
	D.banner(s, "ALL OUTPUTS SWITCH", bt + 10)
	var src: float = (-1.0 if bar % 2 == 0 else 1.0) * GB_H.x
	D.warn(s, {"kind": "er_floor", "space": "box", "src": src}, bt, true)
	var floor_y: float = D.half(s).y
	for col: int in range(28):
		var x: float = -GB_H.x + 4.0 + col * 8.0
		var arm: int = bt + int(absf(x - src) / GB_RIPPLE_V)
		D.shot(s, {"space": "box", "x": x, "y": floor_y - 6.0, "collide": "rect", "w": 3.0, "h": 6.0, "shape": "er_gbspike", "hold": true, "arm": arm, "life": arm + 14})
		if phase >= 1:
			var arm2: int = arm + 32
			D.shot(s, {"space": "box", "x": x, "y": floor_y - 4.5, "collide": "rect", "w": 3.0, "h": 4.5, "shape": "er_gbspike", "echo": true, "hold": true, "arm": arm2, "life": arm2 + 12})
	# The floor itself jolts up and settles.
	D.box_to(s, {"h": 90.0, "cy": 55.0}, 6, bt, "out")
	D.box_to(s, {"h": 100.0, "cy": 60.0}, 24, bt + 6, "back")

# ---------------------------------------------------------------- 4. Return Path

# A ground plane with a slot cut in it. The signal trace crosses the slot, so
# its return current has to detour around the slot's end: that detour is the
# only quiet place (a lit pocket that travels the dashed route). While it
# travels, the slot radiates rings of noise that fill the rest of the box.
# Between drills, stray sparks jump from the slot at you.
# Phase 1: two slots, so the return path snakes around both.
const RP_POCKET: Vector2 = Vector2(18.0, 16.0)
const RP_WARN: int = 52

static func _rp_layout(phase: int, which: int) -> Dictionary:
	var f: float = 1.0 if which == 0 else -1.0
	var slots: Array = []
	var route: Array = []
	var emit: Array = []
	var trace_y: float = 0.0
	if phase == 0:
		slots = [Rect2(-5.0, -56.0, 10.0, 60.0) if which == 0 else Rect2(-5.0, -4.0, 10.0, 60.0)]
		for p: Vector2 in [Vector2(-48, -34), Vector2(-14, -34), Vector2(-14, 18), Vector2(14, 18), Vector2(14, -34), Vector2(48, -34)]:
			route.append(Vector2(p.x, p.y * f))
		emit = [Vector2(0.0, -26.0 * f)]
		trace_y = -34.0 * f
	else:
		if which == 0: slots = [Rect2(-35.0, -56.0, 10.0, 64.0), Rect2(25.0, -8.0, 10.0, 64.0)]
		else: slots = [Rect2(-35.0, -8.0, 10.0, 64.0), Rect2(25.0, -56.0, 10.0, 64.0)]
		for p: Vector2 in [Vector2(-70, 0), Vector2(-42, 0), Vector2(-42, 22), Vector2(-18, 22), Vector2(-18, 0), Vector2(18, 0), Vector2(18, -22), Vector2(42, -22), Vector2(42, 0), Vector2(70, 0)]:
			route.append(Vector2(p.x, p.y * f))
		emit = [Vector2(-30.0, -24.0 * f), Vector2(30.0, 24.0 * f)]
	return {"slots": slots, "route": route, "emit": emit, "traceY": trace_y}

static func _path_len(route: Array) -> float:
	var total: float = 0.0
	for i: int in range(route.size() - 1):
		total += Vector2(route[i]).distance_to(Vector2(route[i + 1]))
	return total

static func _along(route: Array, d: float) -> Vector2:
	var left: float = d
	for i: int in range(route.size() - 1):
		var a: Vector2 = route[i]
		var b: Vector2 = route[i + 1]
		var seg: float = a.distance_to(b)
		if left <= seg: return a.lerp(b, left / maxf(0.001, seg))
		left -= seg
	return Vector2(route[route.size() - 1])

static func _rp_schedule(phase: int) -> Array:
	var drills: Array = []
	var at: int = 8
	var v: float = 1.5 if phase == 0 else 1.6
	for which: int in range(2):
		var lay: Dictionary = _rp_layout(phase, which)
		var length: float = _path_len(lay.route)
		var live: int = at + RP_WARN
		var end: int = live + int(ceil(length / v))
		drills.append({"warn": at, "live": live, "end": end, "which": which, "v": v, "len": length, "route": lay.route, "slots": lay.slots, "emit": lay.emit, "traceY": lay.traceY})
		at = end + 18
	return drills

static func _rp_pocket(dr: Dictionary, t: int) -> Vector2:
	var d: float = clampf(float(t - int(dr.live)) * float(dr.v), 0.0, float(dr.len))
	return _along(dr.route, d)

## The drill whose slot is on screen (the latest one that has been announced).
static func _rp_current(s: Dictionary, t: int) -> Dictionary:
	var current: Dictionary = {}
	for dr: Dictionary in s.drills:
		if t >= int(dr.warn): current = dr
	return current

static func _return_path(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 232.0, "h": 112.0}, 24)
	s.safe = []
	s.botGoal = null
	var dr: Dictionary = _rp_current(s, t)
	if dr.is_empty(): return
	if t == int(dr.warn):
		# The current flows from whichever end of the trace is nearer you.
		var route: Array = dr.route
		if _soul(s).distance_to(Vector2(route[route.size() - 1])) < _soul(s).distance_to(Vector2(route[0])):
			var flipped: Array = route.duplicate()
			flipped.reverse()
			dr.route = flipped
		D.banner(s, "MIND THE GAP" if int(dr.which) == 0 else "AROUND THE SLOT", 50)
		D.warn(s, {"kind": "er_route", "space": "box"}, RP_WARN, true)
		D.effect(s, "lantern", D.to_world(s, _rp_pocket(dr, t)), 30)
	var live: bool = t >= int(dr.live) and t < int(dr.end)
	if t <= int(dr.end) + 4:
		var c: Vector2 = _rp_pocket(dr, t)
		s.safe = [Rect2(c - RP_POCKET, RP_POCKET * 2.0)]
		s.botGoal = c
	else:
		# The noise stops with the current: rings still out there fade away.
		for b: Dictionary in s.bullets:
			if b.shape == "er_emi" and not b.has("fade"): b.fade = 16
	if t == int(dr.live): D.banner(s, "SLOT RADIATES", 40)
	if live and (t - int(dr.live)) % 15 == 0:
		var emitters: Array = dr.emit
		var e: Vector2 = emitters[_div(t - int(dr.live), 15) % emitters.size()]
		D.shot(s, {"space": "box", "x": e.x, "y": e.y, "collide": "ring", "radius": 3.0, "grow": 1.7, "thick": 2.5, "gap": 0.0, "gapWidth": 0.0,
			"shape": "er_emi", "maxRadius": 170.0})
	# Stray sparks jump from the slot whenever no noise is radiating.
	var quiet: bool = not live
	if quiet and t % 26 == 13 and t > 20 and t < int(s.length) - 90:
		var emitters2: Array = dr.emit
		var from: Vector2 = emitters2[_div(t, 26) % emitters2.size()]
		var aim: Vector2 = (_soul(s) - from).normalized()
		if aim == Vector2.ZERO: aim = Vector2.DOWN
		var speed: float = 1.3 if phase == 0 else 1.45
		D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": aim.x * speed, "vy": aim.y * speed, "r": 3.0, "shape": "er_zap", "spin": 0.3, "hold": true, "arm": 20, "life": 190})

static func _rp_probe_spot(s: Dictionary, t: int) -> Vector2:
	for dr: Dictionary in s.drills:
		if t >= int(dr.warn) - 10 and t < int(dr.end) - 30:
			# On the route, a little ahead of the pocket: it carries you there.
			var done: float = clampf(float(t - int(dr.live)) * float(dr.v), 0.0, float(dr.len))
			return _along(dr.route, minf(done + 60.0, float(dr.len) - 6.0))
	var soul: Vector2 = _soul(s)
	var x: float = soul.x + (44.0 if soul.x < 0.0 else -44.0)
	return Vector2(clampf(x, -90.0, 90.0), clampf(soul.y, -40.0, 40.0))

# ---------------------------------------------------------------- 5. Eye Diagram

# Thousands of overlapping bits draw an eye: the clear opening is the only
# place without a trace through it. On the third beat of every bar the eye
# closes (noise and jitter) and opens again a beat later; a dashed outline
# shows how far it will close. Between closings the trigger slips half a bit
# sideways, or the baseline wanders up or down: follow the opening.
# Phase 1: a stray glitch trace streaks through the eye before each closing.
const EYE_UI: float = 148.0
const EYE_RAMP: float = 30.0
const EYE_H_OPEN: float = 38.0
const EYE_H_SHUT: float = 15.0
const EYE_W_OPEN: float = 70.0
const EYE_W_SHUT: float = 48.0

static func _smooth(p: float) -> float:
	var q: float = clampf(p, 0.0, 1.0)
	return q * q * (3.0 - 2.0 * q)

static func _eye_open(s: Dictionary, t: int) -> float:
	var bt: int = _b(s)
	var k: int = _div(t, bt)
	var ph: float = float(t - k * bt) / float(bt)
	match k % 4:
		2: return 1.0 - _smooth(ph / 0.35)
		3: return 0.0 if ph < 0.5 else _smooth((ph - 0.5) / 0.5)
	return 1.0

## ex, ey (eye centre), H (vertical half opening), W (half width) at tick t.
static func _eye_now(s: Dictionary, t: int) -> Dictionary:
	var e: Dictionary = s.eye
	var px: float = _smooth(float(t - int(e.xs)) / float(maxi(1, int(e.xd))))
	var py: float = _smooth(float(t - int(e.ys)) / float(maxi(1, int(e.yd))))
	var o: float = _eye_open(s, t)
	return {"ex": lerpf(float(e.x0), float(e.x1), px), "ey": lerpf(float(e.y0), float(e.y1), py),
		"H": lerpf(EYE_H_SHUT, EYE_H_OPEN, o), "W": lerpf(EYE_W_SHUT, EYE_W_OPEN, o), "open": o}

static func _eye_inside(e: Dictionary, p: Vector2, margin: float) -> bool:
	var dy: float = absf(p.y - float(e.ey))
	var wm: float = float(e.W) - margin
	for k: int in [-1, 0, 1]:
		var dx: float = absf(p.x - (float(e.ex) + k * EYE_UI))
		if dx > wm: continue
		if dy <= (float(e.H) - margin) * minf(1.0, (wm - dx) / EYE_RAMP): return true
	return false

static func _eye_diagram(s: Dictionary, t: int, phase: int) -> void:
	var bt: int = _b(s)
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 112.0}, 24)
		D.banner(s, "MEASURE, DON'T GUESS", 60)
	var e: Dictionary = s.eye
	var k: int = _div(t, bt)
	if t % bt == 0 and t < int(s.length) - 40 - bt:
		if k % 4 == 3:
			_eye_plan(s, t, bt, _div(k, 4) + 1)
		if phase >= 1 and k % 4 == 0 and k >= 4:
			_eye_glitch(s, t, bt, k)
	# Outside the opening, every trace is live.
	var now: Dictionary = _eye_now(s, t)
	if t >= 20 and not _eye_inside(now, _soul(s), 4.0):
		D.hurt(s, D.soul_world(s))
	e.open = now.open

## Decided one beat ahead: odd bars slip the trigger half a bit sideways, even
## bars let the baseline wander up or down.
static func _eye_plan(s: Dictionary, t: int, bt: int, bar: int) -> void:
	var e: Dictionary = s.eye
	var start: int = t + bt
	var cur: Dictionary = _eye_now(s, t)
	if bar % 2 == 1:
		var to: float = 0.0
		if absf(float(e.x1)) < 1.0:
			e.slip = int(e.slip) + 1
			to = EYE_UI * 0.5 * (1.0 if int(e.slip) % 2 == 1 else -1.0)
		e.x0 = cur.ex; e.x1 = to; e.xs = start; e.xd = 2 * bt
		D.banner(s, "TRIGGER SLIP", bt + 10)
		D.warn(s, {"kind": "er_slip", "space": "box", "dir": signf(to - float(cur.ex)), "start": int(s.clock) + bt, "len": 2 * bt}, 3 * bt, true)
	else:
		var old: float = float(e.y1)
		var to2: float = D.rand_range(s, -18.0, 18.0)
		if absf(to2 - old) < 12.0: to2 = clampf(old + (14.0 if old < 0.0 else -14.0), -20.0, 20.0)
		e.y0 = cur.ey; e.y1 = to2; e.ys = start; e.yd = bt
		D.warn(s, {"kind": "er_wander", "space": "box", "to": to2}, 2 * bt)

static func _eye_glitch(s: Dictionary, t: int, bt: int, k: int) -> void:
	var e: Dictionary = s.eye
	var dir: float = 1.0 if _div(k, 4) % 2 == 0 else -1.0
	var ey: float = float(e.y1)
	var y: float = clampf(float(s.soul.y) + D.rand_range(s, -3.0, 3.0), ey - 22.0, ey + 22.0)
	D.warn(s, {"kind": "lane", "y": D.centre(s).y + y, "h": 4.0, "horizontal": true}, bt, true)
	D.warn(s, {"kind": "edge", "space": "box", "x": -dir * (RING_H.x - 4.0), "y": y, "dir": Vector2(dir, 0)}, bt)
	# Fast enough to clear the middle before the eye starts closing.
	D.shot(s, {"space": "box", "x": -dir * (RING_H.x + 10.0), "y": y, "vx": dir * 5.0, "collide": "rect", "w": 16.0, "h": 1.5, "shape": "er_glitch",
		"hold": true, "arm": bt, "life": bt + 70})

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var t: int = int(s.clock) - int(s.leadIn)
	match str(s.patternId):
		"ringing":
			_draw_scope(c, s, v)
			_draw_ringing(c, s, v)
		"crosstalk":
			_draw_board(c, s, v)
			_draw_crosstalk(c, s, v)
		"ground_bounce":
			_draw_board(c, s, v)
			_draw_ground(c, s, v)
		"return_path":
			_draw_board(c, s, v)
			_draw_return(c, s, v, t)
		"eye_diagram":
			_draw_scope(c, s, v)
			_draw_eye(c, s, v, t)
	_draw_rule(c, s, v, t)

static func _box_fill(c: CanvasItem, s: Dictionary, v: Node2D, colour: Color) -> void:
	var h: Vector2 = D.half(s)
	c.draw_colored_polygon(v.box_rect_poly(Rect2(-h, h * 2.0)), colour)

static func _draw_scope(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	_box_fill(c, s, v, SCREEN)
	# Graticule: 10 x 8 divisions, a bright centre cross with minor ticks.
	for i: int in range(1, 10):
		var x: float = -h.x + 2.0 * h.x * i / 10.0
		c.draw_line(v.box_point(Vector2(x, -h.y)), v.box_point(Vector2(x, h.y)), Color(GRID, 0.35 if i == 5 else 0.18), 1)
	for i: int in range(1, 8):
		var y: float = -h.y + 2.0 * h.y * i / 8.0
		c.draw_line(v.box_point(Vector2(-h.x, y)), v.box_point(Vector2(h.x, y)), Color(GRID, 0.35 if i == 4 else 0.18), 1)
	var x2: float = -h.x
	while x2 < h.x:
		c.draw_line(v.box_point(Vector2(x2, -2.0)), v.box_point(Vector2(x2, 2.0)), Color(GRID, 0.4), 1)
		x2 += 2.0 * h.x / 50.0
	_left_text(c, v, v.box_point(Vector2(-h.x + 4.0, h.y - 4.0)), "CH1 200mV/div", Color(YELLOW, 0.4))
	_left_text(c, v, v.box_point(Vector2(h.x - 50.0, h.y - 4.0)), "1ns/div", Color(PHOSPHOR, 0.35))

static func _draw_board(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	_box_fill(c, s, v, PCB_DARK)
	# Faint copper pour hatching and a few vias.
	var x: float = -h.x - h.y
	while x < h.x:
		c.draw_line(v.box_point(Vector2(x, h.y)), v.box_point(Vector2(x + 2.0 * h.y, -h.y)), Color(PCB, 0.55), 1)
		x += 12.0
	for p: Vector2 in [Vector2(-0.8, -0.75), Vector2(0.82, 0.7), Vector2(-0.3, 0.8), Vector2(0.45, -0.8)]:
		var at: Vector2 = v.box_point(p * h)
		c.draw_circle(at, 2.5, Color(COPPER, 0.35))
		c.draw_circle(at, 1.0, Color(INK, 0.8))

static func _left_text(c: CanvasItem, v: Node2D, at: Vector2, words: String, colour: Color) -> void:
	var font: Font = v.get("font")
	if font != null: c.draw_string(font, at, words, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, colour)

static func _dashed(c: CanvasItem, a: Vector2, b: Vector2, colour: Color, width: float = 1.0) -> void:
	var length: float = a.distance_to(b)
	var dir: Vector2 = (b - a) / maxf(1.0, length)
	var x: float = 0.0
	while x < length:
		c.draw_line(a + dir * x, a + dir * minf(length, x + 4.0), colour, width)
		x += 8.0

## The rule-of-thumb readout: a thumbs-up and today's rule, top left.
static func _draw_rule(c: CanvasItem, s: Dictionary, v: Node2D, t: int) -> void:
	if t > 170 or not s.has("rule"): return
	var fade: float = clampf(float(t + 20) / 20.0, 0.0, 1.0) * clampf(float(170 - t) / 30.0, 0.0, 1.0)
	var h: Vector2 = D.half(s)
	var at: Vector2 = v.box_point(Vector2(-h.x + 11.0, -h.y + 11.0))
	_thumb(c, at, Color(COPPER, fade), Color(SILK, fade))
	_left_text(c, v, at + Vector2(10, 4), str(s.rule), Color(YELLOW, 0.85 * fade))

static func _thumb(c: CanvasItem, at: Vector2, fill: Color, line: Color) -> void:
	# A fist with the thumb up.
	c.draw_rect(Rect2(at + Vector2(-5, -1), Vector2(9, 7)), fill)
	c.draw_rect(Rect2(at + Vector2(-4, -8), Vector2(3, 8)), fill)
	c.draw_rect(Rect2(at + Vector2(-5, -1), Vector2(9, 7)), line, false, 1)
	c.draw_rect(Rect2(at + Vector2(-4, -8), Vector2(3, 8)), line, false, 1)
	for i: int in range(3):
		c.draw_line(at + Vector2(0, 1 + i * 2), at + Vector2(4, 1 + i * 2), Color(line, line.a * 0.6), 1)

static func _draw_ringing(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	for w: Dictionary in s.warnings:
		if w.kind != "er_env": continue
		var col: Color = YELLOW if int(w.ch) == 0 else CYAN
		var edge: float = -RING_H.x - 4.0 + RING_V * float(int(s.clock) - int(w.enterClock))
		var x0: float = maxf(edge, -h.x)
		if x0 >= h.x: continue
		var blink: float = 0.5 + 0.5 * sin(float(w.age) * 0.45)
		var waiting: bool = edge < -h.x
		var band: Rect2 = Rect2(Vector2(x0, float(w.lo)), Vector2(h.x - x0, float(w.hi) - float(w.lo)))
		c.draw_colored_polygon(v.box_rect_poly(band), Color(col, (0.10 + 0.08 * blink) if waiting else 0.07))
		_dashed(c, v.box_point(Vector2(x0, float(w.pk))), v.box_point(Vector2(h.x, float(w.pk))), Color(col, 0.75 if waiting else 0.45))
		_dashed(c, v.box_point(Vector2(x0, float(w.y1))), v.box_point(Vector2(h.x, float(w.y1))), Color(col, 0.25))
		if waiting:
			var label_y: float = float(w.pk) + (-3.0 if float(w.pk) < float(w.y1) else 11.0)
			_left_text(c, v, v.box_point(Vector2(-h.x + 14.0, label_y)), "OVERSHOOT", Color(col, 0.8))

static func _draw_crosstalk(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	for y: float in XT_LANES:
		var a: Vector2 = v.box_point(Vector2(-h.x, y))
		var b: Vector2 = v.box_point(Vector2(h.x, y))
		c.draw_line(a, b, Color(COPPER, 0.42), 3)
		c.draw_line(a, b, Color(HOT, 0.12), 1)
	for w: Dictionary in s.warnings:
		if w.kind != "er_victim": continue
		var blink: float = 0.5 + 0.5 * sin(float(w.age) * 0.5)
		var y2: float = float(w.y)
		_dashed(c, v.box_point(Vector2(-h.x, y2)), v.box_point(Vector2(h.x, y2)), Color(CYAN, 0.35 + 0.35 * blink), 2.0)
		var from_x: float = -float(w.dir) * (h.x - 22.0)
		v.text(c, v.box_point(Vector2(from_x, y2 - 3.0)), "NEXT" if bool(w.near) else "FEXT", Color(CYAN, 0.75), 40.0)

static func _draw_ground(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var clock: int = int(s.clock)
	# Ground plane along the floor.
	c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(-h.x, h.y - 2.0), Vector2(2.0 * h.x, 2.0))), Color(COPPER, 0.7))
	_left_text(c, v, v.box_point(Vector2(h.x - 26.0, h.y - 5.0)), "GND", Color(COPPER, 0.6))
	# The output pins along the top, lit when they switch.
	for i: int in range(9):
		var x: float = _gb_pin_x(i)
		var lit: float = clampf(1.0 - float(clock - int(s.pinAt[i])) / 18.0, 0.0, 1.0)
		var pad: Rect2 = Rect2(Vector2(x - 5.0, -h.y), Vector2(10.0, 5.0))
		c.draw_colored_polygon(v.box_rect_poly(pad), Color(COPPER, 0.6).lerp(YELLOW, lit))
		c.draw_circle(v.box_point(Vector2(x, -h.y + 8.0)), 1.5, Color(YELLOW, 0.2 + 0.8 * lit))
	for w: Dictionary in s.warnings:
		if w.kind != "er_floor": continue
		var p: float = float(w.age) / float(w.life)
		var blink: float = 0.5 + 0.5 * sin(float(w.age) * 0.6)
		c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(-h.x, h.y - 14.0), Vector2(2.0 * h.x, 14.0))), Color(ROSE, 0.08 + 0.14 * blink))
		var dir: float = -signf(float(w.src))
		for j: int in range(3):
			var x2: float = float(w.src) + dir * (8.0 + j * 7.0 + p * 20.0)
			v.chevron(c, v.box_point(Vector2(x2, h.y - 8.0)), Vector2(dir, 0), Color(ROSE, 0.5 + 0.5 * p))
	for b: Dictionary in s.bullets:
		if b.shape == "er_bit" and int(b.age) <= int(b.arm):
			_dashed(c, v.box_point(Vector2(float(b.x), -h.y + 8.0)), v.box_point(Vector2(float(b.x), h.y)), Color(YELLOW, 0.25))

static func _draw_return(c: CanvasItem, s: Dictionary, v: Node2D, t: int) -> void:
	var h: Vector2 = D.half(s)
	var dr: Dictionary = _rp_current(s, t)
	if dr.is_empty(): return
	# The signal trace on top of the plane.
	var trace_y: float = float(dr.traceY)
	c.draw_line(v.box_point(Vector2(-h.x, trace_y)), v.box_point(Vector2(h.x, trace_y)), Color(HOT, 0.75), 3)
	_left_text(c, v, v.box_point(Vector2(-h.x + 4.0, trace_y - 4.0)), "SIGNAL", Color(HOT, 0.6))
	for slot: Rect2 in dr.slots:
		var poly: PackedVector2Array = v.box_rect_poly(slot)
		c.draw_colored_polygon(poly, INK)
		c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(SILK, 0.6), 1)
	# The return path (dashed) and the pocket of return current riding it.
	var route: Array = dr.route
	var active: bool = t <= int(dr.end) + 4
	for i: int in range(route.size() - 1):
		_dashed(c, v.box_point(Vector2(route[i])), v.box_point(Vector2(route[i + 1])), Color(MINT, 0.55 if active else 0.2), 2.0)
	if active:
		var pc: Vector2 = _rp_pocket(dr, t)
		var glow: float = 0.5 + 0.5 * sin(float(s.clock) * 0.18)
		c.draw_colored_polygon(v.box_rect_poly(Rect2(pc - RP_POCKET, RP_POCKET * 2.0)), Color(MINT, 0.12 + 0.06 * glow))

static func _hexagon(v: Node2D, cx: float, cy: float, w: float, hh: float) -> PackedVector2Array:
	var ramp: float = minf(EYE_RAMP, w)
	return PackedVector2Array([v.box_point(Vector2(cx - w, cy)), v.box_point(Vector2(cx - w + ramp, cy - hh)), v.box_point(Vector2(cx + w - ramp, cy - hh)),
		v.box_point(Vector2(cx + w, cy)), v.box_point(Vector2(cx + w - ramp, cy + hh)), v.box_point(Vector2(cx - w + ramp, cy + hh))])

static func _draw_eye(c: CanvasItem, s: Dictionary, v: Node2D, t: int) -> void:
	var tt: int = maxi(0, t)
	var e: Dictionary = _eye_now(s, tt)
	var bt: int = _b(s)
	var ex: float = float(e.ex)
	var ey: float = float(e.ey)
	# The traces: a phosphor haze everywhere, the eye openings cut out of it,
	# and a few bundles of overlapping traces around each opening.
	_box_fill(c, s, v, Color(PHOSPHOR, 0.18))
	for k: int in range(-2, 3):
		var cx: float = ex + k * EYE_UI
		c.draw_colored_polygon(_hexagon(v, cx, ey, float(e.W), float(e.H)), SCREEN)
	for j: int in range(5):
		var spread: float = j * 3.0
		var alpha: float = 0.55 - j * 0.09
		for k: int in range(-2, 3):
			var cx2: float = ex + k * EYE_UI + sin(float(tt) * 0.31 + j * 1.7 + k) * 1.2
			var hex: PackedVector2Array = _hexagon(v, cx2, ey, float(e.W) + spread * 0.6, float(e.H) + spread)
			c.draw_polyline(hex + PackedVector2Array([hex[0]]), Color(PHOSPHOR, alpha), 1)
	# The scope's beam drawing the top of the eye, once per beat.
	var ph: float = float(posmod(tt, bt)) / float(bt)
	var beam_x: float = ex - EYE_UI * 0.5 + EYE_UI * ph
	var dx: float = absf(beam_x - ex)
	var top: float = ey - float(e.H) * minf(1.0, (float(e.W) - minf(dx, float(e.W))) / EYE_RAMP)
	c.draw_circle(v.box_point(Vector2(beam_x, top)), 2.0, Color(SILK, 0.8))
	# The closing is foretold a beat ahead by a dashed outline.
	var k_beat: int = _div(tt, bt) % 4
	if k_beat == 1 or (k_beat == 2 and float(e.open) > 0.05):
		var ghost: PackedVector2Array = _hexagon(v, float(s.eye.x1), float(s.eye.y1), EYE_W_SHUT, EYE_H_SHUT)
		ghost.append(ghost[0])
		var blink: float = 0.5 + 0.5 * sin(float(s.clock) * 0.5)
		for i: int in range(ghost.size() - 1):
			_dashed(c, ghost[i], ghost[i + 1], Color(ROSE, 0.45 + 0.4 * blink), 1.0)
	for w: Dictionary in s.warnings:
		match str(w.kind):
			"er_slip":
				var dir: float = float(w.dir)
				var shift: float = fposmod(float(w.age) * 1.2, 12.0)
				for y: float in [-14.0, 0.0, 14.0]:
					for j: int in range(3):
						v.chevron(c, v.box_point(Vector2(ex + dir * (j * 10.0 + shift - 12.0), ey + y)), Vector2(dir, 0), Color(YELLOW, 0.7))
			"er_wander":
				var to: float = float(w.to)
				var ghost2: PackedVector2Array = _hexagon(v, ex, to, EYE_W_OPEN - 10.0, EYE_H_OPEN - 10.0)
				ghost2.append(ghost2[0])
				for i: int in range(ghost2.size() - 1):
					_dashed(c, ghost2[i], ghost2[i + 1], Color(YELLOW, 0.5), 1.0)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var t: int = int(s.clock) - int(s.leadIn)
	if s.patternId == "return_path":
		var dr: Dictionary = _rp_current(s, t)
		if not dr.is_empty() and t <= int(dr.end) + 4:
			var pc: Vector2 = _rp_pocket(dr, t)
			var poly: PackedVector2Array = v.box_rect_poly(Rect2(pc - RP_POCKET, RP_POCKET * 2.0))
			var glow: float = 0.5 + 0.5 * sin(float(s.clock) * 0.18)
			c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(MINT, 0.6 + 0.35 * glow), 2)
			v.text(c, v.box_point(pc + Vector2(0, RP_POCKET.y + 9.0)), "RETURN", Color(MINT, 0.8), 80.0)
	if not bool(s.promised): return
	# A scope probe hovers over each live test point.
	for o: Dictionary in s.objectives:
		if not o.active or o.done: continue
		var top: float = float(o.h) if float(o.w) > 0.0 else 10.0
		var side: float = float(o.w) if float(o.w) > 0.0 else 9.0
		var tip: Vector2 = v.box_point(Vector2(float(o.x) + side, float(o.y) - top))
		var bob: float = sin(float(s.clock) * 0.12) * 1.5
		_probe_icon(c, tip + Vector2(0, bob))

static func _probe_icon(c: CanvasItem, tip: Vector2) -> void:
	var back: Vector2 = tip + Vector2(9, -15)
	c.draw_line(back + Vector2(4, -6), back, Color(INK, 0.9), 4)
	c.draw_line(back, tip + Vector2(2, -4), Color(Color("3a3f4a"), 1.0), 4)
	c.draw_line(back, tip + Vector2(2, -4), Color(SILK, 0.8), 1)
	c.draw_line(back + Vector2(-1, 1), back + Vector2(2, -2), YELLOW, 3)
	c.draw_line(tip + Vector2(2, -4), tip, Color(SILK, 0.95), 1)
	c.draw_arc(tip + Vector2(-1.5, -1.5), 2.0, 0.0, PI, 6, Color(SILK, 0.9), 1)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"er_trace":
			var col: Color = YELLOW if int(b.get("ch", 0)) == 0 else CYAN
			var half: Vector2 = Vector2(float(b.w), 0).rotated(turn)
			var persist: float = clampf(1.0 - float(b.get("u", 0.0)) / (RING_LEN * 1.25), 0.3, 1.0)
			c.draw_line(at - half, at + half, Color(col, 0.22 * alpha * persist), 5.0)
			c.draw_line(at - half, at + half, Color(col, alpha * persist), 2.0)
			if float(b.get("u", 1.0)) == 0.0:
				c.draw_circle(at + half, 3.0, Color(SILK, 0.9 * alpha))
			return true
		"er_spark":
			var col2: Color = YELLOW if int(b.get("ch", 0)) == 0 else CYAN
			var r: float = 3.5
			c.draw_line(at + Vector2(-r, 0).rotated(turn), at + Vector2(r, 0).rotated(turn), Color(col2, alpha), 1)
			c.draw_line(at + Vector2(0, -r).rotated(turn), at + Vector2(0, r).rotated(turn), Color(col2, alpha), 1)
			c.draw_circle(at, 1.8, Color(SILK, alpha))
			return true
		"er_pulse":
			var q: PackedVector2Array = v.quad(at, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(q, Color(HOT, 0.9 * alpha))
			c.draw_polyline(q + PackedVector2Array([q[0]]), Color(SILK, alpha), 1)
			c.draw_line(at + Vector2(-float(b.w) + 2.0, 0).rotated(turn), at + Vector2(float(b.w) - 2.0, 0).rotated(turn), Color(ROSE, alpha), 1)
			return true
		"er_spike":
			var sgn: float = float(b.get("sign", 1))
			var tri: PackedVector2Array = PackedVector2Array([at + Vector2(0, -4.0 * sgn), at + Vector2(3.5, 2.5 * sgn), at + Vector2(-3.5, 2.5 * sgn)])
			c.draw_colored_polygon(tri, Color(CYAN if not b.get("far", false) else Color("9fd8ff"), alpha))
			c.draw_polyline(tri + PackedVector2Array([tri[0]]), Color(SILK, 0.7 * alpha), 1)
			return true
		"er_bit":
			var waiting: bool = int(b.age) <= int(b.arm)
			var a2: float = alpha * (0.5 + 0.5 * sin(float(b.age) * 0.8) if waiting else 1.0)
			c.draw_circle(at, 5.0, Color(INK, 0.6 * a2))
			c.draw_polyline(PackedVector2Array([at + Vector2(-5, 3), at + Vector2(-2, 3), at + Vector2(-2, -3), at + Vector2(2, -3), at + Vector2(2, 3), at + Vector2(5, 3)]),
				Color(YELLOW, a2), 2)
			return true
		"er_gbspike":
			var base: Vector2 = at + Vector2(0, float(b.h)).rotated(turn)
			if int(b.age) <= int(b.arm):
				var soon: float = clampf(1.0 - float(int(b.arm) - int(b.age)) / 24.0, 0.0, 1.0)
				if soon > 0.0: c.draw_line(base, base + Vector2(0, -2.0 - 2.0 * soon).rotated(turn), Color(ROSE, soon * alpha), 2)
				return true
			var tall: float = float(b.h) * 2.0
			var spike: PackedVector2Array = PackedVector2Array([base + Vector2(-3.5, 0).rotated(turn), base + Vector2(3.5, 0).rotated(turn), base + Vector2(0, -tall).rotated(turn)])
			c.draw_colored_polygon(spike, Color(ROSE if not b.get("echo", false) else MAGENTA, alpha))
			c.draw_line(base + Vector2(0, -tall).rotated(turn), base + Vector2(0, -tall + 3.0).rotated(turn), Color(SILK, alpha), 1)
			return true
		"er_emi":
			var radius: float = float(b.radius)
			var n: int = maxi(24, int(radius * 0.5))
			var pts: PackedVector2Array = []
			for i: int in range(n + 1):
				var a: float = i * TAU / n
				pts.append(at + Vector2.from_angle(a) * (radius + sin(a * 9.0 + float(b.age) * 0.6) * 1.6))
			c.draw_polyline(pts, Color(CYAN, 0.25 * alpha), 6)
			c.draw_polyline(pts, Color(CYAN, 0.85 * alpha), 2)
			return true
		"er_zap":
			var waiting2: bool = int(b.age) <= int(b.arm)
			var col3: Color = Color(YELLOW, alpha * (0.4 + 0.6 * absf(sin(float(b.age) * 0.9)) if waiting2 else 1.0))
			var zig: PackedVector2Array = PackedVector2Array([at + Vector2(-4, -3).rotated(turn), at + Vector2(0, -1).rotated(turn), at + Vector2(-1, 1).rotated(turn), at + Vector2(4, 3).rotated(turn)])
			c.draw_polyline(zig, col3, 2)
			c.draw_circle(at, 1.5, Color(SILK, col3.a))
			return true
		"er_glitch":
			var half2: Vector2 = Vector2(float(b.w), 0).rotated(turn)
			c.draw_line(at - half2, at + half2, Color(MAGENTA, 0.25 * alpha), 6.0)
			c.draw_line(at - half2, at + half2, Color(MAGENTA, alpha), 2.0)
			return true
	return false
