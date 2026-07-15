# quest_registry.py

# Importtaa questit tähän
from quests.hunt_rat_king import RatKingQuest
from quests.manure_quest import ManureQuest
from quests.timber_quest import TimberQuest
from quests.crate_quest import CrateQuest
from quests.found_arena_team import FoundArenaTeamQuest

# Rekisteröi ne tähän sanakirjaan (ID -> Luokka)
QUEST_DB = {
    "found_arena_team": FoundArenaTeamQuest(),
    "hunt_01": RatKingQuest(),
    "quest_manure_cleanup": ManureQuest(),
    "quest_first_swing": TimberQuest(),
    "quest_krads_crate": CrateQuest(),
}

def get_all_quest_definitions():
    """Palauttaa listan kaikista questeista QuestManagerille"""
    return list(QUEST_DB.values())

def get_quest_def(quest_id):
    """Hakee tietyn questin tiedot ID:llä"""
    return QUEST_DB.get(quest_id)