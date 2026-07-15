# tests/test_playtest26_fixes.py
"""Pelitestikierros 26: laaja viemäri-questlinja (Rat King vasta lopussa).
1) Iso alue (4600x2800) monine reitteineen ja keräilysolmuineen
2) Vaihe 1 CULL: kaada N rottaa -> raha + XP + heikko ase
3) Vaihe 2 INVASION: lyö aalto + sulje repeämä -> alue turvalliseksi
4) Keräily aukeaa turvallisella alueella (yrtit/sienet resepteja varten)
5) Vaihe 3 valve, 4 lore (Vortex Abyssal + nimetty king), 5 lankkusilta,
   6 sammakko-seppa + portti-ram
6) Vaihe 7: nimetty Rat King (Skrivvax); kaato -> vaihe 8 + hunt_01
7) Sammakko-seppä Brekka rekrytoituu portti-ram rakennettaessa
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


def _menu(m):
    from citys.mucford.muckford_warrens import MuckfordWarrensMenu
    menu = MuckfordWarrensMenu(m)
    menu.on_enter()
    return menu


def _near(m, prop):
    m.player_character.rect.center = prop.rect.center


# ----------------------------------------------------------------------
# 1) Vaihe 1: cull + palkkio
# ----------------------------------------------------------------------

def test_cull_rewards_gold_xp_and_weapon():
    from citys.mucford.muckford_warrens import warrens_state, CULL_TARGET
    m = _manager()
    menu = _menu(m)
    st = warrens_state(m)
    st["quest_stage"] = 1
    gold0 = m.gold
    for mo in list(menu.monsters):
        mo.is_dead = True
    menu._track_kills()
    assert st["rats_culled"] >= CULL_TARGET
    assert st["quest_stage"] == 2, "cull-tavoite etenee invaasioon"
    assert m.gold == gold0 + 40, "Hamo maksaa cullista"
    assert any(getattr(i, "name", "") == "Scrap Blade"
               for i in m.equipment_bag), "heikko ase palkintona"


# ----------------------------------------------------------------------
# 2) Vaihe 2: invaasio + repeämän sulku -> alue turvalliseksi
# ----------------------------------------------------------------------

def test_breach_seal_needs_wave_then_opens_gathering():
    from citys.mucford.muckford_warrens import warrens_state, INVASION_TARGET
    m = _manager()
    menu = _menu(m)
    st = warrens_state(m)
    st["quest_stage"] = 2
    _near(m, menu.arena.breach)
    # Ilman aallon kaatoa ei voi sulkea
    assert menu._try_breach() is True
    assert not st["breach_sealed"], "aalto lyötävä ensin"
    st["invasion_kills"] = INVASION_TARGET
    assert menu._try_breach() is True
    assert st["breach_sealed"]
    assert st["quest_stage"] == 3
    assert st["area_safe"] is True, "alue turvalliseksi -> keräily aukeaa"


def test_gathering_only_when_area_safe():
    from citys.mucford.muckford_warrens import warrens_state
    m = _manager()
    menu = _menu(m)
    st = warrens_state(m)
    node = menu.arena.gather_nodes[0]
    _near(m, node)
    # Ennen turvaamista ei voi kerätä
    assert menu._try_gather() is False
    st["area_safe"] = True
    assert menu._try_gather() is True
    assert node.gathered
    assert m.inventory.get(node.resource_name, 0) >= 1


# ----------------------------------------------------------------------
# 3) Vaiheet 3-6: valve, lore, silta, portti-ram
# ----------------------------------------------------------------------

def test_valve_advances_to_camp():
    from citys.mucford.muckford_warrens import warrens_state
    m = _manager()
    menu = _menu(m)
    st = warrens_state(m)
    st["quest_stage"] = 3
    _near(m, menu.arena.valve)
    menu._try_valve()
    assert st["valve_turned"] and st["quest_stage"] == 4


def test_lore_needs_camp_cleared_then_triggers_tremor():
    from citys.mucford.muckford_warrens import warrens_state, CAMP_TARGET
    m = _manager()
    menu = _menu(m)
    st = warrens_state(m)
    st["quest_stage"] = 4
    _near(m, menu.arena.lore_board)
    assert menu._try_lore() is True
    assert not st["lore_read"], "leiri siivottava ensin"
    st["camp_kills"] = CAMP_TARGET
    menu._try_lore()
    assert st["lore_read"]
    assert st["quest_stage"] == 5 and st["tremor_triggered"] is True
    # Lore mainitsee Vortex Abyssalin ja Mestarin (menun oma dialogi)
    assert menu.dialogue_active
    text = " ".join(menu.dialogue_pages)
    assert "Abyssal" in text and "Master" in text


def test_bridge_needs_wood():
    from citys.mucford.muckford_warrens import (
        warrens_state, BRIDGE_MATERIAL, BRIDGE_WOOD)
    m = _manager()
    menu = _menu(m)
    st = warrens_state(m)
    st["quest_stage"] = 5
    _near(m, menu.arena.bridge_site)
    assert menu._try_bridge() is True
    assert not st["bridge_built"], "puu vaaditaan"
    m.inventory[BRIDGE_MATERIAL] = BRIDGE_WOOD
    menu._try_bridge()
    assert st["bridge_built"] and st["quest_stage"] == 6


def test_device_recruits_smith_and_opens_gate():
    from citys.mucford.muckford_warrens import warrens_state, DEVICE_RECIPE
    m = _manager()
    menu = _menu(m)
    st = warrens_state(m)
    st["quest_stage"] = 6
    st["bridge_built"] = True
    menu._refresh_npcs()   # Brekka ilmestyy
    smith = [n for n in menu.warrens_npcs
             if getattr(n, "warrens_role", "") == "smith"]
    assert smith, "sammakko-seppä työpajalla"
    _near(m, smith[0])
    menu._talk_smith()
    menu.dialogue_active = False
    assert st["smith_met"]
    # Ilman materiaaleja ei rakenneta
    _near(m, menu.arena.device_site)
    assert menu._try_device() is True
    assert not st["device_built"]
    for k, v in DEVICE_RECIPE.items():
        m.inventory[k] = v
    menu._try_device()
    assert st["device_built"]
    assert st["quest_stage"] == 7 and st["boss_unlocked"]
    assert st["smith_recruited"], "Brekka liittyy tiimiin"
    assert any(getattr(u, "is_smith", False) for u in m.my_team)
    assert m.has_smith is True
    assert menu.boss is not None, "iso portti auki -> boss herää"


# ----------------------------------------------------------------------
# 4) Vaihe 7-8: nimetty Rat King + kaato
# ----------------------------------------------------------------------

def test_named_rat_king_and_completion():
    from citys.mucford.muckford_warrens import warrens_state, RAT_KING_NAME
    from quest_system import quest_manager
    m = _manager()
    menu = _menu(m)
    st = warrens_state(m)
    st["quest_stage"] = 7
    st["boss_unlocked"] = True
    menu._spawn_boss_if_needed()
    assert menu.boss.name == RAT_KING_NAME
    assert "Abyssal" in menu.boss.name or "Crown" in menu.boss.name
    menu.boss.is_dead = True
    menu._process_boss()
    assert st["boss_defeated"] and st["quest_stage"] == 8
    q = quest_manager.quests.get("hunt_01")
    assert q is not None and q.completed
