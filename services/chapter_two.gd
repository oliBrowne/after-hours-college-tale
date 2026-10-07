class_name NativeChapterTwo
extends RefCounted
const BOSSES: Array[String] = ["errata", "index", "eric"]
const AFTERMATHS: Array[String] = ["errata", "index", "eric", "source_reel", "playback"]
static func say(g: Node, lines: Array, flags: Dictionary = {}) -> void:
	g.dialogue(lines, func() -> void:
		g.state.flags.merge(flags,true);g.persist();g.resume_world())
static func fight(g: Node, id: String, lines: Array) -> void:
	g.dialogue(lines,func() -> void: g.boss_id=id;g.start_battle())
static func handle(g: Node, object: Dictionary) -> bool:
	if object.get("kind","")=="door":return false
	var f: Dictionary=g.state.flags
	var room: String=str(g.state.room)
	if not room.begins_with("N") and not room.begins_with("E"):return false
	match str(object.id):
		"nell":
			if f.get("library_pass",false):
				say(g,[["Nell","Reading room left. Moving stacks right. Engineering across the quad. Those are destinations, not assignments.","warm"],["Nell","The source reel unlocks INDEX. Your bookmark is a stopping point, not a duty to finish every page.","neutral"]]);return true
			say(g,[["Nell","Closing time. Unless you're returning the voice that's been checking out entire lives.","concern"],["Imani","It borrowed mine without asking.","concern"],["Nell","Objects used when people make promises are waking up. The catalogue keeps a future for every promise.","neutral"],["Walt","And when a person changes their mind?","neutral"],["Nell","That's the part INDEX won't shelve. Take this visitor pass. Choose a bookmark in the reading room; turn the crank in the stacks.","neutral"],["Nell","Cal and Dev have the earlier recording at Engineering. Bring it back to the closed archive. I'll keep the return desk lit.","warm"]],{"library_pass":true});return true
		"recording_choice":
			if f.has("imani_recording"):
				say(g,[["Imani","My rough demo stays. A shaky note still belongs to me.","warm"]]);return true
			g.dialogue([["Loudspeaker","IMANI BELL. EVERY AUDIENCE APPROVES. EVERY NOTE ARRIVES ON TIME.","warm"],["Imani","It sounds wonderful. It also sounds like somebody who never gets tired.","concern"],["Jules","Do you want to hear it?","neutral"],["Imani","I'll choose. Mine has the missed breath before the chorus. I know why I needed it.","neutral"]],g.resume_world,[g.option("Imani keeps her rough demo.",func() -> void: say(g,[["Imani","That one's mine. We can work with the missed breath.","warm"]],{"imani_recording":"own"})),g.option("Imani listens, then chooses her demo.",func() -> void: say(g,[["Imani","I listened. I don't have to hate that version to choose my own.","warm"],["Walt","A comparison isn't a contract.","neutral"]],{"imani_recording":"compared"}))]);return true
		"bookmark":
			say(g,[["Jules","A bookmark with a blank line: NEXT USEFUL STEP.","neutral"],["Imani","Not THE REST OF YOUR LIFE. Much better stationery.","warm"]],{"bookmark_found":true});return true
		"stack_crank":
			if f.get("stacks_shifted",false):say(g,[["Nell","The shelves have stopped at the marked passage. Leave that route open for the next reader.","warm"]]);return true
			g.dialogue([["Jules","The handle moves two shelves, not the whole library.","neutral"],["Walt","Then two shelves is our job.","warm"]],func() -> void:
				f.stacks_shifted=true;g.enter_room(room,g.player.position);g.resume_world());return true
		"errata":
			if f.has("errata_resolution"):say(g,[["ERRATA","ONE SENTENCE MAY STAY IMPERFECT. THIS ONE.","warm"]]);return true
			fight(g,"errata",[["ERRATA","REPLACE UNCERTAINTY. ERASE HESITATION. FIX EVERY LINE.","concern"],["Imani","My recording has a sentence I want to keep.","neutral"],["ERRATA","THEN DEFEND IT. THREE PAUSES. THREE CORRECTIONS. I WILL NOT MISS ONE.","neutral"],["Walt","Or clear the correction machinery. The archive has room for a repair note.","neutral"]]);return true
		"index":
			if f.has("index_resolution"):say(g,[["INDEX","NEXT USEFUL STEP: LISTEN. THE OTHER PAGES CAN WAIT.","warm"]]);return true
			if not f.get("source_reel",false):
				say(g,[["INDEX","YOUR VOICES HAVE SIX HUNDRED POSSIBLE ENDINGS. WHICH ONE IS THE ORIGINAL?","concern"],["Imani","You filed our fear as a plan.","concern"],["INDEX","BRING THE EARLIEST REEL. ENGINEERING CONTROL BOOTH. CAL AND DEV KNOW THE WAY.","neutral"],["Jules","Then we go across the quad. Not through every possible ending.","neutral"]],{"index_seen":true});return true
			if not f.has("imani_recording"):
				say(g,[["Imani","Before we file anything, I need to choose my recording in the reading room.","neutral"]]);return true
			fight(g,"index",[["INDEX","THE SOURCE HAS RETURNED. NOW FINISH EVERY FUTURE IT OPENED.","concern"],["Jules","We can leave one useful stopping point.","neutral"],["INDEX","A STOPPING POINT? EVERY PAGE CONTINUES. PROVE ONE PAGE CAN END.","neutral"],["Imani","Three verses. Then the playback room. I brought my own voice.","warm"]]);return true
		"rook":
			if room=="N05":
				say(g,[["Rook","Margin garden. For things the page can't hold. Mostly students and sandwich crumbs.","warm"],["Walt","You lent a key at Farrand. Thanks.","warm"],["Rook","Useful people get invited back. Useful paper, too.","neutral"],["Imani","Is that why you're keeping the night going?","concern"],["Rook","I only know what I heard by the stage. Engineering is across the quad. I'll check their door.","neutral"]],{"rook_norlin":true});return true
			say(g,[["Rook","Control booth closed. Health and safety. Emotional load-bearing capacity.","neutral"],["Walt","The workshop stairs are open. We can reach the model from above.","neutral"],["Jules","Why close just that door?","concern"],["Rook","Some recordings end a shift. Some end the person working it.","concern"]],{"rook_engineering":true});return true
		"cal":
			say(g,[["Cal","Dev and I built a model that could hold every possible plan. It doesn't hold one real person.","concern"],["Walt","I've repaired radios with that problem. Beautiful circuits. Nowhere for the battery.","warm"],["Cal","Dev drew two grounded supports. Talk to Dev, then take the test-floor stairs to the model.","neutral"]],{"cal_engineering_met":true});return true
		"dev":
			if f.has("eric_resolution"):
				if f.get("bridge_ready",false):say(g,[["Dev","The bridge is holding. Control booth upstairs; the marked shortcut returns to Norlin.","warm"]]);return true
				say(g,[["Dev","Two supports, shared work. Cal, can you brace the near span?","neutral"],["Cal","Yes. Just that span. Then we test it together.","warm"],["Dev","The professor signed off on it himself. First time all night." if f.eric_resolution=="peaceful" else "Professor Eric is resting in the lounge. We'll show him the bridge in daylight.","warm"],["Walt","I'll hold the work light. Ask before changing the load.","neutral"],["Dev","Done. The control booth is accessible upstairs, and the shortcut crosses back to Norlin.","warm"]],{"bridge_ready":true});return true
			say(g,[["Dev","Hi. Sorry about the shouting. I drew a bridge for actual feet, which was apparently controversial.","warm"],["Cal","I put the whole future on the old model.","concern"],["Dev","Revise the model above the test floor. Then talk to Professor Eric downstairs. He's been re-testing the old model since ten.","neutral"],["Dev","If he sees three clean test points, maybe he'll finally call it done.","neutral"],["Dev","Come back to me afterwards. We still need to install the ordinary bridge together.","neutral"]],{"dev_met":true});return true
		"model_plan":
			if f.get("model_revised",false):say(g,[["Cal","Two spans. Two foundations. People can meet in the middle.","warm"]]);return true
			g.dialogue([["Imani","That suspended arch is gorgeous. It has no way down.","concern"],["Walt","Dev's sketch is taped to the rail. Keep the useful pieces; lower two spans onto real foundations.","neutral"],["Jules","Cal's curve, Dev's supports. They decided. We just do the lifting.","neutral"]],g.resume_world,[g.option("Revise the model the way Dev drew it.",func() -> void:
				f.model_revised=true;g.enter_room(room,g.player.position);say(g,[["Imani","It keeps the curve. It just doesn't have to hold everything.","warm"],["Jules","Now the hard part: convincing Professor Eric it's finished. He's downstairs.","neutral"]]))]);return true
		"eric":
			if f.has("eric_resolution"):say(g,[["Professor Eric","Good enough to ship IS a measurement. Go on, the workshop needs you.","warm"]]);return true
			if not f.get("model_revised",false):say(g,[["Professor Eric","Not now, not now. The old model is still ringing. One more measurement.","neutral"],["Jules","He won't stop testing the old one. We should revise the model upstairs first.","neutral"]]);return true
			fight(g,"eric",[["Professor Eric","Visitors! Perfect timing. Hold this probe. One more measurement and we'll know everything.","warm"],["Professor Eric","Rule of thumb: never trust a signal you haven't looked at. So we look. Again. And again.","concern"],["Walt","Pretty sure that bridge has been measured forty times tonight.","concern"],["Professor Eric","Forty-one is a much nicer number!","warm"],["Jules","Three clean readings, then. Maybe he'll let it be done.","neutral"]]);return true
		"source_reel":
			if not f.get("bridge_ready",false):say(g,[["Dev","Install the bridge with us in the workshop first.","neutral"]]);return true
			if f.get("source_reel",false) and f.get("aftermath_pending","")!="source_reel":say(g,[["Jules","We have the source reel. Back across the repaired shortcut, then through the stacks to INDEX.","neutral"]]);return true
			f.source_reel=true;f.aftermath_pending="source_reel";g.persist();aftermath(g,"source_reel");return true
		"playback":
			if not f.has("index_resolution") or not f.get("source_reel",false):say(g,[["Imani","Bring the source reel and settle INDEX first.","neutral"]]);return true
			if f.get("chapter2_complete",false):say(g,[["Imani","Old Main. The directory will tell us who gave the ceremony its first purpose.","neutral"]]);return true
			f.aftermath_pending="playback";g.persist();aftermath(g,"playback");return true
		"norlin_rest", "playback_lamp", "workshop_rest", "control_lamp":
			for member: Dictionary in g.state.party:member.hp=member.max
			g.persist();g.audio.effect("save")
			g.open_menu(g.Mode.MENU,"Rested / choose a save slot",[g.option("Save slot 1",func() -> void:g.manual_save("slot1")),g.option("Save slot 2",func() -> void:g.manual_save("slot2")),g.option("Save slot 3",func() -> void:g.manual_save("slot3")),g.option("Back",g.resume_world)]);return true
	return false
