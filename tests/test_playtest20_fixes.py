# tests/test_playtest20_fixes.py
"""Pelitestikierros 20: rift-invaasioalueet.
1) Maailmankartalta reitit kolmelle riivatulle alueelle (suo,
   hautausmaa, rämemetsä) - target_state "rift_site"
2) Repeämän haastaminen käynnistää teeman mukaiset wavet; viimeisen
   aallon jälkeen saapuu jättimäinen buffattu FINAL BOSS (bossipalkki)
3) Bossin kaaduttua repeämän voi sinetöidä -> Vortex-kristalleja
   (siirretään reppuun vaikka match_in_progress ohjaisi ne loottiin)
4) Paluukyltti vie takaisin maailmankartalle; pelaajan kaatuminen
   nollaa invaasion ja raahaa sisäänkäynnille
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def _site(m, location="rift_whisper_marsh"):
    from menus.rift_site_menu import RiftSiteMenu
    m.pending_world_location = location
    menu = RiftSiteMenu(m)
    menu.on_enter()
    return menu


def _kill_until(menu, target_phase, max_loops=12):
    for _ in range(max_loops):
        for mm in menu.monsters:
            mm.is_dead = True
        for _ in range(200):
            menu.update()
            if menu.phase == target_phase:
                return True
    return menu.phase == target_phase


# ----------------------------------------------------------------------
# 1) Maailmankartta
# ----------------------------------------------------------------------

def test_world_map_has_rift_routes():
    from lore.world_map_data import LOCATIONS, ROUTES
    for loc_id in ("rift_whisper_marsh", "rift_drowned_graveyard",
                   "rift_bogwood"):
        loc = LOCATIONS[loc_id]
        assert loc["target_state"] == "rift_site"
        assert loc["content_state"] == "playable"
        assert "Vortex Crystal" in loc["materials"]
        assert any(loc_id in (r["a"], r["b"]) if isinstance(r, dict)
                   else loc_id in r for r in _route_pairs(ROUTES)), \
            f"reitti puuttuu: {loc_id}"


def _route_pairs(routes):
    out = []
    for r in routes:
        if isinstance(r, dict):
            out.append((r.get("a") or r.get("from"),
                        r.get("b") or r.get("to")))
        else:
            out.append(tuple(r)[:2])
    return out


def test_travel_to_rift_site():
    from systems.world_progression import travel_to
    m = _manager()
    ok, msg, target = travel_to(m, "rift_whisper_marsh")
    assert ok, msg
    assert target == "rift_site"
    assert m.pending_world_location == "rift_whisper_marsh"


# ----------------------------------------------------------------------
# 2) Wavet ja boss
# ----------------------------------------------------------------------

def test_invasion_waves_then_giant_boss():
    m = _manager()
    menu = _site(m, "rift_drowned_graveyard")
    assert menu.theme_id == "graveyard"
    assert menu.phase == "dormant"
    menu._start_invasion()
    assert menu.phase == "wave"
    assert menu.monsters, "aalto 1 vyöryi repeämästä"
    n_waves = len(menu.theme["waves"])
    assert _kill_until(menu, "boss"), "kaikki aallot -> boss saapuu"
    assert menu.wave_index == n_waves
    boss = menu.boss
    assert boss is not None and boss.is_boss, "bossipalkki piirtyy"
    assert boss.name == "Grave Tyrant"
    # Jättiversio: reilusti buffattu perusolentoon nähden
    from units.undead_zombie import UndeadZombie
    from settings import ENEMY_TEAM
    base = UndeadZombie("Verrokki", 0, 0, ENEMY_TEAM)
    assert boss.max_hp >= base.max_hp * 5, "iso HP-buffi"
    assert boss.image.get_width() > base.image.get_width(), \
        "tuplakokoinen sprite"


def test_seal_after_boss_grants_crystals_to_inventory():
    m = _manager()
    menu = _site(m, "rift_whisper_marsh")
    menu._start_invasion()
    # Kesken invaasion ei voi sinetöidä (E antaa vain varoituksen)
    assert menu.phase == "wave"
    assert not menu.rift.is_empty
    _kill_until(menu, "boss")
    menu.boss.is_dead = True
    menu.update()
    assert menu.phase == "sealable"
    m.player_character.rect.center = (menu.rift.rect.centerx + 40,
                                      menu.rift.rect.centery)
    assert menu.rift.try_begin_channel(m.player_character, m,
                                       max_range_bonus=80)
    for _ in range(260):
        menu.update()
        if menu.phase == "sealed":
            break
    assert menu.phase == "sealed"
    assert m.inventory.get("Vortex Crystal", 0) >= 3, \
        "iso repeämä antaa 3-4 kristallia REPPUUN"
    assert not m.round_rewards.get("loot", {}).get("Vortex Crystal"), \
        "kristallit eivät jää lunastamattomaan loottiin"


# ----------------------------------------------------------------------
# 3) Paluu ja kaatuminen
# ----------------------------------------------------------------------

def test_signpost_returns_to_world_map():
    m = _manager()
    menu = _site(m, "rift_bogwood")
    assert menu.theme_id == "bogwood"
    sp = menu.signpost.rect
    m.player_character.rect.center = (sp.centerx + 40, sp.centery)
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert menu.next_state == "world_map", "kyltti vie takaisin"


def test_player_death_triggers_rescue():
    """Pelitesti 21 muutti käytöksen: kaatuminen retkellä vie rescueen
    (herää Muckfordista, noutopalkkio) - invaasio nollautuu vasta
    seuraavalla käynnillä on_enterissä."""
    m = _manager()
    menu = _site(m)
    menu._start_invasion()
    assert menu.phase == "wave"
    m.gold = 200
    m.player_character.is_dead = True
    menu.update()
    assert menu.next_state == "muckford_city", \
        "ilman tiimiä herätään Sunk Caskista"
    assert not m.player_character.is_dead
    assert m.pending_rescue and m.pending_rescue["place"] == "inn"
    assert m.gold == 200 - 25, "Marda perii noutopalkkion"
    # Uusi käynti aloittaa repeämän lepotilasta
    menu2 = _site(m)
    assert menu2.phase == "dormant"
    assert not menu2.monsters
    menu2.draw(pygame.Surface((1920, 1080)))  # piirto kaatumatta
