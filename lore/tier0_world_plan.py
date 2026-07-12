"""Canonical production plan for the playable Tier 0 world around Muckford.

Development order is not player lock order. Wilderness routes remain open once
physically discovered and show a danger warning. Only explicit keys, destroyed
routes, papers or formal arena promotion may block travel.
"""
from __future__ import annotations

from collections import OrderedDict


PLAN_VERSION = 6
CURRENT_FOCUS = "kingsreach_toll"

VALID_STATES = {"live", "partial", "next", "planned", "blocked"}
CONTENT_DOMAINS = (
    "area",
    "npcs",
    "quests",
    "dialogue",
    "resources",
    "creatures",
    "boss",
    "graphics",
    "vfx",
    "audio",
    "persistence",
    "tests",
)


def _area(
    name,
    order,
    level_range,
    purpose,
    environment,
    access_policy,
    entry_from,
    *,
    dependencies=(),
    physical_gate=None,
    npcs=(),
    quest_chains=(),
    resources=(),
    creatures=(),
    boss=None,
    graphics=(),
    vfx=(),
    systems=(),
    deliverables=None,
):
    states = {domain: "planned" for domain in CONTENT_DOMAINS}
    states.update(deliverables or {})
    return {
        "name": str(name),
        "order": int(order),
        "level_range": tuple(level_range),
        "purpose": str(purpose),
        "environment": tuple(environment),
        "access_policy": str(access_policy),
        "entry_from": tuple(entry_from),
        "dependencies": tuple(dependencies),
        "physical_gate": physical_gate,
        "npcs": tuple(npcs),
        "quest_chains": tuple(quest_chains),
        "resources": tuple(resources),
        "creatures": tuple(creatures),
        "boss": boss,
        "graphics": tuple(graphics),
        "vfx": tuple(vfx),
        "systems": tuple(systems),
        "deliverables": states,
    }


MOSTLY_LIVE = {
    "area": "live",
    "npcs": "live",
    "quests": "live",
    "dialogue": "live",
    "resources": "live",
    "creatures": "live",
    "boss": "live",
    "graphics": "live",
    "vfx": "live",
    "audio": "planned",
    "persistence": "live",
    "tests": "live",
}


