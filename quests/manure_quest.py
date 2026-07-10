from .base_quest import QuestDefinition
from npc.base_npc import DialogueNode, DialogueChoice

class ManureQuest(QuestDefinition):
    def __init__(self):
        super().__init__(
            id="quest_manure_cleanup",
            title="Clean the Stables",
            description="Farmer Gus needs help cleaning up manure piles.",
            rep_req=0,
            boss_id=None, # Ei bossia, keräysquest
            rewards={"gold": 5, "reputation": 5, "xp": 10}
        )
        self.required_amount = 5

    def get_dialogue_for_npc(self, npc_id, status):
        if npc_id != "Farmer Gus": return None
        
        nodes = {}
        
        if status == "available":
            nodes["start"] = DialogueNode(
                id="start",
                text="Well hello there. The cows are making a mess again. Want to earn some coin?",
                speaker="Farmer Gus",
                emotion="neutral",
                choices=[
                    DialogueChoice("Sure, I'll help.", "accept_quest", effects=["accept_quest:quest_manure_cleanup"]),
                    DialogueChoice("Not right now.", None, effects=["close_chat"])
                ]
            )
            nodes["accept_quest"] = DialogueNode(
                id="accept_quest",
                text=f"Great! Grab a shovel. Clean up {self.required_amount} piles and dump them in the compost heap. I'll pay you 5 Gold.",
                speaker="Farmer Gus",
                emotion="happy",
                choices=[DialogueChoice("I'm on it.", None, effects=["close_chat"])]
            )
            return nodes

        elif status == "active":
            nodes["start"] = DialogueNode(
                id="start",
                text="Still working? Remember to dump the manure in the pile.",
                speaker="Farmer Gus",
                emotion="neutral",
                choices=[DialogueChoice("I'm on it.", None, effects=["close_chat"])]
            )
            return nodes

        elif status == "completed":
            nodes["start"] = DialogueNode(
                id="start",
                text="Looks much better! Here is your pay. Come back anytime, they never stop pooping.",
                speaker="Farmer Gus",
                emotion="happy",
                choices=[
                    DialogueChoice("Thanks.", None, effects=["finish_quest:quest_manure_cleanup", "close_chat"])
                ]
            )
            return nodes
            
        return None