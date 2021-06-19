#!/usr/bin/env python3
# vim: ft=python

import click

from server_manager.config import cli as config_cli
from server_manager.plugins.cli import cli as plugins_cli


@click.group()
def cli():
    pass


cli.add_command(config_cli, name="config")
cli.add_command(plugins_cli, name="plugin")

if __name__ == "__main__":
    cli()
