from .base_npc import BaseNPC, DialogueNode, DialogueChoice
from settings import GOLD_COLOR, RED, GREEN
import random

class RecruitNPC(BaseNPC):
    def __init__(self, unit):
        # Käytetään yksikön nimeä ID:nä väliaikaisesti
        super().__init__(npc_id=f"recruit_{unit.name}")
        self.unit = unit
        self.name = unit.name
        
        # Laske hinta maineen perusteella
        self.base_cost = unit.cost
        self.final_cost = unit.cost

    def get_portrait_path(self, emotion):
        # Käytetään yksikön omaa kuvaa jos mahdollista, muuten geneerinen
        # ChatMenu hoitaa tämän logiikan jos palautamme None tai erikoispolun
        return None 

    def get_dialogue_root(self, context):
        return "start"

    def get_nodes(self, context):
        nodes = {}
        
        player_rep = context.get("reputation", 0)
        matches_played = context.get("matches_played", 0)
        player_gold = context["player"]["gold"]
        
        # --- HINTALASKURI ---
        # Maine vaikuttaa hintaan
        modifier = 1.0
        
        # Persoonallisuus
        traits = getattr(self.unit, "traits", [])
        race = self.unit.race_name
        
        # Määritä äänensävy rodun/traitien mukaan
        tone = "neutral"
        if race == "Orc" or "Strong" in traits: tone = "aggressive"
        elif race == "Goblin" or "Greedy" in traits: tone = "greedy"
        elif race == "Elf" or "Fast" in traits: tone = "proud"
        elif race == "Dwarf" or "Tough" in traits: tone = "gruff"
        
        intro_text = ""
        
        # Jos pelaaja ei ole taistellut vielä yhtään
        if matches_played == 0:
            if tone == "aggressive": intro_text = "You look soft. I don't fight for weaklings."
            elif tone == "greedy": intro_text = "New in town? Prices are double for rookies."
            elif tone == "proud": intro_text = "I do not waste my arrows on amateur commands."
            else: intro_text = "Who are you? You don't look like a captain. I need work, but I don't work for amateurs."
            modifier = 1.0 # Ei alennusta
            
        else:
            if player_rep > 500:
                modifier = 0.8
                intro_text = f"Commander! The arena champion. It would be an honor to fight for you."
            elif player_rep < -100:
                modifier = 1.5
                intro_text = f"You? I've heard bad things. If you want me, you pay extra. Up front."
            else:
                if tone == "aggressive": intro_text = f"I've seen you fight. Not bad. I can crush skulls for you."
                elif tone == "greedy": intro_text = f"Hiring? I'm expensive, but worth it."
                elif tone == "proud": intro_text = f"Your tactics are adequate. I may consider joining you."
                elif tone == "gruff": intro_text = f"Aye? Need a shield in the line?"
                else: intro_text = f"Looking for a fighter? I'm available. Standard rates."
            
        self.final_cost = int(self.base_cost * modifier)
        
        # --- DIALOGI ---
        
        nodes["start"] = DialogueNode(
            id="start",
            text=intro_text,
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice("What are your skills?", "ask_stats"),
                DialogueChoice("Never mind.", None, effects=["close_chat"])
            ]
        )
        
        # Lisää palkkausvaihtoehto vain jos pelaaja on todistanut itsensä (tai on tarpeeksi rahaa uhitteluun)
        if matches_played > 0 or player_rep > 200:
            nodes["start"].choices.insert(0, DialogueChoice(f"I want to hire you. ({self.final_cost} Gold)", "hire_confirm"))
        else:
            # Jos tuntematon, pitää vakuuttaa
            nodes["start"].choices.insert(0, DialogueChoice("I am building a team for the League.", "convince_rookie"))

        nodes["convince_rookie"] = DialogueNode(
            id="convince_rookie",
            text="Words are wind. Show me gold or glory.",
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice(f"Here is {self.final_cost} Gold. Is that proof enough?", "hire_confirm"),
                DialogueChoice("I'll come back when I'm famous.", None, effects=["close_chat"])
            ]
        )
        
        # Stats info
        stats_text = f"I am a Level {self.unit.level} {self.unit.race_name}. "
        if traits:
            stats_text += f"I am known for being {', '.join(traits)}. "
        stats_text += f"My strength is {self.unit.strength} and I have {self.unit.max_hp} HP."
        
        nodes["ask_stats"] = DialogueNode(
            id="ask_stats",
            text=stats_text,
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice("Impressive.", "start"),
                DialogueChoice("Not what I need.", None, effects=["close_chat"])
            ]
        )
        
        # Hire logic
        can_afford = player_gold >= self.final_cost
        
        if can_afford:
            nodes["hire_confirm"] = DialogueNode(
                id="hire_confirm",
                text="Deal. When do we march?",
                speaker=self.name,
                emotion="happy",
                choices=[
                    DialogueChoice(
                        "Welcome aboard.", 
                        None, 
                        effects=[f"hire_unit:{self.final_cost}", "close_chat"]
                    )
                ]
            )
        else:
            nodes["hire_confirm"] = DialogueNode(
                id="hire_confirm",
                text="You can't afford me. Don't waste my time.",
                speaker=self.name,
                emotion="angry",
                choices=[
                    DialogueChoice("I'll get the money.", None, effects=["close_chat"])
                ]
            )

        return nodes
