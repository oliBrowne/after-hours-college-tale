extends Node
class_name NativeAudioDirector

## One persistent native audio owner. Assets are local; no browser audio context.
## Performed speech is absent. Dialogue uses original nonverbal voice textures.
const ASSET_ROOT: String = "res://assets/audio/"
const MUSIC_CUES: Array[String] = ["arrival", "campus", "umc", "battle", "claim", "claim-boss", "battle-rich", "boss-dark", "last-call", "graduation", "macky", "dawn"]
const MUSIC_METADATA: Dictionary = {
	"last-call":{"bpm":120.0,"beats_per_bar":4,"bars":48},
	"graduation":{"bpm":120.0,"beats_per_bar":4,"bars":64},
	"macky":{"bpm":104.0,"beats_per_bar":4,"bars":16},
	"dawn":{"bpm":104.0,"beats_per_bar":4,"bars":16},
	"arrival": {"bpm":96.0, "beats_per_bar":4, "bars":32},
	"campus": {"bpm":104.0, "beats_per_bar":4, "bars":32},
	"umc": {"bpm":112.0, "beats_per_bar":4, "bars":32},
	"battle": {"bpm":120.0, "beats_per_bar":4, "bars":32},
	"claim": {"bpm":80.0, "beats_per_bar":4, "bars":32},
	"claim-boss": {"bpm":80.0, "beats_per_bar":4, "bars":32},
	"battle-rich": {"bpm":120.0, "beats_per_bar":4, "bars":32},
	"boss-dark": {"bpm":120.0, "beats_per_bar":4, "bars":48},
}
const AMBIENCE_CUES: Array[String] = ["campus-air", "quiet-birds", "umc-room", "hall-clock"]
const VOICED_SPEAKERS: Array[String] = ["jules", "imani", "cal", "mags", "todd", "deion", "chip"]
## Supporting/object voices explicitly reuse local nonverbal sources with a
## distinct pitch/register. These are not unique recordings or performed speech.
const DIALOGUE_REUSE: Dictionary = {
	"jakerson":{"family":"cal","pitch":1.08,"gain":0.8},
	"val":{"family":"mags","pitch":1.08,"gain":0.85},
	"cone committee":{"family":"todd","pitch":1.25,"gain":0.8},
	"chad":{"family":"cal","pitch":1.12,"gain":0.85},
	"mom":{"family":"mags","pitch":0.92,"gain":0.85},
	"nell":{"family":"mags","pitch":1.1,"gain":0.85},
	"dev":{"family":"cal","pitch":1.2,"gain":0.85},
	"errata":{"family":"flyer","pitch":1.2,"gain":0.8,"mechanical":true},
	"autocomplete":{"family":"flyer","pitch":0.62,"gain":0.85,"mechanical":true},
	"loadbearer":{"family":"flyer","pitch":0.78,"gain":0.85,"mechanical":true},
	"eric":{"family":"flyer","pitch":1.0,"gain":0.85},
	"walt": {"family":"cal", "pitch":0.78, "gain":0.85},
	"rook": {"family":"flyer", "pitch":0.85, "gain":0.85, "mechanical":true},
	"encore": {"family":"flyer", "pitch":1.05, "gain":0.8, "mechanical":true},
	"mara": {"family":"mags", "pitch":0.9, "gain":0.9},
	"eli": {"family":"cal", "pitch":1.12, "gain":0.85},
	"booth": {"family":"jules", "pitch":0.86, "gain":0.85},
	"claim": {"family":"flyer", "pitch":0.7, "gain":0.95, "mechanical":true},
	"pinpal": {"family":"todd", "pitch":0.92, "gain":0.9},
	"pip": {"family":"chip", "pitch":1.34, "gain":0.8},
}
const COMBAT_MAP: Dictionary = {
	"swing":"swing-whoosh", "whoosh":"swing-whoosh", "hit":"body-hit", "bodyhit":"body-hit",
	"guard":"guard-metal", "guardmetal":"guard-metal", "shield":"shield-pop", "shieldpop":"shield-pop", "foot":"foot-wood", "stairs":"foot-wood",
	"foot-stone":"foot-stone-rich", "foot-carpet":"foot-carpet-rich", "warning":"ring-warning",
	"whistle":"football-whistle", "footballwhistle":"football-whistle", "stamp":"audit-stamp", "auditstamp":"audit-stamp", "release":"release-warm",
	"enemyhurt":"enemy-hurt", "enemydefeat":"enemy-defeat", "pick":"ui-pick", "ui":"ui-pick", "perfect":"timing-perfect", "timingperfect":"timing-perfect",
	"bird":"bird-chirp", "squirrel":"squirrel-chirp", "rustle":"leaf-rustle",
	"boss-release":"boss-release", "boss-force":"boss-force",
}
const SPEAKERS: Array[String] = ["jules", "imani", "cal", "mags", "flyer"]
const MAX_EFFECTS: int = 8
## Sound-design pass 2026-10-06: ambient one-shots are rate-limited and randomised; the same
## effect never restarts within EFFECT_RETRIGGER_MS (stacked clicks and doubled warnings).
const AMBIENT_ONE_SHOTS: Array[String] = ["bird-chirp", "leaf-rustle", "squirrel-chirp"]
const EFFECT_RETRIGGER_MS: int = 70
const VOICE_BLIP_MS: int = 165
const BLIP_COOLDOWN_MS: int = 75

