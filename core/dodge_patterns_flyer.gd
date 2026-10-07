extends RefCounted
## FLYERER / Paper Orbit: the very first fight. A club flyer stand that will not
## close until somebody reads one page. Four handmade attacks, one per turn,
## cycling in order. Every attack keeps the old promise: one outlined
## invitation drifts through the box; touch it while promised to read it.
## Confirm is the old paper push: for 15 ticks it fends off close paper
## (not staples), then needs 15 more ticks to recover.
## Phase 0 only ever runs Paper Orbit in the game (the first dodge): it is
## gentle and teaches that the box moves and changes shape. Phase 1 (from the
## second turn) adds a layer to every attack.

const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["paper_rings", "tear_tabs", "bulletin", "paper_planes"]
const PHASES: Array[int] = [0, 1]
const PUSH_REACH: float = 24.0
const PUSH_TICKS: int = 15
const PUSH_COOLDOWN: int = 30
const TABS: int = 9

const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const AMBER: Color = Color("e8b45c")
const MINT: Color = Color("b9d5bc")
const ROSE: Color = Color("e8837b")
const LILAC: Color = Color("a68db8")
const BLUE: Color = Color("8fb3ea")
const CORK: Color = Color("6b5238")
## No mint: mint is reserved for the invitation.
const POSTER_HUES: Array[Color] = [Color("e6d6b1"), Color("e8b45c"), Color("8fb3ea"), Color("e0a0d8")]

static func setup(s: Dictionary) -> void:
	var id: String = ORDER[int(s.turn) % ORDER.size()]
	s.patternId = id
	s.length = 420 + 60 * clampi(int(s.phase), 0, 1)
	s.pushUntil = -1
	s.pushReady = 0
	s.tabTorn = []
	s.tabPending = []
	for i: int in range(TABS): s.tabTorn.append(-999)
	s.inviteSpot = Vector2(0.6, 0.0)
	match id:
		"paper_rings":
			s.phaseName = "Paper Orbit"
			s.hint = "Paper circles in. Slip out through each ring's gap. Touch the outlined invitation to read it."
		"tear_tabs":
			s.phaseName = "Tear-Off Tabs"
			s.hint = "Shaking tabs tear off and flutter down. Staples are aimed. Read the outlined invitation."
		"bulletin":
			s.phaseName = "Bulletin Board"
			s.hint = "Outlined posters get pinned down, then torn off. Keep clear. Read the invitation."
		"paper_planes":
			s.phaseName = "Paper Planes"
			s.hint = "Paper planes steer at you, then fly straight. Confirm pushes close paper. Read the invitation."
	# The invitation: one outlined page, collected on touch while promised.
	D.objective(s, {"kind": "touch", "r": 11.0, "label": "invite", "active": false, "x": 70.0, "y": 0.0})

## Confirm: a brief paper push that fends off close paper.
static func confirm(s: Dictionary) -> void:
	if int(s.clock) < int(s.pushReady): return
	s.pushUntil = int(s.clock) + PUSH_TICKS
	s.pushReady = int(s.clock) + PUSH_COOLDOWN
	D.effect(s, "lantern", D.soul_world(s), 20)
	_push(s)

static func _push(s: Dictionary) -> void:
	if int(s.clock) > int(s.pushUntil): return
	var soul: Vector2 = D.soul_world(s)
	for b: Dictionary in s.bullets:
		if not b.get("paper", false) or b.get("friendly", false) or b.has("fade"): continue
		var at: Vector2 = D.bullet_world(s, b)
		var away: Vector2 = at - soul
		if away.length() > PUSH_REACH + float(b.get("r", 4.0)): continue
		b.erase("orbit"); b.erase("wave"); b.erase("home"); b.erase("hold")
		b.friendly = true
		b.fade = 22
		b.ax = 0.0; b.ay = 0.0
		var dir: Vector2 = away.normalized() if away.length() > 0.1 else Vector2.UP
		if b.space == "box": dir = dir.rotated(-float(s.box.rot))
		b.vx = dir.x * 3.2; b.vy = dir.y * 3.2
		b.spin = 0.3
		D.effect(s, "block", at, 12)

