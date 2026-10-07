class_name NativeSideQuests
extends RefCounted
## Small jobs off the main road, all paid in Buff Bucks (flags stay bool or String for the save):
##  - the house party (H02): guests patrol the room, bumping one starts a quick wandering fight, and the
##    kitchen holds Tanner's mom's casserole (flag party_casserole);
##  - the internship desk in the Pearl Street office (P01): three tasks for Kyle once his meeting is over
##    (flags task_coffee, task_slack, task_demo; intern_complete when all three are done).
## Menus only, no new engine: the desk opens a task list, each task is a few choices in a row.

# ---------------------------------------------------------------- the house party

const BUMP: float = 24.0
const SPEED: float = 0.7
const CASSEROLE_PAY: int = 45
## Guests walk between two points each; a bump starts that guest's fight (core/dodge_patterns_rf_*.gd).
const GUESTS: Array = [
	{"id": "guest_hippie", "art": "hippie", "fight": "rf_hippie", "a": Vector2(210, 272), "b": Vector2(470, 272)},
	{"id": "guest_business", "art": "business_major", "fight": "rf_business_major", "a": Vector2(360, 404), "b": Vector2(660, 404)},
	{"id": "guest_runner", "art": "runner", "fight": "rf_runner", "a": Vector2(655, 292), "b": Vector2(655, 424)},
	{"id": "guest_cyclist", "art": "cyclist", "fight": "rf_cyclist", "a": Vector2(446, 198), "b": Vector2(446, 330)},
]
## QA switches bumping off unless a route turns it on, so the story routes never see a patrol.
static var armed: bool = true
static var guests: Array = []

static func party_open(g: Node) -> bool:
	return str(g.state.room) == "H02" and not bool(g.state.flags.get("party_casserole", false))

static func on_enter(g: Node, room: String) -> void:
	guests = []
	armed = not bool(g.qa)
	if room != "H02" or bool(g.state.flags.get("party_casserole", false)): return
	for e: Dictionary in GUESTS:
		var sprite := AnimatedSprite2D.new()
		sprite.sprite_frames = NativeBossArt.frames(str(e.art))
		sprite.centered = false
		sprite.offset = Vector2(-16, -48)
		sprite.set_meta("id", str(e.id)); sprite.set_meta("art_id", str(e.art))
		sprite.set_meta("fight", str(e.fight)); sprite.set_meta("to_b", true)
		sprite.position = e.a
		sprite.play("idle_down")
		var height: float = NativeBossArt.world_height(str(e.art))
		sprite.set_meta("idle_height", height)
		sprite.frame_changed.connect(func() -> void: NativeCastArt.fit(sprite, height))
		sprite.animation_changed.connect(func() -> void: NativeCastArt.fit(sprite, height))
		NativeCastArt.fit(sprite, height)
		g.world.add_child(sprite)
		g.world_npcs.append(sprite); guests.append(sprite)
	if not bool(g.state.flags.get("party_seen", false)):
		g.state.flags.party_seen = true
		g.message("Packed house. Nobody here is looking for a fight, so don't bump anyone.")

## Patrol step, called every world tick. True when a bump just started a fight.
static func tick(g: Node) -> bool:
	if guests.is_empty() or str(g.state.room) != "H02": return false
	for sprite: Variant in guests:
		if not is_instance_valid(sprite): continue
		var s: AnimatedSprite2D = sprite
		var a: Vector2 = Vector2(GUESTS.filter(func(e: Dictionary) -> bool: return str(e.id) == str(s.get_meta("id")))[0].a)
		var b: Vector2 = Vector2(GUESTS.filter(func(e: Dictionary) -> bool: return str(e.id) == str(s.get_meta("id")))[0].b)
		var goal: Vector2 = b if bool(s.get_meta("to_b")) else a
		var change: Vector2 = goal - s.position
		if change.length() <= SPEED: s.position = goal; s.set_meta("to_b", not bool(s.get_meta("to_b")))
		else: s.position += change.normalized() * SPEED
		var dir: String = ("left" if change.x < 0 else "right") if absf(change.x) > absf(change.y) else ("up" if change.y < 0 else "down")
		var anim: String = "walk_" + dir if s.sprite_frames.has_animation("walk_" + dir) else "idle_" + dir if s.sprite_frames.has_animation("idle_" + dir) else "idle_down"
		if str(s.animation) != anim: s.play(anim)
	if not armed or int(g.mode) != int(g.Mode.WORLD) or int(g.grace_ticks) > 0 or NativeRoomScenes.busy(): return false
	for sprite: Variant in guests:
		if is_instance_valid(sprite) and (sprite as Node2D).position.distance_to(g.player.position) < BUMP:
			var fight: String = str(sprite.get_meta("fight"))
			g.message("You bumped into someone!")
			return NativeRandomFights.begin(g, fight)
	return false

