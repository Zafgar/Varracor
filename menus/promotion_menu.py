from __future__ import annotations

import math
import random

import pygame

from menus.base_menu import BaseMenu
from settings import SCREEN_HEIGHT, SCREEN_WIDTH
from systems.tier0_finale import (
    FINAL_REWARD_SP,
    complete_ceremony,
    ensure_finale_state,
    farewell_pages,
    mark_promotion_victory,
)
from ui_kit import GOLD_COLOR, GRAY, GREEN, WHITE, UIButton, draw_text, font_main, font_small, font_title


class Confetti:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(-240, -30)
        self.speed = random.uniform(1.7, 4.8)
        self.color = random.choice(
            [GOLD_COLOR, WHITE, (179, 61, 50), (87, 136, 93), (100, 126, 165)]
        )
        self.size = random.randint(3, 8)
        self.sway = random.uniform(0, 100)
        self.spin = random.uniform(0, math.tau)

    def update(self):
        self.y += self.speed
        self.x += math.sin((self.y + self.sway) * 0.045) * 1.8
        self.spin += 0.08
        if self.y > SCREEN_HEIGHT + 15:
            self.y = random.randint(-70, -10)
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, screen):
        width = max(2, int(self.size * (0.55 + abs(math.sin(self.spin)) * 0.45)))
        pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), width, self.size))


