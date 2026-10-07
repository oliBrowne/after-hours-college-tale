# Dodge pattern scripts

Every boss's defend phase runs on `DodgeBox` (`core/dodge_box.gd`). The boss's
attacks live in one script, `core/dodge_patterns_<id>.gd`, found by file name
(`DodgeBox.handles(id)` is just "does that file exist"). The flyer fight has an
empty `boss_id` in main.gd; it is normalized to `flyer`.

A script is a plain `extends RefCounted` file of static functions over the
pattern Dictionary `s`. It does not need a `class_name`.

## Coordinates

- **Arena space**: (0,0)-(256,120) is the resting box; main.gd draws it at
  screen offset (192,166). The box rests at centre (128,60), size 256x120.
- **Box space**: centre origin, unrotated. The soul always lives here
  (`s.soul.x / y`). Bullets with `space = "box"` live here too and ride along
  when the box moves, resizes or turns. Objectives are in box space.
- `D.to_world(s, local)`, `D.to_local(s, world)`, `D.soul_world(s)`,
  `D.centre(s)`, `D.half(s)` (half size) convert between them.
- main.gd's defend layout has UI panels left and right of the arena (screen
  x 184 and 456, arena x -8 and 264) and the action button and party bars
  below (from about arena y 125). The engine slides the box back between the
  side panels on its own (`_keep_between_panels`), so a full-width box cannot
  slide sideways; keep h <= 120 and cy near 60 apart from brief turns.

## Required functions

```gdscript
const D = preload("res://core/dodge_box.gd")
const ORDER: Array[String] = ["a", "b", "c", "d", "e"]   # one attack per turn, cycling
const PHASES: Array[int] = [0, 1]                         # stages main.gd can pass

static func setup(s: Dictionary) -> void
	# Pick the attack: ORDER[int(s.turn) % ORDER.size()] (s.turn = boss_rounds).
	# Must set: s.patternId, s.length (ticks after lead-in, ~420-600),
	#           s.phaseName (shown under the box), s.hint (two short lines max,
	#           ~90 characters: it is drawn in a 362x55 label above the box).
	# May set:  soul mode (D.set_mode), s.lanes / s.laneY / s.floorY, objectives,
	#           any custom fields the attack needs.
static func tick(s: Dictionary, t: int) -> void
	# Called once per pattern tick while 0 <= t < length - 40 (t = ticks since
	# lead-in). Spawn bullets, warnings, tweens; run timed promise logic here.
static func after(s: Dictionary, t: int) -> void
	# Called every pattern tick after bullets moved and collided (t may be < 0).
static func confirm(s: Dictionary) -> void
	# Called when the player presses confirm (after objective confirms ran).
static func promise_complete(s: Dictionary) -> bool
	# Evaluated every tick; main.gd reads s.promiseComplete when the turn ends.
static func progress(s: Dictionary) -> String
	# The promise progress text main.gd shows (live and after the turn).
	# Keep the wording of the old encounter (see core/*_encounter.gd).
static func draw_under(c: CanvasItem, s: Dictionary, v: Node2D) -> void
	# Inside the box, clipped to it, before bullets (scenery, props, lanes).
static func draw_over(c: CanvasItem, s: Dictionary, v: Node2D) -> void
	# On top, unclipped (things around the box: rigs, banners, labels).
static func draw_bullet(c: CanvasItem, b: Dictionary, at: Vector2, turn: float, alpha: float, v: Node2D) -> bool
	# Draw custom bullet shapes; return true when drawn, false to fall back to
	# the view's built-in shapes. at = screen position, turn = screen rotation.
```

Optional: `static func preview(s: Dictionary, phase: int) -> void` sets what
main.gd sets right after `create` (`revision`, `rejected`, `boundary`) so the
preview tools can exercise every phase. main.gd assigns `s.revision` and
`s.rejected` AFTER `setup` runs, so read them lazily in `tick`, never cache
them in `setup`.

## Engine state you can use (`s`)

- `s.phase` (stage from main.gd), `s.turn`, `s.clock`, `s.leadIn`, `s.duration`,
  `s.beat`, `s.musicBase` (beat = 30 ticks at 120 BPM: `(s.clock + s.musicBase) % 30 == 0`
  is the downbeat), `s.promised` (battle.promise this turn), `s.pressed`.
- `s.box` {cx, cy, w, h, rot}: animate it only with `D.box_to(s, {"w": 140, "rot": PI/4}, dur, delay, ease)`;
  ease is "inout" (default), "in", "out", "linear" or "back". The engine eases the
  box home in the last 40 ticks.
- `s.soul` {x, y, mode, v, grounded, shield, gravity, ducking, lane}.
  `D.set_mode(s, "red" | "blue" | "green" | "lanes" | "flipper")`.
  - blue: gravity `s.soul.gravity` (box space, e.g. Vector2.DOWN); up or confirm
    jumps (hold for height); precision while grounded ducks (smaller hitbox).
  - green: pinned at the centre; the shield turns to the pressed direction and
    blocks bullets with `target = true` coming from that side.
  - lanes: `s.lanes` = array of box-space x positions, `s.laneY` = y. Left/right
    taps hop one lane.
  - flipper: runs along `s.floorY`; confirm swings a flipper for 12 ticks that
    returns bullets with `returnable = true` (counts `s.deflections`).
