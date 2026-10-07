extends SceneTree
## Run: Godot --headless --path godot-game --script res://tests/hub_test.gd
## The Fountain Court hub, the Hill and the Pearl Street office: the new rooms and their doors,
## the shops (Buff Bucks sinks), the two side bosses and their rewards. The walk-through with real
## input is the --qa-hub route.
var checks: int = 0
var failures: int = 0
const NEW_ROOMS: Array[String] = ["C01", "C02", "C03", "H01", "H02", "P01", "P02"]

func _init() -> void:
	_test_rooms()
	_test_people()
	_test_shops()
	_test_side_bosses()
	print("Hub: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _rooms() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://content/rooms.json"))

func _test_rooms() -> void:
	var all: Dictionary = _rooms()
	for id: String in NEW_ROOMS:
		_check(all.has(id), id + " exists")
		var room: Dictionary = all[id]
		var wb: Array = room.walk_bounds
		var entry: Array = room.entry
		_check(float(entry[0]) >= float(wb[0]) and float(entry[0]) <= float(wb[0]) + float(wb[2]) and float(entry[1]) >= float(wb[1]) and float(entry[1]) <= float(wb[1]) + float(wb[3]), id + " entry is on the walkable band")
		_check(ResourceLoader.exists("res://assets/art/rooms/%s/background.png" % id), id + " has its painted background")
		var seen: Dictionary = {}
		for o: Dictionary in room.objects:
			_check(not seen.has(str(o.id)), id + " has one " + str(o.id))
			seen[str(o.id)] = true
			_check(float(o.x) >= 0 and float(o.x) <= float(room.dimensions[0]) and float(o.y) >= 0 and float(o.y) <= float(room.dimensions[1]), id + "/" + str(o.id) + " is inside the room")
			if str(o.kind) in ["talk", "inspect", "save"]: _check(o.has("lines") and not o.lines.is_empty(), id + "/" + str(o.id) + " has something to say")
			if str(o.kind) == "talk" and o.has("sprite"):
				var art: String = str(o.sprite).trim_prefix("npc-")
				_check(NativeBossArt.encounter_cast(art) or NativeCastArt.IDS.has(art), id + "/" + str(o.id) + " sprite " + art + " is drawn")
			for line: Array in o.get("lines", []): _check(not "—" in str(line[1]), id + "/" + str(o.id) + " has no em-dashes")
	# Every door in or out of the new rooms lands on walkable ground, and has a way back.
	var back: Dictionary = {}
	for id: String in all:
		for o: Dictionary in all[id].objects:
			if str(o.kind) != "door": continue
			back[id + ">" + str(o.to)] = true
			_check(all.has(str(o.to)), id + "/" + str(o.id) + " leads to a real room")
			if not all.has(str(o.to)): continue
			var target: Dictionary = all[str(o.to)]
			var wb: Array = target.walk_bounds
			var at: Array = o.spawn
			if NEW_ROOMS.has(id) or NEW_ROOMS.has(str(o.to)):
				_check(float(at[0]) >= float(wb[0]) - 4.0 and float(at[0]) <= float(wb[0]) + float(wb[2]) + 4.0 and float(at[1]) >= float(wb[1]) - 4.0 and float(at[1]) <= float(wb[1]) + float(wb[3]) + 4.0, id + "/" + str(o.id) + " spawn " + str(at) + " is walkable in " + str(o.to))
	for id: String in NEW_ROOMS:
		for o: Dictionary in all[id].objects:
			if str(o.kind) == "door": _check(back.has(str(o.to) + ">" + id), id + " to " + str(o.to) + " has a door back")
	for id: String in ["C01", "H01"]:
		_check(all[id].has("wander") and not all[id].wander.is_empty(), id + " rolls wandering fights")
	_check(str(all.D03.objects.filter(func(o: Dictionary) -> bool: return str(o.id) == "front_doors")[0].to) == "C01", "The dorm's front doors open onto the court")

func _test_people() -> void:
	for id: String in ["tanner", "kyle"]:
		_check(NativeBossArt.drawn(id) and NativeBossArt.encounter_cast(id), id + " has a drawn sheet")
		_check(NativeBossIntro.has_card(id), id + " has a gym-leader card")
		_check(NativeBossIntro.ANSWERS.has(id), id + " answers CONNECT")
		_check(BattleRules.ENEMY_DAMAGE.has(id), id + " has a damage value")
	for who: String in NativeCastArt.ENCOUNTER_SPEAKERS:
		_check(NativeBossArt.drawn(str(NativeCastArt.ENCOUNTER_SPEAKERS[who])), who + " has a portrait sheet")

