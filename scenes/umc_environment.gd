class_name UMCEnvironment
extends Node2D

# Original integer-grid architectural drawings. No inherited map screenshot is used.
const INK = Color("171a2b")
const PLUM = Color("353047")
const STONE = Color("b5816c")
const STONE_DARK = Color("805a58")
const STONE_LIGHT = Color("cea489")
const CREAM = Color("e6d6b1")
const RUST = Color("9e4e52")
const AMBER = Color("e8b45c")
const GOLD = Color("f4d28b")
const SAGE = Color("5c897c")
const GREEN = Color("374a46")
const BLUE = Color("425da6")
const BLUE_DARK = Color("283866")
const PAVE = Color("686475")
const FONT = preload("res://assets/art/afterhours-font.fnt")

var room_id: String = "U01"
var layout: Dictionary = {}
var room_flags: Dictionary = {}
var glove_claimed: bool = false:
	set(value):
		glove_claimed = value
		queue_redraw()
var reduced_motion: bool = false
var elapsed: float = 0.0
var last_ambient_beat: int = -1
var arrival_progress: float = 1.0
var arrival_origin: Vector2 = Vector2(96,258)
var foreground_nodes: Array[Node2D] = []
var foreground_active: bool = false
signal ambient_event(cue: String)

func configure(id: String, definition: Dictionary = {}, flags: Dictionary = {}) -> void:
	room_id = id
	layout = definition
	room_flags = flags
	elapsed = 0.0
	last_ambient_beat = -1
	_rebuild_foreground()
	queue_redraw()

func set_arrival(progress: float) -> void:
	arrival_progress=clampf(progress,0.0,1.0)
	queue_redraw()

func context_lines(id: String, flags: Dictionary = {}) -> Array:
	var resolution=String(flags.get("pinpal_resolution",""))
	if id in ["scoreboard","scorecard"]:
		if resolution=="peaceful":return [["Imani","One practice round. Nobody's name became a number.","warm"],["Walt","The board has switched from scores to the next player's turn.","neutral"]]
		if not resolution.is_empty():return [["Walt","The scoreboard has a repair note. The names are still legible.","neutral"],["Jules","We can put the next player first while we repair it.","warm"]]
		return [["Jules","The board lists people, then refuses to rank them.","neutral"],["Imani","Pin Pal wants a practice partner. One round can be a complete promise.","warm"]]
	if id=="ball_return":
		if not resolution.is_empty():return [["Walt","One ball is waiting quietly. The return stopped asking for every ball at once.","warm"]]
		return [["Walt","The return paddle is working. Pin Pal keeps sending the same ball back.","neutral"],["Jules","We should ask what one round actually means before agreeing to play forever.","concern"]]
	return []

class ConnectionProp extends Node2D:
	var kind: String = "bench"
	var span: int = 80
	const FONT=preload("res://assets/art/afterhours-font.fnt")
	func r(x: float,y: float,w: float,h: float,c: Color) -> void:draw_rect(Rect2(roundf(x),roundf(y),roundf(w),roundf(h)),c)
	func _draw() -> void:
		var ink=Color("171a2b")
		var wood=Color("805a58")
		var cream=Color("e6d6b1")
		var amber=Color("e8b45c")
		var left=-span/2.0
		r(left+2,-1,span,3,Color(ink,0.3))
		match kind:
			"bench":
				r(left,-36,span,24,ink)
				r(left+3,-33,span-6,18,Color("425da6"))
				r(left+5,-31,span-10,2,Color("6b81bf"))
				r(left-2,-13,span+4,6,wood)
				r(left,-12,span,2,cream)
				r(left+7,-7,4,7,ink)
				r(left+span-11,-7,4,7,ink)
			"table":
				r(left,-22,span,13,wood)
				r(left+2,-21,span-4,3,Color("cea489"))
				r(left+6,-9,4,9,ink)
				r(left+span-10,-9,4,9,ink)
				for xx in [left+9,left+span-25]:
					r(xx,-29,16,12,cream)
					r(xx+3,-26,9,2,Color("9e4e52"))
				r(left+span/2-4,-29,8,10,Color("e8b45c"))
			"return":
				r(left,-38,span,31,ink)
				r(left+3,-36,span-6,23,wood)
				r(left+5,-34,12,12,Color("9e4e52"))
				r(left+span-18,-34,12,12,Color("425da6"))
				r(left+7,-32,2,2,ink)
				r(left+9,-28,2,2,ink)
				r(left+span-15,-32,2,2,ink)
				r(left+4,-12,span-8,5,cream)
				r(left+5,-7,4,7,ink)
				r(left+span-9,-7,4,7,ink)
			"arcade":
				r(left,-82,span,81,ink)
				r(left+4,-78,span-8,37,Color("9e4e52"))
				r(left+7,-73,span-14,27,Color("283866"))
				r(left+11,-67,5,5,amber)
				r(left+span-18,-61,7,6,Color("5c897c"))
				r(left+3,-35,span-6,8,cream)
				r(left+10,-38,3,6,Color("9e4e52"))
				r(left+span-11,-33,3,2,Color("425da6"))
				r(left+5,-23,span-10,18,Color("353047"))
			"scoreboard":
				r(-3,-41,6,39,ink)
				r(left,-49,span,32,ink)
				r(left+3,-46,span-6,26,Color("283866"))
				draw_string(FONT,Vector2(left+7,-34),"NEXT UP",HORIZONTAL_ALIGNMENT_LEFT,-1,12,amber)
				for yy in [-29,-25]:r(left+8,yy,span-16,1,cream)
				r(left+9,-3,span-18,3,ink)

