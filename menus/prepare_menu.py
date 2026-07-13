import pygame
from settings import *
from ui_kit import SpriteButton, draw_text, draw_panel, font_title, font_main, font_small, GOLD_COLOR, RED, GREEN, WHITE, GRAY
from menus.base_menu import BaseMenu

class PrepareMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        # 1. Määritetään taistelun koko (montako ukkoa pitää valita)
        # Oletus on 3, mutta League/Boss voi muuttaa tätä
        self.team_limit = getattr(manager, "battle_size", 3)
        if manager.match_mode == "5v5": self.team_limit = 5
        elif manager.match_mode == "1v1": self.team_limit = 1
        
        # 2. Valitut hahmot (lista objekteja)
        self.selected_units = []
        
        # Jos meillä on vähemmän ukkoja kuin raja, valitaan kaikki automaattisesti
        roster = []
        if manager.player_character: roster.append(manager.player_character)
        roster.extend(list(manager.my_team))
        
        living_units = [u for u in roster if u.current_hp > 0]
        if len(living_units) <= self.team_limit:
            self.selected_units = list(living_units)
        
        # 3. Varmistetaan viholliset (Enemy Preview)
        self._ensure_enemies_exist()

        # 4. UI Napit
        self.btn_fight = SpriteButton(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80,
            "assets/ui/btn_start_idle.png", # Käytetään start-nappia pohjana jos ei ole fight-nappia
            "assets/ui/btn_start_hover.png",
            "assets/ui/btn_start_pressed.png",
            label_text="FIGHT!", target_width=300
        )
        
        self.btn_back = SpriteButton(
            100, 50,
            "assets/ui/btn_exit_idle.png",
            "assets/ui/btn_exit_hover.png",
            "assets/ui/btn_exit_pressed.png",
            label_text="BACK", target_width=150
        )

    def _ensure_enemies_exist(self):
        """
        Varmistaa, että manager.enemy_team on täytetty, jotta voimme näyttää ne.
        """
        # Jos olemme liigassa, haetaan vastustaja liigamoottorista
        if self.manager.mode == "League":
            if not self.manager.current_enemy_team:
                # Jos vastustajaa ei ole arvottu, arvotaan se nyt
                # (Oikeasti tämä pitäisi olla tehty jo aiemmin, mutta varoiksi)
                pass 
            
            # Täytetään enemy_team displayta varten
            if self.manager.current_enemy_team:
                roster = self.manager.current_enemy_team.get_roster(self.team_limit)
                self.manager.enemy_team.empty()
                for e in roster:
                    self.manager.enemy_team.add(e)
                    
        # Jos olemme Arenalla ja tiimi on tyhjä, generoidaan satunnainen
        elif self.manager.mode == "Arena":
            if len(self.manager.enemy_team) == 0:
                self.manager.generate_random_enemy_team(self.team_limit)

        # Monster Hunt / Boss Hunt on ladattu jo aiemmin mission_selectissä

    def handle_event(self, event):
        # Hahmon valinta klikkaamalla (Vain omat hahmot)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # Käydään läpi omat hahmot ja katsotaan osuiko klikkaus korttiin
            # HUOM: mittojen PITÄÄ vastata draw-funktiota (320/90/100),
            # muuten klikkaukset osuvat väärien korttien kohdalle
            start_x = 50
            start_y = 150
            card_w = 320
            card_h = 90
            gap_y = 100
            
            # Käytetään samaa listaa kuin piirrossa
            my_roster = []
            if self.manager.player_character: my_roster.append(self.manager.player_character)
            my_roster.extend(list(self.manager.my_team))
            
            for i, unit in enumerate(my_roster):
                rect = pygame.Rect(start_x, start_y + i * gap_y, card_w, card_h)
                if rect.collidepoint(mouse_pos):
                    if unit.current_hp <= 0: return # Ei voi valita kuollutta
                    self.toggle_selection(unit)
                    return

    def toggle_selection(self, unit):
        if unit in self.selected_units:
            self.selected_units.remove(unit)
            # Soita ääni (deselect)
        else:
            if len(self.selected_units) < self.team_limit:
                self.selected_units.append(unit)
                # Soita ääni (select)

    def update(self):
        # Back nappi - liigasta palataan liigavalikkoon, ei hubiin
        if self.btn_back.update():
            self.next_state = "league" if self.manager.mode == "League" \
                else "hub"

        # Fight nappi
        if self.btn_fight.update():
            if len(self.selected_units) > 0: # Ainakin 1 pitää olla
                # Aloita taistelu valituilla
                self.manager.start_match(self.selected_units, self.team_limit)
                # Grand Slam -finaali alkaa cinematic-juonnolla
                if getattr(self.manager, "match_mode", "") == "PROMOTION":
                    self.next_state = "finale_show"
                else:
                    self.next_state = "battle"

    def draw(self, screen):
        # 1. Tausta (Tumma)
        self.draw_themed_background(screen, "forge")
        
        # Otsikko
        title_text = f"PREPARE FOR BATTLE ({len(self.selected_units)}/{self.team_limit})"
        _t = font_title.render(title_text, True, GOLD_COLOR)
        self.draw_header_bar(screen, _t, y=10)
        
        sub_text = f"Mode: {self.manager.mode} - {self.manager.match_mode}"
        draw_text(sub_text, font_main, (150, 150, 150), screen, SCREEN_WIDTH // 2 - 100, 80)

        # --- LEFT SIDE: MY TEAM ---
        draw_text("YOUR ROSTER", font_main, GREEN, screen, 50, 110)
        
        start_x = 50
        start_y = 150
        card_w = 320
        card_h = 90
        gap_y = 100
        
        my_roster = []
        if self.manager.player_character: my_roster.append(self.manager.player_character)
        my_roster.extend(list(self.manager.my_team))
        
        for i, unit in enumerate(my_roster):
            cx = start_x
            cy = start_y + i * gap_y
            
            # Onko valittu?
            is_selected = unit in self.selected_units
            is_dead = unit.current_hp <= 0
            
            # Reunaväri
            border_col = (60, 60, 60)
            if is_selected: border_col = GREEN
            if is_dead: border_col = (40, 0, 0)
            
            # Piirrä kortti
            draw_panel(screen, cx, cy, card_w, card_h, color=(30, 30, 40), border_color=border_col)
            
            # Tiedot
            name_col = WHITE
            if is_dead: name_col = RED
            elif is_selected: name_col = GREEN
            
            # Nimi ja Level
            draw_text(f"{unit.name} (Lvl {getattr(unit, 'level', 1)})", font_main, name_col, screen, cx + 10, cy + 10)
            
            # Luokka
            u_class = unit.__class__.__name__
            draw_text(f"Class: {u_class}", font_small, (180, 180, 180), screen, cx + 10, cy + 35)
            
            # HP Palkki
            hp_pct = max(0, unit.current_hp / unit.max_hp)
            pygame.draw.rect(screen, (50, 0, 0), (cx + 10, cy + 60, 200, 8))
            pygame.draw.rect(screen, GREEN if not is_dead else RED, (cx + 10, cy + 60, 200 * hp_pct, 8))
            
            # Status
            if is_dead:
                draw_text("DEAD", font_small, RED, screen, cx + 230, cy + 35)
            elif is_selected:
                draw_text("READY", font_small, GREEN, screen, cx + 230, cy + 35)

            # Varusteet (Lyhyesti) - ase on equipment["main_hand"], ei unit.weapon
            weapon = unit.equipment.get("main_hand") if hasattr(unit, "equipment") else None
            w_name = getattr(weapon, "name", None) or "Fists"
            draw_text(f"W: {w_name}", font_small, (150, 150, 100), screen, cx + 150, cy + 12)

        # --- RIGHT SIDE: ENEMY TEAM ---
        enemy_x = SCREEN_WIDTH - 370
        draw_text("ENEMY TEAM", font_main, RED, screen, enemy_x, 110)
        
        enemy_roster = list(self.manager.enemy_team)
        
        if not enemy_roster:
            draw_text("Scouting...", font_main, (100, 100, 100), screen, enemy_x, 150)
        else:
            for i, unit in enumerate(enemy_roster):
                cx = enemy_x
                cy = start_y + i * gap_y
                
                # Viholliskortti
                draw_panel(screen, cx, cy, card_w, card_h, color=(40, 20, 20), border_color=RED)
                
                draw_text(f"{unit.name} (Lvl {getattr(unit, 'level', 1)})", font_main, RED, screen, cx + 10, cy + 10)
                
                # Luokka
                u_class = unit.__class__.__name__
                draw_text(f"Class: {u_class}", font_small, (200, 150, 150), screen, cx + 10, cy + 35)
                
                # Varusteet (Tärkeä! Pelaaja näkee mitä vihulla on)
                # Ase/panssari ovat equipmentissa, ei unit.weapon/unit.armor.
                eq = getattr(unit, "equipment", {})
                weapon = eq.get("main_hand")
                armor = eq.get("body")
                w_name = getattr(weapon, "name", None) or "Fists"
                a_name = getattr(armor, "name", None) or "None"
                
                draw_text(f"Weapon: {w_name}", font_small, (200, 200, 100), screen, cx + 10, cy + 55)
                draw_text(f"Armor: {a_name}", font_small, (180, 180, 200), screen, cx + 10, cy + 70)

        # --- VS TEXT ---
        draw_text("VS", font_title, (100, 100, 100), screen, SCREEN_WIDTH // 2 - 30, SCREEN_HEIGHT // 2 - 50)

        # Napit
        self.btn_fight.draw(screen)
        self.btn_back.draw(screen)
        
        # Validation msg
        if len(self.selected_units) != self.team_limit:
            msg = f"Select {self.team_limit} fighters!"
            draw_text(msg, font_small, RED, screen, SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT - 130)