# tests/test_school_wiring.py
"""Pelitesti 40: koulu-erikoistumisten kytkentä loitsuihin + druidin muodot.
1) Summon-cap: perusraja 1, Summoner-nodet nostavat; AI ei casta capin yli
   (mutta korvaa heikon <35% HP summonin uudella)
2) Grave Legion (summon_tier) vahvistaa luurankoja
3) Life Steal: necro-loitsun vahingosta osa loitsijalle
4) hot_power/heal_power vahvistavat parannuksia
5) Muodonmuutos: karhu-tank, mana-drain, HP-säännöt, cooldown paluusta,
   kuolettava osuma murtaa muodon (ei tapa druidia)
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


def _caster(m, **effects):
    p = m.player_character
    p.intelligence = 30
    p.max_mana = 300
    p.current_mana = 300
    p.max_hp = 400
    p.current_hp = 400
    p.rect.center = (500, 500)
    p.school_effects = dict(effects)
    m.my_team.empty()
    m.enemy_team.empty()
    m.all_units.empty()
    m.my_team.add(p)
    m.all_units.add(p)
    return p


# ----------------------------------------------------------------------
# 1) Summon-cap ja AI-järki
# ----------------------------------------------------------------------

def test_summon_cap_base_is_one_and_second_cast_refused():
    from spells.necro.raise_skeleton import RaiseSkeleton
    m = _mgr()
    p = _caster(m)   # ei nodeja -> cap 1
    sp = RaiseSkeleton()
    assert sp.cast(p, None, m) is True
    mana_after = p.current_mana
    assert sp.cast(p, None, m) is False, "cap täynnä -> ei uutta castia"
    assert p.current_mana == mana_after, "hylätty cast ei kuluta manaa"
    assert len(sp.living_summons(p, m)) == 1


def test_summoner_nodes_raise_cap():
    from spells.necro.raise_skeleton import RaiseSkeleton
    m = _mgr()
    p = _caster(m, summon_max=2)   # cap 3
    sp = RaiseSkeleton()
    assert sp.cast(p, None, m)
    assert sp.cast(p, None, m)
    assert sp.cast(p, None, m)
    assert sp.cast(p, None, m) is False
    assert len(sp.living_summons(p, m)) == 3


def test_low_hp_summon_gets_replaced():
    from spells.necro.raise_skeleton import RaiseSkeleton
    m = _mgr()
    p = _caster(m)   # cap 1
    sp = RaiseSkeleton()
    sp.cast(p, None, m)
    old = sp.living_summons(p, m)[0]
    old.current_hp = int(old.max_hp * 0.2)   # alle 35% -> korvattavissa
    assert sp.cast(p, None, m) is True, "heikko summon korvataan uudella"
    alive = sp.living_summons(p, m)
    assert len(alive) == 1
    assert alive[0] is not old
    assert old.is_dead


def test_grave_legion_strengthens_summons():
    from spells.necro.raise_skeleton import RaiseSkeleton
    m = _mgr()
    p = _caster(m, summon_tier=1)
    RaiseSkeleton().cast(p, None, m)
    s = RaiseSkeleton.living_summons(p, m)[0]
    assert s.max_hp == 90, "tier 1 -> 90 HP (perus 45)"


# ----------------------------------------------------------------------
# 3) Life Steal
# ----------------------------------------------------------------------

def test_necro_spell_lifesteal():
    from spells.catalog import make_catalog_spell
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m = _mgr()
    p = _caster(m, lifesteal_pct=0.40)
    p.current_hp = 100
    e = GiantRat("E", 580, 500, ENEMY_TEAM)
    e.max_hp = e.current_hp = 5000
    m.enemy_team.add(e)
    m.all_units.add(e)
    sp = make_catalog_spell("grave_touch")   # necromancy dot
    sp.cast(p, e, m, target_pos=e.rect.center)
    for _ in range(40):
        m.vfx.update(obstacles=[])
    assert p.current_hp > 100, "necro-loitsu varastaa elämää loitsijalle"


# ----------------------------------------------------------------------
# 4) hot_power / heal_power
# ----------------------------------------------------------------------

def test_hot_power_boosts_regrowth():
    from spells.druid.regrowth import Regrowth
    m = _mgr()
    p = _caster(m)
    Regrowth().cast(p, p, m)
    base_per = next(e["dmg"] for e in p.status_effects
                    if e["type"] == "Regen")
    p.status_effects.clear()
    p.school_effects = {"hot_power": 3}
    p.current_mana = 300
    Regrowth().cast(p, p, m)
    boosted = next(e["dmg"] for e in p.status_effects
                   if e["type"] == "Regen")
    assert boosted > base_per, "hot_power kasvattaa HoT-tikkiä"


def test_heal_power_boosts_tiered_heal():
    from spells.tiered_spell import TieredSpell
    spec = {"id": "t_mend", "name": "Mend", "tier": 3, "school": "holy",
            "archetype": "heal", "damage_type": "Holy", "flavor": "t"}
    m = _mgr()
    p = _caster(m)
    p.current_hp = 50
    TieredSpell(spec).cast(p, p, m)
    healed_base = p.current_hp - 50
    p.current_hp = 50
    p.current_mana = 300
    p.school_effects = {"heal_power": 2}
    TieredSpell(spec).cast(p, p, m)
    healed_boost = p.current_hp - 50
    assert healed_boost > healed_base


# ----------------------------------------------------------------------
# 5) Muodonmuutos
# ----------------------------------------------------------------------

def test_bear_form_is_tank_and_maps_hp_proportionally():
    from spells.druid import shapeshift as ss
    m = _mgr()
    p = _caster(m, shapeshift_rank=1)
    p.current_hp = 200   # 50% druidin 400:sta
    str0, def0, max0 = p.strength, p.defense, p.max_hp
    assert ss.enter_form(p, "bear", m)
    assert p.max_hp == int(max0 * 2.2), "karhu on tosi tank (HP x2.2)"
    assert abs(p.current_hp - int(p.max_hp * 0.5)) <= 1, \
        "muodon HP määräytyy druidin sen hetkisen HP:n mukaan"
    assert p.strength == str0 + 15 and p.defense == def0 + 6
    assert p.image is not None and p.image.get_width() > 0


def test_form_drains_mana_and_reverts_to_entry_hp():
    from spells.druid import shapeshift as ss
    m = _mgr()
    p = _caster(m, shapeshift_rank=1)
    p.current_hp = 300
    p.current_mana = 12   # juuri ja juuri sisään; drain lopettaa pian
    assert ss.enter_form(p, "bear", m)
    for _ in range(200):
        ss.tick(p, m)
        if not ss.in_form(p):
            break
    assert not ss.in_form(p), "mana loppui -> muoto purkautuu"
    assert p.current_hp == 300, "druid palaa entry-HP:hen"
    assert p.shapeshift_cooldown > 0, "cooldown alkaa paluusta"


def test_cooldown_blocks_reentry():
    from spells.druid import shapeshift as ss
    m = _mgr()
    p = _caster(m, shapeshift_rank=1)
    ss.enter_form(p, "bear", m)
    ss.exit_form(p, m)
    ok, why = ss.can_enter(p, "bear")
    assert not ok and "cooldown" in why.lower()


def test_lethal_damage_breaks_form_not_druid():
    from spells.druid import shapeshift as ss
    m = _mgr()
    p = _caster(m, shapeshift_rank=1)
    p.current_hp = 250
    ss.enter_form(p, "bear", m)
    p.take_damage(999999, "Physical", manager=m)
    assert not ss.in_form(p), "kuolettava osuma murtaa muodon"
    assert not p.is_dead, "druid EI kuole muodon murtuessa"
    assert p.current_hp == 250, "palaa entry-HP:hen"


def test_rank_gates_higher_forms():
    from spells.druid import shapeshift as ss
    m = _mgr()
    p = _caster(m, shapeshift_rank=1)
    ok, why = ss.can_enter(p, "dragon")
    assert not ok and "rank" in why.lower(), "lohikäärme vaatii korkean rankin"


def test_form_spells_sold_in_druid_shop():
    from spells.spell_registry import get_catalog_school_spells
    names = [getattr(s, "name", "") for s in
             get_catalog_school_spells("druidism")]
    assert "Bear Form" in names
    assert "Dragon Whelp Form" in names
