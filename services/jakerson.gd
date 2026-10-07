class_name NativeJakerson
extends RefCounted
## Jakerson, the computer science student who meets Jules at the Broadway bus stop.
## Instead of a menu tour he walks you to the UMC terrace (stopping to show you how
## to read things and that doors need confirm), then offers a friendly practice spar
## there that explains the battle system, and stays on the terrace as the help NPC.
## Flags: jakerson_seen, intro_seen, jakerson_guide ("" not started, "walk" leading
## you to the terrace, "terrace" waiting there, "skip" you went alone),
## jakerson_resolution (set by finish_battle after the spar).
const TERRACE: String = "U02"
const START: String = "U01"
## Where he waits on the terrace after the walk, beside the compass medallion.
const TERRACE_SPOT: Vector2 = Vector2(400, 192)
## His standing block in U01's rooms.json (x 141, y 243, 18 x 8), freed once he walks.
const HOME_BLOCK: Vector2 = Vector2(150, 247)
const SPEED: float = 70.0 / 60.0
const WAIT_RANGE: float = 104.0
## His side pose looks right; walking left mirrors it.
const SIDE_FACES_RIGHT: bool = true
const GRADUATION_SPOT: Vector2 = Vector2(500, 372)
const JOG: float = 150.0 / 60.0
## The running drop-in scene: {id, sprite, phase "in"|"talk"|"out", door, lines}.
static var scene: Dictionary = {}

static func guide(g: Node) -> String:return str(g.state.flags.get("jakerson_guide",""))
static func active(g: Node) -> bool:return guide(g)=="walk"
static func say(g: Node,lines: Array,then: Callable) -> void:
	g.jakerson_ui=true
	g.dialogue(lines,func() -> void:g.jakerson_ui=false;then.call())
static func leave(g: Node) -> void:
	g.jakerson_ui=false;g.dialogue_choices.clear();g.dialogue_callback=Callable()
	if guide(g)=="":g.state.flags.jakerson_guide="skip"
	g.persist();g.resume_world()
static func controller_controls(g: Node) -> String:
	return "Controller / Up: "+g.binding_label("move_up","controller")+". Down: "+g.binding_label("move_down","controller")+". Left: "+g.binding_label("move_left","controller")+". Right: "+g.binding_label("move_right","controller")+"."
static func controls(g: Node) -> String:
	return "Up: "+g.binding_label("move_up")+". Down: "+g.binding_label("move_down")+". Left: "+g.binding_label("move_left")+". Right: "+g.binding_label("move_right")+"."
static func key(g: Node,action: String) -> String:return str(g.binding_label(action)).get_slice(" / ",0)
static func move_keys(g: Node) -> String:
	return key(g,"move_up")+" "+key(g,"move_left")+" "+key(g,"move_down")+" "+key(g,"move_right")
static func next_place(g: Node) -> String:
	if not g.state.flags.get("mixer_returned",false):return "Imani's club room is inside the UMC, on the left side of the atrium."
	return NativeCampaign.objective(g.state)+". The arrow points at the next door."

# ---------------------------------------------------------------- arrival

static func greeting(g: Node) -> void:
	g.state.flags.jakerson_seen=true;g.state.flags.intro_seen=true;g.persist()
	if g.state.flags.get("movein_done",false):
		# Four years after move-in day: he knows exactly who this is.
		say(g,[["Jules","Eight minutes until the last bus. Mixer back to Imani, then home. One small promise.","neutral"],
			["Jakerson","Jules! Is that Imani's mixer? She's been texting everyone about it since dinner.","warm"],
			["Jakerson","I'm heading to the UMC anyway. Rule forty-one: nobody walks alone on the last night.","warm"],
			["Jules","We got to forty-one?","neutral"],
			["Jakerson","I kept adding them. Also... the campus is being weird tonight. My laptop keeps printing the same line. ONE MORE MINUTE.","concern"],
			["Jakerson","Come on, I'll walk you.","warm"]],func() -> void:offer(g));return
	say(g,[["Jules","Eight minutes until the last bus. Mixer back to Imani, then home. One small promise.","neutral"],
		["Jakerson","Hey! Is that Imani's mixer? She's been texting the whole floor about it.","warm"],
		["Jakerson","I'm Jakerson. Computer science. I'm heading to the UMC anyway, and it's quicker if you know the way.","warm"],
		["Jakerson","Also... the campus is being weird tonight. My laptop keeps printing the same line. ONE MORE MINUTE.","concern"],
		["Jakerson","Come on, I'll walk you.","warm"]],func() -> void:offer(g))
