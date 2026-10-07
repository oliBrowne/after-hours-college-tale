class_name NativeFinalCampaign
extends RefCounted
const IDS: Array[String]=["cone","empty_chair","rook","val"]
const AFTERMATHS: Array[String]=["cone","empty_chair","rook","val","dawn"]
static func handle(g: Node, object: Dictionary) -> bool:
	if object.get("kind","")=="door":return false
	var f: Dictionary=g.state.flags
	var id: String=str(object.id)
	var room: String=str(g.state.room)
	if id=="cone":
		if f.has("cone_resolution"):NativeChapterTwo.say(g,[["CONE COMMITTEE","ONE ROUTE. CANCELLED CALLS STAY CANCELLED.","warm"]]);return true
		g.dialogue([["CONE COMMITTEE","LEFT. RIGHT. BOTH. SAFETY HAS FORMED A COMMITTEE.","concern"],["Jules","One announced route would be safer than three simultaneous instructions.","neutral"]],g.resume_world,[g.option("Practice one marked route.",func() -> void:NativeChapterTwo.fight(g,"cone",[["CONE COMMITTEE","FOLLOW THREE GREEN ROWS. CROSSED-OUT CALLS ARE CANCELLED. MOVE FREELY; NO HOPS REQUIRED.","neutral"]])),g.option("Leave the optional committee for later.",g.resume_world)]);return true
	if id=="empty_chair":
		if f.has("empty_chair_resolution"):NativeChapterTwo.say(g,[["EMPTY CHAIR","THERE IS STILL ROOM FOR SOMEONE TO BE ABSENT.","warm"]]);return true
		g.dialogue([["Imani","Somebody left a chair empty on purpose.","neutral"],["Walt","We don't need to invent who belongs in it.","neutral"]],g.resume_world,[g.option("Respect the empty space.",func() -> void:NativeChapterTwo.fight(g,"empty_chair",[["EMPTY CHAIR","KEEP THE SEAT CLEAR. REST BY THE LITTLE LANTERN. YOU DO NOT HAVE TO FILL EVERY GAP.","neutral"]])),g.option("Leave the chair quietly.",func() -> void:NativeChapterTwo.say(g,[["Jules","We can leave it empty without making it a test.","warm"]],{"absence_respected":true}))]);return true
	if not str(f.get("ending","")).is_empty():
		if id=="mags":NativeChapterTwo.say(g,[["Mags","The mixer is back. The work has an end. I brought breakfast, which is an even better end.","warm"],["Walt","I'll have cocoa. And I'll choose where I go after that.","warm"],["Mags","Of course. Nobody's breakfast comes with an assignment.","warm"]],{"morning_thanks":true});return true
		if id=="booth":NativeChapterTwo.say(g,[["Booth","CLOSED. ORDINARY QUESTIONS AVAILABLE IN DAYLIGHT.","warm"],["Imani","Good. I can bring my ordinary, unfinished answer.","warm"]]);return true
		if room=="U01" and id=="bus":
			if f.get("dawn_complete",false):ending_menu(g);return true
			g.dialogue([["Jules","Mom said I don't have to bring home a successful evening. Just tell her where I am.","neutral"],["Imani","You can tell her now. We can carry the mixer to the bus stop.","warm"],["Walt","And I'll hold the light for one departure. Then breakfast.","warm"]],g.resume_world,[g.option("Jules: I am here. I am coming home.",func() -> void:f.family_reply="where-i-am";f.aftermath_pending="dawn";g.persist();aftermath(g,"dawn")),g.option("Jules: I need help getting home.",func() -> void:f.family_reply="ask-for-help";f.aftermath_pending="dawn";g.persist();aftermath(g,"dawn"))]);return true
	if not room.begins_with("M"):return false
	match id:
		"mags":NativeChapterTwo.say(g,[["Mags","I found a thermos. I found my closing time. Both still work.","warm"],["Jules","Rook is afraid an ending means he stops existing.","concern"],["Mags","People are allowed to clock out before the building falls down. Tell him I saved a cup.","neutral"]],{"mags_macky":true});return true
		"procession_notice":NativeChapterTwo.say(g,[["Jules","Reserved for every possible graduate. The reservation is eating the actual pavement.","concern"],["Pip","A door only needs enough room for the next person.","neutral"]]);return true
		"attendees":
			if f.get("attendees_freed",false):NativeChapterTwo.say(g,[["Mara","Tickets are invitations again. Some people left. Some chose to stay.","warm"]]);return true
			g.dialogue([["Mara","My ticket says I have to arrive as every person I could become. I would settle for one coat.","concern"],["Eli","Mine says leaving cancels my place forever. Nobody told me that when I took it.","concern"],["Imani","A ticket isn't consent to stay forever. You get to choose.","neutral"]],g.resume_world,[g.option("Guests can leave with their tickets.",func() -> void:NativeChapterTwo.say(g,[["Mara","I'll go home. Keep a seat free without writing my name on tomorrow.","warm"],["Eli","I can stay for one ending. Then I leave too.","warm"]],{"attendees_freed":true,"attendee_choice":"leave"})),g.option("Offer one finite, optional gathering.",func() -> void:NativeChapterTwo.say(g,[["Mara","I choose one gathering. I'll leave when it's over.","warm"],["Eli","So will I. A small invitation, answered for ourselves.","warm"]],{"attendees_freed":true,"attendee_choice":"invite"}))]);return true
		"mara":NativeChapterTwo.say(g,[["Mara","One borrowed appliance became a whole night. You still get to choose when you go home.","warm"]]);return true
		"eli":NativeChapterTwo.say(g,[["Eli","I'm keeping an ordinary seat open. I don't need every version of myself to sit in it.","warm"]]);return true
		"final_score":
			g.dialogue([["Imani","The score has no rests. It wants applause to last forever.","concern"],["Jules","What do you want to play?","neutral"],["Imani","A verse I can finish, or an instrumental that makes room for the room. My choice.","neutral"]],g.resume_world,[g.option("Imani chooses her rough verse.",func() -> void:NativeChapterTwo.say(g,[["Imani","I keep the missed breath. I write an ending after the verse.","warm"]],{"music_ready":true,"final_score":"honest"})),g.option("Imani chooses a quiet instrumental.",func() -> void:NativeChapterTwo.say(g,[["Imani","No audition for every listener. An instrumental, with a real final note.","warm"]],{"music_ready":true,"final_score":"instrumental"}))]);return true
		"rook":
			if f.has("rook_resolution"):NativeChapterTwo.say(g,[["Rook","One exit. One shift. Mags promised a cup, not a purpose for my entire life.","warm"]]);return true
			if not f.get("attendees_freed",false) or not f.get("music_ready",false):NativeChapterTwo.say(g,[["Rook","Guests in the cloakroom. Score in the pit. Give those people choices before asking me to trust an ending.","neutral"]]);return true
			NativeChapterTwo.fight(g,"rook",[["Rook","LAST CALL. No one leaves until everyone who could have arrived is accounted for.","concern"],["Jules","That's two incompatible jobs. We can revise one, with you.","neutral"],["Rook","Take the key to one exit first. Then CONNECT offers REVISE: choose west or east and decline the other. I need one shift I can finish.","neutral"],["Walt","After that, two shared stopping cues. You will not hold the room alone.","warm"]]);return true
		"val":
			if f.has("val_resolution"):NativeChapterTwo.say(g,[["Val","The chairs can be chairs. I can ask people what comes next.","warm"]]);return true
			NativeChapterTwo.fight(g,"val",[["VAL","EVERYONE YOU COULD BE. A PLACE FOR ALL OF YOU. NO ONE WILL BE LEFT OUT. NO ONE MAY LEAVE.","concern"],["Jules","The futures have taken the space living people need.","concern"],["Imani","First one familiar return and stopping cue. Then each of us rejects our own impossible role.","neutral"],["Walt","We revise the reserved chairs into an open passage. We hear the small person inside that frame.","neutral"],["Jules","Then an explicit choice: RELEASE the impossible futures, REWRITE one finite gathering, or BREAK the mechanism and repair what happens after.","neutral"],["Pip","Nobody has to lose me forever. I can hold the door because I choose to.","warm"]]);return true
		"dawn_conversation":
			NativeChapterTwo.say(g,[["Jules","The morning isn't asking who I will become. It's asking what we do next.","warm"],["Imani","Breakfast. Then I keep working on my recording, with the missed breath.","warm"],["Walt","I'll check the lantern handle. After cocoa. And I'll ask for the tool I need.","warm"],["Pip","One door at a time. I don't have to be lost to have a purpose.","warm"],["Jules","Let's take the morning path back to the UMC, thank Mags, then call home at the Broadway bus stop.","neutral"]],{"dawn_talk_read":true});return true
		"procession_lamp","lobby_lamp","pit_lamp","balcony_lamp","stage_lamp","dawn_lamp":
			for member: Dictionary in g.state.party:member.hp=member.max
			g.persist();g.audio.effect("save");g.open_menu(g.Mode.MENU,"Rested / choose a save slot",[g.option("Save slot 1",func() -> void:g.manual_save("slot1")),g.option("Save slot 2",func() -> void:g.manual_save("slot2")),g.option("Save slot 3",func() -> void:g.manual_save("slot3")),g.option("Back",g.resume_world)]);return true
	return false
