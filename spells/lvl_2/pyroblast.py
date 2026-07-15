import pygame
from spells.base_spell import Spell
from sound_manager import sound_system

class Pyroblast(Spell):
    def __init__(self):
        super().__init__()
        self.name = "Pyroblast"
        self.description = "A massive ball of magma. Requires Lvl 2."
        
        # --- TIER 2 VAATIMUKSET ---
        self.tier = 2           # Hahmon on oltava vähintään level 2
        self.rarity = "Epic"    # Violetti
        self.cost = 600         # Kallis kaupassa
        
        # Stats
        self.mana_cost = 50     # Vie paljon manaa
        self.cooldown_max = 300 # 5 sekuntia (hidas)
        self.range = 350
        self.base_damage = 60   # Kova vahinko (Fireball oli n. 20)

        self.slot_type = "spell"
        self.icon_color = (180, 40, 10)

    def draw_icon(self, surface, x, y, size):
        # Tumma tausta
        pygame.draw.rect(surface, (40, 10, 5), (x, y, size, size), border_radius=5)
        
        # Iso tulipallo
        cx, cy = x + size // 2, y + size // 2
        pygame.draw.circle(surface, (255, 50, 0), (cx, cy), size // 2.5)
        pygame.draw.circle(surface, (255, 150, 50), (cx, cy), size // 4)
        pygame.draw.circle(surface, (255, 255, 200), (cx, cy), size // 8)

    def cast(self, caster, target, manager):
        # 1. Mana check
        if caster.current_mana < self.mana_cost:
            return False

        # 2. Consume Mana
        caster.current_mana -= self.mana_cost

        # 3. Calculate Damage (Kova skaalaus INT:stä)
        dmg = int(self.base_damage + (caster.intelligence * 1.2))

        # 4. Visuals & Impact
        start = caster.rect.center
        end = target.rect.center

        def on_impact():
            # Deal Damage (välitetään manager, jotta osuma-vfx/aggro toimivat)
            if hasattr(target, "take_damage"):
                target.take_damage(dmg, 'Magic', attacker=caster, manager=manager)
            else:
                target.current_hp -= dmg

            # Massive Explosion VFX
            if hasattr(manager, "vfx"):
                # Iso räjähdys (jos vfx tukee skaalausta, muuten vakio)
                manager.vfx.show_damage(target.rect.centerx, target.rect.top, dmg, type="magic", is_crit=True)
                # Voit lisätä tänne hienomman partikkeliefektin myöhemmin

        # Launch Projectile
        if hasattr(manager, "vfx") and hasattr(manager.vfx, "create_fireball"):
            try:
                sound_system.play_sound("attack_ranged") # Tai joku raskaampi ääni
            except Exception: pass
            
            # Käytetään samaa fireball-projektiilia mutta ehkä eri värillä/koolla jos mahdollista,
            # tässä käytetään perusversiota logiikan testaamiseksi.
            manager.vfx.create_fireball(start, end, on_impact=on_impact)
        else:
            on_impact()

        return True