static func offer(g: Node) -> void:
	g.jakerson_ui=true
	g.open_menu(g.Mode.MENU,"Jakerson / walk to the UMC",[g.option("Lead the way.",func() -> void:start_walk(g)),g.option("I'll find my way / skip the walk.",func() -> void:leave(g))])
static func start_walk(g: Node) -> void:
	g.jakerson_ui=false;g.state.flags.jakerson_guide="walk";g.persist()
	free_home_block(g)
	g.resume_world()
	g.message("Jakerson: Follow me. "+move_keys(g)+" to walk, hold "+key(g,"run")+" to run.")
## Kept for old callers: the walk replaced the menu tour.
static func start(g: Node) -> void:start_walk(g)

# ---------------------------------------------------------------- room setup

## Called by enter_room on the room's object list before it builds the people.
static func room_objects(g: Node,id: String,point: Vector2,objects: Array) -> Array:
	scene={}
	var where: String=guide(g)
	if id=="G01" and g.state.flags.get("jakerson_outfit","")=="tennis" and not g.state.flags.has("jakerson_final_resolution"):
		return objects.filter(func(o: Dictionary) -> bool:return str(o.id)!="jakerson_graduation")
	if id=="M06" and g.state.flags.get("graduation_day",false) and not g.rooms.has("G01"):
		objects=objects.filter(func(o: Dictionary) -> bool:return str(o.id) not in ["val","reserved_chairs"])
		objects.append({"id":"jakerson","name":"Jakerson / class of this year","x":GRADUATION_SPOT.x,"y":GRADUATION_SPOT.y,"kind":"talk","sprite":"npc-jakerson","hit_rect":[-20,-60,40,64]})
		return objects
	if id==START and where=="terrace":
		objects=objects.filter(func(o: Dictionary) -> bool:return str(o.id)!="jakerson")
	var on_route: bool=where=="walk" and id!=START and id in route_rooms(g)
	if (id==TERRACE and where=="terrace") or on_route:
		var at: Vector2=TERRACE_SPOT if where=="terrace" else point+Vector2(30,-12)
		objects.append({"id":"jakerson","name":"Jakerson / student guide","x":at.x,"y":at.y,"kind":"talk","sprite":"npc-jakerson","hit_rect":[-20,-60,40,64]})
	return objects
static func on_enter(g: Node,id: String) -> void:
	if id==START and guide(g) not in ["","skip"]:free_home_block(g)
static func free_home_block(g: Node) -> void:
	if str(g.state.room)!=START:return
	for body: Node in g.obstacles.duplicate():
		if body is StaticBody2D and body.position.distance_to(HOME_BLOCK)<2.0:
			g.obstacles.erase(body);body.queue_free()

## Rooms from Broadway to the terrace through ordinary doors, so a room added in
## between (the bridge) is walked through without changing this file.
static func route_rooms(g: Node) -> Array:
	var previous: Dictionary={START:""}
	var queue: Array=[START]
	while not queue.is_empty():
		var room: String=queue.pop_front()
		if room==TERRACE:break
		for o: Dictionary in g.rooms[room].objects:
			if str(o.kind)!="door" or not o.has("to"):continue
			var next: String=str(o.to)
			if previous.has(next) or not g.rooms.has(next):continue
			previous[next]=room;queue.append(next)
	var path: Array=[]
	var at: String=TERRACE
	while previous.has(at) and at!="":
		path.push_front(at);at=str(previous[at])
	return path
static func exit_door(g: Node,room: String) -> Dictionary:
	var path: Array=route_rooms(g)
	var index: int=path.find(room)
	if index<0 or index>=path.size()-1:return {}
	for o: Dictionary in g.rooms[room].objects:
		if str(o.kind)=="door" and str(o.get("to",""))==str(path[index+1]):return o
	return {}

# ---------------------------------------------------------------- walking

static func npc(g: Node) -> AnimatedSprite2D:
	for sprite: AnimatedSprite2D in g.world_npcs:
		if is_instance_valid(sprite) and str(sprite.get_meta("id",""))=="jakerson":return sprite
	return null
static func area(g: Node) -> Area2D:
	for zone: Area2D in g.areas:
		if str(zone.get_meta("definition").get("id",""))=="jakerson":return zone
	return null
## A clear spot beside an object, on the side nearest to `toward`.
static func stand_near(g: Node,anchor: Vector2,toward: Vector2,radius: float=40.0) -> Vector2:
	var best: Vector2=anchor
	var cost: float=INF
	for ring: float in [radius,radius+10.0,radius+20.0]:
		for i: int in range(16):
			var p: Vector2=anchor+Vector2.from_angle(i*TAU/16.0)*ring
			if not g.navigation.clear(p):continue
			var c: float=p.distance_to(toward)
			if c<cost:cost=c;best=p
		if cost<INF:break
	return best
