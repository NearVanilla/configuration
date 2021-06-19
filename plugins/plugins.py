#!/usr/bin/env python3

from __future__ import annotations

import dataclasses
import enum
import hashlib
import os
from pathlib import Path
from typing import Any, List, Union
from zipfile import ZipFile

import b2sdk  # type: ignore
import click
import yaml
from b2sdk.v1 import B2Api, Bucket, FileVersionInfo, InMemoryAccountInfo  # type: ignore

Pathy = Union[Path, str]


@enum.unique
class PluginPlatform(enum.Enum):
    PAPER = enum.auto()
    VELOCITY = enum.auto()


@dataclasses.dataclass(frozen=True)
class PluginInfo:
    name: str
    version: str
    platform: PluginPlatform
    raw: dict

    @classmethod
    def from_data(cls, data: dict, platform: PluginPlatform) -> PluginInfo:
        return cls(
            name=data["name"], version=data["version"], platform=platform, raw=data
        )


@enum.unique
class B2FileStatus(enum.Enum):
    MISSING = enum.auto()
    UNCHANGED = enum.auto()
    CHANGED = enum.auto()


@dataclasses.dataclass(frozen=True)
class FileWithB2Status:
    file: Path
    status: B2FileStatus


def get_paper_plugin_info(file: Path) -> PluginInfo:
    datafile = "plugin.yml"
    if not file.exists():
        raise FileNotExistentException(file)
    with ZipFile(file) as zipfile:
        try:
            zipfile.getinfo(datafile)
        except KeyError as e:
            raise NotAPaperPluginException(
                f"{file} does not contain {datafile}!"
            ) from e
        with zipfile.open(datafile) as plug:
            data = yaml.safe_load(plug)
        return PluginInfo.from_data(data=data, platform=PluginPlatform.PAPER)


def get_velocity_plugin_info(file: Path) -> PluginInfo:
    datafile = "velocity-plugin.json"
    if not file.exists():
        raise FileNotExistentException(file)
    with ZipFile(file) as zipfile:
        try:
            zipfile.getinfo(datafile)
        except KeyError as e:
            raise NotAVelocityPluginException(
                f"{file} does not contain {datafile}!"
            ) from e
        with zipfile.open(datafile) as plug:
            data = yaml.safe_load(plug)
        return PluginInfo.from_data(data=data, platform=PluginPlatform.VELOCITY)


def get_plugin_info(file: Path) -> PluginInfo:
    if not file.exists():
        raise FileNotExistentException(file)

    try:
        return get_paper_plugin_info(file)
    except NotAPaperPluginException:
        return get_velocity_plugin_info(file)


class PluginException(Exception):
    pass


class NotAPluginException(PluginException):
    pass


class NotAPaperPluginException(NotAPluginException):
    pass


class NotAVelocityPluginException(NotAPluginException):
    pass


class FileNotExistentException(PluginException):
    def __init__(self, file: Path):
        super().__init__(f"File {file} does not exist")


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


@dataclasses.dataclass(frozen=True)
class CliContext:
    plugin_dir: Path
    remote_prefix: Path


@click.group()
@click.option(
    "--plugin-dir",
    "--plugins",
    "-p",
    type=click.Path(exists=True, path_type=Path, file_okay=False, resolve_path=True),
    default=Path("plugins/"),
    help="Directory with plugins",
)
@click.option(
    "--remote-prefix",
    "--prefix",
    "-r",
    type=click.Path(path_type=Path, resolve_path=False),
    default=Path("plugins/"),
    help="Remote plugin dir prefix",
)
@click.pass_context
def cli(ctx, plugin_dir: Path, remote_prefix: Path):
    ctx.obj = CliContext(plugin_dir, remote_prefix)


@cli.command()
@click.pass_context
def status(ctx):
    bucket = b2_bucket_from_env()
    for file in ctx.obj.plugin_dir.glob("*.jar"):
        filestatus = b2_file_status(bucket, file, ctx.obj.remote_prefix)
        click.echo(f"File {file.relative_to(Path('.').resolve())} is {filestatus.name}")


@cli.command()
@click.option("--dry-run", is_flag=True)
@click.pass_context
def upload(ctx, dry_run: bool):
    bucket = b2_bucket_from_env()
    files_to_upload: List[Path] = []
    plugin_dir: Path = ctx.obj.plugin_dir
    with click.progressbar(
        plugin_dir.glob("*.jar"),
        label="Checking plugins",
        item_show_func=lambda x: str(x.name) if x else "",
    ) as bar:
        for file in bar:
            status = b2_file_status(bucket, file, ctx.obj.remote_prefix)
            if status != B2FileStatus.UNCHANGED:
                files_to_upload.append(file)
    if not files_to_upload:
        click.echo("Nothing to upload")
        return
    if dry_run:
        for file in files_to_upload:
            click.echo(f"Would upload {file.name}")
        return
    with click.progressbar(
        files_to_upload,
        label="Uploading plugins",
        item_show_func=lambda x: str(x.name) if x else "",
    ) as bar:
        for file in bar:
            upload_plugin(bucket, file, ctx.obj.remote_prefix)


if __name__ == "__main__":
    cli()
