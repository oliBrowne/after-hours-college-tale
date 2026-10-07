extends RefCounted
## TODD / Stamp Audit: the finite-plan desk in Old Main. Red soul inside a
## circular arena (drawn and enforced here) that shrinks through each cycle.
## Three RED AUDITs a turn: each is announced 45 ticks ahead (banner, beeps,
## red countdown), lasts 45 ticks, sets s.audit (the engine then hurts any
## movement input) and freezes every threat in place. When it ends, anything
## frozen right next to the soul is filed away, the rest resumes.
## Promise: sign both consent boxes (confirm inside each). They count even
## without a promise (free = true), as in the old encounter.
## Five handmade attacks, one per turn, cycling. Stage 1 and 2 add a layer.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["stamp_sector", "red_tape", "sign_here", "take_a_number", "approval_grid"]
const PHASES: Array[int] = [0, 1, 2]
const AUDITS: Array[int] = [125, 275, 425]
const AUDIT_LEN: int = 45
const AUDIT_TELL: int = 45
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const ROSE: Color = Color("e8837b")
const LILAC: Color = Color("a68db8")
const INKBLUE: Color = Color("3d4a8a")
const DESK: Color = Color("2a2030")
const RED: Color = Color("c8404a")

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 540
	s.consentCount = 0
	s.audit = false
	s.radius0 = 60.0 - 4.0 * clampi(int(s.phase), 0, 2)
	s.radius = float(s.radius0)
	s.shrink = 10.0
	s.sectors = []
	s.pens = []
	s.cells = []
	s.auditTell = -1
	var boxes: Array = [Vector2(-32, 0), Vector2(32, 0)]
	match id:
		"stamp_sector":
			s.phaseName = "Rotating Stamp"
			s.hint = "The stamp sweeps the circle. Walk ahead of it and confirm in both consent boxes."
		"red_tape":
			s.phaseName = "Red Tape"
			s.hint = "Tape is strung across the circle where it's dashed. Stay in a clear cell."
			boxes = [Vector2(-28, -22), Vector2(28, 22)]
		"sign_here":
			s.phaseName = "Sign Here"
			s.hint = "The pen follows you and its ink stays wet. Lead it around; sign both boxes."
			boxes = [Vector2(-34, 14), Vector2(34, -14)]
		"take_a_number":
			s.phaseName = "Take a Number"
			s.hint = "Rings of forms close in. Slip through each ring's gap as it passes."
			boxes = [Vector2(0, -30), Vector2(0, 30)]
			s.shrink = 6.0
		"approval_grid":
			s.phaseName = "Approval Process"
			s.hint = "Marked cells get stamped on the beat. Step into an unmarked cell."
			boxes = [Vector2(-24, -24), Vector2(24, 24)]
			s.shrink = 10.0
	for p: Vector2 in boxes:
		D.objective(s, {"kind": "confirm", "x": p.x, "y": p.y, "w": 9.0, "h": 9.0, "label": "SIGN", "always": true, "free": true})

# ---------------------------------------------------------------- arena and audits

static func _audit_phase(t: int) -> Dictionary:
	for at: int in AUDITS:
		if t >= at - AUDIT_TELL and t < at: return {"state": "tell", "at": at, "left": at - t}
		if t >= at and t < at + AUDIT_LEN: return {"state": "audit", "at": at, "left": at + AUDIT_LEN - t}
	return {"state": "free"}

## Ticks until the next audit begins (large if none left).
static func _until_audit(t: int) -> int:
	for at: int in AUDITS:
		if t < at: return at - t
	return 9999

static func _arena(s: Dictionary, t: int) -> void:
	# The circle closes in through each cycle, then relaxes after the audit.
	var start: int = 0
	var finish: int = AUDITS[0]
	for i: int in range(AUDITS.size()):
		if t >= AUDITS[i]:
			start = AUDITS[i] + AUDIT_LEN
			finish = AUDITS[i + 1] if i + 1 < AUDITS.size() else 500
	var target: float = float(s.radius0)
	if t >= start:
		target = float(s.radius0) - float(s.shrink) * clampf(float(t - start) / float(maxi(1, finish - start)), 0.0, 1.0)
	else:
		target = float(s.radius0) - float(s.shrink)
	if _audit_phase(t).state == "audit": target = float(s.radius)
	s.radius = move_toward(float(s.radius), target, 0.8)

