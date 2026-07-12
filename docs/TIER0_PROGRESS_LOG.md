# Tier 0 Development Progress Log

This file records completed implementation batches. The detailed status remains
in `lore/tier0_world_plan.py`.

## 2026-07-12 — World-development foundation

Completed:

- created the canonical Tier 0 area and content-domain registry;
- recorded the ordered route from Muckford through Rattlebridge handoff;
- established the open-risk access rule and explicit physical/formal gates;
- recorded NPC, quest, resource, creature, boss, graphics, VFX, audio,
  persistence and test requirements for every planned area;
- added a persistent player-facing Tier 0 tracker inside `npc_state`;
- exposed Tier 0 advice, phase, objectives and development queue through
  `GameManager`;
- added a command-line development report.

## 2026-07-12 — Muckford Low Fields playable batch

Completed:

- added a 3200 x 2200 freely traversable Low Fields map;
- added Muckford and Whisper Marsh travel routes;
- added generated fields, irrigation, fences, carts, bridges and field VFX;
- added Farmer Gus, Lysa Reedrunner and three stable field workers;
- added irrigation, grain-cart, burrow and footbridge restoration objectives;
- added daily Carrot, Potato, Onion, River Reed, Clay and Softwood nodes;
- added Mud Mites, Reed Skitters and Marsh Rats;
- added persistent projects and focused tests.

Still planned:

- optional Burrow-Mother field boss;
- dedicated field ambience and final painted replacement assets.

## 2026-07-12 — Whisper Marsh story, fishing and boss batch

Completed:

- added Surveyor Kessa Fenmark, Brik Sealrunner and Ferryman Noll;
- replaced the random ferryman event with a persistent named quest;
- linked the Survey Post to explicit story progression;
- added three Whisper Pool survey markers;
- added Greywash Channel and Whisper Pool fish tables;
- added cast, bite, hook and line-tension fishing gameplay;
- added persistent catches and first-catch progression;
- added the code-rendered two-phase Whisper Pool Maw boss;
- validated the expanded suite with 39 passing tests.

Still planned:

- dedicated ambience, fishing sounds, voiced lines and final painted assets.

## 2026-07-12 — Drowned Chapel playable batch

Completed:

- added a 3300 x 2200 flooded chapel, nave, graveyard, bell tower and quarantine
  camp connected physically to Whisper Marsh;
- kept the route open while displaying the Lv 3-5 danger warning;
- added Sister-Medic Rhea Ashford, Brother Iven and three rescueable pilgrims;
- added medicine-chest recovery, pilgrim rescue, three tainted-water samples and
  three Saint Lumen ward braziers;
- added persistent taint exposure and a safe quarantine brazier;
- added daily Medicinal Herb, Grave-Lotus, Sanctified Wax and River Clay nodes;
- added Water-risen Pilgrims, Flooded Acolytes and Bell Wraiths with generated
  graphics and existing combat-AI integration;
- added the two-phase Bell-Drowned Pilgrim, bell-wave attack and persistent
  chapel recovery rewards;
- validated the expanded suite with 47 passing tests.

Still planned:

- dedicated holy, bell and quarantine audio;
- final painted chapel, NPC and monster assets.

## 2026-07-12 — Old Muckford Mine restoration batch

Completed:

- retained Marda's debt-and-key gate and the existing mine road;
- replaced the small cave interior at runtime with a 3800 x 2400 multi-chamber
  mine containing entrance works, abandoned galleries, collapsed rails and the
  Webbed Depths;
- added Foreman Torra Flintvein and missing miners Durn Coalhand, Pell Rook and
  Sava Brasspin with stable lore names and stage-aware dialogue;
- added the restoration chain: light three Coal lanterns, rescue three miners,
  clear three collapses with a pickaxe, destroy four egg sacs, defeat the Cave
  Broodmother and restart the entrance winch;
- added daily Iron Ore, Coal, Stone, Chipped Ruby and Silver Ore depletion and
  respawn tracking;
- added permanent road clearance and daily Iron Ore and Coal production;
- added Grave Pickmen, Rail Wraiths, Web Crawlers, Crystal Husks and Brood Guards;
- added the level 7 three-phase Cave Broodmother;
- validated the complete Muckford suite with 57 passing tests.

Still planned:

- dedicated mining, undead, web and collapse ambience;
- final painted mine, miner and creature assets.

## 2026-07-12 — Muckford Warrens city-crisis batch

Completed:

- added a 3600 x 2400 sewer, food-tunnel, collapsed-cellar and Royal Cistern map;
- added two physical entrances: Hamo's cellar hatch in Muckford and the Low
  Fields drain culvert;
- kept both routes open at every level while displaying the Lv 4-6 danger band;
- added Hamo, Old Rinna Net and the missing Ratcatchers Tessa Trapwire, Brin
  Sootsnare and Dorrik Two-Nails with stage-aware dialogue and persistence;
- added the full crisis chain: trace four violet trails, recover four food
  caches, destroy four Vortex-waste nests, rescue three Ratcatchers, defeat the
  Rat King and report the result;
- added persistent recovered grain and scrap deliveries into Muckford storage;
- added three moving sewer channels, four safe bridges, Vortex-waste exposure,
  poison pressure, fumes, darkness and route-specific return spawns;
- added Sewer Rat Swarms, Violet-Eyed Rats, Rat Riders and Waste Gnawers with
  generated animation sets, distinct AI roles, status effects and loot;
- added a level 6, 1120 HP three-phase Rat King that summons violet regiments,
  Rat Riders and Waste Gnawers, releases Royal Screech and erupts the cistern;
- connected the boss to the existing `rat_king` Tier 0 milestone, legacy hunt
  quest and deed systems;
- permanently disabled Muckford's existing random rat raids after the Rat King
  dies, including removal of any raid already active when the save is loaded;
- added the Gnawed Crown, Vortex Residue, reputation, Silver Piece and city-food
  rewards;
- integrated the area through the current regional-state factory without adding
  a duplicate main-loop state;
- validated compilation, the Tier 0 report, `main.py` import and the complete
  Muckford suite: 66 tests passed in the headless GitHub runner.

Still planned for the Warrens:

- dedicated rat-army, sewer-current and Rat King audio;
- final painted cellar, sewer, NPC and creature assets after gameplay tuning.

Next production focus — Greywash Ford:

1. Build a broad code-rendered river, ford lanes, broken bridge and watchtower.
2. Connect the route physically to Muckford and Whisper Marsh.
3. Add Ferrykeeper Oswin Pike, Shanty Yard Saints and Crown deserters.
4. Implement safe-lane surveying, bridge repair and caravan escort objectives.
5. Add ford fishing, river resources, ambushers and flood-state hazards.
6. Implement the ford crisis boss and open the road toward Kingsreach Toll.
