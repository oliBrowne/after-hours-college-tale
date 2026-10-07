class_name NativeIdleMotion
extends RefCounted
## Idle owns two held pixel poses; feet/scale/rotation are never animated.
static func breathing_at(time: float,seed: int=0) -> bool:
	var phase: float=fposmod(time+(seed%17)*0.31,6.0)
	return phase>=4.5 and phase<5.5
static func apply(sprite: AnimatedSprite2D,height: float,time: float,reduced: bool,seed: int=0) -> void:
	NativeCastArt.fit(sprite,height)
	if NativePixelCast.idle_pose(str(sprite.animation)):
		sprite.pause()
		var frame: int=1 if not reduced and sprite.visible and breathing_at(time,seed) else 0
		if sprite.frame!=frame:sprite.frame=frame
		NativeCastArt.fit(sprite,height)
static func reset(sprite: AnimatedSprite2D,height: float) -> void:
	NativeCastArt.fit(sprite,height)
	if NativePixelCast.idle_pose(str(sprite.animation)):sprite.frame=0;sprite.pause()
