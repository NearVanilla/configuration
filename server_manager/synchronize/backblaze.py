#!/usr/bin/env python3

from __future__ import annotations

import dataclasses
import enum
import os
from pathlib import Path
from typing import Union

import b2sdk  # type: ignore
from b2sdk.v1 import B2Api, Bucket, FileVersionInfo, InMemoryAccountInfo  # type: ignore

from server_manager.synchronize.plugin import PluginInfo, get_plugin_info
from server_manager.synchronize.utils import sha1

Pathy = Union[Path, str]


@enum.unique
class B2FileStatus(enum.Enum):
    MISSING = enum.auto()
    UNCHANGED = enum.auto()
    CHANGED = enum.auto()


@dataclasses.dataclass(frozen=True)
class FileWithB2Status:
    file: Path
    status: B2FileStatus


def b2_bucket_from_env(authorize: bool = True) -> B2Api:
    b2_bucket_name = os.getenv("B2_BUCKET", "nearvanilla-files")
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    if authorize:  # TODO: Fix auth required
        app_key_id = os.environ["B2_KEY_ID"]
        app_key = os.environ["B2_KEY"]
        b2_api.authorize_account("production", app_key_id, app_key)
    return b2_api.get_bucket_by_name(b2_bucket_name)


def plugin_to_b2_name(plugin: PluginInfo) -> str:
    """Returns b2 name for give PluginYaml"""
    return f"{plugin.name}/{plugin.version}.jar"


def file_to_b2_name(file: Path) -> str:
    """Returns b2 name for given plugin file"""
    return plugin_to_b2_name(get_plugin_info(file))


def upload_plugin(
    bucket: Bucket, plugin: Path, remote_prefix: Pathy = Path("plugins/")
) -> FileVersionInfo:
    remote_name = str(Path(remote_prefix) / file_to_b2_name(plugin))
    bucket.upload_local_file(local_file=plugin, file_name=remote_name)


def b2_file_info(
    bucket: Bucket, plugin: Path, remote_prefix: Pathy = Path("plugins/")
) -> FileVersionInfo:
    remote_name = str(Path(remote_prefix) / file_to_b2_name(plugin))
    return bucket.get_file_info_by_name(remote_name)


def b2_file_status(
    bucket: Bucket, file: Path, remote_prefix: Pathy = Path("plugins/")
) -> B2FileStatus:
    try:
        file_info = b2_file_info(bucket, file, remote_prefix)
    except b2sdk.exception.FileNotPresent:
        return B2FileStatus.MISSING
    return (
        B2FileStatus.UNCHANGED
        if file_info.content_sha1 == sha1(file)
        else B2FileStatus.CHANGED
    )
