"""Rattlebridge-specific contract board.

These contracts stay local to Rattlebridge rather than leaking into Muckford's
notice board. Progress is derived from city exploration, Canalworks patrols,
Scrapring wins and Hush-Mantle sightings.
"""

from __future__ import annotations

import pygame

from citys.rattlebridge.rattlebridge_data import RATTLEBRIDGE_CONTRACTS
from menus.base_menu import BaseMenu
from settings import GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import UIButton, draw_text, font_main, font_small, font_title


class RattlebridgeContractsMenu(BaseMenu):
    def __init__(self, manager):
        super().__init__(manager)
        self.feedback = ""
        self.feedback_timer = 0
        self.scroll_y = 0
        self.card_rects = []
        self.btn_back = UIButton(SCREEN_WIDTH - 255, SCREEN_HEIGHT - 90,
                                 200, 55, "BACK", None, GRAY)

    def on_enter(self):
        self.manager.city_spawn_point = "market"
        self._state()

    def _state(self):
        root = self.manager.npc_state.setdefault("rattlebridge", {})
        contracts = root.setdefault("contracts", {})
        for contract in RATTLEBRIDGE_CONTRACTS:
            contracts.setdefault(contract["id"], {
                "status": "available",
                "claimed": False,
            })
        return contracts

    def _contract_state(self, contract_id):
        return self._state()[contract_id]

    def _progress(self, contract):
        root = self.manager.npc_state.setdefault("rattlebridge", {})
        objective = contract["objective"]
        if objective == "survey_freight_deck":
            visited = root.get("districts_visited", [])
            return (1 if "freight_deck" in visited else 0, 1,
                    "Visit and survey the Freight Deck")
        if objective == "gutter_swarm_patrol":
            value = min(3, int(root.get("gutter_patrols", 0)))
            return value, 3, "Clear three Canalworks swarm nests"
        if objective == "scrapring_sponsor_trial":
            introduced = bool(root.get("sera_introduced", False))
            wins = int(getattr(getattr(self.manager, "league_engine", None),
                               "wins_this_tier", 0))
            value = 1 if introduced and wins >= 1 else 0
            return value, 1, "Speak to Sera and win a Tier 1 league match"
        if objective == "hush_mantle_rumors":
            value = min(3, int(root.get("hush_mantle_sightings", 0)))
            return value, 3, "Witness three silent-fog incidents"
        return 0, 1, "Objective not yet tracked"

    def _is_complete(self, contract):
        current, required, _ = self._progress(contract)
        return current >= required

    def _accept(self, contract):
        state = self._contract_state(contract["id"])
        if state["status"] != "available":
            return
        state["status"] = "active"
        self.feedback = f"Accepted: {contract['title']}"
        self.feedback_timer = 180
        sound_system.play_sound("click")

    def _grant_xp(self, amount):
        unit = getattr(self.manager, "player_character", None)
        if not unit or amount <= 0:
            return
        for method_name in ("gain_xp", "add_xp"):
            method = getattr(unit, method_name, None)
            if callable(method):
                method(amount)
                return
        unit.xp = int(getattr(unit, "xp", 0)) + int(amount)

    def _claim(self, contract):
        state = self._contract_state(contract["id"])
        if state["status"] != "active" or not self._is_complete(contract):
            self.feedback = "The contract conditions have not been met."
            self.feedback_timer = 170
            sound_system.play_sound("error")
            return
        reward = contract["reward"]
        self.manager.gold = int(getattr(self.manager, "gold", 0)) + int(reward.get("gold", 0))
        try:
            self.manager.reputation += int(reward.get("reputation", 0))
        except Exception:
            global_state = self.manager.npc_state.setdefault("global", {})
            global_state["reputation"] = int(global_state.get("reputation", 0)) + int(reward.get("reputation", 0))
        self._grant_xp(int(reward.get("xp", 0)))
        for name, amount in reward.get("materials", {}).items():
            try:
                self.manager.add_material(name, amount)
            except Exception:
                self.manager.inventory[name] = self.manager.inventory.get(name, 0) + amount
        state["status"] = "completed"
        state["claimed"] = True
        self.feedback = f"Contract completed: {contract['title']}"
        self.feedback_timer = 240
        sound_system.play_sound("coin")

    def _handle_contract(self, contract):
        state = self._contract_state(contract["id"])
        if state["status"] == "available":
            self._accept(contract)
        elif state["status"] == "active":
            self._claim(contract)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "rattlebridge_city"
            return
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, self.scroll_y - event.y * 55)
            return
        if self.btn_back.is_clicked(event):
            self.next_state = "rattlebridge_city"
            sound_system.play_sound("click")
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, contract in self.card_rects:
                if rect.collidepoint(event.pos):
                    self._handle_contract(contract)
                    return

    def update(self):
        super().update()
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        max_scroll = max(0, len(RATTLEBRIDGE_CONTRACTS) * 230 - 700)
        self.scroll_y = min(self.scroll_y, max_scroll)

    @staticmethod
    def _wrap(text, width, font=font_small):
        lines = []
        current = ""
        for word in str(text).split():
            trial = word if not current else f"{current} {word}"
            if font.size(trial)[0] <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def draw(self, screen):
        self.draw_themed_background(screen, "quest")
        title = font_title.render("RATTLEBRIDGE CONTRACT BOARD", True, GOLD_COLOR)
        self.draw_header_bar(screen, title, y=25)
        draw_text("Union, Crown, arena and bridgeguard work — Lv 6–10",
                  font_main, (190, 195, 205), screen, 80, 120)
        draw_text("Click a contract to accept or claim it. Mouse wheel scrolls.",
                  font_small, GRAY, screen, 80, 152)

        viewport = pygame.Rect(70, 190, SCREEN_WIDTH - 140, SCREEN_HEIGHT - 310)
        pygame.draw.rect(screen, (22, 22, 28), viewport, border_radius=12)
        pygame.draw.rect(screen, (120, 105, 78), viewport, 2, border_radius=12)
        old_clip = screen.get_clip()
        screen.set_clip(viewport)
        self.card_rects = []
        y = viewport.y + 18 - self.scroll_y
        mouse = pygame.mouse.get_pos()

        for contract in RATTLEBRIDGE_CONTRACTS:
            state = self._contract_state(contract["id"])
            current, required, progress_text = self._progress(contract)
            complete = current >= required
            rect = pygame.Rect(viewport.x + 18, y, viewport.w - 36, 205)
            visible = rect.bottom >= viewport.top and rect.top <= viewport.bottom
            if visible:
                hover = rect.collidepoint(mouse)
                if state["status"] == "completed":
                    bg = (34, 56, 43)
                    border = (90, 185, 115)
                elif complete and state["status"] == "active":
                    bg = (58, 50, 33)
                    border = (220, 178, 92)
                elif hover:
                    bg = (43, 44, 54)
                    border = (130, 145, 175)
                else:
                    bg = (31, 32, 39)
                    border = (80, 85, 100)
                pygame.draw.rect(screen, bg, rect, border_radius=10)
                pygame.draw.rect(screen, border, rect, 2, border_radius=10)
                draw_text(contract["title"], font_title, WHITE,
                          screen, rect.x + 24, rect.y + 16)
                low, high = contract["recommended_level"]
                draw_text(f"Giver: {contract['giver']}  |  Recommended Lv {low}-{high}",
                          font_small, (180, 195, 210), screen,
                          rect.x + 26, rect.y + 54)
                sy = rect.y + 86
                for line in self._wrap(contract["summary"], rect.w - 360, font_main):
                    draw_text(line, font_main, (215, 210, 195),
                              screen, rect.x + 26, sy)
                    sy += 28
                draw_text(f"Progress: {current}/{required} — {progress_text}",
                          font_small,
                          GREEN if complete else (220, 175, 100),
                          screen, rect.x + 26, rect.bottom - 52)
                reward = contract["reward"]
                reward_text = (
                    f"{reward.get('gold', 0)} GP  •  {reward.get('reputation', 0)} Rep  •  "
                    f"{reward.get('xp', 0)} XP"
                )
                draw_text(reward_text, font_small, GOLD_COLOR,
                          screen, rect.right - 370, rect.y + 24)
                action = {
                    "available": "CLICK TO ACCEPT",
                    "active": "CLICK TO CLAIM" if complete else "ACTIVE",
                    "completed": "COMPLETED",
                }[state["status"]]
                draw_text(action, font_main, border,
                          screen, rect.right - 250, rect.bottom - 54)
                self.card_rects.append((rect, contract))
            y += 225

        screen.set_clip(old_clip)
        if self.feedback_timer > 0 and self.feedback:
            box = pygame.Rect(370, SCREEN_HEIGHT - 160, SCREEN_WIDTH - 740, 48)
            pygame.draw.rect(screen, (18, 18, 22), box, border_radius=8)
            pygame.draw.rect(screen, (180, 145, 85), box, 2, border_radius=8)
            draw_text(self.feedback, font_main, WHITE,
                      screen, box.x + 20, box.y + 12)
        self.btn_back.draw(screen)
