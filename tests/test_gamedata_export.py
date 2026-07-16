# tests/test_gamedata_export.py
"""Pelitesti 43: Godot-datapeili.
godot/data/*.json exportataan py-versiosta (totuuslähde). Nämä testit
vahtivat että peili on olemassa, validia JSONia ja arvot täsmäävät
py-toteutukseen - jos katalogeja muutetaan eikä exporttia ajeta,
testi kaatuu ja muistuttaa: python tools/export_gamedata.py
"""
import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((64, 64))

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "godot", "data")

STALE_HINT = "aja: python tools/export_gamedata.py"


def _load(name):
    path = os.path.join(DATA, name)
    assert os.path.exists(path), f"{name} puuttuu - {STALE_HINT}"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_all_export_files_exist_and_parse():
    for name in ("stat_curve.json", "spells.json", "gear.json",
                 "skill_tree.json", "shapeshift.json", "training.json"):
        data = _load(name)
        assert isinstance(data, dict) and data


def test_stat_curve_mirror_matches_python():
    from progression.stat_curve import stat_target, BASE, COEF, POWER
    d = _load("stat_curve.json")
    assert d["base"] == BASE and d["coef"] == COEF and d["power"] == POWER
    for lvl, val in d["samples"].items():
        assert stat_target(int(lvl)) == val, \
            f"stat_curve.json vanhentunut - {STALE_HINT}"


def test_spells_mirror_matches_python():
    from spells import spell_scaling as ss
    from spells.catalog import CATALOG
    d = _load("spells.json")
    assert len(d["catalog"]) == len(CATALOG), STALE_HINT
    ids = {s["id"] for s in d["catalog"]}
    assert "arcane_dart" in ids and "sun_flare" in ids
    for t in range(1, 9):
        assert d["tier_base"][str(t)] == ss.TIER_BASE[t], STALE_HINT
        assert d["tier_int_coef"][str(t)] == ss.TIER_INT_COEF[t], STALE_HINT
    # Godotin scaled_damage saa samat arvot samoista taulukoista:
    # tarkistetaan kaava käsin JSON-datalla
    import math
    tier, intel = 5, 300
    expect = ss.scaled_damage(tier, intel, "nuke")
    got = max(0, int(d["tier_base"][str(tier)] * d["archetype_mult"]["nuke"]
                     + intel * d["tier_int_coef"][str(tier)]
                     * d["archetype_mult"]["nuke"]))
    assert got == expect


def test_gear_mirror_matches_python():
    from items.gear_catalog import all_gear
    d = _load("gear.json")
    py_gear = {g.gear_id: g for g in all_gear()}
    assert len(d["items"]) == len(py_gear) == 72, STALE_HINT
    for item in d["items"]:
        g = py_gear[item["id"]]
        assert item["int_bonus"] == g.int_bonus, \
            f"{item['id']} vanhentunut - {STALE_HINT}"
        assert item["price"] == g.cost
        assert item["level_required"] == g.level_required


def test_skill_tree_and_forms_exported():
    from skills.skills_data import SKILL_TREE
    from spells.druid.shapeshift import FORMS
    st = _load("skill_tree.json")
    assert len(st["nodes"]) == len(SKILL_TREE), STALE_HINT
    sf = _load("shapeshift.json")
    assert set(sf["forms"].keys()) == set(FORMS.keys())
    assert sf["forms"]["bear"]["hp_mult"] == FORMS["bear"]["hp_mult"]


def test_godot_project_skeleton_present():
    root = os.path.dirname(DATA)
    for rel in ("project.godot", "scenes/main.tscn", "scripts/main.gd",
                "scripts/player.gd", "scripts/camera_rig.gd",
                "scripts/catalogs.gd"):
        assert os.path.exists(os.path.join(root, rel)), f"{rel} puuttuu"
    # Autoload rekisteröity
    with open(os.path.join(root, "project.godot"), encoding="utf-8") as f:
        proj = f.read()
    assert "Catalogs=" in proj and "main.tscn" in proj
