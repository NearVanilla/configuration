#!/usr/bin/env python3

from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import List

import click
import yaml

from server_manager.cli_utils import get_longest_string_length
from server_manager.jars.utils import download_plugin
from server_manager.plugin import (
    PluginComparison,
    PluginInfo,
    PluginPlatform,
    get_plugin_info,
)


@dataclasses.dataclass(frozen=True)
class JarConfig:
    platform: PluginPlatform
    plugins: List[PluginInfo]

    @classmethod
    def load_config(cls, config_file: Path) -> JarConfig:
        with config_file.open("r") as file:
            data = yaml.safe_load(file)
        assert isinstance(data, dict), "Invalid config"
        platform_string = data.get("platform")
        assert isinstance(platform_string, str)
        platform = PluginPlatform[platform_string.upper()]
        plugin_list = data.get("plugins")
        assert isinstance(plugin_list, list), "Invalid config"
        plugins = [PluginInfo.from_data(plugin, platform) for plugin in plugin_list]
        return cls(platform, plugins)


@dataclasses.dataclass(frozen=True)
class CliContext:
    root_dir: Path
    config: JarConfig


@click.group()
@click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path, file_okay=False, resolve_path=True),
    default=Path(os.getcwd()),
)
@click.pass_context
def cli(ctx, path):
    """Manage server jars"""
    config_file = path / "jars.yaml"
    if not config_file.exists():
        click.echo("Config file does not exist!")
        return 1
    ctx.obj = CliContext(root_dir=path, config=JarConfig.load_config(config_file))


@cli.command()
@click.pass_context
def status(ctx):
    """Check status of jars"""
    longest_plugin_name = get_longest_string_length(
        plugin.name for plugin in ctx.obj.config.plugins
    )
    for plugin in ctx.obj.config.plugins:
        local_file = ctx.obj.root_dir / "plugins" / f"{plugin.name}.jar"
        if not local_file.exists():
            click.echo(f"{plugin.name:<{longest_plugin_name}}\tMISSING")
            continue
        local_info = get_plugin_info(local_file)
        plugin_status = plugin.compare_to(local_info)
        click.echo(f"{plugin.name:<{longest_plugin_name}}\t{plugin_status}")


@cli.command()
@click.pass_context
def download(ctx):
    """Download updates for all outdated and missing plugins"""
    plugins_dir = ctx.obj.root_dir / "plugins"
    plugins_to_update = []
    for plugin in ctx.obj.config.plugins:
        local_file = plugins_dir / f"{plugin.name}.jar"
        if not local_file.exists():
            plugins_to_update.append(plugin)
            continue
        local_info = get_plugin_info(local_file)
        plugin_status = plugin.compare_to(local_info)
        if plugin_status == PluginComparison.OUTDATED:
            plugins_to_update.append(plugin)

    with click.progressbar(
        plugins_to_update,
        label="Downloading plugins",
        item_show_func=lambda x: str(x.name) if x else "",
    ) as bar:
        for plugin in bar:
            local_file = plugins_dir / f"{plugin.name}.jar"
            download_plugin(plugin, local_file)


if __name__ == "__main__":
    cli()
