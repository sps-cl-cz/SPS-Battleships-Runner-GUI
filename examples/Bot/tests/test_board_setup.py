import pytest
from board_setup import BoardSetup

# -----------------------------------------------------------------------------
# Helper function to create and place ships on a board
# -----------------------------------------------------------------------------

def create_board(rows, cols, ships_dict):
    """Helper function to create board setups dynamically and place ships."""
    board = BoardSetup(rows=rows, cols=cols, ships_dict=ships_dict)
    board.place_ships()  # Will fail if not implemented
    return board

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def small_board():
    """
    A 5x5 board with no ships placed.
    Useful for testing initial state, get_tile, etc.
    """
    return BoardSetup(rows=5, cols=5, ships_dict={})

@pytest.fixture
def empty_board():
    """
    A 10x10 board with an empty ships_dict; place_ships() does nothing
    but should not error out.
    """
    return create_board(10, 10, {})

@pytest.fixture
def one_ship_a():
    """
    A 10x10 board with a single ship of ID=1 (e.g. length=2).
    """
    return create_board(10, 10, {1: 1})

@pytest.fixture
def one_ship_b():
    """
    A 10x10 board with a single ship of ID=2 (e.g. length=3).
    """
    return create_board(10, 10, {2: 1})

@pytest.fixture
def two_ships_c():
    """
    A 10x10 board with two ships of ID=3 (e.g. length=4).
    """
    return create_board(10, 10, {3: 2})

@pytest.fixture
def two_different_ships():
    """
    A 10x10 board with 1 ship of ID=1 and 1 ship of ID=2.
    """
    return create_board(10, 10, {1: 1, 2: 1})

@pytest.fixture
def five_different_ships():
    """
    A 10x10 board with IDs 1..5 placed once each.
    """
    return create_board(10, 10, {1: 1, 2: 1, 3: 1, 4: 1, 5: 1})

@pytest.fixture
def many_ships():
    """
    A 10x10 board with multiple ships of IDs 1..5.
    """
    return create_board(10, 10, {1: 3, 2: 3, 3: 2, 4: 2, 5: 2})

@pytest.fixture
def all_seven_ships():
    """
    A 10x10 board with one of each ship ID from 1..7.
    This ensures every ship ID can be placed at least once.
    """
    return create_board(10, 10, {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1})

# -----------------------------------------------------------------------------
# Basic Tests
# -----------------------------------------------------------------------------

def test_board_initialization(small_board: BoardSetup):
    """
    Check that rows/cols are stored and ships_dict is correct.
    """
    assert small_board.rows == 5
    assert small_board.cols == 5
    assert small_board.ships_dict == {}

def test_get_board_structure(small_board: BoardSetup):
    """
    If no ships placed, get_board() should be a 5x5 of all zeros.
    """
    board = small_board.get_board()
    assert len(board) == 5
    assert len(board[0]) == 5
    assert all(cell == 0 for row in board for cell in row)

def test_get_tile_in_range(small_board: BoardSetup):
    """
    get_tile(x,y) should return 0 for an unplaced board in range.
    """
    assert small_board.get_tile(0, 0) == 0
    assert small_board.get_tile(4, 4) == 0

def test_get_tile_out_of_range(small_board: BoardSetup):
    """
    get_tile() with out-of-range coords should raise IndexError.
    """
    with pytest.raises(IndexError):
        small_board.get_tile(-1, 0)
    with pytest.raises(IndexError):
        small_board.get_tile(0, 5)

def test_place_ships_empty_board(empty_board: BoardSetup):
    """
    If ships_dict is empty, place_ships() does nothing but board remains all zeros.
    """
    board = empty_board.get_board()
    assert all(cell == 0 for row in board for cell in row)

def test_place_ships_one_ship(one_ship_a: BoardSetup):
    """
    With a single ship ID=1, we expect at least 2 cells with '1' on a 10x10 board.
    """
    board = one_ship_a.get_board()
    count_occupied = sum(cell != 0 for row in board for cell in row)
    assert count_occupied >= 2, "At least 2 cells should be occupied for ID=1"

def test_place_ships_all_seven(all_seven_ships: BoardSetup):
    """
    With one of each ID=1..7, we expect some non-zero cells for each ship ID.
    We won't test adjacency or correctness here (no edgecases).
    Just ensure the board isn't all zeros and that each ID appears at least once.
    """
    board = all_seven_ships.get_board()
    # Board shouldn't be all zeros
    assert any(cell != 0 for row in board for cell in row), "At least some ships should be placed"

    # Optionally check that each ID (1..7) appears at least once
    found_ids = set()
    for r in board:
        found_ids.update(r)
    found_ids.discard(0)
    # found_ids might contain duplicates, but we only care that each ID in [1..7] is present
    for ship_id in range(1, 8):
        assert ship_id in found_ids, f"Ship ID={ship_id} should appear on the board"

