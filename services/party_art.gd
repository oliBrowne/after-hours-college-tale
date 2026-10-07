class_name NativePartyArt
extends RefCounted
static var metadata: Dictionary={}
static var textures: Dictionary={}
static var animations: Dictionary={}
static func data() -> Dictionary:
	if metadata.is_empty():metadata=JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/party-world-atlas.json"))
	return metadata
static func body(id: String, index: int) -> Texture2D:
	var key: String=id+str(index)
	if textures.has(key):return textures[key]
	var entry: Dictionary=data()[id].cells[index]
	var texture:=AtlasTexture.new();texture.atlas=load("res://assets/art/"+str(data()[id].path))
	var r: Array=entry.rect;texture.region=Rect2(r[0],r[1],r[2],r[3]);texture.filter_clip=true
	texture.set_meta("foot",Vector2(entry.foot[0],entry.foot[1]));texture.set_meta("body_height",entry.height);texture.set_meta("explicit_direction",true)
	textures[key]=texture;return texture
static func frames(id: String) -> SpriteFrames:
	if animations.has(id):return animations[id]
	var result:=SpriteFrames.new();result.remove_animation("default")
	var directions: Array[String]=["down","up","right","left"]
	for row: int in range(4):
		for prefix: String in ["idle_","walk_","run_","interact_"]:
			var name: String=prefix+directions[row]
			result.add_animation(name);result.set_animation_speed(name,10)
			for index: int in range(6 if prefix in ["walk_","run_"] else 1):result.add_frame(name,body(id,row*6+index))
	# Resolved world cameos use the same standing pose as the joined party.
	result.add_animation("settled");result.add_frame("settled",body(id,0))
	# A forceful resolved world cameo has recovered to its standing stance.
	result.add_animation("down");result.add_frame("down",body(id,0))
	# Stepping walk cycles (NativeWalkArt) replace the walk rows once the frames are fitted.
	result.set_meta("walk_key",id)
	animations[id]=result;return result
