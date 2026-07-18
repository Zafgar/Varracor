import random
import pygame
import os
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, RED, GREEN
from sound_manager import sound_system

# Oikeat yksiköt
from units.bog_leech import BogLeech
from units.giant_frog import GiantFrog
from units.corrupted_crow import CorruptedCrow

class MissionLogic:
    def __init__(self, mission_data):
        self.mission_data = mission_data
        self.handles_positioning = True
        
        self.max_waves = 20
        self.current_wave = 0
        self.active = True
        self.wave_in_progress = False
        
        self.wave_delay_timer = 0
        self.announcement_timer = 0
        self.announcement_text = ""
        
        self.total_rewards = {"gold": 0, "xp": 0, "items": []}

    def setup(self, manager):
        self.manager = manager
        # Soita suomusiikkia jos on (fallback crypt theme)
        music_candidates = [
            'assets/music/swamp_theme.mp3', 'assets/music/swamp_theme.wav',
            'assets/music/swamp_loop.mp3', 'assets/music/swamp_loop.wav'
        ]
        music_found = False
        for m in music_candidates:
            if os.path.exists(m):
                sound_system.play_music(m)
                music_found = True
                break
        
        if not music_found:
            sound_system.play_music('assets/music/crypt_theme.wav')

        # Pelaaja aloittaa SISÄÄNKÄYNNILTÄ (lounainen porttikyltti)
        cx, cy = getattr(
            manager.current_arena, "entrance_point",
            (manager.current_arena.width // 2,
             manager.current_arena.height // 2))

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

        # Lisää kartan propit (puut yms) peliin
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
        enemy_count = 6 + int(self.current_wave * 2.0) # Enemmän vihollisia
        if enemy_count > 45: enemy_count = 45 # Korkeampi katto
        
        print(f"--- BOG WAVE {self.current_wave} (Enemies: {enemy_count}) ---")
        
        arena = manager.current_arena
        w, h = arena.width, arena.height

        # Aallot nousevat MAASTOSTA (arena.spawn_zones: lampien takamaat,
        # pesän edusta) - ei satunnaisesti pelaajan niskaan tai veteen
        zones = getattr(arena, "spawn_zones", None)
        spawn_spots = []
        if zones:
            for _ in range(8):
                zone = random.choice(zones)
                spawn_spots.append((random.randint(zone.left, zone.right),
                                    random.randint(zone.top, zone.bottom)))
        else:
            margin = 300
            for _ in range(8):
                spawn_spots.append((random.randint(margin, w - margin),
                                    random.randint(margin, h - margin)))

        for i in range(enemy_count):
            # Valitaan yksi pisteistä
            spot = random.choice(spawn_spots)
            # Pieni hajonta pisteen ympärille
            x = spot[0] + random.randint(-50, 50)
            y = spot[1] + random.randint(-50, 50)
            
            # Visuaalinen efekti spawnille (jos manager tukee)
            if hasattr(manager, "vfx"):
                manager.vfx.create_spawn_fog(x, y)
            
            # --- UNIT SELECTION ---
            roll = random.random()
            unit = None
            
            if self.current_wave >= 3 and roll < 0.35: # 35% Crow wave 3+
                unit = CorruptedCrow(f"Crow {i+1}", x, y, team_color=RED)
            elif self.current_wave >= 3 and roll < 0.6: # Frog wave 3+
                unit = GiantFrog(f"Frog {i+1}", x, y, team_color=RED)
            else:
                unit = BogLeech(f"Leech {i+1}", x, y, team_color=RED)
            
            manager.enemy_team.add(unit)
            manager.all_units.add(unit)

    def on_wave_cleared(self, manager):
        self.wave_in_progress = False
        self.wave_delay_timer = 120
        
        gold = 25 + (self.current_wave * 10)
        exp = 50 + (self.current_wave * 20)
        
        # --- LOOT DROPS (Swamp Resources) ---
        swamp_loot = ["Slime Goo", "Nightcap Fungus"]
        if self.current_wave >= 5: swamp_loot.append("Vortex Residue")
        
        # Chance to get loot every wave (70%)
        if random.random() < 0.7:
            item = random.choice(swamp_loot)
            count = random.randint(1, 2)
            
            # Add to totals for end screen
            for _ in range(count):
                self.total_rewards["items"].append(item)
                
            # Give immediately
            if hasattr(manager, "add_material"):
                manager.add_material(item, count)
                # Visual feedback
                if hasattr(manager, "vfx"):
                    manager.vfx.show_damage(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80, f"+{count} {item}", color=(100, 255, 100))

        # --- REPUTATION (Cap Logic) ---
        # Mainetta saa vain, jos nykyinen maine on alle aallon salliman katon.
        # Esim: Wave 1 (Cap 50), Wave 2 (Cap 70)...
        rep_cap = 30 + (self.current_wave * 20)
        current_rep = manager.reputation
        
        if current_rep < rep_cap:
            base_rep = self.current_wave * 2
            rep_gain = random.randint(base_rep, base_rep + 2)
            
            if hasattr(manager, "modify_faction_rep"):
                manager.modify_faction_rep("shanty", rep_gain) # Local faction
                manager.reputation += rep_gain # Global fame
                if hasattr(manager, "vfx"):
                     manager.vfx.show_damage(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 110, f"+{rep_gain} Rep", color=(200, 200, 255))

        self.total_rewards["gold"] += gold
        self.total_rewards["xp"] += exp
        
        # Apply Gold & XP
        if hasattr(manager, "gold"):
            manager.gold += gold
            
        if hasattr(manager, "player_character") and manager.player_character:
            if hasattr(manager.player_character, "add_xp"):
                manager.player_character.add_xp(exp)
        elif hasattr(manager, "player"): # Fallback
            if hasattr(manager.player, "gold"): manager.player.gold += gold
            if hasattr(manager.player, "gain_exp"): manager.player.gain_exp(exp)

    def update(self, manager):
        if self.announcement_timer > 0: self.announcement_timer -= 1
        
        # Päivitetään lattiaobjektit (MudPools) jotta kuplat toimivat
        if manager.current_arena and hasattr(manager.current_arena, "floor_props"):
            for p in manager.current_arena.floor_props:
                if hasattr(p, "update"): p.update(manager=manager)
            
        if self.wave_delay_timer > 0:
            self.wave_delay_timer -= 1
            if self.wave_delay_timer <= 0:
                self.start_next_wave(manager)
            return

        enemies_alive = sum(1 for e in manager.enemy_team if not getattr(e, "is_dead", False))
        if enemies_alive == 0 and self.wave_in_progress:
            self.on_wave_cleared(manager)

    def is_finished(self, manager):
        return not self.active

    def retreat(self):
        self.finish_mission(self.manager, completed=True)

    def finish_mission(self, manager, completed=False):
        self.active = False
        manager.match_over = True
        manager.match_result = "RETREAT" if completed else "DEFEAT"
        
        existing_loot = manager.round_rewards.get("loot", {})
        
        # Merge wave loot into round rewards
        for item in self.total_rewards["items"]:
            existing_loot[item] = existing_loot.get(item, 0) + 1

        manager.round_rewards = {
            "gold": self.total_rewards["gold"],
            "xp": self.total_rewards["xp"],
            "loot": existing_loot, 
            "wave": self.current_wave
        }
