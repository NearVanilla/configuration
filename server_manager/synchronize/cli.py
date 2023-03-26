#!/usr/bin/env python3

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import List

import click

from server_manager.cli_utils import AliasedGroup
from server_manager.synchronize.backblaze import (
    B2FileStatus,
    b2_bucket_from_env,
    b2_file_status,
    upload_plugin,
    b2_get_all_files,
)
from server_manager.utils import file_to_b2_dir


@dataclasses.dataclass(frozen=True)
class CliContext:
    plugin_dir: Path
    remote_prefix: Path


@click.group(cls=AliasedGroup)
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
    """Synchronize plugins with backblaze"""
    ctx.obj = CliContext(plugin_dir, remote_prefix)


@cli.command()
@click.pass_context
def status(ctx):
    bucket = b2_bucket_from_env()
    for file in ctx.obj.plugin_dir.glob("*.jar"):
        filestatus = b2_file_status(bucket, file, ctx.obj.remote_prefix)
        click.echo(f"File {file.name} is {filestatus.name}")


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
            file_status = b2_file_status(bucket, file, ctx.obj.remote_prefix)
            if file_status != B2FileStatus.PRESENT:
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


@cli.command()
@click.option("--dry-run", is_flag=True)
@click.pass_context
def download(ctx, dry_run: bool):
    bucket = b2_bucket_from_env()
    files_to_download: List[Path] = []
    plugin_dir: Path = ctx.obj.plugin_dir
    remote_files = sorted(
        b2_get_all_files(bucket, ctx.obj.remote_prefix),
        key=lambda f: f.upload_timestamp,
    )
    newest_remote_file = {}
    # TODO: Support one plugin name having different plugins for velocity/paper
    for rfile in remote_files:
        rfile_path = Path(rfile.file_name)
        # rfile_name = rfile_path.name
        # assert rfile_name.endswith(".jar"), rfile_name
        # version = rfile_name.rstrip(".jar")
        plugin_name = rfile_path.parent.name
        newest_remote_file[plugin_name] = rfile
    local_files = {file_to_b2_dir(path): path for path in plugin_dir.glob("*.jar")}
    to_download = {}
    for remote_name, remote_file in newest_remote_file.items():
        local_file_path = local_files.get(remote_name)
        if local_file_path:
            if local_file_path.stat().st_mtime >= remote_file.upload_timestamp:
                # We have newer version
                continue
            to_download[local_file_path] = remote_file
        else:
            to_download[plugin_dir / f"{remote_name}.jar"] = remote_file

    if not to_download:
        click.echo("Nothing to download")
        return
    if dry_run:
        for file in to_download:
            click.echo(f"Would download {file}")
        return
    with click.progressbar(
        to_download.items(),
        label="Downloading plugins",
        item_show_func=lambda x: str(x[0].name) if x else "",
    ) as bar:
        for path, info in bar:
            info.download().save_to(path)


if __name__ == "__main__":
    cli()
