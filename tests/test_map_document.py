# tests/test_map_document.py
"""Karttadokumentin vartiotestit: nimi + koko + vienti + tuonti.

Työnkulku jota nämä suojaavat: editori (F8) -> nimeä (F7) -> vie (F9)
yhdeksi JSON-riviksi -> rivi liitetään chattiin -> kovakoodataan
maps/custom_maps.py:hin -> ladataan takaisin editoriin/peliin.
Serialisointi ja lataus ovat YHTEISET (systems/map_document.py) -
editorilla ja pelillä ei ole rinnakkaisia toteutuksia.
"""
import pygame
import pytest

from settings import ENEMY_TEAM, RED
from systems import map_document as md


class _BareArena:
    """Minimaalinen areena ilman Muckford-layoutia."""

    def __init__(self, w=4000, h=3000):
        self.width, self.height = w, h
        self.map_name = "Test Fields"
        self.props = []
        self.floor_props = []
        self.obstacles = []


def _populated_arena():
    from assets.tiles.muckford_objects import MuckfordTree, Well
    from assets.tiles.effect_emitters import SmokeEmitter, FogPatch
    from assets.tiles.water import FishingJetty, WaterBody
    from units.rat import GiantRat

    arena = _BareArena(8000, 6000)
    tree = MuckfordTree(500, 400)
    tree._editor_note = "landmark"
    arena.props.append(tree)
    arena.obstacles.append(tree)
    well = Well(900, 700)
    arena.props.append(well)
    arena.obstacles.append(well)

    smoke = SmokeEmitter(950, 640, variant=2)
    arena.props.append(smoke)

    fog = FogPatch(2000, 2000, variant=3)
    arena.props.append(fog)

    water = WaterBody(3000, 2500, 900, 500, seed=12, name="South Pool",
                      style="lake")
    arena.floor_props.append(water)
    arena.floor_props.append(FishingJetty(2950, 2700, seed=5))

    rat = GiantRat("Pikkuinen", 1200, 900, ENEMY_TEAM)
    arena.props.append(rat)
    return arena


def test_roundtrip_blob_preserves_everything(manager):
    src = _populated_arena()
    doc = md.serialize_map(src)
    blob = md.export_blob(doc)
    assert "\n" not in blob, "blobin pitää olla YKSI rivi (copy-paste)"

    loaded = md.import_blob("  " + blob + "\n")
    dst = _BareArena(100, 100)
    units = md.apply_to_arena(loaded, dst, manager)

    assert dst.map_name == "Test Fields"
    assert (dst.width, dst.height) == (8000, 6000)
    # Kaikki palasi: 2 esteproppia + 2 efektiä + 1 yksikkö propseissa
    non_units = [p for p in dst.props if not hasattr(p, "team_color")]
    effects = [p for p in non_units if getattr(p, "is_effect", False)]
    assert len(effects) == 2
    assert {type(e).__name__ for e in effects} == {"SmokeEmitter", "FogPatch"}
    assert effects[0].variant in (2, 3)
    # Efektit EIVÄT ole esteitä
    assert not any(getattr(o, "is_effect", False) for o in dst.obstacles)
    # Vesi + laituri palasivat tyylin ja nimen kanssa, esteet laskettu
    from assets.tiles.water import WaterBody
    waters = [p for p in dst.floor_props if isinstance(p, WaterBody)]
    assert len(waters) == 1
    assert waters[0].name == "South Pool" and waters[0].style == "lake"
    assert any(getattr(o, "is_water", False) for o in dst.obstacles)
    # Yksikkö palasi nimensä ja tiiminsä kanssa
    assert len(units) == 1
    assert units[0].name == "Pikkuinen"
    assert type(units[0]).__name__ == "GiantRat"
    # Note säilyi
    tree = next(p for p in dst.props if type(p).__name__ == "MuckfordTree")
    assert getattr(tree, "_editor_note", "") == "landmark"


def test_import_rejects_garbage():
    with pytest.raises(Exception):
        md.import_blob('{"format": "SOMETHING-ELSE"}')
    with pytest.raises(Exception):
        md.import_blob("not json at all")


def test_custom_map_registry_roundtrip(manager):
    from maps import custom_maps

    src = _populated_arena()
    src.map_name = "Registry Test Map"
    blob = md.export_blob(md.serialize_map(src))
    try:
        doc = custom_maps.register(blob)
        assert "Registry Test Map" in custom_maps.custom_map_names()
        assert custom_maps.get_custom_map("Registry Test Map") is doc
        dst = _BareArena()
        md.apply_to_arena(doc, dst, manager)
        assert dst.map_name == "Registry Test Map"
        assert dst.width == 8000
    finally:
        custom_maps.CUSTOM_MAPS.pop("Registry Test Map", None)


def test_resize_arena_supports_huge_maps():
    arena = _BareArena(1920, 1080)
    md.resize_arena(arena, 20000, 12000)
    assert (arena.width, arena.height) == (20000, 12000)


def test_effect_emitters_animate_and_serialize():
    from assets.tiles.effect_emitters import EFFECT_CLASSES

    for cls in EFFECT_CLASSES:
        emitter = cls(100, 100, variant=2)
        assert emitter.is_effect and not emitter.is_structure
        assert emitter.has_shadow is False
        for _ in range(60):
            emitter.update(None, None)
        assert emitter.particles, f"{cls.__name__} ei tuottanut partikkeleita"
        surf = pygame.Surface((300, 300))
        emitter.draw_on_screen(surf, (0, 0))
        extra = emitter.serialize_extra()
        assert extra["variant"] == 2


def test_editor_export_writes_single_line_blob(manager, tmp_path, monkeypatch):
    """F9 kirjoittaa map_export.txt:hen yhden VARRACOR-MAP-rivin."""
    from tools.map_editor import MapEditor

    monkeypatch.chdir(tmp_path)
    manager.current_arena = _populated_arena()
    editor = MapEditor(manager)
    editor.export_map()
    text = (tmp_path / "map_export.txt").read_text().strip()
    assert "\n" not in text
    doc = md.import_blob(text)
    assert doc["name"] == "Test Fields"
    assert doc["width"] == 8000
