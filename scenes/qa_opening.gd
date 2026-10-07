extends Node
## Actual-input opening acceptance route. No direct game or encounter state writes.
## Main attaches this node and awaits run(self). AFTER_HOURS_QA selects evidence folder.
## Optional arguments: --qa-force, --qa-fail-promise, --qa-retry; use --qa-opening.
const WORLD: int = 1
const DIALOGUE: int = 2
const MENU: int = 3
const BATTLE: int = 4
const TIMING: int = 5
const DODGE: int = 7
const RESULT: int = 8
const PAUSE: int = 9
const RESOLVE: int = 10
const INTRO: int = 12
var game: Node
var failed: bool = false
var ticks: int = 0
var trace: Array[String] = []
var folder: String = ""
var captures: Dictionary = {}
var force_claim: bool = false
var fail_promise: bool = false
var pause_checked: bool = false
var failed_promise_checked: bool = false
var retry_route: bool = false
var retry_checked: bool = false
var observe_claim: bool = false
var observations_checked: bool = false
var claim_failed_checked: bool = false

func run(main: Node) -> bool:
	game = main
	force_claim = "--qa-force" in OS.get_cmdline_user_args()
	fail_promise = "--qa-fail-promise" in OS.get_cmdline_user_args()
	retry_route = "--qa-retry" in OS.get_cmdline_user_args()
	observe_claim = "--qa-claim-observe" in OS.get_cmdline_user_args()
	folder = OS.get_environment("AFTER_HOURS_QA")
	if not folder.is_empty(): DirAccess.make_dir_recursive_absolute(folder)
	_log("START ordinary input route; forceCLAIM=%s failPromise=%s; instant text skips reading pace, no simulation acceleration" % [force_claim, fail_promise])
	await _choose("Settings")
	if not bool(game.state.settings.instant): await _choose("Instant dialogue:")
	await _choose("Back")
	if "--qa-reload-claim" in OS.get_cmdline_user_args(): return await _reload_claim()
	await _capture("00-title")
	await _choose("Begin the evening")
	await _movein()
	await _settle()
	if game.jakerson_ui: await _choose("I'll find my way")
	_assert(not game.state.flags.get("imani_joined", false) and not game.state.flags.get("cal_joined", false), "Solo Jules at opening")
	await _capture("01-solo-U01")
	if "--qa-discoveries" in OS.get_cmdline_user_args(): await _object("bike"); await _settle()
	await _door("umc_path", "U08")
	await _door("terrace_path", "U02")
	if "--qa-discoveries" in OS.get_cmdline_user_args(): await _object("eli"); await _settle()
	await _door("main_entrance", "U03")
	await _door("clubroom", "U04")
	if "--qa-discoveries" in OS.get_cmdline_user_args(): await _object("stage"); await _settle()
	await _object("imani")
	await _settle()
	await _choose("I can stay")
	await _settle()
	_assert(game.state.flags.get("mixer_returned", false) and not game.state.flags.get("imani_joined", false), "Mixer returned; Imani stays for sound check")
	await _door("atrium", "U03")
	await _quiet()
	_assert(game.state.flags.get("imani_joined", false) and not game.state.flags.get("cal_joined", false), "Imani joins in the atrium; Cal still absent")
	await _door("clubroom", "U04")
	await _capture("02-duo-U04")
	await _object("flyer")
	await _fight("flyer")
	_assert(game.state.flags.get("flyer_resolution", "") == "peaceful", "Flyerer peaceful resolution")
	await _door("atrium", "U03")
	await _object("booth")
	await _settle()
	_assert(game.state.flags.get("booth_seen", false), "Booth voice investigated")
	await _door("stairs", "U05")
	await _load_before_cal()
	await _object("cal")
	await _settle()
	_assert(game.state.flags.get("imani_joined", false) and game.state.flags.get("cal_joined", false), "Three-member roster recruited incrementally")
	await _capture("04-trio-U05")
	if "--qa-discoveries" in OS.get_cmdline_user_args(): await _object("mags_checklist"); await _settle()
	await _door("connection_stairs", "U06")
	await _capture("05-large-U06")
	if "--qa-discoveries" in OS.get_cmdline_user_args(): await _object("arcade_button"); await _settle()
	await _object("scorecard")
	await _settle()
	await _door("lost_property", "U07")
	await _capture("06-lost-property")
	if "--qa-discoveries" in OS.get_cmdline_user_args(): await _object("lost_labels"); await _settle()
	await _object("claim")
	await _fight("claim")
	_assert(game.state.flags.get("claim_resolution", "") == ("forceful" if force_claim else "peaceful"), "Advisor Bev expected resolution")
	_assert(pause_checked, "Defense pause/resume exercised through menus")
	if fail_promise: _assert(failed_promise_checked, "Failed promise observed before successful recovery")
	if retry_route: _assert(retry_checked, "Defeat and normal Retry exercised")
	_assert(game.state.flags.get("opening_finished", false) and game.state.flags.get("pip_joined", false), "Opening finished; Pip joined")
	await _capture("09-opening-complete")
	if "--qa-discoveries" in OS.get_cmdline_user_args(): await _return_loop()
	_release()
	_log("FAIL" if failed else "PASS uninterrupted actual-input opening route")
	if not folder.is_empty():
		var file: FileAccess = FileAccess.open(folder.path_join("opening-trace.txt"), FileAccess.WRITE)
		if file: file.store_string("\n".join(trace)); file.close()
	return not failed

