class_name NativeGuide
extends RefCounted
## Where to go next: each objective line names the room and object it means, and the
## marker (scenes/guide_marker.gd) points at that object, or at the door to take
## toward it, found through the door graph. An empty room means "search every room".
const TARGETS: Dictionary = {
	"Return Imani's mixer / club room": ["U04", "imani"],
	"Head out through the atrium / the last bus": ["U03", "booth"],
	"Follow the escaped voice / Walt under the bridge": ["U08", "walt"],
	"Read one living invitation / club room": ["U04", "flyer"],
	"Investigate the atrium voice booth": ["U03", "booth"],
	"Ask Cal for the service key / repair landing": ["U05", "cal"],
	"Follow the signal / lost property": ["U07", "claim"],
	"Farrand / east gate in the UMC atrium": ["U03", "farrand_gate"],
	"Give the volunteers an ending / Farrand tent": ["F02", "volunteers"],
	"One bounded rehearsal / Chip on the audience lawn": ["F04", "chip"],
	"Imani chooses her song / backstage cue sheet": ["F05", "consent"],
	"End the repeated show / ENCORE on the main stage": ["F06", "encore"],
	"Follow the ceremony directory / Old Main from Norlin steps": ["N01", "oldmain_route"],
	"Norlin / meet Nell at the checkout desk": ["N02", "nell"],
	"Imani chooses her recording / reading room": ["N03", "recording_choice"],
	"Choose a useful stopping point / reading-room bookmark": ["N03", "bookmark"],
	"Open a passage / crank in the moving stacks": ["N04", "stack_crank"],
	"Keep one sentence / ERRATA in the moving stacks": ["N04", "errata"],
	"Source reel / meet Cal and Dev across the quad at Engineering": ["E02", "dev"],
	"Revise the suspended model / upstairs from the test floor": ["E04", "model_plan"],
	"Probe the test points / Professor Eric on the test floor": ["E03", "eric"],
	"Install the bridge with Dev / shared workshop": ["E02", "dev"],
	"Recover the source reel / upstairs control booth": ["E05", "source_reel"],
	"Return the source / AUTOCOMPLETE in Norlin's closed archive": ["N06", "autocomplete"],
	"Hear the full source / playback room through the archive": ["N07", "playback"],
	"Read the changing notices / Old Main notice hall": ["O02", "notice_limits"],
	"Find VAL's first instruction / Old Main empty office": ["O03", "origin_directory"],
	"Choose explicit limits / consent form in the cabinet room": ["O04", "finite_plan"],
	"Submit one finite plan / Todd at the cabinet desk": ["O04", "todd"],
	"Ask Rook what he fears / Old Main courtyard": ["O01", "rook"],
	"Follow the procession / Macky comes next": ["O01", "macky_route"],
	"Tickets are invitations / Macky cloakroom": ["M03", "attendees"],
	"Imani chooses the ending / Macky orchestra pit": ["M04", "final_score"],
	"Revise one last shift / Rook on the balcony": ["M05", "rook"],
	"Finish the interview / Val on the graduation stage": ["M06", "val"],
	"Choose a morning / party at the dawn exit": ["M07", "dawn_conversation"],
	"Thank Mags / morning UMC terrace": ["U02", "mags"],
	"Call home / Broadway bus stop": ["U01", "bus"],
	"One friendly set / Jakerson on the tennis courts": ["", "jakerson_match"],
}

static func met(flags: Dictionary, requires: Array) -> bool:
	for flag: Variant in requires:
		var value: Variant = flags.get(str(flag), false)
		if value == null or (value is bool and not value) or (value is String and str(value).is_empty()): return false
	return true

static func has_object(g: Node, room: String, id: String) -> bool:
	for o: Dictionary in g.rooms[room].objects:
		if str(o.id) == id: return true
	return false

## Breadth-first over doors from here. Returns {room: [previous room, door object]}.
static func reach(g: Node, open_only: bool) -> Dictionary:
	var here: String = str(g.state.room)
	var seen: Dictionary = {here: ["", {}]}
	var queue: Array = [here]
	while not queue.is_empty():
		var room: String = queue.pop_front()
		for o: Dictionary in g.rooms[room].objects:
			if str(o.get("kind", "")) != "door" or not o.has("to"): continue
			var next: String = str(o.to)
			if seen.has(next) or not g.rooms.has(next): continue
			if open_only and not met(g.state.flags, o.get("requires", [])): continue
			seen[next] = [room, o]; queue.append(next)
	return seen

## {point: Vector2 in this room, door: bool} or {} when there is nothing to show.
static func target(g: Node) -> Dictionary:
	var goal: Array = TARGETS.get(NativeCampaign.objective(g.state), [])
	if goal.is_empty(): return {}
	var here: String = str(g.state.room)
	var id: String = str(goal[1])
	for open_only: bool in [true, false]:
		var seen: Dictionary = reach(g, open_only)
		var room: String = str(goal[0])
		if room.is_empty():
			room = ""
			for candidate: String in seen:
				if has_object(g, candidate, id): room = candidate; break
		if room.is_empty() or not seen.has(room): continue
		if room == here:
			for area: Area2D in g.areas:
				var o: Dictionary = area.get_meta("definition")
				if str(o.id) == id: return {"point": area.position, "door": false}
			return {}
		while str(seen[room][0]) != here: room = str(seen[room][0])
		var door: Dictionary = seen[room][1]
		return {"point": Vector2(float(door.x), float(door.y)), "door": true}
	return {}
