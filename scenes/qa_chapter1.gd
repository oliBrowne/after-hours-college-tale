extends "res://scenes/qa_opening.gd"
func run(main: Node) -> bool:
	game=main;folder=OS.get_environment("AFTER_HOURS_QA")
	force_claim=false;fail_promise=false;retry_route=false;observe_claim=false
	_log("START Chapter 1 ordinary input; no HP, inventory or story flag edits")
	if "--qa-stage" in OS.get_cmdline_user_args():
		await _choose("Continue");await _settle()
		_assert(game.state.room=="F04" and game.state.flags.get("walt_joined",false),"Ordinary Continue resumes the unmodified audience-lawn autosave")
		await _stage_finish()
		return not failed
	if "--qa-farrand" in OS.get_cmdline_user_args():
		await _choose("Continue");await _settle()
		_assert(game.state.room=="F02" and game.state.flags.get("volunteers_released",false),"Ordinary Continue resumes the unmodified earlier-route autosave")
		await _farrand_finish()
		return not failed
	await _choose("Settings")
	if not game.state.settings.instant: await _choose("Instant dialogue:")
	await _choose("Back");await _capture("00-title")
	await _choose("Begin the evening");await _settle()
	if game.jakerson_ui:await _choose("I'll find my way")
	_assert(not game.state.flags.get("imani_joined",false) and not game.state.flags.get("walt_joined",false),"Solo opening")
	await _door("umc_path","U08");await _object("walt");await _settle()
	_assert(not game.state.flags.has("walt_resolution") and game.state.flags.get("walt_met",false),"Walt conversation before Imani cannot start a boss")
	await _door("terrace_path","U02");await _door("main_entrance","U03");await _door("clubroom","U04")
	await _object("imani");await _settle();await _choose("I can stay");await _settle()
	_assert(game.state.flags.get("mixer_returned",false) and not game.state.flags.get("imani_joined",false),"Mixer returned; Imani stays behind for sound check")
	await _object("flyer");await _settle()
	_assert(not game.state.flags.has("flyer_resolution") and int(game.mode)==WORLD,"First boss gate prevents early Flyerer")
	await _door("atrium","U03");await _quiet()
	_assert(game.state.flags.get("imani_joined",false) and not game.state.flags.get("walt_joined",false),"Imani joins in the atrium after the booth plays her voice")
	_assert(game.state.flags.get("jakerson_drop_party",false),"Jakerson drops in to explain party turns")
	await _door("terrace","U02");await _door("outdoor_return","U08")
	await _quiet()
	_assert(game.state.flags.get("jakerson_drop_lob",false),"Jakerson drops in before Walt's fight (gravity lesson)")
	await _object("walt");await _fight("walt")
	_assert(game.state.flags.get("walt_joined",false),"Walt joins through post-fight conversation")
	_assert(game.state.party[2].id=="walt","Final party slot is Walt")
	await _capture("01-walt-party")
	await _door("terrace_path","U02");await _door("main_entrance","U03");await _door("clubroom","U04")
	await _object("flyer");await _fight("flyer")
	await _door("atrium","U03");await _object("booth");await _settle();await _door("stairs","U05")
	await _object("cal");await _settle()
	_assert(game.state.flags.get("cal_key_received",false) and game.state.party[2].id=="walt","Cal gives key without replacing Walt")
	await _door("connection_stairs","U06");await _door("lost_property","U07")
	await _object("claim");await _fight("claim")
	_assert(game.state.flags.get("pip_joined",false),"Pip stays a companion after CLAIM")
	await _door("connection","U06");await _door("atrium","U05");await _door("atrium","U03")
	await _door("farrand_gate","F01");await _capture("02-farrand")
	# Open the persistent mouse map button, select a district and close through input.
	var click := InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_LEFT;click.pressed=true;click.position=game.overlay.map_button.get_global_rect().get_center()
	game.get_viewport().push_input(click, true);await _frame();click=click.duplicate();click.pressed=false;game.get_viewport().push_input(click, true);await _frame()
	_assert(int(game.mode)==13 and game.pause_context,"Native map pauses exploration")
	await _press("move_down");await _capture("03-map");await _press("cancel")
	_assert(int(game.mode)==WORLD and not game.pause_context,"Map returns to unchanged exploration")
	await _object("rook");await _settle();await _door("tent","F02")
	await _object("volunteers");await _settle();await _capture("04-volunteers")
	await _farrand_finish()
	return not failed