static func _clamp_soul(s: Dictionary) -> void:
	var p: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var limit: float = float(s.radius) - 4.0
	if p.length() > limit:
		p = p.normalized() * limit
		s.soul.x = p.x; s.soul.y = p.y

static func _audits(s: Dictionary, t: int) -> void:
	var a: Dictionary = _audit_phase(t)
	match str(a.state):
		"tell":
			if int(a.left) == AUDIT_TELL:
				D.banner(s, "RED AUDIT INCOMING", AUDIT_TELL)
				s.bannerColor = ROSE
				D.warn(s, {"kind": "audit_tell"}, AUDIT_TELL, true)
			if int(a.left) == 30 or int(a.left) == 15: D.warn(s, {"kind": "audit_tick"}, 4, true)
			s.audit = false
		"audit":
			if int(a.left) == AUDIT_LEN:
				_freeze(s, AUDIT_LEN)
				D.banner(s, "RED AUDIT / HOLD STILL", AUDIT_LEN)
				s.bannerColor = RED
			s.audit = true
			if int(a.left) == 1: _thaw(s)
		_:
			s.audit = false

## Freeze every bullet where it is: no movement and no collision until the
## audit is over; lifetimes are extended by the same amount.
static func _freeze(s: Dictionary, ticks: int) -> void:
	for b: Dictionary in s.bullets:
		if b.has("fade") or b.get("frozen", false): continue
		b.frozen = true
		b.hadHold = b.has("hold")
		if b.has("orbit"):
			b.saved = {"av": float(b.orbit.get("av", 0.0)), "dr": float(b.orbit.get("dr", 0.0))}
			b.orbit.av = 0.0; b.orbit.dr = 0.0
		elif b.collide == "ring":
			b.saved = {"grow": float(b.grow)}
			b.grow = 0.0
		else:
			b.hold = true
		b.arm = maxi(int(b.arm), int(b.age) + ticks)
		b.life = int(b.life) + ticks

## Resume. Anything frozen within reach of the soul is filed away instead, so
## nothing can hit a player who was holding still.
static func _thaw(s: Dictionary) -> void:
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	for b: Dictionary in s.bullets:
		if not b.get("frozen", false): continue
		b.frozen = false
		if b.has("saved"):
			var sv: Dictionary = b.saved
			if b.has("orbit"):
				b.orbit.av = float(sv.av); b.orbit.dr = float(sv.dr)
			else:
				b.grow = float(sv.grow)
			b.erase("saved")
		if not bool(b.hadHold): b.erase("hold")
		if b.shape == "pen": continue
		if D.clearance(s, b, soul if b.space == "box" else D.soul_world(s)) < 16.0:
			b.fade = 16
			D.effect(s, "block", D.bullet_world(s, b), 14)

# ---------------------------------------------------------------- contract

static func confirm(_s: Dictionary) -> void:
	pass

static func promise_complete(s: Dictionary) -> bool:
	return int(s.consentCount) >= 2

static func progress(s: Dictionary) -> String:
	return "Consent boxes %d/2%s" % [mini(2, int(s.consentCount)), " / HOLD STILL" if bool(s.get("audit", false)) else ""]

static func tick(s: Dictionary, t: int) -> void:
	if t == 0: D.box_to(s, {"w": 128.0, "h": 128.0}, 20)
	_audits(s, t)
	_arena(s, t)
	_clamp_soul(s)
	var phase: int = clampi(int(s.phase), 0, 2)
	var frozen: bool = bool(s.audit)
	match str(s.patternId):
		"stamp_sector": _stamp_sector(s, t, phase, frozen)
		"red_tape":
			_red_tape(s, t, phase, frozen)
			_tape_motion(s)
		"sign_here": _sign_here(s, t, phase, frozen)
		"take_a_number": _take_a_number(s, t, phase, frozen)
		"approval_grid": _approval_grid(s, t, phase, frozen)
	_sectors(s, frozen)
	# QA autopilot hint: during an audit, stay exactly where you are.
	s.botGoal = Vector2(float(s.soul.x), float(s.soul.y)) if frozen else null

static func after(s: Dictionary, t: int) -> void:
	if t < 0 or int(s.clock) >= int(s.duration) - 40:
		s.audit = false
	_clamp_soul(s)
	var count: int = 0
	for o: Dictionary in s.objectives:
		if o.done: count += 1
	s.consentCount = count

