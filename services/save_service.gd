class_name NativeSaveService
extends RefCounted
## Versioned plain JSON only. A successful save means verified file promotion.
## Backup and rollback files survive failed promotion and interrupted replacement.
const VERSION: int = 1
const CONTENT_VERSION: String = "0.2-native"
const MAX_BYTES: int = 2097152
const SLOTS: Array[String] = ["auto", "slot1", "slot2", "slot3"]
var base_path: String
var last_error: String = ""
static var supported_rooms: Dictionary = {}

func _init(directory: String = "user://saves") -> void:
	base_path = directory.trim_suffix("/")

static func _number(value: Variant) -> bool:
	return (value is float or value is int) and is_finite(float(value))

static func _integer(value: Variant, minimum: int, maximum: int) -> bool:
	return _number(value) and float(value) >= minimum and float(value) <= maximum and float(value) == floorf(float(value))

static func validate_settings(value: Variant) -> bool:
	if not value is Dictionary:
		return false
	var settings: Dictionary = value
	# Old preference/save dictionaries remain valid; Main supplies legacy gains.
	for key: String in ["voices", "ambience"]:
		if settings.has(key) and (not _number(settings[key]) or float(settings[key]) < 0.0 or float(settings[key]) > 1.0):
			return false
	for key: String in ["music", "effects"]:
		if not _number(settings.get(key)) or float(settings[key]) < 0.0 or float(settings[key]) > 1.0:
			return false
	for key: String in ["blips", "instant", "large", "damageAssist", "autoTiming", "reducedMotion"]:
		if not settings.get(key) is bool:
			return false
	if not _number(settings.get("assist")) or not float(settings.assist) in [1.0, 0.85, 0.7]:
		return false
	if not settings.get("bindings") is Dictionary:
		return false
	var used: Dictionary = {}
	var bindings: Dictionary = settings.bindings
	for key: Variant in bindings:
		if not (key is String or key is StringName) or not str(key) in ["move_up", "move_down", "move_left", "move_right", "up", "down", "left", "right", "confirm", "cancel", "menu", "run"]:
			return false
		var binding: Variant = bindings[key]
		if not (_integer(binding, 1, 4294967295) or (binding is String and not str(binding).is_empty() and str(binding).length() <= 40)):
			return false
		if used.has(binding):
			return false
		used[binding] = true
	if settings.has("barks") and not settings.barks is bool:
		return false
	return true

static func validate_state(value: Variant) -> bool:
	if not value is Dictionary:
		return false
	var state: Dictionary = value
	if not _integer(state.get("version"), VERSION, VERSION) or state.get("contentVersion") != CONTENT_VERSION:
		return false
	if supported_rooms.is_empty():supported_rooms=JSON.parse_string(FileAccess.get_file_as_string("res://content/rooms.json"))
	if not supported_rooms.has(state.get("room")):
		return false
	if not _number(state.get("x")) or float(state.x) < 16.0 or float(state.x) > float(supported_rooms[state.room].dimensions[0])-16.0:
		return false
	if not _number(state.get("y")) or float(state.y) < 16.0 or float(state.y) > float(supported_rooms[state.room].dimensions[1])-16.0:
		return false
	if not state.get("party") is Array or state.party.size() != 3:
		return false
	var ids: Array[String] = ["jules", "imani", "cal"]
	for index: int in range(3):
		if not state.party[index] is Dictionary:
			return false
		var member: Dictionary = state.party[index]
		if member.get("id") not in (["cal", "walt"] if index == 2 else [ids[index]]) or not _integer(member.get("max"), 1, 999):
			return false
		if not _integer(member.get("hp"), 0, int(member.max)) or not _integer(member.get("power"), 1, 99) or not _integer(member.get("defence"), 0, 99):
			return false
	if not state.get("inventory") is Dictionary:
		return false
	var inventory: Dictionary = state.inventory
	var total: int = 0
	for key: String in ["granola", "cocoa", "thermos"]:
		if not _integer(inventory.get(key), 0, 8):
			return false
		total += int(inventory[key])
	if inventory.size() != 3 or total > 8:
		return false
	if not state.get("flags") is Dictionary:
		return false
	for key: Variant in state.flags:
		if not (key is String or key is StringName) or not (state.flags[key] is bool or state.flags[key] is String):
			return false
	if not _integer(state.get("seed"), 0, 4294967295) or not _number(state.get("playtime")) or float(state.playtime) < 0.0:
		return false
	return validate_settings(state.get("settings"))

func _absolute(path: String) -> String:
	return ProjectSettings.globalize_path(path)

func _slot_path(slot: String) -> String:
	return base_path.path_join(slot + ".json")

func _parse(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"error": "File does not exist."}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"error": "Could not open file: " + error_string(FileAccess.get_open_error())}
	if file.get_length() > MAX_BYTES:
		file.close()
		return {"error": "Save file exceeds the supported size."}
	var text: String = file.get_as_text()
	file.close()
	var json: JSON = JSON.new()
	var result: Error = json.parse(text)
	if result != OK:
		return {"error": "Invalid JSON at line %d: %s" % [json.get_error_line(), json.get_error_message()]}
	return {"data": json.data}

func _newer(parsed: Dictionary) -> bool:
	var data: Variant = parsed.get("data")
	if not data is Dictionary or not _number(data.get("version")):
		return false
	if float(data.version) > VERSION:
		return true
	# Content updates may retain the data schema while adding unsupported rooms.
	return float(data.version) == VERSION and data.get("contentVersion") is String and data.contentVersion != CONTENT_VERSION

func _valid_file(path: String) -> bool:
	var parsed: Dictionary = _parse(path)
	return parsed.has("data") and validate_state(parsed.data)

