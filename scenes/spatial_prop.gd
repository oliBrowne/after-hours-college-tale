class_name NativeSpatialProp
extends Node2D

const INK = Color("171a2b")
const WOOD = Color("805a58")
const STONE = Color("b5816c")
const CREAM = Color("e6d6b1")
const AMBER = Color("e8b45c")
const BLUE = Color("425da6")
const GREEN = Color("374a46")
const RUST = Color("9e4e52")
const FONT = preload("res://assets/art/afterhours-font.fnt")
var definition: Dictionary
var flags: Dictionary
var elapsed: float = 0.0
var pose: String = "idle"
var reduced_motion: bool=false
var art_texture: Texture2D
var art_anchor: Vector2 = Vector2.ZERO
var label_only: bool = false
var art_flag: String = ""
var art_flag_texture: Texture2D

## Painted rooms hand props a sprite (drawn at its floor anchor) or mark them as already painted.
func use_art(art: Dictionary, painted: bool) -> void:
	label_only = painted
	if art.is_empty(): return
	art_texture = NativeRoomArt.texture(str(art.texture))
	art_anchor = Vector2(float(art.anchor[0]), float(art.anchor[1]))
	if art.has("flag"):
		art_flag = str(art.flag); art_flag_texture = NativeRoomArt.texture(str(art.flag_texture))
	queue_redraw()

func set_pose(value: String) -> void:
	pose = value
	queue_redraw()

func configure(item: Dictionary, room_flags: Dictionary) -> void:
	definition = item
	flags = room_flags
	position = Vector2(item.x, item.y)
	if item.get("object", "") == "bus": z_index = 1
	texture_filter = TEXTURE_FILTER_NEAREST

func step(delta: float) -> void:
	elapsed += delta
	if not definition.is_empty(): queue_redraw()

func r(x: float, y: float, w: float, h: float, color: Color) -> void:
	draw_rect(Rect2(roundf(x), roundf(y), roundf(w), roundf(h)), color)

func text(value: String, at: Vector2, color: Color = CREAM) -> void:
	draw_string(FONT, at.round(), value, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, color)

