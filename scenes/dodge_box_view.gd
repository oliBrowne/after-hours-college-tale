class_name DodgeBoxView
extends Node2D
## Draws a DodgeBox pattern. The frame node draws the box and clips everything
## drawn by its child (bullets, props, soul) to the box, rotation included.
## The over node draws what sits outside or on top: border, rigs, beams, banners.
## Each boss script draws its own scenery through draw_under / draw_over and any
## custom bullet shapes through draw_bullet (see core/DODGE_PATTERNS.md); this
## view draws the box, soul, objectives, built-in bullet shapes and effects.

const INK: Color = Color("0d101c")
const FILL: Color = Color("0a0c17")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const PLUM: Color = Color("292638")
const ROSE: Color = Color("e8837b")
const BLUE: Color = Color("8fb3ea")
const LILAC: Color = Color("a68db8")
const D = preload("res://core/dodge_box.gd")

var pattern: Dictionary = {}
var offset: Vector2 = Vector2(192, 166)
var font: Font
var frame: Node2D
var inner: Node2D
var over: Node2D
## Where the box may be drawn: between the side panels (screen x 172 and 468), under the foe card
## and above the action button (y 291). A box turned or grown past it is drawn shifted and, if
## still too big, scaled down about its centre, so it never covers the HUD. Only the drawing moves:
## the pattern's own geometry (and so the fight) is unchanged.
const SAFE: Rect2 = Rect2(174, 112, 292, 176)
var fit_scale: float = 1.0
var fit_shift: Vector2 = Vector2.ZERO

func _ready() -> void:
	z_index = 210
	font = load("res://assets/art/afterhours-font.fnt")
	frame = Node2D.new()
	frame.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	add_child(frame)
	inner = Node2D.new()
	frame.add_child(inner)
	over = Node2D.new()
	add_child(over)
	frame.draw.connect(_draw_frame)
	inner.draw.connect(_draw_inner)
	over.draw.connect(_draw_over)
	visible = false

func show_pattern(next: Dictionary, at: Vector2) -> void:
	pattern = next; offset = at
	_fit()
	visible = true
	frame.queue_redraw(); inner.queue_redraw(); over.queue_redraw()

func hide_box() -> void:
	visible = false
	fit_scale = 1.0; fit_shift = Vector2.ZERO
	position = Vector2.ZERO; scale = Vector2.ONE

## Screen bounds of the turned box outline.
func _bounds() -> Rect2:
	var points: PackedVector2Array = D.corners(pattern)
	var bounds: Rect2 = Rect2(points[0] + offset, Vector2.ZERO)
	for point: Vector2 in points: bounds = bounds.expand(point + offset)
	return bounds

func _fit() -> void:
	var bounds: Rect2 = _bounds()
	var centre: Vector2 = offset + D.centre(pattern)
	var target: float = minf(1.0, minf(SAFE.size.x / maxf(1.0, bounds.size.x), SAFE.size.y / maxf(1.0, bounds.size.y)))
	var scaled: Rect2 = Rect2(centre + (bounds.position - centre) * target, bounds.size * target)
	var shift: Vector2 = Vector2.ZERO
	if scaled.end.y > SAFE.end.y: shift.y = SAFE.end.y - scaled.end.y
	if scaled.position.y + shift.y < SAFE.position.y: shift.y = SAFE.position.y - scaled.position.y
	if scaled.end.x > SAFE.end.x: shift.x = SAFE.end.x - scaled.end.x
	if scaled.position.x + shift.x < SAFE.position.x: shift.x = SAFE.position.x - scaled.position.x
	# Ease toward the fit so a turning box glides rather than jumps.
	fit_scale = lerpf(fit_scale, target, 0.35) if absf(fit_scale - target) > 0.002 else target
	fit_shift = fit_shift.lerp(shift, 0.35) if fit_shift.distance_to(shift) > 0.2 else shift
	scale = Vector2(fit_scale, fit_scale)
	position = (centre * (1.0 - fit_scale) + fit_shift).round() if fit_scale == 1.0 else centre * (1.0 - fit_scale) + fit_shift

## Screen point -> arena point, undoing the fit (for pointer steering).
func to_arena(screen: Vector2) -> Vector2:
	return (screen - position) / maxf(0.01, fit_scale) - offset

func _w(p: Vector2) -> Vector2:
	return offset + p

func _box_point(local: Vector2) -> Vector2:
	return offset + D.to_world(pattern, local)

## Public helpers for boss scripts: screen position of an arena-space point,
## of a box-space point, a rotated quad, a chevron, and the view's font.
func arena_point(p: Vector2) -> Vector2:
	return offset + p

