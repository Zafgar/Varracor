"""Reusable survey camp for newly reached world-map locations.

Every foundation location is reachable before bespoke local art exists. A full
city or wilderness map can later replace this state without changing location
IDs, routes or saves.
"""

from __future__ import annotations

import pygame

from lore.world_map_data import LOCATIONS, REGIONS, get_neighbors, get_route
from menus.base_menu import BaseMenu
from settings import SCREEN_HEIGHT, SCREEN_WIDTH
from sound_manager import sound_system
from systems.world_progression import (
    arena_access_status,
    current_location_id,
    league_lore_tier,
    mark_location_visited,
    party_level,
    route_key,
    survey_location,
)
from ui_kit import (
    GOLD_COLOR,
    GRAY,
    GREEN,
    WHITE,
    UIButton,
    draw_text,
    font_main,
    font_small,
    font_title,
)


class RegionalStagingMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.location_id = "muckford"
        self.feedback = ""
        self.feedback_timer = 0
        cx = SCREEN_WIDTH // 2
        self.btn_survey = UIButton(
            cx - 390,
            SCREEN_HEIGHT - 120,
            240,
            58,
            "SURVEY AREA",
            None,
            (185, 145, 75),
        )
        self.btn_arena = UIButton(
            cx - 120,
            SCREEN_HEIGHT - 120,
            240,
            58,
            "ARENA DISTRICT",
            None,
            GREEN,
        )
        self.btn_map = UIButton(
            cx + 150,
            SCREEN_HEIGHT - 120,
            240,
            58,
            "WORLD MAP",
            None,
            (105, 135, 190),
        )
        self.btn_back = UIButton(40, 40, 160, 52, "WORLD MAP", None, GRAY)

    def on_enter(self):
        pending = getattr(self.manager, "pending_world_location", None)
        self.location_id = (
            pending if pending in LOCATIONS else current_location_id(self.manager)
        )
        mark_location_visited(self.manager, self.location_id, set_current=True)
        self.manager.pending_world_location = self.location_id
        self.feedback = ""
        self.feedback_timer = 0
        self._sync_buttons()

    def _world_state(self):
        return self.manager.npc_state["world_progression"]

    def _sync_buttons(self):
        state = self._world_state()
        surveyed = self.location_id in state.get("surveyed_locations", ())
        self.btn_survey.text = "AREA SURVEYED" if surveyed else "SURVEY AREA"
        self.btn_survey.set_enabled(not surveyed)

        arena_ok, _reason = arena_access_status(
            self.manager,
            self.location_id,
        )
        location = LOCATIONS[self.location_id]
        self.btn_arena.text = location.get("arena_name") or "NO ARENA"
        self.btn_arena.set_enabled(arena_ok)

    def _open_world_map(self):
        self.manager.world_map_return_state = "regional_staging"
        self.next_state = "world_map"
        sound_system.play_sound("click")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._open_world_map()
            return

        if self.btn_back.is_clicked(event) or self.btn_map.is_clicked(event):
            self._open_world_map()
            return

        if self.btn_survey.is_clicked(event):
            opened = survey_location(self.manager, self.location_id)
            if opened:
                names = ", ".join(
                    LOCATIONS[item]["name"] for item in opened[:4]
                )
                self.feedback = f"Survey complete. New roads mapped: {names}."
            else:
                self.feedback = "Survey complete. No additional safe roads found."
            self.feedback_timer = 300
            sound_system.play_sound("click")
            self._sync_buttons()
            return

        if self.btn_arena.is_clicked(event):
            ok, reason = arena_access_status(
                self.manager,
                self.location_id,
            )
            self.feedback = reason
            self.feedback_timer = 240
            if ok:
                self.manager.current_arena_location = self.location_id
                self.manager.league_return_state = "regional_staging"
                self.next_state = "league"
                sound_system.play_sound("click")
            else:
                sound_system.play_sound("error")

    def update(self):
        super().update()
        mouse = pygame.mouse.get_pos()
        for button in (
            self.btn_survey,
            self.btn_arena,
            self.btn_map,
            self.btn_back,
        ):
            button.update_hover(mouse)
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        self._sync_buttons()

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

    def _draw_wrapped(
        self,
        screen,
        text,
        x,
        y,
        width,
        color=WHITE,
        font=font_small,
        line_height=24,
        limit=None,
    ):
        lines = self._wrap(text, font, width)
        if limit:
            lines = lines[:limit]
        for line in lines:
            draw_text(line, font, color, screen, x, y)
            y += line_height
        return y

    def _draw_region_scene(self, screen, region):
        color = region["color"]
        screen.fill(tuple(max(0, value - 35) for value in color))
        horizon = int(SCREEN_HEIGHT * 0.52)
        pygame.draw.rect(
            screen,
            tuple(max(0, value - 15) for value in color),
            (0, horizon, SCREEN_WIDTH, SCREEN_HEIGHT - horizon),
        )

        mountain_ids = {
            "highstone_sanctum",
            "spirewatch",
            "windstep",
            "gleamhold",
            "ironwind_pass",
            "sanctum_marches",
            "prismhall",
        }
        desert_ids = {
            "saffron_oasis",
            "kestrel_way",
            "hornfall",
            "stonegrit",
            "kharak_tor",
            "howling_barrens",
            "bonewind_necropolis",
        }
        forest_ids = {
            "vinehollow",
            "timbercross",
            "elderroot_grove",
            "moonwatch",
            "deep_wyrdwood",
        }

        if self.location_id in mountain_ids:
            for index in range(9):
                x = index * 260 - 80
                height = 170 + (index % 3) * 75
                pygame.draw.polygon(
                    screen,
                    (55, 62, 75),
                    [
                        (x, horizon),
                        (x + 150, horizon - height),
                        (x + 300, horizon),
                    ],
                )
        elif self.location_id in desert_ids:
            for index in range(7):
                x = index * 330 - 120
                pygame.draw.polygon(
                    screen,
                    (105, 72, 45),
                    [
                        (x, horizon + 40),
                        (x + 170, horizon - 70),
                        (x + 360, horizon + 40),
                    ],
                )
        elif self.location_id in forest_ids:
            for index in range(20):
                x = index * 105
                height = 120 + (index % 5) * 24
                pygame.draw.rect(
                    screen,
                    (35, 58, 40),
                    (x + 35, horizon - height + 40, 14, height),
                )
                pygame.draw.circle(
                    screen,
                    (42, 78, 50),
                    (x + 42, horizon - height + 25),
                    58,
                )
        else:
            for index in range(12):
                x = index * 170
                height = 55 + (index % 4) * 20
                pygame.draw.polygon(
                    screen,
                    (60, 53, 50),
                    [
                        (x, horizon + 20),
                        (x + 70, horizon - height),
                        (x + 150, horizon + 20),
                    ],
                )

        mist = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        for index in range(8):
            pygame.draw.ellipse(
                mist,
                (210, 205, 185, 16 + index * 5),
                (
                    -150 + index * 280,
                    horizon - 40 + (index % 2) * 35,
                    430,
                    110,
                ),
            )
        screen.blit(mist, (0, 0))

    @staticmethod
    def _format_level(levels):
        low, high = levels
        return f"Lv {low}" if low == high else f"Lv {low}-{high}"

    def _draw_lists(self, screen, location, x, y, width):
        groups = (
            ("SERVICES", location.get("services", ()), (145, 215, 165)),
            ("THREATS", location.get("threats", ()), (230, 135, 120)),
            ("MATERIALS", location.get("materials", ()), (155, 185, 230)),
        )
        for label, values, color in groups:
            if not values:
                continue
            draw_text(label, font_small, color, screen, x, y)
            y += 23
            y = self._draw_wrapped(
                screen,
                " • ".join(values),
                x + 12,
                y,
                width - 12,
                (210, 207, 196),
                font_small,
                22,
                3,
            )
            y += 8
        return y

    def _draw_routes(self, screen, x, y, width):
        draw_text(
            "SURVEYED ROADS",
            font_small,
            (210, 185, 120),
            screen,
            x,
            y,
        )
        y += 26
        state = self._world_state()
        known_routes = set(state.get("discovered_routes", ()))
        shown = 0
        for neighbor in get_neighbors(self.location_id):
            if route_key(self.location_id, neighbor) not in known_routes:
                continue
            route = get_route(self.location_id, neighbor)
            target = LOCATIONS[neighbor]
            line = (
                f"{target['name']} — {route['hours']}h — "
                f"danger {route['danger']}/10"
            )
            y = self._draw_wrapped(
                screen,
                line,
                x + 12,
                y,
                width - 12,
                (205, 202, 192),
                font_small,
                21,
                2,
            )
            shown += 1
        if shown == 0:
            y = self._draw_wrapped(
                screen,
                "No outbound road has been mapped. Survey the area first.",
                x + 12,
                y,
                width - 12,
                (205, 170, 115),
                font_small,
                21,
                3,
            )
        return y

    def draw(self, screen):
        location = LOCATIONS[self.location_id]
        region = REGIONS[location["region"]]
        self._draw_region_scene(screen, region)

        dark = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        dark.fill((5, 5, 8, 82))
        screen.blit(dark, (0, 0))

        title = font_title.render(location["name"], True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=20)
        self.btn_back.draw(screen)

        left = pygame.Rect(70, 145, 910, 710)
        right = pygame.Rect(1010, 145, 840, 710)
        self.draw_soft_panel(screen, left, alpha=205, border_alpha=180, radius=12)
        self.draw_soft_panel(screen, right, alpha=205, border_alpha=180, radius=12)

        x, y = left.x + 30, left.y + 28
        draw_text(region["name"], font_main, region["color"], screen, x, y)
        y += 34
        draw_text(
            f"{self._format_level(location['level_range'])}  |  "
            f"Party Lv {party_level(self.manager)}  |  "
            f"Arena Tier {league_lore_tier(self.manager)}",
            font_small,
            (205, 202, 192),
            screen,
            x,
            y,
        )
        y += 38
        y = self._draw_wrapped(
            screen,
            location["summary"],
            x,
            y,
            left.w - 60,
            WHITE,
            font_main,
            28,
            5,
        )
        y += 12
        y = self._draw_wrapped(
            screen,
            location["lore"],
            x,
            y,
            left.w - 60,
            (210, 205, 190),
            font_small,
            23,
            8,
        )
        y += 18

        state = self._world_state()
        surveyed = self.location_id in state.get("surveyed_locations", ())
        camp_text = (
            "The route camp is established and the surrounding approaches "
            "have been surveyed."
            if surveyed
            else "Your team has reached the route camp. Surveying maps nearby "
            "roads and prepares this location for full local-map expansion."
        )
        y = self._draw_wrapped(
            screen,
            camp_text,
            x,
            y,
            left.w - 60,
            (170, 205, 180),
            font_small,
            23,
            6,
        )

        if location.get("arena_tier") is not None:
            y += 14
            arena_ok, arena_reason = arena_access_status(
                self.manager,
                self.location_id,
            )
            y = self._draw_wrapped(
                screen,
                f"Arena: {location['arena_name']} — {arena_reason}",
                x,
                y,
                left.w - 60,
                GREEN if arena_ok else (220, 170, 95),
                font_small,
                23,
                5,
            )

        x2, y2 = right.x + 30, right.y + 28
        y2 = self._draw_lists(screen, location, x2, y2, right.w - 60)
        y2 += 10
        self._draw_routes(screen, x2, y2, right.w - 60)

        content_text = {
            "playable": "This location has a dedicated playable local map.",
            "survey": (
                "This camp is playable now. A full city or wilderness map can "
                "replace it later without changing saves or roads."
            ),
            "future": "The map node exists, but its local content is not ready.",
        }.get(location["content_state"], "")
        self._draw_wrapped(
            screen,
            content_text,
            right.x + 30,
            right.bottom - 95,
            right.w - 60,
            (155, 150, 145),
            font_small,
            21,
            4,
        )

        for button in (self.btn_survey, self.btn_arena, self.btn_map):
            button.draw(screen)

        if self.feedback_timer > 0 and self.feedback:
            panel = pygame.Rect(420, SCREEN_HEIGHT - 190, 1080, 46)
            pygame.draw.rect(screen, (12, 12, 16), panel, border_radius=8)
            pygame.draw.rect(
                screen,
                (180, 150, 95),
                panel,
                2,
                border_radius=8,
            )
            draw_text(
                self.feedback,
                font_small,
                WHITE,
                screen,
                panel.x + 16,
                panel.y + 12,
            )
