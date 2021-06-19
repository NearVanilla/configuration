#!/usr/bin/env python3

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import List

import click

from server_manager.plugins.backblaze import (
    B2FileStatus,
    b2_bucket_from_env,
    b2_file_status,
    upload_plugin,
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
    """Synchronize plugins with backblaze"""
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
