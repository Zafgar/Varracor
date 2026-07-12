# leagues/premades/lost_soliders.py
"""
Lost Soldiers - Tier 0:n CHAMPION-kaliiberin joukkue.
Kurinalainen kilpimuuri + keihassselusta. Kayttaa iron-tason (lvl 2)
varusteita = Tier 0:n paras, mutta silti pelkkaa Tier 0 -kamaa, joten
Tier 1:ssa he tippuisivat takaisin. Ei loitsuja (Tier 0).
"""
from leagues.league_data import Team, weapon_for, shield_for
from units.human import Human


def create_team(tier):
    t = Team("Lost Soldiers", (80, 80, 120), tier)
    t.motto = "Hold the line."
    t.style = "Defensive Shield Wall"
    t.reputation = ("Ex-Heartlands levy that never broke formation. The crowd "
                    "bets safe on them - disciplined, armored, patient.")
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    def soldier(name, weapon_group, shield=True, heavy=False, lvl=None, extra=()):
        u = Human(name, 0, 0, t.color)
        u.level = lvl or base_lvl
        u.unlocked_skills.update((f"wp_{weapon_group}",) + tuple(extra))
        t.equip_unit(u, weapon_for(weapon_group, tier, elite=True))
        if shield:
            u.unlocked_skills.add("arm_shield")
            t.equip_unit(u, shield_for(tier, elite=True))
        if heavy:
            u.unlocked_skills.add("arm_heavy")
            t.equip_unit(u, "Rusty Mail")
            t.equip_unit(u, "Iron Helm")
        else:
            t.equip_unit(u, "Padded Vest")
            t.equip_unit(u, "Leather Cap")
        u.calculate_final_stats()
        u.current_hp = u.max_hp
        t.members.append(u)
        return u

    sergeant = soldier("Sergeant Halbrek", "sword", shield=True, heavy=True,
                       lvl=base_lvl + 1, extra=("str_tank",))
    sergeant.strength += 3
    soldier("Corporal Dane", "sword", shield=True, heavy=True, extra=("str_tank",))
    soldier("Osmund", "sword", shield=True, heavy=False)
    spearman = soldier("Halric", "spear", shield=False, heavy=False)
    spearman.defense += 1
    soldier("Wesk the Steady", "sword", shield=True, heavy=False)

    return t
