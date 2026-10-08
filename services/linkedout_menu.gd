class_name NativeLinkedOutMenu
extends RefCounted
## The LinkedOut app in the pause menu (data and boosts live in core/linkedout.gd): accept connection
## requests, read the feed. A new request shows a notice once, when control returns to the world.
## "Meeting" a scene character (Eli, Mara, Nell) is a flag set the first time Jules talks to them.
## Drawing: main.gd hands LinkedOut captions (starting "LinkedOut") to render() for the profile layout.
const MEET: Dictionary = {"eli": "met_eli", "floormate_208": "met_eli", "mara": "met_mara", "floormate_laundry": "met_mara",
	"nell": "met_nell", "floormate_lobby": "met_nell"}
const BLUE: Color = Color("0a66c2")
const BANNER: Color = Color("1d3f63")
const SKINS: Array[Color] = [Color("f1c9a5"), Color("c68e62"), Color("8d5a3b"), Color("5c3a26")]
const SHIRTS: Array[Color] = [Color("2d5c8a"), Color("7a3e5c"), Color("3f7f5a"), Color("c9a24a"), Color("4b4a7a")]
const BACKDROPS: Array[Color] = [Color("cfe3f2"), Color("e7dcc8"), Color("d4e8d6"), Color("e9d3d3")]
const MONOGRAMS: Array[Color] = [Color("2d5c8a"), Color("7a3e5c"), Color("3f7f5a"), Color("8a6a2e"), Color("4b4a7a")]
const SPEAKERS: Dictionary = {"jules": "Jules", "imani": "Imani", "walt": "Walt", "jakerson": "Jakerson", "eli": "Eli",
	"mara": "Mara", "nell": "Nell", "cal": "Cal", "dev": "Dev", "flyer": "Flyerer", "pinpal": "Pin Pal", "claim": "Advisor Bev",
	"chip": "Chip", "encore": "ENCORE", "errata": "Gwen the Red", "autocomplete": "AUTOCOMPLETE", "eric": "Professor Eric",
	"deion": "Deion Sanders", "todd": "Todd Saliman", "cone": "Captain Lance", "rook": "Rook", "tanner": "Tanner", "kyle": "Kyle",
	"chad": "Chad"}
const JULES: Dictionary = {"id": "jules", "name": "Jules Navarro", "headline": "Campus radio volunteer. Open to mixers.", "skill": "Mixing"}
const EDUCATION: String = "University of Colorado Boulder"
const WORK: Dictionary = {
	"jules": ["Campus radio, volunteer DJ (2025 - present)", "Sound crew, Fountain Court events (2024)"],
	"imani": ["Founder, Sound Check (freshman year - present)", "Sound tech, campus venues (2024)"],
	"walt": ["Lantern keeper, Broadway underpass (since 1994)", "Night watch, Boulder Creek path (2011 - 2019)"],
	"jakerson": ["Tennis club, CU Boulder (freshman year - present)", "Roommate, Farrand Hall (freshman year)"],
	"eli": ["Bike mechanic, Farrand Hall 208 (2025 - present)", "Wheel truing, Boulder bike co-op (2023 - 2025)"],
	"mara": ["Painter, Farrand laundry room murals (2025 - present)", "Set painter, campus theater (2024)"],
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
	"eric": ["Professor, Electrical Engineering, CU Boulder", "Author and teacher, signal integrity"],
	"deion": ["Head Coach, Colorado Buffaloes football", "Head Coach, Jackson State football"],
	"todd": ["President, University of Colorado system", "Budget and finance, University of Colorado system"],
	"cone": ["Captain, Flatirons Peloton (2022 - present)", "Road racer, regional circuit (2016 - 2022)"],
	"rook": ["Night Marshal, residence halls (2025 - present)", "Key control, Farrand Hall (2023 - 2025)"],
	"tanner": ["Rush chair, Interfraternity Council (2026)", "Early shift, campus coffee cart (2025)"],
	"kyle": ["Founder and CEO, DISRUPTR (2026)", "Visionary, Pearl Street office (2025)"],
	"chad": ["Networking, Gold Pass Consulting (2025 - present)", "Sales, Summit Ventures (2023 - 2025)"],
}
static var _avatars: Dictionary = {}
static var _headshots: Dictionary = {}

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
	for p: Dictionary in pending:
		var skip: String = str(p.id)
		options.append(g.option("Ignore " + str(p.name), func() -> void:
			LinkedOut.ignore(g.state.flags, skip)
			changed(g, "Request from %s ignored." % str(LinkedOut.person(skip).name))))
	if not LinkedOut.ignored(f).is_empty():
		options.append(g.option("Restore ignored (%d)" % LinkedOut.ignored(f).size(), func() -> void:
			for p: Dictionary in LinkedOut.ignored(g.state.flags): LinkedOut.restore(g.state.flags, str(p.id))
			changed(g, "Ignored requests are back.")))
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

