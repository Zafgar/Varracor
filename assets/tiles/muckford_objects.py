import pygame
import random
import os
import math
from assets.tiles.prop import Prop, HarvestableProp
from sound_manager import sound_system
from assets.tiles.farm_objects import Apple

class TavernBuilding(Prop):
    """
    The Sunk Cask Tavern.
    Original: 1500x600 -> Scaled: 500x200
    """
    def __init__(self, x, y):
        w, h = 800, 400 # Skaalattu isommaksi (oli 500x200)
        # Hitbox nostettu ylemmäs (hahmon verran), jotta talon eteen voi kävellä
        coll_rect = pygame.Rect(x + 40, y + h - 140, w - 80, 80)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/thesunkcask_tavern.png", color=(100, 80, 60), collision_rect=coll_rect)
        self.is_structure = True
        self.name = "The Sunk Cask"
        # Ovi nostettu vastaamaan uutta seinälinjaa
        self.door_offset = (320, h - 30) # Siirretty alemmas (törmäyslaatikon eteen)

class TownHall(Prop):
    """
    Kaupungintalo (Sponsors).
    Original: 1200x800 -> Scaled: 400x266
    """
    def __init__(self, x, y):
        w, h = 700, 460 # Skaalattu isommaksi (oli 400x266)
        coll_rect = pygame.Rect(x + 40, y + h - 140, w - 80, 80)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/townhall_mudrock.png", color=(120, 100, 80), collision_rect=coll_rect)
        self.is_structure = True
        self.name = "Town Hall"
        self.door_offset = (350, h - 30) # Ovi keskellä

class ScrapIronBuilding(Prop):
    """
    Sepän paja (Blacksmith).
    Original: 1200x800 -> Scaled: 600x400
    """
    def __init__(self, x, y):
        w, h = 600, 400
        # Hitbox nostettu reilusti ylöspäin (n. 2 hahmon verran), jotta takaseinä on oikeassa kohdassa
        coll_rect = pygame.Rect(x + 40, y + h - 220, w - 80, 80)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/scrapiron_muckford.png", color=(80, 80, 90), collision_rect=coll_rect)
        self.is_structure = True
        self.name = "Scrap Iron Smithy"
        self.door_offset = (300, h - 30)

class ScrapBarrel(Prop):
    """
    Romutynnyri. Pieni este.
    """
    def __init__(self, x, y):
        w, h = 40, 50
        # Hitboxia nostettu
        coll_rect = pygame.Rect(x, y + h - 20 - 5, w, 20)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/muckford/barrel.png",
            color=(80, 60, 40),
            collision_rect=coll_rect
        )

class SewerGrate(Prop):
    """
    Viemärinkansi. Ei estä liikkumista, toimii spawn pointina rotille.
    """
    def __init__(self, x, y):
        w, h = 60, 40
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/muckford/sewer_grate.png",
            color=(40, 40, 50)
        )
        self.rect = pygame.Rect(x, y, 0, 0) # Ei törmäystä
        self.blocks_projectiles = False
        self.is_structure = True
        self.has_shadow = False # Litteä

class StreetLamp(Prop):
    """
    Katuvalo. Luo tunnelmaa (VFX hoitaa valon).
    """
    def __init__(self, x, y):
        w, h = 20, 120
        # Hitboxia nostettu
        coll_rect = pygame.Rect(x, y + h - 20 - 10, w, 20)
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/muckford/lamp.png",
            collision_rect=coll_rect,
            color=(30, 30, 30)
        )

class MuckfordField(Prop):
    """
    Viljelyspalsta. Ei estä liikkumista (tai hidastaa vähän).
    """
    def __init__(self, x, y):
        w, h = 300, 200
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/muckford/field.png",
            color=(60, 70, 40)
        )
        self.rect = pygame.Rect(x, y, 0, 0) # Ei törmäystä
        self.blocks_projectiles = False
        self.is_structure = True
        self.has_shadow = False # Litteä