static func promise_complete(s: Dictionary) -> bool:
	return bool(s.objectives[0].done)

static func progress(s: Dictionary) -> String:
	return "Invitation read %d/1" % (1 if bool(s.objectives[0].done) else 0)

static func tick(s: Dictionary, t: int) -> void:
	var phase: int = clampi(int(s.phase), 0, 1)
	_push(s)
	match str(s.patternId):
		"paper_rings": _paper_rings(s, t, phase)
		"tear_tabs": _tear_tabs(s, t, phase)
		"bulletin": _bulletin(s, t, phase)
		"paper_planes": _paper_planes(s, t, phase)
	_invitation(s, t)

static func after(s: Dictionary, t: int) -> void:
	var spawns: Array = []
	for b: Dictionary in s.bullets:
		# Posters torn off the board scatter into scraps.
		if b.has("tear") and not b.get("torn", false) and not b.has("fade") and int(b.age) >= int(b.life) - 1:
			b.torn = true
			b.life = int(b.age)
			spawns.append(b)
		# Loop-the-loop planes turn a full circle once.
		if b.has("loopAt") and int(b.age) >= int(b.loopAt) and int(b.age) < int(b.loopAt) + int(b.loopLen) and not b.get("friendly", false):
			var v: Vector2 = Vector2(float(b.vx), float(b.vy)).rotated(float(b.loopDir) * TAU / float(b.loopLen))
			b.vx = v.x; b.vy = v.y
	for b: Dictionary in spawns:
		_scraps(s, b)
	# QA autopilot: use the push when paper is about to touch.
	s.botPress = false
	if int(s.clock) >= int(s.pushReady) and t >= 0:
		var soul: Vector2 = D.soul_world(s)
		for b: Dictionary in s.bullets:
			if b.get("paper", false) and not b.get("friendly", false) and int(b.age) > int(b.arm) and D.bullet_world(s, b).distance_to(soul) < 13.0:
				s.botPress = true
				break

# ---------------------------------------------------------------- the invitation

static func _invitation(s: Dictionary, t: int) -> void:
	var o: Dictionary = s.objectives[0]
	if o.done: return
	var h: Vector2 = D.half(s)
	var at: Vector2 = Vector2.ZERO
	match str(s.patternId):
		"paper_rings":
			var a: float = 0.006 * t - 0.4
			at = Vector2(cos(a) * 0.62 * h.x, sin(a) * 0.5 * h.y)
		"tear_tabs":
			at = Vector2(sin(t * 0.011 + 1.2) * 0.68 * h.x, 0.58 * h.y)
		"bulletin":
			# Reposted every 130 ticks, on the spot farthest from you.
			if t % 130 == 0 and t > 0:
				var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
				var best: Vector2 = s.inviteSpot
				var far: float = -1.0
				for spot: Vector2 in [Vector2(0.62, -0.5), Vector2(-0.62, -0.5), Vector2(0.62, 0.5), Vector2(-0.62, 0.5), Vector2(0.0, -0.55)]:
					var d: float = (spot * h).distance_to(soul)
					if d > far: far = d; best = spot
				s.inviteSpot = best
				D.effect(s, "pulse", D.to_world(s, best * h), 16)
			at = Vector2(s.inviteSpot) * h
		"paper_planes":
			at = Vector2(sin(t * 0.013) * 0.55 * h.x, cos(t * 0.017) * 0.42 * h.y)
	o.x = at.x; o.y = at.y
	o.active = t >= 40

# ---------------------------------------------------------------- attacks

static func _paper(s: Dictionary, props: Dictionary) -> Dictionary:
	var b: Dictionary = {"collide": "rect", "w": 4.0, "h": 4.5, "shape": "paper", "paper": true, "life": 300}
	b.merge(props, true)
	return D.shot(s, b)

## A ring of paper closing in on the box centre with one gap.
static func _ring(s: Dictionary, radius: float, gap: float, gap_half: float, av: float, dr: float, count: int) -> void:
	var c: Vector2 = D.centre(s)
	for i: int in range(count):
		var a: float = gap + gap_half + (TAU - 2.0 * gap_half) * (float(i) + 0.5) / float(count)
		_paper(s, {"orbit": {"ox": c.x, "oy": c.y, "radius": radius, "angle": a, "av": av, "dr": dr, "minRadius": 4.0}, "rot": a, "spin": 0.04, "life": 400})

