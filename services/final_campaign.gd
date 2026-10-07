class_name NativeFinalCampaign
extends RefCounted
const IDS: Array[String]=["cone","chad","rook","val"]
const AFTERMATHS: Array[String]=["cone","chad","rook","val","dawn"]
static func handle(g: Node, object: Dictionary) -> bool:
	if object.get("kind","")=="door":return false
	var f: Dictionary=g.state.flags
	var id: String=str(object.id)
	var room: String=str(g.state.room)
	if id=="cone":
		if f.has("cone_resolution"):NativeChapterTwo.say(g,[["Captain Lance","ONE LINE. CANCELLED CALLS STAY CANCELLED. I HAVE LAMINATED THE RULE.","warm"]]);return true
		g.dialogue([["Captain Lance","ON YOUR LEFT! ON YOUR RIGHT! ON BOTH SIDES! WHEN THREE RIDERS CALL THREE PASSES, THAT IS NOT A PACELINE. THAT IS A PILEUP WITH A CADENCE.","concern"],["Imani","His kit is so bright I can hear it. He is also whistling at a squirrel.","concern"],["Walt","He keeps checking his mirror for us. Loud, but he is checking.","neutral"],["Jules","One announced line would be safer than three calls at once.","neutral"]],g.resume_world,[g.option("Practice one marked route.",func() -> void:NativeChapterTwo.fight(g,"cone",[["Captain Lance","FOLLOW EACH GREEN ROUTE. ANY CALL MARKED CALL CANCELLED STAYS CANCELLED. MOVE FREELY; NO HOPS REQUIRED.","neutral"]])),g.option("Leave the optional peloton for later.",g.resume_world)]);return true
	if id=="chad":
		if f.has("chad_resolution"):NativeChapterTwo.say(g,[["Chad","Free hour still free? Love that for you. Genuinely.","warm"]]);return true
		g.dialogue([["Chad","Hey hey HEY! Chad. Networking. You're Jules, right? I feel like we've connected before. On LinkedOut.","warm"],["Imani","He has a ring light. In a garden. At night.","concern"],["Chad","Quick coffee chat? Fifteen minutes. Ten. Five! Your calendar says you've got a free hour. Let me just pop something in.","warm"],["Walt","It's free. That's the point of it.","neutral"]],g.resume_world,[g.option("Protect your free hour.",func() -> void:NativeChapterTwo.fight(g,"chad",[["Chad","Love the energy! Let's circle back. I'll pencil in a sync. And a sync about the sync.","warm"]])),g.option("Decline politely.",func() -> void:NativeChapterTwo.say(g,[["Jules","Not tonight, Chad. My calendar's allowed a gap.","warm"],["Chad","...Respect. Huge respect. Circling back never.","warm"]],{"absence_respected":true}))]);return true
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
		"mara":NativeChapterTwo.say(g,[["Mara","My ticket's mine again. I think I'll go home when the song ends. Or before. My call.","warm"]]);return true
		"eli":NativeChapterTwo.say(g,[["Eli","I'm keeping an ordinary seat open. I don't need every version of myself to sit in it.","warm"]]);return true
		"final_score":
			g.dialogue([["Imani","The score has no rests. It wants applause to last forever.","concern"],["Jules","What do you want to play?","neutral"],["Imani","A verse I can finish, or an instrumental that makes room for the room. My choice.","neutral"]],g.resume_world,[g.option("Imani chooses her rough verse.",func() -> void:NativeChapterTwo.say(g,[["Imani","I keep the missed breath. I write an ending after the verse.","warm"]],{"music_ready":true,"final_score":"honest"})),g.option("Imani chooses a quiet instrumental.",func() -> void:NativeChapterTwo.say(g,[["Imani","No audition for every listener. An instrumental, with a real final note.","warm"]],{"music_ready":true,"final_score":"instrumental"}))]);return true
		"rook":
			if f.has("rook_resolution"):NativeChapterTwo.say(g,[["Rook","One exit. One shift. Mags promised a cup, not a purpose for my entire life.","warm"]]);return true
			if not f.get("attendees_freed",false) or not f.get("music_ready",false):NativeChapterTwo.say(g,[["Rook","Guests in the cloakroom. Score in the pit. Give those people choices before asking me to trust an ending.","neutral"]]);return true
			NativeChapterTwo.fight(g,"rook",[["Rook","LAST CALL. No one leaves until everyone who could have arrived is accounted for.","concern"],["Jules","Keep every door open and lock every door. That's two jobs, Rook. Nobody can do both.","neutral"],["Rook","One key. One exit. If I could finish one shift, just one, I'd know it was allowed.","neutral"],["Walt","Then we finish it with you. You won't hold the room alone.","warm"]]);return true
		"val":
			if f.has("val_resolution"):NativeChapterTwo.say(g,[["Val","Off the clock. I'm going to ask people what they actually want next. Out loud. Terrifying.","warm"]]);return true
			NativeChapterTwo.fight(g,"val",[["VAL","WELCOME, CANDIDATES! VAL, VP OF TALENT ACQUISITION. THANK YOU FOR YOUR INTEREST IN... EVERYTHING.","concern"],["VAL","WE'RE HIRING EVERYONE YOU COULD EVER BE. EVERY FUTURE GETS A SEAT. NOBODY LEAVES THE PIPELINE.","concern"],["Jules","Those chairs are full of people who don't exist yet. The real ones are standing in the aisles.","concern"],["Imani","I've had auditions like this. You don't win them. You just stop letting them decide who you are.","neutral"],["Walt","Then we answer as ourselves, and see if anyone up there is listening.","warm"],["Pip","I have no resume. I am a glove. I feel strangely calm.","warm"]]);return true
		"dawn_conversation":
			NativeChapterTwo.say(g,[["Jules","The morning isn't asking who I will become. It's asking what we do next.","warm"],["Imani","Breakfast. Then I keep working on my recording, with the missed breath.","warm"],["Walt","I'll check the lantern handle. After cocoa. And I'll ask for the tool I need.","warm"],["Pip","I would like pancakes. I have no mouth. I would still like them.","warm"],["Jules","Let's take the morning path back to the UMC, thank Mags, then call home at the Broadway bus stop.","neutral"]],{"dawn_talk_read":true});return true
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
	if g.boss_id in ["cone","chad"]:g.battle.final_ready=true
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
	g.foe.sprite_frames=NativeCastArt.frames("val_small" if g.boss_stage==3 else "val");g.foe.play("idle_down");NativeCastArt.fit(g.foe,g.foe_height())
	var lines: Array=[]
	if g.boss_stage==1:lines=[["VAL","LET'S TALK FIVE YEARS OUT. JULES: NEVER MISSES A DEADLINE. IMANI: LOVED BY EVERY MANAGER. WALT: NEEDS NO TEAM.","concern"],["Jules","That's not a five-year plan. That's three people who never sleep.","neutral"],["Walt","Each of us can answer for ourselves on that one.","warm"]]
	elif g.boss_stage==2:lines=[["VAL","WE HAVE MORE CANDIDATES. MANY MORE. EVERY SEAT ON THIS PANEL IS BOOKED.","concern"],["Imani","Booked for people who haven't even applied. The real ones can't reach the door.","neutral"],["Walt","Then cancel one side. An empty chair is allowed.","warm"]]
	else:lines=[["Val","...Can I take the headset off? Thanks. There's no VP. It's just me. Val. The intern.","concern"],["Val","They gave me a target: every possible graduate. Saying 'we went another way' felt like failing all of them.","concern"],["Pip","You can stop interviewing. You're allowed to just ask a question.","warm"],["Jules","Then we have one for you, Val. When does your shift end?","neutral"]]
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
		var first: Array=[["Val","Okay. The pipeline's closed. Every candidate who doesn't exist yet can stop waiting in my lobby.","warm"],["Val","The ones who do exist can apply when they want. Or not. Huh. That's allowed.","warm"],["Imani","My recording stays mine. Nobody had to be erased for that.","warm"]] if ending=="release" else [["Val","One real role. Posted hours. A start date and an end date. Ugh. It's actually a good job.","warm"],["Walt","And people can say no to it. That's what makes the yes count.","neutral"]] if ending=="rewrite" else [["Jules","The panel's off. We'll fix the stage in daylight, not rebuild the machine.","concern"],["Val","You walked out of my interview. ...Honestly? Good for you. I've wanted to for months.","warm"]]
		first.append_array([["Pip","I just watched a VP turn out to be an intern. I have learned so much about careers tonight.","warm"],["Jules","Their jobs belong to them now. We agreed on that together.","neutral"],["Imani","And the booked chairs stop multiplying. The campus has room for morning.","warm"]])
		g.dialogue(first,func() -> void:f.dawn_started=true;f.aftermath_pending="";f.val_checkpoint="";g.enter_room("M07",Vector2(120,445),false);g.persist();g.resume_world());return
	var lines: Array=[["Rook","You held a small job with me. I can finish a shift without having to finish myself.","warm"],["Walt","Mags saved a cup. A cup, not a contract.","warm"],["Jules","The stage is open. Now VAL needs choices from the people it made.","neutral"]] if id=="rook" and peaceful else [["Rook","The key ring is bent. I can lend the stage key without becoming every locked door.","concern"],["Imani","We'll straighten it in daylight. For now, one exit is open.","neutral"]] if id=="rook" else [["Captain Lance","ONE MARKED LINE. THE OTHER CALLS ARE CANCELLED. ON YOUR LEFT, BUT ONLY ONCE.","warm"],["PELOTON","SHARE THE PATH! SHARE THE PATH! (WE PRACTICED.)","warm"]] if id=="cone" and peaceful else [["Jules","The paceline scattered. We left a repair note on the bike rack and a clear path.","neutral"]] if id=="cone" else [["Chad","One unbooked hour. No agenda. I genuinely don't know what to do with my hands.","warm"],["Imani","Sit down. That's the whole agenda.","warm"]] if peaceful else [["Walt","His ring light's cracked. Nobody has to be on all the time, Chad.","neutral"]]
	g.dialogue(lines,func() -> void:
		if id=="rook":f.balcony_open=true
		if id=="chad":f.absence_respected=true
		f.aftermath_pending="";g.persist();g.resume_world())
static func ending_menu(g: Node) -> void:
	var title: String="The End / "+str({"release":"every other future let go","rewrite":"one real offer, with hours","break":"you walked out of the interview"}.get(str(g.state.flags.get("ending","release")),"thanks for playing"))
	var options: Array=[g.option("Keep exploring the changed campus",func() -> void:g.ending_ticks=-1;g.resume_world()),g.option("Return to title",func() -> void:g.ending_ticks=-1;g.show_title())]
	if not g.state.flags.get("graduation_complete",false):options.insert(0,g.option("Epilogue / graduation day",func() -> void:g.ending_ticks=-1;NativeJakerson.graduation(g)))
	# A finished story closes on a card; the epilogue's own menu (before graduation) stays a plain list.
	g.ending_ticks=0 if g.state.flags.get("graduation_complete",false) else -1
	g.open_menu(g.Mode.MENU,title,options)
	if g.ending_ticks==0:g.input_lock=125
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
	return "Finish the interview / Val on the graduation stage"
