# leagues/league_data.py
import random
from settings import *
from items.item_registry import create_item

# New modular loader (optional)
try:
    from leagues.team_loader import load_all_premade_teams
except ImportError:
    load_all_premade_teams = None

# Unit classes
try:
    from units.human import Human
    from units.orc import Orc
    from units.elf import Elf
    from units.goblin import Goblin
except ImportError:
    from gladiator import Gladiator
    Human = Orc = Elf = Goblin = Gladiator


LEAGUE_NAMES = [
    "Iron League", "Bronze League", "Silver League",
    "Gold League", "Platinum League", "Diamond League"
]


class Team:
    """
    League team container for premades + fallback generation.

    NOTE:
    - Primary roster list is `members` (your newer code).
    - For backwards compatibility, `roster` is an alias of members.
    """
    def __init__(self, name, color, tier=0, is_player=False, team_id=None):
        self.name = name
        self.color = color
        self.tier = tier
        self.is_player = is_player

        # Optional stable id for league engine
        self.team_id = team_id

        # Simple UI fields
        self.motto = ""
        self.style = "Balanced"

        # Roster
        self.members = []

        # Back-compat alias
        self.roster = self.members

    def _ensure_sets(self, unit):
        # Make sure common containers exist on Gladiator-like units
        if not hasattr(unit, "unlocked_skills") or unit.unlocked_skills is None:
            unit.unlocked_skills = set()
        if not hasattr(unit, "weapon_masteries") or unit.weapon_masteries is None:
            unit.weapon_masteries = set()
        if not hasattr(unit, "armor_masteries") or unit.armor_masteries is None:
            unit.armor_masteries = set()
        if not hasattr(unit, "can_dual_wield") or unit.can_dual_wield is None:
            unit.can_dual_wield = False

    def equip_unit(self, unit, item_name):
        """Safe helper: creates item and equips. Also grants profs for premades/fallback."""
        it = create_item(item_name)
        if not it:
            return

        self._ensure_sets(unit)

        # Grant profs based on item groups
        req_w = getattr(it, "weapon_group", None)
        if req_w:
            # Your skill tree uses wp_* keys; and Gladiator uses weapon_masteries set.
            unit.weapon_masteries.add(req_w)
            unit.unlocked_skills.add(f"wp_{req_w}")
            unit.unlocked_skills.add(f"prof_{req_w}")  # keep legacy key too
            # Shield is treated as weapon_group="shield" in your design
            if req_w == "shield":
                unit.weapon_masteries.add("shield")

        req_a = getattr(it, "armor_group", None)
        if req_a:
            unit.armor_masteries.add(req_a)
            unit.unlocked_skills.add(f"armor_{req_a}")
            unit.unlocked_skills.add(f"prof_{req_a}")

        # Equip
        try:
            unit.equip_item(it)
        except Exception:
            # Some units may lack equip_item; ignore
            pass

    def _generate_fallback_roster(self):
        """
        Used only when premade files are missing.
        Uses your updated item names.
        """
        count = 5
        base_lvl = 1 + (self.tier * 2)

        for i in range(count):
            g_name = f"{self.name.split(' ')[0]} {i+1}"
            UnitClass = Human  # default

            g = UnitClass(g_name, 0, 0, self.color)
            g.level = max(1, base_lvl + random.randint(-1, 1))

            # Defaults
            w_name = "Rusty Sword"
            a_name = "Padded Vest"

            if i == 0:  # Tank
                w_name = "Weak Axe"
                a_name = "Rusty Mail"
            elif i == 1:  # Ranged
                w_name = "Weak Crossbow"
                a_name = "Padded Vest"
            elif i == 3:  # Mage-ish
                w_name = "Novice Staff"
                a_name = "Novice Robe"

            self.equip_unit(g, w_name)
            self.equip_unit(g, a_name)

            if hasattr(g, "calculate_final_stats"):
                g.calculate_final_stats()
            g.current_hp = getattr(g, "max_hp", 100)

            self.members.append(g)

        # keep alias synced
        self.roster = self.members

    def get_roster(self, size):
        return self.members[:size]


def generate_league_teams(tier):
    """
    Called by league_engine.

    1) Tries to load premade teams from disk (team_loader).
    2) If none exist, creates a few generic teams (fallback).
    """
    teams = []

    # 1) Premades
    if load_all_premade_teams:
        try:
            teams = load_all_premade_teams(tier)
        except Exception:
            teams = []

    # 2) Fallback
    if not teams:
        print("WARNING: No premade teams found. Generating generic teams.")
        base_data = [
            {"name": "Rusty Buckets", "color": (140, 100, 50)},
            {"name": "Goblin Looters", "color": (50, 160, 50)},
            {"name": "Lost Soldiers", "color": (80, 80, 120)},
        ]
        for data in base_data:
            t = Team(data["name"], data["color"], tier=tier, is_player=False)
            teams.append(t)

    return teams
