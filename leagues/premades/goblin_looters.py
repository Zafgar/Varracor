# leagues/premades/goblin_looters.py
"""
Goblin Looters - Tier 0:n heikoin joukkue (C-taso). Nopea mutta hauras
gobliiniparvi: matala HP, ohut panssari, halvat aseet. Usein tykinruokaa.
"""
from leagues.league_data import Team, weapon_for
from units.goblin import Goblin


LOOTER_NAMES = ["Snik", "Grubb", "Pox", "Fizzle", "Wart"]


def create_team(tier):
    t = Team("Goblin Looters", (50, 160, 50), tier)
    t.motto = "Shiny things for us!"
    t.style = "Fragile Swarm"
    t.reputation = ("They don't fight to win - they fight to grab and run. "
                    "Cheap blades, cheaper courage, quick feet.")
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    for i, name in enumerate(LOOTER_NAMES):
        gob = Goblin(name, 0, 0, t.color)
        gob.level = base_lvl
        gob.base_attributes["dex"] += 4 + tier
        group = "dagger" if i % 2 == 0 else "sword"
        gob.unlocked_skills.update([f"wp_{group}", "dex_speed"])
        t.equip_unit(gob, weapon_for(group, tier))
        t.equip_unit(gob, "Leather Cap")
        gob.calculate_final_stats()
        gob.current_hp = gob.max_hp
        t.members.append(gob)

    return t
