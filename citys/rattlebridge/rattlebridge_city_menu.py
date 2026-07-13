"""Playable Rattlebridge city hub.

Rattlebridge is a large bridge-city with a procedural fallback map, ambient
population, named NPCs, district travel, local map and persistent city state.
"""

from __future__ import annotations

import math
import random

import pygame

from citys.rattlebridge.rattlebridge_art import load_rattlebridge_image
from citys.rattlebridge.rattlebridge_data import (
    AMBIENT_LINES,
    DISTRICTS,
    NAMED_NPCS,
)
from citys.rattlebridge.rattlebridge_map import RattlebridgeCityMap
from menus.base_menu import BaseMenu
from races import get_random_name
from settings import (
    GOLD_COLOR,
    GRAY,
    GREEN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from sound_manager import sound_system
from systems.world_progression import mark_location_visited
from ui_kit import draw_text, font_main, font_small, font_title
from units.villager import Villager


class _FreightCart:
    """Kansia pitkin kulkeva rahtikärry vetäjineen (pelkkä ambient-visuaali,
    ei törmäystä). Pyörät pyörivät kuljetun matkan mukaan."""

    def __init__(self, x, y, direction, speed, cargo_color, world_width):
        self.rect = pygame.Rect(int(x), int(y) - 46, 150, 62)
        self.direction = direction
        self.speed = speed
        self.cargo_color = cargo_color
        self.world_width = world_width
        self.travelled = float(x)

    def update(self):
        step = self.speed * self.direction
        self.rect.x += int(round(step))
        self.travelled += abs(step)
        if self.direction > 0 and self.rect.left > self.world_width + 80:
            self.rect.right = -60
        elif self.direction < 0 and self.rect.right < -80:
            self.rect.left = self.world_width + 60

    def draw(self, screen, offset):
        r = self.rect.move(-offset[0], -offset[1])
        if r.right < -60 or r.left > SCREEN_WIDTH + 60:
            return
        flip = self.direction < 0
        # Lava + laidat
        bed = pygame.Rect(r.left + 18, r.top + 14, 108, 30)
        pygame.draw.rect(screen, (96, 70, 44), bed, border_radius=6)
        pygame.draw.rect(screen, (62, 46, 32), bed, 3, border_radius=6)
        # Lasti
        crate = pygame.Rect(bed.left + 12, bed.top - 20, 34, 28)
        pygame.draw.rect(screen, self.cargo_color, crate, border_radius=4)
        pygame.draw.rect(screen, (50, 42, 34), crate, 2, border_radius=4)
        barrel = pygame.Rect(bed.left + 56, bed.top - 16, 30, 24)
        pygame.draw.ellipse(screen, (118, 88, 54), barrel)
        pygame.draw.ellipse(screen, (70, 52, 36), barrel, 2)
        # Pyörät pinnoilla; kulma kuljetusta matkasta
        angle = self.travelled * 0.05
        for wx in (bed.left + 20, bed.right - 20):
            pygame.draw.circle(screen, (48, 42, 36), (wx, r.bottom - 8), 15)
            pygame.draw.circle(screen, (86, 74, 58), (wx, r.bottom - 8), 15, 3)
            for k in range(3):
                a = angle + k * (math.pi / 3)
                pygame.draw.line(screen, (86, 74, 58),
                                 (wx - math.cos(a) * 12, r.bottom - 8 - math.sin(a) * 12),
                                 (wx + math.cos(a) * 12, r.bottom - 8 + math.sin(a) * 12), 2)
        # Aisat + vetäjä (kansityöläinen)
        puller_x = r.right + 26 if not flip else r.left - 26
        hitch_x = bed.right if not flip else bed.left
        pygame.draw.line(screen, (70, 54, 38), (hitch_x, bed.centery),
                         (puller_x - (8 if flip else -8), r.bottom - 26), 4)
        body = pygame.Rect(puller_x - 12, r.bottom - 44, 24, 34)
        pygame.draw.rect(screen, (104, 88, 64), body, border_radius=8)
        head_y = r.bottom - 52
        pygame.draw.circle(screen, (210, 172, 140), (puller_x, head_y), 9)
        # Jalkojen askelheilunta
        swing = math.sin(self.travelled * 0.09) * 6
        pygame.draw.line(screen, (58, 48, 38), (puller_x - 4, r.bottom - 12),
                         (puller_x - 4 + swing, r.bottom + 2), 4)
        pygame.draw.line(screen, (58, 48, 38), (puller_x + 4, r.bottom - 12),
                         (puller_x + 4 - swing, r.bottom + 2), 4)


class RattlebridgeCityMenu(BaseMenu):
    POPULATION = 72
    # Lore: kääpiöt, gnomit ja örkit ovat Rattlebridgessä yleisiä
    # (Ironspan Union, Scrapringin nikkarit, sillan raskas rahti).
    POPULATION_RACES = ("Human", "Human", "Human", "Dwarf", "Dwarf",
                        "Orc", "Gnome", "Goblin", "Elf")

    def __init__(self, manager):
        super().__init__(manager)
        self.rng = random.Random(49117)
        self.city = RattlebridgeCityMap()
        self.arena = self.city
        self.player = manager.player_character
        self.npcs = []
        self.named_npcs = {}
        self.camera_x = 0
        self.camera_y = 0
        self.show_map = False
        self.dialogue_npc = None
        self.dialogue_line = 0
        self.feedback = ""
        self.feedback_timer = 0
        self.current_district = None
        self.district_banner_timer = 0
        self._nearby_landmark = None
        self._nearby_npc = None
        self.hush_timer = self.rng.randint(2400, 4800)
        self.hush_active = 0
        self.hush_alpha = 0
        self.ambient_timer = self.rng.randint(360, 840)
        self.ambient_speaker = None
        self.ambient_text = ""
        self.ambient_text_timer = 0
        self.carts = []
        self._spawn_population()
        self._spawn_named_npcs()
        self._spawn_patrols()
        self._spawn_carts()
        self._place_player("west_gate")
        self._update_camera()

    def _state(self):
        root = self.manager.npc_state.setdefault("rattlebridge", {})
        root.setdefault("visited", True)
        root.setdefault("hush_mantle_sightings", 0)
        root.setdefault("gutter_patrols", 0)
        root.setdefault("customs_checked", False)
        root.setdefault("sera_introduced", False)
        root.setdefault("districts_visited", [])
        return root

    def on_enter(self):
        self.player = self.manager.player_character
        self.manager.current_arena = self.city
        mark_location_visited(self.manager, "rattlebridge", set_current=True)
        self.manager.pending_world_location = "rattlebridge"
        spawn = getattr(self.manager, "city_spawn_point", None)
        self.manager.city_spawn_point = None
        self._place_player(spawn or "west_gate")
        self._update_camera()
        try:
            sound_system.play_music("assets/music/city_theme.mp3")
        except Exception:
            try:
                sound_system.play_music("assets/music/swamp_theme.mp3")
            except Exception:
                pass

    def _place_player(self, spawn):
        points = {
            "west_gate": self.city.spawn_points[0],
            "the_span": self.city.landmarks["the_span"].interaction_point,
            "hospital": self.city.landmarks["bridgeward_hospital"].interaction_point,
            "scrapring": self.city.landmarks["scrapring_gate"].interaction_point,
            "canalworks": self.city.landmarks["canalworks_lift"].interaction_point,
            "market": self.city.landmarks["union_market"].interaction_point,
            "storage": self.city.landmarks["freight_warehouse"].interaction_point,
        }
        x, y = points.get(spawn, points["west_gate"])
        self.player.rect.centerx = int(x)
        self.player.rect.bottom = int(y)
        if not self.city.is_walkable(self.player.rect):
            self.player.rect.center = self.city.main_deck.center
        self.player.facing_right = True

    def _spawn_population(self):
        districts = tuple(DISTRICTS)
        for index in range(self.POPULATION):
            district_id = self.rng.choice(districts)
            x, y = self.city.random_walkable_point(district_id)
            race = self.rng.choice(self.POPULATION_RACES)
            npc = Villager(get_random_name(race), race, x, y, GREEN)
            npc.rattle_role = self.rng.choice((
                "Bridge Worker",
                "Freight Porter",
                "Toll Clerk",
                "Arena Fan",
                "Union Laborer",
                "Caravan Guard",
                "Sponsor Runner",
                "Gear Tender",
                "Lantern Lighter",
                "Quarantine Sister",
            ))
            npc.home_district = district_id
            npc.sim_state = "IDLE"
            npc.sim_timer = self.rng.randint(30, 240)
            npc.sim_target = (x, y)
            if getattr(npc, "ai_controller", None):
                npc.ai_controller.allow_idle_wander = False
            self.npcs.append(npc)

    def _spawn_named_npcs(self):
        for npc_id, data in NAMED_NPCS.items():
            x = int(data["position_norm"][0] * self.city.width)
            y = int(data["position_norm"][1] * self.city.height)
            npc = Villager(data["name"], data["race"], x, y, GREEN)
            npc.rattle_id = npc_id
            npc.rattle_role = data["role"]
            npc.dialogue_lines = tuple(data["dialogue"])
            npc.sim_state = "FIXED"
            npc.animation_state = "idle"
            npc.facing_right = True
            if getattr(npc, "ai_controller", None):
                npc.ai_controller.allow_idle_wander = False
            self.named_npcs[npc_id] = npc
            self.npcs.append(npc)

    def _spawn_patrols(self):
        """Bridgeguard-partiot kiertävät kansia kiinteitä reittejä.
        Käytetään olemassa olevaa Villager-luokkaa (rotu + rooli)."""
        city = self.city
        main_y = city.main_deck.centery + 60
        low_y = city.lower_deck.centery - 40
        routes = (
            [(int(city.width * fx), main_y) for fx in (0.10, 0.34, 0.58, 0.86)],
            [(int(city.width * fx), low_y) for fx in (0.82, 0.55, 0.30, 0.14)],
        )
        for route_index, points in enumerate(routes):
            for offset_index in range(2):
                race = ("Human", "Orc", "Dwarf", "Human")[route_index * 2 + offset_index]
                npc = Villager(get_random_name(race), race,
                               points[0][0] + offset_index * 46,
                               points[0][1] + offset_index * 20,
                               (100, 125, 165))
                npc.rattle_role = "Bridgeguard Patrol"
                npc.sim_state = "PATROL"
                npc.patrol_points = points
                npc.patrol_index = (offset_index * 2) % len(points)
                npc.patrol_offset = (offset_index * 46, offset_index * 20)
                npc.sim_timer = 0
                if getattr(npc, "ai_controller", None):
                    npc.ai_controller.allow_idle_wander = False
                self.npcs.append(npc)

    def _spawn_carts(self):
        """Rahtikärryt kiertävät pää- ja alakantta (Ironspan-rahti)."""
        city = self.city
        lanes = (
            (city.main_deck.bottom - 90, 1),
            (city.main_deck.top + 120, -1),
            (city.lower_deck.centery + 90, 1),
        )
        cargo = ((122, 90, 52), (86, 96, 74), (104, 76, 88))
        for index, (lane_y, direction) in enumerate(lanes):
            self.carts.append(_FreightCart(
                self.rng.randint(0, city.width),
                lane_y,
                direction,
                0.9 + index * 0.25,
                cargo[index % len(cargo)],
                city.width,
            ))

    def _distance_to_npc(self, npc):
        return math.hypot(
            self.player.rect.centerx - npc.rect.centerx,
            self.player.rect.bottom - npc.rect.bottom,
        )

    def _nearest_npc(self, distance=86):
        nearest = None
        nearest_distance = distance
        for npc in self.npcs:
            current = self._distance_to_npc(npc)
            if current < nearest_distance:
                nearest = npc
                nearest_distance = current
        return nearest

    def _open_dialogue(self, npc):
        self.dialogue_npc = npc
        self.dialogue_line = 0
        if getattr(npc, "rattle_id", None) == "sera_quench":
            self._state()["sera_introduced"] = True
        sound_system.play_sound("click")

    def _close_dialogue(self):
        self.dialogue_npc = None
        self.dialogue_line = 0

    def _advance_dialogue(self):
        if not self.dialogue_npc:
            return
        lines = getattr(self.dialogue_npc, "dialogue_lines", ())
        if self.dialogue_line + 1 < len(lines):
            self.dialogue_line += 1
            sound_system.play_sound("click")
        else:
            self._close_dialogue()

    def _enter_landmark(self, landmark):
        state = landmark.target_state
        if landmark.landmark_id in {"world_gate", "east_gate"}:
            self.manager.world_map_return_state = "rattlebridge_city"
            self.next_state = "world_map"
            return
        if landmark.landmark_id == "customs_office":
            self._state()["customs_checked"] = True
            self.feedback = (
                "Crown toll notice: arena teams are exempt from entry fees, "
                "not cargo taxes."
            )
            self.feedback_timer = 260
            sound_system.play_sound("click")
            return
        if landmark.landmark_id == "sera_office":
            self._open_dialogue(self.named_npcs["sera_quench"])
            return
        if landmark.landmark_id == "guard_barracks":
            self._open_dialogue(self.named_npcs["captain_mara_chain"])
            return
        if state:
            if state == "market":
                self.manager.market_return_state = "rattlebridge_city"
                self.manager.city_spawn_point = "market"
            elif state == "city_storage":
                self.manager.city_storage_return_state = "rattlebridge_city"
                self.manager.city_spawn_point = "storage"
            elif state == "rattlebridge_span":
                self.manager.city_spawn_point = "the_span"
            elif state == "rattlebridge_hospital":
                self.manager.city_spawn_point = "hospital"
            elif state == "rattlebridge_scrapring":
                self.manager.city_spawn_point = "scrapring"
            elif state == "rattlebridge_canalworks":
                self.manager.city_spawn_point = "canalworks"
            self.next_state = state
            sound_system.play_sound("click")

    def _interact(self):
        if self.dialogue_npc:
            self._advance_dialogue()
            return
        landmark = self.city.nearby_landmark(self.player.rect)
        if landmark:
            self._enter_landmark(landmark)
            return
        npc = self._nearest_npc()
        if npc:
            if getattr(npc, "rattle_id", None):
                self._open_dialogue(npc)
            else:
                self.ambient_speaker = npc
                self.ambient_text = self.rng.choice(AMBIENT_LINES)
                self.ambient_text_timer = 240
                sound_system.play_sound("click")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                self._interact()
                return
            if event.key == pygame.K_m:
                self.show_map = not self.show_map
                self._close_dialogue()
                sound_system.play_sound("click")
                return
            if event.key == pygame.K_TAB and not self.dialogue_npc:
                self.manager.world_map_return_state = "rattlebridge_city"
                self.next_state = "world_map"
                sound_system.play_sound("click")
                return
            if event.key == pygame.K_ESCAPE:
                if self.dialogue_npc:
                    self._close_dialogue()
                elif self.show_map:
                    self.show_map = False
                else:
                    self.manager.world_map_return_state = "rattlebridge_city"
                    self.next_state = "world_map"
                return
            if event.key == pygame.K_SPACE and not self.show_map:
                mx, my = pygame.mouse.get_pos()
                dx = mx + self.camera_x - self.player.rect.centerx
                dy = my + self.camera_y - self.player.rect.centery
                try:
                    self.player.perform_dash(dx, dy)
                except Exception:
                    pass

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.dialogue_npc:
                self._advance_dialogue()

    def _move_player(self):
        if self.dialogue_npc or self.show_map:
            self.player.animation_state = "idle"
            return
        keys = pygame.key.get_pressed()
        speed = 4.2
        wants_sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        try:
            self.player.set_sprinting(wants_sprint)
            if self.player.is_sprinting and self.player.current_stamina > 0.5:
                speed *= 1.5
        except Exception:
            pass

        dx = float(keys[pygame.K_d] - keys[pygame.K_a]) * speed
        dy = float(keys[pygame.K_s] - keys[pygame.K_w]) * speed
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071

        moved = False
        if not getattr(self.player, "is_dashing", False):
            if dx:
                old_x = self.player.rect.x
                self.player.rect.x += int(round(dx))
                if not self.city.is_walkable(self.player.rect):
                    self.player.rect.x = old_x
                else:
                    moved = True
                    self.player.facing_right = dx > 0
            if dy:
                old_y = self.player.rect.y
                self.player.rect.y += int(round(dy))
                if not self.city.is_walkable(self.player.rect):
                    self.player.rect.y = old_y
                else:
                    moved = True

        self.player.animation_state = "run" if moved else "idle"
        try:
            self.player.update(self.city.obstacles, self.manager)
        except Exception:
            pass

    def _update_population(self):
        for npc in self.npcs:
            if getattr(npc, "rattle_id", None):
                npc.animation_state = "idle"
                try:
                    npc.update(self.city.obstacles, self.manager)
                except Exception:
                    pass
                continue

            npc.sim_timer -= 1
            if npc.sim_state == "PATROL":
                ox, oy = getattr(npc, "patrol_offset", (0, 0))
                tx, ty = npc.patrol_points[npc.patrol_index]
                tx, ty = tx + ox, ty + oy
                dx = tx - npc.rect.centerx
                dy = ty - npc.rect.centery
                distance = math.hypot(dx, dy)
                if distance < 14:
                    npc.patrol_index = (npc.patrol_index + 1) % len(npc.patrol_points)
                    npc.animation_state = "idle"
                else:
                    speed = 0.85
                    old = npc.rect.copy()
                    npc.rect.x += int(round(dx / distance * speed))
                    npc.rect.y += int(round(dy / distance * speed))
                    if not self.city.is_walkable(npc.rect):
                        # Este reitillä: hyppää seuraavaan pisteeseen.
                        npc.rect = old
                        npc.patrol_index = (npc.patrol_index + 1) % len(npc.patrol_points)
                    else:
                        npc.animation_state = "run"
                        npc.facing_right = dx >= 0
                try:
                    npc.update(self.city.obstacles, self.manager)
                except Exception:
                    pass
                continue
            if npc.sim_state == "IDLE":
                npc.animation_state = "idle"
                if npc.sim_timer <= 0:
                    npc.sim_target = self.city.random_walkable_point(
                        getattr(npc, "home_district", None)
                    )
                    npc.sim_state = "WALK"
                    npc.sim_timer = self.rng.randint(280, 620)
            elif npc.sim_state == "WALK":
                tx, ty = npc.sim_target
                dx = tx - npc.rect.centerx
                dy = ty - npc.rect.centery
                distance = math.hypot(dx, dy)
                if distance < 12 or npc.sim_timer <= 0:
                    npc.sim_state = "IDLE"
                    npc.sim_timer = self.rng.randint(60, 240)
                else:
                    speed = 1.0 + (hash(npc.name) % 5) * 0.06
                    move_x = dx / distance * speed
                    move_y = dy / distance * speed
                    old = npc.rect.copy()
                    npc.rect.x += int(round(move_x))
                    npc.rect.y += int(round(move_y))
                    if not self.city.is_walkable(npc.rect):
                        npc.rect = old
                        npc.sim_state = "IDLE"
                        npc.sim_timer = 45
                    else:
                        npc.animation_state = "run"
                        npc.facing_right = move_x >= 0
            try:
                npc.update(self.city.obstacles, self.manager)
            except Exception:
                pass

    def _update_district(self):
        district = self.city.district_at(self.player.rect.center)
        if district != self.current_district:
            self.current_district = district
            self.district_banner_timer = 180
            if district:
                visited = self._state()["districts_visited"]
                if district not in visited:
                    visited.append(district)
        elif self.district_banner_timer > 0:
            self.district_banner_timer -= 1

    def _update_hush_mantle(self):
        if self.hush_active > 0:
            self.hush_active -= 1
            target = 130 if self.hush_active > 90 else 0
            self.hush_alpha += int((target - self.hush_alpha) * 0.08)
            if self.hush_active == 0:
                self.hush_timer = self.rng.randint(3000, 6200)
            return

        self.hush_timer -= 1
        self.hush_alpha = max(0, self.hush_alpha - 4)
        if self.hush_timer <= 0:
            self.hush_active = self.rng.randint(260, 520)
            self._state()["hush_mantle_sightings"] += 1
            self.feedback = "The bridge fog swallows every sound. Hush-Mantle is near."
            self.feedback_timer = 300

    def update(self):
        super().update()
        self._move_player()
        if not getattr(self.manager, "world_paused", False):
            self._update_population()
            for cart in self.carts:
                cart.update()
            self._update_hush_mantle()
            try:
                self.manager.world_clock.update()
            except Exception:
                pass
        self._update_district()
        self._update_camera()
        self._nearby_landmark = self.city.nearby_landmark(self.player.rect)
        self._nearby_npc = None if self._nearby_landmark else self._nearest_npc()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        if self.ambient_text_timer > 0:
            self.ambient_text_timer -= 1

    def _update_camera(self):
        target_x = self.player.rect.centerx - SCREEN_WIDTH // 2
        target_y = self.player.rect.centery - SCREEN_HEIGHT // 2
        self.camera_x = max(0, min(target_x, self.city.width - SCREEN_WIDTH))
        self.camera_y = max(0, min(target_y, self.city.height - SCREEN_HEIGHT))
        self.manager.camera_x = self.camera_x
        self.manager.camera_y = self.camera_y

    def _draw_unit(self, screen, unit):
        try:
            unit.draw_on_screen(screen, (self.camera_x, self.camera_y))
        except Exception:
            rect = unit.rect.move(-self.camera_x, -self.camera_y)
            pygame.draw.rect(screen, getattr(unit, "team_color", GREEN), rect)

    def _draw_local_map(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 6, 8, 215))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(120, 90, SCREEN_WIDTH - 240, SCREEN_HEIGHT - 180)
        pygame.draw.rect(screen, (45, 42, 38), panel, border_radius=14)
        pygame.draw.rect(screen, (170, 145, 95), panel, 3, border_radius=14)

        image = load_rattlebridge_image("city_map", (panel.w - 50, panel.h - 105))
        image.set_alpha(120)
        screen.blit(image, (panel.x + 25, panel.y + 70))

        inner = pygame.Rect(panel.x + 25, panel.y + 70, panel.w - 50, panel.h - 105)
        sx = inner.w / self.city.width
        sy = inner.h / self.city.height
        for district_id, rect in self.city.districts.items():
            mapped = pygame.Rect(
                inner.x + int(rect.x * sx),
                inner.y + int(rect.y * sy),
                max(4, int(rect.w * sx)),
                max(4, int(rect.h * sy)),
            )
            data = DISTRICTS[district_id]
            pygame.draw.rect(screen, data["color"], mapped, 2, border_radius=5)
            draw_text(data["name"], font_small, WHITE, screen,
                      mapped.x + 4, mapped.y + 4)

        for landmark in self.city.landmarks.values():
            px = inner.x + int(landmark.rect.centerx * sx)
            py = inner.y + int(landmark.rect.centery * sy)
            pygame.draw.circle(screen, GOLD_COLOR, (px, py), 6)

        px = inner.x + int(self.player.rect.centerx * sx)
        py = inner.y + int(self.player.rect.centery * sy)
        pygame.draw.circle(screen, WHITE, (px, py), 9)
        pygame.draw.circle(screen, (25, 25, 25), (px, py), 9, 2)
        draw_text("RATTLEBRIDGE LOCAL MAP", font_title, GOLD_COLOR,
                  screen, panel.x + 30, panel.y + 20)
        draw_text("[M] / [ESC] close   [TAB] continent map",
                  font_small, GRAY, screen, panel.right - 380, panel.y + 30)

    def _draw_dialogue(self, screen):
        if not self.dialogue_npc:
            return
        panel = pygame.Rect(180, SCREEN_HEIGHT - 285, SCREEN_WIDTH - 360, 220)
        pygame.draw.rect(screen, (18, 18, 22), panel, border_radius=12)
        pygame.draw.rect(screen, (180, 145, 88), panel, 3, border_radius=12)
        npc = self.dialogue_npc
        draw_text(npc.name, font_title, GOLD_COLOR, screen,
                  panel.x + 28, panel.y + 20)
        draw_text(getattr(npc, "rattle_role", "Citizen"), font_small,
                  (170, 185, 200), screen, panel.x + 30, panel.y + 62)
        lines = getattr(npc, "dialogue_lines", ())
        text = lines[self.dialogue_line] if lines else self.ambient_text
        words = text.split()
        current = ""
        y = panel.y + 96
        for word in words:
            trial = word if not current else f"{current} {word}"
            if font_main.size(trial)[0] > panel.w - 70:
                draw_text(current, font_main, WHITE, screen, panel.x + 30, y)
                y += 30
                current = word
            else:
                current = trial
        if current:
            draw_text(current, font_main, WHITE, screen, panel.x + 30, y)
        draw_text("[E] / click continue   [ESC] close", font_small, GRAY,
                  screen, panel.right - 290, panel.bottom - 30)

    def _draw_hud(self, screen):
        if self.current_district and self.district_banner_timer > 0:
            data = DISTRICTS[self.current_district]
            alpha = min(220, self.district_banner_timer * 3)
            banner = pygame.Surface((520, 74), pygame.SRCALPHA)
            banner.fill((15, 15, 18, alpha))
            screen.blit(banner, (SCREEN_WIDTH // 2 - 260, 70))
            draw_text(data["name"], font_title, GOLD_COLOR, screen,
                      SCREEN_WIDTH // 2 - 230, 82)
            draw_text(data["summary"], font_small, (210, 205, 190), screen,
                      SCREEN_WIDTH // 2 - 230, 116)

        prompt = None
        if self._nearby_landmark:
            prompt = self._nearby_landmark.prompt
        elif self._nearby_npc:
            prompt = f"E: Speak with {self._nearby_npc.name}"
        if prompt and not self.dialogue_npc:
            width = max(340, font_main.size(prompt)[0] + 50)
            rect = pygame.Rect(SCREEN_WIDTH // 2 - width // 2,
                               SCREEN_HEIGHT - 95, width, 48)
            pygame.draw.rect(screen, (15, 15, 18), rect, border_radius=9)
            pygame.draw.rect(screen, (180, 145, 88), rect, 2, border_radius=9)
            draw_text(prompt, font_main, WHITE, screen,
                      rect.x + 25, rect.y + 12)

        if self.feedback_timer > 0 and self.feedback:
            rect = pygame.Rect(300, 160, SCREEN_WIDTH - 600, 54)
            pygame.draw.rect(screen, (20, 20, 24), rect, border_radius=8)
            pygame.draw.rect(screen, (170, 120, 85), rect, 2, border_radius=8)
            draw_text(self.feedback, font_main, WHITE, screen,
                      rect.x + 20, rect.y + 15)

        if self.ambient_text_timer > 0 and self.ambient_speaker:
            sx = self.ambient_speaker.rect.centerx - self.camera_x
            sy = self.ambient_speaker.rect.top - self.camera_y - 48
            text_width = min(520, font_small.size(self.ambient_text)[0] + 26)
            bubble = pygame.Rect(sx - text_width // 2, sy, text_width, 34)
            pygame.draw.rect(screen, (235, 228, 204), bubble, border_radius=12)
            draw_text(self.ambient_text, font_small, (35, 32, 28), screen,
                      bubble.x + 13, bubble.y + 8)

        draw_text("WASD move  SHIFT sprint  E interact  M local map  TAB world map",
                  font_small, (215, 210, 195), screen, 24, 22)

    def draw(self, screen):
        highlighted = self._nearby_landmark.landmark_id if self._nearby_landmark else None
        self.city.draw_background(screen, (self.camera_x, self.camera_y))
        self.city.draw_landmarks(screen, (self.camera_x, self.camera_y), highlighted)

        renderables = list(self.npcs) + [self.player] + list(self.carts)
        renderables.sort(key=lambda item: item.rect.bottom)
        offset = (self.camera_x, self.camera_y)
        for item in renderables:
            if isinstance(item, _FreightCart):
                item.draw(screen, offset)
            else:
                self._draw_unit(screen, item)
        self.city.draw_foreground(screen, (self.camera_x, self.camera_y))

        if self.hush_alpha > 0:
            fog = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fog.fill((175, 185, 190, min(145, self.hush_alpha)))
            for index in range(8):
                x = (pygame.time.get_ticks() // 20 + index * 270) % (SCREEN_WIDTH + 400) - 200
                pygame.draw.ellipse(fog, (220, 225, 225, 28),
                                    (x, 120 + (index % 4) * 190, 520, 170))
            screen.blit(fog, (0, 0))

        self._draw_hud(screen)
        self._draw_dialogue(screen)
        if self.show_map:
            self._draw_local_map(screen)
