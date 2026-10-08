extends RefCounted
## AUTOCOMPLETE: a generic, unbranded AI writing assistant. It swallowed one
## student's humming and now finishes every possible future sentence for
## everyone, confidently and wrongly. (A theme-only re-skin of INDEX: every
## mechanic, timing, random draw, state field, promise rule and progress string
## matches core/dodge_patterns_index.gd; only the look, banners, titles and hint
## text differ, so `stats autocomplete` equals `stats index` row for row.)
## Four handmade attacks, one per turn, cycling: runaway paragraphs (page walls),
## streaming sentences (sliding stacks), suggestion popups (drawers) and a tree
## of possible completions (the branching endings).
## The promise: confirm at the green suggestion at the top centre to accept it,
## then confirm at the dashed STOP box near the bottom (left on verses 1 and 3,
## right on verse 2) so that one sentence is allowed to end.
## Verses: 0 Finishing Your Sentence, 1 Context Window Closing (the text column
## narrows and drifts: the old moving margins), 2 Where Does It Stop? (one more
## layer per attack on top of the narrowing column).
## Look: ghost text typing itself in grey with a blinking caret, a context-window
## bar, accept chips, a loading spinner, a regenerate arrow, red autocorrect
## squiggles under stray typos and falling words, and confidently wrong [1][2][3]
## citations. No real product, company or person is named.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["page_turn", "stacks", "catalogue", "endings"]
const PHASES: Array[int] = [0, 1, 2]
const LENGTH: int = 540
## main.gd draws "<stage> / <title>" in a heading 26 glyphs wide: every stage
## name plus " /" stays within 25 glyphs, so each title gets its own line.
const NAMES: Array[String] = ["Finishing Your Sentence", "Context Window Closing", "Where Does It Stop?"]
const TITLES: Dictionary = {
	"page_turn": "Runaway Paragraphs", "stacks": "Streaming Sentences",
	"catalogue": "Suggestion Popups", "endings": "Possible Completions",
}
## Banners are drawn 8 px a glyph in a 200 px strip: 25 glyphs at most.
const BANNER_ACCEPT: String = "SUGGESTION ACCEPTED"
const BANNER_REGEN: String = "IT REGENERATES"
const BANNER_MIND: String = "IT CHANGES ITS MIND"
const LANE_Y: Array[float] = [-26.0, 0.0, 26.0]
const DRAWER_Y: Array[float] = [-42.0, -14.0, 14.0, 42.0]
const TREE_LEN: Array[float] = [58.0, 50.0, 44.0, 38.0]
const TREE_SPREAD: Array[float] = [0.55, 0.40, 0.28]
## Stray typos that fall off each runaway paragraph (only the count matters).
const LETTERS: String = "teaoinshrdlucmfwypvbg"
## Confident ghost text that types itself behind everything, one row each.
const GHOST_LINES: Array[String] = ["...and then you will", "...so everything is fine", "...as everyone knows [1]", "...which proves it [2][3]", "...and that is the end", "...it was always going to", "...and that is why you"]
const PAPER: Color = Color("dfe4f2")
const GHOST: Color = Color("9aa4c2")
const SKY: Color = Color("7fb0f0")
const ROSE: Color = Color("e8837b")
const MINT: Color = Color("b9d5bc")
const VIOLET: Color = Color("a68db8")
const SLATE: Color = Color("232a44")
const DARK: Color = Color("12162a")
const TOKENS: Array[Color] = [Color("5a6a9c"), Color("6e5c9c"), Color("4f8294"), Color("8a6a92"), Color("6f80ae")]

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	var stage: int = clampi(int(s.phase), 0, 2)
	s.patternId = id
	s.length = LENGTH
	s.phaseName = "%s / %s" % [NAMES[stage], TITLES[id]]
	s.carryBookmark = false
	s.bookmarkDelivered = false
	s.returnX = 48.0 if int(s.phase) % 2 == 0 else 208.0
	s.botGoal = null
	s.bannerColor = SKY
	match id:
		"page_turn":
			s.hint = "Paragraphs sweep across. Slip through each gap. Confirm the green suggestion, then STOP."
		"stacks":
			s.hint = "Sentences stream past. Cross at the missing words. Confirm the green suggestion, then STOP."
		"catalogue":
			s.hint = "Popups slam out where outlined. Confirm the green suggestion, then the STOP box."
		"endings":
			s.hint = "Completions branch out. Stand between the lines. Confirm the green suggestion, then STOP."
	D.objective(s, {"kind": "confirm", "x": 0.0, "y": -36.0, "r": 18.0})
	D.objective(s, {"kind": "confirm", "x": float(s.returnX) - 128.0, "y": 36.0, "r": 18.0, "active": false})

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return bool(s.bookmarkDelivered)

static func progress(s: Dictionary) -> String:
	return "Suggestion kept / STOP reached" if s.bookmarkDelivered else "Take it to the STOP box\nConfirm to stop" if s.carryBookmark else "Accept the green suggestion\nConfirm at top center"

static func tick(s: Dictionary, t: int) -> void:
	var stage: int = clampi(int(s.phase), 0, 2)
	if stage >= 1 and t >= 30: _margins(s, t)
	match str(s.patternId):
		"page_turn": _page_turn(s, t, stage)
		"stacks": _stacks(s, t, stage)
		"catalogue": _catalogue(s, t, stage)
		"endings": _endings(s, t, stage)
	_grow(s)
	_place_objectives(s)

static func after(s: Dictionary, _t: int) -> void:
	var pick: Dictionary = s.objectives[0]
	var slot: Dictionary = s.objectives[1]
	if pick.done and not slot.done and not slot.active:
		slot.active = true
		D.banner(s, BANNER_ACCEPT, 40)
	s.carryBookmark = bool(pick.done) and not bool(slot.done)
	s.bookmarkDelivered = bool(slot.done)

