class_name NativeRoomScenes
extends RefCounted
## Walk-in scenes: the first time you step into certain rooms, the people there play out a
## short moment before you get control back, so key characters show up before their story
## does. Each plays once (flag scene_<id>). main.gd calls step() at the top of world_tick
## and reset() from enter_room.
##
## A scene is a list of steps run in order:
##   ["spawn", actor, cast id, point]      a new sprite for the scene, removed at the end
##   ["borrow", actor, room object id]     an NPC already standing in the room
##   ["walk", [[actor, point, speed], ...]] everyone listed walks at once until all arrive
##   ["face", actor, point or actor]       turn toward something
##   ["jules", point or actor]             Jules turns toward something
##   ["say", lines]                        ordinary dialogue
##   ["wait", ticks]
##   ["leave", actor]                      a spawned actor walks off-screen through its last door

const WALK: float = 1.2
const RUN: float = 2.6
static var run: Dictionary = {}

static func busy() -> bool:return not run.is_empty()

static func reset() -> void:run = {}

static func due(g: Node) -> String:
	var f: Dictionary = g.state.flags
	var room: String = str(g.state.room)
	if room == "U03" and not f.get("mixer_returned", false) and not f.get("scene_chip_todd", false): return "chip_todd"
	if room == "N01" and f.get("chapter1_complete", false) and not f.get("library_pass", false) and not f.get("scene_nell_pencil", false): return "nell_pencil"
	if room == "E01" and not f.has("eric_resolution") and not f.get("scene_eric_lobby", false): return "eric_lobby"
	return ""

static func steps(id: String) -> Array:
	match id:
		"chip_todd":
			# Chip bursts in from the Farrand gate to the president, then dashes back out.
			return [["borrow", "todd", "todd"], ["spawn", "chip", "chip", Vector2(730, 385)],
				["walk", [["chip", Vector2(578, 300), RUN]]], ["face", "chip", "todd"], ["face", "todd", "chip"],
				["say", [["Chip", "Mr. President! Mr. President! The Farrand show is going LONG tonight. Nobody's leaving!", "warm"],
					["Todd Saliman", "Chip. Every event has a closing time. It's in the policy.", "neutral"],
					["Chip", "Policies are for people who don't have an ENCORE!", "warm"],
					["Todd Saliman", "...I'm going to need that in writing.", "neutral"]]],
				["walk", [["chip", Vector2(730, 385), RUN]]], ["leave", "chip"], ["face", "todd", "jules"],
				["say", [["Jules", "Was that the university president? At midnight?", "concern"],
					["Todd Saliman", "Somebody has to sign off on the end of the night.", "neutral"]]]]
		"nell_pencil":
			# Nell steps out of Norlin looking for something that is not supposed to walk.
			return [["spawn", "nell", "nell", Vector2(510, 196)], ["walk", [["nell", Vector2(470, 300), WALK]]], ["face", "nell", "jules"], ["jules", "nell"],
				["say", [["Nell", "Excuse me! Has anyone seen a red pencil go past? About this tall. Walking.", "concern"],
					["Jules", "A pencil. Walking.", "neutral"],
					["Nell", "It's been correcting the flyers on the quad since midnight. If it offers to fix your sentences, say no thank you. Firmly.", "concern"],
					["Imani", "Noted. Firmly.", "warm"],
					["Nell", "I'm Nell, checkout desk. Come in if you need a library pass. Apparently the night shift is all of us.", "warm"]]],
				["walk", [["nell", Vector2(510, 196), WALK]]], ["leave", "nell"]]
		"eric_lobby":
			# Professor Eric and Dev come out of the workshop mid-argument about one more test.
			return [["spawn", "eric", "eric", Vector2(510, 192)], ["spawn", "dev", "dev", Vector2(510, 192)],
				["walk", [["eric", Vector2(468, 300), WALK]]], ["walk", [["dev", Vector2(540, 300), WALK]]],
				["face", "eric", "dev"], ["face", "dev", "eric"],
				["say", [["Professor Eric", "...and THAT is why the return current matters, Dev. Every signal needs a way home. Every one!", "warm"],
					["Dev", "Professor, it's one in the morning. The test floor has been running since ten.", "concern"],
					["Professor Eric", "One more measurement. The old bridge model is still ringing. I can see it in the data.", "neutral"],
					["Dev", "You said that at eleven.", "neutral"],
					["Professor Eric", "And I was right at eleven! Rule of thumb: never trust a signal you haven't looked at. Back to the scope!", "warm"]]],
				["walk", [["eric", Vector2(510, 192), WALK], ["dev", Vector2(510, 192), WALK]]], ["leave", "eric"], ["leave", "dev"],
				["jules", Vector2(510, 192)],
				["say", [["Jules", "Was that a professor? Still teaching?", "neutral"],
					["Imani", "Professor Eric. Signal integrity. My roommate says his office hours never really end.", "warm"],
					["Walt", "Sounds like somebody else's night we know.", "neutral"]]]]
	return []

