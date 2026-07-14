# tests/test_playtest9_fixes.py
"""Pelitestikierros 9: valuuttanäytöt (SP/GP/PL/HC) yhtenäisiksi ja
Crown & Dagger: lompakko + talon kassa + toinen pelipaikka + maine."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

pygame.init()
pygame.display.set_mode((1920, 1080))


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


# ----------------------------------------------------------------------
# Valuuttanäytöt
# ----------------------------------------------------------------------

def test_format_money_conversions():
    from ui_kit import format_money
    assert format_money(134) == "1 GP 34 SP", \
        "134 SP EI ole '134 kultaa' vaan 1 GP 34 SP"
    assert format_money(5) == "5 SP"
    assert format_money(10000) == "1 PL"


def test_quest_rewards_use_currency_format():
    import main  # noqa: F401
    from quest_registry import get_quest_def
    manure = get_quest_def("quest_manure_cleanup")
    assert manure.reward_text == "5 SP", "questin palkkio SP:nä, ei 'Gold'"
    nodes = manure.get_dialogue_for_npc("Farmer Gus", "available")
    accept = nodes["accept_quest"]
    assert "Gold" not in accept.text
    assert "5 SP" in accept.text


def test_recruit_dialogue_shows_formatted_cost():
    import main  # noqa: F401
    from npc.recruit_npc import RecruitNPC
    from units.human import Human
    from settings import GREEN
    u = Human("Pricey Pete", 0, 0, GREEN)
    u.cost = 134
    npc = RecruitNPC(u)
    npc.final_cost = 134
    context = {"player": {"name": "Commander", "gold": 9999},
               "reputation": 0, "matches_played": 0, "unit": u}
    nodes = npc.get_nodes(context)
    texts = []
    for node in nodes.values():
        texts.append(getattr(node, "text", ""))
        for ch in getattr(node, "choices", []) or []:
            texts.append(getattr(ch, "text", ""))
    joined = " | ".join(texts)
    assert "134 Gold" not in joined, "rekryhinta ei saa näkyä kultana"
    assert "1 GP 34 SP" in joined, "hinta muotoillaan valuutoiksi"


# ----------------------------------------------------------------------
# Crown & Dagger: talon kassa
# ----------------------------------------------------------------------

def _crown(m, venue="sunk_cask"):
    from minigames.crown_knives import CrownKnivesMenu
    m.crown_venue = venue
    menu = CrownKnivesMenu(m)
    menu.on_enter()
    return menu


def test_house_purse_pays_wins_and_collects_losses():
    from minigames.crown_knives import get_house, HOUSE_PURSE_MAX
    m = _manager()
    menu = _crown(m)
    house = get_house(m, "sunk_cask")
    assert house["purse"] == HOUSE_PURSE_MAX

    # Voitto: oma panos takaisin + voitto talon kassasta
    m.gold = 0
    menu._round_stake = 50
    menu.current_winnings = 100  # potti = panos + talon vastine
    menu.winner = "PLAYER"
    menu.visual_pot = []
    menu._start_payout_animation(win=True)
    assert m.gold == 100
    assert get_house(m, "sunk_cask")["purse"] == HOUSE_PURSE_MAX - 50

    # Tappio: panos talon kassaan
    menu._round_stake = 30
    menu.winner = "NPC"
    menu.visual_pot = []
    menu._start_payout_animation(win=False)
    assert get_house(m, "sunk_cask")["purse"] == HOUSE_PURSE_MAX - 20


def test_house_purse_refills_over_days():
    from minigames.crown_knives import get_house, HOUSE_REFILL_PER_DAY
    m = _manager()
    house = get_house(m, "sunk_cask")
    house["purse"] = 0
    m.world_clock.day += 2
    house = get_house(m, "sunk_cask")
    assert house["purse"] == 2 * HOUSE_REFILL_PER_DAY, \
        "kassa täyttyy ajan kanssa"


def test_empty_house_refuses_bets():
    from minigames.crown_knives import get_house
    m = _manager()
    menu = _crown(m)
    get_house(m, "sunk_cask")["purse"] = 0
    m.gold = 100
    menu.bet_amount = 20
    menu._start_round()
    assert menu.state == "BETTING", "tyhjä kassa -> diileri ei ota vetoa"
    assert m.gold == 100, "panosta ei veloiteta"
    assert "empty" in menu.message.lower()


def test_win_streak_grants_reputation():
    from minigames.crown_knives import get_house
    m = _manager()
    menu = _crown(m)
    house = get_house(m, "sunk_cask")
    house["wins"] = 2
    from quest_system import quest_manager
    rep0 = quest_manager.reputation
    menu._round_stake = 10
    menu.current_winnings = 20
    menu.winner = "PLAYER"
    menu.visual_pot = []
    menu._start_payout_animation(win=True)
    assert house["wins"] == 3
    assert quest_manager.reputation == rep0 + 1, "joka 3. voitto +1 rep"


def test_venues_have_separate_purses():
    from minigames.crown_knives import get_house, HOUSE_PURSE_MAX
    m = _manager()
    get_house(m, "sunk_cask")["purse"] = 10
    assert get_house(m, "arena_hall")["purse"] == HOUSE_PURSE_MAX, \
        "pelipaikoilla omat kassat"


def test_arena_hall_dealer_opens_game():
    m = _manager()
    from citys.mucford.city_interiors import ArenaHallMenu
    hall = ArenaHallMenu(m)
    hall.on_enter()
    dealer = next(u for u, k in hall.hall_npcs if k == "dealer")
    hall.player.rect.center = (dealer.rect.centerx + 30, dealer.rect.centery)
    hall.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e,
                                         unicode="e"))
    assert hall.next_state == "crown_knives"
    assert m.crown_venue == "arena_hall"
    assert m.crown_return_state == "arena_hall"


def test_crown_draw_shows_wallet_and_house(tmp_path):
    m = _manager()
    m.gold = 137
    menu = _crown(m)
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)  # lompakko + talon kassa piirtyvät kaatumatta
