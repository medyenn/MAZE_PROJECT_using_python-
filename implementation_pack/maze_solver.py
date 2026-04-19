"""Shortest-path solver for the A-Maze-ing project.

Two public functions:
    solve_silent   — pure BFS, no rendering, used for output file generation
    solve_animated — BFS with optional draw_callback for live animation
"""

import time
from collections import deque
from typing import Callable, Deque, Dict, List, Optional, Set, Tuple

NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8

DIRECTIONS: List[Tuple[int, int, int, str]] = [
    (NORTH, -1, 0, "N"),
    (EAST, 0, +1, "E"),
    (SOUTH, +1, 0, "S"),
    (WEST, 0, -1, "W"),
]


def _bfs(
    grid: List[List[int]],
    height: int,
    width: int,
    entry: Tuple[int, int],
    exit_: Tuple[int, int],
) -> Optional[Dict[Tuple[int, int], Tuple[int, int]]]:
    """Run BFS and return came_from dict, or None if unreachable."""
    queue: Deque[Tuple[int, int]] = deque([entry])
    visited: Set[Tuple[int, int]] = {entry}
    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}

    while queue:
        current = queue.popleft()
        if current == exit_:
            return came_from
        r, c = current
        for wall_bit, dr, dc, _ in DIRECTIONS:
            if grid[r][c] & wall_bit:
                continue
            nr, nc = r + dr, c + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if (nr, nc) in visited:
                continue
            visited.add((nr, nc))
            came_from[(nr, nc)] = current
            queue.append((nr, nc))

    return None


def _reconstruct_path(
    came_from: Dict[Tuple[int, int], Tuple[int, int]],
    entry: Tuple[int, int],
    exit_: Tuple[int, int],
) -> Tuple[List[Tuple[int, int]], str]:
    """Backtrack came_from to produce path list and direction string."""
    path: List[Tuple[int, int]] = []
    current = exit_
    while current != entry:
        path.append(current)
        current = came_from[current]
    path.append(entry)
    path.reverse()

    dirs: List[str] = []
    for i in range(len(path) - 1):
        r0, c0 = path[i]
        r1, c1 = path[i + 1]
        dr, dc = r1 - r0, c1 - c0
        if dr == -1:
            dirs.append("N")
        elif dr == +1:
            dirs.append("S")
        elif dc == +1:
            dirs.append("E")
        elif dc == -1:
            dirs.append("W")

    return path, "".join(dirs)


def solve_silent(
    grid: List[List[int]],
    height: int,
    width: int,
    entry: Tuple[int, int],
    exit_: Tuple[int, int],
) -> Tuple[List[Tuple[int, int]], str]:
    """Find shortest path with no display.

    Args:
        grid:   2D list — grid[row][col] = int 0-15
        height: number of maze rows
        width:  number of maze columns
        entry:  (row, col) start cell
        exit_:  (row, col) target cell

    Returns:
        (path_coords, direction_string)

    Raises:
        ValueError if no path exists
    """
    came_from = _bfs(grid, height, width, entry, exit_)
    if came_from is None:
        raise ValueError(
            f"No path from {entry} to {exit_} — maze may be invalid"
        )
    return _reconstruct_path(came_from, entry, exit_)


def solve_animated(
    grid: List[List[int]],
    height: int,
    width: int,
    entry: Tuple[int, int],
    exit_: Tuple[int, int],
    cell_states: Dict[Tuple[int, int], str],
    speed: float = 0.02,
    draw_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Tuple[List[Tuple[int, int]], str]:
    """Find shortest path with optional live cell-by-cell animation.

    Phase 1 — Exploration: cells painted 'visited' as BFS examines them.
    Phase 2 — Backtrack:   shortest-path cells painted 'path'.

    The solver never imports from the renderer. The caller supplies an
    optional draw_callback(row, col, state) that handles all drawing.
    cell_states is updated in-place so a later draw_maze_static call
    reflects the final colours even when draw_callback is None.

    Args:
        grid:          2D list — grid[row][col] = int 0-15
        height:        maze rows
        width:         maze columns
        entry:         (row, col) start
        exit_:         (row, col) target
        cell_states:   updated in-place with state per cell
        speed:         seconds between draw_callback calls
        draw_callback: optional callable(row, col, state)

    Returns:
        (path_coords, direction_string)

    Raises:
        ValueError if no path exists
    """
    queue: Deque[Tuple[int, int]] = deque([entry])
    visited: Set[Tuple[int, int]] = {entry}
    came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
    found = False

    while queue:
        current = queue.popleft()
        r, c = current

        if current != entry and current != exit_:
            cell_states[current] = "visited"
            if draw_callback is not None:
                draw_callback(r, c, "visited")
                time.sleep(speed)

        if current == exit_:
            found = True
            break

        for wall_bit, dr, dc, _ in DIRECTIONS:
            if grid[r][c] & wall_bit:
                continue
            nr, nc = r + dr, c + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if (nr, nc) in visited:
                continue
            visited.add((nr, nc))
            came_from[(nr, nc)] = current
            queue.append((nr, nc))

    if not found:
        raise ValueError(
            f"No path from {entry} to {exit_} — maze may be invalid"
        )

    path, path_str = _reconstruct_path(came_from, entry, exit_)

    for cell in path:
        r, c = cell
        if cell != entry and cell != exit_:
            cell_states[cell] = "path"
            if draw_callback is not None:
                draw_callback(r, c, "path")
                time.sleep(speed)

    return path, path_str
