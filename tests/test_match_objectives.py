# tests/test_match_objectives.py
"""
Sponsoritavoitteet Rattlebridgen Tier 1 -matseissa: arvonta (vain League +
rattlebridge + Tier 1+), neljä tavoitetta, hazard-osumien seuranta
ScrapringArenassa, palkkiot ja sponsorien kärsivällisyysbonus.
"""
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from settings import PLAYER_TEAM, ENEMY_TEAM
from systems import match_objectives as mo


class _Engine:
    def __init__(self, tier):
        self.tier = tier


class _Mgr:
    def __init__(self, engine_tier=2, location="rattlebridge", mode="League"):
        self.gold = 0
        self.reputation = 0
        self.npc_state = {"global": {"reputation": 0}}
        self.league_engine = _Engine(engine_tier)
        self.league_level = engine_tier
        self.mode = mode
        self.current_arena_location = location
        self.current_arena = None


class _Unit:
    def __init__(self, name, hp_ratio=1.0, dead=False, kills=0):
        self.name = name
        self.max_hp = 100
        self.current_hp = int(hp_ratio * 100)
        self.is_dead = dead
        self.stats = {"kills": kills}


def test_roll_only_for_rattlebridge_tier1_league():
    rng = random.Random(7)
    assert mo.roll_match_objective(_Mgr(engine_tier=1), rng) is None      # lore tier 0
    assert mo.roll_match_objective(_Mgr(location="muckford"), rng) is None
    assert mo.roll_match_objective(_Mgr(mode="Arena"), rng) is None
    obj = mo.roll_match_objective(_Mgr(), rng)
    assert obj and obj["id"] in mo.OBJECTIVES
    assert obj["name"] and obj["desc"]


def test_each_objective_check_logic():
    clean = {"fighters": [{"dead": False, "hp_ratio": 1.0, "kills": 0}] * 3,
             "hazard_hits": 0}
    dirty = {"fighters": [{"dead": True, "hp_ratio": 0.0, "kills": 0},
                          {"dead": False, "hp_ratio": 0.2, "kills": 1}],
             "hazard_hits": 3}
    assert mo.OBJECTIVES["clean_sweep"]["check"](clean) is True
    assert mo.OBJECTIVES["clean_sweep"]["check"](dirty) is False
    assert mo.OBJECTIVES["hazard_dance"]["check"](clean) is True
    assert mo.OBJECTIVES["hazard_dance"]["check"](dirty) is False
    assert mo.OBJECTIVES["crowd_pleaser"]["check"](
        {"fighters": [{"kills": 2, "dead": False, "hp_ratio": 1.0}]}) is True
    assert mo.OBJECTIVES["crowd_pleaser"]["check"](clean) is False
    assert mo.OBJECTIVES["iron_discipline"]["check"](clean) is True
    assert mo.OBJECTIVES["iron_discipline"]["check"](dirty) is False


def test_completed_objective_pays_and_boosts_sponsor_patience():
    from systems import sponsors
    m = _Mgr()
    m.reputation = 100
    sponsors.sign_sponsor(m, "ironspan_union")
    state = sponsors.ensure_sponsor_state(m)
    state["signed"]["ironspan_union"]["patience"] = 1
    gold0 = m.gold
    m.current_match_objective = {"id": "clean_sweep", "name": "Clean Sweep",
                                 "desc": "", "sponsor_line": ""}
    fighters = [_Unit("A"), _Unit("B", hp_ratio=0.8)]
    result = mo.evaluate_match_objective(m, True, fighters)
    assert result["completed"] is True
    assert m.gold == gold0 + mo.OBJECTIVE_GOLD
    assert state["signed"]["ironspan_union"]["patience"] == 2
    assert m.npc_state["rattlebridge"]["objective_history"][-1]["completed"]
    assert m.current_match_objective is None


def test_failed_or_lost_objective_pays_nothing():
    m = _Mgr()
    m.current_match_objective = {"id": "clean_sweep", "name": "Clean Sweep",
                                 "desc": "", "sponsor_line": ""}
    fighters = [_Unit("A", dead=True), _Unit("B")]
    result = mo.evaluate_match_objective(m, True, fighters)
    assert result["completed"] is False and m.gold == 0
    # Häviö ei koskaan täytä tavoitetta
    m.current_match_objective = {"id": "iron_discipline", "name": "Iron Discipline",
                                 "desc": "", "sponsor_line": ""}
    result = mo.evaluate_match_objective(m, False, [_Unit("A")])
    assert result["completed"] is False


def test_scrapring_arena_counts_player_hazard_hits():
    from arenas.tier_1.scrapring_arena import ScrapringArena
    from units.human import Human
    arena = ScrapringArena()
    assert arena.player_hazard_hits == 0
    gear = arena.gears[0]
    ally = Human("Ally", 0, 0, PLAYER_TEAM)
    foe = Human("Foe", 0, 0, ENEMY_TEAM)
    ally.rect.center = gear.rect.center
    foe.rect.center = gear.rect.center
    gear.phase, gear.timer = "slam", 999
    arena.update([ally, foe])
    assert arena.player_hazard_hits == 1, "vain pelaajan osumat lasketaan"


def test_hazard_dance_uses_arena_counter():
    m = _Mgr()
    from arenas.tier_1.scrapring_arena import ScrapringArena
    m.current_arena = ScrapringArena()
    m.current_arena.player_hazard_hits = 2
    m.current_match_objective = {"id": "hazard_dance", "name": "Hazard Dance",
                                 "desc": "", "sponsor_line": ""}
    result = mo.evaluate_match_objective(m, True, [_Unit("A")])
    assert result["completed"] is False
