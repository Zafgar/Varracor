# bosses/rat_king/mission.py
import pygame
import os

# --- KORJAUS: Haetaan hahmot UUSISTA eriytetyistä tiedostoista ---
from units.rat_king import RatKing  # Boss haetaan omasta tiedostostaan
from units.rat import GiantRat      # Minion haetaan yleisestä rottatiedostosta

# Lair on edelleen tässä kansiossa, joten piste (.) toimii
from .lair import RatKingLair

# --- TALLENNETAAN ÄÄNI TÄHÄN ---
active_ambient = None

def setup(gamemanager):
    print("--- EXECUTE: Rat King Mission Setup ---")
    
    # 1. Käynnistä äänet
    setup_audio()
    
    # 2. Aseta Arena
    gamemanager.current_arena = RatKingLair()
    
    # 3. Tyhjennä ja luo viholliset
    gamemanager.enemy_team.empty()
    
    # --- Boss Setup ---
    # Lasketaan ruudun keskikohta
    screen_w = gamemanager.screen_width if hasattr(gamemanager, 'screen_width') else 1280
    screen_h = gamemanager.screen_height if hasattr(gamemanager, 'screen_height') else 720
    
    boss_x = screen_w // 2
    boss_y = screen_h // 2 - 100

    boss = RatKing("The Rat King", boss_x, boss_y)
    boss.assign_manager(gamemanager)
    
    gamemanager.enemy_team.add(boss)
    gamemanager.all_units.add(boss) 
    
    # --- Minion Setup ---
    spawn_points = gamemanager.current_arena.spawn_points
    
    if len(spawn_points) >= 3:
        rat1 = GiantRat("Sewer Rat 1", spawn_points[0][0], spawn_points[0][1])
        rat2 = GiantRat("Sewer Rat 2", spawn_points[2][0], spawn_points[2][1])
        
        gamemanager.enemy_team.add(rat1)
        gamemanager.all_units.add(rat1)
        
        gamemanager.enemy_team.add(rat2)
        gamemanager.all_units.add(rat2)
    else:
        for i in range(2):
            minion = GiantRat(f"Sewer Rat {i+1}", boss_x + (i*60) - 30, boss_y + 150)
            gamemanager.enemy_team.add(minion)
            gamemanager.all_units.add(minion)
        
    print(f"Spawned Boss + {len(gamemanager.enemy_team)-1} minions.")

def setup_audio():
    """Lataa ja soittaa taustamusiikin ja ambient-äänet"""
    global active_ambient
    
    # 1. MUSIIKKI
    music_file = "assets/music/rat_boss_theme.wav" 
    
    if os.path.exists(music_file):
        try:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(0.5) 
            pygame.mixer.music.play(-1) 
            print(f"Playing music: {music_file}")
        except Exception as e:
            print(f"Error loading music: {e}")
    else:
        print(f"Music not found: {music_file}")

    # 2. AMBIENT
    ambient_file = "assets/sounds/sewer_ambience.wav" 
    
    if os.path.exists(ambient_file):
        try:
            if active_ambient:
                active_ambient.stop()
                
            active_ambient = pygame.mixer.Sound(ambient_file)
            active_ambient.set_volume(0.3) 
            active_ambient.play(loops=-1) 
            print(f"Playing ambient: {ambient_file}")
        except Exception as e:
            print(f"Error loading ambient: {e}")
    else:
        print(f"Ambient sound not found: {ambient_file}")

def cleanup():
    """Kutsu tätä GameManagerista kun taistelu loppuu!"""
    print("Cleaning up Rat King mission audio...")
    
    # 1. Sammuta musiikki
    pygame.mixer.music.fadeout(1000)
    
    # 2. Sammuta ambient-ääni
    global active_ambient
    if active_ambient:
        active_ambient.stop()
        active_ambient = None