# ---------------------------------------------------------------- hooks

static func handle(g: Node, object: Dictionary) -> bool:
	var id: String = str(object.id)
	var f: Dictionary = g.state.flags
	if id == "kitchen" and str(g.state.room) == "H02":
		if bool(f.get("party_casserole", false)):
			g.dialogue([["Jules", "The kitchen is calm now. Somebody is making pancakes with the lights on.", "warm"]], g.resume_world)
		else:
			g.dialogue([["Jules", "A foil dish on the counter, labeled in marker: FOR TANNER. EAT A VEGETABLE. LOVE, MOM.", "warm"],
				["Jules", "I'm bringing this to the Hill. Somebody should eat a vegetable tonight.", "warm"]], func() -> void:
				f.party_casserole = true
				pay(g, CASSEROLE_PAY)
				g.persist()
				on_enter(g, "none")
				for npc: AnimatedSprite2D in g.world_npcs.duplicate():
					if str(npc.get_meta("id", "")).begins_with("guest_"): g.world_npcs.erase(npc); npc.queue_free()
				g.message("Casserole in hand. +%d Buff Bucks for the delivery" % CASSEROLE_PAY)
				g.resume_world())
		return true
	if id == "intern_desk" and str(g.state.room) == "P01":
		if not f.has("kyle_resolution"):
			g.dialogue([["Jules", "Somebody left a sticky note: 'Intern tasks, ask Kyle for the access code.' Kyle is by the pitch screen.", "neutral"]], g.resume_world)
		else:
			desk(g, "")
		return true
	return false

static func pay(g: Node, amount: int) -> void:
	g.state.flags.buff_bucks = str(NativeRandomFights.bucks(g.state.flags) + amount)

# ---------------------------------------------------------------- the internship desk

const TASKS: Array = [["task_coffee", "Coffee run", 30], ["task_slack", "Clear the Slack storm", 35], ["task_demo", "Friday demo", 50]]
const ORDER: Array = ["Oat latte, extra hot", "Cold brew, no ice", "Chai, double shot"]
const CUPS: Array = ["Oat latte, extra hot", "Cold brew, no ice", "Chai, double shot", "Drip, regular", "Matcha, oat milk"]
## [what comes in, correct move, what Kyle says when you get it wrong]
const PINGS: Array = [
	["@Jules can you pull the numbers by four?", "Reply", "A mention is a person. People get answers."],
	["ANNOUNCEMENT: the fridge will be cleaned Friday. Anything labeled FAMILY gets thrown out.", "React", "Announcements get a thumbs up, not a thesis."],
	["a picture of a cat in a tiny tie, no caption", "Mute", "Memes are why we have a mute button."],
	["ANNOUNCEMENT: pizza Friday has moved to Thursday.", "React", "That one only needs a thumbs up."],
	["a dog standing in front of a whiteboard, 'synergy'", "Mute", "Pure meme. Mute it."],
]
## The demo: three choices, one honest option each.
const DEMO: Array = [
	["Open with:", ["We're like a family here", "The problem a real user actually has", "The roadmap for the next year"], 1],
	["Show:", ["The working feature", "A mockup labeled LIVE", "The logo animation"], 0],
	["Close with:", ["Let's circle back", "Forty thousand users, trust me", "A question: what would you change?"], 2],
]

static func done(f: Dictionary, key: String) -> bool:
	return bool(f.get(key, false))

static func desk(g: Node, note: String) -> void:
	var f: Dictionary = g.state.flags
	var options: Array = []
	for t: Array in TASKS:
		var key: String = str(t[0])
		var label: String = "%s / %s" % [str(t[1]), "done" if done(f, key) else "%d BB" % int(t[2])]
		if key == "task_demo" and not done(f, key) and not (done(f, "task_coffee") and done(f, "task_slack")): label = "%s / after the other two" % str(t[1])
		options.append(g.option(label, func() -> void: start(g, key)))
	options.append(g.option("Back", g.resume_world))
	g.open_menu(g.Mode.MENU, note if not note.is_empty() else "Intern desk / Buff Bucks %d" % NativeRandomFights.bucks(f), options)

