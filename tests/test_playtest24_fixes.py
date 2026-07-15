# tests/test_playtest24_fixes.py
"""Pelitestikierros 24: Muckford Warrens = eeppinen reitti Rat Kingille.
1) Uusi HulkRat-hirviö kuhisemaan tunneleihin
2) Sulkuluku-vivut antavat Rusted Sluice Cog -rattaita
3) Cistern Gate Crank taotaan sepällä (avainesine reppuun, ei bagiin)
4) Royal Cistern -portti aukeaa vain kammella; avaus herättää bossin
   eeppisellä introdialogilla
5) Bossin kaato -> warrens-vaihe 6 + hunt_01 valmis
6) Retkikunnan voi tuoda barracksista mukaan warrensiin
7) Griznak aloittaa ja seuraa Warrens-kriisilinjaa (world_events)
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from settings import PLAYER_TEAM, ENEMY_TEAM


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def _warrens_at_stage5(m):
    """Warrens-tila vaiheeseen 5 (ratcatcherit pelastettu)."""
    from citys.mucford.muckford_warrens import warrens_state
    st = warrens_state(m)
    st.update(
        quest_stage=5,
        traced_signs=["t1", "t2", "t3", "t4"],
        recovered_caches=["c1", "c2", "c3", "c4"],
        destroyed_nests=["n1", "n2", "n3", "n4"],
        rescued_ratcatchers=["r1", "r2", "r3"],
    )
    return st


# ----------------------------------------------------------------------
# 1) Brute Rat (iso rotta) - pelitesti 25: oikea rottayksikkö
# ----------------------------------------------------------------------

def test_brute_rat_stats_and_sprite():
    from units.rat import BruteRat, GiantRat
    brute = BruteRat("Brute", 0, 0, ENEMY_TEAM)
    giant = GiantRat("G", 0, 0, ENEMY_TEAM)
    assert brute.max_hp > giant.max_hp * 3, "brute on selvästi tukevampi"
    assert brute.image is not None


def test_brute_rats_spawn_in_warrens():
    from citys.mucford.muckford_warrens import MuckfordWarrensMenu
    from units.rat import BruteRat
    m = _manager()
    menu = MuckfordWarrensMenu(m)
    menu.on_enter()
    brutes = [mo for mo in menu.monsters if isinstance(mo, BruteRat)]
    assert len(brutes) >= 3, "tunnelit kuhisevat isoja rottia"


# ----------------------------------------------------------------------
# 2-3) Vivut + kampi
# ----------------------------------------------------------------------

def test_levers_give_cogs():
    from citys.mucford.muckford_warrens import MuckfordWarrensMenu, warrens_state
    m = _manager()
    menu = MuckfordWarrensMenu(m)
    menu.on_enter()
    assert len(menu.arena.sluice_levers) == 2
    for lever in menu.arena.sluice_levers:
        m.player_character.rect.center = lever.rect.center
        assert menu._try_lever()
    assert m.inventory.get("Rusted Sluice Cog", 0) == 4
    st = warrens_state(m)
    assert len(set(st["pulled_levers"])) == 2


def test_cistern_gate_crank_crafts_to_inventory():
    m = _manager()
    m.gold = 500
    m.inventory["Iron Ingot"] = 5   # "Iron Bar" kanonisoituu Iron Ingotiksi
    m.inventory["Rusted Sluice Cog"] = 3
    assert m.craft_item("Cistern Gate Crank", None) is True
    assert m.inventory.get("Cistern Gate Crank", 0) == 1, "kampi reppuun"
    assert all(getattr(it, "name", "") != "Cistern Gate Crank"
               for it in m.equipment_bag), "avainesine ei mene bagiin"
    assert m.inventory.get("Rusted Sluice Cog", 0) == 0, "rattaat kului"


def test_crank_blueprint_exists():
    from loot_data import BLUEPRINTS
    bp = BLUEPRINTS["Cistern Gate Crank"]
    assert bp["type"] == "key_item"
    assert "Rusted Sluice Cog" in bp["mats"]


# ----------------------------------------------------------------------
# 4) Portti + bossin intro
# ----------------------------------------------------------------------

def test_gate_requires_crank_then_spawns_boss():
    from citys.mucford.muckford_warrens import MuckfordWarrensMenu, warrens_state
    m = _manager()
    _warrens_at_stage5(m)
    menu = MuckfordWarrensMenu(m)
    menu.on_enter()
    gate = menu.arena.boss_gate
    assert gate is not None, "portti sulkee tien ennen kampea"
    assert menu.boss is None, "boss ei ole vielä hereillä"
    # Ilman kampea portti ei aukea
    m.player_character.rect.center = gate.rect.center
    menu._try_crank_gate()
    st = warrens_state(m)
    assert not st["gate_cranked"], "ilman kampea ei aukea"
    assert menu.boss is None
    # Kammella aukeaa + boss herää eeppisellä introlla
    m.inventory["Cistern Gate Crank"] = 1
    menu._try_crank_gate()
    assert st["gate_cranked"] and st["boss_unlocked"]
    assert menu.arena.boss_gate is None, "portti aukesi"
    assert menu.boss is not None and getattr(menu.boss, "is_boss", True)
    assert menu.dialogue_active, "Rat King uhoaa avauksen jälkeen"
    assert "Rat King" in menu.dialogue_name
    assert m.inventory.get("Cistern Gate Crank", 0) == 0, "kampi kului"


def test_gate_locked_before_stage5():
    from citys.mucford.muckford_warrens import MuckfordWarrensMenu, warrens_state
    m = _manager()
    st = warrens_state(m)
    st["quest_stage"] = 3    # nestien vaihe
    menu = MuckfordWarrensMenu(m)
    menu.on_enter()
    m.inventory["Cistern Gate Crank"] = 1
    gate = menu.arena.boss_gate
    m.player_character.rect.center = gate.rect.center
    menu._try_crank_gate()
    assert not st["gate_cranked"], "porttia ei voi kammeta ennen vaihetta 5"
    assert m.inventory.get("Cistern Gate Crank", 0) == 1, "kampi ei kulu turhaan"


# ----------------------------------------------------------------------
# 5) Bossin kaato
# ----------------------------------------------------------------------

def test_boss_death_completes_hunt_and_stage6():
    from citys.mucford.muckford_warrens import MuckfordWarrensMenu, warrens_state
    from quest_system import quest_manager
    m = _manager()
    st = _warrens_at_stage5(m)
    st["gate_cranked"] = True
    st["boss_unlocked"] = True
    menu = MuckfordWarrensMenu(m)
    menu.on_enter()
    assert menu.boss is not None
    menu.boss.current_hp = 0
    menu.boss.is_dead = True
    menu._process_boss()
    assert st["boss_defeated"]
    assert int(st["quest_stage"]) >= 6
    assert m.inventory.get("Gnawed Crown", 0) >= 1
    q = quest_manager.quests.get("hunt_01")
    assert q is not None and q.completed, "Rat Kingin kaato kuittaa hunt_01"


# ----------------------------------------------------------------------
# 6) Retkikunta warrensissa
# ----------------------------------------------------------------------

def test_expedition_party_joins_warrens():
    from citys.mucford.muckford_warrens import MuckfordWarrensMenu
    from units.human import Human
    from systems import expedition
    m = _manager()
    hero = m.player_character
    hero.unlocked_skills.add("warband_1")
    hero.calculate_final_stats()
    for i in range(2):
        u = Human(f"Apuri{i}", 0, 0, PLAYER_TEAM)
        m.my_team.add(u)
        expedition.toggle_member(m, u)
    menu = MuckfordWarrensMenu(m)
    menu.on_enter()
    assert m.expedition_field_active
    assert len(menu.expedition_units()) == 2, "apurit mukana tunneleissa"
    surf = pygame.Surface((1920, 1080))
    menu.update()
    menu.draw(surf)   # ei kaadu


# ----------------------------------------------------------------------
# 7) Griznak seuraa Warrens-linjaa
# ----------------------------------------------------------------------

def test_griznak_reports_warrens_crisis():
    from systems import griznak_caravan
    m = _manager()
    events = griznak_caravan.world_events(m)
    assert any("Warrens" in e or "sewer hatch" in e for e in events), \
        "Griznak ohjaa viemäriin heti alussa"
    # Edetessä Griznak raportoi vaiheen
    _warrens_at_stage5(m)
    events = griznak_caravan.world_events(m)
    assert any("stage 5" in e for e in events), "Griznak seuraa etenemistä"
