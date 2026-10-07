class_name NativeSideBosses
extends RefCounted
## Optional mini-bosses off the main road, each with a gym-leader card (NativeBossIntro) and a dodge
## script (core/dodge_patterns_<id>.gd): Tanner on the Hill and Kyle in the Pearl Street office.
## Harder than a wandering fight, easier than a chapter boss. They live as ordinary talk objects
## in their room; the object's id is the boss id. Both endings are fine, both pay Buff Bucks (the
## peaceful one the full amount) and the peaceful one sends a LinkedOut request (core/linkedout.gd).
## Flags are the usual <id>_resolution and <id>_rehearsal (saves keep bool and String only).
const BOSSES: Dictionary = {
	"tanner": {"name": "Tanner", "room": "H01", "hp": 130, "bucks": [60, 80],
		"intro": [["Tanner", "BRO. BRO. Did you hear that? That's my brothers carrying me. It's a whole thing.", "warm"],
			["Jules", "Why are you in a toga?", "neutral"],
			["Tanner", "Rush week never ends, bro. And you're a senior. Seniors are legends. Legends get a bid.", "warm"],
			["Jules", "I graduate tomorrow.", "neutral"],
			["Tanner", "PERFECT. Zero commitment. One game night. One. Okay, five.", "warm"]],
		"connect": ["Ask what the bid includes", "Decline one more game", "Say good night"],
		"peaceful": [["Tanner", "Four games declined and I felt nothing but respect. ...Okay. A little FOMO. It passed.", "warm"],
			["Jules", "You can sit down, you know.", "warm"],
			["Tanner", "Bro. I have an 8 AM. I've had an 8 AM every day for three years. I just never went to bed for it.", "concern"],
			["Tanner", "Goodnight, legend. The couch is yours anytime. The brothers will carry you. It's only a little scary.", "warm"]],
		"forceful": [["Tanner", "Okay, okay! Ow! Bro. That's fair. The couch can take it.", "concern"],
			["Jules", "Sorry about the couch.", "concern"],
			["Tanner", "My brothers are going to tell everyone it was a hit and run. Don't worry. They'll be dramatic about it for a week.", "warm"]],
		"done_peaceful": [["Tanner", "Got my 8 AM. Got my eight hours. Got a casserole from my mom. Life is good, bro.", "warm"]],
		"done_forceful": [["Tanner", "The couch has a dent. We're calling it character. Come back when you want a bid.", "warm"]]},
	"kyle": {"name": "Kyle", "room": "P01", "hp": 170, "bucks": [80, 100],
		"intro": [["Kyle", "Jules! Welcome to the team! We say 'family.' We're like a family here.", "warm"],
			["Jules", "I'm an intern for one night.", "neutral"],
			["Kyle", "A night is an eternity in startup time. Let me walk you through the vision. Slide one.", "warm"],
			["Jules", "What does the product do?", "neutral"],
			["Kyle", "Great question! Hold it to the end of the deck. The end of the deck is a rumor.", "warm"]],
		"connect": ["Ask who the customers are", "Ask what the product does", "Take the meeting offline"],
		"peaceful": [["Kyle", "Nobody has ever asked me that three times in a row. ...Okay. Nobody knows what the product does. I don't either.", "concern"],
			["Jules", "You could ask the users.", "warm"],
			["Kyle", "Ask the users. Wild. I'm putting that on a slide. Slide one hundred thirteen.", "warm"],
			["Kyle", "Thanks for the feedback. It's the first feedback I've heard that wasn't a thumbs-up emoji.", "warm"]],
		"forceful": [["Kyle", "Ow! Okay! That was a very direct form of feedback. I'll circle back.", "concern"],
			["Jules", "Sorry. You wouldn't answer the question.", "concern"],
			["Kyle", "That's fair. I'll put it in the retro. Retro's on Thursdays. Every Thursday. For a year.", "warm"]],
		"done_peaceful": [["Kyle", "I wrote down what the product does. It fits on one sticky note. It's on the fridge. Please don't tell the investors.", "warm"]],
		"done_forceful": [["Kyle", "We're like a family here. A family that's put 'ask what the product does' on the roadmap. Q4.", "warm"]]},
}

static func is_boss(id: String) -> bool:
	return BOSSES.has(id)

static func name_of(id: String) -> String:
	return str(BOSSES[id].name) if BOSSES.has(id) else ""

static func hp(id: String) -> int:
	return int(BOSSES[id].hp)

static func connect_labels(id: String) -> Array:
	return BOSSES[id].connect

## Called by begin_battle after its own foe setup: this boss's HP and sprite.
static func setup(g: Node) -> void:
	var id: String = str(g.boss_id)
	g.battle.hp = hp(id)
	g.foe.sprite_frames = NativeBossArt.frames(id)
	g.foe.play("idle_down")

## interact() hook: the boss's object in its own room starts the fight; afterwards it just chats.
static func handle(g: Node, object: Dictionary) -> bool:
	var id: String = str(object.id)
	if not BOSSES.has(id) or str(BOSSES[id].room) != str(g.state.room): return false
	var e: Dictionary = BOSSES[id]
	var done: String = str(g.state.flags.get(id + "_resolution", ""))
	if not done.is_empty():
		g.dialogue(e.done_peaceful if done == "peaceful" else e.done_forceful, g.resume_world)
		return true
	g.dialogue(e.intro, func() -> void:
		g.boss_id = id
		g.start_battle())
	return true

## Buff Bucks for a win (the full roll when peaceful, three fifths when not), plus one thermos if the pack has room.
static func reward(state: Dictionary, id: String, peaceful: bool, r: RandomNumberGenerator) -> Dictionary:
	var range_: Array = BOSSES[id].bucks
	var base: int = r.randi_range(int(range_[0]), int(range_[1]))
	var gain: int = base if peaceful else maxi(1, roundi(float(base) * 0.6))
	var f: Dictionary = state.flags
	f.buff_bucks = str(NativeRandomFights.bucks(f) + gain)
	var item: String = "thermos" if NativeRandomFights.add_item(state.inventory, "thermos") else ""
	return {"gain": gain, "item": item}

## show_aftermath hook: the closing lines, the payout, and back to the world in the same room.
static func aftermath(g: Node, id: String) -> void:
	var f: Dictionary = g.state.flags
	var peaceful: bool = str(f.get(id + "_resolution", "")) == "peaceful"
	g.boss_id = ""
	g.enter_room(str(g.state.room), Vector2(float(g.state.x), float(g.state.y)), false)
	g.grace_ticks = NativeRandomFights.GRACE
	g.dialogue(BOSSES[id].peaceful if peaceful else BOSSES[id].forceful, func() -> void:
		var won: Dictionary = reward(g.state, id, peaceful, NativeRandomFights.rng(g))
		f.aftermath_pending = ""
		g.persist()
		g.message(NativeRandomFights.summary(int(won.gain), str(won.item)))
		g.resume_world())
