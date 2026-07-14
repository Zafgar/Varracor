class QuestDefinition:
    def __init__(self, id, title, description, rep_req=0, boss_id=None, rewards=None):
        self.id = id
        self.title = title
        self.description = description
        self.rep_req = rep_req
        self.boss_id = boss_id
        self.rewards = rewards or {}

    @property
    def reward_text(self):
        parts = []
        if "gold" in self.rewards:
            from ui_kit import format_money
            parts.append(format_money(self.rewards["gold"]))
        return ", ".join(parts)

    def get_dialogue_for_npc(self, npc_id, status):
        return None