func _return_loop() -> void:
	var inventory: Dictionary = game.state.inventory.duplicate(true)
	await _object("pip"); await _settle()
	await _object("lost_labels"); await _settle()
	await _capture("10-lost-property-return")
	await _door("connection", "U06")
	await _object("arcade_button"); await _settle()
	await _capture("11-pip-arcade")
	await _door("club_service", "U04")
	await _object("stage"); await _settle()
	await _object("invitation"); await _settle()
	await _capture("12-returned-club")
	await _door("atrium", "U03")
	await _door("stairs", "U05")
	await _object("mags_checklist"); await _settle()
	await _door("atrium", "U03")
	await _door("terrace", "U02")
	await _object("eli"); await _settle()
	await _object("mags"); await _settle()
	await _door("outdoor_return", "U08")
	await _door("broadway_return", "U01")
	await _object("bike"); await _settle()
	await _capture("13-full-return-loop")
	for flag: String in ["discovery_bike_seen", "discovery_eli_acknowledged", "discovery_cuesheet_seen", "discovery_mags_checklist_seen", "discovery_arcade_seen", "discovery_lostlabels_seen"]:
		_assert(game.state.flags.get(flag, false), "Discovery persisted " + flag)
	_assert(game.state.inventory == inventory, "Return loop creates no duplicate resources")

func _log(message: String) -> void:
	var line: String = "%06d %s room=%s mode=%s" % [ticks, message, game.state.room, game.mode]
	trace.append(line)
	print("QA_INPUT ", line)

func _assert(condition: bool, message: String) -> void:
	if failed: return
	_log(("PASS " if condition else "FAIL ") + message)
	if not condition: failed = true

func _frame() -> void:
	await get_tree().physics_frame
	ticks += 1
	if ticks % 2 == 0 and _recording():
		DirAccess.make_dir_recursive_absolute(video)
		await RenderingServer.frame_post_draw
		game.get_viewport().get_texture().get_image().save_png(video.path_join("f%05d.png" % shot)); shot += 1
	if ticks % 600 == 0: _log("Progress caption=" + str(game.caption) + " selection=" + str(game.selection) + " lock=" + str(game.input_lock))
	# Fights run an extra turn since promises give 45 Openness, so routes get 600 seconds.
	if ticks > 36000 and not failed:
		failed = true; _log("FAIL route exceeded 600 simulation seconds")

func _release() -> void:
	for action: String in ["move_left", "move_right", "move_up", "move_down", "run"]: Input.action_release(action)

func _axis(axis: Vector2, running: bool = false) -> void:
	_release()
	if axis.x < -0.1: Input.action_press("move_left")
	if axis.x > 0.1: Input.action_press("move_right")
	if axis.y < -0.1: Input.action_press("move_up")
	if axis.y > 0.1: Input.action_press("move_down")
	if running: Input.action_press("run")

func _event(action: String, pressed: bool) -> void:
	var event: InputEventAction = InputEventAction.new()
	event.action = action; event.pressed = pressed; event.strength = 1.0 if pressed else 0.0
	game.get_viewport().push_input(event, true)

func _press(action: String = "confirm") -> void:
	while int(game.input_lock) > 0 and not failed: await _frame()
	_event(action, true)
	await _frame()
	_event(action, false)
	await _frame()