## A paper fired along a box row from one side, after an edge warning.
static func _side_paper(s: Dictionary, side: float, y: float, speed: float, warn_ticks: int, props: Dictionary = {}) -> void:
	var h: Vector2 = D.half(s)
	D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": y, "dir": Vector2(-side, 0)}, warn_ticks)
	var b: Dictionary = {"space": "box", "x": side * (h.x + 6.0 + speed * float(warn_ticks)), "y": y, "vx": -side * speed, "rot": 0.0, "spin": 0.1 * side}
	b.merge(props, true)
	_paper(s, b)

# Paper Orbit: rings of paper orbit inward with one gap; aimed paper comes from
# the sides. The box narrows and widens to show it can. Phase 1 doubles each
# ring with a second, offset gap and alternates the spin.
static func _paper_rings(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 212.0, "h": 120.0}, 30)
	if phase == 0:
		if t == 150:
			D.warn(s, {"kind": "curtain"}, 30, true)
			D.box_to(s, {"w": 156.0, "h": 112.0}, 40, 30)
		if t == 290:
			D.box_to(s, {"w": 224.0, "h": 104.0}, 40)
	else:
		if t == 130:
			D.warn(s, {"kind": "curtain"}, 30, true)
			D.box_to(s, {"w": 150.0, "h": 116.0}, 40, 30)
		if t == 260:
			D.box_to(s, {"w": 220.0, "h": 100.0, "cx": 116.0}, 50)
		if t == 380:
			D.box_to(s, {"cx": 140.0}, 50)
	var every: int = 124 if phase == 0 else 100
	if t % every == 20 and t < int(s.length) - 120:
		var gap: float = (D.soul_world(s) - D.centre(s)).angle() + D.rand_range(s, 1.4, 2.4) * (1.0 if D.rand(s) < 0.5 else -1.0)
		var spin: float = 1.0 if int(t / every) % 2 == 0 or phase == 0 else -1.0
		D.effect(s, "pulse", D.centre(s), 20)
		_ring(s, 150.0, gap, 0.8, 0.007 * spin, -1.1 - phase * 0.15, 16)
		if phase > 0:
			_ring(s, 176.0, gap + 1.1 * spin, 0.62, 0.007 * spin, -1.25, 18)
	var side_every: int = 96 if phase == 0 else 80
	if t % side_every == 70 and t < int(s.length) - 90:
		var side: float = 1.0 if int(t / side_every) % 2 == 0 else -1.0
		var y: float = clampf(float(s.soul.y), -D.half(s).y + 8.0, D.half(s).y - 8.0)
		_side_paper(s, side, y, 2.5, 40)
		if phase > 0:
			_side_paper(s, -side, clampf(y + (22.0 if y < 0.0 else -22.0), -D.half(s).y + 8.0, D.half(s).y - 8.0), 2.2, 52)

