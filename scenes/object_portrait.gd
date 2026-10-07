class_name ObjectPortrait
extends Control

# Original native pixel portraits for object speakers. Transparent; UI owns the frame.
const INK = Color("171a2b")
const CREAM = Color("e6d6b1")
const GOLD = Color("e8b45c")
const STONE = Color("b5816c")
const WOOD = Color("805a58")
const SAGE = Color("5c897c")
var speaker: String = "Pip"
var expression: int = 0

static func supports(name: String) -> bool:
	return name.to_lower().replace(" ","") in ["pip","claim","pinpal"]

func _ready() -> void:
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	custom_minimum_size=Vector2(80,80)
	if size==Vector2.ZERO:size=Vector2(80,80)
	clip_contents=true

func configure(name: String, face: Variant = 0) -> void:
	speaker=name
	if face is int:
		expression=clampi(face,0,3)
	else:
		var names={"neutral":0,"warm":1,"amused":1,"concern":2,"surprised":2,"resolved":3,"happy":3}
		expression=int(names.get(String(face),0))
	queue_redraw()

func _notification(what: int) -> void:
	if what==NOTIFICATION_RESIZED:queue_redraw()

func _r(x: float,y: float,w: float,h: float,color: Color) -> void:
	draw_rect(Rect2(x,y,w,h),color)

func _l(a: Vector2,b: Vector2,color: Color,width: float=1) -> void:
	draw_line(a,b,color,width,false)

func _p(points: Array,color: Color) -> void:
	draw_colored_polygon(PackedVector2Array(points),color)

func _draw() -> void:
	var factor=minf(size.x/80.0,size.y/80.0)
	if factor<=0:return
	if factor>=1.0:factor=floorf(factor)
	draw_set_transform((size-Vector2(80,80)*factor)/2.0,0,Vector2.ONE*factor)
	match speaker.to_lower().replace(" ",""):
		"claim":_claim()
		"pinpal":_pin()
		_:_pip()
	draw_set_transform(Vector2.ZERO,0,Vector2.ONE)

func _pip() -> void:
	var finger=3 if expression in [1,3] else 0
	_p([Vector2(22,64),Vector2(15,37),Vector2(15,24),Vector2(21,22),Vector2(26,33),Vector2(27,9-finger),Vector2(34,6-finger),Vector2(39,29),Vector2(43,5+finger),Vector2(49,7+finger),Vector2(50,29),Vector2(57,15),Vector2(64,18),Vector2(62,44),Vector2(70,38),Vector2(77,43),Vector2(65,61),Vector2(59,73),Vector2(26,74)],INK)
	_p([Vector2(25,62),Vector2(18,36),Vector2(18,26),Vector2(20,25),Vector2(28,39),Vector2(30,11-finger),Vector2(33,10-finger),Vector2(38,36),Vector2(46,9+finger),Vector2(48,12+finger),Vector2(47,37),Vector2(59,19),Vector2(61,21),Vector2(59,49),Vector2(70,41),Vector2(73,44),Vector2(62,59),Vector2(56,69),Vector2(28,69)],SAGE)
	_l(Vector2(26,37),Vector2(30,46),Color("3f615c"),2)
	_l(Vector2(39,31),Vector2(39,42),Color("3f615c"),2)
	_l(Vector2(52,33),Vector2(49,44),Color("3f615c"),2)
	_l(Vector2(21,34),Vector2(25,51),Color("b9d5bc"),2)
	_r(22,66,40,12,CREAM)
	for xx in range(25,61,5):_r(xx,69,2,6,Color("3f615c"))
	if expression==3:
		_l(Vector2(29,47),Vector2(35,44),INK,2)
		_l(Vector2(48,44),Vector2(54,47),INK,2)
	else:
		_r(29,45,6,5,INK)
		_r(48,45,6,5,INK)
		_r(32,45,1,1,CREAM)
		_r(51,45,1,1,CREAM)
	if expression==2:
		_r(38,55,7,6,Color("3f615c"))
	elif expression in [1,3]:
		_l(Vector2(36,56),Vector2(42,61),Color("3f615c"),2)
		_l(Vector2(42,61),Vector2(49,55),Color("3f615c"),2)
	else:_r(37,56,10,2,Color("3f615c"))

