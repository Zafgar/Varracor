import pygame
import math
from settings import *

# --- SHADOW CACHE ---
SHADOW_CACHE = {}
def get_shadow(width):
    if width not in SHADOW_CACHE:
        s = pygame.Surface((width, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (10, 10, 10, 160), (0, 0, width, 12)) # Tummempi varjo (alpha 100 -> 160)
        SHADOW_CACHE[width] = s
    return SHADOW_CACHE[width]

class GladiatorRenderer:
    def __init__(self, unit):
        self.unit = unit # Viittaus omistajaan (Gladiator-olio)
        self.facing_right = True  # Tallennetaan suunta, jotta se ei värise
        self._dead_cache = None

    def update_facing(self):
        """ Päivittää hahmon katselusuunnan (AI target tai liike). """
        # 0. PLAYER OVERRIDE (Commander)
        # Jos yksiköllä ei ole AI-kontrolleria (pelaaja), käytetään sen asettamaa suuntaa (hiiri)
        if not getattr(self.unit, "ai_controller", None):
            if hasattr(self.unit, "facing_right"):
                self.facing_right = self.unit.facing_right
            return

        # 1. Jos AI:lla on kohde, katso kohdetta
        if hasattr(self.unit, "ai_controller") and self.unit.ai_controller:
            target = getattr(self.unit.ai_controller, "current_target", None)
            if target and not getattr(target, 'is_dead', True):
                if target.rect.centerx < self.unit.rect.centerx:
                    self.facing_right = False
                else:
                    self.facing_right = True
                return

        # 2. Jos ei kohdetta, katso liikesuuntaan (jos liikkuu)
        if getattr(self.unit, "is_dashing", False):
            dvec = getattr(self.unit, "dash_vector", (0,0))
            if dvec[0] < 0:
                self.facing_right = False
            elif dvec[0] > 0:
                self.facing_right = True

    def draw_on_screen(self, surface, offset=(0, 0)):
        """ Hoitaa hahmon piirtämisen, animaatiot ja varusteet """
        
        # --- 0. KUOLLUT HAHMO ---
        if self.unit.is_dead:
            # Häivytys (Fade out) viimeisen sekunnin aikana (frame 240-300)
            death_timer = getattr(self.unit, "_death_timer", 0)
            alpha = 255
            if death_timer > 240:
                alpha = max(0, int(255 * (1.0 - (death_timer - 240) / 60.0)))

            if self._dead_cache:
                self._dead_cache.set_alpha(alpha)
                r_rect = self._dead_cache.get_rect(center=(self.unit.rect.centerx - offset[0], self.unit.rect.centery - offset[1]))
                r_rect.bottom = self.unit.rect.bottom - offset[1] + 10
                surface.blit(self._dead_cache, r_rect)
                return

            img = self.unit.image
            if not img: return # Ei kuvaa, ei piirretä
            
            # Varmistus: Jos kuva on lista (animaatio), ota ensimmäinen frame
            if isinstance(img, list):
                if len(img) > 0: img = img[0]
                else: return
            
            rotated = pygame.transform.rotate(img, 90)
            # Harmaannuta kuollut (jos mahdollista)
            try:
                gray_surf = rotated.copy()
                gray_surf.fill((160, 160, 160, 255), special_flags=pygame.BLEND_RGBA_MULT)
            except Exception:
                gray_surf = rotated # Fallback jos ei toimi

            gray_surf.set_alpha(alpha)
            self._dead_cache = gray_surf
            r_rect = gray_surf.get_rect(center=(self.unit.rect.centerx - offset[0], self.unit.rect.centery - offset[1]))
            r_rect.bottom = self.unit.rect.bottom - offset[1] + 10
            surface.blit(gray_surf, r_rect)
            return

        # --- 1. LIIKE-ANIMAATIO ---
        self.update_facing()
        now = pygame.time.get_ticks()
        
        # Animaatiomuuttujat
        breathing = math.sin(now * 0.005) * 2  # +/- 2 pikseliä ylös/alas
        wobble_angle = math.sin(now * 0.01) * 3 
        
        # Hyökkäys-kyykky
        attack_offset_y = 0
        if self.unit.attack_cooldown > (self.unit.attack_speed - 15):
             attack_offset_y = 2 # Kyykistyy lyödessä
             wobble_angle = 0

        # Tarkistetaan onko meillä jaettu sprite (legs + torso)
        sprites = getattr(self.unit, "sprites", {})
        has_split_sprite = 'legs' in sprites and 'torso' in sprites
        
        # Lasketaan piirtosijainti kameran mukaan
        draw_rect = self.unit.rect.move(-offset[0], -offset[1])

        # --- PIIRRETÄÄN VARJO (Aina ensin) ---
        # Käytetään välimuistia piirtämisen sijaan
        # Skaalataan varjoa pienemmäksi jos ollaan korkealla
        shadow_scale = 1.0
        if hasattr(self.unit, "jump_height") and self.unit.jump_height > 0:
            # Varjo pienenee kun korkeus kasvaa (min 40%)
            shadow_scale = max(0.4, 1.0 - (self.unit.jump_height / 200.0))
            
        shadow_w = int(draw_rect.width * shadow_scale)
        shadow = get_shadow(shadow_w)
        
        # Keskitetään varjo hahmon alle
        shadow_x = draw_rect.centerx - (shadow_w // 2)
        surface.blit(shadow, (shadow_x, draw_rect.bottom - 6))

        # --- HYPPY EFEKTI (Siirretään hahmoa ylös, varjo jää alas) ---
        if hasattr(self.unit, "jump_height"):
            draw_rect.y -= int(self.unit.jump_height)

        if has_split_sprite:
            # --- TAPA A: JAETTU SPRITE (Hienompi animaatio) ---
            legs = sprites['legs']
            torso = sprites['torso']
            
            if not self.facing_right:
                legs = pygame.transform.flip(legs, True, False)
                torso = pygame.transform.flip(torso, True, False)
                wobble_angle *= -1

            # 1. Jalat (Pysyvät maassa tai heiluvat vähän kävellessä)
            legs_rect = legs.get_rect(midbottom=draw_rect.midbottom)
            surface.blit(legs, legs_rect)
            
            # 2. Torso (Liikkuu hengityksen mukana ylös/alas)
            torso_y = legs_rect.top + int(breathing) + attack_offset_y
            
            # Käännetään torsoa (wobble)
            if abs(wobble_angle) > 0.5:
                rotated_torso = pygame.transform.rotate(torso, wobble_angle)
                # Kääntäminen muuttaa rectin kokoa, pidetään keskipiste samana
                torso_rect = rotated_torso.get_rect(center=(draw_rect.centerx, torso_y + torso.get_height()//2))
                surface.blit(rotated_torso, torso_rect)
            else:
                surface.blit(torso, (legs_rect.x, torso_y))
            
            # Päivitetään draw_rect varusteita varten (seuraa torsoa)
            draw_rect.y = torso_y

        else:
            # --- TAPA B: YKSI SPRITE (Vanha tapa tai fallback) ---
            source = self.unit.image # Use the unit's current image directly
            
            # Jos kuvaa ei vieläkään ole, piirrä placeholder
            if not source:
                pygame.draw.rect(surface, (255, 0, 255), draw_rect)
                return

            if not self.facing_right: 
                source = pygame.transform.flip(source, True, False)
                wobble_angle *= -1
            
            # Hengitys skaalaa koko hahmoa Y-suunnassa vanhassa tavassa
            scale_y = 1.0 + (math.sin(now * 0.005) * 0.02)
            # Use image size, not rect size (rect is now feet only)
            w, h = source.get_width(), int(source.get_height() * scale_y)
            
            scaled = pygame.transform.scale(source, (w, h))
            rotated = pygame.transform.rotate(scaled, wobble_angle)
            
            draw_rect = rotated.get_rect(midbottom=draw_rect.midbottom)
            draw_rect.bottom = self.unit.rect.bottom - offset[1]
            
            surface.blit(rotated, draw_rect)

        # --- 2. VARUSTEET (Equipment) ---
        # Varusteet piirretään torson päälle (käytetään päivitettyä draw_rectiä)
        equip_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, draw_rect.height)
        equipment = getattr(self.unit, "equipment", {})

        # Koodigrafiikka-fallback: ilman tätä ase/kilpi olisi näkymätön
        # kunnes PNG on toimitettu (draw_equipped vaatii item.imagen)
        try:
            from items.procedural_gear import ensure_gear_image
            for _slot in ("body", "head", "off_hand", "main_hand"):
                ensure_gear_image(equipment.get(_slot))
        except Exception:
            pass

        # A) Body Armor
        armor = equipment.get("body")
        if armor and hasattr(armor, "draw_equipped"):
            armor.draw_equipped(surface, equip_rect, self.facing_right, 0)

        # B) Helmet
        helmet = equipment.get("head")
        if helmet and hasattr(helmet, "draw_equipped"):
            # Helmet seuraa pään liikettä tarkasti
            helmet.draw_equipped(surface, equip_rect, self.facing_right, 0)

        # C) Off Hand
        oh = equipment.get('off_hand')
        if oh and hasattr(oh, 'draw_equipped'):
            oh.draw_equipped(surface, equip_rect, self.facing_right, 0)

        # D) Main Hand
        mw = equipment.get('main_hand')
        if mw and hasattr(mw, 'draw_equipped') and getattr(self.unit, "show_main_hand", True):
            timer = self.unit.attack_cooldown if self.unit.attack_cooldown > 0 else 0
            attack_vector = getattr(self.unit, "attack_vector", None)
            # Välitetään myös attack_speed animaation laskemista varten
            try:
                mw.draw_equipped(surface, equip_rect, self.facing_right, timer, getattr(self.unit, "attack_speed", 60), attack_vector)
            except TypeError:
                try:
                    mw.draw_equipped(surface, equip_rect, self.facing_right, timer, getattr(self.unit, "attack_speed", 60))
                except TypeError:
                    mw.draw_equipped(surface, equip_rect, self.facing_right, timer)

        # --- 3. STATUS EFFECTS (STUN) ---
        if getattr(self.unit, "stun_timer", 0) > 0:
            # Pyörivät tähdet pään päällä
            cx = draw_rect.centerx
            cy = draw_rect.top - 10
            t = pygame.time.get_ticks() * 0.01
            
            for i in range(3):
                angle = t + (i * (6.28 / 3))
                radius = 12
                sx = cx + math.cos(angle) * radius
                sy = cy + math.sin(angle) * 4 # Litistetty ympyrä
                pygame.draw.circle(surface, (255, 255, 0), (int(sx), int(sy)), 3)

    def draw_health_bar(self, surface, offset=(0, 0)):
        """ Piirtää HP-, Mana- ja Stamina-palkit hahmon alle """
        if self.unit.is_dead: return
        
        # --- HP BAR ---
        current_hp = getattr(self.unit, "current_hp", 0)
        max_hp = getattr(self.unit, "max_hp", 1)
        pct = max(0.0, min(1.0, float(current_hp) / float(max_hp)))
        
        # Väri: Vihreä omille, punainen vihuille (yksinkertaistettu logiikka)
        col = GREEN # Oletus (Vihreä)
        
        uc = getattr(self.unit, "team_color", None)
        if uc:
            # Tunnistetaan väri (käytetään settings.py vakioita jos mahdollista)
            if uc == RED: col = RED
            elif uc == BLUE: col = (100, 100, 255) # Kirkkaampi sininen palkkiin
            elif uc == (150, 150, 150): col = (200, 200, 200) # Neutraali harmaa
            # Green pysyy vihreänä
        
        bar_x = self.unit.rect.x - offset[0]
        bar_y = self.unit.rect.bottom + 5 - offset[1]
        bar_w = self.unit.rect.width
        
        # Tausta
        pygame.draw.rect(surface, (50,50,50), (bar_x, bar_y, bar_w, 5))
        # Palkki
        pygame.draw.rect(surface, col, (bar_x, bar_y, int(bar_w*pct), 5))
        
        current_y = bar_y + 6

        # --- MANA BAR (Sininen) ---
        max_mana = getattr(self.unit, "max_mana", 0)
        if max_mana > 0:
            current_mana = getattr(self.unit, "current_mana", 0)
            mpct = max(0.0, min(1.0, float(current_mana) / float(max_mana)))
            pygame.draw.rect(surface, (50,50,50), (bar_x, current_y, bar_w, 3))
            pygame.draw.rect(surface, (50, 100, 255), (bar_x, current_y, int(bar_w*mpct), 3)) # BLUE
            current_y += 4

        # --- STAMINA BAR (Keltainen) ---
        max_stamina = getattr(self.unit, "max_stamina", 0)
        if max_stamina > 0:
            current_stamina = getattr(self.unit, "current_stamina", 0)
            spct = max(0.0, min(1.0, float(current_stamina) / float(max_stamina)))
            
            # Stamina väri: Kulta, mutta muuttuu harmaaksi jos loppuu
            stam_col = (255, 215, 0)
            if current_stamina < 10:
                stam_col = (100, 100, 100) # Exhausted

            pygame.draw.rect(surface, (50,50,50), (bar_x, current_y, bar_w, 3))
            pygame.draw.rect(surface, stam_col, (bar_x, current_y, int(bar_w*spct), 3))