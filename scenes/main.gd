extends Node2D

enum Mode { TITLE, WORLD, DIALOGUE, MENU, BATTLE, TIMING, TELEGRAPH, DODGE, RESULT, PAUSE, RESOLVE, GALLERY, INTRO, MAP, BANNER }
const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const PLUM: Color = Color("292638")
const LINE: Color = Color("3d3552")
const TRACK: Color = Color("1d1a2a")
const MUTED: Color = Color("8a8296")
## The bitmap glyphs are 5px wide in 8px cells; a 6px advance reads as words, not spaced-out letters.
const GLYPH: float = 6.0
## Ticks each page of an over-long label stays up before the next page shows.
const LABEL_PAGE_TICKS: int = 150
## What each queued action does, shown under the action log while a turn resolves.
const ACTION_HELP: Dictionary = {"strike": "A timed hit. Accuracy changes damage.", "connect": "Listening. OPEN rises as they open up.", "promise": "A promise: the next defense has a real objective.", "boundary": "A boundary: one smaller, honest task.", "guard": "Guarding: less damage, +12 SYNC.", "shield": "Hold the Light cancels one hit.", "heal": "Healing also revives a fallen ally.", "item": "A supply, used on resolution.", "warmth": "Share the Warmth: heal and guard.", "slow": "Half Time slows the next pattern.", "lantern": "Lantern Ward opens a shelter pocket.", "windbreak": "Windbreak shields one ally.", "brace": "Bracing for the next defense.", "release": "RELEASE: enough for tonight."}
const ACTORS: Array[String] = ["jules", "imani", "walt"]
const INTRO_CARDS: Array = [["BOULDER / LAST LIGHT", "The Flatirons keep the sunset a little longer than the streets."], ["JULES NAVARRO", "One borrowed mixer. One promise to return it. One last bus home."], ["9:12 PM / THE UMC", "The campus bus pulls away. Jules shifts the mixer and looks toward the UMC."]]
var mode: Mode = Mode.TITLE
var state: Dictionary = NativeState.fresh()
var rooms: Dictionary
var tile_data: Dictionary
var world: Node2D
var tilemap: TileMapLayer
var player: WorldActor
var followers: Array[WorldActor] = []
var trail: Array[Vector2] = []
var world_npcs: Array[AnimatedSprite2D] = []
var obstacles: Array[StaticBody2D] = []
var areas: Array[Area2D] = []
var ui: Control
var font: Font
var audio: NativeAudioDirector
var saves: NativeSaveService = NativeSaveService.new()
var overlay: NativeControlOverlay
var pointer_duck: bool = false
var pointer_hop: int = 0
var pointer_mode: bool = false
var hover_index: int = -1
var battle_help: Label
var last_promise_result: String = ""
var buttons: Array[Button] = []
var menu_options: Array = []
var selection: int = 0
var caption: String = ""
var text_nodes: Array[Control] = []
var notice: String = ""
var notice_ticks: int = 0
var input_lock: int = 0
var dialogue_lines: Array = []
var line_index: int = 0
var reveal: float = 0.0
var dialogue_callback: Callable
var dialogue_choices: Array = []
var pause_mode: Mode = Mode.WORLD
var pause_options: Array = []
var pause_caption: String = ""
var pause_selection: int = 0
var settings_return_title: bool = false
var binding_capture: String = ""
var navigation := NativeRoomNavigation.new()
var pointer_path: PackedVector2Array = PackedVector2Array()
var pointer_stall: int = 0
var pause_context: bool = false
var paused_cast_sprites: Array[AnimatedSprite2D] = []
var jakerson_ui: bool = false
var pointer_goal: Vector2 = Vector2.INF
var pointer_object: Dictionary = {}
var dodge_goal: Vector2 = Vector2.INF
var battle: Dictionary = {}
var checkpoint: Dictionary = {}
var plan: Array = []
var actor: int = 0
var target: int = 0
var pattern: Dictionary = {}
var battle_sprites: Array[AnimatedSprite2D] = []
var foe: AnimatedSprite2D
var dodge_view: DodgeBoxView
var phase_ticks: int = 0
var timing_ticks: int = 0
var timing_index: int = 0
var pending_battle: Dictionary = {}
var resolution_ticks: int = 0
var retreating: bool = false
var grace_ticks: int = 0
var hint: String = ""
var battle_error: String = ""
var resume_ticks: int = 0
var ui_dirty: bool = true
var qa: bool = false
var lighting: Node2D
var boss_id: String = ""
var boss_clock: Dictionary = {}
var boss_stage: int = 0
var boss_rounds: int = 0
var beat_defend: bool = false
var feedback: Array[Dictionary] = []
var hit_flash: int = 0
var qa_failed: bool = false
var environment: UMCEnvironment
## The room a fight started in, redrawn without its people behind the battle.
var battle_scenery: Node2D
var backdrop: BoulderTitleBackdrop
var camera: Camera2D
var vfx: CombatVFX
var claim_art: ClaimActor
var pin_art: Node2D
var scene_props: Array[Node2D] = []
var intro_index: int = 0
var intro_ticks: int = 0
## The cards being shown and which one brings the world up: move-in day (none), or the evening.
var intro_cards: Array = INTRO_CARDS
var intro_arrival: int = 2
var transition_ticks: int = 0
var footsteps: float = 0.0
var resolution_index: int = 0
var shown_enemy_hp: int = 0
var boundary_active: bool = false
var action_text: String = ""
var phrase_pause: int = 0
var qa_folder: String = ""
var strange_ticks: int = 0
var peak_music: bool = false
var claim_needs: Dictionary = ClaimNeeds.create()
var pip: Node2D
var bar_marker: Dictionary = {}
var preferences_path: String = "user://preferences.json"
var campus_map: NativeCampusMap
var map_from_pause: bool = false
var qa_record: AudioEffectRecord
var qa_record_finishing: bool = false
var qa_music_events: Array[Dictionary] = []
var graze_sync: int = 0
var arrival_point: Vector2 = Vector2.INF
var growth_note: String = ""
## Dialogue box (and the choice box after it) sits at the top while the people talking stand where
## the bottom box would cover them (Undertale/Deltarune style).
var dialogue_top: bool = false
## A label() whose text did not fit its box shows it a page at a time; this keeps the pages turning.
var paging_labels: bool = false
var wind_fx: NativeWindStreaks
## Screen rect the compact menu's Back button sits in (read by the control overlay).
var menu_back_rect: Rect2 = Rect2()
## Ending card / credits roll shown once after the epilogue, then its callback.
var ending_ticks: int = -1
var ending_done: Callable

func _ready() -> void:
	qa = ("--qa-opening" in OS.get_cmdline_user_args() or "--qa-smoke" in OS.get_cmdline_user_args()) and (OS.has_feature("debug") or not OS.get_environment("AFTER_HOURS_QA").is_empty())
	if qa:
		qa_folder = OS.get_environment("AFTER_HOURS_QA")
		if qa_folder.is_empty(): qa_folder = "user://qa"
		DirAccess.make_dir_recursive_absolute(qa_folder)
		saves = NativeSaveService.new(qa_folder.path_join("saves"))
		preferences_path = qa_folder.path_join("preferences.json")
	DisplayServer.window_set_title("After Hours / Full Evening / 0.7.2")
	get_window().title = "After Hours / Full Evening / 0.7.2"
	var tight: FontVariation = FontVariation.new()
	tight.base_font = load("res://assets/art/afterhours-font.fnt")
	tight.spacing_glyph = int(GLYPH) - 8
	font = tight
	rooms = JSON.parse_string(FileAccess.get_file_as_string("res://content/rooms.json"))
	var cameos: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/cameos.json"))
	for room_id: String in cameos:
		rooms[room_id].objects.append_array(cameos[room_id])
	for definition: Dictionary in rooms.values(): NativeRoomPlacement.prepare(definition)
	tile_data = JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/room-tilemaps.json"))
	_load_preferences()
	configure_input()
	audio = NativeAudioDirector.new()
	add_child(audio)
	audio.set_mix_gains(float(state.settings.music), float(state.settings.effects), float(state.settings.voices), float(state.settings.ambience))
	backdrop = BoulderTitleBackdrop.new()
	backdrop.z_index = -200
	add_child(backdrop)
	world = Node2D.new()
	world.y_sort_enabled = true
	add_child(world)
	var dusk: CanvasModulate = CanvasModulate.new()
	dusk.name="Dusk"
	dusk.color = Color(0.68, 0.72, 0.84, 1)
	world.add_child(dusk)
	lighting = Node2D.new()
	world.add_child(lighting)
	tilemap = TileMapLayer.new()
	tilemap.z_index = -100
	world.add_child(tilemap)
	environment = UMCEnvironment.new()
	environment.z_index = -90
	world.add_child(environment)
	battle_scenery = Node2D.new()
	battle_scenery.y_sort_enabled = true
	battle_scenery.z_index = -150
	battle_scenery.visible = false
	add_child(battle_scenery)
	environment.ambient_event.connect(func(cue: String) -> void: audio.combat(cue))
	player = WorldActor.new()
	world.add_child(player)
	player.configure("jules", true)
	pip = load("res://scenes/pip_actor.gd").new()
	world.add_child(pip)
	pip.visible = false
	for id: String in ["imani", "walt"]:
		var follower: WorldActor = WorldActor.new()
		world.add_child(follower)
		follower.configure(id, false)
		followers.append(follower)
	var marker: NativeGuideMarker = NativeGuideMarker.new()
	marker.game = self
	marker.z_index = 250
	add_child(marker)
	camera = Camera2D.new()
	camera.position = Vector2(320, 180)
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = 640
	camera.limit_bottom = 360
	add_child(camera)
	var canvas: CanvasLayer = CanvasLayer.new()
	add_child(canvas)
	ui = Control.new()
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(ui)
	overlay = NativeControlOverlay.new()
	ui.add_child(overlay)
	overlay.z_index = 500
	overlay.configure(self)
	campus_map = NativeCampusMap.new()
	ui.add_child(campus_map)
	campus_map.configure(self)
	campus_map.hide()
	vfx = CombatVFX.new()
	vfx.z_index = 300
	add_child(vfx)
	dodge_view = DodgeBoxView.new()
	add_child(dodge_view)
	claim_art = ClaimActor.new()
	claim_art.position = Vector2(480, 150)
	claim_art.z_index = 200
	add_child(claim_art)
	pin_art = load("res://scenes/pin_actor.gd").new()
	pin_art.position = Vector2(480, 150)
	pin_art.z_index = 200
	add_child(pin_art)
	_build_battle_sprites()
	enter_room("U01", Vector2(96, 258), false)
	show_title()
	qa = ("--qa-opening" in OS.get_cmdline_user_args() or "--qa-smoke" in OS.get_cmdline_user_args()) and (OS.has_feature("debug") or not OS.get_environment("AFTER_HOURS_QA").is_empty())
	if qa:
		call_deferred("_qa_smoke")

func configure_input() -> void:
	var keys: Dictionary = {"move_up": [KEY_UP, KEY_W], "move_down": [KEY_DOWN, KEY_S], "move_left": [KEY_LEFT, KEY_A], "move_right": [KEY_RIGHT, KEY_D], "confirm": [KEY_Z, KEY_ENTER], "cancel": [KEY_X, KEY_ESCAPE], "menu": [KEY_C, KEY_TAB], "run": [KEY_SHIFT]}
	var pad: Dictionary = {"confirm": JOY_BUTTON_A, "cancel": JOY_BUTTON_B, "menu": JOY_BUTTON_Y, "run": JOY_BUTTON_LEFT_SHOULDER, "move_up": JOY_BUTTON_DPAD_UP, "move_down": JOY_BUTTON_DPAD_DOWN, "move_left": JOY_BUTTON_DPAD_LEFT, "move_right": JOY_BUTTON_DPAD_RIGHT}
	for action: String in keys:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.25)
		Input.action_release(action)
		InputMap.action_erase_events(action)
		var key_list: Array = [state.settings.bindings[action]] if state.settings.bindings.has(action) else keys[action]
		for key: int in key_list:
			var claimed: bool = false
			for other: String in state.settings.bindings:
				if other != action and int(state.settings.bindings[other]) == key:
					claimed = true
			if not claimed:
				var event: InputEventKey = InputEventKey.new()
				event.physical_keycode = key
				InputMap.action_add_event(action, event)
		var button: InputEventJoypadButton = InputEventJoypadButton.new()
		button.button_index = int(pad[action])
		InputMap.action_add_event(action, button)
	for direction: String in ["move_left", "move_right", "move_up", "move_down"]:
		var motion: InputEventJoypadMotion = InputEventJoypadMotion.new()
		motion.axis = JOY_AXIS_LEFT_X if direction in ["move_left", "move_right"] else JOY_AXIS_LEFT_Y
		motion.axis_value = -1.0 if direction in ["move_left", "move_up"] else 1.0
		InputMap.action_add_event(direction, motion)

func _input(event: InputEvent) -> void:
	if mode == Mode.MAP:
		if event.is_action_pressed("cancel") or event.is_action_pressed("menu"):
			close_map(); get_viewport().set_input_as_handled()
		else: campus_map.key(event)
		return
	if event is InputEventMouseMotion:
		pointer_mode = true; hover_index = -1
		for button: Button in buttons:
			if is_instance_valid(button) and button.get_global_rect().has_point(event.position): hover_index = int(button.get_meta("option_index", -1))
		update_command_help()
	if (event is InputEventKey or event is InputEventAction or event is InputEventJoypadButton) and event.is_pressed():
		pointer_mode = false; hover_index = -1; update_command_help()
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if not event.pressed: pointer_duck = false
		if is_instance_valid(overlay) and overlay.owns(event.position): return
	if not binding_capture.is_empty() and (event.is_action_pressed("cancel") or event is InputEventKey and event.pressed and event.physical_keycode == KEY_ESCAPE):
		binding_capture = ""; remap_menu(); get_viewport().set_input_as_handled(); return
	if not binding_capture.is_empty() and event is InputEventKey and event.pressed and not event.echo:
		var code: int = event.physical_keycode
		if code in state.settings.bindings.values():
			caption = "Key already assigned / choose another or cancel"
			ui_dirty = true
			get_viewport().set_input_as_handled()
			return
		else:
			state.settings.bindings[binding_capture] = code
			configure_input()
			_save_preferences()
		binding_capture = ""
		remap_menu()
		get_viewport().set_input_as_handled()
		return
	if input_lock > 0 or (event is InputEventKey and event.echo):
		return
	if not pause_context and jakerson_ui and mode in [Mode.DIALOGUE,Mode.MENU] and event.is_action_pressed("cancel"):
		NativeJakerson.leave(self);get_viewport().set_input_as_handled();return
	if event.is_action_pressed("menu") and mode in [Mode.WORLD, Mode.DIALOGUE, Mode.BATTLE, Mode.TIMING, Mode.TELEGRAPH, Mode.DODGE, Mode.RESOLVE, Mode.INTRO]:
		open_pause()
		get_viewport().set_input_as_handled()
		return
	if mode in [Mode.TITLE, Mode.MENU, Mode.BATTLE, Mode.RESULT, Mode.PAUSE]:
		var command_grid: bool = mode == Mode.BATTLE and caption.contains("Choose an action") and menu_options.size() == 6
		if event is InputEventMouseButton and event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			selection = clampi(selection + (1 if event.button_index == MOUSE_BUTTON_WHEEL_DOWN else -1), 0, maxi(0, menu_options.size() - 1))
			ui_dirty = true
		elif command_grid and (event.is_action_pressed("move_down") or event.is_action_pressed("move_up")):
			# Two rows of three: up/down change row, wrapping into the next column so every command stays reachable.
			var order: Array[int] = [0, 3, 1, 4, 2, 5]
			selection = order[(order.find(selection) + (1 if event.is_action_pressed("move_down") else 5)) % 6]
			ui_dirty = true
		elif event.is_action_pressed("move_down") or event.is_action_pressed("move_right"):
			selection = (selection + 1) % maxi(1, menu_options.size())
			ui_dirty = true
		elif event.is_action_pressed("move_up") or event.is_action_pressed("move_left"):
			selection = (selection - 1 + menu_options.size()) % maxi(1, menu_options.size())
			ui_dirty = true
		elif event.is_action_pressed("confirm"):
			activate(selection)
		elif event.is_action_pressed("cancel"):
			cancel_menu()
		else:
			return
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("confirm"):
		if mode == Mode.DODGE:
			beat_defend = true
		if mode == Mode.INTRO:
			advance_intro()
		elif mode == Mode.WORLD:
			var selected: Dictionary = nearest_object()
			if not selected.is_empty():
				interact(selected)
		elif mode == Mode.DIALOGUE:
			advance_dialogue()
		elif mode == Mode.TIMING:
			finish_timing(false)
		elif mode == Mode.GALLERY:
			show_title()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("cancel") and mode == Mode.GALLERY:
		show_title()
	elif event.is_action_pressed("cancel") and mode == Mode.INTRO:
		finish_arrival(true)
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var point: Vector2 = get_global_transform_with_canvas().affine_inverse() * event.position
		if mode == Mode.WORLD:
			pointer_object = object_at(point)
			pointer_path = navigation.object_route(player.position, pointer_object) if not pointer_object.is_empty() else navigation.route(player.position, navigation.safe_point(point))
			pointer_stall = 0
			pointer_goal = pointer_path[0] if not pointer_path.is_empty() else Vector2.INF
			if pointer_path.is_empty():
				pointer_object = {}
				message("That spot has no clear approach. Try the aisle beside it.")
		elif mode == Mode.DODGE and Rect2(Vector2.ZERO, Vector2(256, 120)).has_point(dodge_view.to_arena(point)):
			dodge_goal = dodge_view.to_arena(point).clamp(Vector2(3, 3), Vector2(253, 117))
		elif mode == Mode.DIALOGUE:
			advance_dialogue()
		elif mode == Mode.TIMING:
			finish_timing(false)

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT: reset_pointer_controls()
	if pause_context: return
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and is_instance_valid(audio) and not qa and mode not in [Mode.TITLE, Mode.PAUSE]:
		open_pause()

func _physics_process(delta: float) -> void:
	if not pause_context and mode != Mode.PAUSE:
		environment.reduced_motion = bool(state.settings.reducedMotion)
		vfx.reduced_flashes = bool(state.settings.reducedMotion)
		claim_art.reduced_motion = bool(state.settings.reducedMotion)
		pin_art.reduced_motion = bool(state.settings.reducedMotion)
		pip.reduced_motion = bool(state.settings.reducedMotion)
		backdrop.step(delta, bool(state.settings.reducedMotion))
		environment.step(delta)
		if battle_scenery.visible:
			for scenery: Node in battle_scenery.get_children():
				if scenery is UMCEnvironment: scenery.reduced_motion = environment.reduced_motion; scenery.step(delta)
				elif scenery is NativeBattleBackdrop: scenery.reduced_motion = environment.reduced_motion; scenery.step(delta)
		vfx.step(delta)
		NativeBattleJuice.step(bool(state.settings.reducedMotion))
		claim_art.step(delta)
		pin_art.step(delta)
		for prop: Node2D in scene_props:
			prop.set("reduced_motion",bool(state.settings.reducedMotion));prop.call("step",delta)
		animate_idle_cast() if mode in [Mode.BATTLE,Mode.DODGE,Mode.TELEGRAPH] else null
		intro_ticks += 1
		transition_ticks = maxi(0, transition_ticks - 1)
		strange_ticks = maxi(0, strange_ticks - 1)
		pip.step(delta)
		if strange_ticks == 0:
			for light: Node in lighting.get_children(): light.energy = 0.55
		if mode == Mode.INTRO:
			ui_dirty = intro_ticks % 8 == 0
			if intro_index == intro_arrival:
				environment.set_arrival(minf(1.0, intro_ticks / 180.0))
				if intro_ticks >= 70: player.art.play("idle_up")
	if not pause_context and mode != Mode.PAUSE:
		hit_flash = maxi(0, hit_flash - 1)
		for popup: Dictionary in feedback:
			popup.ticks = int(popup.ticks) - 1
		feedback = feedback.filter(func(p: Dictionary) -> bool: return int(p.ticks) > 0)
	if is_instance_valid(audio) and not pause_context:
		audio.set_music_speed(float(state.settings.assist) * (0.8 if battle.get("slow", false) else 1.0) if mode in [Mode.DODGE, Mode.TELEGRAPH] else 1.0)
	input_lock = maxi(0, input_lock - 1)
	grace_ticks = maxi(0, grace_ticks - 1)
	if notice_ticks > 0:
		notice_ticks -= 1
		if notice_ticks == 0:
			ui_dirty = true
	if mode not in [Mode.TITLE, Mode.PAUSE, Mode.MENU]:
		state.playtime = float(state.playtime) + delta
	match mode:
		Mode.WORLD:
			world_tick(delta)
			animate_idle_cast()
		Mode.DIALOGUE:
			animate_idle_cast()
			var line: Array = dialogue_lines[line_index]
			var words: String = str(line[1])
			var old_count: int = floori(reveal)
			if phrase_pause > 0:
				phrase_pause -= 1
			else:
				var rate: float = 26.0 if str(line[0]) in ["Cal", "Mags", "Walt"] else 35.0
				reveal += 10000.0 if state.settings.instant else delta * rate
				if floori(reveal) > old_count and old_count < words.length():
					var character: String = words[old_count]
					if character in [".", "!", "?", ","] and not state.settings.instant:
						phrase_pause = 9 if character == "," else 16
					elif character != " " and state.settings.blips and not state.settings.instant:
						audio.voiced_blip(str(line[0]), str(line[2]) if line.size() > 2 else "neutral")
			# The speaker's mouth moves while the words appear and rests at pauses.
			NativeTalkMotion.update(self, floori(reveal) < words.length() and phrase_pause == 0, environment.elapsed)
			ui_dirty = true
		Mode.TIMING:
			timing_ticks += 1
			ui_dirty = true
			if timing_ticks > 60:
				finish_timing(true)
		Mode.RESOLVE:
			resolution_ticks += 1
			if resolution_ticks % 46 == 20:
				present_impact()
				if shown_enemy_hp == 0 and pending_battle.get("outcome", "active") != "active" or plan[resolution_index].kind == "release" and pending_battle.get("outcome", "active") != "active":
					complete_resolution()
					return
			if resolution_ticks >= 46:
				resolution_index += 1
				resolution_ticks = 0
				if resolution_index >= plan.size():
					complete_resolution()
				else:
					present_action()
		Mode.TELEGRAPH:
			phase_ticks = ceili(audio.bar_seconds_remaining(bar_marker) * 60) if audio.bar_is_valid(bar_marker) else phase_ticks - 1
			if audio.bar_ready(bar_marker) or not audio.bar_is_valid(bar_marker) and phase_ticks <= 0:
				if qa: print("QA_MUSIC bar=", bar_marker.get("beat", -1), " overshoot_ticks=", audio.bar_overshoot_ticks(bar_marker))
				if qa: qa_music_events.append({"encounter": "flyer" if boss_id.is_empty() else boss_id, "phase": boss_stage, "bar": bar_marker.get("beat", -1), "overshootTicks": audio.bar_overshoot_ticks(bar_marker), "observedBeat": audio.beat_position()})
				mode = Mode.DODGE
				foe.play("interact_down" if boss_id in ["chip", "deion", "todd"] else "reaction")
				claim_art.set_pose("active"); pin_art.set_pose("active")
				ui_dirty = true
		Mode.DODGE:
			dodge_tick()
	if paging_labels and intro_ticks % LABEL_PAGE_TICKS == 0: ui_dirty = true
	if ending_ticks >= 0 and not pause_context:
		ending_ticks += 1; ui_dirty = true
	if ui_dirty:
		render_ui()
		ui_dirty = false
	queue_redraw()

