# menus/rift_site_menu.py
"""Rift-invaasioalueet (pelitesti 20).

Maailmankartalta pääsee kolmelle riivatulle alueelle (suo, hautausmaa,
rämemetsä), joihin on auennut ISO Vortex-repeämä. Repeämän haastaminen
(E) käynnistää wave-invaasion: alueen teeman mukaisia olentoja vyöryy
repeämästä aalloittain, ja viimeisen aallon jälkeen saapuu FINAL BOSS -
jättimäinen, buffattu versio taistelluista olennoista (bossipalkki).
Kun boss kaatuu, repeämän voi sinetöidä (keräyskanava) - palkkiona
Vortex-kristalleja Commanderin VORTEX-puuhun. Paluukyltti vie takaisin
maailmankartalle (ja sitä kautta sinne mistä tuli).

Pelaajan kaatuminen keskeyttää invaasion: hänet raahataan alueen
sisäänkäynnille ja repeämä rauhoittuu takaisin lepotilaan.
"""
import math
import random

import pygame

from menus.gameplay_screen import GameplayScreen
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, ENEMY_TEAM, GOLD_COLOR, WHITE, GRAY
from sound_manager import sound_system
from systems import keybinds
from ui_kit import draw_text, font_title, font_main, font_small

ARENA_W, ARENA_H = 2400, 1500

# Teemat: lattia, koristeväri, aallot (luokkanimi, määrä) ja boss
THEMES = {
    "marsh": {
        "title": "WHISPER MARSH - RIFT BREACH",
        "floor": (44, 52, 40),
        "accent": (30, 60, 48),
        "waves": [
            [("BogLeech", 3)],
            [("BogLeech", 3), ("GiantFrog", 2)],
            [("BogLeech", 4), ("GiantFrog", 3)],
        ],
        "boss": ("BogLeech", "Broodmother of the Breach"),
    },
    "graveyard": {
        "title": "DROWNED GRAVEYARD - RIFT BREACH",
        "floor": (48, 46, 52),
        "accent": (60, 58, 70),
        "waves": [
            [("UndeadSkeleton", 3)],
            [("UndeadSkeleton", 3), ("UndeadZombie", 2)],
            [("UndeadSkeleton", 3), ("UndeadZombie", 2),
             ("UndeadSkeletonArcher", 2)],
        ],
        "boss": ("UndeadZombie", "Grave Tyrant"),
    },
    "bogwood": {
        "title": "BOGWOOD THICKET - RIFT BREACH",
        "floor": (46, 50, 36),
        "accent": (58, 66, 44),
        "waves": [
            [("GiantRat", 4)],
            [("GiantRat", 4), ("CorruptedCrow", 2)],
            [("GiantRat", 4), ("RatRider", 2), ("CorruptedCrow", 2)],
        ],
        "boss": ("RatRider", "Rift-Rider Alpha"),
    },
}

# Maailmankartan sijainti-id -> teema
LOCATION_THEMES = {
    "rift_whisper_marsh": "marsh",
    "rift_drowned_graveyard": "graveyard",
    "rift_bogwood": "bogwood",
}


def _unit_class(name):
    from units.bog_leech import BogLeech
    from units.giant_frog import GiantFrog
    from units.undead_skeleton import UndeadSkeleton
    from units.undead_zombie import UndeadZombie
    from units.undead_skeleton_archer import UndeadSkeletonArcher
    from units.rat import GiantRat
    from units.rat_rider import RatRider
    from units.corrupted_crow import CorruptedCrow
    return {
        "BogLeech": BogLeech, "GiantFrog": GiantFrog,
        "UndeadSkeleton": UndeadSkeleton, "UndeadZombie": UndeadZombie,
        "UndeadSkeletonArcher": UndeadSkeletonArcher,
        "GiantRat": GiantRat, "RatRider": RatRider,
        "CorruptedCrow": CorruptedCrow,
    }[name]


