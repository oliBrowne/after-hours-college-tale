class_name NativeCampusSupportArt
extends RefCounted
static var data_cache: Dictionary={}
static var textures: Dictionary={}
static var frame_cache: Dictionary={}
static func data() -> Dictionary:
	if data_cache.is_empty():
		data_cache=JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/cal-mags-atlas.json"))
		data_cache.todd=JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/todd-atlas-v4.json")).todd
	return data_cache
static func body(id: String,index: int=0) -> Texture2D:
	var key: String=id+str(index)
	if textures.has(key):return textures[key]
	var entry: Dictionary=data()[id][clampi(index,0,5)];var r: Array=entry.rect
	var t:=AtlasTexture.new();t.atlas=load("res://assets/art/todd-world-v4.png" if id=="todd" else "res://assets/art/cal-mags-world-v1.png");t.region=Rect2(r[0],r[1],r[2],r[3]);t.filter_clip=true
	t.set_meta("foot",Vector2(entry.foot[0],entry.foot[1]));t.set_meta("body_height",entry.height);t.set_meta("explicit_direction",false)
	textures[key]=t;return t
static func frames(id: String) -> SpriteFrames:
	if frame_cache.has(id):return frame_cache[id]
	var frames:=SpriteFrames.new();frames.remove_animation("default")
	var poses: Dictionary={"idle":[0],"tell":[2],"reaction":[3],"settled":[0],"hit":[3],"down":[3]}
	for direction: String in ["down","up","right","left"]:
		var base: int=5 if direction=="up" else 4 if direction in ["left","right"] else 0
		poses["idle_"+direction]=[base];poses["interact_"+direction]=[0,2] if direction=="down" else [base]
	for name: String in poses:
		frames.add_animation(name);frames.set_animation_speed(name,3);frames.set_animation_loop(name,str(name).begins_with("idle"))
		for index: int in poses[name]:frames.add_frame(name,body(id,index))
	frame_cache[id]=frames;return frames