func world_tick(delta: float) -> void:
	# Jakerson's short drop-in scenes hold the player still while he jogs in and out.
	if NativeJakerson.cutscene_step(self): return
	# Walk-in scenes: the people in a room play out a moment the first time Jules arrives.
	if NativeRoomScenes.step(self): return
	var axis: Vector2 = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if axis.length_squared() > 0:
		pointer_goal = Vector2.INF; pointer_path.clear(); pointer_object = {}
	if pointer_goal != Vector2.INF:
		var change: Vector2 = pointer_goal - player.position
		if change.length() < 2:
			if not pointer_path.is_empty(): pointer_path.remove_at(0)
			pointer_goal = pointer_path[0] if not pointer_path.is_empty() else Vector2.INF
			if pointer_goal == Vector2.INF and not pointer_object.is_empty():
				var selected: Dictionary = pointer_object
				pointer_object = {}
				if player.position.distance_to(Vector2(selected.x, selected.y)) < 38: interact(selected)
				return
		else:
			axis = change.normalized() * minf(1.0, change.length() / (128.0 * delta if Input.is_action_pressed("run") else 80.0 * delta))
	var before: Vector2 = player.position
	player.walk(axis, Input.is_action_pressed("run"), delta)
	var moved: float = player.position.distance_to(before)
	state.x = player.position.x
	state.y = player.position.y
	NativeJakerson.world_step(self,moved)
	if NativeRandomFights.step(self, moved): return
	if pointer_goal != Vector2.INF:
		pointer_stall = pointer_stall + 1 if moved < 0.05 and axis.length_squared() > 0 else 0
		if pointer_stall > 60:
			pointer_goal = Vector2.INF; pointer_path.clear(); pointer_object = {}
			message("The path is blocked. Try the open aisle.")
	footsteps += moved
	if footsteps >= 29.0:
		footsteps = fmod(footsteps, 29.0)
		audio.combat("foot-stone" if state.room in ["U01", "U02", "U03", "U08"] else "foot-carpet" if state.room == "U04" else "foot")
	if trail.is_empty() or trail[0].distance_to(player.position) >= 3:
		trail.push_front(player.position)
		if trail.size() > 100: trail.pop_back()
	for i: int in range(followers.size()):
		followers[i].visible = state.flags.get(ACTORS[i + 1] + "_joined", false)
		if followers[i].visible:
			followers[i].follow(trail_point((i + 1) * 48.0))
	pip.visible = state.flags.get("pip_joined", false)
	if pip.visible: pip.position = trail_point(144.0)
	camera.position = camera.position.lerp(Vector2(clampf(player.position.x, camera.limit_left + 320, camera.limit_right - 320), clampf(player.position.y, camera.limit_top + 180, camera.limit_bottom - 180)), 0.15)
	if arrival_point != Vector2.INF and player.position.distance_to(arrival_point) >= 14: arrival_point = Vector2.INF
	if not growth_note.is_empty() and notice_ticks == 0:
		message(growth_note); growth_note = ""
	# Doors no longer open when you walk into them: stand at one and press confirm
	# (the prompt pill shows the key), or click it.
	ui_dirty = true

## The point a set distance back along the player's path. Followers ride this every tick, so they
## glide at the player's pace instead of hopping from one 3px trail point to the next.
func trail_point(distance: float) -> Vector2:
	var at: Vector2 = player.position
	for point: Vector2 in trail:
		var gap: float = at.distance_to(point)
		if gap >= distance: return at.move_toward(point, distance)
		distance -= gap
		at = point
	return at

func enter_room(id: String, point: Vector2, save_now: bool = true) -> void:
	jakerson_ui=false
	set_cast_paused(false)
	reset_pointer_controls()
	NativeCampusWorld.prepare(rooms[id],state.flags)
	navigation.configure(rooms[id])
	point = navigation.safe_point(point)
	arrival_point = point
	refresh_growth()
	pause_context = false
	state.room = id
	state.flags["visited_" + id] = true
	state.x = point.x
	state.y = point.y
	mode = Mode.WORLD
	world.visible = true
	backdrop.visible = false
	clear_battle_scenery()
	player.visible = true
	_set_battle_visible(false)
	pointer_goal = Vector2.INF; pointer_path.clear(); pointer_object = {}
	player.position = point
	player.facing = "up"
	pip.visible = state.flags.get("pip_joined", false)
	pip.position = point
	var bounds: Array = rooms[id].walk_bounds
	player.walk_bounds = Rect2(float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3]))
	trail.clear()
	for i: int in range(100):
		var candidate: Vector2 = point - Vector2(mini(i * 3, 72), 0)
		candidate = candidate.clamp(player.walk_bounds.position, player.walk_bounds.end)
		if not navigation.segment_clear(point, candidate): candidate = (point + Vector2(0, mini(i * 3, 72))).clamp(player.walk_bounds.position, player.walk_bounds.end)
		trail.append(candidate if navigation.segment_clear(point, candidate) else trail[-1] if not trail.is_empty() else point)
	for i: int in range(followers.size()):
		followers[i].position = trail_point((i + 1) * 48.0)
		followers[i].visible = state.flags.get(ACTORS[i + 1] + "_joined", false)
	for node: Node in obstacles + areas + world_npcs + scene_props:
		node.queue_free()
	obstacles.clear(); areas.clear(); world_npcs.clear(); scene_props.clear()
	for light: Node in lighting.get_children(): light.queue_free()
	tilemap.clear()
	tilemap.visible = false
	environment.reduced_motion = bool(state.settings.reducedMotion)
	world.get_node("Dusk").color=Color(0.90,0.88,0.87,1) if state.flags.get("dawn_started",false) else Color(0.68,0.72,0.84,1)
	environment.configure(id, rooms[id], state.flags)
	environment.glove_claimed = bool(state.flags.get("pip_joined", false))
	# The camera stays on the painted room: the dark margin outside the walkable floor (left, right
	# and below) is never shown, wherever that still leaves a full screen to look at.
	camera.limit_left = 0; camera.limit_top = 0
	camera.limit_right = int(rooms[id].dimensions[0])
	camera.limit_bottom = int(rooms[id].dimensions[1])
	var floor_area: Array = rooms[id].walk_bounds
	if float(floor_area[2]) + 8.0 >= 640.0 and camera.limit_right > 640: camera.limit_left = maxi(0, int(floor_area[0]) - 4); camera.limit_right = mini(camera.limit_right, int(floor_area[0]) + int(floor_area[2]) + 4)
	if float(floor_area[3]) + float(floor_area[1]) - 4.0 >= 360.0 and camera.limit_bottom > 360: camera.limit_bottom = mini(camera.limit_bottom, int(floor_area[1]) + int(floor_area[3]) + 4)
	camera.position = Vector2(clampf(point.x, camera.limit_left + 320, camera.limit_right - 320), clampf(point.y, camera.limit_top + 180, camera.limit_bottom - 180))
	for block: Dictionary in rooms[id].blocks:
		var body: StaticBody2D = StaticBody2D.new()
		body.position = Vector2(float(block.x) + float(block.w) / 2, float(block.y) + float(block.h) / 2)
		var collision: CollisionShape2D = CollisionShape2D.new()
		var shape: RectangleShape2D = RectangleShape2D.new()
		shape.size = Vector2(float(block.w), float(block.h))
		collision.shape = shape
		body.add_child(collision); world.add_child(body); obstacles.append(body)
	NativeJakersonArt.wear(str(state.flags.get("jakerson_outfit", "")))
	var room_objects: Array = rooms[id].objects.duplicate(true)
	if id == "U07" and state.flags.has("claim_resolution"):
		room_objects.append({"id":"mags_cleanup", "name":"Mags / intake desk", "x":725, "y":332, "kind":"talk", "sprite":"mags", "hit_rect":[-20,-48,40,54], "lines":[["Mags","One shelf at a time. Then I clock out.","warm"]]})
	room_objects = NativeJakerson.room_objects(self, id, point, room_objects)
	room_objects = NativeMoveIn.room_objects(self, id, room_objects)
	for keepsake_id: String in PartyGrowth.KEEPSAKES:
		var keepsake: Dictionary = PartyGrowth.KEEPSAKES[keepsake_id]
		var holder: String = str(keepsake.member)
		if bool(keepsake.get("shop", false)) or keepsake.room != id or PartyGrowth.found(state.flags, keepsake_id) or (holder != "jules" and not state.flags.get(holder + "_joined", false)): continue
		room_objects.append({"id":"keepsake_" + keepsake_id, "keepsake":keepsake_id, "name":str(keepsake.name) + " / pick up", "x":keepsake.x, "y":keepsake.y, "kind":"keepsake", "hit_rect":[-16,-22,32,30]})
	for object: Dictionary in room_objects:
		if object.id in ["imani", "walt"] and state.flags.get(str(object.id) + "_joined", false): continue
		var area: Area2D = Area2D.new()
		area.position = Vector2(float(object.x), float(object.y))
		area.collision_layer = 4; area.collision_mask = 2
		area.set_meta("definition", object)
		var collision: CollisionShape2D = CollisionShape2D.new()
		var shape: CircleShape2D = CircleShape2D.new(); shape.radius = 28
		collision.shape = shape; area.add_child(collision); world.add_child(area); areas.append(area)
		if object.id in ["claim", "pinpal"]:
			var prop: Node2D = (load("res://scenes/claim_actor.gd") if object.id == "claim" else load("res://scenes/pin_actor.gd")).new()
			prop.position = area.position
			prop.set_meta("id", str(object.id))
			if state.flags.has(str(object.id) + "_resolution"):
				prop.set_pose("resolved" if state.flags[str(object.id) + "_resolution"] == "peaceful" else "down")
			world.add_child(prop); scene_props.append(prop)
		elif object.kind == "keepsake":
			var glint: NativeKeepsakeGlint = NativeKeepsakeGlint.new()
			glint.position = area.position
			glint.set_meta("id", str(object.id))
			world.add_child(glint); scene_props.append(glint)
		elif object.has("sprite"):
			var npc: AnimatedSprite2D = AnimatedSprite2D.new()
			var asset: String = "flyerer" if object.sprite == "flyer" else str(object.sprite).replace("-", "_") if str(object.sprite).begins_with("npc-") else str(object.sprite) + "_world"
			var art_id: String=str(object.sprite).trim_prefix("npc-").replace("-","_")
			var encounter: bool=NativeBossArt.encounter_cast(art_id)
			var upgraded: bool=art_id in NativeCastArt.IDS or art_id in ["flyer","imani","eric"] or encounter
			npc.sprite_frames = NativePartyArt.frames(art_id) if art_id in ["walt","imani"] else NativeBossArt.frames(art_id) if encounter else NativeCastArt.frames(art_id) if upgraded else load("res://resources/art_%s.tres" % asset)
			if seated_frames(object, npc): art_id += "_seated"; upgraded = false
			npc.centered = false
			npc.offset = Vector2(-16, -48)
			npc.position = area.position; npc.play("idle" if object.sprite == "flyer" else "idle_down")
			npc.set_meta("id",str(object.id));npc.set_meta("art_id",art_id);npc.set_meta("idle_height",NativeCastArt.world_height(art_id))
			if upgraded:
				var height: float=NativeCastArt.world_height(art_id)
				npc.frame_changed.connect(func() -> void: NativeCastArt.fit(npc, height))
				npc.animation_changed.connect(func() -> void: NativeCastArt.fit(npc, height))
				NativeCastArt.fit(npc, height)
				var native_texture: Texture2D=npc.sprite_frames.get_frame_texture(npc.animation,npc.frame)
				var visible_rect: Rect2i=native_texture.get_image().get_used_rect()
				var native_rect:=Rect2(npc.offset+Vector2(visible_rect.position),Vector2(visible_rect.size)).grow(2)
				var previous: Array=object.get("hit_rect",[-24,-30,48,40])
				var click_rect:=Rect2(previous[0],previous[1],previous[2],previous[3]).merge(native_rect)
				object.hit_rect=[click_rect.position.x,click_rect.position.y,click_rect.size.x,click_rect.size.y]
			if object.id == "flyer" and state.flags.has("flyer_resolution"):
				npc.play("settled" if state.flags.flyer_resolution == "peaceful" else "down")
				if state.flags.flyer_resolution == "forceful": npc.modulate = Color("b5827b")
			world.add_child(npc); world_npcs.append(npc)
	NativeRoomScenes.reset()
	NativeJakerson.on_enter(self, id)
	NativeSpatialProp.room_left = float(camera.limit_left); NativeSpatialProp.room_size = Vector2(float(camera.limit_right), float(camera.limit_bottom))
	NativeSpatialProp.watch = [player, pip] + followers + world_npcs
	NativeMoveIn.on_enter(self, id)
	for source: Array in rooms[id].lights:
		var pos := Vector2(source[0], source[1])
		var light: PointLight2D = PointLight2D.new()
		light.texture = load("res://assets/art/lamp-light-mask.png")
		light.color = Color("ffcf8f"); light.energy = 0.55; light.position = pos
		lighting.add_child(light)
	audio.set_paused(false)
	audio.room_music(NativeSoundtrack.room_cue(id, str(rooms[id].cue), state.flags))
	audio.ambient("quiet-birds" if id in ["N01","N05"] else "campus-air" if id=="E01" else "hall-clock" if id.begins_with("N") else "umc-room" if id.begins_with("E") else "campus-air" if id.begins_with("F") else "quiet-birds" if id == "U01" else "campus-air" if id in ["U02", "U08"] else "hall-clock" if id in ["U05", "U07"] else "umc-room")
	transition_ticks = 18; input_lock = 3; ui_dirty = true
	if save_now: persist()

func object_at(point: Vector2) -> Dictionary:
	var chosen: Dictionary = {}
	var best: float = INF
	for area: Area2D in areas:
		var object: Dictionary = area.get_meta("definition")
		var raw: Array = object.get("hit_rect", [-24, -30, 48, 40])
		var box := Rect2(area.position + Vector2(raw[0], raw[1]), Vector2(raw[2], raw[3]))
		if not box.has_point(point): continue
		var score: float = point.distance_squared_to(box.get_center())
		if score < best: chosen = object; best = score
	return chosen

func nearest_object() -> Dictionary:
	var nearest: Dictionary = {}
	var distance: float = 38.0
	for area: Area2D in areas:
		var d: float = player.position.distance_to(area.position)
		if d < distance and not (area.get_meta("definition").kind == "door" and arrival_guarded(area.position)):
			distance = d; nearest = area.get_meta("definition")
	return nearest

## The door you just came through stays quiet until you take a few steps, so a
## confirm press left over from dialogue cannot walk you straight back out.
func arrival_guarded(door: Vector2) -> bool:
	return arrival_point != Vector2.INF and door.distance_to(arrival_point) < 44

## Deltarune-style growth: stats follow story milestones and keepsakes.
func refresh_growth() -> void:
	var before: int = int(str(state.flags.get("growth_seen", "0")))
	var reached: int = PartyGrowth.milestones(state.flags)
	# Only a new milestone heals; keepsake swaps just move max HP.
	state.party = PartyGrowth.apply(state.party, state.flags, reached > before)
	if reached > before:
		state.flags.growth_seen = str(reached)
		growth_note = "Everyone feels steadier. Max HP up. Power up."

## A room NPC can sit (Walt on his cardboard) until a flag is set: one still pose held as its idle.
func seated_frames(object: Dictionary, npc: AnimatedSprite2D) -> bool:
	var seated: Dictionary = object.get("seated", {})
	if seated.is_empty() or state.flags.get(str(seated.until), false): return false
	var still: Texture2D = load(str(seated.texture))
	var pose: Texture2D = ImageTexture.create_from_image(still.get_image())
	pose.set_meta("foot", Vector2(float(seated.anchor[0]), float(seated.anchor[1])))
	var frames := SpriteFrames.new()
	frames.add_animation("idle_down")
	frames.add_frame("idle_down", pose); frames.add_frame("idle_down", pose)
	frames.set_meta("native_height", roundi(NativeCastArt.world_height(str(object.sprite).trim_prefix("npc-") + "_seated")))
	npc.sprite_frames = frames
	return true

func living_speakers() -> Array[String]:
	var present: Array[String] = ["Jules"]
	for member: String in ["imani", "walt", "pip"]:
		if state.flags.get(member + "_joined", false): present.append(member.capitalize())
	var names: Dictionary = {"jakerson":"Jakerson", "mara":"Mara", "eli":"Eli", "chip":"Chip", "deion":"Deion Sanders", "todd":"Todd Saliman", "flyer":"Flyerer", "mags":"Mags", "mags_cleanup":"Mags", "imani":"Imani", "cal":"Cal", "walt":"Walt", "encore":"ENCORE", "rook":"Rook", "nell":"Nell", "dev":"Dev", "errata":"Gwen the Red", "autocomplete":"AUTOCOMPLETE", "loadbearer":"LOADBEARER", "eric":"Professor Eric"}
	for npc: AnimatedSprite2D in world_npcs:
		var name: String = names.get(str(npc.get_meta("id", "")), "")
		if not name.is_empty() and not name in present: present.append(name)
	for prop: Node2D in scene_props:
		var name: String = {"claim":"CLAIM", "pinpal":"Pin Pal"}.get(str(prop.get_meta("id", "")), "")
		if not name.is_empty(): present.append(name)
	return present