var _music_player: AudioStreamPlayer
var _ambient_player: AudioStreamPlayer
var _effect_players: Array[AudioStreamPlayer] = []
var _stream_cache: Dictionary = {}
var _blip_variants: Dictionary = {}
var _blip_last_ms: Dictionary = {}
var _music_cue: String = ""
var _music_volume: float = 0.32
var _effects_volume: float = 0.55
var _paused: bool = false
var _enabled: bool = false
var _music_clock_seconds: float = 0.0
var _music_loop_count: int = 0
var _music_last_raw: float = 0.0
var _seek_guard_until_ms: int = 0
var _music_speed: float = 1.0
var _ambience_volume: float = 0.3575
var _voice_volume: float = 0.55
var _resolution_active: bool = false
var _resolution_fade: float = 0.0
var _resolution_tail: float = 0.0
var _resolution_cadence: String = ""
var _resolution_world_cue: String = ""
var _ambient_gain: float = 1.0
var _pitch_compensation: AudioEffectPitchShift
var _ambient_cue: String = ""
var _room_music_active: bool = false
var _room_breath_remaining: float = 0.0
var _music_clock_offset: float = 0.0
var _boss_phase_current: int = -1
var _boss_phase_pending: int = -1
var _boss_phase_bar: float = 0.0
var _music_epoch: int = 0
var _ambient_one_shot_next_ms: int = 0
var _effect_last_ms: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_music_player = AudioStreamPlayer.new()
	_music_player.name = "SceneMusic"
	_music_player.bus = &"Music"
	_music_player.pitch_scale = _music_speed
	add_child(_music_player)
	_ambient_player = AudioStreamPlayer.new()
	_ambient_player.name = "RoomAmbience"
	_ambient_player.bus = &"Ambience"
	add_child(_ambient_player)
	for index: int in range(MAX_EFFECTS):
		var player := AudioStreamPlayer.new()
		player.name = "Effect%d" % index
		player.bus = &"Effects"
		player.set_meta("gain", 1.0)
		player.set_meta("started_ms", 0)
		player.set_meta("speaker", "")
		add_child(player)
		_effect_players.append(player)
	_enabled = true
	var music_bus: int = AudioServer.get_bus_index("Music")
	if music_bus >= 0:
		_pitch_compensation = AudioEffectPitchShift.new()
		_pitch_compensation.fft_size = AudioEffectPitchShift.FFT_SIZE_512
		AudioServer.add_bus_effect(music_bus, _pitch_compensation)
		set_music_speed(_music_speed)
	set_volumes(_music_volume, _effects_volume)