## The stops in the room he is leading you through: [point, line, wait for you there].
static func stops(g: Node) -> Array:
	var room: String=str(g.state.room)
	var door: Dictionary=exit_door(g,room)
	var list: Array=[]
	if door.is_empty():return list
	var door_at: Vector2=Vector2(float(door.x),float(door.y))
	if room==START:
		var taught: bool=bool(g.state.flags.get("movein_done",false))
		list.append([stand_near(g,Vector2(426,214),Vector2(380,240),26.0),"Last bus notice. Eight minutes. Tight, but you've done tighter." if taught else "That's the last bus notice. Walk up to things and press "+key(g,"confirm")+" to read them.",true])
		list.append([stand_near(g,door_at,Vector2(500,240),46.0),"Underpass door. You know the drill: stand on it, press "+key(g,"confirm")+"." if taught else "Doors around here stick. Stand on the door and press "+key(g,"confirm")+".",false])
	elif room=="U08" and g.rooms[room].objects.any(func(o: Dictionary) -> bool: return str(o.id)=="walt"):
		list.append([stand_near(g,Vector2(262,204),Vector2(300,250),44.0),"That's Walt's spot. He keeps a lantern lit down here and fixes radios for half the Hill. Say hi if you want.",true])
		list.append([stand_near(g,door_at,g.player.position,46.0),"Terrace is up these steps. Door, then "+key(g,"confirm")+".",false])
	else:
		list.append([stand_near(g,door_at,g.player.position,46.0),"This way. Same as before: stand on the door and press "+key(g,"confirm")+".",false])
	return list

static func world_step(g: Node,_moved: float) -> void:
	if guide(g)=="walk" and str(g.state.room)==TERRACE and g.transition_ticks==0 and g.mode==g.Mode.WORLD:
		terrace_scene(g);return
	var sprite: AnimatedSprite2D=npc(g)
	if sprite==null:return
	if guide(g)=="walk" and str(g.state.room)!=TERRACE:
		if not sprite.has_meta("plan"):
			sprite.set_meta("plan",stops(g));sprite.set_meta("stop",0);sprite.set_meta("path",PackedVector2Array())
		step_along(g,sprite,sprite.get_meta("plan"))
	elif sprite.has_meta("goal"):
		if not step_to(g,sprite,Vector2(sprite.get_meta("goal"))):
			sprite.remove_meta("goal");face(sprite,g.player.position)

static func step_along(g: Node,sprite: AnimatedSprite2D,plan: Array) -> void:
	var index: int=int(sprite.get_meta("stop",0))
	if index>=plan.size():
		face(sprite,g.player.position);return
	var stop: Array=plan[index]
	var goal: Vector2=stop[0]
	# He waits for you when you fall behind.
	if g.player.position.distance_to(base(sprite))>WAIT_RANGE and base(sprite).distance_to(goal)>2.0:
		face(sprite,g.player.position);return
	if step_to(g,sprite,goal):return
	face(sprite,g.player.position)
	if not sprite.get_meta("said_%d"%index,false):
		sprite.set_meta("said_%d"%index,true);g.message("Jakerson: "+str(stop[1]))
	# A lesson stop: wait until you come close, then carry on.
	if bool(stop[2]) and g.player.position.distance_to(base(sprite))>64.0:return
	if index<plan.size()-1:
		sprite.set_meta("stop",index+1);sprite.set_meta("path",PackedVector2Array())

## One tick of walking toward goal along the room's navigation. True while moving.
static func step_to(g: Node,sprite: AnimatedSprite2D,goal: Vector2) -> bool:
	var at: Vector2=base(sprite)
	if at.distance_to(goal)<=1.0:return false
	var path: PackedVector2Array=sprite.get_meta("path",PackedVector2Array())
	if path.is_empty() or Vector2(path[-1]).distance_to(goal)>1.0:
		path=g.navigation.route(at,goal)
		if path.is_empty():path=PackedVector2Array([goal])
	while path.size()>1 and at.distance_to(path[0])<1.5:path.remove_at(0)
	var change: Vector2=Vector2(path[0])-at
	var moved: Vector2=change if change.length()<=SPEED else change.normalized()*SPEED
	at+=moved
	sprite.set_meta("path",path)
	move_to(g,sprite,at)
	var facing: String=("left" if moved.x<0 else "right") if absf(moved.x)>absf(moved.y) else ("up" if moved.y<0 else "down")
	pose(sprite,"walk_"+facing)
	# His walk steps with the distance covered (NativeWalkArt), feet on the ground.
	var travelled: float=float(sprite.get_meta("travelled",0.0))+moved.length()
	sprite.set_meta("travelled",travelled)
	NativeWalkArt.step(sprite,travelled)
	sprite.position=at
	return true

