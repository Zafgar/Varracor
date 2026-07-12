# leagues/premades/drunken_brawlers.py
"""
Drunken Brawlers - Sunk Cask -kapakan orkkinyrkit. Iskevat kuin maanvyory
(korkea STR/HP), mutta ei kaukoasetta eika kilpia -> kiteavat viholliset
rankaisevat heita. A-tason lahitaisteluvoima.
"""
from leagues.league_data import Team, weapon_for
from units.orc import Orc


BRAWLER_NAMES = ["Grukk", "Morg the Barrel", "Balta", "Skad", "Ulf One-Ear"]


def create_team(tier):
    t = Team("Drunken Brawlers", (180, 100, 100), tier)
    t.motto = "More ale!"
    t.style = "Tanky Melee"
    t.reputation = ("Sunk Cask regulars who settle tabs with their fists. Hit "
                    "like a landslide, guard like nobody's home.")
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    for i, name in enumerate(BRAWLER_NAMES):
        orc = Orc(name, 0, 0, t.color)
        orc.level = base_lvl
        orc.strength += 4 + tier
        orc.max_hp += 30
        group = "mace" if i % 2 == 0 else "axe"
        orc.unlocked_skills.update([f"wp_{group}", "str_tank"])
        t.equip_unit(orc, weapon_for(group, tier))
        t.equip_unit(orc, "Padded Vest")
        t.equip_unit(orc, "Viking Helmet")
        orc.calculate_final_stats()
        orc.current_hp = orc.max_hp
        t.members.append(orc)

    return t
