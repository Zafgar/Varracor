# Varrakor World Map and Level 1–30 Progression

> Canonical technical and design reference for continent travel, regional
> expansion and arena progression. Machine-readable data lives in
> `lore/world_map_data.py`; runtime state and gating live in
> `systems/world_progression.py`.

## Core world rule

The Abyssal Vortex occupies the centre of Varrakor. Safe trade and military
travel therefore forms a broken ring around the Sundered Heartlands rather than
crossing the continent in straight lines.

World travel is node-based:

1. A destination must be discovered.
2. It must have a direct route from the party's current location.
3. Arena tier, reputation and story requirements are checked.
4. Travel consumes world-clock hours.
5. Surveying a reached location reveals adjacent routes and future goals.

The map may show a dangerous future landmark before the player can travel
there. This is intentional: the next goal should be visible without allowing
the progression chain to be skipped.

Character level is primarily a danger warning, not a hard wall. A skilled or
reckless player may enter a higher-level route when all political and story
gates are satisfied. Arena tier, reputation, keys and Vortex-ring order remain
hard gates.

---

## Arena and level progression

The existing `LeagueEngine` uses gameplay tiers 1–6. World lore uses arena tiers
0–5. Runtime code converts them as follows:

| LeagueEngine tier | Lore arena tier | Intended levels | Circuit | Main purpose |
|---:|---:|---:|---|---|
| 1 | 0 | 1–5 | Rookie Dust Circuit | Registration, survival basics and first regional rumors |
| 2 | 1 | 6–10 | Scrapring Circuit | Sponsors, professional gear and trade-route security |
| 3 | 2 | 11–15 | Iron Circle Circuit | Contracts, specialist crafting and regional logistics |
| 4 | 3 | 16–20 | Steel Arena Circuit | Elite tactics, magic integration and faction responsibility |
| 5 | 4 | 21–25 | Silver League Circuit | National champions, war readiness and legendary materials |
| 6 | 5 | 26–30 | Golden League | Highstone authority and deep Vortex expeditions |

Arena promotion reveals the next circuit's cities. It does not automatically
teleport the team to them; the route must still be travelled and surveyed.

### Tier 0 — Levels 1–5

- **Shanty Yard, Muckford:** mud, scrap hazards and team registration.
- **Oasis Pit, Saffron Oasis:** heat, water and stamina discipline.
- **Jungle Drumring, Vinehollow:** poison awareness and slippery terrain.

Tier 0 teaches the same fundamentals in three climates. Muckford is the default
start, while the other two become early long-distance goals after the player
has earned enough reputation and found the caravan routes.

### Tier 1 — Levels 6–10

- **The Scrapring, Rattlebridge:** narrow bridge lanes and moving scrap gates.
- **Bolt Cage, Rivet Row:** steam vents and compressed close combat.
- **Palisade Ring, Timbercross:** falling timber and politically sensitive
  Wyrdwood boundaries.

Tier 1 is when teams become professional organizations. Sponsors, reliable Iron
equipment, regional reputation and route-control contracts become important.

### Tier 2 — Levels 11–15

- **The Iron Circle, Giltgate:** betting, objectives and calculated risk.
- **Contract Court, Ledgerford:** changing rules and penalty zones.
- **Tidepit, Coinharbor:** rising water and Water-risen intrusions.
- **Kestrel Caravan Ring:** moving cargo and changing lanes.

Tier 2 expands the economy. Winning is no longer enough; the team must navigate
contracts, law, markets and specialist materials.

### Tier 3 — Levels 16–20

- **The Steel Arena, Spirewatch:** precision and controlled magic.
- **Skychain Arena, Windstep:** wind and knockback control.
- **Crystal Crucible, Gleamhold:** spell reflection and resonance.
- **Moonring, Moonwatch:** living roots, moonlight and Taint cleansing.

Tier 3 is the first truly elite circuit. Schools of magic and faction duties
become part of ordinary arena preparation.

### Tier 4 — Levels 21–25

- **Silver League Grand Ring, Kharak-Tor:** formation and endurance.
- **Lion Court, Crownhold:** royal decrees and political spectacle.
- **Ossuary Circle, Bonewind Necropolis:** soul winds and controlled undead.

Tier 4 teams are national assets. Their arena seasons coexist with military,
holy, necromantic and border-security duties.

### Tier 5 — Levels 26–30

- **The Golden League, Highstone Sanctum:** Charter trials, Vortex simulations
  and Arkon's final judgment.

The Golden League is one mythic circuit rather than a normal collection of
regional venues. Victory authorizes the team to enter the Vortex as an official
expedition force.

---

## Regional level structure

