import pygame
import os
import random
from settings import *
from gladiator import Gladiator
from ai.base_ai import BaseAI
from sound_manager import sound_system


class TrollAI(BaseAI):
    """Trolli ei pakene ja lataa raskaita iskuja. Regeneraatio hoidetaan
    Troll.update:ssa (ei AI:ssa)."""
    def __init__(self, unit):
        super().__init__(unit)
        self.no_retreat = True


class Troll(Gladiator):
    """
    Metsätrolli — boss-haaste. Klassinen trollimekaniikka:
      - Regeneroi HP:ta joka sekunti
      - Regeneraatio ESTYY jos palaa (Burn-status) -> tuli/tuliloitsut ratkaisu
      - Erittäin tanky ja kovaa lyövä, ei pakene
    Pudottaa Troll Hidea (craftaus).
    """
    def __init__(self, name="Forest Troll", x=0, y=0, team_color=None):
        if team_color is None:
            team_color = ENEMY_TEAM
        super().__init__(name, "Troll", x, y, team_color)
        self.rect = pygame.Rect(x, y, 64, 80)

        self.base_attributes["str"] = 20
        self.base_attributes["dex"] = 4
        self.base_attributes["hp"] = 600
        self.calculate_final_stats()
        # calculate_final_stats laskee HP:n rodun mult:lla; pakotetaan boss-HP
        self.max_hp = 600
        self.current_hp = self.max_hp

        self.speed = 0.8
        self.attack_range = 55
        self.attack_speed = 90   # hidas mutta kova
        self.defense = 4
        self.is_boss = True

        # Regeneraatio
        self.regen_per_sec = 6
        self._regen_tick = 0

        self.show_main_hand = False
        self.sprites = {}
        self._load_sprites()
        self.image = self.sprites.get("idle") or self._fallback()
        self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))
        self.ai_controller = TrollAI(self)

    def load_assets(self):
        return True

    def _fallback(self):
        s = pygame.Surface((64, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (90, 130, 80), (8, 20, 48, 56))
        pygame.draw.circle(s, (110, 150, 95), (32, 20), 16)
        pygame.draw.circle(s, (200, 60, 60), (25, 18), 3)
        pygame.draw.circle(s, (200, 60, 60), (39, 18), 3)
        return s

    def _load_sprites(self):
        base = "assets/races/forest/troll/troll"
        for state in ("idle", "run", "attack", "hurt"):
            path = f"{base}_{state}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[state] = pygame.transform.smoothscale(img, (64, 80))
                except Exception:
                    pass

    def _is_burning(self):
        return any(e.get("type") == "Burn" for e in self.status_effects)

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        if self.is_dead:
            return
        # Regeneraatio kerran sekunnissa, ellei pala
        self._regen_tick += 1
        if self._regen_tick >= 60:
            self._regen_tick = 0
            if not self._is_burning() and self.current_hp < self.max_hp:
                self.current_hp = min(self.max_hp, self.current_hp + self.regen_per_sec)
                if manager:
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                            f"+{self.regen_per_sec}", color=(120, 220, 120))