class MuckfordTree(HarvestableProp):
    """
    Kuollut tai kitukasvuinen puu.
    """
    def __init__(self, x, y, variant=1):
        w, h = 180, 280
        # Kapea runko alhaalla
        coll_w = 40
        coll_h = 30
        coll_rect = pygame.Rect(x + (w - coll_w)//2, y + h - coll_h - 20, coll_w, coll_h)
        
        super().__init__(
            x, y, w, h,
            img_path=f"assets/tiles/muckford/tree_{variant}.png",
            collision_rect=coll_rect,
            color=(50, 45, 40)
        )
        self.resource_name = "Swamp Wood"
        self.max_hits = 5
        self.current_hits = self.max_hits
        self.interaction_label = "Chop"

        # Wind sway
        self.sway_timer = random.uniform(0, 100)
        self.base_image = self.image # Keep original for transformation
        self.origin_pos = (x, y) # Store original top-left for pivoting

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        tool = getattr(attacker, "current_weapon", None)
        self.chop(attacker, tool, manager)
        return 0

    def chop(self, attacker, tool, manager):
        if self.is_empty: return

        # 1. Työkalutarkistus
        tool_type = getattr(tool, "tool_type", "none")
        if tool_type == "none":
             grp = getattr(tool, "weapon_group", "")
             if "axe" in grp: tool_type = "axe"

        if tool_type != "axe":
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Need Axe!", color=(200, 50, 50))
                sound_system.play_sound("error")
            return

        # 2. Osuma
        self.current_hits -= 1
        sound_system.play_sound("axe_1") 
        
        if manager:
            manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(150, 100, 50), count=3)
            manager.vfx.create_falling_leaves(self.rect.centerx, self.rect.centery)

        # 3. Resurssi per isku (Chance)
        if random.random() < 0.4:
            if manager:
                manager.add_material(self.resource_name, 1)
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, f"+1 {self.resource_name}", color=(150, 255, 100))

        # 4. Kaatuu
        if self.current_hits <= 0:
            self.is_empty = True
            if self.image:
                w, h = self.image.get_size()
                stump_h = 40
                if h > stump_h:
                    stump = self.image.subsurface((0, h - stump_h, w, stump_h)).copy()
                    self.image = stump
                    self.image_pos = (self.image_pos[0], self.image_pos[1] + h - stump_h)
            
            if manager:
                manager.add_material(self.resource_name, 2)
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 60, "Timber!", color=(255, 200, 100))
                sound_system.play_sound("mining_break")

    def update(self, obstacles=None, manager=None, **kwargs):
        if self.is_empty: return
        
        # Wind sway animation
        self.sway_timer += 0.02
        sway_amount = math.sin(self.sway_timer) * 2.0 # +/- 2 pixels
        
        # Rotate around bottom center to make top move more
        angle = math.sin(self.sway_timer) * 2.0 # +/- 2 degrees
        self.image = pygame.transform.rotate(self.base_image, angle)
        
        # Adjust image_pos to pivot around bottom center
        w, h = self.base_image.get_size()
        rw, rh = self.image.get_size()
        
        ox, oy = self.origin_pos
        # Align bottom centers:
        # new_x + rw/2 = ox + w/2  => new_x = ox + (w - rw)/2
        # new_y + rh = oy + h      => new_y = oy + (h - rh)
        self.image_pos = (ox + (w - rw) // 2, oy + (h - rh))
        
        # Do NOT update self.rect (collision rect)

class AppleTree(Prop):
    """
    Omenapuu. Ravistamalla (E) tiputtaa omenoita.
    """
    def __init__(self, x, y):
        w, h = 160, 240
        coll_rect = pygame.Rect(x + 60, y + h - 40, 40, 30)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/apple_tree.png", color=(40, 100, 40), collision_rect=coll_rect)
        self.is_structure = True
        self.name = "Apple Tree"
        self.apples_count = random.randint(3, 6)
        self.shake_cooldown = 0
        self.interaction_range = 80
        self.interaction_label = "Shake"

    def shake(self, manager):
        if self.shake_cooldown > 0: return
        if self.apples_count <= 0:
            manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Empty", color=(200, 200, 200))
            return

        self.shake_cooldown = 30
        self.apples_count -= 1
        
        # Tiputa omena
        ax = self.rect.centerx + random.randint(-40, 40)
        ay = self.rect.bottom + random.randint(-10, 20)
        apple = Apple(ax, ay)
        manager.current_arena.props.append(apple)
        manager.all_units.add(apple)
        
        sound_system.play_sound("hover") # Rustle sound placeholder

class FenceVertical(Prop):
    def __init__(self, x, y):
        w, h = 10, 120
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/muckford/fence_1_vertical.png",
            color=(100, 80, 60)
        )
        # Kapea törmäys
        self.rect = pygame.Rect(x, y, w, h)
        self.has_shadow = False