func _connection_props() -> Array:
	return [{"kind":"bench","x":150,"y":402,"w":98},{"kind":"bench","x":460,"y":402,"w":100},{"kind":"table","x":229,"y":428,"w":76},{"kind":"table","x":459,"y":450,"w":76},{"kind":"return","x":241,"y":343,"w":40},{"kind":"return","x":402,"y":343,"w":40},{"kind":"return","x":527,"y":343,"w":40},{"kind":"scoreboard","x":472,"y":343,"w":72},{"kind":"arcade","x":715,"y":289,"w":42},{"kind":"arcade","x":775,"y":289,"w":42},{"kind":"arcade","x":835,"y":289,"w":42},{"kind":"bench","x":845,"y":397,"w":84},{"kind":"table","x":742,"y":416,"w":96}]

func _rebuild_foreground() -> void:
	for node in foreground_nodes:
		if is_instance_valid(node) and not node.is_queued_for_deletion():node.queue_free()
	foreground_nodes.clear()
	foreground_active=false
	var parent=get_parent()
	if not layout.get("placements", []).is_empty():
		var owner: Node = parent if parent is Node2D and parent.y_sort_enabled else self
		for index: int in layout.placements.size():
			var item: Dictionary = layout.placements[index]
			var prop := NativeSpatialProp.new()
			prop.configure(item, room_flags)
			prop.use_art(NativeRoomArt.prop_art(room_id, index), NativeRoomArt.label_only(room_id, index))
			owner.add_child(prop)
			foreground_nodes.append(prop)
		for piece: Node2D in NativeRoomArt.occluders(room_id):
			owner.add_child(piece)
			foreground_nodes.append(piece)
		foreground_active = true
		return
	if room_id!="U06":return
	var target: Node=self
	if parent is Node2D and (parent as Node2D).y_sort_enabled:target=parent
	for item in _connection_props():
		var node=ConnectionProp.new()
		node.kind=item.kind
		node.span=item.w
		node.position=Vector2(item.x,item.y)
		node.z_index=0
		target.add_child(node)
		foreground_nodes.append(node)
	foreground_active=true

func step(delta: float) -> void:
	elapsed += clampf(delta, 0.0, 0.1)
	for prop: Node2D in foreground_nodes:
		if prop is NativeSpatialProp: prop.reduced_motion=reduced_motion;prop.step(delta)
	if room_id in ["U01", "U02"]:
		var beat = floori(elapsed / 7.0)
		if beat != last_ambient_beat:
			last_ambient_beat = beat
			ambient_event.emit("bird_chirp" if beat % 3 != 2 else "leaf_rustle")
	queue_redraw()

func _r(x: float, y: float, w: float, h: float, color: Color) -> void:
	draw_rect(Rect2(roundf(x), roundf(y), roundf(w), roundf(h)), color)

func _l(a: Vector2, b: Vector2, color: Color, width: float = 1.0) -> void:
	draw_line(a.round(), b.round(), color, width, false)

func _p(points: Array, color: Color) -> void:
	draw_colored_polygon(PackedVector2Array(points), color)

func _oval(cx: int, cy: int, rx: int, ry: int, color: Color) -> void:
	for dy in range(-ry, ry + 1):
		var span = floori(float(rx) * sqrt(maxf(0.0, 1.0 - float(dy * dy) / float(ry * ry))))
		_r(cx - span, cy + dy, span * 2 + 1, 1, color)

func _label(text: String, x: int, y: int, color: Color = CREAM) -> void:
	draw_string(FONT, Vector2(x, y), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, color)

func _floor(color: Color = PAVE, top: int = 150, width: int = 600, bottom: int = 316) -> void:
	_r(20, top, width, bottom - top, color)
	for y in range(top, bottom, 16):
		_l(Vector2(20, y), Vector2(20+width, y), Color(color, 0.65).darkened(0.2))
		for x in range(20 + (16 if y % 32 == 0 else 0), 20+width, 32):
			_l(Vector2(x, y), Vector2(x, mini(y + 15, bottom)), color.darkened(0.2))
			_r(x + 2, y + 2, 23, 1, color.lightened(0.12))
			if (x + y) % 64 == 0:
				_r(x + 8, y + 8, 6, 1, color.lightened(0.06))

func _wall(x: int, y: int, w: int, h: int, dark: bool = false) -> void:
	var stone = STONE_DARK if dark else STONE
	_r(x, y, w, h, stone)
	for yy in range(y + 4, y + h, 12):
		_l(Vector2(x, yy), Vector2(x + w, yy), stone.darkened(0.23))
		for xx in range(x + (14 if yy % 24 == 0 else 0), x + w, 28):
			_l(Vector2(xx, yy), Vector2(xx, mini(yy + 11, y + h)), stone.darkened(0.23))
		_r(x + 2, yy + 1, w - 4, 1, stone.lightened(0.09))
	_r(x, y + h - 4, w, 4, CREAM)
	_r(x, y + h, w, 5, INK)

func _window(x: int, y: int, w: int = 28, h: int = 44, lit: bool = true) -> void:
	_r(x - 3, y - 3, w + 6, h + 6, CREAM)
	_r(x, y, w, h, BLUE_DARK)
	_r(x + 3, y + 3, w - 6, h - 6, Color("78634e") if lit else INK)
	_r(x + 4, y + 4, 6, h - 10, AMBER if lit else PLUM)
	_r(x + w / 2 - 1, y, 3, h, STONE_DARK)
	_r(x, y + h / 2, w, 3, STONE_DARK)

