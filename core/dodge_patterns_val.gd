extends RefCounted
## VAL: the graduation ceremony that was told to gather everyone its guests
## could ever become, and never to close. The final boss, in four stages. Each
## stage keeps its own promise and has its own three handmade attacks, cycling
## by turn within the stage (SETS[stage][turn % 3]); ORDER names the slots.
##   Stage 0  Familiar Promises      confirm top return, right stop, left note
##   Stage 1  Nobody Has To Be Ideal hold the shared space (after 3 rejections)
##   Stage 2  Unreserve the Chairs   reserved chairs hurt; hold the open passage
##   Stage 3  An Ordinary Voice      confirm at two ordinary stopping cues
## The promise rules and progress text match NativeFinalEncounter exactly.
## main.gd sets s.revision and s.rejected after setup, so they are read lazily.

const D = preload("res://core/dodge_box.gd")
const SETS: Array = [
	["procession", "roll_call", "reprise"],
	["perfect_record", "loved_by_all", "needs_nobody"],
	["reserved_rows", "seating_chart", "tassel"],
	["strings", "closing_time", "commencement"],
]
## Slots: the stats harness runs turn 0..2 of every stage in PHASES.
const ORDER: Array[String] = ["first", "second", "third"]
const PHASES: Array[int] = [0, 1, 2, 3]
const LENGTHS: Array[int] = [600, 480, 540, 420]
const STAGE_NAMES: Array[String] = ["Familiar Promises", "Nobody Has To Be Ideal", "Unreserve the Chairs", "An Ordinary Voice"]
const TITLES: Dictionary = {
	"procession": "Processional", "roll_call": "Roll Call", "reprise": "Reprise",
	"perfect_record": "Never Disappoints", "loved_by_all": "Loved By Everyone", "needs_nobody": "Needs Nobody",
	"reserved_rows": "Reserved Seating", "seating_chart": "Seating Chart", "tassel": "Turn the Tassel",
	"strings": "Puppet Strings", "closing_time": "Closing Time", "commencement": "Commencement",
}
## Old arena destinations (128,24), (208,96), (48,96) in box space.
const DESTINATIONS: Array[Vector2] = [Vector2(0, -36), Vector2(80, 36), Vector2(-80, 36)]
const DEST_LABELS: Array[String] = ["RETURN", "STOP", "NOTE"]
## Old shared pocket Rect2(104,38,48,54) in box space.
const POCKET: Rect2 = Rect2(-24, -22, 48, 54)
## Old open column y 84 and stopping cue (128,62) in box space.
const SEAT_Y: float = 24.0
const CUE_AT: Vector2 = Vector2(0, 2)
## Old chair fields: x < 100 and x >= 156 in arena space.
const CHAIR_EDGE: float = 28.0
const CALLS: Array[String] = ["JULES.", "IMANI.", "WALT.", "THE WHOLE CLASS.", "PIP.", "JULES, WHO NEVER FAILS.", "IMANI, LOVED BY ALL.", "EVERYONE YOU COULD BE."]
const REPRISES: Array[String] = ["REPRISE: THE STORM", "REPRISE: THE SHOW", "REPRISE: ONE ROUTE", "REPRISE: LAST CALL"]
const HINTS: Dictionary = {
	"procession": ["Graduates march in step: slip through each gap. Confirm top, right, then left marks."],
	"roll_call": ["Names are called, diplomas follow, ribbons unroll. Confirm top, right, then left marks."],
	"reprise": ["VAL replays every promise you kept. Confirm at the top, right, then left marks."],
	"perfect_record": ["Slip through the star ring's flaws; leave red ink. Hold the shared green space.",
		"Slip through the star ring's flaws; leave red ink. Each ally rejects their ideal first."],
	"loved_by_all": ["Step out of the spotlight; stay in the gap when they clap. Hold the shared space.",
		"Step out of the spotlight; stay in the gap when they clap. Reject all three ideals first."],
	"needs_nobody": ["Doors slam and the room pulls you apart. Come back. Hold the shared green space.",
		"Doors slam and the room pulls you apart. Each ally rejects their own ideal first."],
	"reserved_rows": ["Reserved rows descend: pass through the empty seat. Hold the open passage.",
		"Pass through each row's empty seat. Chairs hurt; CONNECT > REVISE opens a side."],
	"seating_chart": ["Leave marked squares before their seats fill. Hold the open passage.",
		"Leave marked squares before they fill. Chairs hurt; CONNECT > REVISE opens a side."],
	"tassel": ["Stay under the tassel's arc or cross behind it. Dodge caps. Hold the open passage.",
		"Stay under the tassel's arc; dodge caps. Chairs hurt; CONNECT > REVISE opens a side."],
	"strings": ["Strings drop where you stand and are cut at each stop. Confirm in the green cue."],
	"closing_time": ["Cross a hand at its gap or through the hub. Confirm at the centre when it stops."],
	"commencement": ["Caps fly; everyone leaves for the exits. Confirm at two stopping cues."],
}
const PIVOT: Vector2 = Vector2(0, -112)
const CORD: float = 150.0

const GOLD: Color = Color("e8b45c")
const CREAM: Color = Color("e6d6b1")
const ROSE: Color = Color("e8837b")
const LILAC: Color = Color("a68db8")
const MINT: Color = Color("b9d5bc")
const PLUM: Color = Color("6b526a")
const INK_RED: Color = Color("e0524a")
const BOARD: Color = Color("3b3550")
const WOOD: Color = Color("7a5c44")

# ---------------------------------------------------------------- setup

static func setup(s: Dictionary) -> void:
	var stage: int = clampi(int(s.phase), 0, 3)
	s.stage = stage
	var options: Array = SETS[stage]
	var id: String = str(options[int(s.turn) % options.size()])
	s.patternId = id
	s.length = LENGTHS[stage]
	s.phaseName = "%s / %s" % [STAGE_NAMES[stage], TITLES[id]]
	s.valTask = 0; s.sharedTicks = 0; s.seatsHold = 0; s.finalCues = 0
	s.chairs = []; s.openColumn = 0.0; s.cueOpen = false; s.cueNumber = 0; s.lastCue = -1
	s.botGoal = null
	s.events = []
	s.assigns = []
	s.bannerColor = GOLD
	match stage:
		0:
			for i: int in range(3):
				D.objective(s, {"kind": "confirm", "x": DESTINATIONS[i].x, "y": DESTINATIONS[i].y, "r": 18.0, "active": i == 0, "label": DEST_LABELS[i]})
		1:
			D.objective(s, {"kind": "hold", "x": POCKET.get_center().x, "y": POCKET.get_center().y, "w": POCKET.size.x * 0.5, "h": POCKET.size.y * 0.5, "need": 90, "active": false, "label": "SHARED SPACE"})
		2:
			D.objective(s, {"kind": "hold", "x": 0.0, "y": SEAT_Y, "r": 22.0, "need": 90, "active": false, "label": "PASSAGE"})
			D.objective(s, {"kind": "avoid", "x": -78.0, "y": 0.0, "w": 50.0, "h": 90.0, "active": true})
			D.objective(s, {"kind": "avoid", "x": 78.0, "y": 0.0, "w": 50.0, "h": 90.0, "active": true})
		3:
			for i: int in range(3):
				D.objective(s, {"kind": "confirm", "x": CUE_AT.x, "y": CUE_AT.y, "r": 20.0, "active": false, "label": "STOP"})
	_set_hint(s)

## Sets what main.gd sets right after create, so every stage can be previewed.
static func preview(s: Dictionary, _phase: int) -> void:
	s.rejected = ["jules", "imani", "walt"]
	s.revision = "left"

static func _set_hint(s: Dictionary) -> void:
	var ready: bool = true
	match int(s.stage):
		1: ready = s.rejected.size() == 3
		2: ready = str(s.revision) in ["left", "right"]
	var pair: Array = HINTS[s.patternId]
	s.hint = pair[0] if ready or pair.size() < 2 else pair[1]

# ---------------------------------------------------------------- promise

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	match int(s.stage):
		0: return int(s.valTask) >= 3
		1: return int(s.sharedTicks) >= 90 and s.rejected.size() == 3
		2: return int(s.seatsHold) >= 90 and str(s.revision) in ["left", "right"]
	return int(s.finalCues) >= 2

static func progress(s: Dictionary) -> String:
	match int(s.stage):
		0: return "One return / one stop %d/3" % mini(3, int(s.valTask))
		1: return "Own ideals rejected %d/3\nShared space %d/90" % [s.rejected.size(), mini(90, int(s.sharedTicks))]
		2: return "REVISE the reserved seats\nOpen passage %d/90" % mini(90, int(s.seatsHold))
	return "Ordinary stopping cues %d/2\nThen choose an ending" % mini(2, int(s.finalCues))

## Keeps the old encounter's fields in step with the objectives every tick.
static func after(s: Dictionary, t: int) -> void:
	match int(s.stage):
		0:
			var done: int = 0
			for o: Dictionary in s.objectives:
				if o.done: done += 1
			s.valTask = done
			for i: int in range(3):
				s.objectives[i].active = i == done
		1:
			var o1: Dictionary = s.objectives[0]
			o1.active = s.rejected.size() == 3
			s.sharedTicks = mini(90, int(o1.progress))
		2:
			_seat_sync(s)
			s.seatsHold = mini(90, int(s.objectives[0].progress))
		3:
			var m: int = posmod(t, 150)
			var number: int = maxi(0, t) / 150
			s.cueNumber = number
			s.cueOpen = t >= 0 and m >= 60 and m < 120
			var got: int = 0
			for i: int in range(3):
				var o3: Dictionary = s.objectives[i]
				o3.active = bool(s.cueOpen) and number == i and not o3.done
				if o3.done:
					got += 1; s.lastCue = i
			s.finalCues = got
			var upcoming: bool = t >= 0 and m >= 32 and m < 120 and number < 3 and not s.objectives[mini(2, number)].done
			s.botGoal = CUE_AT if upcoming and got < 2 else null
	_set_hint(s)

static func _seat_sync(s: Dictionary) -> void:
	var rev: String = str(s.revision)
	s.openColumn = -64.0 if rev == "left" else 64.0 if rev == "right" else 0.0
	var chairs: Array = []
	if rev != "left": chairs.append(Rect2(-200.0, -200.0, 200.0 - CHAIR_EDGE, 400.0))
	if rev != "right": chairs.append(Rect2(CHAIR_EDGE, -200.0, 200.0 - CHAIR_EDGE, 400.0))
	s.chairs = chairs
	var hold: Dictionary = s.objectives[0]
	hold.x = float(s.openColumn)
	hold.active = rev in ["left", "right"]
	s.objectives[1].active = rev != "left"
	s.objectives[2].active = rev != "right"

