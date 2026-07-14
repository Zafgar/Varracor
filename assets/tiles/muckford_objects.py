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
        self.is_flat = True  # lattiapassi: pelto ei peitä hahmoja

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
        # Yhtenäinen keräyskanava (pelitesti 16): E tai klikkaus aloittaa
        # hakkuun - isku 45 framen välein kunnes puu kaatuu
        self.required_tool = "axe"
        self.interaction_range = 90
        self.swing_interval = 45

        # Wind sway
        self.sway_timer = random.uniform(0, 100)
        self.base_image = self.image # Keep original for transformation
        self.origin_pos = (x, y) # Store original top-left for pivoting

    def try_begin_channel(self, player, manager=None, max_range_bonus=40):
        consumed = super().try_begin_channel(player, manager,
                                             max_range_bonus)
        if consumed and self.channel_active:
            # Path of the Timber -portti heti alussa (chop näyttäisi
            # viestin vasta ensimmäisellä iskulla)
            try:
                from systems import commander_progression as _prog
                tool = player.equipment.get("main_hand")
                ok, req = _prog.tool_allowed(manager, player, tool,
                                             "forestry",
                                             "forestry_level_required")
                if not ok:
                    if manager:
                        manager.vfx.show_damage(
                            self.rect.centerx, self.rect.top - 40,
                            f"Requires Timber level {req}!",
                            color=(200, 50, 50))
                    self.cancel_channel()
                    return True
            except Exception:
                pass
            # Palkki kattaa jäljellä olevat iskut
            self.channel_swings_needed = max(1, self.current_hits)
        return consumed

    def on_channel_swing(self, player, manager):
        self.chop(player, player.equipment.get("main_hand"), manager)

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

        # Path of the Timber -tasovaatimus (vain sankarille)
        if manager is not None:
            try:
                from systems import commander_progression as _prog
                ok, req = _prog.tool_allowed(manager, attacker, tool,
                                             "forestry",
                                             "forestry_level_required")
                if not ok:
                    manager.vfx.show_damage(self.rect.centerx,
                                            self.rect.top - 40,
                                            f"Requires Timber level {req}!",
                                            color=(200, 50, 50))
                    sound_system.play_sound("error")
                    return
            except Exception:
                pass

        # 2. Osuma
        self.current_hits -= 1
        sound_system.play_sound("axe_1")
        # Path of the Timber: XP sankarin hakkuusta
        if manager is not None:
            try:
                from systems import commander_progression as _prog
                _prog.on_tree_chopped(manager, attacker,
                                      felled=(self.current_hits <= 0))
            except Exception:
                pass 
        
        if manager:
            manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(150, 100, 50), count=3)
            manager.vfx.create_falling_leaves(self.rect.centerx, self.rect.centery)

        # 3. Resurssi per isku (Chance) - Lumberjack II:n chop_speed parantaa
        if random.random() < 0.4 + float(getattr(attacker, "chop_speed", 0.0)) \
                + (int(getattr(tool, "tool_tier", 1)) - 1) * 0.05:
            if manager:
                manager.add_material(self.resource_name, 1)
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, f"+1 {self.resource_name}", color=(150, 255, 100))
                if attacker is manager.player_character:
                    manager.grant_hero_xp(3, self.rect.centerx, self.rect.top)

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
                # Forest Lordin wood_yield antaa lisäpuuta kaadosta
                bonus = int(getattr(attacker, "wood_yield", 0))
                manager.add_material(self.resource_name, 2 + bonus)
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 60, "Timber!", color=(255, 200, 100))
                sound_system.play_sound("mining_break")

    def update(self, obstacles=None, manager=None, **kwargs):
        if self.is_empty: return

        # Keräyskanava (E/klikkaus -> hakkuu iskuineen)
        self.update_channel(manager)
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
        
        self.interaction_label = "Scavenge"
        self.interaction_range = 100

        # Scavenge logic: iso kasa kestää useita tonkaisuja. Yhtenäinen
        # keräyskanava (pelitesti 16) - 2 iskua per haku, jatkuu
        # automaattisesti kunnes kasa tyhjenee tai pelaaja liikkuu.
        self.max_searches = random.randint(4, 7)
        self.current_searches = self.max_searches
        self.swing_interval = 30
        self.channel_swings_needed = 2
        self._restart_pending = False
        
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

    def harvest(self, manager=None, harvester=None):
        """Yksi tonkaisu: arvo saalis, vähennä hakuja. Kanava jatkuu
        automaattisesti kunnes kasa on tyhjä."""
        if self.is_empty or manager is None:
            return
        item = random.choice(self.loot_table)
        qty = random.randint(1, 2) if item == "Scrap Iron" else 1
        manager.add_material(item, qty)
        manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40,
                                f"+{qty} {item}", color=(200, 200, 200))
        if harvester is getattr(manager, "player_character", None):
            manager.grant_hero_xp(3, self.rect.centerx, self.rect.top)
        sound_system.play_sound("recruit")  # "Chime" sound

        self.current_searches -= 1
        if self.current_searches <= 0:
            self.is_empty = True
            self.image.set_alpha(100)  # Himmennä tyhjä kasa
            sound_system.play_sound("mining_break")
        else:
            self._restart_pending = True

    def update(self, obstacles=None, manager=None):
        if self.is_empty: return
        self.update_channel(manager)
        # Jatka tonkimista automaattisesti kunnes kasa tyhjenee
        if self._restart_pending and not self.channel_active and \
                not self.is_empty and manager is not None:
            self._restart_pending = False
            player = getattr(manager, "player_character", None)
            if player is not None:
                self.try_begin_channel(player, manager)

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

