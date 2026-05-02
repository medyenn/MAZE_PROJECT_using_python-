""""Main entry point for the A-Maze-ing project."""

from __future__ import annotations

import sys
from typing import Optional

from implementation_pack.config_parser import ConfigError, ConfigParser, MazeConfig
from implementation_pack.maze_generator import MazeGenerator, SolutionResult
from implementation_pack.maze_renderer import MazeRenderer, draw_cell, draw_path_connector, color


RESET = "\033[0m"
BOLD = "\033[1m"

C_TITLE = "\033[1;38;5;51m"
C_BORDER = "\033[38;5;240m"
C_LABEL = "\033[38;5;117m"
C_VALUE = "\033[1;38;5;31m"
C_SUCCESS = "\033[38;5;82m"
C_ERROR = "\033[38;5;196m"
C_PROMPT = "\033[38;5;226m"
C_DIM = "\033[38;5;240m"
C_WARN = "\033[38;5;214m"


COLOR_OPTIONS = [
    ("Green",     40),
    ("Cyan",      51),
    ("Blue",      27),
    ("Purple",    57),
    ("Pink",     213),
    ("Orange",   202),
    ("Yellow",   226),
    ("Red",      196),
    ("Teal",      30),
    ("Lavender", 141),
    ("White",    255),
    ("Crimson",  88),
]

SPEED_FAST = 0.01
SPEED_SLOW = 0.09


