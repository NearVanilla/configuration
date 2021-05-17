#!/usr/bin/env python3
# vim: ft=python

from __future__ import annotations  # Postponed evaluation PEP-563

import datetime
import os
from functools import wraps
from pathlib import Path
from typing import Iterable, Union

import click
import git
import jinja2

Substitutions = Union[dict, None]

COMMIT_SUBSTITUTED = "[SUBST]"
COMMIT_CHANGED = "[CHNG]"
CONFIG_PATH = Path("./config")


class ConfContext:
    def __init__(self):
        self.git = GitWrapper(os.getcwd())


pass_conf = click.make_pass_decorator(ConfContext)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = ConfContext()


@cli.command()
@click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path, file_okay=False, resolve_path=True),
)
@pass_conf
def patch(conf, path):
    """Patch the config code, creating new commit"""
    click.secho(str(path))
    click.secho("Submodules:")
    click.secho("\n".join(s.path for s in conf.git.get_all_submodules()))
    sub = next(
        (s for s in conf.git.get_all_submodules() if s.path.absolute() == path), None
    )
    if sub is None:
        raise click.BadParameter("no matching submodule")
    info(sub.get_commit_subject())


@cli.command()
@pass_conf
def unpatch(conf):
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
        self._path = Path(path)
        self._git = git.Repo(self._path)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self._path})"

    @property
    def git(self) -> git.Repo:
        return self._git

    @property
    def path(self) -> Path:
        return self._path

    def list_tracked_files(self, tree=None) -> Iterable[Path]:
        """Return list of tracked files relative to workdir"""
        if tree is None:
            tree = self._git.tree()
        return (
            Path(blob.abspath)
            for blob in tree.traverse(predicate=lambda item, depth: item.type == "blob")
        )

    def all_config_tracked_files(self) -> Iterable[Path]:
        blacklisted_config_suffixes = {".sh"}
        return tuple(
            file
            for file in self.list_tracked_files()
            if file.suffix not in blacklisted_config_suffixes
        )

    def is_worktree_clean(self) -> bool:
        return not self._git.is_dirty()

    def get_commit_subject(self, commit: str = "HEAD") -> str:
        return self._git.commit(commit).summary

    def get_commit_sha(self, commit: str = "HEAD") -> str:
        return self._git.commit(commit).summary.hexsha

    def stage_all_tracked(self) -> None:
        self._git.index.add(str(p) for p in self.list_tracked_files())

    def commit(self, message) -> None:
        self._git.index.commit(message)

    def get_all_submodules(self) -> Iterable[GitWrapper]:
        return {GitWrapper(sm.abspath) for sm in self._git.submodules}


def current_date() -> str:
    return datetime.datetime.now().isoformat()


def path_to_branch(path: Path) -> str:
    """
    Resolve relative path and convert it into branch name.

    >>> from pathlib import Path
    >>> path_to_branch(Path('./some/path'))
    'some_path'
    >>> path_to_branch(Path('config/survival/'))
    'config_survival'
    """
    rel_path = path.absolute().relative_to(Path(".").absolute())
    return str(rel_path).replace("/", "_")


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
        git.stage_all_tracked()
        git.commit(message=f"{COMMIT_SUBSTITUTED} {current_date()}")


# Main :)

if __name__ == "__main__":
    cli()
