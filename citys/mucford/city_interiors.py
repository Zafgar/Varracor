# citys/mucford/city_interiors.py
"""Kaupungin käveltävät sisätilat: Arena Hall ja Town Hallin aula.

Arena Hall (Shanty Yardin portin takana): liigatiski (LEAGUE), Odds-Makerin
vedonlyöntikoju (panosta oman tiimin seuraavaan liigamatsiin), omat vartijat
ovella ja kilpailijatiimien edustajia loungessa (asenteellinen dialogi).

Town Hallin aula: kirjurin tiski (SPONSORS), mainetaulu (REPUTATION) ja
virkailijoita juttelemassa.

Grafiikka on koodipiirrettyä placeholderia (oikeat kuvat voi pudottaa
assets/tiles/interiors/-polkuihin, ks. MISSING_ASSETS.md).
"""
import math
import random

import pygame

from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, GOLD_COLOR, WHITE, GRAY,
                      GREEN)
from menus.gameplay_screen import GameplayScreen
from sound_manager import sound_system
from systems import keybinds
from ui_kit import draw_text, font_main, font_small, format_money
from assets.tiles.prop import Prop
from vfx import VFXManager

WALL = 44
DOOR_W = 150


class _Furniture(Prop):
    def __init__(self, x, y, w, h, img_path=None, collision_rect=None):
        super().__init__(x, y, w, h, img_path=img_path,
                         collision_rect=collision_rect)
        self.has_shadow = False


