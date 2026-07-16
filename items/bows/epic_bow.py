import pygame
from items.base_item import Weapon
from sound_manager import sound_system


class EpicBow(Weapon):
    """
    Epic bow:
    - very high DEX scaling (3.0x)
    - very long range
    - Ethereal Volley (cooldown): next hit gets huge bonus, and fires 3 arrow VFX on attack start
    """

    VOLLEY_COOLDOWN_MS = 7500
    VOLLEY_BONUS_FLAT = 34
    VOLLEY_DEX_SCALE = 1.20  # bonus += DEX * this
    VOLLEY_ARROWS = 3

    def __init__(self):
        super().__init__()
        self.name = "Astraeum Longbow"
        self.rarity = "Epic"
        self.cost = 2400
        self.description = "An epic longbow humming with starfire. Ethereal Volley triggers on cooldown for overwhelming shots."

        # AI/Gladiator logic
        self.type = "ranged"
        self.two_handed = True  # varaa molemmat kadet - ei kilpea/off-handia
        self.slot_type = "main_hand"

        # core stats
        self.damage = 12
        self.attack_range = 520   # todella pitkä
        self.speed_bonus = 0.00   # epic: ei hidasta
        self.scaling = {"DEX": 3.0}

        # internal
        self._volley_last_used = -999999999
        self._volley_armed = False

    # -------------------------
    # helpers
    # -------------------------
    def _now_ms(self):
        try:
            return pygame.time.get_ticks()
        except Exception:
            return 0

    def _ready(self):
        return (self._now_ms() - self._volley_last_used) >= self.VOLLEY_COOLDOWN_MS

    def _play(self, name):
        try:
            sound_system.play_sound(name)
        except Exception:
            pass

    def _apply_bonus_damage(self, target, amount):
        if amount <= 0 or target is None:
            return

        for fn_name in ("take_damage", "receive_damage", "apply_damage"):
            fn = getattr(target, fn_name, None)
            if callable(fn):
                try:
                    fn(int(amount))
                    return
                except Exception:
                    pass

        if hasattr(target, "current_hp"):
            try:
                target.current_hp = max(0, int(target.current_hp) - int(amount))
            except Exception:
                pass

    # -------------------------
    # visuals
    # -------------------------
    def draw_card_icon(self, surface, x, y, size):
        wood = (90, 70, 140)          # purppura runko
        glow = (170, 210, 255)        # sinertävä glow
        star = (255, 245, 200)        # tähtipisteet
        string = (200, 235, 255)      # “energiäjänne”

        # Bow arc
        rect = pygame.Rect(x + size * 0.18, y + size * 0.08, size * 0.64, size * 0.84)
        pygame.draw.arc(surface, wood, rect, 3.14159 / 2, 3.14159 * 1.5, 5)

        # energy string
        pygame.draw.line(surface, string, (x + size * 0.52, y + size * 0.10), (x + size * 0.52, y + size * 0.90), 2)

        # star speckles
        pygame.draw.circle(surface, star, (int(x + size * 0.30), int(y + size * 0.25)), 2)
        pygame.draw.circle(surface, star, (int(x + size * 0.70), int(y + size * 0.35)), 2)
        pygame.draw.circle(surface, star, (int(x + size * 0.62), int(y + size * 0.78)), 2)

        # “ready” marker
        if self._ready():
            pygame.draw.circle(surface, glow, (int(x + size * 0.82), int(y + size * 0.80)), max(3, int(size * 0.07)))

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        offset_x = 7 if facing_right else -7
        hand_x = unit_rect.centerx + offset_x
        hand_y = unit_rect.centery

        top = (hand_x, hand_y - 18)
        bot = (hand_x, hand_y + 18)
        mid = (hand_x + (12 if facing_right else -12), hand_y)

        # pull anim (smooth)
        pull = 0.0
        if attack_cooldown > 0 and attack_cooldown < 24:
            pull = (1.0 - (attack_cooldown / 24.0)) * 14.0

        # volley => näkyvä “charged” aina kun armed/ready
        if self._volley_armed or self._ready():
            pull = max(pull, 7.0)

        pull_x = hand_x + (-14 if facing_right else 14) * (pull / 14.0)

        # limbs
        pygame.draw.lines(surface, (90, 70, 140), False, [top, mid, bot], 3)

        # energy string
        pygame.draw.lines(surface, (200, 235, 255), False, [top, (pull_x, hand_y), bot], 2)

        # arrow preview
        if pull > 2:
            tip_x = pull_x + (24 if facing_right else -24)
            pygame.draw.line(surface, (190, 200, 210), (pull_x, hand_y), (tip_x, hand_y), 2)

        # glow on mid when volley armed
        if self._volley_armed:
            pygame.draw.circle(surface, (170, 210, 255), (int(mid[0]), int(mid[1])), 5)

    # -------------------------
    # hooks (same signature as your WeakBow/RareBow)
    # -------------------------
    def on_attack_start(self, attacker, target, manager):
        self._volley_armed = self._ready()

        self._play("attack_bow")
        if self._volley_armed:
            self._play("power_strike")

        # vfx arrows
        try:
            a = attacker.rect.center
            b = target.rect.center

            # 1 perus nuoli
            manager.vfx.create_arrow(a, b)

            # 2 lisä nuolta jos volley armed (näyttää “mahtavalta”)
            if self._volley_armed:
                for i in range(self.VOLLEY_ARROWS - 1):
                    # pieni hajonta: targettiin eri pisteisiin
                    dx = (i - 0.5) * 18
                    dy = (i - 0.5) * 10
                    manager.vfx.create_arrow(a, (b[0] + dx, b[1] + dy))
        except Exception:
            pass

    def on_hit(self, attacker, target, damage_dealt, manager):
        # basic hit feedback
        try:
            if damage_dealt > 0 and not getattr(target, "is_dead", False):
                manager.vfx.create_blood(target.rect.centerx, target.rect.centery)
        except Exception:
            pass

        # volley bonus
        if not self._volley_armed:
            return

        if damage_dealt <= 0:
            self._volley_armed = False
            return

        dex = int(getattr(attacker, "dexterity", 0) or 0)
        bonus = int(self.VOLLEY_BONUS_FLAT + dex * self.VOLLEY_DEX_SCALE)

        self._apply_bonus_damage(target, bonus)

        self._volley_last_used = self._now_ms()
        self._volley_armed = False

        # heavy hit sound
        self._play("hit_heavy")
