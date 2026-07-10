# citys/mucford/mine_road_menu.py
"""
Kaivostie: epäkuolleiden valtaama reitti Muckfordin vanhalle kaivokselle.

- Avautuu vasta kun pelaaja on maksanut velkansa Mardalle (saa avaimen).
- Epäkuolleet ja malmit palautuvat päivittäin (WorldClock).
- Louhinta vaatii hakun (esim. markkinoilta) - IronOre.take_hit hoitaa loput.
- Poistuminen vasemmasta reunasta takaisin kaupunkiin.
"""
import random
import pygame

from settings import *
from menus.gameplay_screen import GameplayScreen
from ui_kit import draw_text, font_main, font_small, GOLD_COLOR, WHITE
from sound_manager import sound_system
from citys.mucford.mine_road_arena import MineRoadArena


class MineRoadMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = MineRoadArena()
        self.undead = []
        self.exit_rect = pygame.Rect(0, 0, 80, self.arena.height)
        self._spawned_day = -1

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx

        # Pelaaja sisään vasemmalta
        self.player = self.manager.player_character
        self.player.rect.centerx = 140
        self.player.rect.centery = self.arena.height // 2
        self.player.facing_right = True
        self._update_camera()

        # Päivittäinen respawn: epäkuolleet ja malmit palaavat
        day = self.manager.world_clock.day
        if day != self._spawned_day:
            self._spawned_day = day
            self.arena.spawn_ores()
            self._spawn_undead()

        sound_system.play_music('assets/music/swamp_theme.mp3')

    def on_exit(self):
        super().on_exit()
        sound_system.stop_music()

    def _spawn_undead(self):
        """Tien sulkenut epäkuolleiden saarto keskitiellä."""
        from units.undead_skeleton import UndeadSkeleton
        from units.undead_zombie import UndeadZombie
        from units.undead_skeleton_archer import UndeadSkeletonArcher

        # Poista mahdolliset vanhat
        for u in self.undead:
            if u in self.manager.all_units:
                self.manager.all_units.remove(u)
        self.undead = []

        path_y = self.arena.height // 2
        blockade_x = self.arena.width // 2
        spawns = [
            (UndeadSkeleton, blockade_x - 80, path_y - 90),
            (UndeadSkeleton, blockade_x + 60, path_y + 80),
            (UndeadZombie, blockade_x, path_y),
            (UndeadZombie, blockade_x + 160, path_y - 60),
            (UndeadSkeletonArcher, blockade_x + 260, path_y + 30),
        ]
        for cls, x, y in spawns:
            u = cls(cls.__name__.replace("Undead", ""), x, y, ENEMY_TEAM)
            self.undead.append(u)

    def _all_units(self):
        units = [self.player]
        units.extend(u for u in self.undead if not u.is_dead)
        # Malmit mukaan, jotta pelaajan lyönnit osuvat niihin
        units.extend(n for n in self.arena.ore_nodes if not n.is_empty)
        return units

    def update(self):
        if self.manager.paused:
            return

        all_units = self._all_units()
        self._update_gameplay(all_units)

        # GameplayScreen pitää match_in_progress-lippua päällä, jolloin
        # add_material ohjaisi louhitut resurssit taistelun loppuruutuun
        # (jota ei täällä ole). Siirretään saalis suoraan reppuun.
        loot = self.manager.round_rewards.get('loot')
        if loot:
            for name, cnt in list(loot.items()):
                self.manager.inventory[name] = self.manager.inventory.get(name, 0) + cnt
            self.manager.round_rewards['loot'] = {}

        # Maailmankello etenee ulkona
        if not self.manager.world_paused:
            self.manager.world_clock.update()

        # Kaatuminen: raahataan takaisin kylään
        if self.player.is_dead:
            self.player.is_dead = False
            self.player.current_hp = max(1, int(self.player.max_hp * 0.3))
            self.manager.vfx.show_damage(self.player.rect.centerx, self.player.rect.top - 30,
                                         "You crawl back to Muckford...", color=(255, 120, 120))
            self.next_state = "muckford_city"
            return

        # Poistuminen vasemmalta
        if self.player.rect.colliderect(self.exit_rect):
            self.next_state = "muckford_city"

    def handle_event(self, event):
        super().handle_event(event)

    def draw(self, screen):
        all_units = self._all_units()
        self._draw_gameplay(screen, all_units)

        # Sää ja vuorokaudenaika (ulkotila)
        self.manager.world_clock.draw_overlays(screen)
        self.manager.world_clock.draw_hud(screen, font_small)

        # Opasteet
        draw_text("< Muckford", font_main, WHITE, screen, 20, SCREEN_HEIGHT // 2)
        alive = sum(1 for u in self.undead if not u.is_dead)
        if alive > 0:
            draw_text(f"Undead block the road! ({alive} left)", font_main,
                      (255, 100, 100), screen, SCREEN_WIDTH // 2 - 180, 100)
        else:
            draw_text("The road is clear... for today.", font_small,
                      (180, 220, 180), screen, SCREEN_WIDTH // 2 - 130, 100)
            ore_left = sum(1 for n in self.arena.ore_nodes if not n.is_empty)
            if ore_left:
                draw_text(f"Iron deposits at the mine mouth: {ore_left}", font_small,
                          GOLD_COLOR, screen, SCREEN_WIDTH // 2 - 150, 130)
