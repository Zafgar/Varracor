"""Expanded Forest Road combat tutorial for the Muckford opening."""
from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

import pygame

from settings import CHEAT_MODE, ENEMY_TEAM, GOLD_COLOR, GRAY, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import draw_text, font_main, font_small
from systems.muckford_opening_core import FOREST_ROAD_WIDTH, _opening


def _patch_forest_arena() -> None:
    from assets.tiles.forest_objects import ForestBush, ForestCart, ForestRockBig
    from assets.tiles.muckford_objects import ScrapPileBig
    from assets.tiles.vfx import MapVFX
    from citys.mucford.forest_road_arena import ForestRoadArena

    if getattr(ForestRoadArena, "_muckford_opening_installed", False):
        return

    def __init__(self):
        self.width = FOREST_ROAD_WIDTH
        self.height = 1200
        self.floor_image = pygame.Surface((self.width, self.height))
        self._generate_floor()
        self.vfx = MapVFX()
        self.props = []
        self.obstacles = []
        self.floor_props = []
        self._build_level()

        road_y = self.height // 2
        details = [
            ForestCart(1750, road_y - 250),
            ScrapPileBig(2750, road_y + 120),
            ForestRockBig(3850, road_y - 245),
            ForestCart(4950, road_y + 115),
            ForestRockBig(6050, road_y - 245),
        ]
        for prop in details:
            self._add_prop(prop)
        for x in range(500, self.width - 300, 260):
            side_y = road_y - 245 if (x // 260) % 2 else road_y + 165
            if random.random() < 0.55:
                self._add_prop(ForestBush(x, side_y))

    ForestRoadArena.__init__ = __init__
    ForestRoadArena._muckford_opening_installed = True


def _make_tutorial_rat(name: str, x: int, y: int, hp: int, stage: int):
    from units.rat import GiantRat

    rat = GiantRat(name, x, y, ENEMY_TEAM)
    rat.max_hp = hp
    rat.current_hp = hp
    rat.strength = 4 + stage
    rat.dexterity = 8
    rat.speed = 0.75 + stage * 0.04
    rat.attack_speed = 85
    rat.is_tutorial_enemy = True
    return rat


def _tutorial_stage_data(stage: int) -> dict:
    data = {
        0: {
            "title": "MOVE THROUGH THE STORM",
            "instruction": "WASD moves. Hold SHIFT to sprint along the road.",
            "spawn_x": None,
            "gate_x": 900,
        },
        1: {
            "title": "BASIC ATTACK",
            "instruction": "Aim with the mouse and press LMB to strike.",
            "spawn_x": 1300,
            "gate_x": 1800,
        },
        2: {
            "title": "BLOCK",
            "instruction": "Hold RMB near the rat. Blocking uses stamina, then counterattack.",
            "spawn_x": 2350,
            "gate_x": 2900,
        },
        3: {
            "title": "DASH",
            "instruction": "Press SPACE to dash toward the mouse, then finish the pack.",
            "spawn_x": 3450,
            "gate_x": 4050,
        },
        4: {
            "title": "VORTEX SKILL",
            "instruction": "Press 1, aim through the pack, then LMB to cast Vortex Slash.",
            "spawn_x": 4550,
            "gate_x": 5200,
        },
        5: {
            "title": "POWER STRIKE",
            "instruction": "Hold LMB until the blade flares, then release the charged strike.",
            "spawn_x": 5650,
            "gate_x": 6300,
        },
        6: {
            "title": "THE ROAD AHEAD",
            "instruction": "Keep moving toward Muckford. Something is waiting in the rain.",
            "spawn_x": None,
            "gate_x": FOREST_ROAD_WIDTH - 450,
        },
    }
    return data[stage]


def _patch_forest_menu() -> None:
    from citys.mucford.forest_road_menu import ForestRoadMenu
    from menus.gameplay_screen import GameplayScreen
    from spells.commander.seam_cut import SeamCut
    from vfx import VortexPortal

    if getattr(ForestRoadMenu, "_muckford_opening_installed", False):
        return

    previous_init = ForestRoadMenu.__init__
    previous_on_enter = ForestRoadMenu.on_enter
    previous_update = ForestRoadMenu.update
    previous_draw = ForestRoadMenu.draw
    previous_effect = ForestRoadMenu.handle_dialogue_effect

    def __init__(self, manager):
        previous_init(self, manager)
        self.tutorial_stage = 0
        self.tutorial_enemies = []
        self.tutorial_spawned_stage = None
        self.tutorial_block_frames = 0
        self.tutorial_dash_seen = False
        self.tutorial_skill_seen = False
        self.tutorial_power_seen = False
        self.tutorial_feedback = ""
        self.tutorial_feedback_timer = 0
        self._opening_tutorial_finished = False
        self._tutorial_spell_granted = False
        self._tutorial_last_dashes = self.player.current_dashes
        self.boss_approach_x = self.arena.width - 650
        self.boss_vortex_x = self.arena.width - 350
        self.combat_locked = False
        if not CHEAT_MODE and self.player.equipment.get("spell1") is None:
            self.player.equipment["spell1"] = SeamCut()
            self._tutorial_spell_granted = True

    def on_enter(self):
        previous_on_enter(self)
        self.player = self.manager.player_character
        self.player.rect.center = (120, self.arena.height // 2)
        self.player.current_hp = self.player.max_hp
        self.player.current_mana = self.player.max_mana
        self.player.current_stamina = self.player.max_stamina
        self.combat_locked = False
        self.tutorial_stage = 0
        self.tutorial_enemies = []
        self.tutorial_spawned_stage = None
        self.tutorial_block_frames = 0
        self.tutorial_dash_seen = False
        self.tutorial_skill_seen = False
        self.tutorial_power_seen = False
        self._opening_tutorial_finished = False
        self._tutorial_last_dashes = self.player.current_dashes
        if not CHEAT_MODE and self.player.equipment.get("spell1") is None:
            self.player.equipment["spell1"] = SeamCut()
            self._tutorial_spell_granted = True
        self._update_camera()

    def _spawn_stage(self):
        if self.tutorial_stage not in range(1, 6):
            return
        if self.tutorial_spawned_stage == self.tutorial_stage:
            return
        data = _tutorial_stage_data(self.tutorial_stage)
        spawn_x = data["spawn_x"]
        if self.player.rect.centerx < spawn_x - 430:
            return

        layouts: Dict[int, List[Tuple[int, int, int]]] = {
            1: [(0, 0, 42)],
            2: [(0, 0, 58)],
            3: [(0, -55, 45), (90, 55, 45)],
            4: [(0, -70, 38), (115, 0, 38), (230, 70, 38)],
            5: [(0, -55, 75), (120, 55, 75)],
        }
        self.tutorial_enemies = []
        for index, (ox, oy, hp) in enumerate(layouts[self.tutorial_stage]):
            rat = _make_tutorial_rat(
                f"Road Rat {self.tutorial_stage}-{index + 1}",
                spawn_x + ox,
                self.arena.height // 2 + oy,
                hp,
                self.tutorial_stage,
            )
            self.tutorial_enemies.append(rat)
        self.tutorial_spawned_stage = self.tutorial_stage
        try:
            sound_system.play_sound("boss_roar")
        except Exception:
            pass

    def _stage_enemies_dead(self):
        return bool(self.tutorial_enemies) and all(
            getattr(enemy, "is_dead", False) for enemy in self.tutorial_enemies
        )

    def _repeat_stage(self, reason):
        self.tutorial_feedback = reason
        self.tutorial_feedback_timer = 180
        self.tutorial_enemies = []
        self.tutorial_spawned_stage = None
        self.player.current_hp = self.player.max_hp
        self.player.current_stamina = self.player.max_stamina
        self.player.current_mana = self.player.max_mana

    def _advance_stage(self):
        self.tutorial_feedback = "Lesson complete"
        self.tutorial_feedback_timer = 90
        self.tutorial_stage += 1
        self.tutorial_enemies = []
        self.tutorial_spawned_stage = None
        self.player.current_hp = self.player.max_hp
        self.player.current_stamina = self.player.max_stamina
        self.player.current_mana = self.player.max_mana
        if self.tutorial_stage == 2:
            self.tutorial_block_frames = 0
        elif self.tutorial_stage == 3:
            self.tutorial_dash_seen = False
            self._tutorial_last_dashes = self.player.current_dashes
        elif self.tutorial_stage == 4:
            self.tutorial_skill_seen = False
            self.player.spell_cooldowns["spell1"] = 0
        elif self.tutorial_stage == 5:
            self.tutorial_power_seen = False
            weapon = self.player.equipment.get("main_hand")
            if weapon is not None:
                weapon.special_cooldown = 0
                weapon.charge_time = 0
        try:
            sound_system.play_sound("recruit")
        except Exception:
            pass

    def _update_stage(self):
        data = _tutorial_stage_data(self.tutorial_stage)
        gate_x = int(data["gate_x"])
        if self.player.rect.centerx > gate_x:
            self.player.rect.centerx = gate_x

        if self.tutorial_stage == 0:
            if self.player.rect.centerx >= 760:
                self._advance_stage()
            return

        if self.tutorial_stage in range(1, 6):
            self._spawn_stage()
            living = [e for e in self.tutorial_enemies if not e.is_dead]

            if self.tutorial_stage == 2 and living:
                nearest = min(
                    math.hypot(
                        e.rect.centerx - self.player.rect.centerx,
                        e.rect.centery - self.player.rect.centery,
                    )
                    for e in living
                )
                if self.player.is_blocking and nearest < 220:
                    self.tutorial_block_frames += 1

            if self.player.is_dashing or (
                self.player.current_dashes < self._tutorial_last_dashes
            ):
                self.tutorial_dash_seen = True
            self._tutorial_last_dashes = self.player.current_dashes

            if self.player.spell_cooldowns.get("spell1", 0) > 0:
                self.tutorial_skill_seen = True
            weapon = self.player.equipment.get("main_hand")
            if weapon and int(getattr(weapon, "special_cooldown", 0)) > 0:
                self.tutorial_power_seen = True

            if self._stage_enemies_dead():
                if self.tutorial_stage == 2 and self.tutorial_block_frames < 24:
                    self._repeat_stage("Block the attack before killing the rat.")
                elif self.tutorial_stage == 3 and not self.tutorial_dash_seen:
                    self._repeat_stage("Use SPACE to dash before finishing the pack.")
                elif self.tutorial_stage == 4 and not self.tutorial_skill_seen:
                    self._repeat_stage("Use Vortex Slash: press 1, then LMB.")
                elif self.tutorial_stage == 5 and not self.tutorial_power_seen:
                    self._repeat_stage("Charge and release a full Power Strike.")
                else:
                    self._advance_stage()
            return

        if self.tutorial_stage == 6 and self.player.rect.centerx >= self.boss_approach_x:
            self._opening_tutorial_finished = True
            self.combat_locked = True
            flags = self.manager.npc_state.setdefault("global", {}).setdefault(
                "flags", {}
            )
            flags["forest_intro_done"] = False

    def update(self):
        if self._opening_tutorial_finished:
            return previous_update(self)

        GameplayScreen.update(self)
        if self.manager.paused:
            return

        if self.rain_channel and not self.rain_channel.get_busy():
            self.rain_channel = sound_system.play_sound("rain_medium", loops=-1)
        if self.wind_channel and not self.wind_channel.get_busy():
            self.wind_channel = sound_system.play_sound("wind_outside", loops=-1)

        self.manager.all_units.empty()
        self.manager.all_units.add(self.player)
        for enemy in self.tutorial_enemies:
            if not enemy.is_dead:
                self.manager.all_units.add(enemy)

        self.player.run_combat_ai(
            self.manager.all_units, self.arena.obstacles, self.manager
        )
        self.player.update(self.arena.obstacles, self.manager)
        self.player.rect.centery = max(
            360, min(self.player.rect.centery, self.arena.height - 360)
        )

        if self.player.is_dead:
            self.player.is_dead = False
            self.player.current_hp = self.player.max_hp
            self.player.current_mana = self.player.max_mana
            self.player.current_stamina = self.player.max_stamina
            data = _tutorial_stage_data(self.tutorial_stage)
            spawn_x = data.get("spawn_x") or 200
            self.player.rect.center = (
                max(120, spawn_x - 420),
                self.arena.height // 2,
            )
            self.tutorial_enemies = []
            self.tutorial_spawned_stage = None
            self.tutorial_feedback = "The Vortex Blade pulls you back to your feet."
            self.tutorial_feedback_timer = 180

        if not self.manager.world_paused:
            for enemy in self.tutorial_enemies:
                if enemy.is_dead:
                    continue
                enemy.run_combat_ai(
                    self.manager.all_units, self.arena.obstacles, self.manager
                )
                enemy.update(self.arena.obstacles, self.manager)

        self._update_stage()
        if hasattr(self.arena, "update"):
            self.arena.update(self.manager)
        self.manager.vfx.update(obstacles=self.arena.obstacles)
        self._update_camera()

        if self.tutorial_feedback_timer > 0:
            self.tutorial_feedback_timer -= 1

        if self.lightning_timer > 0:
            self.lightning_timer -= 1
        elif random.random() < 0.005:
            self.lightning_timer = random.randint(10, 30)
            self.flash_alpha = 200
            try:
                sound_system.play_sound(
                    random.choice(
                        ["thunder_1", "thunder_2", "thunder_3", "thunder_4"]
                    )
                )
            except Exception:
                pass
        if self.flash_alpha > 0:
            self.flash_alpha -= 10

    def _draw_tutorial_panel(self, screen):
        data = _tutorial_stage_data(self.tutorial_stage)
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 430, 36, 860, 112)
        surface = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(
            surface, (12, 14, 18, 225), surface.get_rect(), border_radius=12
        )
        pygame.draw.rect(
            surface,
            (190, 155, 90, 240),
            surface.get_rect(),
            3,
            border_radius=12,
        )
        screen.blit(surface, panel.topleft)
        draw_text(
            data["title"], font_main, GOLD_COLOR, screen, panel.x + 24, panel.y + 18
        )
        draw_text(
            data["instruction"],
            font_small,
            WHITE,
            screen,
            panel.x + 24,
            panel.y + 57,
        )
        draw_text(
            f"Lesson {self.tutorial_stage + 1}/7",
            font_small,
            GRAY,
            screen,
            panel.right - 130,
            panel.y + 20,
        )
        if self.tutorial_stage == 2:
            draw_text(
                f"Block held: {min(24, self.tutorial_block_frames)}/24",
                font_small,
                (160, 220, 255),
                screen,
                panel.x + 24,
                panel.y + 82,
            )
        if self.tutorial_feedback_timer > 0 and self.tutorial_feedback:
            draw_text(
                self.tutorial_feedback,
                font_small,
                (160, 255, 180),
                screen,
                panel.x + 350,
                panel.y + 82,
            )

    def draw(self, screen):
        if self._opening_tutorial_finished:
            return previous_draw(self, screen)

        offset = (self.camera_x, self.camera_y)
        self.arena.draw_background(screen, offset)
        self.manager.vfx.draw_floor(screen, offset)
        renderables = [self.player] + list(self.arena.props)
        renderables += [e for e in self.tutorial_enemies if not e.is_dead]
        renderables.sort(key=lambda item: item.rect.bottom)
        for item in renderables:
            if hasattr(item, "draw_on_screen"):
                item.draw_on_screen(screen, offset)
            elif getattr(item, "image", None):
                screen.blit(
                    item.image,
                    (item.rect.x - offset[0], item.rect.y - offset[1]),
                )
            if getattr(item, "is_tutorial_enemy", False):
                try:
                    item.draw_health_bar(screen, offset)
                except Exception:
                    pass
        self.arena.draw_foreground(screen, offset)
        self.manager.vfx.draw_top(screen, offset)

        night = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        night.fill((10, 10, 20))
        night.set_alpha(165)
        screen.blit(night, (0, 0))
        if self.flash_alpha > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.fill((200, 200, 255))
            flash.set_alpha(self.flash_alpha)
            screen.blit(flash, (0, 0))

        self.player.draw_hud(screen)
        self._draw_tutorial_panel(screen)
        self.draw_editor(screen)

    def handle_dialogue_effect(self, effect):
        if effect == "spawn_vortex":
            vortex = VortexPortal(
                self.boss_vortex_x,
                self.arena.height // 2,
                duration=999999,
            )
            self.manager.vfx.add_effect(vortex)
            self.active_vortex = vortex
            self.manager.trigger_screen_shake(15)
            try:
                sound_system.play_sound("vortex_spawn")
                self.vortex_channel = sound_system.play_sound(
                    "vortex_loop", loops=-1
                )
            except Exception:
                pass
            return

        if effect == "steal_sword":
            previous_effect(self, effect)
            if self._tutorial_spell_granted and not CHEAT_MODE:
                self.player.equipment["spell1"] = None
                self.player.selected_spell_slot = None
            return

        if effect == "teleport_city":
            state = _opening(self.manager)
            state["intro_complete"] = True
            state["creature_wins"] = 0
            state["bram_hint_shown"] = False
            previous_effect(self, effect)
            return

        return previous_effect(self, effect)

    ForestRoadMenu.__init__ = __init__
    ForestRoadMenu.on_enter = on_enter
    # BUGIKORJAUS: metodit asennettiin vain pitkillä _tutorial_-nimillä,
    # mutta patchattu update/draw kutsuu LYHYITÄ nimiä (self._update_stage
    # jne.) -> AttributeError heti metsäpolulle astuttaessa. Asennetaan
    # molemmilla nimillä.
    ForestRoadMenu._spawn_stage = _spawn_stage
    ForestRoadMenu._stage_enemies_dead = _stage_enemies_dead
    ForestRoadMenu._repeat_stage = _repeat_stage
    ForestRoadMenu._advance_stage = _advance_stage
    ForestRoadMenu._update_stage = _update_stage
    ForestRoadMenu._spawn_tutorial_stage = _spawn_stage
    ForestRoadMenu._tutorial_stage_enemies_dead = _stage_enemies_dead
    ForestRoadMenu._repeat_tutorial_stage = _repeat_stage
    ForestRoadMenu._advance_tutorial_stage = _advance_stage
    ForestRoadMenu._update_tutorial_stage = _update_stage
    ForestRoadMenu._draw_tutorial_panel = _draw_tutorial_panel
    ForestRoadMenu.update = update
    ForestRoadMenu.draw = draw
    ForestRoadMenu.handle_dialogue_effect = handle_dialogue_effect
    ForestRoadMenu._muckford_opening_installed = True


def install_muckford_forest_tutorial() -> None:
    _patch_forest_arena()
    _patch_forest_menu()
