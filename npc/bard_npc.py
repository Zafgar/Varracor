from .base_npc import BaseNPC, DialogueNode, DialogueChoice
from sound_manager import sound_system
import os
import random

class BardNPC(BaseNPC):
    def __init__(self, unit):
        super().__init__(npc_id="bard")
        self.unit = unit
        self.name = "Julian the Bard"
        self.song_cost = 10
        self.hire_cost = 1000 # Kallis, koska on erikoisyksikkö
        
        # Kuvat
        self.portrait_folder = "assets/portraits/bards"
        self.emotions = {
            "neutral": "bard_neutral.png",   # Vakava
            "happy": "bard_happy.png",       # Nauraa
            "thinking": "bard_thinking.png", # Miettii
            "proud": "bard_proud.png",       # Ylpeä
            "angry": "bard_angry.png",       # Vihainen
            "sad": "bard_sad.png"            # Surullinen
        }

    def get_portrait_path(self, emotion):
        fname = self.emotions.get(emotion, "bard_neutral.png")
        return os.path.join(self.portrait_folder, fname)

    def get_dialogue_root(self, context):
        flags = context["my_data"]["flags"]
        
        # Jos jo palkattu (tämä tarkistus on varalla, jos hän on tavernassa vaikka on palkattu)
        if flags.get("is_hired"):
            return "hired_hub"

        if not flags.get("met_before"):
            return "intro"
        
        return "hub"

    def get_nodes(self, context):
        nodes = {}
        player_gold = context["player"]["gold"]
        reputation = context.get("reputation", 0)
        rank = context.get("league_rank", 99)
        flags = context["my_data"]["flags"]
        
        # Onko pelaaja "Nobody" vai "Legend"?
        is_famous = reputation > 800 or rank <= 3
        is_nobody = reputation < 200 and rank > 10
        
        # Tarkista onko Bard jo soittamassa
        ai = getattr(self.unit, "ai_controller", None)
        is_playing = ai and ai.state == "performing"
        
        # --- INTRO ---
        if is_famous:
            intro_text = f"Wait... I know that face. You're the Commander from the arena! The one everyone is whispering about. Julian, at your service. An honor."
            intro_emotion = "happy"
        elif is_nobody:
            intro_text = "Greetings, traveler. The acoustics in here are... acceptable. I am Julian. If you have coin, I have songs. If not, enjoy the silence."
            intro_emotion = "neutral"
        else:
            intro_text = "Ah, a patron with a sword. A mercenary? I am Julian. I collect stories and sing them. Do you have a story worth telling?"
            intro_emotion = "intrigued"

        nodes["intro"] = DialogueNode(
            id="intro",
            text=intro_text,
            speaker=self.name,
            emotion=intro_emotion,
            on_enter_effects=["flag:met_before"],
            choices=[
                DialogueChoice("I need a song.", "hub"),
                DialogueChoice("What do you know about this place?", "lore_hub"),
                DialogueChoice("Just passing through.", None, effects=["close_chat"])
            ]
        )

        # --- HUB ---
        hub_text = "The strings are ready. What is your request?"
        if is_playing:
            hub_text = "I hope the melody pleases you. It helps drown out the screams from the cellar."
        
        nodes["hub"] = DialogueNode(
            id="hub",
            text=hub_text,
            speaker=self.name,
            emotion="neutral",
            choices=[]
        )
        
        # 1. Play Song
        if not is_playing:
            if player_gold >= self.song_cost:
                nodes["hub"].choices.append(
                    DialogueChoice(f"Play a song. ({self.song_cost} Gold)", "play_song", effects=[f"pay_bard:{self.song_cost}", "close_chat"])
                )
            else:
                nodes["hub"].choices.append(
                    DialogueChoice(f"I'd request a song, but I'm short on coin.", "poor")
                )
        
        # 2. Lore / News
        nodes["hub"].choices.append(DialogueChoice("What's the news?", "lore_hub"))
        
        # 3. Recruit (Vain jos kuuluisa)
        if is_famous and not flags.get("is_hired"):
            nodes["hub"].choices.append(DialogueChoice("Join my Guild. I need a personal bard.", "recruit_start"))

        nodes["hub"].choices.append(DialogueChoice("Goodbye.", None, effects=["close_chat"]))

        # --- LORE HUB ---
        nodes["lore_hub"] = DialogueNode(
            id="lore_hub",
            text="I hear everything. The wind carries secrets from the Vortex, and the rats carry secrets from the gutter. What interests you?",
            speaker=self.name,
            emotion="thinking",
            choices=[
                DialogueChoice("Tell me about the Arena.", "lore_arena"),
                DialogueChoice("What is happening with the Vortex?", "lore_vortex"),
                DialogueChoice("Any political rumors?", "lore_politics"),
                DialogueChoice("Back.", "hub")
            ]
        )

        # Lore: Arena
        arena_gossip = [
            "They say the 'Shanty Yard Saints' fight for food, but the 'Unclaimed Five' fight because they enjoy the blood. Watch out for them.",
            "Have you heard of 'The Spin'? Some gladiators stare into the Vortex too long. They gain power, but lose their minds. The crowd loves a tragedy.",
            "Rivet Row has a new cage match. Electrified floors. Nasty business.",
            "Sera Quench is looking for a star. Not a fighter, a *star*. If you want out of Tier 0, you need to put on a show."
        ]
        nodes["lore_arena"] = DialogueNode(
            id="lore_arena",
            text=random.choice(arena_gossip),
            speaker=self.name,
            emotion="intrigued",
            choices=[DialogueChoice("Interesting.", "lore_hub")]
        )

        # Lore: Vortex
        vortex_gossip = [
            "The Thirst That Walks... travelers from Saffron say the water tastes like soap. That means Drownfoam is rising.",
            "In Rattlebridge, they speak of the Hush-Mantle. A fog that eats sound. If you hear nothing, run.",
            "Don't touch the frost on the windows in summer. It's not ice. It's residue.",
            "The Vortex isn't just a storm. It reacts. It knows when we are afraid."
        ]
        nodes["lore_vortex"] = DialogueNode(
            id="lore_vortex",
            text=random.choice(vortex_gossip),
            speaker=self.name,
            emotion="sad",
            choices=[DialogueChoice("Grim tales.", "lore_hub")]
        )

        # Lore: Politics
        politics_gossip = [
            "Bram Carrow keeps a ledger. They say he knows every debt in Muckford. Even the Mayor's.",
            "Hamo is buying rat tails at double price. That means a swarm is coming. Or he's feeding something big.",
            "Marcellus Vane in Giltgate claims to own the air we breathe. He calls it 'Atmospheric Tax'.",
            "The Crown Dominion pretends to rule, but out here? The Guilds are the law."
        ]
        nodes["lore_politics"] = DialogueNode(
            id="lore_politics",
            text=random.choice(politics_gossip),
            speaker=self.name,
            emotion="thinking",
            choices=[DialogueChoice("Good to know.", "lore_hub")]
        )

        # --- RECRUITMENT ---
        nodes["recruit_start"] = DialogueNode(
            id="recruit_start",
            text=f"You want me to chronicle your deeds? A personal bard for the Guild House... It is tempting. The ale here is watered down anyway. My fee is {self.hire_cost} Gold. Up front.",
            speaker=self.name,
            emotion="proud",
            choices=[]
        )

        if player_gold >= self.hire_cost:
            nodes["recruit_start"].choices.append(
                DialogueChoice(f"You're hired. ({self.hire_cost} Gold)", "recruit_confirm", 
                               effects=[f"pay_bard:{self.hire_cost}", "hire_bard", "close_chat"])
            )
        else:
            nodes["recruit_start"].choices.append(
                DialogueChoice("That's too much for a songbird.", "recruit_poor")
            )
        nodes["recruit_start"].choices.append(DialogueChoice("Changed my mind.", "hub"))

        nodes["recruit_poor"] = DialogueNode(
            id="recruit_poor",
            text="Talent isn't cheap, Commander. Come back when your treasury matches your ambition.",
            speaker=self.name,
            emotion="neutral",
            choices=[DialogueChoice("I will.", "hub")]
        )

        nodes["poor"] = DialogueNode(
            id="poor",
            text="Music feeds the soul, but coin feeds the bard. Come back when your purse is heavier.",
            speaker=self.name,
            emotion="neutral",
            choices=[DialogueChoice("Goodbye.", None, effects=["close_chat"])]
        )
        
        # --- HIRED STATE ---
        nodes["hired_hub"] = DialogueNode(
            id="hired_hub",
            text="Commander! The Guild Hall has excellent acoustics. I am composing a ballad about your victory over the Rat King.",
            speaker=self.name,
            emotion="happy",
            choices=[DialogueChoice("Carry on.", None, effects=["close_chat"])]
        )

        return nodes
