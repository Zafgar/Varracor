from .base_quest import QuestDefinition
from npc.base_npc import DialogueNode, DialogueChoice


class CrateQuest(QuestDefinition):
    """Krad (Oddments) pyytää noutamaan kadonneen laatikon hökkelimetsän
    talolta ja tuomaan sen kojulle - kuljetustehtävä maineen kasvattamiseen."""

    def __init__(self):
        super().__init__(
            id="quest_krads_crate",
            title="Krad's Missing Crate",
            description="Fetch Krad's crate from the shanty by the woods "
                        "and carry it back to his stall.",
            rep_req=0,
            boss_id=None,
            rewards={"gold": 8, "reputation": 3, "xp": 12}
        )
        self.required_amount = 1

    def get_dialogue_for_npc(self, npc_id, status):
        if npc_id != "Krad":
            return None
        nodes = {}
        if status == "available":
            nodes["start"] = DialogueNode(
                id="start",
                text="Psst. A crate of mine got... misplaced. It waits at "
                     "the shanty by the woods. Fetch it, no questions, and "
                     "there's coin in it for you.",
                speaker="Krad", emotion="neutral",
                choices=[
                    DialogueChoice("I'll get your crate.", "accept",
                                   effects=["accept_quest:quest_krads_crate"]),
                    DialogueChoice("Sounds shady. No.", None,
                                   effects=["close_chat"]),
                ])
            nodes["accept"] = DialogueNode(
                id="accept",
                text="Knew I liked you. The shanty at the wood's edge - "
                     "and don't shake the crate.",
                speaker="Krad", emotion="happy",
                choices=[DialogueChoice("On my way.", None,
                                        effects=["close_chat"])])
            return nodes
        if status == "active":
            nodes["start"] = DialogueNode(
                id="start",
                text="The crate, friend. Shanty. Woods. Legs.",
                speaker="Krad", emotion="neutral",
                choices=[DialogueChoice("Going.", None,
                                        effects=["close_chat"])])
            return nodes
        if status == "completed":
            nodes["start"] = DialogueNode(
                id="start",
                text="Unshaken and unopened! You're wasted on the arena. "
                     "Here - coin, and a good word in the right ears.",
                speaker="Krad", emotion="happy",
                choices=[DialogueChoice("Pleasure doing business.", None,
                                        effects=["finish_quest:quest_krads_crate",
                                                 "close_chat"])])
            return nodes
        return None
