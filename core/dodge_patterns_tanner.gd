extends RefCounted
## TANNER / the rush chair of the house on The Hill. His brothers carry him in on a
## couch to an airhorn blast; the catchphrase is "Bro. BRO. Rush week never ends."
## An optional mini-boss between chapters: harder than a wandering fight, easier
## than a chapter boss. Three attacks, one per turn, cycling in order. Phase 1 is
## denser; phase 2 is denser still and adds one layer per attack.
##  chant        BRO walls scroll across on the downbeat, the gap shifts every beat.
##               (phase 2: an airhorn band blasts across on the fourth beat)
##  cup_walls    red solo cups rise into walls with a marked gap; a ping-pong ball
##               serves out of each gap and bounces away. (phase 2: lobbed balls)
##  group_photo  a viewfinder shrinks onto you, locks, then flashes. Only standing
##               in it hurts. (phase 1: two frames; phase 2: photobombers jog by)
## The promise ("Decline one more game", peaceful): three game-night markers glow one
## after another, away from the current danger: a pong table (hold), a card game
## (confirm) and finally a bed (hold; "Tanner goes to bed"). While promised, gaps open
## near the active marker and walls rise elsewhere.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["chant", "cup_walls", "group_photo"]
const PHASES: Array[int] = [0, 1, 2]
const GAMES: int = 3
const KINDS: Array[String] = ["hold", "confirm", "hold"]
const LABELS: Array[String] = ["no pong", "no cards", "bed time"]
const WALL_SPEED: float = 1.5
const RISE: float = 3.4          # cups climb this fast, px per tick
const TRACK: int = 38            # the viewfinder shrinks onto you
const LOCK: int = 34             # locked and warning, before the flash
const FLASH: int = 10

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const ROSE: Color = Color("e8837b")
const BLUE: Color = Color("8fb3ea")
const CUP: Color = Color("c8423a")
const CUP_DARK: Color = Color("8e2a2a")
const FELT: Color = Color("2f5a63")
const CREW: Color = Color("2a3550")
const BALL: Color = Color("f2ecd8")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	var phase: int = clampi(int(s.phase), 0, 2)
	s.patternId = id
	s.length = 460 + 40 * phase
	s.walls = []
	s.shots = []
	s.spots = []
	s.gapY = 0.0
	s.gapDir = 1.0
	s.wallN = 0
	s.flashAt = -999
	match id:
		"chant":
			s.phaseName = "Rush Chant"
			s.hint = "BRO walls scroll in on the beat: slip through the gap. Glowing game: stand there, confirm."
			s.spots = [Vector2(-0.55, 0.3), Vector2(-0.55, -0.35), Vector2(-0.5, 0.0)]
		"cup_walls":
			s.phaseName = "Cup Walls"
			s.hint = "Cups rise at the marked gap, a ball serves out of it. Glowing game: stand, confirm."
			s.spots = [Vector2(-0.5, -0.4), Vector2(0.45, -0.45), Vector2(0.0, -0.5)]
		"group_photo":
			s.phaseName = "Group Photo"
			s.hint = "The frame locks on you, then flashes: step out of it. Glowing game: stand there, confirm."
			s.spots = [Vector2(-0.6, -0.45), Vector2(0.6, 0.4), Vector2(0.0, 0.45)]
	for i: int in range(GAMES):
		var props: Dictionary = {"kind": KINDS[i], "label": LABELS[i], "active": false, "x": 0.0, "y": 0.0, "need": 45}
		if KINDS[i] == "hold":
			props.w = 16.0
			props.h = 13.0
		else:
			props.r = 13.0
		D.objective(s, props)

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return _declined(s) >= GAMES

static func progress(s: Dictionary) -> String:
	return "Games declined %d/%d" % [_declined(s), GAMES]

static func _declined(s: Dictionary) -> int:
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	return count

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 2)
	match str(s.patternId):
		"chant": _chant(s, t, phase)
		"cup_walls": _cups(s, t, phase)
		"group_photo": _photo(s, t, phase)
	_games(s, t)

static func after(s: Dictionary, _t: int) -> void:
	if str(s.patternId) == "cup_walls": _settle_cups(s)

# ---------------------------------------------------------------- game night

