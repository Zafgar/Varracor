"""Timing and line-tension fishing minigame for Whisper Marsh anchors."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

import pygame

from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from assets.tiles.water import FishingAnchor
from ui_kit import draw_text, font_main, font_small, font_title


@dataclass(frozen=True)
class FishEntry:
    name: str
    weight: int
    value_sp: int
    stamina: int
    difficulty: int


FISH_TABLES: Dict[str, Dict[str, Tuple[FishEntry, ...]]] = {
    "muckford_marsh": {
        "Greywash Channel": (
            FishEntry("Mudfin", 38, 3, 72, 1),
            FishEntry("Reed Carp", 30, 5, 82, 1),
            FishEntry("Greywash Perch", 22, 7, 94, 2),
            FishEntry("Tinback Eel", 10, 12, 116, 2),
        ),
        "Whisper Pool": (
            FishEntry("Pale Lanternfish", 34, 7, 92, 2),
            FishEntry("Whisper Koi", 28, 10, 108, 2),
            FishEntry("Echo Eel", 24, 14, 126, 3),
            FishEntry("Bog Pike", 14, 19, 148, 3),
        ),
    }
}


def _safe_sound(name: str) -> None:
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def choose_fish(anchor: FishingAnchor, rng: random.Random) -> FishEntry:
    table = FISH_TABLES.get(anchor.fish_table, FISH_TABLES["muckford_marsh"])
    entries = table.get(anchor.water_name) or table["Greywash Channel"]
    total = sum(max(1, entry.weight) for entry in entries)
    roll = rng.uniform(0, total)
    cursor = 0.0
    for entry in entries:
        cursor += max(1, entry.weight)
        if roll <= cursor:
            return entry
    return entries[-1]


class MarshFishingMenu(BaseMenu):
    """Cast, hook and reel a fish without requiring finished fishing assets."""

    def __init__(self, manager):
        super().__init__(manager)
        self.anchor = FishingAnchor(0, 0, "left", "Greywash Channel", 1)
        self.phase = "aim"
        self.cast_power = 0.0
        self.cast_direction = 1.0
        self.wait_timer = 0
        self.bite_timer = 0
        self.reel_timer = 0
        self.tension = 18.0
        self.fish_stamina = 0.0
        self.fish_stamina_max = 1.0
        self.current_fish = None
        self.result_text = ""
        self.result_success = False
        self.rng = random.Random()
        self.water_particles = []
        self.frame = 0

    def on_enter(self):
        pending = getattr(self.manager, "pending_fishing_anchor", None)
        if pending is not None:
            self.anchor = pending
        self.manager.pending_fishing_anchor = None
        seed = (
            int(getattr(self.anchor, "x", 0)) * 31
            + int(getattr(self.anchor, "y", 0)) * 17
            + int(pygame.time.get_ticks())
        )
        self.rng = random.Random(seed)
        self.phase = "aim"
        self.cast_power = 0.05
        self.cast_direction = 1.0
        self.wait_timer = 0
        self.bite_timer = 0
        self.reel_timer = 0
        self.tension = 18.0
        self.current_fish = None
        self.result_text = ""
        self.result_success = False
        self.frame = 0
        self.water_particles = []

    def _return_to_marsh(self):
        self.manager.pending_local_area = None
        self.next_state = getattr(self.manager, "fishing_return_state", "forest_excursion")
        _safe_sound("click")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._return_to_marsh()
            return
        if event.key not in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            return

        if self.phase == "aim":
            self._cast()
        elif self.phase == "bite":
            self._hook()
        elif self.phase == "result":
            self._return_to_marsh()

    def _cast(self):
        self.phase = "waiting"
        quality = 1.0 - abs(0.72 - self.cast_power)
        quality = max(0.1, min(1.0, quality))
        self.wait_timer = int(145 - quality * 75 + self.rng.randint(0, 45))
        _safe_sound("water")

    def _hook(self):
        self.current_fish = choose_fish(self.anchor, self.rng)
        difficulty_bonus = max(0, int(self.anchor.difficulty) - 1) * 12
        self.fish_stamina_max = float(self.current_fish.stamina + difficulty_bonus)
        self.fish_stamina = self.fish_stamina_max
        self.tension = 32.0
        self.reel_timer = 840
        self.phase = "reel"
        _safe_sound("recruit")

    def _lose(self, reason: str):
        self.phase = "result"
        self.result_success = False
        self.result_text = str(reason)
        _safe_sound("error")

    def _award_catch(self):
        fish = self.current_fish
        if fish is None:
            self._lose("The line came back empty.")
            return
        self.manager.inventory[fish.name] = int(self.manager.inventory.get(fish.name, 0)) + 1
        try:
            from systems.whisper_marsh_story import whisper_marsh_story_state

            state = whisper_marsh_story_state(self.manager)
            state["fish_caught"] = int(state.get("fish_caught", 0)) + 1
            catches = state.setdefault("catches", {})
            catches[fish.name] = int(catches.get(fish.name, 0)) + 1
            state["first_fish_caught"] = True
            if int(state.get("quest_stage", 0)) == 6:
                state["quest_stage"] = 7
                state["boss_unlocked"] = True
        except Exception:
            pass
        try:
            self.manager.record_tier0_event("quest", "whisper_marsh_first_catch")
        except Exception:
            pass
        self.phase = "result"
        self.result_success = True
        self.result_text = f"Caught {fish.name}! Market value: {fish.value_sp} SP."
        _safe_sound("recruit")

    def _update_reel(self, held: bool):
        """Advance one deterministic reel frame; exposed for headless tests."""
        if self.phase != "reel" or self.current_fish is None:
            return
        self.reel_timer -= 1
        difficulty = max(self.current_fish.difficulty, int(self.anchor.difficulty))
        surge = math.sin(self.frame * (0.075 + difficulty * 0.012))
        surge += math.sin(self.frame * 0.021 + 1.8) * 0.55
        random_kick = self.rng.uniform(-0.18, 0.32) * difficulty

        if held:
            self.tension += 1.05 + difficulty * 0.16 + max(0.0, surge) * 0.65 + random_kick
            if 24.0 <= self.tension <= 86.0:
                cast_bonus = 0.35 + self.cast_power * 0.55
                self.fish_stamina -= 0.72 + cast_bonus
        else:
            self.tension -= 1.35
            if self.tension < 18.0:
                self.fish_stamina += 0.10 + difficulty * 0.025

        self.tension = max(0.0, self.tension)
        self.fish_stamina = min(self.fish_stamina_max, self.fish_stamina)
        if self.tension >= 100.0:
            self._lose("The line snapped under too much tension.")
        elif self.reel_timer <= 0:
            self._lose("The fish escaped into the reeds.")
        elif self.fish_stamina <= 0:
            self._award_catch()

    def update(self):
        super().update()
        self.frame += 1
        if self.phase == "aim":
            self.cast_power += 0.018 * self.cast_direction
            if self.cast_power >= 1.0:
                self.cast_power = 1.0
                self.cast_direction = -1.0
            elif self.cast_power <= 0.0:
                self.cast_power = 0.0
                self.cast_direction = 1.0
        elif self.phase == "waiting":
            self.wait_timer -= 1
            if self.wait_timer <= 0:
                self.phase = "bite"
                self.bite_timer = 78
                _safe_sound("click")
        elif self.phase == "bite":
            self.bite_timer -= 1
            if self.bite_timer <= 0:
                self._lose("The bite was missed.")
        elif self.phase == "reel":
            keys = pygame.key.get_pressed()
            held = bool(keys[pygame.K_e] or keys[pygame.K_SPACE])
            self._update_reel(held)

        if self.phase in {"waiting", "bite", "reel"} and self.rng.random() < 0.18:
            self.water_particles.append(
                {
                    "x": self.rng.randint(0, SCREEN_WIDTH),
                    "y": self.rng.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT - 80),
                    "life": self.rng.randint(25, 70),
                }
            )
        for particle in self.water_particles:
            particle["life"] -= 1
            particle["y"] -= 0.18
        self.water_particles = [p for p in self.water_particles if p["life"] > 0]

    @staticmethod
    def _bar(screen, rect, value, maximum, fill, border=(196, 180, 128)):
        pygame.draw.rect(screen, (22, 28, 30), rect, border_radius=8)
        pct = max(0.0, min(1.0, float(value) / max(1.0, float(maximum))))
        inner = rect.inflate(-6, -6)
        fill_rect = pygame.Rect(inner.x, inner.y, int(inner.w * pct), inner.h)
        if fill_rect.w > 0:
            pygame.draw.rect(screen, fill, fill_rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2, border_radius=8)

    def _draw_water_scene(self, screen):
        screen.fill((24, 42, 43))
        horizon = SCREEN_HEIGHT // 2 - 40
        pygame.draw.rect(screen, (55, 71, 54), (0, 0, SCREEN_WIDTH, horizon))
        pygame.draw.rect(screen, (26, 66, 78), (0, horizon, SCREEN_WIDTH, SCREEN_HEIGHT - horizon))
        for y in range(horizon + 22, SCREEN_HEIGHT, 34):
            phase = self.frame * 0.045 + y * 0.03
            points = []
            for x in range(-20, SCREEN_WIDTH + 40, 80):
                points.append((x, int(y + math.sin(phase + x * 0.015) * 5)))
            pygame.draw.aalines(screen, (65, 119, 128), False, points)
        for x in range(20, SCREEN_WIDTH, 72):
            height = 28 + (x // 72) % 3 * 12
            pygame.draw.line(screen, (65, 112, 68), (x, horizon + 20), (x + 4, horizon - height), 4)
            pygame.draw.line(screen, (145, 119, 60), (x + 4, horizon - height), (x + 9, horizon - height - 8), 3)
        for particle in self.water_particles:
            pygame.draw.circle(screen, (174, 215, 208), (int(particle["x"]), int(particle["y"])), 2)

    def draw(self, screen):
        self._draw_water_scene(screen)
        title = f"FISHING — {self.anchor.water_name.upper()}"
        draw_text(title, font_title, GOLD_COLOR, screen, 42, 32)
        draw_text("Esc: return to Whisper Marsh", font_small, GRAY, screen, 44, 76)

        panel = pygame.Rect(170, 120, SCREEN_WIDTH - 340, SCREEN_HEIGHT - 220)
        overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
        overlay.fill((15, 22, 24, 215))
        screen.blit(overlay, panel.topleft)
        pygame.draw.rect(screen, (154, 139, 91), panel, 3, border_radius=12)

        if self.phase == "aim":
            draw_text("CAST", font_title, WHITE, screen, panel.x + 35, panel.y + 28)
            draw_text("Press E or Space near the marked sweet spot.", font_main, GRAY, screen, panel.x + 35, panel.y + 72)
            bar = pygame.Rect(panel.x + 90, panel.centery - 25, panel.w - 180, 52)
            pygame.draw.rect(screen, (29, 39, 39), bar, border_radius=10)
            sweet = pygame.Rect(bar.x + int(bar.w * 0.62), bar.y + 4, int(bar.w * 0.20), bar.h - 8)
            pygame.draw.rect(screen, (65, 126, 78), sweet, border_radius=7)
            marker_x = bar.x + int(bar.w * self.cast_power)
            pygame.draw.line(screen, (244, 221, 129), (marker_x, bar.y - 8), (marker_x, bar.bottom + 8), 5)
            pygame.draw.rect(screen, (186, 167, 105), bar, 3, border_radius=10)
        elif self.phase == "waiting":
            draw_text("LINE CAST", font_title, WHITE, screen, panel.x + 35, panel.y + 28)
            draw_text("Watch the float. Do not strike early.", font_main, GRAY, screen, panel.x + 35, panel.y + 72)
            bob_y = panel.centery + int(math.sin(self.frame * 0.12) * 7)
            pygame.draw.line(screen, (180, 170, 125), (panel.centerx, panel.y + 105), (panel.centerx, bob_y), 2)
            pygame.draw.circle(screen, (202, 83, 59), (panel.centerx, bob_y), 12)
            pygame.draw.circle(screen, (238, 220, 154), (panel.centerx, bob_y - 5), 7)
        elif self.phase == "bite":
            draw_text("BITE!", font_title, (242, 199, 77), screen, panel.x + 35, panel.y + 28)
            draw_text("PRESS E OR SPACE NOW", font_title, WHITE, screen, panel.centerx - 190, panel.centery - 30)
            pulse = 48 + int(abs(math.sin(self.frame * 0.22)) * 24)
            pygame.draw.circle(screen, (180, 225, 215), panel.center, pulse, 4)
        elif self.phase == "reel":
            draw_text(self.current_fish.name if self.current_fish else "HOOKED FISH", font_title, WHITE, screen, panel.x + 35, panel.y + 28)
            draw_text("Hold E/Space to reel. Release before tension reaches red.", font_main, GRAY, screen, panel.x + 35, panel.y + 72)
            tension_rect = pygame.Rect(panel.x + 90, panel.y + 150, panel.w - 180, 38)
            fill = (75, 175, 106) if self.tension < 78 else (219, 76, 64)
            self._bar(screen, tension_rect, self.tension, 100, fill)
            draw_text(f"LINE TENSION {int(self.tension)}%", font_small, WHITE, screen, tension_rect.x, tension_rect.y - 24)
            stamina_rect = pygame.Rect(panel.x + 90, panel.y + 245, panel.w - 180, 38)
            self._bar(screen, stamina_rect, self.fish_stamina, self.fish_stamina_max, (70, 131, 184))
            draw_text("FISH STAMINA", font_small, WHITE, screen, stamina_rect.x, stamina_rect.y - 24)
        else:
            color = GREEN if self.result_success else (226, 102, 84)
            draw_text("LANDED" if self.result_success else "LOST", font_title, color, screen, panel.x + 35, panel.y + 28)
            draw_text(self.result_text, font_main, WHITE, screen, panel.x + 35, panel.centery - 20)
            draw_text("Press E, Space or Enter to return.", font_main, GRAY, screen, panel.x + 35, panel.centery + 35)
