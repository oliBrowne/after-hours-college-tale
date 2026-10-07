class_name EncounterDirector
extends RefCounted
## Five distinct authored minigames. Advance only at fixed 60 Hz; pause by not
## stepping. Actor HP and party size remain the battle controller's responsibility.
## Rectangles and angular sectors MUST be rendered with their collision geometry.
const Base = preload("res://core/pattern.gd")
const MASK: int = 0xffffffff
const BEAT: int = 30

static func profile(id: String) -> Dictionary:
	match id:
		"claim": return {"id": id, "profileName": "CLAIM / Lost Property", "instructions": "Carry the marked tag through a sweep. Then deliver one thing and leave a note.", "promise": "Carry one tag; later return one item with an honest boundary.", "phaseName": "Hold On To This", "duration": 480}
		"chip": return {"id": id, "profileName": "Chip / Confetti Hop", "instructions": "Tap left/right to hop columns. Follow the outlined safe column.", "promise": "Reach three called columns.", "phaseName": "Confetti Grid", "duration": 480}
		"deion": return {"id": id, "profileName": "Deion / Hurdle Run", "instructions": "Confirm jumps. Hold precision to duck. You run at fixed X.", "promise": "Clear two hurdles and claim the airborne relay flag.", "phaseName": "Jump / Duck Relay", "duration": 480}
		"todd": return {"id": id, "profileName": "Todd / Stamp Audit", "instructions": "Walk between stamps. Stay still on red AUDIT. Confirm near both boxes.", "promise": "Sign both consent boxes.", "phaseName": "Rotating Audit", "duration": 540}
		"pinpal": return {"id": id, "profileName": "Pin Pal / Return Service", "instructions": "Move left/right. Confirm near a falling ball to flip it back.", "promise": "Return three balls.", "phaseName": "Bumper Flipper", "duration": 480}
		_: return {"id": "flyer", "profileName": "Flyerer / Paper Orbit", "instructions": "Move through the rotating paper gaps. Confirm briefly fends off close paper.", "promise": "Read the outlined invitation.", "phaseName": "Paper Rings", "duration": 420}

static func create(id: String, seed: int, phase: int = 0, music_tick: int = 0) -> Dictionary:
	var state: Dictionary = Base.create(seed)
	var definition: Dictionary = profile(id)
	var origin: int = maxi(0, music_tick)
	state.encounterId = definition.id
	state.profileName = definition.profileName
	state.instructions = definition.instructions
	state.phaseName = definition.phaseName
	state.mechanicInfo = definition.instructions
	state.phase = clampi(phase, 0, 2)
	state.musicBase = origin
	state.leadIn = posmod(30 - origin % 30, 30)
	state.duration = int(state.leadIn) + int(definition.duration) + int(state.phase) * 60
	state.beat = origin / 30
	state.beatPulse = false
	state.audit = false
	state.arenaRadius = 58.0
	state.safeColumn = 128.0
	state.safeLane = 60.0
	state.column = 2
	state.lastInputX = 0
	state.columnsReached = 0
	state.jumpVelocity = 0.0
	state.grounded = true
	state.ducking = false
	state.runnerCleared = 0
	state.deflections = 0
	state.flipperTicks = 0
	state.flipperSuccess = false
	state.gapBoostUntil = -1
	state.paperFlashCooldown = 0
	state.consentCount = 0
	state.carryTag = false
	state.claimSweepPassed = 0
	state.noteLeft = false
	state.delivery = -1
	state.boundary = true
	state.markers = [{"id": 0, "x": 198.0, "y": 60.0, "collected": false, "active": true}]
	if state.encounterId == "chip":
		state.cursor = {"x": 128.0, "y": 92.0}
		state.markers = [{"id": 0, "x": 128.0, "y": 92.0, "collected": false, "active": true}]
	elif state.encounterId == "deion":
		state.cursor = {"x": 64.0, "y": 96.0}
		state.markers = [{"id": 0, "x": 64.0, "y": 55.0, "collected": false, "active": true}]
	elif state.encounterId == "todd":
		state.markers = [{"id": 0, "x": 98.0, "y": 60.0, "collected": false, "active": true}, {"id": 1, "x": 158.0, "y": 60.0, "collected": false, "active": true}]
	elif state.encounterId == "pinpal":
		state.cursor = {"x": 128.0, "y": 104.0}
		state.markers = [{"id": 0, "x": 128.0, "y": 104.0, "collected": false, "active": false}]
	elif state.encounterId == "claim":
		state.duration = int(state.leadIn) + 480
		state.phaseName = "Hold On To This" if int(state.phase) == 0 else "One Thing Now"
		if int(state.phase) == 0:
			state.markers = [{"id": 0, "x": 80.0, "y": 60.0, "collected": false, "active": true}, {"id": 1, "x": 204.0, "y": 36.0, "collected": false, "active": false}]
		else:
			state.instructions = "Pick up a tag. Confirm at ONE destination; leave a note for the other."
			state.markers = [{"id": 0, "x": 128.0, "y": 60.0, "collected": false, "active": true}, {"id": 1, "x": 56.0, "y": 36.0, "collected": false, "active": false}, {"id": 2, "x": 200.0, "y": 100.0, "collected": false, "active": false}]
	return state

