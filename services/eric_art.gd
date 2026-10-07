class_name NativeEricArt
extends RefCounted
## Professor Eric (Engineering Center, E03 boss; shorter than Jules, world height 46). His sheet is res://assets/art/eric-v1.png with
## res://assets/art/eric-atlas.json in the same layout as jakerson-atlas.json: cells 0-5 are his body
## (0 front, 1 talking, 2 tell, 3 reaction, 4 side facing right, 5 back) and cells 6-11 his
## portraits (0 neutral, 1 warm, 2 concern, 3 surprised, 4-5 spare). His step cycle comes from
## assets/art/walk (walk_key "eric"); an optional atlas "walk" entry can list extra cells instead.
## Until that sheet exists he borrows Dev's drawing with the jacket recoloured navy, so the fight and
## the lobby scene still play.
const SHEET: String="res://assets/art/eric-v1.png"
const ATLAS: String="res://assets/art/eric-atlas.json"
static var metadata: Dictionary={}
static var textures: Dictionary={}
static var animations: SpriteFrames
static func drawn() -> bool:return ResourceLoader.exists(SHEET) and FileAccess.file_exists(ATLAS)
static func data() -> Dictionary:
	if metadata.is_empty():metadata=JSON.parse_string(FileAccess.get_file_as_string(ATLAS))
	return metadata
static func cell(index: int) -> Texture2D:
	if textures.has(index):return textures[index]
	var c: Dictionary=data().cells[index];var r: Array=c.rect
	var texture:=AtlasTexture.new();texture.atlas=load(SHEET);texture.region=Rect2(r[0],r[1],r[2],r[3]);texture.filter_clip=true
	texture.set_meta("foot",Vector2(c.foot[0],c.foot[1]));texture.set_meta("body_height",c.height);texture.set_meta("explicit_direction",false)  # left reuses the right-facing cell, mirrored
	# Portraits are drawn at the dialogue size (64x64), so they are placed 1:1.
	if index>=6:texture.set_meta("portrait_scale",1.0);texture.set_meta("portrait_anchor",Vector2(32,64));texture.set_meta("portrait_target",Vector2(32,64))
	textures[index]=texture;return texture
static func body(index: int=0) -> Texture2D:
	if drawn():return cell(clampi(index,0,5))
	return _recolour("body"+str(index),NativeChapterArt.body("dev",index))
static func portrait(expression: int) -> Texture2D:
	if drawn():return cell(6+clampi(expression,0,5))
	return _recolour("face"+str(expression),NativeChapterArt.portrait("dev",expression))
static func frames() -> SpriteFrames:
	if animations!=null:return animations
	if not drawn():
		animations=SpriteFrames.new();animations.remove_animation("default")
		var source: SpriteFrames=NativeChapterArt.frames("dev")
		for name: String in source.get_animation_names():
			animations.add_animation(name);animations.set_animation_speed(name,source.get_animation_speed(name))
			for i: int in range(source.get_frame_count(name)):
				var original: Texture2D=source.get_frame_texture(name,i)
				animations.add_frame(name,_recolour("frame"+str(original.get_instance_id()),original))
		return animations
	animations=SpriteFrames.new();animations.remove_animation("default")
	var walk: Dictionary=data().get("walk",{})
	var poses: Dictionary={"idle":[0],"settled":[0],"tell":[2],"reaction":[3],"hit":[3],"down":[3],"strike":[2],"guard":[0],"connect":[1]}
	for direction: String in ["down","right","left","up"]:
		var index: int=5 if direction=="up" else 4 if direction in ["left","right"] else 0
		var side: String="right" if direction=="left" else direction
		poses["idle_"+direction]=[index];poses["interact_"+direction]=[1,2] if direction=="down" else [index]
		poses["walk_"+direction]=walk.get(side,[index])
	for name: String in poses:
		animations.add_animation(name);animations.set_animation_speed(name,8 if name.begins_with("walk_") else 2)
		for index: int in poses[name]:animations.add_frame(name,cell(int(index)))
	# A step cycle in assets/art/walk/walk.json under "eric" replaces his walk poses (NativeWalkArt).
	animations.set_meta("walk_key","eric");animations.set_meta("walk_mirror_left",true)
	return animations
## Dev's drawing with the red jacket turned navy (rows below the face only, so lips stay as they
## are). Keeps the foot and height the original carried.
static func _recolour(key: String, original: Texture2D) -> Texture2D:
	if original==null:return null
	if textures.has(key):return textures[key]
	var image: Image=NativePixelCast.source_image(original)
	if image==null:return original
	image=image.duplicate();image.convert(Image.FORMAT_RGBA8)
	for y: int in range(image.get_height()):
		for x: int in range(image.get_width()):
			var c: Color=image.get_pixel(x,y)
			if c.a<0.05 or c.s<0.28 or c.v<0.18:continue
			if not (c.h<0.035 or c.h>0.93) or c.s<0.4 or y<image.get_height()*(0.62 if key.begins_with("face") else 0.36):continue
			image.set_pixel(x,y,Color.from_hsv(0.6,clampf(c.s*0.75,0.0,1.0),clampf(c.v*0.95,0.0,1.0),c.a))
	var texture: ImageTexture=ImageTexture.create_from_image(image)
	for meta: StringName in original.get_meta_list():texture.set_meta(meta,original.get_meta(meta))
	textures[key]=texture;return texture
