class_name DodgeBox
extends RefCounted
## Deltarune-style defend phase: a box that moves, resizes and turns, three soul
## modes and handmade per-boss pattern scripts (core/dodge_patterns_*.gd).
## Advance only at fixed 60 Hz; pause by not stepping. Coordinates are arena
## space: (0,0)-(256,120) is the resting box, drawn at main.gd's arena offset.
## Bullets live in arena space or, with space = "box", in box space (centre
## origin, unrotated) so they ride along when the box moves or turns. The soul
## always lives in box space; cursor mirrors it in arena space for main.gd.
## Soul modes: red moves freely, blue falls toward the box floor and jumps
## (precision ducks while grounded), green is pinned in the centre and turns a
## shield toward incoming notes, lanes hops between fixed columns, flipper runs
## along the floor and swings a flipper on confirm that returns "returnable"
## bullets. A pattern can also set audit = true: moving then is a hit.
##
## Each boss is one script, core/dodge_patterns_<id>.gd, found by file name.
## See core/DODGE_PATTERNS.md for the script contract and the objective system
## that carries each boss's promise.

const HOME: Vector2 = Vector2(128, 60)
const HOME_SIZE: Vector2 = Vector2(256, 120)
const SOUL_RADIUS: float = 3.0
const GRAZE_MARGIN: float = 9.0
const GRAZE_CAP: int = 15
const SHIELD_REACH: float = 17.0
const MASK: int = 0xffffffff
const PANEL_LEFT: float = -9.0
const PANEL_RIGHT: float = 265.0
static var _scripts: Dictionary = {}

## The flyer fight runs with an empty boss_id in main.gd.
static func normalize(id: String) -> String:
	return "flyer" if id.is_empty() else id

## Ticks per beat for a song tempo (60 Hz): 30 at 120 BPM, 25 at 144 BPM.
static func beat_ticks_for(bpm: float) -> int:
	return roundi(3600.0 / bpm) if bpm > 0.0 and is_finite(bpm) else 30

static func path_for(id: String) -> String:
	return "res://core/dodge_patterns_%s.gd" % normalize(id)

static func handles(id: String) -> bool:
	return ResourceLoader.exists(path_for(id))

static func script_for(id: String) -> GDScript:
	var key: String = normalize(id)
	if not _scripts.has(key): _scripts[key] = load(path_for(key))
	return _scripts[key]

## beat_ticks is ticks per beat of the boss song (3600 / BPM): 30 at 120 BPM.
static func create(id: String, seed: int, phase: int, music_tick: int, turn: int, beat_ticks: int = 30) -> Dictionary:
	id = normalize(id)
	var bt: int = clampi(beat_ticks, 15, 60)
	var rng: int = seed & MASK
	if rng == 0: rng = 0x6d2b79f5
	var origin: int = maxi(0, music_tick)
	var s: Dictionary = {
		"engine": "box", "encounterId": id, "seed": seed, "rng": rng, "phase": phase, "turn": maxi(0, turn),
		"clock": 0, "tick": 0, "accumulator": 0.0, "globalAccumulator": 0.0,
		"musicBase": origin, "beatTicks": bt, "leadIn": posmod(bt - origin % bt, bt), "beat": origin / bt, "beatPulse": false,
		"box": {"cx": HOME.x, "cy": HOME.y, "w": HOME_SIZE.x, "h": HOME_SIZE.y, "rot": 0.0}, "tweens": [],
		"soul": {"x": 0.0, "y": 0.0, "mode": "red", "v": 0.0, "grounded": true, "hold": 0, "shield": Vector2.UP, "gravity": Vector2.DOWN, "ducking": false, "lane": 0, "lastHop": 0},
		"lanes": [], "laneY": 40.0, "floorY": 48.0, "flipperTicks": 0, "flipperSuccess": false, "deflections": 0, "audit": false,
		"objectives": [], "objectiveCount": 0, "objectiveChanged": false, "revision": "", "rejected": [],
		"cursor": {"x": HOME.x, "y": HOME.y}, "wind": Vector2.ZERO,
		"bullets": [], "effects": [], "warnings": [], "telegraphs": [], "hazards": [], "markers": [], "props": [],
		"invulnerability": 0, "hit": false, "hits": 0, "grazes": 0, "grazeDelta": 0, "done": false, "promiseComplete": false,
		"promised": false, "pressed": false, "banner": "", "bannerTicks": 0, "nextId": 1,
		"wardTicks": 0, "wardPocket": Rect2(104, 82, 48, 34), "boundary": false,
		"lantern": 100, "gustsKept": 0, "lanternRaised": 0, "cuesReached": 0, "cues": [],
	}
	script_for(id).setup(s)
	s.duration = int(s.leadIn) + int(s.length)
	return s

