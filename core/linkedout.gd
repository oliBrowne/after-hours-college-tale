class_name LinkedOut
extends RefCounted
## LinkedOut, Jules's phone app (a parody of a famous networking site). People Jules makes peace
## with, or simply meets, send a connection request; accepting it adds one endorsement, a small
## permanent stat boost read by PartyGrowth. Everything is derived from flags every time, so
## nothing can double-apply and old saves catch up. Pure functions over the flags dictionary.
## Flags (saves only keep bool and String flags): "li_<id>" = "yes" once accepted.
## A boss connects only after a PEACEFUL ending; a forceful one leaves a "viewed your profile"
## post and no request. Scene characters (roommates, Cal, Dev) just need to have been met.
## Stats: max (all three members), power, defence (all members), sync (SYNC at battle start, once).
## Budget at full network: about +44 max HP, +5 power, +3 defence, +20 SYNC.
const PEOPLE: Array = [
	{"id": "imani", "name": "Imani Bell", "headline": "Founder, Sound Check. Open to mixers.", "skill": "Sound Checks", "stat": "sync", "amount": 5, "flag": "imani_joined"},
	{"id": "walt", "name": "Walt", "headline": "The Bridge Keeper. Keeps one light on.", "skill": "Keeping the Lantern Lit", "stat": "max", "amount": 4, "flag": "walt_resolution", "need": "peaceful"},
	{"id": "jakerson", "name": "Jakerson", "headline": "Tennis. Tutor. Roommate. Rule forty-one: nobody walks alone.", "skill": "Patience", "stat": "max", "amount": 4, "flag": "movein_done"},
	{"id": "eli", "name": "Eli", "headline": "Bike mechanic, Farrand Hall 208. First repair's free.", "skill": "Gear Ratios", "stat": "power", "amount": 1, "flag": "met_eli"},
	{"id": "mara", "name": "Mara", "headline": "Painter. Medium: doors.", "skill": "Big Canvas Thinking", "stat": "max", "amount": 4, "flag": "met_mara"},
	{"id": "nell", "name": "Nell", "headline": "Reader. Looking for the last pages.", "skill": "Close Reading", "stat": "sync", "amount": 5, "flag": "met_nell"},
	{"id": "cal", "name": "Cal", "headline": "Night-shift lead, Engineering. Spare wicks on every landing.", "skill": "Load Bearing", "stat": "max", "amount": 4, "flag": "cal_joined"},
	{"id": "dev", "name": "Dev", "headline": "Engineering. Drew a bridge for actual feet.", "skill": "Bridge Design", "stat": "max", "amount": 4, "flag": "dev_met"},
	{"id": "flyer", "name": "Flyerer", "headline": "A club flyer. Please read me.", "skill": "Visibility", "stat": "max", "amount": 4, "flag": "flyer_resolution", "need": "peaceful"},
	{"id": "pinpal", "name": "Pin Pal", "headline": "Bowling pin. Excellent at returns.", "skill": "Return Service", "stat": "max", "amount": 4, "flag": "pinpal_resolution", "need": "peaceful"},
	{"id": "claim", "name": "Advisor Bev", "headline": "Academic Advisor. Have you checked your degree audit?", "skill": "Degree Audits", "stat": "defence", "amount": 1, "flag": "claim_resolution", "need": "peaceful"},
	{"id": "chip", "name": "Chip", "headline": "Stage Manager. Places, everyone.", "skill": "Cueing", "stat": "power", "amount": 1, "flag": "chip_resolution", "need": "peaceful"},
	{"id": "encore", "name": "ENCORE", "headline": "A show seeking an ending.", "skill": "Closure", "stat": "sync", "amount": 5, "flag": "encore_resolution", "need": "peaceful"},
	{"id": "errata", "name": "Gwen the Red", "headline": "Seventh-year TA. See me after class.", "skill": "Constructive Feedback", "stat": "max", "amount": 4, "flag": "errata_resolution", "need": "peaceful"},
	{"id": "autocomplete", "name": "AUTOCOMPLETE", "headline": "Language model. Learning to say I don't know.", "skill": "Humility", "stat": "power", "amount": 1, "flag": "autocomplete_resolution", "need": "peaceful"},
	{"id": "eric", "name": "Professor Eric Bogatin", "headline": "Professor. Rule of Thumb. Measure twice.", "skill": "Measuring Twice", "stat": "power", "amount": 1, "flag": "eric_resolution", "need": "peaceful"},
	{"id": "deion", "name": "Deion Sanders", "headline": "Coach. Prime Time. Open to mentoring.", "skill": "Mentoring", "stat": "defence", "amount": 1, "flag": "deion_resolution", "need": "peaceful"},
	{"id": "todd", "name": "Todd Saliman", "headline": "President. Reads every form.", "skill": "Informed Consent", "stat": "max", "amount": 4, "flag": "todd_resolution", "need": "peaceful"},
	{"id": "cone", "name": "Captain Lance", "headline": "Captain, Flatirons Peloton. On your left.", "skill": "Cadence", "stat": "sync", "amount": 5, "flag": "cone_resolution", "need": "peaceful"},
	{"id": "rook", "name": "Rook", "headline": "Night Marshal. Master of keys.", "skill": "Opening Doors", "stat": "max", "amount": 4, "flag": "rook_resolution", "need": "peaceful"},
	{"id": "tanner", "name": "Tanner", "headline": "Rush chair. 8 AM person, as of last night.", "skill": "Showing Up Early", "stat": "defence", "amount": 1, "flag": "tanner_resolution", "need": "peaceful"},
	{"id": "kyle", "name": "Kyle", "headline": "Founder, CEO, Visionary. Ask me anything. Finally.", "skill": "Asking the Question", "stat": "power", "amount": 1, "flag": "kyle_resolution", "need": "peaceful"},
	{"id": "chad", "name": "Chad", "headline": "Networking Legend. Coffee chat?", "skill": "Small Talk", "stat": "max", "amount": 4, "flag": "chad_resolution", "need": "peaceful"},
]
const STAT_TEXT: Dictionary = {"max": "+%d max HP", "power": "+%d power", "defence": "+%d defense", "sync": "+%d SYNC at battle start"}

