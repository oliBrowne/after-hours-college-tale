class_name NativeCampusWorld
extends RefCounted
static func prepare(room: Dictionary, flags: Dictionary) -> void:
	for prop: Dictionary in room.get("placements",[]):
		if prop.has("base_x"):prop.x=float(prop.base_x)+(float(prop.shift_x) if flags.get("stacks_shifted",false) else 0.0)
	NativeRoomPlacement.prepare(room)