func _process(delta: float) -> void:
	_update_music_clock()
	if _resolution_active and not _paused:
		if _resolution_fade > 0.0:
			_resolution_fade = maxf(0.0, _resolution_fade - delta)
			_music_player.volume_db = _volume_db(_music_volume * _resolution_fade / 0.35)
			if _resolution_fade == 0.0:
				play_music("")
				combat(_resolution_cadence)
				_resolution_tail = 2.65
		elif _resolution_tail > 0.0:
			_resolution_tail = maxf(0.0, _resolution_tail - delta)
			if _resolution_tail == 0.0:
				_resolution_active = false
				var world: String = _resolution_world_cue
				_resolution_world_cue = ""
				if not world.is_empty():
					room_music(world)
	if _enabled and not _paused and _boss_phase_pending >= 0 and NativeSoundtrack.is_battle(_music_cue):
		var song_beat: float = beat_position()
		if song_beat >= _boss_phase_bar:
			var song_bpm: float = float(music_metadata().get("bpm", 120.0))
			var late: float = maxf(0.0, (song_beat - _boss_phase_bar) * 60.0 / song_bpm)
			_seek_music_preserving_clock(float(NativeSoundtrack.phase_starts(_music_cue)[_boss_phase_pending]) + late)
			_boss_phase_current = _boss_phase_pending
			_boss_phase_pending = -1
	if _enabled and not _paused and _boss_phase_pending >= 0 and _music_cue in ["boss-dark","last-call","graduation"]:
		var beat: float = _music_clock_seconds * 2.0
		if beat >= _boss_phase_bar:
			var overshoot: float = maxf(0.0, _music_clock_seconds - _boss_phase_bar / 2.0)
			var target_source: float = float(_boss_phase_pending) * 32.0 + overshoot
			_seek_music_preserving_clock(target_source)
			_boss_phase_current = _boss_phase_pending
			_boss_phase_pending = -1
	if _enabled and not _paused and _music_cue in ["boss-dark","last-call","graduation"] and _boss_phase_current >= 0 and Time.get_ticks_msec() >= _seek_guard_until_ms:
		# Keep each authored section looping until its actual gameplay phase changes.
		var source_elapsed: float = _music_clock_seconds - _music_clock_offset
		var section_end: float = float(_boss_phase_current + 1) * 32.0
		if source_elapsed >= section_end:
			var overshoot: float = fposmod(source_elapsed - section_end, 32.0)
			_seek_music_preserving_clock(float(_boss_phase_current) * 32.0 + overshoot)
	if _paused or not _enabled or not _room_music_active or _music_player.stream == null:
		return
	if _room_breath_remaining > 0.0:
		_room_breath_remaining = maxf(0.0, _room_breath_remaining - delta)
		if _room_breath_remaining == 0.0:
			_music_clock_seconds = 0.0
			_music_loop_count = 0
			_music_last_raw = 0.0
			_music_player.play()
	elif _music_clock_seconds >= _music_player.stream.get_length() * 2.0:
		_music_player.stop()
		_music_clock_seconds = 0.0
		_music_loop_count = 0
		_music_last_raw = 0.0
		_room_breath_remaining = 8.0


func _exit_tree() -> void:
	shutdown()


func music_metadata(cue: String = "") -> Dictionary:
	var key: String = _music_cue if cue.is_empty() else cue
	if NativeSoundtrack.has(key):
		return NativeSoundtrack.metadata(key)
	return (MUSIC_METADATA.get(key, {}) as Dictionary).duplicate(true)


func music_elapsed_seconds() -> float:
	_update_music_clock()
	return _music_clock_seconds


func beat_position() -> float:
	var metadata: Dictionary = music_metadata()
	# Recorded songs carry the time of their first downbeat; generated loops start on one.
	return (music_elapsed_seconds() - float(metadata.get("offset", 0.0))) * float(metadata.get("bpm", 0.0)) / 60.0


func reserve_bar(min_lead_beats: float = 2.0) -> Dictionary:
	var metadata: Dictionary = music_metadata()
	if not _enabled or _music_player.stream == null or metadata.is_empty():
		return {"valid":false}
	var bpm: float = float(metadata.get("bpm", 0.0))
	var beats_per_bar: int = int(metadata.get("beats_per_bar", 4))
	if bpm <= 0.0 or beats_per_bar <= 0:
		return {"valid":false}
	var lead: float = maxf(0.001, min_lead_beats if is_finite(min_lead_beats) else 2.0)
	var target_beat: float = ceil((beat_position() + lead) / float(beats_per_bar)) * float(beats_per_bar)
	return {"valid":true, "cue":_music_cue, "epoch":_music_epoch, "beat":target_beat,
		"music_tick":roundi(target_beat * 3600.0 / bpm), "bpm":bpm, "beats_per_bar":beats_per_bar}


