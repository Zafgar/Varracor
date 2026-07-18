# tests/test_rebuilt_field_maps.py
"""Uusittujen kenttien vartiotestit: rift, suo, viemäri.

Yhteiset vaatimukset (pelitesti 30): selvä sisään/ulos (GateZone),
kerättävät resurssit, rakenteellinen maasto (ei satunnaisripottelua
tyhjyyteen), vesi yhtenäisellä vesimallilla ja spawn-alueet maastossa.
"""
import pygame
import pytest

from systems.field_kit import FieldResourceNode, GateZone


# ---------------------------------------------------------------- rift
def _rift(theme_id):
    from menus.rift_site_menu import THEMES, _RiftArena
    return _RiftArena(THEMES[theme_id], theme_id)

@pytest.mark.parametrize("theme_id", ["marsh", "graveyard", "bogwood"])
def test_rift_arena_has_terrain_water_and_resources(theme_id):
    arena = _rift(theme_id)
    assert arena.width >= 4000 and arena.height >= 2400, "liian pieni"
    # Maastoa ja esteitä on oikeasti (ei tyhjä tasanko)
    assert len(arena.props) > 25, f"{theme_id}: karu tasanko"
    assert len(arena.obstacles) > 15
    # Vesi yhtenäisellä mallilla
    assert arena.waters, f"{theme_id}: ei vettä"
    # Kerättävät resurssit
    nodes = [p for p in arena.props if isinstance(p, FieldResourceNode)]
    assert len(nodes) >= 8, f"{theme_id}: resursseja liian vähän"
    # Taistelukenttä repeämän edessä on esteetön
    clearing = arena._rift_clearing
    for obstacle in arena.obstacles:
        rect = getattr(obstacle, "rect", obstacle)
        assert not clearing.contains(rect), (
            f"{theme_id}: este repeämän taistelukentällä {rect}")
    # Polku sisäänkäynniltä repeämälle pysyy aukinaisena keskeltä
    path = arena._path_rect
    mid_path = pygame.Rect(path.centerx - 150, path.centery - 40, 300, 80)
    for obstacle in arena.obstacles:
        rect = getattr(obstacle, "rect", obstacle)
        assert not rect.colliderect(mid_path), f"{theme_id}: polku tukossa"


def test_rift_menu_uses_gate_and_harvest():
    """Riftin paluuportti on GateZone ja E kerää nodet."""
    import inspect
    from menus import rift_site_menu

    src = inspect.getsource(rift_site_menu.RiftSiteMenu.on_enter)
    assert "GateZone" in src
    src_evt = inspect.getsource(rift_site_menu.RiftSiteMenu.handle_event)
    assert "harvest" in src_evt


# ---------------------------------------------------------------- bog
def test_bog_is_structured_swamp_with_water():
    from maps.bog_1.arena import Arena

    arena = Arena()
    assert (arena.width, arena.height) == (5200, 3400)
    # SUOLLA ON VETTÄ: neljä lampea + esteet rannoille
    assert len(arena.waters) == 4
    assert any(getattr(o, "is_water", False) for o in arena.obstacles)
    # Kalastuspaikka laiturilta
    assert arena.fishing_spots
    # Portti ja peikon pesä
    gates = [p for p in arena.props if isinstance(p, GateZone)]
    assert any("MUCKFORD" in g.label for g in gates)
    assert arena.lair_rect.w > 0
    lair_bones = [p for p in arena.props if isinstance(p, FieldResourceNode)
                  and p.rect.colliderect(arena.lair_rect.inflate(100, 100))]
    assert lair_bones, "pesästä puuttuvat luut"
    # Spawn-alueet maastossa eivät osu veteen
    for zone in arena.spawn_zones:
        for water in arena.waters:
            assert not water.rect.contains(zone), "spawn-alue veden alla"
    # Vanhat crafting-nodet edelleen mukana
    names = {type(p).__name__ for p in arena.props}
    assert {"NightcapFungus", "ScrapPile", "SwampTree",
            "VoidIronNode"} <= names


def test_bog_mission_spawns_in_zones(manager):
    import maps.bog_1.mission as mission_mod
    from maps.bog_1.arena import Arena

    manager.current_arena = Arena()
    logic = mission_mod.MissionLogic({"id": "test"})
    logic.manager = manager
    manager.match_in_progress = True
    logic.start_next_wave(manager)
    spawned = [u for u in manager.enemy_team if not u.is_dead]
    assert spawned
    zones = [z.inflate(140, 140) for z in manager.current_arena.spawn_zones]
    for unit in spawned:
        assert any(z.collidepoint(unit.rect.center) for z in zones), (
            f"{unit.name} spawnasi vyöhykkeiden ulkopuolelle")


# ---------------------------------------------------------------- sewer
def test_sewer_has_gate_and_gatherables():
    from maps.rat_sewer.arena import Arena

    arena = Arena()
    gates = [p for p in arena.props if isinstance(p, GateZone)]
    assert gates and gates[0].kind == "grate"
    nodes = [p for p in arena.props if isinstance(p, FieldResourceNode)]
    assert len(nodes) >= 4
    assert arena.entrance_point == arena.entry_pos


# ------------------------------------------------------- battle harvest
def test_battle_screen_harvest_collects_node(manager):
    """E-keräys toimii taistelutilassa (sama järjestelmä joka kartalla)."""
    from menus.battle_screen import BattleScreen
    from units.commander import Commander

    class _Arena:
        width, height = 2000, 2000
        props = []
        obstacles = []

    arena = _Arena()
    node = FieldResourceNode("t1", 500, 500, "Rusty Scrap", "scrap", (2, 2))
    arena.props = [node]
    manager.current_arena = arena
    if manager.player_character is None:
        manager.player_character = Commander("Test", 0, 0)
    player = manager.player_character
    player.is_dead = False
    player.rect.center = (node.rect.centerx + 30, node.rect.centery)

    screen = BattleScreen(manager)
    before = int(manager.inventory.get("Rusty Scrap", 0))
    screen._try_harvest_nearby()
    assert manager.inventory.get("Rusty Scrap", 0) == before + 2
    assert node.harvested