## The open floor between the reserved chairs: x from .x to .y (box space).
static func _open(s: Dictionary) -> Vector2:
	var rev: String = str(s.revision)
	var hx: float = D.half(s).x
	return Vector2(-hx if rev == "left" else -CHAIR_EDGE, hx if rev == "right" else CHAIR_EDGE)

# ---------------------------------------------------------------- tick

static func tick(s: Dictionary, t: int) -> void:
	if int(s.stage) == 2:
		_seat_sync(s)
		var soul: Vector2 = _soul(s)
		for r: Rect2 in s.chairs:
			if r.has_point(soul): D.hurt(s, D.soul_world(s))
	match str(s.patternId):
		"procession": _procession(s, t)
		"roll_call": _roll_call(s, t)
		"reprise": _reprise(s, t)
		"perfect_record": _perfect_record(s, t)
		"loved_by_all": _loved_by_all(s, t)
		"needs_nobody": _needs_nobody(s, t)
		"reserved_rows": _reserved_rows(s, t)
		"seating_chart": _seating_chart(s, t)
		"tassel": _tassel(s, t)
		"strings": _strings(s, t)
		"closing_time": _closing_time(s, t)
		"commencement": _commencement(s, t)
	_fire_events(s, t)

static func _soul(s: Dictionary) -> Vector2:
	return Vector2(float(s.soul.x), float(s.soul.y))

static func _pick(s: Dictionary, n: int) -> int:
	return mini(n - 1, int(D.rand(s) * float(n)))

static func _seg_dist(p: Vector2, a: Vector2, b: Vector2) -> float:
	var line: Vector2 = b - a
	var k: float = clampf((p - a).dot(line) / maxf(0.00001, line.length_squared()), 0.0, 1.0)
	return p.distance_to(a + line * k)

static func _fire_events(s: Dictionary, t: int) -> void:
	var kept: Array = []
	for e: Dictionary in s.events:
		if int(e.at) != t:
			if int(e.at) > t: kept.append(e)
			continue
		match str(e.kind):
			"flash":
				D.shot(s, {"space": "box", "x": float(e.x), "y": float(e.y), "r": 11.0, "life": 8, "shape": "burst"})
				for i: int in range(8):
					var a: float = i * TAU / 8.0 + 0.2
					D.shot(s, {"space": "box", "x": float(e.x), "y": float(e.y), "vx": cos(a) * 1.5, "vy": sin(a) * 1.5, "r": 2.2, "shape": "sparkle", "life": 120})
			"alarm":
				D.shot(s, {"space": "box", "x": CUE_AT.x, "y": CUE_AT.y, "collide": "ring", "radius": 4.0, "grow": 1.25, "thick": 2.0, "gap": D.rand(s) * TAU, "gapWidth": 0.85, "shape": "chime", "maxRadius": 150.0})
			"toss":
				var h: Vector2 = D.half(s)
				var g: float = 0.1
				var vy: float = -sqrt(2.0 * g * (h.y * 2.0 - 16.0))
				D.shot(s, {"space": "box", "x": float(e.x), "y": h.y + 6.0, "vx": D.rand_range(s, -0.25, 0.25), "vy": vy, "ay": g, "r": 5.0, "shape": "cap", "spin": 0.15, "life": 200})
	s.events = kept

# ================================================================ stage 0
# Familiar Promises: the ceremony replays the familiar. Three destinations.

# Processional: ranks of graduates march in from alternating sides, striding on
# the beat and shuffling between. Proud families' cameras flash where you stand.
# The second half quickens and some ranks march two deep.
static func _procession(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 112.0}, 24)
		s.rank = 0; s.rankGap = 2
	var h: Vector2 = D.half(s)
	var stride: bool = (int(s.clock) + int(s.musicBase)) % 30 < 18
	for b: Dictionary in s.bullets:
		if b.has("march"): b.vx = float(b.march) * (2.0 if stride else 0.45)
	if t == 300: D.banner(s, "EVERY FUTURE MARCHES", 50)
	var every: int = 60 if t < 300 else 48
	if t % every == 6 and t < 510:
		var dir: float = 1.0 if int(s.rank) % 2 == 0 else -1.0
		var double: bool = t >= 300 and int(s.rank) % 3 == 2
		s.rank = int(s.rank) + 1
		var slots: int = 7
		var gap: int = clampi(int(s.rankGap) + _pick(s, 5) - 2, 0, slots - 2)
		s.rankGap = gap
		var spacing: float = (h.y * 2.0 - 12.0) / float(slots - 1)
		for col: int in range(2 if double else 1):
			for i: int in range(slots):
				if i == gap or i == gap + 1: continue
				D.shot(s, {"space": "box", "x": -dir * (h.x + 12.0 + col * 16.0), "y": -h.y + 6.0 + i * spacing, "vx": dir * 0.45, "march": dir,
					"r": 4.5, "shape": "cap", "life": 460, "bob": i})
		D.warn(s, {"kind": "aisle", "x": -dir * (h.x - 3.0), "y": -h.y + 6.0 + (gap + 0.5) * spacing, "h": spacing * 1.2}, 50)
	if t % 80 == 60 and t < 500:
		var at: Vector2 = _soul(s) + Vector2(D.rand_range(s, -5.0, 5.0), D.rand_range(s, -5.0, 5.0))
		s.events.append({"at": t + 40, "kind": "flash", "x": at.x, "y": at.y})
		D.warn(s, {"kind": "viewfinder", "x": at.x, "y": at.y}, 40, true)

# Roll Call: names are called from two lecterns outside the box; each call lobs
# a fan of diplomas at you, which unroll into ribbons along the floor. Every
# fourth call is the whole class: caps rain down every column but two.
static func _roll_call(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 112.0}, 24)
		s.calls = 0
	var h: Vector2 = D.half(s)
	if t % 54 == 16 and t < 500:
		var idx: int = int(s.calls)
		s.calls = idx + 1
		s.caller = -1.0 if idx % 2 == 0 else 1.0
		D.banner(s, CALLS[idx % CALLS.size()], 46)
		if idx % 4 == 3: _whole_class(s, h)
		else: _lob_diplomas(s, h, float(s.caller), 3 if idx < 8 else 4)
	var landed: Array = []
	for b: Dictionary in s.bullets:
		if b.get("unroll", false) and not b.dead and float(b.y) >= h.y - 5.0 and float(b.vy) > 0.0:
			b.dead = true
			landed.append(float(b.x))
	for x: float in landed:
		for side: float in [-1.0, 1.0]:
			D.shot(s, {"space": "box", "x": x, "y": h.y - 3.0, "vx": side * 1.5, "collide": "rect", "w": 5.0, "h": 2.0, "shape": "ribbon", "life": 200})

static func _lob_diplomas(s: Dictionary, h: Vector2, side: float, count: int) -> void:
	var from: Vector2 = Vector2(side * (h.x + 10.0), -h.y + 16.0)
	var soul: Vector2 = _soul(s)
	var flight: float = 48.0
	var g: float = 0.08
	for i: int in range(count):
		var off: float = (float(i) - float(count - 1) * 0.5) * 30.0
		var target: Vector2 = Vector2(clampf(soul.x + off, -h.x + 8.0, h.x - 8.0), clampf(soul.y, -h.y + 10.0, h.y - 12.0))
		var vx: float = (target.x - from.x) / flight
		var vy: float = (target.y - from.y - 0.5 * g * flight * (flight + 1.0)) / flight
		D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": vx, "vy": vy, "ay": g, "r": 4.0, "shape": "scroll", "spin": 0.16 * side, "life": 300, "unroll": true})
		D.warn(s, {"kind": "mark", "x": target.x, "y": target.y}, int(flight))

static func _whole_class(s: Dictionary, h: Vector2) -> void:
	var cols: int = 10
	var spacing: float = (h.x * 2.0 - 16.0) / float(cols - 1)
	var soul: Vector2 = _soul(s)
	var safe: int = clampi(int((soul.x + h.x - 8.0) / spacing + D.rand_range(s, -2.0, 1.0)), 0, cols - 2)
	for k: int in range(cols):
		if k == safe or k == safe + 1: continue
		var x: float = -h.x + 8.0 + k * spacing
		D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 6.0, "horizontal": false}, 36, k == 0)
		for j: int in range(3):
			D.shot(s, {"space": "box", "x": x, "y": -h.y - 8.0 - 2.6 * 36.0 - j * 18.0, "vy": 2.6, "r": 4.5, "shape": "cap", "rot": 0.0, "life": 200})

# Reprise: VAL replays the promises the party already kept, one after another,
# each tinted gold like an old photo: Walt's storm (wind and paper), ENCORE's
# show (spotlights and footlight notes), the Cone Committee's one marked route
# (crossed-out rows fill with traffic) and Rook's last call (key rings).
static func _reprise(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 236.0, "h": 112.0}, 24)
		s.rankGap = 3; s.lastRow = 1
	var seg: int = mini(3, t / 140)
	var local: int = t - seg * 140
	var h: Vector2 = D.half(s)
	if local == 0:
		D.banner(s, REPRISES[seg], 60)
		s.wind = Vector2.ZERO
		s.rigs = [Vector2(36, -34), Vector2(220, -34)] if seg == 1 else []
		s.reprise = seg
	match seg:
		0: _reprise_storm(s, local, h)
		1: _reprise_show(s, local, h)
		2: _reprise_route(s, local, h)
		3: _reprise_keys(s, local, h)
	for b: Dictionary in s.bullets:
		if b.collide == "beam": b.av = float(b.get("sweep", 0.0)) if int(b.age) >= int(b.warn) else 0.0

static func _reprise_storm(s: Dictionary, local: int, h: Vector2) -> void:
	var flipped: bool = local >= 72
	if local == 44: D.warn(s, {"kind": "arrows", "dir": Vector2.RIGHT}, 28, true)
	if local >= 16 and local < 132:
		s.wind = Vector2.ZERO if local >= 62 and local < 80 else Vector2(0.4 if flipped else -0.4, 0)
	else:
		s.wind = Vector2.ZERO
	if local % 18 == 10 and local < 126 and not (local > 56 and local < 80):
		s.rankGap = clampi(int(s.rankGap) + _pick(s, 3) - 1, 0, 5)
		var side: float = -1.0 if flipped else 1.0
		var slots: int = 7
		var spacing: float = (h.y * 2.0 - 10.0) / float(slots - 1)
		for i: int in range(slots):
			if i == int(s.rankGap) or i == int(s.rankGap) + 1: continue
			D.shot(s, {"space": "box", "x": side * (h.x + 10.0), "y": -h.y + 5.0 + i * spacing, "vx": -side * 2.2, "collide": "rect", "w": 4.0, "h": 4.5,
				"shape": "paper", "rot": D.rand(s) * TAU, "spin": D.rand_range(s, -0.12, 0.12), "wave": {"amp": 3.0, "freq": 0.11, "phase": i * 0.8}, "life": 200})

