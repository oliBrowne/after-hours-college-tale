extends SceneTree
## Run: Godot --headless --path godot-game --script res://tests/intern_insider_test.gd
## Intern Insider: postings unlock from story flags, reading is tracked, and the flags still save.
var checks: int = 0
var failures: int = 0

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _init() -> void:
	var f: Dictionary = {}
	_check(InternInsider.listed(f).size() == 1, "fresh game lists only the always-open posting")
	_check(InternInsider.unread(f).size() == 1, "one unread at start")
	_check(not InternInsider.mark_read(f, "talent"), "locked posting cannot be read")
	_check(not f.has("ii_talent"), "locked read writes no flag")
	_check(InternInsider.mark_read(f, "sound"), "open posting reads")
	_check(InternInsider.unread(f).is_empty(), "nothing unread afterwards")
	f["chip_resolution"] = "peaceful"
	f["chapter3_complete"] = true
	_check(InternInsider.listed(f).size() == 3, "story flags unlock postings")
	_check(NativeInternInsiderMenu.badge(f) == " (2 new)", "badge counts unread")
	var g: Dictionary = {"buff_bucks": "5"}
	_check(InternInsider.apply(g, "stage") == 0, "locked posting cannot be applied to")
	_check(InternInsider.apply(g, "sound") == 10 and g.buff_bucks == "15", "Easy Apply pays 10 Buff Bucks")
	_check(InternInsider.apply(g, "sound") == 0 and g.buff_bucks == "15", "applying twice pays nothing")
	_check(InternInsider.status(g, InternInsider.posting("sound")).begins_with("Application sent"), "under review before the story catches up")
	g["imani_joined"] = true
	_check(InternInsider.status(g, InternInsider.posting("sound")) == "Offer received", "Imani joining lands the sound offer")
	_check(InternInsider.read_id(g, "sound") and InternInsider.mark_read(g, "sound") and g["ii_sound"] == "applied", "reading never downgrades an application")
	var k: Dictionary = {"visited_P01": true}
	_check(InternInsider.listed(k).any(func(p: Dictionary) -> bool: return p.id == "founder"), "visiting Kyle's office lists the DISRUPTR posting")
	for p: Dictionary in InternInsider.POSTINGS:
		_check(not str(p.logo).is_empty(), "posting %s has a logo" % str(p.id))
		_check(not str(p.tip).is_empty() and not str(p.blurb).is_empty(), "posting %s has text" % str(p.id))
		f["ii_" + str(p.id)] = "read"
	var data: Dictionary = {"flags": f}
	for v: Variant in f.values():
		_check(v is bool or v is String, "flag value type is bool or String")
	print("InternInsider: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)
