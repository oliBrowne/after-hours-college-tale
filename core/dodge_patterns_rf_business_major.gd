extends RefCounted
## BUSINESS MAJOR / a wandering campus fight. He is building a brand, and the brand is him.
## Three slow, telegraphed attacks, one per turn, cycling in order: business cards,
## handshake, synergy chart. Phase 1 is the same three a little denser.
## The promise "Decline politely": first a green business card (stand in it, press
## confirm to take one), then a marked spot to hold still on for about a second
## (a polite no, thank you). Both sit away from the danger.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["business_cards", "handshake", "synergy_chart"]
const PHASES: Array[int] = [0, 1]
const PIE_LIVE: int = 70
const PIE_HUB: float = 11.0

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const BLUE: Color = Color("8fb3ea")
const LILAC: Color = Color("a68db8")
const ROSE: Color = Color("e8837b")
const SLICES: Array[Color] = [Color("e8837b"), Color("e8b45c"), Color("8fb3ea"), Color("a68db8"), Color("d98fc4"), Color("c9874a"), Color("7fb3b0")]

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	var phase: int = clampi(int(s.phase), 0, 1)
	s.patternId = id
	s.length = 400 + 40 * phase
	s.bannerColor = AMBER
	s.spots = [Vector2(0.62, 0.0), Vector2(-0.62, 0.0)]
	s.pieA0 = 0.0
	s.pieSafe = 0
	s.pieN = 6 + phase
	s.pieSpin = 0.009 + 0.002 * phase
	s.pieTurn = -1
	match id:
		"business_cards":
			s.phaseName = "Business Cards"
			s.hint = "Cards spin along red rows. Confirm on the green card, then hold still on the next spot."
		"handshake":
			s.phaseName = "Handshake"
			s.hint = "Two hands will meet in the red band. Keep out of it. Take the card, then hold to decline."
		"synergy_chart":
			s.phaseName = "Synergy Chart"
			s.hint = "Only one slice of the chart is safe, and it turns. Take the card, then hold to decline."
			s.pieA0 = D.rand(s) * TAU
			s.pieSafe = int(D.rand(s) * float(s.pieN)) % int(s.pieN)
			s.pieTurn = 210 if phase > 0 else -1
	# On the chart the markers ride the turning slice, so the icons stay unlabelled there.
	D.objective(s, {"kind": "confirm", "r": 12.0, "label": "" if id == "synergy_chart" else "card", "active": false})
	D.objective(s, {"kind": "hold", "r": 12.0, "need": 60, "label": "" if id == "synergy_chart" else "no thanks", "active": false})

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return bool(s.objectives[0].done) and bool(s.objectives[1].done)

static func progress(s: Dictionary) -> String:
	return "Card taken %d/1, declined %d/1" % [1 if s.objectives[0].done else 0, 1 if s.objectives[1].done else 0]

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	_markers(s, t)
	match str(s.patternId):
		"business_cards": _cards(s, t, phase)
		"handshake": _handshake(s, t, phase)
		"synergy_chart": _chart(s, t, phase)

static func after(_s: Dictionary, _t: int) -> void:
	pass

## Card first, then the spot: the second shows 24 ticks after the card is taken.
## On the chart both ride the safe slice (the card further out, the spot nearer the hub).
static func _markers(s: Dictionary, t: int) -> void:
	var h: Vector2 = D.half(s)
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		var spot: Vector2 = Vector2(s.spots[i]) * h
		if str(s.patternId) == "synergy_chart":
			spot = Vector2.from_angle(_safe_angle(s, t)) * (62.0 if i == 0 else 38.0)
		o.x = spot.x; o.y = spot.y
		var ready: bool = t >= 40 if i == 0 else last_done >= 0 and int(s.clock) - last_done >= 24
		o.active = ready
		if ready and not bool(o.get("shown", false)):
			o.shown = true
			D.effect(s, "pulse", D.to_world(s, spot), 18)
		return

## A row height that keeps `gap` px clear of the marker being chased (and of the row
## before). On the fight route the first row is simply at your height.
static func _row_y(s: Dictionary, other: float, gap: float) -> float:
	var marker: float = 999.0
	if bool(s.promised):
		for o: Dictionary in s.objectives:
			if not o.done:
				marker = float(o.y); break
	elif other > 900.0:
		return clampf(float(s.soul.y), -44.0, 44.0)
	var y: float = 0.0
	for k: int in range(8):
		y = D.rand_range(s, -46.0, 46.0)
		if absf(y - marker) >= gap and absf(y - other) >= 30.0: break
	return y

# ---------------------------------------------------------------- attacks