static func decorate(g: Node, result: Dictionary, commands: Array) -> void:
	var rejection_committed: bool=false
	for command: Dictionary in commands:
		if command.has("revision"):
			if g.boss_id=="rook":result.revision=str(command.revision)
			if g.boss_id=="val":result.val_revision=str(command.revision)
		if command.has("reject") and g.boss_id=="val" and g.boss_stage==1 and str(command.reject)==str(g.battle.party[int(command.actor)].id):
			rejection_committed=true
			var rejected: Array=result.get("rejected",[]).duplicate()
			if not str(command.reject) in rejected:rejected.append(str(command.reject))
			result.rejected=rejected
		if command.has("ending") and g.boss_id=="val":
			result.ending=str(command.ending)
			if result.ending=="break" and result.outcome=="peaceful":result.outcome="forceful"
	if rejection_committed and result.get("rejected",[]).size()==3:result.promise=true
static func record_defense(g: Node, success: bool, promised: bool) -> bool:
	if not success or not promised:return false
	if g.boss_id=="rook":
		if g.boss_stage==2:g.battle.final_ready=true
		else:g.battle.rook_stage=g.boss_stage+1;g.boss_stage=int(g.battle.rook_stage)
	if g.boss_id in ["cone","empty_chair"]:g.battle.final_ready=true
	if g.boss_id!="val":return false
	if g.boss_stage==3:g.battle.final_ready=true;return false
	g.battle.val_stage=g.boss_stage+1;return true
