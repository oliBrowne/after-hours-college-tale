class_name NativeRandomFights
extends RefCounted
## Wandering fights: small, low-key encounters with people on campus paths (a cyclist late for a
## 9 AM, a hacky-sack circle, a business major with a brand). They are not story bosses: no intro
## card, short HP, a short dodge script each (core/dodge_patterns_rf_<name>.gd), and the same two ways
## out as every fight. Both pay Buff Bucks, the campus currency, the peaceful way a little more.
## Rooms opt in with a "wander" dict in content/rooms.json: {fight id: weight}. A walk-distance
## counter rolls a fight roughly every minute of walking, never during story scenes, right after
## arriving, next to something you can press, or before the first story fight is behind you.
## Flags (saves only keep bool and String flags, so the counts are stored as strings): buff_bucks,
## wander_wins, wander_rolls (makes the dice deterministic),
## wander_off (player switch in Settings), sunbeam_met.
## Art: NativeBossArt id in "art" when its sheet exists, else the "stand_in" cast sprite.
const BASE_GOAL: float = 3600.0
const GOAL_SPREAD: float = 2400.0
const QUIET_NEAR: float = 72.0
const GRACE: int = 360
const FIGHTS: Dictionary = {
	"rf_cyclist": {"name": "Commuter Cyclist", "art": "cyclist", "stand_in": "eli", "hp": 30, "bucks": [6, 10],
		"intro": "ON YOUR LEFT! ...your other left! Sorry, sorry, I have a nine o'clock and a very strong opinion about this bike lane.",
		"connect": ["Ask where the bell is from", "Share the path", "Walk the bike across"],
		"peaceful": "Okay. Bell off, helmet on. I'll walk it across the crosswalk like a person. Don't tell the other cyclists.",
		"forceful": "Ow! Okay, okay! Walking the bike! Do you know how many bikes get stolen here?"},
	"rf_runner": {"name": "Altitude Runner", "art": "runner", "stand_in": "chip", "hp": 28, "bucks": [6, 10],
		"intro": "Not acclimated yet? It's a mental thing. I'm on mile eleven and I feel amazing. Please stop me.",
		"connect": ["Ask how far he's going", "Match his pace", "Walk the last stretch"],
		"peaceful": "Walking. I'm walking. Huh. The leaves are actually kind of nice from down here.",
		"forceful": "Okay. Okay! That's... that's a fair reason to stop. I'll go stretch."},
	"rf_hippie": {"name": "Hacky-Sack Hippie", "art": "hippie", "stand_in": "mara", "hp": 26, "bucks": [5, 9],
		"intro": "Dude. The sack has been in the air for forty minutes. It's a lifestyle, not a game. Wanna circle up?",
		"connect": ["Ask what the circle is for", "Keep the sack up", "Let the sack rest"],
		"peaceful": "That's the longest it's ever stayed up. Honestly? Beautiful. Keep the good vibes, friend.",
		"forceful": "Whoa. Violent vibes. Okay. I'm going to go sit in the shade and think about that."},
	"rf_business_major": {"name": "Business Major", "art": "business_major", "stand_in": "cal", "hp": 32, "bucks": [7, 11],
		"intro": "Hi! Quick question: do you have thirty seconds and a LinkedOut profile? I'm building a brand. The brand is me.",
		"connect": ["Ask what he's selling", "Take one card, then decline", "Say no thank you"],
		"peaceful": "Wow. A boundary. That's a transferable skill. Keep the card, it's laminated.",
		"forceful": "Okay, that's fair feedback. Please leave a review on the way out."},
	"rf_sunbeam": {"name": "Sunbeam", "art": "sunbeam", "stand_in": "walt", "hp": 60, "bucks": [30, 40], "rare": true,
		"intro": "Hey hey hey! Sunbeam, frontman of The Lost Waffles. We're doing a sunset set. The sunset started at two. Join the jam?",
		"connect": ["Ask what the band plays", "Join the jam", "Let the set end"],
		"peaceful": "That's the best crowd we've ever had, and it was three people and a bus. The sun's on you, friend.",
		"forceful": "Whoa, heavy riff. Okay. I'm going to take this as feedback for the second verse."},
}
## Items a win can leave behind (about one in four).
const DROPS: Array[String] = ["granola", "granola", "cocoa"]

