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


# =========================================================
# TIER 0 -ARSENAALI
# Oikeat rekisterinimet (items/<group>/{scrap,weak}_*.py). Vanhat nimet
# kuten "Rusty Sword" EIVAT ole rekisterissa -> yksikko jai nyrkeille.
# scrap = lvl 1 (Tier 0 perus), iron = lvl 2 (Tier 0 eliitti).
# =========================================================
SCRAP_WEAPONS = {
    "sword": "Scrap Blade", "axe": "Dull Hatchet", "mace": "Heavy Branch",
    "spear": "Splintered Pole", "dagger": "Rusty Shiv", "bow": "Scrap Bow",
    "crossbow": "Jammed Crossbow", "staff": "Twisted Stick",
}
IRON_WEAPONS = {
    "sword": "Iron Sword", "axe": "Iron Axe", "mace": "Iron Mace",
    "spear": "Bent Spear", "dagger": "Iron Dagger", "bow": "Short Bow",
    "crossbow": "Light Crossbow", "staff": "Apprentice Staff",
}
# Blacksteel = lore Uncommon (Tier 2 / The Iron Circle). Ks. items/blacksteel/.
BLACKSTEEL_WEAPONS = {
    "sword": "Blacksteel Sword", "axe": "Blacksteel Axe", "mace": "Blacksteel Maul",
    "spear": "Blacksteel Pike", "dagger": "Blacksteel Dirk", "bow": "Yew Longbow",
    "crossbow": "Steel Crossbow", "staff": "Runed Staff",
}
SCRAP_SHIELD = "Pot Lid"
IRON_SHIELD = "Wooden Buckler"
BLACKSTEEL_SHIELD = "Blacksteel Shield"


def weapon_for(group, tier, elite=False):
    """Ryhman ase tierin mukaan (elite nostaa yhden pykalan):
    engine tier 1 = scrap, 2 = iron, >=3 = blacksteel."""
    t = int(tier) + (1 if elite else 0)
    if t >= 3:
        table = BLACKSTEEL_WEAPONS
    elif t == 2:
        table = IRON_WEAPONS
    else:
        table = SCRAP_WEAPONS
    return table.get(group, SCRAP_WEAPONS.get(group, "Scrap Blade"))


def shield_for(tier, elite=False):
    t = int(tier) + (1 if elite else 0)
    if t >= 3:
        return BLACKSTEEL_SHIELD
    if t == 2:
        return IRON_SHIELD
    return SCRAP_SHIELD