func box_point(local: Vector2) -> Vector2:
	return offset + D.to_world(pattern, local)

func box_rect_poly(local: Rect2) -> PackedVector2Array:
	return PackedVector2Array([box_point(local.position), box_point(Vector2(local.end.x, local.position.y)), box_point(local.end), box_point(Vector2(local.position.x, local.end.y))])

func quad(at: Vector2, hw: float, hh: float, turn: float) -> PackedVector2Array:
	return _quad(at, hw, hh, turn)

func chevron(c: CanvasItem, at: Vector2, dir: Vector2, color: Color) -> void:
	_chevron(c, at, dir, color)

func text(c: CanvasItem, at: Vector2, words: String, color: Color, width: float = 200.0) -> void:
	if font != null: c.draw_string(font, at + Vector2(-width * 0.5, 0), words, HORIZONTAL_ALIGNMENT_CENTER, width, 12, color)

func _script() -> GDScript:
	return D.script_for(str(pattern.encounterId))

func _draw_frame() -> void:
	if pattern.is_empty(): return
	var points: PackedVector2Array = D.corners(pattern)
	for i: int in range(points.size()): points[i] += offset
	frame.draw_colored_polygon(points, FILL)

# ---------------------------------------------------------------- inside the box

func _draw_inner() -> void:
	if pattern.is_empty(): return
	var c: CanvasItem = inner
	var clock: int = int(pattern.clock)
	var walt: bool = pattern.encounterId == "walt"
	if pattern.encounterId in ["walt", "encore"]: _draw_backdrop(c, clock, walt)
	_script().draw_under(c, pattern, self)
	for w: Dictionary in pattern.warnings: _draw_warning_inner(c, w)
	if walt: _draw_walt_props(c)
	elif pattern.encounterId == "encore": _draw_cues(c)
	_draw_objectives(c)
	_draw_lanes(c)
	for b: Dictionary in pattern.bullets:
		if b.collide == "beam": _draw_beam(c, b)
	for b: Dictionary in pattern.bullets:
		if b.collide == "beam" or b.get("target", false): continue
		_draw_bullet(c, b)
	_draw_soul(c)
	for e: Dictionary in pattern.effects: _draw_effect(c, e)

func _draw_backdrop(c: CanvasItem, clock: int, walt: bool) -> void:
	var centre: Vector2 = _w(D.centre(pattern))
	if walt:
		# Wind streaks drift with the current wind; rain patterns get a faint wash.
		var wind: Vector2 = Vector2(pattern.wind)
		var drift: float = wind.x if absf(wind.x) > 0.05 else -0.25
		for i: int in range(14):
			var seed_y: float = fposmod(i * 37.0, 150.0) - 75.0
			var x: float = fposmod(i * 61.0 + clock * drift * 3.0, 340.0) - 170.0
			var a: Vector2 = centre + Vector2(x, seed_y)
			c.draw_line(a, a + Vector2(14.0 * signf(drift), 0), Color(0.6, 0.65, 0.8, 0.08 + absf(wind.x) * 0.12), 1)
	else:
		# Stage floor boards and a beat glow.
		var beat_phase: float = float((clock + int(pattern.musicBase)) % int(pattern.get("beatTicks", 30))) / float(pattern.get("beatTicks", 30))
		var glow: float = 0.05 * (1.0 - beat_phase)
		for i: int in range(-6, 7):
			c.draw_line(centre + Vector2(-200, i * 14.0), centre + Vector2(200, i * 14.0), Color(0.55, 0.4, 0.55, 0.07 + glow), 1)