static func is_fight(id: String) -> bool:
	return FIGHTS.has(id)

static func name_of(id: String) -> String:
	return str(FIGHTS[id].name) if FIGHTS.has(id) else ""

static func count(flags: Dictionary, key: String) -> int:
	return int(str(flags.get(key, "0")))

static func bucks(flags: Dictionary) -> int:
	return count(flags, "buff_bucks")

static func hp(id: String) -> int:
	return int(FIGHTS[id].hp)

static func connect_labels(id: String) -> Array:
	return FIGHTS[id].connect

# ---------------------------------------------------------------- art

static func frames(id: String) -> SpriteFrames:
	var e: Dictionary = FIGHTS[id]
	var art: String = str(e.art)
	if NativeBossArt.drawn(art): return NativeBossArt.frames(art)
	return NativeCastArt.frames(str(e.stand_in))

## Called by begin_battle after its own foe setup: this fight's HP, sprite and pose.
static func setup(g: Node) -> void:
	var id: String = str(g.boss_id)
	g.battle.hp = hp(id)
	g.foe.sprite_frames = frames(id)
	g.foe.play("idle_down")

# ---------------------------------------------------------------- when a fight starts

static func active_room(g: Node) -> Dictionary:
	var room: Dictionary = g.rooms.get(str(g.state.room), {})
	return room.get("wander", {})

## Whether wandering fights may start right now, wherever Jules is.
static func allowed(g: Node) -> bool:
	var f: Dictionary = g.state.flags
	# The story QA routes walk these rooms on a fixed clock; only --qa-wander lets fights start.
	if bool(g.qa) and not "--qa-wander" in OS.get_cmdline_user_args(): return false
	if bool(f.get("wander_off", false)) or active_room(g).is_empty(): return false
	# After the first story fight, outside the dorm prologue, with nothing half-finished.
	if not f.has("flyer_resolution") or bool(f.get("movein_active", false)): return false
	if str(f.get("aftermath_pending", "")) != "" or str(g.boss_id) != "": return false
	if int(g.mode) != int(g.Mode.WORLD) or int(g.grace_ticks) > 0 or g.arrival_point != Vector2.INF: return false
	return true

## True when something Jules can press (a door, a person, a prop) is close enough that a fight
## would feel like an ambush.
static func near_something(g: Node) -> bool:
	for o: Dictionary in g.rooms[str(g.state.room)].objects:
		if g.player.position.distance_to(Vector2(float(o.x), float(o.y))) < QUIET_NEAR: return true
	return false

static var walked: float = 0.0
static var goal: float = 0.0

static func rng(g: Node) -> RandomNumberGenerator:
	var r: RandomNumberGenerator = RandomNumberGenerator.new()
	r.seed = int(g.state.get("seed", 271828)) + 7919 * count(g.state.flags, "wander_rolls")
	return r

## Which fight, from this room's weighted list.
static func pick(g: Node) -> String:
	var table: Dictionary = active_room(g)
	var total: float = 0.0
	for id: String in table: total += float(table[id])
	var r: RandomNumberGenerator = rng(g)
	var roll: float = r.randf() * total
	for id: String in table:
		roll -= float(table[id])
		if roll <= 0.0: return id
	return str(table.keys()[0])

static func next_goal(g: Node) -> float:
	return BASE_GOAL + rng(g).randf() * GOAL_SPREAD

static func reset(g: Node) -> void:
	walked = 0.0
	goal = next_goal(g)

