"""Latauserikoisten (systems/charge_specials.py) testit.

Jokaisella aseperheellä on täydestä latauksesta oma erikoinen -
testit varmistavat että ne oikeasti tekevät mitä lupaavat sekä
pelaajan että AI:n koodipolulla (release_charge on yhteinen).
"""
import random

import pygame
import pytest

from settings import PLAYER_TEAM, ENEMY_TEAM


def _unit(x, y, team, weapon=None, mastery=None):
    from units.human import Human
    u = Human("U", x, y, team)
    if weapon is not None:
        u.equipment["main_hand"] = weapon
        if mastery:
            u.weapon_masteries.add(mastery)
    u.equipment["off_hand"] = None
    u.calculate_final_stats()
    u.current_hp = u.max_hp
    u.current_stamina = u.max_stamina
    return u


def _full_charge(weapon):
    weapon.charge_time = weapon.max_charge
    return weapon


def test_axe_whirlwind_hits_all_around(manager):
    from items.axes.weak_axe import WeakAxe
    random.seed(1)
    axe = WeakAxe()
    a = _unit(500, 500, PLAYER_TEAM, axe, "axe")
    e1 = _unit(560, 500, ENEMY_TEAM)   # edessä
    e2 = _unit(440, 500, ENEMY_TEAM)   # TAKANA - normiviilto ei osuisi
    manager.all_units.add(a, e1, e2)
    _full_charge(axe)
    axe.release_charge(a, manager, (560, 500))
    assert e1.current_hp < e1.max_hp, "whirlwind ei osunut eteen"
    assert e2.current_hp < e2.max_hp, "whirlwind ei osunut taakse (360)"


def test_mace_ground_slam_dazes_and_pushes(manager):
    from items.maces.weak_mace import WeakMace
    random.seed(1)
    mace = WeakMace()
    a = _unit(500, 500, PLAYER_TEAM, mace, "mace")
    e = _unit(560, 500, ENEMY_TEAM)
    manager.all_units.add(a, e)
    old_x = e.rect.centerx
    _full_charge(mace)
    mace.release_charge(a, manager, (560, 500))
    assert e.current_hp < e.max_hp
    assert e.stun_timer > 0, "slam ei horjuttanut"
    assert e.rect.centerx > old_x, "slam ei työntänyt kohdetta"


def test_sword_lunge_steps_toward_target(manager):
    from items.swords.weak_sword import WeakSword
    sword = WeakSword()
    a = _unit(500, 500, PLAYER_TEAM, sword, "sword")
    manager.all_units.add(a)
    old_x = a.rect.centerx
    _full_charge(sword)
    sword.release_charge(a, manager, (800, 500))
    assert a.rect.centerx > old_x, "lunge ei astunut kohti"


def test_dagger_fan_spawns_three_knives(manager):
    from items.daggers.weak_dagger import WeakDagger
    dagger = WeakDagger()
    a = _unit(500, 500, PLAYER_TEAM, dagger, "dagger")
    manager.all_units.add(a)
    before = len(manager.vfx.particles)
    _full_charge(dagger)
    dagger.release_charge(a, manager, (800, 500))
    assert len(manager.vfx.particles) - before == 3, "viuhka != 3 veistä"


def test_staff_overload_splashes(manager):
    from systems import charge_specials
    a = _unit(500, 500, PLAYER_TEAM)
    victim = _unit(700, 500, ENEMY_TEAM)
    bystander = _unit(740, 500, ENEMY_TEAM)   # 40 px roiskeen sisällä
    manager.all_units.add(a, victim, bystander)
    proj = charge_specials.ExplosiveBolt.spawn(
        a, manager, (700, 500), 14, 30, 12, (150, 110, 255))
    # Simuloi osuma uhriin
    proj.rect.center = victim.rect.center
    proj.on_hit(victim)
    assert victim.current_hp < victim.max_hp
    assert bystander.current_hp < bystander.max_hp, "roiske ei osunut viereen"


def test_bow_clean_shot_boosts_full_draw(manager):
    from items.bows.weak_bow import WeakBow
    bow = WeakBow()
    a = _unit(500, 500, PLAYER_TEAM, bow, "bow")
    manager.all_units.add(a)
    # Puolilataus
    bow.charge_time = bow.max_charge // 2
    bow.release_charge(a, manager, (900, 500))
    half_dmg = [s for s in manager.vfx.particles.sprites() if hasattr(s, "damage")][-1].damage
    a.attack_cooldown = 0
    # Täysi veto
    _full_charge(bow)
    bow.release_charge(a, manager, (900, 500))
    full_dmg = [s for s in manager.vfx.particles.sprites() if hasattr(s, "damage")][-1].damage
    assert full_dmg > half_dmg * 1.5, (half_dmg, full_dmg)


def test_book_stream_fires_while_held(manager, monkeypatch):
    from items.books.weak_book import WeakBook
    book = WeakBook()
    a = _unit(500, 500, PLAYER_TEAM, book, "book")
    manager.all_units.add(a)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (900, 500))
    before = len(manager.vfx.particles)
    for _ in range(30):   # ~2 x STREAM_INTERVAL
        book.update_charge(a, manager)
    fired = len(manager.vfx.particles) - before
    assert fired >= 2, f"stream ampui vain {fired}"
    # Release streamin jälkeen EI ammu bonuslaukausta
    before2 = len(manager.vfx.particles)
    book.release_charge(a, manager, (900, 500))
    assert len(manager.vfx.particles) == before2

    # Nopea napautus ampuu normaalisti
    a.attack_cooldown = 0
    book._held_frames = 3
    before3 = len(manager.vfx.particles)
    book.release_charge(a, manager, (900, 500))
    assert len(manager.vfx.particles) - before3 == 1
