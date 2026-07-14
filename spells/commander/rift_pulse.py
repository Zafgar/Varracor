import math
import pygame
from items.base_item import Spell
from sound_manager import sound_system


class RiftPulse(Spell):
    """Vortex-pulssi: "antakaa tilaa" -kyky (pelitesti 17). Repeämä
    avautuu hetkeksi Commanderin ympärille: pieni vahinko, mutta KOVA
    sinkaisu poispäin + lyhyt hidastus kaikille lähivihollisille."""

    def __init__(self):
        super().__init__()
        self.name = "Rift Pulse"
        self.tier = 1
        self.rarity = "Legendary"   # Commander-magia, ei myynnissä
        self.cost = 0
        self.description = ("The Vortex breathes out: shove every enemy "
                            "away from you and slow them briefly.")

        self.mana_cost = 12
        self.cooldown_max = 300     # 5 s
        self.range = 150            # vaikutussäde (piirtyy kantamarinkinä)
        self.damage = 4              # pieni piikki - tyonto on pointti
        self.scaling = {"INT": 0.1}
        self.is_skillshot = False   # itsensä ympärille, ei tähtäystä

        self.icon_color = (50, 255, 200)  # Abyssal Teal

    def draw_card_icon(self, surface, x, y, size):
        cx, cy = x + size // 2, y + size // 2
        # Ulospäin sykkivät renkaat
        pygame.draw.circle(surface, (20, 60, 50), (cx, cy), int(size * 0.38), 2)
        pygame.draw.circle(surface, self.icon_color, (cx, cy), int(size * 0.26), 2)
        pygame.draw.circle(surface, (200, 255, 255), (cx, cy), int(size * 0.08))
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            sx = cx + math.cos(a) * size * 0.30
            sy = cy + math.sin(a) * size * 0.30
            ex = cx + math.cos(a) * size * 0.42
            ey = cy + math.sin(a) * size * 0.42
            pygame.draw.line(surface, self.icon_color, (sx, sy), (ex, ey), 2)

    def cast(self, caster, target, manager, target_pos=None):
        if caster.current_mana < self.mana_cost:
            return False
        caster.current_mana -= self.mana_cost

        dmg = int(self.damage + caster.intelligence * self.scaling.get("INT", 0))
        cx, cy = caster.rect.center

        # VFX: kaksi aaltoa + tärähdys
        try:
            manager.vfx.create_shockwave(cx, cy, color=(50, 255, 200),
                                         max_radius=self.range, width=6)
            manager.vfx.create_shockwave(cx, cy, color=(180, 255, 235),
                                         max_radius=int(self.range * 0.6),
                                         width=3)
            manager.trigger_screen_shake(5)
        except Exception:
            pass
        sound_system.play_sound("cmd_vortex_slash")

        my_team = getattr(caster, "team_color", None)
        for u in list(getattr(manager, "all_units", [])):
            if u is caster or getattr(u, "is_dead", False):
                continue
            if getattr(u, "team_color", None) == my_team:
                continue
            dx = u.rect.centerx - cx
            dy = u.rect.centery - cy
            dist = math.hypot(dx, dy)
            if dist > self.range:
                continue
            u.take_damage(dmg, "Magic", attacker=caster, manager=manager)
            # Lyhyt hidastus: "antakaa tilaa"
            try:
                u.apply_status("Slow", 120)  # ~2 s
            except Exception:
                pass
            # Sinkaisu poispäin (ei seinien läpi: check_wall_collision)
            if dist > 0:
                push = 160
                px = (dx / dist) * push
                py = (dy / dist) * push
                try:
                    obstacles = getattr(manager.current_arena, "obstacles", None)
                    u.check_wall_collision(px, py, obstacles)
                except Exception:
                    u.rect.x += int(px)
                    u.rect.y += int(py)

        # Vortex-voiman käyttö: kylä huomaa (lore-reaktio)
        if manager and getattr(manager, "player_character", None) is caster:
            if hasattr(manager, "notice_vortex_use"):
                manager.notice_vortex_use("rift_pulse")
        return True
