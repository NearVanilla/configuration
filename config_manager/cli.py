#!/usr/bin/env python3
# vim: ft=python

from __future__ import annotations  # Postponed evaluation PEP-563

import os
from pathlib import Path

import click

from config_manager.cli_utils import error, info, is_dir_empty
from config_manager.gitwrapper import GitWrapper, WorkTree
from config_manager.substitutions import (
    commit_and_unsubstitute,
    substitute_tracked_and_commit,
)
from config_manager.utils import current_date


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
    for path in value:
        if ctx.obj.git.get_subworktree(Path(path)) is None:
            raise click.BadParameter(f"no such subworktree with path {path}")
    return value


path_argument = click.argument(
    "paths",
    type=click.Path(exists=True, path_type=Path, file_okay=False, resolve_path=True),
    callback=validate_path_is_subworktree,
    nargs=-1,  # Eat all args
)


@click.group()
@click.pass_context
def cli(ctx):
    """Manage configuration and plugins"""
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
def patch(ctx, paths):
    """Patch the config code, creating new commit"""
    for path in paths:
        swt = ctx.obj.git.get_subworktree(path)
        if swt is None:
            error(f"The subworktree at {path} does not exist!")
            return 1
        if not swt.is_initialized(ctx.obj.git):
            error(f"The subworktree at {path} is not initialized!")
            return 1
        info(f"Patching {path}...")
        substitute_tracked_and_commit(swt.git(ctx.obj.git))


@cli.command()
@click.option(
    "--commit-message",
    "--msg",
    type=str,
    required=False,
    default=lambda: f"Update live config {current_date()}",
    show_default="Update live config (current_date)",
)
@path_argument
@click.pass_context
def unpatch(ctx, paths, commit_message):
    """Revert previous config patch, applying new changes first"""
    for path in paths:
        swt = ctx.obj.git.get_subworktree(path)
        if swt is None:
            error(f"The subworktree at {path} does not exist!")
            return 1
        if not swt.is_initialized(ctx.obj.git):
            error(f"The subworktree at {path} is not initialized!")
            return 1
        info(f"Unpatching {path}...")
        commit_and_unsubstitute(swt.git(ctx.obj.git), commit_message)


@cli.command()
@path_argument
@click.pass_context
def status(ctx, paths):
    """Print status of SWTs"""
    if not paths:
        paths = [swt.path for swt in ctx.obj.git.get_all_subworktrees()]
    longest_path = get_longest_string_length(paths)
    for path in paths:
        swt = ctx.obj.git.get_subworktree(path)
        if swt is None:
            click.secho(f"{str(path):<{longest_path}}\tno such SWT")
            continue
        if not swt.is_initialized(ctx.obj.git):
            click.secho(f"{str(path):<{longest_path}}\tnot initialized")
            continue
        state = []
        git = swt.git(ctx.obj.git)
        if not git.repo.is_dirty():
            state.append("Clean")
        else:
            state.append("Dirty")
        if is_substituted(git):
            state.append("Substituted")
        click.secho(f"{str(path):<{longest_path}}\t{', '.join(state)}")


# @cli.group("plugin")
# def plugin_cmd():
#    """Manage plugins"""
#
# plugin_cmd.add_command()


# Main :)

if __name__ == "__main__":
    cli()
