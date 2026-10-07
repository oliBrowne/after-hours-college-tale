extends SceneTree
func _init() -> void:
	var bad := 0
	for id in ["val","autocomplete","chad","advisor","ta"]:
		var f := NativeBossArt.frames(id)
		var ok: bool = NativeBossArt.drawn(id) and f != null and f.has_animation("idle") and NativeBossArt.portrait(id,0) != null and NativeBossArt.entrance(id) != null and NativeBossArt.body(id,0).get_meta("body_height") > 70
		print(id, " ok=", ok, " entrance=", NativeBossArt.entrance(id).get_size(), " body=", NativeBossArt.body(id,0).get_size())
		if not ok: bad += 1
	print("boss_art failures: ", bad)
	quit(bad)