static func start(g: Node, key: String) -> void:
	var f: Dictionary = g.state.flags
	if done(f, key): desk(g, "Already done. Kyle put a gold star sticker on your monitor."); return
	if key == "task_demo" and not (done(f, "task_coffee") and done(f, "task_slack")): desk(g, "Kyle: Friday is for people who've finished Monday and Tuesday."); return
	match key:
		"task_coffee":
			g.dialogue([["Kyle", "Coffee for the standup! Listen carefully, I'll say it once. Oat latte, extra hot. Cold brew, no ice. Chai, double shot.", "warm"],
				["Jules", "Oat latte. Cold brew. Chai. Got it.", "neutral"]], func() -> void: cup(g, 0))
		"task_slack":
			g.dialogue([["Kyle", "The channel is on fire. @mention means a person needs you: Reply. Announcements: React. Memes: Mute.", "warm"]], func() -> void: ping(g, 0, 0))
		"task_demo":
			g.dialogue([["Kyle", "The investors are here. Well. One investor. He's my cousin. Make it count.", "warm"]], func() -> void: slide(g, 0, 0))

static func finish_task(g: Node, key: String) -> void:
	var f: Dictionary = g.state.flags
	var pay_: int = 0
	for t: Array in TASKS:
		if str(t[0]) == key: pay_ = int(t[2])
	f[key] = true
	pay(g, pay_)
	var all: bool = done(f, "task_coffee") and done(f, "task_slack") and done(f, "task_demo")
	var line: String = "Task done. +%d Buff Bucks." % pay_
	if all and not done(f, "intern_complete"):
		f.intern_complete = true
		var item: String = "thermos" if NativeRandomFights.add_item(g.state.inventory, "thermos") else ""
		pay(g, 20)
		line = "All three tasks done. +%d Buff Bucks and a bonus of 20%s." % [pay_, (", plus a thermos" if not item.is_empty() else "")]
	g.persist()
	g.dialogue([["Kyle", "That is the best performance review this company has ever had." if all else "Wow. Done already? I'm adding that to your stack of reviews.", "warm"]], func() -> void:
		g.message(line)
		desk(g, ""))

# coffee: pick the cups in the order Kyle said
static func cup(g: Node, step: int) -> void:
	var options: Array = []
	for c: String in CUPS:
		var pick: String = c
		options.append(g.option(pick, func() -> void:
			if pick == str(ORDER[step]):
				if step + 1 >= ORDER.size(): g.dialogue([["Kyle", "Right order, right temperature, right amount of oat. You're a natural.", "warm"]], func() -> void: finish_task(g, "task_coffee"))
				else: cup(g, step + 1)
			else:
				g.dialogue([["Kyle", "That's not what I said. I said it ONCE. Let me say it once again.", "concern"]], func() -> void: start(g, "task_coffee"))))
	g.open_menu(g.Mode.MENU, "Coffee run / cup %d of %d" % [step + 1, ORDER.size()], options)

# slack: triage five pings, at most one wrong
static func ping(g: Node, index: int, wrong: int) -> void:
	if index >= PINGS.size():
		if wrong <= 1: finish_task(g, "task_slack")
		else: g.dialogue([["Kyle", "Three pings got the wrong treatment. I'm going to let the channel burn a little longer.", "concern"]], func() -> void: desk(g, "Slack storm / try again"))
		return
	var p: Array = PINGS[index]
	var options: Array = []
	for move: String in ["Reply", "React", "Mute"]:
		var pick: String = move
		options.append(g.option(pick, func() -> void:
			if pick == str(p[1]): ping(g, index + 1, wrong)
			else: g.dialogue([["Kyle", str(p[2]), "concern"]], func() -> void: ping(g, index + 1, wrong + 1))))
	g.open_menu(g.Mode.MENU, "Ping %d of %d / %s" % [index + 1, PINGS.size(), str(p[0])], options)

# demo: honest choices, all three
static func slide(g: Node, index: int, good: int) -> void:
	if index >= DEMO.size():
		if good == DEMO.size(): finish_task(g, "task_demo")
		else: g.dialogue([["Kyle", "My cousin says it 'didn't land.' He also says he loves the vibes. Try the deck again.", "concern"]], func() -> void: desk(g, "Friday demo / try again"))
		return
	var s: Array = DEMO[index]
	var options: Array = []
	var choices: Array = s[1]
	for i: int in choices.size():
		var at: int = i
		options.append(g.option(str(choices[i]), func() -> void: slide(g, index + 1, good + (1 if at == int(s[2]) else 0))))
	g.open_menu(g.Mode.MENU, "Friday demo / slide %d of %d / %s" % [index + 1, DEMO.size(), str(s[0])], options)
