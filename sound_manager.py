import pygame
import os

class SoundManager:
    def __init__(self):
        self.sound_enabled = False
        self.sounds = {}
        self.music_playing = None
        
        # Yritetään alustaa äänilaite
        try:
            pygame.mixer.pre_init(44100, -16, 2, 2048)
            pygame.mixer.init()
            self.sound_enabled = True
        except Exception as e:
            print(f"Warning: Audio system failed to initialize. Game will run silent. ({e})")
            self.sound_enabled = False
        
        # Load sounds (Placeholder paths)
        # Lisätty 'coin' ja 'error', koska main.py käyttää niitä
        self.load_sound('attack_melee', 'assets/sounds/sword_swing.wav')
        self.load_sound('attack_bow',   'assets/sounds/bow_shoot.wav')
        self.load_sound('hit',          'assets/sounds/hit_hurt.wav')
        self.load_sound('heal',         'assets/sounds/heal.wav')
        self.load_sound('click',        'assets/sounds/click.wav')
        self.load_sound('hover',        'assets/sfx/hover.wav')
        self.load_sound('recruit',      'assets/sounds/coin.wav')
        self.load_sound('coin',         'assets/sounds/coin.wav') # Alias recruitille
        self.load_sound('win',          'assets/sounds/win_fanfare.wav')
        self.load_sound('error',        'assets/sounds/error.wav')
        self.load_sound('boss_roar',    'assets/sounds/boss_roar.wav')
        
        # --- RAT KING VOICES ---
        self.load_sound('rat_king_intro',   'assets/voices/rat_king/intro.wav')
        self.load_sound('rat_king_hurt',    'assets/voices/rat_king/hurt.wav')
        self.load_sound('rat_king_enrage',  'assets/voices/rat_king/enrage.wav')
        self.load_sound('rat_king_spit',    'assets/voices/rat_king/spit.wav')
        self.load_sound('rat_king_summon',  'assets/voices/rat_king/summon.wav')
        self.load_sound('rat_king_death',   'assets/voices/rat_king/death.wav')

        # --- FIST SOUNDS ---
        self.load_sound('fist_1', 'assets/sfx/fist/fist_1.wav')
        self.load_sound('fist_2', 'assets/sfx/fist/fist_2.wav')
        self.load_sound('fist_3', 'assets/sfx/fist/fist_3.wav')
        self.load_sound('fist_4', 'assets/sfx/fist/fist_4.wav')

        # --- AXE SOUNDS ---
        self.load_sound('axe_1', 'assets/gear/axes/axe_1.wav')
        self.load_sound('axe_2', 'assets/gear/axes/axe_2.wav')
        self.load_sound('axe_3', 'assets/gear/axes/axe_3.wav')
        self.load_sound('axe_4', 'assets/gear/axes/axe_4.wav')

        # --- OTHER WEAPON SOUNDS (Sword, Dagger, Mace, Spear) ---
        for w_type in ['sword', 'dagger', 'mace', 'spear']:
            folder = f"{w_type}s" # swords, daggers...
            for i in range(1, 5):
                self.load_sound(f'{w_type}_{i}', f'assets/gear/{folder}/{w_type}_{i}.wav')

        # --- VORTEX BLADE SOUNDS ---
        self.load_sound('vortex_blade_attack_1', 'assets/gear/swords/vortex_blade_attack_1.wav')
        self.load_sound('vortex_blade_attack_2', 'assets/gear/swords/vortex_blade_attack_2.wav')
        self.load_sound('vortex_blade_attack_3', 'assets/gear/swords/vortex_blade_attack_3.wav')
        self.load_sound('vortex_blade_attack_4', 'assets/gear/swords/vortex_blade_attack_4.wav')
        self.load_sound('vortex_wave_load',      'assets/gear/swords/vortex_wave_load.wav', volume=0.6)
        self.load_sound('vortex_wave_release',   'assets/gear/swords/vortex_wave_release.wav', volume=0.8)
        self.load_sound('vortex_wave_fly',       'assets/gear/swords/vortex_wave_fly_1.wav', volume=0.6) # Käytetään 1. versiota
        self.load_sound('vortex_wave_impact',    'assets/gear/swords/vortex_wave_impact.wav', volume=0.9)

        # --- RANGED & MAGIC WEAPON SOUNDS ---
        for i in range(1, 5):
            self.load_sound(f'bow_{i}',      f'assets/gear/bows/bow_{i}.wav')
            self.load_sound(f'crossbow_{i}', f'assets/gear/crossbows/crossbow_{i}.wav')
            self.load_sound(f'book_{i}',     f'assets/gear/books/book_{i}.wav')
            self.load_sound(f'staff_{i}',    f'assets/gear/staves/staff_{i}.wav')

        # --- MINING SOUNDS ---
        self.load_sound('mining_hit',     'assets/sfx/mining/mining_hit.wav')
        self.load_sound('mining_success', 'assets/sfx/mining/mining_success.wav')
        self.load_sound('mining_break',   'assets/sfx/mining/mining_break.wav')

        # --- UNDEAD SOUNDS ---
        self.load_sound('undead_attack_1', 'assets/sfx/undead/undead_attack_1.wav')
        self.load_sound('undead_attack_2', 'assets/sfx/undead/undead_attack_2.wav')
        self.load_sound('undead_attack_3', 'assets/sfx/undead/undead_attack_3.wav')
        self.load_sound('undead_attack_4', 'assets/sfx/undead/undead_attack_4.wav')

        # --- SWAMP SOUNDS ---
        for i in range(1, 5):
            # Yritetään ladata alaviivalla (attack_1.wav) JA ilman (attack1.wav)
            # Leech
            if not self.load_sound(f'leech_attack_{i}', f'assets/races/swamp/leech/attack_{i}.wav'):
                self.load_sound(f'leech_attack_{i}', f'assets/races/swamp/leech/attack{i}.wav')
            
            if not self.load_sound(f'leech_hurt_{i}',   f'assets/races/swamp/leech/hurt_{i}.wav'):
                self.load_sound(f'leech_hurt_{i}',   f'assets/races/swamp/leech/hurt{i}.wav')

            # Frog
            if not self.load_sound(f'frog_attack_{i}',  f'assets/races/swamp/frog/attack_{i}.wav'):
                self.load_sound(f'frog_attack_{i}',  f'assets/races/swamp/frog/attack{i}.wav')

            if not self.load_sound(f'frog_hurt_{i}',    f'assets/races/swamp/frog/hurt_{i}.wav'):
                self.load_sound(f'frog_hurt_{i}',    f'assets/races/swamp/frog/hurt{i}.wav')

            if not self.load_sound(f'frog_jump_{i}',    f'assets/races/swamp/frog/jump_{i}.wav'):
                self.load_sound(f'frog_jump_{i}',    f'assets/races/swamp/frog/jump{i}.wav')

        # --- BARD SONGS ---
        for i in range(1, 5):
            self.load_sound(f'bard_song_{i}', f'assets/sfx/bard/bard_song_{i}.wav')

        # --- TALKING LOOPS ---
        for i in range(1, 9):
            self.load_sound(f'talking_loop_{i}', f'assets/sfx/talking/talking_loop_{i}.wav')

        # --- EATING & DRINKING LOOPS ---
        for i in range(1, 5):
            self.load_sound(f'drink_loop_{i}', f'assets/sfx/sounds/drink_loop_{i}.wav', volume=0.8)
            self.load_sound(f'eat_loop_{i}', f'assets/sfx/sounds/eat_loop_{i}.wav', volume=0.8)
            
            # --- LAUGH & REACTION ---
            self.load_sound(f'laugh_loop_{i}', f'assets/sfx/sounds/laugh_loop_{i}.wav')
            self.load_sound(f'reaction_{i}', f'assets/sfx/sounds/reaction_{i}.wav', volume=0.8)

        # --- CROWD / EMOTION SOUNDS ---
        for i in range(1, 5):
            self.load_sound(f'loop_clapping_{i}', f'assets/sfx/sounds/loop_clapping_{i}.wav', volume=0.5)
            self.load_sound(f'cheering_{i}', f'assets/sfx/sounds/cheering_{i}.wav', volume=0.6)
            self.load_sound(f'angry_{i}', f'assets/sfx/sounds/angry_{i}.wav', volume=0.7)
            self.load_sound(f'cheer_competition_{i}', f'assets/sfx/sounds/cheer_competition_{i}.wav', volume=0.6)
            self.load_sound(f'booing_{i}', f'assets/sfx/sounds/booing_{i}.wav', volume=0.6)
            self.load_sound(f'belching_{i}', f'assets/sfx/sounds/belching_{i}.wav', volume=0.5)
            self.load_sound(f'sneeze_{i}', f'assets/sfx/sounds/sneeze_{i}.wav', volume=0.5)
            self.load_sound(f'loop_snore_{i}', f'assets/sfx/sounds/loop_snore_{i}.wav', volume=0.4)

        # --- HOUSE SFX ---
        self.load_sound('fireplace_loop', 'assets/sfx/houses/fireplace_loop.wav', volume=0.6)
        self.load_sound('tavern_ambient', 'assets/sfx/houses/tavern_ambient.wav', volume=0.5)
        
        # --- ANIMALS ---
        self.load_sound('moo', 'assets/sfx/animals/moo.wav', volume=0.5)

        # --- NATURE ---
        self.load_sound('rain_medium', 'assets/sfx/nature/rain_medium.wav', volume=0.4)
        self.load_sound('wind_outside', 'assets/sfx/nature/wind_outside_medium.wav', volume=0.3)
        self.load_sound('thunder_1', 'assets/sfx/nature/Close_thunder_crack_1.wav', volume=0.7)
        self.load_sound('thunder_2', 'assets/sfx/nature/Close_thunder_crack_2.wav', volume=0.7)
        self.load_sound('thunder_3', 'assets/sfx/nature/Close_thunder_crack_3.wav', volume=0.7)
        self.load_sound('thunder_4', 'assets/sfx/nature/Close_thunder_crack_4.wav', volume=0.7)
        
        # --- NEW WIND LOOPS ---
        self.load_sound('wind_loop_normal', 'assets/sfx/nature/wind_loop_outside_normal.wav', volume=0.3)
        self.load_sound('wind_loop_gentle', 'assets/sfx/nature/wind_loop_gentle.wav', volume=0.3)

        # --- GRASS SOUNDS ---
        for i in range(1, 5):
            self.load_sound(f'grass_moving_loop_{i}', f'assets/sfx/nature/grass_moving_loop_{i}.wav', volume=0.2)
            
        # --- TREE SOUNDS ---
        for i in range(1, 5):
            self.load_sound(f'tree_loop_windy_{i}', f'assets/sfx/nature/tree_loop_windy_{i}.wav', volume=0.2)

        # --- VORTEX SFX ---
        self.load_sound('vortex_spawn', 'assets/sfx/vortex/vortex_spawn.wav', volume=0.8)
        self.load_sound('vortex_loop', 'assets/sfx/vortex/vortex_loop.wav', volume=0.6)
        self.load_sound('vortex_end', 'assets/sfx/vortex/vortex_end.wav', volume=0.7)
        self.load_sound('devourer_scream_loop', 'assets/sfx/vortex/devourer_scream_loop.wav', volume=0.9)
        self.load_sound('vortex_missile_loop', 'assets/sfx/vortex/vortex_missile_loop.wav', volume=0.5)
        self.load_sound('vortex_explosion', 'assets/sfx/vortex/vortex_explosion.wav', volume=0.8)
        self.load_sound('devourer_laugh', 'assets/voices/vortex/MnemonicDevourer/laughing.wav', volume=1.0)
        self.load_sound('vortex_shout', 'assets/sfx/vortex/vortex_shout.wav', volume=1.0)
        self.load_sound('vortex_suction', 'assets/sfx/vortex/vortex_suction.wav', volume=0.8)
        self.load_sound('vortex_blast', 'assets/sfx/vortex/vortex_blast.wav', volume=1.0)
        
        # --- MARDA SHANT VOICES ---
        self.load_sound('marda_annoyed', 'assets/voices/human/marda/annoyed.wav')
        self.load_sound('marda_arrogant', 'assets/voices/human/marda/arrogant.wav')
        self.load_sound('marda_casual', 'assets/voices/human/marda/casual.wav')
        self.load_sound('marda_laughing', 'assets/voices/human/marda/laughing.wav')
        self.load_sound('marda_pissed', 'assets/voices/human/marda/pissed.wav')
        self.load_sound('marda_rude', 'assets/voices/human/marda/rude.wav')
        self.load_sound('marda_shouting', 'assets/voices/human/marda/shouting.wav')
        self.load_sound('marda_thinking', 'assets/voices/human/marda/thinking.wav')
        
        # --- COMMANDER SPELLS ---
        self.load_sound('cmd_vortex_warp', 'assets/sfx/spells/commander/vortex_warp.wav', volume=0.7)
        self.load_sound('cmd_vortex_slash', 'assets/sfx/spells/commander/vortex_slash.wav', volume=0.8)

        # --- CROWN & KNIVES MINIGAME ---
        # Yritetään ladata sekä 'gamling' (typo) että 'gambling' kansioista
        ck_path = 'assets/tiles/gamling/'
        if not os.path.exists(ck_path) and os.path.exists('assets/tiles/gambling/'):
            ck_path = 'assets/tiles/gambling/'
            
        self.load_sound('ck_draw',    os.path.join(ck_path, 'card_draw.wav'))
        self.load_sound('ck_place',   os.path.join(ck_path, 'card_placing.wav'))
        self.load_sound('ck_shuffle', os.path.join(ck_path, 'card_suffling.wav'))
        self.load_sound('ck_swords',  os.path.join(ck_path, 'swords.wav'))
        self.load_sound('ck_victory', os.path.join(ck_path, 'victory.wav'))
        self.load_sound('ck_coin_draw', os.path.join(ck_path, 'coin_draw.wav'))
        self.load_sound('ck_coin_place', os.path.join(ck_path, 'coin_place.wav'))
        self.load_sound('ck_coin_taking', os.path.join(ck_path, 'coin_taking.wav'))
        self.load_sound('ck_double_spin', os.path.join(ck_path, 'double_or_nothing.wav'))
        
        # --- CROWN & KNIVES VOICES ---
        # Helper to load with flexible extension and error logging
        def load_ck_voice(key, filename_base):
            # Try extensions .wav, .mp3, .ogg
            for ext in ['.wav', '.mp3', '.ogg']:
                fpath = os.path.join(ck_path, filename_base + ext)
                if os.path.exists(fpath):
                    self.load_sound(key, fpath, volume=1.0) # Max volume for voices
                    return
            print(f"[SoundManager] WARNING: Missing voice file '{filename_base}' in {ck_path}")

        load_ck_voice('ck_voice_betting',     'bettin_1')
        load_ck_voice('ck_voice_cheat',       'cheat_1')
        load_ck_voice('ck_voice_dealer_stop', 'dealer_last_move')
        load_ck_voice('ck_voice_dealer_win',  'dealer_win_1')
        load_ck_voice('ck_voice_duel',        'duel_1')
        load_ck_voice('ck_voice_greeting',    'greeting_1')
        load_ck_voice('ck_voice_luck',        'lcuk_1')
        load_ck_voice('ck_voice_player_draw', 'player_draws_1')
        load_ck_voice('ck_voice_player_idle', 'player_idle_1')
        load_ck_voice('ck_voice_player_stop', 'player_stops_1')
        load_ck_voice('ck_voice_player_win',  'player_win_1')
        load_ck_voice('ck_voice_start_round', 'start_round_1')
        load_ck_voice('ck_voice_stop_early',  'stop_early_1')
        load_ck_voice('ck_voice_sword',       'sword_reaction_1')

    def load_sound(self, name, filepath, volume=0.4):
        if self.sound_enabled and os.path.exists(filepath):
            try: 
                self.sounds[name] = pygame.mixer.Sound(filepath)
                # Säädetään äänenvoimakkuutta hieman, etteivät ole liian kovia
                self.sounds[name].set_volume(volume)
                return True
            except Exception: 
                print(f"Failed to load sound file: {filepath}")
        return False

    def play_sound(self, name, loops=0, volume=None):
        if self.sound_enabled and name in self.sounds: 
            s = self.sounds[name]
            if volume is not None:
                s.set_volume(volume)
            return s.play(loops=loops)
        return None

    def play_music(self, filepath, loops=-1):
        if self.sound_enabled and os.path.exists(filepath):
            if self.music_playing != filepath:
                try:
                    pygame.mixer.music.load(filepath)
                    pygame.mixer.music.set_volume(0.3) # Taustamusiikki hiljaisemmalle
                    pygame.mixer.music.play(loops)
                    self.music_playing = filepath
                except Exception:
                    print(f"Failed to load music: {filepath}")

    def stop_music(self):
        if self.sound_enabled:
            pygame.mixer.music.stop()
            self.music_playing = None

    # --- POSITIONAL AUDIO SYSTEM ---
    
    def get_volume_by_distance(self, source_pos, listener_pos, min_dist=100, max_dist=800):
        """Laskee äänenvoimakkuuden kertoimen (0.0 - 1.0) etäisyyden perusteella."""
        if not source_pos or not listener_pos: return 0.0
        
        dx = source_pos[0] - listener_pos[0]
        dy = source_pos[1] - listener_pos[1]
        dist = (dx*dx + dy*dy)**0.5
        
        if dist <= min_dist:
            return 1.0
        elif dist >= max_dist:
            return 0.0
        else:
            return 1.0 - ((dist - min_dist) / (max_dist - min_dist))

    def play_positional(self, name, source_pos, listener_pos, min_dist=100, max_dist=800, loops=0):
        """Soittaa äänen, jonka voimakkuus skaalautuu etäisyyden mukaan."""
        vol = self.get_volume_by_distance(source_pos, listener_pos, min_dist, max_dist)
        
        if vol > 0.01:
            # Soitetaan ääni ja asetetaan kanavan voimakkuus
            channel = self.play_sound(name, loops=loops)
            if channel:
                channel.set_volume(vol)
            return channel
        return None

sound_system = SoundManager()