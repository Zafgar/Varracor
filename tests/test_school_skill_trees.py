# tests/test_school_skill_trees.py
"""Pelitesti 39: koulukohtaiset erikoistumispuut (Necro/Druid/Holy).
Lyhyet puut, erikoistumissuunnat, toisensa poissulkevat koulut, ja efektit
kertyvät unit.school_effects-sanakirjaan.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


def _caster():
    import main  # noqa: F401
    from units.human import Human
    from settings import PLAYER_TEAM
    u = Human("Mage", 0, 0, PLAYER_TEAM)
    u.level = 30
    u.skill_points = 40
    # Avaa loitsiminen (int_apprentice on kaikkien koulujen entry-vaatimus)
    from skills.skill_system import unlock_skill
    unlock_skill(u, "int_scholar")
    unlock_skill(u, "int_apprentice")
    return u


def _unlock(u, *ids):
    from skills.skill_system import unlock_skill
    out = []
    for i in ids:
        out.append(unlock_skill(u, i))
    return out


def test_all_three_school_trees_registered():
    from skills.skills_data import SKILL_TREE
    for nid in ("necro_initiate", "necro_summon_2", "druid_initiate",
                "druid_control_2", "holy_initiate", "holy_buff_2"):
        assert nid in SKILL_TREE, f"{nid} puuttuu puusta"


def test_necro_summoner_effects_accumulate():
    u = _caster()
    ok1, _ = _unlock(u, "necro_initiate")[0], None
    _unlock(u, "necro_summon_1", "necro_summon_2")
    u.calculate_final_stats()
    assert u.magic_school == "necromancy"
    assert u.school_effects.get("summon_max") == 2
    assert u.school_effects.get("summon_tier") == 1


def test_necro_lifesteal_path():
    u = _caster()
    _unlock(u, "necro_initiate", "necro_steal_1", "necro_steal_2")
    u.calculate_final_stats()
    assert abs(u.school_effects.get("lifesteal_pct", 0) - 0.40) < 1e-6


def test_druid_paths_effects():
    u = _caster()
    _unlock(u, "druid_initiate", "druid_life_1", "druid_life_2",
            "druid_control_1")
    u.calculate_final_stats()
    assert u.magic_school == "druidism"
    assert u.school_effects.get("hot_power") == 3
    assert u.school_effects.get("control_power") == 1
    assert u.school_effects.get("nature_damage") == 1


def test_holy_buff_and_heal():
    u = _caster()
    _unlock(u, "holy_initiate", "holy_buff_1", "holy_buff_2", "holy_heal_1")
    u.calculate_final_stats()
    assert u.magic_school == "holy"
    assert u.school_effects.get("team_buff") == 3
    assert u.school_effects.get("team_damage_reduction") == 1
    assert u.school_effects.get("heal_power") == 1


# ----------------------------------------------------------------------
# Toisensa poissulkevat koulut (puu sitoo hahmoa)
# ----------------------------------------------------------------------

def test_schools_are_mutually_exclusive():
    from skills.skill_system import can_unlock, unlock_skill
    u = _caster()
    ok, _ = unlock_skill(u, "necro_initiate")
    assert ok
    # Necro valittu -> Holy/Druid estetty
    can_holy, reason = can_unlock(u, "holy_initiate")
    assert not can_holy and "Committed" in reason
    can_druid, _ = can_unlock(u, "druid_initiate")
    assert not can_druid
    # Necron omat suunnat yhä avattavissa
    can_curse, _ = can_unlock(u, "necro_curse_1")
    assert can_curse


def test_school_entry_requires_apprentice():
    from skills.skill_system import can_unlock
    import main  # noqa: F401
    from units.human import Human
    from settings import PLAYER_TEAM
    u = Human("Grunt", 0, 0, PLAYER_TEAM)
    u.level = 30
    u.skill_points = 40
    # Ei int_apprentice -> ei voi sitoutua kouluun
    can, reason = can_unlock(u, "necro_initiate")
    assert not can and "Prerequisites" in reason
