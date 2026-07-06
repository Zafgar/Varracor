from dataclasses import dataclass, field
from typing import List, Callable, Dict, Optional

@dataclass
class DialogueChoice:
    text: str
    next_node_id: Optional[str] = None  # None = keskustelu päättyy
    effects: List[str] = field(default_factory=list)
    condition: Optional[Callable[[dict], bool]] = None 

@dataclass
class DialogueNode:
    id: str
    text: str
    speaker: str
    emotion: str
    choices: List[DialogueChoice] = field(default_factory=list)
    on_enter_effects: List[str] = field(default_factory=list)

class BaseNPC:
    def __init__(self, npc_id: str):
        self.npc_id = npc_id

    def get_dialogue_root(self, context: dict) -> str:
        return "start"

    def get_nodes(self, context: dict) -> Dict[str, DialogueNode]:
        return {}
    
    def get_portrait_path(self, emotion: str) -> str:
        # Oletuspolku kuville
        return f"assets/portraits/{self.npc_id}/{emotion}.png"