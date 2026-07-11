# Varrakor — Crafting and Gathering Materials

> Canonical human-readable material lore. Machine-readable data lives in
> `lore/materials.py`. Gameplay code, shops, quests and stations should use the
> exact English names shown here.

## System rules

World materials use five primary rarities:

| Rarity | Typical level | Meaning |
|---|---:|---|
| Common | 1–10 | Frontier resources, starter crafting and everyday trade |
| Uncommon | 6–20 | Specialist processing, regional access or guild supplies |
| Rare | 16–25 | Dangerous regions, magical resonance or strong monsters |
| Very Rare | 21–30 | Faction-controlled deposits, Vortex zones and legendary work |
| Mythic | 30+ | Artifact cores, Highstone authority and the Vortex itself |

**Echo Shard** keeps the historical quality label *Epic*, but is stored under
Rare in the five-rarity game system. **Focus Powder** can vary between Uncommon
and Rare depending on crystal quality.

Crafted intermediates such as Scrap Metal Bar, Bandage Roll, Treated Timber,
Leather Straps, Reinforced Cloth and Precision Components are not gathered
world materials. They are produced by stations from the materials below.

---

## 1. Metals, ores and smithing

| Material | Rarity | Level | Primary source | Main station | Lore and future use |
|---|---|---:|---|---|---|
| **Scrap Iron** | Common | 1–5 | Scrap piles, wrecks, battlefields | Smeltery / Blacksmith | Muckford reforges old wreckage into Crude weapons and construction parts. |
| **Coal** | Common | 1+ | Mines and charcoal burners | Smeltery | Basic forge fuel needed for Iron and hotter metal processes. |
| **Iron Ore** | Common | 4–10 | Surface mines | Smeltery | Reliable ore for the first professional equipment tier. |
| **Iron Ingot** | Common | 6–10 | Smelted Iron Ore + Coal | Blacksmith | Used in Iron weapons, armor, tools and station upgrades. |
| **Blacksteel Ore** | Uncommon | 10–15 | Deep Crown and Kharak mines | Advanced Smeltery | Dark ore that demands controlled heat and Tempering Flux. |
| **Tempering Flux** | Uncommon | 11+ | Salt flats, alchemists, forge guilds | Smeltery / Blacksmith | Prevents rare metals from cracking during cooling and reforging. |
| **Blacksteel Ingot** | Uncommon | 11–15 | Refined Blacksteel Ore | Blacksmith | Material for Steel-tier weapons, heavy armor and advanced tools. |
| **Stormsilver Ore** | Rare | 16–20 | Storm-struck Aegis veins | Master Smeltery | Hums before lightning and carries magical resonance. |
| **Stormsilver Ingot** | Rare | 16–20 | Grounded Stormsilver refining | Blacksmith / Enchanter | Elite armor, rune weapons and spellcasting foci. |
| **Sun-Gold Ore** | Very Rare | 21–25 | Crown-controlled holy mines | Sanctified Smeltery | The Crown treats every vein as royal and religious property. |
| **Sun-Gold Ingot** | Very Rare | 21–25 | Consecrated Sun-Gold refining | Master Blacksmith | Holy weapons, legendary armor and sanctified regalia. |
| **Void-Iron** | Very Rare | 26–30 | Outer Shatterbelt fractures | Void Forge | Cold metal that rejects part of the Abyss and resists corruption. |
| **Heartcore Adamant** | Mythic | 30+ | The Eye of the Vortex | Artifact Forge | The world's hardest known material and the frame of Mythic artifacts. |

### Metal progression

`Scrap Iron → Scrap components → Iron Ore → Iron Ingot → Blacksteel → Stormsilver → Sun-Gold / Void-Iron → Heartcore Adamant`

Muckford should handle Scrap and Iron. Blacksteel requires a developed regional
forge. Stormsilver and higher materials belong to specialist locations.

---

## 2. Woods, fibers and bindings

