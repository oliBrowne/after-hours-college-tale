extends SceneTree
## Actual Main dialogue cadence and viewport inputs; authored QA lines are a fixture.
var game: Variant
var complete: bool = false
var output: String
var observations: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("_run")

func _done() -> void:
	complete = true

func _confirm() -> void:
	var pressed := InputEventAction.new()
	pressed.action = &"confirm"
	pressed.pressed = true
	root.push_input(pressed)
	var released := InputEventAction.new()
	released.action = &"confirm"
	released.pressed = false
	root.push_input(released)

func _conversation(name: String, muted_effects: bool) -> void:
	game.audio.set_mix_gains(0.0 if muted_effects else 0.35, 0.0 if muted_effects else 0.5, 0.5, 0.0 if muted_effects else 0.325)
	game.audio.room_music("umc")
	game.audio.ambient("umc")
	game.state.settings.instant = false
	game.state.settings.blips = true
	complete = false
	var lines: Array = [
		["Jules", "Wait... did that booth know me?", "concern"],
		["Imani", "Breathe, Jules. I am here.", "warm"],
		["Cal", "One cable, then one answer.", "neutral"],
		["Jules", "Okay! One thing at a time.", "warm"],
		["Imani", "It is quiet. Too quiet?", "concern"],
		["Cal", "Good. We can do this together.", "warm"],
		["Jules", "This final long fixture line tests revealing the remainder early, without a burst of queued voices.", "concern"],
	]
	var record := AudioEffectRecord.new()
	record.format = AudioStreamWAV.FORMAT_16_BITS
	var bus: int = AudioServer.get_bus_index("Master")
	var index: int = AudioServer.get_bus_effect_count(bus)
	AudioServer.add_bus_effect(bus, record)
	record.set_recording_active(true)
	game.dialogue(lines, Callable(self, "_done"))
	var started: int = Time.get_ticks_msec()
	var line_started: int = started
	var last_line: int = 0
	var last_blips: Dictionary = (game.audio.get("_blip_last_ms") as Dictionary).duplicate()
	var voiced_counts: Dictionary = {}
	var pause_ticks: int = 0
	var skipped: bool = false
	var skip_variants: Dictionary = {}
	while not complete and Time.get_ticks_msec() - started < 40000:
		await physics_frame
		var now: int = Time.get_ticks_msec()
		if int(game.line_index) != last_line:
			last_line = int(game.line_index)
			line_started = now
			observations.append({"capture":name,"line":last_line,"speaker":lines[last_line][0],"mood":lines[last_line][2],"seconds":float(now-started)/1000.0})
		if int(game.phrase_pause) > 0:
			pause_ticks += 1
		var current: Dictionary = game.audio.get("_blip_last_ms")
		for speaker: String in ["jules", "imani", "cal"]:
			var key: String = speaker + ":vocal"
			var time: int = int(current.get(key, -1))
			if time != int(last_blips.get(key, -1)):
				if last_blips.has(key):
					assert(time - int(last_blips[key]) >= 145)
				last_blips[key] = time
				voiced_counts[speaker] = int(voiced_counts.get(speaker, 0)) + 1
		var text: String = str(game.dialogue_lines[game.line_index][1])
		if int(game.line_index) == 6 and not skipped and now-line_started > 450 and int(game.input_lock) == 0:
			assert(float(game.reveal) < text.length())
			_confirm()
			# A repeated press during input lock must not advance this line.
			_confirm()
			assert(int(game.line_index) == 6 and float(game.reveal) >= text.length())
			skip_variants = (game.audio.get("_blip_variants") as Dictionary).duplicate()
			skipped = true
		elif float(game.reveal) >= text.length() and int(game.input_lock) == 0 and now-line_started > 850:
			if skipped:
				assert(game.audio.get("_blip_variants") == skip_variants)
			_confirm()
	assert(complete and skipped and pause_ticks > 0)
	for speaker: String in ["jules", "imani", "cal"]:
		assert(int(voiced_counts.get(speaker, 0)) > 3)
	await create_timer(0.25).timeout
	record.set_recording_active(false)
	var wav: AudioStreamWAV = record.get_recording()
	assert(wav.data.size() > 48000 and wav.save_to_wav(output.path_join(name + ".wav")) == OK)
	AudioServer.remove_bus_effect(bus, index)
	observations.append({"capture":name,"seconds":float(Time.get_ticks_msec()-started)/1000.0,"voiceEvents":voiced_counts,"punctuationPauseTicks":pause_ticks,"earlyRevealSkip":skipped,"skipBurstAbsent":true,"effectsGain":0.0 if muted_effects else 0.5,"voiceGain":0.5})
	print("DIALOGUE CAPTURE " + name + " events=" + str(voiced_counts) + " punctuation=" + str(pause_ticks))

func _run() -> void:
	output = OS.get_environment("AFTER_HOURS_AUDIO_QA")
	assert(not output.is_empty())
	DirAccess.make_dir_recursive_absolute(output)
	game = (load("res://scenes/main.tscn") as PackedScene).instantiate()
	root.add_child(game)
	await process_frame
	game.qa = true
	game.saves = NativeSaveService.new(output.path_join("dialogue-isolated-saves"))
	await _conversation("dialogue-normal-effects-muted", true)
	await _conversation("dialogue-normal-full-mix", false)
	var file: FileAccess = FileAccess.open(output.path_join("dialogue-normal-fixture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"source":"Production Main dialogue API, authored QA fixture lines, actual viewport InputEventAction confirmations", "observations":observations,"performedSpeech":false,"humanListeningApproval":false}, "\t"))
	file.close()
	game.dialogue_callback = Callable()
	game.menu_options.clear()
	game.audio.shutdown()
	game.queue_free()
	await process_frame
	OS.delay_msec(150)
	await process_frame
	print("NORMAL DIALOGUE PASS: actual Main reveal/punctuation/emotions/skip/cooldown, effects-muted voices and full mix, native Master captures.")
	quit(0)
