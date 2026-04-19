import os
import sys
import time
from typing import Any, List, Dict, Optional, Tuple
import shutil


NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8


RESET = "\033[0m"
WALL_CHAR = '██'
EMPTY_CHAR = '  '


def color(code: int) -> str:
    return f"\033[38;5;{code}m"


DEFAULT_COLORS: Dict[str, str] = {
    "wall":    color(28),
    "floor":   RESET,
    "entry":   color(226),
    "exit":    color(196),
    "path":    color(21),
    "visited": color(39),
    "pattern": color(27),
}


def enforce_borders(grid: List[List[int]]) -> List[List[int]]:

    H: int = len(grid)
    W: int = len(grid[0])

    for c in range(W):
        grid[0][c] |= NORTH
        grid[H - 1][c] |= SOUTH

    for r in range(H):
        grid[r][0] |= WEST
        grid[r][W - 1] |= EAST

    return grid


def cell_to_terminal(row: int, col: int) -> Tuple[int, int]:
    """computes the terminal coordinates of a cell's interior"""
    terminal_row: int = row * 2 + 2
    terminal_col: int = col * 4 + 3
    return (terminal_row, terminal_col)


def build_buffer(
    f_grid: List[List[int]],
    height: int,
    width: int,
    entry: Tuple[int, int],
    f_exit: Tuple[int, int],
    cell_states: Dict[Tuple[int, int], str],
    colors: Dict[str, str],
    path_cells: Optional[List[Tuple[int, int]]] = None,
) -> List[List[str]]:
    """builds the 2D character buffer"""

    buf_h = height*2 + 1
    buf_w = width*2 + 1

    wall_char: str = colors["wall"] + WALL_CHAR + RESET
    buf: List[List[str]] = [
        [wall_char] * buf_w for _ in range(buf_h)
    ]

    for r in range(height):
        for c in range(width):
            cell_val = f_grid[r][c]
            if not (cell_val & NORTH):
                buf[r * 2][c * 2 + 1] = EMPTY_CHAR
            if not (cell_val & WEST):
                buf[r * 2 + 1][c * 2] = EMPTY_CHAR
            if (r, c) == entry:
                interior: str = colors["entry"] + WALL_CHAR + RESET
            elif (r, c) == f_exit:
                interior = colors["exit"] + WALL_CHAR + RESET
            else:
                state: str = cell_states.get((r, c), "floor")
                char = EMPTY_CHAR if state == "floor" else WALL_CHAR
                interior = colors.get(state, RESET) + char + RESET

            buf[r * 2 + 1][c * 2 + 1] = interior

    for r in range(height):
        if not (f_grid[r][width - 1] & EAST):
            buf[r * 2 + 1][buf_w - 1] = EMPTY_CHAR
    for c in range(width):
        if not (f_grid[height - 1][c] & SOUTH):
            buf[buf_h - 1][c * 2 + 1] = EMPTY_CHAR

    pattern_char = colors["pattern"] + WALL_CHAR + RESET
    pattern_cells = {
        (r, c)
        for (r, c), state in cell_states.items()
        if state == "pattern" and 0 <= r < height and 0 <= c < width
    }
    for r, c in pattern_cells:
        buf[r * 2 + 1][c * 2 + 1] = pattern_char
        if (r, c + 1) in pattern_cells:
            buf[r * 2 + 1][c * 2 + 2] = pattern_char
        if (r + 1, c) in pattern_cells:
            buf[r * 2 + 2][c * 2 + 1] = pattern_char

    if path_cells:
        path_char = colors["path"] + WALL_CHAR + RESET
        for (r0, c0), (r1, c1) in zip(path_cells, path_cells[1:]):
            if r0 == r1 and abs(c1 - c0) == 1:
                buf[r0 * 2 + 1][min(c0, c1) * 2 + 2] = path_char
            elif c0 == c1 and abs(r1 - r0) == 1:
                buf[min(r0, r1) * 2 + 2][c0 * 2 + 1] = path_char

    return buf


