import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1920, 1080))

from leagues.league_engine import LeagueEngine
from npc.dwarf_league_manager import DwarfLeagueManager
from settings import ENEMY_TEAM, PLAYER_TEAM
from units.human import Human
from units.rat import GiantRat
from systems.muckford_opening_integration import (
    FOREST_ROAD_WIDTH,
    REGISTRATION_CREATURE_WINS,
    REGISTRATION_FEE_SP,
    REGISTRATION_REPUTATION,
    _opening,
    install_muckford_opening_integration,
    register_team,
    registration_status,
)

install_muckford_opening_integration()

from citys.mucford.forest_road_arena import ForestRoadArena


class DummyVFX:
    def show_damage(self, *_args, **_kwargs):
        pass


class DummyManager:
    def __init__(self):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.gold = 0
        self.reputation = 0
        self.innkeeper_debt = 25
        self.team_registration_pending = False
        self.league_engine = LeagueEngine()
        self.village_tasks = None
        self.vfx = DummyVFX()
        self.deeds = []
        self.inventory = {}
        self.player_character = None

    def record_deed(self, deed_id, text):
        self.deeds.append((deed_id, text))


def test_registration_requires_debt_reputation_wins_and_silver():
    manager = DummyManager()
    ok, missing = registration_status(manager)
    assert not ok
    assert len(missing) == 4

    manager.innkeeper_debt = 0
    manager.reputation = REGISTRATION_REPUTATION
    manager.gold = REGISTRATION_FEE_SP
    _opening(manager)["creature_wins"] = REGISTRATION_CREATURE_WINS

    ok, missing = registration_status(manager)
    assert ok
    assert missing == []


def test_register_team_charges_sp_and_updates_league_name():
    manager = DummyManager()
    manager.innkeeper_debt = 0
    manager.reputation = REGISTRATION_REPUTATION
    manager.gold = REGISTRATION_FEE_SP + 7
    _opening(manager)["creature_wins"] = REGISTRATION_CREATURE_WINS

    ok, message = register_team(manager, "  Mudbound   Lanterns!  ")

    assert ok
    assert "Mudbound Lanterns" in message
    assert manager.gold == 7
    assert _opening(manager)["team_registered"] is True
    assert _opening(manager)["team_name"] == "Mudbound Lanterns"
    assert _opening(manager)["first_recruit_free"] is True
    standings = manager.league_engine.get_grand_slam_standings()
    player = next(row for row in standings if row["team_id"] == "PLAYER")
    assert player["team_name"] == "Mudbound Lanterns"


def test_bram_registration_dialogue_unlocks_only_when_ready():
    manager = DummyManager()
    npc = DwarfLeagueManager()
    state = _opening(manager)
    context = {
        "memory": manager.npc_state,
        "my_data": {"flags": {}, "relationship": 0},
        "player": {"gold": 0, "team_name": "Unregistered"},
        "reputation": 0,
        "innkeeper_debt": 25,
        "league_engine": manager.league_engine,
        "player_roster": [],
        "completed_quests": [],
    }
    assert npc.get_dialogue_root(context) == "opening_register_locked"

    context["player"]["gold"] = REGISTRATION_FEE_SP
    context["reputation"] = REGISTRATION_REPUTATION
    context["innkeeper_debt"] = 0
    state["creature_wins"] = REGISTRATION_CREATURE_WINS
    assert npc.get_dialogue_root(context) == "opening_register_ready"


def test_forest_road_is_long_enough_for_staged_encounters():
    arena = ForestRoadArena()
    assert arena.width == FOREST_ROAD_WIDTH
    assert arena.width >= 7000
    assert arena.height == 1200
    assert len(arena.props) > 20


def test_post_intro_rat_kill_counts_and_guarantees_bounty_proof():
    manager = DummyManager()
    player = Human("Tester", 0, 0, PLAYER_TEAM, "Common")
    manager.player_character = player
    state = _opening(manager)
    state["intro_complete"] = True

    rat = GiantRat("Road Rat", 0, 0, ENEMY_TEAM)
    rat.current_hp = 1
    rat.take_damage(999, attacker=player, manager=manager)

    assert state["creature_wins"] == 1
    assert manager.inventory["Rat Tail"] == 1