func interact(object: Dictionary) -> void:
	audio.combat("pick")
	NativeLinkedOutMenu.met(self, object)
	if NativeMoveIn.handle(self, object): return
	if NativeJakerson.handle(self,object):return
	if object.kind == "keepsake":
		pick_up_keepsake(str(object.keepsake)); return
	if NativeCampaign.handle(self, object): return
	if NativeSideBosses.handle(self, object): return
	if NativeShops.handle(self, object): return
	if object.kind == "save" and not str(object.id) in ["lamp", "farrand_lamp"]:
		rest_menu(); return
	if object.kind in ["battle", "challenge"] and not state.flags.get("walt_joined", false):
		if not state.flags.get("imani_joined", false):
			# The poster has its own line; everything else waits on the mixer.
			if str(object.id) != "flyer":
				dialogue([["Jules", "Not now. Imani's mixer comes first.", "neutral"]], resume_world); return
		else:
			dialogue([["Jules", "The voice went under Broadway. We should follow it to the underpass first.", "concern"]], resume_world)
			return
	if object.kind == "door":
		use_door(object); return
	var discovery: Dictionary = NativeDiscoveries.scene(str(object.id), state, living_speakers())
	if not discovery.is_empty():
		dialogue(discovery.lines, func() -> void:
			for flag: String in discovery.complete: state.flags[flag] = true
			if object.id == "arcade_button" and not discovery.complete.is_empty(): audio.combat("pick")
			for prop: Node2D in environment.foreground_nodes: prop.queue_redraw()
			persist(); resume_world())
		return
	if object.kind == "challenge":
		if state.flags.has(str(object.id) + "_resolution"):
			dialogue([["Chip" if object.id == "chip" else "Deion Sanders", "The rehearsal is finished. Let everyone rest.", "warm"]], resume_world)
			return
		dialogue(object.lines, func() -> void: open_menu(Mode.MENU, str(object.name), [option("Try the friendly challenge", func() -> void:
			boss_id = str(object.id); start_battle()), option("Maybe later", resume_world)])); return
	match str(object.id):
		"imani":
			if NativeImaniJoin.talk(self): return
			dialogue([["Imani", "My mixer! You came back. I was beginning to write a song about betrayal.", "warm"], ["Jules", "Would the bag get a solo?", "warm"], ["Imani", "A terrible one. Listen, could you help with sound check, then chairs, then-", "warm"], ["Jules", "I promised Mom I would catch the last bus. One task. That was the deal.", "concern"], ["Imani", "Right. Sorry. I keep making the room louder so I do not have to hear how nervous I am.", "concern"]], resume_world, [option("I can stay for one sound check.", func() -> void: complete_mixer("candid")), option("Return it, but explain the deadline.", func() -> void: complete_mixer("boundary"))])
		"booth":
			if not state.flags.get("imani_joined", false):
				dialogue([["Jules", "NEXT YEAR. Say who you will become. I do not have time to audition for tomorrow.", "concern"]], resume_world)
			else:
				dialogue([["Booth", "Jules Navarro. Tomorrow you will wish you had stayed.", "concern"], ["Jules", "That was my voice. I did not record that.", "concern"], ["Imani", "The booth is not connected to the mixer. It is connected to the floor.", "concern"], ["Jules", "Then we find out who is down there. One real answer. Not our entire future.", "warm"]], func() -> void: state.flags.booth_seen = true; persist(); resume_world())
		"lamp", "farrand_lamp":
			rest_menu()
		"flyer", "pinpal", "claim":
			var key: String = str(object.id) + "_resolution"
			if state.flags.has(key):
				dialogue([["Jules", "We have already made room here.", "warm"]], resume_world); return
			if object.id == "flyer" and not state.flags.get("imani_joined", false):
				dialogue([["Flyerer", "RETURN FIRST. RECRUIT LATER. RETURN FIRST!", "concern"]], resume_world); return
			boss_id = "" if object.id == "flyer" else str(object.id)
			var intro: Dictionary = {"flyer": [["Flyerer", "ONE PAGE! JUST ONE! THE CLUB CANNOT CLOSE IF NOBODY READS!", "concern"], ["Imani", "That poster was just a poster a minute ago. Now it has opinions. We should probably discuss that.", "concern"], ["Jules", "We can read one invitation. Or make enough room to walk past.", "neutral"]], "pinpal": [["Pin Pal", "RETURN SERVICE! RETURN SERVICE!", "warm"], ["Walt", "A bowling pin practicing returns. One ball at a time. I respect a clear job.", "warm"]], "claim": [["CLAIM", "TAKE A NUMBER. TAKE A COAT. TAKE A RESPONSIBILITY. EVERYTHING HAS AN OWNER.", "concern"], ["Jules", "That glove looks like it is waving.", "concern"], ["Imani", "We can carry one thing. We cannot be the owner of every forgotten thing.", "warm"]]}
			dialogue(intro[str(object.id)], start_battle)
		_:
			if object.id == "squirrel": audio.combat("squirrel")
			var contextual: Array = environment.context_lines(str(object.id), state.flags)
			dialogue(contextual if not contextual.is_empty() else object.get("lines", [["Jules", "Something unfinished.", "neutral"]]), resume_world)

## A lamp, a bench or a beanbag: the party rests to full and the player can save.
func rest_menu() -> void:
	for member: Dictionary in state.party: member.hp = member.max
	audio.effect("save")
	open_menu(Mode.MENU, "Warm light / rest and save", [option("Save slot 1", func() -> void: manual_save("slot1")), option("Save slot 2", func() -> void: manual_save("slot2")), option("Save slot 3", func() -> void: manual_save("slot3")), option("Back", resume_world)])

func pick_up_keepsake(id: String) -> void:
	var keepsake: Dictionary = PartyGrowth.KEEPSAKES[id]
	var holder: String = str(keepsake.member)
	state.flags["keepsake_" + id] = true
	var equip_now: bool = PartyGrowth.equipped(state.flags, holder).is_empty()
	if equip_now: state.flags["keepsake_" + holder] = id
	for area: Area2D in areas.duplicate():
		if area.get_meta("definition").get("keepsake", "") == id:
			areas.erase(area); area.queue_free()
	for prop: Node2D in scene_props.duplicate():
		if str(prop.get_meta("id", "")) == "keepsake_" + id:
			scene_props.erase(prop); prop.queue_free()
	refresh_growth()
	audio.effect("save")
	var effect: String = str(PartyGrowth.STAT_TEXT[keepsake.stat]) % int(keepsake.amount)
	if PartyGrowth.PERKS.has(id): effect += ". " + str(PartyGrowth.PERKS[id])
	var note: String = ("%s: %s for %s. Swap in Pause > Party." % [keepsake.name, effect, holder.capitalize()]) if equip_now else ("%s kept for %s: %s. Swap in Pause > Party." % [keepsake.name, holder.capitalize(), effect])
	dialogue(keepsake.lines, func() -> void: persist(); resume_world(); message(note))

func party_menu() -> void:
	var options: Array = []
	for i: int in range(3):
		var member: Dictionary = state.party[i]
		var id: String = str(member.id)
		if i > 0 and not state.flags.get(id + "_joined", false): continue
		var worn: String = PartyGrowth.equipped(state.flags, id)
		options.append(option("%s HP %d/%d POW %d DEF %d / %s" % [id.capitalize(), int(member.hp), int(member.max), int(member.power), int(member.defence), PartyGrowth.KEEPSAKES[worn].name if not worn.is_empty() else "no keepsake"], func() -> void: cycle_keepsake(id)))
	options.append(option("Back", pause_menu))
	open_menu(Mode.MENU, "Party / %schoose someone to swap their keepsake" % ("Buff Bucks %d / " % NativeRandomFights.bucks(state.flags) if state.flags.has("buff_bucks") else ""), options)

func cycle_keepsake(member: String) -> void:
	var owned: Array[String] = PartyGrowth.owned(state.flags, member)
	if owned.is_empty():
		caption = "%s has no keepsakes yet. Look in quiet corners." % member.capitalize(); ui_dirty = true; return
	var choices: Array = [""] + owned
	var next: String = str(choices[(choices.find(PartyGrowth.equipped(state.flags, member)) + 1) % choices.size()])
	state.flags["keepsake_" + member] = next
	refresh_growth()
	var keep: int = selection
	party_menu()
	selection = keep
	caption = (member.capitalize() + " / " + PartyGrowth.describe(next) + (" / " + str(PartyGrowth.PERKS[next]) if PartyGrowth.PERKS.has(next) else "")) if not next.is_empty() else member.capitalize() + " / no keepsake"

func complete_mixer(response: String) -> void:
	# Imani no longer joins here: she joins in the atrium on the way out (services/imani_join.gd).
	NativeImaniJoin.complete_mixer(self, response)

func resume_world() -> void:
	mode = Mode.WORLD
	refresh_growth()
	NativeLinkedOutMenu.notify(self)
	for npc: AnimatedSprite2D in world_npcs:
		var id: String = str(npc.get_meta("id", ""))
		if str(npc.get_meta("art_id",id)) in NativeCastArt.IDS or id == "flyer": npc.play("settled" if state.flags.get(id + "_resolution", "") == "peaceful" else "down" if state.flags.has(id + "_resolution") else "idle_down")
	for prop: Node2D in scene_props:
		var id: String = str(prop.get_meta("id", ""))
		prop.set_pose("resolved" if state.flags.get(id + "_resolution", "") == "peaceful" else "down" if state.flags.has(id + "_resolution") else "idle")
	for prop: Node2D in environment.foreground_nodes:
		if prop is NativeSpatialProp: prop.set_pose("idle")
	pip.set_pose("idle")
	input_lock = 2
	ui_dirty = true

func option(label: String, callback: Callable) -> Dictionary:
	return {"label": label, "run": callback}

func open_menu(next_mode: Mode, title: String, options: Array) -> void:
	if next_mode != Mode.DODGE: pointer_duck = false; pointer_hop = 0
	# Entering the command menu from a defense or dialogue: half a second for
	# mashed confirm presses to die out, so they cannot queue STRIKE by accident.
	var settle: bool = next_mode == Mode.BATTLE and mode != Mode.BATTLE
	mode = next_mode
	hover_index = -1
	caption = title
	menu_options = options
	selection = 0
	input_lock = 30 if settle else 2
	ui_dirty = true

func activate(index: int) -> void:
	if input_lock > 0 or index < 0 or index >= menu_options.size():
		return
	audio.effect("confirm", 0.5)
	battle_error = ""
	var callback: Callable = menu_options[index].run
	callback.call()
	input_lock = maxi(input_lock, 2)
	ui_dirty = true

func show_title() -> void:
	jakerson_ui=false
	notice = ""; notice_ticks = 0; growth_note = ""
	set_cast_paused(false)
	reset_pointer_controls()
	pause_context = false
	world.visible = false; backdrop.visible = true
	camera.position = Vector2(320, 180); camera.limit_left = 0; camera.limit_top = 0; camera.limit_right = 640; camera.limit_bottom = 360
	_set_battle_visible(false)
	boss_id = ""
	var continue_option: Dictionary = option("Continue", func() -> void: load_save("auto"))
	if not has_continue():
		continue_option = option("Continue / no save yet", func() -> void: message("No save yet. Choose Begin the evening to start one."))
		continue_option.disabled = true
	open_menu(Mode.TITLE, "AFTER HOURS", [option("Begin the evening", new_game), continue_option, option("Save files", func() -> void: save_menu(true)), option("Settings", func() -> void: settings_return_title = true; settings_menu()), option("Credits", func() -> void: dialogue([["After Hours", "Original Boulder story RPG. Full Evening / 0.7.2. Thirty-six playable rooms through Macky, three endings and a playable dawn.", "neutral"], ["Production", "Original score, pixel environments and effects. AI-assisted dialogue and sunset art. Vocal textures are nonverbal, not recorded speech.", "neutral"]], show_title))])
	audio.set_paused(false); audio.room_music("arrival"); audio.ambient("campus-air")

func has_continue() -> bool:
	if not saves.load_slot("auto").has("error"): return true
	# An unreadable or newer save still offers Continue, which then explains why it cannot load.
	if FileAccess.file_exists(saves.base_path.path_join("auto.json")): return not qa
	return not qa and not NativeCampaign.legacy_slot(self, "auto").has("error")

## A new game opens on move-in day in Farrand Hall; skipping the cards goes straight to the evening.
func new_game() -> void:
	state = NativeState.fresh(state.settings)
	notice = ""; notice_ticks = 0; growth_note = ""
	boss_id = ""
	intro_cards = NativeMoveIn.CARDS; intro_arrival = -1
	enter_room(NativeMoveIn.START, NativeMoveIn.ENTRY, false)
	world.visible = false; backdrop.visible = true
	intro_index = 0; intro_ticks = 0; mode = Mode.INTRO; ui_dirty = true

## "Four years later", then the Last Light evening on Broadway.
func begin_evening() -> void:
	intro_cards = NativeMoveIn.evening_cards(INTRO_CARDS); intro_arrival = intro_cards.size() - 1
	enter_room("U01", Vector2(96, 258), false)
	world.visible = false; backdrop.visible = true
	intro_index = 0; intro_ticks = 0; mode = Mode.INTRO; ui_dirty = true

func dialogue(lines: Array, completed: Callable, choices: Array = []) -> void:
	dialogue_lines = []
	# Pages follow the box: wrap at the text column's width, then up to three lines a page (four
	# in large text), split evenly so no page is left holding one stray word.
	var large: bool = state.settings.large
	var per_line: int = floori(448.0 / (GLYPH * (2.0 if large else 1.0)))
	var room: int = 4 if large else 3
	for line: Array in lines:
		var mood: String = str(line[2]) if line.size() > 2 else "neutral"
		var rows: Array[String] = []
		var row: String = ""
		for word: String in str(line[1]).split(" "):
			if row.length() + word.length() + 1 > per_line and not row.is_empty():
				rows.append(row); row = ""
			row += (" " if not row.is_empty() else "") + word
		if not row.is_empty(): rows.append(row)
		var pages: int = ceili(float(rows.size()) / room)
		var start: int = 0
		for page: int in range(pages):
			var take: int = ceili(float(rows.size() - start) / (pages - page))
			dialogue_lines.append([line[0], " ".join(rows.slice(start, start + take)), mood])
			start += take
	line_index = 0; reveal = 0; phrase_pause = 0
	dialogue_top = false
	dialogue_callback = completed; dialogue_choices = choices
	mode = Mode.DIALOGUE; input_lock = 2; ui_dirty = true
	stage_dialogue()

func advance_dialogue() -> void:
	var text: String = str(dialogue_lines[line_index][1])
	if reveal < text.length():
		reveal = text.length()
	elif line_index < dialogue_lines.size() - 1:
		line_index += 1
		reveal = 0
		phrase_pause = 0
		stage_dialogue()
	else:
		var choices: Array = dialogue_choices
		dialogue_choices = []
		dialogue_callback.call()
		if not choices.is_empty():
			open_menu(Mode.MENU, choice_caption(choices), choices)
	input_lock = maxi(input_lock, 2)
	ui_dirty = true

## Choices that all begin with a party member's name are that person's to make.
func choice_caption(choices: Array) -> String:
	for who: String in ["Imani", "Walt", "Pip"]:
		if choices.all(func(c: Dictionary) -> bool: return str(c.label).begins_with(who + " ")): return "What does %s choose?" % who
	return "How does Jules answer?"

func message(text: String) -> void:
	notice = text
	notice_ticks = 180
	ui_dirty = true

func persist(slot: String = "auto") -> bool:
	refresh_growth()
	var error: Error = saves.save(slot, state)
	if error != OK: message("Save failed. Previous checkpoint retained.")
	return error == OK

func manual_save(slot: String) -> void:
	if persist(slot):
		resume_world()

func load_save(slot: String) -> void:
	var record: Dictionary = saves.load_slot(slot)
	if record.has("error") and not qa and not FileAccess.file_exists(saves.base_path.path_join(slot + ".json")):
		record = NativeCampaign.legacy_slot(self, slot)
	if record.has("error"):
		message(str(record.error))
		return
	restore_state(record.state)
	message("Recovered previous-good backup." if record.backup else "Loaded " + slot + ".")

func restore_state(restored: Dictionary) -> void:
	growth_note = ""
	state = NativeCampaign.migrate(restored)
	state.settings = NativeState.normalize_audio_settings(state.settings)
	# Current accessibility/audio/key preferences outlive an older checkpoint.
	# If none exist, retain the migrated settings supplied by the save.
	_load_preferences()
	configure_input()
	audio.set_mix_gains(float(state.settings.music), float(state.settings.effects), float(state.settings.voices), float(state.settings.ambience))
	player.visible = true
	enter_room(str(state.room), Vector2(float(state.x), float(state.y)), false)
	if state.flags.has("claim_resolution") and not state.flags.get("opening_finished", false):
		state.flags.opening_finished = true; state.flags.pip_joined = true
		if str(state.flags.get("aftermath_pending", "")).is_empty(): state.flags.aftermath_pending = "claim"
		persist()
	if state.flags.get("walt_intro_pending", false):
		NativeCampaign.introduce_legacy(self)
	elif not str(state.flags.get("aftermath_pending", "")).is_empty():
		show_aftermath(str(state.flags.aftermath_pending))
	elif not str(state.flags.get("val_checkpoint", "")).is_empty() and not state.flags.has("val_resolution"):
		boss_id="val";checkpoint=state.duplicate(true);begin_battle()

func save_menu(from_title: bool = false) -> void:
	var options: Array = []
	for slot: String in ["auto", "slot1", "slot2", "slot3"]:
		options.append(option("Load " + slot, func() -> void: load_save(slot)))
	options.append(option("Export current save", func() -> void: file_dialog(false)))
	options.append(option("Import save", func() -> void: file_dialog(true)))
	options.append(option("Back", show_title if from_title else pause_menu))
	open_menu(Mode.MENU, "Save / load / portable backup", options)

func file_dialog(importing: bool) -> void:
	var picker: FileDialog = FileDialog.new()
	picker.access = FileDialog.ACCESS_FILESYSTEM
	picker.file_mode = FileDialog.FILE_MODE_OPEN_FILE if importing else FileDialog.FILE_MODE_SAVE_FILE
	picker.filters = PackedStringArray(["*.json ; After Hours save"])
	picker.title = "Import checkpoint" if importing else "Export checkpoint"
	picker.current_file = "after-hours-save.json"
	picker.use_native_dialog = true
	add_child(picker)
	picker.file_selected.connect(func(path: String) -> void:
		if importing:
			var result: Dictionary = saves.import_file(path)
			if result.has("error"):
				message(str(result.error))
			else:
				restore_state(result.state)
				persist()
		else:
			var error: Error = saves.export_file(path, state)
			message("Checkpoint exported." if error == OK else "Export failed: " + error_string(error))
		picker.queue_free())
	picker.canceled.connect(func() -> void: picker.queue_free())
	picker.popup_centered(Vector2i(600, 320))

func set_cast_paused(value: bool) -> void:
	if value:
		# Capture only running animations; distance-driven walk frames stay manual.
		for sprite: AnimatedSprite2D in find_children("*", "AnimatedSprite2D", true, false):
			if sprite.is_playing():
				paused_cast_sprites.append(sprite)
				sprite.pause()
	else:
		for sprite: AnimatedSprite2D in paused_cast_sprites:
			if is_instance_valid(sprite):sprite.play()
		paused_cast_sprites.clear()

func open_pause() -> void:
	reset_pointer_controls()
	if not pause_context:
		set_cast_paused(true)
		pause_context = true
		pause_mode = mode
		pause_options = menu_options.duplicate()
		pause_caption = caption
		pause_selection = selection
	settings_return_title = false
	audio.set_paused(true)
	pause_menu()

func pause_menu() -> void:
	var options: Array = [option("Resume", resume_pause)]
	if pause_mode == Mode.WORLD: options.append_array([option("Campus map", open_map), option("Party / keepsakes", party_menu), option("LinkedOut" + NativeLinkedOutMenu.badge(state.flags), func() -> void: NativeLinkedOutMenu.open(self))])
	options.append_array([option("Settings", settings_menu), option("Saves / import / export", func() -> void: save_menu(false)), option("Return to title", show_title)])
	open_menu(Mode.PAUSE, "Paused", options)

func open_map() -> void:
	map_from_pause = pause_context
	if not pause_context: open_pause()
	mode = Mode.MAP
	campus_map.refresh()
	campus_map.show()
	NativeJakerson.observe_map(self)
	ui_dirty = true

func close_map() -> void:
	campus_map.hide()
	if map_from_pause: pause_menu()
	else: resume_pause()

func resume_pause() -> void:
	set_cast_paused(false)
	pause_context = false
	mode = pause_mode
	menu_options = pause_options
	caption = pause_caption
	selection = pause_selection
	input_lock = 2
	resume_ticks = 90 if mode == Mode.DODGE else 0
	audio.set_paused(resume_ticks > 0)
	ui_dirty = true

func cancel_menu() -> void:
	if mode == Mode.BATTLE:
		if caption.contains("Choose an action"):
			undo_command()
		else:
			command_menu()
	elif mode == Mode.PAUSE:
		resume_pause()
	elif mode == Mode.MENU:
		var back: Callable = Callable()
		for choice: Dictionary in menu_options:
			if choice.label in ["Back", "Leave it for now"]:
				back = choice.run
		if back.is_valid():
			back.call()
		# Required dialogue answers have no cancel path.

func settings_menu() -> void:
	var options: Array = [option("Music %d%%" % roundi(float(state.settings.music) * 100), func() -> void:
		state.settings.music = 0.0 if float(state.settings.music) >= 1 else minf(1, ceilf((float(state.settings.music) + 0.001) * 4) / 4)
		_save_preferences()
		settings_menu()), option("Effects %d%%" % roundi(float(state.settings.effects) * 100), func() -> void:
		state.settings.effects = 0.0 if float(state.settings.effects) >= 1 else minf(1, ceilf((float(state.settings.effects) + 0.001) * 4) / 4)
		_save_preferences()
		settings_menu())]
	for gain: String in ["voices", "ambience"]:
		options.append(option(gain.capitalize() + " %d%%" % roundi(float(state.settings[gain]) * 100), func() -> void:
			var value: float = float(state.settings[gain])
			state.settings[gain] = 0.0 if value >= 1.0 else minf(1.0, ceilf((value + 0.001) * 4) / 4)
			_save_preferences(); settings_menu()))
	for key: String in ["blips", "instant", "large", "damageAssist", "autoTiming", "reducedMotion"]:
		options.append(option("%s: %s" % [{"blips":"Dialogue sounds", "instant":"Instant dialogue", "large":"Large dialogue text", "damageAssist":"Reduced incoming damage", "autoTiming":"Automatic strike timing", "reducedMotion":"Reduced motion"}[key], "on" if state.settings[key] else "off"], func() -> void:
			state.settings[key] = not state.settings[key]
			_save_preferences()
			settings_menu()))
	options.append(option("Dodge speed %d%%" % roundi(float(state.settings.assist) * 100), func() -> void:
		state.settings.assist = 0.85 if float(state.settings.assist) == 1.0 else (0.7 if float(state.settings.assist) == 0.85 else 1.0)
		_save_preferences()
		settings_menu()))
	if not settings_return_title and pause_mode == Mode.WORLD:
		options.append(option("Wandering fights: %s" % ("Off" if bool(state.flags.get("wander_off", false)) else "On"), func() -> void:
			state.flags.wander_off = not bool(state.flags.get("wander_off", false))
			persist(); settings_menu()))
	options.append(option("Remap keyboard", remap_menu))
	options.append(option("Back", show_title if settings_return_title else pause_menu))
	open_menu(Mode.MENU, "Settings / story outcomes stay the same", options)

