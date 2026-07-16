"""Latauserikoiset (hold LMB) - keskitetyt toteutukset.

Pelaaja viettää suurimman osan ajasta näiden aseiden kanssa, joten
TÄYSI LATAUS palkitaan aina jollain näyttävällä ja perheen identiteetin
mukaisella (pelitesti 23). Asetiedostot (weak_/scrap_) kutsuvat näitä
yhdellä rivillä - yksi toteutus per erikoinen, ei kopioita.

AI käyttää samoja erikoisia automaattisesti: base_ai:n charge-logiikka
lataa täyteen ja releasettaa, jolloin sama koodipolku ajetaan.

ERIKOISET:
  sword  LUNGE SLASH   - askel eteen + raskas viilto (syöksyvä painike)
  axe    WHIRLWIND     - 360-asteen pyörähdys, osuu KAIKKIIN ympärillä
  mace   GROUND SLAM   - maaisku: aalto vahingoittaa, horjuttaa ja
                         työntää kaikkia lähellä
  dagger FAN OF KNIVES - kolmen veitsen viuhka
  staff  OVERLOAD      - räjähtävä ammus: osumasta roiskevahinko
  bow    CLEAN SHOT    - täysi veto: +25 % ja nopein nuoli
  book   ARCANE STREAM - pohjassa pito suoltaa pikkusalamia (pelaaja)
"""

import math
import random

import pygame

from sound_manager import sound_system

WHIRLWIND_RADIUS = 90
WHIRLWIND_MULT = 1.5
SLAM_RADIUS = 105
SLAM_MULT = 1.2
SLAM_DAZE = 20
SLAM_PUSH = 22.0
LUNGE_STEP = 30.0
LUNGE_MULT = 2.4
FAN_KNIVES = 3
FAN_SPREAD = 0.22        # radiaania per veitsi
CLEAN_SHOT_MULT = 1.25
STREAM_INTERVAL = 13     # frameja per streamin salama
STREAM_DMG_MULT = 0.45
STREAM_STAMINA = 2.0


def _enemies_near(owner, manager, radius):
    out = []
    if not manager:
        return out
    for u in manager.all_units:
        if u is owner or getattr(u, "is_dead", False):
            continue
        if hasattr(owner, "is_ally") and owner.is_ally(u):
            continue
        d = math.hypot(u.rect.centerx - owner.rect.centerx,
                       u.rect.centery - owner.rect.centery)
        if d <= radius:
            out.append(u)
    return out


def _player_feedback(owner, manager, shake, stop=0):
    if manager and owner is getattr(manager, "player_character", None):
        manager.trigger_screen_shake(shake)
        if stop:
            manager.trigger_hit_stop(stop)


def whirlwind(owner, weapon, manager, target_pos):
    """KIRVES: pyörähdysisku - osuu kaikkiin ympärillä olevin."""
    stats = {"str": owner.strength, "dex": owner.dexterity,
             "int": owner.intelligence}
    dmg = int(weapon.calculate_damage(stats) * WHIRLWIND_MULT)
    owner.animation_state = "attack"
    owner.animation_timer = 15
    owner.attack_cooldown = int(owner.attack_speed * 1.2)
    owner.current_stamina = max(0, owner.current_stamina - 18)
    sound_system.play_sound("attack_melee")
    if manager:
        manager.vfx.show_damage(owner.rect.centerx, owner.rect.top - 40,
                                "WHIRLWIND!", color=(255, 170, 90))
        try:
            for i in range(8):
                a = math.tau * i / 8.0
                manager.vfx.create_impact_sparks(
                    owner.rect.centerx + math.cos(a) * 50,
                    owner.rect.centery + math.sin(a) * 50,
                    color=(230, 190, 120), count=4)
        except Exception:
            pass
    hit_any = False
    for u in _enemies_near(owner, manager, WHIRLWIND_RADIUS):
        real = u.take_damage(dmg, "Physical", attacker=owner, manager=manager)
        owner.stats["damage"] += int(real)
        hit_any = hit_any or real > 0
    _player_feedback(owner, manager, 6, stop=4 if hit_any else 0)


def ground_slam(owner, weapon, manager, target_pos):
    """NUIJA: maaisku - aalto vahingoittaa, horjuttaa ja työntää."""
    stats = {"str": owner.strength, "dex": owner.dexterity,
             "int": owner.intelligence}
    dmg = int(weapon.calculate_damage(stats) * SLAM_MULT)
    owner.animation_state = "attack"
    owner.animation_timer = 18
    owner.attack_cooldown = int(owner.attack_speed * 1.3)
    owner.current_stamina = max(0, owner.current_stamina - 22)
    sound_system.play_sound("attack_melee")
    if manager:
        manager.vfx.show_damage(owner.rect.centerx, owner.rect.top - 40,
                                "SLAM!", color=(255, 230, 120))
        try:
            for i in range(12):
                a = math.tau * i / 12.0
                manager.vfx.create_impact_sparks(
                    owner.rect.centerx + math.cos(a) * 70,
                    owner.rect.centery + math.sin(a) * 70,
                    color=(200, 180, 140), count=3)
        except Exception:
            pass
    for u in _enemies_near(owner, manager, SLAM_RADIUS):
        real = u.take_damage(dmg, "Physical", attacker=owner, manager=manager)
        owner.stats["damage"] += int(real)
        if real > 0:
            if getattr(u, "stun_immunity", 0) <= 0:
                u.stun_timer = max(getattr(u, "stun_timer", 0), SLAM_DAZE)
            if hasattr(u, "check_wall_collision"):
                dx = u.rect.centerx - owner.rect.centerx
                dy = u.rect.centery - owner.rect.centery
                l = math.hypot(dx, dy) or 1.0
                u.check_wall_collision(dx / l * SLAM_PUSH,
                                       dy / l * SLAM_PUSH, None)
    _player_feedback(owner, manager, 8, stop=5)


