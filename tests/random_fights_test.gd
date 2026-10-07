extends SceneTree
## Run: Godot --headless --path godot-game --script res://tests/random_fights_test.gd
## Wandering fights: the table, the rooms that use it, the dice, the rewards and the rules for
## when a fight may start. The full walk-in, fight and payout is the --qa-wander input route.
var checks: int = 0
var failures: int = 0

## A stand-in for the game scene with just what NativeRandomFights reads.
class Fake extends Node:
	enum Mode { TITLE, WORLD, DIALOGUE }
	var state: Dictionary = {"seed": 271828, "room": "F04", "flags": {"flyer_resolution": "peaceful"}}
	var rooms: Dictionary = {}
	var mode: int = Mode.WORLD
	var grace_ticks: int = 0
	var arrival_point: Vector2 = Vector2.INF
	var boss_id: String = ""
	var qa: bool = false
	var player: Node2D = Node2D.new()

func _init() -> void:
	_test_table()
	_test_rooms()
	_test_dice()
	_test_rewards()
	_test_rules()
	print("Wandering fights: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _fake(room: String = "F04") -> Fake:
	var g: Fake = Fake.new()
	var all: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/rooms.json"))
	g.rooms = all
	g.state.room = room
	g.player.position = Vector2(-1000, -1000)
	return g

func _test_table() -> void:
	for id: String in NativeRandomFights.FIGHTS:
		var e: Dictionary = NativeRandomFights.FIGHTS[id]
		_check(id.begins_with("rf_"), id + " uses the rf_ prefix")
		_check(NativeRandomFights.is_fight(id) and NativeRandomFights.name_of(id) == str(e.name), id + " is a fight with a name")
		_check(int(e.hp) > 0 and int(e.hp) <= 80, id + " has a small HP pool")
		_check(e.connect is Array and e.connect.size() == 3, id + " has the three CONNECT labels")
		_check(int(e.bucks[0]) > 0 and int(e.bucks[0]) <= int(e.bucks[1]), id + " pays a sane Buff Bucks range")
		_check(not str(e.intro).is_empty() and not str(e.peaceful).is_empty() and not str(e.forceful).is_empty(), id + " has all three lines")
		_check(not "—" in str(e.intro) + str(e.peaceful) + str(e.forceful), id + " lines have no em-dashes")
		_check(NativeCastArt.IDS.has(str(e.stand_in)), id + " stand-in " + str(e.stand_in) + " is a cast sprite")
		_check(NativeCastArt.frames(str(e.stand_in)) != null and NativeRandomFights.frames(id) != null, id + " has sprite frames")
		_check(BattleRules.ENEMY_DAMAGE.has(id) and int(BattleRules.ENEMY_DAMAGE[id]) <= 12, id + " hits lightly")
		_check(DodgeBox.handles(id), id + " has a dodge script")
	_check(not NativeRandomFights.is_fight("walt") and NativeRandomFights.name_of("walt").is_empty(), "Story bosses are not wandering fights")

func _test_rooms() -> void:
	var all: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/rooms.json"))
	var used: Dictionary = {}
	for room: String in all:
		var table: Dictionary = all[room].get("wander", {})
		for id: String in table:
			used[id] = true
			_check(NativeRandomFights.is_fight(id) and float(table[id]) > 0.0, room + " lists a real fight " + id + " with a weight")
		if not table.is_empty():
			_check(not room.begins_with("M") and not room.begins_with("G") and not room.begins_with("D"), room + " is not a finale, graduation or dorm room")
	for id: String in NativeRandomFights.FIGHTS:
		_check(used.has(id), id + " appears in at least one room")
	_check(all.has("F04") and all["F04"].wander.has("rf_sunbeam") and float(all["F04"].wander["rf_sunbeam"]) < float(all["F04"].wander["rf_hippie"]), "Sunbeam is rare and lives on the Farrand lawn")

func _test_dice() -> void:
	var g: Fake = _fake()
	var first: String = NativeRandomFights.pick(g)
	_check(NativeRandomFights.pick(g) == first, "The same save rolls the same fight")
	var seen: Dictionary = {}
	for roll: int in range(60):
		g.state.flags.wander_rolls = str(roll)
		var id: String = NativeRandomFights.pick(g)
		seen[id] = int(seen.get(id, 0)) + 1
		_check(g.rooms.F04.wander.has(id), "Roll %d stays inside the room's list" % roll)
	_check(seen.size() >= 2 and seen.has("rf_hippie"), "Different rolls reach different fights, mostly hippies on the lawn")
	_check(int(seen.get("rf_sunbeam", 0)) <= 15, "Sunbeam is rare (%d of 60)" % int(seen.get("rf_sunbeam", 0)))
	var goal: float = NativeRandomFights.next_goal(g)
	_check(goal >= NativeRandomFights.BASE_GOAL and goal <= NativeRandomFights.BASE_GOAL + NativeRandomFights.GOAL_SPREAD, "The walk goal is about a minute of walking")

func _test_rewards() -> void:
	var r: RandomNumberGenerator = RandomNumberGenerator.new()
	for id: String in NativeRandomFights.FIGHTS:
		var lo: int = int(NativeRandomFights.FIGHTS[id].bucks[0])
		var hi: int = int(NativeRandomFights.FIGHTS[id].bucks[1])
		for seed_value: int in range(20):
			r.seed = seed_value
			var peaceful: int = NativeRandomFights.payout(id, true, r)
			r.seed = seed_value
			var forceful: int = NativeRandomFights.payout(id, false, r)
			_check(peaceful >= lo and peaceful <= hi, id + " peaceful payout in range")
			_check(forceful >= 1 and forceful <= peaceful, id + " forceful payout is smaller but never zero")
	# Whatever a win writes must still be a valid save (flags are bool or String, supplies 8 at most).
	for id: String in NativeRandomFights.FIGHTS:
		var state: Dictionary = NativeState.fresh()
		for seed_value: int in range(40):
			r.seed = seed_value
			var won: Dictionary = NativeRandomFights.reward(state, id, seed_value % 2 == 0, r)
			_check(int(won.gain) >= 1, id + " reward pays something")
			if not NativeSaveService.validate_state(state):
				_check(false, id + " state still saves after win " + str(seed_value))
				break
		_check(NativeSaveService.validate_state(state), id + " state is a valid save after 40 wins")
		_check(NativeRandomFights.count(state.flags, "wander_wins") == 40 and NativeRandomFights.bucks(state.flags) >= 40, id + " counts wins and keeps the balance")
	_check(NativeRandomFights.summary(8, "") == "+8 Buff Bucks" and NativeRandomFights.summary(8, "granola") == "+8 Buff Bucks and a granola", "The payout line names the item")
	_check(NativeRandomFights.bucks({}) == 0 and NativeRandomFights.bucks({"buff_bucks": "12"}) == 12, "Buff Bucks read from flags")

func _test_rules() -> void:
	var g: Fake = _fake()
	_check(NativeRandomFights.allowed(g), "Allowed on the lawn after the first story fight")
	g.state.flags.erase("flyer_resolution")
	_check(not NativeRandomFights.allowed(g), "Not before the first story fight")
	g.state.flags.flyer_resolution = "peaceful"
	g.state.flags.wander_off = true
	_check(not NativeRandomFights.allowed(g), "The Settings switch turns them off")
	g.state.flags.erase("wander_off")
	g.state.flags.movein_active = true
	_check(not NativeRandomFights.allowed(g), "Not during the dorm prologue")
	g.state.flags.erase("movein_active")
	g.state.flags.aftermath_pending = "walt"
	_check(not NativeRandomFights.allowed(g), "Not while an aftermath scene is pending")
	g.state.flags.aftermath_pending = ""
	g.mode = Fake.Mode.DIALOGUE
	_check(not NativeRandomFights.allowed(g), "Only while walking in the world")
	g.mode = Fake.Mode.WORLD
	g.grace_ticks = 10
	_check(not NativeRandomFights.allowed(g), "Not right after a fight")
	g.grace_ticks = 0
	g.arrival_point = Vector2(5, 5)
	_check(not NativeRandomFights.allowed(g), "Not right after arriving in a room")
	g.arrival_point = Vector2.INF
	g.boss_id = "walt"
	_check(not NativeRandomFights.allowed(g), "Not during a story fight")
	g.boss_id = ""
	_check(NativeRandomFights.allowed(g), "Allowed again once everything is clear")
	var quiet: Fake = _fake("G01")
	_check(not NativeRandomFights.allowed(quiet), "A room with no wander list never rolls")
	var door: Dictionary = g.rooms.F04.objects[0]
	g.player.position = Vector2(float(door.x), float(door.y)) + Vector2(10, 0)
	_check(NativeRandomFights.near_something(g), "Standing next to something you can press blocks the roll")
	g.player.position = Vector2(-1000, -1000)
	_check(not NativeRandomFights.near_something(g), "Open ground does not")
