"""Large procedural local map for Rattlebridge.

The map is intentionally more extensive than Muckford and uses a walkable deck
network rather than one rectangular ground plane. Final background art can be
added later without changing collision, landmarks or district coordinates.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from settings import SCREEN_HEIGHT, SCREEN_WIDTH
from citys.rattlebridge.rattlebridge_data import (
    DISTRICTS,
    LANDMARKS,
    WORLD_SIZE_MULTIPLIER,
)


WATER = (22, 43, 53)
WATER_LINE = (40, 73, 80)
DECK_STONE = (88, 80, 69)
DECK_EDGE = (45, 44, 42)
IRON = (62, 62, 60)
BRASS = (164, 128, 69)
LAMP = (230, 180, 82)


@dataclass
class RattlebridgeLandmark:
    landmark_id: str
    name: str
    rect: pygame.Rect
    kind: str
    target_state: str | None
    prompt: str
    district: str

    is_structure: bool = True

    @property
    def interaction_point(self):
        return self.rect.centerx, self.rect.bottom + 36

    @property
    def collision_rect(self):
        if self.kind in {"world_map", "travel", "contract_board"}:
            return pygame.Rect(0, 0, 0, 0)
        return self.rect.inflate(-max(20, self.rect.w // 8),
                                 -max(18, self.rect.h // 6))

    def draw(self, screen, offset=(0, 0), highlighted=False):
        ox, oy = offset
        rect = self.rect.move(-ox, -oy)
        if rect.right < -80 or rect.left > screen.get_width() + 80:
            return
        if rect.bottom < -80 or rect.top > screen.get_height() + 80:
            return

        base = {
            "arena": (83, 69, 64),
            "hospital": (115, 111, 96),
            "interior": (105, 74, 47),
            "market": (115, 82, 51),
            "storage": (91, 73, 53),
            "dungeon": (56, 66, 66),
            "customs": (105, 93, 78),
            "sera": (105, 69, 59),
            "guard": (75, 92, 110),
        }.get(self.kind, (96, 82, 66))
        roof = tuple(max(25, channel - 28) for channel in base)

        shadow = rect.move(10, 12)
        pygame.draw.rect(screen, (25, 25, 26), shadow, border_radius=10)
        pygame.draw.rect(screen, base, rect, border_radius=9)
        roof_rect = pygame.Rect(rect.x - 8, rect.y - 16,
                                rect.w + 16, max(28, rect.h // 6))
        pygame.draw.rect(screen, roof, roof_rect, border_radius=8)
        pygame.draw.line(screen, BRASS, roof_rect.topleft,
                         roof_rect.topright, 3)

        # Doors and windows remain readable at gameplay zoom.
        door = pygame.Rect(rect.centerx - 20, rect.bottom - 48, 40, 48)
        pygame.draw.rect(screen, (47, 37, 30), door, border_radius=4)
        for x in range(rect.left + 28, rect.right - 20, 68):
            pygame.draw.rect(screen, (210, 163, 78),
                             (x, rect.top + 40, 18, 24), border_radius=3)

        if self.kind == "arena":
            pygame.draw.ellipse(screen, (42, 40, 39), rect.inflate(-80, -70), 8)
            for x in range(rect.left + 45, rect.right - 20, 95):
                pygame.draw.circle(screen, IRON, (x, rect.centery), 20)
                pygame.draw.circle(screen, BRASS, (x, rect.centery), 20, 4)
        elif self.kind == "hospital":
            pygame.draw.circle(screen, (220, 204, 130),
                               (rect.centerx, rect.top + 62), 21, 4)
            pygame.draw.line(screen, (220, 204, 130),
                             (rect.centerx, rect.top + 34),
                             (rect.centerx, rect.top + 91), 4)
        elif self.kind == "dungeon":
            pygame.draw.circle(screen, (40, 42, 41), rect.center, 45)
            pygame.draw.circle(screen, (132, 123, 98), rect.center, 45, 7)
        elif self.kind in {"world_map", "travel"}:
            pygame.draw.line(screen, IRON, rect.midtop, rect.midbottom, 10)
            pygame.draw.line(screen, IRON, rect.topleft, rect.topright, 10)
        elif self.kind == "contract_board":
            pygame.draw.rect(screen, (95, 69, 43), rect, border_radius=4)
            pygame.draw.rect(screen, (193, 176, 127), rect.inflate(-12, -16), 3)

        if highlighted:
            pygame.draw.rect(screen, (242, 213, 130), rect.inflate(12, 12),
                             3, border_radius=12)


class RattlebridgeCityMap:
    def __init__(self):
        self.width = int(SCREEN_WIDTH * WORLD_SIZE_MULTIPLIER[0])
        self.height = int(SCREEN_HEIGHT * WORLD_SIZE_MULTIPLIER[1])
        self.world_rect = pygame.Rect(0, 0, self.width, self.height)
        self.rng = random.Random(88241)

        self.main_deck = pygame.Rect(
            0,
            int(self.height * 0.25),
            self.width,
            int(self.height * 0.31),
        )
        self.lower_deck = pygame.Rect(
            int(self.width * 0.10),
            int(self.height * 0.57),
            int(self.width * 0.80),
            int(self.height * 0.34),
        )
        self.connector_decks = [
            pygame.Rect(int(self.width * 0.24), int(self.height * 0.46),
                        int(self.width * 0.075), int(self.height * 0.20)),
            pygame.Rect(int(self.width * 0.51), int(self.height * 0.45),
                        int(self.width * 0.08), int(self.height * 0.22)),
            pygame.Rect(int(self.width * 0.76), int(self.height * 0.45),
                        int(self.width * 0.075), int(self.height * 0.22)),
        ]
        self.walkable_zones = [self.main_deck, self.lower_deck]
        self.walkable_zones.extend(self.connector_decks)

        self.districts = {}
        for district_id, data in DISTRICTS.items():
            nx, ny, nw, nh = data["rect_norm"]
            self.districts[district_id] = pygame.Rect(
                int(nx * self.width),
                int(ny * self.height),
                int(nw * self.width),
                int(nh * self.height),
            )

        self.landmarks = {}
        self.props = []
        self.obstacles = []
        self.floor_props = []
        self.steam_vents = []
        self.cargo_crates = []
        self.lamps = []
        self.cranes = []
        self.market_stalls = []
        self.spawn_points = []
        self.enemy_spawns = []

        self._build_landmarks()
        self._build_city_details()

    def _build_landmarks(self):
        for landmark_id, data in LANDMARKS.items():
            nx, ny = data["position_norm"]
            width, height = data["size"]
            rect = pygame.Rect(
                int(nx * self.width - width / 2),
                int(ny * self.height - height / 2),
                width,
                height,
            )
            landmark = RattlebridgeLandmark(
                landmark_id=landmark_id,
                name=data["name"],
                rect=rect,
                kind=data["kind"],
                target_state=data.get("target_state"),
                prompt=data["prompt"],
                district=data["district"],
            )
            self.landmarks[landmark_id] = landmark
            self.props.append(landmark)
            collision = landmark.collision_rect
            if collision.w > 0 and collision.h > 0:
                self.obstacles.append(collision)

        start = self.landmarks["world_gate"].interaction_point
        self.spawn_points.append((start[0] + 140, start[1]))

    def _zone_contains_structure(self, rect):
        return any(rect.colliderect(obstacle.inflate(40, 40))
                   for obstacle in self.obstacles)

    def _random_point(self, zone, margin=60):
        return (
            self.rng.randint(zone.left + margin, zone.right - margin),
            self.rng.randint(zone.top + margin, zone.bottom - margin),
        )

    def _build_city_details(self):
        # Lamps run along both principal bridge lanes.
        for deck in (self.main_deck, self.lower_deck):
            for x in range(deck.left + 180, deck.right - 180, 330):
                self.lamps.append((x, deck.top + 48))
                self.lamps.append((x + 160, deck.bottom - 48))

        # Freight cranes and steam vents give the city its industrial motion.
        freight = self.districts["freight_deck"]
        for index in range(6):
            x = freight.left + 160 + index * max(180, freight.w // 7)
            self.cranes.append((x, freight.bottom - 60,
                                130 + (index % 3) * 35))

        for zone in (self.main_deck, self.lower_deck):
            for _ in range(16):
                x, y = self._random_point(zone, 90)
                self.steam_vents.append((x, y, self.rng.randint(0, 180)))

        # Market stalls are non-blocking visuals; cargo crates are obstacles.
        market = self.districts["union_market"]
        for row in range(3):
            for col in range(5):
                self.market_stalls.append((
                    market.left + 120 + col * 190,
                    market.top + 130 + row * 145,
                    1 + (row + col) % 3,
                ))

        freight = self.districts["freight_deck"]
        for _ in range(32):
            x, y = self._random_point(freight, 100)
            rect = pygame.Rect(x, y, self.rng.choice((52, 64, 78)),
                               self.rng.choice((46, 58, 70)))
            if self._zone_contains_structure(rect):
                continue
            self.cargo_crates.append(rect)
            self.obstacles.append(rect)

        # Barrier blocks prevent uninterrupted sprinting through the city and
        # create smaller streets without turning the bridge into a maze.
        for district_id in ("west_tollgate", "span_ward",
                            "scrapring_district", "bridgeward"):
            zone = self.districts[district_id]
            for _ in range(5):
                x, y = self._random_point(zone, 90)
                rect = pygame.Rect(x, y, 95, 34)
                if self._zone_contains_structure(rect):
                    continue
                self.cargo_crates.append(rect)
                self.obstacles.append(rect)

        # Canalworks grates double as encounter spawn points.
        canal = self.districts["canal_lift"]
        for index in range(6):
            x = canal.left + 120 + (index % 3) * 170
            y = canal.top + 130 + (index // 3) * 180
            self.enemy_spawns.append((x, y))

    def is_walkable(self, rect):
        center = rect.center
        if not any(zone.collidepoint(center) for zone in self.walkable_zones):
            return False
        return not any(rect.colliderect(obstacle) for obstacle in self.obstacles)

    def district_at(self, point):
        for district_id, rect in self.districts.items():
            if rect.collidepoint(point):
                return district_id
        return None

    def nearby_landmark(self, player_rect, distance=120):
        px, py = player_rect.centerx, player_rect.bottom
        best = None
        best_distance = float("inf")
        for landmark in self.landmarks.values():
            lx, ly = landmark.interaction_point
            current = math.hypot(px - lx, py - ly)
            if current < distance and current < best_distance:
                best = landmark
                best_distance = current
        return best

    def random_walkable_point(self, district_id=None):
        zones = []
        if district_id and district_id in self.districts:
            zones.append(self.districts[district_id])
        else:
            zones.extend(self.walkable_zones)
        for _ in range(40):
            zone = self.rng.choice(zones)
            x, y = self._random_point(zone, 70)
            rect = pygame.Rect(x - 16, y - 12, 32, 24)
            if self.is_walkable(rect):
                return x, y
        return self.main_deck.center

    def _visible(self, rect, offset, margin=120):
        view = pygame.Rect(offset[0] - margin, offset[1] - margin,
                           SCREEN_WIDTH + margin * 2,
                           SCREEN_HEIGHT + margin * 2)
        return view.colliderect(rect)

    @staticmethod
    def _screen_rect(rect, offset):
        return rect.move(-offset[0], -offset[1])

    def _draw_water(self, screen, offset):
        screen.fill(WATER)
        start_y = -(offset[1] % 46)
        phase = int(offset[0] * 0.08) % 70
        for y in range(start_y, SCREEN_HEIGHT, 46):
            pygame.draw.line(screen, WATER_LINE,
                             (-70 + phase, y),
                             (SCREEN_WIDTH + 70 + phase, y), 2)

    def _draw_deck(self, screen, rect, offset, color=DECK_STONE):
        if not self._visible(rect, offset):
            return
        draw_rect = self._screen_rect(rect, offset)
        pygame.draw.rect(screen, DECK_EDGE, draw_rect.inflate(26, 26),
                         border_radius=10)
        pygame.draw.rect(screen, color, draw_rect, border_radius=7)
        pygame.draw.rect(screen, IRON, draw_rect, 7, border_radius=7)

        x_start = draw_rect.left - (draw_rect.left % 90)
        for x in range(x_start, draw_rect.right, 90):
            pygame.draw.line(screen, (112, 100, 82),
                             (x, draw_rect.top + 9),
                             (x, draw_rect.bottom - 9), 2)

    def _draw_districts(self, screen, offset):
        for district_id, rect in self.districts.items():
            if not self._visible(rect, offset):
                continue
            data = DISTRICTS[district_id]
            draw_rect = self._screen_rect(rect, offset)
            overlay = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
            overlay.fill((*data["color"], 58))
            screen.blit(overlay, draw_rect.topleft)
            pygame.draw.rect(screen, (*data["color"],), draw_rect, 3,
                             border_radius=12)

    def _draw_lamp(self, screen, x, y, offset):
        sx, sy = x - offset[0], y - offset[1]
        if not (-50 <= sx <= SCREEN_WIDTH + 50 and -80 <= sy <= SCREEN_HEIGHT + 80):
            return
        pygame.draw.line(screen, (50, 48, 45), (sx, sy + 30), (sx, sy - 45), 7)
        pygame.draw.circle(screen, LAMP, (sx, sy - 48), 10)
        glow = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(glow, (240, 190, 85, 35), (40, 40), 38)
        screen.blit(glow, (sx - 40, sy - 88))

    def _draw_crane(self, screen, x, y, height, offset):
        sx, sy = x - offset[0], y - offset[1]
        if not (-220 <= sx <= SCREEN_WIDTH + 220 and -260 <= sy <= SCREEN_HEIGHT + 100):
            return
        pygame.draw.line(screen, IRON, (sx, sy), (sx, sy - height), 13)
        pygame.draw.line(screen, (80, 76, 68),
                         (sx, sy - height), (sx + 130, sy - height + 10), 10)
        pygame.draw.line(screen, (40, 39, 37),
                         (sx + 112, sy - height + 14), (sx + 112, sy - 55), 3)
        pygame.draw.rect(screen, (100, 72, 42),
                         (sx + 90, sy - 55, 44, 34))

    def _draw_steam(self, screen, x, y, phase, offset):
        sx, sy = x - offset[0], y - offset[1]
        if not (-100 <= sx <= SCREEN_WIDTH + 100 and -120 <= sy <= SCREEN_HEIGHT + 120):
            return
        pygame.draw.circle(screen, (42, 41, 39), (sx, sy), 19)
        pygame.draw.circle(screen, (139, 129, 105), (sx, sy), 19, 4)
        cloud = pygame.Surface((110, 160), pygame.SRCALPHA)
        tick = pygame.time.get_ticks() * 0.002 + phase
        for index in range(4):
            cx = 55 + int(math.sin(tick + index) * 10)
            cy = 125 - index * 32
            pygame.draw.circle(cloud, (210, 214, 208, 44 - index * 7),
                               (cx, cy), 18 + index * 5)
        screen.blit(cloud, (sx - 55, sy - 145))

    def _draw_market_stall(self, screen, x, y, variant, offset):
        rect = pygame.Rect(x - offset[0], y - offset[1], 120, 72)
        if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).inflate(100, 100).colliderect(rect):
            return
        colors = ((132, 52, 53), (62, 104, 79), (122, 91, 48))
        pygame.draw.rect(screen, (80, 54, 35), rect, border_radius=6)
        awning = pygame.Rect(rect.x - 5, rect.y - 20, rect.w + 10, 32)
        pygame.draw.rect(screen, colors[(variant - 1) % len(colors)], awning,
                         border_radius=5)
        for stripe in range(0, awning.w, 24):
            pygame.draw.line(screen, (210, 180, 118),
                             (awning.left + stripe, awning.top),
                             (awning.left + stripe, awning.bottom), 3)

    def draw_background(self, screen, offset=(0, 0)):
        self._draw_water(screen, offset)
        self._draw_deck(screen, self.main_deck, offset)
        self._draw_deck(screen, self.lower_deck, offset, color=(77, 73, 66))
        for connector in self.connector_decks:
            self._draw_deck(screen, connector, offset, color=(81, 77, 69))
        self._draw_districts(screen, offset)

        for x, y, variant in self.market_stalls:
            self._draw_market_stall(screen, x, y, variant, offset)
        for rect in self.cargo_crates:
            if not self._visible(rect, offset):
                continue
            draw_rect = self._screen_rect(rect, offset)
            pygame.draw.rect(screen, (86, 60, 38), draw_rect, border_radius=5)
            pygame.draw.rect(screen, (45, 39, 34), draw_rect, 3, border_radius=5)
            pygame.draw.line(screen, (126, 92, 54), draw_rect.topleft,
                             draw_rect.bottomright, 3)
        for x, y in self.lamps:
            self._draw_lamp(screen, x, y, offset)
        for x, y, height in self.cranes:
            self._draw_crane(screen, x, y, height, offset)
        for x, y, phase in self.steam_vents:
            self._draw_steam(screen, x, y, phase, offset)

    def draw_landmarks(self, screen, offset=(0, 0), highlighted=None):
        for landmark_id, landmark in self.landmarks.items():
            landmark.draw(screen, offset, highlighted=landmark_id == highlighted)

    def draw_foreground(self, screen, offset=(0, 0)):
        # Foreground railings on deck edges add depth without obscuring units.
        for deck in (self.main_deck, self.lower_deck):
            draw_rect = self._screen_rect(deck, offset)
            if draw_rect.bottom < -40 or draw_rect.top > SCREEN_HEIGHT + 40:
                continue
            for x in range(draw_rect.left, draw_rect.right, 54):
                pygame.draw.line(screen, (45, 44, 42),
                                 (x, draw_rect.bottom - 8),
                                 (x, draw_rect.bottom + 18), 5)
            pygame.draw.line(screen, (57, 56, 53),
                             (draw_rect.left, draw_rect.bottom + 4),
                             (draw_rect.right, draw_rect.bottom + 4), 6)
