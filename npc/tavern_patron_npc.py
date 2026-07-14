from .base_npc import BaseNPC, DialogueNode, DialogueChoice
import random
from sound_manager import sound_system
from quest_system import quest_manager

class TavernPatronNPC(BaseNPC):
    def __init__(self, unit):
        super().__init__(npc_id=f"patron_{unit.name}")
        self.unit = unit
        self.name = unit.name

    def get_dialogue_root(self, context):
        return "start"

    def get_nodes(self, context):
        nodes = {}

        # --- QUEST SYSTEM OVERRIDE (kaikki nimetyt NPC:t) ---
        # Aiemmin vain Farmer Gus kysyi questejä - nyt jokainen NPC voi
        # olla questin antaja (Woodsman Alder, Krad...). Questin dialogi
        # jyrää geneerisen rupattelun kun sellaista on tarjolla.
        if quest_manager:
            override = quest_manager.get_npc_dialogue_override(self.name)
            if override:
                nodes.update(override)
                return nodes
        
        # Satunnaisia huhuja ja kommentteja
        gossip = [
            "The ale is watered down today, but it's better than ditch water.",
            "I heard the Rat King is actually two goblins in a trench coat.",
            "Don't go to the old ruins at night. The shadows bite.",
            "My cousin joined the Legion. Haven't heard from him since.",
            "Bram Mudhand runs a tight ship, but he pays well.",
            "If you're heading to the swamp, bring antidotes.",
            "The weather's turning. Vortex winds are blowing.",
            "I lost my lucky coin in a bet against an elf. Never bet against elves.",
            "This town smells of rust and regret.",
            "Cheers, stranger! Long life to you.",
            "Did you see the match yesterday? Blood everywhere.",
            "I'm just here to forget my troubles.",
            "Watch your purse. Pickpockets are everywhere.",
            "The Shanty Consortium raised the rent again."
        ]
        
        # Joskus harvoin joku "jännä" juttu
        if random.random() < 0.2:
            gossip.append("I saw a hooded figure near the sewers. Dropped a bag of gold and vanished.")
            gossip.append("They say there's a secret tunnel under this tavern. Leads straight to the bank.")
        
        text = random.choice(gossip)
        
        nodes["start"] = DialogueNode(
            id="start",
            text=text,
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice("Interesting.", None, effects=["close_chat"]),
                DialogueChoice("Who are you?", "identity"),
                DialogueChoice("Goodbye.", None, effects=["close_chat"])
            ]
        )
        
        nodes["identity"] = DialogueNode(
            id="identity",
            text=f"Me? Just a {self.unit.race_name} trying to survive in Muckford. I work at the docks mostly.",
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice("Stay safe.", None, effects=["close_chat"])
            ]
        )
        
        return nodes
