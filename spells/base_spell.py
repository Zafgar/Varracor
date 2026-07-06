import pygame
from settings import *

class Spell:
    def __init__(self):
        self.name = "Unknown Spell"
        self.description = "..."
        self.mana_cost = 10
        self.cooldown_max = 120 
        self.range = 200
        self.cost = 100 
        self.tier = 1
        
        # --- ITEM YHTEENSOPIVUUS ---
        # Nämä tarvitaan, jotta GuildMenu ja ShopMenu osaavat käsitellä loitsua
        self.type = "Spell"         
        self.slot_type = "spell"    # Main.py ja GuildMenu tarkistavat tämän
        self.rarity = "Common"      
        
        self.icon_color = (100, 100, 255)

    def get_color(self):
        # Palauttaa värin rarityn mukaan (UI:ta varten)
        if self.rarity == "Common": return (200, 200, 200)
        if self.rarity == "Rare": return (50, 100, 255)
        if self.rarity == "Epic": return (180, 50, 255)
        if self.rarity == "Legendary": return (255, 165, 0)
        return (255, 255, 255)

    def draw_card_icon(self, surface, x, y, size):
        # Tätä kutsuu UI (Shop/Guild/Inventory)
        # Piirretään tausta
        pygame.draw.rect(surface, (30, 30, 40), (x, y, size, size), border_radius=5)
        pygame.draw.rect(surface, self.get_color(), (x, y, size, size), 2, border_radius=5)
        
        # Piirretään itse ikoni
        self.draw_icon(surface, x, y, size)

    def draw_icon(self, surface, x, y, size):
        # Oletusikoni (sininen neliö), jos alaluokka ei määrittele omaa
        center_size = size * 0.6
        offset = size * 0.2
        pygame.draw.rect(surface, self.icon_color, (x+offset, y+offset, center_size, center_size), border_radius=3)

    # --- TÄRKEÄ MUUTOS ---
    # Vaihdoimme 'all_units' -> 'manager'.
    # Näin loitsu pääsee käsiksi manager.vfx:ään ja manager.sound_systemiin!
    def cast(self, caster, target, manager):
        """ 
        Tämä ylikirjoitetaan varsinaisissa loitsuissa (esim. Fireball).
        Palauttaa True, jos loitsu onnistui.
        """
        print(f"{caster.name} cast {self.name} but it did nothing!")
        return False