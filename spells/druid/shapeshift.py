import math
import pygame

from items.base_item import Spell
from sound_manager import sound_system

"""Druidin muodonmuutokset (pelaajan suunnittelu):

- Muotoja 4-5; KARHU on ensimmäinen (tosi tank), pieni LOHIKÄÄRME viimeinen.
- Muoto EI kestä kuolemaan asti vaan niin kauan kuin MANA riittää: jokainen
  muoto kuluttaa manaa ollessaan päällä. Kun mana loppuu, muoto purkautuu.
- Muodon purkautuessa druid palaa siihen HP-määrään jossa hän oli muotoon
  MENNESSÄÄN (entry-HP talteen).
- Uuteen muotoon mennessä muodon HP määräytyy druidin SEN HETKISEN HP:n
  mukaan (suhteellinen osuus muodon max-HP:sta).
- Muodonvaihdolla on COOLDOWN joka alkaa kun muodosta palataan takaisin
  druidiksi -> max-HP:ta ei voi resetoida jatkuvasti poistumalla muodosta.
- Placeholder-grafiikat piirretään koodilla (ei asseteja).
"""

# Muotojen data: rank = vaadittu shapeshift_rank (druid-puun nodet).
FORMS = {
    "bear": {
        "name": "Bear Form", "rank": 1,
        "hp_mult": 2.2, "str_bonus": 15, "def_bonus": 6, "speed_mult": 0.85,
        "mana_per_sec": 6.0,
        "color": (122, 84, 48), "size": (58, 46),
        "desc": "A hulking tank: huge health, heavy claws, slow gait.",
    },
    "wolf": {
        "name": "Wolf Form", "rank": 2,
        "hp_mult": 1.3, "str_bonus": 8, "def_bonus": 0, "speed_mult": 1.35,
        "mana_per_sec": 5.0,
        "color": (120, 120, 132), "size": (50, 34),
        "desc": "A swift hunter: fast strikes and faster feet.",
    },
    "treant": {
        "name": "Treant Form", "rank": 3,
        "hp_mult": 2.8, "str_bonus": 12, "def_bonus": 12, "speed_mult": 0.6,
        "mana_per_sec": 8.0,
        "color": (86, 110, 62), "size": (54, 62),
        "desc": "Living timber: immense bulk and bark like iron, but slow.",
    },
    "panther": {
        "name": "Panther Form", "rank": 4,
        "hp_mult": 1.2, "str_bonus": 14, "def_bonus": 0, "speed_mult": 1.5,
        "mana_per_sec": 9.0,
        "color": (44, 40, 56), "size": (52, 32),
        "desc": "A shadow with claws: fragile, vicious, blindingly quick.",
    },
    "dragon": {
        "name": "Dragon Whelp Form", "rank": 5,
        "hp_mult": 2.0, "str_bonus": 26, "def_bonus": 8, "speed_mult": 1.1,
        "mana_per_sec": 14.0,
        "color": (160, 60, 60), "size": (60, 48),
        "desc": "The final secret: a small dragon of tooth, wing and flame.",
    },
}

SHIFT_COOLDOWN = 720   # 12 s - alkaa muodosta PALATTAESSA


def shapeshift_rank(unit):
    return int((getattr(unit, "school_effects", {}) or {})
               .get("shapeshift_rank", 0))


def in_form(unit):
    return getattr(unit, "shapeshift_form", None) is not None


def can_enter(unit, form_id):
    form = FORMS.get(form_id)
    if form is None:
        return False, "Unknown form"
    if in_form(unit):
        return False, "Already shapeshifted"
    if shapeshift_rank(unit) < form["rank"]:
        return False, f"Requires shapeshift rank {form['rank']}"
    if int(getattr(unit, "shapeshift_cooldown", 0)) > 0:
        return False, "Shapeshift on cooldown"
    if unit.current_mana < 10:
        return False, "Not enough mana"
    return True, "OK"


