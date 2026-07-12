# tests/test_gnome.py
"""
Gnome-rotu (Rattlebridgen paja-nikkari): oma yksikkoluokka, Spark Snare
-racial (Slow + Burn lahelle), save-map ja Cog Wardens -tinkeritiimi.
"""
import pytest
from settings import PLAYER_TEAM, ENEMY_TEAM


def test_gnome_unit_constructs():
    from units.gnome import Gnome
    g = Gnome("Pib", 0, 0, PLAYER_TEAM)
    assert g.race_name == "Gnome"
    assert g.image is not None


def test_gnome_in_save_map():
    from save_manager import _unit_class_map
    assert "Gnome" in _unit_class_map()


def test_gnome_spark_snare_debuffs_nearby():
    from units.gnome import Gnome
    from units.human import Human
    from game_manager import GameManager
    m = GameManager(); m.match_in_progress = True; m.current_arena = None
    g = Gnome("Pib", 300, 300, ENEMY_TEAM)
    foe = Human("F", 340, 300, PLAYER_TEAM)
    m.all_units.add(g, foe)
    g.racial_cooldown = 0
    assert g.use_racial_ability(manager=m) is True
    assert foe.has_status("Slow")
    assert foe.has_status("Burn")
    assert g.racial_cooldown > 0


def test_gnome_racial_works_without_manager():
    from units.gnome import Gnome
    g = Gnome("Pib", 0, 0, PLAYER_TEAM)
    g.racial_cooldown = 0
    assert g.use_racial_ability(manager=None) is True


def test_cog_wardens_team_features_gnomes():
    from leagues.premades.tier1.cog_wardens import create_team
    t = create_team(2)
    assert t.manager == "Yorik Sparkspanner"
    races = {u.race_name for u in t.members}
    assert "Gnome" in races
    assert "Dwarf" in races


def test_tier1_league_surfaces_gnome():
    from leagues.league_data import generate_league_teams
    races = set()
    for t in generate_league_teams(2):
        for u in t.members:
            races.add(u.race_name)
    assert "Gnome" in races
