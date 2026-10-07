extends SceneTree
var checks: int=0
var failures: int=0
func check(ok: bool,what: String) -> void:
	checks+=1
	if not ok:failures+=1;print("FAIL ",what)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var roster: Array=NativeCastArt.IDS+NativeCastArt.OBJECT_IDS+["jules","imani"]
	for id: String in roster:
		var raw: SpriteFrames=NativePartyArt.frames(id) if id in ["jules","imani","walt"] else NativeCastArt.frames(id)
		var sprite:=AnimatedSprite2D.new();sprite.sprite_frames=raw;root.add_child(sprite);sprite.position=Vector2(120,150)
		var idle: String="idle_down" if raw.has_animation("idle_down") else "idle"
		sprite.play(idle);var height: int=roundi(NativeCastArt.world_height(id))
		NativeIdleMotion.apply(sprite,height,0,false)
		var frames: SpriteFrames=sprite.sprite_frames;var at: Vector2=sprite.position;var foot: Vector2=sprite.offset
		var base: Image=frames.get_frame_texture(idle,0).get_image();var breathed: Image=frames.get_frame_texture(idle,1).get_image()
		check(base.get_size()==breathed.get_size(),id+" idle textures share canvas")
		var anchor: Vector2=frames.get_frame_texture(idle,0).get_meta("foot")
		var unchanged: bool=true
		for y: int in range(maxi(0,int(anchor.y)-floori(height*0.30)+1),base.get_height()):
			for x: int in range(base.get_width()):unchanged=unchanged and base.get_pixel(x,y)==breathed.get_pixel(x,y)
		check(unchanged,id+" feet/lower legs identical across breathing states")
		# Breathing stays restrained; blinks and sway frames (NativeIdleArt extras, frame 2+) are counted apart.
		var swaps: int=0;var last: int=0;var blink_ticks: int=0;var longest_blink: int=0;var run: int=0
		var extras: Dictionary=frames.get_meta("idle_extras",{})
		for tick: int in range(360):
			NativeIdleMotion.apply(sprite,height,tick/60.0,false)
			var breath: int=1 if sprite.frame==1 else 0
			if breath!=last:swaps+=1;last=breath
			if extras.has("blink") and sprite.frame==int(extras.blink):blink_ticks+=1;run+=1;longest_blink=maxi(longest_blink,run)
			else:run=0
			check(sprite.position==at and sprite.offset==foot and sprite.scale==Vector2.ONE and sprite.rotation==0,id+" idle has no transform shimmer at tick "+str(tick))
		check(swaps==2 or not (extras.get("sway",[]) as Array).is_empty(),id+" restrained idle makes only two held-pose transitions in six seconds (a swaying lantern owns its idle instead)")
		if extras.has("blink"):check(blink_ticks>0 and longest_blink<=12,id+" blinks within six seconds and each blink is short")
		NativeIdleMotion.apply(sprite,height,5.0,true)
		check(sprite.frame==0 and not sprite.is_playing(),id+" reduced motion holds the neutral idle")
		var size: Vector2=frames.get_frame_texture(idle,0).get_size()
		for animation: StringName in frames.get_animation_names():
			for i: int in range(frames.get_frame_count(animation)):
				sprite.animation=animation;sprite.frame=i;NativeCastArt.fit(sprite,height)
				var t: Texture2D=frames.get_frame_texture(animation,i)
				check(t.get_size()==size and Vector2(t.get_meta("foot"))==anchor and sprite.scale==Vector2.ONE,id+" pose/direction canvas and anchor "+str(animation)+"/"+str(i))
		if frames.has_animation("walk_down"):
			sprite.animation="walk_down";sprite.frame=frames.get_frame_count("walk_down")-1;NativeCastArt.fit(sprite,height)
			sprite.play(idle);NativeIdleMotion.apply(sprite,height,0,false)
			check(sprite.position==at and sprite.offset==foot,id+" walking/idle transition preserves feet")
		if frames.has_animation("settled"):
			sprite.play("settled");NativeIdleMotion.apply(sprite,height,5.0,false)
			check(sprite.frame==1 and sprite.scale==Vector2.ONE and sprite.offset==foot,id+" peaceful settled stance shares the restrained idle")
		sprite.queue_free()
	for id: String in ["jules","imani","walt"]:
		var frames: SpriteFrames=NativePixelCast.frames(NativePartyBattleArt.frames(id),72)
		var normal: Image=frames.get_frame_texture("idle",0).get_image();var down: Image=frames.get_frame_texture("down",0).get_image()
		check(down.get_used_rect().size.y<normal.get_used_rect().size.y,id+" kneeling is naturally shorter, never stretched to standing height")
		check(frames.get_frame_count("strike")==4 and is_equal_approx(frames.get_animation_speed("strike"),6),id+" strike impact timing retained")
	var body: SpriteFrames=NativePixelCast.frames(NativeCastArt.frames("todd"),56)
	var left:=AnimatedSprite2D.new();left.sprite_frames=body;left.play("idle_left");NativeCastArt.fit(left,56)
	var t: Texture2D=left.sprite_frames.get_frame_texture(left.animation,0)
	check(left.flip_h and is_zero_approx(left.offset.x+t.get_width()-float(t.get_meta("foot").x)),"Mirrored side view retains the horizontal foot pivot")
	left.free()
	var portrait: Texture2D=NativeCastArt.portrait("Mags",0)
	check(portrait.get_size()==Vector2(128,128) and portrait==NativeCastArt.portrait("Mags",0),"Portrait density and cache remain consistent across repeated dialogue renders")
	for id: String in ["pip","pinpal","claim","booth"]:
		var h: int=106 if id=="booth" else roundi(NativeCastArt.world_height(id))
		var texture: Texture2D=NativePixelCast.texture(NativeCastArt.body(id),h,float(NativeCastArt.body(id).get_meta("body_height")))
		var original: Image=texture.get_image();var moved: Image=NativePixelCast.breathing(texture).get_image()
		check(original.get_used_rect().position.y>=2,id+" procedural consumer has headroom for its one-pixel idle pose")
		check(original.get_size()==moved.get_size(),id+" procedural idle preserves canvas")
		var lower: int=int(texture.get_meta("foot").y)-roundi(h*0.30)+1
		var stable: bool=true
		for y: int in range(lower,original.get_height()):
			for x: int in range(original.get_width()):stable=stable and original.get_pixel(x,y)==moved.get_pixel(x,y)
		check(stable,id+" procedural idle keeps all lower pixels planted")
	var speakers: Array=["Jules","Imani","Walt","Cal","Mags","Jakerson","Mara","Eli","Chip","Deion Sanders","Todd Saliman","Rook","Nell","Dev","ENCORE","ERRATA","INDEX","LOADBEARER","Professor Eric","CONE COMMITTEE","EMPTY CHAIR","VAL","Val","Flyerer","Pip","Pin Pal","CLAIM","Booth"]
	for speaker: String in speakers:
		var first: Texture2D=NativeCastArt.portrait(speaker,0)
		for expression: int in range(4):
			var face: Texture2D=NativeCastArt.portrait(speaker,expression)
			check(is_equal_approx(float(face.get_meta("portrait_scale")),float(first.get_meta("portrait_scale"))),speaker+" expression uses fixed character head/body scale")
			check(face.get_meta("portrait_target")==first.get_meta("portrait_target"),speaker+" expression uses the same eye/bust target")
	for key: String in NativePixelCast.trim_cache:
		var pieces: PackedStringArray=key.split("|");var numbers: PackedStringArray=pieces[1].split(",")
		var source:=AtlasTexture.new();source.atlas=load(pieces[0]);source.region=Rect2(float(numbers[0]),float(numbers[1]),float(numbers[2]),float(numbers[3]))
		var cleaned: Image=NativePixelCast.source_image(source)
		for rect: Array in NativePixelCast.trim_cache[key]:
			var clear: bool=true
			for y: int in range(rect[1],rect[1]+rect[3]):
				for x: int in range(rect[0],rect[0]+rect[2]):clear=clear and cleaned.get_pixel(x,y).a==0
			check(clear,"Registered neighboring-cell remnant cleared only in its consumer region: "+key)
	var g: Node=load("res://scenes/main.tscn").instantiate();root.add_child(g);g.qa=true
	g.saves=NativeSaveService.new(OS.get_environment("CAST_TEST_FOLDER").path_join("saves"));g.preferences_path=OS.get_environment("CAST_TEST_FOLDER").path_join("preferences.json")
	g.state.flags.dawn_started=true;g.state.flags.val_resolution="peaceful";g.state.flags.claim_resolution="peaceful";g.enter_room("U07",Vector2(650,350))
	var cleanup: AnimatedSprite2D
	for npc: AnimatedSprite2D in g.world_npcs:
		if npc.get_meta("id")=="mags_cleanup":cleanup=npc
	check(cleanup!=null and cleanup.get_meta("art_id")=="mags" and cleanup.sprite_frames.has_meta("pixel_source"),"Dawn Mags alias uses the same upgraded world art")
	g.dialogue([["Mags","One shelf at a time.","neutral"]],Callable());check(cleanup!=null and cleanup.animation=="interact_down","Dawn Mags gets the same talking pose")
	g.resume_world();check(cleanup!=null and cleanup.animation=="idle_down","Dawn Mags returns from talk to idle")
	if cleanup!=null:
		var texture: Texture2D=cleanup.sprite_frames.get_frame_texture(cleanup.animation,0)
		var used: Rect2i=texture.get_image().get_used_rect()
		var head: Vector2=cleanup.position+cleanup.offset+Vector2(used.position)+Vector2(used.size.x/2.0,3)
		check(g.object_at(head).get("id","")=="mags_cleanup","Upgraded Mags's visible head is selectable with the production pointer")
	g.state.settings.reducedMotion=true
	g._physics_process(1.0/60.0)
	check(not g.scene_props.is_empty(),"World object cast is present in the actual lost-property room")
	for prop: Node2D in g.scene_props:check(float(prop.get("elapsed"))>0 and prop.get("reduced_motion"),"World object cast shares pause-aware clock and Reduced Motion")
	g.enter_room("U03",Vector2(320,400));g._physics_process(1.0/60.0)
	var found_booth: bool=false
	for prop: Node2D in g.environment.foreground_nodes:
		if prop is NativeSpatialProp and prop.definition.get("object")=="booth":found_booth=true;check(prop.reduced_motion,"Booth shares the cast Reduced Motion preference")
	check(found_booth,"Booth is present in its actual atrium scene")
	g.state.flags.walt_resolution="forceful";g.enter_room("U01",Vector2(100,250));g.resume_world()
	check(NativePartyArt.frames("walt").has_animation("down"),"Forceful Walt world resolution has a valid recovered stance")
	g.audio.shutdown();g.queue_free();await process_frame
	print("Cast consistency checks: ",checks,", failures: ",failures);quit(0 if failures==0 else 1)
