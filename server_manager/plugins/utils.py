#!/usr/bin/env python3

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from server_manager.plugins.plugin import PluginInfo, get_plugin_info


def plugin_to_b2_name(plugin: PluginInfo) -> str:
    """Returns b2 name for give PluginYaml"""
    return f"{plugin.name}/{plugin.version}.jar"


def file_to_b2_name(file: Path) -> str:
    """Returns b2 name for given plugin file"""
    return plugin_to_b2_name(get_plugin_info(file))


def hash_file(file: Path, checksum: Any) -> Any:
    """Update checksum with file chunks"""
    with file.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            checksum.update(chunk)
    return checksum


def md5(file: Path) -> str:
    """Calculate MD5 checksum of file"""
    hash_md5 = hashlib.md5()
    return hash_file(file, hash_md5).hexdigest()


def sha1(file: Path) -> str:
    """Calculate sha1 checksum of file"""
    hash_sha1 = hashlib.sha1()
    return hash_file(file, hash_sha1).hexdigest()
