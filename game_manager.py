# game_manager.py
import pygame
import random
import os
import math
from settings import *
from ui_kit import font_small, font_main, font_title, draw_text, draw_panel, UIButton, SpriteButton, GOLD_COLOR, GRAY, WHITE, draw_item_slot_background, draw_item_tooltip

# --- DATA ---
from mission_data import MONSTER_HUNTS, BOSS_HUNTS
from loot_data import LOOT_DROPS, BLUEPRINTS, NEW_GEAR_STATS
from races import RACES, get_random_name

# --- SYSTEMS ---
from leagues.league_engine import LeagueEngine
from sound_manager import sound_system
from vfx import VFXManager

# --- REGISTRIES ---
from items.item_registry import get_random_shop_items, create_item, get_available_item_classes
from arenas.arena_registry import get_random_arena, get_arena_for
from spells.spell_registry import get_spell_shop_items, get_all_spells_for_shop
from npc.npc_registry import get_npc_class
from missions.boss_registry import load_mission_package

# --- QUESTS ---
try:
    from quest_system import quest_manager
except ImportError:
    quest_manager = None
    print("Warning: Quest System could not be loaded in GameManager.")

# Tilat joissa quest journal -paneeli näytetään (J näyttää/piilottaa)
QUEST_JOURNAL_STATES = (
    "muckford_city", "mine_road", "mine_cave", "forest_excursion",
    "forest_road", "low_fields", "greywash_ford", "kingsreach_toll",
    "muckford_warrens", "drowned_chapel", "old_muckford_mine",
    "whisper_marsh",
)

# --- UNITS ---
from units.human import Human
from units.orc import Orc
from units.elf import Elf
from units.goblin import Goblin
from units.rat import GiantRat
from units.rat_rider import RatRider
from units.undead_skeleton import UndeadSkeleton
from units.undead_zombie import UndeadZombie
from units.undead_skeleton_archer import UndeadSkeletonArcher
from units.commander import Commander
from units.villager import Villager
from units.corrupted_crow import CorruptedCrow
from units.mnemonic_devourer import MnemonicDevourer

# --- CUSTOM ITEMS (New Paths) ---
from items.swords.rat_sword import RatPoisonSword
from items.bows.rat_bow import RatPoisonBow
from items.shields.rat_shield import RatKingShield
from items.staves.rat_staff import RatPoisonStaff
from items.tools.weak_pickaxe import WeakPickaxe
from items.tools.woodcutters_axe import WoodcuttersAxe
from items.swords.weak_sword import WeakSword
from items.axes.weak_axe import WeakAxe
from items.maces.weak_mace import WeakMace
from items.spears.weak_spear import WeakSpear
from items.daggers.weak_dagger import WeakDagger
from items.staves.weak_staff import WeakStaff
from items.books.weak_book import WeakBook
from items.crossbows.weak_crossbow import WeakCrossbow
from items.shields.weak_shield import WeakShield
from items.daggers.scrap_dagger import ScrapDagger
from items.swords.scrap_sword import ScrapSword
from items.axes.scrap_axe import ScrapAxe
from items.maces.scrap_mace import ScrapMace
from items.spears.scrap_spear import ScrapSpear
from items.bows.scrap_bow import ScrapBow
from items.crossbows.scrap_crossbow import ScrapCrossbow
from items.staves.scrap_staff import ScrapStaff
from items.books.scrap_book import ScrapBook
from items.shields.scrap_shield import ScrapShield
from assets.tiles.crypt_objects import SpiritEssence

# --- MENUS ---
from menus.chat_menu import ChatMenu
from npc.recruit_npc import RecruitNPC
from ai.base_ai import BaseAI
from ai.pathfinding import NavigationGrid