func bar_is_valid(marker: Dictionary) -> bool:
	return bool(marker.get("valid", false)) and _enabled and _music_player.stream != null and str(marker.get("cue", "")) == _music_cue and int(marker.get("epoch", -1)) == _music_epoch


func bar_ready(marker: Dictionary) -> bool:
	return bar_is_valid(marker) and not _paused and beat_position() >= float(marker.beat)


func bar_seconds_remaining(marker: Dictionary) -> float:
	if not bar_is_valid(marker):
		return 0.0
	return maxf(0.0, float(marker.beat) - beat_position()) * 60.0 / float(marker.bpm) / _music_speed


func bar_overshoot_ticks(marker: Dictionary) -> int:
	if not bar_is_valid(marker):
		return 0
	return maxi(0, roundi((beat_position() - float(marker.beat)) * 3600.0 / float(marker.bpm)))


func boss_phase(phase: int) -> void:
	if not _enabled:
		return
	if NativeSoundtrack.is_battle(_music_cue):
		_song_phase(phase)
		return
	if _music_cue not in ["boss-dark","last-call","graduation"]:
		play_music("boss-dark")
	var next_phase: int = clampi(phase, 0, 3 if _music_cue=="graduation" else 2)
	if next_phase == _boss_phase_pending:
		return
	if next_phase == _boss_phase_current:
		_boss_phase_pending = -1
		return
	_boss_phase_pending = next_phase
	# Queue a source-section change to the next four-quarter-note bar.
	_boss_phase_bar = ceil((beat_position() + 0.001) / 4.0) * 4.0


## Recorded fight songs: a phase either jumps to a stronger section of the same song on the
## next bar (the beat clock keeps running) or, where NativeSoundtrack says so, moves to another song.
func _song_phase(phase: int) -> void:
	var next_cue: String = NativeSoundtrack.phase_cue(_music_cue, phase)
	if not next_cue.is_empty():
		play_music(next_cue)
		return
	var starts: Array = NativeSoundtrack.phase_starts(_music_cue)
	if starts.size() < 2:
		return
	var next_phase: int = clampi(phase, 0, starts.size() - 1)
	if next_phase == _boss_phase_pending:
		return
	if next_phase == _boss_phase_current:
		_boss_phase_pending = -1
		return
	_boss_phase_pending = next_phase
	var beats_per_bar: float = float(music_metadata().get("beats_per_bar", 4))
	_boss_phase_bar = ceil((beat_position() + 0.001) / beats_per_bar) * beats_per_bar


func phase_music(phase: int) -> void:
	boss_phase(phase)


func _seek_music_preserving_clock(target_source: float) -> void:
	var held_clock: float = _music_clock_seconds
	var held_epoch: int = _music_epoch
	seek_music(target_source)
	# Source bar phase matches while combat's continuous beat clock stays put.
	_music_clock_offset = held_clock - target_source
	_music_clock_seconds = held_clock
	_music_epoch = held_epoch


func set_music_speed(scale: float) -> void:
	# Transport remains measured in source seconds/beats when assist slows playback.
	_update_music_clock()
	_music_speed = clampf(scale if is_finite(scale) else 1.0, 0.5, 1.5)
	if _enabled:
		_music_player.pitch_scale = _music_speed
		if _pitch_compensation != null:
			_pitch_compensation.pitch_scale = 1.0 / _music_speed
			var bus: int = AudioServer.get_bus_index("Music")
			for index: int in range(AudioServer.get_bus_effect_count(bus)):
				if AudioServer.get_bus_effect(bus, index) == _pitch_compensation:
					AudioServer.set_bus_effect_enabled(bus, index, not is_equal_approx(_music_speed, 1.0))