func remap_menu() -> void:
	var options: Array = []
	for action: String in ["move_up", "move_down", "move_left", "move_right", "confirm", "cancel", "menu", "run"]:
		options.append(option(str({"move_up":"Move up", "move_down":"Move down", "move_left":"Move left", "move_right":"Move right", "confirm":"Confirm / interact", "cancel":"Back / cancel", "menu":"Pause", "run":"Run / precision"}[action]) + " / " + binding_label(action), func() -> void:
			binding_capture = action
			caption = "Press a key / Esc or Cancel remap to leave"
			ui_dirty = true))
	options.append(option("Back", settings_menu))
	open_menu(Mode.MENU, "Choose an action, then press a key", options)

func binding_label(action: String,method: String="keyboard") -> String:
	var labels: Array[String]=[]
	var pad_names: Dictionary={JOY_BUTTON_A:"Pad A/Cross",JOY_BUTTON_B:"Pad B/Circle",JOY_BUTTON_X:"Pad X/Square",JOY_BUTTON_Y:"Pad Y/Triangle",JOY_BUTTON_LEFT_SHOULDER:"Pad LB/L1",JOY_BUTTON_RIGHT_SHOULDER:"Pad RB/R1",JOY_BUTTON_DPAD_UP:"D-pad up",JOY_BUTTON_DPAD_DOWN:"D-pad down",JOY_BUTTON_DPAD_LEFT:"D-pad left",JOY_BUTTON_DPAD_RIGHT:"D-pad right"}
	for event: InputEvent in InputMap.action_get_events(action):
		var text: String=""
		if event is InputEventKey and method in ["keyboard","all"]:
			var code: int=event.physical_keycode if event.physical_keycode!=0 else event.keycode
			text=OS.get_keycode_string(code)
		elif event is InputEventJoypadButton and method in ["controller","all"]:
			text=str(pad_names.get(event.button_index,"Pad button "+str(event.button_index)))
		elif event is InputEventJoypadMotion and method in ["controller","all"]:
			if event.axis==JOY_AXIS_LEFT_X:text="Left stick "+("left" if event.axis_value<0 else "right")
			elif event.axis==JOY_AXIS_LEFT_Y:text="Left stick "+("up" if event.axis_value<0 else "down")
			else:text="Pad axis "+str(event.axis)+(" -" if event.axis_value<0 else " +")
		if not text.is_empty() and not text in labels:labels.append(text)
	return " / ".join(labels) if not labels.is_empty() else "Unbound "+method

func _load_preferences() -> void:
	var path: String = preferences_path
	if not qa and not FileAccess.file_exists(path):
		for folder: String in ["AfterHoursCollegeTaleChapter3", "AfterHoursCollegeTaleChapter2","AfterHoursCollegeTaleChapter1","AfterHoursCollegeTaleOpening02"]:
			var candidate: String=OS.get_environment("APPDATA").path_join(folder+"/preferences.json")
			if FileAccess.file_exists(candidate):path=candidate;break
	if FileAccess.file_exists(path):
		var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		if data is Dictionary:
			var candidate: Dictionary = NativeState.fresh(data)
			if NativeSaveService.validate_state(candidate):
				state.settings = candidate.settings

func _save_preferences() -> void:
	var file: FileAccess = FileAccess.open(preferences_path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(state.settings))
		file.flush()
		file.close()
	else:
		message("Settings could not be saved.")
	audio.set_mix_gains(float(state.settings.music), float(state.settings.effects), float(state.settings.voices), float(state.settings.ambience))

func _build_battle_sprites() -> void:
	for i: int in range(3):
		var sprite: AnimatedSprite2D = AnimatedSprite2D.new()
		sprite.sprite_frames = NativePartyBattleArt.frames(ACTORS[i])
		sprite.centered = false
		sprite.offset = Vector2(-24, -72)
		sprite.position = Vector2(48 + i * 74, 150)
		sprite.z_index = 200
		add_child(sprite)
		sprite.play("idle")
		if i in [0,1,2]:
			sprite.frame_changed.connect(func() -> void: NativeCastArt.fit(sprite, 72.0))
			sprite.animation_changed.connect(func() -> void: NativeCastArt.fit(sprite, 72.0))
			NativeCastArt.fit(sprite, 72.0)
		battle_sprites.append(sprite)
	foe = AnimatedSprite2D.new()
	foe.sprite_frames = NativeCastArt.frames("flyer")
	foe.centered = false
	foe.offset = Vector2(-32, -64)
	foe.position = Vector2(480, 146)
	foe.z_index = 200
	add_child(foe)
	foe.play("idle")
	foe.frame_changed.connect(func() -> void: NativeCastArt.fit(foe, foe_height()))
	foe.animation_changed.connect(func() -> void: NativeCastArt.fit(foe, foe_height()))
	NativeCastArt.fit(foe, foe_height())
	wind_fx = NativeWindStreaks.new()
	wind_fx.z_index = 203
	add_child(wind_fx)
	_set_battle_visible(false)

func foe_height() -> float:
	return 40.0 if boss_id=="val" and boss_stage==3 else 104.0 if boss_id=="val" else 80.0

func _set_battle_visible(value: bool) -> void:
	for i: int in range(battle_sprites.size()):
		battle_sprites[i].visible = value and (i == 0 or state.flags.get(ACTORS[i] + "_joined", false))
	foe.visible = value and boss_id not in ["claim", "pinpal"]
	claim_art.visible = value and boss_id == "claim"
	pin_art.visible = value and boss_id == "pinpal"
	vfx.visible = value
	wind_fx.visible = value and boss_id == "walt"
	wind_fx.reduced = bool(state.settings.reducedMotion)
	battle_scenery.visible = value and battle_scenery.get_child_count() > 0

## Shows the room's own painted battle backdrop when it has one; otherwise rebuilds the current room
## (props and painted art, no people) behind the fight, framed so the back wall stays in view and
## the fighters stand on the room's floor.
func show_battle_scenery() -> void:
	clear_battle_scenery()
	var id: String = str(state.room)
	if NativeBattleBackdrop.available(id):
		var painted := NativeBattleBackdrop.new()
		painted.reduced_motion = bool(state.settings.reducedMotion)
		battle_scenery.add_child(painted)
		painted.configure(id, state.flags)
		battle_scenery.position = Vector2.ZERO
		battle_scenery.modulate = Color.WHITE if not state.flags.get("dawn_started", false) else Color(1.0, 0.94, 0.9)
		return
	if not rooms.has(id) or not rooms[id].has("dimensions"): return
	var size := Vector2(float(rooms[id].dimensions[0]), float(rooms[id].dimensions[1]))
	var floor_top: float = float(rooms[id].walk_bounds[1]) if rooms[id].has("walk_bounds") else 120.0
	var origin := Vector2(clampf(player.position.x - 320.0, 0.0, maxf(0.0, size.x - 640.0)), clampf(floor_top - 112.0, 0.0, maxf(0.0, size.y - 360.0)))
	var scenery := UMCEnvironment.new()
	scenery.reduced_motion = bool(state.settings.reducedMotion)
	battle_scenery.add_child(scenery)
	scenery.configure(id, rooms[id], state.flags)
	scenery.glove_claimed = bool(state.flags.get("pip_joined", false))
	battle_scenery.position = -origin
	battle_scenery.modulate = Color(0.6, 0.62, 0.76) if not state.flags.get("dawn_started", false) else Color(0.78, 0.76, 0.76)

func clear_battle_scenery() -> void:
	for child: Node in battle_scenery.get_children():
		battle_scenery.remove_child(child); child.queue_free()
	battle_scenery.visible = false

func start_battle() -> void:
	checkpoint = state.duplicate(true)
	if persist():
		begin_battle()
	else:
		open_menu(Mode.MENU, "Checkpoint write failed", [option("Retry saving", start_battle), option("Continue without reload protection", begin_battle), option("Back", resume_world)])

func begin_battle() -> void:
	reset_pointer_controls()
	if qa and boss_id == "claim" and DisplayServer.get_name() != "headless":
		qa_record = AudioEffectRecord.new()
		AudioServer.add_bus_effect(0, qa_record)
		qa_record.set_recording_active(true)
	feedback.clear(); vfx.clear(); hit_flash = 0; NativeBattleJuice.clear()
	refresh_growth()
	battle = BattleRules.create_battle(state.party, state.inventory)
	battle.sync = mini(100, int(battle.sync) + PartyGrowth.starting_sync(state.flags))
	battle.pass_ready = PartyGrowth.has_perk(state.flags, "bus_pass")
	for i: int in range(1, 3):
		if not state.flags.get(ACTORS[i] + "_joined", false): battle.party[i].hp = 0
	rest_party_poses()
	boss_stage = 0; boss_rounds = 0; boundary_active = false; peak_music = false
	claim_needs = ClaimNeeds.create()
	last_promise_result = ""
	battle.rook_stage=0;battle.revision="";battle.val_revision="";battle.rejected=[];battle.val_stage=0;battle.final_ready=false;battle.val_force=false
	battle.lantern_kept = false; battle.final_cue = false; battle.campus_promise = false
	battle.hp = ({"cone":100,"chad":70,"rook":240,"val":200}[boss_id]) if boss_id in NativeFinalEncounter.IDS else (240 if boss_id=="autocomplete" else 100) if boss_id in NativeChapterTwo.BOSSES else 30 if boss_id == "jakerson" else 150 if boss_id == "jakerson_final" else 76 if boss_id == "walt" else 220 if boss_id == "encore" else 190 if boss_id == "claim" else 70 if boss_id == "pinpal" else int(BossDirector.profile(boss_id).maxHp) if not boss_id.is_empty() else 48
	foe.sprite_frames = NativeCastArt.frames(boss_id.trim_suffix("_final") if boss_id in ["chip", "deion", "todd", "walt", "encore", "errata", "autocomplete", "eric", "cone", "chad", "rook", "val", "jakerson", "jakerson_final"] else "flyer")
	foe.play("idle_down" if boss_id in ["chip", "deion", "todd", "walt", "encore", "errata", "autocomplete", "eric", "cone", "chad", "rook", "val", "jakerson", "jakerson_final"] else "idle")
	if NativeRandomFights.is_fight(boss_id): NativeRandomFights.setup(self)
	elif NativeSideBosses.is_boss(boss_id): NativeSideBosses.setup(self)
	NativeCastArt.fit(foe, foe_height())
	claim_art.set_pose("idle"); pin_art.set_pose("idle")
	plan = []; actor = 0; target = 0; retreating = false; notice_ticks = 0
	var full_hp: int = int(battle.hp)
	var resumed: bool = false
	if boss_id=="val":
		if NativeFinalCampaign.restore_checkpoint(self):
			resumed = true
			# A phase checkpoint keeps the party it was saved with; bring it up to the story's growth.
			battle.party = PartyGrowth.apply(battle.party, state.flags)
			for i: int in range(1, 3):
				if not state.flags.get(ACTORS[i] + "_joined", false): battle.party[i].hp = 0
		foe.sprite_frames=NativeCastArt.frames("val_small" if boss_stage==3 else "val");foe.play("idle_down");NativeCastArt.fit(foe,foe_height())
	shown_enemy_hp = int(battle.hp)
	# Desperation is measured against the boss's full HP, not HP restored from a checkpoint.
	battle.max_hp = full_hp
	# The practice spar starts half open so RELEASE is two kept turns away.
	if boss_id == "jakerson": battle.openness = 30
	while actor < battle.party.size() and int(battle.party[actor].hp) <= 0: actor += 1
	show_battle_scenery()
	world.visible = false; backdrop.visible = false; _set_battle_visible(true)
	camera.position = Vector2(320, 180); camera.limit_left = 0; camera.limit_top = 0; camera.limit_right = 640; camera.limit_bottom = 360
	hint = "Choose one action. Cancel revises your plan."
	audio.play_music("")
	audio.play_music(NativeSoundtrack.battle_cue(boss_id, "last-call" if boss_id=="rook" else "graduation" if boss_id=="val" else "boss-dark" if boss_id not in ["", "pinpal", "jakerson", "jakerson_final"] and not NativeRandomFights.is_fight(boss_id) else "battle-rich"))
	audio.ambient("")
	if actor >= battle.party.size():
		battle.outcome = "defeat"; defeat_menu(); return
	var opening: Callable = func() -> void:
		if boss_id == "jakerson": NativeJakerson.coach(self)
		else: command_menu()
	# Story bosses make an entrance first, like a gym leader; random fights start straight away,
	# and so does a fight resumed from a mid-fight checkpoint.
	if NativeBossIntro.has_card(boss_id) and not resumed:
		mode = Mode.BANNER; caption = ""; menu_options = []; ui_dirty = true
		NativeBossIntro.play(self, boss_id, opening)
	else: opening.call()

func command_menu() -> void:
	open_menu(Mode.BATTLE, str(battle.party[actor].id).capitalize() + " / Choose an action", [option("STRIKE", func() -> void: queue_command({"actor": actor, "kind": "strike"})), option("CONNECT", connect_menu), option("TALENT", talent_menu), option("ITEM", item_menu), option("GUARD", func() -> void: queue_command({"actor": actor, "kind": "guard"})), option("RETREAT", retreat)])

func connect_menu() -> void:
	if boss_id in NativeFinalEncounter.IDS:final_connect_menu();return
	var names: Dictionary = {"": ["Read the club's purpose", "Read one invitation", "Only one page tonight"], "chip": ["Ask for a small rehearsal", "Follow three called columns", "Applause can be quiet"], "deion": ["Ask for a clean handoff", "Carry the relay flag", "Practice, then take a break"], "todd": ["Ask what the form consents to", "Sign two consent boxes", "Allow unanswered questions"], "pinpal": ["Ask what needs returning", "Return three balls", "One ball at a time"], "claim": ["Identify the unclaimed glove", "Carry one numbered tag", "Return ONE thing; leave a note"]}
	names.jakerson_final = ["Ask what he'll miss", "Sign three diploma lines", "We stay friends after this"]
	names.jakerson = ["Ask what he's building", "Catch three green commits", "Spar's over when I say so"]
	names.walt = ["Ask how the lantern helps", "Keep the light through three gusts", "We can clear one path"]
	names.encore = ["Ask who gets to stop", "Answer two stopping cues", "A song can have an ending"]
	names.errata=["Ask whose voice is on the page", "Keep one sentence through three pauses", "Feedback needs consent"]
	names.eric=["Ask what he's measuring", "Probe three test points", "The demo can ship as is"]
	names.autocomplete=["Ask for the original voice", "Accept one useful suggestion", "Let the rest stay unwritten"]
	if NativeRandomFights.is_fight(boss_id): names[boss_id] = NativeRandomFights.connect_labels(boss_id)
	if NativeSideBosses.is_boss(boss_id): names[boss_id] = NativeSideBosses.connect_labels(boss_id)
	var lines: Array = names[boss_id]
	hint = "A promise creates a real objective in the next defense."
	var choices: Array = [option(str(lines[0]), func() -> void: queue_command({"actor": actor, "kind": "connect", "label": str(lines[0])})), option(str(lines[1]), func() -> void: queue_command({"actor": actor, "kind": "promise", "label": str(lines[1])}))]
	if boss_id != "claim" or bool(claim_needs.tagDelivered):
		choices.append(option(str(lines[2]), func() -> void: queue_command({"actor": actor, "kind": "guard", "boundary": true, "label": str(lines[2])})))
	if int(battle.openness) >= 100 and release_ready():
		choices.append(option("RELEASE / good game" if boss_id == "jakerson_final" else "RELEASE / enough for tonight", func() -> void: queue_command({"actor": actor, "kind": "release"})))
	choices.append(option("Back", command_menu))
	open_menu(Mode.BATTLE, "Connect / a concrete promise", choices)

func final_connect_menu() -> void:
	var choices: Array=[]
	var names: Dictionary={"cone":["Ask for one route","Follow three marked rows"],"chad":["Ask what he actually wants","Protect one free hour"],"rook":["Ask what one shift needs","Carry one key to one exit"],"val":["Ask who's really hiring","One answer, one full stop"]}
	choices.append(option(names[boss_id][0],func() -> void:queue_command({"actor":actor,"kind":"connect","label":names[boss_id][0]})))
	if boss_id=="rook" and boss_stage>=1:
		choices.append(option("REVISE / keep west exit; decline east",func() -> void:queue_command({"actor":actor,"kind":"promise","revision":"west","label":"One west exit"})))
		choices.append(option("REVISE / keep east exit; decline west",func() -> void:queue_command({"actor":actor,"kind":"promise","revision":"east","label":"One east exit"})))
	elif boss_id=="val" and boss_stage==1:
		var id: String=str(battle.party[actor].id)
		var line: String={"jules":"Jules: I'll miss deadlines. I still belong","imani":"Imani: Not every manager will love me","walt":"Walt: I work better with a team"}[id]
		choices.append(option(line,func() -> void:queue_command({"actor":actor,"kind":"connect","reject":id,"label":line})))
	elif boss_id=="val" and boss_stage==2:
		choices.append(option("REVISE / unreserve the left chairs",func() -> void:queue_command({"actor":actor,"kind":"promise","revision":"left","label":"Open the left passage"})))
		choices.append(option("REVISE / unreserve the right chairs",func() -> void:queue_command({"actor":actor,"kind":"promise","revision":"right","label":"Open the right passage"})))
	else:
		var line: String="Answer two ordinary stopping cues" if boss_id=="val" and boss_stage==3 else names[boss_id][1]
		choices.append(option(line,func() -> void:queue_command({"actor":actor,"kind":"promise","label":line})))
	if int(battle.openness)>=100 and release_ready():
		if boss_id=="val":
			choices.clear()
			choices.append(option("RELEASE / let every other future go",func() -> void:queue_command({"actor":actor,"kind":"release","ending":"release","label":"RELEASE the other futures"})))
			choices.append(option("REWRITE / one real offer, with hours",func() -> void:queue_command({"actor":actor,"kind":"release","ending":"rewrite","label":"REWRITE one real offer"})))
			choices.append(option("BREAK / walk out; fix the stage later",func() -> void:queue_command({"actor":actor,"kind":"release","ending":"break","label":"BREAK off the interview"})))
		else:choices.append(option("RELEASE / enough for tonight",func() -> void:queue_command({"actor":actor,"kind":"release"})))
	choices.append(option("Back",command_menu))
	var ending_now: bool=boss_id=="val" and int(battle.openness)>=100 and release_ready()
	open_menu(Mode.BATTLE,"Connect / this choice decides the ending" if ending_now else "Connect / choose a finite promise",choices)

func talent_menu() -> void:
	var options: Array = []
	if actor == 0:
		options.append(option("Hold the Light / 20 / cancel one hit", func() -> void: queue_command({"actor": actor, "kind": "shield", "label": "Hold the Light"})))
		if state.flags.get("imani_joined", false):
			options.append(option("Hear Me Out / together / 35 SYNC", func() -> void: queue_command({"actor": 0, "kind": "connect", "joint": "hearMeOut"})))
	elif actor == 1:
		options.append(option("Steady Refrain / 30 / heal or revive", func() -> void: target_menu("heal")))
		var quiet: bool = PartyGrowth.has_perk(state.flags, "earplugs")
		options.append(option("Half Time / %d / slow pattern clocks" % (20 if quiet else 30), func() -> void: queue_command({"actor": actor, "kind": "slow", "label": "Half Time", "discount": 10 if quiet else 0})))
	else:
		options.append(option("Lantern Ward / 25 / shelter pocket", func() -> void: queue_command({"actor": actor, "kind": "lantern", "label": "Lantern Ward"})))
		options.append(option("Windbreak / 20 / protect one ally", func() -> void: target_menu("windbreak")))
		options.append(option("Share the Warmth / 30 / heal 22 + guard", func() -> void: target_menu("warmth")))
	options.append(option("Back", command_menu))
	open_menu(Mode.BATTLE, "Talents / SYNC %s plus queued guards" % battle.sync, options)

func target_menu(kind: String, item: String = "") -> void:
	var options: Array = []
	for i: int in range(3):
		if i > 0 and not state.flags.get(ACTORS[i] + "_joined", false): continue
		options.append(option("%s %s/%s" % [battle.party[i].id, battle.party[i].hp, battle.party[i].max], func() -> void:
			var command: Dictionary = {"actor": actor, "kind": kind, "target": i}
			if kind in ["heal", "windbreak", "warmth"]: command.label = str({"heal":"Steady Refrain", "windbreak":"Windbreak", "warmth":"Share the Warmth"}[kind])
			if kind == "warmth" and PartyGrowth.has_perk(state.flags, "thermos_lid"): command.bonus = 12
			if not item.is_empty():
				command.item = item
			queue_command(command)))
	options.append(option("Back", command_menu))
	open_menu(Mode.BATTLE, "Choose ally / healing also revives", options)

func item_menu() -> void:
	open_menu(Mode.BATTLE, "Supplies / consumed on resolution", [option("Granola (%s) / 30 HP" % battle.inventory.granola, func() -> void: target_menu("item", "granola")), option("Cocoa (%s) / 20 HP all" % battle.inventory.cocoa, func() -> void: queue_command({"actor": actor, "kind": "item", "item": "cocoa"})), option("Thermos (%s) / 45 HP" % battle.inventory.thermos, func() -> void: target_menu("item", "thermos")), option("Back", command_menu)])

