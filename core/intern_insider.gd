class_name InternInsider
extends RefCounted
## Intern Insider, the internship board app on Jules's phone (a parody of a real internship
## listings site and newsletter). It sits beside LinkedOut in the pause menu. Each posting is a
## real-feeling internship that matches somebody Jules meets, and each carries an "insider tip":
## a plain hint about that person and about how Val's interview works. Postings unlock from the
## same story flags LinkedOut reads. Reading one stores ii_<id> = "read" (saves keep only bool and
## String flags). No stats change, so this can never affect balance. Pure functions over flags.
const POSTINGS: Array = [
	{"id": "sound", "title": "Sound Crew Intern", "company": "Fountain Court Events", "pay": "Paid, $17/hr", "flag": "",
		"blurb": "Haul cables, ride the faders, learn what the room needs before it asks.",
		"tip": "Listen before you answer. People get louder when they are nervous, and Val's questions hit hardest when you rush."},
	{"id": "stage", "title": "Stage Intern", "company": "Campus Auditorium", "pay": "Paid, $16/hr", "flag": "chip_resolution",
		"blurb": "Run cues for Chip. Be on headset. Be on time. Be on book.",
		"tip": "Every attack has a cue. Watch the pattern once, then move on the beat instead of guessing."},
	{"id": "advising", "title": "Advising Intern", "company": "Degree Audit Office", "pay": "For credit", "flag": "claim_resolution",
		"blurb": "Help first-years read a degree audit without crying. Bev will train you.",
		"tip": "Bring a plan, not a panic. Val respects a candidate who already knows the next three steps."},
	{"id": "founder", "title": "Founder's Associate", "company": "DISRUPTR, Pearl Street", "pay": "Unpaid. Equity in a vision.", "flag": "kyle_resolution",
		"blurb": "Ask the questions nobody else will. Kyle will answer one, eventually.",
		"tip": "If a posting says equity in a vision, the vision is the pay. Ask what the job actually is."},
	{"id": "network", "title": "Networking Associate", "company": "Gold Pass Consulting", "pay": "Commission only", "flag": "chad_resolution",
		"blurb": "Coffee chats, all day. Must be comfortable saying 'let's circle back'.",
		"tip": "Small talk is a real skill. Chad is good at it. Do not copy the catchphrase, copy the kindness."},
	{"id": "mentor", "title": "Mentorship Fellow", "company": "Athletics Department", "pay": "Paid, $15/hr", "flag": "deion_resolution",
		"blurb": "Shadow a coach. Learn what it takes to show up every day.",
		"tip": "Showing up beats talent in an interview. Stay in the fight until the last question."},
	{"id": "ai", "title": "Humility Research Intern", "company": "Language Lab", "pay": "Paid, $20/hr", "flag": "autocomplete_resolution",
		"blurb": "Teach a language model to say 'I don't know'. Harder than it sounds.",
		"tip": "Saying 'I don't know' is a strong answer. Val's third stage drops the act when you are honest."},
	{"id": "talent", "title": "Talent Acquisition Intern", "company": "Val's Office, Macky Stage", "pay": "Paid, if selected", "flag": "chapter3_complete",
		"blurb": "Final round. One chair. Everyone is a candidate. Please arrive rested.",
		"tip": "The interviewer is tired too. Answer kindly and the real Val shows up in the last stage."},
]

static func posting(id: String) -> Dictionary:
	for p: Dictionary in POSTINGS:
		if str(p.id) == id: return p
	return {}

## A posting with no flag is always listed; otherwise the story flag has to be set.
static func unlocked(flags: Dictionary, p: Dictionary) -> bool:
	var key: String = str(p.flag)
	if key.is_empty(): return true
	var value: Variant = flags.get(key, false)
	return (value is bool and value) or (value is String and not str(value).is_empty())

static func listed(flags: Dictionary) -> Array:
	return POSTINGS.filter(func(p: Dictionary) -> bool: return unlocked(flags, p))

static func read_id(flags: Dictionary, id: String) -> bool:
	return str(flags.get("ii_" + id, "")) == "read"

static func unread(flags: Dictionary) -> Array:
	return listed(flags).filter(func(p: Dictionary) -> bool: return not read_id(flags, str(p.id)))

static func mark_read(flags: Dictionary, id: String) -> bool:
	var p: Dictionary = posting(id)
	if p.is_empty() or not unlocked(flags, p): return false
	flags["ii_" + id] = "read"
	return true

static func detail(p: Dictionary) -> String:
	return "%s\n%s / %s\n%s\nInsider tip: %s" % [str(p.title), str(p.company), str(p.pay), str(p.blurb), str(p.tip)]

static func summary(flags: Dictionary) -> String:
	return "Intern Insider / %d postings / %d unread / 80,000 interns can't be wrong" % [listed(flags).size(), unread(flags).size()]
