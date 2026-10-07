extends RefCounted
## ADVISOR BEV (internal id "claim"): the lost-property desk is her advising office, and she
## thinks every lost thing and every undecided student is her responsibility. She hands out
## take-a-number tickets, runs degree audits and keeps unrolling a four-year plan.
## Five handmade attacks, one per turn, cycling in order: Degree Audit (checklist cards on a
## belt), Take a Number (a ribbon of tickets), Syllabus Week (rolled syllabi that pop open into
## rings of due dates), Advising Hold (sticky notes and HOLD stamps) and The Rolodex (index
## cards circling a Rolodex, pencils from the corners).
## The promise and its fields are the old encounter's, unchanged, because
## core/claim_needs.gd record_defense() and main.gd read them:
##   encounterId, done, promiseComplete, phase, carryTag, claimSweepPassed,
##   delivery, noteLeft, boundary (set by main.gd after create) and
##   markers [{id, x, y, collected, active, noted}] (x, y in arena space).
## Phase 0 "Hold On To This": marker 0 is the numbered ticket (touch while promised sets
## carryTag), marker 1 the owner's pigeonhole (active once carrying, touch). The FOUR-YEAR PLAN
## (a wall of plan pages with one free-elective gap) unrolls across the box twice; each one
## that passes fully while you carry the ticket adds to claimSweepPassed.
## Phase 1 "One Thing Now": marker 0 is the ticket (touch), markers 1 and 2 are
## two returns (confirm), usable only with the boundary set and no delivery
## yet. Confirming at one sets delivery = its id and noteLeft, and leaves a
## note (noted) on the other, which stays uncollected.
## The markers are drawn and steered through objectives 0..2 (same ids).

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["degree_audit", "take_a_number", "syllabus_week", "advising_hold", "rolodex"]
const PHASES: Array[int] = [0, 1]
const SWEEP_SPEED: float = 2.0
const SWEEP_TIMES: Array[int] = [80, 230]

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const ROSE: Color = Color("e8837b")
const LILAC: Color = Color("a68db8")
const PLUM: Color = Color("292638")
const TICKET_RED: Color = Color("c8505a")
const TEAL: Color = Color("2f9c99")
const PARCH: Color = Color("ecdcae")
const STICKY: Color = Color("f2dc7a")
## Header tints for audit cards and plan pages (fall rust, spring teal, summer mustard, mauve, slate).
const TINTS: Array[Color] = [Color("a8584a"), Color("2f9c99"), Color("d8a43c"), Color("a66a8c"), Color("5a6c8a")]

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	var phase: int = clampi(int(s.phase), 0, 1)
	s.patternId = id
	s.length = 480
	s.phaseName = "Hold On To This" if phase == 0 else "One Thing Now"
	s.carryTag = false
	s.claimSweepPassed = 0
	s.noteLeft = false
	s.delivery = -1
	s.sweeps = []
	s.queue = []
	s.ribbons = []
	s.spin = [0.0, 0.0]
	s.spinRate = [0.012, -0.009]
	s.detached = 0
	s.flash = {}
	# Spots are fractions of the box half size, so they ride box changes.
	var tag: Vector2 = Vector2(-0.45, 0.15) if phase == 0 else Vector2(0.0, 0.0)
	var dest: Array = [Vector2(0.62, -0.45)] if phase == 0 else [Vector2(-0.6, -0.45), Vector2(0.6, 0.5)]
	var hint: String = ""
	match id:
		"degree_audit":
			s.attackName = "Degree Audit"
			hint = "Audit cards ride the belt. A shaking card is flung along its red line."
		"take_a_number":
			s.attackName = "Take a Number"
			hint = "The ticket ribbon winds around. NEXT, SWEETIE fires a fan of tickets."
		"syllabus_week":
			s.attackName = "Syllabus Week"
			hint = "Rolled syllabi fall, shake, then open into a ring of due dates. Find the gap."
		"advising_hold":
			s.attackName = "Advising Hold"
			hint = "Sticky notes slap shut on the red row. HOLD stamps drop down the red column."
			if phase == 1: dest = [Vector2(-0.6, -0.6), Vector2(0.6, 0.6)]
		"rolodex":
			s.attackName = "The Rolodex"
			hint = "Index cards circle the Rolodex and breathe. Pencils fly from the corners."
			if phase == 0:
				tag = Vector2(-0.48, 0.35); dest = [Vector2(0.7, -0.62)]
			else:
				tag = Vector2(0.0, -0.66); dest = [Vector2(-0.74, -0.6), Vector2(0.74, 0.62)]
	s.tagSpot = tag
	s.destSpots = dest
	if phase == 0:
		s.hint = "Carry the ticket to its pigeonhole. When the FOUR-YEAR PLAN unrolls, wait in the gap. " + hint
		s.markers = [{"id": 0, "x": 80.0, "y": 60.0, "collected": false, "active": true, "noted": false}, {"id": 1, "x": 204.0, "y": 36.0, "collected": false, "active": false, "noted": false}]
		D.objective(s, {"kind": "touch", "r": 10.0, "label": "ticket"})
		D.objective(s, {"kind": "touch", "r": 12.0, "label": "owner", "active": false})
	else:
		s.hint = "Take the ticket. Confirm at ONE return; the other gets a note. " + hint
		s.markers = [{"id": 0, "x": 128.0, "y": 60.0, "collected": false, "active": true, "noted": false}, {"id": 1, "x": 56.0, "y": 36.0, "collected": false, "active": false, "noted": false}, {"id": 2, "x": 200.0, "y": 100.0, "collected": false, "active": false, "noted": false}]
		D.objective(s, {"kind": "touch", "r": 10.0, "label": "ticket"})
		D.objective(s, {"kind": "confirm", "r": 13.0, "label": "return", "active": false})
		D.objective(s, {"kind": "confirm", "r": 13.0, "label": "return", "active": false})
	_sync(s)

## Lets the preview tools run phase 1 (main.gd sets boundary after create).
static func preview(s: Dictionary, _phase: int) -> void:
	s.boundary = true

static func confirm(s: Dictionary) -> void:
	_sync(s)

static func promise_complete(s: Dictionary) -> bool:
	if int(s.phase) == 0:
		return bool(s.markers[0].collected) and bool(s.markers[1].collected) and int(s.claimSweepPassed) > 0
	return int(s.delivery) > 0 and bool(s.noteLeft)