## The green suggestion and the STOP box keep their old spots while the box is
## full size and stay inside it while the margins move.
static func _place_objectives(s: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	var pick: Dictionary = s.objectives[0]
	var slot: Dictionary = s.objectives[1]
	pick.x = 0.0; pick.y = -minf(36.0, h.y - 14.0)
	slot.x = signf(float(s.returnX) - 128.0) * minf(80.0, h.x - 22.0); slot.y = minf(36.0, h.y - 14.0)

## Moving Margins: the box's side walls drift in and out and the page slides.
static func _margins(s: Dictionary, t: int) -> void:
	var base: float = float(s.get("baseW", 248.0))
	var u: float = float(t - 30)
	s.box.w = base - 44.0 * (0.5 - 0.5 * cos(u * 0.021))
	s.box.cx = 128.0 + 14.0 * sin(u * 0.013)

static func _soul(s: Dictionary) -> Vector2:
	return Vector2(float(s.soul.x), float(s.soul.y))

static func _letter(s: Dictionary) -> String:
	return LETTERS.substr(int(D.rand(s) * LETTERS.length()), 1)

# ---------------------------------------------------------------- strokes

static func _stroke(s: Dictionary, from: Vector2, dir: Vector2, length: float, speed: float, thick: float, warn: int, linger: int, shape: String, extra: Dictionary = {}) -> Dictionary:
	var props: Dictionary = {"space": "box", "x": from.x, "y": from.y, "collide": "rect", "w": 0.5, "h": thick, "rot": dir.angle(), "shape": shape, "arm": warn,
		"life": warn + int(ceil(length / speed)) + linger + 40,
		"stroke": {"ox": from.x, "oy": from.y, "dx": dir.x, "dy": dir.y, "len": length, "speed": speed, "warn": warn, "linger": linger, "cur": 0.0, "full": false, "fullAt": 0}}
	props.merge(extra, true)
	return D.shot(s, props)

static func _grow(s: Dictionary) -> void:
	var tips: Array = []
	for b: Dictionary in s.bullets:
		if not b.has("stroke") or b.has("fade"): continue
		var k: Dictionary = b.stroke
		var grown: float = clampf(float(int(b.age) - int(k.warn)) * float(k.speed), 0.0, float(k.len))
		var d: Vector2 = Vector2(float(k.dx), float(k.dy))
		var mid: Vector2 = Vector2(float(k.ox), float(k.oy)) + d * grown * 0.5
		b.x = mid.x; b.y = mid.y; b.w = maxf(0.5, grown * 0.5)
		k.cur = grown
		if grown >= float(k.len) and not bool(k.full):
			k.full = true; k.fullAt = int(b.age)
			if b.get("tip", false): tips.append([Vector2(float(k.ox), float(k.oy)) + d * float(k.len), d])
		if bool(k.full) and int(b.age) - int(k.fullAt) >= int(k.linger): b.fade = 14
	# Useful Stopping Point: each finished ending lets go of a little card.
	for tip: Array in tips:
		var dir: Vector2 = tip[1]
		D.shot(s, {"space": "box", "x": tip[0].x, "y": tip[0].y, "vx": dir.x * 0.8, "vy": dir.y * 0.8, "collide": "rect", "w": 3.5, "h": 2.5, "rot": dir.angle(), "shape": "chip", "life": 150})

# ---------------------------------------------------------------- Runaway Paragraphs
# Paragraphs of confident text sweep across the box, right to left like reading
# (INDEX's page turns): each is a wall that moves slowly at the edges and fast
# through the middle, with one missing line. Streaming dots and a chevron mark
# each gap on the entry wall before the paragraph runs. Paragraphs come in
# chapters of three, 24 ticks apart, their gaps stepping up or down like a
# staircase, then a breath. Stray typos shake loose from each paragraph as it
# crosses the middle. Verse 3: the last paragraph of each chapter regenerates
# and runs back from the left through the same gap as the one before it.
static func _page_turn(s: Dictionary, t: int, stage: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		s.baseW = 248.0
		D.box_to(s, {"w": 248.0, "h": 116.0}, 24)
		s.gapY = 0.0
		s.holdGap = 0
	var r: int = (t - 16) % 104
	if t >= 16 and t <= 400 and r % 24 == 0 and r < 72:
		var idx: int = r / 24
		var dir: int = -1
		var lim: float = h.y - 17.0
		if idx == 0:
			s.gapY = clampf(float(s.gapY) + D.rand_range(s, -30.0, 30.0), -lim, lim)
			s.stepDir = 1.0 if D.rand(s) < 0.5 else -1.0
			if absf(float(s.gapY)) > lim - 40.0: s.stepDir = -signf(float(s.gapY))
		elif stage >= 2 and idx == 2:
			dir = 1
			D.banner(s, BANNER_REGEN, 40)
		else:
			s.gapY = clampf(float(s.gapY) + float(s.stepDir) * 26.0, -lim, lim)
		for part: int in range(2):
			D.shot(s, {"space": "box", "x": -dir * (h.x + 4.0), "y": 0.0, "collide": "rect", "w": 3.0, "h": 1.0, "shape": "runon", "arm": 30, "life": 140,
				"page": {"dir": dir, "gap": float(s.gapY), "gh": 15.0, "warn": 30, "dur": 66, "part": part}})
	var drops: Array = []
	for b: Dictionary in s.bullets:
		if not b.has("page"): continue
		var pg: Dictionary = b.page
		var p: float = clampf(float(int(b.age) - int(pg.warn)) / float(pg.dur), 0.0, 1.0)
		b.x = -int(pg.dir) * (h.x + 4.0) * cos(p * PI)
		var top: float = -h.y - 4.0
		var bottom: float = h.y + 4.0
		if int(pg.part) == 0:
			bottom = float(pg.gap) - float(pg.gh)
		else:
			top = float(pg.gap) + float(pg.gh)
		b.y = (top + bottom) * 0.5; b.h = maxf(0.5, (bottom - top) * 0.5)
		if int(pg.part) == 0 and int(b.age) == int(pg.warn) + int(pg.dur) / 2: drops.append([float(b.x), float(pg.gap), int(pg.dir)])
		if p >= 1.0 and int(b.age) > int(pg.warn) + int(pg.dur) + 1: b.dead = true
	for drop: Array in drops:
		for i: int in range(2):
			var y: float = float(drop[1]) + (1.0 if i == 0 else -1.0) * D.rand_range(s, 24.0, 44.0)
			if absf(y) > h.y - 4.0: continue
			D.shot(s, {"space": "box", "x": float(drop[0]), "y": y, "vx": int(drop[2]) * 0.55, "vy": D.rand_range(s, -0.15, 0.15), "r": 3.0, "shape": "typo", "ch": _letter(s), "arm": 6, "life": 130})

# ---------------------------------------------------------------- Streaming Sentences
# Three sentences of word tokens stream across the box in alternating
# directions, with gaps where words are missing: cross from the suggestion at
# the top to the STOP box at the bottom through the gaps, resting on the thin
# baselines between sentences. Loose tokens wobble under a red squiggle, then
# drop out of their sentence, and a confidently wrong [1][2][3] citation block
# rolls along the top or bottom aisle, so you have to step into a gap as it
# passes. Verse 3: the middle sentence changes its mind and reverses twice
# (a regenerate arrow warns first).
static func _stacks(s: Dictionary, t: int, stage: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		s.baseW = 240.0
		D.box_to(s, {"w": 240.0, "h": 120.0}, 20)
		s.shelves = [{"dir": 1, "speed": 0.95, "room": 0.0, "run": 0}, {"dir": -1, "speed": 1.3, "room": 0.0, "run": 0}, {"dir": 1, "speed": 1.1, "room": 0.0, "run": 0}]
		for lane: int in range(3):
			var shelf: Dictionary = s.shelves[lane]
			var x: float = -int(shelf.dir) * 132.0
			while absf(x) <= 132.0:
				var step: float = _next_book(s, lane, x, 40)
				x += int(shelf.dir) * step
			shelf.room = 12.0
	for lane: int in range(3):
		var shelf: Dictionary = s.shelves[lane]
		shelf.room = float(shelf.room) - float(shelf.speed)
		if float(shelf.room) <= 0.0:
			var entry: float = -int(shelf.dir) * (h.x + 10.0)
			shelf.room = _next_book(s, lane, entry, 0)
	if stage >= 2:
		for at: int in [170, 330]:
			if t == at - 40:
				D.warn(s, {"kind": "shelf_turn", "y": LANE_Y[1], "dir": -int(s.shelves[1].dir)}, 40, true)
				D.banner(s, BANNER_MIND, 40)
			if t == at:
				s.shelves[1].dir = -int(s.shelves[1].dir)
				for b: Dictionary in s.bullets:
					if b.get("book", false) and int(b.lane) == 1 and not b.has("fall"): b.vx = -float(b.vx)
	if t >= 60 and t <= 400 and (t - 60) % 84 == 0:
		var top: bool = ((t - 60) / 84) % 2 == 0
		var side: float = -1.0 if D.rand(s) < 0.5 else 1.0
		var y: float = -47.0 if top else 47.0
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 4.0), "y": y, "dir": Vector2(-side, 0)}, 40, true)
		D.shot(s, {"space": "box", "x": side * (h.x + 20.0 + 2.2 * 40.0), "y": y, "vx": -side * 2.2, "collide": "rect", "w": 18.0, "h": 9.0, "shape": "citation", "life": 260})
	if t >= 40 and t <= 420 and t % 46 == 0:
		var pick: Array = []
		for b: Dictionary in s.bullets:
			if b.get("book", false) and not b.has("fall") and absf(float(b.x)) < h.x - 30.0: pick.append(b)
		if not pick.is_empty():
			var b: Dictionary = pick[int(D.rand(s) * pick.size())]
			b.fall = 26
	for b: Dictionary in s.bullets:
		if b.has("fall"):
			b.fall = int(b.fall) - 1
			if int(b.fall) > 0:
				b.rot = 0.22 * sin(float(b.fall) * 0.9)
			elif int(b.fall) == 0:
				b.vx = float(b.vx) * 0.4; b.vy = 0.4; b.ay = 0.13; b.spin = 0.05 * signf(float(b.vx) + 0.01)
				b.book = false
		if b.get("book", false) and absf(float(b.x)) > h.x + 14.0 and signf(float(b.x)) == signf(float(b.vx)):
			b.dead = true

