# tests/test_school_keepers.py
"""
Magiakoulujen pitajat: nelja yleiskeeperia (Pure/Holy/Druid/Manip) + Zharok
(Necromancy). Dialogit + admission (unlock_school-efekti) valmiina.
"""
import pytest


def _ctx():
    return {"my_data": {"flags": {}, "relationship": 0},
            "global_data": {"flags": {}, "reputation": 0, "magic": {"schools": []}},
            "player": {"name": "Hero", "gold": 0}}


def test_all_keepers_registered_with_lore_names():
    from npc.npc_registry import get_npc_class
    expect = {
        "keeper_pure": "Lysandra Voss",
        "keeper_holy": "Caldor Aurelian",
        "keeper_druid": "Maelis Rootspeaker",
        "keeper_manip": "Cassian Merrow",
    }
    for nid, frag in expect.items():
        cls = get_npc_class(nid)
        assert cls is not None, f"{nid} not registered"
        assert frag in cls().name


def test_keeper_admission_offers_unlock_effect():
    from npc.npc_registry import get_npc_class
    school_of = {"keeper_pure": "pure", "keeper_holy": "holy",
                 "keeper_druid": "druidism", "keeper_manip": "manipulation"}
    for nid, school in school_of.items():
        npc = get_npc_class(nid)()
        nodes = npc.get_nodes(_ctx())
        admit = nodes["admit"]
        effs = []
        for ch in admit.choices:
            effs += list(getattr(ch, "effects", []) or [])
        assert f"unlock_school:{school}" in effs, f"{nid} missing unlock effect"


def test_zharok_has_necromancy_admission():
    from npc.grand_mortarch import GrandMortarch
    z = GrandMortarch()
    ctx = {"player": {"name": "Hero"},
           "global_data": {"reputation": 0, "flags": {}},
           "my_data": {"flags": {"intro_done": True}, "relationship": 0}}
    nodes = z.get_nodes(ctx)
    assert "necro_admit" in nodes
    effs = []
    for ch in nodes["root_neutral"].choices:
        effs += list(getattr(ch, "effects", []) or [])
    assert "unlock_school:necromancy" in effs


def test_unlock_effect_opens_school(manager):
    # simuloi dialogin efektia suoraan managerin kautta
    manager.inventory["Spirit Essence"] = 5
    ok, _ = manager.try_unlock_school_with_resources("necromancy")
    assert ok and manager.is_school_unlocked("necromancy")
