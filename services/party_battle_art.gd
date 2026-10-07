class_name NativePartyBattleArt
extends RefCounted
static var metadata: Dictionary={}
static var textures: Dictionary={}
static var animations: Dictionary={}
static func data() -> Dictionary:
	if metadata.is_empty():metadata=JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/party-battle-atlas-v2.json"))
	return metadata
static func body(id: String,index: int) -> Texture2D:
	var key: String=id+str(index)
	if textures.has(key):return textures[key]
	var entry: Dictionary=data()[id][clampi(index,0,11)];var r: Array=entry.rect
	var atlas:=AtlasTexture.new();atlas.atlas=load("res://assets/art/party-battle-v2.png");atlas.region=Rect2(r[0],r[1],r[2],r[3]);atlas.filter_clip=true
	atlas.set_meta("foot",Vector2(entry.foot[0],entry.foot[1]));atlas.set_meta("body_height",data()[id][0].height);atlas.set_meta("explicit_direction",true)
	textures[key]=atlas;return atlas
static func frames(id: String) -> SpriteFrames:
	if animations.has(id):return animations[id]
	var result:=SpriteFrames.new();result.remove_animation("default")
	var poses: Dictionary={"idle":[0,1,0],"strike":[2,2,3,4],"guard":[5],"connect":[6,7],"talent":[8,8,6],"hit":[9,9,0],"down":[10],"settled":[11]}
	poses["idle_down"]=poses.idle;poses["interact_down"]=[2];poses["tell"]=[2];poses["reaction"]=poses.hit
	for name: String in poses:
		result.add_animation(name);result.set_animation_loop(name,name=="idle");result.set_animation_speed(name,2 if name=="idle" else 6)
		for frame: int in poses[name]:result.add_frame(name,body(id,frame))
	animations[id]=result;return result
