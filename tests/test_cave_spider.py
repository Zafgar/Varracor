# tests/test_cave_spider.py
"""
Testit Cave Broodmother -bossille, Spiderlingeille, Web-hidastukselle ja
kaivosluolan syvän kammion portille (verkkoseinä + hopeasuoni).
"""
import pytest
from settings import PLAYER_TEAM, ENEMY_TEAM


def _broodmother():
    from units.cave_spider import CaveBroodmother
    return CaveBroodmother("Cave Broodmother", 0, 0)


def test_broodmother_boss_stats():
    b = _broodmother()
    assert b.is_boss is True
    assert b.max_hp == 750
    assert b.current_hp == 750
    assert getattr(b.ai_controller, "no_retreat", False) is True


def test_spider_race_weak_to_fire():
    from races import RACES
    assert "Spider" in RACES
    assert RACES["Spider"]["weakness"] == "Fire"


def test_spiderling_is_weak_and_fast():
    from units.cave_spider import Spiderling
    s = Spiderling("Spiderling", 0, 0)
    assert s.max_hp == 40
    assert s.speed > 1.0
    assert getattr(s, "is_boss", False) is False


def test_broodmother_spawns_brood_below_half(manager):
    b = _broodmother()
    manager.current_arena = None
    manager.enemy_team.add(b)
    manager.all_units.add(b)
    # Anna kohde, jotta run_combat_ai etenee
    from units.human import Human
    hero = Human("Hero", 200, 0, PLAYER_TEAM)
    b.ai_controller.current_target = hero
    # Pudota HP alle puolen ja aja combat-ai
    b.current_hp = int(b.max_hp * 0.4)
    before = len([u for u in manager.enemy_team])
    b.run_combat_ai(manager.all_units, None, manager=manager)
    assert b.brood_spawned is True
    after = len([u for u in manager.enemy_team])
    assert after > before, "Broodmotherin pitäisi kutsua Spiderlingejä"


def test_enemy_factory_creates_spiders(manager):
    from units.cave_spider import CaveBroodmother, Spiderling
    assert isinstance(manager.create_enemy_by_name("Cave Broodmother"), CaveBroodmother)
    assert isinstance(manager.create_enemy_by_name("Spiderling"), Spiderling)


def test_spider_loot_keys(manager):
    from loot_data import LOOT_DROPS
    b = _broodmother()
    assert manager._loot_key_for(b) == "Cave Broodmother"
    assert "Cave Broodmother" in LOOT_DROPS
    from units.cave_spider import Spiderling
    ling = Spiderling("Spiderling 2", 0, 0)
    assert manager._loot_key_for(ling) == "Spiderling"


def test_web_status_slows_movement():
    """Webbed-yksikkö etenee vähemmän kuin vapaa yksikkö samassa ajassa."""
    from game_manager import GameManager
    from units.human import Human

    def walk_distance(webbed):
        m = GameManager()
        hero = Human("Runner", 100, 500, PLAYER_TEAM)
        target = Human("Target", 1600, 500, ENEMY_TEAM)
        m.match_in_progress = True
        m.current_arena = None
        m.my_team.add(hero)
        m.enemy_team.add(target)
        m.all_units.add(hero, target)
        start = hero.rect.centerx
        for _ in range(90):
            if webbed and not any(e.get("type") == "Web" for e in hero.status_effects):
                hero.apply_status("Web", 30, 0)
            hero.run_combat_ai(m.all_units, None, manager=m)
            hero.update(None, manager=m)
        return hero.rect.centerx - start

    free = walk_distance(False)
    webbed = walk_distance(True)
    assert free > 0, "Vapaan pitäisi liikkua kohti kohdetta"
    assert webbed < free, f"Webbed ({webbed}) pitäisi liikkua vähemmän kuin vapaa ({free})"


def test_web_cleansed_by_dwarf_stoneform():
    from gladiator import Gladiator
    d = Gladiator("Stonebeard", "Dwarf", 0, 0, PLAYER_TEAM)
    d.racial_cooldown = 0
    d.apply_status("Web", 150, 0)
    assert any(e.get("type") == "Web" for e in d.status_effects)
    activated = d.use_racial_ability(manager=None)
    assert activated is True
    assert not any(e.get("type") == "Web" for e in d.status_effects), \
        "Dwarfin Stoneformin pitäisi puhdistaa Web"


def test_mine_web_barrier_and_deep_ores():
    from citys.mucford.mine_cave_arena import MineCaveArena, SilverVein
    arena = MineCaveArena()
    # Verkkoseinä lisää esteen
    obstacles_before = len(arena.obstacles)
    arena.add_web_barrier()
    assert arena.web_barrier is not None
    assert len(arena.obstacles) == obstacles_before + 1
    # Poisto ottaa esteen pois
    arena.remove_web_barrier()
    assert arena.web_barrier is None
    assert len(arena.obstacles) == obstacles_before
    # Syvät malmit sisältävät hopeasuonen
    nodes_before = len(arena.ore_nodes)
    arena.spawn_deep_ores()
    assert len(arena.ore_nodes) > nodes_before
    assert any(isinstance(n, SilverVein) for n in arena.ore_nodes)
    # Toistokutsu ei tuplaa
    count = len(arena.ore_nodes)
    arena.spawn_deep_ores()
    assert len(arena.ore_nodes) == count