static func aftermath(g: Node,id: String) -> void:
	var f: Dictionary=g.state.flags
	var peaceful: bool=f.get(id+"_resolution","")=="peaceful"
	g.boss_id="";g.enter_room(str(g.state.room),Vector2(g.state.x,g.state.y),false)
	var scenes: Dictionary={
		"errata":[["ERRATA","THE MISSED BREATH STAYS. TAKE THE PASSAGE.","warm"],["Imani","You can suggest a change. I can choose whether it's mine.","warm"]] if peaceful else [["Imani","The correction ribbon snapped. I left the pencil a repair note.","concern"],["Jules","The archive is ahead. Bring the reading-room bookmark.","neutral"]],
		"eric":[["Professor Eric","Three clean test points. Huh. The answer is: it's done. Good enough, and I measured it.","warm"],["Professor Eric","New rule of thumb for the board: sleep is part of the design. Go install your bridge.","warm"],["Jules","Dev's waiting in the workshop. Let's go install that bridge.","neutral"]] if peaceful else [["Professor Eric","Oof. Okay. Okay. The scope's off. Maybe that was the measurement I needed.","concern"],["Walt","He's alright, just tired. Cal and Dev can finish the bridge in the workshop.","concern"]],
		"index":[["INDEX","FILED UNDER NEXT USEFUL STEP. NOT EVERY POSSIBLE LIFE.","warm"],["Imani","Mine includes a missed breath. Keep it.","warm"],["Jules","Now the playback room through the archive's east door.","neutral"]] if peaceful else [["Nell","The drawers are jammed. I'll reopen one shelf at a time.","concern"],["Imani","Our recording is safe. The playback room is through the east door.","neutral"]],
		"source_reel":[["Loudspeaker","VAL / TALENT ACQUISITION. A SEAT FOR EVERY FUTURE HIRE. BEGIN WITH A PROMISE.","concern"],["Jules","That's the booth's source. Somebody is recruiting a whole graduating class out of things we might become.","concern"],["Walt","Rook shut the direct door. He was afraid this would end his shift.","neutral"],["Imani","Take this back to INDEX through the repaired shortcut. Then we hear the whole recording.","neutral"]],
		"playback":[["Loudspeaker","EVERY POSSIBLE GRADUATE MUST ARRIVE. RESERVE MORE CHAIRS. UNTIL EVERY FUTURE IS SEATED, THE NIGHT REMAINS OPEN.","concern"],["Jules","The chairs are taking the space living people need.","concern"],["Pip","If that magic made me, do I stop too?","concern"],["Walt","You chose to come with us. A purpose can change with the person using it.","neutral"],["Imani","Rook needs to hear that. First, the booth's directory in Old Main. Who gave VAL this job?","neutral"],["Jules","One real answer, then a way home. Take the quad's Old Main path.","warm"]]}
	g.dialogue(scenes[id],func() -> void:
		if id=="playback":f.playback_heard=true;f.chapter2_complete=true
		f.aftermath_pending="";g.persist();g.resume_world())
static func objective(s: Dictionary) -> String:
	var f: Dictionary=s.flags
	if f.get("chapter2_complete",false):return "Follow the ceremony directory / Old Main from Norlin steps"
	if not f.get("library_pass",false):return "Norlin / meet Nell at the checkout desk"
	if not f.has("imani_recording"):return "Imani chooses her recording / reading room"
	if not f.get("bookmark_found",false):return "Choose a useful stopping point / reading-room bookmark"
	if not f.get("stacks_shifted",false):return "Open a passage / crank in the moving stacks"
	if not f.has("errata_resolution"):return "Keep one sentence / ERRATA in the moving stacks"
	if not f.get("dev_met",false):return "Source reel / meet Cal and Dev across the quad at Engineering"
	if not f.get("model_revised",false):return "Revise the suspended model / upstairs from the test floor"
	if not f.has("eric_resolution"):return "Probe the test points / Professor Eric on the test floor"
	if not f.get("bridge_ready",false):return "Install the bridge with Dev / shared workshop"
	if not f.get("source_reel",false):return "Recover the source reel / upstairs control booth"
	if not f.has("index_resolution"):return "Return the source / INDEX in Norlin's closed archive"
	return "Hear the full source / playback room through the archive"