# ---------------------------------------------------------------- helpers

static func rand(s: Dictionary) -> float:
	var value: int = int(s.rng) & MASK
	value = (value ^ (value << 13)) & MASK
	value = (value ^ (value >> 17)) & MASK
	value = (value ^ (value << 5)) & MASK
	s.rng = value
	return float(value) / 4294967296.0

static func rand_range(s: Dictionary, low: float, high: float) -> float:
	return low + (high - low) * rand(s)

static func centre(s: Dictionary) -> Vector2:
	return Vector2(float(s.box.cx), float(s.box.cy))

static func half(s: Dictionary) -> Vector2:
	return Vector2(float(s.box.w), float(s.box.h)) * 0.5

static func to_world(s: Dictionary, local: Vector2) -> Vector2:
	return centre(s) + local.rotated(float(s.box.rot))

static func to_local(s: Dictionary, world: Vector2) -> Vector2:
	return (world - centre(s)).rotated(-float(s.box.rot))

static func soul_world(s: Dictionary) -> Vector2:
	return to_world(s, Vector2(float(s.soul.x), float(s.soul.y)))

static func corners(s: Dictionary, grow: float = 0.0) -> PackedVector2Array:
	var h: Vector2 = half(s) + Vector2(grow, grow)
	return PackedVector2Array([to_world(s, Vector2(-h.x, -h.y)), to_world(s, Vector2(h.x, -h.y)), to_world(s, Vector2(h.x, h.y)), to_world(s, Vector2(-h.x, h.y))])

## Tween box fields (cx, cy, w, h, rot) to target values over dur ticks, starting
## delay ticks from now. The start value is read when the tween begins.
static func box_to(s: Dictionary, target: Dictionary, dur: int, delay: int = 0, ease: String = "inout") -> void:
	for key: String in target:
		s.tweens.append({"key": key, "to": float(target[key]), "start": int(s.clock) + delay, "dur": maxi(1, dur), "ease": ease, "from": null})

static func _ease(p: float, kind: String) -> float:
	match kind:
		"linear": return p
		"in": return p * p
		"out": return 1.0 - (1.0 - p) * (1.0 - p)
		"back": return 1.0 + 2.70158 * pow(p - 1.0, 3) + 1.70158 * pow(p - 1.0, 2)
	return p * p * (3.0 - 2.0 * p)

## Spawn a bullet. Unset keys take defaults; see _update_bullet for behaviours.
static func shot(s: Dictionary, props: Dictionary) -> Dictionary:
	var b: Dictionary = {"id": int(s.nextId), "x": 0.0, "y": 0.0, "vx": 0.0, "vy": 0.0, "ax": 0.0, "ay": 0.0, "r": 4.0, "w": 4.0, "h": 4.0,
		"shape": "dot", "rot": 0.0, "spin": 0.0, "age": 0, "life": 900, "collide": "circle", "space": "arena", "grazed": false, "dead": false, "arm": 0}
	b.merge(props, true)
	b.px = b.x; b.py = b.y
	s.nextId = int(s.nextId) + 1
	s.bullets.append(b)
	return b

## A draw-only telegraph. loud ones also beep through main.gd's warning sound.
static func warn(s: Dictionary, props: Dictionary, life: int, loud: bool = false) -> void:
	var w: Dictionary = {"kind": "line", "age": 0, "life": life, "space": "arena"}
	w.merge(props, true)
	s.warnings.append(w)
	if loud: s.telegraphs.append({"ticksRemaining": life})

static func effect(s: Dictionary, kind: String, at: Vector2, life: int = 18, extra: Dictionary = {}) -> void:
	var e: Dictionary = {"kind": kind, "x": at.x, "y": at.y, "age": 0, "life": life}
	e.merge(extra, true)
	s.effects.append(e)

