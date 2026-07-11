# Varracor crafting station architecture

This document defines where crafting belongs, how stations progress and which
legacy systems still need consolidation.

## Core rule

Crafting is physical and location based. A recipe should have one clear owner.
The player may own and upgrade stations, but a muddy barracks should not replace
an industrial furnace or a professional weapon forge.

## Current production chain

### Muckford Smeltery — material processing

The outdoor Smeltery converts raw mining and scavenging resources into bars.

- Scrap Iron + fuel -> Scrap Metal Bar
- Iron Ore + Coal -> Iron Bar
- Future tiers may add better storage, fuel efficiency, a second queue and rare
  alloy processing.

The Smeltery should never directly produce finished swords, armor or potions.

### Scrap Iron Smithy — weapons and heavy equipment

The town blacksmith owns anvils, forges and heavy metalwork.

- swords, axes, maces, spears and daggers
- shields and future armor pieces
- metal harvesting and mining tools
- future repairs, reforging and equipment quality improvements

Suggested future progression:

1. Scrap Anvil — crude Scrap-tier equipment
2. Iron Forge — Weak/Iron-tier equipment and repairs
3. Master Forge — high-quality gear, reforging and special alloys

The blacksmith can be improved through contracts or town investment, but the
physical building remains in Muckford rather than inside Team Quarters.

### Team Quarters — player-owned support crafting

The Barracks has four independently upgradeable stations. Each station runs one
job at a time, while different stations can work in parallel.

#### Barracks Kitchen

1. Makeshift Hearth
2. Field Kitchen
3. Guild Kitchen

Produces roster meals, healing food and battle-duration buffs. Better tiers
unlock stronger recipes and shorten cooking time.

#### Herbalist Station

1. Makeshift Herb Table
2. Alchemy Bench
3. Guild Distillery

Produces portable potions from farm herbs. Higher tiers unlock antidotes,
strong restoratives, mana elixirs and mixed fortifiers.

#### Quartermaster Workbench

1. Salvage Table
2. Quartermaster Bench
3. Guild Artisan Bench

Produces construction and support components:

- Bandage Roll
- Treated Timber
- Leather Straps
- Reinforced Cloth
- Precision Components

This station is the backbone of Barracks progression. Its master tier unlocks
Precision Components, which are needed by other master stations.

#### Recovery Ward

1. Recovery Cot
2. Field Infirmary
3. Guild Recovery Ward

Provides slow but material-efficient roster healing and injury treatment. This
complements rather than replaces Saint Lumen Field Hospice: the hospital is an
immediate paid service, while the player-owned ward consumes supplies and time.

## Progression dependency chain

The intended order is:

1. Gather Swamp Wood and Scrap Iron.
2. Build the Salvage Table.
3. Craft Bandage Rolls and Treated Timber.
4. Build the Recovery Cot and upgrade basic Kitchen/Herbalist facilities.
5. Use Smeltery bars plus Workbench components to reach Tier 2.
6. Craft Reinforced Cloth and Leather Straps at Workbench Tier 2.
7. Build the Guild Artisan Bench.
8. Craft Precision Components.
9. Use those components for the Guild Distillery and Guild Recovery Ward.

No station may require an item that only that same locked tier can produce.
Focused tests enforce this rule for the Workbench progression graph.

## Timed job rules

- Construction and recipes consume materials when the job begins.
- One job may run per station.
- Different stations may operate at the same time.
- Higher tiers complete recipes faster.
- Jobs use real elapsed time and can complete during battles or while the game
  is closed.
- Completion is processed when Team Quarters is opened or updated.
- If an output fails because a recipe changed during development, all consumed
  materials and gold are refunded and the station is released.
- Station state is stored in `manager.npc_state`, so normal save/load already
  persists it.

## Recommended future stations

### Town Tannery

Heavy hides and foul chemicals fit outside the Barracks. It would convert Troll
Hide, Orc Skin and monster hides into leather sheets. The Quartermaster Bench
would then turn those sheets into straps, padding and light armor components.

### Carpenter or Bowyer

Could be a Muckford artisan or a later Team Quarters annex. It should own bows,
crossbows, staves, shield frames and high-quality wooden handles. This separates
woodcraft from the metal-focused blacksmith.

### Scriptorium / Rune Desk

A later guild or magic-school station for scrolls, spell preparation, runes and
enchanted bindings. It should require reputation with the relevant magic school
and never be available in the starting mud barracks.

### Enchanter's Focus

A late-game station for adding magical properties to already crafted equipment.
The blacksmith creates the physical item; the enchanter modifies it. This keeps
weapon crafting and magical augmentation as separate progression paths.

### Training Yard

Not a crafting station, but it can use the same build/upgrade framework. It may
reduce training cost, unlock team drills and allow injured fighters to perform
light rehabilitation.

## Legacy systems requiring consolidation

`WorkshopMenu` currently reads every entry from `BLUEPRINTS` and can instantly
craft recipes without enforcing a physical station. This bypasses the location
roles above.

The safe migration plan is:

1. Add recipe metadata such as `station`, `station_tier` and `craft_minutes` to
   every blueprint.
2. Make the generic Workshop screen a recipe catalogue and location selector,
   not a universal instant crafter.
3. Route metal recipes to the Muckford blacksmith, processed bars to Smeltery,
   and support crafting to Team Quarters.
4. Preserve old saves and discovered blueprints while changing only where the
   recipe is executed.
5. After all recipes have owners, remove the unrestricted instant-crafting
   fallback.

## Blueprint metadata target

Future recipes should follow a shape similar to:

```python
"Iron Sword": {
    "type": "weapon",
    "station": "blacksmith",
    "station_tier": 2,
    "craft_minutes": 90,
    "cost": 25,
    "mats": {"Iron Bar": 2, "Swamp Wood": 1},
}
```

This metadata lets every UI filter recipes consistently and prevents duplicate,
contradictory crafting rules across menus.