# -----------------------------------------------------------------------------
# Ship Detection Helpers
# -----------------------------------------------------------------------------

def find_ships_of_length(board: BoardSetup, length: int):
    """
    Finds ships of a given length in straight lines (horizontal/vertical).
    We must call board.get_tile(x, y) with x=col, y=row.
    """
    found = []
    for y in range(board.rows):
        for x in range(board.cols):
            # Horizontal check: from x..(x+length-1), same y
            if x + length <= board.cols:
                if all(board.get_tile(x + i, y) != 0 for i in range(length)):
                    found.append(((x, y), "H"))

            # Vertical check: from y..(y+length-1), same x
            if y + length <= board.rows:
                if all(board.get_tile(x, y + i) != 0 for i in range(length)):
                    found.append(((x, y), "V"))
    return found

def find_l_ships(board: BoardSetup):
    """
    Finds L-shaped ships (e.g., ID=5) in any of 8 possible rotations.
    Each offset is (dx, dy) where dx is column offset, dy is row offset.
    We'll keep it consistent with get_tile(x+dx, y+dy).
    """
    
    found = []
    L_SHAPE_OFFSETS = [
        [(0, 0), (1, 0), (2, 0), (2, 1)],   # Standard L
        [(0, 0), (0, 1), (0, 2), (-1, 2)],   # Rotated 90°
        [(0, 0), (0, 1), (1, 1), (2, 1)],   # Rotated 180°
        [(0, 0), (-1, 0), (-1, 1), (-1, 2)],   # Rotated 270°
        [(0, 0), (0, 1), (-1, 1), (-2, 1)],   # Mirrored L
        [(0, 0), (1, 0), (1, 1), (1, 2)],  # Mirrored 90°
        [(0, 0), (0, -1), (1, -1), (2, -1)],  # Mirrored 180°
        [(0, 0), (0, 1), (0, 2), (1, 2)],   # Mirrored 270°
    ]
    for y in range(board.rows):
        for x in range(board.cols):
            for shape in L_SHAPE_OFFSETS:
                try:
                    # check all squares in shape
                    if all(board.get_tile(x + dx, y + dy) != 0 for (dy, dx) in shape):
                        found.append(((x, y), shape))
                except IndexError:
                    continue
    return found

# -----------------------------------------------------------------------------
# Tests Using Detection Helpers
# -----------------------------------------------------------------------------

def test_find_ships_of_length(two_ships_c: BoardSetup):
    """
    ID=3 might represent a ship of length=4. We placed 2 of them.
    find_ships_of_length(...) should detect at least 2 line segments of length=4.
    """
    ships = find_ships_of_length(two_ships_c, 4)
    assert len(ships) >= 2, "Should detect at least 2 line segments of length 4"

def test_find_l_ships(five_different_ships: BoardSetup):
    """
    If ID=5 is an L shape, placing it once among the five.
    find_l_ships() should find at least one L shape.
    """
    ships = find_l_ships(five_different_ships)
    assert len(ships) > 0, "Should detect at least one L-shaped ship"

# -----------------------------------------------------------------------------
# reset_board and board_stats Tests
# -----------------------------------------------------------------------------

def test_reset_board(one_ship_a: BoardSetup):
    """
    After placing a ship, reset_board() should make everything 0 again.
    """
    one_ship_a.reset_board()
    board = one_ship_a.get_board()
    assert all(cell == 0 for row in board for cell in row), "Board should be all zeros after reset"

def test_board_stats_before_placement(small_board: BoardSetup):
    """
    board_stats() on a 5x5 with no ships placed => 25 empty, 0 occupied.
    """
    stats = small_board.board_stats()
    assert stats["empty_spaces"] == 25
    assert stats["occupied_spaces"] == 0

def test_board_stats_after_placement(one_ship_b: BoardSetup):
    """
    For ID=2 (length=3?), we expect at least 3 occupied cells on a 10x10.
    Check board_stats matches actual occupancy.
    """
    board = one_ship_b.get_board()
    total = 10 * 10
    occupied = sum(cell != 0 for row in board for cell in row)
    stats = one_ship_b.board_stats()

    assert stats["occupied_spaces"] == occupied, "occupied_spaces must match actual occupancy"
    assert stats["empty_spaces"] == total - occupied, "empty_spaces must match total minus occupied"
    assert occupied == 3, "We expect exactly 3 cells be occupied for a board with one length-3 ship"
