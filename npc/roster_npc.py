# npc/roster_npc.py
from .base_npc import BaseNPC, DialogueNode, DialogueChoice
from progression.personality import (
    PERSONALITIES, ORIGIN_DESC, relationship_tier, get_line, deeds_summary,
)


class RosterNPC(BaseNPC):
    """
    Oman joukkueen gladiaattorin dialogi. Rivit muuttuvat luonteen,
    pelaajaan-suhteen (relationship) ja urotöiden (deeds) mukaan.
    Jokainen "juttele" nostaa suhdetta hieman.
    """

    def __init__(self, unit):
        super().__init__(npc_id=f"gladiator_{unit.name}")
        self.unit = unit
        self.name = unit.name

    def get_portrait_path(self, emotion):
        return None  # ChatMenu käyttää yksikön omaa kuvaa

    def get_dialogue_root(self, context):
        return "start"

    def get_nodes(self, context):
        u = self.unit
        personality = getattr(u, "personality", None) or "grizzled"
        pdata = PERSONALITIES.get(personality, PERSONALITIES["grizzled"])

        # Suhde pelaajaan npc-muistista
        my_data = context.get("my_data", {})
        rel = int(my_data.get("relationship", 0))
        tier = relationship_tier(rel)

        greeting = get_line(personality, "greeting", tier)
        banter = get_line(personality, "banter", tier)

        nodes = {}
        nodes["start"] = DialogueNode(
            id="start",
            text=greeting,
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice("How are you holding up?", "banter"),
                DialogueChoice("Tell me about yourself.", "backstory"),
                DialogueChoice("Good talk. (+relationship)", None,
                               effects=["rep:3", "close_chat"]),
                DialogueChoice("Later.", None, effects=["close_chat"]),
            ],
        )

        nodes["banter"] = DialogueNode(
            id="banter",
            text=banter,
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice("Keep at it. (+relationship)", "start",
                               effects=["rep:2"]),
                DialogueChoice("Back to it.", None, effects=["close_chat"]),
            ],
        )

        origin = getattr(u, "origin", None)
        origin_line = ORIGIN_DESC.get(origin, "A past best left buried.")
        deeds = deeds_summary(u)
        story = (f"They call me {self.name}, a {pdata['name'].lower()} "
                 f"{u.race_name}. {origin_line} These days I'm {deeds}.")

        nodes["backstory"] = DialogueNode(
            id="backstory",
            text=story,
            speaker=self.name,
            emotion="neutral",
            choices=[
                DialogueChoice("We've come a long way. (+relationship)", "start",
                               effects=["rep:2"]),
                DialogueChoice("Understood.", None, effects=["close_chat"]),
            ],
        )
        return nodes
