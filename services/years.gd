class_name NativeYears
extends RefCounted
## The four years. The story is paced across freshman, sophomore, junior and senior year, and each
## year ends at a milestone fight, so the party grows one person at a time:
##   1 FRESHMAN (fall)    move-in, the mixer, the Flyerer. Jules is alone.
##   2 SOPHOMORE (winter) the booth plays Imani's voice and she joins; the atrium booth, upstairs.
##   3 JUNIOR (spring)    Walt, Cal's key, Advisor Bev.
##   4 SENIOR (winter)    Farrand, the library, Old Main and the Last Light night.
## The year is derived from story flags (nothing new is saved); a title card plays the first time
## it changes while someone is playing, and the season art follows it.
const CARDS: Dictionary = {
	1: ["FRESHMAN YEAR / FALL", "The Flatirons keep the sunset a little longer than the streets."],
	2: ["SOPHOMORE YEAR / WINTER", "Snow on the Flatirons. The hum from the UMC atrium has learned a name."],
	3: ["JUNIOR YEAR / SPRING", "Petals in the gutters, a lantern under Broadway, a radio that will not stop."],
	4: ["SENIOR YEAR / LAST LIGHT", "Four years in. The night before graduation, everything unfinished is still on campus."],
}
const SEASONS: Dictionary = {1: "fall", 2: "winter", 3: "spring", 4: "winter"}
static var for_state: Variant = null
static var seen: int = 0

static func year(f: Dictionary) -> int:
	if f.has("claim_resolution"): return 4
	if f.get("booth_seen", false): return 3
	if f.has("flyer_resolution"): return 2
	return 1

static func season(f: Dictionary, room: String) -> String:
	if bool(f.get("movein_active", false)): return "fall"
	if str(f.get("dawn_talk_read", "")) != "" or room in ["M07", "G01", "G02"]: return "spring"
	return str(SEASONS[year(f)])

## Drops lines from Imani, Walt and Pip while they have not joined.
static func present(lines: Array, f: Dictionary) -> Array:
	return lines.filter(func(l: Array) -> bool:
		var who: String = str(l[0])
		return not (who in ["Imani", "Walt", "Pip"]) or bool(f.get(who.to_lower() + "_joined", false)))

## Called every world tick: the card for a new year, once the dust of the last fight has settled.
static func step(g: Node) -> bool:
	var f: Dictionary = g.state.flags
	if not is_same(for_state, g.state):
		for_state = g.state; seen = year(f)
		return false
	var now: int = year(f)
	if now <= seen or g.mode != g.Mode.WORLD or g.transition_ticks > 0 or NativeRoomScenes.busy() or str(f.get("aftermath_pending", "")) != "" or str(g.boss_id) != "": return false
	seen = now
	g.reset_pointer_controls()
	g.player.walk(Vector2.ZERO, false, 0.0)
	g.intro_cards = [CARDS[now]]; g.intro_arrival = -1
	g.intro_after = func() -> void:
		g.world.visible = true; g.backdrop.visible = false
		g.enter_room(str(g.state.room), Vector2(float(g.state.x), float(g.state.y)), false)
		g.persist(); g.resume_world()
	g.world.visible = false; g.backdrop.visible = true
	g.intro_index = 0; g.intro_ticks = 0; g.mode = g.Mode.INTRO; g.ui_dirty = true
	return true