static func banner(s: Dictionary, text: String, ticks: int = 60) -> void:
	s.banner = text; s.bannerTicks = ticks

static func set_mode(s: Dictionary, mode: String) -> void:
	s.soul.mode = mode
	s.soul.v = 0.0; s.soul.grounded = false; s.soul.hold = 0
	if mode == "green":
		s.soul.x = 0.0; s.soul.y = 0.0
	elif mode == "lanes" and s.lanes.size() > 0:
		var best: int = 0
		for i: int in range(s.lanes.size()):
			if absf(float(s.lanes[i]) - float(s.soul.x)) < absf(float(s.lanes[best]) - float(s.soul.x)): best = i
		s.soul.lane = best
	effect(s, "mode", soul_world(s), 24)

## Add a promise objective in box space. kind: "touch" (collected on contact),
## "confirm" (contact + confirm), "hold" (stay inside for need ticks), "avoid"
## (entering sets broken). Shape is a circle of radius r, or a rect when w and h
## are given (half sizes). Scripts toggle active and read done / progress.
## Touch, confirm and hold only count while promised, unless free = true.
static func objective(s: Dictionary, props: Dictionary) -> Dictionary:
	var o: Dictionary = {"id": s.objectives.size(), "kind": "confirm", "x": 0.0, "y": 0.0, "r": 14.0, "w": 0.0, "h": 0.0,
		"active": true, "done": false, "broken": false, "need": 60, "progress": 0, "label": "", "always": false, "doneAt": -1}
	o.merge(props, true)
	s.objectives.append(o)
	return o

static func inside(s: Dictionary, o: Dictionary, local: Vector2 = Vector2.INF) -> bool:
	var at: Vector2 = Vector2(float(s.soul.x), float(s.soul.y)) if local == Vector2.INF else local
	if float(o.w) > 0.0:
		return absf(at.x - float(o.x)) <= float(o.w) and absf(at.y - float(o.y)) <= float(o.h)
	return at.distance_to(Vector2(float(o.x), float(o.y))) <= float(o.r)

static func _complete(s: Dictionary, o: Dictionary) -> void:
	o.done = true
	o.doneAt = int(s.clock)
	s.objectiveCount = int(s.objectiveCount) + 1
	s.objectiveChanged = true
	effect(s, "kept", to_world(s, Vector2(float(o.x), float(o.y))), 30)

## Like the old encounters, objectives only count while a promise is active
## (battle.promise), unless the objective is marked free (Todd's consent boxes).
static func _counts(s: Dictionary, o: Dictionary) -> bool:
	return bool(s.promised) or bool(o.get("free", false))

static func _objective_confirm(s: Dictionary) -> void:
	for o: Dictionary in s.objectives:
		if o.kind == "confirm" and o.active and not o.done and _counts(s, o) and inside(s, o):
			_complete(s, o)
			return

static func _objective_tick(s: Dictionary) -> void:
	for o: Dictionary in s.objectives:
		if not o.active or o.done: continue
		match str(o.kind):
			"touch":
				if _counts(s, o) and inside(s, o): _complete(s, o)
			"hold":
				if _counts(s, o) and inside(s, o):
					o.progress = int(o.progress) + 1
					if int(o.progress) >= int(o.need): _complete(s, o)
			"avoid":
				if inside(s, o) and not o.broken:
					o.broken = true
					effect(s, "hit", soul_world(s), 20)

# ---------------------------------------------------------------- stepping

