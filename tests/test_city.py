# tests/test_city.py
"""
Muckfordin kaupunkisimulaation testit: villagerit tekevät töitä,
eläimet elävät, eikä mikään kaadu. Yksi jaettu 2 minuutin simulaatio
(module-scoped fixture), jota vasten kaikki tarkistukset ajetaan.
"""
import pytest


@pytest.fixture(scope="module")
def simulated_city():
    """Aja kaupunkia 2 min pelimaailmaa ja palauta lopputila."""
    from game_manager import GameManager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    manager = GameManager()
    city = MuckfordCityMenu(manager)
    for _ in range(7200):
        city.update()
    return manager, city


def test_city_boots_with_npcs_and_animals(simulated_city):
    _, city = simulated_city
    assert len(city.npcs) > 0, "kaupungissa ei ole villagereita"
    assert len(city.animals) > 0, "kaupungissa ei ole elaimia"


def test_manure_stays_bounded(simulated_city):
    from assets.tiles.farm_objects import Manure
    _, city = simulated_city
    manure = sum(1 for p in city.arena.props if isinstance(p, Manure))
    assert manure <= 30, f"lantaa liikaa: {manure}"


def test_villagers_work(simulated_city):
    _, city = simulated_city
    working = sum(1 for n in city.npcs
                  if getattr(getattr(n, "ai_controller", None), "state", 0) == 1)
    assert working > 0, "yksikaan villager ei ole toissa"


def test_villagers_produce_to_city_storage(simulated_city):
    manager, _ = simulated_city
    total = sum(manager.city_storage.values())
    assert total > 0, f"varastoon ei kertynyt mitaan: {manager.city_storage}"


def test_cows_survive_peacetime(simulated_city):
    from units.farm_animals import Cow
    _, city = simulated_city
    cows = [a for a in city.animals if isinstance(a, Cow)]
    assert cows and all(not c.is_dead for c in cows), "lehmia kuoli rauhan aikana"


def test_chicken_hatch_respects_population_cap(manager):
    """Deterministinen kattotesti: 12 kanan jälkeen munat eivät kuoriudu."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from units.farm_animals import Chicken
    from assets.tiles.farm_objects import Egg
    from settings import GREEN

    city = MuckfordCityMenu(manager)
    # Täytä populaatio kattoon
    while sum(1 for a in city.animals if isinstance(a, Chicken)) < 12:
        city.animals.append(Chicken(500, 500, team_color=GREEN))

    egg = Egg(510, 510)
    egg.hatch_timer = 1
    city.arena.props.append(egg)
    before = sum(1 for a in city.animals if isinstance(a, Chicken))

    for _ in range(5):
        city._update_eggs()

    after = sum(1 for a in city.animals if isinstance(a, Chicken))
    assert after == before, "muna kuoriutui vaikka populaatiokatto oli taynna"
    assert egg not in city.arena.props, "muna ei poistunut"
