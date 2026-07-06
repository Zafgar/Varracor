from .base_tile import MapObject

class WoodenCrate(MapObject):
    def __init__(self, x, y, groups):
        path = "assets/objects/crate_wood.png"
        super().__init__(x, y, path, groups)
        self.type = "obstacle"
        self.is_solid = True
        self.destructible = True
        self.hp = 20 # Hajoaa helposti
        
    def destroy(self, manager):
        print("Crate Smashed!")
        # Tähän voisi lisätä koodin: spawn_loot(self.rect.center)
        super().destroy(manager)