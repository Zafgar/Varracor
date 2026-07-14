import pygame
import math
import os
import random
from gladiator import Gladiator
from settings import GREEN, CHEAT_MODE, SCREEN_WIDTH, SCREEN_HEIGHT
from skills.commander_skills_data import (COMMANDER_SKILL_TREE,
                                          COMMANDER_COMMAND_TREE)
from ui_kit import draw_text, font_small, font_main, draw_item_slot_background, GOLD_COLOR, WHITE, draw_icon, draw_panel, draw_item_tooltip, GRAY
from sound_manager import sound_system

# --- HELPER CLASS FOR MATERIALS ---
class MaterialWrapper:
    def __init__(self, name, count):
        self.name = name
        self.count = count
        self.type = "material"
        self.rarity = "Common"
        self.description = "Crafting material."
        self.cost = 0
        self.slot_type = "material"
        self.stats = {}
        
        # Try to fetch real data
        try:
            from items.material_registry import get_material_info
            info = get_material_info(name)
            self.rarity = info.get("rarity", "Common")
            self.description = info.get("desc", "")
            self.cost = info.get("value", 0)
        except Exception: pass
        
    def draw_card_icon(self, screen, x, y, size):
        # Draw count
        draw_text(str(self.count), font_small, WHITE, screen, x + 4, y + size - 20)
        # Draw name (short)
        short = self.name[:6]
        draw_text(short, font_small, (200, 200, 200), screen, x + 4, y + 2)