func _draw() -> void:
	if definition.is_empty(): return
	var w: float = definition.w
	var h: float = definition.h
	var l: float = -w / 2
	var kind: String = definition.kind
	if kind == "flyer_note" and flags.get("flyer_resolution", "") != "forceful": return
	if label_only:
		var label: String = str(definition.get("label", ""))
		var width: float = FONT.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
		var locked: bool = false
		for required: String in definition.get("requires", []):
			if not flags.get(required, false): locked = true
		if not label.is_empty(): r(-width / 2 - 3, -h - 20, width + 6, 15, Color(INK, 0.85)); text(label, Vector2(-width / 2, -h - 9), Color("c46a5c") if locked else AMBER)
		return
	if art_texture != null:
		draw_texture(art_flag_texture if not art_flag.is_empty() and flags.get(art_flag, false) else art_texture, -art_anchor)
		_draw_state_details(kind, w, h, l)
		return
	r(l + 2, -1, w, 3, Color(INK, 0.35))
	match kind:
		"bridge_model":
			r(l,-h,w,8,BLUE);r(l,-h+8,w,4,AMBER)
			var revised: bool=flags.get("model_revised",false)
			for xx: float in [-w/3,w/3]:
				r(xx-5,-h+12,10,h-12 if revised else 35,WOOD);r(xx-15,-4,30,4,STONE)
			r(-w/4,-h+40,w/2,6,CREAM)
			text("SHARED SPANS" if revised else "NO FOUNDATIONS",Vector2(-64,-h+30),AMBER)
		"threshold":
			r(l - 5, -8, w + 10, 10, WOOD); r(l - 5, -8, w + 10, 2, CREAM)
			for xx in range(int(l), int(w / 2), 9): r(xx, -5, 4, 5, STONE)
			var label_width: float = FONT.get_string_size(str(definition.label), HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
			r(-label_width / 2 - 3, -27, label_width + 6, 17, INK)
			text(str(definition.label), Vector2(-label_width / 2, -14), AMBER)
		"door", "stairs":
			r(l, -h, w, h, INK); r(l + 3, -h + 3, w - 6, h - 3, WOOD)
			if kind == "stairs":
				for yy in range(0, int(h), 7):
					r(l + 5, -yy - 5, w - 10, 4, STONE); r(l + 5, -yy - 5, w - 10, 1, CREAM)
			else:
				r(l + 6, -h + 7, w - 12, h - 14, Color("283866"))
				r(-1, -h + 7, 2, h - 10, WOOD); r(w / 2 - 11, -20, 3, 3, AMBER)
			r(l - 3, -3, w + 6, 4, STONE)
			var locked: bool = false
			for required: String in definition.get("requires", []):
				if not flags.get(required, false): locked = true
			if locked: r(l + 5, -13, w - 10, 5, RUST)
			text(str(definition.label), Vector2(l, -h - 5), AMBER)
		"lamp":
			r(-3, -h + 15, 6, h - 15, WOOD); r(-7, -4, 14, 4, INK)
			r(-8, -h, 16, 17, INK); r(-6, -h + 2, 12, 12, AMBER)
			r(-4, -h + 3, 7, 9, CREAM); r(-1, -h + 1, 2, 14, WOOD)
		"planter":
			r(l, -h + 16, w, h - 16, WOOD); r(l, -h + 16, w, 4, STONE)
			for x in range(int(l + 4), int(w / 2 - 3), 9):
				r(x, -h + 6, 5, 14, GREEN); r(x - 3, -h + 9, 9, 4, Color("5c897c")); r(x + 2, -h + 4, 3, 3, AMBER)
			r(l + 2, -3, w - 4, 2, INK)
		"tree":
			r(-4, -h + 29, 8, h - 29, WOOD); r(-1, -h + 29, 2, h - 29, STONE)
			var sway: int = roundi(sin(elapsed * 1.2))
			for branch: Vector2 in [Vector2(-17, 19), Vector2(15, 15), Vector2(0, 2), Vector2(-22, 4), Vector2(23, 3)]:
				r(branch.x - 13 + sway, -h + branch.y, 27, 20, GREEN)
				r(branch.x - 10 + sway, -h + branch.y + 2, 17, 9, Color("53624d"))
		"bench", "seats":
			r(l, -h, w, h - 10, INK); r(l + 3, -h + 3, w - 6, h - 16, BLUE)
			r(l + 5, -h + 5, w - 10, 2, Color("6b81bf")); r(l - 2, -13, w + 4, 6, WOOD)
			r(l, -12, w, 2, CREAM); r(l + 7, -7, 4, 7, INK); r(w / 2 - 11, -7, 4, 7, INK)
		"table", "workbench", "desk", "mixer", "sorting", "pip_table":
			r(l + 6, -h + 15, 5, h - 15, INK); r(w / 2 - 11, -h + 15, 5, h - 15, INK)
			r(l, -h + 10, w, 14, WOOD); r(l + 1, -h + 10, w - 2, 4, STONE)
			r(l + 4, -h + 10, w - 8, 1, CREAM)
			if kind == "mixer" and flags.get("mixer_returned", false):
				r(-28, -h - 4, 56, 15, INK); r(-25, -h - 2, 50, 10, Color("353047"))
				for xx in range(-22, 22, 7): r(xx, -h, 2, 7, CREAM); r(xx - 1, -h + 3, 4, 2, AMBER)
			elif kind == "pip_table":
				if flags.get("pip_joined", false): r(-18, -h + 3, 36, 7, CREAM); r(-15, -h + 5, 25, 1, WOOD)
				else:
					draw_set_transform(Vector2(0, -h + 16))
					NativeCastArt.draw_body(self, "pip", "idle", 36, elapsed, reduced_motion)
					draw_set_transform(Vector2.ZERO)
			else:
				for xx in [l + 10, w / 2 - 28]: r(xx, -h + 1, 18, 8, CREAM); r(xx + 3, -h + 3, 11, 1, RUST)
				if kind == "workbench": r(-9, -h + 2, 19, 3, AMBER); r(-2, -h - 1, 3, 8, BLUE)
				if kind == "sorting": r(-20, -h - 9, 23, 19, BLUE); r(-17, -h - 6, 17, 3, CREAM); r(9, -h - 3, 24, 13, RUST)
		"notice", "sign", "panel", "ticket":
			r(l, -h, w, h, INK); r(l + 2, -h + 2, w - 4, h - 4, WOOD)
			r(l + 4, -h + 4, w - 8, h - 8, CREAM)
			if kind == "sign": text(str(definition.label), Vector2(l + 6, -h + 17), WOOD)
			elif kind == "ticket": r(l + 9, -h + 10, w - 18, 16, BLUE); r(-6, -h + 23, 12, 26, CREAM); text("ONE", Vector2(l + 5, -5), WOOD)
			elif kind == "panel":
				for yy in range(-int(h) + 8, -8, 9): r(l + 8, yy, w - 16, 4, INK); r(l + 10, yy, 4, 4, AMBER)
			else:
				for yy in range(-int(h) + 10, -8, 6): r(l + 7, yy, w - 14, 1, RUST)
				text(str(definition.label), Vector2(l, -h - 5), AMBER)
		"shelf":
			r(l, -h, w, h, INK); r(l + 3, -h + 3, w - 6, h - 5, WOOD)
			for yy in range(-int(h) + 22, -5, 24):
				r(l + 3, yy, w - 6, 3, STONE)
				for xx in range(int(l + 8), int(w / 2 - 8), 19):
					r(xx, yy - 16, 13, 15, BLUE if (xx + yy) % 3 == 0 else RUST); r(xx + 2, yy - 14, 9, 2, CREAM)
		"booth": NativeCastArt.draw_body(self, "booth", pose, h, elapsed, reduced_motion)
		"bike":
			for xx in [-21, 21]: draw_arc(Vector2(xx, -11), 11, 0, TAU, 16, INK, 3); draw_arc(Vector2(xx, -11), 8, 0, TAU, 16, STONE, 1)
			draw_polyline(PackedVector2Array([Vector2(-21, -11), Vector2(-7, -26), Vector2(5, -11), Vector2(-21, -11), Vector2(13, -27), Vector2(21, -11)]), BLUE, 3)
			r(9, -31, 11, 3, CREAM); r(-11, -29, 12, 3, INK)
		"shelter":
			r(l, -h, w, 7, WOOD); r(l + 5, -h + 7, 4, h - 7, INK); r(w / 2 - 9, -h + 7, 4, h - 7, INK)
			r(l + 11, -h + 9, w - 22, 29, Color("42505f")); r(-2, -h + 9, 3, 29, STONE)
			r(l + 6, -h - 19, w - 12, 17, INK)
			text("CAMPUS BUS", Vector2(l + 13, -h - 5), CREAM)
		"rail":
			for xx in range(int(l), int(w / 2), 18): r(xx, -h, 3, h, STONE)
			r(l - 2, -h, w + 4, 5, CREAM); r(l, -h + 5, w, 2, WOOD)
		"stage", "step":
			r(l, -h, w, h, WOOD); r(l, -h, w, 5, STONE)
			for yy in range(-int(h) + 8, 0, 13): r(l + 2, yy, w - 4, 1, INK)
			if kind == "stage":
				r(l + 9, -h - 24, 32, 23, INK); r(w / 2 - 42, -h - 24, 32, 23, INK)
				text("LAST LIGHT / SOUND CHECK", Vector2(-110, -h - 7), AMBER)
		"speaker":
			r(l, -h, w, h, INK); r(l + 3, -h + 3, w - 6, h - 6, WOOD)
			for yy in [-h * 0.7, -h * 0.3]: draw_arc(Vector2(0, yy), w * 0.3, 0, TAU, 12, CREAM, 2)
		"arcade", "scoreboard", "return": _draw_dynamic(kind, w, h, l)
		"mural":
			r(l, -h, w, h, WOOD); r(l + 3, -h + 3, w - 6, h - 6, BLUE)
			draw_colored_polygon(PackedVector2Array([Vector2(l + 6, -8), Vector2(-8, -h + 13), Vector2(4, -h + 25), Vector2(17, -h + 8), Vector2(w / 2 - 6, -8)]), STONE)
			r(l + 6, -11, w - 12, 4, GREEN)
		"cart":
			r(l, -h, w, h - 8, WOOD); r(l + 3, -h + 3, w - 6, h - 15, GREEN)
			r(l + 6, -6, 8, 6, INK); r(w / 2 - 14, -6, 8, 6, INK)
			for xx in range(int(l + 6), int(w / 2 - 6), 10): r(xx, -h - 7, 6, 9, AMBER)

	_draw_state_details(kind, w, h, l)

func _draw_dynamic(kind: String, w: float, h: float, l: float) -> void:
	if kind == "arcade":
		r(l, -h, w, h - 1, INK); r(l + 4, -h + 4, w - 8, 37, RUST)
		r(l + 7, -h + 9, w - 14, 27, Color("283866")); r(l + 3, -35, w - 6, 8, CREAM)
		r(l + 5, -23, w - 10, 18, Color("353047"))
		var changed: bool = flags.get("discovery_arcade_seen", false) and definition.get("object") == "arcade_button"
		var runner: int = floori(fmod(elapsed * 5, w - 20)) if changed else 8 + floori(sin(elapsed * 3) * 2)
		r(l + 9 + runner, -h + 27, 4, 5, AMBER); r(l + w - 18, -h + 25, 3, 9, GREEN)
		r(l + 10, -35 if changed else -32, 4, 3, RUST); r(w / 2 - 11, -33, 3, 2, BLUE)
	elif kind == "scoreboard":
		r(-3, -41, 6, 39, INK); r(l, -h, w, 32, INK)
		r(l + 3, -h + 3, w - 6, 26, Color("283866"))
		text("NAMES" if flags.get("pinpal_resolution", "") == "forceful" else "NEXT UP", Vector2(l + 7, -h + 15), AMBER)
		for yy in [-h + 20, -h + 24]: r(l + 8, yy, w - 16, 1, CREAM)
		if flags.get("pinpal_resolution", "") == "forceful": r(w / 2 - 14, -h + 25, 16, 10, CREAM); r(w / 2 - 11, -h + 29, 9, 1, RUST)
	else:
		r(l, -38, w, 31, INK); r(l + 3, -36, w - 6, 23, WOOD)
		r(l + 4, -12, w - 8, 5, CREAM); r(l + 5, -7, 4, 7, INK); r(w / 2 - 9, -7, 4, 7, INK)
		var outcome: String = flags.get("pinpal_resolution", "")
		var shift: float = roundf(sin(elapsed * 3) * 7) if outcome.is_empty() else 0.0
		var ball := Vector2(shift, -24)
		if outcome == "forceful":
			draw_polyline(PackedVector2Array([Vector2(-9,-34),Vector2(2,-28),Vector2(-4,-19),Vector2(9,-13)]), INK, 2)
			draw_polyline(PackedVector2Array([Vector2(w / 2,-9),Vector2(w / 2+7,-6),Vector2(w / 2+11,-9)]), INK, 2)
			r(w / 2 + 2, -15, 18, 3, WOOD); ball = Vector2(w / 2 + 11, -21)
		draw_circle(ball, 6, BLUE); r(ball.x - 2, ball.y - 3, 2, 2, CREAM)

func _draw_state_details(kind: String, w: float, h: float, l: float) -> void:
	match kind:
		"flyer_note":
			r(-14, -h, 28, 14, CREAM); r(-10, -h + 4, 19, 1, RUST); r(-10, -h + 8, 14, 1, WOOD)
			r(-28, -22, 5, 11, INK)
			draw_polyline(PackedVector2Array([Vector2(-38,-20),Vector2(-28,-25),Vector2(-23,-13),Vector2(-14,-13)]), WOOD, 3)
			r(-28, -24, 4, 3, RUST)
		"bike": r(8, -25, 10, 7, CREAM); r(10, -23, 6, 1, WOOD)
		"stage":
			if definition.get("object") != "stage": return
			r(-17, -17, 34, 15, CREAM)
			for yy in [-13, -9, -5]: r(-13, yy, 25, 1, WOOD)
			if flags.has("flyer_resolution"): r(-14, -6, 27, 1, RUST)
		"table":
			if definition.get("object") == "invitation" and flags.has("flyer_resolution"):
				r(-9, -h, 18, 9, CREAM); r(-6, -h + 3, 12, 1, WOOD)
				if flags.flyer_resolution == "peaceful":
					r(l + 5, -h + 3, 12, 3, WOOD); r(-8, -h + 1, 2, 2, AMBER); r(6, -h + 1, 2, 2, AMBER)
		"ticket":
			if flags.get("claim_resolution", "") == "forceful":
				r(-9, -h + 24, 21, 9, INK); r(-5, -h + 28, 7, 2, RUST)
				for xx in [-11, 8]: r(xx, -17, 13, 9, CREAM); r(xx + 5, -19, 2, 13, BLUE)
		"shelf":
			if definition.get("object") != "lost_labels": return
			var moved: int = 11 if flags.get("claim_resolution", "") == "peaceful" else 0
			r(l + 10 + moved, -32, 21, 10, RUST); r(l + 12 + moved, -29, 17, 2, CREAM)
			r(l + 13 + moved, -40, 13, 7, CREAM); r(l + 16 + moved, -38, 7, 1, WOOD)
			r(w / 2 - 26, -38, 11, 16, BLUE); r(w / 2 - 27, -39, 13, 3, INK)
			if flags.get("claim_resolution", "") == "peaceful": text("PASS ON", Vector2(l + 3, -6), AMBER)
			elif flags.get("claim_resolution", "") == "forceful":
				r(l - 5, -5, 100, 17, INK)
				text("SORT LATER", Vector2(l - 3, 8), AMBER)
				for xx in [-16, 5]: r(xx, -17, 16, 8, CREAM); r(xx + 7, -18, 2, 11, BLUE)
		"cart":
			if definition.get("object") != "mags_checklist": return
			r(-15, -h + 7, 30, 24, CREAM)
			for index: int in range(3):
				r(-11, -h + 10 + index * 6, 4, 4, WOOD); r(-10, -h + 11 + index * 6, 2, 2, CREAM)
				if (index == 0 and flags.get("discovery_mags_checklist_seen", false)) or (index < 2 and flags.get("opening_finished", false)): r(-10, -h + 12 + index * 6, 3, 1, BLUE)
				r(-4, -h + 11 + index * 6, 15, 1, WOOD)
			draw_arc(Vector2(7, -h + 24), 3, 0, TAU, 8, WOOD, 1)
			r(4, -h + 27, 1, 4, WOOD); r(9, -h + 27, 1, 4, WOOD)
			if flags.get("opening_finished", false): r(10, -h + 23, 5, 1, WOOD)
