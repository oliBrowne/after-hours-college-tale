extends SceneTree

func _initialize() -> void:
	var portrait=preload("res://scenes/object_portrait.gd").new()
	root.add_child(portrait)
	portrait.size=Vector2(80,80)
	for speaker in ["Pip","CLAIM","Pin Pal"]:
		assert(portrait.supports(speaker))
		for expression in 4:
			portrait.configure(speaker,expression)
			assert(portrait.expression==expression)
		portrait.configure(speaker,"concern")
		assert(portrait.expression==2)
	assert(not portrait.supports("Jules"))
	var pip=preload("res://scenes/pip_actor.gd").new()
	root.add_child(pip)
	for pose in ["idle","wave","interact","resolved"]:
		pip.set_pose(pose)
		pip.step(1.0/60.0)
		assert(pip.pose==pose)
	print("OBJECT_PORTRAIT_OK: three object speakers/four expressions, aliases and Pip poses.")
	if OS.get_cmdline_user_args().is_empty():
		quit(0)
	else:
		call_deferred("capture")

func capture() -> void:
	var destination=OS.get_cmdline_user_args()[0]
	DirAccess.make_dir_recursive_absolute(destination)
	var viewport=SubViewport.new()
	viewport.size=Vector2i(320,240)
	viewport.disable_3d=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var background=ColorRect.new()
	background.color=Color("171a2b")
	background.size=Vector2(320,240)
	viewport.add_child(background)
	for row in 3:
		for expression in 4:
			var widget=preload("res://scenes/object_portrait.gd").new()
			widget.position=Vector2(expression*80,row*80)
			widget.size=Vector2(80,80)
			viewport.add_child(widget)
			widget.configure(["Pip","CLAIM","Pin Pal"][row],expression)
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(destination.path_join("object-portraits.png"))
	viewport.queue_free()
	await process_frame
	var presentation=SubViewport.new()
	presentation.size=Vector2i(640,360)
	presentation.disable_3d=true
	presentation.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(presentation)
	var game=load("res://scenes/main.tscn").instantiate()
	presentation.add_child(game)
	for frame in 6:await process_frame
	await RenderingServer.frame_post_draw
	presentation.get_texture().get_image().save_png(destination.path_join("native-title.png"))
	game.enter_room("U06",Vector2(780,320),false)
	game.world.visible=true
	game.backdrop.visible=false
	game.resume_world()
	for frame in 6:await process_frame
	await RenderingServer.frame_post_draw
	presentation.get_texture().get_image().save_png(destination.path_join("native-connection.png"))
	game.audio.shutdown()
	game.menu_options.clear()
	game.queue_free()
	presentation.queue_free()
	await process_frame
	await process_frame
	print("NATIVE_PRESENTATION_CAPTURE_DONE "+destination)
	quit(0)
