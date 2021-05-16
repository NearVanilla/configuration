#!/usr/bin/env python3
# vim: ft=python

import datetime
import os
from functools import wraps
from pathlib import Path
from typing import Iterable, Union

import click
import jinja2
import sh
import git

Substitutions = Union[dict, None]

COMMIT_SUBSTITUTED = "[SUBST]"
COMMIT_CHANGED = "[CHNG]"
CONFIG_PATH = Path("./config")


@click.group()
def cli():
    pass


@cli.command()
def patch():
    """Patch the config code, creating new commit"""


@cli.command()
def unpatch():
    """Revert previous config patch, applying new changes first"""


# Helper printers


def info(msg: str) -> None:
    click.secho(f"INFO: {msg}", fg="green", err=True)


def error(msg: str) -> None:
    click.secho(f"ERROR: {msg}", fg="red", err=True)


def debug(msg: str) -> None:
    # TODO: Check if should run debug
    click.secho(f"DEBUG: {msg}", fg="cyan", err=True)


# Exceptions


class ManageException(Exception):
    pass


class DirtyWorkTreeException(ManageException):
    """WorkTree is dirty, but it's required to be empty"""

    def __init__(self):
        super().__init__("Worktree is modified")


class OutsideWorkTreeException(ManageException):
    """Is outside of worktree"""

    def __init__(self):
        super().__init__("Outside of worktree")


class WorkTreeAlreadySubstitutedException(ManageException):
    """Worktree has already been substituted"""

    def __init__(self):
        super().__init__("Worktree already substituted")


# Helpers
def require_clean_workspace(fun):
    @wraps(fun)
    def wrapper(self, *args, **kwargs):
        if not self.is_worktree_clean():
            raise DirtyWorkTreeException()
        return fun(self, *args, **kwargs)

    return wrapper


class GitWrapper:
    def __init__(self, path: Union[str, Path]):
        self._path = CONFIG_PATH / Path(path)
        self._git = git.Repo(path)
        self._gitsh = sh.git.bake(_cwd=self._path)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self._path})"

    def all_config_tracked_files(self) -> Iterable[Path]:
        blacklisted_config_suffixes = {".sh"}
        result = self._gitsh("ls-tree", "-r", "HEAD", "--name-only", "--full-name")
        file_paths = result.stdout.decode("utf-8").strip().split("\n")
        files = (self._path.joinpath(fpath) for fpath in file_paths)
        return tuple(
            file
            for file in files
            if file.suffix not in blacklisted_config_suffixes and file.is_file()
        )

    def is_worktree_clean(self) -> bool:
        return not self._git.is_dirty()

    def _get_commit_field(self, commit: str, field_format: str) -> str:
        res = self._gitsh("rev-list", commit, n=1, format=field_format)
        output = res.stdout.decode("utf-8").strip().split("\n")
        # We expect 2 lines - one with `commit <SHA>` and second with our output
        assert (
            len(output) == 2
        ), f"Expected to get 2 lines of output from rev-list, got instead: {output}"
        # TODO: Maybe should always return all but first line?
        return output[1]

    def get_commit_subject(self, commit: str = "HEAD") -> str:
        return self._get_commit_field(commit=commit, field_format="%s")

    def get_commit_sha(self, commit: str = "HEAD") -> str:
        return self._get_commit_field(commit=commit, field_format="%H")

    def commit(self, *args, **kwargs) -> None:
        self._gitsh.commit(*args, **kwargs)

    def get_all_submodule_paths(self) -> Iterable[Path]:
        # TODO: Replace with getting submodule status?
        # The format is:
        # <STATUS_CHAR><SHA> <PATH> (<REF>)
        # <STATUS_CHAR> can be a space
        paths = set()
        for line in self._gitsh.submodule.status():
            paths.add(' '.join(line[1:].split(' ')[1:-1]))


def current_date() -> str:
    return datetime.datetime.now().isoformat()


# Main commands


def substitute_placeholders(
    files: Iterable[Path], substitutions: Substitutions = None, environment: dict = {}
) -> None:
    if substitutions is None:
        substitutions = os.environ
    for file in files:
        with file.open("r+") as f:
            original = f.read()
            template = jinja2.Template(original, **environment)
            rendered = template.render(**substitutions)
            if rendered != original:
                f.seek(0)
                f.truncate()
                f.write(rendered)


@require_clean_workspace
def substitute_tracked_placeholders(
    git: GitWrapper, substitutions: Substitutions = None
) -> None:
    if git.get_commit_subject("HEAD").startswith(COMMIT_SUBSTITUTED):
        raise WorkTreeAlreadySubstitutedException()
    substitute_placeholders(git.all_config_tracked_files(), substitutions)


def substitute_tracked_and_commit(
    git: GitWrapper, substitutions: Substitutions = None
) -> None:
    substitute_tracked_placeholders(git, substitutions)
    if not git.is_worktree_clean():
        git.commit(all=True, message=f"{COMMIT_SUBSTITUTED} {current_date()}")


# Main :)

if __name__ == "__main__":
    cli()
