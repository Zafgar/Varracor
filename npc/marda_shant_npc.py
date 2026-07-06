import os
from .base_npc import BaseNPC, DialogueNode, DialogueChoice

class MardaShantNPC(BaseNPC):
    def __init__(self):
        super().__init__("marda_shant")
        self.name = "Marda Shant"
        self.portrait_folder = "assets/portraits/mardashant"
        self.voice_folder = "assets/voices/human/marda"

    def get_portrait_path(self, emotion):
        # angry, laughing, normal, pissed, rude, thinking
        fname = "normal.png"
        if emotion == "angry": fname = "angry.png"
        elif emotion == "laughing" or emotion == "happy": fname = "laughing.png"
        elif emotion == "pissed" or emotion == "annoyed": fname = "pissed.png"
        elif emotion == "rude": fname = "rude.png"
        elif emotion == "thinking": fname = "thinking.png"
        
        return os.path.join(self.portrait_folder, fname)

    def get_voice_path(self, emotion):
        fname = "casual.wav"
        if emotion == "angry": fname = "shouting.wav"
        elif emotion == "laughing" or emotion == "happy": fname = "laughing.wav"
        elif emotion == "pissed" or emotion == "annoyed": fname = "pissed.wav"
        elif emotion == "rude": fname = "rude.wav"
        elif emotion == "thinking": fname = "thinking.wav"
        elif emotion == "arrogant": fname = "arrogant.wav"
        elif emotion == "normal": fname = "casual.wav"
        
        return os.path.join(self.voice_folder, fname)

    def get_dialogue_root(self, context):
        flags = context["my_data"].get("flags", {})
        
        # Jos pelaaja on juuri herännyt (ensimmäinen kerta)
        if not flags.get("met"):
            return "intro_wakeup"
            
        return "hub"

    def get_nodes(self, context):
        nodes = {}
        
        # --- INTRO (Herääminen) ---
        nodes["intro_wakeup"] = DialogueNode(
            id="intro_wakeup",
            text="Finally awake? You've been drooling on my floor for two days. I was about to charge you rent for the rug.",
            speaker=self.name,
            emotion="rude",
            choices=[
                DialogueChoice("Where am I?", "intro_where"),
                DialogueChoice("My head hurts...", "intro_mock")
            ]
        )
        
        nodes["intro_where"] = DialogueNode(
            id="intro_where",
            text="The Sunk Cask. Muckford. The armpit of the world. Someone dumped you in the alley. Stripped you clean, too.",
            speaker=self.name,
            emotion="normal",
            choices=[DialogueChoice("I have nothing left.", "intro_gift")]
        )
        
        nodes["intro_mock"] = DialogueNode(
            id="intro_mock",
            text="Boo hoo. Drink some water and get over it. You're lucky the rats didn't eat your toes.",
            speaker=self.name,
            emotion="pissed",
            choices=[DialogueChoice("Where is my gear?", "intro_where")]
        )
        
        nodes["intro_gift"] = DialogueNode(
            id="intro_gift",
            text="I know. Look, I'm not running a charity, but I can't have customers dying of exposure. Take this rusty shiv. It's better than your bare hands.",
            speaker=self.name,
            emotion="thinking",
            on_enter_effects=["flag:met"], # Merkitään tavatuksi
            choices=[
                DialogueChoice("Thanks.", None, effects=["give_scrap_dagger", "close_chat"])
            ]
        )

        # --- HUB (Normaali keskustelu) ---
        nodes["hub"] = DialogueNode(
            id="hub",
            text="What do you want? I'm busy running a business here, not babysitting.",
            speaker=self.name,
            emotion="normal",
            choices=[
                DialogueChoice("I'm looking for recruits.", None, effects=["open_recruit_menu", "close_chat"]),
                DialogueChoice("Any rumors?", "gossip"),
                DialogueChoice("Just passing through.", None, effects=["close_chat"])
            ]
        )
        
        nodes["gossip"] = DialogueNode(
            id="gossip",
            text="Rumors? Hah. Bram Mudhand is looking for fresh meat for the league. And Farmer Gus is complaining about his cows again. The usual misery.",
            speaker=self.name,
            emotion="laughing",
            choices=[DialogueChoice("Back to business.", "hub")]
        )

        return nodes