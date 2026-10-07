extends SceneTree
var checks: int=0
var failures: int=0
func check(ok: bool,message: String) -> void:
	checks+=1
	if not ok:failures+=1;print("FAIL ",message)
func drain(g: Node) -> void:
	for i: int in range(40):
		if g.mode!=g.Mode.DIALOGUE:break
		g.reveal=10000;g.advance_dialogue()
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var g: Node=load("res://scenes/main.tscn").instantiate();root.add_child(g)
	g.qa=true;g.saves=NativeSaveService.new("user://chapter3-focused/saves");g.preferences_path="user://chapter3-focused/preferences.json"
	g.state.flags={"imani_joined":true,"walt_joined":true,"chapter1_complete":true,"chapter2_complete":true}
	g.enter_room("O04",Vector2(120,410),false);NativeChapterThree.handle(g,{"id":"todd"});drain(g)
	check(g.mode==g.Mode.WORLD and not g.state.flags.has("todd_resolution"),"No Todd fight before origin and finite plan")
	g.state.flags.booth_origin=true;NativeChapterThree.handle(g,{"id":"todd"});drain(g)
	check(g.mode==g.Mode.WORLD,"Origin alone cannot replace consent choice")
	g.enter_room("O01",Vector2(120,445),false);g.state.flags.erase("booth_origin");NativeChapterThree.handle(g,{"id":"rook"});drain(g)
	check(not g.state.flags.get("rook_confessed",false),"Rook confession cannot skip source revelation")
	g.state.flags.booth_origin=true;NativeChapterThree.handle(g,{"id":"rook"});drain(g)
	check(g.state.flags.rook_confessed,"Full confession records witnessed source/fear")
	g.enter_room("O04",Vector2(120,410),false);g.state.flags.finite_plan="shared-duties"
	for outcome: String in ["peaceful","forceful"]:
		g.state.flags.todd_resolution=outcome;g.state.flags.aftermath_pending="todd";g.state.flags.erase("chapter3_complete")
		check(g.persist(),outcome+" pending Todd checkpoint writes")
		var before: Dictionary=g.saves.load_slot("auto").state
		g.restore_state(before)
		check(g.mode==g.Mode.DIALOGUE and g.state.flags.aftermath_pending=="todd",outcome+" normal disk restore replays full Todd hook")
		check(not g.state.flags.get("chapter3_complete",false),outcome+" cannot finish chapter before hook")
		drain(g)
		check(g.state.flags.chapter3_complete and g.state.flags.aftermath_pending=="",outcome+" completes finite plan without denying story route")
		check(g.state.party[2].id=="walt",outcome+" preserves Walt party slot")
	var flags: Dictionary=g.state.flags.duplicate(true);g.enter_room("O02",Vector2(120,400),false)
	check(not NativeChapterThree.handle(g,{"id":"office","kind":"door"}),"Chapter 3 handler leaves doors to the navigation controller")
	check(g.state.flags==flags or g.state.flags.get("visited_O02",false),"Door dispatch adds no story progression")
	g.audio.shutdown();g.dialogue_callback=Callable();g.menu_options.clear();g.pause_options.clear();g.dialogue_choices.clear();g.queue_free();await process_frame
	print("Chapter 3 focused checks: ",checks,", failures: ",failures);quit(0 if failures==0 else 1)
