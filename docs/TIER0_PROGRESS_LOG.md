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
- added a permanent mine-road clear state and daily restored-mine production of
  two Iron Ore and one Coal into Muckford city storage;
- added Grave Pickmen, Rail Wraiths, Web Crawlers, Crystal Husks and Brood Guards
  spanning levels 3-6 with generated animation sets and distinct AI roles;
- replaced the old boss encounter with a level 7, 1080 HP three-phase Cave
  Broodmother that summons Web Crawlers and Brood Guards, emits Web Bursts and
  triggers cavern-collapse waves;
- added dynamic player and lantern darkness, dust, collapse hazards, web gates,
  mine supports, carts, rails and production machinery;
- added boss and production rewards, deeds, Tier 0 events and save persistence;
- validated compilation, the content report, `main.py` import and the complete
  Muckford suite: 57 tests passed in the headless GitHub runner.

Still planned for the mine:

- dedicated mining, undead, web and collapse ambience;
- final painted mine, miner and creature assets after gameplay tuning.

Next production focus — Muckford Warrens:

1. Build the sewer, food tunnels, collapsed cellars and Vortex-waste nest map.
2. Add Hamo, Old Rinna Net and the missing Muckford Ratcatchers.
3. Implement persistent food-cache recovery and nest destruction.
4. Add violet-eyed rat swarms, Rat Riders and Waste Gnawers.
5. Connect cleared warrens to reduced Muckford rat raids.
6. Implement the Rat King as the main local Tier 0 crisis boss.
