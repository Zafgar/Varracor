"""Procedural placeholder art and asset loading for Rattlebridge.

Final hand-painted files can be dropped into ``assets/generated/rattlebridge``
using the canonical names below. Until then the game creates readable PNG
placeholders on first run, so every Rattlebridge menu remains functional.
"""

from __future__ import annotations

import math
import os
import random
from pathlib import Path

import pygame


ASSET_DIR = Path("assets") / "generated" / "rattlebridge"
CANONICAL_ASSETS = {
    "city_overview": "city_overview.png",
    "city_map": "city_map.png",
    "scrapring": "scrapring.png",
    "the_span": "the_span.png",
    "bridgeward_hospital": "bridgeward_hospital.png",
    "canalworks": "canalworks.png",
    "props": "props.png",
}

# Also recognize the temporary JPEG names made from the concept art pass.
ALTERNATE_ASSETS = {
    "city_overview": ("city_overview.jpg",),
    "city_map": ("city_map.jpg",),
    "scrapring": ("scrapring.jpg",),
    "the_span": ("the_span.jpg",),
    "bridgeward_hospital": ("bridgeward_hospital.jpg",),
    "canalworks": ("canalworks.jpg",),
    "props": ("props.jpg",),
}

_CACHE = {}


def _safe_convert(surface: pygame.Surface) -> pygame.Surface:
    try:
        return surface.convert_alpha()
    except pygame.error:
        return surface


