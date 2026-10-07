class_name NativeEnvironmentDetail
extends Node2D
static var metadata: Dictionary={}
static var textures: Dictionary={}
static func texture(index: int) -> Texture2D:
	if textures.has(index):return textures[index]
	if metadata.is_empty():metadata=JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/environment-detail-atlas.json"))
	var r: Array=metadata.cells[index];var atlas:=AtlasTexture.new();atlas.atlas=load("res://assets/art/environment-detail-v1.png");atlas.region=Rect2(r[0],r[1],r[2],r[3]);atlas.filter_clip=true;textures[index]=atlas;return atlas
var room: String=""
var layout: Dictionary={}
var dawn: bool=false
func configure(id: String,data: Dictionary,flags: Dictionary) -> void:
	room=id;layout=data;dawn=flags.get("dawn_started",false);queue_redraw()
func _draw() -> void:
	if layout.is_empty():return
	var bounds: Array=layout.walk_bounds
	var width: int=int(layout.dimensions[0]);var height: int=int(layout.dimensions[1])
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	var outdoor: bool=room in ["U01","U02","U08","F01","F03","F04","N01","N05","E01","O01","M01","M07"]
	# Canvas-items rendering draws these half-pixel marks at the 1280x720 window's
	# native density. Character pixels stay nearest-filtered at their existing size.
	for y: int in range(int(bounds[1])+5,height-24,19):
		for x: int in range(27,width-24,31):
			var seed: int=(x*13+y*7)%19
			if outdoor:
				draw_rect(Rect2(x+seed,y,3,0.5),Color(0.50,0.60,0.48,0.18))
				if seed<7:draw_rect(Rect2(x+seed+1,y-2,0.5,2.5),Color(0.57,0.66,0.51,0.25))
			else:
				draw_rect(Rect2(x,y,17,0.5),Color(0.75,0.64,0.60,0.16));draw_rect(Rect2(x+17,y,0.5,8),Color(0.13,0.16,0.24,0.14))
	if room in ["O01","M01","N01"]:
		var facade: Rect2=Rect2(235,48,430,116) if room=="O01" else Rect2(295,55,410,104) if room=="M01" else Rect2(280,48,470,110)
		for y: int in range(int(facade.position.y)+4,int(facade.end.y)-2,7):
			for x: int in range(int(facade.position.x)+2,int(facade.end.x)-14,18):
				if (x+y)%3==0:draw_rect(Rect2(x+(8 if y%2==0 else 0),y,11,0.5),Color(0.84,0.67,0.54,0.19))

	var surface: int=8 if outdoor else 11 if room in ["U04","N03","N07","M03","M05"] else 10 if room.begins_with("M") else 9
	var floor_rect:=Rect2(20,float(bounds[1]),width-40,height-float(bounds[1])-24)
	for y: int in range(int(floor_rect.position.y),int(floor_rect.end.y),64):
		for x: int in range(20,width-20,64):
			draw_texture_rect(texture(surface),Rect2(x,y,64,64).intersection(floor_rect),false,Color(0.77,0.82,0.86,0.38 if outdoor else 0.27))
	if room=="N01":draw_texture_rect(texture(1),Rect2(280,20,470,152),false)
	elif room=="O01":draw_texture_rect(texture(3),Rect2(235,12,430,164),false)
	elif room=="E01":draw_texture_rect(texture(2),Rect2(240,26,480,158),false)
	elif room=="M01":draw_texture_rect(texture(4),Rect2(335,18,350,187),false)
	elif room in ["U01","U02"]:draw_texture_rect(texture(0),Rect2(225,26,265,125),false,Color(0.83,0.81,0.88,1))
	if outdoor:
		draw_texture_rect(texture(5 if room in ["U02","N05","O01","M01","M07"] else 6),Rect2(0,14,132,143),false,Color(0.75,0.78,0.82,1))
		draw_texture_rect(texture(7),Rect2(width-128,93,120,57),false,Color(0.80,0.82,0.84,1))

	# Soft, stepped pools around architectural light sources, below solid props.
	for source: Array in layout.lights:
		var at:=Vector2(source[0],source[1])
		for band: int in range(4):draw_rect(Rect2(at+Vector2(-16-band*7,2+band*2),Vector2(32+band*14,5)),Color(1.0,0.73,0.43,0.016 if dawn else 0.028))
