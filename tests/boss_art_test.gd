extends SceneTree
func _init() -> void:
	var bad := 0
	for id in ["val","autocomplete","chad","advisor","ta","peloton","sunbeam","tanner","kyle","cyclist","runner","hippie","drummer","business_major","engineering_major","philosophy_major","frisbee"]:
		var f := NativeBossArt.frames(id)
		var ok: bool = NativeBossArt.drawn(id) and f != null and f.has_animation("idle") and NativeBossArt.portrait(id,0) != null and (id in ["cyclist","runner","hippie","drummer","business_major","engineering_major","philosophy_major","frisbee"] or NativeBossArt.entrance(id) != null) and NativeBossArt.body(id,0).get_meta("body_height") > 70
		print(id, " ok=", ok, " body=", NativeBossArt.body(id,0).get_size())
		if not ok: bad += 1
	print("boss_art failures: ", bad)
	quit(bad)
