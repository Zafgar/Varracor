# Tier 2 - The Iron Circle
"""Shellwall Sentinels - Tortle-muuri. Erittain sitkea, hidas (maces + kilvet +
Shell Guard). Tier 2:n paras puolustus (A+). Uusi rotu esille."""
from leagues.league_data import build_team


def create_team(tier):
    return build_team(
        "Shellwall Sentinels", (70, 130, 90), tier,
        "Living Bulwark",
        "A wall of shelled sentinels that simply will not fall. Break every weapon "
        "you own on them - they wait, and then they crush.",
        [
            {"name": "Elder Bartok", "race": "Tortle", "weapon": "mace",
             "shield": True, "armor": "heavy", "elite": True, "lvl": 1, "def": 1},
            {"name": "Stoneshell", "race": "Tortle", "weapon": "mace",
             "shield": True, "armor": "heavy"},
            {"name": "Ironback", "race": "Tortle", "weapon": "mace",
             "shield": True, "armor": "heavy"},
            {"name": "Reed Warden", "race": "Human", "weapon": "spear",
             "shield": True, "def": 1},
            {"name": "Fen Warden", "race": "Human", "weapon": "spear", "shield": True},
        ],
        motto="We do not yield.")