static func _reprise_show(s: Dictionary, local: int, h: Vector2) -> void:
	if local >= 20 and local < 104 and (local - 20) % 28 == 0:
		var index: int = ((local - 20) / 28) % 2
		var rig: Vector2 = s.rigs[index]
		var aim: float = (D.soul_world(s) - rig).angle() + D.rand_range(s, -0.2, 0.2)
		var sweep: float = 0.011 * (1.0 if index == 0 else -1.0)
		D.shot(s, {"x": rig.x, "y": rig.y, "collide": "beam", "angle": aim - sweep * 28.0, "len": 300.0, "w0": 6.0, "w1": 40.0, "warn": 30, "live": 40, "av": 0.0, "sweep": sweep, "shape": "cone"})
	if local % 30 == 12 and local < 128:
		for i: int in range(2):
			D.shot(s, {"space": "box", "x": D.rand_range(s, -h.x + 10.0, h.x - 10.0), "y": h.y + 6.0, "vy": -1.4, "r": 3.5, "shape": "note", "rot": -PI / 2.0,
				"wave": {"amp": 7.0, "freq": 0.09, "phase": D.rand(s) * TAU}, "life": 180})

static func _reprise_route(s: Dictionary, local: int, h: Vector2) -> void:
	var rows: Array[float] = [-36.0, 0.0, 36.0]
	if local % 50 == 14 and local < 120:
		var safe: int = posmod(int(s.lastRow) + 1 + _pick(s, 2), 3)
		s.lastRow = safe
		for r: int in range(3):
			if r == safe:
				D.warn(s, {"kind": "route", "y": rows[r]}, 60)
				continue
			D.warn(s, {"kind": "lane", "y": D.centre(s).y + rows[r], "h": 10.0, "horizontal": true}, 34, r == 0 or safe == 0 and r == 1)
			D.warn(s, {"kind": "cancel", "y": rows[r]}, 34)
			# The cancelled call: a full row of cones pops up and stands for a moment.
			var x: float = -h.x + 6.0
			while x < h.x - 2.0:
				D.shot(s, {"space": "box", "x": x, "y": rows[r], "collide": "rect", "w": 4.0, "h": 5.0, "shape": "tcone", "arm": 34, "hold": true, "life": 34 + 26})
				x += 13.0

static func _reprise_keys(s: Dictionary, local: int, h: Vector2) -> void:
	if local == 14:
		for ci: int in range(2):
			var c: Vector2 = D.to_world(s, Vector2(-56.0 if ci == 0 else 56.0, 0.0))
			var missing: int = _pick(s, 10)
			for k: int in range(10):
				if posmod(k - missing, 10) < 3: continue
				D.shot(s, {"orbit": {"ox": c.x, "oy": c.y, "radius": 30.0, "angle": k * TAU / 10.0, "av": 0.022 * (1.0 if ci == 0 else -1.0)},
					"r": 3.5, "shape": "key", "arm": 24, "keyring": ci, "life": 124})
	if local >= 14:
		for b: Dictionary in s.bullets:
			if b.has("keyring"):
				b.orbit.radius = 30.0 + 16.0 * sin(float(local - 14) * 0.045 + float(b.keyring) * PI)
				b.rot = float(b.orbit.angle) + PI * 0.5
	if local % 30 == 26 and local > 30 and local < 128:
		var side: float = -1.0 if (local / 30) % 2 == 0 else 1.0
		var from: Vector2 = Vector2(side * (h.x + 8.0), D.rand_range(s, -h.y + 10.0, h.y - 10.0))
		var aim: Vector2 = (_soul(s) - from).normalized() * 1.7
		D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": aim.x, "vy": aim.y, "r": 3.5, "shape": "key", "rot": aim.angle(), "life": 220})

# ================================================================ stage 1
# Nobody Has To Be Ideal: one attack per imposed ideal. The shared pocket in the
# middle is where the party holds together.

# Never Disappoints (Jules): a perfect ring of gold stars breathes in and out
# around the shared space with two flaws to slip through, red ink crosses out
# wherever you stand, and later a SEE ME circle closes in on you.
static func _perfect_record(s: Dictionary, t: int) -> void:
	var c: Vector2 = D.to_world(s, POCKET.get_center())
	if t == 0:
		D.box_to(s, {"w": 208.0, "h": 116.0}, 24)
		s.ringSpin = 1.0
		for k: int in range(14):
			if k in [0, 1, 7, 8]: continue
			D.shot(s, {"orbit": {"ox": c.x, "oy": c.y, "radius": 76.0, "angle": k * TAU / 14.0, "av": 0.0}, "r": 3.5, "shape": "star", "arm": 40, "starRing": true, "life": 2000})
	if t == 200:
		D.warn(s, {"kind": "spin", "dir": -1.0}, 40, true)
		D.banner(s, "NO MISTAKES", 40)
	if t == 240: s.ringSpin = -1.0
	var radius: float = 50.0 + 26.0 * cos(t * 0.022)
	for b: Dictionary in s.bullets:
		if b.get("starRing", false):
			b.orbit.radius = radius
			b.orbit.ox = c.x; b.orbit.oy = c.y
			b.orbit.av = 0.0 if t < 40 or (t > 210 and t < 240) else 0.011 * float(s.ringSpin)
	if t % 64 == 30 and t < 420:
		var at: Vector2 = _soul(s) + Vector2(D.rand_range(s, -4.0, 4.0), D.rand_range(s, -4.0, 4.0))
		var a0: float = D.rand(s) * PI
		for a: float in [a0 + PI * 0.25, a0 - PI * 0.25]:
			D.shot(s, {"space": "box", "x": at.x, "y": at.y, "collide": "rect", "w": 70.0, "h": 1.6, "rot": a, "arm": 34, "hold": true, "life": 34 + 18, "shape": "pen"})
	if t >= 190 and t % 64 == 62 and t < 420:
		var soul: Vector2 = _soul(s)
		D.shot(s, {"space": "box", "x": soul.x, "y": soul.y, "collide": "ring", "radius": 34.0, "grow": -0.38, "thick": 1.5, "gap": D.rand(s) * TAU, "gapWidth": 1.1,
			"arm": 30, "life": 80, "shape": "inkring"})

# Loved By Everyone (Imani): the audience around the box throws hearts at you
# on every beat, a follow spot lands wherever you stand, and the applause claps
# the box shut top and bottom, leaving only a band through the middle.
static func _loved_by_all(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 112.0}, 24)
		s.clapAt = -999
	var h: Vector2 = D.half(s)
	var soul: Vector2 = _soul(s)
	if t % 30 == 12 and t < 430:
		var from: Vector2
		match _pick(s, 4):
			0: from = Vector2(-h.x - 10.0, D.rand_range(s, -h.y + 8.0, h.y - 8.0))
			1: from = Vector2(h.x + 10.0, D.rand_range(s, -h.y + 8.0, h.y - 8.0))
			2: from = Vector2(D.rand_range(s, -h.x + 10.0, h.x - 10.0), -h.y - 10.0)
			_: from = Vector2(D.rand_range(s, -h.x + 10.0, h.x - 10.0), h.y + 10.0)
		var aim: float = (soul - from).angle()
		for k: int in range(3):
			var a: float = aim + (k - 1) * 0.3
			D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": cos(a) * 1.3, "vy": sin(a) * 1.3, "home": 24, "homeTurn": 0.012, "r": 3.5, "shape": "heart", "pierce": false, "life": 320})
	if t % 96 == 50 and t < 430:
		D.shot(s, {"space": "box", "x": soul.x, "y": soul.y, "r": 15.0, "arm": 44, "hold": true, "life": 44 + 16, "shape": "spot"})
	if t >= 140 and t % 120 == 20 and t < 400:
		s.clapAt = t + 30
		D.warn(s, {"kind": "clap"}, 30, true)
		D.banner(s, "APPLAUSE", 30)
		for side: float in [-1.0, 1.0]:
			D.shot(s, {"space": "box", "x": 0.0, "y": side * (h.y + 44.0), "collide": "rect", "w": h.x + 8.0, "h": 30.0, "shape": "hands", "clap": side, "life": 30 + 46})
	var ct: int = t - int(s.clapAt)
	var k2: float = 0.0
	if ct >= 0 and ct < 10: k2 = float(ct) / 10.0
	elif ct >= 10 and ct < 30: k2 = 1.0
	elif ct >= 30 and ct < 42: k2 = 1.0 - float(ct - 30) / 12.0
	for b: Dictionary in s.bullets:
		if b.has("clap"):
			var side2: float = float(b.clap)
			var closed: float = -36.0 if side2 < 0.0 else 48.0
			b.y = lerpf(side2 * (h.y + 44.0), closed, k2)

