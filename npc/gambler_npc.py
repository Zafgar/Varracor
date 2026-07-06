from .base_npc import BaseNPC, DialogueNode, DialogueChoice
import os

class GamblerNPC(BaseNPC):
    def __init__(self):
        super().__init__("gambler")
        self.name = "Sly 'The Dice' Gix"
        # Käytetään Goblinin portrettia placeholderina
        self.portrait_folder = "assets/portraits/goblin" 

    def get_portrait_path(self, emotion):
        # Fallback geneeriseen gobliniin
        return "assets/portraits/goblin/neutral.png"

    def get_dialogue_root(self, context):
        return "start"

    def get_nodes(self, context):
        nodes = {}
        
        nodes["start"] = DialogueNode(
            id="start",
            text="Step right up! The table is hot, the dice are cold, and the gold is waiting. Care to test your luck?",
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice("Play 'Crown & Knives'", "play"),
                DialogueChoice("How do we play?", "rules"),
                DialogueChoice("Not interested.", None, effects=["close_chat"])
            ]
        )
        
        nodes["rules"] = DialogueNode(
            id="rules",
            text="Crown & Knives is a game of greed and sharp edges. What do you need to know?",
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice("Basics (Goal & Cards)", "explain_goal"),
                DialogueChoice("Combat (Swords)", "explain_swords"),
                DialogueChoice("Special Cards", "explain_specials"),
                DialogueChoice("I know enough. Let's play.", "start")
            ]
        )

        nodes["explain_goal"] = DialogueNode(
            id="explain_goal",
            text="Goal: Collect 8 points. Stop before you bust. Highest score wins. \nCards: Crowns (2), Coins (1). Swords (0) start fights.",
            speaker=self.name,
            emotion="happy",
            choices=[DialogueChoice("Tell me more.", "rules")]
        )

        nodes["explain_swords"] = DialogueNode(
            id="explain_swords",
            text="If there are TWO Swords on the table—anywhere, yours or mine—a Duel begins. We both pick a card from hand to fight. High value wins. If you lose a Duel, you lose points. It's nasty business.",
            speaker=self.name,
            emotion="serious",
            choices=[DialogueChoice("Tell me more.", "rules")]
        )

        nodes["explain_specials"] = DialogueNode(
            id="explain_specials",
            text="Ah, the tricks of the trade. The 'Cheat' card turns any Sword on the table into a Coin. Good for stopping a Duel. The 'Luck' card lets you draw two and keep the best one. Use them wisely.",
            speaker=self.name,
            emotion="happy",
            choices=[DialogueChoice("Tell me more.", "rules")]
        )
        
        nodes["play"] = DialogueNode(
            id="play",
            text="Excellent choice. Let's see if fortune favors the bold.",
            speaker=self.name,
            emotion="happy",
            choices=[
                DialogueChoice("[Sit at Table]", None, effects=["start_minigame:crown_knives"])
            ]
        )
        
        return nodes