static func checkpoint(g: Node) -> void:
	for member: Dictionary in g.battle.party:member.hp=mini(int(member.max),int(member.hp)+18)
	g.merge_party(g.battle.party);g.state.inventory=g.battle.inventory.duplicate(true)
	var b: Dictionary=g.battle
	var saved: Dictionary={"party":b.party,"inventory":b.inventory,"hp":b.hp,"openness":b.openness,"sync":b.sync,"turn":b.turn,"stage":b.val_stage,"rejected":b.get("rejected",[]),"revision":b.get("val_revision",""),"force":b.get("val_force",false)}
	g.state.flags.val_checkpoint=JSON.stringify(saved);g.checkpoint=g.state.duplicate(true)
	if not g.persist():g.message("Phase checkpoint could not be saved. Continue or use pause to retry saving.")
static func restore_checkpoint(g: Node) -> bool:
	var raw: String=str(g.state.flags.get("val_checkpoint",""))
	if raw.is_empty() or raw.length()>32768:return false
	var parser:=JSON.new()
	if parser.parse(raw)!=OK or not parser.data is Dictionary:return false
	var saved: Dictionary=parser.data
	for key: String in ["hp","openness","sync","turn","stage"]:
		if not NativeSaveService._number(saved.get(key)):return false
	if not NativeSaveService._integer(saved.stage,0,3) or not NativeSaveService._integer(saved.hp,1,500) or not NativeSaveService._integer(saved.sync,0,100) or not NativeSaveService._integer(saved.openness,0,100) or not NativeSaveService._integer(saved.turn,0,10000):return false
	if not saved.get("rejected") is Array or saved.rejected.size()>3 or not saved.get("revision") in ["","left","right"] or not saved.get("force") is bool:return false
	var unique: Array=[]
	for id: Variant in saved.rejected:
		if not id in ["jules","imani","walt"] or id in unique:return false
		unique.append(id)
	var validation: Dictionary=g.state.duplicate(true);validation.party=saved.get("party");validation.inventory=saved.get("inventory")
	if not NativeSaveService.validate_state(validation):return false
	g.battle=BattleRules.create_battle(saved.party,saved.inventory)
	for key: String in ["hp","openness","sync","turn"]:g.battle[key]=saved[key]
	g.battle.val_stage=int(saved.stage);g.battle.rejected=unique;g.battle.val_revision=str(saved.revision);g.battle.val_force=bool(saved.force);g.battle.final_ready=false
	g.boss_stage=int(saved.stage);g.boss_rounds=int(saved.stage);g.shown_enemy_hp=int(g.battle.hp)
	return true
