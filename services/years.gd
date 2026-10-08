class_name NativeYears
extends RefCounted
## The four years. The story is paced across freshman, sophomore, junior and senior year, with a
## title card at each milestone, so the party grows one person at a time:
##   stage 1  FRESHMAN, fall            move-in, the mixer, the Flyerer. Jules is alone.
##   stage 2  FRESHMAN, spring term     (after the Flyerer) the booth plays Imani's voice and she joins,
##                                      halfway through the year; the atrium booth ends freshman year.
##   stage 3  SOPHOMORE, fall           Walt joins (the bridge, the lantern), then Cal's key.
##   stage 4  JUNIOR, winter            lost property upstairs, Pin Pal, Advisor Bev.
##   stage 5  SENIOR, the Last Light    Farrand, the library, Old Main and the finale.
## The stage is derived from story flags (nothing new is saved); a title card plays the first time
## it changes while someone is playing, and the season art follows it.
const CARDS: Dictionary = {
	1: ["FRESHMAN YEAR / FALL", "The Flatirons keep the sunset a little longer than the streets."],
	2: ["FRESHMAN YEAR / SPRING TERM", "Early snow on the Flatirons. The hum from the UMC atrium has learned a name."],
	3: ["SOPHOMORE YEAR / FALL", "Red leaves on Broadway, a lantern under the bridge, a radio that will not stop."],
	4: ["JUNIOR YEAR / WINTER", "Snow again. Every office upstairs wants one more form."],
	5: ["SENIOR YEAR / LAST LIGHT", "Four years in. The night before graduation, everything unfinished is still on campus."],
}
const SEASONS: Dictionary = {1: "fall", 2: "winter", 3: "fall", 4: "winter", 5: "winter"}
const YEARS: Dictionary = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4}
static var for_state: Variant = null
static var seen: int = 0

## The four-year title cards ("FRESHMAN YEAR / FALL"), drawn full screen instead of in the story box.
static func is_card(title: String) -> bool:
	return title.begins_with("FRESHMAN YEAR") or title.begins_with("SOPHOMORE YEAR") or title.begins_with("JUNIOR YEAR") or title.begins_with("SENIOR YEAR")

## Accent colour of a year card: red-gold in fall, ice blue in winter, blossom in spring, amber for the Last Light.
static func card_colour(title: String) -> Color:
	if title.contains("LAST LIGHT"): return Color("e8b45c")
	if title.contains("WINTER") or title.contains("SPRING TERM"): return Color("9ab8e8")
	if title.contains("SPRING"): return Color("f0a8c8")
	return Color("e08a4a")

static func stage(f: Dictionary) -> int:
	if f.has("claim_resolution"): return 5
	if f.get("cal_key_received", false): return 4
	if f.get("booth_seen", false): return 3
	if f.has("flyer_resolution"): return 2
	return 1

## 1 freshman, 2 sophomore, 3 junior, 4 senior.
static func year(f: Dictionary) -> int:
	return int(YEARS[stage(f)])

static func season(f: Dictionary, room: String) -> String:
	if bool(f.get("movein_active", false)): return "fall"
	if str(f.get("dawn_talk_read", "")) != "" or room in ["M07", "G01", "G02"]: return "spring"
	return str(SEASONS[stage(f)])

## Drops lines from Imani, Walt and Pip while they have not joined.
static func present(lines: Array, f: Dictionary) -> Array:
	return lines.filter(func(l: Array) -> bool:
		var who: String = str(l[0])
		return not (who in ["Imani", "Walt", "Pip"]) or bool(f.get(who.to_lower() + "_joined", false)))

## Called every world tick: the card for a new year, once the dust of the last fight has settled.
static func step(g: Node) -> bool:
	var f: Dictionary = g.state.flags
	if not is_same(for_state, g.state):
		for_state = g.state; seen = stage(f)
		return false
	var now: int = stage(f)
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
