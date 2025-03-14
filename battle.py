#!/usr/bin/env python3
"""
battle.py

This is the master game runner. It supports these command-line arguments:
  -v               : Verbose output; prints every move.
  -c X             : Count of battles to simulate (default=100).
  -w X             : Board width (default=10).
  -h X             : Board height (default=10).
  -l A,B,C,D,E,F,G : Comma-separated ship counts for IDs 1..7.
                    If specified, turns off the random ship generation.
                    If not specified, a random ship configuration is generated
                    (until at least 30% of the playing field is filled).

The master runner initializes both players' boards & strategies (using their submissions)
and then runs the battle logic—using its own game state to determine hits, sunk ships, etc.—while
also informing the players' strategy modules of the results.
"""

import argparse
import sys
import random
import matplotlib.pyplot as plt
import time
import os

# Import student submissions
from player_1.board_setup.board_setup import BoardSetup as BS1
from player_1.strategy.strategy import Strategy as ST1
from player_2.board_setup.board_setup import BoardSetup as BS2
from player_2.strategy.strategy import Strategy as ST2

# --------------------------
# Helper functions
# --------------------------

def get_ship_instances(board: list[list[int]]) -> list[dict]:
    """
    Given a 2D board (list of lists of ints), identify each ship instance
    as a connected (orthogonally) component of nonzero cells.
    Returns a list of dictionaries, each with keys:
      - "ship_id": the ship type (int)
      - "coords" : a set of (x, y) coordinates belonging to this ship.
      - "hits"   : an initially empty set that will track attacked cells.
    """
    rows = len(board)
    cols = len(board[0]) if rows else 0
    visited = set()
    instances = []

    for y in range(rows):
        for x in range(cols):
            if board[y][x] != 0 and (x, y) not in visited:
                ship_id = board[y][x]
                stack = [(x, y)]
                component = set()
                while stack:
                    cx, cy = stack.pop()
                    if (cx, cy) in component:
                        continue
                    component.add((cx, cy))
                    visited.add((cx, cy))
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = cx+dx, cy+dy
                        if 0 <= nx < cols and 0 <= ny < rows:
                            if board[ny][nx] == ship_id and (nx, ny) not in component:
                                stack.append((nx, ny))
                instances.append({"ship_id": ship_id, "coords": component, "hits": set()})
    return instances

def process_attack(x: int, y: int, ship_instances: list[dict]) -> tuple[bool, bool]:
    """
    Given an attack coordinate (x,y) and a list of ship instances (each a dict with keys
    "coords" and "hits"), determine whether the attack is a hit, and whether it sinks
    one of the ships.
    Marks the cell as hit in the corresponding ship instance if found.
    Returns a tuple (hit, sunk).
    """
    for ship in ship_instances:
        if (x, y) in ship["coords"]:
            ship["hits"].add((x, y))
            if ship["hits"] == ship["coords"]:
                return True, True
            else:
                return True, False
    return False, False

def generate_random_ships(width: int, height: int) -> list[int]:
    """
    Generate a random ship counts list (for ship IDs 1..7) such that the total number
    of ship tiles is at least 30% of the board area.
    
    Predefined tile counts:
      ID1: 2, ID2: 3, ID3: 4, ID4: 4, ID5: 4, ID6: 4, ID7: 6.
    """
    target = int(width * height * 0.3)
    tile_counts = {1: 2, 2: 3, 3: 4, 4: 4, 5: 4, 6: 4, 7: 6}
    ship_counts = {i: 0 for i in range(1,8)}
    total_tiles = 0
    while total_tiles < target:
        ship_type = random.randint(1,7)
        ship_counts[ship_type] += 1
        total_tiles += tile_counts[ship_type]
    return [ship_counts[i] for i in range(1,8)]