## One marker at a time: the next shows up 24 ticks after the last was done.
static func _games(s: Dictionary, t: int) -> void:
	var h: Vector2 = D.half(s)
	var last_done: int = -999
	for i: int in range(s.objectives.size()):
		var o: Dictionary = s.objectives[i]
		if o.done:
			last_done = int(o.doneAt)
			continue
		var spot: Vector2 = Vector2(s.spots[i]) * h
		o.x = spot.x; o.y = spot.y
		var ready: bool = t >= 40 if i == 0 else last_done >= 0 and int(s.clock) - last_done >= 24
		o.active = ready
		if ready and not bool(o.get("shown", false)):
			o.shown = true
			D.effect(s, "pulse", D.to_world(s, spot), 18)
		return

static func _active(s: Dictionary) -> Dictionary:
	for o: Dictionary in s.objectives:
		if o.active and not o.done: return o
	return {}

# ---------------------------------------------------------------- the beat

## Walls wait this long off-box (the warning), then enter exactly on a downbeat.
static func _lead(s: Dictionary) -> int:
	return int(s.beatTicks) + 2 if int(s.beatTicks) >= 30 else int(s.beatTicks) * 2 + 2

static func _on_spawn(s: Dictionary) -> bool:
	return (int(s.clock) + int(s.musicBase) + _lead(s)) % int(s.beatTicks) == 0

# ---------------------------------------------------------------- 1. Rush Chant

## A wall of BRO tokens enters on every downbeat (the fourth beat of each bar is a
## rest in phase 0). The gap shifts each beat by 20 to 34 px. While promised the
## gap opens near the active marker. Phase 2: on the fourth beat the airhorn also
## blasts a band across the box at about your height, warned 38 ticks ahead.
static func _chant(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 112.0}, 30)
	var kept: Array = []
	for w: Dictionary in s.walls:
		if int(w.enter) > int(s.clock): kept.append(w)
	s.walls = kept
	if t < 20 or t >= int(s.length) - 150 or not _on_spawn(s): return
	var lead: int = _lead(s)
	var slot: int = ((int(s.clock) + int(s.musicBase) + lead) / int(s.beatTicks)) % 4
	if phase == 0 and slot == 3: return
	var g: float = float([24.0, 22.0, 21.0][phase])
	var c: float = _next_gap(s, h, g)
	D.warn(s, {"kind": "edge", "space": "box", "x": h.x - 3.0, "y": c + g + 9.0, "dir": Vector2.LEFT}, lead, slot == 0)
	D.warn(s, {"kind": "edge", "space": "box", "x": h.x - 3.0, "y": c - g - 9.0, "dir": Vector2.LEFT}, lead)
	s.walls.append({"gy": c, "g": g, "enter": int(s.clock) + lead})
	var life: int = lead + int((2.0 * h.x + 50.0) / WALL_SPEED)
	var y: float = -h.y + 7.0
	while y < h.y:
		if absf(y - c) >= g + 6.5:
			D.shot(s, {"space": "box", "x": h.x + 14.0, "y": y, "vx": -WALL_SPEED, "collide": "rect", "w": 11.0, "h": 6.5, "shape": "bro", "word": "HEY" if slot == 3 else "BRO", "hold": true, "arm": lead, "life": life})
		y += 14.0
	if phase >= 2 and slot == 3:
		var by: float = clampf(float(s.soul.y) + D.rand_range(s, -10.0, 10.0), -h.y + 12.0, h.y - 12.0)
		D.warn(s, {"kind": "lane", "y": D.centre(s).y + by, "h": 8.0, "horizontal": true}, lead + 6, true)
		D.shot(s, {"space": "box", "x": 0.0, "y": by, "collide": "rect", "w": h.x, "h": 6.0, "shape": "blast", "hold": true, "arm": lead + 6, "life": lead + 18})

static func _next_gap(s: Dictionary, h: Vector2, g: float) -> float:
	var lim: float = h.y - g - 3.0
	var o: Dictionary = _active(s)
	s.wallN = int(s.wallN) + 1
	var c: float = float(s.gapY) + float(s.gapDir) * D.rand_range(s, 20.0, 34.0)
	if absf(c) > lim:
		s.gapDir = -float(s.gapDir)
		c = float(s.gapY) + float(s.gapDir) * D.rand_range(s, 20.0, 34.0)
	c = clampf(c, -lim, lim)
	s.gapY = c
	if bool(s.promised) and not o.is_empty():
		# Halfway to the marker, with a little wobble so the gap still shifts.
		c = lerpf(c, float(o.y), 0.5) + D.rand_range(s, 3.0, 8.0) * (1.0 if int(s.wallN) % 2 == 0 else -1.0)
	return clampf(c, -lim, lim)