func release_ready() -> bool:
	if boss_id in NativeFinalEncounter.IDS:return bool(battle.get("final_ready",false)) and (boss_stage==3 if boss_id=="val" else boss_stage==2 and battle.get("revision","") in ["west","east"] if boss_id=="rook" else true)
	if boss_id in NativeChapterTwo.BOSSES:return bool(battle.get("campus_promise",false)) and boss_stage >= (2 if boss_id=="autocomplete" else 0)
	if boss_id == "claim": return ClaimNeeds.can_release(claim_needs)
	if boss_id == "walt": return bool(battle.get("lantern_kept", false))
	if boss_id == "encore": return boss_stage >= 2 and bool(battle.get("final_cue", false))
	return boss_id not in ["chip", "deion", "todd"] or boss_stage >= 2

func queue_command(command: Dictionary) -> void:
	var proposed: Array = plan.duplicate(true)
	proposed.append(command)
	var error: String = BattleRules.validate_plan(battle, proposed)
	if error.is_empty() and boss_id == "claim": error = ClaimNeeds.validate_plan(claim_needs, proposed)
	if command.kind == "release" and not release_ready(): error = "Complete the promised defense before RELEASE."
	if error == "Not enough projected SYNC.":
		var funded: Array = proposed.duplicate(true)
		for i: int in range(3):
			if int(battle.party[i].hp) > 0 and not proposed.any(func(c: Dictionary) -> bool: return int(c.actor) == i or i == 1 and c.has("joint")):
				funded.append({"actor": i, "kind": "guard"})
		if BattleRules.validate_plan(battle, funded).is_empty():
			error = ""
			hint = "This talent needs a later GUARD. Review before commit."
	if not error.is_empty():
		hint = error
		battle_error = error
		ui_dirty = true
		audio.effect("back")
		return
	plan.append(command.duplicate(true))
	next_actor()

func next_actor() -> void:
	if not battle.party.any(func(member: Dictionary) -> bool: return int(member.hp) > 0):
		battle.outcome = "defeat"; defeat_menu(); return
	actor = -1
	for i: int in range(3):
		if int(battle.party[i].hp) > 0 and not plan.any(func(c: Dictionary) -> bool: return int(c.actor) == i or i == 1 and c.has("joint")):
			actor = i
			break
	if actor < 0:
		open_menu(Mode.BATTLE, "Review party plan", [option("Commit turn", commit_plan), option("Undo last command", undo_command), option("Clear plan", func() -> void:
			plan.clear()
			next_actor())])
	else:
		command_menu()

func undo_command() -> void:
	if not plan.is_empty():
		actor = int(plan.pop_back().actor)
		if int(battle.party[actor].hp) > 0:
			command_menu()
			return
	next_actor()

func commit_plan() -> void:
	var error: String = BattleRules.validate_plan(battle, plan)
	if error.is_empty() and boss_id == "claim": error = ClaimNeeds.validate_plan(claim_needs, plan)
	if plan.any(func(c: Dictionary) -> bool: return c.kind == "release") and not release_ready(): error = "Complete the promised defense before RELEASE."
	if not error.is_empty():
		hint = error
		battle_error = error
		ui_dirty = true
		return
	timing_index = 0
	timing_ticks = 0
	if plan.any(func(c: Dictionary) -> bool: return c.kind == "strike") and not state.settings.autoTiming:
		mode = Mode.TIMING
		ui_dirty = true
	else:
		for command: Dictionary in plan:
			command.timing = 1.0 / 3.0
		resolve_plan()

func finish_timing(missed: bool) -> void:
	var strikes: Array = plan.filter(func(c: Dictionary) -> bool: return c.kind == "strike")
	strikes[timing_index].timing = -1.0 if missed or timing_ticks > 54 else 1.0 - absf(float(timing_ticks) / 54.0 - 0.5) * (1.2 if int(strikes[timing_index].actor) == 0 and PartyGrowth.has_perk(state.flags, "moms_keychain") else 2.0)
	audio.combat("perfect" if float(strikes[timing_index].timing) >= 0.85 else "pick")
	timing_index += 1
	timing_ticks = 0
	if timing_index >= strikes.size():
		resolve_plan()
	input_lock = 2

func resolve_plan() -> void:
	pending_battle = BattleRules.resolve_plan(battle, plan)
	if boss_id in NativeFinalEncounter.IDS:NativeFinalCampaign.decorate(self,pending_battle,plan)
	if boss_id == "claim": pending_battle.openness = 100 if ClaimNeeds.can_release(claim_needs) else 55 if bool(claim_needs.tagDelivered) else 0
	for i: int in range(1, 3):
		if not state.flags.get(ACTORS[i] + "_joined", false): pending_battle.party[i].hp = 0
	boundary_active = plan.any(func(c: Dictionary) -> bool: return bool(c.get("boundary", false)))
	if boundary_active:
		pending_battle.promise = true
		pending_battle.openness = mini(100, int(pending_battle.openness) + (0 if boss_id == "claim" else 15))
	mode = Mode.RESOLVE; resolution_ticks = 0; resolution_index = 0
	shown_enemy_hp = int(battle.hp)
	present_action(); ui_dirty = true

func complete_resolution() -> void:
	var asked: bool = plan.any(func(c: Dictionary) -> bool: return c.kind == "connect" and not c.has("reject") and not c.has("joint"))
	battle = pending_battle; pending_battle = {}; shown_enemy_hp = int(battle.hp)
	foe.modulate = Color.WHITE
	plan.clear()
	if boss_id=="val" and battle.outcome=="forceful" and boss_stage<3:NativeFinalCampaign.force_advance(self);return
	if battle.outcome != "active": finish_battle(); return
	rest_party_poses()
	# Asking a boss something gets an answer (once a fight) before its next attack.
	var reply: Array = NativeBossIntro.answer(boss_id) if asked and not bool(battle.get("answered", false)) else []
	if not reply.is_empty():
		battle.answered = true
		dialogue([reply], start_phase); return
	start_phase()

func rest_party_poses() -> void:
	for i: int in range(battle_sprites.size()):
		battle_sprites[i].modulate = Color.WHITE
		battle_sprites[i].play("idle" if int(battle.party[i].hp) > 0 else "down")

func start_phase() -> void:
	reset_pointer_controls()
	graze_sync = 0
	if boss_id=="val":boss_stage=int(battle.val_stage)
	elif boss_id=="rook":boss_stage=int(battle.rook_stage)
	elif boss_id == "claim":
		boss_stage = ClaimNeeds.combat_phase(claim_needs, int(battle.hp), bool(battle.promise))
		if battle.hp <= 70: peak_music = true
	elif boss_id == "encore" or boss_id=="autocomplete":
		boss_stage = mini(2, boss_rounds)
	elif boss_id in ["chip", "deion", "todd"]:
		boss_stage = BossDirector.next_phase(boss_stage, int(battle.hp), int(BossDirector.profile(boss_id).maxHp), mini(2, boss_rounds))
	else: boss_stage = mini(1, boss_rounds)
	if boss_id not in ["", "pinpal", "jakerson"]: audio.boss_phase(2 if boss_id == "claim" and peak_music else boss_stage)
	audio.set_music_speed(float(state.settings.assist) * (0.8 if battle.slow else 1.0))
	bar_marker = audio.reserve_bar(2.0)
	var tick: int = int(bar_marker.get("music_tick", 0))
	pattern = NativeFinalEncounter.create(boss_id,int(checkpoint.seed)+int(battle.turn),boss_stage,tick) if boss_id in NativeFinalEncounter.IDS else NativeCampusEncounter.create(boss_id,int(checkpoint.seed)+int(battle.turn),boss_stage,tick) if boss_id in NativeChapterTwo.BOSSES else NativeNewEncounter.create(boss_id, int(checkpoint.seed) + int(battle.turn), boss_stage, tick) if boss_id in NativeCampaign.EXPANSION_BOSSES else EncounterDirector.create("flyer" if boss_id.is_empty() else boss_id, int(checkpoint.seed) + int(battle.turn), boss_stage, tick)
	if DodgeBox.handles(boss_id): pattern = DodgeBox.create(boss_id, int(checkpoint.seed) + int(battle.turn), boss_stage, tick, boss_rounds, DodgeBox.beat_ticks_for(float(audio.music_metadata().get("bpm", 120.0))))
	if pattern.get("engine", "") == "box": pattern.references = LinkedOut.accepted_ids(state.flags)
	if boss_id in NativeFinalEncounter.IDS:
		pattern.revision=battle.get("val_revision","") if boss_id=="val" else battle.get("revision","");pattern.rejected=battle.get("rejected",[]).duplicate()
	pattern.wardTicks = (270 if PartyGrowth.has_perk(state.flags, "lantern_wick") else 180) if battle.get("ward", false) else 0
	pattern.wardPocket = Rect2(104, 82, 48, 34)
	pattern.boundary = boundary_active
	# A limit set with CONNECT makes the boss ease off for this attack.
	battle.eased = boundary_active and not retreating
	mode = Mode.TELEGRAPH; phase_ticks = 60
	# Hits go around the party, starting with a different person each round.
	target = posmod(int(battle.turn), 3)
	next_target(false)
	dodge_goal = Vector2.INF; beat_defend = false
	foe.play("interact_down" if boss_id in ["chip", "deion", "todd", "walt", "encore", "errata", "autocomplete", "eric", "cone", "chad", "rook", "val", "jakerson", "jakerson_final"] else "tell")
	claim_art.set_pose("tell"); pin_art.set_pose("tell")
	NativeBattleJuice.windup(claim_art if boss_id == "claim" else pin_art if boss_id == "pinpal" else foe)
	audio.combat("whistle" if boss_id == "deion" else "stamp" if boss_id == "todd" else "warning")
	ui_dirty = true

func dodge_tick() -> void:
	if resume_ticks > 0:
		resume_ticks -= 1
		if resume_ticks == 0: audio.set_paused(false)
		ui_dirty = true
		return
	var axis: Vector2 = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if axis.length_squared() > 0: dodge_goal = Vector2.INF
	elif dodge_goal != Vector2.INF and boss_id not in ["chip", "deion"]:
		var cursor: Vector2 = Vector2(float(pattern.cursor.x), float(pattern.cursor.y))
		axis = (dodge_goal - cursor).normalized() if cursor.distance_to(dodge_goal) > 2 else Vector2.ZERO
	if pointer_hop != 0: axis.x = pointer_hop
	pointer_hop = 0
	var cues_before: int = int(pattern.get("cuesReached", 0))
	var raised_before: int = int(pattern.get("lanternRaised", 0))
	var gusts_before: int = int(pattern.get("gustsKept", 0))
	var warn_before: int = pattern.telegraphs.size()
	var ward_remaining: int = int(pattern.get("wardTicks", 0))
	var ward_clock: int = int(pattern.clock)
	if pattern.get("engine", "") == "box": pattern = DodgeBox.step(pattern, axis, Input.is_action_pressed("run") or pointer_duck, float(state.settings.assist), bool(battle.slow), bool(battle.promise), beat_defend)
	else: pattern = NativeFinalEncounter.step(pattern,axis,Input.is_action_pressed("run") or pointer_duck,float(state.settings.assist),bool(battle.slow),bool(battle.promise),beat_defend) if boss_id in NativeFinalEncounter.IDS else NativeCampusEncounter.step(pattern,axis,Input.is_action_pressed("run") or pointer_duck,float(state.settings.assist),bool(battle.slow),bool(battle.promise),beat_defend) if boss_id in NativeChapterTwo.BOSSES else NativeNewEncounter.step(pattern, axis, Input.is_action_pressed("run") or pointer_duck, float(state.settings.assist), bool(battle.slow), bool(battle.promise), beat_defend) if boss_id in NativeCampaign.EXPANSION_BOSSES else EncounterDirector.step(pattern, axis, Input.is_action_pressed("run") or pointer_duck, float(state.settings.assist), bool(battle.slow), bool(battle.promise), beat_defend)
	if boss_id not in NativeCampaign.EXPANSION_BOSSES and boss_id not in NativeChapterTwo.BOSSES and boss_id not in NativeFinalEncounter.IDS and pattern.get("engine", "") != "box":
		pattern.wardTicks = maxi(0, ward_remaining - (int(pattern.clock) - ward_clock))
		if ward_remaining > 0 and pattern.wardPocket.has_point(Vector2(pattern.cursor.x, pattern.cursor.y)): pattern.hit = false
	if boss_id in NativeCampaign.EXPANSION_BOSSES or boss_id in NativeChapterTwo.BOSSES or boss_id in NativeFinalEncounter.IDS or pattern.get("engine", "") == "box":
		if pattern.get("objectiveChanged",false):audio.combat("perfect")
		if pattern.telegraphs.size() > warn_before: audio.combat("warning")
		if int(pattern.get("cuesReached", 0)) > cues_before or int(pattern.get("gustsKept", 0)) > gusts_before: audio.combat("perfect")
		elif int(pattern.get("lanternRaised", 0)) > raised_before: audio.combat("shield")
	if boss_id == "claim" and boss_stage == 1 and pattern.get("carryTag", false) and int(pattern.clock) > 180 and not peak_music:
		peak_music = true
		audio.boss_phase(2)
	beat_defend = false
	# Guitar pick keepsake: Imani's close dodges on the beat count double.
	var on_beat: bool = PartyGrowth.has_perk(state.flags, "guitar_pick") and pattern.has("beatTicks") and absi(posmod(int(pattern.clock) + int(pattern.get("musicBase", 0)) + 6, int(pattern.beatTicks)) - 6) <= 6
	var graze: int = mini((4 if on_beat else 2) * int(pattern.grazeDelta), (20 if PartyGrowth.has_perk(state.flags, "guitar_pick") else 12) - graze_sync)
	if graze > 0:
		# Close dodges build SYNC: +2 each, at most +12 per defense.
		graze_sync += graze
		battle.sync = mini(100, int(battle.sync) + graze)
		var spark: Vector2 = Vector2(192, 166) + Vector2(float(pattern.cursor.x), float(pattern.cursor.y))
		vfx.play("graze", spark, spark)
		audio.combat("pick")
	if pattern.hit and bool(battle.get("pass_ready", false)):
		# Bus pass keepsake: the first hit of each fight is waved through.
		battle.pass_ready = false; pattern.hit = false
		vfx.play("guard", battle_sprites[target].position, battle_sprites[target].position - Vector2(0, 38), 0)
		audio.combat("guard")
	if pattern.hit:
		var hp: int = int(battle.party[target].hp)
		battle = BattleRules.hit(battle, target, BattleRules.enemy_damage(boss_id, battle, bool(state.settings.damageAssist)))
		var lost: int = hp - int(battle.party[target].hp)
		vfx.play("guard" if lost == 0 else "hit", battle_sprites[target].position, battle_sprites[target].position - Vector2(0, 38), lost)
		audio.combat("guard" if lost == 0 else "hit")
		battle_sprites[target].modulate = Color("df807b")
		battle_sprites[target].play("hit" if int(battle.party[target].hp) > 0 else "down")
		if lost > 0:
			NativeBattleJuice.flinch(battle_sprites[target], Vector2.LEFT, lost); NativeBattleJuice.flash(battle_sprites[target], 6)
			NativeBattleJuice.kick([battle_scenery, foe, claim_art, pin_art] + battle_sprites, 1.0 if lost < 12 else 2.0, 8)
		if int(battle.party[target].hp) <= 0: pattern.invulnerability = 60
		if battle.outcome == "defeat": defeat_menu(); return
		next_target(true)
	for sprite: AnimatedSprite2D in battle_sprites: sprite.modulate = sprite.modulate.lerp(Color.WHITE, 0.16)
	if retreating and int(pattern.clock) >= 180:
		merge_party(battle.party); state.inventory = battle.inventory.duplicate(true)
		if boss_id=="val":state.flags.val_checkpoint=""
		enter_room(str(state.room), Vector2(float(checkpoint.x), float(checkpoint.y)))
		grace_ticks = 180; message("Stepped away. No victory recovery."); return
	if pattern.done:
		boss_rounds += 1
		var success: bool = bool(pattern.promiseComplete)
		var final_advanced: bool=NativeFinalCampaign.record_defense(self,success,bool(battle.promise)) if boss_id in NativeFinalEncounter.IDS else false
		if battle.promise and success:
			if boss_id in NativeChapterTwo.BOSSES and (boss_id!="autocomplete" or boss_stage==2):battle.campus_promise=true
			if boss_id == "walt": battle.lantern_kept = true
			if boss_id == "encore" and boss_stage == 2: battle.final_cue = true
		last_promise_result = ("Promise kept\n" if success else "Promise unfinished\n") + live_promise_progress() if battle.promise else ""
		pointer_duck = false; pointer_hop = 0
		if boss_id == "claim":
			claim_needs = ClaimNeeds.record_defense(claim_needs, pattern, bool(battle.promise), boundary_active)
			if battle.promise and success:
				battle.openness = 100 if ClaimNeeds.can_release(claim_needs) else 55 if bool(claim_needs.tagDelivered) else 0
				battle.promise = false
			else: battle.promise = false
		else: battle = BattleRules.complete_promise(battle, success)
		if boss_id == "claim": boss_stage = ClaimNeeds.combat_phase(claim_needs, int(battle.hp))
		hint = last_promise_result if not last_promise_result.is_empty() else "Your next turn."
		audio.set_music_speed(1.0)
		rest_party_poses()
		actor = 0
		while actor < 3 and int(battle.party[actor].hp) <= 0: actor += 1
		if final_advanced:NativeFinalCampaign.checkpoint(self);NativeFinalCampaign.phase_dialogue(self)
		elif boss_id == "jakerson" and battle.outcome == "active":NativeJakerson.coach(self)
		else:command_menu()
	ui_dirty = true

## Moves the hit target to the next conscious party member (or keeps it, if it is still up and
## advance is false).
func next_target(advance: bool) -> void:
	if advance: target = (target + 1) % 3
	for _i: int in range(3):
		if int(battle.party[target].hp) > 0: return
		target = (target + 1) % 3

func retreat() -> void:
	reset_pointer_controls()
	retreating = true
	plan.clear()
	battle.guards = [false, false, false]
	battle.shield = false
	battle.brace = false
	battle.ward = false; battle.windbreak_target = -1
	battle.slow = false
	battle.promise = false
	hint = "RETREAT: survive three seconds, then step away."
	start_phase()

func defeat_menu() -> void:
	open_menu(Mode.RESULT, "Everyone is down / No permanent loss", [option("Retry / restore pre-battle supplies", func() -> void:
		var settings: Dictionary = state.settings
		state = checkpoint.duplicate(true)
		state.settings = settings
		begin_battle()), option("Return to checkpoint", func() -> void:
		var settings: Dictionary = state.settings
		state = checkpoint.duplicate(true)
		state.settings = settings
		enter_room(str(state.room), Vector2(float(state.x), float(state.y)), false)), option("Settings", func() -> void:
		open_pause()
		settings_menu())])
	audio.effect("defeat")

func finish_battle() -> void:
	if NativeRandomFights.is_fight(boss_id): NativeRandomFights.finish(self); return
	reset_pointer_controls()
	var resolved_id: String = "flyer" if boss_id.is_empty() else boss_id
	merge_party(BattleRules.recover(battle.party))
	state.inventory = battle.inventory.duplicate(true)
	state.flags[resolved_id + "_resolution"] = str(battle.outcome)
	state.flags[resolved_id + "_rehearsal"] = str(battle.outcome)
	state.flags.aftermath_pending = resolved_id
	if resolved_id=="val":state.flags.ending=str(battle.get("ending","break"));state.flags.val_checkpoint=""
	if resolved_id == "claim":
		state.flags.opening_finished = true; state.flags.pip_joined = true
	persist()
	var peaceful: bool = battle.outcome == "peaceful"
	vfx.play("promise" if peaceful else "dissolve", foe.position, foe.position - Vector2(0, 35))
	claim_art.set_pose("resolved" if peaceful else "down"); pin_art.set_pose("resolved" if peaceful else "down")
	audio.resolve_battle(peaceful)
	if qa and boss_id == "claim" and qa_record != null: qa_finish_record()
	open_menu(Mode.RESULT, "A promise kept" if peaceful else "The way is clear", [option("Continue", func() -> void: show_aftermath(resolved_id))])

