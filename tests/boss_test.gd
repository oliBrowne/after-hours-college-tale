extends SceneTree
const Director = preload("res://core/boss_director.gd")
var checks: int = 0
var failures: int = 0

func _init() -> void:
	_test_progression()
	_test_replays()
	_test_defend()
	_test_promises()
	print("Godot boss director: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _test_progression() -> void:
	_check(Director.phase_for(100, 100) == 0, "Full-health opening phase")
	_check(Director.phase_for(71, 100) == 0 and Director.phase_for(70, 100) == 1, "70-percent transition threshold exact")
	_check(Director.phase_for(36, 100) == 1 and Director.phase_for(35, 100) == 2, "35-percent transition threshold exact")
	_check(Director.phase_for(100, 100, 2) == 2, "Peaceful progress independently advances needs")
	_check(Director.next_phase(0, 1, 100) == 1 and Director.next_phase(1, 1, 100) == 2, "At most one phase transition per committed turn")
	_check(Director.next_phase(2, 100, 100) == 2, "Phase never regresses after recovery")
	_check(Director.profile("chip").maxHp != Director.profile("deion").maxHp and Director.profile("todd").maxHp != Director.profile("chip").maxHp, "Distinct profile balance defaults")
	_check(Director.profile("unknown").id == "chip", "Unknown profile has deterministic safe fallback")
	_check(Director.create("chip", 1, 99, -20).phase == 2 and Director.create("chip", 1, 0, -20).leadIn == 0, "Invalid phase and negative playback origin safely clamped")

func _replay(profile: String, phase: int, assist: float = 1.0, slow: bool = false, paused: bool = false, follow_safe: bool = false, promise: bool = false) -> Dictionary:
	var state: Dictionary = Director.create(profile, 12345, phase)
	var hit_count: int = 0
	var pulses: int = 0
	var bound_ok: bool = true
	var warning_ok: bool = true
	var safe_ok: bool = true
	var external_ok: bool = true
	var last_beat_clock: int = -30
	while not state.done:
		var tick: int = int(state.tick)
		if paused and tick % 55 == 0:
			var frozen: Dictionary = state.duplicate(true)
			# Rendering, pausing and elapsed real time never enter simulation state.
			for _frame: int in range(30):
				var _visible_beat: int = int(state.beat)
			_check(state == frozen, "Pause holds all clocks and hazard positions: " + profile)
		var input: Vector2 = Vector2(1.0 if tick % 100 < 50 else -1.0, 1.0 if tick % 140 < 70 else -1.0)
		if follow_safe:
			input = Vector2(signf(128.0 - float(state.cursor.x)), signf(float(state.safeLane) - float(state.cursor.y)))
			if profile == "todd":
				input = Vector2(signf(float(state.safeColumn) - float(state.cursor.x)), signf(60.0 - float(state.cursor.y)))
		state = Director.step(state, input, false, assist, slow, promise)
		if state.hit:
			hit_count += 1
		if state.beatPulse:
			if int(state.clock) - 1 - last_beat_clock != 30:
				warning_ok = false
			last_beat_clock = int(state.clock) - 1
			pulses += 1
		if int(state.clock) < 61 and not state.hazards.is_empty():
			warning_ok = false
		if state.hazards.size() > 200:
			bound_ok = false
		if state.safeWindow and not state.hazards.is_empty():
			safe_ok = false
		for hazard: Dictionary in state.hazards:
			if int(hazard.born) == int(state.clock) - 1:
				if float(hazard.x) >= 0.0 and float(hazard.x) <= 256.0 and float(hazard.y) >= 0.0 and float(hazard.y) <= 120.0:
					external_ok = false
		if int(state.tick) > 2000:
			_check(false, "Boss phase always terminates")
			break
	state.testHits = hit_count
	state.testPulses = pulses
	state.testBounded = bound_ok
	state.testWarnings = warning_ok
	state.testSafeWindows = safe_ok
	state.testExternal = external_ok
	return state

func _test_replays() -> void:
	for profile: String in ["chip", "deion", "todd"]:
		for phase: int in range(3):
			var state: Dictionary = _replay(profile, phase)
			var label: String = profile + "/phase" + str(phase)
			_check(state == _replay(profile, phase), "Exact deterministic replay: " + label)
			_check(state.tick == (16 + phase * 2) * 30, "Authored phase duration: " + label)
			_check(state.testPulses == 16 + phase * 2 and state.testWarnings, "120-BPM pulse spacing and two-beat tells: " + label)
			_check(state.testBounded and state.testExternal, "Bounded hazards spawn beyond arena: " + label)
			_check(state.testSafeWindows and state.hazards.is_empty() and state.telegraphs.is_empty(), "Rest windows and terminal cleanup: " + label)
			_check(_replay(profile, phase, 1.0, false, false, true).testHits == 0, "Authored announced corridor is survivable without timing: " + label)
		var normal: Dictionary = _replay(profile, 0)
		_check(normal == _replay(profile, 0, 1.0, false, true), "Inserted pause/render frames do not change phase results: " + profile)
		var half: Dictionary = _replay(profile, 0, 1.0, true)
		_check(half.tick == 600 and half.testPulses == 16, "Half Time expands phase and beat windows together: " + profile)
		var combined: Dictionary = _replay(profile, 0, 0.7, true)
		_check(combined.tick == 858 and combined.testPulses == 16 and combined == _replay(profile, 0, 0.7, true), "Combined assists preserve beat count and deterministic replay: " + profile)
	var offset: Dictionary = Director.create("chip", 8, 0, 12)
	var first_pulse: int = -1
	while not offset.done:
		offset = Director.step(offset, Vector2.ZERO)
		if offset.beatPulse and first_pulse < 0:
			first_pulse = int(offset.clock) - 1
	_check(first_pulse == 18 and offset.duration == 498, "Existing music offset aligns first pulse and attack lead-in")
	var original: Dictionary = Director.create("chip", 9)
	Director.step(original, Vector2.RIGHT)
	_check(original.cursor.x == 128.0 and original.tick == 0, "Boss step preserves prior replay state")

func _hazard() -> Dictionary:
	return {"id": 500, "x": 128.0, "y": 60.0, "previousX": 128.0, "previousY": 60.0, "radius": 5.0, "vx": 0.0, "vy": 0.0, "grazed": false, "born": 60, "shape": "disc"}

func _test_defend() -> void:
	var state: Dictionary = Director.create("deion", 1)
	state.clock = 60
	state.hazards = [_hazard()]
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, false, true)
	_check(state.defendSuccess and state.defendBlock and not state.hit and state.defendBlocks == 1, "On-beat fresh defend cancels a hit")
	_check(state.invulnerability == 45 and not state.defendCharge, "Defend consumes one charge and grants normal protection")
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, false, true)
	_check(not state.defendSuccess and state.defendMiss, "Repeated presses cannot farm the same beat")
	state = Director.create("deion", 1)
	state.clock = 74
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, false, true)
	_check(state.defendMiss and not state.defendCharge and not state.hit, "Off-beat defend has no penalty")
	state = Director.create("chip", 1)
	state.clock = 60
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, false, true)
	for _tick: int in range(14):
		state = Director.step(state, Vector2.ZERO)
	_check(not state.defendCharge, "Unused timed-defend charge expires")
	state = Director.create("deion", 1)
	state.clock = 60
	state.hazards = [_hazard()]
	state = Director.step(state, Vector2.ZERO)
	_check(state.hit and not state.defendBlock, "Ordinary dodging and damage remain active without timed defend")

func _test_promises() -> void:
	var state: Dictionary = Director.create("chip", 19)
	for _tick: int in range(100):
		state = Director.step(state, Vector2(signf(218.0 - float(state.cursor.x)), signf(92.0 - float(state.cursor.y))), false, 1.0, false, true)
	_check(state.promiseComplete, "Chip invitation remains reachable")
	state = _replay("deion", 0, 1.0, false, false, true, true)
	_check(state.promiseComplete, "Deion response-only relay marker is reachable via announced corridor")
	state = Director.create("todd", 19)
	while not state.done:
		var target: Dictionary = state.markers[0] if not state.markers[0].collected else state.markers[1]
		state = Director.step(state, Vector2(signf(float(target.x) - float(state.cursor.x)), signf(float(target.y) - float(state.cursor.y))), false, 1.0, false, true)
	_check(state.promiseComplete, "Todd's two distinct bell answers are reachable")
