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


def test_farm_has_storage_and_manure_pile(simulated_city):
    """Regressio: nämä puuttuivat kartalta, jolloin lantaquest oli
    mahdoton suorittaa (ei paikkaa mihin dumpata)."""
    from assets.tiles.farm_objects import FarmStorage, ManurePile
    _, city = simulated_city
    assert any(isinstance(p, FarmStorage) for p in city.arena.props)
    assert any(isinstance(p, ManurePile) for p in city.arena.props)


def test_manure_quest_dump(manager):
    """Lantaquest etenee ja valmistuu kun lanta dumpataan kompostiin."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.farm_objects import ManurePile
    from quest_system import quest_manager

    city = MuckfordCityMenu(manager)
    q = quest_manager.get_quest("quest_manure_cleanup")
    quest_manager.accept_quest("quest_manure_cleanup")
    manager.inventory["Manure"] = 5

    pile = next(p for p in city.arena.props if isinstance(p, ManurePile))
    assert city._try_interact_prop(pile, check_collision=False)
    assert q.progress == 5
    assert q.status == "completed"


def test_eggs_stay_bounded(manager):
    """Munien määrä kartalla ei kasva rajatta (katto 20)."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.farm_objects import Egg
    from units.farm_animals import Chicken

    city = MuckfordCityMenu(manager)
    chickens = [a for a in city.animals if isinstance(a, Chicken)]
    for _ in range(40):
        for c in chickens:
            c.ai_controller.egg_timer = 0
            c.ai_controller._lay_egg(manager)
    eggs = sum(1 for p in city.arena.props if isinstance(p, Egg))
    assert eggs <= 20, f"munia kartalla {eggs} (katto 20)"


def test_arena_gate_and_bram(manager):
    """Shanty Yard -portti ja Bram ovat kaupungissa; E portilla avaa liigan."""
    import pygame
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.muckford_objects import ShantyYardGate

    city = MuckfordCityMenu(manager)
    gate = next((p for p in city.arena.props if isinstance(p, ShantyYardGate)), None)
    assert gate is not None, "Shanty Yard -portti puuttuu kartalta"
    assert getattr(city, "bram", None) is not None, "Bram puuttuu"

    city.player.rect.center = (gate.rect.centerx, gate.rect.bottom + 40)
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.next_state == "league"


def test_poi_icons(manager):
    """POI-ikonit kattavat questin, kaupan, liigan, tavernan ja sepän."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(manager)
    kinds = {k for _, _, k in city._poi_icon_list()}
    assert "trade" in kinds       # Hamo
    assert "league" in kinds      # Bram + portti
    assert "tavern" in kinds
    assert "smith" in kinds
    assert any(k.startswith("quest") for k in kinds)  # Farmer Gus


def test_barracks_in_city_and_enter(manager):
    """Team Barracks on kartalla ja E avaa tiimitilan."""
    import pygame
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.muckford_objects import TeamBarracks

    city = MuckfordCityMenu(manager)
    barr = next((p for p in city.arena.props if isinstance(p, TeamBarracks)), None)
    assert barr is not None, "Barracks puuttuu kartalta"
    assert getattr(city, "barracks", None) is barr

    city.player.rect.center = (barr.rect.centerx, barr.rect.bottom + 40)
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.next_state == "barracks"


def test_barracks_menu_roster_and_equip(manager):
    """Barracks-menu näyttää roosterin ja ohjaa varusteisiin."""
    import pygame
    from menus.barracks_menu import BarracksMenu

    manager.recruit_initial_hero()
    bm = BarracksMenu(manager)
    roster = bm._roster()
    assert manager.player_character in roster
    assert len(roster) >= 2  # commander + hero

    # Equipment-nappi -> guild + return state (draw asettaa _last_draw_rect)
    import pygame as pg
    surf = pg.Surface((1920, 1080))
    bm.draw(surf)
    pos = bm.btn_equip._last_draw_rect.center
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
    bm.handle_event(ev)
    assert bm.next_state == "guild"
    assert manager.guild_return_state == "barracks"