TIER0_AREAS = OrderedDict({
    "muckford": _area(
        "Muckford",
        0,
        (1, 5),
        "Tier 0 hub for debt, registration, farming, crafting and arena management.",
        ("mud streets", "farms", "scrap market", "Shanty Yard"),
        "open_hub",
        (),
        npcs=(
            "Bram Mudhand Carrow",
            "Marda Shant",
            "Hamo",
            "Sister-Medic Rhea Ashford",
            "Farmer Gus",
        ),
        quest_chains=(
            "Marda's debt and mine key",
            "Official team registration",
            "Hamo rat-tail bounties",
            "Farmer Gus field work",
            "Warrens cellar-hatch crisis",
        ),
        resources=("Scrap Iron", "Coal", "Bitterleaf", "farm produce"),
        creatures=("Rat raids",),
        boss="The Rat King of Muckford",
        graphics=("city props", "farms", "arena gate", "sewer hatch", "NPC placeholders"),
        vfx=("rain", "mud", "smeltery", "raid warnings", "post-Warrens peace state"),
        systems=("economy", "registration", "farming", "barracks", "league", "rat raids"),
        deliverables={domain: "live" for domain in CONTENT_DOMAINS},
    ),
    "low_fields": _area(
        "Muckford Low Fields",
        1,
        (1, 3),
        "First exterior work zone for gathering and visible town recovery.",
        ("wet fields", "irrigation channel", "crop roads", "willow margins"),
        "open_with_warning",
        ("muckford", "whisper_marsh", "muckford_warrens"),
        dependencies=("muckford",),
        npcs=("Farmer Gus", "Lysa Reedrunner", "Orin Ditchhand", "Mela Root", "Tarn Wick"),
        quest_chains=(
            "Mend the irrigation channel",
            "Protect the grain cart",
            "Seal the Mud Mite burrows",
            "Rebuild the lower field footbridge",
        ),
        resources=("Carrot", "Potato", "Onion", "River Reed", "Clay", "Softwood"),
        creatures=("Mud Mite", "Reed Skitter", "Marsh Rat"),
        boss="The Burrow-Mother optional field event",
        graphics=("procedural crop fields", "irrigation water", "fences", "carts", "bridges"),
        vfx=("water ripples", "crop movement", "drifting seed", "flies", "low mist"),
        systems=("daily resources", "field restoration", "NPC dialogue", "open-risk travel"),
        deliverables={
            "area": "live",
            "npcs": "live",
            "quests": "live",
            "dialogue": "live",
            "resources": "live",
            "creatures": "live",
            "boss": "planned",
            "graphics": "live",
            "vfx": "live",
            "audio": "planned",
            "persistence": "live",
            "tests": "live",
        },
    ),
    "whisper_marsh": _area(
        "Whisper Marsh",
        2,
        (1, 5),
        "Main Tier 0 wilderness for gathering, hunting, survey work and fishing.",
        ("Greywash channel", "drowned woodland", "reeds", "Whisper Pool"),
        "open_with_warning",
        ("muckford", "low_fields", "drowned_chapel", "greywash_ford"),
        dependencies=("muckford",),
        npcs=("Surveyor Kessa Fenmark", "Brik Sealrunner", "Ferryman Noll"),
        quest_chains=(
            "Develop the Survey Post",
            "Rescue Ferryman Noll",
            "Map Whisper Pool",
            "Build the Tackle Bench",
            "Catch the first marsh fish",
            "Defeat the Whisper Pool Maw",
        ),
        resources=("Bogwort", "River Reed", "Driftwood", "Clay", "Nightcap Fungus", "marsh fish"),
        creatures=(
            "Mud Mite", "Reed Skitter", "Bog Tick", "Spore Toad",
            "Mire-Lurker Spawn", "Drowned Mudling", "Fen Stalker",
            "Rotcap Shambler", "Marshback Brute", "Whisper Moth",
        ),
        boss="Whisper Pool Maw",
        graphics=("procedural water", "marsh props", "generated monsters", "fishing scene"),
        vfx=("currents", "shore foam", "ripples", "spores", "poison", "boss wake"),
        systems=("survey post", "persistent quests", "fishing", "monster ecology"),
        deliverables=dict(MOSTLY_LIVE),
    ),
    "drowned_chapel": _area(
        "Drowned Chapel",
        3,
        (3, 5),
        "Saint Lumen ruin introducing Water-risen, taint exposure and holy field work.",
        ("flooded chapel", "sunken graveyard", "bell tower", "quarantine camp"),
        "open_with_warning",
        ("whisper_marsh",),
        dependencies=("whisper_marsh",),
        npcs=("Sister-Medic Rhea Ashford", "Brother Iven", "Pilgrim Senn", "Pilgrim Orla", "Brother Cal"),
        quest_chains=(
            "Recover the Saint Lumen medicine chest",
            "Rescue three trapped pilgrims",
            "Sample the Vortex-tainted water",
            "Light three holy ward braziers",
            "Silence the drowned bell",
        ),
        resources=("Medicinal Herb", "Grave-Lotus", "Sanctified Wax", "River Clay"),
        creatures=("Water-risen Pilgrim", "Flooded Acolyte", "Bell Wraith", "Drowned Mudling", "Bog Tick", "Whisper Moth"),
        boss="The Bell-Drowned Pilgrim",
        graphics=("flooded chapel", "graveyard", "quarantine camp", "generated enemies"),
        vfx=("bell waves", "holy wards", "water reflections", "taint haze"),
        systems=("rescues", "taint exposure", "quarantine rest", "holy ward progression"),
        deliverables=dict(MOSTLY_LIVE),
    ),
    "old_muckford_mine": _area(
        "Old Muckford Mine",
        4,
        (3, 7),
        "Multi-chamber mining dungeon, crew rescue and industrial restoration.",
        ("mine road", "abandoned galleries", "collapsed rail", "Webbed Depths"),
        "physical_gate",
        ("muckford",),
        dependencies=("muckford",),
        physical_gate="Marda's mine key; debt must be settled and the key collected.",
        npcs=("Marda Shant", "Foreman Torra Flintvein", "Durn Coalhand", "Pell Rook", "Sava Brasspin"),
        quest_chains=(
            "Relight three lantern stations",
            "Rescue the missing miners",
            "Clear three collapse piles",
            "Destroy four egg sacs",
            "Defeat the Cave Broodmother",
            "Restart controlled ore production",
        ),
        resources=("Iron Ore", "Coal", "Stone", "Chipped Ruby", "Silver Ore", "Spider Silk"),
        creatures=("Grave Pickman", "Rail Wraith", "Web Crawler", "Crystal Husk", "Brood Guard"),
        boss="Cave Broodmother",
        graphics=("3800x2400 generated mine", "rails and carts", "lantern network", "collapse piles", "egg sacs", "generated enemies"),
        vfx=("dynamic darkness", "lantern light", "dust", "falling stone", "web bursts"),
        systems=("Marda key gate", "daily ore depletion", "crew rescue", "collapse hazards", "three-phase boss", "daily production"),
        deliverables=dict(MOSTLY_LIVE),
    ),
    "muckford_warrens": _area(
        "Muckford Warrens",
        5,
        (4, 6),
        "Rat-army dungeon and the main local crisis beneath Muckford.",
        ("sewers", "food tunnels", "Vortex-waste nests", "collapsed cellars", "Royal Cistern"),
        "open_with_warning",
        ("muckford", "low_fields"),
        dependencies=("muckford", "low_fields"),
        npcs=(
            "Hamo",
            "Old Rinna Net",
            "Tessa Trapwire",
            "Brin Sootsnare",
            "Dorrik Two-Nails",
        ),
        quest_chains=(
            "Trace four violet-eyed rat trails",
            "Recover four stolen food caches",
            "Destroy four Vortex-waste nests",
            "Rescue three Muckford Ratcatchers",
            "Defeat the Rat King",
            "Report the end of the city crisis",
        ),
        resources=("Rat Tail", "Rotten Flesh", "Vortex Residue", "Scrap Iron", "Recovered Grain"),
        creatures=("Sewer Rat Swarm", "Violet-Eyed Rat", "Rat Rider", "Waste Gnawer"),
        boss="The Rat King of Muckford",
        graphics=(
            "3600x2400 generated sewer and cellar map",
            "three flowing waste channels",
            "bridges and drain culverts",
            "food caches and Vortex nests",
            "generated rat army and Rat King",
        ),
        vfx=("violet eye glow", "waste fumes", "moving sewer current", "Royal Screech", "cistern waste waves", "dynamic darkness"),
        systems=(
            "Muckford cellar hatch",
            "Low Fields drain route",
            "persistent crisis chain",
            "waste exposure",
            "three-phase Rat King",
            "permanent city raid shutdown",
        ),
        deliverables=dict(MOSTLY_LIVE),
    ),
    "greywash_ford": _area(
        "Greywash Ford",
        6,
        (5, 7),
        "Open-risk river crossing from Muckford mud to Crown roads.",
        ("wide river", "three shallow fords", "repairable bridge", "abandoned watchtower", "western causeway"),
        "open_with_warning",
        ("muckford", "whisper_marsh", "kingsreach_toll"),
        dependencies=("whisper_marsh",),
        npcs=("Ferrykeeper Oswin Pike", "Saint Mara Wold", "Hobb Reed", "Captain Garran Vale"),
        quest_chains=(
            "Survey three safe ford lanes",
            "Defeat six Crown deserters",
            "Repair the central bridge",
            "Escort the caravan across five checkpoints",
            "Search the abandoned watchtower",
            "Defeat Captain Garran Vale",
            "Open the Kingsreach road",
        ),
        resources=("River Reed", "Clay", "Driftwood", "Scrap Iron", "Greywash fish"),
        creatures=("Greywash Riverjaw", "Crown Deserter", "Ford Brute"),
        boss="Captain Garran Vale",
        graphics=(
            "3900x2500 generated river crossing",
            "1000-pixel procedural fast river",
            "three ford lanes",
            "broken and repaired bridge states",
            "watchtower and caravan",
            "generated creatures and captain",
        ),
        vfx=("fast current", "shore foam", "ford spray", "rain flood state", "storm flood state", "command shout", "floodgate waves"),
        systems=(
            "Muckford, Whisper Marsh and Kingsreach routes",
            "daily river resources",
            "weather-scaled current hazard",
            "Greywash fishing table",
            "persistent bridge development",
            "five-stage caravan escort",
            "three-phase deserter captain",
            "Kingsreach access handoff",
        ),
        deliverables=dict(MOSTLY_LIVE),
    ),
    "kingsreach_toll": _area(
        "Kingsreach Toll",
        7,
        (6, 8),
        "Crown checkpoint, political preview and formal gate to Tier 1 roads.",
        ("stone causeway", "toll booths", "quarantine tents", "caravan rest"),
        "formal_gate",
        ("greywash_ford",),
        dependencies=("greywash_ford",),
        physical_gate="Greywash Ford must be secured; entry then requires papers, payment, Crown service or a risky smuggler route.",
        npcs=("Crown toll captain", "quarantine medic", "caravan merchants", "smuggler contact"),
        quest_chains=(
            "Present or obtain travel papers",
            "Resolve the quarantine inspection",
            "Choose payment, service or smuggling",
            "Deliver Bram's recommendation",
            "Open the counted Crown road",
        ),
        resources=("Parchment Sheet", "Wax Seal", "Iron Ore", "quarantine medicine"),
        creatures=("road bandits", "toll enforcers", "quarantine escapees"),
        boss="Optional road-bandit leader or corrupt toll enforcer",
        graphics=("Crown stone road", "gatehouse", "inspection booths", "quarantine tents", "caravan yard"),
        vfx=("banner movement", "road dust", "inspection braziers", "seal stamping", "quarantine haze"),
        systems=("papers", "tolls", "reputation choices", "quarantine", "smuggler alternative", "promotion handoff"),
        deliverables={
            "area": "next",
            "npcs": "next",
            "quests": "next",
            "dialogue": "next",
            "resources": "partial",
            "creatures": "partial",
            "boss": "planned",
            "graphics": "next",
            "vfx": "next",
            "audio": "planned",
            "persistence": "next",
            "tests": "next",
        },
    ),
    "tier0_finale": _area(
        "Tier 0 Finale",
        8,
        (5, 6),
        "Tie arena success and Muckford service into an earned promotion.",
        ("Shanty Yard ceremony", "Muckford streets", "western departure"),
        "milestone",
        ("muckford", "kingsreach_toll"),
        dependencies=("muckford_warrens", "greywash_ford"),
        npcs=("Bram Mudhand Carrow", "Sera Quench", "Marda Shant", "Hamo"),
        quest_chains=("Win Rookie Dust", "Resolve a major crisis", "Receive Bram's recommendation"),
        resources=("Tier 1 charter", "sponsor letter", "travel papers"),
        creatures=("promotion rival team",),
        boss="Promotion match or Rat King depending on player path",
        graphics=("promotion ceremony", "crowd", "departure caravan"),
        vfx=("crowd scraps", "torchlight", "league banner"),
        systems=("promotion validation", "branch-aware finale", "Rattlebridge unlock"),
    ),
    "rattlebridge_handoff": _area(
        "Rattlebridge Handoff",
        9,
        (6, 10),
        "End Tier 0 inside the professional Scrapring circuit.",
        ("bridge approach", "city gates", "Scrapring district"),
        "tier1_gate",
        ("kingsreach_toll",),
        dependencies=("tier0_finale", "kingsreach_toll"),
        physical_gate="Formal Arena Tier 1 promotion.",
        npcs=("Sera Quench", "Rattlebridge officials", "Scrapring sponsors"),
        quest_chains=("Register the promoted team", "Find Tier 1 lodging", "Enter the Scrapring"),
        resources=("professional contracts", "Tier 1 gear access"),
        creatures=("bridge raiders",),
        boss="Future Scrapring promotion rival",
        graphics=("Rattlebridge city foundation", "bridge districts", "Scrapring"),
        vfx=("canal water", "industrial smoke", "bridge traffic"),
        systems=("Tier 1 league", "sponsors", "professional economy"),
        deliverables={
            "area": "partial",
            "npcs": "partial",
            "quests": "partial",
            "dialogue": "partial",
            "resources": "partial",
            "creatures": "planned",
            "boss": "planned",
            "graphics": "partial",
            "vfx": "partial",
            "audio": "planned",
            "persistence": "partial",
            "tests": "partial",
        },
    ),
})


