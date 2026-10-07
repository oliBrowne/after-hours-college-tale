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

static func world_step(g: Node) -> bool:
	var f: Dictionary = g.state.flags
	if str(g.state.room) != "U03" or not f.get("mixer_returned", false) or f.get("imani_joined", false): return false
	if g.mode != g.Mode.WORLD or g.transition_ticks > 0 or NativeJakerson.busy(): return false
	scene(g)
	return true

static func scene(g: Node) -> void:
	var f: Dictionary = g.state.flags
	g.strange_ticks = 240
	g.audio.combat("warning")
	g.dialogue([["Booth", "Check, check. Is anyone still here?", "concern"],
		["Jules", "That's Imani's voice. But she's back in the club room.", "concern"],
		["Booth", "Nobody is coming to your show. Stay anyway. ONE MORE MINUTE.", "concern"],
		["Jules", "The posters are shaking. It's... leaving. Out the doors, toward Broadway.", "concern"],
		["Imani", "Jules! My mixer just played that back. I never said that. I would never say that about my own show.", "concern"],
		["Imani", "Something took my sound check and made it say the thing I'm scared of. And now it's out there saying it to everyone.", "concern"],
		["Jules", "I have a bus to catch. On Broadway.", "neutral"],
		["Jules", "It went under the bridge. Walt is down there with his lantern." if f.get("walt_met", false) else "It went under the bridge, toward the underpass.", "concern"],
		["Imani", "Then we're going the same way. You don't owe me your night. Just the walk.", "warm"],
		["Imani", "And I'm not letting you walk toward that thing alone. I can keep our rhythm steady, and patch you up if it gets loud.", "warm"]],
		func() -> void:
			f.imani_joined = true; f.imani_voice_heard = true
			g.refresh_growth(); g.persist(); g.resume_world()
			g.message("Imani joined. She heals and steadies the rhythm in fights."))
