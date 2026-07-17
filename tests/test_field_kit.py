# tests/test_field_kit.py
"""Kenttätyökalupakin vartiotestit: YKSI järjestelmä kenttien palasille.

Resurssinodet, portit (selvä sisään/ulos), luolastoseinät ja -käytävät
tulevat systems/field_kit.py:stä - vanhat neljä kopioitua nodeluokkaa
ovat nyt pakin alaluokkia."""
import pygame
import pytest

from systems.field_kit import (
    DEFAULT_PAINTERS, FieldResourceNode, FloorPatch, GateZone, WallSegment,
    build_dungeon, spread_points,
)


class _FakeManager:
    def __init__(self):
        self.inventory = {}


def test_resource_node_harvest_flow():
    node = FieldResourceNode("n1", 100, 100, "Iron Ore", "ore", (2, 2))
    m = _FakeManager()
    msg = node.harvest(m)
    assert msg == "+2 Iron Ore"
    assert m.inventory["Iron Ore"] == 2
    assert node.harvested
    # Toinen keräys ei anna mitään
    assert node.harvest(m) is None
    assert m.inventory["Iron Ore"] == 2


def test_all_default_painters_draw():
    for style in DEFAULT_PAINTERS:
        node = FieldResourceNode("x", 0, 0, style.title(), style)
        assert node.image.get_size() == (node.SIZE, node.SIZE)
        # Kuvassa on jotain (ei tyhjä pinta)
        assert pygame.mask.from_surface(node.image).count() > 10, style


def test_legacy_node_classes_are_kit_subclasses():
    """Neljä vanhaa kopioluokkaa perii nyt pakin rungon."""
    from citys.mucford.forest_excursion import MarshResourceNode
    from citys.mucford.drowned_chapel import ChapelResourceNode
    from citys.mucford.greywash_ford import FordResourceNode
    from citys.mucford.kingsreach_toll import TollResourceNode

    for cls in (MarshResourceNode, ChapelResourceNode, FordResourceNode,
                TollResourceNode):
        assert issubclass(cls, FieldResourceNode), cls.__name__

    # Rakentuminen vanhoilla signatuureilla toimii
    marsh = MarshResourceNode(10, 10, "Bogwort", "herb", (1, 2))
    assert marsh.resource_name == "Bogwort"
    chapel = ChapelResourceNode("c1", 10, 10, "Grave-Lotus")
    assert chapel.style == "lotus"
    ford = FordResourceNode("f1", 10, 10, "Driftwood", "driftwood")
    toll = TollResourceNode("t1", 10, 10, "Charcoal", "charcoal")
    for node in (marsh, chapel, ford, toll):
        assert not node.harvested
        assert node.image is not None


def test_gate_zone_kinds_and_label():
    for kind in ("arch", "sign", "ladder", "grate", "portal"):
        gate = GateZone(50, 50, kind=kind, label=f"TO {kind.upper()}",
                        facing="down")
        assert gate.is_gate
        assert not gate.is_structure          # portista voi kävellä
        assert gate.image.get_width() > 0
        extra = gate.serialize_extra()
        assert extra["kind"] == kind and "label" in extra


def test_build_dungeon_corridors_not_one_big_square():
    """Luolasto EI ole iso neliö: kammiot + käytävät, seinät välissä."""
    rooms = [pygame.Rect(200, 200, 600, 500),
             pygame.Rect(1400, 200, 600, 500),
             pygame.Rect(800, 1100, 800, 600)]
    corridors = [pygame.Rect(800, 380, 600, 140),     # huone1 -> huone2
                 pygame.Rect(1100, 700, 140, 400)]    # huone2 -> huone3
    walls, floors = build_dungeon(rooms + corridors, 2400, 2000,
                                  wall_style="crypt")
    assert walls, "seiniä pitää syntyä"
    assert len(floors) == len(rooms) + len(corridors)
    # Estemäärä pysyy järkevänä (kuori, ei umpitäyttö)
    assert len(walls) < 250, f"liikaa seinäpaloja: {len(walls)}"
    # Kammioiden VÄLISSÄ (käytävän vieressä) on seinää
    beside_corridor = pygame.Rect(800, 560, 600, 100)  # käytävän alapuoli
    assert any(w.rect.colliderect(beside_corridor) for w in walls), (
        "käytävän viereltä puuttuu seinä - tämä olisi iso avoin neliö"
    )
    # Kammion keskellä EI ole seinää
    assert not any(w.rect.collidepoint(rooms[0].center) for w in walls)
    # Käytävällä EI ole seinää
    assert not any(w.rect.collidepoint(corridors[0].center) for w in walls)
    # Seinät ovat oikeita esteitä (kulku + ammukset)
    assert all(w.is_structure and w.blocks_projectiles for w in walls)


def test_spread_points_respects_min_dist_and_avoid():
    import math
    import random
    rng = random.Random(5)
    area = pygame.Rect(0, 0, 2000, 1500)
    water = pygame.Rect(800, 0, 400, 1500)
    points = spread_points(rng, area, 20, min_dist=120, avoid=[water])
    assert len(points) >= 15
    for i, (x, y) in enumerate(points):
        assert not water.collidepoint(x, y)
        for x2, y2 in points[i + 1:]:
            assert math.hypot(x - x2, y - y2) >= 120


def test_kit_classes_roundtrip_in_map_document(manager):
    """Portit/seinät/lattiat/nodet kulkevat VARRACOR-MAP-viennin läpi."""
    from systems import map_document as md

    class _BareArena:
        def __init__(self):
            self.width, self.height = 3000, 2000
            self.map_name = "Kit Test"
            self.props = []
            self.floor_props = []
            self.obstacles = []

    src = _BareArena()
    src.props.append(GateZone(100, 100, kind="arch", label="ENTER",
                              facing="down"))
    src.props.append(FieldResourceNode("r1", 500, 500, "Crystal", "crystal"))
    wall = WallSegment(900, 900, 200, 80, style="sewer")
    src.props.append(wall)
    src.obstacles.append(wall)
    src.floor_props.append(FloorPatch(300, 300, 400, 400, style="dirt"))

    blob = md.export_blob(md.serialize_map(src))
    dst = _BareArena()
    md.apply_to_arena(md.import_blob(blob), dst, manager)

    types = {type(p).__name__ for p in dst.props}
    assert {"GateZone", "FieldResourceNode", "WallSegment"} <= types
    gate = next(p for p in dst.props if isinstance(p, GateZone))
    assert gate.label == "ENTER" and gate.kind == "arch"
    node = next(p for p in dst.props if isinstance(p, FieldResourceNode))
    assert node.resource_name == "Crystal" and node.style == "crystal"
    new_wall = next(p for p in dst.props if isinstance(p, WallSegment))
    assert new_wall.style == "sewer" and new_wall in dst.obstacles
    floor = next(p for p in dst.floor_props if isinstance(p, FloorPatch))
    assert floor.style == "dirt"
