class_name DodgePatternsEncore
extends RefCounted
## ENCORE: the show that will not end. Five handmade attacks, one per turn,
## cycling in order and locked to the song's beat (s.beatTicks). The promise is
## two stopping cues per turn (of three offered): step into an open green cue box and confirm, or
## (Call and Response) block the green cue notes with the shield.
## Stage 1 and 2 (later verses) layer more onto every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["spotlights", "call_response", "feedback", "curtain_call", "finale"]
const PHASES: Array[int] = [0, 1, 2]
## ENCORE's song is 144 BPM: one beat is s.beatTicks ticks (25 at 144 BPM,
## 30 at the 120 BPM grid), read from the track main.gd is playing.
static func _b(s: Dictionary) -> int:
	return int(s.get("beatTicks", 30))

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 480
	s.rigs = []
	s.speakers = []
	s.cues = []
	match id:
		"spotlights":
			s.phaseName = "Follow Spot"
			s.hint = "Spotlights mark their line, then sweep. Confirm inside each green cue box."
			s.rigs = [Vector2(36, -34), Vector2(220, -34)]
		"call_response":
			s.phaseName = "Call and Response"
			s.hint = "You can't move. Turn the shield to meet each note. Block green notes for cues."
			s.length = 510
		"feedback":
			s.phaseName = "Feedback"
			s.hint = "Speakers ring on the beat. Find each ring's gap. Confirm in green cue boxes."
			s.speakers = [Vector2(-2, 60), Vector2(258, 60)]
		"curtain_call":
			s.phaseName = "Curtain Call"
			s.hint = "Curtains close on the downbeat. Dodge roses. Confirm in green cue boxes."
		"finale":
			s.phaseName = "Final Verse"
			s.hint = "The stage chases the spotlight. Everything at once. Confirm in green cue boxes."
			s.rigs = [Vector2(128, -40)]
	if id != "call_response":
		# Three cue boxes, two needed (the old encounter also gave three chances).
		# Cues land on beats 4, 9 and 14 and stay open four beats (100 ticks at 144 BPM).
		for beat: int in [4, 9, 14]:
			s.cues.append({"t": beat * _b(s), "open": 4 * _b(s), "x": 0.0, "y": 0.0, "got": false, "placed": false})

static func confirm(s: Dictionary) -> void:
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	for cue: Dictionary in s.cues:
		if cue.placed and not cue.got and _cue_open(s, cue) and soul.distance_to(Vector2(float(cue.x), float(cue.y))) <= 15.0:
			cue.got = true
			s.cuesReached = int(s.cuesReached) + 1
			D.effect(s, "kept", D.to_world(s, Vector2(float(cue.x), float(cue.y))), 30)

static func _cue_open(s: Dictionary, cue: Dictionary) -> bool:
	var t: int = int(s.clock) - int(s.leadIn)
	return t >= int(cue.t) and t < int(cue.t) + int(cue.open)

static func promise_complete(s: Dictionary) -> bool:
	return int(s.cuesReached) >= 2

static func tick(s: Dictionary, t: int) -> void:
	var stage: int = clampi(int(s.phase), 0, 2)
	for cue: Dictionary in s.cues:
		if t == int(cue.t) - 30:
			# Place the cue 50-95 px from the soul: far enough that reaching it is a
			# decision, near enough to reach inside its four-beat window at 144 BPM.
			var h: Vector2 = D.half(s) - Vector2(16, 16)
			var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
			var spot: Vector2 = soul
			for attempt: int in range(8):
				var angle: float = D.rand_range(s, -PI, PI)
				spot = soul + Vector2.from_angle(angle) * D.rand_range(s, 50.0, 95.0)
				spot = Vector2(clampf(spot.x, -h.x, h.x), clampf(spot.y, -h.y, h.y))
				if spot.distance_to(soul) >= 40.0: break
			cue.x = spot.x; cue.y = spot.y; cue.placed = true
			D.warn(s, {"kind": "cue", "space": "box", "x": spot.x, "y": spot.y}, 30, true)
	match str(s.patternId):
		"spotlights": _spotlights(s, t, stage)
		"call_response": _call_response(s, t, stage)
		"feedback": _feedback(s, t, stage)
		"curtain_call": _curtain_call(s, t, stage)
		"finale": _finale(s, t, stage)
	_sweep(s)