func _door(cx: int, bottom: int, name: String, width: int = 40) -> void:
	_r(cx - width / 2 - 5, bottom - 61, width + 10, 64, CREAM)
	_r(cx - width / 2 - 2, bottom - 57, width + 4, 58, INK)
	_r(cx - width / 2, bottom - 55, width, 54, STONE_DARK)
	_r(cx - width / 2 + 4, bottom - 50, width / 2 - 6, 34, BLUE_DARK)
	_r(cx + 2, bottom - 50, width / 2 - 6, 34, BLUE_DARK)
	_r(cx - 1, bottom - 55, 2, 54, INK)
	_r(cx - 5, bottom - 17, 2, 4, AMBER)
	_r(cx + 4, bottom - 17, 2, 4, AMBER)
	_r(cx - width / 2 - 8, bottom, width + 16, 4, STONE_LIGHT)
	_r(cx - width / 2 - 12, bottom + 4, width + 24, 3, CREAM)
	_r(cx - name.length() * 4 - 4, bottom - 76, name.length() * 8 + 8, 14, INK)
	_label(name, cx - name.length() * 4, bottom - 66, AMBER)

func _bottom_exit(cx: int, name: String, floor_y: int = 308) -> void:
	_r(cx - 32, floor_y, 64, 9, STONE_LIGHT)
	_r(cx - 22, floor_y+2, 44, 8, CREAM)
	_r(cx - 1, floor_y-16, 3, 13, AMBER)
	_p([Vector2(cx - 6, floor_y-9), Vector2(cx + 7, floor_y-9), Vector2(cx, floor_y-1)], AMBER)
	_label(name, cx - name.length() * 4, floor_y+27, CREAM)

func _lamp(x: int, y: int, short: bool = false) -> void:
	# Deliberate stepped warm light pools; only furniture casts a simple ink shadow.
	_r(x - 29, y - 1, 58, 10, Color(AMBER, 0.035))
	_r(x - 21, y, 42, 7, Color(AMBER, 0.065))
	_r(x - 12, y + 1, 24, 4, Color(AMBER, 0.095))
	var height = 30 if short else 53
	_r(x - 2, y - height, 4, height, INK)
	_r(x - 7, y - height - 10, 14, 13, INK)
	_r(x - 5, y - height - 8, 10, 8, AMBER)
	_r(x - 2, y - height - 7, 4, 6, GOLD)
	_p([Vector2(x - 9, y - height - 10), Vector2(x, y - height - 17), Vector2(x + 9, y - height - 10)], INK)
	_r(x - 9, y, 18, 3, INK)

func _bench(x: int, y: int, w: int = 68) -> void:
	_r(x, y, w, 6, INK)
	_r(x + 2, y - 8, w - 4, 10, STONE_DARK)
	for yy in range(y - 7, y + 1, 3):
		_r(x + 4, yy, w - 8, 1, STONE_LIGHT)
	_r(x + 7, y + 6, 4, 12, INK)
	_r(x + w - 11, y + 6, 4, 12, INK)

func _plant(x: int, y: int, large: bool = false) -> void:
	var size = 16 if large else 10
	_r(x - size / 2, y - 9, size, 13, STONE_DARK)
	_r(x - size / 2 - 2, y - 10, size + 4, 4, STONE_LIGHT)
	for leaf in [Vector2(-8, -18), Vector2(8, -23), Vector2(0, -30), Vector2(-10, -29)]:
		_l(Vector2(x, y - 10), Vector2(x, y - 28) + leaf / 2, SAGE)
		_oval(x + int(leaf.x), y + int(leaf.y), 7 if large else 5, 5, GREEN)
		_r(x + leaf.x - 2, y + leaf.y - 2, 4, 2, SAGE)

func _table(x: int, y: int, w: int = 64) -> void:
	_r(x + 3, y + 5, w, 7, Color(INK, 0.6))
	_r(x, y - 8, w, 14, STONE_DARK)
	_r(x + 2, y - 7, w - 4, 3, STONE_LIGHT)
	_r(x + 5, y + 6, 4, 12, INK)
	_r(x + w - 9, y + 6, 4, 12, INK)

func _tree(x: int, y: int) -> void:
	_r(x - 4, y - 23, 8, 30, INK)
	_r(x - 1, y - 23, 3, 26, STONE_DARK)
	for leaf in [Vector2(-15,-28), Vector2(16,-32), Vector2(0,-49), Vector2(-20,-47), Vector2(21,-51)]:
		_oval(x + int(leaf.x), y + int(leaf.y), 19, 15, GREEN)
		_oval(x + int(leaf.x) - 4, y + int(leaf.y) - 4, 11, 8, Color("53624d"))

func _draw() -> void:
	if not NativeRoomArt.manifest(room_id).is_empty():
		NativeRoomArt.draw_room(self, room_id, elapsed, reduced_motion, room_flags)
		if room_id == "U01": _arrival_action_visuals()
		return
	if room_id.begins_with("M"):
		NativeMackyEnvironment.draw(self,room_id,layout,room_flags,0.0 if reduced_motion else elapsed)
		return
	if room_id.begins_with("N") or room_id.begins_with("E") or room_id.begins_with("O"):
		NativeCampusEnvironment.draw(self,room_id,layout,room_flags,0.0 if reduced_motion else elapsed)
		return
	if room_id.begins_with("F"):
		NativeFestivalEnvironment.draw(self, room_id, layout, room_flags, 0.0 if reduced_motion else elapsed)
		return
	if not layout.is_empty():
		_draw_spatial()
		return
	_r(0, 0, 640, 360, INK)
	if room_id=="U06": _r(0,0,960,540,INK)
	match room_id:
		"U01": _arrival()
		"U02": _terrace()
		"U03": _atrium()
		"U04": _clubroom()
		"U05": _stairwell()
		"U06": _connection()
		"U07": _lost_property()
		_: _atrium()
	_fauna()

