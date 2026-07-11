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


def test_tier1_canon_and_promotion_preview():
    """Tier 1 -kaanon: 8 tiimiä + Sera; promootio-preview toimii."""
    from lore.world_data import (get_tier_teams, get_tier_preview,
                                 TIER1_CHARACTERS, TIER1_ARENAS)
    teams = get_tier_teams(1)
    assert len(teams) == 8
    assert any(t["name"] == "Bridgeguard Five" for t in teams)
    assert "sera_quench" in TIER1_CHARACTERS
    assert "scrapring" in TIER1_ARENAS

    p = get_tier_preview(1)
    assert p["keeper"] == "Sera Quench"
    assert p["hub"] == "Rattlebridge"

    from leagues.league_data import generate_league_teams
    league = generate_league_teams(2)  # game tier 2 = lore tier 1
    names = [t.name for t in league]
    assert "Rattlebridge Runners" in names


def test_tier_promotion_advances(manager):
    """Promootio nostaa tieria ja lataa uuden tierin tiimit."""
    le = manager.league_engine
    le._ensure_initialized()
    start_tier = le.tier
    le.promote_player()
    assert le.tier == start_tier + 1


def test_gladiator_personality_and_origin():
    """Rekrytoitavat yksiköt saavat luonteen ja taustan; bossit eivät."""
    import pygame
    from units.orc import Orc
    from units.goblin import Goblin
    from progression.personality import PERSONALITIES, ORIGINS

    orc = Orc("Grok", 0, 0, (50, 200, 50))
    assert orc.personality in PERSONALITIES
    assert orc.origin in ORIGINS

    gob = Goblin("Snik", 0, 0, (50, 200, 50))
    assert gob.personality in PERSONALITIES


def test_roster_dialogue_evolves_with_relationship(manager):
    """Roster-dialogi muuttuu suhteen mukaan; jutteleminen nostaa suhdetta."""
    from units.orc import Orc
    orc = Orc("Grok", 0, 0, (50, 200, 50))
    orc.personality = "hothead"  # deterministinen

    menu_neutral = manager.open_roster_dialogue(orc)
    neutral_line = menu_neutral.nodes["start"].text

    manager.npc_state["gladiator_Grok"]["relationship"] = 70
    menu_devoted = manager.open_roster_dialogue(orc)
    devoted_line = menu_devoted.nodes["start"].text
    assert neutral_line != devoted_line, "dialogi ei muuttunut suhteen mukaan"

    # "Good talk" nostaa suhdetta rep-efektin kautta
    menu_neutral.apply_effect("rep:3")
    assert manager.npc_state["gladiator_Grok"]["relationship"] >= 70


def test_rival_gladiator_dialogue_by_reputation(manager):
    """Rivaalin dialogi muuttuu pelaajan maineen mukaan."""
    info = ("Vane Kestrel", "Shanty Yard Saints", "arrogant")
    manager.reputation = 0
    low = manager.open_rival_dialogue(info).nodes["start"].text
    manager.reputation = 500
    high = manager.open_rival_dialogue(info).nodes["start"].text
    assert low != high


def test_personality_persists_through_save(manager, tmp_path, monkeypatch):
    """Luonne ja tausta säilyvät tallennuksessa."""
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE", str(tmp_path / "s.json"))

    manager.recruit_initial_hero()
    hero = list(manager.my_team)[0]
    hero.personality = "loyal"
    hero.origin = "Deserter"
    assert save_manager.save_game(manager)

    from game_manager import GameManager
    m2 = GameManager()
    assert save_manager.load_game(m2)
    h2 = list(m2.my_team)[0]
    assert h2.personality == "loyal"
    assert h2.origin == "Deserter"
