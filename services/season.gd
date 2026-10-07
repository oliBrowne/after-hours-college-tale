class_name NativeSeason
extends RefCounted
## The campus through the year. state.flags.season is "" (the painted look, early autumn), "fall",
## "winter" or "spring"; the story decides when it turns, this only makes the art follow it.
## Painted rooms carry variants in their manifest ("background_winter", a prop's "texture_fall",
## a battle's "near_spring", ...) made by tools/seasons/build_seasons.py; anything without a
## variant keeps its usual look. Backgrounds' season images are overlays (only the changed
## pixels, see overlay()); props and battle layers are whole images (see pick()). Weather (snowfall, a gust of leaves, petals) is drawn here.

const SEASONS: Array[String] = ["fall", "winter", "spring"]
const SNOW := Color("f2f6ff")
const FALL_LEAVES: Array[Color] = [Color("d0602a"), Color("a8322c"), Color("e2a63a"), Color("8c3a24"), Color("c4842c")]
const SPRING_PETALS: Array[Color] = [Color("fbe2ee"), Color("f4b6d0"), Color("ffffff"), Color("f8cadc")]

static var _layer_cache: Dictionary = {}

static func current(flags: Dictionary) -> String:
	var value: String = str(flags.get("season", ""))
	return value if value in SEASONS else ""

## The manifest value for `key` in this season: at dawn "<key>_dawn_<season>", then "<key>_dawn";
## otherwise "<key>_<season>", then plain `key`. Returns null when the key is missing.
static func pick(data: Dictionary, key: String, flags: Dictionary, dawn_aware: bool = true) -> Variant:
	var season: String = current(flags)
	if dawn_aware and bool(flags.get("dawn_started", false)) and data.has(key + "_dawn"):
		if season != "" and data.has(key + "_dawn_" + season): return data[key + "_dawn_" + season]
		return data[key + "_dawn"]
	if season != "" and data.has(key + "_" + season): return data[key + "_" + season]
	return data.get(key)

## A painted room's season layer: "<key>_<season>" (at dawn "<key>_dawn_<season>") is an overlay
## holding only the pixels the season changes, drawn over the image it was made from. Dawn with a
## season but no dawn layer keeps the plain dawn look. Returns null when there is none.
static func overlay(data: Dictionary, key: String, flags: Dictionary) -> Variant:
	var season: String = current(flags)
	if season == "": return null
	if bool(flags.get("dawn_started", false)) and data.has(key + "_dawn"):
		return data.get(key + "_dawn_" + season)
	return data.get(key + "_" + season)

## How many leaves fall per manifest "leaves" area: none from bare winter trees, a lot in deep fall.
static func leaf_count(flags: Dictionary) -> int:
	match current(flags):
		"winter", "spring": return 0
		"fall": return 15
	return 7

static func leaf_colors(flags: Dictionary, normal: Array[Color]) -> Array[Color]:
	return FALL_LEAVES if current(flags) == "fall" else normal

## Animated layers adjusted for the season: blowing leaves become petals in spring, thicken in
## fall and stop in winter. Cached per list and season.
static func adapt_layers(layers: Array, flags: Dictionary) -> Array:
	var season: String = current(flags)
	if season == "" or layers.is_empty(): return layers
	var key: String = "%d:%s" % [layers.hash(), season]
	if _layer_cache.has(key): return _layer_cache[key]
	var out: Array = []
	for layer: Dictionary in layers:
		if str(layer.get("kind", "")) == "particles" and str(layer.get("style", "leaf")) == "leaf":
			if season == "winter": continue
			var changed: Dictionary = layer.duplicate()
			if season == "fall": changed["count"] = int(layer.get("count", 8)) * 2
			else: changed["style"] = "petal"; changed["count"] = maxi(3, int(layer.get("count", 8)) / 2)
			out.append(changed)
		else:
			out.append(layer)
	_layer_cache[key] = out
	return out