static func progress(s: Dictionary) -> String:
	var markers: Array = s.get("markers", [])
	if int(s.get("phase", 0)) == 0:
		return "Ticket %s / plan %s\ndelivered %s" % ["held" if s.get("carryTag", false) else "open", "clear" if int(s.get("claimSweepPassed", 0)) > 0 else "open", "yes" if markers.size() > 1 and markers[1].get("collected", false) else "open"]
	return "One return %s / note %s\nboundary %s" % ["done" if int(s.get("delivery", 0)) > 0 else "open", "left" if s.get("noteLeft", false) else "open", "kept" if s.get("boundary", false) and s.get("promiseComplete", false) else "offered" if s.get("boundary", false) else "open"]

## The old marker rules, carried by objectives with the same ids.
static func _sync(s: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	var objs: Array = s.objectives
	var spots: Array = [Vector2(s.tagSpot)] + Array(s.destSpots)
	for i: int in range(objs.size()):
		var at: Vector2 = Vector2(spots[i]) * h
		objs[i].x = at.x; objs[i].y = at.y
	if objs[0].done and not bool(s.carryTag):
		s.carryTag = true
		D.banner(s, "TICKET HELD", 40)
	if int(s.phase) == 0:
		objs[1].active = bool(s.carryTag) and not objs[1].done
	else:
		for i: int in [1, 2]:
			if objs[i].done and int(s.delivery) < 0:
				s.delivery = i
				s.noteLeft = true
				s.markers[3 - i].noted = true
				D.banner(s, "RETURNED. NOTE LEFT.", 60)
				D.effect(s, "kept", D.to_world(s, Vector2(float(objs[3 - i].x), float(objs[3 - i].y))), 30)
		for i: int in [1, 2]:
			objs[i].active = bool(s.carryTag) and bool(s.boundary) and int(s.delivery) < 0 and not objs[i].done
	for i: int in range(s.markers.size()):
		var m: Dictionary = s.markers[i]
		var world: Vector2 = D.to_world(s, Vector2(float(objs[i].x), float(objs[i].y)))
		m.x = world.x; m.y = world.y
		m.collected = bool(objs[i].done)
		if i > 0 and bool(s.carryTag): m.active = int(s.delivery) < 0

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	if phase == 0:
		for at: int in SWEEP_TIMES:
			if t == at - 50: _sweep_start(s, t)
	match str(s.patternId):
		"degree_audit": _degree_audit(s, t, phase)
		"take_a_number": _take_a_number(s, t, phase)
		"syllabus_week": _syllabus_week(s, t, phase)
		"advising_hold": _advising_hold(s, t, phase)
		"rolodex": _rolodex(s, t, phase)
	_run_queue(s, t)
	_sync(s)

static func after(s: Dictionary, t: int) -> void:
	_sync(s)
	if t < 0: return
	# Plan sweeps: count each one that has fully passed while you carry the ticket.
	var h: Vector2 = D.half(s)
	for sweep: Dictionary in s.sweeps:
		sweep.x = float(sweep.x) + float(sweep.vx)
		if not sweep.counted and float(sweep.x) < -h.x - 16.0:
			sweep.counted = true
			if bool(s.carryTag):
				s.claimSweepPassed = int(s.claimSweepPassed) + 1
				s.objectiveChanged = true
				D.banner(s, "ELECTIVE FOUND", 40)
				D.effect(s, "kept", D.soul_world(s), 30)
	var spawns: Array = []
	for b: Dictionary in s.bullets:
		if b.has("fade"): continue
		# Clapping sticky notes meet in the middle and pull back.
		if b.has("clap") and not b.get("clapped", false) and absf(float(b.x)) <= 11.0:
			b.clapped = true
			b.vx = -float(b.vx) * 0.55
			if float(b.x) < 0.0: D.effect(s, "pulse", D.to_world(s, Vector2(0, float(b.y))), 14)
		# Rolled syllabi pop open into a ring of due dates.
		if b.has("popAt") and int(b.age) >= int(b.popAt):
			spawns.append(b)
	for b: Dictionary in spawns:
		_pop(s, b)

# ---------------------------------------------------------------- shared pieces

static func _run_queue(s: Dictionary, t: int) -> void:
	var kept: Array = []
	var due: Array = []
	for e: Dictionary in s.queue:
		if int(e.at) <= t: due.append(e)
		else: kept.append(e)
	s.queue = kept
	for e: Dictionary in due:
		match str(e.kind):
			"fling": _fling(s, e)
			"fan": _fan(s, e)
			"pencil": _pencil(s, e)
			"stamp":
				D.shot(s, {"space": "box", "x": float(e.x), "y": -D.half(s).y - 8.0, "vy": 3.0, "collide": "rect", "w": 6.0, "h": 4.0, "shape": "hold_stamp", "life": 160})
			"belt":
				var on: Vector2 = _belt_point(s, float(e.u) + float(s.spin[0]))
				D.shot(s, {"space": "box", "x": on.x, "y": on.y, "belt": float(e.u), "collide": "rect", "w": 8.0, "h": 5.5, "shape": "audit_card", "hue": int(e.hue), "life": 2000, "arm": 12})
				D.effect(s, "mode", D.to_world(s, on), 16)

static func _sweeping(s: Dictionary) -> bool:
	var h: Vector2 = D.half(s)
	for sweep: Dictionary in s.sweeps:
		if float(sweep.x) < h.x + 30.0 and float(sweep.x) > -h.x - 20.0: return true
	return false

## The FOUR-YEAR PLAN: a wall of plan pages crosses right to left with a two-page gap, the one
## free elective.
static func _sweep_start(s: Dictionary, t: int) -> void:
	var h: Vector2 = D.half(s)
	var step: float = 15.0
	var slots: int = int(ceil((h.y * 2.0 - 6.0) / step)) + 1
	var top: float = -float(slots - 1) * step * 0.5
	var k: int = 1 + int(D.rand(s) * float(slots - 3))
	var x: float = h.x + 16.0 + SWEEP_SPEED * 50.0
	var id: int = s.sweeps.size()
	for i: int in range(slots):
		if i == k or i == k + 1: continue
		D.shot(s, {"space": "box", "x": x, "y": top + i * step, "vx": -SWEEP_SPEED, "collide": "rect", "w": 6.0, "h": 6.5, "shape": "plan_page", "hue": (i + id) % TINTS.size(), "life": 420, "sweep": id})
	s.sweeps.append({"x": x, "vx": -SWEEP_SPEED, "gapY": top + (float(k) + 0.5) * step, "counted": false, "born": t, "id": id})
	D.banner(s, "THE FOUR-YEAR PLAN", 50)
	s.telegraphs.append({"ticksRemaining": 50})

# ---------------------------------------------------------------- attacks

# Degree Audit: audit cards ride a belt around the inside of the box. A card
# shakes and shows a red line (a requirement left unchecked), then is flung along
# it (aimed at you) and a new one drops onto the belt. Phase 1 flings two at a
# time and the belt reverses halfway.
static func _belt_point(s: Dictionary, u: float) -> Vector2:
	var h: Vector2 = D.half(s) - Vector2(11, 11)
	var lengths: Array[float] = [h.x * 2.0, h.y * 2.0, h.x * 2.0, h.y * 2.0]
	var total: float = (h.x + h.y) * 4.0
	var d: float = fposmod(u, total)
	if d < lengths[0]: return Vector2(-h.x + d, -h.y)
	d -= lengths[0]
	if d < lengths[1]: return Vector2(h.x, -h.y + d)
	d -= lengths[1]
	if d < lengths[2]: return Vector2(h.x - d, h.y)
	d -= lengths[2]
	return Vector2(-h.x, h.y - d)

static func _degree_audit(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 240.0, "h": 124.0}, 24)
		var total: float = 4.0 * (120.0 - 11.0 + 62.0 - 11.0)
		for i: int in range(16):
			if i % 4 == 3: continue
			D.shot(s, {"space": "box", "belt": total * float(i) / 16.0, "collide": "rect", "w": 8.0, "h": 5.5, "shape": "audit_card", "hue": i % TINTS.size(), "life": 2000})
	if phase > 0 and t == 220:
		D.warn(s, {"kind": "spin", "dir": -1.0}, 40, true)
		D.banner(s, "THE AUDIT RE-RUNS", 40)
	var speed: float = 0.8 if phase == 0 else 1.1
	if phase > 0 and t >= 260: speed = -1.1
	if phase > 0 and t > 220 and t < 260: speed = 0.0
	s.spin[0] = float(s.spin[0]) + speed
	for b: Dictionary in s.bullets:
		if not b.has("belt") or b.has("flinging"): continue
		var at: Vector2 = _belt_point(s, float(b.belt) + float(s.spin[0]))
		b.x = at.x; b.y = at.y; b.px = at.x; b.py = at.y
		var vertical: bool = absf(absf(at.x) - (h.x - 11.0)) < 0.5
		b.rot = PI * 0.5 if vertical else 0.0
	var every: int = 56 if phase == 0 else 46
	if _sweeping(s): every *= 2
	if t % every == 20 and t > 30 and t < int(s.length) - 90:
		for n: int in range(1 + phase):
			_fling_warn(s, t, n == 1)

