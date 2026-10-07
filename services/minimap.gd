class_name NativeMinimap
extends RefCounted
## Data behind the corner minimap and the full campus map: where every room sits on the
## schematic, which rooms the player knows, the route to the current objective, and which
## people in a room have been spoken to. Reads the door graph and objective data; owns no story.
const CELL: Vector2 = Vector2(29, 21)
const POS: Dictionary = {
	"D01": Vector2i(0, 1), "D02": Vector2i(1, 1), "D03": Vector2i(2, 1),
	"C01": Vector2i(6, 3), "C02": Vector2i(5, 1), "C03": Vector2i(7, 1),
	"H01": Vector2i(8, 3), "H02": Vector2i(9, 3), "P01": Vector2i(8, 4), "P02": Vector2i(9, 4),
	"U01": Vector2i(0, 8), "U08": Vector2i(1, 8), "U02": Vector2i(2, 8), "U03": Vector2i(3, 7),
	"U04": Vector2i(2, 6), "U06": Vector2i(3, 5), "U05": Vector2i(4, 6), "U07": Vector2i(3, 4),
	"F01": Vector2i(5, 8), "F02": Vector2i(6, 9), "F03": Vector2i(6, 7), "F04": Vector2i(7, 8), "F05": Vector2i(8, 9), "F06": Vector2i(8, 7),
	"N01": Vector2i(9, 6), "N02": Vector2i(10, 7), "N03": Vector2i(11, 8), "N04": Vector2i(12, 7), "N05": Vector2i(11, 6), "N06": Vector2i(13, 6), "N07": Vector2i(13, 8),
	"E01": Vector2i(15, 7), "E02": Vector2i(16, 7), "E03": Vector2i(17, 7), "E04": Vector2i(17, 6), "E05": Vector2i(16, 6),
	"O01": Vector2i(11, 4), "O02": Vector2i(12, 3), "O03": Vector2i(13, 2), "O04": Vector2i(12, 2),
	"M01": Vector2i(14, 4), "M02": Vector2i(15, 3), "M03": Vector2i(15, 2), "M04": Vector2i(16, 4), "M05": Vector2i(15, 5), "M06": Vector2i(17, 3), "M07": Vector2i(18, 4),
	"G01": Vector2i(19, 5), "G02": Vector2i(19, 6),
}
const TINTS: Dictionary = {"D": "c9a0a8", "C": "e8b45c", "H": "c98c6a", "P": "a69ac9", "U": "8fb9c9", "F": "d08c9b", "N": "9bc9a0", "E": "c9c58f", "O": "b9a58f", "M": "c98fbf", "G": "9fd0d0"}
const MAX_SPOKEN_KINDS: Array[String] = ["talk"]
static var cache_key: String = ""
static var cache: Dictionary = {}

static func point(id: String) -> Vector2:
	var cell: Vector2i = POS.get(id, Vector2i.ZERO)
	return Vector2(cell.x * CELL.x, cell.y * CELL.y)

static func tint(id: String) -> Color:
	return Color(str(TINTS.get(id.substr(0, 1), "b9d5bc")))

static func short_name(value: Variant) -> String:
	return str(value).split(" /")[0]

static func door_open(g: Node, door: Dictionary) -> bool:
	return NativeGuide.met(g.state.flags, door.get("requires", []))

static func spoken_flag(room: String, object: Dictionary) -> String:
	return "talked_%s_%s" % [room, str(object.id)]

## Hook from main.interact: remember who the player has talked to.
static func talked(g: Node, object: Dictionary) -> void:
	if str(object.get("kind", "")) in MAX_SPOKEN_KINDS: g.state.flags[spoken_flag(str(g.state.room), object)] = true

## What the objective points at: {room, id, name} or {} when the objective has no marker.
static func goal(g: Node) -> Dictionary:
	var entry: Array = NativeGuide.TARGETS.get(NativeCampaign.objective(g.state), [])
	if entry.is_empty(): return {}
	var id: String = str(entry[1])
	var room: String = str(entry[0])
	if room.is_empty():
		for candidate: String in g.rooms:
			if NativeGuide.has_object(g, candidate, id): room = candidate; break
	if room.is_empty() or not g.rooms.has(room): return {}
	for o: Dictionary in g.rooms[room].objects:
		if str(o.id) == id: return {"room": room, "id": id, "name": short_name(o.name), "kind": str(o.get("kind", ""))}
	return {}

## Rooms from here to the objective's room, following open doors first. Empty when unreachable.
static func route(g: Node) -> Array:
	var target: Dictionary = goal(g)
	if target.is_empty(): return []
	var here: String = str(g.state.room)
	for open_only: bool in [true, false]:
		var seen: Dictionary = NativeGuide.reach(g, open_only)
		var room: String = str(target.room)
		if not seen.has(room): continue
		var path: Array = [room]
		while room != here:
			room = str(seen[room][0]); path.push_front(room)
		return path
	return []

## Goal and route, recomputed only when the room or objective changes.
static func plan(g: Node) -> Dictionary:
	var key: String = "%s|%s|%d" % [g.state.room, NativeCampaign.objective(g.state), g.state.flags.size()]
	if key != cache_key:
		cache_key = key
		cache = {"goal": goal(g), "route": route(g)}
	return cache

static func people(g: Node, room: String) -> Array:
	var out: Array = []
	var target: Dictionary = goal(g)
	for o: Dictionary in g.rooms[room].objects:
		var kind: String = str(o.get("kind", ""))
		if kind != "talk" and kind != "battle" and kind != "challenge": continue
		var next: bool = not target.is_empty() and str(target.room) == room and str(target.id) == str(o.id)
		out.append({"name": short_name(o.name), "next": next, "boss": kind != "talk", "spoken": bool(g.state.flags.get(spoken_flag(room, o), false))})
	return out

static func unspoken(g: Node, room: String) -> int:
	var count: int = 0
	for p: Dictionary in people(g, room):
		if not p.boss and not p.spoken: count += 1
	return count

static func visited(g: Node, room: String) -> bool:
	return bool(g.state.flags.get("visited_" + room, false)) or str(g.state.room) == room

## Visited rooms, rooms one door from a visited room, and the objective's room are on the map; the rest are fog.
static func known(g: Node, room: String) -> bool:
	if visited(g, room): return true
	var target: Dictionary = plan(g).goal
	if not target.is_empty() and str(target.room) == room: return true
	for other: String in g.rooms:
		if not visited(g, other): continue
		for o: Dictionary in g.rooms[other].objects:
			if str(o.get("kind", "")) == "door" and str(o.get("to", "")) == room: return true
	return false

## Door edges between laid-out rooms, each pair once: [from, to, open].
static func edges(g: Node) -> Array:
	var out: Array = []
	var done: Dictionary = {}
	for room: String in POS:
		if not g.rooms.has(room): continue
		for o: Dictionary in g.rooms[room].objects:
			if str(o.get("kind", "")) != "door" or not POS.has(str(o.get("to", ""))): continue
			var to: String = str(o.to)
			var pair: String = room + to if room < to else to + room
			var open: bool = door_open(g, o)
			if done.has(pair):
				if open: out[int(done[pair])][2] = true
				continue
			done[pair] = out.size()
			out.append([room, to, open])
	return out
