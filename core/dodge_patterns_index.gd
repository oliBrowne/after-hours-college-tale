extends RefCounted
## INDEX: the catalogue in Norlin's closed archive that files every possible
## future. "NOW FINISH EVERY FUTURE IT OPENED." Four handmade attacks, one per
## turn, cycling: pages that turn into walls, sliding stacks, card catalogue
## drawers and a branching tree of possible endings.
## The promise (Deliver one useful bookmark): confirm at the green bookmark at
## the top centre to pick it up, then confirm at the outlined return slot near
## the bottom (left on verses 1 and 3, right on verse 2) to file it.
## Verses: 0 Page Walls, 1 Moving Margins (the box's margins move), 2 Useful
## Stopping Point (one more layer per attack on top of the moving margins).

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["page_turn", "stacks", "catalogue", "endings"]
const PHASES: Array[int] = [0, 1, 2]
const LENGTH: int = 540
const NAMES: Array[String] = ["Page Walls", "Moving Margins", "Useful Stopping Point"]
const LANE_Y: Array[float] = [-26.0, 0.0, 26.0]
const DRAWER_Y: Array[float] = [-42.0, -14.0, 14.0, 42.0]
const TREE_LEN: Array[float] = [58.0, 50.0, 44.0, 38.0]
const TREE_SPREAD: Array[float] = [0.55, 0.40, 0.28]
const LETTERS: String = "ABCDEFGHIKLMNOPRSTUWY"
const PAPER: Color = Color("e6d6b1")
const CREAM: Color = Color("f1e6c8")
const ROSE: Color = Color("e8837b")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const LILAC: Color = Color("a68db8")
const WOOD: Color = Color("6c4a36")
const DARK: Color = Color("1a1420")
const SPINES: Array[Color] = [Color("8a4b4b"), Color("4b6a8a"), Color("6a7a4b"), Color("8a744b"), Color("6b4b8a")]

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	var stage: int = clampi(int(s.phase), 0, 2)
	s.patternId = id
	s.length = LENGTH
	s.phaseName = NAMES[stage]
	s.carryBookmark = false
	s.bookmarkDelivered = false
	s.returnX = 48.0 if int(s.phase) % 2 == 0 else 208.0
	s.botGoal = null
	s.bannerColor = AMBER
	match id:
		"page_turn":
			s.hint = "Pages turn across the box. Slip through each torn gap. Carry the bookmark to its slot."
		"stacks":
			s.hint = "Shelves slide past. Cross through the missing books. Carry the bookmark to its slot."
		"catalogue":
			s.hint = "Drawers slam out of the walls where outlined. Carry the bookmark to its slot."
		"endings":
			s.hint = "Possible endings branch out. Stand between the lines. Carry the bookmark to its slot."
	D.objective(s, {"kind": "confirm", "x": 0.0, "y": -36.0, "r": 18.0})
	D.objective(s, {"kind": "confirm", "x": float(s.returnX) - 128.0, "y": 36.0, "r": 18.0, "active": false})

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return bool(s.bookmarkDelivered)

static func progress(s: Dictionary) -> String:
	return "Bookmark filed / done" if s.bookmarkDelivered else "Carry to outlined slot\nConfirm to file it" if s.carryBookmark else "Pick up green bookmark\nConfirm at top centre"

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
		D.banner(s, "BOOKMARK", 40)
	s.carryBookmark = bool(pick.done) and not bool(slot.done)
	s.bookmarkDelivered = bool(slot.done)

## The bookmark and slot keep their old spots while the box is full size and
## stay inside it while the margins move.
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
		D.shot(s, {"space": "box", "x": tip[0].x, "y": tip[0].y, "vx": dir.x * 0.8, "vy": dir.y * 0.8, "collide": "rect", "w": 3.5, "h": 2.5, "rot": dir.angle(), "shape": "card", "life": 150})

