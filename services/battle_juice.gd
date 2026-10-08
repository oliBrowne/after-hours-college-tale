class_name NativeBattleJuice
extends RefCounted
## Battle feel. A striking party member lunges at the foe, a hit foe flinches back with a white flash,
## a hit party member is knocked back, the foe leans in before each attack, and hard hits kick the stage.
## Offsets are whole pixels added to each sprite's home position, so the pixel art is never scaled or
## rotated. Only physics ticks advance them, like CombatVFX. Reduced motion keeps the flash and drops
## the lunges, knockbacks and shakes.
static var moves: Dictionary = {}
static var flashes: Dictionary = {}
static var shake_nodes: Array = []
static var shake_ticks: int = 0
static var shake_size: float = 0.0
static var reduced: bool = false
static var _shader: Shader

static func shader() -> Shader:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = "shader_type canvas_item;\nuniform float flash : hint_range(0.0, 1.0) = 0.0;\nuniform vec4 tint : source_color = vec4(1.0);\nvoid fragment() {\n\tvec4 c = texture(TEXTURE, UV) * COLOR;\n\tCOLOR = vec4(mix(c.rgb, tint.rgb, flash), c.a);\n}\n"
	return _shader

static func _move(node: Node2D, kind: String, direction: Vector2, life: int, strength: float = 1.0) -> void:
	if node == null or not is_instance_valid(node): return
	var id: int = node.get_instance_id()
	var home: Vector2 = moves[id].home if moves.has(id) else node.position
	moves[id] = {"node": node, "home": home, "kind": kind, "dir": direction, "tick": 0, "life": life, "strength": strength}

## A party member steps in toward the foe and back (a strike).
static func lunge(node: Node2D, direction: Vector2 = Vector2.RIGHT) -> void: _move(node, "lunge", direction, 24)
## Each party member's own strike (46 ticks, the hit lands at tick 20): Jules winds up and dashes in
## with afterimages, Imani jabs twice, Walt leans back and slams. Drives the sprite's pose too.
static func strike(node: Node2D, member_id: String, direction: Vector2 = Vector2.RIGHT) -> void:
	if node == null or not is_instance_valid(node): return
	if node is AnimatedSprite2D: (node as AnimatedSprite2D).play("strike"); (node as AnimatedSprite2D).pause()
	_move(node, "strike_" + member_id, direction, 46)

## Pose (frame of the strike animation) and push-in distance for a character at a tick of its strike.
static func strike_pose(member_id: String, t: int) -> int:
	match member_id:
		"imani":
			if t < 6: return 2
			if t < 12: return 3
			if t < 17: return 4 if t < 14 else 2
			if t < 28: return 3
			return 4 if t < 36 else 0
		"walt":
			if t < 16: return 2
			if t < 30: return 3
			return 4 if t < 40 else 0
		_:
			if t < 16: return 2
			if t < 28: return 3
			return 4 if t < 38 else 0

static func strike_push(member_id: String, t: int) -> float:
	match member_id:
		"imani":
			if t < 4: return -4.0 * t / 4.0
			if t < 9: return -4.0 + 34.0 * float(t - 4) / 5.0
			if t < 14: return 30.0 - 20.0 * float(t - 9) / 5.0
			if t < 19: return 10.0 + 28.0 * float(t - 14) / 5.0
			if t < 26: return 38.0
			return 38.0 * (1.0 - float(t - 26) / 20.0)
		"walt":
			if t < 16: return -9.0 * sin(t / 16.0 * PI / 2.0)
			if t < 20: return -9.0 + 38.0 * float(t - 16) / 4.0
			if t < 32: return 29.0
			return 29.0 * (1.0 - float(t - 32) / 14.0)
		_:
			if t < 8: return -6.0 * sin(t / 8.0 * PI / 2.0)
			if t < 18: return -6.0 + 72.0 * pow(float(t - 8) / 10.0, 0.6)
			if t < 28: return 66.0
			return 66.0 * (1.0 - float(t - 28) / 18.0)

## Knocked back by a hit and shaking it off; strength grows with the damage.
static func flinch(node: Node2D, direction: Vector2, damage: int = 0) -> void: _move(node, "flinch", direction, 20, clampf(0.6 + damage / 12.0, 0.6, 1.6))
## The foe draws back, then leans in, before an attack.
static func windup(node: Node2D, direction: Vector2 = Vector2.LEFT) -> void: _move(node, "windup", direction, 26)
## A white flash that fades over a few ticks.
static func flash(node: CanvasItem, ticks: int = 8, tint: Color = Color.WHITE) -> void:
	if node == null or not is_instance_valid(node): return
	if not (node.material is ShaderMaterial and (node.material as ShaderMaterial).shader == shader()):
		var material := ShaderMaterial.new(); material.shader = shader(); node.material = material
	(node.material as ShaderMaterial).set_shader_parameter("tint", tint)
	flashes[node.get_instance_id()] = {"node": node, "tick": 0, "life": ticks}
## A short kick of the whole stage: the nodes given move together.
static func kick(nodes: Array, size: float = 2.0, ticks: int = 10) -> void:
	if reduced: return
	_settle_shake()
	shake_nodes = []
	for node: Node2D in nodes:
		if node != null and is_instance_valid(node): shake_nodes.append({"node": node, "home": moves[node.get_instance_id()].home if moves.has(node.get_instance_id()) else node.position})
	shake_size = size; shake_ticks = ticks

