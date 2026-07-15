# spells/spell_vfx.py
"""Näyttävät, täysin koodilla piirretyt loitsu-VFX:t. Kaikki nojaa koodiin
(ei kuva-asseteja), joten glow/partikkelit tehdään pehmeillä alpha-kehillä.

Sisältää:
- ELEMENTS: elementtipaletit (glow/core/spark) vahinkotyypeittäin
- glow_surface(): pehmeä hehkuympyrä (välimuistitettu)
- Mote / Flash: ajautuvat/haihtuvat hehkupartikkelit
- TieredBolt: kerroksellinen, sykkivä hehkuammus + vana + osumaräjähdys
- impact_burst / aoe_burst / cast_flash / channel_beam: rikkaat efektit
"""
import math
import random
import pygame

from vfx import Projectile, VFXSprite


# Vahinkotyyppien paletit: (glow=ulkohehku, core=ydin, spark=kipinä)
ELEMENTS = {
    "Fire":      {"glow": (255, 120, 30),  "core": (255, 230, 150), "spark": (255, 160, 60),  "rise": -0.18},
    "Frost":     {"glow": (120, 200, 255), "core": (235, 250, 255), "spark": (180, 225, 255), "rise": 0.05},
    "Arcane":    {"glow": (170, 90, 240),  "core": (235, 205, 255), "spark": (205, 150, 255), "rise": 0.0},
    "Lightning": {"glow": (110, 195, 255), "core": (255, 255, 255), "spark": (185, 240, 255), "rise": 0.0},
    "Holy":      {"glow": (255, 215, 110), "core": (255, 255, 235), "spark": (255, 240, 170), "rise": -0.14},
    "Necrotic":  {"glow": (80, 200, 120),  "core": (205, 255, 210), "spark": (150, 235, 165), "rise": -0.05},
    "Nature":    {"glow": (110, 200, 90),  "core": (215, 255, 180), "spark": (160, 235, 130), "rise": 0.12},
    "Poison":    {"glow": (150, 220, 80),  "core": (220, 255, 170), "spark": (185, 240, 120), "rise": 0.10},
    "Magic":     {"glow": (150, 150, 255), "core": (230, 230, 255), "spark": (190, 190, 255), "rise": 0.0},
    "Holy_ray":  {"glow": (255, 230, 140), "core": (255, 255, 240), "spark": (255, 245, 190), "rise": 0.0},
}


def palette(damage_type):
    return ELEMENTS.get(damage_type, ELEMENTS["Magic"])


# --- Pehmeä hehkuympyrä (radial gradient alpha-kehinä), välimuistitettu ---
_GLOW_CACHE = {}


