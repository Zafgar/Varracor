import random
from leagues.league_data import Team
from items.item_registry import create_item
from units.human import Human
from units.orc import Orc

def create_team(tier):
    t = Team("Bandit Clan", (100, 40, 40), tier)
    t.motto = "Your gold or your life."
    t.style = "Aggressive"
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    # 1. Bandit Chief (Orc)
    boss = Orc("Chief", 0, 0, t.color)
    boss.level = base_lvl + 1
    boss.strength += 6
    boss.unlocked_skills.update(["wp_axe", "str_execute"])
    
    t.equip_unit(boss, "Woodcutter's Axe")
    t.equip_unit(boss, "Padded Vest") # Bandiitit eivät käytä heavy armoria
    t.equip_unit(boss, "Iron Helm")
    
    boss.calculate_final_stats()
    boss.current_hp = boss.max_hp
    t.members.append(boss)

    # 2. Marauders (2 kpl, Melee Humans)
    for i in range(2):
        man = Human(f"Marauder {i+1}", 0, 0, t.color)
        man.level = base_lvl
        man.strength += 2
        man.unlocked_skills.update(["wp_axe"])
        
        t.equip_unit(man, "Woodcutter's Axe")
        t.equip_unit(man, "Padded Vest")
        
        man.calculate_final_stats()
        man.current_hp = man.max_hp
        t.members.append(man)

    # 3. Poachers (2 kpl, Ranged Humans)
    for i in range(2):
        bow = Human(f"Poacher {i+1}", 0, 0, t.color)
        bow.level = base_lvl
        bow.dexterity += 3
        bow.unlocked_skills.update(["wp_crossbow"])
        
        t.equip_unit(bow, "Weak Crossbow")
        t.equip_unit(bow, "Padded Vest")
        t.equip_unit(bow, "Leather Cap")
        
        bow.calculate_final_stats()
        bow.current_hp = bow.max_hp
        t.members.append(bow)

    return t