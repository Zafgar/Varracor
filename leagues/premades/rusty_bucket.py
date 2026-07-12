# leagues/premades/rusty_bucket.py
"""
Rusty Buckets - konkarit. Pyorea, budjettivarusteinen viisikko (aiemmin vain
2 jasenta = bugi). B/C-taso. Asevalikoima laajalti: kirves, miekka, keihas,
kilpi, varsijousi.
"""
from leagues.league_data import Team, weapon_for, shield_for
from units.human import Human


def create_team(tier):
    t = Team("Rusty Buckets", (140, 100, 50), tier)
    t.motto = "Old but gold."
    t.style = "Balanced Veterans"
    t.reputation = ("Past their prime, but they've seen every trick twice. "
                    "Slow to impress, hard to fool.")
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    cap = Human("Buckethead", 0, 0, t.color)
    cap.level = base_lvl + 1
    cap.base_attributes["str"] += 4
    cap.unlocked_skills.update(["wp_axe", "arm_heavy", "str_tank"])
    t.equip_unit(cap, weapon_for("axe", tier))
    t.equip_unit(cap, "Rusty Mail")
    t.equip_unit(cap, "Iron Helm")
    cap.calculate_final_stats()
    cap.current_hp = cap.max_hp
    t.members.append(cap)

    shieldman = Human("Old Fenwick", 0, 0, t.color)
    shieldman.level = base_lvl
    shieldman.unlocked_skills.update(["wp_sword", "arm_shield"])
    t.equip_unit(shieldman, weapon_for("sword", tier))
    t.equip_unit(shieldman, shield_for(tier))
    t.equip_unit(shieldman, "Padded Vest")
    t.equip_unit(shieldman, "Leather Cap")
    shieldman.calculate_final_stats()
    shieldman.current_hp = shieldman.max_hp
    t.members.append(shieldman)

    spear = Human("Greaves", 0, 0, t.color)
    spear.level = base_lvl
    spear.unlocked_skills.update(["wp_spear"])
    t.equip_unit(spear, weapon_for("spear", tier))
    t.equip_unit(spear, "Padded Vest")
    t.equip_unit(spear, "Leather Cap")
    spear.calculate_final_stats()
    spear.current_hp = spear.max_hp
    t.members.append(spear)

    grunt = Human("Tobb", 0, 0, t.color)
    grunt.level = base_lvl
    grunt.unlocked_skills.update(["wp_sword"])
    t.equip_unit(grunt, weapon_for("sword", tier))
    t.equip_unit(grunt, "Padded Vest")
    grunt.calculate_final_stats()
    grunt.current_hp = grunt.max_hp
    t.members.append(grunt)

    bow = Human("Rusty Sal", 0, 0, t.color)
    bow.level = base_lvl
    bow.base_attributes["dex"] += 2
    bow.unlocked_skills.update(["wp_crossbow"])
    t.equip_unit(bow, weapon_for("crossbow", tier))
    t.equip_unit(bow, "Padded Vest")
    t.equip_unit(bow, "Leather Cap")
    bow.calculate_final_stats()
    bow.current_hp = bow.max_hp
    t.members.append(bow)

    return t
