class_name CombatVFX
extends Node2D

# Only step() advances time. No timers, random calls, Tween or render-rate state.
var effects: Array[Dictionary] = []
var font: Font = preload("res://assets/art/afterhours-font.fnt")
var reduced_flashes: bool = false

func play(kind: String, origin: Vector2, target: Vector2, damage: int = 0, text: String = "") -> void:
	var lifetime = 0.6
	match kind:
		"guard", "shield", "heal", "promise": lifetime = 0.8
		"dissolve", "foe_dissolve": lifetime = 1.0
		"hit", "impact": lifetime = 0.52
		"crit", "combo": lifetime = 0.95
	if effects.size() >= 32:
		effects.pop_front()
	effects.append({"kind":kind,"origin":origin,"target":target,"damage":damage,"text":text,"age":0.0,"life":lifetime})
	# The number gets its own, longer-lived pop so it can be read after the burst fades.
	if damage > 0:
		effects.append({"kind":"number","origin":origin,"target":target,"damage":damage,"heal":kind == "heal","age":0.0,"life":1.1})
	queue_redraw()

func step(seconds: float) -> void:
	var dt = clampf(seconds, 0.0, 0.1)
	for effect in effects:
		effect.age += dt
	for index in range(effects.size() - 1, -1, -1):
		if effects[index].age >= effects[index].life:
			effects.remove_at(index)
	queue_redraw()

func clear() -> void:
	effects.clear()
	queue_redraw()

func is_active() -> bool:
	return not effects.is_empty()

func _square(center: Vector2, size: float, color: Color) -> void:
	draw_rect(Rect2((center-Vector2.ONE*size/2).round(),Vector2.ONE*size),color)

func _line(a: Vector2, b: Vector2, color: Color, width: float = 1.0) -> void:
	draw_line(a.round(),b.round(),color,width,false)

func _burst(target: Vector2, t: float, color: Color, count: int = 12) -> void:
	for i in count:
		var angle=float(i)*TAU/float(count)
		var direction=Vector2(cos(angle),sin(angle))
		var distance=6.0+t*(24.0+float((i*7)%13))
		var center=target+direction*distance+Vector2(0,t*t*18.0)
		_square(center,3.0 if i%3==0 else 2.0,Color(color,1.0-t))

func _ring(target: Vector2, radius: float, color: Color, segments: int = 16) -> void:
	for i in segments:
		var a=float(i)*TAU/float(segments)
		var b=float(i+1)*TAU/float(segments)
		_line(target+Vector2(cos(a),sin(a))*radius,target+Vector2(cos(b),sin(b))*radius,color,2)

