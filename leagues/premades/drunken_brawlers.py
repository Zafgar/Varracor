from leagues.league_data import Team
from items.item_registry import create_item
from units.orc import Orc

def create_team(tier):
    t = Team("Drunken Brawlers", (180, 100, 100), tier)
    t.motto = "More ale!"
    t.style = "Tanky Melee"
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    for i in range(5):
        orc = Orc(f"Brawler {i+1}", 0, 0, t.color)
        orc.level = base_lvl
        
        # Paljon voimaa ja HP
        orc.strength += 4 + tier
        orc.max_hp += 30
        
        # Skillit
        orc.unlocked_skills.update(["wp_axe", "wp_mace", "str_tank"])
        
        # Varusteet (Sekoitus kirveitä ja nuijia jos nuijat tehty, muuten kirveitä)
        # Oletetaan että "War Mace" ei ehkä ole vielä Level 1 itemeissä, käytetään kirveitä.
        t.equip_unit(orc, "Woodcutter's Axe")
        
        # Ei paitaa! (Brawlers) Tai kevyt liivi.
        t.equip_unit(orc, "Padded Vest")
        
        # Viiking kypärä sopii näille
        t.equip_unit(orc, "Viking Helmet") 
        
        orc.calculate_final_stats()
        orc.current_hp = orc.max_hp
        t.members.append(orc)

    return t