# tests/test_spell_catalog.py
"""Pelitesti 34: tier-loitsukatalogi (pari loitsua per tier).
Varmistaa: kaikki kastautuvat kaatumatta, numerot johtuvat tier-perustasta,
korkeampi tier = enemmän vahinkoa, rikas selite, ja Sun Flare on Holy (ei Pure).
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


def _setup():
    import main  # noqa: F401
    from game_manager import GameManager
    m = GameManager()
    p = m.player_character
    p.intelligence = 50
    p.max_mana = 800
    p.current_mana = 800
    p.rect.center = (500, 500)
    m.current_arena = _Arena()
    m.my_team.empty()
    m.enemy_team.empty()
    m.all_units.empty()
    m.my_team.add(p)
    m.all_units.add(p)
    return m, p


def _enemy(m, x=600, hp=100000):
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    e = GiantRat("E", x, 500, ENEMY_TEAM)
    e.max_hp = e.current_hp = hp
    m.enemy_team.add(e)
    m.all_units.add(e)
    return e


def test_catalog_has_spells_each_tier():
    from spells.catalog import CATALOG
    tiers = {}
    for s in CATALOG:
        tiers.setdefault(s["tier"], 0)
        tiers[s["tier"]] += 1
    for t in range(1, 9):
        assert tiers.get(t, 0) >= 2, f"tierillä {t} vähintään pari loitsua"


def test_every_catalog_spell_casts_without_crash():
    from spells.catalog import all_catalog_spells
    for sp in all_catalog_spells():
        m, p = _setup()
        e = _enemy(m)
        ok = sp.cast(p, e, m, target_pos=e.rect.center)
        assert ok, f"{sp.name} ei kastautunut"
        for _ in range(30):
            m.vfx.update(obstacles=[])


def test_damage_increases_with_tier_for_nukes():
    from spells.catalog import all_catalog_spells
    # Kerää yhden kohteen nuke-vahinko per tier
    dmg_by_tier = {}
    for sp in all_catalog_spells():
        if sp.archetype != "nuke":
            continue
        m, p = _setup()
        e = _enemy(m)
        hp0 = e.current_hp
        sp.cast(p, e, m, target_pos=e.rect.center)
        # Aja mahdollinen cast time loppuun (korkeat tierit latautuvat)
        for _ in range(int(getattr(sp, "cast_time", 0)) + 2):
            p.update([], m)
        for _ in range(20):
            m.vfx.update(obstacles=[])
        dmg_by_tier.setdefault(sp.tier, []).append(hp0 - e.current_hp)
    tiers = sorted(dmg_by_tier)
    maxes = [max(dmg_by_tier[t]) for t in tiers]
    assert maxes == sorted(maxes), "nuke-vahinko nousee tierien myötä"
    assert maxes[-1] > maxes[0] * 5, "korkein tier selvästi kovempi"


def test_mana_and_price_scale_with_tier():
    from spells.catalog import make_catalog_spell
    from spells.spell_scaling import tier_mana, tier_price
    dart = make_catalog_spell("arcane_dart")     # tier 1
    obliv = make_catalog_spell("oblivion")       # tier 8
    assert dart.mana_cost == tier_mana(1)
    assert obliv.mana_cost == tier_mana(8)
    assert obliv.cost > dart.cost
    assert obliv.mana_cost > dart.mana_cost


def test_rich_description_has_key_fields():
    from spells.catalog import make_catalog_spell
    desc = make_catalog_spell("flame_wave").describe()
    for token in ("School:", "Type:", "Range:", "Damage:", "Mana:",
                  "Cooldown:", "Price:"):
        assert token in desc, f"selitteestä puuttuu {token}"
    # Flavor-teksti mukana ja monirivinen
    assert len(desc.splitlines()) >= 7


def test_sun_flare_and_sunray_are_holy_not_pure():
    from spells.catalog import make_catalog_spell
    from spells.spell_registry import (get_pure_catalog_spells,
                                        get_catalog_school_spells)
    sf = make_catalog_spell("sun_flare")
    assert sf.school == "holy"
    # Ei Pure-katalogissa
    assert "sun_flare" not in [s.spell_id for s in get_pure_catalog_spells()]
    # Vanha Sun Ray tarjotaan Holyn kautta
    holy_names = [getattr(s, "name", "") for s in get_catalog_school_spells("holy")]
    assert "Sun Ray" in holy_names


def test_heal_archetype_heals_ally():
    # Rakennetaan tilapäinen heal-spell katalogispecistä
    from spells.tiered_spell import TieredSpell
    spec = {"id": "test_mend", "name": "Mend", "tier": 3, "school": "druidism",
            "archetype": "heal", "damage_type": "Nature",
            "flavor": "test"}
    sp = TieredSpell(spec)
    m, p = _setup()
    p.max_hp = 500
    p.current_hp = 100
    assert sp.cast(p, p, m)
    assert p.current_hp > 100
