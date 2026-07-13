import pygame
import math
from settings import *
from ui_kit import UIButton, draw_panel, draw_text, font_title, font_main, font_small, GOLD_COLOR, GREEN, RED, WHITE, YELLOW, GRAY, format_money
from menus.base_menu import BaseMenu
from reputation.reputation_data import REPUTATION_FACTIONS

# XP logic import
from progression.xp_table import (
    MAX_LEVEL,
    level_from_xp,
    xp_for_level,
    next_level_xp,
    xp_to_next_level,
    level_progress_ratio
)


def draw_progress_bar(screen, x, y, w, h, pct,
                      back=(40, 40, 60),
                      fill=(80, 200, 120),
                      border=(180, 180, 180)):
    pct = max(0.0, min(1.0, float(pct)))
    pygame.draw.rect(screen, back, (x, y, w, h))
    pygame.draw.rect(screen, fill, (x, y, int(w * pct), h))
    pygame.draw.rect(screen, border, (x, y, w, h), 2)


def projected_level_and_flags(current_total_xp: int, gain: int):
    """
    Project total XP after gain and return:
    (old_lvl, new_lvl, new_total_xp, leveled_up_bool, level_ups_count)
    """
    cur = int(current_total_xp or 0)
    g = int(gain or 0)

    old_lvl = level_from_xp(cur)
    # cap total xp at max level threshold (optional but clean)
    max_total = xp_for_level(MAX_LEVEL)
    new_total = min(max_total, cur + max(0, g))
    new_lvl = level_from_xp(new_total)

    ups = max(0, new_lvl - old_lvl)
    return old_lvl, new_lvl, new_total, (ups > 0), ups


