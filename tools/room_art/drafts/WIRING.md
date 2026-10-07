# Room wiring notes (visuals lane, 2026-10-07)

Drafts in this folder use the rooms.json shape plus helper keys (`arrivals`, `npc_spots`, `suggested`, `note`) that can be stripped. Music cues are guesses.

| from | exit | to | spawn in the target |
|---|---|---|---|
| D01 | hallway door (58,134) | D02 | [150,196] |
| D02 | stairs (1210,176) | D03 | [56,196] |
| D03 | stairs (56,176) | D02 | [1210,196] |
| D03 | front doors (262,176) | C01 | [1770,234] |
| C01 | Farrand door (1770,212) | D03 | [262,196] |
| C01 | Book Store door (860,212) | C02 | [400,410] |
| C01 | Career Center door (1340,212) | C03 | [400,410] |
| C02 | exit (400,446) | C01 | [860,234] |
| C03 | exit (400,446) | C01 | [1340,234] |
| C01 | west edge, Broadway (34,392) | H01 | [880,340] |
| H01 | east edge (930,340) | C01 | [74,392] |
| H01 | party house door (485,240) | H02 | [400,420] |
| H02 | front door (400,462) | H01 | [485,256] |
| C01 | new "PEARL ST" threshold, west edge below the Hill exit, about (34,470) | P01 | [62,204] |
| P01 | stairs_down (62,176) | C01 | [80,470] |
| P01 | break_room door (880,176) | P02 | [64,184] |
| P02 | office_door (64,152) | P01 | [880,204] |

Other C01 exits already in its draft: UMC main doors to U03 [360,420], north lanes to M01 [120,460] and O01 [120,445], Norlin gate to N01 [120,300], east edge to F01 [120,400], south walk to E01 [105,440].

Mini-boss spots: tanner at (470,446) in H01 or (400,380) in H02; kyle at (700,262) in P01. Save spots: D03 lobby lamp (456,332), C03 waiting chairs, P02 beanbag, C01 fountain bench.
Sprite ids for the NPC/boss objects match the art ids in assets/art (kyle, tanner, sunbeam, ...). Startup name "DISRUPTR" and its slide jokes are in p01_lib.slide(). House letters on the Hill are invented; Tanner's cape reads XI OMEGA XI, so the party house sign (XOL) can be changed in h01_lib.py to match.
