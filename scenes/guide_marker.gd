class_name NativeGuideMarker
extends Node2D
## The "go here next" marker: a mint chevron bobbing over the next door or person,
## or an arrow at the screen edge pointing toward it. After Pip joins, Pip's glove
## does the pointing.
const MINT: Color = Color("b9d5bc")
const AMBER: Color = Color("e8b45c")
const INK: Color = Color("0d101c")
var game: Node

func _process(_delta: float) -> void:
	queue_redraw()

func _draw() -> void:
	if game == null or int(game.mode) != 1 or not game.world.visible or NativeJakerson.busy() or NativeRoomScenes.busy() or NativeJakerson.guide(game) == "walk": return
	var goal: Dictionary = NativeGuide.target(game)
	if goal.is_empty(): return
	var point: Vector2 = goal.point
	if game.player.position.distance_to(point) < 34.0: return
	var reduced: bool = bool(game.state.settings.reducedMotion)
	var t: float = Time.get_ticks_msec() / 1000.0
	var bob: float = 0.0 if reduced else roundf(sin(t * 4.0) * 3.0)
	var pip: bool = bool(game.state.flags.get("pip_joined", false))
	var colour: Color = AMBER if pip else MINT
	var centre: Vector2 = game.camera.get_screen_center_position()
	var view: Rect2 = Rect2(centre - Vector2(320, 180), Vector2(640, 360))
	var tip: Vector2 = point + Vector2(0, -50 - bob)
	if view.grow(-12).has_point(tip):
		_chevron(tip, Vector2.DOWN, colour, pip)
		return
	# Off screen: an arrow on the edge, on the line from the player toward it.
	var inner: Rect2 = view.grow(-26)
	var from: Vector2 = game.player.position.clamp(inner.position, inner.end)
	var dir: Vector2 = (point - from).normalized()
	var scale_x: float = INF if absf(dir.x) < 0.001 else ((inner.end.x if dir.x > 0 else inner.position.x) - from.x) / dir.x
	var scale_y: float = INF if absf(dir.y) < 0.001 else ((inner.end.y if dir.y > 0 else inner.position.y) - from.y) / dir.y
	var at: Vector2 = from + dir * minf(scale_x, scale_y) - dir * bob
	_chevron(at, dir, colour, pip)

func _chevron(at: Vector2, dir: Vector2, colour: Color, pip: bool) -> void:
	var side: Vector2 = Vector2(-dir.y, dir.x)
	var points: PackedVector2Array = PackedVector2Array([at + dir * 8.0, at - dir * 4.0 + side * 8.0, at - dir * 1.0, at - dir * 4.0 - side * 8.0])
	var outline: PackedVector2Array = PackedVector2Array([at + dir * 10.5, at - dir * 5.5 + side * 10.5, at - dir * 2.0, at - dir * 5.5 - side * 10.5])
	draw_colored_polygon(outline, INK)
	draw_colored_polygon(points, colour)
	if pip:
		# Pip's glove behind the arrow, pointing.
		var palm: Vector2 = at - dir * 13.0
		draw_circle(palm, 5.0, INK)
		draw_circle(palm, 4.0, Color("e6d6b1"))
		draw_line(palm, palm + dir * 6.0, Color("e6d6b1"), 2.0)