func _choose(prefix: String) -> void:
	if failed: return
	var index: int = -1
	for i: int in range(game.menu_options.size()):
		if str(game.menu_options[i].label).begins_with(prefix): index = i; break
	if index < 0:
		_assert(false, "Missing menu choice " + prefix + " in " + str(game.caption)); return
	while int(game.selection) != index and not failed: await _press("move_down")
	await _press()

func _settle() -> void:
	_release()
	while int(game.mode) in [DIALOGUE, INTRO] and not failed:
		if int(game.mode) == DIALOGUE and str(game.dialogue_lines[game.line_index][0]) == "Imani":
			var mood: String = str(game.dialogue_lines[game.line_index][2])
			var key: String = "dialogue-imani-" + mood
			if not captures.has(key):
				captures[key] = true; await _capture("02-" + key)
		if int(game.mode) == INTRO and int(game.intro_index) == 2 and int(game.intro_ticks) >= 30 and not captures.has("arrival-world"):
			captures["arrival-world"] = true; await _capture("01-arrival-bus-departure")
		if int(game.mode) == INTRO and int(game.intro_ticks) < 30: await _frame()
		else:
			if int(game.mode) == DIALOGUE and _recording():
				for _r: int in range(80): await _frame()
			await _press()
	for _i: int in range(4): await _frame()

func _load_before_cal() -> void:
	if failed: return
	var before: Dictionary = game.state.duplicate(true)
	_release()
	await _press("menu")
	_assert(int(game.mode) == PAUSE, "World pause menu opened before Cal")
	await _choose("Saves / import / export")
	await _choose("Load auto")
	for _i: int in range(4): await _frame()
	_assert(int(game.mode) == WORLD and str(game.state.room) == "U05", "Normal save-menu load returns to repair landing")
	_assert(game.state.flags.get("imani_joined", false) and not game.state.flags.get("cal_joined", false), "Save/load preserves duo roster before Cal")
	var same: bool = game.state.party.size() == before.party.size()
	if same:
		for i: int in range(before.party.size()):
			var original: Dictionary = before.party[i]
			var loaded: Dictionary = game.state.party[i]
			if str(loaded.id) != str(original.id): same = false
			for key: String in ["hp", "max", "power", "defence"]:
				if int(loaded[key]) != int(original[key]): same = false
	for key: String in ["granola", "cocoa", "thermos"]:
		if int(game.state.inventory[key]) != int(before.inventory[key]): same = false
	if not same:
		_log("Load comparison before=" + JSON.stringify({"party": before.party, "inventory": before.inventory}) + " after=" + JSON.stringify({"party": game.state.party, "inventory": game.state.inventory}))
	_assert(same, "Save/load preserves member IDs, HP, stats and supply counts")
	await _capture("04-duo-save-load")

## Move-in day with the ordinary inputs: Jakerson introduces himself, Jules reads a few things, walks the hall
## down to the lobby, wins the practice spar peacefully, makes the bet and four years go by (ends on the
## evening's greeting).
func _movein() -> void:
	if failed: return
	for _i: int in range(600):
		if int(game.mode) != INTRO: break
		await _press()
	_assert(str(game.state.room) == "D01" and bool(game.state.flags.get("movein_active", false)), "A new game opens on move-in day in room 214")
	await _quiet()
	_assert(bool(game.state.flags.get("movein_met", false)) and not NativeRoomScenes.busy() and int(game.mode) == WORLD, "Jakerson introduces himself, then Jules has control")
	await _capture("00-movein-room")
	await _object("jules_bed"); await _settle()
	await _object("jakerson"); await _settle()
	await _door("hallway", "D02")
	await _quiet()
	_assert(bool(game.state.flags.get("movein_ahead", false)), "Jakerson goes ahead to the lobby once Jules is in the hall")
	await _object("floormate_208"); await _settle()
	await _object("floormate_lounge"); await _settle()
	await _capture("00-movein-hall")
	await _door("stairs_lobby", "D03")
	await _quiet()
	await _object("front_doors"); await _settle()
	_assert(str(game.state.room) == "D03" and bool(game.state.flags.get("movein_active", false)), "The front doors keep Jules in the lobby until the bet is made")
	await _object("jakerson_lobby"); await _settle()
	_assert(str(game.caption).begins_with("Jakerson / a friendly spar"), "Jakerson offers the practice spar at the ping-pong table")
	await _choose("Sure, show me")
	await _spar()
	_assert(game.state.flags.get("jakerson_resolution", "") == "peaceful", "Dorm spar ends with RELEASE")
	_assert(str(game.caption).begins_with("Jakerson / loser buys the boba"), "The bet follows the spar")
	await _choose("Deal. I'm ordering taro")
	await _settle()
	_assert(bool(game.state.flags.get("movein_done", false)) and not bool(game.state.flags.get("movein_active", false)) and game.state.flags.get("movein_boba", "") == "taro", "Move-in day ends with the bet")

