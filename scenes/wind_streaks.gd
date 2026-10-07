class_name NativeWindStreaks
extends Node2D
## Wind blowing across the foe side of the Hold the Light fight, so the lantern-bearer there reads as
## the one being protected and the wind as the thing being faced. Pure drawing; reduced motion holds it still.
var reduced: bool = false
var elapsed: float = 0.0

func _process(delta: float) -> void:
	if not visible: return
	elapsed += delta
	queue_redraw()

func _draw() -> void:
	var t: float = 0.0 if reduced else elapsed
	for i: int in range(9):
		var lane: float = 74.0 + float(i) * 9.0 + float((i * 7) % 5) * 2.0
		var length: float = 34.0 + float((i * 13) % 6) * 9.0
		var speed: float = 150.0 + float((i * 29) % 5) * 30.0
		var x: float = 700.0 - fmod(t * speed + float(i) * 83.0, 420.0)
		var edge: float = clampf(minf(x - 300.0, 660.0 - x) / 40.0, 0.0, 1.0)
		if edge <= 0.0: continue
		var y: float = roundf(lane + sin(t * 2.0 + float(i)) * 2.0)
		draw_line(Vector2(roundf(x), y + 1.0), Vector2(roundf(x + length), y + 1.0), Color("0d101c", 0.45 * edge), 3.0)
		draw_line(Vector2(roundf(x), y), Vector2(roundf(x + length), y), Color("eef5fb", 0.95 * edge), 2.0)
		draw_line(Vector2(roundf(x + length), y), Vector2(roundf(x + length + 6.0), y - 4.0), Color("eef5fb", 0.95 * edge), 2.0)
