class_name NativeIdleMotion
extends RefCounted
## Idle owns held pixel poses; feet/scale/rotation are never animated. Besides breathing, sprites
## with extra idle art (NativeIdleArt) blink every few seconds and Walt's lantern sways (their
## idle poses are fidget_* one-shots played by NativeNpcLife). Each sprite runs on its own rhythm.
static func breathing_at(time: float,seed: int=0) -> bool:
	var phase: float=fposmod(time+(seed%17)*0.31,6.0)
	return phase>=4.5 and phase<5.5
## The idle frame to hold at this moment: base 0, breathing 1, or one of the extras.
static func frame_at(extras: Dictionary,time: float,seed: int,breathing: bool) -> int:
	var s: int=absi(seed)%101
	if extras.has("blink") and fposmod(time+float(s)*0.21,3.2+float(s%4)*0.4)<0.13:return int(extras.blink)
	var sway: Array=extras.get("sway",[])
	if not sway.is_empty():return int(sway[(int(time*2.0)+s)%sway.size()])
	return 1 if breathing else 0
static func apply(sprite: AnimatedSprite2D,height: float,time: float,reduced: bool,seed: int=0) -> void:
	NativeCastArt.fit(sprite,height)
	if NativePixelCast.idle_pose(str(sprite.animation)):
		sprite.pause()
		var breathing: bool=not reduced and sprite.visible and breathing_at(time,seed)
		var frame: int=1 if breathing else 0
		if not reduced and str(sprite.animation)=="idle_down" and sprite.sprite_frames.has_meta("idle_extras"):
			frame=frame_at(sprite.sprite_frames.get_meta("idle_extras"),time,seed,breathing)
		if sprite.frame!=frame:sprite.frame=frame
		NativeCastArt.fit(sprite,height)
static func reset(sprite: AnimatedSprite2D,height: float) -> void:
	NativeCastArt.fit(sprite,height)
	if NativePixelCast.idle_pose(str(sprite.animation)):sprite.frame=0;sprite.pause()