# ---------------------------------------------------------------- Page Turns
# Pages of the catalogue turn across the box, right to left like reading: each
# page is a wall that moves slowly at the edges and fast through the spine,
# with one torn gap. Ribbons mark each gap before the page lifts. Pages come
# in chapters of three, 24 ticks apart, their gaps stepping up or down like a
# staircase, then a breath. Loose words slip off each page as it crosses the
# spine. Verse 3: the last page of each chapter flips back from the left
# through the same gap as the page before it.
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
			D.banner(s, "IT FLIPS BACK", 40)
		else:
			s.gapY = clampf(float(s.gapY) + float(s.stepDir) * 26.0, -lim, lim)
		for part: int in range(2):
			D.shot(s, {"space": "box", "x": -dir * (h.x + 4.0), "y": 0.0, "collide": "rect", "w": 3.0, "h": 1.0, "shape": "page", "arm": 30, "life": 140,
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
			D.shot(s, {"space": "box", "x": float(drop[0]), "y": y, "vx": int(drop[2]) * 0.55, "vy": D.rand_range(s, -0.15, 0.15), "r": 3.0, "shape": "glyph", "ch": _letter(s), "arm": 6, "life": 130})

# ---------------------------------------------------------------- Sliding Stacks
# Three shelves of books slide across the box in alternating directions, with
# gaps where books are missing: cross from the bookmark at the top to the slot
# at the bottom through the gaps, resting on the thin strips between shelves.
# Loose books wobble, then fall off their shelf, and a returns cart rolls along
# the top or bottom aisle, so you have to step into a shelf gap as it passes.
# Verse 3: the middle shelf reverses twice (arrows warn first).
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
				D.banner(s, "THE SHELF TURNS", 40)
			if t == at:
				s.shelves[1].dir = -int(s.shelves[1].dir)
				for b: Dictionary in s.bullets:
					if b.get("book", false) and int(b.lane) == 1 and not b.has("fall"): b.vx = -float(b.vx)
	if t >= 60 and t <= 400 and (t - 60) % 84 == 0:
		var top: bool = ((t - 60) / 84) % 2 == 0
		var side: float = -1.0 if D.rand(s) < 0.5 else 1.0
		var y: float = -47.0 if top else 47.0
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 4.0), "y": y, "dir": Vector2(-side, 0)}, 40, true)
		D.shot(s, {"space": "box", "x": side * (h.x + 20.0 + 2.2 * 40.0), "y": y, "vx": -side * 2.2, "collide": "rect", "w": 18.0, "h": 9.0, "shape": "cart", "life": 260})
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
		"shape": "book", "hue": int(D.rand(s) * SPINES.size()), "book": true, "lane": lane, "arm": arm, "life": 2000})
	return half_w * 2.0 + 1.5

# ---------------------------------------------------------------- Card Catalogue
# The walls are catalogue cabinets. Drawers are outlined first, then slam out
# from the walls, hold, and slide back: a snake path, pincers, or a pull aimed
# at your row. Open drawers flick index cards at you. Verse 3: two drawers in
# the ceiling join the snake patterns.
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
			D.shot(s, {"space": "box", "x": face.x, "y": face.y, "vx": cos(a) * 1.6, "vy": sin(a) * 1.6, "collide": "rect", "w": 3.5, "h": 2.5, "rot": a, "shape": "card", "life": 200})

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
					D.shot(s, {"space": "box", "x": x, "y": -h.y, "collide": "rect", "w": 12.0, "h": 0.5, "shape": "drawer", "arm": 32, "life": 200, "drawer": {"top": true, "at": x, "depth": 46.0, "warn": 32, "side": 0, "cards": false}})
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
	D.shot(s, {"space": "box", "x": side * h.x, "y": y, "collide": "rect", "w": 0.5, "h": 12.0, "shape": "drawer", "arm": 32 + delay, "life": 200,
		"drawer": {"side": side, "at": y, "depth": depth, "warn": 32 + delay, "cards": true}})

# ---------------------------------------------------------------- Possible Endings
# "SIX HUNDRED POSSIBLE ENDINGS": a tree of futures branches out from a wall,
# fifteen lines splitting three times. The whole tree is drawn faint first, then
# it grows from its root; one branch is always laid through where you stand, so
# step into a wedge between lines. Trees come from the left, right, top and
# bottom. Verse 2: each finished ending lets go of a card that drifts on.
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
	# Catalogue paper: faint lines, and the margins (they move from verse 2).
	for i: int in range(-3, 4):
		var y: float = i * 16.0
		c.draw_line(v.box_point(Vector2(-h.x, y)), v.box_point(Vector2(h.x, y)), Color(0.6, 0.55, 0.45, 0.07), 1)
	var margin: Color = Color(LILAC, 0.30 if int(s.phase) >= 1 else 0.14)
	for side: float in [-1.0, 1.0]:
		c.draw_line(v.box_point(Vector2(side * (h.x - 10.0), -h.y)), v.box_point(Vector2(side * (h.x - 10.0), h.y)), margin, 1)
	if s.patternId == "stacks":
		for y: float in LANE_Y:
			var shelf: Rect2 = Rect2(Vector2(-h.x, y + 6.5), Vector2(h.x * 2.0, 2.0))
			c.draw_colored_polygon(v.box_rect_poly(shelf), Color(WOOD, 0.75))
	if s.patternId == "catalogue":
		for side: float in [-1.0, 1.0]:
			for y: float in DRAWER_Y:
				var plate: Vector2 = v.box_point(Vector2(side * (h.x - 3.0), y))
				c.draw_rect(Rect2(plate - Vector2(2, 3), Vector2(4, 6)), Color(AMBER, 0.35))
	for w: Dictionary in s.warnings:
		if w.kind == "shelf_turn":
			var dir: Vector2 = Vector2(float(w.dir), 0)
			for i: int in range(6):
				var x: float = fposmod(float(w.age) * 2.0 * dir.x + i * 44.0, h.x * 2.0) - h.x
				v.chevron(c, v.box_point(Vector2(x, float(w.y))), dir, Color(ROSE, 0.8))
	# The return slot is outlined for the whole turn while promised.
	if bool(s.promised) and not bool(s.bookmarkDelivered):
		var slot: Dictionary = s.objectives[1]
		var r: Rect2 = Rect2(Vector2(float(slot.x) - 11.0, float(slot.y) - 12.0), Vector2(22, 24))
		var poly: PackedVector2Array = v.box_rect_poly(r)
		poly.append(poly[0])
		_dashed_poly(c, poly, Color(MINT, 0.75 if s.carryBookmark else 0.4))
		if not s.objectives[0].done:
			_ribbon(c, v.box_point(Vector2(float(s.objectives[0].x), float(s.objectives[0].y))), 1.0)

