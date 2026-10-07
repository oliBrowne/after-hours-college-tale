class_name NativeCampusMap
extends Control
var game: Node
var room_view: ScrollContainer
var room_list: Control
var rooms_mode: bool = false
var room_buttons: Array[Button] = []
var room_selection: int = 0
var details: Label
var district_buttons: Array[Button] = []
var image: TextureRect
var scroll: ScrollContainer
var selected: int = 0
var zoom: float = 0.5
const DISTRICTS: Array[String] = ["UMC / Broadway", "Farrand / Last Light", "Norlin", "Engineering", "Old Main", "Macky"]
const ROOM_IDS: Array = [["U01","U08","U02","U03","U04","U05","U06","U07"],["F01","F02","F03","F04","F05","F06"],["N01","N02","N03","N04","N05","N06","N07"],["E01","E02","E03","E04","E05"],["O01","O02","O03","O04"],["M01","M02","M03","M04","M05","M06","M07"]]
func configure(controller: Node) -> void:
	game=controller
	position=Vector2(8,8);size=Vector2(624,344);z_index=510
	var background := Panel.new()
	background.size=size
	background.add_theme_stylebox_override("panel",game.style_panel())
	add_child(background)
	var heading := Label.new()
	heading.text="BOULDER / LAST LIGHT"
	heading.position=Vector2(12,8)
	heading.add_theme_font_override("font",game.font);heading.add_theme_font_size_override("font_size",12)
	add_child(heading)
	scroll=ScrollContainer.new();scroll.position=Vector2(12,36);scroll.size=Vector2(380,252)
	add_child(scroll)
	image=TextureRect.new();image.texture=load("res://assets/art/campus-map-v1.png")
	image.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	image.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	image.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	scroll.add_child(image)
	var district_layer := Control.new()
	image.add_child(district_layer)
	var marks: Array[Vector2]=[Vector2(0.38,0.7),Vector2(0.62,0.74),Vector2(0.45,0.43),Vector2(0.8,0.49),Vector2(0.28,0.36),Vector2(0.17,0.52)]
	for i: int in range(DISTRICTS.size()):
		var button: Button=make_button(DISTRICTS[i],Vector2(404,36+i*26),Vector2(208,23),func() -> void: select_district(i))
		district_buttons.append(button)
		var pin: Button=make_button(str(i+1),marks[i]*Vector2(760,450),Vector2(26,24),func() -> void: select_district(i),district_layer)
		pin.set_meta("map_anchor",marks[i]);pin.tooltip_text=DISTRICTS[i]
	room_view=ScrollContainer.new();room_view.position=scroll.position;room_view.size=scroll.size
	add_child(room_view);room_view.hide()
	room_list=Control.new();room_list.custom_minimum_size=Vector2(360,240);room_view.add_child(room_list)
	details=Label.new();details.position=Vector2(404,198);details.size=Vector2(208,125)
	details.add_theme_font_override("font",game.font);details.add_theme_font_size_override("font_size",12)
	details.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	add_child(details)
	make_button("-",Vector2(12,300),Vector2(30,27),func() -> void: zoom=maxf(0.5,zoom-0.25);resize_map())
	make_button("+",Vector2(48,300),Vector2(30,27),func() -> void: zoom=minf(1.75,zoom+0.25);resize_map())
	make_button("Rooms",Vector2(88,300),Vector2(108,27),func() -> void: rooms_mode=not rooms_mode;show_rooms())
	make_button("Close map",Vector2(206,300),Vector2(150,27),game.close_map)
	var note := Label.new();note.text="Scroll to pan / Rooms shows local doors"
	note.position=Vector2(12,276);note.add_theme_font_override("font",game.font);note.add_theme_font_size_override("font_size",12)
	add_child(note)
	resize_map()
func make_button(value: String, at: Vector2, span: Vector2, callback: Callable, parent: Node=self) -> Button:
	var button := Button.new();button.text=value;button.position=at;button.size=span
	button.add_theme_font_override("font",game.font);button.add_theme_font_size_override("font_size",12)
	button.add_theme_stylebox_override("normal",game.style_panel())
	var hover: StyleBoxFlat=game.style_panel();hover.bg_color=Color("51425a")
	button.add_theme_stylebox_override("hover",hover);button.add_theme_stylebox_override("focus",hover)
	button.mouse_default_cursor_shape=Control.CURSOR_POINTING_HAND
	button.pressed.connect(callback);parent.add_child(button)
	return button