func _draw_warning_inner(c: CanvasItem, w: Dictionary) -> void:
	var fade: float = 0.5 + 0.5 * sin(float(w.age) * 0.5)
	match str(w.kind):
		"lane":
			var r: Rect2 = Rect2(_w(Vector2(-200, float(w.y) - float(w.h))), Vector2(660, float(w.h) * 2.0)) if w.horizontal else Rect2(_w(Vector2(float(w.x) - float(w.w), -200)), Vector2(float(w.w) * 2.0, 520))
			c.draw_rect(r, Color(ROSE, 0.22 + 0.2 * fade))
			c.draw_rect(r, Color(ROSE, 0.75), false, 1)
		"edge":
			var at: Vector2 = _box_point(Vector2(float(w.x), float(w.y)))
			_chevron(c, at, Vector2(w.dir).rotated(float(pattern.box.rot)), Color(ROSE, 0.5 + 0.5 * fade))
		"puddle":
			var at2: Vector2 = _box_point(Vector2(float(w.x), float(w.y)))
			c.draw_arc(at2, 4.0 + float(w.age) * 0.15, PI, TAU, 10, Color(BLUE, 0.4 + 0.5 * fade), 1)
			c.draw_line(at2 + Vector2(-9, 0), at2 + Vector2(9, 0), Color(BLUE, 0.7), 1)
		"cue":
			var at3: Vector2 = _box_point(Vector2(float(w.x), float(w.y)))
			c.draw_rect(Rect2(at3 - Vector2(9, 10), Vector2(18, 20)), Color(MINT, 0.25 * fade), false, 1)
		"arrows":
			var dir: Vector2 = w.dir
			for i: int in range(5):
				var y: float = -40.0 + i * 20.0
				var x: float = fposmod(float(w.age) * 2.0 * dir.x + i * 30.0, 200.0) - 100.0
				_chevron(c, _box_point(Vector2(x, y)), dir.rotated(float(pattern.box.rot)), Color(AMBER, 0.45))
		"spin":
			var centre: Vector2 = _w(D.centre(pattern))
			var a0: float = float(w.age) * -0.12
			c.draw_arc(centre, 30.0, a0, a0 + 2.0, 12, Color(AMBER, 0.6), 1)
			c.draw_arc(centre, 30.0, a0 + PI, a0 + PI + 2.0, 12, Color(AMBER, 0.6), 1)

func _draw_objectives(c: CanvasItem) -> void:
	for o: Dictionary in pattern.objectives:
		if not (bool(pattern.promised) or o.always): continue
		if not o.active and not o.done: continue
		if o.done and int(pattern.clock) - int(o.doneAt) > 40 and o.kind != "avoid": continue
		var centre: Vector2 = box_point(Vector2(float(o.x), float(o.y)))
		var rect: Rect2 = Rect2(Vector2(float(o.x), float(o.y)) - Vector2(float(o.w), float(o.h)), Vector2(float(o.w), float(o.h)) * 2.0) if float(o.w) > 0.0 else Rect2(Vector2(float(o.x), float(o.y)) - Vector2(9, 10), Vector2(18, 20))
		var poly: PackedVector2Array = box_rect_poly(rect)
		var outline: PackedVector2Array = poly + PackedVector2Array([poly[0]])
		match str(o.kind):
			"avoid":
				c.draw_colored_polygon(poly, Color(Color("6b526a"), 0.35 if not o.broken else 0.6))
				c.draw_polyline(outline, Color("8f6f8c") if not o.broken else ROSE, 2)
				c.draw_line(poly[0], poly[2], Color(PLUM, 0.9), 1)
				c.draw_line(poly[1], poly[3], Color(PLUM, 0.9), 1)
			_:
				if o.done:
					c.draw_colored_polygon(poly, Color(MINT, 0.5))
					c.draw_polyline(PackedVector2Array([centre + Vector2(-4, 0), centre + Vector2(-1, 4), centre + Vector2(5, -4)]), INK, 2)
					continue
				var pulse: float = 0.5 + 0.5 * sin(float(pattern.clock) * 0.2)
				c.draw_colored_polygon(poly, Color(MINT, 0.12 + 0.08 * pulse))
				c.draw_polyline(outline, MINT, 2)
				if o.kind == "hold":
					var fill: float = clampf(float(o.progress) / float(maxi(1, int(o.need))), 0.0, 1.0)
					var base: Vector2 = box_point(Vector2(rect.position.x, rect.end.y + 3.0))
					var tip: Vector2 = box_point(Vector2(rect.position.x + rect.size.x * fill, rect.end.y + 3.0))
					c.draw_line(base, tip, MINT, 2)
				elif o.kind == "confirm":
					c.draw_circle(centre, 2.0 + pulse, Color(MINT, 0.8))
				if not str(o.label).is_empty(): text(c, box_point(Vector2(rect.get_center().x, rect.position.y - 3.0)), str(o.label), MINT)

func _draw_lanes(c: CanvasItem) -> void:
	if str(pattern.soul.mode) != "lanes": return
	var h: Vector2 = D.half(pattern)
	for x: Variant in pattern.lanes:
		c.draw_line(box_point(Vector2(float(x), -h.y)), box_point(Vector2(float(x), h.y)), Color(LILAC, 0.25), 1)

func _chevron(c: CanvasItem, at: Vector2, dir: Vector2, color: Color) -> void:
	var side: Vector2 = Vector2(-dir.y, dir.x)
	c.draw_polyline(PackedVector2Array([at - dir * 3.0 + side * 4.0, at + dir * 2.0, at - dir * 3.0 - side * 4.0]), color, 1)

