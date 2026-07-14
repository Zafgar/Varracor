"""Canonical world-map, route and arena progression data for Varrakor.

Coordinates use a 1000 x 650 logical map. Gameplay menus scale them to the
current resolution. This module intentionally contains no pygame imports so it
can be tested and reused by saves, quests, travel and future local maps.
"""

from __future__ import annotations

from collections import OrderedDict


WORLD_MAP_SIZE = (1000, 650)

# Arena tier -> intended fighter/party level band. LeagueEngine tier 1 maps to
# lore tier 0, so gameplay code should subtract one before using this table.
ARENA_LEVEL_BANDS = {
    0: (1, 5),
    1: (6, 10),
    2: (11, 15),
    3: (16, 20),
    4: (21, 25),
    5: (26, 30),
}

REGIONS = OrderedDict({
    "sundered_heartlands": {
        "name": "The Sundered Heartlands",
        "faction": None,
        "level_range": (1, 30),
        "color": (105, 82, 78),
        "polygon": [(365, 205), (535, 170), (650, 250), (620, 395),
                    (505, 455), (370, 395), (325, 285)],
        "summary": ("Ruined roads, marshes and shattered settlements circling "
                    "the Abyssal Vortex."),
        "themes": ("ruins", "marsh", "Taint", "broken trade roads"),
    },
    "crownlands": {
        "name": "The Crownlands",
        "faction": "crown_dominion",
        "level_range": (5, 25),
        "color": (126, 132, 91),
        "polygon": [(40, 160), (360, 105), (390, 230), (325, 285),
                    (370, 395), (245, 505), (55, 440)],
        "summary": ("River plains, fortified trade cities and Crown-controlled "
                    "industry west of the Vortex."),
        "themes": ("roads", "taxes", "industry", "holy authority"),
    },
    "sunscar_expanse": {
        "name": "The Sunscar Expanse",
        "faction": "horned_throne",
        "level_range": (1, 28),
        "color": (151, 108, 62),
        "polygon": [(245, 505), (370, 395), (505, 455), (620, 395),
                    (795, 505), (750, 635), (265, 635)],
        "summary": ("Desert roads, quarries, fortress plateaus and water-starved "
                    "caravan settlements."),
        "themes": ("heat", "water", "honor", "caravans"),
    },
    "wyrdwood": {
        "name": "The Wyrdwood",
        "faction": "lupine_wardens",
        "level_range": (1, 25),
        "color": (61, 104, 72),
        "polygon": [(650, 250), (925, 145), (970, 445), (795, 505),
                    (620, 395)],
        "summary": ("Ancient forest, jungle margins and sacred groves guarded "
                    "by the Lupine Wardens."),
        "themes": ("living forest", "poisons", "druidism", "Taint cleansing"),
    },
    "aegis_peaks": {
        "name": "The Aegis Peaks & Sanctum Marches",
        "faction": "highstone_sanctum",
        "level_range": (14, 30),
        "color": (105, 121, 148),
        "polygon": [(190, 40), (800, 35), (925, 145), (650, 250),
                    (535, 170), (365, 205), (360, 105)],
        "summary": ("Neutral mountain roads, crystal cities and Highstone's "
                    "fortress-temple above the kingdoms."),
        "themes": ("snow", "crystal", "neutral law", "elite arenas"),
    },
})


def _location(name, region, pos, level_range, kind, summary, lore,
              required_tier=0, required_rep=0, reveal_tier=0,
              arena_tier=None, arena_name=None, target_state=None,
              content_state="future", services=(), threats=(), materials=(),
              requires_manager_attr=None, requires_visited=(), landmark=False):
    return {
        "name": name,
        "region": region,
        "map_pos": tuple(pos),
        "level_range": tuple(level_range),
        "kind": kind,
        "summary": summary,
        "lore": lore,
        "required_tier": int(required_tier),
        "required_rep": int(required_rep),
        "reveal_tier": int(reveal_tier),
        "arena_tier": arena_tier,
        "arena_name": arena_name,
        "target_state": target_state,
        "content_state": content_state,
        "services": tuple(services),
        "threats": tuple(threats),
        "materials": tuple(materials),
        "requires_manager_attr": requires_manager_attr,
        "requires_visited": tuple(requires_visited),
        "landmark": bool(landmark),
    }


