extends SceneTree
var game: Node
var checks: int = 0
var failures: int = 0
func _initialize() -> void: call_deferred("run")
func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok: failures += 1; print("FAIL ", message)
func run() -> void:
	var folder: String = OS.get_environment("AFTER_HOURS_FIXTURE")
	if folder.is_empty(): quit(2); return
	DirAccess.make_dir_recursive_absolute(folder)
	game = load("res://scenes/main.tscn").instantiate()
	game.preferences_path = folder.path_join("preferences.json")
	game.saves = NativeSaveService.new(folder.path_join("saves"))
	root.add_child(game); game.qa = true; game.set_physics_process(false)
	game.state.settings.instant = true; game.state.settings.large = true
	game.state.settings.reducedMotion = true; game.state.settings.music = 0.75
	game.state.settings.effects = 0.25; game.state.settings.voices = 0.0
	game.state.settings.ambience = 0.5; game.state.settings.bindings = {"confirm":KEY_Q}
	game._save_preferences()
	var preferred: Dictionary = JSON.parse_string(JSON.stringify(game.state.settings))
	var old: Dictionary = NativeState.fresh()
	old.flags = {"discovery_bike_seen":true}; old.inventory.granola = 1
	old.flags.visited_U01 = true
	var inventory: Dictionary = JSON.parse_string(JSON.stringify(old.inventory))
	check(game.saves.save("slot1", old) == OK, "Older checkpoint fixture written")
	game.load_save("slot1")
	check(game.state.settings == preferred, "Loading retains current persisted accessibility/audio/bindings")
	check(game.state.flags == old.flags and game.state.inventory == inventory, "Loading still restores gameplay data")
	check(InputMap.action_has_event("confirm", make_key(KEY_Q)), "Restored preferences configure current binding")
	check(game.saves.export_file(folder.path_join("old-portable.json"), old) == OK, "Older portable fixture exported")
	var imported: Dictionary = game.saves.import_file(folder.path_join("old-portable.json"))
	check(not imported.has("error"), "Portable checkpoint validates")
	game.restore_state(imported.state)
	check(game.state.settings == preferred, "Import restoration retains current persisted preferences")
	check(game.state.flags == old.flags and game.state.inventory == inventory, "Import restoration still restores gameplay")
	var invalid: FileAccess = FileAccess.open(game.preferences_path, FileAccess.WRITE)
	invalid.store_string('{"music":999}'); invalid.close()
	game.restore_state(old.duplicate(true))
	check(game.state.settings.instant == false and game.state.settings.music == old.settings.music, "Invalid preferences fall back to valid checkpoint settings")
	game.preferences_path = folder.path_join("never-created-preferences.json")
	old.settings.erase("voices"); old.settings.erase("ambience")
	game.restore_state(old.duplicate(true))
	check(game.state.settings.has("voices") and game.state.settings.has("ambience"), "No preferences still migrates legacy gains")
	game.audio.shutdown(); game.menu_options.clear(); game.pause_options.clear(); game.dialogue_choices.clear(); game.dialogue_callback = Callable()
	game.queue_free(); await process_frame
	print("Preferences restore: ", checks, " checks, ", failures, " failures")
	quit(0 if failures == 0 else 1)
func make_key(code: int) -> InputEventKey:
	var event := InputEventKey.new(); event.physical_keycode = code; return event
