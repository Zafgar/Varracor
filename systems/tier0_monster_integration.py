"""Runtime integration for Muckford's level 1-5 monster ecology."""
from __future__ import annotations

import random

from settings import ENEMY_TEAM
from systems.tier0_monster_ecology import (
    TIER0_ECOLOGY,
    TIER0_LOOT_DROPS,
    build_whisper_marsh_population,
    create_monster,
)


_INSTALLED = False


def _patch_loot_tables() -> None:
    from loot_data import LOOT_DROPS

    LOOT_DROPS.update(TIER0_LOOT_DROPS)


def _patch_world_map_threats() -> None:
    from lore.world_map_data import LOCATIONS

    location = LOCATIONS.get("whisper_marsh")
    if not location:
        return
    location["threats"] = (
        "Mud Mites and Reed Skitters",
        "Bog Ticks and Spore Toads",
        "Mire-Lurker Spawn and Drowned Mudlings",
        "Fen Stalkers and Rotcap Shamblers",
        "Marshback Brutes and Whisper Moths",
    )


def _patch_game_manager() -> None:
    from game_manager import GameManager

    if getattr(GameManager, "_tier0_monsters_installed", False):
        return
    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self.tier0_monster_catalog = tuple(TIER0_ECOLOGY)

    def create_tier0_monster(self, species, x, y, team_color=ENEMY_TEAM, name=None):
        return create_monster(
            species,
            x,
            y,
            team_color,
            name=name,
        )

    GameManager.__init__ = __init__
    GameManager.create_tier0_monster = create_tier0_monster
    GameManager._tier0_monsters_installed = True


def _patch_whisper_marsh_population() -> None:
    from citys.mucford.forest_excursion import ForestExcursionMenu, outskirts_state

    if getattr(ForestExcursionMenu, "_tier0_monsters_installed", False):
        return
    previous_enter = ForestExcursionMenu.on_enter

    def on_enter(self):
        result = previous_enter(self)

        # Replace only the generic baseline rats/crows. Event-specific Flood Rats,
        # the Greywash Troll and any future named encounter remain intact.
        for monster in list(self.monsters):
            name = str(getattr(monster, "name", ""))
            if name.startswith("Marsh Rat ") or name.startswith("Drowned Crow "):
                self.monsters.remove(monster)

        state = outskirts_state(self.manager)
        seed = random.randrange(1, 2**31 - 1)
        rng = random.Random(seed)
        population = build_whisper_marsh_population(
            self.arena,
            rng,
            ENEMY_TEAM,
            visits=int(state.get("visits", 1)),
            camp_stage=int(state.get("camp_stage", 0)),
        )
        for monster in population:
            self.monsters.add(monster)

        self.ecology_seed = seed
        self.ecology_population = population
        return result

    ForestExcursionMenu.on_enter = on_enter
    ForestExcursionMenu._tier0_monsters_installed = True


def install_tier0_monster_integration() -> None:
    global _INSTALLED
    _patch_loot_tables()
    _patch_world_map_threats()
    if _INSTALLED:
        return
    _patch_game_manager()
    _patch_whisper_marsh_population()
    _INSTALLED = True


# Pure registries are safe to expose immediately for imports, tests and tools.
_patch_loot_tables()
_patch_world_map_threats()
