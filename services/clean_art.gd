class_name NativeCleanArt
extends RefCounted
## Clean pixel-art versions of the shrunk cast sprites, baked offline (tools/clean_art) from the exact
## image NativePixelCast makes, so every design detail stays where Astra put it. Looked up by the
## shrunk image's size and checksum; a sprite without a baked version is drawn as before.
## AH_NATIVE_DUMP=<folder> saves each shrunk image (and its source) there for the baker.
const ENABLED: bool = true
const DIR: String = "res://assets/art/native-clean/"
static var _dump: String = OS.get_environment("AH_NATIVE_DUMP")

static func key(image: Image) -> String:
	var ctx := HashingContext.new()
	ctx.start(HashingContext.HASH_MD5)
	ctx.update(image.get_data())
	return "%dx%d-%s" % [image.get_width(), image.get_height(), ctx.finish().hex_encode().substr(0, 16)]

static func dumping() -> bool:
	return _dump != ""

static func swap(image: Image, source: Image) -> Image:
	if not ENABLED and _dump == "": return image
	var k: String = key(image)
	if _dump != "":
		if not FileAccess.file_exists(_dump.path_join(k + ".png")):
			image.save_png(_dump.path_join(k + ".png"))
			source.save_png(_dump.path_join(k + "-src.png"))
	if not ENABLED: return image
	var path: String = DIR + k + ".png"
	if not ResourceLoader.exists(path): return image
	var baked: Image = (load(path) as Texture2D).get_image()
	if baked.is_compressed(): baked.decompress()
	baked.convert(Image.FORMAT_RGBA8)
	return baked if baked.get_size() == image.get_size() else image