## Business Cards: two rows at a time, one row per side. Each row is a line of
## spinning cards with a hole in it. The rows are red bands first.
static func _cards(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
		D.banner(s, "NICE TO MEET YOU", 70)
	var every: int = 100 - 20 * phase
	if t % every == 14 and t < int(s.length) - 190:
		var n: int = int(t / every)
		var y1: float = _row_y(s, 999.0, 28.0)
		var y2: float = _row_y(s, y1, 28.0)
		_row(s, y1, 1.0 if n % 2 == 0 else -1.0, phase)
		_row(s, y2, -1.0 if n % 2 == 0 else 1.0, phase)

static func _row(s: Dictionary, y: float, side: float, phase: int) -> void:
	var h: Vector2 = D.half(s)
	var hole: int = 1 + int(D.rand(s) * 4.0) % 4
	D.warn(s, {"kind": "lane", "y": D.centre(s).y + y, "h": 11.0, "horizontal": true}, 40, side > 0.0)
	D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": y, "dir": Vector2(-side, 0)}, 40)
	for k: int in range(6):
		if k == hole: continue
		D.shot(s, {"space": "box", "x": side * (h.x + 14.0 + k * 34.0), "y": y, "vx": -side * (1.9 + 0.3 * phase), "collide": "rect", "w": 6.0, "h": 4.0, "shape": "card", "spin": 0.15 * side, "hold": true, "arm": 40, "life": 40 + 300})

## Handshake: two big hands come in along a red band, meet in the middle, shake
## three times and go back. Everything outside the band is safe.
static func _handshake(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
		D.banner(s, "FIRM HANDSHAKE", 70)
	var every: int = 118 - 26 * phase
	if t % every == 16 and t < int(s.length) - 230:
		_shake(s, _row_y(s, 999.0, 34.0), 44)
	if phase > 0 and t % every == 16 + 56 and t < int(s.length) - 230:
		_shake(s, _row_y(s, 999.0, 34.0), 44)
	var h: Vector2 = D.half(s)
	for b: Dictionary in s.bullets:
		if not b.has("shake"): continue
		var u: int = int(b.age) - int(b.arm)
		var hold: int = 36
		var span: int = int(float(b.span) / 2.4)
		var meet: float = float(b.side) * 14.0
		var start: float = float(b.side) * (h.x + 34.0)
		var along: float = 0.0
		if u > 0: along = clampf(float(u) / float(span), 0.0, 1.0) if u <= span + hold else clampf(float(2 * span + hold - u) / float(span), 0.0, 1.0)
		b.x = lerpf(start, meet, along)
		b.y = float(b.row) + (5.0 * sin(float(u - span) * 0.55) if u > span and u < span + hold else 0.0)
		b.px = b.x; b.py = b.y

static func _shake(s: Dictionary, y: float, warn: int) -> void:
	var h: Vector2 = D.half(s)
	D.warn(s, {"kind": "lane", "y": D.centre(s).y + y, "h": 18.0, "horizontal": true}, warn, true)
	for side: float in [-1.0, 1.0]:
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": y, "dir": Vector2(-side, 0)}, warn)
		var span: float = h.x + 34.0 - 14.0
		D.shot(s, {"space": "box", "x": side * (h.x + 34.0), "y": y, "collide": "rect", "w": 17.0, "h": 9.0, "shape": "hand", "face": -side, "shake": true, "side": side, "row": y, "span": span, "arm": warn, "life": warn + 2 * int(span / 2.4) + 36 + 6})

## Synergy Chart: a pie chart over the whole box, ghosted for a moment, then live:
## every slice hurts except the mint one. It turns slowly; the hub is not safe.
## Phase 1 has seven slices and reverses once ("REORG").
static func _chart(s: Dictionary, t: int, _phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 224.0, "h": 112.0}, 30)
		D.banner(s, "LET'S CIRCLE BACK", 70)
	if int(s.pieTurn) >= 0 and t == int(s.pieTurn) - 40:
		D.banner(s, "REORG", 50)
		D.warn(s, {"kind": "ding"}, 40, true)
	if t >= PIE_LIVE and _hazard(s, Vector2(float(s.soul.x), float(s.soul.y)), t):
		D.hurt(s, D.soul_world(s))

static func _pie_angle(s: Dictionary, t: int) -> float:
	var turn: int = int(s.pieTurn)
	var spin: float = float(s.pieSpin)
	if turn >= 0 and t > turn: return float(s.pieA0) + spin * float(turn) - spin * float(t - turn)
	return float(s.pieA0) + spin * float(t)

static func _safe_angle(s: Dictionary, t: int) -> float:
	return _pie_angle(s, t) + (float(s.pieSafe) + 0.5) * TAU / float(s.pieN)

## Is a box-space point on a hurting part of the chart? The soul's size counts as a
## 3 px margin, so touching a slice edge from the safe slice is not a hit.
static func _hazard(s: Dictionary, at: Vector2, t: int) -> bool:
	var r: float = at.length()
	if r < PIE_HUB: return true
	var slice: float = TAU / float(s.pieN)
	var margin: float = asin(minf(1.0, 3.0 / r))
	for d: float in [-margin, 0.0, margin]:
		if int(fposmod(at.angle() + d - _pie_angle(s, t), TAU) / slice) % int(s.pieN) != int(s.pieSafe): return true
	return false

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var t: int = int(s.clock) - int(s.leadIn)
	if str(s.patternId) == "synergy_chart" and t >= 10 and t < int(s.length) - 30:
		var live: bool = t >= PIE_LIVE
		var n: int = int(s.pieN)
		var flash: float = 0.5 + 0.5 * sin(float(t) * 0.4)
		for i: int in range(n):
			var a0: float = _pie_angle(s, t) + float(i) * TAU / float(n)
			var fan: PackedVector2Array = PackedVector2Array([v.box_point(Vector2.ZERO)])
			for k: int in range(9):
				fan.append(v.box_point(Vector2.from_angle(a0 + TAU / float(n) * float(k) / 8.0) * 140.0))
			if i == int(s.pieSafe):
				c.draw_colored_polygon(fan, Color(MINT, 0.3))
			elif live:
				c.draw_colored_polygon(fan, Color(SLICES[i], 0.3))
			else:
				c.draw_colored_polygon(fan, Color(SLICES[i], 0.1 + 0.1 * flash))
			c.draw_line(fan[0], fan[1], Color(CREAM, 0.35 if live else 0.2), 1)
			if i == int(s.pieSafe):
				c.draw_line(fan[0], fan[1], Color(MINT, 0.9), 2)
				c.draw_line(fan[0], fan[8], Color(MINT, 0.9), 2)
		c.draw_circle(v.box_point(Vector2.ZERO), PIE_HUB, Color(ROSE, 0.55 if live else 0.2))
		c.draw_arc(v.box_point(Vector2.ZERO), PIE_HUB, 0.0, TAU, 16, Color(CREAM, 0.6), 1)
	# Markers: a business card to take, then a polite "no, thank you" sign to stand on.
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if bool(s.promised) and o.active and not o.done:
			var at: Vector2 = v.box_point(Vector2(float(o.x), float(o.y)))
			if i == 0:
				_card(c, at, 0.0, Color(MINT, 0.9), Color(INK, 0.8))
			else:
				c.draw_arc(at, 5.5, 0.0, TAU, 14, Color(MINT, 0.9), 1)
				c.draw_line(at + Vector2(-4, 4), at + Vector2(4, -4), Color(MINT, 0.9), 1)

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"card":
			_card(c, at, turn, Color(CREAM, alpha), Color(INK, 0.7 * alpha))
			return true
		"hand":
			# A big cartoon hand with a cuff; palm, four fingers and a thumb.
			var f: float = float(b.get("face", 1.0))
			var ghost: float = 0.35 if int(b.age) <= int(b.arm) else 1.0
			var skin: Color = Color(CREAM, alpha * ghost)
			var line: Color = Color(INK, 0.7 * alpha * ghost)
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-f * 17, -8), at + Vector2(-f * 9, -8), at + Vector2(-f * 9, 8), at + Vector2(-f * 17, 8)]), Color(LILAC, alpha * ghost))
			c.draw_line(at + Vector2(-f * 9, -8), at + Vector2(-f * 9, 8), Color(CREAM, alpha * ghost), 2)
			c.draw_colored_polygon(v.quad(at + Vector2(f * 0.5, 0), 8.0, 8.0, 0.0), skin)
			for k: int in range(4):
				var fy: float = -6.0 + k * 4.0
				c.draw_colored_polygon(v.quad(at + Vector2(f * 12.0, fy), 4.5, 1.6, 0.0), skin)
				c.draw_line(at + Vector2(f * 8.0, fy + 2.0), at + Vector2(f * 16.0, fy + 2.0), line, 1)
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-f * 4, -8), at + Vector2(f * 3, -8), at + Vector2(f * 6, -12)]), skin)
			return true
	return false

## A business card: cream rectangle, a logo dot and two lines of tiny type.
static func _card(c: CanvasItem, at: Vector2, turn: float, body: Color, ink: Color) -> void:
	var q: PackedVector2Array = PackedVector2Array([at + Vector2(-6, -4).rotated(turn), at + Vector2(6, -4).rotated(turn), at + Vector2(6, 4).rotated(turn), at + Vector2(-6, 4).rotated(turn)])
	c.draw_colored_polygon(q, body)
	c.draw_circle(at + Vector2(-3.5, -1.5).rotated(turn), 1.0, Color(AMBER, body.a))
	c.draw_line(at + Vector2(-1, -2).rotated(turn), at + Vector2(4, -2).rotated(turn), ink, 1)
	c.draw_line(at + Vector2(-4, 1.5).rotated(turn), at + Vector2(4, 1.5).rotated(turn), ink, 1)
