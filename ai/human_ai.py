# ai/human_ai.py
from ai.base_ai import BaseAI

class HumanAI(BaseAI):
    """ 
    Human AI: Placeholder. 
    Delegates all logic to BaseAI. 
    """
    def execute_ai(self, all_units, obstacles, manager=None):
        # Kutsuu suoraan isäluokan (BaseAI) metodia ilman omia lisäyksiä
        super().execute_ai(all_units, obstacles, manager)