## Spawn guard: nothing new in the last stretch before an audit or during it.
static func _quiet(t: int, margin: int = 20) -> bool:
	var a: Dictionary = _audit_phase(t)
	return a.state == "audit" or (a.state == "tell" and int(a.left) <= margin)

# ---------------------------------------------------------------- stamp sectors (shared)

static func _sector(s: Dictionary, angle: float, arc: float, av: float, warn: int) -> void:
	s.sectors.append({"angle": angle, "arc": arc, "av": av, "age": 0, "warn": warn, "inner": 12.0})

static func _sectors(s: Dictionary, frozen: bool) -> void:
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	for sec: Dictionary in s.sectors:
		if frozen: continue
		sec.age = int(sec.age) + 1
		if int(sec.age) > int(sec.warn): sec.angle = wrapf(float(sec.angle) + float(sec.av), -PI, PI)
		if int(sec.age) <= int(sec.warn): continue
		var r: float = soul.length()
		if r < float(sec.inner) - 3.0: continue
		var slack: float = 3.0 / maxf(r, 6.0)
		if absf(wrapf(soul.angle() - float(sec.angle), -PI, PI)) <= float(sec.arc) + slack:
			D.hurt(s, D.soul_world(s))

# ---------------------------------------------------------------- 1. Rotating Stamp

# A giant stamp sweeps the circle like a clock hand; the hub in the middle is
# out of its reach, but DENIED stamps slam down wherever you stand (a shrinking
# shadow is the tell). Stage 1: a second stamp opposite. Stage 2: after each
# audit the stamps sweep the other way, faster.
static func _stamp_sector(s: Dictionary, t: int, phase: int, frozen: bool) -> void:
	if t == 0:
		var a0: float = D.rand(s) * TAU
		_sector(s, a0, 0.5, 0.014, 40)
		if phase >= 1: _sector(s, a0 + PI, 0.4, 0.014, 40)
	if phase >= 2:
		for at: int in AUDITS:
			if t == at + AUDIT_LEN:
				for sec: Dictionary in s.sectors: sec.av = -float(sec.av) * 1.15
	if frozen or _quiet(t) or t < 40: return
	if t % 48 == 0 and t < 480:
		_stamp(s, Vector2(float(s.soul.x), float(s.soul.y)), 36, 9.0)
	# Ink spatters fly out along the stamp's leading edge, ahead of its sweep.
	if t % (30 if phase == 0 else 20) == 10 and t < 480:
		for sec: Dictionary in s.sectors:
			if int(sec.age) <= int(sec.warn): continue
			var lead: float = float(sec.angle) + (float(sec.arc) + 0.25) * signf(float(sec.av))
			var dir: Vector2 = Vector2.from_angle(lead)
			D.shot(s, {"space": "box", "x": dir.x * 14.0, "y": dir.y * 14.0, "vx": dir.x * 1.3, "vy": dir.y * 1.3, "r": 3.0, "shape": "ink", "life": 70})

static func _stamp(s: Dictionary, at: Vector2, warn: int, r: float) -> void:
	D.shot(s, {"space": "box", "x": at.x, "y": at.y, "r": r, "hold": true, "arm": warn, "life": warn + 10, "shape": "stamp", "warnTicks": warn})

# ---------------------------------------------------------------- 2. Red Tape

# Red tape is strung across the circle as chords. Each is a dashed line first,
# then pulled tight for a while. Chords pile up and split the circle into
# cells, never across an unsigned consent box. Stage 1: some tapes slide
# sideways while tight. Stage 2: some tapes turn slowly around their middle.
static func _red_tape(s: Dictionary, t: int, phase: int, frozen: bool) -> void:
	if frozen or _quiet(t, 44) or t < 10 or t > 470: return
	if t % 30 != 10: return
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	for attempt: int in range(8):
		var angle: float = D.rand(s) * PI
		var normal: Vector2 = Vector2.from_angle(angle + PI * 0.5)
		# Pass near the soul so it has to step aside.
		var offset: float = soul.dot(normal) + D.rand_range(s, -5.0, 5.0)
		var mid: Vector2 = normal * clampf(offset, -40.0, 40.0)
		var dir: Vector2 = Vector2.from_angle(angle)
		var ok: bool = true
		for o: Dictionary in s.objectives:
			if o.done: continue
			var p: Vector2 = Vector2(float(o.x), float(o.y))
			if absf((p - mid).dot(normal)) < 16.0: ok = false
		if not ok: continue
		var half_len: float = sqrt(maxf(1.0, 70.0 * 70.0 - mid.length_squared()))
		var b: Dictionary = {"space": "box", "x": mid.x, "y": mid.y, "collide": "rect", "w": half_len, "h": 2.0, "rot": angle, "arm": 40, "hold": true,
			"life": 40 + 130, "shape": "tape"}
		if phase >= 1 and attempt % 2 == 0:
			b.slide = normal * (0.12 if D.rand(s) < 0.5 else -0.12)
		if phase >= 2 and attempt % 3 == 1:
			b.turn = 0.004 if D.rand(s) < 0.5 else -0.004
		D.shot(s, b)
		return

