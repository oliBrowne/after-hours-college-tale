class_name NativeTalkMotion
extends RefCounted
## Whoever is speaking moves while their line types: a drawn "talk_<facing>" cycle when the cast
## has one, otherwise their talking pose ("interact_<facing>") traded with idle a few times a
## second. Everyone else keeps the way they were facing, so a walk-in scene's people can look at
## each other while they talk. main.gd calls stage() for each new line and update() every frame
## of dialogue.

const DIRECTIONS: Array[String] = ["down", "left", "right", "up"]
## Pose swaps per second for cast without a drawn talk cycle.
const BEAT: float = 5.0

static func facing(sprite: AnimatedSprite2D) -> String:
	var parts: PackedStringArray = str(sprite.animation).split("_")
	if parts.size() > 1 and parts[-1] in DIRECTIONS: return parts[-1]
	var name: String = str(sprite.get_meta("facing", ""))
	return name if name in DIRECTIONS else "down"

static func talking_pose(sprite: AnimatedSprite2D, direction: String) -> String:
	var frames: SpriteFrames = sprite.sprite_frames
	if frames.has_animation("talk_" + direction): return "talk_" + direction
	if frames.has_animation("interact_" + direction): return "interact_" + direction
	return "idle_" + direction

## The world sprites for this line's speaker: the party member or the room's cast sprites.
static func speakers(g: Node, speaker: String, identities: Dictionary) -> Array:
	var found: Array = []
	if not g.world.visible: return found
	for i: int in range(3):
		var person: WorldActor = g.player if i == 0 else g.followers[i - 1]
		if person.visible and g.ACTORS[i].capitalize() == speaker: found.append(person.art)
	var art: String = str(identities.get(speaker, ""))
	if not art.is_empty():
		for npc: AnimatedSprite2D in g.world_npcs:
			if str(npc.get_meta("art_id", npc.get_meta("id", ""))) == art: found.append(npc)
	return found

## A new line: the speaker takes their talking pose, everyone else settles to idle where they face.
static func stage(g: Node, speaker: String, identities: Dictionary) -> void:
	var talkers: Array = speakers(g, speaker, identities)
	g.set_meta("talkers", talkers)
	for npc: AnimatedSprite2D in g.world_npcs:
		if not (str(npc.get_meta("art_id", npc.get_meta("id", ""))) in NativeCastArt.IDS or npc.get_meta("id", "") == "flyer"): continue
		if npc in talkers: continue
		if g.state.flags.has(str(npc.get_meta("id")) + "_resolution") and npc.sprite_frames.has_animation("settled"): npc.play("settled"); continue
		var idle: String = "idle_" + facing(npc)
		npc.play(idle if npc.sprite_frames.has_animation(idle) else "idle_down")
	for i: int in range(3):
		var person: WorldActor = g.player if i == 0 else g.followers[i - 1]
		if person.visible and not person.art in talkers: person.art.play("idle_" + person.facing)
	for sprite: AnimatedSprite2D in talkers: _play(sprite, talking_pose(sprite, _face(sprite)))

## Every dialogue frame: keep the speaker's mouth moving while text is still appearing.
static func update(g: Node, typing: bool, time: float) -> void:
	for sprite: Variant in g.get_meta("talkers", []):
		if not is_instance_valid(sprite): continue
		var talker: AnimatedSprite2D = sprite
		var direction: String = _face(talker)
		var pose: String = talking_pose(talker, direction)
		if not typing or bool(g.state.settings.reducedMotion): _play(talker, "idle_" + direction); continue
		if pose.begins_with("talk_"): _play(talker, pose); continue
		_play(talker, pose if int(time * BEAT) % 2 == 0 else "idle_" + direction)

static func _face(sprite: AnimatedSprite2D) -> String:
	var owner: Node = sprite.get_parent()
	if owner is WorldActor: return str((owner as WorldActor).facing)
	return facing(sprite)

static func _play(sprite: AnimatedSprite2D, animation: String) -> void:
	if not sprite.sprite_frames.has_animation(animation): animation = "idle_down"
	if str(sprite.animation) == animation: return
	if str(sprite.get_meta("art_id", "")) == "jakerson": NativeJakerson.pose(sprite, animation); return
	sprite.play(animation)
	if not sprite.get_parent() is WorldActor: NativeCastArt.fit(sprite, float(sprite.get_meta("idle_height", 48.0)))