static func _q(value: float, scale: float = 1024.0) -> float:
	return roundf(value * scale) / scale

static func _random(state: Dictionary) -> float:
	var value: int = int(state.rng)
	value = (value ^ (value << 13)) & MASK
	value = (value ^ (value >> 17)) & MASK
	value = (value ^ (value << 5)) & MASK
	state.rng = value
	return float(value) / 4294967296.0

static func _tell(state: Dictionary, data: Dictionary, delay: int = 60) -> void:
	var tell: Dictionary = data.duplicate(true)
	tell.id = int(state.nextId)
	tell.ticksRemaining = delay
	tell.direction = tell.get("direction", "right")
	tell.y = tell.get("y", 60.0)
	tell.x = tell.get("x", 128.0)
	state.nextId = int(state.nextId) + 1
	state.telegraphs.append(tell)

static func _schedule(state: Dictionary, relative: int) -> void:
	var phase: int = int(state.phase)
	match str(state.encounterId):
		"claim":
			if phase == 0:
				if relative % 90 == 0:
					_tell(state, {"kind": "linear", "shape": "claim_tag", "x": 32.0 + floorf(_random(state) * 5.0) * 48.0, "y": -14.0, "vx": 0.0, "vy": 2.5})
				if relative % 180 == 90:
					_tell(state, {"kind": "linear", "shape": "claim_sweep", "x": 278.0, "y": 96.0, "vx": -4.0, "vy": 0.0, "collision": "rect", "halfWidth": 10.0, "halfHeight": 9.0})
			elif relative % 120 == 0:
				var safe_row: int = int(floorf(_random(state) * 3.0))
				state.safeLane = 28.0 + safe_row * 32.0
				for row: int in range(3):
					if row != safe_row:
						_tell(state, {"kind": "linear", "shape": "sleeve", "x": -28.0, "y": 28.0 + row * 32.0, "vx": 4.0, "vy": 0.0, "collision": "rect", "halfWidth": 12.0, "halfHeight": 9.0})
		"flyer":
			if relative % 180 == 0:
				_tell(state, {"kind": "ring", "gap": _random(state) * TAU, "shape": "ring", "radius": 160.0, "x": 128.0, "y": 60.0})
			if relative % 120 == 30:
				var from_right: bool = (relative / 120) % 2 == 0
				_tell(state, {"kind": "linear", "shape": "paper", "aimed": true, "radius": 3.0, "x": 278.0 if from_right else -22.0, "y": float(state.cursor.y), "vx": -3.0 if from_right else 3.0, "vy": 0.0})
		"chip":
			if relative % 120 == 0:
				var previous: int = roundi((float(state.safeColumn) - 24.0) / 52.0)
				var shift: int = -1 if _random(state) < 0.5 else 1
				var target: int = clampi(previous + shift * (2 if phase > 0 else 1), 0, 4)
				state.safeColumn = 24.0 + target * 52.0
				state.markers[0] = {"id": relative / 120, "x": state.safeColumn, "y": 92.0, "collected": false, "active": true}
				for column: int in range(5):
					if column != target:
						_tell(state, {"kind": "linear", "shape": "confetti", "x": 24.0 + column * 52.0, "y": -14.0, "vx": 0.0, "vy": 4.2 + phase * 0.3, "axis": "vertical"})
		"deion":
			if relative % 120 == 0:
				var high: bool = (relative / 120) % 2 == 1
				_tell(state, {"kind": "linear", "shape": "overhead" if high else "hurdle", "x": 278.0, "y": 53.0 if high else 104.0, "vx": -4.8 - phase * 0.6, "vy": 0.0, "collision": "rect", "halfWidth": 8.0, "halfHeight": 49.0 if high else 16.0})
		"todd":
			if relative % 180 == 0:
				var angle: float = _random(state) * TAU
				_tell(state, {"kind": "sector", "shape": "stamp_sector", "x": 128.0, "y": 60.0, "angle": angle, "arc": 0.85, "innerRadius": 14.0, "radius": 58.0 - phase * 6.0})
				_tell(state, {"kind": "audit", "shape": "audit", "x": 128.0, "y": 60.0}, 90)
				_tell(state, {"kind": "linear", "shape": "stamp", "aimed": true, "radius": 3.0, "x": float(state.cursor.x), "y": -20.0, "vx": 0.0, "vy": 3.0})
		"pinpal":
			if relative % 90 == 0:
				var x: float = 64.0 + floorf(_random(state) * 3.0) * 64.0
				_tell(state, {"kind": "linear", "shape": "ball", "x": x, "y": -14.0, "vx": (1.0 + phase * 0.3) * (-1.0 if _random(state) < 0.5 else 1.0), "vy": 2.0 + phase * 0.2})

