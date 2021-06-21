# vim: ft=python

from pathlib import Path
from typing import Iterable

import click


def is_dir_empty(path: Path) -> bool:
    """Checks whether directory is empty"""
    return not any(path.iterdir())


def get_longest_string_length(strings: Iterable[str]) -> int:
    """
    Gets the longest stringy value of the argument contents

    >>> get_longest_string_length([])
    0
    >>> get_longest_string_length(["a"])
    1
    >>> get_longest_string_length(["abcd"])
    4
    >>> get_longest_string_length(["abcd", "h"])
    4
    >>> get_longest_string_length(["h", "ghij"])
    4
    >>> get_longest_string_length(["abcd", "h", "ghijk"])
    5
    >>> from pathlib import Path
    >>> get_longest_string_length([Path("x")])
    1
    >>> get_longest_string_length([Path("xyz")])
    3
    """
    longest_string = 0
    for string in strings:
        stringlen = len(str(string))
        longest_string = stringlen if stringlen > longest_string else longest_string
    return longest_string


# Helper printers


def info(msg: str) -> None:
    click.secho(f"INFO: {msg}", fg="green", err=True)


def error(msg: str) -> None:
    click.secho(f"ERROR: {msg}", fg="red", err=True)


def debug(msg: str) -> None:
    # TODO: Check if should run debug
    click.secho(f"DEBUG: {msg}", fg="cyan", err=True)
