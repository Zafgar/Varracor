# tests/test_magic_progression.py
"""
Magian eteneminen: Pure auki heti, muut koulut quest-linjoina (resurssi +
maine + pitaja), Abyssal-taitopuut lore-tapahtumista. Tila tallentuu.
"""
import pytest


def test_pure_open_by_default(manager):
    assert manager.is_school_unlocked("pure") is True


def test_special_schools_locked_initially(manager):
    for s in ("necromancy", "holy", "druidism", "manipulation"):
        assert manager.is_school_unlocked(s) is False


def test_unlock_requires_resource(manager):
    ok, reason = manager.try_unlock_school_with_resources("necromancy")
    assert ok is False
    assert "Spirit Essence" in reason
    assert manager.is_school_unlocked("necromancy") is False


def test_unlock_with_resource_spends_and_opens(manager):
    manager.inventory["Spirit Essence"] = 6
    ok, msg = manager.try_unlock_school_with_resources("necromancy")
    assert ok is True
    assert manager.inventory["Spirit Essence"] == 1  # 6 - 5
    assert manager.is_school_unlocked("necromancy") is True
    assert manager.has_deed("school_necromancy")


def test_unlock_state_persists_in_npc_state(manager):
    manager.inventory["Spirit Essence"] = 5
    manager.try_unlock_school_with_resources("necromancy")
    assert "necromancy" in manager.npc_state["global"]["magic"]["schools"]


def test_abyssal_trees_learned_via_lore(manager):
    assert manager.knows_abyssal_tree("warping") is False
    assert manager.learn_abyssal_tree("warping") is True
    assert manager.knows_abyssal_tree("warping") is True
    # ei duplikoidu
    assert manager.learn_abyssal_tree("warping") is False


def test_unlock_requirement_text():
    from magic.progression import unlock_requirement_text
    assert "Spirit Essence" in unlock_requirement_text("necromancy")
    assert unlock_requirement_text("pure") == "Open to all"
