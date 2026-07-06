import random
from ai.tavern_ai import TavernAI

class GamblerAI(TavernAI):
    def __init__(self, unit):
        super().__init__(unit)
        self.state = "sitting"
        # Nollataan tarpeet, jotta hän ei lähde hakemaan ruokaa/juomaa
        self.social = 0 
        self.thirst = 0
        self.hunger = 0
        self.tiredness = 0

    def execute_ai(self, all_units, obstacles, manager=None):
        # Pakota istumaan
        if self.state != "sitting":
            self.state = "sitting"
            self.state_timer = 9999
            
        # Varmista suunta (oikealle, kohti pöytää/huonetta)
        self.unit.facing_right = True 
        self.unit.animation_state = "idle"
        
        # Satunnainen höpinä itsekseen
        if random.random() < 0.005 and manager:
             lines = [
                 "Come on, papa needs a new pair of boots.", 
                 "Roll the bones!", 
                 "High stakes tonight.",
                 "The odds are always right.",
                 "Just one more throw..."
             ]
             manager.vfx.create_speech_bubble(self.unit, random.choice(lines), duration=120)

        # Päivitä kannettava esine (jos on)
        if self.carried_item:
            self.carried_item.update_position(self.unit)