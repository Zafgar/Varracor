import pygame
import random
import os
from settings import *
from menus.base_menu import BaseMenu
from ui_kit import draw_text, font_title, font_main, GOLD_COLOR, WHITE

class LoadingScreen(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.timer = 160 # Pidennetty kesto (n. 2.5s) jotta ehtii lukea
        self.dots = 0
        self.dot_timer = 0
        self.fade_alpha = 255 # Aloita mustasta (fade in)
        
        # Haetaan kohde managerilta, oletuksena hub
        self.target_state = getattr(manager, "loading_target_state", "hub")
        
        # Loading Data (Image ID -> Texts)
        self.loading_data = {
            1: [
                "The Abyssal Vortex doesn’t ‘open’ like a gate—it behaves like a wound that keeps trying to widen.",
                "Near the Vortex, direction lies. Follow landmarks, not instinct.",
                "Veteran hunters say the Rift ‘learns’ patterns… then repeats them with cruel precision."
            ],
            2: [
                "Muckford survives on salvage: broken blades become nails, and scraps become meals.",
                "Early tiers reward preparation—bandages and salves often matter more than armor.",
                "In Muckford slang, a ‘clean run’ means you came back with the same name you left with."
            ],
            3: [
                "Highstone calls the arenas ‘training grounds’—but the tithe is real, and nothing beyond basic healing is free.",
                "Arkon’s judgment is quiet. That silence has ended more feuds than any treaty.",
                "Holy seals can contain Vortex-taint… for a price measured in coin and vows."
            ],
            4: [
                "Arena managers answer to coin, reputation, and survival—not to kings.",
                "A win in one region can make you famous… and hunted in another.",
                "The arenas became a truce mechanism: disputes settle in sand so armies don’t march."
            ],
            5: [
                "Swarms are ‘small wars’—weak individually, unstoppable in numbers.",
                "Rats don’t just bite. They strip supplies, break morale, and collapse cities from the inside.",
                "Hamo’s rule: ‘If it moves like a tide, don’t fight it head-on. Break the path.’"
            ],
            6: [
                "The Wyrdwood Wardens protect beings the other realms would call ‘monsters.’",
                "Forest reagents can’t be forged—only earned through trust.",
                "In Wyrdwood law, taking more than you need is a crime… paid back in blood or service."
            ],
            7: [
                "Kharak’s dunes hide more than sand—old bones, buried ruins, and beasts drawn by the wild call.",
                "Caravans trade rare salts, resins, and hides… but every route has a price.",
                "Minotaur law values endurance: if you can’t hold the line, you don’t deserve it."
            ],
            8: [
                "Spire ruins test arrogance. Many who enter return quiet—or not at all.",
                "In Spire doctrine, battle is calculation. In the Rift, calculation becomes prophecy… or a lie.",
                "Glasslike ground punishes greed: one mistake, and the fight ends beneath your feet."
            ],
            9: [
                "Arena registration covers basic healing. Restoration and cleansing are billed separately.",
                "Some wounds aren’t physical. Vortex-taint can cling to memory, not flesh.",
                "Temple seals can reattach what battle removes… but every miracle has a receipt."
            ],
            10: [
                "Some enemies don’t hunt flesh—they hunt what you remember.",
                "Veterans call it ‘The Forgetter.’ Those who survive rarely agree on its face.",
                "If a voice echoes twice, don’t answer. It may be testing your anchor."
            ]
        }
        
        # Pick random image and text
        self.img_id = random.randint(1, 10)
        self.current_text = random.choice(self.loading_data[self.img_id])
        
        # Load Image
        self.bg_image = None
        try:
            path = os.path.join("assets", "images", "loading", f"loading_{self.img_id}.png")
            if os.path.exists(path):
                raw = pygame.image.load(path).convert()
                self.bg_image = pygame.transform.smoothscale(raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
            else:
                print(f"Loading image not found: {path}")
        except Exception as e:
            print(f"Error loading loading screen: {e}")

    def update(self):
        self.timer -= 1
        
        # Fade In
        if self.fade_alpha > 0:
            self.fade_alpha -= 5
            if self.fade_alpha < 0: self.fade_alpha = 0
        
        # Animoi pisteet (...)
        self.dot_timer += 1
        if self.dot_timer > 15:
            self.dot_timer = 0
            self.dots = (self.dots + 1) % 4
            
        if self.timer <= 0:
            self.next_state = self.target_state

    def draw(self, screen):
        w, h = screen.get_size()
        
        # Draw Background
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill((10, 10, 15))
            
        # Darken bottom area for text
        s = pygame.Surface((w, 150), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        screen.blit(s, (0, h - 150))
        
        # Loading text
        txt = "LOADING" + "." * self.dots
        # Lasketaan tekstin leveys jotta se pysyy ruudulla (oikea alakulma)
        txt_surf = font_title.render(txt, True, GOLD_COLOR)
        screen.blit(txt_surf, (w - txt_surf.get_width() - 50, h - 80))
        
        # Flavor Text (Centered)
        text_surf = font_main.render(self.current_text, True, (220, 220, 220))
        text_rect = text_surf.get_rect(center=(w // 2, h - 100))
        
        # Jos teksti on liian leveä, skaalaa hieman tai piirrä vasempaan reunaan
        if text_rect.width > w - 100:
            text_rect.left = 50
        
        screen.blit(text_surf, text_rect)
        
        # Progress bar (fake)
        bar_w = w
        bar_h = 10
        pct = 1.0 - (self.timer / 160.0)
        if pct > 1.0: pct = 1.0
        pygame.draw.rect(screen, (50, 50, 60), (0, h - bar_h, bar_w, bar_h))
        pygame.draw.rect(screen, GOLD_COLOR, (0, h - bar_h, int(bar_w * pct), bar_h))
        
        # Fade Overlay
        if self.fade_alpha > 0:
            fade = pygame.Surface((w, h), pygame.SRCALPHA)
            fade.fill((0, 0, 0, self.fade_alpha))
            screen.blit(fade, (0, 0))