def build_team(name, color, tier, style, reputation, roster, motto=""):
    """DRY-rakentaja authored-tiimeille (Tier 1+). roster = lista dicteja:
      name, race('Human'/'Orc'/'Elf'/'Goblin'),
      weapon(group), shield(bool), armor('light'/'heavy'/'cloth'),
      cap(bool), elite(bool), scrap(bool), lvl(bonus),
      str/dex/int/hp/def (base_attributes-bonus), skills(list).
    Stat-bonukset menevat base_attributesiin (selviavat calc:sta)."""
    from units.human import Human
    from units.orc import Orc
    from units.elf import Elf
    from units.goblin import Goblin
    races = {"Human": Human, "Orc": Orc, "Elf": Elf, "Goblin": Goblin}
    try:
        from units.werewolf import Werewolf
        from units.tortle import Tortle
        races.update({"Werewolf": Werewolf, "Tortle": Tortle})
    except Exception:
        pass

    t = Team(name, color, tier)
    t.motto = motto
    t.style = style
    t.reputation = reputation
    t.authored = True
    base_lvl = max(1, 1 + tier * 2)

    for spec in roster:
        cls = races.get(spec.get("race", "Human"), Human)
        u = cls(spec["name"], 0, 0, color)
        u.level = base_lvl + spec.get("lvl", 0)
        for key, battr in (("str", "str"), ("dex", "dex"), ("int", "int"),
                           ("hp", "max_hp"), ("def", "def_flat")):
            if key in spec:
                u.base_attributes[battr] = u.base_attributes.get(battr, 0) + spec[key]
        for sk in spec.get("skills", []):
            u.unlocked_skills.add(sk)

        wg = spec.get("weapon")
        if wg:
            u.unlocked_skills.add(f"wp_{wg}")
            wname = (SCRAP_WEAPONS.get(wg) if spec.get("scrap")
                     else weapon_for(wg, tier, elite=spec.get("elite", False)))
            t.equip_unit(u, wname)
        if spec.get("shield"):
            u.unlocked_skills.add("arm_shield")
            t.equip_unit(u, shield_for(tier, elite=spec.get("elite", False)))

        armor = spec.get("armor", "light")
        if armor == "heavy":
            u.unlocked_skills.add("arm_heavy")
            t.equip_unit(u, "Rusty Mail")
            t.equip_unit(u, "Iron Helm")
        elif armor == "cloth":
            t.equip_unit(u, "Novice Robe")
        else:
            t.equip_unit(u, "Padded Vest")
            if spec.get("cap", True):
                t.equip_unit(u, "Leather Cap")

        u.calculate_final_stats()
        u.current_hp = u.max_hp

        # Loitsut (Tier 2+): asetetaan calc:n JALKEEN, koska calc nollaa
        # spell_slots/max_spell_tier skilleista.
        spells = spec.get("spells")
        if spells:
            u.spell_slots_unlocked = set(range(1, min(len(spells), 3) + 1))
            u.max_spell_tier = max(getattr(u, "max_spell_tier", 0), 1)
            u.max_mana = max(getattr(u, "max_mana", 20), 45)
            u.current_mana = u.max_mana
            for i, sp in enumerate(spells[:3], start=1):
                it = create_item(sp)
                if it:
                    u.equipment[f"spell{i}"] = it

        t.members.append(u)
    return t


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

    # Back-compat alias: `roster` seuraa aina `members`-listaa. (Aiemmin tama
    # oli kertaluontoinen viittaus, jonka premade-tiedostojen `t.members = []`
    # katkaisi -> league_enginen _safe_roster naki tyhjan listan.)
    @property
    def roster(self):
        return self.members

    @roster.setter
    def roster(self, value):
        self.members = value

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

        # Kilvet vaativat "shield"-proficiencyn weapon_masteriesissa (ks.
        # can_equip_item_to_slot). Kilvella on armor_group/type "shield",
        # EI weapon_group, joten yllaoleva ei kata tata -> lisataan tassa.
        # Ilman tata premade-tiimien kilvet EIVAT koskaan varustu.
        if str(getattr(it, "type", "")).lower() == "shield" or req_a == "shield":
            unit.weapon_masteries.add("shield")
            unit.unlocked_skills.add("arm_shield")

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
            w_name = "Scrap Blade"
            a_name = "Padded Vest"

            if i == 0:  # Tank
                w_name = "Dull Hatchet"
                a_name = "Rusty Mail"
            elif i == 1:  # Ranged
                w_name = "Jammed Crossbow"
                a_name = "Padded Vest"
            elif i == 3:  # Mage-ish
                w_name = "Twisted Stick"
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

    # 1.5) Lore-nimet: tiimit nimetään tierinsa kaanonin mukaan
    # (lore/world_data.py ARENA_TEAMS; game tier 1 = lore tier 0)
    try:
        from lore.world_data import get_tier_teams
        lore_teams = get_tier_teams(max(0, int(tier) - 1))
        for team, lore in zip(teams, lore_teams):
            # Authored-tiimeilla (Tier 1+) on jo lore-nimi ja maine -> ei nimeta uudelleen.
            if getattr(team, "authored", False):
                continue
            team.name = lore["name"]
            team.manager = lore.get("manager")
            team.lore_desc = lore.get("desc", "")
    except Exception as e:
        print(f"[League] Lore team naming skipped: {e}")

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
