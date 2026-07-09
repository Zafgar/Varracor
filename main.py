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
from menus.muckford_intro_screen import MuckfordIntroScreen
from minigames.crown_knives import CrownKnivesMenu
from menus.test_menu import TestMenu

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
        "muckford_intro": MuckfordIntroScreen(manager),
        "test_arena": TestMenu(manager)
    }
    
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
            if current_state_key not in ["menu", "loading", "match_loading"]:
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
                
                # --- State Transition Logic ---
                if old_key == "league" and new_key == "battle":
                    pass

                if new_key == "skill_tree":
                    if hasattr(manager, "selected_hero") and manager.selected_hero:
                        menus["skill_tree"].set_unit(manager.selected_hero)
                
                if new_key == "mission_select":
                    menus["mission_select"].selected_mission = None
                
                if new_key == "prepare":
                    menus["prepare"] = PrepareMenu(manager)

                if new_key == "mission_prepare":
                    menus["mission_prepare"] = MissionPrepareMenu(manager)
                
                if new_key == "loading":
                    menus["loading"] = LoadingScreen(manager)
                
                if new_key == "manager_menu":
                    menus["manager_menu"] = ManagerMenu(manager)
                
                if new_key == "commander_skills":
                    menus["commander_skills"] = CommanderSkillMenu(manager)
                
                if new_key == "workshop_locations":
                    menus["workshop_locations"] = WorkshopLocationMenu(manager)
                
                if new_key == "sponsors":
                    menus["sponsors"] = SponsorMenu(manager)
                
                if new_key == "reputation":
                    menus["reputation"] = ReputationMenu(manager)
                
                if new_key == "magic_school":
                    menus["magic_school"] = MagicSchoolMenu(manager)
                
                if new_key == "necro_school":
                    menus["necro_school"] = NecroSchoolMenu(manager)
                
                if new_key == "shop_locations":
                    menus["shop_locations"] = ShopLocationMenu(manager)
                
                if new_key == "city_storage":
                    menus["city_storage"] = CityStorageMenu(manager)
                
                # Re-init tavern only if NOT returning from dialogue (preserves state)
                if new_key == "tavern_sunk_cask" and old_key not in ["dialogue", "crown_knives"]:
                     menus["tavern_sunk_cask"] = TavernMenu(manager)

                # Init City
                if new_key == "muckford_city" and old_key != "dialogue":
                    if menus["muckford_city"] is None:
                        menus["muckford_city"] = MuckfordCityMenu(manager)
                    # Kutsu on_enter aina kun tullaan (paitsi dialogista palatessa)
                    if hasattr(menus["muckford_city"], "on_enter"):
                        menus["muckford_city"].on_enter()
                        
                # Init Blacksmith
                if new_key == "blacksmith_interior" and old_key != "dialogue":
                    if menus["blacksmith_interior"] is None:
                        menus["blacksmith_interior"] = BlacksmithMenu(manager)
                    if hasattr(menus["blacksmith_interior"], "on_enter"):
                        menus["blacksmith_interior"].on_enter()
                
                # Init Forest Road
                if new_key == "forest_road":
                    # Luo uusi vain jos ei ole olemassa.
                    # ÄLÄ luo uutta jos palataan dialogista, jotta tila säilyy.
                    if menus["forest_road"] is None:
                        menus["forest_road"] = ForestRoadMenu(manager)
                    menus["forest_road"].on_enter()

                if new_key == "muckford_intro":
                    menus["muckford_intro"] = MuckfordIntroScreen(manager)
                
                if new_key == "test_arena":
                    menus["test_arena"] = TestMenu(manager)
                    menus["test_arena"].on_enter()
                
                if new_key == "battle" or new_key == "game":
                    pass

                # --- MATCH LOADING SETUP ---
                if new_key == "match_loading":
                    if hasattr(manager, "pending_match_data"):
                        units, limit = manager.pending_match_data
                        menus["match_loading"].set_match_data(units, limit)
                
                if new_key == "crown_knives":
                    menus["crown_knives"].on_enter()

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