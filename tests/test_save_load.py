# tests/test_save_load.py
"""Tallennusjärjestelmän round-trip-testi."""
import os

import save_manager


def test_save_load_roundtrip(manager, tmp_path, monkeypatch):
    # Ohjaa tallennus väliaikaishakemistoon
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE", str(tmp_path / "savegame.json"))

    from items.swords.weak_sword import WeakSword

    manager.recruit_initial_hero()
    hero = list(manager.my_team)[0]
    hero.level = 5
    hero.xp = 1234
    hero.skill_points = 3
    hero.unlocked_skills.add("sword_mastery")
    hero.equipment["main_hand"] = WeakSword()

    manager.gold = 4242
    manager.inventory["Rat Tail"] = 7
    manager.reputations["muckford"] = 15
    manager.player_character.level = 4
    manager.player_character.unlocked_skills.add("cmd_leadership")

    assert save_manager.save_game(manager) is True
    assert os.path.exists(save_manager.SAVE_FILE)

    # Lataa tuoreeseen manageriin
    from game_manager import GameManager
    m2 = GameManager()
    assert save_manager.load_game(m2) is True

    assert m2.gold == 4242
    assert m2.inventory.get("Rat Tail") == 7
    assert m2.reputations.get("muckford") == 15

    units = list(m2.my_team)
    assert len(units) == 1
    h2 = units[0]
    assert h2.name == "Hero"
    assert h2.level == 5
    assert h2.xp == 1234
    assert "sword_mastery" in h2.unlocked_skills
    assert type(h2.equipment["main_hand"]).__name__ == "WeakSword"

    assert m2.player_character.level == 4
    assert "cmd_leadership" in m2.player_character.unlocked_skills


def test_load_without_save_returns_false(manager, tmp_path, monkeypatch):
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE", str(tmp_path / "ei_ole.json"))
    assert save_manager.load_game(manager) is False