## The spar with ordinary menu input: answer every coaching line, follow its advice.
func _spar() -> void:
	var start: int = ticks
	var coached: int = 0
	while not failed and int(game.mode) != RESULT:
		if ticks - start > 9000: _assert(false, "Spar did not resolve"); break
		match int(game.mode):
			DIALOGUE:
				coached += 1
				if not captures.has("coach-%d" % int(game.battle.get("coached", 0))):
					captures["coach-%d" % int(game.battle.get("coached", 0))] = true; await _capture("04-coach-%d" % int(game.battle.get("coached", 0)))
				await _settle()
			BATTLE:
				_release()
				if str(game.caption) == "Review party plan": await _choose("Commit turn")
				elif str(game.caption).contains("Choose an action"): await _choose("CONNECT")
				elif str(game.caption).begins_with("Connect"):
					var labels: Array = game.menu_options.map(func(o: Dictionary) -> String: return str(o.label))
					if labels.any(func(l: String) -> bool: return l.begins_with("RELEASE")): await _choose("RELEASE")
					elif int(game.battle.turn) == 0: await _choose("Ask what")
					else: await _choose("Catch three")
				else: _assert(false, "Unexpected spar menu " + str(game.caption))
			DODGE:
				await _defend_box("jakerson")
			_:
				_release(); await _frame()
	_assert(coached >= 3, "Jakerson coached each turn (%d)" % coached)
	await _capture("05-spar-result")
	await _choose("Continue"); await _settle()

func _definition(id: String) -> Dictionary:
	for object: Dictionary in game.rooms[str(game.state.room)].objects:
		if str(object.id) == id: return object
	_assert(false, "Missing room object " + id)
	return {}

func _walk(point: Vector2, tolerance: float = 6.0) -> void:
	if failed: return
	var room: String = str(game.state.room)
	var bounds: Array = game.rooms[room].walk_bounds
	var grid: AStarGrid2D = AStarGrid2D.new()
	var dims: Array = game.rooms[room].get("dimensions", [960, 540])
	var cols: int = maxi(121, ceili(float(dims[0]) / 8.0) + 1); var rows: int = maxi(69, ceili(float(dims[1]) / 8.0) + 1)
	grid.region = Rect2i(0, 0, cols, rows); grid.cell_size = Vector2(8, 8)
	grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER; grid.update()
	var walk: Rect2 = Rect2(float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3]))
	for y: int in range(rows):
		for x: int in range(cols):
			var at: Vector2 = Vector2(x * 8, y * 8)
			var solid: bool = not walk.has_point(at)
			for block: Dictionary in game.rooms[room].get("blocks", []):
				var rect: Rect2 = Rect2(float(block.x), float(block.y), float(block.w), float(block.h)).grow(10)
				if rect.has_point(at): solid = true
			grid.set_point_solid(Vector2i(x, y), solid)
	var from: Vector2i = Vector2i(roundi(game.player.position.x / 8), roundi(game.player.position.y / 8))
	var to: Vector2i = Vector2i(roundi(point.x / 8), roundi(point.y / 8))
	grid.set_point_solid(from, false); grid.set_point_solid(to, false)
	var path: PackedVector2Array = grid.get_point_path(from, to)
	if path.is_empty(): _assert(false, "No walkable route to " + str(point)); return
	path.append(point)
	var start: int = ticks
	for destination: Vector2 in path:
		while game.player.position.distance_to(destination) > tolerance and not failed and str(game.state.room) == room:
			if int(game.mode) != WORLD or NativeJakerson.busy() or NativeRoomScenes.busy(): await _quiet()
			_axis(destination - game.player.position, true)
			await _frame()
			if ticks - start > 2400: _assert(false, "Walking stuck " + str(game.player.position) + " -> " + str(destination))
		if str(game.state.room) != room: break
	_release()

