import random
from settings import *
from sound_manager import sound_system
from units.rat_king import RatKing
from units.rat import GiantRat
import maps.rat_sewer.vfx as rs_vfx

class MissionLogic:
    def __init__(self, mission_data):
        self.data = mission_data
        self.pending_enemies = []
        self.spawn_timer = 0

    def setup(self, manager):
        # Tyhjennetään vanhat viholliset varmuuden vuoksi
        manager.enemy_team.empty()
        manager.all_units.empty()
        for u in manager.active_player_units: manager.all_units.add(u)

        # Soitetaan boss-musiikki jos kyseessä on Rat King
        if self.data.get('id') == "boss_rat_king":
            sound_system.play_music('assets/music/rat_boss_theme.wav')

        if self.data.get('id') == "boss_rat_king":
            # --- BOSS SETUP ---
            boss_x = manager.current_arena.width // 2
            boss_y = manager.current_arena.height // 2
            
            king = RatKing("Rat King", boss_x, boss_y)
            king.assign_manager(manager)
            manager.enemy_team.add(king)
            manager.all_units.add(king)
            
            # Lisätään pari alkurottaa
            for _ in range(2):
                sp = manager.current_arena.get_spawn_point()
                minion = GiantRat("Minion", sp[0], sp[1], team_color=king.team_color)
                manager.enemy_team.add(minion)
                manager.all_units.add(minion)
        else:
            # --- NORMAL MONSTER HUNT ---
            enemy_list = self.data.get('enemies', [])
            for name, qty in enemy_list:
                for _ in range(qty):
                    self.pending_enemies.append(name)
            random.shuffle(self.pending_enemies)

        # Pelaaja keskelle
        manager._position_units_center(list(manager.active_player_units), manager.current_arena.width // 2, manager.current_arena.height // 2)

    def update(self, manager):
        if self.pending_enemies:
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                name = self.pending_enemies.pop(0)
                enemy = manager.create_enemy_by_name(name)
                if enemy:
                    pos = manager.current_arena.get_spawn_point()
                    enemy.rect.center = pos
                    manager.enemy_team.add(enemy)
                    manager.all_units.add(enemy)
                    if manager.vfx: manager.vfx.create_spawn_fog(pos[0], pos[1])
                self.spawn_timer = 60

    def is_finished(self, manager):
        return len(self.pending_enemies) == 0

def setup(manager):
    """Tätä kutsutaan boss_registryn kautta"""
    import maps.rat_sewer.arena as rs_arena
    manager.current_arena = rs_arena.Arena()
    manager.current_mission_logic = MissionLogic(manager.selected_mission)
    manager.current_map_vfx = rs_vfx.MapVFX()
    manager.current_mission_logic.setup(manager)
