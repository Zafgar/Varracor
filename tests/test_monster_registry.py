# tests/test_monster_registry.py
"""Keskitetyn monster-rekisterin vartiotestit.

KRIITTINEN ominaisuus: jokainen pelin monster on luotava rekisterin kautta
ja sen on toimittava MILLÄ TAHANSA kartalla - paljas GameManager ilman
areenaa/karttaa riittää (Vortex-repeämät, kryptan aallot, aluespawnit ja
questit käyttävät kaikki samaa polkua).
"""
import pytest

from ai.base_ai import BaseAI
from settings import ENEMY_TEAM
from units import monster_registry as reg


ALL_NAMES = reg.monster_names()


def test_registry_is_not_empty_and_has_all_areas():
    # Vähintään: 10 tier0 + 6 kaivos + 4 ford + 4 toll + 4 chapel + boss +
    # klassikot + undead + suo + rattlebridge
    assert len(ALL_NAMES) >= 40
    for expected in (
        "Mud Mite", "Whisper Moth",              # tier 0
        "Grave Pickman", "Deep Cave Broodmother", # kaivos
        "Captain Garran Vale",                    # ford
        "Tollmaster Hadrik Crowl",                # toll
        "Bell Wraith",                            # chapel
        "Whisper Pool Maw",                       # pool
        "Giant Rat", "Rat King", "Forest Troll",  # klassikot
        "Skeleton", "Zombie", "Skeleton Archer",  # undead
        "Bog Leech", "Giant Frog", "Corrupted Crow",
        "Hush-Mantle", "Red Lantern Cadaver",     # rattlebridge
    ):
        assert reg.monster_info(expected) is not None, expected


def test_aliases_resolve():
    assert reg.monster_info("Troll").name == "Forest Troll"
    assert reg.monster_info("Broodmother").name == "Cave Broodmother"
    assert reg.monster_info("Archer").name == "Skeleton Archer"
    assert reg.monster_info("hush mantle").name == "Hush-Mantle"
    assert reg.monster_info("Olematon Otus") is None


@pytest.mark.parametrize("name", ALL_NAMES)
def test_every_monster_spawns_and_runs_anywhere(manager, name):
    """Map-riippumattomuus: monster syntyy ja toimii paljaalla managerilla.

    Ei areenaa, ei karttaa, ei spawn-järjestelmää - luonti + yksi
    AI-frame + update eivät saa kaatua, kontrollerin on oltava BaseAI ja
    kuvan on oltava koodipiirretty placeholder (ei tyhjä)."""
    manager.match_in_progress = True
    manager.current_arena = None

    unit = reg.create_monster(name, 300, 300, ENEMY_TEAM)
    assert unit.team_color == ENEMY_TEAM
    assert not unit.is_dead
    assert unit.max_hp > 0 and unit.current_hp > 0
    assert unit.walk_speed > 0, f"{name}: walk_speed puuttuu"

    # Yksi AI-kehys kaikille
    assert isinstance(unit.ai_controller, BaseAI), (
        f"{name}: {type(unit.ai_controller).__name__} ei peri BaseAI:ta"
    )

    # Placeholder-grafiikka olemassa ilman asseteja
    assert unit.image is not None
    assert unit.image.get_width() > 0 and unit.image.get_height() > 0

    # Toimii ilman karttaa: muutama frame AI:ta ja updatea
    manager.enemy_team.add(unit)
    manager.all_units.add(unit)
    for _ in range(5):
        unit.run_combat_ai(manager.all_units, None, manager=manager)
        unit.update(None, manager=manager)


def test_mission_data_enemy_names_resolve():
    """Kaikkien missioiden vihollisnimet löytyvät rekisteristä (tai ovat
    humanoideja) - ei enää hiljaisia Goblin-korvikkeita."""
    from mission_data import MONSTER_HUNTS, BOSS_HUNTS

    humanoids = {"Bandit", "Goblin"}
    missing = []
    for hunt in BOSS_HUNTS.values():
        for enemy_name, _qty in hunt.get("enemies", []):
            if enemy_name not in humanoids and reg.monster_info(enemy_name) is None:
                missing.append((hunt["id"], enemy_name))
    for hunts in MONSTER_HUNTS.values():
        for hunt in hunts:
            for enemy_name, _qty in hunt.get("enemies", []):
                if enemy_name not in humanoids and reg.monster_info(enemy_name) is None:
                    missing.append((hunt["id"], enemy_name))
    assert not missing, f"Mission-viholliset puuttuvat rekisteristä: {missing}"


def test_rift_themes_resolve_through_registry():
    """Vortex-repeämäteemojen kaikki aallot ja bossit tulevat rekisteristä."""
    from menus.rift_site_menu import THEMES, _unit_class

    for theme in THEMES.values():
        for wave in theme["waves"]:
            for cls_name, _count in wave:
                assert _unit_class(cls_name) is not None
        boss_cls, _boss_name = theme["boss"]
        assert _unit_class(boss_cls) is not None


def test_ecology_species_resolve_through_registry():
    """Aluespawn-ekologian lajit ovat rekisterin lajeja."""
    from systems.tier0_monster_ecology import TIER0_ECOLOGY

    for entry in TIER0_ECOLOGY:
        info = reg.monster_info(entry.species)
        assert info is not None, entry.species
        assert info.level == entry.level, (
            f"{entry.species}: rekisterin taso {info.level} != "
            f"ekologian taso {entry.level}"
        )


def test_roles_and_levels_sane():
    valid_roles = {"swarm", "skirmisher", "ambusher", "pouncer", "ranged",
                   "support", "tank", "shock", "boss"}
    for info in reg.MONSTERS:
        assert info.role in valid_roles, f"{info.name}: outo rooli {info.role}"
        assert 1 <= info.level <= 10, f"{info.name}: outo taso {info.level}"
    # Jokaiselle roolille löytyy vähintään yksi edustaja
    for role in valid_roles:
        assert reg.monsters_by_role(role), f"rooli {role} tyhjä"


def test_create_enemy_by_name_uses_registry(manager):
    """GameManagerin vihollistehdas luo rekisterimonsterit oikein."""
    rat = manager.create_enemy_by_name("Giant Rat")
    assert type(rat).__name__ == "GiantRat"
    troll = manager.create_enemy_by_name("Forest Troll")
    assert type(troll).__name__ == "Troll"
    king = manager.create_enemy_by_name("Rat King")
    assert type(king).__name__ == "RatKing"
    assert king.team_color == ENEMY_TEAM