def compute_expected_xp_gain_for_unit(manager, unit):
    """
    Match GameManager.apply_rewards logic
    """
    xp_total = int(manager.round_rewards.get("xp", 0) or 0)
    if xp_total <= 0:
        return 0

    last = list(getattr(manager, "last_fighters", []) or [])
    if not last:
        return 0

    alive = [u for u in last if u and not getattr(u, "is_dead", False)]
    fighters = alive if alive else [u for u in last if u]

    if not fighters:
        return 0

    each = max(1, xp_total // len(fighters))
    return each if unit in fighters else 0


class BattleReportMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_next = UIButton(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 100, 200, 60, "NEXT >", None, GREEN)
        
        # --- ANIMATION STATE ---
        self.target_gold = int(self.manager.round_rewards.get("gold", 0))
        self.target_xp = int(self.manager.round_rewards.get("xp", 0))
        self.display_gold = 0.0
        self.display_xp = 0.0
        self.timer = 0

    def update(self):
        super().update()
        self.timer += 1
        
        # Rolling numbers animation (Lerp)
        if self.display_gold < self.target_gold:
            self.display_gold += max(1, (self.target_gold - self.display_gold) * 0.1)
            
        if self.display_xp < self.target_xp:
            self.display_xp += max(1, (self.target_xp - self.display_xp) * 0.1)

    def handle_event(self, event):
        # Skip animation on click
        if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
            if self.display_gold < self.target_gold * 0.95 or self.display_xp < self.target_xp * 0.95:
                self.display_gold = self.target_gold
                self.display_xp = self.target_xp
                return

        if self.btn_next.is_clicked(event):
            self.next_state = "loot_screen"

    def draw(self, screen):
        # 1. Background (Themed)
        self.draw_themed_background(screen, mood="city")

        # Result
        res_col = GREEN if self.manager.match_result == "VICTORY" else RED
        draw_text(self.manager.match_result, font_title, res_col, screen, SCREEN_WIDTH // 2 - 120, 40)

        # --- MUUTOS: Piilotetaan palkinnot tästä ruudusta (siirretty Loot Screeniin) ---
        # draw_panel(screen, SCREEN_WIDTH // 2 - 260, 95, 520, 55)
        # g_amt = int(self.display_gold)
        # xp_amt = int(self.display_xp)
        # draw_text(f"+{g_amt} GOLD", font_main, GOLD_COLOR, screen, SCREEN_WIDTH // 2 - 240, 108)
        # draw_text(f"+{xp_amt} XP (on claim)", font_main, (180, 220, 255), screen, SCREEN_WIDTH // 2 + 40, 108)
        
        draw_text("Battle Statistics", font_main, WHITE, screen, SCREEN_WIDTH // 2 - 80, 110)

        # Table headers
        table_y = 170
        headers = ["UNIT", "LVL", "XP", "DMG", "KILL", "ASSIST", "HEAL"]
        col_x = [110, 290, 350, 560, 650, 740, 840]

        for i, h in enumerate(headers):
            draw_text(h, font_main, GOLD_COLOR, screen, col_x[i], table_y)

        # Sort by damage
        my_fighters = [u for u in self.manager.all_units if getattr(u, "team_color", None) == GREEN]
        my_fighters.sort(key=lambda x: x.stats.get("damage", 0), reverse=True)

        for i, u in enumerate(my_fighters):
            row_y = table_y + 42 + (i * 52)

            # Row background for readability (Zebra striping)
            row_bg_col = (30, 30, 40) if i % 2 == 0 else (35, 35, 45)
            pygame.draw.rect(screen, row_bg_col, (col_x[0] - 10, row_y, 800, 40), border_radius=4)

            total_xp = int(getattr(u, "xp", 0) or 0)
            old_lvl = int(getattr(u, "level", level_from_xp(total_xp)) or 1)
            # jos level attr on jostain syystä pielessä, korjaa UI:lle
            old_lvl = level_from_xp(total_xp)

            gain = compute_expected_xp_gain_for_unit(self.manager, u)
            old_lvl2, new_lvl, new_total, leveled, ups = projected_level_and_flags(total_xp, gain)

            # XP text / thresholds
            if old_lvl >= MAX_LEVEL:
                xp_text = "MAX"
                pct = 1.0
                to_next = 0
            else:
                nxt = next_level_xp(total_xp)  # total XP threshold for next level
                to_next = xp_to_next_level(total_xp)
                xp_text = f"{total_xp}/{nxt} (+{gain})"
                pct = level_progress_ratio(new_total)

            # Row texts
            draw_text(getattr(u, "name", "Unit"), font_small, WHITE, screen, col_x[0], row_y + 8)
            draw_text(str(old_lvl), font_small, WHITE, screen, col_x[1], row_y + 8)
            draw_text(xp_text, font_small, (200, 220, 255), screen, col_x[2], row_y + 8)

            # Bar + "to next"
            bar_x = col_x[2]
            bar_y = row_y + 26
            draw_progress_bar(screen, bar_x, bar_y, 170, 12, pct, fill=(90, 180, 255))

            if old_lvl < MAX_LEVEL:
                pass # Removed "to next" text to save space and reduce clutter

            if leveled:
                draw_text(f"LEVEL UP! (+{ups})", font_small, (255, 220, 120), screen, bar_x + 185, row_y + 8)

            # Stats
            draw_text(str(int(u.stats.get("damage", 0))), font_small, WHITE, screen, col_x[3], row_y + 8)
            draw_text(str(int(u.stats.get("kills", 0))), font_small, WHITE, screen, col_x[4], row_y + 8)
            draw_text(str(int(u.stats.get("assists", 0))), font_small, WHITE, screen, col_x[5], row_y + 8)
            draw_text(str(int(u.stats.get("healing", 0))), font_small, WHITE, screen, col_x[6], row_y + 8)

        self.btn_next.check_hover(pygame.mouse.get_pos())
        self.btn_next.draw(screen)


class LootScreenMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_claim = UIButton(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 150, 200, 60, "CLAIM REWARDS", "coin", GOLD_COLOR)

    def update(self):
        super().update()

    def handle_event(self, event):
        if self.btn_claim.is_clicked(event):
            self.manager.apply_rewards()
            
            if self.manager.is_game_over:
                self.next_state = "menu"
            
            # --- NEW: Check for Promotion Victory ---
            elif getattr(self.manager, "match_mode", "") == "PROMOTION" and self.manager.match_result == "VICTORY":
                # Nosta tieriä jos ei vielä tehty
                if hasattr(self.manager, "league_engine") and self.manager.league_engine:
                    self.manager.league_engine.promote_player()
                
                # Siirry seremoniaan
                self.next_state = "promotion_ceremony"

            elif getattr(self.manager, "mode", "") == "League":
                # Liigamatsin jälkeen takaisin liigavalikkoon (sarjataulukko,
                # seuraava vastustaja) - ei vanhaan hubiin
                self.next_state = "league"
            else:
                self.next_state = "hub"

    def draw(self, screen):
        self.draw_themed_background(screen, mood="city")
        draw_text("VICTORY REWARDS", font_title, GOLD_COLOR, screen, SCREEN_WIDTH // 2 - 160, 50)

        # Gold + XP panels
        g_amt = int(self.manager.round_rewards.get("gold", 0))
        xp_amt = int(self.manager.round_rewards.get("xp", 0))

        draw_panel(screen, SCREEN_WIDTH // 2 - 220, 140, 440, 70)
        draw_text(f"+ {format_money(g_amt)}", font_title, YELLOW, screen, SCREEN_WIDTH // 2 - 170, 150)

        draw_panel(screen, SCREEN_WIDTH // 2 - 220, 220, 440, 70)
        draw_text(f"+ {xp_amt} XP", font_title, (180, 220, 255), screen, SCREEN_WIDTH // 2 - 140, 230)

        # Items
        loot = self.manager.round_rewards.get("loot", {})
        ly = 330
        if loot:
            draw_text("ITEMS FOUND:", font_main, WHITE, screen, SCREEN_WIDTH // 2 - 70, 290)
            for item_name, count in loot.items():
                draw_text(f"{item_name} x{count}", font_main, (200, 200, 255), screen, SCREEN_WIDTH // 2 - 90, ly)
                ly += 30
        else:
            draw_text("No items found this time.", font_small, GRAY, screen, SCREEN_WIDTH // 2 - 90, 330)

        self.btn_claim.check_hover(pygame.mouse.get_pos())
        self.btn_claim.draw(screen)


class SwarmReportMenu(BaseMenu):
    """
    Yhdistetty raportti Swarm/Monster Hunt -moodille.
    Näyttää: Wave, Stats, Loot, Gold, XP.
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.btn_hub = UIButton(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 60, "RETURN TO HUB", None, GREEN)

    def handle_event(self, event):
        if self.btn_hub.is_clicked(event):
            # TÄRKEÄÄ: Lunasta palkinnot kun poistutaan
            self.manager.apply_rewards()
            self.next_state = "hub"

    def draw(self, screen):
        self.draw_themed_background(screen, mood="quest")
        
        # 1. Otsikko ja Wave
        res_col = GREEN if self.manager.match_result == "VICTORY" else RED
        status_text = "SWARM CLEARED" if self.manager.match_result == "VICTORY" else "SWARM OVER"
        draw_text(status_text, font_title, res_col, screen, SCREEN_WIDTH // 2 - 140, 30)
        
        wave = self.manager.round_rewards.get("wave", 0)
        draw_text(f"Reached Wave: {wave}", font_title, GOLD_COLOR, screen, SCREEN_WIDTH // 2 - 110, 80)

        # 2. Palkinnot (Gold & XP)
        g = int(self.manager.round_rewards.get("gold", 0))
        xp = int(self.manager.round_rewards.get("xp", 0))
        draw_text(f"Total Rewards: {format_money(g)}  |  {xp} XP", font_main, WHITE, screen, SCREEN_WIDTH // 2 - 150, 130)
        
        # --- REPUTATION CHANGES ---
        rep_changes = self.manager.round_rewards.get("rep_changes", {})
        if rep_changes:
            rep_y = 160
            
            # Helper to find faction name
            def get_faction_name(fid):
                for cat in REPUTATION_FACTIONS.values():
                    if fid in cat["factions"]:
                        return cat["factions"][fid]["name"]
                return fid.capitalize()

            for fid, amount in rep_changes.items():
                fname = get_faction_name(fid)
                sign = "+" if amount > 0 else ""
                col = GREEN if amount > 0 else RED
                draw_text(f"{fname}: {sign}{amount} Rep", font_small, col, screen, SCREEN_WIDTH // 2 - 150, rep_y)
                rep_y += 20

        # 3. Vasen paneeli: Squad Stats
        stats_x = 100
        stats_y = 260 # Siirretty alemmas (oli 200)
        draw_text("SQUAD PERFORMANCE", font_main, GOLD_COLOR, screen, stats_x, stats_y)
        
        # Headers
        draw_text("Unit", font_small, GRAY, screen, stats_x, stats_y + 30)
        draw_text("Kills", font_small, GRAY, screen, stats_x + 200, stats_y + 30)
        draw_text("Damage", font_small, GRAY, screen, stats_x + 300, stats_y + 30)
        
        fighters = list(self.manager.last_fighters)
        fighters.sort(key=lambda u: u.stats.get("kills", 0), reverse=True)
        
        for i, u in enumerate(fighters[:10]): # Max 10 listaan
            y = stats_y + 60 + (i * 25)
            draw_text(u.name, font_small, WHITE, screen, stats_x, y)
            draw_text(str(u.stats.get("kills", 0)), font_small, WHITE, screen, stats_x + 200, y)
            draw_text(str(int(u.stats.get("damage", 0))), font_small, WHITE, screen, stats_x + 300, y)

        # 4. Oikea paneeli: Loot
        loot_x = SCREEN_WIDTH // 2 + 100
        loot_y = 260 # Siirretty alemmas (oli 200)
        draw_text("LOOT OBTAINED", font_main, GOLD_COLOR, screen, loot_x, loot_y)
        
        loot = self.manager.round_rewards.get("loot", {})
        for i, (item, count) in enumerate(loot.items()):
            draw_text(f"{count}x {item}", font_small, (200, 200, 255), screen, loot_x, loot_y + 40 + (i * 25))

        self.btn_hub.check_hover(pygame.mouse.get_pos())
        self.btn_hub.draw(screen)