# Needs Nobody (Walt): the room drifts you away from the middle, doors slam
# into the box in a zigzag that sweeps back and forth, and halfway the box
# closes in to one lonely cell with embers rising from Walt's lantern.
static func _needs_nobody(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 116.0}, 24)
		s.door = 0; s.doorStep = 1; s.drift = 1.0; s.doorGap = 0.0
	var h: Vector2 = D.half(s)
	var soul: Vector2 = _soul(s)
	if t >= 30 and t < 440:
		if absf(soul.x) > 1.0: s.drift = signf(soul.x)
		s.wind = Vector2(0.3 * float(s.drift), 0)
	else:
		s.wind = Vector2.ZERO
	if t == 180:
		D.warn(s, {"kind": "curtain"}, 30, true)
		D.banner(s, "NEEDS NOBODY", 40)
		D.box_to(s, {"w": 132.0}, 40, 10)
	if t == 340:
		D.banner(s, "YOU CAN CHOOSE COMPANY", 40)
		D.box_to(s, {"w": 240.0}, 40)
	if t % 20 == 10 and t < 420:
		var col: int = int(s.door)
		var reach0: float = (h.x if t < 180 or t > 360 else 66.0) - 7.0
		var x: float = lerpf(-reach0, reach0, float(col) / 7.0)
		var top: bool = (t / 20) % 2 == 0
		var next: int = col + int(s.doorStep)
		if next >= 8 or next < 0:
			s.doorStep = -int(s.doorStep)
			next = col + int(s.doorStep)
		s.door = next
		s.doorGap = clampf(float(s.doorGap) + D.rand_range(s, -16.0, 16.0), -28.0, 28.0)
		var inner: float = float(s.doorGap) + (-6.0 if top else 6.0)
		D.shot(s, {"space": "box", "x": x, "y": -300.0, "collide": "rect", "w": 5.0, "h": 4.0, "shape": "door", "doorTop": top, "inner": inner, "arm": 30, "hold": true, "life": 30 + 64})
		D.warn(s, {"kind": "doorway", "x": x, "top": top, "inner": inner}, 30)
	var splinters: Array = []
	for b: Dictionary in s.bullets:
		if not b.has("doorTop"): continue
		var age: int = int(b.age) - 30
		if age == 8: splinters.append(Vector2(float(b.x), float(b.inner)))
		var k: float = 0.0
		if age >= 0 and age < 8: k = float(age) / 8.0
		elif age >= 8 and age < 52: k = 1.0
		elif age >= 52: k = maxf(0.0, 1.0 - float(age - 52) / 10.0)
		var top2: bool = b.doorTop
		var inner: float = float(b.inner)
		var outer: float = -h.y - 4.0 if top2 else h.y + 4.0
		var half_len: float = absf(outer - inner) * 0.5
		var mid: float = (inner + outer) * 0.5
		b.h = half_len
		b.y = mid + (outer - inner) * (1.0 - k)
	for at: Vector2 in splinters:
		for side: float in [-1.0, 1.0]:
			D.shot(s, {"space": "box", "x": at.x, "y": at.y, "vx": side * 1.5, "vy": D.rand_range(s, -0.3, 0.3), "r": 2.2, "shape": "grit", "spin": 0.3, "life": 120})
	# Hugging a wall alone is no shelter: a lantern there throws sparks at you.
	if t % 50 == 25 and t < 430 and absf(soul.x) > h.x * 0.45:
		var side: float = signf(soul.x)
		var from: Vector2 = Vector2(side * (h.x + 4.0), clampf(soul.y + D.rand_range(s, -10.0, 10.0), -h.y + 8.0, h.y - 8.0))
		var aim: float = (soul - from).angle()
		for k: int in range(3):
			var a: float = aim + (k - 1) * 0.3
			D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": cos(a) * 1.5, "vy": sin(a) * 1.5, "r": 2.5, "shape": "ember", "arm": 22, "hold": true, "life": 22 + 140})
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": from.y, "dir": Vector2(-side, 0)}, 22)
	if t >= 200 and t < 350 and t % 9 == 0:
		D.shot(s, {"space": "box", "x": D.rand_range(s, -h.x + 6.0, h.x - 6.0), "y": h.y + 6.0, "vy": -1.0, "r": 2.5, "shape": "ember",
			"wave": {"amp": 7.0, "freq": 0.07, "phase": D.rand(s) * TAU}, "life": 200})

# ================================================================ stage 2
# Unreserve the Chairs: the reserved fields hurt. Without REVISE only the aisle
# between them is free; with it, one whole side opens up.

# Reserved Seating: rows of folding chairs descend over the open floor, each with
# one empty seat to pass through, while RESERVED cards are flung out of the
# reserved fields at you. Later rows also rise from the floor.
static func _reserved_rows(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"h": 116.0}, 20)
		s.rowGap = 0.0; s.rowN = 0; s.cardN = 0
	var h: Vector2 = D.half(s)
	var open: Vector2 = _open(s)
	var soul: Vector2 = _soul(s)
	if t == 270: D.banner(s, "EVERY SEAT IS SPOKEN FOR", 50)
	var every: int = 46 if t < 270 else 40
	if t % every == 8 and t < 470:
		var up: bool = t >= 270 and int(s.rowN) % 2 == 1
		s.rowN = int(s.rowN) + 1
		var gx: float = clampf(float(s.rowGap) + D.rand_range(s, -44.0, 44.0), open.x + 14.0, open.y - 14.0)
		s.rowGap = gx
		var x: float = open.x + 4.0
		while x <= open.y - 2.0:
			if absf(x - gx) >= 16.0:
				D.shot(s, {"space": "box", "x": x, "y": (h.y + 10.0) if up else (-h.y - 10.0), "vy": -1.05 if up else 1.05, "collide": "rect", "w": 5.0, "h": 4.5,
					"shape": "chair", "flipY": up, "life": 260})
			x += 14.0
		D.warn(s, {"kind": "seatgap", "x": gx, "up": up}, 44)
	if t % 36 == 30 and t < 450:
		var sides: Array[float] = []
		if str(s.revision) != "left": sides.append(-1.0)
		if str(s.revision) != "right": sides.append(1.0)
		var side: float = sides[int(s.cardN) % sides.size()]
		s.cardN = int(s.cardN) + 1
		var y: float = clampf(soul.y + D.rand_range(s, -8.0, 8.0), -h.y + 6.0, h.y - 6.0)
		D.shot(s, {"space": "box", "x": side * (CHAIR_EDGE + 8.0), "y": y, "vx": -side * 1.9, "collide": "rect", "w": 4.0, "h": 3.0, "shape": "card",
			"arm": 24, "hold": true, "life": 24 + 170})
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (CHAIR_EDGE - 3.0), "y": y, "dir": Vector2(-side, 0)}, 24)

# Seating Chart: VAL assigns seats on a grid over the open floor. Marked squares
# fill with chairs a moment later (checkerboards, rows, columns, a ring around
# you). Possible graduates drift out of the reserved fields between charts.
static func _seating_chart(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"h": 112.0}, 20)
		s.chartN = 0; s.ghostN = 0
	var h: Vector2 = D.half(s)
	var soul: Vector2 = _soul(s)
	var every: int = 58 if t < 250 else 50
	if t % every == 14 and t < 440:
		var grid: Dictionary = _grid(s)
		var cols: int = grid.cols
		var sc: int = clampi(int((soul.x - float(grid.left)) / float(grid.cw)), 0, cols - 1)
		var sr: int = clampi(int((soul.y + h.y) / float(grid.ch)), 0, 3)
		var kind: int = int(s.chartN) % 6
		s.chartN = int(s.chartN) + 1
		var free_row: int = clampi(sr + _pick(s, 3) - 1, 0, 3)
		var free_col: int = clampi(sc + _pick(s, 3) - 1, 0, cols - 1)
		var neighbours: Array = []
		for di: int in [-1, 0, 1]:
			for dj: int in [-1, 0, 1]:
				if (di != 0 or dj != 0) and sc + di >= 0 and sc + di < cols and sr + dj >= 0 and sr + dj < 4: neighbours.append(Vector2i(sc + di, sr + dj))
		var escape: Vector2i = neighbours[_pick(s, neighbours.size())] if neighbours.size() > 0 else Vector2i(-1, -1)
		var keep: Vector2i = Vector2i(clampi(sc + _pick(s, 3) - 1, 0, cols - 1), clampi(sr + _pick(s, 3) - 1, 0, 3))
		var lit: Array = []
		for i: int in range(cols):
			for j: int in range(4):
				var on: bool = false
				match kind:
					0: on = (i + j) % 2 == 0
					1: on = (i + j) % 2 == 1
					2: on = j != free_row
					3: on = i != free_col
					4: on = absi(i - sc) <= 1 and absi(j - sr) <= 1 and Vector2i(i, j) != escape
					_: on = D.rand(s) < 0.5 and Vector2i(i, j) != keep
				if on: lit.append(Rect2(float(grid.left) + i * float(grid.cw), -h.y + j * float(grid.ch), float(grid.cw), float(grid.ch)))
		s.assigns.append({"cells": lit, "live": t + 42, "end": t + 64})
		D.banner(s, ["SEATING CHART", "SEATING CHART", "BY ROW", "BY COLUMN", "AROUND YOU", "AS IT FALLS"][kind], 30)
		s.telegraphs.append({"ticksRemaining": 20})
	var kept: Array = []
	for a: Dictionary in s.assigns:
		if t >= int(a.live) and t < int(a.end):
			for r: Rect2 in a.cells:
				if r.has_point(soul): D.hurt(s, D.soul_world(s))
		if t < int(a.end) + 12: kept.append(a)
	s.assigns = kept
	if t % 44 == 24 and t < 440:
		var sides: Array[float] = []
		if str(s.revision) != "left": sides.append(-1.0)
		if str(s.revision) != "right": sides.append(1.0)
		var side: float = sides[int(s.ghostN) % sides.size()]
		s.ghostN = int(s.ghostN) + 1
		D.shot(s, {"space": "box", "x": side * (CHAIR_EDGE + 14.0), "y": D.rand_range(s, -h.y + 10.0, h.y - 10.0), "vx": -side * 0.85,
			"wave": {"amp": 9.0, "freq": 0.06, "phase": D.rand(s) * TAU}, "r": 4.5, "shape": "ghost", "arm": 22, "life": 260})

static func _grid(s: Dictionary) -> Dictionary:
	var h: Vector2 = D.half(s)
	var rev: String = str(s.revision)
	var left: float = -h.x if rev == "left" else -CHAIR_EDGE
	var right: float = h.x if rev == "right" else CHAIR_EDGE
	var cols: int = maxi(2, int((right - left) / 28.0))
	return {"left": left, "cols": cols, "cw": (right - left) / float(cols), "ch": h.y * 0.5}

# Turn the Tassel: a giant tassel swings from above like a pendulum; you stay
# under its arc or cross when it is away. Caps are tossed in and bounce along
# the floor, and threads fly off the tassel at the end of every swing.
static func _tassel(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"h": 120.0}, 20)
		s.swingPhase = 0.0; s.swingAmp = 0.0; s.swingSign = 0.0
	var h: Vector2 = D.half(s)
	var open: Vector2 = _open(s)
	if t == 250: D.banner(s, "MOVE THE TASSEL", 50)
	s.swingPhase = float(s.swingPhase) + (0.042 if t < 250 else 0.047)
	# Autopilot: once the passage is held (or there is none), wait under the arc.
	var holding: bool = s.objectives[0].active and not s.objectives[0].done
	s.botGoal = null if holding else Vector2((open.x + open.y) * 0.5, h.y - 12.0)
	s.swingAmp = minf(0.8, float(s.swingAmp) + 0.01)
	var theta: float = float(s.swingAmp) * sin(float(s.swingPhase))
	s.swingAngle = theta
	var narrow: bool = _open(s).y - _open(s).x < 80.0
	var cord: float = (118.0 if narrow else 126.0) + clampf(float(t - 250) / 60.0, 0.0, 1.0) * (14.0 if narrow else 20.0)
	s.cordLen = cord
	var tip: Vector2 = PIVOT + Vector2(sin(theta), cos(theta)) * cord
	if t == 0:
		D.shot(s, {"space": "box", "collide": "rect", "w": cord * 0.5, "h": 2.0, "shape": "cord", "arm": 20, "life": 2000, "cord": true})
		D.shot(s, {"space": "box", "r": 7.0, "shape": "bob", "arm": 20, "life": 2000, "cord": true})
	for b: Dictionary in s.bullets:
		if not b.has("cord"): continue
		if b.shape == "cord":
			var mid: Vector2 = (PIVOT + tip) * 0.5
			b.x = mid.x; b.y = mid.y; b.rot = (tip - PIVOT).angle(); b.w = cord * 0.5
		else:
			b.x = tip.x; b.y = tip.y
	var sign_now: float = signf(cos(float(s.swingPhase)))
	if t > 60 and t < 480 and float(s.swingSign) != 0.0 and sign_now != float(s.swingSign):
		var outward: float = signf(theta)
		for k: int in range(5):
			var a: float = PI * 0.5 - outward * 0.9 + (k - 2) * 0.28
			D.shot(s, {"space": "box", "x": tip.x, "y": tip.y, "vx": cos(a) * 1.3, "vy": sin(a) * 1.3 - 0.6, "ay": 0.04, "r": 2.0, "shape": "thread", "life": 160})
	s.swingSign = sign_now
	if t % (56 if open.y - open.x < 80.0 else 44) == 30 and t < 470:
		var x: float = D.rand_range(s, open.x + 8.0, open.y - 8.0)
		var wide: bool = open.y - open.x > 80.0
		var fall: float = 0.6 * 30.0 + 0.11 * 30.0 * 31.0 * 0.5
		D.shot(s, {"space": "box", "x": x, "y": -h.y - 6.0 - fall, "vx": D.rand_range(s, -0.6, 0.6) if wide else D.rand_range(s, -0.2, 0.2), "vy": 0.6, "ay": 0.11, "bounce": 0.6,
			"r": 5.0, "shape": "cap", "spin": 0.08, "life": 260})
		D.warn(s, {"kind": "edge", "space": "box", "x": x, "y": -h.y + 4.0, "dir": Vector2.DOWN}, 30)

