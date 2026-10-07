class_name NativeLinkedOutMenu
extends RefCounted
## The LinkedOut app in the pause menu (data and boosts live in core/linkedout.gd): accept connection
## requests, read the feed. A new request shows a notice once, when control returns to the world.
## "Meeting" a scene character (Eli, Mara, Nell) is a flag set the first time Jules talks to them.
## Drawing: main.gd hands LinkedOut captions (starting "LinkedOut") to render() for the profile layout.
const MEET: Dictionary = {"eli": "met_eli", "floormate_208": "met_eli", "mara": "met_mara", "floormate_laundry": "met_mara",
	"nell": "met_nell", "floormate_lobby": "met_nell"}
const BLUE: Color = Color("0a66c2")
const SKINS: Array[Color] = [Color("f1c9a5"), Color("c68e62"), Color("8d5a3b"), Color("5c3a26")]
const SHIRTS: Array[Color] = [Color("2d5c8a"), Color("7a3e5c"), Color("3f7f5a"), Color("c9a24a"), Color("4b4a7a")]
const BACKDROPS: Array[Color] = [Color("cfe3f2"), Color("e7dcc8"), Color("d4e8d6"), Color("e9d3d3")]
const JULES: Dictionary = {"id": "jules", "name": "Jules Navarro", "headline": "Campus radio volunteer. Open to mixers."}
const WORK: Dictionary = {
	"jules": ["Campus radio, volunteer DJ (2025 - present)", "Sound crew, Fountain Court events (2024)"],
	"imani": ["Founder, Sound Check (2025 - present)", "Sound tech, campus venues (2024)"],
	"walt": ["Lantern keeper, Broadway underpass (since 1994)", "Night watch, Boulder Creek path (2011 - 2019)"],
	"jakerson": ["Tennis coach, UMC courts (2023 - present)", "Roommate, Farrand Hall (2026)"],
	"eli": ["Bike mechanic, Farrand Hall 208 (2025 - present)", "Wheel truing, Boulder bike co-op (2023 - 2025)"],
	"mara": ["Painter, Farrand laundry room murals (2025 - present)", "Set painter, campus theatre (2024)"],
	"nell": ["Reader, Norlin Library (2024 - present)", "Tutor, Writing Center (2023 - 2024)"],
	"cal": ["Night-shift lead, Engineering (2024 - present)", "Lab tech, Engineering Center (2022 - 2024)"],
	"dev": ["Engineer, bridge design studio (2025 - present)", "Drafting intern, civil lab (2024)"],
	"flyer": ["Freelance flyer distribution (2025 - present)", "Event posting, Pearl Street (2024)"],
	"pinpal": ["Returns specialist, bowling alley (2024 - present)", "Pin setter (2021 - 2024)"],
	"claim": ["Academic Advisor, Degree Audit Office (2018 - present)", "Advising intern (2016 - 2018)"],
	"chip": ["Stage Manager, campus auditorium (2024 - present)", "Crew, campus productions (2022 - 2024)"],
	"encore": ["Performer, final acts (2019 - present)", "Opening act, every season (2017 - 2019)"],
	"errata": ["Teaching Assistant, Chem 1 (seventh year)", "Grader, Physics 1 (2019 - 2020)"],
	"autocomplete": ["Language model, various products (2023 - present)", "Autocorrect, phone keyboard (2019 - 2023)"],
	"eric": ["Professor, Electrical Engineering (2009 - present)", "Lecturer, signal integrity short courses"],
	"deion": ["Coach, Prime Time Athletics (2018 - present)", "Mentor, Eastside Youth Program (2012 - 2018)"],
	"todd": ["President's Office, administration (2021 - present)", "Budget office, university system (2014 - 2021)"],
	"cone": ["Captain, Flatirons Peloton (2022 - present)", "Road racer, regional circuit (2016 - 2022)"],
	"rook": ["Night Marshal, residence halls (2025 - present)", "Key control, Farrand Hall (2023 - 2025)"],
	"tanner": ["Rush chair, Interfraternity Council (2026)", "Early shift, campus coffee cart (2025)"],
	"kyle": ["Founder and CEO, Finally (2026)", "Visionary, Pearl Street office (2025)"],
	"chad": ["Networking, Gold Pass Consulting (2025 - present)", "Sales, Summit Ventures (2023 - 2025)"],
}
static var _avatars: Dictionary = {}

static func met(g: Node, object: Dictionary) -> void:
	var flag: String = str(MEET.get(str(object.get("id", "")), ""))
	if not flag.is_empty(): g.state.flags[flag] = true

static func badge(flags: Dictionary) -> String:
	var waiting: int = LinkedOut.pending(flags).size()
	return " (%d new)" % waiting if waiting > 0 else ""

## "LinkedOut: ..." once per newly possible connection, never over another notice.
static func notify(g: Node) -> void:
	var f: Dictionary = g.state.flags
	var known: int = LinkedOut.accepted(f).size() + LinkedOut.pending(f).size()
	if known <= int(str(f.get("li_seen", "0"))) or int(g.notice_ticks) > 0: return
	f.li_seen = str(known)
	g.message("LinkedOut: new connection request. Pause > LinkedOut.")

static func is_profile(caption: String) -> bool:
	return caption.begins_with("LinkedOut")

