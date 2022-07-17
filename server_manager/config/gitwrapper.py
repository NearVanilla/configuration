# vim: ft=python

from __future__ import annotations  # Postponed evaluation PEP-563

import dataclasses
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Iterable, Optional, Set, Union

import git  # type: ignore

from server_manager.config.exceptions import *

Substitutions = Union[dict, None]


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

    @classmethod
    def is_initialized(cls, path: Path) -> bool:
        try:
            cls(path)
            return True
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            return False

    @property
    def repo(self) -> git.Repo:
        return self._repo

    @property
    def path(self) -> Path:
        return self._path

    @property
    def working_tree_dir(self) -> Path:
        return Path(self.repo.working_tree_dir)

    def list_tracked_files(self, tree=None) -> Iterable[Path]:
        """Return list of tracked files relative to workdir"""
        if tree is None:
            tree = self._repo.tree()
        tracked = (
            Path(blob.abspath)
            for blob in tree.traverse(predicate=lambda item, depth: item.type == "blob")
        )
        return (file for file in tracked if file.exists())

    def all_config_tracked_files(self) -> Iterable[Path]:
        whitelisted_config_suffixes = {
            ".conf",
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

    @require_clean_workspace
    def create_detached_empty_branch(self, name: str, message: str):
        with changed_reset_head(self._repo, git.Head(self._repo, f"refs/heads/{name}")):
            # GitPython is stupid and will throw errors when commiting on orphaned branch
            # https://github.com/gitpython-developers/GitPython/issues/615
            # https://stackoverflow.com/questions/47078961/create-an-orphan-branch-without-using-the-orphan-flag
            # https://github.com/gitpython-developers/GitPython/issues/633
            self._repo.git.commit("--message", message, "--allow-empty")