## Spawns the next book (or leaves a gap) at x on a shelf; returns the room it
## takes before the next one.
static func _next_book(s: Dictionary, lane: int, x: float, arm: int) -> float:
	var shelf: Dictionary = s.shelves[lane]
	if int(shelf.run) <= 0:
		shelf.run = 3 + int(D.rand(s) * 5.0)
		return D.rand_range(s, 28.0, 46.0)
	shelf.run = int(shelf.run) - 1
	var half_w: float = D.rand_range(s, 2.5, 5.0)
	var half_h: float = D.rand_range(s, 5.0, 6.5)
	# Leave the middle clear at the start, where the soul stands.
	if arm > 0 and lane == 1 and absf(x) < 20.0: return half_w * 2.0 + 1.5
	D.shot(s, {"space": "box", "x": x, "y": LANE_Y[lane] + (6.5 - half_h), "vx": int(shelf.dir) * float(shelf.speed), "collide": "rect", "w": half_w, "h": half_h,
		"shape": "token", "hue": int(D.rand(s) * TOKENS.size()), "book": true, "lane": lane, "arm": arm, "life": 2000})
	return half_w * 2.0 + 1.5

# ---------------------------------------------------------------- Suggestion Popups
# The walls are text fields. Popups are outlined first, then slam out from the
# walls, hold, and slide back: a snake path, pincers, or a pull aimed at your
# row. Open popups flick suggestion chips at you. Verse 3: two popups drop from
# the ceiling and join the snake patterns.
static func _catalogue(s: Dictionary, t: int, stage: int) -> void:
	if t == 0:
		s.baseW = 256.0
		D.box_to(s, {"w": 256.0, "h": 120.0}, 20)
		s.pull = int(D.rand(s) * 4.0)
	if t >= 20 and t <= 420 and (t - 20) % 74 == 0:
		_pull(s, stage)
	var h: Vector2 = D.half(s)
	var cards: Array = []
	for b: Dictionary in s.bullets:
		if not b.has("drawer"): continue
		var dw: Dictionary = b.drawer
		var age: int = int(b.age) - int(dw.warn)
		var open: float = 0.0
		if age > 0:
			if age <= 10: open = 1.0 - pow(1.0 - age / 10.0, 2.0)
			elif age <= 38: open = 1.0
			elif age <= 56: open = 1.0 - (age - 38) / 18.0
			else: b.dead = true
		if age == 10 and bool(dw.get("cards", true)): cards.append(b)
		var depth: float = float(dw.depth) * open
		if bool(dw.get("top", false)):
			b.x = float(dw.at); b.y = -h.y + depth * 0.5; b.w = 12.0; b.h = maxf(0.5, depth * 0.5)
		else:
			var wall: float = float(dw.side) * h.x
			b.x = wall - float(dw.side) * depth * 0.5; b.y = float(dw.at); b.w = maxf(0.5, depth * 0.5); b.h = 12.0
	for b: Dictionary in cards:
		var dw2: Dictionary = b.drawer
		var face: Vector2 = Vector2(float(b.x) - float(dw2.side) * float(b.w), float(b.y))
		var aim: float = (_soul(s) - face).angle()
		for i: int in range(1 + mini(1, stage)):
			var a: float = aim + (i - 0.5 * mini(1, stage)) * 0.35 + D.rand_range(s, -0.08, 0.08)
			D.shot(s, {"space": "box", "x": face.x, "y": face.y, "vx": cos(a) * 1.6, "vy": sin(a) * 1.6, "collide": "rect", "w": 3.5, "h": 2.5, "rot": a, "shape": "chip", "life": 200})

