"""
strategy.py

This module contains the Strategy class responsible for:
 - Tracking the known state of the enemy board.
 - Deciding which (x, y) cell to attack next.
 - Registering the result of each attack (hit/miss, sunk).
 - Keeping track of remaining enemy ships in a ships_dict.
"""

class GameOver(Exception):
    """Custom exception for game over"""
    pass

class Strategy:
    def __init__(self, rows: int, cols: int, ships_dict: dict[int, int]):
        """
        Initializes the game strategy with enemy board dimensions and ship configuration.
        
        Parameters:
        rows (int): Number of rows in enemy board
        cols (int): Number of columns in enemy board
        ships_dict (dict): Dictionary mapping ship IDs to their quantities
        """
        # Store board dimensions
        self.rows = rows
        self.cols = cols
        
        # Initialize tracking variables
        self.ships_dict = ships_dict.copy()
        self.attacked = set()
        self.enemy_board = [['?' for _ in range(cols)] for _ in range(rows)]
        self.probability_map = [[1.0 for _ in range(cols)] for _ in range(rows)]
        
        # Define ship metadata including size and shape
        self.ship_metadata = {
            1: 2, 2: 3, 3: 4, 4: 4, 5: 4, 6: 4, 7: 6  # ID: size
        }
        
        # Copy of remaining ships for tracking purposes
        self.ships_remaining = ships_dict.copy()

        self.ship_shapes = {
            1: {"type": "I", "size": 2},   # I (2)
            2: {"type": "I", "size": 3},   # I (3)
            3: {"type": "I", "size": 4},   # I (4)
            4: {"type": "T", "size": 4},   # T (3+1)
            5: {"type": "L", "size": 3},   # L (3x2)
            6: {"type": "Z", "size": 4},   # Z (2x3)
            7: {"type": "TT", "size": 6}   # TT (4+2)
        }

    def get_next_attack(self) -> tuple[int, int]:
        """
        Determines the next attack position based on probability map.
        Prioritizes cells with the highest probability of containing a ship.
        Uses checkerboard pattern for tie-breaking.
        """
        max_prob = -1
        candidates = []
        
        # Find all cells with maximum probability
        for y in range(self.rows):
            for x in range(self.cols):
                if (x, y) not in self.attacked:
                    if self.probability_map[y][x] > max_prob:
                        max_prob = self.probability_map[y][x]
                        candidates = [(x, y)]
                    elif self.probability_map[y][x] == max_prob:
                        candidates.append((x, y))
        
        # Use checkerboard pattern for tie-breaking
        if len(candidates) > 1:
            candidates.sort(key=lambda pos: (pos[0] + pos[1]) % 2, reverse=True)
        
        return candidates[0] if candidates else self._fallback_attack()

    def register_attack(self, x: int, y: int, is_hit: bool, is_sunk: bool):
        """
        Updates game state based on attack result.
        
        Parameters:
        x (int): X coordinate of attack
        y (int): Y coordinate of attack
        is_hit (bool): True if attack hit a ship
        is_sunk (bool): True if attack sunk a ship
        """
        self.attacked.add((x, y))
        self.enemy_board[y][x] = 'H' if is_hit else 'M'
        
        if is_hit:
            self._update_probabilities_on_hit(x, y)
            if is_sunk:
                self._mark_sunk_ship_area(x, y)
                self._update_ship_count(x, y)

    def _update_probabilities_on_hit(self, x: int, y: int):
        directions = [(-1,0), (1,0), (0,-1), (0,1)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                if (nx, ny) not in self.attacked:
                    self.probability_map[ny][nx] *= 2.0

    def _mark_sunk_ship_area(self, x: int, y: int):
        visited = set()
        queue = [(x, y)]
        ship_cells = []
        
        while queue:
            cx, cy = queue.pop(0)
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            
            if 0 <= cx < self.cols and 0 <= cy < self.rows:
                if self.enemy_board[cy][cx] == 'H':
                    ship_cells.append((cx, cy))
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nx, ny = cx + dx, cy + dy
                        queue.append((nx, ny))
        
        if not ship_cells:
            return
        
        # Calculate boundaries for marking surrounding area
        min_x = max(0, min(cx for cx, cy in ship_cells) - 1)
        max_x = min(self.cols-1, max(cx for cx, cy in ship_cells) + 1)
        min_y = max(0, min(cy for cx, cy in ship_cells) - 1)
        max_y = min(self.rows-1, max(cy for cx, cy in ship_cells) + 1)
        
        # Mark surrounding area as impossible positions
        for y in range(min_y, max_y+1):
            for x in range(min_x, max_x+1):
                if (x, y) not in self.attacked:
                    self.probability_map[y][x] = 0.0

    def _fallback_attack(self):
        for y in range(self.rows):
            for x in range(self.cols):
                if (x, y) not in self.attacked:
                    return x, y
        raise RuntimeError("No remaining attack positions")

    def _true_all_ships_sunk(self) -> bool:
        """Checks the actual state through hit counts"""
        total_hits = sum(row.count('H') for row in self.enemy_board)
        required_hits = sum(
            spec['size'] * count 
            for ship_id, count in self.ships_dict.items() 
            for spec in [self.ship_metadata[ship_id]]
        )
        return total_hits >= required_hits

    def _update_ship_count(self, x: int, y: int):
        """Detects ship size and updates counts"""
        ship_size = self._detect_ship_size(x, y)
        for ship_id, size in self.ship_metadata.items():
            if size == ship_size and self.ships_remaining.get(ship_id, 0) > 0:
                self.ships_remaining[ship_id] -= 1
                break

    def _detect_ship_size(self, x: int, y: int) -> int:
        """Helper method for tests - detects ship size"""
        visited = set()
        queue = [(x, y)]
        size = 0
        
        while queue:
            cx, cy = queue.pop(0)
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            
            if self.enemy_board[cy][cx] == 'H':
                size += 1
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows:
                        queue.append((nx, ny))
        return size

    def detect_ship_direction(self, x: int, y: int) -> list:
        """Detects probable ship direction based on neighboring hits"""
        directions = []
        
        # Check horizontal direction
        left = any(self.enemy_board[y][x-i] == 'H' for i in range(1, x+1))
        right = any(self.enemy_board[y][x+i] == 'H' for i in range(1, self.cols-x))
        if left or right:
            directions.extend([(-1,0), (1,0)])
        
        # Check vertical direction
        up = any(self.enemy_board[y-i][x] == 'H' for i in range(1, y+1))
        down = any(self.enemy_board[y+i][x] == 'H' for i in range(1, self.rows-y))
        if up or down:
            directions.extend([(0,-1), (0,1)])
        
        return directions if directions else [(-1,0),(1,0),(0,-1),(0,1)]

    def get_enemy_board(self) -> list[list[str]]:
        """Required by tests - returns a copy of the game board"""
        return [row.copy() for row in self.enemy_board]

    def get_remaining_ships(self) -> dict[int, int]:
        """Required by tests - returns remaining ships"""
        return self.ships_remaining.copy()

    def all_ships_sunk(self) -> bool:
        """Required by tests - checks ship status"""
        return sum(self.ships_remaining.values()) == 0

    def analyze_ship_shape(self, x: int, y: int) -> tuple[int, str]:
        visited = set()
        queue = [(x, y)]
        min_x, max_x = x, x
        min_y, max_y = y, y
        cells = []
        
        while queue:
            cx, cy = queue.pop(0)
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            cells.append((cx, cy))
            
            min_x = min(min_x, cx)
            max_x = max(max_x, cx)
            min_y = min(min_y, cy)
            max_y = max(max_y, cy)
            
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if self.enemy_board[ny][nx] == 'H' and (nx, ny) not in visited:
                        queue.append((nx, ny))

        norm_cells = [(x - min_x, y - min_y) for (x, y) in cells]
        width = max_x - min_x + 1  
        height = max_y - min_y + 1
        size = len(norm_cells)

        if size == 6 and width >= 4 and height >= 2:
            middle_x = (width - 1) / 2
            if all((x, 0) in norm_cells for x in range(4)) and \
               (middle_x, 1) in norm_cells and (middle_x, 2) in norm_cells:
                return 6, "TT"

        if size == 4 and width == 3 and height == 2:
            if {(0,0), (1,0), (1,1), (2,1)}.issubset(norm_cells) or \
               {(0,1), (1,1), (1,0), (2,0)}.issubset(norm_cells):
                return 4, "Z"

        if size == 3 and (width == 3 and height == 1) or (height == 3 and width == 1):
            return 3, "I"
        elif size == 3 and (width == 2 and height == 2):
            return 3, "L"

        if size == 4:
            main_axis = 'x' if width > height else 'y'
            if main_axis == 'x':
                middle = width // 2
                if any((middle, y) in norm_cells for y in range(1, height)):
                    return 4, "T"
            else:
                middle = height // 2
                if any((x, middle) in norm_cells for x in range(1, width)):
                    return 4, "T"

        if width == 1 or height == 1:
            return size, "I"

        return size, "Unknown"