func _test_shops() -> void:
	var all: Dictionary = _rooms()
	for shop: String in NativeShops.SHOPS:
		var found: bool = false
		for room: String in all:
			for o: Dictionary in all[room].objects:
				if str(o.id) == shop: found = true
		_check(found, shop + " is a real object in a room")
		for entry: Dictionary in NativeShops.SHOPS[shop].stock:
			_check(int(entry.price) > 0, shop + " charges something")
			_check((entry.has("item") and NativeShops.SUPPLIES.has(str(entry.item))) or (entry.has("keepsake") and PartyGrowth.KEEPSAKES.has(str(entry.keepsake)) and bool(PartyGrowth.KEEPSAKES[str(entry.keepsake)].get("shop", false))), shop + " sells something real")
	var state: Dictionary = NativeState.fresh()
	state.flags.buff_bucks = "100"
	var granola: Dictionary = {"item": "granola", "price": 8}
	var before: int = int(state.inventory.granola)
	var sale: Dictionary = NativeShops.buy(state, granola)
	_check(bool(sale.ok) and NativeRandomFights.bucks(state.flags) == 92 and int(state.inventory.granola) == before + 1, "A supply costs Buff Bucks and lands in the pack")
	_check(NativeSaveService.validate_state(state), "The state still saves after a purchase")
	for i: int in range(10): NativeShops.buy(state, granola)
	_check(NativeShops.pack_total(state.inventory) <= NativeShops.PACK_LIMIT, "The pack never goes over its limit")
	var refused: Dictionary = NativeShops.buy(state, granola)
	_check(not bool(refused.ok) and "full" in str(refused.text), "A full pack refuses the sale")
	var broke: Dictionary = NativeState.fresh()
	_check(not bool(NativeShops.buy(broke, {"item": "cocoa", "price": 10}).ok), "No Buff Bucks, no sale")
	var hoodie: Dictionary = {"keepsake": "buffs_hoodie", "price": 60}
	var rich: Dictionary = NativeState.fresh()
	rich.flags.buff_bucks = "200"
	_check(bool(NativeShops.buy(rich, hoodie).ok) and PartyGrowth.found(rich.flags, "buffs_hoodie") and PartyGrowth.equipped(rich.flags, "jules") == "buffs_hoodie", "A keepsake is bought and worn when the slot is empty")
	_check(NativeRandomFights.bucks(rich.flags) == 140 and not bool(NativeShops.buy(rich, hoodie).ok) and NativeRandomFights.bucks(rich.flags) == 140, "A keepsake can be bought once, and the second try costs nothing")
	_check(NativeSaveService.validate_state(rich), "The state still saves after a keepsake")
	_check(PartyGrowth.stats("jules", rich.flags).max == PartyGrowth.stats("jules", {}).max + 10, "The hoodie adds 10 max HP")
	_check(NativeShops.stock({}, "register").size() == 1 and NativeShops.stock({"imani_joined": true, "walt_joined": true}, "register").size() == 3, "The register only offers gear for friends who are with you")

func _test_side_bosses() -> void:
	for id: String in NativeSideBosses.BOSSES:
		var e: Dictionary = NativeSideBosses.BOSSES[id]
		_check(int(e.hp) >= 100 and int(e.hp) <= 200, id + " has a mini-boss HP pool")
		_check(e.connect.size() == 3 and e.intro.size() >= 3 and e.peaceful.size() >= 2 and e.forceful.size() >= 2, id + " has all its lines")
		for key: String in ["intro", "peaceful", "forceful", "done_peaceful", "done_forceful"]:
			for line: Array in e[key]: _check(not "—" in str(line[1]), id + " " + key + " has no em-dashes")
		_check(DodgeBox.handles(id), id + " has a dodge script")
		_check(_rooms()[str(e.room)].objects.any(func(o: Dictionary) -> bool: return str(o.id) == id), id + " stands in " + str(e.room))
		var state: Dictionary = NativeState.fresh()
		var r: RandomNumberGenerator = RandomNumberGenerator.new()
		r.seed = 7
		var won: Dictionary = NativeSideBosses.reward(state, id, true, r)
		r.seed = 7
		var lesser: Dictionary = NativeSideBosses.reward(NativeState.fresh(), id, false, r)
		_check(int(won.gain) >= int(e.bucks[0]) and int(won.gain) <= int(e.bucks[1]) and int(lesser.gain) < int(won.gain), id + " pays more for the peaceful way")
		_check(NativeSaveService.validate_state(state), id + " reward still saves")
	# The peaceful ending sends a LinkedOut request, the forceful one a profile view.
	var flags: Dictionary = {"tanner_resolution": "peaceful", "kyle_resolution": "forceful"}
	_check(LinkedOut.person("tanner").name == "Tanner" and LinkedOut.unlocked(flags, LinkedOut.person("tanner")) and not LinkedOut.unlocked(flags, LinkedOut.person("kyle")), "Tanner connects after a peaceful ending, Kyle does not after a forceful one")