class ShantyYardGate(Prop):
    """
    Shanty Yard -areenan sisäänkäynti (Tier 0, The Rookie Dust Circuit).
    Romusta ja tynnyreistä kyhätty portti; E vie liigavalikkoon.
    """
    def __init__(self, x, y):
        w, h = 340, 280
        # Törmäys vain sivupylväissä, keskellä kulkuaukko oveen asti
        coll_rect = pygame.Rect(x, y, w, h - 90)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/shanty_yard_gate.png",
                         color=(90, 70, 50), collision_rect=coll_rect)
        self.door_offset = (w // 2, h - 20)
        self.interaction_range = 100
        self.interaction_label = "Shanty Yard"
        self._draw_procedural_gate(w, h)

    def _draw_procedural_gate(self, w, h):
        """Procedural fallback jos kuvaa ei ole (korvautuu automaattisesti
        kun assets/tiles/muckford/shanty_yard_gate.png lisätään)."""
        if not self.image or self.image.get_at((0, 0)) == (90, 70, 50, 255):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            wood = (110, 85, 55); dark = (70, 55, 40)
            # Pylväät
            pygame.draw.rect(surf, wood, (10, 40, 50, h - 40))
            pygame.draw.rect(surf, wood, (w - 60, 40, 50, h - 40))
            # Kaari + banneri
            pygame.draw.rect(surf, dark, (0, 20, w, 45))
            pygame.draw.rect(surf, (150, 40, 40), (w // 2 - 70, 60, 140, 70))
            pygame.draw.polygon(surf, (150, 40, 40),
                                [(w // 2 - 70, 130), (w // 2 + 70, 130), (w // 2, 160)])
            # Tynnyrit pylväiden juurella
            for bx in (15, w - 55):
                pygame.draw.ellipse(surf, (120, 90, 60), (bx, h - 70, 45, 60))
                pygame.draw.ellipse(surf, dark, (bx, h - 70, 45, 60), 3)
            self.image = surf


class TeamBarracks(Prop):
    """
    Pelaajan oma tiimitila (Team Quarters). Bram antaa nämä köyhät tilat
    kun pelaaja liittyy Tier 0:aan. E avaa tiimivalikon (varusteet + jutut).
    """
    def __init__(self, x, y):
        w, h = 380, 300
        coll_rect = pygame.Rect(x + 20, y + h - 90, w - 40, 70)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/team_barracks.png",
                         color=(70, 65, 55), collision_rect=coll_rect)
        self.door_offset = (w // 2, h - 20)
        self.interaction_range = 100
        self.interaction_label = "Barracks"
        self._draw_procedural(w, h)

    def _draw_procedural(self, w, h):
        if not self.image or self.image.get_at((0, 0)) == (70, 65, 55, 255):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            wall = (95, 80, 62); dark = (60, 50, 40); roof = (120, 70, 55)
            # Runko
            pygame.draw.rect(surf, wall, (20, 90, w - 40, h - 90))
            pygame.draw.rect(surf, dark, (20, 90, w - 40, h - 90), 4)
            # Vino paikattu katto
            pygame.draw.polygon(surf, roof, [(10, 95), (w - 10, 95), (w - 40, 30), (50, 45)])
            pygame.draw.polygon(surf, dark, [(10, 95), (w - 10, 95), (w - 40, 30), (50, 45)], 3)
            # Ovi
            pygame.draw.rect(surf, dark, (w // 2 - 35, h - 90, 70, 90))
            pygame.draw.rect(surf, (150, 130, 90), (w // 2 - 35, h - 90, 70, 90), 3)
            # Ikkunat (laudoitetut)
            for wx in (45, w - 105):
                pygame.draw.rect(surf, (40, 45, 55), (wx, 120, 60, 50))
                pygame.draw.line(surf, wall, (wx, 145), (wx + 60, 145), 4)
            # Kyltti
            pygame.draw.rect(surf, (150, 130, 90), (w // 2 - 50, 100, 100, 22))
            self.image = surf


class NoticeBoard(Prop):
    """
    Ilmoitustaulu torilla. E avaa kylätehtävät (side-tasks): tarjolla
    olevat (maineen mukaan), aktiiviset ja lunastettavat.
    """
    def __init__(self, x, y):
        w, h = 120, 150
        coll_rect = pygame.Rect(x + 10, y + h - 40, w - 20, 30)
        super().__init__(x, y, w, h, img_path="assets/tiles/muckford/notice_board.png",
                         color=(90, 70, 45), collision_rect=coll_rect)
        self.door_offset = (w // 2, h - 10)
        self.interaction_range = 90
        self.interaction_label = "Notices"
        self._draw_procedural(w, h)

    def _draw_procedural(self, w, h):
        if not self.image or self.image.get_at((0, 0)) == (90, 70, 45, 255):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            post = (95, 70, 45); board = (140, 110, 70); paper = (235, 225, 200)
            # Kaksi pylvästä
            pygame.draw.rect(surf, post, (18, 50, 12, h - 50))
            pygame.draw.rect(surf, post, (w - 30, 50, 12, h - 50))
            # Taulu
            pygame.draw.rect(surf, board, (10, 20, w - 20, 80))
            pygame.draw.rect(surf, (70, 50, 30), (10, 20, w - 20, 80), 3)
            # Katos
            pygame.draw.polygon(surf, (110, 60, 45),
                                [(4, 24), (w - 4, 24), (w - 18, 6), (18, 6)])
            # Lappuja
            for px, py in ((22, 34), (58, 30), (40, 60), (74, 58)):
                pygame.draw.rect(surf, paper, (px, py, 22, 20))
                pygame.draw.line(surf, (120, 120, 110), (px + 3, py + 6), (px + 18, py + 6), 1)
                pygame.draw.line(surf, (120, 120, 110), (px + 3, py + 12), (px + 15, py + 12), 1)
            self.image = surf


class HerbalistTent(Prop):
    """Saggan rohtoteltta (pelitesti 18): Muckfordin ainoa parantaja.
    Teltan luona Sagga hoitaa sotureiden sairaudet ja vammat maksusta
    ja myy rohtoja."""

    def __init__(self, x, y):
        w, h = 170, 140
        coll_rect = pygame.Rect(x + 14, y + h - 52, w - 28, 40)
        super().__init__(x, y, w, h,
                         img_path="assets/tiles/muckford/herbalist_tent.png",
                         color=(96, 84, 66), collision_rect=coll_rect)
        self.is_structure = True
        self.name = "Herbalist's Tent"
        self.interaction_range = 110
        self.interaction_label = "Herbalist"
        self._draw_procedural(w, h)

    def _draw_procedural(self, w, h):
        if not self.image or self.image.get_at((0, 0)) == (96, 84, 66, 255):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            canvas = (128, 108, 78)
            canvas_dark = (100, 84, 60)
            # Telttakangas (kolmio) + keskisauma
            pygame.draw.polygon(surf, canvas,
                                [(w // 2, 8), (w - 6, h - 16), (6, h - 16)])
            pygame.draw.polygon(surf, canvas_dark,
                                [(w // 2, 8), (w - 6, h - 16),
                                 (w // 2 + 20, h - 16)])
            pygame.draw.polygon(surf, (66, 54, 40),
                                [(w // 2, 8), (w - 6, h - 16), (6, h - 16)],
                                3)
            # Oviaukko
            pygame.draw.polygon(surf, (36, 30, 26),
                                [(w // 2, 34), (w // 2 + 24, h - 16),
                                 (w // 2 - 24, h - 16)])
            # Yrttikimput narussa
            pygame.draw.line(surf, (70, 58, 42), (14, 46), (w - 14, 46), 2)
            for hx, col in ((30, (96, 150, 90)), (58, (150, 170, 90)),
                            (108, (110, 160, 120)), (138, (170, 140, 90))):
                pygame.draw.line(surf, (70, 58, 42), (hx, 46), (hx, 56), 1)
                pygame.draw.circle(surf, col, (hx, 62), 7)
                pygame.draw.circle(surf, (50, 70, 45), (hx, 62), 7, 1)
            # Pata teltansuulla
            pygame.draw.ellipse(surf, (52, 52, 58), (18, h - 36, 34, 22))
            pygame.draw.ellipse(surf, (30, 30, 34), (18, h - 36, 34, 22), 2)
            pygame.draw.circle(surf, (140, 210, 150), (35, h - 28), 4)
            self.image = surf


class RoadSignpost(Prop):
    """Tienviitta kadun päässä: E avaa maailmankartan reitit.
    Muckfordista lähtee teitä moneen suuntaan - viitta tekee sen
    näkyväksi pelikentällä (ei vain M-näppäimen takana)."""

    def __init__(self, x, y):
        w, h = 90, 140
        coll_rect = pygame.Rect(x + 34, y + h - 34, 22, 26)
        super().__init__(x, y, w, h,
                         img_path="assets/tiles/muckford/road_signpost.png",
                         color=(96, 74, 48), collision_rect=coll_rect)
        self.interaction_range = 100
        self.interaction_label = "World routes"
        self._draw_procedural(w, h)

    def _draw_procedural(self, w, h):
        if not self.image or self.image.get_at((0, 0)) == (96, 74, 48, 255):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            post = (98, 74, 46)
            plank = (140, 110, 70)
            # Pylväs
            pygame.draw.rect(surf, post, (w // 2 - 6, 18, 12, h - 18))
            pygame.draw.rect(surf, (60, 44, 28), (w // 2 - 6, 18, 12, h - 18), 2)
            # Viittalaudat eri suuntiin
            for py, flip, txt_w in ((22, False, 40), (52, True, 34), (82, False, 46)):
                if flip:
                    pts = [(w // 2 - 38, py), (w // 2 + 14, py),
                           (w // 2 + 14, py + 20), (w // 2 - 38, py + 20),
                           (w // 2 - 48, py + 10)]
                else:
                    pts = [(w // 2 - 14, py), (w // 2 + 38, py),
                           (w // 2 + 48, py + 10), (w // 2 + 38, py + 20),
                           (w // 2 - 14, py + 20)]
                pygame.draw.polygon(surf, plank, pts)
                pygame.draw.polygon(surf, (70, 52, 32), pts, 2)
                lx = w // 2 - (34 if flip else -2)
                pygame.draw.line(surf, (74, 58, 40), (lx, py + 10),
                                 (lx + txt_w - 12, py + 10), 2)
            self.image = surf


class QuestCrate(Prop):
    """Krads Missing Crate -questin laatikko hökkelin edustalla.
    Ilmestyy kun tehtävä on aktiivinen; E poimii sen mukaan."""

    def __init__(self, x, y):
        w, h = 64, 56
        super().__init__(x, y, w, h,
                         img_path="assets/tiles/muckford/quest_crate.png",
                         color=(96, 74, 48),
                         collision_rect=pygame.Rect(x, y + 16, w, 40))
        self.interaction_range = 90
        self.interaction_label = "Pick up crate"
        if not self.image or self.image.get_at((0, 0)) == (96, 74, 48, 255):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(surf, (128, 98, 60), (2, 10, w - 4, h - 12),
                             border_radius=4)
            pygame.draw.rect(surf, (66, 48, 30), (2, 10, w - 4, h - 12), 3,
                             border_radius=4)
            pygame.draw.line(surf, (66, 48, 30), (4, h // 2 + 4),
                             (w - 4, h // 2 + 4), 3)
            pygame.draw.line(surf, (66, 48, 30), (w // 2, 12),
                             (w // 2, h - 4), 3)
            # "K"-polttomerkki
            pygame.draw.line(surf, (170, 60, 50), (14, 20), (14, 40), 3)
            pygame.draw.line(surf, (170, 60, 50), (14, 30), (26, 20), 3)
            pygame.draw.line(surf, (170, 60, 50), (14, 30), (26, 40), 3)
            self.image = surf
