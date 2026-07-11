# tests/test_smoke.py
"""Savutestit: peli käynnistyy ja ydinjärjestelmät alustuvat."""


def test_main_imports():
    import main  # noqa: F401 - koko menupuu ja järjestelmät importtaantuvat


def test_game_manager_boots(manager):
    assert manager.gold >= 0
    assert manager.player_character is not None
    assert len(manager.recruit_options) > 0
    assert len(manager.shop_items) > 0


def test_boss_registry():
    from missions.boss_registry import load_mission_package
    assert load_mission_package("boss_rat_king") is not None


def test_item_registry():
    from items.item_registry import create_item, create_fists, get_available_item_classes
    fists = create_fists()
    assert fists is not None and fists.name == "Fists"
    classes = get_available_item_classes()
    assert len(classes) > 20
    item = create_item("WeakSword")
    assert item is not None


def test_overlay_cache():
    from ui_kit import get_fullscreen_overlay
    s1 = get_fullscreen_overlay((0, 0, 0, 150))
    s2 = get_fullscreen_overlay((0, 0, 0, 150))
    assert s1 is s2


def test_dialogue_event_handling(manager):
    import pygame

    class FakeUnit:
        rect = pygame.Rect(0, 0, 10, 10)
        name = "Tester"

    manager.start_dialogue(FakeUnit(), "Hei!", options=[
        {"text": "A", "action": "opt_a"},
        {"text": "B", "action": "opt_b"},
    ])
    assert manager.active_dialogue is not None

    # Numeronäppäin valitsee ja sulkee
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)
    assert manager.handle_dialogue_event(ev) is True
    assert manager.active_dialogue is None

    # SPACE sulkee
    manager.start_dialogue(FakeUnit(), "Moi taas")
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    assert manager.handle_dialogue_event(ev) is True
    assert manager.active_dialogue is None


def test_tier0_lore_integration():
    """Tier 0 -kaanon: 6 tiimiä managereineen kytkeytyy liigaan."""
    from lore.world_data import get_tier_teams, TIER0_CHARACTERS, HAMO_BOUNTIES
    teams = get_tier_teams(0)
    assert len(teams) == 6
    assert teams[0]["manager"] == "Mara Pikestring"
    assert "hamo" in TIER0_CHARACTERS
    assert HAMO_BOUNTIES["Rat Tail"] > 0

    from leagues.league_data import generate_league_teams
    league = generate_league_teams(1)  # game tier 1 = lore tier 0
    names = [t.name for t in league]
    assert "Shanty Yard Saints" in names
    assert "The Siltbound" in names


def test_hamo_dialogue_and_bounty(manager):
    """Hamo aukeaa ja ostaa rotanhännät bounty-hintaan."""
    from quest_system import quest_manager
    manager.inventory["Rat Tail"] = 7
    menu = manager.open_dialogue("hamo")
    assert menu is not None
    gold0 = manager.gold
    menu.apply_effect("hamo_sell_tails")
    assert manager.gold == gold0 + 7 * 4
    assert manager.inventory.get("Rat Tail", 0) == 0
