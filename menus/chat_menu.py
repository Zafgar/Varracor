import pygame
import os
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import draw_panel, draw_text, UIButton, font_title, font_main, font_small
from sound_manager import sound_system

class ChatMenu(BaseMenu):
    def __init__(self, manager, npc_instance, context, return_state="hub"):
        super().__init__(manager)
        self.npc = npc_instance
        self.context = context
        self.return_state = return_state # Minne palataan kun dialogi loppuu

        # Haetaan data
        self.nodes = self.npc.get_nodes(self.context)
        start_id = self.npc.get_dialogue_root(self.context)
        self.current_node = self.nodes.get(start_id)

        # Typewriter tila
        self.displayed_text = ""
        self.char_index = 0
        self.timer = 0
        self.text_speed = 15 
        self.finished_typing = False

        self.portrait_image = None
        self.buttons = []

        # --- UI-MITAT (MUOKATTU) ---
        self.tb_w = 1150  # Text Box Width
        self.tb_h = 280   # Text Box Height
        self.tb_x = 30    # Text Box X (vasen reuna)
        self.tb_y = SCREEN_HEIGHT - self.tb_h - 20 
        
        # Alustetaan ensimmäinen node
        self.load_node_assets()
        self.process_enter_effects()
        self.record_history()

    def record_history(self):
        if not self.current_node: return
        npc_data = self.manager.npc_state.setdefault(self.npc.npc_id, {})
        if "history" not in npc_data:
            npc_data["history"] = []
        npc_data["history"].append(self.current_node.id)

    def load_node_assets(self):
        if not self.current_node: return
        
        self.displayed_text = ""
        self.char_index = 0
        self.finished_typing = False
        self.buttons = []

        # 1. KUVAN LATAUS
        loaded = False
        
        # A) Yritetään ladata tiedostosta (Prioriteetti 1: Bard, Mortarch yms.)
        path = self.npc.get_portrait_path(self.current_node.emotion)
        if path and os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                ow, oh = img.get_size()
                target_h = int(SCREEN_HEIGHT * 0.90)
                aspect_ratio = ow / oh
                target_w = int(target_h * aspect_ratio)
                self.portrait_image = pygame.transform.smoothscale(img, (target_w, target_h))
                loaded = True
            except Exception: pass

        # B) Jos ei tiedostoa, käytetään Unitin kuvaa (Prioriteetti 2: Recruits)
        if not loaded and hasattr(self.npc, "unit") and hasattr(self.npc.unit, "big_image") and self.npc.unit.big_image:
            img = self.npc.unit.big_image
            ow, oh = img.get_size()
            target_h = int(SCREEN_HEIGHT * 0.90)
            aspect_ratio = ow / oh
            target_w = int(target_h * aspect_ratio)
            
            self.portrait_image = pygame.transform.smoothscale(img, (target_w, target_h))
            loaded = True

        # C) Fallback
        if not loaded and not self.portrait_image:
             self.portrait_image = pygame.Surface((600, 800))
             self.portrait_image.fill((60, 40, 40))

        # 2. ÄÄNEN SOITTO (REAKTIO)
        if hasattr(self.npc, "get_voice_path"):
            voice_path = self.npc.get_voice_path(self.current_node.emotion)
            if voice_path and os.path.exists(voice_path):
                try:
                    sfx = pygame.mixer.Sound(voice_path)
                    sfx.set_volume(0.9) # Kovempi ääni
                    sfx.play()
                except Exception as e:
                    pass

    def process_enter_effects(self):
        if not self.current_node: return
        for eff in self.current_node.on_enter_effects:
            self.apply_effect(eff)

    def apply_effect(self, effect_str):
        """
        ÄLYKÄS EFEKTI-TULKKI
        Käsittelee komentoja muodossa "komento:arvo".
        """
        if not effect_str: return

        # 1. HAE DATAT
        npc_id = self.npc.npc_id
        npc_data = self.manager.npc_state.setdefault(npc_id, {"relationship": 0, "flags": {}, "history": []})
        global_data = self.manager.npc_state.setdefault("global", {"flags": {}, "reputation": 0})
        
        parts = effect_str.split(":")
        command = parts[0]
        value = parts[1] if len(parts) > 1 else None
        
        # --- PERUS KOMENNOT ---
        
        if command == "flag" and value:
            npc_data["flags"][value] = True

        elif command == "global_flag" and value:
            global_data["flags"][value] = True

        elif command == "rep" and value:
            try:
                amount = int(value)
                npc_data["relationship"] += amount
            except Exception: pass

        elif command == "fame" and value:
            try:
                amount = int(value)
                self.manager.reputation += amount
                global_data["reputation"] = self.manager.reputation
            except Exception: pass

        # --- QUEST KOMENNOT ---

        # "quest_unlock:hunt_01" -> Pakottaa tehtävän auki (Locked -> Available)
        elif command == "quest_unlock" and value:
            try:
                from quest_system import quest_manager
                # Tuki dict-muotoiselle quest-listalle
                quests_iter = quest_manager.quests.values() if isinstance(quest_manager.quests, dict) else quest_manager.quests
                for q in quests_iter:
                    # Tarkistetaan sekä uusi (.id) että vanha (.quest_id) tapa
                    qid = getattr(q, "id", getattr(q, "quest_id", None))
                    if qid == value:
                        q.unlocked = True
                        print(f"QUEST UNLOCKED: {q.title}")
            except ImportError:
                print("Error: Could not import quest_manager")

        # "accept_quest:hunt_01" -> Aloittaa tehtävän (Active)
        elif command == "accept_quest" and value:
            try:
                from quest_system import quest_manager
                quest_manager.accept_quest(value)
            except ImportError: pass

        # "finish_quest:hunt_01" -> Lunastaa palkinnot (Finished)
        elif command == "finish_quest" and value:
            try:
                from quest_system import quest_manager
                rewards = quest_manager.finish_quest(value)
                # BUGIKORJAUS: palkinnot jäivät aiemmin maksamatta
                # (finish_quest palauttaa ne, mutta paluuarvoa ei käytetty)
                if rewards:
                    gold = int(rewards.get("gold", 0))
                    if gold:
                        self.manager.gold += gold
                    rep = int(rewards.get("reputation", 0))
                    if rep:
                        quest_manager.add_reputation(rep)
                        self.manager.reputation = quest_manager.reputation
                    if gold or rep:
                        print(f"[Quest] Rewards paid: {gold} gold, {rep} reputation")
                        try:
                            from sound_manager import sound_system
                            sound_system.play_sound("coin")
                        except Exception:
                            pass
            except ImportError: pass
            
        # "clear_reaction" -> Nollaa NPC:n reaktion (esim. taistelun jälkeen)
        elif command == "clear_reaction":
            try:
                from quest_system import quest_manager
                quest_manager.clear_reaction()
            except ImportError: pass
            
        # --- RECRUITMENT ---
        elif command == "hire_unit" and value:
            # Palkkaa nykyinen NPC-yksikkö
            if hasattr(self.npc, "unit"):
                cost = int(value)
                if self.manager.hire_unit_by_reference(self.npc.unit, cost):
                    print(f"Hired {self.npc.unit.name} for {cost}")

        # --- BARD ---
        elif command == "pay_bard" and value:
            cost = int(value)
            if self.manager.gold >= cost:
                self.manager.gold -= cost
                # Käske Bardia soittamaan
                if hasattr(self.npc, "unit") and hasattr(self.npc.unit, "ai_controller"):
                    ai = self.npc.unit.ai_controller
                    if hasattr(ai, "request_performance"):
                        ai.request_performance(self.manager.current_arena.obstacles, self.manager)

        elif command == "hire_bard":
            # Palkkaa Bardin tiimiin
            if hasattr(self.npc, "unit"):
                # Lisää pelaajan tiimiin
                self.manager.my_team.add(self.npc.unit)
                # Merkitse palkatuksi
                npc_data = self.manager.npc_state.setdefault(self.npc.npc_id, {"flags": {}})
                npc_data["flags"]["is_hired"] = True
                print(f"Hired {self.npc.unit.name}!")

        # --- NAVIGOINTI ---
        elif command == "close_chat":
            self.next_state = self.return_state
            
        # --- MINIGAMES ---
        elif command == "start_minigame" and value:
            self.next_state = value

        # --- LEGACY TUKI ---
        elif effect_str == "set_flag_intro_done":
            npc_data["flags"]["intro_done"] = True
        elif effect_str == "rep_plus_5":
            npc_data["relationship"] += 500
        elif effect_str == "set_flag_griznak_intro_done":
            npc_data["flags"]["intro_done"] = True
            
        # --- FALLBACK: MANAGER ---
        else:
            # Jos ei tunnistettu täällä, annetaan managerin yrittää (esim. spawn_vortex)
            if hasattr(self.manager, "handle_dialogue_effect"):
                self.manager.handle_dialogue_effect(effect_str)

    def create_choice_buttons(self):
        self.buttons = []
        if not self.current_node: return

        valid_choices = [c for c in self.current_node.choices 
                         if c.condition is None or c.condition(self.context)]
        
        # Napit
        btn_w = 500
        btn_h = 45
        btn_gap = 10
        start_x = self.tb_x + self.tb_w - btn_w - 40
        start_y = self.tb_y + 60

        for i, choice in enumerate(valid_choices):
            y = start_y + (i * (btn_h + btn_gap))
            btn = UIButton(start_x, y, btn_w, btn_h, choice.text, None, WHITE, (50, 50, 70))
            btn.choice_data = choice
            self.buttons.append(btn)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
            if not self.finished_typing:
                self.finished_typing = True
                self.displayed_text = self.current_node.text
                self.create_choice_buttons()
                return

        if self.finished_typing:
            for btn in self.buttons:
                if btn.is_clicked(event):
                    try: sound_system.play_sound("click")
                    except Exception: pass
                    self.make_choice(btn.choice_data)
                    return

    def make_choice(self, choice_obj):
        for eff in choice_obj.effects:
            self.apply_effect(eff)
            if eff == "enter_league":
                self.next_state = "league"

        if self.next_state: return
        
        if choice_obj.next_node_id:
            self.current_node = self.nodes.get(choice_obj.next_node_id)
            self.load_node_assets()
            self.process_enter_effects()
            self.record_history()
        else:
            self.next_state = self.return_state

    def update(self):
        if not self.finished_typing and self.current_node:
            self.timer += 16
            if self.timer >= self.text_speed:
                self.timer = 0
                self.char_index += 1
                self.displayed_text = self.current_node.text[:self.char_index]
                if self.char_index >= len(self.current_node.text):
                    self.finished_typing = True
                    self.create_choice_buttons()
        
        mp = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.check_hover(mp)

    def draw(self, screen):
        # 1. Tumma tausta
        from ui_kit import get_fullscreen_overlay
        screen.blit(get_fullscreen_overlay((0, 0, 0, 180)), (0, 0))

        # 2. ISO MUOTOKUVA (Oikea ala)
        if self.portrait_image:
            img_x = SCREEN_WIDTH - self.portrait_image.get_width()
            img_y = SCREEN_HEIGHT - self.portrait_image.get_height()
            screen.blit(self.portrait_image, (img_x, img_y))

        # 3. TEKSTILAATIKKO
        draw_panel(screen, self.tb_x, self.tb_y, self.tb_w, self.tb_h)

        # 4. PUHUJAN NIMI
        if self.current_node:
            name_panel_w = 300
            name_panel_h = 50
            name_panel_x = self.tb_x
            name_panel_y = self.tb_y - name_panel_h + 5
            
            draw_panel(screen, name_panel_x, name_panel_y, name_panel_w, name_panel_h)
            draw_text(self.current_node.speaker, font_title, GOLD_COLOR, 
                      screen, name_panel_x + 20, name_panel_y + 10)

        # 5. TEKSTI
        text_max_w = self.tb_w - 600 
        lines = self.wrap_text(self.displayed_text, font_main, text_max_w)
        for i, line in enumerate(lines):
            draw_text(line, font_main, WHITE, screen, self.tb_x + 30, self.tb_y + 50 + (i * 35))

        # 6. NAPIT
        for btn in self.buttons:
            btn.draw(screen)

    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] < max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        return lines