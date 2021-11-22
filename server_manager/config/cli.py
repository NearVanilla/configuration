#!/usr/bin/env python3
# vim: ft=python

from __future__ import annotations  # Postponed evaluation PEP-563

import os
from pathlib import Path

import click

from server_manager.cli_utils import (
    AliasedGroup,
    error,
    get_longest_string_length,
    info,
    is_dir_empty,
)
from server_manager.config.gitwrapper import GitWrapper
from server_manager.config.substitutions import (
    commit_and_unsubstitute,
    is_substituted,
    substitute_tracked_and_commit,
)
from server_manager.config.utils import current_date


def current_dir_git_wrapper() -> GitWrapper:
    path = os.getcwd()
    if not GitWrapper.is_initialized(path):
        raise click.BadParameter(f"no git repo at current directory - {path}")
    return GitWrapper(path)


def validate_ref_not_exists(ctx, param, value):
    try:
        # pylint: disable=pointless-statement
        current_dir_git_wrapper().repo.references[value]
        raise click.BadParameter(f"reference with name {value} exists already")
    except IndexError:
        return value


def validate_path_is_git_worktree(ctx, param, value):

    for path in value:
        if not GitWrapper.is_initialized(path):
            raise click.BadParameter(f"no git repo at {path}")
        gw = GitWrapper(path)
        gw_worktree = gw.working_tree_dir
        if gw_worktree != path:
            raise click.BadParameter(
                f"passed path {path}, which is not root of repo at {gw_worktree}"
            )
    return value


paths_argument = click.argument(
    "paths",
    type=click.Path(exists=True, path_type=Path, file_okay=False, resolve_path=True),
    callback=validate_path_is_git_worktree,
    nargs=-1,  # Eat all args
)


@click.group(cls=AliasedGroup)
def cli():
    """Manage configuration and plugins"""


@cli.command()
@click.argument("revision", type=str, callback=validate_ref_not_exists)
@click.argument("message", type=str, required=False)
def new_server(revision, message):
    """Create new REVISION, with empty commit with MESSAGE"""
    current_dir_git_wrapper().create_detached_empty_branch(
        revision, message or f"Initial commit for {revision}"
    )


@cli.command()
@paths_argument
def patch(paths):
    """Patch the config code, creating new commit"""
    for path in paths:
        info(f"Patching {path}...")
        substitute_tracked_and_commit(GitWrapper(path))


@cli.command()
@click.option(
    "--commit-message",
    "--msg",
    type=str,
    required=False,
    default=lambda: f"Update live config {current_date()}",
    show_default="Update live config (current_date)",
)
@paths_argument
def unpatch(paths, commit_message):
    """Revert previous config patch, applying new changes first"""
    for path in paths:
        info(f"Unpatching {path}...")
        commit_and_unsubstitute(GitWrapper(path), commit_message)


@cli.command()
@paths_argument
def status(paths):
    """Print git repo status"""
    longest_path = get_longest_string_length(paths)
    for path in paths:
        if not GitWrapper.is_initialized(path):
            click.secho(f"{str(path):<{longest_path}}\tno such repo")
            continue
        state = []
        git = GitWrapper(path)
        if not git.repo.is_dirty():
            state.append("Clean")
        else:
            state.append("Dirty")
        if is_substituted(git):
            state.append("Substituted")
        click.secho(f"{str(path):<{longest_path}}\t{', '.join(state)}")


# Main :)

if __name__ == "__main__":
    cli()