def make_boss(cls, name, x, y):
    """Jättimäinen, buffattu versio olennosta: 6x HP, 2x voima,
    tuplakokoinen sprite ja bossipalkki (is_boss)."""
    boss = cls(name, x, y, ENEMY_TEAM)
    boss.name = name
    boss.max_hp = int(boss.max_hp * 6)
    boss.current_hp = boss.max_hp
    boss.strength = int(getattr(boss, "strength", 8) * 2)
    boss.defense = int(getattr(boss, "defense", 0)) + 4
    boss.speed = max(0.6, float(getattr(boss, "speed", 1.0)) * 0.9)
    boss.is_boss = True
    boss.xp_value = int(getattr(boss, "xp_value", 20)) * 5
    # Skaalaa kaikki spritet tuplakokoon
    try:
        for key, img in list(getattr(boss, "sprites", {}).items()):
            if isinstance(img, list):
                boss.sprites[key] = [pygame.transform.scale(
                    f, (f.get_width() * 2, f.get_height() * 2))
                    for f in img]
            elif img is not None:
                boss.sprites[key] = pygame.transform.scale(
                    img, (img.get_width() * 2, img.get_height() * 2))
        if boss.image is not None:
            boss.image = pygame.transform.scale(
                boss.image, (boss.image.get_width() * 2,
                             boss.image.get_height() * 2))
    except Exception:
        pass
    # Isompi hitbox (maltillisesti)
    boss.rect = boss.rect.inflate(int(boss.rect.w * 0.6),
                                  int(boss.rect.h * 0.6))
    boss.rect.center = (x, y)
    return boss


class _RiftArena:
    """Kevyt proseduraalinen erämaakenttä repeämätaistelulle."""

    def __init__(self, theme):
        self.width = ARENA_W
        self.height = ARENA_H
        self.theme = theme
        self.obstacles = []
        self.props = []
        self._base = None
        rng = random.Random(hash(theme["title"]) & 0xFFFF)
        # Hajanaisia "tuppaita" (läiskiä) koristeeksi - ei törmäystä
        self._patches = [(rng.randint(80, ARENA_W - 120),
                          rng.randint(80, ARENA_H - 120),
                          rng.randint(30, 90)) for _ in range(60)]

    def draw_background(self, screen, offset=(0, 0)):
        if self._base is None:
            base = pygame.Surface((self.width, self.height))
            base.fill(self.theme["floor"])
            for x, y, r in self._patches:
                pygame.draw.ellipse(base, self.theme["accent"],
                                    (x, y, r * 2, r))
            # Reunavarjostus
            pygame.draw.rect(base, (20, 18, 22),
                             (0, 0, self.width, self.height), 24)
            self._base = base
        screen.blit(self._base, (-int(offset[0]), -int(offset[1])))


class RiftSiteMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.theme_id = "marsh"
        self.monsters = []
        self.phase = "dormant"   # dormant/wave/pause/boss/sealable/sealed
        self.wave_index = 0
        self.pause_timer = 0
        self.banner = ""
        self.banner_timer = 0
        self.boss = None
        self.rift = None
        self.signpost = None

    # ------------------------------------------------------------------
    def on_enter(self):
        super().on_enter()
        loc = getattr(self.manager, "pending_world_location", None)
        self.theme_id = LOCATION_THEMES.get(loc, self.theme_id)
        self.theme = THEMES[self.theme_id]
        self.arena = _RiftArena(self.theme)

        from assets.tiles.muckford_objects import RiftFissure, RoadSignpost
        # ISO repeämä kentän itälaidalla
        self.rift = RiftFissure(ARENA_W - 560, ARENA_H // 2 - 100)
        # Iso versio: tuplakuva, isompi saalis, sinetöinti vasta bossin
        # jälkeen (portitetaan try_begin-tarkistuksella alla)
        try:
            self.rift.image = pygame.transform.scale(
                self.rift.image, (240, 180))
            self.rift.image_pos = (self.rift.image_pos[0] - 60,
                                   self.rift.image_pos[1] - 45)
        except Exception:
            pass
        self.rift.rect = pygame.Rect(ARENA_W - 580, ARENA_H // 2 - 60,
                                     160, 80)
        self.rift.min_drop = 3
        self.rift.max_drop = 4
        self.rift.channel_swings_needed = 4
        self.rift.expire_frames = 10 ** 9   # iso repeämä ei sulkeudu itse
        self.rift.interaction_label = "Rift"
        self.arena.props.append(self.rift)

        # Paluukyltti sisäänkäynnillä (länsi)
        self.signpost = RoadSignpost(140, ARENA_H // 2 - 80)
        self.arena.props.append(self.signpost)

        # Pelaaja sisään länsilaidalta
        self.player = self.manager.player_character
        self.player.rect.center = (280, ARENA_H // 2)
        self.player.current_hp = max(self.player.current_hp, 1)

        self.monsters = []
        self.boss = None
        self.phase = "dormant"
        self.wave_index = 0
        self._set_banner(f"{self.theme['title']} - a great rift looms "
                         f"to the east.", 300)
        self._update_camera()

    def on_exit(self):
        super().on_exit()
        self.manager.match_in_progress = False

    def _set_banner(self, text, frames=240):
        self.banner = text
        self.banner_timer = frames

    # ------------------------------------------------------------------
    # Invaasion kulku
    # ------------------------------------------------------------------
    def _start_invasion(self):
        self.phase = "wave"
        self.wave_index = 0
        self._spawn_wave(0)
        sound_system.play_sound("battle_start")
        try:
            self.manager.trigger_screen_shake(8)
        except Exception:
            pass

    def _spawn_wave(self, idx):
        self.monsters = [m for m in self.monsters if not m.is_dead]
        wave = self.theme["waves"][idx]
        rx, ry = self.rift.rect.center
        rng = random.Random()
        n_total = 0
        for cls_name, count in wave:
            cls = _unit_class(cls_name)
            for _ in range(count):
                x = rx + rng.randint(-160, 60)
                y = ry + rng.randint(-220, 220)
                mob = cls(cls_name.replace("Undead", "Rift-"), x, y,
                          ENEMY_TEAM)
                self.monsters.append(mob)
                n_total += 1
        self._set_banner(f"WAVE {idx + 1}/{len(self.theme['waves'])} - "
                         f"{n_total} horrors pour from the rift!", 240)
        sound_system.play_sound("cmd_vortex_slash")

    def _spawn_boss(self):
        cls_name, boss_name = self.theme["boss"]
        cls = _unit_class(cls_name)
        rx, ry = self.rift.rect.center
        self.boss = make_boss(cls, boss_name, rx - 120, ry)
        self.monsters.append(self.boss)
        self.phase = "boss"
        self._set_banner(f"{boss_name.upper()} forces its way through!",
                         300)
        try:
            self.manager.trigger_screen_shake(12)
        except Exception:
            pass
        sound_system.play_sound("battle_start")

    def _reset_invasion(self):
        """Pelaaja kaatui: invaasio raukeaa, repeämä palaa lepotilaan."""
        self.monsters = []
        self.boss = None
        self.phase = "dormant"
        self.wave_index = 0
        self.player.is_dead = False
        self.player.current_hp = max(1, int(self.player.max_hp * 0.3))
        self.player.rect.center = (280, ARENA_H // 2)
        self._set_banner("You are dragged back to the trailhead... "
                         "the rift still hungers.", 300)

    def _update_invasion(self):
        if self.phase == "wave":
            if all(m.is_dead for m in self.monsters):
                self.wave_index += 1
                if self.wave_index >= len(self.theme["waves"]):
                    self.phase = "pause"
                    self.pause_timer = 120
                    self._set_banner("The rift convulses...", 120)
                else:
                    self.phase = "pause"
                    self.pause_timer = 90
                    self._set_banner(f"Wave {self.wave_index} cleared!", 90)
        elif self.phase == "pause":
            self.pause_timer -= 1
            if self.pause_timer <= 0:
                if self.wave_index >= len(self.theme["waves"]):
                    self._spawn_boss()
                else:
                    self.phase = "wave"
                    self._spawn_wave(self.wave_index)
        elif self.phase == "boss":
            if self.boss is not None and self.boss.is_dead:
                self.phase = "sealable"
                self._set_banner("The breach shudders - SEAL IT NOW! "
                                 "(E at the rift)", 400)
                sound_system.play_sound("win")

        # Sinetöinti valmis (keräyskanava tyhjensi repeämän)
        if self.phase == "sealable" and self.rift.is_empty:
            self.phase = "sealed"
            self._set_banner("The rift collapses. The land breathes "
                             "again. (Signpost leads home.)", 500)
            # Kristallit suoraan reppuun: match_in_progress ohjaisi ne
            # round_rewards-loottiin jota ei täällä koskaan lunasteta
            m = self.manager
            loot = m.round_rewards.get("loot", {}) if \
                isinstance(getattr(m, "round_rewards", None), dict) else {}
            n = int(loot.pop("Vortex Crystal", 0))
            if n:
                m.inventory["Vortex Crystal"] = \
                    m.inventory.get("Vortex Crystal", 0) + n
                m.vfx.show_damage(self.rift.rect.centerx,
                                  self.rift.rect.top - 50,
                                  f"+{n} Vortex Crystal!",
                                  color=(190, 140, 255))
            try:
                self.manager.grant_hero_xp(25, self.player.rect.centerx,
                                           self.player.rect.top)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def handle_event(self, event):
        super().handle_event(event)
        if event.type != pygame.KEYDOWN or \
                not keybinds.matches(event.key, "interact"):
            return
        if self.manager.active_dialogue or self.manager.dialogue_cooldown > 0:
            return
        px, py = self.player.rect.center
        # Paluukyltti
        sp = self.signpost.rect
        if math.hypot(px - sp.centerx, py - sp.centery) < 120:
            self.manager.world_map_return_state = "world_map"
            self.next_state = "world_map"
            sound_system.play_sound("click")
            return
        # Repeämä
        rr = self.rift.rect
        if math.hypot(px - rr.centerx, py - rr.centery) < 170:
            if self.phase == "dormant":
                self._start_invasion()
            elif self.phase == "sealable":
                self.rift.try_begin_channel(self.player, self.manager,
                                            max_range_bonus=80)
            elif self.phase in ("wave", "pause", "boss"):
                self.manager.vfx.show_damage(
                    rr.centerx, rr.top - 30,
                    "The rift resists - its spawn still lives!",
                    color=(200, 140, 240))

    def update(self):
        if self.manager.paused:
            return
        alive = [m for m in self.monsters if not m.is_dead]
        all_units = [self.player] + alive
        self._update_gameplay(all_units)

        # Repeämä sykkii (partikkelit + kanava sinetöinnissä)
        if self.phase == "sealable":
            self.rift.update(None, self.manager)
        elif not self.rift.is_empty and random.random() < 0.1:
            try:
                self.manager.vfx.create_void_particles(
                    self.rift.rect.centerx + random.randint(-60, 60),
                    self.rift.rect.centery + random.randint(-30, 20))
            except Exception:
                pass

        if self.banner_timer > 0:
            self.banner_timer -= 1

        # Pelaajan kaatuminen nollaa invaasion
        if self.player.is_dead:
            self._reset_invasion()
            return

        self._update_invasion()

    # ------------------------------------------------------------------
    def draw(self, screen):
        offset = (self.camera_x, self.camera_y)
        self.arena.draw_background(screen, offset)
        self.manager.vfx.draw_floor(screen, offset)

        renderables = list(self.arena.props) + \
            [m for m in self.monsters if not m.is_dead] + [self.player]
        renderables.sort(key=lambda o: o.rect.bottom)
        for obj in renderables:
            if hasattr(obj, "draw_on_screen"):
                obj.draw_on_screen(screen, offset)
            elif getattr(obj, "image", None):
                screen.blit(obj.image, (obj.rect.x - offset[0],
                                        obj.rect.y - offset[1]))
        self.manager.vfx.draw_top(screen, offset)

        # Bossipalkki
        self._draw_boss_bar(screen, [m for m in self.monsters
                                     if not m.is_dead])

        # Otsikko + tilanne
        head = pygame.Rect(SCREEN_WIDTH // 2 - 360, 14, 720, 46)
        pygame.draw.rect(screen, (16, 14, 20), head, border_radius=10)
        pygame.draw.rect(screen, (150, 110, 220), head, 2, border_radius=10)
        surf = font_main.render(self.theme["title"], True, (220, 200, 255))
        screen.blit(surf, surf.get_rect(center=head.center))
        if self.phase == "wave":
            draw_text(f"Wave {self.wave_index + 1}/"
                      f"{len(self.theme['waves'])}   Enemies left: "
                      f"{sum(1 for m in self.monsters if not m.is_dead)}",
                      font_small, WHITE, screen, head.x + 12,
                      head.bottom + 8)

        # Banneri
        if self.banner_timer > 0 and self.banner:
            surf = font_main.render(self.banner, True, (230, 210, 255))
            bx = SCREEN_WIDTH // 2 - surf.get_width() // 2
            bg = pygame.Surface((surf.get_width() + 30,
                                 surf.get_height() + 12), pygame.SRCALPHA)
            bg.fill((20, 12, 30, 200))
            screen.blit(bg, (bx - 15, 94))
            screen.blit(surf, (bx, 100))

        # Kehotteet
        px, py = self.player.rect.center
        if math.hypot(px - self.signpost.rect.centerx,
                      py - self.signpost.rect.centery) < 120:
            self.manager._draw_floating_prompt(
                screen, self.signpost.rect.centerx,
                self.signpost.rect.top - 24, "E", offset, "Travel back")
        rr = self.rift.rect
        if math.hypot(px - rr.centerx, py - rr.centery) < 170 and \
                not self.rift.is_empty:
            label = {"dormant": "Challenge the rift",
                     "sealable": "SEAL THE RIFT"}.get(self.phase)
            if label:
                self.manager._draw_floating_prompt(
                    screen, rr.centerx, rr.top - 40, "E", offset, label)

        # HUD
        if self.player:
            self.player.draw_hud(screen)
        self.draw_editor(screen)