func _draw_walt_props(c: CanvasItem) -> void:
	if pattern.patternId == "rain":
		var roof: Rect2 = pattern.roof
		var a: Vector2 = _box_point(roof.position)
		var poly: PackedVector2Array = PackedVector2Array([_box_point(roof.position), _box_point(Vector2(roof.end.x, roof.position.y)), _box_point(roof.end), _box_point(Vector2(roof.position.x, roof.end.y))])
		c.draw_colored_polygon(poly, Color("6c5a4a"))
		c.draw_polyline(poly + PackedVector2Array([poly[0]]), AMBER, 1)
		var shade: PackedVector2Array = PackedVector2Array([_box_point(Vector2(roof.position.x, roof.end.y)), _box_point(roof.end), _box_point(Vector2(roof.end.x + float(pattern.slant) * 30.0, roof.end.y + 70.0)), _box_point(Vector2(roof.position.x + float(pattern.slant) * 30.0, roof.end.y + 70.0))])
		c.draw_colored_polygon(shade, Color(0.9, 0.7, 0.35, 0.06))
		c.draw_line(a + Vector2(4, 6), a + Vector2(4, 4), AMBER, 1)
	var local: Vector2 = DodgePatternsWalt.lantern_local(pattern)
	var at: Vector2 = _box_point(local)
	var lit: float = clampf(float(pattern.lantern) / 100.0, 0.0, 1.0)
	var raised: bool = int(pattern.lanternRaised) > 0
	var flicker: float = 0.85 + 0.15 * sin(float(pattern.clock) * 0.37)
	var radius: float = DodgePatternsWalt.LANTERN_REACH
	c.draw_circle(at, radius, Color(0.95, 0.72, 0.32, (0.10 + (0.12 if raised else 0.0)) * lit * flicker))
	c.draw_arc(at, radius, 0, TAU, 28, Color(AMBER, (0.25 + (0.45 if raised else 0.0)) * maxf(0.3, lit)), 1)
	var lift: Vector2 = Vector2(0, -4) if raised else Vector2.ZERO
	c.draw_line(at + lift + Vector2(-2, -7), at + lift + Vector2(2, -7), CREAM, 1)
	c.draw_rect(Rect2(at + lift + Vector2(-3, -6), Vector2(6, 9)), Color("3a3020"))
	c.draw_rect(Rect2(at + lift + Vector2(-2, -4), Vector2(4, 5)), Color(1.0, 0.8, 0.4, 0.3 + 0.7 * lit))
	c.draw_rect(Rect2(at + lift + Vector2(-3, -6), Vector2(6, 9)), AMBER, false, 1)

func _draw_cues(c: CanvasItem) -> void:
	var t: int = int(pattern.clock) - int(pattern.leadIn)
	for cue: Dictionary in pattern.get("cues", []):
		if not cue.placed: continue
		var open: bool = t >= int(cue.t) and t < int(cue.t) + int(cue.open)
		if not open and not cue.got: continue
		if cue.got and t > int(cue.t) + int(cue.open) + 20: continue
		var at: Vector2 = _box_point(Vector2(float(cue.x), float(cue.y)))
		var r: Rect2 = Rect2(at - Vector2(9, 10), Vector2(18, 20))
		if cue.got:
			c.draw_rect(r, Color(MINT, 0.5))
			c.draw_polyline(PackedVector2Array([at + Vector2(-4, 0), at + Vector2(-1, 4), at + Vector2(5, -4)]), INK, 2)
		else:
			var left: float = 1.0 - float(t - int(cue.t)) / float(cue.open)
			c.draw_rect(r, Color(MINT, 0.18))
			c.draw_rect(r, MINT, false, 2)
			c.draw_rect(Rect2(r.position + Vector2(0, 22), Vector2(18.0 * left, 2)), MINT)

