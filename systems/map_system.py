import pygame
from tiles.floors import DungeonFloor, MudFloor
from tiles.walls import BrickWall

TILE_SIZE = 64

class TileMap:
    def __init__(self):
        self.floor_group = pygame.sprite.Group()
        self.wall_group = pygame.sprite.Group()
        self.all_tiles = pygame.sprite.Group()

    def generate_room(self, width_tiles, height_tiles, type="dungeon"):
        self.floor_group.empty()
        self.wall_group.empty()
        self.all_tiles.empty()

        for row in range(height_tiles):
            for col in range(width_tiles):
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                
                # REUNAT -> SEINÄT
                if row == 0 or row == height_tiles - 1 or col == 0 or col == width_tiles - 1:
                    BrickWall(x, y, [self.wall_group, self.all_tiles])
                else:
                    # KESKUSTA -> LATTIA
                    if type == "dungeon":
                        DungeonFloor(x, y, [self.floor_group, self.all_tiles])
                    elif type == "swamp":
                        MudFloor(x, y, [self.floor_group, self.all_tiles])

    def get_obstacles(self):
        obstacles = []
        for sprite in self.wall_group:
            obstacles.append(sprite.rect)
        return obstacles

    def update(self):
        self.all_tiles.update()

    def draw(self, screen):
        self.floor_group.draw(screen)
        self.wall_group.draw(screen)