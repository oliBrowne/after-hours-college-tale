class_name NativeCampaign
extends RefCounted
const VERSION: String = "0.7.0 / FULL EVENING"
const EXPANSION_BOSSES: Array[String] = ["walt","encore"]
static func migrate(before: Dictionary) -> Dictionary:
	var s: Dictionary=before.duplicate(true)
	# The test-floor boss LOADBEARER became Professor Eric (2026-10-07); carry his outcome over.
	if s.has("flags") and s.flags.has("loadbearer_resolution") and not s.flags.has("eric_resolution"): s.flags.eric_resolution = s.flags.loadbearer_resolution
	# The garden boss EMPTY CHAIR became Chad the networker (2026-10-07); carry his outcome over.
	if s.has("flags") and s.flags.has("empty_chair_resolution") and not s.flags.has("chad_resolution"): s.flags.chad_resolution = s.flags.empty_chair_resolution
	# The archive boss INDEX became AUTOCOMPLETE (2026-10-07); carry its outcome and a pending aftermath
	# hook over. The old flag stays beside the new one, so the same save still opens in an older build.
	if s.has("flags") and s.flags.has("index_resolution") and not s.flags.has("autocomplete_resolution"): s.flags.autocomplete_resolution = s.flags.index_resolution
	if s.has("flags") and s.flags.has("index_seen") and not s.flags.has("autocomplete_seen"): s.flags.autocomplete_seen = s.flags.index_seen
	if s.has("flags"):
		for hook: String in ["aftermath_pending", "legacy_aftermath_pending"]:
			if str(s.flags.get(hook, "")) == "index": s.flags[hook] = "autocomplete"
	if str(s.party[2].id)=="cal":
		s.party[2]=BattleRules.initial_party()[2].duplicate(true)
		s.flags.roster_revision="jules-imani-walt"
		if s.flags.get("cal_joined",false): s.flags.cal_key_received=true
		if s.flags.get("imani_joined",false) and not s.flags.get("walt_joined",false): s.flags.walt_intro_pending=true
	return s
static func legacy_slot(game: Node, slot: String) -> Dictionary:
	for folder: String in ["AfterHoursCollegeTaleChapter3", "AfterHoursCollegeTaleChapter2", "AfterHoursCollegeTaleChapter1", "AfterHoursCollegeTaleOpening02"]:
		var base: String=OS.get_environment("APPDATA").path_join(folder)
		var record: Dictionary=NativeSaveService.new(base.path_join("saves")).load_slot(slot)
		if record.has("state"):return record
	return {"error":"No earlier save found."}
static func introduce_legacy(game: Node) -> void:
	game.dialogue([["Jules","Cal sent a note: he and Dev are at Engineering. The old repairs are still done.","neutral"],["Imani","That escaped recording went under Broadway. Someone in the underpass is keeping a lantern lit.","concern"],["Jules","We should meet him before following this signal any farther.","neutral"]],func() -> void:
		game.state.flags.walt_intro_pending=false
		game.state.flags.legacy_aftermath_room=str(game.state.room)
		game.state.flags.legacy_aftermath_pending=str(game.state.flags.get("aftermath_pending", ""))
		game.state.flags.aftermath_pending=""
		game.enter_room("U08",Vector2(64,272))
		game.resume_world())
