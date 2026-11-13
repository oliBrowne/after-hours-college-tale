extends "res://scenes/qa_wander.gd"
## Actual-input route for the Intern Insider app: open it from the pause menu, read a posting, apply,
## and check the Buff Bucks bonus and the story-gated postings. --qa-intern runs it.

func run(main: Node) -> bool:
	game=main;folder=OS.get_environment("AFTER_HOURS_QA")
	force_claim=false;fail_promise=false;retry_route=false;observe_claim=false
	_log("START Fountain Court hub, ordinary input")
	await _choose("Settings")
	if not game.state.settings.instant: await _choose("Instant dialogue:")
	await _choose("Back");await _choose("Begin the evening")
	for _i: int in range(60):
		if int(game.mode)!=INTRO:break
		await _press("cancel")
	await _quiet()
	if game.jakerson_ui:await _choose("I'll find my way")
	_assert(int(game.mode)==WORLD,"Skipping the intro cards lands in the world")
	var f: Dictionary=game.state.flags
	f.imani_joined=true;f.buff_bucks="0"
	game.open_pause();await _settle()
	await _choose("Intern Insider");await _settle()
	_assert(int(game.mode)==MENU and str(game.caption).begins_with("Intern Insider"),"The board opens: "+str(game.caption))
	await _capture("01-board")
	await _choose("Sound Crew Intern");await _settle()
	_assert(str(game.caption).begins_with("Intern Insider\n"),"A posting opens as a card")
	await _capture("02-posting")
	await _choose("Easy Apply");await _settle()
	_assert(InternInsider.applied_id(f,"sound") and NativeRandomFights.bucks(f)==10,"Easy Apply pays 10 Buff Bucks once: "+str(f.get("buff_bucks")))
	_assert(InternInsider.status(f,InternInsider.posting("sound"))=="Offer received","Imani joined, so the sound offer lands")
	await _capture("03-applied")
	f.visited_P01=true;f.chapter3_complete=true
	await _choose("Back to postings");await _settle()
	_assert(InternInsider.listed(f).size()==3,"The Pearl Street visit and chapter 3 list two more postings")
	await _capture("04-more")
	_log("PASS Intern Insider route")
	return true
