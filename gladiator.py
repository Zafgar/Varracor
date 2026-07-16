import pygame
import math
import random

# --- SETTINGS & ASSETS ---
from settings import *
from races import RACES
from sound_manager import sound_system

# --- PROGRESSION ---
from progression.xp_table import MAX_LEVEL, level_from_xp

# Skill effects
from skills.skills_data import SKILL_TREE
try:
    from skills.school_trees_data import SCHOOL_TREE as _SCHOOL_NODES
except Exception:
    _SCHOOL_NODES = {}

# --- MODULES ---
from renderer import GladiatorRenderer
from items.item_registry import create_fists
from ui_kit import format_money

# --- AI ---
try:
    from ai.human_ai import HumanAI
except ImportError:
    HumanAI = None


# Esteiden (rect, type) -parien välimuisti (ks. Gladiator._nearby_obstacles)
_OBSTACLE_PAIRS_CACHE = {}


class Gladiator(pygame.sprite.Sprite):
    """
    Gladiator = unit base class.

    Features:
      - Spell slots (1..3) unlock via skill tree.
      - Weapon/Armor require Proficiency (Hard Lock).
      - Items can have 'on_update' hooks for Auras/AoE.
      - Passive bonuses (STR/DEX/INT) work on ALL items.
    """

    def __init__(self, name, race_name, x, y, team_color):
        super().__init__()
        self.name = name
        self.race_name = race_name
        self.team_color = team_color

        # --- ATTRIBUTES ---
        self.max_hp = 100
        self.current_hp = 100
        self.max_mana = 0
        self.current_mana = 0
        self.strength = 5
        self.dexterity = 5
        self.intelligence = 5
        self.speed = 1.0
        self.walk_speed = 1.0
        self.defense = 0

        self.base_mana_regen = 0.02
        self.mana_regen = self.base_mana_regen

        # Passiivinen HP-regen (pelitesti 22): perusnopeuden päälle
        # laskettava lisä (HP/frame); delay estää regenin osuman jälkeen
        self.hp_regen = 0.0
        self.hp_regen_delay = 0
        self._hp_regen_pool = 0.0

        # Global cooldown multiplier (lower = faster)
        self.cooldown_multiplier = 1.0

        # --- SUB-PIXEL MOVE (speed < 1.0 still moves) ---
        self._move_rem_x = 0.0
        self._move_rem_y = 0.0

        # --- MORALE (0-100, neutraali 50) ---
        # Nousee yhteisestä ajasta barracksissa ja voitoista, laskee
        # tappioista. Vaikuttaa vahinkoon: 0.9x (0) ... 1.1x (100).
        self.morale = 50
        self.last_social_day = -1  # world_clock.day jolloin viimeksi juteltu

        # --- STAMINA SYSTEM ---
        self.max_stamina = 100
        self.current_stamina = 100
        # Arcane strain: loitsimisen fyysinen/henkinen kuormitus.
        self.max_strain = 100
        self.current_strain = 0.0
        self.strain_regen = 0.15
        self.stamina_regen = 0.25 # Hieman nopeampi palautuminen

        # Combat states
        self.is_blocking = False
        self.is_sprinting = False
        self.is_dashing = False
        self.is_channeling = False # New state for spells like Sun Ray
        self.is_charging = False # UUSI: Estää staminan palautumisen ladatessa

        # Dash vectors
        self.dash_timer = 0
        self.max_dashes = 1 # Oletus: 1 syöksy
        self.current_dashes = 1
        self.dash_recharge_timer = 0
        # GAME FEEL: 3 s -> 2 s per lataus (dodge käytettävissä useammin)
        self.dash_recharge_time = 120
        self.dash_vector = (0.0, 0.0)
        # GAME FEEL: nopea pyrähdys (5.0 x 10 framea) hitaan liu'un
        # (3.5 x 15) sijaan - sama matka, puolet ajasta, i-framet tallella
        self.dash_speed_mult = 5.0
        self.dash_damage = 0 # UUSI: Vahinko törmäyksessä
        self.dash_hit_list = [] # Lista osutuista yksiköistä (ettei osu samaan montaa kertaa)
        self.jump_height = 0 # Visuaalinen hyppykorkeus (pikseleinä)

        # Attack stats
        self.attack_range = 35
        self.weapon_type = "melee"
        self.weapon_effect = "damage"

        # --- SKILL TREE (derived each recalculation) ---
        # New for weapon collision
        self.attack_vector = (0.0, 0.0)

        self.weapon_masteries = set()   # e.g. {"sword","dagger","bow","shield","book",...}
        self.armor_masteries = set()    # e.g. {"light","medium","heavy","cloth"}
        self.can_dual_wield = False
        self.block_stamina_mult = 1.0
        self.block_timer = 0 # GAME FEEL: frameja blokin alusta (parry-ikkuna)
        self.parry_cooldown = 0 # onnistuneen parryn jälkeinen lukitus
        self.riposte_timer = 0  # perfect parry avaa vastaiskuikkunan
        self.shield_tier = 1    # 1 = perus, 2 = Tower Discipline -kilvet
        self.shield_bash_cd = 0 # kilpi-iskun cooldown
        self.heavy_armor_penalty_mult = 1.0
        self.double_shot_chance = 0.0
        self.temp_speed_mult = 1.0 # UUSI: Väliaikainen nopeuskerroin (esim. lataus)

        # Spell unlocks (NOT tied to level)
        self.spell_slots_unlocked = set()  # {1,2,3}
        self.max_spell_tier = 0            # 0 => cannot equip/cast spells

        # Combat runtime
        self.is_dead = False
        self.facing_right = True # Alustettava: AI/liike päivittää tätä myöhemmin
        self.attack_cooldown = 0
        self.spell_cooldowns = {"spell1": 0, "spell2": 0, "spell3": 0}
        self.attack_speed = 60  # frames between attacks
        self.cost = 0
        self.training_count = 0

        self.stats = {"damage": 0, "healing": 0, "kills": 0, "assists": 0}
        self.attackers = set()
        self.status_effects = []
        # Latautuva loitsu (spells/casting.py): cast time + interrupt + counter
        self.active_cast = None
        self.traits = []
        # Synnynnäiset talentit (systems/talents.py): efektit joita
        # calculate_final_stats kuluttaa + insight-gated kuvaukset
        self.talent_effects = {}
        self.talent_details = []

        # --- IDENTITY (luonne + tausta) ---
        # Vain rekrytoitavilla roduilla; bosseille/eläimille jää None.
        self.personality = None
        self.origin = None
        try:
            from progression.personality import assign_personality, RACE_WEIGHTS
            if race_name in RACE_WEIGHTS:
                self.personality, self.origin = assign_personality(race_name)
        except Exception:
            pass

        # --- RACIAL ABILITIES ---
        self.is_invisible = False      # Goblin Shadowstep
        self.invis_timer = 0
        self.revealed = False          # See Invisibility paljastaa
        self.reveal_timer = 0
        self.stoneform_timer = 0       # Dwarf Stoneform (-50% vahinko)
        self.speed_buff_timer = 0      # Elf Wind Dance (+40% nopeus)
        self.frenzy_timer = 0          # Werewolf Bloodmoon Frenzy
        self.shell_timer = 0           # Tortle Shell Guard
        self.racial_cooldown = 0

        # --- SKILL FLAGS ---
        self.has_executioner = False
        self.has_second_wind = False
        self.has_steady_draw = False # Estää jousen jännityksen staggeroinnin
        self.second_wind_triggered = False

        # --- PROGRESSION ---
        self.max_level = MAX_LEVEL
        self.level = 1
        self.xp = 0
        self.skill_points = 0
        self.unlocked_skills = set()

        self.just_leveled_up = False
        self._level_up_timer = 0
        
        # --- ANIMATION STATE ---
        self.animation_state = "idle"
        self.animation_timer = 0
        self.stun_timer = 0 # UUSI: Osuman aiheuttama lamaannus
        self.stun_immunity = 0 # Estää stunlockin (ei voi stunnata heti uudestaan)

        self._death_timer = 0
        # Equip error message for UI/menus
        self.last_equip_error = ""

        # --- BASE STATS FROM RACE ---
        base_stat = 5
        if race_name in RACES:
            data = RACES[race_name]
            self.base_attributes = {
                "str": int(base_stat * data.get("str_mult", 1.0)),
                "dex": int(base_stat * data.get("spd_mult", 1.0)),
                "int": base_stat,
                "hp": int(100 * data.get("hp_mult", 1.0)),
                "mana": 20,
                "def_flat": int(data.get("defense", 0)),
            }
            if "hp_flat" in data:
                self.base_attributes["hp"] = int(data["hp_flat"])
        else:
            self.base_attributes = {"str": base_stat, "dex": base_stat, "int": base_stat, "hp": 100, "mana": 20, "def_flat": 0}

        # HUOM: "max_hp"-avainta EI esitäytetä tässä. Se jäädytti rodun
        # perus-HP:n ENNEN kuin aliluokka ehti asettaa omansa - troll (600),
        # commander (150), corrupted_crow (50) yms. eivät koskaan saaneet
        # aiottua HP:tään, koska calculate_final_stats luki vanhentuneen
        # "max_hp":n. Nyt: "hp" on perusarvo; "max_hp" on valinnainen
        # ylikirjoitus (rat_king, premade-buffit) jonka aliluokka asettaa
        # itse. calculate_final_stats: get("max_hp", get("hp", 100)).

        # --- ASE-AFFINITEETIT (rotu + rekrytoinnin satunnaisperkit) ---
        # {weapon_group: kerroin}, esim. {'axe': 1.15}. Näkyvät traits-listassa
        # rekrytointikortilla.
        self.weapon_affinities = dict(RACES.get(race_name, {}).get('affinity', {}))
        for _g, _mult in self.weapon_affinities.items():
            self.traits.append(f"{_g.capitalize()} Affinity +{int(round((_mult - 1) * 100))}%")

        # --- EQUIPMENT ---
        self.equipment = {
            "head": None,
            "body": None,
            "main_hand": create_fists(),
            "off_hand": None,
            "spell1": None,
            "spell2": None,
            "spell3": None,
            "usable": None,
            "usable2": None,
        }

        self.primary_weapon = self.equipment["main_hand"]
        self.current_weapon = self.primary_weapon
        self.armor = None
        self.armor_name = "No Armor"

        # --- VISUALS & RENDERER ---
        # Physics Rect (Jalat) - Pienempi korkeus parempaa syvyysvaikutelmaa varten
        self.rect = pygame.Rect(x, y, 32, 24)
        self.image = pygame.Surface((32, 48), pygame.SRCALPHA).convert_alpha()
        self.rect.topleft = (x, y)
        self.sprites = {}

        self.renderer = GladiatorRenderer(self)
        self.use_sprites = self.load_assets()

        # --- INITIALIZATION ---
        self.calculate_final_stats()
        self.current_hp = self.max_hp
        self.current_mana = self.max_mana
        self.current_stamina = self.max_stamina

        self.ai_controller = None
        if HumanAI:
            self.ai_controller = HumanAI(self)

        if not self.use_sprites:
            self.draw_procedural()

    @property
    def hurt_rect(self):
        """
        Returns the 'body' rectangle for combat hit detection.
        Extends upwards from the physics rect (feet).
        """
        height = self.image.get_height() if self.image else 60
        return pygame.Rect(self.rect.centerx - self.rect.width//2, self.rect.bottom - height, self.rect.width, height)

    # --- DELEGATED DRAWING METHODS ---
    def draw_on_screen(self, surface, offset=(0, 0)):
        # Muodonmuutos: piirrä koodipiirretty peto humanoidin sijaan
        if getattr(self, "shapeshift_form", None) is not None \
                and getattr(self, "image", None) is not None:
            img = self.image
            x = self.rect.centerx - img.get_width() // 2 - offset[0]
            y = self.rect.bottom - img.get_height() - offset[1]
            surface.blit(img, (x, y))
            return
        self.renderer.draw_on_screen(surface, offset)

    def draw_health_bar(self, surface, offset=(0, 0)):
        self.renderer.draw_health_bar(surface, offset)
        self._draw_cast_bar(surface, offset)

    def _draw_cast_bar(self, surface, offset=(0, 0)):
        """Latauspalkki yksikön pään päälle latautuvan loitsun ajaksi."""
        c = getattr(self, "active_cast", None)
        if c is None or getattr(c, "done", True):
            return
        ox, oy = offset
        w, h = 62, 7
        x = self.rect.centerx - w // 2 - ox
        y = self.rect.top - 24 - oy
        pygame.draw.rect(surface, (10, 10, 14), (x - 1, y - 1, w + 2, h + 2),
                         border_radius=3)
        pygame.draw.rect(surface, (44, 44, 54), (x, y, w, h), border_radius=3)
        col = getattr(getattr(c, "spell", None), "icon_color", (180, 180, 255))
        fw = max(0, min(w, int(w * c.progress)))
        if fw > 0:
            pygame.draw.rect(surface, col, (x, y, fw, h), border_radius=3)
        pygame.draw.rect(surface, (205, 205, 215), (x, y, w, h), 1,
                         border_radius=3)
        name = getattr(getattr(c, "spell", None), "name", "")
        if name:
            try:
                from ui_kit import font_small
                lbl = font_small.render(name, True, (225, 222, 210))
                surface.blit(lbl, (self.rect.centerx - lbl.get_width() // 2 - ox,
                                   y - 16))
            except Exception:
                pass

    def draw_info_card(self, surface, x, y, w=200, h=260, bg_color=(30, 30, 35), border_color=(60, 60, 70), show_cost=False, hover=False, can_afford=True, show_talent_details=False):
        """
        Piirtää informatiivisen kortin yksiköstä (esim. Tavern/Roster -valikoihin).
        Näyttää: Nimi, Rotu, Level, HP/Mana, Statsit, Traitit.
        show_talent_details: Commanderin Appraiser's Eye paljastaa talenttien
        tarkat vaikutukset (muuten vain nimet näkyvät).
        """
        # Yritetään hakea fontit, tai käytetään oletusta
        try:
            from ui_kit import font_main, font_small
        except ImportError:
            font_main = pygame.font.SysFont("Arial", 18, bold=True)
            font_small = pygame.font.SysFont("Arial", 14)

        rect = pygame.Rect(x, y, w, h)
        
        # Tausta
        draw_bg = (40, 40, 50) if hover else bg_color
        pygame.draw.rect(surface, draw_bg, rect, border_radius=8)
        
        # Reuna
        b_col = (150, 150, 180) if hover else border_color
        pygame.draw.rect(surface, b_col, rect, 2, border_radius=8)
        
        # 1. Otsikko (Nimi + Lvl)
        name_surf = font_main.render(self.name, True, (255, 255, 255))
        race_surf = font_small.render(f"Lvl {self.level} {self.race_name}", True, (180, 180, 180))
        
        surface.blit(name_surf, (x + 10, y + 8))
        surface.blit(race_surf, (x + 10, y + 30))
        
        # 2. Portrait (Oikea yläkulma)
        face = getattr(self, "big_image", self.image)
        if face:
            s = int(w * 0.35) # Pienennetään kuvaa hieman (35%), jotta teksti mahtuu paremmin
            # Varmistetaan että kuva on olemassa (procedural fallback)
            if not getattr(self, "use_sprites", False):
                self.draw_procedural()
                face = self.image
                
            scaled = pygame.transform.smoothscale(face, (s, s))
            p_rect = pygame.Rect(x + w - s - 10, y + 10, s, s)
            pygame.draw.rect(surface, (20, 20, 20), p_rect)
            pygame.draw.rect(surface, (60, 60, 60), p_rect, 1)
            surface.blit(scaled, p_rect)
            
        # 3. Palkit (HP / Mana)
        bar_w = 100
        bar_h = 6
        bx = x + 10
        by = y + 55
        
        # HP
        pct_hp = self.current_hp / max(1, self.max_hp)
        pygame.draw.rect(surface, (60, 0, 0), (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, (200, 50, 50), (bx, by, int(bar_w * pct_hp), bar_h))
        
        # Mana (jos on)
        if self.max_mana > 0:
            by += 10
            pct_mana = self.current_mana / max(1, self.max_mana)
            pygame.draw.rect(surface, (0, 0, 60), (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, (50, 100, 255), (bx, by, int(bar_w * pct_mana), bar_h))
            
        # 4. Stats Grid
        start_y = y + 85
        col1 = x + 10
        col2 = x + w // 2 + 5
        row_h = 22 # Kasvatetaan riviväliä luettavuuden parantamiseksi
        
        surface.blit(font_small.render(f"STR: {self.strength}", True, (255, 100, 100)), (col1, start_y))
        surface.blit(font_small.render(f"DEX: {self.dexterity}", True, (100, 255, 100)), (col2, start_y))
        surface.blit(font_small.render(f"INT: {self.intelligence}", True, (100, 150, 255)), (col1, start_y + row_h))
        surface.blit(font_small.render(f"DEF: {self.defense}", True, (200, 200, 200)), (col2, start_y + row_h))
        surface.blit(font_small.render(f"SPD: {self.speed:.1f}", True, (220, 220, 220)), (col1, start_y + row_h*2))
        surface.blit(font_small.render(f"CRI: {int(self.crit_chance*100)}%", True, (220, 220, 0)), (col2, start_y + row_h*2))
        
        # 5. Personality + Traits
        row_i = 3
        if self.personality:
            try:
                from progression.personality import PERSONALITIES
                pname = PERSONALITIES.get(self.personality, {}).get("name", self.personality)
                p_y = start_y + row_h * row_i + 5
                origin = f" ({self.origin})" if self.origin else ""
                surface.blit(font_small.render(f"{pname}{origin}", True, (150, 220, 255)), (col1, p_y))
                row_i += 1
            except Exception:
                pass
        if self.traits:
            t_str = ", ".join(self.traits[:3])
            t_max = max(18, int((w - 20) / 8))
            t_line = f"Traits: {t_str}"
            if len(t_line) > t_max:
                # Rivitys pilkun kohdalta, jotta nimet eivät katkea kesken
                cut = t_line.rfind(", ", 0, t_max)
                cut = cut if cut > 0 else t_max
                t_rows = [t_line[:cut], t_line[cut:].lstrip(", ")[:t_max]]
            else:
                t_rows = [t_line]
            for t_row in t_rows:
                t_y = start_y + row_h * row_i + 5
                surface.blit(font_small.render(t_row, True, (255, 215, 0)), (col1, t_y))
                row_i += 1
            # Talenttien tarkat vaikutukset vaativat Appraiser's Eye -taidon
            details = getattr(self, "talent_details", None)
            if details:
                max_y = y + h - (30 if show_cost else 12)
                if show_talent_details:
                    # Katkaisu skaalautuu kortin leveyteen (ei ylivuotoa)
                    max_chars = max(18, int((w - 20) / 8))
                    for d in details:
                        d_y = start_y + row_h * row_i + 5
                        if d_y + 16 > max_y:
                            break
                        surface.blit(font_small.render(d[:max_chars], True,
                                                       (185, 230, 185)),
                                     (col1, d_y))
                        row_i += 1
                else:
                    d_y = start_y + row_h * row_i + 5
                    if d_y + 16 <= max_y:
                        surface.blit(font_small.render(
                            "? Appraiser's Eye reveals more", True,
                            (130, 130, 150)), (col1, d_y))

        # 6. Hinta
        if show_cost:
            cost_y = h - 25
            c_col = (50, 200, 50) if can_afford else (200, 50, 50)
            c_txt = font_main.render(format_money(self.cost), True, c_col)
            surface.blit(c_txt, (x + 10, y + cost_y))

    # =========================================================
    # EQUIP REQUIREMENT HELPERS (used by GuildMenu)
    # =========================================================
    def _normalize_weapon_group(self, g: str) -> str:
        """
        Normalize weapon group names to canonical values.
        For example, polearm/halberd/glaive/pike all map to "spear", and
        "xbow" maps to "crossbow". If no mapping exists the input is returned.
        """
        if not g:
            return ""
        s = str(g).lower().replace(" ", "")
        mapping = {
            "polearm": "spear",
            "halberd": "spear",
            "glaive": "spear",
            "pike": "spear",
            "xbow": "crossbow",
            "crossbow": "crossbow",
        }
        return mapping.get(s, s)

    def _weapon_group_from_item(self, item) -> str:
        g = getattr(item, "weapon_group", None)
        if g:
            return self._normalize_weapon_group(g)
        n = str(getattr(item, "name", "")).lower()
        if "crossbow" in n or "xbow" in n:
            return "crossbow"
        if "bow" in n:
            return "bow"
        if "dagger" in n or "shiv" in n:
            return "dagger"
        if "spear" in n or "pike" in n or "halberd" in n or "glaive" in n:
            return "spear"
        if "staff" in n:
            return "staff"
        if "mace" in n or "hammer" in n or "club" in n:
            return "mace"
        if "axe" in n:
            return "axe"
        if "sword" in n:
            return "sword"
        if "book" in n or "tome" in n:
            return "book"
        if "shield" in n:
            return "shield"
        if "relic" in n or "orb" in n or "talisman" in n or "idol" in n:
            return "relic"
        return ""

    def _armor_group_from_item(self, item) -> str:
        """
        Normalize armor group names. Treat "light" and "cloth" synonyms as cloth.
        """
        g = getattr(item, "armor_group", None)
        if g:
            s = str(g).lower()
            if s in ("light", "cloth", "robe", "leather"):
                return "cloth"
            return s
        n = str(getattr(item, "name", "")).lower()
        if "heavy" in n:
            return "heavy"
        if "medium" in n:
            return "medium"
        if "light" in n or "leather" in n or "cloth" in n or "robe" in n:
            return "cloth"
        return ""

    def _spell_tier_from_item(self, spell) -> int:
        for key in ("tier", "spell_tier", "spell_level", "level"):
            if hasattr(spell, key):
                try:
                    v = int(getattr(spell, key) or 1)
                    return max(1, v)
                except Exception:
                    pass
        return 1

    def _slot_index_from_name(self, slot_name: str) -> int:
        return {"spell1": 1, "spell2": 2, "spell3": 3}.get(slot_name, 0)

    def _has_spell_slot(self, idx: int) -> bool:
        """
        Backward-compatible:
          - if spell_slots_unlocked is set/list/tuple => membership check
          - if spell_slots_unlocked is int => treat as "max unlocked slot number" (e.g. 2 => slot1+2)
        """
        s = self.spell_slots_unlocked
        if isinstance(s, int):
            return idx > 0 and s >= idx
        try:
            return idx in s
        except TypeError:
            return False

    def can_equip_item_to_slot(self, slot_name: str, item):
        """
        Returns (ok: bool, reason: str)

        Rules:
          - Level requirement must be met (min 1, max 30).
          - Spell slots are locked unless unlocked in tree.
          - Spell tier is locked unless unlocked in tree.
          - Shield is locked unless proficient.
          - Off-hand weapon requires dual wield unlock.
          - Main-hand weapon requires Proficiency (HARD LOCK).
          - Armor requires Proficiency (HARD LOCK).
        """
        if item is None:
            return True, ""

        # Normalize slot name aliases
        sname = str(slot_name or "").lower().replace(" ", "").replace("-", "_")
        slot_map = {
            "mainhand": "main_hand",
            "offhand": "off_hand",
            "spellslot1": "spell1",
            "spell_slot1": "spell1",
            "spell1": "spell1",
            "spellslot2": "spell2",
            "spell_slot2": "spell2",
            "spell2": "spell2",
            "spellslot3": "spell3",
            "spell_slot3": "spell3",
            "spell3": "spell3",
            "head": "head",
            "body": "body",
            "usable": "usable",
            "usable2": "usable2",
        }
        slot_name = slot_map.get(sname, slot_name)

        # 1. Spell slots – spells are NOT level-locked, handle before level check
        if slot_name in ("spell1", "spell2", "spell3"):
            idx = self._slot_index_from_name(slot_name)
            if not self._has_spell_slot(idx):
                return False, f"Spell Slot {idx} is locked (unlock in skill tree)."
            req_tier = self._spell_tier_from_item(item)
            if self.max_spell_tier <= 0:
                return False, "You cannot use spells yet (unlock Spell Tier 1)."
            if req_tier > self.max_spell_tier:
                return False, f"Requires Spell Tier {req_tier} (you have Tier {self.max_spell_tier})."
            return True, ""

        # 0. Level Requirement (UNIVERSAL – applies only to non-spells)
        req_lvl = int(getattr(item, "level_required", 1) or 1)
        if self.level < req_lvl:
            return False, f"Requires Level {req_lvl}."

        # 2. Off-hand
        if slot_name == "off_hand":
            # Kaksikätinen pääase varaa molemmat kädet (jousi, varsijousi,
            # keihäs, sauva) - ei kilpeä eikä off-hand-asetta niiden kanssa
            mh = self.equipment.get("main_hand")
            if mh is not None and getattr(mh, "two_handed", False):
                return False, (f"{getattr(mh, 'name', 'Weapon')} requires "
                               "both hands.")
            t = str(getattr(item, "type", "")).lower()
            if t == "shield":
                if "shield" not in self.weapon_masteries:
                    return False, "Shield proficiency required (Shieldbearer)."
                # Paremmat kilvet (tier 2) vaativat Tower Discipline -noden
                if int(getattr(item, "shield_tier", 1)) > \
                        int(getattr(self, "shield_tier", 1)):
                    return False, ("Advanced shield - requires Tower "
                                   "Discipline (skill tree).")
                return True, ""
            if t == "relic":
                # Relikvit vaativat Relic User -noden (int-haara)
                if "relic" not in self.weapon_masteries:
                    return False, "Relic proficiency required (Relic User)."
                return True, ""
            # Off-hand weapon needs dual wield unlock
            if getattr(item, "slot_type", "") == "main_hand" or hasattr(item, "calculate_damage"):
                if not self.can_dual_wield:
                    return False, "Dual Wield is locked (unlock in skill tree)."
                # Off-hand weapon still requires proficiency
                w_group = self._weapon_group_from_item(item)
                if w_group and w_group != "fists" and w_group not in self.weapon_masteries:
                    return False, f"Requires {w_group.capitalize()} Training."
            return True, ""

        # 3. Main hand Weapon (HARD LOCK)
        if slot_name == "main_hand":
            # Kaksikätinen ase vaatii vapaan off-hand-käden
            if getattr(item, "two_handed", False) and \
                    self.equipment.get("off_hand") is not None:
                return False, "Requires both hands (unequip off-hand first)."
            w_group = self._weapon_group_from_item(item)
            # Elämäntaitotyökalut (hakku, kirves, vapa): käyttöoikeus tulee
            # Commander Paths -poluista (tools-listat), EI asekoulutuksesta.
            # Liian korkean tierin työkalun käyttö estetään käyttöhetkellä
            # (commander_progression.tool_allowed).
            # Työkalut eivät vaadi asemestaruutta (pelitesti 19: matalan
            # tierin työkalut käyvät käteen heti kun ne saa - tierit
            # portittaa Commander PATHS tekemisen kautta)
            if w_group in ("pickaxe", "lumber_axe", "fishing_rod",
                           "harvest_tool"):
                return True, ""
            # Fists/None always allowed
            if w_group and w_group != "fists":
                if w_group not in self.weapon_masteries:
                    return False, f"Requires {w_group.capitalize()} Training."

        # 4. Armor (HARD LOCK)
        if slot_name in ("body", "head"):
            a_group = self._armor_group_from_item(item)
            if a_group and a_group not in self.armor_masteries:
                return False, f"Requires {a_group.capitalize()} Armor skill."

        return True, ""

    def can_equip_to_slot(self, slot_name: str, item) -> bool:
        """
        Backwards-compatible wrapper for older menu code.
        IMPORTANT: GuildMenu expects a boolean return here.
        """
        ok, reason = self.can_equip_item_to_slot(slot_name, item)
        self.last_equip_error = str(reason or "") if not ok else ""
        return bool(ok)

    # =========================================================
    # STATS CALCULATION
    # =========================================================
    def calculate_final_stats(self):
        # Reset derived systems
        self.weapon_masteries = set()
        # Baseline armor mastery: cloth (light armor is mapped to cloth)
        self.armor_masteries = {"cloth"}
        self.can_dual_wield = False
        self.block_stamina_mult = 1.0
        self.heavy_armor_penalty_mult = 1.0
        self.double_shot_chance = 0.0
        self.speed_multiplier = 1.0
        self.has_executioner = False
        self.has_second_wind = False

        self.crit_chance = 0.05
        self.range_bonus = 0
        self.hazard_sense = 0
        self.damage_reduction = 0.0
        self.xp_mult = 1.0
        self.cooldown_multiplier = 1.0
        self.mana_regen = self.base_mana_regen

        self.spell_slots_unlocked = set()
        self.max_spell_tier = 0

        # Koulukohtaiset erikoistumisefektit (Necro/Druid/Holy). Loitsut lukevat
        # nämä (summon_max, lifesteal_pct, hot_power, heal_power, team_buff...).
        self.school_effects = {}
        self.magic_school = None

        # Skill-puun PROSENTTIBONUKSET (str_pct/dex_pct/int_pct): kerätään
        # puusta ja sovelletaan VARUSTEIDEN JÄLKEEN, jotta % kertoo myös
        # gearin antamat statit (statit tulevat pääosin gearista).
        _pct = {"str_pct": 0.0, "dex_pct": 0.0, "int_pct": 0.0}

        # Base Stats
        base_hp_val = int(self.base_attributes.get("max_hp", self.base_attributes.get("hp", 100)))
        self.max_hp = base_hp_val
        self.max_mana = int(self.base_attributes.get("mana", 20))
        self.strength = int(self.base_attributes.get("str", 5))
        self.dexterity = int(self.base_attributes.get("dex", 5))
        self.intelligence = int(self.base_attributes.get("int", 5))
        # Arcane strain -katto skaalaa kurilla/kestavyydella (INT).
        self.max_strain = 80 + self.intelligence * 4
        if getattr(self, "current_strain", 0.0) > self.max_strain:
            self.current_strain = float(self.max_strain)
        self.defense = int(self.base_attributes.get("def_flat", 0))

        # Skill Tree effects
        for skill_id in list(self.unlocked_skills):
            skill_data = SKILL_TREE.get(skill_id, {})
            effects = skill_data.get("effects", {}) or {}

            if "str" in effects:
                self.strength += int(effects["str"])
            if "dex" in effects:
                self.dexterity += int(effects["dex"])
            if "int" in effects:
                self.intelligence += int(effects["int"])
            # Prosenttibonukset (uusi malli: puu antaa %, gear antaa määrät)
            for _k in ("str_pct", "dex_pct", "int_pct"):
                if _k in effects:
                    _pct[_k] += float(effects[_k])
            if "max_hp" in effects:
                self.max_hp += int(effects["max_hp"])
            if "max_mana" in effects:
                self.max_mana += int(effects["max_mana"])
            if "defense" in effects:
                self.defense += int(effects["defense"])
            if "mana_regen" in effects:
                self.mana_regen += float(effects["mana_regen"])
            if "cooldown_mult" in effects:
                self.cooldown_multiplier *= float(effects["cooldown_mult"])
            if "speed_mult" in effects:
                self.speed_multiplier *= float(effects["speed_mult"])
            if "crit_chance" in effects:
                self.crit_chance += float(effects["crit_chance"])
            if "range_bonus" in effects:
                self.range_bonus += int(effects["range_bonus"])
            if "hazard_sense" in effects:
                self.hazard_sense = max(self.hazard_sense, int(effects["hazard_sense"]))

            # Proficiencies
            if "weapon_prof" in effects:
                p = effects["weapon_prof"]
                if isinstance(p, (list, tuple, set)):
                    self.weapon_masteries.update([str(x).lower() for x in p])
                else:
                    self.weapon_masteries.add(str(p).lower())

            if "armor_prof" in effects:
                p = effects["armor_prof"]
                if isinstance(p, (list, tuple, set)):
                    self.armor_masteries.update([str(x).lower() for x in p])
                else:
                    self.armor_masteries.add(str(p).lower())

            # Kilpitier (Tower Discipline): paremmat kilvet vaativat tämän
            if "shield_tier" in effects:
                self.shield_tier = max(getattr(self, "shield_tier", 1),
                                       int(effects["shield_tier"]))

            # Spell unlocks
            if "unlock_spell_slot" in effects:
                p = effects["unlock_spell_slot"]
                if isinstance(p, (list, tuple, set)):
                    for x in p:
                        try:
                            self.spell_slots_unlocked.add(int(x))
                        except Exception:
                            pass
                else:
                    try:
                        self.spell_slots_unlocked.add(int(p))
                    except Exception:
                        pass

            if "spell_tier" in effects:
                self.max_spell_tier = max(self.max_spell_tier, int(effects["spell_tier"]))
            if "max_spell_tier" in effects:
                self.max_spell_tier = max(self.max_spell_tier, int(effects["max_spell_tier"]))

            # Specials
            if "heavy_armor_mult" in effects:
                self.heavy_armor_penalty_mult *= float(effects["heavy_armor_mult"])
            if "ignore_armor_penalty" in effects:
                self.heavy_armor_penalty_mult = 0.0
            if "can_dual_wield" in effects:
                self.can_dual_wield = True
            if "shield_efficiency" in effects:
                self.block_stamina_mult = max(0.1, 1.0 - float(effects["shield_efficiency"]))
            if "block_stamina_mult" in effects:
                self.block_stamina_mult *= float(effects["block_stamina_mult"])
            if "dual_shot_chance" in effects:
                self.double_shot_chance += float(effects["dual_shot_chance"])
            if "executioner" in effects:
                self.has_executioner = True
            if "second_wind" in effects:
                self.has_second_wind = True
            if "steady_draw" in effects:
                self.has_steady_draw = True

            # Koulukohtaiset erikoistumisefektit (Necro/Druid/Holy)
            if skill_id in _SCHOOL_NODES:
                for k, v in effects.items():
                    if k.startswith("school_"):
                        self.magic_school = k[len("school_"):]
                    elif isinstance(v, (int, float)):
                        self.school_effects[k] = self.school_effects.get(k, 0) + v
                    else:
                        self.school_effects[k] = v

        # No implicit spell tier: spell tier must be unlocked via skill tree.

        # Equipment stats & penalties
        gear_spd_penalty = 0
        bonus_stamina = 0  # varusteiden stamina lisätään uudelleenlaskennan JÄLKEEN
        self.armor = None
        self.armor_name = "No Armor"

        for slot, item in self.equipment.items():
            if not item:
                continue

            # Standard stats
            if hasattr(item, "defense"):
                self.defense += int(item.defense)
            if hasattr(item, "health_bonus"):
                self.max_hp += int(item.health_bonus)
            if hasattr(item, "mana_bonus"):
                self.max_mana += int(item.mana_bonus)
            if hasattr(item, "crit_bonus"):
                self.crit_chance += float(item.crit_bonus)

            # --- UNIVERSAL PASSIVE BONUS (Aseet, Armor, Helmet, Off-hand) ---
            # Suorat primääristatit varusteista (statit tulevat pääosin
            # gearista - stat_curve mitoittaa määrät per taso/tier)
            if hasattr(item, "str_bonus"):
                self.strength += int(getattr(item, "str_bonus", 0) or 0)
            if hasattr(item, "dex_bonus"):
                self.dexterity += int(getattr(item, "dex_bonus", 0) or 0)
            if hasattr(item, "int_bonus"):
                self.intelligence += int(getattr(item, "int_bonus", 0) or 0)

            # Erikoistumisvarusteet (relikvit yms.): koulubonukset kertyvät
            # school_effects-sanakirjaan kuten puun nodet
            for _k, _v in (getattr(item, "school_bonuses", {}) or {}).items():
                if isinstance(_v, (int, float)):
                    self.school_effects[_k] = self.school_effects.get(_k, 0) + _v
                else:
                    self.school_effects[_k] = _v

            if hasattr(item, "passive_bonuses"):
                bonuses = getattr(item, "passive_bonuses", {}) or {}
                for k, v in bonuses.items():
                    if k == "hp":
                        self.max_hp += v
                    elif k == "mana":
                        self.max_mana += v
                    elif k == "stamina":
                        bonus_stamina += v
                    elif k == "str":
                        self.strength += v
                    elif k == "dex":
                        self.dexterity += v
                    elif k == "int":
                        self.intelligence += v
                    elif k == "mana_regen":
                        self.mana_regen += v

            item_speed_mod = float(getattr(item, "speed_bonus", 0))
            armor_group = self._armor_group_from_item(item)

            # Proficiency penalty for medium/heavy if not known
            if armor_group in ("medium", "heavy") and armor_group not in self.armor_masteries:
                gear_spd_penalty -= 0.20

            # Heavy armor weight management
            if armor_group == "heavy":
                item_speed_mod *= self.heavy_armor_penalty_mult

            gear_spd_penalty += item_speed_mod

            if slot == "body":
                self.armor = item
                self.armor_name = getattr(item, "name", "No Armor")

        # Skill-puun prosenttibonukset: sovelletaan gearin JÄLKEEN, ennen
        # johdettuja statteja (stamina/strain) -> % hyödyttää myös niitä.
        if _pct["str_pct"]:
            self.strength = int(self.strength * (1.0 + _pct["str_pct"]))
        if _pct["dex_pct"]:
            self.dexterity = int(self.dexterity * (1.0 + _pct["dex_pct"]))
        if _pct["int_pct"]:
            self.intelligence = int(self.intelligence * (1.0 + _pct["int_pct"]))
            self.max_strain = 80 + self.intelligence * 4

        # Final calculations
        self.max_stamina = 50 + (self.strength * 1.5) + (self.dexterity * 1.5)
        self.max_stamina += bonus_stamina  # varusteet (bugikorjaus: ei jyrää)

        # --- TALENTIT (synnynnäiset lahjat, systems/talents.py) ---
        _tal = getattr(self, "talent_effects", {}) or {}
        self.defense += int(_tal.get("defense", 0))
        self.max_stamina += float(_tal.get("max_stamina", 0))
        self.crit_chance += float(_tal.get("crit_chance", 0.0))
        self.damage_reduction += float(_tal.get("damage_reduction", 0.0))
        self.speed_multiplier *= float(_tal.get("speed_mult", 1.0))
        self.xp_mult *= float(_tal.get("xp_mult", 1.0))

        dex_compensation = self.dexterity * 0.005
        # GAME FEEL (pelitesti 23): taisteluliikkeen perusvauhti nostettu
        # 1.0 -> 2.0 px/frame (oli ryömintää; kaupunkikävely on 4.0).
        # Sprintillä ~3.6 -> yhtenäinen tuntuma kaupungin kanssa.
        # Symmetrinen muutos: kaikki yksiköt liikkuvat samalla kaavalla.
        final_speed_mod = float(gear_spd_penalty) + float(dex_compensation)

        self.walk_speed = max(0.5, (2.0 + (self.dexterity * 0.025) + final_speed_mod) * self.speed_multiplier)
        self.speed = self.walk_speed

        dex_cdr = min(0.5, self.dexterity * 0.015)
        self.cooldown_multiplier *= (1.0 - dex_cdr)

        # Weapon stats
        w = self.equipment.get("main_hand")
        if not w:
            w = create_fists()
            self.equipment["main_hand"] = w

        # --- FIX: Update current_weapon reference ---
        self.current_weapon = w

        # Aseperheen identiteetti (systems/weapon_feel.py): rytmi, range
        # ja staminakulut eroavat perheittäin - dagger nopea, mace raskas
        from systems import weapon_feel
        w_group = self._weapon_group_from_item(w)

        self.attack_range = int(getattr(w, "attack_range", 35)) \
            + int(self.range_bonus) + weapon_feel.range_add(w_group)
        self.weapon_type = str(getattr(w, "type", "melee")).lower()
        self.weapon_effect = str(getattr(w, "effect", "damage")).lower()

        base_atk_spd = 60.0
        if hasattr(w, "speed_bonus"):
            base_atk_spd -= (float(w.speed_bonus) * 10.0)
        base_atk_spd *= weapon_feel.cd_mult(w_group)

        # Weapon proficiency penalty: slower if not proficient (except fists)
        if w_group and (w_group not in self.weapon_masteries) and (getattr(w, "name", "") != "Fists"):
            base_atk_spd *= 2.0

        self.attack_speed = int(max(20, base_atk_spd * float(self.cooldown_multiplier)))

        # Sairaudet/vammat (pelitesti 18): nopeus, stamina ja max-HP
        # kärsivät kunnes tila paranee (Commander on immuuni tiloille)
        if getattr(self, "conditions", None):
            try:
                from systems import conditions as _cond
                _m = _cond.modifiers(self)
                self.walk_speed = max(0.2, self.walk_speed
                                      * _m["speed_mult"])
                self.speed = self.walk_speed
                self.max_stamina = max(10, int(self.max_stamina
                                               * _m["stamina_mult"]))
                self.max_hp = max(10, int(self.max_hp * _m["hp_mult"]))
            except Exception:
                pass

        # Clamp
        self.current_hp = min(self.current_hp, self.max_hp)
        self.current_stamina = min(self.current_stamina, self.max_stamina)
        self.current_mana = min(self.current_mana, self.max_mana)

        if not self.equipment.get("body"):
            self.armor_name = "No Armor"

    # =========================================================
    # EQUIPMENT MANAGEMENT
    # =========================================================
    def equip_item_to_slot(self, slot, item):
        """
        Equip an item into the given slot. Before equipping, validate the
        requirement rules via can_equip_item_to_slot(). On success the
        existing item in the slot is returned; on failure the attempted
        item is returned unchanged and the equipment remains the same.
        """
        # Perform lock checks. Spells are handled inside can_equip_item_to_slot()
        ok, reason = self.can_equip_item_to_slot(slot, item)
        if not ok:
            # record reason for UI consumption and do not change equipment
            self.last_equip_error = str(reason or "")
            # return the attempted item back so that caller can restore it
            return item

        # equipping None (unequip) is always allowed
        old_item = self.equipment.get(slot)
        self.equipment[slot] = item
        self.calculate_final_stats()
        return old_item

    def unequip_slot(self, slot):
        if slot == "main_hand":
            old = self.equipment.get("main_hand")
            if old and getattr(old, "name", "") == "Fists":
                return None
            self.equipment["main_hand"] = create_fists()
            self.calculate_final_stats()
            return old

        old = self.equipment.get(slot)
        if old:
            self.equipment[slot] = None
            self.calculate_final_stats()
        return old

    def equip_primary(self, item):
        self.equip_item_to_slot("main_hand", item)

    def equip_item(self, item):
        self.equip_item_to_slot(getattr(item, "slot_type", "main_hand"), item)

    # =========================================================
    # DRAWING
    # =========================================================
    def load_assets(self):
        return False

    def draw_procedural(self):
        if getattr(self, "use_sprites", False):
            return
        self.image.fill((100, 100, 100, 255))

    # =========================================================
    # ACTIONS
    # =========================================================
    def set_sprinting(self, active: bool):
        if self.stun_timer > 0: return
        
        if active:
            if not self.is_sprinting and self.current_stamina > 25 and not self.is_blocking:
                self.is_sprinting = True
        else:
            self.is_sprinting = False

    def set_blocking(self, active: bool):
        if self.stun_timer > 0: return

        # GAME FEEL: parry-ikkuna - block_timer mittaa montako framea
        # blokki on ollut ylhäällä; tuore blokki (<=10) torjuu täydellisesti
        if active and not self.is_blocking:
            self.block_timer = 0
        
        if self.is_dashing:
            self.is_blocking = False
            return

        # UUSI: Estä blockaus jos ladataan asetta tai hyökätään
        if self.is_charging or self.animation_state == "attack":
            self.is_blocking = False
            return

        offhand = self.equipment.get("off_hand")
        mainhand = self.equipment.get("main_hand")
        
        is_shield = offhand and str(getattr(offhand, "type", "")).lower() == "shield"
        has_shield_prof = "shield" in self.weapon_masteries

        # Weapon blocking (Parry) - Sallitaan jos on melee-ase (ei nyrkit)
        is_weapon = mainhand and getattr(mainhand, "type", "") == "melee" and getattr(mainhand, "name", "") != "Fists"

        can_block = (is_shield and has_shield_prof) or is_weapon

        if active and can_block and self.current_stamina > 0:
            self.is_blocking = True
            self.is_sprinting = False
        else:
            self.is_blocking = False

    def perform_dash(self, dx, dy):
        if self.is_dashing or self.is_dead or self.stun_timer > 0:
            return False
        
        # Tarkista onko varauksia
        if self.current_dashes > 0:
            self.current_dashes -= 1
            # Resetoi latausajastin jos se oli nollassa (tai pidä se käynnissä jos lataa toista)
            # Yksinkertainen: Lataa aina yhtä kerrallaan
            self.is_dashing = True
            self.is_blocking = False
            self.dash_timer = 10
            self.dash_damage = 0 # Nollataan oletuksena (ase asettaa tämän jos on hyökkäys)
            self.dash_hit_list = [] # Tyhjennetään osumalista
            
            l = math.hypot(dx, dy) or 1.0
            self.dash_vector = (dx / l, dy / l)
            sound_system.play_sound("swish")
            return True
        return False

    def perform_shield_bash(self, target_pos, manager=None):
        """KILPI-ISKU: LMB blokin aikana - lyhyt tyrkkäys eteenpäin joka
        vahingoittaa (STR-skaalaus), horjuttaa (20 f) ja työntää lähellä
        olevat viholliset. Vaatii kilven + shield-masteryn + aktiivisen
        blokin. Sama koodipolku pelaajalle ja AI:lle."""
        off = self.equipment.get("off_hand")
        if not (off and str(getattr(off, "type", "")).lower() == "shield"):
            return False
        if "shield" not in self.weapon_masteries:
            return False
        if not self.is_blocking or self.is_dead or self.stun_timer > 0:
            return False
        if getattr(self, "shield_bash_cd", 0) > 0:
            return False
        if self.current_stamina < 15:
            return False

        self.shield_bash_cd = 90
        self.current_stamina -= 15
        self.animation_state = "attack"
        self.animation_timer = 12
        dx = target_pos[0] - self.rect.centerx
        dy = target_pos[1] - self.rect.centery
        l = math.hypot(dx, dy) or 1.0
        # Tyrkkäysaskel eteen
        self.check_wall_collision(dx / l * 10.0, dy / l * 10.0, None)
        sound_system.play_sound("swish")

        dmg = int(4 + self.strength * 0.5)
        if manager:
            manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40,
                                    "BASH!", color=(200, 220, 255))
            for u in manager.all_units:
                if u is self or self.is_ally(u) or getattr(u, "is_dead", False):
                    continue
                ux = u.rect.centerx - self.rect.centerx
                uy = u.rect.centery - self.rect.centery
                dist = math.hypot(ux, uy)
                # Etusektori: kohteen pitää olla iskusuunnassa
                if dist > 60 or (ux * dx + uy * dy) <= 0:
                    continue
                real = u.take_damage(dmg, "Physical", attacker=self,
                                     manager=manager)
                self.stats["damage"] += int(real)
                if getattr(u, "stun_immunity", 0) <= 0:
                    u.stun_timer = max(getattr(u, "stun_timer", 0), 20)
                if hasattr(u, "check_wall_collision"):
                    ul = dist or 1.0
                    u.check_wall_collision(ux / ul * 16.0, uy / ul * 16.0,
                                           None)
            if self is getattr(manager, "player_character", None):
                manager.trigger_hit_stop(3)
                manager.trigger_screen_shake(4)
        return True

    def perform_dodge(self):
        if self.ai_controller and hasattr(self.ai_controller, "current_target"):
            target = self.ai_controller.current_target
            if target:
                dx = self.rect.centerx - target.rect.centerx
                dy = self.rect.centery - target.rect.centery
                return self.perform_dash(dx, dy)
        ang = random.random() * math.tau
        return self.perform_dash(math.cos(ang), math.sin(ang))

    def is_ally(self, other):
        """Tarkistaa onko kohde liittolainen (Vihreä ja Sininen ovat kavereita)."""
        if other is self: return True
        t1 = getattr(self, "team_color", "Neutral")
        t2 = getattr(other, "team_color", "Neutral")
        
        if t1 == t2: return True
        
        # Green (Player) ja Blue (Ally) ovat liittolaisia
        is_t1_good = (t1 == GREEN or t1 == BLUE)
        is_t2_good = (t2 == GREEN or t2 == BLUE)
        
        if is_t1_good and is_t2_good: return True
        return False

    # =========================================================
    # COMBAT
    # =========================================================
    def perform_attack(self, target=None, manager=None, damage_mult=1.0, range_override=None, target_pos=None):
        if self.is_dead:
            return False
        if self.stun_timer > 0:
            return False
        # Jos target on annettu, tarkistetaan onko se validi
        if target and (target is self or getattr(target, "is_dead", False)):
            return False
            
        if self.attack_cooldown > 0:
            return False
        if self.current_stamina < 5:
            # GAME FEEL: kerro pelaajalle MIKSI lyönti ei lähde
            if manager and self is getattr(manager, "player_character", None):
                if getattr(self, "_exhaust_flash_cd", 0) <= 0:
                    self._exhaust_flash_cd = 45
                    manager.vfx.show_damage(self.rect.centerx,
                                            self.rect.top - 30,
                                            "EXHAUSTED", color=(160, 160, 160))
            return False

        # --- UUSI: Hyökkäys peruuttaa blockauksen ---
        self.is_blocking = False

        # Asetetaan hyökkäysanimaatio
        self.animation_state = "attack"
        self.animation_timer = 15 # Animaation kesto frameina

        w = self.equipment.get("main_hand") or create_fists()

        # Jos target on määritelty (esim. AI), tehdään etäisyystarkistukset
        if target:
            max_range = range_override if range_override is not None else getattr(self, "attack_range", 0)
            
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            ground_dist = math.hypot(dx, dy)
            
            my_h = getattr(self, "jump_height", 0)
            target_h = getattr(target, "jump_height", 0)
            h_diff = abs(target_h - my_h)
            
            total_dist = math.hypot(ground_dist, h_diff)
            
            if total_dist > max_range:
                return False
            
            self.attack_vector = (dx,dy)

            # --- LOS CHECK ---
            if manager and getattr(manager, "current_arena", None):
                obstacles = getattr(manager.current_arena, "obstacles", [])
                if not self.has_line_of_sight(target, obstacles):
                    return False
        elif target_pos:
            # Lyödään kohti annettua pistettä (kursori)
            dx = target_pos[0] - self.rect.centerx
            dy = target_pos[1] - self.rect.centery
            self.attack_vector = (dx, dy)
        else:
            # Ei kohdetta -> Lyödään katsesuuntaan
            self.attack_vector = (10 if self.facing_right else -10, 0)

        # --- STAMINA COST CALCULATION ---
        # GAME FEEL: 18 -> 14 - lyöntisarjat eivät kuivaa staminaa heti
        base_cost = 14
        w_group = getattr(w, "weapon_group", "")
        reduction = 0
        
        # Raskaat aseet (STR)
        if w_group in ["axe", "mace", "spear", "shield", "fists", "sword"]:
            reduction = self.strength * 0.3
        # Kevyet / Ranged aseet (DEX)
        elif w_group in ["dagger", "bow", "crossbow"]:
            reduction = self.dexterity * 0.3
        # Taika-aseet (INT - henkinen keskittyminen vähentää rasitusta)
        elif w_group in ["staff", "book"]:
            reduction = self.intelligence * 0.3
            
        # Aseperheen staminakerroin (dagger/fists kevyt, mace raskas)
        from systems import weapon_feel
        final_cost = max(4, int((base_cost - reduction)
                                * weapon_feel.stamina_mult(w_group)))

        self.attack_cooldown = self.attack_speed
        self.current_stamina = max(0, self.current_stamina - final_cost)
        self._break_invisibility(manager)  # Hyökkäys paljastaa

        # GAME FEEL: pieni syöksähdys lyönnin suuntaan (painon ja
        # sitoutumisen tuntu) - vain melee, seinät kunnioittaen
        if getattr(w, "type", "") == "melee":
            _al = math.hypot(self.attack_vector[0], self.attack_vector[1]) or 1.0
            _obs = None
            if manager and getattr(manager, "current_arena", None):
                _obs = getattr(manager.current_arena, "obstacles", None)
            self.check_wall_collision(self.attack_vector[0] / _al * 8.0,
                                      self.attack_vector[1] / _al * 8.0, _obs)

        # --- HITBOX CHECK (UUSI) ---
        hit_targets = []
        
        if hasattr(w, "get_swing_rect"):
            swing_rect = w.get_swing_rect(self.rect, self.facing_right, 0, self.attack_speed, self.attack_vector)
            
            # UNIFIED HIT DETECTION (AI & PLAYER)
            # Etsitään aina kaikki osumat alueelta. Tämä mahdollistaa "Cleave"-vahingon myös AI:lle.
            if manager:
                for u in manager.all_units:
                    if u is self or self.is_ally(u) or u.is_dead: continue
                    # Käytä hurt_rect jos on, muuten rect
                    hr = getattr(u, "hurt_rect", u.rect)
                    if swing_rect.colliderect(hr):
                        hit_targets.append(u)
            
            # AI-spesifi palaute: Jos meillä oli tietty kohde, mutta se EI ole osumalistassa -> MISS
            if target and target not in hit_targets:
                 if manager:
                     manager.vfx.show_damage(target.rect.centerx, target.rect.top - 20, "MISS", color=(200, 200, 200))
        else:
            # Fallback aseille ilman hitboxia (esim. vanhat tai ranged)
            if target:
                hit_targets.append(target)

        # 1. ASEEN ÄÄNI (Aina ensin)
        if hasattr(w, "on_attack_start") and manager:
            # Soita ääni (käytä ensimmäistä kohdetta tai None)
            t = hit_targets[0] if hit_targets else None
            
            # FIX: Jos hitbox ei osunut (t is None), mutta meillä oli alkuperäinen kohde (AI)
            # tai tähtäyspiste (Pelaaja), luodaan nukkekohde.
            if t is None:
                dummy_pos = None
                if target: # AI:n alkuperäinen kohde
                    dummy_pos = target.rect.center
                elif target_pos: # Pelaajan kursori
                    dummy_pos = target_pos
                
                if dummy_pos:
                    class DummyTarget:
                        def __init__(self, x, y): self.rect = pygame.Rect(x, y, 1, 1); self.is_dead = False
                    t = DummyTarget(dummy_pos[0], dummy_pos[1])

            w.on_attack_start(self, t, manager)
        else:
            sound_system.play_sound("attack_melee")

        # 2. RODUN ÄÄNI (Satunnainen lisämauste, ei korvaa aseen ääntä)
        if self.race_name in ["Undead", "Skeleton", "Zombie"]:
            if random.random() < 0.4:
                sound_system.play_sound(random.choice(['undead_attack_1', 'undead_attack_2', 'undead_attack_3', 'undead_attack_4']))
        elif self.race_name == "Bog Leech":
            if random.random() < 0.4:
                sound_system.play_sound(random.choice([f'leech_attack_{i}' for i in range(1, 5)]))
        elif self.race_name == "Giant Frog":
            if random.random() < 0.4:
                sound_system.play_sound(random.choice([f'frog_attack_{i}' for i in range(1, 5)]))

        stats = {"str": self.strength, "dex": self.dexterity, "int": self.intelligence, "spd": self.speed}

        # Käsitellään kaikki osumat
        for t in hit_targets:
            dmg = 5
            if hasattr(w, "calculate_damage"):
                dmg = w.calculate_damage(stats)
            # Perheen DPS-kompensaatio (rytmi muuttui weapon_feelissä)
            dmg *= weapon_feel.dmg_mult(getattr(w, "weapon_group", ""))
            # Ase-affiniteetti (rotu/perkki)
            dmg *= self.weapon_affinities.get(getattr(w, "weapon_group", ""), 1.0)
            # Moraali: 0.9x (0) ... 1.0x (50) ... 1.1x (100)
            dmg *= 0.9 + 0.2 * (getattr(self, "morale", 50) / 100.0)
            # Sairaudet/vammat heikentävät iskua (pelitesti 18)
            if getattr(self, "conditions", None):
                try:
                    from systems import conditions as _cond
                    dmg *= _cond.modifiers(self)["damage_mult"]
                except Exception:
                    pass

            is_crit = False
            if random.random() < self.crit_chance:
                dmg *= 1.5
                is_crit = True

            if self.has_executioner and t.current_hp < t.max_hp * 0.30:
                dmg *= 1.15

            dmg = int(dmg * float(damage_mult))

            # Aseperheen osumakerroin: backstab, tip damage, riposte
            # (systems/weapon_feel.py - sama pelaajalle ja AI:lle)
            if getattr(w, "type", "") == "melee":
                dmg = int(dmg * weapon_feel.pre_hit_mult(
                    self, t, getattr(w, "weapon_group", ""), manager))

            if self.weapon_effect == "heal":
                t.heal(abs(dmg), manager)
            else:
                real_dmg = t.take_damage(dmg, "Physical", attacker=self, manager=manager)
                self.stats["damage"] += int(real_dmg)
                # HUOM: tappo kirjataan take_damagessa (kaikki osumatyypit)
                if hasattr(w, "on_hit"):
                    w.on_hit(self, t, real_dmg, manager)
                # GAME FEEL: mikrotyrkkäys osumasta - isku tuntuu kontaktilta
                if real_dmg > 0 and hasattr(t, "check_wall_collision"):
                    _kl = math.hypot(self.attack_vector[0], self.attack_vector[1]) or 1.0
                    t.check_wall_collision(self.attack_vector[0] / _kl * 7.0,
                                           self.attack_vector[1] / _kl * 7.0, None)
                # Aseperheen osumaefekti: mace-daze, spear-työntö,
                # fists-combo (systems/weapon_feel.py)
                if getattr(w, "type", "") == "melee":
                    weapon_feel.post_hit(self, t,
                                         getattr(w, "weapon_group", ""),
                                         real_dmg, manager)
            
            # --- GAME FEEL: HIT STOP & SHAKE (Vain pelaajalle) ---
            if manager and self == getattr(manager, "player_character", None):
                manager.trigger_hit_stop(4) # Pysäytä peli 4 frameksi (n. 60ms)
                manager.trigger_screen_shake(3) # Täräytä ruutua
            
            if is_crit and manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 10, "CRIT!", is_crit=True)

        # Ranged dual shot chance
        # (Tämä toimii vain jos target on määritelty, koska ranged ei käytä swing_rectiä samalla tavalla)
        if target and self.weapon_type == "ranged" and self.double_shot_chance > 0:
            if random.random() < self.double_shot_chance:
                if manager:
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30, "DUAL!")
                dmg2 = 5
                if hasattr(w, "calculate_damage"):
                    dmg2 = w.calculate_damage(stats)
                if random.random() < self.crit_chance:
                    dmg2 *= 1.5
                real_dmg2 = target.take_damage(int(dmg2), "Physical", attacker=self, manager=manager)
                self.stats["damage"] += int(real_dmg2)

        return True

    def has_line_of_sight(self, target, obstacles):
        if not obstacles: return True
        x1, y1 = self.rect.center
        x2, y2 = target.rect.center
        
        for obs in obstacles:
            if obs is target or obs is self: continue
            
            r = getattr(obs, "rect", obs)
            # Default to blocking
            blocks = getattr(obs, "blocks_projectiles", True)
            
            # Check type for map tiles (don't block sight over water/mud)
            t = getattr(obs, "type", None)
            if t in ["water", "mud", "lava"]: blocks = False
            
            if not blocks: continue
            
            if r.clipline(x1, y1, x2, y2):
                return False
        return True

    def heal(self, amount, manager=None):
        if self.is_dead:
            return
        old = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + int(amount))
        diff = int(self.current_hp - old)
        if diff > 0 and manager:
            manager.vfx.show_damage(self.rect.centerx, self.rect.top, diff, type="heal")

    def adjust_morale(self, delta):
        """Moraali pysyy välillä 0-100."""
        self.morale = max(0, min(100, int(getattr(self, "morale", 50) + delta)))

    def take_damage(self, amount, damage_type="Physical", attacker=None, manager=None):
        if self.is_dead:
            return 0

        if self.is_dashing:
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, "DODGE")
            return 0

        # Osuma keskeyttää passiivisen HP-regenin 5 sekunniksi
        self.hp_regen_delay = 300

        # --- LAUMA-APU (pelitesti 25): kitetystä ei palkita ---
        # Kun yksikköön osutaan, lähellä olevat TOIMETTOMAT liittolaiset
        # kääntyvät hyökkääjää vastaan. Pelaaja ei voi enää nyppiä
        # vihollisia yksi kerrallaan max-rangesta - lauma vastaa yhdessä.
        if attacker is not None and manager is not None and \
                not self.is_ally(attacker):
            for ally in (getattr(manager, "all_units", None) or ()):
                if ally is self or ally is attacker or \
                        getattr(ally, "is_dead", False):
                    continue
                if not self.is_ally(ally):
                    continue
                ai = getattr(ally, "ai_controller", None)
                if ai is None:
                    continue
                cur = getattr(ai, "current_target", None)
                if cur is not None and not getattr(cur, "is_dead", False):
                    continue   # on jo kimpussa jonkun
                d = math.hypot(ally.rect.centerx - self.rect.centerx,
                               ally.rect.centery - self.rect.centery)
                if d <= 350:
                    ai.current_target = attacker
                    ai.rethink_timer = max(getattr(ai, "rethink_timer", 0), 60)

        # --- POINT BLANK: etäaseet heikkoja nollaetäisyydeltä ---
        # Melee vs ranged -dynamiikka (systems/weapon_feel.py): jousi/
        # varsijousi/kirja/sauva tekee -40 % kun kohde on iholla. Antaa
        # meleelle syyn painaa kiinni ja ampujalle syyn pitää etäisyys -
        # korjaa myös AI-kitingin joka voitti kaikki melee-matsit.
        if attacker is not None and \
                str(getattr(attacker, "weapon_type", "")) == "ranged":
            _pb = math.hypot(self.rect.centerx - attacker.rect.centerx,
                             self.rect.centery - attacker.rect.centery)
            from systems import weapon_feel as _wf
            if _pb < _wf.POINT_BLANK_DIST:
                amount = int(amount * _wf.POINT_BLANK_MULT)
                if manager:
                    manager.vfx.show_damage(self.rect.centerx,
                                            self.rect.top - 45,
                                            "POINT BLANK",
                                            color=(170, 170, 170))

        offhand = self.equipment.get("off_hand")
        mainhand = self.equipment.get("main_hand") # Haetaan pääase torjuntatehon laskemiseen

        # --- GAME FEEL: PERFECT PARRY ---
        # Tuore blokki (nostettu <=10 framea ennen osumaa) torjuu melee-
        # iskun täydellisesti ILMAN staminakulua ja horjuttaa hyökkääjää.
        # Palkitsee reaktion; toimii symmetrisesti myös AI:lle.
        if self.is_blocking and damage_type == "Physical" \
                and getattr(self, "block_timer", 999) <= 10 \
                and getattr(self, "parry_cooldown", 0) <= 0 \
                and attacker is not None \
                and getattr(attacker, "weapon_type", "melee") != "ranged":
            self.parry_cooldown = 90   # kerran per 1.5 s (AI togglaa blokkia)
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 25,
                                        "PERFECT PARRY!", color=(255, 230, 120))
                try:
                    manager.vfx.create_impact_sparks(
                        self.rect.centerx, self.rect.centery,
                        color=(255, 230, 120), count=10)
                except Exception:
                    pass
                # Tuntuu kädessä: tärinä + pysäytys jos pelaaja osallisena
                if self is getattr(manager, "player_character", None) or \
                        attacker is getattr(manager, "player_character", None):
                    manager.trigger_hit_stop(5)
                    manager.trigger_screen_shake(4)
            sound_system.play_sound("swish")
            if getattr(attacker, "stun_immunity", 0) <= 0:
                attacker.stun_timer = max(getattr(attacker, "stun_timer", 0), 25)
                if manager:
                    manager.vfx.show_damage(attacker.rect.centerx,
                                            attacker.rect.top - 20,
                                            "STAGGERED", color=(200, 200, 255))
            # Riposte-ikkuna: seuraava melee-isku 1.5 s sisällä tekee +30 %
            # (systems/weapon_feel.py kuluttaa tämän)
            self.riposte_timer = 90
            return 0

        # Blocking (Shield or Weapon)
        if self.is_blocking and damage_type == "Physical":
            is_shield = offhand and str(getattr(offhand, "type", "")).lower() == "shield"
            
            # --- BLOCK EFFICIENCY (Damage Reduction) ---
            block_pct = 0.1 # Oletus (Nyrkit)
            
            if is_shield:
                block_pct = 1.0 # Kilpi torjuu kaiken
            elif mainhand:
                w_group = self._weapon_group_from_item(mainhand)
                if w_group == "sword": block_pct = 0.5
                elif w_group == "dagger": block_pct = 0.3
                elif w_group in ["axe", "mace"]: block_pct = 0.4
                elif w_group == "spear": block_pct = 0.45
                elif w_group == "staff": block_pct = 0.4
                elif w_group in ["bow", "crossbow", "book"]: block_pct = 0.2
            
            # KIRVES: GUARD CRUSH - puolittaa blokin tehon ja repii
            # blokkaajan staminaa (kirveen identiteetti: raivopää joka
            # murtaa kilpimuurit; systems/weapon_feel.py)
            _atk_w = None
            if attacker is not None and hasattr(attacker, "equipment"):
                _atk_w = attacker.equipment.get("main_hand")
            if getattr(_atk_w, "weapon_group", "") == "axe":
                from systems import weapon_feel as _wf
                block_pct *= _wf.GUARD_CRUSH_BLOCK_CUT
                self.current_stamina = max(
                    0, self.current_stamina - _wf.GUARD_CRUSH_STAMINA)
                if manager:
                    manager.vfx.show_damage(self.rect.centerx,
                                            self.rect.top - 45,
                                            "GUARD CRUSH!",
                                            color=(255, 150, 80))

            base_cost = max(2, float(amount) - (self.strength * 0.4))
            
            # Aseella torjuminen vie enemmän staminaa (2.5x)
            cost_mult = float(self.block_stamina_mult)
            if not is_shield:
                cost_mult *= 2.5
                
            actual_cost = base_cost * cost_mult
            
            if self.current_stamina >= actual_cost:
                self.current_stamina -= actual_cost
                
                # Vähennä vahinkoa
                blocked_amount = int(amount * block_pct)
                amount -= blocked_amount
                
                if manager:
                    txt = "BLOCKED" if is_shield else "PARRY"
                    if amount <= 0:
                        manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, txt)
                        return 0
                    else:
                        # Osittainen torjunta (näytetään harmaalla tekstillä)
                        manager.vfx.show_damage(self.rect.centerx, self.rect.top - 35, txt, color=(180, 180, 180))
            else:
                self.current_stamina = 0
                self.is_blocking = False
                if manager:
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30, "BREAK!")
                amount = int(amount * 0.5)

        # Passive shield block chance
        if offhand and str(getattr(offhand, "type", "")).lower() == "shield" and damage_type == "Physical":
            chance = float(getattr(offhand, "block_chance", 0.15))
            if attacker and getattr(attacker, "weapon_type", "") == "ranged":
                chance *= 2.0
            if random.random() < chance:
                if manager:
                    manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, "Block")
                return 0

        # Stoneform: -50% kaikesta vahingosta
        if self.stoneform_timer > 0:
            amount = int(amount * 0.5)

        # Tortle Shell Guard: -75% vahinko (mutta juurtunut, ei liiku)
        if getattr(self, 'shell_timer', 0) > 0:
            amount = int(amount * 0.25)

        # Warded/Barkskin (buff-loitsut): -30% vahinko
        if self.has_status("Warded"):
            amount = int(amount * 0.7)

        # Werewolf Bloodmoon Frenzy: hyokkaaja lyo kovempaa
        if attacker is not None and getattr(attacker, 'frenzy_timer', 0) > 0:
            amount = int(amount * 1.2)

        # Talentti: Thick Skin yms. luontainen vahingonvähennys
        dr = float(getattr(self, "damage_reduction", 0.0))
        if dr > 0:
            amount = int(amount * max(0.2, 1.0 - dr))

        final = max(1, int(amount) - int(self.defense))
        self.current_hp -= final
        self._break_invisibility(manager)  # Osuma paljastaa

        # Vahinko keskeyttää latautuvan loitsun (jos interruptible)
        if getattr(self, "active_cast", None) is not None:
            try:
                from spells import casting
                casting.on_caster_damaged(self)
            except Exception:
                pass

        # Werewolf Frenzy: hyokkaaja imee elamaa osuessaan
        if (attacker is not None and not getattr(attacker, 'is_dead', False)
                and getattr(attacker, 'frenzy_timer', 0) > 0):
            heal = max(1, int(final * 0.3))
            attacker.current_hp = min(attacker.max_hp, attacker.current_hp + heal)

        # --- HIT STUN & ANIMATION (Vasta kun vahinko on varma) ---
        # Vain jos ei immuniteettia
        if self.stun_immunity <= 0:
            stun_frames = 8 + int(final * 0.5) # Käytetään lopullista vahinkoa
            self.stun_timer = min(30, stun_frames) # Max 0.5s stun
            self.stun_immunity = 60 # 1 sekunnin suoja seuraavalta stunilta

        # --- CHARGE INTERRUPT / STAGGER ---
        # Melee-osuma keskeyttää aseen jännityksen/latauksen (esim. jousi):
        # lataus menetetään ja tulee tavallista pidempi horjahdus.
        # Steady Draw -skill estää tämän kokonaan.
        if (damage_type == "Physical" and attacker is not None
                and getattr(attacker, "weapon_type", "melee") == "melee"
                and self.is_charging and not self.has_steady_draw):
            w = self.equipment.get("main_hand")
            if w is not None:
                if getattr(w, "charge_time", 0) > 0:
                    w.charge_time = 0
                if getattr(w, "load_progress", 0) > 0:
                    w.load_progress = 0
            self.is_charging = False
            self.temp_speed_mult = 1.0
            self.stun_timer = max(self.stun_timer, 25) # Stagger ohittaa stun-immuniteetin
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 35,
                                        "STAGGERED!", color=(255, 160, 60))

        # Asetetaan osumaanimaatio
        self.animation_state = "hurt"
        self.animation_timer = 12
        
        played_custom = False
        if self.race_name == "Bog Leech":
            if random.random() < 0.5:
                played_custom = sound_system.play_sound(random.choice([f'leech_hurt_{i}' for i in range(1, 5)]))
        elif self.race_name == "Giant Frog":
            if random.random() < 0.5:
                played_custom = sound_system.play_sound(random.choice([f'frog_hurt_{i}' for i in range(1, 5)]))
        
        if not played_custom:
            sound_system.play_sound("hit")

        if manager:
            manager.vfx.show_damage(self.rect.centerx, self.rect.top, int(final), is_crit=False)

        if attacker and attacker != self:
            self.attackers.add(attacker)

        if self.current_hp <= 0:
            # Druidin muoto murtuu ennen kuolemaa: druid palaa entry-HP:hen
            # (muoto ei kestä kuolemaan asti - mana ja muodon HP ovat rajat)
            if getattr(self, "shapeshift_form", None):
                try:
                    from spells.druid import shapeshift
                    shapeshift.exit_form(self, manager, broken=True)
                    return final
                except Exception:
                    pass
            self.current_hp = 0
            self.is_dead = True
            if attacker:
                # Tapon kirjaus keskitetysti: myös nuolet, loitsut ja muut
                # epäsuorat osumat krediittaavat (raidipalkkiot, areena-XP).
                # perform_attack EI enää kirjaa erikseen (tuplakirjauksen esto).
                if attacker != self and hasattr(attacker, "stats"):
                    attacker.stats["kills"] = attacker.stats.get("kills", 0) + 1
                for helper in self.attackers:
                    if helper != attacker and not helper.is_dead:
                        helper.stats["assists"] += 1
        
        # Second Wind: Heal once when low
        if self.has_second_wind and not self.second_wind_triggered and not self.is_dead:
            if self.current_hp < self.max_hp * 0.30:
                self.second_wind_triggered = True
                self.heal(20, manager)
                if manager: manager.vfx.show_damage(self.rect.centerx, self.rect.top - 40, "Second Wind!", color=(50, 255, 50))

        return final

    # =========================================================
    # UPDATE & AOE
    # =========================================================
    def _follow_team_order(self, order_type, all_units, obstacles, manager):
        """Commanderin huudon toteutus: 'rally' = ryhmity komentajan luo,
        'charge' = sprinttaa lähimmän vihollisen kimppuun. Palauttaa True
        jos käsky ohjasi tätä framea (normaali AI ohitetaan)."""
        ai = self.ai_controller
        pc = getattr(manager, "player_character", None)
        if ai is None or not hasattr(ai, "_move_towards"):
            return False

        if order_type == "rally":
            if pc is None:
                return False
            dx = pc.rect.centerx - self.rect.centerx
            dy = pc.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 110:
                self.set_sprinting(self.current_stamina > 10)
                ai._move_towards(dx, dy, dist, obstacles, all_units, manager)
            else:
                self.set_sprinting(False)
                self.animation_state = "idle"
            return True

        if order_type == "charge":
            enemy = None
            best = 1e9
            for u in all_units:
                if u is self or getattr(u, "is_dead", True):
                    continue
                if getattr(u, "is_structure", False):
                    continue
                if u.team_color == self.team_color:
                    continue
                d = math.hypot(u.rect.centerx - self.rect.centerx,
                               u.rect.centery - self.rect.centery)
                if d < best:
                    best, enemy = d, u
            if enemy is None:
                return False
            reach = max(60, int(getattr(self, "attack_range", 60)))
            if best > reach:
                self.set_sprinting(self.current_stamina > 10)
                dx = enemy.rect.centerx - self.rect.centerx
                dy = enemy.rect.centery - self.rect.centery
                ai._move_towards(dx, dy, best, obstacles, all_units, manager)
            else:
                self.set_sprinting(False)
                self.perform_attack(target=enemy, manager=manager)
            return True

        return False

    def run_combat_ai(self, all_units, obstacles=None, manager=None):
        if self.is_dead or self.stun_timer > 0:
            return

        # --- CHANNELING CHECK ---
        if self.is_channeling:
            return # Stop AI (movement & attacks) completely

        # --- AOE / UPDATE HOOK FOR ITEMS ---
        # This allows Aura Helms, Regenerating Armor, etc. to work properly per-frame.
        if manager:
            for slot, item in self.equipment.items():
                if item and hasattr(item, "on_update"):
                    item.on_update(self, all_units, manager)
        # -----------------------------------

        # --- COMMANDER SHOUT: tiimikäsky ohittaa normaalin AI:n hetkeksi ---
        if manager is not None and self.ai_controller and \
                int(getattr(manager, "team_order_timer", 0)) > 0:
            pc = getattr(manager, "player_character", None)
            if pc is not None and self is not pc and \
                    self.team_color == pc.team_color and \
                    self in getattr(manager, "my_team", ()):
                order = getattr(manager, "team_order", None) or {}
                if self._follow_team_order(order.get("type"), all_units,
                                           obstacles, manager):
                    return

        # --- RETKIKÄSKYT (pelitesti 21): retkikartoilla aktiivinen
        # kenttäkomento (follow/kite/defend) ohjaa retkeläisen liikettä;
        # "free" ja soveltumattomat tilanteet valuvat normaaliin AI:hin ---
        if manager is not None and self.ai_controller and \
                getattr(manager, "expedition_field_active", False) and \
                self in (getattr(manager, "expedition_party", None) or ()):
            from systems import expedition
            if expedition.follow_order(self, all_units, obstacles, manager):
                self.prevent_overlap(all_units)
                return

        if self.ai_controller:
            # HUOM: Ei except TypeError -fallbackia! Se piilotti aidot
            # TypeErrorit AI:n sisältä (esim. rikkinäinen create_arrow-kutsu)
            # ja ajoi AI:n uudelleen ilman manageria. Kaikki AI:t tukevat
            # manager-parametria.
            self.ai_controller.execute_ai(all_units, obstacles, manager)
        self.prevent_overlap(all_units)

    def update(self, obstacles=None, manager=None):
        if self.is_dead:
            if manager:
                self._death_timer += 1
                # Poistetaan kentältä 5 sekunnin kuluttua (300 framea)
                if self._death_timer > 300:
                    if self in manager.all_units:
                        manager.all_units.remove(self)
            return
        
        self._death_timer = 0 # Nollataan jos herää henkiin

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        for k in self.spell_cooldowns:
            if self.spell_cooldowns[k] > 0:
                self.spell_cooldowns[k] -= 1
        
        # --- DASH RECHARGE ---
        if self.current_dashes < self.max_dashes:
            self.dash_recharge_timer += 1
            if self.dash_recharge_timer >= self.dash_recharge_time:
                self.dash_recharge_timer = 0
                self.current_dashes += 1
                if manager: manager.vfx.show_damage(self.rect.centerx, self.rect.top - 20, "Dash Ready", color=(100, 255, 255))
        
        # --- STUN UPDATE ---
        if self.stun_timer > 0:
            self.stun_timer -= 1
            self.is_blocking = False # Ei voi torjua stunnattuna
            self.is_sprinting = False
            # Dashia ei tarvitse nollata, koska dashin aikana ei voi ottaa vahinkoa (stun)
        elif self.stun_immunity > 0:
            self.stun_immunity -= 1

        # --- ANIMATION STATE UPDATE ---
        if self.animation_timer > 0:
            self.animation_timer -= 1
        else:
            # Oletustila: idle
            self.animation_state = "idle"
            # Jos liikutaan (AI chase tai dash), tila on run
            if self.is_dashing or self.is_sprinting:
                self.animation_state = "run"
            elif self.ai_controller and getattr(self.ai_controller, "state", "idle") == "chase":
                self.animation_state = "run"

        # Reset channeling flag (VFX will set it again next frame if active)
        self.is_channeling = False
        # is_charging nollataan loopin lopussa, jotta regen-tarkistus ehtii nähdä sen

        if self.current_stamina <= 0:
            self.is_blocking = False
            self.is_sprinting = False

        # Parry-ikkunan laskuri (ks. set_blocking / take_damage)
        if self.is_blocking:
            self.block_timer += 1
        if getattr(self, "parry_cooldown", 0) > 0:
            self.parry_cooldown -= 1
        if getattr(self, "riposte_timer", 0) > 0:
            self.riposte_timer -= 1
        if getattr(self, "shield_bash_cd", 0) > 0:
            self.shield_bash_cd -= 1
        if getattr(self, "_exhaust_flash_cd", 0) > 0:
            self._exhaust_flash_cd -= 1

        can_regen = not (self.is_blocking or self.is_sprinting or self.is_dashing or self.is_charging) and self.stun_timer <= 0
        if can_regen:
            self.current_stamina += self.stamina_regen
        if self.current_mana < self.max_mana:
            self.current_mana += self.mana_regen

        # --- PASSIIVINEN HP-REGEN (pelitesti 22) ---
        # Haavat umpeutuvat itsestään kun ei ole otettu osumaa hetkeen
        # (take_damage asettaa hp_regen_delayn). Nopeus skaalautuu
        # max HP:hen: ~0.8 % / s -> täysi palautuminen n. 2 minuutissa.
        if getattr(self, "hp_regen_delay", 0) > 0:
            self.hp_regen_delay -= 1
        elif self.current_hp < self.max_hp and \
                not any(e.get("type") in ("Burn", "Poison")
                        for e in self.status_effects):
            # Palo/myrkky estää haavojen umpeutumisen (mm. trollitaktikka)
            rate = self.max_hp * 0.008 / 60.0 + getattr(self, "hp_regen", 0.0)
            self._hp_regen_pool = getattr(self, "_hp_regen_pool", 0.0) + rate
            if self._hp_regen_pool >= 1.0:
                whole = int(self._hp_regen_pool)
                self._hp_regen_pool -= whole
                self.current_hp = min(self.max_hp, self.current_hp + whole)

        # --- RACIAL TIMERS ---
        if self.racial_cooldown > 0: self.racial_cooldown -= 1
        if getattr(self, "current_strain", 0.0) > 0:
            self.current_strain = max(0.0, self.current_strain - getattr(self, "strain_regen", 0.15))
        if self.stoneform_timer > 0: self.stoneform_timer -= 1
        if self.speed_buff_timer > 0: self.speed_buff_timer -= 1
        if getattr(self, 'frenzy_timer', 0) > 0: self.frenzy_timer -= 1
        if getattr(self, 'shell_timer', 0) > 0: self.shell_timer -= 1
        if self.reveal_timer > 0:
            self.reveal_timer -= 1
            if self.reveal_timer <= 0:
                self.revealed = False
        if self.is_invisible:
            self.invis_timer -= 1
            if self.invis_timer <= 0:
                self._break_invisibility()
            elif self.image:
                try: self.image.set_alpha(70 if not self.revealed else 150)
                except Exception: pass

        current_speed = self.walk_speed
        if self.is_invisible: current_speed *= 1.3   # Shadowstep
        if self.speed_buff_timer > 0: current_speed *= 1.4  # Wind Dance
        if getattr(self, 'frenzy_timer', 0) > 0: current_speed *= 1.35  # Werewolf Frenzy
        if getattr(self, 'shell_timer', 0) > 0: current_speed = 0.0     # Tortle Shell (root)
        if self.is_dashing:
            current_speed = self.walk_speed * self.dash_speed_mult
            move_x = self.dash_vector[0] * current_speed
            move_y = self.dash_vector[1] * current_speed
            self.check_wall_collision(move_x, move_y, obstacles)
            self.dash_timer -= 1

            # GAME FEEL: dash-vana (kipinäjälki joka toisella framella)
            if manager and self.dash_timer % 2 == 0:
                try:
                    manager.vfx.create_impact_sparks(
                        self.rect.centerx, self.rect.centery,
                        color=(170, 210, 255), count=3)
                except Exception:
                    pass
            
            # --- DASH DAMAGE CHECK ---
            if self.dash_damage > 0 and manager:
                for u in manager.all_units:
                    if u != self and u.team_color != self.team_color and not u.is_dead:
                        # Tarkistetaan ettei ole jo osuttu tällä syöksyllä
                        # Käytetään hurt_rect jos on, muuten rect (Props)
                        hr = getattr(u, "hurt_rect", u.rect)
                        if u not in self.dash_hit_list and self.rect.colliderect(hr):
                            u.take_damage(self.dash_damage, "Physical", self, manager)
                            manager.vfx.create_impact_sparks(u.rect.centerx, u.rect.centery, color=(200, 200, 200))
                            self.dash_hit_list.append(u) # Merkitään osutuksi
            
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.dash_damage = 0 # Varmistetaan nollaus
            self.current_stamina = min(self.current_stamina, self.max_stamina)
            return
        
        elif self.stun_timer > 0:
            current_speed = 0 # Ei liiku stunnattuna
            
        elif self.is_sprinting:
            if self.current_stamina > 0.5:
                current_speed *= 1.6
                self.current_stamina -= 0.3
            else:
                self.is_sprinting = False
        elif self.is_blocking:
            # GAME FEEL: blockaus ei saa tuntua liimalta - 0.5 -> 0.65
            current_speed *= 0.65

        # Apply temporary modifier (Weapon charge etc.)
        current_speed *= self.temp_speed_mult
        self.temp_speed_mult = 1.0 # Reset for next frame

        # GAME FEEL / TASAPAINO: laukauksen jälkeinen jalkatyö - ampuja
        # hidastuu kunnes puolet cooldownista on kulunut. Antaa meleelle
        # mahdollisuuden kuroa kitettäjää (ilman tätä samaa vauhtia
        # perääntyvä kirja/jousi voitti KAIKKI melee-matsit) ja tekee
        # ampumisesta painavan tuntuista myös pelaajalle.
        if self.weapon_type == "ranged" and \
                self.attack_cooldown > self.attack_speed * 0.5:
            current_speed *= 0.55

        # Web/Slow-status hidastaa liikettä (esim. hämähäkin verkko)
        if any(e.get("type") in ("Web", "Slow") for e in self.status_effects):
            current_speed *= 0.5

        # Salli täysi pysähdys (esim. lataus tai stun), muuten pidä miniminopeus
        if current_speed < 0.05:
            self.speed = 0.0
        else:
            self.speed = max(0.3, current_speed)
            
        self.current_stamina = max(0, min(self.current_stamina, self.max_stamina))

        self.is_charging = False # Reset for next frame

        # Latautuva loitsu: edistä castia (valmistuessaan laukaisee efektin)
        if self.active_cast is not None:
            try:
                from spells import casting
                casting.tick_caster(self, manager)
            except Exception:
                self.active_cast = None

        # Druidin muodonmuutos: manan kulutus + cooldownin lasku
        if getattr(self, "shapeshift_form", None) is not None \
                or int(getattr(self, "shapeshift_cooldown", 0)) > 0:
            try:
                from spells.druid import shapeshift
                shapeshift.tick(self, manager)
            except Exception:
                pass

        # Status effects
        for effect in self.status_effects[:]:
            effect["timer"] -= 1
            if effect["type"] == "Burn" and effect["timer"] % 60 == 0:
                self.take_damage(effect["dmg"], "Fire", manager=manager)
            elif effect["type"] == "Poison" and effect["timer"] % 60 == 0:
                self.take_damage(effect["dmg"], "Poison", manager=manager)
            elif effect["type"] == "Regen" and effect["timer"] % 60 == 0:
                # Druidin Regrowth: parannus joka sekunti (heal-over-time)
                self.heal(effect["dmg"], manager=manager)
            if effect["timer"] <= 0:
                self.status_effects.remove(effect)

        if obstacles:
            self._handle_obstacles_passive(obstacles)
            self._resolve_stuck_state(obstacles, manager)

        if self._level_up_timer > 0:
            self._level_up_timer -= 1
            if self._level_up_timer <= 0:
                self.just_leveled_up = False

        # --- FAILSAFE: MAP BOUNDARIES ---
        # Varmistetaan, ettei hahmo ole ajautunut seinien läpi kartan ulkopuolelle.
        if manager and getattr(manager, "current_arena", None):
            arena = manager.current_arena
            # Käytetään pientä marginaalia (esim. 5px) seinän sisäpuolella
            margin = 5
            
            # Haetaan mitat turvallisesti (fallback SCREEN_WIDTH/HEIGHT)
            aw = getattr(arena, "width", SCREEN_WIDTH)
            ah = getattr(arena, "height", SCREEN_HEIGHT)
            
            if self.rect.left < margin: self.rect.left = margin
            if self.rect.right > aw - margin: self.rect.right = aw - margin
            if self.rect.top < margin: self.rect.top = margin
            if self.rect.bottom > ah - margin: self.rect.bottom = ah - margin

    # --- SUB-PIXEL STEP HELPERS ---
    def _step_from_float(self, v: float):
        if v > 0:
            step = math.floor(v)
        elif v < 0:
            step = math.ceil(v)
        else:
            step = 0
        return int(step), (v - step)

    def check_wall_collision(self, dx, dy, obstacles):
        dx_total = dx + self._move_rem_x
        dy_total = dy + self._move_rem_y

        step_x, self._move_rem_x = self._step_from_float(dx_total)
        step_y, self._move_rem_y = self._step_from_float(dy_total)

        if not obstacles:
            self.rect.x += step_x
            self.rect.y += step_y
            return

        nearby = self._nearby_obstacles(obstacles)

        # X axis
        self.rect.x += step_x
        for r, t in nearby:
            if (t is None or t in ["wall", "water"]) and self.rect.colliderect(r):
                if step_x > 0:
                    self.rect.right = r.left
                elif step_x < 0:
                    self.rect.left = r.right

        # Y axis
        self.rect.y += step_y
        for r, t in nearby:
            if (t is None or t in ["wall", "water"]) and self.rect.colliderect(r):
                if step_y > 0:
                    self.rect.bottom = r.top
                elif step_y < 0:
                    self.rect.top = r.bottom

    def _handle_obstacles_passive(self, obstacles):
        for r, t in self._nearby_obstacles(obstacles, pad=20):
            if t and self.rect.colliderect(r):
                if t == "mud":
                    if not getattr(self, "mud_immune", False):
                        self.speed = self.walk_speed * 0.5
                elif t == "lava":
                    self.take_damage(1, "Fire")

    def _resolve_stuck_state(self, obstacles, manager):
        """Työntää hahmon pois seinien sisältä tai kartan ulkopuolelta."""
        # 1. Map Boundaries (Työnnä kartalle jos ulkona)
        if manager and getattr(manager, "current_arena", None):
            arena = manager.current_arena
            aw = getattr(arena, "width", 2000)
            ah = getattr(arena, "height", 2000)
            force = 4.0
            if self.rect.left < 0: self.rect.x += force
            if self.rect.right > aw: self.rect.x -= force
            if self.rect.top < 0: self.rect.y += force
            if self.rect.bottom > ah: self.rect.y -= force

        # 2. Obstacle Collision (Työnnä ulos seinistä)
        if not obstacles: return
        
        for r, t in self._nearby_obstacles(obstacles, pad=20):
            if (t is None or t == "wall") and self.rect.colliderect(r):
                # Oletus: Työnnä poispäin esteen keskipisteestä
                dx = self.rect.centerx - r.centerx
                dy = self.rect.centery - r.centery
                
                # Jos ollaan ihan keskellä, arvotaan suunta
                if abs(dx) < 1 and abs(dy) < 1: dx, dy = 1, 0
                
                dist = math.hypot(dx, dy) or 1
                push = 3.0
                self.rect.x += (dx / dist) * push
                self.rect.y += (dy / dist) * push

    def _iter_obstacles(self, obs):
        if isinstance(obs, pygame.sprite.AbstractGroup):
            for s in obs.sprites():
                r = getattr(s, "rect", None)
                if r:
                    yield r, getattr(s, "type", None)
            return
        if hasattr(obs, "rect"):
            yield obs.rect, getattr(obs, "type", None)
            return
        if isinstance(obs, (list, tuple)):
            for o in obs:
                if isinstance(o, pygame.Rect):
                    yield o, None
                else:
                    r = getattr(o, "rect", None)
                    if r:
                        yield r, getattr(o, "type", None)

    def _nearby_obstacles(self, obs, pad=100):
        """
        Palauttaa vain yksikön lähellä olevat esteet [(rect, type), ...].
        Estelistan purku välimuistitetaan (esteet ovat staattisia), koska
        koko listan läpikäynti joka yksikölle joka frame oli kaupungissa
        selvästi suurin yksittäinen suorituskykysyöppö.
        """
        if not obs:
            return ()
        key = id(obs)
        n = len(obs) if hasattr(obs, "__len__") else -1
        cached = _OBSTACLE_PAIRS_CACHE.get(key)
        if cached is not None and cached[0] == n:
            pairs = cached[1]
        else:
            pairs = list(self._iter_obstacles(obs))
            if len(_OBSTACLE_PAIRS_CACHE) > 32:
                _OBSTACLE_PAIRS_CACHE.clear()
            _OBSTACLE_PAIRS_CACHE[key] = (n, pairs)

        ux, uy = self.rect.centerx, self.rect.centery
        out = []
        for pair in pairs:
            r = pair[0]
            if abs(r.centerx - ux) > (r.w >> 1) + pad: continue
            if abs(r.centery - uy) > (r.h >> 1) + pad: continue
            out.append(pair)
        return out

    # --- AI HELPERS ---
    def try_cast_spells(self, t, all_units, manager=None):
        if not manager:
            return False

        if self.has_status("Silence"):
            return False

        # --- MANAN HALLINTA ---
        # 1. Jos parannusloitsu on varusteissa ja joku tiimissä on pahasti
        #    haavoittunut, castataan parannus ENSIN slottijärjestyksestä
        #    riippumatta.
        # 2. Jos parannus on varusteissa ja itse ollaan alle 70% HP,
        #    varataan sen mana: halvempia damage-loitsuja ei spämmätä
        #    manan loppuun.
        heal_slots = []
        offensive_slots = []
        for slot in ["spell1", "spell2", "spell3"]:
            spell = self.equipment.get(slot)
            if not spell:
                continue
            if getattr(spell, "is_heal", False) or "heal" in str(getattr(spell, "name", "")).lower():
                heal_slots.append(slot)
            else:
                offensive_slots.append(slot)

        reserve_mana = 0
        heal_needed = False
        if heal_slots:
            cheapest_heal = min(int(getattr(self.equipment[s], "mana_cost", 0)) for s in heal_slots)
            hurt_pct = self.current_hp / max(1, self.max_hp)
            ally_hurt = any(
                u.team_color == self.team_color and not u.is_dead
                and u.current_hp < u.max_hp * 0.6
                for u in all_units)
            heal_needed = hurt_pct < 0.6 or ally_hurt
            if hurt_pct < 0.7 or ally_hurt:
                reserve_mana = cheapest_heal

        slot_order = (heal_slots + offensive_slots) if heal_needed else (offensive_slots + heal_slots)

        for slot in slot_order:
            idx = self._slot_index_from_name(slot)
            if not self._has_spell_slot(idx):
                continue

            spell = self.equipment.get(slot)
            if not spell:
                continue

            req_tier = self._spell_tier_from_item(spell)
            if self.max_spell_tier <= 0 or req_tier > self.max_spell_tier:
                continue

            # Tarkistetaan resurssit ensin
            cost = getattr(spell, "mana_cost", 0)
            if self.current_mana < cost or self.spell_cooldowns.get(slot, 0) > 0:
                continue
            # Arcane strain: liian uupunut ei voi loitsia
            strain_cost = float(getattr(spell, "strain", 0))
            if getattr(self, "current_strain", 0.0) + strain_cost > getattr(self, "max_strain", 9999):
                continue
            # Mana-varaus: älä polta parannukseen tarvittavaa manaa
            # damage-loitsuun
            if slot not in heal_slots and reserve_mana > 0:
                if self.current_mana - cost < reserve_mana:
                    continue

            rng = float(getattr(spell, "range", 0))
            real_target = t
            target_pos = t.rect.center
            spell_name = str(getattr(spell, "name", "")).lower()

            # --- HEALING LOGIC ---
            # Jos loitsu on parannus, etsitään haavoittunut kaveri
            if getattr(spell, "is_heal", False) or "heal" in spell_name:
                best_ally = None
                lowest_pct = 1.0
                
                for u in all_units:
                    if u.team_color == self.team_color and not u.is_dead:
                        d = math.hypot(u.rect.centerx - self.rect.centerx, u.rect.centery - self.rect.centery)
                        if d <= rng:
                            pct = u.current_hp / u.max_hp
                            if pct < 1.0 and pct < lowest_pct:
                                lowest_pct = pct
                                best_ally = u
                                target_pos = u.rect.center
                
                if not best_ally: continue # Ei ketään parannettavaa
                real_target = best_ally
            
            # --- OFFENSIVE LOGIC ---
            elif math.hypot(t.rect.centerx - self.rect.centerx, t.rect.centery - self.rect.centery) > rng:
                continue # Vihollinen liian kaukana

            # Try casting with target_pos (New System) or fallback (Old System)
            try:
                success = spell.cast(self, real_target, manager, target_pos=target_pos)
            except TypeError:
                success = spell.cast(self, real_target, manager)

            if success:
                self.spell_cooldowns[slot] = int(getattr(spell, "cooldown_max", 60))
                self.current_strain = min(getattr(self, "max_strain", 9999),
                                          getattr(self, "current_strain", 0.0)
                                          + float(getattr(spell, "strain", 0)))
                self._break_invisibility(manager)  # Loitsu paljastaa
                return True
        return False

    def prevent_overlap(self, all_units):
        hits = pygame.sprite.spritecollide(self, all_units, False)
        for other in hits:
            if other != self and not other.is_dead:
                dx = self.rect.centerx - other.rect.centerx
                dy = self.rect.centery - other.rect.centery
                dist = math.hypot(dx, dy)
                if 0 < dist < 20:
                    self.rect.x += (dx / dist) * 2
                    self.rect.y += (dy / dist) * 2

    # --- PROGRESSION ---
    def add_xp(self, amount: int) -> bool:
        if self.level >= MAX_LEVEL:
            return False
        gained = max(0, int(round(amount * float(getattr(self, "xp_mult", 1.0)))))
        if gained <= 0:
            return False
        self.xp += gained
        old_level = int(self.level)
        new_level = min(MAX_LEVEL, int(level_from_xp(self.xp)))
        if new_level > old_level:
            for _ in range(old_level, new_level):
                self._on_level_up()
            self.level = new_level
            return True
        return False

    def _on_level_up(self):
        self.skill_points += 1
        self.just_leveled_up = True
        self._level_up_timer = 30

    def clear_level_up_flag(self):
        self.just_leveled_up = False
        self._level_up_timer = 0

    # =========================================================
    # RACIAL ABILITIES
    # =========================================================
    RACIAL_INFO = {
        "Goblin": ("Shadowstep", "Näkymättömyys + nopeus; toiminta tai osuma rikkoo"),
        "Dwarf": ("Stoneform", "-50% vahinko 4s; puhdistaa stunit ja efektit"),
        "Human": ("Adrenaline Rush", "Palauttaa staminaa ja hyökkäys heti valmis"),
        "Elf": ("Wind Dance", "+40% nopeus 4s ja syöksyt takaisin"),
        "Gnome": ("Spark Snare", "Kipinäansat lähelle: Slow + pieni Burn vihollisille"),
    }

    def get_racial_info(self):
        """Palauttaa (nimi, kuvaus) tai None jos rodulla ei ole kykyä."""
        return self.RACIAL_INFO.get(self.race_name)

    def use_racial_ability(self, manager=None):
        """Aktivoi rodun erikoiskyvyn. Palauttaa True jos aktivoitui."""
        if self.racial_cooldown > 0 or self.is_dead:
            return False
        race = self.race_name
        # Stun estää muut kyvyt paitsi Dwarfin Stoneformin, joka nimenomaan
        # puhdistaa stunin (hätäkyky).
        if self.stun_timer > 0 and race != "Dwarf":
            return False

        if race == "Goblin":
            # Kesto skaalautuu tasolla: 2s + 0.2s/lvl
            self.is_invisible = True
            self.revealed = False
            self.invis_timer = 120 + self.level * 12
            self.racial_cooldown = 1500  # 25s
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                        "*poof*", color=(160, 160, 200))
            return True

        if race == "Dwarf":
            self.stoneform_timer = 240  # 4s
            self.stun_timer = 0
            self.status_effects = [e for e in self.status_effects
                                   if e.get("type") not in ("Burn", "Bleed", "Poison", "Slow", "Web")]
            self.racial_cooldown = 1800  # 30s
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                        "STONEFORM!", color=(150, 150, 160))
            return True

        if race == "Human":
            self.current_stamina = min(self.max_stamina, self.current_stamina + 40)
            self.attack_cooldown = 0
            self.racial_cooldown = 1500
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                        "ADRENALINE!", color=(255, 220, 100))
            return True

        if race == "Elf":
            self.speed_buff_timer = 240  # 4s, +40% nopeus updatessa
            self.current_dashes = self.max_dashes
            self.dash_recharge_timer = 0
            self.racial_cooldown = 1500
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                        "WIND DANCE!", color=(150, 255, 200))
            return True

        if race == "Werewolf":
            # Bloodmoon Frenzy: 5s +nopeus, +vahinko ja elamanimu
            self.frenzy_timer = 300
            self.racial_cooldown = 1800  # 30s
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                        "BLOODMOON FRENZY!", color=(200, 40, 40))
            return True

        if race == "Gnome":
            # Spark Snare: levittää kipinäansat lähelle -> Slow + pieni Burn
            # vihollisiin (tinker/skirmisher-kontrolli). Toimii ilman manageria
            # (ei kohteita), jolloin vain cooldown kuluu.
            if manager is not None:
                cx, cy = self.rect.center
                for u in list(getattr(manager, "all_units", []) or []):
                    if getattr(u, "is_dead", False) or u is self:
                        continue
                    if getattr(u, "team_color", None) == self.team_color:
                        continue
                    if math.hypot(u.rect.centerx - cx, u.rect.centery - cy) < 140:
                        u.apply_status("Slow", 150)
                        u.apply_status("Burn", 90, 3)
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                        "SPARK SNARE!", color=(255, 200, 90))
            self.racial_cooldown = 1500  # 25s
            return True

        if race == "Tortle":
            # Shell Guard: 5s -75% vahinko, mutta juurtunut (ei liiku)
            self.shell_timer = 300
            self.stun_timer = 0
            self.racial_cooldown = 1800  # 30s
            if manager:
                manager.vfx.show_damage(self.rect.centerx, self.rect.top - 30,
                                        "SHELL GUARD!", color=(80, 160, 90))
            return True

        return False

    def _break_invisibility(self, manager=None):
        if self.is_invisible:
            self.is_invisible = False
            self.invis_timer = 0
            if self.image:
                try: self.image.set_alpha(255)
                except Exception: pass

    def reveal(self, duration=180):
        """See Invisibility -kyky paljastaa tämän yksikön kaikille."""
        self.revealed = True
        self.reveal_timer = max(self.reveal_timer, duration)

    def apply_status(self, type, duration, damage=0):
        self.status_effects.append({"type": type, "timer": duration, "dmg": damage})

    def has_status(self, type_name):
        for eff in self.status_effects:
            if eff["type"] == type_name:
                return True
        return False