# ================================================================ stage 3
# An Ordinary Voice: VAL is small now. Every 150 ticks the fight offers an
# ordinary stopping cue in the centre (open 60..120); the attacks make room.

# Puppet Strings: strings drop to where you stand from above and below, then
# sway. When the cue opens they are cut and fall as beads. The frame squeezes
# in between cues and loosens at each one.
static func _strings(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 220.0, "h": 112.0}, 24)
		s.stringN = 0
	var h: Vector2 = D.half(s)
	var soul: Vector2 = _soul(s)
	var m: int = posmod(t, 150)
	var quiet: bool = m >= 46 and m < 120
	if m == 124 and t < 300: D.box_to(s, {"w": 156.0}, 70)
	if m == 36 and t > 100: D.box_to(s, {"w": 220.0}, 22)
	if m == 60:
		D.banner(s, "SNIP", 40)
		var cut: Array = []
		for b: Dictionary in s.bullets:
			if b.has("baseX"):
				b.dead = true
				cut.append(b)
		for b: Dictionary in cut:
			for k: int in range(4):
				var y: float = float(b.y) - float(b.h) + float(b.h) * 2.0 * (k + 0.5) / 4.0
				D.shot(s, {"space": "box", "x": float(b.x), "y": y, "vy": 0.3, "ay": 0.05, "r": 2.5, "shape": "bead", "life": 160})
	if not quiet and t % (32 if t < 150 else 26) == 4 and t < 370:
		var top: bool = int(s.stringN) % 2 == 0
		s.stringN = int(s.stringN) + 1
		var x: float = clampf(soul.x + D.rand_range(s, -5.0, 5.0), -h.x + 6.0, h.x - 6.0)
		_string(s, h, x, soul.y, top)
		# From the second verse the strings come as a Z: a partner from the other
		# edge closes one side, so you leave by the open one.
		if t >= 100:
			var side: float = 1.0 if D.rand(s) < 0.5 else -1.0
			if absf(x + side * 24.0) > h.x - 8.0: side = -side
			_string(s, h, x + side * 24.0, soul.y, not top)
	for b: Dictionary in s.bullets:
		if b.has("baseX") and int(b.age) > int(b.arm):
			b.x = float(b.baseX) + 3.0 * sin(float(int(b.age) - int(b.arm)) * 0.09)
	if not quiet and t % 50 == 30 and t < 360:
		var y2: float = clampf(soul.y + D.rand_range(s, -14.0, 14.0), -h.y + 8.0, h.y - 8.0)
		for k: int in range(3):
			D.shot(s, {"space": "box", "x": h.x + 10.0 + k * 9.0, "y": y2, "vx": -1.3, "r": 2.5, "shape": "word", "life": 260})

# Closing Time: a clock face around the stopping cue. Its hands are live; each
# has a gap to cross through, and the hub always lets you pass under them. The
# alarm rings out from the hub until the clock stops for the cue, and the hours
# fall inward toward the centre.
static func _string(s: Dictionary, h: Vector2, x: float, soul_y: float, top: bool) -> void:
	var edge: float = -h.y - 4.0 if top else h.y + 4.0
	var end: float = clampf(soul_y + (26.0 if top else -26.0), -h.y + 12.0, h.y - 12.0)
	if top: end = maxf(end, soul_y + 10.0)
	else: end = minf(end, soul_y - 10.0)
	D.shot(s, {"space": "box", "x": x, "y": (edge + end) * 0.5, "collide": "rect", "w": 1.5, "h": absf(end - edge) * 0.5, "shape": "string", "arm": 30, "hold": true,
		"life": 30 + 50, "baseX": x, "top": top})

static func _closing_time(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 184.0, "h": 120.0}, 24)
		s.hourA = -PI * 0.5 + 0.9; s.minA = -PI * 0.5 - 1.7
	var m: int = posmod(t, 150)
	var window: bool = m >= 60 and m < 120
	var slow: float = 0.35 if window else 1.0
	if t == 0:
		for i: int in range(4):
			D.shot(s, {"space": "box", "collide": "rect", "w": 4.0, "h": 2.5 if i < 2 else 2.0, "shape": "hand", "hand": i, "arm": 40, "life": 2000})
	if t >= 40:
		s.hourA = float(s.hourA) + 0.009 * slow
		s.minA = float(s.minA) + 0.026 * slow
	var segs: Array = _hand_segments(s)
	for b: Dictionary in s.bullets:
		if not b.has("hand"): continue
		var seg: Array = segs[int(b.hand)]
		var a: Vector2 = seg[0]
		var e: Vector2 = seg[1]
		var mid: Vector2 = (a + e) * 0.5
		b.x = mid.x; b.y = mid.y; b.rot = (e - a).angle(); b.w = a.distance_to(e) * 0.5
	if m == 60: D.banner(s, "IT CAN STOP HERE", 40)
	# The alarm rings three times a cycle and is silent while the cue is open.
	if m in [2, 22, 124] and t < 370:
		s.events.append({"at": t + 20, "kind": "alarm"})
		D.warn(s, {"kind": "alarm"}, 20, true)
	if t % 70 == 50 and t < 350:
		var start: int = _pick(s, 12)
		for k: int in range(4):
			var a: float = (start + k * 3) * TAU / 12.0 + D.rand_range(s, -0.1, 0.1)
			var dir: Vector2 = Vector2.from_angle(a)
			D.shot(s, {"space": "box", "x": CUE_AT.x + dir.x * 92.0, "y": CUE_AT.y + dir.y * 92.0, "vx": -dir.x * 0.6, "vy": -dir.y * 0.6, "r": 3.5, "shape": "numeral",
				"rot": a + PI * 0.5, "arm": 20, "life": 100})

static func _hand_segments(s: Dictionary) -> Array:
	var hd: Vector2 = Vector2.from_angle(float(s.get("hourA", 0.0)))
	var md: Vector2 = Vector2.from_angle(float(s.get("minA", 0.0)))
	return [[CUE_AT + hd * 22.0, CUE_AT + hd * 30.0], [CUE_AT + hd * 54.0, CUE_AT + hd * 130.0],
		[CUE_AT + md * 22.0, CUE_AT + md * 58.0], [CUE_AT + md * 80.0, CUE_AT + md * 150.0]]

# Commencement: caps are tossed up from the floor on every beat (one at your
# feet) and fall back, while everyone walks out of the centre toward the exits.
# The tosses leave the stopping cue clear while it is open.
static func _commencement(s: Dictionary, t: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 232.0, "h": 112.0}, 24)
		s.walkN = 0
	var h: Vector2 = D.half(s)
	var soul: Vector2 = _soul(s)
	var m: int = posmod(t, 150)
	var window: bool = m >= 40 and m < 120
	if t == 320:
		s.bannerColor = CREAM
		D.banner(s, "THEN CHOOSE AN ENDING", 60)
	if t % 30 == 20 and t < 360:
		var n: int = 2 if t < 200 else 3
		for k: int in range(n):
			var x: float = D.rand_range(s, -h.x + 12.0, h.x - 12.0)
			if k == 0 and not window: x = soul.x + D.rand_range(s, -6.0, 6.0)
			if window and absf(x - CUE_AT.x) < 28.0: x = (1.0 if x >= CUE_AT.x else -1.0) * D.rand_range(s, 30.0, h.x - 12.0)
			x = clampf(x, -h.x + 10.0, h.x - 10.0)
			s.events.append({"at": t + 30, "kind": "toss", "x": x})
			D.warn(s, {"kind": "toss", "x": x}, 30, k == 0)
	if t % 22 == 6 and t < 370:
		var side: float = 1.0 if int(s.walkN) % 2 == 0 else -1.0
		s.walkN = int(s.walkN) + 1
		var a: float = (0.0 if side > 0.0 else PI) + D.rand_range(s, -0.75, 0.75)
		var dir: Vector2 = Vector2.from_angle(a)
		D.shot(s, {"space": "box", "x": CUE_AT.x + dir.x * 30.0, "y": CUE_AT.y + dir.y * 30.0, "vx": dir.x * 0.85, "vy": dir.y * 0.85, "r": 4.5, "shape": "walker",
			"arm": 18, "life": 220, "flipX": side < 0.0})

# ================================================================ drawing

static func _off(v: Node2D) -> Vector2:
	var o: Variant = v.get("offset")
	return o if o is Vector2 else Vector2(192, 166)

static func _bp(s: Dictionary, v: Node2D, local: Vector2) -> Vector2:
	return _off(v) + D.to_world(s, local)

static func _text(c: CanvasItem, v: Node2D, at: Vector2, words: String, color: Color, size: int = 12, width: float = 120.0) -> void:
	var font: Variant = v.get("font")
	if font is Font: c.draw_string(font, at + Vector2(-width * 0.5, 0), words, HORIZONTAL_ALIGNMENT_CENTER, width, size, color)

static func _chev(c: CanvasItem, at: Vector2, dir: Vector2, color: Color) -> void:
	var side: Vector2 = Vector2(-dir.y, dir.x)
	c.draw_polyline(PackedVector2Array([at - dir * 3.0 + side * 4.0, at + dir * 2.0, at - dir * 3.0 - side * 4.0]), color, 1)

