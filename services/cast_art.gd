class_name NativeCastArt
extends RefCounted

## Generated cast sheets remain untouched. Atlas regions trim transparent padding
## at runtime; scene sprites keep their planted foot pivot and nearest filtering.
const PEOPLE = ["Mara", "Eli", "Chip", "Deion Sanders", "Todd Saliman"]
const OBJECTS = ["Flyerer", "Pip", "Pin Pal", "CLAIM", "Booth"]
const IDS = ["cal", "mags", "jakerson", "mara", "eli", "chip", "deion", "todd", "walt", "encore", "rook", "nell", "dev", "errata", "autocomplete", "eric", "cone", "chad", "val", "val_small"]
const OBJECT_IDS = ["flyer", "pip", "pinpal", "claim", "booth"]
const BODY_REGIONS = {"mara": [[70, 0, 165, 256], [299, 0, 188, 256], [525, 0, 179, 256], [753, 0, 167, 256], [983, 0, 132, 256], [1155, 0, 161, 256]], "eli": [[55, 256, 175, 240], [292, 256, 213, 240], [521, 256, 194, 240], [745, 256, 199, 240], [990, 256, 128, 240], [1157, 256, 166, 240]], "chip": [[44, 496, 189, 235], [285, 496, 222, 235], [508, 496, 211, 235], [747, 496, 196, 235], [965, 496, 165, 235], [1148, 496, 194, 235]], "deion": [[55, 731, 158, 241], [299, 731, 199, 241], [521, 731, 190, 241], [747, 731, 186, 241], [995, 731, 131, 241], [1165, 731, 160, 241]], "todd": [[59, 11, 306, 608], [423, 11, 366, 608], [874, 11, 347, 608], [60, 644, 365, 578], [532, 627, 191, 600], [895, 632, 287, 595]], "flyer": [[29, 21, 269, 313], [339, 15, 280, 319], [662, 21, 271, 313]], "pip": [[53, 334, 251, 279], [351, 331, 274, 282], [696, 332, 259, 281]], "pinpal": [[66, 613, 190, 321], [368, 613, 254, 321], [714, 613, 197, 321]], "claim": [[12, 934, 297, 340], [315, 934, 351, 340], [669, 934, 292, 340]], "booth": [[12, 1275, 298, 304], [334, 1270, 303, 309], [666, 1272, 295, 307]]}
const BODY_ANCHORS = {"mara": [[147, 253], [387.5, 253], [617, 253], [834, 253], [1054.5, 253], [1233, 253]], "eli": [[142.5, 495], [380.5, 495], [615, 495], [850.5, 495], [1057, 495], [1236, 495]], "chip": [[138, 729], [381, 729], [611.5, 729], [845.5, 729], [1052.5, 729], [1243.5, 729]], "deion": [[137, 970], [383.5, 969], [612.5, 970], [839, 969], [1054, 970], [1241, 970]], "todd": [[214.5, 609], [625, 609], [1044.5, 609], [267.5, 1212], [619.5, 1217], [1045.5, 1217]], "flyer": [[183.5, 324], [499.5, 324], [824.5, 324]], "pip": [[163.5, 610], [487, 610], [816, 610]], "pinpal": [[160.5, 925], [472, 925], [810.5, 925]], "claim": [[158.5, 1264], [484.5, 1264], [813, 1266]], "booth": [[167.5, 1569], [496.5, 1569], [832, 1569]]}
const STANDING_HEIGHT = {"mara": 248, "eli": 239, "chip": 232, "deion": 236, "todd": 588, "flyer": 292, "pip": 268, "pinpal": 303, "claim": 327, "booth": 291}
static var textures: Dictionary = {}
static var images: Dictionary = {}
static var animations: Dictionary = {}
static var portrait_layouts: Dictionary = {}

static func _region(path: String, column: int, columns: int, top: int, bottom: int, trim: bool = false) -> Texture2D:
	var key: String = "%s/%d/%d/%d/%s" % [path, column, top, bottom, trim]
	if textures.has(key): return textures[key]
	var source: Texture2D = load(path)
	var left: int = floori(float(source.get_width()) * column / columns)
	var right: int = floori(float(source.get_width()) * (column + 1) / columns)
	var rect: Rect2i = Rect2i(left, top, right - left, bottom - top)
	if trim:
		if not images.has(path): images[path] = source.get_image()
		var image: Image = images[path]
		var used: Rect2i = image.get_region(rect).get_used_rect()
		if used.has_area(): rect = Rect2i(rect.position + used.position, used.size)
	var atlas := AtlasTexture.new()
	atlas.atlas = source
	atlas.region = Rect2(rect)
	atlas.filter_clip = true
	textures[key] = atlas
	return atlas

