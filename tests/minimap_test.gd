extends SceneTree
## Run: Godot --headless --path godot-game --script res://tests/minimap_test.gd
## The schematic layout behind the minimap and campus map: every room has a unique spot, the
## doors only join rooms that exist, and every objective target lies on the map.
var checks: int = 0
var failures: int = 0

func _init() -> void:
	var rooms: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/rooms.json"))
	var spots: Dictionary = {}
	for id: String in rooms:
		_check(NativeMinimap.POS.has(id), id + " has a map position")
	for id: String in NativeMinimap.POS:
		_check(rooms.has(id), id + " is a real room")
		var cell: Vector2i = NativeMinimap.POS[id]
		_check(not spots.has(cell), id + " does not share a cell")
		spots[cell] = id
		var point: Vector2 = NativeMinimap.point(id)
		_check(point.x + 25.0 + 14.0 <= 608.0 and point.y + 15.0 + 8.0 <= 218.0, id + " fits the full map")
	for id: String in rooms:
		for o: Dictionary in rooms[id].objects:
			if str(o.get("kind", "")) == "door": _check(rooms.has(str(o.get("to", ""))), id + " door leads to a real room")
	for objective: String in NativeGuide.TARGETS:
		var entry: Array = NativeGuide.TARGETS[objective]
		_check(str(entry[0]).is_empty() or NativeMinimap.POS.has(str(entry[0])), objective + " target room is on the map")
	print("Minimap: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)
