extends "res://scenes/qa_wander.gd"
## Actual-input route for the Fountain Court hub, the Hill and the Pearl Street office: step down
## from the UMC terrace, buy supplies until the pack is full, rest on the bench, buy a keepsake in the
## Book Store, visit the Career Center, then beat Tanner the peaceful way and Kyle the hard way
## (when their dodge scripts exist), checking Buff Bucks and the LinkedOut requests along the way.
## --qa-hub runs it. Story flags are set directly; everything else is clicks and keys.
const BANNER: int = 14

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
	f.imani_joined=true;f.walt_joined=true;f.buff_bucks="300"
	game.enter_room("U02",Vector2(108,278),false)
	await _quiet()
	# The court opens once the first story fight is behind Jules.
	await _object("fountain_steps")
	_assert(str(game.state.room)=="U02" and str(game.notice).contains("poster"),"The steps stay shut before the first fight: "+str(game.notice))
	f.flyer_resolution="peaceful"
	await _door("fountain_steps","C01")
	await _quiet()
	_assert(game.world_npcs.size()>=10,"The court is full of people (%d)"%game.world_npcs.size())
	await _capture("01-court")
	# Supplies from the waffle truck until the pack is full.
	await _object("truck_waffles");await _settle()
	_assert(int(game.mode)==MENU and str(game.caption).begins_with("Waffle truck"),"The waffle truck opens its counter: "+str(game.caption))
	var before: int=NativeRandomFights.bucks(f)
	var cocoa: int=int(game.state.inventory.cocoa)
	await _choose("Cocoa")
	_assert(NativeRandomFights.bucks(f)==before-10 and int(game.state.inventory.cocoa)==cocoa+1,"A cocoa costs 10 Buff Bucks and lands in the pack: "+str(game.caption))
	for _i: int in range(6):await _choose("Cocoa")
	_assert(NativeShops.pack_total(game.state.inventory)==NativeShops.PACK_LIMIT,"The pack stops at 8 supplies: "+str(game.caption))
	_assert(str(game.caption).contains("full"),"A full pack says so")
	await _capture("02-truck-menu")
	await _choose("Back");await _quiet()
	_assert(int(game.mode)==WORLD,"Leaving the counter returns to the court")
	# A bench to rest and save on.
	await _object("fountain_bench");await _quiet()
	_assert(int(game.mode)==MENU and str(game.caption).begins_with("Warm light"),"The fountain bench is a rest and save spot: "+str(game.caption))
	await _choose("Back");await _quiet()
	# A person on the court talks.
	await _object("court_philosopher");await _settle()
	_assert(int(game.mode)==WORLD,"Talking to a stranger on the court ends back in the world")
	# The Book Store sells keepsakes.
	await _door("book_store","C02")
	await _object("register");await _settle()
	_assert(int(game.mode)==MENU and str(game.caption).begins_with("Book Store register"),"The register opens: "+str(game.caption))
	before=NativeRandomFights.bucks(f)
	await _choose("Buffs hoodie")
	_assert(PartyGrowth.found(f,"buffs_hoodie") and PartyGrowth.equipped(f,"jules")=="buffs_hoodie" and NativeRandomFights.bucks(f)==before-60,"The hoodie is bought and worn: "+str(game.caption))
	await _choose("Buffs hoodie")
	_assert(NativeRandomFights.bucks(f)==before-60,"Buying it twice costs nothing")
	await _capture("03-register-menu")
	await _choose("Back");await _quiet()
	await _door("court_exit","C01")
	# The Career Center: a kiosk and a walk-in advisor.
	await _door("career_center","C03")
	await _object("advisor");await _settle()
	_assert(int(game.mode)==WORLD,"The advisor talks and lets go")
	await _object("waiting_chairs");await _quiet()
	_assert(int(game.mode)==MENU and str(game.caption).begins_with("Warm light"),"The waiting chairs are a rest and save spot")
	await _choose("Back");await _quiet()
	await _door("court_exit","C01")
	# The dorm is reachable from the court and its front doors lead back out.
	await _door("farrand_hall","D03")
	await _door("front_doors","C01")
	# The Hill, then Tanner.
	await _object("hill")
	_assert(str(game.state.room)=="C01" and str(game.notice).contains("ENCORE"),"The Hill waits for chapter one: "+str(game.notice))
	f.chapter1_complete=true
	await _door("hill","H01")
	await _quiet()
	_assert(bool(f.get("scene_tanner_couch",false)) and not NativeRoomScenes.busy() and int(game.mode)==WORLD,"The couch walk-in plays out and hands control back")
	_assert(game.world_npcs.any(func(n: AnimatedSprite2D) -> bool:return str(n.get_meta("id",""))=="tanner" and n.visible),"Tanner is standing on the Hill after the couch lands")
	await _capture("04-the-hill")
	await _object("hill_philosopher");await _settle()
	await _door("party_door","H02")
	await _capture("05-house-party")
	_assert(NativeSideQuests.guests.size()==NativeSideQuests.GUESTS.size(),"Four guests patrol the party")
	await _object("dj");await _settle()
	# Bump a guest: a quick wandering fight, then the casserole in the kitchen.
	NativeSideQuests.armed=true
	for _i: int in range(game.grace_ticks+10):await _frame()
	var guest: Node2D=NativeSideQuests.guests[0]
	game.player.position=guest.position
	for _i: int in range(4):await _frame()
	_assert(int(game.mode)==DIALOGUE,"Bumping a guest starts a fight line")
	var bumped: String=""
	for key: String in NativeRandomFights.FIGHTS:
		if NativeRandomFights.name_of(key)==str(game.dialogue_lines[game.line_index][0]):bumped=key
	_assert(bumped=="rf_hippie","The bump is that guest's fight: "+bumped)
	await _settle()
	before=NativeRandomFights.bucks(f)
	await _wander_fight(bumped,true)
	_assert(NativeRandomFights.bucks(f)>before and str(game.state.room)=="H02","The fight paid Buff Bucks and left Jules in the party")
	NativeSideQuests.armed=false
	before=NativeRandomFights.bucks(f)
	await _object("kitchen");await _settle()
	_assert(bool(f.get("party_casserole",false)) and NativeRandomFights.bucks(f)==before+NativeSideQuests.CASSEROLE_PAY,"The casserole pays in the kitchen")
	_assert(NativeSideQuests.guests.is_empty(),"The patrol is gone once the casserole is taken")
	await _door("front_door","H01")
	if DodgeBox.handles("tanner"):
		before=NativeRandomFights.bucks(f)
		await _object("tanner");await _settle()
		_assert(int(game.mode) in [BATTLE,BANNER] and game.boss_id=="tanner" and int(game.battle.hp)==NativeSideBosses.hp("tanner"),"Tanner's fight opens with his own HP: "+str(game.battle.get("hp",-1)))
		await _side_fight("tanner",true)
		_assert(str(f.get("tanner_resolution",""))=="peaceful" and NativeRandomFights.bucks(f)-before>=60,"Tanner pays his full Buff Bucks the peaceful way (%d)"%(NativeRandomFights.bucks(f)-before))
		_assert(LinkedOut.pending(f).any(func(p: Dictionary)->bool:return str(p.id)=="tanner"),"Tanner sends a LinkedOut request")
		_assert(int(game.mode)==WORLD and str(game.state.room)=="H01" and game.boss_id=="","Back on the Hill after the fight")
		await _object("tanner");await _settle()
		_assert(int(game.mode)==WORLD,"Afterwards Tanner just chats")
	else:
		_log("SKIP Tanner's fight: no dodge script yet")
	# Pearl Street, then Kyle the hard way.
	await _door("hill_return","C01")
	await _object("pearl_st")
	_assert(str(game.state.room)=="C01" and str(game.notice).contains("reel"),"Pearl Street waits for chapter two: "+str(game.notice))
	f.chapter2_complete=true
	await _door("pearl_st","P01")
	await _capture("06-open-office")
	await _object("coworker_board");await _settle()
	await _object("intern_desk");await _settle()
	_assert(int(game.mode)==WORLD and not f.has("task_coffee"),"The intern desk waits for Kyle's meeting")
	if DodgeBox.handles("kyle"):
		before=NativeRandomFights.bucks(f)
		await _object("kyle");await _settle()
		_assert(int(game.mode) in [BATTLE,BANNER] and game.boss_id=="kyle","Kyle's fight opens")
		await _side_fight("kyle",false)
		_assert(str(f.get("kyle_resolution",""))=="forceful" and NativeRandomFights.bucks(f)-before>=48,"Kyle still pays the hard way (%d)"%(NativeRandomFights.bucks(f)-before))
		_assert(not LinkedOut.pending(f).any(func(p: Dictionary)->bool:return str(p.id)=="kyle") and LinkedOut.viewed_only(f).any(func(p: Dictionary)->bool:return str(p.id)=="kyle"),"Kyle only views the profile after a forceful ending")
	else:
		_log("SKIP Kyle's fight: no dodge script yet")
	await _object("intern_desk");await _quiet()
	_assert(int(game.mode)==MENU and str(game.caption).begins_with("Intern desk"),"The desk lists the tasks: "+str(game.caption))
	await _choose("Friday demo");await _quiet()
	_assert(str(game.caption).contains("Friday is for"),"The demo is locked until the first two")
	before=NativeRandomFights.bucks(f)
	await _choose("Coffee run");await _settle()
	await _choose("Drip, regular");await _settle()
	_assert(int(game.mode)==MENU and str(game.caption).begins_with("Coffee run / cup 1"),"A wrong cup restarts the order: "+str(game.caption))
	for cup: String in NativeSideQuests.ORDER:await _choose(cup)
	await _settle()
	_assert(bool(f.get("task_coffee",false)) and NativeRandomFights.bucks(f)==before+30,"The coffee run pays 30")
	for move: String in ["Reply","React","Mute","React","Mute"]:
		if move=="Reply":
			await _choose("Clear the Slack storm");await _settle()
		await _choose(move)
	await _settle()
	_assert(bool(f.get("task_slack",false)),"The Slack storm clears")
	await _choose("Friday demo");await _settle()
	for pick: String in ["The problem a real user actually has","The working feature","A question: what would you change?"]:await _choose(pick)
	await _settle()
	_assert(bool(f.get("task_demo",false)) and bool(f.get("intern_complete",false)),"The demo lands and the internship is complete")
	_assert(NativeSaveService.validate_state(game.state),"The state still saves after the tasks")
	await _choose("Back");await _quiet()
	await _door("break_room","P02")
	await _object("beanbag");await _quiet()
	_assert(int(game.mode)==MENU and str(game.caption).begins_with("Warm light"),"The beanbag is a rest and save spot")
	await _choose("Back");await _quiet()
	await _door("office_door","P01")
	await _door("stairs_down","C01")
	_log("PASS hub route")
	return not failed