## Called at the top of world_tick. True while a scene holds the world still.
static func step(g: Node) -> bool:
	if run.is_empty():
		if g.transition_ticks > 0 or g.mode != g.Mode.WORLD or NativeJakerson.busy() or NativeJakerson.guide(g) == "walk": return false
		var id: String = due(g)
		if id.is_empty(): return false
		g.state.flags["scene_" + id] = true; g.persist()
		g.player.walk(Vector2.ZERO, false, 0.0)
		run = {"id": id, "steps": steps(id), "index": 0, "actors": {}, "spawned": [], "wait": 0, "saying": false}
	if bool(run.saying): return true
	var list: Array = run.steps
	while int(run.index) < list.size():
		var s: Array = list[int(run.index)]
		if not _do(g, s): return true
		run.index = int(run.index) + 1
		if bool(run.saying): return true
	_finish(g)
	return false

## Runs one step for this tick. True when the step is finished.
static func _do(g: Node, s: Array) -> bool:
	var actors: Dictionary = run.actors
	match str(s[0]):
		"spawn":
			var sprite := AnimatedSprite2D.new()
			sprite.sprite_frames = NativeCastArt.frames(str(s[2]))
			sprite.set_meta("id", "scene_" + str(s[1])); sprite.set_meta("art_id", str(s[2]))
			sprite.set_meta("idle_height", NativeCastArt.world_height(str(s[2])))
			sprite.z_index = g.player.z_index
			g.world.add_child(sprite); g.world_npcs.append(sprite)
			sprite.set_meta("base", Vector2(s[3])); sprite.position = Vector2(s[3]); sprite.set_meta("door", Vector2(s[3]))
			_pose(sprite, "idle_down")
			actors[str(s[1])] = sprite; run.spawned.append(sprite)
		"borrow":
			for npc: AnimatedSprite2D in g.world_npcs:
				if str(npc.get_meta("id", "")) == str(s[2]):
					npc.set_meta("base", npc.position); actors[str(s[1])] = npc
		"walk":
			var moving: bool = false
			for move: Array in s[1]:
				var sprite: AnimatedSprite2D = actors.get(str(move[0]))
				if sprite != null and is_instance_valid(sprite) and _walk(g, sprite, Vector2(move[1]), float(move[2])): moving = true
			if moving: return false
			for move: Array in s[1]:
				var sprite2: AnimatedSprite2D = actors.get(str(move[0]))
				if sprite2 != null and is_instance_valid(sprite2): _pose(sprite2, "idle_" + str(sprite2.get_meta("facing", "down"))); sprite2.position = _base(sprite2)
		"face":
			var who: AnimatedSprite2D = actors.get(str(s[1]))
			if who != null and is_instance_valid(who): _face(who, _point(g, s[2]))
		"jules":
			var d: Vector2 = _point(g, s[1]) - g.player.position
			g.player.facing = ("left" if d.x < 0 else "right") if absf(d.x) > absf(d.y) else ("up" if d.y < 0 else "down")
			g.player.art.play("idle_" + g.player.facing)
		"say":
			run.saying = true
			g.dialogue(s[1], func() -> void:
				run.saying = false; g.resume_world())
		"wait":
			run.wait = int(run.wait) + 1
			if int(run.wait) < int(s[1]): return false
			run.wait = 0
		"leave":
			var gone: AnimatedSprite2D = actors.get(str(s[1]))
			if gone != null and is_instance_valid(gone):
				g.world_npcs.erase(gone); gone.queue_free(); actors.erase(str(s[1]))
	return true