def draw_board(board, title="", filename=None):
    """Vykreslí herní plochu s loděmi"""
    if not hasattr(draw_board, 'figures'):
        # Initialize figures dictionary if it doesn't exist
        draw_board.figures = {}
        plt.ion()  # Turn on interactive mode
    
    if title not in draw_board.figures:
        # Create new figure if it doesn't exist
        fig, ax = plt.subplots(figsize=(8, 8))
        fig.canvas.manager.set_window_title(title)  # Set unique window title
        draw_board.figures[title] = (fig, ax)
        plt.show(block=False)
        plt.pause(0.1)  # Allow time for window to appear
    else:
        # Use existing figure
        fig, ax = draw_board.figures[title]
    
    # Clear previous content
    ax.clear()
    
    # Create a custom colormap
    from matplotlib.colors import ListedColormap
    colors = [
        'white',        # 0: Empty
        'blue',         # 1: Ship ID 1
        'blue',         # 2: Ship ID 2
        'blue',         # 3: Ship ID 3
        'blue',         # 4: Ship ID 4
        'blue',         # 5: Ship ID 5
        'blue',         # 6: Ship ID 6
        'blue',         # 7: Ship ID 7
        'lime',         # 8: Hit
        'darkgreen',    # 9: Hit and Sunk
        'red'           # 10: Miss
    ]
    cmap = ListedColormap(colors)
    
    # Create a copy of the board for visualization
    visual_board = [row.copy() for row in board]
    
    # Mark hits (8), sunk ships (9), and misses (10)
    for y in range(len(visual_board)):
        for x in range(len(visual_board[y])):
            if visual_board[y][x] == 8:  # Hit
                visual_board[y][x] = 8
            elif visual_board[y][x] == 9:  # Miss
                visual_board[y][x] = 10
            # Sunk ships are already marked as 9 in the board logic
    
    # Draw new content
    im = ax.imshow(visual_board, cmap=cmap, vmin=0, vmax=10)
    ax.set_title(title)
    ax.grid(color='black', linestyle='--', linewidth=0.5)
    
    # Update the figure
    fig.canvas.draw()
    fig.canvas.flush_events()
    
    # Save to file if requested
    if filename:
        plt.savefig(filename)

def log_move(log_file, move_num, player, x, y, hit, sunk):
    """Zapíše informace o tahu do log souboru"""
    with open(log_file, 'a') as f:
        f.write(f"Move {move_num}: Player {player} attacks ({x},{y}) -> {'Hit' if hit else 'Miss'}{' and Sunk' if sunk else ''}\n")

# --------------------------
# Battle simulation function
# --------------------------

def simulate_battle(verbose: bool, width: int, height: int, ship_counts: list[int], starting_player: int) -> tuple[int, int]:
    """
    Simulate one battle between two players.
    
    Parameters:
      verbose       : If True, print detailed moves.
      width, height : Board dimensions.
      ship_counts   : List of 7 integers for ship counts for IDs 1..7.
      starting_player: 1 or 2; which player starts the battle.
    
    Returns:
      (winner, moves) where:
        - winner is 1, 2, or 0 for a draw.
        - moves is the number of moves played.
    
    If moves exceed width*height*100, the battle is considered a draw.
    """
    max_moves = width * height * 100
    
    # Build ships_dict from ship_counts list: keys 1..7.
    ships_dict = {i+1: ship_counts[i] for i in range(7)}
    
    # Initialize Player 1:
    p1_bs = BS1(height, width, ships_dict)
    p1_bs.place_ships()
    p1_board = p1_bs.get_board()
    p1_strat = ST1(height, width, ships_dict)
    p1_instances = get_ship_instances(p1_board)
    
    # Initialize Player 2:
    p2_bs = BS2(height, width, ships_dict)
    p2_bs.place_ships()
    p2_board = p2_bs.get_board()
    p2_strat = ST2(height, width, ships_dict)
    p2_instances = get_ship_instances(p2_board)
    
    moves = 0
    current_player = starting_player

    # Create logs directory if it doesn't exist
    log_dir = f"./logs/battle_log_{int(time.time())}"
    os.makedirs(log_dir, exist_ok=True)

    player1_moves_log = log_dir + "/Player1/"
    player2_moves_log = log_dir + "/Player2/"
    os.makedirs(player1_moves_log, exist_ok=True)
    os.makedirs(player2_moves_log, exist_ok=True)


    # Initialize logging
    log_file_path = os.path.join(log_dir, f"battle_log.txt")
    with open(log_file_path, 'w') as f:
        f.write(f"New battle started: {width}x{height}, ships: {ship_counts}\n P1_board:{p1_instances} \n P2_board:{p2_instances}")

    # Show initial boards
    draw_board(p1_board, "Player 1 Board", os.path.join(player1_moves_log, "player1_initial.png"))
    draw_board(p2_board, "Player 2 Board", os.path.join(player2_moves_log, "player2_initial.png"))
    plt.pause(0.1)  # Allow time for initial windows to appear

    while moves < max_moves:
        moves += 1
        if current_player == 1:
            x, y = p1_strat.get_next_attack()
            hit, sunk = process_attack(x, y, p2_instances)
            p1_strat.register_attack(x, y, is_hit=hit, is_sunk=sunk)
            log_move(log_file_path, moves, 1, x, y, hit, sunk)
            if verbose:
                print(f"Move {moves}: Player 1 attacks ({x},{y}) -> {'Hit' if hit else 'Miss'}{' and Sunk' if sunk else ''}")
            # Update visualization
            p2_board[y][x] = 8 if hit else 9  # Mark hit/miss
            draw_board(p2_board, "Player 2 Board", os.path.join(player2_moves_log, f"player2_move_{moves}.png"))
            plt.pause(0.01)  # Allow time for update
            if all(ship["hits"] == ship["coords"] for ship in p2_instances):
                if verbose:
                    print(f"Player 1 wins after {moves} moves!")
                return 1, moves
            current_player = 2
        else:
            x, y = p2_strat.get_next_attack()
            hit, sunk = process_attack(x, y, p1_instances)
            p2_strat.register_attack(x, y, is_hit=hit, is_sunk=sunk)
            log_move(log_file_path, moves, 2, x, y, hit, sunk)
            if verbose:
                print(f"Move {moves}: Player 2 attacks ({x},{y}) -> {'Hit' if hit else 'Miss'}{' and Sunk' if sunk else ''}")
            # Update visualization
            p1_board[y][x] = 8 if hit else 9  # Mark hit/miss
            draw_board(p1_board, "Player 1 Board", os.path.join(player1_moves_log, f"player1_move_{moves}.png"))
            plt.pause(0.01)  # Allow time for update
            if all(ship["hits"] == ship["coords"] for ship in p1_instances):
                if verbose:
                    print(f"Player 2 wins after {moves} moves!")
                return 2, moves
            current_player = 1

    # If we exceeded max_moves, consider it a draw.
    if verbose:
        print(f"Battle ended in a draw after {moves} moves.")
    return 0, moves

