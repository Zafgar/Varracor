import pygame
import sys
from settings import *
from game_manager import GameManager
from sound_manager import sound_system

# --- MENU IMPORTS ---
from menus.magic_menu import MagicMenu
from menus.main_menu import MainMenu
from menus.town_hub import TownHub      
from menus.shop_menu import ShopMenu
from menus.recruit_menu import RecruitMenu
from menus.mission_menu import MissionMenu
from menus.prepare_menu import PrepareMenu 
from menus.battle_screen import BattleScreen
from menus.guild_menu import GuildMenu
from menus.hospital_menu import HospitalMenu
from menus.post_battle_menu import BattleReportMenu, LootScreenMenu, SwarmReportMenu
from menus.workshop_menu import WorkshopMenu
from menus.quest_menu import QuestMenu
from menus.skill_tree_menu import SkillTreeMenu
from menus.league_menu import LeagueMenu 
from menus.hall_of_fame_menu import HallOfFameMenu
from menus.chat_menu import ChatMenu  
from menus.promotion_menu import PromotionMenu
from menus.squad_select_menu import SquadSelectMenu # <--- UUSI IMPORT
from menus.mission_prepare_menu import MissionPrepareMenu
from menus.loading_screen import LoadingScreen
from menus.manager_menu import ManagerMenu
from menus.commander_skill_menu import CommanderSkillMenu
from menus.workshop_location_menu import WorkshopLocationMenu
from menus.sponsor_menu import SponsorMenu
from menus.reputation_menu import ReputationMenu
from menus.magic_school_menu import MagicSchoolMenu
from menus.necro_school_menu import NecroSchoolMenu
from menus.intro_screen import IntroScreen
from menus.shop_location_menu import ShopLocationMenu
from menus.match_loading_screen import MatchLoadingScreen
from citys.mucford.tavern_menu import TavernMenu
from citys.mucford.muckford_city_menu import MuckfordCityMenu
from citys.mucford.blacksmith_menu import BlacksmithMenu
from menus.city_storage_menu import CityStorageMenu
from citys.mucford.forest_road_menu import ForestRoadMenu
from citys.mucford.mine_road_menu import MineRoadMenu
from citys.mucford.mine_cave_menu import MineCaveMenu
from menus.muckford_intro_screen import MuckfordIntroScreen
from minigames.crown_knives import CrownKnivesMenu
from menus.test_menu import TestMenu
from menus.options_menu import OptionsMenu
from menus.barracks_menu import BarracksMenu
from menus.notice_board_menu import NoticeBoardMenu
from menus.market_menu import MarketMenu

pygame.init()
# SCALED skaalaa 1920x1080-pelin automaattisesti näytön kokoon (pienemmätkin näytöt toimivat)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
pygame.display.set_caption("AutoArena: Gladiator Tycoon")
clock = pygame.time.Clock()