- `s.audit = true`: any movement input is a hit while it is set (Todd).
- `s.wind` (Vector2, arena px/tick) pushes red and blue souls.
- `s.safe`: Array of Rect2 in box space; hits inside are ignored (lit
  foundations, quiet pockets, shelters).
- `s.banner` / `D.banner(s, "TEXT", ticks)`; `s.bannerColor` overrides its colour.
- `s.hits`, `s.grazes`, `s.grazeDelta` (managed by the engine).

## Bullets: `D.shot(s, props)` returns the Dictionary

Defaults: `x y vx vy ax ay r=4 w=4 h=4 shape="dot" rot spin age life=900 collide="circle" space="arena" arm=0`.

- Movement: velocity + acceleration (`ax/ay`), `drag` (multiplier per tick),
  `wave` {amp, freq, phase} sway around the travel line, `orbit`
  {ox, oy, radius, angle, av, dr, minRadius, maxRadius}, `home` (ticks of
  steering toward the soul, `homeTurn` rad/tick), `bounce` (restitution off the
  box floor, box space only), `hold` + `arm` (sit still until age > arm).
- Collision `collide`: "circle" (r, swept), "rect" (half sizes w/h, rotated by
  rot), "ring" {radius, grow, thick, gap, gapWidth, gapSpin, maxRadius}: an
  expanding ring with one gap, "beam" {angle, len, w0, w1, warn, live, av}: a
  cone/line that warns for `warn` ticks then is live for `live` ticks,
  "none" (decoration).
- `pierce = false` removes a bullet when it hits. `friendly = true` never hurts.
  `cue = true` bullets never hurt (they are pickups for green mode).
  `target = true` marks a green-mode note (drawn outside the box too).
  `fade` (ticks) makes it fade and stop colliding.
- Built-in shapes the view draws: paper, sheet, leaf, grit, can, bag, drop, note,
  cue_note, flip_note, squeal, confetti (hue 0-3), rose, ring, dot. Anything
  else: draw it in `draw_bullet`.

Warnings (draw-only telegraphs): `D.warn(s, props, life, loud)`. Built-in kinds:
`lane` {x|y, w|h, horizontal} (a red band), `edge` {x, y, dir} chevron, `cue`
{x, y} green box outline, `puddle`, `arrows` {dir}, `spin`, and over the box
`gust` {dir}, `flip`, `curtain`. Loud warnings play main.gd's warning sound.
Every attack must be telegraphed before it can hurt (a warning, a beam's warn
time, `arm`, or a bullet entering slowly from off-box).

Effects (draw-only): `D.effect(s, kind, arena_point, life, extra)` with kind
graze, hit, block, kept, gutter, lantern, splash, mode, pulse (drawn over).

`D.hurt(s, arena_point)` damages the soul from script-side hazards (same
invulnerability, ward and safe-rect rules as a bullet).

## Promise objectives: `D.objective(s, props)`

Box-space zones the view draws in mint (or plum hatching for avoid zones):

| kind | completes when |
|---|---|
| touch | the soul touches it |
| confirm | the soul is inside and the player confirms |
| hold | the soul stays inside for `need` ticks (progress shows as a bar) |
| avoid | never completes; entering sets `broken` |

Props: `x y` (centre), `r` (circle) or `w h` (rect half sizes), `active`,
`need`, `label`, `always` (draw even without a promise), `free` (counts even
without a promise; Todd's consent boxes). Touch, confirm and hold only count
while `s.promised` unless `free`. Completing one sets `done`, `doneAt`, bumps
`s.objectiveCount` and sets `s.objectiveChanged` (main.gd plays the "perfect"
sound). Scripts move objectives (`o.x / o.y`), toggle `active`, and read `done`,
`progress`, `broken`. If a script counts something itself, set
`s.objectiveChanged = true` on that tick for the sound.

## QA autopilot hints

`DodgeBot` (scenes/qa_dodge_bot.gd) heads for the first active, unfinished,
non-avoid objective and presses confirm inside confirm objectives. A script can
steer it by setting `s.botGoal` (box-space Vector2, or null) and
`s.botPress = true`. It dodges by simulating ahead, so anything it should avoid
has to go through the engine's collision (bullets, `D.hurt`, audit).

## Design bar (what "Deltarune-level" means here)

- Each attack has one clear idea and two or three layers that interact
  (the box changes shape, the soul mode changes, the pattern is aimed or has a
  rhythm, there is a safe route that moves).
- Telegraph everything. Fair, readable, beatable without getting hit by a
  careful player; the bot's hits (stats harness) should stay low (0-3 per turn),
  while standing still should get hit noticeably more.
- Later phases add a layer to each attack rather than just speeding it up.
- Keep bullets under ~150 alive at once; `D.shot` caps at 320.
- The promise must stay achievable while dodging: give objectives time windows
  of at least ~60 ticks and do not put them under unavoidable fire.
