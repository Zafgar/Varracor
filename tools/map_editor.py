import pygame
import json
import os
import random
from settings import *
from ui_kit import draw_text, font_small, font_main, GOLD_COLOR, WHITE, GRAY, GREEN, RED

# --- ASSET REGISTRY ---
from assets.tiles.house_objects import *
from assets.tiles.tavern_objects import *
from assets.tiles.muckford_objects import *
from assets.tiles.farm_objects import *
from assets.tiles.forest_objects import *
from assets.tiles.crypt_objects import *
from assets.tiles.crypt_walls import *
from assets.tiles.blacksmith_objects import *
from assets.tiles.prop import Prop
from assets.tiles.bog_objects import *
from units.villager import Villager
from units.bard import Bard
from units.marda_shant import MardaShant
from units.rat import GiantRat
from crafting.swamp.scrap_pile import ScrapPile
from items.item_registry import create_item
from loot_data import BLUEPRINTS
from gladiator import Gladiator
from units.human import Human
from units.orc import Orc
from units.elf import Elf
from units.goblin import Goblin
from units.rat_rider import RatRider
from units.rat_king import RatKing
from units.undead_skeleton import UndeadSkeleton
from units.undead_zombie import UndeadZombie
from units.undead_skeleton_archer import UndeadSkeletonArcher
from units.corrupted_crow import CorruptedCrow
from units.bog_leech import BogLeech
from units.giant_frog import GiantFrog
from units.mnemonic_devourer import MnemonicDevourer
from assets.tiles.water import (
    FishingJetty, WaterBody, carve_water, rebuild_water_blockers,
)
from assets.tiles.editor_floors import StoneFloor, WoodFloor, GrassFloor
from assets.tiles.effect_emitters import (
    SmokeEmitter, FogPatch, EmberEmitter, FireflySwarm,
)
from systems import map_document

