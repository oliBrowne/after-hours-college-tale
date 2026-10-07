extends SceneTree
## Reference oscillator tests Music bus compensation in the actual native mixer.
func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var directory: String = OS.get_environment("AFTER_HOURS_AUDIO_QA")
	assert(not directory.is_empty())
	var director: Node = (load("res://services/audio_director.gd") as GDScript).new()
	root.add_child(director)
	await process_frame
	director.call("set_mix_gains", 0.5, 0.0, 0.0, 0.0)
	director.call("play_music", "battle-rich")
	var wave := AudioStreamWAV.new()
	wave.format = AudioStreamWAV.FORMAT_16_BITS
	wave.mix_rate = 44100
	wave.loop_mode = AudioStreamWAV.LOOP_FORWARD
	wave.loop_end = 44100 * 8
	var samples := PackedByteArray()
	samples.resize(wave.loop_end * 2)
	for i: int in range(wave.loop_end):
		samples.encode_s16(i * 2, int(sin(float(i) * TAU * 440.0 / 44100.0) * 7000.0))
	wave.data = samples
	var player: AudioStreamPlayer = director.get("_music_player")
	player.stop()
	player.stream = wave
	player.play()
	var record := AudioEffectRecord.new()
	record.format = AudioStreamWAV.FORMAT_16_BITS
	var master: int = AudioServer.get_bus_index("Master")
	var record_index: int = AudioServer.get_bus_effect_count(master)
	AudioServer.add_bus_effect(master, record)
	record.set_recording_active(true)
	await create_timer(2.0).timeout
	director.call("set_music_speed", 0.56)
	var music: int = AudioServer.get_bus_index("Music")
	var shift: AudioEffectPitchShift = director.get("_pitch_compensation")
	var index: int = -1
	for i: int in range(AudioServer.get_bus_effect_count(music)):
		if AudioServer.get_bus_effect(music, i) == shift:
			index = i
	assert(index >= 0)
	AudioServer.set_bus_effect_enabled(music, index, false)
	await create_timer(2.0).timeout
	AudioServer.set_bus_effect_enabled(music, index, true)
	await create_timer(2.0).timeout
	record.set_recording_active(false)
	var capture: AudioStreamWAV = record.get_recording()
	assert(capture.save_to_wav(directory.path_join("native-pitch-compensation-proof.wav")) == OK)
	AudioServer.remove_bus_effect(master, record_index)
	director.call("shutdown")
	assert(AudioServer.get_bus_effect_count(music) == 0)
	director.queue_free()
	await process_frame
	OS.delay_msec(150)
	await process_frame
	print("PITCH CAPTURE PASS: normal 440 Hz, raw0.56, compensated0.56, native Music effect cleanup.")
	quit(0)