class PromotionMenu(BaseMenu):
    """Tier 0 finale ceremony after the Rookie Dust promotion victory."""

    def __init__(self, manager):
        super().__init__(manager)
        self.btn_continue = UIButton(
            SCREEN_WIDTH // 2 - 175,
            SCREEN_HEIGHT - 105,
            350,
            62,
            "CONTINUE",
            None,
            GREEN,
        )
        self.confetti = [Confetti() for _ in range(165)]
        self.timer = 0
        self.pages = []
        self.page_index = 0
        self.started = False
        self.completed = False
        self.signature = None
        self.torch_phase = 0.0

    def _ensure_started(self):
        state = ensure_finale_state(self.manager)
        signature = (
            bool(state.get("promotion_won")),
            bool(state.get("ceremony_complete")),
            int(getattr(getattr(self.manager, "league_engine", None), "tier", 1)),
            str(getattr(self.manager, "match_result", "")),
        )
        if self.started and signature == self.signature:
            return
        if getattr(self.manager, "match_mode", "") == "PROMOTION" and getattr(self.manager, "match_result", "") == "VICTORY":
            mark_promotion_victory(self.manager)
        state = ensure_finale_state(self.manager)
        if state.get("promotion_won"):
            self.pages = farewell_pages(self.manager)
        else:
            self.pages = [
                {
                    "speaker": "Arena Clerk",
                    "text": "No valid Rookie Dust promotion victory is recorded. Return to Bram's league ledger.",
                }
            ]
        self.page_index = min(int(state.get("farewell_pages_seen", 0)), max(0, len(self.pages) - 1))
        self.completed = bool(state.get("ceremony_complete"))
        self.started = True
        self.signature = (
            bool(state.get("promotion_won")),
            bool(state.get("ceremony_complete")),
            int(getattr(getattr(self.manager, "league_engine", None), "tier", 1)),
            str(getattr(self.manager, "match_result", "")),
        )
        self._sync_button()

    def on_enter(self):
        self.started = False
        self._ensure_started()

    def _sync_button(self):
        if self.page_index >= len(self.pages) - 1:
            self.btn_continue.text = "DEPART FOR RATTLEBRIDGE"
        else:
            self.btn_continue.text = "NEXT"

    def _advance(self):
        self._ensure_started()
        if self.page_index < len(self.pages) - 1:
            self.page_index += 1
            state = ensure_finale_state(self.manager)
            state["farewell_pages_seen"] = max(
                int(state.get("farewell_pages_seen", 0)),
                self.page_index,
            )
            self._sync_button()
            return
        complete_ceremony(self.manager)
        self.completed = True
        self.manager.pending_local_area = "kingsreach_toll"
        self.manager.pending_world_location = "kingsreach_toll"
        self.manager.kingsreach_entry = "greywash_ford"
        self.next_state = "regional_staging"

    def handle_event(self, event):
        self._ensure_started()
        if self.btn_continue.is_clicked(event):
            self._advance()
            return
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_SPACE,
            pygame.K_e,
        ):
            self._advance()

    def update(self):
        self._ensure_started()
        self.timer += 1
        self.torch_phase += 0.09
        for particle in self.confetti:
            particle.update()
        self.btn_continue.update_hover(pygame.mouse.get_pos())

    @staticmethod
    def _wrap(text, font, width):
        lines = []
        current = ""
        for word in str(text).split():
            trial = word if not current else f"{current} {word}"
            if font.size(trial)[0] <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _draw_yard(self, screen):
        screen.fill((25, 24, 29))
        horizon = int(SCREEN_HEIGHT * 0.44)
        pygame.draw.rect(screen, (54, 48, 44), (0, horizon, SCREEN_WIDTH, SCREEN_HEIGHT - horizon))
        pygame.draw.rect(screen, (76, 63, 49), (0, horizon + 90, SCREEN_WIDTH, SCREEN_HEIGHT - horizon - 90))
        for x in range(-40, SCREEN_WIDTH + 80, 86):
            y = horizon + 108 + ((x // 86) % 3) * 12
            pygame.draw.ellipse(screen, (61, 51, 43), (x, y, 128, 34))
            pygame.draw.arc(screen, (103, 83, 61), (x + 12, y + 3, 104, 24), 3.2, 6.0, 2)

        # Shanty Yard fence and arena arch.
        for x in range(0, SCREEN_WIDTH, 74):
            pygame.draw.rect(screen, (79, 58, 41), (x, horizon - 10, 15, 118))
            pygame.draw.polygon(screen, (103, 75, 48), [(x - 3, horizon - 10), (x + 8, horizon - 34), (x + 18, horizon - 10)])
        arch = pygame.Rect(SCREEN_WIDTH // 2 - 260, horizon - 170, 520, 225)
        pygame.draw.arc(screen, (102, 84, 61), arch, math.pi, math.tau, 38)
        pygame.draw.rect(screen, (92, 72, 51), (arch.left + 8, arch.centery, 42, 180))
        pygame.draw.rect(screen, (92, 72, 51), (arch.right - 50, arch.centery, 42, 180))

        # Tier 1 banner.
        banner = pygame.Rect(SCREEN_WIDTH // 2 - 145, horizon - 150, 290, 132)
        pygame.draw.polygon(
            screen,
            (128, 43, 39),
            [banner.topleft, banner.topright, (banner.right - 25, banner.bottom), (banner.centerx, banner.bottom - 20), (banner.left + 25, banner.bottom)],
        )
        pygame.draw.rect(screen, (199, 157, 68), banner, 4)
        pygame.draw.circle(screen, (210, 174, 80), banner.center, 31, 5)
        pygame.draw.line(screen, (210, 174, 80), (banner.centerx - 40, banner.centery), (banner.centerx + 40, banner.centery), 5)

        # Crowd silhouettes with simple waving animation.
        crowd_y = horizon + 80
        for index in range(34):
            x = 28 + index * 58
            height = 52 + (index % 5) * 8
            wave = int(math.sin(self.timer * 0.07 + index) * 7)
            body = (42 + index % 3 * 6, 39 + index % 4 * 5, 37 + index % 2 * 6)
            pygame.draw.circle(screen, body, (x, crowd_y - height), 13)
            pygame.draw.rect(screen, body, (x - 13, crowd_y - height + 10, 26, height - 10), border_radius=7)
            if index % 3 == 0:
                pygame.draw.line(screen, body, (x - 5, crowd_y - height + 23), (x - 19, crowd_y - height - 8 + wave), 7)
            if index % 4 == 0:
                pygame.draw.line(screen, body, (x + 5, crowd_y - height + 23), (x + 21, crowd_y - height - 12 - wave), 7)

        # Torches.
        for x in (135, SCREEN_WIDTH - 135, SCREEN_WIDTH // 2 - 350, SCREEN_WIDTH // 2 + 350):
            pygame.draw.line(screen, (83, 60, 41), (x, horizon + 45), (x, horizon - 70), 9)
            flame_y = horizon - 80 + int(math.sin(self.torch_phase + x * 0.01) * 5)
            pygame.draw.circle(screen, (219, 91, 35), (x, flame_y), 18)
            pygame.draw.circle(screen, (250, 177, 54), (x, flame_y - 4), 10)

        dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dark.fill((8, 7, 10, 38))
        screen.blit(dark, (0, 0))

    def _draw_rewards(self, screen):
        state = ensure_finale_state(self.manager)
        panel = pygame.Rect(SCREEN_WIDTH - 430, 115, 365, 175)
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        surface.fill((18, 20, 24, 222))
        screen.blit(surface, panel.topleft)
        pygame.draw.rect(screen, (167, 135, 72), panel, 2, border_radius=10)
        draw_text("TIER 1 CHARTER", font_main, GOLD_COLOR, screen, panel.x + 22, panel.y + 17)
        rewards = (
            "Bram's Recommendation",
            "Sera Quench Sponsor Letter",
            f"{int(state.get('reward_sp', FINAL_REWARD_SP) or FINAL_REWARD_SP)} SP",
            "+10 Reputation",
        )
        y = panel.y + 58
        for reward in rewards:
            draw_text(f"• {reward}", font_small, WHITE, screen, panel.x + 28, y)
            y += 27

    def draw(self, screen):
        self._ensure_started()
        self._draw_yard(screen)
        for particle in self.confetti:
            particle.draw(screen)

        pulse = 1.0 + math.sin(self.timer * 0.05) * 0.035
        title = font_title.render("TIER 1 PROMOTION", True, GOLD_COLOR)
        scaled = pygame.transform.smoothscale(
            title,
            (max(1, int(title.get_width() * pulse)), max(1, int(title.get_height() * pulse))),
        )
        screen.blit(scaled, scaled.get_rect(center=(SCREEN_WIDTH // 2, 70)))

        self._draw_rewards(screen)
        page = self.pages[self.page_index] if self.pages else {"speaker": "Bram", "text": "The ledger is closed."}
        panel = pygame.Rect(120, SCREEN_HEIGHT - 385, SCREEN_WIDTH - 240, 245)
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        surface.fill((17, 18, 22, 239))
        screen.blit(surface, panel.topleft)
        pygame.draw.rect(screen, (183, 146, 73), panel, 3, border_radius=12)
        draw_text(page["speaker"], font_main, GOLD_COLOR, screen, panel.x + 28, panel.y + 22)
        y = panel.y + 70
        for line in self._wrap(page["text"], font_main, panel.w - 56)[:5]:
            draw_text(line, font_main, WHITE, screen, panel.x + 28, y)
            y += 32
        draw_text(
            f"Farewell {self.page_index + 1}/{len(self.pages)}",
            font_small,
            GRAY,
            screen,
            panel.right - 145,
            panel.bottom - 30,
        )
        self.btn_continue.draw(screen)
