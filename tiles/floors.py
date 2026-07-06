from .base_tile import MapObject
import random

class DungeonFloor(MapObject):
    def __init__(self, x, y, groups):
        # Jos sinulla on variaatioita (01, 02), voit arpoa ne tässä
        path = "assets/tiles/floors/dungeon_floor.png" 
        super().__init__(x, y, path, groups)
        self.type = "floor"
        self.is_solid = False

class MudFloor(MapObject):
    def __init__(self, x, y, groups):
        path = "assets/tiles/floors/mud.png"
        super().__init__(x, y, path, groups)
        self.type = "mud"
        self.is_solid = False