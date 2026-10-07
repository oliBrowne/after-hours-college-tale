class_name PartyGrowth
extends RefCounted
## Deltarune-style growth. No EXP: stats come from fixed story milestones, the
## same on peaceful and forceful routes, plus one equipped keepsake per member.
## Stats are derived from flags every refresh, so old saves catch up and
## nothing can double-apply. Pure functions; callers own the returned state.

const MEMBERS: Array[String] = ["jules", "imani", "walt"]
const MILESTONES: Array[String] = ["claim_resolution", "chapter1_complete", "chapter2_complete", "chapter3_complete"]
## [max HP, power, defence] at the start and after each milestone.
const TABLE: Dictionary = {
	"jules": [[84, 14, 2], [96, 16, 2], [110, 18, 3], [124, 20, 3], [140, 22, 4]],
	"imani": [[72, 10, 1], [82, 12, 1], [94, 14, 2], [106, 16, 2], [120, 18, 3]],
	"walt": [[96, 12, 3], [108, 14, 3], [122, 16, 4], [136, 18, 4], [152, 20, 5]],
}
## One slot per member. Found = flag "keepsake_<id>"; equipped = flag "keepsake_<member>" holding an id.
const KEEPSAKES: Dictionary = {
	"bus_pass": {"member": "jules", "name": "Bus pass", "stat": "defence", "amount": 1, "room": "U01", "x": 52, "y": 204, "lines": [["Jules", "My bus pass. It slipped out of the mixer bag. Still good until midnight.", "warm"]]},
	"guitar_pick": {"member": "imani", "name": "Guitar pick", "stat": "power", "amount": 2, "room": "U04", "x": 60, "y": 320, "lines": [["Imani", "My lucky pick! I was sure the flyer stand ate it.", "warm"]]},
	"lantern_wick": {"member": "walt", "name": "Spare lantern wick", "stat": "defence", "amount": 1, "room": "U05", "x": 580, "y": 264, "lines": [["Walt", "A spare wick. Cal leaves one on every landing. I'll carry it.", "neutral"]]},
	"moms_keychain": {"member": "jules", "name": "Mom's keychain", "stat": "power", "amount": 2, "room": "U07", "x": 60, "y": 322, "lines": [["Jules", "Mom's spare keychain. I lost this in September. Somebody turned it in.", "warm"]]},
	"setlist": {"member": "imani", "name": "Setlist", "stat": "sync", "amount": 10, "room": "F05", "x": 748, "y": 294, "lines": [["Imani", "My setlist, taped to an amp. One song circled. Just one.", "warm"]]},
	"thermos_lid": {"member": "walt", "name": "Thermos lid", "stat": "max", "amount": 12, "room": "F03", "x": 748, "y": 302, "lines": [["Walt", "A thermos lid. Mine went missing years ago. Close enough.", "warm"]]},
	"earplugs": {"member": "imani", "name": "Earplugs", "stat": "defence", "amount": 1, "room": "N03", "x": 60, "y": 334, "lines": [["Imani", "Foam earplugs. Quiet is allowed.", "neutral"]]},
	"trail_map": {"member": "walt", "name": "Trail map", "stat": "power", "amount": 2, "room": "N05", "x": 60, "y": 318, "lines": [["Walt", "An old trail map. Every path on it ends somewhere. Good.", "warm"]]},
	"night_lanyard": {"member": "jules", "name": "Night-shift lanyard", "stat": "max", "amount": 8, "room": "E02", "x": 748, "y": 326, "lines": [["Jules", "A night-shift lanyard. Dev says it's for whoever stays late. Tonight that's me.", "neutral"]]},
}
## What each keepsake does besides its stat (read where the effect happens: main.gd and battle_rules.gd).
const PERKS: Dictionary = {"bus_pass": "Blocks the first hit of each fight", "moms_keychain": "Wider STRIKE timing for Jules", "guitar_pick": "Close dodges on the beat give double SYNC", "earplugs": "Half Time costs 10 less SYNC", "lantern_wick": "Lantern Ward's safe pocket lasts longer", "thermos_lid": "Share the Warmth heals 12 more"}
const STAT_TEXT: Dictionary = {"defence": "+%d defence", "power": "+%d power", "max": "+%d max HP", "sync": "+%d SYNC at battle start"}

static func milestones(flags: Dictionary) -> int:
	var count: int = 0
	for flag: String in MILESTONES:
		var value: Variant = flags.get(flag, false)
		if (value is bool and value) or (value is String and not str(value).is_empty()): count += 1
	return count

static func found(flags: Dictionary, id: String) -> bool:
	return KEEPSAKES.has(id) and bool(flags.get("keepsake_" + id, false))

static func owned(flags: Dictionary, member: String) -> Array[String]:
	var ids: Array[String] = []
	for id: String in KEEPSAKES:
		if KEEPSAKES[id].member == member and found(flags, id): ids.append(id)
	return ids

static func equipped(flags: Dictionary, member: String) -> String:
	var id: String = str(flags.get("keepsake_" + member, ""))
	return id if found(flags, id) and KEEPSAKES[id].member == member else ""

static func describe(id: String) -> String:
	var keepsake: Dictionary = KEEPSAKES[id]
	return str(keepsake.name) + " / " + str(STAT_TEXT[keepsake.stat]) % int(keepsake.amount)

static func stats(member: String, flags: Dictionary) -> Dictionary:
	var row: Array = TABLE[member][mini(milestones(flags), TABLE[member].size() - 1)]
	var result: Dictionary = {"max": int(row[0]), "power": int(row[1]), "defence": int(row[2]), "sync": 0}
	var id: String = equipped(flags, member)
	if not id.is_empty(): result[KEEPSAKES[id].stat] = int(result[KEEPSAKES[id].stat]) + int(KEEPSAKES[id].amount)
	return result

## Returns the party with derived max/power/defence. When heal is true (a new
## milestone) a higher max heals by the gain, as a level-up does; swapping a
## keepsake passes false so it can never be cycled for free HP. HP is always
## clamped to the new max.
static func apply(party: Array, flags: Dictionary, heal: bool = true) -> Array:
	var grown: Array = party.duplicate(true)
	for member: Dictionary in grown:
		if not TABLE.has(str(member.get("id", ""))): continue
		var derived: Dictionary = stats(str(member.id), flags)
		var gain: int = maxi(0, int(derived.max) - int(member.get("max", derived.max))) if heal else 0
		member.max = int(derived.max)
		member.power = int(derived.power)
		member.defence = int(derived.defence)
		member.hp = clampi(int(member.get("hp", derived.max)) + gain, 0, int(derived.max))
	return grown

## SYNC a battle starts with on top of the base 20, from equipped keepsakes of joined members.
## True when a joined member is wearing this keepsake.
static func has_perk(flags: Dictionary, id: String) -> bool:
	if not KEEPSAKES.has(id): return false
	var member: String = str(KEEPSAKES[id].member)
	return (member == "jules" or bool(flags.get(member + "_joined", false))) and equipped(flags, member) == id

static func starting_sync(flags: Dictionary) -> int:
	var bonus: int = 0
	for member: String in MEMBERS:
		if member != "jules" and not bool(flags.get(member + "_joined", false)): continue
		bonus += int(stats(member, flags).sync)
	return bonus
