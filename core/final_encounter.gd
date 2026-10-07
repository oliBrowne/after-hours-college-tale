class_name NativeFinalEncounter
extends RefCounted
const IDS: Array[String]=["cone","chad","rook","val"]
static func create(id: String, seed: int, phase: int, music_tick: int) -> Dictionary:
	var p: Dictionary=EncounterDirector.create("flyer",seed,phase,music_tick)
	p.encounterId=id;p.hazards=[];p.telegraphs=[];p.markers=[];p.musicBase=music_tick
	p.duration=int(p.leadIn)+(360 if id=="chad" else 450 if id=="cone" else [600,480,540,420][clampi(phase,0,3)] if id=="val" else 540)
	p.phase=clampi(phase,0,3);p.phaseName="One Marked Route" if id=="cone" else "Let's Circle Back" if id=="chad" else ["Keys and Exits","Two Impossible Jobs","One Shift Together"][clampi(phase,0,2)] if id=="rook" else ["Familiar Promises","Nobody Has To Be Ideal","Unreserve the Chairs","An Ordinary Voice"][clampi(phase,0,3)]
	p.wardTicks=0;p.wardPocket=Rect2(104,82,48,34);p.revision="";p.rejected=[]
	p.objectiveCount=0;p.objectiveChanged=false;p.routesKept=0;p.lastRoute=-1;p.routeNumber=0;p.safeLane=24.0;p.cancelledLane=-1.0
	p.quietPocket=Rect2(22,70,58,40);p.emptySpace=Rect2(104,32,48,56);p.chairEntered=false;p.quietTicks=0
	p.keyHeld=false;p.exitReached=false;p.chosenExit=48.0;p.exitHold=0;p.sharedCues=0;p.lastCue=-1;p.cueOpen=false;p.cueNumber=0
	p.sharedPocket=Rect2(104,38,48,54);p.sharedTicks=0;p.chairs=[];p.openColumn=128.0;p.seatsHold=0;p.finalCues=0;p.valTask=0
	if id=="chad":p.cursor={"x":48.0,"y":90.0}
	return p
