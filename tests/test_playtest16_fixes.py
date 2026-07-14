# tests/test_playtest16_fixes.py
"""Pelitestikierros 16: YHTENÄINEN KERÄYS.

E ja hiiren klikkaus käynnistävät SAMAN keräyskanavan
(HarvestableProp.try_begin_channel/update_channel): latauspalkki etenee,
pelaaja heilauttaa iskun välein (animaatio + efektit + äänet), liike
keskeyttää, ja logiikka on yksi ja sama joka kartalla - joten Commander-
polkujen bonukset (chop_speed, forestry-portit...) osuvat aina.
"""
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


def _equip_axe(hero):
    from items.tools.weak_lumberaxe import WeakLumberAxe
    hero.equipment["main_hand"] = WeakLumberAxe()


def _city_with_tree(m):
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.muckford_objects import MuckfordTree
    city = MuckfordCityMenu(m)
    city.on_enter()
    tree = next(p for p in city.arena.props
                if isinstance(p, MuckfordTree) and not p.is_empty)
    city.player.rect.center = (tree.rect.centerx + 50, tree.rect.centery)
    return city, tree


# ----------------------------------------------------------------------
# E ja klikkaus -> sama kanava
# ----------------------------------------------------------------------

def test_e_starts_tree_channel_and_chops_until_felled():
    m = _manager()
    _equip_axe(m.player_character)
    city, tree = _city_with_tree(m)
    hits0 = tree.current_hits
    wood_key = tree.resource_name  # integraatiot voivat nimetä uudelleen
    wood0 = m.inventory.get(wood_key, 0)
    # E-polku (sama metodi jota myös klikkaus käyttää)
    assert city._try_interact_prop(tree, check_collision=False) is True
    assert tree.channel_active, "kanava käynnistyi E:llä"
    # Aja kanavaa: isku swing_intervalin välein kunnes puu kaatuu
    for _ in range(tree.swing_interval * (tree.max_hits + 1)):
        tree.update(None, m)
        if tree.is_empty:
            break
    assert tree.is_empty, "puu kaatuu kanavan lopussa"
    assert tree.current_hits < hits0
    assert m.inventory.get(wood_key, 0) > wood0, "puuta kertyi"


def test_click_on_tree_canopy_starts_same_channel():
    m = _manager()
    _equip_axe(m.player_character)
    city, tree = _city_with_tree(m)
    # Klikkaa puun NÄKYVÄÄN latvukseen (ei pieneen runkorectiin)
    wx = tree.image_pos[0] + 20
    wy = tree.image_pos[1] + 30
    sx = wx - city.camera_x
    sy = wy - city.camera_y
    assert city._handle_click((sx, sy)) is True
    assert tree.channel_active, "klikkaus aloittaa hakkuun kuten E"


def test_channel_swing_sets_attack_animation():
    m = _manager()
    _equip_axe(m.player_character)
    city, tree = _city_with_tree(m)
    tree.try_begin_channel(m.player_character, m)
    for _ in range(tree.swing_interval):
        tree.update(None, m)
    assert m.player_character.animation_state == "attack", \
        "isku näyttää hyökkäysanimaation myös E-polulla"
    assert m.player_character.animation_timer > 0


def test_movement_cancels_channel():
    m = _manager()
    _equip_axe(m.player_character)
    city, tree = _city_with_tree(m)
    tree.try_begin_channel(m.player_character, m)
    assert tree.channel_active
    m.player_character.rect.x += 40  # kävely pois
    tree.update(None, m)
    assert not tree.channel_active, "liike keskeyttää keräyksen"


def test_axe_required_no_air_swing():
    m = _manager()
    m.player_character.equipment["main_hand"] = None
    m.player_character.calculate_final_stats()
    city, tree = _city_with_tree(m)
    # Kutsu "kulutetaan" (viesti) mutta kanava ei ala eikä lyödä ilmaan
    consumed = tree.try_begin_channel(m.player_character, m)
    assert consumed is True
    assert not tree.channel_active, "ilman kirvestä ei aloiteta"


def test_too_far_does_not_start():
    m = _manager()
    _equip_axe(m.player_character)
    city, tree = _city_with_tree(m)
    m.player_character.rect.center = (tree.rect.centerx + 600,
                                      tree.rect.centery)
    assert tree.try_begin_channel(m.player_character, m) is False


