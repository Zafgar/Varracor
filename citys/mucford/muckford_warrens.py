"""Playable Muckford Warrens beneath the Tier 0 city.

The area is deliberately code-rendered so its map, NPCs, quests, collision,
persistence and boss mechanics can be tuned before final painted assets exist.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from assets.tiles.prop import Prop
from menus.gameplay_screen import GameplayScreen
from settings import ENEMY_TEAM, GOLD_COLOR, GRAY, GREEN, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from sound_manager import sound_system
from ui_kit import draw_text, font_main, font_small
# Pelitesti 25: OIKEAT rottayksiköt (samat kuin Rat King Lair /
# maps.rat_sewer) - ei enää koodipiirrettyjä placeholder-silhuetteja
# (units.muckford_warrens_monsters poistettu).
from units.rat import GiantRat, BruteRat
from units.rat_rider import RatRider
from units.rat_king import RatKing
from units.villager import Villager
from vfx import VFXManager


WARRENS_WIDTH = 4600
WARRENS_HEIGHT = 2800
WARRENS_SEED = 91377

# --- Rat Kingin nimi ja lore (pelitesti 26) ---
# Rat King on itse Vortex Abyssal -alueen asukki. Hän yrittää kerätä
# tarpeeksi abyssal-voimaa vallatakseen Muckfordin ja levitäkseen
# laajemmalle. "Mestari" vaatii että nämä valtakunnat maksavat - miksi,
# sitä ei kerrota.
RAT_KING_NAME = "Skrivvax, the Gnawing Crown"

# Vaihekohtaiset tavoitemäärät
CULL_TARGET = 12       # vaihe 1: montako perusrottaa kaadettava
INVASION_TARGET = 10   # vaihe 2: invaasioaallon rotat ennen sulkua
CAMP_TARGET = 8        # vaihe 4: rottaleirin vartijat

# Uusi 8-vaiheinen questlinja (Rat King on vasta lopussa)
WARRENS_OBJECTIVES = {
    0: "Climb down and speak with Hamo at the cellar hatch.",
    1: "Cull the sewer rats gnawing at Muckford's foundations "
       f"(0/{CULL_TARGET}).",
    2: "A rat invasion pours from a breach - clear the wave and seal "
       "the breach tunnel.",
    3: "Turn the flood valve to drain the sunken passage ahead.",
    4: "Storm the rats' camp and read what they left behind.",
    5: "The tremor cracked the old passage - bridge the broken floor "
       "with planks.",
    6: "Reach the flooded workshop, raise the Frog Smith's gate-ram, "
       "and open the way to the deep cistern.",
    7: f"Descend into the Abyssal Cistern and end {RAT_KING_NAME}.",
    8: "The Warrens are secured. Rat raids against Muckford have ended.",
}

# Kerättävät resurssit turvallisilta kammioilta (aktivoituvat kun
# invaasio on suljettu, vaihe 3+). Yrttejä, sieniä ja outoja juttuja
# reseptejä varten.
# Keräyssolmut hajallaan koko laajalla kartalla (eri haaroissa, jotta
# keräily palkitsee tunneleiden tutkimisen - pelitesti 26b)
GATHER_NODES = (
    ("gather_moss_1", "moss", 980, 520), ("gather_moss_2", "moss", 2500, 2320),
    ("gather_cap_1", "cap", 1560, 1680), ("gather_cap_2", "cap", 3360, 900),
    ("gather_root_1", "root", 820, 2360), ("gather_root_2", "root", 2680, 640),
    ("gather_odd_1", "oddity", 3520, 2000), ("gather_odd_2", "oddity", 1900, 480),
)
GATHER_KINDS = {
    "moss": ("Sewer Moss", (86, 150, 96), "Damp luminous sewer moss."),
    "cap": ("Glowcap Mushroom", (150, 120, 200), "A softly glowing fungus."),
    "root": ("Rustroot Herb", (176, 120, 70), "A bitter iron-tinged herb."),
    "oddity": ("Bogwater Curio", (120, 170, 190), "Something strange the "
               "rats hoarded."),
}

# Vaihe 5: lankkusillan rakennusmateriaali
BRIDGE_MATERIAL = "Rough Timber"
BRIDGE_WOOD = 4
# Vaihe 6: sammakkosepän portti-ramin resepti (kytkee keräilyn mukaan)
DEVICE_RECIPE = {"Iron Ingot": 4, "Scrap Iron": 6, "Bogwater Curio": 2}
DEVICE_RECIPE_TEXT = "4 Iron Ingot, 6 Scrap Iron and 2 Bogwater Curio"


def _safe_sound(name: str) -> None:
    try:
        sound_system.play_sound(name)
    except Exception:
        pass


def warrens_state(manager) -> dict:
    global_data = manager.npc_state.setdefault("global", {})
    state = global_data.setdefault("muckford_warrens", {})
    state.setdefault("visits", 0)
    state.setdefault("quest_stage", 0)
    # Vaihe 1: rottakaadot
    state.setdefault("rats_culled", 0)
    state.setdefault("cull_reward_claimed", False)
    # Vaihe 2: invaasion sulku
    state.setdefault("invasion_kills", 0)
    state.setdefault("breach_sealed", False)
    state.setdefault("area_safe", False)          # keräys aukeaa
    # Vaihe 3: tulvaventtiili
    state.setdefault("valve_turned", False)
    # Vaihe 4: rottaleiri + lore
    state.setdefault("camp_kills", 0)
    state.setdefault("lore_read", False)
    state.setdefault("tremor_triggered", False)
    # Vaihe 5: lankkusilta
    state.setdefault("bridge_built", False)
    # Vaihe 6: sammakkosepän portti-ramin rakennus
    state.setdefault("smith_met", False)
    state.setdefault("smith_recruited", False)
    state.setdefault("device_built", False)
    # Vaihe 7-8: boss + raportti
    state.setdefault("boss_unlocked", False)
    state.setdefault("boss_defeated", False)
    state.setdefault("boss_reward_claimed", False)
    state.setdefault("boss_intro_seen", False)
    state.setdefault("report_reward_claimed", False)
    state.setdefault("city_raids_ended", False)
    state.setdefault("completed", False)
    state.setdefault("waste_exposure", 0)
    # Kerätyt solmut (id-lista)
    state.setdefault("gathered_nodes", [])
    return state


def sync_warrens_story(manager) -> bool:
    """Etenee vaiheesta seuraavaan kun ehdot täyttyvät. Palauttaa True jos
    vaihe muuttui."""
    state = warrens_state(manager)
    changed = False
    while True:
        stage = int(state.get("quest_stage", 0))
        if stage == 1 and int(state.get("rats_culled", 0)) >= CULL_TARGET:
            state["quest_stage"] = 2
        elif stage == 2 and state.get("breach_sealed"):
            state["quest_stage"] = 3
            state["area_safe"] = True    # keräys aukeaa
        elif stage == 3 and state.get("valve_turned"):
            state["quest_stage"] = 4
        elif stage == 4 and state.get("lore_read"):
            state["quest_stage"] = 5
            state["tremor_triggered"] = True
        elif stage == 5 and state.get("bridge_built"):
            state["quest_stage"] = 6
        elif stage == 6 and state.get("device_built"):
            state["quest_stage"] = 7
            state["boss_unlocked"] = True
        elif stage == 7 and state.get("boss_defeated"):
            state["quest_stage"] = 8
            state["city_raids_ended"] = True
        else:
            break
        changed = True
    return changed


def warrens_objective(manager) -> str:
    sync_warrens_story(manager)
    state = warrens_state(manager)
    stage = int(state.get("quest_stage", 0))
    if stage == 1:
        return WARRENS_OBJECTIVES[1].replace(
            f"(0/{CULL_TARGET})",
            f"({min(int(state.get('rats_culled', 0)), CULL_TARGET)}/"
            f"{CULL_TARGET})")
    return WARRENS_OBJECTIVES.get(stage, WARRENS_OBJECTIVES[8])


class RectObstacle:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.blocks_projectiles = True
        self.is_structure = True
        self.name = "Sewer Wall"


class WarrensProp(Prop):
    def __init__(self, x: int, y: int, width: int, height: int, style: str, blocking=False):
        super().__init__(x, y, width, height, color=(0, 0, 0))
        self.style = str(style)
        self.image_pos = (x, y)
        self.is_structure = bool(blocking)
        self.blocks_projectiles = bool(blocking)
        self.has_shadow = style not in {"bridge", "pipe", "grate", "water_marker"}
        self._redraw()

    def _redraw(self):
        w, h = self.rect.size
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        if self.style == "brick_wall":
            image.fill((47, 43, 42))
            for y in range(0, h, 28):
                offset = 20 if (y // 28) % 2 else 0
                for x in range(-offset, w, 40):
                    pygame.draw.rect(image, (67, 61, 58), (x + 2, y + 2, 36, 23), 2)
            pygame.draw.line(image, (26, 24, 24), (0, h - 5), (w, h - 5), 6)
        elif self.style == "pipe":
            pygame.draw.rect(image, (73, 73, 68), (0, h // 2 - 9, w, 18), border_radius=8)
            pygame.draw.line(image, (126, 118, 98), (3, h // 2 - 4), (w - 3, h // 2 - 4), 3)
            for x in range(18, w, 65):
                pygame.draw.rect(image, (47, 47, 45), (x, h // 2 - 14, 10, 28), 3)
        elif self.style == "bridge":
            pygame.draw.rect(image, (72, 61, 50), (0, 5, w, h - 10), border_radius=5)
            for x in range(4, w, 24):
                pygame.draw.rect(image, (119, 84, 48), (x, 8, 18, h - 16), border_radius=2)
                pygame.draw.line(image, (166, 123, 72), (x + 3, 12), (x + 14, 12), 2)
            pygame.draw.line(image, (48, 38, 32), (0, 7), (w, 7), 4)
            pygame.draw.line(image, (48, 38, 32), (0, h - 7), (w, h - 7), 4)
        elif self.style == "crate":
            pygame.draw.rect(image, (90, 61, 38), (4, 5, w - 8, h - 10), border_radius=4)
            pygame.draw.rect(image, (143, 101, 58), (4, 5, w - 8, h - 10), 4, border_radius=4)
            pygame.draw.line(image, (60, 43, 31), (10, 10), (w - 10, h - 10), 6)
            pygame.draw.line(image, (60, 43, 31), (w - 10, 10), (10, h - 10), 6)
        elif self.style == "bar_gate":
            for x in range(5, w, 14):
                pygame.draw.rect(image, (87, 82, 76), (x, 0, 7, h))
                pygame.draw.line(image, (139, 129, 111), (x + 2, 0), (x + 2, h), 2)
            for y in (20, h - 26):
                pygame.draw.rect(image, (55, 52, 49), (0, y, w, 12))
        elif self.style == "throne":
            pygame.draw.ellipse(image, (45, 36, 38), (5, h - 32, w - 10, 28))
            pygame.draw.rect(image, (84, 64, 54), (18, 32, w - 36, h - 54), border_radius=9)
            pygame.draw.polygon(image, (130, 94, 45), [(15, 38), (31, 4), (48, 30), (w // 2, 0), (w - 48, 30), (w - 31, 4), (w - 15, 38)])
            for x in range(28, w - 20, 24):
                pygame.draw.circle(image, (151, 65, 167), (x, 57), 5)
        elif self.style == "drain":
            pygame.draw.ellipse(image, (40, 38, 37), (2, 2, w - 4, h - 4))
            pygame.draw.ellipse(image, (102, 96, 85), (5, 5, w - 10, h - 10), 5)
            for x in range(16, w - 10, 18):
                pygame.draw.line(image, (78, 74, 68), (x, 9), (x, h - 9), 5)
        self.image = image


class CitySewerHatch(Prop):
    """Visible Muckford-side entrance added beside Hamo at runtime."""

    def __init__(self, x: int, y: int, cleared=False):
        super().__init__(x, y, 104, 72, color=(0, 0, 0))
        self.rect = pygame.Rect(x + 7, y + 32, 90, 34)
        self.image_pos = (x, y)
        self.has_shadow = False
        self.blocks_projectiles = False
        self.is_structure = False
        self.cleared = bool(cleared)
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((104, 72), pygame.SRCALPHA)
        pygame.draw.ellipse(image, (43, 39, 37), (3, 22, 98, 43))
        pygame.draw.ellipse(image, (104, 95, 79), (7, 18, 90, 43), 5)
        for x in range(20, 91, 15):
            pygame.draw.line(image, (78, 72, 64), (x, 25), (x, 56), 5)
        color = (103, 178, 118) if self.cleared else (168, 86, 191)
        pygame.draw.circle(image, color, (86, 18), 6)
        self.image = image


class GatherNode(Prop):
    """Kerättävä yrtti/sieni/outo juttu turvallisilta viemärikammioilta
    (pelitesti 26). E poimii kun alue on turvattu (invaasio suljettu).
    Antaa reseptimateriaaleja."""

    def __init__(self, node_id: str, kind: str, x: int, y: int, gathered=False):
        super().__init__(x, y, 60, 60, color=(0, 0, 0))
        self.node_id = str(node_id)
        self.kind = str(kind)
        self.gathered = bool(gathered)
        self.rect = pygame.Rect(x + 12, y + 34, 36, 22)
        self.image_pos = (x, y)
        self.has_shadow = False
        self.blocks_projectiles = False
        self.is_structure = False
        self._sway = random.uniform(0, 6.28)
        self._redraw()

    @property
    def resource_name(self):
        return GATHER_KINDS.get(self.kind, ("Curio",))[0]

    def _redraw(self):
        image = pygame.Surface((60, 60), pygame.SRCALPHA)
        col = GATHER_KINDS.get(self.kind, ("", (150, 150, 150)))[1]
        if self.gathered:
            pygame.draw.line(image, (60, 58, 52), (18, 52), (42, 52), 3)
        elif self.kind == "cap":  # sieni: lakit
            for cx, cy, r in ((22, 40, 10), (36, 44, 7), (30, 32, 8)):
                pygame.draw.rect(image, (150, 130, 110), (cx - 2, cy, 4, 12))
                pygame.draw.ellipse(image, col, (cx - r, cy - r + 2, r * 2, r + 4))
                pygame.draw.circle(image, (230, 220, 245), (cx - 3, cy - 2), 2)
        elif self.kind == "moss":  # sammal: matala läiskä
            pygame.draw.ellipse(image, col, (8, 40, 44, 16))
            for sx in (16, 28, 40):
                pygame.draw.circle(image, (140, 200, 150), (sx, 46), 4)
        else:  # yrtti/outo: varret + kukat
            for sx in (20, 30, 40):
                pygame.draw.line(image, (90, 130, 90), (sx, 54), (sx - 2, 30), 3)
                pygame.draw.circle(image, col, (sx - 2, 28), 5)
        self.image = image


class BreachTunnel(Prop):
    """Repeämätunneli josta rotta-invaasio vyöryy (vaihe 2). E sulkee sen
    kun aalto on lyöty."""

    def __init__(self, x: int, y: int, sealed=False):
        super().__init__(x, y, 150, 130, color=(0, 0, 0))
        self.sealed = bool(sealed)
        self.rect = pygame.Rect(x + 20, y + 60, 110, 60)
        self.image_pos = (x, y)
        self.blocks_projectiles = False
        self.is_structure = False
        self.pulse = random.randint(0, 120)
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((150, 130), pygame.SRCALPHA)
        if self.sealed:
            # Kivi/tiili tukittu
            pygame.draw.ellipse(image, (52, 47, 44), (15, 40, 120, 80))
            for ry in range(48, 112, 18):
                off = 14 if (ry // 18) % 2 else 0
                for rx in range(20 - off, 130, 28):
                    pygame.draw.rect(image, (74, 66, 60), (rx, ry, 24, 15), 2)
        else:
            # Musta aukko + violettia sumua
            pygame.draw.ellipse(image, (30, 26, 30), (12, 34, 126, 88))
            pygame.draw.ellipse(image, (8, 6, 10), (28, 46, 94, 64))
            for cx, cy, r in ((55, 74, 7), (82, 66, 9), (70, 90, 6)):
                pygame.draw.circle(image, (150, 70, 170), (cx, cy), r)
        self.image = image

    def update(self, *args, **kwargs):
        self.pulse = (self.pulse + 1) % 120


class FloodValve(Prop):
    """Iso tulvaventtiilipyörä (vaihe 3). E kääntää -> vesi laskee ja tie
    aukeaa eteenpäin."""

    def __init__(self, x: int, y: int, turned=False):
        super().__init__(x, y, 80, 96, color=(0, 0, 0))
        self.turned = bool(turned)
        self.rect = pygame.Rect(x + 16, y + 54, 48, 34)
        self.image_pos = (x, y)
        self.is_structure = False
        self.blocks_projectiles = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((80, 96), pygame.SRCALPHA)
        # Putki + laippa
        pygame.draw.rect(image, (66, 60, 54), (30, 40, 20, 52))
        pygame.draw.rect(image, (44, 40, 36), (24, 78, 32, 14))
        # Venttiilipyörä
        cx, cy = 40, 34
        wheel = (150, 196, 120) if self.turned else (176, 110, 84)
        pygame.draw.circle(image, wheel, (cx, cy), 22, 5)
        for a in range(0, 360, 60):
            r = math.radians(a + (30 if self.turned else 0))
            pygame.draw.line(image, wheel, (cx, cy),
                             (cx + 20 * math.cos(r), cy + 20 * math.sin(r)), 4)
        pygame.draw.circle(image, (40, 36, 32), (cx, cy), 6)
        self.image = image


class LoreBoard(Prop):
    """Rottaleirin loretaulu/kirje (vaihe 4): Rat Kingin suunnitelma ja
    Vortex Abyssal -lore. E lukee."""

    def __init__(self, x: int, y: int, read=False):
        super().__init__(x, y, 84, 104, color=(0, 0, 0))
        self.read = bool(read)
        self.rect = pygame.Rect(x + 14, y + 70, 56, 30)
        self.image_pos = (x, y)
        self.is_structure = False
        self.blocks_projectiles = False
        self._redraw()

    def _redraw(self):
        image = pygame.Surface((84, 104), pygame.SRCALPHA)
        # Jalat + lankkutaulu
        pygame.draw.line(image, (70, 52, 36), (22, 100), (22, 40), 6)
        pygame.draw.line(image, (70, 52, 36), (62, 100), (62, 40), 6)
        pygame.draw.rect(image, (108, 84, 54), (10, 24, 64, 44), border_radius=3)
        pygame.draw.rect(image, (72, 56, 36), (10, 24, 64, 44), 3, border_radius=3)
        # Naulattu kirje + violetti sinetti
        pygame.draw.rect(image, (222, 210, 180), (20, 30, 34, 30))
        for ly in range(35, 58, 5):
            pygame.draw.line(image, (120, 108, 92), (24, ly), (50, ly), 1)
        pygame.draw.circle(image, (150, 70, 170), (52, 58), 5)
        self.image = image


class BuildSite(Prop):
    """Rakennuspiste (pelitesti 26): lankkusilta (vaihe 5) tai sammakko-
    sepän portti-rami (vaihe 6). E rakentaa kun materiaalit riittävät."""

    def __init__(self, site_id: str, kind: str, x: int, y: int, w: int, h: int,
                 built=False):
        super().__init__(x, y, w, h, color=(0, 0, 0))
        self.site_id = str(site_id)
        self.kind = str(kind)   # "bridge" | "device"
        self.built = bool(built)
        self._w, self._h = w, h
        self.rect = pygame.Rect(x, y + h - 40, w, 40)
        self.image_pos = (x, y)
        self.is_structure = False
        self.blocks_projectiles = False
        self._redraw()

    def _redraw(self):
        W, H = self._w, self._h
        image = pygame.Surface((W, H), pygame.SRCALPHA)
        if self.kind == "bridge":
            if self.built:
                # Valmis lankkusilta
                pygame.draw.rect(image, (108, 82, 50), (0, H - 34, W, 26))
                for lx in range(4, W, 26):
                    pygame.draw.rect(image, (74, 56, 34), (lx, H - 34, 20, 26), 2)
            else:
                # Murtunut lattia + tyhjä aukko
                pygame.draw.rect(image, (18, 15, 18), (6, H - 30, W - 12, 24))
                for jx in (10, W // 2, W - 20):
                    pygame.draw.polygon(image, (40, 34, 34),
                                        [(jx, H - 30), (jx + 10, H - 30),
                                         (jx + 4, H - 8)])
        else:  # device: portti-rami / metallilaite
            if self.built:
                pygame.draw.rect(image, (120, 120, 130), (W // 2 - 40, H - 54, 80, 46), border_radius=4)
                pygame.draw.rect(image, (80, 80, 92), (W // 2 - 40, H - 54, 80, 46), 3, border_radius=4)
                pygame.draw.rect(image, (150, 150, 160), (W // 2 - 8, H - 40, 60, 16))
            else:
                # Tyhjä työpiste: alasin + telineet
                pygame.draw.rect(image, (60, 58, 62), (W // 2 - 26, H - 30, 52, 22), border_radius=3)
                pygame.draw.line(image, (90, 88, 92), (W // 2 - 40, H - 8),
                                 (W // 2 + 40, H - 8), 4)
        self.image = image


class MuckfordWarrensArena:
    def __init__(self, manager):
        self.manager = manager
        self.width = WARRENS_WIDTH
        self.height = WARRENS_HEIGHT
        self.props: List[object] = []
        self.floor_props: List[object] = []
        self.obstacles: List[object] = []
        # Uudet questlinjan interaktiivit (pelitesti 26)
        self.gather_nodes: List[GatherNode] = []
        self.breach: Optional[BreachTunnel] = None
        self.valve: Optional[FloodValve] = None
        self.lore_board: Optional[LoreBoard] = None
        self.bridge_site: Optional[BuildSite] = None
        self.device_site: Optional[BuildSite] = None
        self.bridges: List[pygame.Rect] = []
        self.tainted_channels: List[pygame.Rect] = []
        self.vfx = VFXManager()
        self.rng = random.Random(WARRENS_SEED)
        self.floor_image = pygame.Surface((self.width, self.height))
        self.flow_offset = 0
        self.fumes = []
        self.boss_gate: Optional[WarrensProp] = None
        self.city_exit = pygame.Rect(0, 300, 74, 500)
        self.low_fields_exit = pygame.Rect(0, self.height - 680, 74, 520)
        # Abyssal Cistern: bossiareena kaukana idässä (iso alue)
        self.royal_cistern = pygame.Rect(3860, 360, 660, 2080)
        self._generate_floor()
        self._build_level()
        self.refresh_persistent(manager)

    def _load_floor_tiles(self):
        """Lataa viemärin lattialaatat samoista lähteistä kuin Rat King
        Lair / maps.rat_sewer (pelitesti 25). Ilman assetteja tehdään
        laattamainen märkä kivilattia proseduraalisesti."""
        import os
        tiles = []
        for folder in ("sewer_floors", "floors"):
            base = os.path.join("assets", "tiles", folder)
            for fname in ("dungeon_floor_1.png", "dungeon_floor_2.png"):
                fpath = os.path.join(base, fname)
                if os.path.exists(fpath):
                    try:
                        img = pygame.image.load(fpath).convert()
                        tiles.append(pygame.transform.scale(img, (128, 128)))
                    except Exception:
                        pass
            if tiles:
                break
        if not tiles:
            for base_shade in (30, 34, 38):
                t = pygame.Surface((128, 128))
                t.fill((base_shade, base_shade - 3, base_shade - 4))
                for _ in range(40):
                    sx = self.rng.randint(0, 127)
                    sy = self.rng.randint(0, 127)
                    d = self.rng.randint(-6, 8)
                    pygame.draw.circle(t, (base_shade + d, base_shade - 3 + d,
                                           base_shade - 4 + d),
                                       (sx, sy), self.rng.randint(3, 9))
                pygame.draw.rect(t, (20, 18, 18), (0, 0, 128, 128), 2)
                tiles.append(t)
        return tiles

    def _generate_floor(self):
        tiles = self._load_floor_tiles()
        for ty in range(0, self.height, 128):
            for tx in range(0, self.width, 128):
                self.floor_image.blit(self.rng.choice(tiles), (tx, ty))
        # Kuivat huoltokäytävät kammioiden välillä (vaaleampi kivi)
        for a, b, wdt in (
            ((90, 620), (self.width - 230, 620), 150),
            ((180, 2150), (self.width - 310, 2150), 170),
            ((820, 620), (820, 2200), 135),
            ((1900, 580), (1900, 2230), 135),
            ((3000, 600), (3000, 2210), 135),
            ((3760, 700), (3760, 2100), 135),
        ):
            pygame.draw.line(self.floor_image, (58, 51, 47), a, b, wdt)
        # Viemärikanavat: kuljettavia mutta myrkyllisiä (wade-hazard)
        channels = (
            pygame.Rect(470, 1240, 3600, 250),
            pygame.Rect(1650, 300, 260, 2200),
            pygame.Rect(2900, 340, 250, 2100),
        )
        self.tainted_channels = [pygame.Rect(rect) for rect in channels]
        for rect in channels:
            pygame.draw.rect(self.floor_image, (30, 54, 47), rect, border_radius=16)
            pygame.draw.rect(self.floor_image, (58, 74, 61), rect, 9, border_radius=16)
            pygame.draw.line(self.floor_image, (93, 102, 76), rect.topleft, rect.topright, 4)
            pygame.draw.line(self.floor_image, (22, 34, 32), rect.bottomleft, rect.bottomright, 6)
        # Royal Cistern -kammio (bossiareena idässä)
        pygame.draw.ellipse(self.floor_image, (44, 36, 40), self.royal_cistern)
        pygame.draw.ellipse(self.floor_image, (83, 57, 86), self.royal_cistern, 14)

    def _add(self, prop, blocking=False):
        self.props.append(prop)
        if blocking or getattr(prop, "is_structure", False):
            self.obstacles.append(prop)

    def _build_level(self):
        w, h = self.width, self.height
        self.obstacles.extend(
            [
                RectObstacle((0, -40, w, 40)),
                RectObstacle((0, h, w, 40)),
                RectObstacle((-40, 0, 40, h)),
                RectObstacle((w, 0, 40, h)),
            ]
        )
        # Tiiliseinät jakavat kartan kammioihin (iso viemäriverkosto)
        wall_specs = (
            (560, 80, 130, 820), (560, 1720, 130, 980),
            (1240, 80, 130, 660), (1240, 1820, 130, 900),
            (2200, 80, 140, 780), (2200, 1780, 140, 940),
            (3120, 80, 130, 840), (3120, 1800, 130, 920),
            (3760, 120, 120, 760), (3760, 1900, 120, 780),
        )
        for spec in wall_specs:
            self._add(WarrensProp(*spec, "brick_wall", blocking=True), blocking=True)
        for x, y, length in (
            (280, 360, 460), (980, 940, 520), (2080, 380, 470),
            (2480, 2340, 560), (3080, 1010, 520), (3900, 520, 420),
        ):
            self.props.append(WarrensProp(x, y, length, 44, "pipe", blocking=False))
        bridge_specs = (
            (760, 1200, 190, 370), (1820, 1150, 200, 450),
            (2820, 1160, 200, 430), (3480, 1200, 200, 370),
        )
        for spec in bridge_specs:
            bridge = WarrensProp(*spec, "bridge", blocking=False)
            self.bridges.append(pygame.Rect(spec))
            self.props.append(bridge)
        for x, y in ((470, 520), (1060, 2020), (2040, 580), (2560, 2020),
                     (3060, 580), (3620, 1700)):
            self._add(WarrensProp(x, y, 115, 85, "crate", blocking=True), blocking=True)
        self.city_drain = WarrensProp(105, 430, 130, 110, "drain", blocking=False)
        self.low_fields_drain = WarrensProp(105, self.height - 520, 130, 110, "drain", blocking=False)
        self.props.extend((self.city_drain, self.low_fields_drain))
        self.throne = WarrensProp(4180, 1180, 210, 240, "throne", blocking=True)
        self._add(self.throne, blocking=True)

        state = warrens_state(self.manager)

        # Kerättävät solmut (aktivoituvat kun alue on turvattu)
        gathered = set(state.get("gathered_nodes", ()))
        for node_id, kind, x, y in GATHER_NODES:
            node = GatherNode(node_id, kind, x, y, node_id in gathered)
            self.gather_nodes.append(node)
            self.props.append(node)

        # Questitehtävät ovat ERI HAAROISSA kaukana toisistaan - viemäri
        # pakottaa pitkille matkoille (pelitesti 26b)
        # Vaihe 2: invaasion repeämä LUOTEISTUNNELISSA
        self.breach = BreachTunnel(1180, 300, state.get("breach_sealed"))
        self.props.append(self.breach)

        # Vaihe 3: tulvaventtiili LOUNAISHAARASSA (kaukana etelässä)
        self.valve = FloodValve(1240, 2360, state.get("valve_turned"))
        self.props.append(self.valve)

        # Vaihe 4: rottaleirin loretaulu POHJOISKESKUSTAN kammiossa
        self.lore_board = LoreBoard(2520, 320, state.get("lore_read"))
        self.props.append(self.lore_board)

        # Vaihe 5: lankkusilta murtuneen lattian yli KAAKKOISHAARASSA
        self.bridge_site = BuildSite("plank_bridge", "bridge", 3000, 2320,
                                     260, 120, state.get("bridge_built"))
        self.props.append(self.bridge_site)

        # Vaihe 6: sammakkosepän työpaja / portti-ram (itäinen työpaja)
        self.device_site = BuildSite("gate_ram", "device", 3720, 1120,
                                     180, 130, state.get("device_built"))
        self.props.append(self.device_site)

        self.set_boss_gate(not state.get("boss_defeated"))

    def set_boss_gate(self, active: bool):
        if active and self.boss_gate is None:
            self.boss_gate = WarrensProp(3800, 700, 66, 1400, "bar_gate", blocking=True)
            self._add(self.boss_gate, blocking=True)
        elif not active and self.boss_gate is not None:
            if self.boss_gate in self.props:
                self.props.remove(self.boss_gate)
            if self.boss_gate in self.obstacles:
                self.obstacles.remove(self.boss_gate)
            self.boss_gate = None

    def refresh_persistent(self, manager):
        state = warrens_state(manager)
        gathered = set(state.get("gathered_nodes", ()))
        for node in self.gather_nodes:
            node.gathered = node.node_id in gathered
            node._redraw()
        if self.breach:
            self.breach.sealed = bool(state.get("breach_sealed"))
            self.breach._redraw()
        if self.valve:
            self.valve.turned = bool(state.get("valve_turned"))
            self.valve._redraw()
        if self.lore_board:
            self.lore_board.read = bool(state.get("lore_read"))
            self.lore_board._redraw()
        if self.bridge_site:
            self.bridge_site.built = bool(state.get("bridge_built"))
            self.bridge_site._redraw()
        if self.device_site:
            self.device_site.built = bool(state.get("device_built"))
            self.device_site._redraw()
        # Suuri Abyssal Cistern -portti aukeaa vasta kun portti-ram on
        # rakennettu (device_built) tai boss jo kaadettu.
        self.set_boss_gate(not state.get("device_built")
                           and not state.get("boss_defeated"))

    def player_is_wading(self, point: Tuple[int, int]) -> bool:
        if any(bridge.collidepoint(point) for bridge in self.bridges):
            return False
        return any(channel.collidepoint(point) for channel in self.tainted_channels)

    def update(self, manager=None):
        self.flow_offset = (self.flow_offset + 1) % 44
        self.vfx.update(manager)
        for prop in self.props:
            if hasattr(prop, "update"):
                try:
                    prop.update(manager=manager)
                except TypeError:
                    prop.update()
        if random.random() < 0.12:
            self.fumes.append(
                {
                    "x": random.randint(650, self.width - 180),
                    "y": random.choice((1070, 1210, 1540, 1840)),
                    "life": random.randint(70, 160),
                    "size": random.randint(4, 10),
                }
            )
        for fume in self.fumes:
            fume["life"] -= 1
            fume["y"] -= 0.18
        self.fumes = [fume for fume in self.fumes if fume["life"] > 0]

    def draw_background(self, screen, offset=(0, 0)):
        screen.blit(self.floor_image, (-int(offset[0]), -int(offset[1])))

    def draw_foreground(self, screen, offset=(0, 0)):
        ox, oy = int(offset[0]), int(offset[1])
        for channel in self.tainted_channels:
            visible = channel.move(-ox, -oy)
            clipped = visible.clip(screen.get_rect())
            if clipped.w <= 0 or clipped.h <= 0:
                continue
            horizontal = channel.w > channel.h
            if horizontal:
                for x in range(channel.left - self.flow_offset, channel.right, 44):
                    sx = x - ox
                    sy = channel.centery - oy
                    pygame.draw.line(screen, (66, 101, 82), (sx, sy - 34), (sx + 20, sy - 29), 3)
                    pygame.draw.line(screen, (39, 72, 62), (sx + 8, sy + 37), (sx + 30, sy + 31), 2)
            else:
                for y in range(channel.top - self.flow_offset, channel.bottom, 44):
                    sx = channel.centerx - ox
                    sy = y - oy
                    pygame.draw.line(screen, (66, 101, 82), (sx - 33, sy), (sx - 27, sy + 20), 3)
                    pygame.draw.line(screen, (39, 72, 62), (sx + 34, sy + 8), (sx + 28, sy + 30), 2)
        for fume in self.fumes:
            x, y = int(fume["x"] - ox), int(fume["y"] - oy)
            if -20 < x < screen.get_width() + 20 and -20 < y < screen.get_height() + 20:
                pygame.draw.circle(screen, (137, 67, 151), (x, y), fume["size"], 2)
        self.vfx.draw_top(screen, offset)


class MuckfordWarrensMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = MuckfordWarrensArena(manager)
        self.monsters = pygame.sprite.Group()
        self.warrens_npcs: List[Villager] = []
        self.dynamic_props: List[object] = []
        self.boss: Optional[RatKing] = None
        self.feedback = ""
        self.feedback_timer = 0
        self.warning = ""
        self.warning_timer = 0
        self.dialogue_active = False
        self.dialogue_name = ""
        self.dialogue_pages: List[str] = []
        self.dialogue_index = 0
        self._dialogue_queue: List[tuple] = []   # ketjutetut dialogit
        self.dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.wade_tick = 0
        self.boss_wave_timer = 0

    def on_exit(self):
        super().on_exit()
        # Rat King + kutsutut rotat pois managerin ryhmistä, etteivät
        # vuoda muihin karttoihin (pelitesti 25)
        for grp in ("enemy_team", "all_units"):
            group = getattr(self.manager, grp, None)
            if group is None:
                continue
            for mo in list(self.monsters):
                if mo in group:
                    group.remove(mo)

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx
        self.player = self.manager.player_character
        entry = getattr(self.manager, "warrens_entry", None) or "muckford"
        self.manager.warrens_entry = None
        if entry == "low_fields":
            self.player.rect.center = (190, self.arena.height - 410)
            self.player.facing_right = True
        else:
            self.player.rect.center = (190, 570)
            self.player.facing_right = True
        self.player.is_dead = False
        self.player.current_hp = max(1, self.player.current_hp)
        # Retkikunta mukaan barracksista koottuna (pelitesti 24)
        try:
            self.enable_expedition()
        except Exception:
            pass
        state = warrens_state(self.manager)
        state["visits"] = int(state.get("visits", 0)) + 1
        sync_warrens_story(self.manager)
        self.arena.refresh_persistent(self.manager)
        self.monsters.empty()
        self._spawn_population()
        self._refresh_npcs()
        self._spawn_boss_if_needed()
        self._update_camera()
        try:
            advice = self.manager.get_tier0_area_advice("muckford_warrens")
            self.warning = advice.get("warning", "Recommended Lv 4-6")
            self.warning_timer = 420
        except Exception:
            self.warning = "OPEN RISK — recommended Lv 4-6"
            self.warning_timer = 420
        try:
            from systems.world_progression import mark_location_visited
            mark_location_visited(self.manager, "muckford_warrens", set_current=True)
        except Exception:
            pass
        try:
            self.manager.record_tier0_event("visit", "muckford_warrens")
            self.manager.record_tier0_event("risk_seen", "muckford_warrens")
        except Exception:
            pass
        _safe_sound("click")

    @staticmethod
    def _npc(name: str, race: str, x: int, y: int, role: str):
        npc = Villager(name, race, x, y, team_color=GREEN)
        npc.ai_controller = None
        npc.name = str(name)
        npc.warrens_role = str(role)
        npc.animation_state = "idle"
        return npc

    def _refresh_npcs(self):
        for prop in list(self.dynamic_props):
            if prop in self.arena.props:
                self.arena.props.remove(prop)
        self.dynamic_props = []
        self.warrens_npcs = []
        state = warrens_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        # Hamo vahtii sisäänkäyntiä koko kriisin ajan
        self.warrens_npcs.append(self._npc("Hamo", "Goblin", 290, 560, "hamo"))
        # Sammakko-seppä Brekka odottaa työpajallaan vaiheesta 6 (kunnes
        # rekrytoidaan tiimiin) - pelaaja kohtaa hänet portti-ramin luona
        if stage >= 6 and not state.get("smith_recruited"):
            self._add_frog_smith()
        self.dynamic_props = list(self.warrens_npcs)
        self.arena.props.extend(self.dynamic_props)

    def _add_frog_smith(self):
        """Lisää sammakkosepän (Brekka) työpajalle staattisena NPC:nä.
        Rekrytointi tapahtuu portti-rami rakennettaessa (vaihe 6)."""
        ds = self.arena.device_site.rect if self.arena.device_site else None
        x = (ds.centerx - 90) if ds else 3700
        y = (ds.top - 30) if ds else 1120
        smith = self._npc("Brekka the Frog Smith", "Frogfolk", x, y, "smith")
        self.warrens_npcs.append(smith)

    def _rat(self, cls, name, x, y):
        """Luo OIKEAN rottayksikön ja liittää sen warrens-ryhmään +
        managerin enemy_teamiin (Rat Kingin summon vaatii enemy_teamin)."""
        rat = cls(name, x, y, ENEMY_TEAM)
        rat.team_color = ENEMY_TEAM
        self.monsters.add(rat)
        return rat

    def _spawn_population(self):
        state = warrens_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        safe = bool(state.get("area_safe"))
        self._counters = {}
        # Perusrottia hajallaan tunneleissa (vähemmän kun alue turvattu)
        base = [
            (GiantRat, 760, 520), (GiantRat, 1100, 1500), (GiantRat, 1500, 900),
            (GiantRat, 2200, 1980), (GiantRat, 2700, 560), (GiantRat, 3060, 1960),
            (GiantRat, 1240, 460), (GiantRat, 1620, 1780), (GiantRat, 2060, 780),
            (GiantRat, 2500, 1560), (GiantRat, 2960, 700), (GiantRat, 3300, 1820),
            (RatRider, 1440, 2040), (RatRider, 2360, 460), (RatRider, 3020, 1520),
            (RatRider, 1900, 1260), (RatRider, 2820, 1760),
            (BruteRat, 1760, 940), (BruteRat, 2640, 1980), (BruteRat, 3100, 470),
        ]
        if safe:
            # Alue turvattu invaasion sulun jälkeen -> harvakseltaan rottia,
            # keräily rauhassa
            base = base[::3]
        for cls, x, y in base:
            self._spawn_rat(cls, x, y)
        # Vaihe 2: invaasioaalto repeämästä (jos ei vielä suljettu)
        if stage == 2 and not state.get("breach_sealed") and self.arena.breach:
            self._spawn_invasion_wave()
        # Vaihe 4: rottaleirin vartijat loretaulun ympärillä
        if stage == 4 and not state.get("lore_read") and self.arena.lore_board:
            self._spawn_camp()

    def _spawn_rat(self, cls, x, y):
        n = self._counters[cls] = self._counters.get(cls, 0) + 1
        label = {GiantRat: "Sewer Rat", RatRider: "Rat Rider",
                 BruteRat: "Brute Rat"}[cls]
        return self._rat(cls, f"{label} {n}", x, y)

    def _spawn_invasion_wave(self):
        bx, by = self.arena.breach.rect.center
        for i in range(6):
            self._spawn_rat(GiantRat, bx + (i - 3) * 60, by + 90 + (i % 2) * 40)
        for i in range(3):
            self._spawn_rat(RatRider, bx + (i - 1) * 110, by + 180)
        self._spawn_rat(BruteRat, bx, by + 250)

    def _spawn_camp(self):
        cx, cy = self.arena.lore_board.rect.center
        for i in range(5):
            self._spawn_rat(GiantRat, cx + (i - 2) * 90, cy - 120 - (i % 2) * 40)
        for i in range(2):
            self._spawn_rat(RatRider, cx + (i - 1) * 140, cy - 200)
        self._spawn_rat(BruteRat, cx - 40, cy - 300)

    def _spawn_boss_if_needed(self):
        state = warrens_state(self.manager)
        self.boss = None
        if not state.get("boss_unlocked") or state.get("boss_defeated"):
            return
        self.arena.set_boss_gate(False)
        # OIKEA Rat King -boss (units.rat_king): sylky, summon, rage,
        # superhyppy - sama kuin alun perin rakennettu (pelitesti 25).
        # Nimetty (pelitesti 26): Skrivvax, the Gnawing Crown.
        self.boss = RatKing(RAT_KING_NAME,
                            self.arena.royal_cistern.centerx - 60,
                            self.arena.royal_cistern.centery)
        self.boss.assign_manager(self.manager)
        self.boss.team_color = ENEMY_TEAM
        self.monsters.add(self.boss)
        self.manager.enemy_team.add(self.boss)
        # Eeppinen intro ensimmäisellä kohtaamisella: Vortex Abyssal -lore
        if not state.get("boss_intro_seen"):
            state["boss_intro_seen"] = True
            self._open_dialogue(
                RAT_KING_NAME,
                (
                    "SsSSo. You bridged my broken road, raised the frog's "
                    "iron ram, and cranked my last gate. Persistent meat.",
                    "I am no gutter vermin, Commander. I crawled up from "
                    "the Abyssal Vortex itself. I only need a little more "
                    "of its power, and Muckford is the FIRST bowl I empty.",
                    "The Master's demand is simple: these little kingdoms "
                    "PAY. You do not get to ask why. You only get to "
                    "DROWN. COME!",
                ),
            )
            try:
                self.manager.trigger_screen_shake(16)
            except Exception:
                pass
        self._flash(f"{RAT_KING_NAME} rises from the Abyssal Cistern.", 320)

    def _near(self, rect: pygame.Rect, inflate=76) -> bool:
        return self.player.rect.colliderect(rect.inflate(inflate, inflate))

    def _flash(self, message: str, duration=220):
        self.feedback = str(message)
        self.feedback_timer = int(duration)

    @staticmethod
    def _wrap(text: str, font, width: int) -> List[str]:
        lines = []
        current = ""
        for word in str(text).split():
            trial = word if not current else f"{current} {word}"
            if font.size(trial)[0] <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _open_dialogue(self, name: str, pages: Sequence[str]):
        """Avaa dialogin. Jos dialogi on jo auki, ketjutetaan jonoon (näin
        esim. loretaulu -> Griznakin reaktio -> bossin intro pelaavat
        peräkkäin siististi, pelitesti 26b)."""
        entry = (str(name), [str(p) for p in pages])
        if self.dialogue_active:
            self._dialogue_queue.append(entry)
        else:
            self._show_dialogue(*entry)

    def _show_dialogue(self, name, pages):
        self.dialogue_active = True
        self.dialogue_name = name
        self.dialogue_pages = list(pages)
        self.dialogue_index = 0
        _safe_sound("click")

    def _advance_dialogue_queue(self):
        if self._dialogue_queue:
            self._show_dialogue(*self._dialogue_queue.pop(0))
        else:
            self.dialogue_active = False

    # ------------------------------------------------------------------
    # Griznak kommentoi joka etenemisen ja avaa seuraavan tehtävän
    # (pelitesti 26b): "aina kun questi etenee, Griznak käy dialogia"
    # ------------------------------------------------------------------
    _GRIZNAK_ADVANCE = {
        2: ("Heh - you thinned them. But scouts say a breach tore open in "
            "the NORTH-WEST tunnels and rats are POURING through. Get up "
            "there, break the wave, and seal it shut."),
        3: ("Breach sealed - the near tunnels have gone quiet. Safe to "
            "pick herbs and fungus down here now, if you've the time. "
            "Next: the far SOUTH-WEST passage is flooded. Find the valve "
            "and drain it."),
        4: ("Water's dropping. Their main camp is way up the NORTH-EAST "
            "arm. Storm it and read whatever they nailed up - I want to "
            "know who is giving rats ORDERS."),
        5: ("...the Abyssal Vortex. A 'Master'. Bad, hero, that's bad. "
            "And that tremor? The SOUTH-EAST floor caved in. Lay a plank "
            "bridge across it and keep pushing east."),
        6: ("Across the bridge is the old flooded workshop. Brekka the "
            "frog smith is walled up in there - help him raise his "
            "gate-ram and the deep cistern finally opens."),
        7: ("The great gate's open. Skrivvax - the crowned rat himself - "
            "waits in the Abyssal Cistern at the far EAST. This is the "
            "job I hired you for. Go end it."),
        8: ("It's DEAD? Hah! You actually did it, hero. Muckford's yours "
            "to walk now. Come find my wagon topside for your due."),
    }

    def _griznak_says(self, to_stage: int):
        lines = self._GRIZNAK_ADVANCE.get(int(to_stage))
        if lines:
            self._open_dialogue("Griznak the Shifty", (lines,))

    # ------------------------------------------------------------------
    # Hamo + sammakko-seppä + questin edistys
    # ------------------------------------------------------------------
    def _hamo_dialogue(self):
        state = warrens_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        if stage == 0:
            state["quest_stage"] = 1
            try:
                self.manager.record_tier0_event("flag", "muckford_warrens_started")
            except Exception:
                pass
            self._open_dialogue("Hamo", (
                "You came down after all. Good. The rats have gone from "
                "nuisance to ARMY - and something down there is driving them.",
                f"Start simple: cull {CULL_TARGET} of the sewer rats "
                "gnawing our foundations. Coin and a blade for your trouble.",
                "The hatch opens at any level, Commander, but these tunnels "
                "are Lv 4-6 work. Bring friends from the barracks."))
            return
        pages = {
            1: (f"Keep culling. Sewer rats put down: "
                f"{state.get('rats_culled', 0)}/{CULL_TARGET}.",),
            2: ("A breach tore open north of here and rats are POURING out. "
                "Break the wave, then seal the breach tunnel.",),
            3: ("With the breach sealed the near tunnels are safe - gather "
                "what herbs and fungus you can. Then find the flood valve "
                "east and drain the sunken passage.",),
            4: ("Past the drained passage is their camp. Storm it and read "
                "whatever the vermin left nailed up. I want to know who is "
                "GIVING these rats orders.",),
            5: ("That tremor... half the old passage caved in. Bridge the "
                "broken floor with planks to press on.",),
            6: ("The flooded workshop is just ahead. Old Brekka the frog "
                "smith is holed up there - help raise his gate-ram and the "
                "deep cistern opens.",),
            7: (f"The great gate is open. {RAT_KING_NAME} waits in the "
                "Abyssal Cistern. End it.",),
            8: ("No more raid bells, no more glowing eyes at the granary. "
                "Muckford eats because of you, Commander.",),
        }.get(stage, ("The Warrens are quiet now. Rest easy.",))
        if stage == 8:
            self._report()
            return
        self._open_dialogue("Hamo", pages)

    def _report(self):
        state = warrens_state(self.manager)
        if not state.get("report_reward_claimed"):
            self.manager.gold += 180
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 12
            self.manager.city_storage["Recovered Grain"] = int(self.manager.city_storage.get("Recovered Grain", 0)) + 8
            state["report_reward_claimed"] = True
        state["completed"] = True
        state["city_raids_ended"] = True
        try:
            self.manager.record_tier0_event("quest", "muckford_warrens_cleared")
            self.manager.record_tier0_event("flag", "muckford_rat_raids_ended")
        except Exception:
            pass
        self._open_dialogue("Hamo", (
            f"{RAT_KING_NAME} is dead and whatever 'Master' he served has "
            "lost its crown down here. The Warrens still have teeth, but "
            "no orders.",
            "Muckford is yours to walk safely now - the deep tunnels make "
            "a fine gathering ground. +180 SP, +12 reputation."))
        self._flash("Muckford Warrens secured. Rat raids ended.", 420)

    def _talk_smith(self):
        """Sammakko-seppä Brekka: lore + vihje portti-ramin rakennuksesta."""
        state = warrens_state(self.manager)
        state["smith_met"] = True
        self._open_dialogue("Brekka the Frog Smith", (
            "Hrrk. A living face! I've been walled in here since the water "
            "rose. That crowned rat wants my forge - not happening.",
            "Bring me the makings and I'll raise my gate-ram against the "
            f"deep cistern gate: {DEVICE_RECIPE_TEXT}.",
            "Break that crown for good and I'll march with you, Commander. "
            "A team could use a smith who swings a hammer both ways."))

    def _recruit_smith(self):
        """Rekrytoi Brekka pelaajan tiimiin (portti-ram rakennettu)."""
        state = warrens_state(self.manager)
        if state.get("smith_recruited"):
            return
        state["smith_recruited"] = True
        try:
            from units.frog_smith import FrogSmith
            from settings import PLAYER_TEAM
            smith = FrogSmith("Brekka", self.player.rect.centerx - 60,
                              self.player.rect.centery, PLAYER_TEAM)
            self.manager.my_team.add(smith)
            self.manager.has_smith = True
            _safe_sound("recruit")
            self._flash("Brekka the Frog Smith joins your team! "
                        "(gear repairs are cheaper now)", 360)
        except Exception:
            pass
        self._refresh_npcs()

    def _try_npc(self) -> bool:
        for npc in self.warrens_npcs:
            if not self._near(npc.rect, 74):
                continue
            role = getattr(npc, "warrens_role", "")
            if role == "hamo":
                self._hamo_dialogue()
            elif role == "smith":
                self._talk_smith()
            else:
                self._open_dialogue(npc.name, ("Watch the water, friend.",))
            return True
        return False

    # ------------------------------------------------------------------
    # Kerättävät solmut (yrtit/sienet) - aukeavat kun alue on turvattu
    # ------------------------------------------------------------------
    def _try_gather(self) -> bool:
        state = warrens_state(self.manager)
        if not state.get("area_safe"):
            return False
        for node in self.arena.gather_nodes:
            if node.gathered or not self._near(node.rect, 70):
                continue
            gathered = state.setdefault("gathered_nodes", [])
            if node.node_id not in gathered:
                gathered.append(node.node_id)
            node.gathered = True
            node._redraw()
            res = node.resource_name
            self.manager.inventory[res] = int(
                self.manager.inventory.get(res, 0)) + random.randint(1, 2)
            self._flash(f"Gathered {res}.")
            _safe_sound("mining_break")
            try:
                self.manager.grant_hero_xp(2, node.rect.centerx, node.rect.top)
            except Exception:
                pass
            return True
        return False

    # ------------------------------------------------------------------
    # Questin interaktiivit: breach, valve, lore, bridge, device
    # ------------------------------------------------------------------
    def _try_breach(self) -> bool:
        state = warrens_state(self.manager)
        breach = self.arena.breach
        if breach is None or breach.sealed or not self._near(breach.rect, 90):
            return False
        if int(state.get("quest_stage", 0)) != 2:
            return False
        # Vaatii invaasioaallon kaatamisen ensin
        if int(state.get("invasion_kills", 0)) < INVASION_TARGET:
            left = INVASION_TARGET - int(state.get("invasion_kills", 0))
            self._flash(f"The breach spews too many rats to seal - clear "
                        f"the wave first ({left} left).", 220)
            _safe_sound("error")
            return True
        breach.sealed = True
        breach._redraw()
        state["breach_sealed"] = True
        _safe_sound("mining_break")
        if sync_warrens_story(self.manager):
            self.arena.refresh_persistent(self.manager)
            self._flash("Breach sealed! The near tunnels fall quiet.", 300)
            self._griznak_says(3)
        return True

    def _try_valve(self) -> bool:
        state = warrens_state(self.manager)
        valve = self.arena.valve
        if valve is None or valve.turned or not self._near(valve.rect, 84):
            return False
        if int(state.get("quest_stage", 0)) != 3:
            self._flash("The valve won't budge yet.", 160)
            return True
        valve.turned = True
        valve._redraw()
        state["valve_turned"] = True
        _safe_sound("mining_break")
        try:
            self.manager.trigger_screen_shake(8)
        except Exception:
            pass
        if sync_warrens_story(self.manager):
            self.arena.refresh_persistent(self.manager)
            self._flash("The valve groans and the flooded passage drains.", 300)
            self._griznak_says(4)
        return True

    def _try_lore(self) -> bool:
        state = warrens_state(self.manager)
        board = self.arena.lore_board
        if board is None or board.read or not self._near(board.rect, 84):
            return False
        if int(state.get("quest_stage", 0)) != 4:
            return True
        if int(state.get("camp_kills", 0)) < CAMP_TARGET:
            left = CAMP_TARGET - int(state.get("camp_kills", 0))
            self._flash(f"The camp still crawls with guards - clear them "
                        f"first ({left} left).", 220)
            _safe_sound("error")
            return True
        board.read = True
        board._redraw()
        state["lore_read"] = True
        # Lore: Rat Kingin suunnitelma, Vortex Abyssal, "Mestari vaatii
        # että valtakunnat maksavat" - mutta ei kerrota miksi.
        self._open_dialogue("A Rat-Scrawled Proclamation", (
            f"'By claw of {RAT_KING_NAME}, denizen of the Abyssal Vortex: "
            "gnaw deep, drink the seepage, GROW.'",
            "'When the crown holds power enough, Muckford is the first "
            "kingdom to kneel. Then the ford. Then the bridge-cities. Then "
            "all the little kingdoms of soft meat.'",
            "'The Master demands they PAY. We do not ask the Master why. "
            "We only open the way.'"))
        if sync_warrens_story(self.manager):
            self.arena.refresh_persistent(self.manager)
            # Tärinä + jokin murtuu -> lankkusilta-vaihe
            try:
                self.manager.trigger_screen_shake(20)
            except Exception:
                pass
            self._flash("A deep tremor rolls through the stone - something "
                        "far below just BROKE.", 360)
            self._griznak_says(5)   # ketjuun proklamaation jälkeen
        return True

    def _try_bridge(self) -> bool:
        state = warrens_state(self.manager)
        site = self.arena.bridge_site
        if site is None or site.built or not self._near(site.rect, 96):
            return False
        if int(state.get("quest_stage", 0)) != 5:
            return False
        need = BRIDGE_WOOD
        have = int(self.manager.inventory.get(BRIDGE_MATERIAL, 0))
        if have < need:
            self._flash(f"Broken floor. Need {need} {BRIDGE_MATERIAL} to "
                        f"lay a plank bridge (have {have}).", 260)
            _safe_sound("error")
            return True
        self.manager.inventory[BRIDGE_MATERIAL] = have - need
        if self.manager.inventory[BRIDGE_MATERIAL] <= 0:
            del self.manager.inventory[BRIDGE_MATERIAL]
        site.built = True
        site._redraw()
        state["bridge_built"] = True
        _safe_sound("mining_break")
        if sync_warrens_story(self.manager):
            self.arena.refresh_persistent(self.manager)
            self._refresh_npcs()   # Brekka ilmestyy työpajalle
            self._flash("Plank bridge laid. The flooded workshop lies "
                        "across - and someone is hammering in there.", 340)
            self._griznak_says(6)
        return True

    def _try_device(self) -> bool:
        state = warrens_state(self.manager)
        site = self.arena.device_site
        if site is None or site.built or not self._near(site.rect, 96):
            return False
        if int(state.get("quest_stage", 0)) != 6:
            return False
        if not state.get("smith_met"):
            self._flash("Talk to Brekka the Frog Smith first - it's his "
                        "gate-ram.", 220)
            return True
        # Materiaalitarkistus
        missing = [f"{n} x{c}" for n, c in DEVICE_RECIPE.items()
                   if int(self.manager.inventory.get(n, 0)) < c]
        if missing:
            self._flash("Gate-ram needs: " + ", ".join(missing), 300)
            _safe_sound("error")
            return True
        for n, c in DEVICE_RECIPE.items():
            self.manager.inventory[n] -= c
            if self.manager.inventory[n] <= 0:
                del self.manager.inventory[n]
        site.built = True
        site._redraw()
        state["device_built"] = True
        _safe_sound("mining_break")
        try:
            self.manager.trigger_screen_shake(14)
        except Exception:
            pass
        # Portti-ram avaa ison Abyssal Cistern -portin + rekrytoi Brekka
        if sync_warrens_story(self.manager):
            self.arena.set_boss_gate(False)
            self._flash("The gate-ram slams home - the great bar-gate "
                        "buckles open. The Abyssal Cistern gapes beyond.", 380)
            self._recruit_smith()
            self._griznak_says(7)          # Griznak ensin,
            self._spawn_boss_if_needed()   # sitten bossin intro ketjuun
        return True

    def handle_event(self, event):
        if self.dialogue_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._dialogue_queue.clear()
                    self.dialogue_active = False
                    return
                if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.dialogue_index += 1
                    if self.dialogue_index >= len(self.dialogue_pages):
                        self._advance_dialogue_queue()
                    return
            return
        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            if self._try_npc():
                return
            if self._try_gather():
                return
            if (self._try_breach() or self._try_valve() or self._try_lore()
                    or self._try_bridge() or self._try_device()):
                return

    def _transfer_loot(self):
        loot = self.manager.round_rewards.get("loot")
        if not loot:
            return
        for name, amount in list(loot.items()):
            self.manager.inventory[name] = int(self.manager.inventory.get(name, 0)) + int(amount)
        self.manager.round_rewards["loot"] = {}

    def _apply_sewer_hazard(self):
        if not self.arena.player_is_wading(self.player.rect.center):
            self.wade_tick = 0
            return
        self.wade_tick += 1
        if self.wade_tick % 45 != 0:
            return
        state = warrens_state(self.manager)
        # Ennen invaasion sulkua vesi on myrkyllisempää; turvatulla
        # alueella vain hidastaa (pelitesti 26)
        safe = bool(state.get("area_safe"))
        exposure_gain = 1 if safe else 4
        state["waste_exposure"] = min(100, int(state.get("waste_exposure", 0)) + exposure_gain)
        try:
            self.player.apply_status("Slow", 55, 0)
        except Exception:
            pass
        if int(state.get("waste_exposure", 0)) >= 60 and not safe:
            try:
                self.player.take_damage(4, "Poison", manager=self.manager)
                self.player.apply_status("Poison", 90, 2)
            except Exception:
                self.player.current_hp = max(1, self.player.current_hp - 4)
            self._flash("Vortex waste burns through the sewer water.", 90)
        elif self.wade_tick % 135 == 0:
            self._flash("Sewer current slows movement. Bridges avoid the waste.", 90)

    def _process_boss(self):
        if self.boss is None:
            return
        # Rat King (units.rat_king) kutsuu rottia suoraan enemy_teamiin +
        # all_unitsiin - imetään ne warrens-ryhmään jotta taistelu-AI ja
        # piirto toimivat yhtenäisesti (pelitesti 25)
        for e in list(self.manager.enemy_team):
            if e is self.boss:
                continue
            if e not in self.monsters:
                self.monsters.add(e)
            self.manager.enemy_team.remove(e)
        if not self.boss.is_dead:
            return
        state = warrens_state(self.manager)
        if state.get("boss_defeated"):
            return
        state["boss_defeated"] = True
        state["city_raids_ended"] = True
        state["boss_unlocked"] = False
        sync_warrens_story(self.manager)   # -> vaihe 8 (raportti)
        if not state.get("boss_reward_claimed"):
            self.manager.gold += 100
            self.manager.reputation = int(getattr(self.manager, "reputation", 0)) + 6
            self.manager.inventory["Gnawed Crown"] = int(self.manager.inventory.get("Gnawed Crown", 0)) + 1
            self.manager.inventory["Vortex Residue"] = int(self.manager.inventory.get("Vortex Residue", 0)) + 3
            state["boss_reward_claimed"] = True
        try:
            self.manager.record_tier0_event("boss", "rat_king")
            self.manager.record_tier0_event("flag", "muckford_rat_raids_ended")
        except Exception:
            pass
        try:
            self.manager.record_deed("rat_king", "slew the Rat King beneath Muckford and ended the sewer raids")
        except Exception:
            pass
        try:
            from quest_system import quest_manager
            if quest_manager:
                quest = quest_manager.quests.get("hunt_01")
                if quest:
                    quest.completed = True
                    quest.status = "completed"
        except Exception:
            pass
        self.manager.next_raid_day = 10 ** 9
        self.arena.set_boss_gate(False)
        self._flash(f"{RAT_KING_NAME} slain! +100 SP, +6 reputation.", 420)
        self._griznak_says(8)
        self._refresh_npcs()

    def _track_kills(self):
        """Laskee kaatuneet rotat vaihekohtaisiin laskureihin (pelitesti
        26): vaihe 1 cull, vaihe 2 invaasio, vaihe 4 leiri. Antaa cull-
        palkkion (raha + XP + heikko ase) kun tavoite täyttyy."""
        if not hasattr(self, "_counted_dead"):
            self._counted_dead = set()
        state = warrens_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        for mo in self.monsters:
            if mo is self.boss or not getattr(mo, "is_dead", False):
                continue
            if id(mo) in self._counted_dead:
                continue
            self._counted_dead.add(id(mo))
            if stage == 1:
                state["rats_culled"] = int(state.get("rats_culled", 0)) + 1
            elif stage == 2:
                state["invasion_kills"] = int(state.get("invasion_kills", 0)) + 1
            elif stage == 4:
                state["camp_kills"] = int(state.get("camp_kills", 0)) + 1
        # Vaihe 1: cull-palkkio + eteneminen
        if stage == 1 and int(state.get("rats_culled", 0)) >= CULL_TARGET \
                and not state.get("cull_reward_claimed"):
            state["cull_reward_claimed"] = True
            self.manager.gold += 40
            try:
                self.manager.grant_hero_xp(30, self.player.rect.centerx,
                                           self.player.rect.top)
            except Exception:
                pass
            self._grant_weak_weapon()
            if sync_warrens_story(self.manager):
                self._flash("The rats are thinned. +40 SP and a spare blade.",
                            300)
                self._griznak_says(2)
                if self.arena.breach and not self.arena.breach.sealed:
                    self._spawn_invasion_wave()   # invaasioaalto käynnistyy

    def _grant_weak_weapon(self):
        """Antaa heikon aseen cull-palkkiona (repun equipment_bagiin)."""
        try:
            item = self.manager._create_loot_item("Scrap Blade")
            if item is not None:
                self.manager.equipment_bag.append(item)
        except Exception:
            pass

    def update(self):
        if self.dialogue_active or self.manager.paused:
            if self.feedback_timer > 0:
                self.feedback_timer -= 1
            return
        living = [monster for monster in self.monsters if not monster.is_dead]
        all_units = [self.player] + self.expedition_units() + living
        self._update_gameplay(all_units)
        self._transfer_loot()
        self._track_kills()
        self._apply_sewer_hazard()
        self._process_boss()

        if self.player.is_dead:
            self.player.is_dead = False
            self.player.current_hp = max(1, int(self.player.max_hp * 0.3))
            self.manager.city_spawn_point = "warrens_hatch"
            self.next_state = "muckford_city"
            return

        if self.player.rect.colliderect(self.arena.city_exit):
            self.manager.match_in_progress = False
            self.manager.city_spawn_point = "warrens_hatch"
            self.next_state = "muckford_city"
            return
        if self.player.rect.colliderect(self.arena.low_fields_exit):
            self.manager.match_in_progress = False
            self.manager.pending_local_area = "low_fields"
            self.manager.pending_world_location = "low_fields"
            self.manager.low_fields_entry = "warrens"
            self.next_state = "regional_staging"
            return

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        if self.warning_timer > 0:
            self.warning_timer -= 1

    def _nearest_prompt(self):
        for npc in self.warrens_npcs:
            if self._near(npc.rect, 74):
                return npc.rect, f"Talk to {npc.name}"
        state = warrens_state(self.manager)
        stage = int(state.get("quest_stage", 0))
        # Kerättävät solmut (alue turvattu)
        if state.get("area_safe"):
            for node in self.arena.gather_nodes:
                if not node.gathered and self._near(node.rect, 70):
                    return node.rect, f"Gather {node.resource_name}"
        a = self.arena
        if stage == 2 and a.breach and not a.breach.sealed and \
                self._near(a.breach.rect, 90):
            return a.breach.rect, "Seal the breach tunnel"
        if stage == 3 and a.valve and not a.valve.turned and \
                self._near(a.valve.rect, 84):
            return a.valve.rect, "Turn the flood valve"
        if stage == 4 and a.lore_board and not a.lore_board.read and \
                self._near(a.lore_board.rect, 84):
            return a.lore_board.rect, "Read the rats' proclamation"
        if stage == 5 and a.bridge_site and not a.bridge_site.built and \
                self._near(a.bridge_site.rect, 96):
            return a.bridge_site.rect, "Build a plank bridge"
        if stage == 6 and a.device_site and not a.device_site.built and \
                self._near(a.device_site.rect, 96):
            return a.device_site.rect, "Raise the Frog Smith's gate-ram"
        return None

    def _draw_darkness(self, screen):
        self.dark_overlay.fill((5, 4, 8, 218))
        lights = [((self.player.rect.centerx, self.player.rect.centery), 335)]
        for x, y in ((350, 600), (960, 620), (2000, 600), (3000, 620),
                     (3760, 900), (4180, 1300)):
            lights.append(((x, y), 150))
        a = self.arena
        if a.breach and not a.breach.sealed:
            lights.append((a.breach.rect.center, 110))
        if self.boss is not None and not self.boss.is_dead:
            rage = 25 if getattr(self.boss, "rage_triggered", False) else 0
            lights.append((self.boss.rect.center, 205 + rage))
        for (world_x, world_y), radius in lights:
            x = int(world_x - self.camera_x)
            y = int(world_y - self.camera_y)
            flicker = random.randint(-5, 5)
            for r, alpha in ((radius + flicker, 155), (int(radius * 0.68), 82), (int(radius * 0.38), 28), (54, 0)):
                pygame.draw.circle(self.dark_overlay, (5, 4, 8, alpha), (x, y), max(4, r))
        screen.blit(self.dark_overlay, (0, 0))

    def _draw_dialogue(self, screen):
        # Yhtenäinen Muckford-tyylinen dialogi (puhuja esiin + nimikilpi)
        from systems.area_dialogue import draw_area_dialogue
        if draw_area_dialogue(self, screen):
            return
        if not self.dialogue_active or not self.dialogue_pages:
            return
        panel = pygame.Rect(165, SCREEN_HEIGHT - 260, SCREEN_WIDTH - 330, 205)
        overlay = pygame.Surface(panel.size, pygame.SRCALPHA)
        overlay.fill((20, 17, 22, 244))
        screen.blit(overlay, panel.topleft)
        pygame.draw.rect(screen, (153, 91, 169), panel, 3, border_radius=9)
        draw_text(self.dialogue_name, font_main, GOLD_COLOR, screen, panel.x + 24, panel.y + 18)
        y = panel.y + 60
        page = self.dialogue_pages[self.dialogue_index]
        for line in self._wrap(page, font_main, panel.w - 48)[:4]:
            draw_text(line, font_main, WHITE, screen, panel.x + 24, y)
            y += 29
        draw_text("[E / Enter] continue    [Esc] close", font_small, GRAY, screen, panel.right - 355, panel.bottom - 27)

    def draw(self, screen):
        living = [monster for monster in self.monsters if not monster.is_dead]
        all_units = [self.player] + self.expedition_units() + living
        self._draw_gameplay(screen, all_units)
        self._draw_darkness(screen)
        # HUD piirretään pimeyden PÄÄLLE - muuten HP/mana-pallot ja
        # palkit himmenevät lukukelvottomiksi (pelaajapalaute)
        if getattr(self, "player", None):
            self.player.draw_hud(screen)
        prompt = None if self.dialogue_active else self._nearest_prompt()
        if prompt:
            rect, label = prompt
            try:
                self.manager._draw_floating_prompt(
                    screen,
                    rect.centerx,
                    rect.top - 16,
                    "E",
                    (self.camera_x, self.camera_y),
                    label,
                )
            except Exception:
                pass
        state = warrens_state(self.manager)
        draw_text("MUCKFORD WARRENS — OPEN RISK Lv 4-6", font_small, WHITE, screen, 34, 32)
        draw_text(f"CRISIS: {warrens_objective(self.manager)}", font_small, (219, 184, 121), screen, 34, 58)
        stage = int(state.get("quest_stage", 0))
        prog = f"Stage {min(stage, 8)}/8"
        if stage == 1:
            prog += f"   Rats culled: {state.get('rats_culled', 0)}/{CULL_TARGET}"
        elif stage == 2:
            prog += (f"   Invasion cleared: "
                     f"{min(state.get('invasion_kills', 0), INVASION_TARGET)}"
                     f"/{INVASION_TARGET}")
        elif stage == 4:
            prog += (f"   Camp guards: "
                     f"{min(state.get('camp_kills', 0), CAMP_TARGET)}"
                     f"/{CAMP_TARGET}")
        draw_text(f"Threats: {len(living)}   {prog}", font_small, GRAY,
                  screen, 34, 84)
        draw_text(
            "Upper west drain: Muckford   Lower west drain: Low Fields   Sewer water slows and carries Vortex waste.",
            font_small,
            GRAY,
            screen,
            34,
            108,
        )
        if self.warning_timer > 0:
            surface = font_main.render(self.warning, True, (237, 153, 92))
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 136))
        if self.feedback_timer > 0:
            surface = font_main.render(self.feedback, True, GOLD_COLOR)
            screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 170))
        self._draw_dialogue(screen)
