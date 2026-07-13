# tests/test_weather_ambience.py
"""Sään äänimaisema: ukkonen soittaa oikeat avaimet (thunder_1..4,
regressio: vanha koodi soitti olematonta 'thunder'-avainta), sade/tuuli-
luupit seuraavat säätä ja sammuvat sisätiloihin mentäessä."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from world_clock import WorldClock


class _FakeChannel:
    def __init__(self):
        self.faded = False

    def fadeout(self, ms):
        self.faded = True


def _capture_sounds(monkeypatch):
    """Korvaa sound_system.play_sound tallentavalla versiolla."""
    from sound_manager import sound_system
    played = []

    def fake_play(name, loops=0, volume=None):
        played.append((name, loops))
        return _FakeChannel()

    monkeypatch.setattr(sound_system, "play_sound", fake_play)
    return played


def test_storm_thunder_uses_real_sound_keys(monkeypatch):
    played = _capture_sounds(monkeypatch)
    clock = WorldClock()
    clock.weather = "storm"
    clock._ambient_weather = "storm"  # ohita luuppikäynnistys tässä testissä
    clock._thunder_delay = 1
    clock.update()
    thunder = [n for n, _l in played if n.startswith("thunder")]
    assert thunder, "ukkosen jyrähdys soitettiin"
    assert thunder[0] in ("thunder_1", "thunder_2", "thunder_3", "thunder_4")


def test_ambient_loops_follow_weather(monkeypatch):
    played = _capture_sounds(monkeypatch)
    clock = WorldClock()
    clock.weather = "rain"
    clock.weather_timer = 10_000_000  # ei säänvaihtoa kesken testin
    clock.update()
    assert clock._ambient_weather == "rain"
    loop_names = [n for n, l in played if l == -1]
    assert "rain_medium" in loop_names

    # Sään vaihtuessa vanhat luupit feidataan ja uudet alkavat
    old_channels = list(clock._ambient_channels)
    assert old_channels
    clock.weather = "clear"
    clock.update()
    assert clock._ambient_weather == "clear"
    assert all(ch.faded for ch in old_channels)


def test_stop_ambient_on_indoors(monkeypatch):
    _capture_sounds(monkeypatch)
    clock = WorldClock()
    clock.weather = "storm"
    clock.weather_timer = 10_000_000
    clock.update()
    chans = list(clock._ambient_channels)
    assert chans
    clock.stop_ambient()
    assert clock._ambient_channels == []
    assert all(ch.faded for ch in chans)
    # Ulos palatessa luupit käynnistyvät taas
    clock.update()
    assert clock._ambient_weather == "storm"
    assert clock._ambient_channels


def test_clock_hud_draws_at_custom_position():
    from ui_kit import font_small
    clock = WorldClock()
    surf = pygame.Surface((1920, 1080))
    clock.draw_hud(surf, font_small, x=800)
    clock.minutes = 23 * 60.0  # yö -> kuu-ikoni
    clock.weather = "storm"
    clock.draw_hud(surf, font_small)
