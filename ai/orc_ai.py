# ai/orc_ai.py
from ai.base_ai import BaseAI

class OrcAI(BaseAI):
    """ 
    Orc AI: Placeholder.
    Delegates all logic to BaseAI.
    (Future: Rage mechanics)
    """
    def execute_ai(self, all_units, obstacles, manager=None):
        super().execute_ai(all_units, obstacles, manager)