func _draw_bullet(c: CanvasItem, b: Dictionary) -> void:
	var at: Vector2 = offset + D.bullet_world(pattern, b)
	var turn: float = float(b.rot) + (float(pattern.box.rot) if b.space == "box" else 0.0)
	var alpha: float = clampf(float(b.fade) / 24.0, 0.0, 1.0) if b.has("fade") else 1.0
	if b.get("friendly", false): alpha *= 0.55
	if _script().draw_bullet(c, b, at, turn, alpha, self): return
	match str(b.shape):
		"paper", "sheet":
			var hw: float = float(b.w); var hh: float = float(b.h)
			var q: PackedVector2Array = _quad(at, hw, hh, turn)
			c.draw_colored_polygon(q, Color(CREAM, alpha))
			var x1: Vector2 = Vector2(-hw + 1.5, -hh * 0.3).rotated(turn); var x2: Vector2 = Vector2(hw - 1.5, -hh * 0.3).rotated(turn)
			c.draw_line(at + x1, at + x2, Color(LILAC, alpha), 1)
			c.draw_line(at + x1 + Vector2(0, hh * 0.6).rotated(turn), at + x2 + Vector2(0, hh * 0.6).rotated(turn), Color(LILAC, alpha), 1)
		"leaf":
			var pts: PackedVector2Array = []
			for i: int in range(8):
				var a: float = i * TAU / 8.0
				pts.append(at + Vector2(cos(a) * float(b.r) * 1.3, sin(a) * float(b.r) * 0.7).rotated(turn))
			c.draw_colored_polygon(pts, Color(Color("c9874a"), alpha))
			c.draw_line(at + Vector2(-float(b.r) * 1.5, 0).rotated(turn), at + Vector2(float(b.r) * 1.2, 0).rotated(turn), Color(Color("6e3f23"), alpha), 1)
		"grit":
			var tri: PackedVector2Array = PackedVector2Array([at + Vector2(0, -3).rotated(turn), at + Vector2(3, 2).rotated(turn), at + Vector2(-2.5, 2.5).rotated(turn)])
			c.draw_colored_polygon(tri, Color(Color("b49a80"), alpha))
		"can":
			c.draw_circle(at, float(b.r), Color(Color("9aa3ad"), alpha))
			c.draw_line(at + Vector2(-float(b.r) + 1, 0).rotated(turn), at + Vector2(float(b.r) - 1, 0).rotated(turn), Color(ROSE, alpha), 2)
		"bag":
			var r: float = float(b.r)
			var blob: PackedVector2Array = []
			for i: int in range(12):
				var a2: float = i * TAU / 12.0
				var wobble: float = 1.0 + 0.12 * sin(a2 * 3.0 + float(b.age) * 0.2)
				blob.append(at + Vector2(cos(a2) * r * wobble, sin(a2) * r * 0.85 * wobble).rotated(turn))
			c.draw_colored_polygon(blob, Color(Color("d9d4c7"), 0.92 * alpha))
			c.draw_arc(at + Vector2(-2.5, -r * 0.8).rotated(turn), 2.5, PI + turn, TAU + turn, 6, Color(Color("8a8478"), alpha), 1)
			c.draw_arc(at + Vector2(2.5, -r * 0.8).rotated(turn), 2.5, PI + turn, TAU + turn, 6, Color(Color("8a8478"), alpha), 1)
		"drop":
			var v: Vector2 = Vector2(float(b.vx), float(b.vy))
			if b.space == "box": v = v.rotated(float(pattern.box.rot))
			c.draw_line(at - v.normalized() * 7.0, at + v.normalized() * 1.0, Color(Color("b8d6f5"), alpha), 2 if float(b.r) > 2.0 else 1)
		"note", "cue_note", "flip_note":
			var colour: Color = MINT if b.shape == "cue_note" else ROSE if b.shape == "flip_note" else AMBER
			colour.a = alpha
			var head: PackedVector2Array = []
			for i: int in range(10):
				var a3: float = i * TAU / 10.0
				head.append(at + Vector2(cos(a3) * 3.6, sin(a3) * 2.6).rotated(-0.45))
			c.draw_colored_polygon(head, colour)
			c.draw_line(at + Vector2(3, -1), at + Vector2(3, -10), colour, 1)
			c.draw_line(at + Vector2(3, -10), at + Vector2(6, -6), colour, 1)
			if b.shape == "flip_note" and int(b.get("flip", 0)) == 0:
				c.draw_arc(at, 7.0, 0, TAU, 12, Color(ROSE, 0.5), 1)
		"squeal":
			var dir: Vector2 = Vector2(float(b.vx), float(b.vy)).normalized()
			var side: Vector2 = Vector2(-dir.y, dir.x)
			c.draw_polyline(PackedVector2Array([at - dir * 6 + side * 2, at - dir * 3 - side * 2, at + side * 2, at + dir * 3 - side * 2]), Color(Color("a6e3e9"), alpha), 1)
			c.draw_circle(at, 1.5, Color(Color("e6fbff"), alpha))
		"confetti":
			var colours: Array[Color] = [AMBER, MINT, ROSE, LILAC]
			var col: Color = colours[int(b.get("hue", 0)) % 4]; col.a = alpha
			c.draw_colored_polygon(_quad(at, 2.5, 1.4 + absf(sin(float(b.age) * 0.2)) * 0.8, turn), col)
		"rose":
			c.draw_line(at, at + Vector2(0, 6).rotated(turn), Color(Color("7aa36b"), alpha), 1)
			c.draw_circle(at, 3.5, Color(Color("c8505a"), alpha))
			c.draw_arc(at, 2.0, turn, turn + 4.5, 6, Color(Color("f09aa0"), alpha), 1)
		"ring":
			var gw: float = float(b.gapWidth) * 0.5
			c.draw_arc(at, float(b.radius), float(b.gap) + gw, float(b.gap) + TAU - gw, maxi(24, int(float(b.radius) * 0.6)), Color(CREAM, 0.95 * alpha), float(b.thick) * 2.0)
			c.draw_arc(at, float(b.radius) - float(b.thick) - 2.0, float(b.gap) + gw, float(b.gap) + TAU - gw, maxi(24, int(float(b.radius) * 0.6)), Color(LILAC, 0.25 * alpha), 1)
		_:
			c.draw_circle(at, float(b.r), Color(CREAM, alpha))

