import os
from settings import *
from .base_npc import BaseNPC, DialogueNode, DialogueChoice

class GrandMortarch(BaseNPC):
    def __init__(self):
        super().__init__("grand_mortarch")
        self.name = "Grand Mortarch Zharok"
        
        # Määritellään kuvat ja äänet
        self.assets_dir = "assets/portraits/mortarch"
        self.voice_dir = "assets/voices/mortarch"
        
        # 10 ilmettä/tyyliä
        self.emotions = {
            "neutral": "mortarch_neutral.png",
            "stern": "mortarch_stern.png",
            "intrigued": "mortarch_intrigued.png",
            "commanding": "mortarch_commanding.png",
            "disappointed": "mortarch_disappointed.png",
            "pleased": "mortarch_pleased.png",
            "analyzing": "mortarch_analyzing.png",
            "warning": "mortarch_warning.png",
            "casting": "mortarch_casting.png",
            "silence": "mortarch_silence.png"
        }
        
        self.voices = {
            "intro": "mortarch_intro.wav",
            "neutral": "mortarch_neutral.wav",
            "stern": "mortarch_stern.wav",
            "intrigued": "mortarch_intrigued.wav",
            "dismissive": "mortarch_dismissive.wav",
            "approve": "mortarch_approve.wav",
            "warn": "mortarch_warn.wav",
            "explain": "mortarch_explain.wav",
            "ritual": "mortarch_ritual.wav",
            "silence": "mortarch_silence.wav"
        }

    def get_portrait_path(self, emotion):
        filename = self.emotions.get(emotion, "mortarch_neutral.png")
        return os.path.join(self.assets_dir, filename)

    def get_voice_path(self, emotion):
        filename = self.voices.get(emotion, "mortarch_neutral.wav")
        return os.path.join(self.voice_dir, filename)

    def get_dialogue_root(self, context):
        # Context sisältää: my_data (flags, relationship), global_data (reputation), player (gold, name)
        flags = context["my_data"]["flags"]
        
        # 1. ENSIESITTELY (Jos ei ole tavattu)
        if not flags.get("intro_done", False):
            return "intro_start"
            
        # 2. NORMAALI KESKUSTELU (Riippuu maineesta)
        rep = context["my_data"]["relationship"]
        
        if rep < -500:
            return "root_hated"
        elif rep > 1000:
            return "root_respected"
        else:
            return "root_neutral"

    def get_nodes(self, context):
        # Haetaan dataa kontekstista logiikkaa varten
        player_name = context["player"]["name"]
        global_rep = context["global_data"]["reputation"]
        ashen_rep = context["my_data"]["relationship"]
        
        # Tarkistetaan onko pelaaja "Holy" -myönteinen (Crown Dominion rep)
        # Oletetaan että GameManagerin reputations-dict on saatavilla contextin kautta tai haetaan se
        # Yksinkertaistuksen vuoksi käytetään tässä placeholder-logiikkaa
        is_holy_aligned = False # Tähän voisi lisätä tarkistuksen myöhemmin

        nodes = {}

        # --- INTRO SEQUENCE ---
        
        intro_text = "You stand within the Bonewind Necropolis. The air is dry and smells of preservation salts."
        if global_rep > 2000:
            intro_text += f" I know of you, {player_name}. Your fame echoes loudly. But noise does not impress me."
        else:
            intro_text += " Another stray seeking power. Tread carefully."

        nodes["intro_start"] = DialogueNode(
            id="intro_start",
            speaker="Zharok the Quiet",
            text=intro_text,
            emotion="neutral",
            on_enter_effects=["flag:intro_done"], # Merkitään nähdyksi
            choices=[
                DialogueChoice(text="Who are you?", next_node_id="intro_identity"),
                DialogueChoice(text="I seek to learn Necromancy.", next_node_id="intro_necromancy"),
                DialogueChoice(text="[Look around] This place is... orderly.", next_node_id="intro_order")
            ]
        )

        nodes["intro_identity"] = DialogueNode(
            id="intro_identity",
            speaker="Zharok the Quiet",
            text="I am Grand Mortarch Zharok. I hold the keys to the Ashen Ossuary. I am the architect of the final threshold.",
            emotion="stern",
            choices=[
                DialogueChoice(text="What is this place?", next_node_id="intro_purpose"),
                DialogueChoice(text="I am here to trade.", next_node_id="intro_end")
            ]
        )

        nodes["intro_order"] = DialogueNode(
            id="intro_order",
            speaker="Zharok the Quiet",
            text="Death is a process. It has rules. Structure. Only the Vortex introduces chaos. We are here to correct that error.",
            emotion="approve",
            on_enter_effects=["rep:50"], # Pieni bonus oikeasta asenteesta
            choices=[
                DialogueChoice(text="I agree. Chaos must be contained.", next_node_id="intro_purpose"),
                DialogueChoice(text="I just want power.", next_node_id="intro_power")
            ]
        )

        nodes["intro_necromancy"] = DialogueNode(
            id="intro_necromancy",
            speaker="Zharok the Quiet",
            text="Necromancy is not a toy. It is surgery on the fabric of existence. One slip, and the Vortex claims you.",
            emotion="warning",
            choices=[
                DialogueChoice(text="I am disciplined.", next_node_id="intro_purpose"),
                DialogueChoice(text="I'll take my chances.", next_node_id="intro_dismiss")
            ]
        )
        
        nodes["intro_power"] = DialogueNode(
            id="intro_power",
            speaker="Zharok the Quiet",
            text="Power without control is a wildfire. It burns the wielder first. Do not waste my time with ambition. Show me results.",
            emotion="disappointed",
            on_enter_effects=["rep:-20"],
            choices=[
                DialogueChoice(text="Understood.", next_node_id="intro_end")
            ]
        )

        nodes["intro_dismiss"] = DialogueNode(
            id="intro_dismiss",
            speaker="Zharok the Quiet",
            text="Then you will likely die screaming. The Ossuary does not mourn fools.",
            emotion="dismissive",
            choices=[
                DialogueChoice(text="...", next_node_id="intro_end")
            ]
        )

        nodes["intro_purpose"] = DialogueNode(
            id="intro_purpose",
            speaker="Zharok the Quiet",
            text="The Vortex animates the dead without permission. It creates a mockery of life. We bind the restless. We study the Essence signatures to seal the breach.",
            emotion="analyzing",
            choices=[
                DialogueChoice(text="How can I help?", next_node_id="intro_essence"),
                DialogueChoice(text="I see.", next_node_id="intro_end")
            ]
        )

        nodes["intro_essence"] = DialogueNode(
            id="intro_essence",
            speaker="Zharok the Quiet",
            text="When you cull the undead, sometimes a fragment remains. A Spirit Essence. Bring them to me. Do not let them dissipate back into the Vortex.",
            emotion="intrigued",
            choices=[
                DialogueChoice(text="I will gather them.", next_node_id="intro_end")
            ]
        )

        nodes["intro_end"] = DialogueNode(
            id="intro_end",
            speaker="Zharok the Quiet",
            text="We are done. The archives are open to those who prove their worth. Do not disturb the silence without cause.",
            emotion="silence",
            choices=[
                DialogueChoice(text="[Leave]", next_node_id=None) # None sulkee chatin
            ]
        )

        # --- ROOT NODES (Recurring) ---

        nodes["root_neutral"] = DialogueNode(
            id="root_neutral",
            speaker="Zharok the Quiet",
            text="The Mortarch looks up from a scroll of flayed skin. 'Speak.'",
            emotion="neutral",
            choices=[
                DialogueChoice(text="I have Spirit Essence to offer.", next_node_id=None), # Tämä sulkee chatin ja pelaaja on menussa
                DialogueChoice(text="Tell me about the Vortex.", next_node_id="lore_vortex"),
                DialogueChoice(text="[Leave]", next_node_id=None)
            ]
        )

        nodes["root_respected"] = DialogueNode(
            id="root_respected",
            speaker="Zharok the Quiet",
            text="Ah, the Binder returns. Your work in the field has provided valuable data. The Ossuary acknowledges you.",
            emotion="pleased",
            choices=[
                DialogueChoice(text="I have more Essence.", next_node_id=None),
                DialogueChoice(text="Teach me higher mysteries.", next_node_id="lore_mastery"),
                DialogueChoice(text="[Leave]", next_node_id=None)
            ]
        )

        nodes["root_hated"] = DialogueNode(
            id="root_hated",
            speaker="Zharok the Quiet",
            text="You are a disruption. A variable I should eliminate. Give me one reason not to have you thrown into the pit.",
            emotion="stern",
            choices=[
                DialogueChoice(text="I have gold.", next_node_id=None),
                DialogueChoice(text="[Leave]", next_node_id=None)
            ]
        )

        # --- LORE NODES ---

        nodes["lore_vortex"] = DialogueNode(
            id="lore_vortex",
            speaker="Zharok the Quiet",
            text="The Vortex is a wound. It bleeds magic that defies physics. The Radiant Synod calls it 'evil'. I call it 'inefficient'. It wastes potential.",
            emotion="analyzing",
            choices=[
                DialogueChoice(text="Interesting perspective.", next_node_id="root_neutral")
            ]
        )

        nodes["lore_mastery"] = DialogueNode(
            id="lore_mastery",
            speaker="Zharok the Quiet",
            text="True mastery is not about raising an army. Any fool can animate a corpse. True mastery is preventing the corpse from decaying while it serves you.",
            emotion="casting",
            choices=[
                DialogueChoice(text="I understand.", next_node_id="root_respected")
            ]
        )

        return nodes
