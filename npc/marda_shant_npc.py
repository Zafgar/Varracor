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
                DialogueChoice("Thanks.", "intro_debt", effects=["give_scrap_dagger"])
            ]
        )

        # --- VELKA (Alkutarina: yöt tajuttomana maksavat) ---
        nodes["intro_debt"] = DialogueNode(
            id="intro_debt",
            text="Don't thank me yet. Two nights on my floor, a ruined rug, and the broth I spooned into you - that's 25 gold you owe me. Work it off in the village. Farmer Gus always needs hands, and the woods are full of scrap.",
            speaker=self.name,
            emotion="rude",
            on_enter_effects=["set_innkeeper_debt:25"],
            choices=[
                DialogueChoice("I'll get your money.", None, effects=["close_chat"]),
                DialogueChoice("25 gold?! For a floor?!", "intro_debt_argue")
            ]
        )

        nodes["intro_debt_argue"] = DialogueNode(
            id="intro_debt_argue",
            text="The floor was the cheap part. You screamed about a 'Vortex' half the night and scared away my customers. 25. Gold. Or the guards hear about the stranger who can't pay his debts.",
            speaker=self.name,
            emotion="angry",
            choices=[
                DialogueChoice("Fine. I'll pay.", None, effects=["close_chat"])
            ]
        )

        # --- HUB (Normaali keskustelu) ---
        debt = int(context.get("innkeeper_debt", 0))
        gold = int(context.get("player", {}).get("gold", 0))

        hub_choices = [
            DialogueChoice("I'm looking for recruits.", None, effects=["open_recruit_menu", "close_chat"]),
            DialogueChoice("Any rumors?", "gossip"),
        ]
        if debt > 0:
            hub_choices.insert(0, DialogueChoice(f"About my debt... ({debt} gold)", "debt_status"))
        hub_choices.append(DialogueChoice("Just passing through.", None, effects=["close_chat"]))

        hub_text = "What do you want? I'm busy running a business here, not babysitting."
        if debt > 0:
            hub_text = f"You still owe me {debt} gold. I haven't forgotten, and neither should you."

        nodes["hub"] = DialogueNode(
            id="hub",
            text=hub_text,
            speaker=self.name,
            emotion="normal" if debt <= 0 else "annoyed",
            choices=hub_choices
        )

        if debt > 0:
            if gold >= debt:
                nodes["debt_status"] = DialogueNode(
                    id="debt_status",
                    text=f"Well, well. {debt} gold, and we're square. Hand it over.",
                    speaker=self.name,
                    emotion="thinking",
                    choices=[
                        DialogueChoice(f"Pay {debt} gold.", "debt_paid", effects=["pay_innkeeper_debt"]),
                        DialogueChoice("Not yet.", "hub")
                    ]
                )
                nodes["debt_paid"] = DialogueNode(
                    id="debt_paid",
                    text="Hmph. Didn't think you had it in you. Here - take this old key. My late husband's mining claim, east of the village. Undead crawl that road nowadays, but if you can clear them, the iron is yours. Consider us square.",
                    speaker=self.name,
                    emotion="laughing",
                    on_enter_effects=["give_mine_key"],
                    choices=[DialogueChoice("Pleasure doing business.", None, effects=["close_chat"])]
                )
            else:
                nodes["debt_status"] = DialogueNode(
                    id="debt_status",
                    text=f"You have {gold} gold and you owe me {debt}. Do I look like I take promises? Go shovel manure, chop wood, milk a cow - Muckford pays for honest sweat.",
                    speaker=self.name,
                    emotion="pissed",
                    choices=[DialogueChoice("I'm working on it.", "hub")]
                )
        
        nodes["gossip"] = DialogueNode(
            id="gossip",
            text="Rumors? Hah. Bram Mudhand is looking for fresh meat for the league. And Farmer Gus is complaining about his cows again. The usual misery.",
            speaker=self.name,
            emotion="laughing",
            choices=[DialogueChoice("Back to business.", "hub")]
        )

        return nodes