static func _new_hazard(state: Dictionary, tell: Dictionary) -> Dictionary:
	return {"id": int(tell.id), "x": float(tell.x), "y": float(tell.y), "previousX": float(tell.x), "previousY": float(tell.y), "radius": float(tell.get("radius", 5.0)) if str(tell.kind) == "linear" else 5.0, "aimed": bool(tell.get("aimed", false)), "vx": float(tell.get("vx", 0.0)), "vy": float(tell.get("vy", 0.0)), "grazed": false, "born": int(state.clock), "shape": str(tell.shape), "collision": str(tell.get("collision", "circle")), "halfWidth": float(tell.get("halfWidth", 0.0)), "halfHeight": float(tell.get("halfHeight", 0.0)), "friendly": false, "collided": false, "cleared": false}

static func _spawn(state: Dictionary, tell: Dictionary) -> void:
	if tell.kind == "audit":
		return
	if tell.kind == "ring":
		for index: int in range(18):
			var angle: float = float(index) * TAU / 18.0
			if absf(wrapf(angle - float(tell.gap), -PI, PI)) < 0.8:
				continue
			var ring: Dictionary = _new_hazard(state, tell)
			ring.id = int(tell.id) * 100 + index
			ring.shape = "paper"
			ring.orbitAngle = angle
			ring.orbitRadius = 160.0
			ring.x = 128.0 + cos(angle) * 160.0
			ring.y = 60.0 + sin(angle) * 160.0
			ring.previousX = ring.x
			ring.previousY = ring.y
			state.hazards.append(ring)
	elif tell.kind == "sector":
		var sector: Dictionary = _new_hazard(state, tell)
		sector.collision = "sector"
		sector.angle = float(tell.angle)
		sector.arc = float(tell.arc)
		sector.innerRadius = float(tell.innerRadius)
		sector.radius = float(state.arenaRadius) - 1.0
		sector.grace = 45 if _sector_hit(state.cursor, sector) else 0
		state.hazards.append(sector)
	else:
		state.hazards.append(_new_hazard(state, tell))

