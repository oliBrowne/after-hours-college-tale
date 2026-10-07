class_name DodgePattern
extends RefCounted
## One step is one fixed 60 Hz simulation tick. Pause by not calling step().
## The amber cursor and all coordinates are local to the 256 x 120 arena.
## Assist slows the global clock; Half Time additionally slows the pattern clock.

const ARENA: Vector2 = Vector2(256.0, 120.0)
const DURATION: int = 420
const MASK: int = 0xffffffff

static func create(seed: int) -> Dictionary:
	var rng: int = seed & MASK
	if rng == 0:
		rng = 0x6d2b79f5
	return {"seed": seed, "rng": rng, "tick": 0, "clock": 0, "accumulator": 0.0, "globalAccumulator": 0.0, "cursor": {"x": 128.0, "y": 60.0}, "hazards": [], "telegraphs": [], "markers": [{"id": 0, "x": 218.0, "y": 92.0, "collected": false}], "invulnerability": 0, "hit": false, "grazes": 0, "grazeDelta": 0, "done": false, "promiseComplete": false, "nextId": 1}

static func _random(state: Dictionary) -> float:
	var value: int = int(state.rng) & MASK
	value = (value ^ (value << 13)) & MASK
	value = (value ^ (value >> 17)) & MASK
	value = (value ^ (value << 5)) & MASK
	state.rng = value
	return float(value) / 4294967296.0

static func _pixel(value: float) -> float:
	return roundf(value * 1024.0) / 1024.0

static func _clock(value: float) -> float:
	return roundf(value * 10000.0) / 10000.0

static func _segment_distance(point: Vector2, start: Vector2, finish: Vector2) -> float:
	var difference: Vector2 = finish - start
	var divisor: float = difference.length_squared()
	if divisor == 0.0:
		divisor = 1.0
	var progress: float = clampf((point - start).dot(difference) / divisor, 0.0, 1.0)
	return point.distance_to(start + difference * progress)

static func step(before: Dictionary, input: Vector2, precision: bool = false, assist: float = 1.0, slow: bool = false, promise: bool = false) -> Dictionary:
	var state: Dictionary = before.duplicate(true)
	state.hit = false
	state.grazeDelta = 0
	if state.done:
		return state
	var speed_scale: float = clampf(assist if is_finite(assist) else 1.0, 0.1, 1.0)
	var direction: Vector2 = Vector2(clampf(input.x if is_finite(input.x) else 0.0, -1.0, 1.0), clampf(input.y if is_finite(input.y) else 0.0, -1.0, 1.0))
	var length: float = maxf(1.0, direction.length())
	var speed: float = (64.0 if precision else 112.0) / 60.0 * speed_scale
	state.cursor.x = _pixel(clampf(float(state.cursor.x) + direction.x / length * speed, 3.0, 253.0))
	state.cursor.y = _pixel(clampf(float(state.cursor.y) + direction.y / length * speed, 3.0, 117.0))
	state.tick = int(state.tick) + 1
	state.globalAccumulator = _clock(float(state.globalAccumulator) + speed_scale)
	while float(state.globalAccumulator) >= 1.0:
		state.globalAccumulator = _clock(float(state.globalAccumulator) - 1.0)
		state.invulnerability = maxi(0, int(state.invulnerability) - 1)
	state.accumulator = _clock(float(state.accumulator) + speed_scale * (0.8 if slow else 1.0))
	while float(state.accumulator) >= 1.0 and not state.done:
		state.accumulator = _clock(float(state.accumulator) - 1.0)
		if int(state.clock) % 48 == 0 and int(state.clock) < 336:
			var lane: int = floori(_random(state) * 4.0)
			state.telegraphs.append({"id": int(state.nextId), "y": 18.0 + lane * 28.0, "ticksRemaining": 45, "direction": "right"})
			state.nextId = int(state.nextId) + 1
		for hazard: Dictionary in state.hazards:
			hazard.previousX = hazard.x
			hazard.previousY = hazard.y
			hazard.x = _pixel(float(hazard.x) + float(hazard.vx))
			hazard.y = _pixel(float(hazard.y) + float(hazard.vy))
		var pending: Array = []
		for tell: Dictionary in state.telegraphs:
			tell.ticksRemaining = int(tell.ticksRemaining) - 1
			if int(tell.ticksRemaining) < 0:
				state.hazards.append({"id": int(tell.id), "x": -12.0, "y": float(tell.y), "previousX": -12.0, "previousY": float(tell.y), "radius": 5.0, "vx": 2.0, "vy": 0.0, "grazed": false, "born": int(state.clock)})
			else:
				pending.append(tell)
		state.telegraphs = pending
		var live: Array = []
		for hazard: Dictionary in state.hazards:
			if float(hazard.x) < 268.0 and int(state.clock) - int(hazard.born) < 180 and live.size() < 200:
				live.append(hazard)
		state.hazards = live
		var cursor: Vector2 = Vector2(float(state.cursor.x), float(state.cursor.y))
		for hazard: Dictionary in state.hazards:
			var distance: float = _segment_distance(cursor, Vector2(float(hazard.previousX), float(hazard.previousY)), Vector2(float(hazard.x), float(hazard.y)))
			if distance <= float(hazard.radius) + 3.0:
				hazard.grazed = true
				if int(state.invulnerability) == 0:
					state.hit = true
					state.invulnerability = 45
			elif distance <= float(hazard.radius) + 11.0 and not hazard.grazed:
				hazard.grazed = true
				if int(state.grazes) < 12:
					state.grazes = int(state.grazes) + 1
					state.grazeDelta = int(state.grazeDelta) + 1
		state.clock = int(state.clock) + 1
		if int(state.clock) >= DURATION:
			state.done = true
			state.hazards = []
			state.telegraphs = []
	if promise:
		var cursor: Vector2 = Vector2(float(state.cursor.x), float(state.cursor.y))
		for marker: Dictionary in state.markers:
			if cursor.distance_to(Vector2(float(marker.x), float(marker.y))) <= 12.0:
				marker.collected = true
	state.promiseComplete = true
	for marker: Dictionary in state.markers:
		if not marker.collected:
			state.promiseComplete = false
	return state
