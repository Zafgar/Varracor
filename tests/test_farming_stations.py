import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

# Import order matches the real game and installs all Barracks extensions.
from menus.barracks_menu import BarracksMenu
import citys.mucford.farming_stations as stations
from citys.mucford.farming_stations import (
    REAL_SECONDS_PER_GAME_MINUTE,
    begin_station_recipe,
    begin_station_upgrade,
    job_progress,
    process_station_jobs,
    station_level,
    station_node,
)


class DummyUnit:
    def __init__(self):
        self.max_hp = 100
        self.current_hp = 30
        self.max_mana = 50
        self.current_mana = 20
        self.max_stamina = 80
        self.current_stamina = 25
        self.strength = 5
        self.dexterity = 5
        self.intelligence = 5
        self.defense = 1
        self.injured = True
        self.injury_severity = "Minor"
        self.is_dead = False
        self._farming_meal_effects = {}

    def calculate_final_stats(self):
        self.max_hp = max(1, int(self.max_hp))
        self.max_stamina = max(1, int(self.max_stamina))


class DummyManager:
    def __init__(self):
        self.gold = 1000
        self.inventory = {}
        self.city_storage = {}
        self.equipment_bag = []
        self.npc_state = {"global": {"reputation": 0, "flags": {}}}
        self.player_character = DummyUnit()
        self.my_team = [DummyUnit()]


def finish_time(manager, station_id):
    return float(station_node(manager, station_id)["job"]["finish_at"])


def test_station_defaults_preserve_existing_kitchen_and_herbalist():
    manager = DummyManager()
    assert getattr(BarracksMenu, "_tiered_stations_installed", False)
    assert station_level(manager, "kitchen") == 1
    assert station_level(manager, "herbalist") == 1
    assert station_level(manager, "workbench") == 0
    assert station_level(manager, "infirmary") == 0
    json.dumps(manager.npc_state)


def test_building_workbench_consumes_resources_and_finishes_over_time():
    manager = DummyManager()
    manager.inventory.update({"Rough Timber": 10, "Scrap Iron": 6})
    start = 1000.0

    ok, message = begin_station_upgrade(manager, "workbench", now=start)

    assert ok, message
    assert manager.gold == 900
    assert manager.inventory == {}
    node = station_node(manager, "workbench")
    assert node["job"]["target_level"] == 1
    assert station_level(manager, "workbench") == 0
    assert job_progress(node, now=start) == 0.0

    process_station_jobs(manager, now=finish_time(manager, "workbench") - 0.1)
    assert station_level(manager, "workbench") == 0

    completed = process_station_jobs(manager,
                                     now=finish_time(manager, "workbench") + 0.1)
    assert completed
    assert station_level(manager, "workbench") == 1
    assert station_node(manager, "workbench")["job"] is None


def test_station_recipe_tier_lock_is_enforced():
    manager = DummyManager()
    station_node(manager, "workbench")["level"] = 1
    manager.inventory.update({
        "Iron Ingot": 2,
        "Silver Filigree Wire": 1,
        "Focus Powder": 1,
    })

    ok, message = begin_station_recipe(
        manager, "workbench", "Precision Components", now=100.0)

    assert not ok
    assert "tier 3" in message.lower()
    assert manager.inventory["Iron Ingot"] == 2


def test_workbench_job_places_components_in_city_storage():
    manager = DummyManager()
    station_node(manager, "workbench")["level"] = 1
    manager.inventory.update({"Plant Fiber": 2, "Bitterleaf": 1})

    ok, message = begin_station_recipe(
        manager, "workbench", "Bandage Roll", now=500.0)
    assert ok, message
    end = finish_time(manager, "workbench")
    process_station_jobs(manager, now=end + 0.1)

    assert manager.city_storage["Bandage Roll"] == 2
    assert station_node(manager, "workbench")["completed_jobs"] == 1


