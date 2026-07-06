import pygame

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

# --- GAME CONSTANTS ---
STARTING_GOLD = 100000
BASE_RECRUIT_COST = 80

# --- FONT SIZES ---
FONT_SIZE_UI = 20
FONT_SIZE_TITLE = 30

# --- DEBUG & CHEATS ---
# Kun tämä on True:
# - Paina 'L' Guild-valikossa -> Level Up
# - Paina 'M' Guild-valikossa -> Lisää rahaa
CHEAT_MODE = True

# --- ASSET CONFIGURATION ---
ENABLE_VIDEO_BACKGROUND = True # Set to False if video loading fails (e.g. codec issues)