| Material | Rarity | Level | Primary source | Main station | Lore and future use |
|---|---|---:|---|---|---|
| **Plant Fiber** | Common | 1+ | Farms, reeds and grasses | Quartermaster Workbench | Bowstrings, cloth, bandages and bindings. Crop harvesting can yield spare fiber. |
| **Rough Timber** | Common | 1–5 | Muckford forest edge and salvage | Carpenter / Workbench | Crude handles, shields and station construction. Formerly called Swamp Wood. |
| **Resin** | Common | 1–10 | Tree wounds and resin traps | Carpenter / Alchemy | Laminates bows, waterproofs wood and stabilizes potions. |
| **Oakwood** | Common | 6–10 | Managed forests | Carpenter / Bowyer | Professional bows, shield frames and Iron-tier hafts. |
| **Refined Binding Kit** | Uncommon | 6+ | Crafted guild supply | Quartermaster Workbench | Standard cord, fasteners and resin needed for Uncommon equipment. |
| **Ironbark** | Uncommon | 11–15 | Protected Wyrdwood groves | Wyrdwood Carpenter | Naturally armored wood for living shields and druid equipment. |
| **Moonwillow** | Rare | 16–20 | Moonlit Wyrdwood stands | Master Bowyer / Druid | Magical bows, lunar foci and druid staves. |
| **Elderroot Fiber** | Very Rare | 21–25 | Sacred Elderroot roots | Verdant Covenant Artisan | Partly living fiber used in legendary bindings and living armor. |

The Wardens strictly control Ironbark, Moonwillow and Elderroot harvesting.
Illegal logging should damage Wyrdwood reputation and may trigger patrols.

---

## 3. Hides, bones and monster parts

| Material | Rarity | Level | Primary source | Main station | Lore and future use |
|---|---|---:|---|---|---|
| **Tanned Hide** | Common | 1–10 | Processed common beast hides | Tannery | Light armor, padding, pouches and simple straps. |
| **Leather** | Common | 6–15 | Selected and refined Tanned Hide | Tannery / Leatherworker | Quivers, gloves, grips and Iron-tier armor components. |
| **Direhide** | Uncommon | 11–20 | Dangerous predators | Advanced Tannery | Heavy leather equipment and monster-resistant protection. |
| **Trollbone Plating** | Rare | 16–20 | Mature troll bone | Bonewright / Blacksmith | Regenerative armor and shield reinforcement. |
| **Drake Scale** | Very Rare | 21–25 | Drakes and lesser dragons | Master Tannery / Blacksmith | Fire-resistant armor and legendary heat shielding. |
| **Abyssal Chitin** | Very Rare | 26–30 | Armored Vortex creatures | Void Forge | Taint-resistant expedition armor; fragments may continue moving. |
| **Echo Heart** | Mythic | 30+ | Major Abyssal Echo bosses | Artifact Forge | Repeating boss will used as the core of Mythic artifacts. |

Raw monster drops such as Troll Hide, Orc Skin or Spider Silk can still exist.
They become standardized materials only after processing at the correct station.

---

## 4. Herbs, alchemy and potions

| Material | Rarity | Level | Primary source | Main station | Lore and future use |
|---|---|---:|---|---|---|
| **Bitterleaf** | Common | 1+ | Muckford fields and marsh edges | Herbalist Station | Basic healing potions, recovery meals and field dressings. |
| **Sunblossom** | Uncommon | 6–15 | Sunny clearings and temple gardens | Alchemy / Holy Apothecary | Stamina brews, holy remedies and strong restoratives. |
| **Nightcap Fungus** | Uncommon | 6–15 | Wet caves and frog territory | Alchemy Bench | Antidotes, sleep draughts and toxin studies. |
| **Moondew Petals** | Rare | 16–20 | Lunar flowers before dawn | Advanced Alchemy | Mana recovery and lunar inks; must be sealed before sunrise. |
| **Grave-Lotus** | Rare | 16–25 | Battlefields and ossuary pools | Necromantic Apothecary | Necromantic mixtures and dangerous corruption cleansing. |
| **Vortex Residue** | Very Rare | 26–30 | Vortex creatures and fractures | Taint Laboratory | Highest-tier potion catalyst with severe corruption risk. |

Muckford's older names are migrated automatically:

- `Medicinal Herb` and `Bogwort` → **Bitterleaf**
- `Sunleaf` → **Sunblossom**
- `Moonpetal` → **Moondew Petals**

Local food herbs such as Marsh Mint, Yarrow, Siltroot and Ironstem may remain as
regional crops, but they are not part of the global rarity registry.

---

## 5. Magic, runes and trinkets

