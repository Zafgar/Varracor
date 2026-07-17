# tests/test_placeholder_sprites.py
"""Placeholder-grafiikan vartiotestit.

Jokaisen monsterin on piirryttävä ILMAN asset-tiedostoja: koodipiirretty
siluetti, ei tyhjä eikä yksivärinen täyttölaatta. Undead + rider olivat
aiemmin pelkkiä flat-fill-neliöitä."""
import pygame
import pytest

from settings import ENEMY_TEAM
from units import monster_registry as reg


def _color_count(surface: pygame.Surface) -> int:
    """Montako eri väriä pinnassa on (pieni otanta riittää)."""
    colors = set()
    w, h = surface.get_size()
    for x in range(0, w, 2):
        for y in range(0, h, 2):
            colors.add(tuple(surface.get_at((x, y))))
            if len(colors) > 4:
                return len(colors)
    return len(colors)


@pytest.mark.parametrize("name", [
    "Skeleton", "Zombie", "Skeleton Archer", "Rat Rider",
])
def test_humanoid_monsters_have_drawn_placeholders(name):
    unit = reg.create_monster(name, 100, 100, ENEMY_TEAM)
    # Siluetti eikä flat fill: väriä JA läpinäkyvää taustaa
    assert _color_count(unit.image) > 3, (
        f"{name}: placeholder näyttää yksiväriseltä täyttölaatalta"
    )
    # Tilakohtaiset spritet olemassa (animaatiokone ei putoa tyhjään)
    for state in ("idle", "run", "attack" if name != "Rat Rider" else "charge_1"):
        assert state in unit.sprites, f"{name}: tila {state} puuttuu"
    # Eri tilat näyttävät eriltä (isku ei ole sama kuva kuin idle)
    key = "attack" if name != "Rat Rider" else "charge_2"
    idle_bytes = pygame.image.tostring(unit.sprites["idle"], "RGBA")
    other_bytes = pygame.image.tostring(unit.sprites[key], "RGBA")
    assert idle_bytes != other_bytes, f"{name}: tilat ovat identtisiä"


def test_every_registry_monster_renders_something():
    for name in reg.monster_names():
        unit = reg.create_monster(name, 100, 100, ENEMY_TEAM)
        assert unit.image is not None, name
        assert _color_count(unit.image) >= 2, (
            f"{name}: kuva näyttää tyhjältä/yksiväriseltä"
        )
