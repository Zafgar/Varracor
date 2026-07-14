# tests/test_scrapring_arena.py
"""
Scrapring-areena (Rattlebridge Tier 1): crushing gears, steam bursts ja
magnet plates -vaarat + sijaintitietoinen areenavalinta.
"""
import pytest
from settings import PLAYER_TEAM


class _Stub:
    """Kevyt yksikkö magneettilaattatesteihin (ei tarvitse koko Gladiatoria)."""
    def __init__(self, rect, armor_group=None):
        import pygame
        self.rect = pygame.Rect(rect)
        self.is_dead = False
        self.statuses = []
        if armor_group is not None:
            self.armor = type("Arm", (), {"armor_group": armor_group})()
        else:
            self.armor = None

    def _armor_group_from_item(self, item):
        g = str(getattr(item, "armor_group", "")).lower()
        return "heavy" if "heavy" in g else ("cloth" if g else None)

    def apply_status(self, kind, duration, dmg=0):
        self.statuses.append(kind)

    def has_status(self, kind):
        return kind in self.statuses


def _arena():
    from arenas.tier_1.scrapring_arena import ScrapringArena
    return ScrapringArena()


def test_gear_slam_crushes_and_stuns():
    from units.human import Human
    a = _arena()
    gear = a.gears[0]
    u = Human("Victim", 0, 0, PLAYER_TEAM)
    u.rect.center = gear.rect.center
    hp0 = u.current_hp
    gear.phase, gear.timer = "slam", 999
    a.update([u])
    assert u.current_hp < hp0, "rattaan iskun pitäisi tehdä vahinkoa"
    assert u.stun_timer > 0, "iskun pitäisi tainnuttaa"


def test_gear_open_is_safe():
    from units.human import Human
    a = _arena()
    gear = a.gears[0]
    u = Human("Safe", 0, 0, PLAYER_TEAM)
    u.rect.center = gear.rect.center
    hp0 = u.current_hp
    gear.phase, gear.timer = "open", 999
    a.update([u])
    assert u.current_hp == hp0, "auki oleva ratas ei satu"


def test_steam_burst_burns():
    from units.human import Human
    a = _arena()
    vent = a.steam_vents[0]
    u = Human("Scald", 0, 0, PLAYER_TEAM)
    u.rect.center = vent.rect.center
    hp0 = u.current_hp
    vent.phase, vent.timer = "burst", 999
    a.update([u])
    assert u.current_hp < hp0
    assert u.has_status("Burn")


def test_magnet_plate_slows_metal_only():
    a = _arena()
    plate = a.magnet_plates[0]
    metal = _Stub(plate, armor_group="heavy")
    cloth = _Stub(plate, armor_group="cloth")
    a.update([metal, cloth])
    assert metal.has_status("Slow"), "metallihaarniska juuttuu magneettiin"
    assert not cloth.has_status("Slow"), "kangas ei juutu"


def test_is_metal_armored_helper():
    from arenas.tier_1.scrapring_arena import ScrapringArena
    assert ScrapringArena._is_metal_armored(_Stub((0, 0, 10, 10), "heavy")) is True
    assert ScrapringArena._is_metal_armored(_Stub((0, 0, 10, 10), "cloth")) is False
    assert ScrapringArena._is_metal_armored(_Stub((0, 0, 10, 10), None)) is False


def test_location_aware_arena_selection():
    from arenas.arena_registry import get_arena_for
    from arenas.tier_1.scrapring_arena import ScrapringArena
    assert isinstance(get_arena_for(2, "rattlebridge"), ScrapringArena)
    # Tuntematon sijainti -> tier-poolin arvonta (Scrapring VOI osua, koska
    # se kuuluu tier 2 -pooliin - mutta ei joka kerta)
    samples = [get_arena_for(2, "some_other_place") for _ in range(12)]
    assert any(not isinstance(a, ScrapringArena) for a in samples)
