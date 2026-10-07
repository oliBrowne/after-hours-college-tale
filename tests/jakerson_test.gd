extends SceneTree
var checks: int=0
var failures: int=0
func _initialize() -> void:call_deferred("run")
func check(ok: bool,text: String) -> void:
	checks+=1
	if not ok:failures+=1;print("FAIL ",text)
func run() -> void:
	var folder: String=OS.get_environment("AFTER_HOURS_JAKERSON_QA")
	DirAccess.make_dir_recursive_absolute(folder)
	var g: Node=load("res://scenes/main.tscn").instantiate();root.add_child(g)
	g.qa=true;g.preferences_path=folder.path_join("preferences.json");g.saves=NativeSaveService.new(folder.path_join("saves"))
	var old: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("AFTER_HOURS_OLD_SAVE")))
	check(NativeSaveService.validate_state(old),"Earned approved baseline save remains schema-valid")
	g.restore_state(old)
	check(g.mode==g.Mode.WORLD and not g.jakerson_ui and not NativeJakerson.active(g),"Old completed save loads without forced introduction or tutorial")
	check(g.state.flags.get("dawn_complete",false) and g.state.flags.get("ending","")=="release","Old terminal campaign state retained")
	check(NativeJakerson.next_place(g).contains(NativeCampaign.objective(g.state)) and not NativeJakerson.next_place(g).contains("club room for Imani"),"Old-save completion guidance uses current campaign objective")
	var stock: Dictionary=g.state.inventory.duplicate(true)
	var definition: Dictionary={}
	for object: Dictionary in g.rooms.U01.objects:
		if object.id=="jakerson":definition=object
	check(not definition.is_empty() and g.navigation.object_route(g.player.position,definition).size()>0,"Guide has a real reachable interaction approach")
	g.interact(definition)
	check(g.mode==g.Mode.DIALOGUE and g.dialogue_lines[0][0]=="Jakerson","Legacy arrival offers voluntary help when interacted with")
	NativeJakerson.leave(g)
	NativeJakerson.tips(g)
	check(str(g.dialogue_lines[0][1]).contains("keep exploring") and not str(g.dialogue_lines[0][1]).contains("Guard"),"Dawn tips reflect already completed progress")
	NativeJakerson.leave(g)
	check(g.state.inventory==stock,"Greeting/tips do not grant any supplies")
	g.new_game();g.finish_arrival(true)
	check(not g.state.flags.has("jakerson_step") and not g.jakerson_ui,"Skipping arrival does not invent tutorial progress")
	Input.action_press("move_up");g.state.settings.bindings={"confirm":KEY_W,"move_left":KEY_J};g.configure_input()
	check(not Input.is_action_pressed("move_up"),"Changing key mappings clears a formerly held movement")
	check(g.binding_label("move_up")=="Up" and g.binding_label("move_left")=="J" and g.binding_label("confirm")=="W","Displayed controls reflect partial remap and removed conflicts")
	var key:=InputEventKey.new();key.physical_keycode=KEY_W;key.pressed=true
	check(key.is_action_pressed("confirm") and not key.is_action_pressed("move_up"),"Remapped physical confirm is not also old W movement")
	NativeJakerson.start(g)
	check(NativeJakerson.guide(g)=="walk" and str(g.notice).contains(" J ") and NativeJakerson.hint(g).contains(" J "),"Walk starts with actual configured direction labels")
	check(NativeJakerson.route_rooms(g).front()=="U01" and NativeJakerson.route_rooms(g).back()=="U02" and not NativeJakerson.exit_door(g,"U01").is_empty(),"Walk follows the real door route to the terrace")
	NativeJakerson.leave(g)
	check(g.mode==g.Mode.WORLD and not g.jakerson_ui,"Leaving restores exploration")
	check(g.binding_label("confirm","all").contains("W") and g.binding_label("confirm","controller")=="Pad A/Cross","Controller confirm is derived alongside remapped keyboard")
	check(g.binding_label("cancel","controller")=="Pad B/Circle" and g.binding_label("menu","controller")=="Pad Y/Triangle","Controller cancel and map menu mappings displayed")
	check(NativeJakerson.controller_controls(g).contains("D-pad up") and NativeJakerson.controller_controls(g).contains("Left stick down"),"Both configured controller movement methods displayed")
	var pad:=InputEventJoypadButton.new();pad.button_index=JOY_BUTTON_A;pad.pressed=true
	check(pad.is_action_pressed("confirm"),"Real controller event matches remapped confirm InputMap")
	var altered:=InputEventJoypadButton.new();altered.button_index=JOY_BUTTON_X
	InputMap.action_erase_events("confirm");InputMap.action_add_event("confirm",altered)
	check(g.binding_label("confirm","controller")=="Pad X/Square" and not g.binding_label("confirm","all").contains("A/Cross"),"Prompt follows actual modified controller event rather than hardcoded action")
	g.configure_input()
	var frames: SpriteFrames=NativeJakersonArt.frames()
	for name: String in ["idle_down","idle_up","idle_right","interact_down","settled"]:
		check(frames.has_animation(name),"Guide includes "+name)
	var sprite: AnimatedSprite2D=AnimatedSprite2D.new();sprite.sprite_frames=frames;root.add_child(sprite);sprite.play("idle_down");sprite.position=Vector2(132,249)
	NativeIdleMotion.apply(sprite,60,0,false,4);var feet: Vector2=sprite.position
	NativeIdleMotion.apply(sprite,60,1,false,4)
	check(sprite.position==feet and sprite.offset==-Vector2(sprite.sprite_frames.get_frame_texture(sprite.animation,sprite.frame).get_meta("foot")),"Tall body uses measured grounded feet during breathing")
	for face: int in range(4):check(NativeJakersonArt.portrait(face)!=null,"Distinct dialogue expression "+str(face))
	check(NativeCastArt.portrait("Jakerson",1)==NativePixelCast.portrait(NativeJakersonArt.portrait(1)),"Dialogue uses integrated guide portraits")
	check(g.state.party[2].id=="walt" and not g.state.flags.get("walt_joined",false),"Guide does not change party or first-boss progression")
	sprite.queue_free();g.audio.shutdown();g.queue_free();await process_frame
	print("Jakerson focused checks: ",checks,", failures: ",failures);quit(0 if failures==0 else 1)