static func base(sprite: AnimatedSprite2D) -> Vector2:return Vector2(sprite.get_meta("base",sprite.position))
static func move_to(g: Node,sprite: AnimatedSprite2D,at: Vector2) -> void:
	sprite.set_meta("base",at);sprite.position=at
	var zone: Area2D=area(g)
	if zone!=null:
		zone.position=at
		var definition: Dictionary=zone.get_meta("definition");definition.x=at.x;definition.y=at.y
## Plays a pose and keeps the idle breathing from undoing the mirror (main.gd skips "moving" NPCs).
static func pose(sprite: AnimatedSprite2D,animation: String) -> void:
	if str(sprite.animation)!=animation:sprite.play(animation)
	NativeCastArt.fit(sprite,NativeCastArt.world_height("jakerson"))
	var mirrored: bool=animation.ends_with("left") if SIDE_FACES_RIGHT else animation.ends_with("right")
	if mirrored:
		var t: Texture2D=sprite.sprite_frames.get_frame_texture(sprite.animation,sprite.frame)
		sprite.flip_h=true;sprite.offset.x=-(t.get_width()-float(t.get_meta("foot").x))
	sprite.set_meta("moving",true)
static func face(sprite: AnimatedSprite2D,target: Vector2) -> void:
	var d: Vector2=target-base(sprite)
	var facing: String=("left" if d.x<0 else "right") if absf(d.x)>absf(d.y)*1.4 else ("up" if d.y<0 else "down")
	pose(sprite,"idle_"+facing)
	sprite.position=base(sprite)

# ---------------------------------------------------------------- the terrace and the spar

static func terrace_scene(g: Node) -> void:
	g.state.flags.jakerson_guide="terrace";g.persist()
	if g.state.flags.has("jakerson_resolution"):
		say(g,[["Jakerson","And that's the UMC. Usually it's dead by now.","warm"],
			["Jakerson","...Did that flyer on the door just turn its own page?","concern"],
			["Jules","Doors that think about it. Flyers that read themselves. Is this normal here?","concern"],
			["Jakerson","Not even in finals week. Something in there wants people to stay. ONE MORE MINUTE, every time.","concern"],
			["Jakerson","If something gets in your face tonight, you don't have to beat it. Same as the ping-pong table: listen, make one small promise, keep it, and it lets go.","warm"],
			["Jakerson","I'll be out here if you need a hint. Imani's club room is inside, left side of the atrium.","warm"]],func() -> void:walk_to_spot(g);g.resume_world())
		return
	say(g,[["Jakerson","And that's the UMC. Usually it's dead by now.","warm"],
		["Jakerson","...Did that flyer on the door just turn its own page?","concern"],
		["Jules","Doors that think about it. Flyers that read themselves. Is this normal here?","concern"],
		["Jakerson","Not even in finals week. Something in there wants people to stay. ONE MORE MINUTE, every time.","concern"],
		["Jakerson","If something gets in your face tonight, you don't have to beat it. Listen, make one small promise, keep it, and it lets go.","warm"],
		["Jakerson","Easier to show you. Quick friendly spar? I'll go easy. That's a promise too.","warm"]],func() -> void:spar_offer(g))
static func spar_offer(g: Node) -> void:
	g.jakerson_ui=true
	g.open_menu(g.Mode.MENU,"Jakerson / a friendly spar",[g.option("Sure, show me.",func() -> void:begin_spar(g)),g.option("No time, I have a bus.",func() -> void:
		say(g,[["Jakerson","Fair. I'll be out here if you change your mind. Imani's club room is inside, left side of the atrium.","warm"]],func() -> void:walk_to_spot(g);g.resume_world()))])
static func begin_spar(g: Node) -> void:
	g.jakerson_ui=false
	g.boss_id="jakerson";g.start_battle()
static func walk_to_spot(g: Node) -> void:
	var sprite: AnimatedSprite2D=npc(g)
	if sprite!=null and str(g.state.room)==TERRACE:sprite.set_meta("goal",TERRACE_SPOT);sprite.set_meta("path",PackedVector2Array())

