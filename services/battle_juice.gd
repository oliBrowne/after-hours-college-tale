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
	for id: int in moves.keys():
		var m: Dictionary = moves[id]
		var node: Node2D = m.node
		if not is_instance_valid(node): moves.erase(id); continue
		m.tick = int(m.tick) + 1
		if int(m.tick) >= int(m.life) or reduced:
			node.position = m.home; moves.erase(id)
		else:
			node.position = m.home + _offset(m).round()
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
	for f: Dictionary in flashes.values():
		if is_instance_valid(f.node) and (f.node as CanvasItem).material is ShaderMaterial: ((f.node as CanvasItem).material as ShaderMaterial).set_shader_parameter("flash", 0.0)
	flashes.clear()
