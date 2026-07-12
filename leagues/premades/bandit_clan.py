# leagues/premades/bandit_clan.py
"""
Bandit Clan - tietullirosvot. Tasapainoinen: orkkipaallikko + kirvesmiehet
edessa, jousiampujat (varsijousi) takana. A/B-taso, aggressiivinen.
"""
from leagues.league_data import Team, weapon_for
from units.human import Human
from units.orc import Orc


def create_team(tier):
    t = Team("Bandit Clan", (100, 40, 40), tier)
    t.motto = "Your gold or your life."
    t.style = "Aggressive Skirmish"
    t.reputation = ("Road-toll cutthroats. Bram tolerates them because they "
                    "draw a bloodthirsty crowd - and pay their fines.")
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    boss = Orc("Red Corla", 0, 0, t.color)
    boss.level = base_lvl + 1
    boss.base_attributes["str"] += 6
    boss.unlocked_skills.update(["wp_axe", "str_execute"])
    t.equip_unit(boss, weapon_for("axe", tier, elite=True))
    t.equip_unit(boss, "Padded Vest")
    t.equip_unit(boss, "Iron Helm")
    boss.calculate_final_stats()
    boss.current_hp = boss.max_hp
    t.members.append(boss)

    for name in ("Vench", "Dob the Hook"):
        man = Human(name, 0, 0, t.color)
        man.level = base_lvl
        man.base_attributes["str"] += 2
        man.unlocked_skills.update(["wp_axe"])
        t.equip_unit(man, weapon_for("axe", tier))
        t.equip_unit(man, "Padded Vest")
        t.equip_unit(man, "Leather Cap")
        man.calculate_final_stats()
        man.current_hp = man.max_hp
        t.members.append(man)

    for name in ("Sly Ada", "Fenn"):
        bow = Human(name, 0, 0, t.color)
        bow.level = base_lvl
        bow.base_attributes["dex"] += 3
        bow.unlocked_skills.update(["wp_crossbow"])
        t.equip_unit(bow, weapon_for("crossbow", tier))
        t.equip_unit(bow, "Padded Vest")
        t.equip_unit(bow, "Leather Cap")
        bow.calculate_final_stats()
        bow.current_hp = bow.max_hp
        t.members.append(bow)

    return t