func _bird(x: int, y: int, phase: int) -> void:
	_r(x+2,y+8,1,3,STONE_DARK)
	_r(x+6,y+8,1,3,STONE_DARK)
	_p([Vector2(x,y+5),Vector2(x+4,y+2),Vector2(x+8,y+4),Vector2(x+7,y+8),Vector2(x+2,y+9)],STONE_LIGHT)
	_r(x+7,y+2,5,5,STONE_DARK)
	_r(x+9,y+3,1,1,INK)
	_r(x+12,y+4,3,1,AMBER)
	_p([Vector2(x,y+6),Vector2(x-4,y+3),Vector2(x-2,y+8)],PLUM)
	if phase==0:
		_r(x+3,y+4,4,3,PLUM)
	else:
		_p([Vector2(x+3,y+5),Vector2(x+1,y-2),Vector2(x+6,y+1),Vector2(x+7,y+6)],PLUM)

func _squirrel(x: int, y: int, phase: int) -> void:
	# Curled tail is an outlined hook, not an ellipse/primitive animal stand-in.
	_p([Vector2(x+11,y+8),Vector2(x+16,y+4),Vector2(x+18,y-2),Vector2(x+15,y-7),Vector2(x+11,y-8),Vector2(x+8,y-5),Vector2(x+9,y-1),Vector2(x+12,y),Vector2(x+11,y-4),Vector2(x+14,y-3),Vector2(x+15,y+1),Vector2(x+12,y+5)],STONE_DARK)
	_r(x+12,y-5,2,2,STONE_LIGHT)
	_p([Vector2(x,y+5),Vector2(x+5,y+2),Vector2(x+10,y+4),Vector2(x+12,y+8),Vector2(x+7,y+11),Vector2(x+1,y+9)],STONE)
	_r(x-2,y+1,7,6,STONE_LIGHT)
	_p([Vector2(x-1,y+1),Vector2(x-1,y-3),Vector2(x+2,y+1)],STONE_DARK)
	_r(x-1,y+3,1,1,INK)
	_r(x-4,y+5,3,1,INK)
	_r(x+(0 if phase==0 else 2),y+10,4,2,STONE_DARK)
	_r(x+8-(0 if phase==0 else 2),y+10,4,2,STONE_DARK)

func _fauna() -> void:
	var phase = floori(elapsed*5.0)%2
	if room_id=="U01":
		_bird(116+floori(sin(elapsed*0.35)*18.0),244,phase)
		_bird(153+floori(sin(elapsed*0.29+1.0)*15.0),259,0)
		_squirrel(535+floori(sin(elapsed*0.22)*18.0),327,phase)
	elif room_id=="U02":
		_bird(254+floori(sin(elapsed*0.32)*16.0),239,phase)
		_bird(286+floori(sin(elapsed*0.32+0.8)*12.0),252,0)
		_squirrel(28+floori(sin(elapsed*0.25)*5.0),327,phase)
	if room_id in ["U01","U02"]:
		for leaf in 8:
			var xx=40+(leaf*17)%43+floori(sin(elapsed*1.1+leaf)*2.0)
			var yy=73+(leaf*11)%39
			_r(xx,yy,3,1,SAGE)
			_r(560+xx%45,yy-8,3,1,SAGE)
	if room_id in ["U03","U05"]:
		var lamp_position=Vector2(442,234) if room_id=="U03" else Vector2(546,242)
		var point=(lamp_position+Vector2(cos(elapsed*1.7)*15.0,sin(elapsed*2.1)*10.0)).round()
		_r(point.x,point.y,2,3,CREAM)
		var spread=3 if phase==0 else 1
		_r(point.x-spread,point.y-1,spread,2,STONE_LIGHT)
		_r(point.x+2,point.y-1,spread,2,STONE_LIGHT)

func _arrival() -> void:
	_r(0,0,640,360,GREEN)
	_floor(PAVE)
	_r(0,150,18,167,INK)
	for yy in range(154,315,22): _r(0,yy,18,7,CREAM)
	_wall(77,54,244,83)
	for xx in [98,148,240,290]: _window(xx,74,20,38)
	_r(71,29,256,24,RUST)
	for yy in range(32,53,5): _l(Vector2(75,yy),Vector2(323,yy),Color("c37361"))
	_door(201,141,"UMC WAY",32)
	_wall(383,34,175,93)
	for xx in [401,448,504]: _window(xx,54,22,42)
	_r(377,10,187,24,RUST)
	_tree(45,126)
	_tree(597,124)
	# Glass bus shelter, timetable and worn route strip, distinct from the campus facades.
	_r(358,199,105,9,INK)
	_r(363,149,5,52,INK)
	_r(453,149,5,52,INK)
	_r(359,143,104,7,BLUE_DARK)
	_r(370,154,78,40,Color(BLUE,0.22))
	_r(416,157,20,30,CREAM)
	for yy in [161,166,171,176,181]: _r(419,yy,13,1,BLUE_DARK)
	_bench(370,198,78)
	_label("LAST BUS",372,139,AMBER)
	_lamp(74,218)
	_lamp(552,217)
	_bench(364,276,79)
	# Bicycle rack and original diamond-frame bike.
	for xx in [490,521]:
		_oval(xx,281,11,11,INK)
		_oval(xx,281,9,9,PAVE)
		_l(Vector2(xx-8,281),Vector2(xx+8,281),STONE_LIGHT)
		_l(Vector2(xx,273),Vector2(xx,289),STONE_LIGHT)
	_l(Vector2(490,281),Vector2(506,263),RUST,2)
	_l(Vector2(506,263),Vector2(513,281),RUST,2)
	_l(Vector2(490,281),Vector2(513,281),RUST,2)
	_l(Vector2(513,281),Vector2(522,262),RUST,2)
	_l(Vector2(501,262),Vector2(510,262),INK,2)
	_l(Vector2(519,261),Vector2(526,261),INK,2)
	_label("EUCLID / BROADWAY",32,339,CREAM)
	_bottom_exit(590,"UMC")
	_arrival_action_visuals()

