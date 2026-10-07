extends "res://scenes/qa_opening.gd"
## Actual-input route for wandering fights: walk the Farrand lawn with the keys until a fight starts,
## win one peacefully (CONNECT, promise, RELEASE) and one forcefully (STRIKE), check the Buff Bucks
## payout, the quiet spell after a fight, the pause-menu readout and the Settings switch.
## --qa-wander runs it. Only this route lets fights start under QA (NativeRandomFights.allowed).
const SPOT: Vector2 = Vector2(700, 300)

func run(main: Node) -> bool:
	game=main;folder=OS.get_environment("AFTER_HOURS_QA")
	force_claim=false;fail_promise=false;retry_route=false;observe_claim=false
	_log("START Wandering fights, ordinary input")
	await _choose("Settings")
	if not game.state.settings.instant: await _choose("Instant dialogue:")
	await _choose("Back");await _choose("Begin the evening")
	for _i: int in range(60):
		if int(game.mode)!=INTRO:break
		await _press("cancel")
	await _quiet()
	if game.jakerson_ui:await _choose("I'll find my way")
	_assert(int(game.mode)==WORLD,"Skipping the intro cards lands in the world")
	# Setup: the first story fight is behind us, and we stand on open ground on the Farrand lawn.
	game.state.flags.flyer_resolution="peaceful"
	game.enter_room("F04",SPOT)
	await _quiet()
	_assert(str(game.state.room)=="F04" and not NativeRandomFights.near_something(game),"Standing on open ground on the lawn")
	await _walk_around(120)
	_assert(int(game.mode)==WORLD and NativeRandomFights.walked>0.0,"Walking builds up the fight counter without starting one early")
	# Win one peacefully.
	var first: String=await _wander_into_fight()
	var before: int=NativeRandomFights.bucks(game.state.flags)
	await _wander_fight(first,true)
	var gain: int=NativeRandomFights.bucks(game.state.flags)-before
	_assert(gain>=int(NativeRandomFights.FIGHTS[first].bucks[0]) and gain<=int(NativeRandomFights.FIGHTS[first].bucks[1]),"A peaceful win pays its full Buff Bucks range (%d)"%gain)
	_assert(int(game.mode)==WORLD and str(game.state.room)=="F04" and game.boss_id=="" and str(game.state.flags.get("aftermath_pending",""))=="","Back in the world, no story aftermath left pending")
	_assert(str(game.notice).begins_with("+%d Buff Bucks"%gain),"The payout is announced: "+str(game.notice))
	_assert(not game.state.flags.has(first+"_resolution"),"A wandering fight leaves no story flags")
	await _capture("01-after-peaceful-win")
	# The quiet spell: no second fight straight away.
	NativeRandomFights.force(game)
	await _walk_around(120)
	_assert(int(game.mode)==WORLD and game.boss_id=="","No second fight during the quiet spell after a win")
	# The pause menu shows the balance.
	await _press("menu")
	await _choose("Party / keepsakes")
	_assert(str(game.caption).contains("Buff Bucks %d"%NativeRandomFights.bucks(game.state.flags)),"The party screen shows the Buff Bucks balance: "+str(game.caption))
	await _choose("Back");await _choose("Resume");await _quiet()
	# The Settings switch turns fights off, and back on.
	await _press("menu");await _choose("Settings");await _choose("Wandering fights: On");await _choose("Wandering fights: Off")
	_assert(not bool(game.state.flags.get("wander_off",false)),"The switch flips back on")
	await _choose("Wandering fights: On");await _choose("Back");await _choose("Resume");await _quiet()
	_assert(bool(game.state.flags.get("wander_off",false)),"The switch turns wandering fights off")
	for _i: int in range(game.grace_ticks+30):await _frame()
	NativeRandomFights.force(game)
	await _walk_around(150)
	_assert(int(game.mode)==WORLD and game.boss_id=="","With the switch off nothing starts")
	await _press("menu");await _choose("Settings");await _choose("Wandering fights: Off");await _choose("Back");await _choose("Resume");await _quiet()
	_assert(not bool(game.state.flags.get("wander_off",false)),"Back on")
	# Win one the hard way.
	var second: String=await _wander_into_fight()
	before=NativeRandomFights.bucks(game.state.flags)
	await _wander_fight(second,false)
	gain=NativeRandomFights.bucks(game.state.flags)-before
	_assert(gain>=1 and gain<=int(NativeRandomFights.FIGHTS[second].bucks[1]),"A forceful win still pays, a little less (%d)"%gain)
	_assert(NativeRandomFights.count(game.state.flags,"wander_wins")==2,"Two wins counted")
	await _capture("02-after-forceful-win")
	_log("PASS wandering fights route")
	return not failed

## Walks left and right for a number of frames with the movement keys.
func _walk_around(frames: int) -> void:
	for i: int in range(frames):
		if int(game.mode)!=WORLD or failed:break
		_axis(Vector2.RIGHT if (i/30)%2==0 else Vector2.LEFT)
		await _frame()
	_release()

## Forces the next roll and walks until a fight's opening line appears; returns the fight id.
func _wander_into_fight() -> String:
	for _i: int in range(game.grace_ticks+10):await _frame()
	NativeRandomFights.force(game)
	await _walk_around(90)
	_assert(int(game.mode)==DIALOGUE,"Walking starts a fight with its opening line")
	if failed:return ""
	var speaker: String=str(game.dialogue_lines[game.line_index][0])
	var id: String=""
	for key: String in NativeRandomFights.FIGHTS:
		if NativeRandomFights.name_of(key)==speaker:id=key
	_assert(not id.is_empty() and game.rooms[str(game.state.room)].wander.has(id),"The fight is one of this room's: "+speaker)
	await _capture("00-fight-line-"+id)
	await _settle()
	_log("After the opening line mode=%d boss=%s caption=%s"%[int(game.mode),str(game.boss_id),str(game.caption)])
	_assert(int(game.mode)==BATTLE and game.boss_id==id and int(game.battle.hp)==NativeRandomFights.hp(id),"The battle opens with no intro card and the fight's own HP (%d)"%int(game.battle.get("hp",-1)))
	return id

## The fight with ordinary menu input. Peaceful: CONNECT with the promise, RELEASE when it shows.
## Forceful: STRIKE with the timing press.
func _wander_fight(id: String,peaceful: bool) -> void:
	var start: int=ticks
	var promise: String=str(NativeRandomFights.connect_labels(id)[1])
	while not failed and int(game.mode)!=RESULT:
		if ticks-start>9000:_assert(false,"Wandering fight did not resolve "+id);break
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
				else:_assert(false,"Unexpected wandering-fight menu "+str(game.caption))
			DODGE:await _defend(id)
			TIMING:
				_release()
				if int(game.timing_ticks)>=27:await _press()
				else:await _frame()
			DIALOGUE:await _settle()
			_:
				_release();await _frame()
	_release()
	if failed:return
	var expected: String="peaceful" if peaceful else "forceful"
	_assert(str(game.battle.outcome)==expected,"Wandering fight %s ended %s (turns %d)"%[id,expected,int(game.battle.turn)])
	await _capture("03-result-"+expected)
	await _choose("Continue")
	await _settle()