class MapEditor:
    def __init__(self, manager):
        self.manager = manager
        self.active = False
        self.show_menu = False
        
        self.selected_prop_class = None
        self.dragged_prop = None
        self.drag_offset = (0, 0)
        self.drag_start_pos = None # Undo varten
        self.fill_start = None # Box fill varten
        
        self.history = [] # Undo stack
        
        # Editor Settings
        self.show_grid = False
        self.snap_to_grid = False
        self.show_hitboxes = False # H-key toggle
        self.grid_size = 40
        self.variant_index = 1
        
        # Asset Categories
        self.categories = {
            "Ground": [StoneFloor, WoodFloor, GrassFloor],
            "Walls": [HouseWall, BlacksmithWall, CryptBackWall, CryptSideWall],
            "Doors": [HouseDoor],
            "Furniture": [InnTable, InnTable2, InnBed, InnDoubleBed, InnCounter, InnFireplace, 
                          WorkTable, CabinetHorizontal, WardrobeCloth, BookshelfHorizontal, 
                          GamblersTable, SmallRoomTable, CookingTable, BathTub, Anvil, Forge, 
                          WeaponRack, EquipmentTable],
            "Decor": [BearRug, Vase, InnDrinksTable, BarDrinksTable, FoodBucket, GroundFoodPile, 
                      BarrelGroup, MagicCrystal, StagePlatform, InnDrink, InnFood],
            "City": [TavernBuilding, TownHall, ScrapIronBuilding, ShantyHouse, Well, StreetLamp, 
                     SewerGrate, ScrapBarrel, MuckfordStage, MuckfordStall],
            "Nature": [MuckfordTree, AppleTree, ForestBush, ForestRockBig, ForestGrass,
                       GrassPatch, BogTree, BogReed, MudPool],
            # Vesi: WaterBody maalataan SHIFT+raahauksella (mikä tahansa koko
            # -> lammet/joet/meret), FishingJetty klikillä rannalle. Esteet
            # lasketaan automaattisesti laituriaukkoineen.
            "Water": [WaterBody, FishingJetty],
            # Tunnelmaefektit: savu/sumu/kipinät/tulikärpäset - eivät
            # esteitä, variant ([ ja ]) säätää voimakkuutta/sädettä
            "Effects": [SmokeEmitter, FogPatch, EmberEmitter, FireflySwarm],
            "Farm": [Barn, ChickenCoop, FarmStorage, FarmFenceHorizontal, FarmFenceVertical, 
                     MuckfordField, ManurePile],
            "Crypt": [CryptPillar, CryptBigPillar, CryptRock, BrokenPillar, CryptCoffin, CryptTree, CryptGrass],
            "Items": [Apple, Egg, Manure, ScrapPile, ScrapPileBig],
            "Units": [
                Villager, MardaShant, Bard, 
                Human, Orc, Elf, Goblin, 
                GiantRat, RatRider, RatKing,
                UndeadSkeleton, UndeadZombie, UndeadSkeletonArcher,
                CorruptedCrow, BogLeech, GiantFrog,
                MnemonicDevourer
            ],
            # System-rivit rakennetaan _system_items():ssä (mm. custom-
            # karttojen Load-rivit maps/custom_maps.py-rekisteristä)
            "System": []
        }
        
        self.current_category = "Furniture"
        self.scroll_y = 0
        self.menu_rect = pygame.Rect(SCREEN_WIDTH - 300, 0, 300, SCREEN_HEIGHT)
        
        # Ghost cache
        self.ghost_instance = None
        self.ghost_class = None
        self.ghost_variant = 1
        self.ghost_team_idx = -1
        self.ghost_angle = 0
        self.ghost_facing_right = True
        
        # Shadow Settings
        self.shadow_active = True
        self.shadow_shape = "ellipse" # ellipse, rect, circle
        
        # Tekstinsyöttö (note / kartan nimi / kartan koko / yksikön nimi)
        self.typing_mode = None     # None | "note" | "map_name" | "map_size" | "unit_name"
        self.note_text_buffer = ""
        self.note_target_prop = None

        # Team Colors
        self.team_colors = [
            ("Red (Enemy)", RED),
            ("Green (Player)", GREEN),
            ("Blue (Ally)", BLUE),
            ("Neutral", (150, 150, 150))
        ]
        self.team_color_idx = 0
        
        self.show_help = True
        
        # --- ITEM LISTS FOR EDITOR ---
        self.item_lists = {
            "main_hand": ["Iron Sword", "Iron Axe", "Iron Mace", "Iron Spear", "Iron Dagger", "Wooden Bow", "Wooden Staff", "Scrap Sword", "Scrap Axe", "Scrap Spear"],
            "off_hand": ["Wooden Shield", "Iron Shield", "Scrap Shield", "Iron Dagger", "Scrap Dagger"],
            "body": ["Leather Armor", "Chainmail", "Plate Armor", "Robes", "Rags"],
            "head": ["Leather Cap", "Iron Helmet", "Hood"]
        }
        # Add blueprints to lists
        for name, data in BLUEPRINTS.items():
            t = data.get("type", "")
            if t == "weapon": self.item_lists["main_hand"].append(name)
            elif t == "shield": self.item_lists["off_hand"].append(name)
            elif t == "armor": self.item_lists["body"].append(name)
            elif t == "helmet": self.item_lists["head"].append(name)
            
        # Remove duplicates
        for k in self.item_lists:
            unique = list(set(self.item_lists[k]))
            if "None" in unique: unique.remove("None")
            self.item_lists[k] = ["None"] + sorted(unique)

    def toggle(self):
        self.active = not self.active
        if self.active:
            print("Map Editor ENABLED. Press ALT for menu.")
        else:
            self.selected_prop_class = None
            self.dragged_prop = None

    def handle_event(self, event):
        if not self.active: return False
        
        # Camera offset from manager
        cam_x = getattr(self.manager, "camera_x", 0)
        cam_y = getattr(self.manager, "camera_y", 0)
        offset = (cam_x, cam_y)

        # --- TEXT INPUT MODE ---
        if self.typing_mode:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._commit_text_input()
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self.typing_mode = None
                    self.note_target_prop = None
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.note_text_buffer = self.note_text_buffer[:-1]
                    return True
                else:
                    if len(event.unicode) > 0 and event.unicode.isprintable():
                        self.note_text_buffer += event.unicode
                    return True
            return True # Block other events

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LALT or event.key == pygame.K_RALT:
                self.show_menu = not self.show_menu
                return True
            
            if event.key == pygame.K_F5:
                self.save_project()
                return True
                
            if event.key == pygame.K_F6:
                self.load_project()
                return True
            
            if event.key == pygame.K_ESCAPE:
                # Toggle Editor OFF (Test Mode)
                self.toggle()
                return True
            
            if event.key == pygame.K_F9:
                self.export_map()
                return True

            # F7 = nimeä kartta, Shift+F7 = muuta areenan kokoa
            if event.key == pygame.K_F7:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self._start_text_input("map_size")
                else:
                    self._start_text_input("map_name")
                return True

            # U = nimeä osoitettu yksikkö (NPC/monsteri)
            if event.key == pygame.K_u:
                self.start_unit_rename(offset)
                return True

            if event.key == pygame.K_DELETE:
                self.delete_hovered(offset)
                return True
            
            # Undo (Ctrl+Z)
            if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.undo_last_action()
                return True

            # Duplicate (Ctrl+D)
            if event.key == pygame.K_d and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.duplicate_hovered(offset)
                return True
                
            # Note (N)
            if event.key == pygame.K_n:
                self.start_note_input(offset)
                return True
            
            # Inventory Edit (Shift + 1-4)
            if (pygame.key.get_mods() & pygame.KMOD_SHIFT) and event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                self.handle_inventory_edit(event.key, offset)
                return True
            
            # --- HITBOX EDITING ---
            # Shift + Arrows = Resize Hitbox
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                if event.key == pygame.K_UP:    self.adjust_hitbox(offset, 0, -2, 0, 0); return True
                if event.key == pygame.K_DOWN:  self.adjust_hitbox(offset, 0, 2, 0, 0); return True
                if event.key == pygame.K_LEFT:  self.adjust_hitbox(offset, -2, 0, 0, 0); return True
                if event.key == pygame.K_RIGHT: self.adjust_hitbox(offset, 2, 0, 0, 0); return True

            # Alt + Arrows = Move Hitbox Offset
            if pygame.key.get_mods() & pygame.KMOD_ALT:
                if event.key == pygame.K_UP:    self.adjust_hitbox(offset, 0, 0, 0, -2); return True
                if event.key == pygame.K_DOWN:  self.adjust_hitbox(offset, 0, 0, 0, 2); return True
                if event.key == pygame.K_LEFT:  self.adjust_hitbox(offset, 0, 0, -2, 0); return True
                if event.key == pygame.K_RIGHT: self.adjust_hitbox(offset, 0, 0, 2, 0); return True

            # Enter = Apply Hitbox to All of Type
            if event.key == pygame.K_RETURN:
                self.apply_hitbox_to_all(offset)
                return True

            # Flip Facing (F)
            if event.key == pygame.K_f:
                self.flip_selection(offset)
                return True

            # Z-Order (PageUp/Down)
            if event.key == pygame.K_PAGEUP:
                self.change_z_order(offset, 1)
                return True
            if event.key == pygame.K_PAGEDOWN:
                self.change_z_order(offset, -1)
                return True

            # Team Color (C)
            if event.key == pygame.K_c:
                self.team_color_idx = (self.team_color_idx + 1) % len(self.team_colors)
                self.ghost_class = None # Force regen
                return True
            
            # Rotate (R)
            if event.key == pygame.K_r:
                self.rotate_selection()
                return True

            # Nudge (Arrows)
            nudge_x, nudge_y = 0, 0
            step = self.grid_size if self.snap_to_grid else 1
            if event.key == pygame.K_LEFT: nudge_x = -step
            if event.key == pygame.K_RIGHT: nudge_x = step
            if event.key == pygame.K_UP: nudge_y = -step
            if event.key == pygame.K_DOWN: nudge_y = step
            
            if nudge_x != 0 or nudge_y != 0:
                # Jos raahataan, liikuta raahattavaa
                if self.dragged_prop:
                    self.dragged_prop.rect.x += nudge_x
                    self.dragged_prop.rect.y += nudge_y
                    self.dragged_prop.image_pos = self.dragged_prop.rect.topleft
                # Muuten panoroi kameraa reippaasti (isot kartat)
                else:
                    pan = self.grid_size * 3
                    self.manager.camera_x += (nudge_x > 0) * pan - (nudge_x < 0) * pan
                    self.manager.camera_y += (nudge_y > 0) * pan - (nudge_y < 0) * pan
                return True

            # --- NEW CONTROLS ---
            if event.key == pygame.K_g:
                self.show_grid = not self.show_grid
                return True
                
            if event.key == pygame.K_x: # X for Snap (S is for movement)
                self.snap_to_grid = not self.snap_to_grid
                return True
            
            if event.key == pygame.K_h: # H for Hitboxes
                self.show_hitboxes = not self.show_hitboxes
                return True
                
            if event.key == pygame.K_LEFTBRACKET: # [ Variant -
                self.variant_index = max(1, self.variant_index - 1)
                self.ghost_class = None # Force regen
                self.ghost_angle = 0
                return True
                
            if event.key == pygame.K_RIGHTBRACKET: # ] Variant +
                self.variant_index += 1
                self.ghost_class = None # Force regen
                self.ghost_angle = 0
                return True
                
            if event.key == pygame.K_j: # J for Shadow
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # Cycle shape
                    shapes = ["ellipse", "rect", "circle"]
                    try:
                        idx = shapes.index(self.shadow_shape)
                        self.shadow_shape = shapes[(idx + 1) % len(shapes)]
                    except Exception: self.shadow_shape = "ellipse"
                else:
                    self.shadow_active = not self.shadow_active
                
                self.apply_shadow_to_hovered(offset)
                return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                mx, my = pygame.mouse.get_pos()
                
                # Menu interaction
                if self.show_menu and self.menu_rect.collidepoint(mx, my):
                    self.handle_menu_click(mx, my)
                    return True # Consume event
                
                # World interaction
                wx = mx + offset[0]
                wy = my + offset[1]
                
                # Apply Snap
                keys = pygame.key.get_pressed()
                if self.snap_to_grid or keys[pygame.K_LSHIFT]:
                    wx = round(wx / self.grid_size) * self.grid_size
                    wy = round(wy / self.grid_size) * self.grid_size
                
                if self.selected_prop_class:
                    # Shift + Click = Start Box Fill
                    if keys[pygame.K_LSHIFT]:
                        self.fill_start = (wx, wy)
                    else:
                        self.place_prop(wx, wy)
                else:
                    self.start_drag(wx, wy, offset)
                return True # Consume event
                
            elif event.button == 3: # Right Click
                # Cancel selection / Stop drag
                self.selected_prop_class = None
                self.ghost_instance = None
                self.dragged_prop = None
                self.fill_start = None
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.fill_start:
                    # Execute Box Fill
                    mx, my = pygame.mouse.get_pos()
                    wx = mx + offset[0]
                    wy = my + offset[1]
                    self.execute_fill(self.fill_start, (wx, wy))
                    self.fill_start = None
                    return True
                
                if self.dragged_prop:
                    self.stop_drag()
                    return True
        
        elif event.type == pygame.MOUSEWHEEL:
            if self.show_menu and self.menu_rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_y -= event.y * 30
                self.scroll_y = max(0, self.scroll_y)
                return True

        return False

    def save_project(self, filename="test_map_project.json"):
        """Tallentaa koko areenan (meta + sisältö) projektiksi.
        Serialisointi on jaettu systems/map_document.py:n kanssa."""
        if not self.manager.current_arena:
            return
        doc = map_document.serialize_map(self.manager.current_arena)
        try:
            with open(filename, "w") as f:
                json.dump(doc, f, indent=2)
            print(f"Project saved to {filename} ({doc['name']})")
            if hasattr(self.manager, "vfx"):
                self.manager.vfx.show_damage(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, "PROJECT SAVED", color=GREEN)
        except Exception as e:
            print(f"Error saving project: {e}")

    def load_project(self, filename="test_map_project.json"):
        if not os.path.exists(filename):
            print(f"Project file {filename} not found.")
            return
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading project: {e}")
            return
        if not self.manager.current_arena:
            return
        if data.get("format") == map_document.FORMAT_KEY:
            map_document.apply_to_arena(data, self.manager.current_arena,
                                        self.manager)
        else:
            # Legacy-projekti (pelkät props/floor_props ilman metaa)
            self.manager.current_arena.props.clear()
            self.manager.current_arena.obstacles.clear()
            if hasattr(self.manager.current_arena, "floor_props"):
                self.manager.current_arena.floor_props.clear()
            self._reconstruct_list(data.get("props", []), is_floor=False)
            self._reconstruct_list(data.get("floor_props", []), is_floor=True)
            rebuild_water_blockers(self.manager.current_arena)
        print(f"Project loaded from {filename}")
        if hasattr(self.manager, "vfx"):
            self.manager.vfx.show_damage(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, "PROJECT LOADED", color=GREEN)

    # ------------------------------------------------ tekstinsyöttö
    def _start_text_input(self, mode, target=None):
        self.typing_mode = mode
        self.note_target_prop = target
        arena = self.manager.current_arena
        if mode == "map_name":
            self.note_text_buffer = str(getattr(arena, "map_name", "") or "")
        elif mode == "map_size":
            self.note_text_buffer = (f"{getattr(arena, 'width', 0)}x"
                                     f"{getattr(arena, 'height', 0)}")
        elif mode == "unit_name":
            self.note_text_buffer = str(getattr(target, "name", ""))
        else:
            self.note_text_buffer = str(getattr(target, "_editor_note", ""))

    def _commit_text_input(self):
        mode = self.typing_mode
        text = self.note_text_buffer.strip()
        arena = self.manager.current_arena
        if mode == "note" and self.note_target_prop:
            self.note_target_prop._editor_note = text
            self.note_target_prop._editor_created = True
            print(f"Note set: {text}")
        elif mode == "map_name" and arena is not None and text:
            arena.map_name = text
            print(f"Map renamed: {text}")
        elif mode == "map_size" and arena is not None:
            try:
                w, h = (int(v) for v in text.lower().replace(" ", "").split("x"))
                map_document.resize_arena(arena, max(1920, w), max(1080, h))
                print(f"Arena resized: {arena.width}x{arena.height}")
            except Exception:
                print(f"Bad size (use WIDTHxHEIGHT): {text!r}")
        elif mode == "unit_name" and self.note_target_prop and text:
            self.note_target_prop.name = text
            self.note_target_prop._editor_created = True
            print(f"Unit renamed: {text}")
        self.typing_mode = None
        self.note_target_prop = None

    def start_unit_rename(self, offset):
        mx, my = pygame.mouse.get_pos()
        found = self._find_hovered(mx + offset[0], my + offset[1])
        if found and hasattr(found, "name") and hasattr(found, "team_color"):
            self._start_text_input("unit_name", found)

    def _get_class_by_name(self, name):
        for cat_list in self.categories.values():
            for item in cat_list:
                if isinstance(item, type) and item.__name__ == name:
                    return item
        return None

    def _reconstruct_list(self, obj_list, is_floor=False):
        for obj_data in obj_list:
            cls_name = obj_data["class"]
            cls = self._get_class_by_name(cls_name)
            if not cls: continue
            
            x = obj_data["x"]
            y = obj_data["y"]
            variant = obj_data.get("variant", 1)
            col = obj_data.get("team_color", None)
            if col: col = tuple(col)
            
            try:
                # Yritetään luoda objekti (erikoiskäsittely yksiköille)
                try:
                    if cls is WaterBody:
                        obj = WaterBody(x, y, obj_data.get("w", 400),
                                        obj_data.get("h", 300),
                                        seed=obj_data.get("seed", 7),
                                        name=obj_data.get("name", "water"),
                                        style=obj_data.get("style", "auto"))
                    elif cls is FishingJetty:
                        obj = FishingJetty(x, y, obj_data.get("w", 170),
                                           obj_data.get("h", 64),
                                           seed=obj_data.get("seed", 3))
                    elif cls == Villager: obj = Villager("Villager", "Human", x, y, col or GREEN)
                    elif cls == Bard: obj = Bard("Bard", "Elf", x, y, col or GREEN)
                    elif cls == MardaShant: obj = MardaShant(x, y)
                    elif cls == GiantRat: obj = GiantRat("Rat", x, y, team_color=col or RED)
                    elif cls == Human: obj = Human("Bandit", x, y, col or RED, "Common")
                    elif cls == Orc: obj = Orc("Orc", x, y, col or RED)
                    elif cls == Elf: obj = Elf("Elf", x, y, col or RED)
                    elif cls == Goblin: obj = Goblin("Goblin", x, y, col or RED)
                    elif cls == RatRider: obj = RatRider("Rat Rider", x, y, col or RED)
                    elif cls == RatKing: obj = RatKing("Rat King", x, y)
                    elif cls == UndeadSkeleton: obj = UndeadSkeleton("Skeleton", x, y, col or RED)
                    elif cls == UndeadZombie: obj = UndeadZombie("Zombie", x, y, col or RED)
                    elif cls == UndeadSkeletonArcher: obj = UndeadSkeletonArcher("Archer", x, y, col or RED)
                    elif cls == CorruptedCrow: obj = CorruptedCrow("Crow", x, y, col or RED)
                    elif cls == BogLeech: obj = BogLeech("Leech", x, y, col or RED)
                    elif cls == GiantFrog: obj = GiantFrog("Frog", x, y, col or RED)
                    elif cls == MnemonicDevourer: obj = MnemonicDevourer(); obj.rect.topleft = (x, y)
                    else: obj = cls(x, y, variant=variant)
                except Exception:
                    obj = cls(x, y)

                if "angle" in obj_data and hasattr(obj, "rotate"):
                    obj.rotate(obj_data["angle"])
                
                if "facing_right" in obj_data and hasattr(obj, "facing_right"):
                    obj.facing_right = obj_data["facing_right"]
                
                if "note" in obj_data:
                    obj._editor_note = obj_data["note"]
                    obj._editor_created = True
                
                if "equipment" in obj_data and hasattr(obj, "equip_item"):
                    for slot, item_name in obj_data["equipment"].items():
                        item = create_item(item_name)
                        if item: obj.equip_item(item)

                if is_floor:
                    self.manager.current_arena.floor_props.append(obj)
                else:
                    self.manager.current_arena.props.append(obj)
                    if obj.rect.w > 0 and obj.rect.h > 0 \
                            and not isinstance(obj, Gladiator) \
                            and not getattr(obj, "is_floor", False) \
                            and not getattr(obj, "is_effect", False):
                        self.manager.current_arena.obstacles.append(obj)
                        
            except Exception as e:
                print(f"Failed to reconstruct {cls_name}: {e}")

    def execute_fill(self, start, end):
        """Täyttää alueen valitulla objektilla."""
        x1, y1 = start
        x2, y2 = end

        # Järjestä koordinaatit (min -> max)
        sx = min(x1, x2)
        sy = min(y1, y2)
        ex = max(x1, x2)
        ey = max(y1, y2)

        # Snap to grid
        gs = self.grid_size
        sx = round(sx / gs) * gs
        sy = round(sy / gs) * gs
        ex = round(ex / gs) * gs
        ey = round(ey / gs) * gs

        # Vesi: raahaus = YKSI yhtenäinen allas/joki, ei ruudukkotäyttö
        if self.selected_prop_class is WaterBody:
            w = max(self.grid_size * 2, int(ex - sx))
            h = max(self.grid_size * 2, int(ey - sy))
            arena = self.manager.current_arena
            if arena is not None:
                water = carve_water(arena, (int(sx), int(sy), w, h),
                                    seed=random.randint(1, 9999))
                self.history.append({"type": "place", "obj": water})
                print(f"Water carved: {water.rect}")
            return

        # Loop ja aseta
        for cy in range(int(sy), int(ey) + 1, gs):
            for cx in range(int(sx), int(ex) + 1, gs):
                self.place_prop(cx, cy)

    def update(self):
        if not self.active: return

        cam_x = getattr(self.manager, "camera_x", 0)
        cam_y = getattr(self.manager, "camera_y", 0)

        # Efektiemitterit ja vedet elävät myös editorissa (ruuduissa,
        # jotka eivät itse päivitä propeja)
        arena = self.manager.current_arena
        if arena is not None:
            for p in arena.props:
                if getattr(p, "is_effect", False):
                    p.update(None, self.manager)
            for p in getattr(arena, "floor_props", []):
                if isinstance(p, WaterBody):
                    p.update(None, self.manager)
        
        if self.dragged_prop:
            mx, my = pygame.mouse.get_pos()
            wx = mx + cam_x
            wy = my + cam_y
            
            # Move image_pos
            new_x = wx - self.drag_offset[0]
            new_y = wy - self.drag_offset[1]
            
            # Snap to grid
            keys = pygame.key.get_pressed()
            if self.snap_to_grid or keys[pygame.K_LSHIFT]:
                new_x = round(new_x / self.grid_size) * self.grid_size
                new_y = round(new_y / self.grid_size) * self.grid_size
            
            # Update prop
            if hasattr(self.dragged_prop, "image_pos"):
                # Calculate delta to move rect
                dx = new_x - self.dragged_prop.image_pos[0]
                dy = new_y - self.dragged_prop.image_pos[1]
                
                self.dragged_prop.image_pos = (new_x, new_y)
                self.dragged_prop.rect.x += dx
                self.dragged_prop.rect.y += dy

    def draw(self, screen):
        if not self.active: return
        
        cam_x = getattr(self.manager, "camera_x", 0)
        cam_y = getattr(self.manager, "camera_y", 0)
        offset = (cam_x, cam_y)
        
        # Draw Grid
        if self.show_grid:
            self._draw_grid_lines(screen, offset)
            
        # Draw Hitboxes
        if self.show_hitboxes and self.manager.current_arena:
            for obs in self.manager.current_arena.obstacles:
                r = getattr(obs, "rect", obs)
                pygame.draw.rect(screen, (255, 255, 0), (r.x - offset[0], r.y - offset[1], r.w, r.h), 1)
            
            # Draw props that are not obstacles too (blue)
            for p in self.manager.current_arena.props:
                r = p.rect
                col = (0, 100, 255)
                if p not in self.manager.current_arena.obstacles:
                    col = (100, 200, 255) # Lighter blue for non-obstacles
                
                pygame.draw.rect(screen, col, (r.x - offset[0], r.y - offset[1], r.w, r.h), 1)
                
                # Draw Hurtbox (Red) if exists
                if hasattr(p, "hurt_rect"):
                    hr = p.hurt_rect
                    pygame.draw.rect(screen, (255, 50, 50), (hr.x - offset[0], hr.y - offset[1], hr.w, hr.h), 1)
        
        # Draw Fill Preview
        if self.fill_start:
            mx, my = pygame.mouse.get_pos()
            # Screen coords for start
            sx = self.fill_start[0] - offset[0]
            sy = self.fill_start[1] - offset[1]
            
            w = mx - sx
            h = my - sy
            
            # Piirrä vihreä laatikko
            pygame.draw.rect(screen, (0, 255, 0), (sx, sy, w, h), 2)
            # Piirrä mitat
            draw_text(f"{int(abs(w)//self.grid_size)+1}x{int(abs(h)//self.grid_size)+1}", font_small, (0, 255, 0), screen, mx + 10, my + 10)

        # Draw UI info
        snap_txt = "ON" if self.snap_to_grid else "OFF (Shift)"
        team_name = self.team_colors[self.team_color_idx][0]
        current_col = self.team_colors[self.team_color_idx][1]
        
        tool_name = "None"
        if self.selected_prop_class:
            tool_name = self.selected_prop_class if isinstance(self.selected_prop_class, str) else self.selected_prop_class.__name__
            
        # Top Bar Background
        pygame.draw.rect(screen, (0, 0, 0, 200), (0, 0, SCREEN_WIDTH, 40))
            
        shad_txt = self.shadow_shape if self.shadow_active else "OFF"
        arena = self.manager.current_arena
        map_name = getattr(arena, "map_name", "") or "Unnamed"
        map_size = (f"{getattr(arena, 'width', 0)}x"
                    f"{getattr(arena, 'height', 0)}")
        info_text = (f"EDITOR | {map_name} [{map_size}] | Tool: {tool_name} "
                     f"| Var: {self.variant_index} | Snap(X): {snap_txt} "
                     f"| Shadow(J): {shad_txt} | ALT: Menu | F9: Export")
        draw_text(info_text, font_small, GREEN, screen, 10, 10)
        
        # Team Indicator in Top Bar (Right side)
        ind_x = SCREEN_WIDTH - 250
        # Swatch
        pygame.draw.rect(screen, current_col, (ind_x, 10, 20, 20), border_radius=3)
        pygame.draw.rect(screen, WHITE, (ind_x, 10, 20, 20), 1, border_radius=3)
        draw_text(f"Team (C): {team_name}", font_small, WHITE, screen, ind_x + 30, 10)
        
        # Draw Ghost
        if self.selected_prop_class and not self.show_menu:
            mx, my = pygame.mouse.get_pos()
            wx = mx + offset[0]
            wy = my + offset[1]
            
            # Snap ghost
            keys = pygame.key.get_pressed()
            if self.snap_to_grid or keys[pygame.K_LSHIFT]:
                wx = round(wx / self.grid_size) * self.grid_size
                wy = round(wy / self.grid_size) * self.grid_size
            
            # Update/Create ghost
            if self.ghost_class != self.selected_prop_class or self.ghost_variant != self.variant_index or self.ghost_team_idx != self.team_color_idx:
                try:
                    current_color = self.team_colors[self.team_color_idx][1]
                    # Try with variant
                    try:
                        # Special handling for Units in ghost
                        if self.selected_prop_class == Villager:
                            self.ghost_instance = Villager("Ghost", "Human", wx, wy, current_color)
                        elif self.selected_prop_class == Bard:
                            self.ghost_instance = Bard("Ghost", "Elf", wx, wy, current_color)
                        elif self.selected_prop_class == GiantRat:
                            self.ghost_instance = GiantRat("Ghost", wx, wy, team_color=current_color)
                        elif self.selected_prop_class == MardaShant:
                            self.ghost_instance = MardaShant(wx, wy)
                        elif self.selected_prop_class == Human:
                            self.ghost_instance = Human("Ghost", wx, wy, current_color, "Common")
                        elif self.selected_prop_class == Orc:
                            self.ghost_instance = Orc("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == Elf:
                            self.ghost_instance = Elf("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == Goblin:
                            self.ghost_instance = Goblin("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == RatRider:
                            self.ghost_instance = RatRider("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == RatKing:
                            self.ghost_instance = RatKing("Ghost", wx, wy)
                        elif self.selected_prop_class == UndeadSkeleton:
                            self.ghost_instance = UndeadSkeleton("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == UndeadZombie:
                            self.ghost_instance = UndeadZombie("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == UndeadSkeletonArcher:
                            self.ghost_instance = UndeadSkeletonArcher("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == CorruptedCrow:
                            self.ghost_instance = CorruptedCrow("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == BogLeech:
                            self.ghost_instance = BogLeech("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == GiantFrog:
                            self.ghost_instance = GiantFrog("Ghost", wx, wy, current_color)
                        elif self.selected_prop_class == MnemonicDevourer:
                            self.ghost_instance = MnemonicDevourer()
                            self.ghost_instance.rect.topleft = (wx, wy)
                        else:
                            self.ghost_instance = self.selected_prop_class(wx, wy, variant=self.variant_index)
                    except Exception:
                        self.ghost_instance = self.selected_prop_class(wx, wy)
                        
                    self.ghost_class = self.selected_prop_class
                    self.ghost_variant = self.variant_index
                    self.ghost_team_idx = self.team_color_idx
                    self.ghost_facing_right = True # Reset flip on new class
                    
                    # Apply rotation if needed
                    if self.ghost_angle != 0 and hasattr(self.ghost_instance, "rotate"):
                        self.ghost_instance.rotate(self.ghost_angle)
                    
                    if self.ghost_instance.image:
                        self.ghost_instance.image.set_alpha(150)
                        
                    # Apply Flip
                    if hasattr(self.ghost_instance, "facing_right"):
                        self.ghost_instance.facing_right = self.ghost_facing_right
                        
                except Exception: pass
            
            if self.ghost_instance:
                # Update pos
                self.ghost_instance.image_pos = (wx, wy)
                # Draw
                # Draw Team Indicator for Ghost
                if hasattr(self.ghost_instance, "team_color"):
                    cx, cy = self.ghost_instance.rect.centerx - offset[0], self.ghost_instance.rect.bottom - offset[1]
                    col = self.ghost_instance.team_color
                    pygame.draw.ellipse(screen, col, (cx - 15, cy - 6, 30, 12), 2)
                
                self.ghost_instance.draw_on_screen(screen, offset)
                
        # Draw Notes on objects
        if self.manager.current_arena:
            for p in self.manager.current_arena.props:
                note = getattr(p, "_editor_note", "")
                if note:
                    sx, sy = p.rect.centerx - offset[0], p.rect.top - offset[1] - 20
                    draw_text(note, font_small, (255, 100, 255), screen, sx, sy)

        # Draw Hover Info (Inventory etc)
        self._draw_hover_info(screen, offset)

        # Draw Typing UI
        if self.typing_mode:
            cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            box_w, box_h = 500, 80
            rect = pygame.Rect(cx - box_w//2, cy - box_h//2, box_w, box_h)

            pygame.draw.rect(screen, (30, 30, 40), rect, border_radius=8)
            pygame.draw.rect(screen, GOLD_COLOR, rect, 2, border_radius=8)

            labels = {
                "note": "EDIT NOTE",
                "map_name": "MAP NAME",
                "map_size": "ARENA SIZE (esim. 8000x5000)",
                "unit_name": "UNIT NAME",
            }
            label = labels.get(self.typing_mode, "EDIT")
            draw_text(f"{label} (Enter to save, Esc to cancel):", font_small, GRAY, screen, rect.x + 15, rect.y + 10)
            draw_text(self.note_text_buffer + "|", font_main, WHITE, screen, rect.x + 15, rect.y + 40)

        # Draw Help Overlay
        if self.show_help:
            self.draw_help(screen)

        # Draw Menu
        if self.show_menu:
            self.draw_menu(screen)

    def draw_help(self, screen):
        """Piirtää pikaohjeet ruudun oikeaan yläkulmaan."""
        lines = [
            "EDITOR CONTROLS",
            "F5: Save Project",
            "F6: Load Project",
            "F7: Map Name",
            "Shift+F7: Arena Size",
            "F8: Toggle Editor",
            "F9: Export Map Code",
            "ESC: Test Mode (Play)",
            "ALT: Open/Close Menu",
            "LMB: Place / Select / Move",
            "RMB: Cancel Selection",
            "DEL: Delete Object",
            "R: Rotate Object",
            "ARROWS: Pan / Nudge",
            "G: Toggle Grid",
            "X: Toggle Snap",
            "J: Toggle Shadow",
            "Shift+J: Shadow Shape",
            "H: Toggle Hitboxes",
            "N: Edit Note",
            "U: Rename Unit",
            "Shift+Arrows: Resize Box",
            "Alt+Arrows: Move Box",
            "Enter: Apply Box to All",
            "F: Flip Unit",
            "PgUp/Dn: Z-Order",
            "C: Cycle Team Color",
            "Shift+1-4: Edit Gear",
            "Ctrl+Z: Undo",
            "Ctrl+D: Duplicate",
        ]
        
        w = 220
        h = len(lines) * 20 + 20
        x = SCREEN_WIDTH - w - 10
        y = 10
        
        # Jos menu on auki, siirrä vasemmalle
        if self.show_menu:
            x -= 300
            
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, (x, y))
        pygame.draw.rect(screen, (100, 100, 100), (x, y, w, h), 1)
        
        for i, line in enumerate(lines):
            col = GOLD_COLOR if i == 0 else WHITE
            draw_text(line, font_small, col, screen, x + 10, y + 10 + i * 20)

    def _draw_hover_info(self, screen, offset):
        mx, my = pygame.mouse.get_pos()
        wx = mx + offset[0]
        wy = my + offset[1]
        
        found = None
        # Find top-most unit
        if self.manager.current_arena:
            for p in reversed(self.manager.current_arena.props):
                if hasattr(p, "rect") and p.rect.collidepoint(wx, wy):
                    if hasattr(p, "team_color"): # It's a unit
                        if getattr(p, "is_dead", False): continue # Skip dead units
                        found = p
                        break
        
        if found:
            # Draw Team Indicator
            cx, cy = found.rect.centerx - offset[0], found.rect.bottom - offset[1]
            
            col = found.team_color
            if not isinstance(col, (tuple, list)):
                col = (150, 150, 150)

            pygame.draw.ellipse(screen, col, (cx - 20, cy - 8, 40, 16), 3)
            
            # Draw Info Box
            bx, by = mx + 20, my + 20
            bw, bh = 220, 140
            
            # Ensure on screen
            if bx + bw > SCREEN_WIDTH: bx -= bw + 40
            if by + bh > SCREEN_HEIGHT: by -= bh + 40
            
            pygame.draw.rect(screen, (30, 30, 40), (bx, by, bw, bh), border_radius=8)
            pygame.draw.rect(screen, col, (bx, by, bw, bh), 2, border_radius=8)
            
            draw_text(found.name, font_main, WHITE, screen, bx + 10, by + 10)
            
            # Equipment
            eq = getattr(found, "equipment", {})
            mh = eq.get("main_hand"); mh_n = mh.name if mh else "None"
            oh = eq.get("off_hand"); oh_n = oh.name if oh else "None"
            bd = eq.get("body"); bd_n = bd.name if bd else "None"
            
            draw_text(f"Main (S+1): {mh_n}", font_small, (200, 200, 200), screen, bx + 10, by + 40)
            draw_text(f"Off (S+2): {oh_n}", font_small, (200, 200, 200), screen, bx + 10, by + 60)
            draw_text(f"Body (S+3): {bd_n}", font_small, (200, 200, 200), screen, bx + 10, by + 80)

    def _draw_grid_lines(self, screen, offset):
        w, h = screen.get_size()
        # Calculate start based on offset to align with world 0,0
        start_x = -(offset[0] % self.grid_size)
        start_y = -(offset[1] % self.grid_size)
        
        # Draw vertical lines
        for x in range(start_x, w, self.grid_size):
            pygame.draw.line(screen, (50, 50, 60), (x, 0), (x, h))
        # Draw horizontal lines
        for y in range(start_y, h, self.grid_size):
            pygame.draw.line(screen, (50, 50, 60), (0, y), (w, y))

    def draw_menu(self, screen):
        # Background
        pygame.draw.rect(screen, (30, 30, 35), self.menu_rect)
        pygame.draw.line(screen, GOLD_COLOR, (self.menu_rect.left, 0), (self.menu_rect.left, SCREEN_HEIGHT), 2)
        
        # Categories
        cat_y = 10
        x = self.menu_rect.left + 10
        
        for cat in self.categories.keys():
            col = GOLD_COLOR if cat == self.current_category else GRAY
            draw_text(cat, font_main, col, screen, x, cat_y)
            cat_y += 30
            
        pygame.draw.line(screen, (100, 100, 100), (x, cat_y), (SCREEN_WIDTH, cat_y), 1)
        
        # Items
        item_y = cat_y + 10 - self.scroll_y
        if self.current_category == "System":
            items = self._system_items()
        else:
            items = self.categories[self.current_category]

        # Clip
        clip_rect = pygame.Rect(self.menu_rect.left, cat_y + 2, self.menu_rect.width, SCREEN_HEIGHT - cat_y - 70)
        screen.set_clip(clip_rect)
        
        for item_class in items:
            name = item_class if isinstance(item_class, str) else item_class.__name__
            col = WHITE
            if self.selected_prop_class == item_class: col = GREEN
            
            draw_text(name, font_small, col, screen, x, item_y)
            item_y += 25
            
        screen.set_clip(None)
        
        # Draw Team Indicator at bottom of menu
        bot_y = SCREEN_HEIGHT - 70
        pygame.draw.rect(screen, (25, 25, 30), (self.menu_rect.left, bot_y, self.menu_rect.width, 70))
        pygame.draw.line(screen, (80, 80, 80), (self.menu_rect.left, bot_y), (SCREEN_WIDTH, bot_y), 1)
        
        team_name = self.team_colors[self.team_color_idx][0]
        current_col = self.team_colors[self.team_color_idx][1]
        
        draw_text("Active Team (Press C):", font_small, GRAY, screen, self.menu_rect.left + 15, bot_y + 10)
        
        swatch_rect = pygame.Rect(self.menu_rect.left + 15, bot_y + 35, 20, 20)
        pygame.draw.rect(screen, current_col, swatch_rect, border_radius=3)
        pygame.draw.rect(screen, WHITE, swatch_rect, 1, border_radius=3)
        draw_text(team_name, font_main, WHITE, screen, self.menu_rect.left + 45, bot_y + 32)

    def _system_items(self):
        """System-välilehden rivit: karttakomennot + custom-kartat."""
        items = ["Export Map Code (F9)", "Rename Map (F7)",
                 "Resize Arena (Shift+F7)", "New Blank Map"]
        try:
            from maps.custom_maps import custom_map_names
            items.extend(f"Load: {name}" for name in custom_map_names())
        except Exception:
            pass
        return items

    def _run_system_command(self, name):
        arena = self.manager.current_arena
        if name.startswith("Export Map Code"):
            self.export_map()
        elif name.startswith("Rename Map"):
            self._start_text_input("map_name")
        elif name.startswith("Resize Arena"):
            self._start_text_input("map_size")
        elif name == "New Blank Map" and arena is not None:
            doc = {"format": map_document.FORMAT_KEY, "version": 1,
                   "name": getattr(arena, "map_name", "New Map") or "New Map",
                   "width": getattr(arena, "width", 5760),
                   "height": getattr(arena, "height", 3240),
                   "props": [], "floor_props": [], "units": []}
            map_document.apply_to_arena(doc, arena, self.manager)
            print("Arena cleared (New Blank Map)")
        elif name.startswith("Load: ") and arena is not None:
            from maps.custom_maps import get_custom_map
            doc = get_custom_map(name[6:])
            if doc:
                map_document.apply_to_arena(doc, arena, self.manager)
                print(f"Custom map loaded: {doc['name']} "
                      f"({doc['width']}x{doc['height']})")
                if hasattr(self.manager, "vfx"):
                    self.manager.vfx.show_damage(
                        SCREEN_WIDTH//2, SCREEN_HEIGHT//2,
                        f"LOADED: {doc['name']}", color=GREEN)

    def handle_menu_click(self, mx, my):
        # Check Categories
        cat_y = 10
        x = self.menu_rect.left + 10

        for cat in self.categories.keys():
            if pygame.Rect(x, cat_y, 200, 25).collidepoint(mx, my):
                self.current_category = cat
                self.scroll_y = 0
                return
            cat_y += 30

        # Check Items
        item_y = cat_y + 10 - self.scroll_y
        if self.current_category == "System":
            items = self._system_items()
        else:
            items = self.categories[self.current_category]

        for item_class in items:
            name = item_class if isinstance(item_class, str) else item_class.__name__
            if pygame.Rect(x, item_y, 250, 20).collidepoint(mx, my):
                if isinstance(item_class, str):
                    self._run_system_command(name)
                    return
                self.selected_prop_class = item_class
                self.ghost_class = None # Force regen
                self.ghost_angle = 0
                print(f"Selected: {name}")
                return
            item_y += 25

    def place_prop(self, x, y):
        if not self.manager.current_arena: return

        obj = None

        # Try with variant first
        try:
            if isinstance(self.selected_prop_class, str): return # Skip strings (commands)

            # Vesi ja laituri: lattiakerrokseen + esteet uusiksi
            arena = self.manager.current_arena
            if self.selected_prop_class is WaterBody:
                water = carve_water(arena, (x, y, 400, 300),
                                    seed=random.randint(1, 9999))
                self.history.append({"type": "place", "obj": water})
                return
            if self.selected_prop_class is FishingJetty:
                jetty = FishingJetty(x, y)
                arena.floor_props.append(jetty)
                rebuild_water_blockers(arena)
                self.history.append({"type": "place", "obj": jetty})
                print(f"Jetty placed; fishing spots: "
                      f"{getattr(arena, 'fishing_spots', [])}")
                return

            current_color = self.team_colors[self.team_color_idx][1]
            
            # Special handling for Units
            if self.selected_prop_class == Villager:
                obj = Villager("Villager", "Human", x, y, current_color)
            elif self.selected_prop_class == Bard:
                obj = Bard("Bard", "Elf", x, y, current_color)
            elif self.selected_prop_class == MardaShant:
                obj = MardaShant(x, y)
            elif self.selected_prop_class == GiantRat:
                obj = GiantRat("Rat", x, y, team_color=current_color)
            elif self.selected_prop_class == Human:
                obj = Human("Bandit", x, y, current_color, "Common")
            elif self.selected_prop_class == Orc:
                obj = Orc("Orc", x, y, current_color)
            elif self.selected_prop_class == Elf:
                obj = Elf("Elf", x, y, current_color)
            elif self.selected_prop_class == Goblin:
                obj = Goblin("Goblin", x, y, current_color)
            elif self.selected_prop_class == RatRider:
                obj = RatRider("Rat Rider", x, y, current_color)
            elif self.selected_prop_class == RatKing:
                obj = RatKing("Rat King", x, y)
            elif self.selected_prop_class == UndeadSkeleton:
                obj = UndeadSkeleton("Skeleton", x, y, current_color)
            elif self.selected_prop_class == UndeadZombie:
                obj = UndeadZombie("Zombie", x, y, current_color)
            elif self.selected_prop_class == UndeadSkeletonArcher:
                obj = UndeadSkeletonArcher("Archer", x, y, current_color)
            elif self.selected_prop_class == CorruptedCrow:
                obj = CorruptedCrow("Crow", x, y, current_color)
            elif self.selected_prop_class == BogLeech:
                obj = BogLeech("Leech", x, y, current_color)
            elif self.selected_prop_class == GiantFrog:
                obj = GiantFrog("Frog", x, y, current_color)
            elif self.selected_prop_class == MnemonicDevourer:
                obj = MnemonicDevourer()
                obj.rect.topleft = (x, y)
            elif self.selected_prop_class in [StoneFloor, WoodFloor, GrassFloor]:
                obj = self.selected_prop_class(x, y, variant=self.variant_index)
            else:
                # Standard Props
                obj = self.selected_prop_class(x, y, variant=self.variant_index)
        except Exception:
            # Fallback to default constructor
            try:
                obj = self.selected_prop_class(x, y)
            except Exception:
                print(f"Could not instantiate {self.selected_prop_class.__name__}")
                return

        # Apply rotation
        if self.ghost_angle != 0 and hasattr(obj, "rotate"):
            obj.rotate(self.ghost_angle)

        # Apply flip
        if hasattr(obj, "facing_right"):
            obj.facing_right = self.ghost_facing_right

        # Apply shadow settings
        obj.has_shadow = self.shadow_active
        obj._shadow_shape = self.shadow_shape

        # Add to arena
        # Jos on lattia, lisää floor_props listaan (jos olemassa), muuten props
        if getattr(obj, "is_floor", False) and hasattr(self.manager.current_arena, "floor_props"):
            self.manager.current_arena.floor_props.append(obj)
        else:
            self.manager.current_arena.props.append(obj)
        
        # KORJAUS: Älä lisää yksiköitä (Gladiator) esteisiin, muuten ne törmäävät itseensä!
        # Älä myöskään lisää lattiaa tai efektiemittereitä esteisiin
        if obj.rect.w > 0 and obj.rect.h > 0 and not isinstance(obj, Gladiator) \
                and not getattr(obj, "is_floor", False) \
                and not getattr(obj, "is_effect", False):
            self.manager.current_arena.obstacles.append(obj)

        # Tag for export
        obj._editor_created = True
        
        # Record for Undo
        self.history.append({"type": "place", "obj": obj})
        print(f"Placed: {obj}")

    def start_drag(self, wx, wy, offset):
        if not self.manager.current_arena: return
        
        # Find top-most prop under mouse
        found = None
        for p in reversed(self.manager.current_arena.props):
            if hasattr(p, "image_pos") and p.image:
                r = pygame.Rect(p.image_pos[0], p.image_pos[1], p.image.get_width(), p.image.get_height())
                if r.collidepoint(wx, wy):
                    found = p
                    break
        
        if found:
            self.dragged_prop = found
            self.drag_start_pos = found.image_pos # Store for undo
            self.drag_offset = (wx - found.image_pos[0], wy - found.image_pos[1])
            print(f"Dragging {found}")

    def stop_drag(self):
        if self.dragged_prop:
            p = self.dragged_prop
            # Record move for Undo only if position changed
            if self.drag_start_pos != p.image_pos:
                self.history.append({"type": "move", "obj": p, "old_pos": self.drag_start_pos})
                # Tag as modified so it gets exported (even if not created in this session)
                p._editor_created = True 
            
            self.dragged_prop = None

    def delete_hovered(self, offset):
        if not self.manager.current_arena: return
        mx, my = pygame.mouse.get_pos()
        wx = mx + offset[0]
        wy = my + offset[1]
        
        found = None
        for p in reversed(self.manager.current_arena.props):
            if hasattr(p, "image_pos") and p.image:
                r = pygame.Rect(p.image_pos[0], p.image_pos[1], p.image.get_width(), p.image.get_height())
                if r.collidepoint(wx, wy):
                    found = p
                    break
        
        if found:
            if found in self.manager.current_arena.props:
                self.manager.current_arena.props.remove(found)
            if found in self.manager.current_arena.obstacles:
                self.manager.current_arena.obstacles.remove(found)
            # Tarkista myös floor_props
            if hasattr(self.manager.current_arena, "floor_props") and found in self.manager.current_arena.floor_props:
                self.manager.current_arena.floor_props.remove(found)
            
            self.history.append({"type": "delete", "obj": found})
            print(f"Deleted {found}")

    def start_note_input(self, offset):
        mx, my = pygame.mouse.get_pos()
        found = self._find_hovered(mx + offset[0], my + offset[1])
        if found:
            self._start_text_input("note", found)

    def handle_inventory_edit(self, key, offset):
        mx, my = pygame.mouse.get_pos()
        wx = mx + offset[0]
        wy = my + offset[1]
        
        found = None
        if self.manager.current_arena:
            for p in reversed(self.manager.current_arena.props):
                if hasattr(p, "rect") and p.rect.collidepoint(wx, wy):
                    if hasattr(p, "equipment"):
                        found = p
                        break
        
        if found:
            slot = None
            lst = []
            if key == pygame.K_1: slot = "main_hand"; lst = self.item_lists["main_hand"]
            elif key == pygame.K_2: slot = "off_hand"; lst = self.item_lists["off_hand"]
            elif key == pygame.K_3: slot = "body"; lst = self.item_lists["body"]
            elif key == pygame.K_4: slot = "head"; lst = self.item_lists["head"]
            
            if slot and lst:
                # Cycle
                current = found.equipment.get(slot)
                curr_name = current.name if current else "None"
                
                try: idx = lst.index(curr_name)
                except Exception: idx = -1
                
                new_name = lst[(idx + 1) % len(lst)]
                
                item = create_item(new_name) if new_name != "None" else None
                found.equip_item(item)
                
                found._editor_created = True # Mark modified
                print(f"Equipped {new_name} to {found.name}")
                
                if self.manager and hasattr(self.manager, "vfx"):
                    self.manager.vfx.show_damage(found.rect.centerx, found.rect.top - 20, new_name, color=GOLD_COLOR)

    def flip_selection(self, offset):
        # 1. Ghost (Placing mode)
        if self.selected_prop_class and not self.show_menu:
            self.ghost_facing_right = not self.ghost_facing_right
            # Force update visual
            if self.ghost_instance and hasattr(self.ghost_instance, "facing_right"):
                self.ghost_instance.facing_right = self.ghost_facing_right
            return

        # 2. Hovered Unit (Editing mode)
        mx, my = pygame.mouse.get_pos()
        wx = mx + offset[0]
        wy = my + offset[1]
        
        found = self._find_hovered(wx, wy)
        if found and hasattr(found, "facing_right"):
            found.facing_right = not found.facing_right
            found._editor_created = True
            print(f"Flipped {found.name}")

    def change_z_order(self, offset, direction):
        mx, my = pygame.mouse.get_pos()
        wx = mx + offset[0]
        wy = my + offset[1]
        
        found = self._find_hovered(wx, wy)
        if found:
            props = self.manager.current_arena.props
            if found in props:
                idx = props.index(found)
                new_idx = idx + direction
                if 0 <= new_idx < len(props):
                    props.pop(idx)
                    props.insert(new_idx, found)
                    print(f"Moved {found} Z-order {direction}")

    def _find_hovered(self, wx, wy):
        if not self.manager.current_arena: return None
        # Search reversed to find top-most
        for p in reversed(self.manager.current_arena.props):
            if hasattr(p, "image_pos") and p.image:
                r = pygame.Rect(p.image_pos[0], p.image_pos[1], p.image.get_width(), p.image.get_height())
                if r.collidepoint(wx, wy):
                    return p
        return None

    def adjust_hitbox(self, offset, dw, dh, dx, dy):
        mx, my = pygame.mouse.get_pos()
        wx = mx + offset[0]
        wy = my + offset[1]
        
        found = self._find_hovered(wx, wy)
        if found:
            # Muokkaa rectiä
            found.rect.width = max(1, found.rect.width + dw)
            found.rect.height = max(1, found.rect.height + dh)
            found.rect.x += dx
            found.rect.y += dy
            
            found._hitbox_modified = True
            found._editor_created = True
            self.show_hitboxes = True # Näytä hitboxit automaattisesti kun muokataan
            print(f"Modified Hitbox: {found.name} {found.rect}")

    def apply_hitbox_to_all(self, offset):
        mx, my = pygame.mouse.get_pos()
        wx = mx + offset[0]
        wy = my + offset[1]
        
        target = self._find_hovered(wx, wy)
        if target and getattr(target, "_hitbox_modified", False):
            # Laske suhteellinen offset kuvan sijainnista
            # Prop.image_pos on kuvan vasen yläkulma
            rel_x = target.rect.x - target.image_pos[0]
            rel_y = target.rect.y - target.image_pos[1]
            w = target.rect.width
            h = target.rect.height
            
            count = 0
            for p in self.manager.current_arena.props:
                if type(p) == type(target):
                    p.rect.width = w
                    p.rect.height = h
                    p.rect.x = p.image_pos[0] + rel_x
                    p.rect.y = p.image_pos[1] + rel_y
                    p._hitbox_modified = True
                    count += 1
            
            if self.manager and hasattr(self.manager, "vfx"):
                self.manager.vfx.show_damage(target.rect.centerx, target.rect.top - 40, f"Updated {count} Hitboxes!", color=GREEN)
            print(f"Applied hitbox to {count} instances of {type(target).__name__}")

    def rotate_selection(self):
        # Jos raahataan, käännä raahattavaa
        if self.dragged_prop and hasattr(self.dragged_prop, "rotate"):
            self.dragged_prop.rotate(90)
            self.dragged_prop._editor_created = True
        # Muuten käännä haamua
        else:
            self.ghost_angle = (self.ghost_angle + 90) % 360
            self.ghost_class = None # Force regen to apply rotation cleanly
            print(f"Rotation: {self.ghost_angle}")

    def apply_shadow_to_hovered(self, offset):
        mx, my = pygame.mouse.get_pos()
        wx = mx + offset[0]
        wy = my + offset[1]
        
        found = self._find_hovered(wx, wy)
        if found:
            found.has_shadow = self.shadow_active
            found._shadow_shape = self.shadow_shape
            found._editor_created = True

    def undo_last_action(self):
        if not self.history:
            print("Nothing to undo.")
            return
            
        action = self.history.pop()
        
        if action["type"] == "place":
            obj = action["obj"]
            if obj in self.manager.current_arena.props:
                self.manager.current_arena.props.remove(obj)
            if obj in self.manager.current_arena.obstacles:
                self.manager.current_arena.obstacles.remove(obj)
            if hasattr(self.manager.current_arena, "floor_props") and obj in self.manager.current_arena.floor_props:
                self.manager.current_arena.floor_props.remove(obj)
            # Vesi/laituri poistui -> esteet uusiksi
            if isinstance(obj, (WaterBody, FishingJetty)):
                rebuild_water_blockers(self.manager.current_arena)
            print(f"Undo Place: {obj}")
            
        elif action["type"] == "delete":
            obj = action["obj"]
            
            if getattr(obj, "is_floor", False) and hasattr(self.manager.current_arena, "floor_props"):
                self.manager.current_arena.floor_props.append(obj)
            else:
                self.manager.current_arena.props.append(obj)
                
            if obj.rect.w > 0 and obj.rect.h > 0 and not isinstance(obj, Gladiator) and not getattr(obj, "is_floor", False):
                self.manager.current_arena.obstacles.append(obj)
            print(f"Undo Delete: {obj}")
            
        elif action["type"] == "move":
            obj = action["obj"]
            old_pos = action["old_pos"]
            # Restore pos
            dx = old_pos[0] - obj.image_pos[0]
            dy = old_pos[1] - obj.image_pos[1]
            obj.image_pos = old_pos
            obj.rect.x += dx
            obj.rect.y += dy
            print(f"Undo Move: {obj}")

    def duplicate_hovered(self, offset):
        mx, my = pygame.mouse.get_pos()
        wx = mx + offset[0]
        wy = my + offset[1]
        
        found = None
        for p in reversed(self.manager.current_arena.props):
            if hasattr(p, "image_pos") and p.image:
                r = pygame.Rect(p.image_pos[0], p.image_pos[1], p.image.get_width(), p.image.get_height())
                if r.collidepoint(wx, wy):
                    found = p
                    break
        
        if found:
            cls = found.__class__
            x, y = found.image_pos
            variant = getattr(found, "variant", 1)
            
            try:
                # Use found unit's color for duplication
                col = getattr(found, "team_color", self.team_colors[self.team_color_idx][1])
                # Special handling for Units duplication
                if cls == Villager:
                    new_obj = Villager("Villager", "Human", x, y, col)
                elif cls == Bard:
                    new_obj = Bard("Bard", "Elf", x, y, col)
                elif cls == GiantRat:
                    new_obj = GiantRat("Rat", x, y, team_color=col)
                elif cls == MardaShant:
                    new_obj = MardaShant(x, y)
                elif cls == Human:
                    new_obj = Human("Bandit", x, y, col, "Common")
                elif cls == Orc:
                    new_obj = Orc("Orc", x, y, col)
                elif cls == Elf:
                    new_obj = Elf("Elf", x, y, col)
                elif cls == Goblin:
                    new_obj = Goblin("Goblin", x, y, col)
                elif cls == RatRider:
                    new_obj = RatRider("Rat Rider", x, y, col)
                elif cls == RatKing:
                    new_obj = RatKing("Rat King", x, y)
                elif cls == UndeadSkeleton:
                    new_obj = UndeadSkeleton("Skeleton", x, y, col)
                elif cls == UndeadZombie:
                    new_obj = UndeadZombie("Zombie", x, y, col)
                elif cls == UndeadSkeletonArcher:
                    new_obj = UndeadSkeletonArcher("Archer", x, y, col)
                elif cls == CorruptedCrow:
                    new_obj = CorruptedCrow("Crow", x, y, col)
                elif cls == BogLeech:
                    new_obj = BogLeech("Leech", x, y, col)
                elif cls == GiantFrog:
                    new_obj = GiantFrog("Frog", x, y, col)
                elif cls == MnemonicDevourer:
                    new_obj = MnemonicDevourer()
                    new_obj.rect.topleft = (x, y)
                else:
                    new_obj = cls(x, y, variant=variant)
            except Exception:
                try:
                    new_obj = cls(x, y)
                except Exception:
                    print("Cannot duplicate complex object")
                    return
            
            # Apply color
            new_obj.team_color = col
            
            self.manager.current_arena.props.append(new_obj)
            if new_obj.rect.w > 0 and new_obj.rect.h > 0 \
                    and not isinstance(new_obj, Gladiator) \
                    and not getattr(new_obj, "is_floor", False) \
                    and not getattr(new_obj, "is_effect", False):
                self.manager.current_arena.obstacles.append(new_obj)
            
            new_obj._editor_created = True
            self.history.append({"type": "place", "obj": new_obj})
            
            # Start dragging immediately
            self.dragged_prop = new_obj
            self.drag_start_pos = (x, y)
            self.drag_offset = (wx - x, wy - y)
            print(f"Duplicated {found}")

    def export_map(self):
        """Vie KOKO kartan yhdeksi JSON-riviksi (VARRACOR-MAP).

        Rivi kirjoitetaan map_export.txt:hen ja tulostetaan konsoliin
        selkein merkein. Työnkulku: kopioi rivi chattiin -> se
        kovakoodataan maps/custom_maps.py-rekisteriin -> System-valikon
        'Load:' lataa sen takaisin editoriin millä koneella tahansa.
        """
        arena = self.manager.current_arena
        if arena is None:
            return
        doc = map_document.serialize_map(arena)
        blob = map_document.export_blob(doc)
        try:
            with open("map_export.txt", "w") as f:
                f.write(blob + "\n")
        except Exception as e:
            print(f"Error writing map_export.txt: {e}")
        stats = (f"{len(doc['props'])} props, "
                 f"{len(doc['floor_props'])} floor, "
                 f"{len(doc['units'])} units, "
                 f"{doc['width']}x{doc['height']}")
        print("=" * 70)
        print(f"MAP EXPORT: {doc['name']} ({stats})")
        print("KOPIOI ALLA OLEVA RIVI (myos map_export.txt:ssa):")
        print("=" * 70)
        print(blob)
        print("=" * 70)
        if hasattr(self.manager, "vfx"):
            self.manager.vfx.show_damage(
                SCREEN_WIDTH//2, SCREEN_HEIGHT//2,
                f"EXPORTED: {doc['name']}", color=GREEN)
