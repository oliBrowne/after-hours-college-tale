extends SceneTree

var failures: Array[String] = []

func check(condition: bool, description: String) -> void:
	if not condition:
		failures.append(description)
		push_error(description)

func _initialize() -> void:
	for actor in ["deion", "chip", "todd", "mara", "eli"]:
		var frames = load("res://resources/art_npc_%s.tres" % actor) as SpriteFrames
		check(frames != null, actor + " SpriteFrames load")
		if frames == null:
			continue
		check(frames.get_animation_names().size() == 12, actor + " has 12 directional animations")
		for direction in ["down", "left", "right", "up"]:
			for pair in [["idle", 2], ["walk", 6], ["interact", 3]]:
				var animation = StringName("%s_%s" % [pair[0], direction])
				check(frames.has_animation(animation), actor + " " + String(animation))
				check(frames.get_frame_count(animation) == pair[1], actor + " correct frame count")
				for index in frames.get_frame_count(animation):
					var texture = frames.get_frame_texture(animation, index) as AtlasTexture
					check(texture != null, actor + " AtlasTexture exists")
					if texture != null:
						check(texture.region.size == Vector2(40, 56), actor + " 40x56 frame")
						check(Rect2(Vector2.ZERO, texture.atlas.get_size()).encloses(texture.region), actor + " region in atlas bounds")
		var portrait = load("res://assets/art/npc-%s-portraits.png" % actor) as Texture2D
		check(portrait != null and portrait.get_size() == Vector2(320, 80), actor + " four 80px portraits")
	var mask = load("res://assets/art/lamp-light-mask.png") as Texture2D
	check(mask != null and mask.get_size() == Vector2(128, 128), "PointLight2D mask")
	if failures.is_empty():
		print("NATIVE_NPC_ART_OK: five 44-frame directional actors, five expression portrait sets, and light mask.")
		quit(0)
	else:
		print("NATIVE_NPC_ART_FAILED: " + str(failures.size()))
		quit(1)
