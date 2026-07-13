# tests/test_adventure_loop.py
"""Muckfordin seikkailusilmukka: rottaraidi spawnaa ja palkitsee pelaajan
tapoista (myös epäsuorat tapot krediittaavat - regressio: vain melee
kirjasi tapot), ja suuntapaneeli näyttää seuraavat tavoitteet myös
tiimirekisteröinnin jälkeen."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))


def _city():
    import main  # noqa: F401
    from game_manager import GameManager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    m = GameManager()
    menu = MuckfordCityMenu(m)
    menu.on_enter()
    return m, menu


def test_indirect_kills_credit_attacker():
    """Nuoli/loitsutappojen pitää kasvattaa stats['kills'] (take_damage)."""
    import main  # noqa: F401
    from units.human import Human
    from settings import GREEN, RED
    a = Human("Archer", 0, 0, GREEN, "Common")
    t = Human("Target", 50, 0, RED, "Common")
    t.defense = 0
    while not t.is_dead:
        t.take_damage(60, "Physical", attacker=a)  # kuin projektiili
    assert a.stats["kills"] == 1
    # Kuolleen lyöminen ei tuplaa
    t.take_damage(60, "Physical", attacker=a)
    assert a.stats["kills"] == 1


def test_raid_spawns_and_rewards_player_kills():
    m, menu = _city()
    m.world_clock.minutes = 10 * 60.0
    m.next_raid_day = m.world_clock.day
    hero = m.player_character
    xp0, gold0 = hero.xp, m.gold

    for _ in range(1500):
        menu.update()
        if menu.raid_state == "active":
            break
    assert menu.raid_state == "active"
    assert len(menu.raid_rats) >= 4

    for rat in menu.raid_rats:
        while not rat.is_dead:
            rat.take_damage(50, attacker=hero, manager=m)
    for _ in range(300):
        menu.update()
        if menu.raid_state == "idle":
            break
    assert "REPELLED" in menu.raid_result
    assert hero.xp > xp0, "raidin tapot antavat Commanderille XP:tä"
    assert m.gold > gold0, "raidin torjunta palkitaan kullalla"


def test_tracker_shows_objectives_after_registration():
    m, menu = _city()
    m.team_registered = True
    from systems.tier0_world_tracker import ensure_tier0_state, tier0_phase
    ensure_tier0_state(m)
    assert tier0_phase(m) >= 1
    objs = m.get_tier0_objectives(2)
    assert objs, "suunta ei katoa rekisteröinnin jälkeen"
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)  # paneeli piirtyy tavoitteineen ilman virheitä