class FenceHorizontal(Prop):
    def __init__(self, x, y):
        w, h = 40, 10
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/muckford/fence_1_horizontal.png",
            color=(100, 80, 60)
        )
        # Matala törmäys
        self.rect = pygame.Rect(x, y, w, h)
        self.has_shadow = False

class ForestFloor(Prop):
    """
    Metsän pohja (1000x700).
    """
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, img_path="assets/tiles/floors/muckford_forest.png", color=(20, 40, 20))
        self.rect = pygame.Rect(x, y, 0, 0) # Lattia
        self.is_structure = False
        self.has_shadow = False
        
        # Tiilitetään kuva alueelle
        path = "assets/tiles/floors/muckford_forest.png"
        if os.path.exists(path):
             self._tile_image(w, h, path)

    def _tile_image(self, w, h, path):
        try:
            tile = pygame.image.load(path).convert()
            self.image = pygame.Surface((w, h))
            tw, th = tile.get_size()
            for r in range(0, h, th):
                for c in range(0, w, tw):
                    self.image.blit(tile, (c, r))
        except Exception: pass

class ScrapPileBig(HarvestableProp):
    """
    Iso romukasa, jota voi tonkia.
    """
    def __init__(self, x, y):
        w, h = 160, 110 # Pienennetty (oli 200x140)
        coll_rect = pygame.Rect(x + 15, y + h - 80, w - 30, 35)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/scrap_big.png", color=(80, 70, 60), collision_rect=coll_rect)
        self.is_structure = True
        
        self.interaction_label = "Scavenge (Hold)"
        self.interaction_range = 100
        
        # Scavenge logic
        self.max_searches = random.randint(4, 7)
        self.current_searches = self.max_searches
        self.interact_timer = 0
        self.interact_max = 60 # 1 sekunti per haku
        
        self.loot_table = [
            "Scrap Iron", "Scrap Iron", "Scrap Iron", # Yleisin
            "Swamp Wood", "Swamp Wood",
            "Coal", 
            "Bone Fragment",
            "Rat Tail"
        ]

    def refill(self):
        """Palauttaa kasan täyteen (kutsutaan kun päivä vaihtuu / matsi pelattu)."""
        self.is_empty = False
        self.current_searches = random.randint(4, 7)
        self.image.set_alpha(255) # Palauta näkyvyys
        # Poista "Empty" merkinnät lataamalla kuva uudestaan tai piirtämällä päälle (yksinkertaisinta ladata uudestaan jos mahdollista, tai vain poistaa tummennus)
        # Tässä tapauksessa Prop-luokka ei tue helppoa reloadia, joten luotamme alphaan.
        # Jos piirsimme "Empty" tekstin kuvaan, se pitäisi pyyhkiä. 
        # Yksinkertaisin tapa: Prop lataa kuvan initissä. Voimme pakottaa sen uudestaan jos tarve, 
        # mutta tässä riittää että emme piirrä "Empty" tekstiä update/draw:ssa jos !is_empty.

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return

        if manager and manager.player_character:
            player = manager.player_character
            dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
            
            keys = pygame.key.get_pressed()
            if dist < self.interaction_range and keys[pygame.K_e]:
                self.interact_timer += 1
                
                if self.interact_timer >= self.interact_max:
                    self.interact_timer = 0
                    self.current_searches -= 1
                    
                    # Loot
                    item = random.choice(self.loot_table)
                    qty = 1
                    if item == "Scrap Iron": qty = random.randint(1, 2)
                    
                    manager.add_material(item, qty)
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, f"+{qty} {item}", color=(200, 200, 200))
                    sound_system.play_sound("recruit") # "Chime" sound
                    
                    if self.current_searches <= 0:
                        self.is_empty = True
                        self.image.set_alpha(100) # Himmennä tyhjä kasa
                        sound_system.play_sound("mining_break")
            else:
                self.interact_timer = 0

    def draw_on_screen(self, screen, offset):
        super().draw_on_screen(screen, offset)
        if not self.is_empty and self.interact_timer > 0:
            self.draw_interaction_bar(screen, offset, self.interact_timer / self.interact_max)

