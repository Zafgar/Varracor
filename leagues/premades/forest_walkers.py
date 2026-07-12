# leagues/premades/forest_walkers.py
"""
Forest Walkers - Wyrdwoodin haltiajoukkue. Lasitykki-kaukotaistelu:
jousiampujat + sauvaa heiluttava druidi. Kova DPS, mutta hauras. Ei loitsuja
viela Tier 0:ssa - sauva on lyoma/kaukoase. B-taso.
"""
from leagues.league_data import Team, weapon_for
from units.elf import Elf


RANGER_NAMES = ["Aeric", "Sylas", "Thanic", "Wrenna"]


def create_team(tier):
    t = Team("Forest Walkers", (30, 100, 30), tier)
    t.motto = "The woods have eyes."
    t.style = "Ranged / Kiting"
    t.reputation = ("Wyrdwood-born hunters. They kite you into the dark and "
                    "pick you apart - but pin them down and they break.")
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    druid = Elf("Elowen", 0, 0, t.color)
    druid.level = base_lvl
    druid.intelligence += 5
    druid.unlocked_skills.update(["wp_staff", "int_mana"])
    t.equip_unit(druid, weapon_for("staff", tier))
    t.equip_unit(druid, "Novice Robe")
    druid.calculate_final_stats()
    druid.current_hp = druid.max_hp
    druid.current_mana = druid.max_mana
    t.members.append(druid)

    for name in RANGER_NAMES:
        ranger = Elf(name, 0, 0, t.color)
        ranger.level = base_lvl
        ranger.dexterity += 4
        ranger.unlocked_skills.update(["wp_bow", "dex_crit"])
        t.equip_unit(ranger, weapon_for("bow", tier))
        t.equip_unit(ranger, "Padded Vest")
        t.equip_unit(ranger, "Leather Cap")
        ranger.calculate_final_stats()
        ranger.current_hp = ranger.max_hp
        t.members.append(ranger)

    return t
