class_name NativeMinimapView
extends Control
## Draws the room schematic (see services/minimap.gd). `full` is the pause-menu map, where rooms
## can be picked with the mouse or arrow keys; otherwise it is the small corner minimap that
## follows the player during exploration.
signal picked(room: String)
const NODE: Vector2 = Vector2(25, 15)
const GOLD: Color = Color("ffd25e")
const INK: Color = Color("0d101c")
const EDGE: Color = Color("5a4f70")
const EDGE_LOCKED: Color = Color("3d3552")
const MINT: Color = Color("b9d5bc")
const CREAM: Color = Color("e6d6b1")
const SKY: Color = Color("7fc4ff")
var game: Node
var full: bool = false
var selected: String = ""
var shift: Vector2 = Vector2(14, 8)

func setup(controller: Node, is_full: bool) -> void:
	game = controller
	full = is_full
	mouse_filter = Control.MOUSE_FILTER_STOP if full else Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	if not full: size = Vector2(116, 74)

func _process(_delta: float) -> void:
	if game == null: return
	if not full:
		visible = corner_visible()
	if visible: queue_redraw()

func corner_visible() -> bool:
	return int(game.mode) == 1 and game.world.visible and not game.pause_context and not NativeJakerson.busy() and not NativeRoomScenes.busy() and NativeJakerson.guide(game) != "walk" and not bool(game.state.flags.get("minimap_off", false))

func scale_factor() -> float:
	return 1.0 if full else 0.5

func offset() -> Vector2:
	if full: return shift
	return size / 2.0 - (NativeMinimap.point(str(game.state.room)) + NODE / 2.0) * scale_factor()

func node_rect(room: String) -> Rect2:
	return Rect2(NativeMinimap.point(room) * scale_factor() + offset(), NODE * scale_factor())

func _gui_input(event: InputEvent) -> void:
	if not full or not (event is InputEventMouseButton or event is InputEventMouseMotion): return
	if event is InputEventMouseButton and not (event.pressed and event.button_index == MOUSE_BUTTON_LEFT): return
	for room: String in NativeMinimap.POS:
		if game.rooms.has(room) and node_rect(room).grow(2).has_point(event.position):
			select(room, event is InputEventMouseButton)
			return

func select(room: String, clicked: bool = false) -> void:
	if room == selected and not clicked: return
	selected = room
	picked.emit(room)
	queue_redraw()

## Arrow-key movement: the nearest known room in that direction.
func move(direction: Vector2) -> void:
	var from: Vector2 = NativeMinimap.point(selected)
	var best: String = ""
	var best_score: float = INF
	for room: String in NativeMinimap.POS:
		if room == selected or not game.rooms.has(room) or not NativeMinimap.known(game, room): continue
		var delta: Vector2 = NativeMinimap.point(room) - from
		var along: float = delta.dot(direction)
		if along <= 1.0: continue
		var score: float = along + absf(delta.dot(Vector2(-direction.y, direction.x))) * 2.2
		if score < best_score: best_score = score; best = room
	if not best.is_empty(): select(best)

func _draw() -> void:
	if game == null or not game.rooms.has(game.state.room): return
	var here: String = str(game.state.room)
	var plan: Dictionary = NativeMinimap.plan(game)
	var route: Array = plan.route
	var t: float = Time.get_ticks_msec() / 1000.0
	var calm: bool = bool(game.state.settings.reducedMotion)
	var pulse: float = 0.5 if calm else 0.5 + 0.5 * sin(t * 5.0)
	if not full:
		draw_rect(Rect2(Vector2.ZERO, size), Color(INK, 0.82))
		draw_rect(Rect2(Vector2.ZERO, size), EDGE_LOCKED, false, 1.0)
	var edge_width: float = 1.0 if not full else 1.5
	for e: Array in NativeMinimap.edges(game):
		if not NativeMinimap.visited(game, e[0]) and not NativeMinimap.visited(game, e[1]): continue
		# Long hub spokes only show when they are part of the route.
		if NativeMinimap.point(e[0]).distance_to(NativeMinimap.point(e[1])) > 100.0: continue
		var a: Vector2 = node_rect(e[0]).get_center()
		var b: Vector2 = node_rect(e[1]).get_center()
		draw_line(a, b, EDGE if e[2] else EDGE_LOCKED, edge_width)
	for i: int in range(route.size() - 1):
		draw_line(node_rect(route[i]).get_center(), node_rect(route[i + 1]).get_center(), Color(GOLD, 0.55 + 0.45 * pulse), 2.0 if full else 1.5)
	for room: String in NativeMinimap.POS:
		if game.rooms.has(room): draw_room(room, here, plan, pulse)
	if not full: draw_corner_extras(here, plan)