## Coaching before each choice in the spar: one idea at a time, from what just happened.
static func coach(g: Node) -> void:
	var b: Dictionary=g.battle
	var step: int=int(b.get("coached",0))
	b.coached=step+1
	var z: String=key(g,"confirm")
	var lines: Array=[]
	if step==0:
		lines=[["Jakerson","Okay! Each turn you choose one action. Then it's my turn: I attack, and you dodge inside the box.","warm"],
			["Jakerson","STRIKE hits me. CONNECT is talking, and it fills my OPEN bar. At 100 you can RELEASE: the fight ends and nobody gets hurt.","warm"],
			["Jakerson","Try CONNECT, then ask what I'm building.","warm"]]
	elif int(b.openness)>=100:
		lines=[["Jakerson","OPEN is full! CONNECT has a new choice now: RELEASE. Pick it and we're done.","warm"]]
	elif str(g.last_promise_result).begins_with("Promise unfinished"):
		lines=[["Jakerson","So close. Promise again: when a green commit shows up, stand in it and press "+z+".","warm"]]
	elif not bool(b.get("promise_taught",false)):
		b.promise_taught=true
		lines=[["Jakerson","Nice dodging! Close calls charge SYNC, the bar your team's talents run on.","warm"],
			["Jakerson","Now make a promise: CONNECT, then 'Catch three green commits'. During my attack, stand in each green box and press "+z+".","warm"],
			["Jakerson","Keep it and OPEN jumps way up.","warm"]]
	else:
		lines=[["Jakerson","GUARD halves the damage you take and charges SYNC. The last CONNECT choice sets a limit: you say when it ends, and my attack goes easier.","warm"],
			["Jakerson","Whatever you pick, OPEN is what ends this nicely.","warm"]]
	g.dialogue(lines,func() -> void:g.command_menu())

static func after_spar(g: Node) -> void:
	var peaceful: bool=str(g.state.flags.get("jakerson_resolution",""))=="peaceful"
	g.boss_id=""
	g.enter_room(str(g.state.room),Vector2(g.state.x,g.state.y),false)
	if NativeMoveIn.active(g):NativeMoveIn.aftermath(g,peaceful);return
	var lines: Array=[["Jakerson","See? You never knocked me over. You kept one promise and the fight just... ended.","warm"],
		["Jakerson","STRIKE works too. But things around here remember being hit.","neutral"]] if peaceful else [["Jakerson","Ow. Okay, that works too.","concern"],
		["Jakerson","But things around here remember being hit. Next time, try keeping a promise instead.","neutral"]]
	lines.append(["Jakerson","Go return that mixer. Imani's club room is inside, left side of the atrium. I'll be out here if you need a hint.","warm"])
	say(g,lines,func() -> void:
		g.state.flags.aftermath_pending="";g.persist();walk_to_spot(g);g.resume_world())

# ---------------------------------------------------------------- talking to him

static func observe_map(_g: Node) -> void:pass
static func hint(g: Node) -> String:
	if guide(g)!="walk":return ""
	return "Follow Jakerson to the UMC. Walk: "+move_keys(g)+". Read things and open doors: "+key(g,"confirm")+"."
static func handle(g: Node,object: Dictionary) -> bool:
	if str(object.id) in ["jakerson_graduation","jakerson_match"]:
		if g.state.flags.has("jakerson_final_resolution"):say(g,[["Jakerson","You passed. I'm framing the bruise.","warm"]],func() -> void:g.resume_world())
		elif str(object.id)=="jakerson_match":say(g,[["Jakerson","Ready? Same rules as the terrace. I just have more of them now.","warm"]],func() -> void:rematch_offer(g))
		else:say(g,[["Jakerson","Courts are through the gate on the right. Go on, I'll catch up.","warm"]],func() -> void:g.resume_world())
		return true
	if object.id!="jakerson":return false
	if str(g.state.room)=="M06" and g.state.flags.get("graduation_day",false):
		if g.state.flags.has("jakerson_final_resolution"):say(g,[["Jakerson","You passed. I'm framing the bruise.","warm"]],func() -> void:g.resume_world())
		else:rematch_offer(g)
		return true
	if guide(g)=="walk":
		say(g,[["Jakerson","Almost there. Stick with me.","warm"]],func() -> void:g.resume_world());return true
	if not g.state.flags.get("jakerson_seen",false):
		g.state.flags.jakerson_seen=true;g.persist()
		say(g,[["Jakerson","Hey, I'm Jakerson. Computer science. Need a hand finding your way?","warm"]],func() -> void:menu(g))
	else:menu(g)
	return true
static func menu(g: Node) -> void:
	g.jakerson_ui=true
	var options: Array=[g.option("What should I do next?",func() -> void:next_tip(g)),g.option("Remind me how this works.",func() -> void:remind(g)),g.option("Any tips?",func() -> void:tips(g))]
	if not g.state.flags.has("jakerson_resolution"):
		options.append(g.option("Spar with me? (practice fight)",func() -> void:begin_spar(g)))
	options.append_array([g.option("Just saying hi.",func() -> void:say(g,[["Jakerson","Helping someone else is a great excuse to avoid my own assignments.","warm"]],func() -> void:menu(g))),g.option("Leave it for now",func() -> void:leave(g))])
	g.open_menu(g.Mode.MENU,"Jakerson / one thing at a time",options)