static func _sector_hit(cursor: Dictionary, hazard: Dictionary) -> bool:
	var delta: Vector2 = Vector2(float(cursor.x) - float(hazard.x), float(cursor.y) - float(hazard.y))
	var radius: float = delta.length()
	return radius >= float(hazard.innerRadius) - 3.0 and radius <= float(hazard.radius) + 3.0 and absf(wrapf(delta.angle() - float(hazard.angle), -PI, PI)) <= float(hazard.arc)

static func _distance(point: Vector2, start: Vector2, finish: Vector2) -> float:
	var line: Vector2 = finish - start
	var progress: float = clampf((point - start).dot(line) / maxf(0.00001, line.length_squared()), 0.0, 1.0)
	return point.distance_to(start + line * progress)

static func _hit(state: Dictionary) -> void:
	if int(state.invulnerability) == 0:
		state.hit = true
		state.invulnerability = 45

static func _move(state: Dictionary, direction: Vector2, precision: bool, assist: float) -> void:
	var speed: float = (64.0 if precision else 112.0) / 60.0 * assist
	var id: String = str(state.encounterId)
	if id == "deion":
		state.cursor.x = 64.0
		return
	if id == "chip":
		var sign_x: int = int(signf(direction.x)) if absf(direction.x) > 0.25 else 0
		if sign_x != 0 and sign_x != int(state.lastInputX):
			state.column = clampi(int(state.column) + sign_x, 0, 4)
		state.lastInputX = sign_x
		state.cursor.x = 24.0 + int(state.column) * 52.0
		state.cursor.y = 92.0
		return
	var move: Vector2 = direction / maxf(1.0, direction.length()) * speed
	state.cursor.x = _q(clampf(float(state.cursor.x) + move.x, 3.0, 253.0))
	if id == "pinpal":
		state.cursor.y = 104.0
	else:
		state.cursor.y = _q(clampf(float(state.cursor.y) + move.y, 3.0, 117.0))
	if id == "todd":
		var delta: Vector2 = Vector2(float(state.cursor.x) - 128.0, float(state.cursor.y) - 60.0)
		if delta.length() > float(state.arenaRadius) - 3.0:
			delta = delta.normalized() * (float(state.arenaRadius) - 3.0)
			state.cursor = {"x": _q(128.0 + delta.x), "y": _q(60.0 + delta.y)}

static func _global_tick(state: Dictionary, precision: bool) -> void:
	state.invulnerability = maxi(0, int(state.invulnerability) - 1)
	state.flipperTicks = maxi(0, int(state.flipperTicks) - 1)
	state.paperFlashCooldown = maxi(0, int(state.paperFlashCooldown) - 1)
	if state.encounterId == "deion":
		state.ducking = precision and state.grounded
		if not state.grounded:
			state.cursor.y = _q(float(state.cursor.y) + float(state.jumpVelocity))
			state.jumpVelocity = _q(float(state.jumpVelocity) + 0.28)
			if float(state.cursor.y) >= 96.0:
				state.grounded = true
				state.jumpVelocity = 0.0
				state.cursor.y = 110.0 if precision else 96.0
		else:
			state.cursor.y = 110.0 if precision else 96.0

