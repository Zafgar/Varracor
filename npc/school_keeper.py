# npc/school_keeper.py
"""
Yleiskayttoinen magiakoulun pitaja-NPC (Pure/Holy/Druidism/Manipulation).

Yksi luokka parametrisoituna koulukunnalla: dialogit rakennetaan lore-datasta
(magic/schools.py) ja avaamisvaatimuksista (magic/progression.py). Necromancylla
on oma bespoke-pitaja (grand_mortarch.py, Zharok).

Portaitit lisataan myohemmin (get_portrait_path osoittaa paikkaan); dialogit
ovat valmiina jo nyt.
"""
import os
from .base_npc import BaseNPC, DialogueNode, DialogueChoice
from magic.schools import SCHOOLS
from magic.progression import SCHOOL_UNLOCK, unlock_requirement_text


# npc_id -> koulukunta-avain
KEEPER_SCHOOL = {
    "keeper_pure": "pure",
    "keeper_holy": "holy",
    "keeper_druid": "druidism",
    "keeper_manip": "manipulation",
}


class SchoolKeeper(BaseNPC):
    def __init__(self, npc_id):
        super().__init__(npc_id)
        self.school_key = KEEPER_SCHOOL.get(npc_id, "pure")
        self.school = SCHOOLS.get(self.school_key, {})
        self.req = SCHOOL_UNLOCK.get(self.school_key, {})
        self.name = self.req.get("keeper", self.school.get("leader", "Magister"))
        self.assets_dir = f"assets/portraits/{self.school_key}"

    def get_portrait_path(self, emotion):
        return os.path.join(self.assets_dir, f"{emotion}.png")

    def get_dialogue_root(self, context):
        flags = context["my_data"].get("flags", {})
        if not flags.get("intro_done"):
            return "intro"
        # Onko koulu jo auki pelaajalle?
        gm = getattr(self, "_manager", None)
        return "root"

    def get_nodes(self, context):
        s = self.school
        req = self.req
        name = self.name
        org = s.get("name", "the school")
        seat = req.get("location", s.get("seat", "the seat"))
        character = s.get("character", "")
        reqtext = unlock_requirement_text(self.school_key)

        # Onko pelaaja jo hyvaksytty? (global magic-tila)
        gdata = context.get("global_data", {})
        opened = gdata.get("flags", {}).get(f"school_{self.school_key}_open")
        already = self.school_key in gdata.get("magic", {}).get("schools", []) or opened
        just_denied = gdata.get("flags", {}).get(f"school_{self.school_key}_denied")

        nodes = {}

        nodes["intro"] = DialogueNode(
            id="intro",
            speaker=name,
            text=(f"You stand in {seat}, the seat of {org}. I am {name}. "
                  f"{character}"),
            emotion="neutral",
            on_enter_effects=["flag:intro_done"],
            choices=[
                DialogueChoice("Teach me about your magic.", "teach"),
                DialogueChoice("I seek admission.", "admit"),
                DialogueChoice("[Leave]", None),
            ],
        )

        nodes["teach"] = DialogueNode(
            id="teach",
            speaker=name,
            text=("Magic is common knowledge - true command of it is not. It takes "
                  "discipline, drilling, and endurance; every spell exacts a toll of "
                  "arcane strain on body and mind. The first three tiers anyone may "
                  "learn through Pure Magic. To pass beyond them into our art, you "
                  "must be one of us."),
            emotion="analyzing",
            choices=[
                DialogueChoice("And how do I join?", "admit"),
                DialogueChoice("I see.", "root"),
            ],
        )

        # Admission haara riippuu tilasta
        if already:
            admit_node = DialogueNode(
                id="admit",
                speaker=name,
                text=f"You already walk our path. {org} is open to you.",
                emotion="pleased",
                choices=[DialogueChoice("Thank you.", "root")],
            )
        else:
            admit_node = DialogueNode(
                id="admit",
                speaker=name,
                text=(f"Admission is not bought with coin alone. Bring what we ask "
                      f"and prove your standing: {reqtext}. Then I will open the "
                      f"doors of {org} to you."),
                emotion="stern",
                choices=[
                    DialogueChoice("[Offer what you have]", "attempt",
                                   effects=[f"unlock_school:{self.school_key}"]),
                    DialogueChoice("Not yet.", "root"),
                ],
            )
        nodes["admit"] = admit_node

        # Tulos-node (unlock_school-efekti ajettu valinnassa)
        nodes["attempt"] = DialogueNode(
            id="attempt",
            speaker=name,
            text=("The doors open. Welcome to our number - do not make me regret it. "
                  f"({org})" if not just_denied else
                  f"You lack what we require. Return with {reqtext}."),
            emotion="pleased",
            choices=[DialogueChoice("[Continue]", "root")],
        )

        nodes["root"] = DialogueNode(
            id="root",
            speaker=name,
            text="The archives are patient. Speak, or study.",
            emotion="neutral",
            choices=[
                DialogueChoice("Teach me about your magic.", "teach"),
                DialogueChoice("I seek admission.", "admit"),
                DialogueChoice("[Leave]", None),
            ],
        )

        return nodes


# --- No-arg alaluokat rekisterointia varten (get_npc_class kutsuu Class()) ---
class KeeperPure(SchoolKeeper):
    def __init__(self):
        super().__init__("keeper_pure")


class KeeperHoly(SchoolKeeper):
    def __init__(self):
        super().__init__("keeper_holy")


class KeeperDruid(SchoolKeeper):
    def __init__(self):
        super().__init__("keeper_druid")


class KeeperManip(SchoolKeeper):
    def __init__(self):
        super().__init__("keeper_manip")
