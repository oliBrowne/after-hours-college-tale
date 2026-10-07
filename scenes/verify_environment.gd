extends SceneTree

func _initialize() -> void:
	var environment = preload("res://scenes/umc_environment.gd").new()
	root.add_child(environment)
	for id in ["U01","U02","U03","U04","U05","U06","U07"]:
		environment.configure(id)
		for tick in 120:
			environment.step(1.0/60.0)
		assert(environment.room_id==id)
		assert(absf(environment.elapsed-2.0)<0.001)
	var claim = preload("res://scenes/claim_actor.gd").new()
	root.add_child(claim)
	for pose in ["idle","tell","active","hit","resolved"]:
		claim.set_pose(pose)
		claim.step(1.0/60.0)
		assert(claim.pose==pose)
	var pin = preload("res://scenes/pin_actor.gd").new()
	root.add_child(pin)
	for pose in ["idle","tell","active","hit","resolved"]:
		pin.set_pose(pose)
		pin.step(1.0/60.0)
		assert(pin.pose==pose)
	var vfx = preload("res://scenes/combat_vfx.gd").new()
	root.add_child(vfx)
	for kind in ["strike","hit","guard","heal","foe_dissolve"]:
		vfx.play(kind,Vector2(100,100),Vector2(480,140),17)
	assert(vfx.effects.size()==5)
	for tick in 120:
		vfx.step(1.0/60.0)
	assert(not vfx.is_active())
	vfx.play("hit",Vector2.ZERO,Vector2(1,1),1)
	vfx.clear()
	assert(not vfx.is_active())
	print("NATIVE_ENVIRONMENT_OK: seven rooms configure/reset/step, CLAIM/Pin Pal poses, deterministic VFX expiry/cleanup.")
	quit(0)
