extends RefCounted
## ERRATA: the correction machine in the moving stacks. "REPLACE UNCERTAINTY.
## ERASE HESITATION. FIX EVERY LINE." Four handmade attacks, one per turn,
## cycling. The box is a ruled page; ERRATA's red pen strikes lines, swaps your
## letters, types over the page and circles you as an error.
## The promise (Keep One Sentence) is three sentence pauses per turn: a green
## sentence box opens for 75 ticks, three times, and confirming inside it while
## promised keeps that pause. The kept sentence's line is never written over.
## Phase 1 (from the second turn) adds a layer to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["strikethrough", "anagram", "typewriter", "proofmarks"]
const PHASES: Array[int] = [0, 1]
const LENGTH: int = 450
const WINDOWS: Array[int] = [40, 185, 330]
const OPEN: int = 75
const ROWS: Array[float] = [-48.0, -32.0, -16.0, 0.0, 16.0, 32.0, 48.0]
const SLOT: float = 12.0
const SLOTS: int = 20
const WORD_TOP: String = "HESITATE"
const WORD_BOTTOM: String = "PERHAPS?"
const LETTERS: String = "ABCDEFGHIKLMNOPRSTUVWY"
const RED: Color = Color("e0524a")
const PINK: Color = Color("e8837b")
const PAPER: Color = Color("e6d6b1")
const MINT: Color = Color("b9d5bc")
const DARK: Color = Color("1a1420")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = LENGTH
	s.phaseName = "Keep One Sentence"
	s.sentencesKept = 0
	s.lastSentence = -1
	s.sentenceWindow = false
	s.sentenceNumber = -1
	s.botGoal = null
	s.bannerColor = PINK
	var spots: Array = []
	match id:
		"strikethrough":
			s.hint = "The red pen strikes whole lines. Stand on a clean line. Confirm in each green sentence."
			spots = [Vector2(-32, 32), Vector2(48, -16), Vector2(-56, 16)]
		"anagram":
			s.hint = "ERRATA swaps your letters. Read their dotted paths. Confirm in each green sentence."
			spots = [Vector2(-40, 0), Vector2(44, -8), Vector2(0, 12)]
		"typewriter":
			s.hint = "Pinned to the page: jump the cursor, land in the spaces. Confirm in each green sentence."
			spots = [Vector2(-60, 36), Vector2(36, 36), Vector2(-24, 36)]
		"proofmarks":
			s.hint = "Red circles close in on you. Leave through the gap. Confirm in each green sentence."
			spots = [Vector2(-60, 28), Vector2(56, -26), Vector2(-40, -28)]
	s.spots = spots
	for i: int in range(3):
		D.objective(s, {"kind": "confirm", "x": spots[i].x, "y": spots[i].y, "r": 19.0, "active": false})

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return int(s.sentencesKept) >= 3

static func progress(s: Dictionary) -> String:
	return "Sentence pauses %d/3\nConfirm in green box" % int(s.sentencesKept)

static func tick(s: Dictionary, t: int) -> void:
	_sentences(s, t)
	var phase: int = int(s.phase)
	match str(s.patternId):
		"strikethrough": _strikethrough(s, t, phase)
		"anagram": _anagram(s, t, phase)
		"typewriter": _typewriter(s, t, phase)
		"proofmarks": _proofmarks(s, t, phase)
	_grow(s)

static func after(s: Dictionary, _t: int) -> void:
	var kept: int = 0
	for i: int in range(3):
		if s.objectives[i].done:
			kept += 1
			s.lastSentence = i
	s.sentencesKept = kept

# ---------------------------------------------------------------- the promise

static func _sentences(s: Dictionary, t: int) -> void:
	for i: int in range(3):
		var start: int = WINDOWS[i]
		var o: Dictionary = s.objectives[i]
		if t == start - 30:
			D.warn(s, {"kind": "sentence", "x": float(o.x), "y": float(o.y)}, 30, true)
			s.botGoal = Vector2(float(o.x), float(o.y))
		elif t == start:
			o.active = true
			s.sentenceWindow = true
			s.sentenceNumber = i
			s.botGoal = null
		elif t == start + OPEN:
			o.active = false
			s.sentenceWindow = false

