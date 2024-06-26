from __future__ import annotations

import dataclasses
import enum
import os
from pathlib import Path
from typing import Union, List, Iterable

import b2sdk  # type: ignore
from b2sdk.v1 import B2Api, Bucket, FileVersionInfo, InMemoryAccountInfo, FileVersion  # type: ignore

from server_manager.utils import file_to_b2_name, file_to_b2_dir

Pathy = Union[Path, str]


@enum.unique
class B2FileStatus(enum.Enum):
    MISSING = enum.auto()
    PRESENT = enum.auto()


@dataclasses.dataclass(frozen=True)
class FileWithB2Status:
    file: Path
    status: B2FileStatus


def b2_bucket_from_env() -> B2Api:
    b2_bucket_name = os.getenv("B2_BUCKET", "nearvanilla-files")
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    app_key_id = os.environ["B2_KEY_ID"]
    app_key = os.environ["B2_KEY"]
    b2_api.authorize_account("production", app_key_id, app_key)
    return b2_api.get_bucket_by_name(b2_bucket_name)


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
        b2_file_info(bucket, file, remote_prefix)
    except b2sdk.exception.FileNotPresent:
        return B2FileStatus.MISSING
    return B2FileStatus.PRESENT


# def b2_list_files(
#    bucket: Bucket, directory: str, remote_prefix: Pathy = Path("plugins/")
# ) -> Iterable[FileVersion]:
#    for file_version, _folder_name in bucket.ls(str(Path(remote_prefix) / directory)):
#        print
#
# def b2_list_plugin_files(
#    bucket: Bucket, file: Path, remote_prefix: Pathy = Path("plugins/")
# ):
#    return b2_list_files(bucket=bucket, directory=file_to_b2_dir(file), remote_prefix=remote_prefix)
#
def b2_get_all_files(
    bucket: Bucket, directory: str, remote_prefix: Pathy = Path("plugins/")
) -> Iterable[FileVersion]:
    for file_version, _folder_name in bucket.ls(str(remote_prefix), recursive=True):
        yield file_version
