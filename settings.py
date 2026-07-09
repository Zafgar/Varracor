import pygame
import sys

# --- SCREEN SETTINGS ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

# --- COLORS ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)
GOLD_COLOR = (255, 215, 0)
ORANGE = (255, 165, 0)
PURPLE = (150, 50, 200) # Quest / Boss väri

# Tiimivärit. Käytä AINA näitä vakioita team_color-vertailuissa,
# älä koskaan kovakoodattua väriarvoa.
PLAYER_TEAM = GREEN
ENEMY_TEAM = (255, 50, 50)

# --- DEBUG & CHEATS ---
# Käynnistä peli cheat-tilassa: python main.py --cheat  (tai PLAY_DEV.bat)
# Kun tämä on True:
# - Paina 'L' Guild-valikossa -> Level Up
# - Paina 'M' Guild-valikossa -> Lisää rahaa
# - F8 avaa karttaeditorin
CHEAT_MODE = "--cheat" in sys.argv

# --- GAME CONSTANTS ---
STARTING_GOLD = 100000 if CHEAT_MODE else 500
BASE_RECRUIT_COST = 80

# --- FONT SIZES ---
FONT_SIZE_UI = 20
FONT_SIZE_TITLE = 30

# --- ASSET CONFIGURATION ---
ENABLE_VIDEO_BACKGROUND = True # Set to False if video loading fails (e.g. codec issues)