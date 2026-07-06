from leagues.league_data import Team
from items.item_registry import create_item
from units.human import Human

def create_team(tier):
    t = Team("Rusty Buckets", (140, 100, 50), tier, is_player=False)
    t.motto = "Old but gold."
    t.members = []
    
    base_lvl = max(1, 1 + tier * 2)

    # --- KAPTEENI (Tank) ---
    cap = Human("Buckethead", 0, 0, t.color)
    cap.level = base_lvl
    cap.strength += 5
    
    # Skillit (AI tarvitsee nämä käyttääkseen kamoja)
    cap.unlocked_skills.add("wp_axe")
    cap.unlocked_skills.add("arm_heavy")
    
    # Varusteet (UUDET NIMET)
    # Varmista, että nämä on item_registryssä!
    t.equip_unit(cap, "Woodcutter's Axe")
    t.equip_unit(cap, "Rusty Mail") 
    t.equip_unit(cap, "Iron Helm")
    
    cap.calculate_final_stats()
    cap.current_hp = cap.max_hp
    t.members.append(cap)

    # --- ALOKAS (Rogue) ---
    recruit = Human("Scrap", 0, 0, t.color)
    recruit.level = base_lvl
    
    # Varusteet
    t.equip_unit(recruit, "Rusty Sword")
    t.equip_unit(recruit, "Padded Vest") # Light Armor
    
    recruit.calculate_final_stats()
    recruit.current_hp = recruit.max_hp
    t.members.append(recruit)
    
    # Täytä loput geneerisillä jos tarvis (tai tee loop)
    # Tässä tehdään vain 2 esimerkkiä
    return t