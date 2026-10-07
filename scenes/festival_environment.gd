class_name NativeFestivalEnvironment
extends RefCounted
static func draw(node: Node2D, room: String, layout: Dictionary, flags: Dictionary, elapsed: float) -> void:
	var size:=Vector2(layout.dimensions[0],layout.dimensions[1])
	node.draw_rect(Rect2(Vector2.ZERO,size),Color("161e2b"))
	node.draw_rect(Rect2(20,142,size.x-40,size.y-166),Color("34483e") if room in ["F01","F03","F04"] else Color("514c61"))
	for y: int in range(146,int(size.y)-24,16):
		for x: int in range(24,int(size.x)-24,32):
			node.draw_rect(Rect2(x,y,25,1),Color("43544b") if room in ["F01","F03","F04"] else Color("60576a"))
			if (x+y)%64==0: node.draw_rect(Rect2(x+5,y+4,4,2),Color("8a7760"))
	for index: int in range(14):
		var x: float=20+index*(size.x-40)/13.0
		node.draw_rect(Rect2(x,48+(index%3)*8,20,60),Color("213b3d"))
		node.draw_rect(Rect2(x+7,81,4,55),Color("584555"))
		node.draw_rect(Rect2(x-3,52+(index%3)*8,30,18),Color("344d42"))
	node.draw_line(Vector2(25,114),Vector2(size.x-25,127),Color("9f7761"),1)
	for x: int in range(30,int(size.x)-25,35):
		node.draw_rect(Rect2(x,117,3,5),Color("e8b45c"))
	if room=="F02":
		node.draw_colored_polygon(PackedVector2Array([Vector2(155,176),Vector2(400,65),Vector2(640,176)]),Color("9e4e52"))
		node.draw_rect(Rect2(162,176,477,32),Color("804355"))
		if flags.get("volunteers_released",false):
			node.draw_string(preload("res://assets/art/afterhours-font.fnt"),Vector2(305,204),"SHIFT FINISHED",HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("e6d6b1"))
	elif room in ["F04","F06"]:
		var width: float=360 if room=="F06" else 430
		var left: float=size.x/2-width/2
		node.draw_rect(Rect2(left,66,width,74),Color("292638"))
		for x: int in range(int(left),int(left+width),24):
			node.draw_rect(Rect2(x,68,12,70),Color("6e3b50"))
		node.draw_string(preload("res://assets/art/afterhours-font.fnt"),Vector2(left+30,112),"LAST LIGHT / ONE FINAL SET",HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("e8b45c"))
		if not flags.has("encore_resolution") and room=="F06":
			var sway: float=0 if flags.get("reduced_motion",false) else sin(elapsed)*7
			node.draw_line(Vector2(left+30,138),Vector2(size.x/2+sway,312),Color(0.8,0.6,0.3,0.2),3)
	elif room=="F05":
		node.draw_rect(Rect2(32,60,size.x-64,76),Color("4d3647"))
		for x: int in range(40,int(size.x)-40,16): node.draw_rect(Rect2(x,64,7,66),Color("673e50"))
	node.draw_string(preload("res://assets/art/afterhours-font.fnt"),Vector2(25,138),str(layout.name),HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("b9d5bc"))
