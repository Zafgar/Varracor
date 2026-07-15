# tests/test_casting.py
"""Pelitesti 37: cast time + interrupt + counterspell -perusta.
Kovemmat loitsut latautuvat; lataus voidaan keskeyttää vahingolla tai
counterilla; juurruttava loitsu keskeytyy liikkeestä; valmistuessaan
loitsu laukeaa.
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


def _caster(m):
    p = m.player_character
    p.intelligence = 40
    p.max_mana = 800
    p.current_mana = 800
    p.rect.center = (400, 500)
    return p


# ----------------------------------------------------------------------
# Cast-metadata: korkea tier saa cast timen, matala on välitön
# ----------------------------------------------------------------------

def test_high_tier_has_cast_time_low_tier_instant():
    from spells.catalog import make_catalog_spell
    assert make_catalog_spell("arcane_dart").cast_time == 0     # tier 1
    sun = make_catalog_spell("sun_flare")                       # tier 8
    assert sun.cast_time > 0
    assert sun.rooted_while_casting is True
    assert sun.counterable is True
    assert "Cast:" in sun.describe()


# ----------------------------------------------------------------------
# Cast charge -> laukeaa vasta valmistuttuaan
# ----------------------------------------------------------------------

def test_cast_time_delays_effect_until_complete():
    from spells.casting import is_casting
    from spells.catalog import make_catalog_spell
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m = _mgr()
    p = _caster(m)
    e = GiantRat("E", 470, 500, ENEMY_TEAM)
    e.max_hp = e.current_hp = 100000
    m.all_units.empty()
    m.all_units.add(p)
    m.all_units.add(e)
    sp = make_catalog_spell("oblivion")  # tier 8, cast_time 90
    hp0 = e.current_hp
    assert sp.cast(p, e, m, target_pos=e.rect.center) is True
    assert is_casting(p), "loitsu latautuu"
    # Puolivälissä ei vielä vahinkoa
    for _ in range(sp.cast_time // 2):
        p.update([], m)
    assert e.current_hp == hp0
    # Latauksen loputtua ammus lähtee ja osuu
    for _ in range(sp.cast_time):
        p.update([], m)
    for _ in range(30):
        m.vfx.update(obstacles=[])
    assert not is_casting(p)
    assert e.current_hp < hp0, "loitsu laukeaa latauksen jälkeen"


# ----------------------------------------------------------------------
# Interrupt: vahinko keskeyttää latauksen
# ----------------------------------------------------------------------

def test_damage_interrupts_cast():
    from spells.casting import is_casting
    from spells.catalog import make_catalog_spell
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m = _mgr()
    p = _caster(m)
    e = GiantRat("E", 700, 500, ENEMY_TEAM)
    e.max_hp = e.current_hp = 100000
    m.all_units.empty()
    m.all_units.add(p)
    m.all_units.add(e)
    sp = make_catalog_spell("sun_flare")
    sp.cast(p, e, m, target_pos=e.rect.center)
    assert is_casting(p)
    ehp0 = e.current_hp
    p.take_damage(20, "Physical", manager=m)   # osuma keskeyttää
    assert not is_casting(p), "vahinko keskeytti latauksen"
    for _ in range(sp.cast_time + 40):
        p.update([], m)
        m.vfx.update(obstacles=[])
    assert e.current_hp == ehp0, "keskeytetty loitsu ei tee vahinkoa"


def test_non_interruptible_survives_damage():
    from spells import casting
    m = _mgr()
    p = _caster(m)
    fired = []
    casting.start_cast(p, None, 30, lambda: fired.append(1),
                       rooted=True, interruptible=False, counterable=True)
    p.take_damage(50, "Physical", manager=m)
    assert casting.is_casting(p), "steady-loitsu ei keskeydy vahingosta"
    for _ in range(30):
        casting.tick_caster(p)
    assert fired == [1]


# ----------------------------------------------------------------------
# Counterspell
# ----------------------------------------------------------------------

def test_counter_cast_interrupts_enemy():
    from spells import casting
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m = _mgr()
    p = _caster(m)
    enemy = GiantRat("Mage", 500, 500, ENEMY_TEAM)
    m.all_units.empty()
    m.all_units.add(p)
    m.all_units.add(enemy)
    fired = []
    casting.start_cast(enemy, None, 60, lambda: fired.append(1),
                       counterable=True)
    countered = casting.counter_cast(p, list(m.all_units), rng=400)
    assert countered is enemy
    assert not casting.is_casting(enemy)
    for _ in range(80):
        casting.tick_caster(enemy)
    assert fired == [], "counteroitu loitsu ei laukea"


def test_counter_respects_uncounterable_and_range():
    from spells import casting
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m = _mgr()
    p = _caster(m)
    e1 = GiantRat("Far", 1800, 500, ENEMY_TEAM)     # kantaman ulkopuolella
    e2 = GiantRat("Immune", 480, 500, ENEMY_TEAM)
    m.all_units.empty()
    for u in (p, e1, e2):
        m.all_units.add(u)
    casting.start_cast(e1, None, 60, lambda: None, counterable=True)
    casting.start_cast(e2, None, 60, lambda: None, counterable=False)
    countered = casting.counter_cast(p, list(m.all_units), rng=400)
    assert countered is None, "ei counteria kantaman ulkop. / uncounterable"
    assert casting.is_casting(e1) and casting.is_casting(e2)


# ----------------------------------------------------------------------
# Rooted: liike keskeyttää juurruttavan latauksen
# ----------------------------------------------------------------------

def test_movement_interrupts_rooted_cast():
    from spells import casting
    m = _mgr()
    p = _caster(m)
    casting.start_cast(p, None, 40, lambda: None, rooted=True)
    assert casting.is_rooted(p)
    assert casting.on_caster_moved(p) is True
    assert not casting.is_casting(p)