## The line (row index) of the sentence that is open or about to open, or -1.
static func _kept_row(s: Dictionary, t: int) -> int:
	for i: int in range(3):
		if t >= WINDOWS[i] - 36 and t < WINDOWS[i] + OPEN:
			return _row_of(float(s.objectives[i].y))
	return -1

static func _row_of(y: float) -> int:
	var best: int = 0
	for i: int in range(ROWS.size()):
		if absf(ROWS[i] - y) < absf(ROWS[best] - y): best = i
	return best

static func _soul(s: Dictionary) -> Vector2:
	return Vector2(float(s.soul.x), float(s.soul.y))

static func _letter(s: Dictionary) -> String:
	var i: int = int(D.rand(s) * LETTERS.length())
	return LETTERS.substr(i, 1)

# ---------------------------------------------------------------- strokes

## A red pen stroke: a box-space rect that, after warn ticks of dashed
## telegraph, grows from `from` along `dir` at `speed`, lingers, then fades.
static func _stroke(s: Dictionary, from: Vector2, dir: Vector2, length: float, speed: float, thick: float, warn: int, linger: int, shape: String, extra: Dictionary = {}) -> Dictionary:
	var props: Dictionary = {"space": "box", "x": from.x, "y": from.y, "collide": "rect", "w": 0.5, "h": thick, "rot": dir.angle(), "shape": shape, "arm": warn,
		"life": warn + int(ceil(length / speed)) + linger + 40,
		"stroke": {"ox": from.x, "oy": from.y, "dx": dir.x, "dy": dir.y, "len": length, "speed": speed, "warn": warn, "linger": linger, "cur": 0.0, "full": false, "fullAt": 0}}
	props.merge(extra, true)
	return D.shot(s, props)

static func _grow(s: Dictionary) -> void:
	var spawn: Array = []
	for b: Dictionary in s.bullets:
		if b.has("stroke") and not b.has("fade"):
			var k: Dictionary = b.stroke
			var grown: float = clampf(float(int(b.age) - int(k.warn)) * float(k.speed), 0.0, float(k.len))
			var d: Vector2 = Vector2(float(k.dx), float(k.dy))
			var mid: Vector2 = Vector2(float(k.ox), float(k.oy)) + d * grown * 0.5
			b.x = mid.x; b.y = mid.y; b.w = maxf(0.5, grown * 0.5)
			k.cur = grown
			if grown >= float(k.len) and not bool(k.full):
				k.full = true; k.fullAt = int(b.age)
				for i: int in range(int(b.get("crumbs", 0))):
					var at: Vector2 = Vector2(float(k.ox), float(k.oy)) + d * float(k.len) * D.rand_range(s, 0.2, 0.8)
					spawn.append(at)
			if bool(k.full) and int(b.age) - int(k.fullAt) >= int(k.linger): b.fade = 14
		elif b.has("contract") and not b.has("fade"):
			if int(b.age) >= int(b.arm):
				b.grow = -float(b.contract)
				b.gapSpin = float(b.get("spinAfter", 0.0))
			if float(b.radius) < 7.0:
				b.dead = true
				_burst(s, Vector2(float(b.x), float(b.y)))
	# Struck words fall apart: a few loose letters drop out of the line, but
	# never onto a kept sentence that is open or about to open.
	var t: int = int(s.clock) - int(s.leadIn)
	for at: Vector2 in spawn:
		var clear: bool = true
		for i: int in range(3):
			if t >= WINDOWS[i] - 50 and t < WINDOWS[i] + OPEN and absf(at.x - float(s.objectives[i].x)) < 30.0 and at.y < float(s.objectives[i].y): clear = false
		if not clear: continue
		D.shot(s, {"space": "box", "x": at.x, "y": at.y, "vx": D.rand_range(s, -0.3, 0.3), "vy": -0.9, "ay": 0.06, "r": 3.0, "shape": "glyph", "ch": _letter(s), "life": 150, "spin": 0.05})

