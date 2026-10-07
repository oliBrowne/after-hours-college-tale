class_name NativeKeepsakeGlint
extends Node2D
## A small keepsake lying on the floor, with a slow twinkle so quiet corners are worth a look.

const GOLD: Color = Color("e8b45c")
const CREAM: Color = Color("fff3d6")
const SHADOW: Color = Color(0.05, 0.06, 0.1, 0.45)
var elapsed: float = 0.0
var reduced_motion: bool = false

func set_pose(_pose: String) -> void:
	pass

## Called by main every physics tick, like the other scene props.
func step(delta: float) -> void:
	elapsed = fmod(elapsed + delta, 2.4)
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(-5, -1, 10, 2), SHADOW)
	draw_rect(Rect2(-4, -5, 8, 4), GOLD)
	draw_rect(Rect2(-3, -5, 2, 1), CREAM)
	# One short twinkle every 2.4 seconds; a soft constant dot otherwise.
	var t: float = elapsed / 0.5
	if t < 1.0 and not reduced_motion:
		var reach: float = 2.0 + 3.0 * sin(t * PI)
		var color: Color = Color(CREAM, 0.9)
		draw_line(Vector2(2, -9 - reach), Vector2(2, -9 + reach), color, 1)
		draw_line(Vector2(2 - reach, -9), Vector2(2 + reach, -9), color, 1)
	else:
		draw_rect(Rect2(2, -9, 1, 1), Color(CREAM, 0.6))