func _terrace() -> void:
	_r(0,0,640,360,GREEN)
	_floor()
	_wall(126,55,388,103)
	_r(120,28,400,26,RUST)
	for yy in range(30,53,5): _l(Vector2(124,yy),Vector2(516,yy),Color("c37361"))
	for xx in [151,199,247,365,413,461]: _window(xx,76,25,43)
	_door(320,163,"UMC",46)
	for i in 3:
		_r(281-i*7,165+i*5,78+i*14,5,STONE_LIGHT)
		_r(284-i*7,169+i*5,72+i*14,1,STONE_DARK)
	_l(Vector2(269,154),Vector2(269,182),INK,2)
	_l(Vector2(372,154),Vector2(372,182),INK,2)
	_tree(45,122)
	_tree(588,119)
	_lamp(112,213)
	_lamp(536,212)
	for i in 11:
		var xx=112+i*38
		var yy=173+floori(sin(float(i)/10.0*PI)*11.0)
		_l(Vector2(xx,yy),Vector2(xx+38,yy+2 if i<5 else yy-2),INK)
		_r(xx,yy+1,3,4,AMBER)
		_r(xx+1,yy+2,1,2,GOLD)
	_bench(176,271,74)
	_table(407,265,78)
	for xx in [414,430,446,462]:
		_r(xx,253,10,9,CREAM)
		_r(xx+2,255,6,1,BLUE)
	_r(566,244,31,59,INK)
	_r(569,247,25,51,BLUE)
	_label("LAST",568,259,AMBER)
	_label("LIGHT",565,273,CREAM)
	_plant(548,284,true)
	_bottom_exit(80,"BROADWAY")

func _atrium() -> void:
	_floor(STONE_DARK)
	_wall(20,32,600,117)
	for xx in [38,183,401]: _window(xx,56,32,55)
	_door(110,169,"CLUB ROOM",42)
	# Full donated recording cabinet, with curtains, microphone and recording deck.
	_r(253,53,111,93,INK)
	_r(257,57,103,86,STONE_DARK)
	_r(262,62,93,15,AMBER)
	_label("NEXT YEAR",272,74,INK)
	_r(264,81,90,62,PLUM)
	for xx in [264,271,342,349]: _r(xx,81,5,60,BLUE)
	_table(287,125,43)
	_r(293,116,27,7,INK)
	_r(297,118,3,2,RUST)
	_r(303,118,12,2,SAGE)
	_l(Vector2(308,87),Vector2(308,113),INK,2)
	_oval(308,87,4,6,CREAM)
	_label("RECORD / LISTEN",263,158,CREAM)
	# Stair mouth is an actual rising stair flight, separate from the cabinet and doors.
	_r(481,80,112,108,INK)
	_r(488,85,98,104,STONE_DARK)
	for i in 10:
		_r(494,88+i*10,86,8,STONE_LIGHT)
		_r(494,94+i*10,86,2,STONE_DARK)
	_l(Vector2(487,86),Vector2(487,190),INK,3)
	_l(Vector2(586,86),Vector2(586,190),INK,3)
	_label("CONNECTION",483,72,AMBER)
	_r(523,183,18,4,AMBER)
	_r(530,175,4,12,AMBER)
	_table(206,195,69)
	_r(220,181,31,12,INK)
	for xx in range(223,248,5):
		_r(xx,184,2,5,BLUE)
		_r(xx,185,2,1,AMBER)
	_label("RETURN MIXER",194,225,CREAM)
	_bench(418,267,88)
	_lamp(442,271,true)
	_plant(40,267,true)
	_plant(589,273,true)
	# Inlaid compass and doorway threshold supply useful orientation.
	_l(Vector2(320,232),Vector2(320,258),CREAM)
	_l(Vector2(307,245),Vector2(333,245),CREAM)
	_r(315,240,11,11,STONE_LIGHT)
	_bottom_exit(320,"TERRACE")

