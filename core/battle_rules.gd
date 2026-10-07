class_name BattleRules
extends RefCounted
## Pure battle rules. All returned state is independent of the caller's state.
## Timing is accuracy 0..1; negative misses; default 1/3 gives a 1.0 multiplier.

static func initial_party() -> Array[Dictionary]:
	return [{"id": "jules", "hp": 84, "max": 84, "power": 14, "defence": 2}, {"id": "imani", "hp": 72, "max": 72, "power": 10, "defence": 1}, {"id": "walt", "hp": 96, "max": 96, "power": 12, "defence": 3}]

static func create_battle(party: Array = [], inventory: Dictionary = {}) -> Dictionary:
	var members: Array = initial_party() if party.is_empty() else party.duplicate(true)
	var supplies: Dictionary = {"granola": 2, "cocoa": 1, "thermos": 1} if inventory.is_empty() else inventory.duplicate(true)
	return {"party": members, "hp": 48, "openness": 0, "sync": 20, "inventory": supplies, "guards": [false, false, false], "shield": false, "brace": false, "slow": false, "promise": false, "outcome": "active", "turn": 0}

static func _cost(command: Dictionary) -> int:
	if command.has("joint"):
		return 35
	return int({"shield": 20, "heal": 30, "slow": 30, "brace": 20, "lantern": 25, "windbreak": 20, "warmth": 30}.get(command.get("kind", ""), 0)) - int(command.get("discount", 0))

static func _priority(command: Dictionary) -> int:
	if command.get("kind", "") == "guard":
		return 0
	return 1 if command.has("joint") else 2

static func _ordered(commands: Array) -> Array:
	var ordered: Array = commands.duplicate(true)
	ordered.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var pa: int = _priority(a)
		var pb: int = _priority(b)
		return int(a.actor) < int(b.actor) if pa == pb else pa < pb)
	return ordered

static func validate_plan(battle: Dictionary, commands: Array) -> String:
	if battle.outcome != "active":
		return "Encounter has ended."
	var party: Array = battle.party
	if not _conscious(party):
		return "No conscious actor."
	var guard_count: int = 0
	for value: Variant in commands:
		if not value is Dictionary:
			return "Invalid command."
		var command: Dictionary = value
		if command.get("kind", "") == "guard":
			guard_count += 1
	var budget: int = mini(100, int(battle.sync) + guard_count * 12)
	var items: Dictionary = battle.inventory.duplicate(true)
	var used: Dictionary = {}
	var promises: int = 0
	for command: Dictionary in commands:
		if typeof(command.get("actor")) != TYPE_INT:
			return "Actor is unavailable."
		var actor: int = command.actor
		var kind: String = str(command.get("kind", ""))
		if actor < 0 or actor >= party.size() or int(party[actor].hp) <= 0:
			return "Actor is unavailable."
		if used.has(actor):
			return "A party member has already committed their turn."
		used[actor] = true
		if not kind in ["strike", "connect", "promise", "release", "guard", "shield", "heal", "slow", "brace", "item", "lantern", "windbreak", "warmth"]:
			return "Unknown command."
		if command.has("joint"):
			if command.joint != "hearMeOut" or kind != "connect" or actor != 0 or party.size() < 2 or int(party[1].hp) <= 0 or used.has(1):
				return "Hear Me Out requires Jules and Imani."
			used[1] = true
		var member: Dictionary = party[actor]
		if (kind == "shield" and member.id != "jules") or (kind in ["heal", "slow"] and member.id != "imani") or (kind == "brace" and member.id not in ["walt", "cal"]):
			return "This talent belongs to another party member."
		var item: String = str(command.get("item", "granola"))
		if kind in ["lantern", "windbreak", "warmth"] and member.id != "walt": return "This talent belongs to Walt."
		if kind in ["heal", "windbreak", "warmth"] or (kind == "item" and item != "cocoa"):
			if typeof(command.get("target")) != TYPE_INT:
				return "Choose a valid ally."
			var target: int = command.target
			if target < 0 or target >= party.size():
				return "Choose a valid ally."
		if kind == "promise":
			promises += 1
			if promises > 1:
				return "Only one promise can be active in a phase."
		budget -= _cost(command)
		if budget < 0:
			return "Not enough projected SYNC."
		if kind == "item":
			if not items.has(item):
				return "That item is unavailable."
			items[item] = int(items[item]) - 1
			if int(items[item]) < 0:
				return "That item is unavailable."
		if command.has("timing") and (not command.timing is float and not command.timing is int):
			return "Timing must be finite."
		if command.has("timing") and not is_finite(float(command.timing)):
			return "Timing must be finite."
	var openness: int = int(battle.openness)
	for command: Dictionary in _ordered(commands):
		if command.kind == "connect":
			openness = mini(100, openness + (50 if command.has("joint") else 25))
		if command.kind == "release" and openness < 100:
			return "RELEASE needs 100 Openness."
	return ""

static func _conscious(party: Array) -> bool:
	for member: Dictionary in party:
		if int(member.hp) > 0:
			return true
	return false

static func _heal(battle: Dictionary, target: int, amount: int) -> void:
	var member: Dictionary = battle.party[target]
	member.hp = mini(int(member.max), int(member.hp) + amount)

