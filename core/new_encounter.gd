class_name NativeNewEncounter
extends RefCounted
const ARENA := Rect2(0,0,256,120)
static func create(id: String, seed: int, phase: int, music_tick: int) -> Dictionary:
	var p: Dictionary = EncounterDirector.create("flyer",seed,phase,music_tick)
	p.encounterId=id; p.hazards=[]; p.telegraphs=[]; p.markers=[]
	p.duration=int(p.leadIn)+(480 if id=="encore" else 420)
	p.phaseName="Hold the Light" if id=="walt" else ["House Lights","Speaker Pulse","Final Curtain"][clampi(phase,0,2)]
	p.lantern=100; p.gustsKept=0; p.cuesReached=0; p.shelter=Rect2(106,32,44,60)
	p.wardTicks=0; p.wardPocket=Rect2(104,82,48,34); p.lastCue=-1; p.cueOpen=false; p.safeColumn=128.0
	p.lastGust=-1; p.lanternRaised=0; p.musicBase=music_tick
	return p
static func _tell(p: Dictionary, x: float, y: float, vx: float, vy: float, w: float, h: float, delay: int = 60) -> void:
	p.telegraphs.append({"x":x,"y":y,"vx":vx,"vy":vy,"halfWidth":w,"halfHeight":h,"ticksRemaining":delay,"axis":"vertical" if vy!=0 else "horizontal"})
static func step(before: Dictionary, axis: Vector2, precision: bool, assist: float, slow: bool, promised: bool, pressed: bool) -> Dictionary:
	var p: Dictionary = before.duplicate(true)
	p.hit=false; p.grazeDelta=0; p.beatPulse=false
	if p.done: return p
	var speed: float=clampf(assist,0.1,1.0)
	EncounterDirector._move(p,axis,precision,speed)
	var at := Vector2(p.cursor.x,p.cursor.y)
	if pressed and p.encounterId=="walt" and at.distance_to(Vector2(128,62))<=24:
		p.lanternRaised=90
		p.lantern=mini(100,int(p.lantern)+35)
	if pressed and p.encounterId=="encore" and p.cueOpen and int(p.lastCue)!=int(p.get("cueNumber",-1)) and at.distance_to(Vector2(p.safeColumn,92))<=18:
		p.lastCue=p.cueNumber; p.cuesReached=int(p.cuesReached)+1
	p.tick=int(p.tick)+1
	p.globalAccumulator=float(p.globalAccumulator)+speed
	while p.globalAccumulator>=1.0:
		p.globalAccumulator-=1.0
		p.invulnerability=maxi(0,int(p.invulnerability)-1)
		p.lanternRaised=maxi(0,int(p.lanternRaised)-1)
	p.accumulator=float(p.accumulator)+speed*(0.8 if slow else 1.0)
	while p.accumulator>=1.0 and not p.done:
		p.accumulator-=1.0
		p.wardTicks=maxi(0,int(p.wardTicks)-1)
		var relative: int=int(p.clock)-int(p.leadIn)
		p.beat=(int(p.musicBase)+int(p.clock))/30
		p.beatPulse=(int(p.musicBase)+int(p.clock))%30==0
		if relative>=0:
			if p.encounterId=="walt":
				if relative%120==0 and relative<360:
					for y: float in [16.0,48.0,80.0,112.0]: _tell(p,-12,y,3.1+int(p.phase)*0.2,0,5,3,60)
				# Loose debris falls through one half of the shelter as the gust arrives; the shelter does not stop it.
				if relative%120==20 and relative<360:
					_tell(p,[117.0,139.0][(relative/120+int(p.phase))%2],-10,0,2.2+int(p.phase)*0.2,9,5,45);p.telegraphs[-1].debris=true
				if int(p.phase)>=1 and relative%120==55 and relative<360:
					_tell(p,[139.0,117.0][(relative/120+int(p.phase))%2],-10,0,2.4,9,5,45);p.telegraphs[-1].debris=true
				if relative%120==60 and relative<420:
					var sheltered: bool=p.shelter.has_point(at) and int(p.lanternRaised)>0
					p.lantern=maxi(0,int(p.lantern)-(0 if sheltered else 34))
					if sheltered: p.gustsKept=int(p.gustsKept)+1
			else:
				if relative%150==0:
					p.safeColumn=[48.0,128.0,208.0][(relative/150+int(p.phase))%3]
					p.cueNumber=relative/150; p.cueOpen=false
					if int(p.phase)==0:
						for x: float in [48.0,128.0,208.0]:
							if x!=p.safeColumn: _tell(p,x,-30,0,2.4,24,8,75)
					elif int(p.phase)==1:
						for y: float in [30.0,60.0,90.0]: _tell(p,-20,y,2.8,0,5,5,75); _tell(p,276,y,-2.8,0,5,5,75)
					else:
						_tell(p,p.safeColumn-80,-30,0,1.8,52,6,90)
						_tell(p,p.safeColumn+80,-30,0,1.8,52,6,90)
				p.cueOpen=relative%150>=90 and relative%150<140
				p.markers=[{"id":0,"x":p.safeColumn,"y":92.0,"active":p.cueOpen,"collected":int(p.lastCue)==int(p.cueNumber)}]
		var pending: Array=[]
		for tell: Dictionary in p.telegraphs:
			tell.ticksRemaining=int(tell.ticksRemaining)-1
			if tell.ticksRemaining<0:
				var h: Dictionary=tell.duplicate(true);h.collision="rect";h.grazed=false; p.hazards.append(h)
			else: pending.append(tell)
		p.telegraphs=pending
		var live: Array=[]
		for h: Dictionary in p.hazards:
			var old := Vector2(h.x,h.y)
			h.x=float(h.x)+float(h.vx);h.y=float(h.y)+float(h.vy)
			if h.x < -90 or h.x > 346 or h.y>145: continue
			var protected: bool=(p.encounterId=="walt" and not h.get("debris",false) and p.shelter.has_point(at) and int(p.lantern)>0) or int(p.wardTicks)>0 and p.wardPocket.has_point(at)
			var rect := Rect2(Vector2(h.x-h.halfWidth-3,h.y-h.halfHeight-3),Vector2((h.halfWidth+3)*2,(h.halfHeight+3)*2))
			var swept := rect.merge(Rect2(old-Vector2(h.halfWidth+3,h.halfHeight+3),rect.size))
			if swept.has_point(at) and not protected: EncounterDirector._hit(p)
			elif rect.grow(8).has_point(at) and not h.grazed:
				h.grazed=true;p.grazeDelta=mini(1,int(p.grazeDelta)+1)
			live.append(h)
		p.hazards=live;p.clock=int(p.clock)+1
		if int(p.clock)>=int(p.duration): p.done=true;p.telegraphs=[];p.hazards=[]
	p.promiseComplete=(int(p.gustsKept)>=3 and int(p.lantern)>0) if p.encounterId=="walt" else int(p.cuesReached)>=2
	return p
