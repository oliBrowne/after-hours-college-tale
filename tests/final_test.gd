extends SceneTree
var checks: int=0
var failures: int=0
func check(ok: bool,what: String) -> void:
	checks+=1
	if not ok:failures+=1;print("FAIL ",what)
func drain(g: Node) -> void:
	for i: int in range(50):
		if g.mode!=g.Mode.DIALOGUE:break
		g.reveal=10000;g.advance_dialogue()
func drive(id: String,phase: int,assist: float,slow: bool,promised: bool,revision: String="",rejected: Array=[]) -> Dictionary:
	var p: Dictionary=NativeFinalEncounter.create(id,7102,phase,0);p.revision=revision;p.rejected=rejected
	for i: int in range(6000):
		var at:=Vector2(p.cursor.x,p.cursor.y);var dest:=Vector2(128,62)
		match id:
			"cone":dest=Vector2(128,p.safeLane)
			"chad":dest=Vector2(48,90)
			"rook":dest=Vector2(60,24) if phase==0 and not p.keyHeld else Vector2(196,96) if phase==0 else Vector2(48 if revision=="west" else 208,70) if phase==1 else Vector2(128,84)
			"val":dest=[Vector2(128,24),Vector2(208,96),Vector2(48,96)][mini(2,int(p.valTask))] if phase==0 else Vector2(64 if revision=="left" else 192,84) if phase==2 else Vector2(128,62)
		var d: Vector2=dest-at;var axis:=Vector2(signf(d.x) if absf(d.x)>2 else 0,signf(d.y) if absf(d.y)>2 else 0)
		p=NativeFinalEncounter.step(p,axis,false,assist,slow,promised,at.distance_to(dest)<15)
		if p.done:break
	return p
