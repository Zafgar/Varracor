"""Tier 0 team introduction portraits and persistent first-visit gate."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from menus.tier0_team_intro import (
    INTRO_FLAG,
    has_seen_tier0_team_intro,
    mark_tier0_team_intro_seen,
    render_team_portrait,
    should_show_tier0_team_intro,
    team_portrait_slug,
)


class _Engine:
    tier = 1


class _Manager:
    def __init__(self):
        self.league_engine = _Engine()
        self.npc_state = {"global": {"reputation": 0, "flags": {}, "deeds": []}}


def test_intro_flag_lives_in_persisted_npc_memory():
    manager = _Manager()
    assert should_show_tier0_team_intro(manager) is True
    assert has_seen_tier0_team_intro(manager) is False

    mark_tier0_team_intro_seen(manager)

    assert manager.npc_state["global"]["flags"][INTRO_FLAG] is True
    assert has_seen_tier0_team_intro(manager) is True
    assert should_show_tier0_team_intro(manager) is False


def test_intro_only_applies_to_rookie_dust_tier():
    manager = _Manager()
    manager.league_engine.tier = 2
    assert should_show_tier0_team_intro(manager) is False


def test_team_portrait_slug_is_stable_for_override_art():
    assert team_portrait_slug("Croak & Dagger") == "croak_dagger"
    assert team_portrait_slug("The Unclaimed Five") == "the_unclaimed_five"


def test_all_live_tier0_teams_render_a_full_portrait():
    pygame.init()
    pygame.display.set_mode((320, 180))

    from leagues.league_data import generate_league_teams

    teams = generate_league_teams(1)
    assert [team.name for team in teams] == [
        "Shanty Yard Saints",
        "Muckford Ratcatchers",
        "The Unclaimed Five",
        "The Ragged Lanterns",
        "Croak & Dagger",
        "The Siltbound",
        "Rusty Buckets",
    ]

    for team in teams:
        portrait = render_team_portrait(team, (320, 180))
        assert portrait.get_size() == (320, 180)
        assert portrait.get_bounding_rect().width == 320
        assert len(team.members) == 5

    # NOTE: do not call pygame.quit() here - the session-scoped conftest fixture
    # owns pygame's lifecycle. Quitting mid-session tore down the display and
    # cascaded "cannot convert without pygame.display initialized" into every
    # later module's manager fixture.
