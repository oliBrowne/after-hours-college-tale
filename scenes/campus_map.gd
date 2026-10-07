class_name NativeCampusMap
extends Control
## The pause-menu campus map: every room as a node on a schematic joined by its doors, with the
## player's room, the route to the current objective and the people still to talk to marked.
## Pick rooms with the mouse or arrow keys; the panel below lists who is there and where the doors go.
var game: Node
var view: NativeMinimapView
var selected_room: String = ""
var header: Label
var next_line: Label
var room_line: Label
var people_line: Label
var doors_line: Label
var toggle: Button

func configure(controller: Node) -> void:
	game = controller
	position = Vector2(8, 8); size = Vector2(624, 344); z_index = 510
	var background := Panel.new()
	background.size = size
	background.add_theme_stylebox_override("panel", game.style_panel())
	add_child(background)
	header = make_label(Vector2(12, 6), Vector2(220, 16), "CAMPUS MAP", game.MINT)
	next_line = make_label(Vector2(150, 6), Vector2(460, 16), "", game.AMBER)
	view = NativeMinimapView.new()
	view.setup(game, true)
	view.position = Vector2(8, 26); view.size = Vector2(608, 218)
	view.picked.connect(show_room)
	add_child(view)
	var split := ColorRect.new()
	split.color = game.LINE; split.position = Vector2(8, 248); split.size = Vector2(608, 1)
	add_child(split)
	room_line = make_label(Vector2(12, 252), Vector2(300, 16), "", game.CREAM)
	people_line = make_label(Vector2(12, 268), Vector2(290, 70), "", game.CREAM)
	doors_line = make_label(Vector2(310, 268), Vector2(180, 70), "", game.CREAM)
	toggle = make_button("Minimap: on", Vector2(500, 266), Vector2(116, 23), toggle_minimap)
	make_button("Close map", Vector2(500, 294), Vector2(116, 23), game.close_map)
	var legend := make_label(Vector2(500, 322), Vector2(120, 16), "! next  blue = talk", game.MUTED)
	legend.add_theme_font_size_override("font_size", 12)

func make_label(at: Vector2, span: Vector2, value: String, colour: Color) -> Label:
	var label := Label.new()
	label.text = value; label.position = at; label.size = span
	label.add_theme_font_override("font", game.font); label.add_theme_font_size_override("font_size", 12)
	label.add_theme_color_override("font_color", colour)
	label.clip_text = true
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(label)
	return label

func make_button(value: String, at: Vector2, span: Vector2, callback: Callable) -> Button:
	var button := Button.new(); button.text = value; button.position = at; button.size = span
	button.add_theme_font_override("font", game.font); button.add_theme_font_size_override("font_size", 12)
	button.add_theme_stylebox_override("normal", game.style_panel())
	var hover: StyleBoxFlat = game.style_panel(); hover.bg_color = Color("51425a")
	button.add_theme_stylebox_override("hover", hover); button.add_theme_stylebox_override("focus", hover)
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.focus_mode = Control.FOCUS_NONE
	button.pressed.connect(callback); add_child(button)
	return button

func toggle_minimap() -> void:
	game.state.flags["minimap_off"] = not bool(game.state.flags.get("minimap_off", false))
	refresh_toggle()

func refresh_toggle() -> void:
	toggle.text = "Minimap: " + ("off" if bool(game.state.flags.get("minimap_off", false)) else "on")

func refresh() -> void:
	refresh_toggle()
	next_line.text = "NEXT: " + game.objective()
	selected_room = str(game.state.room)
	view.select(selected_room, true)
	show_room(selected_room)

func show_room(room: String) -> void:
	selected_room = room
	if not game.rooms.has(room): return
	var seen: bool = NativeMinimap.visited(game, room)
	var status: String = "You are here" if str(game.state.room) == room else "Explored" if seen else "Not explored yet"
	var plan: Dictionary = NativeMinimap.plan(game)
	if not plan.goal.is_empty() and str(plan.goal.room) == room: status += " / go here next"
	room_line.text = "%s  (%s)" % [NativeMinimap.short_name(game.rooms[room].name) if seen or NativeMinimap.known(game, room) else "Unknown", status]
	var lines: Array[String] = []
	if seen:
		for p: Dictionary in NativeMinimap.people(game, room):
			var mark: String = "!" if p.next else "x" if p.boss else "-" if p.spoken else "*"
			lines.append("%s %s" % [mark, p.name])
	people_line.text = "People:\n" + ("\n".join(lines.slice(0, 3)) if not lines.is_empty() else ("none" if seen else "go there to find out"))
	var doors: Array[String] = []
	if seen:
		for o: Dictionary in game.rooms[room].objects:
			if str(o.get("kind", "")) != "door" or not game.rooms.has(str(o.get("to", ""))): continue
			doors.append(NativeMinimap.short_name(game.rooms[str(o.to)].name) + ("" if NativeMinimap.door_open(game, o) else " (locked)"))
	doors_line.text = "Doors:\n" + ("\n".join(doors.slice(0, 3)) if not doors.is_empty() else "")

func key(event: InputEvent) -> void:
	var dirs: Dictionary = {"move_up": Vector2.UP, "move_down": Vector2.DOWN, "move_left": Vector2.LEFT, "move_right": Vector2.RIGHT}
	for action: String in dirs:
		if event.is_action_pressed(action):
			view.move(dirs[action])
			get_viewport().set_input_as_handled()
			return
	if event.is_action_pressed("confirm"):
		view.select(str(game.state.room), true)
		get_viewport().set_input_as_handled()

func _exit_tree() -> void: game = null