def lunge_slash(owner, weapon, manager, target_pos):
    """MIEKKA: syöksyviilto - askel eteen + raskas isku."""
    dx = target_pos[0] - owner.rect.centerx
    dy = target_pos[1] - owner.rect.centery
    l = math.hypot(dx, dy) or 1.0
    obs = None
    if manager and getattr(manager, "current_arena", None):
        obs = getattr(manager.current_arena, "obstacles", None)
    owner.check_wall_collision(dx / l * LUNGE_STEP, dy / l * LUNGE_STEP, obs)
    if manager:
        manager.vfx.show_damage(owner.rect.centerx, owner.rect.top - 40,
                                "LUNGE!", color=(160, 230, 255))
    owner.perform_attack(None, manager, damage_mult=LUNGE_MULT,
                         target_pos=target_pos)
    _player_feedback(owner, manager, 6)


def fan_of_knives(owner, weapon, manager, target_pos, throw_dmg, speed,
                  proj_img):
    """TIKARI: kolmen veitsen viuhka täydestä latauksesta."""
    from vfx import Projectile
    base = math.atan2(target_pos[1] - owner.rect.centery,
                      target_pos[0] - owner.rect.centerx)
    dist = max(120.0, math.hypot(target_pos[0] - owner.rect.centerx,
                                 target_pos[1] - owner.rect.centery))
    if manager:
        manager.vfx.show_damage(owner.rect.centerx, owner.rect.top - 40,
                                "FAN OF KNIVES!", color=(255, 140, 140))
    for i in range(FAN_KNIVES):
        a = base + (i - FAN_KNIVES // 2) * FAN_SPREAD
        tp = (owner.rect.centerx + math.cos(a) * dist,
              owner.rect.centery + math.sin(a) * dist)
        proj = Projectile(owner.rect.centerx, owner.rect.centery, tp,
                          speed, int(throw_dmg * 0.8), owner, manager,
                          image=proj_img)
        if manager:
            manager.vfx.add_projectile(proj)
    _player_feedback(owner, manager, 4)


class ExplosiveBolt:
    """SAUVA: räjähtävä ammus - osumasta roiskevahinko ympärille.
    Kääre joka rakentaa MagicProjectilen ja lisää räjähdyksen on_hitiin."""

    @staticmethod
    def spawn(owner, manager, target_pos, speed, dmg, size, color,
              splash_radius=70, splash_mult=0.5):
        from vfx import MagicProjectile
        proj = MagicProjectile(owner.rect.centerx, owner.rect.centery,
                               target_pos, speed, dmg, owner, manager,
                               color=color, size=size)
        original_on_hit = proj.on_hit

        def exploding_hit(target):
            original_on_hit(target)
            if manager:
                manager.vfx.show_damage(proj.rect.centerx,
                                        proj.rect.centery - 20,
                                        "OVERLOAD!", color=(190, 150, 255))
                try:
                    manager.vfx.create_impact_sparks(
                        proj.rect.centerx, proj.rect.centery,
                        color=color, count=14)
                except Exception:
                    pass
                manager.trigger_screen_shake(4)
                splash = int(dmg * splash_mult)
                for u in manager.all_units:
                    if u is owner or u is target or getattr(u, "is_dead", False):
                        continue
                    if hasattr(owner, "is_ally") and owner.is_ally(u):
                        continue
                    d = math.hypot(u.rect.centerx - proj.rect.centerx,
                                   u.rect.centery - proj.rect.centery)
                    if d <= splash_radius:
                        u.take_damage(splash, "Magic", attacker=owner,
                                      manager=manager)

        proj.on_hit = exploding_hit
        if manager:
            manager.vfx.add_projectile(proj)
        return proj


def stream_bolt(owner, weapon, manager, frame_counter):
    """KIRJA: Arcane Stream - pohjassa pito suoltaa pikkusalamia.
    Kutsutaan update_chargesta joka frame; ampuu STREAM_INTERVAL välein.
    Palauttaa päivitetyn laskurin."""
    owner.is_charging = True
    owner.temp_speed_mult = 0.6
    frame_counter += 1
    if frame_counter < STREAM_INTERVAL:
        return frame_counter
    if owner.current_stamina < STREAM_STAMINA:
        return 0
    owner.current_stamina -= STREAM_STAMINA
    from vfx import MagicProjectile
    mx, my = pygame.mouse.get_pos()
    if manager:
        mx += getattr(manager, "camera_x", 0)
        my += getattr(manager, "camera_y", 0)
    # Kevyt hajonta - stream tuntuu energiselta, ei laserilta
    a = math.atan2(my - owner.rect.centery, mx - owner.rect.centerx)
    a += random.uniform(-0.06, 0.06)
    dist = max(120.0, math.hypot(mx - owner.rect.centerx,
                                 my - owner.rect.centery))
    tp = (owner.rect.centerx + math.cos(a) * dist,
          owner.rect.centery + math.sin(a) * dist)
    stats = {"int": owner.intelligence}
    dmg = max(1, int(weapon.calculate_damage(stats) * STREAM_DMG_MULT))
    proj = MagicProjectile(owner.rect.centerx, owner.rect.centery, tp,
                           18, dmg, owner, manager,
                           color=(170, 130, 255), size=5)
    if manager:
        manager.vfx.add_projectile(proj)
    sound_system.play_sound("book_1")
    return 0
