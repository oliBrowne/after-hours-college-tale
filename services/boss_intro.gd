class_name NativeBossIntro
extends Node2D
## A gym-leader intro card before every story boss, like a Pokemon gym battle: a band sweeps
## across, the boss slides in, and a title banner lands with their name and catchphrase.
## Random path fights don't get one, so the bosses stand out. The first meeting in a session
## plays the full card; rematches and checkpoint retries play a short one. Confirm skips.
## Art hook: res://assets/art/entrance/<id>.png, when it exists, replaces the boss's idle pose
## (feet at the bottom centre of the image).

## id: [title, name, catchphrase, accent colour]
const CARDS: Dictionary = {
	"jakerson": ["YOUR TUTOR", "JAKERSON", "Quick friendly spar? I'll go easy. That's a promise too.", "8fc7e8"],
	"jakerson_final": ["GRADUATION REMATCH", "JAKERSON", "One last friendly set. Loser buys the boba.", "8fc7e8"],
	"walt": ["THE BRIDGE KEEPER", "WALT", "The wind is doing the talking now. Keep your light up.", "e8b45c"],
	"flyer": ["CLUB FAIR MENACE", "FLYERER", "ONE PAGE! JUST ONE! THE CLUB CANNOT CLOSE IF NOBODY READS!", "e6d6b1"],
	"pinpal": ["RETURN SERVICE", "PIN PAL", "RETURN SERVICE! RETURN SERVICE!", "e8837b"],
	"claim": ["LOST PROPERTY", "CLAIM", "TAKE A NUMBER. TAKE A COAT. EVERYTHING HAS AN OWNER.", "a68db8"],
	"chip": ["STAGE MANAGER", "CHIP", "Places, everyone! Policies are for people without an ENCORE!", "e8b45c"],
	"deion": ["COACH PRIME", "DEION SANDERS", "You can sprint forever, or you can hand it to a teammate.", "cfb87c"],
	"todd": ["THE PRESIDENT", "TODD SALIMAN", "A plan with limits. Let's see if it survives an audit.", "cfb87c"],
	"cone": ["ONE MARKED ROUTE", "CONE COMMITTEE", "LEFT. RIGHT. BOTH. SAFETY HAS FORMED A COMMITTEE.", "e8a05c"],
	"encore": ["THE SHOW THAT WON'T END", "ENCORE", "THE SONG HAS NO AGREEMENT. AGAIN!", "e8837b"],
	"eric": ["RULE OF THUMB", "PROFESSOR ERIC", "Hold this probe. One more measurement and we'll know everything.", "9fe0a8"],
	"errata": ["FIX EVERY LINE", "ERRATA", "REPLACE UNCERTAINTY. ERASE HESITATION.", "e8837b"],
	"index": ["EVERY POSSIBLE NAME", "INDEX", "THE SOURCE HAS RETURNED. NOW FINISH EVERY FUTURE IT OPENED.", "b9d5bc"],
	"chad": ["NETWORKING LEGEND", "CHAD", "Let's circle back. Coffee chat? Coffee chat.", "7fb2e8"],
	"rook": ["NIGHT MARSHAL", "ROOK", "LAST CALL. No one leaves until everyone is accounted for.", "a68db8"],
	"val": ["VP OF TALENT ACQUISITION", "VAL", "WHERE DO YOU SEE YOURSELF IN FIVE YEARS?", "e8837b"],
}
## What a boss says back the first time in a fight someone asks it something with CONNECT.
const ANSWERS: Dictionary = {
	"jakerson": ["Jakerson", "A rhythm game for my intro CS final. It only crashes when I'm nervous. So, always."],
	"jakerson_final": ["Jakerson", "Honestly? This. Showing someone the ropes and watching them not need me."],
	"walt": ["Walt", "It doesn't stop the wind. It just shows you where your feet are. That's usually enough."],
	"flyer": ["Flyerer", "IT SAYS... 'A PLACE TO MAKE NOISE TOGETHER.' OH. NOT 'EVERYONE, FOREVER.'"],
	"pinpal": ["Pin Pal", "THREE BALLS. NOBODY BROUGHT THEM BACK. I KEEP SERVING SO SOMEONE WILL."],
	"claim": ["CLAIM", "ITEM 41: ONE GLOVE. NO OWNER ON FILE. IT KEEPS WAVING AT YOU."],
	"chip": ["Chip", "A SMALL one? ...Okay. Three columns, one bow, then we let people go home. Maybe."],
	"deion": ["Deion Sanders", "That's the right question. Nobody runs the whole field alone. Show me you can hand it off."],
	"todd": ["Todd Saliman", "Good. Read the fine print. This one says 'everything, indefinitely'. That's not consent. That's a typo."],
	"encore": ["ENCORE", "STOP? THE CROWD STOPS WHEN... WHEN THEY WANT TO? NOBODY TOLD ME THAT WAS ALLOWED."],
	"errata": ["ERRATA", "...THE WRITER'S. I ONLY MEANT TO HELP. I KEPT HELPING UNTIL NOTHING WAS LEFT."],
	"eric": ["Professor Eric", "The return path! Everyone watches the signal. Nobody asks where the current comes home. Rule of thumb: always ask."],
	"index": ["INDEX", "THE ORIGINAL IS... ONE STUDENT, HUMMING. I FILED SIX HUNDRED ENDINGS ON TOP OF IT."],
	"cone": ["CONE COMMITTEE", "ONE ROUTE. WE HAD THREE PROPOSALS. NOBODY WANTED TO CANCEL THE OTHERS."],
	"chad": ["Chad", "...Honestly? A friend who doesn't need anything from me. Wild, right? Let's circle back on that."],
	"rook": ["Rook", "One shift. One exit. And somebody to tell me when it ends."],
	"val": ["VAL", "WHO'S HIRING? ...I AM. I THINK. SOMEONE TOLD ME TO FILL EVERY SEAT, AND I NEVER ASKED WHO."],
}
const FULL: int = 150
const SHORT: int = 80
const INK: Color = Color("0d101c")
const CREAM: Color = Color("e6d6b1")
const MINT: Color = Color("b9d5bc")
## Cards seen this session; a second meeting plays the short card.
static var seen: Dictionary = {}