static func _fling_warn(s: Dictionary, t: int, far: bool) -> void:
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var pick: Dictionary = {}
	var best: float = -INF if far else INF
	for b: Dictionary in s.bullets:
		if not b.has("belt") or b.has("flinging"): continue
		var d: float = Vector2(float(b.x), float(b.y)).distance_to(soul)
		# Not the nearest one (no surprise from beside you), not one far away.
		var score: float = absf(d - 90.0)
		if far: score = d
		if (far and score > best) or (not far and score < best):
			best = score; pick = b
	if pick.is_empty(): return
	pick.flinging = true
	var from: Vector2 = Vector2(float(pick.x), float(pick.y))
	var dir: Vector2 = (soul - from).normalized()
	pick.shake = t + 34
	pick.aim = dir
	s.queue.append({"at": t + 34, "kind": "fling", "id": int(pick.id), "dx": dir.x, "dy": dir.y})

static func _fling(s: Dictionary, e: Dictionary) -> void:
	for b: Dictionary in s.bullets:
		if int(b.id) != int(e.id) or not b.has("belt"): continue
		var u: float = float(b.belt)
		b.erase("belt")
		b.erase("flinging")
		b.vx = float(e.dx) * 2.6; b.vy = float(e.dy) * 2.6
		b.life = int(b.age) + 160
		s.queue.append({"at": int(s.clock) - int(s.leadIn) + 70, "kind": "belt", "u": u, "hue": int(b.hue)})
		return

# Take a Number: a ribbon of numbered tickets unrolls from the dispenser and
# winds through the box like a snake. NEXT, SWEETIE: the dispenser lights, shows
# its aim, and fires a fan of tickets. Phase 1 adds a second ribbon from a
# second dispenser.
static func _ribbon_head(s: Dictionary, r: Dictionary, tau: float) -> Vector2:
	var h: Vector2 = D.half(s)
	var dispenser: Vector2 = Vector2(float(r.dx), -h.y - 10.0)
	var at: float = maxf(0.0, tau)
	var head: Vector2 = Vector2(sin(at * float(r.fx) + float(r.px)) * 0.8 * h.x, sin(at * float(r.fy) + float(r.py)) * 0.74 * h.y)
	if tau < 0.0:
		var start: Vector2 = Vector2(sin(float(r.px)) * 0.8 * h.x, sin(float(r.py)) * 0.74 * h.y)
		return start.lerp(dispenser, clampf(-tau / 40.0, 0.0, 1.0))
	return head

