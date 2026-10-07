class_name NativeCampusEncounter
extends RefCounted
static func create(id: String, seed: int, phase: int, music_tick: int) -> Dictionary:
	var p: Dictionary=EncounterDirector.create("flyer",seed,phase,music_tick)
	p.encounterId=id;p.hazards=[];p.telegraphs=[];p.markers=[]
	p.duration=int(p.leadIn)+(540 if id=="index" else 450 if id=="errata" else 420)
	p.phaseName=(["Page Walls","Moving Margins","Useful Stopping Point"][clampi(phase,0,2)] if id=="index" else "Keep One Sentence" if id=="errata" else "Shared Foundations")
	p.wardTicks=0;p.wardPocket=Rect2(104,82,48,34);p.musicBase=music_tick
	p.sentencesKept=0;p.lastSentence=-1;p.sentenceWindow=false;p.sentenceX=96.0
	p.anchorsLit=[false,false];p.currentAnchor=0;p.carryBookmark=false;p.bookmarkDelivered=false
	p.safeLane=84.0;p.returnX=48.0 if phase%2==0 else 208.0;p.objectiveCount=0
	return p
static func step(before: Dictionary, axis: Vector2, precision: bool, assist: float, slow: bool, promised: bool, pressed: bool) -> Dictionary:
	var p: Dictionary=before.duplicate(true)
	p.hit=false;p.grazeDelta=0;p.beatPulse=false
	if p.done:return p
	var speed: float=clampf(assist,0.1,1.0)
	EncounterDirector._move(p,axis,precision,speed)
	var at:=Vector2(p.cursor.x,p.cursor.y)
	var before_count: int=int(p.objectiveCount)
	if pressed and promised:
		if p.encounterId=="errata" and p.sentenceWindow and int(p.lastSentence)!=int(p.get("sentenceNumber",-1)) and at.distance_to(Vector2(p.sentenceX,84))<=19:
			p.lastSentence=p.sentenceNumber;p.sentencesKept=int(p.sentencesKept)+1;p.objectiveCount=p.sentencesKept
		elif p.encounterId=="eric" and p.get("anchorWindow",false):
			var index: int=int(p.currentAnchor)
			if not p.anchorsLit[index] and at.distance_to(Vector2(58 if index==0 else 198,90))<=20:p.anchorsLit[index]=true;p.objectiveCount=int(p.anchorsLit[0])+int(p.anchorsLit[1])
		elif p.encounterId=="index":
			if not p.carryBookmark and not p.bookmarkDelivered and at.distance_to(Vector2(128,24))<=18:p.carryBookmark=true
			elif p.carryBookmark and at.distance_to(Vector2(p.returnX,96))<=18:p.carryBookmark=false;p.bookmarkDelivered=true;p.objectiveCount=1
	p.objectiveChanged=int(p.objectiveCount)>before_count
	p.tick=int(p.tick)+1;p.globalAccumulator=float(p.globalAccumulator)+speed
	while p.globalAccumulator>=1.0:
		p.globalAccumulator-=1.0;p.invulnerability=maxi(0,int(p.invulnerability)-1)
	p.accumulator=float(p.accumulator)+speed*(0.8 if slow else 1.0)
	while p.accumulator>=1.0 and not p.done:
		p.accumulator-=1.0;p.wardTicks=maxi(0,int(p.wardTicks)-1)
		var relative: int=int(p.clock)-int(p.leadIn)
		p.beatPulse=(int(p.musicBase)+int(p.clock))%30==0
		p.beat=(int(p.musicBase)+int(p.clock))/30
		if relative>=0:
			match str(p.encounterId):
				"errata":
					p.sentenceNumber=relative/150;p.sentenceX=96.0 if (relative/150)%2==0 else 160.0
					p.sentenceWindow=relative%150>=45 and relative%150<120
					p.markers=[{"id":0,"x":p.sentenceX,"y":84.0,"active":p.sentenceWindow,"collected":int(p.lastSentence)==int(p.sentenceNumber)}]
					if relative%150==0:
						NativeNewEncounter._tell(p,p.sentenceX-54,-24,0,2.1,24,5,60)
						NativeNewEncounter._tell(p,p.sentenceX+54,-24,0,2.1,24,5,60)
						if int(p.phase)>0:NativeNewEncounter._tell(p,-18,28,2.7,0,6,5,60)
				"eric":
					p.currentAnchor=mini(1,relative/180);p.anchorWindow=relative<360 and relative%180<115
					p.markers=[]
					for index: int in range(2):p.markers.append({"id":index,"x":58.0 if index==0 else 198.0,"y":90.0,"active":int(p.currentAnchor)==index and p.anchorWindow,"collected":p.anchorsLit[index]})
					if relative%180==0 and relative<360:
						NativeNewEncounter._tell(p,58 if int(p.currentAnchor)==0 else 198,-24,0,2.0,23,7,120)
						NativeNewEncounter._tell(p,128,-24,0,2.0,20,7,120)
				"index":
					p.safeLane=84.0 if (relative/180)%2==0 else 36.0
					p.markers=[{"id":0,"x":128.0,"y":24.0,"active":not p.carryBookmark and not p.bookmarkDelivered,"collected":p.carryBookmark or p.bookmarkDelivered},{"id":1,"x":p.returnX,"y":96.0,"active":p.carryBookmark,"collected":p.bookmarkDelivered}]
					if relative%180==0:
						for y: float in [12.0,36.0,60.0,84.0,108.0]:
							if absf(y-float(p.safeLane))>22:NativeNewEncounter._tell(p,-16 if (relative/180)%2==0 else 272,y,2.3 if (relative/180)%2==0 else -2.3,0,4,8,90)
						if int(p.phase)>0:
							NativeNewEncounter._tell(p,8,-24,0,1.8,8,6,90)
							NativeNewEncounter._tell(p,248,-24,0,1.8,8,6,90)
		var pending: Array=[]
		for tell: Dictionary in p.telegraphs:
			tell.ticksRemaining=int(tell.ticksRemaining)-1
			if tell.ticksRemaining<0:
				var h: Dictionary=tell.duplicate(true);h.collision="rect";h.grazed=false;p.hazards.append(h)
			else:pending.append(tell)
		p.telegraphs=pending
		var live: Array=[]
		for h: Dictionary in p.hazards:
			var old:=Vector2(h.x,h.y)
			h.x=float(h.x)+float(h.vx);h.y=float(h.y)+float(h.vy)
			if h.x < -48 or h.x>304 or h.y>150:continue
			var protected: bool=int(p.wardTicks)>0 and p.wardPocket.has_point(at)
			if p.encounterId=="eric":
				for index: int in range(2):
					if p.anchorsLit[index] and Rect2(38 if index==0 else 178,64,40,52).has_point(at):protected=true
			var rect:=Rect2(Vector2(h.x-h.halfWidth-3,h.y-h.halfHeight-3),Vector2((h.halfWidth+3)*2,(h.halfHeight+3)*2))
			var swept: Rect2=rect.merge(Rect2(old-Vector2(h.halfWidth+3,h.halfHeight+3),rect.size))
			if swept.has_point(at) and not protected:EncounterDirector._hit(p)
			elif rect.grow(8).has_point(at) and not h.grazed:h.grazed=true;p.grazeDelta=mini(1,int(p.grazeDelta)+1)
			live.append(h)
		p.hazards=live;p.clock=int(p.clock)+1
		if int(p.clock)>=int(p.duration):p.done=true;p.telegraphs=[];p.hazards=[]
	p.promiseComplete=int(p.sentencesKept)>=3 if p.encounterId=="errata" else bool(p.anchorsLit[0]) and bool(p.anchorsLit[1]) if p.encounterId=="eric" else bool(p.bookmarkDelivered)
	return p
static func progress(p: Dictionary) -> String:
	match str(p.encounterId):
		"errata":return "Sentence pauses %d/3\nConfirm in green box" % int(p.sentencesKept)
		"eric":return "Foundations lit %d/2\nConfirm before weight falls" % int(p.objectiveCount)
		_:return "Bookmark filed / done" if p.bookmarkDelivered else "Carry to outlined slot\nConfirm to file it" if p.carryBookmark else "Pick up green bookmark\nConfirm at top centre"
