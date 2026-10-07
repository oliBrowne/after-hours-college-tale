class_name BossDirector
extends RefCounted
## Optional authored boss challenges; Flyerer and DodgePattern remain unchanged.
## 120 BPM = 30 simulation ticks/beat. Audio never controls damage or progression.
## Step once per physics tick; pausing means no calls. beatPulse is a visual/audio cue.
## Music playback must follow assist * (0.8 for Half Time), matching pattern clocks.
## Timed defend is optional: a fresh confirm press within five ticks of a beat
## grants one short shield; missing the beat never costs HP, SYNC, or story progress.

const BasePattern = preload("res://core/pattern.gd")
const TICKS_PER_BEAT: int = 30
const BPM: int = 120
const MAX_HAZARDS: int = 200
const MASK: int = 0xffffffff

static func profile(id: String) -> Dictionary:
	match id:
		"deion":
			return {"id": id, "bpm": BPM, "maxHp": 260, "defence": 1, "phases": ["Lane Relay", "Cross-Court", "Overtime"], "tell": "The outlined relay lane stays open. Cross into it during CALL.", "promise": "Touch the relay flag during RESPONSE."}
		"todd":
			return {"id": id, "bpm": BPM, "maxHp": 340, "defence": 1, "phases": ["Call and Answer", "Counterpoint", "Last Cadence"], "tell": "Notes descend, then rise. The outlined column is always clear.", "promise": "Answer both outlined bell lights."}
		_:
			return {"id": "chip", "bpm": BPM, "maxHp": 180, "defence": 1, "phases": ["Paper Crown", "Folded Chorus", "Final Flourish"], "tell": "Folded planes alternate sides. Read each announced row.", "promise": "Read the one outlined invitation."}

static func phase_for(hp: int, max_hp: int, progress: int = 0) -> int:
	var health_phase: int = 0
	if max_hp > 0:
		if hp * 100 <= max_hp * 35:
			health_phase = 2
		elif hp * 100 <= max_hp * 70:
			health_phase = 1
	return clampi(maxi(health_phase, progress), 0, 2)

static func next_phase(previous: int, hp: int, max_hp: int, progress: int = 0) -> int:
	# Call only between turns: no surprise transformation inside a dodge phase.
	return maxi(clampi(previous, 0, 2), mini(clampi(previous, 0, 2) + 1, phase_for(hp, max_hp, progress)))

static func create(profile_id: String, seed: int, phase: int = 0, music_tick: int = 0) -> Dictionary:
	var state: Dictionary = BasePattern.create(seed)
	var definition: Dictionary = profile(profile_id)
	var stage: int = clampi(phase, 0, 2)
	var origin_tick: int = maxi(0, music_tick)
	var offset: int = posmod(origin_tick, TICKS_PER_BEAT)
	state.profileId = definition.id
	state.phase = stage
	state.phaseName = definition.phases[stage]
	state.musicBase = origin_tick
	state.leadIn = posmod(TICKS_PER_BEAT - offset, TICKS_PER_BEAT)
	state.duration = int(state.leadIn) + (16 + stage * 2) * TICKS_PER_BEAT
	state.beat = floori(float(origin_tick) / TICKS_PER_BEAT)
	state.beatPulse = false
	state.beatFraction = float(offset) / TICKS_PER_BEAT
	state.phaseBeat = -1
	state.callResponse = "READY"
	state.safeWindow = true
	state.safeLane = 60.0
	state.safeColumn = 128.0
	state.defendSuccess = false
	state.defendMiss = false
	state.defendBlock = false
	state.defendCharge = false
	state.defendUntil = -1
	state.lastDefendBeat = -1
	state.defendBlocks = 0
	if state.profileId == "deion":
		state.markers = [{"id": 0, "x": 128.0, "y": 60.0, "collected": false, "active": false}]
	elif state.profileId == "todd":
		state.markers = [{"id": 0, "x": 80.0, "y": 78.0, "collected": false, "active": true}, {"id": 1, "x": 176.0, "y": 42.0, "collected": false, "active": true}]
	else:
		state.markers[0].active = true
	return state

static func _pixel(value: float) -> float:
	return roundf(value * 1024.0) / 1024.0

static func _clock(value: float) -> float:
	return roundf(value * 10000.0) / 10000.0

static func _random(state: Dictionary) -> float:
	var value: int = int(state.rng) & MASK
	value = (value ^ (value << 13)) & MASK
	value = (value ^ (value >> 17)) & MASK
	value = (value ^ (value << 5)) & MASK
	state.rng = value
	return float(value) / 4294967296.0