func shutdown() -> void:
	_resolution_active = false
	_resolution_world_cue = ""
	if _pitch_compensation != null:
		var bus: int = AudioServer.get_bus_index("Music")
		if bus >= 0:
			for index: int in range(AudioServer.get_bus_effect_count(bus) - 1, -1, -1):
				if AudioServer.get_bus_effect(bus, index) == _pitch_compensation:
					AudioServer.remove_bus_effect(bus, index)
		_pitch_compensation = null
	# Call before replacing/freeing the persistent game root, not on room changes.
	if not _enabled:
		return
	_music_player.stop()
	_music_player.stream = null
	_ambient_player.stop()
	_ambient_player.stream = null
	for player: AudioStreamPlayer in _effect_players:
		player.stop()
		player.stream = null
	_stream_cache.clear()
	_blip_last_ms.clear()
	_effect_last_ms.clear()
	_blip_variants.clear()
	_music_cue = ""
	_music_clock_seconds = 0.0
	_music_loop_count = 0
	_music_last_raw = 0.0
	_seek_guard_until_ms = 0
	_music_clock_offset = 0.0
	_boss_phase_current = -1
	_boss_phase_pending = -1
	_music_epoch += 1
	_ambient_cue = ""
	_room_music_active = false
	_room_breath_remaining = 0.0
	_enabled = false


func seek_music(seconds: float) -> void:
	if not _enabled or _music_player.stream == null:
		return
	if not is_finite(seconds):
		return
	var length: float = _music_player.stream.get_length()
	if length <= 0.0:
		return
	var target: float = maxf(0.0, seconds)
	var loop_start: float = _loop_start(length)
	var period: float = length - loop_start
	_music_epoch += 1
	_music_loop_count = maxi(0, int(floor((target - loop_start) / period))) if target >= length else 0
	_music_last_raw = target - float(_music_loop_count) * period
	_music_clock_seconds = target
	_music_clock_offset = 0.0
	_music_player.seek(_music_last_raw)
	# The render thread can still see the previous mix block immediately after seek.
	_seek_guard_until_ms = Time.get_ticks_msec() + int(ceil((AudioServer.get_output_latency() + 0.05) * 1000.0))


func _update_music_clock() -> void:
	if not _enabled or _paused or _music_player.stream == null or not _music_player.playing:
		return
	if Time.get_ticks_msec() < _seek_guard_until_ms:
		return
	var length: float = _music_player.stream.get_length()
	if length <= 0.0:
		return
	var raw: float = _music_player.get_playback_position()
	# Recorded songs loop back to a bar after their intro, not to 0.
	var loop_start: float = _loop_start(length)
	var period: float = length - loop_start
	# A genuine period wrap is distinct from a tiny mixer-position jitter.
	if _music_last_raw > loop_start + period * 0.75 and raw < loop_start + period * 0.25:
		_music_loop_count += 1
	_music_last_raw = raw
	var audible: float = raw + (AudioServer.get_time_since_last_mix() - AudioServer.get_output_latency()) * _music_speed
	var elapsed: float = float(_music_loop_count) * period + audible + _music_clock_offset
	# The hardware estimate may jitter by a sample/block; never move attacks backwards.
	_music_clock_seconds = maxf(_music_clock_seconds, maxf(0.0, elapsed))


func _loop_start(length: float) -> float:
	var stream: AudioStreamOggVorbis = _music_player.stream as AudioStreamOggVorbis
	if stream == null:
		return 0.0
	return clampf(stream.loop_offset, 0.0, maxf(0.0, length - 0.5))


