extends SceneTree
## Preview / tuning harness for DodgeBox patterns, outside the game.
##   godot --path . -s tests/dodge_preview.gd -- stats [boss ...] [quick]   (quick = one seed)
##   DODGE_BEAT_TICKS=25 sets the song beat (3600 / BPM; 25 for ENCORE's 144 BPM song).
##   xvfb-run godot --path . -s tests/dodge_preview.gd -- frames walt 0 1 <out_dir> [every]

const D = preload("res://core/dodge_box.gd")

func _initialize() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() == 0 or args[0] == "stats":
		var bosses: Array = Array(args.slice(1)).filter(func(a: String) -> bool: return a != "quick")
		if bosses.is_empty(): bosses = ["walt", "encore"]
		_stats(bosses, "quick" in args)
		quit()
		return
	var driver: Node2D = load("res://tests/dodge_preview_driver.gd").new()
	driver.boss = args[1]; driver.turn = int(args[2]); driver.phase = int(args[3]); driver.out = args[4]
	if args.size() > 5: driver.every = int(args[5])
	root.add_child(driver)

## Scripts list their attacks in ORDER and the phases worth testing in PHASES.
## An optional static preview(s, phase) sets what main.gd would set after create
## (revision, rejected, boundary) so every phase can be exercised here.
static func has_static(script: GDScript, name: String) -> bool:
	for m: Dictionary in script.get_script_method_list():
		if str(m.name) == name: return true
	return false

static func make(boss: String, seed: int, phase: int, turn: int) -> Dictionary:
	var beat: int = int(OS.get_environment("DODGE_BEAT_TICKS")) if not OS.get_environment("DODGE_BEAT_TICKS").is_empty() else 30
	var p: Dictionary = D.create(boss, seed, phase, 0, turn, beat)
	var script: GDScript = D.script_for(boss)
	if has_static(script, "preview"): script.preview(p, phase)
	return p

func _stats(bosses: Array, quick: bool = false) -> void:
	for boss: String in bosses:
		var consts: Dictionary = D.script_for(boss).get_script_constant_map()
		var order: Array = consts.get("ORDER", [])
		var phases: Array = consts.get("PHASES", [0, 1])
		for turn: int in range(order.size()):
			for phase: int in phases:
				var line: String = "%-11s %-15s phase %d " % [boss, order[turn], phase]
				for seed: int in ([1234] if quick else [1234, 77, 4242]):
					var p: Dictionary = make(boss, seed + turn, phase, turn)
					var idle: Dictionary = make(boss, seed + turn, phase, turn)
					var bot: DodgeBot = DodgeBot.new()
					var peak: int = 0
					while not p.done:
						var choice: Dictionary = bot.choose(p)
						D.step(p, choice.axis, bool(choice.get("precision", false)), 1.0, false, true, choice.press)
						D.step(idle, Vector2.ZERO, false, 1.0, false, true, false)
						peak = maxi(peak, p.bullets.size())
					line += " | bot %d hits, idle %d, graze %2d, promise %s, peak %3d" % [p.hits, idle.hits, p.grazes, "Y" if p.promiseComplete else "n", peak]
				print(line)
				printraw("")
