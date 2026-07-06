import pygame
import math
import random
import os
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from menus.base_menu import BaseMenu
from ui_kit import UIButton, draw_text, font_title, font_main, font_small, GOLD_COLOR, WHITE, RED, GREEN, GRAY, draw_panel, format_money
from sound_manager import sound_system

# --- CONSTANTS ---
CARD_W, CARD_H = 100, 140
ASSET_PATH = "assets/tiles/gamling/"


class Card:
    def __init__(self, ctype, image):
        self.type = ctype # "CROWN", "COIN", "SWORD", "CHEAT", "LUCK"
        self.image = image
        self.rect = pygame.Rect(0, 0, CARD_W, CARD_H)
        self.is_duel_penalty = False # Jos True, Sword on paljastettu duelissa (-2 pistettä)

    def get_score(self):
        if self.type == "CROWN": return 2
        if self.type == "COIN": return 1
        if self.type == "SWORD":
            return -2 if self.is_duel_penalty else 0
        return 0

class CrownKnivesMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.bet_amount = 50
        
        # Betting State
        self.coin_values = {"silver": 10, "gold": 10000, "platinum": 10000000, "crown": 10000000000}
        
        # UI Rects for coin piles
        self.coin_rects = {}
        # Pot moved to the right
        self.pot_rect = pygame.Rect(SCREEN_WIDTH//2 + 400, SCREEN_HEIGHT//2 - 100, 300, 200)
        
        # Visual coins in pot [{"type": "gold", "x": 100, "y": 200, "owner": "player"}]
        self.visual_pot = []
        self.animating_coins = [] # For win animation
        self.held_coin = None # {"type": "gold", "from": "source"|"pot", "index": -1}
        self.payout_timer = 0
        self.coin_loop_channel = None
        
        # Staging counts (coins selected but not in pot)
        self.staging_counts = {"silver": 0, "gold": 0, "platinum": 0, "crown": 0}
        self.pot_counts = {"silver": 0, "gold": 0, "platinum": 0, "crown": 0}

        # Load Assets
        self.images = {}
        self._load_assets()
        
        # Game State
        self.deck = []
        self.p_hand = []
        self.ai_hand = []
        self.p_board = []
        self.ai_board = []
        self.discard_pile = []
        
        self.state = "BETTING" # BETTING, PLAYER_TURN, AI_TURN, DUEL, DUEL_SELECT, LUCK_SELECT, CHEAT_TARGET_SELECT, WIN_DECISION, DOUBLE_ANIMATION, PAYOUT, GAME_OVER
        self.last_turn_mode = False # Jos True, vastustaja lopetti ja meillä on 1 siirto
        
        self.p_stopped = False
        self.ai_stopped = False
        self.winner = None
        self.message = ""
        self.message_timer = 0
        
        # Duel vars
        self.duel_cards = [] # (p_card, ai_card)
        self.duel_timer = 0
        
        # Luck vars
        self.luck_options = [] # [Card, Card]
        
        # UI
        self.btn_play = UIButton(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 180, 200, 60, "PLAY CARD", None, GREEN)
        self.btn_stop = UIButton(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 230, 200, 60, "STOP (Hold)", None, RED)
        
        # Draw Pile (Deck) Rect - Vasemmalla
        self.deck_rect = pygame.Rect(350, SCREEN_HEIGHT // 2 - CARD_H // 2, CARD_W, CARD_H)

        # Game Over / Betting UI
        self.btn_leave = UIButton(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 100, 200, 60, "LEAVE TABLE", None, GRAY)
        self.btn_leave_bet = UIButton(30, 30, 160, 50, "LEAVE TABLE", None, GRAY)
        self.btn_again = UIButton(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 20, 200, 60, "PLAY AGAIN", None, GREEN)
        
        # Betting Buttons
        self.btn_deal = UIButton(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 180, 200, 60, "DEAL CARDS", None, GOLD_COLOR)
        self.btn_start = UIButton(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 30, 200, 60, "DEAL CARDS", None, GOLD_COLOR)
        self.btn_deal.enabled = False
        
        # Double or Nothing UI
        self.btn_collect = UIButton(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 250, 200, 60, "COLLECT", None, GREEN)
        self.current_winnings = 0
        self.double_streak = 0
        
        # Double Coin Physics
        self.double_coin_rect = pygame.Rect(0, 0, 80, 80)
        self.double_coin_pos = pygame.math.Vector2(0, 0)
        self.double_coin_vel = pygame.math.Vector2(0, 0)
        self.double_coin_state = "IDLE" # IDLE, DRAGGING, THROWN, BOUNCE, SPIN, RESULT
        self.spin_phase = "IDLE" # TOSS, SPIN
        self.coin_y = 0
        self.coin_vy = 0
        self.coin_scale_x = 1.0
        
        self.selected_card_idx = -1
        self.dragging_card_idx = None
        self.drag_offset = (0, 0)
        self.cheat_card_idx = -1
        
        # Voice Logic
        self.player_idle_timer = 0
        self.first_round = True
        self.current_voice_channel = None

    def _play_voice(self, key):
        """Soittaa puheen ja keskeyttää edellisen, jos se on vielä kesken."""
        if self.current_voice_channel and self.current_voice_channel.get_busy():
            self.current_voice_channel.stop()
        self.current_voice_channel = sound_system.play_sound(key)

    def on_enter(self):
        self._reset_to_betting()
        self._play_voice("ck_voice_greeting")

    def on_exit(self):
        if self.coin_loop_channel:
            self.coin_loop_channel.stop()
            self.coin_loop_channel = None

    def _load_assets(self):
        files = {
            "CROWN": "crown.png", "COIN": "coin.png", "SWORD": "sword.png",
            "CHEAT": "cheat.png", "LUCK": "luck.png", "BACK": "face.png",
            "TABLE": "table.png",
            "coin_silver": "coin_silver.png", "coin_gold": "coin_gold.png", "coin_platinum": "coin_platinum.png", "coin_crown": "coin_crown.png",
            "coin_crown_num": "coin_crown_num.png"
        }
        
        # Tarkistetaan polku (gamling vs gambling)
        load_path = ASSET_PATH
        if not os.path.exists(load_path):
            if os.path.exists("assets/tiles/gambling/"):
                load_path = "assets/tiles/gambling/"

        for key, fname in files.items():
            path = os.path.join(load_path, fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    if key == "TABLE":
                        self.images[key] = pygame.transform.smoothscale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    elif key.startswith("coin_"):
                        self.images[key] = pygame.transform.smoothscale(img, (64, 64)) # Coin size
                    else:
                        self.images[key] = pygame.transform.smoothscale(img, (CARD_W, CARD_H))
                    continue
                except: pass
            
            # Fallback surface (jos kuvaa ei löydy)
            if key == "TABLE":
                s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                s.fill((20, 40, 20))
            elif key.startswith("coin_") or key == "coin_crown_num":
                s = pygame.Surface((64, 64), pygame.SRCALPHA)
                pygame.draw.circle(s, GOLD_COLOR, (32, 32), 30)
            else:
                s = pygame.Surface((CARD_W, CARD_H))
                s.fill((100, 100, 100))
                pygame.draw.rect(s, WHITE, (0,0,CARD_W,CARD_H), 2)
            self.images[key] = s

    def _reset_to_betting(self):
        self.state = "BETTING"
        self.message = "Place your bet"
        self.p_hand = []
        self.ai_hand = []
        self.p_board = []
        self.ai_board = []
        self.winner = None
        self.dragging_card_idx = None
        self.staging_counts = {"silver": 0, "gold": 0, "platinum": 0, "crown": 0}
        self.pot_counts = {"silver": 0, "gold": 0, "platinum": 0, "crown": 0}
        self.bet_amount = 0
        self.visual_pot = []
        self.animating_coins = []
        self.held_coin = None
        self.p_duel_card = None
        self.ai_duel_card = None
        self.turn_delay_timer = 0
        self.p_score_mod = 0
        self.ai_score_mod = 0
        if self.coin_loop_channel:
            self.coin_loop_channel.stop()
            self.coin_loop_channel = None
        self.current_winnings = 0
        self.double_streak = 0
        self.double_coin_state = "IDLE"
        self.double_coin_pos = pygame.math.Vector2(0, 0)
        self.double_coin_vel = pygame.math.Vector2(0, 0)
        self.spin_timer = 0
        
        if not self.first_round:
            self._play_voice("ck_voice_betting")

    def _start_round(self):
        # Subtract gold
        # AI matches bet visually
        for c_type, count in self.pot_counts.items():
            # Add visual coins for AI
            # Limit visual coins to avoid lag if count is huge
            visual_count = min(count, 20) 
            for _ in range(visual_count):
                offset_x = random.randint(0, 100)
                offset_y = random.randint(0, 50)
                self.visual_pot.append({
                    "type": c_type,
                    "x": self.pot_rect.x + 20 + offset_x,
                    "y": self.pot_rect.y + 20 + offset_y,
                    "owner": "npc"
                })
        
        # Update pot counts to reflect total (Player + AI)
        for c_type in self.pot_counts:
            self.pot_counts[c_type] *= 2

        self.first_round = False
        self._play_voice("ck_voice_start_round")

        self.manager.gold -= self.bet_amount
        
        # Create Deck (24 cards)
        self.deck = []
        counts = {"CROWN": 6, "COIN": 8, "SWORD": 6, "CHEAT": 2, "LUCK": 2}
        for ctype, count in counts.items():
            for _ in range(count):
                self.deck.append(Card(ctype, self.images[ctype]))
        
        random.shuffle(self.deck)
        
        self.p_hand = [self.deck.pop(), self.deck.pop()]
        self.ai_hand = [self.deck.pop(), self.deck.pop()]
        self.p_board = []
        self.ai_board = []
        self.discard_pile = []
        
        self.p_stopped = False
        self.ai_stopped = False
        self.last_turn_mode = False
        self.state = "PLAYER_TURN"
        self.message = "Your Turn"
        self.selected_card_idx = -1
        self.winner = None
        self.dragging_card_idx = None
        self.cheat_card_idx = -1
        self.turn_delay_timer = 0

    def get_score(self, board, bonus=0):
        total = sum(c.get_score() for c in board) + bonus
        return max(0, total) # Pisteet eivät voi olla negatiivisia

    def count_swords_total(self):
        # Lasketaan vain aktiiviset miekat (ei duel-rangaistuksia)
        p_swords = sum(1 for c in self.p_board if c.type == "SWORD" and not c.is_duel_penalty)
        ai_swords = sum(1 for c in self.ai_board if c.type == "SWORD" and not c.is_duel_penalty)
        return p_swords + ai_swords

    def _transform_sword_to_coin(self, target_card):
        target_card.type = "COIN"
        target_card.image = self.images["COIN"]
        
        # VFX
        cx, cy = target_card.rect.center
        self.manager.vfx.create_impact_sparks(cx, cy, color=GOLD_COLOR, count=10)
        self.manager.vfx.show_damage(cx, cy - 40, "CHEAT!", color=GOLD_COLOR)
        sound_system.play_sound("magic_fail")

    def _handle_cheat_selection(self, pos):
        # Check Player Board
        for c in self.p_board:
            if c.type == "SWORD" and not c.is_duel_penalty and c.rect.collidepoint(pos):
                self._transform_sword_to_coin(c)
                self._finalize_cheat_play()
                return

        # Check AI Board
        for c in self.ai_board:
            if c.type == "SWORD" and not c.is_duel_penalty and c.rect.collidepoint(pos):
                self._transform_sword_to_coin(c)
                self._finalize_cheat_play()
                return

    def _finalize_cheat_play(self):
        card = self.p_hand.pop(self.cheat_card_idx)
        self.discard_pile.append(card)
        self.state = "PLAYER_TURN"
        self._play_voice("ck_voice_cheat")
        self._end_turn()

    def handle_event(self, event):
        if self.state == "BETTING":
            if self.btn_leave_bet.is_clicked(event):
                self.next_state = "tavern_sunk_cask"
                return
            
            if self.bet_amount > 0 and self.btn_start.is_clicked(event):
                sound_system.play_sound("ck_shuffle")
                self._start_round()
                return
            
            # --- DRAG & DROP BETTING ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                # 1. Check Source Piles (Add to Staging)
                for c_type, rect in self.coin_rects.items():
                    if rect.collidepoint(mx, my):
                        val = self.coin_values[c_type]
                        # Cost of 1 coin
                        cost = val
                        current_staged_cost = sum(self.staging_counts[k] * self.coin_values[k] for k in self.staging_counts)
                        total_potential_bet = self.bet_amount + current_staged_cost + cost
                        
                        if event.button == 1: # LMB Add 1
                            if self.staging_counts[c_type] < 10: # Max stack 10
                                if self.manager.gold >= total_potential_bet:
                                    self.staging_counts[c_type] += 1
                                    sound_system.play_sound("ck_coin_draw")
                                else:
                                    sound_system.play_sound("error")
                        elif event.button == 3: # RMB Remove 1
                            if self.staging_counts[c_type] > 0:
                                self.staging_counts[c_type] -= 1
                                sound_system.play_sound("ck_coin_draw")
                        return

                # 2. Check Staging Piles (Drag to Pot)
                for c_type, rect in self.coin_rects.items():
                    # Staging area is above the source rect
                    staging_rect = pygame.Rect(rect.x, rect.y - 120, rect.width, 120)
                    if staging_rect.collidepoint(mx, my) and self.staging_counts[c_type] > 0:
                        self.held_coin = {
                            "type": c_type,
                            "count": self.staging_counts[c_type],
                            "from": "staging"
                        }
                        self.staging_counts[c_type] = 0 # Temp remove
                        sound_system.play_sound("ck_coin_draw")
                        return

                # 3. Check Pot (Drag out)
                for i in range(len(self.visual_pot) - 1, -1, -1):
                    c = self.visual_pot[i]
                    if c["owner"] == "player":
                        r = pygame.Rect(c["x"], c["y"], 64, 64)
                        if r.collidepoint(mx, my):
                            c_type = c["type"]
                            self.visual_pot.pop(i)
                            self.pot_counts[c_type] -= 1
                            self.bet_amount -= self.coin_values[c_type]
                            
                            self.held_coin = {
                                "type": c_type,
                                "count": 1,
                                "from": "pot"
                            }
                            sound_system.play_sound("ck_coin_draw")
                            return

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.held_coin:
                    mx, my = event.pos
                    c_type = self.held_coin["type"]
                    count = self.held_coin["count"]

                    # If dropped in Pot Area
                    if self.pot_rect.collidepoint(mx, my):
                        # Add to pot
                        self.pot_counts[c_type] += count
                        self.bet_amount += count * self.coin_values[c_type]
                        
                        # Add visual coin for player
                        # Limit visual coins to avoid clutter if stack is huge
                        vis_count = min(count, 20)
                        for _ in range(vis_count):
                            offset_x = random.randint(0, 200)
                            offset_y = random.randint(0, 100)
                            self.visual_pot.append({
                                "type": c_type,
                                "x": self.pot_rect.x + 20 + offset_x,
                                "y": self.pot_rect.y + 50 + offset_y,
                                "owner": "player"
                            })
                        sound_system.play_sound("ck_coin_place")
                    
                    else:
                        # Dropped outside (Return to staging)
                        if self.held_coin["from"] == "pot":
                             # Refunded (already removed from pot counts in MOUSEDOWN)
                             sound_system.play_sound("ck_coin_place")
                        else:
                             self.staging_counts[c_type] += count
                             sound_system.play_sound("ck_coin_place")

                    self.held_coin = None
            return

        if self.state == "WIN_DECISION":
            if self.btn_collect.is_clicked(event):
                self._start_payout_animation(win=True)
                sound_system.play_sound("coin")
            
            # Coin Dragging Logic
            if self.double_streak < 3:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.double_coin_rect.collidepoint(event.pos):
                        self.double_coin_state = "DRAGGING"
                        self.double_coin_vel = pygame.math.Vector2(0, 0)
                
                elif event.type == pygame.MOUSEMOTION:
                    if self.double_coin_state == "DRAGGING":
                        self.double_coin_pos = pygame.math.Vector2(event.pos)
                        self.double_coin_rect.center = event.pos
                        self.double_coin_vel = pygame.math.Vector2(event.rel)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.double_coin_state == "DRAGGING":
                        if self.double_coin_vel.y < -5: # Thrown upwards
                            self.state = "DOUBLE_ANIMATION"
                            self.double_coin_state = "THROWN"
                        else:
                            self._reset_double_coin_pos()

            return

        if self.state == "GAME_OVER":
            if self.btn_leave.is_clicked(event):
                self.next_state = "tavern_sunk_cask"
            elif self.btn_again.is_clicked(event):
                self._reset_to_betting()
                sound_system.play_sound("click")
            return

        if self.state == "LUCK_SELECT":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                cx = SCREEN_WIDTH // 2
                cy = SCREEN_HEIGHT // 2
                
                # Check luck options
                for i, card in enumerate(self.luck_options):
                    rect = pygame.Rect(cx - 120 + i*140, cy - 70, CARD_W, CARD_H)
                    if rect.collidepoint(mx, my):
                        # Keep this card
                        self.p_hand.append(card)
                        sound_system.play_sound("ck_draw")
                        
                        # Put other at bottom of deck (if exists)
                        if len(self.luck_options) > 1:
                            other = self.luck_options[1-i]
                            self.deck.insert(0, other) # Insert at 0 (bottom)
                        
                        self.luck_options = []
                        self.state = "PLAYER_TURN"
                        self._end_turn()
                        return
            return

        if self.state == "DUEL_SELECT":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                start_x = SCREEN_WIDTH // 2 - (len(self.p_hand) * 60)
                for i, card in enumerate(self.p_hand):
                    rect = pygame.Rect(start_x + i * 120, SCREEN_HEIGHT - 160, CARD_W, CARD_H)
                    if rect.collidepoint(mx, my):
                        self.p_duel_card = self.p_hand.pop(i)
                        sound_system.play_sound("click")
                        self._start_duel_animation()
                        return
            return

        if self.state == "CHEAT_TARGET_SELECT":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_cheat_selection(event.pos)
                elif event.button == 3: # Right click cancel
                    self.state = "PLAYER_TURN"
                    self.message = "Your Turn"
                    self.cheat_card_idx = -1
                    sound_system.play_sound("click")
            return

        if self.state == "PLAYER_TURN" and not self.p_stopped:
            # Reset idle timer on interaction
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.player_idle_timer = 0

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    
                    # Hand Selection / Drag Start
                    start_x = SCREEN_WIDTH // 2 - (len(self.p_hand) * 60)
                    for i, card in enumerate(self.p_hand):
                        rect = pygame.Rect(start_x + i * 120, SCREEN_HEIGHT - 160, CARD_W, CARD_H)
                        if rect.collidepoint(mx, my):
                            self.selected_card_idx = i
                            self.dragging_card_idx = i
                            self.drag_offset = (rect.x - mx, rect.y - my)
                            sound_system.play_sound("click")
                            return

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.dragging_card_idx is not None:
                    mx, my = pygame.mouse.get_pos()
                    # Drop zone: Above the hand area (e.g. y < SCREEN_HEIGHT - 200)
                    if my < SCREEN_HEIGHT - 200:
                        if self.dragging_card_idx < len(self.p_hand):
                            self._play_card("PLAYER", self.dragging_card_idx)
                    self.dragging_card_idx = None
            
            # Actions (Release)
            if event.type == pygame.MOUSEBUTTONUP:
                if self.btn_play.is_clicked(event):
                    if self.selected_card_idx >= 0 and self.selected_card_idx < len(self.p_hand):
                        self._play_card("PLAYER", self.selected_card_idx)
                
                elif self.deck_rect.collidepoint(event.pos):
                    if len(self.p_hand) < 4:
                        self._draw_card("PLAYER")
                    else:
                        self.message = "Hand Full (Max 4)!"
                        
                elif self.btn_stop.is_clicked(event):
                    self._stop_playing("PLAYER")

    def _play_card(self, who, card_idx):
        # --- PLAYER CHEAT INTERCEPTION ---
        if who == "PLAYER":
            card = self.p_hand[card_idx]
            if card.type == "CHEAT":
                if self.count_swords_total() > 0:
                    self.state = "CHEAT_TARGET_SELECT"
                    self.cheat_card_idx = card_idx
                    self.message = "Select a Sword to convert"
                    return
                else:
                    self.message = "No Swords to Cheat!"
                    sound_system.play_sound("error")
                    return

        hand = self.p_hand if who == "PLAYER" else self.ai_hand
        board = self.p_board if who == "PLAYER" else self.ai_board
        
        card = hand.pop(card_idx)
        self.selected_card_idx = -1
        
        # --- VFX ---
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        
        # Calculate card position for VFX
        idx = len(board) - 1
        mat_x = (SCREEN_WIDTH - 800) // 2
        x = mat_x + 20 + idx * 110 + CARD_W // 2
        
        if who == "PLAYER":
            y = cy + 50 + CARD_H // 2
            self.manager.vfx.create_impact_sparks(x, y, color=GOLD_COLOR)
            score = card.get_score()
            if score != 0:
                col = GREEN if score > 0 else RED
                txt = f"+{score}" if score > 0 else f"{score}"
                self.manager.vfx.show_damage(x, y - 60, txt, color=col)
        else:
            y = cy - 200 + CARD_H // 2
            self.manager.vfx.create_impact_sparks(x, y, color=(200, 50, 50))

        # --- SPECIAL EFFECTS ---
        if card.type == "CHEAT":
            # AI Logic for CHEAT (Player handled above)
            if who == "AI":
                target_card = None
                # Prioritize own swords (Score +1)
                for c in self.ai_board:
                    if c.type == "SWORD" and not c.is_duel_penalty: target_card = c; break
                
                # Fallback to enemy swords (Prevent duel)
                if not target_card:
                    for c in self.p_board:
                        if c.type == "SWORD" and not c.is_duel_penalty: target_card = c; break
                
                if target_card:
                    self._transform_sword_to_coin(target_card)
                    self.message = "Dealer used Cheat!"
                
                self.discard_pile.append(card)

        elif card.type == "LUCK":
            self.discard_pile.append(card) # LUCK card goes to discard immediately
            sound_system.play_sound("ck_place")
            sound_system.play_sound("ck_draw")
            # Draw 2, Keep 1, Bottom 1
            c1 = self.deck.pop() if self.deck else None
            c2 = self.deck.pop() if self.deck else None
            
            cards = [c for c in [c1, c2] if c]
            
            if who == "PLAYER":
                if cards:
                    self.luck_options = cards
                    self.state = "LUCK_SELECT"
                    return # Wait for input
            else:
                if not cards:
                    self.message = "Deck Empty! Dealer wasted Luck."
                    
                # AI Logic: Keep highest value
                if cards:
                    cards.sort(key=lambda c: c.get_score(), reverse=True)
                    keep = cards[0]
                    self.ai_hand.append(keep)
                    if len(cards) > 1: 
                        self.deck.insert(0, cards[1]) # Bottom
                    self.message = "Dealer used Luck."
                    self._play_voice("ck_voice_luck")
        
        else:
            # Normal card (Crown, Coin, Sword)
            board.append(card)
            sound_system.play_sound("ck_place")
            
            if card.type == "SWORD":
                if random.random() < 0.4:
                    self._play_voice("ck_voice_sword")

        # Check Duel
        if self.count_swords_total() >= 2:
            self._setup_duel()
            return

        # Jos pelattiin erikoiskortti, lisätään viive jotta pelaaja ehtii reagoida
        if card.type in ["CHEAT", "LUCK"]:
            self.turn_delay_timer = 120 # 2 sekunnin viive
            return

        self._end_turn()

    def _draw_card(self, who):
        hand = self.p_hand if who == "PLAYER" else self.ai_hand
        if self.deck:
            hand.append(self.deck.pop())
            sound_system.play_sound("ck_draw")
            if who == "PLAYER" and random.random() < 0.3:
                self._play_voice("ck_voice_player_draw")
            self._end_turn()
        else:
            self.message = "Deck Empty!"

    def _stop_playing(self, who):
        board = self.p_board if who == "PLAYER" else self.ai_board
        bonus = self.p_score_mod if who == "PLAYER" else self.ai_score_mod
        score = self.get_score(board, bonus)
        
        # Rule: If stop < 8 -> Immediate Loss
        if score < 8:
            self.winner = "AI" if who == "PLAYER" else "PLAYER"
            self.message = f"{who} stopped too early! ({score} < 8)"
            if who == "PLAYER":
                self._play_voice("ck_voice_stop_early")
            self._game_over()
            return

        if who == "PLAYER":
            self.p_stopped = True
            self.message = "Player Stopped."
            self._play_voice("ck_voice_player_stop")
        else:
            self.ai_stopped = True
            self.message = "Dealer Stopped."
            self._play_voice("ck_voice_dealer_stop")
            
        # Rule: Opponent gets ONE last action
        self.last_turn_mode = True
        self._end_turn()

    def _setup_duel(self):
        # AI Selection (Automatic)
        if self.ai_hand:
            self.ai_duel_card = self.ai_hand.pop(random.randint(0, len(self.ai_hand)-1))
        elif self.deck:
            self.ai_duel_card = self.deck.pop()
        else:
            self.ai_duel_card = None

        # Player Selection
        if self.p_hand:
            self.state = "DUEL_SELECT"
            self.message = "DUEL! Select a card to fight!"
        else:
            # Auto-pick from deck if hand empty
            if self.deck:
                self.p_duel_card = self.deck.pop()
            else:
                self.p_duel_card = None
            self._start_duel_animation()

    def _start_duel_animation(self):
        self.duel_cards = [self.p_duel_card, self.ai_duel_card]
        self.state = "DUEL"
        self.duel_timer = 180
        sound_system.play_sound("ck_swords")
        self._play_voice("ck_voice_duel")
        
        # VFX
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        self.manager.vfx.create_shockwave(cx, cy + CARD_H//2, color=RED)
        self.manager.vfx.create_impact_sparks(cx, cy + CARD_H//2, color=WHITE, count=15)

    def _resolve_duel(self):
        p_card, ai_card = self.duel_cards
        
        # 1. Calculate points from revealed cards (SHOW ONLY)
        def calc_duel_points(card):
            if not card: return 0
            if card.type == "CROWN": return 2
            if card.type == "COIN": return 1
            if card.type == "SWORD": return -2
            return 0

        p_val = calc_duel_points(p_card)
        ai_val = calc_duel_points(ai_card)
        
        self.p_score_mod += p_val
        self.ai_score_mod += ai_val
        
        # VFX for points
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        if p_val != 0:
            col = GREEN if p_val > 0 else RED
            self.manager.vfx.show_damage(cx - 100, cy + 50, f"{'+' if p_val > 0 else ''}{p_val}", color=col)
        if ai_val != 0:
            col = GREEN if ai_val > 0 else RED
            self.manager.vfx.show_damage(cx + 100, cy - 50, f"{'+' if ai_val > 0 else ''}{ai_val}", color=col)

        # 2. Return cards to hand (They do NOT go to board)
        if p_card:
            self.p_hand.append(p_card)
        if ai_card:
            self.ai_hand.append(ai_card)
        
        # 3. Remove the swords that triggered the duel (Clean the table)
        # "ne 2 miekkaa, jotka olivat pöydässä ... poistetaan"
        for c in self.p_board[:]:
            if c.type == "SWORD" and not c.is_duel_penalty:
                self.p_board.remove(c)
                self.discard_pile.append(c)
                
        for c in self.ai_board[:]:
            if c.type == "SWORD" and not c.is_duel_penalty:
                self.ai_board.remove(c)
                self.discard_pile.append(c)
        
        self.duel_cards = []
        
        # Resume turn
        self.state = "PLAYER_TURN" if not self.p_stopped else "AI_TURN"
        self._end_turn()

    def _end_turn(self):
        if self.winner: return

        # Check if game over (Both stopped or Last Turn used)
        if self.p_stopped and self.ai_stopped:
            self._calculate_winner()
            return
            
        # Switch turn
        if self.state == "PLAYER_TURN":
            if self.last_turn_mode and self.ai_stopped:
                # Player just took their last action
                self._calculate_winner()
                return
                
            if not self.ai_stopped:
                self.state = "AI_TURN"
                self.message_timer = 60 # AI thinks
            else:
                # AI stopped, Player continues (Last Turn Mode)
                self.state = "PLAYER_TURN"
                
        elif self.state == "AI_TURN":
            if self.last_turn_mode and self.p_stopped:
                # AI just took their last action
                self._calculate_winner()
                return

            if not self.p_stopped:
                self.state = "PLAYER_TURN"
            else:
                # Player stopped, AI continues (Last Turn Mode)
                self.state = "AI_TURN"
                self.message_timer = 60

    def update(self):
        if self.state == "DUEL":
            self.duel_timer -= 1
            if self.duel_timer <= 0:
                self._resolve_duel()
            return
        
        self.manager.vfx.update()

        # Viive erikoiskorttien jälkeen
        if self.turn_delay_timer > 0:
            self.turn_delay_timer -= 1
            if self.turn_delay_timer <= 0:
                self._end_turn()
            return

        if self.state == "DOUBLE_ANIMATION":
            self._update_double_animation()
            return

        if self.state == "PLAYER_TURN":
            self.player_idle_timer += 1
            if self.player_idle_timer == 600: # 10s
                self._play_voice("ck_voice_player_idle")
        else:
            self.player_idle_timer = 0

        if self.state == "AI_TURN":
            self.message_timer -= 1
            if self.message_timer <= 0:
                self._ai_logic()

    def _ai_logic(self):
        ai_score = self.get_score(self.ai_board, self.ai_score_mod)
        p_score = self.get_score(self.p_board, self.p_score_mod)
        
        # 1. Stop condition
        if ai_score >= 8:
            # If we are winning, stop
            if ai_score > p_score:
                self._stop_playing("AI")
                return
            # If tied, Dealer wins, so stop
            if ai_score == p_score:
                self._stop_playing("AI")
                return
            
            # If this is the LAST TURN (Player stopped), we MUST beat player now.
            if self.p_stopped:
                # If we are losing, we must play/draw.
                # If we are winning, stop.
                pass 
            else:
                # Normal play. If we have a good score (e.g. 12+), stop.
                if ai_score >= 12:
                    self._stop_playing("AI")
                    return

        # 2. Play Crown/Coin/Cheat/Luck
        for i, c in enumerate(self.ai_hand):
            if c.type == "CHEAT":
                # Check targets (Own sword for profit, Enemy sword for defense)
                has_own_sword = any(card.type == "SWORD" and not card.is_duel_penalty for card in self.ai_board)
                has_enemy_sword = any(card.type == "SWORD" and not card.is_duel_penalty for card in self.p_board)
                
                if has_own_sword or has_enemy_sword:
                    self._play_card("AI", i)
                    return
            elif c.type in ["CROWN", "COIN", "LUCK"]:
                self._play_card("AI", i)
                return
        
        # 3. Play Sword (Only if it triggers duel or desperate)
        swords_on_board = self.count_swords_total()
        has_good_duel_card = any(c.type in ["CROWN", "COIN"] for c in self.ai_hand)
        
        for i, c in enumerate(self.ai_hand):
            if c.type == "SWORD":
                if swords_on_board >= 1: # Will trigger duel
                    # Duel if we have a good card to win it, OR if we are losing and need chaos
                    if has_good_duel_card or (self.p_stopped and ai_score < p_score):
                        self._play_card("AI", i)
                        return
        
        # 4. Draw
        if len(self.ai_hand) < 4:
            self._draw_card("AI")
        else:
            # Hand full, must play something (Sword)
            self._play_card("AI", 0)

    def _calculate_winner(self):
        p_score = self.get_score(self.p_board, self.p_score_mod)
        ai_score = self.get_score(self.ai_board, self.ai_score_mod)
        
        # Rule: < 8 is loss. (Already checked on Stop, but check again for safety)
        if p_score < 8: 
            self.winner = "AI"
            self.message = "Player failed to reach 8!"
        elif ai_score < 8:
            self.winner = "PLAYER"
            self.message = "Dealer failed to reach 8!"
        else:
            if p_score > ai_score:
                self.winner = "PLAYER"
            elif ai_score > p_score:
                self.winner = "AI"
            else:
                # Tie -> Crowns
                p_crowns = sum(1 for c in self.p_board if c.type == "CROWN")
                ai_crowns = sum(1 for c in self.ai_board if c.type == "CROWN")
                if p_crowns > ai_crowns: self.winner = "PLAYER"
                elif ai_crowns > p_crowns: self.winner = "AI"
                else: self.winner = "AI" # Dealer wins absolute ties
        
        self._game_over()
        
    def _game_over(self):
        if self.winner == "PLAYER":
            win_amt = self.bet_amount * 2
            self.current_winnings = win_amt
            self.double_streak = 0
            
            self.message = f"VICTORY! Won {format_money(win_amt)}."
            sound_system.play_sound("ck_victory")
            self._play_voice("ck_voice_player_win")
            cx = SCREEN_WIDTH // 2
            cy = SCREEN_HEIGHT // 2
            self.manager.vfx.create_fireburst(cx, cy)
            
            # Go to decision instead of payout
            self.state = "WIN_DECISION"
            self._reset_double_coin_pos()
        else:
            self.message = "DEFEAT! House wins."
            sound_system.play_sound("error")
            self._play_voice("ck_voice_dealer_win")
            self._start_payout_animation(win=False)

    def _reset_double_coin_pos(self):
        self.double_coin_state = "IDLE"
        self.double_coin_pos = pygame.math.Vector2(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50)
        self.double_coin_rect.center = (int(self.double_coin_pos.x), int(self.double_coin_pos.y))
        self.double_coin_vel = pygame.math.Vector2(0, 0)

    def _update_double_animation(self):
        # Physics constants
        gravity = 0.8
        table_y = SCREEN_HEIGHT // 2 + 100
        
        if self.double_coin_state in ["THROWN", "BOUNCE"]:
            self.double_coin_pos += self.double_coin_vel
            self.double_coin_vel.y += gravity
            
            # Wall Bounce
            radius = 40 # Coin is 80x80
            if self.double_coin_pos.x < radius:
                self.double_coin_pos.x = radius
                self.double_coin_vel.x *= -0.7 # Lose some energy
            elif self.double_coin_pos.x > SCREEN_WIDTH - radius:
                self.double_coin_pos.x = SCREEN_WIDTH - radius
                self.double_coin_vel.x *= -0.7

            # Hit Table
            if self.double_coin_pos.y >= table_y:
                self.double_coin_pos.y = table_y
                
                if self.double_coin_state == "THROWN":
                    # First bounce
                    self.double_coin_state = "BOUNCE"
                    self.double_coin_vel.y = -self.double_coin_vel.y * 0.6 # Dampened bounce
                    self.double_coin_vel.x *= 0.8
                    sound_system.play_sound("ck_coin_place")
                elif self.double_coin_state == "BOUNCE":
                    # Second hit -> Start Spin
                    self.double_coin_state = "SPIN"
                    self.spin_timer = 240 # 4 seconds
                    sound_system.play_sound("ck_double_spin")

        elif self.double_coin_state == "SPIN":
            self.spin_timer -= 1
            if self.spin_timer <= 0:
                # Result
                is_win = random.choice([True, False])
                self.double_coin_state = "RESULT"
                self.spin_timer = 120 # 2 seconds pause
                self.double_result = is_win
                
                if is_win:
                    self.current_winnings *= 2
                    self.double_streak += 1
                    self.message = f"DOUBLED! Total: {format_money(self.current_winnings)}"
                    sound_system.play_sound("ck_victory")
                    self.manager.vfx.create_fireburst(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
                else:
                    self.current_winnings = 0
                    self.message = "LOST IT ALL!"
                    sound_system.play_sound("error")

        elif self.double_coin_state == "RESULT":
            self.spin_timer -= 1
            if self.spin_timer <= 0:
                if self.double_result:
                    if self.double_streak >= 3:
                        self._start_payout_animation(win=True)
                    else:
                        self.state = "WIN_DECISION"
                        self._reset_double_coin_pos()
                else:
                    self.winner = "AI"
                    self.state = "GAME_OVER"
                    self.visual_pot = []
            
    def _start_payout_animation(self, win):
        self.state = "PAYOUT"
        self.payout_timer = 0
        self.animating_coins = []
        
        target_y = SCREEN_HEIGHT + 50 # Player wins -> bottom
        if self.winner != "PLAYER":
            target_y = -50 # Dealer wins -> top
            
        # If player won (and collected), add gold now
        if win:
            self.manager.gold += self.current_winnings

        # Calculate delay spread based on coin count (More coins = longer animation)
        coin_count = len(self.visual_pot)
        max_delay = max(30, coin_count * 4) # Min 0.5s, scales with count
        
        for i, c in enumerate(self.visual_pot):
            self.animating_coins.append({
                "type": c["type"],
                "x": c["x"],
                "y": c["y"],
                "tx": c["x"], # Keep X roughly same
                "ty": target_y,
                "speed": random.uniform(15, 25),
                "delay": random.randint(0, max_delay)
            })
        self.visual_pot = [] # Clear static pot
        
        # Start loop sound
        if self.animating_coins:
             self.coin_loop_channel = sound_system.play_sound("ck_coin_taking", loops=-1)

    def draw(self, screen):
        # Background
        screen.fill((20, 40, 20)) # Varmistetaan että ruutu tyhjenee
        if "TABLE" in self.images:
            screen.blit(self.images["TABLE"], (0,0))

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # --- BETTING SCREEN ---
        # Draw Betting UI elements even if game is running (pot visible)
        
        # --- POT AREA ---
        # Draw pot background
        pygame.draw.rect(screen, (0, 0, 0, 50), self.pot_rect, border_radius=20)
        pygame.draw.rect(screen, (100, 80, 40), self.pot_rect, 2, border_radius=20)
        
        # Pot Text (Counts)
        pot_str = f"{self.pot_counts['silver']} SL  {self.pot_counts['gold']} GP  {self.pot_counts['platinum']} PL  {self.pot_counts['crown']} CR"
        draw_text("POT CONTENTS:", font_small, GOLD_COLOR, screen, self.pot_rect.x + 20, self.pot_rect.top - 40)
        draw_text(pot_str, font_main, WHITE, screen, self.pot_rect.x + 20, self.pot_rect.top - 15)
        
        # draw_text(f"POT: {self.bet_amount * 2}", font_main, GOLD_COLOR, screen, self.pot_rect.centerx - 40, self.pot_rect.top - 30)
        
        # Draw Coins in Pot
        for c in self.visual_pot:
            img = self.images.get(f"coin_{c['type']}")
            if img:
                screen.blit(img, (c["x"], c["y"]))

        # --- PAYOUT ANIMATION ---
        if self.state == "PAYOUT":
            self.payout_timer += 1
            all_done = True
            for c in self.animating_coins:
                if c["delay"] > 0:
                    c["delay"] -= 1
                    all_done = False
                    continue
                
                # Move
                dy = c["ty"] - c["y"]
                if abs(dy) > c["speed"]:
                    c["y"] += c["speed"] * (1 if dy > 0 else -1)
                    all_done = False
                else:
                    # Arrived (play sound once)
                    if not c.get("landed"):
                        c["landed"] = True
                        # sound_system.play_sound("coin", volume=0.3) # Loop replaces individual ticks
                
                img = self.images.get(f"coin_{c['type']}")
                if img: screen.blit(img, (c["x"], c["y"]))
            
            if all_done and self.payout_timer > 60:
                if self.coin_loop_channel:
                    self.coin_loop_channel.stop()
                    self.coin_loop_channel = None
                self.state = "GAME_OVER"

        # --- SOURCE PILES (Bottom Right) ---
        # Only visible during betting
        if self.state == "BETTING":
            # Define positions (Bottom Right)
            start_x = SCREEN_WIDTH - 450
            pile_y = SCREEN_HEIGHT - 100
            gap = 100
            
            coin_types = ["silver", "gold", "platinum", "crown"]
            current_staged_cost = sum(self.staging_counts[k] * self.coin_values[k] for k in self.staging_counts)
            current_funds = self.manager.gold - self.bet_amount - current_staged_cost
            
            for i, c_type in enumerate(coin_types):
                x = start_x + i * gap
                rect = pygame.Rect(x, pile_y, 64, 64)
                self.coin_rects[c_type] = rect
                
                # Draw base coin
                img = self.images.get(f"coin_{c_type}")
                if img:
                    screen.blit(img, rect)
                
                # Draw Count available
                # val = self.coin_values[c_type]
                # count = current_funds // val
                # col = WHITE if count > 0 else (100, 100, 100)
                # draw_text(f"{count}", font_small, col, screen, x + 10, pile_y + 70)
                
                # Draw Staging Stack
                staged = self.staging_counts[c_type]
                if staged > 0:
                    stack_x = x
                    stack_base_y = pile_y - 80
                    # Visual stack limit
                    vis_stack = min(staged // 10 + 1, 10) # 1 coin per 10 count visually? Or just stack
                    vis_stack = min(staged, 10)

                    for j in range(vis_stack):
                        offset_y = j * 5
                        screen.blit(img, (stack_x, stack_base_y - offset_y))
                    
                    draw_text(f"{staged}", font_main, WHITE, screen, stack_x + 15, stack_base_y - (vis_stack*5) - 20)

            # Dragged Coin
            if self.held_coin:
                mx, my = pygame.mouse.get_pos()
                img = self.images.get(f"coin_{self.held_coin['type']}")
                if img: screen.blit(img, (mx - 32, my - 32))

            # Buttons
            self.btn_leave_bet.draw(screen)
            
            # Header
            draw_panel(screen, cx - 200, 30, 400, 60, (0,0,0,150), GOLD_COLOR)
            draw_text("PLACE YOUR BET", font_title, GOLD_COLOR, screen, cx - 120, 45)

            if self.bet_amount > 0:
                self.btn_start.draw(screen)
            
            if self.message:
                 draw_text(self.message, font_main, RED, screen, cx - 100, cy + 140)
            return

        # --- BOARD ---
        
        # --- PLAYMATS (Backgrounds for cards) ---
        mat_w = 800
        mat_h = 180
        mat_x = (SCREEN_WIDTH - mat_w) // 2 # Keskitetty
        
        # AI Mat
        s = pygame.Surface((mat_w, mat_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 80))
        screen.blit(s, (mat_x, cy - 220))
        pygame.draw.rect(screen, (60, 30, 30), (mat_x, cy - 220, mat_w, mat_h), 2, border_radius=10)
        
        # Player Mat
        s2 = pygame.Surface((mat_w, mat_h), pygame.SRCALPHA)
        s2.fill((0, 0, 0, 80))
        screen.blit(s2, (mat_x, cy + 30))
        pygame.draw.rect(screen, (30, 60, 30), (mat_x, cy + 30, mat_w, mat_h), 2, border_radius=10)

        # AI Area (Left Top)
        draw_panel(screen, 50, cy - 200, 200, 100, (40, 20, 20), border_color=(100, 50, 50))
        draw_text("DEALER", font_small, (200, 100, 100), screen, 70, cy - 180)
        draw_text(f"{self.get_score(self.ai_board, self.ai_score_mod)}", font_main, WHITE, screen, 70, cy - 150)
        if self.ai_stopped: draw_text("STOPPED", font_main, RED, screen, 150, cy - 150)
        
        for i, c in enumerate(self.ai_board):
            c.rect.topleft = (mat_x + 20 + i * 110, cy - 200) # Update rect for clicking
            screen.blit(c.image, c.rect)
            
            if c.is_duel_penalty:
                draw_text("-2", font_main, RED, screen, mat_x + 20 + i * 110 + 30, cy - 200 + 50)
            
        # Player Area (Left Bottom)
        draw_panel(screen, 50, cy + 50, 200, 100, (20, 40, 20), border_color=(50, 100, 50))
        draw_text("PLAYER", font_small, (100, 200, 100), screen, 70, cy + 70)
        draw_text(f"{self.get_score(self.p_board, self.p_score_mod)}", font_main, WHITE, screen, 70, cy + 100)
        if self.p_stopped: draw_text("STOPPED", font_main, GREEN, screen, 150, cy + 100)

        for i, c in enumerate(self.p_board):
            c.rect.topleft = (mat_x + 20 + i * 110, cy + 50) # Update rect for clicking
            screen.blit(c.image, c.rect)
            
            if c.is_duel_penalty:
                draw_text("-2", font_main, RED, screen, mat_x + 20 + i * 110 + 30, cy + 50 + 50)

        # --- HANDS ---
        # AI Hand (Face down) - Centered Top
        ai_hand_w = len(self.ai_hand) * 60
        start_x_ai = (SCREEN_WIDTH - ai_hand_w) // 2
        for i, c in enumerate(self.ai_hand):
            screen.blit(self.images["BACK"], (start_x_ai + i * 60, 50))
            
        # Player Hand
        start_x = SCREEN_WIDTH // 2 - (len(self.p_hand) * 60)
        mouse_pos = pygame.mouse.get_pos()
        for i, c in enumerate(self.p_hand):
            # Skip drawing if dragging
            if i == self.dragging_card_idx:
                continue

            x = start_x + i * 120
            y = SCREEN_HEIGHT - 160
            
            # Hover/Select effect
            offset = 0
            if i == self.selected_card_idx: offset = -20
            elif pygame.Rect(x, y, CARD_W, CARD_H).collidepoint(mouse_pos): offset = -10
            
            screen.blit(c.image, (x, y + offset))
            if i == self.selected_card_idx:
                pygame.draw.rect(screen, GOLD_COLOR, (x, y + offset, CARD_W, CARD_H), 3)

        # Draw Dragged Card
        if self.dragging_card_idx is not None and self.dragging_card_idx < len(self.p_hand):
            c = self.p_hand[self.dragging_card_idx]
            mx, my = mouse_pos
            dx, dy = self.drag_offset
            screen.blit(c.image, (mx + dx, my + dy))

        # --- DRAW PILE ---
        if self.deck:
            # Draw stack effect
            for i in range(min(3, len(self.deck))):
                screen.blit(self.images["BACK"], (self.deck_rect.x - i*2, self.deck_rect.y - i*2))
        else:
            pygame.draw.rect(screen, (50, 50, 50), self.deck_rect, 2)
            draw_text("Empty", font_small, GRAY, screen, self.deck_rect.centerx - 20, self.deck_rect.centery)

        # --- UI ---
        if self.state == "PLAYER_TURN" and not self.p_stopped:
            self.btn_play.draw(screen)
            self.btn_stop.draw(screen)
            
        if self.state == "GAME_OVER":
            draw_panel(screen, cx - 300, cy - 120, 600, 300, (0, 0, 0, 220))
            msg_w = font_title.size(self.message)[0]
            draw_text(self.message, font_title, GOLD_COLOR, screen, cx - msg_w//2, cy - 80)
            self.btn_leave.draw(screen)
            self.btn_again.draw(screen)
            
        if self.state == "DUEL":
            draw_panel(screen, cx - 300, cy - 150, 600, 300, (50, 0, 0, 200))
            draw_text("DUEL!", font_title, RED, screen, cx - 50, cy - 100)
            if len(self.duel_cards) == 2:
                p_c, ai_c = self.duel_cards
                if p_c: screen.blit(p_c.image, (cx - 120, cy))
                if ai_c: screen.blit(ai_c.image, (cx + 20, cy))
                
        if self.state == "DUEL_SELECT":
            draw_panel(screen, cx - 300, cy - 150, 600, 300, (50, 0, 0, 200))
            draw_text("DUEL!", font_title, RED, screen, cx - 50, cy - 100)
            draw_text("Select a card from your hand!", font_main, WHITE, screen, cx - 150, cy - 50)

        if self.state == "LUCK_SELECT":
            draw_panel(screen, cx - 300, cy - 150, 600, 300, (20, 40, 20, 230), border_color=GREEN)
            draw_text("FATE'S CHOICE", font_title, GOLD_COLOR, screen, cx - 100, cy - 120)
            draw_text("Choose one card to keep:", font_main, WHITE, screen, cx - 120, cy - 80)
            
            mouse_pos = pygame.mouse.get_pos()
            for i, c in enumerate(self.luck_options):
                x = cx - 120 + i*140
                y = cy - 40
                rect = pygame.Rect(x, y, CARD_W, CARD_H)
                screen.blit(c.image, (x, y))
                if rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, GOLD_COLOR, rect, 3)
        
        if self.state == "CHEAT_TARGET_SELECT":
            draw_text("SELECT TARGET SWORD", font_title, GOLD_COLOR, screen, cx - 150, cy - 100)
            # Highlight valid targets
            mouse_pos = pygame.mouse.get_pos()
            for c in self.p_board + self.ai_board:
                if c.type == "SWORD" and not c.is_duel_penalty:
                    # Draw highlight rect
                    pygame.draw.rect(screen, GOLD_COLOR, c.rect.inflate(10, 10), 3, border_radius=5)
                    if c.rect.collidepoint(mouse_pos):
                        # Hover effect
                        pygame.draw.rect(screen, WHITE, c.rect.inflate(14, 14), 3, border_radius=5)

        if self.state == "WIN_DECISION":
            draw_panel(screen, cx - 300, cy - 160, 600, 480, (0, 0, 0, 220), GOLD_COLOR)
            
            title_w = font_main.size("VICTORY!")[0]
            draw_text("VICTORY!", font_main, GREEN, screen, cx - title_w//2, cy - 130)
            
            win_str = f"Winnings: {format_money(self.current_winnings)}"
            win_w = font_main.size(win_str)[0]
            draw_text(win_str, font_main, WHITE, screen, cx - win_w//2, cy - 100)
            
            if self.double_streak < 3:
                dbl_title = "DOUBLE OR NOTHING?"
                dbl_w = font_main.size(dbl_title)[0]
                draw_text(dbl_title, font_main, GOLD_COLOR, screen, cx - dbl_w//2, cy - 50)
                
                instr = "Throw the coin to risk it all!"
                instr_w = font_small.size(instr)[0]
                draw_text(instr, font_small, WHITE, screen, cx - instr_w//2, cy - 20)
                
                # Draw the draggable coin
                img = self.images.get("coin_crown")
                if img:
                    # Scale slightly larger for UI (80x80)
                    scaled = pygame.transform.smoothscale(img, (80, 80))
                    screen.blit(scaled, (int(self.double_coin_pos.x) - 40, int(self.double_coin_pos.y) - 40))
                    
                streak_str = f"Streak: {self.double_streak}/3"
                streak_w = font_small.size(streak_str)[0]
                draw_text(streak_str, font_small, GRAY, screen, cx - streak_w//2, cy + 120)
            else:
                max_str = "Max Streak Reached!"
                max_w = font_main.size(max_str)[0]
                draw_text(max_str, font_main, GOLD_COLOR, screen, cx - max_w//2, cy + 50)

            self.btn_collect.draw(screen)

        if self.state == "DOUBLE_ANIMATION":
            # Draw Coin
            img_key = "coin_crown"
            scale_x = 1.0
            
            if self.double_coin_state == "SPIN":
                scale_x = abs(math.sin(pygame.time.get_ticks() * 0.02))
                phase = math.sin(pygame.time.get_ticks() * 0.02)
                img_key = "coin_crown" if phase > 0 else "coin_crown_num"
            elif self.double_coin_state == "RESULT":
                img_key = "coin_crown" if self.double_result else "coin_crown_num"

            base_img = self.images.get(img_key)
            if base_img:
                w = int(80 * scale_x) # 80px size
                if w > 0:
                    scaled = pygame.transform.smoothscale(base_img, (w, 80))
                    screen.blit(scaled, (int(self.double_coin_pos.x) - w//2, int(self.double_coin_pos.y) - 40))

        # Message
        if self.message and self.state != "GAME_OVER":
            msg_w = font_main.size(self.message)[0]
            draw_text(self.message, font_main, WHITE, screen, cx - msg_w//2, cy)
            
        # VFX Layer
        self.manager.vfx.draw_top(screen, (0,0))
