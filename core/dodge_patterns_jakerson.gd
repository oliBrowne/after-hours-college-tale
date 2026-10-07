extends RefCounted
## JAKERSON / practice spar on the UMC terrace. The friendly first fight: it only
## exists to teach the defend box. Three slow, heavily telegraphed attacks, one
## per turn, cycling in order. Hits do very little (ENEMY_DAMAGE 3).
## The promise: three "commits" (mint boxes) show up one after another; stand in
## each and press confirm while promised. Every commit sits away from the
## current danger and stays for as long as it takes.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["falling_code", "loading_bar", "tennis_rally"]
const PHASES: Array[int] = [0, 1]
const COMMITS: int = 3

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const BLUE: Color = Color("8fb3ea")
const LILAC: Color = Color("a68db8")
const ROSE: Color = Color("e8837b")
const BALL: Color = Color("d8e86a")
const GLYPHS: Array[String] = ["0", "1", "{", "}", ";", "<", ">", "#"]

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 400 + 40 * clampi(int(s.phase), 0, 1)
	s.commitSpots = []
	s.bars = []
	match id:
		"falling_code":
			s.phaseName = "Falling Code"
			s.hint = "Red bands warn where code will drop. Step out of them. Green boxes: stand inside, press Z."
			s.commitSpots = [Vector2(-0.6, 0.45), Vector2(0.6, 0.45), Vector2(0.0, -0.4)]
		"loading_bar":
			s.phaseName = "Loading Bar"
			s.hint = "A loading bar sweeps across. Slip through its gap. Green boxes: stand inside, press Z."
			s.commitSpots = [Vector2(0.62, -0.42), Vector2(-0.62, 0.42), Vector2(0.62, 0.42)]
		"tennis_rally":
			s.phaseName = "Tennis Rally"
			s.hint = "Jakerson serves soft bounces along the floor. Stay high between them. Catch the commits."
			s.commitSpots = [Vector2(-0.55, -0.5), Vector2(0.15, -0.55), Vector2(0.6, -0.5)]
	for i: int in range(COMMITS):
		D.objective(s, {"kind": "confirm", "r": 13.0, "label": "commit" if i == 0 else "", "active": false, "x": 0.0, "y": 0.0})

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return _caught(s) >= COMMITS

static func progress(s: Dictionary) -> String:
	return "Commits caught %d/%d" % [_caught(s), COMMITS]

static func _caught(s: Dictionary) -> int:
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	return count

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	match str(s.patternId):
		"falling_code": _falling_code(s, t, phase)
		"loading_bar": _loading_bar(s, t, phase)
		"tennis_rally": _tennis_rally(s, t, phase)
	_commits(s, t)

static func after(s: Dictionary, _t: int) -> void:
	# Bars are drawn and collide as one wall with a gap; the blocks are bullets.
	pass

# ---------------------------------------------------------------- commits

## One commit at a time: the next appears 24 ticks after the last was caught.
static func _commits(s: Dictionary, t: int) -> void:
	var h: Vector2 = D.half(s)
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		var spot: Vector2 = Vector2(s.commitSpots[i]) * h
		o.x = spot.x; o.y = spot.y
		var ready: bool = t >= 40 if i == 0 else last_done >= 0 and int(s.clock) - last_done >= 24
		o.active = ready
		if ready and not bool(o.get("shown", false)):
			o.shown = true
			D.effect(s, "pulse", D.to_world(s, spot), 18)
		return

# ---------------------------------------------------------------- attacks

## Falling Code: a red band shows a column, then three glyphs drift down it.
## Every other column is the one you stand in, so you learn to step aside.
static func _falling_code(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 200.0, "h": 112.0}, 30)
	var every: int = 46 if phase == 0 else 38
	if t % every == 10 and t < int(s.length) - 110:
		var h: Vector2 = D.half(s)
		var x: float = float(s.soul.x) if int(t / every) % 2 == 0 else D.rand_range(s, -h.x + 14.0, h.x - 14.0)
		x = clampf(x, -h.x + 12.0, h.x - 12.0)
		D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 9.0, "horizontal": false}, 36, int(t / every) % 3 == 0)
		for i: int in range(3):
			D.shot(s, {"space": "box", "x": x, "y": -h.y - 8.0 - i * 18.0, "vy": 0.95 + phase * 0.15, "r": 4.0, "shape": "glyph", "glyph": GLYPHS[int(D.rand(s) * GLYPHS.size())], "arm": 36, "hold": true, "life": 300})

