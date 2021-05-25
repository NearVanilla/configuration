#!/usr/bin/env python3
# vim: ft=python

from __future__ import annotations  # Postponed evaluation PEP-563

import dataclasses
import datetime
import json
import os
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Iterable, Set, Union

import click
import git
import jinja2

Substitutions = Union[dict, None]

COMMIT_SUBSTITUTED = "[SUBST]"
COMMIT_CHANGED = "[CHNG]"
SUBWORKTREE_PATH = Path(".subworktrees.json")


class ConfContext:
    def __init__(self):
        self.git = GitWrapper(os.getcwd())


class NonEmptySubworktreeDestinationError(click.UsageError):
    pass


def validate_ref_not_exists(ctx, param, value):
    try:
        ctx.obj.git.repo.references[value]
        raise click.BadParameter(f"reference with name {value} exists already")
    except IndexError:
        return value


def validate_path_is_subworktree(ctx, param, value):
    if (
        next(
            (
                swt
                for swt in ctx.obj.git.repo.get_all_subworktrees()
                if swt.path == Path(value)
            ),
            None,
        )
        is None
    ):
        raise click.BadParameter(f"no such subworktree with path {value}")
    return value


def is_dir_empty(path: Path) -> bool:
    """Checks whether directory is empty"""
    return not any(path.iterdir())


path_argument = click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path, file_okay=False, resolve_path=True),
    callback=validate_path_is_subworktree,
)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = ConfContext()


@cli.command()
@click.argument("path", type=click.Path(path_type=Path))
@click.argument("revision", type=str, callback=validate_ref_not_exists)
@click.argument("message", type=str, required=False)
@click.pass_context
def new_subworktree(ctx, path, revision, message):
    """Create new REVISION, with empty commit with MESSAGE, and configure it to mount under PATH"""
    worktree = WorkTree(path, revision)
    ctx.obj.git.create_detached_empty_branch(
        revision, message or f"Initial commit for {revision}"
    )
    ctx.obj.git.add_subworktree(worktree)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize all subworktrees"""
    for subworktree in ctx.obj.git.get_all_subworktrees():
        if not subworktree.path.exists() or is_dir_empty(subworktree.path):
            click.echo(f"Initializing subworktree {subworktree}")
            subworktree.init(ctx.obj.git)
        else:
            if subworktree.is_initialized(ctx.obj.git):
                click.echo(f"Skipping already initialized subworktree {subworktree}")
            else:
                raise NonEmptySubworktreeDestinationError(
                    f"Unable to initialize subworktree at path {subworktree.path} since it exists, is not empty and not an existing subworktree"
                )


@cli.command()
@path_argument
@click.pass_context
def patch(ctx, path):
    """Patch the config code, creating new commit"""
    sub = next(
        (s for s in ctx.obj.git.get_all_submodules() if s.path.absolute() == path), None
    )
    if sub is None:
        raise click.BadParameter("no matching submodule")
    info(sub.get_commit_subject())


@cli.command()
@path_argument
@click.pass_context
def unpatch(ctx):
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


class RefNotExistsError(ValueError):
    def __init__(self, ref):
        super().__init__(f"Reference named '{ref}' does not exist")


# Helpers
@dataclasses.dataclass(frozen=True)
class WorkTree:
    path: Path
    revision: str

    def __post_init__(self):
        object.__setattr__(self, "path", Path(self.path))

    def init(self, parent: GitWrapper) -> GitWrapper:
        parent.repo.git.worktree("add", self.path, self.revision)
        return self.git(parent)

    def git(self, parent: GitWrapper) -> GitWrapper:
        return GitWrapper(parent.working_tree_dir / self.path)

    def is_initialized(self, parent: GitWrapper) -> bool:
        try:
            self.git(parent)
            return True
        except git.InvalidGitRepositoryError:
            return False


class WorkTreeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, Path):
            return str(obj)
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


@contextmanager
def changed_reset_head(repo: git.Repo, head: git.Head):
    previous_ref = repo.head.reference
    if repo.is_dirty():
        raise DirtyWorkTreeException()
    try:
        repo.head.reference = head
        repo.head.reset()
        yield
    finally:
        repo.head.reference = previous_ref
        repo.head.reset()


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
        self._repo = git.Repo(self._path)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self._path})"

    @property
    def repo(self) -> git.Repo:
        return self._repo

    @property
    def path(self) -> Path:
        return self._path

    @property
    def working_tree_dir(self) -> Path:
        return Path(self.repo.working_tree_dir)

    @property
    def _subworktree_file(self) -> Path:
        return self.working_tree_dir / SUBWORKTREE_PATH

    def list_tracked_files(self, tree=None) -> Iterable[Path]:
        """Return list of tracked files relative to workdir"""
        if tree is None:
            tree = self._repo.tree()
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
        return not self._repo.is_dirty()

    def get_commit_subject(self, commit: str = "HEAD") -> str:
        return self._repo.commit(commit).summary

    def get_commit_sha(self, commit: str = "HEAD") -> str:
        return self._repo.commit(commit).hexsha

    def stage_all_tracked(self) -> None:
        self._repo.index.add(str(p) for p in self.list_tracked_files())

    def commit(self, message) -> None:
        self._repo.index.commit(message)

    def get_reference_names(self) -> Set[str]:
        return {ref.name for ref in self._repo.references}

    def get_all_subworktrees(self) -> Iterable[WorkTree]:
        if not self._subworktree_file.exists():
            return tuple()
        with self._subworktree_file.open("r") as file:
            return tuple(WorkTree(**swt) for swt in json.load(file))

    def add_subworktree(self, worktree: WorkTree):
        worktrees = self.get_all_subworktrees()
        paths = set(w.path for w in worktrees)
        if worktree.path in paths:
            raise ValueError(f"SubWorkTree already registered at path: {worktree.path}")
        if worktree.revision not in self.get_reference_names():
            raise RefNotExistsError(worktree.revision)
        with self._subworktree_file.open("w") as file:
            json.dump(worktrees + (worktree,), file, indent=2, cls=WorkTreeEncoder)

    @require_clean_workspace
    def create_detached_empty_branch(self, name: str, message: str):
        with changed_reset_head(self._repo, git.Head(self._repo, f"refs/heads/{name}")):
            # GitPython is stupid and will throw errors when commiting on orphaned branch
            # https://github.com/gitpython-developers/GitPython/issues/615
            # https://stackoverflow.com/questions/47078961/create-an-orphan-branch-without-using-the-orphan-flag
            # https://github.com/gitpython-developers/GitPython/issues/633
            self._repo.git.commit("--message", message, "--allow-empty")


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