static func next_tip(g: Node) -> void:
	say(g,[["Jakerson",next_place(g),"neutral"]],func() -> void:menu(g))
static func remind(g: Node) -> void:
	say(g,[["Jakerson",controls(g),"neutral"],["Jakerson",controller_controls(g),"neutral"],["Jakerson","Talk, read and open doors with "+g.binding_label("confirm","all")+" nearby, or click. Map is the Map button or "+g.binding_label("menu","all")+" then Campus map.","neutral"],["Jakerson","In a fight, CONNECT fills OPEN, a kept promise fills it fast, and at 100 RELEASE ends it kindly.","warm"]],func() -> void:menu(g))
static func tips(g: Node) -> void:
	var text: String="Follow the arrow to the next door. One mixer is plenty for now."
	if g.state.flags.get("walt_joined",false):text="Guard helps build shared SYNC. A small promise creates a real task during defense. Everyone can do a part."
	if g.state.flags.get("dawn_started",false):text="You can keep exploring. Nobody needs the evening to start over."
	say(g,[["Jakerson",text,"warm"]],func() -> void:menu(g))

# ---------------------------------------------------------------- drop-ins
## He jogs in from a door, teaches one thing right before you need it, and jogs off.
## Each fires once (flag "jakerson_drop_<id>"). The player holds still meanwhile.

static func busy() -> bool:return not scene.is_empty()
static func drop_lines(g: Node,id: String) -> Array:
	var z: String=key(g,"confirm")
	match id:
		"party":
			var basics: Array=[] if g.state.flags.has("jakerson_resolution") else [["Jakerson","You skipped my tour, so here's the thirty-second version.","warm"],
				["Jakerson","In a fight, everyone picks one action, then you dodge in the box. STRIKE hurts. CONNECT fills OPEN, and at 100, RELEASE ends it kindly.","warm"],
				["Jakerson","A promise like \"keep the light through three gusts\" gives you a job in the next attack. Keep it and OPEN jumps.","warm"]]
			return [["Jakerson","Whoa, you two! Quick thing before you go.","warm"]]+basics+[
				["Jakerson","With two of you, everyone picks an action each turn. Then you dodge together, and the hits take turns landing on each of you.","warm"],
				["Jakerson","Imani's TALENTS run on SYNC: Steady Refrain heals or picks someone back up, Half Time slows the attack down.","warm"],
				["Jakerson","Close dodges and GUARD charge SYNC. Okay, bye! Go get your voice back.","warm"]]
		"lob":
			return [["Jakerson","Hey! Late hit with the tennis club. The courts have lights. Heads up: the wind under this bridge is about to get rough.","warm"],
				["Jakerson","Some attacks turn you blue. Blue means gravity: you fall.","warm"],
				["Jakerson","Press "+key(g,"move_up")+" or "+z+" to jump, and hold it to go higher. Like a lob: read where it lands, then move.","warm"],
				["Jakerson","And GUARD isn't hiding. It charges SYNC for the whole team. My doubles partner's waiting, gotta go!","warm"]]
		"keepsake":
			return [["Jakerson","Ooh, a keepsake! Each one helps one person in their own way.","warm"],
				["Jakerson","Open Pause, then Party, and choose who wears it. One each.","warm"],
				["Jakerson","Imani's guitar pick makes close dodges on the beat worth double SYNC. Walt's gear helps him shelter people. Jules's stuff keeps Jules standing.","warm"]]
		"limit":
			return [["Jakerson","Lost property, huh. Things in here really hold on.","concern"],
				["Jakerson","Remember the third CONNECT choice? That's setting a limit: you say where it ends.","warm"],
				["Jakerson","Set one and the next attack goes easier on everybody. You don't owe anything your whole night.","warm"]]
		"beat":
			return [["Jakerson","Listen. The music out here has a beat, and so does whatever's on that stage.","warm"],
				["Jakerson","From here on, attacks land on the beat. Count along and move on it.","warm"],
				["Jakerson","Green cues open right on the downbeat. Be there when they do.","warm"]]
	return []