func _object(id: String) -> void:
	if failed: return
	await _quiet()
	var object: Dictionary = _definition(id)
	if object.is_empty(): return
	_release()
	for _i: int in range(5): await _frame()
	var raw: Array = object.get("hit_rect", [-24, -30, 48, 40])
	var at := Vector2(object.x, object.y) + Vector2(raw[0] + raw[2] / 2.0, raw[1] + raw[3] / 2.0)
	var screen: Vector2 = game.world.get_global_transform_with_canvas() * at
	if not Rect2(10, 64, 620, 246).has_point(screen):
		var route: PackedVector2Array = game.navigation.object_route(game.player.position, object)
		_assert(not route.is_empty(), "Keyboard approach for initially offscreen " + id)
		if failed: return
		await _walk(route[-1], 8)
		screen = game.world.get_global_transform_with_canvas() * at
	var motion := InputEventMouseMotion.new()
	motion.position = screen; motion.global_position = screen
	game.get_viewport().push_input(motion, true)
	await _frame()
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT; click.pressed = true
	click.position = screen; click.global_position = screen
	game.get_viewport().push_input(click, true)
	await _frame()
	click = click.duplicate(); click.pressed = false
	game.get_viewport().push_input(click, true)
	_assert(str(game.pointer_object.get("id", "")) == id or int(game.mode) != WORLD, "Visible-body mouse selects " + id)
	var start: int = ticks
	while game.pointer_goal != Vector2.INF and int(game.mode) == WORLD and not failed:
		await _frame()
		if ticks - start > 1800: _assert(false, "Production pointer route stuck at " + str(game.player.position) + " for " + id)
	_assert(int(game.mode) != WORLD or object.kind == "door", "Production pointer interacts with " + id + " (player " + str(game.player.position) + ", notice \"" + str(game.notice) + "\")")

## Let story scenes that start on their own (Imani in the atrium, Jakerson's
## drop-in lessons) play out with ordinary presses before the next action.
func _quiet() -> void:
	var calm: int = 0
	while calm < 4 and not failed:
		if int(game.mode) == DIALOGUE: await _settle(); calm = 0
		elif NativeJakerson.busy() or NativeRoomScenes.busy() or int(game.transition_ticks) > 0: _release(); await _frame(); calm = 0
		else: await _frame(); calm += 1

func _door(id: String, next_room: String) -> void:
	if failed: return
	_log("Production mouse route through " + id)
	await _object(id)
	await _settle()
	_assert(str(game.state.room) == next_room, "Entered " + next_room)

