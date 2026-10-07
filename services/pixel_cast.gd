class_name NativePixelCast
extends RefCounted
## Consumer-sized pixel textures; raw generated art is never modified.
static var frames_cache: Dictionary={}
static var texture_cache: Dictionary={}
static var portrait_cache: Dictionary={}
static var trim_cache: Dictionary={}
static var breathing_cache: Dictionary={}
static func source_image(texture: Texture2D) -> Image:
	var image: Image=texture.atlas.get_image().get_region(Rect2i(texture.region)) if texture is AtlasTexture else texture.get_image()
	image.convert(Image.FORMAT_RGBA8)
	if texture is AtlasTexture:
		if trim_cache.is_empty():trim_cache=JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/consumer-trims-v1.json"))
		var r: Rect2i=Rect2i(texture.region)
		var key: String=texture.atlas.resource_path+"|%d,%d,%d,%d"%[r.position.x,r.position.y,r.size.x,r.size.y]
		for rect: Array in trim_cache.get(key,[]):image.fill_rect(Rect2i(rect[0],rect[1],rect[2],rect[3]),Color.TRANSPARENT)
	return image
static func crisp(image: Image) -> void:
	for y: int in range(image.get_height()):
		for x: int in range(image.get_width()):
			var color: Color=image.get_pixel(x,y)
			color.a=1.0 if color.a>=0.5 else 0.0
			image.set_pixel(x,y,color)
static func native_image(texture: Texture2D,height: int,standing: float) -> Image:
	var image: Image=source_image(texture)
	var scale: float=height/maxf(1.0,standing)
	var source: Image=image.duplicate() if NativeCleanArt.dumping() else null
	image.resize(maxi(1,roundi(image.get_width()*scale)),maxi(1,roundi(image.get_height()*scale)),Image.INTERPOLATE_NEAREST)
	crisp(image)
	return NativeCleanArt.swap(image,source)
static func pivot(texture: Texture2D,height: int,standing: float) -> Vector2i:
	return Vector2i((Vector2(texture.get_meta("foot",Vector2(texture.get_width()/2.0,texture.get_height())))*(height/maxf(1.0,standing))).round())
static func make_texture(image: Image,foot: Vector2i,height: int,explicit: bool) -> Texture2D:
	var texture:=ImageTexture.create_from_image(image)
	texture.set_meta("foot",Vector2(foot));texture.set_meta("body_height",height);texture.set_meta("explicit_direction",explicit);texture.set_meta("native_pixels",true)
	return texture
static func texture(raw: Texture2D,height: int,standing: float=-1.0) -> Texture2D:
	if raw==null:return null
	if raw.get_meta("native_pixels",false) and int(raw.get_meta("body_height"))==height:return raw
	if standing<=0:standing=float(raw.get_meta("body_height",raw.get_height()))
	var key: String=str(raw.get_instance_id())+"/"+str(height)+"/"+str(standing)
	if texture_cache.has(key):return texture_cache[key]
	var image: Image=native_image(raw,height,standing);var foot: Vector2i=pivot(raw,height,standing)
	var padded:=Image.create(image.get_width()+4,image.get_height()+4,false,Image.FORMAT_RGBA8)
	padded.blit_rect(image,Rect2i(Vector2i.ZERO,image.get_size()),Vector2i(2,2))
	var result: Texture2D=make_texture(padded,foot+Vector2i(2,2),height,raw.get_meta("explicit_direction",false))
	result.set_meta("source_asset",raw.atlas.resource_path if raw is AtlasTexture else raw.resource_path)
	texture_cache[key]=result;return result
static func breathing(texture: Texture2D) -> Texture2D:
	# A held one-pixel upper-body pose; legs and the feet remain exactly identical.
	# The integer canvas does not rotate, stretch, or accumulate fractional drift.
	var key: int=texture.get_instance_id()
	if breathing_cache.has(key):return breathing_cache[key]
	var image: Image=texture.get_image();var result: Image=image.duplicate()
	var foot: Vector2i=Vector2i(texture.get_meta("foot"))
	var split: int=clampi(foot.y-roundi(float(texture.get_meta("body_height"))*0.30),2,image.get_height()-1)
	var upper: Rect2i=Rect2i(0,1,image.get_width(),split-1)
	result.blit_rect(image,upper,Vector2i.ZERO)
	var output: Texture2D=make_texture(result,foot,int(texture.get_meta("body_height")),texture.get_meta("explicit_direction",false))
	output.set_meta("source_asset",texture.get_meta("source_asset",""))
	breathing_cache[key]=output;return output
static func idle_pose(name: String) -> bool:
	return name.begins_with("idle") or name=="settled"
