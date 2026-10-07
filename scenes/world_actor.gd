class_name WorldActor
extends CharacterBody2D

var art: AnimatedSprite2D
var appearance_height: float=52.0
var facing: String = "down"
var travelled: float = 0.0
var walk_bounds: Rect2 = Rect2(20, 150, 600, 166)

func configure(actor_id: String, blocking: bool) -> void:
	appearance_height=NativeCastArt.world_height(actor_id)
	art = AnimatedSprite2D.new()
	art.sprite_frames = NativePartyArt.frames(actor_id)
	art.centered = false
	art.offset = Vector2(-16, -48)
	art.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(art)
	art.play("idle_down")
	if actor_id in ["jules","imani","walt"]:
		art.frame_changed.connect(func() -> void: NativeCastArt.fit(art, appearance_height))
		art.animation_changed.connect(func() -> void: NativeCastArt.fit(art, appearance_height))
		NativeCastArt.fit(art, appearance_height)
	collision_layer = 2 if blocking else 0
	collision_mask = 1 if blocking else 0
	var foot: CollisionShape2D = CollisionShape2D.new()
	var shape: RectangleShape2D = RectangleShape2D.new()
	shape.size = Vector2(14, 8)
	foot.shape = shape
	foot.position = Vector2(0, -4)
	add_child(foot)

func walk(direction: Vector2, running: bool, delta: float) -> void:
	if direction.length_squared() > 1.0:
		direction = direction.normalized()
	velocity = direction * (128.0 if running else 80.0)
	var before: Vector2 = position
	move_and_slide()
	position.x = clampf(position.x, walk_bounds.position.x, walk_bounds.end.x)
	position.y = clampf(position.y, walk_bounds.position.y, walk_bounds.end.y)
	var movement: Vector2 = position - before
	travelled += movement.length()
	if movement.length_squared() > 0.0001:
		art.rotation=0.0
		facing = ("left" if movement.x < 0 else "right") if absf(movement.x) > absf(movement.y) else ("up" if movement.y < 0 else "down")
		var animation_name: String = ("run_" if running else "walk_") + facing
		art.animation = animation_name
		art.pause()
		art.frame = NativeWalkArt.frame_for(art.sprite_frames, art.animation, travelled, running)
	elif not (str(art.animation).begins_with("fidget") and art.is_playing()):
		art.play("idle_" + facing)
	if delta <= 0:
		velocity = Vector2.ZERO

func follow(point: Vector2) -> void:
	var change: Vector2 = point - position
	if change.length_squared() > 0.1:
		art.rotation=0.0
		facing = ("left" if change.x < 0 else "right") if absf(change.x) > absf(change.y) else ("up" if change.y < 0 else "down")
		travelled += change.length()
		position = point
		art.animation = "walk_" + facing
		art.pause()
		art.frame = NativeWalkArt.frame_for(art.sprite_frames, art.animation, travelled, false)
	elif not (str(art.animation).begins_with("fidget") and art.is_playing()):
		art.play("idle_" + facing)