class MuckfordStall(Prop):
    """
    Markkinakoju.
    Variant 1: Kristallit/Tavarat
    Variant 2: Ruoka
    """
    def __init__(self, x, y, variant=1):
        # Pienennetty lisää (oli 200x140) -> 140x100
        w, h = 140, 100
        
        # Hitbox: Yläosa (tiski/teltta), alaosa vapaa liikkumiselle
        coll_h = 40
        coll_rect = pygame.Rect(x + 10, y + 30, w - 20, coll_h)
        
        img_name = f"muckford_stall_{variant}.png"
        
        super().__init__(
            x, y, w, h,
            img_path=f"assets/tiles/muckford/{img_name}",
            collision_rect=coll_rect,
            color=(120, 100, 80)
        )
        self.is_structure = True
        self.name = "Market Stall"

class MuckfordStage(Prop):
    """
    Esiintymislava.
    Source 1000x500 -> Skaalataan n. 500x250 (Pienennetty).
    """
    def __init__(self, x, y):
        w, h = 360, 180 # Pienennetty (oli 500x250)
        
        # Hitbox: Vain kapea kaistale yläreunassa (takaseinä).
        # Kavennettu sivuilta (x+40, w-80), jotta ei törmää "tyhjään" reunoilla.
        # Tämä mahdollistaa sen, että hahmo voi kävellä lavan "päällä" (alueella),
        # ja Y-sort piirtää hahmon lavan päälle, koska hahmon Y > lavan Y.
        coll_rect = pygame.Rect(x + 30, y, w - 60, 25) 
        
        super().__init__(
            x, y, w, h,
            img_path="assets/tiles/muckford/muckford_stage.png",
            collision_rect=coll_rect,
            color=(100, 80, 60)
        )
        self.is_structure = False # Ei ole este AI:lle (paitsi yläreuna)
        self.name = "Stage"

class ShantyHouse(Prop):
    """
    Tavallinen hökkelitalo (pienempi kuin taverna).
    """
    def __init__(self, x, y, variant=1):
        self.variant = variant
        
        if variant == 1:
            # Normi talo (1200x700 -> skaalattu n. 480x280)
            w, h = 480, 280
            img_name = "muckford_house_1.png"
            # Hitbox alhaalla
            coll_rect = pygame.Rect(x + 20, y + h - 60, w - 40, 40)
            
        elif variant == 2:
            # Etupihallinen talo (1200x800 -> skaalattu n. 480x320)
            w, h = 480, 320
            img_name = "muckford_house_2.png"
            # Hitbox vasta kuvan keskiosasta vähän yli (talon seinä)
            # Jättää etupihan vapaaksi (tai aidan sisään)
            coll_y_offset = int(h * 0.40) # Nostettu ylemmäs (enemmän tilaa pihalla)
            coll_h = 50
            coll_rect = pygame.Rect(x + 20, y + coll_y_offset, w - 40, coll_h)
            
        else: # variant 3
            # Isoin talo (Pienennetty pyynnöstä, oli 640x400)
            w, h = 520, 340
            img_name = "muckford_house_3.png"
            # Hitbox alhaalla
            coll_rect = pygame.Rect(x + 30, y + h - 70, w - 60, 50)

        super().__init__(
            x, y, w, h,
            img_path=f"assets/tiles/muckford/{img_name}",
            collision_rect=coll_rect,
            color=(100, 90, 80) # Fallback väri
        )
        self.is_structure = True

