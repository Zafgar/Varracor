# tests/test_playtest17_fixes.py
"""Pelitestikierros 17:
1) hotbarin hover-tooltipit + toimintopalkin sisältöikonit (LMB = ase,
   DASH = saappaat, BLOCK = kilpi/ase)
2) instant cast per slotti (options/CONTROLS): näppäin castaa heti
   kursorin suuntaan
3) hotbarin sivut (2 = pikatyökalut nopeaan vaihtoon), lukko mana-orbin
   vieressä ja kykyjen raahausjärjestely lukko auki
4) Rift Pulse = "antakaa tilaa": pieni vahinko, kova työntö + hidastus
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


@pytest.fixture
def tmp_prefs(tmp_path, monkeypatch):
    from systems import hotbar_prefs
    monkeypatch.setattr(hotbar_prefs, "OPTIONS_FILE",
                        str(tmp_path / "options.json"))
    monkeypatch.setattr(hotbar_prefs, "_loaded", False)
    monkeypatch.setattr(hotbar_prefs, "_state",
                        {"instant": {}, "locked": True})
    return hotbar_prefs


class _FakeKeys:
    def __init__(self, *down):
        self.down = set(down)

    def __getitem__(self, code):
        if code > 100000:
            raise IndexError(code)
        return code in self.down


# ----------------------------------------------------------------------
# 1) Asetusten persistenssi
# ----------------------------------------------------------------------

def test_hotbar_prefs_roundtrip(tmp_prefs):
    hp = tmp_prefs
    assert hp.is_locked() is True
    assert hp.is_instant("spell1") is False
    hp.set_instant("spell1", True)
    hp.set_locked(False)
    # Uusi "sessio" lukee tiedostosta
    hp._loaded = False
    hp._state = {"instant": {}, "locked": True}
    assert hp.is_instant("spell1") is True
    assert hp.is_locked() is False


# ----------------------------------------------------------------------
# 2) Instant cast
# ----------------------------------------------------------------------

def test_instant_cast_fires_on_keypress(tmp_prefs, monkeypatch):
    from systems import keybinds
    m = _manager()
    hero = m.player_character
    hero.equipment["main_hand"] = None
    from spells.commander.rift_pulse import RiftPulse
    hero.equipment["spell1"] = RiftPulse()  # tuore sankari: slotit tyhjiä
    tmp_prefs.set_instant("spell1", True)
    casts = []
    monkeypatch.setattr(hero, "_try_use_slot",
                        lambda slot, x, y, units, mg: casts.append(slot)
                        or True)
    key1 = keybinds.key("spell_1")
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: _FakeKeys(key1))
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (0, 0, 0))
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (960, 540))
    hero.prev_keys = _FakeKeys()
    hero.run_combat_ai([hero], [], manager=m)
    assert casts == ["spell1"], "instant cast laukesi heti näppäimestä"
    assert hero.selected_spell_slot is None, "slottia ei jäädä valitsemaan"


def test_without_instant_key_selects_slot(tmp_prefs, monkeypatch):
    from systems import keybinds
    m = _manager()
    hero = m.player_character
    from spells.commander.rift_pulse import RiftPulse
    hero.equipment["spell1"] = RiftPulse()
    assert tmp_prefs.is_instant("spell1") is False
    key1 = keybinds.key("spell_1")
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: _FakeKeys(key1))
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (0, 0, 0))
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (960, 540))
    hero.prev_keys = _FakeKeys()
    hero.run_combat_ai([hero], [], manager=m)
    assert hero.selected_spell_slot == "spell1", "vanha tapa: valinta"
    hero.selected_spell_slot = None


# ----------------------------------------------------------------------
# 3) Hotbarin sivut, lukko, pikatyökalut ja raahaus
# ----------------------------------------------------------------------

def test_page2_quick_equip_swaps_tool():
    from items.tools.weak_pickaxe import WeakPickaxe
    m = _manager()
    hero = m.player_character
    pick = WeakPickaxe()
    m.equipment_bag.append(pick)
    old = hero.equipment.get("main_hand")
    quick = hero._quick_items()
    assert pick in quick, "reppuhakku näkyy sivulla 2"
    idx = quick.index(pick)
    assert hero.try_quick_equip(idx, m) is True
    assert hero.equipment["main_hand"] is pick
    if old is not None and getattr(old, "name", "") != "Fists":
        assert old in m.equipment_bag, "vanha ase palasi reppuun"


def test_hotbar_lock_and_page_buttons(tmp_prefs):
    m = _manager()
    hero = m.player_character
    surf = pygame.Surface((1920, 1080))
    hero.draw_hud(surf)
    assert hero._hotbar_ui.get("lock") and hero._hotbar_ui.get("down")
    # Lukon klikkaus togglaa
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                            pos=hero._hotbar_ui["lock"].center, button=1)
    assert hero.handle_hotbar_event(ev, m) is True
    assert tmp_prefs.is_locked() is False
    # Nuoli alas -> sivu 2 (pikatyökalut)
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                            pos=hero._hotbar_ui["down"].center, button=1)
    assert hero.handle_hotbar_event(ev, m) is True
    assert hero.hotbar_page == 2
    hero.draw_hud(surf)  # sivu 2 piirtyy kaatumatta


def test_drag_reorders_spell_slots(tmp_prefs):
    m = _manager()
    hero = m.player_character
    tmp_prefs.set_locked(False)
    from spells.commander.rift_pulse import RiftPulse
    hero.equipment["spell1"] = RiftPulse()
    surf = pygame.Surface((1920, 1080))
    hero.draw_hud(surf)
    rects = {ref: rect for rect, ref in hero._hotbar_rects}
    a_item = hero.equipment.get("spell1")
    b_item = hero.equipment.get("spell2")
    assert a_item is not None
    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                              pos=rects["spell1"].center, button=1)
    assert hero.handle_hotbar_event(down, m) is True
    assert hero._drag_slot == "spell1"
    up = pygame.event.Event(pygame.MOUSEBUTTONUP,
                            pos=rects["spell2"].center, button=1)
    assert hero.handle_hotbar_event(up, m) is True
    assert hero.equipment.get("spell2") is a_item, "raahaus vaihtoi paikat"
    assert hero.equipment.get("spell1") is b_item


def test_locked_hotbar_does_not_drag(tmp_prefs):
    m = _manager()
    hero = m.player_character
    tmp_prefs.set_locked(True)
    surf = pygame.Surface((1920, 1080))
    hero.draw_hud(surf)
    rect = hero._hotbar_rects[0][0]
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=rect.center,
                            button=1)
    assert hero.handle_hotbar_event(ev, m) is False
    assert hero._drag_slot is None


def test_hud_tooltips_and_action_icons_draw():
    m = _manager()
    hero = m.player_character
    surf = pygame.Surface((1920, 1080))
    hero.draw_hud(surf)
    # Hover slotin päällä -> tooltip piirtyy kaatumatta
    rect = hero._hotbar_rects[0][0]
    import unittest.mock as mock
    with mock.patch.object(pygame.mouse, "get_pos",
                           return_value=rect.center):
        hero.draw_hud(surf)
    # Toimintoruutujen tooltipit
    hero._draw_action_tooltip(surf, "LMB", 900, 800)
    hero._draw_action_tooltip(surf, "SPACE", 900, 800)
    hero._draw_action_tooltip(surf, "RMB", 900, 800)
    hero._draw_boots_icon(surf, 100, 100, 40)
    hero._draw_shield_icon(surf, 100, 100, 40)


# ----------------------------------------------------------------------
# 4) Rift Pulse: työntö + hidastus, pieni vahinko
# ----------------------------------------------------------------------

def test_rift_pulse_pushes_and_slows():
    from spells.commander.rift_pulse import RiftPulse
    from units.human import Human
    from settings import PLAYER_TEAM, ENEMY_TEAM
    m = _manager()
    hero = m.player_character
    hero.rect.center = (1000, 1000)
    hero.current_mana = hero.max_mana
    foe = Human("Ahdistaja", 0, 0, ENEMY_TEAM)
    foe.rect.center = (1060, 1000)
    foe.defense = 0
    m.all_units.empty()
    m.all_units.add([hero, foe])
    m.current_arena = None
    hp0 = foe.current_hp
    d0 = abs(foe.rect.centerx - hero.rect.centerx)
    spell = RiftPulse()
    assert spell.cast(hero, None, m) is True
    d1 = abs(foe.rect.centerx - hero.rect.centerx)
    assert d1 >= d0 + 100, "kova sinkaisu poispäin"
    assert any(e.get("type") == "Slow" for e in foe.status_effects), \
        "lyhyt hidastus"
    dmg = hp0 - foe.current_hp
    assert 0 < dmg <= 20, f"vahinko pieni ({dmg}) - työntö on pointti"