static func drop_due(g: Node) -> String:
	var f: Dictionary=g.state.flags
	var room: String=str(g.state.room)
	if f.get("chapter1_complete",false):return ""
	if f.get("imani_joined",false) and not f.get("walt_joined",false) and room=="U03" and not f.get("jakerson_drop_party",false):return "party"
	if f.get("imani_joined",false) and not f.get("walt_joined",false) and not f.get("jakerson_drop_lob",false):
		for o: Dictionary in g.rooms[room].objects:
			if str(o.id)=="walt":return "lob"
	if not f.get("jakerson_drop_keepsake",false):
		for id: String in PartyGrowth.KEEPSAKES:
			if PartyGrowth.found(f,id):return "keepsake"
	if room=="U07" and not f.has("claim_resolution") and not f.get("jakerson_drop_limit",false):return "limit"
	if room=="F06" and not f.has("encore_resolution") and not f.get("jakerson_drop_beat",false):return "beat"
	return ""
## The door to jog in from: the room's nearest door that is not right on top of you.
static func entry_point(g: Node) -> Vector2:
	var best: Vector2=g.player.position+Vector2(-150,0)
	var cost: float=INF
	for o: Dictionary in g.rooms[str(g.state.room)].objects:
		if str(o.kind)!="door":continue
		var at: Vector2=Vector2(float(o.x),float(o.y))
		var d: float=at.distance_to(g.player.position)
		if d>=40.0 and d<cost:cost=d;best=at
	return best
static func outfit_frames(tennis: bool) -> SpriteFrames:
	return NativeJakersonArt.frames_for("tennis") if tennis else NativeCastArt.frames("jakerson")
## Called at the top of world_tick. True while a drop-in holds the world still.
static func cutscene_step(g: Node) -> bool:
	if scene.is_empty():
		if g.transition_ticks>0 or g.mode!=g.Mode.WORLD or guide(g)=="walk":return false
		var id: String=drop_due(g)
		if id.is_empty():return false
		g.state.flags["jakerson_drop_"+id]=true;g.persist()
		var sprite:=AnimatedSprite2D.new()
		sprite.sprite_frames=outfit_frames(id=="lob")
		sprite.set_meta("id","jakerson_drop");sprite.set_meta("idle_height",NativeCastArt.world_height("jakerson"))
		sprite.z_index=g.player.z_index
		var door: Vector2=entry_point(g)
		g.world.add_child(sprite);g.world_npcs.append(sprite)
		sprite.set_meta("base",door);sprite.position=door
		g.player.walk(Vector2.ZERO,false,0.0)
		scene={"id":id,"sprite":sprite,"phase":"in","door":door,"path":PackedVector2Array()}
		g.audio.combat("pick")
		return true
	var sprite: AnimatedSprite2D=scene.sprite
	if not is_instance_valid(sprite):scene={};return false
	match str(scene.phase):
		"in":
			var side: float=-1.0 if Vector2(scene.door).x<g.player.position.x else 1.0
			var goal: Vector2=g.navigation.safe_point(g.player.position+Vector2(30.0*side,0))
			if not jog(g,sprite,goal):
				face(sprite,g.player.position)
				g.player.facing="left" if side<0 else "right";g.player.art.play("idle_"+g.player.facing)
				scene.phase="talk"
				var id: String=str(scene.id)
				g.dialogue(drop_lines(g,id),func() -> void:
					scene.phase="out";sprite.set_meta("path",PackedVector2Array());g.resume_world())
		"out":
			if not jog(g,sprite,Vector2(scene.door)):
				g.world_npcs.erase(sprite);sprite.queue_free();scene={}
				return false
	return true
static func jog(g: Node,sprite: AnimatedSprite2D,goal: Vector2) -> bool:
	var at: Vector2=base(sprite)
	if at.distance_to(goal)<=2.0:return false
	var path: PackedVector2Array=sprite.get_meta("path",PackedVector2Array())
	if path.is_empty() or Vector2(path[-1]).distance_to(goal)>2.0:
		path=g.navigation.route(at,goal)
		if path.is_empty():path=PackedVector2Array([goal])
	while path.size()>1 and at.distance_to(path[0])<2.5:path.remove_at(0)
	var change: Vector2=Vector2(path[0])-at
	var moved: Vector2=change if change.length()<=JOG else change.normalized()*JOG
	at+=moved;sprite.set_meta("path",path)
	sprite.set_meta("base",at)
	var facing: String=("left" if moved.x<0 else "right") if absf(moved.x)>absf(moved.y) else ("up" if moved.y<0 else "down")
	pose(sprite,"walk_"+facing)
	var travelled: float=float(sprite.get_meta("travelled",0.0))+moved.length()
	sprite.set_meta("travelled",travelled)
	NativeWalkArt.step(sprite,travelled,true)
	sprite.position=at
	return true

# ---------------------------------------------------------------- graduation