| Material | Rarity | Level | Primary source | Main station | Lore and future use |
|---|---|---:|---|---|---|
| **Arcane Dust** | Uncommon | 6–20 | Disenchanted items and spell residue | Enchanter / Scriptorium | Neutral base for enchantments, runes and Arcane Ink. |
| **Silver Filigree Wire** | Uncommon | 10–20 | Jeweler guilds | Jeweler / Enchanter | Rings, amulets, focus cages and precision mechanisms. |
| **Mirror Dust** | Uncommon | 10–20 | Argent Veil mirrors | Manipulation Enchanter | Illusion jewelry, mind wards and reflective inks. |
| **Focus Powder** | Uncommon/Rare | 11–20 | Ground focus crystals | Alchemy / Enchanter | Spell stabilization, mana brews and focus construction. |
| **Focus Crystal Shard** | Rare | 16–25 | Crystal caverns and broken foci | Enchanter / Scriptorium | Rare caster equipment and master crafting stations. |
| **Rune Plate** | Rare | 16–25 | Runesmiths and old vaults | Rune Desk / Blacksmith | Safe rune upgrades for weapons and armor. |
| **Sanctified Ember** | Rare | 16–25 | Radiant Synod braziers | Holy Enchanter | Holy trinkets, undead wards and purification seals. |
| **Soul Ash** | Rare | 16–25 | Necromantic remains | Necromantic Enchanter | Spirit bindings, death wards and Ossuary trinkets. |
| **Echo Shard** | Rare *(Epic grade)* | 18–30 | Lesser Abyssal Echo bosses | Enchanter / Artifact Forge | Legendary upgrades containing a fragment of a boss identity. |
| **Seal-Lacquer** | Very Rare | 22–30 | Highstone charter stores | Highstone Rune Desk | Anti-corruption coating and legal artifact seals. |
| **Charter Seal Token** | Mythic | 30+ | Granted by Highstone | Artifact Registry | Permission to create and register a legal Mythic artifact. |

Holy and necromantic ingredients should remain mechanically distinct. A
Sanctified Ember cannot simply replace Soul Ash without changing the result.

---

## 6. Scrolls and spell components

| Material | Rarity | Level | Primary source | Main station | Lore and future use |
|---|---|---:|---|---|---|
| **Parchment Sheet** | Common | 1+ | Scribes, tanners and markets | Scriptorium | Scrolls, spellbooks, maps and contracts. |
| **Wax Seal** | Common | 1+ | Markets and beekeepers | Scriptorium | Closes contracts, ritual packets and sealed scrolls. |
| **Arcane Ink** | Uncommon | 6+ | Arcane Dust mixed with ink | Scriptorium | Spell scrolls, rune diagrams and enchanted contracts. |
| **Spell Focus Bead** | Uncommon | 6–15 | Prism workshops and jewelers | Scriptorium / Enchanter | Gives a spell a stable starting point and upgrades staves. |

---

## Current gameplay connections

The registry is already connected to:

- inventory and loot recognition
- old-save name migration
- Muckford market sell prices and Common supply stock
- hover lore in the Muckford market
- farming crops and potion ingredients
- Smeltery Iron Ingot production
- blueprint station metadata
- Barracks station upgrade costs and component recipes
- active Muckford material contracts
- future regional contract templates

### Active Muckford contracts

- Fuel for the Mud Furnace — Coal
- Fiber for the Cots — Plant Fiber
- A Proper Iron Batch — Iron Ore
- The Bitterleaf Standard — Bitterleaf
- Nightcap Warning — Nightcap Fungus
- Ink and Oaths — Parchment Sheet and Wax Seal

### Future contract chains

Code templates already exist for Blacksteel, Wyrdwood bindings, tannery work,
Stormsilver, Sun-Gold, Grave-Lotus and Soul Ash, Prism components, Outer
Shatterbelt samples, Echo Shards and Highstone artifact authorization.

---

## Canonical compatibility aliases

| Older name | Canonical name |
|---|---|
| Iron Bar | Iron Ingot |
| Swamp Wood | Rough Timber |
| Void Iron | Void-Iron |
| Dragon Scale | Drake Scale |
| Stormsilver | Stormsilver Ore |
| Sun-Gold / Sun-Gold Vein | Sun-Gold Ore |
| Bogwort / Medicinal Herb | Bitterleaf |
| Sunleaf | Sunblossom |
| Moonpetal | Moondew Petals |

Aliases exist only for save and code compatibility. New content must use the
canonical names.