func _claim() -> void:
	# Close-up roller/dispenser face, framed by real hooks, cloth and ticket strips.
	_r(36,0,8,74,INK)
	_r(38,1,4,72,WOOD)
	_p([Vector2(4,22),Vector2(5,12),Vector2(12,9),Vector2(18,16),Vector2(40,7),Vector2(63,17),Vector2(66,8),Vector2(75,10),Vector2(77,22),Vector2(70,23),Vector2(69,15),Vector2(64,23),Vector2(40,15),Vector2(16,23),Vector2(10,17),Vector2(10,23)],INK)
	_l(Vector2(17,17),Vector2(40,10),STONE,2)
	_l(Vector2(41,10),Vector2(63,18),STONE,2)
	_p([Vector2(12,21),Vector2(22,24),Vector2(23,44),Vector2(16,62),Vector2(5,60),Vector2(6,41)],Color("425da6"))
	_l(Vector2(14,25),Vector2(11,53),Color("6b81bf"),2)
	_r(5,57,12,5,CREAM)
	_p([Vector2(60,21),Vector2(72,20),Vector2(76,43),Vector2(68,68),Vector2(56,66),Vector2(53,44)],Color("9e4e52"))
	_l(Vector2(64,26),Vector2(63,60),Color("c37361"),2)
	_r(57,62,13,5,STONE)
	_r(22,26,37,41,INK)
	_r(25,28,31,35,STONE)
	_r(27,32,27,24,CREAM)
	_r(27,57,27,5,WOOD)
	_r(29,22,24,8,WOOD)
	_r(32,24,18,4,CREAM)
	if expression in [1,3]:
		_l(Vector2(31,42),Vector2(36,39),INK,2)
		_l(Vector2(44,39),Vector2(49,42),INK,2)
	else:
		_r(31,40,6,6,INK)
		_r(44,40,6,6,INK)
		_r(34,40,1,1,GOLD)
		_r(47,40,1,1,GOLD)
		if expression==2:
			_l(Vector2(30,36),Vector2(37,38),WOOD)
			_l(Vector2(43,38),Vector2(50,36),WOOD)
	_r(29,56,24,4,INK)
	_r(34,60,15,20,CREAM)
	_r(37,62,9,2,Color("9e4e52"))
	_r(38,68,2,7,INK)
	_r(42,68,2,7,INK)
	_l(Vector2(14,43),Vector2(19,48),INK)
	_r(17,48,8,13,CREAM)
	_r(19,51,4,2,WOOD)

func _pin() -> void:
	# Framed close-up keeps head, red neck bands and worn enamel visible together.
	_p([Vector2(31,4),Vector2(49,4),Vector2(60,16),Vector2(60,31),Vector2(50,44),Vector2(49,56),Vector2(63,77),Vector2(18,77),Vector2(31,56),Vector2(30,45),Vector2(20,31),Vector2(20,17)],INK)
	_p([Vector2(33,7),Vector2(47,7),Vector2(57,17),Vector2(57,30),Vector2(47,43),Vector2(46,57),Vector2(59,76),Vector2(22,76),Vector2(34,57),Vector2(33,44),Vector2(23,30),Vector2(23,18)],CREAM)
	_l(Vector2(27,20),Vector2(27,30),Color("faf0d5"),2)
	_l(Vector2(50,20),Vector2(53,31),STONE,2)
	_r(29,51,23,5,Color("9e4e52"))
	_r(28,61,26,5,Color("9e4e52"))
	_r(17,22,22,12,INK)
	_r(44,22,22,12,INK)
	_l(Vector2(37,26),Vector2(45,26),INK,3)
	_l(Vector2(21,24),Vector2(30,24),Color("6b81bf"),2)
	_l(Vector2(47,24),Vector2(57,24),Color("6b81bf"),2)
	_l(Vector2(17,24),Vector2(22,19),INK,2)
	if expression in [1,3]:
		_l(Vector2(34,39),Vector2(40,43),STONE,2)
		_l(Vector2(40,43),Vector2(48,37),STONE,2)
	elif expression==2:_r(38,39,7,5,STONE)
	else:_r(35,39,12,2,STONE)
	_l(Vector2(28,72),Vector2(35,74),STONE)
	_r(51,72,2,3,STONE)