func _clubroom() -> void:
	_floor(Color("635567"))
	_wall(20,32,600,116,true)
	_door(530,173,"CONNECTION",48)
	# Raised rehearsal stage with cable legs, acoustic wall panels and a drum kit.
	_r(38,115,377,33,STONE_DARK)
	_r(41,117,371,5,STONE_LIGHT)
	for xx in [49,96,144,191,240,289,338]:
		_r(xx,53,35,53,BLUE_DARK)
		for yy in [57,63,69,75,81,87,93]: _r(xx+4,yy,27,1,BLUE)
	_r(55,87,32,28,INK)
	_r(59,91,24,19,PLUM)
	for yy in [95,100,105]: _r(62,yy,18,1,STONE_DARK)
	_r(80,77,10,9,AMBER)
	_oval(213,103,17,14,RUST)
	_oval(213,103,13,10,CREAM)
	_r(205,97,16,2,PLUM)
	for xx in [181,245]:
		_l(Vector2(xx,86),Vector2(xx,119),INK,2)
		_oval(xx,83,14,3,AMBER)
		_l(Vector2(xx-8,120),Vector2(xx,113),INK)
		_l(Vector2(xx+8,120),Vector2(xx,113),INK)
	_oval(194,88,10,7,RUST)
	_oval(234,87,10,7,RUST)
	_l(Vector2(320,76),Vector2(320,123),INK,2)
	_oval(320,75,4,7,CREAM)
	_l(Vector2(308,124),Vector2(332,124),INK,2)
	_label("LAST LIGHT / REHEARSAL",77,135,AMBER)
	# Chairs stand to the right of the broad route; paper planes/recruitment board distinguish clubroom.
	for pos in [Vector2(348,208),Vector2(397,230),Vector2(445,207)]:
		_r(pos.x,pos.y-19,25,21,BLUE_DARK)
		_r(pos.x+3,pos.y-16,19,12,BLUE)
		_r(pos.x-2,pos.y+1,29,5,STONE_LIGHT)
		_r(pos.x+2,pos.y+6,3,9,INK)
		_r(pos.x+20,pos.y+6,3,9,INK)
	_table(137,271,91)
	for xx in [148,169,194]:
		_r(xx,259,17,12,CREAM)
		_r(xx+3,262,10,2,RUST)
	_r(567,217,31,60,STONE_DARK)
	_r(570,220,25,51,AMBER)
	for yy in [225,239,254]:
		_r(573,yy,19,11,CREAM)
		_r(576,yy+3,12,1,BLUE_DARK)
	_l(Vector2(79,126),Vector2(92,140),INK,2)
	_l(Vector2(92,140),Vector2(260,141),INK,2)
	_lamp(284,276,true)
	_bottom_exit(80,"ATRIUM")

func _stairwell() -> void:
	_floor(Color("697477"))
	_wall(20,28,600,119,true)
	# Large two-flight service stairwell: upper run, turning landing, lower run, iron rail.
	_r(58,64,239,98,INK)
	_r(64,69,225,88,STONE_DARK)
	for i in 9:
		_r(72,73+i*9,86,7,STONE_LIGHT)
		_r(72,79+i*9,86,2,STONE_DARK)
	_r(166,69,36,88,PLUM)
	for i in 9:
		_r(208,73+i*9,73,7,STONE_LIGHT)
		_r(208,79+i*9,73,2,STONE_DARK)
	_l(Vector2(67,66),Vector2(67,163),INK,3)
	_l(Vector2(162,66),Vector2(162,160),INK,3)
	_l(Vector2(203,66),Vector2(203,161),INK,3)
	_l(Vector2(286,66),Vector2(286,163),INK,3)
	_r(89,160,112,8,CREAM)
	_label("DOWN / CONNECTION",77,86,AMBER)
	_r(140,160,10,16,AMBER)
	_p([Vector2(135,169),Vector2(155,169),Vector2(145,178)],AMBER)
	# Exposed conduit, access hatch, tagged repair cart; no fantasy generic neon wall.
	_l(Vector2(329,42),Vector2(580,42),INK,4)
	_l(Vector2(580,42),Vector2(580,134),INK,4)
	_l(Vector2(331,40),Vector2(578,40),STONE_LIGHT)
	for xx in [356,419,489,548]: _r(xx,38,3,8,AMBER)
	_r(434,68,96,63,INK)
	_r(439,73,86,53,SAGE)
	_r(444,78,76,43,Color("3f615c"))
	for yy in [84,93,102,111]: _r(450,yy,64,2,INK)
	_r(492,122,16,7,AMBER)
	_label("SERVICE / 02",408,145,CREAM)
	_table(374,266,94)
	_r(382,246,32,13,INK)
	_r(385,249,26,9,RUST)
	_r(393,244,10,3,CREAM)
	_l(Vector2(426,248),Vector2(438,258),CREAM,2)
	_r(438,247,18,12,SAGE)
	for xx in [381,456]:
		_oval(xx,287,5,5,INK)
	_r(357,295,139,2,AMBER)
	for xx in range(362,494,12): _r(xx,296,5,2,INK)
	_lamp(546,279,true)
	_bench(223,270,83)
	_bottom_exit(80,"ATRIUM")