static func person(id: String) -> Dictionary:
	for p: Dictionary in PEOPLE:
		if str(p.id) == id: return p
	return {}

## Whether this person is in Jules's orbit yet (a request can be sent).
static func unlocked(flags: Dictionary, p: Dictionary) -> bool:
	var value: Variant = flags.get(str(p.flag), false)
	if p.has("need"): return value is String and str(value) == str(p.need)
	return (value is bool and value) or (value is String and not str(value).is_empty())

static func accepted_id(flags: Dictionary, id: String) -> bool:
	return str(flags.get("li_" + id, "")) == "yes"

static func accepted(flags: Dictionary) -> Array:
	return PEOPLE.filter(func(p: Dictionary) -> bool: return accepted_id(flags, str(p.id)) and unlocked(flags, p))

static func pending(flags: Dictionary) -> Array:
	return PEOPLE.filter(func(p: Dictionary) -> bool: return unlocked(flags, p) and not accepted_id(flags, str(p.id)) and not ignored_id(flags, str(p.id)))

static func ignored_id(flags: Dictionary, id: String) -> bool:
	return str(flags.get("li_" + id, "")) == "no"

## Requests the player turned down; they leave the list but can be restored.
static func ignored(flags: Dictionary) -> Array:
	return PEOPLE.filter(func(p: Dictionary) -> bool: return unlocked(flags, p) and ignored_id(flags, str(p.id)))

static func ignore(flags: Dictionary, id: String) -> bool:
	var p: Dictionary = person(id)
	if p.is_empty() or not unlocked(flags, p) or accepted_id(flags, id): return false
	flags["li_" + id] = "no"
	return true

static func restore(flags: Dictionary, id: String) -> bool:
	if not ignored_id(flags, id): return false
	flags.erase("li_" + id)
	return true

## Bosses beaten the hard way: they looked at the profile and nothing else.
static func viewed_only(flags: Dictionary) -> Array:
	return PEOPLE.filter(func(p: Dictionary) -> bool: return p.has("need") and str(flags.get(str(p.flag), "")) not in ["", str(p.need)])

## The ids Jules can name as references (Val's interview skips a question when its person vouches).
static func accepted_ids(flags: Dictionary) -> Array:
	return accepted(flags).map(func(p: Dictionary) -> String: return str(p.id))

static func bonus(flags: Dictionary, stat: String) -> int:
	var total: int = 0
	for p: Dictionary in accepted(flags):
		if str(p.stat) == stat: total += int(p.amount)
	return total

static func effect_text(p: Dictionary) -> String:
	return str(STAT_TEXT[p.stat]) % int(p.amount)

static func accept(flags: Dictionary, id: String) -> bool:
	var p: Dictionary = person(id)
	if p.is_empty() or not unlocked(flags, p) or accepted_id(flags, id): return false
	flags["li_" + id] = "yes"
	return true

## The "thrilled to announce" post for a new connection.
static func announcement(p: Dictionary) -> String:
	return "Thrilled to announce: Jules is now connected with %s. Endorsed for %s (%s)." % [str(p.name), str(p.skill), effect_text(p)]

## The profile feed, newest connection first, then the people who only looked.
static func feed(flags: Dictionary) -> Array[String]:
	var posts: Array[String] = []
	var mine: Array = accepted(flags)
	mine.reverse()
	for p: Dictionary in mine: posts.append(announcement(p))
	for p: Dictionary in viewed_only(flags): posts.append("%s viewed your profile. Message left on read." % str(p.name))
	if posts.is_empty(): posts.append("No activity yet. Go meet somebody.")
	return posts

## The standing gag: how many people viewed Jules's profile this week.
static func views(flags: Dictionary) -> int:
	return 1 + 3 * accepted(flags).size() + 2 * pending(flags).size() + int(str(flags.get("wander_wins", "0")))

static func summary(flags: Dictionary) -> String:
	return "LinkedOut / %d connections / %d requests / %d people viewed your profile" % [accepted(flags).size(), pending(flags).size(), views(flags)]
