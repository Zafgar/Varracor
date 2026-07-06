# ai/elf_ai.py
from ai.base_ai import BaseAI

class ElfAI(BaseAI):
    """ 
    Elf AI: Placeholder.
    Delegates all logic to BaseAI. 
    (Future: Power shots and kiting)
    """
    def execute_ai(self, all_units, obstacles, manager=None):
        super().execute_ai(all_units, obstacles, manager)