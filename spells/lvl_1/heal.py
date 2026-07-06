import pygame
from spells.base_spell import Spell

class MinorHeal(Spell):
    def __init__(self):
        super().__init__()
        # TÄRKEÄÄ: Nimen on sisällettävä "Heal", jotta AI tajuaa targetoida omia!
        self.name = "Minor Heal"
        self.description = "Restores HP to an ally."
        
        self.mana_cost = 30
        self.cooldown_max = 240 # 4 sekuntia
        self.range = 250        # Kantama
        self.cost = 250         # Hinta kaupassa
        
        self.base_heal = 20
        self.tier = 1
        
        # UI-tiedot
        self.rarity = "Common"
        self.slot_type = "spell"
        
        # Vihreä ikoni (jos piirtoa ei käytetä)
        self.icon_color = (0, 200, 50)

    def draw_icon(self, surface, x, y, size):
        # Vihreä tausta
        pygame.draw.rect(surface, (20, 50, 20), (x, y, size, size), border_radius=5)
        # Risti (Plus-merkki)
        center_x, center_y = x + size//2, y + size//2
        thick = size // 3
        # Vaaka
        pygame.draw.rect(surface, (0, 255, 100), (x + 5, center_y - thick//2, size - 10, thick))
        # Pysty
        pygame.draw.rect(surface, (0, 255, 100), (center_x - thick//2, y + 5, thick, size - 10))

    def cast(self, caster, target, manager):
        """
        Parantaa kohdetta.
        Target on tässä tapauksessa liittolainen (Unit-luokan AI hoitaa valinnan).
        """
        # 1. Tarkista mana
        if caster.current_mana < self.mana_cost:
            return False

        # 2. Vähennä mana
        caster.current_mana -= self.mana_cost

        # 3. Laske parannus (INT vaikuttaa)
        heal_amt = self.base_heal + (caster.intelligence * 0.8)
        heal_amt = int(heal_amt)
        
        # 4. Toteuta parannus
        target.heal(heal_amt)
        
        # 5. VISUAALINEN EFEKTI (Managerin kautta)
        # Vihreät hiukkaset
        manager.vfx.create_heal_effect(target.rect.centerx, target.rect.centery)
        
        # Näytetään numero (vihreänä, koska type="heal")
        manager.vfx.show_damage(target.rect.centerx, target.rect.top, heal_amt, type="heal")
        
        print(f"{caster.name} heals {target.name} for {heal_amt} HP!")
        return True