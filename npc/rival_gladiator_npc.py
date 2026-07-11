# npc/rival_gladiator_npc.py
from .base_npc import BaseNPC, DialogueNode, DialogueChoice


# Kanonisia Tier 0 -tiimien jäseniä, jotka lorvivat Muckfordissa.
# (nimi, tiimi, asenne) — asenne ohjaa dialogia.
RIVAL_GLADIATORS = [
    ("Vane Kestrel",  "Shanty Yard Saints",   "arrogant"),
    ("Rook",          "Muckford Ratcatchers", "gruff"),
    ("Sil",           "The Unclaimed Five",   "cagey"),
    ("Bright Ada",    "The Ragged Lanterns",  "warm"),
]

ATTITUDE_LINES = {
    "arrogant": {
        "greeting": "You're the new 'Commander'? The Saints don't lose to mud-teams. Watch and learn.",
        "rep_low": "Nobody's heard of you. Come back when the crowd chants your name.",
        "rep_high": "So you're the one they're all talking about. Enjoy it while it lasts.",
    },
    "gruff": {
        "greeting": "Ratcatcher business. We clear the sewers so the rest of you can sleep. Don't get underfoot.",
        "rep_low": "Green as they come. The rats'll teach you fast.",
        "rep_high": "Heard you can hold a line. Fine. Stay out of our tunnels.",
    },
    "cagey": {
        "greeting": "...The Unclaimed Five don't talk shop with strangers. But everyone's got a price.",
        "rep_low": "Bram's got his eye on you. That's not a compliment.",
        "rep_high": "You're making waves. Careful - waves draw sharks.",
    },
    "warm": {
        "greeting": "Oh, a new team! The Lanterns pull folk out of the dark - maybe we'll pull you out someday too.",
        "rep_low": "Chin up. Everyone starts in the mud here. Even the greats.",
        "rep_high": "The whole quarter's rooting for you now. Don't let the crowd change you.",
    },
}


class RivalGladiatorNPC(BaseNPC):
    """Kilpailevan tiimin gladiaattori kylässä. Asenne riippuu tiimistä
    ja pelaajan maineesta."""

    def __init__(self, name, team, attitude):
        super().__init__(npc_id=f"rival_{name.replace(' ', '_')}")
        self.name = name
        self.team = team
        self.attitude = attitude

    def get_portrait_path(self, emotion):
        return None

    def get_dialogue_root(self, context):
        return "start"

    def get_nodes(self, context):
        lines = ATTITUDE_LINES.get(self.attitude, ATTITUDE_LINES["gruff"])
        rep = int(context.get("reputation", 0))

        text = lines["greeting"]
        if rep > 300:
            text = lines["rep_high"]
        elif rep < 50:
            text = lines["rep_low"]

        nodes = {}
        nodes["start"] = DialogueNode(
            id="start",
            text=text,
            speaker=f"{self.name} ({self.team})",
            emotion="neutral",
            choices=[
                DialogueChoice("We'll see you in the Yard.", "boast"),
                DialogueChoice("Walk away.", None, effects=["close_chat"]),
            ],
        )
        nodes["boast"] = DialogueNode(
            id="boast",
            text="Big talk from a rookie. The Shanty Yard doesn't care about talk. Bring your best - or don't bother.",
            speaker=f"{self.name} ({self.team})",
            emotion="neutral",
            choices=[DialogueChoice("Count on it.", None, effects=["close_chat"])],
        )
        return nodes