static func after(s: Dictionary, _t: int) -> void:
	# Turnaround notes: they stop at the shield's edge, swing to the far side
	# and come in from there.
	if s.patternId != "call_response": return
	var soul: Vector2 = D.soul_world(s)
	for b: Dictionary in s.bullets:
		if not b.has("flip"): continue
		var offset: Vector2 = Vector2(float(b.x), float(b.y)) - soul
		if int(b.flip) == 0 and offset.length() <= 46.0:
			b.flip = 1; b.flipAngle = offset.angle(); b.vx = 0.0; b.vy = 0.0
		elif int(b.flip) >= 1 and int(b.flip) <= 24:
			b.flip = int(b.flip) + 1
			var a: float = float(b.flipAngle) + PI * float(int(b.flip) - 1) / 24.0
			b.x = soul.x + cos(a) * 46.0; b.y = soul.y + sin(a) * 46.0
			if int(b.flip) == 25:
				var inward: Vector2 = -Vector2.from_angle(a) * float(b.speed)
				b.vx = inward.x; b.vy = inward.y

static func _note(s: Dictionary, from: Vector2, to: Vector2, speed: float, props: Dictionary = {}) -> Dictionary:
	var v: Vector2 = (to - from).normalized() * speed
	var b: Dictionary = {"x": from.x, "y": from.y, "vx": v.x, "vy": v.y, "r": 3.5, "shape": "note", "rot": v.angle(), "life": 400}
	b.merge(props, true)
	return D.shot(s, b)

static func _cone(s: Dictionary, rig: Vector2, angle: float, sweep: float, warn_ticks: int = 30, live: int = 42) -> void:
	D.shot(s, {"x": rig.x, "y": rig.y, "collide": "beam", "angle": angle, "len": 300.0, "w0": 6.0, "w1": 46.0, "warn": warn_ticks, "live": live, "av": 0.0, "sweep": sweep, "shape": "cone"})

# Follow Spot: cone beams from two rigs above the box. Each marks its line, then
# lights and sweeps. Footlight notes rise on every beat.
static func _spotlights(s: Dictionary, t: int, stage: int) -> void:
	if t == 0: D.box_to(s, {"w": 236.0, "h": 112.0}, 20)
	# Spacing is in beats, kept near 1.5 / 1.2 beats at 120 BPM and eased at
	# faster tempos so the attack stays as dense in time.
	var b: int = _b(s)
	var every: int = (b * 3) / 2 if stage == 0 else (b * 6) / 5
	if b < 30: every = b * 2 if stage == 0 else (b * 3) / 2
	if t % every == 0 and t >= 30 and t < 420:
		var index: int = int(t / every) % 2
		var rig: Vector2 = s.rigs[index]
		var aim: float = (D.soul_world(s) - rig).angle() + D.rand_range(s, -0.25, 0.25)
		var sweep: float = (0.010 + stage * 0.003) * (1.0 if index == 0 else -1.0)
		_cone(s, rig, aim - sweep * 30.0, sweep)
		if stage >= 2 and t % (every * 2) == 0:
			var other: Vector2 = s.rigs[1 - index]
			_cone(s, other, (D.soul_world(s) - other).angle() + 0.5 * (1.0 if index == 0 else -1.0), -sweep * 0.7, 40, 40)
	if t % _b(s) == 0 and t < 440:
		var h: Vector2 = D.half(s)
		for i: int in range(maxi(1, roundi((2 + stage) * b / 30.0))):
			D.shot(s, {"space": "box", "x": D.rand_range(s, -h.x + 10.0, h.x - 10.0), "y": h.y + 6.0, "vy": -1.5 - stage * 0.2, "r": 3.5, "shape": "note", "rot": -PI / 2.0, "wave": {"amp": 7.0, "freq": 0.09, "phase": D.rand(s) * TAU}, "life": 200})

# Call and Response: the green soul. Notes arrive exactly on the beat from four
# sides. Later verses add eighth notes and turnaround notes.
static func _call_response(s: Dictionary, t: int, stage: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 72.0, "h": 72.0}, 24)
		D.set_mode(s, "green")
		D.banner(s, "HOLD YOUR GROUND", 50)
		s.callPlan = _plan_calls(s, stage)
	var soul: Vector2 = D.soul_world(s)
	var speed: float = 1.7 + stage * 0.25
	var distance: float = 150.0
	var travel: int = int(distance / speed)
	for call: Dictionary in s.callPlan:
		if int(call.arrive) - travel == t:
			var dir: Vector2 = call.dir
			var from: Vector2 = soul + dir * distance
			var props: Dictionary = {"target": true, "speed": speed}
			if call.cue: props.merge({"cue": true, "shape": "cue_note"}, true)
			if call.flip:
				# Arrives from the far side after a half turn at radius 46.
				from = soul - dir * distance
				props.merge({"flip": 0, "shape": "flip_note"}, true)
			_note(s, from, soul, speed, props)

