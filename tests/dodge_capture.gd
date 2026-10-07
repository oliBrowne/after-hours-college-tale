extends SceneTree
## Plays real battle turns against any boss with DodgeBot at the controls and
## saves frames from the actual game screen.
##   xvfb-run godot --path . -s tests/dodge_capture.gd -- walt <out_dir> <turns> <every> [video] [plan=T:S,T:S]
## plan forces each captured turn's attack (T = turn index into the boss's
## ORDER) and stage (S), rebuilding the pattern the way start_phase does.

var game: Node
var bot: DodgeBot = DodgeBot.new()
var boss: String
var out: String
var turns: int
var every: int
var video: bool = false
var plan: Array = []

func _initialize() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	boss = args[0]; out = args[1]; turns = int(args[2]); every = int(args[3])
	video = args.size() > 4 and args[4] == "video"
	for a: String in args:
		if a.begins_with("plan="):
			for pair: String in a.substr(5).split(","):
				var bits: PackedStringArray = pair.split(":")
				plan.append([int(bits[0]), int(bits[1])])
	if not plan.is_empty(): turns = plan.size()
	DirAccess.make_dir_recursive_absolute(out)
	game = load("res://scenes/main.tscn").instantiate()
	root.add_child(game)
	_drive.call_deferred()

func _frame() -> void:
	await physics_frame

func _drive() -> void:
	for i: int in range(20): await _frame()
	game.state.flags.imani_joined = true
	if boss not in ["walt", "", "flyer", "claim", "pinpal"]: game.state.flags.walt_joined = true
	game.boss_id = "" if boss == "flyer" else boss
	game.checkpoint = game.state.duplicate(true)
	game.begin_battle()
	for i: int in range(10): await _frame()
	var shot: int = 0
	for turn: int in range(turns):
		game.battle.promise = true
		game.start_phase()
		if not plan.is_empty():
			var forced_turn: int = int(plan[turn][0]); var stage: int = int(plan[turn][1])
			game.boss_stage = stage
			game.pattern = DodgeBox.create(game.boss_id, 1234 + forced_turn, stage, 0, forced_turn, DodgeBox.beat_ticks_for(float(game.audio.music_metadata().get("bpm", 120.0))))
			var script: GDScript = DodgeBox.script_for(game.boss_id)
			for m: Dictionary in script.get_script_method_list():
				if str(m.name) == "preview": script.preview(game.pattern, stage)
			game.pattern.wardTicks = 0; game.pattern.wardPocket = Rect2(104, 82, 48, 34)
			if boss == "claim": game.pattern.boundary = true
		var waited: int = 0
		while int(game.mode) == 6:
			await _frame(); waited += 1
			if waited > 150: game.mode = 7
		var frame: int = 0
		print("turn ", turn, " pattern ", game.pattern.get("patternId", "?"), " stage ", game.boss_stage)
		while int(game.mode) == 7:
			var p: Dictionary = game.pattern
			var choice: Dictionary = bot.choose(p)
			var axis: Vector2 = choice.axis
			for pair: Array in [["move_left", -axis.x], ["move_right", axis.x], ["move_up", -axis.y], ["move_down", axis.y]]:
				if float(pair[1]) > 0.05: Input.action_press(pair[0], float(pair[1]))
				else: Input.action_release(pair[0])
			if choice.get("precision", false): Input.action_press("run")
			else: Input.action_release("run")
			if choice.press: game.beat_defend = true
			await _frame()
			for member: Dictionary in game.battle.party:
				if int(member.hp) > 0: member.hp = int(member.max)
			if video or frame % every == 0:
				await RenderingServer.frame_post_draw
				var image: Image = root.get_texture().get_image()
				image.save_png(out.path_join("%s-t%d-%s-%04d.png" % [boss, turn, str(p.get("patternId", "x")), frame if not video else shot]))
				shot += 1
			frame += 1
		print("  hits ", game.pattern.get("hits", -1), " grazes ", game.pattern.get("grazes", -1), " promise ", game.pattern.get("promiseComplete", false), " sync ", game.battle.sync)
		for i: int in range(20): await _frame()
		game.mode = 4
	quit()
