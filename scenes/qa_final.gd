extends "res://scenes/qa_chapter3.gd"
var ending: String="release"
func run(main: Node) -> bool:
	game=main;folder=OS.get_environment("AFTER_HOURS_QA")
	ending="rewrite" if "--qa-ending-rewrite" in OS.get_cmdline_user_args() else "break" if "--qa-ending-break" in OS.get_cmdline_user_args() else "release"
	_log("START finale exported ordinary inputs, no HP/resources/flags edited, ending="+ending)
	await _choose("Continue");await _settle()
	if not str(game.state.flags.get("val_checkpoint","")).is_empty():
		_assert(game.boss_id=="val" and game.boss_stage==3,"Continue restores unchanged earned VAL phase 4 checkpoint")
	elif game.state.room=="M05" and game.state.flags.get("rook_resolution","")=="peaceful":
		_assert(game.state.flags.get("attendees_freed",false) and game.state.flags.get("music_ready",false),"Continue preserves earned preparation choices and full Rook aftermath")
		await _door("stage","M06");await _object("stage_lamp");await _choose("Back");await _capture("05-graduation-stage")
		await _object("val");await _settle()
	else:
		_assert(game.state.room=="O01" and game.state.flags.get("chapter3_complete",false) and game.state.flags.get("rook_confessed",false),"Continue preserves earned Old Main ending")
		await _door("macky_route","M01");await _capture("01-macky-towers")
		await _object("mags");await _settle();await _door("lobby","M02");await _object("lobby_directory");await _settle()
		await _door("cloakroom","M03");await _object("attendees");await _settle();await _choose("Guests can leave");await _settle();await _capture("02-guests-choose")
		await _object("mara");await _settle();await _object("eli");await _settle();await _door("lobby","M02");await _door("pit","M04")
		await _object("final_score");await _settle();await _choose("Imani chooses her rough");await _settle();await _capture("03-finite-score")
		_assert(game.state.flags.get("attendees_freed",false) and game.state.flags.get("music_ready",false),"Two preparation branches completed through real choices")
		await _door("balcony_lift","M05");await _object("balcony_lamp");await _choose("Back");await _object("rook");await _fight("rook")
		_assert(game.state.flags.get("rook_resolution","")=="peaceful" and game.state.flags.get("balcony_open",false),"Rook's full ordered shift opens shortcut and stage")
		await _capture("04-last-call-ended");await _door("stage","M06");await _object("stage_lamp");await _choose("Back");await _capture("05-graduation-stage")
		await _object("val");await _settle()
	await _fight("val")
	_assert(game.state.room=="M07" and game.state.flags.get("dawn_started",false) and game.state.flags.get("ending","")==ending,"Explicit ending consequence opens playable dawn")
	await _capture("06-playable-dawn");await _object("dawn_conversation");await _settle();await _door("umc_return","U03");await _object("booth");await _settle()
	await _door("terrace","U02");await _object("mags");await _settle();await _capture("07-morning-thanks");await _door("outdoor_return","U08");await _door("broadway_return","U01")
	await _object("bus");await _settle();await _choose("Jules: I am here");await _settle()
	_assert(game.state.flags.get("dawn_complete",false) and game.state.flags.get("aftermath_pending","")=="","Full family response concludes the evening")
	if game.rooms.has("G01") and game.rooms.has("G02"):
		_assert(game.state.room=="G01" and game.state.flags.get("graduation_day",false) and int(game.mode)==WORLD,"Graduation cutscene on Folsom Field follows the dawn")
		await _capture("08-graduation");await _door("courts_path","G02");await _object("jakerson_match");await _settle()
	else:
		_assert(game.state.room=="M06" and game.state.flags.get("graduation_day",false),"Graduation cutscene on Macky's stage follows the dawn")
		await _capture("08-graduation")
	_assert(str(game.caption).begins_with("Jakerson"),"Jakerson offers a last friendly match")
	await _choose("One last spar");await _fight("jakerson_final")
	_assert(game.state.flags.get("graduation_complete",false) and game.state.flags.get("jakerson_final_resolution","")=="peaceful","Friendly graduation match ends peacefully")
	await _capture("08-home-ending")
	await _choose("Keep exploring");await _press("menu");await _choose("Campus map");await _capture("09-complete-map");await _press("cancel");await _press("cancel")
	_assert(int(game.mode)==WORLD and game.state.party[2].id=="walt","Finished game remains playable with chosen party")
	_release();_log("FAIL" if failed else "PASS finale ordinary inputs / "+ending+" / playable dawn and home return");_write_trace();return not failed
