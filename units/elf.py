# units/elf.py
import pygame
import random
import os
import math

from settings import *
from gladiator import Gladiator

from ai.base_ai import BaseAI
try:
    from ai.elf_ai import ElfAI
except ImportError:
    ElfAI = None


def _display_ready() -> bool:
    return pygame.display.get_init() and pygame.display.get_surface() is not None


def _safe_convert_alpha(surf: pygame.Surface) -> pygame.Surface:
    # convert_alpha() vaatii display moden -> ei kaadeta latauksessa.
    if _display_ready():
        try:
            return surf.convert_alpha()
        except Exception:
            return surf
    return surf


def _corners(sim: pygame.Surface):
    w, h = sim.get_width(), sim.get_height()
    return [
        sim.get_at((0, 0)),
        sim.get_at((w - 1, 0)),
        sim.get_at((0, h - 1)),
        sim.get_at((w - 1, h - 1)),
    ]


def _maybe_key_background(raw_img: pygame.Surface) -> pygame.Surface:
    """
    If the PNG has an opaque solid background (often white),
    try to colorkey it away before trimming/scaling.
    This helps when assets are not exported with transparency.
    """
    try:
        cs = _corners(raw_img)
        # all opaque?
        if not all(c.a == 255 for c in cs):
            return raw_img

        # colors close to each other?
        def dist(a, b):
            return abs(a.r - b.r) + abs(a.g - b.g) + abs(a.b - b.b)

        if max(dist(cs[0], c) for c in cs[1:]) > 20:
            return raw_img

        bg = cs[0]
        # only attempt if it's bright-ish (typical white / beige bg)
        if (bg.r + bg.g + bg.b) < 680:  # ~ 226*3
            return raw_img

        img = raw_img.copy()
        img.set_colorkey((bg.r, bg.g, bg.b))
        return img
    except Exception:
        return raw_img


def _trim_transparent(img: pygame.Surface) -> pygame.Surface:
    try:
        br = img.get_bounding_rect(min_alpha=1)
    except TypeError:
        br = img.get_bounding_rect()
    if br.w <= 0 or br.h <= 0:
        return img
    return img.subsurface(br).copy()