class Counter(_Furniture):
    """Tiski (liigatiski / kirjurin pöytä)."""

    def __init__(self, x, y, w=260, label_color=(150, 60, 55)):
        super().__init__(x, y, w, 110,
                         img_path="assets/tiles/interiors/counter.png",
                         collision_rect=pygame.Rect(x, y + 30, w, 74))
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((w, 110), pygame.SRCALPHA)
            pygame.draw.rect(s, (104, 78, 48), (0, 26, w, 74), border_radius=8)
            pygame.draw.rect(s, (44, 32, 20), (0, 26, w, 74), 3, border_radius=8)
            pygame.draw.rect(s, (126, 96, 60), (0, 26, w, 18),
                             border_top_left_radius=8, border_top_right_radius=8)
            # Liina + kirja
            pygame.draw.rect(s, label_color, (w // 2 - 40, 30, 80, 60))
            pygame.draw.rect(s, (222, 214, 190), (w // 2 - 24, 40, 48, 34))
            pygame.draw.line(s, (90, 80, 70), (w // 2, 40), (w // 2, 74), 2)
            self.image = s


class OddsBoard(_Furniture):
    """Vedonlyöntikoju taululla."""

    def __init__(self, x, y):
        super().__init__(x, y, 200, 170,
                         img_path="assets/tiles/interiors/odds_board.png",
                         collision_rect=pygame.Rect(x, y + 110, 200, 56))
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((200, 170), pygame.SRCALPHA)
            # Taulu
            pygame.draw.rect(s, (34, 30, 26), (10, 0, 180, 104), border_radius=6)
            pygame.draw.rect(s, (196, 164, 90), (10, 0, 180, 104), 3, border_radius=6)
            for i, (txt_w, col) in enumerate([(90, (222, 186, 92)),
                                              (120, (200, 200, 210)),
                                              (70, (222, 186, 92)),
                                              (100, (200, 200, 210))]):
                pygame.draw.line(s, col, (24, 20 + i * 22),
                                 (24 + txt_w, 20 + i * 22), 3)
            # Koju
            pygame.draw.rect(s, (104, 78, 48), (0, 112, 200, 54), border_radius=8)
            pygame.draw.rect(s, (44, 32, 20), (0, 112, 200, 54), 3, border_radius=8)
            pygame.draw.circle(s, (222, 186, 92), (170, 138), 12)
            pygame.draw.circle(s, (44, 32, 20), (170, 138), 12, 2)
            self.image = s


class TrophyCase(_Furniture):
    def __init__(self, x, y):
        super().__init__(x, y, 220, 120,
                         img_path="assets/tiles/interiors/trophy_case.png",
                         collision_rect=pygame.Rect(x, y + 70, 220, 46))
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((220, 120), pygame.SRCALPHA)
            pygame.draw.rect(s, (70, 56, 40), (0, 10, 220, 110), border_radius=8)
            pygame.draw.rect(s, (150, 190, 210, 90), (12, 22, 196, 66),
                             border_radius=6)
            pygame.draw.polygon(s, (222, 186, 92), [(50, 74), (70, 74), (64, 40), (56, 40)])
            pygame.draw.circle(s, (170, 120, 70), (110, 60), 12)
            pygame.draw.circle(s, (150, 150, 165), (165, 58), 10)
            self.image = s


class Bench(_Furniture):
    def __init__(self, x, y, w=180):
        super().__init__(x, y, w, 56,
                         img_path="assets/tiles/interiors/bench.png",
                         collision_rect=pygame.Rect(x, y + 16, w, 36))
        if self.image.get_at((0, 0)) == (100, 100, 100, 255):
            s = pygame.Surface((w, 56), pygame.SRCALPHA)
            pygame.draw.rect(s, (110, 84, 52), (0, 12, w, 24), border_radius=6)
            pygame.draw.rect(s, (44, 32, 20), (0, 12, w, 24), 2, border_radius=6)
            for lx in (14, w - 22):
                pygame.draw.rect(s, (70, 52, 34), (lx, 34, 10, 20))
            self.image = s


class _Wall(Prop):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, max(1, w), max(1, h))
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.image_pos = (x, y)
        self.rect = pygame.Rect(x, y, w, h)
        self.has_shadow = False


class _InteriorArena:
    """Kevyt sisätila-areena GameplayScreen-rajapinnalla."""

    def __init__(self, width, height, floor=(88, 68, 46), wall=(112, 94, 72),
                 banner_colors=()):
        self.width = width
        self.height = height
        self.vfx = VFXManager()
        self.props = []
        self.obstacles = []
        self._floor_col = floor
        self._wall_col = wall
        self._banner_colors = banner_colors
        self.door_rect = pygame.Rect(width // 2 - DOOR_W // 2,
                                     height - WALL - 10, DOOR_W, WALL + 20)
        self._background = None
        d = self.door_rect
        self.props.extend([
            _Wall(0, 0, width, WALL + 50),
            _Wall(0, 0, WALL, height),
            _Wall(width - WALL, 0, WALL, height),
            _Wall(0, height - WALL, d.left, WALL),
            _Wall(d.right, height - WALL, width - d.right, WALL),
        ])

    def finalize(self):
        self.obstacles = [p for p in self.props if p.rect.w > 0]

    def _render_background(self):
        w, h = self.width, self.height
        bg = pygame.Surface((w, h))
        bg.fill(self._floor_col)
        rng = random.Random(7)
        line = tuple(max(0, c - 12) for c in self._floor_col)
        # Kivilaatta/lankkukuvio
        for py in range(0, h, 52):
            pygame.draw.line(bg, line, (0, py), (w, py), 1)
            for px in range((py // 52) % 2 * 26, w, 52):
                pygame.draw.line(bg, line, (px, py), (px, py + 52), 1)
        for _ in range(30):
            px, py = rng.randint(40, w - 100), rng.randint(90, h - 90)
            pygame.draw.ellipse(bg, line, (px, py, rng.randint(20, 60),
                                           rng.randint(8, 20)))
        # Seinät
        pygame.draw.rect(bg, self._wall_col, (0, 0, w, WALL + 50))
        pygame.draw.rect(bg, self._wall_col, (0, 0, WALL, h))
        pygame.draw.rect(bg, self._wall_col, (w - WALL, 0, WALL, h))
        pygame.draw.rect(bg, self._wall_col, (0, h - WALL, w, WALL))
        pygame.draw.rect(bg, (36, 28, 22), (0, 0, w, h), 6)
        for px in range(0, w, 88):
            pygame.draw.line(bg, tuple(max(0, c - 22) for c in self._wall_col),
                             (px, 0), (px, WALL + 50), 2)
        # Liput yläseinälle
        for i, fx in enumerate(range(int(w * 0.12), int(w * 0.9), 240)):
            if not self._banner_colors:
                break
            col = self._banner_colors[i % len(self._banner_colors)]
            pygame.draw.polygon(bg, col, [(fx, 6), (fx + 52, 6), (fx + 26, 84)])
            pygame.draw.polygon(bg, (40, 30, 22),
                                [(fx, 6), (fx + 52, 6), (fx + 26, 84)], 2)
        # Oviaukko
        d = self.door_rect
        pygame.draw.rect(bg, (30, 24, 18), (d.x, h - WALL, d.w, WALL))
        pygame.draw.rect(bg, (120, 100, 70), (d.x, h - WALL, d.w, 8))
        self._background = bg

    def draw_background(self, screen, offset=(0, 0)):
        if self._background is None:
            self._render_background()
        screen.blit(self._background, (-offset[0], -offset[1]))

    def update(self, manager=None):
        pass


class _InteriorMenuBase(GameplayScreen):
    """Yhteinen runko käveltäville sisätiloille (ovi, NPC:t, promptit)."""

    TITLE = "INTERIOR"
    OVERLAY_ALPHA = 60

    def __init__(self, manager):
        super().__init__(manager)
        self.hall_npcs = []      # (unit, kind)
        self._overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                       pygame.SRCALPHA)
        self._city_return_pos = None
        self._keep_positions = False

    # Alaluokat: rakenna areena + NPC:t
    def _build(self):
        raise NotImplementedError

    def on_enter(self):
        super().on_enter()
        self.player = self.manager.player_character
        if self._keep_positions and self.arena is not None:
            self._keep_positions = False
        else:
            self._city_return_pos = self.player.rect.center
            self._build()
            door = self.arena.door_rect
            self.player.rect.centerx = door.centerx
            self.player.rect.bottom = door.top - 10
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx
        self._update_camera()

    def _make_npc(self, name, race, x, y, kind):
        from units.villager import Villager
        npc = Villager(name, race, x, y, team_color=GREEN)
        npc.name = name  # Villager lisää job-liitteen; pidetään puhdas nimi
        self.hall_npcs.append((npc, kind))
        return npc

    def _nearest_interactable(self):
        px, py = self.player.rect.centerx, self.player.rect.centery
        best = (None, None, 1e9)

        def consider(kind, obj, ox, oy, radius):
            nonlocal best
            d = math.hypot(ox - px, oy - py)
            if d < radius and d < best[2]:
                best = (kind, obj, d)

        for unit, kind in self.hall_npcs:
            consider(kind, unit, unit.rect.centerx, unit.rect.centery, 95)
        for kind, prop, radius in self._prop_interactables():
            consider(kind, prop, prop.rect.centerx, prop.rect.centery, radius)
        door = self.arena.door_rect
        consider("leave", door, door.centerx, door.top, 110)
        return best

    def _prop_interactables(self):
        return []

    def _prompt_label(self, kind, obj):
        return None

    def _run_interaction(self, kind, obj):
        return False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and \
                event.key in keybinds.keys_for("interact"):
            if self.manager.active_dialogue or self.manager.dialogue_cooldown > 0:
                return super().handle_event(event)
            kind, obj, _d = self._nearest_interactable()
            if kind == "leave":
                if self._city_return_pos:
                    self.player.rect.center = self._city_return_pos
                self.next_state = "muckford_city"
                sound_system.play_sound("click")
                return
            if kind and self._run_interaction(kind, obj):
                return
        super().handle_event(event)

    def update(self):
        if self.manager.paused:
            return
        # BaseMenu (editor)
        from menus.base_menu import BaseMenu
        BaseMenu.update(self)
        if self.manager.active_dialogue:
            self.manager.vfx.update(obstacles=self.arena.obstacles)
            return
        self.manager.match_in_progress = True
        all_units = [self.player] + [u for u, _k in self.hall_npcs]
        self.manager.all_units.empty()
        self.manager.all_units.add(all_units)
        self.player.run_combat_ai(all_units, self.arena.obstacles,
                                  manager=self.manager)
        self.player.update(self.arena.obstacles, self.manager)
        for unit, _kind in self.hall_npcs:
            unit.animation_state = "idle"
            unit.update(self.arena.obstacles, self.manager)
        self.manager.vfx.update(obstacles=self.arena.obstacles)
        self._update_camera()

    def draw(self, screen):
        offset = (self.camera_x, self.camera_y)
        all_units = [self.player] + [u for u, _k in self.hall_npcs]
        self.arena.draw_background(screen, offset)
        self.manager.vfx.draw_floor(screen, offset)
        renderables = [p for p in self.arena.props] + all_units
        renderables.sort(key=lambda x: x.rect.bottom)
        for obj in renderables:
            if hasattr(obj, "draw_on_screen"):
                obj.draw_on_screen(screen, offset)
            elif getattr(obj, "image", None):
                screen.blit(obj.image, (obj.rect.x - offset[0],
                                        obj.rect.y - offset[1]))
        self.manager.vfx.draw_top(screen, offset)
        self._overlay.fill((10, 8, 14, self.OVERLAY_ALPHA))
        screen.blit(self._overlay, (0, 0))
        self._draw_header(screen)
        self._draw_prompt(screen, offset)
        self._draw_extra(screen)
        if self.player:
            # HUD häivytetään kun hahmo jää sen taakse
            p_screen_y = self.player.rect.centery - self.camera_y
            hud_surface = getattr(self.manager, "hud_surface", None)
            if p_screen_y > SCREEN_HEIGHT - 200 and hud_surface is not None:
                hud_surface.fill((0, 0, 0, 0))
                self.player.draw_hud(hud_surface)
                hud_surface.set_alpha(90)
                screen.blit(hud_surface, (0, 0))
                hud_surface.set_alpha(255)
            else:
                self.player.draw_hud(screen)
        self.draw_editor(screen)

    def _draw_extra(self, screen):
        pass

    def _draw_header(self, screen):
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 300, 16, 600, 50)
        pygame.draw.rect(screen, (15, 17, 22), panel, border_radius=10)
        pygame.draw.rect(screen, (170, 140, 85), panel, 2, border_radius=10)
        surf = font_main.render(self.TITLE, True, GOLD_COLOR)
        screen.blit(surf, surf.get_rect(center=panel.center))

    def _draw_prompt(self, screen, offset):
        if self.manager.active_dialogue:
            return
        kind, obj, _d = self._nearest_interactable()
        if not kind:
            return
        if kind == "leave":
            text = "E - Leave"
            ox, oy = obj.centerx, obj.top - 40
        else:
            text = self._prompt_label(kind, obj)
            if not text:
                return
            ox, oy = obj.rect.centerx, obj.rect.top - 34
        surf = font_small.render(text, True, WHITE)
        x = ox - offset[0] - surf.get_width() // 2
        y = oy - offset[1]
        bg = pygame.Rect(x - 10, y - 6, surf.get_width() + 20,
                         surf.get_height() + 12)
        pygame.draw.rect(screen, (15, 17, 22), bg, border_radius=8)
        pygame.draw.rect(screen, (170, 140, 85), bg, 1, border_radius=8)
        screen.blit(surf, (x, y))


# ======================================================================
# ARENA HALL
# ======================================================================

BET_OPTIONS = (20, 50, 100)
BET_PAYOUT = 2.0


class ArenaHallMenu(_InteriorMenuBase):
    TITLE = "SHANTY YARD - ARENA HALL"
    OVERLAY_ALPHA = 55

    def _build(self):
        self.hall_npcs = []
        a = _InteriorArena(2000, 1200, floor=(96, 82, 62), wall=(104, 86, 66),
                           banner_colors=((140, 44, 44), (196, 164, 90)))
        w, h = a.width, a.height
        # Liigatiski ylös keskelle
        self.league_desk = Counter(w // 2 - 130, WALL + 90,
                                   label_color=(150, 60, 55))
        a.props.append(self.league_desk)
        # Vedonlyöntikoju oikealle
        self.odds_stand = OddsBoard(w - WALL - 300, h // 2 - 160)
        a.props.append(self.odds_stand)
        # Palkintovitriini vasemmalle + penkit loungeen
        a.props.append(TrophyCase(WALL + 60, h // 2 - 220))
        a.props.append(Bench(WALL + 90, h // 2 + 60))
        a.props.append(Bench(WALL + 90, h // 2 + 220))
        a.finalize()
        self.arena = a

        # Liigaisäntä tiskille
        self._make_npc("Bram Mudhand", "Dwarf",
                       self.league_desk.rect.centerx,
                       self.league_desk.rect.top - 26, "league_host")
        # Vedonvälittäjä kojulle
        self._make_npc("Odds-Maker Vint", "Goblin",
                       self.odds_stand.rect.centerx - 60,
                       self.odds_stand.rect.centery + 10, "bookie")
        # Vartijat oven pieliin
        d = a.door_rect
        self._make_npc("Yard Guard", "Human", d.left - 70, d.top - 60, "guard")
        self._make_npc("Yard Guard", "Orc", d.right + 70, d.top - 60, "guard")
        # Kilpailijatiimien edustajat loungeen
        try:
            from npc.rival_gladiator_npc import RIVAL_GLADIATORS
            races = {"arrogant": "Elf", "gruff": "Dwarf", "cagey": "Goblin",
                     "warm": "Human"}
            for i, (rname, team, attitude) in enumerate(RIVAL_GLADIATORS[:3]):
                rep = self._make_npc(rname, races.get(attitude, "Human"),
                                     WALL + 200, h // 2 + 40 + i * 150, "rival")
                rep.rival_info = (rname, team, attitude)
        except Exception:
            pass

    def _prop_interactables(self):
        return [("league_desk", self.league_desk, 130),
                ("betting", self.odds_stand, 130)]

    def _prompt_label(self, kind, obj):
        return {
            "league_desk": "E - League board (matches & standings)",
            "league_host": "E - League board (matches & standings)",
            "betting": "E - Place a wager",
            "bookie": "E - Place a wager",
            "guard": "E - Talk",
            "rival": f"E - Talk with {getattr(obj, 'name', 'rival')}",
        }.get(kind)

    def _run_interaction(self, kind, obj):
        if kind in ("league_desk", "league_host"):
            self.manager.league_return_state = "arena_hall"
            self._keep_positions = True
            self.next_state = "league"
            sound_system.play_sound("click")
            return True
        if kind in ("betting", "bookie"):
            self._open_bet_dialogue()
            return True
        if kind == "guard":
            self.manager.start_dialogue(
                obj, "Weapons stay sheathed in the hall, Commander. "
                     "The Yard's sand is where debts get settled.",
                options=[{"text": "Understood.", "action": "close_dialogue"}])
            return True
        if kind == "rival":
            info = getattr(obj, "rival_info", None)
            if info:
                self.manager.open_rival_dialogue(info,
                                                 return_state="arena_hall")
                self._keep_positions = True
                self.next_state = "dialogue_active"
            return True
        return False

    # -------------------- Vedonlyönti --------------------
    def _open_bet_dialogue(self):
        bookie = next((u for u, k in self.hall_npcs if k == "bookie"), None)
        bet = getattr(self.manager, "active_bet", None)
        if bet:
            self.manager.start_dialogue(
                bookie,
                f"You already have {format_money(bet['amount'])} riding on "
                f"your next league match. Win it, and I pay double.",
                options=[{"text": "I'll hold my ticket.",
                          "action": "close_dialogue"}])
            return
        options = []
        for amount in BET_OPTIONS:
            options.append({
                "text": f"Bet {format_money(amount)} on my next league win "
                        f"(pays x{BET_PAYOUT:.0f})",
                "action": f"hall_bet_{amount}",
            })
        options.append({"text": "Not today.", "action": "close_dialogue"})
        self.manager.dialogue_action_handler = self._on_bet_action
        self.manager.start_dialogue(
            bookie,
            "Vint grins over his slate. Simple terms, Commander: coin down, "
            "your team wins its next LEAGUE match, I pay double. They lose, "
            "the Yard eats your stake.",
            options=options)

    def _on_bet_action(self, action):
        manager = self.manager
        manager.dialogue_action_handler = None
        if isinstance(action, str) and action.startswith("hall_bet_"):
            amount = int(action.rsplit("_", 1)[1])
            if manager.gold < amount:
                manager.vfx.show_damage(
                    self.player.rect.centerx, self.player.rect.top - 30,
                    "Not enough coin for that wager.", color=(255, 150, 120))
                sound_system.play_sound("error")
            else:
                manager.gold -= amount
                manager.active_bet = {"amount": amount}
                manager.vfx.show_damage(
                    self.player.rect.centerx, self.player.rect.top - 30,
                    f"Wager placed: {format_money(amount)}",
                    color=(150, 230, 160))
                sound_system.play_sound("coin")
        manager.active_dialogue = None
        manager.dialogue_cooldown = 20

    def on_exit(self):
        super().on_exit()
        # Ei jätetä omaa action-handleria roikkumaan
        if getattr(self.manager, "dialogue_action_handler", None) == \
                self._on_bet_action:
            self.manager.dialogue_action_handler = None

    def _draw_extra(self, screen):
        bet = getattr(self.manager, "active_bet", None)
        if bet:
            chip = pygame.Rect(24, 90, 330, 44)
            pygame.draw.rect(screen, (15, 17, 22), chip, border_radius=9)
            pygame.draw.rect(screen, (196, 164, 90), chip, 2, border_radius=9)
            draw_text(f"Active wager: {format_money(bet['amount'])} "
                      f"(pays x{BET_PAYOUT:.0f})", font_small,
                      (222, 200, 140), screen, chip.x + 14, chip.y + 12)


# ======================================================================
# TOWN HALL
# ======================================================================

class TownHallMenu(_InteriorMenuBase):
    TITLE = "MUCKFORD TOWN HALL"
    OVERLAY_ALPHA = 45

    def _build(self):
        self.hall_npcs = []
        a = _InteriorArena(1600, 1000, floor=(92, 76, 54), wall=(118, 100, 78),
                           banner_colors=((84, 96, 140),))
        w, h = a.width, a.height
        self.clerk_desk = Counter(w // 2 - 130, WALL + 80,
                                  label_color=(84, 96, 140))
        a.props.append(self.clerk_desk)
        self.ledger_board = OddsBoard(w - WALL - 260, h // 2 - 120)
        a.props.append(self.ledger_board)
        a.props.append(Bench(WALL + 80, h // 2 + 40))
        a.props.append(Bench(w - WALL - 260, h - WALL - 160))
        a.finalize()
        self.arena = a

        self._make_npc("Clerk Odessa", "Human",
                       self.clerk_desk.rect.centerx,
                       self.clerk_desk.rect.top - 26, "clerk")
        self._make_npc("Scribe Tull", "Goblin",
                       WALL + 160, h // 2 + 10, "scribe")

    def _prop_interactables(self):
        return [("sponsors", self.clerk_desk, 130),
                ("reputation", self.ledger_board, 130)]

    def _prompt_label(self, kind, obj):
        return {
            "sponsors": "E - Sponsor ledger",
            "clerk": "E - Sponsor ledger",
            "reputation": "E - Standing & reputation",
            "scribe": "E - Talk",
        }.get(kind)

    def _run_interaction(self, kind, obj):
        if kind in ("sponsors", "clerk"):
            self._keep_positions = True
            self.next_state = "sponsors"
            sound_system.play_sound("click")
            return True
        if kind == "reputation":
            self._keep_positions = True
            self.next_state = "reputation"
            sound_system.play_sound("click")
            return True
        if kind == "scribe":
            self.manager.start_dialogue(
                obj, "Every debt, deed and rat tail in Muckford ends up in "
                     "these books. Keep your name on the right pages.",
                options=[{"text": "I'll keep that in mind.",
                          "action": "close_dialogue"}])
            return True
        return False
