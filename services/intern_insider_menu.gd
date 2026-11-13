class_name NativeInternInsiderMenu
extends RefCounted
## The Intern Insider board in the pause menu (data in core/intern_insider.gd): pick a posting
## to read it and its insider tip. Reading marks it read; the menu badge counts unread postings.

static func badge(flags: Dictionary) -> String:
	var waiting: int = InternInsider.unread(flags).size()
	return " (%d new)" % waiting if waiting > 0 else ""

static func open(g: Node) -> void:
	var options: Array = []
	for p: Dictionary in InternInsider.listed(g.state.flags):
		var id: String = str(p.id)
		var mark: String = "" if InternInsider.read_id(g.state.flags, id) else " *"
		options.append(g.option(str(p.title) + mark, func() -> void:show(g, id)))
	options.append(g.option("Back", g.pause_menu))
	g.open_menu(g.Mode.MENU, InternInsider.summary(g.state.flags), options)

static func show(g: Node, id: String) -> void:
	var p: Dictionary = InternInsider.posting(id)
	if p.is_empty(): return
	if InternInsider.mark_read(g.state.flags, id): g.persist()
	g.open_menu(g.Mode.MENU, InternInsider.detail(p), [g.option("Back to postings", func() -> void:open(g))])
