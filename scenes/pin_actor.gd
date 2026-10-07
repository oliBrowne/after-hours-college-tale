class_name PinActor
extends Node2D

# Pin Pal: scuffed enamel bowling pin wearing borrowed sunglasses, original pixel drawing.
# Position is the planted bottom centre; visual bounds are approximately (-19,-76,38,76).
var pose: String = "idle"
var elapsed: float = 0.0
var reduced_motion: bool = false

func set_pose(value: String) -> void:
	if value!=pose:
		pose=value
		elapsed=0.0
		queue_redraw()

func step(delta: float) -> void:
	elapsed+=clampf(delta,0.0,0.1)
	queue_redraw()

func _r(x: float,y: float,w: float,h: float,color: Color) -> void:
	draw_rect(Rect2(roundf(x),roundf(y),roundf(w),roundf(h)),color)

func _l(a: Vector2,b: Vector2,color: Color,width: float=1.0) -> void:
	draw_line(a.round(),b.round(),color,width,false)

func _p(points: Array,color: Color) -> void:
	draw_colored_polygon(PackedVector2Array(points),color)

func _draw() -> void:
	NativeCastArt.draw_body(self, "pinpal", pose, 76, elapsed, reduced_motion)
