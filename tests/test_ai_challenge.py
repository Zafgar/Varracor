"""AI:n haastavuus (pelitesti 25): kite-suojat ja laumakäytös.

1. ANTI-KITE: skriptattu "kitettäjä" (lyö max-rangesta ja juoksee pois,
   sprintaten) EI saa selvitä ilmaiseksi - AI:n ennakointi (kulman
   leikkaus), syöksyt ja sprintti saavat sen kiinni.
2. LAUMA-APU: kun yhteen osuu, lähellä oleva toimeton liittolainen
   kääntyy hyökkääjää vastaan - vihollisia ei voi nyppiä yksitellen.
3. KIERTOLIIKE: AI ei seiso paikallaan osumien välissä.
"""
import math
import random

import pygame
import pytest

from settings import PLAYER_TEAM, ENEMY_TEAM


def _fighter(x, y, team, weapon=None, mastery=None, quality="Veteran"):
    from units.human import Human
    u = Human("F", x, y, team, quality=quality)
    if weapon is not None:
        u.equipment["main_hand"] = weapon
    u.equipment["off_hand"] = None
    u.calculate_final_stats()
    if mastery:
        u.weapon_masteries.add(mastery)
        u.calculate_final_stats()
    u.current_hp = u.max_hp
    u.current_stamina = u.max_stamina
    return u


def test_hit_and_run_kiter_gets_caught(manager):
    """Kitettäjä (lyö rangesta, juoksee pois sprintillä) ottaa osumia -
    AI:ta ei voi juoksuttaa ilmaiseksi."""
    from items.spears.weak_spear import WeakSpear
    from items.swords.weak_sword import WeakSword
    random.seed(11)
    kiter = _fighter(400, 500, PLAYER_TEAM, WeakSpear(), "spear")
    kiter.ai_controller = None   # skriptattu ohjaus
    chaser = _fighter(700, 500, ENEMY_TEAM, WeakSword(), "sword")
    manager.all_units.add(kiter, chaser)
    manager.match_in_progress = True
    manager.current_arena = None

    for frame in range(3600):
        if kiter.is_dead or chaser.is_dead:
            break
        # KITER-SKRIPTI: lyö jos rangella, muuten juokse POISPÄIN
        dx = chaser.rect.centerx - kiter.rect.centerx
        dy = chaser.rect.centery - kiter.rect.centery
        dist = math.hypot(dx, dy)
        if dist <= kiter.attack_range and kiter.attack_cooldown <= 0:
            kiter.perform_attack(chaser, manager)
        else:
            kiter.set_sprinting(kiter.current_stamina > 10)
            l = dist or 1.0
            kiter.check_wall_collision(-dx / l * kiter.speed,
                                       -dy / l * kiter.speed, None)
        kiter.update(None, manager=manager)
        chaser.run_combat_ai(manager.all_units, None, manager=manager)
        chaser.update(None, manager=manager)
        manager.vfx.update(obstacles=None)

    dmg_taken = kiter.max_hp - kiter.current_hp
    assert dmg_taken >= 20, (
        f"Kitettäjä otti vain {dmg_taken} vahinkoa 60 sekunnissa - "
        "AI:ta voi juoksuttaa ilmaiseksi (ennakointi/dash ei toimi)")


def test_pack_assists_when_ally_attacked(manager):
    """Osuma yhteen herättää lähellä olevan toimettoman liittolaisen."""
    from items.swords.weak_sword import WeakSword
    random.seed(2)
    attacker = _fighter(300, 500, PLAYER_TEAM, WeakSword(), "sword")
    victim = _fighter(600, 500, ENEMY_TEAM)
    buddy = _fighter(700, 500, ENEMY_TEAM)
    manager.all_units.add(attacker, victim, buddy)
    assert buddy.ai_controller is not None
    buddy.ai_controller.current_target = None

    victim.take_damage(10, "Physical", attacker=attacker, manager=manager)
    assert buddy.ai_controller.current_target is attacker, (
        "Lauma-apu ei toiminut - vihollisia voi nyppiä yksi kerrallaan")


def test_pack_assist_ignores_far_allies(manager):
    from items.swords.weak_sword import WeakSword
    attacker = _fighter(300, 500, PLAYER_TEAM, WeakSword(), "sword")
    victim = _fighter(600, 500, ENEMY_TEAM)
    far_buddy = _fighter(1400, 500, ENEMY_TEAM)
    manager.all_units.add(attacker, victim, far_buddy)
    far_buddy.ai_controller.current_target = None
    victim.take_damage(10, "Physical", attacker=attacker, manager=manager)
    assert far_buddy.ai_controller.current_target is not attacker, (
        "Lauma-apu ei saa ylettyä koko kartalle")


def test_ai_orbits_between_swings(manager):
    """AI ei seiso naulattuna kohteen vieressä cooldownin aikana."""
    from items.maces.weak_mace import WeakMace
    random.seed(7)
    ai_unit = _fighter(500, 500, ENEMY_TEAM, WeakMace(), "mace")
    dummy = _fighter(528, 500, PLAYER_TEAM)   # mace-rangen (36) sisällä
    dummy.ai_controller = None
    manager.all_units.add(ai_unit, dummy)
    ai_unit.attack_cooldown = 60   # pakota odotustila
    positions = set()
    for _ in range(50):
        ai_unit.attack_cooldown = max(20, ai_unit.attack_cooldown)  # pysy odottavana
        # Matala stamina ohittaa charge-haaran (jolla AI lataa slamia
        # paikallaan - sekin on liikettä parempi kuin tapissa seisominen,
        # mutta tässä testataan kiertoliikettä)
        ai_unit.current_stamina = 35
        ai_unit.run_combat_ai(manager.all_units, None, manager=manager)
        ai_unit.update(None, manager=manager)
        positions.add(ai_unit.rect.topleft)
    assert len(positions) > 5, (
        "AI seisoo paikallaan osumien välissä - kiertoliike puuttuu")