static func _take_a_number(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 236.0, "h": 120.0}, 24)
		s.ribbons = [{"dx": 100.0, "fx": 0.011, "fy": 0.019, "px": 1.2, "py": -1.3, "start": 20, "id": 0}]
		if phase > 0:
			s.ribbons.append({"dx": -100.0, "fx": -0.013, "fy": 0.016, "px": -1.0, "py": 2.0, "start": 120, "id": 1})
		for r: Dictionary in s.ribbons:
			for i: int in range(14):
				D.shot(s, {"space": "box", "x": float(r.dx), "y": -h.y - 20.0, "collide": "rect", "w": 5.0, "h": 3.5, "shape": "ticket", "seg": i, "ribbon": int(r.id), "life": 2000, "number": 40 + i})
	for b: Dictionary in s.bullets:
		if not b.has("seg"): continue
		var r: Dictionary = s.ribbons[int(b.ribbon)]
		var tau: float = float(t - int(r.start) - int(b.seg) * 6)
		var at: Vector2 = _ribbon_head(s, r, tau)
		var ahead: Vector2 = _ribbon_head(s, r, tau + 2.0)
		b.x = at.x; b.y = at.y; b.px = at.x; b.py = at.y
		if ahead.distance_to(at) > 0.05: b.rot = (ahead - at).angle()
	var every: int = 80 if phase == 0 else 64
	if _sweeping(s): every = 120
	if t % every == 40 and t < int(s.length) - 90:
		var side: float = 1.0 if int(t / every) % 2 == 0 or phase == 0 else -1.0
		var from: Vector2 = Vector2(100.0 * side, -h.y - 10.0)
		if phase == 0: from = Vector2(100.0, -h.y - 10.0)
		var aim: float = (Vector2(float(s.soul.x), float(s.soul.y)) - from).angle()
		s.serving = {"until": t + 32, "x": from.x, "aim": aim, "number": 40 + int(t / every)}
		s.telegraphs.append({"ticksRemaining": 32})
		s.queue.append({"at": t + 32, "kind": "fan", "x": from.x, "y": from.y, "aim": aim, "count": 3 if phase == 0 else 5})

static func _fan(s: Dictionary, e: Dictionary) -> void:
	var count: int = int(e.count)
	for i: int in range(count):
		var a: float = float(e.aim) + (float(i) - float(count - 1) * 0.5) * 0.28
		D.shot(s, {"space": "box", "x": float(e.x), "y": float(e.y), "vx": cos(a) * 2.2, "vy": sin(a) * 2.2, "collide": "rect", "w": 5.0, "h": 3.5, "rot": a, "shape": "ticket", "life": 220, "number": 50 + i})

# Syllabus Week: rolled syllabi fall (every other one over you), shake, then
# pop open into a ring of due dates with one gap. Phase 1 syllabi spin as they
# open and sprinkle a spiral.
static func _syllabus_week(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 220.0, "h": 124.0}, 24)
	var every: int = 36 if phase == 0 else 28
	if _sweeping(s): every = 60
	if t % every == 10 and t < int(s.length) - 110:
		var aimed: bool = int(t / every) % 2 == 0
		var x: float = clampf(float(s.soul.x) + D.rand_range(s, -12.0, 12.0), -h.x + 12.0, h.x - 12.0) if aimed else D.rand_range(s, -h.x + 14.0, h.x - 14.0)
		var spin: bool = phase > 0 and int(t / every) % 2 == 1
		D.shot(s, {"space": "box", "x": x, "y": -h.y - 10.0, "vy": 1.0, "collide": "rect", "w": 2.5, "h": 9.0, "shape": "syllabus", "popAt": int(D.rand_range(s, 62.0, 80.0)), "spinPop": spin, "life": 400, "hue": int(D.rand(s) * 4.0)})
	# Phase 1 sprinklers.
	for b: Dictionary in s.bullets:
		if b.get("sprinkle", 0) > 0 and t % 4 == 0:
			b.sprinkle = int(b.sprinkle) - 1
			for k: int in range(2):
				var a: float = float(b.rot) + k * PI
				D.shot(s, {"space": "box", "x": float(b.x), "y": float(b.y), "vx": cos(a) * 1.5, "vy": sin(a) * 1.5, "r": 2.0, "shape": "due_date", "life": 160})

static func _pop(s: Dictionary, b: Dictionary) -> void:
	b.erase("popAt")
	var from: Vector2 = Vector2(float(b.x), float(b.y))
	var count: int = 12
	var gap: int = int(D.rand(s) * count)
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	# The gap never faces you directly: you have to step to it.
	var toward: int = int(round(fposmod((soul - from).angle(), TAU) / TAU * count)) % count
	if absi(gap - toward) <= 1 or absi(gap - toward) >= count - 1: gap = (toward + count / 2) % count
	for i: int in range(count):
		if i == gap or i == (gap + 1) % count: continue
		var a: float = float(i) * TAU / float(count)
		D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": cos(a) * 1.4, "vy": sin(a) * 1.4, "r": 2.2, "shape": "due_date", "life": 200})
	b.shape = "unrolled"
	b.collide = "none"
	b.friendly = true
	b.vx = 0.0; b.vy = -0.5
	b.fade = 60
	b.spin = 0.12 if b.get("spinPop", false) else 0.0
	if b.get("spinPop", false): b.sprinkle = 9
	D.effect(s, "pulse", D.to_world(s, from), 14)

# Advising Hold: sticky notes slap shut from both sides along a red row at your
# height, then pull back. A HOLD stamp comes down a red column. Phase 1 slaps
# two rows at once and the box squeezes while they do.
static func _advising_hold(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 196.0, "h": 132.0}, 24)
	var every: int = 70 if phase == 0 else 58
	if _sweeping(s): every = 100
	if t % every == 15 and t < int(s.length) - 100:
		var y: float = clampf(float(s.soul.y), -h.y + 10.0, h.y - 10.0)
		var rows: Array[float] = [y]
		if phase > 0:
			rows.append(clampf(y + (40.0 if y < 0.0 else -40.0), -h.y + 10.0, h.y - 10.0))
			D.box_to(s, {"h": 112.0}, 20, 20)
			D.box_to(s, {"h": 132.0}, 24, 70)
		for row: float in rows:
			D.warn(s, {"kind": "lane", "y": D.centre(s).y + row, "h": 9.0, "horizontal": true}, 38, row == rows[0])
			for side: float in [-1.0, 1.0]:
				var speed: float = 3.2
				D.shot(s, {"space": "box", "x": side * (h.x + 14.0 + speed * 38.0), "y": row, "vx": -side * speed, "collide": "rect", "w": 11.0, "h": 8.0, "shape": "sticky", "clap": true, "side": side, "life": 200})
	var point_every: int = 90 if phase == 0 else 70
	if t % point_every == 60 and t < int(s.length) - 90 and not _sweeping(s):
		var xs: Array[float] = [clampf(float(s.soul.x), -h.x + 8.0, h.x - 8.0)]
		if phase > 0: xs.append(clampf(-xs[0] * 0.6 + D.rand_range(s, -20.0, 20.0), -h.x + 8.0, h.x - 8.0))
		for x: float in xs:
			D.warn(s, {"kind": "lane", "x": D.centre(s).x + x, "w": 7.0, "horizontal": false}, 36)
			s.flash[str(x)] = {"x": x, "until": int(s.clock) + 36}
			s.queue.append({"at": t + 30, "kind": "stamp", "x": x})