DEVELOPMENT_DOMAIN_ORDER = CONTENT_DOMAINS


def completion_ratio(area_id: str) -> float:
    area = TIER0_AREAS[str(area_id)]
    weights = {
        "live": 1.0,
        "partial": 0.5,
        "next": 0.0,
        "planned": 0.0,
        "blocked": 0.0,
    }
    values = [weights[state] for state in area["deliverables"].values()]
    return sum(values) / max(1, len(values))


def dependency_ready(area_id: str) -> bool:
    area = TIER0_AREAS[str(area_id)]
    for dependency in area["dependencies"]:
        if dependency not in TIER0_AREAS:
            return False
        if completion_ratio(dependency) <= 0.0:
            return False
    return True


def next_development_batch(limit: int = 8):
    """Return unfinished domains in explicit priority and area order."""
    priority = {"next": 0, "partial": 1, "planned": 2, "blocked": 3, "live": 9}
    tasks = []
    for area_id, area in TIER0_AREAS.items():
        if not dependency_ready(area_id):
            continue
        for domain_index, domain in enumerate(DEVELOPMENT_DOMAIN_ORDER):
            state = area["deliverables"][domain]
            if state == "live":
                continue
            tasks.append({
                "area_id": area_id,
                "area": area["name"],
                "domain": domain,
                "state": state,
                "order": area["order"],
                "sort": (priority[state], area["order"], domain_index),
            })
    tasks.sort(key=lambda item: item["sort"])
    return [
        {key: value for key, value in task.items() if key != "sort"}
        for task in tasks[:max(0, int(limit))]
    ]