func show_aftermath(resolved_id: String) -> void:
	if NativeSideBosses.is_boss(resolved_id): NativeSideBosses.aftermath(self, resolved_id); return
	if resolved_id in NativeFinalCampaign.AFTERMATHS:NativeFinalCampaign.aftermath(self,resolved_id);return
	if resolved_id == "jakerson": NativeJakerson.after_spar(self); return
	if resolved_id == "jakerson_final": NativeJakerson.after_final(self); return
	if resolved_id=="todd":NativeChapterThree.aftermath(self);return
	if resolved_id in NativeChapterTwo.AFTERMATHS:
		NativeChapterTwo.aftermath(self,resolved_id);return
	if resolved_id in NativeCampaign.EXPANSION_BOSSES:
		NativeCampaign.aftermath(self, resolved_id)
		return
	var peaceful: bool = str(state.flags.get(resolved_id + "_resolution", "")) == "peaceful"
	boss_id = ""
	enter_room(str(state.room), Vector2(float(state.x), float(state.y)), false)
	var aftermath: Dictionary = {"flyer": [["Flyerer", "One reader. One page. We can close now.", "warm"], ["Imani", "We did not promise forever. And it worked.", "warm"], ["Imani", "Now the atrium booth. I want to know why it used my voice.", "concern"]] if peaceful else [["Imani", "The stand's bent. I've left a note by the hinge.", "concern"], ["Jules", "Then we check that voice in the atrium.", "neutral"]], "pinpal": [["Pin Pal", "RETURN RECEIVED. THANK YOU FOR PLAYING.", "warm"]] if peaceful else [["Walt", "The housing's cracked. Leave it switched off.", "concern"], ["Jules", "I'll put the ball on the rack.", "neutral"]], "claim": [["CLAIM", "ONE RETURN. ONE NOTE. THE REST CAN WAIT.", "warm"], ["Pip", "I am coming with you. I can point. That is a surprisingly useful glove skill.", "warm"], ["Jules", "The booth has a maker. We find them, then find a way home.", "warm"], ["Mags", "Mags, from the cart out front. I heard all of that. Leaving something unfinished on purpose is harder than it looks.", "warm"]] if peaceful else [["Mags", "Mags, from the cart out front. The ticket spool broke; I'll sort it. Leave the glove with me?", "concern"], ["Pip", "Actually, I would like to come with them.", "warm"], ["Jules", "Then we find who made that booth. Together.", "warm"]]}
	dialogue(aftermath.get(resolved_id, [[resolved_id.capitalize(), "Good practice. Remember to rest.", "warm"]]), func() -> void:
		state.flags.aftermath_pending = ""
		persist()
		resume_world())

func style_panel(border: Color = LINE) -> StyleBoxFlat:
	# Quiet frames: a dim line by default, amber only where the eye should go.
	var style: StyleBoxFlat = StyleBoxFlat.new()
	style.bg_color = INK
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(3)
	style.anti_aliasing = false
	return style

func panel(rect: Rect2, border: Color = LINE) -> Panel:
	var node: Panel = Panel.new()
	node.position = rect.position
	node.size = rect.size
	node.add_theme_stylebox_override("panel", style_panel(border))
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(node)
	text_nodes.append(node)
	return node

func fill(rect: Rect2, color: Color) -> ColorRect:
	var node: ColorRect = ColorRect.new()
	node.position = rect.position; node.size = rect.size; node.color = color
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(node); text_nodes.append(node)
	return node

func meter(rect: Rect2, fraction: float, color: Color) -> void:
	fill(rect, TRACK)
	var width: float = roundf(rect.size.x * clampf(fraction, 0.0, 1.0))
	if width > 0: fill(Rect2(rect.position, Vector2(width, rect.size.y)), color)

func text_width(text: String, size_px: int = 12) -> float:
	return text.length() * GLYPH * size_px / 12.0

func keycap(key: String, at: Vector2) -> float:
	var width: float = maxf(16.0, text_width(key) + 8.0)
	panel(Rect2(at, Vector2(width, 16)), CREAM)
	var cap: Label = label(key, Rect2(at + Vector2(0, 1), Vector2(width, 15)), 12, CREAM)
	cap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return width

func caret(at: Vector2, color: Color) -> void:
	for row: int in range(4): fill(Rect2(at + Vector2(row, row), Vector2(7 - row * 2, 1)), color)

func label(text: String, rect: Rect2, size_px: int = 12, color: Color = CREAM) -> Label:
	var node: Label = Label.new()
	var clean: String = text.replace("Â·", " / ").replace("â€”", "-").replace("â†’", ">").replace("â€™", "'")
	clean = key_words(clean)
	var max_chars: int = maxi(6, floori(rect.size.x / (GLYPH * size_px / 12.0)))
	var wrapped: Array[String] = []
	for paragraph: String in clean.split("\n"):
		var line: String = ""
		for word: String in paragraph.split(" "):
			if line.length() + word.length() + 1 > max_chars and not line.is_empty():
				wrapped.append(line)
				line = ""
			line += (" " if not line.is_empty() else "") + word
		wrapped.append(line)
	# Never draw past the box: text taller than the box shows a page at a time, turning every
	# few seconds, with page dots in the box's bottom-right corner.
	var room: int = maxi(1, floori((rect.size.y + 2.0) / (font.get_height(size_px) + 2.0)))
	var pages: int = ceili(float(wrapped.size()) / room)
	var page: int = 0
	if pages > 1:
		paging_labels = true
		page = (intro_ticks / LABEL_PAGE_TICKS) % pages
		var per_page: int = ceili(float(wrapped.size()) / pages)
		wrapped = wrapped.slice(page * per_page, page * per_page + per_page)
	node.text = "\n".join(wrapped)
	node.max_lines_visible = room
	node.position = rect.position
	node.size = rect.size
	node.add_theme_font_override("font", font)
	node.add_theme_font_size_override("font_size", size_px)
	node.add_theme_color_override("font_color", color)
	node.add_theme_constant_override("line_spacing", 2)
	node.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	node.clip_text = true
	node.clip_contents = true
	# Set bounds after enabling wrap; Label's earlier unwrapped minimum is wider.
	node.size = rect.size
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(node)
	text_nodes.append(node)
	if pages > 1 and room > 1:
		for dot: int in range(pages):
			fill(Rect2(rect.end.x - 4 - (pages - 1 - dot) * 5, rect.end.y - 2, 3, 2), AMBER if dot == page else LINE)
	return node

## Prompts written with a keyboard key ("up or Z jumps") read the same on any device.
func key_words(text: String) -> String:
	if not text.contains("Z"): return text
	var key := RegEx.new()
	key.compile("(?<![A-Za-z0-9'])Z(?![A-Za-z0-9'])")
	return key.sub(text, "confirm", true)

func right_label(text: String, rect: Rect2, color: Color = CREAM) -> Label:
	var node: Label = label(text, rect, 12, color)
	node.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	return node

func render_ui() -> void:
	for node: Control in text_nodes: node.queue_free()
	text_nodes.clear(); buttons.clear(); battle_help = null
	paging_labels = false
	menu_back_rect = Rect2()
	if is_instance_valid(overlay): overlay.update_state()
	var stack: float = 40.0
	if mode == Mode.WORLD and world.visible:
		# One compact card: where you are, then what to do next.
		var place: String = str(rooms[state.room].name)
		var goal: String = objective()
		var width: float = clampf(maxf(text_width(place) + 24, text_width(goal) + 46), 180, 470)
		panel(Rect2(12, 10, width, 40))
		label(place, Rect2(22, 13, width - 20, 16), 12, MINT)
		fill(Rect2(23, 35, 4, 4), AMBER)
		label(goal, Rect2(32, 30, width - 40, 16), 12, CREAM)
		stack = 56
	elif mode == Mode.MENU and world.visible and caption.begins_with("Which objective"):
		panel(Rect2(12, stack, 616, 24))
		label(objective(), Rect2(24, stack + 3, 592, 20), 12, AMBER)
		stack += 28
	if mode == Mode.WORLD:
		var tutorial_hint: String=NativeJakerson.hint(self)
		# One line of guidance at a time: the standing hint steps aside while a bark is showing.
		if not tutorial_hint.is_empty() and notice_ticks <= 0:
			panel(Rect2(12,stack,470,40));label(tutorial_hint,Rect2(22,stack+4,450,34),12,MINT)
			stack += 44
		var object: Dictionary = nearest_object()
		if not object.is_empty():
			# A small prompt pill near the player's eyeline instead of a full-width bar.
			var name: String = object_label(object)
			var key: String = binding_label("confirm").get_slice(" / ", 0)
			var width: float = text_width(key) + text_width(name) + 40
			var left: float = roundf(320 - width / 2)
			panel(Rect2(left, 322, width, 26))
			var cap: float = keycap(key, Vector2(left + 6, 327))
			label(name, Rect2(left + cap + 14, 328, width - cap - 18, 16), 12, CREAM)
	elif mode == Mode.TITLE:
		label("AFTER", Rect2(27, 38, 260, 58), 36, CREAM)
		label("HOURS", Rect2(27, 88, 260, 58), 36, AMBER)
		label("C O L L E G E  T A L E", Rect2(29, 154, 265, 24), 12)
		label("0.7.4 / CAST EVENING", Rect2(420, 332, 196, 18), 12, MINT)
		label("One small promise.\nOne very long evening.", Rect2(29, 181, 265, 46), 12, MINT)
		panel(Rect2(20, 228, 252, 122))
		render_options(Rect2(26, 234, 240, 115))
	elif mode == Mode.INTRO:
		var arrival: bool = intro_index == intro_arrival
		var top: float = 12 if arrival else 211
		panel(Rect2(28, top, 584, 128))
		label(str(intro_cards[intro_index][0]), Rect2(44, top + 14, 552, 28), 18, AMBER)
		var text: String = str(intro_cards[intro_index][1])
		label(text.left(mini(text.length(), intro_ticks / 2)), Rect2(44, top + 53, 552, 58), 12)
		var advance: Button = Button.new()
		advance.text = binding_label("confirm") + (" / begin" if intro_index == intro_cards.size() - 1 else " / continue")
		advance.position = Vector2(390, top + 102); advance.size = Vector2(210, 23)
		advance.add_theme_font_override("font", font); advance.add_theme_font_size_override("font_size", 12)
		advance.add_theme_color_override("font_color", MINT)
		advance.add_theme_color_override("font_hover_color", Color.WHITE)
		advance.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		advance.focus_mode = Control.FOCUS_NONE
		advance.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
		advance.pressed.connect(advance_intro)
		ui.add_child(advance); text_nodes.append(advance)
		var skip: Button = Button.new()
		skip.text = binding_label("cancel") + (" / skip move-in day" if intro_arrival < 0 else " / skip arrival")
		skip.position = Vector2(36, top + 102); skip.size = Vector2(288, 23)
		skip.add_theme_font_override("font", font); skip.add_theme_font_size_override("font_size", 12)
		skip.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		skip.focus_mode = Control.FOCUS_NONE; skip.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
		skip.pressed.connect(func() -> void: finish_arrival(true))
		ui.add_child(skip); text_nodes.append(skip)
	elif mode == Mode.DIALOGUE:
		var large: bool = state.settings.large
		var top: float = 38.0 if dialogue_top else 130.0 if large else 214.0
		var height: float = 220 if large else 136
		panel(Rect2(12, top, 616, height))
		var line: Array = dialogue_lines[line_index]
		var speaker: String = str(line[0])
		var mood: String = str(line[2]) if line.size() > 2 else "neutral"
		var talking: bool = reveal < str(line[1]).length()
		var face: int = 2 if mood == "concern" else 3 if mood == "warm" else 0
		# A speaker with no portrait (a voice, a notice) gets the whole box for text, not an empty frame.
		var iconic: Texture2D = NativeTalkArt.icon(speaker, talking and intro_ticks % 20 < 12)
		if NativeCastArt.portrait(speaker, face) == null and NativeTalkArt.portrait(speaker, face) == null and iconic == null:
			var bare_tab: float = text_width(speaker) + 16
			fill(Rect2(22, top - 8, bare_tab, 17), AMBER)
			label(speaker, Rect2(30, top - 7, bare_tab - 8, 16), 12, INK)
			label(str(line[1]).left(floori(reveal)), Rect2(30, top + 18, 582, height - 34), 24 if large else 12)
			if not talking: caret(Vector2(606, top + height - 14), AMBER)
			return
		# While a line types out the mouth flaps (closed on punctuation); portraits without drawn
		# open mouths fall back to swapping in the talking face.
		var open: bool = talking and intro_ticks % 10 < 5 and not str(line[1]).substr(maxi(0, floori(reveal) - 1), 1) in [".", ",", "!", "?"]
		var mouth: Texture2D = NativeTalkArt.portrait(speaker, face) if open else null
		if mouth == null and talking and mood != "concern" and intro_ticks % 16 < 8 and NativeTalkArt.portrait(speaker, face) == null: face = 1
		if iconic != null: portrait_texture(iconic, Rect2(16, top + 4, 128, 128))
		elif mouth != null: portrait_texture(mouth, Rect2(16, top + 4, 128, 128))
		else: portrait(speaker, face, Rect2(16, top + 4, 128, 128))
		fill(Rect2(150, top + 10, 1, height - 20), LINE)
		# Name tab sits on the frame, so the speaker reads before the line does.
		var tab: float = text_width(speaker) + 16
		fill(Rect2(158, top - 8, tab, 17), AMBER)
		label(speaker, Rect2(166, top - 7, tab - 8, 16), 12, INK)
		label(str(line[1]).left(floori(reveal)), Rect2(164, top + 18, 448, height - 34), 24 if large else 12)
		if not talking: caret(Vector2(606, top + height - 14), AMBER)
	elif mode in [Mode.MENU, Mode.PAUSE]:
		if ending_ticks >= 0 and not pause_context and mode == Mode.MENU and caption.begins_with("The end"):
			render_ending()
		elif pause_context and pause_mode == Mode.WORLD and (caption == "Paused" or caption.begins_with("Party") or party_caption(caption)):
			render_pause_screen()
		else:
			# A framed box sized to its options. Story choices sit where the dialogue box was (bottom,
			# or top when the speakers stand low); other menus hang from the top.
			var quiz: float = 46.0 if stack > 40.0 else 0.0
			var has_back: bool = mode == Mode.MENU and menu_options.any(func(choice: Dictionary) -> bool: return choice.label == "Back")
			var count: int = maxi(1, menu_options.size() - (1 if has_back else 0))
			var caption_lines: int = clampi(ceili(text_width(caption) / 464.0), 1, 2)
			var head: float = 20.0 + 18.0 * caption_lines
			var back_room: float = 26.0 if has_back else 0.0
			var rows: int = clampi(count, 1, floori((318.0 - quiz - head - 10.0 - back_room) / 23.0))
			var height: float = head + rows * 23.0 + 10.0 + back_room
			var top: float = 22.0 + quiz
			if world.visible and not pause_context and mode == Mode.MENU:
				top = maxf(22.0 + quiz, 38.0 if dialogue_top else 350.0 - height)
			panel(Rect2(70, top, 500, height))
			label(caption, Rect2(88, top + 10, 464, 18.0 * caption_lines), 12, AMBER)
			fill(Rect2(88, top + head - 5, 464, 1), LINE)
			# Back is drawn by the overlay button in the row after the options.
			render_options(Rect2(88, top + head + 2, 464, (rows + (1 if has_back else 0)) * 23.0))
			if has_back: menu_back_rect = Rect2(88, top + head + 2 + rows * 23.0, 464, 23)
	elif mode in [Mode.BATTLE, Mode.TIMING, Mode.TELEGRAPH, Mode.DODGE, Mode.RESOLVE, Mode.RESULT, Mode.BANNER]:
		render_battle_ui()
	if notice_ticks > 0 and mode == Mode.WORLD:
		var width: float = minf(text_width(notice) + 28, 616)
		var lines: int = 1 if text_width(notice) <= 588 else 2
		panel(Rect2(12, stack + 2, width, 12 + 18 * lines), AMBER)
		label(notice, Rect2(26, stack + 8, width - 20, 18 * lines), 12, AMBER)
	elif notice_ticks > 0 and mode == Mode.TITLE:
		panel(Rect2(312, 270, 304, 50), AMBER)
		label(notice, Rect2(322, 276, 286, 40), 12, AMBER)

func party_caption(text: String) -> bool:
	# cycle_keepsake writes "<Name> / <keepsake>" while the party list is open.
	for member: String in ACTORS:
		if text.begins_with(member.capitalize() + " /") or text.begins_with(member.capitalize() + " has no"): return true
	return false

func render_pause_screen() -> void:
	fill(Rect2(0, 0, 640, 360), Color(INK, 0.55))
	var party: bool = not caption == "Paused"
	panel(Rect2(16, 16, 196, 328))
	label("PARTY" if party else "PAUSED", Rect2(30, 26, 170, 16), 12, AMBER)
	fill(Rect2(30, 46, 168, 1), LINE)
	render_options(Rect2(22, 54, 184, 200))
	if party:
		label(caption if party_caption(caption) else "Pick someone to swap their keepsake.", Rect2(30, 232, 170, 72), 12, MINT)
	var row: int = 0
	for i: int in range(3):
		var member: Dictionary = state.party[i]
		var id: String = str(member.id)
		if i > 0 and not state.flags.get(id + "_joined", false): continue
		var top: float = 16 + row * 80
		var chosen: bool = party and selection == row
		panel(Rect2(224, top, 400, 72), AMBER if chosen else LINE)
		label(id.capitalize(), Rect2(238, top + 9, 140, 16), 12, AMBER if chosen else CREAM)
		right_label("HP %d/%d" % [int(member.hp), int(member.max)], Rect2(450, top + 9, 160, 16))
		meter(Rect2(238, top + 30, 372, 5), float(member.hp) / maxf(1.0, float(member.max)), AMBER)
		label("POW %d   DEF %d" % [int(member.power), int(member.defence)], Rect2(238, top + 46, 160, 16), 12, MINT)
		var worn: String = PartyGrowth.equipped(state.flags, id)
		right_label(PartyGrowth.describe(worn) if not worn.is_empty() else "No keepsake", Rect2(370, top + 46, 240, 16), CREAM if not worn.is_empty() else MUTED)
		row += 1
	var found: int = PartyGrowth.KEEPSAKES.keys().filter(func(id: String) -> bool: return PartyGrowth.found(state.flags, id)).size()
	panel(Rect2(224, 264, 400, 80))
	label(str(rooms[state.room].name), Rect2(238, 273, 372, 16), 12, MINT)
	label(objective(), Rect2(238, 292, 372, 34), 12, CREAM)
	right_label("Keepsakes %d/%d" % [found, PartyGrowth.KEEPSAKES.size()], Rect2(410, 273, 200, 16), MUTED)

## The closing card: the scene fades to dark, the title and an end line fade in, then the choices
## (keep exploring / title) appear underneath in a small framed list.
func render_ending() -> void:
	var fade: float = clampf(ending_ticks / 80.0, 0.0, 1.0)
	fill(Rect2(0, 0, 640, 360), Color(0.04, 0.05, 0.09, fade))
	if ending_ticks < 50: return
	var shown: float = clampf((ending_ticks - 50) / 60.0, 0.0, 1.0)
	var tint: Color = Color(1, 1, 1, shown)
	var title: Label = label("AFTER HOURS", Rect2(120, 70, 400, 50), 36, Color(CREAM, shown)); title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var sub: Label = label("C O L L E G E   T A L E", Rect2(120, 122, 400, 20), 12, Color(AMBER, shown)); sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	fill(Rect2(220, 152, 200, 1), Color(LINE, shown))
	var line: Label = label("THE END", Rect2(120, 164, 400, 24), 18, Color(MINT, shown)); line.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if ending_ticks < 120: return
	var rows: int = menu_options.size()
	var top: float = 296.0 - rows * 23.0
	panel(Rect2(150, top - 10, 340, rows * 23.0 + 18))
	render_options(Rect2(160, top, 320, rows * 23.0))

func render_options(rect: Rect2) -> void:
	var reviewing: bool = mode == Mode.BATTLE and caption == "Review party plan"
	var grid: bool = mode == Mode.BATTLE and (caption.contains("Choose an action") or reviewing)
	var rows: int = floori(rect.size.y / 23)
	# A list longer than the box but short enough for two columns (e.g. five CONNECT options and
	# Back in the battle panel) splits into columns instead of scrolling Back out of view.
	var per_column: int = ceili(menu_options.size() / 2.0)
	var columns: int = 2 if not grid and menu_options.size() > rows and rect.size.x >= 400 and per_column <= rows else 1
	var first: int = 0 if grid or columns == 2 else maxi(0, selection - rows + 1)
	var count: int = 3 if reviewing else 6 if grid else menu_options.size() if columns == 2 else rows
	var names_only: bool = pause_context and mode == Mode.MENU and (caption.begins_with("Party") or party_caption(caption))
	if not grid and columns == 1 and menu_options.size() > rows:
		var track: ColorRect = ColorRect.new()
		track.position = Vector2(rect.end.x + 2, rect.position.y); track.size = Vector2(3, rect.size.y); track.color = PLUM
		track.mouse_filter = Control.MOUSE_FILTER_IGNORE; ui.add_child(track); text_nodes.append(track)
		var thumb: ColorRect = ColorRect.new()
		var thumb_height: float = rect.size.y * rows / float(menu_options.size())
		thumb.position = track.position + Vector2(0, (rect.size.y - thumb_height) * first / float(maxi(1, menu_options.size() - rows)))
		thumb.size = Vector2(3, thumb_height); thumb.color = AMBER
		thumb.mouse_filter = Control.MOUSE_FILTER_IGNORE; ui.add_child(thumb); text_nodes.append(thumb)
	for i: int in range(first, mini(menu_options.size(), first + count)):
		if mode == Mode.MENU and menu_options[i].label == "Back": continue
		var chosen: bool = i == selection
		var button: Button = Button.new()
		button.set_meta("option_index", i)
		button.text = str(menu_options[i].label).get_slice(" ", 0) if names_only else str(menu_options[i].label)
		button.add_theme_font_override("font", font)
		button.add_theme_font_size_override("font_size", 12)
		button.add_theme_color_override("font_color", MUTED if menu_options[i].get("disabled", false) else INK if chosen else CREAM)
		button.add_theme_color_override("font_hover_color", Color.WHITE)
		button.clip_text = true
		button.position = rect.position + (Vector2((i % 3) * (rect.size.x / 3), (i / 3) * 35) if grid else Vector2((i / per_column) * (rect.size.x / 2 + 4), (i % per_column) * 23) if columns == 2 else Vector2(0, (i - first) * 23))
		var option_size: Vector2 = Vector2(rect.size.x / 3 - 8, 24 if reviewing else 30) if grid else Vector2(rect.size.x / 2 - 4, 22) if columns == 2 else Vector2(rect.size.x, 22)
		button.size = option_size
		button.alignment = HORIZONTAL_ALIGNMENT_CENTER if grid else HORIZONTAL_ALIGNMENT_LEFT
		# Selected = solid amber with dark text; the rest stay quiet so one choice stands out.
		var normal: StyleBoxFlat = StyleBoxFlat.new()
		normal.bg_color = AMBER if chosen else Color(INK, 0.94) if grid else Color(0, 0, 0, 0)
		normal.border_color = AMBER if chosen else LINE
		normal.set_border_width_all(1 if grid or chosen else 0)
		normal.set_corner_radius_all(3)
		normal.anti_aliasing = false
		normal.content_margin_left = 8; normal.content_margin_right = 8; normal.content_margin_top = 0; normal.content_margin_bottom = 0
		button.add_theme_stylebox_override("normal", normal)
		button.add_theme_stylebox_override("disabled", normal); button.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
		var hover: StyleBoxFlat = normal.duplicate()
		hover.bg_color = Color("51425a") if not chosen else AMBER.lightened(0.15); hover.border_color = AMBER; hover.set_border_width_all(1)
		button.add_theme_stylebox_override("hover", hover); button.add_theme_stylebox_override("pressed", hover)
		button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		button.focus_mode = Control.FOCUS_NONE
		button.mouse_entered.connect(func() -> void:
			if pointer_mode: hover_index = i; update_command_help())
		button.mouse_exited.connect(func() -> void:
			if hover_index == i: hover_index = -1; update_command_help())
		button.pressed.connect(func() -> void: activate(i))
		ui.add_child(button); text_nodes.append(button); buttons.append(button)
		# Size again once the slim styleboxes apply; the default theme's cached minimum clamped it taller.
		button.update_minimum_size()
		button.size = option_size

