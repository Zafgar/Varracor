"""Aseperheiden identiteetit - jokainen ase tuntuu erilaiselta.

YKSI paikka joka määrittää miten aseperheet eroavat toisistaan
(pelitesti 23: "jokaisen aseen pitää tuntua erilaiselta ja
miellyttävältä"). Gladiator-runko kutsuu näitä hookkeja, joten
PELAAJA JA AI saavat identiteetit automaattisesti samoina.

PERHEIDEN IDENTITEETIT:
  sword    - Kaksintaistelija: ripeä perusrytmi, tasainen. Riposte
             (kaikille melee-aseille): onnistuneen PERFECT PARRYN
             jälkeinen isku tekee +30 %.
  dagger   - Salamurhaaja: SELVÄSTI nopein rytmi, kevyt staminalle,
             BACKSTAB +50 % selästä (kohde katsoo poispäin).
  axe      - Raivopää: hidas ja raskas, GUARD CRUSH - blokin läpi
             menee puolet enemmän ja blokkaajan stamina rasittuu.
  mace     - Murskain: hitain, 20 % DAZE (18 f mini-stun).
  spear    - Etäisyyden herra: pisin melee-range, TIP DAMAGE +15 %
             kaukaa (>45 px) ja osuma työntää kohdetta enemmän.
  fists    - Nyrkkeilijä: erittäin nopea ja halpa, joka 3. peräkkäinen
             osuma horjuttaa (COMBO!).
  bow      - Jännitys: lataus/veto omassa asekoodissa (ennallaan).
  crossbow - Raskas laukaus: pitkä lataus rytmissä (reload-tuntuma).
  staff/book - Loitsijan etäase: kevyt rytmi, kantama tekee eron.
"""

import math

# Perhekohtaiset kertoimet: cd = attack_speed-kerroin (pienempi = nopeampi
# rytmi), dmg = vahinkokompensaatio joka pitää perheen DPS:n kutakuinkin
# ennallaan (RYTMI erottaa perheet, ei raaka DPS - tier-tasapaino säilyy),
# range = lisä attack_rangeen, stamina = lyönnin hintakerroin
FAMILY = {
    "sword":    {"cd": 0.85, "dmg": 1.00, "range": 4,  "stamina": 1.0},
    "dagger":   {"cd": 0.55, "dmg": 0.60, "range": 2,  "stamina": 0.65},
    "axe":      {"cd": 1.15, "dmg": 1.15, "range": 2,  "stamina": 1.15},
    "mace":     {"cd": 1.15, "dmg": 1.15, "range": 2,  "stamina": 1.15},
    "spear":    {"cd": 1.05, "dmg": 1.00, "range": 12, "stamina": 1.0},
    "fists":    {"cd": 0.50, "dmg": 0.60, "range": 0,  "stamina": 0.5},
    "bow":      {"cd": 1.00, "dmg": 1.00, "range": 0,  "stamina": 1.0},
    "crossbow": {"cd": 1.15, "dmg": 1.35, "range": 0,  "stamina": 1.0},
    "staff":    {"cd": 1.00, "dmg": 1.00, "range": 0,  "stamina": 1.0},
    "book":     {"cd": 0.95, "dmg": 1.00, "range": 0,  "stamina": 1.0},
}

POINT_BLANK_DIST = 70     # etäase tekee vähemmän kun kohde on iholla
POINT_BLANK_MULT = 0.6
BACKSTAB_MULT = 1.5
TIP_DAMAGE_MULT = 1.15
TIP_DAMAGE_DIST = 45
RIPOSTE_MULT = 1.3
RIPOSTE_WINDOW = 90       # frameja perfect parrysta
GUARD_CRUSH_BLOCK_CUT = 0.5   # kirves puolittaa blokin tehon
GUARD_CRUSH_STAMINA = 12
DAZE_CHANCE = 0.25
DAZE_FRAMES = 18
FIST_COMBO_HITS = 3
FIST_COMBO_STAGGER = 12
SPEAR_PUSH = 10.0


def _fam(group):
    return FAMILY.get(str(group or ""), {})


