class_name NativeChapterThree
extends RefCounted
static func handle(g: Node, object: Dictionary) -> bool:
	if not str(g.state.room).begins_with("O") or object.get("kind","")=="door":return false
	var f: Dictionary=g.state.flags
	match str(object.id):
		"notice_limits":
			NativeChapterTwo.say(g,[["Loudspeaker","JULES: NEVER DISAPPOINT. IMANI: KEEP EVERY AUDIENCE. WALT: NEED NOBODY.","concern"],["Jules","Those aren't office hours. They're sentences with no stopping point.","concern"],["Imani","Nobody asked whether I wanted every audience.","neutral"],["Walt","And needing someone is different from handing them my life.","neutral"],["Jules","The first recording is in the empty office. Let's find who wrote this job description.","neutral"]],{"notice_limits":true});return true
		"origin_directory":
			if f.get("booth_origin",false):NativeChapterTwo.say(g,[["Jules","Someone gave Val a hiring target: every possible graduate. The pledge booth multiplied it by every imagined future.","neutral"],["Imani","Then the interview needs an end time. And a door.","neutral"]]);return true
			NativeChapterTwo.say(g,[["Directory","TALENT PIPELINE / VAL. RECRUIT EVERYONE THEY COULD BECOME. DO NOT CLOSE UNTIL ALL ARE HIRED.","concern"],["Jules","A hiring target with no end date. Somebody handed Val a job that could never finish.","concern"],["Imani","The booth asked for promises, and every answer became another candidate who had to show up.","neutral"],["Walt","Some things held those promises long enough to wake up. The glove. The catalogue. The marshal.","neutral"],["Pip","...If we stop the source, what happens to me?","concern"],["Jules","We ask you first. Nobody decides that for you.","warm"],["Imani","Todd's desk is next door and Rook's outside. Then Macky.","neutral"]],{"booth_origin":true});return true
		"family_phone":
			NativeChapterTwo.say(g,[["Jules","Mom's message: You don't have to bring me a successful evening. Just tell me where you are.","concern"],["Jules","I can write where I am. Not a promise to finish every problem before calling.","neutral"]],{"family_message_read":true});return true
		"finite_plan":
			g.dialogue([["Todd Saliman","This desk exists for one very real question: what exactly are you agreeing to?","neutral"],["Imani","One gathering. Each person can leave. Nobody signs for somebody else.","neutral"],["Walt","And work gets named, shared and stopped. Not passed to whoever looks most available.","neutral"]],g.resume_world,[g.option("One gathering / one closing time.",func() -> void:NativeChapterTwo.say(g,[["Jules","One gathering that ends. Attendance is a choice.","warm"]],{"finite_plan":"one-gathering"})),g.option("Shared duties / the right to decline.",func() -> void:NativeChapterTwo.say(g,[["Jules","Named tasks. Shared responsibility. A right to say no.","warm"]],{"finite_plan":"shared-duties"}))]);return true
		"todd":
			if not f.get("booth_origin",false):
				NativeChapterTwo.say(g,[["Todd Saliman","Read the original directory in the empty office first. Then we can talk about limits.","neutral"]]);return true
			if not f.has("finite_plan"):
				NativeChapterTwo.say(g,[["Todd Saliman","Good, you've read it. Now the consent form on the desk: choose your limits before we talk.","neutral"]]);return true
			if f.has("todd_resolution"):
				if not f.get("chapter3_complete",false):
					f.aftermath_pending="todd";g.persist();aftermath(g)
				else:NativeChapterTwo.say(g,[["Todd Saliman","The finite plan is accepted. Make space for people to answer for themselves.","warm"]])
				return true
			NativeChapterTwo.fight(g,"todd",[["Todd Saliman","A plan with limits. Let's test whether it survives an audit.","neutral"],["Imani","The consent boxes are choices, not a promise to answer everything.","neutral"],["Todd Saliman","Confirm at both outlined boxes. When RED AUDIT appears, hold still. Three verses; then submit the finite plan.","neutral"],["Jules","One useful rehearsal. We can also clear the machinery and repair it afterwards.","neutral"]]);return true
		"rook":
			if not f.get("booth_origin",false):NativeChapterTwo.say(g,[["Rook","The directory is inside. I'd recommend not reading it. Which has never made anyone less curious.","neutral"],["Jules","You know what is on that reel.","concern"],["Rook","I heard the instruction when they switched it on. That's what I know.","concern"]]);return true
			if f.get("rook_confessed",false):NativeChapterTwo.say(g,[["Rook","Macky. I still have keys. I just don't know which job they belong to anymore.","concern"]]);return true
			NativeChapterTwo.say(g,[["Rook","I closed the Engineering door. I knew the reel would lead here.","concern"],["Walt","You thought stopping the ceremony would stop you.","neutral"],["Rook","I am folded paper with a job. When the job ends, does the paper stay a person?","concern"],["Pip","I don't need somebody to lose me forever. I can hold a door because I choose to.","warm"],["Imani","ENCORE can host a show that ends. INDEX can keep a stopping place. Your purpose can change too.","neutral"],["Rook","You make that sound possible. I still don't trust an ending.","concern"],["Jules","Then come to Macky and hear the choices. We won't write your answer for you.","neutral"]],{"rook_confessed":true});return true
		"courtyard_lamp", "cabinet_lamp":
			for member: Dictionary in g.state.party:member.hp=member.max
			g.persist();g.audio.effect("save")
			g.open_menu(g.Mode.MENU,"Rested / choose a save slot",[g.option("Save slot 1",func() -> void:g.manual_save("slot1")),g.option("Save slot 2",func() -> void:g.manual_save("slot2")),g.option("Save slot 3",func() -> void:g.manual_save("slot3")),g.option("Back",g.resume_world)]);return true
	return false
static func aftermath(g: Node) -> void:
	var f: Dictionary=g.state.flags
	g.boss_id="";g.enter_room(str(g.state.room),Vector2(g.state.x,g.state.y),false)
	var lines: Array=[["Todd Saliman","Two explicit choices. One finite plan. Approved for the people who actually chose it.","warm"],["Imani","And room for a different answer. We're keeping that.","warm"]] if f.get("todd_resolution","")=="peaceful" else [["Todd Saliman","The stamp rig is damaged. I'll file the limits by hand and arrange repairs.","concern"],["Walt","The people still get a choice. That's the part we keep.","neutral"]]
	lines.append(["Jules","Rook is in the courtyard. We need to speak with him about what happens when this job ends, then follow the procession to Macky.","neutral"])
	g.dialogue(lines,func() -> void:f.chapter3_complete=true;f.aftermath_pending="";g.persist();g.resume_world())
static func objective(s: Dictionary) -> String:
	var f: Dictionary=s.flags
	if not f.get("notice_limits",false):return "Read the changing notices / Old Main notice hall"
	if not f.get("booth_origin",false):return "Find VAL's first instruction / Old Main empty office"
	if not f.has("finite_plan"):return "Choose explicit limits / consent form in the cabinet room"
	if not f.get("chapter3_complete",false):return "Submit one finite plan / Todd at the cabinet desk"
	if not f.get("rook_confessed",false):return "Ask Rook what he fears / Old Main courtyard"
	return "Follow the procession / Macky comes next"
