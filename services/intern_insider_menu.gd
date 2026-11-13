class_name NativeInternInsiderMenu
extends RefCounted
## The Intern Insider app in the pause menu (data in core/intern_insider.gd). Layout mirrors the
## LinkedOut screen: a nav bar, a postings list down the left and the focused posting as a card on
## the right. Opening a posting reads it and offers Easy Apply. main.gd hands every caption that
## starts with "Intern Insider" to render(); a caption with a second line is the posting view.
const TEAL: Color = Color("0f8b8d")
const BANNER: Color = Color("17454a")
const STRIPE: Color = Color("2aa6a8")
const LOGOS: Array[Color] = [Color("2d5c8a"), Color("7a3e5c"), Color("3f7f5a"), Color("8a6a2e"), Color("4b4a7a")]
const INK: Color = Color("e6d6b1")
const MUTED: Color = Color("8a8296")
const AMBER: Color = Color("e8b45c")
const LINE: Color = Color("3d3552")

static func is_board(caption: String) -> bool:
	return caption.begins_with("Intern Insider")

static func badge(flags: Dictionary) -> String:
	var waiting: int = InternInsider.unread(flags).size()
	return " (%d new)" % waiting if waiting > 0 else ""

## "Intern Insider: new postings" once per newly listed posting, never over another notice.
static func notify(g: Node) -> void:
	var f: Dictionary = g.state.flags
	var known: int = InternInsider.listed(f).size() + InternInsider.offers(f)
	if known <= maxi(1, int(str(f.get("ii_seen", "0")))) or int(g.notice_ticks) > 0: return
	f.ii_seen = str(known)
	g.message("Intern Insider: something new on the board. Pause > Intern Insider.")

static func open(g: Node) -> void:
	var options: Array = []
	for p: Dictionary in InternInsider.listed(g.state.flags):
		var id: String = str(p.id)
		options.append(g.option(str(p.title), func() -> void:show(g, id)))
	options.append(g.option("Back", g.pause_menu))
	g.open_menu(g.Mode.MENU, InternInsider.summary(g.state.flags), options)

static func show(g: Node, id: String) -> void:
	var p: Dictionary = InternInsider.posting(id)
	if p.is_empty(): return
	if InternInsider.mark_read(g.state.flags, id): g.persist()
	var options: Array = []
	if not InternInsider.applied_id(g.state.flags, id):
		options.append(g.option("Easy Apply", func() -> void:apply(g, id)))
	options.append(g.option("Back to postings", func() -> void:open(g)))
	g.open_menu(g.Mode.MENU, "Intern Insider\n" + id, options)

static func apply(g: Node, id: String) -> void:
	var bonus: int = InternInsider.apply(g.state.flags, id)
	if bonus <= 0: return
	g.persist()
	g.audio.effect("save")
	g.message("Application sent. +%d Buff Bucks for being proactive." % bonus)
	show(g, id)

static func render(g: Node) -> void:
	var f: Dictionary = g.state.flags
	var posts: Array = InternInsider.listed(f)
	g.panel(Rect2(8, 8, 624, 344))
	g.fill(Rect2(8, 8, 624, 28), TEAL)
	g.fill(Rect2(16, 12, 20, 20), Color.WHITE)
	g.label("II", Rect2(18, 14, 20, 16), 12, TEAL)
	var nav: Array = [["Postings", 52], ["Applied", 112], ["Offers", 170], ["Newsletter", 220]]
	for item: Array in nav: g.label(str(item[0]), Rect2(float(item[1]), 14.0, 110.0, 18.0), 12, Color.WHITE)
	g.right_label("%d applied  |  %d offers" % [InternInsider.applied(f).size(), InternInsider.offers(f)], Rect2(392, 14, 232, 18), Color.WHITE)
	g.panel(Rect2(12, 42, 196, 304))
	g.label("Open postings (%d)" % posts.size(), Rect2(22, 48, 180, 18), 12, AMBER)
	g.render_options(Rect2(18, 68, 184, 250))
	if g.menu_options.any(func(o: Dictionary) -> bool: return o.label == "Back"):
		g.menu_back_rect = Rect2(18, 322, 184, 23)
	g.panel(Rect2(216, 42, 412, 304))
	var focus: Dictionary = {}
	var viewing: bool = g.caption.contains("\n")
	if viewing: focus = InternInsider.posting(g.caption.split("\n")[1])
	elif g.selection >= 0 and g.selection < posts.size(): focus = posts[g.selection]
	if focus.is_empty(): _welcome(g)
	else: _card(g, focus, viewing)

static func _logo(g: Node, at: Vector2, size: float, letters: String, color: Color) -> void:
	g.fill(Rect2(at, Vector2(size, size)), color)
	var node: Label = g.label(letters, Rect2(at + Vector2(0, size / 2.0 - 14.0), Vector2(size, 28)), 12 if size < 40 else 18, Color.WHITE)
	node.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

static func _centred(g: Node, text: String, rect: Rect2, color: Color) -> void:
	var node: Label = g.label(text, rect, 12, color)
	node.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

static func _welcome(g: Node) -> void:
	g.fill(Rect2(217, 43, 410, 30), BANNER)
	g.fill(Rect2(217, 73, 410, 12), STRIPE)
	g.label("Intern Insider", Rect2(228, 76, 320, 28), 18, INK)
	g.label("Clutter-free internship postings. Real insider tips.", Rect2(228, 106, 390, 16), 12, MUTED)
	g.label("80,000 interns can't be wrong. Several of them are wrong sometimes.", Rect2(228, 126, 390, 34), 12, INK)

static func _card(g: Node, p: Dictionary, viewing: bool) -> void:
	var f: Dictionary = g.state.flags
	var id: String = str(p.id)
	var logo_color: Color = LOGOS[absi(id.hash()) % LOGOS.size()]
	g.fill(Rect2(217, 43, 410, 30), BANNER)
	g.fill(Rect2(217, 73, 410, 12), STRIPE)
	_logo(g, Vector2(228, 90), 56.0, str(p.logo), logo_color)
	g.label(str(p.title), Rect2(294, 88, 330, 28), 18, INK)
	g.label("%s  -  %s" % [str(p.company), str(p.where)], Rect2(294, 112, 330, 18), 12, INK)
	g.label("%s  |  Rated %s of 5  |  %d interns viewing" % [str(p.pay), InternInsider.rating(p), InternInsider.viewing(p)], Rect2(294, 132, 330, 16), 12, MUTED)
	var done: bool = InternInsider.applied_id(f, id)
	g.fill(Rect2(228, 154, 104, 20), Color("3d3552") if done else TEAL)
	_centred(g, "Applied" if done else "Easy Apply", Rect2(228, 156, 104, 16), INK if done else Color.WHITE)
	var state: String = InternInsider.status(f, p)
	g.label(state, Rect2(342, 156, 280, 16), 12, AMBER if state == "Offer received" else MUTED)
	g.fill(Rect2(228, 182, 396, 1), LINE)
	g.label("About the role", Rect2(228, 186, 380, 16), 12, AMBER)
	g.label(str(p.blurb), Rect2(228, 204, 390, 44), 12, INK)
	g.fill(Rect2(228, 254, 396, 1), LINE)
	g.label("Insider tip", Rect2(228, 258, 380, 16), 12, AMBER)
	if viewing or InternInsider.read_id(f, id):
		g.label(str(p.tip), Rect2(228, 276, 390, 64), 12, INK)
	else:
		g.label("Open the posting to read the tip.", Rect2(228, 276, 390, 20), 12, MUTED)