static func draw_over(c: CanvasItem, s: Dictionary, v) -> void:
	if bool(s.promised) and bool(s.carryBookmark):
		_ribbon(c, v.box_point(_soul(s)) + Vector2(7, -6), 0.9)

static func _ribbon(c: CanvasItem, at: Vector2, alpha: float) -> void:
	var poly: PackedVector2Array = PackedVector2Array([at + Vector2(-3, -7), at + Vector2(3, -7), at + Vector2(3, 6), at + Vector2(0, 3), at + Vector2(-3, 6)])
	c.draw_colored_polygon(poly, Color(MINT, alpha))
	c.draw_line(at + Vector2(-3, -7), at + Vector2(3, -7), Color(DARK, alpha), 1)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v) -> bool:
	var armed: bool = int(b.age) > int(b.arm)
	match str(b.shape):
		"page":
			var pg: Dictionary = b.page
			var top: Vector2 = v.box_point(Vector2(float(b.x), float(b.y) - float(b.h)))
			var bottom: Vector2 = v.box_point(Vector2(float(b.x), float(b.y) + float(b.h)))
			if not armed:
				# Ribbon markers on the entry wall show where the gap will be.
				if int(pg.part) == 0:
					var edge: float = -int(pg.dir) * (D.half(v.pattern).x - 4.0)
					var blink: float = 0.5 + 0.4 * sin(float(b.age) * 0.5)
					for y: float in [float(pg.gap) - float(pg.gh), float(pg.gap) + float(pg.gh)]:
						c.draw_line(v.box_point(Vector2(edge - 6.0, y)), v.box_point(Vector2(edge + 6.0, y)), Color(AMBER, blink * alpha), 2)
					v.chevron(c, v.box_point(Vector2(edge, float(pg.gap))), Vector2(float(pg.dir), 0), Color(AMBER, blink * alpha))
					_dashed(c, v.box_point(Vector2(-D.half(v.pattern).x, float(pg.gap) - float(pg.gh))), v.box_point(Vector2(D.half(v.pattern).x, float(pg.gap) - float(pg.gh))), Color(AMBER, 0.25 * alpha))
					_dashed(c, v.box_point(Vector2(-D.half(v.pattern).x, float(pg.gap) + float(pg.gh))), v.box_point(Vector2(D.half(v.pattern).x, float(pg.gap) + float(pg.gh))), Color(AMBER, 0.25 * alpha))
				return true
			# A page seen edge-on: wider through the spine, with ruled lines.
			var p: float = clampf(float(int(b.age) - int(pg.warn)) / float(pg.dur), 0.0, 1.0)
			var lean: float = 2.0 + 5.0 * sin(p * PI)
			var poly: PackedVector2Array = PackedVector2Array([top + Vector2(-lean, 0), top + Vector2(lean, 0), bottom + Vector2(lean, 0), bottom + Vector2(-lean, 0)])
			c.draw_colored_polygon(poly, Color(CREAM, 0.95 * alpha))
			var y0: float = top.y + 4.0
			while y0 < bottom.y - 2.0:
				c.draw_line(Vector2(top.x - lean + 1.0, y0), Vector2(top.x + lean - 1.0, y0), Color(LILAC, 0.7 * alpha), 1)
				y0 += 5.0
			var torn: Vector2 = bottom if int(pg.part) == 0 else top
			c.draw_line(torn + Vector2(-lean - 1.0, 0), torn + Vector2(lean + 1.0, 0), Color(AMBER, alpha), 2)
			return true
		"book":
			var hw: float = float(b.w); var hh: float = float(b.h)
			var col: Color = SPINES[int(b.get("hue", 0)) % SPINES.size()]
			var a: float = alpha * (1.0 if armed else 0.45)
			c.draw_colored_polygon(v.quad(at, hw, hh, turn), Color(col, a))
			c.draw_line(at + Vector2(-hw, -hh * 0.45).rotated(turn), at + Vector2(hw, -hh * 0.45).rotated(turn), Color(AMBER, 0.8 * a), 1)
			c.draw_line(at + Vector2(-hw, hh * 0.5).rotated(turn), at + Vector2(hw, hh * 0.5).rotated(turn), Color(CREAM, 0.5 * a), 1)
			if b.has("fall") and int(b.fall) > 0:
				c.draw_polyline(v.quad(at, hw + 1.5, hh + 1.5, turn) + PackedVector2Array([v.quad(at, hw + 1.5, hh + 1.5, turn)[0]]), Color(ROSE, a), 1)
			return true
		"drawer":
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
			var body: Rect2 = Rect2(Vector2(float(b.x) - float(b.w), float(b.y) - float(b.h)), Vector2(float(b.w), float(b.h)) * 2.0)
			var drawn: PackedVector2Array = v.box_rect_poly(body)
			c.draw_colored_polygon(drawn, Color(WOOD, alpha))
			drawn.append(drawn[0])
			c.draw_polyline(drawn, Color(AMBER, 0.8 * alpha), 1)
			if bool(dw.get("top", false)):
				var face: Vector2 = v.box_point(Vector2(float(b.x), float(b.y) + float(b.h) - 3.0))
				c.draw_line(face + Vector2(-4, 0), face + Vector2(4, 0), Color(AMBER, alpha), 2)
			else:
				var front: float = float(b.x) - float(dw.side) * float(b.w)
				c.draw_line(v.box_point(Vector2(front, float(b.y) - float(b.h))), v.box_point(Vector2(front, float(b.y) + float(b.h))), Color(Color("8a6448"), alpha), 3)
				c.draw_line(v.box_point(Vector2(front - float(dw.side) * 0.0, float(b.y) - 3.0)), v.box_point(Vector2(front, float(b.y) + 3.0)), Color(AMBER, alpha), 2)
				var x: float = front + float(dw.side) * 6.0
				while absf(x - front) < float(b.w) * 2.0 - 6.0:
					c.draw_line(v.box_point(Vector2(x, float(b.y) - float(b.h) - 2.0)), v.box_point(Vector2(x, float(b.y) - float(b.h) + 3.0)), Color(CREAM, 0.7 * alpha), 2)
					x += float(dw.side) * 9.0
			return true
		"cart":
			var body: PackedVector2Array = v.quad(at + Vector2(0, 1), 18.0, 5.0, turn)
			c.draw_colored_polygon(body, Color(Color("4a3a30"), alpha))
			body.append(body[0])
			c.draw_polyline(body, Color(AMBER, alpha), 1)
			for i: int in range(6):
				c.draw_rect(Rect2(at + Vector2(-16.0 + i * 5.5, -9.0), Vector2(4, 6)), Color(SPINES[i % SPINES.size()], alpha))
			c.draw_circle(at + Vector2(-12, 7), 2.0, Color(CREAM, alpha))
			c.draw_circle(at + Vector2(12, 7), 2.0, Color(CREAM, alpha))
			return true
		"card":
			c.draw_colored_polygon(v.quad(at, 3.5, 2.5, turn), Color(CREAM, alpha))
			c.draw_line(at + Vector2(-2.5, -0.8).rotated(turn), at + Vector2(2.5, -0.8).rotated(turn), Color(ROSE, alpha), 1)
			return true
		"branch":
			var k: Dictionary = b.stroke
			var o: Vector2 = Vector2(float(k.ox), float(k.oy))
			var d: Vector2 = Vector2(float(k.dx), float(k.dy))
			var a2: Vector2 = v.box_point(o)
			if not armed:
				var blink2: float = 0.25 + 0.2 * sin(float(b.age) * 0.5)
				_dashed(c, a2, v.box_point(o + d * float(k.len)), Color(LILAC, blink2 * alpha + 0.15))
				return true
			var head: Vector2 = v.box_point(o + d * float(k.cur))
			c.draw_line(a2, head, Color(LILAC, alpha), 5.0)
			c.draw_line(a2, head, Color(CREAM, 0.6 * alpha), 1.0)
			if int(b.get("level", 0)) == 3 and bool(k.full):
				c.draw_colored_polygon(v.quad(head, 3.0, 2.2, d.angle() + turn - float(b.rot)), Color(CREAM, alpha))
			return true
		"glyph":
			c.draw_circle(at, 4.0, Color(DARK, 0.7 * alpha))
			var font: Font = v.font
			if font != null:
				c.draw_string(font, at + Vector2(-10.0, 4.3), str(b.ch), HORIZONTAL_ALIGNMENT_CENTER, 20.0, 12, Color(PAPER, alpha * (1.0 if armed else 0.5)))
			return true
	return false

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
