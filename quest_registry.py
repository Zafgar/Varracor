# quest_registry.py

# Importtaa questit tähän
from quests.hunt_rat_king import RatKingQuest
from quests.manure_quest import ManureQuest
# from quests.hunt_skeleton import SkeletonQuest  <-- Esimerkki tulevasta

# Rekisteröi ne tähän sanakirjaan (ID -> Luokka)
QUEST_DB = {
    "hunt_01": RatKingQuest(),
    "quest_manure_cleanup": ManureQuest()
}

def get_all_quest_definitions():
    """Palauttaa listan kaikista questeista QuestManagerille"""
    return list(QUEST_DB.values())

def get_quest_def(quest_id):
    """Hakee tietyn questin tiedot ID:llä"""
    return QUEST_DB.get(quest_id)