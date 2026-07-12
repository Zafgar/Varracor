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
- migrated existing team registration, Forest Road, Whisper Marsh visits,
  Survey Post stages, fishing readiness and mine-key facts into the tracker;
- exposed Tier 0 advice, phase, objectives and development queue through
  `GameManager`;
- added a command-line development report;
- set `low_fields` as the next implementation focus.

Previously completed foundations now represented honestly in the registry:

- Muckford city and opening progression;
- Forest Road combat tutorial;
- Whisper Marsh procedural water and development;
- level 1–5 marsh monster ecology and code-rendered graphics;
- Old Muckford Mine partial foundation;
- Rattlebridge partial city foundation.

## 2026-07-12 — Muckford Low Fields playable batch

Completed:

- added a 3200 x 2200 freely traversable Low Fields map;
- added a Muckford west gate, return spawn and a south-east foot route into
  Whisper Marsh;
- registered the Low Fields world-map node and both local travel routes;
- kept entry open at every level while displaying the recommended Lv 1-3 risk;
- added procedural crop fields, roads, fences, irrigation water, carts, bridges,
  work markers, burrow mounds, drifting seeds, flies and low mist;
- added Farmer Gus, Saint Lumen runner Lysa Reedrunner and three stable field
  workers with local dialogue;
- added the restoration chain: repair irrigation, defend the grain cart, seal
  three Mud Mite burrows and build the lower footbridge;
- added daily renewable Carrot, Potato, Onion, River Reed, Clay and Softwood
  nodes that cannot be harvested repeatedly on the same world day;
- added Mud Mites, Reed Skitters, Marsh Rats and a quest-specific grain-cart
  attack using the existing Tier 0 AI ecology;
- added persistent projects, burrows, quest counters, one-time supplies and
  completion rewards inside the existing save-compatible `npc_state`;
- added focused Low Fields tests and expanded the Muckford CI workflow;
- validated the complete Muckford suite: 31 tests passed and `main.py` imported
  successfully in the headless runner.

Still planned for Low Fields:

- The Burrow-Mother optional level 3 field boss;
- dedicated field ambience and creature audio beyond the existing reusable
  sound cues;
- final painted replacement assets after gameplay tuning.

Next production focus:

1. Complete Whisper Marsh NPC placement and dialogue.
2. Turn its partial survey events into explicit quest states.
3. Add the first playable fishing minigame using the existing fishing anchors.
4. Define and implement the Whisper Pool boss before opening Drowned Chapel.
