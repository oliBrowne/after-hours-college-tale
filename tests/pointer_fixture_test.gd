extends SceneTree
var game: Node
var failed: int = 0
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var folder: String = OS.get_environment("AFTER_HOURS_FIXTURE")
	if folder.is_empty(): quit(2); return
	DirAccess.make_dir_recursive_absolute(folder)
	game = load("res://scenes/main.tscn").instantiate()
	game.preferences_path = folder.path_join("preferences.json")
	game.saves = NativeSaveService.new(folder.path_join("slots"))
	root.add_child(game)
	for fixture: Array in [["U01","bike"],["U01","mara"],["U02","eli"],["U02","squirrel"],["U03","todd"],["U03","booth"],["U04","flyer"],["U06","scoreboard"],["U06","pinpal"],["U06","chip"],["U06","deion"],["U07","pip"],["U07","claim"]]:
		game.state = NativeState.fresh()
		game.state.flags = {"imani_joined": true, "cal_joined": true, "mixer_returned": true, "booth_seen":true}
		var room: Dictionary = game.rooms[fixture[0]]
		game.enter_room(fixture[0], Vector2(room.entry[0], room.entry[1]), false)
		for _i: int in range(6): await physics_frame
		var object: Dictionary
		for item: Dictionary in room.objects:
			if item.id == fixture[1]: object = item
		var raw: Array = object.hit_rect
		var position: Vector2 = game.world.get_global_transform_with_canvas() * (Vector2(object.x, object.y) + Vector2(raw[0] + raw[2] / 2.0, raw[1] + raw[3] / 2.0))
		var click := InputEventMouseButton.new()
		click.button_index = MOUSE_BUTTON_LEFT; click.pressed = true; click.position = position
		game.get_viewport().push_input(click)
		await physics_frame
		var selected: bool = game.pointer_object.get("id", "") == fixture[1]
		for _i: int in range(1800):
			if game.mode != game.Mode.WORLD or game.pointer_goal == Vector2.INF: break
			await physics_frame
		var pass_case: bool = selected and game.mode == game.Mode.DIALOGUE
		if not pass_case: failed += 1
		print("POINTER_FIXTURE ", fixture, " selected=", selected, " dialogue=", game.mode == game.Mode.DIALOGUE, " position=", game.player.position, " pass=", pass_case)
	game.audio.shutdown(); game.dialogue_callback = Callable(); game.menu_options.clear(); game.pause_options.clear(); game.dialogue_choices.clear()
	game.queue_free(); await process_frame
	print("Pointer fixtures: 13 checks, failures: ", failed)
	quit(0 if failed == 0 else 1)