# The Rolodex: two rings of index cards circle the Rolodex in the middle, in
# opposite directions, breathing in and out. Pencils are tossed from the corners
# at you. Phase 1 reverses the rings halfway and cards fly off the outer ring.
static func _rolodex(s: Dictionary, t: int, phase: int) -> void:
	var h: Vector2 = D.half(s)
	if t == 0:
		D.box_to(s, {"w": 208.0, "h": 132.0}, 24)
		var counts: Array[int] = [9, 16]
		for ring: int in range(2):
			for k: int in range(counts[ring]):
				if ring == 0 and k >= 7: continue
				if ring == 1 and k >= 13: continue
				D.shot(s, {"space": "box", "collide": "rect", "w": 6.0, "h": 2.5, "shape": "index_card", "ring": ring, "slot": k, "slots": counts[ring], "life": 2000})
		D.shot(s, {"space": "box", "x": 0.0, "y": 0.0, "r": 7.0, "shape": "rolodex_hub", "hold": true, "life": 2000})
	if phase > 0 and t == 200:
		D.warn(s, {"kind": "spin", "dir": -1.0}, 40, true)
		D.banner(s, "ROLODEX SPINS BACK", 40)
	var rates: Array = s.spinRate
	if phase > 0 and t >= 200 and t < 240: rates = [0.0, 0.0]
	elif phase > 0 and t >= 240: rates = [-0.012, 0.010]
	s.spin[0] = float(s.spin[0]) + float(rates[0])
	s.spin[1] = float(s.spin[1]) + float(rates[1])
	var radii: Array[float] = [34.0 + 8.0 * sin(t * 0.03), 60.0 + 9.0 * sin(t * 0.03 + PI)]
	for b: Dictionary in s.bullets:
		if not b.has("ring"): continue
		var ring: int = int(b.ring)
		var a: float = float(b.slot) * TAU / float(b.slots) + float(s.spin[ring])
		var at: Vector2 = Vector2(cos(a), sin(a)) * radii[ring]
		b.x = at.x; b.y = at.y; b.px = at.x; b.py = at.y
		b.rot = a + PI * 0.5
		if b.has("detachAt") and t >= int(b.detachAt):
			var tangent: Vector2 = Vector2(-sin(a), cos(a)) * signf(float(rates[ring]) + 0.0001)
			b.erase("ring")
			b.vx = tangent.x * 1.8 + cos(a) * 0.7; b.vy = tangent.y * 1.8 + sin(a) * 0.7
			b.spin = 0.2
			b.life = int(b.age) + 200
	if phase > 0 and t % 50 == 25 and t > 60 and t < int(s.length) - 90 and int(s.detached) < 5:
		for b: Dictionary in s.bullets:
			if int(b.get("ring", -1)) == 1 and not b.has("detachAt") and D.rand(s) < 0.2:
				b.detachAt = t + 24
				s.detached = int(s.detached) + 1
				break
	var every: int = 64 if phase == 0 else 52
	if _sweeping(s): every = 110
	if t % every == 30 and t < int(s.length) - 90:
		var corner: Vector2 = Vector2(1.0 if D.rand(s) < 0.5 else -1.0, 1.0 if D.rand(s) < 0.5 else -1.0)
		var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
		var dir: Vector2 = (soul - corner * (h - Vector2(4, 4))).normalized()
		D.warn(s, {"kind": "edge", "space": "box", "x": corner.x * (h.x - 6.0), "y": corner.y * (h.y - 6.0), "dir": dir}, 32)
		s.queue.append({"at": t + 32, "kind": "pencil", "cx": corner.x, "cy": corner.y})

static func _pencil(s: Dictionary, e: Dictionary) -> void:
	var h: Vector2 = D.half(s)
	var from: Vector2 = Vector2(float(e.cx) * (h.x + 6.0), float(e.cy) * (h.y + 6.0))
	var dir: Vector2 = (Vector2(float(s.soul.x), float(s.soul.y)) - from).normalized()
	D.shot(s, {"space": "box", "x": from.x, "y": from.y, "vx": dir.x * 2.0, "vy": dir.y * 2.0, "r": 5.0, "shape": "pencil", "spin": 0.2, "life": 200})

# ---------------------------------------------------------------- drawing

