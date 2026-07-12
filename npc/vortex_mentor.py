# npc/vortex_mentor.py
"""
Tia Muir - the Vortex entity that stopped the hero and took his memory.

She is the reason the game begins the way it does: she halted the Commander so
he would learn to *see the other reality* woven through everything, and she does
not blame the Vortex-born for the world's troubles. She is, arguably, right -
things are not black and white. Because the hero forgot both himself and her,
their conversations are lessons: she teaches him the Abyssal Weave, the arts the
world calls forbidden and she calls the Tia Muira ("the seeing").

Encountered through Vortex-rifts (random Vortex encounters unlock her lessons).
Each lesson she gives opens one of the five Abyssal skill trees.

Portraits/voices come later; dialogue is ready.
"""
import os
from .base_npc import BaseNPC, DialogueNode, DialogueChoice

# Taitopuu -> (opetuksen nimi, opetusteksti)
LESSONS = {
    "warping": (
        "Warping",
        "Space is not a wall; it is a suggestion. Stop asking to move through it "
        "and simply agree with it that you are already elsewhere. There. Feel the "
        "seam? Fold it."),
    "anchoring": (
        "Anchoring",
        "Everything that flees is only borrowing motion it did not earn. Take it "
        "back. Hold a thing to its place and even the Vortex cannot pull it loose. "
        "You are an anchor now - learn to drop it."),
    "severing": (
        "Severing",
        "Every ward, every summons, every lie is a thread tied to something. You "
        "have always been able to cut. Most never learn *what*. Find the thread "
        "that should not be - and sever it."),
    "echoing": (
        "Echoing",
        "Time is not a river. It is a held breath. A moment can be repeated; a "
        "wound can be un-had. Do not command it - remind it. It remembers being "
        "whole."),
    "taint": (
        "Taint Management",
        "They fear the corruption because they cannot hold it. You can. Take the "
        "rot into your hand, weigh it, and let it become strength before it becomes "
        "ruin. This is the hardest seeing, and the truest."),
}


class VortexMentor(BaseNPC):
    def __init__(self):
        super().__init__("vortex_mentor")
        self.name = "Tia Muir"
        self.assets_dir = "assets/portraits/vortex_mentor"

    def get_portrait_path(self, emotion):
        return os.path.join(self.assets_dir, f"{emotion}.png")

    def get_dialogue_root(self, context):
        flags = context["my_data"].get("flags", {})
        if not flags.get("met_before"):
            return "first_meeting"
        return "hub"

    def get_nodes(self, context):
        gdata = context.get("global_data", {})
        learned = set(gdata.get("magic", {}).get("abyssal_trees", []))
        nodes = {}

        # --- ENSIKOHTAAMINEN ---
        nodes["first_meeting"] = DialogueNode(
            id="first_meeting",
            speaker="???",
            text=("The air unstitches. Something that is almost a person is standing "
                  "in the tear. 'You don't remember me. Good - that means it held.' "
                  "'I am the one who stopped you. I took your name so you could set "
                  "it down and finally look.'"),
            emotion="calm",
            on_enter_effects=["flag:met_before"],
            choices=[
                DialogueChoice("You erased my memory. Why?", "why"),
                DialogueChoice("You're one of the Vortex things. You did this to us.", "blame"),
            ],
        )

        nodes["why"] = DialogueNode(
            id="why",
            speaker="Tia Muir",
            text=("'Because you were about to win the wrong war. You saw one reality - "
                  "the loud one, with its banners and its blame - and you were very "
                  "good at it. I needed you to see the other one underneath. So I "
                  "stopped you, and let the noise fall out of your head.'"),
            emotion="calm",
            choices=[
                DialogueChoice("The other reality?", "other_reality"),
                DialogueChoice("Then give my name back.", "name"),
            ],
        )

        nodes["blame"] = DialogueNode(
            id="blame",
            speaker="Tia Muir",
            text=("'We did not make your famines, your debts, your little cruelties. "
                  "Those were yours long before the first rift opened. The Vortex is "
                  "a mirror your world would rather smash than look into.' She is not "
                  "angry. That is the unsettling part - she might be right."),
            emotion="knowing",
            choices=[
                DialogueChoice("...Maybe. Show me, then.", "other_reality"),
                DialogueChoice("I don't accept that.", "grey"),
            ],
        )

        nodes["grey"] = DialogueNode(
            id="grey",
            speaker="Tia Muir",
            text=("'You don't have to. Nothing here is clean - not me, not the Synod "
                  "that would burn me, not you. Accept only this: the answer you were "
                  "chasing was too simple to be true. Learn to see, and decide for "
                  "yourself.'"),
            emotion="calm",
            choices=[DialogueChoice("Teach me, then.", "other_reality")],
        )

        nodes["name"] = DialogueNode(
            id="name",
            speaker="Tia Muir",
            text=("'When you can see well enough to hold it without it holding you. "
                  "Not before. A name is a thread too - and you are not yet ready to "
                  "learn what yours is tied to.'"),
            emotion="knowing",
            choices=[DialogueChoice("...Fine. Teach me.", "other_reality")],
        )

        nodes["other_reality"] = DialogueNode(
            id="other_reality",
            speaker="Tia Muir",
            text=("'The Weave is not a school with walls. It is Tia Muira - the seeing. "
                  "I will teach it to you a thread at a time, each time the rifts let "
                  "us meet. Choose what you are ready to see.'"),
            emotion="calm",
            choices=self._lesson_choices(learned) + [DialogueChoice("Not now.", "hub")],
        )

        # --- HUB (myohemmat kohtaamiset) ---
        nodes["hub"] = DialogueNode(
            id="hub",
            speaker="Tia Muir",
            text=("The tear opens again. 'Still here. Still looking. Good. What will "
                  "you learn to see today?'"),
            emotion="calm",
            choices=self._lesson_choices(learned) + [
                DialogueChoice("Why do you help me?", "grey"),
                DialogueChoice("[Step back through]", None),
            ],
        )

        # --- OPETUS-NODET (yksi per taitopuu) ---
        for tree, (label, text) in LESSONS.items():
            already = tree in learned
            nodes[f"lesson_{tree}"] = DialogueNode(
                id=f"lesson_{tree}",
                speaker="Tia Muir",
                text=(f"[{label}] {text}" if not already
                      else f"'You already see the {label} weave. Do not waste it.'"),
                emotion="knowing",
                on_enter_effects=([f"learn_abyssal:{tree}"] if not already else []),
                choices=[DialogueChoice("[The seeing settles into you]", "hub")],
            )

        return nodes

    def _lesson_choices(self, learned):
        out = []
        for tree, (label, _t) in LESSONS.items():
            tag = " (known)" if tree in learned else ""
            out.append(DialogueChoice(f"Teach me the {label} weave{tag}.",
                                      f"lesson_{tree}"))
        return out
