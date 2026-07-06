from leagues.league_data import Team
from items.item_registry import create_item
from units.elf import Elf

def create_team(tier):
    t = Team("Forest Walkers", (30, 100, 30), tier)
    t.motto = "The woods have eyes."
    t.style = "Ranged/Kiting"
    t.members = []
    base_lvl = max(1, 1 + tier * 2)

    # 1. Druid (Mage/Healer)
    druid = Elf("Druid", 0, 0, t.color)
    druid.level = base_lvl
    druid.intelligence += 5
    druid.unlocked_skills.update(["wp_staff", "spell_slot_1", "int_mana"])
    
    t.equip_unit(druid, "Novice Staff")
    t.equip_unit(druid, "Novice Robe")
    # Jos sinulla on "Minor Heal", lisää se tähän:
    # item = create_item("MinorHeal")
    # if item: druid.equip_item_to_slot("spell1", item)
    
    druid.calculate_final_stats()
    druid.current_hp = druid.max_hp
    druid.current_mana = druid.max_mana
    t.members.append(druid)

    # 2. Rangers (4 kpl)
    for i in range(4):
        ranger = Elf(f"Ranger {i+1}", 0, 0, t.color)
        ranger.level = base_lvl
        ranger.dexterity += 4
        ranger.unlocked_skills.update(["wp_crossbow", "dex_crit"])
        
        t.equip_unit(ranger, "Weak Crossbow")
        t.equip_unit(ranger, "Padded Vest")
        t.equip_unit(ranger, "Leather Cap")
        
        ranger.calculate_final_stats()
        ranger.current_hp = ranger.max_hp
        t.members.append(ranger)

    return t