def _font(size: int, bold=False):
    try:
        return pygame.font.SysFont("serif", size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


def _noise(surface, rng, amount=1200, alpha=16):
    width, height = surface.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    for _ in range(amount):
        x = rng.randrange(width)
        y = rng.randrange(height)
        value = rng.randrange(65, 165)
        overlay.set_at((x, y), (value, value, value, alpha))
    surface.blit(overlay, (0, 0))


def _draw_water(surface, rect, rng):
    pygame.draw.rect(surface, (22, 45, 55), rect)
    for y in range(rect.top + 16, rect.bottom, 34):
        phase = rng.randint(-12, 12)
        pygame.draw.line(
            surface,
            (45, 77, 83),
            (rect.left + 20 + phase, y),
            (rect.right - 20 + phase, y),
            2,
        )


def _draw_bridge(surface, rect, stone=(92, 83, 70), iron=(70, 69, 67)):
    pygame.draw.rect(surface, (32, 30, 28), rect.inflate(24, 24), border_radius=8)
    pygame.draw.rect(surface, stone, rect, border_radius=6)
    pygame.draw.rect(surface, iron, rect, 6, border_radius=6)
    for x in range(rect.left + 24, rect.right, 80):
        pygame.draw.line(surface, (122, 108, 82), (x, rect.top + 8),
                         (x, rect.bottom - 8), 2)
    for x in range(rect.left + 20, rect.right - 20, 42):
        pygame.draw.circle(surface, (44, 43, 42), (x, rect.top + 12), 3)
        pygame.draw.circle(surface, (44, 43, 42), (x, rect.bottom - 12), 3)


def _draw_building(surface, rect, base, roof, windows=True, chimney=False):
    pygame.draw.rect(surface, (34, 31, 28), rect.inflate(12, 12), border_radius=7)
    pygame.draw.rect(surface, base, rect, border_radius=5)
    roof_rect = pygame.Rect(rect.x - 8, rect.y - 18, rect.w + 16, 38)
    pygame.draw.rect(surface, roof, roof_rect, border_radius=5)
    pygame.draw.line(surface, (196, 167, 105), roof_rect.topleft,
                     roof_rect.topright, 2)
    if windows:
        for x in range(rect.left + 24, rect.right - 20, 42):
            pygame.draw.rect(surface, (218, 177, 92),
                             (x, rect.y + 38, 14, 20), border_radius=2)
    pygame.draw.rect(surface, (49, 40, 32),
                     (rect.centerx - 14, rect.bottom - 38, 28, 38))
    if chimney:
        pygame.draw.rect(surface, (67, 59, 52),
                         (rect.right - 35, rect.top - 48, 18, 38))


def _draw_crane(surface, base_x, base_y, height=190):
    pygame.draw.line(surface, (67, 66, 62),
                     (base_x, base_y), (base_x, base_y - height), 14)
    pygame.draw.line(surface, (82, 78, 70),
                     (base_x, base_y - height),
                     (base_x + 130, base_y - height + 12), 10)
    pygame.draw.line(surface, (47, 44, 40),
                     (base_x + 112, base_y - height + 16),
                     (base_x + 112, base_y - 78), 3)
    pygame.draw.rect(surface, (90, 70, 48),
                     (base_x + 92, base_y - 78, 40, 32))


def _draw_banner(surface, x, y, color):
    pygame.draw.line(surface, (58, 52, 45), (x, y), (x, y + 100), 6)
    points = [(x + 4, y + 8), (x + 66, y + 18),
              (x + 56, y + 72), (x + 4, y + 62)]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.line(surface, (224, 190, 112), points[0], points[1], 2)


def _draw_steam(surface, x, y, tick=0):
    cloud = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for index in range(5):
        radius = 18 + index * 5
        cx = x + int(math.sin((tick + index) * 0.8) * 10)
        cy = y - index * 26
        pygame.draw.circle(cloud, (205, 210, 205, 48 - index * 5),
                           (cx, cy), radius)
    surface.blit(cloud, (0, 0))


def _save(surface, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        pygame.image.save(surface, str(path))
    except Exception:
        pass


def _city_overview(size=(1600, 900)):
    rng = random.Random(7711)
    surface = pygame.Surface(size)
    _draw_water(surface, surface.get_rect(), rng)
    horizon = int(size[1] * 0.6)
    pygame.draw.rect(surface, (56, 52, 47), (0, horizon, size[0], size[1] - horizon))
    for idx, y in enumerate((180, 330, 505, 655)):
        rect = pygame.Rect(-40 + idx * 45, y, size[0] + 80 - idx * 90, 92)
        _draw_bridge(surface, rect,
                     stone=(101 - idx * 5, 89 - idx * 4, 72 - idx * 3))
    for idx in range(15):
        x = 40 + idx * 108
        y = 105 + (idx % 4) * 116
        _draw_building(surface, pygame.Rect(x, y, 92, 110),
                       (100, 78, 58), (64, 59, 54), chimney=idx % 3 == 0)
    for x in (150, 540, 1010, 1390):
        _draw_crane(surface, x, 690, 180 + (x % 3) * 25)
    for x in range(80, size[0] - 80, 240):
        _draw_banner(surface, x, 185, (124, 39 + (x % 2) * 40, 48))
    for x in (280, 790, 1270):
        _draw_steam(surface, x, 180)
    _noise(surface, rng, 3600, 12)
    return surface


def _city_map(size=(1600, 1100)):
    rng = random.Random(7722)
    surface = pygame.Surface(size)
    _draw_water(surface, surface.get_rect(), rng)
    bridges = [
        pygame.Rect(40, 170, 1520, 240),
        pygame.Rect(120, 590, 1360, 210),
        pygame.Rect(300, 410, 260, 180),
        pygame.Rect(1030, 400, 260, 190),
    ]
    for rect in bridges:
        _draw_bridge(surface, rect)
    blocks = [
        pygame.Rect(120, 200, 250, 150),
        pygame.Rect(440, 205, 310, 150),
        pygame.Rect(835, 205, 260, 150),
        pygame.Rect(1180, 205, 275, 150),
        pygame.Rect(230, 620, 300, 145),
        pygame.Rect(610, 620, 350, 145),
        pygame.Rect(1050, 615, 300, 155),
    ]
    colors = [(111, 84, 57), (98, 74, 55), (118, 92, 64)]
    for idx, rect in enumerate(blocks):
        _draw_building(surface, rect, colors[idx % len(colors)],
                       (62, 60, 58), chimney=idx % 2 == 0)
    for x in range(100, 1500, 170):
        pygame.draw.rect(surface, (56, 54, 50), (x, 442, 55, 55), border_radius=4)
        pygame.draw.rect(surface, (115, 82, 43), (x + 8, 450, 39, 39), border_radius=3)
    for x in (120, 480, 840, 1210):
        _draw_crane(surface, x, 1020, 155)
    _noise(surface, rng, 4200, 10)
    return surface


def _scrapring(size=(1600, 1100)):
    rng = random.Random(7733)
    surface = pygame.Surface(size)
    surface.fill((37, 35, 34))
    outer = pygame.Rect(95, 70, 1410, 950)
    pygame.draw.ellipse(surface, (80, 70, 60), outer)
    pygame.draw.ellipse(surface, (145, 113, 72), outer, 18)
    floor = outer.inflate(-170, -150)
    pygame.draw.ellipse(surface, (92, 86, 78), floor)
    pygame.draw.ellipse(surface, (38, 36, 34), floor, 9)
    for index in range(12):
        angle = index / 12 * math.tau
        cx = floor.centerx + math.cos(angle) * floor.w * 0.40
        cy = floor.centery + math.sin(angle) * floor.h * 0.40
        pygame.draw.circle(surface, (55, 53, 52), (int(cx), int(cy)), 52)
        pygame.draw.circle(surface, (134, 121, 94), (int(cx), int(cy)), 52, 8)
        for tooth in range(8):
            a = tooth / 8 * math.tau
            px = int(cx + math.cos(a) * 35)
            py = int(cy + math.sin(a) * 35)
            pygame.draw.circle(surface, (58, 56, 54), (px, py), 7)
    for rect in (
        pygame.Rect(420, 310, 180, 100),
        pygame.Rect(980, 310, 180, 100),
        pygame.Rect(420, 690, 180, 100),
        pygame.Rect(980, 690, 180, 100),
    ):
        pygame.draw.rect(surface, (67, 89, 91), rect, border_radius=9)
        pygame.draw.rect(surface, (130, 160, 160), rect, 5, border_radius=9)
    for x, y in ((800, 250), (800, 850), (310, 550), (1290, 550)):
        pygame.draw.circle(surface, (52, 50, 48), (x, y), 38)
        pygame.draw.circle(surface, (180, 175, 155), (x, y), 28, 5)
        _draw_steam(surface, x, y - 30)
    for x in range(160, 1450, 170):
        _draw_banner(surface, x, 80, (125, 45, 53))
    _noise(surface, rng, 3200, 12)
    return surface


def _interior(size, palette, beds=False, tavern=False):
    rng = random.Random(sum(palette) + size[0])
    surface = pygame.Surface(size)
    surface.fill(palette)
    for x in range(0, size[0], 80):
        pygame.draw.line(surface, (palette[0] + 10, palette[1] + 8, palette[2] + 5),
                         (x, 0), (x, size[1]), 2)
    pygame.draw.rect(surface, (42, 38, 34), (40, 40, size[0] - 80, size[1] - 80), 14)
    if tavern:
        pygame.draw.rect(surface, (91, 58, 37), (90, 90, 420, 105), border_radius=12)
        for x in range(610, size[0] - 160, 260):
            pygame.draw.rect(surface, (95, 63, 40), (x, 250, 170, 85), border_radius=12)
            pygame.draw.rect(surface, (88, 56, 36), (x, 610, 170, 85), border_radius=12)
        for x in range(120, 480, 72):
            pygame.draw.circle(surface, (105, 64, 34), (x, 245), 28)
        pygame.draw.rect(surface, (85, 52, 33), (110, size[1] - 250, 250, 150), border_radius=8)
        pygame.draw.circle(surface, (230, 115, 48), (235, size[1] - 175), 58)
    elif beds:
        for row_y in (165, 470, 770):
            for x in range(120, size[0] - 260, 270):
                pygame.draw.rect(surface, (188, 180, 160), (x, row_y, 170, 82), border_radius=8)
                pygame.draw.rect(surface, (120, 105, 88), (x, row_y, 170, 82), 5, border_radius=8)
                pygame.draw.line(surface, (125, 48, 45), (x + 205, row_y - 40),
                                 (x + 205, row_y + 135), 5)
        pygame.draw.rect(surface, (100, 93, 82), (size[0] - 400, 95, 250, 190), border_radius=8)
        pygame.draw.circle(surface, (235, 205, 100), (size[0] - 275, 150), 45)
    _noise(surface, rng, 2600, 9)
    return surface


def _canalworks(size=(1600, 1100)):
    rng = random.Random(7744)
    surface = pygame.Surface(size)
    surface.fill((31, 38, 39))
    channels = [
        pygame.Rect(0, 210, 1600, 190),
        pygame.Rect(0, 720, 1600, 190),
        pygame.Rect(500, 0, 170, 1100),
        pygame.Rect(1110, 0, 170, 1100),
    ]
    for rect in channels:
        pygame.draw.rect(surface, (30, 67, 65), rect)
        for y in range(rect.top + 15, rect.bottom, 35):
            pygame.draw.line(surface, (45, 92, 86), (rect.left, y), (rect.right, y), 2)
    walkways = [
        pygame.Rect(0, 70, 1600, 110),
        pygame.Rect(0, 430, 1600, 220),
        pygame.Rect(0, 940, 1600, 110),
        pygame.Rect(250, 0, 150, 1100),
        pygame.Rect(790, 0, 150, 1100),
        pygame.Rect(1380, 0, 150, 1100),
    ]
    for rect in walkways:
        pygame.draw.rect(surface, (72, 69, 62), rect)
        pygame.draw.rect(surface, (118, 109, 91), rect, 5)
    for _ in range(30):
        x = rng.randint(80, 1510)
        y = rng.randint(80, 1010)
        pygame.draw.circle(surface, (51, 99, 54), (x, y), rng.randint(8, 26))
    for x, y in ((300, 480), (850, 520), (1440, 560), (900, 980)):
        pygame.draw.circle(surface, (58, 57, 54), (x, y), 44)
        pygame.draw.circle(surface, (122, 115, 93), (x, y), 44, 6)
    _noise(surface, rng, 4100, 12)
    return surface


def _props(size=(1600, 1100)):
    surface = pygame.Surface(size)
    surface.fill((245, 242, 232))
    _draw_crane(surface, 160, 310, 210)
    _draw_banner(surface, 360, 90, (130, 48, 55))
    pygame.draw.rect(surface, (86, 61, 40), (520, 130, 180, 130), border_radius=8)
    pygame.draw.rect(surface, (56, 51, 45), (760, 130, 250, 45), border_radius=5)
    pygame.draw.rect(surface, (56, 51, 45), (760, 200, 250, 45), border_radius=5)
    pygame.draw.circle(surface, (64, 62, 59), (1150, 190), 70)
    pygame.draw.circle(surface, (135, 124, 98), (1150, 190), 70, 9)
    for x in (160, 300, 440):
        pygame.draw.circle(surface, (92, 58, 32), (x, 560), 56)
        pygame.draw.line(surface, (45, 38, 32), (x - 56, 560), (x + 56, 560), 6)
    pygame.draw.rect(surface, (68, 64, 59), (650, 470, 390, 95), border_radius=10)
    pygame.draw.rect(surface, (111, 102, 86), (650, 470, 390, 95), 7, border_radius=10)
    for x in range(690, 1020, 55):
        pygame.draw.circle(surface, (40, 39, 38), (x, 516), 6)
    pygame.draw.rect(surface, (103, 76, 48), (1120, 440, 300, 200), border_radius=10)
    pygame.draw.rect(surface, (70, 67, 63), (170, 820, 380, 70), border_radius=8)
    for x in range(190, 530, 50):
        pygame.draw.line(surface, (35, 34, 32), (x, 820), (x + 25, 890), 5)
    pygame.draw.rect(surface, (73, 73, 69), (720, 790, 300, 180), border_radius=8)
    pygame.draw.rect(surface, (148, 138, 112), (720, 790, 300, 180), 7, border_radius=8)
    return surface


def generate_placeholder_assets(force=False):
    """Create all placeholder files. Returns a mapping of asset key to path."""
    pygame.font.init()
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    factories = {
        "city_overview": _city_overview,
        "city_map": _city_map,
        "scrapring": _scrapring,
        "the_span": lambda: _interior((1600, 1100), (74, 55, 39), tavern=True),
        "bridgeward_hospital": lambda: _interior((1600, 1100), (78, 78, 72), beds=True),
        "canalworks": _canalworks,
        "props": _props,
    }
    paths = {}
    for key, filename in CANONICAL_ASSETS.items():
        path = ASSET_DIR / filename
        if force or not path.exists():
            _save(factories[key](), path)
        paths[key] = path
    return paths


def _candidate_paths(key):
    filename = CANONICAL_ASSETS[key]
    yield ASSET_DIR / filename
    stem = Path(filename).stem
    yield ASSET_DIR / f"{stem}_final.png"
    yield ASSET_DIR / f"{stem}_final.jpg"
    for alternate in ALTERNATE_ASSETS.get(key, ()):
        yield ASSET_DIR / alternate


def resolve_asset_path(key):
    if key not in CANONICAL_ASSETS:
        raise KeyError(f"Unknown Rattlebridge asset key: {key}")
    for path in _candidate_paths(key):
        if path.exists():
            return path
    return generate_placeholder_assets().get(key)


def load_rattlebridge_image(key, size=None, alpha=False):
    cache_key = (key, tuple(size) if size else None, bool(alpha))
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    path = resolve_asset_path(key)
    image = None
    if path and path.exists():
        try:
            image = pygame.image.load(str(path))
            image = image.convert_alpha() if alpha else image.convert()
        except Exception:
            image = None

    if image is None:
        image = pygame.Surface(size or (960, 540), pygame.SRCALPHA)
        image.fill((65, 60, 54, 255))

    if size and image.get_size() != tuple(size):
        image = pygame.transform.smoothscale(image, size)
    image = _safe_convert(image)
    _CACHE[cache_key] = image
    return image.copy()


def clear_rattlebridge_asset_cache():
    _CACHE.clear()
