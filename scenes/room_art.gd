class_name NativeRoomArt
extends RefCounted
## Painted mid-resolution room art from assets/art/rooms/<ID>/manifest.json.
## Rooms without a manifest keep their procedural drawing.

const MANIFEST := "res://assets/art/rooms/%s/manifest.json"
const FAUNA_TEXTURE := "res://assets/art/rooms/fauna.png"
const FAUNA_REGIONS := "res://assets/art/rooms/fauna.json"
const LEAF_COLORS: Array[Color] = [Color("c8682e"), Color("a83c32"), Color("d9a441")]

static var manifests: Dictionary = {}
static var fauna_regions: Dictionary = {}
static var textures: Dictionary = {}

static func manifest(room_id: String) -> Dictionary:
	if not manifests.has(room_id):
		var data: Dictionary = {}
		var path: String = MANIFEST % room_id
		if FileAccess.file_exists(path):
			var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
			if parsed is Dictionary: data = parsed
		manifests[room_id] = data
	return manifests[room_id]

static func texture(path: String) -> Texture2D:
	if not textures.has(path): textures[path] = load(path)
	return textures[path]

static func prop_art(room_id: String, index: int) -> Dictionary:
	return manifest(room_id).get("props", {}).get(str(index), {})

static func label_only(room_id: String, index: int) -> bool:
	return float(index) in manifest(room_id).get("label_only", [])

## Painted pieces that sit in front of characters standing behind them (y-sorted on `base`).
static func occluders(room_id: String) -> Array[Node2D]:
	var nodes: Array[Node2D] = []
	for item: Dictionary in manifest(room_id).get("occluders", []):
		var sprite := Sprite2D.new()
		sprite.texture = texture(str(item.texture))
		sprite.centered = false
		sprite.position = Vector2(float(item.x), float(item.base))
		sprite.offset = Vector2(0, float(item.y) - float(item.base))
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		nodes.append(sprite)
	return nodes

static func draw_room(canvas: CanvasItem, room_id: String, elapsed: float, reduced_motion: bool, flags: Dictionary = {}) -> void:
	var art: Dictionary = manifest(room_id)
	var dawn: bool = bool(flags.get("dawn_started", false)) and art.has("background_dawn")
	canvas.draw_texture(texture(str(art.background_dawn if dawn else art.background)), Vector2.ZERO)
	# State overlays painted into the room: {texture, x, y, flag, and "equals" or "when" (default true)}.
	for overlay: Dictionary in art.get("overlays", []):
		if shows(overlay, flags): canvas.draw_texture(texture(str(overlay.texture)), Vector2(float(overlay.x), float(overlay.y)))
	var t: float = 0.0 if reduced_motion else elapsed
	for area: Array in art.get("leaves", []):
		for leaf: int in 7:
			var fall: float = fmod(t * (9.0 + leaf * 2.0) + leaf * 13.0, float(area[3]))
			var sway: float = sin(t * 1.3 + leaf * 2.1) * 4.0
			var at := Vector2(float(area[0]) + float((leaf * 23) % int(area[2])) + sway, float(area[1]) + fall).round()
			canvas.draw_rect(Rect2(at, Vector2(2, 1)), LEAF_COLORS[leaf % LEAF_COLORS.size()])
	draw_fauna(canvas, art.get("fauna", []), t, float(art.get("width", 640)))
	# Animated layers (screens, neon, spotlights), same kinds as battle backdrops; "flag" makes one conditional.
	var lt: float = 1.3 if reduced_motion else elapsed
	for layer: Dictionary in art.get("layers", []):
		if layer.has("flag") and not shows(layer, flags): continue
		NativeBattleBackdrop.draw_layer(canvas, layer, lt, float(art.get("width", 640)))

static func shows(overlay: Dictionary, flags: Dictionary) -> bool:
	var value: Variant = flags.get(str(overlay.flag), null)
	if overlay.has("equals"): return str(value) == str(overlay.equals)
	var set_: bool = bool(value) if value is bool else value != null and str(value) != ""
	return set_ == bool(overlay.get("when", true))

## Animals from fauna.png: walkers sway back and forth, "fly" ones cross the width and wrap.
static func draw_fauna(canvas: CanvasItem, animals: Array, t: float, width: float) -> void:
	if fauna_regions.is_empty() and FileAccess.file_exists(FAUNA_REGIONS):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FAUNA_REGIONS))
		if parsed is Dictionary: fauna_regions = parsed
	var sheet: Texture2D = texture(FAUNA_TEXTURE)
	for animal: Dictionary in animals:
		var region: Array = fauna_regions.get(str(animal.kind), [])
		if region.is_empty(): continue
		var size := Vector2(float(region[2]), float(region[3]))
		var frame: int = int(t * float(animal.get("rate", 1.0))) % int(region[4])
		var at := Vector2(float(animal.x), float(animal.y))
		var flip: bool = bool(animal.get("flip", false))
		if animal.has("fly"):
			at.x = fmod(at.x + t * float(animal.fly), width + 40.0) - 20.0
			at.y += roundf(sin(t * 0.9 + at.x * 0.01) * 3.0)
		else:
			var swing: float = sin(t * float(animal.get("speed", 0.0)))
			at.x += roundf(swing * float(animal.get("range", 0.0)))
			if float(animal.get("range", 0.0)) > 0.0 and cos(t * float(animal.get("speed", 0.0))) < 0.0: flip = not flip
		var rect := Rect2((at - Vector2(size.x / 2.0, size.y)).round(), size)
		if flip:
			canvas.draw_set_transform(Vector2(rect.position.x * 2.0 + size.x, 0), 0.0, Vector2(-1, 1))
		canvas.draw_texture_rect_region(sheet, rect, Rect2(float(region[0]) + frame * size.x, float(region[1]), size.x, size.y))
		if flip: canvas.draw_set_transform(Vector2.ZERO)
