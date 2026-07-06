import pygame
import random
import math
from ai.base_ai import BaseAI
from sound_manager import sound_system
from assets.tiles.house_objects import HouseDoor

# Yleiset keskusteluaiheet kaikille siviileille
DIALOGUE_TOPICS = {
    "rats": [
        "Rats' eyes are glowing purple lately. That ain't hunger, it's the residue.",
        "Don't ask what's in Marda's Ratpot Pie today. Just eat it.",
        "I swear the Rat-Armies are organizing. Saw them marching in formation.",
        "Hamo is paying double for tails. Something big is coming.",
        "The Rat King isn't a myth. I heard scratching beneath the floorboards.",
        "If the granary is empty, the King has awakened.",
        "Saw a rat eating Vortex sludge. It hissed at me.",
        "My cousin went into the sewers. Never came back."
    ],
    "arena": [
        "Saw a velvet cloak in the crowd. Sera Quench's scout?",
        "Shanty Yard Saints are fighting today! True Muckford heroes.",
        "I threw a barrel at a goblin in the last match. Best part of the show.",
        "One big win, and I'm out of this mud.",
        "The sand in the Shanty Yard is red for a reason.",
        "Mudhand's champions look weak. The Saints will crush them.",
        "If you want out of Tier 0, you need to put on a show.",
        "Sera Quench is looking for new blood. Maybe this is my chance?"
    ],
    "debt": [
        "Bram's ledger is heavier than a warhammer.",
        "Marda Shant never forgets a tab. Sign or suffer.",
        "Bram offered me an extension... but I have to haul scrap for free.",
        "Don't cross Mudhand. Your name goes in the black book.",
        "Need coin? Hamo is hiring, if you're desperate.",
        "Collectors are out in force tonight. Keep your head down.",
        "I sold my grandmother's ring. Still not enough."
    ],
    "health": [
        "Stay away from the west gate. Sister Rhea is burning clothes.",
        "Sewer fever is spreading. That cough sounds bad.",
        "Real healing costs too much. I bought a tonic from the Ratcatchers.",
        "Sister Rhea says it's a plague. I say it's the Vortex.",
        "Don't breathe the fog. It rots the lungs.",
        "The Hospice is full. They are turning people away."
    ],
    "vortex": [
        "Wind changed. Tastes like ash.",
        "The Old Mill is safe by day, but things without shadows walk there at night.",
        "The Unclaimed Five went into the mist. Not all came back.",
        "Did you see the sky flicker last night? The Breath-Gate is active.",
        "Don't stare at the purple lightning. It stares back.",
        "Marshlight Sirens are calling from the bog."
    ],
    "casual": [
        "Mud everywhere. I hate this town.",
        "At least the roof isn't leaking... much.",
        "Cheers. To surviving another day.",
        "This ale tastes like rusty water.",
        "My back aches. Stone beds are unforgiving.",
        "Just keep working. Bram is watching."
    ],
    "weather": [
        "Rain, rain, rain. Muckford never dries.",
        "Fog's thick enough to chew on."
        "Acid rain coming. I can smell the sulfur."
    ],
    "work": [
        "Scrap prices are down again. Thanks to the Consortium.",
        "Mining in the dark. Always in the dark.",
        "Found a vein of iron, but the goblins took it."
    ]
}

