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
        self.speed = self.walk_speed = 1.2 * 1.85  # uusi liikeskaala (pelitesti 28); pelkka .speed ylikirjoittui updatessa
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

        # Fallback: koodipiirretty rottasiluetti (ei harmaa laatikko)
        from units.placeholder_sprites import quadruped_frames
        self.sprites = quadruped_frames(
            (48, 36),
            body=(118, 92, 74),     # ruskea turkki
            accent=(84, 62, 50),
            eye=(226, 70, 60),
        )
        self.image = self.sprites["idle"]
        self.rect = self.image.get_rect(center=self.rect.center)
        return True

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


class BruteRat(GiantRat):
    """Iso, sitkeä lihasrotta viemäriverkoston syvyyksiin (pelitesti 25).
    Sama Giant Rat -grafiikka tuplakokoon skaalattuna - hidas mutta rankka
    panssarimurskaaja."""

    def __init__(self, name, x, y, team_color=(200, 50, 50)):
        super().__init__(name, x, y, team_color)
        self.max_hp = 420
        self.current_hp = 420
        self.strength = 34
        self.dexterity = 9
        self.speed = 0.8
        self.attack_speed = 80
        self.attack_range = 70
        try:
            for key, img in list(getattr(self, "sprites", {}).items()):
                if img is not None:
                    self.sprites[key] = pygame.transform.scale(
                        img, (img.get_width() * 2, img.get_height() * 2))
            if getattr(self, "image", None) is not None:
                self.image = pygame.transform.scale(
                    self.image, (self.image.get_width() * 2,
                                 self.image.get_height() * 2))
                self.rect = self.image.get_rect(center=self.rect.center)
        except Exception:
            pass