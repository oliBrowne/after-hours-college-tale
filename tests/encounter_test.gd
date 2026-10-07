extends SceneTree
const Director = preload("res://core/encounter_director.gd")
var checks: int = 0
var failures: int = 0

func _init() -> void:
	_test_motion()
	_test_replays()
	_test_audit()
	_test_claim()
	_test_idle_pressure()
	print("Godot encounter director: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _towards(state: Dictionary, target: Vector2) -> Vector2:
	var delta: Vector2 = target - Vector2(float(state.cursor.x), float(state.cursor.y))
	return Vector2(signf(delta.x) if absf(delta.x) > 1.0 else 0.0, signf(delta.y) if absf(delta.y) > 1.0 else 0.0)

func _controls(state: Dictionary) -> Dictionary:
	var input: Vector2 = Vector2.ZERO
	var precision: bool = false
	var confirm: bool = false
	match str(state.encounterId):
		"flyer":
			var target: Vector2 = Vector2(128, 60) if state.markers[0].collected else Vector2(198, 60)
			if state.markers[0].collected:
				for threat: Dictionary in state.hazards + state.telegraphs:
					if threat.get("aimed", false): target.y = 67.5 if absf(float(threat.y) - 60) < 4 else 60
			input = _towards(state, target)
		"chip":
			if int(state.lastInputX) == 0:
				input.x = signf(float(state.safeColumn) - float(state.cursor.x))
		"deion":
			for hazard: Dictionary in state.hazards:
				if float(hazard.x) > 50.0 and float(hazard.x) < 145.0:
					if hazard.shape == "overhead": precision = true
					elif state.grounded: confirm = true
		"todd":
			var relative: int = int(state.clock) - int(state.leadIn)
			if relative < 0 or relative % 180 < 90 or relative % 180 >= 150:
				var target: Vector2 = Vector2(128.0, 60.0)
				for marker: Dictionary in state.markers:
					if not marker.collected:
						target = Vector2(float(marker.x), float(marker.y))
						break
				if int(state.consentCount) >= 2:
					for threat: Dictionary in state.hazards + state.telegraphs:
						if threat.get("aimed", false): target.x = 135.5 if absf(float(threat.x) - 128) < 4 else 128
				input = _towards(state, target)
				confirm = Vector2(float(state.cursor.x), float(state.cursor.y)).distance_to(target) < 10.0
		"pinpal":
			for tell: Dictionary in state.telegraphs:
				if tell.shape == "ball": input.x = signf(float(tell.x) - float(state.cursor.x))
			for hazard: Dictionary in state.hazards:
				if not hazard.friendly:
					input.x = signf(float(hazard.x) - float(state.cursor.x)) if absf(float(hazard.x) - float(state.cursor.x)) > 2.0 else 0.0
					confirm = float(hazard.y) >= 86.0 and absf(float(hazard.x) - float(state.cursor.x)) < 22.0 and int(state.flipperTicks) == 0
		"claim":
			var target: Vector2 = Vector2(80.0, 60.0) if int(state.phase) == 0 else Vector2(128.0, 60.0)
			if state.carryTag:
				if not state.markers[1].collected:
					target = Vector2(float(state.markers[1].x), float(state.markers[1].y))
				else:
					target = Vector2(204.0, 36.0) if int(state.phase) == 0 else Vector2(56.0, float(state.safeLane))
			input = _towards(state, target)
			confirm = int(state.phase) > 0 and Vector2(float(state.cursor.x), float(state.cursor.y)).distance_to(target) < 10.0
	return {"input": input, "precision": precision, "confirm": confirm}

func _replay(id: String, phase: int = 0, assist: float = 1.0, slow: bool = false, seed: int = 123) -> Dictionary:
	var state: Dictionary = Director.create(id, seed, phase)
	var hits: int = 0
	var max_hazards: int = 0
	var pulses: int = 0
	var warnings: bool = true
	while not state.done:
		var controls: Dictionary = _controls(state)
		state = Director.step(state, controls.input, controls.precision, assist, slow, true, controls.confirm)
		if state.hit: hits += 1
		if state.beatPulse: pulses += 1
		max_hazards = maxi(max_hazards, state.hazards.size())
		if int(state.clock) < 61 and not state.hazards.is_empty(): warnings = false
		if int(state.tick) > 2000:
			_check(false, "Encounter terminates: " + id)
			break
	state.testHits = hits
	state.testBounded = max_hazards <= 200
	state.testWarnings = warnings
	state.testPulses = pulses
	return state

func _test_motion() -> void:
	var state: Dictionary = Director.create("chip", 1)
	state = Director.step(state, Vector2.RIGHT)
	_check(state.cursor.x == 180.0 and state.cursor.y == 92.0, "Chip moves by discrete 52-pixel column hops")
	state = Director.step(state, Vector2.RIGHT)
	_check(state.cursor.x == 180.0, "Held direction does not slide or repeat hops")
	state = Director.step(state, Vector2.ZERO)
	state = Director.step(state, Vector2.RIGHT)
	_check(state.cursor.x == 232.0, "Fresh direction edge advances another column")
	state = Director.create("deion", 1)
	state = Director.step(state, Vector2.ONE, false, 1.0, false, false, true)
	_check(state.cursor.x == 64.0 and state.cursor.y < 96.0 and not state.grounded, "Deion ignores walking; confirm initiates ballistic jump")
	state = Director.create("deion", 1)
	state = Director.step(state, Vector2.LEFT, true)
	_check(state.cursor.x == 64.0 and state.cursor.y == 110.0 and state.ducking, "Precision becomes ground duck in runner")
	state = Director.create("pinpal", 1)
	state = Director.step(state, Vector2.UP)
	_check(state.cursor.y == 104.0, "Pin Pal flipper stays on bottom rail")
	state = Director.create("flyer", 1)
	state = Director.step(state, Vector2.UP)
	_check(state.cursor.y < 60.0, "Flyerer preserves free continuous movement")
	state = Director.create("todd", 1, 2)
	for _tick: int in range(100): state = Director.step(state, Vector2.RIGHT)
	_check(Vector2(float(state.cursor.x) - 128.0, float(state.cursor.y) - 60.0).length() < 47.0, "Todd constrains cursor to shrinking circular arena")

func _test_replays() -> void:
	for id: String in ["flyer", "chip", "deion", "todd", "pinpal"]:
		for phase: int in range(3):
			var state: Dictionary = _replay(id, phase)
			var label: String = id + "/" + str(phase)
			_check(state == _replay(id, phase), "Exact deterministic replay: " + label)
			_check(state.testBounded and state.testWarnings, "Bounded hazards and minimum one-second warning: " + label)
			_check(state.hazards.is_empty() and state.telegraphs.is_empty(), "Terminal cleanup: " + label)
			_check(state.promiseComplete, "Authored promise achievable using unique controls: " + label + " returns=" + str(state.deflections))
			_check(state.testHits == 0, "Demonstrated safe route without unavoidable damage: " + label)
		var normal: Dictionary = _replay(id)
		var slowed: Dictionary = _replay(id, 0, 0.7, true)
		_check(slowed.testPulses == normal.testPulses and slowed.testBounded, "Combined clocks preserve music beat count: " + id)
		_check(slowed.promiseComplete and slowed.testHits == 0, "Combined assist still supports a clean complete objective: " + id)
	var frozen: Dictionary = Director.create("deion", 42)
	for _tick: int in range(35): frozen = Director.step(frozen, Vector2.ZERO)
	var snapshot: Dictionary = frozen.duplicate(true)
	for _render_frame: int in range(200):
		var _visual_cursor: Dictionary = frozen.cursor
	_check(frozen == snapshot, "Pause and render-only frames cannot advance physics")
	var resumed: Dictionary = Director.step(frozen, Vector2.ZERO)
	_check(frozen == snapshot and resumed.clock == int(snapshot.clock) + 1, "Resume advances exactly one tick without mutating snapshot")

func _test_audit() -> void:
	var state: Dictionary = Director.create("todd", 10)
	state.clock = 90
	state = Director.step(state, Vector2.ZERO)
	_check(state.audit and not state.hit and state.hazards.is_empty(), "Red Audit is safe when player remains still")
	state = Director.step(state, Vector2.RIGHT)
	_check(state.hit, "Moving during explicitly announced Audit causes a hit")
	state = Director.create("todd", 10)
	state.cursor = {"x": 98.0, "y": 60.0}
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, true)
	_check(not state.markers[0].collected, "Consent boxes require affirmative confirm, not mere proximity")
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, true, true)
	_check(state.markers[0].collected and state.consentCount == 1, "Fresh confirm signs one consent box exactly once")
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, true, true)
	_check(state.consentCount == 1, "Repeated confirm cannot duplicate consent")

