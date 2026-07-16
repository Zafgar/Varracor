import pygame
import os
from settings import *
from gladiator import Gladiator
from sound_manager import sound_system

try:
    from ai.human_ai import HumanAI
except ImportError:
    HumanAI = None


class FrogSmith(Gladiator):
    """
    Sammakko-seppä-soturi (Frogfolk). Kanoninen marsh-smith joka liittyy
    pelaajan tiimiin: taistelee areenalla JA toimii tiimin seppänä
    (manager.has_smith -> varusteiden korjaus/parannus halvempaa).
    Käyttää HumanAI:ta, jotta se taistelee liittolaisena oikein.
    """

    def __init__(self, name="Brekka", x=0, y=0, team_color=None):
        if team_color is None:
            team_color = PLAYER_TEAM
        super().__init__(name, "Frogfolk", x, y, team_color)
        self.rect = pygame.Rect(x, y, 46, 46)

        # Kestävä nuija-soturi
        self.base_attributes["str"] = 13
        self.base_attributes["dex"] = 8
        self.base_attributes["int"] = 6
        self.base_attributes["hp"] = 160
        self.calculate_final_stats()
        self.current_hp = self.max_hp

        self.speed = self.walk_speed = 0.95 * 1.85  # uusi liikeskaala (pelitesti 28); pelkka .speed ylikirjoittui updatessa
        self.attack_range = 45
        self.mud_immune = True
        self.is_smith = True  # Tunniste seppä-perkille

        # Grafiikat (frog-spritet fallbackilla)
        self.sprites = {}
        self._load_sprites()
        self.image = self.sprites.get("idle") or self._fallback_image()

        self.ai_controller = HumanAI(self) if HumanAI else self.ai_controller

    def load_assets(self):
        return True

    def _fallback_image(self):
        s = pygame.Surface((46, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (70, 130, 70), (4, 10, 38, 32))
        pygame.draw.circle(s, (90, 160, 90), (16, 16), 6)
        pygame.draw.circle(s, (90, 160, 90), (30, 16), 6)
        pygame.draw.circle(s, (20, 20, 20), (16, 16), 2)
        pygame.draw.circle(s, (20, 20, 20), (30, 16), 2)
        return s

    def _load_sprites(self):
        base = "assets/races/swamp/frog_smith/smith"
        for state in ("idle", "run", "attack", "hurt"):
            path = f"{base}_{state}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[state] = pygame.transform.smoothscale(img, (46, 46))
                except Exception:
                    pass