# ---------------------------------------------------------------- 2. Cup Walls

## Every so often a lane flashes, then a wall of cups rises out of the floor there
## with a gap marked in amber; a ping-pong ball waits in the gap and serves out of
## it toward you, bouncing. Walls stand for a while, then sink. Phase 1: faster,
## two balls per gap. Phase 2: lobbed balls also drop down marked columns.
static func _cups(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 116.0}, 30)
	var every: int = int([76, 62, 56][phase])
	var stop: int = int(s.length) - 200
	if t >= 16 and t < stop and t % every == 16: _new_wall(s, h, phase)
	if phase >= 2 and t >= 40 and t < stop + 60 and t % 66 == 40:
		var x: float = clampf(float(s.soul.x) + D.rand_range(s, -30.0, 30.0), -h.x + 12.0, h.x - 12.0)
		D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 6.0, "horizontal": false}, 36, true)
		D.shot(s, {"space": "box", "x": x, "y": -h.y - 6.0, "ay": 0.1, "r": 4.0, "shape": "pong", "hold": true, "arm": 36, "bounce": 0.5, "life": 240})

static func _new_wall(s: Dictionary, h: Vector2, phase: int) -> void:
	var g: float = float([22.0, 20.0, 19.0][phase])
	var x: float = _wall_x(s, h)
	var gy: float = D.rand_range(s, -h.y + g + 4.0, 0.3 * h.y)
	var rise: float = 2.0 * h.y + 14.0
	var stand: int = 34 + int(rise / RISE) + 90
	D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 9.0, "horizontal": false}, 36, true)
	s.walls.append({"x": x, "gy": gy, "g": g, "until": int(s.clock) + stand})
	var y: float = -h.y + 6.0
	while y < h.y - 3.0:
		if absf(y - gy) > g + 6.0:
			D.shot(s, {"space": "box", "x": x, "y": y + rise, "vy": -RISE, "collide": "rect", "w": 7.0, "h": 6.0, "shape": "cup", "hold": true, "arm": 34, "ty": y, "sink": stand, "life": stand + 60})
		y += 12.0
	var side: float = 1.0 if float(s.soul.x) > x else -1.0
	for i: int in range(1 + mini(phase, 1)):
		D.shot(s, {"space": "box", "x": x, "y": gy + i * 10.0, "vx": side * (1.6 + 0.1 * phase), "vy": -1.2, "ay": 0.1, "bounce": 0.82, "r": 3.5, "shape": "pong", "hold": true, "arm": 74 + 18 * i, "life": 74 + 18 * i + 240})

## Walls aim at you every other time (so you must act), but keep their distance
## from each other and from the active marker while promised.
static func _wall_x(s: Dictionary, h: Vector2) -> float:
	var o: Dictionary = _active(s)
	var x: float = 0.0
	for attempt: int in range(10):
		x = D.rand_range(s, -h.x + 22.0, h.x - 22.0)
		if attempt % 2 == 0: x = clampf(float(s.soul.x) + D.rand_range(s, -30.0, 30.0), -h.x + 22.0, h.x - 22.0)
		var near: bool = bool(s.promised) and not o.is_empty() and absf(float(o.x) - x) < 36.0
		for w: Dictionary in s.walls:
			if absf(float(w.x) - x) < 50.0: near = true
		if not near: break
	return x

## Cups stop where they were stacked, then sink out of the box when the wall is done.
static func _settle_cups(s: Dictionary) -> void:
	for b: Dictionary in s.bullets:
		if str(b.shape) != "cup" or not b.has("ty"): continue
		if float(b.vy) < 0.0 and float(b.y) <= float(b.ty):
			b.y = b.ty; b.vy = 0.0
		elif int(b.age) >= int(b.sink) and float(b.vy) <= 0.0:
			b.vy = 2.4

# ---------------------------------------------------------------- 3. Group Photo