def glow_surface(radius, color, max_alpha=170, layers=8):
    radius = max(2, int(radius))
    max_alpha = max(10, min(255, (int(max_alpha) // 10) * 10))
    key = (radius, color, max_alpha)
    surf = _GLOW_CACHE.get(key)
    if surf is None:
        d = radius * 2
        surf = pygame.Surface((d, d), pygame.SRCALPHA)
        for k in range(layers, 0, -1):
            r = max(1, int(radius * k / layers))
            a = int(max_alpha * ((layers - k + 1) / layers) ** 1.7)
            pygame.draw.circle(surf, (color[0], color[1], color[2], a),
                               (radius, radius), r)
        if len(_GLOW_CACHE) < 4000:
            _GLOW_CACHE[key] = surf
    return surf


class Mote(VFXSprite):
    """Ajautuva, haihtuva hehkupartikkeli (kipinä/lehti/kaasupilvi)."""
    def __init__(self, x, y, color, size=6, life=18, drift=1.0, gravity=0.0):
        super().__init__(x, y, life)
        self.color = color
        self.size = size
        self.gravity = gravity
        self.vx = random.uniform(-drift, drift)
        self.vy = random.uniform(-drift, drift)
        self.fx, self.fy = float(x), float(y)
        self._render(1.0)

    def _render(self, frac):
        g = glow_surface(max(2, int(self.size * (0.5 + 0.5 * frac))),
                         self.color, int(150 * frac))
        self.image = g
        self.rect = g.get_rect(center=(int(self.fx), int(self.fy)))

    def update(self, obstacles=None):
        self.timer += 1
        if self.timer >= self.duration:
            self.kill()
            return
        self.fx += self.vx
        self.fy += self.vy
        self.vy += self.gravity
        self._render(1.0 - self.timer / self.duration)


class Flash(VFXSprite):
    """Kirkas hehkupurske joka laajenee ja haihtuu."""
    def __init__(self, x, y, color, radius, life=16):
        super().__init__(x, y, life)
        self.color = color
        self.radius = radius
        self.cx, self.cy = x, y
        self._render(0.0)

    def _render(self, frac):
        r = max(2, int(self.radius * (0.35 + 0.65 * frac)))
        g = glow_surface(r, self.color, int(200 * (1.0 - frac)))
        self.image = g
        self.rect = g.get_rect(center=(self.cx, self.cy))

    def update(self, obstacles=None):
        self.timer += 1
        if self.timer >= self.duration:
            self.kill()
            return
        self._render(self.timer / self.duration)


class TieredBolt(Projectile):
    """Kerroksellinen hehkuammus: ulkohehku + ydin + valkoinen keskus +
    kiertävät kipinät + haihtuva vana. Osumassa rikas elementtiräjähdys.
    Käyttäytyminen (nuke/aoe/dot) tulee liitetystä spell-oliosta."""

    def __init__(self, x, y, target_pos, speed, damage, owner, manager, spell):
        self.spell = spell
        pal = palette(getattr(spell, "damage_type", "Magic"))
        self.glow = pal["glow"]
        self.core = pal["core"]
        self.spark = pal["spark"]
        self.core_r = 7 + min(7, int(getattr(spell, "tier", 1)))
        self.box = self.core_r * 6
        img = pygame.Surface((self.box, self.box), pygame.SRCALPHA)
        super().__init__(x, y, target_pos, speed, damage, owner, manager,
                         image=img, duration=110)
        self._t = 0
        self._render()

    def _render(self):
        s = self.box
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        c = s // 2
        pulse = 1.0 + 0.18 * math.sin(self._t * 0.4)
        # 1. ulkohehku
        g = glow_surface(int(self.core_r * 2.3 * pulse), self.glow, 80)
        surf.blit(g, (c - g.get_width() // 2, c - g.get_height() // 2))
        # 2. ydin
        cg = glow_surface(int(self.core_r * pulse), self.core, 220)
        surf.blit(cg, (c - cg.get_width() // 2, c - cg.get_height() // 2))
        # 3. valkoinen keskus
        pygame.draw.circle(surf, (255, 255, 255), (c, c),
                           max(2, int(self.core_r * 0.42)))
        # 4. kiertävät kipinät
        for k in range(3):
            ang = self._t * 0.35 + k * (2 * math.pi / 3)
            ox = math.cos(ang) * self.core_r * 1.5
            oy = math.sin(ang) * self.core_r * 1.5
            pygame.draw.circle(surf, self.spark,
                               (int(c + ox), int(c + oy)), 2)
        self.image = surf
        self.rect = self.image.get_rect(
            center=(int(self.pos_x), int(self.pos_y)))

    def update(self, obstacles=None):
        self._t += 1
        # vana (haihtuva hehkumote)
        try:
            self.manager.vfx.add_effect(
                Mote(self.pos_x, self.pos_y, self.glow,
                     size=self.core_r, life=12, drift=0.5))
        except Exception:
            pass
        super().update(obstacles)   # liike + törmäys -> on_hit/on_wall_hit
        if self.alive():
            self._render()

    # ---- osuma: vahinko + arkkityyppi + räjähdys ----
    def on_hit(self, target):
        sp = self.spell
        dtype = getattr(sp, "damage_type", "Magic")
        if sp.archetype == "aoe":
            self._explode()
            return
        target.take_damage(self.damage, dtype, self.owner, self.manager)
        if sp.archetype == "dot":
            st = _dot_status(dtype)
            per = max(1, int(self.damage * 0.35))
            try:
                target.apply_status(st, 180, per)
            except Exception:
                pass
        impact_burst(self.manager, self.rect.centerx, self.rect.centery,
                     dtype, radius=int(self.core_r * 3.2),
                     sparks=10 + sp.tier)

    def on_wall_hit(self):
        if self.spell.archetype == "aoe":
            self._explode()
        else:
            impact_burst(self.manager, self.rect.centerx, self.rect.centery,
                         getattr(self.spell, "damage_type", "Magic"),
                         radius=int(self.core_r * 2.6), sparks=6)
            self.kill()

    def _explode(self):
        sp = self.spell
        cx, cy = self.rect.center
        radius = int(getattr(sp, "radius", 100))
        aoe_burst(self.manager, cx, cy, getattr(sp, "damage_type", "Magic"),
                  radius)
        owner_team = getattr(self.owner, "team_color", None)
        for u in list(self.manager.all_units):
            if u is self.owner or getattr(u, "is_dead", False):
                continue
            if getattr(u, "team_color", None) == owner_team:
                continue
            if math.hypot(u.rect.centerx - cx, u.rect.centery - cy) <= radius:
                u.take_damage(self.damage, getattr(sp, "damage_type", "Magic"),
                              self.owner, self.manager)
        self.kill()


def _dot_status(damage_type):
    return {"Fire": "Burn"}.get(damage_type, "Poison")


# --- Rikkaat efektifunktiot ---
def impact_burst(manager, x, y, damage_type, radius=42, sparks=10):
    pal = palette(damage_type)
    vfx = manager.vfx
    try:
        vfx.add_effect(Flash(x, y, pal["core"], int(radius * 0.8)))
        vfx.create_shockwave(x, y, color=pal["glow"], max_radius=radius,
                             width=4)
        vfx.create_impact_sparks(x, y, color=pal["spark"], count=sparks)
        for _ in range(max(3, sparks // 2)):
            vfx.add_effect(Mote(x, y, pal["glow"], size=6, life=24,
                                drift=2.4, gravity=pal["rise"]))
    except Exception:
        pass


def aoe_burst(manager, x, y, damage_type, radius=110):
    pal = palette(damage_type)
    vfx = manager.vfx
    try:
        vfx.add_effect(Flash(x, y, pal["core"], radius, life=20))
        # kaksi laajenevaa kehää
        vfx.create_shockwave(x, y, color=pal["glow"], max_radius=radius,
                             width=6)
        vfx.create_shockwave(x, y, color=pal["spark"],
                             max_radius=int(radius * 0.6), width=3)
        vfx.create_impact_sparks(x, y, color=pal["spark"], count=22)
        for _ in range(18):
            ang = random.uniform(0, 2 * math.pi)
            d = random.uniform(0.2, 1.0) * radius
            mx = x + math.cos(ang) * d
            my = y + math.sin(ang) * d
            vfx.add_effect(Mote(mx, my, pal["glow"], size=8, life=30,
                                drift=1.6, gravity=pal["rise"]))
    except Exception:
        pass


def cast_flash(manager, caster, damage_type):
    """Pieni hehkupurske loitsijan kohdalla loitsua heitettäessä."""
    pal = palette(damage_type)
    try:
        cx, cy = caster.rect.centerx, caster.rect.centery - 10
        manager.vfx.add_effect(Flash(cx, cy, pal["core"], 22, life=12))
        for _ in range(5):
            manager.vfx.add_effect(Mote(cx, cy, pal["glow"], size=5,
                                        life=16, drift=1.6, gravity=-0.1))
    except Exception:
        pass


def pulse_ring(manager, x, y, damage_type, radius):
    """Utility-loitsun oma alue-pulssi: kaksi kehää + kipinäkranssi."""
    pal = palette(damage_type)
    try:
        manager.vfx.create_shockwave(x, y, color=pal["glow"],
                                     max_radius=radius, width=6)
        manager.vfx.create_shockwave(x, y, color=pal["spark"],
                                     max_radius=int(radius * 0.55), width=3)
        for _ in range(14):
            ang = random.uniform(0, 2 * math.pi)
            mx = x + math.cos(ang) * radius * 0.7
            my = y + math.sin(ang) * radius * 0.7
            manager.vfx.add_effect(Mote(mx, my, pal["glow"], size=6,
                                        life=22, drift=1.2))
    except Exception:
        pass
