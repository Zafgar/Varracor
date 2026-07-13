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

## 2026-07-12 — Greywash Ford crossing batch

Completed:

- added a 3900 x 2500 open-risk river map connecting Muckford, Whisper Marsh and
  the western Crown causeway;
- added a 1000-pixel-wide procedural Greywash with fast current, moving foam,
  spray, ripples and weather-scaled flood states;
- added three surveyable shallow ford lanes and a fourth safe crossing created
  by repairing the central bridge;
- added 31 daily River Reed, Clay, Driftwood and Scrap Iron gathering nodes;
- added a dedicated Greywash fish table with Ford Dace, Crownscale Perch,
  Stonebelly Carp, Flood Eel and Greywash Pike;
- kept Greywash fishing persistence separate from the Whisper Marsh quest chain;
- added Ferrykeeper Oswin Pike and the Shanty Yard Saints Saint Mara Wold and
  Hobb Reed with stable names and stage-aware dialogue;
- added the persistent route chain: survey three lanes, defeat six Crown
  deserters, repair the bridge, escort a caravan across five checkpoints, search
  the abandoned watchtower, defeat Garran Vale and report the secured road;
- added caravan ambushes, a generated caravan cart, watchtower evidence, Crown
  seals and city-storage trade rewards;
- added Greywash Riverjaws, Crown Deserters and Ford Brutes with generated
  animation sets, distinct combat AI, status effects and loot;
- added the level 7, 1380 HP three-phase Captain Garran Vale, deserter
  reinforcements, Ford Brute reinforcements, Command Shout and floodgate waves;
- added permanent bridge persistence, daily resource reset, fishing catches,
  caravan progress, boss state and Kingsreach road access;
- fixed the caravan to complete exactly on the fifth checkpoint and preserved
  the correct Greywash-to-Whisper-Marsh return spawn;
- validated compilation, the Tier 0 report, `main.py` import and the complete
  Muckford suite: 75 tests passed in the headless GitHub runner.

Still planned for Greywash Ford:

- dedicated river, caravan, deserter and Garran Vale audio;
- final painted riverbank, bridge, watchtower, NPC and creature assets after
  interactive gameplay and performance tuning.

## 2026-07-12 — Kingsreach Toll checkpoint batch

Completed:

- added a 3800 x 2300 Crown checkpoint map with a paved causeway, wall segments,
  gatehouse, two toll booths, quarantine camp, caravan yard, bandit camp and
  south-west smuggler culvert;
- connected the east exit to Greywash Ford and the west exit to Rattlebridge's
  existing Tier 1 gate;
- added Toll Captain Elric Dorn, Medic Vela Marrow, Salla Quill and Nix Quickreed
  with stable identities and stage-aware dialogue;
- added mandatory quarantine inspection followed by four real resolution paths:
  Garran Vale evidence, a 140 SP toll, quarantine service or a 35 SP smuggler route;
- added Crown reputation consequences: evidence and service improve standing,
  payment gives modest credit and smuggling damages Crown reputation;
- added 28 daily Feverfew, Clean Bandage, Charcoal and Parchment Sheet gathering
  nodes plus Salla Quill's checkpoint trade stock;
- added quarantine service requiring six Feverfew, four Clean Bandages, three
  Charcoal and containment of four Fevered Escapees;
- added generated Causeway Bandits, Crown Toll Enforcers and Fevered Escapees with
  distinct AI, status effects and loot;
- added the optional smuggler-route boss Tollmaster Hadrik Crowl, level 8 with
  1640 HP, three phases, collector reinforcements, paid knives, tax shouts and
  Crown-stamp shockwaves;
- added Stamped Crown Travel Papers and the Crown Promotion Docket as the legal
  handoff from the checkpoint to Bram Carrow;
- synchronized completed Kingsreach saves with the existing league engine so a
  successful Rookie Dust promotion converts the docket into Bram's Recommendation
  and opens the Rattlebridge road;
- persisted the selected route, toll payment, service work, boss state, daily
  resources, pass issuance, quarantine exposure and Crown reputation delta;
- validated compilation, the Tier 0 report, `main.py` import and the complete
  Muckford suite: 87 tests passed in the headless GitHub runner.

Still planned for Kingsreach Toll:

- dedicated checkpoint, quarantine, merchant, enforcer and Crowl audio;
- final painted gatehouse, tents, carts, NPCs and enemy assets after interactive
  performance and route-balance tuning.

## 2026-07-13 — Tier 0 Finale batch

Completed:

- added persistent finale state for the Crown Promotion Docket, league result,
  ceremony, rewards and western departure;
- required Kingsreach clearance, Stamped Crown Travel Papers, Bram's recorded
  docket, one major Muckford crisis and Rookie Dust Top 2 qualification before
  the final promotion match can begin;
- added high-priority Bram dialogue for receiving the Crown docket, explaining
  missing requirements and acknowledging the promotion victory;
- connected the existing 1v1, 3v3 and 5v5 Grand Slam standings and promotion
  rival directly to the finale gate;
- fixed the existing promotion flow so one victory advances exactly once from
  Rookie Dust to Scrapring instead of applying the tier increase twice;
- rebuilt the promotion screen as a code-drawn Shanty Yard farewell with an arena
  arch, Tier 1 banner, animated crowd, torches and confetti;
- added seven branch-aware farewell pages from Bram, Marda, Hamo, Sera Quench's
  representative and the Muckford crowd;
- made the farewell mention the major crisis solved and the route selected at
  Kingsreach Toll;
- granted Bram's Recommendation, Tier 1 Charter, Sera Quench Sponsor Letter,
  250 SP and 10 reputation exactly once;
- required formal Tier 1 promotion, Stamped Crown papers and the completed
  farewell ceremony at both the physical Kingsreach exit and world-map route;
- made runtime-added world routes tolerant of lore-registry reload order instead
  of crashing on a temporarily missing local destination;
- validated compilation, the Tier 0 report, `main.py` import and the complete
  Muckford suite: 96 tests passed in the headless GitHub runner.

Still planned for the finale:

- dedicated crowd, ledger-stamp, farewell and promotion music/audio;
- final painted ceremony portraits and Tier 1 departure art after interactive
  pacing and layout tuning.

Next production focus — Rattlebridge Handoff:

1. Build the bridge approach and professional Crown gate inspection.
2. Present the Tier 1 Charter, Bram's Recommendation and sponsor letter in play.
3. Add Sera Quench's first full meeting and Tier 1 registration dialogue.
4. Add initial lodging, professional contract and sponsor onboarding quests.
5. Connect the existing Rattlebridge districts into one persistent arrival arc.
6. Begin the Scrapring Circuit without removing access back to Muckford.
