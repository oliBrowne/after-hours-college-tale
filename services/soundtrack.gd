class_name NativeSoundtrack
extends RefCounted

## oliver's Suno recordings as the game's soundtrack. This file only decides which song plays
## where; NativeAudioDirector still owns playback. Set ENABLED to false to hear the old score.
## Song files are assets/audio/<cue>.ogg, cut to loop on a bar (loop_offset) and
## normalised (world about -28 LUFS, fights -25, VAL -23). Beat grids are measured from the
## recordings: offset is the first downbeat in seconds, so fight attacks still land on bars.
const ENABLED: bool = true

const CUES: Dictionary = {
	"song-theme-main": {"kind":"world", "bpm":93.137, "beats_per_bar":4, "offset":0.4515, "loop_offset":33.9504},
	"song-theme-quiet": {"kind":"world", "bpm":92.251, "beats_per_bar":4, "offset":2.4453, "loop_offset":10.2501},
	"song-theme-dawn": {"kind":"world", "bpm":91.931, "beats_per_bar":4, "offset":0.7637, "loop_offset":26.8701},
	"song-night-bus": {"kind":"world", "bpm":83.952, "beats_per_bar":4, "offset":0.3603, "loop_offset":8.9366},
	"song-night-bus-late": {"kind":"world", "bpm":109.991, "beats_per_bar":4, "offset":0.3757, "loop_offset":15.6497},
	"song-walt-lantern": {"kind":"battle", "bpm":120.015, "beats_per_bar":4, "offset":0.5692, "loop_offset":24.5662, "phase_starts":[0.5692, 14.5675, 24.5662]},
	"song-walt-company": {"kind":"world", "bpm":104.583, "beats_per_bar":4, "offset":1.8525, "loop_offset":27.0955},
	"song-encore-showdown": {"kind":"battle", "bpm":143.998, "beats_per_bar":4, "offset":1.5663, "loop_offset":13.2331, "phase_starts":[1.5663, 23.2333, 44.9002]},
	"song-last-call": {"kind":"world", "bpm":110.471, "beats_per_bar":4, "offset":1.2115, "loop_offset":7.729},
	"song-val-finale": {"kind":"battle", "bpm":120.044, "beats_per_bar":4, "offset":1.4953, "loop_offset":51.4771, "phase_starts":[1.4953, 15.4902, 75.4683]},
	"song-val-resolution": {"kind":"battle", "bpm":119.938, "beats_per_bar":4, "offset":0.2955, "loop_offset":100.3472},
}

## Old room cue -> song. Rooms keep their rooms.json cue; the swap happens here.
const WORLD: Dictionary = {
	"arrival": "song-theme-main",       # title screen and Broadway arrival: One More Minute (main theme)
	"campus": "song-theme-quiet",       # outdoor exploration: One More Minute, the quiet take
	"umc": "song-night-bus",            # indoor rooms, chapter one: Track 2 ("Last Bus Around the Corner")
	"macky": "song-last-call",          # Macky, the approach to VAL: The Last Call
	"dawn": "song-theme-dawn",          # after VAL, the morning: One More Minute, soft reprise
}
## Fights with their own song. Every other fight keeps its current music.
const BOSSES: Dictionary = {
	"walt": "song-walt-lantern",
	"encore": "song-encore-showdown",
	"val": "song-val-finale",
}
## A fight phase that moves to a different song instead of a stronger section of the same one.
const PHASE_SONGS: Dictionary = {
	"song-val-finale": {3: "song-val-resolution"},  # VAL's last, reconciling phase
}


static func has(cue: String) -> bool:
	return ENABLED and CUES.has(cue)


static func metadata(cue: String) -> Dictionary:
	return (CUES.get(cue, {}) as Dictionary).duplicate(true) if has(cue) else {}


static func is_battle(cue: String) -> bool:
	return has(cue) and str(CUES[cue].kind) == "battle"


static func phase_starts(cue: String) -> Array:
	return (metadata(cue).get("phase_starts", []) as Array)


static func phase_cue(cue: String, phase: int) -> String:
	if not has(cue):
		return ""
	return str((PHASE_SONGS.get(cue, {}) as Dictionary).get(phase, ""))


## Song for an old world cue; unknown or disabled cues pass through unchanged.
static func world_cue(cue: String) -> String:
	if not ENABLED:
		return cue
	return str(WORLD.get(cue, cue))


## Room music: the room's own cue, with story moments layered on top.
static func room_cue(room_id: String, cue: String, flags: Dictionary) -> String:
	if flags.get("dawn_started", false):
		return "dawn"
	if not ENABLED:
		return cue
	var pending: String = str(flags.get("aftermath_pending", ""))
	if pending == "walt":
		return "song-walt-company"      # Walt joins: his theme, quieter and without the drums
	if pending == "val":
		return "song-val-resolution"    # straight after VAL: A Future With Room for You, second take
	if cue == "umc" and room_id.substr(0, 1) in ["N", "E", "O"]:
		return "song-night-bus-late"    # indoor rooms from chapter two on: Track 2, the other take
	return cue


static func battle_cue(boss: String, fallback: String) -> String:
	return str(BOSSES[boss]) if ENABLED and BOSSES.has(boss) else fallback
