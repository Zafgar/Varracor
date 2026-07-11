# citys/mucford/mine_cave_menu.py
"""
Kaivoksen sisäosa: pimeä luola. Valo kulkee pelaajan mukana
(soihtuefekti). Vahvemmat epäkuolleet vartioivat syvyyksiä, ja
rubiinisuoni odottaa perimmäisessä nurkassa.
"""
import random
import pygame

from settings import *
from menus.gameplay_screen import GameplayScreen
from ui_kit import draw_text, font_main, font_small, GOLD_COLOR, WHITE
from sound_manager import sound_system
from citys.mucford.mine_cave_arena import MineCaveArena


class MineCaveMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = MineCaveArena()
        self.undead = []
        self.boss = None
        self.exit_rect = pygame.Rect(0, self.arena.height // 2 - 200, 70, 400)
        self._spawned_day = -1
        self._dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.banner = ""
        self.banner_timer = 0

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx

        self.player = self.manager.player_character
        self.player.rect.centerx = 140
        self.player.rect.centery = self.arena.height // 2
        self.player.facing_right = True
        self._update_camera()

        day = self.manager.world_clock.day
        if day != self._spawned_day:
            self._spawned_day = day
            self.arena.spawn_ores()
            self._spawn_undead()

        # --- SYVÄN KAMMION PORTTI (Broodmother) ---
        self._setup_deep_gate()

        sound_system.play_music('assets/music/crypt_theme.mp3')

    def _setup_deep_gate(self):
        """Verkkoseinä + Broodmother, kunnes boss on kaadettu (deed).
        Kaadon jälkeen verkko poissa ja syvä kammio auki pysyvästi."""
        deep_open = self.manager.has_deed("mine_broodmother")
        if deep_open:
            self.arena.remove_web_barrier()
            self.arena.spawn_deep_ores()
            self.boss = None
            return

        # Ei vielä kaadettu: pystytä verkko ja bossi sen eteen
        self.arena.add_web_barrier()
        if self.boss is None or self.boss.is_dead:
            from units.cave_spider import CaveBroodmother
            bx = self.arena.wall_x - 150
            by = self.arena.height // 2
            self.boss = CaveBroodmother("Cave Broodmother", bx, by, ENEMY_TEAM)
            self.manager.enemy_team.add(self.boss)
            self.manager.all_units.add(self.boss)

    def on_exit(self):
        super().on_exit()
        sound_system.stop_music()
        # Siivoa boss + Spiderlingit enemy_teamista, etteivät vuoda muihin
        # tiloihin. Jos bossia ei kaadettu, se palaa tuoreena ensi käynnillä.
        for e in list(self.manager.enemy_team):
            self.manager.enemy_team.remove(e)
            if e in self.manager.all_units:
                self.manager.all_units.remove(e)
        self.boss = None

    def _spawn_undead(self):
        """Syvyyksien vartijat: vahvempia kuin tien saarto."""
        from units.undead_skeleton import UndeadSkeleton
        from units.undead_zombie import UndeadZombie
        from units.undead_skeleton_archer import UndeadSkeletonArcher

        for u in self.undead:
            if u in self.manager.all_units:
                self.manager.all_units.remove(u)
        self.undead = []

        w, h = self.arena.width, self.arena.height
        spawns = [
            (UndeadSkeleton, w * 0.45, h * 0.3),
            (UndeadSkeleton, w * 0.5, h * 0.7),
            (UndeadZombie, w * 0.65, h * 0.5),
            (UndeadSkeletonArcher, w * 0.8, h * 0.35),
            (UndeadSkeletonArcher, w * 0.85, h * 0.65),
        ]
        for cls, x, y in spawns:
            u = cls(cls.__name__.replace("Undead", ""), int(x), int(y), ENEMY_TEAM)
            # Syvyyksien vartijat ovat sitkeämpiä
            u.max_hp = int(u.max_hp * 1.4)
            u.current_hp = u.max_hp
            u.strength = int(getattr(u, "strength", 5) * 1.2)
            self.undead.append(u)

    def _leashed_undead(self):
        """Epäkuolleet heräävät vasta kun pelaaja tulee lähelle
        (eivät ryntää kartan poikki heti sisään astuttaessa)."""
        import math as _math
        px, py = self.player.rect.center
        active = []
        for u in self.undead:
            if u.is_dead:
                continue
            d = _math.hypot(u.rect.centerx - px, u.rect.centery - py)
            if d < 550 or getattr(u, "_aggro", False):
                u._aggro = True
                active.append(u)
        return active

    def _all_units(self):
        units = [self.player]
        units.extend(self._leashed_undead())
        # Broodmother + sen kutsumat Spiderlingit (enemy_teamissa)
        for e in self.manager.enemy_team:
            if not e.is_dead:
                units.append(e)
        units.extend(n for n in self.arena.ore_nodes if not n.is_empty)
        return units

    def update(self):
        if self.manager.paused:
            return

        all_units = self._all_units()
        self._update_gameplay(all_units)

        # Broodmotherin kaato aukaisee syvän kammion pysyvästi
        if self.boss is not None and self.boss.is_dead:
            self.manager.record_deed(
                "mine_broodmother",
                "slew the Cave Broodmother and opened the deep mine")
            self.arena.remove_web_barrier()
            self.arena.spawn_deep_ores()
            self.boss = None
            self.banner = "The web tears away — the deep mine is open!"
            self.banner_timer = 360
            self.manager.vfx.show_damage(self.player.rect.centerx, self.player.rect.top - 40,
                                         "DEEP MINE UNLOCKED", color=(210, 215, 255))

        if self.banner_timer > 0:
            self.banner_timer -= 1

        # Saalis suoraan reppuun (ks. mine_road_menu, sama syy)
        loot = self.manager.round_rewards.get('loot')
        if loot:
            for name, cnt in list(loot.items()):
                self.manager.inventory[name] = self.manager.inventory.get(name, 0) + cnt
            self.manager.round_rewards['loot'] = {}

        if self.player.is_dead:
            self.player.is_dead = False
            self.player.current_hp = max(1, int(self.player.max_hp * 0.3))
            self.manager.vfx.show_damage(self.player.rect.centerx, self.player.rect.top - 30,
                                         "You crawl out of the dark...", color=(255, 120, 120))
            self.next_state = "mine_road"
            return

        if self.player.rect.colliderect(self.exit_rect):
            self.next_state = "mine_road"

    def _draw_darkness(self, screen):
        """Luolan pimeys: valokehä pelaajan (soihdun) ympärillä."""
        self._dark_overlay.fill((5, 5, 12, 230))
        px = self.player.rect.centerx - self.camera_x
        py = self.player.rect.centery - self.camera_y
        # Lepattava soihtu
        flicker = random.randint(-8, 8)
        for radius, alpha in ((300 + flicker, 160), (220 + flicker, 90),
                              (150 + flicker, 40), (90, 0)):
            pygame.draw.circle(self._dark_overlay, (5, 5, 12, alpha), (px, py), radius)
        # Pieni valo myös rubiineista
        for node in self.arena.ore_nodes:
            if getattr(node, "resource_name", "") == "Chipped Ruby" and not node.is_empty:
                nx = node.rect.centerx - self.camera_x
                ny = node.rect.centery - self.camera_y
                if -100 < nx < SCREEN_WIDTH + 100 and -100 < ny < SCREEN_HEIGHT + 100:
                    pygame.draw.circle(self._dark_overlay, (60, 10, 20, 120), (nx, ny), 70)
        screen.blit(self._dark_overlay, (0, 0))

    def draw(self, screen):
        all_units = self._all_units()
        self._draw_gameplay(screen, all_units)
        self._draw_darkness(screen)

        draw_text("< Mine Road", font_main, WHITE, screen, 20, SCREEN_HEIGHT // 2)
        alive = sum(1 for u in self.undead if not u.is_dead)
        if alive > 0:
            draw_text(f"Something stirs in the dark... ({alive})", font_small,
                      (255, 120, 120), screen, SCREEN_WIDTH // 2 - 150, 90)

        if self.boss is not None and not self.boss.is_dead:
            draw_text("A CAVE BROODMOTHER guards the deep chamber. (Fire burns spiders)",
                      font_small, (200, 160, 220), screen, SCREEN_WIDTH // 2 - 260, 60)

        if self.banner_timer > 0:
            surf = font_main.render(self.banner, True, (210, 215, 255))
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, 120))