static func _tell(state: Dictionary, x: float, y: float, vx: float, vy: float, shape: String, direction: String) -> void:
	state.telegraphs.append({"id": int(state.nextId), "x": x, "y": y, "vx": vx, "vy": vy, "shape": shape, "direction": direction, "ticksRemaining": 60, "axis": "vertical" if vy != 0.0 else "horizontal"})
	state.nextId = int(state.nextId) + 1

static func _call(state: Dictionary, cycle: int) -> void:
	var phase: int = int(state.phase)
	if state.profileId == "chip":
		var lane: int = floori(_random(state) * 4.0)
		var direction: int = 1 if (cycle + phase) % 2 == 0 else -1
		var safe_lane: int = lane if phase == 2 else (lane + 1) % 4
		state.safeLane = 18.0 + safe_lane * 28.0
		for row: int in range(4):
			var selected: bool = row == lane if phase == 0 else (row == lane or row == (lane + 2) % 4) if phase == 1 else row != lane
			if selected:
				_tell(state, -14.0 if direction > 0 else 270.0, 18.0 + row * 28.0, direction * (3.2 + phase * 0.4), 0.0, "paper", "right" if direction > 0 else "left")
	elif state.profileId == "deion":
		var lane: int = floori(_random(state) * 3.0)
		state.safeLane = 32.0 + lane * 28.0
		var direction: int = 1 if cycle % 2 == 0 else -1
		var gap: float = 48.0 - phase * 4.0
		for row: int in range(10):
			var y: float = 6.0 + row * 12.0
			if absf(y - float(state.safeLane)) > gap / 2.0:
				_tell(state, -14.0 if direction > 0 else 270.0, y, direction * (6.0 + phase * 0.2), 0.0, "disc", "right" if direction > 0 else "left")
		state.markers[0].y = state.safeLane
	else:
		state.safeColumn = 96.0 if cycle % 2 == 0 else 160.0
		var direction: int = 1 if (cycle + phase) % 2 == 0 else -1
		var gap: float = 64.0 - phase * 8.0
		for column: int in range(8):
			var x: float = 20.0 + column * 32.0
			if absf(x - float(state.safeColumn)) > gap / 2.0:
				var bend: float = 0.0 if phase == 0 else (0.2 if column % 2 == 0 else -0.2)
				_tell(state, x, -14.0 if direction > 0 else 134.0, bend, direction * (3.4 + phase * 0.3), "note", "down" if direction > 0 else "up")

static func _segment_distance(point: Vector2, start: Vector2, finish: Vector2) -> float:
	var delta: Vector2 = finish - start
	var divisor: float = maxf(delta.length_squared(), 0.00001)
	var progress: float = clampf((point - start).dot(delta) / divisor, 0.0, 1.0)
	return point.distance_to(start + delta * progress)