static func _pull(s: Dictionary, stage: int) -> void:
	var h: Vector2 = D.half(s)
	var scale: float = h.x / 128.0
	s.pull = (int(s.pull) + 1 + int(D.rand(s) * 2.0)) % 4
	var soul_row: int = 0
	for i: int in range(4):
		if absf(DRAWER_Y[i] - float(s.soul.y)) < absf(DRAWER_Y[soul_row] - float(s.soul.y)): soul_row = i
	match int(s.pull):
		0, 1:
			var flip: int = int(s.pull)
			for i: int in range(4):
				_drawer(s, -1 if (i + flip) % 2 == 0 else 1, DRAWER_Y[i], 104.0 * scale, i * 3)
			if stage >= 2:
				for x: float in [-60.0, 60.0]:
					D.shot(s, {"space": "box", "x": x, "y": -h.y, "collide": "rect", "w": 12.0, "h": 0.5, "shape": "popup", "arm": 32, "life": 200, "drawer": {"top": true, "at": x, "depth": 46.0, "warn": 32, "side": 0, "cards": false}})
		2:
			_drawer(s, -1, DRAWER_Y[1], 96.0 * scale, 0)
			_drawer(s, 1, DRAWER_Y[1], 96.0 * scale, 0)
			_drawer(s, -1, DRAWER_Y[2], 96.0 * scale, 4)
			_drawer(s, 1, DRAWER_Y[2], 96.0 * scale, 4)
			_drawer(s, -1, DRAWER_Y[0], 170.0 * scale, 8)
			_drawer(s, 1, DRAWER_Y[3], 170.0 * scale, 8)
		3:
			_drawer(s, -1, DRAWER_Y[soul_row], 100.0 * scale, 0)
			_drawer(s, 1, DRAWER_Y[soul_row], 100.0 * scale, 0)
			var side: int = -1 if D.rand(s) < 0.5 else 1
			for r: int in [soul_row - 1, soul_row + 1]:
				if r >= 0 and r < 4:
					_drawer(s, side, DRAWER_Y[r], 150.0 * scale, 6)
					side = -side

static func _drawer(s: Dictionary, side: int, y: float, depth: float, delay: int) -> void:
	var h: Vector2 = D.half(s)
	D.shot(s, {"space": "box", "x": side * h.x, "y": y, "collide": "rect", "w": 0.5, "h": 12.0, "shape": "popup", "arm": 32 + delay, "life": 200,
		"drawer": {"side": side, "at": y, "depth": depth, "warn": 32 + delay, "cards": true}})

# ---------------------------------------------------------------- Possible Completions
# "SIX HUNDRED POSSIBLE COMPLETIONS": a tree of futures branches out from a wall,
# fifteen lines splitting three times. The whole tree is drawn faint first, then
# it grows from its root; one branch is always laid through where you stand, so
# step into a wedge between lines. Trees come from the left, right, top and
# bottom. Verse 2: each finished branch lets go of a suggestion chip that drifts on.
# Verse 3: a mirrored tree grows from the opposite wall 20 ticks later.
static func _endings(s: Dictionary, t: int, stage: int) -> void:
	if t == 0:
		s.baseW = 248.0
		D.box_to(s, {"w": 248.0, "h": 116.0}, 24)
	var every: int = 62 if stage < 2 else 70
	if t >= 16 and t <= 410 and (t - 16) % every == 0:
		var n: int = (t - 16) / every
		var side: String = ["left", "right", "top", "left", "right", "bottom"][n % 6]
		_tree(s, side, stage)
		s.mirror = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}[side]
	if stage >= 2 and t >= 36 and t <= 410 and (t - 36) % every == 0:
		_tree(s, str(s.mirror), stage)

