extends SceneTree
## Soundtrack checks: every song loops on a bar, story moments pick the right song, and a
## recorded fight song keeps the beat clock steady through phase jumps and loop wraps.
var checks: int = 0
var failures: int = 0
var director: Node

func _initialize() -> void:
	call_deferred("_run")

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _wait(seconds: float) -> void:
	await create_timer(seconds).timeout

func _run() -> void:
	_test_files()
	_test_choices()
	director = NativeAudioDirector.new()
	root.add_child(director)
	await process_frame
	await _test_world()
	await _test_fight()
	await _test_switch()
	await _test_sfx()
	director.call("shutdown")
	print("Soundtrack: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _test_files() -> void:
	for cue: String in NativeSoundtrack.CUES:
		var meta: Dictionary = NativeSoundtrack.metadata(cue)
		var stream: AudioStreamOggVorbis = load("res://assets/audio/%s.ogg" % cue) as AudioStreamOggVorbis
		_check(stream != null, cue + " loads")
		if stream == null:
			continue
		var bar: float = 4.0 * 60.0 / float(meta.bpm)
		var length: float = stream.get_length()
		var loop_bars: float = (length - float(meta.loop_offset)) / bar
		_check(float(meta.loop_offset) < length - 20.0, cue + " loops over at least 20 seconds")
		_check(absf(loop_bars - roundf(loop_bars)) < 0.01, cue + " loop is a whole number of bars (%.3f)" % loop_bars)
		_check(absf(fposmod(float(meta.loop_offset) - float(meta.offset) + bar * 0.5, bar) - bar * 0.5) < 0.002, cue + " loop starts on a downbeat")
		for start: float in NativeSoundtrack.phase_starts(cue):
			_check(start < length and absf(fposmod(start - float(meta.offset) + bar * 0.5, bar) - bar * 0.5) < 0.002, cue + " phase start %.2f sits on a bar" % start)
		if str(meta.kind) == "battle" and cue != "song-encore-showdown":
			_check(absf(float(meta.bpm) - 120.0) < 0.1, cue + " fits the 120 BPM attack grid")

func _test_choices() -> void:
	_check(NativeSoundtrack.world_cue("arrival") == "song-theme-main", "Title and arrival use the main theme")
	_check(NativeSoundtrack.room_cue("U02", "campus", {}) == "campus" and NativeSoundtrack.world_cue("campus") == "song-theme-quiet", "Outdoor rooms use the quiet take")
	_check(NativeSoundtrack.world_cue(NativeSoundtrack.room_cue("U03", "umc", {})) == "song-night-bus", "Chapter one interiors use Track 2")
	_check(NativeSoundtrack.room_cue("N03", "umc", {}) == "song-night-bus-late", "Later interiors use Track 2's other take")
	_check(NativeSoundtrack.room_cue("U07", "claim", {}) == "claim", "Lost property keeps its own music")
	_check(NativeSoundtrack.world_cue(NativeSoundtrack.room_cue("M02", "macky", {})) == "song-last-call", "Macky approach uses The Last Call")
	_check(NativeSoundtrack.room_cue("U01", "arrival", {"aftermath_pending":"walt"}) == "song-walt-company", "Walt joining plays his quiet theme")
	_check(NativeSoundtrack.room_cue("M06", "macky", {"aftermath_pending":"val"}) == "song-val-resolution", "After VAL plays the resolution")
	_check(NativeSoundtrack.world_cue(NativeSoundtrack.room_cue("M07", "macky", {"dawn_started":true})) == "song-theme-dawn", "Dawn plays the soft reprise")
	_check(NativeSoundtrack.battle_cue("walt", "boss-dark") == "song-walt-lantern" and NativeSoundtrack.battle_cue("encore", "boss-dark") == "song-encore-showdown" and NativeSoundtrack.battle_cue("val", "graduation") == "song-val-finale", "Boss songs")
	_check(NativeSoundtrack.battle_cue("chip", "boss-dark") == "boss-dark" and NativeSoundtrack.battle_cue("rook", "last-call") == "last-call" and NativeSoundtrack.battle_cue("", "battle-rich") == "battle-rich", "Other fights keep their music")

func _test_world() -> void:
	director.call("room_music", "arrival")
	_check(str(director.get("_music_cue")) == "song-theme-main", "room_music swaps arrival for the main theme")
	var player: AudioStreamPlayer = director.get("_music_player")
	_check(is_equal_approx((player.stream as AudioStreamOggVorbis).loop_offset, float(NativeSoundtrack.metadata("song-theme-main").loop_offset)), "Loop point applied to the stream")
	director.call("room_music", "umc")
	_check(str(director.get("_music_cue")) == "song-night-bus", "room_music swaps umc for Track 2")
	director.call("room_music", "song-walt-company")
	_check(str(director.get("_music_cue")) == "song-walt-company", "room_music accepts a song cue directly")
	await _wait(0.2)

func _test_fight() -> void:
	director.call("play_music", "song-walt-lantern")
	var meta: Dictionary = director.call("music_metadata")
	_check(is_equal_approx(float(meta.bpm), float(NativeSoundtrack.CUES["song-walt-lantern"].bpm)), "Fight song metadata reaches the director")
	_check(int(director.get("_boss_phase_current")) == 0, "Fight song starts in phase 0")
	await _wait(1.0)
	var b0: float = director.call("beat_position")
	_check(b0 > 0.5, "Beat clock runs (%.2f)" % b0)
	var marker: Dictionary = director.call("reserve_bar", 2.0)
	_check(bool(marker.valid) and int(marker.beat) % 4 == 0, "Bars can be reserved on the song")
	director.call("boss_phase", 1)
	_check(int(director.get("_boss_phase_pending")) == 1, "Phase 1 queued for the next bar")
	await _wait(2.6)
	_check(int(director.get("_boss_phase_current")) == 1, "Phase 1 jumped on the bar")
	var player: AudioStreamPlayer = director.get("_music_player")
	var start: float = float(NativeSoundtrack.phase_starts("song-walt-lantern")[1])
	_check(player.get_playback_position() >= start and player.get_playback_position() < start + 3.0, "Playback moved to the phase 1 section (%.2f)" % player.get_playback_position())
	_check(bool(director.call("bar_is_valid", marker)), "Phase jump keeps the reserved bar valid")
	var b1: float = director.call("beat_position")
	_check(b1 > b0 + 4.0, "Beat clock kept counting through the jump")
	# Loop wrap: run up to the end of the file and across the seam.
	var length: float = player.stream.get_length()
	director.call("seek_music", length - 1.0)
	await _wait(0.3)
	var before: float = director.call("beat_position")
	await _wait(1.6)
	var after: float = director.call("beat_position")
	var wrapped: float = player.get_playback_position()
	var lo: float = float(NativeSoundtrack.metadata("song-walt-lantern").loop_offset)
	_check(wrapped >= lo and wrapped < lo + 2.0, "Song wrapped to its loop point (%.2f)" % wrapped)
	_check(absf((after - before) - 1.6 * 2.0) < 0.6, "Beat clock steady across the loop seam (%.2f beats in 1.6 s)" % (after - before))

func _test_switch() -> void:
	director.call("play_music", "song-val-finale")
	director.call("boss_phase", 2)
	_check(int(director.get("_boss_phase_pending")) == 2, "VAL phase 2 queues a section jump")
	director.call("boss_phase", 3)
	_check(str(director.get("_music_cue")) == "song-val-resolution", "VAL's last phase moves to the resolution song")
	director.call("boss_phase", 3)
	_check(str(director.get("_music_cue")) == "song-val-resolution", "Repeating the last phase keeps the song")
	director.call("play_music", "boss-dark")
	director.call("boss_phase", 1)
	_check(int(director.get("_boss_phase_pending")) == 1 and str(director.get("_music_cue")) == "boss-dark", "Old boss music still uses its sections")
	await _wait(0.1)

func _test_sfx() -> void:
	# Sound-design pass: constant sounds are quiet, bright clicks are tamed, repeats are limited.
	for name: String in ["foot-wood", "foot-stone-rich", "foot-carpet-rich", "foot-grass"]:
		_check(_peak_db(name) <= -24.5, name + " footstep is quiet (%.1f dBFS)" % _peak_db(name))
	for name: String in ["body-hit", "swing-whoosh", "shield-pop", "guard-metal", "ring-warning"]:
		_check(_peak_db(name) <= -15.5, name + " no longer clips the mix (%.1f dBFS)" % _peak_db(name))
	_check(_peak_db("vocal-imani-neutral-1") <= -16.5, "Dialogue voices sit under the music")
	var players: Array = director.get("_effect_players")
	director.call("combat", "bird_chirp")
	director.call("combat", "bird_chirp")
	director.call("combat", "leaf_rustle")
	var ambient_playing: int = 0
	for player: AudioStreamPlayer in players:
		if player.playing and player.stream != null and player.stream.resource_path.get_file().begins_with("bird") or player.playing and player.stream != null and player.stream.resource_path.get_file().begins_with("leaf"):
			ambient_playing += 1
	_check(ambient_playing == 1, "Birds and leaves cannot repeat back to back (%d playing)" % ambient_playing)
	director.call("effect", "ring-warning")
	director.call("effect", "ring-warning")
	var warnings: int = 0
	for player: AudioStreamPlayer in players:
		if player.playing and player.stream != null and player.stream.resource_path.get_file() == "ring-warning.wav":
			warnings += 1
	_check(warnings == 1, "A warning fired twice in one frame plays once")
	await _wait(0.1)

func _peak_db(name: String) -> float:
	var f: FileAccess = FileAccess.open("res://assets/audio/%s.wav" % name, FileAccess.READ)
	if f == null:
		return 0.0
	var bytes: PackedByteArray = f.get_buffer(f.get_length())
	var peak: int = 1
	for i: int in range(44, bytes.size() - 1, 2):
		peak = maxi(peak, absi(bytes.decode_s16(i)))
	return 20.0 * log(float(peak) / 32768.0) / log(10.0)
