extends SceneTree
## Run: Godot --headless --path godot-game --script res://tests/rules_test.gd
const Rules = preload("res://core/battle_rules.gd")
const Pattern = preload("res://core/pattern.gd")
var checks: int = 0
var failures: int = 0

func _init() -> void:
	_test_rules()
	_test_patterns()
	print("Godot pure rules: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _test_rules() -> void:
	var battle: Dictionary = Rules.create_battle()
	_check(battle.party[0].hp == 84 and battle.party[1].hp == 72 and battle.party[2].hp == 96, "Canonical party HP")
	_check(battle.hp == 48 and battle.sync == 20, "Flyerer starts with 48 HP and 20 SYNC")
	battle.sync = 90
	var commands: Array = [{"actor": 0, "kind": "guard"}, {"actor": 1, "kind": "heal", "target": 0}, {"actor": 2, "kind": "brace"}]
	_check(Rules.validate_plan(battle, commands).is_empty(), "Projected guard funds valid plan")
	var next: Dictionary = Rules.resolve_plan(battle, commands)
	_check(next.sync == 50 and battle.sync == 90, "Guard cap precedes spend; caller state unchanged")
	battle.sync = 0
	_check("SYNC" in Rules.validate_plan(battle, commands), "Over-reservation rejected")
	battle = Rules.create_battle()
	battle.sync = 8
	next = Rules.resolve_plan(battle, [{"actor": 0, "kind": "shield"}, {"actor": 2, "kind": "guard"}])
	_check(next.sync == 0 and next.shield, "Later actor guard funds earlier actor talent")
	battle.sync = 80
	battle.inventory.granola = 1
	_check("item" in Rules.validate_plan(battle, [{"actor": 0, "kind": "item", "target": 0}, {"actor": 1, "kind": "item", "target": 1}]), "Double item use rejected")
	_check("committed" in Rules.validate_plan(battle, [{"actor": 0, "kind": "connect", "joint": "hearMeOut"}, {"actor": 1, "kind": "guard"}]), "Joint action reserves second actor")
	next = Rules.resolve_plan(battle, [{"actor": 0, "kind": "connect", "joint": "hearMeOut"}, {"actor": 2, "kind": "guard"}])
	_check(next.openness == 50 and next.sync == 57, "Joint action executes before singles")
	_check("talent" in Rules.validate_plan(battle, [{"actor": 0, "kind": "heal", "target": 0}]), "Talent ownership enforced")
	_check("ally" in Rules.validate_plan(battle, [{"actor": 1, "kind": "heal", "target": 99}]), "Invalid ally rejected")
	_check("one promise" in Rules.validate_plan(battle, [{"actor": 0, "kind": "promise"}, {"actor": 1, "kind": "promise"}]), "Only one promise per phase")
	battle.party[0].hp = 0
	_check("Actor" in Rules.validate_plan(battle, [{"actor": 0, "kind": "guard"}]), "Downed actor cannot queue a command")
	battle = Rules.create_battle()
	battle.hp = 10
	next = Rules.resolve_plan(battle, [{"actor": 0, "kind": "strike", "timing": 1.0}, {"actor": 1, "kind": "item", "target": 0}])
	_check(next.hp == 0 and next.outcome == "forceful" and next.inventory == battle.inventory, "Exact lethal stops later consumable")
	_check(Rules.hit(next, 0).party == next.party, "Enemy cannot attack after forceful victory")
	battle = Rules.create_battle()
	_check(Rules.resolve_plan(battle, [{"actor": 0, "kind": "strike"}]).hp == 35, "Default timing gives 1.0 multiplier")
	_check(Rules.resolve_plan(battle, [{"actor": 0, "kind": "strike", "timing": -1.0}]).hp == 47, "Missed timing deals one damage")
	var jules_hit: Dictionary = Rules.strike_result("jules", 14, {"kind": "strike", "hits": [1.0]})
	_check(int(jules_hit.crits) == 1 and int(jules_hit.damage) == 29, "A perfect Jules swing is a critical: " + str(jules_hit))
	_check(int(Rules.strike_result("jules", 14, {"kind": "strike", "hits": [0.8]}).crits) == 0, "A good but not perfect swing is no critical")
	var imani_hit: Dictionary = Rules.strike_result("imani", 10, {"kind": "strike", "hits": [1.0, 1.0]})
	_check(int(imani_hit.crits) == 2 and int(imani_hit.damage) == 24, "Imani's two perfect beats both crit: " + str(imani_hit))
	_check(int(Rules.strike_result("imani", 10, {"kind": "strike", "hits": [-1.0, 1.0]}).damage) == 13, "A missed beat is 1 damage, the other still counts")
	_check(int(Rules.strike_result("walt", 12, {"kind": "strike", "hits": [0.5]}).damage) > int(Rules.strike_result("jules", 12, {"kind": "strike", "hits": [0.5]}).damage), "Walt hits heavier than Jules for the same timing")
	_check(Rules.taps("imani") == 2 and Rules.taps("jules") == 1 and Rules.taps("walt") == 1, "Imani taps twice")
	_check(is_equal_approx(Rules.combo_for([{"kind": "strike", "timing": 0.5}]), 1.0) and is_equal_approx(Rules.combo_for([{"kind": "strike", "timing": 0.5}, {"kind": "strike", "timing": 0.5}, {"kind": "strike", "timing": 0.5}]), 1.4) and is_equal_approx(Rules.combo_for([{"kind": "strike", "timing": 0.5}, {"kind": "strike", "timing": -1.0}]), 1.0), "Each extra landed striker adds 20 percent")
	battle = Rules.create_battle()
	var solo_hp: int = int(Rules.resolve_plan(battle, [{"actor": 0, "kind": "strike", "timing": 0.5}]).hp)
	var duo_hp: int = int(Rules.resolve_plan(battle, [{"actor": 0, "kind": "strike", "timing": 0.5}, {"actor": 2, "kind": "strike", "timing": 0.5}]).hp)
	_check(48 - duo_hp > (48 - solo_hp) + 5, "A team of two outdamages two separate swings")
	battle.guards[0] = true
	battle.brace = true
	battle.shield = true
	next = Rules.hit(battle, 0, 12)
	_check(next.party[0].hp == 84 and not next.shield, "Shield cancels first hit before reductions")
	_check(Rules.hit(next, 0, 12).party[0].hp == 80, "Defence then guard then brace")
	battle = Rules.create_battle()
	battle.party[0].hp = 0
	battle.sync = 30
	_check(Rules.resolve_plan(battle, [{"actor": 1, "kind": "heal", "target": 0}]).party[0].hp == 28, "Talent revives a downed ally")
	_check(Rules.resolve_plan(battle, [{"actor": 2, "kind": "item", "item": "thermos", "target": 0}]).party[0].hp == 45, "Thermos revives a downed ally")
	_check(Rules.recover(battle.party)[0].hp == 17 and battle.party[0].hp == 0, "Victory recovery revives and is pure")
	battle = Rules.resolve_plan(Rules.create_battle(), [{"actor": 0, "kind": "connect"}, {"actor": 1, "kind": "promise"}])
	_check(Rules.complete_promise(battle, false).openness == 25, "Failed promise leaves peaceful route available")
	battle = Rules.complete_promise(battle, true)
	_check(battle.openness == 70 and battle.outcome == "active", "Kept promise adds 45 Openness and still requires explicit release")
	_check(Rules.resolve_plan(battle, [{"actor": 0, "kind": "connect"}, {"actor": 1, "kind": "connect"}, {"actor": 2, "kind": "release"}]).outcome == "peaceful", "Explicit release settles Flyerer")
	battle = Rules.create_battle()
	battle.openness = 75
	next = Rules.resolve_plan(battle, [{"actor": 0, "kind": "connect"}, {"actor": 1, "kind": "release"}, {"actor": 2, "kind": "strike"}])
	_check(next.outcome == "peaceful" and next.hp == 48, "Planned connect exposes release; terminal actions stop")
	battle = Rules.create_battle([], {"granola": 0, "cocoa": 0, "thermos": 0})
	battle.hp = 5
	next = Rules.resolve_plan(battle, [{"actor": 0, "kind": "promise"}, {"actor": 1, "kind": "strike", "timing": 1.0}])
	_check(next.outcome == "forceful" and not next.promise, "Empty-supply victory cancels impossible promise neutrally")
	battle = Rules.create_battle()
	battle.party[0].hp = 1
	battle.party[1].hp = 0
	next = Rules.hit(battle, 0, 100)
	_check(next.outcome == "active", "Single downed target is not defeat")
	_check(Rules.hit(next, 2, 1000).outcome == "defeat", "All downed opens defeat")

func _replay(seed: int, assist: float = 1.0, slow: bool = false) -> Dictionary:
	var state: Dictionary = Pattern.create(seed)
	while not state.done:
		var tick: int = int(state.tick)
		var input: Vector2 = Vector2(1.0 if tick % 100 < 50 else -1.0, 1.0 if tick % 140 < 70 else -1.0)
		state = Pattern.step(state, input, false, assist, slow)
		if int(state.tick) > 2000:
			_check(false, "Replay must terminate")
			break
	return state

func _hazard(y: float, vx: float = 0.0, x: float = 128.0) -> Dictionary:
	return {"id": 22, "x": x, "y": y, "previousX": x, "previousY": y, "radius": 5.0, "vx": vx, "vy": 0.0, "grazed": false, "born": 0}

func _test_patterns() -> void:
	_check(_replay(123, 0.7, true) == _replay(123, 0.7, true), "Seeded replay deterministic with combined clocks")
	_check(_replay(123).tick == 420, "Normal phase lasts 420 ticks")
	_check(_replay(123, 1.0, true).tick == 525, "Half Time extends phase to 525 ticks")
	_check(_replay(123, 0.7, true).tick == 750, "Half Time plus 70 percent assist lasts 750 ticks")
	var state: Dictionary = Pattern.create(123)
	var warnings: Array[int] = []
	var bounded: bool = true
	var first_safe: bool = true
	var outside: bool = true
	for tick: int in range(420):
		state = Pattern.step(state, Vector2.ZERO)
		if tick < 45 and not state.hazards.is_empty():
			first_safe = false
		if tick % 48 == 0 and tick < 336:
			warnings.append(roundi((float(state.telegraphs.back().y) - 18.0) / 28.0))
		for hazard: Dictionary in state.hazards:
			if int(hazard.born) == int(state.clock) - 1 and float(hazard.x) != -12.0:
				outside = false
		if state.hazards.size() >= 10:
			bounded = false
	_check(warnings == [0, 3, 1, 3, 1, 1, 2], "32-bit xorshift sequence matches verified browser reference")
	_check(first_safe, "At least 45 ticks warning before hazards")
	_check(outside and bounded, "No spawn on cursor; hazard counts remain bounded")
	_check(state.done and state.hazards.is_empty() and state.telegraphs.is_empty(), "Phase completion clears hazards and warnings")
	state = Pattern.step(Pattern.create(19), Vector2.ONE)
	var travel: float = Vector2(float(state.cursor.x) - 128.0, float(state.cursor.y) - 60.0).length()
	_check(absf(travel - 112.0 / 60.0) < 0.01, "Diagonal cursor movement normalized")
	state = Pattern.create(19)
	for _tick: int in range(90):
		var input: Vector2 = Vector2(signf(218.0 - float(state.cursor.x)), signf(92.0 - float(state.cursor.y)))
		state = Pattern.step(state, input, false, 1.0, false, true)
	_check(state.promiseComplete, "Outlined invitation reachable during phase")
	state = Pattern.create(1)
	state.hazards = [_hazard(60.0, 56.0, 100.0)]
	state = Pattern.step(state, Vector2.ZERO)
	_check(state.hit and state.invulnerability == 45 and state.grazeDelta == 0, "Swept collision hits fast projectile, gives 45-tick protection, no graze")
	state.hazards = [_hazard(60.0)]
	state = Pattern.step(state, Vector2.ZERO)
	_check(not state.hit and state.invulnerability == 44, "Protected ticks suppress repeated damage")
	state = Pattern.create(1)
	state.hazards = [_hazard(70.0)]
	state = Pattern.step(state, Vector2.ZERO)
	_check(state.grazeDelta == 1, "Near miss awards one graze")
	state = Pattern.step(state, Vector2.ZERO)
	_check(state.grazeDelta == 0 and state.grazes == 1, "Projectile cannot grant repeated graze awards")
	state = Pattern.create(1)
	state.hazards = [_hazard(60.0)]
	state = Pattern.step(state, Vector2.ZERO)
	state.cursor.y = 70.0
	state = Pattern.step(state, Vector2.ZERO)
	_check(state.grazes == 0, "Collision projectile cannot later award graze")
	var before: Dictionary = Pattern.create(5)
	state = Pattern.step(before, Vector2.RIGHT)
	_check(before.cursor.x == 128.0 and before.tick == 0 and state.tick == 1, "Simulation never mutates previous replay state")