class LifeAI(BaseAI):
    def __init__(self, unit):
        super().__init__(unit)
        
        # Perustarpeet (0-100)
        self.thirst = random.randint(0, 50)
        self.hunger = random.randint(0, 50)
        self.cold = random.randint(0, 50)
        self.social = random.randint(0, 50)
        self.tiredness = random.randint(0, 50)
        
        # Kasvunopeudet
        self.thirst_rate = random.uniform(0.03, 0.08)
        self.hunger_rate = random.uniform(0.02, 0.06)
        self.cold_rate = random.uniform(0.01, 0.04)
        self.social_rate = random.uniform(0.02, 0.05)
        self.tiredness_rate = 0.03

        # Tilakone
        self.state = "idle"
        self.state_timer = random.randint(40, 120)
        self.next_state = None
        self.target_pos = None
        self.target_obj = None
        
        # Sosiaalinen
        self.conversation_partner = None
        self.reply_timer = 0
        self.chat_turns = 0
        self.current_topic = None

    def update_needs(self):
        self.thirst += self.thirst_rate
        self.hunger += self.hunger_rate
        self.cold += self.cold_rate
        self.social += self.social_rate
        self.tiredness += self.tiredness_rate

    def _execute_move(self, obstacles, all_units, manager):
        self.unit.animation_state = "run"
        
        if self.target_pos:
            dx = self.target_pos[0] - self.unit.rect.centerx
            dy = self.target_pos[1] - self.unit.rect.centery
            
            # --- OVIEN KÄSITTELY ---
            if obstacles:
                for obs in obstacles:
                    if isinstance(obs, HouseDoor) and not obs.is_open:
                        # Kasvatettu tunnistusaluetta (20 -> 40)
                        if self.unit.rect.inflate(40, 40).colliderect(obs.interaction_rect):
                            obs.toggle() # Avaa ovi
            
            dist = math.hypot(dx, dy)
            
            # Jos ollaan perillä TAI lähellä kohdetta (ruuhka) ja jumissa
            if dist < 30 or (dist < 100 and self.stuck_counter > 30):
                self._on_arrive(manager)
                self.stuck_counter = 0 # Nollaa jumi-laskuri
            else:
                # Hard Stuck Reset
                if self.stuck_counter > 80:
                    self.stuck_counter = 0
                    if manager and random.random() < 0.3:
                        manager.vfx.create_speech_bubble(self.unit, "Blocked...", duration=60)
                    self._plan_wander(obstacles)
                    return

                # Kierto (Slide)
                if self.stuck_counter > 10:
                    angle = math.atan2(dy, dx)
                    if (self.stuck_counter // 40) % 2 == 0:
                        slide_angle = angle + 1.5
                    else:
                        slide_angle = angle - 1.5
                    
                    slide_dx = math.cos(slide_angle) * 100
                    slide_dy = math.sin(slide_angle) * 100
                    
                    final_dx = dx * 0.2 + slide_dx * 0.8
                    final_dy = dy * 0.2 + slide_dy * 0.8
                    self._move_towards(final_dx, final_dy, dist, obstacles, all_units)
                else:
                    self._move_towards(dx, dy, dist, obstacles, all_units)

    def _plan_wander(self, obstacles):
        self.state = "move_to"
        self.next_state = "idle"
        self.state_timer = random.randint(150, 300)
        # Satunnainen piste (karkea arvio alueesta, aliluokat voivat tarkentaa)
        self.target_pos = (self.unit.rect.centerx + random.randint(-200, 200), 
                           self.unit.rect.centery + random.randint(-200, 200))

    def _on_arrive(self, manager):
        # Oletus: siirry seuraavaan tilaan tai idle
        if self.next_state:
            self.state = self.next_state
            self.next_state = None
            if self.state_timer <= 0: self.state_timer = 60
        else:
            self.state = "idle"
            self.state_timer = 60

    def _say_something(self, manager, is_reply=False):
        text = None
        topic = None

        if not text:
            if is_reply and self.current_topic:
                topic = self.current_topic
            else:
                topic = random.choice(list(DIALOGUE_TOPICS.keys()))
                self.current_topic = topic
                
            lines = DIALOGUE_TOPICS.get(topic, DIALOGUE_TOPICS["casual"])
            text = random.choice(lines)
        
        manager.vfx.create_speech_bubble(self.unit, text, duration=240)
        
        if random.random() < 0.15:
            s_id = random.randint(1, 4)
            sound_system.play_sound(f"laugh_loop_{s_id}")
        else:
            talk_id = random.randint(1, 8)
            sound_system.play_sound(f"talking_loop_{talk_id}")