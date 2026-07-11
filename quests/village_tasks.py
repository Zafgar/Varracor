# quests/village_tasks.py
"""
Kylän pikkutehtävät (side-tasks) — datavetoinen kehys.

Jokainen tehtävä on VillageTask, jonka vaiheita (stages) ajetaan
järjestyksessä. Uuden tehtävän lisääminen = uusi merkintä VILLAGE_TASKS-
listaan; koodia ei tarvitse muuttaa.

Tehtävätyypit (stage["kind"]):
  - "talk":    keskustele (näyttää tekstin, valinnat voivat haarauttaa)
  - "collect": kerää N kpl materiaalia (tarkistetaan inventaariosta)
  - "deliver": vie materiaalia kohteeseen (kuluttaa inventaariosta)
  - "reach":   mene paikkaan (giver hoitaa lippuna)

Palkinnot (task["rewards"]):
  gold, reputation, xp, item (luokan nimi), fighter (unit spec),
  material {name: count}.
"""


class VillageTask:
    def __init__(self, data):
        self.id = data["id"]
        self.title = data["title"]
        self.giver = data["giver"]
        self.summary = data.get("summary", "")
        self.stages = data["stages"]
        self.rewards = data.get("rewards", {})
        self.rep_req = data.get("rep_req", 0)
        # Miten kylä muistaa tämän urotyön (dialogeissa myöhemmin)
        self.deed_text = data.get("deed_text", "")
        # Runtime
        self.status = "available"   # available, active, ready_turnin, done
        self.stage_index = 0

    @property
    def current_stage(self):
        if 0 <= self.stage_index < len(self.stages):
            return self.stages[self.stage_index]
        return None

    def advance(self):
        self.stage_index += 1
        if self.stage_index >= len(self.stages):
            self.status = "ready_turnin"

    def to_dict(self):
        return {"status": self.status, "stage_index": self.stage_index}

    def from_dict(self, d):
        self.status = d.get("status", "available")
        self.stage_index = int(d.get("stage_index", 0))


# =========================================================
# TEHTÄVÄDATA (helppo laajentaa: lisää dict tähän)
# =========================================================
VILLAGE_TASKS = [
    {
        "id": "grain_haul",
        "title": "Grain for the Mill",
        "giver": "Farmer Gus",
        "summary": "Carry 3 sacks of grain from the farm to the market stall.",
        "deed_text": "hauled the mill's grain when Gus's back gave out",
        "rep_req": 0,
        "stages": [
            {"kind": "talk",
             "text": "The mill's out of grain and my back's out of commission. "
                     "Haul 3 sacks to the market stall and there's coin in it."},
            {"kind": "collect", "item": "Grain Sack", "count": 3,
             "hint": "Grab grain sacks from the barn."},
            {"kind": "deliver", "item": "Grain Sack", "count": 3, "to": "market",
             "hint": "Drop the sacks at the market stall."},
        ],
        "rewards": {"gold": 25, "reputation": 3, "xp": 10},
    },
    {
        "id": "forest_herbs",
        "title": "Hospice Herbs",
        "giver": "Sister-Medic Rhea Ashford",
        "summary": "Gather 5 Bogwort from the forest for the hospice.",
        "deed_text": "gathered healing herbs for the hospice",
        "rep_req": 0,
        "stages": [
            {"kind": "talk",
             "text": "The wounded keep coming and my herb stores are dry. "
                     "Bring me 5 Bogwort from the forest edge - it stops bleeding."},
            {"kind": "collect", "item": "Bogwort", "count": 5,
             "hint": "Bogwort grows in the forest to the east."},
        ],
        "rewards": {"gold": 20, "reputation": 5, "xp": 8,
                    "material": {"Weak Health Potion Recipe": 1}},
    },
    {
        "id": "lost_girl",
        "title": "The Lost Girl",
        "giver": "Marda Shant",
        "summary": "A tavern regular's daughter wandered toward the forest road.",
        "deed_text": "found the lost girl on the forest road",
        "rep_req": 5,
        "stages": [
            {"kind": "talk",
             "text": "One of my regulars is beside herself - her girl ran off "
                     "toward the forest road. Rats about lately. Find the child."},
            {"kind": "reach", "target": "forest_road",
             "hint": "Search the forest road."},
        ],
        # Valinnalla varustettu lopetus: viet lapsen kotiin tai... et
        "rewards": {"gold": 40, "reputation": 12, "xp": 20,
                    "fighter": {"race": "Human", "quality": "Common",
                                "name": "Wren"}},
    },
    {
        "id": "marsh_smith",
        "title": "The Marsh Smith",
        "giver": "Notice Board",
        "summary": "A Frogfolk smith is stranded in the swamp - bring back "
                   "her lost hammer-head (Void Iron) and she'll join you.",
        "deed_text": "brought the marsh smith Brekka into the fold",
        "rep_req": 25,
        "stages": [
            {"kind": "talk",
             "text": "Posted: Frogfolk smith seeks her stolen hammer-head. "
                     "Reward: her services. She forges AND fights."},
            {"kind": "collect", "item": "Void Iron", "count": 2,
             "hint": "Void Iron is mined on the swamp road."},
        ],
        "rewards": {"gold": 0, "reputation": 15, "xp": 25,
                    "fighter": {"race": "Frogfolk", "name": "Brekka"}},
    },
    {
        "id": "hamo_dispute",
        "title": "Broker's Quarrel",
        "giver": "Hamo",
        "summary": "Two goblin brokers are feuding over a rat-tail contract.",
        "deed_text": "settled the brokers' feud without bloodshed",
        "rep_req": 10,
        "stages": [
            {"kind": "talk",
             "text": "Psst. Me and Griznak both claim the same rat-tail contract. "
                     "It's getting... stabby. Talk him down and I'll cut you in."},
            {"kind": "talk",
             "text": "You smoothed it over? Heh. Griznak owes me now. "
                     "Here - a blade I 'found'. Don't ask."},
        ],
        "rewards": {"gold": 30, "reputation": 8, "xp": 15,
                    "item": "ScrapDagger"},
    },
]


def get_all_village_tasks():
    return [VillageTask(d) for d in VILLAGE_TASKS]