func _fight(id: String) -> void:
	await _settle()
	if id == "flyer" and retry_route and not retry_checked: await _lose_and_retry()
	_check_party_poses("Fresh " + id)
	var start: int = ticks
	var turn_logged: int = -1
	while not failed and int(game.mode) != RESULT:
		if ticks - start > 6000: _assert(false, "Battle did not resolve " + id); break
		match int(game.mode):
			BATTLE:
				_release()
				_check_party_poses("Planning " + id)
				if int(game.battle.turn) != turn_logged:
					turn_logged = int(game.battle.turn); _log("Battle " + id + " turn=" + str(turn_logged) + " openness=" + str(game.battle.openness))
					if id == "claim" and observe_claim and turn_logged >= 2 and not observations_checked:
						_assert(not bool(game.claim_needs.tagDelivered) and not ClaimNeeds.can_release(game.claim_needs) and int(game.battle.openness) == 0, "Repeated legal observation cannot complete Advisor Bev needs or unlock RELEASE")
						observations_checked = not failed
					if id == "claim" and observe_claim and turn_logged >= 3 and not claim_failed_checked:
						_assert(not bool(game.claim_needs.tagDelivered) and not bool(game.pattern.promiseComplete) and int(game.battle.openness) == 0, "Missed Advisor Bev ticket promise remains recoverable and does not advance needs")
						claim_failed_checked = not failed
					if id == "flyer" and fail_promise and turn_logged == 1:
						_assert(not bool(game.pattern.promiseComplete) and not bool(game.battle.promise), "Missed promise fails cleanly and clears pending objective")
						failed_promise_checked = not failed
				if str(game.caption) == "Review party plan":
					var key: String = "plan-" + id
					if not captures.has(key): captures[key] = true; await _capture("07-" + key)
					await _choose("Commit turn")
				elif str(game.caption).contains("Choose an action"):
					if id == "claim" and observe_claim and turn_logged < 2: await _choose("CONNECT")
					elif id == "claim" and force_claim: await _choose("STRIKE")
					elif int(game.actor) == 0 or id == "claim" and int(game.actor) == 1 and int(game.boss_stage) == 1: await _choose("CONNECT")
					else: await _choose("GUARD")
				elif str(game.caption).begins_with("Connect"):
					var release: bool = false
					for choice: Dictionary in game.menu_options:
						if str(choice.label).begins_with("RELEASE"): release = true
					if id == "claim" and observe_claim and turn_logged < 2:
						_assert(not release, "Uncompleted Advisor Bev has no RELEASE menu")
						await _choose("Ask why the glove")
					elif release and int(game.actor) == 0: await _choose("RELEASE")
					elif id == "claim" and int(game.actor) == 1: await _choose("Return ONE")
					else: await _choose("Carry one" if id == "claim" else "Read one invitation")
				else: _assert(false, "Unexpected battle menu " + str(game.caption))
			DODGE:
				if id == "claim" and observe_claim and turn_logged < 3: _release(); await _frame()
				elif not pause_checked and int(game.pattern.clock) >= 80: await _pause_defense()
				else: await _defend(id)
			TIMING:
				_release()
				if int(game.timing_index) == 0 and int(game.timing_ticks) >= 5 and not captures.has("timing-early"):
					captures["timing-early"] = true; await _capture("07-claim-timing-early")
				if int(game.timing_index) == 0 and int(game.timing_ticks) >= 20 and not captures.has("timing-late"):
					captures["timing-late"] = true; await _capture("07-claim-timing-late")
				if int(game.timing_ticks) >= 27:
					_log("Timing confirm at tick=" + str(game.timing_ticks) + " strike=" + str(game.timing_index))
					await _press()
				else: await _frame()
			RESOLVE:
				_release()
				if force_claim and id == "claim" and int(game.resolution_ticks) >= 21 and not captures.has("strike-impact"):
					captures["strike-impact"] = true; await _capture("07-claim-strike-impact")
				else: await _frame()
			MENU:
				_assert(false, "Unexpected battle interruption " + str(game.caption) + " save=" + str(game.saves.last_error))
			# A boss answering a CONNECT question.
			DIALOGUE: await _settle()
			_:
				_release(); await _frame()
	_release()
	if failed: return
	var expected: String = "forceful" if id == "claim" and force_claim else "peaceful"
	_assert(game.battle.outcome == expected, "Battle ended " + expected + " " + id)
	await _capture("03-flyer-peaceful" if id == "flyer" else "08-claim-" + expected)
	if id == "claim" and "--qa-stop-at-claim-result" in OS.get_cmdline_user_args(): await _interrupt("result")
	await _choose("Continue")
	if id == "claim" and "--qa-stop-at-claim-dialogue" in OS.get_cmdline_user_args(): await _interrupt("dialogue")
	await _settle()

func _write_trace() -> void:
	var file: FileAccess = FileAccess.open(folder.path_join("opening-trace.txt"), FileAccess.WRITE)
	if file: file.store_string("\n".join(trace)); file.close()

func _interrupt(at: String) -> void:
	_assert(game.state.flags.get("opening_finished", false) and game.state.flags.get("pip_joined", false) and game.state.flags.get("aftermath_pending", "") == "claim", "Advisor Bev atomic completion and resumable aftermath at " + at)
	await _capture("10-interrupt-" + at)
	if at == "result":
		while game.qa_record != null: await _frame()
	var timing: FileAccess = FileAccess.open(folder.path_join("music-timing.json"), FileAccess.WRITE)
	if timing: timing.store_string(JSON.stringify(game.qa_music_events, "\t")); timing.close()
	_write_trace()
	var file: FileAccess = FileAccess.open(folder.path_join("interruption-ready.txt"), FileAccess.WRITE)
	if file: file.store_string(at); file.close()
	while true: await _frame()