class Smeltery(Prop):
    """
    Sulatto. Muuttaa Scrap Ironin ja Puun -> Scrap Metal Bariksi.
    """
    def __init__(self, x, y):
        w, h = 180, 160
        coll_rect = pygame.Rect(x + 20, y + h - 60, w - 40, 50) # Nostettu 10px (oli h-50)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/smeltery.png", color=(60, 50, 50), collision_rect=coll_rect)
        self.is_structure = True
        self.name = "Smeltery"
        
        self.interaction_range = 150
        self.interaction_label = "Use"
        
        # Varasto
        self.current_job = None # {type, timer, max_time}
        self.output_inventory = {} # "Item Name": count
        self.interact_cooldown = 0
        
        # Villager AI support & Automation
        self.wood_stored = 0
        self.scrap_stored = 0
        self.max_storage = 20

    @property
    def bars_ready(self):
        """Yhteensopivuus vanhan koodin kanssa (palauttaa valmiiden tuotteiden määrän)."""
        return sum(self.output_inventory.values())

    @bars_ready.setter
    def bars_ready(self, value):
        """Yhteensopivuus: Jos vanha koodi yrittää nollata tai vähentää valmiita harkkoja."""
        current = self.bars_ready
        if value == 0:
            self.output_inventory.clear()
        elif value < current:
            # Vähennetään tuotteita (vanha koodi kerää harkkoja)
            diff = current - value
            keys = list(self.output_inventory.keys())
            for k in keys:
                if diff <= 0: break
                amount = self.output_inventory[k]
                remove = min(diff, amount)
                self.output_inventory[k] -= remove
                if self.output_inventory[k] <= 0:
                    del self.output_inventory[k]
                diff -= remove

    def interact(self, manager):
        if self.interact_cooldown > 0: return

        # A) Kerää valmiit tuotteet
        if self.output_inventory:
            for item, count in self.output_inventory.items():
                manager.add_material(item, count)
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, f"+{count} {item}", color=(200, 200, 255))
            self.output_inventory.clear()
            sound_system.play_sound("recruit")
            self.interact_cooldown = 20
        
        # B) Avaa valikko (Näytä reseptit ja tila)
        else:
            status_msg = f"Storage: {self.scrap_stored} Scrap, {self.wood_stored} Wood."
            if self.current_job:
                pct = int((self.current_job["timer"] / self.current_job["max_time"]) * 100)
                status_msg += f" Working... ({pct}%)"

            options = [
                {"text": "Scrap Bar (2 Scrap, 1 Wood)", "action": "smelter_scrap"},
                {"text": "Iron Bar (2 Iron Ore, 1 Coal)", "action": "smelter_iron"},
                {"text": "Deposit Resources", "action": "smelter_deposit"},
                {"text": "Cancel", "action": "close"}
            ]
            manager.start_dialogue(self, status_msg, options)
            self.interact_cooldown = 20

    def handle_menu_action(self, action, manager):
        """Kutsutaan GameManagerin dialogista."""
        if self.current_job:
            manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Busy!", color=(255, 50, 50))
            return

        inv = manager.inventory
        
        if action == "smelter_scrap":
            # Resepti: 2 Scrap Iron + 1 Swamp Wood -> 1 Scrap Metal Bar
            if inv.get("Scrap Iron", 0) >= 2 and inv.get("Swamp Wood", 0) >= 1:
                inv["Scrap Iron"] -= 2
                inv["Swamp Wood"] -= 1
                self.current_job = {"output": "Scrap Metal Bar", "timer": 0, "max_time": 300}
                sound_system.play_sound("click")
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Smelting...", color=(200, 200, 200))
            else:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Missing Items!", color=(255, 50, 50))
                sound_system.play_sound("error")

        elif action == "smelter_iron":
            # Resepti: 2 Iron Ore + 1 Coal -> 1 Iron Bar
            if inv.get("Iron Ore", 0) >= 2 and inv.get("Coal", 0) >= 1:
                inv["Iron Ore"] -= 2
                inv["Coal"] -= 1
                self.current_job = {"output": "Iron Bar", "timer": 0, "max_time": 400} # Hieman hitaampi
                sound_system.play_sound("click")
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Smelting...", color=(200, 200, 200))
            else:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Missing Items!", color=(255, 50, 50))
                sound_system.play_sound("error")

        elif action == "smelter_deposit":
            # Talleta kaikki sopivat resurssit (Scrap & Wood) varastoon
            deposited = False
            
            # Scrap
            scrap_space = self.max_storage - self.scrap_stored
            scrap_has = inv.get("Scrap Iron", 0)
            to_add_scrap = min(scrap_space, scrap_has)
            if to_add_scrap > 0:
                inv["Scrap Iron"] -= to_add_scrap
                self.scrap_stored += to_add_scrap
                deposited = True

            # Wood
            wood_space = self.max_storage - self.wood_stored
            wood_has = inv.get("Swamp Wood", 0)
            to_add_wood = min(wood_space, wood_has)
            if to_add_wood > 0:
                inv["Swamp Wood"] -= to_add_wood
                self.wood_stored += to_add_wood
                deposited = True
            
            if deposited:
                sound_system.play_sound("click")
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Deposited", color=(150, 255, 150))
            else:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Nothing to deposit", color=(200, 200, 200))

    def update(self, obstacles=None, manager=None):
        # 0. Villager Automation (Auto-smelt from stored resources)
        if not self.current_job and self.wood_stored >= 1 and self.scrap_stored >= 2:
            self.wood_stored -= 1
            self.scrap_stored -= 2
            self.current_job = {"output": "Scrap Metal Bar", "timer": 0, "max_time": 300}
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Auto-Smelt", color=(200, 200, 200))

        # 1. Prosessointi
        if self.current_job:
            job = self.current_job
            job["timer"] += 1
            
            # VFX: Savua yläreunasta keskeltä
            if job["timer"] % 20 == 0 and manager and hasattr(manager, "vfx"):
                # Savu nousee piipusta/katolta
                smoke_x = self.rect.centerx
                smoke_y = self.rect.top + 10
                manager.vfx.create_smoke(smoke_x, smoke_y)
                
            # VFX: Kipinöintiä satunnaisesti
            if random.random() < 0.05 and manager:
                spark_x = self.rect.centerx + random.randint(-20, 20)
                spark_y = self.rect.bottom - 30
                manager.vfx.create_impact_sparks(spark_x, spark_y, color=(255, 200, 50), count=3)

            # Valmis?
            if job["timer"] >= job["max_time"]:
                out = job["output"]
                self.output_inventory[out] = self.output_inventory.get(out, 0) + 1
                self.current_job = None
                sound_system.play_sound("mining_hit") # Kilahdus
                if manager:
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Done!", color=(100, 255, 100))
                    # Iso pöllähdys kun valmis
                    for _ in range(5):
                        manager.vfx.create_smoke(self.rect.centerx + random.randint(-10, 10), self.rect.top + 10)

        if self.interact_cooldown > 0:
            self.interact_cooldown -= 1

        # Siivoa tyhjät slotit outputista, jotta valikko aukeaa oikein
        if self.output_inventory:
            self.output_inventory = {k: v for k, v in self.output_inventory.items() if v > 0}


    def draw_on_screen(self, screen, offset):
        super().draw_on_screen(screen, offset)
        
        # Piirrä progress bar jos prosessoi
        if self.current_job:
            self.draw_interaction_bar(screen, offset, self.current_job["timer"] / self.current_job["max_time"])
            
        # Piirrä "Ready" ikoni jos harkkoja on valmiina
        if self.output_inventory:
            # Pieni kultainen/hopeinen neliö pään päällä
            bx = self.rect.centerx - offset[0] - 10
            by = self.rect.top - offset[1] - 30
            pygame.draw.rect(screen, (200, 200, 220), (bx, by, 20, 10))
            pygame.draw.rect(screen, (255, 255, 255), (bx, by, 20, 10), 1)