func draw_room(room: String, here: String, plan: Dictionary, pulse: float) -> void:
	var r: Rect2 = node_rect(room)
	if not Rect2(Vector2.ZERO, size).grow(NODE.x).intersects(r): return
	var colour: Color = NativeMinimap.tint(room)
	var target: bool = not plan.goal.is_empty() and str(plan.goal.room) == room
	if not NativeMinimap.known(game, room):
		draw_rect(Rect2(r.get_center() - Vector2(2, 2), Vector2(4, 4)), EDGE_LOCKED)
		return
	var seen: bool = NativeMinimap.visited(game, room)
	if room == here:
		draw_rect(r, Color(GOLD, 0.35 + 0.3 * pulse))
		draw_rect(r, Color.WHITE, false, 2.0 if full else 1.0)
	elif seen:
		draw_rect(r, Color(colour, 0.3))
		draw_rect(r, colour, false, 1.0)
	else:
		draw_rect(r, Color(colour, 0.08))
		draw_rect(r, Color(colour, 0.6), false, 1.0)
	if target and room != here:
		draw_rect(r.grow(1.0), Color(GOLD, 0.5 + 0.5 * pulse), false, 2.0 if full else 1.0)
	if full:
		var text: String = room if seen else "?"
		draw_string(game.font, Vector2(r.position.x, r.position.y + 12), text, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, 12, CREAM if seen else Color(colour, 0.8))
		if room == selected: draw_rect(r.grow(3.0), Color.WHITE, false, 1.0)
	# Blue pips: people here you have not talked to yet.
	var waiting: int = mini(3, NativeMinimap.unspoken(game, room)) if seen else 0
	for i: int in range(waiting):
		var pip: float = 3.0 if full else 2.0
		draw_rect(Rect2(r.position + Vector2(2 + i * (pip + 1.0), r.size.y - pip - 1.0), Vector2(pip, pip)), SKY)
	if target:
		var lift: float = 0.0 if bool(game.state.settings.reducedMotion) else roundf(sin(Time.get_ticks_msec() / 220.0) * 2.0)
		var top: Vector2 = r.position + Vector2(r.size.x - 4.0, -6.0 + lift)
		draw_string(game.font, top, "!", HORIZONTAL_ALIGNMENT_LEFT, -1, 12 if full else 10, GOLD)

## Corner only: the objective's name, and an edge arrow when the target room is off the little screen.
func draw_corner_extras(_here: String, plan: Dictionary) -> void:
	if plan.goal.is_empty(): return
	var r: Rect2 = node_rect(str(plan.goal.room))
	var view: Rect2 = Rect2(Vector2(6, 6), size - Vector2(12, 12))
	if not view.intersects(r):
		var centre: Vector2 = size / 2.0
		var dir: Vector2 = (r.get_center() - centre).normalized()
		var sx: float = INF if absf(dir.x) < 0.001 else ((view.end.x if dir.x > 0 else view.position.x) - centre.x) / dir.x
		var sy: float = INF if absf(dir.y) < 0.001 else ((view.end.y if dir.y > 0 else view.position.y) - centre.y) / dir.y
		var at: Vector2 = centre + dir * minf(sx, sy)
		var side: Vector2 = Vector2(-dir.y, dir.x)
		draw_colored_polygon(PackedVector2Array([at + dir * 5.0, at - dir * 3.0 + side * 4.0, at - dir * 3.0 - side * 4.0]), GOLD)
	var line: String = "> " + str(plan.goal.name)
	draw_rect(Rect2(0, size.y - 14, size.x, 14), Color(INK, 0.9))
	draw_string(game.font, Vector2(3, size.y - 3), line, HORIZONTAL_ALIGNMENT_LEFT, size.x - 6, 12, GOLD)
