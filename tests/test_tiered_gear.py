# tests/test_tiered_gear.py
"""Pelitesti 42: tier-varusteet (statit tulevat gearista).
- 72 varusteen katalogi (9 linjaa x 8 tieriä), budjetit statikäyrästä
- Erikoistumisrelikvit: koulubonukset kertyvät school_effects-sanakirjaan
  varusteista (summoner/leech/life/wild/light) - useita reittejä magiassa
- Relic vaatii Relic User -noden; level_req portittaa
- Koulukaupat myyvät oman koulunsa varusteet, maine-portit päällä
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


class _Arena:
    obstacles = []
    width = 2000
    height = 2000


def _mgr():
    import main  # noqa: F401
    from game_manager import GameManager
    m = GameManager()
    m.current_arena = _Arena()
    return m


def _caster_unit(level=28):
    import main  # noqa: F401
    from units.human import Human
    from settings import PLAYER_TEAM
    from skills.skill_system import unlock_skill
    u = Human("Magus", 0, 0, PLAYER_TEAM)
    u.level = level
    u.skill_points = 40
    unlock_skill(u, "int_scholar")
    unlock_skill(u, "int_relic_user")   # relic-proficiency
    u.calculate_final_stats()           # masteries päivittyvät puusta
    return u


# ----------------------------------------------------------------------
# Katalogi + budjetit
# ----------------------------------------------------------------------

def test_catalog_size_and_unique_ids():
    # Armor rework (pelitesti 26): 9 alkup. linjaa + 6 vartaloa +
    # 5 kypärää + 3 kilpeä = 23 linjaa x 8 tieriä = 184
    from items.gear_catalog import CATALOG
    assert len(CATALOG) == 184
    ids = [g["id"] for g in CATALOG]
    assert len(set(ids)) == 184


def test_budgets_follow_curve():
    from items.gear_catalog import make_gear
    t1 = make_gear("arcanist_t1")
    t8 = make_gear("arcanist_t8")
    assert t8.int_bonus > t1.int_bonus * 30, \
        "T8 antaa satoja, T1 muutamia (käyrä)"
    w8 = make_gear("warrior_t8")
    assert w8.str_bonus > 200 and w8.defense > 100
    assert t8.cost > t1.cost
    assert t8.level_req > t1.level_req


def test_describe_has_key_fields():
    from items.gear_catalog import make_gear
    d = make_gear("necro_leech_t4").describe()
    for token in ("Slot:", "Tier:", "School:", "Stats:", "Specialization:",
                  "Requires: Level", "Price:"):
        assert token in d, f"selitteestä puuttuu {token}"


# ----------------------------------------------------------------------
# Koulubonukset varusteista
# ----------------------------------------------------------------------

def test_relic_school_bonuses_merge_into_school_effects():
    from items.gear_catalog import make_gear
    u = _caster_unit()
    relic = make_gear("necro_leech_t4")
    left = u.equip_item_to_slot("off_hand", relic)
    assert left is not relic or u.equipment["off_hand"] is relic, \
        "relikvi menee käteen relic-proficiencylla"
    u.calculate_final_stats()
    assert abs(u.school_effects.get("lifesteal_pct", 0) - 0.08) < 1e-6


def test_summoner_relic_raises_summon_cap():
    from items.gear_catalog import make_gear
    from spells.necro.raise_skeleton import RaiseSkeleton
    m = _mgr()
    u = _caster_unit()
    u.max_mana = 300
    u.current_mana = 300
    u.rect.center = (500, 500)
    m.my_team.empty()
    m.all_units.empty()
    m.my_team.add(u)
    m.all_units.add(u)
    u.equipment["off_hand"] = make_gear("necro_summoner_t5")  # +1 summon
    u.calculate_final_stats()
    u.max_mana = 300
    u.current_mana = 300   # recalc clampaa manan -> asetetaan sen jälkeen
    sp = RaiseSkeleton()
    assert sp.summon_cap(u) == 2
    assert sp.cast(u, None, m)
    assert sp.cast(u, None, m)
    assert sp.cast(u, None, m) is False


def test_wild_totem_cuts_form_upkeep():
    from items.gear_catalog import make_gear
    from spells.druid import shapeshift as ss
    m = _mgr()
    u = _caster_unit()
    u.max_mana = 300
    u.school_effects = {"shapeshift_rank": 1}
    u.current_mana = 100
    ss.enter_form(u, "bear", m)
    for _ in range(600):    # 10 s
        ss.tick(u, m)
    mana_plain = u.current_mana
    ss.exit_form(u, m)
    # Sama uudestaan wild-totemin upkeep-alennuksella
    u2 = _caster_unit()
    u2.max_mana = 300
    u2.equipment["off_hand"] = make_gear("druid_wild_t6")  # -30% upkeep
    u2.calculate_final_stats()
    u2.school_effects["shapeshift_rank"] = 1
    u2.current_mana = 100
    ss.enter_form(u2, "bear", m)
    for _ in range(600):
        ss.tick(u2, m)
    assert u2.current_mana > mana_plain, "totem alentaa muodon ylläpitoa"


# ----------------------------------------------------------------------
# Portit
# ----------------------------------------------------------------------

def test_relic_requires_relic_proficiency():
    import main  # noqa: F401
    from units.human import Human
    from settings import PLAYER_TEAM
    from items.gear_catalog import make_gear
    u = Human("Grunt", 0, 0, PLAYER_TEAM)
    u.level = 30
    ok, reason = u.can_equip_item_to_slot("off_hand",
                                          make_gear("pure_focus_t1"))
    assert not ok and "elic" in reason


def test_level_req_blocks_high_tier():
    from items.gear_catalog import make_gear
    u = _caster_unit(level=5)
    ok, reason = u.can_equip_item_to_slot("off_hand",
                                          make_gear("pure_focus_t8"))
    assert not ok and "Level" in reason


# ----------------------------------------------------------------------
# Kaupat
# ----------------------------------------------------------------------

def test_school_shops_sell_their_gear():
    from menus.school_spell_shop import (make_radiant_synod,
                                          make_ashen_catalog,
                                          make_prism_catalog)
    m = _mgr()
    holy_names = [getattr(s, "name", "") for s in make_radiant_synod(m).spells]
    assert "Dawnlight Censer" in holy_names
    necro_names = [getattr(s, "name", "") for s in make_ashen_catalog(m).spells]
    assert "Throne of the Restless" in necro_names
    pure_names = [getattr(s, "name", "") for s in make_prism_catalog(m).spells]
    assert "Apprentice Robe" in pure_names, "caster-kaavut Prismistä"


def test_buying_gear_adds_fresh_tiered_gear():
    from menus.school_spell_shop import make_prism_catalog
    from items.tiered_gear import TieredGear
    m = _mgr()
    m.gold = 10 ** 6
    m.modify_faction_rep("prism", 100)
    shop = make_prism_catalog(m)
    idx = next(i for i, s in enumerate(shop.spells)
               if getattr(s, "gear_id", "") == "arcanist_t2")
    shop.selected = idx
    surf = pygame.Surface((1920, 1080))
    shop.draw(surf)
    shop.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=shop._buy_rect.center))
    bought = m.equipment_bag[-1]
    assert isinstance(bought, TieredGear)
    assert bought.gear_id == "arcanist_t2"
    assert bought is not shop.spells[idx], "tuore kopio, ei jaettu instanssi"


def test_gear_rep_gated_like_spells():
    from menus.school_spell_shop import make_ashen_catalog
    m = _mgr()
    m.gold = 10 ** 6
    shop = make_ashen_catalog(m)
    t8 = next(s for s in shop.spells
              if getattr(s, "gear_id", "") == "necro_summoner_t8")
    assert shop._rep_required(t8) == 70
    assert not shop._rep_ok(t8)
    m.modify_faction_rep("ashen", 70)
    assert shop._rep_ok(t8)
