# items/procedural_gear.py
"""Proseduraalinen varustegrafiikka: koodipiirretty fallback kun PNG puuttuu.

Kaikki draw_equipped-toteutukset vaativat item.imagen - ilman tätä aseet ja
kilvet olisivat NÄKYMÄTTÖMIÄ hahmojen käsissä kunnes spritet on toimitettu.
ensure_gear_image(item) rakentaa pienen koodigrafiikan aseryhmän mukaan ja
sävyttää kahvan/yksityiskohdat rarityn värillä. Kun oikea PNG ilmestyy
(esim. Asset Studion kautta), luokan oma _load_image voittaa eikä tätä
koskaan kutsuta.
"""

from __future__ import annotations

import pygame

RARITY_ACCENT = {
    "common": (150, 150, 155),
    "uncommon": (110, 190, 110),
    "rare": (110, 150, 230),
    "epic": (180, 110, 220),
    "legendary": (235, 170, 70),
}

_METAL = (168, 168, 176)
_DARK_METAL = (110, 110, 120)
_WOOD = (122, 88, 54)
_DARK_WOOD = (86, 60, 36)


def _accent(item):
    return RARITY_ACCENT.get(str(getattr(item, "rarity", "Common")).lower(),
                             RARITY_ACCENT["common"])


def _surface(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


# ---------------------------------------------------------------- muodot

def _sword(item):
    s = _surface(20, 48)
    a = _accent(item)
    pygame.draw.polygon(s, _METAL, [(10, 0), (14, 6), (13, 30), (7, 30), (6, 6)])
    pygame.draw.line(s, (220, 220, 228), (10, 2), (10, 28), 1)
    pygame.draw.rect(s, a, (3, 30, 14, 4))
    pygame.draw.rect(s, _DARK_WOOD, (8, 34, 4, 11))
    pygame.draw.circle(s, a, (10, 46), 3)
    return s


def _dagger(item):
    s = _surface(14, 30)
    a = _accent(item)
    pygame.draw.polygon(s, _METAL, [(7, 0), (10, 5), (9, 18), (5, 18), (4, 5)])
    pygame.draw.rect(s, a, (2, 18, 10, 3))
    pygame.draw.rect(s, _DARK_WOOD, (5, 21, 4, 8))
    return s


def _axe(item):
    s = _surface(28, 46)
    a = _accent(item)
    pygame.draw.rect(s, _WOOD, (12, 6, 5, 38))
    pygame.draw.polygon(s, _METAL, [(16, 4), (27, 8), (25, 20), (16, 18)])
    pygame.draw.line(s, a, (25, 9), (24, 18), 2)
    return s


def _mace(item):
    s = _surface(22, 46)
    a = _accent(item)
    pygame.draw.rect(s, _WOOD, (9, 14, 4, 30))
    pygame.draw.circle(s, _DARK_METAL, (11, 9), 8)
    for px, py in ((5, 4), (17, 4), (3, 12), (19, 12), (11, 0)):
        pygame.draw.circle(s, a, (px, py), 2)
    return s


def _spear(item):
    s = _surface(12, 62)
    a = _accent(item)
    pygame.draw.rect(s, _WOOD, (5, 12, 3, 50))
    pygame.draw.polygon(s, _METAL, [(6, 0), (11, 12), (1, 12)])
    pygame.draw.rect(s, a, (3, 12, 7, 2))
    return s


def _bow(item):
    s = _surface(26, 54)
    a = _accent(item)
    pygame.draw.arc(s, _WOOD, (2, 2, 34, 50), 1.4, 4.9, 3)
    pygame.draw.line(s, (210, 210, 210), (8, 4), (8, 50), 1)
    pygame.draw.rect(s, a, (2, 24, 6, 6))
    return s


def _crossbow(item):
    s = _surface(34, 30)
    a = _accent(item)
    pygame.draw.rect(s, _WOOD, (4, 13, 26, 5))
    pygame.draw.arc(s, _METAL, (0, 2, 30, 26), 0.6, 2.5, 3)
    pygame.draw.line(s, (210, 210, 210), (4, 6), (4, 26), 1)
    pygame.draw.rect(s, a, (22, 11, 6, 9))
    return s


def _staff(item):
    s = _surface(16, 60)
    a = _accent(item)
    pygame.draw.rect(s, _DARK_WOOD, (6, 10, 4, 50))
    pygame.draw.circle(s, a, (8, 8), 6)
    pygame.draw.circle(s, (255, 255, 255), (6, 6), 2)
    return s


def _book(item):
    s = _surface(24, 28)
    a = _accent(item)
    pygame.draw.rect(s, _DARK_WOOD, (2, 2, 20, 24), border_radius=3)
    pygame.draw.rect(s, a, (2, 2, 20, 24), 2, border_radius=3)
    pygame.draw.line(s, a, (12, 4), (12, 24), 1)
    return s


def _shield(item):
    s = _surface(28, 36)
    a = _accent(item)
    pygame.draw.polygon(s, _DARK_METAL,
                        [(2, 4), (26, 4), (26, 20), (14, 34), (2, 20)])
    pygame.draw.polygon(s, a,
                        [(2, 4), (26, 4), (26, 20), (14, 34), (2, 20)], 2)
    pygame.draw.circle(s, a, (14, 14), 4)
    return s


def _helmet(item):
    s = _surface(26, 20)
    a = _accent(item)
    pygame.draw.arc(s, _METAL, (1, 2, 24, 30), 0.0, 3.14, 8)
    pygame.draw.rect(s, a, (1, 14, 24, 3))
    return s


def _armor(item):
    s = _surface(30, 26)
    a = _accent(item)
    pygame.draw.rect(s, _DARK_METAL, (4, 2, 22, 22), border_radius=6)
    pygame.draw.rect(s, a, (4, 2, 22, 22), 2, border_radius=6)
    pygame.draw.line(s, a, (15, 4), (15, 22), 1)
    return s


def _tool(item):
    s = _surface(24, 44)
    a = _accent(item)
    pygame.draw.rect(s, _WOOD, (10, 8, 4, 36))
    tool_type = str(getattr(item, "tool_type", "")).lower()
    if tool_type == "pickaxe":
        pygame.draw.arc(s, _METAL, (0, 0, 24, 16), 0.3, 2.8, 4)
    else:
        pygame.draw.polygon(s, _METAL, [(14, 4), (23, 8), (21, 16), (14, 14)])
    pygame.draw.rect(s, a, (10, 8, 4, 3))
    return s


def _fishing_rod(item):
    s = _surface(16, 52)
    a = _accent(item)
    pygame.draw.line(s, _WOOD, (3, 50), (12, 4), 3)
    pygame.draw.line(s, (200, 200, 205), (12, 4), (14, 26), 1)
    pygame.draw.arc(s, (185, 185, 192), (11, 24, 6, 6), 3.0, 6.0, 1)
    pygame.draw.rect(s, a, (4, 42, 5, 3))
    return s


_BY_GROUP = {
    "sword": _sword, "dagger": _dagger, "axe": _axe, "mace": _mace,
    "spear": _spear, "bow": _bow, "crossbow": _crossbow, "staff": _staff,
    "book": _book, "shield": _shield, "pickaxe": _tool, "lumber_axe": _tool,
    "harvest_tool": _tool, "instrument": _book, "lute": _book,
    "fishing_rod": _fishing_rod,
}


def build_gear_image(item):
    """Rakentaa koodigrafiikan itemille tyypin perusteella (tai None)."""
    itype = str(getattr(item, "type", "")).lower()
    slot = str(getattr(item, "slot_type", "")).lower()
    group = str(getattr(item, "weapon_group", "")).lower()

    if itype == "shield" or (slot == "off_hand" and not group):
        return _shield(item)
    if slot == "head":
        return _helmet(item)
    if slot == "body":
        return _armor(item)
    if getattr(item, "tool_type", None):
        return _tool(item)
    builder = _BY_GROUP.get(group)
    if builder:
        return builder(item)
    if itype in ("melee", "ranged"):
        return _sword(item)
    if slot == "main_hand":
        # Geneerinen kädessä pidettävä (ämpärit yms. sekalaiset)
        return _tool(item)
    return None


def ensure_gear_image(item):
    """Lisää proseduraalisen imagen jos PNG puuttuu. Idempotentti."""
    if item is None or getattr(item, "image", None) is not None:
        return
    if getattr(item, "_procedural_gear_done", False):
        return
    item._procedural_gear_done = True
    if str(getattr(item, "name", "")).lower() in ("fists", "no armor"):
        return
    try:
        surf = build_gear_image(item)
    except Exception:
        surf = None
    if surf is not None:
        item.image = surf
