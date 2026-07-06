import random
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, RED
from sound_manager import sound_system
from units.rat import GiantRat
from units.rat_king import RatKing

class MissionLogic:
    def __init__(self, mission_data):
        self.mission_data = mission_data
        self.handles_positioning = True
        
        self.max_waves = 15
        self.current_wave = 0
        self.active = True
        self.wave_in_progress = False
        
        self.wave_delay_timer = 0
        self.announcement_timer = 0
        self.announcement_text = ""
        
        self.total_rewards = {"gold": 0, "xp": 0, "items": []}

    def setup(self, manager):
        self.manager = manager
        # Musiikki (Käytetään Bog/Swamp teemaa toistaiseksi)
        try: sound_system.play_music('assets/music/swamp_theme.mp3')
        except: sound_system.play_music('assets/music/battle_theme.mp3')

        # Pelaaja keskelle pääkatua
        cx, cy = manager.current_arena.width // 2, manager.current_arena.height // 2
        
        if manager.player_character:
            pc = manager.player_character
            if pc not in manager.active_player_units:
                manager.active_player_units.add(pc)
                manager.all_units.add(pc)
                pc.is_dead = False
                pc.current_hp = pc.max_hp
        
        manager._position_units_center(list(manager.active_player_units), cx, cy)
        manager.camera_x = cx - SCREEN_WIDTH // 2
        manager.camera_y = cy - SCREEN_HEIGHT // 2

        # Lisää kartan propit
        if manager.current_arena and hasattr(manager.current_arena, "props"):
            for p in manager.current_arena.props:
                manager.all_units.add(p)

        self.start_next_wave(manager)

    def start_next_wave(self, manager):
        if self.current_wave >= self.max_waves:
            self.finish_mission(manager, completed=True)
            return

        self.current_wave += 1
        self.wave_in_progress = True
        
        self.announcement_text = f"WAVE {self.current_wave}"
        self.announcement_timer = 180
        
        # --- SPAWN LOGIC ---
        enemy_count = 5 + int(self.current_wave * 1.5)
        
        # Boss Wave (Rat King)
        spawn_boss = (self.current_wave == 10)
        
        print(f"--- MUCKFORD WAVE {self.current_wave} (Enemies: {enemy_count}) ---")
        
        # Haetaan viemärit areenalta
        spawns = getattr(manager.current_arena, "enemy_spawns", [])
        if not spawns: spawns = [(100, 100)] # Fallback

        for i in range(enemy_count):
            spot = random.choice(spawns)
            x = spot[0] + random.randint(-20, 20)
            y = spot[1] + random.randint(-20, 20)
            
            if hasattr(manager, "vfx"):
                manager.vfx.create_spawn_fog(x, y)
            
            unit = GiantRat(f"Sewer Rat {i+1}", x, y, team_color=RED)
            # Skaalataan vaikeutta
            unit.max_hp += self.current_wave * 5
            unit.current_hp = unit.max_hp
            
            manager.enemy_team.add(unit)
            manager.all_units.add(unit)

        if spawn_boss:
            bx, by = spawns[0]
            boss = RatKing("The Rat King", bx, by)
            boss.assign_manager(manager)
            manager.enemy_team.add(boss)
            manager.all_units.add(boss)
            self.announcement_text = "THE RAT KING APPEARS!"

    def on_wave_cleared(self, manager):
        self.wave_in_progress = False
        self.wave_delay_timer = 120
        
        gold = 20 + (self.current_wave * 5)
        exp = 40 + (self.current_wave * 10)
        
        self.total_rewards["gold"] += gold
        self.total_rewards["xp"] += exp
        
        if hasattr(manager, "add_material"):
            manager.add_material("Scrap Iron", random.randint(1, 3))

    def update(self, manager):
        if self.announcement_timer > 0: self.announcement_timer -= 1
        if self.wave_delay_timer > 0:
            self.wave_delay_timer -= 1
            if self.wave_delay_timer <= 0:
                self.start_next_wave(manager)
            return

        enemies_alive = sum(1 for e in manager.enemy_team if not getattr(e, "is_dead", False))
        if enemies_alive == 0 and self.wave_in_progress:
            self.on_wave_cleared(manager)

    def is_finished(self, manager): return not self.active
    def retreat(self): self.finish_mission(self.manager, completed=True)
    def finish_mission(self, manager, completed=False):
        self.active = False
        manager.match_over = True
        manager.match_result = "RETREAT" if completed else "DEFEAT"
        manager.round_rewards = {"gold": self.total_rewards["gold"], "xp": self.total_rewards["xp"], "loot": manager.round_rewards.get("loot", {}), "wave": self.current_wave}