static func portrait(speaker: String,expression: int) -> Texture2D:
	var key: String="native_portrait/"+speaker+"/"+str(expression)
	if textures.has(key):return textures[key]
	var raw: Texture2D=source_portrait(speaker,expression)
	if raw!=null and not raw.has_meta("portrait_scale"):
		if not portrait_layouts.has(speaker):
			var bounds:=Rect2i()
			for face: int in range(4):
				var image: Image=NativePixelCast.source_image(source_portrait(speaker,face));NativePixelCast.crisp(image)
				var used: Rect2i=image.get_used_rect()
				bounds=bounds.merge(used) if bounds.has_area() else used
			portrait_layouts[speaker]={"scale":64.0/maxi(bounds.size.x,bounds.size.y),"anchor":Vector2(bounds.get_center().x,bounds.end.y)}
		raw.set_meta("portrait_scale",portrait_layouts[speaker].scale)
		raw.set_meta("portrait_anchor",portrait_layouts[speaker].anchor)
		raw.set_meta("portrait_target",Vector2(32,64))
	var fitted: Texture2D=NativePixelCast.portrait(raw)
	if fitted!=null:textures[key]=fitted
	return fitted
## Speakers that wear one of the encounter characters' own portraits (the people on the Hill, the court and the paths).
const ENCOUNTER_SPEAKERS: Dictionary = {"Tanner": "tanner", "Kyle": "kyle", "Drummer": "drummer", "Frisbee kid": "frisbee", "Volunteer": "advisor_mini", "Philosophy major": "philosophy_major", "Hippie": "hippie", "Business major": "business_major", "Professor": "professor", "Engineering major": "engineering_major", "Cyclist": "cyclist", "Athlete": "athlete", "Runner": "runner", "Commuter Cyclist": "cyclist", "Altitude Runner": "runner", "Hacky-Sack Hippie": "hippie", "Business Major": "business_major", "Sunbeam": "sunbeam"}
static func source_portrait(speaker: String, expression: int) -> Texture2D:
	if ENCOUNTER_SPEAKERS.has(speaker) and NativeBossArt.drawn(str(ENCOUNTER_SPEAKERS[speaker])):return NativeBossArt.portrait(str(ENCOUNTER_SPEAKERS[speaker]),expression)
	if speaker=="Jakerson":return NativeJakersonArt.portrait(expression)
	if speaker=="Professor Eric":return NativeEricArt.portrait(expression)
	if speaker=="VAL" and NativeBossArt.drawn("val"):return NativeBossArt.portrait("val",expression)
	if speaker in ["VAL","Val","CONE COMMITTEE"]:return NativeFinalArt.portrait({"VAL":"val","Val":"val_small","CONE COMMITTEE":"cone"}[speaker],expression)
	# VAL (the VP) and Chad have their own sheets; Chad falls back to Eli's look without his.
	if speaker=="Chad":return NativeBossArt.portrait("chad",expression) if NativeBossArt.drawn("chad") else source_portrait("Eli",expression)
	# AUTOCOMPLETE (INDEX's replacement) has its own sheet; without it the old INDEX portraits stand in.
	if speaker=="AUTOCOMPLETE" and NativeBossArt.drawn("autocomplete"):return NativeBossArt.portrait("autocomplete",expression)
	# Gwen the Red (ERRATA's replacement) has her own sheet; without it the old ERRATA portraits stand in.
	if speaker=="Gwen the Red":return NativeBossArt.portrait("ta",expression) if NativeBossArt.drawn("ta") else NativeChapterArt.portrait("errata",expression)
	if speaker in ["Nell","Dev","ERRATA","AUTOCOMPLETE","LOADBEARER"]:return NativeChapterArt.portrait(speaker.to_lower(),expression)
	if speaker in ["Walt", "ENCORE", "Rook"]: return NativeExpansionArt.portrait(speaker.to_lower(), expression)
	var face: int = clampi(expression, 0, 3)
	var row: int = ["Jules", "Imani", "Cal", "Mags"].find(speaker)
	if row >= 0:
		return _region("res://assets/art/dialogue-expressions-v2.png", face, 4, floori(row * 1254.0 / 4), floori((row + 1) * 1254.0 / 4))
	row = PEOPLE.find(speaker)
	if row >= 0:
		var cuts: Array = [0, 305, 585, 859, 1122, 1402]
		return _region("res://assets/art/support-dialogue-v3.png", face, 4, cuts[row], cuts[row + 1])
	row = OBJECTS.find(speaker)
	if row >= 0:
		var cuts: Array = [0, 274, 550, 830, 1102, 1402]
		return _region("res://assets/art/object-dialogue-v3.png", face, 4, cuts[row], cuts[row + 1])
	return null

