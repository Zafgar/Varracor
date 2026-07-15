# tests/test_spell_vfx.py
"""Pelitesti 36: näyttävät koodilla piirretyt loitsu-VFX:t.
Varmistaa: glow-pinnat, Mote/Flash haihtuvat, TieredBolt jättää vanan ja
räjähtää osumassa, ja jokainen katalogin vahinkotyyppi on paletissa.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


class _Arena:
    obstacles = []
    width = 2000
    height = 2000


def _mgr():
    import main  # noqa: F401
    from game_manager import GameManager
    m = GameManager()
    m.current_arena = _Arena()
    return m


def test_glow_surface_is_cached_and_sized():
    from spells.spell_vfx import glow_surface
    a = glow_surface(20, (255, 120, 30), 170)
    b = glow_surface(20, (255, 120, 30), 170)
    assert a is b, "sama glow välimuistista"
    assert a.get_width() == 40 and a.get_flags() & pygame.SRCALPHA


def test_all_catalog_damage_types_have_palette():
    from spells.catalog import CATALOG
    from spells.spell_vfx import ELEMENTS
    for spec in CATALOG:
        assert spec["damage_type"] in ELEMENTS, \
            f"{spec['damage_type']} puuttuu paletista"


def test_mote_and_flash_fade_and_die():
    from spells.spell_vfx import Mote, Flash
    m = Mote(100, 100, (255, 120, 30), size=8, life=6)
    for _ in range(6):
        m.update()
    assert not m.alive(), "Mote haihtuu ja kuolee"
    f = Flash(100, 100, (255, 240, 170), 30, life=6)
    for _ in range(6):
        f.update()
    assert not f.alive(), "Flash haihtuu ja kuolee"


def test_tiered_bolt_leaves_trail_and_bursts_on_hit():
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    from spells.catalog import make_catalog_spell
    m = _mgr()
    p = m.player_character
    p.intelligence = 30
    p.max_mana = 300
    p.current_mana = 300
    p.rect.center = (400, 500)
    e = GiantRat("E", 470, 500, ENEMY_TEAM)
    e.max_hp = e.current_hp = 100000
    m.all_units.empty()
    m.all_units.add(p)
    m.all_units.add(e)
    hp0 = e.current_hp
    make_catalog_spell("arcane_dart").cast(p, e, m, target_pos=e.rect.center)
    peak = 0
    for _ in range(60):
        m.vfx.update(obstacles=[])
        peak = max(peak, len(m.vfx.particles))
    assert peak >= 10, "ammuksen vana + osuma tuottavat partikkeleita"
    assert e.current_hp < hp0, "osuma tekee silti vahinkoa"


def test_aoe_and_impact_burst_spawn_particles():
    from spells.spell_vfx import impact_burst, aoe_burst
    m = _mgr()
    n0 = len(m.vfx.particles)
    impact_burst(m, 300, 300, "Fire", radius=40, sparks=10)
    assert len(m.vfx.particles) > n0
    n1 = len(m.vfx.particles)
    aoe_burst(m, 500, 500, "Holy", radius=120)
    assert len(m.vfx.particles) > n1


def test_vfx_draws_without_crash():
    from spells.spell_vfx import impact_burst
    m = _mgr()
    impact_burst(m, 400, 400, "Frost", radius=50, sparks=12)
    surf = pygame.Surface((1920, 1080))
    for _ in range(10):
        m.vfx.update(obstacles=[])
        m.vfx.draw_top(surf, (0, 0))