## Called every walking tick from world_tick; returns true when a fight just started.
static func step(g: Node, moved: float) -> bool:
	if moved <= 0.0 or not allowed(g): return false
	if goal <= 0.0: goal = next_goal(g)
	walked += moved
	if walked < goal or near_something(g): return false
	return begin(g, pick(g))

## Forces the next roll to fire (QA and the test).
static func force(g: Node) -> void:
	goal = 1.0
	walked = 1.0

static func begin(g: Node, id: String) -> bool:
	if not FIGHTS.has(id): return false
	var e: Dictionary = FIGHTS[id]
	g.state.flags.wander_rolls = str(count(g.state.flags, "wander_rolls") + 1)
	if id == "rf_sunbeam": g.state.flags.sunbeam_met = true
	reset(g)
	g.reset_pointer_controls()
	g.dialogue([[str(e.name), str(e.intro), "neutral"]], func() -> void:
		g.boss_id = id
		g.start_battle())
	return true

# ---------------------------------------------------------------- when it ends

## Buff Bucks for a win: the full roll when peaceful, three fifths when not.
static func payout(id: String, peaceful: bool, r: RandomNumberGenerator) -> int:
	var range_: Array = FIGHTS[id].bucks
	var base: int = r.randi_range(int(range_[0]), int(range_[1]))
	return base if peaceful else maxi(1, roundi(float(base) * 0.6))

## Adds one supply if the pack has room (a save holds at most 8 in total).
static func add_item(inventory: Dictionary, item: String) -> bool:
	var total: int = 0
	for key: String in inventory: total += int(inventory[key])
	if total >= 8 or not inventory.has(item): return false
	inventory[item] = int(inventory[item]) + 1
	return true

## Pays Buff Bucks, counts the win and maybe leaves a snack; returns {"gain", "item"}.
static func reward(state: Dictionary, id: String, peaceful: bool, r: RandomNumberGenerator) -> Dictionary:
	var gain: int = payout(id, peaceful, r)
	var item: String = ""
	if bool(FIGHTS[id].get("rare", false)) or r.randi_range(0, 3) == 0:
		var drop: String = DROPS[r.randi_range(0, DROPS.size() - 1)]
		if add_item(state.inventory, drop): item = drop
	var f: Dictionary = state.flags
	f.buff_bucks = str(bucks(f) + gain)
	f.wander_wins = str(count(f, "wander_wins") + 1)
	return {"gain": gain, "item": item}

static func finish(g: Node) -> void:
	g.reset_pointer_controls()
	var id: String = str(g.boss_id)
	g.merge_party(BattleRules.recover(g.battle.party))
	g.state.inventory = g.battle.inventory.duplicate(true)
	var peaceful: bool = g.battle.outcome == "peaceful"
	var won: Dictionary = reward(g.state, id, peaceful, rng(g))
	g.persist()
	g.vfx.play("promise" if peaceful else "dissolve", g.foe.position, g.foe.position - Vector2(0, 35))
	g.audio.resolve_battle(peaceful)
	g.open_menu(g.Mode.RESULT, "A promise kept" if peaceful else "The way is clear", [g.option("Continue", func() -> void:aftermath(g, id, peaceful, int(won.gain), str(won.item)))])

static func aftermath(g: Node, id: String, peaceful: bool, gain: int, item: String) -> void:
	var e: Dictionary = FIGHTS[id]
	g.boss_id = ""
	g.enter_room(str(g.state.room), Vector2(float(g.state.x), float(g.state.y)), false)
	g.grace_ticks = GRACE
	g.dialogue([[str(e.name), str(e.peaceful if peaceful else e.forceful), "warm" if peaceful else "concern"]], func() -> void:
		g.message(summary(gain, item))
		g.resume_world())

static func summary(gain: int, item: String) -> String:
	var text: String = "+%d Buff Bucks" % gain
	if not item.is_empty(): text += " and a %s" % item
	return text
