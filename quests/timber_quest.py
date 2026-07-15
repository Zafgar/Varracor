from .base_quest import QuestDefinition
from npc.base_npc import DialogueNode, DialogueChoice


class TimberQuest(QuestDefinition):
    """Woodsman Alder antaa ensimmäisen kirveen ja opettaa hakkuun.
    Kaada puita hökkelimetsässä - mainetta ja kolikkoa kylätyöstä."""

    def __init__(self):
        super().__init__(
            id="quest_first_swing",
            title="First Swing",
            description="Woodsman Alder wants trees felled at the shanty "
                        "wood's edge.",
            rep_req=0,
            boss_id=None,
            rewards={"gold": 10, "reputation": 3, "xp": 15},
            category="side", giver="Woodsman Alder",
            objectives=["Fell 4 trees at the shanty wood's edge"]
        )
        self.required_amount = 4  # kaadettua puuta

    def get_dialogue_for_npc(self, npc_id, status):
        if npc_id != "Woodsman Alder":
            return None
        nodes = {}
        if status == "available":
            nodes["start"] = DialogueNode(
                id="start",
                text="You swing a sword well enough - let's see you swing an "
                     "axe. Fell four trees by the shanties and the timber's "
                     "yours to keep. Here, take my spare.",
                speaker="Woodsman Alder", emotion="neutral",
                choices=[
                    DialogueChoice("Hand it over.", "accept",
                                   effects=["accept_quest:quest_first_swing",
                                            "give_item:WeakLumberAxe"]),
                    DialogueChoice("Maybe later.", None,
                                   effects=["close_chat"]),
                ])
            nodes["accept"] = DialogueNode(
                id="accept",
                text="Aim low, follow through, and mind your toes. "
                     "Four trees, then come brag about it.",
                speaker="Woodsman Alder", emotion="happy",
                choices=[DialogueChoice("On it.", None,
                                        effects=["close_chat"])])
            return nodes
        if status == "active":
            nodes["start"] = DialogueNode(
                id="start",
                text="Trees don't fall from staring at them. "
                     "Keep swinging - the axe learns your hands.",
                speaker="Woodsman Alder", emotion="neutral",
                choices=[DialogueChoice("Back to work.", None,
                                        effects=["close_chat"])])
            return nodes
        if status == "completed":
            nodes["start"] = DialogueNode(
                id="start",
                text="Clean stumps! You've got a woodsman's arm under all "
                     "that arena bravado. The axe is yours - and here's "
                     "coin for the sweat.",
                speaker="Woodsman Alder", emotion="happy",
                choices=[DialogueChoice("Thanks, Alder.", None,
                                        effects=["finish_quest:quest_first_swing",
                                                 "close_chat"])])
            return nodes
        return None
