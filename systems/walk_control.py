"""Yhtenäinen kävelytilan ohjaus (kaupungit, sisätilat, rauhalliset tiet).

PELAAJAN OHJAUKSEN AUKTORITEETIT - näitä on tasan kaksi:

  1. TAISTELUTILA: Commander.run_combat_ai (units/commander.py).
     Kaikki GameplayScreen-pohjaiset näytöt kutsuvat sitä. Se lukee
     keybinds-asettelun, hoitaa liikkeen, sprintin, dashin, blockin,
     loitsut, huudot ja input-vuotojen estot.

  2. KÄVELYTILA: tämä moduuli. Kaikki näytöt joissa liikutaan ilman
     taistelua (kaupungit, taverna, paja, kanaalit, metsätien
     kävelyosuus) kutsuvat move_player()-funktiota, jotta säännöt ovat
     identtiset joka paikassa:
       - nopeus WALK_SPEED (4.0), sprintti x1.5 joka kuluttaa staminaa
         VAIN liikkuessa
       - diagonaaliliike normalisoitu (ei nopeampaa vinottain)
       - näppäimet keybinds-asettelusta (rebind toimii kaikkialla)
       - sprintti ilman suuntanäppäimiä juoksuttaa hiirtä kohti
       - dash ei keskeydy (Gladiator.update liikuttaa dashin aikana)
       - kääntyminen liikesuunnan mukaan
       - per-akseli törmäys esteisiin TAI walkable-aluetarkistus
       - käynnissä oleva lyönti-/keräysanimaatio saa pyöriä loppuun

ÄLÄ kirjoita näyttöön omaa WASD-luuppia tai kovakoodattua K_SPACE-dashia -
tests/test_walk_control.py vahtii tätä.
"""

import math

import pygame

from systems import keybinds

WALK_SPEED = 4.0
SPRINT_MULT = 1.5
MOUSE_SPRINT_DEADZONE = 40


def move_player(player, *, obstacles=None, walkable=None, bounds=None,
                camera=(0, 0), mouse_sprint=True):
    """Liikuta pelaajaa kävelytilassa yhtenäisillä säännöillä.

    obstacles:   iteroitava objekteista joilla .rect (per-akseli työntö)
    walkable:    callable(rect) -> bool (aluepohjainen tarkistus; jos
                 annettu, käytetään esteiden sijaan)
    bounds:      pygame.Rect johon pelaaja rajataan (esim. areenan koko)
    camera:      (x, y) -offset hiirisprinttiä varten
    mouse_sprint: sprintti ilman suuntanäppäimiä juoksuttaa hiirtä kohti

    Palauttaa True jos pelaaja liikkui. Kutsuja hoitaa player.update():n
    (näytöt antavat sille eri este-/manager-parametrit).
    """
    keys = pygame.key.get_pressed()
    wants_sprint = keybinds.pressed(keys, "sprint")

    dx = dy = 0.0
    if not getattr(player, "is_dashing", False):
        speed = WALK_SPEED
        if keybinds.pressed(keys, "move_up"):
            dy = -speed
        if keybinds.pressed(keys, "move_down"):
            dy = speed
        if keybinds.pressed(keys, "move_left"):
            dx = -speed
        if keybinds.pressed(keys, "move_right"):
            dx = speed

        # Pelkkä sprintti ilman WASD: juokse hiiren osoittamaan suuntaan
        if mouse_sprint and wants_sprint and dx == 0 and dy == 0:
            mx, my = pygame.mouse.get_pos()
            wx = mx + camera[0] - player.rect.centerx
            wy = my + camera[1] - player.rect.centery
            dist = math.hypot(wx, wy)
            if dist > MOUSE_SPRINT_DEADZONE:
                dx = (wx / dist) * speed
                dy = (wy / dist) * speed

        # Diagonaali ei saa olla nopeampi
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071

    # Sprintti kuluttaa staminaa vain liikkuessa
    moving = (dx != 0 or dy != 0)
    try:
        player.set_sprinting(wants_sprint and moving)
        if player.is_sprinting and player.current_stamina > 0.5:
            dx *= SPRINT_MULT
            dy *= SPRINT_MULT
    except Exception:
        pass

    moved = False
    if moving:
        moved = _move_axis(player, int(round(dx)), 0, obstacles, walkable) or moved
        moved = _move_axis(player, 0, int(round(dy)), obstacles, walkable) or moved
        if dx:
            player.facing_right = dx > 0
        if bounds is not None:
            player.rect.clamp_ip(bounds)

    if moved:
        player.animation_state = "run"
    elif getattr(player, "animation_timer", 0) <= 0:
        # Käynnissä oleva lyönti-/keräysanimaatio saa pyöriä loppuun
        player.animation_state = "idle"
    return moved


def _move_axis(player, dx, dy, obstacles, walkable):
    """Siirrä yhtä akselia ja ratkaise törmäys. Palauttaa True jos siirtyi."""
    if dx == 0 and dy == 0:
        return False
    old_x, old_y = player.rect.x, player.rect.y
    player.rect.x += dx
    player.rect.y += dy
    if walkable is not None:
        if not walkable(player.rect):
            player.rect.x, player.rect.y = old_x, old_y
            return False
        return True
    for obs in (obstacles or ()):
        if player.rect.colliderect(obs.rect):
            if dx > 0:
                player.rect.right = obs.rect.left
            elif dx < 0:
                player.rect.left = obs.rect.right
            if dy > 0:
                player.rect.bottom = obs.rect.top
            elif dy < 0:
                player.rect.top = obs.rect.bottom
    return (player.rect.x, player.rect.y) != (old_x, old_y)


def handle_dash_keydown(player, event, camera=(0, 0)):
    """KEYDOWN-event: dash hiiren suuntaan (keybinds 'dash').

    Palauttaa True jos dash suoritettiin. Sama sääntö joka näytössä -
    ei kovakoodattua K_SPACEa.
    """
    if event.type != pygame.KEYDOWN:
        return False
    if not keybinds.matches(event.key, "dash"):
        return False
    mx, my = pygame.mouse.get_pos()
    dx = mx + camera[0] - player.rect.centerx
    dy = my + camera[1] - player.rect.centery
    player.perform_dash(dx, dy)
    return True