func _test_claim() -> void:
	for phase: int in range(2):
		var state: Dictionary = _replay("claim", phase)
		_check(state.tick == 480 and state.promiseComplete, "CLAIM authored phase completes in 480 ticks: " + str(phase))
		_check(state.testWarnings and state.testBounded, "CLAIM tag/sleeve threats remain readable and bounded")
		_check(state.testHits == 0, "CLAIM carries/delivers with a safe route: " + str(phase))
		if phase == 0:
			_check(state.carryTag and state.claimSweepPassed > 0, "CLAIM carries a picked-up tag through an actual sweep")
		else:
			_check(state.delivery == 1 and state.noteLeft and not state.markers[2].collected, "Boundary returns exactly one item and leaves a note for the other")
	var state: Dictionary = Director.create("claim", 1)
	state.carryTag = true
	state.markers[0].collected = true
	state.markers[1].collected = true
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, true)
	_check(not state.promiseComplete, "Picking up and delivering before any sweep does not falsely complete carry goal")
	state = Director.create("claim", 1, 1)
	state.carryTag = true
	state.boundary = false
	state.cursor = {"x": 56.0, "y": 36.0}
	state.markers[0].collected = true
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, true, true)
	_check(not state.markers[1].collected and not state.promiseComplete, "Unaccepted boundary cannot consume a destination or block later delivery")
	state.boundary = true
	state = Director.step(state, Vector2.ZERO, false, 1.0, false, true, true)
	_check(state.promiseComplete and state.markers[2].noted, "Accepting boundary delivers once and visibly notes the other destination")
	state = Director.create("claim", 1)
	state.clock = 60
	state.carryTag = true
	state.hazards = [{"id": 9, "x": 128.0, "y": 60.0, "previousX": 128.0, "previousY": 60.0, "radius": 5.0, "vx": 0.0, "vy": 0.0, "grazed": false, "born": 60, "shape": "claim_tag", "collision": "circle", "friendly": false, "collided": false, "cleared": false}]
	state = Director.step(state, Vector2.ZERO)
	_check(state.hit and state.carryTag, "Taking damage never destroys the carried CLAIM tag")

