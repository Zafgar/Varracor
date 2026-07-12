# tests/test_vortex.py
"""
Vortex-taikuuden reaktiojarjestelma: kun hero kayttaa Vortexia, kyla huomaa,
pelastyy ja NPC:t alkavat kysella. Ensimmainen kaytto on iso lore-paljastus.
"""
import pytest


def test_first_vortex_use_reveals_and_records_deed(manager):
    assert manager.has_seen_vortex() is False
    first = manager.notice_vortex_use("combat")
    assert first is True
    assert manager.has_seen_vortex() is True
    assert manager.has_deed("vortex_revealed")


def test_second_use_not_first_but_counts(manager):
    manager.notice_vortex_use("combat")
    second = manager.notice_vortex_use("combat")
    assert second is False
    g = manager.npc_state["global"]
    assert g["vortex_uses"] == 2
    # deed ei duplikoidu
    deeds = [d for d in manager.get_deeds() if d["id"] == "vortex_revealed"]
    assert len(deeds) == 1


def test_vortex_fear_ticks_down(manager):
    manager.notice_vortex_use("combat")
    assert manager.vortex_fear_active() is True
    for _ in range(600):
        manager.tick_vortex_fear()
    assert manager.vortex_fear_active() is False


def test_vortex_state_persists_in_npc_state(manager):
    """vortex_seen elaa npc_state['global']issa -> tallentuu save-systeemiin."""
    manager.notice_vortex_use("combat")
    assert manager.npc_state["global"]["vortex_seen"] is True


def test_griznak_reacts_to_vortex():
    from npc.griznak_quest_giver import GriznakQuestGiver
    npc = GriznakQuestGiver()
    ctx_seen = {"global_data": {"vortex_seen": True, "deeds": []},
                "my_data": {"flags": {"intro_done": True}}}
    nodes = npc.get_nodes(ctx_seen)
    assert "Vortex" in nodes["root_normal"].text

    ctx_none = {"global_data": {"deeds": []},
                "my_data": {"flags": {"intro_done": True}}}
    nodes2 = npc.get_nodes(ctx_none)
    assert "Vortex" not in nodes2["root_normal"].text
