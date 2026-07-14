import pygame
import math
from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, GRAY, GREEN, RED, draw_panel, format_money
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from assets.tiles.blacksmith_arena import BlacksmithArena
from assets.tiles.blacksmith_objects import Anvil
from loot_data import BLUEPRINTS

class BlacksmithMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        # Alusta kartta
        self.arena = BlacksmithArena()
        self.manager.current_arena = self.arena
        
        # Pelaaja
        self.player = self.manager.player_character
        
        # Aseta pelaaja ovelle (alhaalla keskellä)
        self.player.rect.centerx = self.arena.width // 2
        self.player.rect.bottom = self.arena.height - 80
        self.player.facing_right = True
        
        # Kamera
        self.camera_x = 0
        self.camera_y = 0
        self._update_camera()
        
        # Uloskäyntialue
        self.exit_rect = pygame.Rect(self.arena.width // 2 - 60, self.arena.height - 60, 120, 60)
        
        # --- ANVIL UI ---
        self.active_anvil = False
        self.selected_recipe = None
        self.craft_btn = None
        self.scroll_y = 0
        self.max_scroll = 0
        
        # Kategoriat ja reseptit
        self.categories = [
            {
                "name": "Scrap Tier",
                "id": "scrap",
                "locked": False,
                "expanded": True,
                "items": [
                    "Scrap Sword", "Scrap Axe", "Scrap Mace", "Scrap Dagger", 
                    "Scrap Spear", "Scrap Shield", "Scrap Bow", "Scrap Crossbow",
                    "Scrap Staff", "Scrap Book"
                ]
            },
            {
                "name": "Weak Tier",
                "id": "weak",
                "locked": True, # Lukittu (Commander Skill Tree avaa myöhemmin)
                "expanded": False,
                "items": [
                    "Weak Sword", "Weak Axe", "Weak Mace", "Weak Spear",
                    "Weak Dagger", "Weak Shield" 
                ]
            }
        ]
        
        self.panel_rect = pygame.Rect(0,0,0,0)
        self.list_rect = pygame.Rect(0,0,0,0)

    def on_enter(self):
        self.manager.current_arena = self.arena
        # Resetoi pelaajan sijainti ovelle
        self.player.rect.centerx = self.arena.width // 2
        self.player.rect.bottom = self.arena.height - 80
        self._update_camera()

    def _open_anvil_ui(self):
        self.active_anvil = True
        self.selected_recipe = None
        self.scroll_y = 0
        
        # Layout
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        w, h = 1100, 700 # Isompi paneeli
        x = cx - w // 2
        y = cy - h // 2
        self.panel_rect = pygame.Rect(x, y, w, h)
        self.list_rect = pygame.Rect(x + 40, y + 80, 350, h - 120)
            
        # Craft button
        self.craft_btn = UIButton(x + w - 250, y + h - 80, 200, 50, "FORGE", None, GREEN)

    def handle_event(self, event):
        self.player = self.manager.player_character
        
        # --- UNIVERSAL MAP EDITOR ---
        if self.handle_editor_event(event):
            return
        
        # 0. ANVIL UI HANDLING
        if self.active_anvil:
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_e):
                self.active_anvil = False
                sound_system.play_sound('click')
                return
            
            if event.type == pygame.MOUSEWHEEL:
                if self.list_rect.collidepoint(pygame.mouse.get_pos()):
                    self.scroll_y -= event.y * 20
                    self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                
                # Listan klikkaukset (Kategoriat ja Reseptit)
                if self.list_rect.collidepoint(mx, my):
                    curr_y = self.list_rect.y - self.scroll_y
                    
                    for cat in self.categories:
                        # Header
                        header_h = 50
                        if curr_y + header_h > self.list_rect.y and curr_y < self.list_rect.bottom:
                            if pygame.Rect(self.list_rect.x, curr_y, self.list_rect.width, header_h).collidepoint(mx, my):
                                cat["expanded"] = not cat["expanded"]
                                sound_system.play_sound('click')
                                return
                        curr_y += header_h + 5
                        
                        if cat["expanded"]:
                            item_h = 40
                            for item_name in cat["items"]:
                                if curr_y + item_h > self.list_rect.y and curr_y < self.list_rect.bottom:
                                    if pygame.Rect(self.list_rect.x, curr_y, self.list_rect.width, item_h).collidepoint(mx, my):
                                        if not cat["locked"]:
                                            self.selected_recipe = item_name
                                            sound_system.play_sound('click')
                                        else:
                                            sound_system.play_sound('error')
                                        return
                                curr_y += item_h + 2
                            curr_y += 10
                
                # Craft button
                if self.selected_recipe and self.craft_btn.rect.collidepoint(event.pos):
                    if self.manager.craft_item(self.selected_recipe, None):
                        sound_system.play_sound('recruit') # Craft sound
                    else:
                        sound_system.play_sound('error')
                    return
            return # Block other input
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p and CHEAT_MODE:
                self.manager.world_paused = not self.manager.world_paused

            if event.key == pygame.K_e:
                # 1. Tarkista uloskäynti
                if self.player.rect.colliderect(self.exit_rect):
                    self.next_state = "muckford_city"
                    sound_system.play_sound('click')
                    return
                
                # 2. Tarkista Alasin (Crafting)
                for prop in self.arena.props:
                    if isinstance(prop, Anvil):
                        if self.player.rect.colliderect(prop.rect.inflate(60, 60)):
                            self._open_anvil_ui()
                            sound_system.play_sound('click')
                            return

            # Combat controls (Dash)
            if event.key == pygame.K_SPACE:
                mx, my = pygame.mouse.get_pos()
                wx = mx + self.camera_x
                wy = my + self.camera_y
                dx = wx - self.player.rect.centerx
                dy = wy - self.player.rect.centery
                self.player.perform_dash(dx, dy)

    def update(self):
        super().update() # BaseMenu update (editor)
        
        if self.active_anvil: return

        # Pelaajan liike
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        speed = 4.0
        
        if not self.player.is_dashing:
            if keys[pygame.K_w]: dy = -speed
            if keys[pygame.K_s]: dy = speed
            if keys[pygame.K_a]: dx = -speed
            if keys[pygame.K_d]: dx = speed
            
        # Käänny hiiren suuntaan
        mx, my = pygame.mouse.get_pos()
        wx = mx + self.camera_x
        self.player.facing_right = (wx >= self.player.rect.centerx)
        
        if dx != 0 or dy != 0:
            self.player.animation_state = "run"
            # X
            self.player.rect.x += dx
            for obs in self.arena.obstacles:
                if self.player.rect.colliderect(obs.rect):
                    if dx > 0: self.player.rect.right = obs.rect.left
                    if dx < 0: self.player.rect.left = obs.rect.right
            # Y
            self.player.rect.y += dy
            for obs in self.arena.obstacles:
                if self.player.rect.colliderect(obs.rect):
                    if dy > 0: self.player.rect.bottom = obs.rect.top
                    if dy < 0: self.player.rect.top = obs.rect.bottom
            
            # Rajoita huoneeseen
            self.player.rect.clamp_ip(pygame.Rect(0, 0, self.arena.width, self.arena.height))
        else:
            self.player.animation_state = "idle"
            
        self.player.update(self.arena.obstacles, self.manager)
        self.arena.update(manager=self.manager)
        self._update_camera()

    def _update_camera(self):
        target_x = self.player.rect.centerx - SCREEN_WIDTH // 2
        target_y = self.player.rect.centery - SCREEN_HEIGHT // 2
        
        # Keskitä pieni huone ruudulle
        if self.arena.width <= SCREEN_WIDTH:
            self.camera_x = -(SCREEN_WIDTH - self.arena.width) // 2
        else:
            self.camera_x = max(0, min(target_x, self.arena.width - SCREEN_WIDTH))
            
        if self.arena.height <= SCREEN_HEIGHT:
            self.camera_y = -(SCREEN_HEIGHT - self.arena.height) // 2
        else:
            self.camera_y = max(0, min(target_y, self.arena.height - SCREEN_HEIGHT))
            
        # Sync to manager (for HUD transparency logic)
        self.manager.camera_x = self.camera_x
        self.manager.camera_y = self.camera_y

    def draw(self, screen):
        screen.fill((10, 10, 12))
        offset = (self.camera_x, self.camera_y)
        
        self.arena.draw_background(screen, offset)
        
        # Piirrä objektit ja pelaaja (Y-sort)
        renderables = list(self.arena.props) + [self.player]
        renderables.sort(key=lambda x: x.rect.bottom)
        
        for obj in renderables:
            if hasattr(obj, "draw_on_screen"):
                obj.draw_on_screen(screen, offset)
                
        self.arena.draw_foreground(screen, offset)
        
        # Prompts
        if self.player.rect.colliderect(self.exit_rect):
            p_x = self.player.rect.centerx - offset[0]
            p_y = self.player.rect.top - offset[1]
            draw_text("Exit (E)", font_main, WHITE, screen, p_x - 40, p_y - 40)
            
        for prop in self.arena.props:
            if isinstance(prop, Anvil) and self.player.rect.colliderect(prop.rect.inflate(60, 60)):
                self.manager._draw_floating_prompt(screen, prop.rect.centerx, prop.rect.top - 20, "E", offset, "Craft")
        
        # Anvil Overlay
        if self.active_anvil:
            self._draw_anvil_ui(screen)
            
        # Editor
        self.draw_editor(screen)

    def _draw_anvil_ui(self, screen):
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Panel
        x, y, w, h = self.panel_rect
        
        draw_panel(screen, x, y, w, h, title="BLACKSMITH'S ANVIL")
        
        # --- RESOURCES INFO (Top Right) ---
        inv = self.manager.inventory
        res_x = x + w - 300
        res_y = y + 40
        
        draw_text("YOUR MATERIALS", font_main, WHITE, screen, res_x, res_y)
        draw_text(f"Scrap Bar: {inv.get('Scrap Metal Bar', 0)}", font_small, (200, 200, 200), screen, res_x, res_y + 25)
        draw_text(f"Swamp Wood: {inv.get('Swamp Wood', 0)}", font_small, (200, 200, 200), screen, res_x, res_y + 45)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # --- Laske listan korkeus ja maksimirullaus ---
        total_content_h = 0
        for cat in self.categories:
            total_content_h += 50 + 5 # header + gap
            if cat["expanded"]:
                total_content_h += len(cat["items"]) * (40 + 2) # item + gap
                total_content_h += 10 # gap after items
        view_h = self.list_rect.height
        self.max_scroll = max(0, total_content_h - view_h)

        # --- LEFT LIST (Scrollable) ---
        # Clip area
        prev_clip = screen.get_clip()
        screen.set_clip(self.list_rect)
        
        curr_y = self.list_rect.y - self.scroll_y
        
        for cat in self.categories:
            # Header
            header_h = 50
            header_rect = pygame.Rect(self.list_rect.x, curr_y, self.list_rect.width, header_h)
            
            # Draw Header
            head_col = (60, 60, 70)
            if header_rect.collidepoint(mouse_pos): head_col = (70, 70, 80)
            pygame.draw.rect(screen, head_col, header_rect, border_radius=5)
            
            icon = "[-]" if cat["expanded"] else "[+]"
            title = f"{icon} {cat['name']}"
            title_col = GOLD_COLOR if not cat["locked"] else (150, 50, 50)
            draw_text(title, font_main, title_col, screen, header_rect.x + 10, header_rect.y + 12)
            
            if cat["locked"]:
                draw_text("(LOCKED)", font_small, (150, 50, 50), screen, header_rect.right - 80, header_rect.y + 15)
            
            curr_y += header_h + 5
            
            # Items
            if cat["expanded"]:
                item_h = 40
                for item_name in cat["items"]:
                    item_rect = pygame.Rect(self.list_rect.x + 20, curr_y, self.list_rect.width - 20, item_h)
                    
                    # Draw Item
                    is_sel = (item_name == self.selected_recipe)
                    bg_col = (40, 40, 50)
                    if is_sel: bg_col = (60, 80, 60)
                    elif item_rect.collidepoint(mouse_pos) and not cat["locked"]: bg_col = (50, 50, 60)
                    
                    pygame.draw.rect(screen, bg_col, item_rect, border_radius=4)
                    if is_sel:
                        pygame.draw.rect(screen, GREEN, item_rect, 1, border_radius=4)
                        
                    txt_col = WHITE if not cat["locked"] else GRAY
                    draw_text(item_name, font_small, txt_col, screen, item_rect.x + 10, item_rect.y + 10)
                    
                    curr_y += item_h + 2
                curr_y += 10
        
        screen.set_clip(prev_clip)
        
        # --- SCROLLBAR ---
        if self.max_scroll > 0:
            bar_bg_rect = pygame.Rect(self.list_rect.right + 5, self.list_rect.top, 10, self.list_rect.height)
            pygame.draw.rect(screen, (20, 20, 25), bar_bg_rect, border_radius=5)
            
            # Handle
            content_h = view_h + self.max_scroll
            handle_h = max(20, (view_h / content_h) * view_h)
            
            scroll_pct = self.scroll_y / self.max_scroll
            handle_y = self.list_rect.top + (self.list_rect.height - handle_h) * scroll_pct
            handle_rect = pygame.Rect(bar_bg_rect.x, handle_y, 10, handle_h)
            pygame.draw.rect(screen, (80, 80, 90), handle_rect, border_radius=5)
            
        # Details Area
        details_x = self.list_rect.right + 40
        details_y = y + 100
        
        # Erotinviiva
        pygame.draw.line(screen, (60, 60, 70), (details_x - 20, y + 80), (details_x - 20, y + h - 80), 2)
        
        if self.selected_recipe:
            data = BLUEPRINTS.get(self.selected_recipe, {})
            
            # Title
            draw_text(self.selected_recipe, font_title, GOLD_COLOR, screen, details_x, details_y)
            
            # Desc
            draw_text(data.get('desc', ''), font_main, (200, 200, 200), screen, details_x, details_y + 60)
            
            # Cost
            draw_text(f"Cost: {format_money(data.get('cost', 0))}", font_main, WHITE, screen, details_x, details_y + 100)
            
            # Materials
            mat_y = details_y + 160
            draw_text("REQUIRED MATERIALS:", font_main, GOLD_COLOR, screen, details_x, mat_y)
            
            mats = data.get('mats', {})
            mat_y += 40
            can_afford = True
            
            for mat, req in mats.items():
                owned = self.manager.inventory.get(mat, 0)
                col = GREEN if owned >= req else RED
                if owned < req: can_afford = False
                
                draw_text(f"• {mat}: {owned}/{req}", font_main, col, screen, details_x + 20, mat_y)
                mat_y += 30
                
            # Gold check
            if self.manager.gold < data.get('cost', 0):
                can_afford = False
                
            # Craft Button
            self.craft_btn.enabled = can_afford
            self.craft_btn.check_hover(mouse_pos)
            self.craft_btn.draw(screen)
            
        else:
            draw_text("Select a blueprint from the list.", font_main, GRAY, screen, details_x, details_y + 100)
            
        # Close hint
        draw_text("Press 'E' or 'ESC' to close", font_small, GRAY, screen, x + w - 180, y + h - 30)
