class_name ClaimNeeds
extends RefCounted
## CLAIM's two concrete needs are independent of conversational Openness.
## Pass the completed production director state, never a presentation counter.

static func create() -> Dictionary:
	return {"tagDelivered": false, "oneReturned": false, "boundaryKept": false}

static func combat_phase(needs: Dictionary, enemy_hp: int, promised: bool = false) -> int:
	# Damage may change attacks/music; it does not satisfy peaceful needs.
	# A newly offered first promise remains achievable after prior damage.
	if promised and not bool(needs.get("tagDelivered", false)): return 0
	return 1 if bool(needs.get("tagDelivered", false)) or enemy_hp <= 110 else 0

static func can_release(needs: Dictionary) -> bool:
	return bool(needs.get("tagDelivered", false)) and bool(needs.get("oneReturned", false)) and bool(needs.get("boundaryKept", false))

static func validate_plan(needs: Dictionary, commands: Array) -> String:
	for command: Dictionary in commands:
		if command.get("kind", "") == "release" and not can_release(needs):
			return "CLAIM needs one carried tag, then one return with a note."
	return ""

static func _marker(pattern: Dictionary, id: int) -> Dictionary:
	for marker: Dictionary in pattern.get("markers", []):
		if int(marker.get("id", -1)) == id: return marker
	return {}

static func record_defense(before: Dictionary, pattern: Dictionary, promised: bool, boundary: bool) -> Dictionary:
	var needs: Dictionary = before.duplicate(true)
	if pattern.get("encounterId", "") != "claim" or not bool(pattern.get("done", false)) or not bool(pattern.get("promiseComplete", false)):
		return needs
	# The boundary alternative is itself a promise, even without a PROMISE action.
	if not promised and not boundary: return needs
	var pickup: Dictionary = _marker(pattern, 0)
	if not bool(pattern.get("carryTag", false)) or not bool(pickup.get("collected", false)): return needs
	if int(pattern.get("phase", -1)) == 0:
		if not promised: return needs
		var destination: Dictionary = _marker(pattern, 1)
		if bool(destination.get("collected", false)) and int(pattern.get("claimSweepPassed", 0)) > 0:
			needs.tagDelivered = true
	elif int(pattern.get("phase", -1)) == 1 and bool(needs.get("tagDelivered", false)):
		var delivery: int = int(pattern.get("delivery", -1))
		if delivery not in [1, 2] or not boundary or not bool(pattern.get("boundary", false)) or not bool(pattern.get("noteLeft", false)): return needs
		var returned: Dictionary = _marker(pattern, delivery)
		var left: Dictionary = _marker(pattern, 3 - delivery)
		if bool(returned.get("collected", false)) and bool(left.get("noted", false)) and not bool(left.get("collected", false)):
			needs.oneReturned = true
			needs.boundaryKept = true
	return needs