def _print_ship_positions(ship_instances: list[dict]):
    """Print positions of all ships"""
    for ship in ship_instances:
        print(f"Ship ID {ship['ship_id']}: {sorted(ship['coords'])}")

# --------------------------
# Main function
# --------------------------

def main():
    plt.close('all')  # Close any existing figures
    
    parser = argparse.ArgumentParser(description="Battle simulation between two players.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--count", type=int, default=1, help="Number of battles (default=1 for gui)")
    parser.add_argument("-W", "--width", type=int, default=10, help="Board width (default=10)")
    parser.add_argument("-H", "--height", type=int, default=10, help="Board height (default=10)")
    parser.add_argument("-l", "--list", type=str, default=None,
                        help="Comma-separated ship counts for IDs 1..7 (if specified, turns off random ship generation)")
    args = parser.parse_args()

    verbose = args.verbose
    battle_count = args.count
    width = args.width
    height = args.height

    if args.list is None:
        ship_counts = generate_random_ships(width, height)
        if verbose:
            print(f"Random ship counts generated: {ship_counts}")
    else:
        try:
            ship_counts = list(map(int, args.list.split(',')))
            if len(ship_counts) != 7:
                raise ValueError
        except ValueError:
            print("Invalid ship counts list. Must be 7 comma-separated integers.")
            sys.exit(1)

    wins = {1: 0, 2: 0, 0: 0}  # 0 indicates a draw.
    total_moves = 0

    for battle_num in range(1, battle_count+1):
        # Alternate starting player: if battle number is odd, Player 1 starts; if even, Player 2 starts.
        starting_player = 1 if (battle_num % 2 == 1) else 2
        if verbose:
            print(f"\n=== Battle {battle_num} (Player {starting_player} starts) ===")
        winner, moves = simulate_battle(verbose, width, height, ship_counts, starting_player)
        wins[winner] += 1
        total_moves += moves
        if verbose:
            outcome = "Draw" if winner == 0 else f"Winner: Player {winner}"
            print(f"Battle {battle_num} finished: {outcome} in {moves} moves.")

    avg_moves = total_moves / battle_count if battle_count else 0
    print("\n=== Overall Battle Results ===")
    print(f"Total battles: {battle_count}")
    print(f"Player 1 wins: {wins[1]}")
    print(f"Player 2 wins: {wins[2]}")
    print(f"Draws: {wins[0]}")
    print(f"Average game length: {avg_moves:.2f} moves")

if __name__ == "__main__":
    main()
