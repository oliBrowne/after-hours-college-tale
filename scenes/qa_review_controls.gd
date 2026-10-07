extends "res://scenes/qa_opening.gd"
## Targeted UI fixture: battle roster setup is explicit, not world-route proof.

func run(main: Node) -> bool:
	game = main; folder = OS.get_environment("AFTER_HOURS_QA")
	DirAccess.make_dir_recursive_absolute(folder)
	_log("START native mouse intro + legal battle-controls fixture; battle roster seeded explicitly")
	await _choose("Settings"); await _choose("Instant dialogue:"); await _choose("Back")
	await _choose("Settings")
	for _i: int in range(20):
		var wheel: InputEventMouseButton = InputEventMouseButton.new()
		wheel.button_index = MOUSE_BUTTON_WHEEL_DOWN; wheel.pressed = true; wheel.position = Vector2(400, 250)
		game.get_viewport().push_input(wheel, true); await _frame()
	await _click(Vector2(400, 309))
	_assert(int(game.mode) == 0, "Mouse wheel exposes and clicks Back in long Settings menu")
	await _choose("Begin the evening")
	for _i: int in range(35): await _frame()
	await _click(Vector2(495, 325))
	_assert(int(game.intro_index) == 0 and game.intro_ticks >= str(game.INTRO_CARDS[0][1]).length() * 2, "Mouse first click reveals intro text")
	await _click(Vector2(495, 325))
	_assert(int(game.intro_index) == 1, "Mouse second click advances intro")
	for _i: int in range(35): await _frame()
	await _click(Vector2(495, 325)); await _click(Vector2(495, 325))
	_assert(int(game.intro_index) == 2 and game.world.visible and not game.backdrop.visible, "Third arrival scene uses actual world")
	for _i: int in range(100): await _frame()
	await _capture("controls-in-world-arrival")
	await _click(Vector2(495, 126)); await _click(Vector2(495, 126))
	await _settle()
	var normal: Dictionary = game.state.duplicate(true)
	await _press("menu"); await _choose("Return to title"); await _choose("Begin the evening")
	await _press("cancel")
	_assert(int(game.mode) == WORLD and game.state.flags == normal.flags and game.state.party == normal.party and game.state.inventory == normal.inventory, "Skip and complete arrival yield identical starting story/roster/supplies")
	# Explicit isolated battle fixture; subsequent selections use real menu inputs.
	game.state.flags.imani_joined = true; game.state.flags.cal_joined = true
	game.state.party[0].hp = 0; game.state.party[1].hp = 20
	game.enter_room("U07", Vector2(96, 258), false)
	game.boss_id = "claim"; game.start_battle()
	await _frame()
	_assert(int(game.actor) == 1, "Fresh battle selects conscious Imani when Jules is down")
	_check_party_poses("Initial fixture")
	await _choose("GUARD"); await _choose("GUARD")
	await _capture("controls-down-review")
	await _choose("Clear plan")
	_assert(int(game.actor) == 1 and game.plan.is_empty(), "Clear plan selects first conscious member")
	await _press("cancel")
	_assert(int(game.actor) == 1, "Undo empty plan keeps unconscious Jules unavailable")
	await _choose("TALENT"); await _choose("Steady Refrain"); await _choose("jules")
	await _choose("GUARD")
	_assert(game.plan.size() == 2 and int(game.plan[0].target) == 0, "Revive target and funded guard queued legally")
	await _capture("controls-revive-review")
	await _choose("Commit turn")
	while int(game.mode) == RESOLVE and not failed: await _frame()
	_assert(int(game.battle.party[0].hp) > 0 and str(game.battle_sprites[0].animation) == "idle", "Revived Jules stands before defense")
	# Survive via production movement; no direct cursor or health changes.
	while int(game.mode) != BATTLE and not failed:
		if int(game.mode) == DODGE:
			_axis(Vector2(0, -1) if game.pattern.cursor.y > 56 else Vector2(0, 1))
		await _frame()
	_release()
	_assert(int(game.actor) == 0, "Next turn includes revived Jules")
	await _choose("STRIKE"); await _choose("ITEM"); await _choose("Granola"); await _choose("imani"); await _choose("GUARD")
	await _capture("controls-mixed-review")
	await _choose("Undo last command")
	_assert(int(game.actor) == 2 and game.plan.size() == 2, "Undo returns to removed conscious actor")
	await _choose("GUARD"); await _choose("Clear plan")
	_assert(int(game.actor) == 0 and game.plan.is_empty(), "Clear includes Jules after revival")
	await _choose("GUARD"); await _choose("GUARD"); await _choose("GUARD"); await _choose("Commit turn")
	while int(game.mode) != BATTLE and not failed:
		if int(game.mode) == RESULT: _assert(false, "Fixture party survives guarded resource-building turn"); break
		if int(game.mode) == DODGE: _axis(Vector2(0, -1) if game.pattern.cursor.y > 56 else Vector2(0, 1))
		await _frame()
	_release()
	await _choose("TALENT"); await _choose("Hear Me Out"); await _choose("GUARD")
	await _capture("controls-joint-review")
	await _choose("Clear plan")
	await _choose("TALENT"); await _choose("Hold the Light")
	await _choose("TALENT"); await _choose("Half Time")
	await _choose("TALENT"); await _choose("Brace")
	_assert(int(game.actor) == 2 and game.plan.size() == 2 and not str(game.battle_error).is_empty(), "Unaffordable shared-resource action is rejected visibly")
	await _capture("controls-invalid-resource")
	_log("FAIL" if failed else "PASS native mouse intro and down/clear/undo/revive/mixed/joint/resource controls")
	_write_trace()
	return not failed

func _click(point: Vector2) -> void:
	while int(game.input_lock) > 0: await _frame()
	var motion: InputEventMouseMotion = InputEventMouseMotion.new()
	motion.position = point; motion.global_position = point
	game.get_viewport().push_input(motion, true)
	for pressed: bool in [true, false]:
		var event: InputEventMouseButton = InputEventMouseButton.new()
		event.position = point; event.global_position = point
		event.button_index = MOUSE_BUTTON_LEFT; event.pressed = pressed
		game.get_viewport().push_input(event, true)
		await _frame()
