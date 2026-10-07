extends SceneTree
const Needs = preload("res://core/claim_needs.gd")
const Rules = preload("res://core/battle_rules.gd")
const Director = preload("res://core/encounter_director.gd")
var checks: int = 0
var failures: int = 0

func _init() -> void:
	_test_bypass()
	_test_objectives()
	print("Godot Advisor Bev needs: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition: failures += 1; printerr("FAIL: ", label)

func _towards(state: Dictionary, target: Vector2) -> Vector2:
	var delta: Vector2 = target - Vector2(float(state.cursor.x), float(state.cursor.y))
	return Vector2(signf(delta.x) if absf(delta.x) > 1 else 0, signf(delta.y) if absf(delta.y) > 1 else 0)

func _complete(phase: int, boundary: bool = true, promised: bool = true) -> Dictionary:
	var state: Dictionary = Director.create("claim", 42, phase)
	state.boundary = boundary
	while not state.done:
		var target: Vector2 = Vector2(80, 60) if phase == 0 else Vector2(128, 60)
		if state.carryTag: target = Vector2(float(state.markers[1].x), float(state.markers[1].y))
		var confirm: bool = phase == 1 and Vector2(float(state.cursor.x), float(state.cursor.y)).distance_to(target) < 10
		state = Director.step(state, _towards(state, target), false, 1.0, false, promised, confirm)
	return state

func _test_bypass() -> void:
	var needs: Dictionary = Needs.create()
	var battle: Dictionary = Rules.create_battle()
	battle.hp = 190
	battle = Rules.resolve_plan(battle, [{"actor": 0, "kind": "connect"}, {"actor": 1, "kind": "connect"}, {"actor": 2, "kind": "connect"}])
	battle = Rules.resolve_plan(battle, [{"actor": 0, "kind": "connect"}, {"actor": 1, "kind": "guard"}, {"actor": 2, "kind": "guard"}])
	_check(battle.openness == 100, "Repeated observations reproduce generic 100 Openness bypass")
	var commands: Array = [{"actor": 0, "kind": "release"}]
	_check(Rules.validate_plan(battle, commands).is_empty(), "Generic battle rules intentionally permit ordinary release at 100")
	_check(Rules.resolve_plan(battle, commands).outcome == "peaceful", "Source-derived bypass reproduces without actual needs")
	_check(not Needs.validate_plan(needs, commands).is_empty() and not Needs.can_release(needs), "Advisor Bev production gate rejects that exact release plan")
	_check(Needs.combat_phase(needs, 190) == 0, "Rounds and observations cannot advance peaceful phase")
	_check(Needs.combat_phase(needs, 110) == 1 and not Needs.can_release(needs), "Damage advances attack/music phase independently without granting peaceful release")
	_check(Needs.combat_phase(needs, 80, true) == 0, "Offering first promise after prior damage restores reachable carry objective")
	battle = Rules.resolve_plan(battle, [{"actor": 0, "kind": "strike", "timing": 1.0}, {"actor": 1, "kind": "strike", "timing": 1.0}, {"actor": 2, "kind": "strike", "timing": 1.0}])
	while battle.outcome == "active": battle = Rules.resolve_plan(battle, [{"actor": 0, "kind": "strike", "timing": 1.0}, {"actor": 1, "kind": "strike", "timing": 1.0}, {"actor": 2, "kind": "strike", "timing": 1.0}])
	_check(battle.outcome == "forceful" and not Needs.can_release(needs), "Forceful route remains reachable without manufacturing concrete needs")

func _test_objectives() -> void:
	var empty: Dictionary = Needs.create()
	var first: Dictionary = _complete(0)
	var second: Dictionary = _complete(1)
	_check(first.promiseComplete and second.promiseComplete, "Real director controls can complete both authored needs")
	_check(not Needs.can_release(Needs.record_defense(empty, second, true, true)), "Returning before tag delivery cannot satisfy sequence")
	var carried: Dictionary = Needs.record_defense(empty, first, true, false)
	_check(carried.tagDelivered and not empty.tagDelivered, "Completed carry through actual sweep advances independent copied need state")
	_check(Needs.combat_phase(carried, 190) == 1 and not Needs.can_release(carried), "First need changes phase but does not unlock release")
	_check(Needs.combat_phase(carried, 80, true) == 1, "Completed first need keeps next promised return in phase one")
	var released: Dictionary = Needs.record_defense(carried, second, true, true)
	_check(Needs.can_release(released) and Needs.validate_plan(released, [{"actor": 0, "kind": "release"}]).is_empty(), "One return plus explicit note unlocks peaceful release")
	_check(Needs.record_defense(carried, second, false, true) == released, "Explicit boundary alternative can complete second need without duplicate PROMISE")
	_check(Needs.record_defense(released, second, true, true) == released, "Completion event replay is idempotent")
	_check(not Needs.can_release(Needs.record_defense(carried, second, true, false)), "Unaccepted boundary cannot manufacture completion")
	var incomplete: Dictionary = second.duplicate(true)
	incomplete.done = false
	_check(Needs.record_defense(carried, incomplete, true, true) == carried, "Intermediate contact cannot resolve a need before the defense ends")
	incomplete = second.duplicate(true); incomplete.promiseComplete = false
	_check(Needs.record_defense(carried, incomplete, true, true) == carried, "Failed second promise preserves first need and allows retry")
	var failed_second: Dictionary = _complete(1, false)
	var preserved: Dictionary = Needs.record_defense(carried, failed_second, true, false)
	_check(not failed_second.promiseComplete and preserved == carried, "Real director failure without accepted boundary retains the carried-ticket need")
	_check(Needs.can_release(Needs.record_defense(preserved, second, true, true)), "A later real boundary return recovers peacefully after that failed attempt")
	incomplete = second.duplicate(true); incomplete.markers[2].collected = true
	_check(not Needs.can_release(Needs.record_defense(carried, incomplete, true, true)), "Returning both items violates one-item boundary")
	incomplete = first.duplicate(true); incomplete.claimSweepPassed = 0
	_check(not Needs.record_defense(empty, incomplete, true, false).tagDelivered, "Tag contacts without surviving a carry sweep are insufficient")
	var failed: Dictionary = _complete(0, true, false)
	_check(not failed.promiseComplete and Needs.record_defense(empty, failed, false, false) == empty, "Observation-only defense cannot fulfill carried-ticket need")
	_check(Needs.record_defense(carried, first, true, false) == carried, "Repeated successful first objectives never replace the second need")
	_check(Needs.create() == empty and not Needs.can_release(Needs.create()), "Normal battle retry initializes both concrete needs afresh")