func _connection() -> void:
	_floor(Color("66606e"),150,920,510)
	_wall(20,30,920,119,true)
	_label("THE CONNECTION",234,27,AMBER)
	# Seven full-depth maple lanes remain visible in the entrance camera.
	_r(163,130,420,189,INK)
	for lane in 7:
		var xx=170+lane*58
		_r(xx,133,49,182,Color("bd9468"))
		for board in range(xx+3,xx+47,7):
			_r(board,135,1,177,Color("906c51"))
		for joint in range(152,302,29):
			_r(xx+3+(joint%3)*7,joint,13,1,Color("a58160"))
		_r(xx-3,132,3,183,PLUM)
		_r(xx+49,132,4,183,PLUM)
		_r(xx,306,49,3,CREAM)
		for arrow in [11,24,37]:
			_p([Vector2(xx+arrow,262),Vector2(xx+arrow-3,269),Vector2(xx+arrow+3,269)],STONE_DARK)
		for pin in [Vector2(24,159),Vector2(17,151),Vector2(31,151),Vector2(10,142),Vector2(24,142),Vector2(38,142)]:
			_r(xx+pin.x-2,pin.y,4,9,CREAM)
			_r(xx+pin.x-1,pin.y+2,2,2,RUST)
		_r(xx+15,109,21,12,BLUE_DARK)
		_label(str(lane+1),xx+22,119,AMBER)
	_label("ONE ROUND / ONE PROMISE",231,95,CREAM)
	# The approach apron connects the return machines to a compact social area.
	_r(164,319,419,30,Color("8b7370"))
	_r(164,347,419,2,STONE_LIGHT)
	_r(287,349,66,127,Color("84726e"))
	_r(350,350,287,28,Color("84726e"))
	_r(611,243,38,134,Color("84726e"))
	for yy in [367,398,429]:
		_p([Vector2(320,yy-6),Vector2(315,yy),Vector2(325,yy)],Color(AMBER,0.55))
	if layout.is_empty(): _label("LOST PROPERTY  >",481,387,AMBER)
	_r(601,196,60,7,STONE_LIGHT)
	_r(601,200,60,3,STONE_DARK)
	_label("PRACTICE",594,185,CREAM)
	# Shoe hire and Chip's western pocket have their own low divider and seats.
	_r(37,181,99,102,INK)
	_r(40,184,93,96,STONE_DARK)
	for yy in [202,224,246,269]:
		_r(44,yy,85,3,CREAM)
		for xx in [47,67,88,109]:
			_r(xx,yy-10,13,8,RUST if (xx+yy)%3==0 else BLUE)
			_r(xx+2,yy-3,11,2,STONE_LIGHT)
	_label("SHOE HIRE",39,174,CREAM)
	_r(44,294,89,3,AMBER)
	_label("CHIP'S CORNER",40,319,CREAM)
	_r(88,349,111,53,Color("625b77"))
	if layout.is_empty(): _lamp(72,390,true)
	# East arcade and lounge are a second destination, visibly beyond the practice gap.
	_r(684,190,177,104,Color("51485f"))
	_r(684,291,177,3,AMBER)
	_label("ARCADE / LAST CREDIT",687,187,CREAM)
	_r(686,360,215,72,Color("625b77"))
	_r(688,362,211,2,Color("8b7794"))
	_label("CLUB SCORECARDS",682,444,CREAM)
	if layout.is_empty(): _lamp(913,393,true)
	# Doorway recess and hand-painted route marks stay clear of the arcade footprint.
	_r(866,211,49,126,Color("84726e"))
	_r(848,329,44,8,Color("84726e"))
	_p([Vector2(888,253),Vector2(882,262),Vector2(894,262)],AMBER)
	_p([Vector2(888,287),Vector2(882,296),Vector2(894,296)],AMBER)
	if layout.is_empty(): _door(880,210,"LOST PROPERTY",48)
	if layout.is_empty(): _bottom_exit(320,"ATRIUM",480)

func _arrival_action_visuals() -> void:
	if arrival_progress>=1.0:return
	# Original narrow overhead bus: roof hatch, window banks, wheel wells and amber lamps.
	var by=roundi(178.0-pow(arrival_progress,1.6)*370.0)
	_r(24,by+5,47,141,Color(INK,0.35))
	_r(22,by,45,137,INK)
	_r(25,by+3,39,131,CREAM)
	_r(25,by+20,39,94,BLUE_DARK)
	_r(30,by+22,29,89,BLUE)
	_r(34,by+42,21,26,STONE_LIGHT)
	_r(37,by+45,15,20,STONE_DARK)
	for yy in [by+23,by+43,by+77,by+97]:
		_r(26,yy,5,13,INK)
		_r(58,yy,5,13,INK)
	_r(31,by+7,26,10,BLUE_DARK)
	_r(32,by+8,24,3,Color("6b81bf"))
	_r(27,by+2,5,2,AMBER)
	_r(57,by+2,5,2,AMBER)
	_r(27,by+130,5,2,RUST)
	_r(57,by+130,5,2,RUST)
	_r(20,by+29,3,20,INK)
	_r(65,by+29,3,20,INK)
	_r(20,by+96,3,20,INK)
	_r(65,by+96,3,20,INK)
	# The borrowed mixer tilts up into Jules's adjusting-hands pose, then settles into the bag.
	if arrival_progress<0.68:
		var lift=roundi(sin(minf(arrival_progress/0.68,1.0)*PI)*4.0)
		var mx=roundi(arrival_origin.x+12)
		var my=roundi(arrival_origin.y-22)-lift
		_r(mx,my,21,12,INK)
		_r(mx+2,my+2,17,8,STONE_DARK)
		for xx in [mx+4,mx+9,mx+14]:
			_r(xx,my+3,2,5,CREAM)
			_r(xx,my+4,2,2,AMBER)
		_r(mx+5,my-2,11,2,CREAM)

