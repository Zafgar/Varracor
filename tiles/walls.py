from .base_tile import MapObject

class BrickWall(MapObject):
    def __init__(self, x, y, groups):
        # Varmista että tämä tiedostonimi vastaa assets-kansiossa olevaa!
        path = "assets/tiles/walls/brick_wall.png"
        super().__init__(x, y, path, groups)
        self.type = "wall"
        self.is_solid = True