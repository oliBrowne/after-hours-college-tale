extends SceneTree
## Run: Godot --headless --path godot-game --script res://tests/growth_test.gd
## Deltarune-style growth, keepsakes, per-boss damage and the Walt debris.
const Rules = preload("res://core/battle_rules.gd")
const Growth = preload("res://core/party_growth.gd")
var checks: int = 0
var failures: int = 0

func _init() -> void:
	_test_milestones()
	_test_keepsakes()
	_test_damage()
	_test_walt_debris()
	print("Godot growth and balance: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _stats(party: Array, index: int) -> Array:
	return [int(party[index].hp), int(party[index].max), int(party[index].power), int(party[index].defence)]

func _test_milestones() -> void:
	var start: Array = Rules.initial_party()
	_check(Growth.apply(start, {}) == start, "No milestones leaves the starting party unchanged")
	var forceful: Array = Growth.apply(start, {"claim_resolution": "forceful"})
	var peaceful: Array = Growth.apply(start, {"claim_resolution": "peaceful"})
	_check(_stats(forceful, 0) == [96, 96, 16, 2] and _stats(forceful, 1) == [82, 82, 12, 1] and _stats(forceful, 2) == [108, 108, 14, 3], "Opening milestone raises all three and heals by the gain")
	_check(forceful == peaceful, "Peaceful and forceful routes grow the same")
	_check(Growth.apply(forceful, {"claim_resolution": "forceful"}) == forceful, "Applying twice never doubles a boost")
	var hurt: Array = start.duplicate(true)
	hurt[0].hp = 50
	_check(_stats(Growth.apply(hurt, {"claim_resolution": "peaceful"}), 0) == [62, 96, 16, 2], "An old save keeps its damage but gains the new max")
	var late: Dictionary = {"claim_resolution": "peaceful", "chapter1_complete": true, "chapter2_complete": true, "chapter3_complete": true}
	var grown: Array = Growth.apply(start, late)
	_check(_stats(grown, 0) == [140, 140, 22, 4] and _stats(grown, 1) == [120, 120, 18, 3] and _stats(grown, 2) == [152, 152, 20, 5], "Chapter 3 save loads with final stats")
	_check(Growth.milestones({"claim_resolution": "", "chapter1_complete": false}) == 0, "Empty or false milestone flags do not count")
	var legacy: Array = start.duplicate(true)
	legacy[2] = {"id": "cal", "hp": 40, "max": 100, "power": 9, "defence": 4}
	_check(Growth.apply(legacy, late)[2] == legacy[2], "Unknown legacy member is left for migration")
	var state: Dictionary = NativeState.fresh()
	state.flags = late.duplicate()
	state.flags.growth_seen = "4"
	state.flags.keepsake_bus_pass = true
	state.flags.keepsake_jules = "bus_pass"
	state.party = Growth.apply(state.party, state.flags)
	_check(NativeSaveService.validate_state(state), "Grown party and keepsake flags pass the save validator")

func _test_keepsakes() -> void:
	var start: Array = Rules.initial_party()
	var flags: Dictionary = {"keepsake_night_lanyard": true, "keepsake_jules": "night_lanyard"}
	var worn: Array = Growth.apply(start, flags)
	_check(_stats(worn, 0) == [92, 92, 14, 2], "Lanyard adds 8 max HP and heals by it")
	flags.keepsake_jules = ""
	_check(_stats(Growth.apply(worn, flags), 0) == [84, 84, 14, 2], "Removing a keepsake clamps HP to the lower max")
	var hurt: Array = start.duplicate(true)
	hurt[0].hp = 50
	var swapped: Array = Growth.apply(hurt, {"keepsake_night_lanyard": true, "keepsake_jules": "night_lanyard"}, false)
	_check(_stats(swapped, 0) == [50, 92, 14, 2], "Equipping a keepsake raises max HP without healing")
	swapped = Growth.apply(Growth.apply(swapped, {"keepsake_night_lanyard": true, "keepsake_jules": ""}, false), {"keepsake_night_lanyard": true, "keepsake_jules": "night_lanyard"}, false)
	_check(_stats(swapped, 0) == [50, 92, 14, 2], "Cycling a keepsake off and on never heals")
	_check(Growth.stats("jules", {"keepsake_jules": "bus_pass"}).defence == 2, "An equipped keepsake that was never found gives nothing")
	_check(Growth.stats("jules", {"keepsake_guitar_pick": true, "keepsake_jules": "guitar_pick"}).power == 14, "Another member's keepsake gives nothing")
	_check(Growth.stats("imani", {"keepsake_guitar_pick": true, "keepsake_imani": "guitar_pick"}).power == 12, "Guitar pick adds 2 power")
	var setlist: Dictionary = {"keepsake_setlist": true, "keepsake_imani": "setlist"}
	_check(Growth.starting_sync(setlist) == 0, "Setlist needs Imani in the party")
	setlist.imani_joined = true
	_check(Growth.starting_sync(setlist) == 10, "Setlist adds 10 starting SYNC")
	_check(Growth.owned({"keepsake_bus_pass": true, "keepsake_moms_keychain": true, "keepsake_setlist": true}, "jules") == ["bus_pass", "moms_keychain"], "Owned keepsakes are listed per member")
	for id: String in Growth.KEEPSAKES:
		var keepsake: Dictionary = Growth.KEEPSAKES[id]
		_check(keepsake.member in Growth.MEMBERS and Growth.STAT_TEXT.has(keepsake.stat) and int(keepsake.x) > 0 and int(keepsake.y) > 0, id + " is placed and has a known stat")

func _test_damage() -> void:
	var battle: Dictionary = Rules.create_battle()
	battle.max_hp = 48
	_check(Rules.enemy_damage("walt", battle) == 10 and Rules.enemy_damage("", battle) == 8, "Opening bosses hit for 8 to 10")
	_check(Rules.enemy_damage("encore", battle) == 17 and Rules.enemy_damage("autocomplete", battle) == 22 and Rules.enemy_damage("rook", battle) == 26 and Rules.enemy_damage("val", battle) == 28, "Later bosses hit harder")
	_check(Rules.enemy_damage("val", battle, true) == 14, "Reduced incoming damage halves a hit")
	battle.openness = 50
	_check(Rules.desperate(battle) and Rules.enemy_damage("val", battle) == 35, "At 50 Openness a boss hits 25 percent harder")
	battle.openness = 0
	battle.hp = 24
	_check(Rules.desperate(battle) and Rules.enemy_damage("walt", battle) == 13, "At half HP a boss hits 25 percent harder")
	battle.eased = true
	_check(Rules.enemy_damage("walt", battle) == 6, "A limit set with CONNECT eases the hit instead of the desperate bonus")
	battle.eased = false
	battle.hp = 25
	_check(not Rules.desperate(battle), "Above half HP and under 50 Openness is not desperate")
	battle.promise = true
	_check(Rules.complete_promise(battle, true).openness == 45, "A kept promise is worth 45 Openness")

func _run_walt(x: float, ticks: int, phase: int = 0) -> Dictionary:
	var p: Dictionary = NativeNewEncounter.create("walt", 99, phase, 0)
	p.cursor.x = x
	var hits: int = 0
	for _i: int in range(ticks):
		p = NativeNewEncounter.step(p, Vector2.ZERO, false, 1.0, false, true, true)
		if p.hit: hits += 1
		if p.done: break
	return {"pattern": p, "hits": hits}

func _test_walt_debris() -> void:
	var stay: Dictionary = _run_walt(128.0, 2000)
	_check(int(stay.hits) >= 1, "Standing still in the shelter gets caught by debris")
	_check(int(stay.pattern.gustsKept) >= 3 and int(stay.pattern.lantern) > 0, "The lantern promise itself still works from the centre")
	var first: Dictionary = _run_walt(145.0, int(NativeNewEncounter.create("walt", 99, 0, 0).leadIn) + 119)
	_check(int(first.hits) == 0, "Stepping to the clear half of the shelter dodges the first debris")
	var telegraphed: bool = false
	var p: Dictionary = NativeNewEncounter.create("walt", 99, 1, 0)
	for _i: int in range(int(p.leadIn) + 60):
		p = NativeNewEncounter.step(p, Vector2.ZERO, false, 1.0, false, false, false)
		for tell: Dictionary in p.telegraphs:
			if tell.get("debris", false): telegraphed = true
	_check(telegraphed, "Debris is warned before it falls")