static func _pt(at: Vector2, turn: float, x: float, y: float) -> Vector2:
	return at + Vector2(x, y).rotated(turn)

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var t: int = int(s.clock) - int(s.leadIn)
	# A degree audit printout: faint ruled lines and a red margin.
	var y: float = -h.y + 14.0
	while y < h.y:
		c.draw_line(v.box_point(Vector2(-h.x, y)), v.box_point(Vector2(h.x, y)), Color(LILAC, 0.05), 1)
		y += 14.0
	c.draw_line(v.box_point(Vector2(-h.x + 12.0, -h.y)), v.box_point(Vector2(-h.x + 12.0, h.y)), Color(ROSE, 0.07), 1)
	if s.patternId == "degree_audit":
		var inset: Vector2 = h - Vector2(11, 11)
		for grow: float in [-7.0, 7.0]:
			var r: Rect2 = Rect2(-inset - Vector2(grow, grow), (inset + Vector2(grow, grow)) * 2.0)
			var poly: PackedVector2Array = v.box_rect_poly(r)
			c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(AMBER, 0.18), 1)
		# Belt slats move with the belt.
		var total: float = (inset.x + inset.y) * 4.0
		var u: float = fposmod(float(s.spin[0]), 12.0)
		while u < total:
			var p: Vector2 = _belt_point(s, u)
			c.draw_circle(v.box_point(p), 0.8, Color(AMBER, 0.25))
			u += 12.0
		for b: Dictionary in s.bullets:
			if b.has("shake") and t < int(b.shake) and b.has("aim"):
				var from: Vector2 = Vector2(float(b.x), float(b.y))
				var a: Vector2 = b.aim
				var blink: float = 0.4 + 0.4 * sin(t * 0.6)
				var d: float = 10.0
				while d < 260.0:
					c.draw_line(v.box_point(from + a * d), v.box_point(from + a * (d + 6.0)), Color(ROSE, blink), 1)
					d += 12.0
	if s.patternId == "rolodex":
		var centre: Vector2 = v.box_point(Vector2.ZERO)
		for ring: int in range(2):
			var base: float = 34.0 if ring == 0 else 60.0
			c.draw_arc(centre, base, 0, TAU, 40, Color(AMBER, 0.08), 1)
	if s.patternId == "take_a_number" and s.has("serving") and t < int(s.serving.until):
		var from2: Vector2 = Vector2(float(s.serving.x), -h.y - 10.0)
		var dir: Vector2 = Vector2.from_angle(float(s.serving.aim))
		var blink2: float = 0.4 + 0.4 * sin(t * 0.6)
		for k: int in [-1, 0, 1]:
			var dk: Vector2 = dir.rotated(k * 0.28 * (2.0 if int(s.phase) > 0 else 1.0))
			c.draw_line(v.box_point(from2 + dk * 14.0), v.box_point(from2 + dk * 200.0), Color(ROSE, blink2 * (1.0 if k == 0 else 0.5)), 1)
	# The ticket, the owner's pigeonhole and the returns, under their mint outlines.
	var objs: Array = s.objectives
	if bool(s.promised):
		var tag: Dictionary = objs[0]
		if tag.active and not tag.done: _draw_tag(c, v.box_point(Vector2(float(tag.x), float(tag.y))), float(s.box.rot), 1.0)
		for i: int in range(1, objs.size()):
			var o: Dictionary = objs[i]
			var at: Vector2 = v.box_point(Vector2(float(o.x), float(o.y)))
			if s.markers[i].get("noted", false):
				# A sticky note left on the pigeonhole.
				c.draw_colored_polygon(v.quad(at, 7.0, 8.0, -0.1), Color(STICKY, 0.92))
				for k: int in range(3):
					c.draw_line(at + Vector2(-4, -4 + k * 3.5), at + Vector2(4 - k * 2, -4 + k * 3.5), Color(Color("8a6a3c"), 0.9), 1)
			elif o.active and not o.done:
				# A pigeonhole with a label card: where a thing belongs.
				c.draw_polyline(PackedVector2Array([at + Vector2(-4.5, -4), at + Vector2(-4.5, 4), at + Vector2(4.5, 4), at + Vector2(4.5, -4)]), Color(CREAM, 0.8), 2)
				c.draw_rect(Rect2(at + Vector2(-2.5, 5.5), Vector2(5, 2)), Color(CREAM, 0.8))

## The numbered ticket you carry: a gold take-a-number stub with notched sides.
static func _draw_tag(c: CanvasItem, at: Vector2, turn: float, alpha: float) -> void:
	var q: PackedVector2Array = PackedVector2Array([
		_pt(at, turn, -6, -3.5), _pt(at, turn, 6, -3.5), _pt(at, turn, 6, -1.2), _pt(at, turn, 4.6, 0), _pt(at, turn, 6, 1.2),
		_pt(at, turn, 6, 3.5), _pt(at, turn, -6, 3.5), _pt(at, turn, -6, 1.2), _pt(at, turn, -4.6, 0), _pt(at, turn, -6, -1.2)])
	c.draw_colored_polygon(q, Color(AMBER, alpha))
	c.draw_line(_pt(at, turn, -2.5, -1.2), _pt(at, turn, 2.0, -1.2), Color(INK, alpha), 1)
	c.draw_line(_pt(at, turn, -2.5, 1.4), _pt(at, turn, 0.5, 1.4), Color(INK, alpha), 1)
	c.draw_line(_pt(at, turn, 3.6, -2.5), _pt(at, turn, 3.6, 2.5), Color(INK, 0.5 * alpha), 1)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	var t: int = int(s.clock) - int(s.leadIn)
	# The carried ticket dangles from the soul.
	if bool(s.carryTag) and not bool(s.done):
		var soul: Vector2 = v.arena_point(D.soul_world(s))
		var sway: float = sin(float(s.clock) * 0.15) * 2.0
		c.draw_line(soul + Vector2(3, 3), soul + Vector2(6 + sway, 9), CREAM, 1)
		_draw_tag(c, soul + Vector2(9 + sway, 11), 0.3, 1.0)
	# The note left at the other return (labelled outside the clip).
	for i: int in range(1, s.markers.size()):
		if bool(s.promised) and s.markers[i].get("noted", false):
			var o: Dictionary = s.objectives[i]
			var inward: float = -signf(float(o.x)) * 18.0
			v.text(c, v.box_point(Vector2(float(o.x) + inward, float(o.y) - 12.0)), "note left", LILAC, 80)
	# Plan telegraph at the right edge: pages waiting, the free elective in mint.
	for sweep: Dictionary in s.sweeps:
		if float(sweep.x) <= h.x + 8.0: continue
		var gy: float = float(sweep.gapY)
		var blink: float = 0.5 + 0.5 * sin(t * 0.4)
		var edge: float = h.x + 9.0
		c.draw_line(v.box_point(Vector2(edge, -h.y)), v.box_point(Vector2(edge, h.y)), Color(ROSE, 0.35 + 0.3 * blink), 2)
		c.draw_line(v.box_point(Vector2(edge, gy - 15.0)), v.box_point(Vector2(edge, gy + 15.0)), Color(MINT, 0.6 + 0.4 * blink), 3)
		v.chevron(c, v.box_point(Vector2(h.x - 5.0, gy)), Vector2.LEFT.rotated(float(s.box.rot)), Color(MINT, 0.6 + 0.4 * blink))
		v.chevron(c, v.box_point(Vector2(h.x - 11.0, gy)), Vector2.LEFT.rotated(float(s.box.rot)), Color(MINT, 0.4 + 0.4 * blink))
	if s.patternId == "take_a_number":
		var dispensers: Array[float] = [100.0]
		if int(s.phase) > 0: dispensers.append(-100.0)
		for dx: float in dispensers:
			var at: Vector2 = v.box_point(Vector2(dx, -h.y - 10.0))
			var lit: bool = s.has("serving") and t < int(s.serving.until) and absf(float(s.serving.x) - dx) < 1.0
			c.draw_rect(Rect2(at + Vector2(-12, -10), Vector2(24, 16)), TICKET_RED if lit and t % 8 < 5 else Color("5a2a3a"))
			c.draw_rect(Rect2(at + Vector2(-12, -10), Vector2(24, 16)), CREAM, false, 1)
			c.draw_rect(Rect2(at + Vector2(-6, 4), Vector2(12, 3)), INK)
		if s.has("serving") and t < int(s.serving.until) + 20:
			v.text(c, v.box_point(Vector2(0, -h.y - 2.0)) + Vector2(0, -24), "NEXT, SWEETIE: %d" % int(s.serving.number), AMBER, 200)
	if s.patternId == "advising_hold":
		for key: String in s.flash:
			var f: Dictionary = s.flash[key]
			if int(s.clock) >= int(f.until): continue
			var at2: Vector2 = v.box_point(Vector2(float(f.x), -h.y - 9.0))
			_draw_stamper(c, at2, 1.0)