## After the dawn, the epilogue: graduation day, years later, then a last friendly match.
static func graduation(g: Node) -> void:
	var f: Dictionary=g.state.flags
	# Folsom Field (G01) and the tennis courts (G02) come from the visuals lane; Macky's stage is the fallback.
	var field: bool=g.rooms.has("G01") and g.rooms.has("G02")
	f.graduation_day=true;f.jakerson_outfit="";g.persist()
	if field:g.enter_room("G01",Vector2(500,486),false)
	else:g.enter_room("M06",Vector2(420,404),false)
	var place: String=("Folsom Field" if field else "Macky Auditorium")
	var lines: Array=[["Loudspeaker","Four years later. "+place+", in daylight. Commencement.","neutral"],
		["Loudspeaker","Jules Navarro.","warm"],
		["Imani","WOOO! That's my bus buddy!","warm"],
		["Walt","I brought the lantern. It's daytime. It still felt right.","warm"],
		["Loudspeaker","Jakerson. Computer science.","warm"],
		["Jakerson","Four years ago you were running for a bus with somebody else's mixer.","warm"],
		["Jules","And you walked me to the UMC and then made me fight you.","warm"],
		["Jakerson","Friendly spar! Look how that turned out.","warm"],
		["Jakerson","One more? For old times. One last friendly set, everything I ever showed you. Loser buys the boba.","warm"]]
	if f.get("movein_done",false):
		var order: String=NativeMoveIn.boba(f)
		lines=[["Loudspeaker","Commencement. "+place+", in daylight.","neutral"],
			["Loudspeaker","Jules Navarro.","warm"],
			["Imani","WOOO! That's my bus buddy!","warm"],
			["Walt","I brought the lantern. It's daytime. It still felt right.","warm"],
			["Loudspeaker","Jakerson. Computer science.","warm"],
			["Jakerson","Four years ago you asked if I snored. Last night I walked you to the UMC like it was move-in day again.","warm"],
			["Jules","You snore. And you only walked me so you wouldn't have to carry the mixer.","warm"],
			["Jakerson","Details. Remember what we shook on in the lobby? One real match, you and me. Loser buys the boba"+(". I remember you're ordering "+order+"." if not order.is_empty() else "."),"warm"]]
	if not field:
		say(g,lines,func() -> void:rematch_offer(g));return
	lines.append_array([["Jakerson","I booked the courts. Give me two minutes to lose the gown.","warm"],["Imani","He's been carrying a racket under that gown all morning.","warm"]])
	say(g,lines,func() -> void:
		f.jakerson_outfit="tennis";g.persist()
		g.enter_room("G01",g.player.position,false);g.resume_world()
		g.message("Jakerson is waiting on the tennis courts, through the gate on the right."))
static func rematch_offer(g: Node) -> void:
	g.jakerson_ui=true
	g.open_menu(g.Mode.MENU,"Jakerson / one last friendly match",[g.option("One last spar.",func() -> void:
		g.jakerson_ui=false;g.boss_id="jakerson_final";g.start_battle()),g.option("Maybe after the photos.",func() -> void:
		say(g,[["Jakerson","I'll be right here. In a gown. Stretching.","warm"]],func() -> void:g.resume_world()))])
static func after_final(g: Node) -> void:
	var f: Dictionary=g.state.flags
	var peaceful: bool=str(f.get("jakerson_final_resolution",""))=="peaceful"
	g.boss_id=""
	g.enter_room(str(g.state.room),Vector2(g.state.x,g.state.y),false)
	var lines: Array=[["Jakerson","Okay, okay! You passed. With honors.","warm"],
		["Jakerson","Funny. I spent four years teaching you how things work, and you three taught me when to stop.","warm"]] if peaceful else [["Jakerson","Ow! Okay. Passed. Maybe a little too well.","concern"],
		["Jakerson","Kidding. Mostly. You still kept your promises when it counted.","warm"]]
	var order: String=NativeMoveIn.boba(f)
	if f.get("movein_done",false) and not order.is_empty():
		lines.append(["Jakerson","So who lost? Nobody. Which means we both buy. One "+order+", one for me, and I pay first. Rule forty-two.","warm"] if peaceful else ["Jakerson","So I lost, officially. One "+order+" coming up. Rule forty-two: always pay your bets.","warm"])
	lines.append_array([["Imani","Group photo! Before anyone gets sentimental.","warm"],["Walt","Too late.","warm"],["Jules","One more minute. Then we go.","warm"]])
	say(g,lines,func() -> void:
		f.graduation_complete=true;f.aftermath_pending="";g.persist();NativeFinalCampaign.ending_menu(g))