static func step(p: Dictionary, axis: Vector2, precision: bool = false, assist: float = 1.0, slow: bool = false, promised: bool = false, pressed: bool = false) -> Dictionary:
	p.hit = false; p.grazeDelta = 0; p.beatPulse = false; p.objectiveChanged = false; p.flipperSuccess = false
	p.promised = promised
	if p.done: return p
	var scale: float = clampf(assist if is_finite(assist) else 1.0, 0.1, 1.0)
	var input: Vector2 = Vector2(clampf(axis.x if is_finite(axis.x) else 0.0, -1.0, 1.0), clampf(axis.y if is_finite(axis.y) else 0.0, -1.0, 1.0))
	p.pressed = pressed
	var before: Vector2 = Vector2(float(p.soul.x), float(p.soul.y))
	_move_soul(p, input, precision, scale, pressed)
	if bool(p.audit) and input.length_squared() > 0.01:
		_hurt(p, soul_world(p))
	if pressed:
		if str(p.soul.mode) == "flipper" and int(p.flipperTicks) == 0: p.flipperTicks = 12
		_objective_confirm(p)
		script_for(str(p.encounterId)).confirm(p)
	p.tick = int(p.tick) + 1
	p.globalAccumulator = float(p.globalAccumulator) + scale
	while float(p.globalAccumulator) >= 1.0:
		p.globalAccumulator = float(p.globalAccumulator) - 1.0
		p.invulnerability = maxi(0, int(p.invulnerability) - 1)
		p.lanternRaised = maxi(0, int(p.lanternRaised) - 1)
		p.flipperTicks = maxi(0, int(p.flipperTicks) - 1)
	p.accumulator = float(p.accumulator) + scale * (0.8 if slow else 1.0)
	while float(p.accumulator) >= 1.0 and not p.done:
		p.accumulator = float(p.accumulator) - 1.0
		_pattern_tick(p)
	return p

static func _move_soul(p: Dictionary, input: Vector2, precision: bool, scale: float, pressed: bool) -> void:
	var soul: Dictionary = p.soul
	var rot: float = float(p.box.rot)
	var local_input: Vector2 = input.rotated(-rot)
	var h: Vector2 = half(p) - Vector2(4, 4)
	h = Vector2(maxf(0.0, h.x), maxf(0.0, h.y))
	soul.ducking = false
	match str(soul.mode):
		"lanes":
			var lanes: Array = p.lanes
			if lanes.size() > 0:
				var sign_x: int = int(signf(local_input.x)) if absf(local_input.x) > 0.25 else 0
				if sign_x != 0 and sign_x != int(soul.lastHop):
					soul.lane = clampi(int(soul.lane) + sign_x, 0, lanes.size() - 1)
					effect(p, "hop", soul_world(p), 10)
				soul.lastHop = sign_x
				var target: float = float(lanes[clampi(int(soul.lane), 0, lanes.size() - 1)])
				soul.x = move_toward(float(soul.x), target, 9.0 * scale)
				soul.y = float(p.laneY)
		"flipper":
			var speed_f: float = (72.0 if precision else 128.0) / 60.0 * scale
			soul.x = clampf(float(soul.x) + local_input.x * speed_f, -h.x, h.x)
			soul.y = minf(float(p.floorY), h.y)
		"green":
			if input.length_squared() > 0.25:
				soul.shield = Vector2(signf(input.x), 0) if absf(input.x) >= absf(input.y) else Vector2(0, signf(input.y))
			soul.x = 0.0; soul.y = 0.0
		"blue":
			var g: Vector2 = soul.gravity
			var side: Vector2 = Vector2(-g.y, g.x)
			var speed: float = (64.0 if precision else 104.0) / 60.0 * scale
			var pos: Vector2 = Vector2(float(soul.x), float(soul.y)) + side * local_input.dot(side) * speed
			var up_held: bool = local_input.dot(-g) > 0.5 or int(soul.hold) > 0
			if precision and soul.grounded and not pressed and local_input.dot(-g) <= 0.5:
				soul.ducking = true
				up_held = false
			if pressed: soul.hold = 12
			soul.hold = maxi(0, int(soul.hold) - 1)
			if soul.grounded and (up_held or pressed):
				soul.grounded = false
				soul.v = -3.7
			if not soul.grounded:
				soul.v = float(soul.v) + (0.17 if up_held and float(soul.v) < 0.0 else 0.42) * scale
				soul.v = minf(float(soul.v), 5.5)
			pos += g * float(soul.v) * scale
			pos += Vector2(p.wind).rotated(-rot) * scale
			var floor_hit: bool = (g.y > 0.5 and pos.y >= h.y) or (g.y < -0.5 and pos.y <= -h.y) or (g.x > 0.5 and pos.x >= h.x) or (g.x < -0.5 and pos.x <= -h.x)
			pos = pos.clamp(-h, h)
			if floor_hit and float(soul.v) >= 0.0:
				soul.grounded = true; soul.v = 0.0
			elif not floor_hit and soul.grounded:
				soul.grounded = false
			soul.x = pos.x; soul.y = pos.y
		_:
			var speed: float = (64.0 if precision else 112.0) / 60.0 * scale
			var move: Vector2 = local_input / maxf(1.0, local_input.length()) * speed
			move += Vector2(p.wind).rotated(-rot) * scale
			var pos: Vector2 = (Vector2(float(soul.x), float(soul.y)) + move).clamp(-h, h)
			soul.x = pos.x; soul.y = pos.y
	var world: Vector2 = soul_world(p)
	p.cursor = {"x": world.x, "y": world.y}