## A rubber stamp hovering over the red column, base down.
static func _draw_stamper(c: CanvasItem, at: Vector2, alpha: float) -> void:
	var wood: Color = Color(Color("8a5a3c"), alpha)
	c.draw_circle(at + Vector2(0, -12), 3.0, wood)
	c.draw_rect(Rect2(at + Vector2(-1.5, -10), Vector2(3, 7)), wood)
	c.draw_rect(Rect2(at + Vector2(-6, -3), Vector2(12, 5)), Color(TICKET_RED, alpha))
	c.draw_rect(Rect2(at + Vector2(-6, -3), Vector2(12, 5)), Color(CREAM, alpha), false, 1)

## A sticky note (the old clapping hand): pale yellow, a curled corner and a scribbled "see me".
static func _draw_sticky(c: CanvasItem, at: Vector2, turn: float, alpha: float) -> void:
	c.draw_colored_polygon(PackedVector2Array([_pt(at, turn, -9, -6.5), _pt(at, turn, 9, -6.5), _pt(at, turn, 9, 3.5), _pt(at, turn, 5.5, 6.5), _pt(at, turn, -9, 6.5)]), Color(STICKY, alpha))
	c.draw_colored_polygon(PackedVector2Array([_pt(at, turn, 9, 3.5), _pt(at, turn, 5.5, 6.5), _pt(at, turn, 5.5, 3.5)]), Color(Color("c8a850"), alpha))
	c.draw_line(_pt(at, turn, -9, -4.5), _pt(at, turn, 9, -4.5), Color(Color("d8bc58"), alpha), 1)
	c.draw_line(_pt(at, turn, -6, -1.5), _pt(at, turn, 5, -1.5), Color(Color("8a6a3c"), alpha), 1)
	c.draw_line(_pt(at, turn, -6, 1.2), _pt(at, turn, 1, 1.2), Color(Color("8a6a3c"), alpha), 1)
	c.draw_line(_pt(at, turn, -6, 3.8), _pt(at, turn, -1, 3.8), Color(TICKET_RED, alpha), 1)
	c.draw_polyline(PackedVector2Array([_pt(at, turn, -9, -6.5), _pt(at, turn, 9, -6.5), _pt(at, turn, 9, 3.5), _pt(at, turn, 5.5, 6.5), _pt(at, turn, -9, 6.5), _pt(at, turn, -9, -6.5)]), Color(INK, 0.45 * alpha), 1)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"plan_page":
			# One page of the four-year plan: a tinted semester header and three lines of fine print.
			var tint: Color = TINTS[int(b.get("hue", 0)) % TINTS.size()]
			c.draw_colored_polygon(v.quad(at, 6.0, 6.5, turn), Color(PARCH, alpha))
			c.draw_colored_polygon(v.quad(_pt(at, turn, 0, -4.8), 6.0, 1.7, turn), Color(tint, alpha))
			for k: int in range(3):
				c.draw_line(_pt(at, turn, -4, -0.8 + k * 2.6), _pt(at, turn, 4 - k * 1.5, -0.8 + k * 2.6), Color(INK, 0.55 * alpha), 1)
			c.draw_polyline(v.quad(at, 6.0, 6.5, turn) + PackedVector2Array([v.quad(at, 6.0, 6.5, turn)[0]]), Color(CREAM, 0.6 * alpha), 1)
			return true
		"audit_card":
			# A degree audit card: tinted header, two requirement lines and a checkbox. The card about
			# to be flung shows an unchecked red box and shakes.
			var tint2: Color = TINTS[int(b.get("hue", 0)) % TINTS.size()]
			var flagged: bool = b.has("shake")
			var shake: Vector2 = Vector2.ZERO
			if flagged and b.has("belt"):
				shake = Vector2(sin(float(b.age) * 1.9), cos(float(b.age) * 2.3)) * 1.5
			var base: Vector2 = at + shake
			var hw: float = float(b.w)
			var hh: float = float(b.h)
			var q: PackedVector2Array = v.quad(base, hw, hh, turn)
			c.draw_colored_polygon(q, Color(PARCH, alpha))
			c.draw_colored_polygon(v.quad(_pt(base, turn, 0, -hh + 1.5), hw, 1.5, turn), Color(tint2, alpha))
			c.draw_line(_pt(base, turn, -1.0, 0.0), _pt(base, turn, hw - 1.5, 0.0), Color(INK, 0.6 * alpha), 1)
			c.draw_line(_pt(base, turn, -1.0, 2.6), _pt(base, turn, hw - 3.5, 2.6), Color(INK, 0.6 * alpha), 1)
			var box_at: Vector2 = _pt(base, turn, -hw + 3.4, 1.3)
			var bq: PackedVector2Array = v.quad(box_at, 1.5, 1.5, turn)
			c.draw_polyline(bq + PackedVector2Array([bq[0]]), Color(ROSE if flagged else TEAL, alpha), 1)
			if flagged:
				c.draw_line(_pt(box_at, turn, -1.2, -1.2), _pt(box_at, turn, 1.2, 1.2), Color(ROSE, alpha), 1)
				c.draw_line(_pt(box_at, turn, 1.2, -1.2), _pt(box_at, turn, -1.2, 1.2), Color(ROSE, alpha), 1)
			else:
				c.draw_polyline(PackedVector2Array([_pt(box_at, turn, -1.0, 0.0), _pt(box_at, turn, -0.2, 1.0), _pt(box_at, turn, 1.4, -1.4)]), Color(TEAL, alpha), 1)
			c.draw_polyline(q + PackedVector2Array([q[0]]), Color(ROSE if flagged else CREAM, alpha), 1)
			return true
		"ticket":
			# A take-a-number ticket: red body, perforation and a printed number.
			var q2: PackedVector2Array = v.quad(at, 5.0, 3.5, turn)
			c.draw_colored_polygon(q2, Color(TICKET_RED, alpha))
			c.draw_line(_pt(at, turn, -2, -3.5), _pt(at, turn, -2, 3.5), Color(CREAM, 0.85 * alpha), 1)
			c.draw_line(_pt(at, turn, 0.5, -1), _pt(at, turn, 3.5, -1), Color(CREAM, alpha), 1)
			c.draw_line(_pt(at, turn, 0.5, 1), _pt(at, turn, 2.5, 1), Color(CREAM, alpha), 1)
			c.draw_polyline(q2 + PackedVector2Array([q2[0]]), Color(Color("f2ede0"), 0.55 * alpha), 1)
			return true
		"syllabus":
			# A rolled syllabus: parchment tube, wooden ends and a red ribbon. It shakes before it opens.
			var shake2: float = 0.0
			if b.has("popAt") and int(b.age) > int(b.popAt) - 20: shake2 = sin(float(b.age) * 1.6) * 0.25
			var tt: float = turn + shake2
			c.draw_colored_polygon(v.quad(at, 2.6, 7.5, tt), Color(PARCH, alpha))
			c.draw_colored_polygon(v.quad(_pt(at, tt, 0, -8.2), 3.4, 1.0, tt), Color(Color("8a5a3c"), alpha))
			c.draw_colored_polygon(v.quad(_pt(at, tt, 0, 8.2), 3.4, 1.0, tt), Color(Color("8a5a3c"), alpha))
			c.draw_colored_polygon(v.quad(_pt(at, tt, 0, -1.5), 2.9, 1.1, tt), Color(TICKET_RED, alpha))
			c.draw_line(_pt(at, tt, -1.2, 2.5), _pt(at, tt, 1.2, 2.5), Color(INK, 0.5 * alpha), 1)
			c.draw_line(_pt(at, tt, -1.2, 4.5), _pt(at, tt, 0.8, 4.5), Color(INK, 0.5 * alpha), 1)
			if shake2 != 0.0: c.draw_arc(at, 11.0, 0, TAU, 14, Color(ROSE, 0.5 * alpha), 1)
			return true
		"unrolled":
			# The syllabus opened flat: a long page of due dates, curling at both ends.
			c.draw_colored_polygon(v.quad(at, 11.0, 6.5, turn), Color(PARCH, 0.75 * alpha))
			for k: int in range(4):
				c.draw_line(_pt(at, turn, -8, -4.2 + k * 2.8), _pt(at, turn, 8 - k * 2.0, -4.2 + k * 2.8), Color(INK, 0.4 * alpha), 1)
			c.draw_line(_pt(at, turn, -11, -6.5), _pt(at, turn, -11, 6.5), Color(Color("8a5a3c"), alpha), 2)
			c.draw_line(_pt(at, turn, 11, -6.5), _pt(at, turn, 11, 6.5), Color(Color("8a5a3c"), alpha), 2)
			return true
		"due_date":
			# A due date: a little calendar square with a red edge.
			var dq: PackedVector2Array = v.quad(at, 2.4, 2.4, turn)
			c.draw_colored_polygon(dq, Color(PARCH, alpha))
			c.draw_polyline(dq + PackedVector2Array([dq[0]]), Color(ROSE, alpha), 1)
			c.draw_line(_pt(at, turn, -1.2, -0.4), _pt(at, turn, 1.2, -0.4), Color(INK, 0.6 * alpha), 1)
			return true
		"sticky":
			_draw_sticky(c, at, turn, alpha)
			return true
		"hold_stamp":
			# ADVISING HOLD: a red block with a cream border and a struck-through account line.
			c.draw_rect(Rect2(at - Vector2(6, 4), Vector2(12, 8)), Color(TICKET_RED, alpha))
			c.draw_rect(Rect2(at - Vector2(6, 4), Vector2(12, 8)), Color(CREAM, alpha), false, 1)
			c.draw_line(at + Vector2(-3.5, -1.5), at + Vector2(3.5, -1.5), Color(CREAM, alpha), 1)
			c.draw_line(at + Vector2(-3.5, 1.5), at + Vector2(3.5, 1.5), Color(CREAM, alpha), 1)
			return true
		"index_card":
			# An index card on the Rolodex ring: cream, a red top rule and a teal tab line.
			var cq: PackedVector2Array = v.quad(at, 6.0, 2.5, turn)
			c.draw_colored_polygon(cq, Color(PARCH, alpha))
			c.draw_line(_pt(at, turn, -6, -1.3), _pt(at, turn, 6, -1.3), Color(TICKET_RED, alpha), 1)
			c.draw_line(_pt(at, turn, -5, 0.9), _pt(at, turn, 3, 0.9), Color(TEAL, 0.8 * alpha), 1)
			c.draw_polyline(cq + PackedVector2Array([cq[0]]), Color(CREAM, 0.7 * alpha), 1)
			if b.has("detachAt"): c.draw_arc(at, 8.0, 0, TAU, 12, Color(ROSE, 0.6 * alpha), 1)
			return true
		"rolodex_hub":
			c.draw_circle(at, 7.0, Color(Color("4a2f3a"), alpha))
			c.draw_arc(at, 7.0, 0, TAU, 16, Color(AMBER, alpha), 1)
			for k: int in range(8):
				var a2: float = k * PI * 0.25 + float(v.pattern.clock) * 0.01
				c.draw_line(at + Vector2.from_angle(a2) * 3.5, at + Vector2.from_angle(a2) * 9.0, Color(PARCH, alpha), 1)
			c.draw_circle(at, 2.0, Color(AMBER, alpha))
			return true
		"pencil":
			# A sharpened pencil, tumbling: yellow barrel, wood tip, graphite point, eraser and band.
			c.draw_colored_polygon(v.quad(at, 4.5, 1.5, turn), Color(Color("e8c040"), alpha))
			c.draw_colored_polygon(PackedVector2Array([_pt(at, turn, 4.5, -1.5), _pt(at, turn, 7.5, 0), _pt(at, turn, 4.5, 1.5)]), Color(PARCH, alpha))
			c.draw_line(_pt(at, turn, 6.6, 0), _pt(at, turn, 7.8, 0), Color(INK, alpha), 1)
			c.draw_colored_polygon(v.quad(_pt(at, turn, -5.8, 0), 1.3, 1.5, turn), Color(ROSE, alpha))
			c.draw_line(_pt(at, turn, -4.4, -1.5), _pt(at, turn, -4.4, 1.5), Color(CREAM, alpha), 1)
			return true
	return false