LOCATIONS = OrderedDict({
    # ------------------------------------------------------------------
    # Sundered Heartlands and Vortex
    # ------------------------------------------------------------------
    "muckford": _location(
        "Muckford", "sundered_heartlands", (350, 345), (1, 5), "city",
        "Mud-built Tier 0 hub on the western edge of the Heartlands.",
        "Debt, salvage and the Shanty Yard make Muckford the arena system's harshest entry gate.",
        arena_tier=0, arena_name="Shanty Yard", target_state="muckford_city",
        content_state="playable", services=("Market", "Smeltery", "Team Quarters", "Hospice"),
        threats=("rat raids", "marsh disease"), materials=("Scrap Iron", "Coal", "Bitterleaf"),
        landmark=True,
    ),
    "shanty_yard": _location(
        "Shanty Yard", "sundered_heartlands", (382, 325), (1, 5), "arena",
        "Muckford's Tier 0 arena and registration yard.",
        "Bram's circuit tests whether a team can survive debt, mud and badly maintained hazards.",
        arena_tier=0, arena_name="Shanty Yard", target_state="league",
        content_state="playable", services=("League registration", "1v1", "3v3", "5v5"),
        threats=("scrap hazards",), landmark=True,
    ),
    "whisper_marsh": _location(
        "Whisper Marsh", "sundered_heartlands", (425, 395), (1, 5), "wilds",
        "Low marsh and drowned woodland south-east of Muckford.",
        "The water repeats voices after dark, and every rain pushes new creatures toward the roads.",
        target_state="forest_excursion", content_state="playable",
        services=("foraging", "monster hunt"),
        threats=("Mire-Lurkers", "Bog Leeches", "giant frogs"),
        materials=("Bitterleaf", "Nightcap Fungus", "Resin"),
    ),
    # --- RIFT-INVAASIOALUEET (pelitesti 20) ---
    # Vortex-repeämiä aukeaa erämaihin: wave-taistelu + jättiboss,
    # sinetöinnistä Vortex-kristalleja VORTEX-puuhun.
    "rift_whisper_marsh": _location(
        "Whisper Marsh Rift", "sundered_heartlands", (447, 412), (3, 8),
        "vortex",
        "A great Vortex rift has torn open among the drowned pools.",
        "The marsh water boils around the breach. Leeches and frogs pour "
        "out in waves - and something far larger waits behind them.",
        target_state="rift_site", content_state="playable",
        services=("rift invasion",),
        threats=("Bog Leeches", "giant frogs", "Broodmother"),
        materials=("Vortex Crystal",),
    ),
    "rift_drowned_graveyard": _location(
        "Drowned Graveyard Rift", "sundered_heartlands", (395, 430), (4, 9),
        "vortex",
        "A rift yawns between the sunken headstones south of Muckford.",
        "The dead answer the Vortex first. Skeletons and worse climb from "
        "the breach in waves until the Grave Tyrant itself steps through.",
        target_state="rift_site", content_state="playable",
        services=("rift invasion",),
        threats=("undead", "Grave Tyrant"),
        materials=("Vortex Crystal",),
    ),
    "rift_bogwood": _location(
        "Bogwood Rift", "sundered_heartlands", (470, 355), (3, 8),
        "vortex",
        "A rift crackles in the tangled bog-forest east of the city.",
        "Rat packs and corrupted crows swarm from the tear, driven ahead "
        "of a rider that no longer remembers being anything else.",
        target_state="rift_site", content_state="playable",
        services=("rift invasion",),
        threats=("rat packs", "corrupted crows", "Rift-Rider Alpha"),
        materials=("Vortex Crystal",),
    ),
    "old_mine_road": _location(
        "Old Muckford Mine", "sundered_heartlands", (315, 300), (3, 7), "dungeon",
        "Abandoned mine road and a web-sealed cave system.",
        "The mine once supplied cheap iron. Undead and the Cave Broodmother now guard its deeper chamber.",
        target_state="mine_road", content_state="playable",
        services=("mining",), threats=("undead", "Cave Broodmother"),
        materials=("Iron Ore", "Coal", "Chipped Ruby"),
        requires_manager_attr=("mine_key_owned", True),
    ),
    "greywash_ford": _location(
        "Greywash Ford", "sundered_heartlands", (330, 300), (5, 7), "wilds",
        "Shallow river crossing north-west of Muckford where the Western causeway begins.",
        "The Greywash marks where Muckford's mud ends and Crown-laid stone starts. "
        "The causeway climbs north-west from here toward the Crown tolls; "
        "ford ambushers, deserters and toll-dodgers prey on teams too poor to "
        "pay the King's road.",
        required_tier=0, reveal_tier=0, target_state="regional_staging",
        content_state="survey", services=("ford crossing", "scouting"),
        threats=("ford ambushers", "toll-dodgers", "Gutter overflow"),
        materials=("Scrap Iron", "Bitterleaf", "River Reed"),
    ),
    "sundered_ruins": _location(
        "Sundered Road Ruins", "sundered_heartlands", (470, 315), (6, 10), "ruins",
        "Collapsed toll roads and settlements nearer the Vortex.",
        "The ruins are the first place where ordinary road patrols become Vortex containment work.",
        required_tier=1, reveal_tier=1, content_state="survey",
        target_state="regional_staging", threats=("Water-risen", "Taint pockets"),
        materials=("Scrap Iron", "Arcane Dust"),
    ),
    "outer_shatterbelt": _location(
        "Outer Shatterbelt", "sundered_heartlands", (535, 305), (26, 27), "vortex",
        "The first stable ring surrounding the Abyssal Vortex.",
        "Reality fractures here in visible seams. Highstone permits only Golden League teams to cross.",
        required_tier=5, required_rep=150, reveal_tier=4, content_state="survey",
        target_state="regional_staging", threats=("Abyssal Chitin hosts", "Taint storms"),
        materials=("Void-Iron", "Abyssal Chitin", "Vortex Residue"), landmark=True,
    ),
    "spiral_scar": _location(
        "Spiral Scar", "sundered_heartlands", (565, 315), (28, 29), "vortex",
        "A rotating fault where distance and time fold around the Vortex.",
        "Scouts mark paths with synchronized bells because maps change between one heartbeat and the next.",
        required_tier=5, required_rep=220, reveal_tier=5, content_state="future",
        requires_visited=("outer_shatterbelt",), threats=("Mnemonic Echoes", "time fractures"),
        materials=("Echo Shard", "Vortex Residue"),
    ),
    "the_throat": _location(
        "The Throat", "sundered_heartlands", (590, 325), (29, 30), "vortex",
        "The narrowing descent into the Vortex's living storm.",
        "Every expedition hears the same impossible breathing, even in complete silence.",
        required_tier=5, required_rep=300, reveal_tier=5, content_state="future",
        requires_visited=("spiral_scar",), threats=("major Abyssal Echoes",),
        materials=("Echo Heart",),
    ),
    "the_eye": _location(
        "The Eye", "sundered_heartlands", (610, 335), (30, 30), "vortex",
        "The core of the Abyssal Vortex.",
        "Heartcore Adamant forms where the world's laws are compressed into one impossible point.",
        required_tier=5, required_rep=400, reveal_tier=5, content_state="future",
        requires_visited=("the_throat",), threats=("world-class Abyssal Echoes",),
        materials=("Heartcore Adamant", "Echo Heart"), landmark=True,
    ),

    # ------------------------------------------------------------------
    # Crownlands
    # ------------------------------------------------------------------
    "kingsreach_toll": _location(
        "Kingsreach Toll", "crownlands", (299, 274), (6, 8), "outpost",
        "Crown tollgate on the causeway, the first checkpoint of King Alaric's roads.",
        "North-west of the Greywash the road turns to counted Crown stone. Every "
        "wheel, boot and blade is taxed here, and the guards are bored, bribable "
        "and quick to quarantine anyone coughing on the way down from fever-struck "
        "Rattlebridge, one more day's march north-west.",
        required_tier=0, reveal_tier=0, target_state="regional_staging",
        content_state="survey", services=("toll gate", "Crown notices", "caravan rest"),
        threats=("toll enforcers", "road bandits", "quarantine sweeps"),
        materials=("Parchment Sheet", "Wax Seal", "Iron Ore"),
    ),
    "rattlebridge": _location(
        "Rattlebridge", "crownlands", (275, 240), (6, 9), "city",
        "Massive bridge-city and the main western route around the Vortex.",
        "Sera Quench turns desperate Tier 1 teams into marketable Scrapring brands.",
        required_tier=1, reveal_tier=0, arena_tier=1, arena_name="The Scrapring",
        target_state="regional_staging", content_state="survey",
        services=("Tier 1 league", "sponsors", "caravan market"),
        threats=("bridge raiders",), materials=("Iron Ore", "Parchment Sheet"), landmark=True,
    ),
    "rivet_row": _location(
        "Rivet Row", "crownlands", (205, 315), (7, 10), "city",
        "Industrial smoke-city south-west of Rattlebridge.",
        "Its Bolt Cage rewards brutal control in cramped mechanical arenas.",
        required_tier=1, reveal_tier=1, arena_tier=1, arena_name="Bolt Cage",
        target_state="regional_staging", content_state="survey",
        services=("Blacksteel forge", "Bolt Cage", "repair guilds"),
        threats=("factory fires", "metal thieves"),
        materials=("Iron Ingot", "Blacksteel Ore", "Tempering Flux"),
    ),
    "giltgate": _location(
        "Giltgate", "crownlands", (155, 260), (11, 14), "city",
        "Wealthy market city whose gates are plated to advertise its success.",
        "Vessik Coincroak's Iron Circle makes contracts and odds as important as sword work.",
        required_tier=2, reveal_tier=1, arena_tier=2, arena_name="The Iron Circle",
        target_state="regional_staging", content_state="survey",
        services=("Tier 2 league", "betting", "advanced market"),
        threats=("contract traps",), materials=("Blacksteel Ingot", "Silver Filigree Wire"), landmark=True,
    ),
    "ledgerford": _location(
        "Ledgerford", "crownlands", (115, 210), (12, 15), "city",
        "Court, customs and accounting city on the Crownflow River.",
        "Here a team can lose a season to a clause before anyone draws a weapon.",
        required_tier=2, reveal_tier=2, arena_tier=2, arena_name="Contract Court",
        target_state="regional_staging", content_state="survey",
        services=("contracts", "legal reputation", "scriptorium"),
        threats=("customs seizures",), materials=("Arcane Ink", "Wax Seal", "Parchment Sheet"),
    ),
    "coinharbor": _location(
        "Coinharbor", "crownlands", (70, 345), (13, 16), "port",
        "Western trade port facing Water-risen swarms.",
        "Arena teams double as harbor defenders when the sea disgorges Vortex-corrupted dead.",
        required_tier=2, reveal_tier=2, arena_tier=2, arena_name="Tidepit",
        target_state="regional_staging", content_state="survey",
        services=("sea contracts", "shipping", "Tidepit"),
        threats=("Water-risen", "sea monsters"), materials=("Direhide", "Arcane Dust"), landmark=True,
    ),
    "crownhold": _location(
        "Crownhold", "crownlands", (210, 120), (21, 25), "capital",
        "Human capital at the Crownflow river junction.",
        "Alaric Vane rules through bureaucracy, military pageantry and carefully rationed access.",
        required_tier=4, required_rep=100, reveal_tier=2, arena_tier=4,
        arena_name="Lion Court", target_state="regional_staging", content_state="survey",
        services=("royal contracts", "Sunspire Basilica", "Mirror Court"),
        threats=("political manipulation",), materials=("Sun-Gold Ore", "Sanctified Ember"), landmark=True,
    ),
    "sunspire_basilica": _location(
        "Sunspire Basilica", "crownlands", (235, 95), (18, 25), "magic_school",
        "Seat of the Radiant Synod and Crown holy medicine.",
        "Its light heals quickly, but every treatment is recorded as a moral debt.",
        required_tier=3, required_rep=80, reveal_tier=3, content_state="future",
        services=("Holy Magic", "Sunbound Hospice"), materials=("Sanctified Ember", "Sunblossom"),
    ),
    "mirror_court": _location(
        "Mirror Court", "crownlands", (185, 95), (18, 25), "magic_school",
        "Public diplomatic court concealing the Argent Veil.",
        "Every polished wall is designed to make visitors unsure which expression was truly theirs.",
        required_tier=3, required_rep=100, reveal_tier=3, content_state="future",
        services=("Manipulation Magic", "intelligence contracts"),
        materials=("Mirror Dust", "Silver Filigree Wire"),
    ),

    # ------------------------------------------------------------------
    # Sunscar Expanse
    # ------------------------------------------------------------------
    "saffron_oasis": _location(
        "Saffron Oasis", "sunscar_expanse", (405, 540), (1, 5), "city",
        "Palm oasis and Tier 0 caravan stop on the desert's eastern road.",
        "Water discipline defines its arena: waste strength early and the heat wins first.",
        required_rep=10, reveal_tier=0, arena_tier=0, arena_name="Oasis Pit",
        target_state="regional_staging", content_state="survey",
        services=("Tier 0 league", "water market", "caravan camp"),
        threats=("heat", "raiders"), materials=("Resin", "Tanned Hide"), landmark=True,
    ),
    "kestrel_way": _location(
        "Caravanserai Kestrel-Way", "sunscar_expanse", (520, 555), (11, 15), "caravanserai",
        "Fortified caravan exchange linking the southern routes.",
        "Its Tier 2 ring changes hazards between rounds as caravans arrive with new cargo.",
        required_tier=2, reveal_tier=1, arena_tier=2, arena_name="Kestrel Caravan Ring",
        target_state="regional_staging", content_state="survey",
        services=("Tier 2 league", "caravan contracts", "desert supplies"),
        threats=("sand predators",), materials=("Direhide", "Tempering Flux"),
    ),
    "hornfall": _location(
        "Hornfall", "sunscar_expanse", (625, 550), (16, 20), "fortress",
        "Rock fortress guarding the western approach to Kharak-Tor.",
        "Hornfall measures service in guarded wells and defended road miles, not speeches.",
        required_tier=3, reveal_tier=2, target_state="regional_staging", content_state="survey",
        services=("military contracts", "Stoneblood Hospice"),
        threats=("siege beasts",), materials=("Trollbone Plating", "Blacksteel Ingot"),
    ),
    "stonegrit": _location(
        "Stonegrit", "sunscar_expanse", (690, 590), (17, 21), "quarry_city",
        "Quarry city supplying the Horned Throne's fortresses.",
        "Dust, falling stone and labor feuds make every contract physically and politically dangerous.",
        required_tier=3, reveal_tier=3, target_state="regional_staging", content_state="survey",
        services=("quarry", "heavy crafting"), threats=("stone giants", "cave-ins"),
        materials=("Trollbone Plating", "Focus Crystal Shard"),
    ),
    "bonewind_necropolis": _location(
        "Bonewind Necropolis", "sunscar_expanse", (705, 465), (19, 23), "necropolis",
        "City of the dead and seat of the Ashen Ossuary.",
        "Zharok's mortarchs treat death as a discipline; uncontrolled necromancy is punished without mercy.",
        required_tier=3, required_rep=70, reveal_tier=2, arena_tier=4,
        arena_name="Ossuary Circle", target_state="regional_staging", content_state="survey",
        services=("Necromancy", "death contracts", "Bonewright"),
        threats=("restless dead", "soul storms"), materials=("Soul Ash", "Grave-Lotus"), landmark=True,
    ),
    "kharak_tor": _location(
        "Kharak-Tor", "sunscar_expanse", (735, 535), (21, 25), "capital",
        "Minotaur capital built on a fortified stone plateau.",
        "The Silver League Grand Ring is a military proving ground disguised as sport.",
        required_tier=4, required_rep=100, reveal_tier=2, arena_tier=4,
        arena_name="Silver League Grand Ring", target_state="regional_staging", content_state="survey",
        services=("Tier 4 league", "master smiths", "Stoneblood Hospice"),
        threats=("honor trials",), materials=("Drake Scale", "Trollbone Plating"), landmark=True,
    ),
    "howling_barrens": _location(
        "The Howling Barrens", "sunscar_expanse", (650, 625), (24, 28), "wilds",
        "Extreme southern frontier beyond reliable caravan law.",
        "The wind howls through fossil canyons loudly enough to hide entire monster migrations.",
        required_tier=4, required_rep=130, reveal_tier=4, content_state="future",
        threats=("drakes", "giant predators"), materials=("Drake Scale", "Direhide"), landmark=True,
    ),

    # ------------------------------------------------------------------
    # Wyrdwood
    # ------------------------------------------------------------------
    "vinehollow": _location(
        "Vinehollow", "wyrdwood", (825, 455), (1, 5), "city",
        "Dangerous settlement where jungle and wet forest meet.",
        "Its Drumring teaches footing, poison awareness and respect for terrain before raw strength.",
        required_rep=10, reveal_tier=0, arena_tier=0, arena_name="Jungle Drumring",
        target_state="regional_staging", content_state="survey",
        services=("Tier 0 league", "poison experts", "antidotes"),
        threats=("venom beasts", "slippery hazards"),
        materials=("Nightcap Fungus", "Direhide", "Resin"), landmark=True,
    ),
    "timbercross": _location(
        "Timbercross", "wyrdwood", (735, 310), (6, 10), "border_city",
        "Palisade logging city on the Crown-Wyrdwood border.",
        "Every felled tree is political. Arena matches often settle disputes patrols cannot.",
        required_tier=1, reveal_tier=0, arena_tier=1, arena_name="Palisade Ring",
        target_state="regional_staging", content_state="survey",
        services=("Tier 1 league", "woodworking", "border contracts"),
        threats=("border skirmishes",), materials=("Oakwood", "Ironbark"), landmark=True,
    ),
    "elderroot_grove": _location(
        "Elderroot Grove", "wyrdwood", (835, 285), (13, 18), "sacred_grove",
        "Ancient grove and headquarters of the Verdant Covenant.",
        "The roots remember old wars and tighten around anyone carrying uncontrolled Taint.",
        required_tier=2, required_rep=60, reveal_tier=2, target_state="regional_staging",
        content_state="survey", services=("Druidism", "living crafting", "Taint cleansing"),
        threats=("territorial spirits",), materials=("Moonwillow", "Elderroot Fiber"), landmark=True,
    ),
    "moonwatch": _location(
        "Moonwatch", "wyrdwood", (885, 210), (17, 22), "capital",
        "Werewolf capital raised above the forest canopy.",
        "Fenric Greyfang watches the moonlit borders and judges outsiders by what they leave unharmed.",
        required_tier=3, required_rep=90, reveal_tier=2, arena_tier=3,
        arena_name="Moonring", target_state="regional_staging", content_state="survey",
        services=("Tier 3 league", "Moonbloom Sanctuary", "Warden contracts"),
        threats=("Taint incursions",), materials=("Moonwillow", "Focus Powder"), landmark=True,
    ),
    "deep_wyrdwood": _location(
        "Deep Wyrdwood", "wyrdwood", (925, 330), (20, 25), "wilds",
        "Unmapped living forest east of Elderroot Grove.",
        "Paths close behind careless travelers, and the forest itself chooses which wounds it will forgive.",
        required_tier=4, required_rep=120, reveal_tier=3, content_state="future",
        threats=("ancient beasts", "living labyrinth"),
        materials=("Elderroot Fiber", "Ironbark", "Moonwillow"),
    ),

    # ------------------------------------------------------------------
    # Aegis Peaks and Sanctum Marches
    # ------------------------------------------------------------------
    "sanctum_marches": _location(
        "Sanctum Marches", "aegis_peaks", (510, 145), (14, 18), "marches",
        "Guarded foothill roads beneath Highstone authority.",
        "The Marches are neutral only because every kingdom fears breaking Arkon's road law first.",
        required_tier=2, reveal_tier=1, target_state="regional_staging", content_state="survey",
        services=("neutral contracts", "caravan guards"),
        threats=("mountain raiders",), materials=("Stormsilver Ore", "Focus Crystal Shard"), landmark=True,
    ),
    "prismhall": _location(
        "Prismhall", "aegis_peaks", (585, 135), (15, 20), "magic_school",
        "Neutral campus of the Prism Collegium.",
        "Pure Magic is taught as a common language before students are trusted with faction schools.",
        required_tier=2, required_rep=50, reveal_tier=2, target_state="regional_staging",
        content_state="survey", services=("Pure Magic", "Scriptorium", "Enchanter"),
        threats=("unstable experiments",), materials=("Arcane Dust", "Spell Focus Bead", "Arcane Ink"),
    ),
    "ironwind_pass": _location(
        "Ironwind Pass", "aegis_peaks", (350, 115), (16, 20), "mountain_pass",
        "Strategic pass between Crown roads and the neutral north.",
        "Control of the pass determines which kingdom reaches Highstone without crossing hostile borders.",
        required_tier=3, reveal_tier=2, target_state="regional_staging", content_state="survey",
        services=("escort contracts",), threats=("avalanches", "peak predators"),
        materials=("Stormsilver Ore", "Blacksteel Ore"), landmark=True,
    ),
    "windstep": _location(
        "Windstep", "aegis_peaks", (470, 85), (16, 20), "city",
        "Lower mountain city built around suspension roads.",
        "Its Skychain arena punishes teams that cannot control space and knockback.",
        required_tier=3, reveal_tier=3, arena_tier=3, arena_name="Skychain Arena",
        target_state="regional_staging", content_state="survey",
        services=("Tier 3 league", "mountain guides"), threats=("falls", "high winds"),
        materials=("Stormsilver Ore", "Focus Powder"),
    ),
    "gleamhold": _location(
        "Gleamhold", "aegis_peaks", (610, 75), (17, 21), "city",
        "Crystal-cut city reflecting light across the lower peaks.",
        "The Crystal Crucible rewards spell timing and punishes uncontrolled area attacks.",
        required_tier=3, reveal_tier=3, arena_tier=3, arena_name="Crystal Crucible",
        target_state="regional_staging", content_state="survey",
        services=("Tier 3 league", "crystal market", "enchanting"),
        threats=("crystal resonance"), materials=("Focus Crystal Shard", "Rune Plate"),
    ),
    "spirewatch": _location(
        "Spirewatch", "aegis_peaks", (690, 105), (18, 22), "city",
        "Elegant lower-peak city of duel halls and observatories.",
        "Lord Caelith Vaelor's Steel Arena treats positioning and precision as proof of civilization.",
        required_tier=3, reveal_tier=2, arena_tier=3, arena_name="The Steel Arena",
        target_state="regional_staging", content_state="survey",
        services=("Tier 3 league", "duel halls", "elite trainers"),
        threats=("elite rival teams",), materials=("Stormsilver Ingot", "Rune Plate"), landmark=True,
    ),
    "highstone_sanctum": _location(
        "Highstone Sanctum", "aegis_peaks", (545, 45), (26, 30), "sanctum",
        "Neutral fortress-temple and seat of the Golden League.",
        "Arkon's protocols turn the strongest arena teams into legal Vortex expedition forces.",
        required_tier=5, required_rep=150, reveal_tier=3, arena_tier=5,
        arena_name="The Golden League", target_state="regional_staging", content_state="survey",
        services=("Tier 5 league", "artifact registry", "best hospice", "Arkon's court"),
        threats=("final trials",), materials=("Seal-Lacquer", "Charter Seal Token"), landmark=True,
    ),
})


