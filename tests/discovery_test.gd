extends SceneTree
var game: Node
var checks: int = 0
var failures: int = 0
func check(value: bool, label: String) -> void:
	checks += 1
	if not value: failures += 1; print("FAIL ", label)
func _initialize() -> void: call_deferred("run")
func finish() -> void:
	for _i: int in range(40):
		if game.mode != game.Mode.DIALOGUE: break
		game.advance_dialogue()
func object(id: String) -> Dictionary:
	for area: Area2D in game.areas:
		var item: Dictionary = area.get_meta("definition")
		if item.id == id: return item
	return {}
func run() -> void:
	var folder: String = OS.get_environment("AFTER_HOURS_FIXTURE")
	if folder.is_empty(): quit(2); return
	DirAccess.make_dir_recursive_absolute(folder)
	game = load("res://scenes/main.tscn").instantiate()
	game.preferences_path = folder.path_join("preferences.json")
	game.saves = NativeSaveService.new(folder.path_join("saves"))
	root.add_child(game); game.set_physics_process(false)
	game.state = NativeState.fresh()
	game.state.flags = {"imani_joined":true, "walt_joined":true, "cal_joined":true, "mixer_returned":true, "booth_seen":true}
	var inventory: Dictionary = game.state.inventory.duplicate(true)
	var party: Array = game.state.party.duplicate(true)
	for fixture: Array in [["U01","bike","discovery_bike_seen"],["U02","eli","discovery_eli_acknowledged"],["U04","stage","discovery_cuesheet_seen"],["U05","mags_checklist","discovery_mags_checklist_seen"],["U06","arcade_button","discovery_arcade_seen"],["U07","lost_labels","discovery_lostlabels_seen"]]:
		var room: Dictionary = game.rooms[fixture[0]]
		game.enter_room(fixture[0], Vector2(room.entry[0], room.entry[1]), false)
		game.interact(object(fixture[1]))
		check(game.mode == game.Mode.DIALOGUE and game.dialogue_lines.size() <= 4, str(fixture[1]) + " short discovery")
		check(not game.state.flags.get(fixture[2], false), str(fixture[1]) + " interrupted dialogue has no completed flag")
		if fixture[1] == "eli": check(str(game.dialogue_lines).contains("Once for the brake"), "Eli payoff wins over mixer-returned repeat")
		finish()
		check(game.state.flags.get(fixture[2], false), str(fixture[1]) + " flag commits after dialogue")
		check(game.state.inventory == inventory and game.state.party == party, str(fixture[1]) + " no resources or stats awarded")
		check(game.saves.load_slot("auto").state.flags.get(fixture[2], false), str(fixture[1]) + " automatic save persists flag")
		game.interact(object(fixture[1])); finish()
		check(game.state.inventory == inventory and game.state.party == party, str(fixture[1]) + " repeat remains resource-neutral")
		await process_frame
	check(game.saves.export_file(folder.path_join("portable.json"), game.state) == OK, "Discoveries export")
	var portable: Dictionary = game.saves.import_file(folder.path_join("portable.json"))
	check(not portable.has("error") and portable.state.flags == game.state.flags, "Discoveries survive portable import")
	for id: String in ["stage", "mags_checklist", "arcade_button", "lost_labels"]:
		var solo: Dictionary = NativeState.fresh()
		var scene: Dictionary = NativeDiscoveries.scene(id, solo, ["Jules"])
		check(scene.complete == ["discovery_lostlabels_seen"] if id == "lost_labels" else scene.complete.is_empty(), id + " absent speakers do not perform physical actions; read labels can be marked seen")
		for line: Array in scene.lines: check(line[0] == "Jules", id + " absent speakers never speak")
	var absent_eli: Dictionary = NativeDiscoveries.scene("eli", NativeState.fresh(), ["Jules"])
	check(absent_eli.complete.is_empty() and absent_eli.lines[0][0] == "Jules", "Absent Eli has explicit factual fallback without acknowledgement")
	for outcome: String in ["peaceful", "forceful"]:
		game.state.flags.claim_resolution = outcome; game.state.flags.pinpal_resolution = outcome; game.state.flags.flyer_resolution = outcome
		game.state.flags.pip_joined = true; game.state.flags.opening_finished = true
		game.enter_room("U07", Vector2(360,405), false)
		check("Mags" in game.living_speakers(), "Mags physically present for " + outcome + " cleanup")
		for id: String in ["claim", "spool", "pip", "lost_labels"]:
			game.interact(object(id)); var text: String = str(game.dialogue_lines)
			check(not text.contains("owner") and not text.contains("already kept"), id + " late " + outcome + " text follows actual state")
			if id == "pip": check(text.contains("Gone with the people"), "Pip interaction becomes departure note")
			finish()
		game.state.flags.aftermath_pending = "pinpal"
		game.enter_room("U06", Vector2(620,380), false)
		game.show_aftermath("pinpal")
		check(str(game.dialogue_lines).contains("THANK YOU") == (outcome == "peaceful"), "Pin Pal aftermath matches " + outcome)
		finish(); await process_frame
	game.audio.shutdown(); game.menu_options.clear(); game.pause_options.clear(); game.dialogue_choices.clear(); game.dialogue_callback = Callable()
	game.queue_free(); await process_frame
	print("R2 discovery fixtures: ", checks, " checks, ", failures, " failures")
	quit(0 if failures == 0 else 1)
