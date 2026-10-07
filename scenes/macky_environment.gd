class_name NativeMackyEnvironment
extends RefCounted
const FONT=preload("res://assets/art/afterhours-font.fnt")
static func draw(n: Node2D,room: String,layout: Dictionary,flags: Dictionary,t: float) -> void:
	var size:=Vector2(layout.dimensions[0],layout.dimensions[1])
	var dawn: bool=flags.get("dawn_started",false) or room=="M07"
	var outdoor: bool=room in ["M01","M07"]
	n.draw_rect(Rect2(Vector2.ZERO,size),Color("39364b") if dawn else Color("141d31"))
	if outdoor:
		for y: int in range(0,144,8):n.draw_rect(Rect2(0,y,size.x,8),Color("cc967d").lerp(Color("655675"),y/144.0) if dawn else Color("554763").lerp(Color("202a43"),y/144.0))
		for peak: Vector2 in [Vector2(70,55),Vector2(175,31),Vector2(270,46)]:
			n.draw_colored_polygon(PackedVector2Array([peak,peak+Vector2(-65,83),peak+Vector2(34,83)]),Color("383b50"));n.draw_line(peak+Vector2(-3,9),peak+Vector2(-48,76),Color("746879"),2)
		n.draw_rect(Rect2(20,142,size.x-40,size.y-166),Color("50624e") if dawn else Color("30443c"))
		for y: int in range(154,int(size.y)-24,22):
			for x: int in range(26,int(size.x)-26,34):n.draw_rect(Rect2(x,y,22,1),Color("68735b") if dawn else Color("40564a"))
		if room=="M01":
			# The same integer-grid brick/window style as the earlier campus rooms.
			n.draw_rect(Rect2(335,44,350,125),Color("864e4f"))
			n.draw_colored_polygon(PackedVector2Array([Vector2(324,46),Vector2(365,22),Vector2(655,22),Vector2(696,46)]),Color("343443"))
			for x: int in range(350,671,44):
				n.draw_rect(Rect2(x,63,23,46),Color("1e293c"));n.draw_rect(Rect2(x+4,67,15,31),Color("b48761"));n.draw_rect(Rect2(x+10,67,2,31),Color("634752"))
			n.draw_rect(Rect2(335,117,350,5),Color("b6977d"))
			n.draw_rect(Rect2(476,102,68,70),Color("233446"));n.draw_rect(Rect2(482,108,56,62),Color("b78156"));n.draw_rect(Rect2(509,108,2,62),Color("634752"))
			for x: int in [463,548]:n.draw_rect(Rect2(x,90,9,83),Color("b6977d"))
		for x: int in [52,int(size.x)-66]:
			var sway: int=roundi(sin(t*1.2+x)*2)
			n.draw_rect(Rect2(x+11,76,8,81),Color("695653"))
			for i: int in range(5):n.draw_rect(Rect2(x+sway+(i%2)*12,46+i*14,38,24),Color("486050") if dawn else Color("2c493d"))
		for i: int in range(5):
			var x: int=700+i*17+roundi(sin(t+i)*4);var y: int=279+(i%2)*7
			n.draw_rect(Rect2(x,y,7,4),Color("b6b292"));n.draw_line(Vector2(x-3,y+2),Vector2(x+2,y+1),Color("283441"),1)
	else:
		n.draw_rect(Rect2(20,142,size.x-40,size.y-166),Color("4b3f52"))
		for y: int in range(147,int(size.y)-24,18):
			n.draw_line(Vector2(22,y),Vector2(size.x-22,y),Color("635062"),1)
			for x: int in range(30,int(size.x)-30,56):n.draw_rect(Rect2(x,y+3,2,5),Color("716071"))
		n.draw_rect(Rect2(20,22,size.x-40,120),Color("775658"))
		for x: int in range(34,int(size.x)-34,46):n.draw_rect(Rect2(x,25,12,112),Color("956c61"));n.draw_rect(Rect2(x+12,25,3,112),Color("483647"))
		n.draw_rect(Rect2(22,123,size.x-44,9),Color("aa896d"))
		match room:
			"M02":
				for x: int in [65,615]:n.draw_rect(Rect2(x,52,122,62),Color("333445"));n.draw_rect(Rect2(x+6,58,110,35),Color("b69771"))
			"M03":
				for x: int in range(180,680,62):n.draw_rect(Rect2(x,78,26,41),Color("494157"));n.draw_line(Vector2(x+12,67),Vector2(x+12,119),Color("b6a182"),1)
			"M04":
				n.draw_rect(Rect2(255,43,452,73),Color("272b3e"))
				for i: int in range(26):n.draw_rect(Rect2(267+i*16,100-absf(sin(i+t))*24,4,4+absf(sin(i+t))*24),Color("ba9676"))
			"M05":
				n.draw_rect(Rect2(200,39,560,82),Color("252b41"))
				for x: int in range(211,751,28):n.draw_rect(Rect2(x,44,16,8),Color("6a566a"));n.draw_line(Vector2(x+3,52),Vector2(x+3,59),Color("b39179"),1)
			"M06":
				n.draw_rect(Rect2(140,36,680,74),Color("2a293e"))
				for x: int in [150,740]:
					for y: int in range(43,109,11):n.draw_rect(Rect2(x,y,67,10),Color("805568").lerp(Color("382b44"),(y-43)/66.0))
				n.draw_rect(Rect2(460,42,50,56),Color("b1966b"));n.draw_rect(Rect2(477,42,17,56),Color("45374f"))
				if dawn:n.draw_string(FONT,Vector2(325,94),"ONE GATHERING / ENDED",HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("c0d5ba"))
	n.draw_string(FONT,Vector2(25,138),str(layout.name),HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("c0d5ba"))