static func _finish(g: Node) -> void:
	for sprite: Variant in run.spawned:
		if is_instance_valid(sprite):
			g.world_npcs.erase(sprite); (sprite as Node).queue_free()
	for actor: Variant in run.actors.values():
		if is_instance_valid(actor): (actor as AnimatedSprite2D).set_meta("moving", false)
	run = {}

static func _point(g: Node, target: Variant) -> Vector2:
	if target is Vector2: return target
	if str(target) == "jules": return g.player.position
	var sprite: AnimatedSprite2D = run.actors.get(str(target))
	return _base(sprite) if sprite != null and is_instance_valid(sprite) else g.player.position

static func _base(sprite: AnimatedSprite2D) -> Vector2:return Vector2(sprite.get_meta("base", sprite.position))

## One tick of walking toward goal along the room's walkable route. False once there.
static func _walk(g: Node, sprite: AnimatedSprite2D, goal: Vector2, speed: float) -> bool:
	var at: Vector2 = _base(sprite)
	if at.distance_to(goal) <= speed:
		sprite.set_meta("base", goal); sprite.position = goal; sprite.set_meta("path", PackedVector2Array())
		return false
	var path: PackedVector2Array = sprite.get_meta("path", PackedVector2Array())
	if path.is_empty() or Vector2(path[-1]).distance_to(goal) > 2.0:
		path = g.navigation.route(at, goal)
		if path.is_empty(): path = PackedVector2Array([goal])
	while path.size() > 1 and at.distance_to(path[0]) < speed + 0.5: path.remove_at(0)
	var change: Vector2 = Vector2(path[0]) - at
	var moved: Vector2 = change if change.length() <= speed else change.normalized() * speed
	at += moved; sprite.set_meta("path", path); sprite.set_meta("base", at)
	var facing: String = ("left" if moved.x < 0 else "right") if absf(moved.x) > absf(moved.y) else ("up" if moved.y < 0 else "down")
	sprite.set_meta("facing", facing)
	_pose(sprite, ("walk_" if sprite.sprite_frames.has_animation("walk_" + facing) else "idle_") + facing)
	var travelled: float = float(sprite.get_meta("travelled", 0.0)) + moved.length()
	sprite.set_meta("travelled", travelled)
	# Cast with drawn step cycles (NativeWalkArt) step by distance; the rest dip 1px per step.
	var stepping: bool = sprite.sprite_frames.get_frame_count(sprite.animation) > 1
	NativeWalkArt.step(sprite, travelled, speed >= RUN)
	sprite.position = at + (Vector2.ZERO if stepping or fmod(travelled, 18.0) >= 9.0 else Vector2(0, -1))
	return true

static func _face(sprite: AnimatedSprite2D, target: Vector2) -> void:
	var d: Vector2 = target - _base(sprite)
	var facing: String = ("left" if d.x < 0 else "right") if absf(d.x) > absf(d.y) * 1.2 else ("up" if d.y < 0 else "down")
	sprite.set_meta("facing", facing)
	_pose(sprite, "idle_" + facing); sprite.position = _base(sprite)

## Plays a pose with the cast's usual fitting (which mirrors left poses) and keeps the idle
## motion and glances off this sprite while the scene moves it.
static func _pose(sprite: AnimatedSprite2D, animation: String) -> void:
	if not sprite.sprite_frames.has_animation(animation): animation = "idle_down"
	if str(sprite.animation) != animation: sprite.play(animation)
	if str(sprite.get_meta("art_id", "")) == "jakerson": NativeJakerson.pose(sprite, animation); return
	NativeCastArt.fit(sprite, float(sprite.get_meta("idle_height", 56.0)))
	sprite.set_meta("moving", true)
