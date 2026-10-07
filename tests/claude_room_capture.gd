extends SceneTree
## Renders whole rooms (environment plus props, no people) to PNGs:
## -- <out dir> [room ids...] [flag=value ...]   (value true/false or a string; files get a suffix per flag set)

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	var out: String = args[0]
	DirAccess.make_dir_recursive_absolute(out)
	var rooms: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/rooms.json"))
	var ids: Array = []
	var flags: Dictionary = {}
	var suffix: String = ""
	for arg: String in args.slice(1):
		if "=" in arg:
			var pair: PackedStringArray = arg.split("=", true, 1)
			flags[pair[0]] = true if pair[1] == "true" else false if pair[1] == "false" else pair[1]
			suffix += "-" + pair[0] + "-" + pair[1]
		else:
			ids.append(arg)
	if ids.is_empty(): ids = rooms.keys()
	for id: String in ids:
		var layout: Dictionary = rooms[id]
		NativeCampusWorld.prepare(layout, flags)  # same as the game: shifted stacks, blocks, lights
		var size := Vector2i(int(layout.dimensions[0]), int(layout.dimensions[1]))
		var viewport := SubViewport.new()
		viewport.size = size
		viewport.disable_3d = true
		viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(viewport)
		var holder := Node2D.new()
		holder.y_sort_enabled = true
		viewport.add_child(holder)
		var env := UMCEnvironment.new()
		holder.add_child(env)
		env.configure(id, layout, flags)
		env.step(0.5)
		for i in 3: await process_frame
		await RenderingServer.frame_post_draw
		viewport.get_texture().get_image().save_png(out.path_join(id + suffix + ".png"))
		viewport.queue_free()
		await process_frame
	quit(0)