static func _tree(s: Dictionary, side: String, stage: int) -> void:
	var h: Vector2 = D.half(s)
	var angle: float = 0.0
	var scale: float = 1.0
	match side:
		"right": angle = PI
		"top": angle = PI / 2.0; scale = 0.62
		"bottom": angle = -PI / 2.0; scale = 0.62
	var forward: Vector2 = Vector2.from_angle(angle)
	var across: Vector2 = Vector2.from_angle(angle + PI / 2.0)
	var soul: Vector2 = _soul(s)
	# Root on the wall, shifted along it so one branch runs through the soul.
	var wall: Vector2 = -forward * Vector2(h.x + 2.0, h.y + 2.0).dot(forward.abs())
	var depth: float = (soul - wall).dot(forward)
	var offsets: Array = []
	_tree_offsets(Vector2.ZERO, 0.0, 0, scale, depth, offsets)
	var shift: float = 0.0
	if not offsets.is_empty(): shift = float(offsets[int(D.rand(s) * offsets.size())])
	var limit: float = (h.y if absf(forward.x) > 0.5 else h.x) - 10.0
	var along: float = clampf(soul.dot(across) - shift, -limit, limit)
	var root: Vector2 = wall + across * along
	_branch(s, root, angle, 0, 0, scale, stage)

## Collects the sideways offset of every branch at a given forward depth.
static func _tree_offsets(from: Vector2, angle: float, level: int, scale: float, depth: float, out: Array) -> void:
	var length: float = TREE_LEN[level] * scale
	var dir: Vector2 = Vector2.from_angle(angle)
	var end: Vector2 = from + dir * length
	if depth >= from.x and depth <= end.x and absf(dir.x) > 0.01:
		out.append(from.y + dir.y * (depth - from.x) / dir.x)
	if level < 3:
		_tree_offsets(end, angle + TREE_SPREAD[level], level + 1, scale, depth, out)
		_tree_offsets(end, angle - TREE_SPREAD[level], level + 1, scale, depth, out)

static func _branch(s: Dictionary, from: Vector2, angle: float, level: int, delay: int, scale: float, stage: int) -> void:
	var length: float = TREE_LEN[level] * scale
	var speed: float = 5.0
	var dir: Vector2 = Vector2.from_angle(angle)
	var grow_ticks: int = int(ceil(length / speed))
	var total: int = int(ceil((TREE_LEN[0] + TREE_LEN[1] + TREE_LEN[2] + TREE_LEN[3]) * scale / speed))
	var linger: int = 26 + total - (delay + grow_ticks)
	_stroke(s, from, dir, length, speed, 2.5, 34 + delay, linger, "branch", {"level": level, "tip": level == 3 and stage >= 1})
	if level < 3:
		var end: Vector2 = from + dir * length
		_branch(s, end, angle + TREE_SPREAD[level], level + 1, delay + grow_ticks, scale, stage)
		_branch(s, end, angle - TREE_SPREAD[level], level + 1, delay + grow_ticks, scale, stage)

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v) -> void:
	var h: Vector2 = D.half(s)
	var stage: int = clampi(int(s.phase), 0, 2)
	_ghost_text(c, s, v, h)
	# The text column: margin guides with ruler handles (they move from verse 2),
	# and the context-window bar along the top that fills as the column narrows.
	var margin: Color = Color(SKY, 0.30 if int(s.phase) >= 1 else 0.14)
	for side: float in [-1.0, 1.0]:
		var mx: float = side * (h.x - 10.0)
		c.draw_line(v.box_point(Vector2(mx, -h.y)), v.box_point(Vector2(mx, h.y)), margin, 1)
		if stage >= 1:
			var handle: Vector2 = v.box_point(Vector2(mx, -h.y + 1.0))
			c.draw_colored_polygon(PackedVector2Array([handle + Vector2(-3, 0), handle + Vector2(3, 0), handle + Vector2(0, 5)]), Color(SKY, 0.55))
	if stage >= 1: _context_bar(c, s, v, h)
	if s.patternId == "stacks":
		# Each sentence is typed along its own baseline.
		for y: float in LANE_Y:
			var baseline: Rect2 = Rect2(Vector2(-h.x, y + 6.5), Vector2(h.x * 2.0, 2.0))
			c.draw_colored_polygon(v.box_rect_poly(baseline), Color(GHOST, 0.40))
	if s.patternId == "catalogue":
		# Where popups attach: a small chevron pointing in from each wall.
		for side: float in [-1.0, 1.0]:
			for y: float in DRAWER_Y:
				v.chevron(c, v.box_point(Vector2(side * (h.x - 4.0), y)), Vector2(-side, 0), Color(SKY, 0.40))
	for w: Dictionary in s.warnings:
		if w.kind == "shelf_turn":
			var dir: Vector2 = Vector2(float(w.dir), 0)
			for i: int in range(6):
				var x: float = fposmod(float(w.age) * 2.0 * dir.x + i * 44.0, h.x * 2.0) - h.x
				v.chevron(c, v.box_point(Vector2(x, float(w.y))), dir, Color(ROSE, 0.8))
			_regenerate(c, v.box_point(Vector2(0.0, float(w.y))), float(w.age), dir.x)
	# The STOP box is outlined for the whole turn while promised.
	if bool(s.promised) and not bool(s.bookmarkDelivered):
		var slot: Dictionary = s.objectives[1]
		var r: Rect2 = Rect2(Vector2(float(slot.x) - 11.0, float(slot.y) - 12.0), Vector2(22, 24))
		var poly: PackedVector2Array = v.box_rect_poly(r)
		poly.append(poly[0])
		var lit: float = 0.75 if s.carryBookmark else 0.4
		_dashed_poly(c, poly, Color(MINT, lit))
		var mid: Vector2 = v.box_point(Vector2(float(slot.x), float(slot.y)))
		c.draw_arc(mid, 7.0, 0.0, TAU, 16, Color(MINT, lit * 0.7), 1)
		c.draw_rect(Rect2(mid + Vector2(-3, -3), Vector2(6, 6)), Color(MINT, lit * 0.7))
		_label(c, v, v.box_point(Vector2(float(slot.x), float(slot.y) - 15.0)), "STOP", Color(MINT, lit))
		if not s.objectives[0].done:
			var pick: Vector2 = v.box_point(Vector2(float(s.objectives[0].x), float(s.objectives[0].y)))
			_accept_chip(c, pick + Vector2(0, -3), 1.0)
			# A loading spinner circles the suggestion until you accept it.
			var spin: float = float(s.clock) * 0.15
			c.draw_arc(pick, 14.0, spin, spin + 1.9, 8, Color(SKY, 0.85), 2)
			c.draw_arc(pick, 14.0, spin + PI, spin + PI + 1.0, 6, Color(SKY, 0.5), 2)
			_label(c, v, pick + Vector2(0, 26), "ACCEPT", Color(MINT, 0.6))