static func _dashed(c: CanvasItem, a: Vector2, b: Vector2, color: Color, dash: float = 4.0) -> void:
	var length: float = a.distance_to(b)
	var dir: Vector2 = (b - a) / maxf(0.001, length)
	var d: float = 0.0
	while d < length:
		c.draw_line(a + dir * d, a + dir * minf(length, d + dash), color, 1)
		d += dash * 2.0

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var stage: int = int(s.stage)
	var h: Vector2 = D.half(s)
	var clock: int = int(s.clock)
	var t: int = clock - int(s.leadIn)
	# The hall: a faint carpet aisle and rows of seat backs.
	for i: int in range(-4, 5):
		var y: float = i * 16.0
		c.draw_line(_bp(s, v, Vector2(-h.x - 40.0, y)), _bp(s, v, Vector2(h.x + 40.0, y)), Color(GOLD, 0.035), 1)
	var aisle: PackedVector2Array = PackedVector2Array([_bp(s, v, Vector2(-12, -h.y - 10)), _bp(s, v, Vector2(12, -h.y - 10)), _bp(s, v, Vector2(12, h.y + 10)), _bp(s, v, Vector2(-12, h.y + 10))])
	c.draw_colored_polygon(aisle, Color(0.45, 0.12, 0.18, 0.10))
	match stage:
		0:
			for o: Dictionary in s.objectives:
				if o.active and not o.done and bool(s.promised):
					c.draw_arc(_bp(s, v, Vector2(float(o.x), float(o.y))), 18.0, 0, TAU, 28, Color(MINT, 0.3), 1)
		1:
			var o1: Dictionary = s.objectives[0]
			if not o1.active:
				var r: Rect2 = POCKET
				var corners: Array[Vector2] = [r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]
				for i: int in range(4):
					_dashed(c, _bp(s, v, corners[i]), _bp(s, v, corners[(i + 1) % 4]), Color(LILAC, 0.45))
		2:
			_draw_chairs(c, s, v)
			var o2: Dictionary = s.objectives[0]
			if o2.active and not o2.done and bool(s.promised):
				c.draw_arc(_bp(s, v, Vector2(float(o2.x), float(o2.y))), 22.0, 0, TAU, 28, Color(MINT, 0.35), 1)
		3:
			if bool(s.cueOpen):
				c.draw_arc(_bp(s, v, CUE_AT), 20.0, 0, TAU, 28, Color(MINT, 0.4), 1)
	match str(s.patternId):
		"needs_nobody":
			var wind: float = Vector2(s.wind).x
			if absf(wind) > 0.01:
				for i: int in range(6):
					var y: float = -h.y + 12.0 + i * (h.y * 2.0 - 24.0) / 5.0
					var x: float = signf(wind) * fposmod(float(clock) * 0.6 + i * 13.0, h.x)
					_chev(c, _bp(s, v, Vector2(x, y)), Vector2(signf(wind), 0), Color(LILAC, 0.25))
		"seating_chart": _draw_chart(c, s, v, t)
		"closing_time": _draw_clock(c, s, v, t)
	for w: Dictionary in s.warnings:
		_draw_warning(c, s, v, w)

static func _draw_warning(c: CanvasItem, s: Dictionary, v: Node2D, w: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	var p: float = float(w.age) / maxf(1.0, float(w.life))
	var blink: float = 0.5 + 0.5 * sin(float(w.age) * 0.5)
	match str(w.kind):
		"aisle":
			var at: Vector2 = _bp(s, v, Vector2(float(w.x), float(w.y)))
			var hh: float = float(w.h) * 0.5
			c.draw_line(at + Vector2(0, -hh), at + Vector2(0, hh), Color(GOLD, 0.8 * (1.0 - p) + 0.2), 2)
			c.draw_line(at + Vector2(-3, -hh), at + Vector2(3, -hh), GOLD, 1)
			c.draw_line(at + Vector2(-3, hh), at + Vector2(3, hh), GOLD, 1)
		"viewfinder":
			var at2: Vector2 = _bp(s, v, Vector2(float(w.x), float(w.y)))
			var size: float = lerpf(26.0, 12.0, p)
			var col: Color = Color(CREAM, 0.4 + 0.5 * blink)
			for sx: float in [-1.0, 1.0]:
				for sy: float in [-1.0, 1.0]:
					var corner: Vector2 = at2 + Vector2(sx, sy) * size
					c.draw_line(corner, corner - Vector2(sx * 5.0, 0), col, 1)
					c.draw_line(corner, corner - Vector2(0, sy * 5.0), col, 1)
			c.draw_circle(at2, 1.5, Color(ROSE, blink))
		"mark":
			var at3: Vector2 = _bp(s, v, Vector2(float(w.x), float(w.y)))
			var col3: Color = Color(ROSE, 0.3 + 0.4 * p)
			c.draw_line(at3 + Vector2(-4, -4), at3 + Vector2(4, 4), col3, 1)
			c.draw_line(at3 + Vector2(-4, 4), at3 + Vector2(4, -4), col3, 1)
		"route":
			var a: Vector2 = _bp(s, v, Vector2(-h.x, float(w.y) - 9.0))
			var r: Rect2 = Rect2(a, Vector2(h.x * 2.0, 18.0))
			c.draw_rect(r, Color(GOLD, 0.08))
			c.draw_rect(r, Color(GOLD, 0.35), false, 1)
			for i: int in range(5):
				_chev(c, _bp(s, v, Vector2(-h.x + 20.0 + i * h.x * 0.45, float(w.y))), Vector2.RIGHT, Color(GOLD, 0.5))
		"cancel":
			var l: Vector2 = _bp(s, v, Vector2(-h.x, float(w.y)))
			var r2: Vector2 = _bp(s, v, Vector2(h.x, float(w.y)))
			for i: int in range(6):
				var x: Vector2 = l.lerp(r2, (i + 0.5) / 6.0)
				c.draw_line(x + Vector2(-4, -4), x + Vector2(4, 4), Color(ROSE, 0.45), 1)
				c.draw_line(x + Vector2(-4, 4), x + Vector2(4, -4), Color(ROSE, 0.45), 1)
		"doorway":
			var top: bool = w.top
			var y0: float = -h.y if top else float(w.inner)
			var y1: float = float(w.inner) if top else h.y
			var poly: PackedVector2Array = PackedVector2Array([_bp(s, v, Vector2(float(w.x) - 5.0, y0)), _bp(s, v, Vector2(float(w.x) + 5.0, y0)), _bp(s, v, Vector2(float(w.x) + 5.0, y1)), _bp(s, v, Vector2(float(w.x) - 5.0, y1))])
			c.draw_colored_polygon(poly, Color(ROSE, 0.10 + 0.15 * blink))
			c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(ROSE, 0.4), 1)
		"seatgap":
			var y: float = -h.y + 6.0 if not w.up else h.y - 6.0
			var at4: Vector2 = _bp(s, v, Vector2(float(w.x), y))
			c.draw_rect(Rect2(at4 - Vector2(8, 4), Vector2(16, 8)), Color(GOLD, 0.25 + 0.4 * blink), false, 1)
			_chev(c, at4 + Vector2(0, 8 if not w.up else -8), Vector2.DOWN if not w.up else Vector2.UP, Color(GOLD, 0.6))
		"clap":
			var col5: Color = Color(ROSE, 0.3 + 0.6 * p)
			for x2: float in [-0.6, 0.0, 0.6]:
				_chev(c, _bp(s, v, Vector2(h.x * x2, -h.y + 5.0)), Vector2.DOWN, col5)
				_chev(c, _bp(s, v, Vector2(h.x * x2, h.y - 5.0)), Vector2.UP, col5)
		"alarm":
			var hub: Vector2 = _bp(s, v, CUE_AT)
			c.draw_arc(hub, 20.0 - 14.0 * p, 0, TAU, 20, Color(ROSE, 0.4 + 0.5 * blink), 1)
		"toss":
			var at5: Vector2 = _bp(s, v, Vector2(float(w.x), h.y - 2.0))
			c.draw_arc(at5, 4.0 + p * 4.0, PI, TAU, 10, Color(GOLD, 0.4 + 0.5 * blink), 1)
			c.draw_line(at5 + Vector2(-7, 0), at5 + Vector2(7, 0), Color(GOLD, 0.6), 1)

