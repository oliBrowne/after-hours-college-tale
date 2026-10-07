extends SceneTree
## Real legacy dictionaries through production Main preference and save-slot paths.
var game: Variant
var checks: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func _assert_gains(settings: Dictionary, effects: float, voices: float, ambience: float) -> void:
	assert(settings.has("voices") and settings.has("ambience"))
	assert(is_equal_approx(float(settings.effects), effects))
	assert(is_equal_approx(float(settings.voices), voices))
	assert(is_equal_approx(float(settings.ambience), ambience))

func _action(action: String) -> void:
	while int(game.input_lock) > 0:
		await physics_frame
	var press := InputEventAction.new()
	press.action = action
	press.pressed = true
	root.push_input(press)
	var release := InputEventAction.new()
	release.action = action
	root.push_input(release)
	await physics_frame

func _change_effects() -> void:
	# The production Settings menu cycles Effects 0.5 -> 0.75 -> 1 -> 0.
	await _action("move_down")
	assert(str(game.menu_options[game.selection].label).begins_with("Effects "))
	await _action("confirm")

func _mute_effects() -> void:
	game.settings_menu()
	for expected: float in [0.75, 1.0, 0.0]:
		await _change_effects()
		_assert_gains(game.state.settings, expected, 0.5, 0.325)
		assert(is_equal_approx(float(game.audio.get("_voice_volume")), 0.5))
		assert(is_equal_approx(float(game.audio.get("_ambience_volume")), 0.325))

func _write(path: String, data: Dictionary) -> void:
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	assert(file != null)
	file.store_string(JSON.stringify(data))
	file.close()

func _run() -> void:
	var directory: String = OS.get_environment("AFTER_HOURS_AUDIO_MIGRATION_QA")
	assert(not directory.is_empty())
	DirAccess.make_dir_recursive_absolute(directory)
	var legacy: Dictionary = NativeState.preferences()
	legacy.erase("voices")
	legacy.erase("ambience")
	var migrated: Dictionary = NativeState.normalize_audio_settings(legacy)
	_assert_gains(migrated, 0.5, 0.5, 0.325)
	assert(not legacy.has("voices") and not legacy.has("ambience"))
	assert(NativeState.normalize_audio_settings(migrated) == migrated)
	migrated.bindings.confirm = 90
	assert(not (legacy.bindings as Dictionary).has("confirm"))
	checks.append("Pure deep-copy helper; original legacy Effects captured; idempotence")
	var explicit_zero: Dictionary = legacy.duplicate(true)
	explicit_zero.voices = 0.0
	explicit_zero.ambience = 0.0
	_assert_gains(NativeState.normalize_audio_settings(explicit_zero), 0.5, 0.0, 0.0)
	explicit_zero.erase("ambience")
	_assert_gains(NativeState.normalize_audio_settings(explicit_zero), 0.5, 0.0, 0.325)
	explicit_zero.erase("voices")
	explicit_zero.effects = 0.0
	_assert_gains(NativeState.normalize_audio_settings(explicit_zero), 0.0, 0.0, 0.0)
	checks.append("Explicit stored zeros and partial migration preserved; legacy Effects zero migrates to zeros")
	var malformed: Dictionary = legacy.duplicate(true)
	malformed.effects = {"bad":"corrupt"}
	assert(not NativeSaveService.validate_settings(NativeState.normalize_audio_settings(malformed)))
	checks.append("Malformed original Effects retained/rejected without unsafe conversion")
	if "--helper-only" in OS.get_cmdline_user_args():
		print("LEGACY AUDIO HELPER PASS: " + str(checks))
		quit(0)
		return
	game = (load("res://scenes/main.tscn") as PackedScene).instantiate()
	root.add_child(game)
	await process_frame
	game.qa = true
	game.preferences_path = directory.path_join("preferences.json")
	game.saves = NativeSaveService.new(directory.path_join("slots"))
	_write(game.preferences_path, legacy)
	game._load_preferences()
	_assert_gains(game.state.settings, 0.5, 0.5, 0.325)
	await _mute_effects()
	var stored: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(game.preferences_path))
	_assert_gains(stored, 0.0, 0.5, 0.325)
	game.state = NativeState.fresh()
	game._load_preferences()
	_assert_gains(game.state.settings, 0.0, 0.5, 0.325)
	checks.append("Actual old preferences load -> Effects menu 0.75/1/0 -> preferences write/reload retains Voices0.5/Ambience0.325")
	var old_state: Dictionary = NativeState.fresh()
	old_state.settings = legacy.duplicate(true)
	assert(game.saves.save("slot1", old_state) == OK)
	var original: Dictionary = game.saves.load_slot("slot1")
	assert(not original.state.settings.has("voices") and not original.state.settings.has("ambience"))
	game.load_save("slot1")
	_assert_gains(game.state.settings, 0.5, 0.5, 0.325)
	await _mute_effects()
	assert(game.persist("slot2"))
	game.state = NativeState.fresh()
	game.load_save("slot2")
	_assert_gains(game.state.settings, 0.0, 0.5, 0.325)
	checks.append("Actual raw old slot1 -> Main load -> Effects menu 0.75/1/0 -> production persist slot2/load retains independent gains")
	old_state.settings = legacy.duplicate(true)
	old_state.settings.voices = 0.0
	old_state.settings.ambience = 0.0
	assert(game.saves.save("slot3", old_state) == OK)
	game.load_save("slot3")
	_assert_gains(game.state.settings, 0.5, 0.0, 0.0)
	_write(game.preferences_path, old_state.settings)
	game._load_preferences()
	_assert_gains(game.state.settings, 0.5, 0.0, 0.0)
	checks.append("Explicit zeros preserved through both actual Main load paths")
	_write(directory.path_join("migration-report.json"), {"pass":true,"source":"Old fixture dictionaries, production Main preference/slot APIs and actual viewport Settings action events", "checks":checks,"slotPaths":["slots/slot1.json","slots/slot2.json","slots/slot3.json"],"preferencesPath":"preferences.json"})
	game.menu_options.clear()
	game.dialogue_callback = Callable()
	game.audio.shutdown()
	game.queue_free()
	await process_frame
	OS.delay_msec(150)
	await process_frame
	print("LEGACY AUDIO MIGRATION PASS: " + str(checks))
	quit(0)
