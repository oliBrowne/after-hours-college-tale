class_name NativeMoveIn
extends RefCounted
## Move-in day: the short prologue four years before the Last Light night. Jules arrives in
## Farrand Hall room 214 (D01), meets Jakerson, the roommate nobody chose, learns to walk, read
## and use doors from him, wanders the hall (D02) and the lobby (D03), then takes his practice
## spar at the ping-pong table. He ends it with a bet: loser buys the boba, graduation day.
## Then "Four years later" and the evening begins at Broadway as before.
## Flags: movein_active (prologue running), movein_met (Jakerson has introduced himself),
## movein_ahead (Jules has left room 214, so Jakerson went ahead to the lobby),
## movein_done, movein_boba (taro | mango | biggest, paid off at graduation).
## Skipping the intro cards skips all of it, and saves from before this existed never see it.
const START: String = "D01"
const ENTRY: Vector2 = Vector2(80, 200)
const LOBBY: String = "D03"
const OBJECTIVE: String = "Meet Jakerson / Farrand Hall lobby"
const CARDS: Array = [
	["MOVE-IN DAY / FARRAND HALL", "Late August in Boulder. Every window on campus has a cardboard box in it."],
	["JULES NAVARRO / ROOM 214", "One blue mattress, three boxes, and a roommate nobody chose."],
]
const LATER: Array = ["FOUR YEARS LATER", "The night before graduation, the Flatirons look exactly the same."]
const BOBA: Dictionary = {
	"taro": "taro",
	"mango": "mango",
	"biggest": "the biggest cup on the menu",
}

static func active(g: Node) -> bool:return bool(g.state.flags.get("movein_active", false))

## What the evening's intro cards say after the dorm: "Four years later", then the usual three.
static func evening_cards(intro: Array) -> Array:
	return intro.duplicate()

## The world appears and Jakerson's introduction plays (a walk-in scene, see NativeRoomScenes).
static func begin(g: Node) -> void:
	g.state.flags.movein_active = true
	g.world.visible = true; g.backdrop.visible = false
	g.environment.set_arrival(1.0)
	g.persist(); g.resume_world()

# ---------------------------------------------------------------- the introduction

static func steps() -> Array:
	var walk: float = NativeRoomScenes.WALK
	return [["borrow", "jakerson", "jakerson"], ["wait", 50], ["face", "jakerson", "jules"],
		["say", [["Jakerson", "Oh! Hi! You must be Jules!", "warm"]]],
		["walk", [["jakerson", "jules", walk]]], ["face", "jakerson", "jules"], ["jules", "jakerson"],
		["say", [["Jakerson", "I'm Jakerson. Random assignment. Lucky us.", "warm"],
			["Jules", "Hi. Sorry, I'm still working out where everything goes. Is that your tennis racket on the wall?", "neutral"],
			["Jakerson", "Racket, trophy, laptop, and zero furniture sense. I moved in yesterday, so I took the window side. Is that okay? I can swap.", "warm"],
			["Jules", "The window is great. Honestly, I was just hoping my roommate wasn't a stranger who snores.", "warm"],
			["Jakerson", "Oh, I snore. But I made a list of roommate rules, so it evens out. Rule one: knock twice.", "warm"],
			["Jules", "Only twice?", "neutral"],
			["Jakerson", "Three is for emergencies and pizza. Rule two: look around before you ask me where anything is. {move} to walk, hold {run} to run.", "warm"],
			["Jakerson", "Walk up to anything and press {confirm} to look at it or talk to it. To use a door, stand on it and press {confirm}.", "warm"],
			["Jakerson", "Rule three: floor meeting is in the lobby at nine, and I need a witness for something first.", "warm"],
			["Jules", "A witness?", "concern"],
			["Jakerson", "You'll see. Unpack, poke around, then come find me downstairs. Hallway door, then the stairs.", "warm"]]],
		["walk", [["jakerson", Vector2(470, 272), walk]]], ["face", "jakerson", "jules"],
		["call", introduced]]

static func introduced(g: Node) -> void:
	g.state.flags.movein_met = true; g.persist()
	g.message("Look around Room 214, then take the hallway door.")

# ---------------------------------------------------------------- the rooms

static func on_enter(g: Node, id: String) -> void:
	if not active(g): return
	if id == "D02" and not g.state.flags.get("movein_ahead", false):
		g.state.flags.movein_ahead = true

## Jakerson is in the lobby once Jules has gone out into the hall, and only there.
static func room_objects(g: Node, id: String, objects: Array) -> Array:
	if id == "D01" and bool(g.state.flags.get("movein_ahead", false)):
		return objects.filter(func(o: Dictionary) -> bool:return str(o.id) != "jakerson")
	if id == LOBBY and not active(g):
		return objects.filter(func(o: Dictionary) -> bool:return str(o.id) != "jakerson_lobby")
	return objects

static func say(g: Node, lines: Array, then: Callable = Callable()) -> void:
	g.dialogue(lines, func() -> void:
		if then.is_valid(): then.call()
		else: g.resume_world())

