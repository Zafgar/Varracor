# ai/rat_ai.py
"""Rat Rider -tekoäly - BaseAI:n päälle rakennettu (yksi AI-kehys).

AIEMMIN tämä oli täysin erillinen toteutus (oma tilakone, oma chase/
retreat/flank-liike, oma separation), joka ohitti BaseAI:n parannukset
(reitinhaku, anti-kite-ennakko, kiertoliike, jumiutumisen purku). Nyt
jäljellä on vain ratsastajan ERIKOISUUDET - pitkä rynnäkkö (charge) ja
pomminheitto - ja kaikki perusliike/kohdennus/hyökkäys tulee BaseAI:sta.

Rynnäkön vaiheet (unit.charge_phase):
  0 = ei rynnäkköä, 1 = lataus paikallaan, 2 = syöksy, 3 = törmäysjäykkyys
"""
import math

import pygame

from ai.base_ai import BaseAI


class RatAI(BaseAI):
    def __init__(self, unit):
        super().__init__(unit)

    def execute_ai(self, all_units, obstacles=None, manager=None):
        if self.unit.is_dead:
            return

        # --- RYNNÄKKÖSEKVENSSI (ohittaa normaalin AI:n kunnes valmis) ---
        if getattr(self.unit, "charge_phase", 0):
            self._run_charge_sequence(all_units, manager)
            return

        # --- ERIKOISKYKYJEN KÄYTTÖPÄÄTÖKSET ---
        if not self._is_valid_target(self.current_target):
            self.current_target = self.find_best_target(all_units, manager)
        target = self.current_target
        if target:
            dist = math.hypot(
                target.rect.centerx - self.unit.rect.centerx,
                target.rect.centery - self.unit.rect.centery,
            )
            # Rynnäkkö: keskipitkältä matkalta, kun kyky on valmis
            if getattr(self.unit, "charge_cooldown", 1) <= 0 and 250 < dist < 800:
                self.unit.start_charge()
                return
            # Pomminheitto: heiton jälkeen BaseAI:n kiertoliike hoitaa
            # etäisyyden pitämisen, erillistä retreat-tilaa ei tarvita
            if getattr(self.unit, "throw_cooldown", 1) <= 0 and 150 < dist < 450:
                if self.unit.perform_throw(target, manager):
                    return

        # --- KAIKKI MUU: yhteinen kehys (chase, hyökkäys, väistöt) ---
        super().execute_ai(all_units, obstacles, manager)

    def _run_charge_sequence(self, all_units, manager):
        unit = self.unit

        if unit.charge_phase == 1:  # Lataus (windup)
            unit.charge_timer -= 1
            if unit.charge_timer <= 0:
                unit.charge_phase = 2
                unit.charge_timer = 80
                if self.current_target:
                    dx = self.current_target.rect.centerx - unit.rect.centerx
                    dy = self.current_target.rect.centery - unit.rect.centery
                    unit.facing_right = dx > 0
                    unit.perform_dash(dx, dy)
                    # Pitkä rynnäkkö: nopeampi ja pidempi kuin perussyöksy
                    unit.dash_speed_mult = 5.0
                    unit.dash_timer = 80
            return

        if unit.charge_phase == 2:  # Syöksy käynnissä
            hits = pygame.sprite.spritecollide(unit, all_units, False)
            for h in hits:
                if h is not unit and not unit.is_ally(h) and not getattr(h, "is_dead", False):
                    # Törmäys! AoE-isku ja tainnutus
                    unit.charge_phase = 3
                    unit.charge_timer = 20
                    unit.is_dashing = False
                    if manager:
                        manager.vfx.create_explosion(unit.rect.centerx, unit.rect.centery)
                        for u in all_units:
                            if not unit.is_ally(u) and not getattr(u, "is_dead", False):
                                d = math.hypot(u.rect.centerx - unit.rect.centerx,
                                               u.rect.centery - unit.rect.centery)
                                if d < 60:
                                    u.take_damage(20, "Physical", unit, manager)
                                    u.apply_status("Stun", 30)
                    break
            if not unit.is_dashing and unit.charge_phase == 2:
                unit.charge_phase = 0  # Syöksy loppui osumatta
            return

        if unit.charge_phase == 3:  # Törmäysjäykkyys
            unit.charge_timer -= 1
            if unit.charge_timer <= 0:
                unit.charge_phase = 0
            return
