extends SceneTree
const Saves = preload("res://services/save_service.gd")
const Rules = preload("res://core/battle_rules.gd")
const ROOT: String = "res://../work/godot-save-qa"
var checks: int = 0
var failures: int = 0

class WriteFailure:
	extends "res://services/save_service.gd"
	func _write_json(_path: String, _state: Dictionary) -> Error:
		return ERR_FILE_CANT_WRITE

class CorruptTemporary:
	extends "res://services/save_service.gd"
	func _write_json(path: String, _state: Dictionary) -> Error:
		var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
		if file == null:
			return FileAccess.get_open_error()
		file.store_string("{broken")
		file.close()
		return ERR_FILE_CORRUPT

class PromotionFailure:
	extends "res://services/save_service.gd"
	func _rename(source: String, destination: String) -> Error:
		if source.ends_with("auto.json.tmp") and destination.ends_with("auto.json"):
			return ERR_FILE_CANT_WRITE
		return super._rename(source, destination)

class RestoreFailure:
	extends "res://services/save_service.gd"
	func _rename(source: String, destination: String) -> Error:
		if destination.ends_with("auto.json") and (source.ends_with(".tmp") or source.ends_with(".rollback")):
			return ERR_FILE_CANT_WRITE
		return super._rename(source, destination)

class BackupFailure:
	extends "res://services/save_service.gd"
	func _rename(source: String, destination: String) -> Error:
		if source.ends_with(".bak.tmp"):
			return ERR_FILE_CANT_WRITE
		return super._rename(source, destination)

func _init() -> void:
	_test_validation()
	_test_files()
	_test_failures()
	print("Godot native saves: %d checks, %d failures" % [checks, failures])
	quit(0 if failures == 0 else 1)

func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("FAIL: " + label)

func _state() -> Dictionary:
	return {"version": 1, "contentVersion": "0.2-native", "room": "U01", "x": 96.0, "y": 258.0, "party": Rules.initial_party(), "inventory": {"granola": 2, "cocoa": 1, "thermos": 1}, "flags": {}, "seed": 271828, "playtime": 0.0, "settings": {"music": 0.35, "effects": 0.5, "blips": true, "instant": false, "large": false, "assist": 1.0, "damageAssist": false, "autoTiming": false, "reducedMotion": false, "bindings": {}}}

func _test_validation() -> void:
	_check(Saves.validate_state(_state()), "Canonical native fresh state accepted")
	var roundtrip: Variant = JSON.parse_string(JSON.stringify(_state()))
	_check(Saves.validate_state(roundtrip), "JSON integral floating-point numbers accepted")
	_check(not Saves.validate_state(null) and not Saves.validate_state([]), "Only a plain state dictionary accepted")
	for field: String in ["version", "contentVersion", "room", "party", "inventory", "flags", "settings", "seed", "playtime", "x", "y"]:
		var missing: Dictionary = _state()
		missing.erase(field)
		_check(not Saves.validate_state(missing), "Missing required field rejected: " + field)
	var state: Dictionary = _state()
	state.settings = {}
	_check(not Saves.validate_state(state), "Malformed settings cannot enter UI")
	state = _state()
	state.party[0].erase("power")
	_check(not Saves.validate_state(state), "Missing combat stat rejected")
	state = _state()
	state.party[0].hp = 85
	_check(not Saves.validate_state(state), "HP above max rejected")
	state = _state()
	state.party[0].hp = 0.5
	_check(not Saves.validate_state(state), "Fractional HP rejected")
	state = _state()
	state.party[0].hp = 0
	_check(Saves.validate_state(state), "Downed party member is a valid checkpoint")
	state = _state()
	state.flags.bad = {"object": true}
	_check(not Saves.validate_state(state), "Structured arbitrary flag rejected")
	state = _state()
	state.flags.flyer_resolution = "peaceful"
	state.flags.booth_seen = true
	_check(Saves.validate_state(state), "Named string and boolean outcomes accepted")
	state = _state()
	state.inventory.granola = 9
	_check(not Saves.validate_state(state), "Consumable cap rejected")
	state = _state()
	state.inventory.granola = 8
	_check(not Saves.validate_state(state), "Total inventory cap rejected")
	state = _state()
	state.seed = 1.5
	_check(not Saves.validate_state(state), "Fractional seed rejected")
	state = _state()
	state.seed = 4294967296
	_check(not Saves.validate_state(state), "Seed outside uint32 rejected")
	state = _state()
	state.playtime = -1.0
	_check(not Saves.validate_state(state), "Negative playtime rejected")
	state = _state()
	state.x = NAN
	_check(not Saves.validate_state(state), "Non-finite coordinate rejected")
	state = _state()
	state.settings.bindings = {"confirm": KEY_Z, "cancel": KEY_Z}
	_check(not Saves.validate_state(state), "Duplicate physical key binding rejected")
	state.settings.bindings = {"confirm": KEY_Z, "cancel": KEY_X}
	_check(Saves.validate_state(state), "Native physical key bindings accepted")
	state.settings.bindings = {"move_up": KEY_W, "move_down": KEY_S, "move_left": KEY_A, "move_right": KEY_D, "confirm": KEY_Z, "cancel": KEY_X}
	_check(Saves.validate_state(state), "Canonical native move actions accepted")
	for assist: float in [1.0, 0.85, 0.7]:
		state.settings.assist = assist
		_check(Saves.validate_state(state), "Supported assist accepted: " + str(assist))
	state.settings.assist = 0.0
	_check(not Saves.validate_state(state), "Zero assist cannot freeze progression")

