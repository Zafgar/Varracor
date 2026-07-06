import heapq
import math

class NavigationGrid:
    def __init__(self, arena, tile_size=40):
        self.tile_size = tile_size
        # Lasketaan ruudukon koko areenan koon perusteella
        self.width = int(arena.width // tile_size) + 1
        self.height = int(arena.height // tile_size) + 1
        self.grid = [[0 for _ in range(self.height)] for _ in range(self.width)]
        self._build_grid(arena)

    def _build_grid(self, arena):
        """Merkitsee esteet ruudukkoon."""
        obstacles = getattr(arena, "obstacles", [])
        for obs in obstacles:
            # Tarkistetaan onko objekti este (seinä, talo, aita)
            # Prop-luokalla on is_structure=True tai type="wall"
            is_blocking = getattr(obs, "is_structure", False) or getattr(obs, "type", "") == "wall"
            
            # Poikkeus: Muta (type="mud") ei estä reitinhakua, se vain hidastaa
            if getattr(obs, "type", "") == "mud":
                is_blocking = False

            if not is_blocking:
                continue
            
            # Muunnetaan rect ruudukko-koordinaateiksi
            r = obs.rect
            start_x = max(0, int(r.left // self.tile_size))
            end_x = min(self.width, int(r.right // self.tile_size) + 1)
            start_y = max(0, int(r.top // self.tile_size))
            end_y = min(self.height, int(r.bottom // self.tile_size) + 1)

            for x in range(start_x, end_x):
                for y in range(start_y, end_y):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.grid[x][y] = 1 # 1 = Blocked

    def get_path(self, start_pos, end_pos):
        """A* Pathfinding: Palauttaa listan pisteitä (world coords) alusta loppuun."""
        start_node = (int(start_pos[0] // self.tile_size), int(start_pos[1] // self.tile_size))
        end_node = (int(end_pos[0] // self.tile_size), int(end_pos[1] // self.tile_size))

        # Tarkistetaan rajat
        if not self._is_valid(start_node) or not self._is_valid(end_node):
            return None
            
        # Jos loppupiste on seinän sisällä, etsi lähin vapaa ruutu
        if self.grid[end_node[0]][end_node[1]] == 1:
             end_node = self._find_nearest_free(end_node)
             if not end_node: return None

        # A* Algoritmi
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: self._heuristic(start_node, end_node)}
        
        visited = set()

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == end_node:
                return self._reconstruct_path(came_from, current)
            
            visited.add(current)

            for neighbor in self._get_neighbors(current):
                if neighbor in visited: continue

                tentative_g_score = g_score[current] + 1 # Oletetaan kustannukseksi 1
                
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, end_node)
                    
                    # Lisää open settiin jos ei jo siellä (yksinkertaistettu tarkistus)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None # Ei reittiä

    def _is_valid(self, node):
        x, y = node
        return 0 <= x < self.width and 0 <= y < self.height

    def _get_neighbors(self, node):
        x, y = node
        neighbors = []
        # 8 suuntaa (myös diagonaalit)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nx, ny = x + dx, y + dy
            if self._is_valid((nx, ny)) and self.grid[nx][ny] == 0:
                # Estä kulmien leikkaaminen jos vieressä on seinä
                if abs(dx) == 1 and abs(dy) == 1:
                    if self.grid[x + dx][y] == 1 or self.grid[x][y + dy] == 1:
                        continue
                neighbors.append((nx, ny))
        return neighbors

    def _heuristic(self, a, b):
        # Manhattan distance on nopea ja riittävä ruudukolle
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _reconstruct_path(self, came_from, current):
        total_path = [self._grid_to_world(current)]
        while current in came_from:
            current = came_from[current]
            total_path.append(self._grid_to_world(current))
        return total_path[::-1] # Käännä lista (alku -> loppu)

    def _grid_to_world(self, node):
        # Palauttaa ruudun keskipisteen
        return (node[0] * self.tile_size + self.tile_size // 2, 
                node[1] * self.tile_size + self.tile_size // 2)

    def _find_nearest_free(self, node):
        # BFS etsii lähimmän vapaan ruudun
        queue = [node]
        visited = set([node])
        while queue:
            curr = queue.pop(0)
            if self.grid[curr[0]][curr[1]] == 0:
                return curr
            
            # Tarkista naapurit (vain 4 suuntaa nopeuden vuoksi)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = curr[0] + dx, curr[1] + dy
                if self._is_valid((nx, ny)) and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
            
            if len(visited) > 50: return None # Luovuta jos ei löydy läheltä
        return None