class Elf(Gladiator):
    """
    Elf sprites:
    - assets/races/elf/*.png variants (random per unit)
    - cached per (filepath, target_w, target_h)
    - trims transparent borders + bottom-aligns into the hitbox surface
      => fixes "floating" feet due to whitespace in PNG
    """

    sprite_cache = {}  # (filepath, w, h) -> Surface
    BIG_SCALE = 3

    def __init__(self, name, x, y, team_color, quality="Common"):
        super().__init__(name, "Elf", x, y, team_color)

        # --- FEET HITBOX ---
        self.rect = pygame.Rect(x, y + 44, 30, 20)
        
        self.image = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))

        self.big_image = pygame.Surface((self.rect.w * self.BIG_SCALE, self.rect.h * self.BIG_SCALE), pygame.SRCALPHA)

        # --- OMINAISUUDET ---
        self.cost = 140
        self.upgrade_cost = 140
        self.quality = quality

        # Trait
        if not hasattr(self, "traits") or self.traits is None:
            self.traits = []
        if "Quick" not in self.traits:
            self.traits.append("Quick")

        # AI
        self.ai_controller = ElfAI(self) if ElfAI else BaseAI(self)

        # --- GRAFIIKKA & ANIMAATIO ---
        self.sprites = {}
        self.last_pos = self.rect.topleft
        self.hurt_timer = 0

        self.show_main_hand = True
        self.show_off_hand = True
        
        self._load_sprites()
        self.image = self.sprites.get("idle", pygame.Surface((40, 64), pygame.SRCALPHA))
        if not self.sprites:
            self.image.fill((50, 120, 50))

        # Portrait / UI
        if not getattr(self, "big_image", None):
            self.big_image = pygame.transform.smoothscale(self.image, (self.rect.w * self.BIG_SCALE, self.rect.h * self.BIG_SCALE))
            self.big_image = _safe_convert_alpha(self.big_image)

        # Stats
        self.calculate_final_stats()
        self.current_hp = self.max_hp
        self.current_mana = self.max_mana

    def load_assets(self):
        return True

    # =========================================================
    # SPRITES
    # =========================================================
    def _load_sprites(self):
        """
        Loads all animation states for the elf (attack, cast, idle, etc.).
        Assumes filenames like 'elf_idle_1.png', 'elf_attack_1.png'.
        """
        states = ["idle", "run", "attack", "cast", "hurt"]
        base_name = "elf"
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        elf_dir = os.path.join(root_dir, "assets", "races", "elf")

        loaded_any = False
        for state in states:
            path = os.path.join(elf_dir, f"{base_name}_{state}_1.png")
            
            target_w, target_h = 40, 64 # Visuaalinen koko (ei hitbox)
            cache_key = (path, target_w, target_h)

            cached = Elf.sprite_cache.get(cache_key)
            if cached:
                self.sprites[state] = cached.copy()
                loaded_any = True
                continue

            if not os.path.exists(path):
                continue

            try:
                raw_img = pygame.image.load(path)
                raw_img = _safe_convert_alpha(raw_img)
                raw_img = _maybe_key_background(raw_img)
                cropped = _trim_transparent(raw_img)

                max_w, max_h = max(1, target_w - 2), max(1, target_h - 2)
                s = min(max_w / cropped.get_width(), max_h / cropped.get_height())
                new_w = max(1, int(cropped.get_width() * s))
                new_h = max(1, int(cropped.get_height() * s))

                # --- Generate High-Res Portrait (Idle only) ---
                if state == "idle":
                    self.big_image = cropped

                scaled = pygame.transform.smoothscale(cropped, (new_w, new_h))
                scaled = _safe_convert_alpha(scaled)

                final = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
                final.fill((0, 0, 0, 0))

                x = (target_w - new_w) // 2
                y = target_h - new_h
                final.blit(scaled, (x, y))
                final = _safe_convert_alpha(final)

                self.sprites[state] = final
                Elf.sprite_cache[cache_key] = final.copy()
                loaded_any = True
            except Exception as e:
                print(f"[ELF] Error loading sprite {path}: {e}")
        
        return loaded_any

    def _apply_team_color(self):
        """Small team marks only (no foot bar)."""
        try:
            # small shoulder pin
            pygame.draw.circle(self.image, self.team_color, (self.rect.w - 10, int(self.rect.h * 0.42)), 3)
            # small forearm band
            pygame.draw.rect(
                self.image,
                self.team_color,
                pygame.Rect(6, int(self.rect.h * 0.58), 10, 3),
                border_radius=2
            )
        except Exception:
            pass

    # =========================================================
    # PROCEDURAL (fallback)
    # =========================================================
    # =========================================================
    # COMBAT & UPDATE
    # =========================================================
    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        dmg_dealt = super().take_damage(amount, damage_type, attacker, manager)
        if dmg_dealt > 0 and not self.is_dead:
            self.hurt_timer = 15 # frames for hurt animation
        return dmg_dealt

    def update(self, obstacles=None, manager=None):
        super().update(obstacles, manager)

        if self.is_dead:
            return

        # --- Animation State Logic ---
        new_state = "idle"

        # 1. Hurt (highest priority)
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            new_state = "hurt"
        
        # 2. Attack
        elif self.attack_cooldown > self.attack_speed * 0.7:
            new_state = "attack"
            
        # 3. Cast
        else:
            is_casting = False
            for slot, cd in self.spell_cooldowns.items():
                spell = self.equipment.get(slot)
                if spell:
                    max_cd = getattr(spell, "cooldown_max", 0)
                    if max_cd > 0 and cd > max_cd * 0.8:
                        is_casting = True
                        break
            if is_casting:
                new_state = "cast"
            
            # 4. Walk
            elif self.rect.topleft != self.last_pos:
                new_state = "run"
            
            # 5. Idle
            else:
                new_state = "idle"
            
        # Set the image for the renderer
        if self.sprites.get(new_state):
            self.image = self.sprites[new_state]
        else:
            # Fallback to idle if a state is missing
            self.image = self.sprites.get("idle", self.image)

        # Store position for next frame's movement check
        self.last_pos = self.rect.topleft