static func phase_dialogue(g: Node) -> void:
	g.boss_stage=int(g.battle.val_stage)
	g.foe.sprite_frames=NativeFinalArt.frames("val_small" if g.boss_stage==3 else "val");g.foe.play("idle_down");NativeCastArt.fit(g.foe,g.foe_height())
	var lines: Array=[]
	if g.boss_stage==1:lines=[["VAL","JULES NEVER DISAPPOINTS. IMANI IS LOVED BY EVERYONE. WALT NEEDS NOBODY.","concern"],["Jules","Those people can't live a real day. In CONNECT, each of us rejects our own role; nobody answers for someone else.","neutral"],["Walt","Then we hold one shared green space. I can choose company without giving away my independence.","warm"]]
	elif g.boss_stage==2:lines=[["Imani","The ideal roles are paper. The chairs still take real space.","neutral"],["Jules","CONNECT > REVISE. Give up the reserved seats on one side. Then hold that usable passage open.","neutral"],["Walt","People get to choose whether they enter. An empty chair is allowed.","warm"]]
	else:lines=[["Val","I wanted everyone to have somewhere to go. I thought an ending meant I had failed them.","concern"],["Pip","I can hold a door. You can ask a question. We can choose a new small job.","warm"],["Jules","Two ordinary stopping cues. Then we choose openly what happens to this mechanism.","neutral"]]
	g.dialogue(lines,g.command_menu)
static func force_advance(g: Node) -> void:
	g.battle.outcome="active";g.battle.val_force=true;g.battle.val_stage=int(g.battle.get("val_stage",0))+1;g.battle.hp=160
	g.actor=0
	while g.actor<3 and int(g.battle.party[g.actor].hp)<=0:g.actor+=1
	checkpoint(g);phase_dialogue(g)
