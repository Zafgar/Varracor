import random
from leagues.league_data import Team
from items.item_registry import create_item
from units.goblin import Goblin
from units.human import Human

def create_team(tier):
    t = Team("Arena Rats", (100, 100, 100), tier)
    t.motto = "Fight dirty."
    t.style = "Evasive"
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    for i in range(5):
        # 50/50 Human tai Goblin
        if random.random() < 0.5:
            u = Goblin(f"Rat {i+1}", 0, 0, t.color)
        else:
            u = Human(f"Scoundrel {i+1}", 0, 0, t.color)
            
        u.level = base_lvl
        u.dexterity += 5
        
        # Skillit: Sword (tikari) ja Dual Wield (jos itemit sallii)
        u.unlocked_skills.update(["wp_sword", "dex_dodge"])
        
        # Varustus
        t.equip_unit(u, "Rusty Sword")
        t.equip_unit(u, "Padded Vest")
        
        # Mahdollisuus "Off-hand sword" jos dual wield sallittu
        # (Vaatisi can_dual_wield skillin, lisätään se varmuuden vuoksi)
        if random.random() < 0.3:
            u.unlocked_skills.add("can_dual_wield")
            # equip_item laittaa automaattisesti off-handiin jos main on täynnä?
            # Gladiator.equip_item logiikka laittaa main_handiin oletuksena.
            # Käytetään manuaalista off-handia:
            off = create_item("Rusty Sword")
            if off: u.equip_item_to_slot("off_hand", off)

        u.calculate_final_stats()
        u.current_hp = u.max_hp
        t.members.append(u)

    return t