static func frames(raw: SpriteFrames,height: int) -> SpriteFrames:
	if raw.has_meta("pixel_source"):raw=raw.get_meta("pixel_source")
	var key: String=str(raw.get_instance_id())+"/"+str(height)
	if frames_cache.has(key):return frames_cache[key]
	var names: PackedStringArray=raw.get_animation_names()
	var reference: String="idle_down" if raw.has_animation("idle_down") else "idle" if raw.has_animation("idle") else str(names[0])
	var standing_texture: Texture2D=raw.get_frame_texture(reference,0)
	var standing: float=float(standing_texture.get_meta("body_height",standing_texture.get_height()))
	var left: int=0;var right: int=0;var above: int=0;var below: int=0
	for name: StringName in names:
		for i: int in range(raw.get_frame_count(name)):
			var t: Texture2D=raw.get_frame_texture(name,i);var at: Vector2i=pivot(t,height,standing)
			var size:=Vector2i(maxi(1,roundi(t.get_width()*height/standing)),maxi(1,roundi(t.get_height()*height/standing)))
			left=maxi(left,at.x);right=maxi(right,size.x-at.x);above=maxi(above,at.y);below=maxi(below,size.y-at.y)
	var anchor:=Vector2i(left+2,above+2);var canvas_size:=Vector2i(left+right+4,above+below+4)
	var fitted: Dictionary={};var result:=SpriteFrames.new();result.remove_animation("default")
	result.set_meta("pixel_source",raw);result.set_meta("native_height",height)
	for name: StringName in names:
		result.add_animation(name);result.set_animation_speed(name,raw.get_animation_speed(name));result.set_animation_loop(name,raw.get_animation_loop(name))
		var count: int=1 if idle_pose(str(name)) else raw.get_frame_count(name)
		for i: int in range(count):
			var t: Texture2D=raw.get_frame_texture(name,i);var id: int=t.get_instance_id()
			if not fitted.has(id):
				var image:=Image.create(canvas_size.x,canvas_size.y,false,Image.FORMAT_RGBA8)
				var body: Image=native_image(t,height,standing);image.blit_rect(body,Rect2i(Vector2i.ZERO,body.get_size()),anchor-pivot(t,height,standing))
				fitted[id]=make_texture(image,anchor,height,t.get_meta("explicit_direction",false))
				fitted[id].set_meta("source_asset",t.atlas.resource_path if t is AtlasTexture else t.resource_path)
			result.add_frame(name,fitted[id],raw.get_frame_duration(name,i))
		if idle_pose(str(name)):
			result.add_frame(name,breathing(result.get_frame_texture(name,0)))
			result.set_animation_speed(name,1.0);result.set_animation_loop(name,true)
	NativeWalkArt.apply(result,raw)
	frames_cache[key]=result;return result
static func fit(sprite: AnimatedSprite2D,height: int) -> void:
	if sprite.get_meta("fitting_pixels",false):return
	sprite.set_meta("fitting_pixels",true)
	if int(sprite.sprite_frames.get_meta("native_height",-1))!=height:
		var animation: StringName=sprite.animation;var frame: int=sprite.frame;var progress: float=sprite.frame_progress;var playing: bool=sprite.is_playing()
		sprite.sprite_frames=frames(sprite.sprite_frames,height)
		sprite.animation=animation;sprite.set_frame_and_progress(mini(frame,sprite.sprite_frames.get_frame_count(animation)-1),progress)
		if playing:sprite.play()
		else:sprite.pause()
	# animation_changed fires before the frame resets, so the old frame can be past the new animation's end.
	var t: Texture2D=sprite.sprite_frames.get_frame_texture(sprite.animation,mini(sprite.frame,maxi(0,sprite.sprite_frames.get_frame_count(sprite.animation)-1)))
	if t==null:sprite.set_meta("fitting_pixels",false);return
	sprite.centered=false;sprite.offset=-Vector2(t.get_meta("foot"));sprite.scale=Vector2.ONE;sprite.rotation=0.0;sprite.flip_h=false
	if str(sprite.animation).ends_with("left") and not t.get_meta("explicit_direction",false):
		sprite.flip_h=true;sprite.offset.x=-(t.get_width()-float(t.get_meta("foot").x))
	sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;sprite.set_meta("fitting_pixels",false)
static func portrait(raw: Texture2D) -> Texture2D:
	if raw==null:return null
	var key: int=raw.get_instance_id()
	if portrait_cache.has(key):return portrait_cache[key]
	var source: Image=source_image(raw);crisp(source);var used: Rect2i=source.get_used_rect()
	if not used.has_area():return raw
	var image: Image=source
	var ratio: float=float(raw.get_meta("portrait_scale",64.0/maxi(used.size.x,used.size.y)))
	image.resize(maxi(1,roundi(image.get_width()*ratio)),maxi(1,roundi(image.get_height()*ratio)),Image.INTERPOLATE_NEAREST)
	var canvas:=Image.create(64,64,false,Image.FORMAT_RGBA8)
	var anchor: Vector2=raw.get_meta("portrait_anchor",Vector2(used.get_center().x,used.end.y))
	var target: Vector2=raw.get_meta("portrait_target",Vector2(32,64))
	canvas.blit_rect(image,Rect2i(Vector2i.ZERO,image.get_size()),Vector2i((target-anchor*ratio).round()))
	canvas.resize(128,128,Image.INTERPOLATE_NEAREST)
	var result:=ImageTexture.create_from_image(canvas);result.set_meta("native_portrait",true);result.set_meta("portrait_scale",ratio);result.set_meta("portrait_target",target);result.set_meta("source_asset",raw.atlas.resource_path if raw is AtlasTexture else raw.resource_path);portrait_cache[key]=result;return result
