class_name NativeRoomNavigation
extends RefCounted

const CELL: int = 8
var grid: AStarGrid2D
var bounds: Rect2
var blocks: Array = []
var entry: Vector2

func configure(room: Dictionary) -> void:
	var raw: Array = room.walk_bounds
	bounds = Rect2(raw[0], raw[1], raw[2], raw[3])
	blocks = room.blocks
	var spawn: Array = room.entry
	entry = Vector2(spawn[0], spawn[1])
	grid = AStarGrid2D.new()
	grid.region = Rect2i(0, 0, ceili(bounds.end.x / CELL) + 1, ceili(bounds.end.y / CELL) + 1)
	grid.cell_size = Vector2(CELL, CELL)
	grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.default_estimate_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.update()
	for y: int in range(grid.region.size.y):
		for x: int in range(grid.region.size.x):
			grid.set_point_solid(Vector2i(x, y), not clear(Vector2(x * CELL, y * CELL)))

func clear(point: Vector2) -> bool:
	if point.x < bounds.position.x or point.y < bounds.position.y or point.x > bounds.end.x or point.y > bounds.end.y: return false
	var feet: Rect2 = Rect2(point - Vector2(7, 8), Vector2(14, 8)).grow(0.5)
	for block: Dictionary in blocks:
		if feet.intersects(Rect2(block.x, block.y, block.w, block.h), true): return false
	return true

func segment_clear(a: Vector2, b: Vector2) -> bool:
	var steps: int = maxi(1, ceili(a.distance_to(b) / 3.0))
	for i: int in range(steps + 1):
		if not clear(a.lerp(b, float(i) / steps)): return false
	return true

func nearest_cell(point: Vector2) -> Vector2i:
	var rounded := Vector2i(roundi(point.x / CELL), roundi(point.y / CELL))
	if grid.is_in_boundsv(rounded) and not grid.is_point_solid(rounded): return rounded
	var found: Vector2i = Vector2i(-1, -1)
	var best: float = INF
	for y: int in range(grid.region.size.y):
		for x: int in range(grid.region.size.x):
			var cell := Vector2i(x, y)
			if grid.is_point_solid(cell): continue
			var score: float = point.distance_squared_to(Vector2(cell * CELL))
			if score < best:
				found = cell; best = score
	return found

func safe_point(point: Vector2) -> Vector2:
	var start: Vector2i = nearest_cell(entry)
	var destination: Vector2i = nearest_cell(point)
	if destination.x < 0 or grid.get_id_path(start, destination).is_empty(): return Vector2(start * CELL)
	if clear(point) and segment_clear(Vector2(destination * CELL), point): return point
	return Vector2(destination * CELL)

func route(origin: Vector2, goal: Vector2) -> PackedVector2Array:
	if not clear(goal): return PackedVector2Array()
	var start: Vector2i = nearest_cell(origin)
	var end: Vector2i = nearest_cell(goal)
	if start.x < 0 or end.x < 0: return PackedVector2Array()
	var path: PackedVector2Array = grid.get_point_path(start, end)
	if path.is_empty() or not segment_clear(origin, path[0]) or not segment_clear(path[-1], goal): return PackedVector2Array()
	path.append(goal)
	return path

func object_route(origin: Vector2, object: Dictionary) -> PackedVector2Array:
	var anchor := Vector2(object.x, object.y)
	var candidates: Array[Vector2] = []
	if object.has("approach"): candidates.append(Vector2(object.approach[0], object.approach[1]))
	for radius: int in [22, 30]:
		for angle: int in range(16): candidates.append(anchor + Vector2.from_angle(angle * TAU / 16) * radius)
	var best: PackedVector2Array = PackedVector2Array()
	var best_cost: float = INF
	for candidate: Vector2 in candidates:
		if not clear(candidate) or candidate.distance_to(anchor) > 38: continue
		var path: PackedVector2Array = route(origin, candidate)
		if path.is_empty(): continue
		var cost: float = origin.distance_to(path[0])
		for i: int in range(1, path.size()): cost += path[i - 1].distance_to(path[i])
		if cost < best_cost: best = path; best_cost = cost
	return best
