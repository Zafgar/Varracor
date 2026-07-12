from .base_npc import BaseNPC, DialogueNode, DialogueChoice
from quest_system import quest_manager 

class GriznakQuestGiver(BaseNPC):
    def __init__(self):
        super().__init__("griznak_quest_giver")
        self.name = "Griznak the Shifty"

    def get_portrait_path(self, emotion):
        return f"assets/portraits/goblin/{emotion}.png"

    def get_dialogue_root(self, context):
        # 1. QUEST OVERRIDE (Tärkein!)
        # Tarkistetaan ensin, onko aktiivisella/valmiilla questilla sanottavaa.
        # Jos on, palautetaan "start", koska quest-tiedostot käyttävät sitä aloituksena.
        if quest_manager.get_npc_dialogue_override(self.npc_id):
            return "start" 

        # 2. Perus intro-tarkistus
        my_flags = context["my_data"].get("flags", {})
        if not my_flags.get("intro_done"):
            return "root_intro"

        # 3. Reagointi edelliseen taisteluun (Geneerinen, jos ei quest-overridea)
        if quest_manager.pending_reaction:
            if quest_manager.last_battle_result == "win":
                return "root_win"
            elif quest_manager.last_battle_result == "loss":
                return "root_loss"

        # 4. Normaalitila
        if not quest_manager.any_available_quests():
            return "root_empty"
            
        return "root_normal"

    def get_nodes(self, context):
        nodes = {}

        # Urotekojen tunnustus: Griznak kuulee kylän juoruista mitä olet tehnyt
        gdata = context.get("global_data", {})
        deeds = gdata.get("deeds", [])
        if gdata.get("vortex_seen"):
            # Vortex-reaktio: pelko ja kysymykset (lore-paljastus)
            normal_text = ("...I saw what you did out there. That was no arena trick. "
                           "That was the Vortex. Folk are whispering, and not kindly - "
                           "some won't even say the word. What ARE you, really? "
                           "...Bah. Pick a contract, if your hands have stopped shaking.")
        elif deeds:
            normal_text = (f"Word travels, hero. Heard you {deeds[-1]['text']}. "
                           f"Heh. Now pick a contract or get out of my sight.")
        else:
            normal_text = "Back again? Pick a contract or get out of my sight."

        # --- 1. LATAA QUEST-DIALOGIT (Dynaaminen) ---
        # Hakee dialogit suoraan quest-tiedostosta (esim. hunt_rat_king.py)
        # Jos Rat King on voitettu, sieltä tulee nodeja, jotka lisätään tähän listaan.
        quest_dialogue = quest_manager.get_npc_dialogue_override(self.npc_id)
        if quest_dialogue:
            nodes.update(quest_dialogue)
        
        # --- 2. PERUS DIALOGIT (Staattinen) ---
        
        # INTRO
        nodes["root_intro"] = DialogueNode(
            id="root_intro",
            text="Heheh... Look who crawled out of the arena. Fresh meat, looking for real work?",
            speaker="Griznak",
            emotion="neutral",
            choices=[
                DialogueChoice("Who are you?", "intro_1"),
                DialogueChoice("I'm looking for coin.", "intro_2")
            ],
            on_enter_effects=["sound:goblin_laugh"]
        )

        nodes["intro_1"] = DialogueNode(
            id="intro_1",
            text="I am Griznak. I know where the big monsters sleep. And I know who pays to kill them.",
            speaker="Griznak",
            emotion="proud",
            choices=[
                DialogueChoice("Show me the contracts.", "intro_end")
            ]
        )

        nodes["intro_2"] = DialogueNode(
            id="intro_2",
            text="Aren't we all? Listen. The Arena pays peanuts. The Guild pays... better. But only if you survive.",
            speaker="Griznak",
            emotion="neutral",
            choices=[
                DialogueChoice("I can handle it.", "intro_end")
            ]
        )

        nodes["intro_end"] = DialogueNode(
            id="intro_end",
            text="Good. Don't die. It's bad for my reputation. Here is the list.",
            speaker="Griznak",
            emotion="happy",
            choices=[
                DialogueChoice(
                    text="[Open Contracts]", 
                    next_node_id=None, 
                    effects=["flag:intro_done", "close_chat"]
                )
            ]
        )

        # GENEERISET REAKTIOT (Jos questilla ei ole omaa sanottavaa)
        nodes["root_loss"] = DialogueNode(
            id="root_loss",
            text="You look terrible! Did the rats beat you up? Pathetic.",
            speaker="Griznak",
            emotion="happy",
            choices=[
                DialogueChoice("Shut up.", None, effects=["clear_reaction", "close_chat"]),
                DialogueChoice("It was a tactical retreat.", None, effects=["clear_reaction", "close_chat"])
            ]
        )

        nodes["root_win"] = DialogueNode(
            id="root_win",
            text="Not bad. You survived and got paid. Maybe you are worth something after all.",
            speaker="Griznak",
            emotion="proud",
            choices=[
                DialogueChoice("Show me the next job.", None, effects=["clear_reaction", "close_chat"]),
                DialogueChoice("Easy money.", None, effects=["clear_reaction", "close_chat"])
            ]
        )

        nodes["root_empty"] = DialogueNode(
            id="root_empty",
            text="I got nothing for you right now. Come back later.",
            speaker="Griznak",
            emotion="neutral",
            choices=[DialogueChoice("Fine.", None, effects=["close_chat"])]
        )

        nodes["root_normal"] = DialogueNode(
            id="root_normal",
            text=normal_text,
            speaker="Griznak",
            emotion="neutral",
            choices=[DialogueChoice("Just looking.", None, effects=["close_chat"])]
        )

        return nodes