def validate_plan() -> list[str]:
    errors = []
    orders = []
    for area_id, area in TIER0_AREAS.items():
        orders.append(area["order"])
        missing_domains = set(CONTENT_DOMAINS) - set(area["deliverables"])
        if missing_domains:
            errors.append(f"{area_id}: missing domains {sorted(missing_domains)}")
        for domain, state in area["deliverables"].items():
            if state not in VALID_STATES:
                errors.append(f"{area_id}.{domain}: invalid state {state}")
        for dependency in area["dependencies"]:
            if dependency not in TIER0_AREAS:
                errors.append(f"{area_id}: unknown dependency {dependency}")
        if area["access_policy"] in {"physical_gate", "formal_gate", "tier1_gate"} and not area["physical_gate"]:
            errors.append(f"{area_id}: gated area missing description")
        if not area["graphics"]:
            errors.append(f"{area_id}: graphics plan is empty")
        if not area["vfx"]:
            errors.append(f"{area_id}: VFX plan is empty")
    if len(orders) != len(set(orders)):
        errors.append("area development order contains duplicates")

    visiting = set()
    visited = set()

    def visit(area_id):
        if area_id in visiting:
            errors.append(f"dependency cycle at {area_id}")
            return
        if area_id in visited:
            return
        visiting.add(area_id)
        for dependency in TIER0_AREAS[area_id]["dependencies"]:
            visit(dependency)
        visiting.remove(area_id)
        visited.add(area_id)

    for area_id in TIER0_AREAS:
        visit(area_id)
    return errors
