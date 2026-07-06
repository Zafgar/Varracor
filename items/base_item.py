import pygame

class Item:
    def __init__(self):
        self.name = "Unknown Item"
        self.rarity = "Common"
        self.cost = 10
        self.level_required = 1
        self.type = "misc"
        self.slot_type = "bag" # Oletus: menee reppuun
        self.description = ""
        
        # Charging mechanics
        self.charge_time = 0
        self.max_charge = 60
        self.charge_enabled = False
        
        # UI-värit
        self.base_image = None
        self.icon_color = (100, 100, 100)

    def draw_card_icon(self, surface, x, y, size):
        # Oletuslaatikko
        pygame.draw.rect(surface, (50, 50, 50), (x, y, size, size))
        pygame.draw.rect(surface, (200, 200, 200), (x, y, size, size), 2)

    def get_swing_rect(self, unit_rect, facing_right, attack_timer, total_cooldown, attack_vector=None):
        # define dmg box during attack animation
        swing_rect = pygame.Rect(unit_rect.x,unit_rect.y,50,50)
        return swing_rect

    def on_update(self, owner, all_units, manager):
        # Kutsutaan joka frame (esim. aurat)
        pass
        
    def update_charge(self, owner, manager):
        # Kutsutaan kun pelaaja pitää nappia pohjassa
        pass
        
    def release_charge(self, owner, manager, target_pos):
        # Kutsutaan kun pelaaja päästää napin
        pass

class Weapon(Item):
    def __init__(self):
        super().__init__()
        self.type = "melee"
        self.slot_type = "main_hand"
        self.weapon_group = "" # "sword", "axe", "book", etc.
        
        self.damage = 1
        self.attack_range = 30
        self.speed_bonus = 0.0
        
        # Skaalaus (esim. {'STR': 0.5})
        self.scaling = {} 
        self.weapon_effect = "damage"

    def calculate_damage(self, stats):
        # Base damage
        dmg = self.damage
        
        # Skaalaus
        str_val = stats.get("str", 10)
        dex_val = stats.get("dex", 10)
        int_val = stats.get("int", 10)
        
        bonus = 0.0
        if self.scaling:
            bonus += str_val * self.scaling.get("STR", 0.0)
            bonus += dex_val * self.scaling.get("DEX", 0.0)
            bonus += int_val * self.scaling.get("INT", 0.0)
            
        return int(dmg + bonus)

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer, total_cooldown=60, attack_vector=None):
        pass

    def on_attack_start(self, attacker, target, manager):
        pass

    def on_hit(self, attacker, target, damage_dealt, manager):
        pass

# Armor-luokka rekisteröintiä varten
class Armor(Item):
    def __init__(self):
        super().__init__()
        self.type = "armor"
        self.slot_type = "body"
        self.armor_group = "cloth"
        
        self.defense = 0
        self.health_bonus = 0
        self.mana_bonus = 0
        self.speed_bonus = 0.0

    def draw_equipped(self, surface, unit_rect, facing_right, attack_timer):
        pass

class Spell(Item):
    def __init__(self):
        super().__init__()
        self.type = "spell"
        self.slot_type = "spell1" # Default slot
        self.mana_cost = 10
        self.cooldown_max = 60
        self.range = 300
        self.damage = 10
        self.scaling = {"INT": 1.0}
        
        # Projectile settings
        self.is_skillshot = True
        self.projectile_speed = 10
        self.projectile_color = (100, 150, 255)
        self.projectile_size = 10

    def cast(self, caster, target, manager, target_pos=None):
        """Default cast implementation for projectile spells."""
        if self.is_skillshot:
            # Determine target position
            if not target_pos and target:
                target_pos = target.rect.center
            
            if target_pos:
                dmg = self.damage + (caster.intelligence * self.scaling.get("INT", 0))
                from vfx import MagicProjectile
                proj = MagicProjectile(caster.rect.centerx, caster.rect.centery, target_pos, self.projectile_speed, int(dmg), caster, manager, color=self.projectile_color, size=self.projectile_size)
                manager.vfx.add_projectile(proj)
                return True
        return False