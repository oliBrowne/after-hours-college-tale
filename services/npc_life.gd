class_name NativeNpcLife
extends RefCounted
## Room NPCs look around while nobody is talking to them: now and then they glance left or
## right (each on its own slow rhythm), and when Jules walks up they turn to face them. Only sprites
## with side poses take part; poses that tell a story (settled, down, interact) are left alone.
## A turn is held for at least HOLD seconds, so people don't flick back and forth.
const NOTICE_RADIUS: float = 72.0
const GLANCE: float = 1.6
const HOLD: float = 1.2

static func update(npc: AnimatedSprite2D, player: Vector2, time: float, reduced: bool) -> void:
	var current: String = str(npc.animation)
	if not current.begins_with("idle_"): return
	var frames: SpriteFrames = npc.sprite_frames
	if not (frames.has_animation("idle_left") and frames.has_animation("idle_right") and frames.has_animation("idle_up")): return
	var want: String = facing(npc, player, time, reduced)
	if want == current: return
	if time - float(npc.get_meta("turned_at", -INF)) < HOLD: return
	npc.set_meta("turned_at", time)
	npc.play(want)

static func facing(npc: AnimatedSprite2D, player: Vector2, time: float, reduced: bool) -> String:
	var gap: Vector2 = player - npc.position
	if gap.length() < NOTICE_RADIUS:
		# Keep the current side or up/down unless Jules has clearly moved round to the other one.
		var current: String = str(npc.animation)
		var side: bool = current in ["idle_left", "idle_right"]
		var ratio: float = absf(gap.x) / maxf(absf(gap.y), 0.001)
		if side and ratio < 0.5 or not side and ratio > 1.5: side = not side
		if side: return "idle_right" if gap.x > 0 else "idle_left"
		return "idle_up" if gap.y < -6 else "idle_down"
	if reduced: return "idle_down"
	var seed: int = absi(str(npc.get_meta("id", "")).hash()) % 97
	var period: float = 12.0 + float(seed % 7) * 2.0
	var clock: float = time + float(seed) * 0.37
	if fposmod(clock, period) >= GLANCE: return "idle_down"
	return "idle_left" if (int(clock / period) + seed) % 2 == 0 else "idle_right"
