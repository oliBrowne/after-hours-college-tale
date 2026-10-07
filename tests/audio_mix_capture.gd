extends SceneTree
## Real Main scene/menus/rules/mixer, fixture boss entry, automated lawful inputs.
## This is encounter QA, not evidence of a complete world route or human audition.
const GameScene: PackedScene = preload("res://scenes/main.tscn")
var events: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var output: String = OS.get_environment("AFTER_HOURS_AUDIO_QA")
	if output.is_empty():
		push_error("Set AFTER_HOURS_AUDIO_QA to a writable QA output directory.")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var game: Variant = GameScene.instantiate()
	root.add_child(game)
	await process_frame
	game.saves = NativeSaveService.new(output.path_join("isolated-saves"))
	game.state.flags.imani_joined = true
	game.state.flags.cal_joined = true
	game.state.settings.music = 0.65
	game.state.settings.effects = 0.7
	game.state.settings.instant = false
	game.state.settings.blips = true
	game.state.settings.assist = 1.0
	game.state.settings.damageAssist = true
	game.state.settings.autoTiming = true
	game.audio.set_volumes(0.65, 0.7)
	game.boss_id = "chip"
	game.checkpoint = game.state.duplicate(true)
	var recording := AudioEffectRecord.new()
	recording.format = AudioStreamWAV.FORMAT_16_BITS
	var master: int = AudioServer.get_bus_index("Master")
	var effect_index: int = AudioServer.get_bus_effect_count(master)
	AudioServer.add_bus_effect(master, recording)
	recording.set_recording_active(true)
	game.dialogue([["Chip", "Okay! One small rehearsal.", "warm"], ["Jules", "One thing at a time.", "concern"]], Callable(game, "begin_battle"))
	var started: int = Time.get_ticks_msec()
	var last_mode: int = -1
	var last_stage: int = -1
	var hop_release: bool = false
	var result_at: int = -1
	while Time.get_ticks_msec() - started < 95000:
		await physics_frame
		var current_mode: int = int(game.mode)
		if current_mode != last_mode or int(game.boss_stage) != last_stage:
			events.append({"seconds":float(Time.get_ticks_msec()-started)/1000.0,"mode":current_mode,"stage":int(game.boss_stage),"beat":game.audio.beat_position(),"hp":int(game.battle.get("hp",180))})
			last_mode = current_mode
			last_stage = int(game.boss_stage)
		if current_mode == 2:
			var text: String = str(game.dialogue_lines[game.line_index][1])
			if float(game.reveal) >= text.length() and int(game.input_lock) == 0:
				game.advance_dialogue()
		elif current_mode == 4 and int(game.input_lock) == 0:
			var actor: int = int(game.actor)
			var openness: int = int(game.battle.openness)
			var want: String = "Commit turn" if actor < 0 else "GUARD" if actor == 0 or int(game.boss_rounds) >= 2 else "CONNECT"
			if actor == 0 and openness >= 100 and int(game.boss_stage) >= 2:
				want = "CONNECT"
			var choices: Array = game.menu_options
			var chosen: int = -1
			for i: int in range(choices.size()):
				var label: String = str(choices[i].label)
				if label == want or actor == 0 and openness >= 100 and int(game.boss_stage) >= 2 and label.begins_with("RELEASE"):
					chosen = i
					break
			if chosen < 0 and str(game.caption).begins_with("Connect"):
				chosen = 0
			if chosen >= 0:
				game.activate(chosen)
		elif current_mode == 7:
			var current: int = int(game.pattern.column)
			var desired: int = roundi((float(game.pattern.safeColumn) - 24.0) / 52.0)
			Input.action_release("move_left")
			Input.action_release("move_right")
			if hop_release:
				hop_release = false
			elif current != desired:
				Input.action_press("move_left" if desired < current else "move_right")
				hop_release = true
		elif current_mode == 8:
			if result_at < 0:
				result_at = Time.get_ticks_msec()
			if Time.get_ticks_msec() - result_at > 3000:
				break
	Input.action_release("move_left")
	Input.action_release("move_right")
	recording.set_recording_active(false)
	var stream: AudioStreamWAV = recording.get_recording()
	var path: String = output.path_join("chip-native-master-mix.wav")
	var error: Error = stream.save_to_wav(path)
	AudioServer.remove_bus_effect(master, effect_index)
	var report: Dictionary = {"source":"Actual Main scene/menus/rules/AudioServer Master output; fixture Chip entry and automated legitimate commands/hops", "engineArgs":OS.get_cmdline_args(),"captureSettings":{"music":0.65,"effects":0.7,"assist":1.0,"damageAssist":true,"autoTiming":true},"sampleRate":stream.mix_rate,"stereo":stream.stereo,"bytes":stream.data.size(),"outcome":game.battle.get("outcome", "unknown"),"phasesSeen":events,"performedSpeech":false,"audibleApproval":"not established by capture"}
	var report_file: FileAccess = FileAccess.open(output.path_join("chip-native-master-mix.json"), FileAccess.WRITE)
	report_file.store_string(JSON.stringify(report, "\t"))
	var success: bool = error == OK and stream.data.size() > 48000 and game.battle.get("outcome") == "peaceful"
	game.audio.shutdown()
	game.menu_options.clear()
	game.pause_options.clear()
	game.dialogue_choices.clear()
	game.dialogue_callback = Callable()
	game.queue_free()
	await process_frame
	OS.delay_msec(200)
	await process_frame
	print("ACTUAL NATIVE MASTER CAPTURE %s: %s, %s bytes; inspect JSON for phases/outcome, listen before approval." % ["PASS" if success else "FAIL", path, stream.data.size()])
	quit(0 if success else 1)