## A viewfinder (wide, then tall, then wide) closes in on you over 38 ticks, tracking
## you, then locks where it is and warns for 34 ticks, then flashes for 10: only
## standing inside hurts. Phase 1: a second frame starts halfway through the first.
## Phase 2: brothers jog through the shot (photobombers) along warned lanes.
static func _photo(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 208.0, "h": 112.0}, 30)
	var every: int = int([112, 98, 88][phase])
	if t >= 20 and t < int(s.length) - 150:
		if (t - 20) % every == 0: _frame(s, t, phase)
		if phase >= 1 and (t - 20) % every == every / 2: _frame(s, t, phase)
	_track(s, t)
	if phase >= 2 and t >= 50 and t < int(s.length) - 170 and t % 120 == 50:
		var o: Dictionary = _active(s)
		var y: float = clampf(float(s.soul.y) + D.rand_range(s, -24.0, 24.0), -h.y + 14.0, h.y - 14.0)
		if bool(s.promised) and not o.is_empty() and absf(float(o.y) - y) < 30.0: y = -float(o.y)
		var side: float = -1.0 if int(t / 120) % 2 == 0 else 1.0
		D.warn(s, {"kind": "lane", "y": D.centre(s).y + y, "h": 13.0, "horizontal": true}, 38, true)
		D.warn(s, {"kind": "edge", "space": "box", "x": -side * (h.x - 3.0), "y": y, "dir": Vector2(side, 0)}, 38)
		D.shot(s, {"space": "box", "x": -side * (h.x + 14.0), "y": y, "vx": side * 1.4, "collide": "rect", "w": 6.0, "h": 11.0, "shape": "runner", "hold": true, "arm": 38, "life": 38 + int((2.0 * h.x + 40.0) / 1.4)})

static func _frame(s: Dictionary, t: int, phase: int) -> void:
	var wide: bool = int(s.wallN) % 2 == 0
	s.wallN = int(s.wallN) + 1
	var final: Vector2 = Vector2(58.0, 26.0) if wide else Vector2(26.0, 50.0)
	final *= float([1.0, 0.94, 0.9][phase])
	s.shots.append({"x": float(s.soul.x), "y": float(s.soul.y), "bw": 128.0, "bh": 82.0, "fw": final.x, "fh": final.y, "w": 128.0, "h": 82.0, "born": t, "state": "track"})

static func _track(s: Dictionary, t: int) -> void:
	var kept: Array = []
	for sh: Dictionary in s.shots:
		var age: int = t - int(sh.born)
		if sh.state == "track":
			var p: float = clampf(float(age) / TRACK, 0.0, 1.0)
			var e: float = 1.0 - (1.0 - p) * (1.0 - p)
			sh.x = lerpf(float(sh.x), float(s.soul.x), 0.12)
			sh.y = lerpf(float(sh.y), float(s.soul.y), 0.12)
			sh.w = lerpf(float(sh.bw), float(sh.fw), e)
			sh.h = lerpf(float(sh.bh), float(sh.fh), e)
			if age >= TRACK:
				sh.state = "lock"
				D.warn(s, {"kind": "frame", "space": "box", "x": sh.x, "y": sh.y, "w": sh.w, "h": sh.h}, LOCK, true)
				D.shot(s, {"space": "box", "x": sh.x, "y": sh.y, "collide": "rect", "w": sh.w, "h": sh.h, "shape": "flash", "hold": true, "arm": LOCK, "life": LOCK + FLASH})
		elif sh.state == "lock" and age >= TRACK + LOCK:
			sh.state = "flash"
			s.flashAt = int(s.clock)
		if age < TRACK + LOCK + FLASH: kept.append(sh)
	s.shots = kept

# ---------------------------------------------------------------- drawing

