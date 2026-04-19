"""Configuration parser for the A-Maze-ing project.

This module reads a configuration file written with one KEY=VALUE pair
per line, validates the content, and returns a MazeConfig instance
ready to be used by the project maze generator.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""


@dataclass
class MazeConfig:
    """Store validated maze configuration values."""

    width: int
    height: int
    entry: Tuple[int, int]
    exit: Tuple[int, int]
    output_file: str
    perfect: bool
    seed: Optional[int] = None
    algorithm: Optional[str] = None
    display_mode: Optional[str] = None


class ConfigParser:
    """Parse and validate the project configuration file."""

    REQUIRED_KEYS = {
        "WIDTH",
        "HEIGHT",
        "ENTRY",
        "EXIT",
        "OUTPUT_FILE",
        "PERFECT",
    }

    OPTIONAL_KEYS = {
        "SEED",
        "ALGORITHM",
        "DISPLAY_MODE",
    }

    @classmethod
    def parse(cls, file_path: str) -> MazeConfig:
        """
        Read, validate, and convert one configuration file.

        Args:
            file_path: Path to the configuration file.

        Returns:
            A MazeConfig instance ready for maze generation.

        Raises:
            ConfigError: If the file cannot be read or contains
                invalid or incomplete configuration values.
        """
        raw_values: Dict[str, str] = cls._read_pairs(file_path)
        cls._check_required_keys(raw_values)
        cls._check_unknown_keys(raw_values)

        width: int = cls._parse_positive_int(raw_values["WIDTH"], "WIDTH")
        height: int = cls._parse_positive_int(raw_values["HEIGHT"], "HEIGHT")
        entry: Tuple[int, int] = cls._parse_coordinates(
            raw_values["ENTRY"],
            "ENTRY",
        )
        exit_pos: Tuple[int, int] = cls._parse_coordinates(
            raw_values["EXIT"],
            "EXIT",
        )
        output_file: str = cls._parse_output_file(
            raw_values["OUTPUT_FILE"],
            file_path,
        )
        perfect: bool = cls._parse_bool(raw_values["PERFECT"], "PERFECT")

        seed: Optional[int] = None
        if "SEED" in raw_values and raw_values["SEED"] != "":
            seed = cls._parse_int(raw_values["SEED"], "SEED")

        algorithm: Optional[str] = cls._parse_optional_text(
            raw_values.get("ALGORITHM")
        )
        display_mode: Optional[str] = cls._parse_optional_text(
            raw_values.get("DISPLAY_MODE")
        )

        cls._check_bounds(entry, width, height, "ENTRY")
        cls._check_bounds(exit_pos, width, height, "EXIT")

        if entry == exit_pos:
            raise ConfigError("ENTRY and EXIT must be different cells.")

        return MazeConfig(
            width=width,
            height=height,
            entry=entry,
            exit=exit_pos,
            output_file=output_file,
            perfect=perfect,
            seed=seed,
            algorithm=algorithm,
            display_mode=display_mode,
        )

    @classmethod
    def _read_pairs(cls, file_path: str) -> Dict[str, str]:
        """
        Read KEY=VALUE pairs from the configuration file.

        Blank lines and comment lines are ignored. Keys are normalized
        to uppercase so the parser behaves consistently.

        Args:
            file_path: Path to the configuration file.

        Returns:
            A dictionary containing raw string values.

        Raises:
            ConfigError: If the file cannot be read or a line is invalid.
        """
        data: Dict[str, str] = {}

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line_number, raw_line in enumerate(file, start=1):
                    line: str = raw_line.strip()

                    if not line or line.startswith("#"):
                        continue

                    if "=" not in line:
                        raise ConfigError(
                            f"Line {line_number}: expected KEY=VALUE."
                        )

                    key_part, value_part = line.split("=", 1)
                    key: str = key_part.strip().upper()
                    value: str = value_part.strip()

                    if key == "":
                        raise ConfigError(
                            f"Line {line_number}: configuration key is empty."
                        )

                    if value == "":
                        raise ConfigError(
                            f"Line {line_number}: value for '{key}' is empty."
                        )

                    if key in data:
                        raise ConfigError(
                            f"Line {line_number}: duplicate key '{key}'."
                        )

                    data[key] = value

        except FileNotFoundError as exc:
            raise ConfigError(
                f"Configuration file not found: {file_path}"
            ) from exc
        except PermissionError as exc:
            raise ConfigError(
                f"Permission denied while reading: {file_path}"
            ) from exc
        except IsADirectoryError as exc:
            raise ConfigError(
                f"Configuration path is a directory: {file_path}"
            ) from exc
        except OSError as exc:
            raise ConfigError(
                f"Unable to read configuration file: {file_path}"
            ) from exc

        return data

    @classmethod
    def _check_required_keys(cls, raw_values: Dict[str, str]) -> None:
        """
        Ensure all mandatory keys are present.

        Args:
            raw_values: Raw configuration mapping.

        Raises:
            ConfigError: If one or more mandatory keys are missing.
        """
        missing = cls.REQUIRED_KEYS - set(raw_values.keys())
        if missing:
            formatted: str = ", ".join(sorted(missing))
            raise ConfigError(
                f"Missing mandatory configuration keys: {formatted}."
            )

    @classmethod
    def _check_unknown_keys(cls, raw_values: Dict[str, str]) -> None:
        """
        Reject unsupported configuration keys.

        Args:
            raw_values: Raw configuration mapping.

        Raises:
            ConfigError: If an unknown key is found.
        """
        allowed = cls.REQUIRED_KEYS | cls.OPTIONAL_KEYS
        unknown = set(raw_values.keys()) - allowed

        if unknown:
            formatted: str = ", ".join(sorted(unknown))
            raise ConfigError(
                f"Unknown configuration keys: {formatted}."
            )

    @staticmethod
    def _parse_int(value: str, key: str) -> int:
        """
        Convert one text value to an integer.

        Args:
            value: Raw text value.
            key: Key name used in error messages.

        Returns:
            The converted integer.

        Raises:
            ConfigError: If the value is not a valid integer.
        """
        try:
            return int(value)
        except ValueError as exc:
            raise ConfigError(
                f"{key} must be an integer, got: {value!r}."
            ) from exc

    @classmethod
    def _parse_positive_int(cls, value: str, key: str) -> int:
        """
        Convert one text value to a strictly positive integer.

        Args:
            value: Raw text value.
            key: Key name used in error messages.

        Returns:
            The converted positive integer.

        Raises:
            ConfigError: If the value is invalid or not positive.
        """
        result: int = cls._parse_int(value, key)
        if result <= 0:
            raise ConfigError(f"{key} must be a positive integer.")
        return result

    @staticmethod
    def _parse_bool(value: str, key: str) -> bool:
        """
        Convert one text value to a boolean.

        Accepted values are True/False, yes/no, and 1/0,
        case-insensitively.

        Args:
            value: Raw text value.
            key: Key name used in error messages.

        Returns:
            The converted boolean.

        Raises:
            ConfigError: If the value is not recognized.
        """
        lowered: str = value.strip().lower()

        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False

        raise ConfigError(
            f"{key} must be a boolean value "
            f"(True/False, yes/no, or 1/0)."
        )

    @classmethod
    def _parse_coordinates(
        cls,
        value: str,
        key: str,
    ) -> Tuple[int, int]:
        """
        Convert one text value to a coordinate pair.

        Accepted forms are 'x,y' and '(x,y)'.

        Args:
            value: Raw coordinate text.
            key: Key name used in error messages.

        Returns:
            A tuple of two integers: (x, y).

        Raises:
            ConfigError: If the format or values are invalid.
        """
        cleaned: str = value.strip()

        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = cleaned[1:-1].strip()

        parts = [part.strip() for part in cleaned.split(",")]
        if len(parts) != 2:
            raise ConfigError(f"{key} must use the format x,y.")

        x: int = cls._parse_int(parts[0], key)
        y: int = cls._parse_int(parts[1], key)

        if x < 0 or y < 0:
            raise ConfigError(f"{key} coordinates must be non-negative.")

        return (x, y)

    @classmethod
    def _parse_output_file(cls, value: str, config_file: str) -> str:
        """
        Validate the output filename.

        Rules:
        - Must be a .txt file
        - Must not be 'requirements.txt'
        - Must not overwrite the config file itself
        - Must not be a directory or invalid name

        Args:
            value: Raw OUTPUT_FILE value.
            config_file: Path to the current configuration file.

        Returns:
            A cleaned output filename.

        Raises:
            ConfigError: If the output target is invalid.
        """
        cleaned: str = value.strip()
        if cleaned == "":
            raise ConfigError("OUTPUT_FILE cannot be empty.")

        output_path = Path(cleaned)
        config_path = Path(config_file)

        if output_path.name in {"", ".", ".."}:
            raise ConfigError("OUTPUT_FILE must be a valid filename.")

        if output_path.is_dir():
            raise ConfigError("OUTPUT_FILE cannot be a directory.")

        if output_path.resolve() == config_path.resolve():
            raise ConfigError(
                "OUTPUT_FILE cannot be the configuration file itself."
            )

        if output_path.name.lower() == "requirements.txt":
            raise ConfigError(
                "OUTPUT_FILE cannot be 'requirements.txt'."
            )

        if output_path.suffix.lower() != ".txt":
            raise ConfigError(
                "OUTPUT_FILE must end with '.txt'."
            )

        return cleaned

    @staticmethod
    def _parse_optional_text(value: Optional[str]) -> Optional[str]:
        """
        Normalize an optional text field.

        Args:
            value: Optional raw text.

        Returns:
            The stripped string, or None if missing or empty.
        """
        if value is None:
            return None

        cleaned: str = value.strip()
        if cleaned == "":
            return None

        return cleaned

    @staticmethod
    def _check_bounds(
        position: Tuple[int, int],
        width: int,
        height: int,
        label: str,
    ) -> None:
        """
        Ensure one coordinate pair is inside maze bounds.

        Args:
            position: Coordinate pair to validate.
            width: Maze width.
            height: Maze height.
            label: Position name for error reporting.

        Raises:
            ConfigError: If the coordinates are outside the maze.
        """
        x, y = position
        if not (0 <= x < width and 0 <= y < height):
            raise ConfigError(
                f"{label} is outside maze bounds "
                f"(width={width}, height={height})."
            )
