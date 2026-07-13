# tests/test_water_fishing.py
"""
Vesi ja kalastus: koodipiirretty lampi (pohja + animoidut kerrokset),
kulkuesteet laiturikaistaa lukuunottamatta, kalastussession tilakone,
Angler-taitojen vaikutus ja kalojen talousintegraatio.
"""
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from systems import fishing as fs


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


# ---------------------------------------------------------------- vesi

def test_water_body_builds_and_animates():
    from assets.tiles.water import WaterBody
    water = WaterBody(100, 100, 400, 260, seed=3)
    assert water.base.get_size() == (400, 260)
    surf = pygame.Surface((800, 600))
    for _ in range(10):
        water.update()
        water.draw(surf, (0, 0))
    water.splash(200, 200)
    assert len(water.ripples) >= 1, "roiske synnyttää väreilyrenkaan"
    # Ruudun ulkopuolella piirto ei kaadu (näkyvyysrajaus)
    water.draw(surf, (5000, 5000))


def test_pond_carved_with_walkable_jetty():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    arena = city.arena
    assert hasattr(arena, "fishing_pond") and hasattr(arena, "fishing_spot")
    blockers = [o for o in arena.obstacles if getattr(o, "is_water", False)]
    assert len(blockers) == 3
    # Laiturin keskikohta kulkukelpoinen, syvä vesi ei
    jc = arena.fishing_jetty.center
    assert not any(b.rect.collidepoint(jc) for b in blockers)
    deep = (arena.fishing_pond.centerx, arena.fishing_pond.top + 15)
    assert any(b.rect.collidepoint(deep) for b in blockers)
    # Lammen alle ei jäänyt puita/esteitä
    for prop in arena.props:
        assert not arena.fishing_pond.contains(prop.rect), \
            f"{type(prop).__name__} jäi lammen alle"


# ---------------------------------------------------------------- sessio

def test_fishing_session_state_machine():
    s = fs.FishingSession(skill=0, rng=random.Random(1))
    assert s.state == "WAITING"
    # Liian aikainen isku säikäyttää (ei saalista, odotus alkaa alusta)
    assert s.hook() is None
    # Kelaa nykäisyyn
    s.timer = 1
    assert s.update() == "bite"
    assert s.state == "BITE"
    fish = s.hook()
    assert fish is not None and fish["name"] in \
        {f["name"] for f in fs.FISH_SPECIES}
    assert s.state == "WAITING", "saaliin jälkeen uusi heitto"
    # Ikkunan ohitus -> escaped
    s.timer = 1
    s.update()
    s.timer = 1
    assert s.update() == "escaped"


def test_angler_skill_speeds_waits_and_extends_window():
    slow = fs.FishingSession(skill=0, rng=random.Random(9))
    fast = fs.FishingSession(skill=2, rng=random.Random(9))
    assert fast.timer < slow.timer, "Angler lyhentää odotusta"
    slow.timer = 1
    fast.timer = 1
    slow.update()
    fast.update()
    assert fast.timer > slow.timer, "Angler pidentää tartuntaikkunaa"


def test_angler_skill_improves_rare_catch():
    rng = random.Random(42)
    base = sum(1 for _ in range(3000)
               if fs.roll_fish(rng, 0)["name"] in ("Whisker Catfish", "Marsh Pike"))
    rng = random.Random(42)
    skilled = sum(1 for _ in range(3000)
                  if fs.roll_fish(rng, 2)["name"] in ("Whisker Catfish", "Marsh Pike"))
    assert skilled > base * 1.2, "harvinaiset yleistyvät taidolla"


# ---------------------------------------------------------------- kaupunki

def test_city_fishing_flow_catch_to_inventory():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from items.item_registry import create_item
    city = MuckfordCityMenu(m)
    city.on_enter()
    spot = city.arena.fishing_spot
    city.player.rect.center = (spot[0] - 60, spot[1])

    # Ilman vapaa E ei aloita
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.fishing_session is None

    rod = create_item("FishingRod")
    assert rod is not None and rod.tool_type == "fishing"
    m.equipment_bag.append(rod)
    assert fs.has_rod(m) is True

    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.fishing_session is not None
    city.fishing_session.rng = random.Random(5)
    city.fishing_session.timer = 1
    city.update()
    assert city.fishing_session.state == "BITE"
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    fish_names = {f["name"] for f in fs.FISH_SPECIES}
    caught = [k for k in m.inventory if k in fish_names]
    assert caught, "saalis päätyi reppuun"

    # Piirto kesken session (koho + siima) ei kaadu
    surf = pygame.Surface((1920, 1080))
    city._update_camera()
    city.draw(surf)


def test_fish_economy_and_recipe():
    from lore.world_data import MARKET_PRICES
    for f in fs.FISH_SPECIES:
        assert MARKET_PRICES["sell"].get(f["name"]) == f["price"], \
            f"{f['name']} puuttuu myyntihinnoista"
    assert "Fishing Rod" in MARKET_PRICES["buy"]
    from citys.mucford.market_data import MARKET_SHOPS
    odd = [g["name"] for g in MARKET_SHOPS["oddments"]["goods"]]
    assert "Fishing Rod" in odd, "vapa myynnissä Kradilla"
    from citys.mucford.farming_expansion import MEAL_RECIPES
    assert "Mudwater Fish Stew" in MEAL_RECIPES
    assert "Mudfin" in MEAL_RECIPES["Mudwater Fish Stew"]["ingredients"]


def test_fishing_skill_nodes_in_commander_tree():
    from skills.commander_skills_data import COMMANDER_SKILL_TREE
    assert "fishing_1" in COMMANDER_SKILL_TREE
    assert COMMANDER_SKILL_TREE["fishing_2"]["requires"] == ["fishing_1"]
    m = _manager()
    hero = m.player_character
    hero.unlocked_skills.update({"husbandry_1", "fishing_1", "fishing_2"})
    hero.calculate_final_stats()
    assert hero.fishing == 2
