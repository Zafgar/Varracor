import pygame
import os
import math
import random
from settings import ENEMY_TEAM
from gladiator import Gladiator
from ai.base_ai import BaseAI
from sound_manager import sound_system


class SpiderAI(BaseAI):
    """Hämähäkit eivät pakene ja jahtaavat sinnikkäästi."""
    def __init__(self, unit):
        super().__init__(unit)
        self.no_retreat = True


class Spiderling(Gladiator):
    """Pieni nopea hämähäkki. Broodmother kutsuu näitä. Heikko mutta
    myrkyllinen puraisu lähietäisyydeltä."""
    def __init__(self, name="Spiderling", x=0, y=0, team_color=None):
        if team_color is None:
            team_color = ENEMY_TEAM
        super().__init__(name, "Spider", x, y, team_color)
        self.rect = pygame.Rect(x, y, 34, 30)
        self.base_attributes["str"] = 6
        self.base_attributes["dex"] = 14
        self.base_attributes["hp"] = 40
        self.calculate_final_stats()
        self.max_hp = 40
        self.current_hp = self.max_hp
        self.speed = 1.7
        self.attack_range = 34
        self.attack_speed = 45
        self.defense = 0
        self.show_main_hand = False
        self.sprites = {}
        self.image = self._fallback((110, 90, 130), 34, 30)
        self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 3, self.rect.h * 3))
        self.ai_controller = SpiderAI(self)

    def load_assets(self):
        return True

    def _fallback(self, body, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        pygame.draw.ellipse(s, body, (cx - 8, cy - 6, 16, 14))
        pygame.draw.circle(s, tuple(min(255, c + 30) for c in body), (cx, cy - 6), 5)
        # jalat
        for sign in (-1, 1):
            for i, dy in enumerate((-5, 0, 5)):
                pygame.draw.line(s, (40, 30, 45),
                                 (cx, cy), (cx + sign * (w // 2), cy + dy), 2)
        pygame.draw.circle(s, (220, 40, 40), (cx - 2, cy - 7), 1)
        pygame.draw.circle(s, (220, 40, 40), (cx + 2, cy - 7), 1)
        return s

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)


class CaveBroodmother(Gladiator):
    """
    Kaivosluolan Broodmother — jättihämähäkki-boss, joka saartaa syvemmän
    kammion. Kunnes se kaadetaan, verkkoseinä estää pääsyn rikkaampiin
    malmeihin (rubiini/hopea).

    Mekaniikat:
      - Venom Spit (kaukotaisto): myrkyttää kohteen (Poison DOT).
      - Web Shot (kaukotaisto): sotkee kohteen verkkoon (Web slow).
      - Kutsuu 2 Spiderlingiä kerran, kun HP putoaa alle 50 %.
      - Ei pakene (SpiderAI.no_retreat).
    Pudottaa Spider Silkia ja Venom Glandin.
    """
    def __init__(self, name="Cave Broodmother", x=0, y=0, team_color=None):
        if team_color is None:
            team_color = ENEMY_TEAM
        super().__init__(name, "Spider", x, y, team_color)
        self.rect = pygame.Rect(x, y, 96, 84)

        self.base_attributes["str"] = 26
        self.base_attributes["dex"] = 12
        self.base_attributes["hp"] = 750
        self.base_attributes["def_flat"] = 6
        self.calculate_final_stats()
        # calculate_final_stats laskee HP:n rodun mult:lla; pakotetaan boss-HP
        self.max_hp = 750
        self.current_hp = self.max_hp

        self.speed = 1.15
        self.attack_range = 60
        self.attack_speed = 70
        self.defense = 6
        self.is_boss = True

        # Kykyjen cooldownit
        self.spit_cooldown = 150
        self.web_cooldown = 300
        self.brood_spawned = False

        self.show_main_hand = False
        self.sprites = {}
        self._load_sprites()
        self.image = self.sprites.get("idle") or self._fallback()
        self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * 2, self.rect.h * 2))
        self.ai_controller = SpiderAI(self)

    def load_assets(self):
        return True

    def _fallback(self):
        s = pygame.Surface((96, 84), pygame.SRCALPHA)
        cx, cy = 48, 46
        # jalat
        for sign in (-1, 1):
            for dy in (-14, -4, 6, 16):
                pygame.draw.line(s, (30, 22, 34), (cx, cy),
                                 (cx + sign * 46, cy + dy), 4)
        pygame.draw.ellipse(s, (70, 55, 85), (cx - 22, cy - 14, 44, 40))
        pygame.draw.circle(s, (95, 75, 115), (cx, cy - 12), 13)
        # silmät
        for ex in (-6, -2, 2, 6):
            pygame.draw.circle(s, (230, 40, 40), (cx + ex, cy - 14), 2)
        return s

    def _load_sprites(self):
        base = "assets/races/cave/broodmother/broodmother"
        for state in ("idle", "run", "attack", "hurt"):
            path = f"{base}_{state}_1.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites[state] = pygame.transform.smoothscale(img, (96, 84))
                except Exception:
                    pass

    def update(self, obstacles=None, manager=None):
        if self.spit_cooldown > 0:
            self.spit_cooldown -= 1
        if self.web_cooldown > 0:
            self.web_cooldown -= 1
        super().update(obstacles, manager)

    def run_combat_ai(self, all_units, obstacles=None, manager=None):
        if self.is_dead:
            return

        # Kutsu pentue kerran, kun terveys putoaa puoleen
        if not self.brood_spawned and self.current_hp < self.max_hp * 0.5:
            self._spawn_brood(manager)

        target = self.ai_controller.current_target if self.ai_controller else None
        if target and not target.is_dead:
            dist = math.hypot(target.rect.centerx - self.rect.centerx,
                              target.rect.centery - self.rect.centery)
            if 90 < dist < 480:
                if self.spit_cooldown <= 0:
                    self._venom_spit(target, manager)
                    return
                if self.web_cooldown <= 0:
                    self._web_shot(target, manager)
                    return

        super().run_combat_ai(all_units, obstacles, manager)

    def _spawn_brood(self, manager):
        self.brood_spawned = True
        if not manager:
            return
        manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40,
                                "SKITTER!", color=(180, 120, 220))
        arena = manager.current_arena
        aw = getattr(arena, "width", 1920) if arena else 1920
        ah = getattr(arena, "height", 1080) if arena else 1080
        for _ in range(2):
            sx = self.rect.centerx + random.randint(-90, 90)
            sy = self.rect.centery + random.randint(-90, 90)
            # Pidä spawn areenan sisällä, jotta reunalle ajautunut boss
            # kutsuu silti parvensa (ei hiljaista epäonnistumista).
            sx = max(20, min(aw - 20, sx))
            sy = max(20, min(ah - 20, sy))
            ling = Spiderling("Spiderling", sx, sy, team_color=self.team_color)
            manager.enemy_team.add(ling)
            manager.all_units.add(ling)
            manager.vfx.create_spawn_fog(sx, sy)

    def _venom_spit(self, target, manager):
        self.spit_cooldown = 210
        self.animation_state = "attack"
        self.animation_timer = 24
        sound_system.play_sound("swish")
        if not manager:
            return
        start, end = self.rect.center, target.rect.center

        def on_hit():
            if target and not target.is_dead:
                dmg = 14 + int(self.strength * 0.4)
                target.take_damage(dmg, "Poison", attacker=self, manager=manager)
                target.apply_status("Poison", 180, 3)
                manager.vfx.create_acid_puddle(target.rect.centerx, target.rect.centery)
                manager.vfx.show_damage(target.rect.centerx, target.rect.top,
                                        "POISONED", color=(120, 220, 60))

        manager.vfx.create_fireball(start, end, on_impact=on_hit)

    def _web_shot(self, target, manager):
        self.web_cooldown = 360
        self.animation_state = "attack"
        self.animation_timer = 24
        sound_system.play_sound("swish")
        if not manager:
            return
        start, end = self.rect.center, target.rect.center

        def on_hit():
            if target and not target.is_dead:
                target.take_damage(6, "Physical", attacker=self, manager=manager)
                target.apply_status("Web", 150, 0)
                manager.vfx.show_damage(target.rect.centerx, target.rect.top,
                                        "WEBBED", color=(220, 220, 255))

        manager.vfx.create_fireball(start, end, on_impact=on_hit)
