"""Interactive continent map for Varrakor world discovery and travel."""

from __future__ import annotations

import math

import pygame

from lore.world_map_data import LOCATIONS, REGIONS, ROUTES, WORLD_MAP_SIZE
from menus.base_menu import BaseMenu
from settings import SCREEN_HEIGHT, SCREEN_WIDTH
from sound_manager import sound_system
from systems.world_progression import (
    current_location_id,
    league_lore_tier,
    location_status,
    party_level,
    refresh_world_progression,
    travel_to,
    world_progress_summary,
)
from ui_kit import (
    GOLD_COLOR,
    GRAY,
    GREEN,
    RED,
    WHITE,
    UIButton,
    draw_text,
    font_main,
    font_small,
    font_title,
)


class WorldMapMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.map_rect = pygame.Rect(38, 132, 1240, SCREEN_HEIGHT - 178)
        self.info_rect = pygame.Rect(1300, 132, SCREEN_WIDTH - 1338,
                                    SCREEN_HEIGHT - 178)
        self.btn_back = UIButton(45, 45, 150, 52, "BACK", None, GRAY)
        self.btn_travel = UIButton(self.info_rect.x + 30,
                                   self.info_rect.bottom - 78,
                                   self.info_rect.w - 60, 52,
                                   "TRAVEL", None, GREEN)
        self.selected_location = "muckford"
        self.node_rects = {}
        self.feedback = ""
        self.feedback_timer = 0
        self.return_state = "hub"

    def on_enter(self):
        refresh_world_progression(self.manager)
        self.return_state = getattr(self.manager, "world_map_return_state", "hub") or "hub"
        current = current_location_id(self.manager)
        if self.selected_location not in LOCATIONS:
            self.selected_location = current
        self.feedback = ""
        self.feedback_timer = 0

    def _return(self):
        self.next_state = self.return_state
        sound_system.play_sound("click")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._return()
                return
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._attempt_travel()
                return

        if self.btn_back.is_clicked(event):
            self._return()
            return

        if self.btn_travel.is_clicked(event):
            self._attempt_travel()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for location_id, rect in self.node_rects.items():
                if rect.collidepoint(event.pos):
                    self.selected_location = location_id
                    self.feedback = ""
                    sound_system.play_sound("click")
                    return

    def _attempt_travel(self):
        ok, message, target_state = travel_to(
            self.manager, self.selected_location)
        self.feedback = message
        self.feedback_timer = 240
        sound_system.play_sound("click" if ok else "error")
        if ok and target_state:
            self.manager.world_map_return_state = "world_map"
            self.next_state = target_state

    def update(self):
        super().update()
        refresh_world_progression(self.manager)
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        self.btn_back.update_hover(pygame.mouse.get_pos())
        self.btn_travel.update_hover(pygame.mouse.get_pos())

    def _map_point(self, logical_pos):
        logical_w, logical_h = WORLD_MAP_SIZE
        x = self.map_rect.x + int(logical_pos[0] / logical_w * self.map_rect.w)
        y = self.map_rect.y + int(logical_pos[1] / logical_h * self.map_rect.h)
        return x, y

    def _wrap(self, text, font, width):
        words = str(text).split()
        lines = []
        current = ""
        for word in words:
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

    def _draw_wrapped(self, screen, text, x, y, width, color=WHITE,
                      font=font_small, line_height=22, max_lines=None):
        lines = self._wrap(text, font, width)
        if max_lines is not None:
            lines = lines[:max_lines]
        for line in lines:
            draw_text(line, font, color, screen, x, y)
            y += line_height
        return y

    def _draw_parchment(self, screen):
        self.draw_themed_background(screen, mood="city")
        parchment = pygame.Surface(self.map_rect.size, pygame.SRCALPHA)
        parchment.fill((79, 67, 50, 245))
        for y in range(0, parchment.get_height(), 18):
            shade = 10 + int(8 * math.sin(y * 0.035))
            pygame.draw.line(
                parchment,
                (105 + shade, 89 + shade, 64 + shade, 25),
                (0, y), (parchment.get_width(), y), 1,
            )
        screen.blit(parchment, self.map_rect.topleft)
        pygame.draw.rect(screen, (174, 147, 99), self.map_rect, 3,
                         border_radius=8)

    def _draw_regions(self, screen):
        for region_id, region in REGIONS.items():
            points = [self._map_point(point) for point in region["polygon"]]
            color = region["color"]
            fill = tuple(max(0, min(255, value)) for value in color)
            pygame.draw.polygon(screen, fill, points)
            pygame.draw.polygon(screen, (185, 168, 125), points, 2)

            center_x = sum(point[0] for point in points) // len(points)
            center_y = sum(point[1] for point in points) // len(points)
            label = font_small.render(region["name"], True, (225, 213, 177))
            screen.blit(label, (center_x - label.get_width() // 2,
                                center_y - label.get_height() // 2))

        # Vortex rings are deliberately placed over the Heartlands rather than
        # treated as a kingdom region.
        center = self._map_point((570, 320))
        for radius, color in ((56, (55, 25, 70)), (38, (79, 30, 91)),
                              (22, (118, 48, 120)), (9, (220, 210, 240))):
            scaled = max(4, int(radius * self.map_rect.w / WORLD_MAP_SIZE[0]))
            pygame.draw.circle(screen, color, center, scaled, 2)
        draw_text("ABYSSAL VORTEX", font_small, (232, 205, 245), screen,
                  center[0] - 65, center[1] + 42)

        draw_text("WESTERN SEA", font_small, (142, 178, 195), screen,
                  self.map_rect.x + 20, self.map_rect.centery)
        draw_text("MISTBOUND SEA", font_small, (142, 178, 195), screen,
                  self.map_rect.right - 155, self.map_rect.centery - 20)
        draw_text("SOUTHERN EXPANSE", font_small, (142, 178, 195), screen,
                  self.map_rect.centerx - 75, self.map_rect.bottom - 30)

    def _draw_routes(self, screen, discovered):
        current = current_location_id(self.manager)
        for route in ROUTES:
            a, b = route["a"], route["b"]
            if a not in discovered or b not in discovered:
                continue
            pa = self._map_point(LOCATIONS[a]["map_pos"])
            pb = self._map_point(LOCATIONS[b]["map_pos"])
            connected = current in (a, b)
            color = (205, 180, 115) if connected else (90, 83, 70)
            width = 3 if connected else 1
            pygame.draw.line(screen, color, pa, pb, width)
            if route["danger"] >= 8:
                mid = ((pa[0] + pb[0]) // 2, (pa[1] + pb[1]) // 2)
                pygame.draw.circle(screen, (170, 60, 70), mid, 3)

    def _node_color(self, location_id, status):
        location = LOCATIONS[location_id]
        if status["current"]:
            return GOLD_COLOR
        if location["content_state"] == "future":
            return (105, 72, 78)
        if status["can_travel"]:
            return (80, 205, 115)
        if status["visited"]:
            return (100, 160, 215)
        if location["content_state"] == "survey":
            return (205, 155, 78)
        return (130, 130, 135)

    def _draw_nodes(self, screen, discovered):
        self.node_rects = {}
        for location_id, location in LOCATIONS.items():
            if location_id not in discovered:
                continue
            status = location_status(self.manager, location_id)
            x, y = self._map_point(location["map_pos"])
            radius = 10 if location["kind"] in ("capital", "sanctum") else 7
            if location["kind"] == "vortex":
                radius = 6
            color = self._node_color(location_id, status)
            selected = location_id == self.selected_location

            pygame.draw.circle(screen, (20, 20, 24), (x, y), radius + 3)
            pygame.draw.circle(screen, color, (x, y), radius)
            if location.get("arena_tier") is not None:
                pygame.draw.circle(screen, (215, 155, 230), (x, y),
                                   radius + 5, 2)
            if selected:
                pulse = 3 + int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 4)
                pygame.draw.circle(screen, WHITE, (x, y), radius + 7 + pulse, 2)
            elif status["current"]:
                pygame.draw.circle(screen, WHITE, (x, y), radius + 7, 2)

            self.node_rects[location_id] = pygame.Rect(
                x - radius - 8, y - radius - 8,
                (radius + 8) * 2, (radius + 8) * 2,
            )

            if selected or status["current"] or location.get("landmark"):
                label = font_small.render(location["name"], True, WHITE)
                screen.blit(label, (x + 12, y - 10))

    def _format_level(self, level_range):
        low, high = level_range
        return f"Lv {low}" if low == high else f"Lv {low}-{high}"

    def _draw_info(self, screen):
        self.draw_soft_panel(screen, self.info_rect, alpha=205,
                             border_alpha=190, radius=10)
        location = LOCATIONS[self.selected_location]
        status = location_status(self.manager, self.selected_location)
        region = REGIONS[location["region"]]
        x = self.info_rect.x + 24
        y = self.info_rect.y + 20
        width = self.info_rect.w - 48

        title_color = self._node_color(self.selected_location, status)
        y = self._draw_wrapped(screen, location["name"], x, y, width,
                               title_color, font_main, 28, 2)
        draw_text(f"{region['name']}  |  {self._format_level(location['level_range'])}",
                  font_small, (190, 190, 185), screen, x, y + 2)
        y += 34

        if location.get("arena_tier") is not None:
            draw_text(
                f"Arena Tier {location['arena_tier']}: {location['arena_name']}",
                font_small, (215, 155, 230), screen, x, y)
            y += 26

        status_color = GREEN if status["can_travel"] else (220, 170, 95)
        y = self._draw_wrapped(screen, status["reason"], x, y, width,
                               status_color, font_small, 21, 3)
        if status["warning"] and status["warning"] != status["reason"]:
            y = self._draw_wrapped(screen, status["warning"], x, y, width,
                                   (235, 120, 90), font_small, 21, 2)
        y += 8

        y = self._draw_wrapped(screen, location["summary"], x, y, width,
                               WHITE, font_main, 25, 4)
        y += 7
        y = self._draw_wrapped(screen, location["lore"], x, y, width,
                               (205, 200, 185), font_small, 21, 6)
        y += 10

        def draw_list(label, values, color):
            nonlocal y
            if not values:
                return
            draw_text(label, font_small, color, screen, x, y)
            y += 21
            y = self._draw_wrapped(screen, " • ".join(values), x + 10, y,
                                   width - 10, (195, 195, 190),
                                   font_small, 20, 4)
            y += 6

        draw_list("SERVICES", location.get("services"), (135, 205, 165))
        draw_list("THREATS", location.get("threats"), (225, 125, 110))
        draw_list("MATERIALS", location.get("materials"), (150, 180, 225))

        content_label = {
            "playable": "PLAYABLE LOCAL AREA",
            "survey": "SURVEY CAMP / EXPANSION FOUNDATION",
            "future": "FUTURE PLAYABLE AREA",
        }.get(location["content_state"], location["content_state"].upper())
        draw_text(content_label, font_small, (155, 150, 145), screen,
                  x, self.btn_travel.rect.y - 32)

        self.btn_travel.text = (
            "YOU ARE HERE" if status["current"] else
            "TRAVEL" if status["can_travel"] else
            "LOCKED"
        )
        self.btn_travel.set_enabled(status["can_travel"])
        self.btn_travel.draw(screen)

    def draw(self, screen):
        self._draw_parchment(screen)
        title = font_title.render("VARRAKOR WORLD MAP", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=20)

        summary = world_progress_summary(self.manager)
        draw_text(
            f"Party Lv {summary['party_level']}  |  Arena Tier {summary['league_tier']}  |  "
            f"Rep {summary['reputation']}  |  Explored {summary['visited']}/{summary['total_locations']}",
            font_small, (205, 200, 185), screen, 225, 72)

        state = refresh_world_progression(self.manager)
        discovered = set(state["discovered_locations"])
        self._draw_regions(screen)
        self._draw_routes(screen, discovered)
        self._draw_nodes(screen, discovered)
        self._draw_info(screen)

        self.btn_back.draw(screen)
        if self.feedback_timer > 0 and self.feedback:
            panel = pygame.Rect(360, SCREEN_HEIGHT - 68, 900, 42)
            pygame.draw.rect(screen, (10, 10, 14), panel, border_radius=8)
            pygame.draw.rect(screen, (160, 135, 90), panel, 2,
                             border_radius=8)
            draw_text(self.feedback, font_small, WHITE, screen,
                      panel.x + 16, panel.y + 11)