static func handle(game: Node, object: Dictionary) -> bool:
	if NativeFinalCampaign.handle(game,object):return true
	if NativeChapterThree.handle(game,object):return true
	if NativeChapterTwo.handle(game,object):return true
	var f: Dictionary=game.state.flags
	var id: String=str(object.id)
	if id=="walt":
		if f.get("walt_joined",false): return false
		if f.has("walt_resolution"): aftermath(game,"walt");return true
		if not f.get("booth_seen",false):
			if f.get("walt_met",false):
				var still: Array=[["Walt","Still here. The porch is open, the bus is not.","warm"],["Walt","Go on, return the thing in your bag. I'll keep the light on.","neutral"]] if not f.get("mixer_returned",false) else [["Walt","Still here. The radio hasn't stopped muttering about the UMC, either.","concern"],["Walt","Find out what's humming in that atrium. Then come back and tell me, and I'll bring the lantern.","neutral"]] if not f.get("flyer_resolution",false) else [["Walt","That hum in the atrium has a name now, doesn't it?","concern"],["Walt","Check the booth. When it gets loud enough, you know where my porch is.","neutral"]]
				game.dialogue(still,game.resume_world);return true
			game.dialogue([["Walt","Mind the cardboard. It's my front porch.","neutral"],["Jules","Sorry. I'm just cutting through to the UMC.","neutral"],["Walt","Everybody does. Fastest way under Broadway, as long as you don't look at anyone.","neutral"],["Jules","I'm looking. Are you all right down here?","concern"],["Walt","Dry, mostly. I'm Walt. I fix radios for the shops on the Hill, when they remember to pay.","warm"],["Walt","That one's been odd all night. Every station it finds plays the same student voice. Saying a name.","concern"],["Jules","Whose name?","concern"],["Walt","Couldn't tell you. It kept saying it would rather have stayed. Go on, return whatever's in that bag.","neutral"],["Walt","If the voice gets louder, you know where my porch is.","warm"]],func() -> void: f.walt_met=true;game.persist();game.resume_world());return true
		game.dialogue([["Walt","You came back. The radio went quiet an hour ago. Now the wind is doing the talking.","concern"],["Imani","It escaped from our speaker. We've been following it.","concern"],["Walt","Then it came through here first. It's throwing my cardboard around like it's looking for someone.","concern"],["Jules","What would actually help?","neutral"],["Walt","One lantern through three gusts. Stay in its shelter and raise it when the warning comes. Or clear the loose debris.","neutral"]],func() -> void: game.boss_id="walt";game.start_battle());return true
	if id=="cal":
		if not f.get("walt_joined",false):
			game.dialogue([["Cal","That signal is running under Broadway. Check whoever is holding the light in the underpass before following it downstairs.","concern"],["Jules","One actual step first. Then we come back for the key.","neutral"]],game.resume_world);return true
		game.dialogue([["Cal","I'm staying here to disconnect the signal. Dev needs my hands at Engineering later.","neutral"],["Walt","We can take the smaller job downstairs.","neutral"],["Cal","Take the service key. It opens bowling and lost property. My repair work is not your homework.","warm"]],func() -> void:
			f.cal_key_received=true;f.cal_joined=true;game.persist();game.resume_world());return true
	if id=="rook":
		var lines: Array=[["Rook","Evening. Night marshal. Key lender. Occasional folding-chair enthusiast.","warm"],["Jules","You work here? This late?","neutral"],["Rook","Someone has to hold the doors. Leaving is allowed, by the way. People forget.","neutral"],["Rook","The volunteers keep being called back. Take the side passage. I lent them a key; they need an ending.","concern"]]
		if f.get("rook_met",false): lines=[["Rook","You've got three people and one plan. Bold ratio.","warm"],["Walt","And a lantern. We can see where the plan ends.","neutral"]]
		game.dialogue(lines,func() -> void: f.rook_met=true;game.persist();game.resume_world());return true
	if id=="volunteers":
		if not f.get("volunteers_released",false):
			game.dialogue([["Imani","The same three volunteers have folded this tent twice.","concern"],["Jules","Then we agree on one last task, with an end.","neutral"],["Walt","Tie the dry canvas; leave the wet one for daylight. Nobody owes a storm their whole evening.","neutral"],["Imani","Done. They're going home. I'll tell the stage that rest counts.","warm"]],func() -> void: f.volunteers_released=true;game.persist();game.resume_world());return true
		game.dialogue([["Jules","The canvas is tied. Their empty mugs are drying.","warm"]],game.resume_world);return true
	if id=="consent":
		game.dialogue([["Imani","The poster says everyone must perform. My name is already printed.","concern"],["Walt","Printing it isn't asking.","neutral"],["Imani","I choose one song. My unfinished one, or an instrumental. Three verses, then I stop.","warm"]],game.resume_world,[game.option("Imani chooses her unfinished song.",func() -> void: f.imani_performance="honest";game.persist();game.resume_world()),game.option("Imani chooses an instrumental.",func() -> void: f.imani_performance="instrumental";game.persist();game.resume_world())]);return true
	if id=="encore":
		if f.has("encore_resolution"): game.dialogue([["ENCORE","The lights can go out. Somebody heard the ending.","warm"]],game.resume_world);return true
		if not f.has("chip_resolution") or not f.get("volunteers_released",false) or not f.has("imani_performance"):
			game.dialogue([["ENCORE","THE CROWD IS STILL WORKING. THE SONG HAS NO AGREEMENT. AGAIN!","concern"],["Jules","First the volunteers, Chip's rehearsal and Imani's own choice.","neutral"]],game.resume_world);return true
		game.dialogue([["ENCORE","IF THE SHOW ENDS, WHO AM I FOR?","concern"],["Imani","An audience can leave and still have listened. I chose one song, not my entire life.","warm"],["Walt","A light can go out without being thrown away.","neutral"],["Jules","Three verses. One stopping cue. We can do that together.","neutral"]],func() -> void: game.boss_id="encore";game.start_battle());return true
	return false
