class_name NativeTalkArt
extends RefCounted
## Mouth-open dialogue portraits drawn at native size (assets/art/talk/<speaker>-<face>.png, 64x64):
## while a line types out, the portrait flaps between its face and this one.
const DIR: String = "res://assets/art/talk/"
static var cache: Dictionary = {}

static func slug(speaker: String) -> String:
	return "val_boss" if speaker == "VAL" else speaker.to_lower().replace(" ", "_")

## The open-mouth version of a portrait face, at the size dialogue portraits are drawn (2x), or null.
static func portrait(speaker: String, face: int) -> Texture2D:
	var key: String = slug(speaker) + "-" + str(face)
	if cache.has(key): return cache[key]
	var texture: Texture2D = null
	if ResourceLoader.exists(DIR + key + ".png"):
		var image: Image = (load(DIR + key + ".png") as Texture2D).get_image()
		if image.is_compressed(): image.decompress()
		image.convert(Image.FORMAT_RGBA8)
		image.resize(image.get_width() * 2, image.get_height() * 2, Image.INTERPOLATE_NEAREST)
		texture = ImageTexture.create_from_image(image)
	cache[key] = texture
	return texture