static func _pattern_tick(p: Dictionary) -> void:
	var absolute: int = int(p.clock) + int(p.musicBase)
	p.beat = absolute / int(p.beatTicks)
	p.beatPulse = bool(p.beatPulse) or absolute % int(p.beatTicks) == 0
	p.wardTicks = maxi(0, int(p.wardTicks) - 1)
	_run_tweens(p)
	var t: int = int(p.clock) - int(p.leadIn)
	var script: GDScript = script_for(str(p.encounterId))
	if t >= 0 and int(p.clock) < int(p.duration) - 40:
		script.tick(p, t)
	if int(p.clock) == int(p.duration) - 40:
		_wind_down(p)
	# The soul is re-clamped every tick so a shrinking box pushes it inward.
	var h: Vector2 = half(p) - Vector2(4, 4)
	h = Vector2(maxf(0.0, h.x), maxf(0.0, h.y))
	var local: Vector2 = Vector2(float(p.soul.x), float(p.soul.y)).clamp(-h, h)
	p.soul.x = local.x; p.soul.y = local.y
	var world: Vector2 = soul_world(p)
	p.cursor = {"x": world.x, "y": world.y}
	_objective_tick(p)
	var live: Array = []
	for b: Dictionary in p.bullets:
		_update_bullet(p, b)
		if b.dead: continue
		_collide(p, b, world, local)
		if not b.dead: live.append(b)
	p.bullets = live.slice(maxi(0, live.size() - 320))
	for list: String in ["effects", "warnings"]:
		var kept: Array = []
		for e: Dictionary in p[list]:
			e.age = int(e.age) + 1
			if int(e.age) < int(e.life): kept.append(e)
		p[list] = kept
	var tells: Array = []
	for tell: Dictionary in p.telegraphs:
		tell.ticksRemaining = int(tell.ticksRemaining) - 1
		if int(tell.ticksRemaining) > 0: tells.append(tell)
	p.telegraphs = tells
	p.bannerTicks = maxi(0, int(p.bannerTicks) - 1)
	script.after(p, t)
	p.clock = int(p.clock) + 1
	if int(p.clock) >= int(p.duration):
		p.done = true
		p.bullets = []; p.warnings = []; p.telegraphs = []
	var complete: bool = bool(script.promise_complete(p))
	# Keeping a promise ends the attack early: it winds down about 1.7 s later, so nobody gets
	# knocked out in "extra time" after the job is done. Only an objective that was open and
	# then got done counts (one that starts complete, like "never touch X", runs full length).
	if bool(p.promised) and t >= 0:
		if not complete: p.promiseOpen = true
		elif bool(p.get("promiseOpen", false)) and not bool(p.get("keptEarly", false)):
			p.keptEarly = true
			p.duration = mini(int(p.duration), int(p.clock) + 100)
	p.promiseComplete = complete

static func _wind_down(p: Dictionary) -> void:
	p.wind = Vector2.ZERO
	for b: Dictionary in p.bullets:
		b.fade = 24
	box_to(p, {"cx": HOME.x, "cy": HOME.y, "w": HOME_SIZE.x, "h": HOME_SIZE.y, "rot": 0.0}, 30)
	if str(p.soul.mode) != "red": set_mode(p, "red")
	p.soul.gravity = Vector2.DOWN