def _build_form_image(form_id):
    """Koodipiirretty placeholder-peto (ei asseteja)."""
    form = FORMS[form_id]
    w, h = form["size"]
    c = form["color"]
    dark = tuple(max(0, x - 34) for x in c)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body = pygame.Rect(2, h // 3, w - 8, h - h // 3 - 2)
    pygame.draw.ellipse(surf, c, body)
    pygame.draw.ellipse(surf, dark, body, 2)
    # Pää
    head_r = max(6, h // 4)
    hx = w - head_r - 2
    hy = h // 3
    pygame.draw.circle(surf, c, (hx, hy), head_r)
    pygame.draw.circle(surf, dark, (hx, hy), head_r, 2)
    # Silmä
    pygame.draw.circle(surf, (250, 220, 120), (hx + head_r // 3, hy - 2), 2)
    # Korvat / sarvet / siivet muodon mukaan
    if form_id == "bear":
        pygame.draw.circle(surf, dark, (hx - head_r + 2, hy - head_r + 2), 4)
        pygame.draw.circle(surf, dark, (hx + head_r - 4, hy - head_r + 2), 4)
    elif form_id in ("wolf", "panther"):
        pygame.draw.polygon(surf, dark, [(hx - 6, hy - head_r + 2),
                                          (hx - 2, hy - head_r - 6),
                                          (hx + 2, hy - head_r + 2)])
    elif form_id == "treant":
        for k in range(3):
            bx = 8 + k * (w // 4)
            pygame.draw.line(surf, dark, (bx, h // 3), (bx - 4, 2), 3)
            pygame.draw.circle(surf, (110, 160, 80), (bx - 4, 4), 4)
    elif form_id == "dragon":
        # Siipi + häntäpiikki
        pygame.draw.polygon(surf, dark, [(w // 3, h // 3),
                                          (w // 6, 2),
                                          (w // 2, h // 3 - 4)])
        pygame.draw.polygon(surf, dark, [(2, h - 8), (10, h - 14),
                                          (10, h - 4)])
    # Jalat
    for k in range(4):
        lx = 8 + k * ((w - 20) // 3)
        pygame.draw.rect(surf, dark, (lx, h - 8, 5, 8))
    return surf


def enter_form(unit, form_id, manager=None):
    ok, why = can_enter(unit, form_id)
    if not ok:
        return False
    form = FORMS[form_id]

    # Talteen: entry-HP (tähän palataan) ja alkuperäiset statit
    unit._shift_saved = {
        "entry_hp": int(unit.current_hp),
        "max_hp": int(unit.max_hp),
        "strength": int(unit.strength),
        "defense": int(unit.defense),
        "speed_multiplier": float(getattr(unit, "speed_multiplier", 1.0)),
        "image": getattr(unit, "image", None),
    }

    # Muodon HP määräytyy druidin SEN HETKISEN HP:n mukaan (suhteellinen).
    frac = max(0.05, unit.current_hp / max(1, unit.max_hp))
    form_max = int(unit.max_hp * form["hp_mult"])
    unit.max_hp = form_max
    unit.current_hp = max(1, int(form_max * frac))
    unit.strength += form["str_bonus"]
    unit.defense += form["def_bonus"]
    unit.speed_multiplier = getattr(unit, "speed_multiplier", 1.0) * form["speed_mult"]

    unit.shapeshift_form = form_id
    unit._shift_mana_acc = 0.0
    # Placeholder-grafiikka
    try:
        unit.image = _build_form_image(form_id)
    except Exception:
        pass
    if manager is not None:
        try:
            from spells.spell_vfx import pulse_ring
            pulse_ring(manager, unit.rect.centerx, unit.rect.centery,
                       "Nature", 60)
        except Exception:
            pass
    try:
        sound_system.play_sound("recruit")
    except Exception:
        pass
    return True


def exit_form(unit, manager=None, broken=False):
    """Palauttaa druidin: HP = entry-HP, statit ennalleen, cooldown ALKAA."""
    saved = getattr(unit, "_shift_saved", None)
    if saved is None or not in_form(unit):
        return False
    unit.max_hp = saved["max_hp"]
    unit.current_hp = max(1, min(saved["entry_hp"], saved["max_hp"]))
    unit.strength = saved["strength"]
    unit.defense = saved["defense"]
    unit.speed_multiplier = saved["speed_multiplier"]
    if saved.get("image") is not None:
        unit.image = saved["image"]
    unit.shapeshift_form = None
    unit._shift_saved = None
    unit.is_dead = False   # muodon murtuminen EI tapa druidia
    # Cooldown alkaa kun muodosta palataan -> ei max-HP-resetin väärinkäyttöä
    unit.shapeshift_cooldown = SHIFT_COOLDOWN
    if manager is not None:
        try:
            from spells.spell_vfx import impact_burst
            impact_burst(manager, unit.rect.centerx, unit.rect.centery,
                         "Nature", radius=40, sparks=10)
        except Exception:
            pass
    return True


def tick(unit, manager=None):
    """Kutsutaan joka frame (Gladiator.update): manan kulutus + cooldown."""
    cd = int(getattr(unit, "shapeshift_cooldown", 0))
    if cd > 0:
        unit.shapeshift_cooldown = cd - 1
    if not in_form(unit):
        return
    form = FORMS.get(unit.shapeshift_form)
    if form is None:
        unit.shapeshift_form = None
        return
    # Kuolettava vahinko murtaa muodon -> druid palaa entry-HP:hen
    if unit.current_hp <= 0 or getattr(unit, "is_dead", False):
        exit_form(unit, manager, broken=True)
        return
    # Mana kuluu joka frame; kun loppuu, muoto purkautuu
    unit._shift_mana_acc = getattr(unit, "_shift_mana_acc", 0.0) \
        + form["mana_per_sec"] / 60.0
    if unit._shift_mana_acc >= 1.0:
        drain = int(unit._shift_mana_acc)
        unit._shift_mana_acc -= drain
        unit.current_mana -= drain
    if unit.current_mana <= 0:
        unit.current_mana = 0
        exit_form(unit, manager)


class ShapeshiftSpell(Spell):
    """Equipattava 'kivi': castaus muuttaa druidin muotoon; castaus muodossa
    palauttaa druidiksi (cooldown alkaa paluusta)."""

    _META = {"bear": (2, 350), "wolf": (3, 800), "treant": (4, 1600),
             "panther": (5, 2800), "dragon": (6, 6000)}

    def __init__(self, form_id):
        super().__init__()
        form = FORMS[form_id]
        self.form_id = form_id
        self.name = form["name"]
        tier, price = self._META.get(form_id, (2, 500))
        self.tier = tier
        self.cost = price
        self.school = "druidism"
        self.archetype = "shapeshift"
        self.damage_type = "Nature"
        self.rarity = "Rare" if form["rank"] < 5 else "Legendary"
        self.mana_cost = 10          # sisäänmenon hinta; ylläpito kuluttaa lisää
        self.cooldown_max = 30
        self.range = 0
        self.is_skillshot = False
        self.icon_color = form["color"]
        self.description = form["desc"]

    def describe(self):
        form = FORMS[self.form_id]
        lines = [form["desc"], ""]
        lines.append(f"School: Druidism   Tier: {self.tier}   ({self.rarity})")
        lines.append(f"Requires: Shapeshift rank {form['rank']} (Druid tree)")
        lines.append(f"Form: HP x{form['hp_mult']}, STR +{form['str_bonus']}, "
                     f"DEF +{form['def_bonus']}, speed x{form['speed_mult']}")
        lines.append(f"Upkeep: {form['mana_per_sec']:.0f} mana/s while "
                     f"shifted   Entry: {self.mana_cost} mana   "
                     f"Price: {self.cost} SP")
        lines.append("")
        lines.append("The form lasts while mana holds. Leaving the form "
                     "returns you to the health you entered with, and "
                     "shapeshifting goes on cooldown.")
        return "\n".join(lines)

    def cast(self, caster, target, manager, target_pos=None):
        # Muodossa castaus = palaa druidiksi (cooldown alkaa)
        if in_form(caster):
            if caster.shapeshift_form == self.form_id:
                return exit_form(caster, manager)
            return False    # eri muoto päällä - palaa ensin druidiksi
        if caster.current_mana < self.mana_cost:
            return False
        if not enter_form(caster, self.form_id, manager):
            return False
        caster.current_mana -= self.mana_cost
        return True

    def draw_card_icon(self, surface, x, y, size):
        form = FORMS[self.form_id]
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, (18, 26, 18), rect, border_radius=8)
        pygame.draw.rect(surface, (120, 210, 120), rect, 2, border_radius=8)
        # Pieni tassunjälki
        cx, cy = x + size // 2, y + size // 2
        pygame.draw.ellipse(surface, form["color"],
                            (cx - 7, cy - 2, 14, 11))
        for k in range(3):
            pygame.draw.circle(surface, form["color"],
                               (cx - 6 + k * 6, cy - 7), 3)


def make_form_spells():
    """Kaikki muotoloitsut kauppaan (rank-vaatimus näkyy selitteessä)."""
    return [ShapeshiftSpell(fid) for fid in
            ("bear", "wolf", "treant", "panther", "dragon")]