var game: Node
var id: String = ""
var card: Array = []
var done: Callable
var ticks: int = 0
var length: int = FULL
var reduced: bool = false
var accent: Color = CREAM
var hold_mode: int = 0
var boss: Node2D
var hero: AnimatedSprite2D

static func key(boss_id: String) -> String:
	return "flyer" if boss_id.is_empty() else boss_id

static func has_card(boss_id: String) -> bool:
	return CARDS.has(key(boss_id))

## [speaker, line] for a boss's answer to a CONNECT question, or [] if it has none.
static func answer(boss_id: String) -> Array:
	return ANSWERS.get(key(boss_id), [])

## Starts the card over the battle. g.mode must already be the holding mode; `then` runs when
## the card ends (not if the player leaves to the title from the pause menu meanwhile).
static func play(g: Node, boss_id: String, then: Callable) -> void:
	var layer := CanvasLayer.new()
	layer.layer = 3
	g.add_child(layer)
	var intro := NativeBossIntro.new()
	layer.add_child(intro)
	intro.begin(g, key(boss_id), then)

func begin(g: Node, which: String, then: Callable) -> void:
	game = g; id = which; card = CARDS[id]; done = then
	accent = Color(str(card[3]))
	reduced = bool(g.state.settings.reducedMotion)
	length = SHORT if seen.has(id) else FULL
	seen[id] = true
	hold_mode = int(g.mode)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var entrance: String = "res://assets/art/entrance/%s.png" % id
	if ResourceLoader.exists(entrance):
		var still := Sprite2D.new()
		still.texture = load(entrance)
		still.centered = false
		still.offset = Vector2(-still.texture.get_width() / 2.0, -still.texture.get_height())
		boss = still
	else:
		var art := AnimatedSprite2D.new()
		art.sprite_frames = NativeCastArt.frames("val_small" if id == "val" and int(g.boss_stage) == 3 else id.trim_suffix("_final"))
		art.play("idle_down" if art.sprite_frames.has_animation("idle_down") else "idle")
		var height: float = 150.0 if id != "flyer" else 130.0
		NativeCastArt.fit(art, height)
		# Animated cast frames differ in size; refit each frame like the battle sprites do.
		art.frame_changed.connect(func() -> void: NativeCastArt.fit(art, height))
		boss = art
	add_child(boss)
	hero = AnimatedSprite2D.new()
	hero.sprite_frames = NativePartyBattleArt.frames("jules")
	hero.play("idle")
	NativeCastArt.fit(hero, 92.0)
	add_child(hero)
	g.audio.combat("whoosh")
	_place()

