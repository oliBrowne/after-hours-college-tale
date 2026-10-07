class_name NativeExpansionArt
extends RefCounted
static var metadata: Dictionary = {}
static var cache: Dictionary = {}
static var frame_cache: Dictionary = {}
static func data() -> Dictionary:
	if metadata.is_empty(): metadata = JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/expansion-atlas.json"))
	return metadata
static func body(id: String, index: int = 0) -> Texture2D:
	var key: String = id + str(index)
	if cache.has(key): return cache[key]
	var entries: Array = data()[id]
	var entry: Dictionary = entries[clampi(index, 0, entries.size()-1)]
	var raw: Array = entry.rect
	var texture := AtlasTexture.new()
	texture.atlas = load("res://assets/art/walt-production-v1.png" if id == "walt" else "res://assets/art/festival-cast-v1.png")
	texture.region = Rect2(raw[0],raw[1],raw[2],raw[3]); texture.filter_clip = true
	texture.set_meta("foot", Vector2(entry.foot[0],entry.foot[1]))
	texture.set_meta("body_height", 210.0 if id == "walt" else 324.0 if id == "encore" else 338.0)
	texture.set_meta("explicit_direction", true)
	cache[key] = texture
	return texture
static func portrait(id: String, face: int) -> Texture2D:
	var texture := AtlasTexture.new()
	texture.atlas = load("res://assets/art/walt-production-v1.png" if id == "walt" else "res://assets/art/festival-cast-v1.png")
	var cols: int = 6 if id == "walt" else 4
	var row: int = 2 if id == "encore" else 3
	var top: int = 1106 if id == "walt" else int(data().festival_cuts[row])
	var bottom: int = 1278 if id == "walt" else int(data().festival_cuts[row+1])
	var width: int = texture.atlas.get_width()
	var left: int = width*clampi(face,0,3)/cols
	var right: int = width*(clampi(face,0,3)+1)/cols
	texture.region = Rect2(left,top,right-left,bottom-top); texture.filter_clip = true
	return texture
static func world_frames(id: String) -> SpriteFrames:
	if frame_cache.has(id): return frame_cache[id]
	var frames := SpriteFrames.new(); frames.remove_animation("default")
	var poses: Dictionary = {"idle":[24 if id=="walt" else 0],"tell":[25 if id=="walt" else 1],"reaction":[27 if id=="walt" else 1],"settled":[28 if id=="walt" else 3],"hit":[26 if id=="walt" else 2],"down":[29 if id=="walt" else 2],"strike":[25 if id=="walt" else 1],"guard":[27 if id=="walt" else 0],"connect":[28 if id=="walt" else 3]}
	var directions: Array[String] = ["down","up","right","left"]
	for row: int in range(4):
		var start: int = row*6 if id=="walt" else 0
		poses["idle_"+directions[row]] = [start]
		poses["interact_"+directions[row]] = [start,25] if id=="walt" and row==0 else [start]
		poses["walk_"+directions[row]] = range(start,start+6) if id=="walt" else [0]
		poses["run_"+directions[row]] = poses["walk_"+directions[row]]
	for name: String in poses:
		frames.add_animation(name); frames.set_animation_speed(name,6.0)
		for index: int in poses[name]: frames.add_frame(name, body(id,index))
	frame_cache[id] = frames
	return frames