static func _run_tweens(p: Dictionary) -> void:
	var kept: Array = []
	for tw: Dictionary in p.tweens:
		var elapsed: int = int(p.clock) - int(tw.start)
		if elapsed < 0:
			kept.append(tw); continue
		if tw.from == null: tw.from = float(p.box[tw.key])
		var progress: float = clampf(float(elapsed + 1) / float(tw.dur), 0.0, 1.0)
		p.box[tw.key] = lerpf(float(tw.from), float(tw.to), _ease(progress, str(tw.ease)))
		if progress < 1.0: kept.append(tw)
	p.tweens = kept
	_keep_between_panels(p)

## main.gd's defend layout has panels left and right of the arena (screen x 184
## and 456, arena x -8 and 264). Slide the box back so its turned outline stays
## between them; a box too wide to fit stays centred.
static func _keep_between_panels(p: Dictionary) -> void:
	var rot: float = float(p.box.rot)
	var reach: float = absf(float(p.box.w) * 0.5 * cos(rot)) + absf(float(p.box.h) * 0.5 * sin(rot))
	var low: float = PANEL_LEFT + reach
	var high: float = PANEL_RIGHT - reach
	p.box.cx = clampf(float(p.box.cx), low, high) if low <= high else (PANEL_LEFT + PANEL_RIGHT) * 0.5

## Behaviours, read from optional keys:
## vx/vy + ax/ay (acceleration), drag; orbit {ox, oy, radius, angle, av, dr};
## wave {amp, freq} sideways sway around the travel line; home (ticks of steering
## toward the soul, turn rate homeTurn); bounce (box space floor restitution);
## ring {radius, grow, thick, gap, gapWidth, gapSpin}; beam {angle, len, w0, w1,
## warn, live, av}; target (green-mode notes fly to the soul); fade (despawn ticks).
static func _update_bullet(p: Dictionary, b: Dictionary) -> void:
	b.age = int(b.age) + 1
	if int(b.age) > int(b.life):
		b.dead = true; return
	if b.has("fade"):
		b.fade = int(b.fade) - 1
		if int(b.fade) <= 0: b.dead = true; return
	b.px = b.x; b.py = b.y
	b.rot = float(b.rot) + float(b.spin)
	if b.has("orbit"):
		var o: Dictionary = b.orbit
		o.angle = float(o.angle) + float(o.get("av", 0.0))
		o.radius = float(o.radius) + float(o.get("dr", 0.0))
		b.x = float(o.ox) + cos(float(o.angle)) * float(o.radius)
		b.y = float(o.oy) + sin(float(o.angle)) * float(o.radius)
		if float(o.radius) < float(o.get("minRadius", -INF)) or float(o.radius) > float(o.get("maxRadius", INF)): b.dead = true
		return
	if b.collide == "ring":
		b.radius = float(b.radius) + float(b.grow)
		b.gap = float(b.gap) + float(b.get("gapSpin", 0.0))
		if float(b.radius) > float(b.get("maxRadius", 420.0)): b.dead = true
		return
	if b.collide == "beam":
		b.angle = float(b.angle) + float(b.get("av", 0.0))
		b.x = float(b.x) + float(b.vx); b.y = float(b.y) + float(b.vy)
		if int(b.age) >= int(b.warn) + int(b.live): b.dead = true
		return
	if int(b.age) <= int(b.arm) and b.has("hold"):
		return
	if b.has("home") and int(b.home) > 0:
		b.home = int(b.home) - 1
		var aim: Vector2 = (_soul_in(p, b) - Vector2(float(b.x), float(b.y)))
		var velocity: Vector2 = Vector2(float(b.vx), float(b.vy))
		var turned: Vector2 = velocity.rotated(clampf(velocity.angle_to(aim), -float(b.get("homeTurn", 0.05)), float(b.get("homeTurn", 0.05))))
		b.vx = turned.x; b.vy = turned.y
	b.vx = float(b.vx) + float(b.ax); b.vy = float(b.vy) + float(b.ay)
	if b.has("drag"):
		b.vx = float(b.vx) * float(b.drag); b.vy = float(b.vy) * float(b.drag)
	if b.has("wave"):
		var w: Dictionary = b.wave
		w.bx = float(w.get("bx", b.x)) + float(b.vx); w.by = float(w.get("by", b.y)) + float(b.vy)
		var dir: Vector2 = Vector2(float(b.vx), float(b.vy)).normalized()
		var sway: float = float(w.amp) * sin(float(b.age) * float(w.freq) + float(w.get("phase", 0.0)))
		b.x = float(w.bx) - dir.y * sway; b.y = float(w.by) + dir.x * sway
	else:
		b.x = float(b.x) + float(b.vx); b.y = float(b.y) + float(b.vy)
	if b.has("bounce") and b.space == "box":
		var floor_y: float = half(p).y - float(b.r)
		if float(b.y) > floor_y and float(b.vy) > 0.0:
			b.y = floor_y; b.vy = -absf(float(b.vy)) * float(b.bounce)
	var at: Vector2 = Vector2(float(b.x), float(b.y))
	var reach: float = 460.0
	if b.space == "box": reach = maxf(half(p).x, half(p).y) + 120.0
	var origin: Vector2 = Vector2.ZERO if b.space == "box" else centre(p)
	if at.distance_to(origin) > reach and int(b.age) > 30: b.dead = true