static func _plan_calls(s: Dictionary, stage: int) -> Array:
	var dirs: Array[Vector2] = [Vector2.LEFT, Vector2.UP, Vector2.RIGHT, Vector2.DOWN]
	var plan: Array = []
	var last: int = 0
	var cue_beats: Array[int] = [5, 10, 14]
	for beat: int in range(2, 15):
		var arrive: int = beat * _b(s)
		var turn: int = 1 if D.rand(s) < 0.5 else -1
		if D.rand(s) < 0.25: turn = 2
		last = posmod(last + turn, 4)
		var flip: bool = stage >= 1 and beat % 4 == 3
		plan.append({"arrive": arrive, "dir": dirs[last], "cue": beat in cue_beats, "flip": flip})
		if stage == 0 and beat % 4 == 2:
			plan.append({"arrive": arrive + _b(s) / 2, "dir": dirs[posmod(last + 2, 4)], "cue": false, "flip": false})
		if stage >= 1 and beat % 2 == 0 and beat < 14:
			var off: int = posmod(last + (1 if D.rand(s) < 0.5 else -1), 4)
			plan.append({"arrive": arrive + _b(s) / 2, "dir": dirs[off], "cue": false, "flip": false})
		if stage >= 2 and beat % 3 == 1:
			plan.append({"arrive": arrive + _b(s) / 4, "dir": dirs[posmod(last + 2, 4)], "cue": false, "flip": false})
	return plan

# Feedback: rings with one gap expand from speakers just outside the box, one
# per beat. Later verses add a ceiling mic and darts that track you briefly.
static func _feedback(s: Dictionary, t: int, stage: int) -> void:
	if t == 0: D.box_to(s, {"w": 208.0, "h": 116.0}, 20)
	if t % _b(s) == 0 and t >= 30 and t < 430:
		var index: int = int(t / _b(s)) % 2
		var speaker: Vector2 = s.speakers[index]
		var toward: float = (D.soul_world(s) - speaker).angle()
		var offset: float = D.rand_range(s, 0.35, 0.7) * (1.0 if D.rand(s) < 0.5 else -1.0)
		D.shot(s, {"x": speaker.x, "y": speaker.y, "collide": "ring", "radius": 6.0, "grow": 1.45 + stage * 0.15, "thick": 2.0, "gap": toward + offset, "gapWidth": 0.62 * maxf(1.0, 30.0 / _b(s)), "gapSpin": 0.0 if stage < 2 else 0.002 * (1.0 if index == 0 else -1.0), "shape": "ring", "maxRadius": 360.0})
		D.effect(s, "pulse", speaker, 14)
	if stage >= 1 and t % (_b(s) * 4) == _b(s) * 2 + _b(s) / 2 and t < 420:
		var mic: Vector2 = Vector2(128, -36)
		D.shot(s, {"x": mic.x, "y": mic.y, "collide": "ring", "radius": 6.0, "grow": 1.2, "thick": 2.0, "gap": (D.soul_world(s) - mic).angle() + PI * 0.5, "gapWidth": 0.5, "shape": "ring", "maxRadius": 300.0})
		D.effect(s, "pulse", mic, 14)
	if t % 70 == 35 and t > 60 and t < 420:
		var speaker2: Vector2 = s.speakers[int(t / 70) % 2]
		var aim: Vector2 = (D.soul_world(s) - speaker2).normalized() * 2.0
		D.shot(s, {"x": speaker2.x, "y": speaker2.y, "vx": aim.x, "vy": aim.y, "home": 40 + stage * 20, "homeTurn": 0.035, "r": 2.5, "shape": "squeal", "life": 220})