class GameManager:
    def __init__(self):
        # --- ECONOMY & SEASON ---
        self.gold = STARTING_GOLD
        
        # Synkataan mainepisteet heti alussa QuestManagerista
        self.reputation = quest_manager.reputation if quest_manager else 0
        
        # UUSI: Yksityiskohtainen maine-järjestelmä (Faction ID -> Score)
        self.reputations = {} 
        
        self.league_level = 1 
        self.season_wins = 0
        self.season_losses = 0
        self.matches_played = 0
        self.season_length = 5
        self.season_message = ""

        # --- LEAGUE SYSTEM ---
        self.league_engine = LeagueEngine()
        # Kronikka (all-time Hall of Fame) kirjoitetaan npc_stateen -> save.
        self.league_engine.manager = self

        # --- KYLÄTEHTÄVÄT (side-tasks) ---
        try:
            from systems.village_task_manager import VillageTaskManager
            self.village_tasks = VillageTaskManager()
        except Exception as e:
            print(f"Warning: VillageTaskManager failed to load: {e}")
            self.village_tasks = None

        # Tiimin seppä (sammakko-seppä liittynyt) -> varusteperkit
        self.has_smith = False
        self.current_enemy_team = None 
        self.match_mode = "1v1"

        # --- INVENTORY ---
        self.inventory = {}
        self.crafting_bag = self.inventory
        self.equipment_bag = []
        self.city_storage = {} # Kylän varastot (resurssit)
        self.loot_gained = {}
        self._known_materials = self._build_known_material_set()
        
        self.round_rewards = {'gold': 0, 'loot': {}, 'xp': 0}
        self.last_fighters = []

        # --- TEAMS ---
        self.my_team = pygame.sprite.Group()
        self.active_player_units = pygame.sprite.Group()
        self.enemy_team = pygame.sprite.Group()
        self.all_units = pygame.sprite.Group()

        # --- VFX SYSTEM ---
        self.vfx = VFXManager()

        # --- WORLD CLOCK & WEATHER ---
        from world_clock import WorldClock
        self.world_clock = WorldClock()
        # Koulutusjärjestelmä: gladiaattorit koulussa saavat statteja joka
        # pelipäivä (systems/training_school). Rekisteröidään day-listener.
        self.training_roster = []
        self.world_clock.day_listeners = [self._on_training_day]

        # --- INNKEEPER DEBT (alkutarina: yöt tajuttomana Sunk Caskissa) ---
        self.innkeeper_debt = 0
        # Barracksin taso (1-3): määrää punkkien määrän ja tiimin koon
        self.barracks_level = 1
        self.hire_block_message = ""
        # Arena Hallin aktiivinen veto: {"amount": SP} tai None (legacy)
        self.active_bet = None
        # Vedonlyöntitoimiston avoimet kupongit (systems/betting.py)
        self.open_bets = []
        # Viimeisin sijainti kaupungissa (save/load palauttaa tähän)
        self.last_city_pos = None
        # Kaivoksen avain: Marda antaa kun velka on maksettu
        self.mine_key_owned = False
        # Tier 0 -sponsorisopimus (SponsorMenu) + varastolahjoituslaskuri
        self.tier0_sponsor = None
        self.storage_donations = 0
        # Quest journal -paneeli pelinäkymässä (J tai klikkaus piilottaa)
        self.show_quest_journal = True
        self._journal_toggle_rect = None
        # Täysi RPG-questijournal (pelitesti 27): J avaa; välilehdet
        # MAIN/SIDE/COMPLETED, tehtävätiedot ja seurannan valinta
        self.show_full_journal = False
        self.journal_tab = "main"
        self.journal_selected = None
        self._journal_ui = {}
        # HUD-trackerin siirrettävä sijainti (None = oletus, oikea laita).
        # Pelaaja voi raahata paneelia; sijainti säilyy pelikertojen yli.
        try:
            from systems.ui_prefs import get_quest_tracker_pos
            self.journal_tracker_pos = get_quest_tracker_pos()
        except Exception:
            self.journal_tracker_pos = None
        self._journal_dragging = False
        self._journal_drag_off = (0, 0)
        self._journal_tracker_rect = None
        self._journal_drag_handle = None
        # Retkikunta (pelitesti 21): barracksin sotapöydältä koottu ryhmä,
        # aktiivinen kenttäkomento ja [T]-valikon tila. Rescue-data täytetään
        # kun Commander kaatuu retkellä (systems/expedition.py).
        self.expedition_party = []
        self.expedition_order = "follow"
        self.expedition_field_active = False
        self.tactics_menu_open = False
        self.pending_rescue = None

        # --- GAME STATE ---
        self.mode = "Arena" 
        self.selected_mission = None
        self.hunt_tier = 1
        self.match_in_progress = False
        self.match_over = False
        self.match_result = ""
        self.current_arena = None
        self.is_game_over = False
        self.current_mission_logic = None
        self.current_map_vfx = None
        self.camera_x = 0
        self.camera_y = 0
        self.screen_shake = 0
        self.hit_stop_timer = 0 # UUSI: Pysäyttää pelin hetkeksi osumissa
        self.loading_target_state = "hub" # Minne latausruutu vie
        self.pathfinder = None # UUSI: Reitinhaku
        
        # --- IN-GAME DIALOGUE ---
        self.active_dialogue = None # { "unit": unit, "text": "..." }
        self.dialogue_cooldown = 0
        self.active_escort = None # { "unit": unit, "target": prop }
        self.dialogue_scroll = 0
        self.pending_dialogue_menu = None
        # Valikko voi rekisteröidä oman action-käsittelijän (esim. Tavernan
        # give_scrap_dagger). Tuntemattomat actionit valuvat aina
        # _handle_dialogue_actionille.
        self.dialogue_action_handler = None
        self.is_in_dialogue = False # Estää HUDin piirtämisen overlay-dialogin aikana
        
        # --- NPC MEMORY ---
        self.npc_state = {
            "global": { "reputation": self.reputation, "flags": {}, "deeds": [] }
        }

        # --- HUB DATA ---
        self.recruit_options = []
        self.shop_items = []
        self.magic_shop_items = []
        self.battle_size = 3
        
        # --- PLAYER CHARACTER ---
        self.camera_locked = True # Lock camera to player character by default
        self.player_character = Commander()
        # Hotbarin sivu 2 (pikatyökalut) tarvitsee pääsyn reppuun
        self.player_character.manager_ref = self

        # Give tools for testing
        if CHEAT_MODE:
            self.equipment_bag.append(WeakPickaxe())
            self.equipment_bag.append(WoodcuttersAxe())
            
            # Add all weapons
            for cls in get_available_item_classes():
                try:
                    item = cls()
                    t = str(getattr(item, "type", "")).lower()
                    if "weapon" in t or "melee" in t or "ranged" in t or "shield" in t:
                        self.equipment_bag.append(item)
                except Exception:
                    pass

        # Alusta Hubin tiedot
        self.refresh_hub()

        # --- GLOBAL UI (Pause Menu) ---
        self.paused = False
        self.world_paused = False # Pysäyttää kaiken paitsi pelaajan
        self.pause_buttons = []
        self.ui_esc_bg = None
        self._init_pause_menu()
        
        # --- GLOBAL INVENTORY UI ---
        self.show_inventory = False
        
        # --- HUD SURFACE (Transparency support) ---
        self.hud_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    def _init_pause_menu(self):
        # Load Background
        try:
            path = "assets/ui/esc.png"
            if os.path.exists(path):
                self.ui_esc_bg = pygame.image.load(path).convert_alpha()
        except Exception: pass

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        
        # Napit (SpriteButton)
        # Oletetaan että kuvat ovat assets/ui/btn_resume_idle.png jne.
        # Jos ei löydy, SpriteButton käyttää fallback-piirtoa.
        
        self.btn_resume = SpriteButton(
            cx, 0, # Y asetetaan dynaamisesti piirrossa
            "assets/ui/btn_resume_idle.png", "assets/ui/btn_resume_hover.png", "assets/ui/btn_resume_pressed.png",
            "RESUME", target_width=250
        )
        
        self.btn_options = SpriteButton(
            cx, 0,
            "assets/ui/btn_options_idle.png", "assets/ui/btn_options_hover.png", "assets/ui/btn_options_pressed.png",
            "OPTIONS", target_width=250
        )
        
        self.btn_hub = SpriteButton(
            cx, 0,
            "assets/ui/btn_hub_idle.png", "assets/ui/btn_hub_hover.png", "assets/ui/btn_hub_pressed.png",
            "RETURN TO HUB", target_width=250
        )

        # BUGIKORJAUS: save-nappi lainasi OPTIONS-kuvia -> pausessa näkyi
        # kaksi "OPTIONS"-nappia. Omat kuvapolut (fallback piirtää tekstin
        # kunnes btn_save/btn_load -kuvat lisätään assetteihin).
        self.btn_save = SpriteButton(
            cx, 0,
            "assets/ui/btn_save_idle.png", "assets/ui/btn_save_hover.png", "assets/ui/btn_save_pressed.png",
            "SAVE GAME", target_width=250
        )

        self.btn_load = SpriteButton(
            cx, 0,
            "assets/ui/btn_load_idle.png", "assets/ui/btn_load_hover.png", "assets/ui/btn_load_pressed.png",
            "LOAD GAME", target_width=250
        )

        self.btn_exit = SpriteButton(
            cx, 0,
            "assets/ui/btn_exit_idle.png", "assets/ui/btn_exit_hover.png", "assets/ui/btn_exit_pressed.png",
            "EXIT GAME", target_width=250
        )

        self.pause_buttons = [self.btn_resume, self.btn_save, self.btn_load,
                              self.btn_options, self.btn_hub, self.btn_exit]
        self.save_feedback_msg = ""
        self.save_feedback_timer = 0

        # Save/Load-slottipaneeli pausen sisällä
        self.pause_panel_mode = None      # None | "save" | "load"
        self.pause_slot_rects = []        # (rect, slot_no)
        self.pause_name_slot = None       # slotti jota nimetään
        self.pause_name_buffer = ""

    # --- SAVE / LOAD ---
    def save_current_game(self):
        import save_manager
        ok = save_manager.save_game(self)
        self.save_feedback_msg = "Game Saved!" if ok else "Save Failed!"
        self.save_feedback_timer = 120  # ~2 sekuntia
        sound_system.play_sound('click' if ok else 'error')
        return ok

    def load_saved_game(self):
        import save_manager
        ok = save_manager.load_game(self)
        self.save_feedback_msg = "Game Loaded!" if ok else "No Save Found!"
        self.save_feedback_timer = 120
        sound_system.play_sound('click' if ok else 'error')
        return ok

    # --- HERO XP ---
    def grant_hero_xp(self, amount, x=None, y=None):
        """Antaa Commanderille XP:tä (esim. kaupungin töistä) ja näyttää sen.
        Palauttaa True jos hahmo nousi tason."""
        pc = self.player_character
        if not pc or amount <= 0:
            return False
        leveled = pc.add_xp(int(amount))
        px = x if x is not None else pc.rect.centerx
        py = y if y is not None else pc.rect.top
        self.vfx.show_damage(px, py - 30, f"+{int(amount)} XP", color=(190, 150, 255))
        if leveled:
            self.vfx.show_damage(pc.rect.centerx, pc.rect.top - 60, "LEVEL UP!", color=(255, 215, 0))
            sound_system.play_sound("win")
        return leveled

    # --- REPUTATION SYSTEM ---
    def _on_training_day(self):
        """Pelipäivän vaihtuessa: koulutuksessa olevat saavat statinsa."""
        try:
            from systems import training_school
            training_school.advance_day(self)
        except Exception:
            pass

    def get_faction_rep(self, faction_id):
        if faction_id == "global":
            return self.reputation
        return self.reputations.get(faction_id, 0)

    def modify_faction_rep(self, faction_id, amount):
        if faction_id not in self.reputations:
            self.reputations[faction_id] = 0
        self.reputations[faction_id] += int(amount)
        # Huom: self.reputation (Global Fame) voi olla summa näistä tai erillinen arvo

    # =========================================================
    # DEED MEMORY (kylä muistaa urotyöt)
    # =========================================================
    def record_deed(self, deed_id, text):
        """Merkitsee urotyön kylän muistiin. deed_id estää duplikaatit."""
        g = self.npc_state.setdefault("global", {})
        deeds = g.setdefault("deeds", [])
        if any(d.get("id") == deed_id for d in deeds):
            return False
        deeds.append({"id": deed_id, "text": text})
        return True

    def has_deed(self, deed_id):
        deeds = self.npc_state.get("global", {}).get("deeds", [])
        return any(d.get("id") == deed_id for d in deeds)

    def get_deeds(self):
        return list(self.npc_state.get("global", {}).get("deeds", []))

    def latest_deed_text(self):
        deeds = self.get_deeds()
        return deeds[-1]["text"] if deeds else None

    # =========================================================
    # VORTEX-TAIKUUS (heron pelottava signature-voima)
    # =========================================================
    def notice_vortex_use(self, source="combat"):
        """Kutsutaan kun hero paastaa valloilleen Vortex-taikuutta. Ensimmainen
        kaytto on iso lore-paljastus: kylalaiset pelastyvat ja kysymykset
        heraavat (NPC-dialogit reagoivat 'vortex_seen'-lippuun)."""
        g = self.npc_state.setdefault("global", {})
        first = not g.get("vortex_seen", False)
        g["vortex_seen"] = True
        g["vortex_uses"] = int(g.get("vortex_uses", 0)) + 1
        # Tuoreen pelon ajastin: kyla reagoi hetken voimakkaammin.
        g["vortex_fear_timer"] = 600
        if first:
            self.record_deed(
                "vortex_revealed",
                "unleashed the Vortex - a power the townsfolk fear to name")
            hero = getattr(self, "player_character", None)
            if hero is not None and getattr(self, "vfx", None):
                try:
                    self.vfx.show_damage(hero.rect.centerx, hero.rect.top - 60,
                                         "THE VORTEX STIRS", color=(150, 60, 220))
                except Exception:
                    pass
            if hasattr(self, "trigger_screen_shake"):
                try:
                    self.trigger_screen_shake(16)
                except Exception:
                    pass
        return first

    def has_seen_vortex(self):
        return bool(self.npc_state.get("global", {}).get("vortex_seen", False))

    def vortex_fear_active(self):
        """Tosi hetken ajan Vortexin kayton jalkeen (kyla viela peloissaan)."""
        return int(self.npc_state.get("global", {}).get("vortex_fear_timer", 0)) > 0

    def tick_vortex_fear(self):
        g = self.npc_state.get("global", {})
        if int(g.get("vortex_fear_timer", 0)) > 0:
            g["vortex_fear_timer"] = int(g["vortex_fear_timer"]) - 1

    # =========================================================
    # MAGIAN ETENEMINEN (koulukunnat + Abyssal-taitopuut)
    # =========================================================
    def _magic_state(self):
        g = self.npc_state.setdefault("global", {})
        m = g.setdefault("magic", {})
        m.setdefault("schools", [])
        m.setdefault("abyssal_trees", [])
        return m

    def is_school_unlocked(self, school):
        from magic.progression import SCHOOL_UNLOCK
        if CHEAT_MODE:
            return True
        if SCHOOL_UNLOCK.get(school, {}).get("default"):
            return True
        return school in self._magic_state()["schools"]

    def unlocked_schools(self):
        from magic.progression import SCHOOL_UNLOCK, default_schools
        if CHEAT_MODE:
            return list(SCHOOL_UNLOCK.keys())
        seen = list(default_schools())
        for s in self._magic_state()["schools"]:
            if s not in seen:
                seen.append(s)
        return seen

    def unlock_school(self, school):
        from magic.progression import SCHOOL_UNLOCK
        try:
            from magic.schools import SCHOOLS
            org = SCHOOLS.get(school, {}).get("org", school)
        except Exception:
            org = school
        st = self._magic_state()
        if school not in st["schools"] and not SCHOOL_UNLOCK.get(school, {}).get("default"):
            st["schools"].append(school)
            self.record_deed(f"school_{school}", f"was admitted to {org}")
            return True
        return False

    def can_unlock_school(self, school):
        from magic.progression import SCHOOL_UNLOCK
        req = SCHOOL_UNLOCK.get(school)
        if req is None:
            return False, "Unknown school"
        res = req.get("resource")
        if res and int(self.inventory.get(res[0], 0)) < res[1]:
            return False, f"Need {res[1]}x {res[0]}"
        return True, ""

    def try_unlock_school_with_resources(self, school):
        if self.is_school_unlocked(school):
            return True, "Already open"
        ok, reason = self.can_unlock_school(school)
        if not ok:
            return False, reason
        from magic.progression import SCHOOL_UNLOCK
        res = SCHOOL_UNLOCK.get(school, {}).get("resource")
        if res:
            self.inventory[res[0]] = int(self.inventory.get(res[0], 0)) - res[1]
        self.unlock_school(school)
        return True, "unlocked"

    def knows_abyssal_tree(self, tree):
        if CHEAT_MODE:
            return True
        return tree in self._magic_state().get("abyssal_trees", [])

    def learn_abyssal_tree(self, tree):
        st = self._magic_state()
        trees = st.setdefault("abyssal_trees", [])
        if tree not in trees:
            trees.append(tree)
            self.record_deed(f"abyssal_{tree}",
                             f"learned to see the other reality: the {tree} weave")
            return True
        return False

    # =========================================================
    # DIALOGUE SYSTEM
    # =========================================================
    def open_dialogue(self, npc_id: str):
        le = self.league_engine
        rank = le.get_player_rank()
        
        # Päivitetään reputaatio aina ennen dialogia
        if quest_manager:
            self.reputation = quest_manager.reputation
        
        if npc_id not in self.npc_state:
            self.npc_state[npc_id] = {"relationship": 0, "flags": {}, "history": []}
        if "global" not in self.npc_state:
             self.npc_state["global"] = {"reputation": self.reputation, "flags": {}}
        
        # Varmistetaan että globaali reputaatio on ajan tasalla
        self.npc_state["global"]["reputation"] = self.reputation

        my_roster = [u for u in self.all_units if getattr(u, "team_color", None) == PLAYER_TEAM]

        # Kerätään suoritetut tehtävät kontekstiin
        completed_ids = []
        if quest_manager:
            completed_ids = [q.id for q in quest_manager.quests.values() if q.completed]

        context = {
            "player": { "name": "Commander", "gold": self.gold },
            "memory": self.npc_state,
            "my_data": self.npc_state[npc_id],
            "global_data": self.npc_state["global"],
            "league_engine": le,
            "player_roster": my_roster,
            "league_tier": self._get_league_tier(),
            "league_rank": rank,
            "reputation": self.reputation,
            "completed_quests": completed_ids,
            "innkeeper_debt": int(getattr(self, "innkeeper_debt", 0)),
            "inventory": self.inventory,
        }
        # Griznakin kuulutukset: parvet ja bossit pitäjillä (pelitesti 23)
        try:
            from systems import griznak_caravan
            context["world_events"] = griznak_caravan.world_events(self)
        except Exception:
            context["world_events"] = []

        NPC_Class = get_npc_class(npc_id)
        if NPC_Class:
            menu = ChatMenu(self, NPC_Class(), context)
            
            # FIX: Nollataan taistelureaktio heti dialogin avaamisen jälkeen.
            # Tämä estää sen, että dialogi jäisi looppaamaan "häviö"-viestiä ikuisesti.
            if quest_manager and quest_manager.pending_reaction:
                quest_manager.clear_reaction()
                
            return menu
        else:
            print(f"Error: NPC ID '{npc_id}' not found.")
            return None

    def open_rival_dialogue(self, rival_info, return_state="muckford_city"):
        """Avaa asenteellisen dialogin rivaalitiimin gladiaattorin kanssa."""
        from npc.rival_gladiator_npc import RivalGladiatorNPC
        name, team, attitude = rival_info
        npc = RivalGladiatorNPC(name, team, attitude)
        if npc.npc_id not in self.npc_state:
            self.npc_state[npc.npc_id] = {"relationship": 0, "flags": {}, "history": []}
        context = {
            "player": {"name": "Commander", "gold": self.gold},
            "reputation": self.reputation,
            "my_data": self.npc_state[npc.npc_id],
        }
        menu = ChatMenu(self, npc, context, return_state=return_state)
        self.pending_dialogue_menu = menu
        return menu

    def open_roster_dialogue(self, unit, return_state="barracks"):
        """Avaa dialogin oman joukkueen jäsenen kanssa (Barracks).
        Dialogi muuttuu luonteen, suhteen ja urotöiden mukaan."""
        from npc.roster_npc import RosterNPC
        npc = RosterNPC(unit)
        # Varmista NPC-muisti (suhde säilyy yli dialogien ja tallennuksen)
        if npc.npc_id not in self.npc_state:
            self.npc_state[npc.npc_id] = {"relationship": 0, "flags": {}, "history": []}
        context = {
            "player": {"name": "Commander", "gold": self.gold},
            "reputation": self.reputation,
            "matches_played": self.matches_played,
            "my_data": self.npc_state[npc.npc_id],
            "unit": unit,
            "owned": True,
        }
        menu = ChatMenu(self, npc, context, return_state=return_state)
        self.pending_dialogue_menu = menu
        return menu

    def open_recruit_dialogue(self, unit, return_state="tavern_sunk_cask"):
        """Avaa dialogin tietyn rekrytoitavan yksikön kanssa.
        return_state: prospektit tavataan myös kaupungilla (muckford_city)."""
        npc = RecruitNPC(unit)

        context = {
            "player": { "name": "Commander", "gold": self.gold },
            "reputation": self.reputation,
            "matches_played": self.matches_played, # Lisätty tieto otteluista
            "unit": unit
        }

        menu = ChatMenu(self, npc, context, return_state=return_state)
        self.pending_dialogue_menu = menu
        return menu

    def open_patron_dialogue(self, unit, return_state="tavern_sunk_cask"):
        """Avaa dialogin satunnaisen tavernan asiakkaan kanssa."""
        from npc.tavern_patron_npc import TavernPatronNPC
        npc = TavernPatronNPC(unit)
        
        context = {
            "player": { "name": "Commander", "gold": self.gold },
            "reputation": self.reputation,
            "unit": unit
        }
        
        # Jos ollaan Muckfordissa, lisätään quest-tila contextiin
        # Tämä on hieman purkkaa, mutta toimii tässä rakenteessa
        # Etsitään MuckfordCityMenu valikoista (jos se on luotu)
        # Huom: main.py hallitsee menuja, manager ei suoraan omista niitä listana
        # Mutta voimme olettaa että jos olemme dialogissa, olemme oikeassa tilassa
        # Koska emme pääse helposti käsiksi menuun täältä, käytetään globaalia eventtiä tai
        # tallennetaan tila manageriin.
        
        # Yritetään hakea MuckfordCityMenu jos se on aktiivinen (tai tallennettu johonkin)
        # Koska emme pääse käsiksi 'menus'-sanakirjaan täältä, emme voi lukea tilaa suoraan.
        # Ratkaisu: MuckfordCityMenu päivittää tilan manageriin ennen dialogin avaamista.
        if hasattr(self, "manure_quest_status"):
            context["manure_quest_status"] = self.manure_quest_status
        
        menu = ChatMenu(self, npc, context, return_state=return_state)
        self.pending_dialogue_menu = menu
        return menu

    def open_bard_dialogue(self, unit):
        """Avaa dialogin Bardin kanssa."""
        from npc.bard_npc import BardNPC
        npc = BardNPC(unit)
        
        # Varmistetaan NPC-muisti
        if "bard" not in self.npc_state:
            self.npc_state["bard"] = {"relationship": 0, "flags": {}, "history": []}

        # Kerätään rikas konteksti (kuten DwarfManagerilla)
        le = self.league_engine
        rank = le.get_player_rank()
        completed_ids = []
        if quest_manager:
            completed_ids = [q.id for q in quest_manager.quests.values() if q.completed]

        context = {
            "player": { "name": "Commander", "gold": self.gold },
            "memory": self.npc_state,
            "my_data": self.npc_state["bard"],
            "league_engine": le,
            "league_rank": rank,
            "reputation": self.reputation,
            "completed_quests": completed_ids,
            "unit": unit
        }
        
        menu = ChatMenu(self, npc, context, return_state="tavern_sunk_cask")
        self.pending_dialogue_menu = menu
        return menu

   # =========================================================
    # BOSS HUNT SYSTEM
    # =========================================================
    def start_boss_hunt(self, boss_id, selected_fighters=None):
        if boss_id not in BOSS_HUNTS:
            print(f"Error: Unknown boss_id {boss_id}")
            return False
            
        self.mode = "Boss Hunt"
        self.selected_mission = BOSS_HUNTS[boss_id]
        
        mission_module = load_mission_package(boss_id)
        
        if mission_module:
            print(f"Starting Boss Hunt: {boss_id}...")
            
            self.loot_gained = {}
            self.round_rewards = {'gold': 0, 'loot': {}, 'xp': 0}
            self.all_units.empty()
            self.active_player_units.empty()
            self.enemy_team.empty()
            self.current_map_vfx = None
            self.current_mission_logic = None
            
            # --- TÄSSÄ MUUTOS: Käytä valittuja tai koko tiimiä ---
            fighters = selected_fighters if selected_fighters else list(self.my_team)
            
            for f in fighters:
                self.active_player_units.add(f)
                # Reset resources for boss hunt
                f.current_mana = f.max_mana
                f.current_stamina = f.max_stamina
                f.attack_cooldown = 0
                for k in f.spell_cooldowns: f.spell_cooldowns[k] = 0
                f.second_wind_triggered = False
                f.stats = {'damage': 0, 'healing': 0, 'kills': 0, 'assists': 0}
            
            self.last_fighters = list(self.active_player_units)
            # -----------------------------------------------------
            
            # --- MISSION SETUP ---
            self.mission_handles_positioning = False
            mission_module.setup(self)

            self.match_in_progress = True
            self.match_over = False
            self.match_result = ""

            # Mission voi lavastaa yksiköt itse (esim. Rat King valta-
            # istuimelleen, pelaajat viemärin suulle) - ei ylikirjoiteta
            if not getattr(self, "mission_handles_positioning", False):
                self._position_units(list(self.active_player_units),
                                     side="left")
                self._position_units(list(self.enemy_team), side="right")
            self.update_all_groups()
            
            # Alusta pathfinder
            if self.current_arena:
                self.pathfinder = NavigationGrid(self.current_arena)
            
            return True
        else:
            print(f"Critical Error: No mission script found for {boss_id}!")
            return False

    # =========================================================
    # STANDARD MATCH LOGIC
    # =========================================================
    def start_match(self, selected_units, battle_size_limit=None):
        self.loot_gained = {}
        self.round_rewards = {'gold': 0, 'loot': {}, 'xp': 0}
        self.match_in_progress = True
        self.match_over = False
        self.match_result = ""
        
        self.all_units.empty()
        self.enemy_team.empty()
        self.active_player_units.empty()
        self.pending_enemies = []
        self.spawn_timer = 0
        self.current_map_vfx = None
        self.current_mission_logic = None

        # BUGIKORJAUS: edellisen taistelun efektit (lentävät ammukset,
        # AoE-kyvyt, tekstit) vuotivat seuraavalle areenalle ja "isku
        # siirtyi toiseen mappiin". Tyhjennetään kaikki VFX-ryhmät.
        try:
            self.vfx.particles.empty()
            self.vfx.floor_particles.empty()
            self.vfx.texts.empty()
        except Exception:
            pass

        fighters = selected_units
        if battle_size_limit:
            fighters = selected_units[:battle_size_limit]
            self.battle_size = battle_size_limit
        else:
            self.battle_size = len(selected_units)

        self.last_fighters = list(fighters)

        # Sairaana/vammautuneena areenalle? Kuolemanriski lukitaan nyt
        # (pelitesti 18) ja realisoituu matsin jälkeen.
        try:
            from systems import conditions as _cond
            _cond.mark_prebattle_risks(self, fighters)
        except Exception:
            pass

        for f in fighters:
            if f:
                self.active_player_units.add(f)
                f.stats = {'damage': 0, 'healing': 0, 'kills': 0, 'assists': 0}
                
                # Reset resources
                f.current_mana = f.max_mana
                f.current_stamina = f.max_stamina
                f.attack_cooldown = 0
                for k in f.spell_cooldowns: f.spell_cooldowns[k] = 0
                f.second_wind_triggered = False
                
                try: f.attackers.clear()
                except Exception: pass

        if self.mode == "League":
            if self.current_enemy_team:
                enemy_units = self.current_enemy_team.get_roster(self.battle_size)
                for e in enemy_units:
                    if not e: continue
                    e.current_hp = e.max_hp
                    e.current_mana = e.max_mana
                    e.is_dead = False
                    try: e.kill()
                    except Exception: pass
                    self.enemy_team.add(e)
                if getattr(self, "match_mode", "") == "PROMOTION":
                    # Grand Slam -finaali pelataan aina isolla stadionilla
                    # (katsomot, best-of-3 -jujut). Kierros määrää twistin.
                    from arenas.tier_1.grand_slam_arena import GrandSlamArena
                    from systems.grand_slam_series import get_series
                    self.current_arena = GrandSlamArena()
                    self.current_arena.set_twist(
                        int(get_series(self).get("round", 1)))
                else:
                    self.current_arena = get_arena_for(
                        self._get_league_tier(),
                        getattr(self, "current_arena_location", None))
                # Rattlebridgen matseihin arvotaan kiertävä sponsoritavoite.
                try:
                    from systems.match_objectives import roll_match_objective
                    roll_match_objective(self)
                except Exception:
                    self.current_match_objective = None

        elif self.mode == "Arena":
            tier = 1 if self.league_level < 3 else 2
            self.current_arena = get_random_arena(tier)
            self.generate_random_enemy_team(len(fighters))

        elif self.mode == "Monster Hunt":
            if self.selected_mission:
                self.load_mission_data(self.selected_mission)
                
                # FIX: Poistetaan Commander jos tehtävä pakotti hänet mukaan, mutta pelaaja ei valinnut häntä
                if self.player_character and self.player_character not in fighters:
                    if self.player_character in self.active_player_units:
                        self.active_player_units.remove(self.player_character)
                    if self.player_character in self.all_units:
                        self.all_units.remove(self.player_character)
            else:
                self.end_match(False)
                return

        # Position units ONLY if the mission logic doesn't handle it itself
        if not (self.current_mission_logic and getattr(self.current_mission_logic, "handles_positioning", False)):
            self._position_units(fighters, side="left")
            self._position_units(list(self.enemy_team), side="right")
        
        for u in fighters:
            if u: self.all_units.add(u)
        for e in self.enemy_team:
            self.all_units.add(e)
            
        # Alusta pathfinder
        if self.current_arena:
            self.pathfinder = NavigationGrid(self.current_arena)

    def load_mission_data(self, mission):
        arena_name = mission.get('arena', 'Basic Arena')
        
        if arena_name == "Rat Sewer":
            import maps.rat_sewer.arena as rs_arena
            import maps.rat_sewer.mission as rs_mission
            import maps.rat_sewer.vfx as rs_vfx
            
            self.current_arena = rs_arena.Arena()
            self.current_mission_logic = rs_mission.MissionLogic(mission)
            self.current_map_vfx = rs_vfx.MapVFX()
            
            self.current_mission_logic.setup(self)
            self.pathfinder = NavigationGrid(self.current_arena)
            return

        if arena_name == "Crypt":
            import maps.crypt_1.arena as c_arena
            import maps.crypt_1.mission as c_mission
            import maps.crypt_1.vfx as c_vfx
            
            self.current_arena = c_arena.Arena()
            self.current_mission_logic = c_mission.MissionLogic(mission)
            self.current_map_vfx = c_vfx.MapVFX()
            
            self.current_mission_logic.setup(self)
            self.pathfinder = NavigationGrid(self.current_arena)
            return

        if arena_name == "Bog":
            import maps.bog_1.arena as b_arena
            import maps.bog_1.mission as b_mission
            import maps.bog_1.vfx as b_vfx
            
            self.current_arena = b_arena.Arena()
            self.current_mission_logic = b_mission.MissionLogic(mission)
            self.current_map_vfx = b_vfx.MapVFX()
            
            self.current_mission_logic.setup(self)
            self.pathfinder = NavigationGrid(self.current_arena)
            return

        if arena_name == "Muckford":
            import assets.tiles.arena as m_arena
            import assets.tiles.mission as m_mission
            import assets.tiles.vfx as m_vfx
            
            self.current_arena = m_arena.Arena()
            self.current_mission_logic = m_mission.MissionLogic(mission)
            self.current_map_vfx = m_vfx.MapVFX()
            self.current_mission_logic.setup(self)
            self.pathfinder = NavigationGrid(self.current_arena)
            return

        # Normaali Monster Hunt
        self.current_arena = get_random_arena(1)
        enemy_list = mission.get('enemies', [])
        for name, qty in enemy_list:
            for _ in range(qty):
                enemy = self.create_enemy_by_name(name)
                if enemy: self.enemy_team.add(enemy)
        self.pathfinder = NavigationGrid(self.current_arena)

    def create_enemy_by_name(self, name):
        # Tarkistetaan onko kyseessä Boss (Rat King)
        if name == "Rat King":
            from units.rat_king import RatKing
            # Etsitään bossin sijainti (keskellä)
            boss = RatKing("Rat King", 0, 0)
            boss.assign_manager(self)
            return boss

        if name in ("Troll", "Forest Troll"):
            from units.troll import Troll
            return Troll("Forest Troll", 0, 0)

        if name in ("Cave Broodmother", "Broodmother"):
            from units.cave_spider import CaveBroodmother
            return CaveBroodmother("Cave Broodmother", 0, 0)
        if name == "Spiderling":
            from units.cave_spider import Spiderling
            return Spiderling("Spiderling", 0, 0)

        if name in ("Hush-Mantle", "Hush Mantle"):
            from units.rattlebridge_threats import HushMantle
            return HushMantle("Hush-Mantle", 0, 0)
        if name == "Gutter Vermin":
            from units.rattlebridge_threats import GutterVermin
            return GutterVermin("Gutter Vermin", 0, 0)
        if name == "Red Lantern Cadaver":
            from units.rattlebridge_threats import RedLanternCadaver
            return RedLanternCadaver("Red Lantern Cadaver", 0, 0)

        RED = ENEMY_TEAM
        if name == 'Giant Rat': return GiantRat(name, 0, 0)
        if name == 'Rat Rider': return RatRider(name, 0, 0, RED)
        if name == 'Bandit': return Human("Bandit", 0, 0, RED, "Common")
        if name == 'Skeleton': return UndeadSkeleton("Skeleton", 0, 0, RED)
        if name == 'Zombie': return UndeadZombie("Zombie", 0, 0, RED)
        if name == 'Skeleton Archer': return UndeadSkeletonArcher("Archer", 0, 0, RED)
        if name == 'Corrupted Crow': return CorruptedCrow("Crow", 0, 0, RED)
        return Goblin("Minion", 0, 0, RED)

    def generate_random_enemy_team(self, count):
        available = [Human, Orc, Goblin]
        if self.league_level > 2: available.append(Elf)
        for i in range(count):
            EC = random.choice(available)
            if EC == Human: e = Human(f"Bandit {i+1}", 0, 0, RED, "Common")
            elif EC == Orc: e = Orc(f"Orc {i+1}", 0, 0, RED)
            elif EC == Elf: e = Elf(f"Ranger {i+1}", 0, 0, RED)
            else: e = Goblin(f"Gob {i+1}", 0, 0, RED)
            self.enemy_team.add(e)

    # =========================================================
    # GAME LOOP UPDATE
    # =========================================================
    def update_match(self):
        # Vortex-pelon vaimeneminen (kyla rauhoittuu vahitellen)
        self.tick_vortex_fear()
        # --- HIT STOP (Game Feel) ---
        if self.hit_stop_timer > 0:
            self.hit_stop_timer -= 1
            # Päivitetään vain tärinän vaimeneminen, ei muuta pelilogiikkaa
            if self.screen_shake > 0:
                self.screen_shake *= 0.9
                if self.screen_shake < 1: self.screen_shake = 0
            return

        # --- DIALOGUE PAUSE ---
        if self.active_dialogue:
            # Peli on pausella. Input käsitellään eventtipohjaisesti
            # handle_dialogue_event:issä (main loopin kautta).
            if self.dialogue_cooldown > 0:
                self.dialogue_cooldown -= 1
            return

        if not self.match_in_progress:
            return
            
        if self.dialogue_cooldown > 0:
            self.dialogue_cooldown -= 1

        if self.current_arena:
            self.current_arena.update(self.all_units)
        obs = self.current_arena.obstacles if self.current_arena else None

        # --- CAMERA UPDATE ---
        # Jos kamera on lukittu ja Commander on kentällä
        if self.camera_locked and self.player_character and not self.player_character.is_dead and self.player_character in self.all_units:
            # Keskitetään kamera Commanderiin
            target_x = self.player_character.rect.centerx - SCREEN_WIDTH // 2
            target_y = self.player_character.rect.centery - SCREEN_HEIGHT // 2
            
            # Smooth Follow (Lerp) - Pehmeämpi liike
            self.camera_x += (target_x - self.camera_x) * 0.15
            self.camera_y += (target_y - self.camera_y) * 0.15
        else:
            # Vapaa kamera (hiiren reunat)
            mx, my = pygame.mouse.get_pos()
            scroll_speed = 15
            margin = 50
            if mx < margin: self.camera_x -= scroll_speed
            elif mx > SCREEN_WIDTH - margin: self.camera_x += scroll_speed
            if my < margin: self.camera_y -= scroll_speed
            elif my > SCREEN_HEIGHT - margin: self.camera_y += scroll_speed
        
        # Clamp camera
        max_w = getattr(self.current_arena, 'width', SCREEN_WIDTH) if self.current_arena else SCREEN_WIDTH
        max_h = getattr(self.current_arena, 'height', SCREEN_HEIGHT) if self.current_arena else SCREEN_HEIGHT
        self.camera_x = max(0, min(self.camera_x, max_w - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, max_h - SCREEN_HEIGHT))

        # --- SCREEN SHAKE DECAY ---
        if self.screen_shake > 0:
            self.screen_shake *= 0.9 # Vaimenee 10% joka frame
            if self.screen_shake < 1: self.screen_shake = 0

        if self.current_mission_logic:
            self.current_mission_logic.update(self)
        
        if self.current_map_vfx:
            self.current_map_vfx.update(self)

        # --- PICKUP LOGIC & DEATH SPAWN ---
        # Tarkistetaan kuolleet viholliset loot-spawnia varten
        for u in self.enemy_team:
            if getattr(u, "is_dead", False) and not getattr(u, "loot_spawned", False):
                u.loot_spawned = True
                # Jos Undead ja Crypt-tehtävä -> 5% chance Spirit Essence
                if getattr(u, "race_name", "") == "Undead" and "Crypt" in str(self.selected_mission):
                    if random.random() < 0.15: # 15% (Nostettu jotta näkyy paremmin)
                        essence = SpiritEssence(u.rect.centerx, u.rect.centery)
                        self.all_units.add(essence) # Lisätään kentälle
                        self.vfx.create_impact_sparks(u.rect.centerx, u.rect.centery, color=(50, 255, 200), count=10)

        # Tarkistetaan keräykset (Commander osuu Essenceen)
        if self.player_character and not self.player_character.is_dead:
            # Etsitään SpiritEssence objektit all_units ryhmästä
            pickups = [s for s in self.all_units if isinstance(s, SpiritEssence)]
            hits = pygame.sprite.spritecollide(self.player_character, pickups, True) # True = kill sprite
            
            for p in hits:
                # Kerätty!
                sound_system.play_sound("recruit") # "Chime" ääni
                self.add_material("Spirit Essence", 1)
                self.vfx.show_damage(self.player_character.rect.centerx, self.player_character.rect.top - 40, "+1 Spirit Essence", color=(50, 255, 50))

        # Normal update
        for u in self.all_units:
            if self.world_paused and u != self.player_character:
                continue
            u.run_combat_ai(self.all_units, obs, manager=self)
            u.update(obs, manager=self)
        self.vfx.update(obstacles=obs)
        
        # Tarkistetaan pelin tila joka frame (eikä vain tärähdyksessä)
        self.check_match_status()
        
        # Escort Mission Update
        if self.active_escort:
            self._update_escort_mission()
            
            # Check for UI close click (X button)
            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                ui_w = 260
                x = 30
                y = 20
                close_rect = pygame.Rect(x + ui_w - 25, y + 5, 20, 20)
                if close_rect.collidepoint(mx, my):
                    self.stop_escort_mission()

    def check_match_status(self):
        if not self.match_in_progress: return

        enemies_alive = any(not getattr(u, "is_dead", False) for u in self.enemy_team)
        my_alive = any(not getattr(u, "is_dead", False) for u in self.active_player_units)

        mission_complete = True
        if self.current_mission_logic:
            mission_complete = self.current_mission_logic.is_finished(self)

        if not enemies_alive and mission_complete:
            self.end_match(True)
        elif not my_alive:
            self.end_match(False)

    def trigger_screen_shake(self, amount):
        self.screen_shake = max(self.screen_shake, amount)

    def trigger_hit_stop(self, frames):
        self.hit_stop_timer = frames

    def _dialogue_option_at(self, mx, my):
        """Palauttaa dialogivaihtoehdon annetuissa ruutukoordinaateissa tai None.
        Geometrian on vastattava _draw_dialogue_overlayn piirtoa."""
        if not self.active_dialogue:
            return None
        opts = self.active_dialogue.get("options")
        if not opts:
            return None
        box_w, box_h = 800, 200
        box_x = (SCREEN_WIDTH - box_w) // 2
        box_y = (SCREEN_HEIGHT - box_h) // 2
        view_y = box_y + 130
        view_h = 70
        oy = view_y - self.dialogue_scroll
        for opt in opts:
            if box_x + 220 <= mx <= box_x + 700 and oy <= my <= oy + 25 and view_y <= my <= view_y + view_h:
                return opt
            oy += 30
        return None

    def handle_dialogue_event(self, event):
        """Eventtipohjainen in-game dialogin ohjaus. Palauttaa True jos event käsiteltiin."""
        if not self.active_dialogue:
            return False

        if event.type == pygame.MOUSEWHEEL:
            self.handle_dialogue_scroll(event.y)
            return True

        # Aktiivinen valikko voi tarjota oman action-käsittelijän
        action_handler = self.dialogue_action_handler or self._handle_dialogue_action

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            opt = self._dialogue_option_at(*event.pos)
            if opt:
                action_handler(opt["action"])
            return True

        if event.type == pygame.KEYDOWN:
            opts = self.active_dialogue.get("options") or []
            number_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                           pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
            if event.key in number_keys:
                idx = number_keys.index(event.key)
                if idx < len(opts):
                    action_handler(opts[idx]["action"])
                return True
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_e):
                self.active_dialogue = None
                self.dialogue_cooldown = 20
                return True
            return True  # Muut näppäimet eivät tee mitään dialogin aikana

        # Kuluta muutkin hiiritapahtumat, ettei alla oleva valikko reagoi
        return event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION) and False

    def handle_dialogue_scroll(self, amount):
        if not self.active_dialogue: return
        opts = self.active_dialogue.get("options", [])
        if not opts: return
        
        total_h = len(opts) * 30
        view_h = 70 # 200 (box) - 130 (start y)
        max_scroll = max(0, total_h - view_h)
        
        self.dialogue_scroll -= amount * 10
        self.dialogue_scroll = max(0, min(self.dialogue_scroll, max_scroll))

    def start_dialogue(self, unit, text, options=None):
        """Avaa in-game dialogin ja pausaa pelin."""
        self.active_dialogue = {"unit": unit, "text": text, "options": options}
        self.dialogue_cooldown = 60 # Estä välitön sulkeutuminen (1 sekunti)
        self.dialogue_scroll = 0

    def _handle_dialogue_action(self, action):
        if action == "accept_escort":
            self.start_escort_mission(self.active_dialogue["unit"])
        elif action == "stop_escort":
            self.stop_escort_mission()
            
        # Smeltery actions
        elif action.startswith("smelter_"):
            target = self.active_dialogue["unit"]
            if hasattr(target, "handle_menu_action"):
                target.handle_menu_action(action, self)
                
        self.active_dialogue = None
        self.dialogue_cooldown = 20

    def start_escort_mission(self, unit):
        # Etsi talo
        houses = []
        if self.current_arena and hasattr(self.current_arena, "props"):
            for p in self.current_arena.props:
                if "House" in p.__class__.__name__:
                    houses.append(p)
        
        if not houses:
            print("No houses found for escort.")
            return

        target = random.choice(houses)
        self.active_escort = {
            "unit": unit,
            "target": target
        }
        unit.is_escorted = True
        if unit.ai_controller and hasattr(unit.ai_controller, "set_follow_target"):
            unit.ai_controller.set_follow_target(self.player_character)
        
        sound_system.play_sound("recruit")
        self.vfx.show_damage(unit.rect.centerx, unit.rect.top - 50, "ESCORT STARTED!", color=GOLD_COLOR)

    def _update_escort_mission(self):
        data = self.active_escort
        unit = data["unit"]
        target = data["target"]
        
        if unit.is_dead:
            self.vfx.show_damage(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, "MISSION FAILED", color=RED)
            self.active_escort = None
            return
            
        # Tarkista etäisyys taloon (Ovelle / Markerille)
        target_x = target.rect.centerx
        target_y = target.rect.bottom + 20
        
        dist = math.hypot(unit.rect.centerx - target_x, unit.rect.centery - target_y)
        if dist < 100: # Perillä (Tarkempi alue)
            self.gold += 150
            
            # --- REPUTATION REWARDS ---
            self.modify_faction_rep("shanty", 30)  # Consortium: "Safe streets for business."
            self.modify_faction_rep("lumen", 15)   # Temple: "A life saved from the plague."
            self.modify_faction_rep("mudhand", 5)  # Bram: "Less chaos on my turf."
            
            self.vfx.show_damage(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, "MISSION COMPLETE!", color=GOLD_COLOR)
            self.vfx.show_damage(unit.rect.centerx, unit.rect.top - 40, "Thank you!", color=WHITE)
            sound_system.play_sound("win")
            
            unit.kill() # Menee taloon
            self.active_escort = None

    def stop_escort_mission(self):
        if self.active_escort:
            unit = self.active_escort["unit"]
            unit.is_escorted = False
            
            if unit.ai_controller and hasattr(unit.ai_controller, "trigger_betrayal"):
                unit.ai_controller.trigger_betrayal(self.player_character)
                
            self.active_escort = None
            self.vfx.show_damage(unit.rect.centerx, unit.rect.top - 50, "Traitor!", color=RED)

    # --- QUEST EFFECTS (Called from Dialogue) ---
    def handle_dialogue_effect(self, effect):
        # Etsi aktiivinen menu (MuckfordCityMenu)
        # Tämä on hieman purkkaa, mutta toimii tässä rakenteessa
        # Oikeampi tapa olisi rekisteröidä callbackit
        
        # Etsitään MuckfordCityMenu valikoista (jos se on luotu)
        # Huom: main.py hallitsee menuja, manager ei suoraan omista niitä listana
        # Mutta voimme olettaa että jos olemme dialogissa, olemme oikeassa tilassa
        
        # Koska emme pääse helposti käsiksi menuun täältä, käytetään globaalia eventtiä tai
        # tallennetaan tila manageriin.
        # Yksinkertaisin: Jos effect on "accept_manure_quest", asetetaan lippu jota menu lukee.
        
        if effect == "accept_manure_quest":
            self.pending_quest_action = "accept_manure"
        elif effect == "finish_manure_quest":
            self.pending_quest_action = "finish_manure"
            
        # Välitä efekti aktiiviselle menulle (esim. ForestRoadMenu)
        # Tämä on hieman purkkaa, mutta toimii tässä rakenteessa
        # Etsitään aktiivinen menu (joka ei ole dialogue)
        # Koska emme pääse käsiksi 'menus' sanakirjaan täältä helposti,
        # oletamme että jos olemme ForestRoadMenussa, se on tallennettu johonkin tai
        # voimme käyttää globaalia eventtiä.
        # Mutta koska ForestRoadMenu on 'gameplay_screen', voimme yrittää kutsua sitä.
        # Parempi tapa: ChatMenu kutsuu tätä, ja ChatMenu tietää return_staten.
        # Mutta ChatMenu ei tiedä menun instanssia.
        
        # Yksinkertainen ratkaisu: Tallenna efekti manageriin ja anna menun lukea se update-loopissa.
        self.pending_dialogue_effect = effect
            
        # UUSI GENEERINEN QUEST SYSTEM TUKI
        if effect.startswith("accept_quest:"):
            qid = effect.split(":")[1]
            if quest_manager:
                quest_manager.accept_quest(qid)
                sound_system.play_sound('recruit')
                
        if effect.startswith("finish_quest:"):
            qid = effect.split(":")[1]
            if quest_manager:
                rewards = quest_manager.finish_quest(qid)
                if rewards:
                    if "gold" in rewards: 
                        self.gold += rewards["gold"]
                        self.vfx.show_damage(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, f"+{rewards['gold']} Gold", color=GOLD_COLOR)
                    sound_system.play_sound('coin')

    def end_match(self, win):
        self.match_in_progress = False
        self.match_over = True
        self.match_result = "VICTORY" if win else "DEFEAT"

        # Moraali: voitot nostavat, tappiot painavat koko tiimiä.
        # Drillmaster tuplaa voittobonuksen, Iron Presence puolittaa sakon.
        pc = self.player_character
        win_gain = 8 if getattr(pc, "drillmaster", 0) else 4
        loss_hit = -3 if getattr(pc, "iron_presence", 0) else -6
        for u in self.my_team:
            if hasattr(u, "adjust_morale"):
                u.adjust_morale(win_gain if win else loss_hit)

        # Sairaudet/vammat matsin jäljiltä (pelitesti 18): kaatuneet ja
        # kolhitut voivat vammautua; sairaana kentälle laitettu voi kuolla
        try:
            from systems import conditions as _cond
            _msgs = _cond.apply_battle_aftermath(
                self, list(getattr(self, "last_fighters", []) or []), win)
            if _msgs:
                self.hire_block_message = "  |  ".join(_msgs[:2])
                self._toast_timer = 420
        except Exception:
            pass

        # Tier 0 -sponsorin voittobonus (allekirjoitettu sopimus)
        if win and self.mode == "League" and \
                getattr(self, "tier0_sponsor", None):
            try:
                from sponsors.sponsor_data import SPONSORS
                _sp = SPONSORS.get(self.tier0_sponsor)
                if _sp:
                    bonus = 15
                    self.gold += bonus
                    self.hire_block_message = (
                        f"{_sp['name']} win bonus: +{bonus} SP")
                    self._toast_timer = 300
            except Exception:
                pass

        # Arena Hallin vedonlyönti ratkeaa liigamatsissa
        bet = getattr(self, "active_bet", None)
        if bet and self.mode == "League":
            from citys.mucford.city_interiors import BET_PAYOUT
            if win:
                payout = int(bet["amount"] * float(bet.get("mult",
                                                           BET_PAYOUT)))
                self.gold += payout
                self.hire_block_message = (f"Vint pays out your wager: "
                                           f"+{payout} SP!")
            else:
                self.hire_block_message = (f"Your {bet['amount']} SP wager "
                                           f"is lost to the Yard.")
            self._toast_timer = 300
            self.active_bet = None

        # Path of the Arena: XP tapoista + voitosta jos sankari taisteli
        try:
            from systems import commander_progression as _prog
            _prog.on_match_end(self, win)
        except Exception:
            pass

        if win:
            sound_system.play_sound('win')
            if self.mode in ["Monster Hunt", "Boss Hunt"] and self.selected_mission:
                # KORJAUS: Kutsutaan quest-tarkistusta
                self.check_quest_completion(self.selected_mission['id'])
        
        else:
            # HÄVIÖ: Ilmoita Quest Managerille (Griznakin kuittailua varten)
            if quest_manager:
                quest_manager.set_battle_result("loss")

        if self.mode == "League" and self.current_enemy_team:
            # --- CONSTRUCT MATCH STATS ---
            match_stats = {"fighters": []}
            
            # Player units
            for u in self.last_fighters:
                if u:
                    match_stats["fighters"].append({
                        "name": u.name,
                        "kills": u.stats.get("kills", 0)
                    })
            
            # Enemy units
            for u in self.enemy_team:
                match_stats["fighters"].append({
                    "name": u.name,
                    "kills": u.stats.get("kills", 0)
                })

            # HUOM: PROMOTION on best-of-3 -SARJA - yksittäistä kierrosta ei
            # raportoida enginelle (report_match_result promotoisi heti 1.
            # voitosta). Sarjan ratkaisu: systems/grand_slam_series.py.
            if getattr(self, "match_mode", "") != "PROMOTION":
                try:
                    self.league_engine.report_match_result(
                        mode=self.match_mode, player_win=win,
                        enemy_team=self.current_enemy_team,
                        match_stats=match_stats,
                        player_fighters=list(self.last_fighters),
                        enemy_units=list(self.enemy_team),
                    )
                except Exception: pass
            # Muiden parien taustamatsit ratkaistaan heti pelaajan matsin
            # päätteeksi (sama kierros etenee kaikilla samaan aikaan).
            try:
                self.league_engine.get_standings(self.match_mode)
            except Exception:
                pass

            # Vedonlyöntitoimiston kupongit ratkeavat kun kierros on
            # pelattu (oma matsi + simuloidut taustamatsit)
            try:
                from systems.betting import check_open_bets
                msgs = check_open_bets(self)
                if msgs:
                    self.hire_block_message = "  |  ".join(msgs[:2])
                    self._toast_timer = 420
            except Exception:
                pass

            # Rattlebridge sponsors settle on every Tier 1 league match.
            if getattr(self, "current_arena_location", None) == "rattlebridge":
                try:
                    from systems import sponsors
                    result = sponsors.build_match_result(win, list(self.last_fighters))
                    self.last_sponsor_settlement = sponsors.on_league_match_end(self, result)
                    # Erääntyneet kuukausistipendit (28 pv jakso) samalla.
                    sponsors.collect_due_stipends(self)
                except Exception:
                    self.last_sponsor_settlement = None
                # Sponsoritavoite arvioidaan settlementin jälkeen: esitys
                # rakentaa brändin (bonus + kärsivällisyys), muttei pelasta
                # jo katkennutta sopimusta.
                try:
                    from systems.match_objectives import evaluate_match_objective
                    evaluate_match_objective(self, win, list(self.last_fighters))
                except Exception:
                    self.last_objective_result = None

        self.calculate_rewards(win)
        self.loot_gained = dict(self.round_rewards.get("loot", {}))
        
        # PÄIVITÄ REPUTAATIO LOPUKSI (JOS SITÄ TULI LISÄÄ)
        if quest_manager:
            self.reputation = quest_manager.reputation

    # =========================================================
    # REWARDS
    # =========================================================
    def check_quest_completion(self, mission_id):
        """
        KORJATTU VERSIO: Ei käytä suoraa for-looppia, vaan kutsuu
        QuestManagerin älykästä hakumetodia.
        """
        if not quest_manager: return

        # 1. Kerro voitosta (NPC dialogia varten)
        quest_manager.set_battle_result("win")
        
        # 2. Etsi ja merkitse tehtävä valmiiksi
        completed_quest = quest_manager.complete_quest_by_boss(mission_id)
        
        if completed_quest:
            # 3. Jaa palkinnot
            rewards = completed_quest.rewards
            
            if "gold" in rewards:
                self.gold += rewards["gold"]
            if "xp" in rewards:
                for unit in self.my_team:
                    if hasattr(unit, "add_xp"): unit.add_xp(rewards["xp"])
            if "items" in rewards:
                for item_name, count in rewards["items"].items():
                    # Tarkistetaan onko kyseessä varuste vai materiaali
                    item_obj = self._create_loot_item(item_name)
                    if item_obj:
                        # Se on varuste -> Reppuun
                        self.equipment_bag.append(item_obj)
                        # Jos count > 1, luodaan loputkin
                        for _ in range(count - 1):
                            self.equipment_bag.append(self._create_loot_item(item_name))
                        print(f"*** QUEST REWARD: {item_name} added to Equipment Bag! ***")
                    else:
                        # Se on materiaali -> Inventaarioon
                        self.add_loot_name(item_name, count)

            if "reputation" in rewards:
                # QuestManager hoitaa oman reputationinsa, mutta synkataan varmuuden vuoksi
                self.reputation = quest_manager.reputation
                
            print(f"--- MATCH END: Quest '{completed_quest.title}' rewards distributed! ---")
            
            # --- VISUAL FEEDBACK ---
            if self.vfx:
                # Show a large notification in the center of the screen
                self.vfx.show_damage(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100, "QUEST COMPLETE!", color=(255, 215, 0))
                self.vfx.show_damage(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60, f"{completed_quest.title}", color=(200, 200, 200))

    def calculate_rewards(self, win):
        # Säilytetään taistelun aikana kerätty loot (esim. mainatut malmit)
        existing_loot = self.round_rewards.get('loot', {})
        self.round_rewards = {'gold': 0, 'loot': existing_loot, 'xp': 0}
        
        if win:
            if self.mode == "League":
                tier = self._get_league_tier()
                self.round_rewards['gold'] = 100 + (tier * 50)
            elif self.mode == "Arena":
                self.round_rewards['gold'] = 50 + (self.league_level * 10)
                self.season_wins += 1
            elif self.mode in ["Monster Hunt", "Boss Hunt"]:
                 if self.selected_mission:
                     self.round_rewards['gold'] = self.selected_mission.get('reward_gold', 0)
                     self.round_rewards['rep'] = self.selected_mission.get('reward_rep', 0)
        else:
            self.round_rewards['gold'] = 15
            if self.mode == "Arena": self.season_losses += 1

        if self.mode == "Arena": self.matches_played += 1
        
        # --- LOOT GENERATION (Enemies) ---
        if win:
            # Käydään läpi kaikki viholliset (myös kuolleet)
            # Huom: enemy_team sisältää ne vielä tässä vaiheessa
            for enemy in self.enemy_team:
                base_name = self._loot_key_for(enemy)
                drops = LOOT_DROPS.get(base_name)
                if drops:
                    # Tuki listalle (uusi) tai dictille (vanha)
                    drop_list = drops if isinstance(drops, list) else [drops]
                    
                    for d in drop_list:
                        # 1. Tarkista todennäköisyys
                        if random.random() > d.get('chance', 1.0): # 1.0 = Guaranteed
                            continue

                        # 2. Selvitä itemin nimi (yksittäinen vai one_of-listasta)
                        item_name = d.get('item')
                        if 'one_of' in d:
                            item_name = random.choice(d['one_of'])
                        
                        if not item_name: continue

                        qty = random.randint(d.get('min', 1), d.get('max', 1))
                        
                        # 3. Luo esine tai lisää materiaali
                        item_obj = self._create_loot_item(item_name)
                        if item_obj:
                            self.equipment_bag.append(item_obj)
                            print(f"*** LOOT DROP: {item_obj.name} added to Equipment Bag! ***")
                            self.round_rewards['loot'][item_name] = self.round_rewards['loot'].get(item_name, 0) + 1
                        else:
                            # Materiaali
                            self.round_rewards['loot'][item_name] = self.round_rewards['loot'].get(item_name, 0) + qty
        
        enemy_level_sum = sum(int(getattr(e, "level", 1) or 1) for e in self.enemy_team)
        xp_total = 0
        if win:
            base = 35 if self.mode == "Arena" else 65
            xp_total = base + enemy_level_sum * 10
        else:
            xp_total = 10 + enemy_level_sum * 3
        self.round_rewards["xp"] = int(max(0, xp_total))

    def _loot_key_for(self, enemy):
        """Mäppää vihollisen LOOT_DROPS-avaimeksi. Kestää numeroidut nimet
        ('Skeleton 2') ja tunnistaa perheet substringilla."""
        import re
        raw = getattr(enemy, "name", "") or ""
        # Poista mahdollinen numero lopusta ("Bandit 3" -> "Bandit")
        stripped = re.sub(r"\s+\d+$", "", raw).strip()
        # 1) Suora täsmäys (tarkin ensin)
        for candidate in (raw, stripped):
            if candidate in LOOT_DROPS:
                return candidate
        # 2) Perheet substringilla (spesifisin ensin)
        families = [
            ("Rat King", "Rat King"),
            ("Troll", "Troll"),
            ("Broodmother", "Cave Broodmother"),
            ("Spiderling", "Spiderling"),
            ("Hush", "Hush-Mantle"),
            ("Cadaver", "Red Lantern Cadaver"),
            ("Gutter", "Gutter Vermin"),
            ("Rat Rider", "Rat Rider"),
            ("Skeleton Archer", "Skeleton Archer"),
            ("Archer", "Skeleton Archer"),
            ("Skeleton", "Skeleton"),
            ("Zombie", "Zombie"),
            ("Crow", "Corrupted Crow"),
            ("Rat", "Giant Rat"),
            ("Frog", "Giant Frog"),
            ("Leech", "Bog Leech"),
        ]
        for needle, key in families:
            if needle in stripped and key in LOOT_DROPS:
                return key
        return stripped

    def _create_loot_item(self, name):
        """Luo esineen nimen perusteella. Tukee custom Rat-esineitä."""
        # Standard Items (create_item hoitaa nyt kaikki esineet dynaamisesti)
        # Materiaalit (kuten 'Rat Tail') palauttavat None create_itemistä, mikä on oikein
        return create_item(name)

    def apply_rewards(self):
        self.gold += self.round_rewards['gold']
        
        # --- REPUTATION HANDLING ---
        # 1. Faction specific (Dict)
        rep_dict = self.round_rewards.get('rep_changes', {})
        for faction, amount in rep_dict.items():
            self.modify_faction_rep(faction, amount)
            
        # 2. Global / Generic (Int) - Legacy tuki
        rep_gain = self.round_rewards.get('rep', 0) # Jos tehtävä antaa suoraa "Global Famea"
        if rep_gain != 0:
            self.reputation += rep_gain
            if quest_manager: quest_manager.reputation = self.reputation
        
        # Käsittele loot (Erottele materiaalit varusteista)
        loot_dict = self.round_rewards.get('loot', {})
        for name, count in loot_dict.items():
            # Jos se on varuste, se on jo lisätty equipment_bagiin calculate_rewardsissa.
            # Lisätään inventaarioon VAIN jos se on materiaali (eli _create_loot_item palauttaa None).
            if not self._create_loot_item(name):
                self.add_loot_name(name, count)

        xp_total = int(self.round_rewards.get("xp", 0))
        fighters = [u for u in self.last_fighters if u]
        if fighters and xp_total > 0:
            each = max(1, xp_total // len(fighters))
            for u in fighters:
                if hasattr(u, "add_xp") and u.add_xp(each):
                    print(f"{u.name} leveled up!")
        
        # FIX: Kaikki yksiköt (myös Commander) parannetaan täyteen taistelun jälkeen
        roster_to_heal = list(self.my_team)
        if self.player_character: roster_to_heal.append(self.player_character)
        
        for u in roster_to_heal:
            u.current_hp = u.max_hp
            u.current_mana = u.max_mana
            u.current_stamina = u.max_stamina
            u.is_dead = False

        for u in list(self.enemy_team):
            try: u.kill()
            except Exception: pass

        if self.mode == "Arena" and self.matches_played >= self.season_length:
            if self.season_wins >= 3:
                self.league_level += 1
                self.gold += 200 * self.league_level
            elif self.season_wins < 2 and self.league_level > 1:
                self.league_level -= 1
            self.matches_played = 0
            self.season_wins = 0
            self.season_losses = 0

        # BUGIKORJAUS (pelitesti 13): Grand Slam -sarjan välissä rosteria
        # EI saa tyhjentää - handle_promotion_result käynnistää seuraavan
        # kierroksen last_fighters-listalla. Tyhjennys aiheutti sen että
        # 2. matsiin ei spawnannut ketään ja tuli automaattinen DEFEAT.
        if getattr(self, "match_mode", "") != "PROMOTION":
            self.last_fighters = []
            self.active_player_units.empty()
        self.refresh_hub()

        # --- AUTOSAVE ---
        # Tallennetaan automaattisesti taistelun jälkeen, ettei edistys katoa
        try:
            import save_manager
            save_manager.save_game(self)
        except Exception as e:
            print(f"[Save] Autosave failed: {e}")

    # =========================================================
    # HELPERS & HUB MANAGEMENT
    # =========================================================
    def refresh_hub(self):
        self.generate_recruits()
        self.generate_shop()
        self.check_game_over()
        print("Town Hub refreshed!")

    def recruit_initial_hero(self):
        hero = Human("Hero", 100, 300, GREEN, "Veteran")
        self.my_team.add(hero)
        self.update_all_groups()

    def generate_recruits(self):
        self.recruit_options = []
        possible_classes = [Human, Orc, Elf, Goblin]
        
        for i in range(6):
            UnitClass = random.choice(possible_classes)
            
            # Determine race name for name generation
            race_name = "Human"
            if UnitClass == Orc: race_name = "Orc"
            elif UnitClass == Elf: race_name = "Elf"
            elif UnitClass == Goblin: race_name = "Goblin"
            
            name = get_random_name(race_name)
            
            if UnitClass == Human: 
                u = Human(name, 0, 0, GREEN, "Common")
            else: 
                u = UnitClass(name, 0, 0, GREEN)
            
            # Synnynnäiset lahjakkuudet (systems/talents.py): jokainen
            # rekry on uniikki - 1-3 talenttia + mahdollinen heikkous.
            # Nimet näkyvät kortilla; tarkat numerot vaativat Commanderin
            # Appraiser's Eye -taidon.
            from systems.talents import roll_talents, apply_talents
            talents, quirk = roll_talents()
            u.cost += apply_talents(u, talents, quirk)
            u.cost = max(15, u.cost)

            self.recruit_options.append(u)

    def barracks_bunk_count(self):
        from citys.mucford.barracks_interior_arena import BUNKS_PER_LEVEL
        return BUNKS_PER_LEVEL.get(int(getattr(self, "barracks_level", 1)), 6)

    def team_capacity(self):
        """Roosterin katto: tarvitaan SEKÄ punkat (barracksin taso) ETTÄ
        johtajuus (COMMAND-puun Recruiter-noodit, oletus 6)."""
        pc = self.player_character
        leadership = int(getattr(pc, "team_capacity", 6)) if pc else 6
        return min(self.barracks_bunk_count(), leadership)

    def has_free_bunk(self):
        """Commander vie yhden paikan; loput ovat gladiaattoreille."""
        return 1 + len(self.my_team) < self.team_capacity()

    def _roster_block_reason(self):
        """Kertoo kumpi raja estää palkkauksen: punkat vai johtajuus."""
        pc = self.player_character
        leadership = int(getattr(pc, "team_capacity", 6)) if pc else 6
        if self.barracks_bunk_count() <= leadership:
            return ("No free bunks in the barracks - "
                    "upgrade it to house more fighters.")
        return ("Your leadership caps the roster - unlock Recruiter "
                "in the COMMAND skill tree.")

    def hire_recruit(self, index):
        if not self.has_free_bunk():
            self.hire_block_message = self._roster_block_reason()
            self._toast_timer = 240
            return False
        if index < len(self.recruit_options) and self.recruit_options[index]:
            rec = self.recruit_options[index]
            if self.gold >= rec.cost:
                self.gold -= rec.cost
                self.my_team.add(rec)
                self._restore_unit_ai(rec)
                self.update_all_groups()
                self.recruit_options[index] = None
                return True
        return False
        
    def hire_unit_by_reference(self, unit, cost):
        """Palkkaa yksikön suoraan objektiviittauksella (Dialogista)."""
        if not self.has_free_bunk():
            self.hire_block_message = self._roster_block_reason()
            self._toast_timer = 240
            return False
        if self.gold >= cost:
            self.gold -= cost
            self.my_team.add(unit)
            self._restore_unit_ai(unit)
            self.update_all_groups()
            # Poista recruit_options listasta
            if unit in self.recruit_options:
                idx = self.recruit_options.index(unit)
                self.recruit_options[idx] = None
            return True
        return False

    def _restore_unit_ai(self, unit):
        """Palauttaa yksikön alkuperäisen taisteluälyn (TavernAI -> Combat AI)."""
        if hasattr(unit, "_combat_ai_backup") and unit._combat_ai_backup:
            unit.ai_controller = unit._combat_ai_backup
            # Siivotaan backup pois
            del unit._combat_ai_backup
        else:
            # Fallback: Jos backupia ei löydy, luodaan uusi perusäly
            # Tämä estää pelin kaatumisen tai TavernAI:n jäämisen päälle
            if not isinstance(unit.ai_controller, BaseAI) or "TavernAI" in str(type(unit.ai_controller)):
                unit.ai_controller = BaseAI(unit)

    def generate_shop(self):
        """Päivittää kaupan valikoiman: 12 esinettä per harvinaisuustaso."""
        new_shop_list = []
        rarity_levels = ["Common", "Rare", "Epic", "Legendary"]
        
        for r in rarity_levels:
            try:
                # Pyydetään 12 esinettä per taso
                items = get_random_shop_items(12, rarity_mode=r)
                new_shop_list.extend(items)
            except TypeError:
                # Fallback jos item_registry ei tue rarity-filtteriä
                new_shop_list.extend(get_random_shop_items(12))
        
        self.shop_items = new_shop_list
        self.magic_shop_items = get_all_spells_for_shop()
        print(f"[Shop] Market refreshed with {len(self.shop_items)} items.")

    def buy_shop_item(self, index, is_magic=False):
        lst = self.magic_shop_items if is_magic else self.shop_items
        if index < len(lst) and lst[index]:
            item = lst[index]
            if self.gold >= item.cost:
                self.gold -= item.cost
                self.equipment_bag.append(item)
                lst[index] = None
                return True
        return False
    
    def buy_item(self, item_index, target_unit):
        return self.buy_shop_item(item_index)

    def sell_item(self, item):
        if item in self.equipment_bag:
            sell_price = int(item.cost * 0.5)
            self.gold += sell_price
            self.equipment_bag.remove(item)
            return True
        return False

    def heal_team(self):
        if self.gold >= 50:
            self.gold -= 50
            for u in self.my_team:
                u.heal(1000)
                u.is_dead = False
                u.current_hp = u.max_hp
                u.current_mana = u.max_mana
                u.current_stamina = u.max_stamina
            return True
        return False

    def smith_discount(self):
        """Tiimin seppä (Brekka) alentaa koulutus-/korjauskuluja 20%."""
        return 0.8 if getattr(self, "has_smith", False) else 1.0

    def train_unit(self, unit, stat_name):
        base_cost = getattr(unit, 'upgrade_cost', 100)
        current_cost = int(base_cost * self.smith_discount())
        if self.gold >= current_cost:
            self.gold -= current_cost
            if stat_name == 'str':
                unit.base_attributes['str'] += 2
                unit.base_attributes.setdefault('max_hp', 100)
                unit.base_attributes['max_hp'] += 10
            elif stat_name == 'dex':
                unit.base_attributes['dex'] += 2
            elif stat_name == 'int':
                unit.base_attributes['int'] += 2
                unit.base_attributes['mana'] += 5

            unit.calculate_final_stats()
            unit.current_hp = unit.max_hp
            unit.current_mana = unit.max_mana
            # Seuraavan tason perushinta kasvaa perushinnasta (ei alennetusta)
            unit.upgrade_cost = int(base_cost * 1.2)
            return True
        return False
    
    def dismiss_unit(self, unit):
        if unit in self.my_team:
            print(f"Dismissed {unit.name}.")
            unit.kill()
            self.update_all_groups()
            
            # Palauta tavern pooliin (recruit_options)
            for i in range(len(self.recruit_options)):
                if self.recruit_options[i] is None:
                    self.recruit_options[i] = unit
                    return True
            self.recruit_options.append(unit)
            return True
        return False

    def check_game_over(self):
        living = [u for u in self.my_team if u.current_hp > 0 and not getattr(u, "is_dead", False)]
        if not living and self.gold < 50 and len(self.my_team) > 0:
            self.is_game_over = True
        else:
            self.is_game_over = False

    def craft_item(self, recipe_name, target_unit):
        if recipe_name not in BLUEPRINTS: return False
        recipe = BLUEPRINTS[recipe_name]
        if self.gold < recipe['cost']: return False
        
        if not CHEAT_MODE:
            for mat, count in recipe['mats'].items():
                if self.inventory.get(mat, 0) < count: return False

        self.gold -= recipe['cost']
        if not CHEAT_MODE:
            for mat, count in recipe['mats'].items():
                self.inventory[mat] -= count
                if self.inventory[mat] <= 0: del self.inventory[mat]
            # Sparing Hammer (Path of the Anvil 10): 15 % mahdollisuus
            # saada yksi materiaali takaisin
            try:
                from systems import commander_progression as _prog
                import random as _random
                if _prog.has_perk(self, "smithing", "sparing_hammer") and \
                        recipe['mats'] and _random.random() < 0.15:
                    saved = next(iter(recipe['mats']))
                    self.add_material(saved, 1)
            except Exception:
                pass

        # Avainesineet/materiaalit (esim. Cistern Gate Crank) menevät suoraan
        # reppuun, ei equipment_bagiin - niitä ei voi varustaa (pelitesti 24)
        if recipe.get('type') in ('key_item', 'material'):
            self.inventory[recipe_name] = self.inventory.get(recipe_name, 0) + 1
        else:
            try:
                new_item = self._create_loot_item(recipe_name)
                if new_item:
                    self.equipment_bag.append(new_item)
                else:
                    self.add_material(recipe_name, 1)
            except Exception:
                self.add_material(recipe_name, 1)

        # Path of the Anvil: XP jokaisesta taonnasta
        try:
            from systems import commander_progression as _prog
            _prog.on_item_crafted(self, recipe.get('cost', 0))
        except Exception:
            pass
        return True

    def equip_from_bag(self, item):
        """Siirtää esineen repusta pelaajan varusteisiin."""
        if item in self.equipment_bag:
            self.equipment_bag.remove(item)
            slot = getattr(item, "slot_type", "main_hand")
            old_item = self.player_character.equip_item_to_slot(slot, item)
            
            if old_item is item: # Epäonnistui (esim. vaatimukset)
                self.equipment_bag.append(item)
                sound_system.play_sound('error')
            else:
                if old_item: self.equipment_bag.append(old_item)
                sound_system.play_sound('recruit')

    def unequip_item(self, slot):
        item = self.player_character.unequip_slot(slot)
        if item:
            self.equipment_bag.append(item)
            sound_system.play_sound('click')

    # --- HELPERS ---
    def _get_league_tier(self) -> int:
        ladders = getattr(self.league_engine, "ladders", None)
        if isinstance(ladders, dict):
            return int(ladders.get(self.match_mode, 1))
        return 1

    def _position_units(self, units, side: str):
        if not units: return
        arena = self.current_arena
        # Isot areenat (esim. Grand Slam -stadion) määrittelevät omat
        # spawn-pisteensä; muuten käytetään ruutukoon oletuksia.
        # BUGIKORJAUS (pelitesti 22): osa areenoista (Rat Sewer) käyttää
        # spawn_points-LISTAA - .get(side) listalle kaatoi bossijahdin
        spawn = None
        if arena is not None:
            pts = getattr(arena, "spawn_points", None)
            if isinstance(pts, dict):
                spawn = pts.get(side)
        if spawn:
            start_x, start_y = int(spawn[0]), int(spawn[1])
        else:
            start_x = 100 if side == "left" else SCREEN_WIDTH - 150
            start_y = 200
        step_y = 70
        for i, u in enumerate(units):
            u.rect.topleft = (start_x, start_y + i * step_y)

    def _position_units_center(self, units, cx, cy):
        # Asettaa yksiköt ryppääseen keskelle
        for i, u in enumerate(units):
            angle = (i / len(units)) * 6.28
            radius = 40
            u.rect.center = (cx + math.cos(angle)*radius, cy + math.sin(angle)*radius)

    def _combat_y_bounds(self):
        return 110, SCREEN_HEIGHT - 110

    def _build_known_material_set(self):
        mats = set()
        try:
            for bp in BLUEPRINTS.values():
                for m in bp.get("mats", {}).keys(): mats.add(m)
        except Exception: pass
        return mats

    def _looks_like_material(self, name):
        return name in self._known_materials

    def add_loot_many(self, loot_dict):
        if not loot_dict: return
        for name, cnt in loot_dict.items():
            self.add_loot_name(name, cnt)

    def add_loot_name(self, item_name, count=1):
        if not item_name: return
        self.inventory[item_name] = self.inventory.get(item_name, 0) + count
        
    def add_material(self, name, count=1):
        if not name: return
        count = int(count)
        
        # Jos taistelu on käynnissä, lisätään round_rewardsiin (näkyy loppuruudussa)
        if self.match_in_progress:
            if 'loot' not in self.round_rewards: self.round_rewards['loot'] = {}
            self.round_rewards['loot'][name] = self.round_rewards['loot'].get(name, 0) + count
        else:
            # Muuten suoraan reppuun (esim. crafting)
            self.inventory[name] = self.inventory.get(name, 0) + count

    def update_all_groups(self):
        self.all_units.empty()
        for u in self.my_team: self.all_units.add(u)
        for u in self.enemy_team: self.all_units.add(u)

    def draw_names_overlay(self, screen, offset):
        """Piirtää nimet yksiköiden ja resurssien päälle kun ALT on pohjassa."""
        for sprite in self.all_units:
            # Optimointi: Piirrä vain jos ruudulla
            sx = sprite.rect.centerx - offset[0]
            sy = sprite.rect.centery - offset[1]
            if not (-100 < sx < SCREEN_WIDTH + 100 and -100 < sy < SCREEN_HEIGHT + 100):
                continue

            name = None
            color = (255, 255, 255)

            # 1. Kerättävät resurssit (loot_item) - Sienet, Puut, Romu
            if hasattr(sprite, "loot_item"):
                if getattr(sprite, "is_empty", False): continue
                name = sprite.loot_item
                color = (255, 215, 0) # Kulta

            # 2. Malmit (resource_name) - Iron Ore
            elif hasattr(sprite, "resource_name"):
                if getattr(sprite, "is_empty", False): continue
                name = sprite.resource_name
                color = (200, 200, 220) # Rauta

            # 3. Yksiköt (HP-palkilliset)
            elif hasattr(sprite, "current_hp") and hasattr(sprite, "max_hp"):
                if getattr(sprite, "is_dead", False): continue
                name = getattr(sprite, "name", "Unit")
                
                # Piilota "Structure" nimiset (seinät yms), ellei haluta nähdä niitä
                if name == "Structure": continue

                team = getattr(sprite, "team_color", None)
                
                if team == PLAYER_TEAM: color = (100, 255, 100) # Pelaaja (Vihreä)
                elif team == ENEMY_TEAM: color = (255, 100, 100) # Vihollinen (Punainen)
                else: color = (220, 220, 220)

            if name:
                # Piirrä teksti hahmon yläpuolelle
                surf = font_small.render(name, True, color)
                top_y = getattr(sprite, "hurt_rect", sprite.rect).top
                rect = surf.get_rect(center=(sx, top_y - offset[1] - 15))
                
                # Varjo (Outline) parantaa luettavuutta
                shad = font_small.render(name, True, (0, 0, 0))
                screen.blit(shad, (rect.x + 1, rect.y + 1))
                screen.blit(surf, rect)

    def draw_interaction_prompts(self, screen, offset):
        """Piirtää leijuvat vihjeet (esim. 'E') vuorovaikutettavien kohteiden päälle."""
        player = self.player_character
        if not player or player.is_dead: return

        px, py = player.rect.center
        
        # 1. Villagers (Talk)
        for u in self.all_units:
            if isinstance(u, Villager) and not u.is_dead:
                dist = math.hypot(u.rect.centerx - px, u.rect.centery - py)
                top_y = u.hurt_rect.top
                if dist < 80:
                    self._draw_floating_prompt(screen, u.rect.centerx, top_y - 40, "E", offset, "Talk")
            
            # Resources / Loot (Scrap, Ore)
            elif hasattr(u, "interaction_range") and u.interaction_range > 0 and not getattr(u, "is_empty", False):
                # Geneerinen vuorovaikutus (Data-driven)
                dist = math.hypot(u.rect.centerx - px, u.rect.centery - py)
                
                if dist < u.interaction_range:
                    label = getattr(u, "interaction_label", "Use")
                    self._draw_floating_prompt(screen, u.rect.centerx, u.rect.top - 30, "E", offset, label)

        # 2. Escort Target (House)
        if self.active_escort:
            target = self.active_escort["target"]
            # Target is a Prop
            tx = target.rect.centerx
            ty = target.rect.bottom + 20
            dist = math.hypot(tx - px, ty - py)
            if dist < 100:
                 self._draw_floating_prompt(screen, tx, target.rect.top - 40, "!", offset, "Arrived")

    # ==================================================================
    # QUEST JOURNAL (pelitesti 27): HUD-seuranta + täysi RPG-journal
    # ==================================================================
    @staticmethod
    def _quest_reward_parts(q):
        from ui_kit import format_money
        rw = q.rewards or {}
        parts = []
        if rw.get("gold"):
            parts.append(format_money(int(rw["gold"])))
        if rw.get("reputation"):
            parts.append(f"+{rw['reputation']} rep")
        if rw.get("xp"):
            parts.append(f"{rw['xp']} XP")
        items = rw.get("items") or {}
        for name, cnt in items.items():
            parts.append(f"{name} x{cnt}")
        return parts

    def _draw_quest_journal(self, screen):
        """HUD-seurantapaneeli oikeassa laidassa: näyttää VAIN seuratut
        aktiiviset/palautettavat questit. J avaa täyden journalin,
        silmänappi piilottaa paneelin."""
        if quest_manager is None:
            return
        panel_w = 360
        # Siirrettävä sijainti: oletus oikea laita, muuten pelaajan raahaama.
        default_x = SCREEN_WIDTH - panel_w - 24
        default_y = 170
        pos = self.journal_tracker_pos
        x = default_x if pos is None else int(pos[0])
        y = default_y if pos is None else int(pos[1])

        if not self.show_quest_journal:
            chip = pygame.Rect(x + panel_w - 126, y, 126, 34)
            pygame.draw.rect(screen, (18, 18, 24), chip, border_radius=9)
            pygame.draw.rect(screen, (150, 130, 80), chip, 2, border_radius=9)
            draw_text("QUESTS [J]", font_small, (220, 200, 150), screen,
                      chip.x + 14, chip.y + 8)
            self._journal_toggle_rect = chip
            self._journal_tracker_rect = None
            self._journal_drag_handle = None
            return

        # Seuratut aktiiviset + palautusvalmiit (main ensin)
        tracked = [q for q in quest_manager.quests.values()
                   if q.status in ("active", "completed")
                   and not q.is_finished
                   and quest_manager.is_tracked(q.id)]
        tracked.sort(key=lambda q: (q.category != "main",
                                    q.status != "completed"))
        rows = tracked[:5]

        h = 58 + (len(rows) * 62 if rows else 40)
        # Pidä paneeli ruudun sisällä
        x = max(8, min(x, SCREEN_WIDTH - panel_w - 8))
        y = max(8, min(y, SCREEN_HEIGHT - h - 8))
        panel = pygame.Rect(x, y, panel_w, h)
        self._journal_tracker_rect = panel
        # Raahauskahva = otsikkorivi (pois lukien silmänappi)
        self._journal_drag_handle = pygame.Rect(panel.x, panel.y,
                                                panel_w - 52, 36)
        surf = pygame.Surface(panel.size, pygame.SRCALPHA)
        surf.fill((14, 14, 20, 205))
        screen.blit(surf, panel.topleft)
        pygame.draw.rect(screen, (150, 130, 80), panel, 2, border_radius=10)
        # Raahauskahvan vihje: pienet tartuntapisteet otsikon vasemmalla
        for gx in range(panel.x + 8, panel.x + 16, 4):
            for gy in range(panel.y + 12, panel.y + 26, 5):
                pygame.draw.circle(screen, (110, 100, 70), (gx, gy), 1)
        draw_text("QUEST TRACKER", font_small, GOLD_COLOR, screen,
                  panel.x + 22, panel.y + 10)
        draw_text("[J] Journal", font_small, (150, 150, 160), screen,
                  panel.x + 158, panel.y + 12)
        # Silmänappi (piilota tracker)
        eye = pygame.Rect(panel.right - 42, panel.y + 6, 32, 26)
        pygame.draw.rect(screen, (40, 38, 32), eye, border_radius=7)
        pygame.draw.rect(screen, (150, 130, 80), eye, 1, border_radius=7)
        pygame.draw.ellipse(screen, (220, 200, 150),
                            (eye.x + 7, eye.y + 8, 18, 10), 2)
        pygame.draw.circle(screen, (220, 200, 150), eye.center, 3)
        self._journal_toggle_rect = eye

        yy = panel.y + 42
        if not rows:
            draw_text("No tracked quests.", font_small, GRAY, screen,
                      panel.x + 14, yy)
            draw_text("Press [J] to open the journal.", font_small,
                      GRAY, screen, panel.x + 14, yy + 20)
            return
        for q in rows:
            ready = (q.status == "completed")
            # Main-questit kullalla, side vaaleana
            if ready:
                col = (140, 230, 150)
            elif q.category == "main":
                col = (245, 210, 120)
            else:
                col = WHITE
            marker = "✦ " if q.category == "main" else "• "
            draw_text(marker + q.title[:32], font_small, col, screen,
                      panel.x + 14, yy)
            req = q.required_amount
            if ready:
                status = "READY - return to the giver!"
            elif req > 1:
                status = f"Progress {int(q.progress)}/{req}"
            else:
                status = self._quest_current_objective(q)
            draw_text(status[:50], font_small,
                      (150, 200, 160) if ready else (170, 170, 180),
                      screen, panel.x + 26, yy + 20)
            yy += 62

    def _live_objective_states(self, q):
        """Elävästi seurattujen questien per-tavoite valmiuslista
        (True/False). None jos quest ei ole erikoistapaus. Yhtenäistää
        onboarding-seurannan journaliin (esim. areenatiimin perustus)."""
        if q.id == "found_arena_team":
            try:
                from systems.muckford_opening_core import (
                    arena_team_objective_states)
                return arena_team_objective_states(self)
            except Exception:
                return None
        return None

    def _quest_current_objective(self, q):
        """Palauttaa questin nykyisen tavoiterivin (main-questeilla
        vaiheittain warrens-tilan tai elävän edistymän mukaan)."""
        objs = q.objectives
        states = self._live_objective_states(q)
        if states is not None and objs:
            for i, done in enumerate(states):
                if not done and i < len(objs):
                    return objs[i]
            return objs[-1]
        if q.id == "hunt_01" and objs:
            try:
                from citys.mucford.muckford_warrens import warrens_state
                stage = int(warrens_state(self).get("quest_stage", 0))
            except Exception:
                stage = 0
            idx = min(max(stage - 1, 0), len(objs) - 1)
            return objs[idx]
        if objs:
            return objs[0]
        return (q.description or "")[:60]

    # ---- Täysi RPG-journal (välilehdet, tiedot, seurannan valinta) ----
    def _journal_quests_for_tab(self, tab):
        if quest_manager is None:
            return []
        out = []
        for q in quest_manager.quests.values():
            if q.status == "locked":
                continue
            if tab == "completed":
                if q.is_finished:
                    out.append(q)
            elif tab == "main":
                if q.category == "main" and not q.is_finished:
                    out.append(q)
            else:  # side
                if q.category != "main" and not q.is_finished:
                    out.append(q)
        # Aktiiviset/valmiit ensin, sitten saatavilla olevat
        order = {"completed": 0, "active": 1, "available": 2}
        out.sort(key=lambda q: order.get(q.status, 3))
        return out

    def _journal_sync_selection(self):
        rows = self._journal_quests_for_tab(self.journal_tab)
        ids = [q.id for q in rows]
        if self.journal_selected not in ids:
            self.journal_selected = ids[0] if ids else None

    def _handle_full_journal_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_j):
                self.show_full_journal = False
                sound_system.play_sound('click')
                return True
            if event.key == pygame.K_TAB:
                order = ["main", "side", "completed"]
                i = (order.index(self.journal_tab) + 1) % 3
                self.journal_tab = order[i]
                self._journal_sync_selection()
                sound_system.play_sound('click')
                return True
            if event.key in (pygame.K_DOWN, pygame.K_UP):
                rows = self._journal_quests_for_tab(self.journal_tab)
                ids = [q.id for q in rows]
                if ids:
                    i = ids.index(self.journal_selected) \
                        if self.journal_selected in ids else 0
                    i = (i + (1 if event.key == pygame.K_DOWN else -1)) % len(ids)
                    self.journal_selected = ids[i]
                return True
            if event.key in (pygame.K_t, pygame.K_RETURN, pygame.K_SPACE):
                if self.journal_selected:
                    quest_manager.toggle_tracked(self.journal_selected)
                    sound_system.play_sound('click')
                return True
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            ui = self._journal_ui
            for rect, tab in ui.get("tabs", []):
                if rect.collidepoint(event.pos):
                    self.journal_tab = tab
                    self._journal_sync_selection()
                    sound_system.play_sound('click')
                    return True
            for rect, qid in ui.get("rows", []):
                if rect.collidepoint(event.pos):
                    self.journal_selected = qid
                    sound_system.play_sound('click')
                    return True
            track_btn = ui.get("track_btn")
            if track_btn and track_btn.collidepoint(event.pos) \
                    and self.journal_selected:
                quest_manager.toggle_tracked(self.journal_selected)
                sound_system.play_sound('click')
                return True
            close_btn = ui.get("close_btn")
            if close_btn and close_btn.collidepoint(event.pos):
                self.show_full_journal = False
                sound_system.play_sound('click')
                return True
        return False

    def _draw_full_journal(self, screen):
        from ui_kit import get_fullscreen_overlay
        self._journal_ui = {"tabs": [], "rows": [], "track_btn": None,
                            "close_btn": None}
        screen.blit(get_fullscreen_overlay((0, 0, 0, 200)), (0, 0))
        pw, ph = 1160, 720
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(screen, (22, 20, 26), panel, border_radius=16)
        pygame.draw.rect(screen, GOLD_COLOR, panel, 3, border_radius=16)
        draw_text("QUEST JOURNAL", font_title, GOLD_COLOR, screen,
                  px + 34, py + 22)
        # Sulkunappi
        close_btn = pygame.Rect(panel.right - 52, py + 22, 34, 34)
        pygame.draw.rect(screen, (60, 40, 40), close_btn, border_radius=8)
        pygame.draw.rect(screen, (200, 120, 110), close_btn, 2, border_radius=8)
        draw_text("X", font_main, (230, 180, 170), screen,
                  close_btn.x + 11, close_btn.y + 5)
        self._journal_ui["close_btn"] = close_btn

        # Välilehdet
        tab_defs = [("main", "MAIN"), ("side", "SIDE"), ("completed", "DONE")]
        tx = px + 34
        for key, label in tab_defs:
            n = len(self._journal_quests_for_tab(key))
            w = 190
            rect = pygame.Rect(tx, py + 76, w, 42)
            active = (self.journal_tab == key)
            pygame.draw.rect(screen, (54, 46, 30) if active else (30, 28, 34),
                             rect, border_radius=9)
            pygame.draw.rect(screen, GOLD_COLOR if active else (90, 84, 70),
                             rect, 2, border_radius=9)
            draw_text(f"{label} ({n})", font_main,
                      (245, 220, 150) if active else (170, 165, 155),
                      screen, rect.x + 20, rect.y + 9)
            self._journal_ui["tabs"].append((rect, key))
            tx += w + 12

        # Vasen lista
        list_rect = pygame.Rect(px + 34, py + 134, 420, ph - 200)
        pygame.draw.rect(screen, (16, 15, 20), list_rect, border_radius=10)
        pygame.draw.rect(screen, (80, 74, 60), list_rect, 1, border_radius=10)
        rows = self._journal_quests_for_tab(self.journal_tab)
        if self.journal_selected not in [q.id for q in rows]:
            self.journal_selected = rows[0].id if rows else None
        yy = list_rect.y + 12
        if not rows:
            draw_text("Nothing here yet.", font_small, GRAY, screen,
                      list_rect.x + 16, yy + 6)
        for q in rows:
            row = pygame.Rect(list_rect.x + 8, yy, list_rect.w - 16, 52)
            sel = (q.id == self.journal_selected)
            if sel:
                pygame.draw.rect(screen, (54, 48, 32), row, border_radius=8)
                pygame.draw.rect(screen, GOLD_COLOR, row, 2, border_radius=8)
            ready = (q.status == "completed")
            col = ((140, 230, 150) if ready else
                   (245, 210, 120) if q.category == "main" else WHITE)
            draw_text(q.title[:30], font_main, col, screen,
                      row.x + 14, row.y + 6)
            sub = ("READY to turn in" if ready else
                   "Finished" if q.is_finished else
                   q.status.capitalize())
            draw_text(sub, font_small, (150, 150, 160), screen,
                      row.x + 14, row.y + 30)
            # Seuranta-merkki
            if not q.is_finished and quest_manager.is_tracked(q.id):
                draw_text("TRACKED", font_small, (150, 200, 160), screen,
                          row.right - 92, row.y + 8)
            self._journal_ui["rows"].append((row, q.id))
            yy += 58

        # Oikea: yksityiskohdat
        det = pygame.Rect(px + 474, py + 134, pw - 474 - 34, ph - 200)
        pygame.draw.rect(screen, (16, 15, 20), det, border_radius=10)
        pygame.draw.rect(screen, (80, 74, 60), det, 1, border_radius=10)
        q = quest_manager.quests.get(self.journal_selected) \
            if self.journal_selected else None
        if q is None:
            draw_text("Select a quest.", font_main, GRAY, screen,
                      det.x + 24, det.y + 24)
        else:
            dx, dy = det.x + 26, det.y + 22
            badge = "MAIN QUEST" if q.category == "main" else "SIDE QUEST"
            bcol = (245, 210, 120) if q.category == "main" else (170, 200, 230)
            draw_text(badge, font_small, bcol, screen, dx, dy)
            draw_text(q.title, font_title, GOLD_COLOR, screen, dx, dy + 22)
            if q.giver:
                draw_text(f"Given by {q.giver}", font_small, (170, 165, 155),
                          screen, dx, dy + 62)
            # Kuvaus (rivitys)
            oy = dy + 92
            for line in self._wrap_text(q.description or "", font_small,
                                        det.w - 52)[:4]:
                draw_text(line, font_small, (210, 205, 195), screen, dx, oy)
                oy += 22
            # Tavoitteet
            oy += 12
            draw_text("OBJECTIVES", font_small, GOLD_COLOR, screen, dx, oy)
            oy += 26
            objs = q.objectives
            states = self._live_objective_states(q)
            cur = -1
            if states is None and q.id == "hunt_01":
                try:
                    from citys.mucford.muckford_warrens import warrens_state
                    cur = int(warrens_state(self).get("quest_stage", 0)) - 1
                except Exception:
                    cur = -1
            # Elävästi seuratuilla questeilla: ensimmäinen keskeneräinen = [>]
            first_open = -1
            if states is not None:
                for i, done in enumerate(states):
                    if not done:
                        first_open = i
                        break
            if objs:
                for i, ob in enumerate(objs):
                    if states is not None:
                        done_i = states[i] if i < len(states) else False
                        if q.is_finished or done_i:
                            mark, mcol = "[x]", (140, 210, 150)
                        elif i == first_open:
                            mark, mcol = "[>]", (245, 220, 150)
                        else:
                            mark, mcol = "[ ]", (160, 160, 170)
                    elif q.is_finished or (cur >= 0 and i < cur):
                        mark, mcol = "[x]", (140, 210, 150)
                    elif cur >= 0 and i == cur:
                        mark, mcol = "[>]", (245, 220, 150)
                    else:
                        mark, mcol = "[ ]", (160, 160, 170)
                    for j, line in enumerate(self._wrap_text(
                            f"{mark} {ob}", font_small, det.w - 52)):
                        draw_text(line, font_small, mcol, screen,
                                  dx + (0 if j == 0 else 28), oy)
                        oy += 22
            else:
                req = q.required_amount
                txt = (f"Progress {int(q.progress)}/{req}" if req > 1
                       else "In progress")
                draw_text(txt, font_small, (200, 200, 210), screen, dx, oy)
                oy += 22
            # Palkinnot
            oy += 12
            draw_text("REWARDS", font_small, GOLD_COLOR, screen, dx, oy)
            parts = self._quest_reward_parts(q)
            draw_text("  ".join(parts) if parts else "-", font_small,
                      (200, 180, 120), screen, dx + 120, oy)

            # Seuranta-nappi (ei valmiille)
            if not q.is_finished:
                tracked = quest_manager.is_tracked(q.id)
                btn = pygame.Rect(det.x + 26, det.bottom - 58, 250, 40)
                pygame.draw.rect(screen, (48, 66, 48) if tracked else (44, 40, 48),
                                 btn, border_radius=9)
                pygame.draw.rect(screen, (130, 200, 150) if tracked
                                 else (150, 140, 120), btn, 2, border_radius=9)
                label = "TRACKED - click to hide" if tracked \
                    else "TRACK this quest"
                draw_text(label, font_main,
                          (150, 220, 160) if tracked else (210, 200, 180),
                          screen, btn.x + 18, btn.y + 8)
                self._journal_ui["track_btn"] = btn

        draw_text("[Tab] switch  [Up/Down] select  [T/Enter] track  "
                  "[J/Esc] close", font_small, (150, 150, 160), screen,
                  px + 34, panel.bottom - 32)

    @staticmethod
    def _wrap_text(text, font, width):
        words = str(text).split()
        lines, cur = [], ""
        for w in words:
            trial = w if not cur else f"{cur} {w}"
            if font.size(trial)[0] <= width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def _draw_floating_prompt(self, screen, x, y, key_text, offset, label_text=None):
        # Floating effect (Siniaalto)
        float_y = math.sin(pygame.time.get_ticks() * 0.008) * 4
        
        sx = x - offset[0]
        sy = y - offset[1] + float_y
        
        # Key bubble (E)
        key_surf = font_main.render(key_text, True, (255, 255, 255))
        kw, kh = key_surf.get_size()
        padding = 8
        
        bg_rect = pygame.Rect(sx - kw//2 - padding, sy - kh//2 - padding, kw + padding*2, kh + padding*2)
        
        # Shadow (Tumma tausta)
        shadow_rect = bg_rect.copy()
        shadow_rect.y += 2
        s = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 100), s.get_rect(), border_radius=6)
        screen.blit(s, shadow_rect.topleft)
        
        # Box
        pygame.draw.rect(screen, (40, 40, 50), bg_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 215, 0), bg_rect, 2, border_radius=6) # Gold border
        
        screen.blit(key_surf, (sx - kw//2, sy - kh//2))
        
        # Optional Label below (e.g. "Talk")
        if label_text:
            lbl_surf = font_small.render(label_text, True, (200, 200, 200))
            lw, lh = lbl_surf.get_size()
            
            # Text shadow
            lbl_shad = font_small.render(label_text, True, (0, 0, 0))
            screen.blit(lbl_shad, (sx - lw//2 + 1, bg_rect.bottom + 3))
            
            screen.blit(lbl_surf, (sx - lw//2, bg_rect.bottom + 2))

    def draw_game(self, screen):
        # Apply screen shake to camera offset
        shake_x, shake_y = 0, 0
        if self.screen_shake > 0:
            shake_x = random.randint(-int(self.screen_shake), int(self.screen_shake))
            shake_y = random.randint(-int(self.screen_shake), int(self.screen_shake))
            
        offset = (self.camera_x + shake_x, self.camera_y + shake_y)
        
        if self.current_arena:
            try:
                self.current_arena.draw_background(screen, offset)
            except TypeError:
                self.current_arena.draw_background(screen)
        
        # 1. Piirrä lattiaefektit (Acid Puddle) hahmojen alle
        self.vfx.draw_floor(screen, offset)

        if self.current_map_vfx:
            self.current_map_vfx.draw_floor(screen, offset)

        # --- ESCORT DESTINATION MARKER ---
        if self.active_escort:
            target = self.active_escort["target"]
            # Kohde: Talon edusta
            tx = target.rect.centerx - offset[0]
            ty = target.rect.bottom + 20 - offset[1]
            
            # Sykkivä efekti
            pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5 # 0..1
            radius = 80 + int(pulse * 10)
            
            # Piirrä "Zone" (Läpinäkyvä keltainen)
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 215, 0, 60), (radius, radius), radius)
            pygame.draw.circle(s, (255, 215, 0, 150), (radius, radius), radius, 2)
            screen.blit(s, (tx - radius, ty - radius))

        # Järjestä yksiköt Y-koordinaatin mukaan (Draw Order)
        sorted_units = sorted(self.all_units, key=lambda u: u.rect.bottom)

        player = self.player_character
        player_rect = player.rect if player else None

        for u in sorted_units:
            # --- TRANSPARENCY LOGIC ---
            alpha = 255
            if player_rect and u != player:
                is_obscuring = False
                # Check if u is an obstacle in the arena
                if self.current_arena and u in getattr(self.current_arena, "obstacles", []):
                    # Check overlap and Y-order (u is "in front" if bottom is greater)
                    if u.rect.colliderect(player_rect) and u.rect.bottom > player_rect.bottom:
                        is_obscuring = True
                
                if is_obscuring:
                    alpha = 100

            # --- PLAYER HIGHLIGHT (3v3/5v5 Clarity) ---
            if u == player:
                # Piirrä valkoinen rinkula jalkojen alle
                pygame.draw.ellipse(screen, (255, 255, 255), 
                                    (u.rect.x - offset[0] - 4, u.rect.bottom - offset[1] - 6, u.rect.width + 8, 12), 2)

            # Apply alpha
            if alpha < 255 and hasattr(u, "image") and u.image:
                u.image.set_alpha(alpha)
            
            # Draw
            if hasattr(u, 'draw_on_screen'): u.draw_on_screen(screen, offset)
            elif not getattr(u, "use_sprites", False):
                u.draw_procedural()
                screen.blit(u.image, (u.rect.x - offset[0], u.rect.y - offset[1]))
            
            # Reset alpha immediately
            if alpha < 255 and hasattr(u, "image") and u.image:
                u.image.set_alpha(255)

            u.draw_health_bar(screen, offset)
            
        if self.current_arena and hasattr(self.current_arena, "draw_foreground"):
            try:
                self.current_arena.draw_foreground(screen, offset)
            except TypeError:
                self.current_arena.draw_foreground(screen)
            
        # 2. Piirrä muut efektit (Damage text, räjähdykset) hahmojen päälle
        self.vfx.draw_top(screen, offset)

        if self.current_map_vfx:
            self.current_map_vfx.draw_top(screen, offset)

        # --- DEBUG HITBOXES (CHEAT_MODE) ---
        if CHEAT_MODE:
            # 1. Esteet (Keltainen)
            if self.current_arena:
                for obs in getattr(self.current_arena, "obstacles", []):
                    r = getattr(obs, "rect", obs)
                    pygame.draw.rect(screen, (255, 255, 0), (r.x - offset[0], r.y - offset[1], r.w, r.h), 1)
            
            # 2. Yksiköt
            for u in self.all_units:
                # Physics / Jalat (Punainen)
                pygame.draw.rect(screen, (255, 0, 0), (u.rect.x - offset[0], u.rect.y - offset[1], u.rect.w, u.rect.h), 1)
                # Hurtbox / Vartalo (Sininen)
                if hasattr(u, "hurt_rect"):
                    hr = u.hurt_rect
                    pygame.draw.rect(screen, (0, 100, 255), (hr.x - offset[0], hr.y - offset[1], hr.w, hr.h), 1)

        # --- INTERACTION PROMPTS ---
        self.draw_interaction_prompts(screen, offset)

        # --- ALT OVERLAY ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LALT] or keys[pygame.K_RALT]:
            self.draw_names_overlay(screen, offset)
            
        # --- ESCORT UI ---
        if self.active_escort:
            self._draw_escort_ui(screen)
            
        # --- DIALOGUE OVERLAY ---
        if self.active_dialogue:
            self._draw_in_game_dialogue(screen)

    def _draw_in_game_dialogue(self, screen):
        """Piirtää dialogi-popupin ruudun alaosaan."""
        data = self.active_dialogue
        unit = data["unit"]
        text = data["text"]
        
        # Tummenna tausta
        from ui_kit import get_fullscreen_overlay
        screen.blit(get_fullscreen_overlay((0, 0, 0, 150)), (0, 0))

        # Popup Box
        box_w, box_h = 800, 200
        box_x = (SCREEN_WIDTH - box_w) // 2
        box_y = (SCREEN_HEIGHT - box_h) // 2 # Keskelle ruutua
        
        draw_panel(screen, box_x, box_y, box_w, box_h, color=(30, 30, 40), border_color=(100, 100, 120))
        
        # Portrait (Vasemmalla, skaalattu isoksi)
        if hasattr(unit, "big_image") and unit.big_image:
            # Skaalaa korkeuden mukaan
            p_h = 250
            ratio = unit.big_image.get_width() / unit.big_image.get_height()
            p_w = int(p_h * ratio)
            portrait = pygame.transform.smoothscale(unit.big_image, (p_w, p_h))
            
            # Piirrä laatikon vasempaan reunaan, hieman yli laatikon yläreunan
            screen.blit(portrait, (box_x - 20, box_y - (p_h - box_h) - 20))
        
        # Nimi
        draw_text(unit.name, font_title, GOLD_COLOR, screen, box_x + 220, box_y + 20)
        
        # Teksti
        draw_text(f'"{text}"', font_main, WHITE, screen, box_x + 220, box_y + 80)
        
        # Options
        opts = data.get("options")
        if opts:
            view_x = box_x + 220
            view_y = box_y + 130
            view_w = box_w - 240
            view_h = box_h - 140 # ~60px tilaa
            
            # Clip area for scrolling
            prev_clip = screen.get_clip()
            screen.set_clip(pygame.Rect(view_x, view_y, view_w, view_h))
            
            oy = view_y - self.dialogue_scroll
            mx, my = pygame.mouse.get_pos()
            for opt in opts:
                # Hover highlight
                col = GOLD_COLOR
                # Check hover within bounds
                if box_x + 220 <= mx <= box_x + 700 and oy <= my <= oy + 25 and view_y <= my <= view_y + view_h:
                    col = WHITE
                
                draw_text(opt["text"], font_main, col, screen, box_x + 220, oy)
                oy += 30
            
            screen.set_clip(prev_clip)
        
        # Ohje
        draw_text("Press SPACE to close", font_small, GRAY, screen, box_x + box_w - 200, box_y + box_h - 30)

    def _draw_escort_ui(self, screen):
        # Top Left Position (Siistimpi ja pienempi)
        ui_w = 260
        ui_h = 65
        x = 30 # Hieman enemmän marginaalia reunasta
        y = 20
        
        # Taustapaneeli
        draw_panel(screen, x, y, ui_w, ui_h, color=(30, 30, 40), border_color=(100, 100, 120))
        
        # Tekstit (Pienemmät fontit)
        draw_text("ESCORT MISSION", font_main, GOLD_COLOR, screen, x + 15, y + 10)
        draw_text("Guide villager to safety", font_small, (200, 200, 200), screen, x + 15, y + 35)
        
        # Close Button (X)
        close_rect = pygame.Rect(x + ui_w - 25, y + 5, 20, 20)
        pygame.draw.rect(screen, (200, 50, 50), close_rect, border_radius=4)
        pygame.draw.line(screen, WHITE, (close_rect.left + 5, close_rect.top + 5), (close_rect.right - 5, close_rect.bottom - 5), 2)
        pygame.draw.line(screen, WHITE, (close_rect.left + 5, close_rect.bottom - 5), (close_rect.right - 5, close_rect.top + 5), 2)
        
        # Arrow Logic
        target = self.active_escort["target"]
        
        # Target screen pos (Doorstep)
        tx = target.rect.centerx - self.camera_x
        ty = target.rect.bottom + 20 - self.camera_y
        
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        # Jos kohde ei ole ruudulla, piirrä nuoli
        if not (0 < tx < SCREEN_WIDTH and 0 < ty < SCREEN_HEIGHT):
            dx = tx - cx
            dy = ty - cy
            angle = math.atan2(dy, dx)
            
            arrow_dist = 300
            ax = cx + math.cos(angle) * arrow_dist
            ay = cy + math.sin(angle) * arrow_dist
            
            p1 = (ax + math.cos(angle) * 20, ay + math.sin(angle) * 20)
            p2 = (ax + math.cos(angle + 2.5) * 15, ay + math.sin(angle + 2.5) * 15)
            p3 = (ax + math.cos(angle - 2.5) * 15, ay + math.sin(angle - 2.5) * 15)
            
            pygame.draw.polygon(screen, GOLD_COLOR, [p1, p2, p3])

    # =========================================================
    # GLOBAL UI & PAUSE
    # =========================================================
    def handle_ui_event(self, event, current_state_key):
        """Käsittelee globaalit UI-tapahtumat (ESC, Pause-valikko)."""

        # --- IN-GAME DIALOGUE (ennen kaikkea muuta, myös ESC:iä) ---
        if self.active_dialogue:
            if self.handle_dialogue_event(event):
                return True

        # --- SAVE/LOAD-SLOTTIPANEELIN SYÖTE (pausen sisällä) ---
        # BUGIKORJAUS: tämä on käsiteltävä ENNEN inventory/hotkey-pikanäppäimiä,
        # muuten tallennuksen nimeä kirjoittaessa esim. 'i' avasi inventoryn
        # taustalle. Nimen kirjoitus kaappaa kaikki näppäimet.
        if self.paused and self.pause_panel_mode:
            handled = self._handle_pause_panel_event(event)
            if handled is not None:
                return handled

        # Inventory Toggle
        if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            # Estä inventoryn avaus Forest Roadilla (tarina-syyt)
            if current_state_key == "forest_road" and not CHEAT_MODE:
                sound_system.play_sound('error')
                return True

            self.show_inventory = not self.show_inventory
            sound_system.play_sound('click')
            return True

        if self.show_inventory:
            # ESC sulkee inventoryn (kuten I)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.show_inventory = False
                sound_system.play_sound('click')
                return True
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and event.button == 1:
                # Delegate to Commander
                self.player_character.handle_inventory_event(event, self)
            return True # Estä muut toiminnot kun inventory on auki

        # Hotbarin syöte (lukko, sivunuolet, pikatyökalut, raahaus)
        if self.player_character and not self.paused \
                and not self.active_dialogue and not self.show_inventory \
                and current_state_key in (QUEST_JOURNAL_STATES
                                          + ("battle", "game")):
            try:
                if self.player_character.handle_hotbar_event(event, self):
                    return True
            except Exception:
                pass

        # Täysi RPG-questijournal: avoinna kaappaa syötteen (pelitesti 27)
        if self.show_full_journal:
            if self._handle_full_journal_event(event):
                return True
            return True  # journal on modaalinen

        # HUD-trackerin raahaus: otsikkorivistä (pois lukien silmänappi)
        # voi vetää paneelin haluamaansa kohtaan. Sijainti säilyy saveen.
        if current_state_key in QUEST_JOURNAL_STATES \
                and self.show_quest_journal and not self.show_full_journal:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and self._journal_drag_handle is not None \
                    and self._journal_drag_handle.collidepoint(event.pos):
                self._journal_dragging = True
                r = self._journal_tracker_rect
                self._journal_drag_off = (event.pos[0] - r.x,
                                          event.pos[1] - r.y)
                return True
            if event.type == pygame.MOUSEMOTION and self._journal_dragging:
                ox, oy = self._journal_drag_off
                self.journal_tracker_pos = (event.pos[0] - ox,
                                            event.pos[1] - oy)
                return True
            if event.type == pygame.MOUSEBUTTONUP and self._journal_dragging \
                    and event.button == 1:
                self._journal_dragging = False
                try:
                    from systems.ui_prefs import set_quest_tracker_pos
                    set_quest_tracker_pos(self.journal_tracker_pos)
                except Exception:
                    pass
                return True

        # Quest journal: J avaa täyden journalin; silmänappi piilottaa
        # HUD-seurantapaneelin
        if current_state_key in QUEST_JOURNAL_STATES:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_j:
                self.show_full_journal = True
                self._journal_sync_selection()
                sound_system.play_sound('click')
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and self._journal_toggle_rect is not None \
                    and self._journal_toggle_rect.collidepoint(event.pos):
                self.show_quest_journal = not self.show_quest_journal
                sound_system.play_sound('click')
                return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Toggle pause (vain jos ei olla päävalikossa/latauksessa)
                # Tämän tarkistus tehdään main.py:ssä tai oletetaan että tätä kutsutaan vain pelitiloissa
                self.paused = not self.paused
                sound_system.play_sound('click')
                return True # Event handled

            # --- QUICKSAVE / QUICKLOAD ---
            if event.key == pygame.K_F5:
                self.save_current_game()
                return True
            if event.key == pygame.K_F9:
                if self.load_saved_game():
                    self.paused = False
                    return "muckford_city"  # suoraan pelimaailmaan
                return True

        if self.paused:
            # Pause-valikon napit toimivat pollauksella (_update_pause_menu),
            # eivät eventeillä. BUGIKORJAUS: kun valikko on auki ja klikkaa
            # (esim. RESUMEa tai tyhjää), hiiriklikkaus valui pelimaailmaan ja
            # hahmo löi LMB:llä. Kulutetaan kaikki eventit paussin ajaksi,
            # ettei mikään valu taustan combat-käsittelyyn.
            return True

        return None

    def _handle_pause_panel_event(self, event):
        """Save/Load-slottipaneelin syöte. Palauttaa True/str jos käsitelty,
        None jos event valuu normaalille käsittelylle."""
        import save_manager

        # Nimen syöttö (save)
        if self.pause_name_slot is not None:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.pause_name_slot = None
                    pygame.key.set_repeat()  # näppäintoisto pois
                    return True
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    name = self.pause_name_buffer.strip() or None
                    ok = save_manager.save_to_slot(self, self.pause_name_slot,
                                                   name or "")
                    self.save_feedback_msg = "Game Saved!" if ok else "Save Failed!"
                    self.save_feedback_timer = 120
                    sound_system.play_sound('click' if ok else 'error')
                    self.pause_name_slot = None
                    self.pause_panel_mode = None
                    pygame.key.set_repeat()  # näppäintoisto pois
                    return True
                if event.key == pygame.K_BACKSPACE:
                    self.pause_name_buffer = self.pause_name_buffer[:-1]
                    return True
                ch = getattr(event, "unicode", "")
                if ch and ch.isprintable() and len(self.pause_name_buffer) < 24:
                    self.pause_name_buffer += ch
                return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                return True
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.pause_panel_mode = None
            sound_system.play_sound('click')
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Poistonapit (X) ennen rivivalintaa
            for rect, slot in getattr(self, "pause_delete_rects", []):
                if rect.collidepoint(event.pos):
                    if getattr(self, "pause_delete_armed", None) == slot:
                        save_manager.delete_slot(slot)
                        self.pause_delete_armed = None
                        self.save_feedback_msg = "Save deleted."
                        self.save_feedback_timer = 120
                        sound_system.play_sound('click')
                    else:
                        self.pause_delete_armed = slot
                        sound_system.play_sound('hover')
                    return True
            for rect, slot in self.pause_slot_rects:
                if rect.collidepoint(event.pos):
                    if self.pause_panel_mode == "save":
                        if slot == 0:
                            sound_system.play_sound('error')
                            return True
                        # Aloita nimeäminen (oletusnimi = pelipäivä)
                        self.pause_name_slot = slot
                        clock = getattr(self, "world_clock", None)
                        default = ""
                        if clock is not None:
                            try:
                                default = (f"Day {clock.day_of_season} "
                                           f"{clock.get_time_string()}")
                            except Exception:
                                pass
                        self.pause_name_buffer = default
                        # BUGIKORJAUS: näppäintoisto päälle nimeä kirjoittaessa,
                        # jotta backspacea pohjassa pitäen pyyhkii jatkuvasti
                        # (ei tarvitse näpyttää). Nollataan kun nimeäminen loppuu.
                        pygame.key.set_repeat(300, 40)
                        sound_system.play_sound('click')
                        return True
                    else:  # load
                        rows = {r["slot"]: r for r in save_manager.list_slots()}
                        if not rows.get(slot, {}).get("exists"):
                            sound_system.play_sound('error')
                            return True
                        ok = (save_manager.load_game(self) if slot == 0 else
                              save_manager.load_from_slot(self, slot))
                        self.save_feedback_msg = ("Game Loaded!" if ok
                                                  else "Load Failed!")
                        self.save_feedback_timer = 120
                        sound_system.play_sound('click' if ok else 'error')
                        if ok:
                            self.paused = False
                            self.pause_panel_mode = None
                            return "muckford_city"
                        return True
            # Klikkaus paneelin ulkopuolelle sulkee
            self.pause_panel_mode = None
            return True
        return None

    def _draw_pause_panel(self, screen):
        """Save/Load-slottien piirto: nimi + pelipäivä + tallennusaika."""
        import save_manager
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        panel = pygame.Rect(cx - 360, cy - 300, 720, 600)
        surf = pygame.Surface(panel.size, pygame.SRCALPHA)
        surf.fill((16, 14, 12, 240))
        screen.blit(surf, panel.topleft)
        pygame.draw.rect(screen, (196, 158, 82), panel, 3, border_radius=14)
        title = "SAVE GAME - choose a slot" if self.pause_panel_mode == "save"             else "LOAD GAME - choose a slot"
        draw_text(title, font_main, GOLD_COLOR, screen, panel.x + 28,
                  panel.y + 20)
        draw_text("[ESC] back", font_small, GRAY, screen,
                  panel.right - 110, panel.y + 24)

        rows = save_manager.list_slots()
        if self.pause_panel_mode == "save":
            rows = [r for r in rows if r["slot"] != 0]
        self.pause_slot_rects = []
        self.pause_delete_rects = []
        y = panel.y + 70
        mouse = pygame.mouse.get_pos()
        for row in rows:
            rect = pygame.Rect(panel.x + 24, y, panel.w - 48, 78)
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(screen, (46, 40, 34) if hover else (30, 27, 24),
                             rect, border_radius=10)
            pygame.draw.rect(screen, (150, 122, 76), rect, 2, border_radius=10)
            slot_label = "QUICKSAVE (F5)" if row["slot"] == 0                 else f"SLOT {row['slot']}"
            draw_text(slot_label, font_small, (200, 180, 140), screen,
                      rect.x + 16, rect.y + 8)
            if self.pause_name_slot == row["slot"]:
                # Nimen syöttö käynnissä
                cursor = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else " "
                draw_text(f"Name: {self.pause_name_buffer}{cursor}",
                          font_main, WHITE, screen, rect.x + 16, rect.y + 34)
                draw_text("[ENTER] save   [ESC] cancel", font_small, GRAY,
                          screen, rect.right - 250, rect.y + 44)
            elif row["exists"]:
                draw_text(row["name"], font_main, WHITE, screen,
                          rect.x + 16, rect.y + 32)
                info = row["game_date"] or ""
                draw_text(info, font_small, (170, 200, 170), screen,
                          rect.x + 240, rect.y + 12)
                draw_text(f"saved {row['saved_at']}", font_small,
                          (150, 150, 160), screen, rect.x + 240, rect.y + 46)
            else:
                draw_text("- Empty -", font_main, (120, 120, 125), screen,
                          rect.x + 16, rect.y + 32)
            self.pause_slot_rects.append((rect, row["slot"]))
            # Poistonappi olemassa oleville tallennuksille
            if row["exists"] and self.pause_name_slot != row["slot"]:
                del_rect = pygame.Rect(rect.right - 50, rect.y + 20, 36, 36)
                armed = getattr(self, "pause_delete_armed", None) == row["slot"]
                pygame.draw.rect(screen, (120, 40, 34) if armed else (52, 34, 32),
                                 del_rect, border_radius=8)
                pygame.draw.rect(screen, (230, 110, 90), del_rect, 2,
                                 border_radius=8)
                xs = font_small.render("X", True, (255, 200, 190))
                screen.blit(xs, xs.get_rect(center=del_rect.center))
                self.pause_delete_rects.append((del_rect, row["slot"]))
            y += 88

    def _update_pause_menu(self, current_state_key):
        """Päivittää pause-valikon logiikan (napit). Kutsutaan draw_ui_overlaysta."""
        if self.btn_resume.update():
                self.paused = False
                return None

        # Slottipaneelin ollessa auki päänapit eivät reagoi
        if self.pause_panel_mode:
            return None

        if self.btn_save.update():
            self.pause_panel_mode = "save"
            sound_system.play_sound('click')
            return None

        if self.btn_load.update():
            self.pause_panel_mode = "load"
            sound_system.play_sound('click')
            return None

        if self.btn_options.update():
            self.paused = False
            return "options"

        # Hub-nappi: Vain jos sallittu
        allow_hub = True
        if current_state_key == "forest_road" and not CHEAT_MODE:
            allow_hub = False
            
        if allow_hub and self.btn_hub.update():
            self.paused = False
            return "hub"
            
        if self.btn_exit.update():
            return "exit"
            
        return None

    def draw_ui_overlay(self, screen, current_state_key):
        """Piirtää HUDin ja Pause-valikon."""

        # 0. Yleinen ilmoitus (esim. palkkaus estyi: punkat täynnä)
        if getattr(self, "hire_block_message", "") and \
                getattr(self, "_toast_timer", 0) > 0:
            self._toast_timer -= 1
            surf = font_small.render(self.hire_block_message, True, (255, 200, 150))
            box = pygame.Rect(SCREEN_WIDTH // 2 - surf.get_width() // 2 - 18,
                              88, surf.get_width() + 36, 44)
            pygame.draw.rect(screen, (26, 22, 20), box, border_radius=9)
            pygame.draw.rect(screen, (200, 140, 90), box, 2, border_radius=9)
            screen.blit(surf, (box.x + 18, box.y + 11))
            if self._toast_timer <= 0:
                self.hire_block_message = ""

        # 0.5 Kello näkyy myös sisätiloissa (pelaajapalaute: "mikä aika on?")
        if current_state_key in ("tavern_sunk_cask", "blacksmith_interior",
                                 "barracks_interior", "arena_hall",
                                 "town_hall") and not self.paused:
            try:
                self.world_clock.draw_hud(screen, font_small)
            except Exception:
                pass

        # 0.6 Quest journal -paneeli (J tai silmänappi piilottaa/näyttää)
        if current_state_key in QUEST_JOURNAL_STATES and not self.paused \
                and not self.active_dialogue and not self.show_inventory \
                and not self.show_full_journal:
            try:
                self._draw_quest_journal(screen)
            except Exception:
                pass

        # 0.65 Täysi RPG-journal (modaalinen overlay, pelitesti 27)
        if self.show_full_journal:
            try:
                self._draw_full_journal(screen)
            except Exception:
                pass

        # 1. COMMANDER HUD (Vain pelitiloissa)
        gameplay_states = ["muckford_city", "tavern_sunk_cask", "blacksmith_interior", "battle", "game"]
        if current_state_key in gameplay_states and self.player_character and not self.paused and not self.active_dialogue and not self.is_in_dialogue:
            # Taistelussa piirretään vain jos Commander on mukana
            if current_state_key in ["battle", "game"]:
                if self.player_character not in self.active_player_units:
                    return # Ei piirretä jos ei kentällä
            
            # --- DYNAMIC HUD TRANSPARENCY ---
            # Jos pelaaja on ruudun alareunassa (HUDin alla), muutetaan HUD läpinäkyväksi
            p_screen_y = self.player_character.rect.centery - self.camera_y
            hud_threshold = SCREEN_HEIGHT - 160 # HUDin arvioitu korkeus + marginaali
            
            if p_screen_y > hud_threshold:
                # Käytetään välimuistipintaa
                self.hud_surface.fill((0, 0, 0, 0))
                self.player_character.draw_hud(self.hud_surface)
                
                # Laske alpha (255 -> 40) mitä alemmas mennään
                dist = p_screen_y - hud_threshold
                max_dist = 100
                alpha = max(40, 255 - int((dist / max_dist) * 215))
                
                self.hud_surface.set_alpha(alpha)
                screen.blit(self.hud_surface, (0, 0))
            else:
                self.player_character.draw_hud(screen)
                
            # --- WORLD PAUSED INDICATOR ---
            if self.world_paused:
                draw_text("WORLD PAUSED (CHEAT)", font_title, (200, 50, 50), screen, SCREEN_WIDTH // 2 - 150, 100)

        # 2. INVENTORY
        if self.show_inventory:
            self.player_character.draw_inventory(screen, self)

        # 2. PAUSE MENU
        if self.paused:
            # --- 1. CALCULATE LAYOUT & UPDATE RECTS ---
            # Lasketaan sijainnit ENNEN update-kutsua, jotta napit ovat oikeassa paikassa
            cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            
            # Määritellään mitkä napit näkyvät
            show_hub = True
            if current_state_key == "forest_road" and not CHEAT_MODE:
                show_hub = False
            
            # Asettelu: näkyvät napit järjestyksessä
            visible_buttons = [self.btn_resume, self.btn_save, self.btn_load,
                               self.btn_options]
            if show_hub:
                visible_buttons.append(self.btn_hub)
            visible_buttons.append(self.btn_exit)

            btn_h = 60
            gap = 20
            content_h = len(visible_buttons) * (btn_h + gap)

            bg_w = 320 # Kapeampi (oli 530)
            bg_h = max(300, content_h + 100)
            bg_y = cy - bg_h // 2

            start_y = bg_y + 50 # Nostettu ylemmäs

            # Päivitä nappien sijainnit ja törmäysalueet (rect)
            current_y = start_y
            for btn in visible_buttons:
                btn.base_x = cx; btn.base_y = current_y
                btn.rect.topleft = (cx - btn.width // 2, current_y)
                current_y += 80

            # Päivitä logiikka tässä (koska SpriteButton vaatii jatkuvaa päivitystä)
            action = self._update_pause_menu(current_state_key)
            if action:
                # HACK: Koska olemme draw-loopissa, emme voi palauttaa tilaa suoraan main-looppiin helposti.
                # Mutta voimme asettaa sen manageriin ja main.py lukee sen?
                # Tai luotamme siihen että main.py kutsuu handle_ui_event... 
                # Mutta SpriteButton.update() palauttaa True vain yhdellä framella.
                # Tehdään niin että tallennetaan pending_state.
                self.pending_state_change = action

            from ui_kit import get_fullscreen_overlay
            screen.blit(get_fullscreen_overlay((0, 0, 0, 200)), (0, 0))

            # --- DRAW ESC FRAME ---
            if self.ui_esc_bg:
                scaled_bg = pygame.transform.smoothscale(self.ui_esc_bg, (bg_w, bg_h))
                bg_x = cx - bg_w // 2
                screen.blit(scaled_bg, (bg_x, bg_y))
                
                # Napit
                for btn in visible_buttons:
                    btn.draw(screen)
            else:
                # Fallback
                draw_text("PAUSED", font_title, GOLD_COLOR, screen, cx - 60, cy - 150)
                for btn in self.pause_buttons:
                    # SpriteButton draw hoitaa sijainnin jos se on asetettu
                    # Mutta tässä fallbackissa ne voivat olla missä vain.
                    # Asetetaan ne keskelle.
                    pass # (Oletetaan että esc.png löytyy, tai korjaa fallback myöhemmin)

            # Save/Load-slottipaneeli nappien päälle
            if self.pause_panel_mode:
                self._draw_pause_panel(screen)

            # Tarkista pending state change (HACK)
            if hasattr(self, "pending_state_change") and self.pending_state_change:
                # Tämä pitäisi käsitellä main loopissa.
                pass

        # --- SAVE/LOAD FEEDBACK (näkyy myös ilman pause-valikkoa, esim. F5) ---
        if self.save_feedback_timer > 0:
            self.save_feedback_timer -= 1
            msg_color = GOLD_COLOR if "Saved" in self.save_feedback_msg or "Loaded" in self.save_feedback_msg else (255, 80, 80)
            draw_text(self.save_feedback_msg, font_title, msg_color, screen,
                      SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 120)