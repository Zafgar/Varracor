# tests/test_vortex_mentor.py
"""
Tia Muir - Vortex-mentori joka vei heron muistin ja opettaa hanelle Abyssal
Weaven (Tia Muira). Moraalisesti harmaa; opetukset avaavat taitopuut.
"""
import pytest


def _ctx(learned=None):
    return {"my_data": {"flags": {}, "relationship": 0},
            "global_data": {"flags": {}, "reputation": 0,
                            "magic": {"abyssal_trees": list(learned or [])}},
            "player": {"name": "?"}}


def test_mentor_registered():
    from npc.npc_registry import get_npc_class
    cls = get_npc_class("vortex_mentor")
    assert cls is not None
    assert cls().name == "Tia Muir"


def test_first_meeting_then_hub():
    from npc.vortex_mentor import VortexMentor
    m = VortexMentor()
    # ei tavattu -> first_meeting
    assert m.get_dialogue_root(_ctx()) == "first_meeting"
    # tavattu -> hub
    ctx = _ctx()
    ctx["my_data"]["flags"]["met_before"] = True
    assert m.get_dialogue_root(ctx) == "hub"


def test_each_lesson_teaches_its_tree():
    from npc.vortex_mentor import VortexMentor, LESSONS
    m = VortexMentor()
    nodes = m.get_nodes(_ctx())
    for tree in LESSONS:
        node = nodes[f"lesson_{tree}"]
        assert f"learn_abyssal:{tree}" in node.on_enter_effects


def test_known_lesson_does_not_reteach():
    from npc.vortex_mentor import VortexMentor
    m = VortexMentor()
    nodes = m.get_nodes(_ctx(learned=["warping"]))
    # jo opittu -> ei enaa learn-efektia
    assert "learn_abyssal:warping" not in nodes["lesson_warping"].on_enter_effects


def test_mentor_is_morally_grey():
    """Mentori ei syyta Vortex-olentoja ja on 'ehka oikeassa'."""
    from npc.vortex_mentor import VortexMentor
    m = VortexMentor()
    nodes = m.get_nodes(_ctx())
    text = " ".join(n.text for n in nodes.values()).lower()
    assert "mirror" in text or "not clean" in text or "right" in text


def test_learn_abyssal_via_manager(manager):
    for tree in ("warping", "anchoring", "severing", "echoing", "taint"):
        assert manager.knows_abyssal_tree(tree) is False
        assert manager.learn_abyssal_tree(tree) is True
        assert manager.knows_abyssal_tree(tree) is True
