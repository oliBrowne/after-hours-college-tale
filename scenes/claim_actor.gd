class_name ClaimActor
extends Node2D

# CLAIM's original pixel construction: rack, mismatched sleeves, ticket eyes and wheels.
# Position is the bottom centre; visual extent is approximately Rect2(-34,-80,68,80).
var pose: String = "idle"
var elapsed: float = 0.0
var reduced_motion: bool = false

func set_pose(value: String) -> void:
	if pose != value:
		pose = value
		elapsed = 0.0
		queue_redraw()

func step(delta: float) -> void:
	elapsed += clampf(delta,0.0,0.1)
	queue_redraw()

func _r(x: float,y: float,w: float,h: float,color: Color) -> void:
	draw_rect(Rect2(roundf(x),roundf(y),roundf(w),roundf(h)),color)

func _l(a: Vector2,b: Vector2,color: Color,width: float=1.0) -> void:
	draw_line(a.round(),b.round(),color,width,false)

func _p(points: Array,color: Color) -> void:
	draw_colored_polygon(PackedVector2Array(points),color)

func _oval(cx: int,cy: int,rx: int,ry: int,color: Color) -> void:
	for yy in range(-ry,ry+1):
		var span=floori(float(rx)*sqrt(maxf(0.0,1.0-float(yy*yy)/float(ry*ry))))
		_r(cx-span,cy+yy,span*2+1,1,color)

func _draw() -> void:
	NativeCastArt.draw_body(self, "claim", pose, 88, elapsed, reduced_motion)