func play_music(cue: String) -> void:
	if not _enabled:
		return
	if not cue.is_empty():
		_resolution_active = false
		_resolution_world_cue = ""
	_room_music_active = false
	_room_breath_remaining = 0.0
	if cue in ["battle", "battle-rich", "boss-dark", "last-call", "graduation", "claim", "claim-boss"] or NativeSoundtrack.is_battle(cue):
		ambient("")
	if cue.is_empty():
		_music_player.stop()
		_music_player.stream = null
		_music_cue = ""
		_music_clock_seconds = 0.0
		_music_loop_count = 0
		_music_last_raw = 0.0
		_seek_guard_until_ms = 0
		_music_clock_offset = 0.0
		_boss_phase_current = -1
		_boss_phase_pending = -1
		_music_epoch += 1
		return
	if cue not in MUSIC_CUES and not NativeSoundtrack.has(cue):
		push_warning("Unknown music cue: %s" % cue)
		return
	# Room revisit and retry retain one playback origin, never another player.
	if cue == _music_cue and _music_player.stream != null:
		if not _music_player.playing and not _paused:
			_music_player.play()
		return
	var stream: AudioStream = _get_stream(cue, "ogg")
	if stream == null:
		return
	if stream is AudioStreamOggVorbis:
		(stream as AudioStreamOggVorbis).loop = true
		if NativeSoundtrack.has(cue):
			(stream as AudioStreamOggVorbis).loop_offset = float(NativeSoundtrack.metadata(cue).get("loop_offset", 0.0))
	_music_player.stop()
	_music_player.stream = stream
	_music_cue = cue
	_music_epoch += 1
	_boss_phase_current = 0 if cue in ["boss-dark","last-call","graduation"] or NativeSoundtrack.phase_starts(cue).size() > 1 else -1
	_boss_phase_pending = -1
	_music_clock_seconds = 0.0
	_music_clock_offset = 0.0
	_music_loop_count = 0
	_music_last_raw = 0.0
	_seek_guard_until_ms = 0
	_music_player.volume_db = _volume_db(_music_volume)
	_music_player.play()
	_music_player.stream_paused = _paused


func room_music(cue: String) -> void:
	# World music never selects a fight loop. The title arrival asset stays intact.
	var song: String = NativeSoundtrack.world_cue(cue)
	var world_cue: String = song if NativeSoundtrack.has(song) else cue if cue in ["arrival", "campus", "umc", "macky", "dawn"] else NativeSoundtrack.world_cue("umc")
	# Immediate Continue keeps the cadence audible before restoring room score.
	if _resolution_active:
		_resolution_world_cue = world_cue
		return
	_ambient_gain = 1.0
	set_ambience_volume(_ambience_volume)
	set_music_speed(1.0)
	play_music(world_cue)
	_room_music_active = true


func ambient(cue: String) -> void:
	if not _enabled:
		return
	if cue.is_empty():
		_ambient_player.stop()
		_ambient_player.stream = null
		_ambient_cue = ""
		return
	var key: String = {"outside":"campus-air", "birds":"quiet-birds", "umc":"umc-room", "hall":"hall-clock"}.get(cue, cue)
	if key not in AMBIENCE_CUES:
		return
	if key == _ambient_cue and _ambient_player.stream != null:
		return
	var stream: AudioStream = _get_stream(key, "ogg")
	if stream == null:
		return
	if stream is AudioStreamOggVorbis:
		(stream as AudioStreamOggVorbis).loop = true
	_ambient_player.stop()
	_ambient_player.stream = stream
	_ambient_player.volume_db = _volume_db(_ambience_volume * _ambient_gain)
	_ambient_cue = key
	_ambient_player.play()
	_ambient_player.stream_paused = _paused


func set_ambience_volume(volume: float) -> void:
	_ambience_volume = clampf(volume if is_finite(volume) else 0.3575, 0.0, 1.0)
	if _enabled:
		_ambient_player.volume_db = _volume_db(_ambience_volume * _ambient_gain)


func set_voice_volume(volume: float) -> void:
	_voice_volume = clampf(volume if is_finite(volume) else 0.55, 0.0, 1.0)
	if not _enabled:
		return
	for player: AudioStreamPlayer in _effect_players:
		if not str(player.get_meta("speaker", "")).is_empty():
			player.volume_db = _volume_db(_voice_volume * float(player.get_meta("gain", 1.0)))
			if _voice_volume == 0.0:
				player.stop()


func resolve_battle(peaceful: bool) -> void:
	if not _enabled:
		return
	# Freeze section scheduling; fade the battle score before its resolved cadence.
	_boss_phase_pending = -1
	_boss_phase_current = -1
	_room_music_active = false
	_resolution_active = true
	_resolution_fade = 0.35
	_resolution_tail = 0.0
	_resolution_world_cue = ""
	_resolution_cadence = "boss-release" if peaceful else "boss-force"
	_ambient_gain = 0.35
	ambient("hall-clock")
	set_ambience_volume(_ambience_volume)


