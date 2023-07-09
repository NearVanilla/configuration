#!/usr/bin/env python3
# vim: ft=python

import dataclasses
import sys
from pathlib import Path

import sh  # type: ignore

fgsh = sh.bake(_in=sys.stdin, _out=sys.stdout, _err=sys.stderr)


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
