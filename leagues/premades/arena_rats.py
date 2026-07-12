# leagues/premades/arena_rats.py
"""
Arena Rats - Shanty Yardin katutappelijat (gobliineja ja ihmisia sekaisin).
Tikarit, vaistely ja likaiset kaksoisaseet. B/C-taso: nopeita ja arsyttavia,
mutta ohut panssari.
"""
import random
from leagues.league_data import Team, weapon_for
from items.item_registry import create_item
from units.goblin import Goblin
from units.human import Human


RAT_NAMES = ["Scab", "Nettle", "Grin", "Two-Tooth", "Sniv"]


def create_team(tier):
    t = Team("Arena Rats", (100, 100, 100), tier)
    t.motto = "Fight dirty."
    t.style = "Evasive Duelists"
    t.reputation = ("Gutter-fighters with no honor and all elbows. Half of them "
                    "owe Old Rinna money; all of them carry a hidden blade.")
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    for i, base_name in enumerate(RAT_NAMES):
        if i % 2 == 0:
            u = Goblin(base_name, 0, 0, t.color)
        else:
            u = Human(base_name, 0, 0, t.color)
        u.level = base_lvl
        u.base_attributes["dex"] += 5
        u.unlocked_skills.update(["wp_dagger", "dex_dodge"])

        t.equip_unit(u, weapon_for("dagger", tier))
        t.equip_unit(u, "Padded Vest")

        if random.random() < 0.4:
            u.unlocked_skills.add("can_dual_wield")
            off = create_item(weapon_for("dagger", tier))
            if off:
                u.equip_item_to_slot("off_hand", off)

        u.calculate_final_stats()
        u.current_hp = u.max_hp
        t.members.append(u)

    return t
