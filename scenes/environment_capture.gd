extends SceneTree

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	var arguments=OS.get_cmdline_user_args()
	if arguments.is_empty():
		push_error("Provide an absolute output directory after --")
		quit(1)
		return
	var destination=arguments[0]
	DirAccess.make_dir_recursive_absolute(destination)
	var viewport=SubViewport.new()
	viewport.size=Vector2i(640,360)
	viewport.disable_3d=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var environment=preload("res://scenes/umc_environment.gd").new()
	viewport.add_child(environment)
	for id in ["U01","U02","U03","U04","U05","U06","U07"]:
		viewport.size=Vector2i(960,540) if id=="U06" else Vector2i(640,360)
		environment.configure(id)
		environment.step(0.08)
		await process_frame
		await RenderingServer.frame_post_draw
		var image=viewport.get_texture().get_image()
		var error=image.save_png(destination.path_join(id+".png"))
		if error!=OK:push_error("Capture failed "+id)
	var claim=preload("res://scenes/claim_actor.gd").new()
	claim.position=Vector2(400,220)
	claim.set_pose("tell")
	viewport.add_child(claim)
	claim.step(0.08)
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(destination.path_join("CLAIM.png"))
	var pin=preload("res://scenes/pin_actor.gd").new()
	pin.position=Vector2(480,220)
	pin.set_pose("tell")
	viewport.add_child(pin)
	pin.step(0.08)
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(destination.path_join("PIN.png"))
	var vfx=preload("res://scenes/combat_vfx.gd").new()
	viewport.add_child(vfx)
	vfx.play("strike",Vector2(160,210),Vector2(480,185),24)
	vfx.play("guard",Vector2(240,220),Vector2(240,220))
	vfx.play("hit",Vector2(400,220),Vector2(400,175),8)
	for tick in 3:vfx.step(0.1)
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(destination.path_join("VFX.png"))
	print("ENVIRONMENT_CAPTURE_DONE "+destination)
	quit(0)