static func _tell(p: Dictionary,x: float,y: float,vx: float,vy: float,w: float,h: float,delay: int=75) -> void:NativeNewEncounter._tell(p,x,y,vx,vy,w,h,delay)
static func step(before: Dictionary, axis: Vector2, precision: bool, assist: float, slow: bool, promised: bool, pressed: bool) -> Dictionary:
	var p: Dictionary=before.duplicate(true);p.hit=false;p.grazeDelta=0;p.beatPulse=false;p.objectiveChanged=false
	if p.done:return p
	var speed: float=clampf(assist,0.1,1.0);EncounterDirector._move(p,axis,precision,speed)
	var at:=Vector2(p.cursor.x,p.cursor.y)
	var count_before: int=int(p.objectiveCount)
	if pressed and promised:
		if p.encounterId=="rook":
			if int(p.phase)==0:
				if not p.keyHeld and at.distance_to(Vector2(60,24))<=16:p.keyHeld=true
				elif p.keyHeld and at.distance_to(Vector2(196,96))<=16:p.exitReached=true;p.objectiveCount=1
			elif int(p.phase)==2 and p.cueOpen and int(p.lastCue)!=int(p.cueNumber) and at.distance_to(Vector2(128,84))<=18:p.lastCue=p.cueNumber;p.sharedCues=int(p.sharedCues)+1;p.objectiveCount=p.sharedCues
		elif p.encounterId=="val":
			if int(p.phase)==0:
				var destinations: Array[Vector2]=[Vector2(128,24),Vector2(208,96),Vector2(48,96)]
				if int(p.valTask)<3 and at.distance_to(destinations[int(p.valTask)])<=18:p.valTask=int(p.valTask)+1;p.objectiveCount=p.valTask
			elif int(p.phase)==3 and p.cueOpen and int(p.lastCue)!=int(p.cueNumber) and at.distance_to(Vector2(128,62))<=20:p.lastCue=p.cueNumber;p.finalCues=int(p.finalCues)+1;p.objectiveCount=p.finalCues
	p.tick=int(p.tick)+1;p.globalAccumulator=float(p.globalAccumulator)+speed
	while p.globalAccumulator>=1.0:p.globalAccumulator-=1.0;p.invulnerability=maxi(0,int(p.invulnerability)-1)
	p.accumulator=float(p.accumulator)+speed*(0.8 if slow else 1.0)
	while p.accumulator>=1.0 and not p.done:
		p.accumulator-=1.0;p.wardTicks=maxi(0,int(p.wardTicks)-1)
		var relative: int=int(p.clock)-int(p.leadIn)
		p.beatPulse=(int(p.musicBase)+int(p.clock))%30==0;p.beat=(int(p.musicBase)+int(p.clock))/30
		if relative>=0:
			match str(p.encounterId):
				"cone":
					p.routeNumber=relative/150;p.safeLane=[24.0,60.0,96.0][int(p.routeNumber)%3];p.cancelledLane=[96.0,24.0,60.0][int(p.routeNumber)%3]
					p.markers=[{"id":0,"x":128.0,"y":p.safeLane,"active":relative%150>=60 and relative%150<135,"collected":int(p.lastRoute)==int(p.routeNumber)}]
					if promised and relative%150>=75 and relative%150<135 and int(p.lastRoute)!=int(p.routeNumber) and absf(at.y-float(p.safeLane))<14 and absf(at.x-128)<40:p.lastRoute=p.routeNumber;p.routesKept=int(p.routesKept)+1;p.objectiveCount=p.routesKept
					if relative%150==0:
						for y: float in [24.0,60.0,96.0]:
							if y!=p.safeLane:_tell(p,-16,y,2.5,0,5,12,75)
				"chad":
					if p.emptySpace.has_point(at):p.chairEntered=true
					if promised and p.quietPocket.has_point(at) and not p.chairEntered:p.quietTicks=int(p.quietTicks)+1
					p.markers=[{"id":0,"x":48.0,"y":90.0,"active":true,"collected":int(p.quietTicks)>=120}]
					if relative%120==0:
						for x: float in [100.0,156.0,208.0]:_tell(p,x,-20,0,1.8,7,4,90)
					p.objectiveCount=mini(120,int(p.quietTicks))
				"rook":
					if int(p.phase)==0:
						p.markers=[{"id":0,"x":60.0,"y":24.0,"active":not p.keyHeld,"collected":p.keyHeld},{"id":1,"x":196.0,"y":96.0,"active":p.keyHeld,"collected":p.exitReached}]
					elif int(p.phase)==1:
						p.chosenExit=48.0 if p.revision=="west" else 208.0
						p.markers=[{"id":0,"x":p.chosenExit,"y":70.0,"active":not str(p.revision).is_empty(),"collected":int(p.exitHold)>=60}]
						if promised and p.revision in ["west","east"] and at.distance_to(Vector2(p.chosenExit,70))<=20:p.exitHold=int(p.exitHold)+1
						p.objectiveCount=mini(60,int(p.exitHold))
					else:
						p.cueNumber=relative/150;p.cueOpen=relative%150>=75 and relative%150<135
						p.markers=[{"id":0,"x":128.0,"y":84.0,"active":p.cueOpen,"collected":int(p.lastCue)==int(p.cueNumber)}]
					if relative%150==0:
						for y: float in [18.0,106.0]:_tell(p,-20,y,2.8,0,8,6,75)
					if int(p.phase)==0 and relative%180==0:_tell(p,128,-20,0,1.8,9,5,90)
					if int(p.phase)==1 and relative%120==0:
						for x: float in [48.0,208.0]:
							if str(p.revision).is_empty() or x!=p.chosenExit:_tell(p,x,-20,0,2.1,10,6,75)
				"val":
					if int(p.phase)==0:
						var destinations: Array[Vector2]=[Vector2(128,24),Vector2(208,96),Vector2(48,96)]
						p.markers=[]
						for index: int in range(3):p.markers.append({"id":index,"x":destinations[index].x,"y":destinations[index].y,"active":int(p.valTask)==index,"collected":int(p.valTask)>index})
						if relative%180==0:
							p.safeLane=84.0 if (relative/180)%2==0 else 36.0
							for y: float in [12.0,36.0,60.0,84.0,108.0]:
								if y!=p.safeLane:_tell(p,-20,y,2.0,0,5,7,90)
					elif int(p.phase)==1:
						if promised and p.rejected.size()==3 and p.sharedPocket.has_point(at):p.sharedTicks=int(p.sharedTicks)+1
						p.markers=[{"id":0,"x":128.0,"y":62.0,"active":p.rejected.size()==3,"collected":int(p.sharedTicks)>=90}];p.objectiveCount=mini(90,int(p.sharedTicks))
						if relative%120==0:
							for x: float in [32.0,224.0]:_tell(p,x,-20,0,1.8,22,8,75)
					elif int(p.phase)==2:
						p.openColumn=64.0 if p.revision=="left" else 192.0 if p.revision=="right" else 128.0
						p.chairs=[]
						if p.revision!="left":p.chairs.append(Rect2(0,0,100,120))
						if p.revision!="right":p.chairs.append(Rect2(156,0,100,120))
						if promised and p.revision in ["left","right"] and at.distance_to(Vector2(p.openColumn,84))<=22:p.seatsHold=int(p.seatsHold)+1
						p.markers=[{"id":0,"x":p.openColumn,"y":84.0,"active":p.revision in ["left","right"],"collected":int(p.seatsHold)>=90}];p.objectiveCount=mini(90,int(p.seatsHold))
						if relative%180==0:_tell(p,128,-20,0,1.7,12,6,90)
					else:
						p.cueNumber=relative/150;p.cueOpen=relative%150>=60 and relative%150<120
						p.markers=[{"id":0,"x":128.0,"y":62.0,"active":p.cueOpen,"collected":int(p.lastCue)==int(p.cueNumber)}]
						if relative==0:
							_tell(p,20,-20,0,1.3,10,5,90);_tell(p,236,-20,0,1.3,10,5,90)
		var pending: Array=[]
		for tell: Dictionary in p.telegraphs:
			tell.ticksRemaining=int(tell.ticksRemaining)-1
			if tell.ticksRemaining<0:
				var h: Dictionary=tell.duplicate(true);h.collision="rect";h.grazed=false;p.hazards.append(h)
			else:pending.append(tell)
		p.telegraphs=pending
		var live: Array=[]
		var protected: bool=int(p.wardTicks)>0 and p.wardPocket.has_point(at) or p.encounterId=="chad" and p.quietPocket.has_point(at) or p.encounterId=="rook" and int(p.phase)==2 and p.sharedPocket.has_point(at)
		for chair: Rect2 in p.chairs:
			if chair.has_point(at) and not protected:EncounterDirector._hit(p)
		for h: Dictionary in p.hazards:
			var old:=Vector2(h.x,h.y);h.x=float(h.x)+float(h.vx);h.y=float(h.y)+float(h.vy)
			if h.x < -48 or h.x>304 or h.y>150:continue
			var rect:=Rect2(Vector2(h.x-h.halfWidth-3,h.y-h.halfHeight-3),Vector2((h.halfWidth+3)*2,(h.halfHeight+3)*2))
			var swept: Rect2=rect.merge(Rect2(old-Vector2(h.halfWidth+3,h.halfHeight+3),rect.size))
			if swept.has_point(at) and not protected:EncounterDirector._hit(p)
			elif rect.grow(8).has_point(at) and not h.grazed:h.grazed=true;p.grazeDelta=mini(1,int(p.grazeDelta)+1)
			live.append(h)
		p.hazards=live;p.clock=int(p.clock)+1
		if int(p.clock)>=int(p.duration):p.done=true;p.telegraphs=[];p.hazards=[]
	var threshold: int=120 if p.encounterId=="chad" else 60 if p.encounterId=="rook" and int(p.phase)==1 else 90 if p.encounterId=="val" and int(p.phase) in [1,2] else 0
	p.objectiveChanged=int(p.objectiveCount)>=threshold and count_before<threshold if threshold>0 else int(p.objectiveCount)>count_before
	p.promiseComplete=false
	match str(p.encounterId):
		"cone":p.promiseComplete=int(p.routesKept)>=3
		"chad":p.promiseComplete=int(p.quietTicks)>=120 and not p.chairEntered
		"rook":p.promiseComplete=p.exitReached if int(p.phase)==0 else int(p.exitHold)>=60 and p.revision in ["west","east"] if int(p.phase)==1 else int(p.sharedCues)>=2 and p.revision in ["west","east"]
		"val":p.promiseComplete=int(p.valTask)>=3 if int(p.phase)==0 else int(p.sharedTicks)>=90 and p.rejected.size()==3 if int(p.phase)==1 else int(p.seatsHold)>=90 and p.revision in ["left","right"] if int(p.phase)==2 else int(p.finalCues)>=2
	return p
static func progress(p: Dictionary) -> String:
	match str(p.encounterId):
		"cone":return "Marked routes %d/3\nCrossed-out calls cancelled" % mini(3,int(p.routesKept))
		"chad":return "Quiet time %d/120\nKeep the slot FREE" % mini(120,int(p.quietTicks))
		"rook":return "Key %s / exit %s" % ["held" if p.keyHeld else "open","reached" if p.exitReached else "open"] if int(p.phase)==0 else "CONNECT > REVISE\nChoose one exit; decline one" if str(p.revision).is_empty() else "Chosen exit held %d/60" % mini(60,int(p.exitHold)) if int(p.phase)==1 else "Shared stopping cues %d/2" % mini(2,int(p.sharedCues))
		_:return "One return / one stop %d/3" % mini(3,int(p.valTask)) if int(p.phase)==0 else "Own ideals rejected %d/3\nShared space %d/90" % [p.rejected.size(),mini(90,int(p.sharedTicks))] if int(p.phase)==1 else "REVISE the reserved seats\nOpen passage %d/90" % mini(90,int(p.seatsHold)) if int(p.phase)==2 else "Ordinary stopping cues %d/2\nThen choose an ending" % mini(2,int(p.finalCues))