func _quad(at: Vector2, hw: float, hh: float, turn: float) -> PackedVector2Array:
	return PackedVector2Array([at + Vector2(-hw, -hh).rotated(turn), at + Vector2(hw, -hh).rotated(turn), at + Vector2(hw, hh).rotated(turn), at + Vector2(-hw, hh).rotated(turn)])

func _draw_soul(c: CanvasItem) -> void:
	var at: Vector2 = _w(D.soul_world(pattern))
	var mode: String = str(pattern.soul.mode)
	if mode == "green":
		c.draw_arc(at, D.SHIELD_REACH, 0, TAU, 32, Color(MINT, 0.25), 1)
		var dir: Vector2 = pattern.soul.shield
		var side: Vector2 = Vector2(-dir.y, dir.x)
		var mid: Vector2 = at + dir * 12.0
		c.draw_line(mid - side * 8.0, mid + side * 8.0, AMBER, 3)
		c.draw_line(mid - side * 8.0 + dir, mid + side * 8.0 + dir, CREAM, 1)
	if mode == "flipper":
		var lift: float = 6.0 if int(pattern.flipperTicks) > 0 else 0.0
		var left: Vector2 = at + Vector2(-24, 4).rotated(float(pattern.box.rot))
		var right: Vector2 = at + Vector2(24, 4 - lift * 1.5).rotated(float(pattern.box.rot))
		c.draw_line(left, right, MINT if lift > 0.0 else Color(MINT, 0.6), 3)
	if pattern.get("audit", false):
		c.draw_arc(at, 9.0, 0, TAU, 16, Color(ROSE, 0.8), 1)
	if int(pattern.invulnerability) % 8 >= 4: return
	var colour: Color = BLUE if mode == "blue" else MINT if mode == "green" else Color("e0a0d8") if mode == "lanes" else AMBER
	if pattern.soul.get("ducking", false):
		var g2: Vector2 = Vector2(pattern.soul.gravity).rotated(float(pattern.box.rot))
		var low: Vector2 = at + g2 * 2.0
		c.draw_rect(Rect2(low - Vector2(5, 3), Vector2(10, 6)), colour)
		c.draw_circle(low, 1, Color.WHITE)
		return
	c.draw_rect(Rect2(at - Vector2(4, 5), Vector2(8, 9)), colour)
	c.draw_circle(at, 1, Color.WHITE)
	if mode == "blue":
		var g: Vector2 = Vector2(pattern.soul.gravity).rotated(float(pattern.box.rot))
		c.draw_line(at + g * 6.0 + Vector2(-g.y, g.x) * 3.0, at + g * 6.0 - Vector2(-g.y, g.x) * 3.0, Color(BLUE, 0.6), 1)

func _draw_effect(c: CanvasItem, e: Dictionary) -> void:
	var at: Vector2 = _w(Vector2(float(e.x), float(e.y)))
	var p: float = float(e.age) / float(e.life)
	match str(e.kind):
		"graze":
			for i: int in range(4):
				var a: float = i * TAU / 4.0 + 0.6
				c.draw_line(at + Vector2.from_angle(a) * (5 + p * 8), at + Vector2.from_angle(a) * (7 + p * 10), Color(CREAM, 1.0 - p), 1)
		"hit":
			c.draw_arc(at, 4 + p * 16, 0, TAU, 20, Color(ROSE, 1.0 - p), 2)
		"block":
			c.draw_arc(at, 3 + p * 8, 0, TAU, 12, Color(MINT if e.get("cue", false) else AMBER, 1.0 - p), 2)
		"kept":
			c.draw_arc(at, 8 + p * 26, 0, TAU, 28, Color(MINT, 1.0 - p), 2)
		"gutter":
			for i: int in range(5):
				c.draw_circle(at + Vector2(-6 + i * 3, -p * 14 - i), 2 + p * 3, Color(0.6, 0.6, 0.65, 0.5 * (1.0 - p)))
		"lantern":
			c.draw_arc(at, 6 + p * 20, 0, TAU, 24, Color(AMBER, 1.0 - p), 1)
		"splash":
			c.draw_circle(at + Vector2(-2, -p * 3), 1, Color(BLUE, 1.0 - p))
			c.draw_circle(at + Vector2(2, -p * 3), 1, Color(BLUE, 1.0 - p))
		"mode":
			c.draw_arc(at, 20 - p * 14, 0, TAU, 20, Color(CREAM, 1.0 - p), 1)

