# citys/mucford/market_stalls.py
"""Muckfordin market-alueen kojut: koodipiirretyt liikkeet joihin kävellään.

Jokainen koju piirtää katoksensa liikkeen värillä ja tunnusikonin
(porkkana/miekka/kilpi/pullo/laatikko). E-avaimella aukeaa liikkeen oma
kauppasivu (district_shop). Kojut ovat visuaalisia (ei törmäystä), joten
ne eivät riko kaupungin polkuja.
"""

from __future__ import annotations

import pygame

from citys.mucford.market_data import MARKET_SHOPS


def _build_stall_image(shop: dict) -> pygame.Surface:
    w, h = 168, 128
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    awning = shop.get("awning", (110, 90, 60))
    dark = tuple(max(0, c - 34) for c in awning)

    # Varjo + pöytä
    pygame.draw.ellipse(s, (12, 10, 8, 90), (10, h - 26, w - 20, 22))
    table = pygame.Rect(16, 58, w - 32, 44)
    pygame.draw.rect(s, (92, 66, 42), table, border_radius=6)
    pygame.draw.rect(s, (58, 42, 28), table, 3, border_radius=6)
    for px in range(table.left + 14, table.right - 8, 30):
        pygame.draw.line(s, (70, 50, 32), (px, table.top + 4),
                         (px, table.bottom - 4), 2)
    # Jalat
    pygame.draw.rect(s, (58, 42, 28), (table.left + 6, table.bottom, 10, 22))
    pygame.draw.rect(s, (58, 42, 28), (table.right - 16, table.bottom, 10, 22))

    # Katos raidoilla + tolpat
    pygame.draw.rect(s, (58, 42, 28), (12, 22, 8, 46))
    pygame.draw.rect(s, (58, 42, 28), (w - 20, 22, 8, 46))
    canopy = pygame.Rect(4, 8, w - 8, 30)
    pygame.draw.rect(s, awning, canopy, border_radius=8)
    for stripe in range(canopy.left + 10, canopy.right, 26):
        pygame.draw.rect(s, dark, (stripe, canopy.top + 2, 12, canopy.h - 4))
    for k in range(6):
        fx = canopy.left + 8 + k * ((canopy.w - 16) // 5)
        pygame.draw.polygon(s, awning, [(fx, canopy.bottom), (fx + 14, canopy.bottom),
                                        (fx + 7, canopy.bottom + 9)])

    # Tunnusikoni pöydälle
    kind = shop.get("kind", "general")
    cx, cy = table.centerx, table.top - 8
    if kind == "produce":
        pygame.draw.circle(s, (168, 60, 52), (cx - 16, cy + 20), 9)   # omena
        pygame.draw.circle(s, (196, 150, 60), (cx + 6, cy + 22), 8)   # muna
        pygame.draw.polygon(s, (96, 132, 62), [(cx + 22, cy + 12),
                            (cx + 30, cy + 28), (cx + 14, cy + 28)])   # yrtti
    elif kind == "weapons":
        pygame.draw.line(s, (168, 168, 176), (cx - 16, cy + 30), (cx + 14, cy), 5)
        pygame.draw.line(s, (108, 80, 50), (cx - 20, cy + 34), (cx - 12, cy + 26), 6)
        pygame.draw.line(s, (120, 120, 128), (cx - 6, cy + 6), (cx + 4, cy + 16), 3)
    elif kind == "armor":
        shield = pygame.Rect(cx - 14, cy + 2, 28, 30)
        pygame.draw.rect(s, (96, 108, 134), shield, border_radius=10)
        pygame.draw.rect(s, (60, 68, 88), shield, 3, border_radius=10)
        pygame.draw.line(s, (60, 68, 88), (cx, shield.top + 4),
                         (cx, shield.bottom - 4), 2)
    elif kind == "potions":
        pygame.draw.rect(s, (120, 84, 140), (cx - 8, cy + 8, 16, 22),
                         border_radius=6)
        pygame.draw.rect(s, (208, 196, 168), (cx - 4, cy + 2, 8, 8))
        pygame.draw.circle(s, (170, 120, 190), (cx + 16, cy + 24), 7)
    else:  # general
        crate = pygame.Rect(cx - 16, cy + 6, 30, 24)
        pygame.draw.rect(s, (116, 88, 52), crate, border_radius=4)
        pygame.draw.line(s, (78, 58, 36), crate.topleft, crate.bottomright, 3)
        pygame.draw.circle(s, (176, 150, 96), (cx + 20, cy + 24), 6)

    return s


class MarketStall(pygame.sprite.Sprite):
    """Kaupunkiin sijoitettava koju. Yhteensopiva kaupungin renderables- ja
    props-putkien kanssa (rect + image + update)."""

    def __init__(self, shop_id: str, x: int, y: int):
        super().__init__()
        self.shop_id = shop_id
        self.shop = MARKET_SHOPS[shop_id]
        self.image = _build_stall_image(self.shop)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.is_market_stall = True

    def update(self, *args, **kwargs):
        pass

    @property
    def interact_point(self):
        return self.rect.centerx, self.rect.bottom + 26


def build_market_row(center_x: int, base_y: int, spacing: int = 300):
    """Kojurivi market-aukiolle, keskitettynä annettuun pisteeseen."""
    stalls = []
    ids = list(MARKET_SHOPS)
    start = center_x - ((len(ids) - 1) * spacing) // 2
    for index, shop_id in enumerate(ids):
        stalls.append(MarketStall(shop_id, start + index * spacing, base_y))
    return stalls
