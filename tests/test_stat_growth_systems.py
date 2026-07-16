# tests/test_stat_growth_systems.py
"""Pelitesti 41: statikasvun perusta.
1) Statikäyrä: kymmeniä lvl 5, ~50-80 lvl 10, ~250 lvl 15, 500+ lvl 20,
   1000+ lvl 30 (sileä potenssikaava)
2) Skill-puun statinodet ovat nyt PROSENTTEJA jotka kertovat myös gearin
   antamat statit (statit tulevat pääosin varusteista)
3) Koulutuskoulu: pelipäivät antavat statteja, päivämaksu/etukäteisjakso,
   reputation avaa paremmat tasot
4) Loitsukaupat: korkeampi tier vaatii koulun mainetta
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


def _mgr():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def _unit(level=5):
    from units.human import Human
    from settings import PLAYER_TEAM
    u = Human("Trainee", 0, 0, PLAYER_TEAM)
    u.level = level
    u.skill_points = 40
    return u


# ----------------------------------------------------------------------
# 1) Statikäyrä
# ----------------------------------------------------------------------

def test_stat_curve_waypoints():
    from progression.stat_curve import stat_target
    assert 10 <= stat_target(5) <= 40, "lvl 5: kymmeniä"
    assert 40 <= stat_target(10) <= 120, "lvl 10: ~50-100"
    assert 180 <= stat_target(15) <= 320, "lvl 15: ~250"
    assert 400 <= stat_target(20) <= 700, "lvl 20: 500-600"
    assert stat_target(30) >= 1000, "lvl 30: 1000+"
    # Sileä ja monotoninen
    vals = [stat_target(l) for l in range(1, 31)]
    assert vals == sorted(vals)


def test_daily_training_gain_scales_with_level():
    from progression.stat_curve import daily_training_gain
    assert daily_training_gain(5) >= 1
    assert daily_training_gain(20) > daily_training_gain(5)
    assert daily_training_gain(20, 2.2) > daily_training_gain(20, 1.0)


# ----------------------------------------------------------------------
# 2) Prosenttinodet kertovat gear-statit
# ----------------------------------------------------------------------

def test_tree_pct_multiplies_gear_stats():
    import main  # noqa: F401
    from skills.skill_system import unlock_skill
    u = _unit()
    u.calculate_final_stats()
    base_str = u.strength
    # Simuloi isot gear-statit (statit tulevat pääosin varusteista)
    class _BigGear:
        name = "Trainer Plate"
        slot_type = "body"
        type = "armor"
        defense = 0
        str_bonus = 200
    u.equipment["body"] = _BigGear()
    u.calculate_final_stats()
    with_gear = u.strength
    assert with_gear >= base_str + 200
    # Might-node on nyt +10% STR -> kertoo MYÖS gearin 200
    ok, msg = unlock_skill(u, "might")
    if not ok:  # node-id voi olla eri - etsi str_pct-node
        from skills.skills_data import SKILL_TREE
        nid = next(k for k, v in SKILL_TREE.items()
                   if v.get("effects", {}).get("str_pct") and
                   not v.get("requires"))
        ok, msg = unlock_skill(u, nid)
    assert ok, msg
    u.calculate_final_stats()
    assert u.strength >= int(with_gear * 1.09), \
        "prosenttinode kertoo gear-statit (ei vain +5)"


# ----------------------------------------------------------------------
# 3) Koulutuskoulu
# ----------------------------------------------------------------------

def test_training_prepaid_period_gains_and_graduates():
    from systems import training_school as ts
    m = _mgr()
    u = _unit(level=10)
    m.gold = 10000
    int0 = None
    u.calculate_final_stats()
    int0 = u.intelligence
    ok, msg = ts.enroll(m, u, "int", tier="basic", days=5)
    assert ok, msg
    gold_after_prepay = m.gold
    assert gold_after_prepay == 10000 - ts.daily_cost(u, "basic") * 5
    # 5 pelipäivää
    for _ in range(5):
        m.world_clock.advance_day()
    assert u.in_training is None, "jakso päättyi -> valmistui"
    assert m.gold == gold_after_prepay, "etukäteisjakso ei veloita lisää"
    u.calculate_final_stats()
    assert u.intelligence > int0, "koulutus kasvatti INT:iä"


def test_training_daily_payment_stops_when_broke():
    from systems import training_school as ts
    m = _mgr()
    u = _unit(level=10)
    cost = ts.daily_cost(u, "basic")
    m.gold = cost * 2  # rahat riittävät 2 päivään
    ok, _ = ts.enroll(m, u, "str", tier="basic", days=None)
    assert ok
    m.world_clock.advance_day()
    m.world_clock.advance_day()
    assert u.in_training is not None
    m.world_clock.advance_day()   # 3. päivä: ei varaa -> koulutus loppuu
    assert u.in_training is None, "rahaton -> koulutus keskeytyy"


def test_training_tier_gated_by_reputation():
    from systems import training_school as ts
    m = _mgr()
    u = _unit(level=8)
    m.gold = 100000
    m.reputation = 0
    ok, msg = ts.enroll(m, u, "str", tier="elite")
    assert not ok and "eputation" in msg
    m.reputation = 25
    ok, _ = ts.enroll(m, u, "str", tier="elite")
    assert ok
    assert "elite" in ts.available_tiers(m)


def test_cannot_double_enroll():
    from systems import training_school as ts
    m = _mgr()
    u = _unit()
    m.gold = 100000
    assert ts.enroll(m, u, "str")[0]
    ok, msg = ts.enroll(m, u, "int")
    assert not ok and "already" in msg


# ----------------------------------------------------------------------
# 4) Loitsukauppojen reputation-portit
# ----------------------------------------------------------------------

def test_shop_rep_gates_high_tier_spells():
    from menus.school_spell_shop import make_radiant_synod
    m = _mgr()
    m.gold = 10 ** 6
    shop = make_radiant_synod(m)
    # Sun Flare on tier 8 -> vaatii 70 radiant-mainetta
    sf = next(s for s in shop.spells if getattr(s, "name", "") == "Sun Flare")
    assert shop._rep_required(sf) == 70
    assert not shop._rep_ok(sf)
    n0 = len(m.equipment_bag)
    shop._buy(sf)
    assert len(m.equipment_bag) == n0, "ilman mainetta ei voi ostaa"
    m.modify_faction_rep("radiant", 70)
    assert shop._rep_ok(sf)
    shop._buy(sf)
    assert len(m.equipment_bag) == n0 + 1, "maine avaa oston"


def test_tier1_spells_free_of_rep():
    from menus.school_spell_shop import make_prism_catalog
    m = _mgr()
    shop = make_prism_catalog(m)
    t1 = next(s for s in shop.spells if getattr(s, "tier", 0) == 1)
    assert shop._rep_required(t1) == 0
    assert shop._rep_ok(t1)
