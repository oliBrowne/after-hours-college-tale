extends SceneTree
var main: Node
var folder: String
class Gallery extends Node2D:
	var page: int
	const FONT = preload("res://assets/art/afterhours-font.fnt")
	func _draw() -> void:
		draw_rect(Rect2(0, 0, 640, 360), Color("353047"))
		if page < 2:
			var ids: Array = NativeCastArt.IDS if page == 0 else NativeCastArt.OBJECT_IDS
			for row: int in range(ids.size()):
				var id: String = ids[row]
				draw_string(FONT, Vector2(8, 22 + row * 66), id, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("e6d6b1"))
				for col: int in range(6 if page == 0 else 3):
					var texture: Texture2D = NativeCastArt.body(id, col)
					var base := Vector2(120 + col * 90, 66 + row * 66)
					var factor: float = 56.0 / float(texture.get_meta("body_height"))
					var foot: Vector2 = texture.get_meta("foot")
					draw_line(base - Vector2(35, 0), base + Vector2(35, 0), Color("b9d5bc"), 1)
					draw_texture_rect(texture, Rect2((base - foot * factor).round(), (texture.get_size() * factor).round()), false)
		else:
			var names: Array = ["Jules", "Imani", "Cal", "Mags"] + NativeCastArt.PEOPLE + NativeCastArt.OBJECTS
			var first: int = (page - 2) * 4
			for row: int in range(mini(4, names.size() - first)):
				var name: String = names[first + row]
				draw_string(FONT, Vector2(5, row * 87 + 14), name, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("e6d6b1"))
				for col: int in range(4):
					var texture: Texture2D = NativeCastArt.portrait(name, col)
					draw_texture_rect(texture, Rect2(150 + col * 115, row * 87 + 2, 80, 80), false)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	folder = OS.get_environment("AFTER_HOURS_CAPTURE")
	DirAccess.make_dir_recursive_absolute(folder)
	for page: int in range(6):
		var gallery := Gallery.new()
		gallery.page = page; gallery.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		root.add_child(gallery)
		await process_frame; await process_frame; await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(folder.path_join("cast-%d.png" % page))
		gallery.queue_free(); await process_frame
	# Composition fixtures show production scenes; they are not uninterrupted route evidence.
	main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	main.state.flags = {"imani_joined": true, "cal_joined": true, "mixer_returned": true, "flyer_resolution":"peaceful", "booth_seen":true}
	for id: String in main.rooms:
		main.enter_room(id, Vector2(main.rooms[id].entry[0], main.rooms[id].entry[1]), false)
		await process_frame; await process_frame; await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(folder.path_join("room-%s.png" % id))
	for view: Array in [["U04", Vector2(390, 285)], ["U06", Vector2(825, 380)], ["U07", Vector2(630, 237)], ["U03", Vector2(369, 280)]]:
		main.enter_room(view[0], view[1], false)
		if view[0] == "U03": main.dialogue([["Booth", "One real answer.", "concern"]], main.resume_world)
		await process_frame; await process_frame; await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(folder.path_join("detail-%s.png" % view[0]))
	main.set_physics_process(false)
	for id: String in ["", "chip", "deion", "todd", "pinpal", "claim"]:
		main.boss_id = id; main.begin_battle()
		await process_frame; await process_frame; await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(folder.path_join("battle-%s.png" % ("flyer" if id.is_empty() else id)))
	main.queue_free(); await process_frame
	quit()
