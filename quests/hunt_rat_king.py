from .base_quest import QuestDefinition
from npc.base_npc import DialogueNode, DialogueChoice

class RatKingQuest(QuestDefinition):
    def __init__(self):
        super().__init__(
            id="hunt_01",
            title="The Rat King",
            description="Something is driving the rats beneath Muckford into "
                        "an army. Descend the Warrens, uncover who commands "
                        "them, and end the crowned rat's reign.",
            rep_req=0,
            boss_id="boss_rat_king",
            rewards={"gold": 500, "reputation": 100, "items": {"Rat Tail": 5}},
            category="main",
            giver="Griznak the Shifty",
            objectives=[
                "Cull the sewer rats gnawing at Muckford's foundations",
                "Break the rat invasion and seal the breach tunnel",
                "Drain the flooded passage and storm the rats' camp",
                "Bridge the broken floor and raise the Frog Smith's gate-ram",
                "Descend into the Abyssal Cistern and end the Rat King",
            ],
        )

    def get_dialogue_for_npc(self, npc_id, status):
        # Example: Griznak might have something to say about this
        if npc_id == "griznak_quest_giver":
            nodes = {}
            if status == "available":
                nodes["start"] = DialogueNode(
                    id="start",
                    text="The Rat King is getting bold. He thinks he owns the sewers. Go teach him a lesson.",
                    speaker="Griznak",
                    emotion="neutral",
                    choices=[
                        DialogueChoice("I'll take the job.", "accept", effects=["accept_quest:hunt_01"]),
                        DialogueChoice("Maybe later.", None, effects=["close_chat"])
                    ]
                )
                nodes["accept"] = DialogueNode(
                    id="accept",
                    text="Good. Bring me his tail, or don't come back.",
                    speaker="Griznak",
                    emotion="happy",
                    choices=[DialogueChoice("Consider it done.", None, effects=["close_chat"])]
                )
                return nodes
            elif status == "active":
                nodes["start"] = DialogueNode(
                    id="start",
                    text="Why is the Rat King still breathing? Get back in there!",
                    speaker="Griznak",
                    emotion="angry",
                    choices=[DialogueChoice("I'm working on it.", None, effects=["close_chat"])]
                )
                return nodes
            elif status == "completed":
                nodes["start"] = DialogueNode(
                    id="start",
                    text="You actually did it? Hah! I owe Hamo money now. Here's your cut.",
                    speaker="Griznak",
                    emotion="surprised",
                    choices=[
                        DialogueChoice("Pleasure doing business.", None, effects=["finish_quest:hunt_01", "close_chat"])
                    ]
                )
                return nodes
        return None