def print_buffer(buf: List[List[str]], delay: float = 0.007) -> None:
    for row in buf:
        for cell in row:
            sys.stdout.write(cell)
            sys.stdout.flush()
            if delay > 0:
                time.sleep(delay)
        sys.stdout.write('\n')
    sys.stdout.flush()


def clear_screen() -> None:
    """rints \033[2J\033[H"""
    os.system('clear')
    sys.stdout.flush()


def draw_maze_static(
    grid: List[List[int]],
    height: int,
    width: int,
    entry: Tuple[int, int],
    exit_: Tuple[int, int],
    cell_states: Dict[Tuple[int, int], str],
    colors: Dict[str, str],
    path_cells: Optional[List[Tuple[int, int]]] = None,
    delay: float = 0.007,
) -> None:
    """prints the buffer to terminal"""
    clear_screen()
    buf: List[List[str]] = build_buffer(
        grid, height, width, entry, exit_, cell_states, colors, path_cells
    )
    print_buffer(buf, delay=delay)


TERMINAL_rows, _ = shutil.get_terminal_size()


def _draw_terminal_block(
    terminal_row: int,
    terminal_col: int,
    state: str,
    colors: Dict[str, str],
) -> None:
    color_str = colors.get(state, RESET)
    sys.stdout.write(f'\033[{terminal_row};{terminal_col}H')
    sys.stdout.write(color_str + WALL_CHAR + RESET)


def draw_cell(
    row: int,
    col: int,
    state: str,
    colors: Dict[str, str],
    height: int,
    width: int,
    grid: Optional[List[List[int]]] = None,
    spread_walls: bool = True,
) -> None:
    """moves cursor to (term_row, term_col)
    prints the correctly colored character
    moves cursor back to a safe position (bottom of screen).

    spread_walls: when True (default), open wall slots adjacent to this cell
    are also colored — used for the BFS visited phase so cells look filled in.
    Pass False for path cells so only the cell interior is colored here;
    the connector between two consecutive path cells is drawn separately via
    draw_path_connector.
    """
    if not (0 <= row < height and 0 <= col < width):
        return

    terminal_row, terminal_col = cell_to_terminal(row, col)

    _draw_terminal_block(terminal_row, terminal_col, state, colors)

    if spread_walls and grid is not None:
        cell_val = grid[row][col]
        if not (cell_val & NORTH):
            _draw_terminal_block(row * 2 + 1, col * 4 + 3, state, colors)
        if not (cell_val & SOUTH):
            _draw_terminal_block(row * 2 + 3, col * 4 + 3, state, colors)
        if not (cell_val & WEST):
            _draw_terminal_block(row * 2 + 2, col * 4 + 1, state, colors)
        if not (cell_val & EAST):
            _draw_terminal_block(row * 2 + 2, col * 4 + 5, state, colors)

    sys.stdout.write(f"\033[{TERMINAL_rows};1H")

    sys.stdout.flush()


def draw_path_connector(
    r0: int,
    c0: int,
    r1: int,
    c1: int,
    colors: Dict[str, str],
) -> None:
    """Color the wall slot between two adjacent path cells (r0,c0)-(r1,c1).

    Terminal coordinate derivation - build_buffer places connectors at these
    buffer indices; terminal_col = buf_col*2+1, terminal_row = buf_row+1:
      horizontal pair: buf[r0*2+1][min(c0,c1)*2+2]
        -> term_row = r0*2+2,         term_col = min(c0,c1)*4+5
      vertical pair:   buf[min(r0,r1)*2+2][c0*2+1]
        -> term_row = min(r0,r1)*2+3, term_col = c0*4+3
    """
    path_char = colors.get("path", RESET) + WALL_CHAR + RESET
    if r0 == r1 and abs(c1 - c0) == 1:
        term_row = r0 * 2 + 2
        term_col = min(c0, c1) * 4 + 5
    elif c0 == c1 and abs(r1 - r0) == 1:
        term_row = min(r0, r1) * 2 + 3
        term_col = c0 * 4 + 3
    else:
        sys.stdout.write(f"\033[{TERMINAL_rows};1H")
        sys.stdout.flush()
        return
    sys.stdout.write(f"\033[{term_row};{term_col}H")
    sys.stdout.write(path_char)
    sys.stdout.flush()
    sys.stdout.write(f"\033[{TERMINAL_rows};1H")
    sys.stdout.flush()