static func handle(g: Node, object: Dictionary) -> bool:
	var id: String = str(object.id)
	if id == "jakerson" and str(g.state.room) == START and active(g):
		say(g, [["Jakerson", "Look around! Rule two. The lobby is down the hallway and the stairs. I'll be the one losing to a ping-pong table.", "warm"]])
		return true
	if id == "jakerson_lobby":
		challenge(g); return true
	if id == "front_doors" and active(g):
		say(g, [["Jules", "Campus can wait until tomorrow. Right now there's a roommate by the ping-pong table who needs a witness.", "neutral"]])
		return true
	if id == "floormate_208":
		say(g, [["Eli", "Careful, bike parts. I'm Eli, 208. I fix bikes in the doorway because the hallway has better light.", "warm"],
			["Jules", "Does anybody actually pay you?", "neutral"],
			["Eli", "First repair's free. The second one's coffee. The third is a long conversation about gear ratios.", "warm"],
			["Jules", "I don't have a bike.", "neutral"],
			["Eli", "You will. Everyone gets a bike by October.", "warm"]])
		return true
	if id == "floormate_lounge":
		say(g, [["Imani", "Have you seen a name tag that says TY? It's not mine. It's been on the floor since move-in and I keep expecting someone to claim it.", "neutral"],
			["Jules", "I'm Jules. 214. I just got here.", "warm"],
			["Imani", "Imani, 216. I'm starting a music club. Sound Check. We have a name, a sign-up sheet and no equipment at all.", "warm"],
			["Jules", "That sounds like most clubs.", "neutral"],
			["Imani", "If you ever see a mixer lying around, think of me.", "warm"],
			["Jules", "I'll keep an eye out.", "warm"]])
		return true
	if id == "floormate_laundry":
		say(g, [["Mara", "Three of these shirts are paint-stained and one of them is a crime scene. Don't ask which.", "warm"],
			["Jules", "You paint?", "neutral"],
			["Mara", "Right now I paint the inside of my own door. The RA says a door isn't a canvas. I say it's the biggest canvas on the floor.", "warm"],
			["Mara", "Welcome to Farrand. The dryers eat quarters and the washers eat socks.", "warm"]])
		return true
	if id == "floormate_lobby":
		say(g, [["Nell", "Shh. I'm at the good part. ...Oh. Hi. I'm Nell. I'm working my way through the lobby's donated bookshelf.", "warm"],
			["Jules", "All of it?", "neutral"],
			["Nell", "Someone keeps taking the last pages. I'll find them. It's practically a hobby.", "concern"]])
		return true
	return false

# ---------------------------------------------------------------- the spar and the bet

static func challenge(g: Node) -> void:
	say(g, [["Jakerson", "There you are! Okay. Witness duty. I have been losing to this ping-pong table for forty minutes.", "warm"],
		["Jules", "You play tennis. How do you lose to a table?", "neutral"],
		["Jakerson", "It has a net made of marker and no respect for me. New idea: forget the table. Friendly spar. I attack, you dodge, and I'll explain the rules as we go.", "warm"],
		["Jakerson", "It's how I settle everything. Think of it as roommate orientation.", "warm"]], func() -> void:
		g.jakerson_ui = true
		g.open_menu(g.Mode.MENU, "Jakerson / a friendly spar", [
			g.option("Sure, show me.", func() -> void:NativeJakerson.begin_spar(g)),
			g.option("Give me a minute.", func() -> void:
				say(g, [["Jakerson", "Take your time. Rule four: I never leave a ping-pong table with unfinished business.", "warm"]], func() -> void:
					g.jakerson_ui = false; g.resume_world()))]))

## After the spar: the bet, then four years go by.
static func aftermath(g: Node, peaceful: bool) -> void:
	var lines: Array = [["Jakerson", "See? You never hit me once. You kept one promise and the fight just... ended.", "warm"],
		["Jakerson", "Striking works too. People remember being hit, though. Even over a ping-pong table.", "neutral"]] if peaceful else [["Jakerson", "Ow. Okay, that works too.", "concern"],
		["Jakerson", "People remember being hit, though. Next time, try keeping a promise instead.", "neutral"]]
	lines.append_array([["Jakerson", "Okay, official roommate business. College is going to be a blur and I want one thing on the calendar.", "warm"],
		["Jakerson", "Graduation day. One real match, you and me. Loser buys the boba.", "warm"],
		["Jules", "That's four years from now.", "concern"],
		["Jakerson", "Four years is plenty of time to learn tennis. I'll even teach you. So? Do we have a deal?", "warm"]])
	say(g, lines, func() -> void:
		g.jakerson_ui = true
		g.open_menu(g.Mode.MENU, "Jakerson / loser buys the boba", [
			g.option("Deal. I'm ordering taro.", func() -> void:shake(g, "taro")),
			g.option("Deal. I'm ordering mango.", func() -> void:shake(g, "mango")),
			g.option("Deal. And I'm ordering the biggest cup.", func() -> void:shake(g, "biggest"))]))

static func shake(g: Node, flavor: String) -> void:
	g.jakerson_ui = false
	g.state.flags.movein_boba = flavor
	var reply: String = {"taro": "Taro. Brave. Disgusting, but brave.", "mango": "Mango. Safe, sweet and undefeated. Fine.",
		"biggest": "The biggest cup. Oh, you're going to regret that. I'm putting it on the calendar."}[flavor]
	say(g, [["Jakerson", reply, "warm"], ["Jakerson", "Shake on it. Rule five: a bet only counts if we both remember it.", "warm"],
		["Jules", "Four years. I won't forget.", "warm"]], func() -> void:finish(g))

static func finish(g: Node) -> void:
	var f: Dictionary = g.state.flags
	f.movein_done = true; f.movein_active = false; f.aftermath_pending = ""
	g.persist()
	g.begin_evening()

## How Jakerson refers to the bet at graduation, or "" for a save that never made it.
static func boba(flags: Dictionary) -> String:
	return str(BOBA.get(str(flags.get("movein_boba", "")), ""))