# ---------------------------------------------------------------- outside / on top

func _draw_over() -> void:
	if pattern.is_empty(): return
	var c: CanvasItem = over
	if pattern.patternId == "curtain_call": _draw_curtains(c)
	for rig: Vector2 in pattern.get("rigs", []): _draw_rig(c, _w(rig))
	for b: Dictionary in pattern.bullets:
		if b.collide == "beam" and int(b.age) >= int(b.warn):
			c.draw_circle(_w(Vector2(float(b.x), float(b.y))) + Vector2(0, 4), 6.0, Color(1.0, 0.95, 0.75, 0.5))
	for speaker: Vector2 in pattern.get("speakers", []): _draw_speaker(c, _w(speaker))
	for e: Dictionary in pattern.effects:
		if e.kind == "pulse":
			var p: float = float(e.age) / float(e.life)
			c.draw_arc(_w(Vector2(float(e.x), float(e.y))), 8 + p * 10, 0, TAU, 16, Color(CREAM, 0.6 * (1.0 - p)), 1)
	var points: PackedVector2Array = D.corners(pattern)
	for i: int in range(points.size()): points[i] += offset
	points.append(points[0])
	# Notes aimed at the green soul are drawn outside the box too, so you can
	# read them coming from a distance (as in Undyne's spears).
	for b: Dictionary in pattern.bullets:
		if b.get("target", false): _draw_bullet(c, b)
	var border: Color = MINT if pattern.get("beatPulse", false) else AMBER
	if pattern.soul.mode == "blue": border = border.lerp(BLUE, 0.5)
	c.draw_polyline(points, border, 2)
	for w: Dictionary in pattern.warnings:
		if w.kind == "gust": _draw_gust(c, w)
		elif w.kind == "flip" or w.kind == "curtain": _draw_squeeze(c, w)
	if int(pattern.bannerTicks) > 0 and font != null:
		# Attack callouts sit on their own dark plate just clear of the (turned) box outline, so
		# the border never strikes through them and the backdrop never swallows them.
		var colour: Color = Color(pattern.get("bannerColor", ROSE if pattern.encounterId == "walt" else MINT))
		var words: String = str(pattern.banner)
		var width: float = font.get_string_size(words, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
		var bottom: float = roundf(_bounds().position.y - 4.0)
		var plate: Rect2 = Rect2(Vector2(roundf(_w(D.centre(pattern)).x - width * 0.5 - 6.0), bottom - 16.0), Vector2(roundf(width + 12.0), 16.0))
		c.draw_rect(plate, Color(INK, 0.92))
		c.draw_rect(plate, Color(colour, 0.7), false, 1)
		if int(pattern.bannerTicks) % 16 < 11:
			c.draw_string(font, Vector2(plate.position.x + 6.0, bottom - 4.0), words, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, colour)
	_script().draw_over(c, pattern, self)

func _draw_beam(c: CanvasItem, b: Dictionary) -> void:
	var origin: Vector2 = _w(Vector2(float(b.x), float(b.y)))
	var dir: Vector2 = Vector2.from_angle(float(b.angle))
	var side: Vector2 = Vector2(-dir.y, dir.x)
	var tip: Vector2 = origin + dir * float(b.len)
	var lit: bool = int(b.age) >= int(b.warn)
	if not lit:
		var p: float = float(b.age) / float(b.warn)
		c.draw_line(origin + side * float(b.w0) * 0.5, tip + side * float(b.w1) * 0.5, Color(ROSE, 0.25 + 0.5 * p), 1)
		c.draw_line(origin - side * float(b.w0) * 0.5, tip - side * float(b.w1) * 0.5, Color(ROSE, 0.25 + 0.5 * p), 1)
		return
	var left: int = int(b.warn) + int(b.live) - int(b.age)
	var alpha: float = clampf(float(left) / 8.0, 0.0, 1.0)
	var cone: PackedVector2Array = PackedVector2Array([origin + side * float(b.w0) * 0.5, tip + side * float(b.w1) * 0.5, tip - side * float(b.w1) * 0.5, origin - side * float(b.w0) * 0.5])
	c.draw_colored_polygon(cone, Color(1.0, 0.93, 0.7, 0.45 * alpha))
	var core: PackedVector2Array = PackedVector2Array([origin + side * float(b.w0) * 0.2, tip + side * float(b.w1) * 0.2, tip - side * float(b.w1) * 0.2, origin - side * float(b.w0) * 0.2])
	c.draw_colored_polygon(core, Color(1.0, 0.98, 0.88, 0.35 * alpha))

func _draw_curtains(c: CanvasItem) -> void:
	var h: Vector2 = D.half(pattern)
	var centre: Vector2 = _w(D.centre(pattern))
	var full: float = 134.0
	if h.x >= full - 2.0: return
	for side: float in [-1.0, 1.0]:
		var inner_x: float = centre.x + side * h.x
		var outer_x: float = centre.x + side * full
		var r: Rect2 = Rect2(Vector2(minf(inner_x, outer_x), centre.y - h.y), Vector2(absf(outer_x - inner_x), h.y * 2.0))
		c.draw_rect(r, Color("5a2030"))
		var x: float = r.position.x + 3.0
		while x < r.end.x:
			c.draw_line(Vector2(x, r.position.y), Vector2(x, r.end.y), Color("3a1420"), 1)
			x += 6.0
		c.draw_line(Vector2(inner_x, r.position.y), Vector2(inner_x, r.end.y), Color("c8505a"), 1)

func _draw_rig(c: CanvasItem, at: Vector2) -> void:
	c.draw_line(at + Vector2(0, -14), at + Vector2(0, -6), Color("4a4458"), 2)
	c.draw_rect(Rect2(at + Vector2(-7, -6), Vector2(14, 10)), Color("2c2838"))
	c.draw_rect(Rect2(at + Vector2(-7, -6), Vector2(14, 10)), LILAC, false, 1)
	c.draw_circle(at + Vector2(0, 4), 4, AMBER)

func _draw_speaker(c: CanvasItem, at: Vector2) -> void:
	c.draw_rect(Rect2(at + Vector2(-11, -18), Vector2(22, 36)), Color("1e1b28"))
	c.draw_rect(Rect2(at + Vector2(-11, -18), Vector2(22, 36)), LILAC, false, 1)
	c.draw_circle(at + Vector2(0, 5), 7, Color("3a3448"))
	c.draw_arc(at + Vector2(0, 5), 7, 0, TAU, 16, CREAM, 1)
	c.draw_circle(at + Vector2(0, -10), 3, Color("3a3448"))

func _draw_gust(c: CanvasItem, w: Dictionary) -> void:
	var dir: Vector2 = w.dir
	var h: Vector2 = D.half(pattern)
	var p: float = float(w.age) / float(w.life)
	for i: int in range(3):
		var y: float = -h.y * 0.6 + i * h.y * 0.6
		var start: Vector2 = _box_point(Vector2(-dir.x * (h.x + 22.0), y))
		var shift: float = fposmod(float(w.age) * 1.5 + i * 7.0, 14.0)
		for j: int in range(2):
			_chevron(c, start + Vector2(dir.x * (shift + j * 6.0), 0), Vector2(signf(dir.x), 0), Color(ROSE, 0.4 + 0.6 * p))

func _draw_squeeze(c: CanvasItem, w: Dictionary) -> void:
	var h: Vector2 = D.half(pattern)
	var p: float = float(w.age) / float(w.life)
	var col: Color = Color(ROSE, 0.3 + 0.6 * p)
	if w.kind == "curtain":
		for side: float in [-1.0, 1.0]:
			var at: Vector2 = _box_point(Vector2(side * (h.x + 8.0), 0))
			_chevron(c, at, Vector2(-side, 0), col)
			_chevron(c, at + Vector2(0, -16), Vector2(-side, 0), col)
			_chevron(c, at + Vector2(0, 16), Vector2(-side, 0), col)
	else:
		for x: float in [-0.6, 0.0, 0.6]:
			_chevron(c, _box_point(Vector2(h.x * x, -h.y - 10.0)), Vector2(0, -1).rotated(float(pattern.box.rot)), col)
			_chevron(c, _box_point(Vector2(h.x * x, h.y + 10.0)), Vector2(0, 1).rotated(float(pattern.box.rot)), col)
