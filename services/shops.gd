class_name NativeShops
extends RefCounted
## Where Buff Bucks go: the food trucks and the coffee cart on the Fountain Court sell supplies, and
## the Book Store register sells keepsakes (the same one-slot-per-member gear as the ones Jules finds,
## PartyGrowth.KEEPSAKES entries marked "shop"). A counter is any object whose id is in SHOPS.
## Supplies respect the pack's cap of 8 in total (the save format allows no more), and a keepsake can
## be bought once. Nothing here uses EXP or stores a number: the balance lives in the buff_bucks flag.
const PACK_LIMIT: int = 8
const SUPPLIES: Dictionary = {
	"granola": "Granola / 30 HP to one friend",
	"cocoa": "Cocoa / 20 HP to everyone",
	"thermos": "Thermos / 45 HP to one friend",
}
## id: {name, seller, hello, stock: [{item | keepsake, price}], bye}
const SHOPS: Dictionary = {
	"truck_chile": {"name": "Green chile truck", "seller": "Cook",
		"hello": "Green chile on everything. Even the granola. Especially the granola. What'll it be?",
		"stock": [{"item": "granola", "price": 8}]},
	"truck_dumplings": {"name": "Dumpling truck", "seller": "Dumpling cook",
		"hello": "Twelve dumplings, one thermos of broth, zero complaints. The thermos is the good part.",
		"stock": [{"item": "thermos", "price": 14}]},
	"truck_waffles": {"name": "Waffle truck", "seller": "Waffle cook",
		"hello": "Waffles at a quarter to anything o'clock. The cocoa's for people who don't want the waffle. Nobody has ever not wanted the waffle.",
		"stock": [{"item": "cocoa", "price": 10}]},
	"coffee_cart": {"name": "Coffee cart", "seller": "Barista",
		"hello": "Hot drinks, cold drinks, and one cocoa for the kids who say they don't drink coffee.",
		"stock": [{"item": "cocoa", "price": 9}, {"item": "thermos", "price": 15}]},
	"register": {"name": "Book Store register", "seller": "Cashier",
		"hello": "Gear's on the wall, tags are on the gear, Buff Bucks are on me. Pick one.",
		"stock": [{"keepsake": "buffs_hoodie", "price": 60}, {"keepsake": "lyric_notebook", "price": 55}, {"keepsake": "wool_socks", "price": 50}]},
}

static func is_shop(id: String) -> bool:
	return SHOPS.has(id)

static func bucks(flags: Dictionary) -> int:
	return NativeRandomFights.bucks(flags)

static func pack_total(inventory: Dictionary) -> int:
	var total: int = 0
	for key: String in inventory: total += int(inventory[key])
	return total

## Whether this keepsake's holder is with Jules (a friend who has not joined cannot be given gear yet).
static func holder_here(flags: Dictionary, keepsake: String) -> bool:
	var member: String = str(PartyGrowth.KEEPSAKES[keepsake].member)
	return member == "jules" or bool(flags.get(member + "_joined", false))

## The stock the player can see right now.
static func stock(flags: Dictionary, shop: String) -> Array:
	return SHOPS[shop].stock.filter(func(e: Dictionary) -> bool: return not e.has("keepsake") or holder_here(flags, str(e.keepsake)))

static func label(entry: Dictionary, flags: Dictionary, inventory: Dictionary) -> String:
	if entry.has("keepsake"):
		var id: String = str(entry.keepsake)
		if PartyGrowth.found(flags, id): return "%s / owned" % PartyGrowth.describe(id)
		return "%s / %d BB" % [PartyGrowth.describe(id), int(entry.price)]
	var item: String = str(entry.item)
	return "%s / %d BB (have %d)" % [str(SUPPLIES[item]), int(entry.price), int(inventory.get(item, 0))]

## The sale itself, on plain dictionaries so a test can run it: returns {"ok", "text"}.
static func buy(state: Dictionary, entry: Dictionary) -> Dictionary:
	var flags: Dictionary = state.flags
	var price: int = int(entry.price)
	if entry.has("keepsake"):
		var id: String = str(entry.keepsake)
		if PartyGrowth.found(flags, id): return {"ok": false, "text": "You already have the %s." % str(PartyGrowth.KEEPSAKES[id].name)}
		if bucks(flags) < price: return {"ok": false, "text": "Not enough Buff Bucks (%d of %d)." % [bucks(flags), price]}
		flags.buff_bucks = str(bucks(flags) - price)
		flags["keepsake_" + id] = true
		var holder: String = str(PartyGrowth.KEEPSAKES[id].member)
		var worn: bool = PartyGrowth.equipped(flags, holder).is_empty()
		if worn: flags["keepsake_" + holder] = id
		return {"ok": true, "text": "%s bought%s. Swap it in Pause > Party." % [str(PartyGrowth.KEEPSAKES[id].name), " and worn" if worn else ""]}
	var item: String = str(entry.item)
	if bucks(flags) < price: return {"ok": false, "text": "Not enough Buff Bucks (%d of %d)." % [bucks(flags), price]}
	if pack_total(state.inventory) >= PACK_LIMIT: return {"ok": false, "text": "Your pack is full (%d of %d)." % [pack_total(state.inventory), PACK_LIMIT]}
	flags.buff_bucks = str(bucks(flags) - price)
	NativeRandomFights.add_item(state.inventory, item)
	return {"ok": true, "text": "Bought one %s." % item}

## interact() hook: true when the object is a counter.
static func handle(g: Node, object: Dictionary) -> bool:
	var id: String = str(object.id)
	if not is_shop(id): return false
	var shop: Dictionary = SHOPS[id]
	g.dialogue([[str(shop.seller), str(shop.hello), "warm"]], func() -> void: open(g, id, ""))
	return true

static func open(g: Node, id: String, note: String) -> void:
	var shop: Dictionary = SHOPS[id]
	var options: Array = []
	for entry: Dictionary in stock(g.state.flags, id):
		var picked: Dictionary = entry
		options.append(g.option(label(entry, g.state.flags, g.state.inventory), func() -> void: purchase(g, id, picked)))
	options.append(g.option("Back", g.resume_world))
	g.open_menu(g.Mode.MENU, caption(g, id) if note.is_empty() else note, options)

static func caption(g: Node, id: String) -> String:
	return "%s / Buff Bucks %d / pack %d of %d" % [str(SHOPS[id].name), bucks(g.state.flags), pack_total(g.state.inventory), PACK_LIMIT]

static func purchase(g: Node, id: String, entry: Dictionary) -> void:
	var result: Dictionary = buy(g.state, entry)
	if bool(result.ok):
		g.audio.effect("save")
		g.refresh_growth()
		g.persist()
	var keep: int = g.selection
	open(g, id, "")
	g.selection = mini(keep, g.menu_options.size() - 1)
	g.caption = str(result.text) + " / " + caption(g, id)
	g.ui_dirty = true
