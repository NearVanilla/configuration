#!/usr/bin/env python3
# vim: ft=python

import dataclasses
import sys
from pathlib import Path
from typing import Iterable

import click
import sh  # type: ignore

from server_manager.cli_utils import AliasedGroup, info
from server_manager.config import cli as config_cli
from server_manager.jars.cli import cli as jars_cli
from server_manager.synchronize.cli import cli as synchronize_cli

fgsh = sh(_in=sys.stdin, _out=sys.stdout, _err=sys.stderr)


def get_git_top_level(cwd=None) -> Path:
    result = sh.contrib.git("rev-parse", "--show-toplevel", _cwd=cwd)
    return Path(str(result))


def get_config_dir(start_dir=Path.cwd()) -> Path:
    subdir = "server-config"
    toplevel = start_dir
    config_dir = toplevel / subdir
    while not config_dir.exists():
        toplevel = get_git_top_level(toplevel.parent)
        config_dir = toplevel / subdir
    return config_dir


@dataclasses.dataclass(frozen=True)
class ManagementPaths:
    toplevel: Path
    config_dir: Path
    plugin_dir: Path
    script: Path


def get_management_paths(start_dir=Path.cwd()) -> ManagementPaths:
    config_dir = get_config_dir(start_dir=start_dir).resolve()
    toplevel = config_dir / ".."
    return ManagementPaths(
        toplevel=toplevel,
        config_dir=config_dir,
        plugin_dir=toplevel / "plugins",
        script=toplevel / "manage.py",
    )


@click.group(cls=AliasedGroup)
def cli():
    pass


cli.add_command(config_cli, name="config")
cli.add_command(synchronize_cli, name="synchronize")
cli.add_command(jars_cli, name="jars")


@cli.command()
@click.pass_context
def update_plugins(ctx: click.Context):
    """Download updated version of all plugins, upload them to B2 and update jar config"""
    management_paths = get_management_paths()
    top_dir = management_paths.toplevel
    topsh = fgsh(_cwd=top_dir)
    config_dir = management_paths.config_dir
    cwd = Path(".").resolve()
    if cwd.is_relative_to(config_dir):
        # CWD is a subdir - only update this one
        paths: Iterable[Path] = (cwd,)
    else:
        paths = config_dir.iterdir()

    info("Downloading plugin updates...")
    topsh.mineager.plugin.update()
    info("Uploading updated plugins to B2")
    topsh.python3(management_paths.script, "synchronize", "upload")
    for path in paths:
        info(f"Updating jar config in {path.name}")
        topsh.python3(management_paths.script, "jars", "update", path)


if __name__ == "__main__":
    cli()