func _physics_process(_delta: float) -> void:
	if game == null or not is_instance_valid(game): return
	# The pause menu draws underneath this layer, so step aside while it is open.
	get_parent().visible = not bool(game.pause_context)
	if bool(game.pause_context): return
	if int(game.mode) != hold_mode:
		# Left for the title (or anything else) mid-card: drop it without starting the fight.
		get_parent().queue_free(); return
	game.input_lock = maxi(int(game.input_lock), 2)
	ticks += 1
	if ticks == _land(): game.audio.combat("perfect")
	_place()
	queue_redraw()
	if ticks >= length:
		get_parent().queue_free()
		done.call()

func _input(event: InputEvent) -> void:
	if game == null or bool(game.pause_context) or ticks < 14: return
	if event.is_action_pressed("confirm") or event.is_action_pressed("cancel"):
		ticks = maxi(ticks, length - 14)

## When the banner lands: early in the short card.
func _land() -> int:
	return 22 if length == FULL else 12

func _progress(start: int, span: int) -> float:
	if reduced: return 1.0
	var t: float = clampf(float(ticks - start) / span, 0.0, 1.0)
	return 1.0 - pow(1.0 - t, 3.0)

func _exit() -> float:
	return 0.0 if reduced else clampf(float(ticks - (length - 14)) / 14.0, 0.0, 1.0)

func _place() -> void:
	var out: float = _exit()
	boss.position = Vector2(lerpf(760.0, 470.0, _progress(2, 18)) + out * 300.0, 292.0)
	hero.position = Vector2(lerpf(-80.0, 112.0, _progress(4, 18)) - out * 220.0, 300.0)
	boss.modulate.a = 1.0 - out; hero.modulate.a = 1.0 - out

func _draw() -> void:
	var out: float = _exit()
	var fade: float = 1.0 - out
	draw_rect(Rect2(0, 0, 640, 360), Color(INK, 0.86 * fade * _progress(0, 8)))
	# The band: a slanted stripe in the boss's colour, sweeping in from the right.
	var sweep: float = _progress(0, 14)
	var dx: float = (1.0 - sweep) * 700.0 + out * -700.0
	var band := PackedVector2Array([Vector2(dx + 40, 84), Vector2(dx + 700, 84), Vector2(dx + 640, 300), Vector2(dx - 20, 300)])
	draw_colored_polygon(band, Color(accent.darkened(0.62), 0.92 * fade))
	draw_line(Vector2(dx + 40, 84), Vector2(dx + 700, 84), Color(accent, fade), 2.0)
	draw_line(Vector2(dx - 20, 300), Vector2(dx + 640, 300), Color(accent, fade), 2.0)
	# Speed lines behind the boss while the card is up.
	if not reduced:
		for i: int in range(9):
			var y: float = 100.0 + i * 22.0
			var x: float = fposmod(700.0 - float(ticks) * (9.0 + i % 3 * 3.0) - i * 97.0, 760.0) - 60.0
			draw_line(Vector2(x, y), Vector2(x + 40.0 + (i % 4) * 18.0, y), Color(accent.lightened(0.2), 0.35 * fade), 1.0)
	# The flash as the boss lands.
	if not reduced and ticks >= _land() and ticks < _land() + 8:
		draw_rect(Rect2(0, 0, 640, 360), Color(1, 1, 1, 0.45 * (1.0 - float(ticks - _land()) / 8.0)))
	# The title banner, sliding in from the left.
	var land: float = _progress(_land() - 8, 14)
	var bx: float = (land - 1.0) * 420.0 - out * 420.0
	var plate := PackedVector2Array([Vector2(bx, 206), Vector2(bx + 392, 206), Vector2(bx + 372, 274), Vector2(bx, 274)])
	draw_colored_polygon(plate, Color(INK, 0.94 * fade))
	draw_line(Vector2(bx, 206), Vector2(bx + 392, 206), Color(accent, fade), 2.0)
	draw_line(Vector2(bx, 274), Vector2(bx + 372, 274), Color(accent, fade), 2.0)
	var font: Font = game.font
	if font == null: return
	draw_string(font, Vector2(bx + 22, 224), str(card[0]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(accent, fade))
	var name_size: int = 24 if str(card[1]).length() * 12 <= 340 else 18
	draw_string(font, Vector2(bx + 20, 256), str(card[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, name_size, Color(CREAM, fade))
	# The catchphrase strip along the bottom.
	var quote: float = _progress(_land(), 12)
	var line: String = "\"" + str(card[2]) + "\""
	draw_rect(Rect2(0, 316, 640, 30), Color(INK, 0.9 * fade * quote))
	draw_string(font, Vector2(20, 336), line, HORIZONTAL_ALIGNMENT_LEFT, 600, 12, Color(MINT, fade * quote))