static func draw_over(c: CanvasItem, s: Dictionary, v) -> void:
	if bool(s.promised) and bool(s.carryBookmark):
		_accept_chip(c, v.box_point(_soul(s)) + Vector2(8, -6), 0.9)

## Ghost text types itself out to the right in grey, one confident sentence per
## row, each with a blinking caret, then fades and starts another.
static func _ghost_text(c: CanvasItem, s: Dictionary, v, h: Vector2) -> void:
	var font: Font = v.font
	if font == null: return
	var clock: int = int(s.clock)
	for i: int in range(-3, 4):
		var row: int = i + 3
		var shifted: int = clock + row * 41
		var local: int = shifted % 260
		var words: String = GHOST_LINES[(shifted / 260 + row) % GHOST_LINES.size()]
		var typed: int = mini(words.length(), local / 5)
		var fade: float = clampf(float(260 - local) / 30.0, 0.0, 1.0)
		var at: Vector2 = v.box_point(Vector2(-h.x + 16.0, i * 16.0 + 4.0))
		c.draw_string(font, at, words.substr(0, typed), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(GHOST, 0.11 * fade))
		if (clock / 18 + row) % 2 == 0:
			c.draw_rect(Rect2(at + Vector2(typed * 8.0 + 1.0, -9.0), Vector2(2, 11)), Color(SKY, 0.28 * fade))

## The context-window bar: full width is the whole window, the bright part is
## how much of it the narrowing column has used up.
static func _context_bar(c: CanvasItem, s: Dictionary, v, h: Vector2) -> void:
	var fill: float = clampf((float(s.get("baseW", 248.0)) - float(s.box.w)) / 44.0, 0.0, 1.0)
	var left: float = -(h.x - 10.0)
	var width: float = (h.x - 10.0) * 2.0
	var y: float = -h.y + 3.0
	c.draw_line(v.box_point(Vector2(left, y)), v.box_point(Vector2(left + width, y)), Color(SKY, 0.14), 2)
	c.draw_line(v.box_point(Vector2(left, y)), v.box_point(Vector2(left + width * fill, y)), Color(SKY, 0.65), 2)

## A circular arrow that turns the way the line is about to run.
static func _regenerate(c: CanvasItem, at: Vector2, age: float, dir: float) -> void:
	var sweep: float = 4.4
	var a0: float = signf(dir) * age * 0.16
	var a1: float = a0 + signf(dir) * sweep
	c.draw_arc(at, 9.0, minf(a0, a1), maxf(a0, a1), 16, Color(ROSE, 0.85), 2)
	var tip: Vector2 = at + Vector2.from_angle(a1) * 9.0
	var heading: Vector2 = Vector2.from_angle(a1 + signf(dir) * PI * 0.5)
	c.draw_polyline(PackedVector2Array([tip - heading * 3.0 + Vector2(-heading.y, heading.x) * 3.0, tip + heading * 2.0, tip - heading * 3.0 - Vector2(-heading.y, heading.x) * 3.0]), Color(ROSE, 0.95), 1)

## A label with the ghost text knocked out behind it so it reads at a glance.
static func _label(c: CanvasItem, v, at: Vector2, words: String, color: Color) -> void:
	var width: float = words.length() * 8.0
	c.draw_rect(Rect2(at + Vector2(-width * 0.5 - 1.0, -10.0), Vector2(width + 2.0, 13.0)), Color(0.04, 0.05, 0.09, 0.9))
	v.text(c, at, words, color, width + 8.0)

