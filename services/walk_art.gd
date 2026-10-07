class_name NativeWalkArt
extends RefCounted
## Stepping walk cycles drawn at native size by tools/walk_cycle: the legs pass each other and the
## body rises a pixel on each passing step, so walkers stop gliding. They replace the walk and run
## animations of fitted world frames whose source is tagged with "walk_key"; a strip whose canvas
## no longer matches the fitted frames (the art was resized) is skipped and the old frames stay.
const DIR: String = "res://assets/art/walk/"
## Pixels travelled per full cycle (two steps) when walking and when running.
const CYCLE: float = 36.0
const RUN_CYCLE: float = 44.0
static var metadata: Dictionary = {}
static var strips: Dictionary = {}

static func data() -> Dictionary:
	if metadata.is_empty():
		metadata = JSON.parse_string(FileAccess.get_file_as_string(DIR + "walk.json"))
	return metadata

static func cycle(key: String, direction: String) -> Array:
	var id: String = key + "/" + direction
	if strips.has(id): return strips[id]
	var cells: Array = []
	var entry: Dictionary = data().get(key, {}).get(direction, {})
	if not entry.is_empty():
		var sheet: Image = (load(DIR + str(entry.file)) as Texture2D).get_image()
		if sheet.is_compressed(): sheet.decompress()
		sheet.convert(Image.FORMAT_RGBA8)
		var size := Vector2i(int(entry.size[0]), int(entry.size[1]))
		for i: int in range(int(entry.frames)):
			var texture := ImageTexture.create_from_image(sheet.get_region(Rect2i(Vector2i(i * size.x, 0), size)))
			texture.set_meta("foot", Vector2(float(entry.foot[0]), float(entry.foot[1])))
			texture.set_meta("explicit_direction", true); texture.set_meta("native_pixels", true)
			cells.append(texture)
	strips[id] = cells
	return cells

## Swaps the stepping cycles into fitted frames (NativePixelCast.frames calls this).
static func apply(frames: SpriteFrames, raw: SpriteFrames) -> void:
	var key: String = str(raw.get_meta("walk_key", ""))
	if key.is_empty(): return
	var mirror_left: bool = raw.get_meta("walk_mirror_left", false)
	for direction: String in ["down", "up", "right", "left"]:
		var cells: Array = cycle(key, "right" if direction == "left" and mirror_left else direction)
		if cells.is_empty() or not frames.has_animation("idle_" + direction): continue
		var fitted: Texture2D = frames.get_frame_texture("idle_" + direction, 0)
		if fitted.get_size() != (cells[0] as Texture2D).get_size() or Vector2(fitted.get_meta("foot")) != Vector2(cells[0].get_meta("foot")): continue
		for prefix: String in ["walk_", "run_"]:
			var name: String = prefix + direction
			if not frames.has_animation(name): continue
			frames.clear(name)
			for texture: Texture2D in cells:
				texture.set_meta("body_height", fitted.get_meta("body_height", 0))
				# Right-only art walks left mirrored, the way fit() mirrors its idle.
				texture.set_meta("explicit_direction", not mirror_left)
				frames.add_frame(name, texture)

## The frame of a walk animation for the distance walked: one step per half cycle, whatever the frame count.
static func frame_for(frames: SpriteFrames, animation: StringName, travelled: float, running: bool) -> int:
	var count: int = maxi(1, frames.get_frame_count(animation))
	return floori(travelled * count / (RUN_CYCLE if running else CYCLE)) % count

## Holds a sprite on the walk frame for the distance it has covered.
static func step(sprite: AnimatedSprite2D, travelled: float, running: bool = false) -> void:
	sprite.pause()
	sprite.frame = frame_for(sprite.sprite_frames, sprite.animation, travelled, running)
