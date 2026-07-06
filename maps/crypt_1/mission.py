import random
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, RED
from sound_manager import sound_system
from items.material_registry import MATERIAL_DB
from units.undead_skeleton import UndeadSkeleton
from units.undead_zombie import UndeadZombie
from units.undead_skeleton_archer import UndeadSkeletonArcher
from assets.tiles.crypt_vfx import VortexPortal

class MissionLogic:
    def __init__(self, mission_data):
        self.mission_data = mission_data
        self.handles_positioning = True
        
        # --- ASETUKSET ---
        self.max_waves = 40
        self.current_wave = 0
        self.active = True
        self.wave_in_progress = False
        
        # Ajastimet
        self.wave_delay_timer = 0      # Odotus aaltojen välillä
        self.announcement_timer = 0    # Tekstin näkymisaika
        self.announcement_text = ""
        
        # Palkintokertymä
        self.total_rewards = {
            "gold": 0,
            "exp": 0,
            "items": []
        }
        
        # Loot-taulukot
        self.materials_by_rarity = {
            "Common": [], "Uncommon": [], "Rare": [], "Epic": [], "Legendary": []
        }
        for name, data in MATERIAL_DB.items():
            r = data.get("rarity", "Common")
            if r in self.materials_by_rarity:
                self.materials_by_rarity[r].append(name)

    def setup(self, manager):
        self.manager = manager
        # --- MUSIC ---
        sound_system.play_music('assets/music/crypt_theme.wav')

        # --- PLAYER POSITION ---
        # KORJATTU: Asetetaan pelaaja kartan keskelle, ei ruudun keskelle
        cx, cy = manager.current_arena.width // 2, manager.current_arena.height // 2
        
        # Lisätään Commander kentälle
        if manager.player_character:
            pc = manager.player_character
            if pc not in manager.active_player_units:
                manager.active_player_units.add(pc)
                manager.all_units.add(pc)
                pc.is_dead = False
                pc.current_hp = pc.max_hp
        
        manager._position_units_center(list(manager.active_player_units), cx, cy)
        
        # Keskitetään kamera pelaajiin
        manager.camera_x = cx - SCREEN_WIDTH // 2
        manager.camera_y = cy - SCREEN_HEIGHT // 2

        # --- MAP PROPS (Seinät yms) ---
        if manager.current_arena and hasattr(manager.current_arena, "props"):
            for p in manager.current_arena.props:
                if not hasattr(p, "run_combat_ai"):
                    p.run_combat_ai = lambda *args, **kwargs: None
                if not hasattr(p, "take_damage"):
                    p.take_damage = lambda *args, **kwargs: 0
                
                p.is_structure = True
                p.team_color = "Neutral"
                manager.all_units.add(p)

        # Aloitetaan ensimmäinen aalto heti
        print("Crypt Mission Setup Complete. Starting Wave 1.")
        self.start_next_wave(manager)

    def start_next_wave(self, manager):
        if self.current_wave >= self.max_waves:
            self.finish_mission(manager, completed=True)
            return

        self.current_wave += 1
        self.wave_in_progress = True
        
        # Asetetaan ilmoitus (näkyy 3 sekuntia / 180 framea)
        self.announcement_text = f"WAVE {self.current_wave}"
        self.announcement_timer = 180
        
        # --- SPAWN LOGIC ---
        # Käyttäjän pyynnön mukainen nopea kasvu alussa, joka hidastuu myöhemmin.
        wave = self.current_wave
        wave_counts = {1: 4, 2: 8, 3: 14, 4: 20, 5: 30}

        if wave in wave_counts:
            enemy_count = wave_counts[wave]
        else:
            # Aallon 5 jälkeen kasvu on lineaarisempaa.
            enemy_count = 30 + (wave - 5) * 2

        # Rajoitetaan maksimimäärä, ettei peli tukkeudu täysin.
        if enemy_count > 35: enemy_count = 35
        
        print(f"--- WAVE {self.current_wave}/{self.max_waves} (Enemies: {enemy_count}) ---")

        # KORJATTU: Määritellään 8 spawn-aluetta ympäri karttaa
        w, h = manager.current_arena.width, manager.current_arena.height
        zone_size = 400
        margin = 200
        
        spawn_zones = [
            # Corners
            pygame.Rect(margin, margin, zone_size, zone_size),                               # Top-Left
            pygame.Rect(w - margin - zone_size, margin, zone_size, zone_size),             # Top-Right
            pygame.Rect(margin, h - margin - zone_size, zone_size, zone_size),             # Bottom-Left
            pygame.Rect(w - margin - zone_size, h - margin - zone_size, zone_size, zone_size), # Bottom-Right
            # Mids
            pygame.Rect(margin, h // 2 - zone_size // 2, zone_size, zone_size),            # Mid-Left
            pygame.Rect(w - margin - zone_size, h // 2 - zone_size // 2, zone_size, zone_size), # Mid-Right
            pygame.Rect(w // 2 - zone_size // 2, margin, zone_size, zone_size),            # Top-Mid
            pygame.Rect(w // 2 - zone_size // 2, h - margin - zone_size, zone_size, zone_size)  # Bottom-Mid
        ]
        
        # Valitaan aktiiviset spawn-alueet tälle aallolle (1-4 kpl määrästä riippuen)
        num_zones = 1
        if enemy_count > 8: num_zones = 2
        if enemy_count > 16: num_zones = 3
        if enemy_count > 25: num_zones = 4
        
        active_zones = random.sample(spawn_zones, min(len(spawn_zones), num_zones))
        
        # Luodaan portaalit ja tallennetaan niiden sijainnit
        portals = []
        for zone in active_zones:
            px = random.randint(zone.left, zone.right)
            py = random.randint(zone.top, zone.bottom)
            
            # Luodaan visuaalinen portaali (kestää 3 sekuntia)
            if hasattr(manager, "vfx"):
                portal = VortexPortal(px, py, duration=180)
                manager.vfx.floor_particles.add(portal)
            
            portals.append((px, py))

        for i in range(enemy_count):
            # Spawnataan vihollinen satunnaisesta portaalista
            spawn_pos = random.choice(portals)
            x = spawn_pos[0] + random.randint(-30, 30)
            y = spawn_pos[1] + random.randint(-30, 30)
            
            # --- Vihollistyyppien todennäköisyydet muuttuvat waven mukaan ---
            # Jousimiehet yleistyvät nopeasti, zombiet täydentävät ja luurangot vähenevät.
            archer_chance = 0.0
            zombie_chance = 0.0

            # Jousimiehiä alkaa tulla aallosta 3 lähtien, ja niiden osuus kasvaa.
            if self.current_wave >= 3:
                # Wave 3: ~16%, Wave 10: ~30%, Wave 20: 50%
                archer_chance = min(0.5, 0.1 + (self.current_wave / 20.0) * 0.4)

            # Zombeja alkaa tulla aallosta 2 lähtien.
            if self.current_wave >= 2:
                # Wave 2: ~18%, Wave 10: ~28%, Wave 20: 40%
                zombie_chance = min(0.4, 0.15 + (self.current_wave / 20.0) * 0.25)

            roll = random.random()
            unit = None
            
            if roll < archer_chance:
                unit = UndeadSkeletonArcher(f"Archer {i+1}", x, y, RED)
            elif roll < archer_chance + zombie_chance:
                unit = UndeadZombie(f"Zombie {i+1}", x, y, RED)
            else:
                unit = UndeadSkeleton(f"Skeleton {i+1}", x, y, RED)
            
            if unit:
                manager.enemy_team.add(unit)
                manager.all_units.add(unit)
                if hasattr(manager, "vfx"):
                    manager.vfx.create_spawn_fog(x, y)

    def on_wave_cleared(self, manager):
        self.wave_in_progress = False
        self.wave_delay_timer = 120 # 2 sekuntia taukoa ennen seuraavaa
        
        # Laske palkinnot
        gold = 30 + (self.current_wave * 15)
        exp = 60 + (self.current_wave * 30)
        
        # Loot drop logic
        items = []
        drop_count = 1
        if self.current_wave > 10: drop_count = random.randint(1, 2)
        if self.current_wave > 25: drop_count = random.randint(2, 3)
        
        allowed_rarities = ["Common"]
        if self.current_wave >= 5: allowed_rarities.append("Uncommon")
        if self.current_wave >= 15: allowed_rarities.append("Rare")
        if self.current_wave >= 25: allowed_rarities.append("Epic")
        
        for _ in range(drop_count):
            chosen_rarity = random.choice(allowed_rarities)
            pool = self.materials_by_rarity.get(chosen_rarity, [])
            if not pool: pool = self.materials_by_rarity.get("Common", [])
            if pool: items.append(random.choice(pool))

        # Tallenna
        self.total_rewards["gold"] += gold
        self.total_rewards["exp"] += exp
        self.total_rewards["items"].extend(items)
        
        # --- REPUTATION (Cap Logic) ---
        # Mainetta saa vain, jos nykyinen maine on alle aallon salliman katon.
        rep_cap = 30 + (self.current_wave * 20)
        current_rep = manager.reputation
        
        if current_rep < rep_cap:
            base_rep = self.current_wave * 2
            rep_gain = random.randint(base_rep, base_rep + 2)
            
            if hasattr(manager, "modify_faction_rep"):
                # Shanty & Lumen hyötyvät eniten kryptan puhdistuksesta
                manager.modify_faction_rep("shanty", rep_gain)
                manager.modify_faction_rep("lumen", rep_gain)
                manager.reputation += rep_gain # Global fame
                
                if hasattr(manager, "vfx"):
                     manager.vfx.show_damage(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 110, f"+{rep_gain} Rep", color=(200, 200, 255))

        # --- APPLY GOLD & XP & ITEMS ---
        if hasattr(manager, "gold"):
            manager.gold += gold
            
        if hasattr(manager, "player_character") and manager.player_character:
            if hasattr(manager.player_character, "add_xp"):
                manager.player_character.add_xp(exp)
        
        # Materiaalit lisätään managerin kautta (menee reppuun)
        for it in items:
            if hasattr(manager, "add_material"):
                manager.add_material(it)

        print(f"Wave {self.current_wave} Cleared! Rewards: {gold}g, {exp}xp")

    def update(self, manager):
        # Päivitä ilmoitustekstin ajastin
        if self.announcement_timer > 0:
            self.announcement_timer -= 1
            
        # Jos aaltojen välissä on tauko
        if self.wave_delay_timer > 0:
            self.wave_delay_timer -= 1
            if self.wave_delay_timer <= 0:
                self.start_next_wave(manager)
            return

        # Tarkista onko vihollisia jäljellä
        enemies_alive = 0
        for e in manager.enemy_team:
            if not getattr(e, "is_dead", False):
                enemies_alive += 1
        
        if enemies_alive == 0 and self.wave_in_progress:
            self.on_wave_cleared(manager)

    def is_finished(self, manager):
        return not self.active

    def retreat(self):
        """Kutsutaan kun pelaaja painaa RUN-nappia."""
        # Merkitään suoritetuksi jotta lootit säilyy
        self.finish_mission(self.manager, completed=True)

    def finish_mission(self, manager, completed=False):
        self.active = False
        manager.match_over = True
        manager.match_result = "RETREAT" if completed else "DEFEAT"
        
        # Tallenna ennätys
        if hasattr(manager, "player"):
            current_best = getattr(manager.player, "crypt_best_wave", 0)
            if self.current_wave > current_best:
                manager.player.crypt_best_wave = self.current_wave
        
        # Säilytetään olemassa oleva loot (esim. Iron Ore)
        existing_loot = manager.round_rewards.get("loot", {})
        
        # Aseta palkinnot näkyviin loppuruutua varten
        manager.round_rewards = {
            "gold": self.total_rewards["gold"],
            "xp": self.total_rewards["exp"],
            "loot": existing_loot, 
            "wave": self.current_wave
        }
        
        # Yhdistetään wave-palkinnot loottiin
        for item in self.total_rewards["items"]:
            manager.round_rewards["loot"][item] = manager.round_rewards["loot"].get(item, 0) + 1