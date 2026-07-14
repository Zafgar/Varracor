# citys/mucford/barracks_interior_menu.py
"""Team Barracksin sisätila: pelaaja ja gladiaattorit kävelevät samassa
tilassa. Punkat rajaavat tiimin koon, juttelu nostaa moraalia (kerran/pv),
komentajan pöytä avaa tiiminhallinnan ja suunnitelmataulu kehityksen.
Punkassa voi nukkua aamuun (koko tiimi palautuu)."""
import math
import random

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD_COLOR, WHITE, GRAY
from menus.gameplay_screen import GameplayScreen
from sound_manager import sound_system
from systems import keybinds
from ui_kit import draw_text, font_main, font_small, format_money
from citys.mucford.barracks_interior_arena import (
    BarracksInteriorArena, BUNKS_PER_LEVEL, UPGRADE_COSTS, LEVEL_NAMES,
)


class BarracksInteriorMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = BarracksInteriorArena(self._level())
        self.residents = []          # (unit, wander-data)
        self.show_upgrade = False
        self.upgrade_feedback = ""
        self._overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                       pygame.SRCALPHA)
        self.banner = ""
        self.banner_timer = 0
        # Kun palataan dialogista/pöytävalikosta, väki ei teleporttaa
        self._keep_positions = False

    # ------------------------------------------------------------------
    def _level(self):
        return max(1, min(3, int(getattr(self.manager, "barracks_level", 1))))

    def on_enter(self):
        super().on_enter()
        if self.arena.level != self._level():
            self.arena = BarracksInteriorArena(self._level())
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx

        self.player = self.manager.player_character
        roster_ids = [id(u) for u in self.manager.my_team if not u.is_dead]
        same_roster = roster_ids == [id(u) for u, _d in self.residents]
        if self._keep_positions and same_roster:
            # Paluu dialogista/valikosta: kaikki jäävät paikoilleen
            self._keep_positions = False
        else:
            door = self.arena.door_rect
            self.player.rect.centerx = door.centerx
            self.player.rect.bottom = door.top - 10
            self._spawn_residents()
        self._update_camera()
        self.show_upgrade = False
        self.upgrade_feedback = ""

    def on_exit(self):
        super().on_exit()
        # Gladiaattorit eivät saa jäädä managerin all_units-ryhmään
        for unit, _data in self.residents:
            unit.animation_state = "idle"

    # ------------------------------------------------------------------
    def _spawn_residents(self):
        """Sijoittaa oman tiimin gladiaattorit sisätilaan oleilemaan."""
        self.residents = []
        rng = random.Random(self.manager.world_clock.day)
        pois = self._points_of_interest()
        for i, unit in enumerate(self.manager.my_team):
            if unit.is_dead:
                continue
            spot = pois[i % len(pois)]
            unit.rect.center = (spot[0] + rng.randint(-30, 30),
                                spot[1] + rng.randint(-20, 20))
            unit.animation_state = "idle"
            unit.current_hp = max(unit.current_hp, 1)
            self.residents.append((unit, {
                "target": None,
                "wait": rng.randint(60, 300),
            }))

    def _points_of_interest(self):
        """Oleskelupisteet: punkkien edustat, pöydän ääri, takka, nukke."""
        a = self.arena
        pois = [(b.rect.centerx, b.rect.bottom + 46) for b in a.bunks]
        t = a.table.rect
        pois += [(t.centerx - 80, t.top - 30), (t.centerx + 80, t.top - 30),
                 (t.centerx - 60, t.bottom + 34), (t.centerx + 60, t.bottom + 34)]
        pois.append((a.hearth.rect.right + 70, a.hearth.rect.centery + 20))
        for p in a.props:
            if type(p).__name__ == "TrainingDummy":
                pois.append((p.rect.centerx - 70, p.rect.centery))
        return pois

    def _update_resident(self, unit, data):
        """Kevyt oleskelu-AI: kävele pisteelle, jää hengailemaan, jatka."""
        if data["wait"] > 0:
            data["wait"] -= 1
            if unit.animation_state == "run":
                unit.animation_state = "idle"
            return
        if data["target"] is None:
            pois = self._points_of_interest()
            data["target"] = random.choice(pois)
        tx, ty = data["target"]
        dx = tx - unit.rect.centerx
        dy = ty - unit.rect.centery
        dist = math.hypot(dx, dy)
        if dist < 12:
            data["target"] = None
            data["wait"] = random.randint(240, 900)
            unit.animation_state = "idle"
            return
        speed = 1.6
        step_x = speed * dx / dist
        step_y = speed * dy / dist
        unit.facing_right = dx > 0
        unit.animation_state = "run"
        # Törmäystesti: kokeile täysi askel, sitten akselit erikseen
        for mx, my in ((step_x, step_y), (step_x, 0), (0, step_y)):
            moved = unit.rect.move(mx, my)
            if not any(moved.colliderect(o.rect) for o in self.arena.obstacles):
                unit.rect = moved
                return
        # Jumissa: valitse uusi kohde
        data["target"] = None
        data["wait"] = 60

    # ------------------------------------------------------------------
    def _nearest_interactable(self):
        """(kind, obj, dist): gladiaattori, punkka, pöytä, taulu tai ovi."""
        px, py = self.player.rect.centerx, self.player.rect.centery
        best = (None, None, 1e9)

        def consider(kind, obj, ox, oy, radius):
            nonlocal best
            d = math.hypot(ox - px, oy - py)
            if d < radius and d < best[2]:
                best = (kind, obj, d)

        for unit, _data in self.residents:
            consider("talk", unit, unit.rect.centerx, unit.rect.centery, 95)
        for bunk in self.arena.bunks:
            consider("sleep", bunk, bunk.rect.centerx, bunk.rect.centery, 95)
        d = self.arena.desk
        consider("desk", d, d.rect.centerx, d.rect.centery, 120)
        b = self.arena.plans_board
        consider("plans", b, b.rect.centerx, b.rect.centery, 120)
        door = self.arena.door_rect
        consider("leave", door, door.centerx, door.top, 110)
        return best

    def handle_event(self, event):
        # Kehityspaneeli nappaa syötteet
        if self.show_upgrade:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_e):
                    self.show_upgrade = False
                elif event.key == pygame.K_RETURN:
                    self._try_upgrade()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if getattr(self, "_upgrade_btn", None) and \
                        self._upgrade_btn.collidepoint(event.pos):
                    self._try_upgrade()
                else:
                    self.show_upgrade = False
                return
            return

        if event.type == pygame.KEYDOWN and \
                event.key in keybinds.keys_for("interact"):
            if self.manager.active_dialogue or self.manager.dialogue_cooldown > 0:
                return super().handle_event(event)
            kind, obj, _d = self._nearest_interactable()
            if kind == "talk":
                self._talk_to(obj)
            elif kind == "sleep":
                self._sleep()
            elif kind == "desk":
                self.manager.barracks_return_state = "barracks_interior"
                self.manager.guild_return_state = "barracks"
                self._keep_positions = True
                self.next_state = "barracks"
                sound_system.play_sound("click")
            elif kind == "plans":
                self.show_upgrade = True
                self.upgrade_feedback = ""
                sound_system.play_sound("click")
            elif kind == "leave":
                self.next_state = "muckford_city"
                sound_system.play_sound("click")
            return

        super().handle_event(event)

    # ------------------------------------------------------------------
    def _talk_to(self, unit):
        """Juttele gladiaattorin kanssa: ensimmäinen rupattelu päivässä
        nostaa moraalia, ja RosterNPC-dialogi syventää tuttavuutta."""
        clock = self.manager.world_clock
        if getattr(unit, "last_social_day", -1) != clock.day:
            unit.last_social_day = clock.day
            gain = 8
            unit.adjust_morale(gain)
            self.manager.vfx.show_damage(
                unit.rect.centerx, unit.rect.top - 30,
                f"+{gain} MORALE", color=(140, 230, 150))
        menu = self.manager.open_roster_dialogue(
            unit, return_state="barracks_interior")
        if menu:
            self._keep_positions = True
            self.next_state = "dialogue_active"

    def _sleep(self):
        """Nuku aamuun: koko tiimi palautuu ja saa hieman moraalia."""
        clock = self.manager.world_clock
        clock.advance_day()
        clock.minutes = 7 * 60.0
        roster = [self.manager.player_character] + list(self.manager.my_team)
        for u in roster:
            if u is None:
                continue
            u.current_hp = u.max_hp
            u.current_stamina = u.max_stamina
            u.current_mana = getattr(u, "max_mana", 0)
            if hasattr(u, "adjust_morale") and u is not self.manager.player_character:
                u.adjust_morale(3)
        self.banner = "You rest until morning. The team feels refreshed."
        self.banner_timer = 300
        sound_system.play_sound("win")
        self._spawn_residents()

    def _try_upgrade(self):
        nxt = self._level() + 1
        cost = UPGRADE_COSTS.get(nxt)
        if not cost:
            self.upgrade_feedback = "The barracks is fully upgraded."
            return
        gold_cost = cost["gold"]
        inv = self.manager.inventory
        missing = []
        if self.manager.gold < gold_cost:
            missing.append(f"{format_money(gold_cost)}")
        for name, need in cost.items():
            if name == "gold":
                continue
            if inv.get(name, 0) < need:
                missing.append(f"{name} x{need}")
        if missing:
            self.upgrade_feedback = "Missing: " + ", ".join(missing)
            sound_system.play_sound("error")
            return
        self.manager.gold -= gold_cost
        for name, need in cost.items():
            if name == "gold":
                continue
            inv[name] = inv.get(name, 0) - need
            if inv[name] <= 0:
                del inv[name]
        self.manager.barracks_level = nxt
        self.arena = BarracksInteriorArena(nxt)
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx
        self.show_upgrade = False
        self.banner = f"BARRACKS UPGRADED: {LEVEL_NAMES[nxt]}!"
        self.banner_timer = 420
        sound_system.play_sound("win")
        self._spawn_residents()
        self._update_camera()

    # ------------------------------------------------------------------
    def update(self):
        if self.manager.paused:
            return
        super().update()  # BaseMenu (editor)
        if self.manager.active_dialogue or self.show_upgrade:
            self.manager.vfx.update(obstacles=self.arena.obstacles)
            return

        self.manager.world_clock.update()
        self.manager.match_in_progress = True

        all_units = [self.player] + [u for u, _d in self.residents]
        self.manager.all_units.empty()
        self.manager.all_units.add(all_units)

        self.player.run_combat_ai(all_units, self.arena.obstacles,
                                  manager=self.manager)
        self.player.update(self.arena.obstacles, self.manager)

        for unit, data in self.residents:
            self._update_resident(unit, data)
            unit.update(self.arena.obstacles, self.manager)

        self.manager.vfx.update(obstacles=self.arena.obstacles)
        self._update_camera()

        if self.banner_timer > 0:
            self.banner_timer -= 1

    # ------------------------------------------------------------------
    def draw(self, screen):
        offset = (self.camera_x, self.camera_y)
        all_units = [self.player] + [u for u, _d in self.residents]

        self.arena.draw_background(screen, offset)
        self.manager.vfx.draw_floor(screen, offset)

        # Lattiapassi: matot/romut/halkeamat aina yksiköiden alle
        solids = []
        for p in self.arena.props:
            if getattr(p, "is_flat", False):
                screen.blit(p.image, (p.image_pos[0] - offset[0],
                                      p.image_pos[1] - offset[1]))
            else:
                solids.append(p)

        renderables = solids + all_units
        renderables.sort(key=lambda x: x.rect.bottom)
        for obj in renderables:
            if hasattr(obj, "draw_on_screen"):
                obj.draw_on_screen(screen, offset)
            elif getattr(obj, "image", None):
                screen.blit(obj.image, (obj.rect.x - offset[0],
                                        obj.rect.y - offset[1]))

        self.manager.vfx.draw_top(screen, offset)
        self._draw_ambience(screen, offset)
        self._draw_morale_chips(screen, offset)
        self._draw_header(screen)
        self._draw_prompt(screen, offset)
        if self.show_upgrade:
            self._draw_upgrade_panel(screen)
        if self.banner_timer > 0 and self.banner:
            surf = font_main.render(self.banner, True, GOLD_COLOR)
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, 130))
        if self.player:
            self.player.draw_hud(screen)
        self.draw_editor(screen)

    def _draw_ambience(self, screen, offset):
        """Sisätilan tunnelma: hämärä + takan/kynttilän lämmin valo."""
        lvl = self.arena.level
        self._overlay.fill((8, 8, 16, 110 if lvl == 1 else 70))
        if self.arena.hearth and self.arena.hearth.lit:
            fr = self.arena.hearth.flame_rect()
            fx = fr.centerx - offset[0]
            fy = fr.centery - offset[1]
            flicker = random.randint(-6, 6)
            for radius, alpha in ((320 + flicker, 40), (210 + flicker, 15),
                                  (120, 0)):
                pygame.draw.circle(self._overlay, (8, 8, 16, alpha),
                                   (fx, fy), radius)
            # Liekki itse
            for i in range(3):
                w = 16 - i * 4
                h = 26 - i * 6 + random.randint(-3, 3)
                col = [(226, 120, 40), (250, 180, 60), (255, 230, 130)][i]
                pygame.draw.ellipse(screen, col,
                                    (fx - w // 2, fy - h + 14, w, h))
        # Kynttilänvalo pöydällä (taso 2+)
        if lvl >= 2:
            t = self.arena.table.rect
            tx = t.centerx - offset[0]
            ty = t.top - offset[1]
            pygame.draw.circle(self._overlay, (8, 8, 16, 30), (tx, ty), 180)
        screen.blit(self._overlay, (0, 0))

    def _draw_morale_chips(self, screen, offset):
        for unit, _data in self.residents:
            m = int(getattr(unit, "morale", 50))
            x = unit.rect.centerx - offset[0]
            y = unit.rect.top - offset[1] - 34
            col = ((220, 90, 80) if m < 35 else
                   (222, 186, 92) if m < 65 else (130, 220, 140))
            chip = pygame.Rect(x - 26, y, 52, 16)
            pygame.draw.rect(screen, (20, 20, 26), chip, border_radius=8)
            pygame.draw.rect(screen, col, chip, 1, border_radius=8)
            surf = font_small.render(f"{m}", True, col)
            screen.blit(surf, surf.get_rect(center=chip.center))

    def _draw_header(self, screen):
        lvl = self.arena.level
        used = 1 + sum(1 for u in self.manager.my_team if not u.is_dead)
        total = BUNKS_PER_LEVEL[lvl]
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 330, 16, 660, 54)
        pygame.draw.rect(screen, (15, 17, 22), panel, border_radius=10)
        pygame.draw.rect(screen, (170, 140, 85), panel, 2, border_radius=10)
        draw_text(f"TEAM BARRACKS - {LEVEL_NAMES[lvl]} (Lv {lvl})",
                  font_main, GOLD_COLOR, screen, panel.x + 18, panel.y + 14)
        occ = f"Bunks {used}/{total}"
        col = (220, 120, 100) if used >= total else (180, 220, 180)
        surf = font_small.render(occ, True, col)
        screen.blit(surf, (panel.right - surf.get_width() - 18, panel.y + 18))

    def _draw_prompt(self, screen, offset):
        if self.manager.active_dialogue or self.show_upgrade:
            return
        kind, obj, _d = self._nearest_interactable()
        if not kind:
            return
        labels = {
            "talk": lambda o: f"E - Talk with {o.name}",
            "sleep": lambda o: "E - Sleep until morning",
            "desk": lambda o: "E - Team ledger (roster & gear)",
            "plans": lambda o: "E - Barracks upgrade plans",
            "leave": lambda o: "E - Leave the barracks",
        }
        text = labels[kind](obj)
        if kind == "talk":
            oy = obj.rect.top - 46
            ox = obj.rect.centerx
        elif kind == "leave":
            ox, oy = obj.centerx, obj.top - 40
        else:
            ox, oy = obj.rect.centerx, obj.rect.top - 30
        surf = font_small.render(text, True, WHITE)
        x = ox - offset[0] - surf.get_width() // 2
        y = oy - offset[1]
        bg = pygame.Rect(x - 10, y - 6, surf.get_width() + 20,
                         surf.get_height() + 12)
        pygame.draw.rect(screen, (15, 17, 22), bg, border_radius=8)
        pygame.draw.rect(screen, (170, 140, 85), bg, 1, border_radius=8)
        screen.blit(surf, (x, y))

    def _draw_upgrade_panel(self, screen):
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 170))
        screen.blit(shade, (0, 0))
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 380, SCREEN_HEIGHT // 2 - 260,
                            760, 520)
        pygame.draw.rect(screen, (24, 24, 30), panel, border_radius=14)
        pygame.draw.rect(screen, GOLD_COLOR, panel, 3, border_radius=14)
        lvl = self._level()
        draw_text("BARRACKS UPGRADE PLANS", font_main, GOLD_COLOR, screen,
                  panel.x + 34, panel.y + 26)
        draw_text(f"Current: {LEVEL_NAMES[lvl]} (Lv {lvl}) - "
                  f"{BUNKS_PER_LEVEL[lvl]} bunks", font_small, WHITE,
                  screen, panel.x + 34, panel.y + 74)

        nxt = lvl + 1
        cost = UPGRADE_COSTS.get(nxt)
        self._upgrade_btn = None
        if not cost:
            draw_text("The hall is complete. Your champions live in style.",
                      font_small, (170, 230, 170), screen,
                      panel.x + 34, panel.y + 130)
        else:
            perks = {
                2: ["+2 bunks (8 total) - room for more fighters",
                    "A lit hearth and proper furnishings",
                    "The team rests easier (better morale from sleep)"],
                3: ["+2 bunks (10 total)",
                    "Trophy shelf, banners and a training dummy",
                    "A hall worthy of champions"],
            }[nxt]
            draw_text(f"Next: {LEVEL_NAMES[nxt]} (Lv {nxt})", font_main,
                      WHITE, screen, panel.x + 34, panel.y + 124)
            y = panel.y + 170
            for line in perks:
                draw_text(f"- {line}", font_small, (214, 201, 145), screen,
                          panel.x + 44, y)
                y += 30
            y += 16
            draw_text("COST:", font_small, GRAY, screen, panel.x + 34, y)
            y += 28
            gold_ok = self.manager.gold >= cost["gold"]
            draw_text(f"{format_money(cost['gold'])}", font_small,
                      (130, 220, 140) if gold_ok else (220, 120, 100),
                      screen, panel.x + 44, y)
            y += 28
            for name, need in cost.items():
                if name == "gold":
                    continue
                have = self.manager.inventory.get(name, 0)
                ok = have >= need
                draw_text(f"{name}: {have}/{need}", font_small,
                          (130, 220, 140) if ok else (220, 120, 100),
                          screen, panel.x + 44, y)
                y += 28
            btn = pygame.Rect(panel.centerx - 140, panel.bottom - 92, 280, 52)
            pygame.draw.rect(screen, (65, 135, 80), btn, border_radius=8)
            pygame.draw.rect(screen, WHITE, btn, 2, border_radius=8)
            surf = font_main.render("BUILD (ENTER)", True, WHITE)
            screen.blit(surf, surf.get_rect(center=btn.center))
            self._upgrade_btn = btn
        if self.upgrade_feedback:
            draw_text(self.upgrade_feedback, font_small, (255, 190, 120),
                      screen, panel.x + 34, panel.bottom - 36)
        draw_text("ESC to close", font_small, GRAY, screen,
                  panel.x + 34, panel.bottom - 66 if not self.upgrade_feedback
                  else panel.bottom - 130)
