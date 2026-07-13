# menus/finale_show_menu.py
"""Grand Slam -finaalin cinematic-kuori.

Vaiheet (manager.finale_series["mode"] ohjaa):
  intro:    Bram juontaa (kuuluttajapaneeli), yleisö hurraa, kamera
            panoroi stadionin yli -> joukkueet kävelevät porteista
            kehään -> ROUND 1 -splash -> taistelu
  round:    lyhyt juonto (kierroksen juju) -> splash -> taistelu
  champion: konfetit + hurraava yleisö + CHAMPIONS-teksti -> seremonia

Eteneminen: klikkaus / E / SPACE / ENTER.
"""

import math
import random

import pygame

from menus.base_menu import BaseMenu
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from sound_manager import sound_system
from systems.grand_slam_series import get_series, ROUND_TWISTS
from ui_kit import (GOLD_COLOR, WHITE, GRAY, draw_text, font_main,
                    font_small, font_title, font_header)


class FinaleShowMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.series = get_series(manager)
        self.timer = 0
        self.arena = manager.current_arena

        # Kierroksen juju käyttöön areenalle
        rnd = int(self.series.get("round", 1))
        if hasattr(self.arena, "set_twist"):
            self.arena.set_twist(rnd)

        mode = self.series.get("mode", "intro")
        self.phase = {"intro": "announce", "round": "round_talk",
                      "champion": "champion"}[mode]
        self.script_idx = 0
        self.script = self._build_script(mode)

        # Kamera haltuun cinemaattisen ajaksi. Juonnon aikana näytetään
        # yläkatsomo + GRAND SLAM -banneri; kävelyyn keskitetään monttuun.
        self._old_camera_locked = getattr(manager, "camera_locked", True)
        manager.camera_locked = False
        if self.phase == "announce":
            self._aim_camera_at_stands()
        else:
            self._center_camera()

        # Walk-in -tiedot
        self.walk_t = 0.0
        self._walk_plan = None

        self.splash_timer = 0
        self.confetti = []
        if self.phase == "champion":
            self._spawn_confetti()
            if hasattr(self.arena, "cheer"):
                self.arena.cheer(big=True)

    # ------------------------------------------------------------------
    def _team_names(self):
        mine = "My Guild"
        try:
            flags = self.manager.npc_state.get("global", {}).get("flags", {})
            mine = flags.get("team_name") or mine
        except Exception:
            pass
        enemy = getattr(self.manager.current_enemy_team, "name", "The Rivals")
        return mine, enemy

    def _build_script(self, mode):
        mine, enemy = self._team_names()
        rnd = int(self.series.get("round", 1))
        twist_name, twist_desc = ROUND_TWISTS.get(rnd, ROUND_TWISTS[3])
        if mode == "intro":
            style = getattr(self.manager.current_enemy_team, "style", "")
            style_line = f" They fight {style.lower()}!" if style else ""
            return [
                "MUCKFORD! Quiet down, you beautiful mudlarks!",
                "The ledger is CLOSED. The season is DECIDED. "
                "Tonight - the GRAND SLAM FINAL!",
                f"From the east gate... {enemy.upper()}!{style_line}",
                f"And from the west gate... our own mud-blooded upstarts... "
                f"{mine.upper()}!",
                "BEST OF THREE FALLS! First to two victories takes the "
                "Tier 1 Charter and marches to Rattlebridge!",
                "Fighters - TO YOUR GATES!",
            ]
        if mode == "round":
            score = f"{self.series['wins']} - {self.series['losses']}"
            return [
                f"The score stands {score}! Round {rnd} - {twist_name}!",
                twist_desc,
            ]
        # champion
        return []

    # ------------------------------------------------------------------
    def _center_camera(self):
        arena = self.arena
        cx = getattr(arena, "width", SCREEN_WIDTH) // 2
        cy = getattr(arena, "height", SCREEN_HEIGHT) // 2
        self.manager.camera_x = max(0, cx - SCREEN_WIDTH // 2)
        self.manager.camera_y = max(0, cy - SCREEN_HEIGHT // 2)

    def _aim_camera_at_stands(self):
        """Juontovaihe: yläkatsomo, liput ja finaalibanneri kuvaan."""
        arena = self.arena
        cx = getattr(arena, "width", SCREEN_WIDTH) // 2
        self.manager.camera_x = max(0, cx - SCREEN_WIDTH // 2)
        self.manager.camera_y = 0

    def _plan_walk_in(self):
        """Joukkueet porttien suulta riveihin kehän keskiviivan molemmin
        puolin."""
        arena = self.arena
        gate_l = getattr(arena, "gate_left", (100, arena.height // 2))
        gate_r = getattr(arena, "gate_right", (arena.width - 100,
                                               arena.height // 2))
        cx = arena.width // 2
        cy = arena.height // 2
        plan = []
        mine = [u for u in self.manager.active_player_units if u]
        foes = [u for u in self.manager.enemy_team if u]
        for i, u in enumerate(mine):
            tx = cx - 260
            ty = cy - (len(mine) - 1) * 45 + i * 90
            u.rect.center = (int(gate_l[0]), int(gate_l[1]))
            u.facing_right = True
            plan.append((u, gate_l, (tx, ty)))
        for i, u in enumerate(foes):
            tx = cx + 260
            ty = cy - (len(foes) - 1) * 45 + i * 90
            u.rect.center = (int(gate_r[0]), int(gate_r[1]))
            u.facing_right = False
            plan.append((u, gate_r, (tx, ty)))
        return plan

    def _spawn_confetti(self):
        rng = random.Random()
        self.confetti = [{
            "x": rng.uniform(0, SCREEN_WIDTH),
            "y": rng.uniform(-500, -10),
            "v": rng.uniform(2.0, 5.0),
            "c": rng.choice([GOLD_COLOR, WHITE, (200, 70, 60),
                             (100, 160, 110), (110, 130, 190)]),
            "s": rng.randint(4, 9),
        } for _ in range(220)]

    # ------------------------------------------------------------------
    def _advance(self):
        if self.phase in ("announce", "round_talk"):
            self.script_idx += 1
            sound_system.play_sound(
                f"cheering_{random.randint(1, 4)}", volume=0.4)
            if self.script_idx >= len(self.script):
                if self.phase == "announce":
                    self.phase = "walkin"
                    self.walk_t = 0.0
                    self._walk_plan = self._plan_walk_in()
                    self._center_camera()
                else:
                    self._start_splash()
        elif self.phase == "champion":
            # Juhlista seremoniaan (farewell + palkinnot)
            self.manager.camera_locked = self._old_camera_locked
            self.next_state = "promotion_ceremony"

    def _start_splash(self):
        self.phase = "splash"
        self.splash_timer = 130
        if hasattr(self.arena, "cheer"):
            self.arena.cheer(big=True)

    def handle_event(self, event):
        if self.handle_editor_event(event):
            return
        clicked = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        keyed = (event.type == pygame.KEYDOWN and event.key in (
            pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e))
        if clicked or keyed:
            if self.phase == "walkin":
                self.walk_t = 1.0  # skippaa kävelyn loppuun
            else:
                self._advance()

    # ------------------------------------------------------------------
    def update(self):
        super().update()
        self.timer += 1

        # Areena elää koko esityksen ajan (yleisö, soihdut)
        try:
            self.arena.update(self.manager.all_units)
        except Exception:
            pass
        self.manager.vfx.update()

        if self.phase == "announce":
            # Hidas panorointi katsomon yli juonnon aikana
            arena_w = getattr(self.arena, "width", SCREEN_WIDTH)
            base = max(0, arena_w // 2 - SCREEN_WIDTH // 2)
            drift = math.sin(self.timer * 0.004) * 220
            self.manager.camera_x = max(0, int(base + drift))

        if self.phase == "walkin":
            self.walk_t = min(1.0, self.walk_t + 1.0 / 190.0)
            ease = 1 - (1 - self.walk_t) ** 2
            for u, start, target in (self._walk_plan or []):
                x = start[0] + (target[0] - start[0]) * ease
                y = start[1] + (target[1] - start[1]) * ease
                u.rect.center = (int(x), int(y))
                u.animation_state = "run" if self.walk_t < 1.0 else "idle"
            if self.walk_t >= 1.0:
                self._start_splash()

        elif self.phase == "splash":
            self.splash_timer -= 1
            if self.splash_timer <= 0:
                # Kamera takaisin pelaajalle ja taisteluun
                self.manager.camera_locked = self._old_camera_locked
                self.next_state = "battle"

        elif self.phase == "champion":
            for p in self.confetti:
                p["y"] += p["v"]
                p["x"] += math.sin(p["y"] * 0.03) * 1.4
                if p["y"] > SCREEN_HEIGHT + 12:
                    p["y"] = random.uniform(-60, -10)

    # ------------------------------------------------------------------
    def draw(self, screen):
        # Stadion + joukkueet
        self.manager.draw_game(screen)

        if self.phase in ("announce", "round_talk"):
            self._draw_announcer(screen)
        elif self.phase == "walkin":
            self._draw_walkin_banner(screen)
        elif self.phase == "splash":
            self._draw_splash(screen)
        elif self.phase == "champion":
            self._draw_champion(screen)
        self.draw_editor(screen)

    def _draw_announcer(self, screen):
        if self.script_idx >= len(self.script):
            return
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 560, SCREEN_HEIGHT - 300,
                            1120, 210)
        surf = pygame.Surface(panel.size, pygame.SRCALPHA)
        surf.fill((14, 14, 20, 235))
        screen.blit(surf, panel.topleft)
        pygame.draw.rect(screen, (196, 158, 82), panel, 3, border_radius=14)
        draw_text("BRAM MUDHAND - Master of Ceremonies", font_main,
                  GOLD_COLOR, screen, panel.x + 30, panel.y + 20)
        # rivitys
        words = self.script[self.script_idx].split()
        lines, cur = [], ""
        for w in words:
            t = w if not cur else f"{cur} {w}"
            if font_header.size(t)[0] <= panel.w - 60:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        y = panel.y + 66
        for line in lines[:3]:
            draw_text(line, font_header, WHITE, screen, panel.x + 30, y)
            y += 40
        draw_text(f"[E] continue   ({self.script_idx + 1}/{len(self.script)})",
                  font_small, GRAY, screen, panel.right - 240,
                  panel.bottom - 32)

    def _draw_walkin_banner(self, screen):
        mine, enemy = self._team_names()
        pulse = 1.0 + math.sin(self.timer * 0.08) * 0.02
        txt = font_title.render(f"{mine}  VS  {enemy}", True, GOLD_COLOR)
        txt = pygame.transform.smoothscale(
            txt, (int(txt.get_width() * pulse), int(txt.get_height() * pulse)))
        shadow = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
        shadow.blit(txt, (0, 0))
        shadow.fill((0, 0, 0, 170), special_flags=pygame.BLEND_RGBA_MULT)
        x = SCREEN_WIDTH // 2 - txt.get_width() // 2
        screen.blit(shadow, (x + 3, 63))
        screen.blit(txt, (x, 60))
        draw_text("The teams enter the arena...", font_main, (220, 215, 200),
                  screen, SCREEN_WIDTH // 2 - 150, 150)

    def _draw_splash(self, screen):
        rnd = int(self.series.get("round", 1))
        twist_name, _ = ROUND_TWISTS.get(rnd, ROUND_TWISTS[3])
        big = font_title.render(f"ROUND {rnd}", True, (255, 90, 60))
        shake_x = random.randint(-3, 3)
        screen.blit(big, (SCREEN_WIDTH // 2 - big.get_width() // 2 + shake_x,
                          SCREEN_HEIGHT // 2 - 140))
        if rnd > 1:
            sub = font_header.render(twist_name, True, GOLD_COLOR)
            screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2,
                              SCREEN_HEIGHT // 2 - 50))
        if self.splash_timer < 60:
            fight = font_title.render("FIGHT!", True, WHITE)
            screen.blit(fight,
                        (SCREEN_WIDTH // 2 - fight.get_width() // 2,
                         SCREEN_HEIGHT // 2 + 20))

    def _draw_champion(self, screen):
        veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        veil.fill((8, 6, 4, 90))
        screen.blit(veil, (0, 0))
        for p in self.confetti:
            pygame.draw.rect(screen, p["c"],
                             (int(p["x"]), int(p["y"]), p["s"] // 2 + 2,
                              p["s"]))
        mine, _ = self._team_names()
        pulse = 1.0 + math.sin(self.timer * 0.06) * 0.04
        big = font_title.render("CHAMPIONS OF THE ROOKIE DUST!", True,
                                GOLD_COLOR)
        big = pygame.transform.smoothscale(
            big, (int(big.get_width() * pulse), int(big.get_height() * pulse)))
        screen.blit(big, (SCREEN_WIDTH // 2 - big.get_width() // 2,
                          SCREEN_HEIGHT // 2 - 180))
        name = font_header.render(mine, True, WHITE)
        screen.blit(name, (SCREEN_WIDTH // 2 - name.get_width() // 2,
                           SCREEN_HEIGHT // 2 - 80))
        score = font_main.render(
            f"Series {self.series['wins']} - {self.series['losses']}",
            True, (220, 210, 180))
        screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2,
                            SCREEN_HEIGHT // 2 - 30))
        draw_text("The crowd storms the stands - Muckford roars your name!",
                  font_main, (230, 220, 200), screen,
                  SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 + 30)
        draw_text("[E] Begin the victory ceremony", font_main, GOLD_COLOR,
                  screen, SCREEN_WIDTH // 2 - 170, SCREEN_HEIGHT - 120)
