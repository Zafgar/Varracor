# ai/goblin_ai.py
from ai.base_ai import BaseAI

class GoblinAI(BaseAI):
    """ 
    Goblin AI: Placeholder.
    Delegates all logic to BaseAI.
    (Future: Low HP targeting priority)
    """
    def execute_ai(self, all_units, obstacles, manager=None):
        super().execute_ai(all_units, obstacles, manager)