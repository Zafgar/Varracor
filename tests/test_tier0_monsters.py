import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from settings import ENEMY_TEAM, PLAYER_TEAM
from systems.muckford_opening_integration import install_muckford_opening_integration

install_muckford_opening_integration()

from citys.mucford.forest_excursion import WhisperMarshArena
from loot_data import LOOT_DROPS
from systems.tier0_monster_ecology import (
    TIER0_ECOLOGY,
    TIER0_LOOT_DROPS,
    build_whisper_marsh_population,
)
from units.human import Human
from units.tier0_monsters import (
    BogTick,
    FenStalker,
    MarshbackBrute,
    MireLurkerSpawn,
    MudMite,
    ReedSkitter,
    RotcapShambler,
    SporeToad,
    TIER0_MONSTER_CLASSES,
    WhisperMoth,
)


class DummyVFX:
    def __init__(self):
        self.floor_particles = pygame.sprite.Group()

    def show_damage(self, *_args, **_kwargs):
        pass

    def create_impact_sparks(self, *_args, **_kwargs):
        pass


class DummyArena:
    width = 1600
    height = 1000
    obstacles = []


class CombatManager:
    def __init__(self, units=()):
        self.vfx = DummyVFX()
        self.current_arena = DummyArena()
        self.all_units = pygame.sprite.Group(*units)
        self.player_character = None


class OutskirtsManager:
    def __init__(self):
        self.npc_state = {"global": {"flags": {}, "deeds": []}}
        self.inventory = {}


def make_target(x=260, y=200):
    target = Human("Training Target", x, y, PLAYER_TEAM, "Common")
    target.ai_controller = None
    target.max_hp = 2000
    target.current_hp = target.max_hp
    target.max_stamina = 500
    target.current_stamina = 500
    return target


def test_catalog_has_two_distinct_monsters_at_every_level_1_to_5():
    assert len(TIER0_MONSTER_CLASSES) == 10
    levels = [monster_class.THREAT_LEVEL for monster_class in TIER0_MONSTER_CLASSES]
    assert {level: levels.count(level) for level in range(1, 6)} == {
        1: 2,
        2: 2,
        3: 2,
        4: 2,
        5: 2,
    }
    assert len({entry.species for entry in TIER0_ECOLOGY}) == 10


def test_every_monster_has_generated_animation_frames_and_readable_art():
    for index, monster_class in enumerate(TIER0_MONSTER_CLASSES):
        monster = monster_class(monster_class.SPECIES, 100 + index * 5, 100, ENEMY_TEAM)
        assert monster.level == monster_class.THREAT_LEVEL
        assert monster.ai_controller is not None
        assert set(monster._generated_frames) == {"idle", "run", "attack", "hurt", "dead"}
        assert len(monster._generated_frames["idle"]) == 2
        assert len(monster._generated_frames["run"]) == 2
        assert len(monster._generated_frames["attack"]) == 2
        for frames in monster._generated_frames.values():
            for frame in frames:
                assert frame.get_bounding_rect().width > 10
                assert frame.get_bounding_rect().height > 8


def test_every_monster_can_damage_a_target_and_apply_species_effects():
    for monster_class in TIER0_MONSTER_CLASSES:
        monster = monster_class(monster_class.SPECIES, 200, 200, ENEMY_TEAM)
        target_x = 200 + min(100, max(20, monster.attack_range - 8))
        target = make_target(target_x, 200)
        manager = CombatManager((monster, target))
        manager.player_character = target
        hp_before = target.current_hp
        stamina_before = target.current_stamina

        assert monster.perform_attack(target, manager=manager)
        assert target.current_hp < hp_before
        if monster.STATUS_EFFECT:
            assert target.has_status(monster.STATUS_EFFECT[0])
        if monster.STAMINA_DRAIN:
            assert target.current_stamina < stamina_before


def test_special_ai_behaviours_trigger_without_full_battle_loop():
    random.seed(4)

    target = make_target(360, 220)
    pouncer = MireLurkerSpawn("Pouncer", 150, 220, ENEMY_TEAM)
    pouncer.ai_controller.pounce_cooldown = 0
    manager = CombatManager((pouncer, target))
    pouncer.run_combat_ai(manager.all_units, [], manager)
    assert pouncer.is_dashing
    assert pouncer.dash_damage > 0

    target = make_target(410, 220)
    brute = MarshbackBrute("Brute", 150, 220, ENEMY_TEAM)
    brute.ai_controller.charge_cooldown = 0
    manager = CombatManager((brute, target))
    brute.run_combat_ai(manager.all_units, [], manager)
    assert brute.is_dashing
    assert brute.dash_damage >= 10

    target = make_target(270, 220)
    stalker = FenStalker("Stalker", 150, 220, ENEMY_TEAM)
    manager = CombatManager((stalker, target))
    stalker.run_combat_ai(manager.all_units, [], manager)
    assert not stalker.ai_controller.hidden
    assert stalker.ambush_ready

    target = make_target(220, 220)
    shambler = RotcapShambler("Shambler", 150, 220, ENEMY_TEAM)
    shambler.ai_controller.pulse_cooldown = 0
    manager = CombatManager((shambler, target))
    shambler.run_combat_ai(manager.all_units, [], manager)
    assert target.has_status("Poison")
    assert target.has_status("Slow")

    target = make_target(205, 220)
    moth = WhisperMoth("Moth", 150, 220, ENEMY_TEAM)
    moth.ai_controller.kite_cooldown = 0
    manager = CombatManager((moth, target))
    moth.run_combat_ai(manager.all_units, [], manager)
    assert moth.is_dashing

    target = make_target(230, 220)
    mite = MudMite("Mite A", 150, 220, ENEMY_TEAM)
    ally = MudMite("Mite B", 175, 235, ENEMY_TEAM)
    manager = CombatManager((mite, ally, target))
    mite.run_combat_ai(manager.all_units, [], manager)
    assert mite.temp_speed_mult > 1.0


def test_local_aggro_keeps_deep_monsters_from_crossing_whole_map():
    brute = MarshbackBrute("Distant Brute", 100, 100, ENEMY_TEAM)
    target = make_target(1200, 800)
    manager = CombatManager((brute, target))
    start = brute.rect.center
    for _ in range(90):
        brute.run_combat_ai(manager.all_units, [], manager)
        brute.update([], manager)
    assert brute.ai_controller.current_target is None
    assert brute.rect.center == start
    assert target.current_hp == target.max_hp


def test_loot_registry_contains_every_new_species():
    assert set(TIER0_LOOT_DROPS).issubset(LOOT_DROPS)
    for monster_class in TIER0_MONSTER_CLASSES:
        drops = LOOT_DROPS[monster_class.SPECIES]
        assert drops
        assert all(0 < float(drop["chance"]) <= 1 for drop in drops)


def test_whisper_marsh_population_uses_low_and_deep_difficulty_bands():
    manager = OutskirtsManager()
    arena = WhisperMarshArena(manager)
    population = build_whisper_marsh_population(
        arena,
        random.Random(9917),
        ENEMY_TEAM,
        visits=4,
        camp_stage=2,
    )
    levels = [monster.level for monster in population]
    assert len(population) >= 10
    assert min(levels) <= 2
    assert max(levels) == 5
    assert all(monster.ai_controller is not None for monster in population)
    assert all(not arena._is_water(monster.rect.center, inset=0) for monster in population)
