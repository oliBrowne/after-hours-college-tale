extends "res://scenes/qa_opening.gd"
## Actual-input route for the opening walk with Jakerson and the practice spar.
## --qa-jakerson runs it; --qa-remapped and --qa-pad still check the control text.
## AFTER_HOURS_VIDEO=<dir> saves every second frame for a clip (see qa_opening.gd).

func run(main: Node) -> bool:
	game=main;folder=OS.get_environment("AFTER_HOURS_QA")
	if not video.is_empty(): DirAccess.make_dir_recursive_absolute(video)
	await _choose("Settings")
	if "--qa-remapped" in OS.get_cmdline_user_args():
		await _choose("Remap keyboard");await _choose("Confirm / interact")
		_keyboard(KEY_W,true);await _frame();_keyboard(KEY_W,false);await _frame()
		await _choose("Move left")
		_keyboard(KEY_J,true);await _frame();_keyboard(KEY_J,false);await _frame()
		_assert(game.binding_label("confirm")=="W" and game.binding_label("move_up")=="Up" and game.binding_label("move_left")=="J","Actual remap menus replace movement and remove conflicting W default")
		_assert(NativeJakerson.controls(game).contains("Up: Up.") and NativeJakerson.controls(game).contains("Left: J."),"Tutorial reports actual partial bindings without unavailable defaults")
		await _press("cancel")
	await _choose("Back");await _choose("Begin the evening")
	await _movein()
	_assert(int(game.mode)==MENU and game.jakerson_ui,"Four years later the evening opens on Jakerson's greeting and walk offer")
	_assert(str(game.dialogue_lines[1][0])=="Jakerson","Jakerson is the first NPC greeting")
	await _capture("01-first-npc-greeting");await _settle()
	_assert(str(game.caption).begins_with("Jakerson / walk"),"Jakerson offers to walk you to the UMC")
	await _choose("Lead the way")
	_assert(NativeJakerson.guide(game)=="walk" and int(game.mode)==WORLD,"Walk starts in the world, not a menu")
	_assert(not NativeJakerson.hint(game).is_empty(),"The world shows a follow hint during the walk")
	var inventory: Dictionary=game.state.inventory.duplicate(true)
	# Follow him: stay a short way behind until he has made every stop in the room.
	while str(game.state.room)!="U02" and not failed:
		var room: String=str(game.state.room)
		var start: int=ticks
		while not failed:
			var sprite: AnimatedSprite2D=NativeJakerson.npc(game)
			if sprite==null:_assert(false,"Jakerson is present in "+room);break
			var plan: Array=sprite.get_meta("plan",[])
			var last: int=plan.size()-1
			var at: Vector2=NativeJakerson.base(sprite)
			if not plan.is_empty() and int(sprite.get_meta("stop",0))==last and at.distance_to(plan[last][0])<2.0:break
			var gap: Vector2=at-game.player.position
			if int(game.mode)!=WORLD:await _settle()
			elif gap.length()>40:_axis(gap.normalized())
			else:_release()
			await _frame()
			if ticks-start>2400:_assert(false,"Jakerson's walk stalled in "+room+" at "+str(at));break
		_release()
		if failed:break
		await _capture("02-walk-"+room)
		var door: Dictionary=NativeJakerson.exit_door(game,room)
		_assert(not door.is_empty(),"Route continues from "+room)
		if failed:break
		# Walking onto a door no longer opens it.
		await _walk(Vector2(float(door.x),float(door.y)),4)
		for _i: int in range(40):await _frame()
		_assert(str(game.state.room)==room,"Standing on "+str(door.id)+" does not open it")
		await _capture("03-door-prompt-"+room)
		await _press()
		for _i: int in range(4):await _frame()
		_assert(str(game.state.room)==str(door.to),"Confirm on "+str(door.id)+" opens it")
	for _i: int in range(30):await _frame()
	_assert(int(game.mode)==DIALOGUE and str(game.dialogue_lines[0][0])=="Jakerson","Terrace scene starts on arrival")
	await _settle()
	_assert(NativeJakerson.guide(game)=="terrace" and int(game.mode)==WORLD and str(game.state.room)=="U02","On the terrace, no second spar: the dorm already taught it")
	_assert(game.state.inventory==inventory,"The walk and spar cost no supplies")
	# With no spar to re-enter the room, he walks to his spot by the medallion; wait for him there.
	for _i: int in range(600):
		var jakerson: AnimatedSprite2D=NativeJakerson.npc(game)
		if jakerson!=null and not jakerson.has_meta("goal"):break
		await _frame()
	for _i: int in range(60):await _frame()
	await _capture("06-terrace-after")
	await _object("jakerson");await _settle()
	_assert(str(game.caption).begins_with("Jakerson / one thing"),"Terrace Jakerson opens the help menu")
	_assert(not game.menu_options.any(func(o: Dictionary) -> bool:return str(o.label).begins_with("Spar")),"No second spar offer after the spar")
	await _choose("What should I do next");await _settle();await _choose("Leave it for now")
	_assert(int(game.mode)==WORLD and not game.jakerson_ui,"Leaving the help menu returns to the world")
	await _door("main_entrance","U03")
	_release();_log("FAIL" if failed else "PASS Jakerson walk and practice spar route")
	_write_trace();return not failed

## Room objects plus the ones added in code (Jakerson on the terrace).
func _definition(id: String) -> Dictionary:
	for zone: Area2D in game.areas:
		if str(zone.get_meta("definition").get("id",""))==id:return zone.get_meta("definition")
	return super._definition(id)
func _key(action: String) -> int:
	for event: InputEvent in InputMap.action_get_events(action):
		if event is InputEventKey:return event.physical_keycode if event.physical_keycode!=0 else event.keycode
	return 0
func _keyboard(code: int,pressed: bool) -> void:
	var event:=InputEventKey.new();event.physical_keycode=code;event.keycode=code;event.pressed=pressed
	# Viewport injection delivers key events but does not maintain held keys.
	# Resolve held actions through the real configured InputMap, then dispatch
	# the same physical key event locally; never change player/cursor state.
	for action: StringName in InputMap.get_actions():
		if event.is_action(action):
			if pressed:Input.action_press(action)
			else:Input.action_release(action)
	game.get_viewport().push_input(event,true)
func _event(action: String,pressed: bool) -> void:
	if "--qa-pad" in OS.get_cmdline_user_args():
		for binding: InputEvent in InputMap.action_get_events(action):
			if binding is InputEventJoypadButton:
				var event:=InputEventJoypadButton.new();event.button_index=binding.button_index;event.pressed=pressed
				if pressed:Input.action_press(action)
				else:Input.action_release(action)
				game.get_viewport().push_input(event,true);return
	_keyboard(_key(action),pressed)
func _stick(axis: int,value: float) -> void:
	var event:=InputEventJoypadMotion.new();event.axis=axis;event.axis_value=value
	for direction: String in ["move_up","move_down","move_left","move_right"]:
		for binding: InputEvent in InputMap.action_get_events(direction):
			if binding is InputEventJoypadMotion and binding.axis==axis:
				if value!=0 and signf(value)==signf(binding.axis_value):Input.action_press(direction,absf(value))
				else:Input.action_release(direction)
	game.get_viewport().push_input(event,true)
func _write_trace() -> void:
	if folder.is_empty():return
	var file: FileAccess=FileAccess.open(folder.path_join("jakerson-trace.txt"),FileAccess.WRITE)
	if file:file.store_string("\n".join(trace));file.close()
