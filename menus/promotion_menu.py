import pygame
import random
import math
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import SpriteButton, draw_text, font_title, font_main, GOLD_COLOR, WHITE

class Confetti:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(-200, -50)
        self.speed = random.uniform(2, 5)
        self.color = random.choice([GOLD_COLOR, WHITE, (255, 100, 100), (100, 255, 100), (100, 100, 255)])
        self.size = random.randint(4, 8)
        self.sway = random.uniform(0, 100)
    
    def update(self):
        self.y += self.speed
        self.x += math.sin((self.y + self.sway) * 0.05) * 2
        if self.y > SCREEN_HEIGHT:
            self.y = random.randint(-50, 0)
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

class PromotionMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        
        self.btn_continue = SpriteButton(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
            "assets/ui/btn_start_idle.png",
            "assets/ui/btn_start_hover.png",
            "assets/ui/btn_start_pressed.png",
            label_text="CONTINUE", target_width=300
        )
        
        self.confetti = [Confetti() for _ in range(150)]
        self.timer = 0
        
        # POISTETTU TÄSTÄ: emme hae tieriä initissä, koska se kaataa pelin
        # ja näyttäisi väärää tietoa (pelin aloitustiedon).

    def handle_event(self, event):
        if self.btn_continue.update(): 
            self.next_state = "hub"

    def update(self):
        self.timer += 1
        for c in self.confetti:
            c.update()

    def draw(self, screen):
        screen.fill((20, 20, 25))
        
        # Piirretään konfetti taustalle
        for c in self.confetti:
            c.draw(screen)
            
        # --- HAE TIER NIMI TÄSSÄ (TURVALLISESTI) ---
        tier_name = "New Rank"
        if hasattr(self.manager, "league_engine") and self.manager.league_engine:
            # Käytetään samaa logiikkaa kuin GameManagerissa
            le = self.manager.league_engine
            # Yritetään hakea tier numero (oletus 1)
            current_tier = getattr(le, "tier", 1)
            
            # Yritetään hakea nimi listasta, jos semmoinen on
            names = getattr(le, "TIER_NAMES", {})
            tier_name = names.get(current_tier, f"Tier {current_tier}")

        # Tekstit
        scale = 1.0 + math.sin(self.timer * 0.05) * 0.05
        
        # RANK UP title
        title_surf = font_title.render("PROMOTION!", True, GOLD_COLOR)
        w, h = title_surf.get_size()
        scaled_surf = pygame.transform.scale(title_surf, (int(w * scale), int(h * scale)))
        rect = scaled_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(scaled_surf, rect)
        
        # Tier info
        draw_text("Congratulations, Commander!", font_main, WHITE, screen, SCREEN_WIDTH//2 - 140, 250)
        draw_text(f"You have ascended to:", font_main, (200, 200, 200), screen, SCREEN_WIDTH//2 - 100, 300)
        
        draw_text(str(tier_name).upper(), font_title, (100, 255, 100), screen, SCREEN_WIDTH//2 - 100, 350)
        
        draw_text("New challenges and stronger opponents await.", font_main, (150, 150, 150), screen, SCREEN_WIDTH//2 - 190, 450)

        # Nappi
        self.btn_continue.draw(screen)