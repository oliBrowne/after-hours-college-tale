class_name NativeBattleBackdrop
extends Node2D
## A room's own painted battle backdrop (the "battle" section of its art manifest): the far image,
## layers that move behind the scenery (clouds, birds), the near image with the sky cut out, then
## layers in front (leaves, lamp glow, spotlights, neon). Rooms without one keep the dimmed room view.

const LEAF_COLORS: Array[Color] = [Color("c8682e"), Color("a83c32"), Color("d9a441"), Color("8c4a2a")]

var spec: Dictionary = {}
var elapsed: float = 0.0
var reduced_motion: bool = false

static func available(room_id: String) -> bool:
	return NativeRoomArt.manifest(room_id).has("battle")

func configure(room_id: String, flags: Dictionary = {}) -> void:
	spec = NativeRoomArt.manifest(room_id).get("battle", {}).duplicate()
	# Dawn variants replace the night images once the sun is up.
	if bool(flags.get("dawn_started", false)):
		for key: String in ["far", "near"]:
			if spec.has(key + "_dawn"): spec[key] = spec[key + "_dawn"]
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	queue_redraw()

func step(delta: float) -> void:
	elapsed += delta
	if is_visible_in_tree(): queue_redraw()

func _draw() -> void:
	if spec.is_empty(): return
	# Reduced motion holds one still frame, picked so lights read as lit.
	var t: float = 1.3 if reduced_motion else elapsed
	draw_texture(NativeRoomArt.texture(str(spec.far)), Vector2.ZERO)
	_draw_layers("far", t)
	if spec.has("near"): draw_texture(NativeRoomArt.texture(str(spec.near)), Vector2.ZERO)
	_draw_layers("near", t)

func _draw_layers(depth: String, t: float) -> void:
	for layer: Dictionary in spec.get("layers", []):
		if str(layer.get("depth", "near")) == depth: draw_layer(self, layer, t, 640.0)

## Draws one animated layer; rooms use the same kinds in their manifest "layers".
static func draw_layer(c: CanvasItem, layer: Dictionary, t: float, width: float) -> void:
	match str(layer.kind):
		"drift": _drift(c, layer, t, width)
		"fauna": NativeRoomArt.draw_fauna(c, layer.get("fauna", []), t, width)
		"twinkle": _twinkle(c, layer, t)
		"blink": _blink(c, layer, t)
		"beam": _beam(c, layer, t)
		"particles": _particles(c, layer, t)
		"movers": _movers(c, layer, t)

static func _h(i: int, salt: int) -> float:
	return fposmod(sin(float(i) * 12.9898 + float(salt) * 78.233) * 43758.5453, 1.0)

static func _color(value: Variant, alpha: float = 1.0) -> Color:
	var c := Color(str(value))
	c.a *= alpha
	return c

## A strip that scrolls sideways and wraps (clouds, haze).
static func _drift(c: CanvasItem, layer: Dictionary, t: float, width: float) -> void:
	var tex: Texture2D = NativeRoomArt.texture(str(layer.texture))
	var w: float = float(tex.get_width())
	var x: float = roundf(fposmod(t * float(layer.get("speed", 0.0)), w)) - w
	var tint := Color(1, 1, 1, float(layer.get("alpha", 1.0)))
	while x < width:
		c.draw_texture(tex, Vector2(x, float(layer.get("y", 0))), tint)
		x += w

## Lamps and bulbs that breathe: [x, y, colour, size] each, alpha stepped so it stays pixel-crisp.
static func _twinkle(c: CanvasItem, layer: Dictionary, t: float) -> void:
	var low: float = float(layer.get("min", 0.4))
	var rate: float = float(layer.get("rate", 1.0))
	var points: Array = layer.get("points", [])
	for i: int in points.size():
		var p: Array = points[i]
		var wave: float = 0.5 + 0.5 * sin(t * rate * (0.8 + 0.4 * _h(i, 3)) + _h(i, 1) * TAU)
		var a: float = snappedf(low + (1.0 - low) * wave, 0.25)
		var size: float = float(p[3]) if p.size() > 3 else 1.0
		var at := Vector2(float(p[0]), float(p[1]))
		c.draw_rect(Rect2(at - Vector2(size + 1, size + 1), Vector2(size * 2 + 2, size * 2 + 2)), _color(p[2], a * 0.22))
		c.draw_rect(Rect2(at - Vector2(size, 0), Vector2(size * 2, 1)), _color(p[2], a * 0.5))
		c.draw_rect(Rect2(at - Vector2(0, size), Vector2(1, size * 2)), _color(p[2], a * 0.5))
		c.draw_rect(Rect2(at, Vector2.ONE), _color(p[2], minf(1.0, a + 0.25)))

## On/off frames (neon letters, a traffic light): shown while pattern[int(t * rate) % len] is "1".
static func _blink(c: CanvasItem, layer: Dictionary, t: float) -> void:
	var pattern: String = str(layer.get("pattern", "1"))
	var on: bool = pattern[int(t * float(layer.get("rate", 1.0))) % pattern.length()] == "1"
	if not on: return
	if layer.has("texture"):
		c.draw_texture(NativeRoomArt.texture(str(layer.texture)), Vector2(float(layer.get("x", 0)), float(layer.get("y", 0))))
	for r: Array in layer.get("rects", []):
		c.draw_rect(Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])), _color(r[4], float(r[5]) if r.size() > 5 else 1.0))