func resize_map() -> void:
	image.custom_minimum_size=Vector2(760,450)*zoom
	image.size=image.custom_minimum_size
	for pin: Node in image.get_child(0).get_children(): pin.position=pin.get_meta("map_anchor")*image.size
func refresh() -> void:
	var index: int=["U","F","N","E","O","M"].find(str(game.state.room).substr(0,1))
	select_district(maxi(0,index));district_buttons[maxi(0,index)].grab_focus()
func select_district(index: int) -> void:
	selected=index
	if index>=5:
		details.text=wrap_text(DISTRICTS[index]+"\nPlanned district.\nNot playable in 0.6.0.\nMacky is next.")
		show_rooms()
		return
	var visited: int=0
	for room_id: String in ROOM_IDS[index]:
		if game.state.flags.get("visited_"+room_id,false): visited+=1
	var access: String="Open" if index==5 and game.state.flags.get("chapter3_complete",false) and game.state.flags.get("rook_confessed",false) else "Finish Todd and hear Rook" if index==5 else "Open" if index==4 and game.state.flags.get("chapter2_complete",false) else "Finish Norlin playback" if index==4 else "Open" if index==0 or index==1 and game.state.flags.has("claim_resolution") and game.state.flags.get("walt_joined",false) or index>=2 and game.state.flags.get("chapter1_complete",false) else "Finish ENCORE" if index>=2 else "Locked until Advisor Bev + Walt"
	details.text=wrap_text("Rooms seen %d/%d\n%s\nNext: %s" % [visited,ROOM_IDS[index].size(),access,game.objective()])
	show_rooms()
func _exit_tree() -> void: game=null

func key(event: InputEvent) -> void:
	if event.is_action_pressed("confirm"):
		var focused: Control=get_viewport().gui_get_focus_owner()
		if focused is Button: focused.pressed.emit()
		else: select_district(selected)
	elif rooms_mode and not room_buttons.is_empty() and (event.is_action_pressed("move_down") or event.is_action_pressed("move_up")):
		room_selection=posmod(room_selection+(1 if event.is_action_pressed("move_down") else -1),room_buttons.size())
		room_buttons[room_selection].grab_focus()
	elif event.is_action_pressed("move_down") or event.is_action_pressed("move_right"):
		select_district((selected+1)%DISTRICTS.size());district_buttons[selected].grab_focus()
	elif event.is_action_pressed("move_up") or event.is_action_pressed("move_left"):
		select_district(posmod(selected-1,DISTRICTS.size()));district_buttons[selected].grab_focus()
	else: return
	get_viewport().set_input_as_handled()

func wrap_text(value: String) -> String:
	var lines: Array[String]=[]
	for paragraph: String in value.split("\n"):
		var line: String=""
		for word: String in paragraph.split(" "):
			if line.length()+word.length()+1>25 and not line.is_empty(): lines.append(line);line=""
			line+=(" " if not line.is_empty() else "")+word
		lines.append(line)
	return "\n".join(lines.slice(0,8))
func show_rooms() -> void:
	scroll.visible=not rooms_mode;room_view.visible=rooms_mode
	for child: Node in room_list.get_children(): child.queue_free()
	room_buttons.clear();room_selection=0
	if not rooms_mode:return
	for i: int in range(ROOM_IDS[selected].size()):
		var room_id: String=ROOM_IDS[selected][i]
		var room_name: String=str(game.rooms[room_id].name).split(" /")[0]
		var status: String="* " if game.state.room==room_id else "+ " if game.state.flags.get("visited_"+room_id,false) else "? "
		room_buttons.append(make_button(status+room_name,Vector2(0,i*30),Vector2(360,28),func() -> void: room_details(room_id),room_list))
	room_list.custom_minimum_size=Vector2(360,maxi(240,ROOM_IDS[selected].size()*30))
func room_details(room_id: String) -> void:
	var room: Dictionary=game.rooms[room_id]
	var lines: Array[String]=[str(room.name),"Current room" if game.state.room==room_id else "Explored" if game.state.flags.get("visited_"+room_id,false) else "Unexplored","Doors:"]
	for object: Dictionary in room.objects:
		if object.kind!="door":continue
		var unlocked: bool=true
		for flag: String in object.get("requires",[]):
			if not game.state.flags.get(flag,false):unlocked=false
		lines.append(("Open: " if unlocked else "Locked: ")+str(game.rooms[object.to].name).split(" /")[0])
	details.text=wrap_text("\n".join(lines))
