class_name NativeCampusEnvironment
extends RefCounted
const FONT=preload("res://assets/art/afterhours-font.fnt")
static func draw(n: Node2D, room: String, layout: Dictionary, flags: Dictionary, elapsed: float) -> void:
	var size:=Vector2(layout.dimensions[0],layout.dimensions[1])
	var outside: bool=room in ["N01","N05","E01","O01"]
	var engineering: bool=room.begins_with("E")
	n.draw_rect(Rect2(Vector2.ZERO,size),Color("121b2b"))
	n.draw_rect(Rect2(20,142,size.x-40,size.y-166),Color("314239") if outside else Color("48525b") if engineering else Color("48414d"))
	for y: int in range(146,int(size.y)-24,20):
		for x: int in range(24,int(size.x)-24,40):
			n.draw_rect(Rect2(x,y,32,1),Color("42544a") if outside else Color("58616a") if engineering else Color("5c505e"))
			if (x+y)%80==0:n.draw_rect(Rect2(x+4,y+4,3,1),Color("837565"))
	if room=="O01":
		n.draw_rect(Rect2(235,44,430,121),Color("864e4f"))
		n.draw_colored_polygon(PackedVector2Array([Vector2(218,48),Vector2(280,17),Vector2(620,17),Vector2(685,48)]),Color("343443"))
		for x: int in range(253,653,48):
			n.draw_rect(Rect2(x,67,26,56),Color("1e293c"));n.draw_rect(Rect2(x+4,71,18,35),Color("b48761"));n.draw_rect(Rect2(x+12,71,2,35),Color("634752"))
		n.draw_rect(Rect2(414,83,73,85),Color("5c4350"));n.draw_rect(Rect2(436,26,28,37),Color("864e4f"))
		n.draw_rect(Rect2(432,22,36,5),Color("383344"))
	elif room=="N01":
		# Norlin's west terrace, compressed into a fictional navigable quad.
		n.draw_rect(Rect2(280,27,470,135),Color("966d64"))
		n.draw_rect(Rect2(260,38,510,10),Color("b6977d"))
		for x: int in range(302,735,62):
			n.draw_rect(Rect2(x,62,35,82),Color("1e2b3e"))
			n.draw_rect(Rect2(x+5,67,25,48),Color("d5a268"))
			n.draw_rect(Rect2(x+17,67,2,48),Color("5d4a57"))
			n.draw_rect(Rect2(x-8,52,10,108),Color("b6977d"))
			n.draw_rect(Rect2(x-10,50,14,5),Color("d3b494"))
		n.draw_rect(Rect2(462,65,96,106),Color("233446"))
		n.draw_rect(Rect2(474,70,72,98),Color("b78156"))
	elif room=="N05":
		for x: int in range(24,int(size.x)-24,24):
			n.draw_rect(Rect2(x,60,18,63),Color("3c5146"))
			n.draw_rect(Rect2(x+6,87,4,58),Color("6b514d"))
		for i: int in range(5):
			var bx: int=578+i*19+int(sin(elapsed+i)*4)
			n.draw_rect(Rect2(bx,208+(i%2)*6,8,5),Color("b2a88b"))
			n.draw_rect(Rect2(bx+7,208+(i%2)*6,3,2),Color("e8b45c"))
			n.draw_rect(Rect2(bx-3,210+(i%2)*6,4,2),Color("202936"))
	elif engineering:
		n.draw_rect(Rect2(30,28,size.x-60,112),Color("4b4655"))
		for x: int in range(40,int(size.x)-40,48):
			n.draw_rect(Rect2(x,50,30,59),Color("263f48"))
			n.draw_rect(Rect2(x+4,54,22,14),Color("88977a"))
			n.draw_rect(Rect2(x,118,32,5),Color("9c8064"))
		if room=="E03":
			n.draw_rect(Rect2(585,104,304,90),Color("28454b"))
			n.draw_line(Vector2(592,174),Vector2(884,174),Color("91a495"),3)
			for x: int in [612,752,878]:n.draw_rect(Rect2(x,128,6,97),Color("9c8064"))
		elif room=="E05":
			n.draw_rect(Rect2(370,47,172,66),Color("233446"))
			for x: int in range(382,530,18):n.draw_rect(Rect2(x,61,8,4),Color("8aa58c"))
			if flags.get("source_reel",false):n.draw_string(FONT,Vector2(378,96),"SOURCE RECOVERED",HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("e8b45c"))
	else:
		n.draw_rect(Rect2(25,25,size.x-50,114),Color("674d59"))
		for x: int in range(40,int(size.x)-40,76):
			n.draw_rect(Rect2(x,47,54,70),Color("263044"))
			n.draw_rect(Rect2(x+4,50,46,38),Color("a07863"))
			n.draw_rect(Rect2(x+26,50,2,38),Color("453c51"))
		if room=="N04":
			n.draw_rect(Rect2(28,124,size.x-56,9),Color("a07863"))
			n.draw_string(FONT,Vector2(315,121),"MARKED PASSAGE / "+("OPEN" if flags.get("stacks_shifted",false) else "TURN CRANK"),HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("e8b45c"))
		elif room=="N07":
			n.draw_rect(Rect2(300,50,196,50),Color("1d273c"))
			for i: int in range(23):n.draw_rect(Rect2(310+i*8,75-absf(sin(i*1.7+elapsed))*14,3,2+absf(sin(i*1.7+elapsed))*28),Color("8ca992"))
		elif room=="N06":
			n.draw_string(FONT,Vector2(280,106),"POSSIBLE LIVES / CLOSED ARCHIVE",HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("d2b191"))
	n.draw_string(FONT,Vector2(25,138),str(layout.name),HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("b9d5bc"))
