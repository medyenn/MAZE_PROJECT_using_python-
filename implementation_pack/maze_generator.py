"""Maze generation logic for the main project.

This module builds the maze used by the application from a parsed
configuration object. It keeps the same general structure as the
reusable MazeGenerator module, while adding the mandatory "42"
blocked pattern required by the subject when the maze is large
enough to contain it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag
from pathlib import Path
import random
from typing import Dict, List, Optional, Set, Tuple

from .config_parser import MazeConfig
from .maze_solver import solve_silent


class Wall(IntFlag):
    """Bit flags describing which walls of a cell are closed."""

    NONE = 0
    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8
    ALL = NORTH | EAST | SOUTH | WEST


@dataclass
class Cell:
    """Store one maze cell and its current state."""

    x: int
    y: int
    walls: Wall = Wall.ALL
    visited: bool = False
    is_42: bool = False


@dataclass
class SolutionResult:
    """Store the result of a shortest-path search."""

    found: bool
    path: List[Tuple[int, int]]
    directions: str
    length: int


@dataclass
class SolutionTraceResult:
    """Store the shortest path and BFS visit order used for animation."""

    found: bool
    path: List[Tuple[int, int]]
    directions: str
    length: int
    visited_order: List[Tuple[int, int]]


DIRECTIONS: Dict[str, Tuple[int, int, Wall, Wall]] = {
    "N": (0, -1, Wall.NORTH, Wall.SOUTH),
    "E": (1, 0, Wall.EAST, Wall.WEST),
    "S": (0, 1, Wall.SOUTH, Wall.NORTH),
    "W": (-1, 0, Wall.WEST, Wall.EAST),
}


class MazeGenerator:
    """
    Generate and solve the maze defined by a MazeConfig instance.

    The maze is carved with an iterative depth-first traversal.
    Cells reserved for the mandatory "42" figure stay fully closed
    and are excluded from the carved walkable area.
    """

    _PATTERN_OFFSETS: List[Tuple[int, int]] = [
        # "4" (3 columns wide)
        (0, 0), (2, 0),
        (0, 1), (2, 1),
        (0, 2), (1, 2), (2, 2),
        (2, 3),
        (2, 4),
        # "2" (3 columns wide), starting at x=4 (1-column gap)
        (4, 0), (5, 0), (6, 0),
        (6, 1),
        (4, 2), (5, 2), (6, 2),
        (4, 3),
        (4, 4), (5, 4), (6, 4),
    ]
    _PATTERN_WIDTH = 7
    _PATTERN_HEIGHT = 5

    def __init__(self, config: MazeConfig) -> None:
        self.width: int = config.width
        self.height: int = config.height
        self.entry: Tuple[int, int] = config.entry
        self.exit: Tuple[int, int] = config.exit
        self.seed: Optional[int] = config.seed
        self.perfect: bool = config.perfect
        self.output_file: str = config.output_file
        self.last_save_error: Optional[str] = None

        self._random: random.Random = random.Random(self.seed)
        self._cells: List[List[Cell]] = []
        self._pattern_drawn: bool = False

        self._validate_init_args()

    def _validate_init_args(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Width and height must be positive integers.")

        self._validate_position(self.entry, "ENTRY")
        self._validate_position(self.exit, "EXIT")

        if self.entry == self.exit:
            raise ValueError("ENTRY and EXIT must be different cells.")

        self._validate_entry_exit_not_in_pattern()

    def _validate_position(
        self,
        position: Tuple[int, int],
        label: str,
    ) -> None:
        x, y = position
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError(f"{label} is outside maze bounds.")

    def _init_grid(self) -> None:
        self._cells = []
        for y in range(self.height):
            row: List[Cell] = []
            for x in range(self.width):
                row.append(Cell(x=x, y=y))
            self._cells.append(row)

    def _get_cell(self, x: int, y: int) -> Optional[Cell]:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._cells[y][x]
        return None

    def _get_unvisited_neighbors(self, cell: Cell) -> List[Tuple[str, Cell]]:
        neighbors: List[Tuple[str, Cell]] = []

        for direction, (dx, dy, _, _) in DIRECTIONS.items():
            neighbor: Optional[Cell] = self._get_cell(cell.x + dx, cell.y + dy)
            if neighbor is None:
                continue
            if neighbor.visited:
                continue
            if neighbor.is_42:
                continue
            neighbors.append((direction, neighbor))

        return neighbors

    def _remove_wall_between(
        self,
        current: Cell,
        neighbor: Cell,
        direction: str,
    ) -> None:
        _, _, current_wall, neighbor_wall = DIRECTIONS[direction]
        current.walls &= ~current_wall
        neighbor.walls &= ~neighbor_wall

    def _pattern_origin(self) -> Optional[Tuple[int, int]]:
        min_width: int = self._PATTERN_WIDTH + 2
        min_height: int = self._PATTERN_HEIGHT + 2

        if self.width < min_width or self.height < min_height:
            return None

        start_x: int = (self.width - self._PATTERN_WIDTH) // 2
        start_y: int = (self.height - self._PATTERN_HEIGHT) // 2
        return (start_x, start_y)

    def _pattern_cells(self) -> Set[Tuple[int, int]]:
        origin: Optional[Tuple[int, int]] = self._pattern_origin()
        if origin is None:
            return set()

        start_x, start_y = origin
        return {
            (start_x + offset_x, start_y + offset_y)
            for offset_x, offset_y in self._PATTERN_OFFSETS
            if 0 <= start_x + offset_x < self.width
            and 0 <= start_y + offset_y < self.height
        }

    def _validate_entry_exit_not_in_pattern(self) -> None:
        pattern_cells = self._pattern_cells()
        if self.entry in pattern_cells:
            raise ValueError(
                "ENTRY cannot be inside the mandatory 42 pattern.")
        if self.exit in pattern_cells:
            raise ValueError("EXIT cannot be inside the mandatory 42 pattern.")

    def _draw_42_pattern(self) -> bool:
        origin: Optional[Tuple[int, int]] = self._pattern_origin()
        if origin is None:
            print("Error: maze too small to display the mandatory 42 pattern.")
            self._pattern_drawn = False
            return False

        start_x, start_y = origin

        for offset_x, offset_y in self._PATTERN_OFFSETS:
            x: int = start_x + offset_x
            y: int = start_y + offset_y

            if (x, y) == self.entry or (x, y) == self.exit:
                continue

            cell: Optional[Cell] = self._get_cell(x, y)
            if cell is None:
                continue

            cell.walls = Wall.ALL
            cell.visited = True
            cell.is_42 = True

        self._pattern_drawn = True
        return True

    def _find_generation_start(self) -> Optional[Cell]:
        entry_cell: Optional[Cell] = self._get_cell(
            self.entry[0],
            self.entry[1],
        )
        if entry_cell is not None and not entry_cell.is_42:
            return entry_cell

        for row in self._cells:
            for cell in row:
                if not cell.is_42:
                    return cell

        return None

    def _carve_paths(self) -> bool:
        start_cell: Optional[Cell] = self._find_generation_start()
        if start_cell is None:
            return False

        stack: List[Cell] = [start_cell]
        start_cell.visited = True

        while stack:
            current: Cell = stack[-1]
            neighbors: List[Tuple[str, Cell]] = (
                self._get_unvisited_neighbors(current)
            )

            if not neighbors:
                stack.pop()
                continue

            direction, neighbor = self._random.choice(neighbors)
            self._remove_wall_between(current, neighbor, direction)
            neighbor.visited = True
            stack.append(neighbor)

        return True

    def _enforce_border_walls(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                cell: Cell = self._cells[y][x]

                if y == 0:
                    cell.walls |= Wall.NORTH
                if y == self.height - 1:
                    cell.walls |= Wall.SOUTH
                if x == 0:
                    cell.walls |= Wall.WEST
                if x == self.width - 1:
                    cell.walls |= Wall.EAST

    def _snapshot_walls(self) -> List[List[Wall]]:
        return [[cell.walls for cell in row] for row in self._cells]

    def _restore_walls(self, snapshot: List[List[Wall]]) -> None:
        for y in range(self.height):
            for x in range(self.width):
                self._cells[y][x].walls = snapshot[y][x]

    def _imperfect_candidates(self) -> List[Tuple[int, int, str]]:
        candidates: List[Tuple[int, int, str]] = []

        for y in range(self.height):
            for x in range(self.width):
                cell = self._cells[y][x]
                if cell.is_42:
                    continue

                if x + 1 < self.width:
                    right = self._cells[y][x + 1]
                    if (not right.is_42) and (cell.walls & Wall.EAST):
                        candidates.append((x, y, "E"))

                if y + 1 < self.height:
                    bottom = self._cells[y + 1][x]
                    if (not bottom.is_42) and (cell.walls & Wall.SOUTH):
                        candidates.append((x, y, "S"))

        return candidates

    def _open_candidate(self, x: int, y: int, direction: str) -> bool:
        dx, dy, _, _ = DIRECTIONS[direction]
        current = self._get_cell(x, y)
        neighbor = self._get_cell(x + dx, y + dy)
        if current is None or neighbor is None:
            return False
        self._remove_wall_between(current, neighbor, direction)
        return True

    def _check_wall_consistency(self) -> bool:
        for y in range(self.height):
            for x in range(self.width):
                cell = self._cells[y][x]
                if x + 1 < self.width:
                    east_open = not (cell.walls & Wall.EAST)
                    west_open = not (self._cells[y][x + 1].walls & Wall.WEST)
                    if east_open != west_open:
                        return False
                if y + 1 < self.height:
                    south_open = not (cell.walls & Wall.SOUTH)
                    north_open = not (self._cells[y + 1][x].walls & Wall.NORTH)
                    if south_open != north_open:
                        return False
        return True

    def _check_border_walls(self) -> bool:
        for x in range(self.width):
            if not (self._cells[0][x].walls & Wall.NORTH):
                return False
            if not (self._cells[self.height - 1][x].walls & Wall.SOUTH):
                return False
        for y in range(self.height):
            if not (self._cells[y][0].walls & Wall.WEST):
                return False
            if not (self._cells[y][self.width - 1].walls & Wall.EAST):
                return False
        return True

    def _check_no_forbidden_open_areas(self) -> bool:
        if self.width < 3 or self.height < 3:
            return True

        for y in range(self.height - 2):
            for x in range(self.width - 2):
                fully_open = True
                for by in range(y, y + 3):
                    for bx in range(x, x + 3):
                        cell = self._cells[by][bx]
                        if bx < x + 2 and (cell.walls & Wall.EAST):
                            fully_open = False
                            break
                        if by < y + 2 and (cell.walls & Wall.SOUTH):
                            fully_open = False
                            break
                    if not fully_open:
                        break
                if fully_open:
                    return False
        return True

    def _check_connectivity_walkable(self) -> bool:
        start = self.entry
        if self._cells[start[1]][start[0]].is_42:
            return False

        visited: Set[Tuple[int, int]] = {start}
        frontier: List[Tuple[int, int]] = [start]

        while frontier:
            cx, cy = frontier.pop()
            current = self._cells[cy][cx]
            for dx, dy, wall_mask, _ in DIRECTIONS.values():
                nx = cx + dx
                ny = cy + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if self._cells[ny][nx].is_42:
                    continue
                if current.walls & wall_mask:
                    continue
                nxt = (nx, ny)
                if nxt in visited:
                    continue
                visited.add(nxt)
                frontier.append(nxt)

        for y in range(self.height):
            for x in range(self.width):
                if self._cells[y][x].is_42:
                    continue
                if (x, y) not in visited:
                    return False

        return True

    def _check_42_pattern_integrity(self) -> bool:
        if not self._pattern_drawn:
            return True

        origin = self._pattern_origin()
        if origin is None:
            return True

        start_x, start_y = origin
        for offset_x, offset_y in self._PATTERN_OFFSETS:
            x = start_x + offset_x
            y = start_y + offset_y
            if (x, y) == self.entry or (x, y) == self.exit:
                continue
            cell = self._get_cell(x, y)
            if cell is None:
                return False
            if not cell.is_42:
                return False
            if cell.walls != Wall.ALL:
                return False

        return True

    def _is_valid_generated_maze(self) -> bool:
        if not self._cells:
            return False
        if not self._check_wall_consistency():
            return False
        if not self._check_border_walls():
            return False
        if not self._check_no_forbidden_open_areas():
            return False
        if not self._check_42_pattern_integrity():
            return False

        entry_cell = self._get_cell(*self.entry)
        exit_cell = self._get_cell(*self.exit)
        if entry_cell is None or exit_cell is None:
            return False
        if entry_cell.is_42 or exit_cell.is_42:
            return False

        if not self._check_connectivity_walkable():
            return False

        return self.solve().found

    def _apply_imperfect_openings(self) -> bool:
        candidates = self._imperfect_candidates()
        if not candidates:
            return False

        self._random.shuffle(candidates)
        target_openings = max(1, len(candidates) // 12)
        opened = 0

        for x, y, direction in candidates:
            if opened >= target_openings:
                break

            snapshot = self._snapshot_walls()
            if not self._open_candidate(x, y, direction):
                continue

            self._enforce_border_walls()
            if self._is_valid_generated_maze():
                opened += 1
            else:
                self._restore_walls(snapshot)

        return opened > 0

    def generate(self) -> bool:
        try:
            self._init_grid()
            self._draw_42_pattern()

            if not self._carve_paths():
                return False

            self._enforce_border_walls()

            if not self._is_valid_generated_maze():
                return False

            if not self.perfect:
                baseline = self._snapshot_walls()
                improved = self._apply_imperfect_openings()
                if not improved:
                    self._restore_walls(baseline)
                    print("Error: could not create an imperfect maze safely; "
                          "falling back to valid perfect layout.")

                if not self._is_valid_generated_maze():
                    self._restore_walls(baseline)
                    if not self._is_valid_generated_maze():
                        return False

            return True
        except (IndexError, KeyError, ValueError):
            return False

    def get_cells(self) -> List[List[Cell]]:
        return self._cells

    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        return self._get_cell(x, y)

    def _to_solver_grid(self) -> List[List[int]]:
        return [[int(cell.walls) for cell in row] for row in self._cells]

    def solve_with_trace(
        self,
        start: Optional[Tuple[int, int]] = None,
        end: Optional[Tuple[int, int]] = None,
    ) -> SolutionTraceResult:
        if not self._cells:
            return SolutionTraceResult(False, [], "", -1, [])

        start_pos: Tuple[int, int] = start if start is not None else self.entry
        end_pos: Tuple[int, int] = end if end is not None else self.exit

        try:
            self._validate_position(start_pos, "START")
            self._validate_position(end_pos, "END")
        except ValueError:
            return SolutionTraceResult(False, [], "", -1, [])

        if self._cells[start_pos[1]][start_pos[0]].is_42:
            return SolutionTraceResult(False, [], "", -1, [])
        if self._cells[end_pos[1]][end_pos[0]].is_42:
            return SolutionTraceResult(False, [], "", -1, [])

        try:
            row_col_path, directions = solve_silent(
                self._to_solver_grid(),
                self.height,
                self.width,
                (start_pos[1], start_pos[0]),
                (end_pos[1], end_pos[0]),
            )
        except ValueError:
            return SolutionTraceResult(False, [], "", -1, [])

        path = [(col, row) for row, col in row_col_path]
        return SolutionTraceResult(
            found=True,
            path=path,
            directions=directions,
            length=max(0, len(path) - 1),
            visited_order=path,
        )

    def solve(
        self,
        start: Optional[Tuple[int, int]] = None,
        end: Optional[Tuple[int, int]] = None,
    ) -> SolutionResult:
        traced = self.solve_with_trace(start=start, end=end)
        return SolutionResult(
            found=traced.found,
            path=traced.path,
            directions=traced.directions,
            length=traced.length,
        )

    def to_hex_rows(self) -> List[str]:
        rows: List[str] = []

        for row in self._cells:
            hex_row: str = "".join(
                format(int(cell.walls), "X") for cell in row)
            rows.append(hex_row)

        return rows

    def to_output_string(self) -> str:
        solution: SolutionResult = self.solve()
        lines: List[str] = self.to_hex_rows()
        lines.append("")
        lines.append(f"{self.entry[0]},{self.entry[1]}")
        lines.append(f"{self.exit[0]},{self.exit[1]}")
        lines.append(solution.directions)
        return "\n".join(lines) + "\n"

    def save_to_file(self, output_file: Optional[str] = None) -> bool:
        target: str = (
            output_file if output_file is not None else self.output_file
        )
        output_path = Path(target).expanduser()
        self.last_save_error = None

        try:
            if output_path.parent != Path("."):
                output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as file:
                file.write(self.to_output_string())
            return True
        except PermissionError:
            self.last_save_error = (
                f"Permission denied while writing output file: {target}"
            )
            return False
        except FileNotFoundError:
            self.last_save_error = (
                "Output path does not exist and could"
                f" not be created: {target}")
            return False
        except IsADirectoryError:
            self.last_save_error = (
                f"Output path is a directory, not a file: {target}"
            )
            return False
        except OSError as exc:
            self.last_save_error = (
                f"Unable to write output file '{target}': {exc}"
            )
            return False
