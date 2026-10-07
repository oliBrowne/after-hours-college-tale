class_name PipActor
extends Node2D

# Original animated lost glove, wrist planted at the node origin.
var pose: String = "idle"
var elapsed: float = 0.0
var reduced_motion: bool = false

func set_pose(value: String) -> void:
	if pose!=value:
		pose=value
		elapsed=0.0
		queue_redraw()

func step(delta: float) -> void:
	elapsed+=clampf(delta,0.0,0.1)
	queue_redraw()

func _r(x: float,y: float,w: float,h: float,color: Color) -> void:
	draw_rect(Rect2(roundf(x),roundf(y),roundf(w),roundf(h)),color)

func _l(a: Vector2,b: Vector2,color: Color) -> void:
	draw_line(a.round(),b.round(),color,1,false)

func _draw() -> void:
	NativeCastArt.draw_body(self, "pip", pose, 36, elapsed, reduced_motion)
