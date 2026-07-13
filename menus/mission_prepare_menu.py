import pygame
from settings import *
from ui_kit import SpriteButton, draw_text, draw_panel, font_title, font_main, font_small, GOLD_COLOR, RED, GREEN, WHITE, GRAY, format_money
from menus.base_menu import BaseMenu

class MissionPrepareMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.team_limit = 10 # Default for missions
        self.selected_units = []
        
        # Auto-select first 3 alive
        roster = []
        if manager.player_character: roster.append(manager.player_character)
        roster.extend(list(manager.my_team))
        
        living = [u for u in roster if u.current_hp > 0]
        self.selected_units = living[:min(len(living), self.team_limit)]
        
        self.btn_fight = SpriteButton(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80,
            "assets/ui/btn_start_idle.png",
            "assets/ui/btn_start_hover.png",
            "assets/ui/btn_start_pressed.png",
            label_text="START MISSION", target_width=300
        )
        
        self.btn_back = SpriteButton(
            100, 50,
            "assets/ui/btn_exit_idle.png",
            "assets/ui/btn_exit_hover.png",
            "assets/ui/btn_exit_pressed.png",
            label_text="RETREAT", target_width=150
        )

    def _get_mission_intel(self):
        mission = self.manager.selected_mission
        if not mission: return ["No mission selected."]
        
        enemies = mission.get('enemies', [])
        hints = []
        
        # --- SWARM DETECTION ---
        is_swarm = "Crypt" in mission.get('title', '') or "Swarm" in mission.get('title', '')
        if is_swarm:
            hints.append("OBJECTIVE: Survive as long as possible.")
        
        # Analyze enemies
        enemy_names = [e[0] for e in enemies]
        
        # Flavor text & Hints
        if any("Skeleton" in n or "Zombie" in n or "Undead" in n for n in enemy_names):
            hints.append("The restless dead await in the shadows.")
            hints.append("INTEL: Undead are relentless but slow.")
            hints.append("WEAKNESS: Fire and Holy magic.")
            hints.append("RESISTANCE: Ice and Poison.")
        elif any("Rat" in n for n in enemy_names):
            hints.append("Squeaking sounds echo from the darkness.")
            hints.append("INTEL: Beasts swarm in large numbers.")
            hints.append("WEAKNESS: Fire scares them.")
        elif any("Goblin" in n for n in enemy_names):
            hints.append("Chattering and clanking of scrap metal.")
            hints.append("INTEL: Goblins are fast and tricky.")
        elif any("Orc" in n for n in enemy_names):
            hints.append("Heavy footsteps shake the ground.")
            hints.append("INTEL: Orcs are tough and hit hard.")
            hints.append("WEAKNESS: Magic attacks.")
        else:
            hints.append("Unknown threats ahead.")
            hints.append("Stay sharp, Commander.")
            
        return hints

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # Unit selection (Left side)
            start_x = 50
            start_y = 150
            card_w = 320
            card_h = 90
            gap_y = 100
            
            my_roster = []
            if self.manager.player_character: my_roster.append(self.manager.player_character)
            my_roster.extend(list(self.manager.my_team))
            for i, unit in enumerate(my_roster):
                col = i // 7
                row = i % 7
                cx = start_x + col * 340
                cy = start_y + row * gap_y
                rect = pygame.Rect(cx, cy, card_w, card_h)
                if rect.collidepoint(mouse_pos):
                    if unit.current_hp <= 0: return # Can't select dead
                    
                    if unit in self.selected_units:
                        self.selected_units.remove(unit)
                    elif len(self.selected_units) < self.team_limit:
                        self.selected_units.append(unit)
                    return

    def update(self):
        if self.btn_back.update():
            self.next_state = "mission_select"
            
        if self.btn_fight.update():
            if self.selected_units:
                # Asetetaan data latausruudulle ja siirrytään sinne
                # Huom: main.py:n menus-sanakirjassa on "match_loading"
                self.manager.pending_match_data = (self.selected_units, self.team_limit)
                self.next_state = "match_loading"

    def draw(self, screen):
        self.draw_themed_background(screen, "forge")
        
        mission = self.manager.selected_mission
        title = mission['title'] if mission else "Unknown Mission"
        
        draw_text("MISSION BRIEFING", font_title, GOLD_COLOR, screen, SCREEN_WIDTH // 2 - 150, 30)
        draw_text(f"Target: {title}", font_main, WHITE, screen, SCREEN_WIDTH // 2 - 100, 80)

        # --- LEFT: ROSTER ---
        draw_text(f"SELECT SQUAD ({len(self.selected_units)}/{self.team_limit})", font_main, GREEN, screen, 50, 110)
        
        start_x = 50
        start_y = 150
        card_w = 320
        card_h = 90
        gap_y = 100
        
        my_roster = []
        if self.manager.player_character: my_roster.append(self.manager.player_character)
        my_roster.extend(list(self.manager.my_team))
        
        for i, unit in enumerate(my_roster):
            col = i // 7
            row = i % 7
            cx = start_x + col * 340
            cy = start_y + row * gap_y
            
            is_selected = unit in self.selected_units
            is_dead = unit.current_hp <= 0
            
            border_col = (60, 60, 60)
            if is_selected: border_col = GREEN
            if is_dead: border_col = RED
            
            draw_panel(screen, cx, cy, card_w, card_h, color=(30, 30, 40), border_color=border_col)
            
            name_col = WHITE
            if is_dead: name_col = RED
            elif is_selected: name_col = GREEN
            
            draw_text(f"{unit.name} (Lvl {getattr(unit, 'level', 1)})", font_main, name_col, screen, cx + 10, cy + 10)
            
            # Stats row
            s_str = int(getattr(unit, "strength", 0))
            s_dex = int(getattr(unit, "dexterity", 0))
            s_int = int(getattr(unit, "intelligence", 0))
            draw_text(f"STR:{s_str} DEX:{s_dex} INT:{s_int}", font_small, (180, 180, 180), screen, cx + 10, cy + 35)
            
            # HP
            hp_pct = max(0, unit.current_hp / unit.max_hp)
            pygame.draw.rect(screen, (50, 0, 0), (cx + 10, cy + 60, 200, 8))
            pygame.draw.rect(screen, GREEN if not is_dead else RED, (cx + 10, cy + 60, 200 * hp_pct, 8))
            
            # Gear
            wep = getattr(unit, "equipment", {}).get("main_hand")
            w_name = wep.name if wep else "Fists"
            draw_text(w_name, font_small, (200, 200, 100), screen, cx + 220, cy + 60)

        # --- RIGHT: INTEL ---
        intel_x = SCREEN_WIDTH - 500
        intel_y = 150
        intel_w = 450
        intel_h = 400
        
        draw_text("MISSION INTEL", font_main, RED, screen, intel_x, 110)
        draw_panel(screen, intel_x, intel_y, intel_w, intel_h, color=(20, 15, 15), border_color=RED)
        
        hints = self._get_mission_intel()
        iy = intel_y + 20
        for line in hints:
            col = WHITE
            if "WEAKNESS" in line: col = (100, 255, 100)
            if "RESISTANCE" in line: col = (255, 100, 100)
            if "INTEL" in line: col = GOLD_COLOR
            if "OBJECTIVE" in line: col = (255, 165, 0) # Orange
            
            draw_text(line, font_small, col, screen, intel_x + 20, iy)
            iy += 30
            
        # Reward info
        if mission:
            ry = intel_y + intel_h - 80
            draw_text("REWARDS:", font_main, GOLD_COLOR, screen, intel_x + 20, ry)
            
            arena_type = mission.get('arena', '')
            is_wave_mission = arena_type in ["Muckford", "Crypt", "Bog"] or "Swarm" in mission.get('title', '')
            
            if is_wave_mission:
                draw_text("SURVIVE THE WAVES", font_main, (255, 100, 100), screen, intel_x + 20, ry + 25)
                draw_text("Gold & Reputation scale with waves.", font_small, WHITE, screen, intel_x + 20, ry + 50)
                draw_text("Survive longer for better rewards.", font_small, GRAY, screen, intel_x + 20, ry + 70)
            else:
                draw_text(f"{format_money(mission.get('reward_gold', 0))}", font_small, WHITE, screen, intel_x + 20, ry + 25)
                if 'reward_rep' in mission:
                    draw_text(f"{mission['reward_rep']} Reputation", font_small, WHITE, screen, intel_x + 150, ry + 25)

        self.btn_back.draw(screen)
        self.btn_fight.draw(screen)