static func _figure(c: CanvasItem, base: Vector2, size: float, col: Color, cap: bool = false) -> void:
	c.draw_circle(base + Vector2(0, -26.0 * size), 4.6 * size, col)
	c.draw_colored_polygon(PackedVector2Array([base + Vector2(-8, 0) * size, base + Vector2(-7, -19) * size, base + Vector2(7, -19) * size, base + Vector2(8, 0) * size]), col)
	if cap: c.draw_line(base + Vector2(-5.5, -29.5) * size, base + Vector2(5.5, -29.5) * size, Color(ROSE, col.a), 2.0)

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var clock: int = int(s.clock)
	var hit: float = 1.0 - float((clock + int(s.musicBase)) % int(s.beatTicks)) / float(s.beatTicks)
	match str(s.patternId):
		"chant":
			# Four beat pips (the bar), the crowd on the right bobbing on the beat,
			# and amber brackets on the gap of every wall still waiting off-box.
			for i: int in range(4):
				var lit: bool = int(s.beat) % 4 == i
				c.draw_circle(v.box_point(Vector2(-h.x + 10.0 + i * 9.0, -h.y + 8.0)), 3.0, Color(AMBER, 0.9) if lit else Color(CREAM, 0.15))
			for i: int in range(5):
				_figure(c, v.box_point(Vector2(h.x - 10.0, -h.y + 20.0 + i * 24.0 - hit * 2.0)), 0.7, Color(CREW, 0.8), i == 2)
			for w: Dictionary in s.walls:
				var blink: float = 0.55 + 0.4 * sin(float(clock) * 0.5)
				for e: float in [-1.0, 1.0]:
					var y: float = float(w.gy) + e * float(w.g)
					c.draw_line(v.box_point(Vector2(h.x - 26.0, y)), v.box_point(Vector2(h.x - 3.0, y)), Color(AMBER, blink), 2)
		"cup_walls":
			c.draw_line(v.box_point(Vector2(-h.x, h.y - 2.0)), v.box_point(Vector2(h.x, h.y - 2.0)), Color(CUP, 0.35), 2)
			for w: Dictionary in s.walls:
				if clock >= int(w.until): continue
				var blink2: float = 0.55 + 0.4 * sin(float(clock) * 0.5)
				for e2: float in [-1.0, 1.0]:
					var yy: float = float(w.gy) + e2 * float(w.g)
					c.draw_line(v.box_point(Vector2(float(w.x) - 14.0, yy)), v.box_point(Vector2(float(w.x) + 14.0, yy)), Color(AMBER, blink2), 2)
		"group_photo":
			# The group lines up along the bottom and strikes a pose on every flash.
			var glow: float = clampf(1.0 - float(clock - int(s.flashAt)) / 18.0, 0.0, 1.0)
			for i: int in range(7):
				var pose: float = 1.0 + 0.12 * glow * (1.0 if i % 2 == 0 else -1.0)
				_figure(c, v.box_point(Vector2(-84.0 + i * 28.0, h.y + 1.0)), 0.9 * pose, Color(CREW, 0.75).lerp(Color(CREAM, 0.8), glow), i == 1 or i == 4)
			for w2: Dictionary in s.warnings:
				if str(w2.kind) == "frame": _viewfinder(c, v, Vector2(float(w2.x), float(w2.y)), Vector2(float(w2.w), float(w2.h)), Color(ROSE, 0.75 + 0.25 * sin(float(w2.age) * 0.6)), true)
			for sh: Dictionary in s.shots:
				if sh.state == "track": _viewfinder(c, v, Vector2(float(sh.x), float(sh.y)), Vector2(float(sh.w), float(sh.h)), Color(CREAM, 0.7), false)
	var pulse: float = 0.5 + 0.5 * sin(float(clock) * 0.2)
	for o: Dictionary in s.objectives:
		if bool(s.promised) and o.active and not o.done: _game_icon(c, v, int(o.id), Vector2(float(o.x), float(o.y)), pulse)

## Corner brackets and a crosshair; locked frames also show the REC dot.
static func _viewfinder(c: CanvasItem, v: Node2D, centre: Vector2, half: Vector2, col: Color, locked: bool) -> void:
	for sx: float in [-1.0, 1.0]:
		for sy: float in [-1.0, 1.0]:
			var corner: Vector2 = centre + Vector2(sx * half.x, sy * half.y)
			c.draw_polyline(PackedVector2Array([v.box_point(corner + Vector2(-sx * 12.0, 0)), v.box_point(corner), v.box_point(corner + Vector2(0, -sy * 12.0))]), col, 2)
	if locked: c.draw_colored_polygon(v.box_rect_poly(Rect2(centre - half, half * 2.0)), Color(ROSE, 0.10))
	c.draw_line(v.box_point(centre + Vector2(-4, 0)), v.box_point(centre + Vector2(4, 0)), Color(col, 0.6), 1)
	c.draw_line(v.box_point(centre + Vector2(0, -4)), v.box_point(centre + Vector2(0, 4)), Color(col, 0.6), 1)
	if locked: c.draw_circle(v.box_point(centre + Vector2(half.x - 6.0, -half.y + 6.0)), 2.5, ROSE)

