# tests/test_crypt_rebuild.py
"""Uusitun kryptan vartiotestit: käytävät, kuristuskohdat, sisään/ulos."""
import pygame
import pytest

from maps.crypt_1.arena import Arena


@pytest.fixture()
def arena():
    return Arena()


def test_crypt_is_corridor_dungeon_not_open_square(arena):
    """Sanktuaarin ja ulkokammioiden välissä on SEINÄÄ - kulku onnistuu
    vain käytävistä (kuristuskohdat)."""
    walls = [p for p in arena.props if type(p).__name__ == "WallSegment"]
    assert len(walls) > 10

    sanctum = arena.rooms["sanctum"]
    west = arena.rooms["west"]
    # Sanktuaarin ja länsikammion väli: käytävä on y~1620-1780; sen ylä-
    # ja alapuolella pitää olla seinää
    above = pygame.Rect(west.right, sanctum.top, 40, 250)
    below = pygame.Rect(west.right, sanctum.bottom - 250, 40, 250)
    assert any(w.rect.colliderect(above) for w in walls), "aukko käytävän yllä"
    assert any(w.rect.colliderect(below) for w in walls), "aukko käytävän alla"
    # Itse käytävä on auki
    corridor_mid = (west.right + 300, 1700)
    assert not any(w.rect.collidepoint(corridor_mid) for w in walls)
    # Kammioiden keskustat ovat auki
    for room in arena.rooms.values():
        assert not any(w.rect.collidepoint(room.center) for w in walls), (
            f"seinä kammion keskellä: {room}")


def test_crypt_entrance_exit_and_portals(arena):
    from systems.field_kit import GateZone

    gates = [p for p in arena.props if isinstance(p, GateZone)]
    labels = {g.label for g in gates}
    assert any("MUCKFORD" in label for label in labels), "sisäänkäynti puuttuu"
    assert any("VAULT" in label for label in labels), "holvi puuttuu"
    # Pelaaja aloittaa sisääntulohallista
    assert arena.rooms["entry"].inflate(60, 200).collidepoint(
        arena.entrance_point)
    # Portaalit ovat ulkokammioissa - EI sanktuaarissa
    assert len(arena.portal_points) == 5
    sanctum = arena.rooms["sanctum"]
    for point in arena.portal_points:
        assert not sanctum.collidepoint(point)


def test_crypt_has_resources_and_atmosphere(arena):
    from systems.field_kit import FieldResourceNode
    from assets.tiles.effect_emitters import EffectEmitter

    nodes = [p for p in arena.props if isinstance(p, FieldResourceNode)]
    assert len(nodes) >= 8, "keräysresursseja pitää olla"
    resources = {n.resource_name for n in nodes}
    assert "Vortex Shard" in resources, "holvin aarre puuttuu"
    ores = [p for p in arena.props if getattr(p, "type", "") == "ore"]
    assert len(ores) >= 2, "rautamalmi puuttuu"
    emitters = [p for p in arena.props if isinstance(p, EffectEmitter)]
    assert len(emitters) >= 5


def test_crypt_mission_spawns_waves_at_chamber_portals(manager):
    """Aalto 1 syntyy ulkokammion portaalista, ei satunnaisesta nurkasta."""
    import maps.crypt_1.mission as mission_mod

    manager.current_arena = Arena()
    logic = mission_mod.MissionLogic({"id": "test", "title": "t"})
    logic.manager = manager
    manager.match_in_progress = True
    logic.start_next_wave(manager)

    spawned = [u for u in manager.enemy_team if not u.is_dead]
    assert spawned, "aalto ei spawnannut vihollisia"
    chamber_rects = [arena_room.inflate(200, 200) for name, arena_room
                     in manager.current_arena.rooms.items()
                     if name in ("west", "east", "north", "nw", "ne")]
    for unit in spawned:
        assert any(room.collidepoint(unit.rect.center)
                   for room in chamber_rects), (
            f"{unit.name} spawnasi kammioiden ulkopuolelle "
            f"{unit.rect.center}")


def test_crypt_pathfinding_grid_sees_walls(manager):
    """Reitinhaku näkee uudet seinät (vanhat paljaat rectit eivät edes
    rekisteröityneet is_structure-tarkistukseen)."""
    from ai.pathfinding import NavigationGrid

    arena = Arena()
    grid = NavigationGrid(arena)
    # Seinäkuori HETI sanktuaarin reunan takana on tukossa (kaukainen
    # umpikallio on tyhjää - kuori riittää, koska se ympäröi kammiot)
    sanctum = arena.rooms["sanctum"]
    wall_x = sanctum.left + 60          # kaukana käytäväaukoista
    wall_y = sanctum.top - 50           # kuoren sisällä
    gx, gy = int(wall_x // 40), int(wall_y // 40)
    assert grid.grid[gx][gy] == 1, "seinä puuttuu reitinhakuruudukosta"
    # Käytäväsolu on auki
    cx, cy = int((arena.rooms["west"].right + 300) // 40), int(1700 // 40)
    assert grid.grid[cx][cy] == 0, "käytävä tukossa reitinhaussa"