static func step(before: Dictionary, input: Vector2, precision: bool = false, assist: float = 1.0, slow: bool = false, promise: bool = false, defend_pressed: bool = false) -> Dictionary:
	var state: Dictionary = before.duplicate(true)
	state.hit = false
	state.grazeDelta = 0
	state.beatPulse = false
	state.flipperSuccess = false
	if state.done:
		return state
	var scale: float = clampf(assist if is_finite(assist) else 1.0, 0.1, 1.0)
	var direction: Vector2 = Vector2(clampf(input.x if is_finite(input.x) else 0.0, -1.0, 1.0), clampf(input.y if is_finite(input.y) else 0.0, -1.0, 1.0))
	if defend_pressed:
		if state.encounterId == "deion" and state.grounded and not precision:
			state.grounded = false
			state.cursor.y = 96.0
			state.jumpVelocity = -5.3
		elif state.encounterId == "pinpal" and int(state.flipperTicks) == 0:
			state.flipperTicks = 12
		elif state.encounterId == "flyer" and int(state.paperFlashCooldown) == 0:
			state.gapBoostUntil = int(state.clock) + 15
			state.paperFlashCooldown = 30
	_move(state, direction, precision, scale)
	state.tick = int(state.tick) + 1
	state.globalAccumulator = _q(float(state.globalAccumulator) + scale, 10000.0)
	while float(state.globalAccumulator) >= 1.0:
		state.globalAccumulator = _q(float(state.globalAccumulator) - 1.0, 10000.0)
		_global_tick(state, precision)
	state.accumulator = _q(float(state.accumulator) + scale * (0.8 if slow else 1.0), 10000.0)
	while float(state.accumulator) >= 1.0 and not state.done:
		state.accumulator = _q(float(state.accumulator) - 1.0, 10000.0)
		var relative: int = int(state.clock) - int(state.leadIn)
		var absolute: int = int(state.clock) + int(state.musicBase)
		state.beat = absolute / 30
		state.beatPulse = state.beatPulse or absolute % 30 == 0
		if state.encounterId == "todd":
			state.audit = relative >= 0 and relative % 180 >= 90 and relative % 180 < 150
			state.arenaRadius = 58.0 - int(state.phase) * 6.0 - float(posmod(maxi(0, relative), 180)) / 180.0 * 10.0
			state.mechanicInfo = "AUDIT: HOLD STILL" if state.audit else "Walk to a box, then confirm."
			if state.audit: state.hazards.clear()
			if state.audit and direction.length_squared() > 0.01:
				_hit(state)
		if relative >= 0 and int(state.clock) + 60 < int(state.duration):
			_schedule(state, relative)
		var pending: Array = []
		for tell: Dictionary in state.telegraphs:
			tell.ticksRemaining = int(tell.ticksRemaining) - 1
			if int(tell.ticksRemaining) < 0:
				_spawn(state, tell)
			else:
				pending.append(tell)
		state.telegraphs = pending
		var live: Array = []
		var cursor: Vector2 = Vector2(float(state.cursor.x), float(state.cursor.y))
		for hazard: Dictionary in state.hazards:
			hazard.previousX = hazard.x
			hazard.previousY = hazard.y
			if hazard.has("orbitRadius"):
				hazard.orbitRadius = float(hazard.orbitRadius) - 1.5 - int(state.phase) * 0.15
				hazard.orbitAngle = float(hazard.orbitAngle) + 0.01 + int(state.phase) * 0.003
				hazard.x = _q(128.0 + cos(float(hazard.orbitAngle)) * float(hazard.orbitRadius))
				hazard.y = _q(60.0 + sin(float(hazard.orbitAngle)) * float(hazard.orbitRadius))
				if float(hazard.orbitRadius) < 18.0:
					continue
			elif hazard.collision == "sector":
				if state.audit:
					continue
				hazard.angle = float(hazard.angle) + 0.009 + int(state.phase) * 0.003
				hazard.radius = float(state.arenaRadius) - 1.0
			else:
				hazard.x = _q(float(hazard.x) + float(hazard.vx))
				hazard.y = _q(float(hazard.y) + float(hazard.vy))
				if state.encounterId == "pinpal":
					if float(hazard.x) < 8.0 or float(hazard.x) > 248.0:
						hazard.vx = -float(hazard.vx)
						hazard.x = clampf(float(hazard.x), 8.0, 248.0)
					if not hazard.friendly and int(state.flipperTicks) > 0 and absf(float(hazard.x) - float(state.cursor.x)) <= 24.0 and float(hazard.y) >= 86.0 and float(hazard.y) <= 112.0:
						hazard.friendly = true
						hazard.vy = -3.0
						hazard.vx = (float(hazard.x) - float(state.cursor.x)) * 0.08
						state.deflections = int(state.deflections) + 1
						state.flipperSuccess = true
						state.flipperTicks = 0
				if state.encounterId == "claim" and hazard.shape == "claim_sweep" and float(hazard.x) < -16.0 and not hazard.cleared:
					hazard.cleared = true
					if state.carryTag: state.claimSweepPassed = int(state.claimSweepPassed) + 1
				if float(hazard.x) < -30.0 or float(hazard.x) > 290.0 or float(hazard.y) > 140.0 or (hazard.friendly and float(hazard.y) < -20.0):
					continue
			if live.size() >= 200:
				continue
			live.append(hazard)
			if hazard.friendly:
				continue
			var collision: bool = false
			var distance: float = _distance(cursor, Vector2(float(hazard.previousX), float(hazard.previousY)), Vector2(float(hazard.x), float(hazard.y)))
			if hazard.collision == "sector":
				collision = int(state.clock) - int(hazard.born) >= int(hazard.grace) and _sector_hit(state.cursor, hazard)
			elif hazard.collision == "rect":
				var closest_x: float = clampf(float(state.cursor.x), minf(float(hazard.previousX), float(hazard.x)), maxf(float(hazard.previousX), float(hazard.x)))
				var hurt: float = 2.0 if state.ducking else 3.0
				collision = absf(float(state.cursor.x) - closest_x) <= float(hazard.halfWidth) + hurt and absf(float(state.cursor.y) - float(hazard.y)) <= float(hazard.halfHeight) + hurt
			else:
				collision = distance <= float(hazard.radius) + 3.0
			if collision:
				hazard.collided = true
				hazard.grazed = true
				if not (state.encounterId == "flyer" and int(state.clock) <= int(state.gapBoostUntil)):
					_hit(state)
			elif hazard.collision == "circle" and distance <= float(hazard.radius) + 11.0 and not hazard.grazed:
				hazard.grazed = true
				if int(state.grazes) < 12:
					state.grazes = int(state.grazes) + 1
					state.grazeDelta = int(state.grazeDelta) + 1
			if state.encounterId == "deion" and float(hazard.x) < 50.0 and not hazard.cleared:
				hazard.cleared = true
				if not hazard.collided:
					state.runnerCleared = int(state.runnerCleared) + 1
		state.hazards = live
		state.clock = int(state.clock) + 1
		if int(state.clock) >= int(state.duration):
			state.done = true
			state.hazards = []
			state.telegraphs = []
	var cursor: Vector2 = Vector2(float(state.cursor.x), float(state.cursor.y))
	if state.encounterId == "claim" and state.carryTag:
		for marker: Dictionary in state.markers:
			if int(marker.id) > 0: marker.active = int(state.delivery) < 0
	if promise or state.encounterId == "todd":
		for marker: Dictionary in state.markers:
			if not marker.collected and marker.get("active", true) and cursor.distance_to(Vector2(float(marker.x), float(marker.y))) <= 12.0:
				if state.encounterId == "claim" and int(state.phase) > 0 and int(marker.id) > 0 and not state.boundary:
					continue
				var confirm_required: bool = state.encounterId == "todd" or (state.encounterId == "claim" and int(state.phase) > 0 and int(marker.id) > 0)
				if not confirm_required or defend_pressed:
					marker.collected = true
					if state.encounterId == "chip": state.columnsReached = int(state.columnsReached) + 1
					if state.encounterId == "todd": state.consentCount = int(state.consentCount) + 1
					if state.encounterId == "claim":
						if int(marker.id) == 0:
							state.carryTag = true
						elif int(state.phase) > 0 and state.boundary:
							state.delivery = int(marker.id)
							state.noteLeft = true
							for other: Dictionary in state.markers:
								if int(other.id) > 0 and int(other.id) != int(marker.id): other.noted = true
	state.promiseComplete = true
	for marker: Dictionary in state.markers:
		if not marker.collected: state.promiseComplete = false
	if state.encounterId == "chip": state.promiseComplete = int(state.columnsReached) >= 3
	if state.encounterId == "deion": state.promiseComplete = state.markers[0].collected and int(state.runnerCleared) >= 2
	if state.encounterId == "pinpal":
		state.promiseComplete = int(state.deflections) >= 3
		state.markers[0].collected = state.promiseComplete
	if state.encounterId == "claim":
		state.promiseComplete = state.markers[0].collected and state.markers[1].collected and int(state.claimSweepPassed) > 0 if int(state.phase) == 0 else int(state.delivery) > 0 and state.noteLeft
	return state
