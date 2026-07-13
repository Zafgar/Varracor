import pygame
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from items.item_registry import create_fists

class ManagerMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.unit = self.manager.player_character
        
        # --- UI LAYOUT ---
        self.btn_back = UIButton(30, 30, 120, 50, "BACK", None, GRAY)
        
        # UUSI NAPPI: Commander Skills
        self.btn_skills = UIButton(SCREEN_WIDTH - 250, 30, 220, 50, "COMMANDER SKILLS", None, GOLD_COLOR)
        
        # UUSI NAPPI: Sponsors (Skills-napin vasemmalla puolella)
        self.btn_sponsors = UIButton(SCREEN_WIDTH - 480, 30, 220, 50, "SPONSORS", None, (100, 200, 255))
        
        # UUSI NAPPI: Reputation (Sponsors-napin vasemmalla puolella)
        self.btn_rep = UIButton(SCREEN_WIDTH - 710, 30, 220, 50, "REPUTATION", None, (200, 100, 255))

        # UUSI NAPPI: Team (areenatiimin hallinta - Team Quarters)
        self.btn_team = UIButton(SCREEN_WIDTH - 940, 30, 220, 50, "TEAM", None, GREEN)

        # UUSI NAPPI: Paths (kykypolut - XP suoraan tekemisestä)
        self.btn_paths = UIButton(SCREEN_WIDTH - 1170, 30, 220, 50, "PATHS", None, (120, 190, 210))
        
        self.slots_center_x = int(SCREEN_WIDTH * 0.30)
        self.slots_center_y = int(SCREEN_HEIGHT * 0.45)
        
        self.bag_x = int(SCREEN_WIDTH * 0.55)
        self.bag_y = 150
        self.bag_w = SCREEN_WIDTH - self.bag_x - 30
        self.bag_h = SCREEN_HEIGHT - self.bag_y - 30
        
        # Drag & Drop State
        self.drag_item = None
        self.drag_source = None      # 'bag' or 'slot'
        self.drag_origin_index = None  # bag real index OR slot name str
        self.drag_origin_obj = None
        
        self.feedback_msg = ""
        self.feedback_timer = 0

    def get_slot_rects(self, cx, cy):
        s = 80
        return {
            # Gear (Top)
            'head':      pygame.Rect(cx, cy - 130, s, s),
            'body':      pygame.Rect(cx, cy + 130, s, s),
            'main_hand': pygame.Rect(cx - 140, cy, s, s),
            'off_hand':  pygame.Rect(cx + 140, cy, s, s),
            
            # Spells / Abilities (Bottom Rows)
            'spell1':    pygame.Rect(cx - 140, cy + 260, s, s),
            'spell2':    pygame.Rect(cx, cy + 260, s, s),
            'spell3':    pygame.Rect(cx + 140, cy + 260, s, s),
            'spell4':    pygame.Rect(cx - 140, cy + 360, s, s),
            'spell5':    pygame.Rect(cx, cy + 360, s, s),
            'spell6':    pygame.Rect(cx + 140, cy + 360, s, s),
            'usable':    pygame.Rect(cx + 280, cy + 260, s, s),
            'usable2':   pygame.Rect(cx + 280, cy + 360, s, s)
        }

    def _show_feedback(self, msg):
        self.feedback_msg = str(msg)
        self.feedback_timer = 120

    def _valid_slot_type(self, item, slot_name: str) -> bool:
        if not item: return True
        slot_name = str(slot_name).lower()
        item_slot = str(getattr(item, "slot_type", "")).lower()
        item_type = str(getattr(item, "type", "")).lower()

        if slot_name.startswith("spell"):
            return (item_slot == "spell") or (item_type == "spell") or ("spell" in item_slot)
        if slot_name in ["head", "body"]:
            return item_slot in ["head", "body"]
        if slot_name == "usable":
            return item_slot == "usable"
        if slot_name in ["main_hand", "off_hand"]:
            if item_slot in ["main_hand", "off_hand", "weapon", "melee", "ranged"]: return True
            if item_type in ["weapon", "melee", "ranged", "shield"]: return True
            return False
        return False

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        if event.type == pygame.KEYDOWN:
            if CHEAT_MODE:
                if event.key == pygame.K_l:
                    if self.unit.add_xp(1000):
                        sound_system.play_sound('recruit')
                        self._show_feedback(f"CHEAT: {self.unit.name} Leveled Up!")
                    else:
                        self._show_feedback(f"CHEAT: {self.unit.name} gained 1000 XP")

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.rect.collidepoint(mouse_pos):
                # Palataan sinne mistä valikko avattiin (kaupunki C-näppäimellä
                # tai hub) - valikko on toimintavalikko pelin sisällä
                self.next_state = getattr(self.manager, "manager_return_state",
                                          None) or "hub"
                sound_system.play_sound('click')
                return
            
            if self.btn_skills.rect.collidepoint(mouse_pos):
                self.next_state = "commander_skills"
                sound_system.play_sound('click')
                return
            
            if self.btn_sponsors.rect.collidepoint(mouse_pos):
                self.next_state = "sponsors"
                sound_system.play_sound('click')
                return
            
            if self.btn_rep.rect.collidepoint(mouse_pos):
                self.next_state = "reputation"
                sound_system.play_sound('click')
                return

            if self.btn_team.rect.collidepoint(mouse_pos):
                self.manager.barracks_return_state = "manager_menu"
                self.next_state = "barracks"
                sound_system.play_sound('click')
                return

            if self.btn_paths.rect.collidepoint(mouse_pos):
                self.next_state = "paths"
                sound_system.play_sound('click')
                return

            # 1. Drag from Bag
            bag_cols = 6
            cell = 74
            start_x = self.bag_x + 10
            start_y = self.bag_y + 10
            
            # Filter bag items (show all for manager)
            bag_items = [(i, item) for i, item in enumerate(self.manager.equipment_bag) if item]
            
            for vi, (real_idx, item) in enumerate(bag_items):
                col = vi % bag_cols
                row = vi // bag_cols
                rect = pygame.Rect(start_x + col * cell, start_y + row * cell, 68, 68)
                
                if rect.collidepoint(mouse_pos):
                    self.drag_item = item
                    self.drag_source = 'bag'
                    self.drag_origin_index = real_idx
                    self.drag_origin_obj = item
                    sound_system.play_sound('click')
                    return

            # 2. Drag from Slot
            slots = self.get_slot_rects(self.slots_center_x, self.slots_center_y)
            for name, rect in slots.items():
                item = self.unit.equipment.get(name)
                if rect.collidepoint(mouse_pos) and item:
                    if getattr(item, "name", "") == "Fists": continue
                    self.drag_item = item
                    self.drag_source = 'slot'
                    self.drag_origin_index = name
                    self.drag_origin_obj = item
                    sound_system.play_sound('click')
                    return

        elif event.type == pygame.MOUSEBUTTONUP:
            if not self.drag_item: return
            
            dropped = False
            slots = self.get_slot_rects(self.slots_center_x, self.slots_center_y)
            
            # A) Drop to Slot
            for name, rect in slots.items():
                if rect.collidepoint(mouse_pos):
                    # Check validity
                    if not self._valid_slot_type(self.drag_item, name):
                        self._show_feedback("Wrong slot type.")
                        sound_system.play_sound('error')
                        break
                    
                    # Check equip requirements
                    ok, reason = self.unit.can_equip_item_to_slot(name, self.drag_item)
                    if not ok:
                        self._show_feedback(reason)
                        sound_system.play_sound('error')
                        break
                        
                    # Handle swap logic
                    origin_slot = None
                    origin_item = None
                    if self.drag_source == "slot":
                        origin_slot = self.drag_origin_index
                        origin_item = self.unit.equipment.get(origin_slot)
                        # Temp unequip
                        if origin_slot == "main_hand": self.unit.equipment["main_hand"] = create_fists()
                        else: self.unit.equipment[origin_slot] = None
                        
                    # Equip
                    old_item = self.unit.equip_item_to_slot(name, self.drag_item)
                    
                    # Verify success
                    if self.unit.equipment.get(name) is self.drag_item:
                        # Success!
                        if self.drag_source == "bag":
                            # Remove from bag
                            if self.drag_origin_index < len(self.manager.equipment_bag) and self.manager.equipment_bag[self.drag_origin_index] is self.drag_origin_obj:
                                self.manager.equipment_bag.pop(self.drag_origin_index)
                            else:
                                # Fallback remove
                                if self.drag_origin_obj in self.manager.equipment_bag:
                                    self.manager.equipment_bag.remove(self.drag_origin_obj)
                        
                        # Return old item to bag
                        if old_item and getattr(old_item, "name", "") not in ["Fists", "No Armor"]:
                            self.manager.equipment_bag.append(old_item)
                            
                        dropped = True
                        sound_system.play_sound('recruit')
                    else:
                        # Failed, revert
                        if origin_slot:
                            self.unit.equipment[origin_slot] = origin_item
                            self.unit.calculate_final_stats()
                        self._show_feedback("Equip failed.")
                        sound_system.play_sound('error')
                    break

            # B) Drop to Bag (Unequip)
            bag_rect = pygame.Rect(self.bag_x, self.bag_y, self.bag_w, self.bag_h)
            if not dropped and bag_rect.collidepoint(mouse_pos):
                if self.drag_source == 'slot':
                    rem = self.unit.unequip_slot(self.drag_origin_index)
                    if rem:
                        self.manager.equipment_bag.append(rem)
                    dropped = True
                    sound_system.play_sound('click')
                elif self.drag_source == 'bag':
                    dropped = True # Cancel drag

            self.drag_item = None
            self.drag_source = None

    def draw(self, screen):
        screen.fill((20, 20, 28))
        self.draw_themed_background(screen, mood="guild")
        
        self.btn_back.check_hover(pygame.mouse.get_pos())
        self.btn_back.draw(screen)
        
        self.btn_skills.check_hover(pygame.mouse.get_pos())
        self.btn_skills.draw(screen)
        
        self.btn_sponsors.check_hover(pygame.mouse.get_pos())
        self.btn_sponsors.draw(screen)
        
        self.btn_rep.check_hover(pygame.mouse.get_pos())
        self.btn_rep.draw(screen)

        self.btn_team.check_hover(pygame.mouse.get_pos())
        self.btn_team.draw(screen)

        self.btn_paths.check_hover(pygame.mouse.get_pos())
        self.btn_paths.draw(screen)
        
        draw_text("COMMANDER PROFILE", font_title, GOLD_COLOR, screen, SCREEN_WIDTH // 2 - 180, 30)
        
        # --- CHARACTER STATS (Left) ---
        cx, cy = self.slots_center_x, self.slots_center_y
        
        # Portrait / Visual
        if not getattr(self.unit, "use_sprites", False):
            self.unit.draw_procedural()
        
        img = getattr(self.unit, "big_image", self.unit.image)
        if img:
            s_img = pygame.transform.smoothscale(img, (160, 240))
            screen.blit(s_img, (cx - 80, cy - 120))
            
        # Stats Panel
        stats_x = 50
        stats_y = 150
        draw_panel(screen, stats_x, stats_y, 300, 400, color=(30, 30, 40))
        
        draw_text(self.unit.name, font_main, WHITE, screen, stats_x + 20, stats_y + 20)
        draw_text(f"Level {self.unit.level}", font_small, GOLD_COLOR, screen, stats_x + 20, stats_y + 50)
        
        sy = stats_y + 90
        draw_text(f"Health: {self.unit.max_hp}", font_small, GREEN, screen, stats_x + 20, sy); sy += 25
        draw_text(f"Mana: {self.unit.max_mana}", font_small, (100, 150, 255), screen, stats_x + 20, sy); sy += 25
        draw_text(f"Stamina: {int(self.unit.max_stamina)}", font_small, YELLOW, screen, stats_x + 20, sy); sy += 35
        
        draw_text(f"Strength: {self.unit.strength}", font_small, RED, screen, stats_x + 20, sy); sy += 25
        draw_text(f"Dexterity: {self.unit.dexterity}", font_small, YELLOW, screen, stats_x + 20, sy); sy += 25
        draw_text(f"Intelligence: {self.unit.intelligence}", font_small, (100, 150, 255), screen, stats_x + 20, sy); sy += 35
        
        draw_text(f"Defense: {self.unit.defense}", font_small, WHITE, screen, stats_x + 20, sy); sy += 25
        draw_text(f"Speed: {self.unit.speed:.1f}", font_small, WHITE, screen, stats_x + 20, sy); sy += 25

        # --- EQUIPMENT SLOTS (Center) ---
        slots = self.get_slot_rects(cx, cy)
        mouse_pos = pygame.mouse.get_pos()
        
        for name, rect in slots.items():
            # Draw slot bg
            col = (60, 60, 70)
            if rect.collidepoint(mouse_pos): col = (80, 80, 90)
            pygame.draw.rect(screen, col, rect, border_radius=8)
            pygame.draw.rect(screen, (100, 100, 100), rect, 2, border_radius=8)
            
            # Label
            l_surf = font_small.render(name.replace("_", " ").upper(), True, (150, 150, 150))
            screen.blit(l_surf, (rect.centerx - l_surf.get_width()//2, rect.top - 20))
            
            # Item
            item = self.unit.equipment.get(name)
            if item and getattr(item, "name", "") not in ["Fists", "No Armor"]:
                if item == self.drag_item:
                    # Ghost
                    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    s.fill((0, 0, 0, 100))
                    screen.blit(s, rect)
                else:
                    if hasattr(item, 'draw_card_icon'):
                        item.draw_card_icon(screen, rect.x + 5, rect.y + 5, 70)
                    
                    # Tooltip on hover
                    if rect.collidepoint(mouse_pos) and not self.drag_item:
                        from ui_kit import draw_item_tooltip
                        draw_item_tooltip(screen, item, mouse_pos[0] + 20, mouse_pos[1] + 20)

        # --- INVENTORY BAG (Right) ---
        draw_text("INVENTORY", font_main, WHITE, screen, self.bag_x, self.bag_y - 30)
        pygame.draw.rect(screen, (25, 25, 30), (self.bag_x, self.bag_y, self.bag_w, self.bag_h), border_radius=10)
        pygame.draw.rect(screen, (60, 60, 70), (self.bag_x, self.bag_y, self.bag_w, self.bag_h), 2, border_radius=10)
        
        bag_cols = 6
        cell = 74
        start_x = self.bag_x + 10
        start_y = self.bag_y + 10
        
        bag_items = [(i, item) for i, item in enumerate(self.manager.equipment_bag) if item]
        
        for vi, (real_idx, item) in enumerate(bag_items):
            col = vi % bag_cols
            row = vi // bag_cols
            bx, by = start_x + col * cell, start_y + row * cell
            rect = pygame.Rect(bx, by, 68, 68)
            
            pygame.draw.rect(screen, (40, 40, 45), rect, border_radius=6)
            
            if item == self.drag_item:
                s = pygame.Surface((68, 68), pygame.SRCALPHA)
                s.fill((0, 0, 0, 100))
                screen.blit(s, rect)
            else:
                if hasattr(item, 'draw_card_icon'):
                    item.draw_card_icon(screen, bx + 4, by + 4, 60)
                
                if rect.collidepoint(mouse_pos) and not self.drag_item:
                    from ui_kit import draw_item_tooltip
                    draw_item_tooltip(screen, item, mouse_pos[0] - 250, mouse_pos[1])

        # --- DRAGGED ITEM ---
        if self.drag_item:
            mx, my = mouse_pos
            if hasattr(self.drag_item, 'draw_card_icon'):
                self.drag_item.draw_card_icon(screen, mx - 30, my - 30, 60)

        # --- FEEDBACK ---
        if self.feedback_timer > 0:
            txt_surf = font_main.render(self.feedback_msg, True, RED)
            bg_rect = txt_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
            bg_rect.inflate_ip(20, 10)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect, border_radius=5)
            screen.blit(txt_surf, txt_surf.get_rect(center=bg_rect.center))
