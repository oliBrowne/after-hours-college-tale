extends SceneTree
## Standalone headless or native viewport runner, also shares exported main harness.
func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var scene: PackedScene = load("res://scenes/main.tscn")
	var main: Node = scene.instantiate()
	root.add_child(main)
	await process_frame
	var harness: Node = load("res://scenes/qa_opening.gd").new()
	main.add_child(harness)
	var passed: bool = await harness.run(main)
	quit(0 if passed else 1)
