class_name NativeRoomPlacement
extends RefCounted

## One placement owns its visual base, foot collision, light and interaction.
static func prepare(room: Dictionary) -> void:
	room.blocks = room.get("fixed_blocks", []).duplicate(true)
	room.lights = []
	for prop: Dictionary in room.get("placements", []):
		if int(prop.depth) > 0: room.blocks.append({"x": prop.x - prop.w / 2.0, "y": prop.y - prop.depth, "w": prop.w, "h": prop.depth})
		if prop.kind == "lamp": room.lights.append([prop.x, prop.y - prop.h + 5])
		if prop.get("object") != null:
			for object: Dictionary in room.objects:
				if object.id == prop.object:
					object.x = prop.x + prop.anchor_offset[0]
					object.y = prop.y + prop.anchor_offset[1]
					object.hit_rect = [-prop.w / 2.0 - prop.anchor_offset[0], -prop.h - prop.anchor_offset[1], prop.w, prop.h + 12]
					prop.requires = object.get("requires", []).duplicate()
					if object.get("to") == "U05" and not "booth_seen" in prop.requires and object.id == "stairs": prop.requires.append("booth_seen")
	for object: Dictionary in room.objects:
		if object.has("sprite"): object.hit_rect = [-24, -58, 48, 64]
		if object.id == "claim": object.hit_rect = [-38, -90, 76, 94]
		if object.id == "pinpal": object.hit_rect = [-26, -80, 52, 84]
		if object.id == "pip": object.hit_rect = [-22, -40, 44, 48]
		if object.id == "squirrel": object.hit_rect = [-18, -15, 36, 24]
