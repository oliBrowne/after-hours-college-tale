extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var folder: String = OS.get_environment("AFTER_HOURS_CAPTURE")
	if folder.is_empty(): quit(2); return
	DirAccess.make_dir_recursive_absolute(folder)
	var game: Node = load("res://scenes/main.tscn").instantiate()
	game.preferences_path = folder.path_join("preferences.json")
	game.saves = NativeSaveService.new(folder.path_join("saves"))
	root.add_child(game)
	game.enter_room("U04", Vector2(280, 283), false)
	await process_frame; await process_frame; await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join("initial-U04.png"))
	for phase: String in ["before", "peaceful", "forceful"]:
		game.state = NativeState.fresh()
		game.state.flags = {"imani_joined":true, "cal_joined":true, "mixer_returned":true, "booth_seen":true}
		if phase != "before":
			game.state.flags.merge({"flyer_resolution":phase, "pinpal_resolution":phase, "claim_resolution":phase, "pip_joined":true, "opening_finished":true, "discovery_arcade_seen":true})
		for view: Array in [["U04", Vector2(535,320)], ["U05", Vector2(120,260)], ["U06", Vector2(735,370)], ["U07", Vector2(380,300)]]:
			game.enter_room(view[0], view[1], false)
			await process_frame; await process_frame; await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(folder.path_join("%s-%s.png" % [phase,view[0]]))
		game.enter_room("U07", Vector2(630,237), false)
		await process_frame; await process_frame; await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(folder.path_join("%s-intake.png" % phase))
	game.audio.shutdown(); game.menu_options.clear(); game.pause_options.clear(); game.dialogue_choices.clear(); game.dialogue_callback = Callable()
	game.queue_free(); await process_frame; quit()