# Tear-Off Tabs: the flyer hangs over the box; its phone-number tabs shake, tear
# off and flutter down (every other one over you). A stapler on the side fires
# rows of staples at your height. Phase 1 slides the flyer and folds the box.
static func _tear_tabs(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 220.0, "h": 108.0, "cy": 64.0}, 24)
	if phase > 0:
		for at: int in [150, 310]:
			if t == at:
				D.banner(s, "FOLD", 40)
				D.warn(s, {"kind": "flip"}, 30, true)
				D.box_to(s, {"h": 70.0}, 24, 30)
				D.box_to(s, {"h": 108.0}, 30, 110)
	var every: int = 26 if phase == 0 else 18
	if t % every == 0 and t >= 20 and t < int(s.length) - 80:
		var col: int = int(D.rand(s) * TABS)
		if int(t / every) % 2 == 0:
			var best: float = INF
			for i: int in range(TABS):
				var d: float = absf(_tab_x(s, i, t + 30) - float(s.soul.x))
				if d < best: best = d; col = i
		s.tabPending.append({"col": col, "at": t + 30})
	var pending: Array = []
	for tab: Dictionary in s.tabPending:
		if int(tab.at) == t:
			var col: int = int(tab.col)
			s.tabTorn[col] = t
			_paper(s, {"space": "box", "x": _tab_x(s, col, t), "y": -D.half(s).y - 2.0, "vy": 1.25 + phase * 0.15, "ay": 0.008, "collide": "rect", "w": 2.5, "h": 5.0, "shape": "tab",
				"wave": {"amp": 6.0, "freq": 0.09, "phase": D.rand(s) * TAU}, "life": 260})
		elif int(tab.at) > t:
			pending.append(tab)
	s.tabPending = pending
	var staple_every: int = 100 if phase == 0 else 70
	if t % staple_every == 50 and t < int(s.length) - 90:
		var side: float = 1.0 if int(t / staple_every) % 2 == 0 else -1.0
		var h: Vector2 = D.half(s)
		var y: float = clampf(float(s.soul.y), -h.y + 6.0, h.y - 6.0)
		s.stapler = {"side": side, "y": y, "until": t + 40}
		D.warn(s, {"kind": "edge", "space": "box", "x": side * (h.x - 3.0), "y": y, "dir": Vector2(-side, 0)}, 34, true)
		for i: int in range(3):
			D.shot(s, {"space": "box", "x": side * (h.x + 8.0 + 3.0 * 34.0 + i * 14.0), "y": y, "vx": -side * 3.0, "collide": "rect", "w": 4.0, "h": 1.5, "shape": "staple", "life": 220})

static func _tab_x(s: Dictionary, col: int, t: int) -> float:
	var h: Vector2 = D.half(s)
	var span: float = h.x * 2.0 - 28.0
	var slide: float = sin(t * 0.012) * 16.0 if int(s.phase) > 0 else 0.0
	return -h.x + 14.0 + span * float(col) / float(TABS - 1) + slide

# Bulletin Board: posters are outlined on the cork, then pinned down (solid for
# a while, so the board fills up), then torn off into scraps that fly out, one
# at you. Phase 1 pins two at a time and tilts the board.
static func _bulletin(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 244.0, "h": 120.0}, 24)
	if phase > 0:
		if t == 120: D.box_to(s, {"rot": 0.22}, 60)
		if t == 260: D.box_to(s, {"rot": -0.22}, 70)
		if t == 400: D.box_to(s, {"rot": 0.0}, 50)
	var every: int = 46 if phase == 0 else 40
	if t % every == 10 and t < int(s.length) - 120:
		_poster(s, true)
		if phase > 0: _poster(s, false)
	if t % every == 33 and t < int(s.length) - 120 and phase == 0 and int(t / every) % 2 == 1:
		_poster(s, false)

static func _poster(s: Dictionary, aimed: bool) -> void:
	var h: Vector2 = D.half(s)
	var size: Vector2 = Vector2(D.rand_range(s, 14.0, 20.0), D.rand_range(s, 11.0, 15.0))
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var at: Vector2 = soul + Vector2(D.rand_range(s, -8.0, 8.0), D.rand_range(s, -6.0, 6.0)) if aimed else Vector2(D.rand_range(s, -h.x, h.x), D.rand_range(s, -h.y, h.y))
	at = at.clamp(-h + size, h - size)
	# Never pin a poster over the invitation: try elsewhere, or skip this one.
	var invite: Vector2 = Vector2(float(s.objectives[0].x), float(s.objectives[0].y))
	if not s.objectives[0].done:
		var tries: int = 0
		while absf(at.x - invite.x) < size.x + 18.0 and absf(at.y - invite.y) < size.y + 18.0:
			tries += 1
			if tries > 5: return
			at = Vector2(D.rand_range(s, -h.x, h.x), D.rand_range(s, -h.y, h.y)).clamp(-h + size, h - size)
	D.shot(s, {"space": "box", "x": at.x, "y": at.y, "collide": "rect", "w": size.x, "h": size.y, "shape": "poster", "hold": true, "arm": 40, "life": 40 + 76,
		"tear": true, "hue": int(D.rand(s) * 4.0), "rot": D.rand_range(s, -0.06, 0.06)})