static func _burst(s: Dictionary, at: Vector2) -> void:
	D.effect(s, "hit", D.to_world(s, at), 16)
	var turn: float = D.rand(s) * TAU
	for i: int in range(6):
		var dir: Vector2 = Vector2.from_angle(turn + i * TAU / 6.0)
		D.shot(s, {"space": "box", "x": at.x, "y": at.y, "vx": dir.x * 1.35, "vy": dir.y * 1.35, "r": 3.0, "shape": "glyph", "ch": "x", "life": 140})

# ---------------------------------------------------------------- Strikethrough
# The page is ruled into seven lines. The pen marks three or four of them
# (usually the line you stand on; never the kept sentence's line or the lines
# between you and it near a pause), then strikes them in quick succession;
# struck words drop loose letters. Phase 1: insertion carets shoot up the
# column you stand in.
static func _strikethrough(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 248.0, "h": 116.0}, 24)
	var every: int = 50 if phase == 0 else 44
	if t >= 16 and t <= 372 and (t - 16) % every == 0:
		_strike_pass(s, t, phase, int((t - 16) / every))
	if phase > 0 and t % 66 == 42 and t > 60 and t < 372:
		var h: Vector2 = D.half(s)
		var x: float = clampf(float(s.soul.x) + D.rand_range(s, -8.0, 8.0), -h.x + 10.0, h.x - 10.0)
		_stroke(s, Vector2(x, h.y + 2.0), Vector2.UP, h.y * 2.0 + 4.0, 8.0, 3.0, 32, 10, "caret")

static func _strike_pass(s: Dictionary, t: int, phase: int, pass_index: int) -> void:
	var h: Vector2 = D.half(s)
	var soul_row: int = _row_of(float(s.soul.y))
	var kept: int = _kept_row(s, t)
	var rows: Array[int] = []
	if soul_row != kept and D.rand(s) < 0.9: rows.append(soul_row)
	var want: int = 3 + phase
	var guard: int = 0
	while rows.size() < want and guard < 50:
		guard += 1
		var r: int = int(D.rand(s) * ROWS.size())
		if r == kept or r in rows: continue
		# Near a pause, the lines between you and the sentence stay clean.
		if kept >= 0 and r > mini(soul_row, kept) and r < maxi(soul_row, kept): continue
		rows.append(r)
	# Always leave a clean line within two lines of the soul.
	var free_near: Array[int] = []
	for r: int in range(maxi(0, soul_row - 2), mini(ROWS.size(), soul_row + 3)):
		if not r in rows: free_near.append(r)
	if free_near.is_empty():
		for r: int in rows:
			if r != soul_row and absi(r - soul_row) == 1:
				rows.erase(r); break
	var k: int = 0
	for r: int in rows:
		var from_left: bool = (pass_index + k) % 2 == 0
		var start: Vector2 = Vector2(-h.x - 6.0 if from_left else h.x + 6.0, ROWS[r])
		_stroke(s, start, Vector2.RIGHT if from_left else Vector2.LEFT, h.x * 2.0 + 12.0, 9.0, 3.5, 30 + k * 6, 14, "strike", {"crumbs": 2})
		k += 1

# ---------------------------------------------------------------- Anagram
# Two lines of your words sit at the top and bottom of the page. Every second
# ERRATA trades letters between them: dotted paths show where each letter will
# fly, then pairs cross the page on curved paths. Letters spit punctuation at
# you in between. Phase 1: the page tilts back and forth as it is rewritten.
static func _slot(line: int, i: int) -> Vector2:
	return Vector2(-77.0 + 22.0 * i, -46.0 if line == 0 else 46.0)

