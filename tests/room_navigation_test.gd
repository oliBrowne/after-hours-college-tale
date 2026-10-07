extends SceneTree
var checks: int = 0
var failures: int = 0
func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures += 1; print("FAIL ", message)
func _initialize() -> void:
	var rooms: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/rooms.json"))
	for room: Dictionary in rooms.values(): NativeRoomPlacement.prepare(room)
	for id: String in rooms:
		var room: Dictionary = rooms[id]
		var nav := NativeRoomNavigation.new()
		nav.configure(room)
		check(nav.clear(nav.entry), id + " entry clear")
		for object: Dictionary in room.objects:
			var path: PackedVector2Array = nav.object_route(nav.entry, object)
			check(not path.is_empty(), id + "/" + str(object.id) + " approachable")
			for i: int in range(path.size()):
				check(nav.clear(path[i]), id + "/" + str(object.id) + " path feet clear")
				if i > 0: check(nav.segment_clear(path[i - 1], path[i]), id + "/" + str(object.id) + " path segment clear")
			if object.kind == "door":
				var target := NativeRoomNavigation.new()
				target.configure(rooms[object.to])
				check(target.clear(Vector2(object.spawn[0], object.spawn[1])), id + "/" + str(object.id) + " destination spawn clear")
		for block: Dictionary in room.blocks:
			var old := Vector2(block.x + block.w / 2.0, block.y + block.h / 2.0)
			var fixed: Vector2 = nav.safe_point(old)
			check(nav.clear(fixed) and not nav.route(nav.entry, fixed).is_empty(), id + " furniture-covered saved point safely restored")
	for id: String in NativeCastArt.IDS + NativeCastArt.OBJECT_IDS:
		for pose: int in range(3 if id in NativeCastArt.OBJECT_IDS else 6):
			var texture: Texture2D = NativeCastArt.body(id, pose)
			check(texture != null and texture.get_size().x > 0 and texture.has_meta("foot"), id + " complete pose metadata")
	print("R1 room/cast checks: ", checks, ", failures: ", failures)
	quit(0 if failures == 0 else 1)
