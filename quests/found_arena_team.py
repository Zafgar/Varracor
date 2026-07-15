from .base_quest import QuestDefinition


class FoundArenaTeamQuest(QuestDefinition):
    """Kylään saavuttaessa: perusta virallinen areenatiimi. Tämä on
    yhtenäisen questijournalin main-quest, joka korvaa erillisen oikean
    yläkulman "FOUND AN ARENA TEAM" -paneelin. Tavoitteiden valmius
    lasketaan elävästi opening_progressista (velka/maine/voitot/maksu/
    rekisteröinti)."""

    def __init__(self):
        super().__init__(
            id="found_arena_team",
            title="Found an Arena Team",
            description="Muckford runs on the arena. Clear your slate, make "
                        "a name, win in the yard and save the seal fee, then "
                        "have Bram Mudhand enter your team in the Ledger.",
            rep_req=0,
            boss_id=None,
            rewards={},
            category="main",
            giver="Bram Mudhand",
            objectives=[
                "Clear your debt to Marda Shant",
                "Earn a name in Muckford (reputation 8)",
                "Win 3 creature bouts in the yard",
                "Save the 30 SP registration fee",
                "Register your team with Bram at the Shanty Yard gate",
            ],
        )
