extends "res://scenes/qa_opening.gd"
func run(main: Node) -> bool:
	game=main;folder=OS.get_environment("AFTER_HOURS_QA")
	_log("START Chapter 2 exported ordinary input; no HP, inventory or story flag edits")
	await _choose("Continue");await _settle()
	if "--qa-map-only" in OS.get_cmdline_user_args():
		_assert(game.state.room=="N01" and game.state.flags.get("chapter2_complete",false),"Continue resumes the earned full Chapter 2 autosave")
		await _press("menu");await _choose("Campus map")
		_assert(int(game.mode)==13 and game.campus_map.selected==2,"Map selects current Norlin district")
		await _capture("09-norlin-map");await _press("move_down")
		_assert(game.campus_map.selected==3,"Map keyboard navigates to Engineering")
		var click:=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_LEFT;click.pressed=true;click.position=Vector2(150,324)
		game.get_viewport().push_input(click,true);await _frame();click=click.duplicate();click.pressed=false;game.get_viewport().push_input(click,true);await _frame()
		_assert(game.campus_map.rooms_mode and game.campus_map.room_buttons.size()==5,"Mouse Rooms view lists all five Engineering rooms")
		await _press("confirm");await _capture("10-engineering-doors");await _press("cancel");await _press("cancel")
		_assert(int(game.mode)==WORLD and not game.pause_context,"Map closes back to exploration")
		_log("FAIL" if failed else "PASS Chapter 2 map-only follow-up using earned unchanged save");_write_trace();return not failed
	_assert(game.state.room=="F06" and game.state.flags.get("chapter1_complete",false),"Continue imports the earned Chapter 1 completion save")
	await _door("norlin_route","N01");await _capture("01-norlin-steps")
	await _door("checkout","N02");await _object("nell");await _settle()
	_assert(game.state.flags.get("library_pass",false),"Nell grants library access through conversation")
	await _door("reading","N03");await _object("recording_choice");await _settle();await _choose("Imani keeps");await _settle()
	await _object("bookmark");await _settle();await _capture("02-reading-own-demo")
	await _door("checkout","N02");await _door("stacks","N04");await _object("stack_crank");await _settle();await _capture("03-shifted-stacks")
	await _object("errata");await _fight("errata")
	await _door("archive","N06");await _object("index");await _settle()
	_assert(not game.state.flags.has("index_resolution") and int(game.mode)==WORLD,"INDEX introduces source quest before combat")
	await _door("stacks","N04");await _door("garden","N05");await _object("rook");await _settle();await _capture("04-margin-garden")
	await _door("steps","N01");await _door("engineering","E01");await _object("rook");await _settle();await _capture("05-loading-court")
	await _door("workshop","E02");await _object("cal");await _settle();await _object("dev");await _settle()
	_assert(game.state.party[2].id=="walt","Cal and Dev remain engineering NPCs")
	await _door("test_floor","E03");await _door("model_stairs","E04");await _object("model_plan");await _settle();await _choose("Ask Cal and Dev");await _settle();await _capture("06-shared-model")
	await _door("test_floor","E03");await _object("eric");await _fight("eric")
	await _door("workshop","E02");await _object("dev");await _settle()
	_assert(game.state.flags.get("bridge_ready",false),"Post-battle shared work installs bridge")
	await _door("test_floor","E03");await _door("model_stairs","E04");await _door("control","E05");await _object("source_reel");await _settle();await _capture("07-source-reel")
	await _door("court_shortcut","E01");await _door("bridge_shortcut","N01");await _door("checkout","N02");await _door("stacks","N04");await _door("archive","N06")
	await _object("index");await _fight("index");await _door("playback","N07");await _object("playback");await _settle();await _capture("08-playback-twist")
	_assert(game.state.flags.get("chapter2_complete",false) and game.state.flags.get("aftermath_pending","")=="","Full source hook completes before chapter flag")
	await _door("steps","N01")
	await _press("menu");await _choose("Campus map");await _capture("09-chapter2-map");await _press("cancel");await _press("cancel")
	_release();_log("FAIL" if failed else "PASS Chapter 2 ordinary continuation through Norlin and Engineering")
	_write_trace();return not failed
func _object(id: String) -> void:
	if failed:return
	var object: Dictionary=_definition(id)
	var raw: Array=object.get("hit_rect",[-24,-30,48,40])
	var center:=Vector2(object.x,object.y)+Vector2(raw[0]+raw[2]/2.0,raw[1]+raw[3]/2.0)
	var screen: Vector2=game.world.get_global_transform_with_canvas()*center
	if not Rect2(10,64,620,246).has_point(screen):
		var path: PackedVector2Array=game.navigation.object_route(game.player.position,object)
		_assert(not path.is_empty(),"Keyboard approach for initially offscreen "+id)
		if failed:return
		await _walk(path[-1],8)
	await super._object(id)
func _fight(id: String) -> void:
	await _settle()
	var start: int=ticks
	while not failed and int(game.mode)!=RESULT:
		if ticks-start>6200:_assert(false,"Boss timeout "+id);break
		match int(game.mode):
			BATTLE:
				_release()
				if game.caption=="Review party plan":await _choose("Commit turn")
				elif str(game.caption).contains("Choose an action"):
					await _choose("CONNECT" if game.battle.party.slice(0,game.actor).all(func(m: Dictionary) -> bool:return int(m.hp)<=0) else "GUARD")
				elif str(game.caption).begins_with("Connect"):
					var released: bool=game.menu_options.any(func(c: Dictionary) -> bool:return str(c.label).begins_with("RELEASE"))
					await _choose("RELEASE" if released else "Keep one sentence" if id=="errata" else "Probe three" if id=="eric" else "Deliver one useful")
				else:_assert(false,"Unexpected battle menu "+str(game.caption))
			DODGE:
				if not pause_checked and int(game.pattern.clock)>=80:await _pause_defense()
				else:await _defend(id)
			_:
				_release();await _frame()
	_release()
	if failed:return
	_assert(game.battle.outcome=="peaceful",id+" real objective earns peaceful release")
	await _capture("boss-"+id+"-result");await _choose("Continue");await _settle()
func _defend(id: String) -> void:
	if game.pattern.get("engine","")=="box":
		await _defend_box(id);return
	var p: Dictionary=game.pattern
	var at:=Vector2(p.cursor.x,p.cursor.y)
	var dest:=Vector2(p.sentenceX,84) if id=="errata" else Vector2(58 if int(p.currentAnchor)==0 else 198,90) if id=="eric" else Vector2(p.returnX,96) if p.carryBookmark else Vector2(128,24)
	if id=="index" and p.bookmarkDelivered:dest=Vector2(128,p.safeLane)
	var delta: Vector2=dest-at
	_axis(Vector2(signf(delta.x) if absf(delta.x)>2 else 0,signf(delta.y) if absf(delta.y)>2 else 0))
	var confirm: bool=at.distance_to(dest)<15
	if confirm:_event("confirm",true)
	await _frame()
	if confirm:_event("confirm",false)
	var key: String=id+"-phase-"+str(p.phase)
	if not captures.has(key) and int(p.clock)>=180:captures[key]=true;await _capture("defense-"+key)
