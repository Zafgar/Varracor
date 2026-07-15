# tests/test_spell_functionality.py
"""Loitsujen toiminnallisuuden tarkistus (pelitesti 31).
Käydään läpi kaikki loitsut duellissa: ei kaadu, tekee vahingon/parannuksen
oikeille kohteille, eikä osu loitsijaan/omiin (AoE-friendly-fire -bugi).
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
    p.dexterity = 15
    p.max_mana = 200
    p.current_mana = 200
    p.max_stamina = 200
    p.current_stamina = 200
    p.rect.center = (500, 500)
    m.current_arena = _Arena()
    return m, p


def _enemy(x=700, hp=500):
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    e = GiantRat("Dummy", x, 500, ENEMY_TEAM)
    e.max_hp = hp
    e.current_hp = hp
    return e


def _tick(m, n=40):
    for _ in range(n):
        m.vfx.update(obstacles=[])


# ----------------------------------------------------------------------
# Fireball ei osu loitsijaan eikä omiin (regressio: AoE-friendly fire)
# ----------------------------------------------------------------------

def test_fireball_aoe_spares_caster_and_allies():
    from spells.lvl_1.fireball import Fireball
    from units.human import Human
    from settings import PLAYER_TEAM, ENEMY_TEAM
    from units.rat import GiantRat
    m, p = _setup()
    ally = Human("Ally", 540, 500, PLAYER_TEAM)
    ally.max_hp = ally.current_hp = 300
    enemy = GiantRat("Enemy", 560, 500, ENEMY_TEAM)
    enemy.max_hp = enemy.current_hp = 300
    m.all_units.empty()
    for u in (p, ally, enemy):
        m.all_units.add(u)
    php, ahp, ehp = p.current_hp, ally.current_hp, enemy.current_hp
    Fireball().cast(p, enemy, m, target_pos=enemy.rect.center)
    _tick(m, 30)
    assert p.current_hp == php, "loitsija ei saa vahingoittua omasta fireballista"
    assert ally.current_hp == ahp, "omat eivät kärsi fireballista"
    assert enemy.current_hp < ehp, "vihollinen kärsii räjähdyksestä"


# ----------------------------------------------------------------------
# Kaikki loitsut kastautuvat kaatumatta ja tekevät vahingon/parannuksen
# ----------------------------------------------------------------------

def test_all_offensive_spells_hit_enemy():
    from spells.commander.seam_cut import SeamCut
    from spells.commander.rift_pulse import RiftPulse
    from spells.lvl_1.fireball import Fireball
    from spells.lvl_1.lightning import LightningBolt
    from spells.lvl_2.pyroblast import Pyroblast
    from spells.lvl_2.life_drain import LifeDrain
    from spells.lvl_8.sun_ray import SunRay
    # (spell, enemy_distance) - RiftPulse on lyhyen kantaman ympärispulssi
    cases = [
        ("Vortex Slash", SeamCut(), 200),
        ("Rift Pulse", RiftPulse(), 90),
        ("Fireball", Fireball(), 200),
        ("Lightning", LightningBolt(), 200),
        ("Pyroblast", Pyroblast(), 200),
        ("Life Drain", LifeDrain(), 200),
        ("Sun Ray", SunRay(), 200),
    ]
    for name, spell, dist in cases:
        m, p = _setup()
        e = _enemy(x=500 + dist)
        m.all_units.empty()
        m.all_units.add(p)
        m.all_units.add(e)
        hp0 = e.current_hp
        try:
            ok = spell.cast(p, e, m, target_pos=e.rect.center)
        except TypeError:
            ok = spell.cast(p, e, m)
        _tick(m, 60)
        assert ok, f"{name} ei kastautunut"
        assert e.current_hp < hp0, f"{name} ei tehnyt vahinkoa"


def test_minor_heal_restores_ally_hp():
    from spells.lvl_1.heal import MinorHeal
    m, p = _setup()
    p.max_hp = 500
    p.current_hp = 100
    ok = MinorHeal().cast(p, p, m)
    assert ok
    assert p.current_hp > 100, "Minor Heal palauttaa HP:ta"


def test_rift_pulse_pushes_enemy_and_spares_allies():
    from spells.commander.rift_pulse import RiftPulse
    from units.human import Human
    from settings import PLAYER_TEAM, ENEMY_TEAM
    from units.rat import GiantRat
    m, p = _setup()
    enemy = GiantRat("Enemy", 580, 500, ENEMY_TEAM)
    enemy.max_hp = enemy.current_hp = 300
    ally = Human("Ally", 560, 500, PLAYER_TEAM)
    ally.max_hp = ally.current_hp = 300
    m.all_units.empty()
    for u in (p, ally, enemy):
        m.all_units.add(u)
    ex0 = enemy.rect.centerx
    ahp = ally.current_hp
    RiftPulse().cast(p, None, m)
    assert enemy.rect.centerx > ex0, "vihollinen sinkoutuu poispäin"
    assert ally.current_hp == ahp, "oma ei kärsi Rift Pulsesta"


# ----------------------------------------------------------------------
# INT-skaalaus: jokainen vahinko/parannus = base + INT*kerroin
# (regressio: Life Drain ja Sun Ray skaalasivat ennen kiinteällä luvulla)
# ----------------------------------------------------------------------

def _channel_damage(spell, int_val, frames=120):
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m, p = _setup()
    p.intelligence = int_val
    p.max_hp = 400
    p.current_hp = 200
    e = GiantRat("Dummy", 640, 500, ENEMY_TEAM)
    e.max_hp = e.current_hp = 3000
    m.all_units.empty()
    m.all_units.add(p)
    m.all_units.add(e)
    hp0 = e.current_hp
    spell.cast(p, e, m)
    _tick(m, frames)
    return hp0 - e.current_hp


def test_life_drain_scales_with_int():
    from spells.lvl_2.life_drain import LifeDrain
    low = _channel_damage(LifeDrain(), 10)
    high = _channel_damage(LifeDrain(), 40)
    assert low > 0
    assert high > low, "Life Drain skaalaa INT:llä (ei kiinteä 5)"


def test_sun_ray_scales_with_int():
    from spells.lvl_8.sun_ray import SunRay
    low = _channel_damage(SunRay(), 10)
    high = _channel_damage(SunRay(), 40)
    assert low > 0
    assert high > low, "Sun Ray skaalaa INT:llä (ei kiinteä 12)"
