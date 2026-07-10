# tests/test_world_systems.py
"""Maailmankellon, sään, markkinoiden, velan ja raidien pikatestit."""
import pygame
import pytest


def test_clock_date_and_night():
    from world_clock import WorldClock
    c = WorldClock()
    assert c.get_date_string() == "Day 1 of Thaw, Year 3 A.V."
    assert c.hour == 8 and not c.is_night

    c.minutes = 23 * 60
    assert c.is_night and c.night_alpha() > 100

    c.minutes = 12 * 60
    assert c.night_alpha() == 0

    # Päivän vaihtuminen ja vuodenajat
    c.minutes = 1439.999
    c.update()
    assert c.day == 2
    c.day = 29
    assert c.season == "Sun"
    c.day = 112
    c.advance_day()
    assert c.day == 1 and c.year == 4


def test_clock_save_roundtrip():
    from world_clock import WorldClock
    c = WorldClock()
    c.day = 42; c.year = 3; c.minutes = 1000; c.weather = "rain"
    c2 = WorldClock()
    c2.from_dict(c.to_dict())
    assert (c2.day, c2.year, c2.weather) == (42, 3, "rain")


def test_weather_changes_eventually():
    from world_clock import WorldClock
    c = WorldClock()
    seen = set()
    for _ in range(40):
        c._change_weather()
        seen.add(c.weather)
    assert len(seen) >= 2, "sää ei koskaan vaihdu"


def test_market_sell_and_buy(manager):
    from menus.market_menu import MarketMenu
    manager.inventory["Milk"] = 3
    mm = MarketMenu(manager)
    g0 = manager.gold
    mm._sell("Milk", 2)
    assert manager.gold == g0 + 8  # 2 x 4g
    assert manager.inventory.get("Milk") == 1

    manager.gold = 100
    mm._buy("Empty Bucket")
    assert manager.gold == 95
    assert any(type(i).__name__ == "BucketEmpty" for i in manager.equipment_bag)


def test_innkeeper_debt_flow(manager):
    manager.innkeeper_debt = 25
    manager.npc_state.setdefault("marda_shant",
                                 {"relationship": 0, "flags": {}, "history": []})
    manager.npc_state["marda_shant"]["flags"]["met"] = True

    # Velka näkyy hubissa
    menu = manager.open_dialogue("marda_shant")
    assert "debt_status" in menu.nodes

    # Maksu toimii ja antaa mainetta
    manager.gold = 100
    menu2 = manager.open_dialogue("marda_shant")
    menu2.apply_effect("pay_innkeeper_debt")
    assert manager.innkeeper_debt == 0
    assert manager.gold == 75

    # Maksettuna velkavalintaa ei enää ole
    menu3 = manager.open_dialogue("marda_shant")
    assert "debt_status" not in menu3.nodes


def test_raid_starts_and_retreats(manager):
    """Raidi alkaa kellon mukaan ja päättyy aina (viim. perääntymiseen)."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(manager)

    guards = [n for n in city.npcs if n.name == "Muckford Guard"]
    assert len(guards) == 3, "vartijoita väärä määrä"

    manager.next_raid_day = 1
    manager.world_clock.minutes = 10 * 60

    frames = 0
    while city.raid_state != "active" and frames < 1000:
        city.update(); frames += 1
    assert city.raid_state == "active", "raidi ei alkanut"
    assert len(city.raid_rats) >= 4

    frames = 0
    while city.raid_state == "active" and frames < 4300:
        city.update(); frames += 1
    assert city.raid_state == "idle", "raidi ei paattynyt aikarajaankaan"
    assert manager.next_raid_day > 1, "seuraavaa raidia ei ajastettu"