def cd_mult(group) -> float:
    return float(_fam(group).get("cd", 1.0))


def range_add(group) -> int:
    return int(_fam(group).get("range", 0))


def stamina_mult(group) -> float:
    return float(_fam(group).get("stamina", 1.0))


def dmg_mult(group) -> float:
    return float(_fam(group).get("dmg", 1.0))


def is_behind(attacker, target) -> bool:
    """Onko hyökkääjä kohteen selän takana (kohde katsoo poispäin)?"""
    if getattr(target, "facing_right", True):
        return attacker.rect.centerx < target.rect.centerx
    return attacker.rect.centerx > target.rect.centerx


def pre_hit_mult(attacker, target, group, manager=None) -> float:
    """Vahinkokerroin ENNEN take_damagea + kelluvat tekstit.

    Kutsutaan gladiator.perform_attack-osumaluupista jokaiselle
    melee-osumalle (pelaaja JA AI).
    """
    mult = 1.0

    # RIPOSTE: perfect parry avaa vastaiskuikkunan (kaikki melee)
    if getattr(attacker, "riposte_timer", 0) > 0:
        attacker.riposte_timer = 0
        mult *= RIPOSTE_MULT
        if manager:
            manager.vfx.show_damage(attacker.rect.centerx,
                                    attacker.rect.top - 35,
                                    "RIPOSTE!", color=(255, 230, 120))

    if group == "dagger" and is_behind(attacker, target):
        mult *= BACKSTAB_MULT
        if manager:
            manager.vfx.show_damage(target.rect.centerx,
                                    target.rect.top - 35,
                                    "BACKSTAB!", color=(255, 120, 120))
    elif group == "spear":
        dist = math.hypot(target.rect.centerx - attacker.rect.centerx,
                          target.rect.centery - attacker.rect.centery)
        if dist > TIP_DAMAGE_DIST:
            mult *= TIP_DAMAGE_MULT

    return mult


def post_hit(attacker, target, group, real_dmg, manager=None):
    """Perheen osumaefekti take_damagen JÄLKEEN (pelaaja JA AI)."""
    import random

    if real_dmg <= 0 or getattr(target, "is_dead", False):
        return

    if group == "mace":
        # Murskaimen DAZE: mini-stun kunnioittaa stun-immuniteettia
        if random.random() < DAZE_CHANCE and \
                getattr(target, "stun_immunity", 0) <= 0:
            target.stun_timer = max(getattr(target, "stun_timer", 0),
                                    DAZE_FRAMES)
            if manager:
                manager.vfx.show_damage(target.rect.centerx,
                                        target.rect.top - 35,
                                        "DAZED", color=(255, 255, 150))
    elif group == "spear":
        # Keihäs pitää etäisyyttä: lisätyöntö osumasta
        if hasattr(target, "check_wall_collision"):
            dx = target.rect.centerx - attacker.rect.centerx
            dy = target.rect.centery - attacker.rect.centery
            l = math.hypot(dx, dy) or 1.0
            target.check_wall_collision(dx / l * SPEAR_PUSH,
                                        dy / l * SPEAR_PUSH, None)
    elif group == "fists":
        # Nyrkkeilijän combo: joka 3. peräkkäinen osuma horjuttaa.
        # Sarja katkeaa jos osumien väli venyy yli 1.5 sekunnin.
        import pygame
        now = pygame.time.get_ticks()
        if now - getattr(attacker, "_fist_last_ms", 0) > 1500:
            attacker._fist_combo = 0
        attacker._fist_last_ms = now
        combo = getattr(attacker, "_fist_combo", 0) + 1
        if combo >= FIST_COMBO_HITS:
            combo = 0
            if getattr(target, "stun_immunity", 0) <= 0:
                target.stun_timer = max(getattr(target, "stun_timer", 0),
                                        FIST_COMBO_STAGGER)
            if manager:
                manager.vfx.show_damage(attacker.rect.centerx,
                                        attacker.rect.top - 35,
                                        "COMBO!", color=(255, 180, 90))
        attacker._fist_combo = combo