func command_summary(command: Dictionary) -> String:
	var actor_name: String = str(battle.party[int(command.actor)].id).capitalize()
	var kind: String = str(command.kind)
	var text: String = actor_name + ": " + str(command.get("label", "BOUNDARY" if command.get("boundary", false) else kind.to_upper()))
	if kind == "promise": text += " / next defense"
	if command.has("joint"): text = "Jules + Imani: HEAR ME OUT / 35 SYNC"
	elif kind == "item": text += " " + str(command.item).capitalize() + " x1/%d" % int(battle.inventory[command.item])
	elif kind in ["shield", "heal", "slow", "brace", "lantern", "windbreak", "warmth"]: text += " / %d SYNC" % BattleRules._cost(command)
	elif kind == "guard": text += " / +12 SYNC"
	if command.has("target"): text += " > " + str(battle.party[int(command.target)].id).capitalize()
	return text

func render_battle_ui() -> void:
	var name: String = "FLYERER" if boss_id.is_empty() else "COACH PRIME" if boss_id == "deion" else "HOLD THE LIGHT" if boss_id == "walt" else "JAKERSON" if boss_id == "jakerson_final" else "GWEN THE RED" if boss_id == "errata" else NativeRandomFights.name_of(boss_id).to_upper() if NativeRandomFights.is_fight(boss_id) else boss_id.to_upper()
	# Foe card: name, then real meters instead of bare numbers. It sits top centre, between the
	# party and the foe, so it never covers the enemy sprite (tall bosses reach y 42).
	var card: float = 214.0
	panel(Rect2(card, 8, 212, 62))
	label(name, Rect2(card + 12, 13, 188, 16), 12, AMBER)
	if bool(battle.get("eased", false)) and battle.outcome == "active" and mode in [Mode.TELEGRAPH, Mode.DODGE]: right_label("EASING UP", Rect2(card + 12, 13, 190, 16), MINT)
	elif BattleRules.desperate(battle) and int(battle.openness) < 100 and battle.outcome == "active" and boss_id not in ["jakerson", "jakerson_final"]: right_label("DESPERATE", Rect2(card + 12, 13, 190, 16), Color("e8837b"))
	# OPEN is the meter most fights are won on, so it is the big, bright one; HP is the quiet one.
	label("WIND" if boss_id == "walt" else "HP", Rect2(card + 12, 31, 40, 16), 12, MUTED)
	meter(Rect2(card + 52, 37, 112, 3), float(shown_enemy_hp) / maxf(1.0, float(battle.get("max_hp", shown_enemy_hp))), Color("a8823f"))
	right_label(str(shown_enemy_hp), Rect2(card + 166, 31, 36, 16), MUTED)
	# In Hold the Light the lantern-bearer on the foe side is Walt, who is being helped: say so.
	if boss_id == "walt":
		var plate: float = text_width("WALT / HOLDS THE LIGHT") + 12
		panel(Rect2(480 - plate / 2, 148, plate, 17), MINT)
		label("WALT / HOLDS THE LIGHT", Rect2(480 - plate / 2 + 6, 149, plate - 8, 16), 12, MINT)
	label("OPEN", Rect2(card + 12, 49, 40, 16), 12, MINT)
	meter(Rect2(card + 52, 51, 112, 9), float(battle.openness) / 100.0, MINT)
	right_label("%s%%" % battle.openness, Rect2(card + 166, 49, 36, 16), MINT)
	# Party strip: one card per member, SYNC as its own meter at the end.
	var joined: int = 1 + int(bool(state.flags.get("imani_joined", false))) + int(bool(state.flags.get("walt_joined", false)))
	for i: int in range(joined):
		var member: Dictionary = battle.party[i]
		var x: float = 12 + i * 152
		var acting: bool = actor == i and mode == Mode.BATTLE or target == i and mode == Mode.DODGE
		var down: bool = int(member.hp) <= 0
		panel(Rect2(x, 316, 146, 36), AMBER if acting else LINE)
		label(str(member.id).capitalize(), Rect2(x + 9, 320, 70, 16), 12, MUTED if down else AMBER if acting else CREAM)
		right_label("%d/%d" % [int(member.hp), int(member.max)], Rect2(x + 60, 320, 77, 16), MUTED if down else CREAM)
		meter(Rect2(x + 9, 340, 128, 4), float(member.hp) / maxf(1.0, float(member.max)), Color("e8837b") if int(member.hp) * 4 <= int(member.max) else AMBER)
	panel(Rect2(470, 316, 158, 36), MINT if battle.promise else LINE)
	label("SYNC", Rect2(479, 320, 60, 16), 12, MINT)
	right_label(("PROMISE  " if battle.promise else "") + str(battle.sync), Rect2(520, 320, 99, 16), MINT)
	meter(Rect2(479, 340, 140, 4), float(battle.sync) / 100.0, MINT)
	var progress: String = ""
	if mode in [Mode.TELEGRAPH, Mode.DODGE]: progress = live_promise_progress() if battle.promise else "No promise this turn"
	elif mode == Mode.BATTLE: progress = last_promise_result
	if boss_id == "claim":
		# The three things RELEASE needs (tag delivered, one item returned, a boundary kept).
		var met: int = int(bool(claim_needs.tagDelivered)) + int(bool(claim_needs.oneReturned)) + int(bool(claim_needs.boundaryKept))
		progress += ("\n" if not progress.is_empty() else "") + "Needs met %d/3" % met
	if mode == Mode.BATTLE:
		panel(Rect2(12, 166, 616, 142))
		label(battle_error if not battle_error.is_empty() else caption.replace("Choose an action", "your turn"), Rect2(26, 175, 330, 16), 12, Color("e8837b") if not battle_error.is_empty() else AMBER)
		if not progress.is_empty(): right_label(progress.get_slice("\n", 0), Rect2(330, 175, 284, 16), MINT)
		fill(Rect2(26, 195, 588, 1), LINE)
		var preview: Array[String] = []
		for command: Dictionary in plan: preview.append(command_summary(command))
		if caption == "Review party plan":
			label("\n".join(preview), Rect2(26, 203, 588, 64), 12, MINT)
			render_options(Rect2(26, 274, 594, 26))
		elif caption.contains("Choose an action"):
			render_options(Rect2(26, 205, 594, 71))
			battle_help = label("", Rect2(26, 284, 588, 16), 12, MINT)
			update_command_help()
		else:
			render_options(Rect2(26, 203, 588, 98))
	elif mode == Mode.TIMING:
		panel(Rect2(12, 166, 616, 142))
		var strikes: Array = plan.filter(func(c: Dictionary) -> bool: return c.kind == "strike")
		var striker: String = str(battle.party[int(strikes[timing_index].actor)].id).capitalize()
		label(striker + " / confirm when the light meets the centre", Rect2(26, 175, 584, 16), 12, AMBER)
		fill(Rect2(26, 195, 588, 1), LINE)
		fill(Rect2(80, 241, 480, 9), PLUM)
		fill(Rect2(302, 235, 36, 21), AMBER)
		fill(Rect2(80 + minf(1.0, timing_ticks / 54.0) * 480, 231, 3, 29), CREAM)
	elif mode == Mode.RESOLVE:
		# Keep the command panel at full height: who is acting, the whole turn's plan as a log
		# (done / now / next) and what the current action does.
		panel(Rect2(12, 166, 616, 142))
		label(action_text, Rect2(26, 175, 420, 16), 12, AMBER)
		right_label("Action %d/%d" % [mini(resolution_index + 1, plan.size()), plan.size()], Rect2(450, 175, 164, 16), MUTED)
		fill(Rect2(26, 195, 588, 1), LINE)
		for i: int in range(mini(plan.size(), 3)):
			var row: float = 205 + i * 22
			var now: bool = i == resolution_index
			if now: caret(Vector2(28, row + 5), AMBER)
			label(command_summary(plan[i]), Rect2(42, row, 572, 16), 12, AMBER if now else MUTED if i < resolution_index else CREAM)
		if resolution_index < plan.size():
			var acting: Dictionary = plan[resolution_index]
			var kind: String = "boundary" if acting.get("boundary", false) else str(acting.kind)
			label(str(ACTION_HELP.get(kind, "")), Rect2(26, 284, 588, 16), 12, MINT)
	elif mode in [Mode.TELEGRAPH, Mode.DODGE]:
		var instructions: Dictionary = {"": "Move through the paper gaps. Confirm briefly pushes paper away.", "chip": "Tap left / right to hop. Match the called safe column.", "deion": "%s: jump. %s: duck. Or use the buttons." % [binding_label("confirm"), binding_label("run")], "todd": "Move between stamps. RED AUDIT: stay still. Confirm signs boxes.", "pinpal": "Move left / right. Confirm near a ball to flip it back.", "claim": "Carry the outlined tag." if boss_stage == 0 else "Return one item. Confirm at a destination; leave the other a note."}
		instructions.cone="Follow each green row. Crossed-out rows are cancelled calls."
		instructions.chad="Keep the FREE slot empty. Rest in the Do Not Disturb bubble."
		instructions.rook=["Confirm at the key, then the exit.","CONNECT > REVISE chooses one exit. Hold its green box.","Move into each green cue and confirm together."][mini(2,boss_stage)]
		instructions.val=["Confirm at RETURN, then STOP, then NOTE.","In CONNECT, each of you turns down your own perfect resume. Hold the shared space.","CONNECT > REVISE frees one side of the booked chairs. Hold the way out.","Confirm at two green stopping cues. Then choose an ending."][mini(3,boss_stage)]
		instructions.jakerson_final = "Everything he taught you. With a promise, sign each green line with confirm."
		instructions.jakerson = "Dodge the code. With a promise, stand in each green commit and press confirm."
		instructions.walt = "Stay in the gold shelter. Confirm at the lantern as gusts warn. Dodge debris."
		instructions.encore = "Follow the lit lane. When the cue box opens, move into it and confirm."
		instructions.errata="Dodge the red pen. Confirm in the green box at the three marked pauses."
		instructions.eric="Dodge the traces. With a promise, stand on each test point and press confirm to probe it."
		instructions.autocomplete="Confirm at the green suggestion, then at the STOP box. Slip through the gaps."
		var instruction: String = "Get ready" if mode == Mode.TELEGRAPH else str(pattern.get("phaseName", "Defense"))
		if boss_id == "claim" and mode == Mode.DODGE:
			instruction = "Tag carried / move to the outlined destination" if pattern.get("carryTag", false) else "Pick up the outlined tag"
			if pattern.promiseComplete: instruction = "Tag delivered through the sweep." if int(pattern.phase) == 0 else "One return, one note. Promise kept." if battle.promise else "One return, one note completed."
		if pattern.get("audit", false): instruction = "RED AUDIT / HOLD STILL"
		# Three columns: how to play | arena | what the promise needs.
		# The side panels stop 20px short of the box (emitters and rigs sit just outside its edges).
		panel(Rect2(12, 166, 160, 120))
		var heading: float = 16.0 if text_width(instruction) <= 144 else 34.0
		label(instruction, Rect2(20, 173, 146, heading), 12, Color("e8837b") if pattern.get("audit", false) else AMBER)
		fill(Rect2(20, 177 + heading, 144, 1), LINE)
		label(str(pattern.get("hint", instructions.get(boss_id, ""))), Rect2(20, 183 + heading, 146, 100 - heading), 12, CREAM)
		panel(Rect2(468, 166, 160, 120), MINT if battle.promise else LINE)
		label("PROMISE" if battle.promise else "DEFEND", Rect2(476, 173, 146, 16), 12, MINT if battle.promise else MUTED)
		fill(Rect2(476, 193, 144, 1), LINE)
		var lines: Array[String] = []
		for part: String in progress.replace("\n", " / ").split(" / "):
			var piece: String = part.strip_edges()
			if not piece.is_empty(): lines.append(piece.left(1).to_upper() + piece.substr(1))
		label("\n".join(lines), Rect2(476, 199, 146, 84), 12, CREAM)
		if resume_ticks > 0:
			# The countdown takes the action button's slot (hidden meanwhile), clear of the arena and soul.
			panel(Rect2(232, 291, 176, 22), AMBER)
			var count: Label = label("Resume in %s" % ceili(resume_ticks / 60.0), Rect2(232, 294, 176, 16), 12, AMBER)
			count.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	elif mode == Mode.RESULT:
		panel(Rect2(24, 187, 592, 113), AMBER)
		label(caption, Rect2(40, 202, 560, 26), 18, AMBER)
		render_options(Rect2(40, 242, 556, 51))
func _draw() -> void:
	if strange_ticks > 0 and world.visible and state.room == "U03":
		var booth: Vector2 = Vector2(382, 194)
		for placement: Dictionary in rooms[state.room].placements:
			if placement.kind == "booth": booth = Vector2(placement.x, placement.y - placement.h / 2.0)
		var wave: float = (120 - strange_ticks) % 40
		draw_arc(booth, 9 + wave, 0, TAU, 24, Color(0.6, 0.8, 0.85, 0.5 * (1 - wave / 40)), 1)
		if not state.settings.reducedMotion:
			for light: Node in lighting.get_children():
				light.energy = 0.35 + 0.35 * sin(strange_ticks / 10.0)
	if mode == Mode.WORLD:
		var hovered: Dictionary = object_at(get_global_mouse_position())
		if not hovered.is_empty():
			var anchor := Vector2(hovered.x, hovered.y)
			draw_arc(anchor, 17, 0, TAU, 24, AMBER, 2)
	var defending: bool = mode in [Mode.DODGE, Mode.TELEGRAPH] or pause_context and pause_mode in [Mode.DODGE, Mode.TELEGRAPH]
	var fighting: bool = mode==Mode.DIALOGUE and not world.visible or mode in [Mode.BATTLE, Mode.TIMING, Mode.TELEGRAPH, Mode.DODGE, Mode.RESULT, Mode.RESOLVE, Mode.BANNER]
	if (fighting or pause_context and pause_mode in [Mode.BATTLE, Mode.TIMING, Mode.TELEGRAPH, Mode.DODGE, Mode.RESULT, Mode.RESOLVE]) and battle_scenery.visible:
		# Dim the room behind the fight; deeper below the fighters where the menus sit. A painted
		# battle backdrop carries its own shading.
		if battle_scenery.get_child(0) is UMCEnvironment:
			draw_rect(Rect2(0, 0, 640, 360), Color(INK, 0.3))
			draw_rect(Rect2(0, 150, 640, 6), Color(INK, 0.18))
			for row: int in range(6):
				draw_rect(Rect2(0, 156 + row * 34, 640, 34), Color(INK, 0.32 + row * 0.08))
	elif fighting or pause_context and pause_mode in [Mode.BATTLE, Mode.TIMING, Mode.TELEGRAPH, Mode.DODGE, Mode.RESULT, Mode.RESOLVE]:
		draw_rect(Rect2(0, 0, 640, 360), INK)
		for row: int in range(5):
			draw_rect(Rect2(0, 82 + row * 15, 640, 15), Color("1b1c2d").lerp(Color("302737"), row / 8.0))
			for col: int in range(21):
				draw_line(Vector2(col * 32 + (16 if row % 2 else 0), 83 + row * 15), Vector2(col * 32 + (16 if row % 2 else 0), 96 + row * 15), Color("11131f"), 1)
	if defending and pattern.get("engine", "") == "box":
		dodge_view.show_pattern(pattern, Vector2(192, 166)); return
	dodge_view.hide_box()
	if not defending: return
	var offset: Vector2 = Vector2(192, 166)
	var arena: Rect2 = Rect2(offset, Vector2(256, 120))
	draw_rect(Rect2(offset, Vector2(256, 120)), Color("10121e"))
	draw_rect(Rect2(offset, Vector2(256, 120)), MINT if pattern.get("beatPulse", false) else AMBER, false, 1)
	if int(pattern.get("wardTicks", 0)) > 0:
		draw_rect(Rect2(offset + pattern.wardPocket.position, pattern.wardPocket.size), Color(0.5, 0.8, 0.7, 0.25))
	if boss_id in NativeFinalEncounter.IDS:draw_final_arena(offset)
	if boss_id == "walt":
		draw_rect(Rect2(offset + pattern.shelter.position, pattern.shelter.size), Color(0.9, 0.7, 0.3, 0.2))
		draw_rect(Rect2(offset + pattern.shelter.position, pattern.shelter.size), AMBER, false, 1)
		draw_circle(offset + Vector2(128, 62), 5, CREAM if int(pattern.lanternRaised) > 0 else AMBER)
	if boss_id == "encore":
		draw_rect(Rect2(offset + Vector2(float(pattern.safeColumn) - 20, 0), Vector2(40, 120)), Color(0.5, 0.8, 0.7, 0.15))
	if boss_id == "chip":
		for col: int in range(5): draw_line(offset + Vector2(24 + col * 52, 0), offset + Vector2(24 + col * 52, 120), PLUM, 1)
		draw_rect(Rect2(offset + Vector2(float(pattern.safeColumn) - 20, 0), Vector2(40, 120)), Color(0.5, 0.8, 0.7, 0.14))
	if boss_id == "deion": draw_line(offset + Vector2(0, 113), offset + Vector2(256, 113), CREAM, 1)
	if boss_id == "todd": draw_arc(offset + Vector2(128, 60), float(pattern.arenaRadius), 0, TAU, 48, Color("8f779e"), 1)
	for tell: Dictionary in pattern.telegraphs:
		if tell.get("kind", "") == "ring":
			draw_arc(offset + Vector2(128, 60), 52, float(tell.gap) + 0.6, float(tell.gap) + TAU - 0.6, 32, Color("937791"), 1)
		elif tell.get("kind", "") == "sector":
			draw_sector(offset + Vector2(128, 60), float(tell.get("innerRadius", 14)), float(tell.get("radius", 58)), float(tell.angle), float(tell.arc), Color(0.8, 0.5, 0.45, 0.16))
		elif tell.get("kind", "") != "audit":
			var vertical: bool = tell.get("axis", "horizontal") == "vertical" or absf(float(tell.get("vy", 0))) > 0
			if boss_id in NativeCampaign.EXPANSION_BOSSES or boss_id in NativeChapterTwo.BOSSES or boss_id in NativeFinalEncounter.IDS:
				var warning_rect: Rect2 = Rect2(offset + Vector2(float(tell.x) - float(tell.halfWidth), 0), Vector2(float(tell.halfWidth) * 2, 120)) if vertical else Rect2(offset + Vector2(0, float(tell.y) - float(tell.halfHeight)), Vector2(256, float(tell.halfHeight) * 2))
				draw_rect(warning_rect.intersection(arena), Color(0.8, 0.5, 0.45, 0.22))
			else:
				draw_line(offset + Vector2(float(tell.x), 0) if vertical else offset + Vector2(0, float(tell.y)), offset + Vector2(float(tell.x), 120) if vertical else offset + Vector2(256, float(tell.y)), Color("a68db8"), 1)
	for hazard: Dictionary in pattern.hazards:
		var at: Vector2 = offset + Vector2(float(hazard.x), float(hazard.y))
		if hazard.get("collision", "circle") == "rect":
			var half: Vector2 = Vector2(float(hazard.halfWidth), float(hazard.halfHeight))
			var clipped: Rect2 = Rect2(at - half, half * 2).intersection(arena)
			if clipped.has_area():
				draw_rect(clipped, Color("c28b65") if boss_id == "deion" else CREAM)
				draw_rect(clipped, AMBER, false, 1)
		elif hazard.get("collision", "circle") == "sector":
			draw_sector(at, float(hazard.innerRadius), float(hazard.radius), float(hazard.angle), float(hazard.arc), Color("b06470"))
		elif hazard.get("shape", "") == "stamp":
			draw_clipped(PackedVector2Array([at + Vector2(-3, -3), at + Vector2(3, -3), at + Vector2(3, 3), at + Vector2(-3, 3)]), arena, Color("d49483"))
		elif hazard.get("shape", "") == "ball":
			var ball: PackedVector2Array = []
			for i: int in range(12): ball.append(at + Vector2.from_angle(i * TAU / 12.0) * 5)
			draw_clipped(ball, arena, MINT if hazard.get("friendly", false) else AMBER)
			if arena.has_point(at + Vector2(-1, -2)): draw_circle(at + Vector2(-1, -2), 1, CREAM)
		else:
			draw_clipped(PackedVector2Array([at + Vector2(-5, -4), at + Vector2(5, 0), at + Vector2(-5, 4)]), arena, CREAM if boss_id != "chip" else MINT)
	if battle.promise:
		for marker: Dictionary in pattern.markers:
			if marker.get("active", true) and not marker.collected:
				var at: Vector2 = offset + Vector2(float(marker.x), float(marker.y))
				draw_rect(Rect2(at - Vector2(7, 8), Vector2(14, 16)), MINT, false, 2)
	if pattern.get("flipperTicks", 0) > 0:
		draw_line(offset + Vector2(float(pattern.cursor.x) - 24, 109), offset + Vector2(float(pattern.cursor.x) + 24, 98), MINT, 3)
	var cursor: Vector2 = offset + Vector2(float(pattern.cursor.x), float(pattern.cursor.y))
	if int(pattern.invulnerability) % 8 < 4:
		draw_rect(Rect2(cursor - Vector2(4, 5), Vector2(8, 9)), AMBER)
		draw_circle(cursor, 1, Color.WHITE)