func combat(cue: String) -> void:
	var key: String = cue.strip_edges().to_lower().replace("_", "-")
	var asset: String = str(COMBAT_MAP.get(key, key))
	if asset in AMBIENT_ONE_SHOTS:
		# Birds and leaves: irregular and rare, never on a fixed clock.
		var now: int = Time.get_ticks_msec()
		if now < _ambient_one_shot_next_ms:
			return
		_ambient_one_shot_next_ms = now + randi_range(11000, 26000)
		_play_effect(asset, 0.8, "", randf_range(0.9, 1.1))
		return
	if asset.begins_with("foot"):
		# Footsteps: quieter than everything else, and each one slightly different.
		_play_effect(asset, 0.7, "", randf_range(0.9, 1.08))
		return
	effect(asset)


func voiced_blip(speaker: String, mood: String = "neutral") -> void:
	if _paused or not _enabled or _voice_volume <= 0.0:
		return
	var key: String = speaker.strip_edges().to_lower()
	key = str({"jules navarro":"jules", "imani bell":"imani", "cal rhee":"cal", "mags venn":"mags", "todd saliman":"todd", "deion sanders":"deion", "coach":"deion", "coach deion":"deion", "chip the buffalo":"chip", "pin pal":"pinpal", "booth voice":"booth", "claim / lost property":"claim"}.get(key, key))
	if key not in VOICED_SPEAKERS and not DIALOGUE_REUSE.has(key):
		blip(speaker)
		return
	var profile: Dictionary = DIALOGUE_REUSE.get(key, {"family":key, "pitch":1.0, "gain":1.0})
	var family: String = str(profile.family)
	var mechanical: bool = bool(profile.get("mechanical", false))
	var emotion: String = mood.strip_edges().to_lower()
	emotion = str({"happy":"warm", "relieved":"warm", "hurt":"concern", "angry":"concern", "fear":"concern"}.get(emotion, emotion))
	if emotion not in ["neutral", "warm", "concern"]:
		emotion = "neutral"
	var now: int = Time.get_ticks_msec()
	var cooldown_key: String = key + ":vocal"
	if now - int(_blip_last_ms.get(cooldown_key, -VOICE_BLIP_MS)) < VOICE_BLIP_MS:
		return
	_blip_last_ms[cooldown_key] = now
	var variant: int = int(_blip_variants.get(cooldown_key, 0))
	_blip_variants[cooldown_key] = (variant + 1) % (4 if mechanical else 3)
	var asset: String = "vocal-%s-%s-%d" % [family, emotion, variant + 1]
	if mechanical:
		asset = "blip-%s%s" % [family, "" if variant == 0 else "-%d" % (variant + 1)]
	# A little pitch drift so a long line doesn't sound like one sample on repeat.
	_play_effect(asset, float(profile.gain), key, float(profile.pitch) * randf_range(0.97, 1.03))


func effect(cue: String, gain: float = 1.0) -> void:
	_play_effect(cue, gain, "")


func blip(speaker: String) -> void:
	if _paused or not _enabled or _voice_volume <= 0.0:
		return
	var key: String = speaker.strip_edges().to_lower()
	if key == "flyerer" or key == "foe.flyer":
		key = "flyer"
	if key not in SPEAKERS:
		return
	var now: int = Time.get_ticks_msec()
	var previous: int = int(_blip_last_ms.get(key, -BLIP_COOLDOWN_MS))
	if now - previous < BLIP_COOLDOWN_MS:
		return
	_blip_last_ms[key] = now
	var variant: int = int(_blip_variants.get(key, 0))
	_blip_variants[key] = (variant + 1) % 4
	var suffix: String = "" if variant == 0 else "-%d" % (variant + 1)
	_play_effect("blip-%s%s" % [key, suffix], 0.65, key)