def test_herbalist_job_creates_real_equipment_bag_potion():
    manager = DummyManager()
    manager.inventory.update({"Bitterleaf": 2, "Resin": 1})

    ok, message = begin_station_recipe(
        manager, "herbalist", "Bitterleaf Tonic", now=700.0)
    assert ok, message
    end = finish_time(manager, "herbalist")
    process_station_jobs(manager, now=end + 0.1)

    assert len(manager.equipment_bag) == 1
    assert manager.equipment_bag[0].name == "Bitterleaf Tonic"
    assert manager.inventory == {}


def test_kitchen_job_applies_meal_and_persists_battle_buff():
    manager = DummyManager()
    manager.inventory.update({"Potato": 1, "Egg": 1, "Milk": 1})
    before_hp = manager.player_character.current_hp

    ok, message = begin_station_recipe(
        manager, "kitchen", "Farmhand Breakfast", now=900.0)
    assert ok, message
    end = finish_time(manager, "kitchen")
    process_station_jobs(manager, now=end + 0.1)

    farming = manager.npc_state["farming"]
    assert farming["meal_buff"]["name"] == "Farmhand Breakfast"
    assert farming["meal_buff"]["remaining_battles"] == 2
    assert manager.player_character.current_hp > before_hp


def test_recovery_ward_clears_minor_injuries_after_timed_treatment():
    manager = DummyManager()
    station_node(manager, "infirmary")["level"] = 1
    manager.inventory.update({"Bandage Roll": 2, "Bitterleaf": 1})

    ok, message = begin_station_recipe(
        manager, "infirmary", "Dress Wounds", now=1200.0)
    assert ok, message
    end = finish_time(manager, "infirmary")
    process_station_jobs(manager, now=end + 0.1)

    for unit in [manager.player_character] + manager.my_team:
        assert unit.current_hp > 30
        assert unit.injured is False
        assert unit.injury_severity is None


def test_higher_station_tiers_reduce_recipe_duration():
    low = DummyManager()
    high = DummyManager()
    station_node(low, "herbalist")["level"] = 1
    station_node(high, "herbalist")["level"] = 3
    for manager in (low, high):
        manager.inventory.update({"Bitterleaf": 2, "Resin": 1})

    assert begin_station_recipe(low, "herbalist", "Bitterleaf Tonic",
                                now=2000.0)[0]
    assert begin_station_recipe(high, "herbalist", "Bitterleaf Tonic",
                                now=2000.0)[0]

    low_duration = station_node(low, "herbalist")["job"]["duration_seconds"]
    high_duration = station_node(high, "herbalist")["job"]["duration_seconds"]
    assert low_duration == 25 * REAL_SECONDS_PER_GAME_MINUTE
    assert high_duration < low_duration


def test_different_stations_can_work_in_parallel():
    manager = DummyManager()
    manager.inventory.update({
        "Potato": 1,
        "Egg": 1,
        "Milk": 1,
        "Bitterleaf": 2,
        "Resin": 1,
    })

    assert begin_station_recipe(manager, "kitchen", "Farmhand Breakfast",
                                now=3000.0)[0]
    assert begin_station_recipe(manager, "herbalist", "Bitterleaf Tonic",
                                now=3000.0)[0]
    assert station_node(manager, "kitchen")["job"]
    assert station_node(manager, "herbalist")["job"]


def test_failed_completion_refunds_recipe_inputs(monkeypatch):
    manager = DummyManager()
    manager.inventory.update({"Bitterleaf": 2, "Resin": 1})
    assert begin_station_recipe(
        manager, "herbalist", "Bitterleaf Tonic", now=4000.0)[0]
    assert manager.inventory == {}

    def fail_output(*_args, **_kwargs):
        raise RuntimeError("simulated output failure")

    monkeypatch.setattr(stations, "_complete_recipe", fail_output)
    end = finish_time(manager, "herbalist")
    messages = process_station_jobs(manager, now=end + 0.1)

    assert manager.inventory == {"Bitterleaf": 2, "Resin": 1}
    assert station_node(manager, "herbalist")["job"] is None
    assert "refunded" in messages[-1].lower()
