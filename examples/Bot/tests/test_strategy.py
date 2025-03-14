import pytest
from strategy import Strategy

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def small_strategy():
    """
    A small 5x5 Strategy with 2 ship types:
      - ID=1 => length=2 (count=1)
      - ID=2 => length=3 (count=1)
    Total ships = 2.
    """
    return Strategy(rows=5, cols=5, ships_dict={1: 1, 2: 1})

@pytest.fixture
def bigger_strategy():
    """
    An 8x8 Strategy with more ships:
      - ID=1 => 2
      - ID=2 => 1
      - ID=3 => 1
    """
    return Strategy(rows=8, cols=8, ships_dict={1: 2, 2: 1, 3: 1})

# -----------------------------------------------------------------------------
# Basic Initialization Tests
# -----------------------------------------------------------------------------

def test_init_small_strategy(small_strategy: Strategy):
    """
    Ensure rows, cols, ships_dict are stored, and the enemy board is '?'.
    """
    assert small_strategy.rows == 5
    assert small_strategy.cols == 5
    assert small_strategy.ships_dict == {1: 1, 2: 1}

    board = small_strategy.get_enemy_board()
    assert len(board) == 5
    assert len(board[0]) == 5
    for row in board:
        for cell in row:
            assert cell == '?', "All cells should be '?' at start"

def test_init_bigger_strategy(bigger_strategy: Strategy):
    """
    Similar check for an 8x8 Strategy.
    """
    assert bigger_strategy.rows == 8
    assert bigger_strategy.cols == 8
    assert bigger_strategy.ships_dict == {1: 2, 2: 1, 3: 1}

    board = bigger_strategy.get_enemy_board()
    assert len(board) == 8
    assert len(board[0]) == 8
    for row in board:
        for cell in row:
            assert cell == '?'

# -----------------------------------------------------------------------------
# get_next_attack() Tests
# -----------------------------------------------------------------------------

def test_get_next_attack_in_range(small_strategy: Strategy):
    """
    get_next_attack() should return (x, y) within board boundaries.
    We'll call it multiple times, but we won't require variety.
    """
    for _ in range(5):
        x, y = small_strategy.get_next_attack()
        assert 0 <= x < small_strategy.cols, f"Returned x={x} out of range"
        assert 0 <= y < small_strategy.rows, f"Returned y={y} out of range"

# -----------------------------------------------------------------------------
# register_attack() - Hits and Misses (no sunk)
# -----------------------------------------------------------------------------

def test_register_attack_hit_not_sunk(small_strategy: Strategy):
    """
    If is_hit=True, is_sunk=False => Mark 'H' on the board.
    ships_dict should remain unchanged.
    """
    x, y = 2, 2
    small_strategy.register_attack(x, y, is_hit=True, is_sunk=False)
    board = small_strategy.get_enemy_board()
    assert board[y][x] == 'H'
    assert small_strategy.ships_dict == {1: 1, 2: 1}, "No changes when not sunk"

def test_register_attack_miss(bigger_strategy: Strategy):
    """
    If is_hit=False => Mark 'M'. ships_dict remains unchanged.
    """
    x, y = 3, 3
    bigger_strategy.register_attack(x, y, is_hit=False, is_sunk=False)
    board = bigger_strategy.get_enemy_board()
    assert board[y][x] == 'M'
    assert bigger_strategy.ships_dict == {1: 2, 2: 1, 3: 1}

# -----------------------------------------------------------------------------
# get_enemy_board() Test
# -----------------------------------------------------------------------------

def test_get_enemy_board_updates(small_strategy: Strategy):
    """
    Multiple attacks:
      1) Miss at (0,0) => 'M'
      2) Hit at (1,0) => 'H'
    The board should reflect these, ignoring is_sunk (False).
    """
    small_strategy.register_attack(0, 0, is_hit=False, is_sunk=False)
    small_strategy.register_attack(1, 0, is_hit=True, is_sunk=False)

    board = small_strategy.get_enemy_board()
    assert board[0][0] == 'M'
    assert board[0][1] == 'H'

# -----------------------------------------------------------------------------
# get_remaining_ships() and all_ships_sunk() Tests (No sinking yet)
# -----------------------------------------------------------------------------

def test_get_remaining_ships_unchanged_without_sunk(small_strategy: Strategy):
    """
    If no ships are sunk, get_remaining_ships() should remain the same as initial.
    """
    assert small_strategy.get_remaining_ships() == {1: 1, 2: 1}
    # Register a few hits or misses that are not sunk
    small_strategy.register_attack(0, 0, is_hit=True, is_sunk=False)
    small_strategy.register_attack(1, 1, is_hit=False, is_sunk=False)
    # Should be unchanged
    assert small_strategy.get_remaining_ships() == {1: 1, 2: 1}

def test_all_ships_sunk_unchanged(small_strategy: Strategy):
    """
    If we never sink a ship, all_ships_sunk() should remain False.
    """
    assert small_strategy.all_ships_sunk() is False
    small_strategy.register_attack(0, 0, is_hit=True, is_sunk=False)
    small_strategy.register_attack(1, 1, is_hit=False, is_sunk=False)
    assert small_strategy.all_ships_sunk() is False

# -----------------------------------------------------------------------------
# Tests with Sinking Logic
# -----------------------------------------------------------------------------

def test_sink_first_ship_small_strategy(small_strategy: Strategy):
    """
    1) Start with total ships = 2.
    2) (0,1) => HIT, not sunk => ships still = 2
    3) (1,1) => HIT, sunk => ships => 1
    We check only the total count, not which ID was decremented.
    """
    initial_sum = sum(small_strategy.get_remaining_ships().values())
    assert initial_sum == 2, "Expected 2 ships at start"

    # First hit, not sunk
    small_strategy.register_attack(0, 1, is_hit=True, is_sunk=False)
    mid_sum = sum(small_strategy.get_remaining_ships().values())
    assert mid_sum == 2, "No change if is_sunk=False"

    # Second hit, sunk
    small_strategy.register_attack(1, 1, is_hit=True, is_sunk=True)
    final_sum = sum(small_strategy.get_remaining_ships().values())
    assert final_sum == 1, "One ship should remain after a sink"

def test_sink_two_ships_small_strategy(small_strategy: Strategy):
    """
    1) Start with total ships = 2.
    2) Row=1 => (0,1) HIT, (1,1) SINK => sum=1
    3) Row=3 => (0,3) HIT, not sunk => still sum=1
                (1,3) HIT, not sunk => still sum=1
                (2,3) HIT, sunk => sum=0 => all_ships_sunk()=True
    """
    # Initial
    assert sum(small_strategy.get_remaining_ships().values()) == 2

    # Sink first ship
    small_strategy.register_attack(0, 1, is_hit=True, is_sunk=False)
    small_strategy.register_attack(1, 1, is_hit=True, is_sunk=True)
    assert sum(small_strategy.get_remaining_ships().values()) == 1, "After first sink, 1 ship remains"
    assert not small_strategy.all_ships_sunk()

    # Attempt to sink the second ship
    small_strategy.register_attack(0, 3, is_hit=True, is_sunk=False)
    assert sum(small_strategy.get_remaining_ships().values()) == 1
    small_strategy.register_attack(1, 3, is_hit=True, is_sunk=False)
    assert sum(small_strategy.get_remaining_ships().values()) == 1
    small_strategy.register_attack(2, 3, is_hit=True, is_sunk=True)
    assert sum(small_strategy.get_remaining_ships().values()) == 0, "No ships left"
    assert small_strategy.all_ships_sunk(), "All ships should be sunk now"
