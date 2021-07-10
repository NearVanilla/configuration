#!/usr/bin/env python3
# vim: ft=python

from __future__ import annotations  # Postponed evaluation PEP-563

import dataclasses
import json
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Iterable, Optional, Set, Union

import git  # type: ignore

from server_manager.config.exceptions import *

Substitutions = Union[dict, None]

SUBWORKTREE_PATH = Path(".subworktrees.json")


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
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
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
        whitelisted_config_suffixes = {
            ".conf"
            ".properties",
            ".toml",
            ".txt",
            ".yaml",
            ".yml",
        }
        return tuple(
            file
            for file in self.list_tracked_files()
            if file.suffix in whitelisted_config_suffixes
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

    def get_all_subworktrees(self) -> tuple[WorkTree, ...]:
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

    def get_subworktree(self, path: Path) -> Optional[WorkTree]:
        path = Path(path).resolve()
        return next(
            (swt for swt in self.get_all_subworktrees() if swt.path.resolve() == path),
            None,
        )

    @require_clean_workspace
    def create_detached_empty_branch(self, name: str, message: str):
        with changed_reset_head(self._repo, git.Head(self._repo, f"refs/heads/{name}")):
            # GitPython is stupid and will throw errors when commiting on orphaned branch
            # https://github.com/gitpython-developers/GitPython/issues/615
            # https://stackoverflow.com/questions/47078961/create-an-orphan-branch-without-using-the-orphan-flag
            # https://github.com/gitpython-developers/GitPython/issues/633
            self._repo.git.commit("--message", message, "--allow-empty")