func _draw() -> void:
	for effect in effects:
		var t=clampf(effect.age/effect.life,0.0,1.0)
		var origin:Vector2=effect.origin
		var target:Vector2=effect.target
		var ink=Color("171a2b")
		var cream=Color("e6d6b1")
		var gold=Color("e8b45c")
		var mint=Color("b9d5bc")
		match effect.kind:
			"strike", "slash":
				var tip=origin.lerp(target,minf(1.0,t*3.0))
				var direction=(target-origin).normalized()
				if t<0.38:
					_line(tip-direction*25.0,tip,Color("9e4e52"),5)
					_line(tip-direction*17.0,tip,cream,2)
				else:
					var slash=clampf((t-0.38)/0.4,0.0,1.0)
					_line(target+Vector2(-16+slash*11,17-slash*11),target+Vector2(15-slash*5,-18+slash*5),Color(cream,1-t),3)
					_burst(target,(t-0.38)/0.62,gold,10)
			"hit", "impact":
				_burst(target,t,gold)
				if t<0.24 and not reduced_flashes:
					_line(target+Vector2(-9,-9),target+Vector2(9,9),cream,3)
					_line(target+Vector2(9,-9),target+Vector2(-9,9),cream,3)
			"guard", "shield":
				var alpha=1.0-t*0.8
				_ring(target,10.0+t*20.0,Color(mint,alpha))
				_ring(target,7.0+t*13.0,Color(gold,alpha*0.6),12)
				var points=PackedVector2Array([target+Vector2(-10,-14),target+Vector2(10,-14),target+Vector2(11,1),target+Vector2(0,13),target+Vector2(-11,1),target+Vector2(-10,-14)])
				for i in points.size()-1:_line(points[i],points[i+1],Color(cream,alpha),2)
			"heal", "promise":
				for i in 7:
					var x=float((i*17)%45)-22.0
					var position=target+Vector2(x,15.0-t*40.0-float((i*7)%13))
					_line(position+Vector2(-3,0),position+Vector2(3,0),Color(mint,1-t))
					_line(position+Vector2(0,-3),position+Vector2(0,3),Color(mint,1-t))
			"dissolve", "foe_dissolve":
				for y in 7:
					for x in 7:
						var lag=float((x*3+y*5)%9)*0.035
						var phase=maxf(0.0,t-lag)
						var position=target+Vector2((x-3)*5,(y-3)*5)+Vector2((x-3)*phase*8,-phase*(12+float((x+y)%5)*5))
						_square(position,3,Color(cream if (x+y)%2==0 else gold,1-t))
			"number":
				pass
			"crit", "combo":
				if effect.kind == "crit":
					_burst(target, t, gold, 20)
					_ring(target, 8.0 + t * 34.0, Color(cream, 1.0 - t))
				_text(effect, t, gold if effect.kind == "crit" else mint)
			_:
				_burst(target,t,mint,8)
		if effect.kind=="number":_number(effect,t)

## Damage (warm) and healing (green) numbers: the pixel font at 2x, a 2px ink outline, a quick
## pop from 1.6x, a short rise, and a fade only at the end.
func _number(effect: Dictionary, t: float) -> void:
	var heal: bool = effect.get("heal", false)
	var label: String = ("+" if heal else "") + str(effect.damage)
	var size: int = 24
	var width: float = font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var pop: float = 1.0 + 0.6 * pow(1.0 - clampf(t / 0.14, 0.0, 1.0), 2.0)
	var rise: float = 6.0 + 14.0 * minf(1.0, t / 0.5)
	var alpha: float = 1.0 - clampf((t - 0.7) / 0.3, 0.0, 1.0)
	var fill: Color = Color("8fe39a") if heal else Color("ffb45a") if int(effect.damage) < 12 else Color("ff7a52")
	var anchor: Vector2 = (effect.target as Vector2) + Vector2(0, -24 - rise)
	draw_set_transform(anchor.round(), 0.0, Vector2(pop, pop))
	var base: Vector2 = Vector2(-roundf(width * 0.5), 8)
	var ink: Color = Color("0d101c", alpha)
	for nudge: Vector2 in [Vector2(-2, 0), Vector2(2, 0), Vector2(0, -2), Vector2(0, 2), Vector2(-2, -2), Vector2(2, -2), Vector2(-2, 2), Vector2(2, 2)]:
		draw_string(font, base + nudge, label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, ink)
	draw_string(font, base, label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(fill, alpha))
	draw_set_transform(Vector2.ZERO)

## A short banner word ("CRIT!", "COMBO x1.4") that pops and rises above the target.
func _text(effect: Dictionary, t: float, color: Color) -> void:
	var label: String = str(effect.get("text", ""))
	if label.is_empty(): return
	var size: int = 16
	var width: float = font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var at: Vector2 = Vector2(effect.target) + Vector2(-width / 2.0, -30.0 - 16.0 * minf(1.0, t / 0.5))
	var alpha: float = 1.0 - clampf((t - 0.7) / 0.3, 0.0, 1.0)
	for offset: Vector2 in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1)]:
		draw_string(font, (at + offset).round(), label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(Color("171a2b"), alpha))
	draw_string(font, at.round(), label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(color, alpha))
