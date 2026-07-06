import os
from npc.base_npc import BaseNPC, DialogueNode, DialogueChoice
from units.mnemonic_devourer import MnemonicDevourer

class MnemonicDevourerNPC(BaseNPC):
    def __init__(self, unit=None):
        super().__init__("mnemonic_devourer")
        self.name = "Mnemonic Devourer"
        self.unit = unit
        if not self.unit:
            self.unit = MnemonicDevourer()
            
        self.portrait_path = "assets/portraits/vortex/MnemonicDevourer"
        self.voice_path = "assets/voices/vortex/MnemonicDevourer"

    def get_portrait_path(self, emotion):
        # Map emotions to filenames
        # angry, annoyed, laughing, neutral, pleased
        
        filename = "MnemonicDevourer_neutral.png"
        if emotion in ["angry", "commanding", "threatening", "furious"]:
            filename = "MnemonicDevourer_angry.png"
        elif emotion in ["annoyed", "disappointed"]:
            filename = "MnemonicDevourer_annoyed.png"
        elif emotion in ["happy", "laughing", "amused"]:
            filename = "MnemonicDevourer_laughing.png"
        elif emotion in ["pleased"]:
            filename = "MnemonicDevourer_pleased.png"
        
        return os.path.join(self.portrait_path, filename)

    def get_voice_path(self, emotion):
        # Map emotions to wav files
        filename = "neutral.wav"
        if emotion == "angry": filename = "angry.wav"
        elif emotion == "annoyed": filename = "annoyed.wav"
        elif emotion == "happy" or emotion == "laughing": filename = "laughing.wav"
        elif emotion == "pleased": filename = "pleased.wav"
        
        return os.path.join(self.voice_path, filename)

    # Apumetodit dialogin rakentamiseen (vastaavat CommanderNPC:tä)
    def node(self, id, text, emotion, choices, on_enter_effects=None):
        return DialogueNode(id=id, text=text, speaker=self.name, emotion=emotion, choices=choices, on_enter_effects=on_enter_effects or [])

    def choice(self, text, next_node_id, effects=None):
        return DialogueChoice(text=text, next_node_id=next_node_id, effects=effects or [])

    def get_dialogue_root(self, context):
        # Tarkista onko taistelu keskeytetty (voitto/häviö scripti)
        flags = context["my_data"].get("flags", {})
        
        # UUSI: Käytä "next_dialogue_node" -lippua ohjaamaan dialogin aloitusta
        if flags.get("next_dialogue_node"):
            node_id = flags["next_dialogue_node"]
            flags["next_dialogue_node"] = None # Nollaa, jotta ei toistu
            return node_id
            
        return "root"

    def get_nodes(self, context):
        return {
            # --- REVEAL ---
            "root": self.node("root", "There you are. You followed the seam... and you brought it with you.", "neutral", [self.choice("...", "demand_1")], on_enter_effects=["flag:met_devourer"]),
            
            # --- DEMAND ---
            "demand_1": self.node("demand_1", "That blade does not belong on this side. Place it on the ground.", "annoyed", [self.choice("...", "demand_final")]),
            "demand_final": self.node("demand_final", "Kneel. Do not make me take it the hard way.", "threatening", [
                self.choice("No.", "resp_refuse"),
                self.choice("What are you?", "resp_question"),
                self.choice("Come closer and I'll cut you down.", "resp_threaten"),
                self.choice("I'm not giving you anything. Tell me why you want it.", "resp_stall")
            ]),

            # --- RESPONSES ---
            "resp_refuse": self.node("resp_refuse", "...Expected.", "neutral", [self.choice("...", "pre_fight")]),
            "resp_question": self.node("resp_question", "A correction. A hand that erases mistakes.", "neutral", [self.choice("...", "pre_fight")]),
            "resp_threaten": self.node("resp_threaten", "Do it again.", "amused", [self.choice("...", "pre_fight")]),
            "resp_stall": self.node("resp_stall", "Because it is yours. And because it is not.", "neutral", [self.choice("...", "pre_fight")]),

            # --- PRE-FIGHT ---
            "pre_fight": self.node("pre_fight", "Show me what you remember.", "threatening", [
                self.choice("[FIGHT]", None, effects=["fight_devourer", "close_chat"])
            ]),

            # --- MID-FIGHT BRANCHES (Triggered by Game Logic) ---
            
            # Branch A: Player Strong (Devourer HP < 50%)
            "fight_interrupted_strong": self.node("fight_interrupted_strong", "...Interesting. You still have teeth. I gave you too much room.", "neutral", [
                self.choice("...", "strong_3")
            ]),
            "strong_3": self.node("strong_3", "Stop it. STOP IT! No more games.", "furious", [
                self.choice("...", "strong_5")
            ]),

            # Branch B: Player Weak (Player HP Low or Time Out)
            "fight_interrupted_weak": self.node("fight_interrupted_weak", "Heh... heh... heh. That's all? You walked this far... for that?", "disappointed", [
                self.choice("...", "weak_2")
            ]),
            "weak_2": self.node("weak_2", "Pathetic. I expected more from the one who carries the seam.", "disappointed", [
                self.choice("...", "weak_3")
            ]),
            "weak_3": self.node("weak_3", "Fine. I will finish this.", "neutral", [
                self.choice("...", "fight_resume_weak")
            ]),
            "fight_resume_weak": self.node("fight_resume_weak", "Your struggle is amusing. Let's continue.", "laughing", [
                self.choice("[Continue Fight]", None, effects=["fight_devourer", "close_chat"])
            ]),
            "strong_5": self.node("strong_5", "I didn't come here to die. I came here to *take you apart*.", "furious", [
                self.choice("...", "fight_resume_strong")
            ]),
            "fight_resume_strong": self.node("fight_resume_strong", "This is not over. You will fall.", "furious", [
                self.choice("[Continue Fight]", None, effects=["fight_devourer", "close_chat"])
            ]),
            
            # --- GENERIC RESUME (Fallback) ---
            "fight_resume_generic": self.node("fight_resume_generic", "Why do we pause? The void hungers.", "annoyed", [
                self.choice("[Resume]", None, effects=["fight_devourer", "close_chat"])
            ]),

            # --- FINAL REVEAL ---
            "final_reveal": self.node("final_reveal", "You misunderstand. I'm not here to kill you.", "neutral", [
                self.choice("...", "final_2")
            ]),
            "final_2": self.node("final_2", "That would be wasteful. You have a place in this.", "neutral", [
                self.choice("...", "final_3")
            ]),
            "final_3": self.node("final_3", "Hold still. Let go.", "neutral", [
                self.choice("...", "final_4")
            ]),
            "final_4": self.node("final_4", "Forget.", "commanding", [
                self.choice("...", "aftermath", effects=["wipe_memory_effect"]) # Screen flash / sound
            ]),

            # --- AFTERMATH ---
            "aftermath": self.node("aftermath", "Good. That belongs to the wound.", "pleased", [
                self.choice("...", "aftermath_2")
            ]),
            "aftermath_2": self.node("aftermath_2", "I'll keep what you can't.", "neutral", [
                self.choice("...", "fade_out")
            ]),
            "fade_out": self.node("fade_out", "When you wake... you won't even know what you lost.", "neutral", [
                self.choice("[Blackout]", None, effects=["steal_sword", "teleport_city", "close_chat"])
            ])
        }