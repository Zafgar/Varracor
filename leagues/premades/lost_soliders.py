from leagues.league_data import Team
from items.item_registry import create_item
from units.human import Human

def create_team(tier):
    t = Team("Lost Soldiers", (80, 80, 120), tier)
    t.motto = "Hold the line."
    t.style = "Defensive"
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    # 1. Kapteeni (Tank)
    cap = Human("Sergeant", 0, 0, t.color)
    cap.level = base_lvl + 1
    cap.strength += 3
    cap.unlocked_skills.update(["wp_sword", "arm_heavy", "arm_shield"])
    
    t.equip_unit(cap, "Rusty Sword")
    t.equip_unit(cap, "Wooden Shield") # Off-hand
    t.equip_unit(cap, "Rusty Mail")    # Heavy
    t.equip_unit(cap, "Iron Helm")
    
    cap.calculate_final_stats()
    cap.current_hp = cap.max_hp
    t.members.append(cap)

    # 2. Rivisotilaat (4 kpl)
    for i in range(4):
        sol = Human(f"Private {i+1}", 0, 0, t.color)
        sol.level = base_lvl
        sol.defense += 1 # Luonnostaan sitkeitä
        
        sol.unlocked_skills.update(["wp_sword", "arm_shield"])
        
        t.equip_unit(sol, "Rusty Sword")
        t.equip_unit(sol, "Wooden Shield")
        t.equip_unit(sol, "Padded Vest") # Light armor (budjetti)
        t.equip_unit(sol, "Leather Cap")
        
        sol.calculate_final_stats()
        sol.current_hp = sol.max_hp
        t.members.append(sol)

    return t