static func _anagram(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 200.0, "h": 120.0}, 24)
		for line: int in range(2):
			var word: String = WORD_TOP if line == 0 else WORD_BOTTOM
			for i: int in range(8):
				var at: Vector2 = _slot(line, i)
				D.shot(s, {"space": "box", "x": at.x, "y": at.y, "r": 5.0, "shape": "glyph", "big": true, "ch": word.substr(i, 1), "letter": true, "line": line, "idx": i, "arm": 30, "life": 2000})
	if phase > 0 and t >= 30:
		s.box.rot = 0.24 * sin(float(t - 30) * 0.018)
	var every: int = 62 if phase == 0 else 56
	if t >= 24 and t <= 352 and (t - 24) % every == 0:
		_shuffle(s, t, phase)
	_fly_letters(s, t)
	if t >= 40 and t < 392 and t % 28 == 14:
		var pick: Array = []
		for b: Dictionary in s.bullets:
			if b.get("letter", false) and not b.has("move"): pick.append(b)
		if not pick.is_empty():
			var b: Dictionary = pick[int(D.rand(s) * pick.size())]
			var from: Vector2 = Vector2(float(b.x), float(b.y))
			var aim: Vector2 = (_soul(s) - from).normalized() * (1.45 + phase * 0.15)
			D.effect(s, "block", D.to_world(s, from), 12)
			D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": aim.x, "vy": aim.y, "r": 2.5, "shape": "glyph", "ch": "," if D.rand(s) < 0.5 else ".", "life": 220})

static func _shuffle(s: Dictionary, t: int, phase: int) -> void:
	var by_slot: Dictionary = {}
	for b: Dictionary in s.bullets:
		if b.get("letter", false) and not b.has("move"): by_slot[int(b.line) * 8 + int(b.idx)] = b
	var pairs: int = 3 + phase
	var guard: int = 0
	var made: int = 0
	while made < pairs and guard < 40:
		guard += 1
		var i: int = int(D.rand(s) * 8.0)
		var j: int = int(D.rand(s) * 8.0)
		if not by_slot.has(i) or not by_slot.has(8 + j): continue
		var top: Dictionary = by_slot[i]
		var bottom: Dictionary = by_slot[8 + j]
		by_slot.erase(i); by_slot.erase(8 + j)
		var bend: float = D.rand_range(s, 10.0, 22.0) * (1.0 if D.rand(s) < 0.5 else -1.0)
		_send(top, _slot(1, j), t + 30, 44, bend)
		top.line = 1; top.idx = j
		_send(bottom, _slot(0, i), t + 30, 44, bend)
		bottom.line = 0; bottom.idx = i
		made += 1
	# One quick neighbour swap along a line, so the words visibly change.
	var line: int = 0 if D.rand(s) < 0.5 else 1
	var a: int = int(D.rand(s) * 7.0)
	if by_slot.has(line * 8 + a) and by_slot.has(line * 8 + a + 1):
		var left: Dictionary = by_slot[line * 8 + a]
		var right: Dictionary = by_slot[line * 8 + a + 1]
		_send(left, _slot(line, a + 1), t + 30, 30, 12.0 if line == 0 else -12.0)
		left.idx = a + 1
		_send(right, _slot(line, a), t + 30, 30, 12.0 if line == 0 else -12.0)
		right.idx = a
	D.banner(s, "REARRANGE", 30)

static func _send(b: Dictionary, to: Vector2, start: int, dur: int, bend: float) -> void:
	b.move = {"fx": float(b.x), "fy": float(b.y), "tx": to.x, "ty": to.y, "t0": start, "dur": dur, "bend": bend}

static func _move_point(m: Dictionary, p: float) -> Vector2:
	var from: Vector2 = Vector2(float(m.fx), float(m.fy))
	var to: Vector2 = Vector2(float(m.tx), float(m.ty))
	var e: float = p * p * (3.0 - 2.0 * p)
	var side: Vector2 = (to - from).normalized().orthogonal()
	return from.lerp(to, e) + side * float(m.bend) * sin(PI * e)

static func _fly_letters(s: Dictionary, t: int) -> void:
	for b: Dictionary in s.bullets:
		if not b.has("move"): continue
		var m: Dictionary = b.move
		if t < int(m.t0): continue
		var p: float = clampf(float(t - int(m.t0)) / float(m.dur), 0.0, 1.0)
		var at: Vector2 = _move_point(m, p)
		b.x = at.x; b.y = at.y
		if p >= 1.0: b.erase("move")

