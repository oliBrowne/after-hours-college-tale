class_name NativeBossArt
extends RefCounted
## One loader for every boss drawn to the Professor Eric contract (tools/boss_art/<id>/): a sheet
## res://assets/art/<id>-v1.png with res://assets/art/<id>-atlas.json. Cells 0-5 are the body
## (0 front, 1 talking, 2 tell, 3 reaction, 4 side facing right, 5 back), cells 6-11 the portraits
## (0 neutral, 1 warm, 2 concern, 3 surprised, 4-5 spare) and cell 12, when present, the entrance pose
## named "<id>-entrance". The entrance is also baked to res://assets/art/entrance/<id>.png (feet at the
## bottom centre) for the gym-leader card (tools/boss_art/bake_entrance.py).
## ids: val (the sheet keeps the id "val" in its file names; talk and idle files use the key "val_vp"),
## autocomplete, chad, advisor, ta; peloton, sunbeam, tanner, kyle and the encounter cast follow.
## An optional atlas "walk" entry ({"right":[cells]}) lists extra step cells, and a step cycle in
## assets/art/walk under walk_key replaces them (NativeWalkArt).
const WORLD_HEIGHT: Dictionary={"val":54,"autocomplete":60,"chad":52,"advisor":50,"ta":52,"peloton":54,"sunbeam":52,"tanner":52,"kyle":52,"cyclist":50,"runner":52,"hippie":50,"drummer":51,"business_major":50,"engineering_major":50,"philosophy_major":52,"frisbee":50,"athlete":52,"professor":52,"advisor_mini":50}
const WALK_KEY: Dictionary={"val":"val_vp"}
## Internal boss ids whose art is filed under another id: the fight, flags and saves keep the old id
## (errata) while the sheet, entrance pose and portraits are Gwen the Red's ("ta").
const ART_ALIAS: Dictionary={"errata":"ta"}
static var metadata: Dictionary={}
static var textures: Dictionary={}
static var animations: Dictionary={}
static func art_id(id: String) -> String:return ART_ALIAS.get(id,id)
static func sheet(id: String) -> String:return "res://assets/art/%s-v1.png"%id
static func atlas(id: String) -> String:return "res://assets/art/%s-atlas.json"%id
static func drawn(id: String) -> bool:return ResourceLoader.exists(sheet(id)) and FileAccess.file_exists(atlas(id))
static func data(id: String) -> Dictionary:
	if not metadata.has(id):metadata[id]=JSON.parse_string(FileAccess.get_file_as_string(atlas(id)))
	return metadata[id]
static func world_height(id: String,fallback: float=52.0) -> float:return float(WORLD_HEIGHT.get(id,fallback))
static func cell(id: String,index: int) -> Texture2D:
	var key: String="%s/%d"%[id,index]
	if textures.has(key):return textures[key]
	var c: Dictionary=data(id).cells[index];var r: Array=c.rect
	var texture:=AtlasTexture.new();texture.atlas=load(sheet(id));texture.region=Rect2(r[0],r[1],r[2],r[3]);texture.filter_clip=true
	texture.set_meta("foot",Vector2(c.foot[0],c.foot[1]));texture.set_meta("body_height",c.height);texture.set_meta("explicit_direction",false)  # left reuses the right-facing cell, mirrored
	# Portraits are drawn at the dialogue size (64x64), so they are placed 1:1.
	if index>=6 and index<12:texture.set_meta("portrait_scale",1.0);texture.set_meta("portrait_anchor",Vector2(32,64));texture.set_meta("portrait_target",Vector2(32,64))
	textures[key]=texture;return texture
static func body(id: String,index: int=0) -> Texture2D:
	if not drawn(id):return null
	return cell(id,clampi(index,0,5))
static func portrait(id: String,expression: int) -> Texture2D:
	if not drawn(id):return null
	return cell(id,6+clampi(expression,0,5))
## The entrance pose from cell 12, or the baked file, or null (the card then falls back to the idle pose).
static func entrance(id: String) -> Texture2D:
	var path: String="res://assets/art/entrance/%s.png"%id
	if ResourceLoader.exists(path):return load(path)
	if drawn(id) and data(id).cells.size()>12:return cell(id,12)
	return null
static func frames(id: String) -> SpriteFrames:
	if animations.has(id):return animations[id]
	if not drawn(id):return null
	var result:=SpriteFrames.new();result.remove_animation("default")
	var walk: Dictionary=data(id).get("walk",{})
	var poses: Dictionary={"idle":[0],"settled":[0],"tell":[2],"reaction":[3],"hit":[3],"down":[3],"strike":[2],"guard":[0],"connect":[1]}
	for direction: String in ["down","right","left","up"]:
		var index: int=5 if direction=="up" else 4 if direction in ["left","right"] else 0
		var side: String="right" if direction=="left" else direction
		poses["idle_"+direction]=[index];poses["interact_"+direction]=[1,2] if direction=="down" else [index]
		poses["walk_"+direction]=walk.get(side,[index])
	for name: String in poses:
		result.add_animation(name);result.set_animation_speed(name,8 if name.begins_with("walk_") else 2)
		for index: int in poses[name]:result.add_frame(name,cell(id,int(index)))
	result.set_meta("walk_key",WALK_KEY.get(id,id));result.set_meta("walk_mirror_left",true)
	animations[id]=result;return result