## A 32x32 pixel avatar for people with no drawn portrait: backdrop, shoulders, head, hair.
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

## The person's own in-game portrait, cropped to a round headshot with a light ring.
## Falls back to the pixel avatar when the person has no drawn portrait.
static func headshot(id: String, px: int) -> Texture2D:
	var key: String = "%s/%d" % [id, px]
	if _headshots.has(key): return _headshots[key]
	var raw: Texture2D = null
	var art: String = NativeBossArt.art_id(id)
	if NativeBossArt.drawn(art): raw = NativeBossArt.portrait(art, 0)
	elif SPEAKERS.has(id): raw = NativeCastArt.portrait(str(SPEAKERS[id]), 0)
	if raw == null: return avatar(id)
	var src: Image = NativePixelCast.source_image(raw)
	NativePixelCast.crisp(src)
	var used: Rect2i = src.get_used_rect()
	if not used.has_area(): return avatar(id)
	src = src.get_region(used)
	src.convert(Image.FORMAT_RGBA8)
	var inner: int = px - 4
	var scale: float = float(inner) / maxf(src.get_width(), src.get_height())
	src.resize(maxi(1, roundi(src.get_width() * scale)), maxi(1, roundi(src.get_height() * scale)), Image.INTERPOLATE_NEAREST)
	var out: Image = Image.create(px, px, false, Image.FORMAT_RGBA8)
	out.fill(Color(0, 0, 0, 0))
	var centre: float = (px - 1) / 2.0
	var backdrop: Color = BACKDROPS[absi(id.hash()) % BACKDROPS.size()]
	for y: int in range(px):
		for x: int in range(px):
			var d: float = Vector2(x - centre, y - centre).length()
			if d <= centre - 1.0: out.set_pixel(x, y, backdrop)
			elif d <= centre + 0.5: out.set_pixel(x, y, Color("e6d6b1"))
	out.blend_rect(src, Rect2i(Vector2i.ZERO, src.get_size()), Vector2i((px - src.get_width()) / 2, px - 2 - src.get_height()))
	for y: int in range(px):
		for x: int in range(px):
			if Vector2(x - centre, y - centre).length() > centre + 0.5: out.set_pixel(x, y, Color(0, 0, 0, 0))
	var texture: Texture2D = ImageTexture.create_from_image(out)
	_headshots[key] = texture
	return texture

static func connections(id: String) -> int:
	return 40 + absi(id.hash() / 13) % 900

static func endorsements(id: String) -> int:
	return 3 + absi(id.hash() / 17) % 40

static func mutuals(id: String) -> String:
	var names: Array[String] = []
	for p: Dictionary in LinkedOut.PEOPLE:
		if names.size() == 2: break
		if str(p.id) != id and absi(id.hash() + int(names.size())) % 3 == 0: names.append(str(p.name))
	return "Mutual connections: " + ", ".join(PackedStringArray(names)) if not names.is_empty() else ""

## Renders the LinkedOut layout: a nav bar, the request sidebar, and the focused profile or feed post.
static func render(g: Node) -> void:
	var f: Dictionary = g.state.flags
	var pending: Array = LinkedOut.pending(f)
	g.panel(Rect2(8, 8, 624, 344))
	g.fill(Rect2(8, 8, 624, 28), BLUE)
	g.fill(Rect2(16, 12, 20, 20), Color.WHITE)
	g.label("in", Rect2(18, 14, 20, 16), 12, BLUE)
	var nav: Array = [["Home", 52], ["My Network", 110], ["Jobs", 190], ["Messaging", 236], ["Notifications", 314]]
	for item: Array in nav: g.label(str(item[0]), Rect2(float(item[1]), 14.0, 110.0, 18.0), 12, Color.WHITE)
	g.right_label("%d connections  |  %d requests" % [LinkedOut.accepted(f).size(), pending.size()], Rect2(392, 14, 232, 18), Color.WHITE)
	g.panel(Rect2(12, 42, 196, 304))
	g.label("Manage requests (%d)" % pending.size(), Rect2(22, 48, 180, 18), 12, Color("e8b45c"))
	g.render_options(Rect2(18, 68, 184, 250))
	if g.menu_options.any(func(o: Dictionary) -> bool: return o.label == "Back"):
		g.menu_back_rect = Rect2(18, 322, 184, 23)
	g.panel(Rect2(216, 42, 412, 304))
	if g.caption.contains("\n"):
		_feed_card(g, g.caption.split("\n")[1], g.caption.split("\n")[0])
	else:
		# Menu order: Accept each, [Accept all], Ignore each, then the rest.
		var n: int = pending.size()
		var skip_at: int = n + (1 if n > 1 else 0)
		var which: int = g.selection if g.selection < n else g.selection - skip_at if g.selection >= skip_at and g.selection < skip_at + n else -1
		var focus: Dictionary = JULES if which < 0 else pending[which]
		_profile_card(g, focus, which >= 0)

