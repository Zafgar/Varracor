import pygame
import os
import json
import random
from sound_manager import sound_system

# --- Asset Studion hitbox-overridet ---
# assets/hitbox_overrides.json: {"LuokanNimi": {"dx","dy","w","h"}} suhteessa
# konstruktorin (x, y):hyn. Studio kirjoittaa, tämä soveltaa. Välimuisti
# ladataan kerran; reload_hitbox_overrides() pakottaa uudelleenluvun.
_HITBOX_OVERRIDES = None
_HITBOX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "hitbox_overrides.json")


def _hitbox_overrides():
    global _HITBOX_OVERRIDES
    if _HITBOX_OVERRIDES is None:
        try:
            with open(_HITBOX_FILE, encoding="utf-8") as fh:
                _HITBOX_OVERRIDES = json.load(fh)
        except Exception:
            _HITBOX_OVERRIDES = {}
    return _HITBOX_OVERRIDES


def reload_hitbox_overrides():
    global _HITBOX_OVERRIDES
    _HITBOX_OVERRIDES = None


class Prop(pygame.sprite.Sprite):
    """
    Perusluokka kaikille kartan objekteille.
    Hoitaa kuvan latauksen ja piirtämisen oikeassa järjestyksessä (Y-sort).
    """
    def __init__(self, x, y, w, h, img_path=None, color=(100, 100, 100), collision_rect=None):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        
        if img_path:
            if os.path.exists(img_path):
                try:
                    raw = pygame.image.load(img_path)
                    if pygame.display.get_surface():
                        raw = raw.convert_alpha()
                    self.image = pygame.transform.smoothscale(raw, (w, h))
                except Exception as e:
                    print(f"[Prop] Error loading {img_path}: {e}")
            else:
                print(f"[Prop] Image not found: {img_path}")
            
        # Visuaalinen sijainti (kuvan vasen yläkulma)
        self.image_pos = (x, y)
        
        # Törmäyslaatikko (Logiikka)
        # Jos collision_rect on annettu, käytetään sitä. Muuten koko kuva.
        if collision_rect:
            self.rect = collision_rect
        else:
            self.rect = pygame.Rect(x, y, w, h)

        # Asset Studion hitbox-override jyrää koodissa määritellyn
        override = _hitbox_overrides().get(self.__class__.__name__)
        if override:
            self.rect = pygame.Rect(x + int(override.get("dx", 0)),
                                    y + int(override.get("dy", 0)),
                                    max(1, int(override.get("w", w))),
                                    max(1, int(override.get("h", h))))
            
        self.type = "wall"
        self.blocks_projectiles = True # Oletuksena seinät pysäyttävät ammukset
        self.is_dead = False # Huijataan GameManageria luulemaan tätä yksiköksi
        self.team_color = "Neutral"
        self.is_structure = True # AI tunnistaa tämän ja jättää rauhaan
        
        # AI-yhteensopivuus (ettei peli kaadu kun AI tarkistaa näitä)
        self.name = "Structure"
        self.max_hp = 10000
        self.current_hp = self.max_hp
        
        # --- UUSI: Varjo ---
        self.has_shadow = True
        self._shadow_surf = None
        
        # --- UUSI: Geneerinen vuorovaikutus ---
        self.interaction_range = 0 # 0 = Ei vuorovaikutusta
        self.interaction_label = "" # Esim. "Talk", "Use", "Harvest"
        
        # --- UUSI: Editor Rotation ---
        self.angle = 0

    def rotate(self, angle):
        """Kääntää objektia ja päivittää rectin."""
        self.angle = (self.angle + angle) % 360
        self.image = pygame.transform.rotate(self.image, angle)
        
        # Päivitä rect ja image_pos vastaamaan uutta kokoa, säilyttäen keskipisteen
        old_center = self.rect.center
        self.rect = self.image.get_rect(center=old_center)
        self.image_pos = self.rect.topleft
        
        # Huom: Törmäyslaatikko (collision_rect) pyörii mukana koska se on sidottu rectiin/imageen tässä yksinkertaistuksessa.
        # Monimutkaisemmissa objekteissa collision_rect pitäisi laskea uudelleen.

    def update(self, *args, **kwargs):
        # Tyhjä update-metodi yhteensopivuuden vuoksi (jos GameManager kutsuu)
        pass

    def run_combat_ai(self, *args, **kwargs):
        # Tyhjä AI-metodi yhteensopivuuden vuoksi
        pass

    def take_damage(self, *args, **kwargs):
        return 0

    def _get_shadow(self):
        if self._shadow_surf: return self._shadow_surf
        
        # Varjon leveys suhteessa kuvaan (hieman kapeampi)
        w = int(self.image.get_width() * 0.85)
        h = int(w * 0.3) # Litistetty ellipsi
        
        self._shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # Pehmeä musta varjo
        pygame.draw.ellipse(self._shadow_surf, (0, 0, 0, 80), (0, 0, w, h))
        return self._shadow_surf

    def draw_on_screen(self, screen, offset):
        # Piirrä varjo ensin (jos päällä)
        if self.has_shadow and self.image:
            shad = self._get_shadow()
            sx = self.image_pos[0] + (self.image.get_width() - shad.get_width()) // 2 - offset[0]
            # Sijoitetaan kuvan alareunaan
            sy = self.image_pos[1] + self.image.get_height() - (shad.get_height() // 2) - offset[1] - 3
            screen.blit(shad, (sx, sy))

        if self.image:
            screen.blit(self.image, (self.image_pos[0] - offset[0], self.image_pos[1] - offset[1]))
        # Debug: Piirrä törmäyslaatikko
        # pygame.draw.rect(screen, (255, 0, 0), (self.rect.x - offset[0], self.rect.y - offset[1], self.rect.w, self.rect.h), 1)

    def draw(self, screen, offset):
        # Alias draw_on_screen-metodille
        self.draw_on_screen(screen, offset)

    def draw_health_bar(self, screen, offset):
        pass

    def draw_interaction_bar(self, screen, offset, progress):
        """Piirtää latauspalkin (Hold E)"""
        if progress <= 0: return
        
        bar_w = 60
        bar_h = 8
        x = self.rect.centerx - bar_w // 2 - offset[0]
        y = self.rect.top - 40 - offset[1] # Nostettu ylemmäs (oli 15)
        
        pygame.draw.rect(screen, (40, 40, 40), (x, y, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(screen, (255, 215, 0), (x, y, int(bar_w * progress), bar_h), border_radius=4)

class HarvestableProp(Prop):
    """
    Perusluokka kaikille kerättäville resursseille (puut, malmit, romut).
    """
    def __init__(self, x, y, w, h, img_path=None, color=(100, 100, 100), collision_rect=None):
        super().__init__(x, y, w, h, img_path, color, collision_rect)
        self.is_empty = False
        self.resource_name = "Unknown"
        self.required_tool = None # "axe", "pickaxe", jne.
        self.required_tier = 0
        self.harvest_sound = "mining_hit"
        self.break_sound = "mining_break"
        self.min_drop = 1
        self.max_drop = 1
        self.interaction_range = 60
        self.interaction_label = "Harvest"

    def harvest(self, manager=None, harvester=None):
        if self.is_empty: return

        # Työkalutarkistus
        if self.required_tool and harvester and hasattr(harvester, "equipment"):
            weapon = harvester.equipment.get("main_hand")
            tool_type = getattr(weapon, "tool_type", "none")
            tool_tier = getattr(weapon, "tool_tier", 0)
            
            # Tarkistetaan myös weapon_group fallbackina (esim. kirveet)
            if tool_type == "none" and self.required_tool == "axe":
                grp = getattr(weapon, "weapon_group", "")
                if "axe" in grp or "axe" in getattr(weapon, "name", "").lower():
                    tool_type = "axe"
                    tool_tier = 1 # Oletetaan tier 1 jos ei määritelty
            
            if tool_type != self.required_tool or tool_tier < self.required_tier:
                if manager: 
                    msg = f"Need {self.required_tool.capitalize()}!"
                    if self.required_tier > 1: msg += f" (Tier {self.required_tier})"
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, msg, color=(200, 50, 50))
                return

        self.is_empty = True
        self.image.set_alpha(100) # Himmennä
        
        if manager:
            count = random.randint(self.min_drop, self.max_drop)
            manager.add_material(self.resource_name, count)
            sound_system.play_sound(self.break_sound)
            
            # VFX
            manager.vfx.create_dust_cloud(self.rect.centerx, self.rect.centery)
            manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, f"+{count} {self.resource_name}", color=(200, 200, 200))