# ---------------------------------------------------------------- Typewriter
# Blue soul on the bottom line of the page. A cursor types the line from left
# to right; the faint ghost text shows which slots get letters, so you wait in
# a space and hop the cursor as it passes (it hesitates between words). At the
# end of a line: DING, the carriage slams back (jump it) and the line feeds up
# to the top of the page, where it caps your highest jumps. The kept
# sentences are never typed over. Phase 1: ERRATA backspaces mid-line,
# flinging the deleted letters up into the page.
static func _slot_x(k: int) -> float:
	return -114.0 + SLOT * k

static func _typewriter(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 88.0}, 20)
		D.set_mode(s, "blue")
		s.soul.gravity = Vector2.DOWN
		s.tw = {"x": _slot_x(0) - 8.0, "k": 0, "state": "wait", "wait": 32, "plan": _type_plan(s), "back": false, "dir": 1}
		D.shot(s, {"space": "box", "x": _slot_x(0) - 8.0, "y": 37.0, "collide": "rect", "w": 2.0, "h": 7.0, "shape": "cursor", "cursor": true, "arm": 32, "life": 2000})
		D.banner(s, "TYPESET", 40)
		return
	var tw: Dictionary = s.tw
	var floor_y: float = h.y
	var speed: float = 2.2 + phase * 0.2
	match str(tw.state):
		"wait":
			tw.wait = int(tw.wait) - 1
			if int(tw.wait) <= 0: tw.state = "type"
		"type":
			var k: int = int(tw.k)
			var target: float = _slot_x(k)
			tw.x = move_toward(float(tw.x), target, speed)
			if is_equal_approx(float(tw.x), target):
				var ch: String = str(tw.plan[k])
				if not ch.is_empty():
					D.shot(s, {"space": "box", "x": target, "y": floor_y - 3.5, "collide": "rect", "w": 4.0, "h": 3.5, "shape": "type", "ch": ch, "typed": true, "row": 0, "slot": k, "arm": 3, "life": 2000})
				elif k > 0 and not str(tw.plan[k - 1]).is_empty() and D.rand(s) < 0.45:
					tw.state = "wait"; tw.wait = int(D.rand_range(s, 6.0, 20.0))
				tw.k = k + 1
				if phase > 0 and not bool(tw.back) and k == 11:
					tw.back = true; tw.state = "back"; tw.stop = k - 3
					D.banner(s, "BACKSPACE", 30)
				if int(tw.k) >= SLOTS:
					tw.state = "ding"; tw.wait = 26
					D.banner(s, "DING", 30)
					D.warn(s, {"kind": "edge", "space": "box", "x": h.x - 4.0, "y": floor_y - 7.0, "dir": Vector2.LEFT}, 26, true)
		"back":
			var stop: int = int(tw.stop)
			var target_b: float = _slot_x(int(tw.k) - 1)
			tw.x = move_toward(float(tw.x), target_b, speed * 1.2)
			if is_equal_approx(float(tw.x), target_b):
				var slot: int = int(tw.k) - 1
				for b: Dictionary in s.bullets:
					if b.get("typed", false) and int(b.row) == 0 and int(b.slot) == slot:
						b.typed = false
						b.vx = D.rand_range(s, -0.8, 0.8); b.vy = -2.6; b.ay = 0.11; b.spin = 0.2; b.shape = "glyph"; b.collide = "circle"; b.r = 3.0
				tw.k = slot
				tw.plan[slot] = "" if _sentence_slot(s, slot) else _letter(s)
				if slot <= stop:
					tw.state = "wait"; tw.wait = 14
		"ding":
			tw.wait = int(tw.wait) - 1
			if int(tw.wait) <= 0:
				_line_feed(s)
				tw.state = "return"
		"return":
			tw.x = move_toward(float(tw.x), _slot_x(0) - 8.0, 5.5)
			if float(tw.x) <= _slot_x(0) - 8.0:
				tw.plan = _type_plan(s)
				tw.k = 0; tw.back = false
				tw.state = "wait"; tw.wait = 16
	for b: Dictionary in s.bullets:
		if b.get("cursor", false):
			b.x = float(tw.x); b.y = floor_y - 7.0
		elif b.get("typed", false) and b.has("ty"):
			b.y = move_toward(float(b.y), float(b.ty), 3.0)
		elif b.has("vy") and b.shape == "glyph" and float(b.y) > floor_y + 6.0:
			b.dead = true