func _lost_property() -> void:
	_floor(Color("70686c"))
	_wall(20,28,600,121,true)
	_label("LOST PROPERTY / ADVISING",206,26,AMBER)
	# Numbered cubbies, mismatched belongings and a tagged trolley.
	for shelf in 3:
		var xx=38+shelf*151
		_r(xx,57,132,91,INK)
		_r(xx+3,60,126,85,STONE_DARK)
		for row in 3:
			for col in 4:
				var sx=xx+6+col*31
				var sy=64+row*26
				_r(sx,sy,27,22,PLUM)
				_r(sx+2,sy+19,23,2,STONE_LIGHT)
				var item=(shelf*7+row*4+col)%5
				match item:
					0:
						_p([Vector2(sx+5,sy+8),Vector2(sx+9,sy+3),Vector2(sx+16,sy+4),Vector2(sx+22,sy+10)],RUST)
						_r(sx+3,sy+10,21,3,RUST)
					1:
						_r(sx+8,sy+4,11,13,BLUE)
						_r(sx+11,sy+6,5,8,BLUE_DARK)
					2:
						_r(sx+7,sy+6,12,11,CREAM)
						_r(sx+10,sy+5,6,2,AMBER)
					3:
						_l(Vector2(sx+5,sy+7),Vector2(sx+22,sy+14),SAGE,3)
						_l(Vector2(sx+7,sy+14),Vector2(sx+18,sy+5),SAGE,2)
					4:
						_r(sx+6,sy+7,15,9,STONE_LIGHT)
						_r(sx+15,sy+6,4,3,CREAM)
				_r(sx+1,sy+1,7,3,CREAM)
	_table(106,251,97)
	if not glove_claimed:
		# Pip's individual glove shape: four fingers, thumb, cuff, stitched palm.
		_p([Vector2(143,235),Vector2(140,223),Vector2(142,219),Vector2(145,219),Vector2(146,224),Vector2(147,216),Vector2(150,216),Vector2(151,223),Vector2(152,216),Vector2(155,217),Vector2(155,225),Vector2(158,220),Vector2(161,222),Vector2(160,231),Vector2(166,228),Vector2(168,232),Vector2(160,240),Vector2(146,242)],SAGE)
		_r(145,239,14,6,CREAM)
		_l(Vector2(149,225),Vector2(149,235),Color("3f615c"))
		_l(Vector2(154,225),Vector2(153,235),Color("3f615c"))
		_label("UNCLAIMED",118,273,CREAM)
	else:
		# A departure note preserves the specific change after Pip leaves the table.
		_r(134,229,43,15,INK)
		_r(136,228,39,14,CREAM)
		_r(139,231,20,2,SAGE)
		_r(139,235,29,1,STONE_DARK)
		_r(139,238,23,1,STONE_DARK)
		_p([Vector2(169,228),Vector2(175,228),Vector2(175,234)],STONE_LIGHT)
		_label("LEFT A NOTE",110,273,CREAM)
	_r(478,75,92,91,INK)
	_r(484,80,80,82,STONE_DARK)
	_r(491,88,67,15,CREAM)
	_label("TICKETS",496,101,INK)
	_r(507,119,37,7,INK)
	_r(518,126,15,21,CREAM)
	_r(521,130,9,2,RUST)
	_r(521,139,9,1,PLUM)
	_lamp(564,271,true)
	_bench(376,280,82)
	_bottom_exit(320,"CONNECTION")

func _draw_spatial() -> void:
	var width: int = int(layout.dimensions[0])
	var height: int = int(layout.dimensions[1])
	_r(0, 0, width, height, INK)
	if room_id == "U06":
		_connection()
	else:
		var bounds: Array = layout.walk_bounds
		var top: int = int(bounds[1])
		_floor(Color("686475") if room_id in ["U01", "U02", "U03"] else Color("514b61") if room_id == "U04" else Color("68606a"), top, width - 40, height - 24)
		if room_id not in ["U01", "U02"]:
			_wall(20, 26, width - 40, top - 26, room_id in ["U05", "U07"])
			for x in range(45, width - 60, 78): _window(x, 48, 32, 43, room_id not in ["U05", "U07"])
		else:
			_r(0, 0, width, top, Color("53624d"))
			for yy in range(0, top, 8): _r(0, yy, width, 8, Color("a86468").lerp(Color("5c536c"), float(yy) / top))
			for peak in [Vector2(44, 36), Vector2(119, 20), Vector2(197, 29)]:
				_p([peak, peak + Vector2(-36, 61), peak + Vector2(19, 61)], STONE_DARK)
				_l(peak + Vector2(0, 3), peak + Vector2(-26, 55), STONE_LIGHT, 2)
			if room_id == "U01":
				_wall(227, 61, 174, 75); _wall(451, 40, 169, 96)
				_r(223, 48, 182, 14, RUST); _r(447, 27, 177, 14, RUST)
				for xx in [245, 301, 355]: _window(xx, 78, 21, 38)
				for xx in [472, 527, 578]: _window(xx, 57, 21, 43)
			else:
				_wall(219, 48, 267, 74); _r(215, 32, 275, 16, RUST)
				for xx in [241, 281, 376, 426]: _window(xx, 66, 25, 43)
			_tree(32, 127); _tree(602, 122)
		var names: Dictionary = {"U01":"BROADWAY / LAST BUS", "U02":"UMC / TERRACE", "U03":"ATRIUM / NEXT YEAR", "U04":"LAST LIGHT / CLUB ROOM", "U05":"REPAIR LANDING", "U07":"LOST PROPERTY / ONE THING"}
		_label(names.get(room_id, "THE CONNECTION"), 32, 22, AMBER)
		# Room-specific floor patterns expose the route rather than masking furniture.
		if room_id == "U03":
			_p([Vector2(383, 323), Vector2(394, 340), Vector2(383, 357), Vector2(372, 340)], STONE_DARK)
			_p([Vector2(383, 330), Vector2(389, 340), Vector2(383, 350), Vector2(377, 340)], STONE_LIGHT)
			_label("CLUB <", 39, 249, STONE_LIGHT); _label("REPAIR >", width - 146, 242, STONE_LIGHT)
		elif room_id == "U04":
			_r(126, 206, 528, 64, Color("5e4857")); _r(132, 267, 518, 2, AMBER)
			for x in range(177, 570, 47): _r(x, 279, 2, 11, STONE_DARK)
		elif room_id == "U05":
			for yy in range(153, 179, 6): _r(186, yy, 166, 2, STONE_DARK)
		elif room_id == "U07":
			for x in [180, 475, 602]: _r(x, 201, 2, 199, Color("84726e"))
			_label("SORT / RETURN / RELEASE", 315, 153, STONE_LIGHT)
		elif room_id in ["U01", "U02"]:

			_bird(120 + floori(sin(elapsed * 0.35) * 15), 301, floori(elapsed * 5) % 2)
			if room_id == "U02": _squirrel(173, 259, floori(elapsed * 5) % 2)
	if room_id == "U01": _arrival_action_visuals()