## A mini-boss fight with ordinary menu input: gym card, then CONNECT with the promise and RELEASE, or STRIKE.
func _side_fight(id: String,peaceful: bool) -> void:
	var start: int=ticks
	var promise: String=str(NativeSideBosses.connect_labels(id)[1])
	while not failed and int(game.mode)!=RESULT:
		if ticks-start>12000:_assert(false,"Mini-boss fight did not resolve "+id);break
		match int(game.mode):
			BATTLE:
				_release()
				if str(game.caption)=="Review party plan":await _choose("Commit turn")
				elif str(game.caption).contains("Choose an action"):
					if peaceful:await _choose("CONNECT" if int(game.actor)==0 else "GUARD")
					else:await _choose("STRIKE")
				elif str(game.caption).begins_with("Connect"):
					var labels: Array=game.menu_options.map(func(o: Dictionary) -> String:return str(o.label))
					if labels.any(func(l: String) -> bool:return l.begins_with("RELEASE")):await _choose("RELEASE")
					else:await _choose(promise)
				else:_assert(false,"Unexpected mini-boss menu "+str(game.caption))
			DODGE:await _defend(id)
			TIMING:
				_release()
				if int(game.timing_ticks)>=27:await _press()
				else:await _frame()
			DIALOGUE:await _settle()
			BANNER:
				_release();await _press()
			_:
				_release();await _frame()
	_release()
	if failed:return
	var expected: String="peaceful" if peaceful else "forceful"
	_assert(str(game.battle.outcome)==expected,"Mini-boss %s ended %s (turns %d)"%[id,expected,int(game.battle.turn)])
	await _capture("07-result-"+id)
	await _choose("Continue")
	await _settle()
