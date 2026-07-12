import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1920, 1080))

from menus.barracks_menu import BarracksMenu
from citys.rattlebridge.bridgeward_hospital_menu import BridgewardHospitalMenu
from citys.rattlebridge.canalworks_menu import CanalworksMenu
from citys.rattlebridge.rattlebridge_contracts_menu import RattlebridgeContractsMenu
from citys.rattlebridge.scrapring_menu import ScrapringMenu
from citys.rattlebridge.the_span_menu import TheSpanMenu
from lore.world_map_data import LOCATIONS
from systems.world_progression import arena_access_status


class DummyClock:
    def __init__(self):
        self.minutes = 8 * 60.0
        self.day = 1

    def advance_day(self):
        self.day += 1

    def update(self):
        pass


class DummyLeague:
    def __init__(self, tier=2):
        self.tier = tier
        self.wins_this_tier = 0


class DummyUnit:
    def __init__(self, level=8, hp=100):
        self.level = level
        self.max_hp = hp
        self.current_hp = 20
        self.max_mana = 60
        self.current_mana = 5
        self.max_stamina = 100
        self.current_stamina = 12
        self.injured = True
        self.injury_severity = "Minor"
        self.rect = pygame.Rect(150, 120, 32, 24)
        self.facing_right = True
        self.animation_state = "idle"
        self.is_sprinting = False
        self.is_dashing = False
        self.xp = 0

    def set_sprinting(self, value):
        self.is_sprinting = bool(value)

    def update(self, obstacles=None, manager=None):
        pass

    def draw_on_screen(self, surface, offset=(0, 0)):
        pygame.draw.rect(surface, (50, 200, 50),
                         self.rect.move(-offset[0], -offset[1]))


class DummyManager:
    def __init__(self, tier=2, level=8, gold=500, reputation=30):
        self.npc_state = {
            "global": {
                "reputation": reputation,
                "flags": {},
                "deeds": [],
            }
        }
        self.player_character = DummyUnit(level)
        self.my_team = [DummyUnit(level), DummyUnit(level)]
        self.gold = gold
        self.reputation = reputation
        self.inventory = {}
        self.city_storage = {}
        self.equipment_bag = []
        self.league_engine = DummyLeague(tier)
        self.league_level = tier
        self.world_clock = DummyClock()
        self.world_paused = False
        self.market_return_state = "muckford_city"
        self.city_storage_return_state = "muckford_city"
        self.city_spawn_point = None
        self.current_arena_location = None
        self.league_return_state = None
        self.camera_x = 0
        self.camera_y = 0

    def add_material(self, name, count=1):
        self.inventory[name] = self.inventory.get(name, 0) + int(count)


def test_span_rest_consumes_gold_heals_roster_and_advances_time(monkeypatch):
    manager = DummyManager(gold=100)
    menu = TheSpanMenu(manager)
    monkeypatch.setattr(
        "citys.rattlebridge.the_span_menu.sound_system.play_sound",
        lambda *_args, **_kwargs: None,
    )

    menu._rest()

    assert manager.gold == 82
    assert manager.world_clock.minutes == 16 * 60
    for unit in [manager.player_character] + manager.my_team:
        assert unit.current_hp >= 72
        assert unit.current_mana == unit.max_mana
        assert unit.current_stamina == unit.max_stamina
        assert unit.injured is False
        assert unit.injury_severity is None


def test_span_refuses_rest_without_payment(monkeypatch):
    manager = DummyManager(gold=5)
    menu = TheSpanMenu(manager)
    monkeypatch.setattr(
        "citys.rattlebridge.the_span_menu.sound_system.play_sound",
        lambda *_args, **_kwargs: None,
    )

    menu._rest()

    assert manager.gold == 5
    assert "credit" in menu.feedback.lower()