func use_door(object: Dictionary) -> void:
	for required: String in object.get("requires", []):
		if not state.flags.get(required, false):
			player.position += Vector2(0, 12)
			message(str({"flyer_resolution":"Settle the poster in the club room first.","cal_key_received":"Ask Cal for the service key on the repair landing.", "walt_joined":"Find Walt in the underpass under Broadway first.", "claim_resolution":"Follow the voice into lost property first.", "chip_resolution":"Meet Chip on the audience lawn first.", "volunteers_released":"Finish one task with the volunteers in the tent.", "imani_performance":"Let Imani choose her song backstage.", "chapter1_complete":"Finish ENCORE on Farrand main stage.", "library_pass":"Speak to Nell at the checkout desk.", "stacks_shifted":"Turn the crank in the moving stacks.", "bookmark_found":"Pick up the bookmark in the reading room.", "errata_resolution":"Settle Gwen the Red in the moving stacks.", "dev_met":"Speak to Dev in the workshop.", "bridge_ready":"After Professor Eric's test, return to Dev to install the bridge.", "autocomplete_resolution":"Bring the source reel back to AUTOCOMPLETE.", "playback_heard":"Listen to the reel in the playback room.", "chapter2_complete":"Hear the full reel in Norlin playback.", "notice_limits":"Read the notices in Old Main hall.", "booth_origin":"Read the original directory in the empty office.","rook_confessed":"Hear Rook in Old Main courtyard.","chapter3_complete":"Complete Todd\'s audit in Old Main.","attendees_freed":"Give the cloakroom guests a choice.","music_ready":"Let Imani finish the score in the orchestra pit.","rook_resolution":"Finish Rook\'s last shift on the balcony.","val_resolution":"Choose an ending on the graduation stage.","dawn_talk_read":"Talk with the party at the dawn exit."}.get(required, "Return the mixer, then help the living invitation.")))
			return
	if object.to == "U05" and not state.flags.get("booth_seen", false):
		message("Imani points to the NEXT YEAR booth. Check that voice first."); return
	audio.effect("door-hinge"); audio.effect("door-latch")
	var point: Array = object.spawn
	enter_room(str(object.to), Vector2(float(point[0]), float(point[1])))
	if object.to == "U03" and not state.flags.get("atrium_seen", false):
		state.flags.atrium_seen = true
		dialogue([["Jules", "Warm lights. Student art. A normal room. I can handle one normal room.", "neutral"], ["Jules", "Imani is in the club room to the left. I return the mixer, then I go.", "neutral"]], resume_world)

func objective() -> String:
	return NativeCampaign.objective(state)

func object_label(object: Dictionary) -> String:
	var name: String = str(object.name)
	if state.flags.get("mixer_returned", false): name = name.replace(" / return the mixer", "")
	return name

func advance_intro() -> void:
	if intro_ticks < 30: return
	var full_ticks: int = str(intro_cards[intro_index][1]).length() * 2
	if intro_index == intro_arrival: full_ticks = maxi(full_ticks, 180)
	if intro_ticks < full_ticks:
		intro_ticks = full_ticks; ui_dirty = true
		return
	intro_index += 1; intro_ticks = 0; ui_dirty = true
	if intro_index == intro_arrival:
		world.visible = true; backdrop.visible = false
		environment.arrival_origin = player.position; environment.set_arrival(0.0)
		player.facing = "up"; player.art.play("interact_up")
	if intro_index >= intro_cards.size():
		if intro_arrival < 0: NativeMoveIn.begin(self)
		else: finish_arrival(false)

func finish_arrival(skip: bool) -> void:
	enter_room("U01", Vector2(96, 258), false)
	environment.set_arrival(1.0)
	if skip:
		state.flags.intro_seen = true; persist(); resume_world()
	else:
		NativeJakerson.greeting(self)

func merge_party(members: Array) -> void:
	for i: int in range(3):
		if i == 0 or state.flags.get(ACTORS[i] + "_joined", false): state.party[i] = members[i].duplicate(true)

func present_action() -> void:
	var command: Dictionary = plan[resolution_index]
	var index: int = int(command.actor)
	var kind: String = str(command.kind)
	battle_sprites[index].play("strike" if kind == "strike" else "guard" if kind == "guard" else "talent" if kind in ["shield","heal","slow","lantern","windbreak","warmth"] else "connect")
	action_text = str(battle.party[index].id).capitalize() + " / " + ("A smaller, honest task." if command.get("boundary", false) else kind.capitalize())
	var origin: Vector2 = battle_sprites[index].position - Vector2(0, 34)
	if kind == "strike":
		vfx.play("slash", origin, Vector2(480, 108)); audio.combat("swing")
		NativeBattleJuice.lunge(battle_sprites[index])
	else:
		vfx.play("guard" if kind == "guard" else "heal" if kind in ["heal", "item", "warmth"] else "promise", origin, origin)
		audio.combat("guard" if kind == "guard" else "shield" if kind == "shield" else "release" if kind == "release" else "pick")
	ui_dirty = true

func present_impact() -> void:
	var command: Dictionary = plan[resolution_index]
	if command.kind == "strike":
		var damage: int = 1 if float(command.get("timing", 0)) < 0 else maxi(1, roundi(float(battle.party[int(command.actor)].power) * (0.8 + 0.6 * float(command.get("timing", 1.0 / 3.0))) - 1))
		shown_enemy_hp = maxi(int(pending_battle.hp), shown_enemy_hp - damage)
		vfx.play("impact", Vector2(480, 105), Vector2(480, 105), damage)
		foe.modulate = Color("df8078"); claim_art.set_pose("hit"); pin_art.set_pose("hit")
		foe.play("hit")
		audio.combat("enemyhurt")
		var struck: Node2D = claim_art if boss_id == "claim" else pin_art if boss_id == "pinpal" else foe
		NativeBattleJuice.flinch(struck, Vector2.RIGHT, damage); NativeBattleJuice.flash(struck)
		if damage >= 12: NativeBattleJuice.kick([battle_scenery, foe, claim_art, pin_art] + battle_sprites, 2.0, 10)
	elif str(command.kind) in ["heal", "item", "warmth"]:
		# Healing pops a green number over each ally it reached.
		for i: int in range(mini(3, battle_sprites.size())):
			if command.has("target") and int(command.target) != i: continue
			var gained: int = int(pending_battle.party[i].hp) - int(battle.party[i].hp)
			if gained > 0 and battle_sprites[i].visible: vfx.play("heal", battle_sprites[i].position, battle_sprites[i].position - Vector2(0, 38), gained)
	ui_dirty = true

func stage_dialogue() -> void:
	var speaker: String = str(dialogue_lines[line_index][0])
	for prop: Node2D in scene_props:
		if str(prop.get_meta("id", "")) == {"CLAIM":"claim", "Pin Pal":"pinpal"}.get(speaker, ""):
			prop.set_pose("tell")
	for prop: Node2D in environment.foreground_nodes:
		if prop is NativeSpatialProp and prop.definition.get("object") == "booth": prop.set_pose("tell" if speaker == "Booth" else "idle")
	pip.set_pose("wave" if speaker == "Pip" else "idle")
	var identities: Dictionary = {"Cal":"cal", "Mags":"mags", "Nell":"nell", "Dev":"dev", "Rook":"rook", "Walt":"walt", "ENCORE":"encore", "Gwen the Red":"errata", "AUTOCOMPLETE":"autocomplete", "LOADBEARER":"loadbearer", "Professor Eric":"eric", "VAL":"val", "Val":"val_small", "CONE COMMITTEE":"cone", "Chad":"chad", "Jakerson":"jakerson", "Mara":"mara", "Eli":"eli", "Chip":"chip", "Deion Sanders":"deion", "Todd Saliman":"todd", "Flyerer":"flyer"}
	if speaker != "Booth": NativeTalkMotion.stage(self, speaker, identities)
	dialogue_top = dialogue_side_top(NativeTalkMotion.speakers(self, speaker, identities))
	if speaker == "Booth":
		strange_ticks = 120
		audio.combat("warning")
		for person: WorldActor in [player] + followers:
			if person.visible: person.art.play("interact_up")

## Undertale-style box placement: the box goes to the top when it would cover the people talking
## (the speaker, and Jules a little), and back down when the top box would cover them instead.
func dialogue_side_top(talkers: Array) -> bool:
	if not world.visible: return false
	var large: bool = state.settings.large
	var bottom_edge: float = (130.0 if large else 214.0) - 8.0
	var top_edge: float = (38.0 + 220.0 if large else 38.0 + 136.0) + 8.0
	var canvas: Transform2D = get_viewport().get_canvas_transform()
	var under_bottom: float = 0.0
	var under_top: float = 0.0
	var anchors: Array = []
	for sprite: Variant in talkers: anchors.append([sprite, 1.0])
	anchors.append([player.art, 0.5])
	for anchor: Array in anchors:
		if not is_instance_valid(anchor[0]): continue
		var sprite: Node2D = anchor[0]
		if not sprite.is_visible_in_tree(): continue
		var feet: Vector2 = canvas * sprite.global_position
		if feet.x < -16 or feet.x > 656 or feet.y < 0 or feet.y > 420: continue
		var middle: float = feet.y - 26.0
		if middle > bottom_edge: under_bottom += float(anchor[1])
		if middle < top_edge: under_top += float(anchor[1])
	if under_bottom > under_top: return true
	if under_top > under_bottom: return false
	return dialogue_top

func _qa_smoke() -> void:
	var route: Node = load("res://scenes/qa_hub.gd" if "--qa-hub" in OS.get_cmdline_user_args() else "res://scenes/qa_wander.gd" if "--qa-wander" in OS.get_cmdline_user_args() else "res://scenes/qa_jakerson.gd" if "--qa-jakerson" in OS.get_cmdline_user_args() else "res://scenes/qa_final.gd" if "--qa-final" in OS.get_cmdline_user_args() else "res://scenes/qa_chapter3.gd" if "--qa-chapter3" in OS.get_cmdline_user_args() else "res://scenes/qa_chapter2.gd" if "--qa-chapter2" in OS.get_cmdline_user_args() else "res://scenes/qa_chapter1.gd" if "--qa-chapter1" in OS.get_cmdline_user_args() else "res://scenes/qa_review_controls.gd" if "--qa-review-ui" in OS.get_cmdline_user_args() else "res://scenes/qa_opening.gd").new()
	add_child(route)
	var passed: bool = await route.run(self)
	if qa_record != null and not qa_record_finishing: qa_finish_record()
	while qa_record != null: await get_tree().process_frame
	var timing_file: FileAccess = FileAccess.open(qa_folder.path_join("music-timing.json"), FileAccess.WRITE)
	if timing_file: timing_file.store_string(JSON.stringify(qa_music_events, "\t")); timing_file.close()
	audio.shutdown()
	var tree: SceneTree = get_tree()
	tree.create_timer(0.1).timeout.connect(tree.quit.bind(0 if passed else 1))
	queue_free()

func qa_finish_record() -> void:
	if qa_record_finishing: return
	qa_record_finishing = true
	await get_tree().create_timer(10.5 if "--qa-stop-at-claim-result" in OS.get_cmdline_user_args() else 4.0).timeout
	qa_record.set_recording_active(false)
	var recording: AudioStreamWAV = qa_record.get_recording()
	if recording != null:
		print("QA_AUDIO Master boss recording result=", recording.save_to_wav(qa_folder.path_join("claim-live-mix.wav")))
	for i: int in range(AudioServer.get_bus_effect_count(0) - 1, -1, -1):
		if AudioServer.get_bus_effect(0, i) == qa_record: AudioServer.remove_bus_effect(0, i)
	qa_record = null
	qa_record_finishing = false

func portrait(speaker: String, expression: int, rect: Rect2) -> void:
	portrait_texture(NativeCastArt.portrait(speaker, expression), rect)

func portrait_texture(texture: Texture2D, rect: Rect2) -> void:
	if texture == null: return
	var node := TextureRect.new()
	node.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	node.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	node.texture = texture
	node.position = rect.position; node.size = rect.size
	node.clip_contents = true
	node.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(node); text_nodes.append(node)

func draw_sector(at: Vector2, inner: float, outer: float, angle: float, arc: float, color: Color) -> void:
	var polygon: PackedVector2Array = []
	for i: int in range(17):
		var a: float = angle - arc + 2 * arc * i / 16.0
		polygon.append(at + Vector2(cos(a), sin(a)) * outer)
	for i: int in range(16, -1, -1):
		var a: float = angle - arc + 2 * arc * i / 16.0
		polygon.append(at + Vector2(cos(a), sin(a)) * inner)
	draw_colored_polygon(polygon, color)

func draw_clipped(polygon: PackedVector2Array, rect: Rect2, color: Color) -> void:
	var boundary: PackedVector2Array = [rect.position, rect.position + Vector2(rect.size.x, 0), rect.end, rect.position + Vector2(0, rect.size.y)]
	for piece: PackedVector2Array in Geometry2D.intersect_polygons(polygon, boundary):
		var pixels: PackedVector2Array = []
		for point: Vector2 in piece:
			var pixel: Vector2 = point.round()
			if pixels.is_empty() or pixel != pixels[-1]: pixels.append(pixel)
		if pixels.size() > 1 and pixels[0] == pixels[-1]: pixels.remove_at(pixels.size() - 1)
		if pixels.size() >= 3 and not Geometry2D.triangulate_polygon(pixels).is_empty(): draw_colored_polygon(pixels, color)

func _exit_tree() -> void:
	menu_options.clear(); pause_options.clear(); dialogue_choices.clear()
	dialogue_callback = Callable()
	if is_instance_valid(audio): audio.shutdown()


func reset_pointer_controls() -> void:
	pointer_duck = false; pointer_hop = 0; beat_defend = false; dodge_goal = Vector2.INF
	if is_instance_valid(overlay): overlay.clear_held_input()

func update_command_help() -> void:
	if not is_instance_valid(battle_help): return
	var help: Array[String] = ["Clear loose debris with a timed push." if boss_id == "walt" else "A timed hit. Accuracy changes damage.", "Observe, make a promise or set a boundary.", "Character skills use shared SYNC.", "Use a supply on a chosen ally.", "Reduce damage and add 12 SYNC.", "Survive three seconds to step away."]
	battle_help.text = help[clampi(hover_index if pointer_mode and hover_index >= 0 else selection, 0, 5)]

func live_promise_progress() -> String:
	if pattern.get("engine", "") == "box": return DodgeBox.script_for(boss_id).progress(pattern)
	if boss_id in NativeFinalEncounter.IDS:return NativeFinalEncounter.progress(pattern)
	if boss_id in NativeChapterTwo.BOSSES:return NativeCampusEncounter.progress(pattern)
	var markers: Array = pattern.get("markers", [])
	var read: int = markers.filter(func(marker: Dictionary) -> bool: return marker.get("collected", false)).size()
	match boss_id:
		"walt": return "Lantern %d%% / gusts %d/3" % [int(pattern.get("lantern", 100)), mini(3, int(pattern.get("gustsKept", 0)))]
		"encore": return "Stopping cues %d/2 / verse %d/3" % [mini(2, int(pattern.get("cuesReached", 0))), boss_stage + 1]
		"": return "Invitation read %d/1" % mini(1, read)
		"chip": return "Called columns %d/3" % mini(3, int(pattern.get("columnsReached", 0)))
		"deion": return "Obstacles cleared %d/2 / flag %s" % [mini(2, int(pattern.get("runnerCleared", 0))), "held" if read > 0 else "open"]
		"todd": return "Consent boxes %d/2%s" % [mini(2, int(pattern.get("consentCount", 0))), " / HOLD STILL" if pattern.get("audit", false) else ""]
		"pinpal": return "Balls returned %d/3" % mini(3, int(pattern.get("deflections", 0)))
		"claim":
			if int(pattern.get("phase", boss_stage)) == 0:
				return "Tag %s / sweep %s\ndelivered %s" % ["held" if pattern.get("carryTag", false) else "open", "clear" if int(pattern.get("claimSweepPassed", 0)) > 0 else "open", "yes" if markers.size() > 1 and markers[1].get("collected", false) else "open"]
			return "One return %s / note %s\nboundary %s" % ["done" if int(pattern.get("delivery", 0)) > 0 else "open", "left" if pattern.get("noteLeft", false) else "open", "kept" if claim_needs.boundaryKept or pattern.get("boundary", false) and pattern.get("promiseComplete", false) else "offered" if pattern.get("boundary", false) else "open"]
	return ""

func draw_final_arena(offset: Vector2) -> void:
	if boss_id=="cone":
		draw_rect(Rect2(offset+Vector2(0,float(pattern.safeLane)-12),Vector2(256,24)),Color(0.4,0.8,0.6,0.18))
		if float(pattern.cancelledLane)>=0:
			var y: float=float(pattern.cancelledLane)
			draw_line(offset+Vector2(0,y),offset+Vector2(256,y),PLUM,1)
			draw_line(offset+Vector2(116,y-7),offset+Vector2(140,y+7),CREAM,2);draw_line(offset+Vector2(116,y+7),offset+Vector2(140,y-7),CREAM,2)
	if boss_id=="chad" and pattern.get("engine","")!="box":
		draw_rect(Rect2(offset+pattern.emptySpace.position,pattern.emptySpace.size),Color("6b526a"),false,2)
		draw_line(offset+pattern.emptySpace.position,offset+pattern.emptySpace.end,PLUM,1)
		draw_rect(Rect2(offset+pattern.quietPocket.position,pattern.quietPocket.size),MINT,false,2)
		draw_circle(offset+Vector2(32,98),3,AMBER)
	if boss_id=="rook" and boss_stage==2 or boss_id=="val" and boss_stage==1:
		draw_rect(Rect2(offset+pattern.sharedPocket.position,pattern.sharedPocket.size),Color(0.4,0.8,0.6,0.18))
	if boss_id=="rook" and boss_stage==1 and not str(pattern.revision).is_empty():
		var x: float=208.0 if pattern.revision=="west" else 48.0
		draw_line(offset+Vector2(x-8,62),offset+Vector2(x+8,78),PLUM,2);draw_line(offset+Vector2(x-8,78),offset+Vector2(x+8,62),PLUM,2)
	if boss_id=="val" and boss_stage==2:
		for block: Rect2 in pattern.chairs:
			draw_rect(Rect2(offset+block.position,block.size),Color("534157"))
			for y: int in range(12,120,24):
				for x: int in range(int(block.position.x)+8,int(block.end.x)-8,24):
					draw_rect(Rect2(offset+Vector2(x,y),Vector2(14,10)),Color("95758b"));draw_line(offset+Vector2(x,y+10),offset+Vector2(x,y+17),CREAM,1)

func animate_idle_cast() -> void:
	var t: float=environment.elapsed
	var reduced: bool=bool(state.settings.reducedMotion)
	if world.visible:
		for person: WorldActor in [player]+followers:
			# Standing still, the party fidget too once their art has fidget_<dir> animations.
			if mode == Mode.WORLD and str(person.art.animation).begins_with("idle_"): NativeNpcLife.fidget(person.art,Vector2.INF,t,reduced)
			if str(person.art.animation).begins_with("idle") or str(person.art.animation).begins_with("interact"):
				NativeIdleMotion.apply(person.art,person.appearance_height,t,reduced,person.get_instance_id())
		for npc: AnimatedSprite2D in world_npcs:
			if npc.get_meta("moving", false): continue
			if mode == Mode.WORLD: NativeNpcLife.update(npc,player.position,t,reduced)
			NativeIdleMotion.apply(npc,float(npc.get_meta("idle_height",48.0)),t,reduced,npc.get_instance_id())
	else:
		for i: int in range(battle_sprites.size()):
			var sprite: AnimatedSprite2D=battle_sprites[i]
			if str(sprite.animation)=="idle":NativeIdleMotion.apply(sprite,72.0,t,reduced,i+4)
		if str(foe.animation) in ["idle","idle_down","settled"]:NativeIdleMotion.apply(foe,foe_height(),t,reduced,9)
