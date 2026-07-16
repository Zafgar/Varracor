"""Playable Rattlebridge Canalworks patrol zone.

This is a lightweight exploration/combat-resolution area for the first
Rattlebridge contracts. It uses the Commander sprite, collision lanes, three
persistent swarm nests and an unlockable Gutter Swarm mass encounter.
"""

from __future__ import annotations

import math
import random

import pygame

from citys.rattlebridge.interior_scenes import CanalworksScene
from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, RED, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from systems.world_progression import party_level
from ui_kit import draw_text, font_main, font_small, font_title


class CanalworksMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.rng = random.Random(91337)
        self.player = manager.player_character
        self.feedback = ""
        self.feedback_timer = 0
        self.nearby_target = None
        self.walkable = [
            pygame.Rect(0, 65, SCREEN_WIDTH, 135),
            pygame.Rect(0, 420, SCREEN_WIDTH, 235),
            pygame.Rect(0, 920, SCREEN_WIDTH, 130),
            pygame.Rect(230, 0, 190, SCREEN_HEIGHT),
            pygame.Rect(760, 0, 210, SCREEN_HEIGHT),
            pygame.Rect(1360, 0, 190, SCREEN_HEIGHT),
        ]
        self.blockers = [
            pygame.Rect(475, 430, 120, 90),
            pygame.Rect(1035, 540, 130, 80),
            pygame.Rect(1180, 930, 95, 90),
            pygame.Rect(45, 520, 110, 80),
        ]
        self.nest_points = [
            (325, 140),
            (865, 545),
            (1450, 980),
        ]
        self.boss_point = (1210, 525)
        self.exit_rect = pygame.Rect(70, 80, 145, 85)
        # Kohtaus maalataan suoraan ylla olevasta layoutista, joten grafiikka
        # vastaa aina kavelykaistoja, esteita ja pesapaikkoja.
        self.scene = CanalworksScene(self.walkable, self.blockers,
                                     self.nest_points, self.boss_point,
                                     self.exit_rect)

    def _state(self):
        root = self.manager.npc_state.setdefault("rattlebridge", {})
        nests = root.setdefault("canal_nests", [False, False, False])
        if len(nests) != 3:
            root["canal_nests"] = [False, False, False]
        root.setdefault("gutter_patrols", sum(bool(item) for item in root["canal_nests"]))
        root.setdefault("gutter_boss_defeated", False)
        root.setdefault("canal_visits", 0)
        return root

    def on_enter(self):
        self.player = self.manager.player_character
        self.player.rect.center = (180, 145)
        self.manager.city_spawn_point = "canalworks"
        self._state()["canal_visits"] += 1
        try:
            sound_system.play_music("assets/music/swamp_theme.mp3")
        except Exception:
            pass

    def _roster(self):
        roster = []
        if getattr(self.manager, "player_character", None):
            roster.append(self.manager.player_character)
        roster.extend(list(getattr(self.manager, "my_team", ())))
        return roster

    def _walkable(self, rect):
        if not any(zone.collidepoint(rect.center) for zone in self.walkable):
            return False
        return not any(rect.colliderect(blocker) for blocker in self.blockers)

    def _move(self):
        # Yhtenäinen kävelytilan ohjaus (systems/walk_control.py)
        from systems import walk_control
        walk_control.move_player(
            self.player,
            walkable=self._walkable,
            camera=(getattr(self, "camera_x", 0), getattr(self, "camera_y", 0)))
        try:
            self.player.update(self.blockers, self.manager)
        except Exception:
            pass

    def _target_distance(self, point):
        return math.hypot(
            self.player.rect.centerx - point[0],
            self.player.rect.bottom - point[1],
        )

    def _refresh_target(self):
        self.nearby_target = None
        if self.player.rect.colliderect(self.exit_rect.inflate(50, 50)):
            self.nearby_target = ("exit", None)
            return
        state = self._state()
        for index, point in enumerate(self.nest_points):
            if not state["canal_nests"][index] and self._target_distance(point) < 92:
                self.nearby_target = ("nest", index)
                return
        if (all(state["canal_nests"])
                and not state["gutter_boss_defeated"]
                and self._target_distance(self.boss_point) < 120):
            self.nearby_target = ("boss", None)

    def _damage_roster(self, base):
        level = party_level(self.manager)
        damage = max(2, int(base - level * 0.65))
        for unit in self._roster():
            current = int(getattr(unit, "current_hp", 1))
            unit.current_hp = max(1, current - damage)
        return damage

    def _grant_material(self, name, amount):
        try:
            self.manager.add_material(name, amount)
        except Exception:
            inventory = getattr(self.manager, "inventory", None)
            if not isinstance(inventory, dict):
                self.manager.inventory = {}
                inventory = self.manager.inventory
            inventory[name] = inventory.get(name, 0) + amount

    def _clear_nest(self, index):
        state = self._state()
        if state["canal_nests"][index]:
            return
        damage = self._damage_roster(13 + index * 2)
        state["canal_nests"][index] = True
        state["gutter_patrols"] = sum(bool(item) for item in state["canal_nests"])
        self.manager.gold = int(getattr(self.manager, "gold", 0)) + 12 + index * 4
        self._grant_material("Scrap Iron", 1 + (index % 2))
        if index >= 1:
            self._grant_material("Nightcap Fungus", 1)
        self.feedback = (
            f"Swarm nest {index + 1} cleared. The roster takes {damage} damage. "
            "Contaminated salvage recovered."
        )
        self.feedback_timer = 260
        sound_system.play_sound("coin")

    def _fight_boss(self):
        state = self._state()
        if state["gutter_boss_defeated"]:
            return
        level = party_level(self.manager)
        if level < 8:
            damage = self._damage_roster(24)
            self.feedback = (
                f"The fused Gutter Swarm overwhelms the patrol. The team takes {damage} damage and retreats."
            )
            self.feedback_timer = 280
            sound_system.play_sound("error")
            self.player.rect.center = (180, 145)
            return
        damage = self._damage_roster(20)
        state["gutter_boss_defeated"] = True
        state["gutter_swarm_kills"] = int(state.get("gutter_swarm_kills", 0)) + 1
        self.manager.gold = int(getattr(self.manager, "gold", 0)) + 85
        try:
            self.manager.reputation += 8
        except Exception:
            global_state = self.manager.npc_state.setdefault("global", {})
            global_state["reputation"] = int(global_state.get("reputation", 0)) + 8
        self._grant_material("Direhide", 1)
        self._grant_material("Nightcap Fungus", 2)
        self.feedback = (
            f"Gutter Swarm mass destroyed. The roster takes {damage} damage. "
            "Bridgeguard reputation and rare salvage gained."
        )
        self.feedback_timer = 320
        sound_system.play_sound("coin")

    def _interact(self):
        if not self.nearby_target:
            return
        kind, index = self.nearby_target
        if kind == "exit":
            self.manager.city_spawn_point = "canalworks"
            self.next_state = "rattlebridge_city"
            sound_system.play_sound("click")
        elif kind == "nest":
            self._clear_nest(index)
        elif kind == "boss":
            self._fight_boss()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.city_spawn_point = "canalworks"
                self.next_state = "rattlebridge_city"
                return
            if event.key == pygame.K_e:
                self._interact()
                return

    def update(self):
        super().update()
        self._move()
        self._refresh_target()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        try:
            self.manager.world_clock.update()
        except Exception:
            pass

    def _draw_player(self, screen):
        try:
            self.player.draw_on_screen(screen, (0, 0))
        except Exception:
            pygame.draw.rect(screen, GREEN, self.player.rect)

    def _draw_nest(self, screen, index, point, cleared):
        x, y = point
        if cleared:
            pygame.draw.circle(screen, (65, 58, 51), (x, y), 34)
            pygame.draw.line(screen, (125, 110, 85),
                             (x - 24, y - 20), (x + 25, y + 20), 5)
            return
        pulse = 4 + int(abs(math.sin(pygame.time.get_ticks() * 0.005 + index)) * 7)
        pygame.draw.circle(screen, (58, 105, 59), (x, y), 34 + pulse)
        pygame.draw.circle(screen, (115, 68, 48), (x, y), 28)
        for angle in range(0, 360, 45):
            radians = math.radians(angle + pygame.time.get_ticks() * 0.02)
            rx = x + int(math.cos(radians) * 45)
            ry = y + int(math.sin(radians) * 31)
            pygame.draw.circle(screen, (80, 75, 60), (rx, ry), 7)

    def _draw_boss(self, screen, defeated):
        if defeated:
            return
        x, y = self.boss_point
        pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.004)) * 14)
        pygame.draw.circle(screen, (35, 52, 42), (x, y), 70 + pulse)
        pygame.draw.circle(screen, (82, 122, 72), (x, y), 62)
        for index in range(12):
            angle = index / 12 * math.tau
            px = x + int(math.cos(angle) * 78)
            py = y + int(math.sin(angle) * 52)
            pygame.draw.circle(screen, (92, 67, 48), (px, py), 10)

    def draw(self, screen):
        # Kanaalikohtaus sisaltaa kaistat, esteet, ritilat ja tippuvan veden.
        self.scene.draw(screen)
        pygame.draw.rect(screen, (125, 100, 64), self.exit_rect, 3, border_radius=8)
        draw_text("LIFT EXIT", font_small, WHITE, screen,
                  self.exit_rect.x + 27, self.exit_rect.y + 30)

        state = self._state()
        for index, point in enumerate(self.nest_points):
            self._draw_nest(screen, index, point, state["canal_nests"][index])
        if all(state["canal_nests"]):
            self._draw_boss(screen, state["gutter_boss_defeated"])

        self._draw_player(screen)
        title = font_title.render("RATTLEBRIDGE CANALWORKS", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=18)
        draw_text(
            f"Party Lv {party_level(self.manager)}  |  Nests {sum(state['canal_nests'])}/3  |  "
            f"Gutter mass {'defeated' if state['gutter_boss_defeated'] else 'active'}",
            font_main, WHITE, screen, 40, 92,
        )

        prompt = None
        if self.nearby_target:
            kind, index = self.nearby_target
            if kind == "exit":
                prompt = "E: Return to Rattlebridge"
            elif kind == "nest":
                prompt = f"E: Clear swarm nest {index + 1}"
            else:
                prompt = "E: Engage the fused Gutter Swarm"
        if prompt:
            width = font_main.size(prompt)[0] + 60
            box = pygame.Rect(SCREEN_WIDTH // 2 - width // 2,
                              SCREEN_HEIGHT - 92, width, 48)
            pygame.draw.rect(screen, (15, 18, 18), box, border_radius=9)
            pygame.draw.rect(screen, (145, 165, 105), box, 2, border_radius=9)
            draw_text(prompt, font_main, WHITE, screen,
                      box.x + 30, box.y + 12)

        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(280, 150, SCREEN_WIDTH - 560, 64)
            pygame.draw.rect(screen, (17, 20, 20), box, border_radius=9)
            pygame.draw.rect(screen, (145, 130, 88), box, 2, border_radius=9)
            draw_text(self.feedback, font_main, WHITE,
                      screen, box.x + 22, box.y + 19)

        draw_text("WASD move • SHIFT sprint • E interact • ESC leave",
                  font_small, GRAY, screen, 30, SCREEN_HEIGHT - 32)
