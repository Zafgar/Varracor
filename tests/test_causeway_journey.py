# tests/test_causeway_journey.py
"""
Muckford -> Rattlebridge kuljetaan Western causeway -reittiä pala palalta:
Greywash Ford ja Kingsreach Toll. Testaa reitin suunnat (route_heading),
palojen järjestyksen (journey_legs) ja etenemisen (survey/travel + tier-portti).
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from lore.world_map_data import (
    LOCATIONS, get_route, route_heading, journey_legs,
)
from systems.world_progression import (
    refresh_world_progression, route_key, survey_location,
    travel_to, location_status,
)


class _Clock:
    def __init__(self):
        self.minutes = 8 * 60.0
        self.day = 1

    def advance_day(self):
        self.day += 1


class _Unit:
    def __init__(self, level):
        self.level = level


class _Mgr:
    def __init__(self, league_tier=1, level=8):
        self.npc_state = {"global": {"reputation": 0, "flags": {}, "deeds": []}}
        self.league_engine = type("L", (), {"tier": league_tier})()
        self.league_level = league_tier
        self.player_character = _Unit(level)
        self.my_team = []
        self.reputation = 0
        self.world_clock = _Clock()
        self.mine_key_owned = False
        self.pending_world_location = None

    def set_tier(self, league_tier):
        self.league_engine.tier = league_tier
        self.league_level = league_tier


def test_waypoints_exist_with_expected_regions():
    assert LOCATIONS["greywash_ford"]["region"] == "sundered_heartlands"
    assert LOCATIONS["kingsreach_toll"]["region"] == "crownlands"


def test_no_direct_muckford_to_rattlebridge_route():
    assert get_route("muckford", "rattlebridge") is None


def test_causeway_headings_are_all_north_west():
    legs = [("muckford", "greywash_ford"),
            ("greywash_ford", "kingsreach_toll"),
            ("kingsreach_toll", "rattlebridge")]
    for a, b in legs:
        assert get_route(a, b) is not None, f"missing route {a}->{b}"
        assert route_heading(a, b) == "north-west", f"{a}->{b} heading"


def test_route_heading_is_reversible():
    assert route_heading("rattlebridge", "kingsreach_toll") == "south-east"


def test_journey_legs_walk_through_both_waypoints():
    legs = journey_legs("muckford", "rattlebridge")
    nodes = [legs[0][0]] + [leg[1] for leg in legs]
    assert nodes == ["muckford", "greywash_ford", "kingsreach_toll", "rattlebridge"]
    assert all(leg[2] is not None for leg in legs)      # jokaisella palalla reitti
    assert all(leg[3] == "north-west" for leg in legs)  # ja suunta


def test_first_leg_discovered_on_new_game():
    m = _Mgr(league_tier=1)
    state = refresh_world_progression(m)
    assert route_key("muckford", "greywash_ford") in state["discovered_routes"]
    # Kingsreachin tie ei ole vielä auki (Greywashia ei ole surveytty)
    assert route_key("greywash_ford", "kingsreach_toll") not in state["discovered_routes"]


def test_walk_the_causeway_and_tier_gate_at_rattlebridge():
    m = _Mgr(league_tier=1, level=8)  # lore tier 0 (uusi pelaaja)
    refresh_world_progression(m)

    ok, _, _ = travel_to(m, "greywash_ford")
    assert ok, "ensimmäinen pala pitäisi olla kuljettavissa"
    survey_location(m, "greywash_ford")

    ok, _, _ = travel_to(m, "kingsreach_toll")
    assert ok, "toinen pala aukeaa Greywashin surveystä"
    survey_location(m, "kingsreach_toll")

    st = location_status(m, "rattlebridge")
    assert st["route_discovered"] is True
    assert st["can_travel"] is False        # Tier 0 < required Tier 1
    assert "Tier 1" in st["reason"]

    # Ylennys Tier 1:een avaa sillan
    m.set_tier(2)  # lore tier 1
    st2 = location_status(m, "rattlebridge")
    assert st2["can_travel"] is True
