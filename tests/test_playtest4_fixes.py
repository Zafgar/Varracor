# tests/test_playtest4_fixes.py
"""Pelitestikierros 4: työkalujen equip Paths-poluilla, skill-puu bonuksiksi,
ESC-paneelit, inventoryn ESC, kauppojen ostovahvistus, kojujen vuorokausi-
rytmi, miekkavarkaus introssa ja aluedialogien yhtenäistys."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


# ----------------------------------------------------------------------
# Commander Paths vs. skill-puu
# ----------------------------------------------------------------------

def test_tools_equip_without_weapon_training():
    """Path of the Vein sanoo 'Weak Pickaxe käytettävissä' -> hakun pitää
    myös mahtua käteen ilman skill-puun Pickaxe Trainingia."""
    m = _manager()
    pc = m.player_character
    from items.tools.weak_pickaxe import WeakPickaxe
    pick = WeakPickaxe()
    assert "pickaxe" not in pc.weapon_masteries
    ok, reason = pc.can_equip_item_to_slot("main_hand", pick)
    assert ok, f"hakku ei mahdu käteen: {reason}"


def test_skill_tree_tool_nodes_are_bonus_only():
    """Työkalujen käyttöoikeus tulee Paths-poluista - pistepuun noodit
    eivät saa enää portittaa niitä weapon_prof-luvalla."""
    from skills.commander_skills_data import COMMANDER_SKILL_TREE
    for node_id in ("mining_1", "lumber_1"):
        effects = COMMANDER_SKILL_TREE[node_id]["effects"]
        assert "weapon_prof" not in effects, f"{node_id} portittaa yhä työkalua"
    # Farming EI ole Commander-polku -> sirppilupa säilyy pistepuussa
    assert COMMANDER_SKILL_TREE["harvesting_1"]["effects"].get(
        "weapon_prof") == "harvest_tool"


# ----------------------------------------------------------------------
# ESC-käytös: paneelit ja inventory
# ----------------------------------------------------------------------

def test_station_hub_esc_closes_panel():
    m = _manager()
    from menus.barracks_menu import BarracksMenu
    menu = BarracksMenu(m)
    menu.show_station_hub = True
    assert menu.consumes_escape(), "hub auki -> menu haluaa ESC:n"
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                         key=pygame.K_ESCAPE))
    assert menu.show_station_hub is False, "ESC sulkee crafting-hubin"
    assert not menu.consumes_escape()


def test_barracks_upgrade_panel_esc():
    m = _manager()
    from citys.mucford.barracks_interior_menu import BarracksInteriorMenu
    menu = BarracksInteriorMenu(m)
    menu.on_enter()
    menu.show_upgrade = True
    assert menu.consumes_escape()
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN,
                                         key=pygame.K_ESCAPE))
    assert menu.show_upgrade is False


def test_inventory_esc_closes():
    m = _manager()
    m.show_inventory = True
    handled = m.handle_ui_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
        "muckford_city")
    assert handled is True
    assert m.show_inventory is False, "ESC sulkee inventoryn"
    assert m.paused is False, "ESC EI avaa pausea inventoryn päälle"


# ----------------------------------------------------------------------
# Kaupat: ostovahvistus ja vuorokausirytmi
# ----------------------------------------------------------------------

def test_district_shop_requires_confirmation():
    m = _manager()
    m.gold = 10000
    from menus.district_shop_menu import DistrictShopMenu
    menu = DistrictShopMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    assert menu.row_rects
    rect, entry = menu.row_rects[0]
    gold0 = m.gold
    # 1. klikkaus valitsee - EI osta
    menu.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1))
    assert menu.selected_entry is entry
    assert m.gold == gold0, "pelkkä valinta ei veloita"
    # 2. klikkaus samaan riviin ostaa
    menu.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1))
    assert m.gold < gold0, "toinen klikkaus ostaa"


def test_stalls_closed_at_night():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    stall = city.market_stalls[0]
    m.world_clock.minutes = 23 * 60.0
    assert not city._stalls_open()
    city.next_state = None
    assert city._try_interact_prop(stall) is True
    assert city.next_state is None, "yöllä koju ei aukea"
    m.world_clock.minutes = 12 * 60.0
    assert city._stalls_open()
    city._try_interact_prop(stall)
    assert city.next_state == "district_shop", "päivällä koju aukeaa"


def test_stall_keepers_and_night_lurkers():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    # Päivä: pitäjät kojuilla
    m.world_clock.minutes = 10 * 60.0
    city._update_market_life()
    assert len(city.stall_keepers) == len(city.market_stalls)
    assert all(k in city.npcs for k in city.stall_keepers)
    assert not city.night_lurkers
    # Yö: pitäjät kotiin, hämärähahmot liikkeelle
    m.world_clock.minutes = 23 * 60.0
    city._update_market_life()
    assert not city.stall_keepers
    assert len(city.night_lurkers) == 2
    assert all(l in city.npcs for l in city.night_lurkers)
    # Lurker-hiippailu pyörii kaatumatta
    for _ in range(120):
        city._update_lurker(city.night_lurkers[0])
    # Aamu: hämärähahmot katoavat
    m.world_clock.minutes = 8 * 60.0
    city._update_market_life()
    assert not city.night_lurkers


# ----------------------------------------------------------------------
# Intro: olento vie miekan aina
# ----------------------------------------------------------------------

def test_steal_sword_always_removes_weapon(monkeypatch):
    m = _manager()
    import citys.mucford.forest_road_menu as frm
    from items.tools.weak_pickaxe import WeakPickaxe
    menu = frm.ForestRoadMenu(m)
    sword = WeakPickaxe()
    m.player_character.equipment["main_hand"] = sword
    bag0 = len(m.equipment_bag)
    def _hand():
        # calculate_final_stats täyttää tyhjän käden Fists-nyrkeillä
        item = m.player_character.equipment.get("main_hand")
        return getattr(item, "name", None)

    monkeypatch.setattr(frm, "CHEAT_MODE", False)
    menu.handle_dialogue_effect("steal_sword")
    assert _hand() in (None, "Fists"), "miekka viedään kädestä"
    assert sword not in m.equipment_bag
    assert len(m.equipment_bag) == bag0, "normaalisti miekka katoaa kokonaan"

    # Cheat: miekka viedään kädestä mutta kopio jää reppuun
    sword2 = WeakPickaxe()
    m.player_character.equipment["main_hand"] = sword2
    monkeypatch.setattr(frm, "CHEAT_MODE", True)
    menu.handle_dialogue_effect("steal_sword")
    assert _hand() in (None, "Fists"), "miekka viedään kädestä myös cheatissa"
    assert sword2 in m.equipment_bag, "cheat-tilassa kopio jää reppuun"


# ----------------------------------------------------------------------
# Aluedialogit + inventoryn fallback-paneeli
# ----------------------------------------------------------------------

def test_area_dialogue_shows_speaker():
    from systems.area_dialogue import draw_area_dialogue
    from units.villager import Villager
    from settings import GREEN

    class FakeMenu:
        pass

    menu = FakeMenu()
    menu.dialogue_active = True
    menu.dialogue_name = "Old Rinna Net"
    menu.dialogue_pages = ["Four violet trails lead away from the cellar.",
                           "Trace all four."]
    menu.dialogue_index = 1
    menu.npcs = [Villager("Old Rinna Net", "Human", 100, 100,
                          team_color=GREEN)]
    surf = pygame.Surface((1920, 1080))
    assert draw_area_dialogue(menu, surf) is True
    menu.dialogue_active = False
    assert draw_area_dialogue(menu, surf) is False


def test_inventory_fallback_panel_no_crash():
    """_draw_legacy_character_panel kaatui manager-parametriin (7 args)."""
    m = _manager()
    m.show_inventory = True
    surf = pygame.Surface((1920, 1080))
    m.player_character.draw_inventory(surf, m)  # ei saa kaatua
