# tests/test_casting_integration.py
"""Pelitesti 38: casting-integraatio.
1) Movement-lock: rootattu caster keskeytyy liikkeestä (pelaaja); AI ei
   liiku latauksen aikana.
2) Cast bar: _draw_cast_bar piirtää latauspalkin kun caster latautuu.
3) Counterspell: katalogin loitsu keskeyttää vastustajan latauksen.
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


# ----------------------------------------------------------------------
# 3) Counterspell
# ----------------------------------------------------------------------

def test_counterspell_in_catalog_and_interrupts_enemy():
    from spells import casting
    from spells.catalog import make_catalog_spell
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m = _mgr()
    p = m.player_character
    p.intelligence = 30
    p.max_mana = 400
    p.current_mana = 400
    p.rect.center = (400, 500)
    enemy = GiantRat("Mage", 500, 500, ENEMY_TEAM)
    m.all_units.empty()
    m.all_units.add(p)
    m.all_units.add(enemy)
    fired = []
    casting.start_cast(enemy, None, 60, lambda: fired.append(1),
                       counterable=True)
    cs = make_catalog_spell("counterspell")
    assert cs is not None and cs.archetype == "counter"
    assert "interrupts" in cs.describe().lower()
    assert cs.cast(p, enemy, m, target_pos=enemy.rect.center) is True
    assert not casting.is_casting(enemy), "counter keskeytti vihollisen"
    for _ in range(80):
        casting.tick_caster(enemy)
    assert fired == [], "counteroitu loitsu ei laukea"


def test_counterspell_costs_mana_and_no_damage():
    from spells.catalog import make_catalog_spell
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m = _mgr()
    p = m.player_character
    p.max_mana = 400
    p.current_mana = 400
    p.rect.center = (400, 500)
    e = GiantRat("E", 500, 500, ENEMY_TEAM)
    e.max_hp = e.current_hp = 500
    m.all_units.empty()
    m.all_units.add(p)
    m.all_units.add(e)
    cs = make_catalog_spell("counterspell")
    mana0 = p.current_mana
    cs.cast(p, e, m, target_pos=e.rect.center)
    assert p.current_mana < mana0, "counter kuluttaa manan"
    assert e.current_hp == 500, "counter ei tee vahinkoa"


# ----------------------------------------------------------------------
# 2) Cast bar
# ----------------------------------------------------------------------

def test_cast_bar_draws_only_while_casting():
    from spells import casting
    m = _mgr()
    p = m.player_character
    p.rect.center = (400, 400)
    surf = pygame.Surface((1920, 1080))
    before = surf.copy()
    p._draw_cast_bar(surf, (0, 0))
    assert surf.get_buffer().raw == before.get_buffer().raw, \
        "ei palkkia ilman latausta"
    # Kesken latauksen palkki piirtyy (ruutu muuttuu)
    class _Spell:
        name = "Test"
        icon_color = (200, 120, 255)
    casting.start_cast(p, _Spell(), 60, lambda: None)
    p.active_cast.elapsed = 30
    p._draw_cast_bar(surf, (0, 0))
    assert surf.get_buffer().raw != before.get_buffer().raw, \
        "latauspalkki piirtyy"


# ----------------------------------------------------------------------
# 1) Movement-lock
# ----------------------------------------------------------------------

def test_ai_does_not_move_while_casting():
    from spells import casting
    from ai.base_ai import BaseAI
    from units.rat import GiantRat
    from settings import ENEMY_TEAM
    m = _mgr()
    rat = GiantRat("Caster", 500, 500, ENEMY_TEAM)
    ai = rat.ai_controller if hasattr(rat, "ai_controller") else BaseAI(rat)
    casting.start_cast(rat, None, 60, lambda: None, rooted=True)
    x0 = rat.rect.centerx
    # Yritä liikuttaa - casting estää
    ai._move_towards(100, 0, 100, [], [rat], m)
    assert rat.rect.centerx == x0, "AI ei liiku latauksen aikana"


def test_player_move_interrupts_rooted_cast():
    from spells import casting
    m = _mgr()
    p = m.player_character
    casting.start_cast(p, None, 60, lambda: None, rooted=True)
    assert casting.is_rooted(p)
    # Simuloi liike (sama logiikka kuin commanderin WASD-haarassa)
    if casting.is_rooted(p):
        casting.on_caster_moved(p)
    assert not casting.is_casting(p), "liike keskeytti rootatun latauksen"