static func _scraps(s: Dictionary, poster: Dictionary) -> void:
	var from: Vector2 = Vector2(float(poster.x), float(poster.y))
	var soul: Vector2 = Vector2(float(s.soul.x), float(s.soul.y))
	var aim: float = (soul - from).angle()
	for i: int in range(4):
		var a: float = aim + (0.0 if i == 0 else PI * 0.5 * i + D.rand_range(s, -0.3, 0.3))
		var speed: float = 0.6
		_paper(s, {"space": "box", "x": from.x, "y": from.y, "vx": cos(a) * speed, "vy": sin(a) * speed, "ax": cos(a) * 0.04, "ay": sin(a) * 0.04, "w": 3.0, "h": 3.0,
			"rot": D.rand(s) * TAU, "spin": 0.15, "life": 200, "hue": int(poster.hue)})
	D.effect(s, "pulse", D.to_world(s, from), 14)

# Paper Planes: volleys from alternating sides steer toward you for a moment,
# then fly straight; crumpled pages bounce along the floor. The box pans. Phase 1
# planes loop the loop once mid-flight.
static func _paper_planes(s: Dictionary, t: int, phase: int) -> void:
	if t == 0:
		D.box_to(s, {"w": 220.0, "h": 112.0}, 24)
	if t == 120: D.box_to(s, {"cx": 112.0}, 60)
	if t == 250: D.box_to(s, {"cx": 144.0, "w": 196.0}, 70)
	if t == 380: D.box_to(s, {"cx": 128.0, "w": 220.0}, 50)
	var every: int = 60 if phase == 0 else 50
	if t % every == 20 and t < int(s.length) - 90:
		var side: float = 1.0 if int(t / every) % 2 == 0 else -1.0
		var h: Vector2 = D.half(s)
		var count: int = 2 if phase == 0 else 3
		var centre_y: float = clampf(float(s.soul.y), -h.y + 16.0, h.y - 16.0)
		for i: int in range(count):
			var y: float = clampf(centre_y + (float(i) - float(count - 1) * 0.5) * 34.0, -h.y + 6.0, h.y - 6.0)
			var speed: float = 2.1
			var props: Dictionary = {"collide": "rect", "w": 5.0, "h": 2.5, "shape": "plane", "home": 52, "homeTurn": 0.022, "life": 320, "spin": 0.0}
			if phase > 0 and i == 1:
				props.merge({"loopAt": 70 + int(D.rand(s) * 20.0), "loopLen": 56, "loopDir": side}, true)
			_side_paper(s, side, y, speed, 32, props)
	if t % 80 == 60 and t < int(s.length) - 90:
		var h2: Vector2 = D.half(s)
		var from_left: bool = D.rand(s) < 0.5
		D.shot(s, {"space": "box", "x": -h2.x - 10.0 if from_left else h2.x + 10.0, "y": -h2.y + 10.0, "vx": D.rand_range(s, 1.0, 1.6) * (1.0 if from_left else -1.0), "vy": -0.5, "ay": 0.09, "bounce": 0.82,
			"r": 5.0, "shape": "crumple", "paper": true, "spin": 0.12, "life": 320})

# ---------------------------------------------------------------- drawing