func _fight(id: String) -> void:
	await _settle()
	var start: int=ticks
	while not failed and int(game.mode)!=RESULT:
		if ticks-start>9000:_assert(false,"Final boss timeout "+id);break
		match int(game.mode):
			BATTLE:
				_release()
				if id=="val" and game.boss_stage==3 and not captures.has("phase4-checkpoint"):
					captures["phase4-checkpoint"]=true
					var source: String=ProjectSettings.globalize_path(game.saves.base_path.path_join("auto.json"))
					_assert(DirAccess.copy_absolute(source,folder.path_join("earned-val-phase4.json"))==OK,"Archive byte-identical earned final phase checkpoint for alternative endings")
				if game.caption=="Review party plan":await _choose("Commit turn")
				elif str(game.caption).contains("Choose an action"):
					await _choose("CONNECT" if game.actor==_first_conscious() or id=="val" and game.boss_stage==1 else "GUARD")
				elif str(game.caption).begins_with("Connect"):
					var available: bool=game.menu_options.any(func(c: Dictionary) -> bool:return str(c.label).begins_with("RELEASE"))
					if available:
						await _capture("ending-choice-"+id);await _choose(ending.to_upper() if id=="val" else "RELEASE")
					elif id=="rook":await _choose("Carry one" if game.boss_stage==0 else "REVISE / keep west")
					elif id=="jakerson_final":await _choose("Ask what" if int(game.battle.turn)==0 else "Sign three")
					else:await _choose("One return" if game.boss_stage==0 else str(game.battle.party[game.actor].id).capitalize()+":" if game.boss_stage==1 else "REVISE / unreserve the left" if game.boss_stage==2 else "Answer two")
				else:_assert(false,"Unexpected final menu "+str(game.caption))
			DODGE:
				if not pause_checked and int(game.pattern.clock)>=80:await _pause_defense()
				else:await _defend(id)
			DIALOGUE:await _settle()
			_:
				_release();await _frame()
	_release()
	if failed:return
	_assert(game.battle.outcome==("forceful" if id=="val" and ending=="break" else "peaceful"),id+" actual objectives earn chosen resolution")
	await _capture("boss-"+id+"-result");await _choose("Continue");await _settle()
func _defend(id: String) -> void:
	if game.pattern.get("engine","")=="box":
		await _defend_box(id);return
	var p: Dictionary=game.pattern;var at:=Vector2(p.cursor.x,p.cursor.y);var dest:=Vector2(128,62)
	if id=="rook":dest=Vector2(60,24) if int(p.phase)==0 and not p.keyHeld else Vector2(196,96) if int(p.phase)==0 else Vector2(p.chosenExit,70) if int(p.phase)==1 else Vector2(128,84)
	else:dest=[Vector2(128,24),Vector2(208,96),Vector2(48,96)][mini(2,int(p.valTask))] if int(p.phase)==0 else Vector2(p.openColumn,84) if int(p.phase)==2 else Vector2(128,62)
	if id=="val" and int(p.phase)==0 and int(p.valTask)>=3:dest=Vector2(200,p.safeLane)
	var d: Vector2=dest-at;_axis(Vector2(signf(d.x) if absf(d.x)>2 else 0,signf(d.y) if absf(d.y)>2 else 0))
	var confirm: bool=at.distance_to(dest)<15
	if confirm:_event("confirm",true)
	await _frame()
	if confirm:_event("confirm",false)
	var key: String=id+"-phase-"+str(p.phase)
	if not captures.has(key) and int(p.clock)>=180:captures[key]=true;await _capture("defense-"+key)