## The one useful suggestion: a mint accept chip with an arrow-and-bar mark.
static func _accept_chip(c: CanvasItem, at: Vector2, alpha: float) -> void:
	c.draw_rect(Rect2(at + Vector2(-7, -3.5), Vector2(14, 7)), Color(MINT, alpha))
	var ink: Color = Color(DARK, alpha)
	c.draw_line(at + Vector2(-4, 0), at + Vector2(1, 0), ink, 1)
	c.draw_polyline(PackedVector2Array([at + Vector2(-1, -2), at + Vector2(1.5, 0), at + Vector2(-1, 2)]), ink, 1)
	c.draw_line(at + Vector2(4, -2), at + Vector2(4, 2), ink, 1)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v) -> bool:
	var armed: bool = int(b.age) > int(b.arm)
	match str(b.shape):
		"runon":
			var pg: Dictionary = b.page
			var top: Vector2 = v.box_point(Vector2(float(b.x), float(b.y) - float(b.h)))
			var bottom: Vector2 = v.box_point(Vector2(float(b.x), float(b.y) + float(b.h)))
			if not armed:
				# Markers on the entry wall show where the missing line will be,
				# with typing dots streaming in from it.
				if int(pg.part) == 0:
					var edge: float = -int(pg.dir) * (D.half(v.pattern).x - 4.0)
					var blink: float = 0.5 + 0.4 * sin(float(b.age) * 0.5)
					for y: float in [float(pg.gap) - float(pg.gh), float(pg.gap) + float(pg.gh)]:
						c.draw_line(v.box_point(Vector2(edge - 6.0, y)), v.box_point(Vector2(edge + 6.0, y)), Color(SKY, blink * alpha), 2)
					v.chevron(c, v.box_point(Vector2(edge, float(pg.gap))), Vector2(float(pg.dir), 0), Color(SKY, blink * alpha))
					if int(pg.dir) > 0:
						# The paragraph that regenerates and runs back through the same gap.
						_regenerate(c, v.box_point(Vector2(edge + 17.0, float(pg.gap))), float(b.age), 1.0)
					else:
						for i: int in range(3):
							var wave: float = maxf(0.0, sin(float(b.age) * 0.35 - i * 0.9))
							c.draw_circle(v.box_point(Vector2(edge + int(pg.dir) * (11.0 + i * 7.0), float(pg.gap))), 1.6, Color(SKY, (0.3 + 0.7 * wave) * alpha))
					_dashed(c, v.box_point(Vector2(-D.half(v.pattern).x, float(pg.gap) - float(pg.gh))), v.box_point(Vector2(D.half(v.pattern).x, float(pg.gap) - float(pg.gh))), Color(SKY, 0.25 * alpha))
					_dashed(c, v.box_point(Vector2(-D.half(v.pattern).x, float(pg.gap) + float(pg.gh))), v.box_point(Vector2(D.half(v.pattern).x, float(pg.gap) + float(pg.gh))), Color(SKY, 0.25 * alpha))
				return true
			# A paragraph seen edge-on: wider through the middle, lines of text
			# running out raggedly, and a red autocorrect squiggle on the torn end.
			var p: float = clampf(float(int(b.age) - int(pg.warn)) / float(pg.dur), 0.0, 1.0)
			var lean: float = 2.0 + 5.0 * sin(p * PI)
			var poly: PackedVector2Array = PackedVector2Array([top + Vector2(-lean, 0), top + Vector2(lean, 0), bottom + Vector2(lean, 0), bottom + Vector2(-lean, 0)])
			c.draw_colored_polygon(poly, Color(PAPER, 0.95 * alpha))
			var y0: float = top.y + 4.0
			var line_no: int = 0
			while y0 < bottom.y - 2.0:
				var ragged: float = float(line_no % 3) * 1.4
				c.draw_line(Vector2(top.x - lean + 1.0, y0), Vector2(top.x + lean - 1.0 - ragged, y0), Color(Color("59628a"), 0.75 * alpha), 1)
				y0 += 5.0
				line_no += 1
			var torn: Vector2 = bottom if int(pg.part) == 0 else top
			_squiggle(c, torn + Vector2(-lean - 2.0, 0), torn + Vector2(lean + 2.0, 0), Color(ROSE, alpha), 1.5, 3.0)
			return true
		"token":
			var hw: float = float(b.w); var hh: float = float(b.h)
			var col: Color = TOKENS[int(b.get("hue", 0)) % TOKENS.size()]
			var a: float = alpha * (1.0 if armed else 0.45)
			c.draw_colored_polygon(v.quad(at, hw, hh, turn), Color(col, a))
			c.draw_line(at + Vector2(-hw, -hh * 0.45).rotated(turn), at + Vector2(hw, -hh * 0.45).rotated(turn), Color(PAPER, 0.7 * a), 1)
			c.draw_line(at + Vector2(-hw, hh * 0.5).rotated(turn), at + Vector2(hw, hh * 0.5).rotated(turn), Color(DARK, 0.5 * a), 1)
			if b.has("fall") and int(b.fall) > 0:
				# The assistant second-guesses a word: red underline and outline.
				c.draw_polyline(v.quad(at, hw + 1.5, hh + 1.5, turn) + PackedVector2Array([v.quad(at, hw + 1.5, hh + 1.5, turn)[0]]), Color(ROSE, a), 1)
				_squiggle(c, at + Vector2(-hw - 1.0, hh + 4.0).rotated(turn), at + Vector2(hw + 1.0, hh + 4.0).rotated(turn), Color(ROSE, a), 1.2, 3.0)
			return true
		"popup":
			var dw: Dictionary = b.drawer
			var h: Vector2 = D.half(v.pattern)
			if not armed:
				var blink: float = 0.35 + 0.35 * sin(float(b.age) * 0.55)
				var ghost: Rect2
				if bool(dw.get("top", false)):
					ghost = Rect2(Vector2(float(dw.at) - 12.0, -h.y), Vector2(24.0, float(dw.depth)))
				else:
					var wall: float = float(dw.side) * h.x
					ghost = Rect2(Vector2(minf(wall, wall - float(dw.side) * float(dw.depth)), float(dw.at) - 12.0), Vector2(float(dw.depth), 24.0))
				var poly: PackedVector2Array = v.box_rect_poly(ghost)
				c.draw_colored_polygon(poly, Color(ROSE, 0.06 + 0.06 * blink))
				poly.append(poly[0])
				_dashed_poly(c, poly, Color(ROSE, blink + 0.2))
				return true
			# A suggestion popup: a dark list with ghost-text rows, the first row
			# highlighted, and a bright leading edge.
			var body: Rect2 = Rect2(Vector2(float(b.x) - float(b.w), float(b.y) - float(b.h)), Vector2(float(b.w), float(b.h)) * 2.0)
			var drawn: PackedVector2Array = v.box_rect_poly(body)
			c.draw_colored_polygon(drawn, Color(SLATE, alpha))
			_popup_rows(c, v, b, dw, body, alpha)
			drawn.append(drawn[0])
			c.draw_polyline(drawn, Color(SKY, 0.85 * alpha), 1)
			if bool(dw.get("top", false)):
				var face: Vector2 = v.box_point(Vector2(float(b.x), float(b.y) + float(b.h) - 1.0))
				c.draw_line(face + Vector2(-12, 0), face + Vector2(12, 0), Color(PAPER, 0.9 * alpha), 2)
			else:
				var front: float = float(b.x) - float(dw.side) * float(b.w)
				c.draw_line(v.box_point(Vector2(front, float(b.y) - float(b.h))), v.box_point(Vector2(front, float(b.y) + float(b.h))), Color(PAPER, 0.9 * alpha), 3)
			return true
		"citation":
			# A confidently wrong citation block: [1][2][3].
			var slab: PackedVector2Array = v.quad(at, 18.0, 9.0, turn)
			c.draw_colored_polygon(slab, Color(Color("2c2438"), alpha))
			slab.append(slab[0])
			c.draw_polyline(slab, Color(ROSE, 0.9 * alpha), 1)
			var font: Font = v.font
			for i: int in range(3):
				var mid: float = -12.0 + i * 12.0
				for edge: float in [-1.0, 1.0]:
					var rail: float = mid + edge * 5.0
					c.draw_line(at + Vector2(rail, -6.0).rotated(turn), at + Vector2(rail, 6.0).rotated(turn), Color(PAPER, 0.8 * alpha), 1)
					c.draw_line(at + Vector2(rail, -6.0).rotated(turn), at + Vector2(rail - edge * 1.5, -6.0).rotated(turn), Color(PAPER, 0.8 * alpha), 1)
					c.draw_line(at + Vector2(rail, 6.0).rotated(turn), at + Vector2(rail - edge * 1.5, 6.0).rotated(turn), Color(PAPER, 0.8 * alpha), 1)
				if font != null:
					c.draw_string(font, at + Vector2(mid - 4.0, 4.5), str(i + 1), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(ROSE, alpha))
			return true
		"chip":
			# A suggestion chip flicked at you: a pale pill with an accept arrow.
			c.draw_colored_polygon(v.quad(at, 3.5, 2.5, turn), Color(PAPER, alpha))
			c.draw_polyline(PackedVector2Array([at + Vector2(-1.2, -1.3).rotated(turn), at + Vector2(1.2, 0).rotated(turn), at + Vector2(-1.2, 1.3).rotated(turn)]), Color(Color("3b5fa8"), alpha), 1)
			return true
		"branch":
			var k: Dictionary = b.stroke
			var o: Vector2 = Vector2(float(k.ox), float(k.oy))
			var d: Vector2 = Vector2(float(k.dx), float(k.dy))
			var a2: Vector2 = v.box_point(o)
			if not armed:
				var blink2: float = 0.25 + 0.2 * sin(float(b.age) * 0.5)
				_dashed(c, a2, v.box_point(o + d * float(k.len)), Color(VIOLET, blink2 * alpha + 0.15))
				return true
			var head: Vector2 = v.box_point(o + d * float(k.cur))
			c.draw_line(a2, head, Color(VIOLET, alpha), 5.0)
			c.draw_line(a2, head, Color(PAPER, 0.6 * alpha), 1.0)
			# A sentence forks at every node; each finished branch ends in "...".
			c.draw_circle(a2, 3.0, Color(SKY, alpha))
			if int(b.get("level", 0)) == 3 and bool(k.full):
				var along: Vector2 = Vector2.from_angle(turn)
				for i: int in range(3):
					c.draw_circle(head + along * (1.0 + i * 3.0), 1.1, Color(PAPER, alpha))
			return true
		"typo":
			# A stray typo shaken loose from the page, squiggled in red.
			c.draw_circle(at, 4.0, Color(SLATE, 0.85 * alpha))
			c.draw_arc(at, 4.0, 0.0, TAU, 12, Color(SKY, 0.5 * alpha), 1)
			_squiggle(c, at + Vector2(-4.5, 6.0), at + Vector2(4.5, 6.0), Color(ROSE, alpha * (1.0 if armed else 0.5)), 1.2, 3.0)
			var font: Font = v.font
			if font != null:
				c.draw_string(font, at + Vector2(-10.0, 4.3), str(b.ch), HORIZONTAL_ALIGNMENT_CENTER, 20.0, 12, Color(PAPER, alpha * (1.0 if armed else 0.5)))
			return true
	return false