static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var h: Vector2 = D.half(s)
	if s.patternId == "bulletin":
		c.draw_colored_polygon(v.box_rect_poly(Rect2(-h, h * 2.0)), Color(CORK, 0.35))
		for i: int in range(40):
			var p: Vector2 = Vector2(fposmod(i * 53.0, h.x * 2.0) - h.x, fposmod(i * 29.0, h.y * 2.0) - h.y)
			c.draw_circle(v.box_point(p), 1.0, Color(0.0, 0.0, 0.0, 0.25))
	else:
		# Ruled paper: faint lines and a margin.
		var y: float = -h.y + 12.0
		while y < h.y:
			c.draw_line(v.box_point(Vector2(-h.x, y)), v.box_point(Vector2(h.x, y)), Color(BLUE, 0.07), 1)
			y += 14.0
		c.draw_line(v.box_point(Vector2(-h.x + 22.0, -h.y)), v.box_point(Vector2(-h.x + 22.0, h.y)), Color(ROSE, 0.10), 1)
	if s.patternId == "paper_rings":
		var centre: Vector2 = v.arena_point(D.centre(s))
		c.draw_arc(centre, 6.0, 0, TAU, 16, Color(LILAC, 0.25), 1)
	# The invitation page under its mint outline.
	var o: Dictionary = s.objectives[0]
	if bool(s.promised) and o.active and not o.done:
		var at: Vector2 = v.box_point(Vector2(float(o.x), float(o.y)))
		var turn: float = float(s.box.rot)
		c.draw_colored_polygon(v.quad(at, 6.0, 7.5, turn), Color(CREAM, 0.85))
		for i: int in range(3):
			var row: float = -4.0 + i * 3.5
			c.draw_line(at + Vector2(-4, row).rotated(turn), at + Vector2(4 - (3 if i == 2 else 0), row).rotated(turn), Color(LILAC, 0.9), 1)
		c.draw_circle(at + Vector2(0, -6).rotated(turn), 1.2, ROSE)

static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void:
	var t: int = int(s.clock) - int(s.leadIn)
	if s.patternId == "tear_tabs": _draw_flyer(c, s, v, t)
	if s.patternId == "tear_tabs" and s.has("stapler") and t < int(s.stapler.until):
		var h: Vector2 = D.half(s)
		var side: float = float(s.stapler.side)
		var at: Vector2 = v.box_point(Vector2(side * (h.x + 14.0), float(s.stapler.y)))
		c.draw_rect(Rect2(at + Vector2(-9, -5), Vector2(18, 10)), Color("3a3448"))
		c.draw_rect(Rect2(at + Vector2(-9, -5), Vector2(18, 10)), LILAC, false, 1)
		c.draw_line(at + Vector2(-side * 9.0, 3), at + Vector2(side * 4.0, 3), CREAM, 1)
	# The paper push.
	if int(s.clock) <= int(s.pushUntil):
		var p: float = 1.0 - float(int(s.pushUntil) - int(s.clock)) / float(PUSH_TICKS)
		c.draw_arc(v.arena_point(D.soul_world(s)), PUSH_REACH * (0.6 + 0.4 * p), 0, TAU, 24, Color(CREAM, 0.7 * (1.0 - p)), 2)

static func _draw_flyer(c: CanvasItem, s: Dictionary, v: Node2D, t: int) -> void:
	var h: Vector2 = D.half(s)
	var top: float = -h.y
	var left: Vector2 = v.box_point(Vector2(-h.x + 4.0, top - 26.0))
	var right: Vector2 = v.box_point(Vector2(h.x - 4.0, top - 2.0))
	var r: Rect2 = Rect2(left, right - left)
	c.draw_rect(r, CREAM)
	c.draw_rect(r, AMBER, false, 1)
	v.text(c, Vector2(r.get_center().x, r.position.y + 11.0), "JOIN US! ONE PAGE! READ ME!", INK, r.size.x)
	c.draw_line(Vector2(r.position.x + 6, r.end.y - 6), Vector2(r.end.x - 6, r.end.y - 6), Color(LILAC, 0.6), 1)
	var pending: Dictionary = {}
	for tab: Dictionary in s.tabPending: pending[int(tab.col)] = int(tab.at) - t
	for i: int in range(TABS):
		if t - int(s.tabTorn[i]) < 36: continue
		var x: float = _tab_x(s, i, t)
		var at: Vector2 = v.box_point(Vector2(x, top + 4.0))
		var shake: float = 0.0
		var colour: Color = CREAM
		if pending.has(i):
			shake = sin(t * 1.3 + i) * 1.6
			colour = CREAM.lerp(ROSE, 0.6)
			c.draw_line(v.box_point(Vector2(x, top + 10.0)), v.box_point(Vector2(x, top + 30.0)), Color(ROSE, 0.35), 3)
		c.draw_colored_polygon(v.quad(at + Vector2(shake, 0), 2.5, 5.0, shake * 0.1), colour)
		c.draw_line(at + Vector2(shake, -3), at + Vector2(shake, 3), Color(LILAC, 0.9), 1)

