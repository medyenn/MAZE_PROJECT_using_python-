*This project has been created as part of the 42 curriculum by mennih, aaheddar.*

# A-Maze-ing

## Description

A-Maze-ing is a Python maze generator and terminal visualizer. It reads a configuration file, generates a valid maze, displays it, allows the user to solve it, and saves the result using a hexadecimal wall encoding format.

The project demonstrates core concepts of graph theory, algorithm design, and modular software architecture.

---

## Instructions

Install dependencies:

```bash
make install
```

Run the program:

```bash
python3 a_maze_ing.py config.txt
```

Available commands:

```bash
make run
make debug
make lint
make build
make clean
```

---

## Configuration File

The configuration file contains one `KEY=VALUE` per line.

Comments start with `#` and are ignored.

### Required keys:

```text
WIDTH=12
HEIGHT=12
ENTRY=0,0
EXIT=11,11
OUTPUT_FILE=maze.txt
PERFECT=True
```

### Optional keys:

```text
SEED=42
ALGORITHM=dfs
DISPLAY_MODE=terminal
```

### Rules:

* Coordinates must be inside maze bounds
* ENTRY and EXIT must be different
* Maze must be valid and fully connected

---

## Maze Algorithm

## Maze Generation

The maze is generated using an **iterative Depth-First Search (DFS) algorithm**, also known as the *recursive backtracker*.

### Principle

The maze is represented as a grid where each cell initially contains all four walls (North, East, South, West). The algorithm progressively removes walls to create valid paths between cells.

### Algorithm Steps

1. Start from an initial cell (usually the entry point).
2. Mark the current cell as visited.
3. Retrieve all unvisited neighboring cells.
4. If at least one unvisited neighbor exists:
   - Select one neighbor randomly.
   - Remove the wall between the current cell and the chosen neighbor.
   - Push the current cell onto a stack.
   - Move to the neighbor and repeat the process.
5. If no unvisited neighbors exist:
   - Backtrack by popping the last cell from the stack.
6. Repeat until all cells have been visited.

### Properties

- Ensures **full connectivity** (every cell is reachable).
- Produces a **perfect maze** when enabled (only one path between entry and exit).
- Guarantees **coherent walls** between adjacent cells.
- Supports **randomness with reproducibility** using a seed.

### Internal Representation

Each cell uses a **bitmask encoding** to store walls:
- North, East, South, West are represented as bits
- Removing a wall corresponds to updating the bitmask

This representation allows efficient storage and easy export to the required hexadecimal format.

## Maze Solving

The maze is solved using a **graph traversal algorithm** based on Breadth-First Search (BFS), ensuring the shortest path from the entry to the exit.

### Principle

The maze is interpreted as a graph:
- Each cell is a node
- Open paths between cells are edges

The solver explores the maze while respecting wall constraints.

### Algorithm Steps

1. Initialize:
   - A queue to explore cells
   - A set to track visited cells
   - A dictionary to store parent relationships

2. Start from the entry cell and add it to the queue.

3. While the queue is not empty:
   - Dequeue the current cell
   - If it is the exit, stop the search
   - Otherwise:
     - Retrieve accessible neighbors (no wall between cells)
     - For each unvisited neighbor:
       - Mark it as visited
       - Store its parent (to reconstruct the path)
       - Add it to the queue

4. Once the exit is reached:
   - Reconstruct the path by following parent links from exit to entry

### Properties

- Guarantees the **shortest path** between entry and exit
- Avoids infinite loops using a visited structure
- Works directly on the maze structure using wall constraints

### Output

The solution is represented as:
- A sequence of coordinates (path)
- A sequence of directions using `N`, `E`, `S`, `W`

This path is also used for visualization in the terminal renderer.

## Why This Algorithm (Maze Generation)

The Depth-First Search (DFS) algorithm was chosen for maze generation because it is simple, efficient, and particularly well-suited for building structured mazes.

DFS naturally produces **perfect mazes**, meaning there is exactly one unique path between any two cells. This property directly satisfies the project requirement when the `PERFECT` mode is enabled.

Additionally, DFS generates mazes with long, winding corridors and very few open areas, which ensures:
- Full connectivity between all cells
- No isolated regions
- A visually coherent and natural maze structure

Another advantage of DFS is its low memory usage, as it relies only on a stack to manage backtracking. It is also easy to implement and debug, making it a reliable choice for this project.

Finally, the algorithm integrates well with randomness (via a seed), allowing reproducible maze generation while still producing varied layouts.

## Why This Algorithm (Maze Solving)

The Breadth-First Search (BFS) algorithm was chosen for maze solving because it guarantees finding the **shortest path** between the entry and the exit.

Unlike Depth-First Search, which may find a path but not necessarily the optimal one, BFS explores the maze level by level. This ensures that the first time the exit is reached, the path taken is the shortest possible in terms of number of steps.

This property is essential for the project, as the output requires the **shortest valid path** to be written using cardinal directions (`N`, `E`, `S`, `W`).

BFS is also well-suited for grid-based structures like mazes, where each cell can be treated as a node in a graph. By using a queue and tracking visited cells, the algorithm avoids infinite loops and ensures efficient traversal.

Finally, BFS provides a straightforward way to reconstruct the solution path using parent tracking, making it both reliable and easy to integrate with the rendering system.

## Reusable Module

The maze generator is implemented as a reusable module (`mazegen`).

Example usage:

```python
from maze_generator import MazeGenerator

maze = MazeGenerator(width=10, height=8, entry=(0,0), exit=(9,7))
maze.generate()
solution = maze.solve()
```

### Features:

* Generate maze with custom parameters
* Access grid structure
* Solve maze (shortest path)
* Export to hexadecimal format

---

## Resources and AI Use

### Resources:

* Python documentation
* `random`, `collections`, `dataclasses`, `typing`
* flake8 and mypy documentation

### AI Usage:

AI was used for:

* Reviewing architecture decisions
* Assisting with documentation writing
* Debugging integration issues
* Understanding algorithm behavior

All generated content was reviewed, tested, and validated by the team.

---

## Team and Project Management

### Roles:

* aaheddar: maze generation, parsing
* mennih: maze solver, renderer, integration

### Planning:

Initial plan was to separate generation, solving, and rendering.
During development, the structure evolved into a modular architecture coordinated by the main file.

### What worked well:

* Clear separation of concerns
* Modular design

### Tools Used:

* Git & GitHub
* flake8
* mypy
* Makefile
* Python virtual environments

---

## Visual Features

* Terminal maze rendering
* Path visualization
* Color customization
* Interactive menu

---
