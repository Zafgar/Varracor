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

    def _deck_clip(self, rect):
        """Distriktin osa joka on oikeasti kannella (ei vedessä). Distriktien
        suorakulmiot ulottuvat vesialueelle - somisteet kuuluvat kansille."""
        best = pygame.Rect(rect.centerx, rect.centery, 0, 0)
        for deck in self.walkable_zones:
            clipped = rect.clip(deck)
            if clipped.w * clipped.h > best.w * best.h:
                best = clipped
        return best if best.w > 120 and best.h > 120 else rect

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
        # Kojut rajataan kannelle - distriktin suorakulmio ulottuu veteen.
        market = self._deck_clip(self.districts["union_market"])
        for row in range(3):
            for col in range(5):
                self.market_stalls.append((
                    market.left + 120 + col * 190,
                    market.top + 90 + row * 145,
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

        self._build_lore_setpieces()

    def _build_lore_setpieces(self):
        """Lore-kalusteet: siltakaupungin massiivinen rakenne, Kruunun tullit,
        kuumeslummien punalyhdyt, Scrapringin koneisto ja sponsoribannerit.
        Pelkkää visuaalia - ei törmäyksiä, joten gameplay ei muutu."""
        # --- Sillan kivipilarit ja kaaret vedessä kansien alla ---
        self.piers = []
        for deck in (self.main_deck, self.lower_deck):
            span = max(520, deck.w // 7)
            for x in range(deck.left + span // 2, deck.right, span):
                self.piers.append((x, deck.bottom, 120 + self.rng.randint(-14, 18)))

        # --- Ironspan-riipputornit + ketjukatenaarit pääkannen yllä ---
        tower_y = self.main_deck.top
        self.towers = [
            (int(self.width * 0.30), tower_y),
            (int(self.width * 0.70), tower_y),
        ]

        # --- Jättirattaat kansien kyljissä (Scrapringin koneisto) ---
        self.great_gears = []
        for gx, gy, radius, speed in (
            (self.main_deck.left + int(self.width * 0.055),
             self.main_deck.bottom - 8, 92, 0.25),
            (int(self.width * 0.585), self.main_deck.bottom - 4, 74, -0.4),
            (self.lower_deck.right - 220, self.lower_deck.top + 6, 84, 0.32),
        ):
            self.great_gears.append((gx, gy, radius, speed))

        # --- Proomut lipuvat virran mukana sillan ali ---
        self.barges = []
        for _ in range(4):
            self.barges.append((
                self.rng.randint(60, self.height - 80),          # y
                self.rng.uniform(0.18, 0.45),                     # nopeus
                self.rng.randint(150, 230),                       # pituus
                self.rng.uniform(0, self.width),                  # vaihe
                self.rng.choice(((96, 70, 44), (74, 78, 66), (88, 60, 60))),
            ))

        # --- Punalyhtynarut + karanteeniteltat (kuume, Red Lantern -kujat) ---
        ward = self._deck_clip(self.districts["bridgeward"])
        self.red_lantern_lines = []
        for row in range(3):
            y = ward.top + 90 + row * max(120, ward.h // 4)
            x1 = ward.left + 60 + self.rng.randint(-20, 30)
            x2 = min(ward.right - 60, x1 + self.rng.randint(380, 620))
            self.red_lantern_lines.append((x1, y, x2, y + self.rng.randint(-16, 20)))
        self.quarantine_tents = []
        for _ in range(5):
            x, y = self._random_point(ward, 80)
            rect = pygame.Rect(x, y, 96, 66)
            if self._zone_contains_structure(rect):
                continue
            self.quarantine_tents.append(rect)

        # --- Kruunun banderollit tulliportilla (Kuningas Alaric Vane) ---
        toll = self._deck_clip(self.districts["west_tollgate"])
        self.crown_banners = []
        for index in range(4):
            self.crown_banners.append((
                toll.left + 90 + index * max(150, toll.w // 5),
                toll.top + 70,
            ))

        # --- Sponsoribannerit Scrapringin ympärillä ---
        try:
            from systems.sponsors import SPONSORS
            palette = [s["banner"] for s in SPONSORS.values()]
        except Exception:
            palette = [(100, 120, 140), (170, 90, 120), (120, 150, 90)]
        ring = self._deck_clip(self.districts["scrapring_district"])
        self.sponsor_banners = []
        for index, color in enumerate(palette):
            self.sponsor_banners.append((
                ring.left + 70 + index * max(130, ring.w // (len(palette) + 1)),
                ring.top + 58,
                color,
            ))

        # --- Vesirattaat Canalworksin reunalla ---
        canal = self.districts["canal_lift"]
        self.waterwheels = [
            (canal.left + 40, canal.bottom + 34, 66),
            (canal.right - 60, canal.bottom + 30, 54),
        ]

        # --- Lokit kiertävät nostureita ---
        self.gulls = []
        for x, y, height in self.cranes[:4]:
            self.gulls.append((x + 60, y - height - 30,
                               self.rng.randint(40, 90),
                               self.rng.uniform(0.5, 1.1),
                               self.rng.uniform(0, 6.28)))

        # --- Kannen kuluma: öljytahrat, ruoste ja lätäköt ---
        self.deck_stains = []
        for zone in self.walkable_zones:
            area = zone.w * zone.h
            for _ in range(max(6, area // 260000)):
                x, y = self._random_point(zone, 40)
                kind = self.rng.choice(("oil", "oil", "rust", "puddle"))
                self.deck_stains.append((
                    x, y,
                    self.rng.randint(26, 74),
                    self.rng.randint(12, 30),
                    kind,
                ))

        # --- Ajelehtivat sumupankit (Hush-Mantlen enne) ---
        self.fog_banks = []
        for _ in range(5):
            self.fog_banks.append((
                self.rng.randint(0, self.height),
                self.rng.uniform(0.05, 0.18),
                self.rng.randint(420, 900),
                self.rng.randint(14, 30),
                self.rng.uniform(0, self.width),
            ))

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

    def _district_label(self, district_id):
        """Kerran renderöity distriktin nimikyltti (per-frame alpha-täyttö
        koko distriktin kokoisena maksoi ~24 ms/frame - tämä on ~0)."""
        if not hasattr(self, "_district_labels"):
            self._district_labels = {}
        cached = self._district_labels.get(district_id)
        if cached is not None:
            return cached
        data = DISTRICTS[district_id]
        font = pygame.font.SysFont("georgia", 22, bold=True)
        text = font.render(data["name"].upper(), True, (232, 220, 196))
        plaque = pygame.Surface((text.get_width() + 26, text.get_height() + 12),
                                pygame.SRCALPHA)
        pygame.draw.rect(plaque, (28, 26, 24, 200), plaque.get_rect(),
                         border_radius=6)
        pygame.draw.rect(plaque, (*data["color"], 255), plaque.get_rect(), 2,
                         border_radius=6)
        plaque.blit(text, (13, 6))
        self._district_labels[district_id] = plaque
        return plaque

    def _draw_districts(self, screen, offset):
        for district_id, rect in self.districts.items():
            if not self._visible(rect, offset):
                continue
            data = DISTRICTS[district_id]
            draw_rect = self._screen_rect(rect, offset)
            color = tuple(data["color"])
            pygame.draw.rect(screen, color, draw_rect, 3, border_radius=12)
            # Kulmamerkit vahvistavat rajaa ilman koko alueen sävytystä.
            for cx, cy in (draw_rect.topleft, draw_rect.topright,
                           draw_rect.bottomleft, draw_rect.bottomright):
                pygame.draw.circle(screen, color, (cx, cy), 7)
            plaque = self._district_label(district_id)
            screen.blit(plaque, (draw_rect.left + 16, draw_rect.top + 12))

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

    # ------------------------------------------------------------------
    # Lore-kalusteiden piirto
    # ------------------------------------------------------------------
    def _draw_pier(self, screen, x, deck_bottom, width, offset):
        sx = x - offset[0]
        sy = deck_bottom - offset[1]
        if not (-200 <= sx <= SCREEN_WIDTH + 200):
            return
        depth = SCREEN_HEIGHT + 40 - sy
        if depth <= 10:
            return
        pier = pygame.Rect(sx - width // 2, sy - 6, width, depth + 20)
        pygame.draw.rect(screen, (58, 54, 48), pier)
        pygame.draw.rect(screen, (38, 36, 33), pier, 4)
        # Kaariaukko pilarin läpi
        arch_h = min(150, depth - 20)
        if arch_h > 30:
            arch = pygame.Rect(sx - width // 3, sy + 40, (width * 2) // 3, arch_h)
            pygame.draw.ellipse(screen, WATER, arch)
            pygame.draw.ellipse(screen, (32, 52, 60), arch, 4)
        # Virran vana pilarin ympärillä
        tick = pygame.time.get_ticks() * 0.003
        for k in range(3):
            wy = sy + 60 + k * 34 + int(math.sin(tick + k) * 5)
            pygame.draw.arc(screen, (70, 110, 116),
                            (sx - width, wy, width * 2, 26), 3.5, 6.0, 2)

    def _draw_tower(self, screen, x, deck_top, offset):
        sx = x - offset[0]
        sy = deck_top - offset[1]
        if not (-300 <= sx <= SCREEN_WIDTH + 300):
            return
        h = 240
        pygame.draw.rect(screen, (54, 54, 52), (sx - 26, sy - h, 52, h))
        pygame.draw.rect(screen, (34, 34, 33), (sx - 26, sy - h, 52, h), 4)
        pygame.draw.rect(screen, BRASS, (sx - 32, sy - h - 14, 64, 16),
                         border_radius=4)
        pygame.draw.circle(screen, LAMP, (sx, sy - h - 24), 7)
        # Niittirivit
        for ry in range(sy - h + 22, sy - 10, 34):
            pygame.draw.circle(screen, (90, 88, 82), (sx - 14, ry), 3)
            pygame.draw.circle(screen, (90, 88, 82), (sx + 14, ry), 3)

    def _draw_chains(self, screen, offset):
        """Katenaariketjut tornien välillä ja kansille (Ironspan Union)."""
        if len(self.towers) < 2:
            return
        (x1, y1), (x2, y2) = self.towers[0], self.towers[1]
        top1 = (x1 - offset[0], y1 - 240 - offset[1])
        top2 = (x2 - offset[0], y2 - 240 - offset[1])
        anchors = [
            (self.main_deck.left + 60, self.main_deck.top + 14),
            (self.main_deck.right - 60, self.main_deck.top + 14),
        ]
        spans = [
            (top1, top2, 130),
            ((anchors[0][0] - offset[0], anchors[0][1] - offset[1]), top1, 80),
            (top2, (anchors[1][0] - offset[0], anchors[1][1] - offset[1]), 80),
        ]
        for (ax, ay), (bx, by), sag in spans:
            if max(ax, bx) < -100 or min(ax, bx) > SCREEN_WIDTH + 100:
                continue
            points = []
            for step in range(13):
                t = step / 12
                px = ax + (bx - ax) * t
                py = ay + (by - ay) * t + math.sin(t * math.pi) * sag
                points.append((px, py))
            pygame.draw.lines(screen, (46, 46, 44), False, points, 6)
            pygame.draw.lines(screen, (96, 92, 82), False, points, 2)
            # Pystyriipukkeet kannelle
            for px, py in points[2:-2:2]:
                pygame.draw.line(screen, (52, 52, 50),
                                 (px, py), (px, py + 26), 2)

    def _draw_great_gear(self, screen, x, y, radius, speed, offset):
        sx, sy = x - offset[0], y - offset[1]
        if not (-radius * 2 <= sx <= SCREEN_WIDTH + radius * 2
                and -radius * 2 <= sy <= SCREEN_HEIGHT + radius * 2):
            return
        angle = pygame.time.get_ticks() * 0.001 * speed
        pygame.draw.circle(screen, (58, 57, 54), (sx, sy), radius)
        pygame.draw.circle(screen, (34, 34, 32), (sx, sy), radius, 6)
        for k in range(10):
            a = angle + k * (math.tau / 10)
            tx = sx + int(math.cos(a) * (radius + 10))
            ty = sy + int(math.sin(a) * (radius + 10))
            pygame.draw.circle(screen, (58, 57, 54), (tx, ty), max(7, radius // 7))
        for k in range(5):
            a = angle + k * (math.tau / 5)
            pygame.draw.line(screen, (34, 34, 32), (sx, sy),
                             (sx + int(math.cos(a) * radius * 0.82),
                              sy + int(math.sin(a) * radius * 0.82)), 5)
        pygame.draw.circle(screen, BRASS, (sx, sy), max(10, radius // 5))
        pygame.draw.circle(screen, (34, 34, 32), (sx, sy), max(10, radius // 5), 3)

    def _draw_barge(self, screen, barge, offset):
        y, speed, length, phase, hull = barge
        tick = pygame.time.get_ticks() * 0.06
        x = (phase + tick * speed) % (self.width + 500) - 250
        sx, sy = x - offset[0], y - offset[1]
        if not (-length <= sx <= SCREEN_WIDTH + length
                and -60 <= sy <= SCREEN_HEIGHT + 60):
            return
        body = pygame.Rect(int(sx), int(sy), length, 34)
        pygame.draw.rect(screen, hull, body, border_radius=12)
        pygame.draw.rect(screen, (30, 28, 26), body, 3, border_radius=12)
        for cx in range(body.left + 24, body.right - 20, 44):
            pygame.draw.rect(screen, (70, 52, 34), (cx, body.top - 14, 28, 18),
                             border_radius=3)
        pygame.draw.circle(screen, LAMP, (body.right - 12, body.top - 6), 5)
        pygame.draw.line(screen, (60, 96, 104),
                         (body.left - 34, body.bottom + 3),
                         (body.left - 4, body.bottom + 1), 2)

    def _draw_red_lanterns(self, screen, line, offset):
        x1, y1, x2, y2 = line
        a = (x1 - offset[0], y1 - offset[1])
        b = (x2 - offset[0], y2 - offset[1])
        if max(a[0], b[0]) < -80 or min(a[0], b[0]) > SCREEN_WIDTH + 80:
            return
        pygame.draw.line(screen, (52, 44, 40), a, b, 2)
        count = max(3, int(abs(b[0] - a[0]) // 78))
        flicker = pygame.time.get_ticks() * 0.004
        for k in range(1, count):
            t = k / count
            lx = a[0] + (b[0] - a[0]) * t
            ly = a[1] + (b[1] - a[1]) * t + math.sin(t * math.pi) * 14
            glow = 168 + int(math.sin(flicker + k * 1.7) * 34)
            pygame.draw.line(screen, (52, 44, 40), (lx, ly), (lx, ly + 9), 2)
            pygame.draw.circle(screen, (glow, 52, 46), (int(lx), int(ly + 15)), 7)
            pygame.draw.circle(screen, (255, 190, 120), (int(lx), int(ly + 13)), 2)

    def _draw_quarantine_tent(self, screen, rect, offset):
        if not self._visible(rect, offset):
            return
        r = self._screen_rect(rect, offset)
        pygame.draw.polygon(screen, (168, 156, 128),
                            [(r.left, r.bottom), (r.centerx, r.top),
                             (r.right, r.bottom)])
        pygame.draw.polygon(screen, (92, 84, 66),
                            [(r.left, r.bottom), (r.centerx, r.top),
                             (r.right, r.bottom)], 3)
        pygame.draw.line(screen, (150, 46, 40),
                         (r.centerx - 10, r.centery), (r.centerx + 10, r.centery + 16), 4)
        pygame.draw.line(screen, (150, 46, 40),
                         (r.centerx + 10, r.centery), (r.centerx - 10, r.centery + 16), 4)

    def _draw_crown_banner(self, screen, x, y, offset):
        sx, sy = x - offset[0], y - offset[1]
        if not (-60 <= sx <= SCREEN_WIDTH + 60):
            return
        pygame.draw.line(screen, (48, 46, 44), (sx, sy - 26), (sx, sy + 96), 5)
        sway = math.sin(pygame.time.get_ticks() * 0.0016 + x * 0.01) * 5
        banner = [(sx, sy), (sx + 34 + sway, sy + 4), (sx + 32 + sway, sy + 78),
                  (sx + 16, sy + 66), (sx, sy + 76)]
        pygame.draw.polygon(screen, (120, 34, 40), banner)
        pygame.draw.polygon(screen, (70, 22, 26), banner, 2)
        # Kruunutunnus (Alaric Vane)
        cx, cy = sx + 16, sy + 30
        pygame.draw.polygon(screen, (222, 186, 92),
                            [(cx - 9, cy + 6), (cx - 9, cy - 3), (cx - 4, cy + 1),
                             (cx, cy - 6), (cx + 4, cy + 1), (cx + 9, cy - 3),
                             (cx + 9, cy + 6)])

    def _draw_sponsor_banner(self, screen, x, y, color, offset):
        sx, sy = x - offset[0], y - offset[1]
        if not (-60 <= sx <= SCREEN_WIDTH + 60):
            return
        pygame.draw.line(screen, (48, 46, 44), (sx, sy - 20), (sx, sy + 80), 4)
        sway = math.sin(pygame.time.get_ticks() * 0.002 + y * 0.02) * 4
        pygame.draw.polygon(screen, color,
                            [(sx, sy), (sx + 26 + sway, sy + 3),
                             (sx + 24 + sway, sy + 58), (sx, sy + 52)])
        pygame.draw.circle(screen, (235, 220, 170), (sx + 12, sy + 20), 5, 2)

    def _draw_waterwheel(self, screen, x, y, radius, offset):
        sx, sy = x - offset[0], y - offset[1]
        if not (-radius * 2 <= sx <= SCREEN_WIDTH + radius * 2
                and -radius * 2 <= sy <= SCREEN_HEIGHT + radius * 2):
            return
        angle = pygame.time.get_ticks() * 0.0006
        pygame.draw.circle(screen, (72, 56, 40), (sx, sy), radius, 8)
        pygame.draw.circle(screen, (48, 38, 28), (sx, sy), radius - 12, 3)
        for k in range(8):
            a = angle + k * (math.tau / 8)
            ex = sx + int(math.cos(a) * radius)
            ey = sy + int(math.sin(a) * radius)
            pygame.draw.line(screen, (72, 56, 40), (sx, sy), (ex, ey), 5)
            pygame.draw.line(screen, (96, 76, 52),
                             (ex - int(math.sin(a) * 12), ey + int(math.cos(a) * 12)),
                             (ex + int(math.sin(a) * 12), ey - int(math.cos(a) * 12)), 6)
        splash = pygame.Surface((radius * 2, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(splash, (170, 200, 205, 60), splash.get_rect())
        screen.blit(splash, (sx - radius, sy + radius - 16))

    def _draw_gull(self, screen, gull, offset):
        cx, cy, orbit, speed, phase = gull
        t = pygame.time.get_ticks() * 0.001 * speed + phase
        gx = cx + math.cos(t) * orbit - offset[0]
        gy = cy + math.sin(t * 0.9) * orbit * 0.4 - offset[1]
        if not (-40 <= gx <= SCREEN_WIDTH + 40 and -40 <= gy <= SCREEN_HEIGHT + 40):
            return
        flap = math.sin(t * 7) * 5
        pygame.draw.lines(screen, (222, 224, 226), False,
                          [(gx - 9, gy - flap), (gx, gy), (gx + 9, gy - flap)], 2)

    def _draw_fog_bank(self, screen, bank, offset):
        y, speed, width, alpha, phase = bank
        tick = pygame.time.get_ticks() * 0.05
        x = (phase + tick * speed) % (self.width + width * 2) - width
        sx, sy = x - offset[0], y - offset[1]
        if not (-width <= sx <= SCREEN_WIDTH + width
                and -120 <= sy <= SCREEN_HEIGHT + 120):
            return
        fog = pygame.Surface((width, 130), pygame.SRCALPHA)
        for k in range(4):
            pygame.draw.ellipse(
                fog, (190, 196, 198, max(6, alpha - k * 4)),
                (k * width // 9, k * 9, width - k * width // 5, 120 - k * 14))
        screen.blit(fog, (sx, sy))

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
        for barge in self.barges:
            self._draw_barge(screen, barge, offset)
        for x, deck_bottom, width in self.piers:
            self._draw_pier(screen, x, deck_bottom, width, offset)
        self._draw_deck(screen, self.main_deck, offset)
        self._draw_deck(screen, self.lower_deck, offset, color=(77, 73, 66))
        for connector in self.connector_decks:
            self._draw_deck(screen, connector, offset, color=(81, 77, 69))
        for x, y, rx, ry, kind in self.deck_stains:
            stain = pygame.Rect(x - rx, y - ry, rx * 2, ry * 2)
            if not self._visible(stain, offset):
                continue
            r = self._screen_rect(stain, offset)
            if kind == "oil":
                pygame.draw.ellipse(screen, (66, 61, 53), r)
            elif kind == "rust":
                pygame.draw.ellipse(screen, (99, 74, 55), r)
            else:  # puddle heijastaa taivasta
                pygame.draw.ellipse(screen, (66, 84, 90), r)
                pygame.draw.arc(screen, (140, 165, 168), r.inflate(-6, -4),
                                0.4, 2.4, 2)
        for x, y in self.towers:
            self._draw_tower(screen, x, y, offset)
        self._draw_chains(screen, offset)
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
        for rect in self.quarantine_tents:
            self._draw_quarantine_tent(screen, rect, offset)
        for x, y in self.crown_banners:
            self._draw_crown_banner(screen, x, y, offset)
        for x, y, color in self.sponsor_banners:
            self._draw_sponsor_banner(screen, x, y, color, offset)
        for x, y, radius in self.waterwheels:
            self._draw_waterwheel(screen, x, y, radius, offset)
        for gear in self.great_gears:
            self._draw_great_gear(screen, *gear, offset)
        for line in self.red_lantern_lines:
            self._draw_red_lanterns(screen, line, offset)
        for x, y in self.lamps:
            self._draw_lamp(screen, x, y, offset)
        for x, y, height in self.cranes:
            self._draw_crane(screen, x, y, height, offset)
        for x, y, phase in self.steam_vents:
            self._draw_steam(screen, x, y, phase, offset)
        for gull in self.gulls:
            self._draw_gull(screen, gull, offset)

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
        # Matala ajelehtiva sumu yksiköiden päällä (Hush-Mantlen enne).
        for bank in self.fog_banks:
            self._draw_fog_bank(screen, bank, offset)