## Loading Bar: a column of blocks with one gap sweeps from left to right. The
## gap is outlined in amber while the bar loads at the edge.
static func _loading_bar(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 220.0, "h": 108.0}, 30)
	var every: int = 120 if phase == 0 else 96
	if t % every == 10 and t < int(s.length) - 150:
		var h: Vector2 = D.half(s)
		var from_left: bool = int(t / every) % 2 == 0
		var gap_y: float = (1.0 if float(s.soul.y) < 0.0 else -1.0) * D.rand_range(s, 16.0, h.y - 22.0)
		var gap: float = 22.0 if phase == 0 else 18.0
		var side: float = -1.0 if from_left else 1.0
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": gap_y + gap + 10.0, "dir": Vector2(-side, 0)}, 44, true)
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": gap_y - gap - 10.0, "dir": Vector2(-side, 0)}, 44)
		s.bars.append({"gapY": gap_y, "gap": gap, "side": side, "until": int(s.clock) + 44})
		var y: float = -h.y + 5.0
		while y < h.y:
			if absf(y - gap_y) > gap:
				D.shot(s, {"space": "box", "x": side * (h.x + 6.0), "y": y, "vx": -side * (0.9 + phase * 0.15), "collide": "rect", "w": 4.0, "h": 4.5, "shape": "block", "hold": true, "arm": 44, "life": 44 + 300})
			y += 10.0
	if phase > 0 and t % 70 == 40 and t < int(s.length) - 110:
		var h2: Vector2 = D.half(s)
		D.shot(s, {"space": "box", "x": D.rand_range(s, -h2.x + 20.0, h2.x - 20.0), "y": -h2.y - 6.0, "vy": 0.9, "r": 4.0, "shape": "glyph", "glyph": "%", "life": 220})

## Tennis Rally: soft serves bounce along the floor from the right, one at a
## time; stay up high and they pass under you. Phase 1 serves from both sides.
static func _tennis_rally(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 216.0, "h": 112.0}, 30)
	var every: int = 58 if phase == 0 else 46
	if t % every == 12 and t < int(s.length) - 100:
		var h: Vector2 = D.half(s)
		var side: float = 1.0 if phase == 0 or int(t / every) % 2 == 0 else -1.0
		var y: float = h.y - 20.0
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": y, "dir": Vector2(-side, 0)}, 32, int(t / every) % 2 == 0)
		D.shot(s, {"space": "box", "x": side * (h.x + 6.0 + 1.3 * 32.0), "y": y, "vx": -side * 1.3, "vy": -2.8, "ay": 0.05, "bounce": 0.8, "r": 4.5, "shape": "tennis", "spin": 0.15 * side, "life": 340})

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	match str(s.patternId):
		"tennis_rally":
			# A court: baseline, service line, net post shadows.
			c.draw_line(v.box_point(Vector2(-h.x, h.y - 6.0)), v.box_point(Vector2(h.x, h.y - 6.0)), Color(CREAM, 0.18), 1)
			c.draw_line(v.box_point(Vector2(0, -h.y)), v.box_point(Vector2(0, h.y)), Color(CREAM, 0.08), 1)
		_:
			# Editor gutter: faint line numbers down the left edge.
			var y: float = -h.y + 10.0
			var n: int = 1
			while y < h.y:
				v.text(c, v.box_point(Vector2(-h.x + 8.0, y + 4.0)), str(n), Color(BLUE, 0.18), 16.0)
				y += 14.0; n += 1
	var t: int = int(s.clock) - int(s.leadIn)
	for bar: Dictionary in s.bars:
		if int(s.clock) < int(bar.until):
			var from: Vector2 = Vector2(float(bar.side) * (h.x - 10.0), float(bar.gapY) - float(bar.gap))
			var to: Vector2 = Vector2(float(bar.side) * (h.x - 10.0), float(bar.gapY) + float(bar.gap))
			c.draw_line(v.box_point(from), v.box_point(to), Color(AMBER, 0.5 + 0.4 * sin(t * 0.4)), 2)

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"glyph":
			# A solid dark disc with a bright ring so the glyph reads against any backdrop.
			c.draw_circle(at, 6.5, Color(INK, 0.92 * alpha))
			c.draw_arc(at, 6.5, 0.0, TAU, 14, Color(AMBER, 0.85 * alpha), 1.0)
			v.text(c, at + Vector2(0, 4), str(b.get("glyph", "1")), Color(CREAM, alpha), 12.0)
			return true
		"block":
			c.draw_colored_polygon(v.quad(at, float(b.w), float(b.h), turn), Color(BLUE, 0.85 * alpha))
			c.draw_colored_polygon(v.quad(at + Vector2(-1, -1).rotated(turn), float(b.w) - 2.0, 1.0, turn), Color(CREAM, 0.5 * alpha))
			return true
		"tennis":
			c.draw_circle(at, float(b.r), Color(BALL, alpha))
			c.draw_arc(at + Vector2(-2.5, 0).rotated(turn), 3.2, -1.0 + turn, 1.0 + turn, 6, Color(CREAM, alpha), 1)
			c.draw_arc(at + Vector2(2.5, 0).rotated(turn), 3.2, PI - 1.0 + turn, PI + 1.0 + turn, 6, Color(CREAM, alpha), 1)
			return true
	return false