class Commander(Gladiator):
    def __init__(self, name="Commander", x=0, y=0, team_color=GREEN):
        super().__init__(name, "Human", x, y, team_color)
        # Feet Hitbox
        self.rect = pygame.Rect(x, y, 30, 20) # Pieni fysiikka-hitbox
        # Commander starts with slightly better base stats
        self.base_attributes["str"] = 12
        self.base_attributes["dex"] = 12
        self.base_attributes["int"] = 12
        self.base_attributes["hp"] = 150
        
        # STORY ITEM: Vortex Blade (Menetetään introssa, ellei CHEAT_MODE)
        try:
            from items.swords.vortex_blade import VortexBlade
            self.equipment["main_hand"] = VortexBlade()
        except ImportError: pass

        # CHEAT MODE: Anna loitsut heti alkuun testattavaksi
        if CHEAT_MODE:
            from spells.commander.vortex_warp import VortexWarp
            from spells.commander.seam_cut import SeamCut
            self.equipment["spell1"] = VortexWarp()
            self.equipment["spell2"] = SeamCut()
        
        self.cost = 0 # Commander cannot be bought/sold
        
        self.calculate_final_stats()
        
        # Ensure extra spell slots exist
        for s in ["spell4", "spell5", "spell6"]:
            if s not in self.equipment: self.equipment[s] = None
            
        self.current_hp = self.max_hp
        
        # Commander on pelaajan ohjaama, joten ei AI-kontrolleria
        self.ai_controller = None
        self.facing_right = True
        
        # Tallennetaan peruskuva (idle)
        self.base_image = self.image
        
        # Animaatiomuuttujat
        self.anim_timer = 0
        
        # Input & Spell Targeting
        self.selected_spell_slot = None # "spell1", "spell2", jne.

        # --- HOTBAR (pelitesti 17) ---
        # Sivu 1 = kyvyt/usablet, sivu 2 = pikatyökalut (aseet/työkalut
        # repusta nopeaan vaihtoon). Lukko estää raahausjärjestelyn.
        self.hotbar_page = 1
        self._hotbar_rects = []   # [(rect, slot_name_tai_item)]
        self._hotbar_ui = {}      # "lock"/"up"/"down" -> rect
        self._drag_slot = None    # raahauksen lähtöslotti (sivu 1)
        self.manager_ref = None   # GameManager asettaa (reppu sivulle 2)
        self._melee_hold_block = False  # estää meleen heti castin perään
        self.prev_keys = pygame.key.get_pressed() # Näppäinten tilan seurantaan (toggle)
        self.prev_mouse = (False, False, False) # Hiiren tilan seurantaan

        # Load UI assets
        self.action_button_img = None
        self.hp_frame_img = None
        self.hp_liquid_img = None
        self.mana_frame_img = None
        self.mana_liquid_img = None
        self.action_bar_img = None
        self.stamina_frame_img = None
        self.stamina_energy_img = None
        self.stamina_particles = []
        
        # Inventory UI State
        self.inventory_tab = "GEAR"
        self.inventory_page = 0
        self.inventory_buttons = []
        self.ui_slots = []
        self.dragging_item = None
        self.dragging_from_slot = None
        self.hovered_tooltip_item = None
        
        # Inventory Assets
        self.ui_inv_bg = None
        self.ui_slot_frame = None
        self.ui_inv_main_frame = None
        self.ui_inv_grid_bg = None
        self.ui_equip_bg = None
        self.ui_attributes_bg = None
        self.ui_slot_img = None
        self.ui_attributes_hp_img = None
        self.ui_attributes_mp_img = None
        self.hovered_tooltip_text = None
        self.ui_tab_imgs = {}
        self.ui_money_img = None
        
        self._load_ui_assets()

    def _load_ui_assets(self):
        # Käytetään absoluuttista polkua ja kokeillaan vaihtoehtoja
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths = [
            os.path.join(base_dir, "assets", "ui", "player", "action_button.png"),
            os.path.join(base_dir, "assets", "ui player", "action_button.png")
        ]
        
        action_btn_found = False
        for path in paths:
            if os.path.exists(path):
                try:
                    self.action_button_img = pygame.image.load(path).convert_alpha()
                    print(f"[Commander] Loaded UI asset: {path}")
                    action_btn_found = True
                    break
                except Exception as e: print(f"[Commander] Error loading UI: {e}")
        
        if not action_btn_found:
            print("[Commander] UI asset 'action_button.png' not found.")
        
        # Load HP Orb
        paths_hp = [
            os.path.join(base_dir, "assets", "ui", "player"),
            os.path.join(base_dir, "assets", "ui player")
        ]
        
        for p in paths_hp:
            f_path = os.path.join(p, "hp_frame.png")
            l_path = os.path.join(p, "hp_frame_hp.png")
            if os.path.exists(f_path) and os.path.exists(l_path):
                try:
                    self.hp_frame_img = pygame.image.load(f_path).convert_alpha()
                    self.hp_liquid_img = pygame.image.load(l_path).convert_alpha()
                    print(f"[Commander] Loaded HP Orb assets from {p}")
                    break
                except Exception as e:
                    print(f"[Commander] Error loading HP assets: {e}")
        
        # Load Mana Orb
        for p in paths_hp:
            f_path = os.path.join(p, "mana_frame.png")
            l_path = os.path.join(p, "mana_frame_mana.png")
            if os.path.exists(f_path) and os.path.exists(l_path):
                try:
                    self.mana_frame_img = pygame.image.load(f_path).convert_alpha()
                    self.mana_liquid_img = pygame.image.load(l_path).convert_alpha()
                    print(f"[Commander] Loaded Mana Orb assets from {p}")
                    break
                except Exception as e:
                    print(f"[Commander] Error loading Mana assets: {e}")
        
        # Load Action Bar
        paths_bar = [
            os.path.join(base_dir, "assets", "ui", "player", "action_bar.png"),
            os.path.join(base_dir, "assets", "ui player", "action_bar.png")
        ]
        for p in paths_bar:
            if os.path.exists(p):
                try:
                    self.action_bar_img = pygame.image.load(p).convert_alpha()
                    print(f"[Commander] Loaded Action Bar: {p}")
                    break
                except Exception as e:
                    print(f"[Commander] Error loading Action Bar: {e}")
        
        # Load Stamina Bar
        paths_stam = [
            os.path.join(base_dir, "assets", "ui", "player"),
            os.path.join(base_dir, "assets", "ui player")
        ]
        for p in paths_stam:
            f_path = os.path.join(p, "bar_stamina.png")
            e_path = os.path.join(p, "bar_stamina_energy.png")
            if os.path.exists(f_path) and os.path.exists(e_path):
                try:
                    self.stamina_frame_img = pygame.image.load(f_path).convert_alpha()
                    self.stamina_energy_img = pygame.image.load(e_path).convert_alpha()
                    print(f"[Commander] Loaded Stamina Bar assets from {p}")
                    break
                except Exception as e:
                    print(f"[Commander] Error loading Stamina assets: {e}")
        
        # Load Inventory Assets
        try:
            self.ui_inv_bg = pygame.image.load(os.path.join(base_dir, "assets/ui/inventory/panel_bg.png")).convert_alpha()
            self.ui_slot_frame = pygame.image.load(os.path.join(base_dir, "assets/ui/inventory/slot_frame.png")).convert_alpha()
        except Exception: pass
        
        try:
            path_main = os.path.join(base_dir, "assets/ui player/inventory_main.png")
            if os.path.exists(path_main):
                self.ui_inv_main_frame = pygame.image.load(path_main).convert_alpha()
                print(f"[Commander] Loaded inventory frame: {path_main}")
        except Exception: pass
        
        try:
            path_grid = os.path.join(base_dir, "assets/ui player/grid_9_11.png")
            if os.path.exists(path_grid):
                self.ui_inv_grid_bg = pygame.image.load(path_grid).convert_alpha()
        except Exception: pass
        
        # Load Equip UI
        try:
            path_equip = os.path.join(base_dir, "assets", "ui player", "equip.png")
            if os.path.exists(path_equip):
                self.ui_equip_bg = pygame.image.load(path_equip).convert_alpha()
                print(f"[Commander] Loaded Equip UI: {path_equip}")
        except Exception: pass
        
        # Load Attributes UI
        try:
            path_attr = os.path.join(base_dir, "assets", "ui player", "attributes.png")
            if os.path.exists(path_attr):
                self.ui_attributes_bg = pygame.image.load(path_attr).convert_alpha()
                print(f"[Commander] Loaded Attributes UI: {path_attr}")
            
            path_hp = os.path.join(base_dir, "assets", "ui player", "attributes_hp.png")
            if os.path.exists(path_hp):
                self.ui_attributes_hp_img = pygame.image.load(path_hp).convert_alpha()
                
            path_mp = os.path.join(base_dir, "assets", "ui player", "attributes_mp.png")
            if os.path.exists(path_mp):
                self.ui_attributes_mp_img = pygame.image.load(path_mp).convert_alpha()
                
            # Load Slot Image
            path_slot = os.path.join(base_dir, "assets", "ui player", "slot.png")
            if os.path.exists(path_slot):
                self.ui_slot_img = pygame.image.load(path_slot).convert_alpha()
                print(f"[Commander] Loaded Slot UI: {path_slot}")
                
            # Load Tab Buttons
            self.ui_tab_imgs = {}
            tab_names = {"GEAR": "gear", "SPELLS": "spells", "MATERIALS": "materials"}
            
            for key, name in tab_names.items():
                # Kokeillaan btn_nimi.png ja nimi.png
                candidates = [f"btn_{name}.png", f"{name}.png"]
                for fname in candidates:
                    p1 = os.path.join(base_dir, "assets", "ui player", fname)
                    p2 = os.path.join(base_dir, "assets", "ui", "player", fname)
                    path = p1 if os.path.exists(p1) else p2
                    if os.path.exists(path):
                        try: self.ui_tab_imgs[key] = pygame.image.load(path).convert_alpha()
                        except Exception: pass
                        break
        except Exception: pass
            
        try:
            # Load Money UI
            candidates = [
                os.path.join(base_dir, "assets", "ui player", "money.png"),
                os.path.join(base_dir, "assets", "ui", "player", "money.png"),
                os.path.join(base_dir, "assets", "ui", "money.png")
            ]
            for p in candidates:
                if os.path.exists(p):
                    self.ui_money_img = pygame.image.load(p).convert_alpha()
                    print(f"[Commander] Loaded Money UI: {p}")
                    break
        except Exception: pass

        # VFX Lists
        self.hp_bubbles = []
        self.mana_bubbles = []

    def calculate_final_stats(self):
        super().calculate_final_stats()
        # Commander osaa käyttää kaikkia aseita ja kilpiä (Block vaatii shield-skillin)
        self.weapon_masteries.update(["sword", "axe", "mace", "spear", "dagger", "bow", "crossbow", "staff", "shield"])
        self.armor_masteries.update(["light", "medium", "heavy", "cloth"])

        # --- COMMANDER SKILL TREE EFFECTS ---
        # Gladiator-luokka käsittelee vain perus SKILL_TREE:n.
        # Meidän täytyy käsitellä Commanderin omat taidot tässä.

        # Elämäntaitojen kertymät (nollataan aina ennen silmukkaa, jotta
        # respec/lataus ei tuplaa). Näitä lukevat mm. CropPlot.harvest,
        # IronOre.mine, MuckfordTree.chop, lypsy ja kauppojen hinnoittelu.
        self.mining_speed = 0.0
        self.mining_yield = 0
        self.chop_speed = 0.0
        self.wood_yield = 0
        self.harvest_yield = 0
        self.harvest_quality = 0.0
        self.husbandry = 0
        self.haggler = 0
        self.fishing = 0
        self.insight = 0

        # Johtamispuun kertymät (COMMAND-välilehti)
        self.team_capacity = 6      # johtajuuden sallima roosterin koko
        self.shouts = set()         # avatut taisteluhuudot ("rally"/"charge")
        self.drillmaster = 0        # voitoista tuplamoraali tiimille
        self.iron_presence = 0      # tappioista puolet moraalisakosta

        _LIFE_INT_EFFECTS = ("mining_yield", "wood_yield", "harvest_yield",
                             "husbandry", "haggler", "fishing", "insight")
        _LIFE_FLOAT_EFFECTS = ("mining_speed", "chop_speed", "harvest_quality")

        _ALL_TREES = {**COMMANDER_SKILL_TREE, **COMMANDER_COMMAND_TREE}
        for s_id in self.unlocked_skills:
            if s_id in _ALL_TREES:
                data = _ALL_TREES[s_id]
                effects = data.get("effects", {})

                if "team_cap" in effects:
                    self.team_capacity = max(self.team_capacity,
                                             int(effects["team_cap"]))
                if "shout" in effects:
                    self.shouts.add(str(effects["shout"]))
                if "drillmaster" in effects:
                    self.drillmaster = 1
                if "iron_presence" in effects:
                    self.iron_presence = 1

                if "str" in effects: self.strength += effects["str"]
                if "dex" in effects: self.dexterity += effects["dex"]
                if "int" in effects: self.intelligence += effects["int"]

                if "weapon_prof" in effects:
                    prof = effects["weapon_prof"]
                    # Lisätään weapon_masteries settiin
                    self.weapon_masteries.add(prof)

                if "max_dashes" in effects:
                    self.max_dashes += effects["max_dashes"]

                for key in _LIFE_INT_EFFECTS:
                    if key in effects:
                        setattr(self, key, getattr(self, key) + int(effects[key]))
                for key in _LIFE_FLOAT_EFFECTS:
                    if key in effects:
                        setattr(self, key, getattr(self, key) + float(effects[key]))
        
        # --- COMMANDER PATHS (systems/commander_progression) ---
        # Polkujen milestone-statsit: apply_to_hero() kokoaa nämä
        pe = getattr(self, "_progression_effects", {}) or {}
        self.max_hp += int(pe.get("max_hp", 0))
        self.strength += int(pe.get("str", 0))
        self.dexterity += int(pe.get("dex", 0))
        self.intelligence += int(pe.get("int", 0))
        self.max_mana += int(pe.get("max_mana", 0))
        self.defense += int(pe.get("defense", 0))
        self.max_stamina += int(pe.get("max_stamina", 0))
        self.mana_regen += float(pe.get("mana_regen", 0.0))
        self.crit_chance += float(pe.get("crit_chance", 0.0))
        self.max_strain += int(pe.get("max_strain", 0))
        # Elamantaitopolut (mining/forestry) kasvattavat samoja attribuutteja
        # kuin pistepuun taidot
        self.mining_speed += float(pe.get("mining_speed", 0.0))
        self.mining_yield += int(pe.get("mining_yield", 0))
        self.chop_speed += float(pe.get("chop_speed", 0.0))
        self.wood_yield += int(pe.get("wood_yield", 0))
        # Path of the Vortex: spell slotit ja tierit tasovaatimusten takaa
        for slot in pe.get("unlock_spell_slot", ()):
            self.spell_slots_unlocked.add(int(slot))
        self.max_spell_tier = max(self.max_spell_tier,
                                  int(pe.get("max_spell_tier", 0)))

        # --- STAT SCALING (Attributes -> Pools) ---
        # Lisätään statsien vaikutus HP:hen ja Manaan
        self.max_hp += int(self.strength * 2)
        self.max_mana += int(self.intelligence * 2)
        
        # Varmistetaan että nykyiset arvot pysyvät rajoissa
        self.current_hp = min(self.current_hp, self.max_hp)
        self.current_mana = min(self.current_mana, self.max_mana)

    def can_equip_item_to_slot(self, slot_name, item):
        # CHEAT MODE BYPASS
        if CHEAT_MODE:
            # Tarkista vain että slotti on oikea (spell -> spell slot)
            sname = str(slot_name or "").lower()
            itype = str(getattr(item, "type", "")).lower()
            islot = str(getattr(item, "slot_type", "")).lower()
            
            if "spell" in sname and ("spell" in itype or "spell" in islot):
                return True, ""
            # Muuten käytä normaalia logiikkaa (aseet käsiin jne.)
        
        return super().can_equip_item_to_slot(slot_name, item)

    def load_assets(self):
        # Emme kutsu super().load_assets() alussa, jotta Human-luokan (races/human)
        # kuvia EI ladata muistiin. Tämä estää "väärän PNG:n" periytymisen.

        # 2. Ladataan Commanderin erikoiskuvat
        self.sprites = getattr(self, "sprites", {})
        
        # Käytetään kapeampaa skaalausta (36x64) jotta ei ole "liian leveä"
        target_size = (36, 64)

        def _load_raw(filename):
            path = os.path.join("assets", "player", filename)
            if os.path.exists(path):
                try:
                    return pygame.image.load(path).convert_alpha()
                except Exception: pass
            return None

        def _load(filename):
            img = _load_raw(filename)
            if img:
                return pygame.transform.smoothscale(img, target_size)
            return None

        # Apufunktio: Kokeile useita eri tiedostonimiä
        def _load_any(names):
            for n in names:
                img = _load(n)
                if img: 
                    print(f"[Commander] Loaded sprite: {n}")
                    return img
            return None

        print(f"[Commander] Looking for assets in: {os.path.abspath(os.path.join('assets', 'player'))}")
        
        # Hahmon ID (esim. "1")
        cid = "1"

        # --- SET BIG IMAGE (High Res) ---
        raw_idle = _load_raw(f"commander_idle1_{cid}.png") or _load_raw(f"idle1_{cid}.png") or _load_raw("idle1.png")
        if raw_idle:
            self.big_image = raw_idle

        # Yksittäiset tilat (Kokeillaan eri variaatioita)
        self.sprites["block"] = _load_any([f"commander_block_{cid}.png", f"block_{cid}.png", "block.png"])
        self.sprites["cast"] = _load_any([f"commander_cast_{cid}.png", f"cast_{cid}.png", "cast.png"])
        self.sprites["hurt"] = _load_any([f"commander_hurt_{cid}.png", f"hurt_{cid}.png", "hurt.png"])

        # Hyökkäys
        self.sprites["attack_start"] = _load_any([f"commander_attack1_{cid}.png", f"attack1_{cid}.png", "attack1.png"])
        self.sprites["attack_end"] = _load_any([f"commander_attack2_{cid}.png", f"attack2_{cid}.png", "attack2.png"])
        
        # Ladataan animaatiot (listat)
        self.sprites["idle"] = []
        i1 = _load_any([f"commander_idle1_{cid}.png", f"idle1_{cid}.png", "idle1.png"])
        i2 = _load_any([f"commander_idle2_{cid}.png", f"idle2_{cid}.png", "idle2.png"])
        if i1: self.sprites["idle"].append(i1)
        if i2: self.sprites["idle"].append(i2)
            
        self.sprites["run"] = []
        r1 = _load_any([f"commander_run1_{cid}.png", f"run1_{cid}.png", "run1.png"])
        r2 = _load_any([f"commander_run2_{cid}.png", f"run2_{cid}.png", "run2.png"])
        if r1: self.sprites["run"].append(r1)
        if r2: self.sprites["run"].append(r2)
        
        # Jos edes jotain löytyi, otetaan käyttöön
        if any(self.sprites.values()) or self.sprites.get("idle"):
            self.use_sprites = True
            
            # Asetetaan oletuskuva heti, jotta hahmo ei näytä procedural-ihmiseltä
            if self.sprites["idle"]:
                self.image = self.sprites["idle"][0]
                self.base_image = self.image
            elif self.sprites["attack_start"]:
                self.image = self.sprites["attack_start"]
                self.base_image = self.image
            return True
            
        print("[Commander] No custom sprites found.")
        return False

    def draw_on_screen(self, surface, offset=(0, 0)):
        # 1. RANGE INDICATOR (Piirretään hahmon alle)
        # Selvitä mikä range piirretään (Spell vai Ase)
        draw_range = self.attack_range
        range_color = (255, 255, 255, 30) # Haalea valkoinen oletus
        
        if self.selected_spell_slot:
            item = self.equipment.get(self.selected_spell_slot)
            if item:
                draw_range = getattr(item, "range", 0)
                range_color = (100, 200, 255, 40) # Sinertävä spelleille
        
        if draw_range > 0:
            # Luodaan temporary surface läpinäkyvyyttä varten
            radius = int(draw_range)
            circle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            
            # Piirrä täyttö (hyvin haalea)
            pygame.draw.circle(circle_surf, range_color, (radius, radius), radius)
            # Piirrä ääriviiva (vähän vahvempi)
            border_color = (range_color[0], range_color[1], range_color[2], 100)
            pygame.draw.circle(circle_surf, border_color, (radius, radius), radius, 2)
            
            # Blittaa ruudulle oikeaan kohtaan
            cx, cy = self.rect.center
            surface.blit(circle_surf, (cx - radius - offset[0], cy - radius - offset[1]))
            
        # --- AIMING LINE (Skillshots) ---
        if self.selected_spell_slot:
            item = self.equipment.get(self.selected_spell_slot)
            if item and getattr(item, "is_skillshot", False):
                mx, my = pygame.mouse.get_pos()
                cx = self.rect.centerx - offset[0]
                cy = self.rect.centery - offset[1]
                
                dx = mx - cx
                dy = my - cy
                dist = math.hypot(dx, dy)
                max_r = getattr(item, "range", 0)
                
                if dist > 0:
                    # Rajoita viiva maksimikantamaan
                    draw_dist = min(dist, max_r)
                    
                    # Laske päätepiste
                    ex = cx + (dx/dist) * draw_dist
                    ey = cy + (dy/dist) * draw_dist
                    
                    # Väri (Teal/Cyan Commander teemaan)
                    aim_col = (50, 255, 200)
                    
                    # Piirrä viiva
                    pygame.draw.line(surface, aim_col, (cx, cy), (ex, ey), 2)
                    
                    # Piirrä päätepiste (Tähtäin)
                    pygame.draw.circle(surface, aim_col, (int(ex), int(ey)), 5, 1)
                    pygame.draw.circle(surface, aim_col, (int(ex), int(ey)), 2)

        # 2. NORMAALI PIIRTO (Hahmo + varusteet)
        super().draw_on_screen(surface, offset)

        # 3. ATTACK COOLDOWN INDICATOR (Pään päälle)
        if self.attack_cooldown > 0:
            # Palkin mitat
            bar_w = 40
            bar_h = 4
            bx = self.rect.centerx - bar_w // 2 - offset[0]
            by = self.hurt_rect.top - 10 - offset[1]
            
            # Laske progress (pienenee kun cooldown loppuu)
            pct = self.attack_cooldown / self.attack_speed
            
            # Piirrä tausta ja täyttö (Valkoinen latauspalkki)
            pygame.draw.rect(surface, (50, 50, 50), (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, (220, 220, 220), (bx, by, int(bar_w * pct), bar_h))

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)
        
        self.anim_timer += 1
        
        # Päivitetään sprite tilan mukaan
        target_img = self.base_image
        
        if self.is_blocking and self.sprites.get("block"):
            target_img = self.sprites["block"]
        elif self.animation_state == "hurt" and self.sprites.get("hurt"):
            target_img = self.sprites["hurt"]
        elif self.animation_state == "cast" and self.sprites.get("cast"):
            target_img = self.sprites["cast"]
        elif self.animation_state == "attack":
            # Animaatio: Alussa frame 1, lopussa frame 2
            # animation_timer laskee alaspäin (esim 15 -> 0). Puoliväli n. 8.
            if self.animation_timer > 8 and self.sprites.get("attack_start"):
                target_img = self.sprites["attack_start"]
            elif self.sprites.get("attack_end"):
                target_img = self.sprites["attack_end"]
            elif self.sprites.get("attack_start"):
                target_img = self.sprites["attack_start"]
        
        # Liike-animaatiot
        elif self.animation_state == "run" and self.sprites.get("run"):
            # Vaihda framea joka 10. frame (n. 6fps)
            anim = self.sprites["run"]
            if isinstance(anim, list):
                idx = (self.anim_timer // 10) % len(anim)
                target_img = anim[idx]
            else:
                target_img = anim
        elif self.animation_state == "idle" and self.sprites.get("idle"):
            # Hitaampi idle (n. 2fps)
            anim = self.sprites["idle"]
            if isinstance(anim, list):
                idx = (self.anim_timer // 30) % len(anim)
                target_img = anim[idx]
            else:
                target_img = anim
            
        if target_img and target_img != self.image:
            self.image = target_img
            # ÄLÄ PÄIVITÄ self.rect KOKOA!
            # self.rect on fysiikka-hitbox (jalat), self.image on visuaalinen.
            # Piirto (draw_on_screen) hoitaa kuvan sijoittelun rectin midbottomin perusteella.
            pass

    def _update_shouts(self, keys, manager):
        """Taisteluhuudot: asettaa tiimikäskyn (manager.team_order) jota
        omien gladiaattorien AI seuraa 5 sekuntia. 10 s cooldown."""
        if manager is None:
            return
        from systems import keybinds
        # Käskyn kesto kuluu täällä (commander ajetaan joka frame)
        timer = int(getattr(manager, "team_order_timer", 0))
        if timer > 0:
            manager.team_order_timer = timer - 1
            if manager.team_order_timer == 0:
                manager.team_order = None
        cd = int(getattr(self, "shout_cooldown", 0))
        if cd > 0:
            self.shout_cooldown = cd - 1
            return
        shouts = getattr(self, "shouts", set())
        for action, ability, banner in (
                ("shout_rally", "rally", "RALLY TO ME!"),
                ("shout_charge", "charge", "CHAAARGE!")):
            if ability in shouts and keybinds.pressed(keys, action):
                manager.team_order = {"type": ability}
                manager.team_order_timer = 300   # 5 s
                self.shout_cooldown = 600        # 10 s
                try:
                    manager.vfx.show_damage(self.rect.centerx,
                                            self.rect.top - 50, banner,
                                            color=(255, 210, 90))
                    from sound_manager import sound_system
                    sound_system.play_sound("battle_start")
                except Exception:
                    pass
                break

    def run_combat_ai(self, all_units, obstacles=None, manager=None):
        """
        Commanderin oma 'AI' on pelaajan syöte (WASD + Hiiri).
        """
        if self.is_dead: return
        
        # --- ITEM UPDATES (Tärkeä: Päivittää aseiden cooldownit) ---
        if manager:
            for slot, item in self.equipment.items():
                if item and hasattr(item, "on_update"):
                    item.on_update(self, all_units, manager)
        
        # Estä kontrolli jos stunnattu
        if self.stun_timer > 0: return

        # 0. DASHING (Jos dash on päällä, Gladiator.update hoitaa liikkeen)
        if self.is_dashing:
            return

        # Estä kontrolli jos inventory on auki
        if manager and getattr(manager, "show_inventory", False):
            return

        # BUGIKORJAUS (pelitesti 12): syöte ei saa vuotaa pause-valikon
        # tai dialogin läpi - nappien painelu valikossa castasi loitsuja
        # taustalle. Kun valikko sulkeutuu, pohjassa oleva LMB (valikon
        # sulkenut klikkaus) ei myöskään saa lyödä/castata heti.
        if manager and (getattr(manager, "paused", False)
                        or getattr(manager, "active_dialogue", None)):
            self._resume_input_block = True
            return
        if getattr(self, "_resume_input_block", False):
            self.prev_keys = pygame.key.get_pressed()
            self.prev_mouse = pygame.mouse.get_pressed()
            if self.prev_mouse[0]:
                return  # odotetaan että LMB päästetään irti
            self._resume_input_block = False

        # 1. INPUTS
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        lmb_down = mouse_buttons[0]
        lmb_released = (not lmb_down and self.prev_mouse[0])
        
        mx, my = pygame.mouse.get_pos()
        
        # World coordinates for mouse
        world_mx = mx
        world_my = my
        if manager:
            world_mx += manager.camera_x
            world_my += manager.camera_y

        # 2. KATSESUUNTA (Hiiri)
        self.facing_right = (world_mx >= self.rect.centerx)
        
        # Päivitä attack_vector osoittamaan hiireen (visuaalista kääntöä varten)
        dx = world_mx - self.rect.centerx
        dy = world_my - self.rect.centery
        self.attack_vector = (dx, dy)

        # 3. ACTIONS
        
        # BLOCK (RMB) - Vain jos ei hyökätä (LMB)
        # Tämä estää "kilpikonna"-efektin jos painaa molempia
        if mouse_buttons[2] and not lmb_down:
            self.set_blocking(True)
        else:
            self.set_blocking(False)

        from systems import keybinds

        # COMMANDER SHOUTIT (Rally [G] / Charge [H], avataan COMMAND-puusta)
        self._update_shouts(keys, manager)

        # SPRINT (aktivoituu vasta liikkeessä - ks. LIIKKUMINEN alempana;
        # BUGIKORJAUS: paikallaan seisova ei enää polta staminaa shiftillä)
        _wants_sprint = keybinds.pressed(keys, "sprint")

        # DASH
        if keybinds.pressed(keys, "dash"):
            dx = world_mx - self.rect.centerx
            dy = world_my - self.rect.centery
            self.perform_dash(dx, dy)
            if self.is_dashing: return

        # RACIAL ABILITY - kerran painallusta kohti
        _racial = keybinds.key("racial_ability")
        if keys[_racial] and not self.prev_keys[_racial]:
            if self.racial_cooldown <= 0:
                self.use_racial_ability(manager)
            else:
                sound_system.play_sound("error")

        # SPELL SELECTION (Toggle logic 1-4)
        # Apufunktio tarkistamaan painettiinko nappia juuri nyt.
        # BUGIKORJAUS: tyhjää slottia ei voi enää valita - vanha koodi
        # jätti valinnan päälle ja LMB-melee lakkasi toimimasta kokonaan.
        # Pelitesti 17: instant cast -asetus (options/CONTROLS) castaa
        # HETI kursorin suuntaan ilman valinta+klikkaus -vaihetta.
        # Hotbarin sivulla 2 numeronäppäimet vaihtavat pikatyökalun.
        _PAGE2_IDX = {"spell1": 0, "spell2": 1, "spell3": 2, "usable": 3,
                      "spell4": 3, "spell5": 4, "spell6": 5, "usable2": 6}

        def check_toggle(key_code, slot_name):
            if keys[key_code] and not self.prev_keys[key_code]:
                if getattr(self, "hotbar_page", 1) == 2:
                    self.try_quick_equip(_PAGE2_IDX.get(slot_name, 0),
                                         manager)
                    return
                from systems import hotbar_prefs
                if hotbar_prefs.is_instant(slot_name) and \
                        self.equipment.get(slot_name) is not None:
                    # Suora casti kursorin suuntaan
                    if self._try_use_slot(slot_name, world_mx, world_my,
                                          all_units, manager):
                        self.selected_spell_slot = None
                        self._melee_hold_block = True
                    return
                if self.selected_spell_slot == slot_name:
                    self.selected_spell_slot = None # Deactivate
                elif self.equipment.get(slot_name) is not None:
                    self.selected_spell_slot = slot_name # Activate
                else:
                    sound_system.play_sound("error")

        check_toggle(keybinds.key("spell_1"), "spell1")
        check_toggle(keybinds.key("spell_2"), "spell2")
        check_toggle(keybinds.key("spell_3"), "spell3")
        check_toggle(keybinds.key("usable_1"), "usable")
        check_toggle(keybinds.key("spell_5"), "spell5")
        check_toggle(keybinds.key("spell_6"), "spell6")
        check_toggle(keybinds.key("usable_2"), "usable2")

        # Päivitetään edelliset näppäimet seuraavaa framea varten
        self.prev_keys = keys
        self.prev_mouse = mouse_buttons

        # ATTACK / CAST (LMB)
        if lmb_down:
            if self.selected_spell_slot:
                # Turvaverkko: jos valittu slotti on tyhjentynyt, vapauta
                # valinta jotta melee toimii taas
                if self.equipment.get(self.selected_spell_slot) is None:
                    self.selected_spell_slot = None
                # Yritä käyttää valittua loitsua
                elif self._try_use_slot(self.selected_spell_slot, world_mx, world_my, all_units, manager):
                    # Onnistui: poista valinta JA estä melee kunnes LMB
                    # päästetään irti. BUGIKORJAUS: ilman estoa seuraava
                    # frame (LMB yhä pohjassa, valinta poissa) laukaisi
                    # melee-lyönnin heti castin perään.
                    self.selected_spell_slot = None
                    self._melee_hold_block = True
            elif not getattr(self, "_melee_hold_block", False):
                # Aseen käyttö (Charge tai Attack)
                w = self.equipment.get("main_hand")
                if w and getattr(w, "charge_enabled", False):
                    # Lataava ase (Jousi, Sauva, Varsijousi)
                    w.update_charge(self, manager)
                else:
                    # Normaali lyönti (Miekka, Kirves, Kirja)
                    self.perform_attack(None, manager, target_pos=(world_mx, world_my))

        # RELEASE ATTACK (Jouset yms.)
        if lmb_released:
            # _melee_hold_block: sama klikkaus castasi loitsun - irtipäästö
            # ei saa laukaista release_chargea (= melee-lyöntiä castin perään)
            if not self.selected_spell_slot and \
                    not getattr(self, "_melee_hold_block", False):
                w = self.equipment.get("main_hand")
                if w and getattr(w, "charge_enabled", False):
                    w.release_charge(self, manager, target_pos=(world_mx, world_my))

        # Castin jälkeinen melee-esto raukeaa vasta kun LMB on irti
        # (JA release-käsittely on jo ohitettu tälle framelle)
        if not lmb_down:
            self._melee_hold_block = False


        # 4. LIIKKUMINEN (oletus WASD, sidottavissa)
        dx, dy = 0, 0
        if keybinds.pressed(keys, "move_up"): dy = -1
        if keybinds.pressed(keys, "move_down"): dy = 1
        if keybinds.pressed(keys, "move_left"): dx = -1
        if keybinds.pressed(keys, "move_right"): dx = 1

        # Pelkkä SHIFT ilman WASD: juokse hiiren osoittamaan suuntaan
        if _wants_sprint and dx == 0 and dy == 0:
            _mdx = world_mx - self.rect.centerx
            _mdy = world_my - self.rect.centery
            if math.hypot(_mdx, _mdy) > 60:
                _l = math.hypot(_mdx, _mdy)
                dx, dy = _mdx / _l, _mdy / _l

        self.set_sprinting(_wants_sprint and (dx != 0 or dy != 0))
        
        if dx != 0 or dy != 0:
            l = math.hypot(dx, dy)
            dx, dy = dx/l, dy/l
            self.animation_state = "run" # Pakotetaan juoksu-animaatio WASD-liikkeessä
            
            speed = self.speed
            move_x = dx * speed
            move_y = dy * speed
            
            self.check_wall_collision(move_x, move_y, obstacles)
            
        # 5. ESTÄ PÄÄLLEKKÄISYYS
        self.prevent_overlap(all_units)

    def _find_target_at_pos(self, x, y, all_units):
        best = None
        best_dist = 80 # Toleranssi
        
        for u in all_units:
            if u == self or u.is_dead: continue
            if self.is_ally(u): continue
            
            d = math.hypot(u.rect.centerx - x, u.rect.centery - y)
            if d < best_dist:
                best_dist = d
                best = u
        return best

    def _try_use_slot(self, slot_name, mx, my, all_units, manager):
        item = self.equipment.get(slot_name) 
        if not item: return False
        
        # Cooldown check
        if self.spell_cooldowns.get(slot_name, 0) > 0: return False
        
        # Mana check
        cost = getattr(item, "mana_cost", 0)
        if self.current_mana < cost: return False

        # Target finding
        target = self._find_target_at_pos(mx, my, all_units)
        target_pos = (mx, my)
        
        # Fallback: Jos ei kohdetta, luodaan DummyTarget vanhoille loitsuille
        if not target:
            class DummyTarget:
                def __init__(self, x, y): self.rect = pygame.Rect(x, y, 1, 1); self.is_dead = False; self.team_color = None
                def take_damage(self, *args, **kwargs): return 0
                def heal(self, *args, **kwargs): pass
            target = DummyTarget(mx, my)
        
        # Special handling for Usables (Potions) -> Self cast
        if slot_name in ["usable", "usable2"]:
            target = self
        
        # Cast
        if hasattr(item, "cast"):
            # Otetaan mana talteen ennen loitsua
            mana_before = self.current_mana
            
            # Use item's cast method
            # Note: Some spells might require a target, others might be skillshots or self-buffs.
            # If item.cast returns True, it was successful.
            try:
                success = item.cast(self, target, manager, target_pos=target_pos)
            except TypeError:
                success = item.cast(self, target, manager)
            if success and manager is not None and \
                    self is getattr(manager, "player_character", None):
                # Path of the Weave: XP jokaisesta loitsusta
                try:
                    from systems import commander_progression as _prog
                    _prog.on_player_spell_cast(manager, item)
                except Exception:
                    pass

            if success:
                # Vähennetään manaa vain, jos loitsu ei tehnyt sitä itse (kuten Vortex Warp tekee)
                if self.current_mana == mana_before:
                    self.current_mana -= cost
                
                self.spell_cooldowns[slot_name] = int(getattr(item, "cooldown_max", 60))
                
                # Animation
                self.animation_state = "cast"
                self.animation_timer = 20
                
                # GAME FEEL: Cast Burst (Visuaalinen palaute heti)
                if manager:
                    manager.vfx.create_impact_sparks(self.rect.centerx, self.rect.centery, color=(100, 255, 200), count=8)
                
                return True
        
        return False

    def _draw_racial_indicator(self, screen):
        """Pieni [R]-kykyindikaattori (rotukyky) HUDin vasemmassa alakulmassa."""
        info = self.get_racial_info()
        if not info:
            return
        name = info[0]
        w, h = screen.get_size()
        x, y, size = 24, h - 96, 64
        ready = self.racial_cooldown <= 0
        active = (self.is_invisible or self.stoneform_timer > 0
                  or self.speed_buff_timer > 0)

        border = (255, 220, 120) if ready else (90, 90, 100)
        if active:
            border = (120, 255, 160)
        pygame.draw.rect(screen, (20, 20, 28), (x, y, size, size), border_radius=8)
        pygame.draw.rect(screen, border, (x, y, size, size), 3, border_radius=8)

        # Cooldown-varjostus alhaalta ylös
        if not ready:
            frac = min(1.0, self.racial_cooldown / 1500.0)
            sh = int(size * frac)
            shade = pygame.Surface((size, sh), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 150))
            screen.blit(shade, (x, y + size - sh))
            secs = self.racial_cooldown // 60 + 1
            draw_text(str(secs), font_main, WHITE, screen, x + size // 2 - 8, y + size // 2 - 12)

        draw_text("R", font_main, border, screen, x + 4, y + 2)
        key_font = pygame.font.SysFont("Arial", 11)
        label = key_font.render(name, True, (200, 200, 210))
        screen.blit(label, (x + size // 2 - label.get_width() // 2, y + size + 3))

    def draw_hud(self, screen):
        """Piirtää Commanderin käyttöliittymän (Bars + Quickbar)."""
        w, h = screen.get_size()
        time_ms = pygame.time.get_ticks()
        self._draw_racial_indicator(screen)
        
        # Uudet mitat käyttäjän toiveiden mukaan (506x578 aspect ratio)
        slot_w = 90 
        orig_w, orig_h = 506, 578
        aspect = orig_h / orig_w
        slot_h = int(slot_w * aspect)
        
        gap = -22 # "vähän toistensa päällä" -> negatiivinen väli
        slots = ["spell1", "spell2", "spell3", "spell4", "spell5", "spell6", "usable", "usable2"]
        total_w = len(slots) * slot_w + (len(slots) - 1) * gap
        
        # Center Quickbar
        start_x = (w - total_w) // 2
        start_y = h - slot_h - 10 # Asemointi pohjalle
        
        # --- ORB CONFIG ---
        orb_radius = 65
        orb_y = h - 110 # Laskettu hieman alemmas
        
        # Orbs placed relative to quickbar
        hp_x = start_x - orb_radius - 55 # Siirretty kauemmas vasemmalle
        mana_x = start_x + total_w + orb_radius + 55 # Siirretty kauemmas oikealle

        # --- HELPER: DRAW LIQUID ORB ---
        def draw_orb(cx, cy, radius, current, maximum, color_dark, color_light, label_top, label_bot):
            # 1. Background
            pygame.draw.circle(screen, (10, 10, 10), (cx, cy), radius)
            
            # 2. Liquid
            pct = max(0.0, min(1.0, current / max(1, maximum)))
            if pct > 0:
                surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                
                # Wave params
                wave_h = 8
                fill_h = int(radius * 2 * pct)
                top_y = (radius * 2) - fill_h
                
                # Back wave (Darker, slower)
                offset1 = math.sin(time_ms * 0.002) * wave_h
                rect1 = pygame.Rect(0, top_y + offset1, radius*2, fill_h + 20)
                pygame.draw.rect(surf, color_dark, rect1)
                
                # Front wave (Lighter, faster)
                offset2 = math.cos(time_ms * 0.003) * wave_h
                rect2 = pygame.Rect(0, top_y + offset2 + 5, radius*2, fill_h + 20)
                pygame.draw.rect(surf, color_light, rect2)
                
                # Mask circle
                mask = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(mask, (255, 255, 255), (radius, radius), radius - 4)
                surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                screen.blit(surf, (cx - radius, cy - radius))
            
            # 3. Glass Shine & Border
            pygame.draw.circle(screen, (150, 150, 150), (cx, cy), radius, 4) # Border
            # Shine
            shine_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.arc(shine_surf, (255, 255, 255, 100), (radius//2, radius//4, radius, radius), 0.5, 2.0, 3)
            screen.blit(shine_surf, (cx - radius, cy - radius))

            # 4. Text
            draw_text(str(int(current)), font_main, WHITE, screen, cx - 15, cy - 10)
            draw_text(f"/ {maximum}", font_small, (200, 200, 200), screen, cx - 15, cy + 15)

        # Draw HP Orb (Custom or Default)
        if self.hp_frame_img and self.hp_liquid_img:
            self._draw_custom_hp_orb(screen, hp_x, orb_y, orb_radius)
        else:
            draw_orb(hp_x, orb_y, orb_radius, self.current_hp, self.max_hp, (160, 0, 0), (220, 40, 40), "HP", "")
            
        # Draw Mana Orb (Custom or Default)
        if self.mana_frame_img and self.mana_liquid_img:
            self._draw_custom_mana_orb(screen, mana_x, orb_y, orb_radius)
        else:
            draw_orb(mana_x, orb_y, orb_radius, self.current_mana, self.max_mana, (0, 0, 160), (40, 80, 240), "MP", "")

        # --- 2.5 ACTION BAR & STAMINA BAR ---
        
        # Laske Action Barin mitat (jotta Stamina Bar voidaan skaalata samaan leveyteen)
        ab_width = total_w # Fallback
        ab_height = 50
        if self.action_bar_img:
            target_slot_h = 50
            scale = target_slot_h / 260.0
            ab_width = int(self.action_bar_img.get_width() * scale)
            ab_height = int(self.action_bar_img.get_height() * scale)
            
        # Sijoita Action Bar Quickbarin yläpuolelle (Nostetaan ylemmäs jotta Stamina mahtuu väliin)
        # Jätetään tilaa staminalle (n. 35px)
        action_bar_y = start_y - ab_height - 35
        self._draw_action_bar(screen, start_x, action_bar_y, total_w)

        # --- 3. QUICKBAR (CENTER, sivullinen - pelitesti 17) ---
        self._hotbar_rects = []
        page = getattr(self, "hotbar_page", 1)
        if page == 1:
            for i, slot_name in enumerate(slots):
                bx = start_x + i * (slot_w + gap)
                item = self.equipment.get(slot_name)
                is_selected = (self.selected_spell_slot == slot_name)
                cd = self.spell_cooldowns.get(slot_name, 0)
                self._draw_slot_frame(screen, bx, start_y, slot_w, slot_h,
                                      item=item, label=str(i + 1),
                                      cooldown=cd, is_selected=is_selected)
                self._hotbar_rects.append(
                    (pygame.Rect(bx, start_y, slot_w, slot_h), slot_name))
        else:
            # Sivu 2: pikatyökalut/aseet repusta (klikkaus/näppäin vaihtaa
            # käteen - esim. kirves hakkuuseen, hakku louhintaan)
            quick = self._quick_items()
            for i in range(8):
                bx = start_x + i * (slot_w + gap)
                item = quick[i] if i < len(quick) else None
                in_hand = (item is not None
                           and item is self.equipment.get("main_hand"))
                self._draw_slot_frame(screen, bx, start_y, slot_w, slot_h,
                                      item=item, label=str(i + 1),
                                      cooldown=0, is_selected=in_hand)
                self._hotbar_rects.append(
                    (pygame.Rect(bx, start_y, slot_w, slot_h), item))
        self._draw_hotbar_extras(screen, start_x, start_y, total_w,
                                 slot_w, slot_h, mana_x, orb_y, orb_radius)

        # --- 4. STAMINA BAR (BELOW ACTION BAR) ---
        
        if self.stamina_frame_img and self.stamina_energy_img:
            # Laske skaalaus (sama kuin _draw_custom_stamina_bar käyttää sisäisesti)
            orig_fill_w = 1009
            stam_scale = ab_width / float(orig_fill_w)
            
            # Asemointi: Action Barin alapuolelle
            # _draw_custom_stamina_bar käyttää bottom_y ankkurina (Y=121 kuvassa).
            # Haluamme kuvan yläreunan alkavan Action Barin alta.
            orig_bar_bottom_y = 121
            stamina_y = int(action_bar_y + ab_height - 15 + (orig_bar_bottom_y * stam_scale))
            
            # Piirretään kustomoitu palkki
            self._draw_custom_stamina_bar(screen, start_x + total_w // 2, stamina_y, ab_width)
        else:
            # Fallback: Vanha palkki
            stam_w = ab_width
            stam_h = 8
            stam_x = start_x + (total_w - stam_w) // 2
            stam_y = action_bar_y + ab_height + 5
            
            pct_stam = max(0, self.current_stamina / self.max_stamina)
            
            # Tausta
            pygame.draw.rect(screen, (40, 40, 0), (stam_x, stam_y, stam_w, stam_h), border_radius=2)
            # Palkki
            pygame.draw.rect(screen, (220, 180, 0), (stam_x, stam_y, int(stam_w * pct_stam), stam_h), border_radius=2)

    def _draw_custom_stamina_bar(self, screen, cx, bottom_y, hud_width):
        # Alkuperäiset mitat: 1312x210
        # Täyttöalue: X 153 -> 1162 (leveys 1009), Y-bottom 121
        orig_fill_w = 1009
        orig_fill_start_x = 153
        orig_bar_bottom_y = 121
        
        # Skaalaus: Sovitetaan täyttöalue HUDin leveyteen (total_w)
        scale = hud_width / float(orig_fill_w)
        
        target_w = int(self.stamina_frame_img.get_width() * scale)
        target_h = int(self.stamina_frame_img.get_height() * scale)
        
        # Asemointi: bottom_y on kohta johon palkin "alareuna" (121px kohdalla) osuu
        # Lasketaan kuvan yläkulma
        draw_x = cx - target_w // 2
        draw_y = bottom_y - int(orig_bar_bottom_y * scale)
        
        # 1. Draw Frame
        frame_scaled = pygame.transform.smoothscale(self.stamina_frame_img, (target_w, target_h))
        screen.blit(frame_scaled, (draw_x, draw_y))
        
        # 2. Draw Energy (Cropped)
        pct = max(0.0, min(1.0, self.current_stamina / self.max_stamina))
        
        # Lasketaan kuinka paljon alkuperäisestä kuvasta näytetään
        # Näytetään vasemmalta (0) kohtaan (153 + 1009 * pct) asti
        visible_orig_w = int(orig_fill_start_x + orig_fill_w * pct)
        
        if visible_orig_w > 0:
            # Rajataan alkuperäisestä kuvasta
            crop_rect = pygame.Rect(0, 0, visible_orig_w, self.stamina_energy_img.get_height())
            cropped_surf = self.stamina_energy_img.subsurface(crop_rect)
            
            # Skaalataan rajattu pala
            scaled_crop_w = int(visible_orig_w * scale)
            if scaled_crop_w > 0:
                final_surf = pygame.transform.smoothscale(cropped_surf, (scaled_crop_w, target_h))
                screen.blit(final_surf, (draw_x, draw_y))
                
                # 3. Fire Particles (Tip of the bar)
                tip_x = draw_x + scaled_crop_w
                tip_y = draw_y + int(orig_bar_bottom_y * scale)
                
                if pct < 1.0 and random.random() < 0.4:
                    self.stamina_particles.append({'x': tip_x, 'y': tip_y, 'vx': random.uniform(-1, 0.5), 'vy': random.uniform(-2, -0.5), 'life': random.randint(10, 20), 'size': random.randint(2, 5)})

        # Update & Draw Particles
        for p in self.stamina_particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            p['size'] *= 0.95
            if p['life'] <= 0:
                self.stamina_particles.remove(p)
            else:
                col = (255, 200, 50) if random.random() < 0.5 else (255, 100, 0)
                # Piirretään hehkuva ympyrä
                s = pygame.Surface((int(p['size']*2), int(p['size']*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*col, 150), (int(p['size']), int(p['size'])), int(p['size']))
                screen.blit(s, (p['x'] - p['size'], p['y'] - p['size']))

    def _draw_custom_hp_orb(self, screen, cx, cy, radius):
        # Alkuperäiset koordinaatit
        liq_top_orig = 164
        liq_bottom_orig = 494
        liq_h_orig = liq_bottom_orig - liq_top_orig
        
        # Skaalaus: Sovitetaan nestealue pallon kokoon (halkaisija)
        scale = (radius * 2.0) / liq_h_orig
        
        target_w = int(self.hp_frame_img.get_width() * scale)
        target_h = int(self.hp_frame_img.get_height() * scale)
        
        # Asemointi: Keskitetään nestealueen keskipiste (ei kuvan keskipiste)
        orb_center_y_orig = (liq_top_orig + liq_bottom_orig) / 2
        
        x = cx - target_w // 2
        y = cy - int(orb_center_y_orig * scale)
        
        # 1. Draw Frame
        frame_scaled = pygame.transform.smoothscale(self.hp_frame_img, (target_w, target_h))
        screen.blit(frame_scaled, (x, y))
        
        # 2. Draw Liquid with Wave
        
        # Skaalatut koordinaatit
        liq_top = liq_top_orig * scale
        liq_bottom = liq_bottom_orig * scale
        liq_h = liq_bottom - liq_top
        
        pct = max(0.0, min(1.0, self.current_hp / max(1, self.max_hp)))
        current_level = liq_bottom - (liq_h * pct)
        
        # Cache liquid image if needed (optimization)
        if not hasattr(self, "_cached_hp_liquid") or self._cached_hp_liquid[0] != target_w:
             self._cached_hp_liquid = (target_w, pygame.transform.smoothscale(self.hp_liquid_img, (target_w, target_h)))
        liquid_scaled = self._cached_hp_liquid[1]
        
        # Wave animation parameters
        time_ms = pygame.time.get_ticks()
        wave_amp = 3 * scale # Aallon korkeus
        wave_freq = 0.05
        wave_speed = 0.005
        
        # Piirretään neste viipaleina aaltoilun luomiseksi
        strip_w = 2
        for i in range(0, target_w, strip_w):
            offset = math.sin(i * wave_freq + time_ms * wave_speed) * wave_amp
            strip_y = current_level + offset
            strip_y = max(liq_top, min(liq_bottom, strip_y)) # Clamp
            
            sy_int = int(strip_y)
            h_strip = int(liq_bottom - strip_y)
            
            if h_strip > 0:
                screen.blit(liquid_scaled, (x + i, y + sy_int), (i, sy_int, strip_w, h_strip))
        
        # 3. Bubbles VFX
        if random.random() < 0.15:
            bx = x + random.randint(20, target_w - 20)
            by = y + liq_bottom - random.randint(10, 40) # Spawnataan nesteen pohjalle
            if math.hypot(bx - cx, by - cy) < radius - 5:
                self.hp_bubbles.append({'x': bx, 'y': by, 'speed': random.uniform(0.5, 1.5), 'size': random.randint(2, 4)})
        
        for b in self.hp_bubbles[:]:
            b['y'] -= b['speed']
            # Check surface
            rel_x = b['x'] - x
            wave_off = math.sin(rel_x * wave_freq + time_ms * wave_speed) * wave_amp
            surf_y = y + current_level + wave_off
            
            if b['y'] < surf_y:
                self.hp_bubbles.remove(b)
                continue
            
            # Draw (Light Red)
            pygame.draw.circle(screen, (255, 150, 150), (int(b['x']), int(b['y'])), b['size'])

        # Text
        draw_text(str(int(self.current_hp)), font_main, WHITE, screen, cx - 15, cy - 10)

    def _draw_custom_mana_orb(self, screen, cx, cy, radius):
        # Alkuperäiset koordinaatit
        liq_top_orig = 151
        liq_bottom_orig = 510
        liq_h_orig = liq_bottom_orig - liq_top_orig
        
        # Skaalaus
        scale = (radius * 2.0) / liq_h_orig
        
        target_w = int(self.mana_frame_img.get_width() * scale)
        target_h = int(self.mana_frame_img.get_height() * scale)
        
        # Asemointi
        orb_center_y_orig = (liq_top_orig + liq_bottom_orig) / 2
        
        x = cx - target_w // 2
        y = cy - int(orb_center_y_orig * scale)
        
        # 1. Draw Frame
        frame_scaled = pygame.transform.smoothscale(self.mana_frame_img, (target_w, target_h))
        screen.blit(frame_scaled, (x, y))
        
        # 2. Draw Liquid with Wave
        
        # Skaalatut koordinaatit
        liq_top = liq_top_orig * scale
        liq_bottom = liq_bottom_orig * scale
        liq_h = liq_bottom - liq_top
        
        pct = max(0.0, min(1.0, self.current_mana / max(1, self.max_mana)))
        current_level = liq_bottom - (liq_h * pct)
        
        # Cache liquid image if needed
        if not hasattr(self, "_cached_mana_liquid") or self._cached_mana_liquid[0] != target_w:
             self._cached_mana_liquid = (target_w, pygame.transform.smoothscale(self.mana_liquid_img, (target_w, target_h)))
        liquid_scaled = self._cached_mana_liquid[1]
        
        # Wave animation parameters
        time_ms = pygame.time.get_ticks()
        wave_amp = 3 * scale
        wave_freq = 0.05
        wave_speed = 0.005
        
        # Piirretään neste viipaleina
        strip_w = 2
        for i in range(0, target_w, strip_w):
            offset = math.sin(i * wave_freq + time_ms * wave_speed) * wave_amp
            strip_y = current_level + offset
            strip_y = max(liq_top, min(liq_bottom, strip_y)) # Clamp
            
            sy_int = int(strip_y)
            h_strip = int(liq_bottom - strip_y)
            
            if h_strip > 0:
                screen.blit(liquid_scaled, (x + i, y + sy_int), (i, sy_int, strip_w, h_strip))
        
        # 3. Bubbles VFX
        if random.random() < 0.15:
            bx = x + random.randint(20, target_w - 20)
            by = y + liq_bottom - random.randint(10, 40)
            if math.hypot(bx - cx, by - cy) < radius - 5:
                self.mana_bubbles.append({'x': bx, 'y': by, 'speed': random.uniform(0.5, 1.5), 'size': random.randint(2, 4)})
        
        for b in self.mana_bubbles[:]:
            b['y'] -= b['speed']
            # Check surface
            rel_x = b['x'] - x
            wave_off = math.sin(rel_x * wave_freq + time_ms * wave_speed) * wave_amp
            surf_y = y + current_level + wave_off
            
            if b['y'] < surf_y:
                self.mana_bubbles.remove(b)
                continue
            
            # Draw (Light Blue)
            pygame.draw.circle(screen, (150, 200, 255), (int(b['x']), int(b['y'])), b['size'])

        # Text
        draw_text(str(int(self.current_mana)), font_main, WHITE, screen, cx - 15, cy - 10)

    def _draw_slot_frame(self, screen, x, y, w, h, item=None, label="", cooldown=0, is_selected=False):
        rect = pygame.Rect(x, y, w, h)
        
        # Oletusarvot ikonille (koko alue)
        icon_x, icon_y, icon_w, icon_h = x, y, w, h
        
        # 1. Background / Frame (Action Button Image)
        if self.action_button_img:
            # Skaalataan kuva napin kokoon
            img = pygame.transform.smoothscale(self.action_button_img, (w, h))
            screen.blit(img, (x, y))
            
            # Lasketaan ikonin paikka annettujen pikselimittojen mukaan
            # Original: 506x578
            # Top: 133, Left: 105, Right: 107, Bottom: 171
            
            scale_x = w / 506
            scale_y = h / 578
            
            off_l = 105 * scale_x
            off_t = 133 * scale_y
            off_r = 107 * scale_x
            off_b = 171 * scale_y
            
            icon_x = x + off_l
            icon_y = y + off_t
            icon_w = w - off_l - off_r
            icon_h = h - off_t - off_b
            
            # Jos valittu, piirretään korostusreuna
            if is_selected:
                # Piirretään korostus ikonin ympärille
                sel_rect = pygame.Rect(icon_x, icon_y, icon_w, icon_h)
                pygame.draw.rect(screen, GOLD_COLOR, sel_rect, 2, border_radius=5)
        else:
            # Fallback: Piirretään laatikko jos kuvaa ei ole
            bg_col = (30, 30, 40)
            if is_selected:
                bg_col = (50, 60, 50)
            pygame.draw.rect(screen, bg_col, rect, border_radius=5)
            
            border_col = (70, 70, 80)
            if is_selected:
                border_col = GOLD_COLOR
            pygame.draw.rect(screen, border_col, rect, 2 if is_selected else 1, border_radius=5)

        # 2. Item Icon
        if item:
            # Keskitetään ikoni laskettuun neliöön
            draw_size = min(icon_w, icon_h)
            draw_x = icon_x + (icon_w - draw_size) / 2
            draw_y = icon_y + (icon_h - draw_size) / 2
            
            if hasattr(item, "draw_card_icon"):
                item.draw_card_icon(screen, draw_x, draw_y, draw_size)
            
            # Cooldown Overlay
            if cooldown > 0:
                max_cd = getattr(item, "cooldown_max", 60)
                pct = cooldown / max(1, max_cd)
                
                # Piirretään overlay ikonin päälle
                overlay_h = int(icon_h * pct)
                s = pygame.Surface((icon_w, overlay_h), pygame.SRCALPHA)
                s.fill((0, 0, 0, 150))
                screen.blit(s, (icon_x, icon_y + icon_h - overlay_h))
                
                seconds = math.ceil(cooldown / 60)
                txt = font_main.render(str(seconds), True, WHITE)
                tr = txt.get_rect(center=(icon_x + icon_w/2, icon_y + icon_h/2))
                screen.blit(txt, tr)

        # 3. Label (Hotkey)
        if label:
            # Piirretään numero ikonin yläpuolelle tai kehyksen yläosaan
            draw_text(label, font_small, (220, 220, 220), screen, icon_x - 5, icon_y - 15)

    # ------------------------------------------------------------------
    # HOTBAR-LISÄT (pelitesti 17): sivut, lukko, raahaus, tooltipit
    # ------------------------------------------------------------------
    def _quick_items(self):
        """Sivun 2 pikatyökalut: repun aseet/työkalut, työkalut ensin."""
        m = self.manager_ref
        if m is None:
            return []
        bag = [it for it in getattr(m, "equipment_bag", [])
               if getattr(it, "type", "") in
               ("weapon", "tool", "melee", "ranged")]
        tools = [it for it in bag
                 if getattr(it, "tool_type", "none") not in ("", "none")]
        others = [it for it in bag if it not in tools]
        current = self.equipment.get("main_hand")
        head = [current] if current is not None else []
        return (head + tools + others)[:8]

    def try_quick_equip(self, idx, manager=None):
        """Vaihtaa pikatyökalun käteen (vanha ase takaisin reppuun)."""
        quick = self._quick_items()
        if idx >= len(quick) or quick[idx] is None:
            sound_system.play_sound("error")
            return False
        item = quick[idx]
        current = self.equipment.get("main_hand")
        if item is current:
            return True
        if not self.can_equip_item_to_slot("main_hand", item):
            sound_system.play_sound("error")
            m = manager or self.manager_ref
            if m is not None:
                m.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                  "Can't wield that yet!",
                                  color=(255, 120, 120))
            return False
        m = self.manager_ref
        bag = getattr(m, "equipment_bag", None) if m else None
        if bag is not None and item in bag:
            bag.remove(item)
        if current is not None and getattr(current, "name", "") != "Fists" \
                and bag is not None:
            bag.append(current)
        self.equipment["main_hand"] = item
        self.calculate_final_stats()
        sound_system.play_sound("click")
        if m is not None:
            m.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                              f"{getattr(item, 'name', 'Item')} ready!",
                              color=(180, 220, 255))
        return True

    def _draw_hotbar_extras(self, screen, start_x, start_y, total_w,
                            slot_w, slot_h, mana_x, orb_y, orb_radius):
        """Sivunuolet, lukko (mana-orbin vieressä), sivun nimi ja
        hover-tooltipit hotbarin slotteihin."""
        from systems import hotbar_prefs
        ui = {}
        # Sivunuolet hotbarin oikealla puolella
        ax = start_x + total_w + 6
        up = pygame.Rect(ax, start_y + 4, 30, max(24, slot_h // 2 - 8))
        down = pygame.Rect(ax, start_y + slot_h // 2 + 4, 30,
                           max(24, slot_h // 2 - 8))
        page = getattr(self, "hotbar_page", 1)
        for rect, glyph, active in ((up, "▲", page > 1),
                                    (down, "▼", page < 2)):
            pygame.draw.rect(screen, (30, 28, 24), rect, border_radius=6)
            pygame.draw.rect(screen, (150, 130, 80), rect, 1,
                             border_radius=6)
            col = GOLD_COLOR if active else (100, 95, 85)
            surf = font_small.render(glyph, True, col)
            screen.blit(surf, surf.get_rect(center=rect.center))
        ui["up"] = up
        ui["down"] = down
        label = "ABILITIES" if page == 1 else "TOOLS & WEAPONS"
        draw_text(f"{label}  ({page}/2)", font_small, (190, 175, 140),
                  screen, start_x + 4, start_y - 16)

        # Lukko mana-orbin vieressä
        lock = pygame.Rect(mana_x + orb_radius + 8, orb_y - 14, 30, 34)
        locked = hotbar_prefs.is_locked()
        pygame.draw.rect(screen, (30, 28, 24), lock, border_radius=7)
        pygame.draw.rect(screen, (150, 130, 80), lock, 1, border_radius=7)
        body = pygame.Rect(lock.x + 7, lock.y + 15, 16, 12)
        col = (220, 190, 110) if locked else (140, 200, 150)
        pygame.draw.rect(screen, col, body, border_radius=3)
        # Sanka: kiinni = molemmat päät rungossa, auki = toinen pää irti
        if locked:
            pygame.draw.arc(screen, col, (lock.x + 8, lock.y + 5, 14, 16),
                            0, math.pi, 2)
        else:
            pygame.draw.arc(screen, col, (lock.x + 12, lock.y + 3, 14, 16),
                            0, math.pi * 0.9, 2)
        ui["lock"] = lock
        self._hotbar_ui = ui

        # Raahauksen haamu (sivu 1, lukko auki)
        if self._drag_slot is not None:
            item = self.equipment.get(self._drag_slot)
            if item is not None and hasattr(item, "draw_card_icon"):
                mx, my = pygame.mouse.get_pos()
                item.draw_card_icon(screen, mx - 22, my - 22, 44)

        # Hover-tooltip slotin päällä (nimi, kuvaus, cooldown, damage)
        mx, my = pygame.mouse.get_pos()
        for rect, ref in self._hotbar_rects:
            if not rect.collidepoint((mx, my)):
                continue
            item = self.equipment.get(ref) if isinstance(ref, str) else ref
            if item is None:
                break
            draw_item_tooltip(screen, item, mx, my, player_unit=self)
            if isinstance(ref, str):
                cd = self.spell_cooldowns.get(ref, 0)
                lines = []
                cd_max = getattr(item, "cooldown_max", 0)
                if cd_max:
                    lines.append(f"Cooldown {cd_max / 60.0:.1f}s"
                                 + (f"  (ready in {cd / 60.0:.1f}s)"
                                    if cd > 0 else ""))
                if hotbar_prefs.is_instant(ref):
                    lines.append("Instant cast: ON")
                yy = my - 20
                for line in lines:
                    surf = font_small.render(line, True, (170, 220, 200))
                    bg = pygame.Surface((surf.get_width() + 10,
                                         surf.get_height() + 4),
                                        pygame.SRCALPHA)
                    bg.fill((10, 12, 14, 210))
                    screen.blit(bg, (mx + 18, yy))
                    screen.blit(surf, (mx + 23, yy + 2))
                    yy -= 24
            break

    def handle_hotbar_event(self, event, manager=None):
        """Hotbarin syöte: lukko, sivunuolet, sivun 2 pikavaihto ja
        sivun 1 raahausjärjestely (lukko auki). Palauttaa True jos
        event kulutettiin (ei mene pelimaailmaan)."""
        from systems import hotbar_prefs
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            ui = self._hotbar_ui or {}
            if ui.get("lock") and ui["lock"].collidepoint(event.pos):
                hotbar_prefs.toggle_locked()
                sound_system.play_sound("click")
                return True
            if ui.get("up") and ui["up"].collidepoint(event.pos):
                self.hotbar_page = max(1, getattr(self, "hotbar_page", 1) - 1)
                sound_system.play_sound("click")
                return True
            if ui.get("down") and ui["down"].collidepoint(event.pos):
                self.hotbar_page = min(2, getattr(self, "hotbar_page", 1) + 1)
                sound_system.play_sound("click")
                return True
            for i, (rect, ref) in enumerate(self._hotbar_rects):
                if not rect.collidepoint(event.pos):
                    continue
                if getattr(self, "hotbar_page", 1) == 2:
                    self.try_quick_equip(i, manager)
                    return True
                if not hotbar_prefs.is_locked() and isinstance(ref, str) \
                        and self.equipment.get(ref) is not None:
                    self._drag_slot = ref
                    return True
                return False  # lukittu sivu 1: klikkaus toimii kuten ennen
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 \
                and self._drag_slot is not None:
            src = self._drag_slot
            self._drag_slot = None
            for rect, ref in self._hotbar_rects:
                if rect.collidepoint(event.pos) and isinstance(ref, str) \
                        and ref != src:
                    # Vaihda sisällöt (vain kykysivulla)
                    self.equipment[src], self.equipment[ref] = \
                        self.equipment.get(ref), self.equipment.get(src)
                    self.selected_spell_slot = None
                    sound_system.play_sound("click")
                    return True
            return True  # raahaus päättyi tyhjään - kuluta silti
        return False

    def _draw_boots_icon(self, screen, x, y, size):
        """Dash-ruudun saappaat + vauhtiviivat (koodipiirretty)."""
        s = size
        col = (205, 170, 110)
        dark = (120, 92, 56)
        for ox in (int(s * 0.16), int(s * 0.52)):
            # Varsi + jalkaterä
            pygame.draw.rect(screen, col, (x + ox, y + int(s * 0.25),
                                           int(s * 0.2), int(s * 0.4)),
                             border_radius=3)
            pygame.draw.rect(screen, col,
                             (x + ox, y + int(s * 0.58), int(s * 0.32),
                              int(s * 0.18)), border_radius=3)
            pygame.draw.line(screen, dark, (x + ox, y + int(s * 0.74)),
                             (x + ox + int(s * 0.32), y + int(s * 0.74)), 2)
        for i in range(3):
            ly = y + int(s * (0.3 + i * 0.18))
            pygame.draw.line(screen, (160, 200, 220),
                             (x - int(s * 0.08), ly),
                             (x + int(s * 0.08), ly), 2)

    def _draw_shield_icon(self, screen, x, y, size):
        """Block-ruudun kilpi (koodipiirretty fallback)."""
        s = size
        cx = x + s // 2
        pts = [(cx, y + 2), (x + s - 3, y + int(s * 0.22)),
               (x + s - 5, y + int(s * 0.62)), (cx, y + s - 2),
               (x + 5, y + int(s * 0.62)), (x + 3, y + int(s * 0.22))]
        pygame.draw.polygon(screen, (110, 120, 140), pts)
        pygame.draw.polygon(screen, (60, 66, 80), pts, 2)
        pygame.draw.line(screen, (60, 66, 80), (cx, y + 4),
                         (cx, y + s - 4), 2)

    def _draw_action_tooltip(self, screen, key, mx, my):
        """Toimintoruudun hover-info: mikä toiminto, millä välineellä."""
        weapon = self.equipment.get("main_hand")
        wname = getattr(weapon, "name", "Fists") if weapon else "Fists"
        if key == "LMB":
            title = "ATTACK (Left Mouse)"
            lines = [f"Strike with {wname}.",
                     f"Damage {int(getattr(weapon, 'damage', 0) or 0)}"
                     if weapon else "Unarmed strikes."]
        elif key == "HOLD":
            title = "POWER (Hold LMB)"
            if weapon and getattr(weapon, "charge_enabled", False):
                lines = [f"Charge {wname} and release."]
            else:
                lines = [f"Heavy swings with {wname}."]
        elif key == "SPACE":
            title = "DASH (Space)"
            lines = [f"Dash toward the mouse. "
                     f"Charges {self.current_dashes}/{self.max_dashes}."]
        else:
            off = self.equipment.get("off_hand")
            has_shield = off is not None and \
                getattr(off, "armor_group", "") == "shield"
            title = "BLOCK (Right Mouse)"
            lines = [f"Block with {getattr(off, 'name', wname)}."
                     if has_shield else f"Guard with {wname}.",
                     "Blocking drains stamina."]
        w = max(font_main.size(title)[0],
                *(font_small.size(t)[0] for t in lines)) + 24
        h = 34 + len(lines) * 22
        bx = min(mx + 16, SCREEN_WIDTH - w - 10)
        by = my - h - 12
        pygame.draw.rect(screen, (16, 16, 22), (bx, by, w, h),
                         border_radius=8)
        pygame.draw.rect(screen, (150, 130, 80), (bx, by, w, h), 1,
                         border_radius=8)
        draw_text(title, font_main, GOLD_COLOR, screen, bx + 12, by + 6)
        yy = by + 32
        for line in lines:
            draw_text(line, font_small, (200, 200, 205), screen,
                      bx + 12, yy)
            yy += 22

    def _draw_action_bar(self, screen, x, y, w):
        """Piirtää 4 toimintoruutua: Attack, Power, Block, Dash."""
        
        # Uusi kuvapohjainen piirto
        if self.action_bar_img:
            # Skaalaus: Tavoitekorkeus slotille n. 50px
            # Alkuperäinen slotin korkeus: 418 - 158 = 260px
            target_slot_h = 50
            scale = target_slot_h / 260.0
            
            img_w = self.action_bar_img.get_width()
            img_h = self.action_bar_img.get_height()
            
            target_w = int(img_w * scale)
            target_h = int(img_h * scale)
            
            # Keskitetään
            draw_x = x + (w - target_w) // 2
            draw_y = y
            
            # Piirrä taustakuva
            scaled_img = pygame.transform.smoothscale(self.action_bar_img, (target_w, target_h))
            screen.blit(scaled_img, (draw_x, draw_y))
            
            # Määritellään slotit (Alkuperäiset koordinaatit)
            # Järjestys: LMB, Power, Dash, Block
            slots_def = [
                ("LMB",   77, 158, 353-77, 260),
                ("HOLD",  399, 158, 656-399, 260),
                ("SPACE", 708, 158, 969-708, 260),
                ("RMB",   1017, 158, 1282-1017, 260)
            ]
            
            hover_info = None
            mxp, myp = pygame.mouse.get_pos()
            for key, ox, oy, ow, oh in slots_def:
                # Skaalaa koordinaatit
                sx = draw_x + int(ox * scale)
                sy = draw_y + int(oy * scale)
                sw = int(ow * scale)
                sh = int(oh * scale)

                # --- SISÄLTÖIKONIT (pelitesti 17) ---
                # LMB/POWER = kädessä oleva ase, DASH = saappaat,
                # BLOCK = kilpi (tai ase jolla torjutaan)
                pad = max(4, sw // 8)
                icon_s = min(sw, sh) - pad * 2
                weapon = self.equipment.get("main_hand")
                if key in ("LMB", "HOLD"):
                    if weapon is not None and hasattr(weapon,
                                                      "draw_card_icon"):
                        weapon.draw_card_icon(screen, sx + pad, sy + pad,
                                              icon_s)
                elif key == "SPACE":
                    self._draw_boots_icon(screen, sx + pad, sy + pad, icon_s)
                elif key == "RMB":
                    shield = None
                    off = self.equipment.get("off_hand")
                    if off is not None and \
                            getattr(off, "armor_group", "") == "shield":
                        shield = off
                    if shield is not None and hasattr(shield,
                                                      "draw_card_icon"):
                        shield.draw_card_icon(screen, sx + pad, sy + pad,
                                              icon_s)
                    elif weapon is not None and hasattr(weapon,
                                                        "draw_card_icon"):
                        weapon.draw_card_icon(screen, sx + pad, sy + pad,
                                              icon_s)
                    else:
                        self._draw_shield_icon(screen, sx + pad, sy + pad,
                                               icon_s)

                # Hover-info kerätään; piirretään loopin jälkeen päällimmäiseksi
                if pygame.Rect(sx, sy, sw, sh).collidepoint((mxp, myp)):
                    hover_info = (key, mxp, myp)

                # --- OVERLAYS ---
                # 1. Cooldown Overlay (LMB & HOLD)
                active_cd = 0
                if key == "LMB":
                    active_cd = self.attack_cooldown
                elif key == "HOLD":
                    weapon = self.equipment.get("main_hand")
                    if weapon and hasattr(weapon, "special_cooldown"):
                        active_cd = weapon.special_cooldown
                    else:
                        active_cd = self.attack_cooldown

                if active_cd > 0:
                    s = pygame.Surface((sw, sh), pygame.SRCALPHA)
                    s.fill((0, 0, 0, 150)) # Tummennus
                    screen.blit(s, (sx, sy))
                    
                    seconds = math.ceil(active_cd / 60)
                    txt = font_main.render(str(seconds), True, WHITE)
                    tr = txt.get_rect(center=(sx + sw//2, sy + sh//2))
                    screen.blit(txt, tr)

                # 2. Charge Progress (HOLD)
                elif key == "HOLD" and self.is_charging:
                    weapon = self.equipment.get("main_hand")
                    if weapon:
                        pct = min(1.0, weapon.charge_time / weapon.max_charge)
                        h_bar = int(sh * pct)
                        s = pygame.Surface((sw, h_bar), pygame.SRCALPHA)
                        s.fill((100, 200, 255, 150))
                        screen.blit(s, (sx, sy + sh - h_bar))

                # 3. Dash Recharge (SPACE)
                elif key == "SPACE":
                    if self.is_dashing:
                        # Active dash highlight
                        pygame.draw.rect(screen, (100, 255, 255), (sx, sy, sw, sh), 2, border_radius=5)
                    elif self.current_dashes < self.max_dashes:
                        pct = 1.0 - (self.dash_recharge_timer / self.dash_recharge_time)
                        h_bar = int(sh * pct)
                        s = pygame.Surface((sw, h_bar), pygame.SRCALPHA)
                        s.fill((100, 255, 255, 100))
                        screen.blit(s, (sx, sy + sh - h_bar))
                    
                    # Dash count
                    if self.current_dashes > 0:
                        draw_text(str(self.current_dashes), font_small, WHITE, screen, sx + sw - 20, sy + sh - 25)

                # 4. Block Active (RMB)
                elif key == "RMB" and self.is_blocking:
                    pygame.draw.rect(screen, GOLD_COLOR, (sx, sy, sw, sh), 2, border_radius=5)

            # Hover-tooltip toimintoruuduille
            if hover_info is not None:
                self._draw_action_tooltip(screen, *hover_info)
            return

        # Fallback: Vanha piirtotapa
        slot_s = 50 # Isommat ruudut
        gap = 10
        total_w = 4 * slot_s + 3 * gap
        start_x = x + (w - total_w) // 2
        
        actions = ["LMB", "HOLD", "RMB", "SPACE"]
        
        for i, key in enumerate(actions):
            bx = start_x + i * (slot_s + gap)
            rect = pygame.Rect(bx, y, slot_s, slot_s)
            
            # Tausta
            bg_col = (40, 40, 50)
            border_col = (100, 100, 100)
            
            # Tila-logiikka
            active = False
            
            if key == "LMB": # Attack
                if self.attack_cooldown > 0:
                    bg_col = (60, 30, 30)
            
            elif key == "HOLD": # Power Attack
                weapon = self.equipment.get("main_hand")
                if weapon and getattr(weapon, "charge_enabled", False):
                    if self.is_charging:
                        # Charge progress bar logic handled below
                        bg_col = (60, 60, 100)
                        active = True
                    elif self.attack_cooldown > 0:
                        # Näytä cooldown myös tässä, koska se estää latauksen
                        bg_col = (60, 30, 30)
                else:
                    border_col = (60, 60, 60) # Disabled
            
            elif key == "RMB": # Block
                if self.is_blocking:
                    active = True
                    bg_col = (50, 100, 50)
                    border_col = GOLD_COLOR
            
            elif key == "SPACE": # Dash
                if self.is_dashing:
                    active = True
                    bg_col = (50, 100, 100)
                elif self.current_dashes < self.max_dashes:
                    # Näytä lataus (handled below)
                    # bg_col pysyy normaalina, overlay näyttää latauksen
                    pass
            
            pygame.draw.rect(screen, bg_col, rect, border_radius=4)
            pygame.draw.rect(screen, border_col, rect, 2, border_radius=4)
            
            # Icons (Keskelle)
            cx, cy = bx + slot_s//2, y + slot_s//2
            if key == "LMB": draw_icon(screen, "sword", cx - 6, cy, WHITE)
            elif key == "HOLD": draw_icon(screen, "star", cx, cy, (100, 200, 255))
            elif key == "RMB": draw_icon(screen, "shield", cx, cy, WHITE) # Shield icon placeholder (use plus or similar if shield missing)
            elif key == "SPACE": draw_icon(screen, "play", cx - 4, cy, WHITE) # Play icon as 'move/dash'

            # --- OVERLAYS ---
            
            # 1. Attack Cooldown (LMB & HOLD)
            if key in ["LMB", "HOLD"] and self.attack_cooldown > 0:
                # Full gray overlay + number
                s = pygame.Surface((slot_s, slot_s), pygame.SRCALPHA)
                s.fill((0, 0, 0, 180))
                screen.blit(s, (bx, y))
                
                seconds = math.ceil(self.attack_cooldown / 60)
                txt = font_main.render(str(seconds), True, WHITE)
                tr = txt.get_rect(center=(bx + slot_s//2, y + slot_s//2))
                screen.blit(txt, tr)

            # 2. Charge Progress (HOLD)
            elif key == "HOLD" and self.is_charging:
                weapon = self.equipment.get("main_hand")
                pct = min(1.0, weapon.charge_time / weapon.max_charge)
                h = int(slot_s * pct)
                s = pygame.Surface((slot_s, h), pygame.SRCALPHA)
                s.fill((100, 200, 255, 150))
                screen.blit(s, (bx, y + slot_s - h))

            # 3. Dash Recharge (SPACE)
            elif key == "SPACE" and self.current_dashes < self.max_dashes:
                pct = 1.0 - (self.dash_recharge_timer / self.dash_recharge_time)
                h = int(slot_s * pct)
                s = pygame.Surface((slot_s, h), pygame.SRCALPHA)
                s.fill((100, 255, 255, 100))
                screen.blit(s, (bx, y + slot_s - h))
            
            # Dash count (jos > 0)
            if key == "SPACE":
                draw_text(str(self.current_dashes), font_small, WHITE, screen, bx + slot_s - 15, y + slot_s - 20)
            
            # Tekstit (Pienemmät ja siistimmät)
            # Key (Yläkulma)
            key_surf = pygame.font.SysFont("Arial", 10).render(key, True, (200, 200, 200))
            screen.blit(key_surf, (bx + 3, y + 2))

    # =========================================================
    # INVENTORY UI IMPLEMENTATION
    # =========================================================
    def draw_inventory(self, screen, manager):
        self.inventory_buttons = []
        self.ui_slots = [] # Nollaa slotit joka frame
        self.hovered_tooltip_item = None # Nollaa tooltip-kohde
        self.hovered_tooltip_text = None # Nollaa teksti-tooltip
        
        # Overlay
        from ui_kit import get_fullscreen_overlay
        screen.blit(get_fullscreen_overlay((0, 0, 0, 200)), (0, 0))
        
        # --- UUSI KEHYS LOGIIKKA ---
        if self.ui_inv_main_frame:
            orig_w, orig_h = 1419, 991
            # Skaalataan kehys sopivaksi ruudulle (esim. 90% korkeudesta)
            panel_h_full = int(SCREEN_HEIGHT * 1.05) # Kasvatettu kokoa (oli 0.99)
            aspect = orig_w / orig_h
            panel_w_full = int(panel_h_full * aspect)
            
            px_full = (SCREEN_WIDTH - panel_w_full) // 2
            py_full = (SCREEN_HEIGHT - panel_h_full) // 2

            # Piirrä skaalattu kehys
            frame_scaled = pygame.transform.smoothscale(self.ui_inv_main_frame, (panel_w_full, panel_h_full))
            screen.blit(frame_scaled, (px_full, py_full))

            # Laske sisäalueen mitat ja sijainti (ylikirjoitetaan px, py, panel_w, panel_h)
            scale_x = panel_w_full / orig_w
            scale_y = panel_h_full / orig_h
            
            px = int(px_full + (85 * scale_x))
            py = int(py_full + (124 * scale_y))
            panel_w = int(panel_w_full - (85 * scale_x) - (88 * scale_x))
            panel_h = int(panel_h_full - (124 * scale_y) - (91 * scale_y))
        else:
            # Fallback vanhaan paneeliin jos kuvaa ei löydy
            panel_w, panel_h = 1100, 750
            px = (SCREEN_WIDTH - panel_w) // 2
            py = (SCREEN_HEIGHT - panel_h) // 2
            if self.ui_inv_bg:
                bg_scaled = pygame.transform.smoothscale(self.ui_inv_bg, (panel_w, panel_h))
                screen.blit(bg_scaled, (px, py))
            else:
                draw_panel(screen, px, py, panel_w, panel_h, title="COMMANDER'S ARMORY", color=(25, 25, 30), border_color=(80, 70, 50))
        
        # --- TABS ---
        tabs = ["GEAR", "SPELLS", "MATERIALS"]
        tab_w = 180
        tab_h = 46 # 15% korkeampi
        tx = px + panel_w - (len(tabs) * (tab_w + 10)) - 70 # Hieman vasemmalle
        ty = py + 20
        
        mouse_pos = pygame.mouse.get_pos()
        
        for t in tabs:
            rect = pygame.Rect(tx, ty, tab_w, tab_h)
            
            # Piirrä kuva jos löytyy, muuten vanha laatikko
            img = self.ui_tab_imgs.get(t)
            if img:
                scaled = pygame.transform.smoothscale(img, (tab_w, tab_h))
                screen.blit(scaled, rect)
                # Aktiivinen tabi korostetaan reunalla
                if t == self.inventory_tab:
                    pygame.draw.rect(screen, GOLD_COLOR, rect, 2, border_radius=5)
            else:
                # Fallback
                col = GOLD_COLOR if t == self.inventory_tab else GRAY
                bg_col = (60, 50, 40) if t == self.inventory_tab else (40, 40, 45)
                pygame.draw.rect(screen, bg_col, rect, border_radius=5)
                if t == self.inventory_tab:
                    pygame.draw.rect(screen, GOLD_COLOR, rect, 2, border_radius=5)
                txt_surf = font_main.render(t, True, col)
                txt_rect = txt_surf.get_rect(center=rect.center)
                screen.blit(txt_surf, txt_rect)
            
            # Hover & Click Effect (Harmaa efekti)
            if rect.collidepoint(mouse_pos):
                s = pygame.Surface((tab_w, tab_h), pygame.SRCALPHA)
                if pygame.mouse.get_pressed()[0]:
                    s.fill((0, 0, 0, 80)) # Tummempi painettaessa
                else:
                    s.fill((200, 200, 200, 40)) # Vaalea harmaa hover
                screen.blit(s, rect)
            
            self.inventory_buttons.append((rect, ("tab", t)))
            tx += tab_w + 10
            
        # --- CONTENT ---
        # Jaetaan ruutu kahtia: Vasen (Hahmo) ja Oikea (Reppu)
        left_w = 550 # Kasvatettu tilaa hahmopaneelille (oli 400)
        right_x = px + left_w + 20 + 160 # Grid alkaa heti paneelin jälkeen (siirretty oikealle)
        content_y = py + 30 # Nostettu ylemmäs (oli +80), jotta grid mahtuu
        grid_y = content_y + 40 # Siirretty alas
        
        # Vasen paneeli (Hahmo & Statsit)
        self._draw_character_panel(screen, px + 20, content_y, left_w, panel_h - 100, manager)
        
        if self.inventory_tab == "GEAR":
            self._draw_backpack_grid(screen, right_x, grid_y, panel_w - left_w - 60, panel_h - 100, manager, filter_type="gear")
        elif self.inventory_tab == "SPELLS":
            self._draw_backpack_grid(screen, right_x, grid_y, panel_w - left_w - 60, panel_h - 100, manager, filter_type="spell")
        elif self.inventory_tab == "MATERIALS":
            self._draw_backpack_grid(screen, right_x, grid_y, panel_w - left_w - 60, panel_h - 100, manager, filter_type="material")
            
        # Draw Dragging Item (Cursor)
        if self.dragging_item:
            mx, my = pygame.mouse.get_pos()
            self.dragging_item.draw_card_icon(screen, mx - 30, my - 30, 60)
            
        draw_text("Press 'I' or 'ESC' to close", font_small, GRAY, screen, px + panel_w - 200, py + panel_h - 30)

        # UUSI: Piirretään tooltip aivan päällimmäiseksi (jos jokin slotti asetti sen)
        if self.hovered_tooltip_item:
            mx, my = pygame.mouse.get_pos()
            draw_item_tooltip(screen, self.hovered_tooltip_item, mx + 15, my + 15, self)
        elif self.hovered_tooltip_text:
            mx, my = pygame.mouse.get_pos()
            # Luodaan väliaikainen objekti tooltipin piirtoa varten
            class TooltipDummy:
                def __init__(self, name, desc):
                    self.name = name
                    self.description = desc
                    self.rarity = "Common"
                    self.stats = {}
                    self.level_required = 1
                    self.cost = 0
                    self.slot_type = "Stat Info"
            
            name, desc = self.hovered_tooltip_text
            draw_item_tooltip(screen, TooltipDummy(name, desc), mx + 15, my + 15)

    def _draw_character_panel(self, screen, x, y, w, h, manager=None):
        """Piirtää hahmon, statsit ja varustepaikat 'Paperdoll' -tyylillä."""
        
        # UUSI EQUIP-NÄKYMÄ (Kaikki TABit)
        if self.ui_equip_bg:
            # Adjust position
            equip_x = x + 80 # More right
            equip_y = y - 40 # Slightly up

            # Skaalataan kuva paneelin leveyteen
            img_w = self.ui_equip_bg.get_width()
            img_h = self.ui_equip_bg.get_height()
            scale = w / img_w
            target_h = int(img_h * scale)
            
            # Piirrä taustakuva
            scaled_bg = pygame.transform.smoothscale(self.ui_equip_bg, (w, target_h))
            screen.blit(scaled_bg, (equip_x, equip_y))
            
            # Määritellään slotit (Alkuperäiset koordinaatit kuvassa)
            # (name, x, y, w, h)
            slots_def = [
                ("head", 114, 171, 295-114, 343-171),
                ("off_hand", 868, 175, 1050-868, 344-175),
                ("main_hand", 97, 477, 280-97, 632-477),
                ("body", 885, 475, 1081-885, 633-475)
            ]
            
            for name, ox, oy, ow, oh in slots_def:
                sx = equip_x + int(ox * scale)
                sy = equip_y + int(oy * scale)
                sw = int(ow * scale)
                sh = int(oh * scale)
                
                item = self.equipment.get(name)
                # Piirrä slotti (läpinäkyvä tausta, koska kuvassa on kehykset)
                self._draw_interactive_slot(screen, sx, sy, sw, item, "equip", name, transparent_bg=True, h=sh)

            # Statsit kuvan alle
            stats_y = equip_y + target_h + 5
            self._draw_stats_block(screen, equip_x, stats_y, w, scale_mult=0.5)
            
            # Ability Bar (Statsien oikealle puolelle)
            # Stats vie n. puolet leveydestä (scale_mult=0.5)
            ab_x = equip_x + int(w * 0.5) + 20
            ab_y = stats_y
            self._draw_ability_bar(screen, ab_x, ab_y)
            
            # Money Panel (Ability Barin alle)
            if manager:
                money_y = ab_y + 220 # Items-rivin alle (Items loppuu n. ab_y + 205)
                self._draw_money_panel(screen, ab_x, money_y, int(w * 0.5), manager)
            return

        # VANHA NÄKYMÄ (Fallback tai SPELLS tab)
        self._draw_legacy_character_panel(screen, x, y, w, h, manager)

    def _draw_legacy_character_panel(self, screen, x, y, w, h, manager=None):
        # Vanha koodi siirretty tänne
        
        # Tausta paneelille
        pygame.draw.rect(screen, (20, 20, 25), (x, y, w, h), border_radius=8)
        pygame.draw.rect(screen, (50, 50, 60), (x, y, w, h), 2, border_radius=8)
        
        # --- 1. PORTRAIT (Keskellä ylhäällä) ---
        cx = x + w // 2
        cy = y + 120
        
        # Portrait Frame
        p_w, p_h = 140, 200
        p_rect = pygame.Rect(cx - p_w//2, y + 20, p_w, p_h)
        pygame.draw.rect(screen, (10, 10, 15), p_rect)
        
        # Draw Character Image
        if hasattr(self, "big_image") and self.big_image:
            # Sovita kuva kehykseen
            scaled = pygame.transform.smoothscale(self.big_image, (p_w - 10, p_h - 10))
            screen.blit(scaled, (p_rect.x + 5, p_rect.y + 5))
        
        pygame.draw.rect(screen, GOLD_COLOR, p_rect, 2)
        
        # --- 2. EQUIPMENT SLOTS (Kuvan ympärillä) ---
        slot_s = 60
        
        layout = []
        if self.inventory_tab == "GEAR":
            layout = [
                ("head", cx - slot_s//2, y - 30),
                ("body", p_rect.left - slot_s - 15, p_rect.top + 40),
                ("main_hand", p_rect.left - slot_s - 15, p_rect.bottom - 60),
                ("off_hand", p_rect.right + 15, p_rect.bottom - 60),
            ]

        for slot_name, sx, sy in layout:
            item = self.equipment.get(slot_name)
            # Piirrä slotti ja rekisteröi se
            self._draw_interactive_slot(screen, sx, sy, slot_s, item, "equip", slot_name)
            
            # Tyhjä slotti -ikoni (Placeholder teksti)
            if not item:
                short_name = slot_name[:4].upper()
                draw_text(short_name, font_small, (60, 60, 70), screen, sx + 10, sy + 20)

        # --- 3. STATS (Alhaalla) ---
        self._draw_stats_block(screen, x, y + 320, w)

    def _draw_stats_block(self, screen, x, y, w, scale_mult=1.0):
        # UUSI ATTRIBUTES-NÄKYMÄ
        if self.ui_attributes_bg:
            # Skaalataan kuva paneelin leveyteen * scale_mult
            img_w = self.ui_attributes_bg.get_width()
            img_h = self.ui_attributes_bg.get_height()
            
            target_w = int(w * scale_mult)
            scale = target_w / img_w
            target_h = int(img_h * scale)
            
            scaled_bg = pygame.transform.smoothscale(self.ui_attributes_bg, (target_w, target_h))
            screen.blit(scaled_bg, (x, y))
            
            # Määritellään arvojen paikat (Alkuperäiset Y-koordinaatit kuvassa)
            # X-alue kaikille: 410 - 620
            # (Label, y1, y2, FullName, Description)
            attr_defs = [
                ("STR", 277, 330, "Strength", "Increases Physical Damage and Stamina."),
                ("DEX", 347, 400, "Dexterity", "Increases Attack Speed, Movement Speed, and Crit Chance."),
                ("INT", 418, 471, "Intelligence", "Increases Magic Damage and Mana."),
                ("SPD", 486, 540, "Movement Speed", "Determines how fast you move."),
                ("ASP", 555, 607, "Attack Speed", "Attacks per second."),
                ("DEF", 626, 678, "Defense", "Reduces incoming Physical Damage."),
                ("HP",  695, 747, "Health Points", "If this reaches 0, you are defeated."),
                ("MP",  767, 817, "Mana Points", "Resource for casting spells.")
            ]
            
            mouse_pos = pygame.mouse.get_pos()
            
            # Valitse fontti koon mukaan
            use_font = font_small if scale_mult < 0.6 else font_main
            
            for label, y1, y2, full_name, desc in attr_defs:
                # Laske skaalattu alue
                rect_x = x + int(410 * scale)
                rect_y = y + int(y1 * scale)
                rect_w = int((620 - 410) * scale)
                rect_h = int((y2 - y1) * scale)
                
                rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)
                
                # Hae arvo
                val = ""
                if label == "STR": val = str(self.strength)
                elif label == "DEX": val = str(self.dexterity)
                elif label == "INT": val = str(self.intelligence)
                elif label == "SPD": val = f"{self.speed:.1f}"
                elif label == "ASP": 
                    aps = 60.0 / max(1, self.attack_speed)
                    val = f"{aps:.2f}/s"
                elif label == "DEF": val = str(self.defense)
                elif label == "HP": val = str(self.max_hp)
                elif label == "MP": val = str(self.max_mana)
                
                # Piirrä arvo tai palkki
                if label == "HP" and self.ui_attributes_hp_img:
                    # Piirrä HP Bar (410 -> 611, korkeus 695 -> 747)
                    # Leveys 611 - 410 = 201
                    self._draw_horizontal_bar(screen, x, y, scale, self.ui_attributes_hp_img, self.current_hp, self.max_hp, (410, 695, 201, 52))
                elif label == "MP" and self.ui_attributes_mp_img:
                    # Piirrä MP Bar (410 -> 611, korkeus 767 -> 817)
                    # Leveys 611 - 410 = 201
                    self._draw_horizontal_bar(screen, x, y, scale, self.ui_attributes_mp_img, self.current_mana, self.max_mana, (410, 767, 201, 50))
                
                # Piirrä teksti AINA (palkin päälle)
                txt_surf = use_font.render(val, True, WHITE)
                txt_rect = txt_surf.get_rect(center=rect.center)
                screen.blit(txt_surf, txt_rect)
                
                # Tooltip hoverilla
                if rect.collidepoint(mouse_pos):
                    self.hovered_tooltip_text = (full_name, desc)
            return

        # VANHA TEKSTIPOHJAINEN STATS-BLOCK (Fallback)
        stats_y = y
        
        draw_text("ATTRIBUTES", font_main, GOLD_COLOR, screen, x + 20, stats_y)
        
        # Piirretään statsit kahdessa sarakkeessa
        col1_x = x + 20
        col2_x = x + w // 2 + 10
        curr_y = stats_y + 30
        line_h = 25
        
        # Helper
        def draw_stat(lbl, val, col_x, col_y, color=WHITE):
            draw_text(f"{lbl}:", font_small, (180, 180, 180), screen, col_x, col_y)
            draw_text(str(val), font_main, color, screen, col_x + 60, col_y - 2)

        draw_stat("STR", self.strength, col1_x, curr_y, (255, 100, 100))
        draw_stat("HP", f"{int(self.current_hp)}/{self.max_hp}", col2_x, curr_y, (100, 255, 100))
        curr_y += line_h
        
        draw_stat("DEX", self.dexterity, col1_x, curr_y, (100, 255, 100))
        draw_stat("MP", f"{int(self.current_mana)}/{self.max_mana}", col2_x, curr_y, (100, 150, 255))
        curr_y += line_h
        
        draw_stat("INT", self.intelligence, col1_x, curr_y, (100, 150, 255))
        draw_stat("STAM", int(self.max_stamina), col2_x, curr_y, (255, 215, 0))
        curr_y += line_h
        
        draw_stat("DEF", self.defense, col1_x, curr_y, (200, 200, 200))
        draw_stat("SPD", f"{self.speed:.1f}", col2_x, curr_y, (220, 220, 220))

    def _draw_horizontal_bar(self, screen, x, y, scale, img, current, maximum, box_rect):
        """Piirtää vaakasuuntaisen palkin aaltoilevalla reunalla."""
        if not img: return

        pct = max(0.0, min(1.0, current / max(1, maximum)))
        
        # Alkuperäiset koordinaatit kuvassa
        start_x_orig = box_rect[0]
        bar_top_orig = box_rect[1]
        bar_h_orig = box_rect[3]
        bar_w_orig = box_rect[2]
        
        # Skaalataan kuva paneelin kokoon
        target_w = int(img.get_width() * scale)
        target_h = int(img.get_height() * scale)
        
        # Cache (Optimointi)
        cache_key = (id(img), target_w, target_h)
        if not hasattr(self, "_bar_cache"): self._bar_cache = {}
        if cache_key not in self._bar_cache:
             self._bar_cache[cache_key] = pygame.transform.smoothscale(img, (target_w, target_h))
        
        scaled_img = self._bar_cache[cache_key]
        
        # Lasketaan piirtoalue ruudulla
        screen_bar_x = x + int(start_x_orig * scale)
        screen_bar_y = y + int(bar_top_orig * scale)
        screen_bar_h = int(bar_h_orig * scale)
        screen_bar_w_full = int(bar_w_orig * scale)
        
        screen_fill_w = int(screen_bar_w_full * pct)
        
        # Aaltoilu
        time_ms = pygame.time.get_ticks()
        wave_amp = 3 * scale
        wave_freq = 0.1
        
        for i in range(screen_bar_h):
            wave_val = math.sin(i * wave_freq + time_ms * 0.01) * wave_amp
            current_w = int(screen_fill_w + wave_val)
            current_w = max(0, min(screen_bar_w_full, current_w))
            
            if current_w > 0:
                src_y = int(bar_top_orig * scale) + i
                if src_y < scaled_img.get_height():
                    src_rect = pygame.Rect(int(start_x_orig * scale), src_y, current_w, 1)
                    screen.blit(scaled_img, (screen_bar_x, screen_bar_y + i), src_rect)

    def _draw_ability_bar(self, screen, x, y):
        """Piirtää loitsut (1-6) ja itemit (7-8) riviin."""
        draw_text("ABILITIES", font_main, GOLD_COLOR, screen, x, y)
        
        slot_s = 50
        gap = 5
        start_y = y + 30
        
        # Spells 1-6 (3x2 Grid)
        for i in range(6):
            row = i // 3
            col = i % 3
            
            bx = x + col * (slot_s + gap)
            by = start_y + row * (slot_s + gap)
            
            slot_name = f"spell{i}"
            if i == 0: slot_name = "spell1" # Korjaus loopin indeksointiin
            else: slot_name = f"spell{i+1}"
            
            item = self.equipment.get(slot_name)
            
            self._draw_interactive_slot(screen, bx, by, slot_s, item, "equip", slot_name, use_slot_img=True)
            draw_text(str(i+1), font_small, (200, 200, 200), screen, bx + 4, by + 2)

        # Usables 7-8 (Below spells)
        usable_y = start_y + 2 * (slot_s + gap) + 10
        draw_text("ITEMS", font_small, GOLD_COLOR, screen, x, usable_y - 15)
        
        for i in range(2):
            slot_name = "usable" if i == 0 else "usable2"
            label = "7" if i == 0 else "8"
            bx = x + i * (slot_s + gap)
            by = usable_y
            item = self.equipment.get(slot_name)
            
            self._draw_interactive_slot(screen, bx, by, slot_s, item, "equip", slot_name, use_slot_img=True)
            draw_text(label, font_small, (200, 200, 200), screen, bx + 4, by + 2)

    def _draw_money_panel(self, screen, x, y, w, manager):
        if not self.ui_money_img:
            # Fallback jos kuvaa ei löydy
            draw_text(f"Funds: {manager.gold}", font_main, GOLD_COLOR, screen, x, y)
            return

        img = self.ui_money_img
        orig_w = 1100
        orig_h = 555
        
        scale = w / orig_w
        h = int(orig_h * scale)
        
        scaled_img = pygame.transform.smoothscale(img, (w, h))
        screen.blit(scaled_img, (x, y))
        
        # Currency values
        amount = manager.gold
        hc = amount // 1000000000
        rem = amount % 1000000000
        pl = rem // 1000000
        rem = rem % 1000000
        gp = rem // 1000
        sp = rem % 1000
        
        # Centers from original image (SP, GP, PL, HC)
        centers = [(172, sp), (423, gp), (675, pl), (927, hc)]
        
        # Y coordinate for text (User specified: 433 top, 485 bottom -> center 459)
        text_y_orig = 459
        text_y = y + int(text_y_orig * scale)
        
        for cx_orig, val in centers:
            cx = x + int(cx_orig * scale)
            surf = font_main.render(str(val), True, WHITE)
            rect = surf.get_rect(center=(cx, text_y))
            screen.blit(surf, rect)

    def _draw_backpack_grid(self, screen, x, y, w, h, manager, filter_type="gear"): 
        """Piirretään reppu oikealle puolelle."""
        
        # Grid config
        title = "BACKPACK"
        items = []
        is_material = False
        
        if filter_type == "gear":
            title = "EQUIPMENT STASH"
            items = [it for it in manager.equipment_bag if it.type in ["weapon", "armor", "shield", "helmet", "tool", "melee", "ranged"]]
        elif filter_type == "spell":
            title = "SPELLBOOK & POTIONS"
            items = [it for it in manager.equipment_bag if it.type in ["spell", "usable", "potion", "scroll", "book"]]
        elif filter_type == "material":
            title = "CRAFTING MATERIALS"
            is_material = True
            # Convert dict to list of wrappers
            for name, count in manager.inventory.items():
                if count > 0:
                    items.append(MaterialWrapper(name, count))
            
        start_y = y # Otsikko poistettu
        slot_s = 60
        gap = 4
        cols = 9
        rows = 11
        slots_per_page = cols * rows
        
        # Pagination Logic
        total_pages = max(1, (len(items) - 1) // slots_per_page + 1)
        if self.inventory_page >= total_pages: self.inventory_page = 0
        
        start_idx = self.inventory_page * slots_per_page
        end_idx = start_idx + slots_per_page
        page_items = items[start_idx:end_idx]
        
        # Draw Grid Background (grid_9_11.png)
        grid_draw_x = x
        grid_draw_y = start_y
        
        if self.ui_inv_grid_bg:
            screen.blit(self.ui_inv_grid_bg, (grid_draw_x, grid_draw_y))
            # Adjust start positions based on image (25 left, 22 top)
            grid_start_x = grid_draw_x + 25
            grid_start_y = grid_draw_y + 22
        else:
            # Fallback positioning
            grid_start_x = grid_draw_x
            grid_start_y = grid_draw_y
        
        # Draw Items
        for i in range(slots_per_page):
            row = i // cols
            col = i % cols
            
            bx = grid_start_x + col * (slot_s + gap)
            by = grid_start_y + row * (slot_s + gap)
            
            rect = pygame.Rect(bx, by, slot_s, slot_s)
            
            item = None
            if i < len(page_items):
                item = page_items[i]
            
            # Piirrä slotti ja rekisteröi
            # Huom: Bag slot ID on indeksi equipment_bag -listassa (jos ei materiaali)
            slot_id = -1
            if not is_material and item:
                try:
                    slot_id = manager.equipment_bag.index(item)
                except ValueError: pass
            
            self._draw_interactive_slot(screen, bx, by, slot_s, item, "bag", slot_id, transparent_bg=True)
            
            # Equip action (only for gear/spells)
            if not is_material and item:
                self.inventory_buttons.append((rect, ("equip", item)))

        # Pagination Controls (Below Grid)
        ctrl_y = grid_draw_y + 725 # Grid height ~722
        
        # Prev
        if self.inventory_page > 0:
            prev_rect = pygame.Rect(grid_draw_x + 20, ctrl_y, 100, 30)
            pygame.draw.rect(screen, (60, 60, 70), prev_rect, border_radius=5)
            draw_text("< PREV", font_small, WHITE, screen, prev_rect.x + 20, prev_rect.y + 5)
            self.inventory_buttons.append((prev_rect, ("page", -1)))
            
        # Next
        if self.inventory_page < total_pages - 1:
            next_rect = pygame.Rect(grid_draw_x + 480, ctrl_y, 100, 30)
            pygame.draw.rect(screen, (60, 60, 70), next_rect, border_radius=5)
            draw_text("NEXT >", font_small, WHITE, screen, next_rect.x + 20, next_rect.y + 5)
            self.inventory_buttons.append((next_rect, ("page", 1)))
            
        # Page Info
        draw_text(f"Page {self.inventory_page + 1}/{total_pages}", font_small, GRAY, screen, grid_draw_x + 260, ctrl_y + 5)

    def _draw_interactive_slot(self, screen, x, y, size, item, loc_type, slot_id, transparent_bg=False, h=None, use_slot_img=False):
        """Piirtää slotin ja lisää sen ui_slots-listaan törmäystarkistusta varten."""
        height = h if h is not None else size
        rect = pygame.Rect(x, y, size, height)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)
        
        # Jos tätä itemiä raahataan, piirrä haamu tai tyhjä
        draw_item = item
        if self.dragging_item and self.dragging_from_slot and \
           self.dragging_from_slot['type'] == loc_type and \
           self.dragging_from_slot['id'] == slot_id:
            draw_item = None # Piilota alkuperäinen raahauksen aikana
            
        if use_slot_img and self.ui_slot_img:
            # Piirrä slot.png taustaksi
            scaled_slot = pygame.transform.smoothscale(self.ui_slot_img, (size, height))
            screen.blit(scaled_slot, (x, y))
            if is_hover:
                pygame.draw.rect(screen, (255, 255, 255), rect, 1, border_radius=5)
        elif transparent_bg:
            # Piirretään vain hover-efekti (ei taustaa), koska grid-kuva on alla
            if is_hover:
                s = pygame.Surface((size, size), pygame.SRCALPHA)
                s.fill((255, 255, 255, 30))
                screen.blit(s, (x, y))
            
            # Piirrä rarity-reuna jos item on olemassa
            if draw_item:
                rarity = getattr(draw_item, "rarity", "Common")
                if rarity != "Common":
                    border_col = (150, 150, 150)
                    if rarity == "Rare": border_col = (60, 100, 255)
                    elif rarity == "Epic": border_col = (200, 50, 200)
                    elif rarity == "Legendary": border_col = (255, 180, 0)
                    pygame.draw.rect(screen, border_col, rect, 2, border_radius=5)
        else:
            draw_item_slot_background(screen, x, y, size, draw_item, is_hover)
        
        if draw_item:
            # Keskitetään ikoni slottiin (jos slotti ei ole neliö)
            icon_size = min(size, height)
            icon_y = y + (height - icon_size) // 2
            draw_item.draw_card_icon(screen, x, icon_y, icon_size)
            
        # UUSI: Tallenna tooltip piirrettäväksi myöhemmin (päällimmäiseksi)
        if is_hover and item and not self.dragging_item:
            self.hovered_tooltip_item = item
            
        # Rekisteröi UI-tapahtumia varten
        self.ui_slots.append({'rect': rect, 'type': loc_type, 'id': slot_id, 'item': item})

    def handle_inventory_event(self, event, manager):
        """Käsittelee klikkaukset ja raahauksen."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 1. Start Drag
            for slot in self.ui_slots:
                if slot['rect'].collidepoint(event.pos):
                    item = slot['item']
                    if item and getattr(item, "type", "") != "material": # Materiaaleja ei voi raahata (vielä)
                        self.dragging_item = item
                        self.dragging_from_slot = {'type': slot['type'], 'id': slot['id']}
                        sound_system.play_sound('click')
                    return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # 2. End Drag (Drop)
            if self.dragging_item:
                dropped = False
                for slot in self.ui_slots:
                    if slot['rect'].collidepoint(event.pos):
                        self._perform_drag_drop(self.dragging_from_slot, slot, manager)
                        dropped = True
                        break
                
                # Jos pudotettiin tyhjään (ei slottiin), palautuu automaattisesti
                self.dragging_item = None
                self.dragging_from_slot = None
                if dropped: sound_system.play_sound('recruit')
                
        # Tabit toimivat edelleen klikkauksella
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, data in self.inventory_buttons:
                if rect.collidepoint(event.pos):
                    if data[0] == "tab":
                        self.inventory_tab = data[1]
                        self.inventory_page = 0 # Reset page on tab switch
                        sound_system.play_sound('click')
                    elif data[0] == "page":
                        self.inventory_page += data[1]
                        sound_system.play_sound('click')

    def _perform_drag_drop(self, source, target, manager):
        """Siirtää tavaran paikasta A paikkaan B."""
        # Jos kohde on sama kuin lähde, ei tehdä mitään
        if source['type'] == target['type'] and source['id'] == target['id']:
            return

        item = self.dragging_item
        
        # 1. Bag -> Equip
        if source['type'] == 'bag' and target['type'] == 'equip':
            # Yritä varustaa
            slot_name = target['id']
            
            # Tarkista säännöt
            ok, reason = self.can_equip_item_to_slot(slot_name, item)
            if ok:
                if item in manager.equipment_bag:
                    manager.equipment_bag.remove(item)
                old_item = self.equip_item_to_slot(slot_name, item)
                if old_item:
                    manager.equipment_bag.append(old_item)
            else:
                print(f"Cannot equip: {reason}")
                sound_system.play_sound('error')

        # 2. Equip -> Bag
        elif source['type'] == 'equip' and target['type'] == 'bag':
            # Unequip
            slot_name = source['id']
            unequipped = self.unequip_slot(slot_name)
            if unequipped:
                manager.equipment_bag.append(unequipped)

        # 3. Equip -> Equip (Swap slots)
        elif source['type'] == 'equip' and target['type'] == 'equip':
            src_slot = source['id']
            tgt_slot = target['id']
            
            # Tarkista voiko itemin laittaa uuteen slottiin
            ok, reason = self.can_equip_item_to_slot(tgt_slot, item)
            if ok:
                # Ota item pois lähteestä
                self.equipment[src_slot] = None
                
                # Ota item pois kohteesta (jos on)
                target_item = self.equipment.get(tgt_slot)
                
                # Laita item kohteeseen
                self.equipment[tgt_slot] = item
                
                # Laita target_item lähteeseen (jos sopii)
                if target_item:
                    ok_back, _ = self.can_equip_item_to_slot(src_slot, target_item)
                    if ok_back:
                        self.equipment[src_slot] = target_item
                    else:
                        # Ei sovi takaisin -> laita reppuun
                        manager.equipment_bag.append(target_item)
                
                self.calculate_final_stats()
            else:
                sound_system.play_sound('error')
            
            # Label (Alapuolella)
            # draw_text(labels[i], font_small, (150, 150, 150), screen, bx, y + slot_s + 2)
