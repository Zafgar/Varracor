# assets/tiles/editor_floors.py
"""Editorin lattialaatat (siirretty tools/map_editor.py:stä, jotta
karttalataus (systems/map_document.py) ei riipu editorista)."""
import pygame

from assets.tiles.prop import Prop


class StoneFloor(Prop):
    def __init__(self, x, y, variant=1):
        super().__init__(x, y, 40, 40, color=(60, 60, 65))
        self.rect = pygame.Rect(x, y, 0, 0)
        self.is_structure = False
        self.has_shadow = False
        self.is_floor = True


class WoodFloor(Prop):
    def __init__(self, x, y, variant=1):
        super().__init__(x, y, 40, 40, color=(80, 50, 30))
        self.rect = pygame.Rect(x, y, 0, 0)
        self.is_structure = False
        self.has_shadow = False
        self.is_floor = True


class GrassFloor(Prop):
    def __init__(self, x, y, variant=1):
        super().__init__(x, y, 40, 40, color=(40, 80, 40))
        self.rect = pygame.Rect(x, y, 0, 0)
        self.is_structure = False
        self.has_shadow = False
        self.is_floor = True