static func _tape_motion(s: Dictionary) -> void:
	if bool(s.audit): return
	for b: Dictionary in s.bullets:
		if b.shape != "tape" or int(b.age) <= int(b.arm): continue
		if b.has("slide"):
			var v: Vector2 = b.slide
			b.x = float(b.x) + v.x; b.y = float(b.y) + v.y
		if b.has("turn"): b.rot = float(b.rot) + float(b.turn)

# ---------------------------------------------------------------- 3. Sign Here

# A fountain pen chases you and writes as it goes; the ink stays wet (and
# harmful) for a while, so lead it in loops. Every few seconds it lifts to dot
# an i: a blot lands where you are. Stage 1: blots splash. Stage 2: a second pen.
static func _sign_here(s: Dictionary, t: int, phase: int, frozen: bool) -> void:
	if t == 0:
		_pen(s, Vector2(0, -float(s.radius0) + 8.0), Vector2(1, 0))
	if phase >= 2 and t == 160: _pen(s, Vector2(0, float(s.radius0) - 8.0), Vector2(-1, 0))
	if frozen: return
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	for pen: Dictionary in s.pens:
		var nib: Dictionary = pen.nib
		pen.age = int(pen.age) + 1
		if int(pen.age) < 40: continue
		var at: Vector2 = Vector2(float(nib.x), float(nib.y))
		var vel: Vector2 = pen.vel
		var want: Vector2 = (soul - at).normalized() * (1.05 + 0.1 * phase)
		vel = vel.lerp(want, 0.045)
		if vel.length() > 0.01: vel = vel.normalized() * (1.05 + 0.1 * phase)
		at += vel
		if at.length() > float(s.radius) - 4.0: at = at.normalized() * (float(s.radius) - 4.0)
		nib.x = at.x; nib.y = at.y; nib.rot = vel.angle()
		pen.vel = vel
		if int(pen.age) % 3 == 0:
			D.shot(s, {"space": "box", "x": at.x, "y": at.y, "r": 2.6, "arm": 8, "life": 120, "shape": "ink"})
	if _quiet(t) or t < 60: return
	if t % 50 == 35 and t < 470:
		_stamp(s, soul, 36, 8.0)
		s.blots = s.get("blots", [])
		if phase >= 1: s.blots.append({"at": t + 39, "x": soul.x, "y": soul.y})
	var keep: Array = []
	for bl: Dictionary in s.get("blots", []):
		if int(bl.at) == t:
			for i: int in range(6):
				var a: float = i * TAU / 6.0 + 0.3
				D.shot(s, {"space": "box", "x": float(bl.x), "y": float(bl.y), "vx": cos(a) * 1.3, "vy": sin(a) * 1.3, "drag": 0.97, "r": 2.4, "life": 70, "shape": "ink"})
		elif int(bl.at) > t: keep.append(bl)
	s.blots = keep

static func _pen(s: Dictionary, at: Vector2, vel: Vector2) -> void:
	var nib: Dictionary = D.shot(s, {"space": "box", "x": at.x, "y": at.y, "r": 4.0, "arm": 40, "life": 2000, "shape": "pen", "hold": true})
	s.pens.append({"nib": nib, "vel": vel, "age": 0})
	D.warn(s, {"kind": "cue", "space": "box", "x": at.x, "y": at.y}, 40, true)

# ---------------------------------------------------------------- 4. Take a Number

