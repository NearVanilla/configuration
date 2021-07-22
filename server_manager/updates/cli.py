#!/usr/bin/env python3
# vim: ft=python

from pathlib import Path
from typing import Iterable

import click

from server_manager.cli_utils import AliasedGroup, info
from server_manager.updates.utils import fgsh, get_management_paths


@click.group(cls=AliasedGroup)
def cli():
    pass


@cli.command()
def plugins():
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
