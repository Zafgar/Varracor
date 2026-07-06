import pygame
import os
from gladiator import Gladiator

class GiantRat(Gladiator):
    def __init__(self, name, x, y, team_color=(200, 50, 50)):
        # Kutsutaan kantaluokkaa, joka kutsuu load_assets()
        super().__init__(name, "Rat", x, y, team_color)
        
        # Asetetaan rotan statsit (jos RACES ei niitä asettanut)
        self.max_hp = 60
        self.current_hp = 60
        self.strength = 25
        self.dexterity = 14
        self.speed = 1.2
        self.attack_speed = 45

    def load_assets(self):
        """Lataa Giant Rat -kohtaiset spritet."""
        self.sprites = {}
        
        # Määritellään tiedostojen nimet tiloille
        # KORJAUS: Oikea polku (yksikkömuoto 'rat')
        base_path = os.path.join("assets", "races", "rat")
        
        files = {
            "idle": "giant_rat_run.png",   # Käytetään runia idlenä jos idle puuttuu
            "run": "giant_rat_run.png",
            "attack": "giant_rat_attack.png",
            "hurt": "giant_rat_hurt.png"
        }

        loaded_any = False
        for state, filename in files.items():
            path = os.path.join(base_path, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Skaalataan säilyttäen kuvasuhde (Max 48px)
                    orig_w, orig_h = img.get_size()
                    ratio = min(48 / orig_w, 48 / orig_h)
                    new_size = (int(orig_w * ratio), int(orig_h * ratio))
                    img = pygame.transform.smoothscale(img, new_size)
                    self.sprites[state] = img
                    loaded_any = True
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")
        
        # Asetetaan oletuskuva
        if loaded_any:
            self.image = self.sprites.get("idle") or list(self.sprites.values())[0]
            # Päivitetään rect vastaamaan uutta kuvakokoa
            self.rect = self.image.get_rect(center=self.rect.center)
            return True
            
        return False

    def update(self, obstacles=None, manager=None):
        # Päivitetään logiikka (liike, cooldownit, animation_state)
        super().update(obstacles, manager)
        
        # Vaihdetaan kuva tilan mukaan
        if self.use_sprites:
            state = self.animation_state
            new_img = self.sprites.get(state)
            
            # Fallback: jos "idle" puuttuu, käytä "run"
            if not new_img and state == "idle":
                new_img = self.sprites.get("run")
                
            if new_img:
                self.image = new_img