func _write_json(path: String, state: Dictionary) -> Error:
	var text: String = JSON.stringify(state, "\t")
	if text.to_utf8_buffer().size() > MAX_BYTES:
		return ERR_INVALID_DATA
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(text)
	file.flush()
	var result: Error = file.get_error()
	file.close()
	if result != OK:
		return result
	return OK if _valid_file(path) else ERR_FILE_CORRUPT

func _remove(path: String) -> Error:
	return DirAccess.remove_absolute(_absolute(path)) if FileAccess.file_exists(path) else OK

func _rename(source: String, destination: String) -> Error:
	return DirAccess.rename_absolute(_absolute(source), _absolute(destination))

func _replace(candidate: String, destination: String, rollback: String) -> Error:
	# Caller has verified candidate and preserved any previous-good snapshot.
	if _newer(_parse(rollback)):
		return ERR_INVALID_DATA
	if not FileAccess.file_exists(destination) and _valid_file(rollback):
		var restore_result: Error = _rename(rollback, destination)
		if restore_result != OK:
			return restore_result
	if FileAccess.file_exists(rollback):
		var remove_result: Error = _remove(rollback)
		if remove_result != OK:
			return remove_result
	var had_destination: bool = FileAccess.file_exists(destination)
	if had_destination:
		var move_result: Error = _rename(destination, rollback)
		if move_result != OK:
			return move_result
	var promote_result: Error = _rename(candidate, destination)
	if promote_result != OK:
		if had_destination:
			# If rollback itself cannot be restored, keep it for load_slot recovery.
			_rename(rollback, destination)
		return promote_result
	if not _valid_file(destination):
		_remove(destination)
		if had_destination:
			_rename(rollback, destination)
		return ERR_FILE_CORRUPT
	return OK

func _fail(code: Error, message: String) -> Error:
	last_error = message + ": " + error_string(code)
	return code

func save(slot: String, state: Dictionary) -> Error:
	last_error = ""
	if not slot in SLOTS or not validate_state(state):
		return _fail(ERR_INVALID_DATA, "Invalid slot or state; no save was changed")
	var record: Dictionary = state.duplicate(true)
	var primary: String = _slot_path(slot)
	var backup: String = primary + ".bak"
	var temporary: String = primary + ".tmp"
	var rollback: String = primary + ".rollback"
	for path: String in [primary, rollback, backup, backup + ".rollback"]:
		if _newer(_parse(path)):
			return _fail(ERR_INVALID_DATA, "Newer or unsupported save retained; choose a different slot")
	var directory_result: Error = DirAccess.make_dir_recursive_absolute(_absolute(base_path))
	if directory_result != OK:
		return _fail(directory_result, "Could not create save directory")
	var write_result: Error = _write_json(temporary, record)
	if write_result != OK:
		return _fail(write_result, "Temporary save write or validation failed")
	var previous: Dictionary = {}
	for path: String in [primary, rollback, backup, backup + ".rollback"]:
		var parsed: Dictionary = _parse(path)
		if parsed.has("data") and validate_state(parsed.data):
			previous = parsed.data
			break
	if not previous.is_empty():
		var backup_temporary: String = backup + ".tmp"
		write_result = _write_json(backup_temporary, previous)
		if write_result != OK:
			return _fail(write_result, "Previous-good backup write failed; primary retained")
		var backup_result: Error = _replace(backup_temporary, backup, backup + ".rollback")
		if backup_result != OK:
			return _fail(backup_result, "Previous-good backup promotion failed; primary retained")
	var promote_result: Error = _replace(temporary, primary, rollback)
	if promote_result != OK:
		return _fail(promote_result, "Save promotion failed; previous-good data retained")
	# At least one validated promoted primary now exists; old staging is disposable.
	_remove(rollback)
	_remove(backup + ".rollback")
	return OK

func load_slot(slot: String) -> Dictionary:
	if not slot in SLOTS:
		return {"error": "Unknown save slot."}
	var primary: String = _slot_path(slot)
	var parsed: Dictionary = _parse(primary)
	if _newer(parsed):
		return {"error": "Save belongs to a newer or unsupported version. Original retained."}
	if parsed.has("data") and validate_state(parsed.data):
		return {"state": parsed.data.duplicate(true), "backup": false}
	for path: String in [primary + ".rollback", primary + ".bak", primary + ".bak.rollback"]:
		var fallback: Dictionary = _parse(path)
		if _newer(fallback):
			return {"error": "Recovery file belongs to a newer or unsupported version. Original retained."}
		if fallback.has("data") and validate_state(fallback.data):
			return {"state": fallback.data.duplicate(true), "backup": true}
	return {"error": "No valid checkpoint in this slot. Corrupt and unsupported files are retained."}

func import_file(path: String) -> Dictionary:
	var parsed: Dictionary = _parse(path)
	if not parsed.has("data") or not validate_state(parsed.data):
		return {"error": str(parsed.get("error", "Unsupported or corrupt save; import rejected."))}
	return {"state": parsed.data.duplicate(true), "backup": false}

func export_file(path: String, state: Dictionary) -> Error:
	last_error = ""
	if not validate_state(state):
		return _fail(ERR_INVALID_DATA, "Export rejected; invalid state")
	var existing: Dictionary = _parse(path)
	if _newer(existing):
		return _fail(ERR_INVALID_DATA, "Newer export retained; choose another filename")
	var temporary: String = path + ".tmp"
	var result: Error = _write_json(temporary, state.duplicate(true))
	if result != OK:
		return _fail(result, "Export temporary write failed")
	result = _replace(temporary, path, path + ".rollback")
	if result == OK:
		_remove(path + ".rollback")
	else:
		last_error = "Export replacement failed: " + error_string(result)
	return result
