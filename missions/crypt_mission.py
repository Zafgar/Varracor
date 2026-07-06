import random
import pygame
from items.material_registry import MATERIAL_DB
from units.undead_skeleton import UndeadSkeleton
from units.undead_zombie import UndeadZombie
from units.undead_skeleton_archer import UndeadSkeletonArcher
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class CryptMission:
    def __init__(self, game_manager):
        self.manager = game_manager
        
        # Asetukset
        self.max_waves = 40
        self.current_wave = 0
        self.active = False
        self.wave_in_progress = False
        
        # Palkintokertymä (tilastointia varten)
        self.total_rewards = {
            "gold": 0,
            "exp": 0,
            "items": []
        }
        
        # Ilmoitukset (Wave start)
        self.announcement_text = ""
        self.announcement_timer = 0
        
        # Luokitellaan materiaalit valmiiksi rarityn mukaan
        self.materials_by_rarity = {
            "Common": [], "Uncommon": [], "Rare": [], "Epic": [], "Legendary": []
        }
        for name, data in MATERIAL_DB.items():
            r = data.get("rarity", "Common")
            if r in self.materials_by_rarity:
                self.materials_by_rarity[r].append(name)

    def start_mission(self):
        """Aloittaa mission alusta."""
        self.current_wave = 0
        self.active = True
        self.total_rewards = {"gold": 0, "exp": 0, "items": []}
        print("Crypt Mission Started!")
        self.start_next_wave()

    def update(self):
        """Päivittää missionin sisäistä tilaa (esim. tekstien ajastukset)."""
        if self.announcement_timer > 0:
            self.announcement_timer -= 1

    def start_next_wave(self):
        """Aloittaa seuraavan waven jos mahdollista."""
        if self.current_wave >= self.max_waves:
            self.finish_mission(completed=True)
            return

        self.current_wave += 1
        self.wave_in_progress = True
        
        # Vaikeustaso nousee joka wave
        # difficulty = 1.0 + (self.current_wave * 0.2) # Ei käytetä suoraan tässä logiikassa
        
        # --- SPAWN LOGIC ---
        # Lasketaan vihollisten määrä ja tyypit
        enemy_count = 2 + int(self.current_wave * 0.6) # Esim: Wave 1=2, Wave 10=8, Wave 40=26
        if enemy_count > 15: enemy_count = 15 # Cap ettei peli tukkeudu
        
        print(f"--- WAVE {self.current_wave}/{self.max_waves} ---")
        
        # Tyhjennä vanhat viholliset varmuuden vuoksi (jos jotain jäi roikkumaan)
        # self.manager.enemy_team.empty() # Ei tyhjennetä, jos halutaan ruumiiden jäävän? Yleensä wave-peleissä tyhjennetään tai odotetaan kuolemaa.
        
        spawn_x_start = SCREEN_WIDTH - 300
        spawn_y_range = (150, SCREEN_HEIGHT - 150)
        
        for i in range(enemy_count):
            # Arvo sijainti
            x = random.randint(spawn_x_start, SCREEN_WIDTH - 50)
            y = random.randint(spawn_y_range[0], spawn_y_range[1])
            
            # Arvo tyyppi waven perusteella
            # Wave 1-3: Vain Skeletons
            # Wave 4-9: Skeletons + Zombies
            # Wave 10+: Skeletons + Zombies + Archers
            
            roll = random.random()
            unit = None
            
            if self.current_wave >= 10 and roll < 0.3:
                unit = UndeadSkeletonArcher(f"Archer {i+1}", x, y, (180, 180, 180))
            elif self.current_wave >= 4 and roll < 0.6:
                unit = UndeadZombie(f"Zombie {i+1}", x, y, (100, 120, 100))
            else:
                unit = UndeadSkeleton(f"Skeleton {i+1}", x, y, (200, 200, 200))
            
            if unit:
                self.manager.add_entity(unit, team="enemy")
                # Visuaalinen efekti spawnille
                if hasattr(self.manager, "vfx"):
                    self.manager.vfx.create_spawn_fog(x, y)

    def get_wave_announcement(self):
        """Palauttaa tekstin ruudulle piirrettäväksi."""
        return f"WAVE {self.current_wave}"

    def on_wave_cleared(self):
        """Kutsutaan kun kaikki viholliset on voitettu."""
        if not self.wave_in_progress:
            return

        self.wave_in_progress = False
        
        # Laske ja jaa palkinnot
        gold, exp, items = self.calculate_rewards()
        
        self.total_rewards["gold"] += gold
        self.total_rewards["exp"] += exp
        self.total_rewards["items"].extend(items)
        
        # Lisää palkinnot pelaajalle (Oletus: manager.player on olemassa)
        if hasattr(self.manager, "player"):
            self.manager.player.gold += gold
            self.manager.player.gain_exp(exp)
            # Lisätään materiaalit inventaarioon
            for item_name in items:
                # Oletusmetodi materiaalin lisäykselle
                if hasattr(self.manager.player, "add_material"):
                    self.manager.player.add_material(item_name)
        
        print(f"Wave Cleared! Rewards: {gold}g, {exp}xp, Items: {items}")
        
        # Automaattinen jatko tai odotus (tässä oletetaan että peli kutsuu start_next_wave)
        # self.start_next_wave()

    def on_defeat(self):
        """Kutsutaan jos pelaaja häviää."""
        print(f"Defeat at Wave {self.current_wave}")
        self.finish_mission(completed=False)

    def calculate_rewards(self):
        """Laskee palkinnot nykyisen waven perusteella (nousevat määrät)."""
        # Raha: Base 30 + nouseva määrä (15g per wave)
        gold = 30 + (self.current_wave * 15)
        
        # XP: Base 60 + nouseva määrä (30xp per wave)
        exp = 60 + (self.current_wave * 30)
        
        # Materiaalit: Määrä ja laatu nousee
        items = []
        
        # Drop chance kasvaa hieman
        drop_count = 1
        if self.current_wave > 10: drop_count = random.randint(1, 2)
        if self.current_wave > 25: drop_count = random.randint(2, 3)
        if self.current_wave > 35: drop_count = random.randint(3, 4)
        
        # Määritä sallitut rarityt waven perusteella
        allowed_rarities = ["Common"]
        if self.current_wave >= 5: allowed_rarities.append("Uncommon")
        if self.current_wave >= 15: allowed_rarities.append("Rare")
        if self.current_wave >= 25: allowed_rarities.append("Epic")
        if self.current_wave >= 35: allowed_rarities.append("Legendary")
        
        for _ in range(drop_count):
            # Painotetaan harvinaisempia korkeammilla waveilla
            # Yksinkertainen logiikka: valitaan random rarity sallituista
            # Mutta annetaan painoarvoa paremmille jos wave on korkea
            chosen_rarity = random.choice(allowed_rarities)
            
            # Jos wave on tosi korkea, yritetään "rerollata" parempaan
            if self.current_wave > 20 and chosen_rarity == "Common":
                chosen_rarity = random.choice(allowed_rarities)

            pool = self.materials_by_rarity.get(chosen_rarity, [])
            
            # Fallback: jos pool on tyhjä (esim ei Legendary itemeitä DB:ssä), ota Common
            if not pool: 
                pool = self.materials_by_rarity.get("Common", [])
            
            if pool:
                items.append(random.choice(pool))
                
        return int(gold), int(exp), items

    def retreat(self):
        """Pelaaja pakenee kesken kaiken."""
        print("Retreating from Crypt...")
        # Lopetetaan missio, mutta merkitään 'completed=True' jotta loot-ruutu näkyy
        self.finish_mission(completed=True)

    def finish_mission(self, completed=False):
        self.active = False
        
        status = "COMPLETED" if completed else "DEFEATED"
        print(f"Crypt Mission {status}! Reached Wave: {self.current_wave}")
        print("--- LOOT SUMMARY ---")
        print(f"Gold: {self.total_rewards['gold']}")
        print(f"Items: {self.total_rewards['items']}")
        
        # Tallenna High Score (Best Wave)
        if hasattr(self.manager, "player"):
            current_best = getattr(self.manager.player, "crypt_best_wave", 0)
            if self.current_wave > current_best:
                self.manager.player.crypt_best_wave = self.current_wave
                print(f"NEW RECORD! Wave {self.current_wave}")
        
        # Pakotetaan peli loppumaan ja siirrytään raporttiin
        self.manager.match_over = True
        self.manager.match_result = "RETREAT" if completed else "DEFEAT"