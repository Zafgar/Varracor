class QuestDefinition:
    def __init__(self, id, title, description, rep_req=0, boss_id=None,
                 rewards=None, category="side", objectives=None,
                 giver=None):
        self.id = id
        self.title = title
        self.description = description
        self.rep_req = rep_req
        self.boss_id = boss_id
        self.rewards = rewards or {}
        # Questijournalia varten (pelitesti 27): "main" tai "side",
        # vaiheittaiset tavoitteet ja tehtävänantajan nimi
        self.category = category
        self.objectives = list(objectives or [])
        self.giver = giver

    @property
    def reward_text(self):
        parts = []
        if "gold" in self.rewards:
            from ui_kit import format_money
            parts.append(format_money(self.rewards["gold"]))
        return ", ".join(parts)

    def get_dialogue_for_npc(self, npc_id, status):
        return None