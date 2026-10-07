extends SceneTree
var checks: int=0
var failures: int=0
func check(ok: bool, message: String) -> void:
	checks+=1
	if not ok:failures+=1;print("FAIL ",message)
func drive(p: Dictionary, promised: bool=true, assist: float=1.0, slow: bool=false) -> Dictionary:
	var steps: int=0
	while not p.done and steps<2000:
		var dest:=Vector2(p.sentenceX,84) if p.encounterId=="errata" else Vector2(58 if int(p.currentAnchor)==0 else 198,90) if p.encounterId=="eric" else Vector2(p.returnX,96) if p.carryBookmark else Vector2(128,24)
		if p.encounterId=="autocomplete" and p.bookmarkDelivered:dest=Vector2(128,p.safeLane)
		var at:=Vector2(p.cursor.x,p.cursor.y)
		p=NativeCampusEncounter.step(p,(dest-at).normalized() if dest.distance_to(at)>2 else Vector2.ZERO,false,assist,slow,promised,dest.distance_to(at)<15)
		steps+=1
	return p
func drain(g: Node) -> void:
	for i: int in range(40):
		if g.mode!=g.Mode.DIALOGUE:break
		g.reveal=10000;g.advance_dialogue()
func _initialize() -> void:call_deferred("run")
func run() -> void:
	for id: String in NativeChapterTwo.BOSSES:
		for phase: int in range(3):
			for assisted: bool in [false,true]:
				var p: Dictionary=drive(NativeCampusEncounter.create(id,123,phase,17),true,0.7 if assisted else 1.0,assisted)
				check(p.done and p.promiseComplete,id+" actual objective phase "+str(phase)+" assist "+str(assisted))
			var miss: Dictionary=NativeCampusEncounter.create(id,123,phase,17)
			for i: int in range(1000):
				miss=NativeCampusEncounter.step(miss,Vector2.ZERO,false,1.0,false,true,false)
				if miss.done:break
			check(not miss.promiseComplete,id+" cannot win promise by waiting")
		var unpromised: Dictionary=drive(NativeCampusEncounter.create(id,123,0,0),false)
		check(not unpromised.promiseComplete,id+" objectives require a real promise")
	# INDEX became AUTOCOMPLETE: an old save keeps its outcome and its pending aftermath hook.
	var old: Dictionary=NativeState.fresh()
	old.flags={"chapter1_complete":true,"index_resolution":"peaceful","index_seen":true,"aftermath_pending":"index"}
	var moved: Dictionary=NativeCampaign.migrate(old)
	check(moved.flags.autocomplete_resolution=="peaceful" and moved.flags.autocomplete_seen and moved.flags.aftermath_pending=="autocomplete","Old INDEX save migrates its outcome and pending aftermath to AUTOCOMPLETE")
	check(old.flags.aftermath_pending=="index" and NativeSaveService.validate_state(moved),"AUTOCOMPLETE migration is pure and the result validates")
	var earned: Dictionary=moved.duplicate(true);earned.flags.autocomplete_resolution="forceful"
	check(NativeCampaign.migrate(earned).flags.autocomplete_resolution=="forceful","Migration never overwrites an AUTOCOMPLETE outcome")
	for id: String in NativeChapterTwo.BOSSES:check(NativeBossIntro.has_card(id) and not NativeBossIntro.answer(id).is_empty() and DodgeBox.handles(id),id+" has an intro card, a CONNECT answer and a DodgeBox script")
	# ERRATA became Gwen the Red: the id stays, the card, voice and drawn art are hers.
	check(NativeBossIntro.CARDS.errata[1]=="GWEN THE RED" and NativeBossIntro.CARDS.errata[2]=="SEE ME AFTER CLASS." and NativeBossIntro.answer("errata")[0]=="Gwen the Red","Gwen the Red has the card name, her catchphrase and her CONNECT answer")
	check(NativeBossArt.art_id("errata")=="ta" and NativeBossArt.art_id("eric")=="eric" and ResourceLoader.exists("res://assets/art/entrance/"+NativeBossArt.art_id("errata")+".png"),"The errata card looks up Gwen's entrance pose by her art id")
	check(NativeCastArt.body("errata",0)==NativeBossArt.body("ta",0) and NativeCastArt.frames("errata")==NativeBossArt.frames("ta") and NativeCastArt.source_portrait("Gwen the Red",1)==NativeBossArt.portrait("ta",1) and is_equal_approx(NativeCastArt.world_height("errata"),NativeBossArt.world_height("ta")),"The errata id and the speaker Gwen the Red route to the ta sheet")
	var rooms: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://content/rooms.json"))
	for shifted: bool in [false,true]:
		for room: Dictionary in rooms.values():NativeCampusWorld.prepare(room,{"stacks_shifted":shifted})
		for id: String in rooms:
			if not id.begins_with("N") and not id.begins_with("E"):continue
			var nav:=NativeRoomNavigation.new();nav.configure(rooms[id])
			for object: Dictionary in rooms[id].objects:
				check(not nav.object_route(nav.entry,object).is_empty(),id+"/"+str(object.id)+" reachable shifted="+str(shifted))
				if object.kind=="door":
					var dest:=NativeRoomNavigation.new();dest.configure(rooms[object.to])
					check(dest.clear(Vector2(object.spawn[0],object.spawn[1])),id+" doorway safe in both shelf positions")
	var g: Node=load("res://scenes/main.tscn").instantiate();root.add_child(g)
	g.qa=true;g.saves=NativeSaveService.new("user://chapter2-focused/saves");g.preferences_path="user://chapter2-focused/preferences.json"
	g.state.flags={"imani_joined":true,"walt_joined":true,"chapter1_complete":true,"claim_resolution":"peaceful"}
	g.enter_room("N06",Vector2(120,400),false)
	NativeChapterTwo.handle(g,{"id":"autocomplete"});drain(g)
	check(not g.state.flags.has("autocomplete_resolution") and g.mode==g.Mode.WORLD,"AUTOCOMPLETE source gate prevents early battle")
	g.boss_id="autocomplete";g.battle={"openness":100,"campus_promise":false};g.boss_stage=2
	check(not g.release_ready(),"AUTOCOMPLETE 100 Open and final phase cannot replace the accepted suggestion")
	g.battle.campus_promise=true;g.boss_stage=1;check(not g.release_ready(),"AUTOCOMPLETE requires final verse objective")
	g.boss_stage=2;check(g.release_ready(),"AUTOCOMPLETE real final suggestion plus openness permits release")
	g.enter_room("E03",Vector2(110,430),false);NativeChapterTwo.handle(g,{"id":"eric"});drain(g)
	check(g.mode==g.Mode.WORLD and not g.state.flags.has("eric_resolution"),"Loader gate requires revised model")
	for outcome: String in ["peaceful","forceful"]:
		g.state.flags.eric_resolution=outcome;g.state.flags.erase("bridge_ready")
		g.enter_room("E02",Vector2(120,410),false);NativeChapterTwo.handle(g,{"id":"dev"});drain(g)
		check(g.state.flags.bridge_ready and g.state.party[2].id=="walt",outcome+" installs bridge with Dev without replacing Walt")
	for id: String in NativeChapterTwo.AFTERMATHS:
		g.state.flags.merge({"aftermath_pending":id,"source_reel":true,"autocomplete_resolution":"peaceful"},true)
		if id in NativeChapterTwo.BOSSES:g.state.flags[id+"_resolution"]="peaceful"
		g.state.flags.erase("chapter2_complete");g.state.flags.erase("playback_heard")
		g.enter_room("N07" if id=="playback" else "E05" if id=="source_reel" else "N06",Vector2(120,410),false)
		check(g.persist(),id+" interruption checkpoint writes")
		var loaded: Dictionary=g.saves.load_slot("auto")
		check(loaded.has("state") and loaded.state.flags.aftermath_pending==id,id+" pending hook survives actual disk read")
		g.restore_state(loaded.state)
		check(g.mode==g.Mode.DIALOGUE and g.state.flags.aftermath_pending==id,id+" normal restore replays hook before clearing")
		drain(g)
		check(g.state.flags.aftermath_pending=="",id+" hook clears after full dialogue")
		if id=="playback":check(g.state.flags.chapter2_complete and g.state.flags.playback_heard,"Playback marks chapter only after twist finishes")
	# Nell's walking red pencil comes home once Gwen the Red is settled, and the keeper line names her.
	g.state.flags.merge({"library_pass":true},true);g.state.flags.erase("errata_resolution")
	g.enter_room("N02",Vector2(120,400),false);NativeChapterTwo.handle(g,{"id":"nell"})
	check(not str(g.dialogue_lines[0][1]).contains("red pencil"),"Nell asks nothing about the pencil before Gwen the Red is settled");drain(g)
	g.state.flags.errata_resolution="peaceful";NativeChapterTwo.handle(g,{"id":"nell"})
	check(g.mode==g.Mode.DIALOGUE and str(g.dialogue_lines[0][0])=="Nell" and str(g.dialogue_lines[0][1]).contains("red pencil"),"Nell gets her red pencil back once Gwen the Red is settled");drain(g)
	NativeChapterTwo.handle(g,{"id":"errata"})
	check(g.mode==g.Mode.DIALOGUE and str(g.dialogue_lines[0][0])=="Gwen the Red","The settled errata object speaks as Gwen the Red");drain(g)
	g.state.room="E04";g.state.x=900;g.state.y=470
	check(NativeSaveService.validate_state(g.state),"960-wide Chapter 2 room saves validate")
	g.state.x=INF;check(not NativeSaveService.validate_state(g.state),"Nonfinite position rejected")
	g.audio.shutdown();g.dialogue_callback=Callable();g.menu_options.clear();g.pause_options.clear();g.dialogue_choices.clear();g.queue_free();await process_frame
	print("Chapter 2 focused checks: ",checks,", failures: ",failures);quit(0 if failures==0 else 1)