# Curtain Call: the box squeezes shut on every downbeat and reopens, confetti
# sways down, roses are lobbed from the wings. Later verses bob the stage.
static func _curtain_call(s: Dictionary, t: int, stage: int) -> void:
	if t == 0: D.box_to(s, {"w": 268.0, "h": 112.0}, 20)
	if t % (_b(s) * 4) == _b(s) * 2 and t >= 60 and t < 420:
		D.warn(s, {"kind": "curtain"}, 26, true)
		D.box_to(s, {"w": 96.0 - stage * 8.0}, 26, 26, "in")
		D.box_to(s, {"w": 268.0}, 34, 70, "out")
		if stage >= 1:
			D.box_to(s, {"cy": 48.0}, 30, 26)
			D.box_to(s, {"cy": 64.0}, 30, 70)
	if t % 5 == 0 and t > 20 and t < 440:
		var h: Vector2 = D.half(s)
		D.shot(s, {"space": "box", "x": D.rand_range(s, -h.x, h.x), "y": -h.y - 6.0, "vy": D.rand_range(s, 0.9, 1.3), "r": 2.2, "shape": "confetti", "rot": D.rand(s) * TAU, "spin": 0.2, "wave": {"amp": 9.0, "freq": 0.06, "phase": D.rand(s) * TAU}, "life": 260, "hue": int(D.rand(s) * 4.0)})
	if t % (40 - stage * 8) == 20 and t < 420:
		var left: bool = D.rand(s) < 0.5
		var start: Vector2 = Vector2(-20.0 if left else 276.0, 140.0)
		var target: Vector2 = D.soul_world(s) + Vector2(D.rand_range(s, -12.0, 12.0), 0)
		var ticks: float = 70.0
		var g: float = 0.08
		var vx: float = (target.x - start.x) / ticks
		var vy: float = (target.y - start.y - 0.5 * g * ticks * ticks) / ticks
		D.shot(s, {"x": start.x, "y": start.y, "vx": vx, "vy": vy, "ay": g, "r": 4.0, "shape": "rose", "spin": 0.12 * (1.0 if left else -1.0), "life": 240})

# Final Verse: the box pans across the stage chasing a spotlight while waves of
# notes stream in and a ring bursts on each bar. Everything at once.
static func _finale(s: Dictionary, t: int, stage: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 164.0, "h": 104.0}, 20)
	if t % (_b(s) * 4) == 0 and t >= 30 and t < 420:
		var to_x: float = 128.0 + (60.0 if int(t / (_b(s) * 4)) % 2 == 0 else -60.0)
		D.box_to(s, {"cx": to_x}, 70, 0, "inout")
		s.rigs = [Vector2(128.0 + (to_x - 128.0) * 1.6, -40.0)]
		var rig: Vector2 = s.rigs[0]
		_cone(s, rig, (Vector2(to_x, 60.0) - rig).angle() - 0.5 * signf(to_x - 128.0), 0.012 * signf(to_x - 128.0), 34, 60)
	if t % 12 == 0 and t > 30 and t < 430:
		var from_right: bool = int(t / (_b(s) * 4)) % 2 == 0
		var y: float = 60.0 + sin(t * 0.05) * 40.0
		D.shot(s, {"x": 300.0 if from_right else -44.0, "y": y, "vx": -2.4 if from_right else 2.4, "r": 3.2, "shape": "note", "rot": PI if from_right else 0.0, "wave": {"amp": 5.0, "freq": 0.12}, "life": 260})
	if t % (_b(s) * 4) == _b(s) * 2 and t > 60 and t < 420:
		var c: Vector2 = D.centre(s) + Vector2(0, -80)
		D.shot(s, {"x": c.x, "y": c.y, "collide": "ring", "radius": 4.0, "grow": 1.5 + stage * 0.15, "thick": 2.0, "gap": (D.soul_world(s) - c).angle() + D.rand_range(s, -0.8, 0.8), "gapWidth": 0.55, "shape": "ring", "maxRadius": 300.0})
		D.effect(s, "pulse", c, 14)

## Beams turn by their sweep only once lit.
static func _sweep(s: Dictionary) -> void:
	for b: Dictionary in s.bullets:
		if b.collide == "beam":
			b.av = float(b.sweep) if int(b.age) >= int(b.warn) else 0.0

static func progress(s: Dictionary) -> String:
	return "Stopping cues %d/2 / verse %d/3" % [mini(2, int(s.cuesReached)), int(s.phase) + 1]

static func draw_under(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(_c: CanvasItem, _b: Dictionary, _at: Vector2, _turn: float, _alpha: float, _v: Node2D) -> bool:
	return false
