# tests/test_fast_travel.py
"""
Fast travel: ensivierailu Rattlebridgeen avaa Ironspan Unionin rahtilinjan
Muckfordin ja Rattlebridgen välille (sponsorin operoima pikayhteys).
"""
import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from systems.world_progression import (
    ensure_world_state, has_fast_travel, location_status,
    mark_location_visited, travel_to, unlock_fast_travel,
)


class _Clock:
    def __init__(self):
        self.minutes = 8 * 60.0
        self.day = 1
        self.year = 3

    def advance_day(self):
        self.day += 1


class _Unit:
    def __init__(self, level):
        self.level = level


class _Mgr:
    def __init__(self, league_tier=2, level=8):
        self.npc_state = {"global": {"reputation": 0, "flags": {}, "deeds": []}}
        self.league_engine = type("L", (), {"tier": league_tier})()
        self.league_level = league_tier
        self.player_character = _Unit(level)
        self.my_team = []
        self.reputation = 0
        self.world_clock = _Clock()
        self.mine_key_owned = False
        self.pending_world_location = None


def test_no_fast_travel_before_first_visit():
    m = _Mgr()
    assert has_fast_travel(m, "muckford", "rattlebridge") is False
    st = location_status(m, "rattlebridge")
    assert st["can_travel"] is False
    assert "node by node" in st["reason"] or "route" in st["reason"].lower()


def test_first_rattlebridge_visit_unlocks_freight_line():
    m = _Mgr()
    mark_location_visited(m, "rattlebridge", set_current=True)
    assert has_fast_travel(m, "muckford", "rattlebridge") is True
    assert "freight" in getattr(m, "pending_fast_travel_notice", "").lower()
    # Toinen vierailu ei tuota uutta ilmoitusta
    m.pending_fast_travel_notice = ""
    mark_location_visited(m, "rattlebridge", set_current=True)
    assert m.pending_fast_travel_notice == ""


def test_fast_travel_works_both_directions():
    m = _Mgr()
    mark_location_visited(m, "rattlebridge", set_current=True)

    # Rattlebridge -> Muckford rahtivaunulla
    st = location_status(m, "muckford")
    assert st["can_travel"] is True
    assert "freight" in st["route"]["label"].lower()
    ok, msg, _ = travel_to(m, "muckford")
    assert ok and "freight" in msg.lower()
    assert ensure_world_state(m)["current_location"] == "muckford"

    # Muckford -> Rattlebridge takaisin (tier-portti täyttyy, engine tier 2)
    st = location_status(m, "rattlebridge")
    assert st["can_travel"] is True
    ok, _, target = travel_to(m, "rattlebridge")
    assert ok
    assert target  # kohteella on target_state


def test_fast_travel_state_is_json_safe():
    m = _Mgr()
    unlock_fast_travel(m, "muckford", "rattlebridge")
    json.dumps(m.npc_state)
