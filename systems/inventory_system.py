# systems/item_db.py
import json
import os

class ItemDB:
    def __init__(self, path="data/items.json"):
        self.path = path
        self.items_by_id = {}

    def load(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"ItemDB missing: {self.path}")

        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.items_by_id = {it["id"]: it for it in data.get("items", [])}

    def get(self, item_id: str):
        return self.items_by_id.get(item_id)

    def is_gear(self, item_id: str) -> bool:
        it = self.get(item_id)
        if not it:
            return False
        return it.get("category") in ("weapon", "armor", "spell", "usable")