static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool:
	match str(b.shape):
		"tab":
			c.draw_colored_polygon(v.quad(at, 2.5, 5.0, turn), Color(CREAM, alpha))
			c.draw_line(at + Vector2(0, -3.5).rotated(turn), at + Vector2(0, 3.5).rotated(turn), Color(LILAC, alpha), 1)
			return true
		"staple":
			var d: Vector2 = Vector2(float(b.vx), float(b.vy)).normalized()
			var side: Vector2 = Vector2(-d.y, d.x) * 3.0
			c.draw_polyline(PackedVector2Array([at - d * 3.0 + side, at + d * 3.0 + side, at + d * 3.0 - side, at - d * 3.0 - side]), Color(Color("c9d0da"), alpha), 2)
			return true
		"poster":
			var lit: bool = int(b.age) > int(b.arm)
			var hue: Color = POSTER_HUES[int(b.get("hue", 0)) % POSTER_HUES.size()]
			var q: PackedVector2Array = v.quad(at, float(b.w), float(b.h), turn)
			if not lit:
				var blink: float = 0.4 + 0.4 * sin(float(b.age) * 0.5)
				c.draw_colored_polygon(q, Color(ROSE, 0.08 + 0.1 * blink))
				c.draw_polyline(q + PackedVector2Array([q[0]]), Color(ROSE, 0.5 + blink * 0.5), 1)
				c.draw_circle(at + Vector2(0, -float(b.h) + 3.0).rotated(turn), 2.0, Color(ROSE, 0.5 + blink * 0.5))
				return true
			var left: int = int(b.life) - int(b.age)
			var shake: Vector2 = Vector2(sin(float(b.age) * 1.7), 0) * (1.5 if left < 18 else 0.0)
			q = v.quad(at + shake, float(b.w), float(b.h), turn)
			c.draw_colored_polygon(q, Color(hue, 0.95 * alpha))
			c.draw_polyline(q + PackedVector2Array([q[0]]), Color(INK, 0.8 * alpha), 1)
			for i: int in range(3):
				var y: float = -float(b.h) + 7.0 + i * 5.0
				if y > float(b.h) - 3.0: break
				c.draw_line(at + shake + Vector2(-float(b.w) + 4.0, y).rotated(turn), at + shake + Vector2(float(b.w) - 4.0 - i * 4.0, y).rotated(turn), Color(LILAC, alpha), 1)
			c.draw_circle(at + shake + Vector2(0, -float(b.h) + 3.0).rotated(turn), 2.0, Color(ROSE, alpha))
			return true
		"plane":
			var vel: Vector2 = Vector2(float(b.vx), float(b.vy))
			if b.space == "box": vel = vel.rotated(float(v.pattern.box.rot))
			var d2: Vector2 = vel.normalized() if vel.length() > 0.01 else Vector2.RIGHT
			var side2: Vector2 = Vector2(-d2.y, d2.x)
			c.draw_colored_polygon(PackedVector2Array([at + d2 * 6.0, at - d2 * 5.0 + side2 * 4.0, at - d2 * 3.0, at - d2 * 5.0 - side2 * 4.0]), Color(CREAM, alpha))
			c.draw_line(at + d2 * 6.0, at - d2 * 3.0, Color(LILAC, alpha), 1)
			if b.has("loopAt") and int(b.age) < int(b.loopAt):
				c.draw_arc(at, 8.0, 0, TAU, 12, Color(ROSE, 0.4 * alpha), 1)
			return true
		"crumple":
			var pts: PackedVector2Array = []
			for i: int in range(9):
				var a: float = i * TAU / 9.0
				var rr: float = float(b.r) * (0.8 + 0.25 * sin(a * 3.0 + 1.0))
				pts.append(at + Vector2(cos(a), sin(a)).rotated(turn) * rr)
			c.draw_colored_polygon(pts, Color(CREAM, alpha))
			c.draw_line(at + Vector2(-3, -1).rotated(turn), at + Vector2(2, 2).rotated(turn), Color(LILAC, alpha), 1)
			return true
	return false
