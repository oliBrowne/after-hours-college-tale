class_name NativeDiscoveries
extends RefCounted

## Optional scenes never grant combat resources or gate doors/actions.
## Completion flags are committed by Main only when dialogue finishes.
static func scene(id: String, state: Dictionary, speakers: Array[String]) -> Dictionary:
	var f: Dictionary = state.flags
	var lines: Array = []
	var changes: Array[String] = []
	match id:
		"bike":
			if f.get("opening_finished", false): lines = [["Jules", "At least one thing stayed fixed.", "warm"], ["Imani", "Can we put wheels on the mixer?", "neutral"]]
			elif f.get("discovery_bike_seen", false): lines = [["Jules", "The new cable sits neatly in its clip.", "neutral"]]
			else: lines = [["Jules", "Eli left a tag. 'BRAKE TESTED.'", "neutral"], ["Jules", "'TWICE.' He knows me.", "warm"]]
			changes = ["discovery_bike_seen"]
		"eli":
			if not "Eli" in speakers: return {"lines":[["Jules", "Eli's repair tag is tied to the brake. Tested twice.", "neutral"]], "complete":[]}
			if f.get("discovery_bike_seen", false) and not f.get("discovery_eli_acknowledged", false) and "Eli" in speakers:
				lines = [["Jules", "I saw 'tested twice.'", "warm"], ["Eli", "Once for the brake. Once for you.", "neutral"], ["Jules", "Thank you. For both.", "warm"]]
				changes = ["discovery_eli_acknowledged"]
			elif f.get("discovery_eli_acknowledged", false) or f.get("mixer_returned", false): lines = [["Eli", "Brake holding?", "neutral"], ["Jules", "Better than the rest of tonight.", "warm"]]
		"mags":
			if f.get("opening_finished", false): lines = [["Mags", "One box left on my shift. That one's mine, not yours.", "warm"], ["Jules", "Deal. We only took one glove. It insisted.", "warm"]]
			elif state.room == "U02" and f.get("mixer_returned", false): lines = [["Mags", "Mixer back?", "neutral"], ["Jules", "Back with Imani. One thing done.", "neutral"], ["Mags", "One thing at a time. My cart and I approve.", "warm"]]
			elif state.room == "U05" and f.get("cal_joined", false): lines = [["Mags", "Cal has his key. Follow the useful plan.", "warm"], ["Jules", "One thing at a time.", "neutral"]]
		"mara":
			if state.room == "U01" and f.get("mixer_returned", false): lines = [["Mara", "The bag looks lighter.", "warm"], ["Jules", "Mixer's back. Night's still going.", "neutral"], ["Mara", "Leave room for yourself, too.", "warm"]]
		"mags_checklist":
			if not "Mags" in speakers: lines = [["Jules", "Cups back. Terrace latch. Clock out.", "neutral"]]
			else:
				if f.get("opening_finished", false): lines = [["Jules", "Two done.", "neutral"], ["Mags", "Last one's waiting for me.", "warm"], ["Jules", "The coffee has a tail now.", "warm"], ["Mags", "Cat. Keep up.", "neutral"]]
				elif f.get("discovery_mags_checklist_seen", false): lines = [["Jules", "The coffee ring has better posture than I do.", "warm"]]
				else: lines = [["Jules", "Cups back. Terrace latch. Clock out.", "neutral"], ["Mags", "Three boxes. Coffee ring doesn't count.", "neutral"], ["Jules", "You've drawn legs on it.", "warm"], ["Mags", "Long shift.", "warm"]]
				changes = ["discovery_mags_checklist_seen"]
		"stage":
			if not "Imani" in speakers: lines = [["Jules", "A pencil line through the apology. Welcome. Check mic." if f.has("flyer_resolution") else "Welcome. Check mic. Stop apologizing for the mic.", "neutral"]]
			else:
				if f.has("flyer_resolution"): lines = [["Imani", "I've cut the apology.", "neutral"], ["Jules", "For the mic?", "warm"], ["Imani", "Let's start there.", "warm"]]
				elif f.get("discovery_cuesheet_seen", false): lines = [["Jules", "Her handwriting gets smaller near the bottom.", "neutral"]]
				else: lines = [["Jules", "'Welcome. Check mic. Stop apologizing for the mic.'", "neutral"], ["Imani", "It was a very apologetic rehearsal.", "warm"], ["Jules", "The mic sounded okay.", "neutral"], ["Imani", "Good. One of us did.", "warm"]]
				changes = ["discovery_cuesheet_seen"]
		"arcade_button":
			if not ("Imani" in speakers and "Walt" in speakers): lines = [["Jules", "The button's up. The little character gets past the wall now." if f.get("discovery_arcade_seen", false) else "The little character keeps running into the same wall.", "neutral"]]
			else:
				if f.get("discovery_arcade_seen", false) and "Pip" in speakers: lines = [["Pip", "I could be the spare hand.", "warm"], ["Imani", "You have to let go of the buttons sometimes.", "neutral"], ["Pip", "New information.", "concern"]]
				elif f.get("discovery_arcade_seen", false): lines = [["Walt", "Still clicks.", "neutral"], ["Imani", "Evidence preserved.", "warm"]]
				else: lines = [["Imani", "Oh, I know this one. I'm terrible at this one.", "warm"], ["Walt", "The left button is stuck.", "neutral"], ["Imani", "I've been telling people that for two years.", "warm"], ["Jules", "We're backing you up.", "warm"]]
				changes = ["discovery_arcade_seen"]
		"lost_labels":
			if not ("Walt" in speakers and "Imani" in speakers): return {"lines":[["Jules", "A scarf marked 'PLEASE PASS IT ON.' A closed thermos marked 'SOUP?'", "neutral"]], "complete":["discovery_lostlabels_seen"]}
			if f.get("claim_resolution", "") == "peaceful": lines = [["Pip", "The scarf gets a different shelf.", "warm"], ["Walt", "The thermos keeps its lid.", "neutral"]]
			elif f.get("claim_resolution", "") == "forceful": lines = [["Walt", "Mags bundled the loose tickets.", "neutral"], ["Jules", "The soup has its own bundle.", "warm"], ["Imani", "Standard procedure.", "neutral"]]
			elif f.get("discovery_lostlabels_seen", false): lines = [["Jules", "The scarf has instructions. The thermos has a question.", "neutral"]]
			else: lines = [["Jules", "'Please pass it on.' Someone brought this scarf back on purpose.", "neutral"], ["Walt", "The thermos just says 'SOUP?'", "neutral"], ["Imani", "That's either a label or an invitation.", "warm"], ["Jules", "We're leaving the lid on.", "neutral"]]
			changes = ["discovery_lostlabels_seen"]
		"flyer", "pinpal", "claim":
			if not f.has(id + "_resolution"): return {}
			var peaceful: bool = f[id + "_resolution"] == "peaceful"
			if id == "flyer": lines = [["Flyerer", "ONE PAGE. STILL READ." if peaceful else "STAND OUT OF ORDER.", "warm" if peaceful else "neutral"]]
			elif id == "pinpal": lines = [["Pin Pal", "NEXT PLAYER.", "warm"]] if peaceful else [["Walt", "Still unplugged. The ball's on the rack.", "neutral"]]
			else: lines = [["Advisor Bev", "NEXT, SWEETIE. AFTER TEA.", "warm"]] if peaceful else [["Jules", "The ticket mechanism's stopped.", "neutral"]]
		"invitation":
			if f.get("flyer_resolution", "") == "peaceful": lines = [["Imani", "They've put the sign-up sheet away.", "warm"], ["Jules", "Left the page out, though.", "neutral"]]
			elif f.has("flyer_resolution"): lines = [["Jules", "The club page is readable. The hinge is still bent.", "neutral"]]
		"ball_return":
			if f.get("pinpal_resolution", "") == "peaceful": lines = [["Walt", "It's waiting for someone to roll it.", "warm"]]
			elif f.has("pinpal_resolution"): lines = [["Walt", "Still unplugged. The ball's on the rack.", "neutral"]]
		"spool":
			if f.get("claim_resolution", "") == "peaceful": lines = [["Walt", "It printed one ticket and stopped.", "neutral"]]
			elif f.has("claim_resolution"): lines = [["Walt", "The axle's cracked. Mags has the tickets sorted into bundles.", "concern"]]
		"pip":
			if f.get("pip_joined", false): lines = [["Jules", "'Gone with the people. - Pip.'", "neutral"], ["Pip", "I had help with the handwriting.", "warm"]]
	if lines.is_empty(): return {}
	var present_lines: Array = []
	for line: Array in lines:
		if str(line[0]) in speakers: present_lines.append(line)
	if present_lines.is_empty():
		var observations: Dictionary = {"flyer":"One invitation is pinned flat. The signup flap is closed." if f.get("flyer_resolution", "") == "peaceful" else "The stand's bent. Its repair note is still there.", "pinpal":"One ball is waiting in the return cradle." if f.get("pinpal_resolution", "") == "peaceful" else "The return is unplugged. The ball's on the rack.", "claim":"One ticket. The other returns can wait.", "ball_return":"It's waiting for someone to roll it." if f.get("pinpal_resolution", "") == "peaceful" else "The return is unplugged. The ball's on the rack.", "spool":"It printed one ticket and stopped." if f.get("claim_resolution", "") == "peaceful" else "The axle's cracked. The loose tickets are bundled."}
		present_lines = [["Jules", observations.get(id, "The label is still attached."), "neutral"]]
	return {"lines": present_lines, "complete": changes}