func _farrand_finish() -> void:
	await _door("cable","F01");await _door("food","F03");await _object("mags");await _settle();await _door("lawn","F04")
	await _stage_finish()
func _stage_finish() -> void:
	await _object("chip");await _settle();await _choose("Try the friendly challenge");await _fight("chip")
	_assert(game.state.flags.get("chip_resolution","")=="peaceful","Chip is the required Farrand boss")
	await _door("backstage","F05");await _object("consent");await _settle();await _choose("Imani chooses her honest");await _settle();await _capture("05-backstage-choice")
	await _door("mainstage","F06");await _object("encore");await _fight("encore")
	_assert(game.state.flags.get("chapter1_complete",false),"Chapter 1 ends after ENCORE")
	await _object("norlin_route");await _settle();await _capture("06-chapter1-complete")
	_assert(pause_checked,"New boss preserves defense pause/music freeze")
	_release();_log("FAIL" if failed else "PASS Chapter 1 input continuation through ENCORE" if "--qa-stage" in OS.get_cmdline_user_args() or "--qa-farrand" in OS.get_cmdline_user_args() else "PASS complete Chapter 1 input route")
	_write_trace()
func _fight(id: String) -> void:
	if id in ["flyer","claim"]:
		await super._fight(id);return
	await _settle()
	var start: int=ticks
	var force_walt: bool=id=="walt" and "--qa-force-walt" in OS.get_cmdline_user_args()
	while not failed and int(game.mode)!=RESULT:
		if ticks-start>6200: _assert(false,"Boss timeout "+id);break
		match int(game.mode):
			BATTLE:
				_release();_check_party_poses("Planning "+id)
				if game.caption=="Review party plan": await _choose("Commit turn")
				elif str(game.caption).contains("Choose an action"):
					if force_walt: await _choose("STRIKE")
					elif game.battle.party.slice(0,game.actor).all(func(m: Dictionary) -> bool:return int(m.hp)<=0): await _choose("CONNECT")
					else: await _choose("GUARD")
				elif str(game.caption).begins_with("Connect"):
					var release: bool=game.menu_options.any(func(c: Dictionary) -> bool: return str(c.label).begins_with("RELEASE"))
					if release: await _choose("RELEASE")
					else: await _choose("Keep the light" if id=="walt" else "Follow three" if id=="chip" else "Answer two")
				else: _assert(false,"Unexpected menu "+str(game.caption))
			DODGE:
				if not pause_checked and int(game.pattern.clock)>=80: await _pause_defense()
				else: await _defend(id)
			TIMING:
				if game.timing_ticks>=27: await _press()
				else: await _frame()
			_:
				_release();await _frame()
	_release()
	if failed:return
	_assert(game.battle.outcome==("forceful" if force_walt else "peaceful"),id+" expected outcome")
	if id=="walt": _assert(not game.state.flags.get("walt_joined",false),"Recruitment waits for Walt's dialogue")
	await _capture("boss-"+id+"-result")
	await _choose("Continue");await _settle()
func _defend(id: String) -> void:
	if id in ["flyer","claim"]:
		await super._defend(id);return
	if game.pattern.get("engine","")=="box":
		await _defend_box(id);return
	var p: Dictionary=game.pattern
	var cursor:=Vector2(p.cursor.x,p.cursor.y)
	var dest:=Vector2(128,62) if id=="walt" else Vector2(p.safeColumn,92)
	var delta: Vector2=dest-cursor
	if id=="chip":
		_axis(Vector2(signf(delta.x) if absf(delta.x)>4 and int(p.lastInputX)==0 else 0,0))
	else:
		_axis(Vector2(signf(delta.x) if absf(delta.x)>2 else 0,signf(delta.y) if absf(delta.y)>2 else 0))
	var confirm: bool=id=="walt" and cursor.distance_to(dest)<20 and int(p.clock)%28==0 or id=="encore" and p.cueOpen and cursor.distance_to(dest)<14
	if confirm:_event("confirm",true)
	await _frame()
	if confirm:_event("confirm",false)
	var key: String=id+"-phase-"+str(p.phase)
	if not captures.has(key) and int(p.clock)>=180:
		captures[key]=true;await _capture("defense-"+key)