func _reload_claim() -> bool:
	await _choose("Continue")
	_assert(int(game.mode) == DIALOGUE and game.state.flags.get("aftermath_pending", "") == "claim", "New process resumes Advisor Bev aftermath")
	_assert(game.state.flags.get("opening_finished", false) and game.state.flags.get("pip_joined", false) and game.pip.visible and game.environment.glove_claimed, "Reload restores completed opening, Pip and changed room")
	var inventory: Dictionary = game.state.inventory.duplicate(true)
	var party: Array = game.state.party.duplicate(true)
	await _capture("11-reloaded-aftermath")
	if "--qa-stop-at-claim-dialogue" in OS.get_cmdline_user_args(): await _interrupt("dialogue")
	await _settle()
	_assert(game.state.flags.get("aftermath_pending", "") == "", "Afternath completes and clears pending scene")
	await _press("menu"); await _choose("Return to title"); await _choose("Continue")
	_assert(int(game.mode) == WORLD and game.state.flags.get("aftermath_pending", "") == "", "Completed aftermath does not repeat on next load")
	_assert(game.state.inventory == inventory and game.state.party == party, "Interrupted result reload preserves inventory and recovered roster exactly")
	await _capture("12-interruption-recovery-complete")
	_log("FAIL" if failed else "PASS process interruption and reload recovery")
	_write_trace()
	return not failed

func _check_party_poses(context: String) -> void:
	for i: int in range(game.battle_sprites.size()):
		if not game.battle_sprites[i].visible: continue
		var expected: String = "idle" if int(game.battle.party[i].hp) > 0 else "down"
		if str(game.battle_sprites[i].animation) != expected:
			_assert(false, context + " pose matches health for " + str(game.battle.party[i].id))

func _lose_and_retry() -> void:
	if failed: return
	var original: Dictionary = game.checkpoint.duplicate(true)
	var start: int = ticks
	_log("Retry branch: legal CONNECT plans, remain in warned row without dodging")
	while int(game.mode) != RESULT and not failed:
		if ticks - start > 12000:
			_assert(false, "Idle pressure failed to produce defeat within two hundred simulation seconds"); break
		_release()
		if int(game.mode) == BATTLE:
			if str(game.caption) == "Review party plan":
				_log("Retry pressure turn=%s HP=%s" % [game.battle.turn, game.battle.party.map(func(m: Dictionary) -> int: return int(m.hp))])
				await _choose("Commit turn")
			elif str(game.caption).contains("Choose an action"): await _choose("CONNECT")
			elif str(game.caption).begins_with("Connect"): await _choose("Read the club's purpose")
			else: _assert(false, "Unexpected retry planning menu " + str(game.caption))
		else: await _frame()
	if failed: return
	_assert(game.battle.outcome == "defeat", "Actual warned-row camping produces party defeat")
	await _capture("03-defeat-before-retry")
	await _choose("Retry / restore pre-battle supplies")
	_assert(int(game.mode) == BATTLE and game.battle.outcome == "active", "Normal Retry starts a fresh active battle")
	for i: int in range(original.party.size()):
		var expected_hp: int = int(original.party[i].hp) if i == 0 or original.flags.get(str(original.party[i].id) + "_joined", false) else 0
		_assert(int(game.battle.party[i].hp) == expected_hp and int(game.state.party[i].hp) == int(original.party[i].hp), "Retry restores checkpoint HP for " + str(original.party[i].id))
	for key: String in ["granola", "cocoa", "thermos"]:
		_assert(int(game.battle.inventory[key]) == int(original.inventory[key]), "Retry restores pre-battle " + key)
	_assert(game.state.flags == original.flags, "Retry preserves checkpoint story and roster flags")
	retry_checked = not failed
	await _capture("03-retry-restored-planning")

func _pause_defense() -> void:
	_release()
	await _press("menu")
	_assert(int(game.mode) == PAUSE, "Defense opens actual pause menu")
	var snapshot: Dictionary = game.pattern.duplicate(true)
	var paused_beat: float = game.audio.beat_position()
	for _i: int in range(60): await _frame()
	_assert(game.pattern == snapshot, "Pattern remains identical across sixty paused physics ticks")
	await _capture("07-defense-paused")
	await _choose("Resume")
	_assert(int(game.mode) == DODGE and game.pattern.clock == snapshot.clock, "Resume preserves pattern clock and returns to defense")
	while int(game.resume_ticks) > 1 and not failed: await _frame()
	_assert(game.pattern.clock == snapshot.clock and is_equal_approx(game.audio.beat_position(), paused_beat), "Resume countdown holds both pattern and music transport")
	pause_checked = not failed

