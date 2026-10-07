class_name NativeIdleArt
extends RefCounted
## Extra standing frames drawn at native size (assets/art/idle/<key>-<name>.png): a blink, two or more
## idle poses (glancing aside, hands in pockets, adjusting a cap...) and, for Walt, a slow lantern sway.
## The blink and sway frames are appended to the fitted idle_down animation after the base and
## breathing frames, where NativeIdleMotion picks among them. Each pose becomes a one-shot
## "fidget_down" ("fidget2_down", ...) that NativeNpcLife plays now and then: step in, hold, step out.
## Art whose canvas or foot no longer matches is skipped.
const DIR: String = "res://assets/art/idle/"
const POSES: Array[String] = ["pose1", "pose2", "pose3", "pose4"]

static func _texture(path: String, fitted: Texture2D) -> Texture2D:
	if not ResourceLoader.exists(path): return null
	var image: Image = (load(path) as Texture2D).get_image()
	if image.is_compressed(): image.decompress()
	image.convert(Image.FORMAT_RGBA8)
	if image.get_size() != Vector2i(fitted.get_size()): return null
	var texture := ImageTexture.create_from_image(image)
	for meta: StringName in ["foot", "body_height", "explicit_direction", "native_pixels"]:
		if fitted.has_meta(meta): texture.set_meta(meta, fitted.get_meta(meta))
	return texture

## Called by NativePixelCast.frames for raw frames tagged "idle_key" or "walk_key".
static func apply(frames: SpriteFrames, raw: SpriteFrames) -> void:
	var key: String = str(raw.get_meta("idle_key", raw.get_meta("walk_key", "")))
	if key.is_empty() or not frames.has_animation("idle_down"): return
	var fitted: Texture2D = frames.get_frame_texture("idle_down", 0)
	var extras: Dictionary = {"poses": [], "sway": []}
	var blink: Texture2D = _texture(DIR + key + "-blink.png", fitted)
	if blink != null:
		extras.blink = frames.get_frame_count("idle_down"); frames.add_frame("idle_down", blink)
	for pose: String in POSES:
		var texture: Texture2D = _texture(DIR + key + "-" + pose + ".png", fitted)
		if texture == null: continue
		var name: String = "fidget_down" if extras.poses.is_empty() else "fidget%d_down" % (extras.poses.size() + 1)
		if frames.has_animation(name): frames.remove_animation(name)
		frames.add_animation(name)
		frames.set_animation_loop(name, false)
		frames.set_animation_speed(name, 5.0)
		frames.add_frame(name, fitted, 1.0)
		frames.add_frame(name, texture, 12.0 + float(extras.poses.size() % 3) * 2.0)
		frames.add_frame(name, fitted, 1.0)
		extras.poses.append(name)
	for i: int in range(8):
		var sway: Texture2D = _texture(DIR + key + "-sway-" + str(i) + ".png", fitted)
		if sway == null: break
		extras.sway.append(frames.get_frame_count("idle_down")); frames.add_frame("idle_down", sway)
	if extras.has("blink") or not extras.poses.is_empty() or not extras.sway.is_empty(): frames.set_meta("idle_extras", extras)
