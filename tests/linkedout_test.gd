extends SceneTree
## Run: Godot --headless --path godot-game --script res://tests/linkedout_test.gd
## LinkedOut: who can connect, what accepting does to the party, the feed, and that every flag
## it writes still saves. The menu itself is exercised by the --qa-linkedout input route.
var checks: int = 0
var failures: int = 0

func _init() -> void:
	_test_people()
	_test_unlock_and_accept()
	_test_growth()
	_test_feed()
	_test_saves()
	_test_references()
	print("LinkedOut: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _all_peaceful() -> Dictionary:
	var f: Dictionary = {}
	for p: Dictionary in LinkedOut.PEOPLE:
		f[str(p.flag)] = str(p.need) if p.has("need") else true
	return f

func _test_people() -> void:
	var seen: Dictionary = {}
	var totals: Dictionary = {"max": 0, "power": 0, "defence": 0, "sync": 0}
	for p: Dictionary in LinkedOut.PEOPLE:
		var id: String = str(p.id)
		_check(not seen.has(id), id + " is listed once")
		seen[id] = true
		_check(LinkedOut.STAT_TEXT.has(str(p.stat)) and int(p.amount) > 0, id + " has a real endorsement")
		_check(not str(p.name).is_empty() and not str(p.headline).is_empty() and not str(p.skill).is_empty(), id + " has a profile")
		_check(not p.has("need") or str(p.need) == "peaceful", id + " only needs a peaceful ending")
		_check(not "—" in str(p.headline) + str(p.skill), id + " text has no em-dashes")
		totals[str(p.stat)] = int(totals[str(p.stat)]) + int(p.amount)
	_check(int(totals.max) <= 48 and int(totals.power) <= 5 and int(totals.defence) <= 3 and int(totals.sync) <= 20, "The whole network stays a small boost: %s" % str(totals))
	_check(LinkedOut.person("walt").name == "Walt" and LinkedOut.person("nobody").is_empty(), "person() finds people by id")

func _test_unlock_and_accept() -> void:
	var f: Dictionary = {}
	_check(LinkedOut.pending(f).is_empty() and LinkedOut.accepted(f).is_empty(), "A fresh save has no requests")
	f.walt_resolution = "forceful"
	_check(LinkedOut.pending(f).is_empty(), "A forceful ending sends no request")
	_check(LinkedOut.viewed_only(f).size() == 1, "...but Walt looked at the profile")
	f.walt_resolution = "peaceful"
	_check(LinkedOut.pending(f).size() == 1 and LinkedOut.viewed_only(f).is_empty(), "A peaceful ending sends one")
	f.met_eli = true
	f.cal_joined = true
	f.dev_met = false
	_check(LinkedOut.pending(f).size() == 3, "Meeting scene characters sends requests too (Walt, Eli, Cal)")
	_check(not LinkedOut.accept(f, "dev") and not LinkedOut.accept(f, "chad") and not LinkedOut.accept(f, "nobody"), "Cannot accept someone who has not connected")
	_check(LinkedOut.accept(f, "walt") and LinkedOut.accepted_id(f, "walt"), "Accepting works")
	_check(not LinkedOut.accept(f, "walt"), "Accepting twice does nothing")
	_check(LinkedOut.pending(f).size() == 2 and LinkedOut.accepted(f).size() == 1, "The request moves from pending to accepted")
	f.li_chad = "yes"
	_check(LinkedOut.accepted(f).size() == 1, "A forged acceptance without the meeting does not count")

func _test_growth() -> void:
	var base: Array = PartyGrowth.apply(BattleRules.initial_party(), {})
	var f: Dictionary = _all_peaceful()
	var pending_max: int = int(PartyGrowth.apply(BattleRules.initial_party(), f)[0].max)
	_check(pending_max == int(PartyGrowth.apply(BattleRules.initial_party(), _milestones_of(f))[0].max), "Pending requests change nothing until accepted")
	LinkedOut.accept(f, "walt")
	_check(int(PartyGrowth.apply(BattleRules.initial_party(), f)[0].max) == pending_max + 4, "Accepting Walt adds his +4 max HP")
	for p: Dictionary in LinkedOut.PEOPLE: LinkedOut.accept(f, str(p.id))
	var grown: Array = PartyGrowth.apply(BattleRules.initial_party(), f)
	var bonus_max: int = LinkedOut.bonus(f, "max")
	for i: int in range(3):
		_check(int(grown[i].max) == int(PartyGrowth.apply(BattleRules.initial_party(), _milestones_of(f))[i].max) + bonus_max, "Member %d gets the max HP bonus" % i)
	_check(int(grown[0].power) == int(base[0].power) + LinkedOut.bonus(f, "power") + _milestone_power(f), "Jules gets the power bonus")
	var joined: Dictionary = {"imani_joined": true, "walt_joined": true}
	var with_net: Dictionary = joined.duplicate()
	with_net.merge({"li_imani": "yes", "imani_joined": true})
	_check(PartyGrowth.starting_sync(with_net) == PartyGrowth.starting_sync(joined) + 5, "SYNC endorsements add to the starting SYNC once")
	_check(PartyGrowth.starting_sync({}) == 0, "No endorsements, no starting SYNC")

# The milestone part of the stats, with the LinkedOut flags removed, for comparison.
func _milestones_of(f: Dictionary) -> Dictionary:
	var kept: Dictionary = {}
	for key: String in f:
		if not key.begins_with("li_"): kept[key] = f[key]
	return kept

func _milestone_power(f: Dictionary) -> int:
	return int(PartyGrowth.apply(BattleRules.initial_party(), _milestones_of(f))[0].power) - int(PartyGrowth.apply(BattleRules.initial_party(), {})[0].power)

func _test_feed() -> void:
	var f: Dictionary = {"walt_resolution": "peaceful", "chip_resolution": "forceful"}
	_check(LinkedOut.feed({}).size() == 1 and str(LinkedOut.feed({})[0]).begins_with("No activity"), "An empty feed says so")
	LinkedOut.accept(f, "walt")
	var posts: Array[String] = LinkedOut.feed(f)
	_check(posts.size() == 2 and posts[0].begins_with("Thrilled to announce") and "Walt" in posts[0] and "+4 max HP" in posts[0], "Accepted connections post a thrilled announcement")
	_check("Chip viewed your profile" in posts[1], "A forceful ending leaves a viewed-your-profile post")
	_check(LinkedOut.views(f) > LinkedOut.views({}), "Profile views go up with the network")
	_check(LinkedOut.summary(f).begins_with("LinkedOut / 1 connections / 0 requests"), "The summary counts")
	_check(NativeLinkedOutMenu.badge(f).is_empty() and NativeLinkedOutMenu.badge({"imani_joined": true}) == " (1 new)", "The pause-menu badge counts new requests")

func _test_saves() -> void:
	var state: Dictionary = NativeState.fresh()
	state.flags = _all_peaceful()
	for p: Dictionary in LinkedOut.PEOPLE: LinkedOut.accept(state.flags, str(p.id))
	state.flags.li_seen = str(LinkedOut.accepted(state.flags).size())
	_check(NativeSaveService.validate_state(state), "A fully connected save validates")

## Val's behavioural questions: a vouching connection skips its question.
func _test_references() -> void:
	var D: GDScript = load("res://core/dodge_box.gd")
	_check(LinkedOut.accepted_ids({"walt_resolution": "peaceful", "li_walt": "yes"}) == ["walt"], "References are the accepted ids")
	var voices: Dictionary = {}
	for refs: Array in [[], ["walt", "encore", "cone", "rook"]]:
		var p: Dictionary = D.create("val", 1234, 0, 0, 2, 30)
		p.references = refs
		var vouched: Dictionary = {}
		var projectiles: int = 0
		while not p.done:
			D.step(p, Vector2.ZERO, false, 1.0, false, false, false)
			if "VOUCHES FOR YOU" in str(p.banner): vouched[str(p.banner)] = true
			if int(p.clock) > int(p.leadIn) + 560: projectiles = maxi(projectiles, p.bullets.size())
		voices[refs.size()] = [vouched.size(), projectiles]
	_check(int(voices[0][0]) == 0, "Without references nobody vouches")
	_check(int(voices[4][0]) == 4, "Four references: four people vouch (%s)" % str(voices[4][0]))
	_check(int(voices[4][1]) == 0, "Once every question is vouched for, the box is empty at the end")
