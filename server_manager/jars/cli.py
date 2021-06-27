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

    def save(self, config_file: Path) -> None:
        data = {
            "platform": self.platform.name.title(),
            "plugins": [
                {
                    "name": plugin.name,
                    "version": plugin.version,
                }
                for plugin in self.plugins
            ],
        }
        with config_file.open("w") as file:
            yaml.dump(data, file)


def get_config(path: Path) -> JarConfig:
    config_file = get_config_path(path)
    if not config_file.exists():
        click.echo("Config file does not exist!")
        raise click.BadArgumentUsage("Config file does not exist!")
    return JarConfig.load_config(config_file)


def get_config_path(path: Path) -> Path:
    return path / "jars.yaml"


def get_plugin_dir(path: Path, plugin: PluginInfo) -> Path:
    return path / "plugins" / f"{plugin.name}.jar"


server_path_argument = click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path, file_okay=False, resolve_path=True),
    default=Path(os.getcwd()),
)
updated_plugin_dir_option = click.option(
    "--plugin-dir",
    "--plugins",
    "-p",
    type=click.Path(exists=True, path_type=Path, file_okay=False, resolve_path=True),
    default=Path(os.getcwd()) / "plugins",
    help="Path to where updated plugins are.",
)


@click.group()
def cli():
    """Manage server jars"""


@cli.command()
@server_path_argument
def status(path: Path):
    """Check status of jars"""
    config = get_config(path)
    longest_plugin_name = get_longest_string_length(
        plugin.name for plugin in config.plugins
    )
    for plugin in config.plugins:
        local_file = get_plugin_dir(path, plugin)
        if not local_file.exists():
            click.echo(f"{plugin.name:<{longest_plugin_name}}\tMISSING")
            continue
        local_info = get_plugin_info(local_file)
        plugin_status = plugin.compare_to(local_info)
        click.echo(f"{plugin.name:<{longest_plugin_name}}\t{plugin_status}")


@cli.command()
@server_path_argument
def download(path: Path):
    """Download updates for all outdated and missing plugins"""
    config = get_config(path)
    plugins_to_update = []
    # Check if local version differs
    for plugin in config.plugins:
        local_file = get_plugin_dir(path, plugin)
        if not local_file.exists():
            plugins_to_update.append(plugin)
            continue
        local_info = get_plugin_info(local_file)
        plugin_status = plugin.compare_to(local_info)
        if plugin_status in (PluginComparison.OUTDATED, PluginComparison.CHANGED):
            plugins_to_update.append(plugin)
            continue
        assert plugin_status == PluginComparison.UP_TO_DATE
        # TODO: Confirm SHA1 to check for plugins which are in snapshots

    with click.progressbar(
        plugins_to_update,
        label="Downloading plugins",
        item_show_func=lambda x: str(x.name) if x else "",
    ) as bar:
        for plugin in bar:
            local_file = get_plugin_dir(path, plugin)
            download_plugin(plugin, local_file)


@cli.command()
@server_path_argument
@updated_plugin_dir_option
def update(path: Path, plugin_dir: Path):
    """Update config file with entries from updated plugin dir"""
    config = get_config(path)
    new_plugins = []
    for plugin in config.plugins:
        new_local_file = plugin_dir / f"{plugin.name}.jar"
        if not new_local_file.exists():
            click.echo(f"Unable to find updated plugin for {plugin.name}. Skipping.")
            new_plugins.append(plugin)
            continue
        new_plugin = get_plugin_info(new_local_file)
        compare_status = plugin.compare_to(new_plugin)
        if compare_status == PluginComparison.NEWER:
            click.echo(
                f"WARNING: {plugin.name} version {plugin.version} is newer than {new_plugin.version}. Skipping."
            )
            new_plugins.append(plugin)
            continue
        if compare_status == PluginComparison.OUTDATED:
            click.echo(
                f"Updating {plugin.name} from version {plugin.version} to {new_plugin.version}"
            )
        new_plugins.append(new_plugin)
    config_file = get_config_path(path)
    config.save(config_file)


@cli.command()
@server_path_argument
@click.argument(
    "platform",
    type=click.Choice([entry.name for entry in PluginPlatform]),
    callback=lambda c, p, v: PluginPlatform[v.upper()] if v else None,
    default=PluginPlatform.PAPER.name,
)
def new_config(path: Path, platform: PluginPlatform):
    """Create new config for platform"""
    config_file = get_config_path(path)
    if config_file.exists():
        click.echo("Config file exists already - aborting.")
        return 1
    config = JarConfig(platform=platform, plugins=[])
    config.save(config_file)
    return 0


@cli.command()
@server_path_argument
@click.argument(
    "plugins",
    type=click.Path(
        exists=True, path_type=Path, file_okay=True, dir_okay=False, resolve_path=True
    ),
    nargs=-1,  # Eat all args
)
def add_plugins(path: Path, plugins: List[Path]):
    """Add plugins to the config"""
    config = get_config(path)
    new_plugins = [get_plugin_info(plugin) for plugin in plugins]
    for new_plugin in new_plugins:
        if any(
            new_plugin.name == existing_plugin.name
            for existing_plugin in config.plugins
        ):
            click.echo(f"Can't add already exisitng plugin {new_plugin.name}")
            return 1
    config.plugins.extend(new_plugins)
    config.save(get_config_path(path))


if __name__ == "__main__":
    cli()