static func _sentence_slot(s: Dictionary, k: int) -> bool:
	for spot: Vector2 in s.spots:
		if absf(_slot_x(k) - spot.x) < 10.0: return true
	return false

static func _type_plan(s: Dictionary) -> Array:
	var plan: Array = []
	plan.append("")
	while plan.size() < SLOTS:
		var length: int = 2 + int(D.rand(s) * 3.0)
		for i: int in range(length): plan.append(_letter(s))
		plan.append("")
		if D.rand(s) < 0.75: plan.append("")
	plan = plan.slice(0, SLOTS)
	for k: int in range(SLOTS):
		if _sentence_slot(s, k): plan[k] = ""
	return plan

static func _line_feed(s: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	for b: Dictionary in s.bullets:
		if not b.get("typed", false): continue
		b.row = int(b.row) + 1
		b.ty = h.y - 3.5 - 48.0 * int(b.row)
		if int(b.row) >= 2: b.fade = 16

# ---------------------------------------------------------------- Proofmarks
# ERRATA circles you as an error: the pen draws a red circle around where you
# stand, leaving one gap (facing into the page, or toward an open sentence),
# then the circle closes. Get out through the gap; whatever is left inside is
# deleted in a burst of x's.
# An underline then strikes along your line. Phase 1: a second, smaller circle
# overlaps the first and both gaps turn as they close.
static func _proofmarks(s: Dictionary, t: int, phase: int) -> void:
	if t == 0: D.box_to(s, {"w": 208.0, "h": 112.0}, 24)
	var every: int = 74 if phase == 0 else 66
	if t >= 14 and t <= 360 and (t - 14) % every == 0:
		var at: Vector2 = _soul(s)
		_circle(s, at, 44.0, 0.011 if phase > 0 else 0.0)
		if phase > 0:
			var off: Vector2 = Vector2.from_angle(D.rand(s) * TAU) * 30.0
			var h: Vector2 = D.half(s) - Vector2(20, 20)
			_circle(s, (at + off).clamp(-h, h), 30.0, -0.016, 40)
	if t >= 14 and t <= 372 and (t - 14) % every == 44:
		var h2: Vector2 = D.half(s)
		var from_left: bool = D.rand(s) < 0.5
		var y: float = clampf(float(s.soul.y), -h2.y + 6.0, h2.y - 6.0)
		_stroke(s, Vector2(-h2.x - 6.0 if from_left else h2.x + 6.0, y), Vector2.RIGHT if from_left else Vector2.LEFT, h2.x * 2.0 + 12.0, 8.0, 3.0, 28, 10, "strike")

static func _circle(s: Dictionary, at: Vector2, radius: float, spin: float, arm: int = 28) -> void:
	var inward: float = (-at).angle() if at.length() > 14.0 else D.rand(s) * TAU
	var gap: float = inward + D.rand_range(s, -0.6, 0.6)
	# Around a pause, the way out of the circle faces the kept sentence.
	var t: int = int(s.clock) - int(s.leadIn)
	for i: int in range(3):
		var o: Dictionary = s.objectives[i]
		if not o.done and t >= WINDOWS[i] - 40 and t < WINDOWS[i] + OPEN and Vector2(float(o.x), float(o.y)).distance_to(at) > 10.0:
			gap = (Vector2(float(o.x), float(o.y)) - at).angle() + D.rand_range(s, -0.25, 0.25)
	D.shot(s, {"space": "box", "x": at.x, "y": at.y, "collide": "ring", "radius": radius, "grow": 0.0, "thick": 2.5, "gap": gap, "gapWidth": 1.05, "gapSpin": 0.0,
		"spinAfter": spin, "arm": arm, "shape": "redring", "life": 400, "maxRadius": 999.0, "contract": 0.85})

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v) -> void:
	var h: Vector2 = D.half(s)
	var t: int = int(s.clock) - int(s.leadIn)
	# A ruled page with a red margin.
	for y: float in ROWS:
		if absf(y) > h.y: continue
		c.draw_line(v.box_point(Vector2(-h.x, y)), v.box_point(Vector2(h.x, y)), Color(0.56, 0.68, 0.92, 0.10), 1)
	c.draw_line(v.box_point(Vector2(-h.x + 16.0, -h.y)), v.box_point(Vector2(-h.x + 16.0, h.y)), Color(RED, 0.18), 1)
	# The kept sentence: faint words, a closing timer under it while open.
	if bool(s.promised):
		for i: int in range(3):
			var o: Dictionary = s.objectives[i]
			if not o.active: continue
			var left: float = 1.0 - float(t - WINDOWS[i]) / float(OPEN)
			var base: Vector2 = Vector2(float(o.x) - 9.0, float(o.y) + 13.0)
			c.draw_line(v.box_point(base), v.box_point(base + Vector2(18.0 * clampf(left, 0.0, 1.0), 0)), MINT, 2)
			for j: int in range(3):
				var y2: float = float(o.y) - 5.0 + j * 4.0
				c.draw_line(v.box_point(Vector2(float(o.x) - 6.0, y2)), v.box_point(Vector2(float(o.x) + 6.0 - j * 3.0, y2)), Color(MINT, 0.5), 1)
	for w: Dictionary in s.warnings:
		if w.kind == "sentence":
			var blink: float = 0.4 + 0.4 * sin(float(w.age) * 0.5)
			var r: Rect2 = Rect2(Vector2(float(w.x) - 9.0, float(w.y) - 10.0), Vector2(18, 20))
			var poly: PackedVector2Array = v.box_rect_poly(r)
			poly.append(poly[0])
			_dashed_poly(c, poly, Color(MINT, blink))
	if s.patternId == "typewriter" and s.has("tw"):
		var tw: Dictionary = s.tw
		var from: int = int(tw.k) if str(tw.state) != "return" else SLOTS
		for k: int in range(from, SLOTS):
			var ch: String = str(tw.plan[k])
			if ch.is_empty(): continue
			_glyph(c, v, v.box_point(Vector2(_slot_x(k), h.y - 3.5)), ch, Color(PAPER, 0.16), 12)
	if s.patternId == "anagram":
		for b: Dictionary in s.bullets:
			if not b.has("move"): continue
			var m: Dictionary = b.move
			if t >= int(m.t0) + int(m.dur): continue
			var alpha: float = 0.55 if t < int(m.t0) else 0.18
			for j: int in range(1, 12):
				c.draw_circle(v.box_point(_move_point(m, j / 12.0)), 1.0, Color(PINK, alpha))

