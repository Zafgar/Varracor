# tests/test_monster_ai_unification.py
"""Vartiotestit: YKSI tekoälykehys ajaa kaikkia yksiköitä.

Pelissä oli aiemmin rinnakkaisia AI-toteutuksia (RatAI, UndeadAI), jotka
kirjoittivat oman chase/liikelogiikkansa ja ohittivat BaseAI:n parannukset
(anti-kite, kiertoliike, reitinhaku). Nämä testit estävät regressioita:
jokaisen ai/-moduulin AI-luokan on perittävä BaseAI, ja jokaisen
monsterin ai_controllerin on oltava BaseAI-instanssi.
"""
import importlib
import inspect
import pathlib
import sys

import pytest

from ai.base_ai import BaseAI
from settings import ENEMY_TEAM

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _ai_modules():
    for path in sorted((ROOT / "ai").glob("*.py")):
        if path.name.startswith("__") or path.name == "pathfinding.py":
            continue
        yield f"ai.{path.stem}"


def test_every_ai_class_subclasses_base_ai():
    """Jokainen execute_ai-metodin omaava luokka ai/-paketissa perii BaseAI:n."""
    offenders = []
    for modname in _ai_modules():
        module = importlib.import_module(modname)
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != modname:
                continue
            if not hasattr(cls, "execute_ai"):
                continue
            if not issubclass(cls, BaseAI):
                offenders.append(f"{modname}.{name}")
    assert not offenders, (
        "Rinnakkaisia AI-toteutuksia (eivät peri BaseAI:ta): "
        f"{offenders}"
    )


def test_no_dead_parallel_ai_files():
    """Kuolleet rinnakkaisjärjestelmät eivät saa palata repoon."""
    assert not (ROOT / "units" / "monsters").exists(), (
        "units/monsters/ oli kuollut duplikaatti units/rat.py:stä"
    )
    assert not (ROOT / "ai" / "city_ai.py").exists(), (
        "ai/city_ai.py oli tyhjä kuollut tiedosto"
    )


def _monster_units():
    """Edustava otos eri AI-luokkia käyttävistä monstereista."""
    from units.undead_skeleton import UndeadSkeleton
    from units.undead_zombie import UndeadZombie
    from units.undead_skeleton_archer import UndeadSkeletonArcher
    from units.rat_rider import RatRider
    from units.rat import GiantRat
    from units.tier0_monsters import TIER0_MONSTER_CLASSES

    units = [
        UndeadSkeleton("Skeleton", 100, 100, ENEMY_TEAM),
        UndeadZombie("Zombie", 100, 100, ENEMY_TEAM),
        UndeadSkeletonArcher("Archer", 100, 100, ENEMY_TEAM),
        RatRider("Rat Rider", 100, 100, ENEMY_TEAM),
        GiantRat("Giant Rat", 100, 100, ENEMY_TEAM),
    ]
    for cls in TIER0_MONSTER_CLASSES:
        units.append(cls(cls.SPECIES, 100, 100, ENEMY_TEAM))
    return units


def test_all_monster_controllers_are_base_ai(manager):
    for unit in _monster_units():
        assert isinstance(unit.ai_controller, BaseAI), (
            f"{unit.name}: ai_controller {type(unit.ai_controller).__name__} "
            "ei ole BaseAI-instanssi"
        )


def test_undead_never_retreat_and_never_dash():
    from units.undead_zombie import UndeadZombie
    zombie = UndeadZombie("Zombie", 100, 100, ENEMY_TEAM)
    assert zombie.ai_controller.no_retreat is True
    assert zombie.ai_controller.allow_dash is False


def test_undead_chase_closes_distance(manager):
    """Zombie lähestyy kohdetta yhteisellä kehyksellä (ei jää tapiksi)."""
    from units.undead_zombie import UndeadZombie
    from units.human import Human
    from settings import PLAYER_TEAM

    zombie = UndeadZombie("Zombie", 100, 100, ENEMY_TEAM)
    target = Human("Target", 500, 100, PLAYER_TEAM, "Common")
    manager.my_team.add(target)
    manager.enemy_team.add(zombie)
    manager.all_units.add(target, zombie)

    start = zombie.rect.centerx
    for _ in range(120):
        zombie.run_combat_ai(manager.all_units, None, manager=manager)
        zombie.update(None, manager=manager)
    assert zombie.rect.centerx > start + 50, (
        "Zombie ei lähestynyt kohdetta BaseAI-kehyksellä"
    )


def test_rat_rider_charge_sequence_still_works(manager):
    """Riderin rynnäkkö (charge_phase) toimii BaseAI-pohjaisella RatAI:lla."""
    from units.rat_rider import RatRider
    from units.human import Human
    from settings import PLAYER_TEAM

    rider = RatRider("Rat Rider", 100, 100, ENEMY_TEAM)
    target = Human("Target", 500, 100, PLAYER_TEAM, "Common")
    manager.my_team.add(target)
    manager.enemy_team.add(rider)
    manager.all_units.add(target, rider)

    rider.charge_cooldown = 0
    rider.ai_controller.current_target = target
    saw_windup = False
    for _ in range(240):
        rider.run_combat_ai(manager.all_units, None, manager=manager)
        rider.update(None, manager=manager)
        if rider.charge_phase == 1:
            saw_windup = True
        if saw_windup and rider.charge_phase in (0, 2, 3):
            break
    assert saw_windup, "Rider ei koskaan aloittanut rynnäkköä (start_charge)"