# ----------------------------------------------------------------------
# Romukasat: klikkaus ei enää kerää heti - sama kanava timerillä
# ----------------------------------------------------------------------

def test_scrap_pile_click_uses_timer_channel():
    from crafting.swamp.scrap_pile import ScrapPile
    m = _manager()
    pile = ScrapPile(500, 500)
    m.player_character.rect.center = (540, 520)
    scrap0 = m.inventory.get("Scrap Iron", 0)
    assert pile.try_begin_channel(m.player_character, m) is True
    assert pile.channel_active
    assert m.inventory.get("Scrap Iron", 0) == scrap0, \
        "klikkaus EI kerää heti - timer käy ensin"
    total = pile.swing_interval * pile.channel_swings_needed
    for _ in range(total + 2):
        pile.update(None, m)
    assert pile.is_empty
    assert m.inventory.get("Scrap Iron", 0) > scrap0


def test_big_scrap_pile_channel_continues_until_empty():
    from assets.tiles.muckford_objects import ScrapPileBig
    m = _manager()
    pile = ScrapPileBig(600, 600)
    pile.max_searches = pile.current_searches = 3
    m.player_character.rect.center = (pile.rect.centerx + 60,
                                      pile.rect.centery)
    pile.try_begin_channel(m.player_character, m)
    for _ in range(pile.swing_interval * pile.channel_swings_needed * 6):
        pile.update(None, m)
        if pile.is_empty:
            break
    assert pile.is_empty, "tonkiminen jatkuu automaattisesti loppuun"
    assert pile.current_searches == 0


# ----------------------------------------------------------------------
# Sama järjestelmä muillakin kartoilla (hökkelimetsän propit)
# ----------------------------------------------------------------------

def test_swamp_props_use_unified_channel():
    from crafting.swamp.swamp_tree import SwampTree
    from crafting.swamp.nightcap_fungus import NightcapFungus
    from assets.tiles.prop import HarvestableProp
    m = _manager()
    _equip_axe(m.player_character)
    tree = SwampTree(400, 300)
    shroom = NightcapFungus(800, 800)
    assert isinstance(tree, HarvestableProp)
    assert isinstance(shroom, HarvestableProp)
    # Puu: kirveellä kanava käy
    m.player_character.rect.center = (tree.rect.centerx + 50,
                                      tree.rect.centery)
    assert tree.try_begin_channel(m.player_character, m) is True
    assert tree.channel_active
    # add_material voi mapata nimen (integraatiot) - vertaa kokonaismäärää
    total0 = sum(m.inventory.values())
    for _ in range(tree.swing_interval * tree.channel_swings_needed + 2):
        tree.update(None, m)
    assert sum(m.inventory.values()) > total0, "hakkuusykli antoi puuta"
    # Sieni: ei työkaluvaatimusta
    m.player_character.rect.center = (shroom.rect.centerx + 40,
                                      shroom.rect.centery)
    assert shroom.try_begin_channel(m.player_character, m) is True
    total1 = sum(m.inventory.values())
    for _ in range(shroom.swing_interval * shroom.channel_swings_needed + 2):
        shroom.update(None, m)
    assert sum(m.inventory.values()) > total1, "poiminta antoi sienen"


def test_void_iron_requires_tier3_pickaxe():
    from crafting.swamp.void_iron_node import VoidIronNode
    m = _manager()
    _equip_axe(m.player_character)  # väärä työkalu
    node = VoidIronNode(500, 500)
    m.player_character.rect.center = (node.rect.centerx + 40,
                                      node.rect.centery)
    consumed = node.try_begin_channel(m.player_character, m)
    assert consumed is True and not node.channel_active, \
        "Tier 3 hakku vaaditaan - kanava ei ala kirveellä"


def test_e_hold_autostarts_on_any_map(monkeypatch):
    """E pohjassa lähellä proppia käynnistää kanavan ILMAN kartan omaa
    E-käsittelijää - siksi sama toiminta joka kartalla."""
    from crafting.swamp.scrap_pile import ScrapPile
    from systems import keybinds
    m = _manager()
    pile = ScrapPile(700, 700)
    m.player_character.rect.center = (740, 720)
    monkeypatch.setattr(keybinds, "pressed", lambda keys, action:
                        action == "interact")
    pile.update(None, m)
    assert pile.channel_active, "E-pohjassa aloittaa kanavan suoraan"
