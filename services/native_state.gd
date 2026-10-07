class_name NativeState
extends RefCounted

static func fresh(settings: Dictionary = {}) -> Dictionary:
	return {"version": 1, "contentVersion": "0.2-native", "room": "U01", "x": 96.0, "y": 258.0, "party": BattleRules.initial_party(), "inventory": {"granola": 2, "cocoa": 1, "thermos": 1}, "flags": {}, "seed": 271828, "settings": preferences() if settings.is_empty() else normalize_audio_settings(settings), "playtime": 0.0}

static func normalize_audio_settings(settings: Dictionary) -> Dictionary:
	# Pure/idempotent migration: capture ORIGINAL legacy Effects before filling
	# either independent field. Presence, not truthiness, preserves explicit zero.
	var normalized: Dictionary = settings.duplicate(true)
	var original_effects: float = 0.5
	var legacy_effects: Variant = settings.get("effects", 0.5)
	if (legacy_effects is float or legacy_effects is int) and is_finite(float(legacy_effects)):
		original_effects = float(legacy_effects)
	# Keep invalid original fields intact so validation still rejects corrupt data.
	if not normalized.has("voices"):
		normalized.voices = original_effects
	if not normalized.has("ambience"):
		normalized.ambience = original_effects * 0.65
	return normalized

static func preferences() -> Dictionary:
	return {"music": 0.35, "effects": 0.5, "voices": 0.5, "ambience": 0.325, "blips": true, "instant": false, "large": false, "assist": 1.0, "damageAssist": false, "autoTiming": false, "reducedMotion": false, "bindings": {}}

