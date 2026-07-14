# tests/test_display_and_barracks.py
"""Näyttöasetukset (windowed/borderless/fullscreen + resoluutio) ja
Team Barracksin sisätila: punkat, tiimikoon raja, kehitys, moraali,
juttelu ja nukkuminen."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from settings import PLAYER_TEAM


def _manager():
    import main  # noqa: F401 - asentaa integraatiot
    from game_manager import GameManager
    return GameManager()


def _interior(manager):
    from citys.mucford.barracks_interior_menu import BarracksInteriorMenu
    menu = BarracksInteriorMenu(manager)
    menu.on_enter()
    return menu


def _add_gladiators(manager, count):
    from units.human import Human
    for i in range(count):
        u = Human(f"Fighter {i}", 500 + i * 40, 500, PLAYER_TEAM)
        manager.my_team.add(u)


# ----------------------------------------------------------------------
# Näyttöasetukset
# ----------------------------------------------------------------------

def test_display_settings_roundtrip(tmp_path, monkeypatch):
    from systems import display_settings as ds
    monkeypatch.setattr(ds, "OPTIONS_FILE", str(tmp_path / "options.json"))
    ds.apply(mode="borderless", resolution=(1280, 720))
    ds.save()
    # Nollaa ja lataa takaisin
    ds._state["mode"] = "windowed"
    ds._state["resolution"] = None
    ds.load()
    assert ds.get_mode() == "borderless"
    assert ds.get_resolution() == (1280, 720)
    # Palauta windowed muita testejä varten
    ds.apply(mode="windowed", resolution=None)


def test_display_modes_apply_headless():
    from systems import display_settings as ds
    for mode in ds.MODES:
        ds.apply(mode=mode)  # dummy-ajurilla ei saa kaatua
    ds.apply(mode="windowed", resolution=None)
    assert ds.get_mode() == "windowed"
    labels = [lbl for lbl, _s in ds.available_resolutions()]
    assert labels and labels[0].startswith("AUTO")


def test_options_menu_display_buttons(tmp_path, monkeypatch):
    from systems import display_settings as ds
    monkeypatch.setattr(ds, "OPTIONS_FILE", str(tmp_path / "options.json"))
    from menus.options_menu import OptionsMenu
    m = _manager()
    menu = OptionsMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    assert len(menu.mode_rects) == 3, "kolme näyttötilanappia"
    assert menu.res_prev_rect and menu.res_next_rect
    # Klikkaa FULLSCREEN-nappia
    rect = next(r for r, mode in menu.mode_rects if mode == "fullscreen")
    menu.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=rect.center, button=1))
    assert ds.get_mode() == "fullscreen"
    ds.apply(mode="windowed", resolution=None)


def test_sound_save_options_preserves_other_keys(tmp_path, monkeypatch):
    import json
    import sound_manager as sm
    path = tmp_path / "options.json"
    path.write_text(json.dumps({"keybinds": {"interact": [101]},
                                "display": {"mode": "fullscreen",
                                            "resolution": None}}))
    monkeypatch.setattr(sm, "OPTIONS_FILE", str(path))
    sm.sound_system.save_options()
    data = json.loads(path.read_text())
    assert data["keybinds"] == {"interact": [101]}, "keybinds säilyy"
    assert data["display"]["mode"] == "fullscreen", "display säilyy"
    assert "music_volume" in data


# ----------------------------------------------------------------------
# Barracksin sisätila
# ----------------------------------------------------------------------

def test_interior_level1_layout_and_residents():
    from citys.mucford.barracks_interior_arena import BUNKS_PER_LEVEL
    m = _manager()
    _add_gladiators(m, 3)
    menu = _interior(m)
    assert menu.arena.level == 1
    assert len(menu.arena.bunks) == BUNKS_PER_LEVEL[1] == 6
    assert len(menu.residents) == 3, "gladiaattorit oleilevat sisällä"
    # Pelaaja alkaa ovelta
    assert abs(menu.player.rect.centerx - menu.arena.door_rect.centerx) < 5
    # Oleskelu-AI pyörii kaatumatta ja väki pysyy seinien sisällä
    for _ in range(180):
        menu.update()
    for unit, _d in menu.residents:
        assert 0 < unit.rect.centerx < menu.arena.width
        assert 0 < unit.rect.centery < menu.arena.height
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)


def test_bunk_cap_blocks_hiring():
    from units.human import Human
    m = _manager()
    m.team_registered = True  # opening-portti ei estä palkkaamista
    m.gold = 10000
    _add_gladiators(m, 5)     # commander + 5 = 6/6 punkkaa
    assert not m.has_free_bunk()
    rec = Human("Extra", 0, 0, PLAYER_TEAM)
    assert m.hire_unit_by_reference(rec, 10) is False
    assert "bunk" in m.hire_block_message.lower()
    assert rec not in m.my_team
    # Kehitys tasolle 2 avaa lisäpunkat - MUTTA myös johtajuuden
    # (COMMAND-puun Recruiter) pitää sallia isompi rooster
    m.barracks_level = 2
    assert not m.has_free_bunk(), "johtajuus (6) rajaa yhä"
    pc = m.player_character
    pc.unlocked_skills.add("leader_1")
    pc.calculate_final_stats()
    assert m.has_free_bunk()
    assert m.hire_unit_by_reference(rec, 10) is True


def test_upgrade_flow_consumes_materials():
    from citys.mucford.barracks_interior_arena import UPGRADE_COSTS
    m = _manager()
    menu = _interior(m)
    cost = UPGRADE_COSTS[2]
    # Ilman materiaaleja ei rakenneta
    m.gold = cost["gold"]
    menu._try_upgrade()
    assert m.barracks_level == 1
    assert "Missing" in menu.upgrade_feedback
    # Materiaalit + kulta -> taso 2, 8 punkkaa, takka palaa
    for name, need in cost.items():
        if name != "gold":
            m.inventory[name] = need
    menu._try_upgrade()
    assert m.barracks_level == 2
    assert len(menu.arena.bunks) == 8
    assert menu.arena.hearth.lit
    assert m.gold == 0
    for name, need in cost.items():
        if name != "gold":
            assert m.inventory.get(name, 0) == 0


def test_chat_gives_morale_once_per_day():
    m = _manager()
    _add_gladiators(m, 1)
    menu = _interior(m)
    unit = menu.residents[0][0]
    assert unit.morale == 50
    menu._talk_to(unit)
    assert unit.morale == 58, "ensimmäinen juttelu +8 moraalia"
    assert menu.next_state == "dialogue_active"
    menu.next_state = None
    m.pending_dialogue_menu = None
    menu._talk_to(unit)
    assert unit.morale == 58, "sama päivä ei tuplaa"
    # Uusi päivä -> taas bonus
    m.world_clock.advance_day()
    m.pending_dialogue_menu = None
    menu._talk_to(unit)
    assert unit.morale == 66


def test_sleep_heals_team_and_advances_day():
    m = _manager()
    _add_gladiators(m, 2)
    menu = _interior(m)
    day0 = m.world_clock.day
    for u in [m.player_character] + list(m.my_team):
        u.current_hp = max(1, u.max_hp // 3)
        u.current_stamina = 5
    menu._sleep()
    assert m.world_clock.day == day0 + 1
    assert m.world_clock.hour == 7
    for u in [m.player_character] + list(m.my_team):
        assert u.current_hp == u.max_hp
        assert u.current_stamina == u.max_stamina


def test_morale_persists_in_save(tmp_path, monkeypatch):
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE",
                        str(tmp_path / "savegame.json"))
    m = _manager()
    _add_gladiators(m, 1)
    glad = next(iter(m.my_team))
    glad.morale = 77
    glad.last_social_day = 4
    m.barracks_level = 3
    assert save_manager.save_game(m)
    m2 = _manager()
    assert save_manager.load_game(m2)
    assert m2.barracks_level == 3
    loaded = next(iter(m2.my_team))
    assert loaded.morale == 77
    assert loaded.last_social_day == 4


def test_morale_scales_attack_damage():
    from units.human import Human
    from settings import ENEMY_TEAM
    import pygame as pg
    results = {}
    for morale in (0, 100):
        m = _manager()
        a = Human("Attacker", 300, 300, PLAYER_TEAM)
        t = Human("Target", 340, 300, ENEMY_TEAM)
        t.defense = 0
        a.morale = morale
        a.crit_chance = 0
        m.all_units.empty()
        m.all_units.add([a, t])
        hp0 = t.current_hp
        a.attack_cooldown = 0
        a.current_stamina = a.max_stamina
        assert a.perform_attack(target=t, manager=m, range_override=500)
        results[morale] = hp0 - t.current_hp
    assert results[100] > results[0], "korkea moraali lyö kovempaa"


def test_city_barracks_door_leads_to_interior():
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    m = _manager()
    city = MuckfordCityMenu(m)
    city.on_enter()
    barr = city.barracks
    assert barr is not None
    city.player.rect.centerx = barr.rect.centerx
    city.player.rect.bottom = barr.rect.bottom + 10
    city.handle_event(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_e, unicode="e"))
    assert city.next_state == "barracks_interior"
