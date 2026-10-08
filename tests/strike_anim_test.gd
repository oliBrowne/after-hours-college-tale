extends SceneTree
## Each party member's strike choreography: valid poses, starts and ends at home, reaches the foe by the hit tick.
func _init() -> void:
	var failures: int = 0
	for id: String in ["jules", "imani", "walt"]:
		for t: int in range(46):
			var pose: int = NativeBattleJuice.strike_pose(id, t)
			if pose < 0 or pose > 4: failures += 1; print("bad pose ", id, " ", t)
		if absf(NativeBattleJuice.strike_push(id, 0)) > 0.01: failures += 1; print("start off home ", id)
		if absf(NativeBattleJuice.strike_push(id, 45)) > 6.0: failures += 1; print("end off home ", id)
		if NativeBattleJuice.strike_push(id, 21) < 20.0: failures += 1; print("no reach at the hit ", id)
		if NativeBattleJuice.strike_pose(id, 21) != 3: failures += 1; print("not in the hit pose at the hit ", id)
	print("Strike animation failures: ", failures)
	quit(1 if failures > 0 else 0)