static func draw_over(_c: CanvasItem, _s: Dictionary, _v) -> void:
	pass

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v) -> bool:
	match str(b.shape):
		"strike", "caret":
			var k: Dictionary = b.stroke
			var o: Vector2 = Vector2(float(k.ox), float(k.oy))
			var d: Vector2 = Vector2(float(k.dx), float(k.dy))
			var a: Vector2 = v.box_point(o)
			if int(b.age) <= int(k.warn):
				var blink: float = 0.35 + 0.3 * sin(float(b.age) * 0.6)
				_dashed(c, a, v.box_point(o + d * float(k.len)), Color(PINK, blink * alpha))
				if b.shape == "caret":
					_glyph(c, v, v.box_point(o + d * 7.0), "^", Color(RED, 0.9 * alpha), 12)
				return true
			var head: Vector2 = v.box_point(o + d * float(k.cur))
			c.draw_line(a, head, Color(RED, 0.95 * alpha), float(b.h) * 2.0)
			c.draw_line(a, head, Color(1.0, 0.72, 0.66, 0.45 * alpha), 1)
			if float(k.cur) < float(k.len):
				var dir: Vector2 = (head - a).normalized()
				var side: Vector2 = dir.orthogonal()
				c.draw_colored_polygon(PackedVector2Array([head + dir * 5.0, head - dir * 3.0 + side * 4.0, head - dir * 3.0 - side * 4.0]), Color(DARK, alpha))
				c.draw_line(head - dir * 2.0, head + dir * 5.0, Color(RED, alpha), 1)
			return true
		"glyph":
			var big: bool = b.get("big", false)
			if big:
				c.draw_rect(Rect2(at - Vector2(6, 7), Vector2(12, 14)), Color(DARK, 0.85 * alpha))
				c.draw_rect(Rect2(at - Vector2(6, 7), Vector2(12, 14)), Color(PINK, alpha * (1.0 if int(b.age) > int(b.arm) else 0.35)), false, 1)
			var ch: String = str(b.ch)
			if not big and (ch == "." or ch == ","):
				c.draw_circle(at, 2.8, Color(DARK, alpha))
				c.draw_circle(at, 2.0, Color(Color("f2b0a8"), alpha))
				if ch == ",": c.draw_line(at + Vector2(1, 1), at + Vector2(-1, 4), Color(Color("f2b0a8"), alpha), 1)
				return true
			if not big: c.draw_circle(at, 4.0, Color(DARK, 0.7 * alpha))
			_glyph(c, v, at, ch, Color(PAPER if big else Color("f2b0a8"), alpha), 12)
			return true
		"type":
			var col: Color = PAPER if int(b.age) > int(b.arm) else RED
			c.draw_rect(Rect2(at - Vector2(4, 3.5), Vector2(8, 7)), Color(DARK, alpha))
			_glyph(c, v, at + Vector2(0, 0.5), str(b.ch), Color(col, alpha), 12)
			return true
		"cursor":
			var lit: bool = int(b.age) > int(b.arm)
			var blink2: bool = (int(b.age) / 8) % 2 == 0
			c.draw_rect(Rect2(at - Vector2(2, 7), Vector2(4, 14)), Color(RED if lit else PINK, alpha * (1.0 if lit or blink2 else 0.3)))
			c.draw_line(at + Vector2(-4, -7), at + Vector2(4, -7), Color(RED, alpha), 1)
			c.draw_line(at + Vector2(-4, 7), at + Vector2(4, 7), Color(RED, alpha), 1)
			return true
		"redring":
			var gw: float = float(b.gapWidth) * 0.5
			var g: float = float(b.gap) + turn - float(b.rot)
			var r: float = float(b.radius)
			if int(b.age) <= int(b.arm):
				# The pen draws the circle around you, starting at the gap.
				var p: float = clampf(float(b.age) / float(maxi(1, int(b.arm) - 4)), 0.0, 1.0)
				c.draw_arc(at, r, g + gw, g + gw + (TAU - gw * 2.0) * p, 40, Color(PINK, 0.75 * alpha), 1.5)
				var tip: Vector2 = at + Vector2.from_angle(g + gw + (TAU - gw * 2.0) * p) * r
				c.draw_circle(tip, 2.0, Color(RED, alpha))
				return true
			c.draw_arc(at, r, g + gw, g + TAU - gw, maxi(16, int(r)), Color(RED, 0.95 * alpha), 4.0)
			c.draw_arc(at, r + 0.5, g + gw, g + TAU - gw, maxi(16, int(r)), Color(1.0, 0.75, 0.7, 0.4 * alpha), 1.0)
			return true
	return false

static func _glyph(c: CanvasItem, v, at: Vector2, ch: String, color: Color, size: int) -> void:
	var font: Font = v.font
	if font == null:
		c.draw_circle(at, 3.0, color)
		return
	c.draw_string(font, at + Vector2(-10.0, size * 0.36), ch, HORIZONTAL_ALIGNMENT_CENTER, 20.0, size, color)

static func _dashed(c: CanvasItem, a: Vector2, b: Vector2, color: Color) -> void:
	var length: float = a.distance_to(b)
	var dir: Vector2 = (b - a) / maxf(1.0, length)
	var x: float = 0.0
	while x < length:
		c.draw_line(a + dir * x, a + dir * minf(length, x + 5.0), color, 1)
		x += 9.0

static func _dashed_poly(c: CanvasItem, poly: PackedVector2Array, color: Color) -> void:
	for i: int in range(poly.size() - 1):
		_dashed(c, poly[i], poly[i + 1], color)