func set_volumes(music: float, effects: float) -> void:
	_music_volume = clampf(music if is_finite(music) else 0.32, 0.0, 1.0)
	_effects_volume = clampf(effects if is_finite(effects) else 0.55, 0.0, 1.0)
	if not _enabled:
		return
	_music_player.volume_db = _volume_db(_music_volume)
	_ambient_player.volume_db = _volume_db(_ambience_volume * _ambient_gain)
	for player: AudioStreamPlayer in _effect_players:
		var level: float = _voice_volume if not str(player.get_meta("speaker", "")).is_empty() else _effects_volume
		player.volume_db = _volume_db(level * float(player.get_meta("gain", 1.0)))
		if level <= 0.0:
			player.stop()


func set_mix_gains(music: float, effects: float, voices: float, ambience: float) -> void:
	set_voice_volume(voices)
	set_ambience_volume(ambience)
	set_volumes(music, effects)


func set_paused(paused: bool) -> void:
	# Capture the audible position before suspension; querying it stays frozen.
	if paused and not _paused:
		_update_music_clock()
	_paused = paused
	if not _enabled:
		return
	_music_player.stream_paused = paused
	_ambient_player.stream_paused = paused
	# Short UI/voice effects are stopped, so no stale line bursts out on resume.
	for player: AudioStreamPlayer in _effect_players:
		var cadence: bool = player.stream != null and player.stream.resource_path.get_file().begins_with("boss-")
		if cadence and _resolution_active:
			player.stream_paused = paused
		elif paused:
			player.stop()


func _play_effect(cue: String, gain: float, speaker: String, pitch: float = 1.0) -> void:
	var level: float = _voice_volume if not speaker.is_empty() else _effects_volume
	if not _enabled or _paused or level <= 0.0 or gain <= 0.0:
		return
	# Only asset IDs: do not interpret a cue as a path or executable content.
	if cue.is_empty() or cue.contains("/") or cue.contains("\\") or cue.contains(".."):
		return
	var stream: AudioStream = _get_stream(cue, "wav")
	if stream == null:
		return
	if speaker.is_empty():
		var now: int = Time.get_ticks_msec()
		if now - int(_effect_last_ms.get(cue, -EFFECT_RETRIGGER_MS)) < EFFECT_RETRIGGER_MS:
			return
		_effect_last_ms[cue] = now
	var selected: AudioStreamPlayer = null
	# At most one blip per speaker. Never stack repeated text sounds on skipping.
	if not speaker.is_empty():
		for player: AudioStreamPlayer in _effect_players:
			if String(player.get_meta("speaker", "")) == speaker:
				player.stop()
				selected = player
				break
	if selected == null:
		for player: AudioStreamPlayer in _effect_players:
			if not player.playing:
				selected = player
				break
	if selected == null:
		selected = _effect_players[0]
		for player: AudioStreamPlayer in _effect_players:
			if int(player.get_meta("started_ms", 0)) < int(selected.get_meta("started_ms", 0)):
				selected = player
	selected.stop()
	selected.stream_paused = false
	selected.stream = stream
	# Pool reuse must never carry an object's shifted voice pitch into combat SFX.
	selected.pitch_scale = clampf(pitch if is_finite(pitch) else 1.0, 0.5, 2.0)
	selected.bus = &"Voices" if not speaker.is_empty() else &"Effects"
	selected.set_meta("gain", clampf(gain, 0.0, 2.0))
	selected.set_meta("speaker", speaker)
	selected.set_meta("started_ms", Time.get_ticks_msec())
	selected.volume_db = _volume_db(level * clampf(gain, 0.0, 2.0))
	selected.play()


func _get_stream(cue: String, extension: String) -> AudioStream:
	var asset_path: String = "%s%s.%s" % [ASSET_ROOT, cue, extension]
	if _stream_cache.has(asset_path):
		return _stream_cache[asset_path] as AudioStream
	if not ResourceLoader.exists(asset_path):
		push_warning("Missing audio asset: %s" % asset_path)
		return null
	var stream: AudioStream = load(asset_path) as AudioStream
	if stream == null:
		push_warning("Cannot decode audio asset: %s" % asset_path)
		return null
	_stream_cache[asset_path] = stream
	return stream


func _volume_db(linear: float) -> float:
	return -80.0 if linear <= 0.0 else linear_to_db(linear)

