extends SceneTree

var failures: Array[String] = []

func check(ok: bool, description: String) -> void:
	if not ok:
		failures.append(description)
		push_error(description)

func _initialize() -> void:
	for actor in ["jules", "imani", "cal"]:
		var world = load("res://resources/art_%s_world.tres" % actor) as SpriteFrames
		check(world != null, actor + " world SpriteFrames load")
		if world == null:
			continue
		for direction in ["down", "left", "right", "up"]:
			for pair in [["idle", 2], ["walk", 6], ["run", 6], ["interact", 3]]:
				var animation = StringName("%s_%s" % [pair[0], direction])
				check(world.has_animation(animation), actor + " " + String(animation))
				check(world.get_frame_count(animation) == pair[1], actor + " frame count " + String(animation))
				for frame in world.get_frame_count(animation):
					var texture = world.get_frame_texture(animation, frame) as AtlasTexture
					check(texture != null, actor + " native AtlasTexture")
					if texture != null:
						check(texture.region.size == Vector2(32, 48), actor + " world frame dimensions")
						check(Rect2(Vector2.ZERO, texture.atlas.get_size()).encloses(texture.region), actor + " atlas frame in bounds")
		var battle = load("res://resources/art_%s_battle.tres" % actor) as SpriteFrames
		check(battle != null, actor + " battle SpriteFrames load")
		if battle != null:
			for pair in [["idle", 4], ["strike", 6], ["connect", 6], ["guard", 2], ["hit", 2], ["down", 2], ["victory", 4]]:
				check(battle.get_frame_count(StringName(pair[0])) == pair[1], actor + " battle " + pair[0])
	var maps = JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/room-tilemaps.json"))
	check(maps != null, "Native tile data parses")
	if maps != null:
		for room_id in ["U01", "U02", "U03", "U04"]:
			var room = maps.rooms[room_id]
			var tiles = load(room.tileset) as TileSet
			check(tiles != null, room_id + " native TileSet loads")
			if tiles == null:
				continue
			check(tiles.tile_size == Vector2i(16, 16), room_id + " tile size")
			var atlas = tiles.get_source(0) as TileSetAtlasSource
			check(atlas != null, room_id + " TileSetAtlasSource exists")
			if atlas != null:
				check(atlas.get_tiles_count() == 920, room_id + " 920 unique native tiles")
				check(atlas.texture.get_size() == Vector2(640, 368), room_id + " padded tile atlas dimensions")
				for cell in room.cells:
					check(atlas.has_tile(Vector2i(int(cell[2]), int(cell[3]))), room_id + " atlas coordinates exist")
			check(room.cells.size() == 920, room_id + " 920 mapped cells")
	var font = load("res://assets/art/afterhours-font.fnt") as FontFile
	check(font != null, "Native BMFont imports as FontFile")
	if font != null:
		for code in range(32, 127):
			check(font.has_char(code), "BMFont ASCII glyph " + str(code))
	if failures.is_empty():
		print("NATIVE_ART_OK: 3 four-direction party SpriteFrames, 3 battle sets, 4 native TileSets/3680 cells, and ASCII BMFont validated.")
		quit(0)
	else:
		print("NATIVE_ART_FAILED: " + str(failures.size()) + " issues")
		quit(1)
