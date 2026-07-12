# Tier 0 World Expansion

This document defines how the Muckford region is expanded before the player
enters Rattlebridge and the Tier 1 Scrapring Circuit.

The machine-readable source of truth is:

- `lore/tier0_world_plan.py`
- player save progress: `systems/tier0_world_tracker.py`
- report command: `python tools/tier0_content_report.py`

## Core access rule

Development order is not player lock order.

Most Tier 0 wilderness areas are open after the player discovers a physical
route. Entering below the recommended level remains allowed. The UI shows a
clear danger warning instead of blocking travel.

Only real obstacles may block entry:

- Marda's key blocks the Old Muckford Mine.
- undiscovered or destroyed roads block physical travel.
- Kingsreach Toll may require papers, payment, service or another route.
- Rattlebridge's professional circuit requires formal Tier 1 promotion.

## Canonical development order

1. **Muckford Low Fields** — first exterior work and gathering zone.
2. **Whisper Marsh** — NPCs, survey quests, fishing and pool boss.
3. **Drowned Chapel** — Rhea's flooded holy ruin and Water-risen crisis.
4. **Old Muckford Mine** — galleries, Webbed Depths and mine recovery.
5. **Muckford Warrens** — violet-eyed rat army and Rat King crisis.
6. **Greywash Ford** — open-risk river crossing and caravan route.
7. **Kingsreach Toll** — Crown politics and travel-paper gate.
8. **Tier 0 Finale** — Rookie Dust victory, local service and Bram's recommendation.
9. **Rattlebridge handoff** — professional Scrapring registration.

The player may explore available roads in a different order. The sequence above
is only the order in which complete production-quality content is built.

## Required content pass for every area

Every area is measured across twelve domains:

1. **Area** — playable boundaries, routes, collision, camera and return points.
2. **NPCs** — stable IDs, roles, schedules, placement and persistence.
3. **Quests** — objectives, rewards, retry rules and world changes.
4. **Dialogue** — introductions, active states and completed states.
5. **Resources** — nodes, tools, yields, economy and crafting use.
6. **Creatures** — level band, spawn ecology, AI and loot.
7. **Boss** — encounter mechanics, reward and persistent consequence.
8. **Graphics** — code placeholders first, replaceable final assets later.
9. **VFX** — terrain feedback, attacks, hazards and telegraphs.
10. **Audio** — ambience, creature cues, interaction sounds and boss cues.
11. **Persistence** — visits, projects, quests, bosses and world changes survive saves.
12. **Tests** — compile, main import, deterministic systems and headless encounters.

## Work-batch procedure

Every implementation batch follows the same order:

1. Run `python tools/tier0_content_report.py`.
2. Read the current area's entry in `lore/tier0_world_plan.py`.
3. Check its routes and lore in `lore/world_map_data.py`.
4. Implement the next incomplete domain without silently changing canon.
5. Connect content to GameManager, saves and world progression.
6. Add or update tests before changing the domain state.
7. Update `lore/tier0_world_plan.py`.
8. Add a dated entry to `docs/TIER0_PROGRESS_LOG.md`.
9. Run the focused CI workflow and inspect its output.

No area is declared complete based only on an import test. Runtime-facing systems
need focused headless tests, and large visual areas still need client playtesting
after automated checks.

## Current honest status

### Playable production foundations

- Muckford city, farming, crafting, registration and Shanty Yard access.
- Expanded Forest Road combat tutorial.
- Low Fields gathering, restoration and local travel.
- Whisper Marsh survey chain, fishing, monster ecology and Whisper Pool Maw.
- Drowned Chapel rescue chain, taint exposure and Bell-Drowned Pilgrim.
- Old Muckford Mine restoration, daily ore production and Cave Broodmother.
- Muckford Warrens crisis chain, two physical routes, four rat-army species,
  three-phase Rat King and permanent shutdown of city rat raids.
- Rattlebridge has a substantial city foundation, but its complete Tier 0
  promotion handoff is not finished.

The completed wilderness areas still retain planned audio and final painted art
passes. Their gameplay, persistence, generated placeholders and headless tests
are live.

### Current focus

`greywash_ford`

The next production batch creates the broad Greywash crossing between Muckford's
mud roads and the Crown causeway. It will include a code-rendered fast river,
surveyable ford lanes, a repairable bridge, an abandoned watchtower,
Ferrykeeper Oswin Pike, Shanty Yard Saints, Crown deserters, caravan escort,
river resources, fishing, flood-state hazards and the crisis that opens the road
toward Kingsreach Toll.

## Arena progression relationship

World work complements the Rookie Dust Circuit; it does not replace it.

The normal player should need several seasons to clear a tier. Tier 0 progress
combines:

- 1v1, 3v3 and 5v5 league results;
- team development and injuries;
- local reputation;
- monster and boss hunts;
- resource and settlement projects;
- one major Muckford crisis;
- Bram's formal recommendation.

Easy low-level gathering must not become an unlimited shortcut for money or XP.
Rewards scale with risk, travel depth, contracts and tier progression.
