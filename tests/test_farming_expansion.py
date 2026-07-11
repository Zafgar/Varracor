import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from citys.mucford.farming_expansion import CropPlot, harvesting_level
from citys.mucford.farming_hardening import (
    _absolute_world_minutes,
    _advance_offscreen_growth,
)
from items.tools.bucket import BucketWater
from items.tools.harvest_tools import (
    _HarvestTool,
    CrudeHarvestSickle,
    GuildHarvestScythe,
    IronHarvestSickle,
)
from world_clock import MINUTES_PER_FRAME


class DummyVFX:
    def show_damage(self, *args, **kwargs):
        pass


class DummyClock:
    def __init__(self):
        self.year = 3
        self.day = 1
        self.minutes = 8 * 60.0
        self.weather = "clear"


class DummyManager:
    def __init__(self):
        self.inventory = {}
        self.city_storage = {}
        self.equipment_bag = []
        self.vfx = DummyVFX()
        self.world_clock = DummyClock()


class DummyHarvester:
    def __init__(self, skills, tool):
        self.unlocked_skills = set(skills)
        self.equipment = {"main_hand": tool}
        self.primary_weapon = tool
        self.current_weapon = tool


class DummyFarmingSystem:
    def __init__(self, manager, plots, state):
        self.manager = manager
        self.plots = plots
        self._state = state

    def _state_root(self):
        return self._state


def make_ready_plot(crop):
    state = {"growth_ticks": 0, "watered": False, "harvest_count": 0}
    plot = CropPlot(0, 0, crop, state, "test")
    plot.growth_ticks = plot.data["growth_frames"]
    return plot, state


def test_abstract_harvest_tool_is_not_a_registry_item():
    with pytest.raises(TypeError):
        _HarvestTool()


def test_harvesting_skill_rank_uses_highest_unlocked_rank():
    assert harvesting_level(DummyHarvester([], CrudeHarvestSickle())) == 0
    assert harvesting_level(DummyHarvester(["harvesting_1"], CrudeHarvestSickle())) == 1
    assert harvesting_level(
        DummyHarvester(["harvesting_1", "harvesting_2"], IronHarvestSickle())
    ) == 2
    assert harvesting_level(DummyHarvester(["harvesting_3"], GuildHarvestScythe())) == 3


def test_watering_consumes_water_bucket_and_persists_state():
    manager = DummyManager()
    worker = DummyHarvester(["harvesting_1"], BucketWater())
    state = {"growth_ticks": 0, "watered": False, "harvest_count": 0}
    plot = CropPlot(0, 0, "Carrot", state, "carrot_test")

    assert plot.water(manager, worker, consume_bucket=True)
    assert state["watered"] is True
    assert worker.equipment["main_hand"].name == "Empty Bucket"


def test_crop_requires_matching_skill_and_tool_tier():
    manager = DummyManager()
    plot, _ = make_ready_plot("Cabbage")

    novice = DummyHarvester(["harvesting_1"], CrudeHarvestSickle())
    assert plot.harvest(manager, novice) is False
    assert manager.inventory == {}

    trained = DummyHarvester(["harvesting_1", "harvesting_2"], IronHarvestSickle())
    assert plot.harvest(manager, trained) is True
    assert manager.inventory["Cabbage"] >= 1


def test_master_tool_harvest_resets_and_replants_plot():
    manager = DummyManager()
    plot, state = make_ready_plot("Medicinal Herb")
    master = DummyHarvester(
        ["harvesting_1", "harvesting_2", "harvesting_3"],
        GuildHarvestScythe(),
    )

    assert plot.harvest(manager, master) is True
    assert manager.inventory["Medicinal Herb"] >= 1
    assert plot.growth_ticks == 0
    assert plot.watered is False
    assert state["harvest_count"] == 1


def test_watered_crop_advances_while_player_is_away():
    manager = DummyManager()
    state = {"growth_ticks": 100, "watered": True, "harvest_count": 0}
    plot = CropPlot(0, 0, "Carrot", state, "offscreen_test")
    plot.watered = True
    plot.growth_ticks = 100

    now = _absolute_world_minutes(manager)
    root = {"last_world_minutes": now - MINUTES_PER_FRAME * 50}
    system = DummyFarmingSystem(manager, [plot], root)

    _advance_offscreen_growth(system)

    assert plot.growth_ticks == 150
    assert state["growth_ticks"] == 150
    assert root["last_world_minutes"] == now