static func _draw_chairs(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var rev: String = str(s.revision)
	for side: float in [-1.0, 1.0]:
		var reserved: bool = (side < 0.0 and rev != "left") or (side > 0.0 and rev != "right")
		var inner: float = side * CHAIR_EDGE
		var outer: float = side * (h.x + 2.0)
		var poly: PackedVector2Array = PackedVector2Array([_bp(s, v, Vector2(inner, -h.y)), _bp(s, v, Vector2(outer, -h.y)), _bp(s, v, Vector2(outer, h.y)), _bp(s, v, Vector2(inner, h.y))])
		if reserved:
			c.draw_colored_polygon(poly, Color(0.35, 0.13, 0.2, 0.35))
			c.draw_line(_bp(s, v, Vector2(inner, -h.y)), _bp(s, v, Vector2(inner, h.y)), Color(ROSE, 0.7), 1)
		var y: float = -h.y + 10.0
		var row: int = 0
		while y < h.y - 4.0:
			var x: float = inner + side * 10.0
			while absf(x) < h.x - 4.0:
				var at: Vector2 = _bp(s, v, Vector2(x, y + (row % 2) * 2.0))
				if reserved:
					_chair_icon(c, at, Color(LILAC, 0.75), false)
					c.draw_rect(Rect2(at + Vector2(-3, -6), Vector2(6, 3)), Color(CREAM, 0.7))
				else:
					c.draw_line(at + Vector2(-3, 3), at + Vector2(2, -5), Color(LILAC, 0.18), 1)
				x += side * 18.0
			y += 16.0
			row += 1
		if reserved:
			var plate: Vector2 = _bp(s, v, Vector2((inner + outer) * 0.5, 0.0))
			c.draw_rect(Rect2(plate - Vector2(32, 8), Vector2(64, 12)), Color("1c1424"))
			c.draw_rect(Rect2(plate - Vector2(32, 8), Vector2(64, 12)), Color(ROSE, 0.5), false, 1)
			_text(c, v, plate + Vector2(0, 2), "RESERVED", Color(ROSE, 0.85), 12, 100.0)
		else:
			_text(c, v, _bp(s, v, Vector2((inner + outer) * 0.5, -h.y + 14.0)), "OPEN", Color(MINT, 0.35), 12, 100.0)

static func _chair_icon(c: CanvasItem, at: Vector2, col: Color, flip: bool) -> void:
	var fy: float = -1.0 if flip else 1.0
	c.draw_line(at + Vector2(-4, 0), at + Vector2(4, 0), col, 2)
	c.draw_line(at + Vector2(-4, 0), at + Vector2(-4, -6 * fy), col, 1)
	c.draw_line(at + Vector2(-4, -6 * fy), at + Vector2(1, -6 * fy), col, 1)
	c.draw_line(at + Vector2(-3, 0), at + Vector2(-5, 5 * fy), col, 1)
	c.draw_line(at + Vector2(3, 0), at + Vector2(5, 5 * fy), col, 1)

static func _draw_chart(c: CanvasItem, s: Dictionary, v: Node2D, t: int) -> void:
	var grid: Dictionary = _grid(s)
	var h: Vector2 = D.half(s)
	for i: int in range(int(grid.cols) + 1):
		var x: float = float(grid.left) + i * float(grid.cw)
		c.draw_line(_bp(s, v, Vector2(x, -h.y)), _bp(s, v, Vector2(x, h.y)), Color(LILAC, 0.12), 1)
	for j: int in range(5):
		var y: float = -h.y + j * float(grid.ch)
		c.draw_line(_bp(s, v, Vector2(float(grid.left), y)), _bp(s, v, Vector2(float(grid.left) + float(grid.cols) * float(grid.cw), y)), Color(LILAC, 0.12), 1)
	for a: Dictionary in s.assigns:
		var live: bool = t >= int(a.live) and t < int(a.end)
		var before: int = int(a.live) - t
		if t >= int(a.end): continue
		for r: Rect2 in a.cells:
			var inner: Rect2 = r.grow(-2.0)
			var poly: PackedVector2Array = PackedVector2Array([_bp(s, v, inner.position), _bp(s, v, Vector2(inner.end.x, inner.position.y)), _bp(s, v, inner.end), _bp(s, v, Vector2(inner.position.x, inner.end.y))])
			if live:
				c.draw_colored_polygon(poly, Color(0.55, 0.2, 0.3, 0.55))
				_chair_icon(c, _bp(s, v, r.get_center() + Vector2(0, 2)), CREAM, false)
			else:
				var pulse: float = 0.5 + 0.5 * sin(float(before) * 0.6)
				c.draw_colored_polygon(poly, Color(ROSE, 0.06 + 0.10 * pulse))
				c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(ROSE, 0.35 + 0.3 * (1.0 - float(before) / 42.0)), 1)
				c.draw_rect(Rect2(_bp(s, v, r.get_center()) - Vector2(4, 2), Vector2(8, 4)), Color(CREAM, 0.35))

static func _draw_clock(c: CanvasItem, s: Dictionary, v: Node2D, t: int) -> void:
	var hub: Vector2 = _bp(s, v, CUE_AT)
	c.draw_arc(hub, 88.0, 0, TAU, 64, Color(CREAM, 0.10), 1)
	for k: int in range(12):
		var d: Vector2 = Vector2.from_angle(k * TAU / 12.0)
		c.draw_line(hub + d * 82.0, hub + d * 88.0, Color(CREAM, 0.25), 1)
	c.draw_arc(hub, 20.0, 0, TAU, 24, Color(CREAM, 0.15), 1)
	var live: bool = t >= 40
	var alpha: float = 1.0 if live else 0.35
	var segs: Array = _hand_segments(s)
	for i: int in [0, 2]:
		var tip: Vector2 = _bp(s, v, segs[i + 1][0])
		var gap_start: Vector2 = _bp(s, v, segs[i][1])
		_dashed(c, gap_start, tip, Color(CREAM, 0.3 * alpha), 2.0)
	c.draw_circle(hub, 2.5, Color(GOLD, alpha))

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	match str(s.patternId):
		"roll_call":
			for side: float in [-1.0, 1.0]:
				var at: Vector2 = _bp(s, v, Vector2(side * (h.x + 14.0), -h.y + 22.0))
				var calling: bool = absf(float(s.get("caller", 0.0)) - side) < 0.1 and int(s.bannerTicks) > 0
				c.draw_rect(Rect2(at + Vector2(-7, -2), Vector2(14, 22)), Color("3a2c22"))
				c.draw_rect(Rect2(at + Vector2(-7, -2), Vector2(14, 22)), GOLD if calling else Color(GOLD, 0.4), false, 1)
				c.draw_rect(Rect2(at + Vector2(-9, -5), Vector2(18, 4)), Color("5a4430"))
				if calling: c.draw_arc(at + Vector2(0, -10), 5.0, PI * 1.1, PI * 1.9, 8, Color(CREAM, 0.8), 1)
		"perfect_record", "loved_by_all", "needs_nobody":
			_draw_ideals(c, s, v)
		"tassel":
			var pv: Vector2 = _bp(s, v, PIVOT)
			c.draw_circle(pv, 3.0, GOLD)
		"commencement":
			for side: float in [-1.0, 1.0]:
				var at2: Vector2 = _bp(s, v, Vector2(side * (h.x + 10.0), 0.0))
				c.draw_rect(Rect2(at2 + Vector2(-6, -14), Vector2(12, 28)), Color(MINT, 0.25), false, 1)
				_text(c, v, at2 + Vector2(0, -18), "EXIT", Color(MINT, 0.6), 12, 40.0)
		"strings":
			for b: Dictionary in s.bullets:
				if not b.has("baseX"): continue
				var top: bool = b.top
				var edge: Vector2 = _bp(s, v, Vector2(float(b.x), -h.y - 6.0 if top else h.y + 6.0))
				var col: Color = Color(CREAM, 0.9 if int(b.age) > int(b.arm) else 0.4)
				c.draw_line(edge + Vector2(-7, 0), edge + Vector2(7, 0), col, 2)
				c.draw_line(edge + Vector2(0, -4), edge + Vector2(0, 4), col, 1)