def test_bridgeward_services_have_distinct_injury_results(monkeypatch):
    manager = DummyManager(gold=500)
    manager.player_character.injury_severity = "Serious"
    menu = BridgewardHospitalMenu(manager)
    monkeypatch.setattr(
        "citys.rattlebridge.bridgeward_hospital_menu.sound_system.play_sound",
        lambda *_args, **_kwargs: None,
    )

    menu.selected = "specialist"
    menu._treat()

    assert manager.gold == 375
    assert manager.player_character.current_hp >= 90
    assert manager.player_character.injury_severity == "Minor"
    assert manager.player_character.injured is True
    assert manager.npc_state["rattlebridge"]["hospital_visits"] == 1

    menu.selected = "full"
    menu._treat()
    assert manager.gold == 135
    for unit in [manager.player_character] + manager.my_team:
        assert unit.current_hp == unit.max_hp
        assert unit.injured is False
        assert unit.injury_severity is None


def test_scrapring_access_requires_tier_one_circuit():
    manager = DummyManager(tier=2, level=8)
    menu = ScrapringMenu(manager)
    menu.on_enter()

    ok, reason = arena_access_status(manager, "rattlebridge")
    assert ok
    assert "Scrapring" in reason
    assert menu.btn_league.enabled
    assert manager.current_arena_location == "rattlebridge"

    manager.league_engine.tier = 1
    menu._sync_access()
    assert not menu.btn_league.enabled


def test_canalworks_nests_and_boss_persist_and_reward_materials(monkeypatch):
    manager = DummyManager(level=9, gold=50)
    menu = CanalworksMenu(manager)
    monkeypatch.setattr(
        "citys.rattlebridge.canalworks_menu.sound_system.play_sound",
        lambda *_args, **_kwargs: None,
    )

    for index in range(3):
        menu._clear_nest(index)

    state = manager.npc_state["rattlebridge"]
    assert state["canal_nests"] == [True, True, True]
    assert state["gutter_patrols"] == 3
    assert manager.inventory["Scrap Iron"] >= 4
    assert manager.inventory["Nightcap Fungus"] >= 2

    menu._fight_boss()

    assert state["gutter_boss_defeated"] is True
    assert state["gutter_swarm_kills"] == 1
    assert manager.inventory["Direhide"] == 1
    assert manager.reputation == 38
    assert manager.gold > 50


def test_low_level_party_cannot_defeat_fused_gutter_swarm(monkeypatch):
    manager = DummyManager(level=6)
    menu = CanalworksMenu(manager)
    state = menu._state()
    state["canal_nests"] = [True, True, True]
    monkeypatch.setattr(
        "citys.rattlebridge.canalworks_menu.sound_system.play_sound",
        lambda *_args, **_kwargs: None,
    )

    menu._fight_boss()

    assert state["gutter_boss_defeated"] is False
    assert "overwhelms" in menu.feedback


def test_local_contracts_follow_real_city_state_and_claim_rewards(monkeypatch):
    manager = DummyManager(gold=10, reputation=30)
    menu = RattlebridgeContractsMenu(manager)
    monkeypatch.setattr(
        "citys.rattlebridge.rattlebridge_contracts_menu.sound_system.play_sound",
        lambda *_args, **_kwargs: None,
    )
    contract = next(
        item for item in menu._state()
        if item == "rattlebridge_toll_manifest"
    )
    data = next(
        item for item in __import__(
            "citys.rattlebridge.rattlebridge_data",
            fromlist=["RATTLEBRIDGE_CONTRACTS"],
        ).RATTLEBRIDGE_CONTRACTS
        if item["id"] == contract
    )

    menu._accept(data)
    assert menu._contract_state(contract)["status"] == "active"
    assert not menu._is_complete(data)

    manager.npc_state.setdefault("rattlebridge", {}).setdefault(
        "districts_visited", []
    ).append("freight_deck")
    assert menu._is_complete(data)

    menu._claim(data)

    assert menu._contract_state(contract)["status"] == "completed"
    assert manager.gold == 85
    assert manager.reputation == 38
    assert manager.player_character.xp == 30


def test_playable_world_location_targets_new_city_state():
    location = LOCATIONS["rattlebridge"]
    assert location["content_state"] == "playable"
    assert location["target_state"] == "rattlebridge_city"
