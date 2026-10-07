extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var director: Node = (load("res://services/audio_director.gd") as GDScript).new()
	root.add_child(director)
	await process_frame
	var cases: Array = [
		["Mara", "mara", "vocal-mags-neutral-1", 0.9],
		["Eli", "eli", "vocal-cal-neutral-1", 1.12],
		["Booth voice", "booth", "vocal-jules-neutral-1", 0.86],
		["Advisor Bev", "advisor bev", "vocal-mags-neutral-1", 0.96],
		["Pin Pal", "pinpal", "vocal-todd-neutral-1", 0.92],
		["Pip", "pip", "vocal-chip-neutral-1", 1.34],
		["Jules Navarro", "jules", "vocal-jules-neutral-1", 1.0],
	]
	for entry: Array in cases:
		director.call("voiced_blip", str(entry[0]))
		var matched: bool = false
		for player: AudioStreamPlayer in director.get("_effect_players"):
			if str(player.get_meta("speaker")) == str(entry[1]):
				assert(player.stream != null)
				assert(player.stream.resource_path.ends_with(str(entry[2]) + ".wav"))
				assert(absf(player.pitch_scale - float(entry[3])) < 0.001)
				assert(player.bus == &"Voices")
				matched = true
		assert(matched, "Missing supporting voice: " + str(entry[0]))
		var cycle: String = str(entry[1]) + ":vocal"
		assert(int((director.get("_blip_variants") as Dictionary)[cycle]) == 1)
		director.call("voiced_blip", str(entry[0]))
		assert(int((director.get("_blip_variants") as Dictionary)[cycle]) == 1)
	# Shifted vocal pool entries must not transpose the next ordinary effect.
	for player: AudioStreamPlayer in director.get("_effect_players"):
		player.stop()
	var first: AudioStreamPlayer = (director.get("_effect_players") as Array)[0]
	first.pitch_scale = 1.34
	director.call("effect", "confirm")
	assert(first.pitch_scale == 1.0 and first.bus == &"Effects")
	director.call("set_paused", true)
	director.call("voiced_blip", "Mara", "warm")
	for player: AudioStreamPlayer in director.get("_effect_players"):
		assert(not player.playing)
	director.call("shutdown")
	director.queue_free()
	await process_frame
	OS.delay_msec(150)
	await process_frame
	print("SUPPORTING VOICES PASS: six audible reused families, aliases, pitch profiles, original Jules unchanged, cooldown, effect pitch reset, pause.")
	quit(0)
