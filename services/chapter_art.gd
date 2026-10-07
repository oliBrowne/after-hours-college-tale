class_name NativeChapterArt
extends RefCounted
static var metadata: Dictionary={}
static var cache: Dictionary={}
static var frame_cache: Dictionary={}
static func data() -> Dictionary:
	if metadata.is_empty():metadata=JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/chapter2-atlas.json"))
	return metadata
static func body(id: String, frame: int=0) -> Texture2D:
	var key: String=id+str(frame)
	if cache.has(key):return cache[key]
	var entry: Dictionary=data()[id][clampi(frame,0,3)]
	var raw: Array=entry.rect
	var texture:=AtlasTexture.new();texture.atlas=load("res://assets/art/chapter2-bodies-v1.png")
	texture.region=Rect2(raw[0],raw[1],raw[2],raw[3]);texture.filter_clip=true
	texture.set_meta("foot",Vector2(entry.foot[0],entry.foot[1]));texture.set_meta("body_height",entry.height)
	cache[key]=texture;return texture
static func portrait(id: String, face: int) -> Texture2D:
	var row: int=data().ids.find(id)
	var cuts: Array=data().portrait_cuts
	var texture:=AtlasTexture.new();texture.atlas=load("res://assets/art/chapter2-portraits-v1.png")
	var column: int=clampi(face,0,3)
	var left: int=texture.atlas.get_width()*column/4
	var right: int=texture.atlas.get_width()*(column+1)/4
	texture.region=Rect2(left,cuts[row],right-left,cuts[row+1]-cuts[row]);texture.filter_clip=true
	return texture
static func frames(id: String) -> SpriteFrames:
	if frame_cache.has(id):return frame_cache[id]
	var result:=SpriteFrames.new();result.remove_animation("default")
	var poses: Dictionary={"idle":[0],"tell":[1],"reaction":[2],"settled":[3],"hit":[2],"down":[2],"strike":[1],"guard":[0],"connect":[1]}
	for direction: String in ["up","down","left","right"]:
		poses["idle_"+direction]=[0];poses["walk_"+direction]=[0];poses["run_"+direction]=[0];poses["interact_"+direction]=[1]
	for name: String in poses:
		result.add_animation(name);result.set_animation_speed(name,4)
		for index: int in poses[name]:result.add_frame(name,body(id,index))
	if id in ["nell","dev"]:result.set_meta("walk_key",id);result.set_meta("walk_mirror_left",true)  # stepping cycles from tools/walk_cycle
	frame_cache[id]=result;return result