static func resolve_plan(before: Dictionary, commands: Array) -> Dictionary:
	var battle: Dictionary = before.duplicate(true)
	var error: String = validate_plan(before, commands)
	if not error.is_empty():
		push_error(error)
		return battle
	battle.guards = []
	for _member: Dictionary in battle.party:
		battle.guards.append(false)
	battle.shield = false
	battle.brace = false
	battle.slow = false
	battle.promise = false
	battle.ward = false; battle.windbreak_target = -1
	battle.turn = int(battle.turn) + 1
	for command: Dictionary in _ordered(commands):
		if battle.outcome != "active":
			break
		var actor: int = command.actor
		if int(battle.party[actor].hp) <= 0:
			continue
		battle.sync = int(battle.sync) - _cost(command)
		match str(command.kind):
			"guard":
				battle.guards[actor] = true
				battle.sync = mini(100, int(battle.sync) + 12)
			"shield": battle.shield = true
			"brace": battle.brace = true
			"lantern": battle.ward = true
			"windbreak": battle.windbreak_target = int(command.target)
			"warmth":
				_heal(battle, int(command.target), 22 + int(command.get("bonus", 0)))
				battle.guards[int(command.target)] = true
			"slow": battle.slow = true
			"heal": _heal(battle, int(command.target), 28)
			"item":
				var item: String = str(command.get("item", "granola"))
				battle.inventory[item] = int(battle.inventory[item]) - 1
				if item == "cocoa":
					for index: int in range(battle.party.size()):
						_heal(battle, index, 20)
				else:
					_heal(battle, int(command.target), 45 if item == "thermos" else 30)
			"connect": battle.openness = mini(100, int(battle.openness) + (50 if command.has("joint") else 25))
			"promise": battle.promise = true
			"release":
				battle.outcome = "peaceful"
				battle.promise = false
			"strike":
				var timing: float = float(command.get("timing", 1.0 / 3.0))
				var power: int = int(battle.party[actor].power)
				var damage: int = 1 if timing < 0.0 else maxi(1, roundi(power * (0.8 + 0.6 * minf(1.0, timing)) - 1.0))
				battle.hp = maxi(0, int(battle.hp) - damage)
				if int(battle.hp) == 0:
					battle.outcome = "forceful"
					battle.promise = false
	return battle

## Damage per enemy hit before defence. "" is the Flyerer. Opening bosses are
## gentle; each chapter's bosses hit harder as the party's story stats grow.
const ENEMY_DAMAGE: Dictionary = {"": 8, "jakerson": 3, "walt": 8, "pinpal": 8, "claim": 8, "deion": 8, "chip": 14, "encore": 14, "cone": 14, "errata": 18, "loadbearer": 18, "eric": 18, "index": 18, "chad": 18, "todd": 20, "rook": 22, "val": 24, "jakerson_final": 12}
const PROMISE_OPENNESS: int = 45

## A boss is desperate once Openness reaches 50 or its HP falls to half, so the
## end of a fight is the tense part on either route.
static func desperate(battle: Dictionary) -> bool:
	var max_hp: int = int(battle.get("max_hp", 0))
	return int(battle.get("openness", 0)) >= 50 or (max_hp > 0 and int(battle.get("hp", 0)) * 2 <= max_hp)

## A limit set with CONNECT (battle.eased) softens the next attack instead.
static func enemy_damage(boss_id: String, battle: Dictionary, assist: bool = false) -> int:
	var damage: float = float(ENEMY_DAMAGE.get(boss_id, 10))
	if bool(battle.get("eased", false)): damage *= 0.6
	elif desperate(battle): damage *= 1.25
	if assist: damage /= 2.0
	return ceili(damage)

static func hit(before: Dictionary, actor: int, damage: int = 10) -> Dictionary:
	var battle: Dictionary = before.duplicate(true)
	if battle.outcome != "active" or actor < 0 or actor >= battle.party.size() or int(battle.party[actor].hp) <= 0:
		return battle
	if battle.shield:
		battle.shield = false
		return battle
	var amount: int = maxi(1, damage - int(battle.party[actor].defence))
	if battle.guards[actor]:
		amount = ceili(amount / 2.0)
	if int(battle.get("windbreak_target", -1)) == actor: amount = maxi(1, ceili(amount * 0.6))
	if battle.brace:
		amount = maxi(1, ceili(amount * 0.75))
	battle.party[actor].hp = maxi(0, int(battle.party[actor].hp) - amount)
	if not _conscious(battle.party):
		battle.outcome = "defeat"
		battle.promise = false
	return battle

static func complete_promise(before: Dictionary, success: bool) -> Dictionary:
	var battle: Dictionary = before.duplicate(true)
	if battle.outcome == "active" and battle.promise and success:
		battle.openness = mini(100, int(battle.openness) + PROMISE_OPENNESS)
	battle.promise = false
	return battle

static func recover(party: Array) -> Array[Dictionary]:
	var recovered: Array[Dictionary] = []
	for value: Dictionary in party:
		var member: Dictionary = value.duplicate(true)
		member.hp = mini(int(member.max), int(member.hp) + ceili(int(member.max) * 0.2))
		recovered.append(member)
	return recovered