static func aftermath(g: Node, id: String) -> void:
	var f: Dictionary=g.state.flags;g.boss_id=""
	g.enter_room(str(g.state.room),Vector2(g.state.x,g.state.y),false)
	var peaceful: bool=f.get(id+"_resolution","")=="peaceful"
	if id=="dawn":
		g.dialogue([["Jules","I sent where I am, not a report about who I managed to become.","warm"],["Mom","I can meet you at the stop. You never had to earn the ride home.","warm"],["Imani","One evening. Not every future.","warm"],["Walt","One light. Then daylight.","warm"],["Jules","And a morning we can choose together.","warm"]],func() -> void:f.dawn_complete=true;f.aftermath_pending="";g.persist();NativeJakerson.graduation(g));return
	if id=="val":
		var ending: String=str(f.get("ending","break"))
		var first: Array=[["Val","The impossible futures can go. People can still choose to come back.","warm"],["Imani","My recording stays mine. We did not erase anybody's right to choose.","warm"]] if ending=="release" else [["Val","One finite gathering. Named jobs, shared work, and a closing time.","warm"],["Walt","Ask before inviting people. Leave room for no.","neutral"]] if ending=="rewrite" else [["Jules","The frame is stopped. We'll repair the ordinary room without rebuilding its impossible command.","concern"],["Val","The small puppet still has a voice. The people who chose a new purpose are still here.","warm"]]
		first.append_array([["Rook","One exit. One shift. I can finish it and still choose what comes after.","warm"],["Pip","I choose the door. ENCORE chose a show that ends. INDEX chose a useful stopping place.","warm"],["Jules","Those purposes don't belong to VAL anymore. We agreed them together.","neutral"],["Imani","The reserved chairs stop multiplying. The campus has room for morning.","warm"]])
		g.dialogue(first,func() -> void:f.dawn_started=true;f.aftermath_pending="";f.val_checkpoint="";g.enter_room("M07",Vector2(120,445),false);g.persist();g.resume_world());return
	var lines: Array=[["Rook","You held a small job with me. I can finish a shift without having to finish myself.","warm"],["Walt","Mags saved a cup. A cup, not a contract.","warm"],["Jules","The stage is open. Now VAL needs choices from the people it made.","neutral"]] if id=="rook" and peaceful else [["Rook","The key ring is bent. I can lend the stage key without becoming every locked door.","concern"],["Imani","We'll straighten it in daylight. For now, one exit is open.","neutral"]] if id=="rook" else [["CONE COMMITTEE","ONE MARKED ROUTE. THE OTHER CALLS ARE CANCELLED.","warm"]] if id=="cone" and peaceful else [["Jules","The route tape is broken. We left a repair note and a clear path.","neutral"]] if id=="cone" else [["EMPTY CHAIR","THE SPACE STAYS EMPTY. THAT CAN BE ENOUGH.","warm"]] if peaceful else [["Walt","The chair needs repair. Nobody has to fill it while we do that.","neutral"]]
	g.dialogue(lines,func() -> void:
		if id=="rook":f.balcony_open=true
		if id=="empty_chair":f.absence_respected=true
		f.aftermath_pending="";g.persist();g.resume_world())
static func ending_menu(g: Node) -> void:
	var title: String="Morning / "+str(g.state.flags.get("ending","release")).to_upper()
	var options: Array=[g.option("Keep exploring the changed campus",g.resume_world),g.option("Return to title",g.show_title)]
	if not g.state.flags.get("graduation_complete",false):options.insert(0,g.option("Epilogue / graduation day",func() -> void:NativeJakerson.graduation(g)))
	g.open_menu(g.Mode.MENU,title,options)
static func objective(s: Dictionary) -> String:
	var f: Dictionary=s.flags
	if f.get("graduation_day",false) and not f.has("jakerson_final_resolution"):return "One friendly set / Jakerson on the tennis courts"
	if f.get("dawn_complete",false):return "Evening complete / explore the morning campus"
	if f.has("val_resolution"):
		if not f.get("dawn_talk_read",false):return "Choose a morning / party at the dawn exit"
		if not f.get("morning_thanks",false):return "Thank Mags / morning UMC terrace"
		return "Call home / Broadway bus stop"
	if not f.get("attendees_freed",false):return "Tickets are invitations / Macky cloakroom"
	if not f.get("music_ready",false):return "Imani chooses the ending / Macky orchestra pit"
	if not f.has("rook_resolution"):return "Revise one last shift / Rook on the balcony"
	return "Make room for living people / VAL on the graduation stage"
