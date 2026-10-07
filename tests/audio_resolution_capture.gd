extends SceneTree
## Native API / Master mixer evidence. Not an actual Main route or human audition.
var director: Node
var output: String

func _initialize() -> void:
	call_deferred("_run")

func _wait(seconds: float) -> void:
	await create_timer(seconds).timeout

func _capture(name: String, immediate: bool) -> void:
	var record := AudioEffectRecord.new()
	record.format = AudioStreamWAV.FORMAT_16_BITS
	var master: int = AudioServer.get_bus_index("Master")
	var index: int = AudioServer.get_bus_effect_count(master)
	AudioServer.add_bus_effect(master, record)
	record.set_recording_active(true)
	director.call("set_mix_gains", 0.6, 0.7, 0.5, 0.325)
	director.call("play_music", "boss-dark")
	director.call("seek_music", 65.0)
	await _wait(1.0)
	director.call("resolve_battle", not immediate)
	if immediate:
		director.call("room_music", "umc")
		director.call("ambient", "umc")
	await _wait(0.5)
	assert(str(director.get("_music_cue")) == "")
	assert(not (director.get("_music_player") as AudioStreamPlayer).playing)
	await _wait(1.0)
	director.call("set_paused", true)
	var tail: float = float(director.get("_resolution_tail"))
	await _wait(0.25)
	assert(float(director.get("_resolution_tail")) == tail)
	director.call("set_paused", false)
	await _wait(2.0 if immediate else 8.5)
	assert(not bool(director.get("_resolution_active")))
	if not immediate:
		assert(str(director.get("_music_cue")) == "")
		director.call("room_music", "umc")
		director.call("ambient", "umc")
	assert(str(director.get("_music_cue")) == "umc")
	await _wait(1.0)
	record.set_recording_active(false)
	var wav: AudioStreamWAV = record.get_recording()
	assert(wav != null and wav.data.size() > 48000)
	assert(wav.save_to_wav(output.path_join(name + ".wav")) == OK)
	AudioServer.remove_bus_effect(master, index)
	print("CAPTURE " + name + " bytes=" + str(wav.data.size()))

func _run() -> void:
	output = OS.get_environment("AFTER_HOURS_AUDIO_QA")
	assert(not output.is_empty())
	DirAccess.make_dir_recursive_absolute(output)
	director = (load("res://services/audio_director.gd") as GDScript).new()
	root.add_child(director)
	await process_frame
	# Preference compatibility: optional new gains reject malformed present fields.
	var old: Dictionary = NativeState.preferences()
	old.erase("voices")
	old.erase("ambience")
	assert(NativeSaveService.validate_settings(old))
	old.voices = -0.1
	assert(not NativeSaveService.validate_settings(old))
	director.call("set_mix_gains", 0.0, 0.0, 0.5, 0.325)
	director.call("voiced_blip", "Jules", "concern")
	var heard: bool = false
	for player: AudioStreamPlayer in director.get("_effect_players"):
		if player.playing and player.bus == &"Voices":
			heard = player.volume_db > -80.0
	assert(heard)
	director.call("ambient", "umc")
	assert((director.get("_ambient_player") as AudioStreamPlayer).volume_db > -80.0)
	director.call("set_music_speed", 0.56)
	var shift: AudioEffectPitchShift = director.get("_pitch_compensation")
	assert(shift != null and absf(shift.pitch_scale * 0.56 - 1.0) < 0.001)
	director.call("set_music_speed", 1.0)
	await _capture("result-hold-10s-native-api", false)
	await _capture("result-immediate-continue-native-api", true)
	director.call("shutdown")
	director.queue_free()
	await process_frame
	OS.delay_msec(150)
	await process_frame
	print("RESOLUTION PASS: stopped boss before cadence, quiet hold, queued immediate Continue, pause, independent gains, legacy validation, reciprocal native pitch effect.")
	quit(0)
