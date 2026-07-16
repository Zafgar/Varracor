"""Kävelytilan ohjauksen (systems/walk_control.py) testit.

Kaksi tasoa:
1. Toiminnalliset testit move_player/handle_dash_keydown-funktioille.
2. VAHTITESTI: pelaajan ohjauksella on tasan kaksi auktoriteettia -
   Commander.run_combat_ai (taistelu) ja walk_control (kävely). Testi
   kaatuu jos johonkin näyttöön ilmestyy taas oma kovakoodattu
   WASD-luuppi tai K_SPACE-dash.
"""
import os
import re

import pygame
import pytest

from systems import walk_control
from systems import keybinds

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeKeys:
    """pygame.key.get_pressed()-korvike: vain annetut koodit pohjassa."""

    def __init__(self, *down):
        self.down = set(down)

    def __getitem__(self, code):
        return code in self.down


class DummyPlayer:
    def __init__(self, x=100, y=100):
        self.rect = pygame.Rect(x, y, 30, 40)
        self.is_dashing = False
        self.is_sprinting = False
        self.current_stamina = 100.0
        self.facing_right = True
        self.animation_state = "idle"
        self.animation_timer = 0
        self.dashes = []

    def set_sprinting(self, value):
        self.is_sprinting = bool(value)

    def perform_dash(self, dx, dy):
        self.dashes.append((dx, dy))


class Obstacle:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)


@pytest.fixture(autouse=True)
def _pygame_init():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    yield


def _press(monkeypatch, *actions):
    codes = [keybinds.key(a) for a in actions]
    monkeypatch.setattr(pygame.key, "get_pressed",
                        lambda: FakeKeys(*codes))


def test_moves_right_and_faces_movement(monkeypatch):
    p = DummyPlayer()
    _press(monkeypatch, "move_right")
    moved = walk_control.move_player(p)
    assert moved
    assert p.rect.x == 100 + int(walk_control.WALK_SPEED)
    assert p.facing_right is True
    assert p.animation_state == "run"

    _press(monkeypatch, "move_left")
    walk_control.move_player(p)
    assert p.facing_right is False


def test_diagonal_not_faster(monkeypatch):
    p = DummyPlayer()
    _press(monkeypatch, "move_right", "move_down")
    walk_control.move_player(p)
    dx = p.rect.x - 100
    dy = p.rect.y - 100
    # Normalisoitu: kumpikin akseli alle täyden nopeuden
    assert dx < walk_control.WALK_SPEED
    assert dy < walk_control.WALK_SPEED


def test_sprint_multiplies_and_only_when_moving(monkeypatch):
    p = DummyPlayer()
    _press(monkeypatch, "move_right", "sprint")
    walk_control.move_player(p, mouse_sprint=False)
    assert p.is_sprinting
    assert p.rect.x == 100 + int(round(
        walk_control.WALK_SPEED * walk_control.SPRINT_MULT))

    # Paikallaan sprintti EI aktivoidu (stamina ei kulu tyhjästä)
    p2 = DummyPlayer()
    _press(monkeypatch, "sprint")
    walk_control.move_player(p2, mouse_sprint=False)
    assert not p2.is_sprinting


def test_idle_when_no_input(monkeypatch):
    p = DummyPlayer()
    _press(monkeypatch)
    moved = walk_control.move_player(p)
    assert not moved
    assert p.animation_state == "idle"
    assert p.rect.topleft == (100, 100)


def test_running_animation_not_interrupted(monkeypatch):
    # Käynnissä oleva lyöntianimaatio saa pyöriä loppuun (pelitesti 16)
    p = DummyPlayer()
    p.animation_state = "attack"
    p.animation_timer = 10
    _press(monkeypatch)
    walk_control.move_player(p)
    assert p.animation_state == "attack"


def test_obstacle_blocks_movement(monkeypatch):
    p = DummyPlayer()
    wall = Obstacle(134, 80, 20, 100)   # heti oikealla
    _press(monkeypatch, "move_right")
    walk_control.move_player(p, obstacles=[wall])
    assert p.rect.right == wall.rect.left


def test_walkable_zone_blocks(monkeypatch):
    p = DummyPlayer()
    _press(monkeypatch, "move_right")
    walk_control.move_player(p, walkable=lambda r: False)
    assert p.rect.x == 100

    moved = walk_control.move_player(p, walkable=lambda r: True)
    assert moved


def test_bounds_clamp(monkeypatch):
    p = DummyPlayer(x=2, y=2)
    _press(monkeypatch, "move_left", "move_up")
    walk_control.move_player(p, bounds=pygame.Rect(0, 0, 500, 500))
    assert p.rect.left >= 0
    assert p.rect.top >= 0


def test_no_manual_move_while_dashing(monkeypatch):
    p = DummyPlayer()
    p.is_dashing = True
    _press(monkeypatch, "move_right")
    moved = walk_control.move_player(p)
    assert not moved
    assert p.rect.x == 100


def test_dash_keydown_uses_keybind(monkeypatch):
    p = DummyPlayer()
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (300, 100))
    ev = pygame.event.Event(pygame.KEYDOWN, key=keybinds.key("dash"))
    assert walk_control.handle_dash_keydown(p, ev)
    assert len(p.dashes) == 1
    # Dash suuntautuu hiirtä kohti (oikealle)
    assert p.dashes[0][0] > 0

    other = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F12)
    assert not walk_control.handle_dash_keydown(p, other)
    assert len(p.dashes) == 1


# ---------- Vahtitesti: ei rinnakkaisia ohjaustoteutuksia ----------

# Tiedostot joissa raa'at liikenäppäimet OVAT sallittuja
ALLOWED = {
    os.path.join("systems", "keybinds.py"),      # asettelun määrittely
    os.path.join("systems", "walk_control.py"),   # kävelyauktoriteetti
}

# Kovakoodattu WASD-liike (keys[pygame.K_w] tms.) tai K_SPACE-dash
_MOVE_PATTERN = re.compile(
    r"keys\[pygame\.K_[wasd]\]|K_[wasd]\]\s*-\s*keys\[pygame\.K_[wasd]")
_DASH_PATTERN = re.compile(r"K_SPACE\b[\s\S]{0,220}?perform_dash")


def _game_sources():
    for base in ("menus", "citys", "systems", "units"):
        for dirpath, _dirs, files in os.walk(os.path.join(ROOT, base)):
            for name in files:
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)
    yield os.path.join(ROOT, "gladiator.py")
    yield os.path.join(ROOT, "main.py")


def test_no_duplicate_movement_implementations():
    offenders = []
    for path in _game_sources():
        rel = os.path.relpath(path, ROOT)
        if rel in ALLOWED:
            continue
        with open(path, encoding="utf-8") as f:
            src = f.read()
        if _MOVE_PATTERN.search(src):
            offenders.append(rel + " (kovakoodattu WASD-liike)")
        if _DASH_PATTERN.search(src):
            offenders.append(rel + " (kovakoodattu K_SPACE-dash)")
    assert not offenders, (
        "Pelaajan ohjausta saa toteuttaa vain Commander.run_combat_ai "
        "(taistelu) ja systems/walk_control.py (kävely). Käytä "
        "walk_control.move_player / handle_dash_keydown: " +
        ", ".join(offenders))
