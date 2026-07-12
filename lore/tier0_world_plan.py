"""Canonical development plan for the playable Tier 0 world around Muckford.

This file is the source of truth for both future development sessions and tests.
It is intentionally structured data instead of prose only: every area records
its player-access policy, content dependencies, NPCs, quests, resources,
creatures, graphics, VFX and implementation state.

Rules:
* Development order is not player lock order. Most Tier 0 areas are open once
  their road is discovered; recommended level is a danger warning only.
* Only explicit physical/story obstacles may block travel (for example Marda's
  mine key or formal promotion through Kingsreach Toll).
* A work batch is complete only after persistence and automated tests exist.
* Every content implementation must update this file and the progress log.
"""
from __future__ import annotations

from collections import OrderedDict


PLAN_VERSION = 1
CURRENT_FOCUS = "low_fields"

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
        "name": name,
        "order": int(order),
        "level_range": tuple(level_range),
        "purpose": purpose,
        "environment": tuple(environment),
        "access_policy": access_policy,
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


TIER0_AREAS = OrderedDict({
    "muckford": _area(
        "Muckford",
        0,
        (1, 5),
        "Tier 0 hub, team registration, farming, crafting and arena management.",
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
        ),
        resources=("Scrap Iron", "Coal", "Bitterleaf", "farm produce"),
        creatures=("Rat raids",),
        boss="The Rat King of Muckford (city crisis finale)",
        graphics=("city props", "farms", "arena gate", "NPC placeholders"),
        vfx=("rain", "mud", "smeltery", "raid warnings"),
        systems=("economy", "registration", "farming", "barracks", "league"),
        deliverables={domain: "live" for domain in CONTENT_DOMAINS},
    ),
    "low_fields": _area(
        "Muckford Low Fields",
        1,
        (1, 3),
        "Safe first exterior zone for work, gathering and visible town recovery.",
        ("wet fields", "irrigation ditches", "animal pens", "willow hedges"),
        "open_with_warning",
        ("muckford",),
        dependencies=("muckford",),
        npcs=(
            "Farmer Gus",
            "field workers",
            "Saint Lumen supply runner",
        ),
        quest_chains=(
            "Mend the irrigation channels",
            "Protect the grain carts",
            "Close the mite burrows",
            "Rebuild the field footbridge",
        ),
        resources=(
            "Carrot",
            "Potato",
            "Onion",
            "River Reed",
            "Clay",
            "Softwood",
        ),
        creatures=("Mud Mite", "Reed Skitter", "Marsh Rat"),
        boss="The Burrow-Mother (optional level 3 field event)",
        graphics=(
            "procedural crop fields",
            "ditches and fences",
            "animal shelters",
            "work carts",
        ),
        vfx=("ditch water", "mud splashes", "crop movement", "dust and flies"),
        systems=("field development", "NPC work", "resource deliveries"),
        deliverables={
            "area": "next",
            "npcs": "partial",
            "quests": "next",
            "dialogue": "next",
            "resources": "partial",
            "creatures": "live",
            "boss": "planned",
            "graphics": "next",
            "vfx": "next",
            "audio": "planned",
            "persistence": "next",
            "tests": "next",
        },
    ),
    "whisper_marsh": _area(
        "Whisper Marsh",
        2,
        (1, 5),
        "Main Tier 0 wilderness for gathering, hunting, exploration and fishing.",
        ("Greywash channel", "drowned woodland", "reeds", "Whisper Pool"),
        "open_with_warning",
        ("muckford", "low_fields"),
        dependencies=("muckford",),
        npcs=("lost ferryman", "survey-post workers", "Hamo field contact"),
        quest_chains=(
            "Develop the Survey Post",
            "Find the lost ferryman",
            "Map the Whisper Pool",
            "Prepare the first fishing tackle bench",
        ),
        resources=("Bogwort", "River Reed", "Driftwood", "Clay", "Nightcap Fungus"),
        creatures=(
            "Mud Mite",
            "Reed Skitter",
            "Bog Tick",
            "Spore Toad",
            "Mire-Lurker Spawn",
            "Drowned Mudling",
            "Fen Stalker",
            "Rotcap Shambler",
            "Marshback Brute",
            "Whisper Moth",
        ),
        boss="Greywash Troll / future Whisper Pool boss",
        graphics=("procedural water", "marsh props", "code-rendered monsters"),
        vfx=("currents", "shore foam", "rain ripples", "spores", "poison"),
        systems=("survey-post development", "monster ecology", "fishing foundation"),
        deliverables={
            "area": "live",
            "npcs": "planned",
            "quests": "partial",
            "dialogue": "planned",
            "resources": "live",
            "creatures": "live",
            "boss": "partial",
            "graphics": "live",
            "vfx": "live",
            "audio": "planned",
            "persistence": "live",
            "tests": "live",
        },
    ),
    "drowned_chapel": _area(
        "Drowned Chapel",
        3,
        (3, 5),
        "Saint Lumen ruin that introduces Water-risen, disease and holy field work.",
        ("flooded chapel", "sunken graveyard", "bell tower", "quarantine camp"),
        "open_with_warning",
        ("whisper_marsh",),
        dependencies=("whisper_marsh",),
        npcs=("Sister-Medic Rhea Ashford", "quarantine volunteers", "rescued pilgrims"),
        quest_chains=(
            "Recover the hospice medicine chest",
            "Rescue the trapped pilgrims",
            "Identify the Vortex-tainted water source",
            "Silence the drowned bell",
        ),
        resources=("Medicinal Herb", "Grave-Lotus", "Sanctified Wax", "River Clay"),
        creatures=("Water-risen", "Drowned Mudling", "Bog Tick", "Whisper Moth"),
        boss="The Bell-Drowned Pilgrim",
        graphics=("flooded chapel shell", "grave markers", "holy medical camp"),
        vfx=("bell shockwaves", "holy light", "water reflections", "disease haze"),
        systems=("rescue objectives", "water-level hazards", "quarantine reputation"),
    ),
    "old_muckford_mine": _area(
        "Old Muckford Mine",
        4,
        (3, 7),
        "Mining dungeon, undead investigation and first persistent industrial recovery.",
        ("mine road", "abandoned galleries", "webbed depths", "collapsed rail"),
        "physical_gate",
        ("muckford",),
        dependencies=("muckford",),
        physical_gate="Marda's mine key; debt must be settled and the key collected.",
        npcs=("Marda Shant", "surviving miners", "mine foreman role"),
        quest_chains=(
            "Open the old mine road",
            "Restore lantern stations",
            "Rescue missing miners",
            "Clear the Webbed Depths",
            "Restart controlled ore production",
        ),
        resources=("Iron Ore", "Coal", "Chipped Ruby", "Stone", "Spider Silk"),
        creatures=("Skeletons", "Zombies", "Spiderlings", "Bog Tick"),
        boss="Cave Broodmother",
        graphics=("mine road", "galleries", "rails", "webbed boss chamber"),
        vfx=("dust", "falling stones", "web strands", "lantern light"),
        systems=("mining", "mine development", "light and collapse hazards"),
        deliverables={
            "area": "partial",
            "npcs": "planned",
            "quests": "partial",
            "dialogue": "partial",
            "resources": "live",
            "creatures": "partial",
            "boss": "partial",
            "graphics": "partial",
            "vfx": "partial",
            "audio": "planned",
            "persistence": "partial",
            "tests": "partial",
        },
    ),
    "muckford_warrens": _area(
        "Muckford Warrens",
        5,
        (4, 6),
        "Rat-army dungeon and local story climax beneath Muckford.",
        ("sewers", "food tunnels", "Vortex-waste nests", "collapsed cellars"),
        "open_with_warning",
        ("muckford", "low_fields"),
        dependencies=("muckford", "low_fields"),
        npcs=("Hamo", "Old Rinna Net", "Muckford Ratcatchers"),
        quest_chains=(
            "Trace the violet-eyed rats",
            "Recover stolen food stores",
            "Destroy Vortex-waste nests",
            "Find the Ratcatchers",
            "Hunt the Rat King",
        ),
        resources=("Rat Tail", "Rotten Flesh", "Vortex Residue", "Scrap Iron"),
        creatures=("Rat swarms", "Violet-Eyed Rats", "Rat Riders", "Drowned Mudling"),
        boss="The Rat King of Muckford",
        graphics=("sewer tiles", "burrows", "food caches", "Vortex nests"),
        vfx=("violet eye glow", "waste fumes", "swarm dust", "sewer water"),
        systems=("swarm encounters", "nest destruction", "city raid reduction"),
    ),
    "greywash_ford": _area(
        "Greywash Ford",
        6,
        (5, 7),
        "Open-risk river crossing and physical transition from mud tracks to Crown roads.",
        ("wide river", "shallow ford", "broken bridge", "abandoned watchtower"),
        "open_with_warning",
        ("muckford", "whisper_marsh"),
        dependencies=("whisper_marsh",),
        npcs=("Shanty Yard Saints patrol", "ferrykeeper role", "Crown deserters"),
        quest_chains=(
            "Secure the ford",
            "Repair or replace the crossing",
            "Escort a Muckford caravan",
            "Investigate the abandoned watchtower",
        ),
        resources=("River Reed", "Clay", "Driftwood", "Scrap Iron", "fish"),
        creatures=("river predators", "Marshback Brute", "bandits", "deserters"),
        boss="Gutter Overflow / deserter captain encounter",
        graphics=("procedural river", "ford stones", "bridge", "watchtower"),
        vfx=("fast current", "ford splashes", "foam", "rain flood state"),
        systems=("crossing choices", "caravan escort", "fishing", "bridge development"),
        deliverables={
            "area": "planned",
            "npcs": "planned",
            "quests": "planned",
            "dialogue": "planned",
            "resources": "partial",
            "creatures": "partial",
            "boss": "planned",
            "graphics": "partial",
            "vfx": "partial",
            "audio": "planned",
            "persistence": "planned",
            "tests": "planned",
        },
    ),
    "kingsreach_toll": _area(
        "Kingsreach Toll",
        7,
        (6, 8),
        "Crown checkpoint, political preview and formal gate to the Tier 1 road.",
        ("stone causeway", "toll booths", "quarantine tents", "caravan rest"),
        "formal_gate",
        ("greywash_ford",),
        dependencies=("greywash_ford",),
        physical_gate="Tier 0 recommendation, travel papers or a costly alternative route.",
        npcs=("Crown toll captain role", "quarantine medic role", "caravan merchants"),
        quest_chains=(
            "Obtain valid travel papers",
            "Resolve the quarantine inspection",
            "Choose toll, service or smuggler route",
            "Deliver Bram's recommendation",
        ),
        resources=("Parchment Sheet", "Wax Seal", "Iron Ore"),
        creatures=("road bandits", "toll enforcers", "quarantine escapees"),
        boss="Optional road-bandit leader",
        graphics=("Crown stone road", "gatehouse", "tents", "caravan yard"),
        vfx=("banner movement", "road dust", "inspection braziers"),
        systems=("papers", "tolls", "reputation choices", "promotion handoff"),
    ),
    "tier0_finale": _area(
        "Tier 0 Finale",
        8,
        (5, 6),
        "Tie arena success and Muckford field service into one earned promotion.",
        ("Shanty Yard ceremony", "Muckford streets", "western departure"),
        "milestone",
        ("muckford", "kingsreach_toll"),
        dependencies=("muckford_warrens", "greywash_ford"),
        npcs=("Bram Mudhand Carrow", "Sera Quench", "Marda Shant", "Hamo"),
        quest_chains=(
            "Win the Rookie Dust Circuit",
            "Resolve a major Muckford crisis",
            "Receive Bram's recommendation",
            "Meet Sera Quench's scout",
        ),
        resources=("Tier 1 charter", "sponsor letter", "travel papers"),
        creatures=(),
        boss="Arena promotion match or Rat King, depending on player path",
        graphics=("promotion ceremony", "crowd", "departure caravan"),
        vfx=("crowd confetti scraps", "torchlight", "league banner"),
        systems=("promotion validation", "branch-aware finale", "Rattlebridge unlock"),
    ),
    "rattlebridge_handoff": _area(
        "Rattlebridge Handoff",
        9,
        (6, 10),
        "End Tier 0 and place the team inside the professional Scrapring circuit.",
        ("bridge approach", "city gates", "Scrapring district"),
        "tier1_gate",
        ("kingsreach_toll",),
        dependencies=("tier0_finale", "kingsreach_toll"),
        physical_gate="Formal Arena Tier 1 promotion.",
        npcs=("Sera Quench", "Rattlebridge officials", "Scrapring sponsors"),
        quest_chains=("Register the promoted team", "Find Tier 1 lodging", "Enter the Scrapring"),
        resources=("professional contracts", "Tier 1 gear access"),
        creatures=("bridge raiders",),
        boss=None,
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
    weights = {"live": 1.0, "partial": 0.5, "next": 0.0, "planned": 0.0, "blocked": 0.0}
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
    """Return the next ordered implementation tasks.

    ``next`` states are emitted before ``planned`` states. Existing ``partial``
    work is also returned so it can be finished rather than silently forgotten.
    """
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
    return [{key: value for key, value in task.items() if key != "sort"}
            for task in tasks[:max(0, int(limit))]]


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
        if area["access_policy"] == "physical_gate" and not area["physical_gate"]:
            errors.append(f"{area_id}: physical gate missing description")
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
