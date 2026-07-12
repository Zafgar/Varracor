# tests/test_abyssal.py
"""
Abyssal Weave - paahenkilon Vortex-taika. Viisi taitopuuta (Anchoring,
Severing, Echoing, Warping, Taint). Kaytto laukaisee Vortex-reaktion.
"""
import pytest
from settings import PLAYER_TEAM, ENEMY_TEAM


def _hero_and_foe():
    from game_manager import GameManager
    from units.orc import Orc
    m = GameManager(); m.match_in_progress = True; m.current_arena = None
    hero = m.player_character
    hero.team_color = PLAYER_TEAM
    hero.rect.center = (300, 300)
    foe = Orc("Foe", 360, 300, ENEMY_TEAM)
    foe.current_hp = foe.max_hp
    m.all_units.add(foe)
    return m, hero, foe


def test_abyssal_has_all_five_trees():
    from magic.spell_data import SPELL_LIBRARY
    trees = {v["tree"] for v in SPELL_LIBRARY.values() if v["school"] == "abyssal"}
    assert trees == {"anchoring", "severing", "echoing", "warping", "taint"}


def test_abyssal_spells_resolve():
    from magic.spell_data import SPELL_LIBRARY
    from items.item_registry import create_item
    for n, v in SPELL_LIBRARY.items():
        if v["school"] == "abyssal":
            assert create_item(n) is not None, f"{n} missing"


def test_abyssal_use_triggers_vortex_reaction():
    from items.item_registry import create_item
    m, hero, foe = _hero_and_foe()
    assert m.has_seen_vortex() is False
    create_item("Echo Strike").cast(hero, foe, m)
    assert m.has_seen_vortex() is True


def test_warp_step_moves_hero():
    from items.item_registry import create_item
    m, hero, foe = _hero_and_foe()
    x0 = hero.rect.centerx
    create_item("Warp Step").cast(hero, foe, m, target_pos=(520, 300))
    assert hero.rect.centerx != x0


def test_taint_lance_drains():
    from items.item_registry import create_item
    m, hero, foe = _hero_and_foe()
    hero.current_hp = hero.max_hp * 0.5
    hb = hero.current_hp
    create_item("Taint Lance").cast(hero, foe, m)
    assert any(e["type"] == "Poison" for e in foe.status_effects)
    assert hero.current_hp > hb  # elamansiirto


def test_anchor_field_roots():
    from items.item_registry import create_item
    m, hero, foe = _hero_and_foe()
    create_item("Anchor Field").cast(hero, foe, m)
    assert any(e["type"] == "Web" for e in foe.status_effects)


def test_sever_bonds_strips_wards():
    from items.item_registry import create_item
    m, hero, foe = _hero_and_foe()
    foe.apply_status("Warded", 300, 0)
    create_item("Sever Bonds").cast(hero, foe, m)
    assert not any(e["type"] == "Warded" for e in foe.status_effects)
