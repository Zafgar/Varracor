# tests/test_gear_tiers.py
"""
Gear-tierit: scrap (Tier 0) -> iron (Tier 1) -> blacksteel (Tier 2).
Blacksteel-sarja peritaan weak-aseista ja auto-loytyy registrysta.
"""
import pytest


BLACKSTEEL = ["Blacksteel Sword", "Blacksteel Axe", "Blacksteel Maul",
              "Blacksteel Pike", "Blacksteel Dirk", "Yew Longbow",
              "Steel Crossbow", "Runed Staff", "Blacksteel Shield"]


def test_blacksteel_items_resolve():
    from items.item_registry import create_item
    for n in BLACKSTEEL:
        assert create_item(n) is not None, f"{n} missing from registry"


def test_weapon_for_three_tiers():
    from leagues.league_data import weapon_for
    assert weapon_for("sword", 1) == "Scrap Blade"
    assert weapon_for("sword", 2) == "Iron Sword"
    assert weapon_for("sword", 3) == "Blacksteel Sword"
    # elite nostaa yhden pykalan
    assert weapon_for("sword", 1, elite=True) == "Iron Sword"
    assert weapon_for("sword", 2, elite=True) == "Blacksteel Sword"


def test_shield_for_three_tiers():
    from leagues.league_data import shield_for
    assert shield_for(1) == "Pot Lid"
    assert shield_for(2) == "Wooden Buckler"
    assert shield_for(3) == "Blacksteel Shield"


def test_damage_progression():
    from items.item_registry import create_item
    scrap = create_item("Scrap Blade").damage
    iron = create_item("Iron Sword").damage
    black = create_item("Blacksteel Sword").damage
    assert scrap < iron < black


def test_tier2_materials_sellable():
    from lore.world_data import MARKET_PRICES
    sell = MARKET_PRICES["sell"]
    for m in ("Blacksteel Ore", "Ironbark", "Direhide"):
        assert m in sell and sell[m] > 0
