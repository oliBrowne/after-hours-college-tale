class_name NativeLinkedOutMenu
extends RefCounted
## The LinkedOut app in the pause menu (data and boosts live in core/linkedout.gd): accept connection
## requests, read the feed. A new request shows a notice once, when control returns to the world.
## "Meeting" a scene character (Eli, Mara, Nell) is a flag set the first time Jules talks to them.
const MEET: Dictionary = {"eli": "met_eli", "floormate_208": "met_eli", "mara": "met_mara", "floormate_laundry": "met_mara",
	"nell": "met_nell", "floormate_lobby": "met_nell"}

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

static func open(g: Node) -> void:
	var f: Dictionary = g.state.flags
	var pending: Array = LinkedOut.pending(f)
	var options: Array = []

	## Show each pending request as a profile option with details.
	for p: Dictionary in pending:
		var id: String = str(p.id)
		options.append(g.option("-> " + str(p.name), func() -> void:accept(g, id)))

	if pending.size() > 1:
		options.append(g.option("Accept all", func() -> void:
			for p: Dictionary in LinkedOut.pending(g.state.flags): LinkedOut.accept(g.state.flags, str(p.id))
			changed(g, "Everyone accepted.")))

	options.append(g.option("Profile feed", func() -> void:feed(g, 0)))
	options.append(g.option("Back", g.pause_menu))

	## Build the main header with profile stats.
	var header: Array[String] = []
	var accepted_count: int = LinkedOut.accepted(f).size()
	var request_count: int = pending.size()
	var view_count: int = LinkedOut.views(f)
	header.append("LINKEDOUT")
	header.append("")
	header.append("Connections: %d  |  Requests: %d  |  Views: %d" % [accepted_count, request_count, view_count])
	header.append("")

	## Add connection request preview info.
	if request_count > 0:
		header.append("PENDING REQUESTS:")
		for p: Dictionary in pending:
			header.append("  " + str(p.name) + " - " + str(p.headline))
			header.append("    Skill: " + str(p.skill) + " (" + LinkedOut.effect_text(p) + ")")
	else:
		header.append("No pending requests.")

	g.open_menu(g.Mode.MENU, "\n".join(header), options)

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

	## Format the feed post as a readable activity.
	var post: String = posts[index]
	var formatted_header: Array[String] = []
	formatted_header.append("LINKEDOUT FEED")
	formatted_header.append("")
	formatted_header.append("Post %d/%d" % [index + 1, posts.size()])
	formatted_header.append("")
	formatted_header.append(post)

	g.open_menu(g.Mode.MENU, "\n".join(formatted_header), options)
