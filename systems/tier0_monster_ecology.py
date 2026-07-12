"""Spawn tables, habitat rules and loot for Muckford's level 1-5 fauna."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from settings import ENEMY_TEAM
from units.tier0_monsters import TIER0_MONSTER_BY_SPECIES


@dataclass(frozen=True)
class MonsterEcologyEntry:
    species: str
    level: int
    habitats: Tuple[str, ...]
    weight: int
    group_size: Tuple[int, int]
    summary: str


TIER0_ECOLOGY: Tuple[MonsterEcologyEntry, ...] = (
    MonsterEcologyEntry(
        "Mud Mite", 1, ("mud", "bank", "woodland"), 18, (2, 5),
        "Small scavenger that gains speed when several mites surround prey.",
    ),
    MonsterEcologyEntry(
        "Reed Skitter", 1, ("bank", "reeds", "pool"), 15, (2, 4),
        "Side-stepping marsh crab that clips ankles and slows movement.",
    ),
    MonsterEcologyEntry(
        "Bog Tick", 2, ("mud", "woodland", "ruins"), 11, (1, 3),
        "Buried parasite that drains stamina and heals from its first bite.",
    ),
    MonsterEcologyEntry(
        "Spore Toad", 2, ("pool", "reeds", "fungus"), 12, (1, 3),
        "Toxic toad whose panic response releases a slowing poison cloud.",
    ),
    MonsterEcologyEntry(
        "Mire-Lurker Spawn", 3, ("bank", "pool", "deep_marsh"), 10, (1, 3),
        "Young frog-lizard predator that pounces across broken ground.",
    ),
    MonsterEcologyEntry(
        "Drowned Mudling", 3, ("ruins", "deep_marsh", "mud"), 9, (1, 3),
        "Water-risen humanoid mass that pins victims in clinging silt.",
    ),
    MonsterEcologyEntry(
        "Fen Stalker", 4, ("woodland", "deep_marsh", "reeds"), 6, (1, 2),
        "Camouflaged predator that waits motionless before an ambush lunge.",
    ),
    MonsterEcologyEntry(
        "Rotcap Shambler", 4, ("fungus", "woodland", "ruins"), 6, (1, 2),
        "Walking fungal colony that controls space with recurring spore bursts.",
    ),
    MonsterEcologyEntry(
        "Marshback Brute", 5, ("deep_marsh", "pool", "bank"), 3, (1, 1),
        "Armoured swamp beast that commits to a long, damaging charge.",
    ),
    MonsterEcologyEntry(
        "Whisper Moth", 5, ("pool", "fungus", "deep_marsh"), 3, (1, 2),
        "Large nocturnal moth that spits poison dust and retreats from melee.",
    ),
)

ECOLOGY_BY_SPECIES: Dict[str, MonsterEcologyEntry] = {
    entry.species: entry for entry in TIER0_ECOLOGY
}

TIER0_LOOT_DROPS = {
    "Mud Mite": [
        {"item": "Chitin Fleck", "chance": 0.65, "min": 1, "max": 2},
        {"item": "Mud Gland", "chance": 0.18, "min": 1, "max": 1},
    ],
    "Reed Skitter": [
        {"item": "Claw Fragment", "chance": 0.55, "min": 1, "max": 2},
        {"item": "River Reed", "chance": 0.35, "min": 1, "max": 2},
    ],
    "Bog Tick": [
        {"item": "Coagulated Ichor", "chance": 0.65, "min": 1, "max": 2},
        {"item": "Tick Carapace", "chance": 0.30, "min": 1, "max": 1},
    ],
    "Spore Toad": [
        {"item": "Toadskin", "chance": 0.60, "min": 1, "max": 2},
        {"item": "Nightcap Fungus", "chance": 0.45, "min": 1, "max": 2},
    ],
    "Mire-Lurker Spawn": [
        {"item": "Mire Hide", "chance": 0.75, "min": 1, "max": 2},
        {"item": "Venom Gland", "chance": 0.25, "min": 1, "max": 1},
    ],
    "Drowned Mudling": [
        {"item": "Silt Core", "chance": 0.55, "min": 1, "max": 1},
        {"item": "Rotten Flesh", "chance": 0.55, "min": 1, "max": 2},
    ],
    "Fen Stalker": [
        {"item": "Fen Hide", "chance": 0.85, "min": 1, "max": 2},
        {"item": "Predator Fang", "chance": 0.45, "min": 1, "max": 2},
    ],
    "Rotcap Shambler": [
        {"item": "Spore Sac", "chance": 0.80, "min": 1, "max": 2},
        {"item": "Nightcap Fungus", "chance": 0.70, "min": 1, "max": 3},
    ],
    "Marshback Brute": [
        {"item": "Marshback Plate", "chance": 1.0, "min": 1, "max": 2},
        {"item": "Thick Hide", "chance": 0.75, "min": 1, "max": 2},
    ],
    "Whisper Moth": [
        {"item": "Whisper Dust", "chance": 1.0, "min": 1, "max": 3},
        {"item": "Moth Wing", "chance": 0.65, "min": 1, "max": 2},
    ],
}


def ecology_entries(
    *,
    min_level: int = 1,
    max_level: int = 5,
    habitat: Optional[str] = None,
) -> List[MonsterEcologyEntry]:
    result = []
    for entry in TIER0_ECOLOGY:
        if not min_level <= entry.level <= max_level:
            continue
        if habitat and habitat not in entry.habitats:
            continue
        result.append(entry)
    return result


def choose_species(
    rng: random.Random,
    *,
    min_level: int = 1,
    max_level: int = 5,
    habitat: Optional[str] = None,
) -> MonsterEcologyEntry:
    candidates = ecology_entries(
        min_level=min_level,
        max_level=max_level,
        habitat=habitat,
    )
    if not candidates and habitat:
        candidates = ecology_entries(min_level=min_level, max_level=max_level)
    if not candidates:
        raise ValueError(f"No Tier 0 monsters for levels {min_level}-{max_level}")
    weights = [max(1, entry.weight) for entry in candidates]
    return rng.choices(candidates, weights=weights, k=1)[0]


def create_monster(
    species: str,
    x: int,
    y: int,
    team_color=ENEMY_TEAM,
    *,
    name: Optional[str] = None,
):
    monster_class = TIER0_MONSTER_BY_SPECIES.get(species)
    if monster_class is None:
        raise KeyError(f"Unknown Tier 0 monster: {species}")
    display_name = name or species
    return monster_class(display_name, int(x), int(y), team_color)


def spawn_group(
    species: str,
    center: Sequence[int],
    rng: random.Random,
    team_color=ENEMY_TEAM,
    *,
    count: Optional[int] = None,
    spread: int = 70,
) -> List[object]:
    entry = ECOLOGY_BY_SPECIES[species]
    amount = int(count) if count is not None else rng.randint(*entry.group_size)
    result = []
    for index in range(max(1, amount)):
        x = int(center[0]) + rng.randint(-spread, spread)
        y = int(center[1]) + rng.randint(-spread, spread)
        result.append(
            create_monster(
                species,
                x,
                y,
                team_color,
                name=f"{species} {index + 1}" if amount > 1 else species,
            )
        )
    return result


def _land_point_in_zone(arena, rng: random.Random, zone: str) -> Tuple[int, int]:
    zones = {
        "near": (180, 1380, 350, arena.height - 180),
        "middle": (2300, 2760, 260, arena.height - 180),
        "deep": (2780, arena.width - 160, 520, arena.height - 160),
    }
    left, right, top, bottom = zones[zone]
    for _ in range(500):
        x = rng.randint(left, right)
        y = rng.randint(top, bottom)
        if any(water.contains_point((x, y), inset=-25) for water in arena.waters):
            continue
        if any(
            getattr(obstacle, "rect", None)
            and obstacle.rect.inflate(30, 30).collidepoint(x, y)
            for obstacle in arena.land_obstacles
        ):
            continue
        return x, y
    return arena.random_land_point(180)


def build_whisper_marsh_population(
    arena,
    rng: random.Random,
    team_color=ENEMY_TEAM,
    *,
    visits: int = 1,
    camp_stage: int = 0,
) -> List[object]:
    """Create a difficulty-gradient population instead of global random soup.

    Level 1-2 creatures live west of the Greywash, level 2-4 creatures occupy
    the far bank, and level 4-5 predators remain around Whisper Pool. BaseAI is
    paired with a local aggro radius, so deep threats do not cross the entire
    map to attack a new player at the entrance.
    """
    population: List[object] = []

    near_groups = 3 + min(1, visits // 4)
    for _ in range(near_groups):
        entry = choose_species(rng, min_level=1, max_level=2, habitat=rng.choice(("mud", "bank", "reeds")))
        population.extend(
            spawn_group(entry.species, _land_point_in_zone(arena, rng, "near"), rng, team_color)
        )

    middle_cap = min(4, 3 + max(0, visits - 1) // 3)
    for _ in range(3):
        entry = choose_species(rng, min_level=2, max_level=middle_cap, habitat=rng.choice(("woodland", "deep_marsh", "ruins")))
        population.extend(
            spawn_group(entry.species, _land_point_in_zone(arena, rng, "middle"), rng, team_color)
        )

    # Deep predators are present from the start, but isolated behind exploration
    # distance and the Greywash crossings. Camp progress increases their variety.
    deep_min = 4 if camp_stage < 2 else 3
    deep_groups = 2 if camp_stage < 3 else 3
    for _ in range(deep_groups):
        entry = choose_species(rng, min_level=deep_min, max_level=5, habitat=rng.choice(("pool", "fungus", "deep_marsh")))
        population.extend(
            spawn_group(entry.species, _land_point_in_zone(arena, rng, "deep"), rng, team_color)
        )

    return population