func _directory(name: String) -> String:
	var path: String = ROOT.path_join(name)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path))
	# Delete only explicitly known test file names inside this isolated test folder.
	for slot: String in ["auto", "slot1", "slot2", "slot3", "export"]:
		for suffix: String in [".json", ".json.tmp", ".json.rollback", ".json.bak", ".json.bak.tmp", ".json.bak.rollback"]:
			var file: String = path.path_join(slot + suffix)
			if FileAccess.file_exists(file):
				DirAccess.remove_absolute(ProjectSettings.globalize_path(file))
	return path

func _raw(path: String, text: String) -> void:
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		_check(false, "Test fixture writable: " + path)
		return
	file.store_string(text)
	file.close()

func _read(path: String) -> String:
	return FileAccess.get_file_as_string(path)

func _same(actual: Dictionary, expected: Dictionary) -> bool:
	# JSON represents all numbers as doubles and cannot retain typed Array metadata.
	return JSON.parse_string(JSON.stringify(actual)) == JSON.parse_string(JSON.stringify(expected))

func _test_files() -> void:
	var path: String = _directory("normal")
	var saves: RefCounted = Saves.new(path)
	var state: Dictionary = _state()
	_check(saves.save("auto", state) == OK, "First checkpoint writes and promotes")
	var loaded: Dictionary = Saves.new(path).load_slot("auto")
	_check(loaded.has("state") and _same(loaded.state, state) and not loaded.backup, "Fresh process service reloads identical checkpoint")
	loaded.state.party[0].hp = 1
	_check(saves.load_slot("auto").state.party[0].hp == 84, "Returned state cannot mutate disk checkpoint")
	var next: Dictionary = _state()
	next.room = "U04"
	next.flags.flyer_resolution = "peaceful"
	next.inventory.granola = 1
	next.party[0].hp = 60
	_check(saves.save("auto", next) == OK, "Encounter outcome checkpoint promotes")
	_check(_same(saves.load_slot("auto").state, next), "Party, consumables and named outcome survive reload")
	_check(_same(JSON.parse_string(_read(path.path_join("auto.json.bak"))), state), "Immediately previous-good checkpoint retained")
	_raw(path.path_join("auto.json"), "{corrupt")
	loaded = saves.load_slot("auto")
	_check(loaded.has("state") and _same(loaded.state, state) and loaded.backup, "Corrupt primary recovers valid previous-good backup")
	_check(_read(path.path_join("auto.json")) == "{corrupt", "Recovery preserves original corruption for export")
	_check(saves.save("auto", next) == OK, "Saving recovered state repairs primary safely")
	_check(_same(JSON.parse_string(_read(path.path_join("auto.json.bak"))), state), "Repair does not replace good backup with corrupt primary")
	_check(saves.load_slot("slot3").has("error"), "Missing manual slot reports clear error")
	_check(saves.save("../escape", state) == ERR_INVALID_DATA, "Slot path traversal rejected")
	var invalid: Dictionary = _state()
	invalid.room = "missing"
	var before: String = _read(path.path_join("auto.json"))
	_check(saves.save("auto", invalid) == ERR_INVALID_DATA and _read(path.path_join("auto.json")) == before, "Invalid snapshot cannot overwrite good save")
	var future: Dictionary = _state()
	future.version = 2
	_raw(path.path_join("slot1.json"), JSON.stringify(future))
	before = _read(path.path_join("slot1.json"))
	_check(saves.load_slot("slot1").has("error"), "Unsupported newer checkpoint is not silently downgraded")
	_check(saves.save("slot1", state) == ERR_INVALID_DATA and _read(path.path_join("slot1.json")) == before, "Newer primary retained on write")
	future.version = 1
	future.contentVersion = "0.3-native"
	_raw(path.path_join("slot1.json"), JSON.stringify(future))
	before = _read(path.path_join("slot1.json"))
	_check(saves.save("slot1", state) == ERR_INVALID_DATA and _read(path.path_join("slot1.json")) == before, "Unknown content version retained even with same schema")
	_check(saves.load_slot("slot1").has("error"), "Unsupported content version reports error without downgrade")
	_raw(path.path_join("slot2.json.tmp"), JSON.stringify(next))
	_check(saves.load_slot("slot2").has("error"), "Uncommitted temporary snapshot never loads")
	_raw(path.path_join("slot2.json.rollback"), JSON.stringify(state))
	loaded = saves.load_slot("slot2")
	_check(loaded.has("state") and _same(loaded.state, state) and loaded.backup, "Interrupted primary rename recovers rollback snapshot")
	_check(saves.save("slot2", next) == OK and _same(saves.load_slot("slot2").state, next), "Interrupted replacement can resume safely")
	_check(saves.export_file(path.path_join("export.json"), next) == OK, "Portable export validates and promotes")
	_check(_same(saves.import_file(path.path_join("export.json")).state, next), "Portable import restores full state")
	_raw(path.path_join("export.json"), "not JSON")
	_check(saves.import_file(path.path_join("export.json")).has("error"), "Malformed import rejected")
	_raw(path.path_join("export.json"), JSON.stringify(future))
	_check(saves.import_file(path.path_join("export.json")).has("error") and saves.export_file(path.path_join("export.json"), state) == ERR_INVALID_DATA, "Newer import/export file retained")

func _test_failures() -> void:
	for failure_kind: String in ["write", "corrupt", "promote", "restore", "backup"]:
		var path: String = _directory(failure_kind)
		var normal: RefCounted = Saves.new(path)
		var state: Dictionary = _state()
		_check(normal.save("auto", state) == OK, "Failure fixture established: " + failure_kind)
		var failing: RefCounted
		match failure_kind:
			"write": failing = WriteFailure.new(path)
			"corrupt": failing = CorruptTemporary.new(path)
			"promote": failing = PromotionFailure.new(path)
			"restore": failing = RestoreFailure.new(path)
			"backup": failing = BackupFailure.new(path)
		var next: Dictionary = _state()
		next.flags.flyer_resolution = "forceful"
		_check(failing.save("auto", next) != OK and not failing.last_error.is_empty(), "Failure is reported before success: " + failure_kind)
		var recovered: Dictionary = normal.load_slot("auto")
		_check(recovered.has("state") and _same(recovered.state, state), "Previous-good remains recoverable after failure: " + failure_kind)