## The marker's prop under its mint outline: pong table, card fan, bed.
static func _game_icon(c: CanvasItem, v: Node2D, which: int, at: Vector2, pulse: float) -> void:
	var p: Vector2 = v.box_point(at)
	c.draw_circle(p, 17.0 + pulse * 2.0, Color(AMBER, 0.10 + 0.08 * pulse))
	match which:
		0:
			c.draw_rect(Rect2(p + Vector2(-13, -6), Vector2(26, 12)), FELT)
			c.draw_rect(Rect2(p + Vector2(-13, -6), Vector2(26, 12)), CREAM, false, 1)
			c.draw_line(p + Vector2(0, -6), p + Vector2(0, 6), Color(CREAM, 0.6), 1)
			for k: int in range(3):
				c.draw_circle(p + Vector2(-9.0 + (k % 2) * 3.0, -3.0 + k * 3.0), 1.8, CUP)
				c.draw_circle(p + Vector2(9.0 - (k % 2) * 3.0, -3.0 + k * 3.0), 1.8, CUP)
		1:
			for k: int in range(3):
				var card: PackedVector2Array = v.quad(p + Vector2(-6.0 + k * 6.0, 1.0), 4.5, 6.5, -0.4 + k * 0.4)
				c.draw_colored_polygon(card, CREAM)
				c.draw_polyline(card + PackedVector2Array([card[0]]), INK, 1)
			c.draw_circle(p + Vector2(6, 0), 1.6, ROSE)
		2:
			c.draw_rect(Rect2(p + Vector2(-13, -2), Vector2(26, 9)), Color("6c5a4a"))
			c.draw_rect(Rect2(p + Vector2(-12, -6), Vector2(8, 5)), CREAM)
			c.draw_rect(Rect2(p + Vector2(-3, -5), Vector2(15, 9)), BLUE)
			v.text(c, p + Vector2(8, -9.0 - pulse * 2.0), "z z", Color(CREAM, 0.8), 30)

static func draw_over(_c: CanvasItem, _s: Dictionary, _v: Node2D) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"bro":
			c.draw_colored_polygon(v.quad(at, float(b.w), float(b.h), turn), Color(AMBER, 0.92 * alpha))
			c.draw_polyline(v.quad(at, float(b.w), float(b.h), turn) + PackedVector2Array([v.quad(at, float(b.w), float(b.h), turn)[0]]), Color(CREAM, alpha), 1)
			v.text(c, at + Vector2(0, 4), str(b.get("word", "BRO")), Color(INK, alpha), 24)
			return true
		"cup":
			var up: Vector2 = Vector2(0, -1).rotated(turn)
			var side: Vector2 = Vector2(1, 0).rotated(turn)
			var top: Vector2 = at + up * 6.0
			var low: Vector2 = at - up * 6.0
			c.draw_colored_polygon(PackedVector2Array([top - side * 8.0, top + side * 8.0, low + side * 5.5, low - side * 5.5]), Color(CUP, alpha))
			c.draw_line(at - side * 6.6, at + side * 6.6, Color(CUP_DARK, alpha), 2)
			c.draw_line(top - side * 8.0, top + side * 8.0, Color(CREAM, alpha), 2)
			return true
		"pong":
			c.draw_circle(at, float(b.r), Color(BALL, alpha))
			c.draw_arc(at, float(b.r), 0.5 + turn, 2.6 + turn, 6, Color(AMBER, alpha), 1)
			if int(b.age) <= int(b.arm): c.draw_arc(at, float(b.r) + 3.0 + 1.5 * sin(float(b.age) * 0.4), 0, TAU, 14, Color(CREAM, 0.5 * alpha), 1)
			return true
		"blast":
			if int(b.age) <= int(b.arm): return true
			var fade: float = clampf(float(int(b.life) - int(b.age)) / 8.0, 0.0, 1.0)
			c.draw_colored_polygon(v.quad(at, float(b.w), float(b.h), turn), Color(1.0, 0.9, 0.6, 0.85 * fade * alpha))
			v.text(c, at + Vector2(0, 4), "HONK", Color(INK, fade * alpha), 60)
			return true
		"flash":
			if int(b.age) <= int(b.arm): return true
			var glow: float = clampf(float(int(b.life) - int(b.age)) / float(FLASH), 0.0, 1.0)
			c.draw_colored_polygon(v.quad(at, float(b.w), float(b.h), turn), Color(1.0, 0.98, 0.88, 0.9 * glow * alpha))
			return true
		"runner":
			var step: float = sin(float(b.age) * 0.5) * 3.0
			var cream: Color = Color(CREAM, alpha)
			c.draw_line(at + Vector2(step, 11), at + Vector2(0, 5), cream, 2)
			c.draw_line(at + Vector2(-step, 11), at + Vector2(0, 5), cream, 2)
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-5, 6), at + Vector2(-5, -5), at + Vector2(5, -5), at + Vector2(5, 6)]), cream)
			c.draw_circle(at + Vector2(0, -9), 4.0, cream)
			c.draw_line(at + Vector2(0, -3), at + Vector2(signf(float(b.vx)) * 9.0, -11), cream, 2)
			return true
	return false
