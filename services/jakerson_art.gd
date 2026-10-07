class_name NativeJakersonArt
extends RefCounted
static var metadata: Dictionary={}
static var textures: Dictionary={}
static var animations: SpriteFrames
## Jakerson's outfit: "" is his jacket and hoodie, "tennis" his white warm-up suit and racket.
static var outfit: String=""
const SHEETS: Dictionary={"":"res://assets/art/jakerson-v1.png","tennis":"res://assets/art/jakerson-tennis-v1.png"}
static func wear(name: String) -> void:
	if not SHEETS.has(name):name=""
	if name==outfit:return
	outfit=name;textures.clear();animations=null
static func data() -> Dictionary:
	if metadata.is_empty():metadata=JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/jakerson-atlas.json"))
	return metadata
static func cell(index: int) -> Texture2D:
	if textures.has(index):return textures[index]
	var c: Dictionary=data().cells[index];var r: Array=c.rect
	var texture:=AtlasTexture.new();texture.atlas=load(str(SHEETS[outfit]));texture.region=Rect2(r[0],r[1],r[2],r[3]);texture.filter_clip=true
	texture.set_meta("foot",Vector2(c.foot[0],c.foot[1]));texture.set_meta("body_height",c.height);texture.set_meta("explicit_direction",true)
	textures[index]=texture;return texture
static func body(index: int=0) -> Texture2D:return cell(clampi(index,0,5))
static func portrait(expression: int) -> Texture2D:
	var face: int=clampi(expression,0,5);var texture: Texture2D=cell(6+face)
	# Measured paired-eye midpoint; wide cell padding must not resize the face.
	var anchors: Array=[Vector2(166,93),Vector2(245,93),Vector2(165,93),Vector2(165,93),Vector2(166,93),Vector2(166,93)]
	texture.set_meta("portrait_scale",64.0/269.0);texture.set_meta("portrait_anchor",anchors[face]);texture.set_meta("portrait_target",Vector2(40,32))
	return texture
## Frames for one outfit without changing what he is wearing now (drop-in cutscenes use "tennis").
static var wardrobe: Dictionary={}
static func frames_for(name: String) -> SpriteFrames:
	if not SHEETS.has(name):name=""
	if name==outfit:return frames()
	if wardrobe.has(name):return wardrobe[name]
	var keep: String=outfit;wear(name);var made: SpriteFrames=frames();wardrobe[name]=made;wear(keep)
	return made
static func frames() -> SpriteFrames:
	if animations!=null:return animations
	animations=SpriteFrames.new();animations.remove_animation("default")
	var poses: Dictionary={"idle":[0],"settled":[0],"tell":[2],"reaction":[3],"hit":[3],"down":[3]}
	for direction: String in ["down","right","left","up"]:
		var index: int=5 if direction=="up" else 4 if direction in ["left","right"] else 0
		poses["idle_"+direction]=[index];poses["walk_"+direction]=[index];poses["interact_"+direction]=[1,2] if direction=="down" else [index]
	for name: String in poses:
		animations.add_animation(name);animations.set_animation_speed(name,2)
		for index: int in poses[name]:animations.add_frame(name,cell(index))
	# A stepping walk (NativeWalkArt); his side view faces right and is mirrored for left.
	animations.set_meta("walk_key","jak"+outfit);animations.set_meta("walk_mirror_left",true)
	return animations
