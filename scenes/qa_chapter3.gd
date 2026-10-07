extends "res://scenes/qa_chapter2.gd"
func run(main: Node) -> bool:
	game=main;folder=OS.get_environment("AFTER_HOURS_QA")
	_log("START Chapter 3 normal continuation from earned Chapter 2 save; no HP/resources/flags injected")
	await _choose("Continue");await _settle()
	_assert(game.state.room=="N01" and game.state.flags.get("chapter2_complete",false),"Continue preserves the earned Chapter 2 ending")
	await _door("oldmain_route","O01");await _capture("01-oldmain-courtyard")
	await _object("rook");await _settle();_assert(not game.state.flags.get("rook_confessed",false),"Rook waits for the real directory before his confession")
	await _door("notice_hall","O02");await _object("notice_limits");await _settle();await _capture("02-personal-notices")
	await _door("office","O03");await _object("family_phone");await _settle();await _object("origin_directory");await _settle();await _capture("03-first-purpose")
	_assert(game.state.flags.get("booth_origin",false),"VAL origin read through full dialogue")
	await _door("cabinet_service","O04");await _object("todd");await _settle()
	_assert(int(game.mode)==WORLD and not game.state.flags.has("todd_resolution"),"Todd requires an explicit finite-plan choice")
	await _object("finite_plan");await _settle();await _choose("One gathering");await _settle()
	await _object("todd");await _fight("todd")
	_assert(game.state.flags.get("chapter3_complete",false) and game.state.flags.get("aftermath_pending","")=="","Todd's full aftermath completes Chapter 3")
	await _door("hall","O02");await _door("courtyard","O01");await _object("rook");await _settle();await _capture("04-rook-confession")
	_assert(game.state.flags.get("rook_confessed",false),"Rook admits witnessed knowledge and fear through conversation")
	await _press("menu");await _choose("Campus map");await _capture("05-oldmain-map");await _press("cancel");await _press("cancel")
	_assert(game.state.party[2].id=="walt","Party remains Jules, Imani and Walt")
	_release();_log("FAIL" if failed else "PASS Chapter 3 normal continuation through Old Main/Todd and Rook confession");_write_trace();return not failed
## The promise is carried by whoever is still standing, so a downed Jules does not stall the route.
func _first_conscious() -> int:
	for i: int in game.battle.party.size():
		if int(game.battle.party[i].hp) > 0: return i
	return 0
func _fight(id: String) -> void:
	await _settle()
	var start: int=ticks
	while not failed and int(game.mode)!=RESULT:
		if ticks-start>6200:_assert(false,"Todd fight timeout");break
		match int(game.mode):
			BATTLE:
				_release()
				if game.caption=="Review party plan":await _choose("Commit turn")
				elif str(game.caption).contains("Choose an action"):await _choose("CONNECT" if game.actor==_first_conscious() else "GUARD")
				elif str(game.caption).begins_with("Connect"):
					var released: bool=game.menu_options.any(func(c: Dictionary) -> bool:return str(c.label).begins_with("RELEASE"))
					await _choose("RELEASE" if released else "Sign two")
				else:_assert(false,"Unexpected Todd menu "+str(game.caption))
			DODGE:
				if not pause_checked and int(game.pattern.clock)>=80:await _pause_defense()
				else:await _defend(id)
			_:
				_release();await _frame()
	_release()
	if failed:return
	_assert(game.battle.outcome=="peaceful" and game.boss_stage==2,"Todd final audit earns actual peaceful submission")
	await _capture("boss-todd-result");await _choose("Continue");await _settle()
func _defend(id: String) -> void:
	if game.pattern.get("engine","")=="box":
		await _defend_box(id);return
	var p: Dictionary=game.pattern
	var at:=Vector2(p.cursor.x,p.cursor.y)
	var dest:=Vector2(128,60)
	for marker: Dictionary in p.markers:
		if not marker.collected:dest=Vector2(marker.x,marker.y);break
	var relative: int=maxi(0,int(p.clock)-int(p.leadIn))%180
	var still: bool=relative>=89 and relative<150
	var delta: Vector2=dest-at
	_axis(Vector2.ZERO if still else Vector2(signf(delta.x) if absf(delta.x)>2 else 0,signf(delta.y) if absf(delta.y)>2 else 0))
	var confirm: bool=at.distance_to(dest)<12
	if confirm:_event("confirm",true)
	await _frame()
	if confirm:_event("confirm",false)
	var key: String="todd-phase-"+str(p.phase)
	if not captures.has(key) and int(p.clock)>=180:captures[key]=true;await _capture("defense-"+key)
