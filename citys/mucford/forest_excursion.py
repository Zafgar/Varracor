# citys/mucford/forest_excursion.py
"""
Toistettava metsäretki kylän eteläportista. Foragointi (Bogwort),
puunkaato ja metsähirviöt (rotat, variksia) jotka droppaavat lootia.
Kytkeytyy Hospice-tehtävään (Bogwort) ja hirviödroppeihin.
"""
import pygame
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_TEAM, ENEMY_TEAM, GREEN, GOLD_COLOR, WHITE, GRAY
from menus.gameplay_screen import GameplayScreen
from ui_kit import draw_text, font_main, font_small
from sound_manager import sound_system
from assets.tiles.prop import Prop
from assets.tiles.muckford_objects import ForestFloor, MuckfordTree
from assets.tiles.forest_objects import ForestBush, ForestGrass
from assets.tiles.muckford_floors import MuckfordFloor
from units.rat import GiantRat
from units.corrupted_crow import CorruptedCrow


class BogwortHerb(Prop):
    """Kerättävä yrtti. E antaa 'Bogwort'ia (Hospice-tehtävä)."""
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32, color=(70, 120, 90))
        self.rect = pygame.Rect(x, y, 32, 32)
        self.is_structure = True
        self.has_shadow = False
        self.harvested = False
        self._draw_herb()

    def _draw_herb(self):
        s = pygame.Surface((32, 32), pygame.SRCALPHA)
        if not self.harvested:
            for dx in (-6, 0, 6):
                pygame.draw.line(s, (60, 140, 90), (16 + dx, 30), (16 + dx * 2, 8), 3)
            pygame.draw.circle(s, (150, 100, 200), (16, 8), 4)
            pygame.draw.circle(s, (150, 100, 200), (8, 14), 3)
            pygame.draw.circle(s, (150, 100, 200), (24, 14), 3)
        else:
            pygame.draw.line(s, (90, 90, 60), (14, 30), (14, 20), 2)
        self.image = s


class ForestExcursionArena:
    def __init__(self):
        self.width = int(SCREEN_WIDTH * 2.0)
        self.height = int(SCREEN_HEIGHT * 2.0)
        self.obstacles = []
        self.props = []
        self.floor_props = []
        self.floor = MuckfordFloor(self.width, self.height)
        self._build()

    def _add(self, prop, blocking=False):
        self.props.append(prop)
        if blocking:
            self.obstacles.append(prop)

    def _build(self):
        w, h = self.width, self.height
        self._add(ForestFloor(0, 0, w, h))
        rng = random.Random(4242)
        # Ruoho
        for _ in range(80):
            self._add(ForestGrass(rng.randint(0, w - 40), rng.randint(0, h - 40)))
        # Puut (törmäävät) ja pensaat
        for _ in range(50):
            tx, ty = rng.randint(60, w - 120), rng.randint(60, h - 160)
            if rng.random() < 0.65:
                self._add(MuckfordTree(tx, ty), blocking=True)
            else:
                self._add(ForestBush(tx, ty + 150))
        # Bogwort-yrtit
        self.herbs = []
        for _ in range(8):
            hx, hy = rng.randint(80, w - 80), rng.randint(80, h - 80)
            herb = BogwortHerb(hx, hy)
            self.herbs.append(herb)
            self._add(herb)

    def update(self, manager):
        pass

    def draw_background(self, screen, offset=(0, 0)):
        self.floor.draw(screen, offset)

    def draw_foreground(self, screen, offset=(0, 0)):
        pass


class ForestExcursionMenu(GameplayScreen):
    """Metsäretki: forage + hunt. Poistu ESC-pausevalikosta tai pohjoisreunasta."""

    def __init__(self, manager):
        super().__init__(manager)
        self.arena = ForestExcursionArena()
        self.monsters = pygame.sprite.Group()
        self.feedback = ""
        self.feedback_timer = 0

    def on_enter(self):
        super().on_enter()
        # Aseta pelaaja eteläreunaan (kylästä tullaan alhaalta)
        self.player.rect.center = (self.arena.width // 2, self.arena.height - 120)
        # Spawnaa metsähirviöt
        self.monsters.empty()
        rng = random.Random()
        for i in range(5):
            mx, my = rng.randint(200, self.arena.width - 200), rng.randint(150, self.arena.height - 400)
            if rng.random() < 0.6:
                mon = GiantRat(f"Forest Rat {i+1}", mx, my, ENEMY_TEAM)
            else:
                mon = CorruptedCrow(f"Crow {i+1}", mx, my, ENEMY_TEAM)
            self.monsters.add(mon)
        self._update_camera()

    def _flash(self, msg):
        self.feedback = msg
        self.feedback_timer = 150

    def handle_event(self, event):
        super().handle_event(event)  # ESC-pause, editor
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self._try_forage()

    def _try_forage(self):
        for herb in getattr(self.arena, "herbs", []):
            if herb.harvested:
                continue
            if self.player.rect.colliderect(herb.rect.inflate(50, 50)):
                herb.harvested = True
                herb._draw_herb()
                # Suoraan reppuun (add_material ohjaisi round_rewardsiin
                # koska match_in_progress on päällä metsäretkellä)
                self.manager.inventory["Bogwort"] = self.manager.inventory.get("Bogwort", 0) + 1
                # Kytkös Hospice-tehtävään
                vt = getattr(self.manager, "village_tasks", None)
                if vt:
                    vt.notify_collect(self.manager, "forest_herbs")
                sound_system.play_sound("recruit")
                self._flash("+1 Bogwort")
                return

    def update(self):
        if self.manager.paused:
            return
        all_units = [self.player] + [m for m in self.monsters if not m.is_dead]
        self._update_gameplay(all_units)

        # Poistu pohjoisreunasta (takaisin kaupunkiin)
        if self.player.rect.top < 20:
            self.manager.match_in_progress = False
            self.next_state = "muckford_city"

        if self.feedback_timer > 0:
            self.feedback_timer -= 1

    def draw(self, screen):
        all_units = [self.player] + [m for m in self.monsters if not m.is_dead]
        self._draw_gameplay(screen, all_units)
        offset = (self.camera_x, self.camera_y)

        # Forage-prompt
        for herb in getattr(self.arena, "herbs", []):
            if not herb.harvested and self.player.rect.colliderect(herb.rect.inflate(50, 50)):
                self.manager._draw_floating_prompt(screen, herb.rect.centerx, herb.rect.top - 20, "E", offset, "Gather Bogwort")
                break

        remaining = sum(1 for h in self.arena.herbs if not h.harvested)
        alive = sum(1 for m in self.monsters if not m.is_dead)
        draw_text(f"Forest Trail   Bogwort left: {remaining}   Beasts: {alive}",
                  font_small, WHITE, screen, 40, 40)
        draw_text("Head north to return to Muckford.", font_small, GRAY, screen, 40, 66)
        if self.feedback_timer > 0:
            draw_text(self.feedback, font_main, GOLD_COLOR, screen, SCREEN_WIDTH // 2 - 40, 100)

        self.manager.draw_ui_overlay(screen, "forest_excursion")
