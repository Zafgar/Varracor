import pygame
from menus.gameplay_screen import GameplayScreen
from assets.tiles.test_arena import TestArena
from assets.tiles.vfx import MapVFX
from sound_manager import sound_system
from ui_kit import draw_text, font_title, WHITE

class TestMenu(GameplayScreen):
    def __init__(self, manager):
        super().__init__(manager)
        self.arena = TestArena()
        # Varmistetaan, että areenalla on VFX-instanssi
        if not hasattr(self.arena, 'vfx') or self.arena.vfx is None:
            self.arena.vfx = MapVFX()
        
        self.player = self.manager.player_character

    def on_enter(self):
        super().on_enter()
        self.manager.current_arena = self.arena
        self.manager.current_map_vfx = self.arena.vfx
        
        # Keskitä pelaaja
        if self.player:
            self.player.rect.center = (self.arena.width//2, self.arena.height//2)
        self._update_camera()
        
        # Pysäytä kaikki äänet testitilassa
        sound_system.stop_music()
        pygame.mixer.stop()
        
        # Enable editor by default
        if hasattr(self, "map_editor") and not self.map_editor.active:
            self.map_editor.toggle()

    def update(self):
        # Kerää kaikki yksiköt (Pelaaja + Propit + Mahdolliset viholliset)
        all_units = []
        if self.player:
            all_units.append(self.player)
        all_units.extend(self.arena.props)
        
        if hasattr(self.arena, "enemies"):
            all_units.extend(self.arena.enemies)
            
        # Päivitä pelilogiikka (GameplayScreen hoitaa editorin päivityksen ja pause-tarkistuksen)
        self._update_gameplay(all_units)

    def draw(self, screen):
        screen.fill((20, 20, 25))
        
        # Kerää piirrettävät (GameplayScreen hoitaa Y-lajittelun)
        all_units = []
        if self.player:
            all_units.append(self.player)
        all_units.extend(self.arena.props)
        
        if hasattr(self.arena, "enemies"):
            all_units.extend(self.arena.enemies)
            
        # Piirrä (GameplayScreen hoitaa editorin piirron)
        self._draw_gameplay(screen, all_units)
        
        # Draw overlay text if editor is NOT active (to remind user)
        if hasattr(self, "map_editor") and not self.map_editor.active:
            draw_text("TEST MODE - Press F8 for Editor", font_title, WHITE, screen, 20, 20)