ARENA_CIRCUITS = OrderedDict({
    0: {
        "name": "The Rookie Dust Circuit",
        "level_range": ARENA_LEVEL_BANDS[0],
        "locations": ("shanty_yard", "saffron_oasis", "vinehollow"),
        "purpose": "Survival fundamentals, team registration and first regional contacts.",
    },
    1: {
        "name": "The Scrapring Circuit",
        "level_range": ARENA_LEVEL_BANDS[1],
        "locations": ("rattlebridge", "rivet_row", "timbercross"),
        "purpose": "Sponsors, professional gear and control of trade-route hazards.",
    },
    2: {
        "name": "The Iron Circle Circuit",
        "level_range": ARENA_LEVEL_BANDS[2],
        "locations": ("giltgate", "ledgerford", "coinharbor", "kestrel_way"),
        "purpose": "Contracts, betting, regional logistics and specialist crafting.",
    },
    3: {
        "name": "The Steel Arena Circuit",
        "level_range": ARENA_LEVEL_BANDS[3],
        "locations": ("spirewatch", "windstep", "gleamhold", "moonwatch"),
        "purpose": "Elite tactics, magic integration and faction-level responsibility.",
    },
    4: {
        "name": "The Silver League Circuit",
        "level_range": ARENA_LEVEL_BANDS[4],
        "locations": ("kharak_tor", "crownhold", "bonewind_necropolis"),
        "purpose": "National champions, war readiness and access to legendary materials.",
    },
    5: {
        "name": "The Golden League",
        "level_range": ARENA_LEVEL_BANDS[5],
        "locations": ("highstone_sanctum",),
        "purpose": "Artifact authorization and preparation for the Vortex's deepest rings.",
    },
})


