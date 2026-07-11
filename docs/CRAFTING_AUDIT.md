# Crafting system audit

## Scope reviewed

- Team Quarters / Barracks
- Muckford Smeltery
- Scrap Iron Smithy / Blacksmith interior
- generic Workshop menu
- blueprint data and `GameManager.craft_item`
- save/load coverage

## Current findings

### Team Quarters stations

Status: new coherent implementation.

- four independently tiered stations
- real elapsed construction and recipe jobs
- one queue per station, parallel work across stations
- recipe tier gates and speed improvements
- transactional input handling with refunds on output failure
- JSON-safe persistence through `manager.npc_state`
- focused progression and dependency tests

The physical station artwork is still UI-only. A later Barracks interior can
place visual station props whose appearance changes with station tier.

### Smeltery

Status: useful gameplay, but technically isolated from the new job model.

Current limitations:

- progress is measured in update frames, not elapsed world/real time
- it only advances while the Muckford city menu is actively updating
- current job, stored fuel/resources and ready outputs are properties of the map
  object and are not explicitly included in save data
- recipes and durations are hardcoded in the prop class
- no station tiers, queue expansion or fuel-efficiency upgrades

Recommended change: migrate Smeltery state to a persistent station node and use
the same elapsed-time job format as Barracks, while keeping its physical world
interaction and smoke/spark visuals.

### Blacksmith

Status: functional instant forge, but recipe ownership and tiers are incomplete.

Current limitations:

- categories are hardcoded in the menu
- Scrap recipes are shown directly
- the Weak category is hardcoded as locked rather than driven by progression
- Iron blueprints exist in data but are not represented consistently in the
  blacksmith category list
- forging calls the generic instant `GameManager.craft_item`
- forge tier, craft duration, quality and smith workload are not modeled

Recommended change: add blueprint station metadata and derive all blacksmith
categories from data. Introduce Scrap Anvil, Iron Forge and Master Forge tiers,
then convert forging to persistent timed jobs.

### Generic Workshop menu

Status: legacy bypass.

The menu reads the global `BLUEPRINTS` table and can instantly craft all matching
recipes. This bypasses the intended Smeltery -> Blacksmith -> Barracks chain.

It should become a recipe catalogue and destination selector. It can show where
a discovered recipe is made, the required station tier and whether that station
is currently busy. It should not produce items itself after migration.

### Blueprint and manager layer

Status: insufficient metadata for location-based crafting.

Blueprint entries currently contain type, description, gold cost and materials.
They need:

```python
"station": "blacksmith",
"station_tier": 2,
"craft_minutes": 90,
"output_amount": 1,
```

`GameManager.craft_item` should eventually validate a station context or become
a low-level output helper called only after a station job completes.

## Recommended implementation order

1. Keep the new Barracks stations as the reference job-state format.
2. Add `station`, `station_tier` and `craft_minutes` metadata to blueprints.
3. Add tests ensuring every craftable blueprint has exactly one station owner.
4. Persist and time-convert the Muckford Smeltery without changing its location.
5. Make Blacksmith categories data-driven and add its three forge tiers.
6. Convert Blacksmith crafting from instant output to timed jobs.
7. Turn WorkshopMenu into a catalogue/router and remove universal instant craft.
8. Add external Tannery and Carpenter/Bowyer locations.
9. Add late-game Scriptorium and Enchanter stations behind reputation gates.
10. Add Barracks interior props and visual tier changes after functionality is
    stable.

## Balance principles

- Processing stations should create intermediate materials efficiently.
- Specialist stations should own finished products.
- Higher tiers primarily unlock recipes, speed and queue capacity; they should
  not multiply output so strongly that gathering becomes irrelevant.
- Strong food buffs should last a limited number of battles.
- Potions remain portable single-use equipment.
- Recovery Ward treatment is slower and material-based; the hospital remains
  the immediate gold-based option.
- Station progress must survive saving, changing maps, battles and closing the
  game.
