from leagues.league_data import Team
from items.item_registry import create_item
from units.goblin import Goblin

def create_team(tier):
    t = Team("Goblin Looters", (50, 160, 50), tier)
    t.motto = "Shiny things for us!"
    t.style = "Swarm"
    t.members = []
    
    base_lvl = max(1, 1 + tier * 2)

    # 5 Goblinia
    for i in range(5):
        name = f"Snatch {i+1}"
        gob = Goblin(name, 0, 0, t.color)
        gob.level = base_lvl
        
        # Goblinit ovat nopeita
        gob.dexterity += 4 + tier
        
        # Skillit
        gob.unlocked_skills.add("wp_sword") # Käyttävät Rusty Swordia tikarina
        gob.unlocked_skills.add("dex_speed")
        
        # Varusteet
        t.equip_unit(gob, "Rusty Sword")
        t.equip_unit(gob, "Padded Vest")
        t.equip_unit(gob, "Leather Cap")
        
        gob.calculate_final_stats()
        gob.current_hp = gob.max_hp
        t.members.append(gob)
        
    return t