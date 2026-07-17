# tests/test_water_unification.py
"""Vartiotestit: YKSI vesimalli koko pelissä.

systems/procedural_water.py oli rinnakkainen vesitoteutus - poistettu.
Kaikki vesi on assets/tiles/water.py WaterBody:ä (pond/river/lake),
sama geometria ajaa renderöinnin, törmäyksen ja kalastuksen, ja sama
luokka toimii editorissa (carve_water) ja retkikartoilla (rect+kwargs).
"""
import pathlib

import pygame
import pytest

from assets.tiles.water import (
    FishingAnchor, ProceduralWaterBody, WaterBlocker, WaterBody,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_parallel_water_module_is_gone():
    assert not (ROOT / "systems" / "procedural_water.py").exists(), (
        "systems/procedural_water.py oli rinnakkainen vesimalli - "
        "kaikki vesi tulee assets/tiles/water.py:stä"
    )
    # Vanha nimi on alias samaan luokkaan, ei eri toteutus
    assert ProceduralWaterBody is WaterBody


def test_both_constructor_forms_work():
    a = WaterBody(100, 100, 400, 260, seed=3)             # editorimuoto
    b = WaterBody(pygame.Rect(100, 100, 400, 260), seed=3,
                  name="Test Pool", style="lake")          # retkikarttamuoto
    assert a.rect == b.rect
    assert b.name == "Test Pool"


def test_styles_resolve():
    river = WaterBody(0, 0, 300, 900, seed=1)   # auto -> river
    pond = WaterBody(0, 0, 500, 300, seed=1)    # auto -> pond
    lake = WaterBody(0, 0, 500, 300, seed=1, style="lake")
    assert river.style == "river"
    assert pond.style == "pond"
    assert lake.style == "lake"
    # Lake ei kapene: profiili on täysleveä myös reunoilla
    top_l, top_r = lake._local_bounds_at(4)
    pond_l, pond_r = pond._local_bounds_at(4)
    assert (top_r - top_l) > (pond_r - pond_l)


def test_shared_geometry_api():
    """Sama profiili ajaa contains_point/bounds_at/esteet/kalastuksen."""
    water = WaterBody(pygame.Rect(500, 200, 400, 1200), seed=9,
                      name="Guard River", style="river")
    # Keskipiste on vedessä, kaukana ulkopuolella ei
    assert water.contains_point(water.rect.center)
    assert not water.contains_point((water.rect.left - 200, water.rect.centery))
    # Rannat ovat rectin sisällä
    left, right = water.bounds_at(water.rect.centery)
    assert water.rect.left <= left < right <= water.rect.right
    # Esteet seuraavat rantaa ja ylityskaista jää auki
    band = (700, 800)
    barriers = water.make_collision_barriers([band])
    assert barriers
    assert all(isinstance(b, WaterBlocker) for b in barriers)
    assert not any(band[0] <= b.rect.centery <= band[1] for b in barriers)
    # Kalastusankkurit rannoilla, ei keskellä vettä
    anchors = water.fishing_anchors(6, difficulty=2)
    assert len(anchors) == 6
    for anchor in anchors:
        assert isinstance(anchor, FishingAnchor)
        assert not water.contains_point((anchor.x, anchor.y), inset=5)


def test_ripples_and_editor_serialization():
    water = WaterBody(0, 0, 300, 200, seed=4)
    water.splash(150, 100)
    assert len(water.ripples) == 1
    extra = water.serialize_extra()
    assert extra["w"] == 300 and extra["seed"] == 4 and "style" in extra
    # Editorin ghost tarvitsee image + image_pos
    assert water.image.get_size() == (300, 200)
    assert water.image_pos == (0, 0)
