import pygame
import os
import random
from sound_manager import sound_system

class IronOre(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.type = "ore"  # Tunniste törmäyksiä varten (GameManager/Arena voi käyttää tätä)
        self.team_color = "Neutral" # Tarvitaan targetointiin
        self.is_dead = False        # Tarvitaan targetointiin
        self.is_structure = True    # AI jättää rauhaan
        self.name = "Iron Ore"
        self.resource_name = "Iron Ore"
        
        # Logiikka: 3-5 lyöntiä millä tahansa hakulla
        self.max_hits = random.randint(3, 5)
        self.current_hits = self.max_hits
        self.is_empty = False
        
        # Visuaalit
        self.sprites = {}
        self._load_assets()
        
        # Asetetaan oletuskuva (skaalattu 60x60)
        self.image = self.sprites.get("full", pygame.Surface((60, 60)))
        if not self.sprites:
            self.image.fill((100, 100, 100)) # Harmaa fallback jos kuvia ei löydy
            
        # Hitbox: Pieni "jalanjälki" kuvan alaosassa
        # Tämä estää törmäyksen "tyhjään ilmaan" kiven yläpuolella.
        self.rect = pygame.Rect(x, y, 40, 20)
        # Keskitetään hitbox visuaalisen sijainnin alaosaan
        self.rect.centerx = x + 30 # 60/2
        self.rect.bottom = y + 5  # Nostettu ylemmäs (oli 58), jotta ei blokkaa alapuolelta
        
        self.radius = 20 # Pyöreä hitbox tuki
        
        self.hit_timer = 0 # Animaatioajastin "hit" kuvalle
        self.vfx_timer = random.randint(0, 100) # Satunnainen aloitus kiillolle

    def _load_assets(self):
        # Polku: assets/crafting/ores/
        base_path = os.path.join("assets", "crafting", "ores")
        
        # Määritellään kuvat tiloille
        files = {
            "full": "iron_ore_full.png",
            "hit": "iron_ore_hit.png",
            "empty": "iron_ore_empty.png"
        }
        
        # Pakotetaan kuvat järkevän kokoisiksi
        target_size = (60, 60)
        
        for key, filename in files.items():
            path = os.path.join(base_path, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(img, target_size)
                    self.sprites[key] = img
                except Exception:
                    print(f"[IronOre] Failed to load {filename}")
            else:
                # Hiljainen virhe tai printti debuggausta varten
                # print(f"[IronOre] Image not found: {path}")
                pass

    def update(self, obstacles=None, manager=None):
        # Jos kivi on tyhjä, näytä tyhjä kuva eikä tehdä muuta
        if self.is_empty:
            if self.sprites.get("empty"):
                self.image = self.sprites["empty"]
            return

        # Idle VFX (Kiilto)
        self.vfx_timer += 1
        if self.vfx_timer > 120: # 2 sekunnin välein
            self.vfx_timer = 0
            if manager and hasattr(manager, "vfx"):
                manager.vfx.create_ore_glimmer(self.rect.centerx, self.rect.centery - 10)

        # Osuma-animaatio (välähdys kun kaivetaan)
        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.sprites.get("hit"):
                self.image = self.sprites["hit"]
        else:
            if self.sprites.get("full"):
                self.image = self.sprites["full"]

    def run_combat_ai(self, all_units, obstacles=None, manager=None):
        # Ei tekoälyä
        pass

    def draw_health_bar(self, surface, offset=(0, 0)):
        # Ei HP-palkkia
        pass

    def draw_on_screen(self, surface, offset=(0, 0)):
        # Piirretään kuva siten, että hitbox on sen alaosassa
        # Hitboxin bottom on n. kuvan bottom.
        img_x = self.rect.centerx - (self.image.get_width() // 2)
        img_y = self.rect.bottom + 45 - self.image.get_height()
        surface.blit(self.image, (img_x - offset[0], img_y - offset[1]))

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        # Ohjataan vahinko take_hit-metodiin, joka tarkistaa työkalun
        tool = getattr(attacker, "current_weapon", None)
        self.take_hit(attacker, tool, manager)
        return 0 # Ei varsinaista HP-vahinkoa tässä mielessä

    def take_hit(self, attacker, tool, manager):
        """
        Kutsutaan kun pelaaja lyö tätä objektia.
        
        Args:
            attacker: Unit joka lyö (esim. Commander)
            tool: Ase/Työkalu jolla lyötiin (esim. WeakPickaxe)
            manager: GameManager (resurssien lisäämiseen ja VFX)
        """
        if self.is_empty:
            return

        # 1. Tarkista onko työkalu Pickaxe
        # (WeakPickaxe-luokassa on self.tool_type = "pickaxe")
        tool_type = getattr(tool, "tool_type", "none")
        
        if tool_type != "pickaxe":
            # Väärä työkalu -ääni tai visuaalinen palaute
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top, "Need Pickaxe!", color=(200, 50, 50))
                sound_system.play_sound("error")
            return

        # 2. Vähennä kestävyyttä
        self.current_hits -= 1
        self.hit_timer = 10 # Väläytä "hit" kuvaa 10 framea (n. 0.16s)
        
        # Ääni (käytetään geneeristä hit-ääntä tai mining-ääntä jos on)
        # sound_system.play_sound("mining_hit") # Jos lisäät mining_hit sound_manageriin
        sound_system.play_sound("mining_hit") 
        
        # VFX: Kipinät aina kun lyödään
        if manager:
            manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(200, 200, 150), count=3)

        # 3. Laske resurssien todennäköisyys
        # Twiikattu: Tier 1 pickaxe n. 10% chance per hit (laskettu)
        tier = getattr(tool, "tool_tier", 1)
        drop_chance = 0.05 + (tier * 0.05) # Base 5% + 5% per tier -> Tier 1 = 10%
        
        # Commander Skill vaikutus (Mining yield / luck)
        if hasattr(attacker, "mining_yield"):
            drop_chance += getattr(attacker, "mining_yield", 0) * 0.05
        # Pickaxe Training II:n mining_speed = tehokkaammat iskut
        drop_chance += float(getattr(attacker, "mining_speed", 0.0))

        # 4. Arvo droppi (Iron Ore)
        dropped_ore = 0
        if random.random() < drop_chance:
            dropped_ore = 1
            # Mahdollisuus saada extraa jos tier on korkea (Critical mine)
            if tier > 1 and random.random() < 0.15:
                dropped_ore += 1

        # Path of the Vein: XP sankarin iskuista
        if manager is not None:
            try:
                from systems import commander_progression as _prog
                _prog.on_ore_mined(manager, attacker, dropped_ore)
            except Exception:
                pass

        # 5. Arvo harvinainen droppi (Gem / Stone)
        dropped_rare = None
        # 2% chance for a Gem (laskettu 5% -> 2%)
        if random.random() < 0.02:
            dropped_rare = "Chipped Ruby" # Low level gem
        # 10% chance for Stone (laskettu 20% -> 10%)
        elif random.random() < 0.10:
            dropped_rare = "Stone"

        # 6. Kivi hajoaa (Empty)
        if self.current_hits <= 0:
            self.is_empty = True
            # Aina vähintään 1 Iron Ore kun malmi loppuu (Guaranteed drop)
            dropped_ore += 1
            
            sound_system.play_sound("mining_break")

        # 7. Anna resurssit pelaajalle
        if manager:
            # Iron Ore
            if dropped_ore > 0:
                sound_system.play_sound("mining_success")
                manager.add_material(self.resource_name, dropped_ore)
                if attacker is manager.player_character and hasattr(manager, "grant_hero_xp"):
                    manager.grant_hero_xp(3 * dropped_ore, self.rect.centerx, self.rect.top)
                color = (200, 200, 220) # Ironin harmaa väri
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, f"+{dropped_ore} Iron", color=color)
            
            # Rare drop
            if dropped_rare:
                manager.add_material(dropped_rare, 1)
                r_color = (255, 80, 80) if "Ruby" in dropped_rare else (120, 120, 130)
                # Näytetään hieman eri kohdassa
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, f"+1 {dropped_rare}", color=r_color)
            