func _defend(id: String) -> void:
	if game.pattern.get("engine","")=="box":
		await _defend_box(id);return
	var state: Dictionary = game.pattern
	var cursor: Vector2 = Vector2(float(state.cursor.x), float(state.cursor.y))
	var destination: Vector2 = Vector2(198, 60)
	var confirm: bool = false
	if id == "flyer":
		if not state.markers.is_empty() and state.markers[0].collected: destination = Vector2(128, 60)
		if not state.markers.is_empty() and state.markers[0].collected:
			for threat: Dictionary in state.hazards + state.telegraphs:
				if threat.get("aimed", false): destination.y = 67.5 if absf(float(threat.y) - 60) < 4 else 60
		if fail_promise and int(game.battle.turn) == 1: destination = Vector2(128, 60)
	else:
		destination = Vector2(80, 60) if int(state.phase) == 0 else Vector2(128, 60)
		if state.carryTag:
			if not state.markers[1].collected: destination = Vector2(float(state.markers[1].x), float(state.markers[1].y))
			else: destination = Vector2(204, 36) if int(state.phase) == 0 else Vector2(56, float(state.safeLane))
		confirm = int(state.phase) > 0 and cursor.distance_to(destination) < 10
		if force_claim:
			destination = Vector2(204, 36) if int(state.phase) == 0 else Vector2(56, float(state.safeLane))
			confirm = false
	var delta: Vector2 = destination - cursor
	var tolerance: float = 1.0 if id == "flyer" else 2.0
	_axis(Vector2(signf(delta.x) if absf(delta.x) > tolerance else 0, signf(delta.y) if absf(delta.y) > tolerance else 0))
	if confirm: _event("confirm", true)
	await _frame()
	if confirm: _event("confirm", false)
	var key: String = id + "-phase-" + str(state.phase)
	if not captures.has(key) and int(state.clock) >= 160:
		captures[key] = true; await _capture("07-" + key)

func _capture(name: String) -> void:
	if failed: return
	_log("Checkpoint " + name)
	if folder.is_empty() or DisplayServer.get_name() == "headless": return
	await get_tree().process_frame
	RenderingServer.force_draw(false)
	var image: Image = game.get_viewport().get_texture().get_image()
	var error: Error = image.save_png(folder.path_join(name + ".png"))
	_assert(error == OK, "Native screenshot " + name)

var dodge_bot: DodgeBot
## AFTER_HOURS_VIDEO=<dir> saves every second frame for a clip, while AFTER_HOURS_VIDEO_WHEN
## matches (empty: always; c1story: Imani's atrium scene to Walt; graduation: the epilogue;
## scenes: walk-in room scenes; eric: the Professor Eric fight on the test floor).
## Dialogue lines stay up long enough to read while recording.
var video: String = OS.get_environment("AFTER_HOURS_VIDEO")
var video_when: String = OS.get_environment("AFTER_HOURS_VIDEO_WHEN")
var shot: int = 0

func _recording() -> bool:
	if video.is_empty() or DisplayServer.get_name() == "headless" or game == null: return false
	var f: Dictionary = game.state.flags
	var room: String = str(game.state.room)
	match video_when:
		"c1story":
			if room == "U03" and f.get("mixer_returned", false) and not f.get("imani_joined", false): return true
			return f.get("imani_joined", false) and not f.get("walt_joined", false) and room in ["U03", "U02", "U08"] and int(game.mode) in [WORLD, DIALOGUE, MENU]
		"scenes":
			return NativeRoomScenes.busy()
		"eric":
			return room == "E03" and int(game.mode) != WORLD
		"graduation":
			return f.get("graduation_day", false) and (not f.get("graduation_complete", false) or int(game.mode) == MENU and str(game.caption).begins_with("The End"))
	return true
## Box-engine defenses (core/dodge_box.gd) are flown by DodgeBot with ordinary
## inputs: directions, run for precision/duck, and confirm.
func _defend_box(id: String) -> void:
	if dodge_bot==null: dodge_bot=DodgeBot.new()
	dodge_bot.skip_promise=force_claim and id=="claim" or fail_promise and id=="flyer" and int(game.battle.turn)==1
	var p: Dictionary=game.pattern
	var choice: Dictionary=dodge_bot.choose(p)
	_axis(choice.axis, bool(choice.get("precision", false)))
	if choice.press:_event("confirm",true)
	await _frame()
	if choice.press:_event("confirm",false)
	var key: String=id+"-"+str(p.get("patternId",""))+"-"+str(p.get("phase",0))
	if not captures.has(key) and int(p.clock)>=180:
		captures[key]=true;await _capture("defense-"+key)