class MazeRenderer:
    """Adapter around the function-style renderer helpers."""

    WALL_COLORS: Dict[str, int] = {
        "blue": 21,
        "cyan": 51,
        "green": 40,
        "yellow": 226,
        "red": 196,
        "white": 255,
        "purple": 93,
        "pink": 213,
        "Orange": 202,
    }

    def __init__(self, generator: Any) -> None:
        self.generator = generator
        self.colors: Dict[str, str] = DEFAULT_COLORS.copy()
        self.show_path: bool = False
        self.path_cells: List[Tuple[int, int]] = []
        self.visited_cells: List[Tuple[int, int]] = []
        self.cell_states: Dict[Tuple[int, int], str] = {}
        self._refresh_cell_states()

    @property
    def grid(self) -> List[List[int]]:
        return [
            [int(cell.walls) for cell in row]
            for row in self.generator.get_cells()
        ]

    @property
    def entry_rc(self) -> Tuple[int, int]:
        return (self.generator.entry[1], self.generator.entry[0])

    @property
    def exit_rc(self) -> Tuple[int, int]:
        return (self.generator.exit[1], self.generator.exit[0])

    def _to_row_col(self, cell: Tuple[int, int]) -> Tuple[int, int]:
        x, y = cell
        return (y, x)

    def _refresh_cell_states(self) -> None:
        states: Dict[Tuple[int, int], str] = {}
        for row in self.generator.get_cells():
            for cell in row:
                if cell.is_42:
                    states[(cell.y, cell.x)] = "pattern"

        for cell in self.visited_cells:
            states[self._to_row_col(cell)] = "visited"

        if self.show_path:
            for cell in self.path_cells:
                states[self._to_row_col(cell)] = "path"

        self.cell_states = states

    def set_solution_path(self, path: List[Tuple[int, int]]) -> None:
        self.path_cells = list(path)
        self._refresh_cell_states()

    def set_visited_cells(self, visited: List[Tuple[int, int]]) -> None:
        self.visited_cells = list(visited)
        self._refresh_cell_states()

    def clear_visited_cells(self) -> None:
        self.visited_cells = []
        self._refresh_cell_states()

    def set_path_visibility(self, visible: bool) -> None:
        self.show_path = visible
        self._refresh_cell_states()

    def toggle_path(self) -> None:
        self.set_path_visibility(not self.show_path)

    def _visible_path_rc(self) -> Optional[List[Tuple[int, int]]]:
        if not self.show_path:
            return None
        return [self._to_row_col(cell) for cell in self.path_cells]

    def change_wall_color(self, color_name: str) -> bool:
        code = self.WALL_COLORS.get(color_name.lower())
        if code is None:
            return False
        self.colors["wall"] = color(code)
        return True

    def display(self, clear: bool = True, delay: float = 0.002) -> None:
        height = self.generator.height
        width = self.generator.width
        if clear:
            draw_maze_static(
                self.grid,
                height,
                width,
                self.entry_rc,
                self.exit_rc,
                self.cell_states,
                self.colors,
                self._visible_path_rc(),
                delay=delay,
            )
            return

        print_buffer(build_buffer(
            self.grid,
            height,
            width,
            self.entry_rc,
            self.exit_rc,
            self.cell_states,
            self.colors,
            self._visible_path_rc(),
        ), delay=0)