def _route(a, b, hours, danger, label):
    return {"a": a, "b": b, "hours": int(hours),
            "danger": int(danger), "label": label}


ROUTES = [
    # Heartlands local routes
    _route("muckford", "shanty_yard", 1, 1, "Shanty road"),
    _route("muckford", "whisper_marsh", 4, 2, "Whisper track"),
    # Rift-invaasioalueiden polut (pelitesti 20)
    _route("muckford", "rift_whisper_marsh", 3, 3, "Rift trail (marsh)"),
    _route("muckford", "rift_drowned_graveyard", 3, 3,
           "Rift trail (graveyard)"),
    _route("muckford", "rift_bogwood", 3, 3, "Rift trail (bogwood)"),
    _route("whisper_marsh", "rift_whisper_marsh", 1, 2, "Breach path"),
    _route("muckford", "old_mine_road", 3, 2, "Old mine road"),
    _route("muckford", "sundered_ruins", 6, 4, "Broken Crown road"),

    # Western causeway: Muckford -> Rattlebridge is walked in legs, not one hop.
    _route("muckford", "greywash_ford", 4, 2, "Western causeway (Greywash leg)"),
    _route("greywash_ford", "kingsreach_toll", 4, 3, "Western causeway (toll leg)"),
    _route("kingsreach_toll", "rattlebridge", 4, 3, "Western causeway (bridge approach)"),

    # Western trade loop
    _route("rattlebridge", "rivet_row", 5, 3, "Rivet freight road"),
    _route("rattlebridge", "giltgate", 8, 3, "Crownflow road"),
    _route("giltgate", "ledgerford", 4, 2, "Ledger road"),
    _route("giltgate", "coinharbor", 9, 4, "Western caravan coast"),
    _route("ledgerford", "crownhold", 8, 4, "Royal river road"),
    _route("crownhold", "sunspire_basilica", 1, 2, "Sunspire ascent"),
    _route("crownhold", "mirror_court", 1, 3, "Court avenue"),
    _route("crownhold", "ironwind_pass", 10, 5, "Northern military road"),

    # Southern loop
    _route("muckford", "saffron_oasis", 14, 4, "Silt caravan road"),
    _route("saffron_oasis", "kestrel_way", 9, 4, "Kestrel caravan route"),
    _route("kestrel_way", "hornfall", 8, 5, "Hornfall approach"),
    _route("hornfall", "stonegrit", 5, 5, "Quarry road"),
    _route("hornfall", "kharak_tor", 9, 6, "Throne road"),
    _route("kharak_tor", "bonewind_necropolis", 8, 7, "Bonewind road"),
    _route("kharak_tor", "howling_barrens", 11, 8, "Southern frontier track"),
    _route("bonewind_necropolis", "sundered_ruins", 10, 7, "Deadward road"),

    # Eastern forest loop
    _route("muckford", "vinehollow", 14, 4, "Marsh-jungle road"),
    _route("muckford", "timbercross", 10, 3, "Timber border road"),
    _route("timbercross", "elderroot_grove", 8, 5, "Warden trail"),
    _route("elderroot_grove", "moonwatch", 7, 6, "Moonroot path"),
    _route("vinehollow", "elderroot_grove", 10, 6, "Vine trail"),
    _route("moonwatch", "deep_wyrdwood", 6, 8, "Deep Wyrd path"),
    _route("moonwatch", "spirewatch", 12, 7, "Eastern peak road"),

    # Northern neutral loop
    _route("rattlebridge", "sanctum_marches", 11, 5, "March road"),
    _route("sanctum_marches", "prismhall", 3, 3, "Prism road"),
    _route("sanctum_marches", "ironwind_pass", 7, 6, "Aegis west road"),
    _route("sanctum_marches", "windstep", 6, 6, "Windstep ascent"),
    _route("windstep", "gleamhold", 5, 6, "Lower peak chain"),
    _route("gleamhold", "spirewatch", 5, 6, "Crystal road"),
    _route("windstep", "highstone_sanctum", 12, 9, "Highstone pilgrimage"),
    _route("spirewatch", "highstone_sanctum", 10, 9, "Golden ascent"),

    # Vortex descent
    _route("sundered_ruins", "outer_shatterbelt", 6, 9, "Containment road"),
    _route("outer_shatterbelt", "spiral_scar", 4, 10, "Shifting seam"),
    _route("spiral_scar", "the_throat", 3, 10, "Spiral descent"),
    _route("the_throat", "the_eye", 2, 10, "Final descent"),
]