func _test_idle_pressure() -> void:
	for corner: Vector2 in [Vector2(8, 8), Vector2(248, 8), Vector2(8, 112), Vector2(248, 112)]:
		for phase: int in range(3):
			var edge_state: Dictionary = Director.create("flyer", 93, phase)
			edge_state.cursor = {"x": corner.x, "y": corner.y}
			var edge_hits: int = 0
			while not edge_state.done:
				edge_state = Director.step(edge_state, Vector2.ZERO)
				if edge_state.hit: edge_hits += 1
			_check(edge_hits > 0, "Flyer corner camping is pressured after a warning: %s phase%d" % [corner, phase])
	for id: String in ["flyer", "todd"]:
		for phase: int in range(3):
			var state: Dictionary = Director.create(id, 271828, phase)
			var hits: int = 0
			var warned: bool = false
			var audit_safe: bool = true
			while not state.done:
				for tell: Dictionary in state.telegraphs:
					if tell.get("aimed", false) and int(tell.ticksRemaining) >= 59: warned = true
				state = Director.step(state, Vector2.ZERO)
				if state.hit: hits += 1
				if id == "todd" and state.audit and (state.hit or not state.hazards.is_empty()): audit_safe = false
			_check(hits > 0 and warned, "%s phase%d center camping takes damage after a full one-second aimed warning" % [id, phase])
			if id == "todd": _check(audit_safe, "Todd Audit always clears threats and rewards remaining still")
