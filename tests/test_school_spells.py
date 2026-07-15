# tests/test_school_spells.py
"""Pelitesti 32: kolme ensimmäistä koulukohtaista loitsua (entry-taso).
Necro / Holy / Druid saavat kukin yhden toimivan loitsun; Pure (Prism)
pysyy heti-saatavana. Tässä varmistetaan että ne kastautuvat oikein.
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
    p.intelligence = 20
    p.max_mana = 200
    p.current_mana = 200
    p.max_hp = 300
    p.current_hp = 150
    p.rect.center = (500, 500)
    m.current_arena = _Arena()
    m.my_team.empty()
    m.enemy_team.empty()
    m.all_units.empty()
    m.my_team.add(p)
    m.all_units.add(p)
    return m, p


def _tick_vfx(m, n=30):
    for _ in range(n):
        m.vfx.update(obstacles=[])


# ----------------------------------------------------------------------
# Rekisteröinti + koulutagit
# ----------------------------------------------------------------------

def test_school_spells_registered_and_tagged():
    from spells.spell_registry import get_school_spells, ALL_SPELLS
    from spells.necro.raise_skeleton import RaiseSkeleton
    from spells.holy.smite import Smite
    from spells.druid.regrowth import Regrowth
    assert [c.__name__ for c in get_school_spells("necromancy")] == ["RaiseSkeleton"]
    assert [c.__name__ for c in get_school_spells("holy")] == ["Smite"]
    assert [c.__name__ for c in get_school_spells("druidism")] == ["Regrowth"]
    # Koulutagit paikallaan (tuleva porttilogiikka nojaa näihin)
    assert RaiseSkeleton().school == "necromancy"
    assert Smite().school == "holy"
    assert Regrowth().school == "druidism"
    # EIVÄT saa vuotaa Prismin (Pure) satunnaispooliin
    names = [c.__name__ for c in ALL_SPELLS]
    for n in ("RaiseSkeleton", "Smite", "Regrowth"):
        assert n not in names, f"{n} ei kuulu Prismin satunnaispooliin"


# ----------------------------------------------------------------------
# Necro: Raise Skeleton summonaa liittolaisen loitsijan puolelle
# ----------------------------------------------------------------------

def test_raise_skeleton_summons_ally():
    from spells.necro.raise_skeleton import RaiseSkeleton
    m, p = _setup()
    before = len(m.my_team)
    ok = RaiseSkeleton().cast(p, None, m, target_pos=(600, 500))
    assert ok
    skels = [u for u in m.my_team if type(u).__name__ == "UndeadSkeleton"]
    assert len(skels) == 1, "yksi luuranko liittolaisryhmässä"
    assert skels[0] in m.all_units
    assert p.current_mana == 200 - 25


# ----------------------------------------------------------------------
# Holy: Smite tekee tuplavahingon epäkuolleisiin
# ----------------------------------------------------------------------

def test_smite_double_damage_vs_undead():
    from spells.holy.smite import Smite
    from units.rat import GiantRat
    from units.undead_skeleton import UndeadSkeleton
    from settings import ENEMY_TEAM
    # elävä kohde
    m, p = _setup()
    rat = GiantRat("Rat", 640, 500, ENEMY_TEAM)
    rat.max_hp = rat.current_hp = 500
    m.enemy_team.add(rat)
    m.all_units.add(rat)
    hp0 = rat.current_hp
    Smite().cast(p, rat, m, target_pos=rat.rect.center)
    _tick_vfx(m)
    normal = hp0 - rat.current_hp
    # epäkuollut kohde
    m, p = _setup()
    skel = UndeadSkeleton("Bone", 640, 500, ENEMY_TEAM)
    skel.max_hp = skel.current_hp = 500
    m.enemy_team.add(skel)
    m.all_units.add(skel)
    hp0 = skel.current_hp
    Smite().cast(p, skel, m, target_pos=skel.rect.center)
    _tick_vfx(m)
    undead = hp0 - skel.current_hp
    assert normal > 0
    assert undead == normal * 2, "pyhä valo tekee tuplaa epäkuolleisiin"


# ----------------------------------------------------------------------
# Druid: Regrowth parantaa yli ajan (Regen-status)
# ----------------------------------------------------------------------

def test_regrowth_heals_over_time():
    from spells.druid.regrowth import Regrowth
    m, p = _setup()
    p.current_hp = 100
    ok = Regrowth().cast(p, p, m)
    assert ok
    assert any(e["type"] == "Regen" for e in p.status_effects)
    start = p.current_hp
    for _ in range(200):
        p.update([], m)
    assert p.current_hp > start, "Regrowth parantaa yli ajan"


def test_regrowth_does_not_heal_enemy():
    from spells.druid.regrowth import Regrowth
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m, p = _setup()
    enemy = GiantRat("Rat", 560, 500, ENEMY_TEAM)
    enemy.max_hp = 300
    enemy.current_hp = 100
    m.enemy_team.add(enemy)
    m.all_units.add(enemy)
    # Vihollista klikatessa loitsu kääntyy loitsijaan, ei paranna vihollista
    Regrowth().cast(p, enemy, m)
    assert not any(e["type"] == "Regen" for e in enemy.status_effects)
