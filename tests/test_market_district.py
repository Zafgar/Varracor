# tests/test_market_district.py
"""
Muckfordin market-alue: fyysiset liikkeet kentällä, E avaa liikkeen oman
kauppasivun, paikkakohtainen maine (per-faktio) vaikuttaa hintoihin ja
ostokset kasvattavat VAIN sen liikkeen faktion mainetta.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from systems.faction_reputation import (
    discount_percent, price_multiplier, shop_price,
)
from citys.mucford.market_data import MARKET_SHOPS


# ---------------------------------------------------------------- hinnoittelu

def test_price_multiplier_curve():
    assert price_multiplier(0) == 1.15, "tuntematon maksaa muukalaislisän"
    assert price_multiplier(30) == 1.00, "tuttu naama maksaa listahinnan"
    assert price_multiplier(70) == 0.80, "kanta-asiakkaan katto"
    assert price_multiplier(500) == 0.80, "alennus ei kasva katon yli"
    assert price_multiplier(-50) == 1.15, "lisä ei kasva rajatta"


def test_shop_price_rounds_and_floors_at_one():
    assert shop_price(100, 0) == 115
    assert shop_price(100, 70) == 80
    assert shop_price(1, 70) == 1, "hinta ei putoa alle yhden"
    assert discount_percent(0) == 15
    assert discount_percent(70) == -20


# ---------------------------------------------------------------- kauppadata

def test_all_market_goods_resolve():
    """Jokainen kaupattava item löytyy rekisteristä - ei 'out of stock'."""
    from items.item_registry import create_item
    kinds = set()
    for shop in MARKET_SHOPS.values():
        kinds.add(shop["kind"])
        assert shop["faction"], "liikkeellä oltava maine-faktio"
        for entry in shop["goods"]:
            assert entry["price"] >= 1
            if entry["kind"] == "item":
                item = create_item(entry.get("class", entry["name"]))
                assert item is not None, f"{shop['name']}: {entry['name']} puuttuu"
    # Eri liiketyypit katettu (vihannes/ase/panssari/juoma/sekatavara)
    assert kinds == {"produce", "weapons", "armor", "potions", "general"}


def test_shops_have_distinct_reputations():
    """Maine on paikkakohtainen: eri liikkeillä eri faktiot (sepät jakavat)."""
    factions = [s["faction"] for s in MARKET_SHOPS.values()]
    assert len(set(factions)) >= 4


# ---------------------------------------------------------------- ostovirta

def _manager():
    import main  # noqa: F401  (rekisteröi integraatiot)
    from game_manager import GameManager
    return GameManager()


def test_buy_item_and_material_flow():
    m = _manager()
    m.gold = 500
    m.pending_shop_id = "greenmarket"
    from menus.district_shop_menu import DistrictShopMenu
    menu = DistrictShopMenu(m)
    apple = menu.shop["goods"][0]
    price = menu._final_price(apple)
    assert price == 5, "Apple 4 GP + 15% muukalaislisä = 5"
    assert menu._buy(apple) is True
    assert m.gold == 495
    assert m.inventory.get("Apple", 0) >= 1
    assert m.get_faction_rep("muckford_growers") == 1, "ostos kasvattaa mainetta"
    assert m.get_faction_rep("muckford_smiths") == 0, "muut faktiot eivät liiku"

    # Item-ostos menee equipment_bagiin
    m.pending_shop_id = "scrap_arms"
    menu2 = DistrictShopMenu(m)
    blade = menu2.shop["goods"][0]
    bag_before = len(m.equipment_bag)
    assert menu2._buy(blade) is True
    assert len(m.equipment_bag) == bag_before + 1


def test_buy_without_gold_fails():
    m = _manager()
    m.gold = 0
    m.pending_shop_id = "scrap_arms"
    from menus.district_shop_menu import DistrictShopMenu
    menu = DistrictShopMenu(m)
    assert menu._buy(menu.shop["goods"][0]) is False
    assert m.gold == 0
    assert m.get_faction_rep("muckford_smiths") == 0, "ei mainetta ilman kauppaa"


def test_reputation_lowers_price_in_that_shop_only():
    m = _manager()
    m.modify_faction_rep("muckford_brewers", 70)
    m.pending_shop_id = "bittersip"
    from menus.district_shop_menu import DistrictShopMenu
    menu = DistrictShopMenu(m)
    potion = menu.shop["goods"][0]  # Weak Health Potion 30
    assert menu._final_price(potion) == 24, "kanta-asiakas -20%"
    # Sama tavara ilman mainetta toisessa liikkeessä maksaisi lisän kanssa
    m.pending_shop_id = "greenmarket"
    other = DistrictShopMenu(m)
    assert other._final_price(other.shop["goods"][0]) == 5


# ---------------------------------------------------------------- kaupunki

def test_city_has_market_row_and_e_opens_shop():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    assert len(city.market_stalls) == len(MARKET_SHOPS)
    ids = [s.shop_id for s in city.market_stalls]
    assert ids == list(MARKET_SHOPS), "kaikki liikkeet rivissä"
    for stall in city.market_stalls:
        assert stall in city.arena.props, "koju piirto- ja interaktioputkessa"

    # Kävele kojulle ja paina E -> liikkeen kauppasivu
    stall = city.market_stalls[2]  # mudguard_armory
    city.player.rect.centerx = stall.rect.centerx
    city.player.rect.bottom = stall.rect.bottom + 30
    city.next_state = None
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.next_state == "district_shop"
    assert m.pending_shop_id == "mudguard_armory"


def test_district_shop_state_registered():
    """Tila on datavetoisessa tilakoneessa (factory + recreate joka kerta,
    jotta sivu rakentuu aina oikealle liikkeelle)."""
    import inspect
    import main
    src = inspect.getsource(main.main)
    assert '"district_shop": DistrictShopMenu' in src
    recreate_block = src[src.index("RECREATE_ALWAYS"):]
    recreate_block = recreate_block[:recreate_block.index("}")]
    assert '"district_shop"' in recreate_block


def test_shop_menu_draws_and_leaves_to_city():
    m = _manager()
    m.pending_shop_id = "oddments"
    from menus.district_shop_menu import DistrictShopMenu
    menu = DistrictShopMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.update()
    menu.draw(surf)
    assert len(menu.row_rects) == len(menu.shop["goods"])
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert menu.next_state == "muckford_city"