static func _soul_in(p: Dictionary, b: Dictionary) -> Vector2:
	return Vector2(float(p.soul.x), float(p.soul.y)) if b.space == "box" else soul_world(p)

static func bullet_world(p: Dictionary, b: Dictionary) -> Vector2:
	var at: Vector2 = Vector2(float(b.x), float(b.y))
	return to_world(p, at) if b.space == "box" else at

static func _segment(point: Vector2, a: Vector2, b: Vector2) -> float:
	var line: Vector2 = b - a
	var progress: float = clampf((point - a).dot(line) / maxf(0.00001, line.length_squared()), 0.0, 1.0)
	return point.distance_to(a + line * progress)

## Signed clearance between the soul and a bullet's edge (<= 0 is a hit).
static func clearance(p: Dictionary, b: Dictionary, soul: Vector2) -> float:
	var at: Vector2 = Vector2(float(b.x), float(b.y))
	match str(b.collide):
		"none": return INF
		"rect":
			var d: Vector2 = (soul - at).rotated(-float(b.rot))
			var out: Vector2 = Vector2(maxf(0.0, absf(d.x) - float(b.w)), maxf(0.0, absf(d.y) - float(b.h)))
			return out.length() - SOUL_RADIUS
		"ring":
			var delta: Vector2 = soul - at
			if absf(wrapf(delta.angle() - float(b.gap), -PI, PI)) < float(b.gapWidth) * 0.5: return INF
			return absf(delta.length() - float(b.radius)) - float(b.thick) - SOUL_RADIUS
		"beam":
			if int(b.age) < int(b.warn): return INF
			var dir: Vector2 = Vector2.from_angle(float(b.angle))
			var along: float = clampf((soul - at).dot(dir), 0.0, float(b.len))
			var width: float = lerpf(float(b.w0), float(b.w1), along / maxf(1.0, float(b.len))) * 0.5
			return soul.distance_to(at + dir * along) - width - SOUL_RADIUS
	return _segment(soul, Vector2(float(b.px), float(b.py)), at) - float(b.r) - SOUL_RADIUS

## Damage the soul at an arena-space point (for script-side hazards such as
## Todd's audit or VAL's reserved chairs). Same rules as a bullet hit.
static func hurt(p: Dictionary, world: Vector2) -> void:
	_hurt(p, world)

## Hits respect Lantern Ward's pocket (it follows the box) and any safe rects
## a pattern lists in box space (p.safe, an Array of Rect2).
static func _hurt(p: Dictionary, world: Vector2) -> void:
	var local: Vector2 = to_local(p, world)
	var shielded: bool = int(p.wardTicks) > 0 and Rect2(Vector2(p.wardPocket.position) + centre(p) - HOME, p.wardPocket.size).has_point(world)
	for zone: Rect2 in p.get("safe", []):
		if zone.has_point(local): shielded = true
	if int(p.invulnerability) == 0 and not shielded:
		p.hit = true; p.hits = int(p.hits) + 1
		p.invulnerability = 45
		effect(p, "hit", world, 20)

