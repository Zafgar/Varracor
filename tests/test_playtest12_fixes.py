# tests/test_playtest12_fixes.py
"""Pelitestikierros 12:
1) syöte ei vuoda pause-valikon/dialogin läpi ("painan nappeja valikossa
   ja se castaa taustalla") - Commander-tason portti + GameplayScreen
   pausaa dialogin ajaksi
2) questinantaja kojun takana: E kojulla avaa quest-dialogin kun questin
   voi ottaa/palauttaa (kauppa aukeaa normaalisti questin haun aikana)
3) ilmoitustaulu ei enää generoidu asuinkorttelin talon alle
4) kalastuksen HOOK IT! -kehote kaatoi pelin (väärät argumentit
   _draw_floating_promptille)
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
    import main  # noqa: F401 - asentaa integraatiot
    from game_manager import GameManager
    return GameManager()


def _reset_quests():
    from quest_system import quest_manager
    for qid in ("quest_manure_cleanup", "quest_first_swing",
                "quest_krads_crate"):
        q = quest_manager.get_quest(qid)
        if q:
            q.status = "available"
            q.is_finished = False
            q.progress = 0


def _city(m):
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    return city


# ----------------------------------------------------------------------
# 1) Syötevuoto pause-valikossa / dialogissa
# ----------------------------------------------------------------------

def test_commander_input_blocked_while_paused(monkeypatch):
    from items.swords.weak_sword import WeakSword
    m = _manager()
    hero = m.player_character
    hero.weapon_masteries.add("sword")
    hero.equipment["main_hand"] = WeakSword()
    hero.calculate_final_stats()
    # Testataan suoraa lyöntiä ilman charge-mekaniikkaa
    hero.equipment["main_hand"].charge_enabled = False
    attacks = []
    monkeypatch.setattr(hero, "perform_attack",
                        lambda *a, **k: attacks.append(1))
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (1, 0, 0))
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (960, 540))

    m.paused = True
    hero.run_combat_ai([hero], [], manager=m)
    assert not attacks, "pause-valikossa klikkaus ei lyö/castaa"
    assert hero._resume_input_block

    # Valikko kiinni mutta LMB (valikon sulkenut klikkaus) yhä pohjassa
    m.paused = False
    hero.run_combat_ai([hero], [], manager=m)
    assert not attacks, "valikon sulkenut klikkaus ei laukaise lyöntiä"

    # LMB irti -> esto raukeaa, normaali lyönti toimii taas
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (0, 0, 0))
    hero.run_combat_ai([hero], [], manager=m)
    assert not hero._resume_input_block
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (1, 0, 0))
    hero.run_combat_ai([hero], [], manager=m)
    assert attacks, "esto ei jää päälle pysyvästi"


def test_commander_input_blocked_during_dialogue(monkeypatch):
    from items.swords.weak_sword import WeakSword
    m = _manager()
    hero = m.player_character
    hero.weapon_masteries.add("sword")
    hero.equipment["main_hand"] = WeakSword()
    hero.calculate_final_stats()
    attacks = []
    monkeypatch.setattr(hero, "perform_attack",
                        lambda *a, **k: attacks.append(1))
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: (1, 0, 0))
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (960, 540))
    m.active_dialogue = {"unit": None, "text": "Hei!", "options": []}
    hero.run_combat_ai([hero], [], manager=m)
    assert not attacks, "dialogin klikkaukset eivät castaa taustalla"
    m.active_dialogue = None


def test_gameplay_screen_pauses_during_dialogue(monkeypatch):
    from menus.gameplay_screen import GameplayScreen
    m = _manager()

    class _Arena:
        obstacles = []
        width = 2000
        height = 2000

    gs = GameplayScreen(m)
    gs.arena = _Arena()
    calls = []
    monkeypatch.setattr(gs.player, "run_combat_ai",
                        lambda *a, **k: calls.append(1))
    m.active_dialogue = {"unit": None, "text": "Hei!", "options": []}
    m.dialogue_cooldown = 5
    gs._update_gameplay([gs.player])
    assert not calls, "dialogi pausaa pelilogiikan GameplayScreenillä"
    assert m.dialogue_cooldown == 4, "cooldown kuluu dialogin aikana"
    m.active_dialogue = None
    m.dialogue_cooldown = 0
    gs._update_gameplay([gs.player])
    assert calls, "dialogin jälkeen pelilogiikka jatkuu"


# ----------------------------------------------------------------------
# 2) Questinantaja kojun takana (Krad)
# ----------------------------------------------------------------------

def test_stall_interact_opens_quest_dialogue_when_actionable():
    from quest_system import quest_manager
    m = _manager()
    _reset_quests()
    city = _city(m)
    m.world_clock.minutes = 10 * 60  # hour on property (minuuteista)
    city._update_market_life()
    stall = next(s for s in city.market_stalls
                 if getattr(s, "shop_id", "") == "oddments")
    keeper = city._keeper_for_stall(stall)
    assert keeper is not None and keeper.name == "Krad"
    assert quest_manager.npc_has_actionable_quest("Krad")
    city.player.rect.center = (stall.rect.centerx, stall.rect.bottom + 20)
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert city.next_state == "dialogue_active", \
        "E kojulla avaa Kradin quest-dialogin kun quest on otettavissa"


def test_stall_opens_shop_while_quest_active():
    from quest_system import quest_manager
    m = _manager()
    _reset_quests()
    quest_manager.accept_quest("quest_krads_crate")
    assert not quest_manager.npc_has_actionable_quest("Krad"), \
        "haku kesken - kauppa saa aueta"
    city = _city(m)
    m.world_clock.minutes = 10 * 60  # hour on property (minuuteista)
    city._update_market_life()
    stall = next(s for s in city.market_stalls
                 if getattr(s, "shop_id", "") == "oddments")
    city.player.rect.center = (stall.rect.centerx, stall.rect.bottom + 20)
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert city.next_state == "district_shop", \
        "questin haun aikana kojulta voi yhä ostaa (vapa yms.)"
    _reset_quests()


def test_completed_crate_turnin_at_stall():
    from quest_system import quest_manager
    m = _manager()
    _reset_quests()
    quest_manager.accept_quest("quest_krads_crate")
    q = quest_manager.get_quest("quest_krads_crate")
    q.progress = 1
    q.status = "completed"
    assert quest_manager.npc_has_actionable_quest("Krad")
    city = _city(m)
    m.world_clock.minutes = 10 * 60  # hour on property (minuuteista)
    city._update_market_life()
    stall = next(s for s in city.market_stalls
                 if getattr(s, "shop_id", "") == "oddments")
    city.player.rect.center = (stall.rect.centerx, stall.rect.bottom + 20)
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert city.next_state == "dialogue_active", \
        "palautus onnistuu kojulta"
    _reset_quests()


# ----------------------------------------------------------------------
# 3) Ilmoitustaulu avoimella torilla
# ----------------------------------------------------------------------

def test_notice_board_not_under_buildings():
    from assets.tiles.arena import Arena
    from assets.tiles.muckford_objects import NoticeBoard
    a = Arena()
    board = next(p for p in a.props if isinstance(p, NoticeBoard))
    bw = board.image.get_width() if board.image else board.rect.w
    bh = board.image.get_height() if board.image else board.rect.h
    board_rect = pygame.Rect(board.image_pos[0], board.image_pos[1], bw, bh)
    for p in a.props:
        if p is board or getattr(p, "is_flat", False) or p.rect.w == 0:
            continue
        if not getattr(p, "is_structure", False):
            continue
        pw = p.image.get_width() if p.image else p.rect.w
        ph = p.image.get_height() if p.image else p.rect.h
        prect = pygame.Rect(p.image_pos[0], p.image_pos[1], pw, ph)
        assert not prect.colliderect(board_rect), \
            f"ilmoitustaulu rakennuksen alla: {type(p).__name__}"


# ----------------------------------------------------------------------
# 4) Kalastuskehote ei kaada peliä
# ----------------------------------------------------------------------

def test_fishing_bite_prompt_draws_without_crash():
    m = _manager()
    city = _city(m)

    class _Bite:
        state = "BITE"

    city.fishing_session = _Bite()
    city.active_fishing_spot = (city.player.rect.centerx + 60,
                                city.player.rect.centery + 60)
    surf = pygame.Surface((1920, 1080))
    city.draw(surf)  # HOOK IT! -kehote piirtyy kaatumatta
