#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from server_manager.plugin import PluginInfo, get_plugin_info

URL_INVALID_MATCHER = re.compile(r"[^\w_.-]")


def sanitize_url_part(url_part: str, replacement: str = "_") -> str:
    # TODO: Maybe use https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote
    return URL_INVALID_MATCHER.sub(replacement, url_part)


def plugin_to_b2_name(plugin: PluginInfo) -> str:
    """Returns b2 name for give PluginYaml"""
    # We need to sanitize the version to be url-compliant.
    # B2 can store those files just fine, but can't get them over http
    return f"{sanitize_url_part(plugin.name)}/{sanitize_url_part(plugin.version)}.jar"


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