### Sundered Heartlands

| Location | Levels | Role |
|---|---:|---|
| Muckford / Shanty Yard | 1–5 | Starting hub and arena registration |
| Whisper Marsh | 1–5 | First gathering and monster-hunt wilderness |
| Old Muckford Mine | 3–7 | Iron, Coal, undead and Cave Broodmother |
| Sundered Road Ruins | 6–10 | First containment-zone staging area |
| Outer Shatterbelt | 26–27 | Stable outer Vortex ring |
| Spiral Scar | 28–29 | Shifting time and distance |
| The Throat | 29–30 | Major Abyssal Echo descent |
| The Eye | 30 | Endgame core and Heartcore Adamant |

The Heartlands deliberately contains both the first and last content in the
game. Early players live on its safer edge; endgame teams return through the
same ruined region toward the centre.

### Crownlands

The western loop progresses from Rattlebridge and Rivet Row through Giltgate,
Ledgerford and Coinharbor, then toward Crownhold, Sunspire Basilica and the
Mirror Court. Typical progression runs from levels 6 to 25.

The Crown controls roads, paperwork, industrial capacity and access. Its hard
gates should often be reputation or legal authorization rather than monster
strength alone.

### Sunscar Expanse

The southern loop begins with Saffron Oasis, continues through Kestrel-Way,
Hornfall and Stonegrit, and culminates in Kharak-Tor. Bonewind Necropolis forms
a dangerous north-eastern branch near the Heartlands. The Howling Barrens are a
late-game wilderness beyond reliable caravan law.

Water, travel supplies and defensive caravan contracts define this region.

### Wyrdwood

Vinehollow and Timbercross form the accessible edge. Elderroot Grove,
Moonwatch and the Deep Wyrdwood require increasing Warden trust. Progression is
based on what the player protects as much as what the player defeats.

Illegal harvesting and uncontrolled Taint should eventually modify Wyrdwood
reputation and close otherwise safe routes.

### Aegis Peaks and Sanctum Marches

The neutral north begins around levels 14–18 in the Sanctum Marches and
Prismhall. Ironwind Pass, Windstep, Gleamhold and Spirewatch form the Tier 3
mountain chain. Highstone is reserved for levels 26–30 and Golden League status.

This region connects advanced magic, neutral law, artifact registration and the
final Vortex campaign.

---

## Current implementation states

Every world node has one of three implementation states:

### `playable`

A dedicated local gameplay state already exists.

Current examples:

- Muckford city
- Shanty Yard league entry
- Whisper Marsh / forest excursion
- Old Muckford Mine road and cave

### `survey`

The route is usable now and leads to a procedural regional staging screen. The
player can arrive, read local lore, inspect services and threats, survey nearby
routes and enter the location's arena when the registered tier matches.

This state is the expansion foundation for Rattlebridge, Saffron Oasis,
Vinehollow, Timbercross and the other major cities. A bespoke top-down local map
can later replace `regional_staging` for one location without changing routes,
unlock requirements or saved exploration.

### `future`

The node, route, level range, materials and dependencies exist in the world
graph, but travel is disabled until its playable content is implemented.

Deep Wyrdwood, Howling Barrens and the deepest Vortex rings currently use this
state.

---

## Saved world state

World exploration is stored in:

```text
manager.npc_state["world_progression"]
```

The structure contains:

- `current_location`
- `discovered_locations`
- `visited_locations`
- `surveyed_locations`
- `travel_history`
- `unlock_notices`
- a small internal version number

Because `npc_state` was already saved by the existing save manager, old saves
receive world progression without a save-file version break. Missing state is
initialized at Muckford and existing keys, materials and league progress remain
untouched.

---

## Expansion workflow for a new local area

When implementing a full city or wilderness map:

1. Keep its canonical entry in `lore/world_map_data.py`.
2. Create the local menu/arena files.
3. Change that location's `target_state` from `regional_staging` to the new menu
   state.
4. Change `content_state` from `survey` to `playable`.
5. Register the menu in `main.py`.
6. Preserve the same location ID so old saves and travel history remain valid.
7. Build local quests from the location's services, threats and materials.
8. Implement the signature arena hazards defined in
   `arenas/world_arena_profiles.py` rather than inventing a conflicting arena
   identity later.

Recommended order for full local-map development:

1. Rattlebridge (first Tier 1 hub)
2. Timbercross and Saffron Oasis (regional alternatives)
3. Rivet Row
4. Giltgate / Ledgerford / Coinharbor / Kestrel-Way
5. Sanctum Marches and the Tier 3 mountain chain
6. Faction capitals and magic headquarters
7. Highstone
8. Vortex rings
