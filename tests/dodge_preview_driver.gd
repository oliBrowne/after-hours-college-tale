extends Node2D
const D = preload("res://core/dodge_box.gd")
var boss: String = "walt"
var turn: int = 0
var phase: int = 0
var out: String = "user://dodge"
var every: int = 20
var view: DodgeBoxView
var pattern: Dictionary
var bot: DodgeBot = DodgeBot.new()

func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(out)
	var bg: ColorRect = ColorRect.new(); bg.color = Color("0d101c"); bg.size = Vector2(640, 360); add_child(bg)
	view = DodgeBoxView.new(); add_child(view)
	pattern = load("res://tests/dodge_preview.gd").make(boss, 1234 + turn, phase, turn)
	_run.call_deferred()

func _run() -> void:
	var frame: int = 0
	while not pattern.done:
		var choice: Dictionary = bot.choose(pattern)
		D.step(pattern, choice.axis, bool(choice.get("precision", false)), 1.0, false, true, choice.press)
		view.show_pattern(pattern, Vector2(192, 166))
		await RenderingServer.frame_post_draw
		if frame % every == 0:
			var image: Image = get_viewport().get_texture().get_image()
			image.save_png(out.path_join("%s-%s-p%d-%04d.png" % [boss, pattern.patternId, phase, frame]))
		frame += 1
	print("done ", boss, " ", pattern.patternId, " hits ", pattern.hits, " grazes ", pattern.grazes, " promise ", pattern.promiseComplete)
	get_tree().quit()