## Rows of ghost text inside a popup; the first row is the highlighted choice.
static func _popup_rows(c: CanvasItem, v, b: Dictionary, dw: Dictionary, body: Rect2, alpha: float) -> void:
	var extent: float = body.size.x if not bool(dw.get("top", false)) else body.size.y
	if extent < 14.0: return
	var salt: int = int(b.id)
	if bool(dw.get("top", false)):
		var rows: int = mini(4, int((extent - 2.0) / 10.0))
		for r: int in range(rows):
			var y: float = body.position.y + 2.0 + r * 10.0
			if r == 0: c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(body.position.x + 1.0, y), Vector2(body.size.x - 2.0, 9.0))), Color(SKY, 0.35 * alpha))
			var len_top: float = 8.0 + float((salt * 37 + r * 23) % 11)
			c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(body.position.x + 4.0, y + 3.0), Vector2(len_top, 3.0))), Color(PAPER if r == 0 else GHOST, (0.9 if r == 0 else 0.6) * alpha))
		return
	for r: int in range(2):
		var y2: float = body.position.y + 2.0 + r * 11.0
		if r == 0: c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(body.position.x + 1.0, y2), Vector2(body.size.x - 2.0, 9.0))), Color(SKY, 0.35 * alpha))
		var length: float = minf(extent - 12.0, 30.0 + float((salt * 37 + r * 23) % 40))
		if length < 2.0: continue
		c.draw_colored_polygon(v.box_rect_poly(Rect2(Vector2(body.position.x + 5.0, y2 + 3.0), Vector2(length, 3.0))), Color(PAPER if r == 0 else GHOST, (0.9 if r == 0 else 0.6) * alpha))

## A zigzag underline, like the red line under a word the assistant dislikes.
static func _squiggle(c: CanvasItem, a: Vector2, b: Vector2, color: Color, amp: float, wave: float) -> void:
	var length: float = a.distance_to(b)
	var dir: Vector2 = (b - a) / maxf(1.0, length)
	var side: Vector2 = Vector2(-dir.y, dir.x)
	var steps: int = maxi(2, int(length / (wave * 0.5)))
	var points: PackedVector2Array = PackedVector2Array()
	for i: int in range(steps + 1):
		points.append(a + dir * (length * float(i) / float(steps)) + side * (amp if i % 2 == 0 else -amp))
	c.draw_polyline(points, color, 1)

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