static func _flip(p: Dictionary, b: Dictionary) -> bool:
	if str(p.soul.mode) != "flipper" or int(p.flipperTicks) == 0 or not b.get("returnable", false) or b.get("friendly", false): return false
	var at: Vector2 = Vector2(float(b.x), float(b.y)) if b.space == "box" else to_local(p, Vector2(float(b.x), float(b.y)))
	var paddle: Vector2 = Vector2(float(p.soul.x), float(p.soul.y))
	if absf(at.x - paddle.x) > 26.0 or at.y < paddle.y - 22.0 or at.y > paddle.y + 8.0: return false
	b.friendly = true
	var out: Vector2 = Vector2((at.x - paddle.x) * 0.09, -3.4)
	if b.space != "box": out = out.rotated(float(p.box.rot))
	b.vx = out.x; b.vy = out.y; b.ax = 0.0; b.ay = 0.0
	b.erase("home"); b.erase("wave")
	p.deflections = int(p.deflections) + 1
	p.flipperSuccess = true
	p.flipperTicks = 0
	effect(p, "block", bullet_world(p, b), 14, {"cue": true})
	return true

static func _collide(p: Dictionary, b: Dictionary, world: Vector2, local: Vector2) -> void:
	if int(b.age) <= int(b.arm) or b.has("fade") or b.get("friendly", false): return
	if _flip(p, b): return
	if bool(p.soul.ducking):
		var g: Vector2 = p.soul.gravity
		local = local + g * 3.0
		world = to_world(p, local)
	var soul: Vector2 = local if b.space == "box" else world
	if str(p.soul.mode) == "green" and b.get("target", false):
		var offset: Vector2 = Vector2(float(b.x), float(b.y)) - soul
		if offset.length() <= SHIELD_REACH + float(b.r):
			var facing: Vector2 = Vector2(p.soul.shield) if b.space == "arena" else Vector2(p.soul.shield).rotated(-float(p.box.rot))
			if facing.dot(offset.normalized()) > 0.7:
				b.dead = true
				effect(p, "block", bullet_world(p, b), 14, {"cue": b.get("cue", false)})
				if b.get("cue", false):
					p.cuesReached = int(p.cuesReached) + 1
				return
	var gap: float = clearance(p, b, soul) + (1.5 if bool(p.soul.ducking) else 0.0)
	if gap <= 0.0:
		if b.get("cue", false):
			b.dead = true; return
		_hurt(p, world)
		if b.get("pierce", true) == false: b.dead = true
	elif gap <= GRAZE_MARGIN and not b.grazed and not b.get("cue", false):
		b.grazed = true
		if int(p.grazes) < GRAZE_CAP:
			p.grazes = int(p.grazes) + 1
			p.grazeDelta = int(p.grazeDelta) + 1
			effect(p, "graze", world, 12)

# ---------------------------------------------------------------- autopilot hints

## Where the QA autopilot should head (arena space), or null. The first active,
## unfinished objective that is not an avoid zone; scripts can override with
## p.botGoal (box space) when the promise is something else.
static func bot_goal(p: Dictionary) -> Variant:
	if p.has("botGoal") and p.botGoal != null: return to_world(p, Vector2(p.botGoal))
	for o: Dictionary in p.objectives:
		if o.active and not o.done and o.kind != "avoid":
			return to_world(p, Vector2(float(o.x), float(o.y)))
	return null

static func bot_press(p: Dictionary) -> bool:
	if bool(p.get("botPress", false)): return true
	for o: Dictionary in p.objectives:
		if o.kind == "confirm" and o.active and not o.done and inside(p, o): return true
	if str(p.soul.mode) == "flipper" and int(p.flipperTicks) == 0:
		var paddle: Vector2 = Vector2(float(p.soul.x), float(p.soul.y))
		for b: Dictionary in p.bullets:
			if not b.get("returnable", false) or b.get("friendly", false): continue
			var at: Vector2 = Vector2(float(b.x), float(b.y)) if b.space == "box" else to_local(p, Vector2(float(b.x), float(b.y)))
			if absf(at.x - paddle.x) < 22.0 and at.y > paddle.y - 18.0 and at.y < paddle.y + 4.0 and float(b.vy) > 0.0: return true
	return false

## Cost of standing at a box-space point for avoid zones (used by the autopilot).
static func bot_avoid(p: Dictionary, local: Vector2) -> float:
	var cost: float = 0.0
	for o: Dictionary in p.objectives:
		if o.kind == "avoid" and o.active and inside(p, o, local): cost += 500.0
	return cost