def _write(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def _ok(msg: str) -> None:
    print(C_SUCCESS + "  ✓ " + msg + RESET)


def _err(msg: str) -> None:
    print(C_ERROR + "  ✗ " + msg + RESET)


def _warn(msg: str) -> None:
    print(C_WARN + "  ! " + msg + RESET)


def _info(msg: str) -> None:
    print(C_LABEL + "  " + msg + RESET)


def _prompt(msg: str) -> Optional[str]:
    """Read one line. Returns None on EOF (Ctrl+D). Ignores Ctrl+C."""
    while True:
        try:
            return input(C_PROMPT + msg + RESET).strip()
        except KeyboardInterrupt:
            print()
            _warn("Ctrl+C — use [0] or Ctrl+D to quit.")
        except EOFError:
            print()
            return None


def _val(text: str) -> str:
    """Wrap a status value in the highlight style."""
    return C_VALUE + "[" + text + "]" + RESET


def _color_name_for(code: int) -> str:
    """Return the display name for a color code, or the code as fallback."""
    for name, c in COLOR_OPTIONS:
        if c == code:
            return name
    return str(code)


def _current_color_name(renderer: MazeRenderer, key: str) -> str:
    """Extract the color name currently active for a renderer color key."""
    ansi = renderer.colors.get(key, "")
    for name, code in COLOR_OPTIONS:
        if f"\033[38;5;{code}m" in ansi:
            return name
    return "custom"


def _current_color_ref(renderer: MazeRenderer, key: str) -> str:
    """Extract the color name currently active for a renderer color key."""
    ansi = renderer.colors.get(key, "")
    for name, code in COLOR_OPTIONS:
        if f"\033[38;5;{code}m" in ansi:
            return f"\033[38;5;{code}m"
    return C_VALUE


def print_status(
    config: MazeConfig,
    solution: SolutionResult,
    renderer: MazeRenderer,
    anim_speed: float,
) -> None:
    path_state = "shown" if renderer.show_path else "hidden"
    speed_name = "Fast" if anim_speed <= SPEED_FAST else "Slow"

    print(C_BORDER + "─" * 44 + RESET)
    _info(
        f"Size: {config.width} x {config.height}  "
        f"Seed: {config.seed}  "
        f"Perfect: {config.perfect}  "
        f"Output: {config.output_file}"
    )
    _info(
        f"Path length: {solution.length}  "
        f"Path: {_val(path_state)}  "
        f"Speed: {_val(speed_name)}"
    )
    print(C_BORDER + "─" * 44 + RESET)


def print_menu(
    renderer: MazeRenderer,
    config: MazeConfig,
    anim_speed: float,
) -> None:
    speed_name = "Fast" if anim_speed <= SPEED_FAST else "Slow"
    path_label = "Hide path" if renderer.show_path else "Show path"
    wall_name = _current_color_name(renderer, "wall")
    wall_ref = _current_color_ref(renderer, "wall")

    path_name = _current_color_name(renderer, "path")
    path_ref = _current_color_ref(renderer, "path")

    pat_name = _current_color_name(renderer, "pattern")
    pat_ref = _current_color_ref(renderer, "pattern")

    W = C_BORDER
    R = RESET
    L = C_LABEL
    V = C_VALUE

    print()
    print(W + "┌─ Actions " + "─" * 29 + "┐" + R)
    print(
        W + "│" + R + f"  {L}[1]{R} Re-generate maze" + "\t" * 3 + W + "│" + R)
    print(
        W + "│" + R + f"  {L}[2]{R} Animated"
        " BFS solve" + "\t" * 2 + W + "│" + R)
    print(W + "│" + R + f"  {L}[3]{R} {path_label}" + "\t" * 3 + W + "│" + R)
    print(
        W + "│" + R + f"  {L}[4]{R} Wall color    {wall_ref}[{wall_name}]"
        f"{R}" + "\t" * 2 + W + "│" + R)
    print(
        W + "│" + R + f"  {L}[5]{R} Path color    {path_ref}[{path_name}]"
        f"{R}" + "\t" * 2 + W + "│" + R)
    print(
        W + "│" + R + f"  {L}[6]{R} Pattern color {pat_ref}[{pat_name}]"
        f"{R}" + "\t" * 2 + W + "│" + R)
    print(W + "│" + R + f"  {L}[7]{R} Anim speed    {V}[{speed_name}]{R}" +
           "\t" * 2 + W + "│" + R)
    print(
        W + "│" + R + f"  {L}[8]{R} Perfect mode  {V}[{config.perfect}]"
        f"{R}" + "\t" * 2 + W + "│" + R)
    print(W + "│" + R + f"  {L}[0]{R} Quit" + "\t" * 4 + W + "│" + R)
    print(W + "└" + "─" * 39 + "┘" + R)


def _color_submenu(
    title: str,
    renderer: MazeRenderer,
    config: MazeConfig,
    solution: SolutionResult,
    anim_speed: float,
    color_key: str,
) -> Optional[bool]:
    """Show color picker sub-menu. Returns None on EOF, True otherwise."""
    invalid = False
    while True:
        renderer.display(clear=True, delay=0)
        print_status(config, solution, renderer, anim_speed)
        print()
        print(
            C_BORDER + f"┌─ {title} " + "─" * (39 - len(title)) + "┐" + RESET)

        for i, (name, code) in enumerate(COLOR_OPTIONS, 1):
            swatch = f"\033[38;5;{code}m██{RESET}"
            num = f"{C_LABEL}[{i:2d}]{RESET}"
            name_colored = f"\033[38;5;{code}m{name}{RESET}"
            line = f"  {num} {swatch} {name_colored}"
            pad = " " * max(0, 32 - len(name))
            print(
                C_BORDER + "│" + RESET + line + pad + C_BORDER + "│" + RESET)

        print(C_BORDER + "│" + RESET + f"  {C_LABEL}[ 0]{RESET} ← Go back" +
               "\t" * 3 + "   " + C_BORDER + "│" + RESET)
        print(C_BORDER + "└" + "─" * 42 + "┘" + RESET)

        if invalid:
            _err("Please select a valid option.")
            invalid = False

        choice = _prompt(f"Color choice (0-{len(COLOR_OPTIONS)}): ")
        if choice is None:
            return None
        if choice == "0":
            return True
        try:
            idx = int(choice) - 1
            if not (0 <= idx < len(COLOR_OPTIONS)):
                raise ValueError
            name, code = COLOR_OPTIONS[idx]
            renderer.colors[color_key] = color(code)
            _ok(f"{title} set to {name}.")
            return True
        except (ValueError, IndexError):
            invalid = True


def _speed_submenu(
    renderer: MazeRenderer,
    config: MazeConfig,
    solution: SolutionResult,
    anim_speed: float,
) -> Optional[float]:
    """Return new speed, or None on EOF."""
    invalid = False
    while True:
        renderer.display(clear=True, delay=0)
        print_status(config, solution, renderer, anim_speed)
        print()
        print(C_BORDER + "┌─ Animation Speed " + "─" * 24 + "┐" + RESET)
        print(
            C_BORDER + "│" + RESET + f"  {C_LABEL}[1]{RESET} Fast"
            f"  {C_DIM}(0.01s / cell)"
            f"{RESET}" + "\t" * 2 + "   " + C_BORDER + "│" + RESET)
        print(
            C_BORDER + "│" + RESET + f"  {C_LABEL}[2]{RESET} Slow"
            f"  {C_DIM}(0.08s / cell)"
            f"{RESET}" + "\t" * 2 + "   " + C_BORDER + "│" + RESET)
        print(C_BORDER + "│" + RESET + f"  {C_LABEL}[0]{RESET} ← Go back" +
               "\t" * 3 + "   " + C_BORDER + "│" + RESET)
        print(C_BORDER + "└" + "─" * 42 + "┘" + RESET)

        if invalid:
            _err("Please select 0, 1, or 2.")
            invalid = False

        choice = _prompt("Speed choice (0-2): ")
        if choice is None:
            return None
        if choice == "0":
            return anim_speed
        elif choice == "1":
            _ok("Animation speed set to Fast.")
            return SPEED_FAST
        elif choice == "2":
            _ok("Animation speed set to Slow.")
            return SPEED_SLOW
        else:
            invalid = True


def _animate_solve(
    config: MazeConfig,
    generator: MazeGenerator,
    renderer: MazeRenderer,
    anim_speed: float,
) -> SolutionResult:
    """Run BFS animation then reveal the shortest path."""
    from implementation_pack.maze_solver import solve_animated

    renderer.set_path_visibility(False)
    renderer.clear_visited_cells()
    solution = _compute_solution(generator)
    renderer.set_solution_path(solution.path)
    renderer.display(clear=True, delay=0)

    grid = renderer.grid

    def _callback(r: int, c: int, state: str) -> None:
        if state == "path":
            draw_cell(r, c, state, renderer.colors,
                      generator.height, generator.width,
                      grid=None, spread_walls=False)
            prev = _callback.prev_path_cell  # type: ignore
            if prev is not None:
                draw_path_connector(prev[0], prev[1], r, c, renderer.colors)
            _callback.prev_path_cell = (r, c)  # type: ignore
        else:
            draw_cell(r, c, state, renderer.colors,
                      generator.height, generator.width, grid)
    _callback.prev_path_cell = renderer.entry_rc  # type: ignore

    try:
        path_rc, directions = solve_animated(
            grid,
            generator.height,
            generator.width,
            renderer.entry_rc,
            renderer.exit_rc,
            renderer.cell_states,
            speed=anim_speed,
            draw_callback=_callback,
        )
        if (
            len(path_rc) >= 2
                and _callback.prev_path_cell is not None):  # type: ignore
            draw_path_connector(
                _callback.prev_path_cell[0],  # type: ignore
                _callback.prev_path_cell[1],  # type: ignore
                renderer.exit_rc[0], renderer.exit_rc[1],
                renderer.colors,
            )
        path = [(col, row) for row, col in path_rc]
        solution = SolutionResult(
            found=True,
            path=path,
            directions=directions,
            length=max(0, len(path) - 1),
        )
    except KeyboardInterrupt:
        print()
        _warn("Animation interrupted — showing static result.")
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    renderer.clear_visited_cells()
    renderer.set_solution_path(solution.path)
    renderer.set_path_visibility(True)
    renderer.display(clear=True, delay=0)

    _save_output(generator, config.output_file)

    return solution


def _build_generator(config: MazeConfig) -> MazeGenerator:
    try:
        generator = MazeGenerator(config)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc

    if not generator.generate():
        raise RuntimeError("Maze generation failed.")
    return generator


def _compute_solution(generator: MazeGenerator) -> SolutionResult:
    result = generator.solve()
    if not result.found:
        raise RuntimeError("No valid path found between ENTRY and EXIT.")
    return result


def _create_renderer(
    generator: MazeGenerator,
    solution: SolutionResult,
) -> MazeRenderer:
    renderer = MazeRenderer(generator)
    renderer.set_solution_path(solution.path)
    return renderer


def _save_output(generator: MazeGenerator, output_file: str) -> bool:
    if generator.save_to_file(output_file):
        _ok(f"Output saved to '{output_file}'.")
        return True

    if generator.last_save_error:
        _err(generator.last_save_error)
    else:
        _err("Could not save output file.")
    return False


def _err_inline(msg: str) -> None:
    """Print error above current prompt without adding new prompt."""
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")
    print(C_ERROR + "  ✗ " + msg + RESET)


def _loop(config: MazeConfig) -> int:
    """Main interactive loop. Returns exit code."""
    anim_speed: float = SPEED_FAST

    generator = _build_generator(config)
    solution = _compute_solution(generator)
    _save_output(generator, config.output_file)

    renderer = _create_renderer(generator, solution)
    renderer.display(clear=True, delay=0.001)
    print_status(config, solution, renderer, anim_speed)

    choice_flag = True
    while True:
        if choice_flag:
            print_menu(renderer, config, anim_speed)

        choice_flag = True
        choice = _prompt("Choice (0-8): ")

        if choice is None or choice == "0":
            _info("Goodbye.")
            return 0

        if choice == "1":
            seed_str = _prompt(
                "New seed (Enter to keep current): "
            )
            if seed_str is None:
                _info("Goodbye.")
                return 0

            from implementation_pack.config_parser import MazeConfig as MC
            new_seed = config.seed
            if seed_str:
                try:
                    new_seed = int(seed_str)
                except ValueError:
                    _err("Invalid seed — keeping current.")

            config = MC(
                width=config.width,
                height=config.height,
                entry=config.entry,
                exit=config.exit,
                output_file=config.output_file,
                perfect=config.perfect,
                seed=new_seed,
                algorithm=config.algorithm,
                display_mode=config.display_mode,
            )

            try:
                generator = _build_generator(config)
                solution = _compute_solution(generator)
                _save_output(generator, config.output_file)
                renderer = _create_renderer(generator, solution)
                renderer.display(clear=True, delay=0.001)
                print_status(config, solution, renderer, anim_speed)
                _ok("New maze generated.")
            except RuntimeError as exc:
                _err(str(exc))
            choice_flag = True
            continue

        if choice == "2":
            try:
                solution = _animate_solve(
                    config, generator, renderer, anim_speed
                )
                print_status(config, solution, renderer, anim_speed)
                _ok("Shortest path found and displayed.")
            except RuntimeError as exc:
                _err(str(exc))
            choice_flag = True
            continue

        if choice == "3":
            renderer.toggle_path()
            renderer.display(clear=True, delay=0)
            print_status(config, solution, renderer, anim_speed)
            state = "shown" if renderer.show_path else "hidden"
            _ok(f"Path is now {state}.")
            continue

        if choice == "4":
            result = _color_submenu(
                "Wall Color", renderer, config, solution, anim_speed, "wall"
            )
            if result is None:
                _info("Goodbye.")
                return 0
            renderer.display(clear=True, delay=0)
            print_status(config, solution, renderer, anim_speed)
            continue

        if choice == "5":
            result = _color_submenu(
                "Path Color", renderer, config, solution, anim_speed, "path"
            )
            if result is None:
                _info("Goodbye.")
                return 0
            renderer.display(clear=True, delay=0)
            print_status(config, solution, renderer, anim_speed)
            continue

        if choice == "6":
            result = _color_submenu(
                "42 Pattern Color",
                renderer, config, solution, anim_speed, "pattern")
            if result is None:
                _info("Goodbye.")
                return 0
            renderer.display(clear=True, delay=0)
            print_status(config, solution, renderer, anim_speed)
            continue

        if choice == "7":
            new_speed = _speed_submenu(
                renderer, config, solution, anim_speed
            )
            if new_speed is None:
                _info("Goodbye.")
                return 0
            anim_speed = new_speed
            renderer.display(clear=True, delay=0)
            print_status(config, solution, renderer, anim_speed)
            continue

        if choice == "8":
            from implementation_pack.config_parser import MazeConfig as MC
            config = MC(
                width=config.width,
                height=config.height,
                entry=config.entry,
                exit=config.exit,
                output_file=config.output_file,
                perfect=not config.perfect,
                seed=config.seed,
                algorithm=config.algorithm,
                display_mode=config.display_mode,
            )
            _ok(f"Perfect mode is now {config.perfect}. "
                "Press [1] to regenerate.")
            choice_flag = False
            continue

        else:
            choice_flag = False
            _err_inline("Invalid choice — enter a number from 0 to 8.")


def main() -> int:
    """Parse config and run the interactive loop."""
    if len(sys.argv) != 2:
        print(C_ERROR + "Usage: python3 a_maze_ing.py <config_file>" + RESET,
              file=sys.stderr)
        return 1

    try:
        _info(f"Loading config: {sys.argv[1]}")
        config = ConfigParser.parse(sys.argv[1])
    except KeyboardInterrupt:
        print()
        _err("Interrupted during startup.")
        return 1
    except ConfigError as exc:
        _err(f"Config error: {exc}")
        return 1
    except Exception as exc:
        _err(f"Unexpected error: {exc}")
        return 1

    while True:
        try:
            return _loop(config)
        except KeyboardInterrupt:
            print()
            _warn("Ctrl+C — use [0] or Ctrl+D to quit.")
        except RuntimeError as exc:
            _err(str(exc))
            return 1
        except Exception as exc:
            _err(f"Unexpected error: {exc}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
