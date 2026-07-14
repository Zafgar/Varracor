import pygame
import random
import math
from settings import *
from arenas.base_arena import BaseArena, ArenaObstacle


class StormArena(BaseArena):
    """Myrskytasanko (Tier 2): sadetta, telegraafattu salamanisku ja
    KUNNON suojat - raunioseinät ja siirtolohkareet estävät myös
    ammukset (type 'wall'). Vesilammikot ovat pelkkää maisemaa,
    nuolet lentävät niiden yli.

    BUGIKORJAUS: vanha versio importtasi olemattoman
    vfx.spawn_floating_text-funktion, joten luokka ei koskaan latautunut
    ja registry pudotti tier 2:n BasicArenaan.
    """

    def __init__(self):
        super().__init__("Storm Plains")
        self.floor_color = (40, 50, 40)
        pad = 60

        # Reunaseinät (pitävät taistelijat kentällä)
        t = 100
        self.obstacles.add(ArenaObstacle(-t, -t, SCREEN_WIDTH + t * 2, pad + t, "wall"))
        self.obstacles.add(ArenaObstacle(-t, SCREEN_HEIGHT - pad, SCREEN_WIDTH + t * 2, pad + t, "wall"))
        self.obstacles.add(ArenaObstacle(-t, 0, pad + t, SCREEN_HEIGHT, "wall"))
        self.obstacles.add(ArenaObstacle(SCREEN_WIDTH - pad, 0, pad + t, SCREEN_HEIGHT, "wall"))

        # SUOJAT: kaatuneen tornin raunioseinät + lohkareet
        self.cover = [
            pygame.Rect(int(SCREEN_WIDTH * 0.30), int(SCREEN_HEIGHT * 0.26), 210, 46),
            pygame.Rect(int(SCREEN_WIDTH * 0.58), int(SCREEN_HEIGHT * 0.66), 210, 46),
            pygame.Rect(int(SCREEN_WIDTH * 0.22), int(SCREEN_HEIGHT * 0.62), 70, 66),
            pygame.Rect(int(SCREEN_WIDTH * 0.72), int(SCREEN_HEIGHT * 0.30), 70, 66),
            pygame.Rect(int(SCREEN_WIDTH * 0.47), int(SCREEN_HEIGHT * 0.44), 90, 60),
        ]
        for r in self.cover:
            self.obstacles.add(ArenaObstacle(r.x, r.y, r.w, r.h, "wall"))

        # Vesilammikot (visuaalisia - eivät estä liikettä eivätkä nuolia)
        self.puddles = [
            pygame.Rect(int(SCREEN_WIDTH * 0.40), int(SCREEN_HEIGHT * 0.72), 170, 80),
            pygame.Rect(int(SCREEN_WIDTH * 0.62), int(SCREEN_HEIGHT * 0.18), 150, 70),
        ]

        # Salama: telegraafi -> isku (väisteltävissä)
        self.lightning_timer = random.randint(240, 420)
        self.strike_pos = None
        self.strike_warning = 0
        self.flash_alpha = 0
        self.bolt = []           # piirrettävä salamapolku
        self.bolt_ttl = 0

        # Sade
        self.drops = [[random.uniform(0, SCREEN_WIDTH),
                       random.uniform(0, SCREEN_HEIGHT),
                       random.uniform(14, 22)] for _ in range(140)]

        self._bg = None

    # ------------------------------------------------------------------
    def _build_bg(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(self.floor_color)
        rng = random.Random(7)
        # Märkä nurmi: tummempia ja vaaleampia laikkuja
        for _ in range(260):
            x, y = rng.randint(0, SCREEN_WIDTH), rng.randint(0, SCREEN_HEIGHT)
            c = rng.choice(((34, 44, 34), (46, 58, 44), (38, 52, 40)))
            pygame.draw.ellipse(bg, c, (x, y, rng.randint(30, 90), rng.randint(12, 30)))
        # Reunakivet
        pygame.draw.rect(bg, (52, 56, 60), (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.rect(bg, (52, 56, 60), (0, SCREEN_HEIGHT - 60, SCREEN_WIDTH, 60))
        pygame.draw.rect(bg, (52, 56, 60), (0, 0, 60, SCREEN_HEIGHT))
        pygame.draw.rect(bg, (52, 56, 60), (SCREEN_WIDTH - 60, 0, 60, SCREEN_HEIGHT))
        pygame.draw.rect(bg, (72, 76, 82), (60, 60, SCREEN_WIDTH - 120, SCREEN_HEIGHT - 120), 4)
        # Lammikot: tumma vesi + heijastusreuna
        for p in self.puddles:
            pygame.draw.ellipse(bg, (36, 52, 66), p)
            pygame.draw.ellipse(bg, (86, 112, 132), p, 2)
        return bg

    # ------------------------------------------------------------------
    def update(self, all_units):
        # Sade liikkuu
        for d in self.drops:
            d[0] -= 2.0
            d[1] += d[2]
            if d[1] > SCREEN_HEIGHT:
                d[0] = random.uniform(0, SCREEN_WIDTH + 120)
                d[1] = random.uniform(-40, -5)

        if self.flash_alpha > 0:
            self.flash_alpha -= 12
        if self.bolt_ttl > 0:
            self.bolt_ttl -= 1

        # Telegraafattu salama: varoitusrinki 45 framea ennen iskua
        if self.strike_warning > 0:
            self.strike_warning -= 1
            if self.strike_warning == 0 and self.strike_pos:
                self._strike(all_units)
        else:
            self.lightning_timer -= 1
            if self.lightning_timer <= 0:
                self.lightning_timer = random.randint(300, 540)
                living = [u for u in all_units if not getattr(u, "is_dead", False)]
                if living:
                    t = random.choice(living)
                    self.strike_pos = (t.rect.centerx + random.randint(-40, 40),
                                       t.rect.centery + random.randint(-40, 40))
                    self.strike_warning = 45

    def _strike(self, all_units):
        sx, sy = self.strike_pos
        self.flash_alpha = 140
        # Salamapolku taivaalta
        self.bolt = [(sx + random.randint(-30, 30), 0)]
        y = 0
        while y < sy:
            y += random.randint(40, 90)
            self.bolt.append((sx + random.randint(-26, 26), min(y, sy)))
        self.bolt.append((sx, sy))
        self.bolt_ttl = 10
        try:
            from sound_manager import sound_system
            sound_system.play_sound(random.choice(
                ["thunder_1", "thunder_2", "thunder_3", "thunder_4"]))
        except Exception:
            pass
        for u in all_units:
            if getattr(u, "is_dead", False):
                continue
            if math.hypot(u.rect.centerx - sx, u.rect.centery - sy) < 90:
                u.take_damage(18, "Magic")
        self.strike_pos = None

    # ------------------------------------------------------------------
    def draw_background(self, screen):
        if self._bg is None:
            self._bg = self._build_bg()
        screen.blit(self._bg, (0, 0))
        # Lammikoiden väreily
        tick = pygame.time.get_ticks() * 0.004
        for p in self.puddles:
            r = int(6 + math.sin(tick + p.x) * 3)
            pygame.draw.ellipse(screen, (110, 140, 160),
                                (p.centerx - r * 3, p.centery - r, r * 6, r * 2), 1)

    def draw_foreground(self, screen):
        # Suojat: raunioseinät ja lohkareet
        for i, r in enumerate(self.cover):
            base = (84, 88, 96) if r.w > r.h else (96, 92, 84)
            pygame.draw.rect(screen, (20, 22, 24), r.move(4, 5), border_radius=8)
            pygame.draw.rect(screen, base, r, border_radius=8)
            pygame.draw.rect(screen, (40, 42, 46), r, 3, border_radius=8)
            pygame.draw.line(screen, (60, 62, 68), (r.x + 8, r.y + r.h // 2),
                             (r.right - 8, r.y + r.h // 2), 2)

        # Varoitusrinki ennen salamaa
        if self.strike_warning > 0 and self.strike_pos:
            sx, sy = self.strike_pos
            pct = self.strike_warning / 45.0
            ring = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.circle(ring, (140, 190, 255, 120), (100, 100), 90, 3)
            pygame.draw.circle(ring, (140, 190, 255, 60), (100, 100),
                               int(90 * (1 - pct)))
            screen.blit(ring, (sx - 100, sy - 100))

        # Salamapolku
        if self.bolt_ttl > 0 and len(self.bolt) > 1:
            pygame.draw.lines(screen, (240, 245, 255), False, self.bolt, 4)
            pygame.draw.lines(screen, (150, 180, 255), False, self.bolt, 1)

        # Sade
        for x, y, s in self.drops:
            pygame.draw.line(screen, (120, 140, 190), (x, y), (x - 2, y + 11), 1)

        # Välähdys
        if self.flash_alpha > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.fill((255, 255, 255))
            flash.set_alpha(self.flash_alpha)
            screen.blit(flash, (0, 0))