# Rings of forms queue around the circle and close in, each with one gap,
# turning as they come. Slip through each ring's gap as it passes you; the
# middle is no hiding place. Stage 1: rings alternate direction. Stage 2:
# double rings with offset gaps.
static func _take_a_number(s: Dictionary, t: int, phase: int, frozen: bool) -> void:
	if frozen or _quiet(t, 30) or t > 450: return
	var every: int = 70 if phase == 0 else 60
	if t % every != 5: return
	var k: int = int(t / every)
	var dir: float = 1.0 if phase == 0 or k % 2 == 0 else -1.0
	var gap: float = D.rand(s) * TAU
	_queue_ring(s, gap, dir, float(s.radius0) + 10.0)
	if phase >= 2 and k % 2 == 1:
		_queue_ring(s, gap + PI * 0.75, dir, float(s.radius0) + 28.0)
	D.banner(s, "NOW SERVING %d" % (k + 1), 30)

static func _queue_ring(s: Dictionary, gap: float, dir: float, radius: float) -> void:
	var c: Vector2 = D.centre(s)
	var count: int = 18
	for i: int in range(count):
		var a: float = gap + float(i) * TAU / float(count)
		if i == 0 or i == 1 or i == count - 1: continue
		D.shot(s, {"orbit": {"ox": c.x, "oy": c.y, "radius": radius, "angle": a, "av": 0.006 * dir, "dr": -0.42, "minRadius": 1.0},
			"r": 3.5, "shape": "form", "rot": a + PI * 0.5, "spin": 0.006 * dir, "life": 400})

# ---------------------------------------------------------------- 5. Approval Process

# The circle is ruled into a 3x3 grid. On the beat, a pattern of cells is
# marked (checkerboard, cross, ring, rows), then stamped APPROVED a beat and a
# half later. The circle closes in harder here. Stage 1: the rotating stamp
# joins in. Stage 2: the grid is turned 45 degrees.
const GRID_PATTERNS: Array = [
	[0, 2, 4, 6, 8], [1, 3, 5, 7], [0, 1, 2, 3, 5, 6, 7, 8], [0, 1, 2, 6, 7, 8], [0, 3, 6, 2, 5, 8], [0, 2, 6, 8, 4],
]