## Stage 1: the three ideal portraits VAL holds up over the box. A rejected
## ideal is shown torn.
static func _draw_ideals(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var ids: Array[String] = ["jules", "imani", "walt"]
	var focus: int = ["perfect_record", "loved_by_all", "needs_nobody"].find(str(s.patternId))
	for i: int in range(3):
		var at: Vector2 = _bp(s, v, Vector2((i - 1) * 40.0, -h.y - 32.0))
		var torn: bool = ids[i] in s.rejected
		var col: Color = GOLD if i == focus else Color(GOLD, 0.45)
		c.draw_rect(Rect2(at - Vector2(9, 10), Vector2(18, 20)), Color("1c1a28"))
		c.draw_rect(Rect2(at - Vector2(9, 10), Vector2(18, 20)), col, false, 1)
		c.draw_circle(at + Vector2(0, -2), 3.0, Color(CREAM, 0.6))
		c.draw_rect(Rect2(at + Vector2(-4, 2), Vector2(8, 6)), Color(CREAM, 0.6))
		if torn:
			c.draw_polyline(PackedVector2Array([at + Vector2(-9, -6), at + Vector2(-2, -1), at + Vector2(1, -5), at + Vector2(9, 4)]), ROSE, 1)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, _v: Node2D) -> bool:
	var armed: bool = int(b.age) > int(b.arm)
	match str(b.shape):
		"cap":
			var bob: float = 0.0
			if b.has("march"): bob = -1.5 * absf(sin(float(b.age) * 0.21 + float(b.get("bob", 0)) * 0.6))
			var p: Vector2 = at + Vector2(0, bob)
			var top: PackedVector2Array = PackedVector2Array([p + Vector2(-6.5, -1).rotated(turn), p + Vector2(0, -4.5).rotated(turn), p + Vector2(6.5, -1).rotated(turn), p + Vector2(0, 2.5).rotated(turn)])
			c.draw_colored_polygon(PackedVector2Array([p + Vector2(-3.5, 0).rotated(turn), p + Vector2(3.5, 0).rotated(turn), p + Vector2(3.5, 4).rotated(turn), p + Vector2(-3.5, 4).rotated(turn)]), Color(BOARD, alpha))
			c.draw_colored_polygon(top, Color(Color("4a4363"), alpha))
			c.draw_polyline(top + PackedVector2Array([top[0]]), Color(CREAM, alpha), 1)
			c.draw_line(p + Vector2(0, -1).rotated(turn), p + Vector2(5, 3).rotated(turn), Color(GOLD, alpha), 1)
			c.draw_circle(p + Vector2(5, 4).rotated(turn), 1.2, Color(GOLD, alpha))
		"scroll":
			c.draw_colored_polygon(_quad(at, 6.0, 2.5, turn), Color(CREAM, alpha))
			c.draw_line(at + Vector2(-6, -2.5).rotated(turn), at + Vector2(-6, 2.5).rotated(turn), Color(Color("b8a882"), alpha), 2)
			c.draw_line(at + Vector2(0, -3).rotated(turn), at + Vector2(0, 3).rotated(turn), Color(INK_RED, alpha), 2)
		"ribbon":
			c.draw_colored_polygon(_quad(at, float(b.w), float(b.h), turn), Color(INK_RED, 0.9 * alpha))
			c.draw_line(at + Vector2(-float(b.w), 0).rotated(turn), at + Vector2(float(b.w), 0).rotated(turn), Color(GOLD, alpha), 1)
		"star":
			var a_star: float = alpha * (1.0 if armed else 0.35)
			var pts: PackedVector2Array = []
			for i: int in range(10):
				var rad: float = 4.5 if i % 2 == 0 else 1.9
				pts.append(at + Vector2.from_angle(-PI * 0.5 + i * PI / 5.0 + float(b.age) * 0.03) * rad)
			c.draw_colored_polygon(pts, Color(GOLD, a_star))
			c.draw_circle(at, 1.0, Color(Color("fff6dc"), a_star))
		"pen":
			var hw: float = float(b.w)
			var dir: Vector2 = Vector2.RIGHT.rotated(turn)
			if not armed:
				var k: float = float(b.age) / maxf(1.0, float(b.arm))
				_dashed(c, at - dir * hw, at + dir * hw, Color(INK_RED, 0.25 + 0.45 * k), 3.0)
			else:
				var drawn: float = clampf(float(int(b.age) - int(b.arm)) / 5.0, 0.0, 1.0)
				c.draw_line(at - dir * hw, at - dir * hw + dir * hw * 2.0 * drawn, Color(INK_RED, alpha), 3)
		"inkring":
			var gw: float = float(b.gapWidth) * 0.5
			var rr: float = maxf(1.0, float(b.radius))
			var gap_at: float = float(b.gap) + turn - float(b.rot)
			if armed:
				c.draw_arc(at, rr, gap_at + gw, gap_at + TAU - gw, 32, Color(INK_RED, alpha), 2.5)
			else:
				var segs: int = 16
				for i: int in range(segs):
					var a0: float = gap_at + gw + (TAU - 2.0 * gw) * float(i) / float(segs)
					if i % 2 == 0: c.draw_arc(at, rr, a0, a0 + (TAU - 2.0 * gw) / float(segs), 3, Color(INK_RED, 0.55 * alpha), 1)
			if rr > 10.0: _text(c, _v, at + Vector2(0, -rr - 3.0), "SEE ME", Color(INK_RED, 0.8 * alpha), 12, 60.0)
		"heart":
			var col: Color = Color(Color("f08a9a"), alpha)
			c.draw_circle(at + Vector2(-1.6, -1), 2.0, col)
			c.draw_circle(at + Vector2(1.6, -1), 2.0, col)
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-3.5, -0.5), at + Vector2(3.5, -0.5), at + Vector2(0, 3.8)]), col)
		"spot":
			var rr2: float = float(b.r)
			if not armed:
				var k2: float = float(b.age) / maxf(1.0, float(b.arm))
				c.draw_arc(at, lerpf(40.0, rr2, k2), 0, TAU, 28, Color(Color("fff0c0"), 0.25 + 0.5 * k2), 1)
				c.draw_line(at + Vector2(-4, 0), at + Vector2(4, 0), Color(ROSE, 0.6), 1)
				c.draw_line(at + Vector2(0, -4), at + Vector2(0, 4), Color(ROSE, 0.6), 1)
			else:
				c.draw_circle(at, rr2, Color(1.0, 0.95, 0.75, 0.45 * alpha))
				c.draw_arc(at, rr2, 0, TAU, 28, Color(Color("fff6dc"), alpha), 2)
		"hands":
			var q: PackedVector2Array = _quad(at, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(q, Color(Color("4a2a3a"), 0.92 * alpha))
			var edge_y: float = float(b.h) if float(b.clap) < 0.0 else -float(b.h)
			var x: float = -float(b.w)
			while x < float(b.w):
				var cuff: Vector2 = at + Vector2(x + 5.0, edge_y).rotated(turn)
				c.draw_circle(cuff, 3.5, Color(Color("e8c0a0"), alpha))
				x += 12.0
			c.draw_line(at + Vector2(-float(b.w), edge_y).rotated(turn), at + Vector2(float(b.w), edge_y).rotated(turn), Color(ROSE, alpha), 1)
		"door":
			var q2: PackedVector2Array = _quad(at, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(q2, Color(WOOD, alpha))
			c.draw_polyline(q2 + PackedVector2Array([q2[0]]), Color(GOLD, alpha), 1)
			var knob_y: float = float(b.h) - 6.0 if b.doorTop else -float(b.h) + 6.0
			c.draw_circle(at + Vector2(2, knob_y).rotated(turn), 1.3, Color(GOLD, alpha))
		"cord":
			var cd: Vector2 = Vector2.RIGHT.rotated(turn) * float(b.w)
			var ca: float = alpha * (1.0 if armed else 0.4)
			c.draw_line(at - cd, at + cd, Color(GOLD, 0.95 * ca), 3)
			c.draw_line(at - cd, at + cd, Color(Color("fff0c0"), ca), 1)
		"bob":
			var ba: float = alpha * (1.0 if armed else 0.4)
			var down: Vector2 = Vector2.DOWN
			var across: Vector2 = Vector2.RIGHT
			c.draw_circle(at, 5.0, Color(GOLD, ba))
			for k: int in range(-3, 4):
				c.draw_line(at + across * k * 1.5, at + across * k * 2.2 + down * 9.0, Color(GOLD, 0.9 * ba), 1)
			c.draw_circle(at - down * 4.0, 2.5, Color(Color("c88a3a"), ba))
		"hand":
			var hd: Vector2 = Vector2.RIGHT.rotated(turn) * float(b.w)
			var minute: bool = int(b.hand) >= 2
			var ha: float = alpha * (1.0 if armed else 0.35)
			c.draw_line(at - hd, at + hd, Color(GOLD if minute else CREAM, ha), 3 if minute else 4)
			c.draw_line(at - hd, at + hd, Color(Color("fff6dc"), ha), 1)
		"ember":
			c.draw_circle(at, 2.5, Color(Color("f0a040"), alpha))
			c.draw_circle(at, 1.2, Color(Color("fff0c0"), alpha))
		"chair":
			var colc: Color = Color(CREAM, alpha)
			_chair_icon(c, at, colc, bool(b.get("flipY", false)))
		"card":
			var colk: Color = Color(CREAM, alpha * (1.0 if armed else 0.6))
			c.draw_colored_polygon(_quad(at, 4.5, 3.0, turn + (0.0 if armed else sin(float(b.age) * 0.4) * 0.3)), colk)
			c.draw_line(at + Vector2(-3, -0.8).rotated(turn), at + Vector2(3, -0.8).rotated(turn), Color(INK_RED, alpha), 1)
			c.draw_line(at + Vector2(-3, 1).rotated(turn), at + Vector2(1, 1).rotated(turn), Color(LILAC, alpha), 1)
		"ghost":
			var ga: float = alpha * (0.75 if armed else 0.3)
			c.draw_circle(at + Vector2(0, -3), 2.8, Color(LILAC, ga))
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-4, 5), at + Vector2(-3, -1), at + Vector2(3, -1), at + Vector2(4, 5), at + Vector2(2, 3.5), at + Vector2(0, 5), at + Vector2(-2, 3.5)]), Color(LILAC, ga))
			c.draw_line(at + Vector2(-4.5, -6), at + Vector2(4.5, -6), Color(CREAM, ga), 1)
		"thread":
			var vel: Vector2 = Vector2(float(b.vx), float(b.vy)).normalized()
			c.draw_line(at - vel * 4.0, at + vel * 1.0, Color(GOLD, alpha), 1)
			c.draw_circle(at, 1.2, Color(Color("fff0c0"), alpha))
		"string":
			var top_edge: Vector2 = at + Vector2(0, -float(b.h)).rotated(turn)
			var bottom_edge: Vector2 = at + Vector2(0, float(b.h)).rotated(turn)
			if armed:
				c.draw_line(top_edge, bottom_edge, Color(CREAM, alpha), 2)
				var end_pt: Vector2 = bottom_edge if b.top else top_edge
				c.draw_circle(end_pt, 2.0, Color(GOLD, alpha))
			else:
				_dashed(c, top_edge, bottom_edge, Color(CREAM, 0.2 + 0.5 * float(b.age) / maxf(1.0, float(b.arm))), 3.0)
		"bead":
			c.draw_circle(at, 2.5, Color(LILAC, alpha))
			c.draw_circle(at + Vector2(-0.8, -0.8), 0.8, Color(CREAM, alpha))
		"word":
			c.draw_circle(at, 2.0, Color(CREAM, 0.85 * alpha))
		"numeral":
			var na: float = alpha * (1.0 if armed else 0.35)
			c.draw_line(at + Vector2(-2, -4).rotated(turn), at + Vector2(-2, 4).rotated(turn), Color(CREAM, na), 2)
			c.draw_line(at + Vector2(2, -4).rotated(turn), at + Vector2(2, 4).rotated(turn), Color(CREAM, na), 2)
			c.draw_line(at + Vector2(-3.5, -4).rotated(turn), at + Vector2(3.5, -4).rotated(turn), Color(CREAM, na), 1)
			c.draw_line(at + Vector2(-3.5, 4).rotated(turn), at + Vector2(3.5, 4).rotated(turn), Color(CREAM, na), 1)
		"walker":
			var wa: float = alpha * (0.85 if armed else 0.3)
			var step: float = sin(float(b.age) * 0.3) * 1.5
			c.draw_circle(at + Vector2(0, -4), 2.3, Color(CREAM, wa))
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(-3, -1.5), at + Vector2(3, -1.5), at + Vector2(2.5, 3), at + Vector2(-2.5, 3)]), Color(Color("8fb3ea"), wa))
			c.draw_line(at + Vector2(-1, 3), at + Vector2(-1 - step, 6.5), Color(CREAM, wa), 1)
			c.draw_line(at + Vector2(1, 3), at + Vector2(1 + step, 6.5), Color(CREAM, wa), 1)
		"burst":
			var k3: float = float(b.age) / maxf(1.0, float(b.life))
			c.draw_circle(at, float(b.r) * (0.6 + 0.4 * k3), Color(1.0, 1.0, 0.95, 0.8 * (1.0 - k3)))
		"sparkle":
			c.draw_line(at + Vector2(-3, 0), at + Vector2(3, 0), Color(Color("fff6dc"), alpha), 1)
			c.draw_line(at + Vector2(0, -3), at + Vector2(0, 3), Color(Color("fff6dc"), alpha), 1)
		"chime":
			var gw2: float = float(b.gapWidth) * 0.5
			var g: float = float(b.gap) + turn - float(b.rot)
			c.draw_arc(at, float(b.radius), g + gw2, g + TAU - gw2, maxi(24, int(float(b.radius) * 0.6)), Color(GOLD, 0.95 * alpha), float(b.thick) * 2.0)
		"tcone":
			if not armed:
				var pop: float = float(b.age) / maxf(1.0, float(b.arm))
				c.draw_line(at + Vector2(-4, 4.5), at + Vector2(4, 4.5), Color(Color("e8843c"), 0.2 + 0.5 * pop), 1)
				return true
			c.draw_colored_polygon(PackedVector2Array([at + Vector2(0, -5), at + Vector2(4, 4), at + Vector2(-4, 4)]), Color(Color("e8843c"), alpha))
			c.draw_line(at + Vector2(-2.5, 0), at + Vector2(2.5, 0), Color(CREAM, alpha), 1)
			c.draw_line(at + Vector2(-5, 4.5), at + Vector2(5, 4.5), Color(Color("e8843c"), alpha), 1)
		"key":
			var ka: float = alpha * (1.0 if armed else 0.35)
			var d: Vector2 = Vector2.RIGHT.rotated(turn)
			var sd: Vector2 = Vector2(-d.y, d.x)
			c.draw_arc(at - d * 3.0, 2.3, 0, TAU, 10, Color(GOLD, ka), 1.5)
			c.draw_line(at - d * 0.8, at + d * 5.0, Color(GOLD, ka), 1.5)
			c.draw_line(at + d * 4.0, at + d * 4.0 + sd * 2.2, Color(GOLD, ka), 1)
			c.draw_line(at + d * 2.5, at + d * 2.5 + sd * 2.0, Color(GOLD, ka), 1)
		_:
			return false
	return true

static func _quad(at: Vector2, hw: float, hh: float, turn: float) -> PackedVector2Array:
	return PackedVector2Array([at + Vector2(-hw, -hh).rotated(turn), at + Vector2(hw, -hh).rotated(turn), at + Vector2(hw, hh).rotated(turn), at + Vector2(-hw, hh).rotated(turn)])