## A swinging spotlight: three nested bands from the lamp to a pool on the floor.
static func _beam(c: CanvasItem, layer: Dictionary, t: float) -> void:
	var origin := Vector2(float(layer.x), float(layer.y))
	var swing: float = sin(t * TAU / maxf(0.1, float(layer.get("period", 6.0))) + float(layer.get("phase", 0.0)))
	var angle: float = deg_to_rad(float(layer.get("angle", 90.0)) + float(layer.get("sweep", 0.0)) * swing)
	var dir := Vector2(cos(angle), sin(angle))
	var side := Vector2(-dir.y, dir.x)
	var length: float = float(layer.get("length", 150.0))
	var width: float = float(layer.get("width", 50.0))
	var alpha: float = float(layer.get("alpha", 0.2))
	var tip: Vector2 = origin + dir * length
	for band: int in 3:
		var f: float = 1.0 - band * 0.3
		var poly := PackedVector2Array([origin - side * 2.0 * f, origin + side * 2.0 * f, tip + side * width * 0.5 * f, tip - side * width * 0.5 * f])
		c.draw_colored_polygon(poly, _color(layer.get("color", "fff0c4"), alpha / 3.0))
	var pool_y: float = float(layer.get("floor", tip.y))
	var pool_x: float = origin.x + (pool_y - origin.y) * dir.x / maxf(0.05, dir.y)
	for band: int in 3:
		var r: float = width * 0.5 * (1.0 - band * 0.28)
		c.draw_set_transform(Vector2(pool_x, pool_y), 0.0, Vector2(1.0, 0.22))
		c.draw_circle(Vector2.ZERO, r, _color(layer.get("color", "fff0c4"), alpha * 0.45))
	c.draw_set_transform(Vector2.ZERO)

## Leaves blowing through, wind streaks, dust motes in a light.
static func _particles(c: CanvasItem, layer: Dictionary, t: float) -> void:
	var rect: Array = layer.get("rect", [0, 0, 640, 360])
	var area := Rect2(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
	var speed: Array = layer.get("speed", [20, 10])
	var style: String = str(layer.get("style", "leaf"))
	for i: int in int(layer.get("count", 8)):
		var pace: float = 0.75 + 0.5 * _h(i, 7)
		match style:
			"leaf":
				var p: float = fposmod(t * float(speed[0]) * pace / area.size.x + _h(i, 2), 1.0)
				var y: float = fposmod(_h(i, 4) * area.size.y + t * float(speed[1]) * pace, area.size.y)
				var at := (area.position + Vector2(p * area.size.x, y + sin(t * 2.1 + i) * 3.0)).round()
				var flat: bool = int(t * 5.0 + i) % 3 != 0
				c.draw_rect(Rect2(at, Vector2(2, 1) if flat else Vector2(1, 2)), LEAF_COLORS[i % LEAF_COLORS.size()])
			"wind":
				var run: float = area.size.x * 2.0
				var x: float = fposmod(t * float(speed[0]) * pace + _h(i, 5) * run, run)
				if x > area.size.x: continue
				var length: float = 18.0 + 26.0 * _h(i, 6)
				var y: float = area.position.y + _h(i, 8) * area.size.y + sin(t * 1.4 + i) * 2.0
				c.draw_rect(Rect2(Vector2(area.position.x + x, y).round(), Vector2(length, 1)), Color(1, 0.94, 0.86, 0.22))
				c.draw_rect(Rect2(Vector2(area.position.x + x + length * 0.3, y + 1).round(), Vector2(length * 0.4, 1)), Color(1, 0.94, 0.86, 0.12))
			"dust":
				var y: float = area.end.y - fposmod(t * float(speed[1]) * pace + _h(i, 4) * area.size.y, area.size.y)
				var x: float = area.position.x + _h(i, 2) * area.size.x + sin(t * 0.7 + i) * 4.0
				var a: float = snappedf(0.25 + 0.5 * (0.5 + 0.5 * sin(t * 2.0 + i * 1.3)), 0.25)
				c.draw_rect(Rect2(Vector2(x, y).round(), Vector2.ONE), _color(layer.get("color", "fff0c4"), a))

## Car lights running along a road toward the viewer: they grow as they come closer.
static func _movers(c: CanvasItem, layer: Dictionary, t: float) -> void:
	var from := Vector2(float(layer.from[0]), float(layer.from[1]))
	var to := Vector2(float(layer.to[0]), float(layer.to[1]))
	var count: int = int(layer.get("count", 2))
	var size: Array = layer.get("size", [1, 4])
	var gap: float = float(layer.get("pair", 0.0))
	for i: int in count:
		var p: float = fposmod(t / float(layer.get("period", 8.0)) + float(i) / count + _h(i, 9) * 0.3, 1.0)
		var q: float = p * p if str(layer.get("ease", "in")) == "in" else 1.0 - (1.0 - p) * (1.0 - p)
		var at: Vector2 = from.lerp(to, q)
		var s: float = maxf(1.0, roundf(lerpf(float(size[0]), float(size[1]), q)))
		var a: float = clampf(p * 6.0, 0.0, 1.0) * clampf((1.0 - p) * 8.0, 0.0, 1.0)
		var colour: Color = _color(layer.get("color", "fff0c4"), snappedf(a, 0.25))
		var spread: float = roundf(gap * q * 0.5)
		for k: int in ([-1, 1] if gap > 0.0 else [0]):
			c.draw_rect(Rect2((at + Vector2(k * spread - s * 0.5, -s * 0.25)).round(), Vector2(s, maxf(1.0, roundf(s * 0.5)))), colour)