STARTING_DISCOVERED_LOCATIONS = (
    "muckford",
    "shanty_yard",
    "whisper_marsh",
    "old_mine_road",
    "rattlebridge",
    "saffron_oasis",
    "vinehollow",
    "timbercross",
)


def get_location(location_id):
    return LOCATIONS.get(str(location_id))


def get_region(region_id):
    return REGIONS.get(str(region_id))


def get_neighbors(location_id):
    location_id = str(location_id)
    out = []
    for route in ROUTES:
        if route["a"] == location_id:
            out.append(route["b"])
        elif route["b"] == location_id:
            out.append(route["a"])
    return out


def get_route(a, b):
    a, b = str(a), str(b)
    for route in ROUTES:
        if {route["a"], route["b"]} == {a, b}:
            return route
    return None


# 8-wind compass. Map y grows downward, so "north" is decreasing y.
_COMPASS = [
    (0, "east"), (45, "north-east"), (90, "north"), (135, "north-west"),
    (180, "west"), (225, "south-west"), (270, "south"), (315, "south-east"),
]


def route_heading(a, b):
    """Compass direction travelling from location ``a`` to ``b`` (or None).

    Derived from map positions so every route reports "its direction" without
    hand-authoring. Returns e.g. "north-west".
    """
    import math
    la, lb = get_location(a), get_location(b)
    if not la or not lb:
        return None
    ax, ay = la["map_pos"]
    bx, by = lb["map_pos"]
    dx, dy = bx - ax, -(by - ay)  # flip y so north points up
    if dx == 0 and dy == 0:
        return None
    ang = math.degrees(math.atan2(dy, dx)) % 360
    best = min(_COMPASS, key=lambda c: min((ang - c[0]) % 360, (c[0] - ang) % 360))
    return best[1]


def journey_legs(a, b):
    """Ordered legs of a known multi-hop journey between ``a`` and ``b`` using a
    breadth-first walk over ROUTES. Each leg is (from, to, route, heading).
    Returns [] if no path exists."""
    a, b = str(a), str(b)
    if a == b:
        return []
    prev = {a: None}
    queue = [a]
    while queue:
        cur = queue.pop(0)
        if cur == b:
            break
        for nb in get_neighbors(cur):
            if nb not in prev:
                prev[nb] = cur
                queue.append(nb)
    if b not in prev:
        return []
    path = []
    node = b
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return [(path[i], path[i + 1], get_route(path[i], path[i + 1]),
             route_heading(path[i], path[i + 1]))
            for i in range(len(path) - 1)]


def get_circuit_for_location(location_id):
    for tier, circuit in ARENA_CIRCUITS.items():
        if location_id in circuit["locations"]:
            result = dict(circuit)
            result["tier"] = tier
            return result
    return None


def locations_for_region(region_id):
    return [(location_id, data) for location_id, data in LOCATIONS.items()
            if data["region"] == region_id]