## A 32x32 pixel avatar, drawn once per person: backdrop, shoulders, head, hair.
static func avatar(id: String) -> Texture2D:
	if _avatars.has(id): return _avatars[id]
	var h: int = absi(id.hash())
	var skin: Color = SKINS[h % SKINS.size()]
	var shirt: Color = SHIRTS[(h / 7) % SHIRTS.size()]
	var hair: Color = Color("2a211c") if (h / 11) % 2 == 0 else Color("6b4a2e")
	var img: Image = Image.create(32, 32, false, Image.FORMAT_RGBA8)
	img.fill(BACKDROPS[(h / 3) % BACKDROPS.size()])
	for y: int in range(32):
		for x: int in range(32):
			var dx: float = (x - 16) / 13.0
			var dy: float = (y - 34) / 13.0
			if y >= 21 and dx * dx + dy * dy <= 1.0: img.set_pixel(x, y, shirt)
			if (x - 16) * (x - 16) + (y - 13) * (y - 13) <= 42: img.set_pixel(x, y, skin)
			if (x - 16) * (x - 16) + (y - 11) * (y - 11) <= 45 and y <= 11: img.set_pixel(x, y, hair)
	var texture: Texture2D = ImageTexture.create_from_image(img)
	_avatars[id] = texture
	return texture

static func open(g: Node) -> void:
	var f: Dictionary = g.state.flags
	var pending: Array = LinkedOut.pending(f)
	var options: Array = []
	for p: Dictionary in pending:
		var id: String = str(p.id)
		options.append(g.option("Accept " + str(p.name), func() -> void:accept(g, id)))
	if pending.size() > 1:
		options.append(g.option("Accept all", func() -> void:
			for p: Dictionary in LinkedOut.pending(g.state.flags): LinkedOut.accept(g.state.flags, str(p.id))
			changed(g, "Everyone accepted.")))
	options.append(g.option("Profile feed", func() -> void:feed(g, 0)))
	options.append(g.option("Back", g.pause_menu))
	g.open_menu(g.Mode.MENU, LinkedOut.summary(f), options)

static func accept(g: Node, id: String) -> void:
	if not LinkedOut.accept(g.state.flags, id): return
	changed(g, LinkedOut.announcement(LinkedOut.person(id)))

## A boost changed the party's stats: rederive, save and show the menu again.
static func changed(g: Node, note: String) -> void:
	g.refresh_growth()
	g.persist()
	g.audio.effect("save")
	g.message(note)
	open(g)

## One post per page, newest first.
static func feed(g: Node, index: int) -> void:
	var posts: Array[String] = LinkedOut.feed(g.state.flags)
	index = clampi(index, 0, posts.size() - 1)
	var options: Array = []
	if index + 1 < posts.size(): options.append(g.option("Older post", func() -> void:feed(g, index + 1)))
	options.append(g.option("Back to LinkedOut", func() -> void:open(g)))
	g.open_menu(g.Mode.MENU, "LinkedOut feed %d/%d\n%s" % [index + 1, posts.size(), posts[index]], options)

## The LinkedOut layout: blue header band, options on the left, the focused profile on the right.
## The focused profile is the highlighted request, or Jules's own profile when none is highlighted.
static func render(g: Node) -> void:
	var f: Dictionary = g.state.flags
	var pending: Array = LinkedOut.pending(f)
	g.panel(Rect2(24, 12, 592, 336))
	g.fill(Rect2(24, 12, 592, 38), BLUE)
	g.label("LinkedOut", Rect2(40, 18, 200, 26), 18, Color.WHITE)
	g.right_label("%d connections  |  %d requests  |  %d views" % [LinkedOut.accepted(f).size(), pending.size(), LinkedOut.views(f)], Rect2(260, 26, 350, 16), Color.WHITE)
	g.render_options(Rect2(40, 62, 230, 264))
	if g.menu_options.any(func(o: Dictionary) -> bool: return o.label == "Back"):
		g.menu_back_rect = Rect2(40, 330, 230, 23)
	var focus: Dictionary = JULES
	var body: String = ""
	if g.caption.contains("\n"):
		body = g.caption.split("\n")[1]
	elif g.selection < pending.size():
		focus = pending[g.selection]
	var id: String = str(focus.get("id", "jules"))
	g.fill(Rect2(282, 62, 1, 264), Color("3d3552"))
	g.portrait_texture(avatar(id), Rect2(296, 66, 64, 64))
	g.label(str(focus.name), Rect2(372, 68, 224, 18), 14, Color("e6d6b1"))
	g.label(str(focus.headline), Rect2(372, 88, 224, 40), 12, Color("8a8296"))
	g.fill(Rect2(296, 140, 300, 1), Color("3d3552"))
	if body.is_empty():
		g.label("Experience", Rect2(296, 148, 300, 14), 12, Color("e8b45c"))
		for i: int in range(WORK.get(id, []).size()):
			g.label("- " + str(WORK[id][i]), Rect2(296, 168 + i * 34, 300, 34), 12, Color("e6d6b1"))
		if focus.has("skill"):
			g.label("Endorsed for " + str(focus.skill) + ": " + LinkedOut.effect_text(focus), Rect2(296, 246, 300, 34), 12, Color("b9d5bc"))
			g.label("Accept to connect.", Rect2(296, 296, 300, 14), 12, Color("e8b45c"))
	else:
		g.label("Feed", Rect2(296, 148, 300, 14), 12, Color("e8b45c"))
		g.label(body, Rect2(296, 168, 300, 150), 12, Color("e6d6b1"))
