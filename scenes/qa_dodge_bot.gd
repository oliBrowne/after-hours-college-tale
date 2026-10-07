class_name DodgeBot
extends RefCounted
## A lookahead dodger for previews and tuning: tries each input on a copy of
## the pattern for a short horizon and keeps the one that takes fewest hits.
## Used by the QA routes and the preview tools. Near a promise objective it
## accepts some risk to reach it. Not a difficulty oracle.

const D = preload("res://core/dodge_box.gd")
var plan_axis: Vector2 = Vector2.ZERO
var plan_precision: bool = false
var plan_age: int = 99
var horizon: int = 18
var replan: int = 3
## QA routes that deliberately miss a promise set this: the bot only dodges.
var skip_promise: bool = false

func choose(p: Dictionary) -> Dictionary:
	var press: bool = _want_press(p) and not skip_promise
	if str(p.soul.mode) == "green":
		return {"axis": _shield_axis(p), "press": press}
	plan_age += 1
	if plan_age >= replan:
		plan_age = 0
		var best: Array = _best(p)
		plan_axis = best[0]; plan_precision = best[1]
	return {"axis": plan_axis, "press": press, "precision": plan_precision}

## Each candidate is [axis, precision].
func _candidates(p: Dictionary) -> Array:
	var out: Array = []
	var mode: String = str(p.soul.mode)
	if mode == "blue":
		var up: Vector2 = (-Vector2(p.soul.gravity)).rotated(float(p.box.rot))
		var side: Vector2 = Vector2(-up.y, up.x)
		for sx: float in [-1.0, 0.0, 1.0]:
			for jump: float in [0.0, 1.0]:
				out.append([(side * sx + up * jump).limit_length(1.0), false])
			if p.get("duckable", false): out.append([side * sx, true])
		return out
	if mode in ["lanes", "flipper"]:
		var right: Vector2 = Vector2.RIGHT.rotated(float(p.box.rot))
		for sx: float in [-1.0, 0.0, 1.0]: out.append([right * sx, false])
		return out
	out.append([Vector2.ZERO, false])
	for i: int in range(8): out.append([Vector2.from_angle(i * TAU / 8.0), false])
	return out

func _best(p: Dictionary) -> Array:
	var goal: Variant = _goal(p)
	var deadline: int = _deadline(p)
	var best: Array = [Vector2.ZERO, false]
	var best_score: float = INF
	for candidate: Array in _candidates(p):
		var axis: Vector2 = candidate[0]
		var sim: Dictionary = p.duplicate(true)
		var hits: int = 0
		# Closest approach to the goal along the path, so the bot can stop on a
		# goal nearer than one full-speed horizon instead of stalling short of it.
		var closest: float = INF
		var at_deadline: float = 0.0
		for i: int in range(horizon):
			D.step(sim, axis, bool(candidate[1]), 1.0, false, true, false)
			if sim.hit: hits += 1
			if goal != null: closest = minf(closest, Vector2(float(sim.cursor.x), float(sim.cursor.y)).distance_to(goal))
			if goal != null and int(sim.clock) - int(sim.leadIn) == deadline: at_deadline = Vector2(float(sim.cursor.x), float(sim.cursor.y)).distance_to(goal)
			if sim.done: break
		var at: Vector2 = Vector2(float(sim.cursor.x), float(sim.cursor.y))
		var score: float = hits * (250.0 if goal != null else 1000.0) + at.distance_to(D.centre(sim)) * 0.05
		for b: Dictionary in sim.bullets:
			var gap: float = D.clearance(sim, b, Vector2(float(sim.soul.x), float(sim.soul.y)) if b.space == "box" else at)
			if gap < 14.0: score += (14.0 - gap) * (0.5 if goal != null else 2.0)
		if goal != null: score += closest * 3.0 + at.distance_to(goal) * 1.0 + at_deadline * 4.0
		score += D.bot_avoid(sim, Vector2(float(sim.soul.x), float(sim.soul.y)))
		if axis == plan_axis and bool(candidate[1]) == plan_precision: score -= 0.5
		if score < best_score:
			best_score = score; best = candidate
	return best

## The tick the goal must be held at (Walt's next gust), or -1.
func _deadline(p: Dictionary) -> int:
	if p.encounterId != "walt" or skip_promise: return -1
	var t: int = int(p.clock) - int(p.leadIn)
	for g: int in DodgePatternsWalt.GUSTS:
		if t >= g - 75 and t <= g: return g
	return -1

func _goal(p: Dictionary) -> Variant:
	if skip_promise: return null
	var t: int = int(p.clock) - int(p.leadIn)
	if p.encounterId == "walt":
		for g: int in DodgePatternsWalt.GUSTS:
			if t >= g - 75 and t <= g:
				return D.to_world(p, DodgePatternsWalt.lantern_local(p))
	else:
		for cue: Dictionary in p.get("cues", []):
			if cue.placed and not cue.got and t >= int(cue.t) - 30 and t < int(cue.t) + int(cue.open):
				return D.to_world(p, Vector2(float(cue.x), float(cue.y)))
	return D.bot_goal(p)

func _want_press(p: Dictionary) -> bool:
	var t: int = int(p.clock) - int(p.leadIn)
	var soul: Vector2 = Vector2(float(p.soul.x), float(p.soul.y))
	if p.encounterId == "walt":
		for g: int in DodgePatternsWalt.GUSTS:
			if t >= g - 85 and t < g and int(p.lanternRaised) < g - t + 2 and soul.distance_to(DodgePatternsWalt.lantern_local(p)) <= DodgePatternsWalt.LANTERN_REACH - 2.0:
				return true
		return false
	elif p.encounterId == "encore":
		for cue: Dictionary in p.get("cues", []):
			if cue.placed and not cue.got and t >= int(cue.t) and soul.distance_to(Vector2(float(cue.x), float(cue.y))) <= 12.0:
				return true
		return false
	return D.bot_press(p)

func _shield_axis(p: Dictionary) -> Vector2:
	var soul: Vector2 = D.soul_world(p)
	var nearest: float = INF
	var dir: Vector2 = Vector2.ZERO
	for b: Dictionary in p.bullets:
		if not b.get("target", false): continue
		if b.has("flip") and int(b.flip) < 25: continue
		var offset: Vector2 = D.bullet_world(p, b) - soul
		if offset.length() < nearest:
			nearest = offset.length()
			dir = Vector2(signf(offset.x), 0) if absf(offset.x) >= absf(offset.y) else Vector2(0, signf(offset.y))
	return dir
