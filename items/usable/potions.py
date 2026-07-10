import pygame
from items.base_item import Item
from sound_manager import sound_system

class Potion(Item):
    def __init__(self, name="Potion", heal_amount=0):
        super().__init__()
        self.name = name
        self.slot_type = "usable"
        self.type = "Usable"
        self.heal_amount = heal_amount
        self.cooldown_max = 30

    def cast(self, owner, target, manager, target_pos=None):
        """Juo potion: parantaa käyttäjää ja kuluu loppuun.
        (BUGIKORJAUS: ilman cast-metodia usable-slotti ei tehnyt mitään.)"""
        if owner.current_hp >= owner.max_hp:
            if manager:
                manager.vfx.show_damage(owner.rect.centerx, owner.rect.top - 20,
                                        "Already full!", color=(180, 180, 180))
            return False

        healed = min(self.heal_amount, owner.max_hp - owner.current_hp)
        owner.current_hp += healed
        if manager:
            manager.vfx.show_damage(owner.rect.centerx, owner.rect.top - 20,
                                    f"+{healed}", color=(100, 255, 100))
            manager.vfx.create_impact_sparks(owner.rect.centerx, owner.rect.centery,
                                             color=(255, 80, 80), count=6)
        sound_system.play_sound("heal")

        # Kertakäyttöinen: tyhjennä slotti josta juotiin
        for slot in ("usable", "usable2"):
            if owner.equipment.get(slot) is self:
                owner.equipment[slot] = None
                break
        return True

    def draw_card_icon(self, surface, x, y, size):
        # Pieni pullo
        pygame.draw.rect(surface, (200, 200, 200), (x+size*0.4, y+size*0.2, size*0.2, size*0.1))
        pygame.draw.circle(surface, (255, 50, 50), (x+size*0.5, y+size*0.6), size*0.3)

class WeakHealthPotion(Potion):
    def __init__(self):
        super().__init__("Weak Health Potion", heal_amount=30)
        self.cost = 20
        self.rarity = "Common"
        self.description = "Restores 30 HP."