static func _h(i: int, salt: int) -> float:
	return fposmod(sin(float(i) * 12.9898 + float(salt) * 78.233) * 43758.5453, 1.0)

## Weather over a painted room or battle backdrop of `size`, under the actors: snowfall in three
## depths (far flakes small, faint and slow; near ones 2px and quicker), a wind of leaves in fall,
## petals drifting out of the trees (`areas`, the manifest's leaves rects) in spring. Reduced
## motion keeps a still, sparser snowfall and no drifting leaves or petals.
static func draw_weather(canvas: CanvasItem, flags: Dictionary, t: float, reduced_motion: bool, size: Vector2, areas: Array = []) -> void:
	var season: String = current(flags)
	if season == "winter": _snow(canvas, t, reduced_motion, size)
	elif season == "fall" and not reduced_motion: _gust(canvas, t, size)
	elif season == "spring" and not reduced_motion: _petals(canvas, t, areas)

static func _snow(c: CanvasItem, t: float, still: bool, size: Vector2) -> void:
	var area: float = size.x * size.y
	# depth: [count per 10k px, size, speed px/s, sway px, alpha]
	var depths: Array = [[3.2, 1.0, 9.0, 2.0, 0.42], [1.7, 1.0, 15.0, 3.0, 0.7], [0.55, 2.0, 26.0, 5.0, 0.92]]
	for d: int in depths.size():
		var spec: Array = depths[d]
		var count: int = int(area / 10000.0 * float(spec[0]) * (0.5 if still else 1.0))
		var flake: float = float(spec[1])
		if still and flake > 1.0: continue
		var colour := Color(SNOW, float(spec[4]))
		for i: int in count:
			var seed: int = i * 3 + d * 7919
			var pace: float = 0.7 + 0.6 * _h(seed, 3)
			var span: float = size.y + 8.0
			var y: float = fposmod(_h(seed, 2) * span + t * float(spec[2]) * pace, span) - 4.0
			var x: float = fposmod(_h(seed, 1) * size.x + t * 3.0 * pace + sin(t * (0.6 + 0.5 * _h(seed, 5)) + _h(seed, 4) * TAU) * float(spec[3]), size.x)
			c.draw_rect(Rect2(Vector2(x, y).round(), Vector2(flake, flake)), colour)

static func _gust(c: CanvasItem, t: float, size: Vector2) -> void:
	var count: int = int(size.x / 48.0)
	for i: int in count:
		var pace: float = 0.7 + 0.6 * _h(i, 11)
		var run: float = size.x + 60.0
		var x: float = fposmod(_h(i, 12) * run + t * 34.0 * pace, run) - 30.0
		var y: float = fposmod(_h(i, 13) * size.y + t * 11.0 * pace, size.y) + sin(t * 2.3 + i) * 4.0
		var flat: bool = int(t * 5.0 + i) % 3 != 0
		c.draw_rect(Rect2(Vector2(x, y).round(), Vector2(2, 1) if flat else Vector2(1, 2)), FALL_LEAVES[i % FALL_LEAVES.size()])

static func _petals(c: CanvasItem, t: float, areas: Array) -> void:
	for a: int in areas.size():
		var area: Array = areas[a]
		for i: int in 5:
			var seed: int = a * 17 + i
			var h: float = float(area[3]) + 40.0
			var fall: float = fposmod(t * (6.0 + 3.0 * _h(seed, 21)) + _h(seed, 22) * h, h)
			var sway: float = sin(t * 1.1 + seed * 1.7) * 6.0
			var at := Vector2(float(area[0]) + _h(seed, 23) * float(area[2]) + sway + fall * 0.25, float(area[1]) + fall).round()
			c.draw_rect(Rect2(at, Vector2.ONE if int(t * 3.0 + i) % 4 != 0 else Vector2(2, 1)), SPRING_PETALS[seed % SPRING_PETALS.size()])
