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


# Click stuff
# https://click.palletsprojects.com/en/8.0.x/advanced/#command-aliases
class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

    def resolve_command(self, ctx, args):
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args