static func step(before: Dictionary, input: Vector2, precision: bool = false, assist: float = 1.0, slow: bool = false, promise: bool = false, defend_pressed: bool = false) -> Dictionary:
	var state: Dictionary = before.duplicate(true)
	state.hit = false
	state.grazeDelta = 0
	state.beatPulse = false
	state.defendSuccess = false
	state.defendMiss = false
	state.defendBlock = false
	if state.done:
		return state
	var speed_scale: float = clampf(assist if is_finite(assist) else 1.0, 0.1, 1.0)
	var direction: Vector2 = Vector2(clampf(input.x if is_finite(input.x) else 0.0, -1.0, 1.0), clampf(input.y if is_finite(input.y) else 0.0, -1.0, 1.0))
	var speed: float = (64.0 if precision else 112.0) / 60.0 * speed_scale
	direction /= maxf(1.0, direction.length())
	state.cursor.x = _pixel(clampf(float(state.cursor.x) + direction.x * speed, 3.0, 253.0))
	state.cursor.y = _pixel(clampf(float(state.cursor.y) + direction.y * speed, 3.0, 117.0))
	state.tick = int(state.tick) + 1
	if defend_pressed:
		var absolute_tick: int = int(state.musicBase) + int(state.clock)
		var nearest_beat: int = floori((absolute_tick + 15.0) / TICKS_PER_BEAT)
		var distance: int = absi(absolute_tick - nearest_beat * TICKS_PER_BEAT)
		if distance <= 5 and nearest_beat != int(state.lastDefendBeat):
			state.defendSuccess = true
			state.defendCharge = true
			state.defendUntil = int(state.clock) + 12
			state.lastDefendBeat = nearest_beat
		else:
			state.defendMiss = true
	state.globalAccumulator = _clock(float(state.globalAccumulator) + speed_scale)
	while float(state.globalAccumulator) >= 1.0:
		state.globalAccumulator = _clock(float(state.globalAccumulator) - 1.0)
		state.invulnerability = maxi(0, int(state.invulnerability) - 1)
	state.accumulator = _clock(float(state.accumulator) + speed_scale * (0.8 if slow else 1.0))
	while float(state.accumulator) >= 1.0 and not state.done:
		state.accumulator = _clock(float(state.accumulator) - 1.0)
		var absolute_tick: int = int(state.musicBase) + int(state.clock)
		state.beat = floori(float(absolute_tick) / TICKS_PER_BEAT)
		state.beatFraction = float(posmod(absolute_tick, TICKS_PER_BEAT)) / TICKS_PER_BEAT
		if posmod(absolute_tick, TICKS_PER_BEAT) == 0:
			state.beatPulse = true
		var relative: int = int(state.clock) - int(state.leadIn)
		var cycle_tick: int = posmod(relative, 120)
		state.phaseBeat = floori(float(relative) / TICKS_PER_BEAT)
		state.safeWindow = relative < 0 or cycle_tick >= 105
		state.callResponse = "READY" if relative < 0 else "CALL" if cycle_tick < 60 else "REST" if state.safeWindow else "RESPONSE"
		if int(state.clock) > int(state.defendUntil):
			state.defendCharge = false
		if relative >= 0 and cycle_tick == 0 and int(state.clock) + 60 < int(state.duration):
			_call(state, floori(float(relative) / 120.0))
		for hazard: Dictionary in state.hazards:
			hazard.previousX = hazard.x
			hazard.previousY = hazard.y
			hazard.x = _pixel(float(hazard.x) + float(hazard.vx))
			hazard.y = _pixel(float(hazard.y) + float(hazard.vy))
		var pending: Array = []
		for tell: Dictionary in state.telegraphs:
			tell.ticksRemaining = int(tell.ticksRemaining) - 1
			if int(tell.ticksRemaining) < 0:
				state.hazards.append({"id": int(tell.id), "x": float(tell.x), "y": float(tell.y), "previousX": float(tell.x), "previousY": float(tell.y), "radius": 5.0, "vx": float(tell.vx), "vy": float(tell.vy), "grazed": false, "born": int(state.clock), "shape": str(tell.shape)})
			else:
				pending.append(tell)
		state.telegraphs = pending
		var live: Array = []
		if not state.safeWindow:
			for hazard: Dictionary in state.hazards:
				if float(hazard.x) > -24.0 and float(hazard.x) < 280.0 and float(hazard.y) > -24.0 and float(hazard.y) < 144.0 and int(state.clock) - int(hazard.born) < 120 and live.size() < MAX_HAZARDS:
					live.append(hazard)
		state.hazards = live
		var cursor: Vector2 = Vector2(float(state.cursor.x), float(state.cursor.y))
		for hazard: Dictionary in state.hazards:
			var distance: float = _segment_distance(cursor, Vector2(float(hazard.previousX), float(hazard.previousY)), Vector2(float(hazard.x), float(hazard.y)))
			if distance <= float(hazard.radius) + 3.0:
				hazard.grazed = true
				if int(state.invulnerability) == 0:
					if state.defendCharge:
						state.defendBlock = true
						state.defendBlocks = int(state.defendBlocks) + 1
						state.defendCharge = false
					else:
						state.hit = true
					state.invulnerability = 45
			elif distance <= float(hazard.radius) + 11.0 and not hazard.grazed:
				hazard.grazed = true
				if int(state.grazes) < 12:
					state.grazes = int(state.grazes) + 1
					state.grazeDelta = int(state.grazeDelta) + 1
		state.clock = int(state.clock) + 1
		if int(state.clock) >= int(state.duration):
			state.done = true
			state.hazards = []
			state.telegraphs = []
			state.defendCharge = false
	if state.profileId == "deion":
		state.markers[0].active = state.callResponse in ["RESPONSE", "REST"]
	if promise:
		var cursor: Vector2 = Vector2(float(state.cursor.x), float(state.cursor.y))
		for marker: Dictionary in state.markers:
			if marker.get("active", true) and cursor.distance_to(Vector2(float(marker.x), float(marker.y))) <= 12.0:
				marker.collected = true
	state.promiseComplete = true
	for marker: Dictionary in state.markers:
		if not marker.collected:
			state.promiseComplete = false
	return state