def main():
    manager = GameManager()
    
    # Musiikki
    try:
        sound_system.play_music('assets/sounds/battle_theme.mp3')
    except Exception:
        pass

    # --- ALUSTETAAN VALIKOT ---
    battle_screen = BattleScreen(manager)  # Yksi jaettu instanssi ("game" ja "battle" ovat sama tila)
    menus = {
        "menu": MainMenu(manager),
        "intro": IntroScreen(manager),
        "hub": TownHub(manager),
        "shop": ShopMenu(manager),
        "recruit": RecruitMenu(manager),
        "magic_shop": MagicMenu(manager),
        "mission_select": MissionMenu(manager),
        "prepare": PrepareMenu(manager),
        "game": battle_screen,
        "battle": battle_screen,
        "guild": GuildMenu(manager),
        "hospital": HospitalMenu(manager),
        "workshop": WorkshopMenu(manager),
        "quests": QuestMenu(manager),
        "battle_report": BattleReportMenu(manager),
        "loot_screen": LootScreenMenu(manager),
        "swarm_report": SwarmReportMenu(manager),
        "skill_tree": SkillTreeMenu(manager),
        "league": LeagueMenu(manager),
        "hall_of_fame": HallOfFameMenu(manager),
        "promotion_ceremony": PromotionMenu(manager),
        "dialogue": None,
        "squad_select": None, # Placeholder
        "mission_prepare": MissionPrepareMenu(manager),
        "loading": LoadingScreen(manager),
        "manager_menu": ManagerMenu(manager),
        "commander_skills": CommanderSkillMenu(manager),
        "workshop_locations": WorkshopLocationMenu(manager),
        "sponsors": SponsorMenu(manager),
        "reputation": ReputationMenu(manager),
        "magic_school": MagicSchoolMenu(manager),
        "necro_school": NecroSchoolMenu(manager),
        "shop_locations": ShopLocationMenu(manager),
        "match_loading": MatchLoadingScreen(manager),
        "crown_knives": CrownKnivesMenu(manager),
        "tavern_sunk_cask": None, # Alustetaan tyhjäksi
        "muckford_city": None, # Alustetaan tyhjäksi
        "blacksmith_interior": None, # Alustetaan tyhjäksi
        "city_storage": CityStorageMenu(manager),
        "forest_road": ForestRoadMenu(manager),
        "mine_road": None, # Luodaan tarvittaessa
        "mine_cave": None, # Luodaan tarvittaessa
        "muckford_intro": MuckfordIntroScreen(manager),
        "test_arena": TestMenu(manager),
        "options": OptionsMenu(manager),
        "barracks": BarracksMenu(manager),
        "notice_board": NoticeBoardMenu(manager),
        "market": MarketMenu(manager)
    }
    
    # =========================================================
    # TILASIIRTYMÄSÄÄNNÖT (datavetoinen — uusi valikko ei vaadi
    # muutoksia itse tilakoneeseen, vain rivin näihin tauluihin)
    # =========================================================

    # Millä luokalla tila luodaan (uudelleen)luonnissa
    MENU_FACTORIES = {
        "prepare": PrepareMenu,
        "mission_prepare": MissionPrepareMenu,
        "loading": LoadingScreen,
        "manager_menu": ManagerMenu,
        "commander_skills": CommanderSkillMenu,
        "workshop_locations": WorkshopLocationMenu,
        "sponsors": SponsorMenu,
        "reputation": ReputationMenu,
        "magic_school": MagicSchoolMenu,
        "necro_school": NecroSchoolMenu,
        "shop_locations": ShopLocationMenu,
        "city_storage": CityStorageMenu,
        "muckford_intro": MuckfordIntroScreen,
        "test_arena": TestMenu,
        "options": OptionsMenu,
        "barracks": BarracksMenu,
        "notice_board": NoticeBoardMenu,
        "market": MarketMenu,
        "tavern_sunk_cask": TavernMenu,
        "muckford_city": MuckfordCityMenu,
        "blacksmith_interior": BlacksmithMenu,
        "forest_road": ForestRoadMenu,
        "mine_road": MineRoadMenu,
        "mine_cave": MineCaveMenu,
    }

    # Luodaan aina uusi instanssi tilaan tultaessa
    RECREATE_ALWAYS = {
        "prepare", "mission_prepare", "loading", "manager_menu",
        "commander_skills", "workshop_locations", "sponsors", "reputation",
        "magic_school", "necro_school", "shop_locations", "city_storage",
        "muckford_intro", "test_arena", "options", "market", "barracks", "notice_board",
    }

    # Luodaan uusi PAITSI jos tullaan näistä tiloista (tila säilyy)
    RECREATE_UNLESS_FROM = {
        "tavern_sunk_cask": {"dialogue", "crown_knives"},
    }

    # Luodaan vain jos instanssia ei vielä ole
    CREATE_IF_MISSING = {"muckford_city", "blacksmith_interior", "forest_road", "mine_road", "mine_cave"}

    # Tiloille kutsutaan on_enter() tultaessa
    CALL_ON_ENTER = {
        "muckford_city", "blacksmith_interior", "forest_road", "mine_road",
        "mine_cave", "test_arena", "crown_knives",
    }

    # Näistä tiloista tultaessa EI tehdä alustusta lainkaan
    # (esim. dialogista palatessa kaupungin tila säilyy)
    SKIP_INIT_FROM = {
        "muckford_city": {"dialogue"},
        "blacksmith_interior": {"dialogue"},
    }

    def enter_state(new_key, old_key):
        """Alustaa tilan siirtymäsääntöjen mukaan."""
        # Nollaa valikon rekisteröimä dialogikäsittelijä kun poistutaan sen
        # piiristä. (Dialogisiirtymät eivät kulje tämän funktion kautta,
        # ja crown_knives/tavern säilyttävät tavernan käsittelijän.)
        if new_key not in ("crown_knives", "tavern_sunk_cask"):
            manager.dialogue_action_handler = None

        # Options-valikko muistaa mistä tilasta tultiin
        if new_key == "options" and old_key != "options":
            manager.options_return_state = old_key

        if old_key in SKIP_INIT_FROM.get(new_key, ()):
            pass  # Säilytä vanha tila sellaisenaan
        else:
            factory = MENU_FACTORIES.get(new_key)
            recreate = (
                new_key in RECREATE_ALWAYS
                or (new_key in RECREATE_UNLESS_FROM
                    and old_key not in RECREATE_UNLESS_FROM[new_key])
            )
            if factory and (recreate or (new_key in CREATE_IF_MISSING and menus[new_key] is None)):
                menus[new_key] = factory(manager)
            if new_key in CALL_ON_ENTER and hasattr(menus[new_key], "on_enter"):
                menus[new_key].on_enter()

        # --- Tilakohtaiset erikoisalustukset ---
        if new_key == "skill_tree":
            if getattr(manager, "selected_hero", None):
                menus["skill_tree"].set_unit(manager.selected_hero)

        if new_key == "mission_select":
            menus["mission_select"].selected_mission = None

        if new_key == "match_loading":
            if hasattr(manager, "pending_match_data"):
                units, limit = manager.pending_match_data
                menus["match_loading"].set_match_data(units, limit)

    current_state_key = "menu"
    current_menu = menus[current_state_key]

    running = True
    while running:
        # 1. INPUT
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            # --- GLOBAL UI (Pause & HUD) ---
            # Vain pelitiloissa (ei päävalikossa)
            if current_state_key not in ["menu", "loading", "match_loading", "options"]:
                ui_response = manager.handle_ui_event(event, current_state_key)
                if ui_response:
                    if isinstance(ui_response, str):
                        if ui_response == "exit": running = False
                        else: current_menu.next_state = ui_response
                    continue # Estä valikon omat eventit jos UI käsitteli (esim. pause)
            
            # Safety check before handle_event
            if current_menu is None:
                print("CRITICAL: current_menu is None in event loop! Resetting to Hub.")
                current_state_key = "hub"
                current_menu = menus["hub"]
                continue

            # Käsittele eventit ja katso palauttaako se uuden tilan
            response = current_menu.handle_event(event)
            if response and isinstance(response, str):
                current_menu.next_state = response

        # 2. UPDATE & DRAW
        if not manager.paused:
            update_response = current_menu.update()
            if update_response and isinstance(update_response, str):
                current_menu.next_state = update_response

        current_menu.draw(screen)
        
        # --- DRAW GLOBAL UI ---
        manager.draw_ui_overlay(screen, current_state_key)
        
        # --- CHECK PAUSE MENU ACTIONS ---
        # Koska SpriteButton päivittyy draw_ui_overlay:ssa, tarkistetaan tulos tässä
        if hasattr(manager, "pending_state_change") and manager.pending_state_change:
            req = manager.pending_state_change
            manager.pending_state_change = None
            if req == "exit": running = False
            else: current_menu.next_state = req
        
        # 3. STATE MACHINE
        if current_menu.next_state:
            new_key = current_menu.next_state
            old_key = current_state_key
            
            # --- LOADING SCREEN INTERCEPT ---
            # Pakota latausruutu kun mennään Tavernaan/Kaupunkiin tai sieltä pois
            # (Ei kuitenkaan dialogin, taistelun tai itse latauksen yhteydessä)
            heavy_states = ["tavern_sunk_cask", "muckford_city", "blacksmith_interior"]
            
            # Tarkistetaan onko kyseessä dialogi-siirtymä
            is_dialogue_transition = new_key == "dialogue" or new_key == "dialogue_active" or new_key.startswith("dialogue:")
            
            # 1. Mennään raskaaseen tilaan (esim. Hub -> Tavern)
            if new_key in heavy_states and old_key != "loading" and old_key != "dialogue":
                manager.loading_target_state = new_key
                new_key = "loading"
            
            # 2. Lähdetään raskaasta tilasta (esim. Tavern -> Hub/City)
            elif old_key in heavy_states and new_key not in ["loading", "battle", "game"] and not is_dialogue_transition and new_key not in heavy_states:
                manager.loading_target_state = new_key
                new_key = "loading"

            # --- UUSI: SQUAD SELECT ---
            if new_key.startswith("squad_select:"):
                current_menu.next_state = None
                parts = new_key.split(":")
                mission_id = parts[1]
                
                # Luodaan menu dynaamisesti tälle tehtävälle
                menus["squad_select"] = SquadSelectMenu(manager, mission_id)
                
                current_state_key = "squad_select"
                current_menu = menus["squad_select"]
                current_menu.next_state = None
                continue

            # --- DIALOGIN AVAUS ---
            if new_key.startswith("dialogue:"):
                current_menu.next_state = None 
                npc_id = new_key.split(":")[1]
                
                dialogue_menu = manager.open_dialogue(npc_id)
                
                if dialogue_menu:
                    menus["dialogue"] = dialogue_menu
                    # Aseta paluuosoite automaattisesti vanhaan tilaan
                    dialogue_menu.return_state = old_key
                        
                    current_state_key = "dialogue"
                    current_menu = menus["dialogue"]
                else:
                    print(f"Error: Could not load dialogue for {npc_id}")
                continue 

            # --- DYNAMIC DIALOGUE (Patrons / Recruits) ---
            if new_key == "dialogue_active":
                current_menu.next_state = None
                if manager.pending_dialogue_menu:
                    menus["dialogue"] = manager.pending_dialogue_menu
                    manager.pending_dialogue_menu = None
                    current_state_key = "dialogue"
                    current_menu = menus["dialogue"]
                else:
                    print("Error: No pending dialogue menu found for 'dialogue_active'.")
                continue

            # --- NORMAALI VAIHTO ---
            if new_key == "exit":
                running = False

            # --- CLEANUP OLD STATE ---
            if hasattr(current_menu, "on_exit"):
                current_menu.on_exit()

            if new_key in menus:
                current_menu.next_state = None

                # Alusta uusi tila siirtymäsääntöjen mukaan
                enter_state(new_key, old_key)

                current_state_key = new_key
                current_menu = menus[new_key]
                
                # Safety check: Jos valikko on None (alustus epäonnistui), palataan Hubiin
                if current_menu is None:
                    print(f"CRITICAL ERROR: State '{new_key}' initialized to None! Falling back to Hub.")
                    current_state_key = "hub"
                    current_menu = menus["hub"]
                
                # Varmistetaan, että uuden valikon tila on puhdas (jos se on vanha instanssi)
                current_menu.next_state = None
                
            else:
                print(f"CRITICAL ERROR: State '{new_key}' not found!")
                current_menu.next_state = None 

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()