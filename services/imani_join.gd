class_name NativeImaniJoin
extends RefCounted
## Imani joins later, inside the UMC: returning the mixer no longer recruits her.
## She stays for sound check; when Jules heads back through the atrium, the voice
## booth plays Imani's own voice saying something she never said, and it escapes
## out toward Broadway. She runs out of the club room after it and joins.
## Flags: mixer_returned, jules_response, imani_joined (as before), imani_voice_heard.

static func complete_mixer(g: Node, response: String) -> void:
	g.state.flags.mixer_returned = true
	g.state.flags.jules_response = response
	g.persist()
	var lines: Array = [["Imani", "One sound check. I can work with a small promise.", "warm"],
		["Imani", "Check, check. One more minute of your time, Boulder.", "warm"],
		["Jules", "It sounds good. Really.", "warm"],
		["Imani", "It sounds like my voice is shaking. Thank you. Go catch your bus. Seriously.", "warm"]] if response == "candid" else [
		["Imani", "Eight minutes. Got it. Thank you for bringing it all the way here.", "warm"],
		["Jules", "Good luck tonight.", "warm"],
		["Imani", "Go catch your bus. I'll be fine. Probably.", "concern"]]
	g.dialogue(lines, g.resume_world)

## Imani in the club room after the mixer is back, before the atrium.
static func talk(g: Node) -> bool:
	if not g.state.flags.get("mixer_returned", false) or g.state.flags.get("imani_joined", false): return false
	g.dialogue([["Imani", "Bus! Go! I have forty cables and one nervous song to untangle.", "warm"]], g.resume_world)
	return true

## The booth scene, played by NativeRoomScenes the first time Jules is back in the atrium with
## the mixer returned. It repeats until Imani has joined, so leaving mid-scene can't lose her.
## The booth speaks in Imani's voice, the voice escapes toward Broadway, and Imani runs out of
## the club room after it before she says a word.
static func steps() -> Array:
	return [["call", func(g: Node) -> void:
			g.strange_ticks = 240
			g.audio.combat("warning")],
		["jules", Vector2(382, 252)],
		["say", [["Booth", "Check, check. Is anyone still here?", "concern"],
			["Jules", "That's Imani's voice. But she's back in the club room.", "concern"],
			["Booth", "Nobody is coming to your show. Stay anyway. ONE MORE MINUTE.", "concern"],
			["Jules", "The posters are shaking. It's... leaving. Out the doors, toward Broadway.", "concern"]]],
		["spawn", "imani", "imani", Vector2(90, 205)],
		["walk", [["imani", "jules", NativeRoomScenes.RUN]]], ["face", "imani", "jules"], ["jules", "imani"],
		["say", [["Imani", "Jules! My mixer just played that back. I never said that. I would never say that about my own show.", "concern"],
			["Imani", "Something took my sound check and made it say the thing I'm scared of. And now it's out there saying it to everyone.", "concern"],
			["Jules", "I have a bus to catch. On Broadway.", "neutral"],
			["Jules", "It went under the bridge. Walt is down there with his lantern.", "concern", "walt_met"],
			["Jules", "It went under the bridge, toward the underpass.", "concern", "!walt_met"],
			["Imani", "Then we're going the same way. You don't owe me your night. Just the walk.", "warm"],
			["Imani", "And I'm not letting you walk toward that thing alone. I can keep our rhythm steady, and patch you up if it gets loud.", "warm"]]],
		["call", joined]]

static func joined(g: Node) -> void:
	var f: Dictionary = g.state.flags
	f.imani_joined = true; f.imani_voice_heard = true
	# Her party sprite takes over from the scene's, right where she is standing.
	var standing: Variant = NativeRoomScenes.run.actors.get("imani")
	if standing != null and is_instance_valid(standing) and not g.followers.is_empty():
		g.followers[0].position = Vector2(standing.get_meta("base", standing.position))
	g.refresh_growth(); g.persist()
	g.message("Imani joined. She heals and steadies the rhythm in fights.")