func _initialize() -> void:call_deferred("run")
func run() -> void:
	for id: String in NativeFinalEncounter.IDS:
		for phase: int in range(4 if id=="val" else 3 if id=="rook" else 1):
			for assisted: bool in [false,true]:
				var revision: String="west" if id=="rook" else "left"
				var p: Dictionary=drive(id,phase,0.65 if assisted else 1.0,assisted,true,revision,["jules","imani","walt"])
				check(p.done and p.promiseComplete,id+" phase "+str(phase)+" actual moving/confirm objective, assist="+str(assisted))
				p=drive(id,phase,1.0,false,false,revision,["jules","imani","walt"])
				check(not p.promiseComplete,id+" phase "+str(phase)+" cannot complete without promise")
	check(not drive("rook",1,1.0,false,true).promiseComplete,"Rook cannot finish incompatible exits without REVISE")
	check(not drive("rook",2,1.0,false,true).promiseComplete,"Rook stopping cues alone cannot replace revision")
	check(not drive("val",1,1.0,false,true,"",["jules","imani"]).promiseComplete,"VAL requires Walt's own rejection too")
	var blocked: Dictionary=drive("val",2,1.0,false,true)
	check(not blocked.promiseComplete and blocked.chairs.size()==2,"VAL unrevised chairs remain real collision obstacles")
	check(drive("val",2,1.0,false,true,"right").chairs.size()==1,"REVISE right removes exactly that physical chair field")
	var chair: Dictionary=NativeFinalEncounter.create("chad",1,0,0);chair.cursor={"x":128.0,"y":60.0};chair.clock=chair.leadIn
	chair=NativeFinalEncounter.step(chair,Vector2.ZERO,false,1.0,false,true,false)
	check(chair.chairEntered and not chair.promiseComplete,"Occupying empty chair invalidates quiet promise")
	var g: Node=load("res://scenes/main.tscn").instantiate();root.add_child(g)
	g.qa=true;g.saves=NativeSaveService.new("user://final-focused/saves");g.preferences_path="user://final-focused/preferences.json"
	g.state.flags={"imani_joined":true,"walt_joined":true,"opening_finished":true,"chapter3_complete":true,"rook_confessed":true,"rook_resolution":"peaceful"}
	g.enter_room("M05",Vector2(120,440),false);g.boss_id="rook";g.begin_battle()
	NativeFinalCampaign.record_defense(g,false,true);check(g.battle.rook_stage==0,"Waiting cannot skip Rook's key-and-exit objective")
	NativeFinalCampaign.record_defense(g,true,false);check(g.battle.rook_stage==0,"Unpromised success cannot replace ordered Rook promise")
	NativeFinalCampaign.record_defense(g,true,true);g.connect_menu();check(g.boss_stage==1 and g.menu_options.any(func(c: Dictionary) -> bool:return str(c.label).begins_with("REVISE")),"Kept key objective reveals real REVISE choices next turn")
	NativeFinalCampaign.record_defense(g,true,true);check(g.boss_stage==2 and not g.release_ready(),"Kept chosen exit still requires shared stopping cues")
	NativeFinalCampaign.record_defense(g,true,true);g.battle.revision="west";check(g.release_ready(),"Only ordered shared shift unlocks Rook release")
	for id: String in ["cone","chad"]:
		for outcome: String in ["peaceful","forceful"]:
			g.state.flags[id+"_resolution"]=outcome;g.state.flags.aftermath_pending=id;g.persist();g.restore_state(g.saves.load_slot("auto").state)
			check(g.mode==g.Mode.DIALOGUE and g.state.flags.aftermath_pending==id,id+" "+outcome+" replays optional consequence from disk")
			drain(g);check(g.state.flags.aftermath_pending=="",id+" "+outcome+" full hook clears pending")
	g.enter_room("M06",Vector2(120,440),false);g.boss_id="val";g.begin_battle()
	g.boss_stage=1;g.battle.val_stage=1
	var self_choices: Array=[]
	for i: int in range(3):self_choices.append({"actor":i,"kind":"connect","reject":g.battle.party[i].id})
	check(BattleRules.validate_plan(g.battle,self_choices).is_empty(),"Three actor-owned ideal choices form a legal shared plan")
	var committed: Dictionary=BattleRules.resolve_plan(g.battle,self_choices);NativeFinalCampaign.decorate(g,committed,self_choices)
	check(committed.rejected.size()==3 and committed.promise,"Three real choices arm one shared objective instead of three incompatible promises")
	for id: String in ["jules","imani","walt"]:
		var frames: SpriteFrames=NativePartyBattleArt.frames(id)
		check(frames.get_frame_count("idle")==3 and frames.get_frame_count("strike")==4 and frames.has_animation("talent") and frames.has_animation("hit") and frames.has_animation("down"),id+" complete matching battle animation set")
		var sprite:=AnimatedSprite2D.new();sprite.sprite_frames=frames;sprite.play("idle");root.add_child(sprite);sprite.position=Vector2(200,150)
		NativeIdleMotion.apply(sprite,72,0,false,4);var pivot: Vector2=sprite.position;var old_scale: Vector2=sprite.scale
		NativeIdleMotion.apply(sprite,72,4.0,false,4);check(sprite.position==pivot and sprite.scale==old_scale and sprite.frame==1,id+" breathing changes pixel pose with fixed scale and planted feet")
		NativeIdleMotion.apply(sprite,72,2,true,4);check(is_zero_approx(sprite.rotation),id+" reduced motion stops sway")
		sprite.queue_free()
	g.boss_stage=0;g.battle.val_stage=0
	for phase: int in [1,2,3]:
		g.battle.val_stage=phase;g.battle.rejected=["jules","imani","walt"];g.battle.val_revision="left";g.battle.sync=45;g.battle.inventory.granola=1;g.battle.party[0].hp=30
		NativeFinalCampaign.checkpoint(g)
		var saved: Dictionary=g.saves.load_slot("auto").state
		check(saved.flags.val_checkpoint is String,"Phase checkpoint preserves typed bool/string save schema")
		g.restore_state(saved)
		check(g.boss_stage==phase and g.mode==g.Mode.BATTLE and g.battle.inventory.granola==1 and g.battle.party[0].hp==48,"Actual disk Continue restores phase/supplies without granting repeat recovery")
		check(g.release_ready()==false,"Reloaded phase requires real new defense before ending")
	var valid_raw: String=g.state.flags.val_checkpoint
	for bad: String in ["{}","{broken",JSON.stringify({"hp":0,"openness":0,"sync":0,"turn":0,"stage":3,"rejected":[],"revision":"left","force":false})]:
		g.state.flags.val_checkpoint=bad;check(not NativeFinalCampaign.restore_checkpoint(g),"Malformed phase checkpoint safely rejected")
	g.state.flags.val_checkpoint=valid_raw
	g.battle.val_stage=0;g.battle.outcome="forceful";NativeFinalCampaign.force_advance(g)
	check(g.boss_stage==1 and g.battle.val_force and g.battle.outcome=="active" and g.battle.hp==160,"Force cannot skip directly to VAL ending")
	drain(g)
	for ending: String in ["release","rewrite","break"]:
		g.state.flags.ending=ending;g.state.flags.val_resolution="forceful" if ending=="break" else "peaceful";g.state.flags.aftermath_pending="val";g.state.flags.erase("dawn_started");g.state.flags.erase("dawn_complete")
		g.state.flags.val_checkpoint="";g.enter_room("M06",Vector2(120,440),false);check(g.persist(),ending+" terminal pending checkpoint writes")
		g.restore_state(g.saves.load_slot("auto").state)
		check(g.mode==g.Mode.DIALOGUE and g.state.flags.aftermath_pending=="val" and not g.state.flags.get("dawn_started",false),ending+" full aftermath resumes from real disk before dawn")
		drain(g);check(g.state.room=="M07" and g.state.flags.dawn_started and g.state.flags.aftermath_pending=="",ending+" reaches playable dawn only after consequence hook")
		g.state.flags.aftermath_pending="dawn";g.state.flags.family_reply="where-i-am";g.enter_room("U01",Vector2(120,270),false);g.persist();g.restore_state(g.saves.load_slot("auto").state)
		check(g.mode==g.Mode.DIALOGUE and not g.state.flags.get("dawn_complete",false),ending+" home conversation survives disk reload")
		drain(g);check(g.state.flags.dawn_complete and g.state.flags.aftermath_pending=="",ending+" concludes and offers exploration")
	g.audio.shutdown();g.dialogue_callback=Callable();g.menu_options.clear();g.pause_options.clear();g.dialogue_choices.clear();g.queue_free();await process_frame
	print("Finale focused checks: ",checks,", failures: ",failures);quit(0 if failures==0 else 1)
