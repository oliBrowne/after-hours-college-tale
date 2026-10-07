class_name NativeChapterArt
extends RefCounted
static var metadata: Dictionary={}
static var cache: Dictionary={}
static var frame_cache: Dictionary={}
## AUTOCOMPLETE took over INDEX's boss (2026-10-07). Its own sheet is NativeBossArt's; when that is
## missing, the old INDEX cells in chapter2-atlas.json stand in under the new id.
const LEGACY: Dictionary={"autocomplete":"index"}
## Gwen the Red took over ERRATA's boss the same way: her sheet is NativeBossArt's "ta" (routed in
## cast_art.gd by the id "errata"); the errata cells in chapter2-atlas.json stay as her fallback.
static func resolve(id: String) -> String:return LEGACY.get(id,id)
static func data() -> Dictionary:
	if metadata.is_empty():metadata=JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/chapter2-atlas.json"))
	return metadata
static func body(id: String, frame: int=0) -> Texture2D:
	id=resolve(id)
	var key: String=id+str(frame)
	if cache.has(key):return cache[key]
	var entry: Dictionary=data()[id][clampi(frame,0,3)]
	var raw: Array=entry.rect
	var texture:=AtlasTexture.new();texture.atlas=load("res://assets/art/chapter2-bodies-v1.png")
	texture.region=Rect2(raw[0],raw[1],raw[2],raw[3]);texture.filter_clip=true
	texture.set_meta("foot",Vector2(entry.foot[0],entry.foot[1]));texture.set_meta("body_height",entry.height)
	cache[key]=texture;return texture
static func portrait(id: String, face: int) -> Texture2D:
	var row: int=data().ids.find(resolve(id))
	var cuts: Array=data().portrait_cuts
	var texture:=AtlasTexture.new();texture.atlas=load("res://assets/art/chapter2-portraits-v1.png")
	var column: int=clampi(face,0,3)
	var left: int=texture.atlas.get_width()*column/4
	var right: int=texture.atlas.get_width()*(column+1)/4
	texture.region=Rect2(left,cuts[row],right-left,cuts[row+1]-cuts[row]);texture.filter_clip=true
	return texture
static func frames(id: String) -> SpriteFrames:
	if frame_cache.has(id):return frame_cache[id]
	var source: String=resolve(id)
	var result:=SpriteFrames.new();result.remove_animation("default")
	var poses: Dictionary={"idle":[0],"tell":[1],"reaction":[2],"settled":[3],"hit":[2],"down":[2],"strike":[1],"guard":[0],"connect":[1]}
	for direction: String in ["up","down","left","right"]:
		poses["idle_"+direction]=[0];poses["walk_"+direction]=[0];poses["run_"+direction]=[0];poses["interact_"+direction]=[1]
	for name: String in poses:
		result.add_animation(name);result.set_animation_speed(name,4)
		for index: int in poses[name]:result.add_frame(name,body(source,index))
	if id in ["nell","dev"]:result.set_meta("walk_key",id);result.set_meta("walk_mirror_left",true)  # stepping cycles from tools/walk_cycle
	elif source in ["errata","index"]:result.set_meta("idle_key",source)  # blink and idle poses from assets/art/idle
	frame_cache[id]=result;return result