static func _offset(m: Dictionary) -> Vector2:
	var t: int = int(m.tick); var life: int = int(m.life); var d: Vector2 = m.dir
	match str(m.kind):
		"lunge":
			if t < 6: return d * 14.0 * sin(t / 6.0 * PI / 2.0)
			if t < 10: return d * 14.0
			return d * 14.0 * (1.0 - float(t - 10) / float(life - 10))
		"strike_jules", "strike_imani", "strike_walt":
			var who: String = str(m.kind).substr(7)
			var lift: float = 0.0
			if who == "imani" and (t >= 6 and t < 12 or t >= 17 and t < 24): lift = -3.0
			if who == "jules" and t >= 8 and t < 28: lift = -2.0
			return Vector2(d.x * strike_push(who, t), lift)
		"flinch":
			var fade: float = 1.0 - float(t) / float(life)
			var shake: float = (2.0 if (t / 2) % 2 == 0 else -2.0) * fade if t > 2 else 0.0
			return d * 6.0 * float(m.strength) * fade * fade + Vector2(shake, 0.0)
		"windup":
			if t < 10: return -d * 4.0 * sin(t / 10.0 * PI / 2.0)
			if t < 15: return -d * 4.0 + d * 12.0 * float(t - 10) / 5.0
			return d * 8.0 * (1.0 - float(t - 15) / float(life - 15))
	return Vector2.ZERO

## Advances every effect by one physics tick.
static func step(reduced_motion: bool) -> void:
	reduced = reduced_motion
	_step_ghosts()
	for id: int in moves.keys():
		var m: Dictionary = moves[id]
		var node: Node2D = m.node
		if not is_instance_valid(node): moves.erase(id); continue
		m.tick = int(m.tick) + 1
		if int(m.tick) >= int(m.life) or reduced:
			node.position = m.home; moves.erase(id)
		else:
			node.position = m.home + _offset(m).round()
			var kind: String = str(m.kind)
			if kind.begins_with("strike_") and node is AnimatedSprite2D:
				var who: String = kind.substr(7)
				(node as AnimatedSprite2D).frame = strike_pose(who, int(m.tick))
				if who == "jules" and int(m.tick) >= 8 and int(m.tick) < 22 and int(m.tick) % 2 == 0: _ghost(node)
	for id: int in flashes.keys():
		var f: Dictionary = flashes[id]
		var item: CanvasItem = f.node
		if not is_instance_valid(item): flashes.erase(id); continue
		f.tick = int(f.tick) + 1
		var amount: float = 0.0 if int(f.tick) >= int(f.life) else (1.0 if int(f.tick) <= 2 else 1.0 - float(int(f.tick) - 2) / float(int(f.life) - 2))
		(item.material as ShaderMaterial).set_shader_parameter("flash", amount * 0.85)
		if int(f.tick) >= int(f.life): flashes.erase(id)
	if shake_ticks > 0:
		shake_ticks -= 1
		var amount: float = shake_size * float(shake_ticks) / 10.0
		var offset: Vector2 = Vector2((1.0 if shake_ticks % 2 == 0 else -1.0) * amount, (1.0 if shake_ticks % 4 < 2 else -1.0) * amount * 0.5).round()
		for s: Dictionary in shake_nodes:
			if not is_instance_valid(s.node): continue
			var node: Node2D = s.node
			var moved: Vector2 = Vector2.ZERO
			if moves.has(node.get_instance_id()): moved = node.position - Vector2(moves[node.get_instance_id()].home)
			node.position = Vector2(s.home) + moved + (offset if shake_ticks > 0 else Vector2.ZERO)
		if shake_ticks == 0: _settle_shake()

## A fading copy of a sprite left behind a dash.
static var ghosts: Array = []
static func _ghost(node: AnimatedSprite2D) -> void:
	if node.get_parent() == null: return
	var tex: Texture2D = node.sprite_frames.get_frame_texture(node.animation, node.frame)
	var g := Sprite2D.new()
	g.texture = tex; g.centered = false; g.offset = node.offset; g.scale = node.scale
	g.position = node.position; g.z_index = node.z_index - 1; g.modulate = Color(1.0, 0.8, 0.75, 0.5)
	node.get_parent().add_child(g)
	ghosts.append({"node": g, "tick": 0})

static func _step_ghosts() -> void:
	for gd: Dictionary in ghosts.duplicate():
		if not is_instance_valid(gd.node): ghosts.erase(gd); continue
		gd.tick = int(gd.tick) + 1
		(gd.node as Sprite2D).modulate.a = 0.5 * (1.0 - float(gd.tick) / 8.0)
		if int(gd.tick) >= 8: (gd.node as Node).queue_free(); ghosts.erase(gd)

static func _settle_shake() -> void:
	for s: Dictionary in shake_nodes:
		if is_instance_valid(s.node) and not moves.has((s.node as Node2D).get_instance_id()): (s.node as Node2D).position = s.home
	shake_nodes = []; shake_ticks = 0

## Puts everything back where it lives (battle start and end).
static func clear() -> void:
	_settle_shake()
	for m: Dictionary in moves.values():
		if is_instance_valid(m.node): (m.node as Node2D).position = m.home
	moves.clear()
	for gd: Dictionary in ghosts:
		if is_instance_valid(gd.node): (gd.node as Node).queue_free()
	ghosts.clear()
	for f: Dictionary in flashes.values():
		if is_instance_valid(f.node) and (f.node as CanvasItem).material is ShaderMaterial: ((f.node as CanvasItem).material as ShaderMaterial).set_shader_parameter("flash", 0.0)
	flashes.clear()
