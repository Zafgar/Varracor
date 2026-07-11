import os
from .base_npc import BaseNPC, DialogueNode, DialogueChoice


class HamoNPC(BaseNPC):
    """
    Hamo - goblin bounty broker (Tier 0 -kaanon).
    Liikkuu areenojen liepeillä; Muckfordissa maksaa rottien hännistä
    paremman hinnan kuin markkinakoju ja vihjaa boss-havainnoista.
    """

    def __init__(self):
        super().__init__("hamo")
        self.name = "Hamo"
        self.portrait_folder = "assets/portraits/hamo"
        self.voice_folder = "assets/voices/goblin/hamo"

    def get_portrait_path(self, emotion):
        fname = "normal.png"
        if emotion in ("happy", "laughing"): fname = "grinning.png"
        elif emotion in ("thinking",): fname = "counting.png"
        return os.path.join(self.portrait_folder, fname)

    def get_voice_path(self, emotion):
        fname = "casual.wav"
        if emotion in ("happy", "laughing"): fname = "laughing.wav"
        return os.path.join(self.voice_folder, fname)

    def get_dialogue_root(self, context):
        return "hub"

    def get_nodes(self, context):
        from lore.world_data import HAMO_BOUNTIES
        nodes = {}

        tails = 0
        try:
            tails = int(context.get("inventory", {}).get("Rat Tail", 0))
        except Exception:
            pass
        tail_price = HAMO_BOUNTIES.get("Rat Tail", 4)

        choices = []
        if tails > 0:
            choices.append(DialogueChoice(
                f"[Sell {tails} Rat Tails - {tails * tail_price} gold]",
                "sold_tails",
                effects=["hamo_sell_tails"]))
        choices.append(DialogueChoice("Heard anything about the Rat King?", "boss_tip"))
        choices.append(DialogueChoice("Just passing by.", None, effects=["close_chat"]))

        nodes["hub"] = DialogueNode(
            id="hub",
            text=("Psst. Hamo buys what the arena won't. Rat tails, "
                  f"{tail_price} gold apiece - twice what the stall pays. "
                  "Boss sightings? Even better coin."),
            speaker=self.name,
            emotion="normal",
            choices=choices,
        )

        nodes["sold_tails"] = DialogueNode(
            id="sold_tails",
            text=("Heh heh. Fresh ones. The Consortium pays Hamo, Hamo pays "
                  "you, everybody eats. Bring more - the sewers never run dry."),
            speaker=self.name,
            emotion="happy",
            choices=[DialogueChoice("Pleasure doing business.", None, effects=["close_chat"])],
        )

        nodes["boss_tip"] = DialogueNode(
            id="boss_tip",
            text=("The King's rats come up with PURPLE eyes now. They eat the "
                  "Vortex waste, get meaner. You see purple down there, you "
                  "run - or you bring friends and a big stick."),
            speaker=self.name,
            emotion="thinking",
            choices=[DialogueChoice("Good to know.", "hub")],
        )

        return nodes
