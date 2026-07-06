import os
from npc.base_npc import BaseNPC

# Helper classes for dialogue structure if BaseNPC doesn't provide them
class DialogueNode:
    def __init__(self, id, text, emotion, choices, speaker=None, on_enter_effects=None):
        self.id = id
        self.text = text
        self.emotion = emotion
        self.choices = choices
        self.speaker = speaker
        self.on_enter_effects = on_enter_effects or []

class DialogueChoice:
    def __init__(self, text, next_node_id, condition=None, effects=None):
        self.text = text
        self.next_node_id = next_node_id
        self.condition = condition
        self.effects = effects or []

class CommanderNPC(BaseNPC):
    def __init__(self, unit=None):
        super().__init__("commander_self")
        self.name = "Commander"
        self.unit = unit
        self.portrait_path = "assets/portraits/commander"
        self.voice_path = None

    def get_portrait_path(self, emotion):
        # Map emotions to filenames
        filename = "neutral.png"
        if emotion == "shocked": filename = "shocked.png"
        elif emotion == "angry": filename = "angry.png"
        elif emotion == "happy": filename = "happy.png"
        elif emotion == "thinking": filename = "thinking.png" # Lisätty
        else: filename = "neutral.png"
        
        return os.path.join(self.portrait_path, filename)

    def get_dialogue_root(self, context):
        flags = context["my_data"].get("flags", {})
        if flags.get("vortex_touched"):
            return "vortex_touch"
        return "forest_intro"

    # Helper methods to construct dialogue nodes
    def node(self, id, text, emotion, choices, speaker="Commander", on_enter_effects=None):
        return DialogueNode(id, text, emotion, choices, speaker, on_enter_effects)

    def choice(self, text, next_node_id, condition=None, effects=None):
        return DialogueChoice(text, next_node_id, condition, effects)

    def get_nodes(self, context):
        return {
            "forest_intro": self.node(
                "forest_intro",
                "This weather... it's unnatural. The rain feels heavy, like oil.",
                "neutral",
                [self.choice("Continue...", "forest_intro_2")]
            ),
            "forest_intro_2": self.node(
                "forest_intro_2",
                "I can feel it in my bones. Something is wrong here. The air tastes of... ash.",
                "neutral",
                [self.choice("Look ahead.", "forest_intro_3")]
            ),
            "forest_intro_3": self.node(
                "forest_intro_3",
                "What is that?! A tear in the fabric of the world!",
                "shocked",
                [self.choice("Investigate.", None, effects=["spawn_vortex", "close_chat"])]
            ),
            "vortex_touch": self.node(
                "vortex_touch",
                "It vanished... wait. Something stands in its place. The air ripples around it.",
                "shocked",
                [self.choice("Approach carefully.", None, effects=["close_chat"])]
            )
        }