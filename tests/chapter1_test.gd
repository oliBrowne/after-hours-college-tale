extends SceneTree
var checks: int=0
var failures: int=0
func check(ok: bool, title: String) -> void:
	checks+=1
	if not ok:failures+=1;print("FAIL ",title)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var old: Dictionary=NativeState.fresh()
	old.party[2]={"id":"cal","hp":66,"max":92,"power":12,"defence":3}
	old.flags={"cal_joined":true,"imani_joined":true,"claim_resolution":"peaceful","aftermath_pending":"claim"}
	check(NativeSaveService.validate_state(old),"Cal-era portable save still validates")
	var migrated: Dictionary=NativeCampaign.migrate(old)
	check(migrated.party[2].id=="walt" and migrated.flags.cal_key_received,"Migration replaces slot but keeps key story")
	check(not migrated.flags.get("walt_joined",false) and migrated.flags.walt_intro_pending,"Cal flag cannot recruit Walt")
	check(migrated.flags.aftermath_pending=="claim" and old.party[2].id=="cal","Pending aftermath preserved and migration pure")
	check(NativeSaveService.validate_state(migrated),"Migrated state validates")
	var b: Dictionary=BattleRules.create_battle()
	b.party[0].hp=0;b.sync=18
	var plan: Array=[{"actor":1,"kind":"guard"},{"actor":2,"kind":"warmth","target":0}]
	check(BattleRules.validate_plan(b,plan).is_empty(),"Later warmth funded by guard")
	var after: Dictionary=BattleRules.resolve_plan(b,plan)
	check(after.party[0].hp==22 and after.guards[0] and after.sync==0,"Warmth revives and guards chosen ally")
	check(not BattleRules.validate_plan(b,[{"actor":1,"kind":"lantern"}]).is_empty(),"Lantern is owned by Walt")
	b.sync=100
	after=BattleRules.resolve_plan(b,[{"actor":2,"kind":"windbreak","target":1}])
	var hit: Dictionary=BattleRules.hit(after,1,10)
	check(after.party[1].hp-hit.party[1].hp==6,"Windbreak reduces chosen ally's 9 damage to 6")
	var p: Dictionary=NativeNewEncounter.create("walt",271828,0,0)
	while not p.done: p=NativeNewEncounter.step(p,Vector2.ZERO,false,1.0,false,true,int(p.clock)%28==0)
	check(p.promiseComplete and p.gustsKept==3 and p.lantern>0,"Walt objective survives three signalled gusts")
	p=NativeNewEncounter.create("walt",271828,0,0)
	while not p.done: p=NativeNewEncounter.step(p,Vector2.ZERO,false,1.0,false,true,int(p.clock)%120==0)
	check(p.promiseComplete,"Raising at the warning start covers its whole gust")
	p=NativeNewEncounter.create("walt",271828,0,0)
	while not p.done:p=NativeNewEncounter.step(p,Vector2.ZERO,false,1.0,false,true,false)
	check(not p.promiseComplete and p.gustsKept==0,"Camping shelter without raising lantern fails promise")
	for phase: int in range(3):
		p=NativeNewEncounter.create("encore",271828,phase,0)
		while not p.done:
			var cursor:=Vector2(p.cursor.x,p.cursor.y)
			var dest:=Vector2(p.safeColumn,92)
			var delta: Vector2=dest-cursor
			var axis:=Vector2(signf(delta.x) if absf(delta.x)>2 else 0,signf(delta.y) if absf(delta.y)>2 else 0)
			p=NativeNewEncounter.step(p,axis,false,1.0,false,true,p.cueOpen and cursor.distance_to(dest)<14)
		check(p.promiseComplete and p.cuesReached>=2,"ENCORE actual stopping cues phase "+str(phase))
	var frames: SpriteFrames=NativeExpansionArt.world_frames("walt")
	for direction: String in ["up","down","left","right"]:
		var name: String="walk_"+direction
		check(frames.get_frame_count(name)==6,"Six true frames "+direction)
		check(frames.get_frame_texture(name,0).region!=frames.get_frame_texture(name,1).region,"Distinct walking cells "+direction)
	var main: Node=load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	main.qa=true;main.saves=NativeSaveService.new("user://chapter1-unit")
	main.preferences_path="user://chapter1-unit/no-preferences.json"
	NativeCampaign.handle(main,{"id":"cal"})
	check(not main.state.flags.get("cal_key_received",false),"Early Cal sends player back to Walt before the key")
	check(not main.dialogue_lines.any(func(line: Array) -> bool: return line[0]=="Walt"),"Unrecruited Walt cannot speak in early Cal scene")
	main.restore_state(old)
	check(main.mode==main.Mode.DIALOGUE and main.state.flags.walt_intro_pending,"Late legacy save receives new introduction")
	for i: int in range(10):
		if main.mode!=main.Mode.DIALOGUE:break
		main.reveal=10000;main.advance_dialogue()
	check(main.state.room=="U08" and main.state.flags.legacy_aftermath_pending=="claim","Introduction returns to Walt without losing aftermath")
	for outcome: String in ["peaceful","forceful"]:
		main.state=NativeState.fresh();main.state.flags.imani_joined=true;main.state.flags.walt_resolution=outcome
		NativeCampaign.aftermath(main,"walt")
		check(not main.state.flags.get("walt_joined",false),outcome+" recruitment waits for dialogue")
		for i: int in range(20):
			if main.mode!=main.Mode.DIALOGUE:break
			main.reveal=10000;main.advance_dialogue()
		check(main.state.flags.get("walt_joined",false),outcome+" recruits full Walt")
	# Simulate process interruption at the newly committed tutorial checkpoint.
	main.state=NativeState.fresh();main.state.flags={"imani_joined":true,"walt_resolution":"peaceful","claim_resolution":"peaceful","pip_joined":true,"legacy_aftermath_pending":"claim","legacy_aftermath_room":"U07"}
	NativeCampaign.aftermath(main,"walt")
	for i: int in range(20):
		if main.state.flags.get("walt_joined",false):break
		main.reveal=10000;main.advance_dialogue()
	check(main.state.flags.aftermath_pending=="walt","Tutorial checkpoint remains resumable after recruitment commits")
	var interrupted: Dictionary=main.state.duplicate(true)
	main.restore_state(interrupted)
	check(main.mode==main.Mode.DIALOGUE,"Walt tutorial interruption resumes aftermath")
	for i: int in range(40):
		if main.mode!=main.Mode.DIALOGUE:break
		main.reveal=10000;main.advance_dialogue()
	check(main.state.room=="U07" and main.state.flags.aftermath_pending=="" and main.state.flags.legacy_aftermath_pending=="","Resumed tutorial also completes the original pending Advisor Bev scene")
	main.state=NativeState.fresh();main.state.flags.encore_resolution="peaceful"
	NativeCampaign.aftermath(main,"encore")
	for i: int in range(20):
		if main.state.flags.get("chapter1_complete",false):break
		main.reveal=10000;main.advance_dialogue()
	check(main.state.flags.aftermath_pending=="encore","ENCORE's plot hook remains resumable after chapter completion")
	interrupted=main.state.duplicate(true);main.restore_state(interrupted)
	for i: int in range(40):
		if main.mode!=main.Mode.DIALOGUE:break
		main.reveal=10000;main.advance_dialogue()
	check(main.state.flags.chapter1_complete and main.state.flags.aftermath_pending=="","ENCORE interruption resumes and finishes its plot hook")
	main.audio.shutdown();main.dialogue_callback=Callable();main.menu_options.clear();main.pause_options.clear();main.dialogue_choices.clear()
	main.queue_free();await process_frame
	print("Chapter 1 focused checks: ",checks,", failures: ",failures)
	quit(0 if failures==0 else 1)
