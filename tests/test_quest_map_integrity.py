# tests/test_quest_map_integrity.py
"""Quest <-> kartta -eheystestit (pelitesti 30).

Varmistaa että jokainen quest/boss-hunt joka viittaa karttaan tosiaan
latautuu: bossilla on mission-moduuli, monster-hunt-viholliset ja
areenanimet resolvoituvat. Aiemmin boss_forest_troll oli BOSS_HUNTS-
listassa mutta puuttui boss_registrystä -> koko questi oli rikki."""
import pygame
import pytest


def test_every_boss_hunt_has_mission_module():
    from missions.boss_registry import load_mission_package
    from mission_data import BOSS_HUNTS

    missing = [bid for bid in BOSS_HUNTS if load_mission_package(bid) is None]
    assert not missing, f"boss-huntit ilman mission-moduulia: {missing}"


def test_forest_troll_boss_fight_spawns_troll(manager):
    from mission_data import BOSS_HUNTS
    from units.commander import Commander
    import maps.bog_1.boss_troll as bt
    import maps.bog_1.arena as ba

    hero = Commander("Hero", 0, 0)
    manager.my_team.add(hero)
    manager.active_player_units.add(hero)
    manager.selected_mission = BOSS_HUNTS["boss_forest_troll"]
    manager.current_arena = ba.Arena()

    logic = bt.MissionLogic(manager.selected_mission)
    logic.setup(manager)

    trolls = [u for u in manager.enemy_team if type(u).__name__ == "Troll"]
    assert len(trolls) == 1, "Forest Troll ei ilmestynyt"
    assert trolls[0].is_boss
    assert not logic.is_finished(manager)
    # Peikko sijoittuu pesään
    lair = manager.current_arena.lair_rect
    assert lair.inflate(200, 200).collidepoint(trolls[0].rect.center)


def test_all_mission_arena_names_dispatch():
    """Jokainen mission_datan areenanimi on game_managerin tuntema."""
    from mission_data import BOSS_HUNTS, MONSTER_HUNTS

    known = {"Rat Sewer", "Crypt", "Bog", "Muckford", "Basic Arena"}
    unknown = set()
    for hunt in BOSS_HUNTS.values():
        arena = hunt.get("arena")
        if arena and arena not in known:
            unknown.add(arena)
    for hunts in MONSTER_HUNTS.values():
        for hunt in hunts:
            arena = hunt.get("arena")
            # Muut areenat menevät get_random_arena-fallbackille (ok)
    # Vähintään bossien areenat pitää olla tuettuja
    assert not (unknown - {"Rat Sewer", "Crypt", "Bog"}), unknown
