class_name NativeControlOverlay
extends Control

var game: Node
var map_button: Button
var pause_button: Button
var back_button: Button
var action_button: Button
var duck_button: Button
var left_button: Button
var right_button: Button
var controls: Array[Button] = []

func configure(controller: Node) -> void:
	game = controller
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	map_button = make_button("Map", Rect2(516, 10, 52, 20), game.open_map)
	pause_button = make_button("Pause", Rect2(574, 10, 54, 20), game.open_pause)
	back_button = make_button("Back", Rect2(88, 306, 464, 23), back)
	action_button = make_button("Push paper", Rect2(232, 291, 176, 22), func() -> void: defend())
	make_duck_button()
	left_button = make_button("Hop left", Rect2(192, 291, 124, 22), func() -> void: hop(-1))
	right_button = make_button("Hop right", Rect2(324, 291, 124, 22), func() -> void: hop(1))
	update_state()

func make_duck_button() -> void:
	duck_button = make_button("Hold duck", Rect2(324, 291, 124, 22), func() -> void:
		if game.mode == game.Mode.DODGE and game.resume_ticks == 0: game.pointer_duck = true)
	duck_button.button_down.connect(func() -> void:
		if game.mode == game.Mode.DODGE and game.resume_ticks == 0: game.pointer_duck = true)
	duck_button.button_up.connect(func() -> void: game.pointer_duck = false)

func clear_held_input() -> void:
	# Keep the widget through UI redraws, but discard Godot's retained press
	# state at focus/pause/retry/exit boundaries as well as the gameplay latch.
	if not is_instance_valid(duck_button): return
	controls.erase(duck_button)
	duck_button.hide(); duck_button.queue_free()
	make_duck_button()
	update_state()

func make_button(value: String, rect: Rect2, callback: Callable) -> Button:
	var button := Button.new()
	button.text = value; button.position = rect.position; button.size = rect.size
	button.add_theme_font_override("font", game.font)
	button.add_theme_font_size_override("font_size", 12)
	button.add_theme_color_override("font_color", game.CREAM)
	button.add_theme_color_override("font_hover_color", Color.WHITE)
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(game.INK, 0.94); normal.border_color = game.LINE; normal.set_border_width_all(1)
	normal.set_corner_radius_all(3); normal.anti_aliasing = false
	normal.content_margin_left = 6; normal.content_margin_right = 6; normal.content_margin_top = 0; normal.content_margin_bottom = 0
	var hover: StyleBoxFlat = normal.duplicate()
	hover.bg_color = Color("51425a"); hover.border_color = game.AMBER
	button.add_theme_stylebox_override("normal", normal)
	button.add_theme_stylebox_override("hover", hover); button.add_theme_stylebox_override("pressed", hover)
	button.add_theme_stylebox_override("disabled", normal); button.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	button.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
	button.focus_mode = Control.FOCUS_NONE
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.pressed.connect(callback)
	add_child(button); controls.append(button)
	button.update_minimum_size(); button.size = rect.size
	return button

func owns(point: Vector2) -> bool:
	for button: Button in controls:
		if button.is_visible_in_tree() and button.get_global_rect().has_point(point): return true
	return false

func back() -> void:
	if not game.binding_capture.is_empty():
		game.binding_capture = ""; game.remap_menu(); return
	for option: Dictionary in game.menu_options:
		if option.label == "Back": option.run.call(); return

func defend() -> void:
	if game.mode == game.Mode.DODGE and game.resume_ticks == 0: game.beat_defend = true

func hop(direction: int) -> void:
	if game.mode == game.Mode.DODGE and game.resume_ticks == 0: game.pointer_hop = direction

func update_state() -> void:
	if game == null: return
	map_button.visible = game.mode == game.Mode.WORLD and not game.pause_context
	pause_button.visible = game.mode in [game.Mode.WORLD, game.Mode.DIALOGUE, game.Mode.BATTLE, game.Mode.TIMING, game.Mode.TELEGRAPH, game.Mode.DODGE, game.Mode.RESOLVE, game.Mode.INTRO] and not game.pause_context
	pause_button.position = Vector2(12, 10) if not game.world.visible else Vector2(574, 10)
	var party: bool = game.pause_context and game.mode == game.Mode.MENU and (game.caption.begins_with("Party") or game.party_caption(game.caption))
	back_button.position = Vector2(22, 316) if party else Vector2(88, 306)
	back_button.size = Vector2(184, 22) if party else Vector2(464, 23)
	# A compact menu box places its own Back row.
	if not party and game.menu_back_rect.has_area():
		back_button.position = game.menu_back_rect.position; back_button.size = game.menu_back_rect.size
	back_button.visible = game.mode == game.Mode.MENU and game.menu_options.any(func(option: Dictionary) -> bool: return option.label == "Back")
	back_button.text = "Cancel remap" if not game.binding_capture.is_empty() else "Back"
	# While the resume countdown runs, its plate takes the action button's slot.
	var active: bool = game.mode == game.Mode.DODGE and not game.pause_context and game.resume_ticks == 0
	action_button.visible = active and game.boss_id != "chip"
	action_button.text = str({"":"Push paper", "deion":"Jump", "todd":"Sign", "pinpal":"Flip", "claim":"Return", "walt":"Raise lantern", "encore":"Stopping cue"}.get(game.boss_id, "Defend"))
	action_button.position.x = 192 if game.boss_id == "deion" else 232
	action_button.size.x = 124 if game.boss_id == "deion" else 176
	duck_button.visible = active and game.boss_id == "deion"
	left_button.visible = active and game.boss_id == "chip"
	right_button.visible = left_button.visible
	for button: Button in [action_button, duck_button, left_button, right_button]: button.disabled = game.resume_ticks > 0

func _process(_delta: float) -> void: update_state()

func _exit_tree() -> void: game = null