class ChickenCoop(Prop):
    """
    Kanala. Hautoo munista kanoja.
    """
    def __init__(self, x, y):
        w, h = 120, 100
        coll_rect = pygame.Rect(x + 10, y + h - 50, w - 20, 40) # Nostettu 10px (oli h-40)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/coop.png", color=(70, 60, 50), collision_rect=coll_rect)
        self.is_structure = True
        self.name = "Chicken Coop"
        self.eggs_stored = 0
        self.hatch_timer = 0
        self.hatch_time = 1200 # 20 sekuntia

    def update(self, obstacles=None, manager=None):
        if self.eggs_stored > 0:
            self.hatch_timer += 1
            if self.hatch_timer >= self.hatch_time:
                self.hatch_timer = 0
                self.eggs_stored -= 1
                self._spawn_chicken(manager)

    def _spawn_chicken(self, manager):
        if manager:
            from units.farm_animals import Chicken
            cx = self.rect.centerx + random.randint(-20, 20)
            cy = self.rect.bottom + 20
            chick = Chicken(cx, cy)
            manager.all_units.add(chick)
            manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, "Hatched!", color=(255, 255, 200))
            sound_system.play_sound("recruit")

class Well(Prop):
    """
    Kaivo.
    """
    def __init__(self, x, y):
        w, h = 80, 70
        # Hitbox alaosassa
        coll_rect = pygame.Rect(x + 10, y + 30, 60, 40) # Nostettu 10px (oli y+40)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/well.png", color=(60, 60, 70), collision_rect=coll_rect)
        self.is_structure = True
        self.name = "Well"