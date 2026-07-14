# menus/commander_skill_menu.py
import pygame
from settings import *
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, draw_panel, GOLD_COLOR, WHITE, RED, GRAY
from menus.base_menu import BaseMenu
from sound_manager import sound_system
from skills.commander_skills_data import (COMMANDER_SKILL_TREE,
                                          COMMANDER_COMMAND_TREE)

class CommanderSkillMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_back = UIButton(30, 30, 140, 52, "BACK", None, GRAY)
        self.unit = self.manager.player_character
        
        # Camera
        self.cam_x = SCREEN_WIDTH // 2
        self.cam_y = SCREEN_HEIGHT // 2 + 100 # Aloitetaan hieman alempaa
        self.zoom = 1.0
        
        # Dragging
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)
        self.drag_total = 0

        self.NODE_R = 30

        # Välilehdet: COMMAND = johtaminen (tiimikoko, huudot, läsnäolo),
        # TRADECRAFT = elämäntaitobonukset. Pelaajapalaute: johtamis-
        # valinnat eivät saa hukkua crafting-noodien sekaan.
        self.tabs = [("COMMAND", COMMANDER_COMMAND_TREE),
                     ("TRADECRAFT", COMMANDER_SKILL_TREE)]
        self.active_tab = "COMMAND"
        self.tab_rects = []

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()

        if self.btn_back.is_clicked(event):
            self.next_state = "manager_menu"
            sound_system.play_sound("click")
            return

        # Mouse Drag Logic
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.btn_back.rect.collidepoint(mouse_pos):
                self.is_dragging = True
                self.last_mouse_pos = mouse_pos
                self.drag_total = 0
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
            # Jos ei raahattu paljoa, se on klikkaus
            if self.drag_total < 5:
                self._handle_click(mouse_pos)
            self.drag_total = 0

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                dx = mouse_pos[0] - self.last_mouse_pos[0]
                dy = mouse_pos[1] - self.last_mouse_pos[1]
                self.cam_x += dx
                self.cam_y += dy
                self.drag_total += abs(dx) + abs(dy)
                self.last_mouse_pos = mouse_pos

    def _tree(self):
        for name, tree in self.tabs:
            if name == self.active_tab:
                return tree
        return COMMANDER_COMMAND_TREE

    def _handle_click(self, pos):
        # Välilehden vaihto
        for rect, name in self.tab_rects:
            if rect.collidepoint(pos):
                self.active_tab = name
                sound_system.play_sound("click")
                return
        node_id = self._pick_node(pos)
        if node_id:
            self._try_unlock(node_id)

    def _try_unlock(self, s_id):
        data = self._tree()[s_id]
        
        # 1. Onko jo auki?
        if s_id in self.unit.unlocked_skills:
            return

        # 2. Onko pisteitä?
        cost = data.get("cost", 1)
        if self.unit.skill_points < cost:
            sound_system.play_sound("error")
            print("Not enough skill points!")
            return

        # 3. Onko vaatimukset täytetty?
        reqs = data.get("requires", [])
        for r in reqs:
            if r not in self.unit.unlocked_skills:
                sound_system.play_sound("error")
                print(f"Requires {self._tree()[r]['name']}")
                return

        # 4. Level check
        min_lvl = data.get("min_level", 1)
        if self.unit.level < min_lvl:
            sound_system.play_sound("error")
            print(f"Requires Level {min_lvl}")
            return

        # UNLOCK!
        self.unit.skill_points -= cost
        self.unit.unlocked_skills.add(s_id)
        self.unit.calculate_final_stats() # Päivitä statsit heti
        sound_system.play_sound("recruit")

    def _world_to_screen(self, wx, wy):
        return int(self.cam_x + wx * self.zoom), int(self.cam_y + wy * self.zoom)

    def _pick_node(self, pos):
        mx, my = pos
        for s_id, data in self._tree().items():
            px, py = data.get("pos", (0, 0))
            cx, cy = self._world_to_screen(px, py)
            if (mx - cx)**2 + (my - cy)**2 <= self.NODE_R**2:
                return s_id
        return None

    def draw(self, screen):
        self.draw_themed_background(screen, "guild")
        self.draw_themed_background(screen, mood="forge")

        # Header
        _t = font_title.render("COMMANDER SKILLS", True, GOLD_COLOR)
        self.draw_header_bar(screen, _t, y=10)
        # Taso + XP-eteneminen näkyviin (pelaajapalaute: "XP ei mene
        # mihinkään" - meni kyllä, mutta kertymä ei näkynyt missään)
        from progression.xp_table import xp_for_level
        lvl = int(self.unit.level)
        cur = int(self.unit.xp) - xp_for_level(lvl)
        need = max(1, xp_for_level(lvl + 1) - xp_for_level(lvl))
        draw_text(f"Level {lvl}   XP {cur}/{need}   "
                  f"Skill Points: {self.unit.skill_points}",
                  font_main, WHITE, screen, SCREEN_WIDTH//2 - 220, 80)
        bar = pygame.Rect(SCREEN_WIDTH//2 - 220, 106, 440, 10)
        pygame.draw.rect(screen, (40, 40, 50), bar, border_radius=5)
        fill = bar.copy(); fill.w = int(bar.w * min(1.0, cur / need))
        if fill.w > 0:
            pygame.draw.rect(screen, (190, 150, 255), fill, border_radius=5)
        pygame.draw.rect(screen, (120, 120, 140), bar, 1, border_radius=5)

        # Välilehdet
        self.tab_rects = []
        tx = SCREEN_WIDTH//2 - 220
        for name, _tree in self.tabs:
            w = font_main.size(name)[0] + 36
            rect = pygame.Rect(tx, 128, w, 38)
            active = name == self.active_tab
            pygame.draw.rect(screen, (70, 60, 30) if active else (40, 40, 52),
                             rect, border_radius=7)
            pygame.draw.rect(screen, GOLD_COLOR if active else (100, 100, 115),
                             rect, 2, border_radius=7)
            draw_text(name, font_main, WHITE if active else (180, 180, 190),
                      screen, rect.x + 18, rect.y + 8)
            self.tab_rects.append((rect, name))
            tx += w + 12
        hint = ("Leadership: roster size, battle shouts, presence."
                if self.active_tab == "COMMAND" else
                "Life-skill perks. Tool tiers & spell slots unlock via "
                "Commander PATHS (by doing).")
        draw_text(hint, font_small, GRAY, screen, tx + 16, 138)

        # Draw Connections
        tree = self._tree()
        for s_id, data in tree.items():
            px, py = data.get("pos", (0, 0))
            start = self._world_to_screen(px, py)
            
            for req_id in data.get("requires", []):
                if req_id in tree:
                    r_pos = tree[req_id]["pos"]
                    end = self._world_to_screen(r_pos[0], r_pos[1])
                    
                    col = (100, 100, 100)
                    if req_id in self.unit.unlocked_skills:
                        col = (200, 200, 100) # Keltainen viiva jos edellinen auki
                    
                    pygame.draw.line(screen, col, start, end, 4)

        # Draw Nodes
        mouse_pos = pygame.mouse.get_pos()
        hover_id = self._pick_node(mouse_pos)

        for s_id, data in tree.items():
            px, py = data.get("pos", (0, 0))
            cx, cy = self._world_to_screen(px, py)
            
            is_unlocked = s_id in self.unit.unlocked_skills
            can_buy = True
            
            # Check requirements for color
            for r in data.get("requires", []):
                if r not in self.unit.unlocked_skills:
                    can_buy = False
            
            if is_unlocked:
                color = (255, 215, 0) # Gold
            elif can_buy:
                color = (100, 200, 100) # Green available
            else:
                color = (60, 60, 60) # Gray locked

            pygame.draw.circle(screen, color, (cx, cy), self.NODE_R)
            pygame.draw.circle(screen, WHITE, (cx, cy), self.NODE_R, 2)
            
            # Icon / Text inside node
            short = data.get("name", "?")[0]
            draw_text(short, font_main, (0,0,0), screen, cx - 8, cy - 12)

        # Tooltip
        if hover_id:
            self._draw_tooltip(screen, hover_id, mouse_pos)

        self.btn_back.check_hover(mouse_pos)
        self.btn_back.draw(screen)

    def _draw_tooltip(self, screen, s_id, pos):
        data = self._tree()[s_id]
        mx, my = pos
        x, y = mx + 20, my + 20
        
        draw_panel(screen, x, y, 300, 150, (30, 30, 40))
        
        name_col = GOLD_COLOR if s_id in self.unit.unlocked_skills else WHITE
        draw_text(data["name"], font_main, name_col, screen, x + 15, y + 15)
        draw_text(f"Cost: {data['cost']} SP", font_small, (200, 200, 200), screen, x + 15, y + 45)
        draw_text(data["desc"], font_small, (180, 180, 180), screen, x + 15, y + 70)
        
        # Effects
        effs = []
        for k, v in data.get("effects", {}).items():
            effs.append(f"{k}: {v}")
        if effs:
            draw_text(", ".join(effs), font_small, (100, 255, 100), screen, x + 15, y + 100)