static func _profile_card(g: Node, focus: Dictionary, requesting: bool) -> void:
	var id: String = str(focus.id)
	g.fill(Rect2(217, 43, 410, 30), BANNER)
	g.fill(Rect2(217, 73, 410, 12), Color("2b6aa0"))
	g.portrait_texture(headshot(id, 64), Rect2(228, 56, 64, 64))
	g.label(str(focus.name), Rect2(302, 72, 320, 28), 18, Color("e6d6b1"))
	g.label(str(focus.headline), Rect2(302, 100, 320, 34), 12, Color("e6d6b1"))
	var count: int = LinkedOut.accepted(g.state.flags).size() if id == "jules" else connections(id)
	g.label("Boulder, Colorado  -  %d connections" % count, Rect2(302, 134, 320, 16), 12, Color("8a8296"))
	if requesting:
		g.fill(Rect2(228, 154, 92, 20), BLUE)
		_centred(g, "Connect", Rect2(228, 156, 92, 16), Color.WHITE)
		g.fill(Rect2(328, 154, 80, 20), Color("3d3552"))
		_centred(g, "Ignore", Rect2(328, 156, 80, 16), Color("e6d6b1"))
	g.label(mutuals(id), Rect2(228, 178, 390, 16), 12, Color("8a8296"))
	g.fill(Rect2(228, 198, 396, 1), Color("3d3552"))
	g.label("About: Known for %s." % str(focus.skill), Rect2(228, 203, 390, 16), 12, Color("e6d6b1"))
	g.fill(Rect2(228, 222, 396, 1), Color("3d3552"))
	g.label("Skills: %s" % str(focus.skill), Rect2(228, 227, 300, 16), 12, Color("e8b45c"))
	g.right_label("%d endorsements" % endorsements(id), Rect2(420, 227, 200, 16), Color("8a8296"))
	g.fill(Rect2(228, 246, 396, 1), Color("3d3552"))
	g.label("Experience", Rect2(228, 250, 380, 16), 12, Color("e8b45c"))
	var jobs: Array = WORK.get(id, [])
	for i: int in range(jobs.size()):
		_job_row(g, str(jobs[i]), 268 + i * 22, i)
	g.fill(Rect2(228, 316, 396, 1), Color("3d3552"))
	_monogram(g, Vector2(228, 324), "CU", Color("c9a24a"))
	g.label(EDUCATION, Rect2(252, 324, 290, 16), 12, Color("e6d6b1"))
	g.right_label("Education", Rect2(540, 324, 80, 16), Color("8a8296"))

static func _job_row(g: Node, entry: String, y: float, index: int) -> void:
	var cut: int = entry.rfind(" (")
	var role: String = entry.substr(0, cut) if cut >= 0 else entry
	var dates: String = entry.substr(cut + 2).trim_suffix(")") if cut >= 0 else ""
	_monogram(g, Vector2(228, y), role.substr(0, 1), MONOGRAMS[index % MONOGRAMS.size()])
	g.label(role, Rect2(252, y, 290, 16), 12, Color("e6d6b1"))
	g.right_label(dates, Rect2(540, y, 80, 16), Color("8a8296"))

static func _centred(g: Node, text: String, rect: Rect2, color: Color) -> void:
	var node: Label = g.label(text, rect, 12, color)
	node.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

static func _monogram(g: Node, at: Vector2, letters: String, color: Color) -> void:
	g.fill(Rect2(at, Vector2(16, 16)), color)
	_centred(g, letters, Rect2(at + Vector2(0, 2), Vector2(16, 14)), Color.WHITE)

static func _feed_card(g: Node, body: String, header: String) -> void:
	var stamp: Label = g.label(header, Rect2(420, 52, 200, 16), 12, Color("8a8296"))
	stamp.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	g.portrait_texture(headshot("jules", 44), Rect2(228, 54, 44, 44))
	g.label("Jules Navarro", Rect2(280, 52, 300, 28), 18, Color("e6d6b1"))
	g.label("Campus radio volunteer. Open to mixers.", Rect2(280, 74, 330, 16), 12, Color("8a8296"))
	g.label(body, Rect2(228, 112, 390, 170), 12, Color("e6d6b1"))
	g.fill(Rect2(228, 292, 396, 1), Color("3d3552"))
	var stats: String = "%d likes  |  %d comments  |  %d reposts" % [4 + body.length() % 19, 1 + body.length() % 5, body.length() % 3]
	g.label(stats, Rect2(228, 298, 390, 16), 12, Color("8a8296"))
	g.fill(Rect2(228, 318, 396, 1), Color("3d3552"))
	var actions: Array = ["Like", "Comment", "Repost", "Send"]
	for i: int in range(actions.size()):
		_centred(g, str(actions[i]), Rect2(228 + i * 100, 324, 96, 16), Color("e6d6b1"))