static func aftermath(game: Node, id: String) -> void:
	var f: Dictionary=game.state.flags
	var peaceful: bool=f.get(id+"_resolution","")=="peaceful"
	if id=="walt":
		game.boss_id=""
		game.enter_room(str(game.state.room),Vector2(game.state.x,game.state.y),false)
		var lines: Array=[["Walt","You kept the lantern. You didn't promise to fix everything.","warm"],["Jules","We want to find the recording that started this.","neutral"],["Walt","So do I. I'm coming to inspect that booth, not to become your project.","neutral"],["Imani","Your company. Your choice. That works.","warm"]]
		if not peaceful: lines=[["Walt","The gusts are gone. The lantern handle is bent.","concern"],["Jules","I'll straighten the handle before we leave.","neutral"],["Walt","Good. You said what you'll repair. I'm Walt; I want to find that recording too.","neutral"],["Imani","We can walk together, without deciding each other's whole future.","warm"]]
		game.dialogue(lines,func() -> void:
			f.walt_joined=true;f.walt_intro_pending=false;f.aftermath_pending="walt"
			game.enter_room("U08",Vector2(game.state.x,game.state.y),false)
			game.persist()
			game.dialogue([["Walt","Lantern Ward gives us a shelter pocket. Windbreak protects one ally. Share the Warmth helps someone stand.","warm"],["Jules","Then we follow the voice together.","neutral"]],func() -> void:
				var pending: String=str(f.get("legacy_aftermath_pending", ""))
				f.legacy_aftermath_pending=""
				if not pending.is_empty():
					var old_room: String=str(f.get("legacy_aftermath_room", "U07"))
					var old_entry: Array=game.rooms[old_room].entry
					game.enter_room(old_room, Vector2(old_entry[0],old_entry[1]),false)
					f.aftermath_pending=pending;game.persist();game.show_aftermath(pending)
				else: f.aftermath_pending="";game.persist();game.resume_world()))
	elif id=="encore":
		game.boss_id=""
		game.enter_room("F06",Vector2(360,370),false)
		game.dialogue([["ENCORE","A final note. Then quiet. I can host a show that ends.","warm"]] if peaceful else [["Imani","The speaker went silent. We'll reconnect its ordinary sound in daylight.","concern"],["Walt","The volunteers are safe. We can repair what we broke.","neutral"]],func() -> void:
			f.aftermath_pending="encore";f.chapter1_complete=true;game.persist()
			game.dialogue([["Loudspeaker","If I stop being useful, they'll stop asking me to come.","concern"],["Jules","I never recorded that.","concern"],["Imani","The signal's going toward Norlin. We'll choose what we take with us.","neutral"]],func() -> void: f.aftermath_pending="";game.persist();game.resume_world()))
static func objective(s: Dictionary) -> String:
	var f: Dictionary=s.flags
	if f.get("movein_active",false):return NativeMoveIn.OBJECTIVE
	if f.get("chapter3_complete",false) and f.get("rook_confessed",false):return NativeFinalCampaign.objective(s)
	if f.get("chapter2_complete",false):return NativeChapterThree.objective(s)
	if f.get("chapter1_complete",false): return NativeChapterTwo.objective(s)
	if not f.get("mixer_returned",false): return "Return Imani's mixer / club room"
	if not f.has("flyer_resolution"): return "Read one living invitation / club room"
	if not f.get("imani_joined",false): return "Back through the atrium / something is humming"
	if not f.get("booth_seen",false): return "Investigate the atrium voice booth"
	if not f.get("walt_joined",false): return "Follow the escaped voice / Walt under the bridge"
	if not f.get("cal_key_received",false): return "Ask Cal for the service key / repair landing"
	if not f.has("claim_resolution"): return "Follow the signal / lost property"
	if not str(s.room).begins_with("F"): return "Farrand / east gate in the UMC atrium"
	if not f.get("volunteers_released",false): return "Give the volunteers an ending / Farrand tent"
	if not f.has("chip_resolution"): return "One bounded rehearsal / Chip on the audience lawn"
	if not f.has("imani_performance"): return "Imani chooses her song / backstage cue sheet"
	return "End the repeated show / ENCORE on the main stage"
