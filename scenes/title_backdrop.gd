class_name BoulderTitleBackdrop
extends Node2D

var seconds: float = 0.0
var picture: Sprite2D
var wind: ShaderMaterial

func _ready() -> void:
	picture = Sprite2D.new()
	picture.texture = load("res://assets/art/boulder-title-v2.png")
	picture.centered = false
	picture.show_behind_parent = true
	picture.scale = Vector2(640.0 / picture.texture.get_width(), 360.0 / picture.texture.get_height())
	picture.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var shader: Shader = Shader.new()
	shader.code = "shader_type canvas_item; uniform float wind_time = 0.0; void fragment(){ vec2 p = UV; float canopy = smoothstep(0.70,0.95,p.x) * (1.0-smoothstep(0.40,0.70,p.y)); p.x += sin(wind_time*1.1+p.y*11.0)*0.0028*canopy; p = floor(p*vec2(640.0,360.0))/vec2(640.0,360.0); COLOR = texture(TEXTURE,p); }"
	wind = ShaderMaterial.new()
	wind.shader = shader
	picture.material = wind
	add_child(picture)

func step(delta: float, reduced: bool = false) -> void:
	if not reduced:
		seconds += delta
	wind.set_shader_parameter("wind_time", seconds)
	queue_redraw()

func _draw() -> void:
	for i: int in range(8):
		var x: float = 240.0 + fmod(i * 37.0 + seconds * (7.0 + i % 3), 400.0)
		var y: float = 22.0 + fmod(i * 23.0 + seconds * 9.0, 240.0)
		draw_rect(Rect2(floorf(x), floorf(y + sin(seconds + i) * 5), 2, 1), Color(0.9, 0.5, 0.22, 0.32))
	for i: int in range(7):
		var x: float = 440 + i * 17 + sin(seconds * 0.35 + i) * 3
		var y: float = 286 - fmod(seconds * 6 + i * 9, 35)
		draw_rect(Rect2(floorf(x), floorf(y), 1, 2), Color(1.0, 0.84, 0.63, 0.12))