static func _approval_grid(s: Dictionary, t: int, phase: int, frozen: bool) -> void:
	if t == 0 and phase >= 1:
		_sector(s, D.rand(s) * TAU, 0.32, 0.011, 50)
	if frozen or _quiet(t, 46) or t < 20 or t > 460: return
	if t % 45 != 20: return
	var k: int = int(t / 45)
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var turn: float = PI * 0.25 if phase >= 2 else 0.0
	var size: float = 34.0
	# Pick a pattern that covers the soul's cell, so standing still is wrong.
	var local: Vector2 = soul.rotated(-turn)
	var col: int = clampi(int(floor((local.x + size * 1.5) / size)), 0, 2)
	var row: int = clampi(int(floor((local.y + size * 1.5) / size)), 0, 2)
	var here: int = row * 3 + col
	var pick: Array = GRID_PATTERNS[k % GRID_PATTERNS.size()]
	for j: int in range(GRID_PATTERNS.size()):
		var cand: Array = GRID_PATTERNS[(k + j) % GRID_PATTERNS.size()]
		if cand.has(here):
			pick = cand
			break
	for cell: int in pick:
		var cx: float = (float(cell % 3) - 1.0) * size
		var cy: float = (float(int(cell / 3)) - 1.0) * size
		var p: Vector2 = Vector2(cx, cy).rotated(turn)
		D.shot(s, {"space": "box", "x": p.x, "y": p.y, "collide": "rect", "w": size * 0.5 - 1.0, "h": size * 0.5 - 1.0, "rot": turn, "hold": true, "arm": 44, "life": 54,
			"shape": "cell", "warnTicks": 44})

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var centre: Vector2 = v.box_point(Vector2.ZERO)
	var r: float = float(s.radius)
	# The desk outside the circle.
	c.draw_arc(centre, r + 60.0, 0, TAU, 64, DESK, 120.0)
	for i: int in range(6):
		c.draw_line(v.box_point(Vector2(-70, -60 + i * 24)), v.box_point(Vector2(70, -60 + i * 24)), Color(0.35, 0.25, 0.3, 0.25), 1)
	# Form lines on the paper inside.
	for i: int in range(-4, 5):
		var y: float = i * 12.0
		if absf(y) >= r - 2.0: continue
		var half: float = sqrt(r * r - y * y) - 3.0
		c.draw_line(v.box_point(Vector2(-half, y)), v.box_point(Vector2(half, y)), Color(0.55, 0.6, 0.8, 0.06), 1)
	var audit: bool = bool(s.get("audit", false))
	c.draw_arc(centre, r, 0, TAU, 64, RED if audit else Color("8f779e"), 2)
	if audit: c.draw_circle(centre, r, Color(0.8, 0.15, 0.2, 0.08))
	# Stamp sectors.
	for sec: Dictionary in s.sectors:
		var live: bool = int(sec.age) > int(sec.warn)
		var pts: PackedVector2Array = []
		var a0: float = float(sec.angle) - float(sec.arc)
		var a1: float = float(sec.angle) + float(sec.arc)
		for i: int in range(9):
			var a: float = lerpf(a0, a1, float(i) / 8.0)
			pts.append(v.box_point(Vector2.from_angle(a) * float(sec.inner)))
		for i: int in range(9):
			var a2: float = lerpf(a1, a0, float(i) / 8.0)
			pts.append(v.box_point(Vector2.from_angle(a2) * (r - 1.0)))
		if live:
			c.draw_colored_polygon(pts, Color(Color("b06470"), 0.75 if not audit else 0.4))
			var mid: Vector2 = v.box_point(Vector2.from_angle(float(sec.angle)) * (r * 0.62))
			v.text(c, mid + Vector2(0, 4), "DENIED", Color(Color("f0c0c0"), 0.9), 60.0)
		else:
			c.draw_polyline(pts + PackedVector2Array([pts[0]]), Color(ROSE, 0.4 + 0.4 * sin(float(sec.age) * 0.4)), 1)
	# Telegraphs for tape and grid cells.
	for b: Dictionary in s.bullets:
		var warn_ticks: int = int(b.get("warnTicks", b.get("arm", 0)))
		if int(b.age) > int(b.arm) or b.get("frozen", false): continue
		var p: float = clampf(float(b.age) / float(maxi(1, warn_ticks)), 0.0, 1.0)
		if b.shape == "tape":
			var dir: Vector2 = Vector2.from_angle(float(b.rot))
			var mid2: Vector2 = Vector2(float(b.x), float(b.y))
			var x: float = -float(b.w)
			while x < float(b.w):
				c.draw_line(v.box_point(mid2 + dir * x), v.box_point(mid2 + dir * minf(x + 5.0, float(b.w))), Color(ROSE, 0.35 + 0.55 * p), 1)
				x += 10.0
		elif b.shape == "cell":
			var poly: PackedVector2Array = v.quad(v.box_point(Vector2(float(b.x), float(b.y))), float(b.w), float(b.h), float(b.rot))
			c.draw_colored_polygon(poly, Color(ROSE, 0.06 + 0.16 * p))
			c.draw_polyline(poly + PackedVector2Array([poly[0]]), Color(ROSE, 0.4 + 0.5 * p), 1)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var t: int = int(s.clock) - int(s.leadIn)
	var a: Dictionary = _audit_phase(t)
	var h: Vector2 = D.half(s)
	if a.state == "tell" and t < int(s.length) - 40:
		# Countdown pips above the box: three, emptying.
		var left: int = int(a.left)
		var top: Vector2 = v.box_point(Vector2(0, -h.y - 18.0))
		for i: int in range(3):
			var lit: bool = left > i * 15
			c.draw_circle(top + Vector2(-12 + i * 12, 0), 3.5, RED if lit else Color(RED, 0.25))
		var pulse: float = 0.5 + 0.5 * sin(float(t) * 0.6)
		var pts: PackedVector2Array = D.corners(s, 3.0)
		for i: int in range(pts.size()): pts[i] = v.arena_point(pts[i])
		pts.append(pts[0])
		c.draw_polyline(pts, Color(RED, 0.3 + 0.5 * pulse), 1)
	if bool(s.get("audit", false)):
		var pts2: PackedVector2Array = D.corners(s, 4.0)
		for i: int in range(pts2.size()): pts2[i] = v.arena_point(pts2[i])
		pts2.append(pts2[0])
		c.draw_polyline(pts2, RED, 3)
		# The audit stamp hovering over the box.
		var at: Vector2 = v.box_point(Vector2(h.x + 18.0, -h.y + 10.0))
		c.draw_rect(Rect2(at + Vector2(-8, -4), Vector2(16, 8)), RED)
		c.draw_rect(Rect2(at + Vector2(-3, -14), Vector2(6, 10)), Color("5a3a2a"))
	# Todd's rubber stamp rig sits at the right of the desk.
	var rig: Vector2 = v.box_point(Vector2(h.x + 16.0, h.y - 14.0))
	c.draw_rect(Rect2(rig + Vector2(-7, -3), Vector2(14, 6)), Color("5a3a2a"))
	c.draw_rect(Rect2(rig + Vector2(-5, 3), Vector2(10, 3)), RED)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	var frozen: bool = b.get("frozen", false)
	match str(b.shape):
		"stamp":
			var warn_ticks: int = int(b.get("warnTicks", 30))
			if int(b.age) <= int(b.arm) and not frozen:
				var p: float = clampf(float(b.age) / float(warn_ticks), 0.0, 1.0)
				c.draw_arc(at, float(b.r) + 14.0 * (1.0 - p), 0, TAU, 20, Color(RED, 0.4 + 0.5 * p), 1)
				c.draw_circle(at, float(b.r) * p, Color(0, 0, 0, 0.3))
				return true
			var r: float = float(b.r)
			c.draw_rect(Rect2(at - Vector2(r, r), Vector2(r, r) * 2.0), Color(RED, 0.85 * alpha))
			c.draw_rect(Rect2(at - Vector2(r - 2.0, r - 2.0), Vector2(r - 2.0, r - 2.0) * 2.0), Color(Color("f0c0c0"), alpha), false, 1)
			return true
		"tape":
			if int(b.age) <= int(b.arm) and not frozen: return true
			var dir: Vector2 = Vector2.from_angle(turn)
			var col: Color = Color(RED, alpha) if not frozen else Color(Color("9a5a60"), alpha)
			c.draw_line(at - dir * float(b.w), at + dir * float(b.w), col, 4.0)
			var x: float = -float(b.w) + 4.0
			while x < float(b.w):
				c.draw_line(at + dir * x + Vector2(-dir.y, dir.x) * 1.5, at + dir * (x + 3.0) - Vector2(-dir.y, dir.x) * 1.5, Color(Color("f0c0c0"), 0.5 * alpha), 1)
				x += 9.0
			return true
		"ink":
			c.draw_circle(at, float(b.r), Color(INKBLUE.lerp(Color("6a7ad0"), 0.5 if int(b.age) <= int(b.arm) else 0.0), alpha))
			return true
		"pen":
			var dir2: Vector2 = Vector2.from_angle(float(b.rot))
			var back: Vector2 = at - dir2 * 14.0
			c.draw_line(back, at - dir2 * 3.0, Color(Color("20202a"), alpha), 5.0)
			c.draw_line(back, back + dir2 * 4.0, Color(AMBER, alpha), 5.0)
			c.draw_colored_polygon(PackedVector2Array([at, at - dir2 * 4.0 + Vector2(-dir2.y, dir2.x) * 2.5, at - dir2 * 4.0 - Vector2(-dir2.y, dir2.x) * 2.5]), Color(AMBER, alpha))
			if int(b.age) <= int(b.arm): c.draw_arc(at, 9.0, 0, TAU, 16, Color(RED, 0.6), 1)
			return true
		"form":
			var col2: Color = Color(CREAM, alpha) if not frozen else Color(Color("b0a890"), alpha)
			c.draw_colored_polygon(v.quad(at, 3.0, 4.0, turn), col2)
			c.draw_line(at + Vector2(-2, -1).rotated(turn), at + Vector2(2, -1).rotated(turn), Color(LILAC, alpha), 1)
			c.draw_line(at + Vector2(-2, 1).rotated(turn), at + Vector2(1, 1).rotated(turn), Color(LILAC, alpha), 1)
			return true
		"cell":
			if int(b.age) <= int(b.arm) and not frozen: return true
			var poly: PackedVector2Array = v.quad(at, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(poly, Color(RED, 0.75 * alpha))
			v.text(c, at + Vector2(0, 4), "APPROVED", Color(Color("f0c0c0"), alpha), 70.0)
			return true
	return false
