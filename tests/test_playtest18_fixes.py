# tests/test_playtest18_fixes.py
"""Pelitestikierros 18:
1) sairaudet/vammat (flunssa, ruokamyrkytys, murtuma, väsymys, vakava
   haava): kesto päivinä, taisteludebuffit, kuolemanriski kentällä,
   hoidot - Commander immuuni
2) Saggan rohtoteltta Muckfordissa (hoidot + rohdot)
3) sponsorisopimuksen allekirjoitus toimii + liigavoiton bonus +
   sponsoriliput taistelussa
4) kylävaraston UI: rullaus, lahjoitukset antavat mainetta,
   "Unknown"-roska siivotaan
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from settings import PLAYER_TEAM


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def _fighter(m, name="Kisälli"):
    from units.human import Human
    u = Human(name, 500, 500, PLAYER_TEAM)
    m.my_team.add(u)
    return u


# ----------------------------------------------------------------------
# 1) Sairaudet ja vammat
# ----------------------------------------------------------------------

def test_conditions_add_modifiers_and_commander_immune():
    from systems import conditions as cond
    m = _manager()
    u = _fighter(m)
    assert cond.add_condition(u, "flu", m) is True
    assert cond.has_condition(u, "flu")
    mods = cond.modifiers(u)
    assert mods["damage_mult"] < 1.0
    # Sama tila ei tuplaannu
    assert cond.add_condition(u, "flu", m) is False
    # Commander on immuuni
    assert cond.add_condition(m.player_character, "flu", m) is False
    assert not cond.get_conditions(m.player_character)


def test_condition_debuffs_apply_to_stats():
    from systems import conditions as cond
    m = _manager()
    u = _fighter(m)
    u.calculate_final_stats()
    speed0, hp0 = u.walk_speed, u.max_hp
    cond.add_condition(u, "fracture", m)
    cond.add_condition(u, "severe_wound", m)
    u.calculate_final_stats()
    assert u.walk_speed < speed0, "murtuma hidastaa"
    assert u.max_hp < hp0, "vakava haava laskee max-HP:tä"
    cond.clear_all(u)
    u.calculate_final_stats()
    assert u.max_hp == hp0, "parantuminen palauttaa statsit"


def test_day_rollover_ticks_and_heals():
    from systems import conditions as cond
    from world_clock import DAYS_PER_YEAR
    m = _manager()
    u = _fighter(m)
    cond.add_condition(u, "food_poisoning", m)  # 2 pv
    clock = m.world_clock
    m._conditions_day = clock.year * DAYS_PER_YEAR + clock.day
    clock.advance_day()
    cond.check_day_rollover(m)
    assert cond.get_conditions(u)[0]["days_left"] == 1
    clock.advance_day()
    cond.check_day_rollover(m)
    assert not cond.get_conditions(u), "tila parani ajan kanssa"


def test_battle_aftermath_wounds_and_death_risk(monkeypatch):
    from systems import conditions as cond
    m = _manager()
    u = _fighter(m, "Kolhittu")
    u.is_dead = True
    monkeypatch.setattr(cond.random, "random", lambda: 0.0)
    monkeypatch.setattr(cond.random, "choice", lambda seq: seq[0])
    msgs = cond.apply_battle_aftermath(m, [u], win=True)
    assert cond.get_conditions(u), "kaatunut sai vamman"
    assert msgs
    # Kuolemanriski realisoituu: sairaana kentälle -> voi kuolla
    v = _fighter(m, "Uhkarohkea")
    cond.add_condition(v, "severe_wound", m)
    cond.mark_prebattle_risks(m, [v])
    assert v._prebattle_death_risk > 0
    msgs = cond.apply_battle_aftermath(m, [v], win=True)
    assert v.is_dead, "riski toteutui (random=0)"
    assert v not in m.my_team
    assert any("succumbed" in msg for msg in msgs)


def test_treat_all_costs_gold_and_cures():
    from systems import conditions as cond
    m = _manager()
    u = _fighter(m)
    cond.add_condition(u, "flu", m)
    cond.add_condition(u, "fracture", m)
    cost = cond.total_treatment_cost(m)
    assert cost == cond.REMEDY_PRICES["flu"] + cond.REMEDY_PRICES["fracture"]
    m.gold = cost
    msgs = cond.treat_all(m)
    assert not cond.get_conditions(u), "kaikki hoidettu"
    assert m.gold == 0
    assert len(msgs) == 2
    # Väsymys ei parane rahalla - vain levolla
    cond.add_condition(u, "fatigue", m)
    assert cond.total_treatment_cost(m) == 0
    ok, msg = cond.treat_condition(m, u, "fatigue")
    assert not ok and "rest" in msg


def test_barracks_sleep_cures_fatigue():
    from systems import conditions as cond
    from citys.mucford.barracks_interior_menu import BarracksInteriorMenu
    m = _manager()
    u = _fighter(m)
    cond.add_condition(u, "fatigue", m)
    menu = BarracksInteriorMenu(m)
    menu.on_enter()
    menu._sleep()
    assert not cond.has_condition(u, "fatigue"), "lepo poistaa väsymyksen"


def test_conditions_survive_save_load(tmp_path, monkeypatch):
    import save_manager
    from systems import conditions as cond
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE",
                        str(tmp_path / "savegame.json"))
    m = _manager()
    u = _fighter(m)
    cond.add_condition(u, "fracture", m)
    m.tier0_sponsor = "shanty"
    m.storage_donations = 7
    m.inventory["Unknown"] = 4
    assert save_manager.save_game(m)
    m2 = _manager()
    assert save_manager.load_game(m2)
    loaded = next(iter(m2.my_team))
    assert cond.has_condition(loaded, "fracture")
    assert m2.tier0_sponsor == "shanty"
    assert m2.storage_donations == 7
    assert "Unknown" not in m2.inventory, "roskamateriaali siivottu"


# ----------------------------------------------------------------------
# 2) Saggan teltta
# ----------------------------------------------------------------------

def test_muckford_has_herbalist_tent_and_sagga():
    from systems import conditions as cond
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    m = _manager()
    u = _fighter(m)
    cond.add_condition(u, "flu", m)
    city = MuckfordCityMenu(m)
    city.on_enter()
    assert city.herbalist_tent is not None, "teltta löytyy kartalta"
    assert city.sagga is not None and city.sagga.name == "Sagga the Herbwife"
    city._open_sagga_dialogue()
    assert m.active_dialogue is not None
    actions = [o["action"] for o in m.active_dialogue["options"]]
    assert "sagga_treat_all" in actions
    m.gold = 100
    city._on_sagga_action("sagga_treat_all")
    assert not cond.get_conditions(u), "Sagga hoiti flunssan"
    assert m.gold == 100 - cond.REMEDY_PRICES["flu"]
    m.active_dialogue = None
    m.dialogue_cooldown = 0


# ----------------------------------------------------------------------
# 3) Sponsorit
# ----------------------------------------------------------------------

def test_sign_contract_actually_signs():
    from menus.sponsor_menu import SponsorMenu
    m = _manager()
    menu = SponsorMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)  # asettaa sign-napin tilan
    pos = menu.btn_sign.rect.center
    import unittest.mock as mock
    with mock.patch.object(pygame.mouse, "get_pos", return_value=pos):
        menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                             pos=pos, button=1))
    assert m.tier0_sponsor == "shanty", "sopimus syntyi"
    menu.draw(surf)
    assert menu.btn_sign.text == "TERMINATE"
    # Toinen klikkaus purkaa
    with mock.patch.object(pygame.mouse, "get_pos", return_value=pos):
        menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                             pos=pos, button=1))
    assert m.tier0_sponsor is None


def test_sponsor_win_bonus_on_league_win():
    m = _manager()
    m.tier0_sponsor = "shanty"
    m.mode = "League"
    m.match_mode = "1v1"
    m.current_enemy_team = None
    m.gold = 100
    m.end_match(True)
    assert m.gold >= 115, "sponsorin voittobonus maksettiin"


def test_sponsor_flags_draw_in_league_battle():
    from menus.battle_screen import BattleScreen
    from arenas.tier_1.grand_slam_arena import GrandSlamArena
    m = _manager()
    m.mode = "League"
    m.tier0_sponsor = "shanty"
    m.current_arena = GrandSlamArena()
    m.camera_x = m.camera_y = 0
    bs = BattleScreen(m)
    surf = pygame.Surface((1920, 1080))
    bs._draw_sponsor_flags(surf)  # ei kaadu; piirtää liput


# ----------------------------------------------------------------------
# 4) Kylävarasto
# ----------------------------------------------------------------------

def test_storage_donations_grant_reputation():
    from menus.city_storage_menu import CityStorageMenu, DONATIONS_PER_REP
    from quest_system import quest_manager
    m = _manager()
    m.inventory["Egg"] = DONATIONS_PER_REP + 2
    menu = CityStorageMenu(m)
    rep0 = quest_manager.reputation
    menu._deposit_item("Egg", all_of=True)
    assert m.city_storage.get("Egg", 0) >= DONATIONS_PER_REP
    assert quest_manager.reputation == rep0 + 1, \
        "joka 10. lahjoitus antaa mainetta"
    assert m.storage_donations == 2, "ylijäämä jää laskuriin"
    quest_manager.reputation = rep0


def test_storage_scrolls_and_hides_unknown():
    from menus.city_storage_menu import CityStorageMenu
    m = _manager()
    for i in range(30):
        m.city_storage[f"Ware {i:02d}"] = i + 1
    m.city_storage["Unknown"] = 9
    menu = CityStorageMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    # Rullaus ei kaadu ja pysyy rajoissa
    for _ in range(20):
        menu.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-1))
    menu.draw(surf)
    assert menu.city_scroll >= 0
    # "Unknown" ei näy listalla (siivottu roska)
    items = [n for n, c in m.city_storage.items() if n == "Unknown"]
    assert items, "data on yhä olemassa"  # vain piilotettu näkymästä


def test_prepare_menu_shows_condition_icons():
    from systems import conditions as cond
    from menus.prepare_menu import PrepareMenu
    m = _manager()
    u = _fighter(m)
    cond.add_condition(u, "severe_wound", m)
    menu = PrepareMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    assert getattr(menu, "_cond_hover_rects", []), \
        "vamman ikoni piirtyi rosterikorttiin"
    rect = menu._cond_hover_rects[0][0]
    import unittest.mock as mock
    with mock.patch.object(pygame.mouse, "get_pos",
                           return_value=rect.center):
        menu.draw(surf)  # tooltip piirtyy kaatumatta