static func body(id: String, frame: int = 0) -> Texture2D:
	if id in ["cal","mags","todd"]:return NativeCampusSupportArt.body(id,frame)
	if id=="jakerson":return NativeJakersonArt.body(frame)
	if id=="eric":return NativeEricArt.body(frame)
	if id in ["val","chad","autocomplete"] and NativeBossArt.drawn(id):return NativeBossArt.body(id,frame)
	if id=="chad":return body("eli",frame)
	if id in ["cone","val","val_small"]:return NativeFinalArt.body(id,frame)
	if id=="errata" and NativeBossArt.drawn("ta"):return NativeBossArt.body("ta",frame)
	if id in NativeChapterTwo.BOSSES or id in ["nell","dev"]:return NativeChapterArt.body(id,frame)
	if id in ["walt", "encore", "rook"]: return NativeExpansionArt.body(id, frame)
	if not BODY_REGIONS.has(id): return null
	var index: int = clampi(frame, 0, BODY_REGIONS[id].size() - 1)
	var key: String = "body/%s/%d" % [id, index]
	if textures.has(key): return textures[key]
	var path: String = "res://assets/art/todd-world-v3.png" if id == "todd" else "res://assets/art/object-world-v3.png" if id in OBJECT_IDS else "res://assets/art/support-world-v3.png"
	var raw: Array = BODY_REGIONS[id][index]
	var anchor: Array = BODY_ANCHORS[id][index]
	var atlas := AtlasTexture.new()
	atlas.atlas = load(path)
	atlas.region = Rect2(raw[0], raw[1], raw[2], raw[3])
	atlas.filter_clip = true
	atlas.set_meta("foot", Vector2(anchor[0] - raw[0], anchor[1] - raw[1]))
	atlas.set_meta("body_height", STANDING_HEIGHT[id])
	textures[key] = atlas
	return atlas

static func frames(id: String) -> SpriteFrames:
	if id in ["cal","mags","todd"]:return NativeCampusSupportArt.frames(id)
	if id=="walt":return NativePartyBattleArt.frames(id)
	if id=="jakerson":return NativeJakersonArt.frames()
	if id=="eric":return NativeEricArt.frames()
	if id in ["val","chad","autocomplete"] and NativeBossArt.drawn(id):return NativeBossArt.frames(id)
	if id in ["cone","val","val_small"]:return NativeFinalArt.frames(id)
	if id=="chad":return frames("eli")
	if id=="errata" and NativeBossArt.drawn("ta"):return NativeBossArt.frames("ta")
	if id in NativeChapterTwo.BOSSES or id in ["nell","dev"]:return NativeChapterArt.frames(id)
	if id in ["walt", "encore", "rook"]: return NativeExpansionArt.world_frames(id)
	if animations.has(id): return animations[id]
	var result := SpriteFrames.new()
	result.remove_animation("default")
	var object: bool = id in OBJECT_IDS
	var poses: Dictionary = {"idle": [0], "tell": [1 if object else 2], "reaction": [1 if object else 3], "settled": [2 if object else 0], "hit": [1 if object else 3], "down": [1 if object else 3]}
	for direction: String in ["down", "left", "right", "up"]:
		var idle: int = 0 if direction == "down" or object else 5 if direction == "up" else 4
		poses["idle_" + direction] = [idle]
		poses["walk_" + direction] = [idle, idle]
		poses["run_" + direction] = [idle, idle]
		poses["interact_" + direction] = [0, 1] if direction == "down" else [idle]
	for name: String in poses:
		result.add_animation(name)
		result.set_animation_speed(name, 3.0)
		for index: int in poses[name]: result.add_frame(name, body(id, index))
	if id in ["mara", "eli", "chip", "deion"]: result.set_meta("walk_key", id); result.set_meta("walk_mirror_left", true)  # stepping cycles from tools/walk_cycle
	animations[id] = result
	return result

static func world_height(id: String) -> float:
	if id=="autocomplete":return NativeBossArt.world_height(id) if NativeBossArt.drawn(id) else 56.0
	if NativeBossArt.encounter_cast(id):return NativeBossArt.world_height(id)
	if id=="errata":return NativeBossArt.world_height("ta") if NativeBossArt.drawn("ta") else 56.0
	return float({"jules":52,"imani":50,"walt":52,"cal":52,"mags":54,"mara":52,"eli":54,"nell":50,"dev":52,"eric":46,"val_small":34,"rook":56,"jakerson":60,"flyer":64,"pip":36,"pinpal":76,"claim":88}.get(id,56))
static func fit(sprite: AnimatedSprite2D,height: float) -> void:
	NativePixelCast.fit(sprite,roundi(height))

static func draw_body(node: Node2D, id: String, pose: String, height: float, elapsed: float, reduced: bool) -> void:
	var frame: int = 2 if pose in ["resolved", "settled"] else 1 if pose in ["tell", "windup", "active", "hit", "wave", "interact"] else 0
	# Booth's middle pose is alarm; its open grille conveys a speaking response.
	if id == "booth" and pose in ["tell", "interact", "wave"]: frame = 2
	var texture: Texture2D = NativePixelCast.texture(body(id,frame),roundi(height),float(body(id,0).get_meta("body_height")))
	if texture == null: return
	var scale: float = 1.0
	var anchor: Vector2 = texture.get_meta("foot")
	var sway: float=roundf(sin(elapsed*24.0)*3.0) if pose=="hit" and not reduced else 0.0
	if pose in ["idle","resolved","settled"] and not reduced and NativeIdleMotion.breathing_at(elapsed):texture=NativePixelCast.breathing(texture)
	var tint: Color = Color("b5827b") if pose == "down" else Color.WHITE
	node.draw_texture_rect(texture, Rect2((-anchor * scale + Vector2(sway, 0)).round(), Vector2(texture.get_size() * scale).round()), false, tint)
